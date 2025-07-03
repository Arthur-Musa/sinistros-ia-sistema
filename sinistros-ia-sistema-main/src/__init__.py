import os
import sys

# CONFIGURAÇÃO FORÇADA - Este arquivo DEVE ser importado primeiro em TODOS os módulos
print("[SISTEMA] Configurando variáveis de ambiente...")

# 1. Pegar a chave do ambiente
key = os.environ.get("OPENAI_API_KEY", "")
if key:
    # 2. Garantir que está em TODOS os lugares possíveis
    os.environ["OPENAI_API_KEY"] = key
    
    # 3. Configurar para módulo openai antes de qualquer import
    sys.modules['openai.api_key'] = key
    
    # 4. Adicionar ao path do Python
    if 'OPENAI_API_KEY' not in sys.path:
        sys.path.insert(0, f"OPENAI_API_KEY={key}")
    
    print(f"[SISTEMA] OpenAI configurada com sucesso!")
    print(f"[SISTEMA] 5 Agentes de IA prontos: Triagem, Análise, Cálculo, Compliance e Gerente")
else:
    print("[SISTEMA] ERRO CRÍTICO: OPENAI_API_KEY não encontrada!")
    print("[SISTEMA] Configure no Railway: Settings → Variables → OPENAI_API_KEY")

# Verificar ambiente
print(f"[SISTEMA] Railway detectado: {'SIM' if os.environ.get('RAILWAY_ENVIRONMENT') else 'NÃO'}")
