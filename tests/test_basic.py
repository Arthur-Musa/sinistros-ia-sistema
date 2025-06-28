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
