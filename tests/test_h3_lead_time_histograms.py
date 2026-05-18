from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.h3_lead_time_histograms import (
    EVENT_ROW_COLUMNS,
    HISTOGRAM_COLUMNS,
    build_lead_time_event_rows,
    generate_h3_lead_time_histograms,
    load_tiered_activity,
    main,
    summarize_lead_time_histograms,
    validate_tiered_activity,
)
from operations.analysis.wallet_distribution_inventory import TIER_ORDER


def test_build_lead_time_event_rows_aligns_activity_to_events() -> None:
    rows = build_lead_time_event_rows(
        _toy_events(),
        _toy_activity(),
        lead_window_days=(-2, 0),
    )

    assert tuple(rows.columns) == EVENT_ROW_COLUMNS
    assert len(rows) == 2 * len(TIER_ORDER) * 3

    top_row = rows[
        (rows["event_id"] == "evt_one")
        & (rows["relative_day"] == -2)
        & (rows["tier"] == "tier_1_top_1pct")
    ].iloc[0]
    assert top_row["date"] == "2024-01-08"
    assert top_row["trade_rows"] == 2
    assert bool(top_row["has_activity"]) is True
    assert top_row["total_amount_usd"] == pytest.approx(100.0)

    missing_row = rows[
        (rows["event_id"] == "evt_two")
        & (rows["relative_day"] == 0)
        & (rows["tier"] == "tier_1_top_1pct")
    ].iloc[0]
    assert missing_row["date"] == "2024-01-12"
    assert bool(missing_row["activity_date_available"]) is False
    assert missing_row["trade_rows"] == 0


def test_summarize_lead_time_histograms_is_deterministic() -> None:
    rows = build_lead_time_event_rows(
        _toy_events(),
        _toy_activity(),
        lead_window_days=(-2, 0),
    )

    histogram = summarize_lead_time_histograms(rows)

    assert tuple(histogram.columns) == HISTOGRAM_COLUMNS
    assert len(histogram) == len(TIER_ORDER) * 3
    tier_one_minus_two = histogram[
        (histogram["tier"] == "tier_1_top_1pct")
        & (histogram["relative_day"] == -2)
    ].iloc[0]
    assert tier_one_minus_two["event_count"] == 2
    assert tier_one_minus_two["active_event_days"] == 1
    assert tier_one_minus_two["active_event_share"] == pytest.approx(0.5)
    assert tier_one_minus_two["total_trade_rows"] == 2
    assert tier_one_minus_two["avg_total_amount_usd_per_event"] == pytest.approx(50.0)


def test_validate_tiered_activity_rejects_wallet_addresses() -> None:
    activity = _toy_activity()
    activity["wallet_address"] = "0xabc"

    with pytest.raises(ValueError, match="must not contain wallet_address"):
        validate_tiered_activity(activity)


def test_validate_tiered_activity_rejects_duplicate_date_tier() -> None:
    activity = pd.concat([_toy_activity(), _toy_activity().iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="duplicate date-tier"):
        validate_tiered_activity(activity)


def test_generate_h3_lead_time_histograms_writes_outputs(tmp_path: Path) -> None:
    events_path = tmp_path / "events.csv"
    activity_path = tmp_path / "activity.csv"
    event_rows_path = tmp_path / "event_rows.csv"
    histogram_path = tmp_path / "histogram.csv"
    metadata_path = tmp_path / "metadata.json"
    _write_event_seed(events_path)
    _toy_activity().to_csv(activity_path, index=False)

    result = generate_h3_lead_time_histograms(
        events_csv_path=events_path,
        activity_path=activity_path,
        event_rows_path=event_rows_path,
        histogram_path=histogram_path,
        metadata_path=metadata_path,
        lead_window_days=(-2, 0),
    )

    event_rows = pd.read_csv(event_rows_path)
    histogram = pd.read_csv(histogram_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert result.event_count == 2
    assert len(event_rows) == 2 * len(TIER_ORDER) * 3
    assert len(histogram) == len(TIER_ORDER) * 3
    assert metadata["output"]["contains_wallet_addresses"] is False
    assert metadata["limitations"]["granger_tests_included"] is False


def test_load_tiered_activity_missing_file_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Tiered wallet activity not found"):
        load_tiered_activity(tmp_path / "missing.csv")


def test_cli_returns_clear_error_for_missing_activity(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    events_path = tmp_path / "events.csv"
    _write_event_seed(events_path)

    exit_code = main(
        [
            "--events",
            str(events_path),
            "--activity",
            str(tmp_path / "missing.csv"),
            "--event-rows-output",
            str(tmp_path / "event_rows.csv"),
            "--histogram-output",
            str(tmp_path / "histogram.csv"),
            "--metadata-output",
            str(tmp_path / "metadata.json"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "ERROR: Tiered wallet activity not found" in captured.err


def _toy_events() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"event_id": "evt_one", "event_date": "2024-01-10"},
            {"event_id": "evt_two", "event_date": "2024-01-12"},
        ]
    )


def _toy_activity() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": "2024-01-08",
                "tier": "tier_1_top_1pct",
                "trade_rows": 2,
                "active_wallets": 2,
                "total_amount_usd": 100.0,
                "buy_amount_usd": 100.0,
                "sell_amount_usd": 0.0,
                "net_amount_usd": 100.0,
            },
            {
                "date": "2024-01-10",
                "tier": "tier_2_top_5pct",
                "trade_rows": 1,
                "active_wallets": 1,
                "total_amount_usd": 25.0,
                "buy_amount_usd": 25.0,
                "sell_amount_usd": 0.0,
                "net_amount_usd": 25.0,
            },
            {
                "date": "2024-01-11",
                "tier": "tier_4_observed_baseline",
                "trade_rows": 3,
                "active_wallets": 2,
                "total_amount_usd": 300.0,
                "buy_amount_usd": 300.0,
                "sell_amount_usd": 0.0,
                "net_amount_usd": 300.0,
            },
        ]
    )


def _write_event_seed(path: Path) -> None:
    rows = [
        {
            "event_id": "evt_one",
            "event_date": "2024-01-10",
            "event_time_utc": "12:00:00",
            "title": "Toy event one",
            "description": "Toy event one.",
            "event_type": "major_news",
            "source_url": "https://example.com/one",
            "expected_direction": "neutral",
            "relevance_score": "0.8",
        },
        {
            "event_id": "evt_two",
            "event_date": "2024-01-12",
            "event_time_utc": "12:00:00",
            "title": "Toy event two",
            "description": "Toy event two.",
            "event_type": "major_news",
            "source_url": "https://example.com/two",
            "expected_direction": "neutral",
            "relevance_score": "0.7",
        },
    ]
    pd.DataFrame(rows).to_csv(path, index=False)
