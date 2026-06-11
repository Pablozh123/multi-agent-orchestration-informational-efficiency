"""Build a deterministic anomaly review queue from bounded monitor artifacts.

The queue is a human-review surface over existing monitor outputs. It does not
collect data, expose wallet addresses, calculate metrics with an LLM, activate
agents or MCP, or create trading instructions.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from operations.analysis.monitor_candidate_review_report import (
    MATERIALITY_CONTEXT_OUTPUT,
    REVIEW_REPORT_OUTPUT,
)
from operations.analysis.monitor_detection_backtest import BACKTEST_CASES_OUTPUT
from operations.analysis.monitor_literature_risk_scores import RISK_SCORE_SUMMARY_OUTPUT
from operations.analysis.monitor_reference_candidates import (
    MONITOR_ALERT_COLUMNS,
    monitor_candidate_id,
)
from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.collectors.polymarket_rolling_history import ROLLING_ALERT_ROWS_OUTPUT


REVIEW_UPDATES_INPUT = Path("data/monitor_anomaly_review_status_updates.csv")
REVIEW_DECISIONS_INPUT = Path("data/monitor_anomaly_review_decisions.csv")
QUEUE_OUTPUT = RESULTS_DIR / "monitor_anomaly_review_queue.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "monitor_anomaly_review_summary.csv"
METADATA_OUTPUT = RESULTS_DIR / "monitor_anomaly_review_metadata.json"
DASHBOARD_OUTPUT = RESULTS_DIR / "monitor_anomaly_review_dashboard.html"
CASE_REVIEW_PACKETS_CSV_OUTPUT = RESULTS_DIR / "monitor_anomaly_case_review_packets.csv"
CASE_REVIEW_PACKETS_JSON_OUTPUT = RESULTS_DIR / "monitor_anomaly_case_review_packets.json"
STATUS_TRANSITIONS_CSV_OUTPUT = RESULTS_DIR / "monitor_anomaly_review_status_transitions.csv"
STATUS_TRANSITIONS_JSON_OUTPUT = RESULTS_DIR / "monitor_anomaly_review_status_transitions.json"
DECISION_READINESS_CSV_OUTPUT = RESULTS_DIR / "monitor_anomaly_review_decision_readiness.csv"
DECISION_READINESS_JSON_OUTPUT = RESULTS_DIR / "monitor_anomaly_review_decision_readiness.json"

MAX_MCP_ROWS = 50
ALLOWED_REVIEW_STATUSES = {
    "needs_human_review",
    "source_check_pending",
    "reviewed_false_context",
    "reviewed_keep_candidate",
    "thesis_excluded",
}

QUEUE_COLUMNS: tuple[str, ...] = (
    "case_id",
    "timestamp_utc",
    "market_id",
    "market_slug",
    "question",
    "review_priority",
    "priority_basis",
    "trigger_family",
    "market_move_context",
    "wallet_flow_context",
    "concentration_context",
    "event_context_status",
    "reference_overlap_status",
    "review_label",
    "missing_evidence",
    "human_review_status",
    "review_status_updated_at_utc",
    "review_note",
    "reviewer",
    "review_source_url",
    "event_source_url",
    "allowed_interpretation",
    "blocked_claims",
    "source_artifacts",
)

REVIEW_UPDATE_COLUMNS: tuple[str, ...] = (
    "case_id",
    "human_review_status",
    "review_status_updated_at_utc",
    "reviewer",
    "review_source_url",
    "event_source_url",
    "review_note",
)

REVIEW_DECISION_COLUMNS: tuple[str, ...] = (
    "case_id",
    "target_status",
    "decision_updated_at_utc",
    "reviewer",
    "decision_note",
    "limitations",
    "thesis_use_scope",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "summary_id",
    "queue_row_count",
    "high_priority_count",
    "medium_priority_count",
    "low_priority_count",
    "review_label_counts",
    "event_context_counts",
    "reference_overlap_counts",
    "human_review_status_counts",
    "ready_for_future_agent_contract",
    "ready_for_future_mcp_contract",
    "allowed_interpretation",
    "limitation",
)

CASE_REVIEW_PACKET_COLUMNS: tuple[str, ...] = (
    "case_id",
    "packet_id",
    "market_slug",
    "question",
    "review_priority",
    "human_review_status",
    "source_check_status",
    "source_context",
    "evidence_status",
    "missing_evidence",
    "next_review_step",
    "allowed_interpretation",
    "blocked_claims",
    "future_mcp_access",
    "future_agent_access",
    "source_queue_artifact",
)

STATUS_TRANSITION_COLUMNS: tuple[str, ...] = (
    "case_id",
    "packet_id",
    "current_status",
    "allowed_next_statuses",
    "blocked_next_statuses",
    "transition_requirements",
    "thesis_use_allowed",
    "thesis_use_gate",
    "reviewer_action_required",
    "source_packet_artifact",
    "allowed_interpretation",
    "blocked_claims",
)

DECISION_READINESS_COLUMNS: tuple[str, ...] = (
    "case_id",
    "current_status",
    "target_status",
    "decision_validation_status",
    "allowed_next_statuses",
    "missing_decision_fields",
    "thesis_use_allowed_after_decision",
    "thesis_use_scope",
    "reviewer_action_required",
    "decision_note",
    "limitations",
    "source_decision_artifact",
    "blocked_claims",
)


@dataclass(frozen=True)
class MonitorAnomalyReviewQueueResult:
    """Summary of generated anomaly-review queue artifacts."""

    queue_path: Path
    summary_path: Path
    metadata_path: Path
    dashboard_path: Path
    case_packets_csv_path: Path
    case_packets_json_path: Path
    status_transitions_csv_path: Path
    status_transitions_json_path: Path
    decision_readiness_csv_path: Path
    decision_readiness_json_path: Path
    queue_row_count: int
    high_priority_count: int
    case_packet_row_count: int
    status_transition_row_count: int
    decision_readiness_row_count: int

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "queue_path": str(self.queue_path),
            "summary_path": str(self.summary_path),
            "metadata_path": str(self.metadata_path),
            "dashboard_path": str(self.dashboard_path),
            "case_packets_csv_path": str(self.case_packets_csv_path),
            "case_packets_json_path": str(self.case_packets_json_path),
            "status_transitions_csv_path": str(self.status_transitions_csv_path),
            "status_transitions_json_path": str(self.status_transitions_json_path),
            "decision_readiness_csv_path": str(self.decision_readiness_csv_path),
            "decision_readiness_json_path": str(self.decision_readiness_json_path),
            "queue_row_count": self.queue_row_count,
            "high_priority_count": self.high_priority_count,
            "case_packet_row_count": self.case_packet_row_count,
            "status_transition_row_count": self.status_transition_row_count,
            "decision_readiness_row_count": self.decision_readiness_row_count,
        }


def build_anomaly_review_queue(
    *,
    review_report: pd.DataFrame,
    alert_rows: pd.DataFrame | None = None,
    detection_cases: pd.DataFrame | None = None,
    materiality_context: pd.DataFrame | None = None,
    risk_summary: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Return one bounded review-queue row per monitor review candidate."""

    _validate_review_report(review_report)
    for label, frame in (
        ("alert rows", alert_rows),
        ("detection cases", detection_cases),
        ("materiality context", materiality_context),
        ("risk summary", risk_summary),
    ):
        if frame is not None:
            _reject_wallet_address_columns(frame, label)
    if alert_rows is not None and not alert_rows.empty:
        _validate_alert_rows(alert_rows)

    if review_report.empty:
        return pd.DataFrame(columns=QUEUE_COLUMNS)

    alert_lookup = _alert_lookup(alert_rows if alert_rows is not None else pd.DataFrame())
    detection_lookup = _lookup_by_candidate(
        detection_cases if detection_cases is not None else pd.DataFrame()
    )
    materiality_lookup = _lookup_by_candidate(
        materiality_context if materiality_context is not None else pd.DataFrame()
    )
    risk_lookup = _lookup_by_candidate(risk_summary if risk_summary is not None else pd.DataFrame())

    rows: list[dict[str, object]] = []
    for item in review_report.sort_values(
        ["review_priority", "timestamp_utc", "candidate_id"],
    ).to_dict(orient="records"):
        candidate_id = str(item["candidate_id"])
        detection = detection_lookup.get(candidate_id, {})
        materiality = materiality_lookup.get(candidate_id, {})
        risk = risk_lookup.get(candidate_id, {})
        alert_group = alert_lookup.get(candidate_id, pd.DataFrame())
        rows.append(
            _queue_row(
                item=item,
                alert_group=alert_group,
                detection=detection,
                materiality=materiality,
                risk=risk,
            )
        )
    return pd.DataFrame(rows, columns=QUEUE_COLUMNS)


