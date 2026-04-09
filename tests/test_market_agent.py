"""Smoke-Tests fuer den Market Data Agent.

Nutzt pydantic_ai.models.test.TestModel — KEIN Live-API-Call an Anthropic.
Verifiziert dass System-Prompt geladen, Tools registriert und Output-
Schema validierbar ist.
"""
from __future__ import annotations

import pytest
from pydantic_ai.models.test import TestModel

from operations.agents.market_agent import (
    MarketDataResult,
    MODEL_ID,
    market_agent,
)


def test_model_id_is_haiku() -> None:
    """Market Agent laeuft auf Haiku 4.5 (Tier 1)."""
    assert MODEL_ID == "anthropic:claude-haiku-4-5-20251001"


def test_system_prompt_loaded() -> None:
    """System-Prompt wird aus directives/roles/market_agent.md geladen."""
    prompts = market_agent._system_prompts
    assert len(prompts) >= 1
    joined = " ".join(prompts)
    assert "Market Data Agent" in joined
    assert "Polymarket" in joined


def test_tools_registered() -> None:
    """Alle vier db_tools-Wrapper sind am Agent registriert."""
    tool_names = set(market_agent._function_toolset.tools.keys())
    expected = {
        "fetch_polymarket_prices",
        "query_poll_data",
        "get_market_summary",
        "get_price_volatility_precomputed",
    }
    assert expected.issubset(tool_names), (
        f"missing tools: {expected - tool_names}"
    )


def test_output_schema_validates() -> None:
    """MarketDataResult validiert ein gueltiges Beispiel."""
    result = MarketDataResult(
        summary="Der Markt zeigte im Oktober 2024 eine klare Aufwaertsbewegung.",
        price_range=(0.48, 0.67),
        volatility=0.023,
        divergences=["Poll-Markt-Luecke waechst ab Mitte Oktober auf 8 Punkte."],
        data_sources=["polymarket_prices", "poll_forecasts"],
    )
    assert result.price_range == (0.48, 0.67)
    assert result.volatility == 0.023
    assert len(result.divergences) == 1


@pytest.mark.asyncio
async def test_agent_runs_with_test_model() -> None:
    """Agent laeuft gegen TestModel ohne Live-API-Call.

    TestModel gibt strukturierten Dummy-Output zurueck — wir pruefen
    lediglich dass der Run ohne Exception durchlaeuft und ein
    MarketDataResult-Objekt liefert.
    """
    with market_agent.override(model=TestModel()):
        result = await market_agent.run("Analysiere die Marktdaten fuer Oktober 2024.")
    assert isinstance(result.output, MarketDataResult)
