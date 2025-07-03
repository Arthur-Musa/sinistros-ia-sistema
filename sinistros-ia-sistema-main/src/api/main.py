from src.openai_config import *
from src.openai_config import *
# API REST para Sistema de Sinistros com FastAPI
# Integração completa com o sistema multi-agente

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import uuid
import logging
from enum import Enum
import os
from dotenv import load_dotenv

# Importar o sistema de agentes criado anteriormente
from src.agents.claims_agent_system import (
    processar_sinistro,
    claims_manager,
    Sinistro,
    TipoSinistro,
    StatusSinistro
)

# Configuração
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar FastAPI
app = FastAPI(
    title="API de Análise de Sinistros",
    description="Sistema inteligente multi-agente para análise de sinistros",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== MODELOS DE REQUEST/RESPONSE =====

class NovoSinistroRequest(BaseModel):
    """Request para criar novo sinistro"""
    data_ocorrencia: str = Field(..., example="2024-03-15")
    segurado_nome: str = Field(..., example="João Silva")
    segurado_documento: str = Field(..., example="123.456.789-00")
    segurado_telefone: str = Field(..., example="(11) 98765-4321")
    apolice_numero: str = Field(..., example="APO-2023-987654")
    descricao: str = Field(..., example="Colisão frontal em cruzamento...")
    documentos: List[str] = Field(..., example=["Boletim de Ocorrência", "CNH"])
    valor_estimado: Optional[float] = Field(None, example=45000.00)

class SinistroResponse(BaseModel):
    """Response com dados do sinistro"""
    numero_sinistro: str
    status: StatusSinistro
    tipo: Optional[TipoSinistro]
    data_criacao: str
    mensagem: str
    proximos_passos: List[str]

class AnaliseResponse(BaseModel):
    """Response da análise completa"""
    numero_sinistro: str
    status_final: str
    decisao: str
    valor_aprovado: Optional[float]
    justificativas: List[str]
    compliance_ok: bool
    alertas: List[str]
    relatorio_url: Optional[str]

# ===== BANCO DE DADOS SIMULADO =====

# Em produção, usar banco de dados real (PostgreSQL, MongoDB, etc.)
sinistros_db: Dict[str, Any] = {}
analises_em_andamento: Dict[str, Any] = {}

# ===== ENDPOINTS DA API =====

@app.get("/")
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "api": "Sistema de Análise de Sinistros",
        "versao": "1.0.0",
        "status": "operacional",
        "endpoints": {
            "POST /sinistros": "Criar novo sinistro",
            "GET /sinistros/{numero}": "Consultar sinistro",
            "POST /sinistros/{numero}/analisar": "Iniciar análise",
            "GET /sinistros/{numero}/status": "Status da análise",
            "GET /sinistros/{numero}/relatorio": "Relatório completo"
        }
    }

@app.post("/sinistros", response_model=SinistroResponse)
async def criar_sinistro(sinistro: NovoSinistroRequest):
    """Cria um novo sinistro no sistema"""
    try:
        # Gerar número único do sinistro
        numero_sinistro = f"SIN-{datetime.now().year}-{uuid.uuid4().hex[:8].upper()}"
        
        # Criar objeto sinistro
        novo_sinistro = {
            "numero_sinistro": numero_sinistro,
            "status": StatusSinistro.TRIAGEM,
            "tipo": None,
            "data_ocorrencia": sinistro.data_ocorrencia,
            "data_aviso": datetime.now().isoformat(),
            "data_criacao": datetime.now().isoformat(),
            "segurado": {
                "nome": sinistro.segurado_nome,
                "documento": sinistro.segurado_documento,
                "telefone": sinistro.segurado_telefone
            },
            "apolice": {
                "numero": sinistro.apolice_numero,
                "produto": "A ser consultado"
            },
            "descricao": sinistro.descricao,
            "documentos": sinistro.documentos,
            "valor_estimado": sinistro.valor_estimado,
            "analises": [],
            "compliance_check": None
        }
        
        # Salvar no "banco"
        sinistros_db[numero_sinistro] = novo_sinistro
        
        logger.info(f"Novo sinistro criado: {numero_sinistro}")
        
        return SinistroResponse(
            numero_sinistro=numero_sinistro,
            status=StatusSinistro.TRIAGEM,
            tipo=None,
            data_criacao=novo_sinistro["data_criacao"],
            mensagem="Sinistro registrado com sucesso",
            proximos_passos=[
                "Aguardar análise inicial",
                "Documentação será verificada",
                "Você será notificado sobre o andamento"
            ]
        )
        
    except Exception as e:
        logger.error(f"Erro ao criar sinistro: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sinistros/{numero_sinistro}")
async def consultar_sinistro(numero_sinistro: str):
    """Consulta dados de um sinistro"""
    if numero_sinistro not in sinistros_db:
        raise HTTPException(status_code=404, detail="Sinistro não encontrado")
    
    return sinistros_db[numero_sinistro]

