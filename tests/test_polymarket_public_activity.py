from __future__ import annotations

import json
from pathlib import Path

import httpx
import pandas as pd
import pytest

from operations.collectors.polymarket_public_activity import (
    PUBLIC_ACTIVITY_COLUMNS,
    collect_public_wallet_activity,
    normalize_public_activity_rows,
    validate_public_activity,
)
from operations.collectors.polymarket_readonly import DATA_API_BASE_URL


def test_normalize_public_activity_rows_keeps_public_wallets() -> None:
    activity = normalize_public_activity_rows(
        [_raw_trade("0x" + "1" * 40, 125.0)],
        watchlist=_watchlist(),
        collected_at=pd.Timestamp("2026-05-26T10:00:00Z").to_pydatetime(),
        source_name="toy",
    )

    validated = validate_public_activity(activity)
    assert tuple(validated.columns) == PUBLIC_ACTIVITY_COLUMNS
    assert validated.iloc[0]["proxy_wallet"] == "0x" + "1" * 40
    assert validated.iloc[0]["usdc_size"] == pytest.approx(125.0)
    assert validated.iloc[0]["price"] == pytest.approx(0.42)


def test_validate_public_activity_rejects_invalid_rows() -> None:
    activity = normalize_public_activity_rows(
        [_raw_trade("not-a-wallet", 125.0)],
        watchlist=_watchlist(),
        collected_at=pd.Timestamp("2026-05-26T10:00:00Z").to_pydatetime(),
        source_name="toy",
    )

    with pytest.raises(ValueError, match="invalid proxy_wallet"):
        validate_public_activity(activity)

    invalid = normalize_public_activity_rows(
        [_raw_trade("0x" + "1" * 40, -1.0)],
        watchlist=_watchlist(),
        collected_at=pd.Timestamp("2026-05-26T10:00:00Z").to_pydatetime(),
        source_name="toy",
    )
    with pytest.raises(ValueError, match="negative usdc_size"):
        validate_public_activity(invalid)


def test_live_collection_uses_public_data_api_only(tmp_path: Path) -> None:
    watchlist_path = tmp_path / "watchlist.csv"
    _watchlist().to_csv(watchlist_path, index=False)
    requested_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        if str(request.url).startswith(f"{DATA_API_BASE_URL}/trades"):
            return httpx.Response(200, json=[_raw_trade("0x" + "2" * 40, 200.0)])
        return httpx.Response(404, json={"error": "unexpected"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = collect_public_wallet_activity(
            source="live",
            watchlist_path=watchlist_path,
            activity_path=tmp_path / "activity.csv",
            metadata_path=tmp_path / "metadata.json",
            client=client,
        )

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    assert result.row_count == 1
    assert metadata["method"]["uses_public_data_api"] is True
    assert metadata["method"]["uses_order_endpoints"] is False
    assert all(url.startswith(f"{DATA_API_BASE_URL}/trades") for url in requested_urls)


def _watchlist() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "market_id": "0x" + "a" * 64,
                "condition_id": "0x" + "a" * 64,
                "question": "Will a politics market resolve yes?",
            }
        ]
    )


def _raw_trade(wallet: str, usdc_size: float) -> dict[str, object]:
    return {
        "proxyWallet": wallet,
        "timestamp": 1_780_000_000,
        "conditionId": "0x" + "a" * 64,
        "side": "BUY",
        "usdcSize": usdc_size,
        "price": 0.42,
        "outcome": "YES",
        "transactionHash": "0x" + "b" * 64,
        "name": "Example",
        "pseudonym": "example",
        "title": "Will a politics market resolve yes?",
        "slug": "politics-market",
        "eventSlug": "politics-event",
    }
