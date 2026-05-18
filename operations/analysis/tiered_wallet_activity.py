"""Prepare deterministic H3 wallet activity series by selected tier.

The series joins observed wallet trades to deterministic tier assignments and
aggregates daily activity by tier. It prepares inputs for later H3 timing work
without computing timing statistics.
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

from operations.analysis.classify_wallet_tiers import (
    CLASSIFICATION_OUTPUT,
    METADATA_OUTPUT as CLASSIFICATION_METADATA_OUTPUT,
)
from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.analysis.wallet_distribution_inventory import TIER_ORDER, load_wallet_trades
from operations.db.migrations import DB_PATH


ACTIVITY_OUTPUT = RESULTS_DIR / "h3_tiered_wallet_activity_daily.csv"
ACTIVITY_METADATA_OUTPUT = RESULTS_DIR / "h3_tiered_wallet_activity_metadata.json"
ACTIVITY_COLUMNS: tuple[str, ...] = (
    "date",
    "tier",
    "trade_rows",
    "active_wallets",
    "total_amount_usd",
    "buy_amount_usd",
    "sell_amount_usd",
    "net_amount_usd",
)
CLASSIFICATION_COLUMNS: tuple[str, ...] = ("wallet_address", "tier")


@dataclass(frozen=True)
class TieredActivityResult:
    """Summary of a tiered wallet activity generation run."""

    activity_path: Path
    metadata_path: Path
    row_count: int

    def to_dict(self) -> dict[str, str | int]:
        """Return a JSON-friendly result summary."""

        return {
            "activity_path": str(self.activity_path),
            "metadata_path": str(self.metadata_path),
            "row_count": self.row_count,
        }


def load_wallet_tiers(classification_path: Path = CLASSIFICATION_OUTPUT) -> pd.DataFrame:
    """Load and validate wallet-tier assignments."""

    if not classification_path.exists():
        raise FileNotFoundError(f"Wallet tier classification not found: {classification_path}")
    frame = pd.read_csv(classification_path)
    missing = [column for column in CLASSIFICATION_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"wallet tier classification missing columns: {missing}")

    tiers = frame.loc[:, CLASSIFICATION_COLUMNS].copy()
    for column in CLASSIFICATION_COLUMNS:
        if tiers[column].isna().any() or (
            tiers[column].astype(str).str.strip() == ""
        ).any():
            raise ValueError(f"wallet tier classification contains blank values in {column}")
        tiers[column] = tiers[column].astype(str).str.strip()

    duplicate_wallets = tiers["wallet_address"].duplicated()
    if duplicate_wallets.any():
        duplicates = sorted(tiers.loc[duplicate_wallets, "wallet_address"].unique())
        raise ValueError(f"wallet tier classification has duplicate wallets: {duplicates}")

    allowed_tiers = set(TIER_ORDER)
    invalid_tiers = sorted(set(tiers["tier"]).difference(allowed_tiers))
    if invalid_tiers:
        raise ValueError(f"wallet tier classification has invalid tiers: {invalid_tiers}")
    return tiers


def build_tiered_wallet_activity(
    trades: pd.DataFrame,
    tiers: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Return a complete daily tier panel and compact metadata."""

    required_trade_columns = ("wallet_address", "direction", "amount_usd", "price_timestamp")
    missing_trade_columns = [
        column for column in required_trade_columns if column not in trades.columns
    ]
    if missing_trade_columns:
        raise ValueError(f"wallet trade frame missing columns: {missing_trade_columns}")

    tier_frame = _validate_tier_frame(tiers)
    trade_frame = trades.loc[:, required_trade_columns].copy()
    trade_frame["wallet_address"] = trade_frame["wallet_address"].astype(str).str.strip()
    trade_frame["direction"] = trade_frame["direction"].astype(str).str.strip().str.upper()
    trade_frame["amount_usd"] = pd.to_numeric(trade_frame["amount_usd"], errors="raise")
    if not (trade_frame["amount_usd"] > 0).all():
        raise ValueError("amount_usd must be greater than 0")
    parsed_timestamps = pd.to_datetime(
        trade_frame["price_timestamp"].astype(str).str.replace(" UTCZ", "Z", regex=False),
        errors="raise",
        utc=True,
    )
    trade_frame["date"] = parsed_timestamps.dt.date.astype(str)

    joined = trade_frame.merge(tier_frame, on="wallet_address", how="left")
    missing_tiers = int(joined["tier"].isna().sum())
    if missing_tiers:
        raise ValueError(f"{missing_tiers} trade rows have no wallet tier assignment")

    joined["buy_amount_usd"] = joined["amount_usd"].where(joined["direction"] == "BUY", 0.0)
    joined["sell_amount_usd"] = joined["amount_usd"].where(joined["direction"] == "SELL", 0.0)
    daily = (
        joined.groupby(["date", "tier"], as_index=False)
        .agg(
            trade_rows=("amount_usd", "size"),
            active_wallets=("wallet_address", "nunique"),
            total_amount_usd=("amount_usd", "sum"),
            buy_amount_usd=("buy_amount_usd", "sum"),
            sell_amount_usd=("sell_amount_usd", "sum"),
        )
        .sort_values(["date", "tier"])
    )
    daily["net_amount_usd"] = daily["buy_amount_usd"] - daily["sell_amount_usd"]

    complete = _complete_daily_panel(daily)
    metadata = {
        "input": {
            "trade_rows": int(len(trade_frame)),
            "wallets_with_tiers": int(tier_frame["wallet_address"].nunique()),
            "date_range_start": str(complete["date"].min()),
            "date_range_end": str(complete["date"].max()),
        },
        "source_filter_metadata": {
            "direction_distribution": _direction_distribution(trade_frame),
            "buy_only": set(trade_frame["direction"].unique()) == {"BUY"},
            "minimum_observed_amount_usd": float(trade_frame["amount_usd"].min()),
            "minimum_observed_amount_note": (
                "Observed source-filter metadata only; not an analytical tier threshold."
            ),
        },
        "output": {
            "activity_columns": list(ACTIVITY_COLUMNS),
            "complete_daily_tier_panel": True,
            "contains_wallet_addresses": False,
            "intended_use": "deterministic_h3_tiered_activity_inputs",
        },
        "tier_coverage": _tier_coverage(tier_frame, complete),
    }
    return complete.loc[:, ACTIVITY_COLUMNS], metadata


