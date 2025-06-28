"""
Sistema de monitoramento e métricas
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager
import json

# Importações opcionais para diferentes sistemas de monitoramento
try:
    import sentry_sdk
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

try:
    from prometheus_client import Counter, Histogram, Gauge, Info
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Inicializar Sentry se disponível
if SENTRY_AVAILABLE and settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )
    logger.info("Sentry inicializado")

# Métricas Prometheus se disponível
if PROMETHEUS_AVAILABLE and settings.PROMETHEUS_ENABLED:
    # Contadores
    sinistros_criados = Counter('sinistros_criados_total', 'Total de sinistros criados', ['canal', 'tipo'])
    sinistros_processados = Counter('sinistros_processados_total', 'Total de sinistros processados', ['status', 'agente'])
    webhooks_enviados = Counter('webhooks_enviados_total', 'Total de webhooks enviados', ['evento', 'sucesso'])
    erros_sistema = Counter('erros_sistema_total', 'Total de erros do sistema', ['tipo', 'componente'])
    
    # Histogramas
    tempo_processamento = Histogram('tempo_processamento_sinistro_segundos', 'Tempo de processamento de sinistros', ['tipo'])
    tempo_resposta_api = Histogram('tempo_resposta_api_segundos', 'Tempo de resposta da API', ['endpoint', 'metodo'])
    
    # Gauges
    fila_tamanho = Gauge('fila_processamento_tamanho', 'Tamanho atual da fila de processamento')
    sinistros_em_analise = Gauge('sinistros_em_analise', 'Número de sinistros em análise')
    
    # Info
    sistema_info = Info('sistema_sinistros', 'Informações do sistema')
    sistema_info.info({
        'versao': '1.0.0',
        'ambiente': settings.ENVIRONMENT
    })

class MetricsCollector:
    """Coletor de métricas centralizado"""
    
    def __init__(self):
        self.metrics_buffer = []
        self.start_times = {}
    
    def track_counter(self, metric_name: str, value: float = 1, labels: Optional[Dict[str, str]] = None):
        """Registra um contador"""
        if PROMETHEUS_AVAILABLE and settings.PROMETHEUS_ENABLED:
            if metric_name == "sinistros_criados":
                sinistros_criados.labels(**labels).inc(value)
            elif metric_name == "sinistros_processados":
                sinistros_processados.labels(**labels).inc(value)
            elif metric_name == "webhooks_enviados":
                webhooks_enviados.labels(**labels).inc(value)
            elif metric_name == "erros_sistema":
                erros_sistema.labels(**labels).inc(value)
        
        # Log estruturado
        logger.info(f"Métrica: {metric_name}", extra={
            "metric_type": "counter",
            "metric_name": metric_name,
            "value": value,
            "labels": labels
        })
    
    def track_histogram(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Registra um histograma"""
        if PROMETHEUS_AVAILABLE and settings.PROMETHEUS_ENABLED:
            if metric_name == "tempo_processamento":
                tempo_processamento.labels(**labels).observe(value)
            elif metric_name == "tempo_resposta_api":
                tempo_resposta_api.labels(**labels).observe(value)
        
        # Log estruturado
        logger.info(f"Métrica: {metric_name}", extra={
            "metric_type": "histogram",
            "metric_name": metric_name,
            "value": value,
            "labels": labels
        })
    
    def track_gauge(self, metric_name: str, value: float):
        """Registra um gauge"""
        if PROMETHEUS_AVAILABLE and settings.PROMETHEUS_ENABLED:
            if metric_name == "fila_tamanho":
                fila_tamanho.set(value)
            elif metric_name == "sinistros_em_analise":
                sinistros_em_analise.set(value)
        
        # Log estruturado
        logger.info(f"Métrica: {metric_name}", extra={
            "metric_type": "gauge",
            "metric_name": metric_name,
            "value": value
        })
    
    def start_timer(self, timer_name: str):
        """Inicia um timer"""
        self.start_times[timer_name] = time.time()
    
    def end_timer(self, timer_name: str, metric_name: str, labels: Optional[Dict[str, str]] = None):
        """Finaliza um timer e registra o tempo"""
        if timer_name in self.start_times:
            duration = time.time() - self.start_times[timer_name]
            self.track_histogram(metric_name, duration, labels)
            del self.start_times[timer_name]
            return duration
        return 0

# Instância global do coletor
metrics_collector = MetricsCollector()

# Funções de conveniência
def track_metric(name: str, value: Any, labels: Optional[Dict[str, str]] = None):
    """Registra uma métrica genérica"""
    if isinstance(value, (int, float)):
        metrics_collector.track_counter(name, value, labels)
    else:
        # Para métricas complexas, enviar como log estruturado
        logger.info(f"Métrica: {name}", extra={
            "metric_name": name,
            "value": value,
            "labels": labels
        })

def track_error(error_type: str, exception: Exception, context: Optional[Dict[str, Any]] = None):
    """Registra um erro"""
    # Sentry
    if SENTRY_AVAILABLE and settings.SENTRY_DSN:
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            sentry_sdk.capture_exception(exception)
    
    # Prometheus
    metrics_collector.track_counter("erros_sistema", 1, {
        "tipo": error_type,
        "componente": context.get("componente", "unknown") if context else "unknown"
    })
    
    # Log estruturado
    logger.error(f"Erro: {error_type}", extra={
        "error_type": error_type,
        "exception": str(exception),
        "context": context
    }, exc_info=True)

@contextmanager
def track_time(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """Context manager para medir tempo de execução"""
    timer_name = f"{metric_name}_{time.time()}"
    metrics_collector.start_timer(timer_name)
    
    try:
        yield
    finally:
        metrics_collector.end_timer(timer_name, metric_name, labels)

def log_structured(level: str, message: str, **kwargs):
    """Log estruturado em JSON"""
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message,
        **kwargs
    }
    
    if settings.LOG_FORMAT == "json":
        logger.log(
            getattr(logging, level.upper()),
            json.dumps(log_data)
        )
    else:
        logger.log(
            getattr(logging, level.upper()),
            message,
            extra=kwargs
        )

# Middleware para FastAPI
class MetricsMiddleware:
    """Middleware para coletar métricas da API"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()
            
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    duration = time.time() - start_time
                    
                    # Registrar métrica
                    metrics_collector.track_histogram(
                        "tempo_resposta_api",
                        duration,
                        {
                            "endpoint": scope["path"],
                            "metodo": scope["method"]
                        }
                    )
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)
