#!/bin/bash

echo "🧪 TESTE DOS 5 AGENTES DE IA"
echo "============================"
echo ""

# URL da API
API_URL="https://sinistros-ia-sistema-production.up.railway.app"

# 1. Criar novo sinistro de teste
echo "1️⃣ Criando sinistro de teste..."
RESPONSE=$(curl -s -X POST $API_URL/sinistros \
  -H "Content-Type: application/json" \
  -d '{
    "data_ocorrencia": "2025-07-03",
    "segurado_nome": "Teste 5 Agentes",
    "segurado_documento": "111.222.333-44",
    "segurado_telefone": "(11) 99999-8888",
    "apolice_numero": "APO-5AGENTES-001",
    "descricao": "Colisão traseira em semáforo. Veículo parado foi atingido. Danos na traseira. Whiplash leve. Boletim de ocorrência registrado. Fotos anexadas. Testemunhas presentes.",
    "documentos": ["Boletim de Ocorrência", "CNH", "CRLV", "Fotos dos danos", "Laudo médico", "Declaração testemunha"],
    "valor_estimado": 35000
  }')

NUMERO_SINISTRO=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['numero_sinistro'])")
echo "✅ Sinistro criado: $NUMERO_SINISTRO"
echo ""

# 2. Iniciar análise pelos 5 agentes
echo "2️⃣ Iniciando análise pelos 5 agentes..."
curl -s -X POST $API_URL/sinistros/$NUMERO_SINISTRO/analisar | python3 -m json.tool
echo ""

# 3. Aguardar processamento
echo "⏳ Aguardando 10 segundos para os agentes processarem..."
sleep 10
echo ""

# 4. Verificar status
echo "3️⃣ Verificando status da análise..."
curl -s $API_URL/sinistros/$NUMERO_SINISTRO/status | python3 -m json.tool
echo ""

# 5. Se completo, pegar relatório
echo "4️⃣ Tentando obter relatório final..."
curl -s $API_URL/sinistros/$NUMERO_SINISTRO/relatorio | python3 -m json.tool 2>/dev/null || echo "Análise ainda em andamento ou com erro"
echo ""

echo "5️⃣ Verificando logs do Railway para ver se os agentes foram ativados:"
echo "   Execute: railway logs"
echo ""
echo "Se aparecer '[5 AGENTES]' nos logs, o sistema está funcionando!"
