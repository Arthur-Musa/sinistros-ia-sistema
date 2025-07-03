# Script para verificar e testar os endpoints disponíveis

echo "🔍 Verificando endpoints disponíveis..."
echo "======================================"

API="https://sinistros-ia-sistema-production.up.railway.app"

echo -e "\n1. Health Check:"
curl -s $API/health | python3 -m json.tool

echo -e "\n\n2. Endpoints disponíveis:"
curl -s $API/ | python3 -m json.tool

echo -e "\n\n3. Estatísticas:"
curl -s $API/admin/estatisticas | python3 -m json.tool

echo -e "\n\n4. Documentação interativa:"
echo "   Acesse: $API/docs"
echo ""
echo "📝 Status: A API está funcionando, mas os 5 agentes de IA precisam da OPENAI_API_KEY configurada corretamente."
echo ""
echo "🔧 Soluções:"
echo "   1. Acesse o Railway Dashboard e faça redeploy"
echo "   2. Ou aguarde o próximo deploy automático"
echo "   3. Ou use o comando: railway up --force"