def build_anomaly_review_summary(queue: pd.DataFrame) -> pd.DataFrame:
    """Return a compact summary for the anomaly review queue."""

    _validate_queue(queue)
    high = _count(queue, "review_priority", "high")
    medium = _count(queue, "review_priority", "medium")
    low = _count(queue, "review_priority", "low")
    return pd.DataFrame(
        [
            {
                "summary_id": "monitor_anomaly_review_queue_current",
                "queue_row_count": int(len(queue)),
                "high_priority_count": high,
                "medium_priority_count": medium,
                "low_priority_count": low,
                "review_label_counts": _counts_text(queue, "review_label"),
                "event_context_counts": _counts_text(queue, "event_context_status"),
                "reference_overlap_counts": _counts_text(
                    queue,
                    "reference_overlap_status",
                ),
                "human_review_status_counts": _counts_text(
                    queue,
                    "human_review_status",
                ),
                "ready_for_future_agent_contract": True,
                "ready_for_future_mcp_contract": True,
                "allowed_interpretation": (
                    "Queue rows are deterministic human-review cues over bounded "
                    "monitor artifacts only."
                ),
                "limitation": (
                    "The queue does not prove private information, misconduct, "
                    "causality, tradeability, profitability, or future performance."
                ),
            }
        ],
        columns=SUMMARY_COLUMNS,
    )


def build_anomaly_case_review_packets(queue: pd.DataFrame) -> pd.DataFrame:
    """Return bounded case-review packets for later human, MCP, or agent access."""

    _validate_queue(queue)
    if queue.empty:
        return pd.DataFrame(columns=CASE_REVIEW_PACKET_COLUMNS)

    rows: list[dict[str, object]] = []
    priority_order = {"high": 0, "medium": 1, "low": 2}
    ordered = queue.assign(
        _priority_order=queue["review_priority"].map(priority_order).fillna(9)
    ).sort_values(["_priority_order", "timestamp_utc", "case_id"])
    for item in ordered.drop(columns=["_priority_order"]).to_dict(orient="records"):
        rows.append(_case_review_packet(item))
    packets = pd.DataFrame(rows, columns=CASE_REVIEW_PACKET_COLUMNS)
    _reject_wallet_address_columns(packets, "case review packets")
    return packets


def build_anomaly_review_status_transitions(case_packets: pd.DataFrame) -> pd.DataFrame:
    """Return deterministic review-status transition gates for case packets."""

    _validate_case_packets(case_packets)
    if case_packets.empty:
        return pd.DataFrame(columns=STATUS_TRANSITION_COLUMNS)

    rows = [
        _status_transition_row(item)
        for item in case_packets.sort_values(["review_priority", "case_id"]).to_dict(
            orient="records"
        )
    ]
    transitions = pd.DataFrame(rows, columns=STATUS_TRANSITION_COLUMNS)
    _reject_wallet_address_columns(transitions, "status transitions")
    return transitions


def build_anomaly_review_decision_readiness(
    *,
    status_transitions: pd.DataFrame,
    review_decisions: pd.DataFrame,
) -> pd.DataFrame:
    """Return validated manual decision readiness rows without applying decisions."""

    _validate_status_transitions(status_transitions)
    _validate_review_decisions(review_decisions)
    transition_lookup = {
        str(row["case_id"]): row for row in status_transitions.to_dict(orient="records")
    }
    unknown = sorted(set(review_decisions["case_id"].astype(str)) - set(transition_lookup))
    if unknown:
        raise ValueError(f"review decisions reference unknown case_id values: {unknown}")

    decision_lookup = {
        str(row["case_id"]): row for row in review_decisions.to_dict(orient="records")
    }
    rows = [
        _decision_readiness_row(
            transition=transition,
            decision=decision_lookup.get(str(transition["case_id"]), {}),
        )
        for transition in status_transitions.to_dict(orient="records")
    ]
    readiness = pd.DataFrame(rows, columns=DECISION_READINESS_COLUMNS)
    _reject_wallet_address_columns(readiness, "decision readiness")
    return readiness


def apply_review_status_updates(
    queue: pd.DataFrame,
    updates: pd.DataFrame,
) -> pd.DataFrame:
    """Return queue rows with deterministic human-review status updates applied."""

    _validate_queue(queue)
    _require_columns(updates, ("case_id", "human_review_status"), "status updates")
    invalid = sorted(set(updates["human_review_status"].astype(str)) - ALLOWED_REVIEW_STATUSES)
    if invalid:
        raise ValueError(f"invalid human_review_status values: {invalid}")

    updated = queue.copy()
    for item in updates.to_dict(orient="records"):
        case_id = str(item["case_id"])
        mask = updated["case_id"].astype(str) == case_id
        if not mask.any():
            raise ValueError(f"status update references unknown case_id: {case_id}")
        updated.loc[mask, "human_review_status"] = str(item["human_review_status"])
        updated.loc[mask, "review_status_updated_at_utc"] = str(
            item.get("review_status_updated_at_utc", "")
        )
        if "review_note" in item:
            updated.loc[mask, "review_note"] = str(item["review_note"])
        if "reviewer" in item:
            updated.loc[mask, "reviewer"] = str(item["reviewer"])
        if "review_source_url" in item:
            updated.loc[mask, "review_source_url"] = str(item["review_source_url"])
        if "event_source_url" in item:
            updated.loc[mask, "event_source_url"] = str(item["event_source_url"])
    return updated.loc[:, list(QUEUE_COLUMNS)]


