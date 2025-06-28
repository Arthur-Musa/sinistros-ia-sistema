"""
Configurações centralizadas para ambiente de produção
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Configurações do sistema"""
    
    # Ambiente
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # API Keys
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    
    # Banco de Dados
    DATABASE_URL: str = "postgresql://user:pass@localhost/sinistros_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    # Redis (para filas e cache)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_QUEUE_DB: int = 1
    REDIS_CACHE_DB: int = 2
    
    # Celery (processamento assíncrono)
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list = ["json"]
    
    # Sistema Legado
    LEGACY_SYSTEM_URL: str = "https://api.sistema-legado.com"
    LEGACY_SYSTEM_API_KEY: str = ""
    LEGACY_SYSTEM_TIMEOUT: int = 30
    
    # Webhooks
    WEBHOOK_SECRET: str = ""
    WEBHOOK_TIMEOUT: int = 10
    WEBHOOK_MAX_RETRIES: int = 3
    
    # Monitoramento
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    
    # Logs
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = "/var/log/sinistros/app.log"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    API_RATE_LIMIT: str = "100/minute"
    API_CORS_ORIGINS: list = ["*"]
    
    # Segurança
    SECRET_KEY: str = ""
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AWS (para armazenamento de documentos)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    
    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "noreply@sinistros.com"
    
    # Limites do Sistema
    MAX_FILE_SIZE_MB: int = 10
    MAX_ANALYSIS_TIME_SECONDS: int = 300
    MAX_CONCURRENT_ANALYSES: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Retorna instância única das configurações"""
    return Settings()

# Configurações por ambiente
ENVIRONMENT_CONFIGS = {
    "development": {
        "DEBUG": True,
        "LOG_LEVEL": "DEBUG",
        "DATABASE_URL": "postgresql://dev:dev@localhost/sinistros_dev"
    },
    "staging": {
        "DEBUG": False,
        "LOG_LEVEL": "INFO",
        "DATABASE_URL": "postgresql://staging:pass@staging-db/sinistros_staging"
    },
    "production": {
        "DEBUG": False,
        "LOG_LEVEL": "WARNING",
        "DATABASE_URL": os.getenv("DATABASE_URL"),
        "SENTRY_DSN": os.getenv("SENTRY_DSN"),
    }
}
