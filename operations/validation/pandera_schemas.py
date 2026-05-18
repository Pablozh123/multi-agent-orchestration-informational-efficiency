"""Pandera DataFrame schemas for deterministic thesis data validation."""
from __future__ import annotations

import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Column, DataFrameSchema


def _check_parseable_datetime(series: pd.Series) -> pd.Series:
    """Return True for values parseable as datetimes."""
    cleaned = series.astype(str).str.strip()
    cleaned = cleaned.str.replace(r"\s*UTCZ?\s*$", "", regex=True)
    cleaned = cleaned.str.replace("Z", "+00:00", regex=False)
    parsed = pd.to_datetime(cleaned, utc=True, errors="coerce")
    return parsed.notna()


def _check_lowercase_hex42(series: pd.Series) -> pd.Series:
    """Return True for lowercase 42-character 0x wallet addresses."""
    return series.str.match(r"^0x[0-9a-f]{40}$", na=False)


datetime_check = pa.Check(
    _check_parseable_datetime,
    element_wise=False,
    error="value not parseable as datetime",
)

wallet_address_check = pa.Check(
    _check_lowercase_hex42,
    element_wise=False,
    error="wallet_address must be lowercase 42-character 0x hex",
)


polymarket_prices_schema = DataFrameSchema(
    columns={
        "id": Column(int, nullable=True, required=False),
        "price_timestamp": Column(str, checks=datetime_check),
        "fetched_at": Column(str, checks=datetime_check),
        "market_id": Column(str),
        "token_id": Column(str, nullable=True, required=False),
        "price": Column(float, checks=pa.Check.in_range(0.0, 1.0)),
        "volume_24h": Column(float, nullable=True, required=False),
        "best_bid": Column(float, nullable=True, required=False),
        "best_ask": Column(float, nullable=True, required=False),
    },
    strict=False,
    coerce=True,
)


whale_trades_schema = DataFrameSchema(
    columns={
        "id": Column(int, nullable=True, required=False),
        "price_timestamp": Column(str, checks=datetime_check),
        "tx_hash": Column(str, nullable=True, required=False),
        "wallet_address": Column(str, checks=wallet_address_check),
        "market_id": Column(str, nullable=True, required=False),
        "direction": Column(str, checks=pa.Check.isin(["BUY", "SELL"])),
        "amount_usd": Column(float, checks=pa.Check.greater_than(0.0)),
        "token_id": Column(str, nullable=True, required=False),
        "price_at_trade": Column(float, nullable=True, required=False),
    },
    strict=False,
    coerce=True,
)


poll_forecasts_schema = DataFrameSchema(
    columns={
        "id": Column(int, nullable=True, required=False),
        "date": Column(str, checks=datetime_check),
        "source": Column(str),
        "candidate": Column(str),
        "probability": Column(float, checks=pa.Check.in_range(0.0, 1.0)),
        "poll_type": Column(str, nullable=True, required=False),
    },
    strict=False,
    coerce=True,
)


sentiment_scores_schema = DataFrameSchema(
    columns={
        "id": Column(int, nullable=True, required=False),
        "timestamp": Column(str, checks=datetime_check),
        "source": Column(str),
        "topic": Column(str, nullable=True, required=False),
        "sentiment": Column(float, checks=pa.Check.in_range(-100.0, 100.0)),
        "volume": Column(int, nullable=True, required=False),
        "raw_text_sample": Column(str, nullable=True, required=False),
    },
    strict=False,
    coerce=True,
)


events_timeline_schema = DataFrameSchema(
    columns={
        "id": Column(int, nullable=True, required=False),
        "event_id": Column(str, nullable=True, required=False),
        "event_date": Column(
            str,
            checks=datetime_check,
            nullable=True,
            required=False,
        ),
        "event_time_utc": Column(str, nullable=True, required=False),
        "title": Column(str, nullable=True, required=False),
        "description": Column(str, nullable=True, required=False),
        "event_type": Column(str, nullable=True, required=False),
        "source_url": Column(str, nullable=True, required=False),
        "expected_direction": Column(str, nullable=True, required=False),
        "relevance_score": Column(float, nullable=True, required=False),
        "created_at": Column(
            str,
            checks=datetime_check,
            nullable=True,
            required=False,
        ),
        "event_timestamp": Column(
            str,
            checks=datetime_check,
            nullable=True,
            required=False,
        ),
        "event_category": Column(str, nullable=True, required=False),
        "impact_score": Column(float, nullable=True, required=False),
    },
    strict=False,
    coerce=True,
)


market_maker_exclusions_schema = DataFrameSchema(
    columns={
        "id": Column(int, nullable=True, required=False),
        "wallet_address": Column(str, checks=wallet_address_check),
        "label": Column(str, nullable=True, required=False),
        "source": Column(str, nullable=True, required=False),
        "added_at": Column(str, checks=datetime_check),
    },
    strict=False,
    coerce=True,
)


TABLE_TO_SCHEMA = {
    "polymarket_prices": polymarket_prices_schema,
    "whale_trades": whale_trades_schema,
    "poll_forecasts": poll_forecasts_schema,
    "sentiment_scores": sentiment_scores_schema,
    "events_timeline": events_timeline_schema,
    "market_maker_exclusions": market_maker_exclusions_schema,
}
