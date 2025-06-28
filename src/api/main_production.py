"""
API principal com todas as configurações de produção
"""

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import uuid

# Configurações e banco
from ..config.settings import get_settings
from ..database.connection import get_db, init_db
from ..database.models import Sinistro, StatusSinistro, TipoSinistro, HistoricoSinistro

# Workers e tarefas
from ..workers.tasks import processar_sinistro_async, enviar_webhook

# Integrações
from ..integrations.legacy_system import sincronizar_sinistro_com_legado

# Monitoramento
from ..monitoring.metrics import MetricsMiddleware, track_metric, track_error, track_time

# Modelos Pydantic
from pydantic import BaseModel, Field, validator
from enum import Enum

# Configurar logging
logging.basicConfig(
    level=getattr(logging, get_settings().LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Criar aplicação FastAPI
app = FastAPI(
    title="Sistema Inteligente de Análise de Sinistros",
    description="API para processamento automático de sinistros com IA",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.API_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de métricas
app.add_middleware(MetricsMiddleware)

# Modelos Pydantic para API
class TipoSinistroEnum(str, Enum):
    automovel = "automovel"
    residencial = "residencial"
    vida = "vida"
    empresarial = "empresarial"
    saude = "saude"
    viagem = "viagem"
    outros = "outros"

class StatusSinistroEnum(str, Enum):
    recebido = "recebido"
    triagem = "triagem"
    em_analise = "em_analise"
    documentacao_pendente = "documentacao_pendente"
    em_calculo = "em_calculo"
    em_compliance = "em_compliance"
    aprovado = "aprovado"
    negado = "negado"
    cancelado = "cancelado"
    finalizado = "finalizado"

class SinistroCreate(BaseModel):
    """Modelo para criar sinistro"""
    data_ocorrencia: datetime
    segurado_nome: str = Field(..., min_length=3, max_length=200)
    segurado_documento: str = Field(..., min_length=11, max_length=50)
    segurado_telefone: Optional[str] = Field(None, max_length=30)
    segurado_email: Optional[str] = Field(None, max_length=200)
    apolice_numero: str = Field(..., min_length=5, max_length=50)
    descricao: str = Field(..., min_length=10)
    local_ocorrencia: Optional[str] = None
    valor_estimado: float = Field(0.0, ge=0)
    canal_origem: Optional[str] = "api"
    sistema_origem: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}
    
    @validator('segurado_documento')
    def validar_documento(cls, v):
        # Remover caracteres não numéricos
        doc = ''.join(filter(str.isdigit, v))
        if len(doc) not in [11, 14]:  # CPF ou CNPJ
            raise ValueError('Documento deve ser CPF (11 dígitos) ou CNPJ (14 dígitos)')
        return v

class SinistroResponse(BaseModel):
    """Modelo de resposta para sinistro"""
    id: int
    numero_sinistro: str
    status: StatusSinistroEnum
    tipo: Optional[TipoSinistroEnum]
    data_ocorrencia: datetime
    data_criacao: datetime
    segurado_nome: str
    apolice_numero: str
    valor_estimado: float
    valor_aprovado: float
    canal_origem: str
    
    class Config:
        from_attributes = True

class AnaliseRequest(BaseModel):
    """Requisição para análise"""
    prioridade: Optional[int] = Field(5, ge=1, le=10)
    reprocessar: Optional[bool] = False

class AnaliseResponse(BaseModel):
    """Resposta da análise"""
    task_id: str
    status: str
    mensagem: str

# Handlers de erro
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    track_error("http_error", exc, {"status_code": exc.status_code, "path": request.url.path})
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "timestamp": datetime.now().isoformat()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    track_error("unhandled_error", exc, {"path": request.url.path})
    logger.error(f"Erro não tratado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor", "timestamp": datetime.now().isoformat()}
    )

# Incluir routers
from .integrations_adapter import router as integrations_router
app.include_router(integrations_router, prefix="/api/v1")

# Eventos de startup/shutdown
@app.on_event("startup")
async def startup_event():
    """Inicializar recursos na startup"""
    logger.info("Iniciando aplicação...")
    
    # Inicializar banco
    init_db()
    
    # Verificar conexões
    from ..integrations.legacy_system import legacy_client
    try:
        # Testar conexão com sistema legado
        legacy_client.session.get(f"{settings.LEGACY_SYSTEM_URL}/health")
        logger.info("Conexão com sistema legado OK")
    except Exception as e:
        logger.warning(f"Sistema legado indisponível: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Limpar recursos no shutdown"""
    logger.info("Encerrando aplicação...")

# Rotas da API
@app.get("/health")
async def health_check():
    """Health check da API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

@app.post("/api/v1/sinistros", response_model=SinistroResponse)
async def criar_sinistro(
    sinistro_data: SinistroCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Criar novo sinistro"""
    with track_time("criar_sinistro"):
        try:
            # Gerar número único
            numero_sinistro = f"SIN-{datetime.now().year}-{uuid.uuid4().hex[:8].upper()}"
            
            # Criar sinistro no banco
            sinistro = Sinistro(
                numero_sinistro=numero_sinistro,
                status=StatusSinistro.RECEBIDO,
                data_ocorrencia=sinistro_data.data_ocorrencia,
                segurado_nome=sinistro_data.segurado_nome,
                segurado_documento=sinistro_data.segurado_documento,
                segurado_telefone=sinistro_data.segurado_telefone,
                segurado_email=sinistro_data.segurado_email,
                apolice_numero=sinistro_data.apolice_numero,
                descricao=sinistro_data.descricao,
                local_ocorrencia=sinistro_data.local_ocorrencia,
                valor_estimado=sinistro_data.valor_estimado,
                canal_origem=sinistro_data.canal_origem,
                sistema_origem=sinistro_data.sistema_origem,
                metadata=sinistro_data.metadata
            )
            
            db.add(sinistro)
            db.commit()
            db.refresh(sinistro)
            
            # Histórico
            historico = HistoricoSinistro(
                sinistro_id=sinistro.id,
                acao="sinistro_criado",
                usuario="api",
                descricao=f"Sinistro criado via {sinistro_data.canal_origem}"
            )
            db.add(historico)
            db.commit()
            
            # Sincronizar com sistema legado em background
            background_tasks.add_task(sincronizar_sinistro_com_legado, sinistro)
            
            # Webhook de criação
            background_tasks.add_task(
                enviar_webhook.delay,
                sinistro.numero_sinistro,
                "sinistro.criado",
                {"numero": sinistro.numero_sinistro, "status": "recebido"}
            )
            
            # Métrica
            track_metric("sinistros_criados", 1, {
                "canal": sinistro.canal_origem,
                "tipo": sinistro.tipo.value if sinistro.tipo else "indefinido"
            })
            
            logger.info(f"Sinistro {numero_sinistro} criado com sucesso")
            return sinistro
            
        except Exception as e:
            logger.error(f"Erro ao criar sinistro: {e}")
            track_error("erro_criar_sinistro", e)
            raise HTTPException(status_code=500, detail="Erro ao criar sinistro")

@app.get("/api/v1/sinistros/{numero_sinistro}", response_model=SinistroResponse)
async def obter_sinistro(numero_sinistro: str, db: Session = Depends(get_db)):
    """Obter sinistro por número"""
    sinistro = db.query(Sinistro).filter_by(numero_sinistro=numero_sinistro).first()
    
    if not sinistro:
        raise HTTPException(status_code=404, detail="Sinistro não encontrado")
    
    return sinistro

@app.get("/api/v1/sinistros", response_model=List[SinistroResponse])
async def listar_sinistros(
    status: Optional[StatusSinistroEnum] = None,
    tipo: Optional[TipoSinistroEnum] = None,
    limite: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Listar sinistros com filtros"""
    query = db.query(Sinistro)
    
    if status:
        query = query.filter(Sinistro.status == StatusSinistro[status.value.upper()])
    
    if tipo:
        query = query.filter(Sinistro.tipo == TipoSinistro[tipo.value.upper()])
    
    sinistros = query.offset(offset).limit(limite).all()
    return sinistros

@app.post("/api/v1/sinistros/{numero_sinistro}/analisar", response_model=AnaliseResponse)
async def analisar_sinistro(
    numero_sinistro: str,
    analise_req: AnaliseRequest = AnaliseRequest(),
    db: Session = Depends(get_db)
):
    """Iniciar análise de sinistro pelos agentes"""
    with track_time("iniciar_analise", {"prioridade": str(analise_req.prioridade)}):
        sinistro = db.query(Sinistro).filter_by(numero_sinistro=numero_sinistro).first()
        
        if not sinistro:
            raise HTTPException(status_code=404, detail="Sinistro não encontrado")
        
        # Verificar se já está em análise
        if sinistro.status in [StatusSinistro.EM_ANALISE, StatusSinistro.EM_CALCULO, StatusSinistro.EM_COMPLIANCE]:
            if not analise_req.reprocessar:
                return AnaliseResponse(
                    task_id="",
                    status="em_andamento",
                    mensagem="Sinistro já está sendo analisado"
                )
        
        try:
            # Criar task assíncrona
            task = processar_sinistro_async.apply_async(
                args=[numero_sinistro],
                priority=analise_req.prioridade
            )
            
            # Atualizar status
            sinistro.status = StatusSinistro.TRIAGEM
            db.commit()
            
            # Métrica
            track_metric("analises_iniciadas", 1, {"prioridade": str(analise_req.prioridade)})
            
            return AnaliseResponse(
                task_id=task.id,
                status="iniciado",
                mensagem=f"Análise iniciada. Task ID: {task.id}"
            )
            
        except Exception as e:
            logger.error(f"Erro ao iniciar análise: {e}")
            track_error("erro_iniciar_analise", e)
            raise HTTPException(status_code=500, detail="Erro ao iniciar análise")

@app.get("/api/v1/sinistros/{numero_sinistro}/status")
async def status_analise(numero_sinistro: str, db: Session = Depends(get_db)):
    """Verificar status da análise"""
    sinistro = db.query(Sinistro).filter_by(numero_sinistro=numero_sinistro).first()
    
    if not sinistro:
        raise HTTPException(status_code=404, detail="Sinistro não encontrado")
    
    # Buscar última análise
    ultima_analise = db.query(Analise).filter_by(
        sinistro_id=sinistro.id
    ).order_by(Analise.data_inicio.desc()).first()
    
    return {
        "numero_sinistro": numero_sinistro,
        "status_atual": sinistro.status.value,
        "analise": {
            "em_andamento": sinistro.status in [StatusSinistro.EM_ANALISE, StatusSinistro.TRIAGEM],
            "data_inicio": ultima_analise.data_inicio if ultima_analise else None,
            "data_fim": ultima_analise.data_fim if ultima_analise else None,
            "resultado": ultima_analise.resultado if ultima_analise and ultima_analise.data_fim else None
        }
    }

@app.get("/api/v1/admin/metricas")
async def obter_metricas(db: Session = Depends(get_db)):
    """Obter métricas do sistema"""
    from sqlalchemy import func
    
    # Total por status
    status_count = db.query(
        Sinistro.status,
        func.count(Sinistro.id)
    ).group_by(Sinistro.status).all()
    
    # Total por tipo
    tipo_count = db.query(
        Sinistro.tipo,
        func.count(Sinistro.id)
    ).group_by(Sinistro.tipo).all()
    
    # Valores
    valor_total = db.query(func.sum(Sinistro.valor_estimado)).scalar() or 0
    valor_aprovado = db.query(func.sum(Sinistro.valor_aprovado)).scalar() or 0
    
    return {
        "timestamp": datetime.now().isoformat(),
        "totais": {
            "sinistros": db.query(func.count(Sinistro.id)).scalar(),
            "em_analise": db.query(func.count(Sinistro.id)).filter(
                Sinistro.status.in_([StatusSinistro.EM_ANALISE, StatusSinistro.TRIAGEM])
            ).scalar()
        },
        "por_status": {status.value: count for status, count in status_count if status},
        "por_tipo": {tipo.value if tipo else "indefinido": count for tipo, count in tipo_count},
        "valores": {
            "estimado_total": float(valor_total),
            "aprovado_total": float(valor_aprovado),
            "taxa_aprovacao": (valor_aprovado / valor_total * 100) if valor_total > 0 else 0
        }
    }

# Rota para Prometheus metrics
if settings.PROMETHEUS_ENABLED:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    
    @app.get("/metrics")
    async def metrics():
        """Endpoint para Prometheus coletar métricas"""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main_production:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
                }
            },
            "handlers": {
                "default": {
                    "formatter": "json" if settings.LOG_FORMAT == "json" else "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout"
                },
            },
            "root": {
                "level": settings.LOG_LEVEL,
                "handlers": ["default"]
            }
        }
    )
