"""Evaluate whether monitor candidates detect reviewed events or references."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from operations.analysis.monitor_candidate_review_report import REVIEW_REPORT_OUTPUT
from operations.analysis.monitor_reference_candidates import (
    CANDIDATE_SIMILARITY_SUMMARY_OUTPUT,
)
from operations.analysis.monitor_wallet_graph import GRAPH_METRICS_OUTPUT
from operations.analysis.run_h2_event_windows import RESULTS_DIR, SEED_PATH


BACKTEST_CASES_OUTPUT = RESULTS_DIR / "monitor_detection_backtest_cases.csv"
BACKTEST_SUMMARY_OUTPUT = RESULTS_DIR / "monitor_detection_backtest_summary.csv"
BACKTEST_DASHBOARD_OUTPUT = RESULTS_DIR / "monitor_detection_backtest_dashboard.html"
BACKTEST_METADATA_OUTPUT = RESULTS_DIR / "monitor_detection_backtest_metadata.json"

CASE_COLUMNS: tuple[str, ...] = (
    "case_id",
    "candidate_id",
    "timestamp_utc",
    "market_id",
    "question",
    "max_severity",
    "review_priority",
    "event_hit",
    "pre_event_hit",
    "nearest_event_id",
    "nearest_event_title",
    "lead_time_hours",
    "lead_time_direction",
    "reference_hit",
    "best_reference_case_id",
    "best_similarity_score",
    "graph_cluster_label",
    "false_context_flag",
    "allowed_interpretation",
    "limitation",
    "claim_scope",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "summary_id",
    "candidate_count",
    "event_hit_count",
    "pre_event_hit_count",
    "reference_hit_count",
    "false_context_count",
    "review_yield_proxy",
    "allowed_interpretation",
    "limitation",
)


@dataclass(frozen=True)
class DetectionBacktestResult:
    cases_path: Path
    summary_path: Path
    dashboard_path: Path
    metadata_path: Path
    candidate_count: int
    event_hit_count: int
    reference_hit_count: int

    def to_dict(self) -> dict[str, int | str]:
        return {
            "cases_path": str(self.cases_path),
            "summary_path": str(self.summary_path),
            "dashboard_path": str(self.dashboard_path),
            "metadata_path": str(self.metadata_path),
            "candidate_count": self.candidate_count,
            "event_hit_count": self.event_hit_count,
            "reference_hit_count": self.reference_hit_count,
        }


def build_detection_backtest(
    *,
    review_report: pd.DataFrame,
    events: pd.DataFrame,
    similarity_summary: pd.DataFrame | None = None,
    graph_metrics: pd.DataFrame | None = None,
    pre_event_window_hours: float = 24.0,
    near_event_window_hours: float = 24.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return candidate-level detection cases and compact summary."""

    if pre_event_window_hours < 0 or near_event_window_hours < 0:
        raise ValueError("event windows must be >= 0")
    candidates = _validate_review_report(review_report)
    event_frame = _validate_events(events)
    similarity_lookup = _similarity_lookup(
        similarity_summary if similarity_summary is not None else pd.DataFrame()
    )
    graph_label = _graph_label(graph_metrics if graph_metrics is not None else pd.DataFrame())
    cases: list[dict[str, object]] = []
    for candidate in candidates.to_dict(orient="records"):
        timestamp = pd.Timestamp(candidate["timestamp_utc"])
        event = _nearest_event(timestamp, event_frame)
        lead_hours = event["lead_time_hours"] if event else None
        pre_event_hit = (
            lead_hours is not None and 0 <= lead_hours <= pre_event_window_hours
        )
        near_event_hit = (
            lead_hours is not None and abs(lead_hours) <= near_event_window_hours
        )
        candidate_id = str(candidate["candidate_id"])
        similarity = similarity_lookup.get(candidate_id, {})
        similarity_score = _float(similarity.get("best_similarity_score", 0.0))
        reference_hit = similarity_score >= 0.75
        cluster_label = graph_label if graph_label else "graph_unavailable"
        false_context = not near_event_hit and not reference_hit and cluster_label in {
            "graph_unavailable",
            "isolated_wallet",
        }
        cases.append(
            {
                "case_id": f"detection_case_{len(cases) + 1:03d}",
                "candidate_id": candidate_id,
                "timestamp_utc": candidate["timestamp_utc"],
                "market_id": candidate["market_id"],
                "question": candidate["question"],
                "max_severity": candidate["max_severity"],
                "review_priority": candidate["review_priority"],
                "event_hit": bool(near_event_hit),
                "pre_event_hit": bool(pre_event_hit),
                "nearest_event_id": event["event_id"] if event else "",
                "nearest_event_title": event["title"] if event else "",
                "lead_time_hours": "" if lead_hours is None else round(float(lead_hours), 6),
                "lead_time_direction": _lead_direction(lead_hours),
                "reference_hit": bool(reference_hit),
                "best_reference_case_id": similarity.get("best_reference_case_id", ""),
                "best_similarity_score": round(similarity_score, 6),
                "graph_cluster_label": cluster_label,
                "false_context_flag": bool(false_context),
                "allowed_interpretation": (
                    "Detection-backtest review case only; evaluates whether a "
                    "candidate has event, reference, or wallet-graph context."
                ),
                "limitation": (
                    "No return, PnL, causal, misconduct, or order-execution "
                    "claim is made."
                ),
                "claim_scope": "monitor_detection_backtest_review_only",
            }
        )
    case_frame = pd.DataFrame(cases, columns=CASE_COLUMNS)
    return case_frame, _summary(case_frame)


