"""Pydantic row schemas for deterministic thesis data validation."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


def _ensure_datetime(value: str) -> str:
    """Return `value` if it is a non-empty string parseable as a datetime."""
    if not isinstance(value, str):
        raise TypeError(f"date value must be str, got {type(value).__name__}")

    candidate = value.strip()
    if not candidate:
        raise ValueError("date value must be a non-empty parseable datetime string")

    candidate = re.sub(r"\s*UTCZ?\s*$", "", candidate)
    candidate = candidate.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"date value is not parseable as datetime: {value!r}") from exc
    return value


class PolymarketPriceRow(BaseModel):
    """One row from polymarket_prices."""

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
    def _check_datetime(cls, value: str) -> str:
        return _ensure_datetime(value)


class WhaleTradeRow(BaseModel):
    """One row from whale_trades."""

    id: Optional[int] = None
    price_timestamp: str
    tx_hash: Optional[str] = None
    wallet_address: str = Field(min_length=42, max_length=42)
    market_id: Optional[str] = None
    direction: Literal["BUY", "SELL"]
    amount_usd: float = Field(gt=0.0)
    token_id: Optional[str] = None
    price_at_trade: Optional[float] = None

    @field_validator("price_timestamp")
    @classmethod
    def _check_datetime(cls, value: str) -> str:
        return _ensure_datetime(value)

    @field_validator("wallet_address")
    @classmethod
    def _check_wallet(cls, value: str) -> str:
        if value != value.lower():
            raise ValueError(f"wallet_address must be lowercase: {value!r}")
        if not value.startswith("0x"):
            raise ValueError(f"wallet_address must start with 0x: {value!r}")
        return value


class PollForecastRow(BaseModel):
    """One row from poll_forecasts."""

    id: Optional[int] = None
    date: str
    source: str
    candidate: str
    probability: float = Field(ge=0.0, le=1.0)
    poll_type: Optional[str] = None

    @field_validator("date")
    @classmethod
    def _check_date(cls, value: str) -> str:
        return _ensure_datetime(value)


class SentimentScoreRow(BaseModel):
    """One row from sentiment_scores.

    The source concept is tone. The current SQLite column is `sentiment`, so the
    model accepts either `tone` or `sentiment` and normalizes to `sentiment`.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: Optional[int] = None
    timestamp: str
    source: str
    topic: Optional[str] = None
    sentiment: float = Field(
        validation_alias=AliasChoices("sentiment", "tone"),
        ge=-100.0,
        le=100.0,
    )
    volume: Optional[int] = None
    raw_text_sample: Optional[str] = None

    @field_validator("timestamp")
    @classmethod
    def _check_datetime(cls, value: str) -> str:
        return _ensure_datetime(value)


class EventsTimelineRow(BaseModel):
    """One row from events_timeline."""

    id: Optional[int] = None
    event_id: Optional[str] = None
    event_date: Optional[str] = None
    event_time_utc: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    source_url: Optional[str] = None
    expected_direction: Optional[str] = None
    relevance_score: Optional[float] = None
    created_at: Optional[str] = None
    # Compatibility fields from the first deterministic schema.
    event_timestamp: Optional[str] = None
    event_category: Optional[str] = None
    impact_score: Optional[float] = None

    @field_validator("event_timestamp", "event_date", "created_at")
    @classmethod
    def _check_datetime_if_present(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return _ensure_datetime(value)


class MarketMakerExclusionRow(BaseModel):
    """One row from market_maker_exclusions."""

    id: Optional[int] = None
    wallet_address: str = Field(min_length=42, max_length=42)
    label: Optional[str] = None
    source: Optional[str] = None
    added_at: str

    @field_validator("wallet_address")
    @classmethod
    def _check_wallet(cls, value: str) -> str:
        if value != value.lower() or not value.startswith("0x"):
            raise ValueError(f"wallet_address must be lowercase 0x...: {value!r}")
        return value

    @field_validator("added_at")
    @classmethod
    def _check_added_at(cls, value: str) -> str:
        return _ensure_datetime(value)


TABLE_TO_MODEL = {
    "polymarket_prices": PolymarketPriceRow,
    "whale_trades": WhaleTradeRow,
    "poll_forecasts": PollForecastRow,
    "sentiment_scores": SentimentScoreRow,
    "events_timeline": EventsTimelineRow,
    "market_maker_exclusions": MarketMakerExclusionRow,
}
