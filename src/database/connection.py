"""
Conexão e sessão do banco de dados
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
import logging
from typing import Generator

from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Criar engine do banco
if settings.ENVIRONMENT == "test":
    # Para testes, usar SQLite em memória
    engine = create_engine("sqlite:///:memory:", poolclass=NullPool)
else:
    # Para produção, usar PostgreSQL com pool
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,  # Verificar conexão antes de usar
        echo=settings.DEBUG,  # Log SQL em debug
    )

# Criar sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obter sessão do banco
    Usar com FastAPI:
    
    @app.post("/")
    def create_item(db: Session = Depends(get_db)):
        ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager para obter sessão do banco
    Usar em scripts e workers:
    
    with get_db_session() as db:
        sinistro = db.query(Sinistro).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Erro na transação do banco: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Inicializar banco de dados - criar tabelas"""
    from .models import Base
    Base.metadata.create_all(bind=engine)
    logger.info("Banco de dados inicializado")

def drop_db():
    """Apagar todas as tabelas - CUIDADO!"""
    from .models import Base
    Base.metadata.drop_all(bind=engine)
    logger.warning("Todas as tabelas foram apagadas!")