def generate_detection_backtest_outputs(
    *,
    review_report_path: Path = REVIEW_REPORT_OUTPUT,
    events_path: Path = SEED_PATH,
    similarity_summary_path: Path = CANDIDATE_SIMILARITY_SUMMARY_OUTPUT,
    graph_metrics_path: Path = GRAPH_METRICS_OUTPUT,
    cases_path: Path = BACKTEST_CASES_OUTPUT,
    summary_path: Path = BACKTEST_SUMMARY_OUTPUT,
    dashboard_path: Path = BACKTEST_DASHBOARD_OUTPUT,
    metadata_path: Path = BACKTEST_METADATA_OUTPUT,
    pre_event_window_hours: float = 24.0,
    near_event_window_hours: float = 24.0,
) -> DetectionBacktestResult:
    """Write detection-backtest cases, summary, dashboard, and metadata."""

    review_report = _read_csv(review_report_path, "human review report")
    events = _read_csv(events_path, "curated events")
    similarity = _read_optional_csv(similarity_summary_path)
    graph_metrics = _read_optional_csv(graph_metrics_path)
    cases, summary = build_detection_backtest(
        review_report=review_report,
        events=events,
        similarity_summary=similarity,
        graph_metrics=graph_metrics,
        pre_event_window_hours=pre_event_window_hours,
        near_event_window_hours=near_event_window_hours,
    )
    for path, frame in ((cases_path, cases), (summary_path, summary)):
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)
    _write_dashboard(cases, summary, dashboard_path)
    metadata = _metadata(
        cases=cases,
        review_report_path=review_report_path,
        events_path=events_path,
        similarity_summary_path=similarity_summary_path,
        graph_metrics_path=graph_metrics_path,
        cases_path=cases_path,
        summary_path=summary_path,
        dashboard_path=dashboard_path,
        pre_event_window_hours=pre_event_window_hours,
        near_event_window_hours=near_event_window_hours,
    )
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return DetectionBacktestResult(
        cases_path=cases_path,
        summary_path=summary_path,
        dashboard_path=dashboard_path,
        metadata_path=metadata_path,
        candidate_count=int(len(cases)),
        event_hit_count=int(cases["event_hit"].sum()) if not cases.empty else 0,
        reference_hit_count=int(cases["reference_hit"].sum()) if not cases.empty else 0,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-report", type=Path, default=REVIEW_REPORT_OUTPUT)
    parser.add_argument("--events", type=Path, default=SEED_PATH)
    parser.add_argument("--similarity-summary", type=Path, default=CANDIDATE_SIMILARITY_SUMMARY_OUTPUT)
    parser.add_argument("--graph-metrics", type=Path, default=GRAPH_METRICS_OUTPUT)
    parser.add_argument("--cases-output", type=Path, default=BACKTEST_CASES_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=BACKTEST_SUMMARY_OUTPUT)
    parser.add_argument("--dashboard-output", type=Path, default=BACKTEST_DASHBOARD_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=BACKTEST_METADATA_OUTPUT)
    parser.add_argument("--pre-event-window-hours", type=float, default=24.0)
    parser.add_argument("--near-event-window-hours", type=float, default=24.0)
    args = parser.parse_args(argv)
    try:
        result = generate_detection_backtest_outputs(
            review_report_path=args.review_report,
            events_path=args.events,
            similarity_summary_path=args.similarity_summary,
            graph_metrics_path=args.graph_metrics,
            cases_path=args.cases_output,
            summary_path=args.summary_output,
            dashboard_path=args.dashboard_output,
            metadata_path=args.metadata_output,
            pre_event_window_hours=args.pre_event_window_hours,
            near_event_window_hours=args.near_event_window_hours,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_review_report(frame: pd.DataFrame) -> pd.DataFrame:
    required = (
        "candidate_id",
        "timestamp_utc",
        "market_id",
        "question",
        "max_severity",
        "review_priority",
    )
    _require_columns(frame, required, "human review report")
    data = frame.loc[:, list(required)].copy()
    data["timestamp_utc"] = pd.to_datetime(data["timestamp_utc"], utc=True, errors="raise")
    data["timestamp_utc"] = data["timestamp_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return data


def _validate_events(frame: pd.DataFrame) -> pd.DataFrame:
    _require_columns(frame, ("event_id", "event_date", "title"), "curated events")
    data = frame.loc[:, [column for column in ("event_id", "event_date", "event_time_utc", "title") if column in frame.columns]].copy()
    if "event_time_utc" not in data.columns:
        data["event_time_utc"] = ""
    event_times = []
    for event in data.to_dict(orient="records"):
        event_times.append(_event_timestamp(event["event_date"], event.get("event_time_utc", "")))
    data["event_timestamp_utc"] = event_times
    return data


def _nearest_event(timestamp: pd.Timestamp, events: pd.DataFrame) -> dict[str, object] | None:
    if events.empty:
        return None
    candidate_ts = pd.Timestamp(timestamp)
    best: dict[str, object] | None = None
    best_abs: float | None = None
    for event in events.to_dict(orient="records"):
        event_ts = pd.Timestamp(event["event_timestamp_utc"])
        lead_hours = (event_ts - candidate_ts).total_seconds() / 3600.0
        distance = abs(lead_hours)
        if best_abs is None or distance < best_abs:
            best_abs = distance
            best = {
                "event_id": event["event_id"],
                "title": event["title"],
                "lead_time_hours": lead_hours,
            }
    return best


def _event_timestamp(event_date: object, event_time_utc: object) -> pd.Timestamp:
    date_text = str(event_date).strip()
    time_text = str(event_time_utc).strip()
    if not time_text:
        time_text = "00:00:00"
    if time_text.endswith("Z"):
        timestamp_text = f"{date_text}T{time_text}"
    else:
        timestamp_text = f"{date_text}T{time_text}Z"
    return pd.Timestamp(timestamp_text).tz_convert("UTC")


def _similarity_lookup(frame: pd.DataFrame) -> dict[str, dict[str, object]]:
    if frame.empty:
        return {}
    _require_columns(
        frame,
        ("candidate_id", "best_reference_case_id", "best_similarity_score"),
        "candidate similarity summary",
    )
    return {str(row["candidate_id"]): row for row in frame.to_dict(orient="records")}


def _graph_label(frame: pd.DataFrame) -> str:
    if frame.empty or "cluster_label" not in frame.columns:
        return "graph_unavailable"
    labels = frame["cluster_label"].astype(str).tolist()
    if "shared_bucket_cluster" in labels:
        return "shared_bucket_cluster"
    if "shared_market_context" in labels:
        return "shared_market_context"
    if labels:
        return sorted(labels)[0]
    return "graph_unavailable"


def _summary(cases: pd.DataFrame) -> pd.DataFrame:
    candidate_count = int(len(cases))
    event_hit_count = int(cases["event_hit"].sum()) if not cases.empty else 0
    pre_event_hit_count = int(cases["pre_event_hit"].sum()) if not cases.empty else 0
    reference_hit_count = int(cases["reference_hit"].sum()) if not cases.empty else 0
    false_context_count = int(cases["false_context_flag"].sum()) if not cases.empty else 0
    useful = event_hit_count + reference_hit_count
    review_yield = 0.0 if candidate_count == 0 else useful / candidate_count
    return pd.DataFrame(
        [
            {
                "summary_id": "monitor_detection_backtest_v1",
                "candidate_count": candidate_count,
                "event_hit_count": event_hit_count,
                "pre_event_hit_count": pre_event_hit_count,
                "reference_hit_count": reference_hit_count,
                "false_context_count": false_context_count,
                "review_yield_proxy": round(review_yield, 6),
                "allowed_interpretation": (
                    "Detection quality proxy for monitor review candidates, "
                    "not a return or trading backtest."
                ),
                "limitation": (
                    "Event matching depends on curated timestamps and public "
                    "reference similarity; human review remains required."
                ),
            }
        ],
        columns=SUMMARY_COLUMNS,
    )


def _write_dashboard(cases: pd.DataFrame, summary: pd.DataFrame, dashboard_path: Path) -> None:
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    stats = summary.iloc[0].to_dict() if not summary.empty else {}
    rows = _table_rows(
        cases.head(50),
        (
            "question",
            "max_severity",
            "event_hit",
            "pre_event_hit",
            "reference_hit",
            "lead_time_hours",
            "graph_cluster_label",
            "false_context_flag",
        ),
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Monitor Detection Backtest</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 28px; color: #17202a; }}
    .note {{ background: #fff7e6; border: 1px solid #f0d08a; padding: 12px; border-radius: 6px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 12px; }}
    .metric {{ border: 1px solid #d7dde5; border-radius: 6px; padding: 12px; background: #f8fafc; }}
    .metric strong {{ display: block; font-size: 22px; margin-top: 4px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; font-size: 13px; }}
    th, td {{ border: 1px solid #d7dde5; padding: 7px; text-align: left; vertical-align: top; }}
    th {{ background: #eef2f7; }}
  </style>
</head>
<body>
  <h1>Monitor Detection Backtest</h1>
  <p class="note">This measures whether review candidates have event, reference, or wallet-graph context. It is not a return test, not a causal test, and not a trading signal.</p>
  <section class="metrics">
    <div class="metric">Candidates<strong>{stats.get("candidate_count", 0)}</strong></div>
    <div class="metric">Event hits<strong>{stats.get("event_hit_count", 0)}</strong></div>
    <div class="metric">Reference hits<strong>{stats.get("reference_hit_count", 0)}</strong></div>
    <div class="metric">Review-yield proxy<strong>{float(stats.get("review_yield_proxy", 0.0)):.2f}</strong></div>
  </section>
  <h2>Detection Cases</h2>
  <table><thead><tr><th>Question</th><th>Severity</th><th>Event hit</th><th>Pre-event hit</th><th>Reference hit</th><th>Lead hours</th><th>Graph context</th><th>False context</th></tr></thead><tbody>{rows}</tbody></table>
</body>
</html>
"""
    dashboard_path.write_text(html, encoding="utf-8")


def _table_rows(frame: pd.DataFrame, columns: Sequence[str]) -> str:
    if frame.empty:
        return ""
    rows = []
    for item in frame.loc[:, list(columns)].to_dict(orient="records"):
        cells = "".join(f"<td>{escape(_format_cell(item[column]))}</td>" for column in columns)
        rows.append(f"<tr>{cells}</tr>")
    return "\n".join(rows)


def _format_cell(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _lead_direction(value: object) -> str:
    if value is None or value == "":
        return "unknown"
    number = float(value)
    if number > 0:
        return "candidate_before_event"
    if number < 0:
        return "candidate_after_event"
    return "same_time"


def _metadata(
    *,
    cases: pd.DataFrame,
    review_report_path: Path,
    events_path: Path,
    similarity_summary_path: Path,
    graph_metrics_path: Path,
    cases_path: Path,
    summary_path: Path,
    dashboard_path: Path,
    pre_event_window_hours: float,
    near_event_window_hours: float,
) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "monitor_detection_backtest",
            "pre_event_window_hours": pre_event_window_hours,
            "near_event_window_hours": near_event_window_hours,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
        },
        "inputs": {
            "review_report_path": str(review_report_path),
            "events_path": str(events_path),
            "similarity_summary_path": str(similarity_summary_path),
            "graph_metrics_path": str(graph_metrics_path),
        },
        "outputs": {
            "cases_path": str(cases_path),
            "summary_path": str(summary_path),
            "dashboard_path": str(dashboard_path),
            "candidate_count": int(len(cases)),
            "event_hit_count": int(cases["event_hit"].sum()) if not cases.empty else 0,
            "reference_hit_count": int(cases["reference_hit"].sum()) if not cases.empty else 0,
            "contains_order_instructions": False,
        },
        "limitations": {
            "not_a_return_backtest": True,
            "not_a_causal_test": True,
            "human_review_required": True,
        },
    }


def _read_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    frame = pd.read_csv(path, keep_default_na=False)
    if frame.empty:
        raise ValueError(f"{label} is empty: {path}")
    return frame


def _read_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, keep_default_na=False)


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{label} missing columns: {missing}")


def _float(value: object) -> float:
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


if __name__ == "__main__":
    raise SystemExit(main())
