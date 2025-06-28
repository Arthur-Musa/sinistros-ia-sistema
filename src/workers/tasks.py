"""
Tasks assíncronas do Celery
"""

from celery import Task
from celery.exceptions import MaxRetriesExceededError
import logging
from datetime import datetime, timedelta
import json
import requests
from typing import Dict, Any, Optional

from .celery_app import celery_app
from ..database.connection import get_db_session
from ..database.models import Sinistro, Analise, FilaProcessamento, WebhookLog, HistoricoSinistro, StatusSinistro
from ..agents.claims_agent_system import processar_sinistro as processar_sinistro_agentes
from ..config.settings import get_settings
from ..monitoring.metrics import track_metric, track_error

logger = logging.getLogger(__name__)
settings = get_settings()

class BaseTask(Task):
    """Task base com retry automático"""
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True

@celery_app.task(bind=True, base=BaseTask, name="processar_sinistro_async")
def processar_sinistro_async(self, sinistro_numero: str) -> Dict[str, Any]:
    """
    Processa sinistro de forma assíncrona usando os agentes
    """
    logger.info(f"Iniciando processamento assíncrono do sinistro {sinistro_numero}")
    start_time = datetime.now()
    
    try:
        with get_db_session() as db:
            # Buscar sinistro
            sinistro = db.query(Sinistro).filter_by(numero_sinistro=sinistro_numero).first()
            if not sinistro:
                raise ValueError(f"Sinistro {sinistro_numero} não encontrado")
            
            # Atualizar status
            sinistro.status = StatusSinistro.EM_ANALISE
            db.commit()
            
            # Registrar no histórico
            historico = HistoricoSinistro(
                sinistro_id=sinistro.id,
                acao="analise_iniciada",
                status_anterior=StatusSinistro.TRIAGEM.value,
                status_novo=StatusSinistro.EM_ANALISE.value,
                usuario="sistema",
                descricao="Análise automática iniciada pelos agentes"
            )
            db.add(historico)
            
            # Preparar dados para os agentes
            sinistro_data = {
                "numero_sinistro": sinistro.numero_sinistro,
                "tipo": sinistro.tipo.value if sinistro.tipo else None,
                "data_ocorrencia": sinistro.data_ocorrencia.isoformat(),
                "segurado": {
                    "nome": sinistro.segurado_nome,
                    "documento": sinistro.segurado_documento,
                    "telefone": sinistro.segurado_telefone,
                    "email": sinistro.segurado_email
                },
                "apolice": {
                    "numero": sinistro.apolice_numero,
                    "produto": sinistro.apolice_produto
                },
                "descricao": sinistro.descricao,
                "valor_estimado": sinistro.valor_estimado,
                "documentos": [doc.nome for doc in sinistro.documentos],
                "metadata": sinistro.metadata or {}
            }
            
            # Processar com os agentes
            logger.info(f"Enviando sinistro {sinistro_numero} para análise dos agentes")
            resultado = processar_sinistro_agentes(sinistro_data)
            
            # Salvar análise
            duracao = (datetime.now() - start_time).total_seconds()
            analise = Analise(
                sinistro_id=sinistro.id,
                agente=resultado.get("agent_usado", "GerenteSinistros"),
                tipo_analise="completa",
                data_fim=datetime.now(),
                duracao_segundos=int(duracao),
                resultado=resultado,
                decisao=resultado.get("decisao", "pendente"),
                confianca=resultado.get("confianca", 0.8),
                justificativas=resultado.get("justificativas", []),
                alertas=resultado.get("alertas", []),
                sucesso=True
            )
            db.add(analise)
            
            # Atualizar status do sinistro baseado na decisão
            if "aprovado" in resultado.get("mensagem", "").lower():
                sinistro.status = StatusSinistro.APROVADO
                sinistro.valor_aprovado = resultado.get("valor_aprovado", sinistro.valor_estimado)
            elif "negado" in resultado.get("mensagem", "").lower():
                sinistro.status = StatusSinistro.NEGADO
            else:
                sinistro.status = StatusSinistro.DOCUMENTACAO_PENDENTE
            
            # Atualizar fila
            fila = db.query(FilaProcessamento).filter_by(
                sinistro_numero=sinistro_numero,
                task_id=self.request.id
            ).first()
            if fila:
                fila.status = "concluido"
                fila.data_fim_processamento = datetime.now()
            
            db.commit()
            
            # Enviar webhook
            enviar_webhook.delay(
                sinistro_numero=sinistro_numero,
                evento="analise.concluida",
                dados=resultado
            )
            
            # Métricas
            track_metric("sinistro_processado", 1, {
                "status": sinistro.status.value,
                "duracao": duracao,
                "agente": resultado.get("agent_usado")
            })
            
            logger.info(f"Sinistro {sinistro_numero} processado com sucesso em {duracao:.2f}s")
            return resultado
            
    except Exception as e:
        logger.error(f"Erro ao processar sinistro {sinistro_numero}: {str(e)}")
        track_error("erro_processamento_sinistro", e, {"sinistro": sinistro_numero})
        
        # Atualizar fila com erro
        with get_db_session() as db:
            fila = db.query(FilaProcessamento).filter_by(
                sinistro_numero=sinistro_numero,
                task_id=self.request.id
            ).first()
            if fila:
                fila.status = "erro"
                fila.erro_mensagem = str(e)
                fila.tentativas += 1
                
                if fila.tentativas < fila.max_tentativas:
                    fila.proxima_tentativa = datetime.now() + timedelta(minutes=5 * fila.tentativas)
                    fila.status = "aguardando"
                
            db.commit()
        
        # Retry automático do Celery
        raise self.retry(exc=e, countdown=300)  # Retry em 5 minutos

