import os
from types import SimpleNamespace
from unittest.mock import patch

from src.agents.claims_agent_system import processar_sinistro


SAMPLE_SINISTRO = {
    "numero_sinistro": "SIN-001",
    "data_ocorrencia": "2024-01-01",
    "data_aviso": "2024-01-02",
    "segurado": {"nome": "Joao", "documento": "00000000000"},
    "apolice": {"numero": "AP-1", "produto": "Auto"},
    "descricao": "Teste de sinistro",
    "documentos": ["doc1.pdf"],
    "valor_estimado": 1000.0,
}


def test_processar_sinistro(monkeypatch):
    """Verifica retorno básico de processar_sinistro."""
    if not os.getenv("OPENAI_API_KEY"):
        class DummySwarm:
            def run(self, agent=None, messages=None):
                return SimpleNamespace(
                    messages=[{"content": "Stub"}],
                    agent=SimpleNamespace(name="dummy")
                )
        monkeypatch.setattr(
            "src.agents.claims_agent_system.get_swarm_client",
            lambda: DummySwarm()
        )

    resultado = processar_sinistro(SAMPLE_SINISTRO)

    assert isinstance(resultado, dict)
    for chave in ("mensagem", "agent_usado", "sinistro_numero"):
        assert chave in resultado
