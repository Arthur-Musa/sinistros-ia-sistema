"""
Modelos de banco de dados para o sistema de sinistros
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class StatusSinistro(enum.Enum):
    """Status possíveis de um sinistro"""
    RECEBIDO = "recebido"
    TRIAGEM = "triagem"
    EM_ANALISE = "em_analise"
    DOCUMENTACAO_PENDENTE = "documentacao_pendente"
    EM_CALCULO = "em_calculo"
    EM_COMPLIANCE = "em_compliance"
    APROVADO = "aprovado"
    NEGADO = "negado"
    CANCELADO = "cancelado"
    FINALIZADO = "finalizado"

class TipoSinistro(enum.Enum):
    """Tipos de sinistro"""
    AUTOMOVEL = "automovel"
    RESIDENCIAL = "residencial"
    VIDA = "vida"
    EMPRESARIAL = "empresarial"
    SAUDE = "saude"
    VIAGEM = "viagem"
    OUTROS = "outros"

class Sinistro(Base):
    """Modelo principal de sinistro"""
    __tablename__ = "sinistros"
    
    id = Column(Integer, primary_key=True, index=True)
    numero_sinistro = Column(String(50), unique=True, index=True, nullable=False)
    
    # Status e tipo
    status = Column(SQLEnum(StatusSinistro), default=StatusSinistro.RECEBIDO, nullable=False)
    tipo = Column(SQLEnum(TipoSinistro), nullable=True)
    
    # Datas
    data_ocorrencia = Column(DateTime, nullable=False)
    data_aviso = Column(DateTime, default=func.now(), nullable=False)
    data_criacao = Column(DateTime, default=func.now(), nullable=False)
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now())
    data_conclusao = Column(DateTime, nullable=True)
    
    # Segurado
    segurado_nome = Column(String(200), nullable=False)
    segurado_documento = Column(String(50), nullable=False, index=True)
    segurado_telefone = Column(String(30))
    segurado_email = Column(String(200))
    
    # Apólice
    apolice_numero = Column(String(50), nullable=False, index=True)
    apolice_produto = Column(String(100))
    apolice_vigencia_inicio = Column(DateTime)
    apolice_vigencia_fim = Column(DateTime)
    
    # Detalhes do sinistro
    descricao = Column(Text, nullable=False)
    local_ocorrencia = Column(String(500))
    valor_estimado = Column(Float, default=0.0)
    valor_aprovado = Column(Float, default=0.0)
    
    # Origem e canal
    canal_origem = Column(String(50))  # web, mobile, telefone, presencial
    sistema_origem = Column(String(100))  # sistema legado que enviou
    
    # Metadados
    metadata = Column(JSON, default={})
    
    # Relacionamentos
    analises = relationship("Analise", back_populates="sinistro", cascade="all, delete-orphan")
    documentos = relationship("Documento", back_populates="sinistro", cascade="all, delete-orphan")
    historico = relationship("HistoricoSinistro", back_populates="sinistro", cascade="all, delete-orphan")
    webhooks = relationship("WebhookLog", back_populates="sinistro", cascade="all, delete-orphan")

class Analise(Base):
    """Análises realizadas pelos agentes"""
    __tablename__ = "analises"
    
    id = Column(Integer, primary_key=True, index=True)
    sinistro_id = Column(Integer, ForeignKey("sinistros.id"), nullable=False)
    
    # Informações da análise
    agente = Column(String(50), nullable=False)  # qual agente executou
    tipo_analise = Column(String(50), nullable=False)  # triagem, documentacao, calculo, etc
    
    # Timestamps
    data_inicio = Column(DateTime, default=func.now())
    data_fim = Column(DateTime)
    duracao_segundos = Column(Integer)
    
    # Resultados
    resultado = Column(JSON, nullable=False)  # resultado estruturado da análise
    decisao = Column(String(50))  # aprovado, negado, pendente
    confianca = Column(Float)  # 0-1 score de confiança
    justificativas = Column(JSON, default=[])
    alertas = Column(JSON, default=[])
    
    # Status
    sucesso = Column(Boolean, default=True)
    erro_mensagem = Column(Text)
    
    # Relacionamento
    sinistro = relationship("Sinistro", back_populates="analises")

class Documento(Base):
    """Documentos anexados ao sinistro"""
    __tablename__ = "documentos"
    
    id = Column(Integer, primary_key=True, index=True)
    sinistro_id = Column(Integer, ForeignKey("sinistros.id"), nullable=False)
    
    # Informações do documento
    nome = Column(String(200), nullable=False)
    tipo = Column(String(50))  # pdf, imagem, video
    categoria = Column(String(50))  # boletim, foto, orcamento, laudo
    
    # Armazenamento
    caminho_s3 = Column(String(500))  # caminho no S3
    tamanho_bytes = Column(Integer)
    hash_md5 = Column(String(32))
    
    # Metadados
    data_upload = Column(DateTime, default=func.now())
    validado = Column(Boolean, default=False)
    observacoes = Column(Text)
    
    # Relacionamento
    sinistro = relationship("Sinistro", back_populates="documentos")

class HistoricoSinistro(Base):
    """Histórico de mudanças no sinistro"""
    __tablename__ = "historico_sinistros"
    
    id = Column(Integer, primary_key=True, index=True)
    sinistro_id = Column(Integer, ForeignKey("sinistros.id"), nullable=False)
    
    # Informações da mudança
    data = Column(DateTime, default=func.now())
    usuario = Column(String(100))  # quem fez a mudança
    acao = Column(String(50), nullable=False)  # status_alterado, documento_adicionado, etc
    
    # Detalhes
    status_anterior = Column(String(50))
    status_novo = Column(String(50))
    descricao = Column(Text)
    dados_adicionais = Column(JSON, default={})
    
    # Relacionamento
    sinistro = relationship("Sinistro", back_populates="historico")

class WebhookLog(Base):
    """Log de webhooks enviados"""
    __tablename__ = "webhook_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    sinistro_id = Column(Integer, ForeignKey("sinistros.id"), nullable=False)
    
    # Informações do webhook
    url = Column(String(500), nullable=False)
    evento = Column(String(50), nullable=False)  # sinistro.criado, analise.concluida, etc
    
    # Tentativa
    data_envio = Column(DateTime, default=func.now())
    tentativas = Column(Integer, default=1)
    
    # Resposta
    status_code = Column(Integer)
    resposta = Column(Text)
    sucesso = Column(Boolean, default=False)
    erro = Column(Text)
    
    # Payload
    payload = Column(JSON)
    
    # Relacionamento
    sinistro = relationship("Sinistro", back_populates="webhooks")

class FilaProcessamento(Base):
    """Fila de processamento para análises"""
    __tablename__ = "fila_processamento"
    
    id = Column(Integer, primary_key=True, index=True)
    sinistro_numero = Column(String(50), nullable=False, index=True)
    
    # Status da fila
    status = Column(String(50), default="aguardando")  # aguardando, processando, concluido, erro
    prioridade = Column(Integer, default=5)  # 1-10, onde 1 é mais prioritário
    
    # Timestamps
    data_entrada = Column(DateTime, default=func.now())
    data_inicio_processamento = Column(DateTime)
    data_fim_processamento = Column(DateTime)
    
    # Controle
    tentativas = Column(Integer, default=0)
    max_tentativas = Column(Integer, default=3)
    proxima_tentativa = Column(DateTime)
    
    # Erro
    erro_mensagem = Column(Text)
    
    # Task ID (Celery)
    task_id = Column(String(100), unique=True)
