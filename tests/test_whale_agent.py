"""Smoke-Tests fuer den Whale Activity Agent."""
from __future__ import annotations

import pytest
from pydantic import ValidationError
from pydantic_ai.models.test import TestModel

from operations.agents.whale_agent import (
    MODEL_ID,
    WhaleActivityResult,
    whale_agent,
)


def test_model_id_is_haiku() -> None:
    assert MODEL_ID == "anthropic:claude-haiku-4-5-20251001"


def test_system_prompt_loaded() -> None:
    prompts = whale_agent._system_prompts
    assert prompts
    joined = " ".join(prompts)
    assert "Whale Activity Agent" in joined
    assert "Polygon" in joined


def test_tools_registered() -> None:
    tool_names = set(whale_agent._function_toolset.tools.keys())
    expected = {
        "query_whale_activity",
        "get_whale_net_volume_summary",
        "get_whale_anomalies",
    }
    assert expected.issubset(tool_names)


def test_output_requires_lowercase_addresses() -> None:
    """top_wallets darf keine Uppercase-Adressen enthalten."""
    with pytest.raises(ValidationError):
        WhaleActivityResult(
            summary="test",
            net_volume_usd=1000.0,
            trade_count=5,
            buy_sell_ratio=1.2,
            anomalies_flagged=[],
            top_wallets=["0xABCDEF1234567890ABCDEF1234567890ABCDEF12"],
            data_sources=["whale_trades"],
        )


def test_output_accepts_lowercase_addresses() -> None:
    result = WhaleActivityResult(
        summary="test",
        net_volume_usd=1000.0,
        trade_count=5,
        buy_sell_ratio=1.2,
        anomalies_flagged=[{"date": "2024-10-15", "z_score": 2.3, "amount_usd": 50000}],
        top_wallets=["0xabcdef1234567890abcdef1234567890abcdef12"],
        data_sources=["whale_trades"],
    )
    assert len(result.top_wallets) == 1


@pytest.mark.asyncio
async def test_agent_runs_with_test_model() -> None:
    with whale_agent.override(model=TestModel()):
        result = await whale_agent.run("Analysiere Whale-Aktivitaet Oktober 2024.")
    assert isinstance(result.output, WhaleActivityResult)
