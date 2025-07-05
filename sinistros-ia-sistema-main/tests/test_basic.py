"""Testes básicos para o sistema de sinistros"""

def test_basic():
    """Teste básico para verificar setup"""
    assert True

def test_import_agents():
    """Testa se consegue importar o módulo de agentes"""
    try:
        from src.agents import claims_agent_system
        assert True
    except ImportError:
        assert False, "Não foi possível importar o módulo de agentes"

def test_import_api():
    """Testa se consegue importar o módulo da API"""
    try:
        from src.api import main
        assert hasattr(main, 'app')
    except ImportError:
        assert False, "Não foi possível importar o módulo da API"


def test_agent_models_use_env_vars(monkeypatch):
    """Verifica se os agentes usam variáveis de ambiente para o modelo"""
    monkeypatch.setenv("OPENAI_MODEL", "modelo-teste")
    monkeypatch.setenv("OPENAI_MODEL_FALLBACK", "modelo-reserva")
    import types, sys
    class Dummy:
        def __init__(self, *args, model=None, **kwargs):
            self.model = model
    monkeypatch.setitem(sys.modules, "swarm", types.SimpleNamespace(Agent=Dummy, Swarm=Dummy))
    monkeypatch.setitem(sys.modules, "dotenv", types.SimpleNamespace(load_dotenv=lambda: None))
    import importlib
    module = importlib.import_module("src.agents.claims_agent_system")
    importlib.reload(module)
    assert module.triage_agent.model == "modelo-teste"
    assert module.calculation_agent.model == "modelo-teste"
