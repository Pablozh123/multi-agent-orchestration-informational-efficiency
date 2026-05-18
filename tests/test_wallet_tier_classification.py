from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.classify_wallet_tiers import (
    CLASSIFICATION_COLUMNS,
    classify_wallet_tiers,
    generate_wallet_tier_classification,
    main,
)
from operations.analysis.wallet_distribution_inventory import TIER_METHOD


def test_classify_wallet_tiers_applies_runtime_thresholds_and_tie_policy() -> None:
    classification, metadata = classify_wallet_tiers(_threshold_trades())

    tiers = dict(zip(classification["wallet_address"], classification["tier"]))
    assert tiers["wallet_089"] == "tier_4_observed_baseline"
    assert tiers["wallet_090"] == "tier_3_top_10pct"
    assert tiers["wallet_095"] == "tier_2_top_5pct"
    assert tiers["wallet_099"] == "tier_1_top_1pct"
    assert metadata["percentile_thresholds"] == {
        "p90": 90.0,
        "p95": 95.0,
        "p99": 99.0,
    }
    assert metadata["method"]["name"] == TIER_METHOD


def test_classification_contains_expected_columns_and_metadata() -> None:
    classification, metadata = classify_wallet_tiers(_small_trades())

    assert tuple(classification.columns) == CLASSIFICATION_COLUMNS
    assert len(classification) == 4
    assert metadata["source_filter_metadata"]["buy_only"] is True
    assert metadata["source_filter_metadata"]["minimum_observed_amount_usd"] == 11.0
    assert "not an analytical tier threshold" in metadata[
        "source_filter_metadata"
    ]["minimum_observed_amount_note"]
    assert metadata["output"]["contains_wallet_addresses"] is True
    assert metadata["output"]["intended_use"] == "deterministic_h3_timing_inputs_not_llm_prompts"


def test_generate_wallet_tier_classification_writes_outputs(tmp_path: Path) -> None:
    db_path = tmp_path / "thesis.db"
    csv_path = tmp_path / "wallet_tiers.csv"
    metadata_path = tmp_path / "wallet_tiers_metadata.json"
    _write_wallet_db(db_path, _small_trades())

    result = generate_wallet_tier_classification(
        db_path=db_path,
        classification_path=csv_path,
        metadata_path=metadata_path,
    )

    classification = pd.read_csv(csv_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert result.wallet_count == 4
    assert len(classification) == 4
    assert set(classification["tier"]).issubset(
        {
            "tier_1_top_1pct",
            "tier_2_top_5pct",
            "tier_3_top_10pct",
            "tier_4_observed_baseline",
        }
    )
    assert metadata["tier_counts"]["tier_1_top_1pct"] >= 1


def test_missing_database_returns_clear_cli_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "--db",
            str(tmp_path / "missing.db"),
            "--classification-output",
            str(tmp_path / "tiers.csv"),
            "--metadata-output",
            str(tmp_path / "metadata.json"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "ERROR: Database not found" in captured.err


def _threshold_trades() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "wallet_address": f"wallet_{index:03d}",
                "direction": "BUY",
                "amount_usd": float(index),
                "price_timestamp": f"2024-01-{((index - 1) % 28) + 1:02d} 00:00:00.000 UTCZ",
            }
            for index in range(1, 101)
        ]
    )


def _small_trades() -> pd.DataFrame:
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
