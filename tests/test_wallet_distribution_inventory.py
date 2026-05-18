from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.wallet_distribution_inventory import (
    TIER_METHOD,
    assign_wallet_tiers,
    build_wallet_distribution_inventory,
    compute_percentile_thresholds,
    generate_wallet_distribution_inventory,
    main,
)


def test_percentile_thresholds_use_observed_wallet_distribution() -> None:
    wallets = pd.DataFrame(
        {
            "wallet_address": [f"wallet-{index:03d}" for index in range(1, 101)],
            "cumulative_amount_usd": list(range(1, 101)),
        }
    )

    thresholds = compute_percentile_thresholds(wallets)

    assert thresholds == {"p90": 90.0, "p95": 95.0, "p99": 99.0}


def test_ties_at_threshold_are_assigned_to_higher_tier() -> None:
    wallets = pd.DataFrame(
        {
            "wallet_address": ["a", "b", "c", "d", "e"],
            "cumulative_amount_usd": [89.0, 90.0, 95.0, 99.0, 100.0],
        }
    )

    tiered = assign_wallet_tiers(
        wallets,
        {"p90": 90.0, "p95": 95.0, "p99": 99.0},
    )

    assert dict(zip(tiered["wallet_address"], tiered["tier"])) == {
        "a": "tier_4_observed_baseline",
        "b": "tier_3_top_10pct",
        "c": "tier_2_top_5pct",
        "d": "tier_1_top_1pct",
        "e": "tier_1_top_1pct",
    }


def test_inventory_documents_buy_only_source_filter_metadata() -> None:
    inventory = build_wallet_distribution_inventory(_toy_trades())

    source = inventory["source_filter_metadata"]
    assert inventory["method"]["name"] == TIER_METHOD
    assert source["trade_row_count"] == 6
    assert source["wallet_count"] == 4
    assert source["direction_distribution"] == {
        "BUY": {"trade_rows": 6, "wallets": 4}
    }
    assert source["buy_only"] is True
    assert source["minimum_observed_amount_usd"] == 11.0
    assert "not an analytical tier threshold" in source["minimum_observed_amount_note"]
    assert set(inventory["tier_counts"]) == {
        "tier_1_top_1pct",
        "tier_2_top_5pct",
        "tier_3_top_10pct",
        "tier_4_observed_baseline",
    }


def test_inventory_output_is_compact_and_omits_wallet_addresses(tmp_path: Path) -> None:
    db_path = tmp_path / "thesis.db"
    output_path = tmp_path / "inventory.json"
    _write_wallet_db(db_path)

    result = generate_wallet_distribution_inventory(
        db_path=db_path,
        output_path=output_path,
    )
    text = output_path.read_text(encoding="utf-8")
    payload = json.loads(text)

    assert result.trade_row_count == 6
    assert result.wallet_count == 4
    assert payload["input"]["table"] == "whale_trades"
    assert "0xaaa" not in text
    assert "0xbbb" not in text
    assert "percentile_thresholds" in payload


def test_missing_database_returns_clear_cli_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "--db",
            str(tmp_path / "missing.db"),
            "--output",
            str(tmp_path / "inventory.json"),
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
                "amount_usd": 11.0,
                "price_timestamp": "2024-01-01 00:00:00.000 UTCZ",
            },
            {
                "wallet_address": "0xbbb",
                "direction": "BUY",
                "amount_usd": 20.0,
                "price_timestamp": "2024-01-02 00:00:00.000 UTCZ",
            },
            {
                "wallet_address": "0xbbb",
                "direction": "BUY",
                "amount_usd": 30.0,
                "price_timestamp": "2024-01-03 00:00:00.000 UTCZ",
            },
            {
                "wallet_address": "0xccc",
                "direction": "BUY",
                "amount_usd": 40.0,
                "price_timestamp": "2024-01-04 00:00:00.000 UTCZ",
            },
            {
                "wallet_address": "0xddd",
                "direction": "BUY",
                "amount_usd": 50.0,
                "price_timestamp": "2024-01-05 00:00:00.000 UTCZ",
            },
            {
                "wallet_address": "0xddd",
                "direction": "BUY",
                "amount_usd": 60.0,
                "price_timestamp": "2024-01-06 00:00:00.000 UTCZ",
            },
        ]
    )


def _write_wallet_db(path: Path) -> None:
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
        rows = [
            (
                row["wallet_address"],
                row["direction"],
                row["amount_usd"],
                row["price_timestamp"],
            )
            for row in _toy_trades().to_dict(orient="records")
        ]
        conn.executemany(
            """
            INSERT INTO whale_trades
                (wallet_address, direction, amount_usd, price_timestamp)
            VALUES (?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
    finally:
        conn.close()
