"""Utilities to build extra context for the claim agents."""
from typing import Dict, Any

from .claims_agent_system import consultar_apolice, consultar_historico_segurado


def coletar_contexto_apolice_e_historico(sinistro: Dict[str, Any]) -> str:
    """Return a text chunk with policy details and prior claim history."""
    numero_apolice = sinistro.get("apolice", {}).get("numero")
    documento = sinistro.get("segurado", {}).get("documento")

    apolice = consultar_apolice(numero_apolice) if numero_apolice else {}
    historico = consultar_historico_segurado(documento) if documento else {}

    partes = []

    if apolice:
        partes.append("Detalhes da Apólice:")
        partes.append(f"  - Número: {apolice.get('numero')}")
        partes.append(f"  - Vigente: {'Sim' if apolice.get('vigente') else 'Não'}")
        if apolice.get("coberturas"):
            partes.append("  - Coberturas: " + ", ".join(apolice["coberturas"]))
        if apolice.get("franquia") is not None:
            partes.append(f"  - Franquia: {apolice['franquia']}")
        if apolice.get("limite_indenizacao") is not None:
            partes.append(f"  - Limite de Indenização: {apolice['limite_indenizacao']}")

    if historico:
        partes.append("\nHistórico do Segurado:")
        partes.append(f"  - Sinistros Anteriores: {historico.get('sinistros_anteriores')}")
        partes.append(f"  - Score de Risco: {historico.get('score_risco')}")
        partes.append(f"  - Alertas de Fraude: {'Sim' if historico.get('alertas_fraude') else 'Não'}")

    return "\n".join(partes)
