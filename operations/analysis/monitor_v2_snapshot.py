"""Generate deterministic monitor v2 alerts from recorded or mocked snapshots.

This module is the first prototype for the near-real-time Polymarket
politics/geo anomaly monitor contract. It uses in-memory or CSV snapshot rows,
writes file-based artifacts only, and does not call external APIs, databases,
LLMs, agents, MCP tools, or order-execution paths.
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

from operations.analysis.run_h2_event_windows import RESULTS_DIR


DEFAULT_BASELINE_OBSERVATIONS = 30
DEFAULT_MIN_BASELINE_OBSERVATIONS = 20
ROBUST_SCALE_FACTOR = 1.4826

SNAPSHOT_COLUMNS: tuple[str, ...] = (
    "timestamp_utc",
    "market_id",
    "tier",
    "anomaly_family",
    "metric_name",
    "observed_value",
    "event_candidate_id",
    "event_review_status",
    "evidence_ref",
    "limitation",
    "review_status",
)
ALERT_ROW_COLUMNS: tuple[str, ...] = (
    "timestamp_utc",
    "market_id",
    "tier",
    "anomaly_family",
    "metric_name",
    "observed_value",
    "baseline_window",
    "baseline_observations",
    "rolling_median",
    "rolling_mad",
    "robust_z",
    "rolling_percentile_rank",
    "severity",
    "status",
    "event_candidate_id",
    "event_review_status",
    "evidence_refs",
    "limitation",
    "review_status",
    "claim_scope",
)
ALERT_SUMMARY_COLUMNS: tuple[str, ...] = (
    "market_id",
    "tier",
    "anomaly_family",
    "metric_name",
    "row_count",
    "alert_count",
    "max_severity",
    "max_robust_z",
    "max_percentile_rank",
    "first_alert_at",
    "latest_alert_at",
    "limitation",
    "claim_scope",
)

ALERT_ROWS_OUTPUT = RESULTS_DIR / "monitor_v2_alert_rows.csv"
ALERT_SUMMARY_OUTPUT = RESULTS_DIR / "monitor_v2_alert_summary.csv"
METADATA_OUTPUT = RESULTS_DIR / "monitor_v2_metadata.json"

SEVERITY_RANK = {"none": 0, "info": 1, "watch": 2, "high": 3, "critical": 4}
WATCH_OR_HIGH = {"watch", "high", "critical"}
EVENT_ACCEPTED_STATUSES = {"accepted", "market_mapped"}
WALLET_OR_CONCENTRATION_FAMILIES = {
    "wallet_tier_activity",
    "active_wallet_activity",
    "concentration",
    "wallet_market_cluster",
}


@dataclass(frozen=True)
class MonitorV2SnapshotResult:
    """Summary of generated monitor v2 snapshot artifacts."""

    rows_path: Path
    summary_path: Path
    metadata_path: Path
    row_count: int
    alert_count: int
    summary_row_count: int

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "rows_path": str(self.rows_path),
            "summary_path": str(self.summary_path),
            "metadata_path": str(self.metadata_path),
            "row_count": self.row_count,
            "alert_count": self.alert_count,
            "summary_row_count": self.summary_row_count,
        }


def build_monitor_v2_alert_rows(
    snapshots: pd.DataFrame,
    *,
    baseline_observations: int = DEFAULT_BASELINE_OBSERVATIONS,
    min_baseline_observations: int = DEFAULT_MIN_BASELINE_OBSERVATIONS,
) -> pd.DataFrame:
    """Return row-level monitor diagnostics and alert severities."""

    if baseline_observations < 1:
        raise ValueError("baseline_observations must be >= 1")
    if min_baseline_observations < 1:
        raise ValueError("min_baseline_observations must be >= 1")
    if min_baseline_observations > baseline_observations:
        raise ValueError("min_baseline_observations must be <= baseline_observations")

    frame = validate_snapshot_frame(snapshots)
    rows: list[dict[str, object]] = []
    group_columns = ["market_id", "tier", "anomaly_family", "metric_name"]
    for _, group in frame.groupby(group_columns, sort=True, dropna=False):
        ordered = group.sort_values("timestamp_utc").reset_index(drop=True)
        prior_values: list[float] = []
        for snapshot in ordered.to_dict(orient="records"):
            baseline = prior_values[-baseline_observations:]
            score = _score_value(
                float(snapshot["observed_value"]),
                baseline,
                min_baseline_observations=min_baseline_observations,
            )
            rows.append(
                {
                    "timestamp_utc": snapshot["timestamp_utc"].isoformat().replace("+00:00", "Z"),
                    "market_id": snapshot["market_id"],
                    "tier": snapshot["tier"],
                    "anomaly_family": snapshot["anomaly_family"],
                    "metric_name": snapshot["metric_name"],
                    "observed_value": float(snapshot["observed_value"]),
                    "baseline_window": f"last_{baseline_observations}_completed_observations",
                    **score,
                    "event_candidate_id": snapshot["event_candidate_id"],
                    "event_review_status": snapshot["event_review_status"],
                    "evidence_refs": snapshot["evidence_ref"],
                    "limitation": snapshot["limitation"],
                    "review_status": snapshot["review_status"],
                    "claim_scope": "descriptive_monitor_alert_only",
                }
            )
            prior_values.append(float(snapshot["observed_value"]))

    alert_rows = pd.DataFrame(rows, columns=ALERT_ROW_COLUMNS)
    return _apply_cluster_severity(alert_rows)


def summarize_monitor_v2_alerts(alert_rows: pd.DataFrame) -> pd.DataFrame:
    """Return compact alert summaries by market and metric."""

    _require_columns(alert_rows, ALERT_ROW_COLUMNS, "monitor v2 alert rows")
    if alert_rows.empty:
        return pd.DataFrame(columns=ALERT_SUMMARY_COLUMNS)

    summaries: list[dict[str, object]] = []
    group_columns = ("market_id", "tier", "anomaly_family", "metric_name", "limitation")
    for keys, group in alert_rows.groupby(list(group_columns), sort=True, dropna=False):
        values = dict(zip(group_columns, keys))
        alert_group = group[group["severity"] != "none"]
        summaries.append(
            {
                **values,
                "row_count": int(len(group)),
                "alert_count": int(len(alert_group)),
                "max_severity": _max_severity(group["severity"]),
                "max_robust_z": _safe_max(pd.to_numeric(group["robust_z"], errors="coerce")),
                "max_percentile_rank": _safe_max(
                    pd.to_numeric(group["rolling_percentile_rank"], errors="coerce")
                ),
                "first_alert_at": "" if alert_group.empty else str(alert_group["timestamp_utc"].min()),
                "latest_alert_at": "" if alert_group.empty else str(alert_group["timestamp_utc"].max()),
                "claim_scope": "descriptive_monitor_alert_summary_only",
            }
        )
    return pd.DataFrame(summaries, columns=ALERT_SUMMARY_COLUMNS).sort_values(
        ["market_id", "anomaly_family", "tier", "metric_name"]
    ).reset_index(drop=True)


def generate_monitor_v2_snapshot_outputs(
    *,
    snapshots_path: Path | None = None,
    rows_path: Path = ALERT_ROWS_OUTPUT,
    summary_path: Path = ALERT_SUMMARY_OUTPUT,
    metadata_path: Path = METADATA_OUTPUT,
    baseline_observations: int = DEFAULT_BASELINE_OBSERVATIONS,
    min_baseline_observations: int = DEFAULT_MIN_BASELINE_OBSERVATIONS,
) -> MonitorV2SnapshotResult:
    """Generate deterministic monitor v2 snapshot CSV and metadata artifacts."""

    snapshots = (
        load_snapshot_frame(snapshots_path)
        if snapshots_path is not None
        else build_mock_snapshot_frame()
    )
    rows = build_monitor_v2_alert_rows(
        snapshots,
        baseline_observations=baseline_observations,
        min_baseline_observations=min_baseline_observations,
    )
    summary = summarize_monitor_v2_alerts(rows)

    rows_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    rows.to_csv(rows_path, index=False)
    summary.to_csv(summary_path, index=False)
    metadata_path.write_text(
        json.dumps(
            _build_metadata(
                snapshots=snapshots,
                rows=rows,
                summary=summary,
                snapshots_path=snapshots_path,
                baseline_observations=baseline_observations,
                min_baseline_observations=min_baseline_observations,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return MonitorV2SnapshotResult(
        rows_path=rows_path,
        summary_path=summary_path,
        metadata_path=metadata_path,
        row_count=len(rows),
        alert_count=int((rows["severity"] != "none").sum()),
        summary_row_count=len(summary),
    )


def load_snapshot_frame(path: Path) -> pd.DataFrame:
    """Load monitor v2 snapshots from a CSV file."""

    if not path.exists():
        raise FileNotFoundError(f"Monitor v2 snapshot file not found: {path}")
    return pd.read_csv(path)


def validate_snapshot_frame(snapshots: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize monitor v2 snapshot rows."""

    _require_columns(snapshots, SNAPSHOT_COLUMNS, "monitor v2 snapshots")
    frame = snapshots.loc[:, SNAPSHOT_COLUMNS].copy()
    for column in (
        "market_id",
        "tier",
        "anomaly_family",
        "metric_name",
        "evidence_ref",
        "limitation",
        "review_status",
    ):
        if frame[column].isna().any() or (
            frame[column].astype(str).str.strip() == ""
        ).any():
            raise ValueError(f"monitor v2 snapshots contain blank values in {column}")
        frame[column] = frame[column].astype(str).str.strip()

    for optional_column in ("event_candidate_id", "event_review_status"):
        frame[optional_column] = frame[optional_column].fillna("").astype(str).str.strip()

    frame["timestamp_utc"] = pd.to_datetime(
        frame["timestamp_utc"],
        utc=True,
        errors="raise",
    )
    frame["observed_value"] = pd.to_numeric(frame["observed_value"], errors="raise")
    if frame["observed_value"].isna().any():
        raise ValueError("monitor v2 snapshots contain missing observed_value")
    if "wallet_address" in snapshots.columns:
        raise ValueError("monitor v2 snapshots must not contain wallet_address")
    return frame.sort_values(
        ["market_id", "tier", "anomaly_family", "metric_name", "timestamp_utc"]
    ).reset_index(drop=True)


