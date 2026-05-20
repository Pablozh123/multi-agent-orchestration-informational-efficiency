from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.h3_event_wallet_anomalies import (
    ANOMALY_ROW_COLUMNS,
    ANOMALY_SUMMARY_COLUMNS,
    build_historical_anomaly_rows,
    generate_h3_event_wallet_anomalies,
    main,
    summarize_historical_anomalies,
)


def test_build_historical_anomaly_rows_detects_toy_spikes() -> None:
    rows = build_historical_anomaly_rows(
        _toy_events(),
        _toy_prices(),
        _toy_activity(),
        baseline_window_days=(-10, -3),
        event_window_days=(-1, 1),
        min_baseline_observations=3,
    )

    assert tuple(rows.columns) == ANOMALY_ROW_COLUMNS
    assert set(rows["relative_day"]) == {-1, 0, 1}
    assert rows["date"].min() >= "2024-01-14"
    assert "wallet_address" not in rows.columns

    amount_row = rows[
        (rows["event_id"] == "evt_one")
        & (rows["relative_day"] == 0)
        & (rows["tier"] == "tier_1_top_1pct")
        & (rows["metric_name"] == "log1p_total_amount_usd")
    ].iloc[0]
    assert bool(amount_row["is_anomaly"]) is True
    assert amount_row["baseline_observations"] == 8
    assert amount_row["observed_value"] > amount_row["baseline_mean"]

    concentration_row = rows[
        (rows["event_id"] == "evt_one")
        & (rows["relative_day"] == 0)
        & (rows["anomaly_type"] == "top_tier_concentration_anomaly")
    ].iloc[0]
    assert bool(concentration_row["is_anomaly"]) is True
    assert concentration_row["observed_value"] == pytest.approx(0.969, abs=0.01)


def test_summarize_historical_anomalies_compacts_rows() -> None:
    rows = build_historical_anomaly_rows(
        _toy_events(),
        _toy_prices(),
        _toy_activity(),
        baseline_window_days=(-10, -3),
        event_window_days=(-1, 1),
    )

    summary = summarize_historical_anomalies(rows)

    assert tuple(summary.columns) == ANOMALY_SUMMARY_COLUMNS
    assert "wallet_address" not in summary.columns
    top_summary = summary[
        (summary["event_id"] == "evt_one")
        & (summary["tier"] == "tier_1_top_1pct")
        & (summary["metric_name"] == "log1p_total_amount_usd")
    ].iloc[0]
    assert top_summary["event_window_days"] == 3
    assert top_summary["anomaly_day_count"] >= 1
    assert top_summary["claim_scope"] == "descriptive_historical_anomaly_diagnostic"


def test_missing_event_fields_fail_clearly() -> None:
    events = _toy_events().drop(columns=["source_url"])

    with pytest.raises(ValueError, match="events missing required columns"):
        build_historical_anomaly_rows(events, _toy_prices(), _toy_activity())


def test_overlapping_baseline_and_event_windows_fail() -> None:
    with pytest.raises(ValueError, match="baseline window must end before event window"):
        build_historical_anomaly_rows(
            _toy_events(),
            _toy_prices(),
            _toy_activity(),
            baseline_window_days=(-3, 0),
            event_window_days=(-1, 1),
        )


