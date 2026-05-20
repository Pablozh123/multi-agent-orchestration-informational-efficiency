"""Generate deterministic historical event-centred anomaly outputs.

The module scores market movement, wallet-tier activity, active-wallet counts,
and top-tier concentration around curated politics/geo event dates. It writes
file-based artifacts only and does not call LLMs, agents, MCP tools, external
APIs, or RCP sources.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd

from operations.analysis.event_study import compute_daily_price_changes
from operations.analysis.h3_lead_time_histograms import load_tiered_activity
from operations.analysis.run_h2_event_windows import (
    RESULTS_DIR,
    SEED_PATH,
    load_curated_events,
    load_daily_polymarket_prices,
)
from operations.analysis.tiered_wallet_activity import ACTIVITY_OUTPUT
from operations.analysis.wallet_distribution_inventory import TIER_ORDER
from operations.db.migrations import DB_PATH


DEFAULT_BASELINE_WINDOW = (-30, -8)
DEFAULT_EVENT_WINDOW = (-1, 3)
DEFAULT_MIN_BASELINE_OBSERVATIONS = 3
ANOMALY_Z_THRESHOLD = 2.0
ANOMALY_PERCENTILE_THRESHOLD = 0.95
BASELINE_WINDOW_LABEL = "baseline_minus_30d_to_minus_8d"
EVENT_WINDOW_LABEL = "event_minus_1d_to_plus_3d"
ROWS_OUTPUT = RESULTS_DIR / "h3_event_wallet_anomaly_rows.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h3_event_wallet_anomaly_summary.csv"
METADATA_OUTPUT = RESULTS_DIR / "h3_event_wallet_anomaly_metadata.json"

EVENT_COLUMNS: tuple[str, ...] = (
    "event_id",
    "event_date",
    "title",
    "event_type",
    "source_url",
)
ANOMALY_ROW_COLUMNS: tuple[str, ...] = (
    "event_id",
    "event_date",
    "title",
    "event_type",
    "source_url",
    "market_id",
    "date",
    "relative_day",
    "event_window_label",
    "baseline_window_label",
    "anomaly_type",
    "tier",
    "metric_name",
    "observed_value",
    "baseline_observations",
    "baseline_mean",
    "baseline_std",
    "z_score",
    "percentile_rank",
    "is_anomaly",
    "status",
    "source_artifact",
    "limitation",
)
ANOMALY_SUMMARY_COLUMNS: tuple[str, ...] = (
    "event_id",
    "event_date",
    "title",
    "event_type",
    "source_url",
    "market_id",
    "event_window_label",
    "baseline_window_label",
    "anomaly_type",
    "tier",
    "metric_name",
    "event_window_days",
    "observed_day_count",
    "baseline_observations",
    "max_observed_value",
    "max_z_score",
    "max_percentile_rank",
    "anomaly_day_count",
    "source_artifact",
    "limitation",
    "claim_scope",
)


@dataclass(frozen=True)
class H3EventWalletAnomalyResult:
    """Summary of generated historical anomaly artifacts."""

    rows_path: Path
    summary_path: Path
    metadata_path: Path
    event_count: int
    row_count: int
    summary_row_count: int

    def to_dict(self) -> dict[str, str | int]:
        """Return a JSON-friendly result summary."""

        return {
            "rows_path": str(self.rows_path),
            "summary_path": str(self.summary_path),
            "metadata_path": str(self.metadata_path),
            "event_count": self.event_count,
            "row_count": self.row_count,
            "summary_row_count": self.summary_row_count,
        }


def build_historical_anomaly_rows(
    events: pd.DataFrame,
    prices: pd.DataFrame,
    activity: pd.DataFrame,
    *,
    baseline_window_days: tuple[int, int] = DEFAULT_BASELINE_WINDOW,
    event_window_days: tuple[int, int] = DEFAULT_EVENT_WINDOW,
    min_baseline_observations: int = DEFAULT_MIN_BASELINE_OBSERVATIONS,
    market_id: str | None = None,
) -> pd.DataFrame:
    """Return event-centred historical anomaly rows."""

    _validate_windows(baseline_window_days, event_window_days)
    _validate_min_baseline_observations(min_baseline_observations)
    event_frame = _validate_events(events)
    metric_series = _build_metric_series(prices, activity)

    rows: list[dict[str, object]] = []
    for event in event_frame.to_dict(orient="records"):
        event_date = event["event_date"]
        baseline_start = event_date + timedelta(days=baseline_window_days[0])
        baseline_end = event_date + timedelta(days=baseline_window_days[1])
        for metric in metric_series:
            baseline_values = _values_between(
                metric.frame,
                start_date=baseline_start,
                end_date=baseline_end,
            )
            score_base = _baseline_stats(
                baseline_values,
                min_observations=min_baseline_observations,
            )
            for offset in range(event_window_days[0], event_window_days[1] + 1):
                target_date = event_date + timedelta(days=offset)
                observed = _observed_value(metric.frame, target_date)
                score = _score_observation(
                    observed,
                    baseline_values,
                    score_base,
                )
                rows.append(
                    {
                        **_event_fields(event),
                        "market_id": market_id or "",
                        "date": target_date.isoformat(),
                        "relative_day": offset,
                        "event_window_label": _window_label(
                            event_window_days,
                            EVENT_WINDOW_LABEL,
                        ),
                        "baseline_window_label": _window_label(
                            baseline_window_days,
                            BASELINE_WINDOW_LABEL,
                        ),
                        "anomaly_type": metric.anomaly_type,
                        "tier": metric.tier,
                        "metric_name": metric.metric_name,
                        **score,
                        "source_artifact": metric.source_artifact,
                        "limitation": metric.limitation,
                    }
                )

    return pd.DataFrame(rows, columns=ANOMALY_ROW_COLUMNS)


def summarize_historical_anomalies(rows: pd.DataFrame) -> pd.DataFrame:
    """Return compact event and metric anomaly summaries."""

    _require_columns(rows, ANOMALY_ROW_COLUMNS, "anomaly rows")
    if rows.empty:
        return pd.DataFrame(columns=ANOMALY_SUMMARY_COLUMNS)

    summary_rows: list[dict[str, object]] = []
    group_columns = (
        "event_id",
        "event_date",
        "title",
        "event_type",
        "source_url",
        "market_id",
        "event_window_label",
        "baseline_window_label",
        "anomaly_type",
        "tier",
        "metric_name",
        "source_artifact",
        "limitation",
    )
    for keys, group in rows.groupby(list(group_columns), dropna=False, sort=True):
        values = dict(zip(group_columns, keys))
        observed = pd.to_numeric(group["observed_value"], errors="coerce")
        z_scores = pd.to_numeric(group["z_score"], errors="coerce")
        percentiles = pd.to_numeric(group["percentile_rank"], errors="coerce")
        summary_rows.append(
            {
                **values,
                "event_window_days": int(len(group)),
                "observed_day_count": int(observed.notna().sum()),
                "baseline_observations": int(group["baseline_observations"].max()),
                "max_observed_value": _safe_max(observed),
                "max_z_score": _safe_max(z_scores),
                "max_percentile_rank": _safe_max(percentiles),
                "anomaly_day_count": int(group["is_anomaly"].astype(bool).sum()),
                "claim_scope": "descriptive_historical_anomaly_diagnostic",
            }
        )

    return pd.DataFrame(summary_rows, columns=ANOMALY_SUMMARY_COLUMNS).sort_values(
        ["event_date", "event_id", "anomaly_type", "tier", "metric_name"]
    ).reset_index(drop=True)


def generate_h3_event_wallet_anomalies(
    *,
    db_path: Path = DB_PATH,
    events_csv_path: Path = SEED_PATH,
    activity_path: Path = ACTIVITY_OUTPUT,
    rows_path: Path = ROWS_OUTPUT,
    summary_path: Path = SUMMARY_OUTPUT,
    metadata_path: Path = METADATA_OUTPUT,
    baseline_window_days: tuple[int, int] = DEFAULT_BASELINE_WINDOW,
    event_window_days: tuple[int, int] = DEFAULT_EVENT_WINDOW,
    min_baseline_observations: int = DEFAULT_MIN_BASELINE_OBSERVATIONS,
    market_id: str | None = None,
    token_id: str | None = None,
) -> H3EventWalletAnomalyResult:
    """Generate deterministic historical anomaly row, summary, and metadata files."""

    _validate_windows(baseline_window_days, event_window_days)
    events = load_curated_events(events_csv_path)
    activity = load_tiered_activity(activity_path)
    price_start, price_end = _price_query_bounds(
        events,
        baseline_window_days,
        event_window_days,
    )
    prices = load_daily_polymarket_prices(
        db_path,
        start_date=price_start,
        end_date=price_end,
        market_id=market_id,
        token_id=token_id,
    )

    rows = build_historical_anomaly_rows(
        events,
        prices,
        activity,
        baseline_window_days=baseline_window_days,
        event_window_days=event_window_days,
        min_baseline_observations=min_baseline_observations,
        market_id=market_id,
    )
    summary = summarize_historical_anomalies(rows)

    rows_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    rows.to_csv(rows_path, index=False)
    summary.to_csv(summary_path, index=False)
    metadata_path.write_text(
        json.dumps(
            _build_metadata(
                events=events,
                activity=activity,
                prices=prices,
                rows=rows,
                summary=summary,
                db_path=db_path,
                events_csv_path=events_csv_path,
                activity_path=activity_path,
                baseline_window_days=baseline_window_days,
                event_window_days=event_window_days,
                min_baseline_observations=min_baseline_observations,
                market_id=market_id,
                token_id=token_id,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return H3EventWalletAnomalyResult(
        rows_path=rows_path,
        summary_path=summary_path,
        metadata_path=metadata_path,
        event_count=len(events),
        row_count=len(rows),
        summary_row_count=len(summary),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--events", type=Path, default=SEED_PATH)
    parser.add_argument("--activity", type=Path, default=ACTIVITY_OUTPUT)
    parser.add_argument("--rows-output", type=Path, default=ROWS_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    parser.add_argument("--baseline-start-day", type=int, default=DEFAULT_BASELINE_WINDOW[0])
    parser.add_argument("--baseline-end-day", type=int, default=DEFAULT_BASELINE_WINDOW[1])
    parser.add_argument("--event-start-day", type=int, default=DEFAULT_EVENT_WINDOW[0])
    parser.add_argument("--event-end-day", type=int, default=DEFAULT_EVENT_WINDOW[1])
    parser.add_argument("--min-baseline-observations", type=int, default=DEFAULT_MIN_BASELINE_OBSERVATIONS)
    parser.add_argument("--market-id", default=None)
    parser.add_argument("--token-id", default=None)
    args = parser.parse_args(argv)

    try:
        result = generate_h3_event_wallet_anomalies(
            db_path=args.db,
            events_csv_path=args.events,
            activity_path=args.activity,
            rows_path=args.rows_output,
            summary_path=args.summary_output,
            metadata_path=args.metadata_output,
            baseline_window_days=(args.baseline_start_day, args.baseline_end_day),
            event_window_days=(args.event_start_day, args.event_end_day),
            min_baseline_observations=args.min_baseline_observations,
            market_id=args.market_id,
            token_id=args.token_id,
        )
    except (FileNotFoundError, ValueError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


@dataclass(frozen=True)
class _MetricSeries:
    anomaly_type: str
    tier: str
    metric_name: str
    frame: pd.DataFrame
    source_artifact: str
    limitation: str


def _build_metric_series(prices: pd.DataFrame, activity: pd.DataFrame) -> list[_MetricSeries]:
    price_changes = compute_daily_price_changes(prices)
    price_changes["date"] = pd.to_datetime(price_changes["date"], errors="raise").dt.date
    market_frame = pd.DataFrame(
        {
            "date": price_changes["date"],
            "value": price_changes["price_change"].abs(),
        }
    )

    activity_frame = load_tiered_activity_from_frame(activity)
    activity_frame["date"] = pd.to_datetime(activity_frame["date"], errors="raise").dt.date

    metric_series = [
        _MetricSeries(
            anomaly_type="market_move_anomaly",
            tier="market",
            metric_name="absolute_price_change",
            frame=market_frame,
            source_artifact="data/thesis.db:polymarket_prices",
            limitation="daily market price changes only",
        )
    ]
    for tier in TIER_ORDER:
        tier_frame = activity_frame[activity_frame["tier"] == tier].copy()
        amount_frame = pd.DataFrame(
            {
                "date": tier_frame["date"],
                "value": np.log1p(tier_frame["total_amount_usd"]),
            }
        )
        active_wallet_frame = pd.DataFrame(
            {
                "date": tier_frame["date"],
                "value": tier_frame["active_wallets"].astype(float),
            }
        )
        metric_series.extend(
            [
                _MetricSeries(
                    anomaly_type="wallet_tier_amount_anomaly",
                    tier=tier,
                    metric_name="log1p_total_amount_usd",
                    frame=amount_frame,
                    source_artifact="data/results/h3_tiered_wallet_activity_daily.csv",
                    limitation="BUY-only observed wallet activity extract",
                ),
                _MetricSeries(
                    anomaly_type="active_wallet_anomaly",
                    tier=tier,
                    metric_name="active_wallets",
                    frame=active_wallet_frame,
                    source_artifact="data/results/h3_tiered_wallet_activity_daily.csv",
                    limitation="aggregate tier count only; no wallet-address output",
                ),
            ]
        )

    concentration_frame = _top_tier_share_frame(activity_frame)
    metric_series.append(
        _MetricSeries(
            anomaly_type="top_tier_concentration_anomaly",
            tier="all_tiers",
            metric_name="tier_1_total_amount_share",
            frame=concentration_frame,
            source_artifact="data/results/h3_tiered_wallet_activity_daily.csv",
            limitation="concentration of observed tier activity, not wallet performance",
        )
    )
    return metric_series


def load_tiered_activity_from_frame(activity: pd.DataFrame) -> pd.DataFrame:
    """Validate an in-memory tier activity frame."""

    from operations.analysis.h3_lead_time_histograms import validate_tiered_activity

    return validate_tiered_activity(activity)


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
        "source_url": event["source_url"],
    }


def _top_tier_share_frame(activity: pd.DataFrame) -> pd.DataFrame:
    grouped = activity.groupby("date", as_index=False).agg(
        total_amount_usd=("total_amount_usd", "sum")
    )
    top_tier = (
        activity[activity["tier"] == "tier_1_top_1pct"]
        .groupby("date", as_index=False)
        .agg(top_tier_amount_usd=("total_amount_usd", "sum"))
    )
    frame = grouped.merge(top_tier, on="date", how="left").fillna(
        {"top_tier_amount_usd": 0.0}
    )
    frame["value"] = np.where(
        frame["total_amount_usd"] > 0,
        frame["top_tier_amount_usd"] / frame["total_amount_usd"],
        0.0,
    )
    return frame.loc[:, ["date", "value"]]


def _values_between(frame: pd.DataFrame, *, start_date: date, end_date: date) -> pd.Series:
    mask = (frame["date"] >= start_date) & (frame["date"] <= end_date)
    return pd.to_numeric(frame.loc[mask, "value"], errors="coerce").dropna()


def _observed_value(frame: pd.DataFrame, target_date: date) -> float | None:
    rows = frame.loc[frame["date"] == target_date, "value"]
    if rows.empty:
        return None
    return float(rows.iloc[-1])


def _baseline_stats(
    values: pd.Series,
    *,
    min_observations: int,
) -> dict[str, float | int | str | None]:
    observation_count = int(values.count())
    if observation_count < min_observations:
        return {
            "baseline_observations": observation_count,
            "baseline_mean": None,
            "baseline_std": None,
            "status": "insufficient_baseline",
        }
    mean = float(values.mean())
    std = float(values.std(ddof=0))
    return {
        "baseline_observations": observation_count,
        "baseline_mean": mean,
        "baseline_std": std,
        "status": "ok" if std > 0 else "zero_baseline_variance",
    }


def _score_observation(
    observed: float | None,
    baseline_values: pd.Series,
    score_base: dict[str, float | int | str | None],
) -> dict[str, object]:
    if observed is None:
        return {
            "observed_value": None,
            "baseline_observations": score_base["baseline_observations"],
            "baseline_mean": score_base["baseline_mean"],
            "baseline_std": score_base["baseline_std"],
            "z_score": None,
            "percentile_rank": None,
            "is_anomaly": False,
            "status": "missing_observation",
        }

    status = str(score_base["status"])
    percentile_rank = _percentile_rank(baseline_values, observed)
    z_score: float | None = None
    if status == "ok":
        z_score = (observed - float(score_base["baseline_mean"])) / float(
            score_base["baseline_std"]
        )
    elif status == "zero_baseline_variance" and observed == score_base["baseline_mean"]:
        z_score = 0.0

    is_anomaly = (
        (z_score is not None and z_score >= ANOMALY_Z_THRESHOLD)
        or (
            percentile_rank is not None
            and percentile_rank >= ANOMALY_PERCENTILE_THRESHOLD
            and observed > float(score_base["baseline_mean"] or 0.0)
        )
    )
    return {
        "observed_value": observed,
        "baseline_observations": score_base["baseline_observations"],
        "baseline_mean": score_base["baseline_mean"],
        "baseline_std": score_base["baseline_std"],
        "z_score": z_score,
        "percentile_rank": percentile_rank,
        "is_anomaly": bool(is_anomaly),
        "status": status,
    }


def _percentile_rank(values: pd.Series, observed: float) -> float | None:
    if values.empty:
        return None
    return float((values <= observed).sum() / len(values))


def _price_query_bounds(
    events: pd.DataFrame,
    baseline_window_days: tuple[int, int],
    event_window_days: tuple[int, int],
) -> tuple[date, date]:
    event_dates = pd.to_datetime(events["event_date"], errors="raise").dt.date
    start_offset = min(baseline_window_days[0], event_window_days[0]) - 1
    end_offset = max(baseline_window_days[1], event_window_days[1])
    return min(event_dates) + timedelta(days=start_offset), max(event_dates) + timedelta(
        days=end_offset
    )


def _build_metadata(
    *,
    events: pd.DataFrame,
    activity: pd.DataFrame,
    prices: pd.DataFrame,
    rows: pd.DataFrame,
    summary: pd.DataFrame,
    db_path: Path,
    events_csv_path: Path,
    activity_path: Path,
    baseline_window_days: tuple[int, int],
    event_window_days: tuple[int, int],
    min_baseline_observations: int,
    market_id: str | None,
    token_id: str | None,
) -> dict[str, Any]:
    return {
        "method": {
            "name": "deterministic_historical_politics_geo_anomaly_output",
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
            "min_baseline_observations": min_baseline_observations,
            "anomaly_rule": {
                "z_score_threshold": ANOMALY_Z_THRESHOLD,
                "percentile_rank_threshold": ANOMALY_PERCENTILE_THRESHOLD,
                "tail": "upper_tail_for_all_reported_non_negative_metrics",
            },
        },
        "input": {
            "db_path": str(db_path),
            "events_csv_path": str(events_csv_path),
            "activity_path": str(activity_path),
            "event_count": int(len(events)),
            "price_row_count": int(len(prices)),
            "activity_row_count": int(len(activity)),
            "market_id": market_id or "",
            "token_id": token_id or "",
        },
        "output": {
            "row_count": int(len(rows)),
            "summary_row_count": int(len(summary)),
            "row_columns": list(ANOMALY_ROW_COLUMNS),
            "summary_columns": list(ANOMALY_SUMMARY_COLUMNS),
            "contains_wallet_addresses": False,
            "claim_scope": "descriptive_historical_anomaly_diagnostics_only",
            "anomaly_counts_by_type": _counts_by_type(rows),
        },
        "limitations": {
            "daily_alignment_only": True,
            "uses_existing_curated_us_election_events": True,
            "uses_observed_buy_side_activity_extract": True,
            "does_not_use_rcp": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_send_orders": True,
            "does_not_measure_wallet_performance": True,
        },
    }


def _counts_by_type(rows: pd.DataFrame) -> dict[str, int]:
    counts = rows.loc[rows["is_anomaly"].astype(bool), "anomaly_type"].value_counts()
    return {str(key): int(value) for key, value in counts.sort_index().items()}


def _safe_max(values: pd.Series) -> float | None:
    clean = values.dropna()
    if clean.empty:
        return None
    return float(clean.max())


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


def _validate_min_baseline_observations(value: int) -> None:
    if value < 1:
        raise ValueError("min_baseline_observations must be >= 1")


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


if __name__ == "__main__":
    raise SystemExit(main())
