"""Pandera-DataFrame-Schemas fuer die Core-Tabellen der thesis.db.

Stufe 2 der dreistufigen Validierungs-Pipeline (CLAUDE.md v2.1 §6.1).
Verifiziert inhaltliche Constraints (Wertebereiche, Format, Eindeutigkeit)
auf Pandas-DataFrames, die aus SQLite gelesen wurden.

Spaltennamen folgen exakt dem Schema in init_db.py — siehe Migrations-Plan
fuer die Diskrepanzen zu CLAUDE.md v2.1 §6.2.
"""
from __future__ import annotations

import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Column, DataFrameSchema


# --- Helper checks --------------------------------------------------------


def _check_iso_utc(series: pd.Series) -> pd.Series:
    """Returns boolean Series: True wenn jeder Wert als UTC-Datetime parsebar ist.

    Handles common formats including 'YYYY-MM-DD HH:MM:SS.sss UTCZ' from Dune.
    """
    # Strip trailing ' UTCZ' / ' UTC' suffixes before parsing
    cleaned = series.astype(str).str.replace(r"\s*UTCZ?\s*$", "", regex=True)
    parsed = pd.to_datetime(cleaned, utc=True, errors="coerce")
    return parsed.notna()


def _check_lowercase_hex42(series: pd.Series) -> pd.Series:
    """Returns boolean Series: True wenn jeder Wert eine lowercase 0x...42-Adresse ist."""
    return series.str.match(r"^0x[0-9a-f]{40}$", na=False)


_iso_utc_check = pa.Check(
    _check_iso_utc,
    element_wise=False,
    error="value not parseable as ISO 8601 UTC timestamp",
)

_lowercase_addr_check = pa.Check(
    _check_lowercase_hex42,
    element_wise=False,
    error="wallet_address not lowercase 42-char hex (0x...)",
)


# --- Schemas --------------------------------------------------------------


polymarket_prices_schema = DataFrameSchema(
    columns={
        "id": Column(int, nullable=True, required=False),
        "price_timestamp": Column(str, checks=_iso_utc_check),
        "fetched_at": Column(str, checks=_iso_utc_check),
        "market_id": Column(str),
        "token_id": Column(str, nullable=True),
        "price": Column(float, checks=pa.Check.in_range(0.0, 1.0)),
        "volume_24h": Column(float, nullable=True),
        "best_bid": Column(float, nullable=True),
        "best_ask": Column(float, nullable=True),
    },
    strict=False,
    coerce=True,
)


whale_trades_schema = DataFrameSchema(
    columns={
        "id": Column(int, nullable=True, required=False),
        "price_timestamp": Column(str, checks=_iso_utc_check),
        "tx_hash": Column(str, nullable=True),
        "wallet_address": Column(str, checks=_lowercase_addr_check),
        "market_id": Column(str, nullable=True),
        "direction": Column(str, checks=pa.Check.isin(["BUY", "SELL"])),
        "amount_usd": Column(float, checks=pa.Check.greater_than(0.0)),
        "token_id": Column(str, nullable=True),
        "price_at_trade": Column(float, nullable=True),
    },
    strict=False,
    coerce=True,
)


poll_forecasts_schema = DataFrameSchema(
    columns={
        "id": Column(int, nullable=True, required=False),
        "date": Column(str),
        "source": Column(str),
        "candidate": Column(str),
        "probability": Column(float, checks=pa.Check.in_range(0.0, 1.0)),
        "poll_type": Column(str, nullable=True),
    },
    strict=False,
    coerce=True,
)


sentiment_scores_schema = DataFrameSchema(
    columns={
        "id": Column(int, nullable=True, required=False),
        "timestamp": Column(str, checks=_iso_utc_check),
        "source": Column(str),
        "topic": Column(str, nullable=True),
        "sentiment": Column(float, checks=pa.Check.in_range(-100.0, 100.0)),
        "volume": Column(int, nullable=True),
        "raw_text_sample": Column(str, nullable=True),
    },
    strict=False,
    coerce=True,
)


events_timeline_schema = DataFrameSchema(
    columns={
        "id": Column(int, nullable=True, required=False),
        "event_timestamp": Column(str, checks=_iso_utc_check),
        "event_type": Column(str),
        "event_category": Column(str, nullable=True),
        "description": Column(str, nullable=True),
        "impact_score": Column(float, nullable=True),
    },
    strict=False,
    coerce=True,
)


market_maker_exclusions_schema = DataFrameSchema(
    columns={
        "id": Column(int, nullable=True, required=False),
        "wallet_address": Column(str, checks=_lowercase_addr_check),
        "label": Column(str, nullable=True),
        "source": Column(str, nullable=True),
        "added_at": Column(str),
    },
    strict=False,
    coerce=True,
)


# Registry mapping table_name -> pandera schema. Used by report.py.
TABLE_TO_SCHEMA = {
    "polymarket_prices": polymarket_prices_schema,
    "whale_trades": whale_trades_schema,
    "poll_forecasts": poll_forecasts_schema,
    "sentiment_scores": sentiment_scores_schema,
    "events_timeline": events_timeline_schema,
    "market_maker_exclusions": market_maker_exclusions_schema,
}
