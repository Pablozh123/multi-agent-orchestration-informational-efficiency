"""Whale Activity Agent (Pydantic AI) — Tier 1, Haiku 4.5.

Strukturierte Extraktion aus whale_trades + pre-computed Summaries.
Haiku reicht, weil keine qualitative Einordnung noetig ist.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from pydantic_ai import Agent, RunContext

from operations.tools import db_tools

load_dotenv()


# --- Output schema -------------------------------------------------------


class WhaleActivityResult(BaseModel):
    """Strukturierter Output des Whale Agents."""

    summary: str = Field(description="2–4 Saetze, deutsch-akademisch.")
    net_volume_usd: float = Field(description="Netto BUY − SELL in USD.")
    trade_count: int = Field(ge=0)
    buy_sell_ratio: float = Field(
        ge=0.0,
        description="BUY-USD / SELL-USD; 0.0 wenn SELL == 0.",
    )
    anomalies_flagged: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Dicts mit {date, z_score, amount_usd}.",
    )
    top_wallets: list[str] = Field(
        default_factory=list,
        description="Lowercase-Adressen, sortiert nach |Volumen|.",
    )
    data_sources: list[str] = Field(default_factory=list)

    @field_validator("top_wallets")
    @classmethod
    def _lowercase_addresses(cls, v: list[str]) -> list[str]:
        for addr in v:
            if addr != addr.lower():
                raise ValueError(f"wallet address must be lowercase: {addr!r}")
        return v


# --- System prompt loading ----------------------------------------------


_PROMPT_PATH = Path(__file__).parent.parent.parent / "directives" / "roles" / "whale_agent.md"


def _load_system_prompt() -> str:
    if not _PROMPT_PATH.exists():
        raise FileNotFoundError(f"whale_agent prompt not found at {_PROMPT_PATH}")
    return _PROMPT_PATH.read_text(encoding="utf-8")


# --- Agent instantiation --------------------------------------------------


MODEL_ID = "anthropic:claude-haiku-4-5-20251001"

whale_agent = Agent(
    model=MODEL_ID,
    output_type=WhaleActivityResult,
    system_prompt=_load_system_prompt(),
    retries=2,
)


# --- Tools ---------------------------------------------------------------


@whale_agent.tool
def query_whale_activity(
    ctx: RunContext[None],
    wallet: str | None = None,
    week: str | None = None,
    min_usd: float | None = None,
) -> list[dict[str, Any]]:
    """Liefert Whale-Trades (max. 50 Zeilen).

    Args:
        wallet: Optional — lowercase 42-Zeichen Adresse.
        week: Optional — 'YYYY-Www' oder ISO-Datum.
        min_usd: Optional — Schwellwert in USD.
    """
    return db_tools.query_whale_activity(wallet=wallet, week=week, min_usd=min_usd)


@whale_agent.tool
def get_whale_net_volume_summary(
    ctx: RunContext[None],
) -> list[dict[str, Any]]:
    """Liest pre-computed Tages-Netto-Volumen."""
    return db_tools.get_precomputed_summary("whale_net_volume")


@whale_agent.tool
def get_whale_anomalies(
    ctx: RunContext[None],
) -> list[dict[str, Any]]:
    """Liest pre-computed Anomalie-Flags (|z| > 2)."""
    return db_tools.get_precomputed_summary("whale_anomaly")
