#!/bin/bash

# Script de inicialização para Railway

# Criar diretórios necessários
mkdir -p logs uploads

# Inicializar banco de dados
echo "Inicializando banco de dados..."
python -m src.database.connection init_db

# Detectar qual serviço iniciar baseado na variável RAILWAY_SERVICE_NAME
case "$RAILWAY_SERVICE_NAME" in
  "worker")
    echo "Iniciando Celery Worker..."
    exec celery -A src.workers.celery_app worker --loglevel=info -Q default,analise,webhooks
    ;;
  "beat")
    echo "Iniciando Celery Beat..."
    exec celery -A src.workers.celery_app beat --loglevel=info
    ;;
  "flower")
    echo "Iniciando Flower..."
    exec celery -A src.workers.celery_app flower --port=${PORT:-5555}
    ;;
  *)
    echo "Iniciando API..."
    exec uvicorn src.api.main_production:app --host 0.0.0.0 --port ${PORT:-8000}
    ;;
esac
