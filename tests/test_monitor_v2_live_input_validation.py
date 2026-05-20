from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
from pydantic import ValidationError

from operations.analysis.monitor_v2_live_input_validation import (
    EVENT_CANDIDATE_LIVE_COLUMNS,
    MARKET_SNAPSHOT_LIVE_COLUMNS,
    MARKET_WATCH_LIVE_COLUMNS,
    WALLET_TIER_SNAPSHOT_LIVE_COLUMNS,
    main,
    validate_live_event_candidates,
    validate_live_input_files,
    validate_live_market_snapshots,
    validate_live_market_watch_items,
    validate_live_wallet_tier_snapshots,
)


def test_valid_live_inputs_pass_validation() -> None:
    watchlist = validate_live_market_watch_items(_watchlist())
    market = validate_live_market_snapshots(_market_snapshots())
    wallets = validate_live_wallet_tier_snapshots(_wallet_tier_snapshots())
    events = validate_live_event_candidates(_event_candidates())

    assert tuple(watchlist.columns) == MARKET_WATCH_LIVE_COLUMNS
    assert tuple(market.columns) == MARKET_SNAPSHOT_LIVE_COLUMNS
    assert tuple(wallets.columns) == WALLET_TIER_SNAPSHOT_LIVE_COLUMNS
    assert tuple(events.columns) == EVENT_CANDIDATE_LIVE_COLUMNS
    assert events.iloc[0]["review_status"] == "accepted"


def test_missing_required_live_field_fails_clearly() -> None:
    frame = _watchlist().drop(columns=["market_id"])

    with pytest.raises(ValueError, match="live watchlist missing required columns"):
        validate_live_market_watch_items(frame)


def test_live_market_snapshot_rejects_invalid_timestamp() -> None:
    frame = _market_snapshots()
    frame.loc[0, "collector_received_at_utc"] = "not-a-date"

    with pytest.raises(ValidationError, match="datetime value is not parseable"):
        validate_live_market_snapshots(frame)


def test_live_market_snapshot_rejects_invalid_price_range() -> None:
    frame = _market_snapshots()
    frame.loc[0, "price"] = 1.1

    with pytest.raises(ValidationError, match="price"):
        validate_live_market_snapshots(frame)


def test_live_market_snapshot_rejects_invalid_bucket_boundary() -> None:
    frame = _market_snapshots()
    frame.loc[0, "bucket_end_utc"] = "2026-05-20T00:00:00Z"

    with pytest.raises(ValidationError, match="bucket_start_utc must be before"):
        validate_live_market_snapshots(frame)


def test_live_market_snapshot_requires_source_timestamp_for_source_timestamp_source() -> None:
    frame = _market_snapshots()
    frame.loc[0, "source_timestamp_utc"] = ""

    with pytest.raises(ValidationError, match="source_timestamp_utc is required"):
        validate_live_market_snapshots(frame)


def test_live_wallet_snapshot_rejects_negative_counts_and_amounts() -> None:
    frame = _wallet_tier_snapshots()
    frame.loc[0, "active_wallets"] = -1
    frame.loc[0, "total_observed_amount_usd"] = -10.0

    with pytest.raises(ValidationError, match="active_wallets"):
        validate_live_wallet_tier_snapshots(frame)


def test_live_wallet_snapshot_rejects_wallet_address_fields() -> None:
    frame = _wallet_tier_snapshots()
    frame["wallet_address"] = "0x" + "1" * 40

    with pytest.raises(ValueError, match="wallet-address fields"):
        validate_live_wallet_tier_snapshots(frame)


def test_live_event_candidate_rejects_invalid_review_status() -> None:
    frame = _event_candidates()
    frame.loc[0, "review_status"] = "approved"

    with pytest.raises(ValidationError, match="review_status"):
        validate_live_event_candidates(frame)


def test_live_event_candidate_requires_source_and_market_mapping_when_accepted() -> None:
    frame = _event_candidates()
    frame.loc[0, "source_url"] = ""
    frame.loc[0, "related_market_ids"] = ""

    with pytest.raises(ValidationError, match="source_url is required"):
        validate_live_event_candidates(frame)


