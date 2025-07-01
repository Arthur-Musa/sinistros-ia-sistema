"""
Adaptador para facilitar integração com sistemas existentes
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from ..connectors.claims_receiver import receive_claim_from_channel
from ..database.connection import get_db_session
from ..database.models import Sinistro
from ..monitoring.metrics import track_metric

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.post("/legacy/claim")
async def receive_legacy_claim(
    data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Recebe sinistro do sistema legado
    
    Formato esperado:
    {
        "PolicyNumber": "APL-2024-001",
        "ClaimDate": "2024-01-15T10:30:00",
        "InsuredName": "Nome do Segurado",
        "InsuredDocument": "123.456.789-00",
        "InsuredPhone": "11999999999",
        "InsuredEmail": "email@example.com",
        "Description": "Descrição do sinistro",
        "Location": "São Paulo, SP",
        "EstimatedAmount": 15000.00
    }
    """
    try:
        numero_sinistro = receive_claim_from_channel('legacy', data)
        
        track_metric("integration_legacy_claim", 1)
        
        return {
            "success": True,
            "claim_number": numero_sinistro,
            "message": "Sinistro recebido e enviado para análise"
        }
    
    except Exception as e:
        logger.error(f"Erro ao receber sinistro legado: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mobile/claim")
async def receive_mobile_claim(
    data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Recebe sinistro do app mobile
    
    Formato esperado:
    {
        "auth_token": "token-do-usuario",
        "timestamp": 1704456600,
        "user": {
            "name": "Nome do Usuário",
            "document": "12345678900",
            "phone": "11999999999",
            "email": "usuario@example.com"
        },
        "policy_number": "APL-2024-001",
        "description": "Descrição do sinistro",
        "estimated_value": 15000.00,
        "location": {
            "latitude": -23.550520,
            "longitude": -46.633308
        },
        "photos": ["url1", "url2"],
        "device_info": {
            "platform": "iOS",
            "version": "17.0"
        }
    }
    """
    try:
        numero_sinistro = receive_claim_from_channel('mobile', data)
        
        track_metric("integration_mobile_claim", 1)
        
        return {
            "success": True,
            "claim_number": numero_sinistro,
            "message": "Sinistro recebido via app mobile"
        }
    
    except Exception as e:
        logger.error(f"Erro ao receber sinistro mobile: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/email/claim")
async def receive_email_claim(
    data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Recebe sinistro via email parseado
    
    Formato esperado:
    {
        "email_id": "unique-email-id",
        "from_email": "cliente@example.com",
        "from_name": "Nome do Cliente",
        "subject": "Sinistro - Colisão",
        "body": "Conteúdo do email...",
        "received_at": "2024-01-15T10:30:00",
        "attachments": [
            {
                "filename": "foto1.jpg",
                "url": "s3://bucket/path/foto1.jpg",
                "size": 2048000
            }
        ]
    }
    """
    try:
        numero_sinistro = receive_claim_from_channel('email', data)
        
        track_metric("integration_email_claim", 1)
        
        return {
            "success": True,
            "claim_number": numero_sinistro,
            "message": "Email processado e sinistro criado"
        }
    
    except Exception as e:
        logger.error(f"Erro ao processar email: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch/process")
async def process_batch_file(
    file_url: str,
    file_type: str = "csv",
    background_tasks: BackgroundTasks = None
):
    """
    Processa arquivo batch com múltiplos sinistros
    
    Parâmetros:
    - file_url: URL do arquivo (S3, HTTP, etc)
    - file_type: csv ou xlsx
    """
    try:
        import pandas as pd
        
        # Ler arquivo
        if file_type == "csv":
            df = pd.read_csv(file_url)
        else:
            df = pd.read_excel(file_url)
        
        processed = 0
        errors = []
        
        # Processar cada linha
        for idx, row in df.iterrows():
            try:
                data = row.to_dict()
                data['linha_numero'] = idx + 1
                data['arquivo_origem'] = file_url
                
                receive_claim_from_channel('batch', data)
                processed += 1
                
            except Exception as e:
                errors.append({
                    "linha": idx + 1,
                    "erro": str(e)
                })
        
        track_metric("integration_batch_processed", processed)
        
        return {
            "success": True,
            "total_rows": len(df),
            "processed": processed,
            "errors": errors
        }
    
    except Exception as e:
        logger.error(f"Erro ao processar batch: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/claim/{claim_number}/status")
async def get_claim_status(claim_number: str):
    """
    Retorna status do sinistro para sistemas externos
    """
    try:
        with get_db_session() as db:
            sinistro = db.query(Sinistro).filter_by(
                numero_sinistro=claim_number
            ).first()
            
            if not sinistro:
                raise HTTPException(status_code=404, detail="Sinistro não encontrado")
            
            # Buscar última análise se houver
            analise = None
            if sinistro.analises:
                analise = max(sinistro.analises, key=lambda a: a.criado_em)
            
            return {
                "claim_number": sinistro.numero_sinistro,
                "status": sinistro.status.value,
                "created_at": sinistro.criado_em.isoformat(),
                "insured_name": sinistro.segurado_nome,
                "policy_number": sinistro.apolice_numero,
                "analysis": {
                    "status": analise.status if analise else None,
                    "decision": analise.decisao if analise else None,
                    "risk_score": analise.score_risco if analise else None,
                    "completed_at": analise.finalizado_em.isoformat() if analise and analise.finalizado_em else None
                } if analise else None
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar status: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno")


@router.post("/webhook/register")
async def register_webhook(
    url: str,
    events: list[str],
    secret: Optional[str] = None
):
    """
    Registra webhook para receber notificações
    
    Eventos disponíveis:
    - sinistro.criado
    - analise.iniciada
    - analise.concluida
    - decisao.tomada
    """
    try:
        from ..database.models import Webhook
        
        with get_db_session() as db:
            webhook = Webhook(
                url=url,
                eventos=events,
                secret=secret,
                ativo=True
            )
            db.add(webhook)
            db.commit()
            
            return {
                "success": True,
                "webhook_id": webhook.id,
                "message": "Webhook registrado com sucesso"
            }
    
    except Exception as e:
        logger.error(f"Erro ao registrar webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao registrar webhook")
