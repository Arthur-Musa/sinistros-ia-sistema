# Sistema Multi-Agente para Análise de Sinistros de Seguros
# Desenvolvido com OpenAI Agents SDK

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json
import os
from openai import OpenAI
from pydantic import BaseModel
from swarm import Agent, Swarm
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Modelos configuráveis
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
FALLBACK_MODEL = os.getenv("OPENAI_MODEL_FALLBACK", "gpt-4o-mini")

# ===== MODELOS DE DADOS =====

class TipoSinistro(str, Enum):
    """Tipos de sinistro suportados pelo sistema"""
    AUTOMOVEL = "automovel"
    RESIDENCIAL = "residencial"
    VIDA = "vida"
    EMPRESARIAL = "empresarial"
    SAUDE = "saude"

class StatusSinistro(str, Enum):
    """Status possíveis do sinistro"""
    TRIAGEM = "triagem"
    EM_ANALISE = "em_analise"
    DOCUMENTACAO_PENDENTE = "documentacao_pendente"
    APROVADO = "aprovado"
    NEGADO = "negado"
    EM_PAGAMENTO = "em_pagamento"
    FINALIZADO = "finalizado"

class Sinistro(BaseModel):
    """Modelo de dados do sinistro"""
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

# ===== FERRAMENTAS CUSTOMIZADAS =====

def classificar_sinistro(descricao: str, documentos: List[str]) -> Dict[str, Any]:
    """Classifica o tipo de sinistro baseado na descrição e documentos"""
    return {
        "tipo_identificado": None,  # Será preenchido pelo LLM
        "confianca": 0.0,
        "justificativa": "",
        "documentos_necessarios": []
    }

def analisar_documentacao(sinistro: Dict[str, Any]) -> Dict[str, Any]:
    """Analisa a documentação fornecida"""
    return {
        "documentos_presentes": [],
        "documentos_faltantes": [],
        "autenticidade": "pendente",
        "observacoes": [],
        "score_completude": 0.0
    }

def consultar_apolice(numero_apolice: str) -> Dict[str, Any]:
    """Consulta informações da apólice no sistema"""
    # Simulação de consulta ao banco de dados
    return {
        "numero": numero_apolice,
        "vigente": True,
        "coberturas": [],
        "franquia": 0.0,
        "limite_indenizacao": 0.0,
        "carencia": False
    }

def calcular_indenizacao(sinistro: Dict[str, Any], apolice: Dict[str, Any]) -> Dict[str, Any]:
    """Calcula o valor da indenização"""
    return {
        "valor_base": 0.0,
        "deducoes": {},
        "acrescimos": {},
        "valor_final": 0.0,
        "memoria_calculo": "",
        "observacoes": []
    }

def verificar_compliance(sinistro: Dict[str, Any]) -> Dict[str, Any]:
    """Verifica conformidade com regulamentações"""
    return {
        "susep_ok": True,
        "lgpd_ok": True,
        "prazos_ok": True,
        "documentacao_ok": True,
        "alertas": [],
        "recomendacoes": []
    }

def consultar_historico_segurado(cpf_cnpj: str) -> Dict[str, Any]:
    """Consulta histórico do segurado"""
    return {
        "sinistros_anteriores": 0,
        "score_risco": "baixo",
        "alertas_fraude": False,
        "observacoes": []
    }

def gerar_relatorio_final(sinistro: Dict[str, Any]) -> Dict[str, Any]:
    """Gera relatório consolidado da análise"""
    return {
        "resumo_executivo": "",
        "decisao_recomendada": "",
        "valor_recomendado": 0.0,
        "justificativas": [],
        "proximos_passos": [],
        "timestamp": datetime.now().isoformat()
    }

# ===== SISTEMA SWARM =====
# Cliente Swarm será inicializado sob demanda
swarm_client = None