@app.post("/sinistros/{numero_sinistro}/analisar")
async def iniciar_analise(numero_sinistro: str, background_tasks: BackgroundTasks):
    """Inicia análise assíncrona do sinistro pelos agentes"""
    if numero_sinistro not in sinistros_db:
        raise HTTPException(status_code=404, detail="Sinistro não encontrado")
    
    if numero_sinistro in analises_em_andamento:
        raise HTTPException(status_code=400, detail="Análise já em andamento")
    
    # Marcar como em análise
    sinistros_db[numero_sinistro]["status"] = StatusSinistro.EM_ANALISE
    analises_em_andamento[numero_sinistro] = {
        "inicio": datetime.now().isoformat(),
        "status": "processando"
    }
    
    # Executar análise em background
    background_tasks.add_task(
        executar_analise_background,
        numero_sinistro,
        sinistros_db[numero_sinistro]
    )
    
    return {
        "mensagem": "Análise iniciada",
        "numero_sinistro": numero_sinistro,
        "tempo_estimado": "5-10 minutos",
        "consulte_status_em": f"/sinistros/{numero_sinistro}/status"
    }

async def executar_analise_background(numero_sinistro: str, sinistro_data: Dict[str, Any]):
    """Executa análise pelos agentes em background"""
    try:
        logger.info(f"Iniciando análise do sinistro {numero_sinistro}")
        
        # Executar processamento pelos agentes
        resultado = processar_sinistro(sinistro_data)
        
        # Atualizar status baseado no resultado
        if "aprovado" in resultado.get("decisao", "").lower():
            sinistros_db[numero_sinistro]["status"] = StatusSinistro.APROVADO
        elif "negado" in resultado.get("decisao", "").lower():
            sinistros_db[numero_sinistro]["status"] = StatusSinistro.NEGADO
        else:
            sinistros_db[numero_sinistro]["status"] = StatusSinistro.DOCUMENTACAO_PENDENTE
        
        # Salvar resultado da análise
        sinistros_db[numero_sinistro]["analise_completa"] = resultado
        sinistros_db[numero_sinistro]["data_analise"] = datetime.now().isoformat()
        
        # Atualizar status da análise
        analises_em_andamento[numero_sinistro] = {
            "inicio": analises_em_andamento[numero_sinistro]["inicio"],
            "fim": datetime.now().isoformat(),
            "status": "concluida"
        }
        
        logger.info(f"Análise concluída para sinistro {numero_sinistro}")
        
    except Exception as e:
        logger.error(f"Erro na análise do sinistro {numero_sinistro}: {str(e)}")
        analises_em_andamento[numero_sinistro]["status"] = "erro"
        analises_em_andamento[numero_sinistro]["erro"] = str(e)

@app.get("/sinistros/{numero_sinistro}/status")
async def status_analise(numero_sinistro: str):
    """Verifica status da análise"""
    if numero_sinistro not in sinistros_db:
        raise HTTPException(status_code=404, detail="Sinistro não encontrado")
    
    status_info = {
        "numero_sinistro": numero_sinistro,
        "status_sinistro": sinistros_db[numero_sinistro]["status"],
        "analise_em_andamento": numero_sinistro in analises_em_andamento
    }
    
    if numero_sinistro in analises_em_andamento:
        status_info["analise"] = analises_em_andamento[numero_sinistro]
    
    if "analise_completa" in sinistros_db[numero_sinistro]:
        status_info["analise_disponivel"] = True
        status_info["consulte_em"] = f"/sinistros/{numero_sinistro}/relatorio"
    
    return status_info

@app.get("/sinistros/{numero_sinistro}/relatorio", response_model=AnaliseResponse)
async def obter_relatorio(numero_sinistro: str):
    """Obtém relatório completo da análise"""
    if numero_sinistro not in sinistros_db:
        raise HTTPException(status_code=404, detail="Sinistro não encontrado")
    
    if "analise_completa" not in sinistros_db[numero_sinistro]:
        raise HTTPException(status_code=400, detail="Análise ainda não concluída")
    
    analise = sinistros_db[numero_sinistro]["analise_completa"]
    
    return AnaliseResponse(
        numero_sinistro=numero_sinistro,
        status_final=sinistros_db[numero_sinistro]["status"].value,
        decisao=analise.get("decisao", ""),
        valor_aprovado=analise.get("valor_aprovado"),
        justificativas=analise.get("justificativas", []),
        compliance_ok=analise.get("compliance_ok", False),
        alertas=analise.get("alertas", []),
        relatorio_url=f"/api/v1/relatorios/{numero_sinistro}.pdf"
    )

# ===== ENDPOINTS DE ADMINISTRAÇÃO =====

@app.get("/admin/estatisticas")
async def estatisticas():
    """Estatísticas do sistema"""
    total_sinistros = len(sinistros_db)
    por_status = {}
    
    for sinistro in sinistros_db.values():
        status = sinistro["status"].value
        por_status[status] = por_status.get(status, 0) + 1
    
    return {
        "total_sinistros": total_sinistros,
        "por_status": por_status,
        "analises_em_andamento": len([a for a in analises_em_andamento.values() if a["status"] == "processando"]),
        "tempo_medio_analise": "7 minutos"  # Calcularia baseado em dados reais
    }

# ===== HEALTH CHECK =====

@app.get("/health")
async def health_check():
    """Verifica saúde da aplicação"""
    try:
        # Verificar conexões
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "api": "operational",
                "agents": "operational",
                "database": "operational"  # Verificaria conexão real
            }
        }
        return health_status
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

# ===== EXECUTAR SERVIDOR =====

if __name__ == "__main__":
    import uvicorn
    
    # Configurações de produção
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # False em produção
        workers=4,    # Múltiplos workers em produção
        log_level="info"
    )
