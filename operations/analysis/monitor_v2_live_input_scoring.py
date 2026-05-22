"""Score local replay-first monitor v2 live-style input files.

This module bridges validated local live-style CSV files into deterministic
monitor v2 alert outputs. It is a diagnostic replay bridge only: it does not
call external APIs, WebSockets, databases, LLMs, agents, MCP tools, ML systems,
or order-execution paths.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
from pydantic import ValidationError

from operations.analysis.monitor_v2_live_input_batch import (
    LIVE_EVENT_CANDIDATES_OUTPUT,
    LIVE_MARKET_SNAPSHOTS_OUTPUT,
    LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT,
    LIVE_WATCHLIST_OUTPUT,
    validate_live_batch_consistency,
)
from operations.analysis.monitor_v2_live_input_validation import (
    validate_live_event_candidates,
    validate_live_input_files,
    validate_live_market_snapshots,
    validate_live_market_watch_items,
    validate_live_wallet_tier_snapshots,
)
from operations.analysis.monitor_v2_snapshot import (
    ALERT_ROW_COLUMNS,
    ALERT_SUMMARY_COLUMNS,
    EVENT_ACCEPTED_STATUSES,
    SNAPSHOT_COLUMNS,
    build_monitor_v2_alert_rows,
    summarize_monitor_v2_alerts,
)
from operations.analysis.run_h2_event_windows import RESULTS_DIR


LIVE_SCORING_SNAPSHOTS_OUTPUT = RESULTS_DIR / "monitor_v2_live_scoring_snapshots.csv"
LIVE_ALERT_ROWS_OUTPUT = RESULTS_DIR / "monitor_v2_live_alert_rows.csv"
LIVE_ALERT_SUMMARY_OUTPUT = RESULTS_DIR / "monitor_v2_live_alert_summary.csv"
LIVE_SCORING_VALIDATION_REPORT_OUTPUT = (
    RESULTS_DIR / "monitor_v2_live_scoring_validation_report.json"
)
LIVE_SCORING_METADATA_OUTPUT = RESULTS_DIR / "monitor_v2_live_scoring_metadata.json"

DIAGNOSTIC_BASELINE_OBSERVATIONS = 3
DIAGNOSTIC_MIN_BASELINE_OBSERVATIONS = 2


@dataclass(frozen=True)
class LiveMonitorInputs:
    """Validated local live-style monitor v2 input frames."""

    watchlist: pd.DataFrame
    market_snapshots: pd.DataFrame
    wallet_tier_snapshots: pd.DataFrame
    event_candidates: pd.DataFrame
    validation_report: dict[str, Any]


@dataclass(frozen=True)
class LiveScoringResult:
    """Summary of generated local live-style scoring artifacts."""

    snapshots_path: Path
    rows_path: Path
    summary_path: Path
    validation_report_path: Path
    metadata_path: Path
    snapshot_count: int
    alert_row_count: int
    alert_count: int
    summary_row_count: int

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "snapshots_path": str(self.snapshots_path),
            "rows_path": str(self.rows_path),
            "summary_path": str(self.summary_path),
            "validation_report_path": str(self.validation_report_path),
            "metadata_path": str(self.metadata_path),
            "snapshot_count": self.snapshot_count,
            "alert_row_count": self.alert_row_count,
            "alert_count": self.alert_count,
            "summary_row_count": self.summary_row_count,
        }


def generate_live_monitor_v2_scoring_outputs(
    *,
    watchlist_path: Path = LIVE_WATCHLIST_OUTPUT,
    market_snapshots_path: Path = LIVE_MARKET_SNAPSHOTS_OUTPUT,
    wallet_tier_snapshots_path: Path = LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT,
    event_candidates_path: Path = LIVE_EVENT_CANDIDATES_OUTPUT,
    snapshots_path: Path = LIVE_SCORING_SNAPSHOTS_OUTPUT,
    rows_path: Path = LIVE_ALERT_ROWS_OUTPUT,
    summary_path: Path = LIVE_ALERT_SUMMARY_OUTPUT,
    validation_report_path: Path = LIVE_SCORING_VALIDATION_REPORT_OUTPUT,
    metadata_path: Path = LIVE_SCORING_METADATA_OUTPUT,
    baseline_observations: int = DIAGNOSTIC_BASELINE_OBSERVATIONS,
    min_baseline_observations: int = DIAGNOSTIC_MIN_BASELINE_OBSERVATIONS,
) -> LiveScoringResult:
    """Validate local live-style inputs, score them, and write artifacts."""

    inputs = load_validated_live_inputs(
        watchlist_path=watchlist_path,
        market_snapshots_path=market_snapshots_path,
        wallet_tier_snapshots_path=wallet_tier_snapshots_path,
        event_candidates_path=event_candidates_path,
        validation_report_path=validation_report_path,
    )
    snapshots = build_live_scoring_snapshots(
        inputs.watchlist,
        inputs.market_snapshots,
        inputs.wallet_tier_snapshots,
        inputs.event_candidates,
    )
    alert_rows = build_monitor_v2_alert_rows(
        snapshots,
        baseline_observations=baseline_observations,
        min_baseline_observations=min_baseline_observations,
    )
    alert_summary = summarize_monitor_v2_alerts(alert_rows)

    for path, frame in (
        (snapshots_path, snapshots),
        (rows_path, alert_rows),
        (summary_path, alert_summary),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)

    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(
            _build_metadata(
                inputs=inputs,
                snapshots=snapshots,
                alert_rows=alert_rows,
                alert_summary=alert_summary,
                watchlist_path=watchlist_path,
                market_snapshots_path=market_snapshots_path,
                wallet_tier_snapshots_path=wallet_tier_snapshots_path,
                event_candidates_path=event_candidates_path,
                validation_report_path=validation_report_path,
                baseline_observations=baseline_observations,
                min_baseline_observations=min_baseline_observations,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return LiveScoringResult(
        snapshots_path=snapshots_path,
        rows_path=rows_path,
        summary_path=summary_path,
        validation_report_path=validation_report_path,
        metadata_path=metadata_path,
        snapshot_count=len(snapshots),
        alert_row_count=len(alert_rows),
        alert_count=int((alert_rows["severity"] != "none").sum()),
        summary_row_count=len(alert_summary),
    )


def load_validated_live_inputs(
    *,
    watchlist_path: Path,
    market_snapshots_path: Path,
    wallet_tier_snapshots_path: Path,
    event_candidates_path: Path,
    validation_report_path: Path | None = None,
) -> LiveMonitorInputs:
    """Load, validate, and cross-check all local live-style input files."""

    validation_report = validate_live_input_files(
        watchlist_path=watchlist_path,
        market_snapshots_path=market_snapshots_path,
        wallet_tier_snapshots_path=wallet_tier_snapshots_path,
        event_candidates_path=event_candidates_path,
        report_output_path=validation_report_path,
    )
    watchlist = validate_live_market_watch_items(pd.read_csv(watchlist_path))
    market_snapshots = validate_live_market_snapshots(pd.read_csv(market_snapshots_path))
    wallet_tier_snapshots = validate_live_wallet_tier_snapshots(
        pd.read_csv(wallet_tier_snapshots_path)
    )
    event_candidates = validate_live_event_candidates(pd.read_csv(event_candidates_path))
    validate_live_batch_consistency(
        watchlist=watchlist,
        market_snapshots=market_snapshots,
        wallet_tier_snapshots=wallet_tier_snapshots,
        event_candidates=event_candidates,
    )
    return LiveMonitorInputs(
        watchlist=watchlist,
        market_snapshots=market_snapshots,
        wallet_tier_snapshots=wallet_tier_snapshots,
        event_candidates=event_candidates,
        validation_report=validation_report,
    )


def build_live_scoring_snapshots(
    watchlist: pd.DataFrame,
    market_snapshots: pd.DataFrame,
    wallet_tier_snapshots: pd.DataFrame,
    event_candidates: pd.DataFrame,
) -> pd.DataFrame:
    """Convert validated local live-style inputs to scoring snapshots."""

    validate_live_batch_consistency(
        watchlist=watchlist,
        market_snapshots=market_snapshots,
        wallet_tier_snapshots=wallet_tier_snapshots,
        event_candidates=event_candidates,
    )
    closed_market = _closed_rows(market_snapshots, "live market snapshots")
    closed_wallet = _closed_rows(wallet_tier_snapshots, "live wallet-tier snapshots")
    event_lookup = _event_lookup(event_candidates)
    rows: list[dict[str, object]] = []
    rows.extend(_market_metric_rows(closed_market, event_lookup))
    rows.extend(_wallet_metric_rows(closed_wallet, event_lookup))
    rows.extend(_concentration_metric_rows(closed_wallet, event_lookup))
    if not rows:
        raise ValueError("local live-style inputs produced no scoring snapshots")
    return (
        pd.DataFrame(rows, columns=SNAPSHOT_COLUMNS)
        .sort_values(["timestamp_utc", "market_id", "anomaly_family", "tier", "metric_name"])
        .reset_index(drop=True)
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--watchlist", type=Path, default=LIVE_WATCHLIST_OUTPUT)
    parser.add_argument("--market-snapshots", type=Path, default=LIVE_MARKET_SNAPSHOTS_OUTPUT)
    parser.add_argument("--wallet-tier-snapshots", type=Path, default=LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT)
    parser.add_argument("--event-candidates", type=Path, default=LIVE_EVENT_CANDIDATES_OUTPUT)
    parser.add_argument("--snapshots-output", type=Path, default=LIVE_SCORING_SNAPSHOTS_OUTPUT)
    parser.add_argument("--rows-output", type=Path, default=LIVE_ALERT_ROWS_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=LIVE_ALERT_SUMMARY_OUTPUT)
    parser.add_argument(
        "--validation-report-output",
        type=Path,
        default=LIVE_SCORING_VALIDATION_REPORT_OUTPUT,
    )
    parser.add_argument("--metadata-output", type=Path, default=LIVE_SCORING_METADATA_OUTPUT)
    parser.add_argument("--baseline-observations", type=int, default=DIAGNOSTIC_BASELINE_OBSERVATIONS)
    parser.add_argument(
        "--min-baseline-observations",
        type=int,
        default=DIAGNOSTIC_MIN_BASELINE_OBSERVATIONS,
    )
    args = parser.parse_args(argv)

    try:
        result = generate_live_monitor_v2_scoring_outputs(
            watchlist_path=args.watchlist,
            market_snapshots_path=args.market_snapshots,
            wallet_tier_snapshots_path=args.wallet_tier_snapshots,
            event_candidates_path=args.event_candidates,
            snapshots_path=args.snapshots_output,
            rows_path=args.rows_output,
            summary_path=args.summary_output,
            validation_report_path=args.validation_report_output,
            metadata_path=args.metadata_output,
            baseline_observations=args.baseline_observations,
            min_baseline_observations=args.min_baseline_observations,
        )
    except (FileNotFoundError, ValidationError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _closed_rows(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    closed = frame[frame["bucket_status"].astype(str).str.lower() == "closed"].copy()
    if closed.empty:
        raise ValueError(f"{name} contain no closed bucket rows for scoring")
    return closed


def _market_metric_rows(
    market_snapshots: pd.DataFrame,
    event_lookup: dict[str, list[dict[str, Any]]],
) -> list[dict[str, object]]:
    frame = market_snapshots.copy()
    frame["timestamp_utc"] = pd.to_datetime(
        frame["bucket_end_utc"],
        utc=True,
        errors="raise",
    )
    frame["market_value"] = frame["midpoint"].combine_first(frame["price"])
    frame["market_value"] = pd.to_numeric(frame["market_value"], errors="raise")
    rows: list[dict[str, object]] = []
    for _, group in frame.groupby(["market_id", "token_id"], sort=True):
        ordered = group.sort_values("timestamp_utc").copy()
        ordered["absolute_change"] = ordered["market_value"].diff().abs()
        for item in ordered[ordered["absolute_change"].notna()].to_dict(orient="records"):
            rows.append(
                {
                    "timestamp_utc": _timestamp(item["timestamp_utc"]),
                    "market_id": item["market_id"],
                    "tier": "market",
                    "anomaly_family": "market_move",
                    "metric_name": "absolute_midpoint_change",
                    "observed_value": float(item["absolute_change"]),
                    **_event_context(item["timestamp_utc"], item["market_id"], event_lookup),
                    "evidence_ref": "live_market_snapshots:price_midpoint",
                    "limitation": (
                        "diagnostic local live-style fixture; no live source or "
                        "orderbook claim"
                    ),
                    "review_status": "candidate",
                }
            )
        rows.extend(
            _optional_market_rows(
                ordered,
                "spread",
                "spread_liquidity",
                "spread",
                event_lookup,
            )
        )
        rows.extend(
            _optional_market_rows(
                ordered,
                "volume",
                "volume_activity",
                "volume",
                event_lookup,
            )
        )
    return rows


def _optional_market_rows(
    ordered: pd.DataFrame,
    value_column: str,
    family: str,
    metric_name: str,
    event_lookup: dict[str, list[dict[str, Any]]],
) -> list[dict[str, object]]:
    values = pd.to_numeric(ordered[value_column], errors="coerce")
    if values.notna().sum() == 0:
        return []
    rows: list[dict[str, object]] = []
    for item, observed in zip(ordered.to_dict(orient="records"), values):
        if pd.isna(observed):
            continue
        rows.append(
            {
                "timestamp_utc": _timestamp(item["timestamp_utc"]),
                "market_id": item["market_id"],
                "tier": "market",
                "anomaly_family": family,
                "metric_name": metric_name,
                "observed_value": float(observed),
                **_event_context(item["timestamp_utc"], item["market_id"], event_lookup),
                "evidence_ref": f"live_market_snapshots:{value_column}",
                "limitation": "diagnostic local live-style fixture; source availability varies",
                "review_status": "candidate",
            }
        )
    return rows


def _wallet_metric_rows(
    wallet_tier_snapshots: pd.DataFrame,
    event_lookup: dict[str, list[dict[str, Any]]],
) -> list[dict[str, object]]:
    frame = wallet_tier_snapshots.copy()
    frame["timestamp_utc"] = pd.to_datetime(
        frame["bucket_end_utc"],
        utc=True,
        errors="raise",
    )
    rows: list[dict[str, object]] = []
    for item in frame.to_dict(orient="records"):
        context = _event_context(item["timestamp_utc"], item["market_id"], event_lookup)
        total_amount = float(item["total_observed_amount_usd"])
        rows.extend(
            [
                {
                    "timestamp_utc": _timestamp(item["timestamp_utc"]),
                    "market_id": item["market_id"],
                    "tier": item["tier"],
                    "anomaly_family": "wallet_tier_activity",
                    "metric_name": "log1p_total_observed_amount_usd",
                    "observed_value": float(np.log1p(total_amount)),
                    **context,
                    "evidence_ref": "live_wallet_tier_snapshots:total_observed_amount_usd",
                    "limitation": (
                        "aggregate diagnostic fixture wallet-tier replay; no "
                        "wallet addresses or wallet-performance claim"
                    ),
                    "review_status": "candidate",
                },
                {
                    "timestamp_utc": _timestamp(item["timestamp_utc"]),
                    "market_id": item["market_id"],
                    "tier": item["tier"],
                    "anomaly_family": "active_wallet_activity",
                    "metric_name": "active_wallets",
                    "observed_value": float(item["active_wallets"]),
                    **context,
                    "evidence_ref": "live_wallet_tier_snapshots:active_wallets",
                    "limitation": (
                        "aggregate diagnostic fixture active-wallet tier count; "
                        "no wallet addresses"
                    ),
                    "review_status": "candidate",
                },
            ]
        )
    return rows


def _concentration_metric_rows(
    wallet_tier_snapshots: pd.DataFrame,
    event_lookup: dict[str, list[dict[str, Any]]],
) -> list[dict[str, object]]:
    frame = wallet_tier_snapshots.copy()
    frame["timestamp_utc"] = pd.to_datetime(
        frame["bucket_end_utc"],
        utc=True,
        errors="raise",
    )
    concentration = (
        frame.sort_values(["timestamp_utc", "tier"])
        .groupby(["timestamp_utc", "market_id"], as_index=False)
        .agg({"top_tier_share": "first", "hhi_concentration": "first"})
    )
    rows: list[dict[str, object]] = []
    for item in concentration.to_dict(orient="records"):
        context = _event_context(item["timestamp_utc"], item["market_id"], event_lookup)
        for column in ("top_tier_share", "hhi_concentration"):
            if pd.isna(item[column]):
                continue
            rows.append(
                {
                    "timestamp_utc": _timestamp(item["timestamp_utc"]),
                    "market_id": item["market_id"],
                    "tier": "all_tiers",
                    "anomaly_family": "concentration",
                    "metric_name": column,
                    "observed_value": float(item[column]),
                    **context,
                    "evidence_ref": f"live_wallet_tier_snapshots:{column}",
                    "limitation": (
                        "aggregate diagnostic fixture concentration replay; no "
                        "wallet-performance claim"
                    ),
                    "review_status": "candidate",
                }
            )
    return rows


def _event_lookup(event_candidates: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    reviewed = event_candidates[
        event_candidates["review_status"].isin(EVENT_ACCEPTED_STATUSES)
    ].copy()
    lookup: dict[str, list[dict[str, Any]]] = {}
    for row in reviewed.to_dict(orient="records"):
        published_at = pd.to_datetime(row["published_at_utc"], utc=True, errors="raise")
        for market_id in _parse_list_field(str(row["related_market_ids"])):
            lookup.setdefault(market_id, []).append(
                {
                    "published_at": published_at,
                    "event_candidate_id": str(row["event_candidate_id"]),
                    "event_review_status": str(row["review_status"]),
                }
            )
    for events in lookup.values():
        events.sort(key=lambda item: (item["published_at"], item["event_candidate_id"]))
    return lookup


def _event_context(
    timestamp: Any,
    market_id: str,
    event_lookup: dict[str, list[dict[str, Any]]],
) -> dict[str, str]:
    timestamp_utc = pd.Timestamp(timestamp).tz_convert("UTC")
    candidates = [
        event
        for event in event_lookup.get(str(market_id), [])
        if event["published_at"] <= timestamp_utc
    ]
    if not candidates:
        return {"event_candidate_id": "", "event_review_status": ""}
    latest = candidates[-1]
    return {
        "event_candidate_id": latest["event_candidate_id"],
        "event_review_status": latest["event_review_status"],
    }


def _parse_list_field(value: str) -> list[str]:
    candidate = value.strip()
    if not candidate:
        return []
    if candidate.startswith("["):
        parsed = json.loads(candidate)
        if not isinstance(parsed, list):
            raise ValueError("list field JSON must decode to a list")
        return [str(item).strip() for item in parsed if str(item).strip()]
    return [item.strip() for item in candidate.replace(";", ",").split(",") if item.strip()]


def _timestamp(value: Any) -> str:
    return pd.Timestamp(value).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_metadata(
    *,
    inputs: LiveMonitorInputs,
    snapshots: pd.DataFrame,
    alert_rows: pd.DataFrame,
    alert_summary: pd.DataFrame,
    watchlist_path: Path,
    market_snapshots_path: Path,
    wallet_tier_snapshots_path: Path,
    event_candidates_path: Path,
    validation_report_path: Path,
    baseline_observations: int,
    min_baseline_observations: int,
) -> dict[str, Any]:
    status_counts = _value_counts(alert_rows, "status")
    severity_counts = _value_counts(alert_rows, "severity")
    max_baseline_observations = _max_numeric(alert_rows, "baseline_observations")
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "monitor_v2_live_input_scoring",
            "input_mode": "validated_live_style_files",
            "baseline_observations": baseline_observations,
            "min_baseline_observations": min_baseline_observations,
            "diagnostic_file_baseline_only": True,
            "production_like_min_baseline_observations": 20,
            "alert_rule": "Rule C combined-family confirmation from monitor_v2_snapshot",
            "validates_inputs_before_scoring": True,
            "scores_closed_buckets_only": True,
            "event_context_rule": "event candidate may annotate only buckets at or after published_at_utc",
            "uses_completed_prior_observations": True,
            "baseline_readiness": _baseline_readiness(
                status_counts=status_counts,
                max_baseline_observations=max_baseline_observations,
                min_baseline_observations=min_baseline_observations,
            ),
            "max_baseline_observations_available": max_baseline_observations,
        },
        "inputs": {
            "watchlist_path": str(watchlist_path),
            "market_snapshots_path": str(market_snapshots_path),
            "wallet_tier_snapshots_path": str(wallet_tier_snapshots_path),
            "event_candidates_path": str(event_candidates_path),
            "validation_report_path": str(validation_report_path),
            "watchlist_row_count": int(len(inputs.watchlist)),
            "market_snapshot_row_count": int(len(inputs.market_snapshots)),
            "wallet_tier_snapshot_row_count": int(len(inputs.wallet_tier_snapshots)),
            "event_candidate_row_count": int(len(inputs.event_candidates)),
            "validation_status": inputs.validation_report["status"],
        },
        "outputs": {
            "snapshot_count": int(len(snapshots)),
            "alert_row_count": int(len(alert_rows)),
            "alert_count": int((alert_rows["severity"] != "none").sum()),
            "summary_row_count": int(len(alert_summary)),
            "snapshot_columns": list(SNAPSHOT_COLUMNS),
            "alert_row_columns": list(ALERT_ROW_COLUMNS),
            "summary_columns": list(ALERT_SUMMARY_COLUMNS),
            "severity_counts": severity_counts,
            "status_counts": status_counts,
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "limitations": {
            "file_based_scoring_only": True,
            "diagnostic_scoring_only": True,
            "too_few_buckets_for_production_alerts": True,
            "input_files_may_be_mock_or_read_only_collector": True,
            "uses_aggregate_wallet_tier_activity": True,
            "uses_observed_buy_side_activity_extract": True,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "does_not_use_rcp": True,
            "does_not_send_orders": True,
            "no_profitability_or_private_information_claim": True,
        },
    }


def _value_counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    counts = frame[column].value_counts().sort_index()
    return {str(key): int(value) for key, value in counts.items()}


def _max_numeric(frame: pd.DataFrame, column: str) -> int:
    values = pd.to_numeric(frame[column], errors="coerce").dropna()
    if values.empty:
        return 0
    return int(values.max())


def _baseline_readiness(
    *,
    status_counts: dict[str, int],
    max_baseline_observations: int,
    min_baseline_observations: int,
) -> str:
    if not status_counts:
        return "no_scoring_rows"
    if set(status_counts) == {"insufficient_baseline"}:
        return "insufficient_baseline"
    if max_baseline_observations < min_baseline_observations:
        return "insufficient_baseline"
    if status_counts.get("ok", 0) > 0:
        return "diagnostic_scores_available"
    return "baseline_available_zero_mad_or_non_alerting"


if __name__ == "__main__":
    raise SystemExit(main())
