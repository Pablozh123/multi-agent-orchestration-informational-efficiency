"""Market Data Agent (Pydantic AI) — Tier 1, Haiku 4.5.

Dient als typ-sicherer Wrapper um `operations.tools.db_tools` fuer Polymarket-
Preis- und Poll-Abfragen. Der System-Prompt wird aus
`directives/roles/market_agent.md` geladen, damit Rolle und Constraints
als durchsuchbarer Markdown-Artefakt in der Thesis-Dokumentation leben.

Der Agent liefert strukturierten `MarketDataResult`-Output; keine Freitext-
Interpretation. Tool-Calls sind auf die vier in `db_tools.py` registrierten
Funktionen beschraenkt (LIMIT 50 pro Call).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from operations.tools import db_tools

# Load .env so ANTHROPIC_API_KEY is available when the Agent() is instantiated.
load_dotenv()


# --- Output schema -------------------------------------------------------


class MarketDataResult(BaseModel):
    """Strukturierter Output des Market Agents."""

    summary: str = Field(
        description="2–4 Saetze auf Deutsch, akademisch, sachlich."
    )
    price_range: tuple[float, float] = Field(
        description="(min, max) Preis ueber das Zeitfenster, ∈ [0, 1]."
    )
    volatility: float = Field(
        description="7-Tage-Rolling-StdDev des Preises."
    )
    divergences: list[str] = Field(
        default_factory=list,
        description="Konkrete Abweichungen zwischen Markt und Polls.",
    )
    data_sources: list[str] = Field(
        default_factory=list,
        description="Verwendete Tools/Tabellen.",
    )


# --- System prompt loading ----------------------------------------------


_PROMPT_PATH = Path(__file__).parent.parent.parent / "directives" / "roles" / "market_agent.md"


def _load_system_prompt() -> str:
    """Laedt den System-Prompt aus dem Markdown-Artefakt."""
    if not _PROMPT_PATH.exists():
        raise FileNotFoundError(f"market_agent prompt not found at {_PROMPT_PATH}")
    return _PROMPT_PATH.read_text(encoding="utf-8")


# --- Agent instantiation --------------------------------------------------


MODEL_ID = "anthropic:claude-haiku-4-5-20251001"

market_agent = Agent(
    model=MODEL_ID,
    output_type=MarketDataResult,
    system_prompt=_load_system_prompt(),
    retries=2,
)


# --- Tool registration ----------------------------------------------------


@market_agent.tool
def fetch_polymarket_prices(
    ctx: RunContext[None],
    start_date: str,
    end_date: str,
    resolution: str = "daily",
) -> list[dict[str, Any]]:
    """Liefert Polymarket-Preiszeilen fuer ein Zeitfenster (max. 50).

    Args:
        start_date: ISO-Datum YYYY-MM-DD.
        end_date: ISO-Datum YYYY-MM-DD.
        resolution: 'daily' oder 'raw'.
    """
    return db_tools.fetch_polymarket_prices((start_date, end_date), resolution=resolution)


@market_agent.tool
def query_poll_data(
    ctx: RunContext[None],
    start_date: str,
    end_date: str,
    source: str | None = None,
) -> list[dict[str, Any]]:
    """Liefert Poll-Forecasts fuer ein Zeitfenster (max. 50).

    Args:
        start_date: ISO-Datum YYYY-MM-DD.
        end_date: ISO-Datum YYYY-MM-DD.
        source: Optional — 'fivethirtyeight' oder 'rcp'.
    """
    return db_tools.query_poll_data((start_date, end_date), source=source)


@market_agent.tool
def get_market_summary(
    ctx: RunContext[None],
    start_date: str,
    end_date: str,
) -> dict[str, Any]:
    """Aggregierte Zusammenfassung der polymarket_prices fuer ein Fenster."""
    return db_tools.generate_data_summary("polymarket_prices", (start_date, end_date))


@market_agent.tool
def get_price_volatility_precomputed(
    ctx: RunContext[None],
) -> list[dict[str, Any]]:
    """Liest die pre-computed 7-Tage-Volatility aus analysis_summaries."""
    return db_tools.get_precomputed_summary("price_volatility")