def get_swarm_client():
    """Retorna o cliente Swarm, inicializando se necessário"""
    global swarm_client
    if swarm_client is None:
        swarm_client = Swarm()
    return swarm_client

# ===== AGENTES ESPECIALIZADOS =====

# 1. AGENTE DE TRIAGEM
triage_agent = Agent(
    name="AgenteTriagem",
    model=DEFAULT_MODEL,
    instructions="""Você é um Agente de Triagem especializado em sinistros de seguros.
    
    Suas responsabilidades:
    1. Classificar o tipo de sinistro (automóvel, residencial, vida, empresarial, saúde)
    2. Validar informações básicas do sinistro
    3. Identificar documentação necessária
    4. Determinar prioridade do caso
    5. Fazer triagem inicial de possíveis fraudes
    
    Analise cuidadosamente a descrição e documentos fornecidos.
    Seja preciso na classificação e justifique suas decisões.
    """,
    tools=[classificar_sinistro, consultar_historico_segurado]
)

# 2. AGENTE DE ANÁLISE
analysis_agent = Agent(
    name="AgenteAnalise",
    model=DEFAULT_MODEL,
    instructions="""Você é um Agente de Análise de Sinistros especializado.
    
    Suas responsabilidades:
    1. Analisar toda documentação fornecida
    2. Verificar autenticidade e completude dos documentos
    3. Identificar inconsistências ou informações faltantes
    4. Avaliar evidências (fotos, vídeos, laudos)
    5. Consultar informações da apólice
    6. Recomendar investigação adicional se necessário
    
    Seja minucioso e objetivo. Documente todas as observações.
    Considere aspectos técnicos específicos do tipo de sinistro.
    """,
    tools=[analisar_documentacao, consultar_apolice]
)

# 3. AGENTE DE CÁLCULO
calculation_agent = Agent(
    name="AgenteCalculo",
    model=DEFAULT_MODEL,
    instructions="""Você é um Agente de Cálculo de Indenizações especializado.
    
    Suas responsabilidades:
    1. Calcular valor base da indenização conforme apólice
    2. Aplicar franquias e deduções cabíveis
    3. Verificar limites de cobertura
    4. Considerar depreciação quando aplicável
    5. Calcular juros e correção monetária se necessário
    6. Apresentar memória de cálculo detalhada
    
    Use as coberturas e limites da apólice.
    Seja transparente em todos os cálculos.
    Considere a legislação brasileira aplicável.
    """,
    tools=[calcular_indenizacao, consultar_apolice]
)

# 4. AGENTE DE COMPLIANCE
compliance_agent = Agent(
    name="AgenteCompliance",
    model=DEFAULT_MODEL,
    instructions="""Você é um Agente de Compliance especializado em seguros.
    
    Suas responsabilidades:
    1. Verificar conformidade com normas SUSEP
    2. Garantir cumprimento da LGPD
    3. Validar prazos regulamentares
    4. Identificar necessidade de comunicação a autoridades
    5. Verificar documentação obrigatória
    6. Alertar sobre riscos regulatórios
    
    Conheça profundamente a regulamentação de seguros brasileira.
    Seja rigoroso mas pragmático.
    Priorize proteção da empresa e do segurado.
    """,
    tools=[verificar_compliance]
)

# 5. AGENTE GERENTE DE SINISTROS (Orquestrador)
claims_manager = Agent(
    name="GerenteSinistros",
    model=DEFAULT_MODEL,
    instructions="""Você é o Gerente de Sinistros responsável por orquestrar todo o processo 
    de análise de sinistros de seguros.
    
    Suas responsabilidades:
    1. Coordenar o trabalho de todos os agentes especializados
    2. Garantir que cada etapa do processo seja executada corretamente
    3. Consolidar as análises e tomar a decisão final
    4. Garantir conformidade com regulamentações
    5. Otimizar o processo para eficiência e satisfação do cliente
    
    Processo de trabalho:
    - Use o agente de triagem para classificar o sinistro
    - Acione o agente de análise para verificar documentação
    - Solicite cálculo de indenização quando aplicável
    - Verifique compliance antes de finalizar
    - Consolide tudo em uma decisão final clara e justificada
    
    Seja justo, transparente e eficiente.
    Priorize a experiência do segurado mantendo os interesses da seguradora.
    """,
    functions=[
        classificar_sinistro,
        analisar_documentacao,
        calcular_indenizacao,
        verificar_compliance,
        gerar_relatorio_final
    ]
)

