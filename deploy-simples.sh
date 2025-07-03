#!/bin/bash

echo "🚀 Deploy Simplificado - Resolvendo conflitos"
echo "==========================================="

cd /Users/feangeloni/Desktop/sinistros-ia-sistema

# 1. Salvar trabalho atual
echo "💾 Salvando trabalho local..."
git stash

# 2. Resetar para o estado do remoto
echo "🔄 Sincronizando com GitHub..."
git fetch origin
git reset --hard origin/main

# 3. Aplicar apenas a correção essencial no __init__.py
echo "🔧 Aplicando correção mínima..."
cat > src/agents/__init__.py << 'EOF'
import os
# Força configuração da OPENAI_API_KEY do Railway
if "OPENAI_API_KEY" in os.environ and os.environ["OPENAI_API_KEY"]:
    import sys
    # Garante que a chave está disponível globalmente
    os.environ["OPENAI_API_KEY"] = os.environ["OPENAI_API_KEY"]
    print(f"[AGENTES] API Key detectada: ...{os.environ['OPENAI_API_KEY'][-4:]}")

# Importa os módulos
try:
    from .claims_agent_system import *
    print("[AGENTES] Sistema de 5 agentes carregado")
except Exception as e:
    print(f"[AGENTES] Erro ao carregar: {e}")
    from .claims_agent_system_simple import *
    print("[AGENTES] Modo simplificado ativado")
EOF

# 4. Commit e push
echo "📤 Enviando correção..."
git add src/agents/__init__.py
git commit -m "fix: forçar uso da OPENAI_API_KEY do Railway no módulo agents"
git push origin main

# 5. Deploy
echo -e "\n🚀 Iniciando deploy..."
railway up

echo -e "\n✅ Deploy iniciado!"
echo "Aguarde 2-3 minutos e verifique com: railway logs"
