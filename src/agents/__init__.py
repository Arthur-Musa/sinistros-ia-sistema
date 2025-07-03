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
