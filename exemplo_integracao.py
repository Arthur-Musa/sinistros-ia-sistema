#!/usr/bin/env python3
"""
Exemplo de integração com sistema existente
"""

import requests
from datetime import datetime

API_BASE = "http://localhost:8000"

# 1. Simular recebimento de sinistro do sistema legado
def integrar_sinistro_legado():
    dados = {
        "PolicyNumber": "APL-2024-12345",
        "ClaimDate": datetime.now().isoformat(),
        "InsuredName": "Maria Silva",
        "InsuredDocument": "987.654.321-00",
        "InsuredPhone": "11988887777",
        "InsuredEmail": "maria.silva@email.com",
        "Description": "Colisão traseira em cruzamento",
        "Location": "Av. Paulista, 1000 - São Paulo/SP",
        "EstimatedAmount": 8500.00
    }
    
    # Enviar para API
    resp = requests.post(f"{API_BASE}/integrations/legacy/claim", json=dados)
    
    if resp.status_code == 200:
        result = resp.json()
        print(f"✅ Sinistro criado: {result['claim_number']}")
        return result['claim_number']
    else:
        print(f"❌ Erro: {resp.text}")
        return None

# 2. Verificar status
def verificar_status(numero_sinistro):
    resp = requests.get(f"{API_BASE}/integrations/claim/{numero_sinistro}/status")
    
    if resp.status_code == 200:
        status = resp.json()
        print(f"\n📊 Status do Sinistro {numero_sinistro}:")
        print(f"   Status: {status['status']}")
        print(f"   Segurado: {status['insured_name']}")
        
        if status.get('analysis'):
            print(f"   Análise: {status['analysis']['status']}")
            print(f"   Decisão: {status['analysis']['decision']}")
            print(f"   Score Risco: {status['analysis']['risk_score']}")
    else:
        print(f"❌ Erro ao buscar status")

# 3. Registrar webhook
def registrar_webhook():
    webhook_data = {
        "url": "https://seu-sistema.com/webhook/sinistros",
        "events": ["analise.concluida", "decisao.tomada"],
        "secret": "seu-secret-webhook"
    }
    
    resp = requests.post(f"{API_BASE}/integrations/webhook/register", json=webhook_data)
    
    if resp.status_code == 200:
        print("✅ Webhook registrado com sucesso")
    else:
        print(f"❌ Erro ao registrar webhook: {resp.text}")

if __name__ == "__main__":
    print("🚀 Exemplo de Integração com Sistema de Sinistros IA\n")
    
    # Criar sinistro
    numero = integrar_sinistro_legado()
    
    if numero:
        # Aguardar processamento
        import time
        print("\n⏳ Aguardando análise dos agentes...")
        time.sleep(5)
        
        # Verificar status
        verificar_status(numero)
        
        # Registrar webhook
        print("\n🔔 Registrando webhook para notificações...")
        registrar_webhook()
