from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.tiered_wallet_activity import (
    ACTIVITY_COLUMNS,
    build_tiered_wallet_activity,
    generate_tiered_wallet_activity,
    load_wallet_tiers,
    main,
)


def test_build_tiered_wallet_activity_creates_complete_daily_panel() -> None:
    activity, metadata = build_tiered_wallet_activity(_toy_trades(), _toy_tiers())

    assert tuple(activity.columns) == ACTIVITY_COLUMNS
    assert len(activity) == 12
    assert metadata["output"]["complete_daily_tier_panel"] is True
    assert metadata["output"]["contains_wallet_addresses"] is False

    top_day = activity[
        (activity["date"] == "2024-01-01")
        & (activity["tier"] == "tier_1_top_1pct")
    ].iloc[0]
    assert top_day["trade_rows"] == 1
    assert top_day["active_wallets"] == 1
    assert top_day["buy_amount_usd"] == pytest.approx(10.0)
    assert top_day["sell_amount_usd"] == pytest.approx(0.0)
    assert top_day["net_amount_usd"] == pytest.approx(10.0)

    zero_day = activity[
        (activity["date"] == "2024-01-02")
        & (activity["tier"] == "tier_1_top_1pct")
    ].iloc[0]
    assert zero_day["trade_rows"] == 0
    assert zero_day["total_amount_usd"] == pytest.approx(0.0)


def test_build_tiered_wallet_activity_handles_sell_amounts() -> None:
    trades = _toy_trades().copy()
    trades.loc[len(trades)] = {
        "wallet_address": "0xbbb",
        "direction": "SELL",
        "amount_usd": 5.0,
        "price_timestamp": "2024-01-02 12:00:00.000 UTCZ",
    }

    activity, metadata = build_tiered_wallet_activity(trades, _toy_tiers())

    row = activity[
        (activity["date"] == "2024-01-02")
        & (activity["tier"] == "tier_2_top_5pct")
    ].iloc[0]
    assert row["trade_rows"] == 2
    assert row["buy_amount_usd"] == pytest.approx(20.0)
    assert row["sell_amount_usd"] == pytest.approx(5.0)
    assert row["net_amount_usd"] == pytest.approx(15.0)
    assert metadata["source_filter_metadata"]["buy_only"] is False


def test_missing_tier_assignment_fails_clearly() -> None:
    tiers = _toy_tiers()[lambda frame: frame["wallet_address"] != "0xccc"]

    with pytest.raises(ValueError, match="no wallet tier assignment"):
        build_tiered_wallet_activity(_toy_trades(), tiers)


def test_generate_tiered_wallet_activity_writes_compact_outputs(tmp_path: Path) -> None:
    db_path = tmp_path / "thesis.db"
    classification_path = tmp_path / "tiers.csv"
    activity_path = tmp_path / "activity.csv"
    metadata_path = tmp_path / "metadata.json"
    _write_wallet_db(db_path, _toy_trades())
    _toy_tiers().to_csv(classification_path, index=False)

    result = generate_tiered_wallet_activity(
        db_path=db_path,
        classification_path=classification_path,
        activity_path=activity_path,
        metadata_path=metadata_path,
    )

    activity = pd.read_csv(activity_path)
    metadata_text = metadata_path.read_text(encoding="utf-8")
    metadata = json.loads(metadata_text)
    assert result.row_count == 12
    assert len(activity) == 12
    assert "0xaaa" not in metadata_text
    assert "0xbbb" not in metadata_text
    assert metadata["source_filter_metadata"]["buy_only"] is True


def test_load_wallet_tiers_rejects_duplicate_wallets(tmp_path: Path) -> None:
    path = tmp_path / "tiers.csv"
    pd.DataFrame(
        {
            "wallet_address": ["0xaaa", "0xaaa"],
            "tier": ["tier_1_top_1pct", "tier_2_top_5pct"],
        }
    ).to_csv(path, index=False)

    with pytest.raises(ValueError, match="duplicate wallets"):
        load_wallet_tiers(path)


def test_missing_database_returns_clear_cli_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    classification_path = tmp_path / "tiers.csv"
    _toy_tiers().to_csv(classification_path, index=False)

    exit_code = main(
        [
            "--db",
            str(tmp_path / "missing.db"),
            "--classification",
            str(classification_path),
            "--activity-output",
            str(tmp_path / "activity.csv"),
            "--metadata-output",
            str(tmp_path / "metadata.json"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "ERROR: Database not found" in captured.err


def _toy_trades() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "wallet_address": "0xaaa",
                "direction": "BUY",
                "amount_usd": 10.0,
                "price_timestamp": "2024-01-01 00:00:00.000 UTCZ",
            },
            {
                "wallet_address": "0xbbb",
                "direction": "BUY",
                "amount_usd": 20.0,
                "price_timestamp": "2024-01-02 00:00:00.000 UTCZ",
            },
            {
                "wallet_address": "0xccc",
                "direction": "BUY",
                "amount_usd": 30.0,
                "price_timestamp": "2024-01-03 00:00:00.000 UTCZ",
            },
        ]
    )


def _toy_tiers() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "wallet_address": ["0xaaa", "0xbbb", "0xccc"],
            "tier": [
                "tier_1_top_1pct",
                "tier_2_top_5pct",
                "tier_4_observed_baseline",
            ],
        }
    )


def _write_wallet_db(path: Path, trades: pd.DataFrame) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE whale_trades (
                wallet_address TEXT NOT NULL,
                direction TEXT NOT NULL,
                amount_usd REAL NOT NULL,
                price_timestamp TEXT NOT NULL
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO whale_trades
                (wallet_address, direction, amount_usd, price_timestamp)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    row["wallet_address"],
                    row["direction"],
                    row["amount_usd"],
                    row["price_timestamp"],
                )
                for row in trades.to_dict(orient="records")
            ],
        )
        conn.commit()
    finally:
        conn.close()
