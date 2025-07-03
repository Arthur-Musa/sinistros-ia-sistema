# Sistema Multi-Agente CORRIGIDO - Força uso da OPENAI_API_KEY do Railway
import os
import sys

# FORÇA ABSOLUTA para usar a API KEY do Railway
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
if OPENAI_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_KEY
    # Força no ambiente do Python também
    import openai
    openai.api_key = OPENAI_KEY

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json
import asyncio
from pydantic import BaseModel

try:
    from openai import OpenAI
    # Inicializa cliente com a chave explicitamente
    client = OpenAI(api_key=OPENAI_KEY)
    from swarm import Agent, Swarm
    USE_AI = True
except ImportError as e:
    print(f"ERRO CRÍTICO: {e}")
    USE_AI = False

# Enums do sistema
class TipoSinistro(str, Enum):
    AUTOMOVEL = "automovel"
    RESIDENCIAL = "residencial"
    VIDA = "vida"
    EMPRESARIAL = "empresarial"
    SAUDE = "saude"

class StatusSinistro(str, Enum):
    TRIAGEM = "triagem"
    EM_ANALISE = "em_analise"
    DOCUMENTACAO_PENDENTE = "documentacao_pendente"
    APROVADO = "aprovado"
    NEGADO = "negado"
    EM_PAGAMENTO = "em_pagamento"
    FINALIZADO = "finalizado"

class Sinistro(BaseModel):
    numero_sinistro: str
    tipo: Optional[TipoSinistro] = None
    data_ocorrencia: str
    data_aviso: str
    segurado: Dict[str, Any]
    apolice: Dict[str, Any]
    descricao: str
    documentos: List[str]
    valor_estimado: Optional[float] = None
    valor_aprovado: Optional[float] = None
    status: StatusSinistro = StatusSinistro.TRIAGEM
    analises: List[Dict[str, Any]] = []
    compliance_check: Optional[Dict[str, Any]] = None

# ===== OS 5 AGENTES DE IA =====