def build_mock_snapshot_frame() -> pd.DataFrame:
    """Return a deterministic mocked snapshot fixture for the default CLI run."""

    dates = pd.date_range("2024-10-01T00:00:00Z", periods=31, freq="D")
    metric_specs = (
        (
            "market",
            "market_move",
            "absolute_midpoint_change",
            0.01,
            0.001,
            0.12,
            "mock_clob_snapshot",
            "mocked market movement fixture; no live data",
        ),
        (
            "tier_1_top_1pct",
            "wallet_tier_activity",
            "log1p_total_observed_amount_usd",
            5.00,
            0.08,
            6.60,
            "mock_wallet_tier_snapshot",
            "mocked aggregate wallet-tier fixture; no wallet addresses",
        ),
        (
            "tier_1_top_1pct",
            "active_wallet_activity",
            "active_wallets",
            3.0,
            0.2,
            11.0,
            "mock_wallet_tier_snapshot",
            "mocked aggregate active-wallet fixture; no wallet addresses",
        ),
        (
            "all_tiers",
            "concentration",
            "top_tier_share",
            0.20,
            0.015,
            0.74,
            "mock_wallet_tier_snapshot",
            "mocked concentration fixture; no wallet performance claim",
        ),
    )
    rows: list[dict[str, object]] = []
    for index, timestamp in enumerate(dates):
        is_event_day = index == len(dates) - 1
        for (
            tier,
            family,
            metric_name,
            base,
            step,
            spike,
            evidence_ref,
            limitation,
        ) in metric_specs:
            observed = spike if is_event_day else base + step * (index % 5)
            rows.append(
                {
                    "timestamp_utc": timestamp.isoformat().replace("+00:00", "Z"),
                    "market_id": "mock_polymarket_politics_geo_market",
                    "tier": tier,
                    "anomaly_family": family,
                    "metric_name": metric_name,
                    "observed_value": observed,
                    "event_candidate_id": "mock_event_candidate" if is_event_day else "",
                    "event_review_status": "accepted" if is_event_day else "",
                    "evidence_ref": evidence_ref,
                    "limitation": limitation,
                    "review_status": "candidate",
                }
            )
    return pd.DataFrame(rows, columns=SNAPSHOT_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshots", type=Path, default=None)
    parser.add_argument("--rows-output", type=Path, default=ALERT_ROWS_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=ALERT_SUMMARY_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    parser.add_argument("--baseline-observations", type=int, default=DEFAULT_BASELINE_OBSERVATIONS)
    parser.add_argument("--min-baseline-observations", type=int, default=DEFAULT_MIN_BASELINE_OBSERVATIONS)
    args = parser.parse_args(argv)

    try:
        result = generate_monitor_v2_snapshot_outputs(
            snapshots_path=args.snapshots,
            rows_path=args.rows_output,
            summary_path=args.summary_output,
            metadata_path=args.metadata_output,
            baseline_observations=args.baseline_observations,
            min_baseline_observations=args.min_baseline_observations,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _score_value(
    observed: float,
    baseline_values: Sequence[float],
    *,
    min_baseline_observations: int,
) -> dict[str, object]:
    baseline_count = len(baseline_values)
    if baseline_count < min_baseline_observations:
        return {
            "baseline_observations": baseline_count,
            "rolling_median": None,
            "rolling_mad": None,
            "robust_z": None,
            "rolling_percentile_rank": None,
            "severity": "none",
            "status": "insufficient_baseline",
        }

    values = np.asarray(baseline_values, dtype=float)
    rolling_median = float(np.median(values))
    rolling_mad = float(np.median(np.abs(values - rolling_median)))
    percentile_rank = float((values <= observed).sum() / len(values))
    if rolling_mad <= 0:
        return {
            "baseline_observations": baseline_count,
            "rolling_median": rolling_median,
            "rolling_mad": rolling_mad,
            "robust_z": None,
            "rolling_percentile_rank": percentile_rank,
            "severity": "none",
            "status": "zero_mad",
        }

    robust_z = float((observed - rolling_median) / (ROBUST_SCALE_FACTOR * rolling_mad))
    return {
        "baseline_observations": baseline_count,
        "rolling_median": rolling_median,
        "rolling_mad": rolling_mad,
        "robust_z": robust_z,
        "rolling_percentile_rank": percentile_rank,
        "severity": _severity_from_scores(robust_z, percentile_rank),
        "status": "ok",
    }


def _severity_from_scores(robust_z: float, percentile_rank: float) -> str:
    if robust_z >= 3.0:
        return "high"
    if robust_z >= 2.0 or percentile_rank >= 0.95:
        return "watch"
    if robust_z >= 1.5 or percentile_rank >= 0.90:
        return "info"
    return "none"


def _apply_cluster_severity(rows: pd.DataFrame) -> pd.DataFrame:
    if rows.empty:
        return rows
    upgraded = rows.copy()
    for _, group in upgraded.groupby(["timestamp_utc", "market_id"], sort=False):
        has_reviewed_event = group["event_review_status"].isin(EVENT_ACCEPTED_STATUSES).any()
        has_market_watch = (
            (group["anomaly_family"] == "market_move")
            & group["severity"].isin(WATCH_OR_HIGH)
        ).any()
        has_wallet_watch = (
            group["anomaly_family"].isin(WALLET_OR_CONCENTRATION_FAMILIES)
            & group["severity"].isin(WATCH_OR_HIGH)
        ).any()
        if not (has_reviewed_event and has_market_watch and has_wallet_watch):
            continue
        index = group.index[
            group["severity"].isin(WATCH_OR_HIGH)
            & group["anomaly_family"].isin({"market_move", *WALLET_OR_CONCENTRATION_FAMILIES})
        ]
        upgraded.loc[index, "severity"] = "critical"
    return upgraded.loc[:, ALERT_ROW_COLUMNS]


def _build_metadata(
    *,
    snapshots: pd.DataFrame,
    rows: pd.DataFrame,
    summary: pd.DataFrame,
    snapshots_path: Path | None,
    baseline_observations: int,
    min_baseline_observations: int,
) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "monitor_v2_deterministic_snapshot_prototype",
            "input_mode": "csv_snapshot_replay" if snapshots_path else "built_in_mock_snapshot_fixture",
            "baseline_observations": baseline_observations,
            "min_baseline_observations": min_baseline_observations,
            "robust_score": "robust_z = (value - rolling_median) / (1.4826 * MAD)",
            "percentile_score": "rolling empirical percentile rank",
            "uses_completed_prior_observations": True,
        },
        "inputs": {
            "snapshots_path": "" if snapshots_path is None else str(snapshots_path),
            "snapshot_rows": int(len(snapshots)),
            "columns": list(SNAPSHOT_COLUMNS),
        },
        "outputs": {
            "alert_row_count": int(len(rows)),
            "alert_count": int((rows["severity"] != "none").sum()),
            "summary_row_count": int(len(summary)),
            "row_columns": list(ALERT_ROW_COLUMNS),
            "summary_columns": list(ALERT_SUMMARY_COLUMNS),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "limitations": {
            "mock_or_recorded_snapshots_only": True,
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


def _max_severity(values: pd.Series) -> str:
    return max((str(value) for value in values), key=lambda value: SEVERITY_RANK[value])


def _safe_max(values: pd.Series) -> float | None:
    clean = values.dropna()
    if clean.empty:
        return None
    return float(clean.max())


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


if __name__ == "__main__":
    raise SystemExit(main())
