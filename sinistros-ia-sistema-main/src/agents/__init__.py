# Importar configuração primeiro
try:
    from ..openai_config import *
except:
    import os
    if "OPENAI_API_KEY" in os.environ:
        os.environ["OPENAI_API_KEY"] = os.environ["OPENAI_API_KEY"]

# Agora importar os agentes
from .claims_agent_system import *
print("[5 AGENTES] Sistema carregado - Triagem, Análise, Cálculo, Compliance e Gerente prontos!")