def test_validate_live_input_files_writes_structured_report(tmp_path: Path) -> None:
    watchlist_path = tmp_path / "watchlist.csv"
    market_path = tmp_path / "market.csv"
    wallet_path = tmp_path / "wallet.csv"
    event_path = tmp_path / "events.csv"
    report_path = tmp_path / "report.json"
    _watchlist().to_csv(watchlist_path, index=False)
    _market_snapshots().to_csv(market_path, index=False)
    _wallet_tier_snapshots().to_csv(wallet_path, index=False)
    _event_candidates().to_csv(event_path, index=False)

    report = validate_live_input_files(
        watchlist_path=watchlist_path,
        market_snapshots_path=market_path,
        wallet_tier_snapshots_path=wallet_path,
        event_candidates_path=event_path,
        report_output_path=report_path,
    )

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "pass"
    assert payload["input_mode"] == "replay_first_live_input_files"
    assert payload["validated_inputs"]["watchlist"]["row_count"] == 1
    assert payload["validated_inputs"]["market_snapshots"]["source_classes"] == ["market_state"]
    assert payload["limitations"]["does_not_call_external_apis"] is True
    assert payload["limitations"]["does_not_connect_to_websocket"] is True
    assert payload["limitations"]["does_not_use_agents_or_mcp"] is True


def test_cli_returns_clear_error_when_no_live_inputs(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main([])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "ERROR: At least one monitor v2 live input CSV path" in captured.err


def _base_live_fields(source_class: str) -> dict[str, str]:
    return {
        "collector_received_at_utc": "2026-05-20T00:15:05Z",
        "source_timestamp_utc": "2026-05-20T00:14:30Z",
        "bucket_start_utc": "2026-05-20T00:00:00Z",
        "bucket_end_utc": "2026-05-20T00:15:00Z",
        "timestamp_source": "source",
        "bucket_status": "closed",
        "source_class": source_class,
        "source_name": "mocked_local_fixture",
    }


def _watchlist() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                **_base_live_fields("market_discovery"),
                "watch_id": "watch_politics_geo_001",
                "market_id": "polymarket_politics_geo_001",
                "condition_id": "condition_001",
                "token_ids": "yes_token,no_token",
                "question": "Mock politics/geopolitics market",
                "category": "politics",
                "subcategory": "geopolitics",
                "status": "active",
            }
        ]
    )


def _market_snapshots() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                **_base_live_fields("market_state"),
                "market_id": "polymarket_politics_geo_001",
                "token_id": "yes_token",
                "price": 0.52,
                "midpoint": 0.53,
                "best_bid": 0.52,
                "best_ask": 0.54,
                "spread": 0.02,
                "volume": 1000.0,
                "open_interest": 2500.0,
            }
        ]
    )


def _wallet_tier_snapshots() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                **_base_live_fields("wallet_activity"),
                "market_id": "polymarket_politics_geo_001",
                "tier": "tier_1_top_1pct",
                "active_wallets": 4,
                "trade_count": 7,
                "total_observed_amount_usd": 125000.0,
                "top_tier_share": 0.41,
                "hhi_concentration": 0.19,
                "filter_metadata": "mocked_replay_filter_metadata",
            }
        ]
    )


def _event_candidates() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                **_base_live_fields("event_candidates"),
                "event_candidate_id": "event_candidate_001",
                "detected_at_utc": "2026-05-20T00:12:00Z",
                "published_at_utc": "2026-05-20T00:10:00Z",
                "title": "Mock reviewed politics/geopolitics event",
                "source_url": "https://example.com/mock-event",
                "event_type": "geopolitical_news",
                "related_market_ids": "polymarket_politics_geo_001",
                "expected_effect": "uncertainty_change",
                "review_status": "accepted",
                "review_notes": "mock accepted candidate",
            }
        ]
    )
