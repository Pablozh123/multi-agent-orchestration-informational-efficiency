from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.monitor_v2_input_validation import (
    EVENT_CANDIDATE_COLUMNS,
    MARKET_SNAPSHOT_COLUMNS,
    MARKET_WATCH_COLUMNS,
    WALLET_TIER_SNAPSHOT_COLUMNS,
)
from operations.analysis.monitor_v2_recorded_input_adapter import (
    build_event_candidates,
    build_recorded_watchlist,
    build_wallet_tier_snapshots,
    generate_recorded_monitor_v2_inputs,
    load_recorded_price_snapshots,
    main,
)


def test_build_recorded_inputs_from_toy_artifacts(tmp_path: Path) -> None:
    db_path = tmp_path / "prices.db"
    _write_price_db(db_path)
    market = load_recorded_price_snapshots(
        db_path,
        start_date=pd.Timestamp("2024-01-01").date(),
        end_date=pd.Timestamp("2024-01-03").date(),
        market_id="toy_replay_market",
    )
    watchlist = build_recorded_watchlist(market, market_id="toy_replay_market")
    wallets = build_wallet_tier_snapshots(_toy_activity(), market_id="toy_replay_market")
    events = build_event_candidates(_toy_events(), market_id="toy_replay_market")

    assert tuple(watchlist.columns) == MARKET_WATCH_COLUMNS
    assert tuple(market.columns) == MARKET_SNAPSHOT_COLUMNS
    assert tuple(wallets.columns) == WALLET_TIER_SNAPSHOT_COLUMNS
    assert tuple(events.columns) == EVENT_CANDIDATE_COLUMNS
    assert len(watchlist) == 1
    assert len(market) == 3
    assert len(wallets) == 8
    assert len(events) == 1
    assert "wallet_address" not in wallets.columns
    assert set(events["review_status"]) == {"accepted"}


def test_generate_recorded_monitor_v2_inputs_writes_and_validates_outputs(tmp_path: Path) -> None:
    db_path = tmp_path / "thesis.db"
    events_path = tmp_path / "events.csv"
    activity_path = tmp_path / "activity.csv"
    watchlist_path = tmp_path / "watchlist.csv"
    market_path = tmp_path / "market.csv"
    wallet_path = tmp_path / "wallet.csv"
    event_candidates_path = tmp_path / "event_candidates.csv"
    report_path = tmp_path / "validation_report.json"
    metadata_path = tmp_path / "metadata.json"
    _write_price_db(db_path)
    _write_event_seed(events_path)
    _toy_activity().to_csv(activity_path, index=False)

    result = generate_recorded_monitor_v2_inputs(
        db_path=db_path,
        events_csv_path=events_path,
        activity_path=activity_path,
        watchlist_path=watchlist_path,
        market_snapshots_path=market_path,
        wallet_tier_snapshots_path=wallet_path,
        event_candidates_path=event_candidates_path,
        validation_report_path=report_path,
        metadata_path=metadata_path,
        market_id="toy_replay_market",
    )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert result.watchlist_row_count == 1
    assert result.market_snapshot_row_count == 2
    assert result.wallet_tier_snapshot_row_count == 8
    assert result.event_candidate_row_count == 1
    assert report["status"] == "pass"
    assert metadata["outputs"]["validation_status"] == "pass"
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["contains_order_instructions"] is False
    assert "wallet_address" not in pd.read_csv(wallet_path).columns


def test_adapter_rejects_wallet_address_activity() -> None:
    activity = _toy_activity()
    activity["wallet_address"] = "0x" + "1" * 40

    with pytest.raises(ValueError, match="must not receive wallet_address"):
        build_wallet_tier_snapshots(activity, market_id="toy_replay_market")


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
            "--watchlist-output",
            str(tmp_path / "watchlist.csv"),
            "--market-snapshots-output",
            str(tmp_path / "market.csv"),
            "--wallet-tier-snapshots-output",
            str(tmp_path / "wallet.csv"),
            "--event-candidates-output",
            str(tmp_path / "events_out.csv"),
            "--validation-report-output",
            str(tmp_path / "report.json"),
            "--metadata-output",
            str(tmp_path / "metadata.json"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "ERROR: Database not found" in captured.err


def _write_price_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE polymarket_prices (
                price_timestamp TEXT NOT NULL,
                market_id TEXT NOT NULL,
                token_id TEXT NOT NULL,
                price REAL NOT NULL,
                volume_24h REAL,
                best_bid REAL,
                best_ask REAL
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO polymarket_prices
                (price_timestamp, market_id, token_id, price, volume_24h, best_bid, best_ask)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("2024-01-01T00:00:00Z", "condition", "token_yes", 0.50, 100.0, 0.49, 0.51),
                ("2024-01-02T00:00:00Z", "condition", "token_yes", 0.52, 120.0, 0.51, 0.53),
                ("2024-01-03T00:00:00Z", "condition", "token_yes", 0.54, 140.0, 0.53, 0.55),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def _write_event_seed(path: Path) -> None:
    _toy_events().assign(
        description="Toy event.",
        relevance_score="0.9",
    ).to_csv(path, index=False)


def _toy_events() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "event_id": "evt_toy",
                "event_date": "2024-01-02",
                "event_time_utc": "12:00:00",
                "title": "Toy politics event",
                "event_type": "major_news",
                "source_url": "https://example.com/event",
                "expected_direction": "uncertainty_change",
            }
        ]
    )


def _toy_activity() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for day in ("2024-01-01", "2024-01-02"):
        for tier, amount in (
            ("tier_1_top_1pct", 100.0),
            ("tier_2_top_5pct", 80.0),
            ("tier_3_top_10pct", 60.0),
            ("tier_4_observed_baseline", 40.0),
        ):
            rows.append(
                {
                    "date": day,
                    "tier": tier,
                    "trade_rows": 2,
                    "active_wallets": 2,
                    "total_amount_usd": amount,
                    "buy_amount_usd": amount,
                    "sell_amount_usd": 0.0,
                    "net_amount_usd": amount,
                }
            )
    return pd.DataFrame(rows)
