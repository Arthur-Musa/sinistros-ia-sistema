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
