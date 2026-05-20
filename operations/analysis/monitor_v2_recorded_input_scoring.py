"""Score validated recorded monitor v2 input files.

This module is the deterministic bridge between reviewed recorded monitor v2
input files and alert outputs. It validates every recorded input before
scoring, writes file-based artifacts only, and does not call live APIs,
WebSockets, databases, LLMs, agents, MCP tools, ML systems, or order execution.
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

from operations.analysis.monitor_v2_event_proximity_sensitivity import (
    SENSITIVITY_SUMMARY_COLUMNS,
    build_event_proximity_sensitivity,
)
from operations.analysis.monitor_v2_input_validation import (
    validate_event_candidates,
    validate_market_snapshots,
    validate_market_watch_items,
    validate_recorded_input_files,
    validate_wallet_tier_snapshots,
)
from operations.analysis.monitor_v2_recorded_input_adapter import (
    EVENT_CANDIDATES_OUTPUT,
    MARKET_SNAPSHOTS_OUTPUT,
    WALLET_TIER_SNAPSHOTS_OUTPUT,
    WATCHLIST_OUTPUT,
)
from operations.analysis.monitor_v2_snapshot import (
    ALERT_ROW_COLUMNS,
    ALERT_SUMMARY_COLUMNS,
    DEFAULT_BASELINE_OBSERVATIONS,
    DEFAULT_MIN_BASELINE_OBSERVATIONS,
    EVENT_ACCEPTED_STATUSES,
    SNAPSHOT_COLUMNS,
    build_monitor_v2_alert_rows,
    summarize_monitor_v2_alerts,
)
from operations.analysis.run_h2_event_windows import RESULTS_DIR


SCORING_SNAPSHOTS_OUTPUT = RESULTS_DIR / "monitor_v2_recorded_scoring_snapshots.csv"
ALERT_ROWS_OUTPUT = RESULTS_DIR / "monitor_v2_recorded_alert_rows.csv"
ALERT_SUMMARY_OUTPUT = RESULTS_DIR / "monitor_v2_recorded_alert_summary.csv"
CONTEXT_ROWS_OUTPUT = RESULTS_DIR / "monitor_v2_recorded_context_rows.csv"
VALIDATION_REPORT_OUTPUT = RESULTS_DIR / "monitor_v2_recorded_scoring_validation_report.json"
METADATA_OUTPUT = RESULTS_DIR / "monitor_v2_recorded_scoring_metadata.json"


@dataclass(frozen=True)
class RecordedMonitorInputs:
    """Validated recorded monitor v2 input frames."""

    watchlist: pd.DataFrame
    market_snapshots: pd.DataFrame
    wallet_tier_snapshots: pd.DataFrame
    event_candidates: pd.DataFrame
    validation_report: dict[str, Any]


@dataclass(frozen=True)
class RecordedScoringResult:
    """Summary of generated recorded-input scoring artifacts."""

    snapshots_path: Path
    rows_path: Path
    summary_path: Path
    context_rows_path: Path
    validation_report_path: Path
    metadata_path: Path
    snapshot_count: int
    alert_row_count: int
    alert_count: int
    summary_row_count: int
    context_row_count: int

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "snapshots_path": str(self.snapshots_path),
            "rows_path": str(self.rows_path),
            "summary_path": str(self.summary_path),
            "context_rows_path": str(self.context_rows_path),
            "validation_report_path": str(self.validation_report_path),
            "metadata_path": str(self.metadata_path),
            "snapshot_count": self.snapshot_count,
            "alert_row_count": self.alert_row_count,
            "alert_count": self.alert_count,
            "summary_row_count": self.summary_row_count,
            "context_row_count": self.context_row_count,
        }


def generate_recorded_monitor_v2_scoring_outputs(
    *,
    watchlist_path: Path = WATCHLIST_OUTPUT,
    market_snapshots_path: Path = MARKET_SNAPSHOTS_OUTPUT,
    wallet_tier_snapshots_path: Path = WALLET_TIER_SNAPSHOTS_OUTPUT,
    event_candidates_path: Path = EVENT_CANDIDATES_OUTPUT,
    snapshots_path: Path = SCORING_SNAPSHOTS_OUTPUT,
    rows_path: Path = ALERT_ROWS_OUTPUT,
    summary_path: Path = ALERT_SUMMARY_OUTPUT,
    context_rows_path: Path = CONTEXT_ROWS_OUTPUT,
    validation_report_path: Path = VALIDATION_REPORT_OUTPUT,
    metadata_path: Path = METADATA_OUTPUT,
    baseline_observations: int = DEFAULT_BASELINE_OBSERVATIONS,
    min_baseline_observations: int = DEFAULT_MIN_BASELINE_OBSERVATIONS,
    days_before: int = 1,
    days_after: int = 1,
) -> RecordedScoringResult:
    """Validate recorded inputs, score alerts, and write deterministic outputs."""

    inputs = load_validated_recorded_inputs(
        watchlist_path=watchlist_path,
        market_snapshots_path=market_snapshots_path,
        wallet_tier_snapshots_path=wallet_tier_snapshots_path,
        event_candidates_path=event_candidates_path,
        validation_report_path=validation_report_path,
    )
    snapshots = build_recorded_scoring_snapshots(
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
    event_frame = event_candidates_to_event_frame(inputs.event_candidates)
    _, context_rows = build_event_proximity_sensitivity(
        alert_rows,
        event_frame,
        days_before=days_before,
        days_after=days_after,
    )

    for path, frame in (
        (snapshots_path, snapshots),
        (rows_path, alert_rows),
        (summary_path, alert_summary),
        (context_rows_path, context_rows),
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
                context_rows=context_rows,
                watchlist_path=watchlist_path,
                market_snapshots_path=market_snapshots_path,
                wallet_tier_snapshots_path=wallet_tier_snapshots_path,
                event_candidates_path=event_candidates_path,
                validation_report_path=validation_report_path,
                baseline_observations=baseline_observations,
                min_baseline_observations=min_baseline_observations,
                days_before=days_before,
                days_after=days_after,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return RecordedScoringResult(
        snapshots_path=snapshots_path,
        rows_path=rows_path,
        summary_path=summary_path,
        context_rows_path=context_rows_path,
        validation_report_path=validation_report_path,
        metadata_path=metadata_path,
        snapshot_count=len(snapshots),
        alert_row_count=len(alert_rows),
        alert_count=int((alert_rows["severity"] != "none").sum()),
        summary_row_count=len(alert_summary),
        context_row_count=len(context_rows),
    )


def load_validated_recorded_inputs(
    *,
    watchlist_path: Path,
    market_snapshots_path: Path,
    wallet_tier_snapshots_path: Path,
    event_candidates_path: Path,
    validation_report_path: Path | None = None,
) -> RecordedMonitorInputs:
    """Load and validate all recorded monitor v2 input files."""

    validation_report = validate_recorded_input_files(
        watchlist_path=watchlist_path,
        market_snapshots_path=market_snapshots_path,
        wallet_tier_snapshots_path=wallet_tier_snapshots_path,
        event_candidates_path=event_candidates_path,
        report_output_path=validation_report_path,
    )
    watchlist = validate_market_watch_items(pd.read_csv(watchlist_path))
    market_snapshots = validate_market_snapshots(pd.read_csv(market_snapshots_path))
    wallet_tier_snapshots = validate_wallet_tier_snapshots(
        pd.read_csv(wallet_tier_snapshots_path)
    )
    event_candidates = validate_event_candidates(pd.read_csv(event_candidates_path))
    _validate_market_consistency(
        watchlist=watchlist,
        market_snapshots=market_snapshots,
        wallet_tier_snapshots=wallet_tier_snapshots,
        event_candidates=event_candidates,
    )
    return RecordedMonitorInputs(
        watchlist=watchlist,
        market_snapshots=market_snapshots,
        wallet_tier_snapshots=wallet_tier_snapshots,
        event_candidates=event_candidates,
        validation_report=validation_report,
    )


def build_recorded_scoring_snapshots(
    watchlist: pd.DataFrame,
    market_snapshots: pd.DataFrame,
    wallet_tier_snapshots: pd.DataFrame,
    event_candidates: pd.DataFrame,
) -> pd.DataFrame:
    """Convert validated recorded inputs to long monitor v2 scoring snapshots."""

    _validate_market_consistency(
        watchlist=watchlist,
        market_snapshots=market_snapshots,
        wallet_tier_snapshots=wallet_tier_snapshots,
        event_candidates=event_candidates,
    )
    event_lookup = _event_context_lookup(event_candidates)
    rows: list[dict[str, object]] = []
    rows.extend(_market_metric_rows(market_snapshots, event_lookup))
    rows.extend(_wallet_metric_rows(wallet_tier_snapshots, event_lookup))
    rows.extend(_concentration_metric_rows(wallet_tier_snapshots, event_lookup))
    if not rows:
        raise ValueError("recorded inputs produced no scoring snapshots")
    return pd.DataFrame(rows, columns=SNAPSHOT_COLUMNS).sort_values(
        ["timestamp_utc", "market_id", "anomaly_family", "tier", "metric_name"]
    ).reset_index(drop=True)


def event_candidates_to_event_frame(event_candidates: pd.DataFrame) -> pd.DataFrame:
    """Return curated-event shaped rows from reviewed event candidates."""

    frame = event_candidates[
        event_candidates["review_status"].isin(EVENT_ACCEPTED_STATUSES)
    ].copy()
    if frame.empty:
        raise ValueError("No accepted or market-mapped event candidates available")
    output = pd.DataFrame(
        {
            "event_id": frame["event_candidate_id"].astype(str),
            "event_date": pd.to_datetime(
                frame["published_at_utc"],
                utc=True,
                errors="raise",
            ).dt.date.astype(str),
            "title": frame["title"].astype(str),
            "event_type": frame["event_type"].astype(str),
            "source_url": frame["source_url"].astype(str),
        }
    )
    return output.sort_values(["event_date", "event_id"]).reset_index(drop=True)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--watchlist", type=Path, default=WATCHLIST_OUTPUT)
    parser.add_argument("--market-snapshots", type=Path, default=MARKET_SNAPSHOTS_OUTPUT)
    parser.add_argument("--wallet-tier-snapshots", type=Path, default=WALLET_TIER_SNAPSHOTS_OUTPUT)
    parser.add_argument("--event-candidates", type=Path, default=EVENT_CANDIDATES_OUTPUT)
    parser.add_argument("--snapshots-output", type=Path, default=SCORING_SNAPSHOTS_OUTPUT)
    parser.add_argument("--rows-output", type=Path, default=ALERT_ROWS_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=ALERT_SUMMARY_OUTPUT)
    parser.add_argument("--context-rows-output", type=Path, default=CONTEXT_ROWS_OUTPUT)
    parser.add_argument("--validation-report-output", type=Path, default=VALIDATION_REPORT_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    parser.add_argument("--baseline-observations", type=int, default=DEFAULT_BASELINE_OBSERVATIONS)
    parser.add_argument("--min-baseline-observations", type=int, default=DEFAULT_MIN_BASELINE_OBSERVATIONS)
    parser.add_argument("--days-before", type=int, default=1)
    parser.add_argument("--days-after", type=int, default=1)
    args = parser.parse_args(argv)

    try:
        result = generate_recorded_monitor_v2_scoring_outputs(
            watchlist_path=args.watchlist,
            market_snapshots_path=args.market_snapshots,
            wallet_tier_snapshots_path=args.wallet_tier_snapshots,
            event_candidates_path=args.event_candidates,
            snapshots_path=args.snapshots_output,
            rows_path=args.rows_output,
            summary_path=args.summary_output,
            context_rows_path=args.context_rows_output,
            validation_report_path=args.validation_report_output,
            metadata_path=args.metadata_output,
            baseline_observations=args.baseline_observations,
            min_baseline_observations=args.min_baseline_observations,
            days_before=args.days_before,
            days_after=args.days_after,
        )
    except (FileNotFoundError, ValidationError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _market_metric_rows(
    market_snapshots: pd.DataFrame,
    event_lookup: dict[tuple[str, str], dict[str, str]],
) -> list[dict[str, object]]:
    frame = market_snapshots.copy()
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="raise")
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
                    "evidence_ref": "recorded_market_snapshots:price_midpoint",
                    "limitation": "recorded daily market snapshot replay; no intraday orderbook claim",
                    "review_status": "candidate",
                }
            )
        rows.extend(_optional_market_rows(ordered, "spread", "spread_liquidity", "spread"))
        rows.extend(_optional_market_rows(ordered, "volume", "volume_activity", "volume"))
    return rows


def _optional_market_rows(
    ordered: pd.DataFrame,
    value_column: str,
    family: str,
    metric_name: str,
) -> list[dict[str, object]]:
    if value_column not in ordered.columns:
        return []
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
                "event_candidate_id": "",
                "event_review_status": "",
                "evidence_ref": f"recorded_market_snapshots:{value_column}",
                "limitation": "recorded market snapshot replay; source availability varies",
                "review_status": "candidate",
            }
        )
    return rows


def _wallet_metric_rows(
    wallet_tier_snapshots: pd.DataFrame,
    event_lookup: dict[tuple[str, str], dict[str, str]],
) -> list[dict[str, object]]:
    frame = wallet_tier_snapshots.copy()
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="raise")
    rows: list[dict[str, object]] = []
    for item in frame.to_dict(orient="records"):
        total_amount = float(item["total_observed_amount_usd"])
        context = _event_context(item["timestamp_utc"], item["market_id"], event_lookup)
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
                    "evidence_ref": "recorded_wallet_tier_snapshots:total_observed_amount_usd",
                    "limitation": "aggregate BUY-side wallet-tier replay; no wallet addresses",
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
                    "evidence_ref": "recorded_wallet_tier_snapshots:active_wallets",
                    "limitation": "aggregate active-wallet tier count replay; no wallet addresses",
                    "review_status": "candidate",
                },
            ]
        )
    return rows


def _concentration_metric_rows(
    wallet_tier_snapshots: pd.DataFrame,
    event_lookup: dict[tuple[str, str], dict[str, str]],
) -> list[dict[str, object]]:
    frame = wallet_tier_snapshots.copy()
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="raise")
    concentration = (
        frame.sort_values(["timestamp_utc", "tier"])
        .groupby(["timestamp_utc", "market_id"], as_index=False)
        .agg({"top_tier_share": "first", "hhi_concentration": "first"})
    )
    rows: list[dict[str, object]] = []
    metric_specs = (
        ("top_tier_share", "top_tier_share"),
        ("hhi_concentration", "hhi_concentration"),
    )
    for item in concentration.to_dict(orient="records"):
        context = _event_context(item["timestamp_utc"], item["market_id"], event_lookup)
        for column, metric_name in metric_specs:
            if pd.isna(item[column]):
                continue
            rows.append(
                {
                    "timestamp_utc": _timestamp(item["timestamp_utc"]),
                    "market_id": item["market_id"],
                    "tier": "all_tiers",
                    "anomaly_family": "concentration",
                    "metric_name": metric_name,
                    "observed_value": float(item[column]),
                    **context,
                    "evidence_ref": f"recorded_wallet_tier_snapshots:{column}",
                    "limitation": "aggregate concentration replay; no wallet performance claim",
                    "review_status": "candidate",
                }
            )
    return rows


def _event_context_lookup(event_candidates: pd.DataFrame) -> dict[tuple[str, str], dict[str, str]]:
    lookup: dict[tuple[str, str], dict[str, str]] = {}
    reviewed = event_candidates[event_candidates["review_status"].isin(EVENT_ACCEPTED_STATUSES)]
    for row in reviewed.to_dict(orient="records"):
        event_date = pd.to_datetime(row["published_at_utc"], utc=True, errors="raise").date()
        for market_id in _parse_list_field(str(row["related_market_ids"])):
            lookup[(event_date.isoformat(), market_id)] = {
                "event_candidate_id": str(row["event_candidate_id"]),
                "event_review_status": str(row["review_status"]),
            }
    return lookup


def _event_context(
    timestamp: Any,
    market_id: str,
    event_lookup: dict[tuple[str, str], dict[str, str]],
) -> dict[str, str]:
    event_date = pd.Timestamp(timestamp).date().isoformat()
    return event_lookup.get(
        (event_date, market_id),
        {
            "event_candidate_id": "",
            "event_review_status": "",
        },
    )


def _validate_market_consistency(
    *,
    watchlist: pd.DataFrame,
    market_snapshots: pd.DataFrame,
    wallet_tier_snapshots: pd.DataFrame,
    event_candidates: pd.DataFrame,
) -> None:
    watch_markets = set(watchlist["market_id"].astype(str))
    if not watch_markets:
        raise ValueError("watchlist contains no market_id values")
    for name, frame in (
        ("market snapshots", market_snapshots),
        ("wallet-tier snapshots", wallet_tier_snapshots),
    ):
        unknown = sorted(set(frame["market_id"].astype(str)) - watch_markets)
        if unknown:
            raise ValueError(f"{name} contain market_id values outside watchlist: {unknown}")
    for row in event_candidates.to_dict(orient="records"):
        related = set(_parse_list_field(str(row["related_market_ids"])))
        if row["review_status"] in EVENT_ACCEPTED_STATUSES and not related.intersection(watch_markets):
            raise ValueError(
                "accepted event candidates must map to at least one watchlist market"
            )


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
    inputs: RecordedMonitorInputs,
    snapshots: pd.DataFrame,
    alert_rows: pd.DataFrame,
    alert_summary: pd.DataFrame,
    context_rows: pd.DataFrame,
    watchlist_path: Path,
    market_snapshots_path: Path,
    wallet_tier_snapshots_path: Path,
    event_candidates_path: Path,
    validation_report_path: Path,
    baseline_observations: int,
    min_baseline_observations: int,
    days_before: int,
    days_after: int,
) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "monitor_v2_recorded_input_scoring",
            "input_mode": "validated_recorded_input_files",
            "baseline_observations": baseline_observations,
            "min_baseline_observations": min_baseline_observations,
            "alert_rule": "Rule C combined-family confirmation from monitor_v2_snapshot",
            "event_context_window": f"[-{days_before}d,+{days_after}d]",
            "validates_inputs_before_scoring": True,
            "uses_completed_prior_observations": True,
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
            "context_row_count": int(len(context_rows)),
            "snapshot_columns": list(SNAPSHOT_COLUMNS),
            "alert_row_columns": list(ALERT_ROW_COLUMNS),
            "summary_columns": list(ALERT_SUMMARY_COLUMNS),
            "context_row_columns": list(SENSITIVITY_SUMMARY_COLUMNS),
            "severity_counts": _value_counts(alert_rows, "severity"),
            "context_label_counts": _value_counts(context_rows, "suggested_context_label"),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "limitations": {
            "recorded_files_only": True,
            "daily_replay_only": True,
            "uses_existing_curated_events": True,
            "uses_aggregate_wallet_tier_activity": True,
            "uses_observed_buy_side_activity_extract": True,
            "no_live_websocket_or_api_collection": True,
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


if __name__ == "__main__":
    raise SystemExit(main())