def test_generate_h3_event_wallet_anomalies_writes_outputs(tmp_path: Path) -> None:
    db_path = tmp_path / "thesis.db"
    events_path = tmp_path / "events.csv"
    activity_path = tmp_path / "activity.csv"
    rows_path = tmp_path / "rows.csv"
    summary_path = tmp_path / "summary.csv"
    metadata_path = tmp_path / "metadata.json"
    _write_price_db(db_path, _toy_prices())
    _write_event_seed(events_path)
    _toy_activity().to_csv(activity_path, index=False)

    result = generate_h3_event_wallet_anomalies(
        db_path=db_path,
        events_csv_path=events_path,
        activity_path=activity_path,
        rows_path=rows_path,
        summary_path=summary_path,
        metadata_path=metadata_path,
        baseline_window_days=(-10, -3),
        event_window_days=(-1, 1),
    )

    rows = pd.read_csv(rows_path)
    summary = pd.read_csv(summary_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert result.event_count == 1
    assert len(rows) == 1 * 3 * 10
    assert len(summary) == 10
    assert metadata["output"]["contains_wallet_addresses"] is False
    assert metadata["limitations"]["uses_observed_buy_side_activity_extract"] is True
    assert metadata["limitations"]["does_not_use_agents_or_mcp"] is True
    assert "wallet_address" not in rows.columns
    assert "wallet_address" not in summary.columns


def test_cli_returns_clear_error_for_missing_database(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    events_path = tmp_path / "events.csv"
    activity_path = tmp_path / "activity.csv"
    _write_event_seed(events_path)
    _toy_activity().to_csv(activity_path, index=False)

    exit_code = main(
        [
            "--db",
            str(tmp_path / "missing.db"),
            "--events",
            str(events_path),
            "--activity",
            str(activity_path),
            "--rows-output",
            str(tmp_path / "rows.csv"),
            "--summary-output",
            str(tmp_path / "summary.csv"),
            "--metadata-output",
            str(tmp_path / "metadata.json"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "ERROR: Database not found" in captured.err


def _toy_events() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "event_id": "evt_one",
                "event_date": "2024-01-15",
                "title": "Toy politics event",
                "event_type": "major_news",
                "source_url": "https://example.com/event",
            }
        ]
    )


def _toy_prices() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", "2024-01-16", freq="D")
    prices = [
        0.50,
        0.51,
        0.50,
        0.51,
        0.50,
        0.51,
        0.50,
        0.51,
        0.50,
        0.51,
        0.50,
        0.51,
        0.50,
        0.51,
        0.65,
        0.66,
    ]
    return pd.DataFrame({"date": dates.date.astype(str), "price": prices})


def _toy_activity() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", "2024-01-16", freq="D").date.astype(str)
    rows: list[dict[str, object]] = []
    for day in dates:
        for tier in (
            "tier_1_top_1pct",
            "tier_2_top_5pct",
            "tier_3_top_10pct",
            "tier_4_observed_baseline",
        ):
            top_event_day = day == "2024-01-15" and tier == "tier_1_top_1pct"
            if day == "2024-01-15" and tier != "tier_1_top_1pct":
                amount = 10.0
            else:
                amount = 950.0 if top_event_day else (20.0 if tier == "tier_1_top_1pct" else 180.0)
            active_wallets = 10 if top_event_day else (1 if tier == "tier_1_top_1pct" else 3)
            rows.append(
                {
                    "date": day,
                    "tier": tier,
                    "trade_rows": 5 if top_event_day else 1,
                    "active_wallets": active_wallets,
                    "total_amount_usd": amount,
                    "buy_amount_usd": amount,
                    "sell_amount_usd": 0.0,
                    "net_amount_usd": amount,
                }
            )
    return pd.DataFrame(rows)


def _write_event_seed(path: Path) -> None:
    rows = [
        {
            "event_id": "evt_one",
            "event_date": "2024-01-15",
            "event_time_utc": "12:00:00",
            "title": "Toy politics event",
            "description": "Toy politics event.",
            "event_type": "major_news",
            "source_url": "https://example.com/event",
            "expected_direction": "neutral",
            "relevance_score": "0.9",
        }
    ]
    pd.DataFrame(rows).to_csv(path, index=False)


def _write_price_db(path: Path, prices: pd.DataFrame) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE polymarket_prices (
                price_timestamp TEXT NOT NULL,
                market_id TEXT NOT NULL,
                token_id TEXT NOT NULL,
                price REAL NOT NULL
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO polymarket_prices
                (price_timestamp, market_id, token_id, price)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    f"{row['date']}T00:00:00Z",
                    "market",
                    "token",
                    float(row["price"]),
                )
                for row in prices.to_dict(orient="records")
            ],
        )
        conn.commit()
    finally:
        conn.close()
