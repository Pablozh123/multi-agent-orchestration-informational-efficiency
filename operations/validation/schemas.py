"""Pydantic-Modelle fuer die Core-Tabellen der thesis.db.

Stufe 1 der dreistufigen Validierungs-Pipeline (CLAUDE.md v2.1 §6.1).
Jedes Modell entspricht einer Zeile in der jeweiligen SQLite-Tabelle.
Spaltennamen folgen exakt dem Schema in init_db.py — nicht den Beispielen
in CLAUDE.md v2.1 §6.2 (siehe Migrations-Plan: whale_transactions ist
in Wirklichkeit whale_trades, sentiment_scores.tone ist sentiment usw.).
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ISO 8601 sanity check used by several models. We accept any string that
# pandas/python can parse as a UTC-aware datetime; deeper format checks
# happen in pandera (Stufe 2).
def _ensure_iso_utc(value: str) -> str:
    """Verifiziert, dass `value` als ISO 8601-UTC-Zeitstempel parsebar ist."""
    from datetime import datetime

    if not isinstance(value, str):
        raise TypeError(f"timestamp must be str, got {type(value).__name__}")
    # Accept Z or +00:00 suffix; reject naive timestamps
    candidate = value.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"not an ISO 8601 timestamp: {value!r}") from exc
    return value


class PolymarketPriceRow(BaseModel):
    """Eine Zeile aus polymarket_prices."""

    id: Optional[int] = None
    price_timestamp: str
    fetched_at: str
    market_id: str
    token_id: Optional[str] = None
    price: float = Field(ge=0.0, le=1.0)
    volume_24h: Optional[float] = None
    best_bid: Optional[float] = None
    best_ask: Optional[float] = None

    @field_validator("price_timestamp", "fetched_at")
    @classmethod
    def _check_iso(cls, v: str) -> str:
        return _ensure_iso_utc(v)


class WhaleTradeRow(BaseModel):
    """Eine Zeile aus whale_trades (echter Tabellenname, nicht whale_transactions)."""

    id: Optional[int] = None
    price_timestamp: str
    tx_hash: Optional[str] = None
    wallet_address: str = Field(min_length=42, max_length=42)
    market_id: Optional[str] = None
    direction: Literal["BUY", "SELL"]
    amount_usd: float = Field(gt=0.0)
    token_id: Optional[str] = None
    price_at_trade: Optional[float] = None

    @field_validator("wallet_address")
    @classmethod
    def _lowercase(cls, v: str) -> str:
        if v != v.lower():
            raise ValueError(f"wallet_address must be lowercase: {v!r}")
        if not v.startswith("0x"):
            raise ValueError(f"wallet_address must start with 0x: {v!r}")
        return v

    @field_validator("price_timestamp")
    @classmethod
    def _check_iso(cls, v: str) -> str:
        return _ensure_iso_utc(v)


class PollForecastRow(BaseModel):
    """Eine Zeile aus poll_forecasts."""

    id: Optional[int] = None
    date: str
    source: str
    candidate: str
    probability: float = Field(ge=0.0, le=1.0)
    poll_type: Optional[str] = None


class SentimentScoreRow(BaseModel):
    """Eine Zeile aus sentiment_scores. Spalte heisst `sentiment`, nicht `tone`."""

    id: Optional[int] = None
    timestamp: str
    source: str
    topic: Optional[str] = None
    sentiment: float = Field(ge=-100.0, le=100.0)
    volume: Optional[int] = None
    raw_text_sample: Optional[str] = None

    @field_validator("timestamp")
    @classmethod
    def _check_iso(cls, v: str) -> str:
        return _ensure_iso_utc(v)


class EventsTimelineRow(BaseModel):
    """Eine Zeile aus events_timeline."""

    id: Optional[int] = None
    event_timestamp: str
    event_type: str
    event_category: Optional[str] = None
    description: Optional[str] = None
    impact_score: Optional[float] = None

    @field_validator("event_timestamp")
    @classmethod
    def _check_iso(cls, v: str) -> str:
        return _ensure_iso_utc(v)


class MarketMakerExclusionRow(BaseModel):
    """Eine Zeile aus market_maker_exclusions."""

    id: Optional[int] = None
    wallet_address: str = Field(min_length=42, max_length=42)
    label: Optional[str] = None
    source: Optional[str] = None
    added_at: str

    @field_validator("wallet_address")
    @classmethod
    def _lowercase(cls, v: str) -> str:
        if v != v.lower() or not v.startswith("0x"):
            raise ValueError(f"wallet_address must be lowercase 0x...: {v!r}")
        return v


# Registry mapping table_name -> Pydantic row model. Used by validators.py
# and report.py to pick the right schema for each SQLite table.
TABLE_TO_MODEL = {
    "polymarket_prices": PolymarketPriceRow,
    "whale_trades": WhaleTradeRow,
    "poll_forecasts": PollForecastRow,
    "sentiment_scores": SentimentScoreRow,
    "events_timeline": EventsTimelineRow,
    "market_maker_exclusions": MarketMakerExclusionRow,
}
