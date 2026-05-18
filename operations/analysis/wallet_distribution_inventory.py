"""Generate deterministic H3 wallet distribution inventory metadata.

The inventory reads explicit columns from `whale_trades`, computes wallet-level
distribution summaries, and writes compact metadata for the selected percentile
tier method. It does not write wallet-level address lists.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.db.migrations import DB_PATH


OUTPUT_PATH = RESULTS_DIR / "h3_wallet_distribution_inventory.json"
TIER_METHOD = "wallet_cumulative_amount_usd_percentiles"
TIER_FIELD = "wallet_cumulative_amount_usd"
TIER_PERCENTILES: tuple[tuple[str, float], ...] = (
    ("p90", 0.90),
    ("p95", 0.95),
    ("p99", 0.99),
)
TIER_ORDER: tuple[str, ...] = (
    "tier_1_top_1pct",
    "tier_2_top_5pct",
    "tier_3_top_10pct",
    "tier_4_observed_baseline",
)


@dataclass(frozen=True)
class WalletInventoryResult:
    """Summary of a wallet distribution inventory run."""

    output_path: Path
    trade_row_count: int
    wallet_count: int

    def to_dict(self) -> dict[str, str | int]:
        """Return a JSON-friendly result summary."""

        return {
            "output_path": str(self.output_path),
            "trade_row_count": self.trade_row_count,
            "wallet_count": self.wallet_count,
        }


def load_wallet_trades(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Load explicit H3 wallet-trade columns from SQLite."""

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    try:
        frame = pd.read_sql_query(
            """
            SELECT wallet_address, direction, amount_usd, price_timestamp
            FROM whale_trades
            ORDER BY price_timestamp
            """,
            conn,
        )
    finally:
        conn.close()

    if frame.empty:
        raise ValueError("whale_trades contains no rows")
    return validate_wallet_trades(frame)


