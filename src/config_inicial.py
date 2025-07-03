"""
Configuração inicial do sistema - DEVE ser importado ANTES de qualquer outro módulo
"""
import os
import sys

# CONFIGURAÇÃO CRÍTICA: Forçar uso da OPENAI_API_KEY
api_key = os.environ.get("OPENAI_API_KEY", "")

if api_key:
    # Garantir que está disponível em todos os lugares possíveis
    os.environ["OPENAI_API_KEY"] = api_key
    
    # Configurar para a biblioteca openai
    try:
        import openai
        openai.api_key = api_key
        print(f"[CONFIG] OpenAI configurada com sucesso: ...{api_key[-4:]}")
    except:
        pass
    
    # Configurar variável global
    __builtins__['OPENAI_API_KEY'] = api_key
else:
    print("[CONFIG] AVISO: OPENAI_API_KEY não encontrada!")

# Verificar outras variáveis importantes
print(f"[CONFIG] Ambiente: {os.environ.get('ENVIRONMENT', 'development')}")
print(f"[CONFIG] Railway: {'SIM' if os.environ.get('RAILWAY_ENVIRONMENT') else 'NÃO'}")