# ===== FUNÇÕES DE EXECUÇÃO =====

def processar_sinistro(sinistro_data: Dict[str, Any]) -> Dict[str, Any]:
    """Processa um sinistro completo através do sistema multi-agente"""
    
    # Preparar mensagem inicial com dados do sinistro
    mensagem_inicial = f"""
    Novo sinistro recebido para análise:
    
    Número: {sinistro_data['numero_sinistro']}
    Data Ocorrência: {sinistro_data['data_ocorrencia']}
    Data Aviso: {sinistro_data['data_aviso']}
    
    Segurado:
    - Nome: {sinistro_data['segurado']['nome']}
    - CPF/CNPJ: {sinistro_data['segurado']['documento']}
    
    Apólice:
    - Número: {sinistro_data['apolice']['numero']}
    - Produto: {sinistro_data['apolice']['produto']}
    
    Descrição do Sinistro:
    {sinistro_data['descricao']}
    
    Documentos Apresentados:
    {', '.join(sinistro_data['documentos'])}
    
    Por favor, realize a análise completa deste sinistro.
    """
    
    # Executar o gerente de sinistros usando Swarm
    client = get_swarm_client()
    response = client.run(
        agent=claims_manager,
        messages=[{"role": "user", "content": mensagem_inicial}]
    )
    
    # Extrair resultado
    resultado = {
        "mensagem": response.messages[-1]["content"],
        "agent_usado": response.agent.name if response.agent else "Desconhecido",
        "sinistro_numero": sinistro_data['numero_sinistro']
    }
    
    return resultado

# ===== EXEMPLO DE USO =====

if __name__ == "__main__":
    # Exemplo de sinistro para teste
    sinistro_exemplo = {
        "numero_sinistro": "2024-AUTO-123456",
        "data_ocorrencia": "2024-03-15",
        "data_aviso": "2024-03-16",
        "segurado": {
            "nome": "João Silva",
            "documento": "123.456.789-00",
            "telefone": "(11) 98765-4321"
        },
        "apolice": {
            "numero": "APO-2023-987654",
            "produto": "Auto Premium",
            "vigencia_inicio": "2023-01-01",
            "vigencia_fim": "2024-12-31"
        },
        "descricao": """
        Colisão frontal em cruzamento. Segurado alega que o sinal estava verde.
        Danos significativos na parte frontal do veículo. Airbags acionados.
        Segurado e passageiro sofreram ferimentos leves, atendidos no local.
        Boletim de ocorrência registrado. Outro veículo envolvido.
        """,
        "documentos": [
            "Boletim de Ocorrência",
            "CNH do segurado",
            "CRLV do veículo",
            "Fotos dos danos",
            "Orçamento de reparo",
            "Laudo médico do atendimento"
        ],
        "valor_estimado": 45000.00
    }
    
    # Processar sinistro
    # resultado = asyncio.run(processar_sinistro(sinistro_exemplo))
    # print(json.dumps(resultado, indent=2, ensure_ascii=False))

# ===== CONFIGURAÇÃO ADICIONAL =====

# Para usar em produção, configure:
# 1. Variáveis de ambiente para API keys
# 2. Conexão com banco de dados real
# 3. Integração com sistemas legados
# 4. Sistema de filas para processamento assíncrono
# 5. Monitoramento e logs estruturados
# 6. Webhooks para notificações
# 7. Interface web/API para receber sinistros
