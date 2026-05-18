"""Tests for deterministic data validation helpers."""
from __future__ import annotations

import pandas as pd
import pytest
from pandera.errors import SchemaError
from pydantic import ValidationError

from operations.validation.pandera_schemas import polymarket_prices_schema
from operations.validation.schemas import (
    PolymarketPriceRow,
    SentimentScoreRow,
    WhaleTradeRow,
)
from operations.validation.validators import (
    validate_dataframe,
    validate_row,
    validate_table_row,
    validate_table_rows,
)


VALID_WALLET = "0x" + "a" * 40


def _valid_price_row() -> dict[str, object]:
    return {
        "price_timestamp": "2024-01-01T00:00:00Z",
        "fetched_at": "2024-01-01T00:05:00Z",
        "market_id": "presidential-2024",
        "token_id": "trump-yes",
        "price": 0.52,
    }


def _valid_whale_row() -> dict[str, object]:
    return {
        "price_timestamp": "2024-01-01 04:24:22.000 UTCZ",
        "tx_hash": "0xabc",
        "wallet_address": VALID_WALLET,
        "market_id": "presidential-2024",
        "direction": "BUY",
        "amount_usd": 1200.0,
        "token_id": "trump-yes",
        "price_at_trade": 0.51,
    }


def _valid_sentiment_row() -> dict[str, object]:
    return {
        "timestamp": "2024-01-01T00:00:00Z",
        "source": "gdelt",
        "topic": "us-election",
        "tone": -2.5,
        "volume": 42,
    }


def test_valid_example_rows_pass_validation() -> None:
    price = validate_row(PolymarketPriceRow, _valid_price_row())
    whale = validate_row(WhaleTradeRow, _valid_whale_row())
    sentiment = validate_row(SentimentScoreRow, _valid_sentiment_row())

    assert price.price == 0.52
    assert whale.amount_usd == 1200.0
    assert sentiment.sentiment == -2.5


def test_validate_table_rows_normalizes_tone_to_sentiment() -> None:
    df = validate_table_rows("sentiment_scores", [_valid_sentiment_row()])

    assert list(df["sentiment"]) == [-2.5]
    assert "tone" not in df.columns


def test_invalid_price_fails_validation() -> None:
    row = _valid_price_row() | {"price": 1.2}

    with pytest.raises(ValidationError, match="price"):
        validate_row(PolymarketPriceRow, row)


def test_invalid_amount_usd_fails_validation() -> None:
    row = _valid_whale_row() | {"amount_usd": 0.0}

    with pytest.raises(ValidationError, match="amount_usd"):
        validate_row(WhaleTradeRow, row)


def test_invalid_tone_fails_validation() -> None:
    row = _valid_sentiment_row() | {"tone": -101.0}

    with pytest.raises(ValidationError, match="greater than or equal to -100"):
        validate_row(SentimentScoreRow, row)


def test_invalid_wallet_address_length_fails_validation() -> None:
    row = _valid_whale_row() | {"wallet_address": "0xabc"}

    with pytest.raises(ValidationError, match="wallet_address"):
        validate_row(WhaleTradeRow, row)


def test_dates_must_parse_to_datetime() -> None:
    row = _valid_price_row() | {"price_timestamp": "not-a-date"}

    with pytest.raises(ValidationError, match="parseable as datetime"):
        validate_row(PolymarketPriceRow, row)


def test_missing_critical_field_raises_clear_error() -> None:
    row = _valid_price_row()
    row.pop("price")

    with pytest.raises(ValidationError) as exc_info:
        validate_row(PolymarketPriceRow, row)

    message = str(exc_info.value)
    assert "price" in message
    assert "Field required" in message


def test_pandera_valid_dataframe_passes() -> None:
    df = pd.DataFrame([_valid_price_row()])

    validated = validate_dataframe(polymarket_prices_schema, df)

    assert list(validated["price"]) == [0.52]


def test_pandera_invalid_dataframe_fails() -> None:
    df = pd.DataFrame([_valid_price_row() | {"price": -0.01}])

    with pytest.raises(SchemaError):
        validate_dataframe(polymarket_prices_schema, df)


def test_unknown_table_has_clear_error() -> None:
    with pytest.raises(ValueError, match="no Pydantic validation model registered"):
        validate_table_row("missing_table", {})