@celery_app.task(name="enviar_webhook")
def enviar_webhook(sinistro_numero: str, evento: str, dados: Dict[str, Any]) -> bool:
    """
    Envia webhook para sistemas externos
    """
    logger.info(f"Enviando webhook {evento} para sinistro {sinistro_numero}")
    
    with get_db_session() as db:
        sinistro = db.query(Sinistro).filter_by(numero_sinistro=sinistro_numero).first()
        if not sinistro:
            logger.error(f"Sinistro {sinistro_numero} não encontrado para webhook")
            return False
        
        # URLs de webhook configuradas (podem vir do banco ou configuração)
        webhook_urls = [
            "https://sistema-legado.com/webhooks/sinistros",
            "https://dashboard.empresa.com/api/webhooks",
        ]
        
        payload = {
            "evento": evento,
            "timestamp": datetime.now().isoformat(),
            "sinistro": {
                "numero": sinistro_numero,
                "status": sinistro.status.value,
                "valor_aprovado": sinistro.valor_aprovado
            },
            "dados": dados
        }
        
        # Adicionar assinatura para segurança
        import hmac
        import hashlib
        signature = hmac.new(
            settings.WEBHOOK_SECRET.encode(),
            json.dumps(payload).encode(),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": evento
        }
        
        for url in webhook_urls:
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=settings.WEBHOOK_TIMEOUT
                )
                
                # Registrar log
                webhook_log = WebhookLog(
                    sinistro_id=sinistro.id,
                    url=url,
                    evento=evento,
                    status_code=response.status_code,
                    resposta=response.text[:1000],  # Limitar tamanho
                    sucesso=response.status_code < 400,
                    payload=payload
                )
                db.add(webhook_log)
                
                logger.info(f"Webhook enviado para {url}: {response.status_code}")
                
            except Exception as e:
                logger.error(f"Erro ao enviar webhook para {url}: {str(e)}")
                
                webhook_log = WebhookLog(
                    sinistro_id=sinistro.id,
                    url=url,
                    evento=evento,
                    sucesso=False,
                    erro=str(e),
                    payload=payload
                )
                db.add(webhook_log)
        
        db.commit()
        return True

@celery_app.task(name="limpar_filas_antigas")
def limpar_filas_antigas() -> int:
    """
    Limpa registros antigos da fila de processamento
    """
    logger.info("Limpando filas antigas")
    
    with get_db_session() as db:
        # Remover registros concluídos há mais de 7 dias
        limite = datetime.now() - timedelta(days=7)
        
        deletados = db.query(FilaProcessamento).filter(
            FilaProcessamento.status.in_(["concluido", "erro"]),
            FilaProcessamento.data_fim_processamento < limite
        ).delete()
        
        db.commit()
        
        logger.info(f"Removidos {deletados} registros antigos da fila")
        return deletados

@celery_app.task(name="reprocessar_sinistros_falhos")
def reprocessar_sinistros_falhos() -> int:
    """
    Reprocessa sinistros que falharam e estão aguardando retry
    """
    logger.info("Verificando sinistros para reprocessamento")
    
    with get_db_session() as db:
        # Buscar sinistros aguardando retry
        sinistros_retry = db.query(FilaProcessamento).filter(
            FilaProcessamento.status == "aguardando",
            FilaProcessamento.proxima_tentativa <= datetime.now(),
            FilaProcessamento.tentativas < FilaProcessamento.max_tentativas
        ).all()
        
        reprocessados = 0
        for fila in sinistros_retry:
            logger.info(f"Reprocessando sinistro {fila.sinistro_numero} (tentativa {fila.tentativas + 1})")
            
            # Criar nova task
            task = processar_sinistro_async.delay(fila.sinistro_numero)
            fila.task_id = task.id
            fila.status = "processando"
            fila.data_inicio_processamento = datetime.now()
            
            reprocessados += 1
        
        db.commit()
        
        logger.info(f"Reprocessados {reprocessados} sinistros")
        return reprocessados

@celery_app.task(name="gerar_metricas_sistema")
def gerar_metricas_sistema() -> Dict[str, Any]:
    """
    Gera métricas do sistema para monitoramento
    """
    with get_db_session() as db:
        # Contar sinistros por status
        from sqlalchemy import func
        status_count = db.query(
            Sinistro.status,
            func.count(Sinistro.id)
        ).group_by(Sinistro.status).all()
        
        # Calcular tempo médio de análise
        tempo_medio = db.query(
            func.avg(Analise.duracao_segundos)
        ).filter(
            Analise.sucesso == True,
            Analise.data_fim >= datetime.now() - timedelta(hours=1)
        ).scalar() or 0
        
        # Taxa de aprovação
        total_analisados = db.query(func.count(Sinistro.id)).filter(
            Sinistro.status.in_([StatusSinistro.APROVADO, StatusSinistro.NEGADO])
        ).scalar() or 0
        
        total_aprovados = db.query(func.count(Sinistro.id)).filter(
            Sinistro.status == StatusSinistro.APROVADO
        ).scalar() or 0
        
        taxa_aprovacao = (total_aprovados / total_analisados * 100) if total_analisados > 0 else 0
        
        metricas = {
            "timestamp": datetime.now().isoformat(),
            "sinistros_por_status": {status.value: count for status, count in status_count},
            "tempo_medio_analise_segundos": float(tempo_medio),
            "taxa_aprovacao_percent": taxa_aprovacao,
            "fila_processamento": db.query(func.count(FilaProcessamento.id)).filter(
                FilaProcessamento.status == "aguardando"
            ).scalar() or 0
        }
        
        # Enviar para sistema de monitoramento (Prometheus, Datadog, etc)
        track_metric("metricas_sistema", metricas)
        
        return metricas
