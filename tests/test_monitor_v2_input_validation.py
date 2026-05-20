from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
from pydantic import ValidationError

from operations.analysis.monitor_v2_input_validation import (
    MARKET_SNAPSHOT_COLUMNS,
    MARKET_WATCH_COLUMNS,
    WALLET_TIER_SNAPSHOT_COLUMNS,
    validate_event_candidates,
    validate_market_snapshots,
    validate_market_watch_items,
    validate_recorded_input_files,
    validate_wallet_tier_snapshots,
    main,
)


def test_valid_recorded_inputs_pass_validation() -> None:
    watchlist = validate_market_watch_items(_watchlist())
    market = validate_market_snapshots(_market_snapshots())
    wallets = validate_wallet_tier_snapshots(_wallet_tier_snapshots())
    events = validate_event_candidates(_event_candidates())

    assert tuple(watchlist.columns) == MARKET_WATCH_COLUMNS
    assert tuple(market.columns) == MARKET_SNAPSHOT_COLUMNS
    assert tuple(wallets.columns) == WALLET_TIER_SNAPSHOT_COLUMNS
    assert events.iloc[0]["review_status"] == "accepted"


def test_missing_critical_field_fails_clearly() -> None:
    frame = _watchlist().drop(columns=["market_id"])

    with pytest.raises(ValueError, match="market watchlist missing required columns"):
        validate_market_watch_items(frame)


def test_market_snapshot_rejects_invalid_price() -> None:
    frame = _market_snapshots()
    frame.loc[0, "price"] = 1.2

    with pytest.raises(ValidationError, match="price"):
        validate_market_snapshots(frame)


def test_market_snapshot_requires_price_or_midpoint() -> None:
    frame = _market_snapshots()
    frame.loc[0, "price"] = None
    frame.loc[0, "midpoint"] = None

    with pytest.raises(ValidationError, match="price or midpoint"):
        validate_market_snapshots(frame)


def test_wallet_tier_snapshot_rejects_wallet_addresses() -> None:
    frame = _wallet_tier_snapshots()
    frame["wallet_address"] = "0x" + "1" * 40

    with pytest.raises(ValueError, match="must not contain wallet_address"):
        validate_wallet_tier_snapshots(frame)


def test_event_candidate_requires_source_when_accepted() -> None:
    frame = _event_candidates()
    frame.loc[0, "source_url"] = ""

    with pytest.raises(ValidationError, match="source_url is required"):
        validate_event_candidates(frame)


def test_validate_recorded_input_files_writes_report(tmp_path: Path) -> None:
    watchlist_path = tmp_path / "watchlist.csv"
    market_path = tmp_path / "market.csv"
    wallet_path = tmp_path / "wallet.csv"
    event_path = tmp_path / "events.csv"
    report_path = tmp_path / "report.json"
    _watchlist().to_csv(watchlist_path, index=False)
    _market_snapshots().to_csv(market_path, index=False)
    _wallet_tier_snapshots().to_csv(wallet_path, index=False)
    _event_candidates().to_csv(event_path, index=False)

    report = validate_recorded_input_files(
        watchlist_path=watchlist_path,
        market_snapshots_path=market_path,
        wallet_tier_snapshots_path=wallet_path,
        event_candidates_path=event_path,
        report_output_path=report_path,
    )

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "pass"
    assert payload["validated_inputs"]["watchlist"]["row_count"] == 1
    assert payload["validated_inputs"]["market_snapshots"]["row_count"] == 1
    assert payload["limitations"]["does_not_call_external_apis"] is True
    assert payload["limitations"]["does_not_use_agents_or_mcp"] is True


def test_cli_returns_clear_error_when_no_inputs(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "ERROR: At least one recorded input CSV path" in captured.err


def _watchlist() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "watch_id": "watch_2024_us_presidential",
                "market_id": "polymarket_2024_us_presidential_replay",
                "condition_id": "condition_001",
                "token_ids": "trump_yes,harris_yes",
                "question": "2024 US presidential election winner",
                "category": "politics",
                "subcategory": "us_election",
                "status": "active",
                "source": "recorded_fixture",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z",
            }
        ]
    )


def _market_snapshots() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "timestamp_utc": "2024-07-21T00:00:00Z",
                "market_id": "polymarket_2024_us_presidential_replay",
                "token_id": "trump_yes",
                "price": 0.55,
                "midpoint": 0.55,
                "best_bid": 0.54,
                "best_ask": 0.56,
                "spread": 0.02,
                "volume": 1000.0,
                "open_interest": 5000.0,
                "source": "recorded_fixture",
            }
        ]
    )


def _wallet_tier_snapshots() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "timestamp_utc": "2024-07-21T00:00:00Z",
                "market_id": "polymarket_2024_us_presidential_replay",
                "bucket": "daily",
                "tier": "tier_1_top_1pct",
                "active_wallets": 12,
                "trade_count": 18,
                "total_observed_amount_usd": 125000.0,
                "top_tier_share": 0.42,
                "hhi_concentration": 0.18,
                "source": "recorded_fixture",
                "filter_metadata": "buy_side_observed_extract",
            }
        ]
    )


def _event_candidates() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "event_candidate_id": "event_candidate_biden_withdrawal",
                "detected_at_utc": "2024-07-21T18:00:00Z",
                "published_at_utc": "2024-07-21T17:46:00Z",
                "title": "Biden withdrawal candidate",
                "source_url": "https://example.com/biden-withdrawal",
                "event_type": "election_news",
                "related_market_ids": "polymarket_2024_us_presidential_replay",
                "expected_effect": "uncertainty_change",
                "review_status": "accepted",
                "review_notes": "toy accepted candidate",
            }
        ]
    )
