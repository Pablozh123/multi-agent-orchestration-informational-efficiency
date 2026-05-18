"""Classify observed wallets into deterministic H3 distribution tiers.

The classifier applies the selected wallet-level cumulative `amount_usd`
percentile method. It prepares a reproducible wallet-level artifact for later
H3 timing analysis, but does not run lead-lag or Granger tests.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.analysis.wallet_distribution_inventory import (
    TIER_FIELD,
    TIER_METHOD,
    assign_wallet_tiers,
    build_wallet_distribution_inventory,
    compute_percentile_thresholds,
    compute_wallet_aggregates,
    load_wallet_trades,
)
from operations.db.migrations import DB_PATH


CLASSIFICATION_OUTPUT = RESULTS_DIR / "h3_wallet_tiers.csv"
METADATA_OUTPUT = RESULTS_DIR / "h3_wallet_tiers_metadata.json"
CLASSIFICATION_COLUMNS: tuple[str, ...] = (
    "wallet_address",
    "tier",
    "cumulative_amount_usd",
    "trade_count",
    "max_trade_amount_usd",
    "first_trade_timestamp",
    "last_trade_timestamp",
)


@dataclass(frozen=True)
class WalletTierClassificationResult:
    """Summary of a wallet-tier classification run."""

    classification_path: Path
    metadata_path: Path
    wallet_count: int

    def to_dict(self) -> dict[str, str | int]:
        """Return a JSON-friendly result summary."""

        return {
            "classification_path": str(self.classification_path),
            "metadata_path": str(self.metadata_path),
            "wallet_count": self.wallet_count,
        }


def classify_wallet_tiers(trades: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Return wallet-level tier assignments and compact metadata."""

    wallets = compute_wallet_aggregates(trades)
    thresholds = compute_percentile_thresholds(wallets)
    tiered = assign_wallet_tiers(wallets, thresholds)
    inventory = build_wallet_distribution_inventory(trades)

    classification = (
        tiered.loc[:, CLASSIFICATION_COLUMNS]
        .sort_values(
            ["tier", "cumulative_amount_usd", "wallet_address"],
            ascending=[True, False, True],
        )
        .reset_index(drop=True)
    )
    metadata = {
        "method": {
            "name": TIER_METHOD,
            "tier_field": TIER_FIELD,
            "boundary_policy": "ties_at_threshold_assigned_to_higher_tier",
            "threshold_policy": "runtime_observed_value_percentiles",
        },
        "source_filter_metadata": inventory["source_filter_metadata"],
        "percentile_thresholds": thresholds,
        "tier_counts": inventory["tier_counts"],
        "diagnostic_fields": ["trade_count", "max_trade_amount_usd"],
        "output": {
            "classification_columns": list(CLASSIFICATION_COLUMNS),
            "contains_wallet_addresses": True,
            "intended_use": "deterministic_h3_timing_inputs_not_llm_prompts",
        },
    }
    return classification, metadata


def generate_wallet_tier_classification(
    *,
    db_path: Path = DB_PATH,
    classification_path: Path = CLASSIFICATION_OUTPUT,
    metadata_path: Path = METADATA_OUTPUT,
) -> WalletTierClassificationResult:
    """Generate wallet-tier classification CSV and metadata JSON."""

    trades = load_wallet_trades(db_path)
    classification, metadata = classify_wallet_tiers(trades)

    classification_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    classification.to_csv(classification_path, index=False)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return WalletTierClassificationResult(
        classification_path=classification_path,
        metadata_path=metadata_path,
        wallet_count=len(classification),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--classification-output", type=Path, default=CLASSIFICATION_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)

    try:
        result = generate_wallet_tier_classification(
            db_path=args.db,
            classification_path=args.classification_output,
            metadata_path=args.metadata_output,
        )
    except (FileNotFoundError, ValueError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