def generate_monitor_anomaly_review_queue(
    *,
    review_report_path: Path = REVIEW_REPORT_OUTPUT,
    alert_rows_path: Path = ROLLING_ALERT_ROWS_OUTPUT,
    detection_cases_path: Path = BACKTEST_CASES_OUTPUT,
    materiality_context_path: Path = MATERIALITY_CONTEXT_OUTPUT,
    risk_summary_path: Path = RISK_SCORE_SUMMARY_OUTPUT,
    review_updates_path: Path = REVIEW_UPDATES_INPUT,
    review_decisions_path: Path = REVIEW_DECISIONS_INPUT,
    queue_path: Path = QUEUE_OUTPUT,
    summary_path: Path = SUMMARY_OUTPUT,
    metadata_path: Path = METADATA_OUTPUT,
    dashboard_path: Path = DASHBOARD_OUTPUT,
    case_packets_csv_path: Path = CASE_REVIEW_PACKETS_CSV_OUTPUT,
    case_packets_json_path: Path = CASE_REVIEW_PACKETS_JSON_OUTPUT,
    status_transitions_csv_path: Path = STATUS_TRANSITIONS_CSV_OUTPUT,
    status_transitions_json_path: Path = STATUS_TRANSITIONS_JSON_OUTPUT,
    decision_readiness_csv_path: Path = DECISION_READINESS_CSV_OUTPUT,
    decision_readiness_json_path: Path = DECISION_READINESS_JSON_OUTPUT,
) -> MonitorAnomalyReviewQueueResult:
    """Write the anomaly review queue, compact summary, dashboard, and metadata."""

    review_report = _read_csv_allow_empty(review_report_path, "human review report")
    alert_rows = _read_optional_csv(alert_rows_path)
    detection_cases = _read_optional_csv(detection_cases_path)
    materiality_context = _read_optional_csv(materiality_context_path)
    risk_summary = _read_optional_csv(risk_summary_path)
    review_updates = read_review_status_updates(review_updates_path)
    review_decisions = read_review_decisions(review_decisions_path)

    queue = build_anomaly_review_queue(
        review_report=review_report,
        alert_rows=alert_rows,
        detection_cases=detection_cases,
        materiality_context=materiality_context,
        risk_summary=risk_summary,
    )
    if not review_updates.empty:
        queue = apply_review_status_updates(queue, review_updates)
    summary = build_anomaly_review_summary(queue)
    case_packets = build_anomaly_case_review_packets(queue)
    status_transitions = build_anomaly_review_status_transitions(case_packets)
    decision_readiness = build_anomaly_review_decision_readiness(
        status_transitions=status_transitions,
        review_decisions=review_decisions,
    )

    _write_csv(queue_path, queue)
    _write_csv(summary_path, summary)
    _write_csv(case_packets_csv_path, case_packets)
    _write_case_packets_json(case_packets_json_path, case_packets)
    _write_csv(status_transitions_csv_path, status_transitions)
    _write_status_transitions_json(status_transitions_json_path, status_transitions)
    _write_csv(decision_readiness_csv_path, decision_readiness)
    _write_decision_readiness_json(decision_readiness_json_path, decision_readiness)
    _write_dashboard(queue=queue, summary=summary, dashboard_path=dashboard_path)
    metadata = _metadata(
        queue=queue,
        summary=summary,
        case_packets=case_packets,
        status_transitions=status_transitions,
        review_report_path=review_report_path,
        alert_rows_path=alert_rows_path,
        detection_cases_path=detection_cases_path,
        materiality_context_path=materiality_context_path,
        risk_summary_path=risk_summary_path,
        review_updates_path=review_updates_path,
        review_updates=review_updates,
        review_decisions_path=review_decisions_path,
        review_decisions=review_decisions,
        queue_path=queue_path,
        summary_path=summary_path,
        dashboard_path=dashboard_path,
        case_packets_csv_path=case_packets_csv_path,
        case_packets_json_path=case_packets_json_path,
        status_transitions_csv_path=status_transitions_csv_path,
        status_transitions_json_path=status_transitions_json_path,
        decision_readiness_csv_path=decision_readiness_csv_path,
        decision_readiness_json_path=decision_readiness_json_path,
        decision_readiness=decision_readiness,
    )
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return MonitorAnomalyReviewQueueResult(
        queue_path=queue_path,
        summary_path=summary_path,
        metadata_path=metadata_path,
        dashboard_path=dashboard_path,
        case_packets_csv_path=case_packets_csv_path,
        case_packets_json_path=case_packets_json_path,
        status_transitions_csv_path=status_transitions_csv_path,
        status_transitions_json_path=status_transitions_json_path,
        decision_readiness_csv_path=decision_readiness_csv_path,
        decision_readiness_json_path=decision_readiness_json_path,
        queue_row_count=int(len(queue)),
        high_priority_count=_count(queue, "review_priority", "high"),
        case_packet_row_count=int(len(case_packets)),
        status_transition_row_count=int(len(status_transitions)),
        decision_readiness_row_count=int(len(decision_readiness)),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-report", type=Path, default=REVIEW_REPORT_OUTPUT)
    parser.add_argument("--alert-rows", type=Path, default=ROLLING_ALERT_ROWS_OUTPUT)
    parser.add_argument("--detection-cases", type=Path, default=BACKTEST_CASES_OUTPUT)
    parser.add_argument(
        "--materiality-context",
        type=Path,
        default=MATERIALITY_CONTEXT_OUTPUT,
    )
    parser.add_argument("--risk-summary", type=Path, default=RISK_SCORE_SUMMARY_OUTPUT)
    parser.add_argument("--review-updates", type=Path, default=REVIEW_UPDATES_INPUT)
    parser.add_argument("--review-decisions", type=Path, default=REVIEW_DECISIONS_INPUT)
    parser.add_argument("--queue-output", type=Path, default=QUEUE_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    parser.add_argument("--dashboard-output", type=Path, default=DASHBOARD_OUTPUT)
    parser.add_argument(
        "--case-packets-csv-output",
        type=Path,
        default=CASE_REVIEW_PACKETS_CSV_OUTPUT,
    )
    parser.add_argument(
        "--case-packets-json-output",
        type=Path,
        default=CASE_REVIEW_PACKETS_JSON_OUTPUT,
    )
    parser.add_argument(
        "--status-transitions-csv-output",
        type=Path,
        default=STATUS_TRANSITIONS_CSV_OUTPUT,
    )
    parser.add_argument(
        "--status-transitions-json-output",
        type=Path,
        default=STATUS_TRANSITIONS_JSON_OUTPUT,
    )
    parser.add_argument(
        "--decision-readiness-csv-output",
        type=Path,
        default=DECISION_READINESS_CSV_OUTPUT,
    )
    parser.add_argument(
        "--decision-readiness-json-output",
        type=Path,
        default=DECISION_READINESS_JSON_OUTPUT,
    )
    args = parser.parse_args(argv)

    try:
        result = generate_monitor_anomaly_review_queue(
            review_report_path=args.review_report,
            alert_rows_path=args.alert_rows,
            detection_cases_path=args.detection_cases,
            materiality_context_path=args.materiality_context,
            risk_summary_path=args.risk_summary,
            review_updates_path=args.review_updates,
            review_decisions_path=args.review_decisions,
            queue_path=args.queue_output,
            summary_path=args.summary_output,
            metadata_path=args.metadata_output,
            dashboard_path=args.dashboard_output,
            case_packets_csv_path=args.case_packets_csv_output,
            case_packets_json_path=args.case_packets_json_output,
            status_transitions_csv_path=args.status_transitions_csv_output,
            status_transitions_json_path=args.status_transitions_json_output,
            decision_readiness_csv_path=args.decision_readiness_csv_output,
            decision_readiness_json_path=args.decision_readiness_json_output,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _queue_row(
    *,
    item: Mapping[str, object],
    alert_group: pd.DataFrame,
    detection: Mapping[str, object],
    materiality: Mapping[str, object],
    risk: Mapping[str, object],
) -> dict[str, object]:
    families = _families(item, alert_group)
    metrics = _metrics(item, alert_group)
    event_status = _event_context_status(detection)
    reference_status = _reference_overlap_status(item, detection)
    priority, priority_basis = _priority(
        item=item,
        families=families,
        event_status=event_status,
        reference_status=reference_status,
    )
    return {
        "case_id": str(item["candidate_id"]),
        "timestamp_utc": str(item["timestamp_utc"]),
        "market_id": str(item["market_id"]),
        "market_slug": _market_slug(item),
        "question": str(item.get("question", "")),
        "review_priority": priority,
        "priority_basis": priority_basis,
        "trigger_family": ",".join(families),
        "market_move_context": _market_move_context(item, families, metrics),
        "wallet_flow_context": _wallet_flow_context(item, materiality),
        "concentration_context": _concentration_context(item, families),
        "event_context_status": event_status,
        "reference_overlap_status": reference_status,
        "review_label": _review_label(item, priority),
        "missing_evidence": _missing_evidence(item),
        "human_review_status": _review_status(item),
        "review_status_updated_at_utc": "",
        "review_note": "",
        "reviewer": "",
        "review_source_url": "",
        "event_source_url": "",
        "allowed_interpretation": _allowed_interpretation(),
        "blocked_claims": _blocked_claims(),
        "source_artifacts": _source_artifacts(item, detection, risk),
    }


def _case_review_packet(item: Mapping[str, object]) -> dict[str, object]:
    case_id = _text(item.get("case_id"))
    status = _text(item.get("human_review_status")) or "needs_human_review"
    source_context = _source_context(item)
    return {
        "case_id": case_id,
        "packet_id": f"case_review_packet_{case_id}",
        "market_slug": _text(item.get("market_slug")),
        "question": _text(item.get("question")),
        "review_priority": _text(item.get("review_priority")),
        "human_review_status": status,
        "source_check_status": _source_check_status(item),
        "source_context": source_context,
        "evidence_status": _evidence_status(item),
        "missing_evidence": _text(item.get("missing_evidence")),
        "next_review_step": _next_review_step(item),
        "allowed_interpretation": _text(item.get("allowed_interpretation")),
        "blocked_claims": _text(item.get("blocked_claims")),
        "future_mcp_access": (
            "contract_only_bounded_case_summary; max_rows=50; no_raw_sql; "
            "no_wallet_address_by_default; no_order_path"
        ),
        "future_agent_access": (
            "contract_only_after_llm_audit_log; interpretation_only; "
            "no_metric_calculation"
        ),
        "source_queue_artifact": "monitor_anomaly_review_queue.csv",
    }


def _status_transition_row(item: Mapping[str, object]) -> dict[str, object]:
    current_status = _text(item.get("human_review_status")) or "needs_human_review"
    allowed, blocked, requirements, thesis_allowed, thesis_gate, action = (
        _transition_policy(current_status)
    )
    return {
        "case_id": _text(item.get("case_id")),
        "packet_id": _text(item.get("packet_id")),
        "current_status": current_status,
        "allowed_next_statuses": ";".join(allowed),
        "blocked_next_statuses": ";".join(blocked),
        "transition_requirements": requirements,
        "thesis_use_allowed": thesis_allowed,
        "thesis_use_gate": thesis_gate,
        "reviewer_action_required": action,
        "source_packet_artifact": "monitor_anomaly_case_review_packets.csv",
        "allowed_interpretation": _text(item.get("allowed_interpretation")),
        "blocked_claims": _text(item.get("blocked_claims")),
    }


def _decision_readiness_row(
    *,
    transition: Mapping[str, object],
    decision: Mapping[str, object],
) -> dict[str, object]:
    target_status = _text(decision.get("target_status"))
    missing_fields = _missing_decision_fields(target_status, decision)
    allowed_next = _split_statuses(transition.get("allowed_next_statuses"))
    if not target_status:
        validation_status = "no_decision_recorded"
    elif target_status not in allowed_next:
        raise ValueError(
            "review decision target_status is not allowed for case_id "
            f"{_text(transition.get('case_id'))}: {target_status}"
        )
    elif missing_fields:
        raise ValueError(
            "review decision missing required fields for case_id "
            f"{_text(transition.get('case_id'))}: {missing_fields}"
        )
    else:
        validation_status = "ready_to_apply"

    return {
        "case_id": _text(transition.get("case_id")),
        "current_status": _text(transition.get("current_status")),
        "target_status": target_status,
        "decision_validation_status": validation_status,
        "allowed_next_statuses": _text(transition.get("allowed_next_statuses")),
        "missing_decision_fields": ";".join(missing_fields),
        "thesis_use_allowed_after_decision": _thesis_use_after_decision(target_status),
        "thesis_use_scope": _text(decision.get("thesis_use_scope")),
        "reviewer_action_required": _decision_reviewer_action(
            transition=transition,
            target_status=target_status,
            validation_status=validation_status,
        ),
        "decision_note": _text(decision.get("decision_note")),
        "limitations": _text(decision.get("limitations")),
        "source_decision_artifact": "monitor_anomaly_review_decisions.csv",
        "blocked_claims": _text(transition.get("blocked_claims")),
    }


def _missing_decision_fields(
    target_status: str,
    decision: Mapping[str, object],
) -> list[str]:
    if not target_status:
        return []
    required = ["decision_updated_at_utc", "reviewer", "decision_note"]
    if target_status == "reviewed_keep_candidate":
        required.extend(["limitations", "thesis_use_scope"])
    return [field for field in required if not _text(decision.get(field))]


def _thesis_use_after_decision(target_status: str) -> str:
    if target_status == "reviewed_keep_candidate":
        return "method_appendix_only"
    return "false"


def _decision_reviewer_action(
    *,
    transition: Mapping[str, object],
    target_status: str,
    validation_status: str,
) -> str:
    if validation_status == "no_decision_recorded":
        return _text(transition.get("reviewer_action_required"))
    if validation_status == "ready_to_apply" and target_status == "reviewed_keep_candidate":
        return (
            "Apply only as bounded reviewed-case context with limitations; "
            "do not state causality or private information."
        )
    if validation_status == "ready_to_apply" and target_status == "reviewed_false_context":
        return "Apply as false-context decision and keep excluded from anomaly evidence."
    if validation_status == "ready_to_apply" and target_status == "thesis_excluded":
        return "Apply as thesis exclusion and keep out of thesis-facing outputs."
    return "Resolve decision validation before applying any status update."


def _transition_policy(
    current_status: str,
) -> tuple[list[str], list[str], str, str, str, str]:
    if current_status == "needs_human_review":
        return (
            ["source_check_pending", "thesis_excluded"],
            ["reviewed_keep_candidate", "reviewed_false_context"],
            (
                "Record public market source URL, public event/context source URL, "
                "reviewer, timestamp, and review note before acceptance or "
                "false-context decisions."
            ),
            "false",
            "No thesis-facing use before source check and human review decision.",
            "Open source check or explicitly exclude the case.",
        )
    if current_status == "source_check_pending":
        return (
            ["reviewed_keep_candidate", "reviewed_false_context", "thesis_excluded"],
            ["needs_human_review"],
            (
                "Review source timestamps, market mapping, repeat-bucket evidence, "
                "materiality context, and missing-evidence fields before selecting "
                "a terminal review status."
            ),
            "false",
            (
                "Thesis-facing use remains blocked until a human reviewer marks "
                "reviewed_keep_candidate and documents remaining limitations."
            ),
            "Choose keep, false-context, or exclusion after evidence review.",
        )
    if current_status == "reviewed_keep_candidate":
        return (
            ["thesis_excluded", "reviewed_false_context"],
            ["needs_human_review", "source_check_pending"],
            (
                "Maintain source URLs, review note, method limits, and blocked "
                "claims; downgrade if later review finds false context or thesis "
                "exclusion criteria."
            ),
            "method_appendix_only",
            (
                "Allowed only as bounded reviewed-case context with explicit "
                "limitations; not as causal or private-information evidence."
            ),
            "Keep limitations attached or downgrade if evidence weakens.",
        )
    if current_status == "reviewed_false_context":
        return (
            ["thesis_excluded"],
            ["needs_human_review", "source_check_pending", "reviewed_keep_candidate"],
            (
                "Document why the case is false context and retain blocked claims; "
                "do not reuse as positive anomaly evidence."
            ),
            "false",
            "False-context cases are not thesis-facing anomaly evidence.",
            "Keep as rejected review example or exclude from thesis outputs.",
        )
    if current_status == "thesis_excluded":
        return (
            [],
            [
                "needs_human_review",
                "source_check_pending",
                "reviewed_keep_candidate",
                "reviewed_false_context",
            ],
            (
                "Case is excluded from thesis-facing outputs unless a new manual "
                "review decision is documented outside the automated transition."
            ),
            "false",
            "Excluded cases are not thesis-facing evidence.",
            "No further action unless a new documented review decision is made.",
        )
    return (
        [],
        sorted(ALLOWED_REVIEW_STATUSES),
        "Resolve invalid review status before any further review transition.",
        "false",
        "Invalid review status blocks thesis-facing use.",
        "Correct the curated status worksheet.",
    )


def _source_context(item: Mapping[str, object]) -> str:
    review_url = _text(item.get("review_source_url")) or "not_recorded"
    event_url = _text(item.get("event_source_url")) or "not_recorded"
    reviewer = _text(item.get("reviewer")) or "not_recorded"
    updated_at = _text(item.get("review_status_updated_at_utc")) or "not_recorded"
    note = _text(item.get("review_note")) or "not_recorded"
    return (
        f"review_source_url={review_url}; event_source_url={event_url}; "
        f"reviewer={reviewer}; updated_at_utc={updated_at}; review_note={note}"
    )


def _source_check_status(item: Mapping[str, object]) -> str:
    status = _text(item.get("human_review_status"))
    review_url = _text(item.get("review_source_url"))
    event_url = _text(item.get("event_source_url"))
    if status == "source_check_pending" and review_url and event_url:
        return "public_sources_recorded_pending_human_acceptance"
    if status == "source_check_pending":
        return "source_check_open_missing_public_source_url"
    if status == "needs_human_review":
        return "source_check_not_started"
    if status == "reviewed_keep_candidate":
        return "human_review_kept_candidate"
    if status == "reviewed_false_context":
        return "human_review_false_context"
    if status == "thesis_excluded":
        return "excluded_from_thesis_use"
    return "unknown_review_status"


def _evidence_status(item: Mapping[str, object]) -> str:
    status = _text(item.get("human_review_status"))
    event_context = _text(item.get("event_context_status"))
    reference_context = _text(item.get("reference_overlap_status"))
    missing = _text(item.get("missing_evidence"))
    if status in {"reviewed_false_context", "thesis_excluded"}:
        return "not_eligible_for_thesis_use"
    if status == "reviewed_keep_candidate" and not missing:
        return "human_reviewed_candidate_context_available"
    if status == "source_check_pending":
        return (
            "public_sources_recorded_but_evidence_incomplete; "
            f"event_context={event_context}; reference_context={reference_context}"
        )
    return (
        "human_review_required; "
        f"event_context={event_context or 'missing'}; "
        f"reference_context={reference_context or 'missing'}"
    )


def _next_review_step(item: Mapping[str, object]) -> str:
    status = _text(item.get("human_review_status"))
    if status == "needs_human_review":
        return (
            "Open public market and event/context sources; record source URLs; "
            "keep as review cue only."
        )
    if status == "source_check_pending":
        return (
            "Review source timestamps, repeat-bucket evidence, market mapping, "
            "materiality, and missing evidence; then mark reviewed_keep_candidate, "
            "reviewed_false_context, or thesis_excluded."
        )
    if status == "reviewed_keep_candidate":
        return (
            "Use only as bounded reviewed case context after method-limit review; "
            "do not state causality or private information."
        )
    if status == "reviewed_false_context":
        return "Keep as rejected review example; do not use as anomaly evidence."
    if status == "thesis_excluded":
        return "Keep excluded from thesis-facing outputs unless a new review decision is documented."
    return "Resolve invalid or unknown review status before any further use."


def _priority(
    *,
    item: Mapping[str, object],
    families: Sequence[str],
    event_status: str,
    reference_status: str,
) -> tuple[str, str]:
    existing = str(item.get("review_priority", "")).strip().lower()
    severity = str(item.get("max_severity", "")).strip().lower()
    percentile = _float(item.get("max_percentile_rank"))
    family_count = len([family for family in families if family])
    reasons = [
        f"source_priority={existing or 'missing'}",
        f"max_severity={severity or 'missing'}",
        f"max_percentile_rank={percentile:.3f}",
        f"family_count={family_count}",
        f"reference_overlap={reference_status}",
        f"event_context={event_status}",
    ]
    if existing == "high" or (
        severity in {"high", "critical"}
        and percentile >= 0.95
        and (family_count >= 2 or reference_status == "reference_hit")
    ):
        return "high", "; ".join(reasons)
    if (
        existing == "medium"
        or severity in {"watch", "high", "critical"}
        or percentile >= 0.90
        or family_count >= 2
        or reference_status in {"reference_hit", "partial_reference_overlap"}
        or event_status in {"reviewed_event_context", "pre_event_context"}
    ):
        return "medium", "; ".join(reasons)
    return "low", "; ".join(reasons)


def _review_label(item: Mapping[str, object], priority: str) -> str:
    source_label = str(item.get("insider_risk_review_label", "")).lower()
    if "insider-risk review candidate" in source_label:
        return "insider_risk_review_candidate"
    if "insider-risk watch cue" in source_label:
        return "insider_risk_watch_cue"
    if priority == "high":
        return "anomaly_review_candidate"
    return "anomaly_watch_cue"


def _event_context_status(detection: Mapping[str, object]) -> str:
    if not detection:
        return "not_evaluated"
    if _bool(detection.get("pre_event_hit")):
        return "pre_event_context"
    if _bool(detection.get("event_hit")):
        return "reviewed_event_context"
    if str(detection.get("nearest_event_id", "")).strip():
        return "nearest_event_only"
    return "no_reviewed_event_context"


def _reference_overlap_status(
    item: Mapping[str, object],
    detection: Mapping[str, object],
) -> str:
    score = max(
        _float(item.get("best_similarity_score")),
        _float(detection.get("best_similarity_score")),
    )
    if _bool(detection.get("reference_hit")) or score >= 0.75:
        return "reference_hit"
    if score > 0:
        return "partial_reference_overlap"
    return "no_reference_overlap"


def _market_move_context(
    item: Mapping[str, object],
    families: Sequence[str],
    metrics: Sequence[str],
) -> str:
    marker = (
        "market_move_anomaly_present"
        if "market_move" in families
        else "no_market_move_anomaly_in_candidate"
    )
    midpoint_min = _text(item.get("latest_midpoint_min"))
    midpoint_max = _text(item.get("latest_midpoint_max"))
    return (
        f"{marker}; midpoint_range={midpoint_min or 'missing'}-"
        f"{midpoint_max or 'missing'}; metrics={','.join(metrics) or 'none'}"
    )


def _wallet_flow_context(
    item: Mapping[str, object],
    materiality: Mapping[str, object],
) -> str:
    amount = _coalesce(item.get("total_observed_amount_usd"), materiality.get("total_observed_amount_usd"))
    active_wallets = _coalesce(item.get("active_wallets"), materiality.get("active_wallets"))
    trade_count = _coalesce(item.get("trade_count"), materiality.get("trade_count"))
    amount_per_wallet = _coalesce(item.get("amount_per_wallet"), materiality.get("amount_per_wallet"))
    materiality_label = _coalesce(item.get("materiality_label"), materiality.get("materiality_label"))
    return (
        f"total_observed_amount_usd={_format_number(amount)}; "
        f"active_wallets={_format_number(active_wallets)}; "
        f"trade_count={_format_number(trade_count)}; "
        f"amount_per_wallet_usd={_format_number(amount_per_wallet)}; "
        f"materiality={materiality_label or 'missing'}"
    )


def _concentration_context(
    item: Mapping[str, object],
    families: Sequence[str],
) -> str:
    triggered = "concentration" in families or "market_concentration" in str(
        item.get("triggered_patterns", "")
    )
    coordination = _text(item.get("coordination_label")) or "missing"
    return (
        f"concentration_context={'present' if triggered else 'not_triggered'}; "
        f"coordination_label={coordination}; "
        f"triggered_patterns={_text(item.get('triggered_patterns')) or 'none'}"
    )


def _missing_evidence(item: Mapping[str, object]) -> str:
    base = _text(item.get("missing_evidence"))
    if not base:
        return "manual source checks; repeat-bucket confirmation; event timestamp review"
    return base


def _review_status(item: Mapping[str, object]) -> str:
    status = _text(item.get("human_review_status")) or "needs_human_review"
    if status not in ALLOWED_REVIEW_STATUSES:
        return "needs_human_review"
    return status


def _allowed_interpretation() -> str:
    return (
        "Deterministic anomaly review cue for human source checking and later "
        "bounded SignalSpec drafting only; not a metric calculated by agents."
    )


def _blocked_claims() -> str:
    return (
        "private_information_proof; misconduct_finding; causality; "
        "tradeability; profitability; future_performance; order_instruction; "
        "insider_risk_as_fact"
    )


def _source_artifacts(
    item: Mapping[str, object],
    detection: Mapping[str, object],
    risk: Mapping[str, object],
) -> str:
    artifacts = [
        _text(item.get("source_artifacts")),
        "monitor_anomaly_review_queue.csv",
    ]
    if detection:
        artifacts.append("monitor_detection_backtest_cases.csv")
    if risk:
        artifacts.append("monitor_literature_risk_score_summary.csv")
    return ";".join(sorted({artifact for artifact in artifacts if artifact}))


def _families(item: Mapping[str, object], alert_group: pd.DataFrame) -> list[str]:
    source = _text(item.get("anomaly_families"))
    values = _split_csv(source)
    if not values and not alert_group.empty and "anomaly_family" in alert_group.columns:
        values = sorted(set(alert_group["anomaly_family"].astype(str)))
    return values


def _metrics(item: Mapping[str, object], alert_group: pd.DataFrame) -> list[str]:
    source = _text(item.get("metric_names"))
    values = _split_csv(source)
    if not values and not alert_group.empty and "metric_name" in alert_group.columns:
        values = sorted(set(alert_group["metric_name"].astype(str)))
    return values


def _market_slug(item: Mapping[str, object]) -> str:
    for key in ("subcategory", "market_slug", "market_id"):
        value = _text(item.get(key))
        if value:
            return value
    return ""


def _metadata(
    *,
    queue: pd.DataFrame,
    summary: pd.DataFrame,
    case_packets: pd.DataFrame,
    status_transitions: pd.DataFrame,
    decision_readiness: pd.DataFrame,
    review_report_path: Path,
    alert_rows_path: Path,
    detection_cases_path: Path,
    materiality_context_path: Path,
    risk_summary_path: Path,
    review_updates_path: Path,
    review_updates: pd.DataFrame,
    review_decisions_path: Path,
    review_decisions: pd.DataFrame,
    queue_path: Path,
    summary_path: Path,
    dashboard_path: Path,
    case_packets_csv_path: Path,
    case_packets_json_path: Path,
    status_transitions_csv_path: Path,
    status_transitions_json_path: Path,
    decision_readiness_csv_path: Path,
    decision_readiness_json_path: Path,
) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "monitor_anomaly_review_queue",
            "candidate_source": "bounded monitor candidate human-review report",
            "priority_uses_distribution_percentile_rank": True,
            "priority_uses_existing_monitor_severity": True,
            "fixed_usd_whale_threshold_used": False,
            "uses_existing_files_only": True,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "does_not_use_order_endpoints": True,
        },
        "inputs": {
            "review_report_path": str(review_report_path),
            "alert_rows_path": str(alert_rows_path),
            "detection_cases_path": str(detection_cases_path),
            "materiality_context_path": str(materiality_context_path),
            "risk_summary_path": str(risk_summary_path),
            "review_updates_path": str(review_updates_path),
            "review_decisions_path": str(review_decisions_path),
        },
        "outputs": {
            "queue_path": str(queue_path),
            "summary_path": str(summary_path),
            "dashboard_path": str(dashboard_path),
            "case_packets_csv_path": str(case_packets_csv_path),
            "case_packets_json_path": str(case_packets_json_path),
            "status_transitions_csv_path": str(status_transitions_csv_path),
            "status_transitions_json_path": str(status_transitions_json_path),
            "decision_readiness_csv_path": str(decision_readiness_csv_path),
            "decision_readiness_json_path": str(decision_readiness_json_path),
            "queue_row_count": int(len(queue)),
            "case_packet_row_count": int(len(case_packets)),
            "status_transition_row_count": int(len(status_transitions)),
            "decision_readiness_row_count": int(len(decision_readiness)),
            "high_priority_count": _count(queue, "review_priority", "high"),
            "review_update_row_count": int(len(review_updates)),
            "review_decision_row_count": int(len(review_decisions)),
            "contains_wallet_addresses": _contains_wallet_address_column(queue),
            "case_packets_contain_wallet_addresses": _contains_wallet_address_column(
                case_packets
            ),
            "status_transitions_contain_wallet_addresses": _contains_wallet_address_column(
                status_transitions
            ),
            "decision_readiness_contains_wallet_addresses": _contains_wallet_address_column(
                decision_readiness
            ),
            "contains_order_instructions": False,
            "case_packets_contain_order_instructions": False,
            "status_transitions_contain_order_instructions": False,
            "decision_readiness_contains_order_instructions": False,
            "max_default_rows_for_future_tools": MAX_MCP_ROWS,
        },
        "future_agent_contract": {
            "status": "contract_only_not_implemented",
            "roles": [
                "EventScoutAgent",
                "CaseNarrativeAgent",
                "SkepticReviewerAgent",
                "Orchestrator",
            ],
            "allowed_input": (
                "bounded anomaly review queue, summaries, case packets, and "
                "status transitions only"
            ),
            "agent_metric_calculation_allowed": False,
            "llm_audit_log_required": True,
        },
        "future_mcp_contract": {
            "status": "contract_only_not_implemented",
            "tools": [
                "get_anomaly_review_summary",
                "get_anomaly_case",
                "list_monitor_artifacts",
                "get_method_limits",
            ],
            "max_rows": MAX_MCP_ROWS,
            "raw_sql_allowed": False,
            "wallet_address_exposure_allowed_by_default": False,
            "order_or_trading_path_allowed": False,
            "llm_audit_log_required": True,
        },
        "limitations": {
            "human_review_required": True,
            "not_a_probability_model": True,
            "not_a_causal_test": True,
            "not_a_trade_or_profitability_signal": True,
            "not_a_misconduct_finding": True,
            "not_private_information_evidence": True,
            "agents_and_mcp_not_activated": True,
            "summary_row_count": int(len(summary)),
        },
    }


def _write_dashboard(
    *,
    queue: pd.DataFrame,
    summary: pd.DataFrame,
    dashboard_path: Path,
) -> None:
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    stats = summary.iloc[0].to_dict()
    body = "<p>No anomaly review candidates are currently queued.</p>"
    if not queue.empty:
        body = _queue_cards(queue)
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Monitor Anomaly Review Queue</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 28px; color: #17202a; }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, minmax(130px, 1fr)); gap: 12px; }}
    .metric {{ border: 1px solid #d7dde5; border-radius: 6px; padding: 12px; background: #f8fafc; }}
    .metric strong {{ display: block; font-size: 22px; margin-top: 4px; }}
    .case {{ border: 1px solid #cfd8e3; border-radius: 8px; padding: 16px; margin: 18px 0; background: #ffffff; }}
    .pill {{ display: inline-block; padding: 3px 8px; border-radius: 999px; background: #eef2f7; margin-right: 6px; font-size: 12px; }}
    .pill.high {{ background: #ffe7d6; }}
    .pill.medium {{ background: #fff7cc; }}
    .pill.low {{ background: #e9f7ef; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(240px, 1fr)); gap: 12px; }}
    .box {{ border: 1px solid #e1e7ef; border-radius: 6px; padding: 12px; background: #fbfcfe; }}
    .note {{ background: #fff7e6; border: 1px solid #f0d08a; padding: 12px; border-radius: 6px; }}
    code {{ background: #f1f5f9; padding: 2px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>Monitor Anomaly Review Queue</h1>
  <p class="note">Deterministic review queue over bounded monitor artifacts. Future agents and MCP may read summaries only after audit logging exists; they do not calculate metrics here.</p>
  <section class="metrics">
    <div class="metric">Queued cases<strong>{stats["queue_row_count"]}</strong></div>
    <div class="metric">High priority<strong>{stats["high_priority_count"]}</strong></div>
    <div class="metric">Medium priority<strong>{stats["medium_priority_count"]}</strong></div>
    <div class="metric">Low priority<strong>{stats["low_priority_count"]}</strong></div>
  </section>
  <h2>Review Cases</h2>
  {body}
  <h2>Method Limits</h2>
  <p>{escape(str(stats["limitation"]))}</p>
  <p>Future MCP default row cap: <code>{MAX_MCP_ROWS}</code>. Raw SQL, wallet-address exposure by default, order paths, and agent-computed metrics are out of scope.</p>
</body>
</html>
"""
    dashboard_path.write_text(html, encoding="utf-8")


def _queue_cards(queue: pd.DataFrame) -> str:
    priority_order = {"high": 0, "medium": 1, "low": 2}
    ordered = queue.assign(
        _priority_order=queue["review_priority"].map(priority_order).fillna(9)
    ).sort_values(["_priority_order", "timestamp_utc", "case_id"])
    cards: list[str] = []
    for item in ordered.drop(columns=["_priority_order"]).to_dict(orient="records"):
        priority = str(item["review_priority"])
        cards.append(
            f"""
  <article class="case">
    <h3>{escape(str(item["question"]))}</h3>
    <p>
      <span class="pill {escape(priority)}">priority: {escape(priority)}</span>
      <span class="pill">label: {escape(str(item["review_label"]))}</span>
      <span class="pill">status: {escape(str(item["human_review_status"]))}</span>
    </p>
    <section class="grid">
      <div class="box"><strong>Market move</strong><p>{escape(str(item["market_move_context"]))}</p></div>
      <div class="box"><strong>Wallet flow</strong><p>{escape(str(item["wallet_flow_context"]))}</p></div>
      <div class="box"><strong>Concentration</strong><p>{escape(str(item["concentration_context"]))}</p></div>
      <div class="box"><strong>Context checks</strong><p>Event: {escape(str(item["event_context_status"]))}<br>Reference: {escape(str(item["reference_overlap_status"]))}</p></div>
    </section>
    <p><strong>Missing evidence:</strong> {escape(str(item["missing_evidence"]))}</p>
    <p><strong>Manual review:</strong> reviewer {escape(str(item["reviewer"]) or "not assigned")}; source {escape(str(item["review_source_url"]) or "not recorded")}; note {escape(str(item["review_note"]) or "none")}</p>
    <p><strong>Blocked claims:</strong> {escape(str(item["blocked_claims"]))}</p>
    <p><strong>Case ID:</strong> <code>{escape(str(item["case_id"]))}</code></p>
  </article>
"""
        )
    return "\n".join(cards)


def _alert_lookup(alert_rows: pd.DataFrame) -> dict[str, pd.DataFrame]:
    if alert_rows.empty:
        return {}
    rows = alert_rows.copy()
    rows["case_id"] = [
        monitor_candidate_id(row["timestamp_utc"], row["market_id"])
        for row in rows.to_dict(orient="records")
    ]
    return {str(case_id): group.copy() for case_id, group in rows.groupby("case_id")}


def _lookup_by_candidate(frame: pd.DataFrame) -> dict[str, dict[str, object]]:
    if frame.empty or "candidate_id" not in frame.columns:
        return {}
    return {str(row["candidate_id"]): row for row in frame.to_dict(orient="records")}


def read_review_status_updates(path: Path = REVIEW_UPDATES_INPUT) -> pd.DataFrame:
    """Read optional curated human-review status updates."""

    if not path.exists():
        return pd.DataFrame(columns=REVIEW_UPDATE_COLUMNS)
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    if frame.empty:
        return pd.DataFrame(columns=REVIEW_UPDATE_COLUMNS)
    missing = [column for column in REVIEW_UPDATE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"review status updates missing required columns: {missing}")
    updates = frame.loc[:, list(REVIEW_UPDATE_COLUMNS)].copy()
    for column in REVIEW_UPDATE_COLUMNS:
        updates[column] = updates[column].fillna("").astype(str).str.strip()
    _reject_wallet_address_columns(updates, "review status updates")
    invalid = sorted(
        set(updates["human_review_status"].astype(str)) - ALLOWED_REVIEW_STATUSES
    )
    if invalid:
        raise ValueError(f"invalid human_review_status values: {invalid}")
    empty_case = updates["case_id"].astype(str).str.strip().eq("")
    if empty_case.any():
        raise ValueError("review status updates require case_id for every row")
    duplicated = updates["case_id"].duplicated()
    if duplicated.any():
        repeated = sorted(set(updates.loc[duplicated, "case_id"].astype(str)))
        raise ValueError(f"review status updates contain duplicate case_id values: {repeated}")
    return updates.reset_index(drop=True)


def read_review_decisions(path: Path = REVIEW_DECISIONS_INPUT) -> pd.DataFrame:
    """Read optional curated final review decisions."""

    if not path.exists():
        return pd.DataFrame(columns=REVIEW_DECISION_COLUMNS)
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    if frame.empty:
        return pd.DataFrame(columns=REVIEW_DECISION_COLUMNS)
    missing = [column for column in REVIEW_DECISION_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"review decisions missing required columns: {missing}")
    decisions = frame.loc[:, list(REVIEW_DECISION_COLUMNS)].copy()
    for column in REVIEW_DECISION_COLUMNS:
        decisions[column] = decisions[column].fillna("").astype(str).str.strip()
    _validate_review_decisions(decisions)
    return decisions.reset_index(drop=True)


def _validate_review_report(frame: pd.DataFrame) -> None:
    _require_columns(
        frame,
        (
            "candidate_id",
            "timestamp_utc",
            "market_id",
            "question",
            "anomaly_families",
            "max_severity",
            "max_percentile_rank",
            "review_priority",
            "missing_evidence",
        ),
        "human review report",
    )
    _reject_wallet_address_columns(frame, "human review report")


def _validate_alert_rows(frame: pd.DataFrame) -> None:
    missing = [column for column in MONITOR_ALERT_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"alert rows missing required columns: {missing}")
    _reject_wallet_address_columns(frame, "alert rows")


def _validate_queue(frame: pd.DataFrame) -> None:
    _require_columns(frame, QUEUE_COLUMNS, "anomaly review queue")
    _reject_wallet_address_columns(frame, "anomaly review queue")
    invalid = sorted(set(frame["human_review_status"].astype(str)) - ALLOWED_REVIEW_STATUSES)
    if invalid:
        raise ValueError(f"queue contains invalid human_review_status values: {invalid}")


def _validate_case_packets(frame: pd.DataFrame) -> None:
    _require_columns(frame, CASE_REVIEW_PACKET_COLUMNS, "case review packets")
    _reject_wallet_address_columns(frame, "case review packets")
    invalid = sorted(set(frame["human_review_status"].astype(str)) - ALLOWED_REVIEW_STATUSES)
    if invalid:
        raise ValueError(f"case packets contain invalid human_review_status values: {invalid}")


def _validate_status_transitions(frame: pd.DataFrame) -> None:
    _require_columns(frame, STATUS_TRANSITION_COLUMNS, "status transitions")
    _reject_wallet_address_columns(frame, "status transitions")
    invalid = sorted(set(frame["current_status"].astype(str)) - ALLOWED_REVIEW_STATUSES)
    if invalid:
        raise ValueError(f"status transitions contain invalid current_status values: {invalid}")


def _validate_review_decisions(frame: pd.DataFrame) -> None:
    _require_columns(frame, REVIEW_DECISION_COLUMNS, "review decisions")
    _reject_wallet_address_columns(frame, "review decisions")
    target_values = {value for value in frame["target_status"].astype(str) if value}
    allowed_targets = {
        "reviewed_keep_candidate",
        "reviewed_false_context",
        "thesis_excluded",
    }
    invalid = sorted(target_values - allowed_targets)
    if invalid:
        raise ValueError(f"review decisions contain invalid target_status values: {invalid}")
    empty_case = frame["case_id"].astype(str).str.strip().eq("")
    if empty_case.any():
        raise ValueError("review decisions require case_id for every row")
    duplicated = frame["case_id"].duplicated()
    if duplicated.any():
        repeated = sorted(set(frame.loc[duplicated, "case_id"].astype(str)))
        raise ValueError(f"review decisions contain duplicate case_id values: {repeated}")


def _reject_wallet_address_columns(frame: pd.DataFrame, label: str) -> None:
    forbidden = [column for column in frame.columns if "wallet_address" in column.lower()]
    if forbidden:
        raise ValueError(f"{label} must not contain wallet-address columns: {forbidden}")


def _contains_wallet_address_column(frame: pd.DataFrame) -> bool:
    return any("wallet_address" in column.lower() for column in frame.columns)


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def _read_csv_allow_empty(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"{label} file not found: {path}")
    return pd.read_csv(path, keep_default_na=False)


def _read_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, keep_default_na=False)


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _write_case_packets_json(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "artifact": "monitor_anomaly_case_review_packets",
        "row_count": int(len(frame)),
        "max_default_rows_for_future_tools": MAX_MCP_ROWS,
        "contains_wallet_addresses": _contains_wallet_address_column(frame),
        "contains_order_instructions": False,
        "agent_and_mcp_status": "contract_only_not_implemented",
        "case_packets": frame.to_dict(orient="records"),
    }
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_status_transitions_json(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "artifact": "monitor_anomaly_review_status_transitions",
        "row_count": int(len(frame)),
        "max_default_rows_for_future_tools": MAX_MCP_ROWS,
        "contains_wallet_addresses": _contains_wallet_address_column(frame),
        "contains_order_instructions": False,
        "agent_and_mcp_status": "contract_only_not_implemented",
        "status_transitions": frame.to_dict(orient="records"),
    }
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_decision_readiness_json(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "artifact": "monitor_anomaly_review_decision_readiness",
        "row_count": int(len(frame)),
        "max_default_rows_for_future_tools": MAX_MCP_ROWS,
        "contains_wallet_addresses": _contains_wallet_address_column(frame),
        "contains_order_instructions": False,
        "agent_and_mcp_status": "contract_only_not_implemented",
        "decision_readiness": frame.to_dict(orient="records"),
    }
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _count(frame: pd.DataFrame, column: str, value: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int((frame[column].astype(str) == value).sum())


def _counts_text(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return ""
    counts = frame[column].astype(str).value_counts().sort_index()
    return "; ".join(f"{key}={int(value)}" for key, value in counts.items())


def _split_csv(value: object) -> list[str]:
    text = _text(value)
    if not text:
        return []
    return sorted({part.strip() for part in text.split(",") if part.strip()})


def _split_statuses(value: object) -> list[str]:
    text = _text(value)
    if not text:
        return []
    return [part.strip() for part in text.split(";") if part.strip()]


def _coalesce(*values: object) -> object:
    for value in values:
        text = _text(value)
        if text:
            return value
    return ""


def _format_number(value: object) -> str:
    text = _text(value)
    if not text:
        return "missing"
    try:
        return f"{float(text):.4f}"
    except ValueError:
        return text


def _float(value: object) -> float:
    try:
        text = _text(value)
        if not text:
            return 0.0
        return float(text)
    except (TypeError, ValueError):
        return 0.0


def _bool(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _text(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


if __name__ == "__main__":
    raise SystemExit(main())
