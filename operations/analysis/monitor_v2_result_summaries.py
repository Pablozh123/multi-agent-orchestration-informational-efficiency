"""Generate bounded monitor v2 summaries from accepted recorded scoring outputs.

The summaries in this module are compact, deterministic aggregations of
existing monitor v2 result artifacts. They are intended as a safe boundary for
later review, MCP, or LLM interpretation layers. This module does not call live
APIs, WebSockets, databases, LLMs, agents, MCP tools, ML systems, or execution
paths.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from operations.analysis.monitor_v2_recorded_input_scoring import (
    ALERT_ROWS_OUTPUT,
    ALERT_SUMMARY_OUTPUT,
    CONTEXT_ROWS_OUTPUT,
    METADATA_OUTPUT as SCORING_METADATA_OUTPUT,
    VALIDATION_REPORT_OUTPUT,
)
from operations.analysis.run_h2_event_windows import RESULTS_DIR


SUMMARY_OUTPUT = RESULTS_DIR / "monitor_v2_bounded_summary.csv"
METADATA_OUTPUT = RESULTS_DIR / "monitor_v2_bounded_summary_metadata.json"

SUMMARY_COLUMNS: tuple[str, ...] = (
    "summary_id",
    "summary_type",
    "label",
    "metric",
    "value",
    "source_artifact",
    "allowed_interpretation",
    "limitation",
    "claim_scope",
)

SEVERITY_ORDER = ("none", "info", "watch", "high", "critical")
CONTEXT_LABEL_ORDER = (
    "no_event_alert",
    "context_alert",
    "event_watch_candidate",
    "critical_proximity_candidate",
)


@dataclass(frozen=True)
class MonitorV2SummaryResult:
    """Summary of generated bounded monitor v2 summary artifacts."""

    summary_path: Path
    metadata_path: Path
    row_count: int

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "summary_path": str(self.summary_path),
            "metadata_path": str(self.metadata_path),
            "row_count": self.row_count,
        }


def generate_monitor_v2_bounded_summaries(
    *,
    alert_rows_path: Path = ALERT_ROWS_OUTPUT,
    alert_summary_path: Path = ALERT_SUMMARY_OUTPUT,
    context_rows_path: Path = CONTEXT_ROWS_OUTPUT,
    validation_report_path: Path = VALIDATION_REPORT_OUTPUT,
    scoring_metadata_path: Path = SCORING_METADATA_OUTPUT,
    summary_path: Path = SUMMARY_OUTPUT,
    metadata_path: Path = METADATA_OUTPUT,
) -> MonitorV2SummaryResult:
    """Write bounded monitor v2 summary CSV and metadata artifacts."""

    artifacts = load_monitor_v2_summary_artifacts(
        alert_rows_path=alert_rows_path,
        alert_summary_path=alert_summary_path,
        context_rows_path=context_rows_path,
        validation_report_path=validation_report_path,
        scoring_metadata_path=scoring_metadata_path,
    )
    summary = build_monitor_v2_bounded_summary(
        artifacts,
        alert_rows_path=alert_rows_path,
        alert_summary_path=alert_summary_path,
        context_rows_path=context_rows_path,
        validation_report_path=validation_report_path,
        scoring_metadata_path=scoring_metadata_path,
    )

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(summary_path, index=False)
    metadata_path.write_text(
        json.dumps(
            _build_metadata(
                summary=summary,
                alert_rows_path=alert_rows_path,
                alert_summary_path=alert_summary_path,
                context_rows_path=context_rows_path,
                validation_report_path=validation_report_path,
                scoring_metadata_path=scoring_metadata_path,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return MonitorV2SummaryResult(
        summary_path=summary_path,
        metadata_path=metadata_path,
        row_count=len(summary),
    )


def load_monitor_v2_summary_artifacts(
    *,
    alert_rows_path: Path,
    alert_summary_path: Path,
    context_rows_path: Path,
    validation_report_path: Path,
    scoring_metadata_path: Path,
) -> dict[str, Any]:
    """Load required monitor v2 result artifacts for compact summaries."""

    for path in (
        alert_rows_path,
        alert_summary_path,
        context_rows_path,
        validation_report_path,
        scoring_metadata_path,
    ):
        if not path.exists():
            raise FileNotFoundError(f"Required monitor v2 summary source artifact missing: {path}")

    alert_rows = pd.read_csv(alert_rows_path)
    alert_summary = pd.read_csv(alert_summary_path)
    context_rows = pd.read_csv(context_rows_path)
    validation_report = json.loads(validation_report_path.read_text(encoding="utf-8"))
    scoring_metadata = json.loads(scoring_metadata_path.read_text(encoding="utf-8"))
    _require_columns(
        alert_rows,
        ("severity", "anomaly_family", "metric_name", "claim_scope"),
        str(alert_rows_path),
    )
    _require_columns(
        alert_summary,
        ("anomaly_family", "metric_name", "alert_count", "max_severity", "max_robust_z"),
        str(alert_summary_path),
    )
    _require_columns(context_rows, ("suggested_context_label",), str(context_rows_path))
    _reject_raw_fields(alert_rows, "alert rows")
    _reject_raw_fields(alert_summary, "alert summary")
    _reject_raw_fields(context_rows, "context rows")
    return {
        "alert_rows": alert_rows,
        "alert_summary": alert_summary,
        "context_rows": context_rows,
        "validation_report": validation_report,
        "scoring_metadata": scoring_metadata,
    }


def build_monitor_v2_bounded_summary(
    artifacts: dict[str, Any],
    *,
    alert_rows_path: Path,
    alert_summary_path: Path,
    context_rows_path: Path,
    validation_report_path: Path,
    scoring_metadata_path: Path,
) -> pd.DataFrame:
    """Return compact monitor v2 summary rows from loaded result artifacts."""

    alert_rows = artifacts["alert_rows"]
    alert_summary = artifacts["alert_summary"]
    context_rows = artifacts["context_rows"]
    validation_report = artifacts["validation_report"]
    scoring_metadata = artifacts["scoring_metadata"]
    output_counts = scoring_metadata.get("outputs", {})

    rows: list[dict[str, object]] = [
        _summary_row(
            summary_id="monitor_v2_validation_status",
            summary_type="validation",
            label="recorded_input_scoring",
            metric="validation_status",
            value=str(validation_report.get("status", "unknown")),
            source_artifact=validation_report_path,
            allowed_interpretation="Recorded input files passed deterministic validation before scoring.",
            limitation="Validation confirms file-contract consistency, not live data completeness.",
        ),
        _summary_row(
            summary_id="monitor_v2_snapshot_count",
            summary_type="coverage",
            label="recorded_scoring_snapshots",
            metric="snapshot_count",
            value=int(output_counts.get("snapshot_count", len(alert_rows))),
            source_artifact=scoring_metadata_path,
            allowed_interpretation="The recorded scoring run produced a bounded daily replay panel.",
            limitation="Replay coverage is daily and file-based, not live or intraday.",
        ),
        _summary_row(
            summary_id="monitor_v2_alert_row_count",
            summary_type="coverage",
            label="recorded_alert_rows",
            metric="alert_row_count",
            value=int(output_counts.get("alert_row_count", len(alert_rows))),
            source_artifact=scoring_metadata_path,
            allowed_interpretation="Alert rows are deterministic diagnostics produced from validated inputs.",
            limitation="Row-level alerts remain file-based and should not be pasted into prompts.",
        ),
    ]
    rows.extend(_severity_rows(alert_rows, alert_rows_path))
    rows.extend(_context_rows(context_rows, context_rows_path))
    rows.extend(_family_rows(alert_summary, alert_summary_path))
    rows.extend(_strongest_metric_rows(alert_summary, alert_summary_path))

    frame = pd.DataFrame(rows, columns=SUMMARY_COLUMNS)
    _reject_forbidden_output_text(frame)
    return frame


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--alert-rows", type=Path, default=ALERT_ROWS_OUTPUT)
    parser.add_argument("--alert-summary", type=Path, default=ALERT_SUMMARY_OUTPUT)
    parser.add_argument("--context-rows", type=Path, default=CONTEXT_ROWS_OUTPUT)
    parser.add_argument("--validation-report", type=Path, default=VALIDATION_REPORT_OUTPUT)
    parser.add_argument("--scoring-metadata", type=Path, default=SCORING_METADATA_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)

    try:
        result = generate_monitor_v2_bounded_summaries(
            alert_rows_path=args.alert_rows,
            alert_summary_path=args.alert_summary,
            context_rows_path=args.context_rows,
            validation_report_path=args.validation_report,
            scoring_metadata_path=args.scoring_metadata,
            summary_path=args.summary_output,
            metadata_path=args.metadata_output,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _severity_rows(alert_rows: pd.DataFrame, source_artifact: Path) -> list[dict[str, object]]:
    counts = alert_rows["severity"].value_counts().reindex(SEVERITY_ORDER, fill_value=0)
    return [
        _summary_row(
            summary_id=f"monitor_v2_severity_{severity}",
            summary_type="direct_severity_count",
            label=severity,
            metric="row_count",
            value=int(count),
            source_artifact=source_artifact,
            allowed_interpretation="Direct severity counts describe recorded monitor diagnostics.",
            limitation="Direct severities are descriptive and do not imply trading action.",
        )
        for severity, count in counts.items()
    ]


def _context_rows(context_rows: pd.DataFrame, source_artifact: Path) -> list[dict[str, object]]:
    counts = (
        context_rows["suggested_context_label"]
        .value_counts()
        .reindex(CONTEXT_LABEL_ORDER, fill_value=0)
    )
    return [
        _summary_row(
            summary_id=f"monitor_v2_context_{label}",
            summary_type="event_context_label_count",
            label=label,
            metric="event_window_row_count",
            value=int(count),
            source_artifact=source_artifact,
            allowed_interpretation="Event-context labels describe reviewed daily event-window proximity.",
            limitation="Event proximity is daily context, not same-timestamp reaction-speed evidence.",
        )
        for label, count in counts.items()
    ]


def _family_rows(alert_summary: pd.DataFrame, source_artifact: Path) -> list[dict[str, object]]:
    family = (
        alert_summary.groupby("anomaly_family", as_index=False)["alert_count"]
        .sum()
        .sort_values(["alert_count", "anomaly_family"], ascending=[False, True])
    )
    return [
        _summary_row(
            summary_id=f"monitor_v2_family_alert_count_{row['anomaly_family']}",
            summary_type="metric_family",
            label=str(row["anomaly_family"]),
            metric="alert_count",
            value=int(row["alert_count"]),
            source_artifact=source_artifact,
            allowed_interpretation="Metric-family counts show which aggregate monitor families generated diagnostics.",
            limitation="Family counts are not source attribution or mechanism evidence.",
        )
        for row in family.to_dict(orient="records")
    ]


def _strongest_metric_rows(alert_summary: pd.DataFrame, source_artifact: Path) -> list[dict[str, object]]:
    frame = alert_summary.copy()
    frame["max_robust_z"] = pd.to_numeric(frame["max_robust_z"], errors="coerce")
    frame = frame.dropna(subset=["max_robust_z"])
    if frame.empty:
        return []
    top = frame.sort_values(
        ["max_robust_z", "alert_count", "anomaly_family", "metric_name"],
        ascending=[False, False, True, True],
    ).head(3)
    rows: list[dict[str, object]] = []
    for index, row in enumerate(top.to_dict(orient="records"), start=1):
        rows.append(
            _summary_row(
                summary_id=f"monitor_v2_strongest_metric_{index}",
                summary_type="strongest_metric",
                label=f"{row['anomaly_family']} | {row['metric_name']}",
                metric="max_robust_z",
                value=float(row["max_robust_z"]),
                source_artifact=source_artifact,
                allowed_interpretation="Strongest metrics indicate where robust-score diagnostics were largest.",
                limitation="Large robust scores describe unusual recorded values, not cause or future performance.",
            )
        )
    return rows


def _summary_row(
    *,
    summary_id: str,
    summary_type: str,
    label: str,
    metric: str,
    value: object,
    source_artifact: Path,
    allowed_interpretation: str,
    limitation: str,
    claim_scope: str = "bounded_monitor_summary_only",
) -> dict[str, object]:
    return {
        "summary_id": summary_id,
        "summary_type": summary_type,
        "label": label,
        "metric": metric,
        "value": value,
        "source_artifact": str(source_artifact),
        "allowed_interpretation": allowed_interpretation,
        "limitation": limitation,
        "claim_scope": claim_scope,
    }


def _build_metadata(
    *,
    summary: pd.DataFrame,
    alert_rows_path: Path,
    alert_summary_path: Path,
    context_rows_path: Path,
    validation_report_path: Path,
    scoring_metadata_path: Path,
) -> dict[str, Any]:
    return {
        "method": {
            "name": "monitor_v2_bounded_summary_aggregation",
            "calculation_scope": "compact_aggregation_of_existing_monitor_v2_outputs",
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
        },
        "outputs": {
            "summary_rows": int(len(summary)),
            "summary_columns": list(SUMMARY_COLUMNS),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "source_artifacts": [
            str(alert_rows_path),
            str(alert_summary_path),
            str(context_rows_path),
            str(validation_report_path),
            str(scoring_metadata_path),
        ],
        "limitations": {
            "daily_replay_only": True,
            "uses_existing_recorded_scoring_outputs": True,
            "uses_aggregate_wallet_tier_activity": True,
            "uses_observed_buy_side_activity_extract": True,
            "no_live_websocket_or_api_collection": True,
            "does_not_write_database": True,
            "does_not_send_orders": True,
        },
    }


def _reject_raw_fields(frame: pd.DataFrame, name: str) -> None:
    if "wallet_address" in frame.columns:
        raise ValueError(f"{name} must not contain wallet_address")


def _reject_forbidden_output_text(frame: pd.DataFrame) -> None:
    text = "\n".join(frame.astype(str).agg(" ".join, axis=1).tolist()).lower()
    forbidden = ("0x", "execution directive", "guaranteed")
    found = [term for term in forbidden if term in text]
    if found:
        raise ValueError(f"bounded monitor summary contains forbidden text: {found}")


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


if __name__ == "__main__":
    raise SystemExit(main())
