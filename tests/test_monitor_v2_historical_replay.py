from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.monitor_v2_historical_replay import (
    build_historical_replay_snapshots,
    generate_monitor_v2_historical_replay,
    main,
)
from operations.analysis.monitor_v2_snapshot import (
    SNAPSHOT_COLUMNS,
    build_monitor_v2_alert_rows,
)


def test_build_historical_replay_snapshots_from_toy_artifacts() -> None:
    snapshots = build_historical_replay_snapshots(
        _toy_events(),
        _toy_prices(),
        _toy_activity(),
        market_id="toy_market",
    )

    assert tuple(snapshots.columns) == SNAPSHOT_COLUMNS
    assert "wallet_address" not in snapshots.columns
    assert snapshots["market_id"].nunique() == 1
    assert snapshots["timestamp_utc"].nunique() == 7
    assert len(snapshots) == 7 * 10
    event_rows = snapshots[snapshots["event_candidate_id"] == "evt_spike"]
    assert len(event_rows) == 10
    assert set(event_rows["event_review_status"]) == {"accepted"}


def test_replay_alerts_use_rule_c_and_can_find_event_cluster() -> None:
    snapshots = build_historical_replay_snapshots(
        _toy_events(),
        _toy_prices(),
        _toy_activity(),
        market_id="toy_market",
    )

    rows = build_monitor_v2_alert_rows(
        snapshots,
        baseline_observations=5,
        min_baseline_observations=5,
    )

    final_rows = rows[rows["timestamp_utc"] == "2024-01-08T00:00:00Z"]
    assert set(final_rows[final_rows["severity"] == "critical"]["anomaly_family"]) >= {
        "market_move",
        "wallet_tier_activity",
    }
    assert "wallet_address" not in rows.columns


def test_generate_monitor_v2_historical_replay_writes_outputs(tmp_path: Path) -> None:
    db_path = tmp_path / "thesis.db"
    events_path = tmp_path / "events.csv"
    activity_path = tmp_path / "activity.csv"
    snapshots_path = tmp_path / "snapshots.csv"
    rows_path = tmp_path / "rows.csv"
    summary_path = tmp_path / "summary.csv"
    context_rows_path = tmp_path / "context_rows.csv"
    metadata_path = tmp_path / "metadata.json"
    _write_price_db(db_path, _toy_prices())
    _write_event_seed(events_path)
    _toy_activity().to_csv(activity_path, index=False)

    result = generate_monitor_v2_historical_replay(
        db_path=db_path,
        events_csv_path=events_path,
        activity_path=activity_path,
        snapshots_path=snapshots_path,
        rows_path=rows_path,
        summary_path=summary_path,
        context_rows_path=context_rows_path,
        metadata_path=metadata_path,
        baseline_observations=5,
        min_baseline_observations=5,
        market_id="toy_market",
    )

    snapshots = pd.read_csv(snapshots_path)
    rows = pd.read_csv(rows_path)
    summary = pd.read_csv(summary_path)
    context_rows = pd.read_csv(context_rows_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert result.snapshot_count == len(snapshots)
    assert result.alert_row_count == len(rows)
    assert result.summary_row_count == len(summary)
    assert result.context_row_count == len(context_rows)
    assert metadata["method"]["alert_rule"] == "Rule C combined-family confirmation from monitor_v2_snapshot"
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["contains_order_instructions"] is False
    assert metadata["outputs"]["event_context_window"] == "[-1d,+1d]"
    assert metadata["outputs"]["event_watch_label"] == (
        "separate_descriptive_label_not_severity_upgrade"
    )
    assert metadata["limitations"]["no_live_websocket_or_api_collection"] is True
    assert "wallet_address" not in snapshots.columns
    assert "wallet_address" not in rows.columns
    assert "wallet_address" not in summary.columns
    assert "wallet_address" not in context_rows.columns
    assert "critical_proximity_candidate" in set(context_rows["suggested_context_label"])


def test_missing_event_columns_fail_clearly() -> None:
    events = _toy_events().drop(columns=["source_url"])

    with pytest.raises(ValueError, match="events missing required columns"):
        build_historical_replay_snapshots(events, _toy_prices(), _toy_activity())


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
            "--snapshots-output",
            str(tmp_path / "snapshots.csv"),
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
                "event_id": "evt_spike",
                "event_date": "2024-01-08",
                "title": "Toy politics spike",
                "event_type": "major_news",
                "source_url": "https://example.com/event",
            }
        ]
    )


def _toy_prices() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=8, freq="D").date.astype(str),
            "price": [0.50, 0.51, 0.505, 0.515, 0.507, 0.516, 0.508, 0.70],
        }
    )


def _toy_activity() -> pd.DataFrame:
    dates = pd.date_range("2024-01-02", periods=7, freq="D").date.astype(str)
    rows: list[dict[str, object]] = []
    for index, day in enumerate(dates):
        for tier in (
            "tier_1_top_1pct",
            "tier_2_top_5pct",
            "tier_3_top_10pct",
            "tier_4_observed_baseline",
        ):
            is_spike_day = day == "2024-01-08"
            is_top_tier = tier == "tier_1_top_1pct"
            amount = 1000.0 + 25.0 * index
            active_wallets = 2 + (index % 2)
            if is_spike_day and is_top_tier:
                amount = 120000.0
                active_wallets = 30
            elif is_spike_day:
                amount = 100.0
                active_wallets = 1
            rows.append(
                {
                    "date": day,
                    "tier": tier,
                    "trade_rows": 8 if is_spike_day and is_top_tier else 1,
                    "active_wallets": active_wallets,
                    "total_amount_usd": amount,
                    "buy_amount_usd": amount,
                    "sell_amount_usd": 0.0,
                    "net_amount_usd": amount,
                }
            )
    return pd.DataFrame(rows)


def _write_event_seed(path: Path) -> None:
    pd.DataFrame(
        [
            {
                "event_id": "evt_spike",
                "event_date": "2024-01-08",
                "event_time_utc": "12:00:00",
                "title": "Toy politics spike",
                "description": "Toy politics spike.",
                "event_type": "major_news",
                "source_url": "https://example.com/event",
                "expected_direction": "neutral",
                "relevance_score": "0.9",
            }
        ]
    ).to_csv(path, index=False)


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