def validate_wallet_trades(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize wallet-trade rows for inventory computation."""

    required = ("wallet_address", "direction", "amount_usd", "price_timestamp")
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"wallet trade frame missing columns: {missing}")

    normalized = frame.loc[:, required].copy()
    for column in ("wallet_address", "direction", "price_timestamp"):
        if normalized[column].isna().any() or (
            normalized[column].astype(str).str.strip() == ""
        ).any():
            raise ValueError(f"wallet trade frame contains blank values in {column}")
        normalized[column] = normalized[column].astype(str).str.strip()

    normalized["amount_usd"] = pd.to_numeric(
        normalized["amount_usd"],
        errors="raise",
    )
    if not (normalized["amount_usd"] > 0).all():
        raise ValueError("amount_usd must be greater than 0")

    parsed_timestamps = pd.to_datetime(
        normalized["price_timestamp"].str.replace(" UTCZ", "Z", regex=False),
        errors="raise",
        utc=True,
    )
    normalized["price_timestamp"] = parsed_timestamps.dt.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    normalized["direction"] = normalized["direction"].str.upper()
    return normalized


def compute_wallet_aggregates(trades: pd.DataFrame) -> pd.DataFrame:
    """Aggregate observed trade rows to wallet-level diagnostic fields."""

    validated = validate_wallet_trades(trades)
    grouped = (
        validated.groupby("wallet_address", as_index=False)
        .agg(
            cumulative_amount_usd=("amount_usd", "sum"),
            trade_count=("amount_usd", "size"),
            max_trade_amount_usd=("amount_usd", "max"),
            first_trade_timestamp=("price_timestamp", "min"),
            last_trade_timestamp=("price_timestamp", "max"),
        )
        .sort_values(["cumulative_amount_usd", "wallet_address"], ascending=[False, True])
        .reset_index(drop=True)
    )
    return grouped


def compute_percentile_thresholds(wallets: pd.DataFrame) -> dict[str, float]:
    """Compute observed-value percentile thresholds for tiering."""

    if "cumulative_amount_usd" not in wallets.columns:
        raise ValueError("wallet aggregates missing cumulative_amount_usd")
    amounts = pd.to_numeric(wallets["cumulative_amount_usd"], errors="raise")
    if amounts.empty:
        raise ValueError("wallet aggregates are empty")
    return {
        label: float(amounts.quantile(percentile, interpolation="lower"))
        for label, percentile in TIER_PERCENTILES
    }


def assign_wallet_tiers(
    wallets: pd.DataFrame,
    thresholds: Mapping[str, float],
) -> pd.DataFrame:
    """Assign dataset-relative tiers using cumulative observed amount."""

    required_thresholds = {"p90", "p95", "p99"}
    missing = required_thresholds.difference(thresholds)
    if missing:
        raise ValueError(f"tier thresholds missing: {sorted(missing)}")
    if "cumulative_amount_usd" not in wallets.columns:
        raise ValueError("wallet aggregates missing cumulative_amount_usd")

    frame = wallets.copy()
    amounts = pd.to_numeric(frame["cumulative_amount_usd"], errors="raise")
    frame["tier"] = "tier_4_observed_baseline"
    frame.loc[amounts >= thresholds["p90"], "tier"] = "tier_3_top_10pct"
    frame.loc[amounts >= thresholds["p95"], "tier"] = "tier_2_top_5pct"
    frame.loc[amounts >= thresholds["p99"], "tier"] = "tier_1_top_1pct"
    return frame


def build_wallet_distribution_inventory(trades: pd.DataFrame) -> dict[str, Any]:
    """Build compact H3 wallet distribution inventory metadata."""

    validated = validate_wallet_trades(trades)
    wallets = compute_wallet_aggregates(validated)
    thresholds = compute_percentile_thresholds(wallets)
    tiered = assign_wallet_tiers(wallets, thresholds)

    direction_distribution = _direction_distribution(validated)
    tier_counts = _tier_counts(tiered)
    inventory = {
        "method": {
            "name": TIER_METHOD,
            "tier_field": TIER_FIELD,
            "threshold_policy": "runtime_observed_value_percentiles",
            "boundary_policy": "ties_at_threshold_assigned_to_higher_tier",
            "diagnostic_fields": ["trade_count", "max_trade_amount_usd"],
        },
        "input": {
            "table": "whale_trades",
            "columns": [
                "wallet_address",
                "direction",
                "amount_usd",
                "price_timestamp",
            ],
            "date_range_start": str(validated["price_timestamp"].min()),
            "date_range_end": str(validated["price_timestamp"].max()),
        },
        "source_filter_metadata": {
            "trade_row_count": int(len(validated)),
            "wallet_count": int(len(wallets)),
            "direction_distribution": direction_distribution,
            "buy_only": set(direction_distribution) == {"BUY"},
            "minimum_observed_amount_usd": float(validated["amount_usd"].min()),
            "minimum_observed_amount_note": (
                "Observed source-filter metadata only; not an analytical tier threshold."
            ),
        },
        "percentile_thresholds": thresholds,
        "tier_counts": tier_counts,
        "diagnostics": {
            "cumulative_amount_usd_quantiles": _quantiles(
                wallets["cumulative_amount_usd"]
            ),
            "trade_count_quantiles": _quantiles(wallets["trade_count"]),
            "max_trade_amount_usd_quantiles": _quantiles(
                wallets["max_trade_amount_usd"]
            ),
            "concentration": _concentration(wallets["cumulative_amount_usd"]),
        },
    }
    return inventory


def generate_wallet_distribution_inventory(
    *,
    db_path: Path = DB_PATH,
    output_path: Path = OUTPUT_PATH,
) -> WalletInventoryResult:
    """Generate and write compact wallet distribution inventory metadata."""

    trades = load_wallet_trades(db_path)
    inventory = build_wallet_distribution_inventory(trades)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return WalletInventoryResult(
        output_path=output_path,
        trade_row_count=int(inventory["source_filter_metadata"]["trade_row_count"]),
        wallet_count=int(inventory["source_filter_metadata"]["wallet_count"]),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args(argv)

    try:
        result = generate_wallet_distribution_inventory(
            db_path=args.db,
            output_path=args.output,
        )
    except (FileNotFoundError, ValueError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


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


def _tier_counts(tiered_wallets: pd.DataFrame) -> dict[str, int]:
    counts = tiered_wallets["tier"].value_counts().to_dict()
    return {tier: int(counts.get(tier, 0)) for tier in TIER_ORDER}


def _quantiles(series: pd.Series) -> dict[str, float]:
    values = pd.to_numeric(series, errors="raise")
    return {
        "min": float(values.min()),
        "p50": float(values.quantile(0.50, interpolation="lower")),
        "p75": float(values.quantile(0.75, interpolation="lower")),
        "p90": float(values.quantile(0.90, interpolation="lower")),
        "p95": float(values.quantile(0.95, interpolation="lower")),
        "p99": float(values.quantile(0.99, interpolation="lower")),
        "max": float(values.max()),
    }


def _concentration(amounts: pd.Series) -> dict[str, float]:
    sorted_amounts = pd.to_numeric(amounts, errors="raise").sort_values(
        ascending=False
    )
    total = float(sorted_amounts.sum())
    if total <= 0:
        raise ValueError("wallet cumulative amount total must be greater than 0")

    shares: dict[str, float] = {}
    for count in (1, 5, 10, 25, 50):
        if len(sorted_amounts) >= count:
            shares[f"top_{count}_wallet_share"] = float(
                sorted_amounts.head(count).sum() / total
            )
    return shares


if __name__ == "__main__":
    raise SystemExit(main())