def generate_tiered_wallet_activity(
    *,
    db_path: Path = DB_PATH,
    classification_path: Path = CLASSIFICATION_OUTPUT,
    activity_path: Path = ACTIVITY_OUTPUT,
    metadata_path: Path = ACTIVITY_METADATA_OUTPUT,
) -> TieredActivityResult:
    """Generate tiered daily wallet activity CSV and metadata JSON."""

    trades = load_wallet_trades(db_path)
    tiers = load_wallet_tiers(classification_path)
    activity, metadata = build_tiered_wallet_activity(trades, tiers)

    activity_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    activity.to_csv(activity_path, index=False)
    metadata["input"]["classification_path"] = str(classification_path)
    if CLASSIFICATION_METADATA_OUTPUT.exists():
        metadata["input"]["classification_metadata_path"] = str(
            CLASSIFICATION_METADATA_OUTPUT
        )
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return TieredActivityResult(
        activity_path=activity_path,
        metadata_path=metadata_path,
        row_count=len(activity),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--classification", type=Path, default=CLASSIFICATION_OUTPUT)
    parser.add_argument("--activity-output", type=Path, default=ACTIVITY_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=ACTIVITY_METADATA_OUTPUT)
    args = parser.parse_args(argv)

    try:
        result = generate_tiered_wallet_activity(
            db_path=args.db,
            classification_path=args.classification,
            activity_path=args.activity_output,
            metadata_path=args.metadata_output,
        )
    except (FileNotFoundError, ValueError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_tier_frame(tiers: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in CLASSIFICATION_COLUMNS if column not in tiers.columns]
    if missing:
        raise ValueError(f"wallet tier frame missing columns: {missing}")
    frame = tiers.loc[:, CLASSIFICATION_COLUMNS].copy()
    for column in CLASSIFICATION_COLUMNS:
        if frame[column].isna().any() or (
            frame[column].astype(str).str.strip() == ""
        ).any():
            raise ValueError(f"wallet tier frame contains blank values in {column}")
        frame[column] = frame[column].astype(str).str.strip()
    duplicate_wallets = frame["wallet_address"].duplicated()
    if duplicate_wallets.any():
        duplicates = sorted(frame.loc[duplicate_wallets, "wallet_address"].unique())
        raise ValueError(f"wallet tier frame has duplicate wallets: {duplicates}")
    invalid_tiers = sorted(set(frame["tier"]).difference(TIER_ORDER))
    if invalid_tiers:
        raise ValueError(f"wallet tier frame has invalid tiers: {invalid_tiers}")
    return frame


def _complete_daily_panel(daily: pd.DataFrame) -> pd.DataFrame:
    dates = pd.date_range(daily["date"].min(), daily["date"].max(), freq="D").date
    panel = pd.MultiIndex.from_product(
        [[date_value.isoformat() for date_value in dates], list(TIER_ORDER)],
        names=["date", "tier"],
    ).to_frame(index=False)
    complete = panel.merge(daily, on=["date", "tier"], how="left")
    fill_values = {
        "trade_rows": 0,
        "active_wallets": 0,
        "total_amount_usd": 0.0,
        "buy_amount_usd": 0.0,
        "sell_amount_usd": 0.0,
        "net_amount_usd": 0.0,
    }
    complete = complete.fillna(fill_values)
    complete["trade_rows"] = complete["trade_rows"].astype(int)
    complete["active_wallets"] = complete["active_wallets"].astype(int)
    return complete.sort_values(["date", "tier"]).reset_index(drop=True)


def _direction_distribution(trades: pd.DataFrame) -> dict[str, dict[str, int]]:
    grouped = (
        trades.groupby("direction")
        .agg(trade_rows=("amount_usd", "size"), wallets=("wallet_address", "nunique"))
        .reset_index()
        .sort_values("direction")
    )
    return {
        str(row["direction"]): {
            "trade_rows": int(row["trade_rows"]),
            "wallets": int(row["wallets"]),
        }
        for _, row in grouped.iterrows()
    }


def _tier_coverage(tiers: pd.DataFrame, activity: pd.DataFrame) -> dict[str, dict[str, int]]:
    coverage: dict[str, dict[str, int]] = {}
    wallet_counts = tiers["tier"].value_counts().to_dict()
    for tier in TIER_ORDER:
        tier_activity = activity[activity["tier"] == tier]
        coverage[tier] = {
            "wallet_count": int(wallet_counts.get(tier, 0)),
            "active_days": int((tier_activity["trade_rows"] > 0).sum()),
        }
    return coverage


if __name__ == "__main__":
    raise SystemExit(main())
