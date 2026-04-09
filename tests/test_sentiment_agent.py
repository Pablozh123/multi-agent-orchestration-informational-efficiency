"""Smoke-Tests fuer den Sentiment Agent."""
from __future__ import annotations

import pytest
from pydantic_ai.models.test import TestModel

from operations.agents.sentiment_agent import (
    MODEL_ID,
    SentimentAnalysisResult,
    sentiment_agent,
)


def test_model_id_is_sonnet() -> None:
    assert MODEL_ID == "anthropic:claude-sonnet-4-5"


def test_system_prompt_loaded() -> None:
    prompts = sentiment_agent._system_prompts
    assert prompts
    joined = " ".join(prompts)
    assert "Sentiment Agent" in joined
    assert "GDELT" in joined


def test_tools_registered() -> None:
    tool_names = set(sentiment_agent._function_toolset.tools.keys())
    expected = {
        "fetch_sentiment_data",
        "get_sentiment_daily_summary",
        "query_events_in_window",
    }
    assert expected.issubset(tool_names)


def test_output_schema_empty_window() -> None:
    """Edge-Case: leeres Fenster → volume_total=0, trend=neutral."""
    result = SentimentAnalysisResult(
        summary="Keine Artikel im Fenster.",
        tone_range=(0.0, 0.0),
        volume_total=0,
        trend_direction="neutral",
        notable_shifts=[],
        data_sources=["sentiment_scores"],
    )
    assert result.volume_total == 0
    assert result.trend_direction == "neutral"


def test_output_schema_validates_literal() -> None:
    """trend_direction muss einer der vier Literale sein."""
    with pytest.raises(Exception):
        SentimentAnalysisResult(
            summary="test",
            tone_range=(-1.0, 1.0),
            volume_total=10,
            trend_direction="bullish",  # type: ignore[arg-type]
            notable_shifts=[],
            data_sources=[],
        )


@pytest.mark.asyncio
async def test_agent_runs_with_test_model() -> None:
    with sentiment_agent.override(model=TestModel()):
        result = await sentiment_agent.run("Analysiere Sentiment Oktober 2024.")
    assert isinstance(result.output, SentimentAnalysisResult)
