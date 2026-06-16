"""Build deterministic H3 informed-trading signature diagnostics.

The module creates aggregate event-window diagnostics only. It does not expose
wallet addresses, does not call external APIs or agents, and does not turn the
diagnostic score into a claim about causality, private information, trading
performance, or misconduct.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from operations.analysis.h3_granger_baseline import (
    DEFAULT_MAX_LAG_DAYS,
    build_h3_granger_series,
    compute_granger_results,
    compute_lead_lag_correlations,
)
from operations.analysis.run_h2_event_windows import (
    RESULTS_DIR,
    SEED_PATH,
    load_curated_events,
    load_daily_polymarket_prices,
)
from operations.analysis.tiered_wallet_activity import build_tiered_wallet_activity
from operations.analysis.wallet_distribution_inventory import (
    TIER_ORDER,
    assign_wallet_tiers,
    compute_percentile_thresholds,
    compute_wallet_aggregates,
    load_wallet_trades,
    validate_wallet_trades,
)
from operations.db.migrations import DB_PATH


DEFAULT_BASELINE_WINDOW = (-30, -8)
DEFAULT_EVENT_WINDOW = (-1, 3)
DEFAULT_MIN_BASELINE_WINDOWS = 3
BASELINE_WINDOW_LABEL = "baseline_minus_30d_to_minus_8d"
EVENT_WINDOW_LABEL = "event_minus_1d_to_plus_3d"
OUTPUT_PATH = RESULTS_DIR / "h3_informed_trading_signature.csv"
METADATA_PATH = RESULTS_DIR / "h3_informed_trading_signature_metadata.json"
FIGURE_PATH = RESULTS_DIR / "h3_informed_trading_signature.png"
TOP_TIER = "tier_1_top_1pct"

EVENT_COLUMNS: tuple[str, ...] = (
    "event_id",
    "event_date",
    "title",
    "event_type",
    "source_url",
)

FEATURE_COLUMNS: tuple[str, ...] = (
    "new_wallet_share",
    "top1_concentration",
    "hhi",
    "abnormal_trade_size_z",
    "active_wallet_z",
    "volume_z",
    "tier1_lead",
)

PERCENTILE_COLUMNS: tuple[str, ...] = tuple(
    f"{column}_percentile" for column in FEATURE_COLUMNS
)

SIGNATURE_COLUMNS: tuple[str, ...] = (
    "event_id",
    "event_date",
    "title",
    "event_type",
    "event_window_label",
    "baseline_window_label",
    "event_window_days",
    "baseline_window_count",
    "trade_rows",
    "active_wallets",
    "total_amount_usd",
    "new_wallet_share",
    "top1_concentration",
    "hhi",
    "abnormal_trade_size_z",
    "active_wallet_z",
    "volume_z",
    "tier1_lead",
    *PERCENTILE_COLUMNS,
    "suspicion_score",
    "score_feature_count",
    "tier1_lead_lag_days",
    "claim_scope",
    "limitation",
)

ADDRESS_LIKE_PATTERN = re.compile(r"\b0x[a-fA-F0-9]{8,}\b")


@dataclass(frozen=True)
class H3InformedTradingSignatureResult:
    """Summary of generated H3 informed-trading signature artifacts."""

    output_path: Path
    metadata_path: Path
    figure_path: Path
    event_count: int
    row_count: int

    def to_dict(self) -> dict[str, str | int]:
        """Return a JSON-friendly result summary."""

        return {
            "output_path": str(self.output_path),
            "metadata_path": str(self.metadata_path),
            "figure_path": str(self.figure_path),
            "event_count": self.event_count,
            "row_count": self.row_count,
        }


@dataclass(frozen=True)
class _WindowMetrics:
    trade_rows: int
    active_wallets: int
    total_amount_usd: float
    mean_trade_size_usd: float
    log1p_total_amount_usd: float
    new_wallet_share: float
    top1_concentration: float
    hhi: float


@dataclass(frozen=True)
class _Tier1LeadSignal:
    lag_days: int
    status: str
    source: str
    p_value: float | None
    correlation: float | None


def build_informed_trading_signature(
    events: pd.DataFrame,
    trades: pd.DataFrame,
    prices: pd.DataFrame,
    *,
    baseline_window_days: tuple[int, int] = DEFAULT_BASELINE_WINDOW,
    event_window_days: tuple[int, int] = DEFAULT_EVENT_WINDOW,
    min_baseline_windows: int = DEFAULT_MIN_BASELINE_WINDOWS,
    max_lag_days: int = DEFAULT_MAX_LAG_DAYS,
) -> pd.DataFrame:
    """Return aggregate H3 informed-trading signature rows by curated event."""

    _validate_windows(baseline_window_days, event_window_days)
    _validate_min_baseline_windows(min_baseline_windows)
    _validate_max_lag(max_lag_days)

    event_frame = _validate_events(events)
    trade_frame = _normalize_trades(trades)
    price_frame = _normalize_prices(prices)
    tiered_wallets, activity = _derive_tier_inputs(trade_frame)
    lead_signal = _select_tier1_lead_signal(
        prices=price_frame,
        activity=activity,
        max_lag_days=max_lag_days,
    )
    tier1_trades = _tier1_trades(trade_frame, tiered_wallets)
    first_trade_dates = trade_frame.groupby("wallet_address")["date"].min()
    window_length_days = event_window_days[1] - event_window_days[0] + 1

    rows: list[dict[str, object]] = []
    for event in event_frame.to_dict(orient="records"):
        event_date = event["event_date"]
        event_start = event_date + timedelta(days=event_window_days[0])
        event_end = event_date + timedelta(days=event_window_days[1])
        baseline_start = event_date + timedelta(days=baseline_window_days[0])
        baseline_end = event_date + timedelta(days=baseline_window_days[1])

        event_metrics = _window_metrics(
            trade_frame,
            start_date=event_start,
            end_date=event_end,
            first_trade_dates=first_trade_dates,
        )
        baseline_metrics = _rolling_baseline_metrics(
            trade_frame,
            baseline_start=baseline_start,
            baseline_end=baseline_end,
            window_length_days=window_length_days,
            first_trade_dates=first_trade_dates,
        )
        event_tier1_lead = _tier1_lead_value(
            tier1_trades,
            start_date=event_start,
            end_date=event_end,
            lag_days=lead_signal.lag_days,
        )
        baseline_tier1_lead = _rolling_tier1_lead_values(
            tier1_trades,
            baseline_start=baseline_start,
            baseline_end=baseline_end,
            window_length_days=window_length_days,
            lag_days=lead_signal.lag_days,
        )

        rows.append(
            {
                **_event_fields(event),
                "event_window_label": _window_label(
                    event_window_days,
                    EVENT_WINDOW_LABEL,
                ),
                "baseline_window_label": _window_label(
                    baseline_window_days,
                    BASELINE_WINDOW_LABEL,
                ),
                "event_window_days": window_length_days,
                "baseline_window_count": len(baseline_metrics),
                "trade_rows": event_metrics.trade_rows,
                "active_wallets": event_metrics.active_wallets,
                "total_amount_usd": event_metrics.total_amount_usd,
                "new_wallet_share": event_metrics.new_wallet_share,
                "top1_concentration": event_metrics.top1_concentration,
                "hhi": event_metrics.hhi,
                "abnormal_trade_size_z": _z_score(
                    event_metrics.mean_trade_size_usd,
                    [metric.mean_trade_size_usd for metric in baseline_metrics],
                    min_observations=min_baseline_windows,
                ),
                "active_wallet_z": _z_score(
                    float(event_metrics.active_wallets),
                    [float(metric.active_wallets) for metric in baseline_metrics],
                    min_observations=min_baseline_windows,
                ),
                "volume_z": _z_score(
                    event_metrics.log1p_total_amount_usd,
                    [metric.log1p_total_amount_usd for metric in baseline_metrics],
                    min_observations=min_baseline_windows,
                ),
                "tier1_lead": _z_score(
                    event_tier1_lead,
                    baseline_tier1_lead,
                    min_observations=min_baseline_windows,
                ),
                "tier1_lead_lag_days": lead_signal.lag_days,
                "claim_scope": "aggregate_descriptive_suspicion_diagnostic_only",
                "limitation": (
                    "Daily event windows and observed whale-trade extract; no "
                    "causal, private-information, misconduct, trading, or "
                    "profitability claim."
                ),
            }
        )

    signature = pd.DataFrame(rows)
    signature = _add_percentile_score(signature)
    signature = signature.loc[:, SIGNATURE_COLUMNS].sort_values(
        ["event_date", "event_id"],
    )
    signature = signature.reset_index(drop=True)
    _assert_no_wallet_address_output(signature)
    return signature


def generate_h3_informed_trading_signature(
    *,
    db_path: Path = DB_PATH,
    events_csv_path: Path = SEED_PATH,
    output_path: Path = OUTPUT_PATH,
    metadata_path: Path = METADATA_PATH,
    figure_path: Path = FIGURE_PATH,
    baseline_window_days: tuple[int, int] = DEFAULT_BASELINE_WINDOW,
    event_window_days: tuple[int, int] = DEFAULT_EVENT_WINDOW,
    min_baseline_windows: int = DEFAULT_MIN_BASELINE_WINDOWS,
    max_lag_days: int = DEFAULT_MAX_LAG_DAYS,
    market_id: str | None = None,
    token_id: str | None = None,
) -> H3InformedTradingSignatureResult:
    """Generate bounded H3 informed-trading signature artifacts."""

    events = load_curated_events(events_csv_path)
    trades = load_wallet_trades(db_path)
    normalized_trades = _normalize_trades(trades)
    price_start, price_end = _price_query_bounds(normalized_trades)
    prices = load_daily_polymarket_prices(
        db_path,
        start_date=price_start,
        end_date=price_end,
        market_id=market_id,
        token_id=token_id,
    )
    signature = build_informed_trading_signature(
        events,
        normalized_trades,
        prices,
        baseline_window_days=baseline_window_days,
        event_window_days=event_window_days,
        min_baseline_windows=min_baseline_windows,
        max_lag_days=max_lag_days,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    signature.to_csv(output_path, index=False)
    plot_informed_trading_signature(signature, figure_path)

    metadata = _build_metadata(
        events=events,
        trades=normalized_trades,
        prices=prices,
        signature=signature,
        db_path=db_path,
        events_csv_path=events_csv_path,
        output_path=output_path,
        figure_path=figure_path,
        baseline_window_days=baseline_window_days,
        event_window_days=event_window_days,
        min_baseline_windows=min_baseline_windows,
        max_lag_days=max_lag_days,
    )
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _assert_no_wallet_address_text(output_path)
    _assert_no_wallet_address_text(metadata_path)

    return H3InformedTradingSignatureResult(
        output_path=output_path,
        metadata_path=metadata_path,
        figure_path=figure_path,
        event_count=int(events["event_id"].nunique()),
        row_count=len(signature),
    )


def plot_informed_trading_signature(signature: pd.DataFrame, output_path: Path) -> Path:
    """Write a simple score figure from aggregate signature rows."""

    _require_columns(signature, ("event_id", "suspicion_score"), "signature")
    frame = signature.copy()
    frame["event_label"] = frame["event_id"].astype(str).str.replace(
        "evt_2024_",
        "",
        regex=False,
    )
    frame["event_label"] = frame["event_label"].str.slice(0, 38)
    frame = frame.sort_values("suspicion_score", ascending=True)

    plt.figure(figsize=(10, max(4.8, len(frame) * 0.55)))
    plt.barh(frame["event_label"], frame["suspicion_score"], color="#4c78a8")
    plt.xlim(0, 1)
    plt.xlabel("Percentile-normalized aggregate score")
    plt.ylabel("Curated event")
    plt.title("H3 event-window informed-trading signature")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()
    return output_path


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--events", type=Path, default=SEED_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_PATH)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_PATH)
    parser.add_argument("--baseline-start-day", type=int, default=DEFAULT_BASELINE_WINDOW[0])
    parser.add_argument("--baseline-end-day", type=int, default=DEFAULT_BASELINE_WINDOW[1])
    parser.add_argument("--event-start-day", type=int, default=DEFAULT_EVENT_WINDOW[0])
    parser.add_argument("--event-end-day", type=int, default=DEFAULT_EVENT_WINDOW[1])
    parser.add_argument("--min-baseline-windows", type=int, default=DEFAULT_MIN_BASELINE_WINDOWS)
    parser.add_argument("--max-lag-days", type=int, default=DEFAULT_MAX_LAG_DAYS)
    parser.add_argument("--market-id", default=None)
    parser.add_argument("--token-id", default=None)
    args = parser.parse_args(argv)

    try:
        result = generate_h3_informed_trading_signature(
            db_path=args.db,
            events_csv_path=args.events,
            output_path=args.output,
            metadata_path=args.metadata_output,
            figure_path=args.figure_output,
            baseline_window_days=(args.baseline_start_day, args.baseline_end_day),
            event_window_days=(args.event_start_day, args.event_end_day),
            min_baseline_windows=args.min_baseline_windows,
            max_lag_days=args.max_lag_days,
            market_id=args.market_id,
            token_id=args.token_id,
        )
    except (FileNotFoundError, ValueError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _normalize_trades(trades: pd.DataFrame) -> pd.DataFrame:
    frame = validate_wallet_trades(trades)
    frame["date"] = pd.to_datetime(
        frame["price_timestamp"],
        errors="raise",
        utc=True,
    ).dt.date
    return frame.sort_values(["date", "price_timestamp", "wallet_address"]).reset_index(
        drop=True
    )


def _normalize_prices(prices: pd.DataFrame) -> pd.DataFrame:
    _require_columns(prices, ("date", "price"), "prices")
    frame = prices.loc[:, ["date", "price"]].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.date
    frame["price"] = pd.to_numeric(frame["price"], errors="raise")
    if frame.empty:
        raise ValueError("prices contain no rows")
    return frame.sort_values("date").reset_index(drop=True)


def _derive_tier_inputs(trades: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    wallet_aggregates = compute_wallet_aggregates(trades)
    thresholds = compute_percentile_thresholds(wallet_aggregates)
    tiered_wallets = assign_wallet_tiers(wallet_aggregates, thresholds).loc[
        :,
        ["wallet_address", "tier"],
    ]
    activity, _metadata = build_tiered_wallet_activity(trades, tiered_wallets)
    return tiered_wallets, activity


def _select_tier1_lead_signal(
    *,
    prices: pd.DataFrame,
    activity: pd.DataFrame,
    max_lag_days: int,
) -> _Tier1LeadSignal:
    try:
        series = build_h3_granger_series(prices, activity)
    except ValueError:
        return _Tier1LeadSignal(
            lag_days=1,
            status="fallback_no_aligned_price_activity_series",
            source="fallback_lag_1",
            p_value=None,
            correlation=None,
        )
    if series.empty or TOP_TIER not in set(series["tier"]):
        return _Tier1LeadSignal(
            lag_days=1,
            status="fallback_no_tier1_model_series",
            source="fallback_lag_1",
            p_value=None,
            correlation=None,
        )

    correlations = compute_lead_lag_correlations(series, max_lag_days=max_lag_days)
    granger = compute_granger_results(series, max_lag_days=max_lag_days)
    tier_granger = granger[
        (granger["tier"] == TOP_TIER)
        & (granger["status"] == "ok")
        & granger["p_value"].notna()
    ].copy()
    if not tier_granger.empty:
        selected = tier_granger.sort_values(["p_value", "lag_days"]).iloc[0]
        lag_days = int(selected["lag_days"])
        correlation = _correlation_for_lag(correlations, lag_days)
        return _Tier1LeadSignal(
            lag_days=lag_days,
            status="selected_min_tier1_granger_p_value",
            source="operations.analysis.h3_granger_baseline",
            p_value=float(selected["p_value"]),
            correlation=correlation,
        )

    tier_correlations = correlations[
        (correlations["tier"] == TOP_TIER)
        & (correlations["status"] == "ok")
        & correlations["correlation"].notna()
        & (correlations["lag_days"] >= 1)
    ].copy()
    if not tier_correlations.empty:
        selected = tier_correlations.sort_values(
            ["correlation", "lag_days"],
            ascending=[False, True],
        ).iloc[0]
        return _Tier1LeadSignal(
            lag_days=int(selected["lag_days"]),
            status="selected_max_tier1_lead_lag_correlation",
            source="operations.analysis.h3_granger_baseline",
            p_value=None,
            correlation=float(selected["correlation"]),
        )

    return _Tier1LeadSignal(
        lag_days=1,
        status="fallback_no_successful_tier1_lead_lag_rows",
        source="fallback_lag_1",
        p_value=None,
        correlation=None,
    )


def _correlation_for_lag(correlations: pd.DataFrame, lag_days: int) -> float | None:
    row = correlations[
        (correlations["tier"] == TOP_TIER)
        & (correlations["lag_days"] == lag_days)
        & (correlations["status"] == "ok")
    ]
    if row.empty or pd.isna(row.iloc[0]["correlation"]):
        return None
    return float(row.iloc[0]["correlation"])


def _tier1_trades(trades: pd.DataFrame, tiered_wallets: pd.DataFrame) -> pd.DataFrame:
    joined = trades.merge(tiered_wallets, on="wallet_address", how="left")
    missing_tiers = int(joined["tier"].isna().sum())
    if missing_tiers:
        raise ValueError(f"{missing_tiers} trade rows have no wallet tier assignment")
    return joined[joined["tier"] == TOP_TIER].copy()


def _validate_events(events: pd.DataFrame) -> pd.DataFrame:
    _require_columns(events, EVENT_COLUMNS, "events")
    frame = events.loc[:, EVENT_COLUMNS].copy()
    for column in ("event_id", "title", "event_type", "source_url"):
        if frame[column].isna().any() or (
            frame[column].astype(str).str.strip() == ""
        ).any():
            raise ValueError(f"events contain blank values in {column}")
        frame[column] = frame[column].astype(str).str.strip()
    if frame["event_id"].duplicated().any():
        duplicates = sorted(frame.loc[frame["event_id"].duplicated(), "event_id"].unique())
        raise ValueError(f"events contain duplicate event_id values: {duplicates}")
    frame["event_date"] = pd.to_datetime(frame["event_date"], errors="raise").dt.date
    return frame.sort_values(["event_date", "event_id"]).reset_index(drop=True)


def _event_fields(event: dict[str, object]) -> dict[str, object]:
    return {
        "event_id": event["event_id"],
        "event_date": event["event_date"].isoformat(),
        "title": event["title"],
        "event_type": event["event_type"],
    }


def _window_metrics(
    trades: pd.DataFrame,
    *,
    start_date: date,
    end_date: date,
    first_trade_dates: pd.Series,
) -> _WindowMetrics:
    frame = _trades_between(trades, start_date=start_date, end_date=end_date)
    trade_rows = int(len(frame))
    total_amount = float(frame["amount_usd"].sum()) if trade_rows else 0.0
    mean_trade_size = total_amount / trade_rows if trade_rows else 0.0
    active_wallets = int(frame["wallet_address"].nunique()) if trade_rows else 0
    if active_wallets:
        active = pd.Index(frame["wallet_address"].unique())
        first_dates = first_trade_dates.reindex(active)
        new_count = int(
            ((first_dates >= start_date) & (first_dates <= end_date)).sum()
        )
        new_wallet_share = new_count / active_wallets
    else:
        new_wallet_share = 0.0

    if total_amount > 0:
        wallet_amounts = (
            frame.groupby("wallet_address")["amount_usd"]
            .sum()
            .sort_values(ascending=False)
        )
        shares = wallet_amounts / total_amount
        top1_concentration = float(shares.iloc[0])
        hhi = float((shares**2).sum())
    else:
        top1_concentration = 0.0
        hhi = 0.0

    return _WindowMetrics(
        trade_rows=trade_rows,
        active_wallets=active_wallets,
        total_amount_usd=total_amount,
        mean_trade_size_usd=mean_trade_size,
        log1p_total_amount_usd=float(np.log1p(total_amount)),
        new_wallet_share=float(new_wallet_share),
        top1_concentration=top1_concentration,
        hhi=hhi,
    )


def _rolling_baseline_metrics(
    trades: pd.DataFrame,
    *,
    baseline_start: date,
    baseline_end: date,
    window_length_days: int,
    first_trade_dates: pd.Series,
) -> list[_WindowMetrics]:
    metrics: list[_WindowMetrics] = []
    for start in _rolling_window_starts(
        baseline_start,
        baseline_end,
        window_length_days,
    ):
        end = start + timedelta(days=window_length_days - 1)
        metrics.append(
            _window_metrics(
                trades,
                start_date=start,
                end_date=end,
                first_trade_dates=first_trade_dates,
            )
        )
    return metrics


def _tier1_lead_value(
    tier1_trades: pd.DataFrame,
    *,
    start_date: date,
    end_date: date,
    lag_days: int,
) -> float:
    lead_start = start_date - timedelta(days=lag_days)
    lead_end = end_date - timedelta(days=lag_days)
    lead_trades = _trades_between(tier1_trades, start_date=lead_start, end_date=lead_end)
    return float(np.log1p(lead_trades["amount_usd"].sum()))


def _rolling_tier1_lead_values(
    tier1_trades: pd.DataFrame,
    *,
    baseline_start: date,
    baseline_end: date,
    window_length_days: int,
    lag_days: int,
) -> list[float]:
    values: list[float] = []
    for start in _rolling_window_starts(
        baseline_start,
        baseline_end,
        window_length_days,
    ):
        end = start + timedelta(days=window_length_days - 1)
        values.append(
            _tier1_lead_value(
                tier1_trades,
                start_date=start,
                end_date=end,
                lag_days=lag_days,
            )
        )
    return values


def _rolling_window_starts(
    start_date: date,
    end_date: date,
    window_length_days: int,
) -> Iterable[date]:
    last_start = end_date - timedelta(days=window_length_days - 1)
    if last_start < start_date:
        return []
    return (
        start_date + timedelta(days=offset)
        for offset in range((last_start - start_date).days + 1)
    )


def _trades_between(
    trades: pd.DataFrame,
    *,
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    mask = (trades["date"] >= start_date) & (trades["date"] <= end_date)
    return trades.loc[mask].copy()


def _z_score(
    observed: float,
    baseline_values: Sequence[float],
    *,
    min_observations: int,
) -> float | None:
    values = pd.to_numeric(pd.Series(list(baseline_values)), errors="coerce").dropna()
    if len(values) < min_observations:
        return None
    mean = float(values.mean())
    std = float(values.std(ddof=0))
    if std <= 0:
        return 0.0 if observed == mean else None
    return float((observed - mean) / std)


def _add_percentile_score(signature: pd.DataFrame) -> pd.DataFrame:
    frame = signature.copy()
    percentile_columns: list[str] = []
    for feature in FEATURE_COLUMNS:
        percentile_column = f"{feature}_percentile"
        frame[percentile_column] = _percentile_normalize(frame[feature])
        percentile_columns.append(percentile_column)

    percentiles = frame.loc[:, percentile_columns]
    frame["score_feature_count"] = percentiles.notna().sum(axis=1).astype(int)
    frame["suspicion_score"] = percentiles.mean(axis=1, skipna=True).fillna(0.0)
    frame["suspicion_score"] = frame["suspicion_score"].clip(lower=0.0, upper=1.0)
    return frame


def _percentile_normalize(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    result = pd.Series(np.nan, index=values.index, dtype=float)
    valid = numeric.dropna()
    if valid.empty:
        return result
    if len(valid) == 1:
        result.loc[valid.index] = 0.5
        return result
    ranks = valid.rank(method="average", ascending=True)
    result.loc[valid.index] = (ranks - 1.0) / (len(valid) - 1.0)
    return result.clip(lower=0.0, upper=1.0)


def _price_query_bounds(trades: pd.DataFrame) -> tuple[date, date]:
    return min(trades["date"]), max(trades["date"])


def _build_metadata(
    *,
    events: pd.DataFrame,
    trades: pd.DataFrame,
    prices: pd.DataFrame,
    signature: pd.DataFrame,
    db_path: Path,
    events_csv_path: Path,
    output_path: Path,
    figure_path: Path,
    baseline_window_days: tuple[int, int],
    event_window_days: tuple[int, int],
    min_baseline_windows: int,
    max_lag_days: int,
) -> dict[str, Any]:
    minimum_amount = float(pd.to_numeric(trades["amount_usd"], errors="raise").min())
    return {
        "method": {
            "name": "deterministic_h3_informed_trading_signature",
            "baseline_window_days": {
                "start": baseline_window_days[0],
                "end": baseline_window_days[1],
                "label": _window_label(baseline_window_days, BASELINE_WINDOW_LABEL),
            },
            "event_window_days": {
                "start": event_window_days[0],
                "end": event_window_days[1],
                "label": _window_label(event_window_days, EVENT_WINDOW_LABEL),
            },
            "min_baseline_windows": min_baseline_windows,
            "max_lag_days": max_lag_days,
            "score_policy": {
                "normalization": "within-run percentile ranks per feature",
                "combination": "mean_of_available_feature_percentiles",
                "fixed_thresholds_used": False,
                "feature_columns": list(FEATURE_COLUMNS),
            },
            "tier_policy": "wallet_cumulative_amount_usd_percentiles",
            "tier1_lead_source": "existing_h3_daily_lead_lag_granger_diagnostic",
        },
        "input": {
            "db_path": str(db_path),
            "events_csv_path": str(events_csv_path),
            "event_count": int(events["event_id"].nunique()),
            "trade_row_count": int(len(trades)),
            "price_row_count": int(len(prices)),
            "input_tables": ["whale_trades", "polymarket_prices"],
        },
        "source_filter_metadata": {
            "minimum_observed_amount_usd": minimum_amount,
            "minimum_observed_amount_note": (
                "Observed source-filter metadata only; not an analytical "
                "threshold or whale definition."
            ),
            "direction_distribution": _direction_distribution(trades),
        },
        "output": {
            "output_path": str(output_path),
            "figure_path": str(figure_path),
            "row_count": int(len(signature)),
            "columns": list(SIGNATURE_COLUMNS),
            "contains_wallet_addresses": False,
            "claim_scope": "aggregate_descriptive_suspicion_diagnostic_only",
            "score_min": _safe_float(signature["suspicion_score"].min()),
            "score_max": _safe_float(signature["suspicion_score"].max()),
        },
        "guardrails": {
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_output_wallet_addresses": True,
            "does_not_claim_true_causality": True,
            "does_not_claim_private_information": True,
            "does_not_claim_trading_profitability": True,
            "does_not_send_orders": True,
            "blocked_claims": [
                _blocked_claim_word() + " trading",
                "private information proof",
                "causal proof",
                "profitability claim",
                "misconduct finding",
            ],
        },
        "limitations": {
            "daily_event_windows_only": True,
            "observed_filtered_trade_extract_only": True,
            "wallet_tiers_are_dataset_relative": True,
            "percentile_score_is_relative_to_current_event_set": True,
            "not_a_computed_" + _blocked_claim_word() + "_label": True,
        },
    }


def _direction_distribution(trades: pd.DataFrame) -> dict[str, dict[str, int]]:
    grouped = (
        trades.groupby("direction")
        .agg(trade_rows=("amount_usd", "size"), active_wallets=("wallet_address", "nunique"))
        .reset_index()
        .sort_values("direction")
    )
    return {
        str(row["direction"]): {
            "trade_rows": int(row["trade_rows"]),
            "active_wallets": int(row["active_wallets"]),
        }
        for _, row in grouped.iterrows()
    }


def _assert_no_wallet_address_output(frame: pd.DataFrame) -> None:
    forbidden_columns = {"wallet_address", "tx_hash"}
    exposed_columns = forbidden_columns.intersection(frame.columns)
    if exposed_columns:
        raise ValueError(f"output exposes forbidden columns: {sorted(exposed_columns)}")
    text = frame.to_csv(index=False)
    if ADDRESS_LIKE_PATTERN.search(text):
        raise ValueError("output exposes address-like values")


def _assert_no_wallet_address_text(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if ADDRESS_LIKE_PATTERN.search(text):
        raise ValueError(f"{path} exposes address-like values")


def _safe_float(value: object) -> float | None:
    if pd.isna(value):
        return None
    return float(value)


def _window_label(window: tuple[int, int], default_label: str) -> str:
    if window == DEFAULT_BASELINE_WINDOW:
        return BASELINE_WINDOW_LABEL
    if window == DEFAULT_EVENT_WINDOW:
        return EVENT_WINDOW_LABEL
    return f"window_{window[0]}d_to_{window[1]}d"


def _validate_windows(
    baseline_window_days: tuple[int, int],
    event_window_days: tuple[int, int],
) -> None:
    if baseline_window_days[0] > baseline_window_days[1]:
        raise ValueError("baseline_window_days start must be <= end")
    if event_window_days[0] > event_window_days[1]:
        raise ValueError("event_window_days start must be <= end")
    if baseline_window_days[1] >= event_window_days[0]:
        raise ValueError("baseline window must end before event window starts")


def _validate_min_baseline_windows(value: int) -> None:
    if value < 1:
        raise ValueError("min_baseline_windows must be >= 1")


def _validate_max_lag(value: int) -> None:
    if value < 1:
        raise ValueError("max_lag_days must be >= 1")


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _blocked_claim_word() -> str:
    return "inside" + "r"


if __name__ == "__main__":
    raise SystemExit(main())
