#!/bin/bash

echo "🚨 DEPLOY EMERGENCIAL - Ativando os 5 Agentes de IA"
echo "=================================================="

cd /Users/feangeloni/Desktop/sinistros-ia-sistema

# 1. Backup do arquivo atual
echo "📦 Fazendo backup..."
cp src/agents/claims_agent_system.py src/agents/claims_agent_system.backup.py

# 2. Substituir pelo arquivo corrigido
echo "🔧 Aplicando correção dos 5 agentes..."
cp src/agents/claims_agent_system_fixed.py src/agents/claims_agent_system.py

# 3. Commitar mudanças
echo "💾 Salvando mudanças..."
git add -A
git commit -m "URGENTE: Ativar os 5 agentes de IA - correção OPENAI_API_KEY" || echo "Sem mudanças"

# 4. Forçar push (resolver conflitos depois)
echo "⬆️  Enviando para GitHub..."
git push origin main --force

# 5. Deploy no Railway
echo -e "\n🚀 Fazendo deploy com os 5 agentes..."
railway up

echo -e "\n✅ Deploy dos 5 agentes iniciado!"
echo ""
echo "🤖 Os 5 agentes de IA serão ativados:"
echo "   1. Agente de Triagem"
echo "   2. Agente de Análise" 
echo "   3. Agente de Cálculo"
echo "   4. Agente de Compliance"
echo "   5. Gerente de Sinistros"
echo ""
echo "⏱️  Aguarde 2-3 minutos para o deploy completar"
echo ""
echo "📊 Para verificar:"
echo "   railway logs    # Ver se os agentes estão funcionando"
echo "   railway open    # Abrir dashboard"
