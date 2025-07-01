#!/usr/bin/env python3
"""
Script de teste simplificado sem usar a API da OpenAI
"""

import requests
import json
from datetime import datetime

# URL base da API
BASE_URL = "http://localhost:8000"

# Dados de teste
sinistro_teste = {
    "data_ocorrencia": "2024-01-15",
    "segurado_nome": "João Silva",
    "segurado_documento": "123.456.789-00",
    "segurado_telefone": "(11) 98765-4321",
    "apolice_numero": "APL-2024-001",
    "descricao": "Colisão frontal em via pública. Veículo apresenta danos no para-choque, capô e faróis. Boletim de ocorrência registrado.",
    "documentos": [
        "boletim_ocorrencia.pdf",
        "fotos_veiculo.jpg",
        "orcamento_reparo.pdf"
    ],
    "valor_estimado": 15000.00
}

def test_health():
    """Testa endpoint de health"""
    print("🏥 Testando health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_create_sinistro():
    """Testa criação de sinistro"""
    print("📝 Criando novo sinistro...")
    response = requests.post(f"{BASE_URL}/sinistros", json=sinistro_teste)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data["numero_sinistro"]
    else:
        print(f"Erro: {response.text}")
    print()

def test_get_sinistro(numero_sinistro):
    """Testa busca de sinistro"""
    print(f"🔍 Buscando sinistro {numero_sinistro}...")
    response = requests.get(f"{BASE_URL}/sinistros/{numero_sinistro}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    else:
        print(f"Erro: {response.text}")
    print()

def test_stats():
    """Testa estatísticas"""
    print("📊 Obtendo estatísticas...")
    response = requests.get(f"{BASE_URL}/admin/estatisticas")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

def test_api_info():
    """Testa endpoint raiz"""
    print("🌐 Testando endpoint raiz...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

if __name__ == "__main__":
    print("🚀 Iniciando testes simplificados da API de Sinistros")
    print("=" * 50)
    
    try:
        test_api_info()
        test_health()
        numero = test_create_sinistro()
        if numero:
            test_get_sinistro(numero)
        test_stats()
        
        print("✅ Testes concluídos!")
        print("\n⚠️  Nota: Este teste não executa análise de sinistros para evitar uso da API OpenAI")
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API.")
        print("Certifique-se de que a API está rodando em http://localhost:8000")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
