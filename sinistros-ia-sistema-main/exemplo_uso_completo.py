#!/usr/bin/env python3
"""
Exemplo completo de como usar o Sistema de Agentes de Sinistros
"""

import requests
import json
import time
from datetime import datetime

# URL base da API
BASE_URL = "http://localhost:8000"

def criar_sinistro():
    """Cria um novo sinistro na API"""
    print("📝 Criando novo sinistro...")
    
    # Dados do sinistro - estes serão analisados pelos agentes
    sinistro = {
        "data_ocorrencia": "2024-01-15",
        "segurado_nome": "Maria Santos",
        "segurado_documento": "987.654.321-00",
        "segurado_telefone": "(21) 99876-5432",
        "apolice_numero": "APL-2024-PREMIUM-001",
        "descricao": """
        Colisão traseira em semáforo. Veículo parado foi atingido por outro veículo.
        Danos na traseira incluindo: para-choque, porta-malas e lanterna traseira.
        Boletim de ocorrência registrado. Terceiro assumiu culpa no local.
        Fotos dos danos e documentação completa disponível.
        """,
        "documentos": [
            "boletim_ocorrencia.pdf",
            "fotos_veiculo_traseira.jpg",
            "fotos_veiculo_lateral.jpg",
            "declaracao_terceiro.pdf",
            "orcamento_oficina.pdf"
        ],
        "valor_estimado": 12500.00
    }
    
    response = requests.post(f"{BASE_URL}/sinistros", json=sinistro)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Sinistro criado: {data['numero_sinistro']}")
        print(f"   Status: {data['status']}")
        print(f"   Próximos passos:")
        for passo in data['proximos_passos']:
            print(f"   - {passo}")
        return data['numero_sinistro']
    else:
        print(f"❌ Erro ao criar sinistro: {response.text}")
        return None

def iniciar_analise_agentes(numero_sinistro):
    """Inicia a análise do sinistro pelos agentes de IA"""
    print(f"\n🤖 Iniciando análise pelos agentes de IA...")
    print("   Os seguintes agentes serão acionados:")
    print("   1. 📋 Agente de Triagem - Classifica o tipo e urgência")
    print("   2. 🔍 Agente de Análise - Verifica documentação e valida informações")
    print("   3. 💰 Agente de Cálculo - Calcula indenização baseado na apólice")
    print("   4. ⚖️ Agente de Compliance - Verifica conformidade regulatória")
    print("   5. 👔 Gerente de Sinistros - Orquestra todo processo e toma decisão final")
    
    response = requests.post(f"{BASE_URL}/sinistros/{numero_sinistro}/analisar")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Análise iniciada!")
        print(f"   Tempo estimado: {data['tempo_estimado']}")
        return True
    else:
        print(f"❌ Erro ao iniciar análise: {response.text}")
        return False

def verificar_status_analise(numero_sinistro):
    """Verifica o status da análise em andamento"""
    print(f"\n📊 Verificando status da análise...")
    
    response = requests.get(f"{BASE_URL}/sinistros/{numero_sinistro}/status")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Status do sinistro: {data['status_sinistro']}")
        print(f"   Análise em andamento: {data['analise_em_andamento']}")
        
        if 'analise' in data:
            print(f"   Status da análise: {data['analise']['status']}")
            if data['analise']['status'] == 'concluida':
                print(f"   ✅ Análise concluída!")
                return True
        return False
    else:
        print(f"❌ Erro ao verificar status: {response.text}")
        return False

def obter_resultado_analise(numero_sinistro):
    """Obtém o resultado completo da análise dos agentes"""
    print(f"\n📄 Obtendo resultado da análise...")
    
    # Primeiro verifica o sinistro atualizado
    response = requests.get(f"{BASE_URL}/sinistros/{numero_sinistro}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n🎯 RESULTADO DA ANÁLISE DOS AGENTES:")
        print(f"   Número: {data['numero_sinistro']}")
        print(f"   Status Final: {data['status']}")
        print(f"   Tipo de Sinistro: {data.get('tipo', 'A ser determinado')}")
        
        if 'analise_completa' in data:
            analise = data['analise_completa']
            print(f"\n   📊 Decisão dos Agentes:")
            print(f"   {analise.get('mensagem', 'Análise em processamento')}")
            
    # Tenta obter relatório se disponível
    response = requests.get(f"{BASE_URL}/sinistros/{numero_sinistro}/relatorio")
    if response.status_code == 200:
        relatorio = response.json()
        print(f"\n   💼 Relatório Detalhado:")
        print(f"   - Decisão: {relatorio['decisao']}")
        print(f"   - Valor Aprovado: R$ {relatorio.get('valor_aprovado', 0):,.2f}")
        print(f"   - Compliance: {'✅ OK' if relatorio['compliance_ok'] else '❌ Pendências'}")
        
        if relatorio['justificativas']:
            print(f"\n   📋 Justificativas:")
            for just in relatorio['justificativas']:
                print(f"   - {just}")
                
        if relatorio['alertas']:
            print(f"\n   ⚠️ Alertas:")
            for alerta in relatorio['alertas']:
                print(f"   - {alerta}")

def exemplo_fluxo_completo():
    """Executa o fluxo completo de análise de sinistro"""
    print("=" * 60)
    print("🚀 DEMONSTRAÇÃO DO SISTEMA DE AGENTES DE SINISTROS")
    print("=" * 60)
    
    # Passo 1: Criar sinistro
    numero_sinistro = criar_sinistro()
    if not numero_sinistro:
        return
    
    time.sleep(2)
    
    # Passo 2: Iniciar análise pelos agentes
    # IMPORTANTE: Precisa ter OPENAI_API_KEY configurada no .env
    print("\n⚠️  NOTA: Para análise real com IA, configure OPENAI_API_KEY no arquivo .env")
    print("   Sem a chave, a análise retornará um erro ou resultado simulado")
    
    if iniciar_analise_agentes(numero_sinistro):
        # Passo 3: Aguardar processamento
        print("\n⏳ Aguardando processamento pelos agentes...")
        tentativas = 0
        max_tentativas = 10
        
        while tentativas < max_tentativas:
            time.sleep(3)
            if verificar_status_analise(numero_sinistro):
                break
            tentativas += 1
            print(f"   Ainda processando... ({tentativas}/{max_tentativas})")
        
        # Passo 4: Obter resultado
        obter_resultado_analise(numero_sinistro)
    
    print("\n" + "=" * 60)
    print("✅ Demonstração concluída!")
    print("\n💡 Como funciona:")
    print("1. O sinistro é criado com todas informações necessárias")
    print("2. A API aciona o sistema multi-agente para análise")
    print("3. Cada agente analisa sua área específica:")
    print("   - Triagem: classifica tipo e urgência")
    print("   - Análise: verifica documentos e valida dados")
    print("   - Cálculo: determina valor da indenização")
    print("   - Compliance: verifica conformidade legal")
    print("   - Gerente: toma decisão final integrando todas análises")
    print("4. O resultado é disponibilizado com justificativas detalhadas")

if __name__ == "__main__":
    try:
        # Verifica se API está rodando
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            exemplo_fluxo_completo()
        else:
            print("❌ API não está respondendo")
    except requests.exceptions.ConnectionError:
        print("❌ Erro: API não está rodando!")
        print("   Execute primeiro: python src/api/main.py")
    except Exception as e:
        print(f"❌ Erro: {e}")
