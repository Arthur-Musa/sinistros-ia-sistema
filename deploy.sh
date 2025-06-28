#!/bin/bash

echo "🚀 Deploy do Sistema de Sinistros no Railway"
echo "==========================================="
echo ""

# Verificar se está no diretório correto
if [ ! -f "railway.json" ]; then
    echo "❌ Erro: Execute este script do diretório do projeto!"
    exit 1
fi

echo "✅ Railway CLI já está instalado"
echo ""

# Instruções para login
echo "📝 PASSO 1: Login no Railway"
echo "----------------------------"
echo "Execute o comando abaixo (ele abrirá o navegador):"
echo ""
echo "  railway login"
echo ""
echo "Após fazer login, volte aqui e pressione ENTER para continuar..."
read -p ""

# Criar projeto
echo ""
echo "🔧 PASSO 2: Criar Projeto"
echo "-------------------------"
echo "Criando projeto 'sinistros-ia-sistema'..."
railway init -n sinistros-ia-sistema

if [ $? -ne 0 ]; then
    echo "❌ Erro ao criar projeto. Tentando conectar a projeto existente..."
    railway link
fi

echo ""
echo "✅ Projeto configurado!"

# Configurar variáveis
echo ""
echo "🔑 PASSO 3: Configurar Variáveis de Ambiente"
echo "--------------------------------------------"
echo ""
read -p "Digite sua OPENAI_API_KEY: " OPENAI_KEY

echo ""
echo "Configurando variáveis..."
railway variables set OPENAI_API_KEY="$OPENAI_KEY"
railway variables set ENVIRONMENT=production
railway variables set API_WORKERS=4

echo "✅ Variáveis configuradas!"

# Deploy
echo ""
echo "🚀 PASSO 4: Deploy"
echo "------------------"
echo "Iniciando deploy (isso pode levar 2-3 minutos)..."
echo ""

railway up

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ DEPLOY CONCLUÍDO COM SUCESSO!"
    echo ""
    echo "📋 Informações do seu sistema:"
    railway status
    echo ""
    echo "🌐 Para abrir no navegador: railway open"
    echo "📊 Para ver logs: railway logs"
    echo ""
else
    echo "❌ Erro no deploy. Verifique os logs com: railway logs"
fi
