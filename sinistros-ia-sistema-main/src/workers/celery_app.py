"""
Configuração do Celery para processamento assíncrono
"""

from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
import logging
from datetime import datetime

from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Criar aplicação Celery
celery_app = Celery(
    "sinistros_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["src.workers.tasks"]  # Módulos com tasks
)

# Configuração
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    timezone="America/Sao_Paulo",
    enable_utc=True,
    
    # Configurações de retry
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,  # 60 segundos
    task_max_retries=3,
    
    # Configurações de performance
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Configurações de roteamento
    task_routes={
        "src.workers.tasks.processar_sinistro_async": {"queue": "analise"},
        "src.workers.tasks.enviar_webhook": {"queue": "webhooks"},
        "src.workers.tasks.gerar_relatorio": {"queue": "relatorios"},
    },
    
    # Configurações de fila
    task_default_queue="default",
    task_queues={
        "default": {
            "exchange": "default",
            "exchange_type": "direct",
            "routing_key": "default"
        },
        "analise": {
            "exchange": "analise",
            "exchange_type": "direct",
            "routing_key": "analise",
            "priority": 10  # Alta prioridade
        },
        "webhooks": {
            "exchange": "webhooks",
            "exchange_type": "direct",
            "routing_key": "webhooks",
            "priority": 5
        },
        "relatorios": {
            "exchange": "relatorios",
            "exchange_type": "direct",
            "routing_key": "relatorios",
            "priority": 1  # Baixa prioridade
        }
    }
)

# Configurar beats (tarefas agendadas)
celery_app.conf.beat_schedule = {
    "limpar-filas-antigas": {
        "task": "src.workers.tasks.limpar_filas_antigas",
        "schedule": 3600.0,  # A cada hora
    },
    "reprocessar-falhas": {
        "task": "src.workers.tasks.reprocessar_sinistros_falhos",
        "schedule": 300.0,  # A cada 5 minutos
    },
    "gerar-metricas": {
        "task": "src.workers.tasks.gerar_metricas_sistema",
        "schedule": 60.0,  # A cada minuto
    }
}

# Signals para monitoramento
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    """Log quando task inicia"""
    logger.info(f"Task iniciada: {task.name} [{task_id}]")

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, result=None, **kwargs):
    """Log quando task termina"""
    logger.info(f"Task concluída: {task.name} [{task_id}]")

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    """Log quando task falha"""
    logger.error(f"Task falhou: {sender.name} [{task_id}] - {exception}")

if __name__ == "__main__":
    # Para executar: celery -A src.workers.celery_app worker --loglevel=info
    celery_app.start()
