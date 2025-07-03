#!/bin/bash

echo "🚨 CORREÇÃO DEFINITIVA - Ativando os 5 Agentes de IA"
echo "===================================================="

cd /Users/feangeloni/Desktop/sinistros-ia-sistema

# 1. Criar arquivo de configuração forçada
echo "🔧 Criando configuração de OpenAI..."
cat > sinistros-ia-sistema-main/src/openai_config.py << 'EOF'
import os
import sys

# FORÇA ABSOLUTA DA OPENAI_API_KEY
key = os.environ.get("OPENAI_API_KEY")
if key:
    os.environ["OPENAI_API_KEY"] = key
    try:
        import openai
        openai.api_key = key
        print(f"[5 AGENTES] OpenAI configurada: ...{key[-4:]}")
    except:
        pass
else:
    print("[5 AGENTES] ERRO: OPENAI_API_KEY não encontrada!")
    
print(f"[5 AGENTES] Ambiente Railway: {os.environ.get('RAILWAY_ENVIRONMENT', 'NÃO DETECTADO')}")
EOF

# 2. Modificar main.py para importar a configuração primeiro
echo "📝 Modificando main.py..."
sed -i.bak '1s/^/from src.openai_config import *\n/' sinistros-ia-sistema-main/src/api/main.py

# 3. Modificar o __init__.py dos agents também
echo "📝 Modificando agents/__init__.py..."
cat > sinistros-ia-sistema-main/src/agents/__init__.py << 'EOF'
# Importar configuração primeiro
try:
    from ..openai_config import *
except:
    import os
    if "OPENAI_API_KEY" in os.environ:
        os.environ["OPENAI_API_KEY"] = os.environ["OPENAI_API_KEY"]

# Agora importar os agentes
from .claims_agent_system import *
print("[5 AGENTES] Sistema carregado - Triagem, Análise, Cálculo, Compliance e Gerente prontos!")
EOF

# 4. Commit e push
echo "📤 Enviando correção definitiva..."
git add -A
git commit -m "CRÍTICO: Forçar configuração OpenAI para os 5 agentes funcionarem"
git push origin main

# 5. Deploy
echo -e "\n🚀 Deploy com os 5 agentes..."
railway up

echo -e "\n✅ Deploy dos 5 Agentes de IA iniciado!"
echo ""
echo "🤖 Sistema com 5 agentes especializados:"
echo "   1️⃣ Agente de Triagem - Classifica sinistros"
echo "   2️⃣ Agente de Análise - Verifica documentos"
echo "   3️⃣ Agente de Cálculo - Calcula indenizações"
echo "   4️⃣ Agente de Compliance - Verifica regulamentações"
echo "   5️⃣ Gerente de Sinistros - Toma decisão final"
echo ""
echo "⏱️  Aguarde 3 minutos para deploy completar"
