"""Sentiment Agent (Pydantic AI) — Tier 2, Sonnet 4.5.

Interpretation von GDELT-Tone-Aggregaten. Nutzt qualitative Einordnung
gegen Events, daher Sonnet statt Haiku (siehe CLAUDE.md v2.1 §3.1 Tabelle).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from operations.tools import db_tools

load_dotenv()


# --- Output schema -------------------------------------------------------


class SentimentAnalysisResult(BaseModel):
    """Strukturierter Output des Sentiment Agents."""

    summary: str = Field(description="2–4 Saetze, deutsch-akademisch.")
    tone_range: tuple[float, float] = Field(
        description="(min, max) der Tone-Werte im Fenster, ∈ [-100, 100]."
    )
    volume_total: int = Field(
        ge=0,
        description="Summe der volume-Spalte im Fenster.",
    )
    trend_direction: Literal["positive", "negative", "neutral", "mixed"] = Field(
        description="Qualitative Trend-Einordnung."
    )
    notable_shifts: list[str] = Field(
        default_factory=list,
        description="Auffaellige Aenderungen, jeweils mit Datum.",
    )
    data_sources: list[str] = Field(default_factory=list)


# --- System prompt loading ----------------------------------------------


_PROMPT_PATH = Path(__file__).parent.parent.parent / "directives" / "roles" / "sentiment_agent.md"


def _load_system_prompt() -> str:
    if not _PROMPT_PATH.exists():
        raise FileNotFoundError(f"sentiment_agent prompt not found at {_PROMPT_PATH}")
    return _PROMPT_PATH.read_text(encoding="utf-8")


# --- Agent instantiation --------------------------------------------------


MODEL_ID = "anthropic:claude-sonnet-4-5"

sentiment_agent = Agent(
    model=MODEL_ID,
    output_type=SentimentAnalysisResult,
    system_prompt=_load_system_prompt(),
    retries=2,
)


# --- Tools ---------------------------------------------------------------


@sentiment_agent.tool
def fetch_sentiment_data(
    ctx: RunContext[None],
    start_date: str,
    end_date: str,
    theme: str | None = None,
) -> list[dict[str, Any]]:
    """Liefert Sentiment-Rohdaten (max. 50 Zeilen)."""
    return db_tools.fetch_sentiment_data((start_date, end_date), theme=theme)


@sentiment_agent.tool
def get_sentiment_daily_summary(
    ctx: RunContext[None],
) -> list[dict[str, Any]]:
    """Liest die pre-computed Tages-Aggregate aus analysis_summaries."""
    return db_tools.get_precomputed_summary("sentiment_daily")


@sentiment_agent.tool
def query_events_in_window(
    ctx: RunContext[None],
    start_date: str,
    end_date: str,
    event_type: str | None = None,
) -> list[dict[str, Any]]:
    """Liefert dokumentierte Events im Fenster (events_timeline, max. 50)."""
    return db_tools.query_events_in_window((start_date, end_date), event_type=event_type)
