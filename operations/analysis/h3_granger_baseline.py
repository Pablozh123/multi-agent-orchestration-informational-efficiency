"""Compute deterministic H3 lead-lag correlations and Granger baseline outputs."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import warnings
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import grangercausalitytests

from operations.analysis.event_study import compute_daily_price_changes
from operations.analysis.h3_lead_time_histograms import load_tiered_activity
from operations.analysis.run_h2_event_windows import (
    RESULTS_DIR,
    load_daily_polymarket_prices,
)
from operations.analysis.tiered_wallet_activity import ACTIVITY_OUTPUT
from operations.analysis.wallet_distribution_inventory import TIER_ORDER
from operations.db.migrations import DB_PATH


DEFAULT_MAX_LAG_DAYS = 7
ACTIVITY_MEASURE = "log1p_total_amount_usd_change"
PRICE_MEASURE = "polymarket_daily_price_change"
CORRELATION_OUTPUT = RESULTS_DIR / "h3_lead_lag_correlations.csv"
GRANGER_OUTPUT = RESULTS_DIR / "h3_granger_results.csv"
METADATA_OUTPUT = RESULTS_DIR / "h3_granger_metadata.json"

MODEL_SERIES_COLUMNS: tuple[str, ...] = (
    "date",
    "tier",
    "price_change",
    "activity_value",
    "activity_change",
)

CORRELATION_COLUMNS: tuple[str, ...] = (
    "tier",
    "price_measure",
    "activity_measure",
    "lag_days",
    "observation_count",
    "correlation",
    "status",
)

GRANGER_COLUMNS: tuple[str, ...] = (
    "tier",
    "price_measure",
    "activity_measure",
    "lag_days",
    "observation_count",
    "f_statistic",
    "p_value",
    "df_denom",
    "df_num",
    "status",
)


@dataclass(frozen=True)
class H3GrangerResult:
    """Summary of generated H3 lead-lag and Granger artifacts."""

    correlations_path: Path
    granger_path: Path
    metadata_path: Path
    model_row_count: int
    correlation_row_count: int
    granger_row_count: int

    def to_dict(self) -> dict[str, str | int]:
        """Return a JSON-friendly result summary."""

        return {
            "correlations_path": str(self.correlations_path),
            "granger_path": str(self.granger_path),
            "metadata_path": str(self.metadata_path),
            "model_row_count": self.model_row_count,
            "correlation_row_count": self.correlation_row_count,
            "granger_row_count": self.granger_row_count,
        }


def build_h3_granger_series(
    prices: pd.DataFrame,
    activity: pd.DataFrame,
) -> pd.DataFrame:
    """Return aligned daily price and tier-activity changes for H3 models."""

    price_changes = compute_daily_price_changes(prices)
    price_changes["date"] = pd.to_datetime(price_changes["date"], errors="raise").dt.date
    price_changes["date"] = price_changes["date"].astype(str)

    activity_frame = load_tiered_activity_from_frame(activity)
    activity_frame["activity_value"] = np.log1p(activity_frame["total_amount_usd"])
    activity_frame = activity_frame.sort_values(["tier", "date"]).reset_index(drop=True)
    activity_frame["activity_change"] = activity_frame.groupby("tier")[
        "activity_value"
    ].diff()

    merged = activity_frame.merge(
        price_changes[["date", "price_change"]],
        on="date",
        how="inner",
    )
    merged = merged.dropna(subset=["price_change", "activity_change"])
    return merged.loc[:, MODEL_SERIES_COLUMNS].sort_values(["tier", "date"]).reset_index(
        drop=True
    )


def load_tiered_activity_from_frame(activity: pd.DataFrame) -> pd.DataFrame:
    """Validate an in-memory tier activity frame."""

    from operations.analysis.h3_lead_time_histograms import validate_tiered_activity

    return validate_tiered_activity(activity)


def compute_lead_lag_correlations(
    model_series: pd.DataFrame,
    *,
    max_lag_days: int = DEFAULT_MAX_LAG_DAYS,
) -> pd.DataFrame:
    """Compute tier-level correlations for activity leading price changes."""

    _validate_max_lag(max_lag_days)
    _require_columns(model_series, MODEL_SERIES_COLUMNS, "model_series")
    rows: list[dict[str, object]] = []
    for tier, tier_series in _iter_tier_series(model_series):
        frame = tier_series.sort_values("date").reset_index(drop=True)
        for lag_days in range(0, max_lag_days + 1):
            lagged = frame.assign(
                activity_lagged=frame["activity_change"].shift(lag_days)
            ).dropna(subset=["price_change", "activity_lagged"])
            status = _series_status(lagged, "price_change", "activity_lagged")
            correlation = (
                float(lagged["price_change"].corr(lagged["activity_lagged"]))
                if status == "ok"
                else None
            )
            rows.append(
                {
                    "tier": tier,
                    "price_measure": PRICE_MEASURE,
                    "activity_measure": ACTIVITY_MEASURE,
                    "lag_days": lag_days,
                    "observation_count": int(len(lagged)),
                    "correlation": correlation,
                    "status": status,
                }
            )
    return pd.DataFrame(rows, columns=CORRELATION_COLUMNS)


def compute_granger_results(
    model_series: pd.DataFrame,
    *,
    max_lag_days: int = DEFAULT_MAX_LAG_DAYS,
) -> pd.DataFrame:
    """Compute tier-level Granger test statistics for selected lags."""

    _validate_max_lag(max_lag_days)
    _require_columns(model_series, MODEL_SERIES_COLUMNS, "model_series")
    rows: list[dict[str, object]] = []
    for tier, tier_series in _iter_tier_series(model_series):
        frame = tier_series.sort_values("date").reset_index(drop=True)
        for lag_days in range(1, max_lag_days + 1):
            row = _granger_row(frame, tier=tier, lag_days=lag_days)
            rows.append(row)
    return pd.DataFrame(rows, columns=GRANGER_COLUMNS)


def generate_h3_granger_baseline(
    *,
    db_path: Path = DB_PATH,
    activity_path: Path = ACTIVITY_OUTPUT,
    correlations_path: Path = CORRELATION_OUTPUT,
    granger_path: Path = GRANGER_OUTPUT,
    metadata_path: Path = METADATA_OUTPUT,
    max_lag_days: int = DEFAULT_MAX_LAG_DAYS,
    market_id: str | None = None,
    token_id: str | None = None,
) -> H3GrangerResult:
    """Generate deterministic H3 lead-lag and Granger output files."""

    _validate_max_lag(max_lag_days)
    activity = load_tiered_activity(activity_path)
    start_date, end_date = _activity_bounds(activity)
    prices = load_daily_polymarket_prices(
        db_path,
        start_date=start_date,
        end_date=end_date,
        market_id=market_id,
        token_id=token_id,
    )
    model_series = build_h3_granger_series(prices, activity)
    if model_series.empty:
        raise ValueError("No aligned H3 model observations after differencing")

    correlations = compute_lead_lag_correlations(
        model_series,
        max_lag_days=max_lag_days,
    )
    granger = compute_granger_results(model_series, max_lag_days=max_lag_days)

    correlations_path.parent.mkdir(parents=True, exist_ok=True)
    granger_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    correlations.to_csv(correlations_path, index=False)
    granger.to_csv(granger_path, index=False)

    metadata = _build_metadata(
        activity=activity,
        prices=prices,
        model_series=model_series,
        correlations=correlations,
        granger=granger,
        activity_path=activity_path,
        db_path=db_path,
        max_lag_days=max_lag_days,
    )
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return H3GrangerResult(
        correlations_path=correlations_path,
        granger_path=granger_path,
        metadata_path=metadata_path,
        model_row_count=len(model_series),
        correlation_row_count=len(correlations),
        granger_row_count=len(granger),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--activity", type=Path, default=ACTIVITY_OUTPUT)
    parser.add_argument("--correlations-output", type=Path, default=CORRELATION_OUTPUT)
    parser.add_argument("--granger-output", type=Path, default=GRANGER_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    parser.add_argument("--max-lag-days", type=int, default=DEFAULT_MAX_LAG_DAYS)
    parser.add_argument("--market-id", default=None)
    parser.add_argument("--token-id", default=None)
    args = parser.parse_args(argv)

    try:
        result = generate_h3_granger_baseline(
            db_path=args.db,
            activity_path=args.activity,
            correlations_path=args.correlations_output,
            granger_path=args.granger_output,
            metadata_path=args.metadata_output,
            max_lag_days=args.max_lag_days,
            market_id=args.market_id,
            token_id=args.token_id,
        )
    except (FileNotFoundError, ValueError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _granger_row(
    frame: pd.DataFrame,
    *,
    tier: str,
    lag_days: int,
) -> dict[str, object]:
    valid = frame[["price_change", "activity_change"]].dropna().reset_index(drop=True)
    base = {
        "tier": tier,
        "price_measure": PRICE_MEASURE,
        "activity_measure": ACTIVITY_MEASURE,
        "lag_days": lag_days,
        "observation_count": int(len(valid)),
        "f_statistic": None,
        "p_value": None,
        "df_denom": None,
        "df_num": None,
    }
    status = _series_status(valid, "price_change", "activity_change")
    if status != "ok":
        return {**base, "status": status}

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            result = grangercausalitytests(
                valid[["price_change", "activity_change"]],
                maxlag=lag_days,
                verbose=False,
            )
        f_statistic, p_value, df_denom, df_num = result[lag_days][0]["ssr_ftest"]
    except (ValueError, np.linalg.LinAlgError) as exc:
        return {**base, "status": f"error:{exc.__class__.__name__}"}

    return {
        **base,
        "f_statistic": float(f_statistic),
        "p_value": float(p_value),
        "df_denom": float(df_denom),
        "df_num": float(df_num),
        "status": "ok",
    }


def _series_status(frame: pd.DataFrame, target_col: str, predictor_col: str) -> str:
    if len(frame) < 5:
        return "insufficient_observations"
    if frame[target_col].nunique(dropna=True) < 2:
        return "insufficient_price_variation"
    if frame[predictor_col].nunique(dropna=True) < 2:
        return "insufficient_activity_variation"
    return "ok"


def _iter_tier_series(model_series: pd.DataFrame) -> list[tuple[str, pd.DataFrame]]:
    tier_order = {tier: index for index, tier in enumerate(TIER_ORDER)}
    tiers = sorted(
        model_series["tier"].dropna().astype(str).unique(),
        key=lambda value: tier_order.get(value, len(tier_order)),
    )
    return [(tier, model_series[model_series["tier"] == tier].copy()) for tier in tiers]


def _activity_bounds(activity: pd.DataFrame) -> tuple[date, date]:
    dates = pd.to_datetime(activity["date"], errors="raise").dt.date
    return min(dates), max(dates)


def _build_metadata(
    *,
    activity: pd.DataFrame,
    prices: pd.DataFrame,
    model_series: pd.DataFrame,
    correlations: pd.DataFrame,
    granger: pd.DataFrame,
    activity_path: Path,
    db_path: Path,
    max_lag_days: int,
) -> dict[str, Any]:
    granger_status_counts = granger["status"].value_counts().sort_index().to_dict()
    correlation_status_counts = (
        correlations["status"].value_counts().sort_index().to_dict()
    )
    return {
        "method": {
            "name": "deterministic_h3_daily_lead_lag_granger_baseline",
            "price_measure": PRICE_MEASURE,
            "activity_measure": ACTIVITY_MEASURE,
            "activity_transform": "daily_difference_of_log1p_total_amount_usd",
            "max_lag_days": max_lag_days,
            "granger_direction": "tier_activity_change_precedes_price_change",
        },
        "input": {
            "db_path": str(db_path),
            "activity_path": str(activity_path),
            "price_row_count": int(len(prices)),
            "activity_row_count": int(len(activity)),
            "model_row_count": int(len(model_series)),
            "date_range_start": str(model_series["date"].min()),
            "date_range_end": str(model_series["date"].max()),
            "tiers": sorted(model_series["tier"].unique().tolist()),
        },
        "output": {
            "correlation_columns": list(CORRELATION_COLUMNS),
            "granger_columns": list(GRANGER_COLUMNS),
            "correlation_row_count": int(len(correlations)),
            "granger_row_count": int(len(granger)),
            "correlation_status_counts": {
                str(key): int(value) for key, value in correlation_status_counts.items()
            },
            "granger_status_counts": {
                str(key): int(value) for key, value in granger_status_counts.items()
            },
            "contains_wallet_addresses": False,
            "claim_scope": "predictive_timing_diagnostics_only",
        },
        "limitations": {
            "daily_alignment_only": True,
            "uses_observed_buy_side_activity_extract": True,
            "does_not_establish_true_causality": True,
            "does_not_use_rcp": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
        },
    }


def _validate_max_lag(max_lag_days: int) -> None:
    if max_lag_days < 1:
        raise ValueError("max_lag_days must be >= 1")


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


if __name__ == "__main__":
    raise SystemExit(main())