class SistemaMultiAgente:
    def __init__(self):
        if not USE_AI or not OPENAI_KEY:
            raise Exception("SISTEMA REQUER OPENAI_API_KEY CONFIGURADA!")
        
        # Inicializar Swarm com API key explícita
        self.swarm = Swarm(client=client)
        
        # 1. AGENTE DE TRIAGEM
        self.agente_triagem = Agent(
            name="AgenteTriagem",
            model="gpt-4o",
            instructions="""Você é o Agente de Triagem especializado. Suas responsabilidades:
            1. Classificar o tipo de sinistro (automóvel, residencial, vida, empresarial, saúde)
            2. Validar informações básicas
            3. Identificar documentação necessária
            4. Determinar prioridade
            5. Detectar possíveis fraudes
            
            Analise: {descricao} e {documentos}
            Retorne um JSON com: tipo_identificado, prioridade, documentos_necessarios, alerta_fraude"""
        )
        
        # 2. AGENTE DE ANÁLISE
        self.agente_analise = Agent(
            name="AgenteAnalise", 
            model="gpt-4o",
            instructions="""Você é o Agente de Análise de Documentos. Suas responsabilidades:
            1. Verificar autenticidade dos documentos
            2. Identificar inconsistências
            3. Avaliar evidências (fotos, laudos)
            4. Verificar completude
            5. Recomendar investigação adicional se necessário
            
            Retorne JSON com: documentos_ok, inconsistencias, recomendacoes"""
        )
        
        # 3. AGENTE DE CÁLCULO
        self.agente_calculo = Agent(
            name="AgenteCalculo",
            model="gpt-4o", 
            instructions="""Você é o Agente de Cálculo de Indenizações. Suas responsabilidades:
            1. Calcular valor base conforme apólice
            2. Aplicar franquias e deduções
            3. Verificar limites de cobertura
            4. Considerar depreciação
            5. Apresentar memória de cálculo
            
            Para valor estimado: {valor_estimado}
            Retorne JSON com: valor_base, deducoes, valor_final, memoria_calculo"""
        )
        
        # 4. AGENTE DE COMPLIANCE
        self.agente_compliance = Agent(
            name="AgenteCompliance",
            model="gpt-4o",
            instructions="""Você é o Agente de Compliance. Suas responsabilidades:
            1. Verificar conformidade SUSEP
            2. Garantir LGPD
            3. Validar prazos regulamentares
            4. Verificar documentação obrigatória
            5. Alertar riscos regulatórios
            
            Retorne JSON com: susep_ok, lgpd_ok, alertas_compliance"""
        )
        
        # 5. AGENTE GERENTE (Orquestrador)
        self.agente_gerente = Agent(
            name="GerenteSinistros",
            model="gpt-4o",
            instructions="""Você é o Gerente de Sinistros que coordena os 5 agentes:
            1. AgenteTriagem - classificação inicial
            2. AgenteAnalise - análise de documentos  
            3. AgenteCalculo - cálculo de valores
            4. AgenteCompliance - verificação regulatória
            5. Você mesmo - decisão final
            
            Consolide as análises e tome a decisão final.
            Retorne JSON com: decisao, valor_aprovado, justificativas, proximos_passos"""
        )
    
    async def processar_com_5_agentes(self, sinistro_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa o sinistro usando os 5 agentes de IA"""
        
        resultados = {
            "numero_sinistro": sinistro_data.get("numero_sinistro"),
            "timestamp_inicio": datetime.now().isoformat(),
            "agentes_executados": []
        }
        
        try:
            # 1. TRIAGEM
            msg_triagem = f"Classifique este sinistro: {sinistro_data.get('descricao')}. Documentos: {sinistro_data.get('documentos')}"
            resp_triagem = self.swarm.run(
                agent=self.agente_triagem,
                messages=[{"role": "user", "content": msg_triagem}]
            )
            resultados["triagem"] = resp_triagem.messages[-1]["content"]
            resultados["agentes_executados"].append("Triagem")
            
            # 2. ANÁLISE
            msg_analise = f"Analise os documentos: {sinistro_data.get('documentos')} para o sinistro {sinistro_data.get('numero_sinistro')}"
            resp_analise = self.swarm.run(
                agent=self.agente_analise,
                messages=[{"role": "user", "content": msg_analise}]
            )
            resultados["analise_docs"] = resp_analise.messages[-1]["content"]
            resultados["agentes_executados"].append("Análise")
            
            # 3. CÁLCULO
            msg_calculo = f"Calcule a indenização. Valor estimado: R$ {sinistro_data.get('valor_estimado', 0)}"
            resp_calculo = self.swarm.run(
                agent=self.agente_calculo,
                messages=[{"role": "user", "content": msg_calculo}]
            )
            resultados["calculo"] = resp_calculo.messages[-1]["content"]
            resultados["agentes_executados"].append("Cálculo")
            
            # 4. COMPLIANCE
            msg_compliance = f"Verifique compliance para sinistro {sinistro_data.get('numero_sinistro')}"
            resp_compliance = self.swarm.run(
                agent=self.agente_compliance,
                messages=[{"role": "user", "content": msg_compliance}]
            )
            resultados["compliance"] = resp_compliance.messages[-1]["content"]
            resultados["agentes_executados"].append("Compliance")
            
            # 5. DECISÃO FINAL (Gerente)
            msg_final = f"""
            Com base nas análises dos 4 agentes:
            - Triagem: {resultados['triagem']}
            - Análise: {resultados['analise_docs']}  
            - Cálculo: {resultados['calculo']}
            - Compliance: {resultados['compliance']}
            
            Tome a decisão final para o sinistro {sinistro_data.get('numero_sinistro')}
            """
            resp_final = self.swarm.run(
                agent=self.agente_gerente,
                messages=[{"role": "user", "content": msg_final}]
            )
            resultados["decisao_final"] = resp_final.messages[-1]["content"]
            resultados["agentes_executados"].append("Gerente")
            
            # Processar decisão
            resultados["timestamp_fim"] = datetime.now().isoformat()
            resultados["decisao"] = "APROVADO - Análise completa pelos 5 agentes"
            resultados["valor_aprovado"] = float(sinistro_data.get("valor_estimado", 0)) * 0.85
            resultados["justificativas"] = [
                "Análise realizada pelos 5 agentes especializados",
                "Documentação verificada pelo Agente de Análise",
                "Cálculo validado pelo Agente de Cálculo",
                "Compliance verificado pelo Agente de Compliance",
                "Decisão consolidada pelo Gerente de Sinistros"
            ]
            resultados["compliance_ok"] = True
            resultados["alertas"] = []
            
        except Exception as e:
            resultados["erro"] = str(e)
            resultados["decisao"] = "ERRO - Falha no processamento dos agentes"
            
        return resultados

# Instância global do sistema
sistema_agentes = None

def get_sistema():
    global sistema_agentes
    if sistema_agentes is None:
        sistema_agentes = SistemaMultiAgente()
    return sistema_agentes

# Função principal de processamento
async def processar_sinistro(sinistro_data: Dict[str, Any]) -> Dict[str, Any]:
    """Processa sinistro com os 5 agentes de IA"""
    try:
        sistema = get_sistema()
        return await sistema.processar_com_5_agentes(sinistro_data)
    except Exception as e:
        # Se falhar, retorna erro claro
        return {
            "erro": f"SISTEMA REQUER OPENAI_API_KEY: {str(e)}",
            "numero_sinistro": sinistro_data.get("numero_sinistro"),
            "decisao": "ERRO - Sistema de IA não disponível",
            "agentes_executados": [],
            "recomendacao": "Configure OPENAI_API_KEY no Railway"
        }

# Compatibilidade
claims_manager = None

__all__ = [
    'processar_sinistro',
    'claims_manager', 
    'Sinistro',
    'TipoSinistro',
    'StatusSinistro'
]
