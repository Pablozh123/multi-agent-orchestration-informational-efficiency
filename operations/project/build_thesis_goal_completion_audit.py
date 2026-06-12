"""Build a goal-completion and remaining-gates audit for thesis consolidation."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pandas as pd


DEFAULT_REPO_ROOT = Path(".")
DEFAULT_RESULTS_DIR = Path("data/results")
DEFAULT_DOCS_DIR = Path("docs/project")

AUDIT_OUTPUT = "thesis_goal_completion_audit.csv"
AUDIT_DOC_OUTPUT = "THESIS_GOAL_COMPLETION_AUDIT.md"

AUDIT_COLUMNS: tuple[str, ...] = (
    "audit_id",
    "goal_requirement_de",
    "current_status",
    "evidence_artifacts",
    "key_evidence_de",
    "remaining_gap_de",
    "next_action_de",
)


@dataclass(frozen=True)
class GoalCompletionAuditResult:
    """Generated audit paths and counts."""

    audit_path: Path
    docs_path: Path
    audit_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "audit_path": str(self.audit_path),
            "docs_path": str(self.docs_path),
            "audit_rows": self.audit_rows,
        }


def generate_goal_completion_audit(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> GoalCompletionAuditResult:
    """Generate the goal-completion audit CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    evidence_map = _read_csv(results_dir / "thesis_evidence_map.csv")
    curated_package = _read_csv(results_dir / "thesis_curated_result_package.csv")
    readiness = _read_csv(results_dir / "thesis_submission_readiness_board.csv")
    drafting = _read_csv(results_dir / "thesis_drafting_sequence.csv")
    source_access = _read_csv(results_dir / "thesis_source_access_audit.csv")
    source_structure = _read_csv(results_dir / "thesis_source_structure_inventory.csv")
    source_decisions = _read_csv(results_dir / "thesis_source_review_decision_packets.csv")
    h1_h2_h3_source_notes = _read_csv(results_dir / "thesis_h1_h2_h3_source_review_notes.csv")
    source_progress_ledger = _read_csv(results_dir / "thesis_source_review_progress_ledger.csv")
    manual_source_review_execution_pass = _read_csv(
        results_dir / "thesis_h1_h2_h3_manual_source_review_execution_pass.csv"
    )
    source_progress_protocol = _read_csv(results_dir / "thesis_source_review_progress_protocol.csv")
    source_chapter_handoff = _read_csv(results_dir / "thesis_source_review_chapter_handoff.csv")
    chapter_checklist = _read_csv(results_dir / "thesis_chapter_source_review_checklist.csv")
    h1_h2_h3_drafting_checklist = _read_csv(results_dir / "thesis_h1_h2_h3_drafting_checklist.csv")
    h1_h2_h3_bounded_chapter_draft = _read_csv(
        results_dir / "thesis_h1_h2_h3_bounded_chapter_draft.csv"
    )
    h1_h2_h3_source_gated_writing_pass = _read_csv(
        results_dir / "thesis_h1_h2_h3_source_gated_writing_pass.csv"
    )
    method_traceability = _read_csv(results_dir / "thesis_method_interpretation_traceability.csv")
    result_package_traceability = _read_csv(results_dir / "thesis_result_package_traceability.csv")
    source_coverage = _read_csv(results_dir / "thesis_method_interpretation_source_coverage.csv")
    core_sections = _read_csv(results_dir / "thesis_h1_h2_h3_core_sections.csv")
    agent_control = _read_csv(results_dir / "thesis_agent_pipeline_control_audit.csv")
    agent_upgrade = _read_csv(results_dir / "thesis_agent_pipeline_upgrade_plan.csv")
    final_gate_board = _read_csv(results_dir / "thesis_final_gate_board.csv")
    handoff_package = _read_csv(results_dir / "thesis_advisor_handoff_package.csv")
    handoff_note = _read_csv(results_dir / "thesis_advisor_handoff_note.csv")
    feedback_log = _read_csv(results_dir / "thesis_advisor_feedback_log_template.csv")

    audit = build_goal_completion_audit(
        evidence_map=evidence_map,
        curated_package=curated_package,
        readiness=readiness,
        drafting=drafting,
        source_access=source_access,
        source_structure=source_structure,
        source_decisions=source_decisions,
        h1_h2_h3_source_notes=h1_h2_h3_source_notes,
        source_progress_ledger=source_progress_ledger,
        manual_source_review_execution_pass=manual_source_review_execution_pass,
        source_progress_protocol=source_progress_protocol,
        source_chapter_handoff=source_chapter_handoff,
        chapter_checklist=chapter_checklist,
        h1_h2_h3_drafting_checklist=h1_h2_h3_drafting_checklist,
        h1_h2_h3_bounded_chapter_draft=h1_h2_h3_bounded_chapter_draft,
        h1_h2_h3_source_gated_writing_pass=h1_h2_h3_source_gated_writing_pass,
        method_traceability=method_traceability,
        result_package_traceability=result_package_traceability,
        source_coverage=source_coverage,
        core_sections=core_sections,
        agent_control=agent_control,
        agent_upgrade=agent_upgrade,
        final_gate_board=final_gate_board,
        handoff_package=handoff_package,
        handoff_note=handoff_note,
        feedback_log=feedback_log,
    )
    _validate_audit(audit, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    audit_path = results_dir / AUDIT_OUTPUT
    docs_path = docs_dir / AUDIT_DOC_OUTPUT
    audit.to_csv(audit_path, index=False)
    docs_path.write_text(_render_audit_doc(audit), encoding="utf-8")

    return GoalCompletionAuditResult(
        audit_path=audit_path,
        docs_path=docs_path,
        audit_rows=len(audit),
    )


def build_goal_completion_audit(
    *,
    evidence_map: pd.DataFrame,
    curated_package: pd.DataFrame,
    readiness: pd.DataFrame,
    drafting: pd.DataFrame,
    source_access: pd.DataFrame,
    source_structure: pd.DataFrame,
    source_decisions: pd.DataFrame,
    h1_h2_h3_source_notes: pd.DataFrame,
    source_progress_ledger: pd.DataFrame,
    manual_source_review_execution_pass: pd.DataFrame,
    source_progress_protocol: pd.DataFrame,
    source_chapter_handoff: pd.DataFrame,
    chapter_checklist: pd.DataFrame,
    h1_h2_h3_drafting_checklist: pd.DataFrame,
    h1_h2_h3_bounded_chapter_draft: pd.DataFrame,
    h1_h2_h3_source_gated_writing_pass: pd.DataFrame,
    method_traceability: pd.DataFrame,
    result_package_traceability: pd.DataFrame,
    source_coverage: pd.DataFrame,
    core_sections: pd.DataFrame,
    agent_control: pd.DataFrame,
    agent_upgrade: pd.DataFrame,
    final_gate_board: pd.DataFrame,
    handoff_package: pd.DataFrame,
    handoff_note: pd.DataFrame,
    feedback_log: pd.DataFrame,
) -> pd.DataFrame:
    """Return a bounded audit of current goal evidence and remaining gates."""

    _require_columns(
        evidence_map,
        ("item_type", "thesis_readiness", "primary_artifact", "literature_sources"),
        "evidence map",
    )
    _require_columns(
        curated_package,
        ("package_type", "include_in_core_package", "thesis_readiness"),
        "curated package",
    )
    _require_columns(readiness, ("gate_area", "current_status"), "submission readiness")
    _require_columns(drafting, ("draft_permission", "sequence_id"), "drafting sequence")
    _require_columns(
        source_access,
        ("source_id", "priority_band", "local_file_exists", "access_route"),
        "source access audit",
    )
    _require_columns(
        source_structure,
        ("source_id", "structure_inventory_status"),
        "source structure inventory",
    )
    _require_columns(
        source_decisions,
        ("decision_packet_id", "final_citation_gate", "reviewer_decision"),
        "source review decision packets",
    )
    _require_columns(
        h1_h2_h3_source_notes,
        ("note_id", "thesis_area", "note_status", "selected_table", "selected_figure"),
        "H1-H2-H3 source review notes",
    )
    _require_columns(
        source_progress_ledger,
        (
            "ledger_id",
            "thesis_area",
            "review_progress_state",
            "final_citation_ready",
            "source_status_change_allowed",
        ),
        "source review progress ledger",
    )
    _require_columns(
        manual_source_review_execution_pass,
        (
            "execution_id",
            "thesis_area",
            "source_id",
            "evidence_id",
            "source_known_in_literature_index",
            "primary_artifact_exists",
            "coverage_status",
            "source_status_change_allowed",
            "final_citation_ready",
            "ready_for_bounded_draft",
        ),
        "manual source review execution pass",
    )
    _require_columns(
        source_progress_protocol,
        ("protocol_id", "protocol_area", "current_state", "deterministic_evidence_de"),
        "source review progress protocol",
    )
    _require_columns(
        source_chapter_handoff,
        (
            "handoff_id",
            "thesis_area",
            "coverage_status",
            "source_review_rows",
            "pending_review_rows",
            "final_citation_ready_rows",
            "result_package_items",
        ),
        "source review chapter handoff",
    )
    _require_columns(
        chapter_checklist,
        (
            "checklist_id",
            "thesis_area",
            "check_area",
            "completion_status",
            "ready_for_bounded_draft",
            "ready_for_final_submission",
        ),
        "chapter source review checklist",
    )
    _require_columns(
        h1_h2_h3_drafting_checklist,
        (
            "draft_check_id",
            "thesis_area",
            "draft_step",
            "completion_status",
            "ready_for_bounded_draft",
            "ready_for_final_submission",
        ),
        "H1-H2-H3 drafting checklist",
    )
    _require_columns(
        h1_h2_h3_bounded_chapter_draft,
        (
            "chapter_draft_id",
            "thesis_area",
            "draft_step",
            "method_evidence_ids",
            "interpretation_evidence_ids",
            "literature_source_ids",
            "deterministic_artifacts",
            "selected_tables",
            "selected_figures",
            "ready_for_bounded_draft",
            "ready_for_final_submission",
        ),
        "H1-H2-H3 bounded chapter draft",
    )
    _require_columns(
        h1_h2_h3_source_gated_writing_pass,
        (
            "writing_pass_id",
            "thesis_area",
            "source_coverage_links",
            "source_coverage_gap_rows",
            "writing_pass_status",
            "ready_for_bounded_draft",
            "ready_for_final_submission",
        ),
        "H1-H2-H3 source-gated writing pass",
    )
    _require_columns(
        method_traceability,
        ("item_type", "thesis_readiness", "traceability_status"),
        "method interpretation traceability",
    )
    _require_columns(
        result_package_traceability,
        ("package_type", "include_in_core_package", "package_traceability_status"),
        "result package traceability",
    )
    _require_columns(
        source_coverage,
        (
            "thesis_area",
            "thesis_readiness",
            "source_id",
            "coverage_status",
            "source_known_in_literature_index",
            "primary_artifact_exists",
        ),
        "method interpretation source coverage",
    )
    _require_columns(
        core_sections,
        (
            "hypothesis",
            "method_evidence_ids",
            "interpretation_evidence_ids",
            "literature_source_ids",
            "deterministic_artifacts",
            "selected_tables",
            "selected_figures",
        ),
        "H1-H2-H3 core sections",
    )
    _require_columns(
        agent_control,
        ("control_id", "current_activation_state"),
        "agent pipeline control audit",
    )
    _require_columns(
        agent_upgrade,
        ("upgrade_id", "current_status"),
        "agent pipeline upgrade plan",
    )
    _require_columns(
        final_gate_board,
        (
            "final_gate_id",
            "draft_use_allowed",
            "final_submission_ready",
            "blocking_count",
        ),
        "thesis final gate board",
    )
    _require_columns(handoff_package, ("deliverable_id", "path"), "handoff package")
    _require_columns(handoff_note, ("section_id",), "handoff note")
    _require_columns(feedback_log, ("feedback_id", "advisor_feedback_status"), "feedback log")

    thesis_facing = evidence_map[evidence_map["thesis_readiness"] == "thesis_facing_ready"]
    method_rows = int((thesis_facing["item_type"] == "method").sum())
    interpretation_rows = int((thesis_facing["item_type"] == "interpretation").sum())
    artifact_rows = int(thesis_facing["primary_artifact"].astype(str).str.len().gt(0).sum())
    source_rows = int(thesis_facing["literature_sources"].astype(str).str.len().gt(0).sum())
    core_package = curated_package[curated_package["include_in_core_package"].astype(bool)]
    core_tables = int((core_package["package_type"] == "table").sum())
    core_figures = int((core_package["package_type"] == "figure").sum())
    final_blocked = int(
        readiness["current_status"].astype(str).str.startswith("final_blocked").sum()
    )
    write_now = int((drafting["draft_permission"] == "write_now_bounded").sum())
    future_only = int((drafting["draft_permission"] == "future_work_only").sum())
    feedback_pending = int(
        (feedback_log["advisor_feedback_status"] == "pending_advisor_feedback").sum()
    )
    priority_1_access = source_access[
        source_access["priority_band"] == "priority_1_method_foundation_review"
    ]
    local_access = int(priority_1_access["local_file_exists"].astype(bool).sum())
    external_access = int(
        (priority_1_access["access_route"] == "external_locator_review").sum()
    )
    local_pdf_structures = int(
        (source_structure["structure_inventory_status"] == "local_pdf_structure_available").sum()
    )
    local_html_structures = int(
        (source_structure["structure_inventory_status"] == "local_html_structure_available").sum()
    )
    external_only_structures = int(
        (source_structure["structure_inventory_status"] == "external_only").sum()
    )
    decision_packets = int(len(source_decisions))
    full_review_decisions = int(
        (source_decisions["final_citation_gate"] == "full_source_review_required_before_final_citation").sum()
    )
    metadata_only_decisions = int(
        (source_decisions["final_citation_gate"] == "metadata_and_relevance_review_before_future_work_use").sum()
    )
    pending_decisions = int((source_decisions["reviewer_decision"] == "pending").sum())
    h1_h2_h3_note_rows = int(len(h1_h2_h3_source_notes))
    h1_h2_h3_note_pending = int(
        (h1_h2_h3_source_notes["note_status"] == "pending_manual_source_review").sum()
    )
    h1_h2_h3_note_area_counts = h1_h2_h3_source_notes["thesis_area"].value_counts().to_dict()
    ledger_rows = int(len(source_progress_ledger))
    ledger_pending = int(
        (source_progress_ledger["review_progress_state"] == "pending_manual_review").sum()
    )
    ledger_final_ready = int(source_progress_ledger["final_citation_ready"].astype(bool).sum())
    ledger_status_change_allowed = int(
        source_progress_ledger["source_status_change_allowed"].astype(bool).sum()
    )
    manual_execution_rows = int(len(manual_source_review_execution_pass))
    manual_execution_area_counts = manual_source_review_execution_pass["thesis_area"].value_counts().to_dict()
    manual_execution_unique_sources = int(manual_source_review_execution_pass["source_id"].nunique())
    manual_execution_final_ready = int(
        manual_source_review_execution_pass["final_citation_ready"].astype(bool).sum()
    )
    manual_execution_status_change_allowed = int(
        manual_source_review_execution_pass["source_status_change_allowed"].astype(bool).sum()
    )
    manual_execution_draft_ready = int(
        manual_source_review_execution_pass["ready_for_bounded_draft"].astype(bool).sum()
    )
    manual_execution_coverage_gaps = int(
        manual_source_review_execution_pass["coverage_status"].astype(str).str.contains(
            "gap", case=False
        ).sum()
    )
    manual_execution_unknown_sources = int(
        (~manual_source_review_execution_pass["source_known_in_literature_index"].astype(bool)).sum()
    )
    manual_execution_missing_artifacts = int(
        (~manual_source_review_execution_pass["primary_artifact_exists"].astype(bool)).sum()
    )
    protocol_rows = int(len(source_progress_protocol))
    protocol_areas = int(source_progress_protocol["protocol_area"].nunique())
    traceable_thesis_facing = method_traceability[
        method_traceability["thesis_readiness"] == "thesis_facing_ready"
    ]
    traceable_methods = int((traceable_thesis_facing["item_type"] == "method").sum())
    traceable_interpretations = int(
        (traceable_thesis_facing["item_type"] == "interpretation").sum()
    )
    traceability_gap_count = int(
        (method_traceability["traceability_status"] == "traceability_gap").sum()
    )
    source_coverage_thesis_facing = source_coverage[
        source_coverage["thesis_readiness"] == "thesis_facing_ready"
    ]
    source_coverage_rows = int(len(source_coverage))
    source_coverage_thesis_rows = int(len(source_coverage_thesis_facing))
    source_coverage_unique_sources = int(source_coverage["source_id"].nunique())
    source_coverage_gaps = int((source_coverage["coverage_status"] == "coverage_gap").sum())
    source_coverage_area_counts = (
        source_coverage_thesis_facing["thesis_area"].value_counts().to_dict()
    )
    package_gap_count = int(
        (result_package_traceability["package_traceability_status"] == "package_traceability_gap").sum()
    )
    traceable_core_package = result_package_traceability[
        result_package_traceability["include_in_core_package"].astype(bool)
    ]
    traceable_core_tables = int((traceable_core_package["package_type"] == "table").sum())
    traceable_core_figures = int((traceable_core_package["package_type"] == "figure").sum())
    core_section_rows = int(len(core_sections))
    core_section_hypotheses = "; ".join(core_sections["hypothesis"].astype(str).tolist())
    chapter_handoff_rows = int(len(source_chapter_handoff))
    chapter_handoff_review_rows = int(source_chapter_handoff["source_review_rows"].astype(int).sum())
    chapter_handoff_pending = int(source_chapter_handoff["pending_review_rows"].astype(int).sum())
    chapter_handoff_final_ready = int(
        source_chapter_handoff["final_citation_ready_rows"].astype(int).sum()
    )
    chapter_handoff_covered = int(
        (source_chapter_handoff["coverage_status"] == "covered_artifact_source_package_ready").sum()
    )
    chapter_checklist_rows = int(len(chapter_checklist))
    chapter_checklist_draft_ready = int(
        chapter_checklist["ready_for_bounded_draft"].astype(bool).sum()
    )
    chapter_checklist_final_ready = int(
        chapter_checklist["ready_for_final_submission"].astype(bool).sum()
    )
    chapter_checklist_final_blocked = int(
        chapter_checklist["completion_status"].astype(str).str.startswith("final_blocked").sum()
    )
    h1_h2_h3_drafting_rows = int(len(h1_h2_h3_drafting_checklist))
    h1_h2_h3_drafting_draft_ready = int(
        h1_h2_h3_drafting_checklist["ready_for_bounded_draft"].astype(bool).sum()
    )
    h1_h2_h3_drafting_final_ready = int(
        h1_h2_h3_drafting_checklist["ready_for_final_submission"].astype(bool).sum()
    )
    h1_h2_h3_drafting_final_blocked = int(
        h1_h2_h3_drafting_checklist["completion_status"]
        .astype(str)
        .str.startswith("final_blocked")
        .sum()
    )
    h1_h2_h3_bounded_draft_rows = int(len(h1_h2_h3_bounded_chapter_draft))
    h1_h2_h3_bounded_draft_ready = int(
        h1_h2_h3_bounded_chapter_draft["ready_for_bounded_draft"].astype(bool).sum()
    )
    h1_h2_h3_bounded_draft_final_ready = int(
        h1_h2_h3_bounded_chapter_draft["ready_for_final_submission"].astype(bool).sum()
    )
    h1_h2_h3_bounded_draft_areas = "; ".join(
        sorted(h1_h2_h3_bounded_chapter_draft["thesis_area"].astype(str).unique().tolist())
    )
    source_gated_writing_rows = int(len(h1_h2_h3_source_gated_writing_pass))
    source_gated_writing_draft_ready = int(
        h1_h2_h3_source_gated_writing_pass["ready_for_bounded_draft"].astype(bool).sum()
    )
    source_gated_writing_final_ready = int(
        h1_h2_h3_source_gated_writing_pass["ready_for_final_submission"].astype(bool).sum()
    )
    source_gated_writing_coverage_gaps = int(
        h1_h2_h3_source_gated_writing_pass["source_coverage_gap_rows"].astype(int).sum()
    )
    agent_control_rows = int(len(agent_control))
    agent_documentation_only = int(
        (agent_control["current_activation_state"] == "future_documentation_only").sum()
    )
    agent_deferred = int((agent_control["current_activation_state"] == "future_deferred").sum())
    agent_active = int(agent_control["current_activation_state"].astype(str).str.contains("active").sum())
    agent_upgrade_rows = int(len(agent_upgrade))
    agent_upgrade_active = int(agent_upgrade["current_status"].astype(str).str.contains("active").sum())
    final_gate_rows = int(len(final_gate_board))
    final_gate_draft_allowed = int(final_gate_board["draft_use_allowed"].astype(bool).sum())
    final_gate_ready = int(final_gate_board["final_submission_ready"].astype(bool).sum())
    final_gate_not_ready = int((~final_gate_board["final_submission_ready"].astype(bool)).sum())
    final_gate_blocking_count = int(final_gate_board["blocking_count"].astype(int).sum())

    rows = [
        _audit_row(
            audit_id="goal_audit_01_active_goal",
            goal_requirement_de="Genau ein aktives Konsolidierungsziel bleibt fuehrend.",
            current_status="proved_current_artifact",
            evidence_artifacts="GOAL.md",
            key_evidence_de="GOAL.md fuehrt goal-thesis-consolidation-001 als einziges aktives Ziel.",
            remaining_gap_de="Kein fachlicher Gap; Ziel bleibt aktiv, weil finale Gates offen sind.",
            next_action_de="Weiter nur im Phase-12-Scope arbeiten.",
        ),
        _audit_row(
            audit_id="goal_audit_02_evidence_map",
            goal_requirement_de="Methoden und Interpretationen sind auf Artefakte und Quellen gemappt.",
            current_status="draft_ready_final_source_review_pending",
            evidence_artifacts="data/results/thesis_evidence_map.csv; data/results/thesis_citation_readiness.csv; data/results/thesis_source_access_audit.csv; data/results/thesis_source_structure_inventory.csv; data/results/thesis_source_review_decision_packets.csv; data/results/thesis_h1_h2_h3_source_review_notes.csv; docs/project/THESIS_H1_H2_H3_SOURCE_REVIEW_NOTES.md; data/results/thesis_source_review_progress_ledger.csv; docs/project/THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md; data/results/thesis_h1_h2_h3_manual_source_review_execution_pass.csv; docs/project/THESIS_H1_H2_H3_MANUAL_SOURCE_REVIEW_EXECUTION_PASS.md; data/results/thesis_source_review_progress_protocol.csv; docs/project/THESIS_SOURCE_REVIEW_PROGRESS_PROTOCOL.md; data/results/thesis_method_interpretation_traceability.csv; data/results/thesis_method_interpretation_source_coverage.csv; docs/project/THESIS_METHOD_INTERPRETATION_SOURCE_COVERAGE.md",
            key_evidence_de=(
                f"Thesis-facing Evidence: {len(thesis_facing)} Zeilen; "
                f"Methoden: {method_rows}; Interpretationen: {interpretation_rows}; "
                f"Artefaktverweise: {artifact_rows}; Quellenverweise: {source_rows}. "
                f"Priority-1 Source Access: {len(priority_1_access)} Quellen; "
                f"lokal verfuegbar: {local_access}; extern zu pruefen: {external_access}. "
                f"Source Structure: {local_pdf_structures} PDF, {local_html_structures} HTML, "
                f"{external_only_structures} external-only Zeilen. "
                f"Source Decisions: {decision_packets} Pakete; Full Review: {full_review_decisions}; "
                f"Metadata-only: {metadata_only_decisions}; pending: {pending_decisions}. "
                f"H1-H2-H3 Source Notes: {h1_h2_h3_note_rows} Zeilen; "
                f"H1: {int(h1_h2_h3_note_area_counts.get('H1', 0))}; "
                f"H2: {int(h1_h2_h3_note_area_counts.get('H2', 0))}; "
                f"H3: {int(h1_h2_h3_note_area_counts.get('H3', 0))}; "
                f"pending: {h1_h2_h3_note_pending}. "
                f"Source Progress Ledger: {ledger_rows} Zeilen; pending: {ledger_pending}; "
                f"final-ready: {ledger_final_ready}; "
                f"source-status changes erlaubt: {ledger_status_change_allowed}. "
                f"Manual Execution Pass: {manual_execution_rows} Zeilen; "
                f"H1: {int(manual_execution_area_counts.get('H1', 0))}; "
                f"H2: {int(manual_execution_area_counts.get('H2', 0))}; "
                f"H3: {int(manual_execution_area_counts.get('H3', 0))}; "
                f"unique sources: {manual_execution_unique_sources}; "
                f"bounded-draft-ready: {manual_execution_draft_ready}; "
                f"final-ready: {manual_execution_final_ready}; "
                f"source-status changes erlaubt: {manual_execution_status_change_allowed}; "
                f"coverage gaps: {manual_execution_coverage_gaps}; "
                f"unknown sources: {manual_execution_unknown_sources}; "
                f"missing artifacts: {manual_execution_missing_artifacts}. "
                f"Source Progress Protocol: {protocol_rows} Zeilen in {protocol_areas} Bereichen. "
                f"Traceability: {traceable_methods} Methoden, {traceable_interpretations} Interpretationen, "
                f"{traceability_gap_count} Gaps. "
                f"Source Coverage: {source_coverage_rows} Links; thesis-facing: "
                f"{source_coverage_thesis_rows}; unique sources: {source_coverage_unique_sources}; "
                f"H1: {int(source_coverage_area_counts.get('H1', 0))}; "
                f"H2: {int(source_coverage_area_counts.get('H2', 0))}; "
                f"H3: {int(source_coverage_area_counts.get('H3', 0))}; "
                f"coverage gaps: {source_coverage_gaps}."
            ),
            remaining_gap_de="Finale Zitationsreife bleibt vom manuellen Source Review abhaengig.",
            next_action_de="Priority-1-Quellen mit Seiten- oder Abschnittsnotizen pruefen.",
        ),
        _audit_row(
            audit_id="goal_audit_03_curated_package",
            goal_requirement_de="Ergebnisdarstellung nutzt wenige starke Tabellen und Figuren.",
            current_status="proved_current_artifact",
            evidence_artifacts="data/results/thesis_curated_result_package.csv; data/results/thesis_table_figure_captions.csv; data/results/thesis_result_package_traceability.csv; data/results/thesis_h1_h2_h3_core_sections.csv; docs/research/THESIS_H1_H2_H3_CORE_SECTIONS.md; data/results/thesis_source_review_chapter_handoff.csv; docs/project/THESIS_SOURCE_REVIEW_CHAPTER_HANDOFF.md; data/results/thesis_chapter_source_review_checklist.csv; docs/project/THESIS_CHAPTER_SOURCE_REVIEW_CHECKLIST.md; data/results/thesis_h1_h2_h3_drafting_checklist.csv; docs/project/THESIS_H1_H2_H3_DRAFTING_CHECKLIST.md; data/results/thesis_h1_h2_h3_bounded_chapter_draft.csv; docs/research/THESIS_H1_H2_H3_BOUNDED_CHAPTER_DRAFT.md; data/results/thesis_h1_h2_h3_source_gated_writing_pass.csv; docs/research/THESIS_H1_H2_H3_SOURCE_GATED_WRITING_PASS.md; docs/research/THESIS_CHAPTER_DRAFT.md",
            key_evidence_de=(
                f"Kernpaket: {core_tables} Tabellen und {core_figures} Figuren. "
                f"Traceability-Kernpaket: {traceable_core_tables} Tabellen, "
                f"{traceable_core_figures} Figuren, {package_gap_count} Gaps. "
                f"H1-H2-H3 Core Sections: {core_section_rows} Zeilen "
                f"({core_section_hypotheses}) mit Methode, Interpretation, "
                "Quellen, Artefakten, Tabellen und Figuren. "
                f"Chapter Handoff: {chapter_handoff_rows} Kapitel; "
                f"coverage-ready: {chapter_handoff_covered}; review rows: "
                f"{chapter_handoff_review_rows}; pending: {chapter_handoff_pending}; "
                f"final-ready: {chapter_handoff_final_ready}. "
                f"Chapter Checklist: {chapter_checklist_rows} Checks; "
                f"bounded-draft-ready: {chapter_checklist_draft_ready}; "
                f"final-ready: {chapter_checklist_final_ready}; "
                f"final-blocked: {chapter_checklist_final_blocked}. "
                f"H1-H2-H3 Drafting Checklist: {h1_h2_h3_drafting_rows} Checks; "
                f"bounded-draft-ready: {h1_h2_h3_drafting_draft_ready}; "
                f"final-ready: {h1_h2_h3_drafting_final_ready}; "
                f"final-blocked: {h1_h2_h3_drafting_final_blocked}. "
                f"H1-H2-H3 Bounded Chapter Draft: {h1_h2_h3_bounded_draft_rows} "
                f"Bausteine ({h1_h2_h3_bounded_draft_areas}); bounded-draft-ready: "
                f"{h1_h2_h3_bounded_draft_ready}; final-ready: "
                f"{h1_h2_h3_bounded_draft_final_ready}. "
                f"Source-gated Writing Pass: {source_gated_writing_rows} Kapitel; "
                f"bounded-draft-ready: {source_gated_writing_draft_ready}; "
                f"final-ready: {source_gated_writing_final_ready}; "
                f"coverage gaps: {source_gated_writing_coverage_gaps}. "
                "Main Chapter Draft: Source-Gated Integration fuer H1, H2 und H3 "
                "ist im BA-Draft sichtbar."
            ),
            remaining_gap_de="Finale Nummerierung, Layout und finale Zitation folgen erst nach Source Review.",
            next_action_de="H1-H3 Kapitel gegen Source Review, Wording Guard und finale Tabellen-/Figurenplatzierung pruefen.",
        ),
        _audit_row(
            audit_id="goal_audit_04_readiness_labels",
            goal_requirement_de="Outputs sind thesis-facing, descriptive, blocked oder future-only markiert.",
            current_status="proved_current_artifact",
            evidence_artifacts="data/results/thesis_submission_readiness_board.csv; data/results/thesis_drafting_sequence.csv",
            key_evidence_de=(
                f"Readiness Gates: {len(readiness)}; final blockiert: {final_blocked}; "
                f"write-now Schritte: {write_now}; future-only Schritte: {future_only}."
            ),
            remaining_gap_de="Final blockierte Gates muessen sichtbar bleiben.",
            next_action_de="Draft schreiben, aber Source Review, Swiss-Gate und Render-QA nicht ueberspringen.",
        ),
        _audit_row(
            audit_id="goal_audit_05_h1_h2_h3_boundaries",
            goal_requirement_de="H1-H2-H3 Interpretationen bleiben an deterministische Outputs gebunden.",
            current_status="proved_current_artifact",
            evidence_artifacts="data/results/thesis_core_results_table.csv; docs/research/THESIS_WORDING_GUARD.md",
            key_evidence_de="Wording Guard blockiert Universal-, Intraday-, Kausalitaets-, Private-Information- und Profitabilitaetsclaims.",
            remaining_gap_de="Finale Formulierungen muessen beim Schreiben gegen den Wording Guard geprueft werden.",
            next_action_de="H1-H3 Kapitel mit Evidence IDs und Limitationen schreiben.",
        ),
        _audit_row(
            audit_id="goal_audit_06_swiss_gate",
            goal_requirement_de="Swiss Referendum bleibt bis zum offiziellen Resultat beschreibend.",
            current_status="final_blocked_official_result",
            evidence_artifacts="data/results/swiss_referendum_10mio_latest_source_comparison.csv; docs/research/THESIS_PROJECT_HIGHLEVEL_VIEW.md",
            key_evidence_de="Swiss ist als descriptive_pending_result markiert.",
            remaining_gap_de="Offizielles Resultat vom 14. Juni 2026 und Post-Resultat-Mapping fehlen.",
            next_action_de="Nach offiziellem Resultat Swiss-Artefakte neu generieren und Wording pruefen.",
        ),
        _audit_row(
            audit_id="goal_audit_07_monitor_boundary",
            goal_requirement_de="Monitor bleibt Prototype/Appendix, solange Human Review fehlt.",
            current_status="appendix_only_pending_human_review",
            evidence_artifacts="data/results/monitor_anomaly_review_summary.csv; data/results/thesis_project_highlevel_view.csv",
            key_evidence_de="Monitor Review-Access bleibt pausiert und thesis-facing Alert-Evidenz ist blockiert.",
            remaining_gap_de="Human Source Review der Monitor-Cases fehlt.",
            next_action_de="Monitor hoechstens als read-only Prototype und Review Workflow erwaehnen.",
        ),
        _audit_row(
            audit_id="goal_audit_08_future_agents",
            goal_requirement_de="Agentenpipeline ist nur Highlevel-Future-Work.",
            current_status="deferred_future_work_only",
            evidence_artifacts="data/results/thesis_agent_assistance_protocol.csv; docs/research/THESIS_AGENT_ASSISTANCE_PROTOCOL.md; data/results/thesis_agent_pipeline_control_audit.csv; docs/project/THESIS_AGENT_PIPELINE_CONTROL_AUDIT.md; data/results/thesis_agent_pipeline_upgrade_plan.csv; docs/research/THESIS_AGENT_PIPELINE_UPGRADE_PLAN.md",
            key_evidence_de=(
                f"Agent Control: {agent_control_rows} Rollen; "
                f"documentation-only: {agent_documentation_only}; deferred: {agent_deferred}; "
                f"aktiv: {agent_active}. Agent Upgrade Plan: {agent_upgrade_rows} Reihen; "
                f"aktive Upgrade-Reihen: {agent_upgrade_active}. Human-Owner, Proof-Artifact, "
                "Failure-Mode, llm_audit_log, bounded prompts, max 50 rows und Tests "
                "bleiben Vorbedingungen."
            ),
            remaining_gap_de="Keine Aktivierung im aktuellen Goal erlaubt.",
            next_action_de="Nur Future-Work-Abschnitt schreiben, keine Runtime-Agenten implementieren.",
        ),
        _audit_row(
            audit_id="goal_audit_09_advisor_package",
            goal_requirement_de="Dozentenpaket, Uebergabetext, Checklist und Feedbacklog sind vorhanden.",
            current_status="proved_current_artifact",
            evidence_artifacts="data/results/thesis_advisor_handoff_package.csv; docs/project/DOZENTEN_UEBERGABE_TEXT.md; docs/project/DOZENTEN_ABSPRACHE_CHECKLIST.md; docs/project/DOZENTEN_FEEDBACK_LOG.md",
            key_evidence_de=(
                f"Handoff Package: {len(handoff_package)} Dateien; "
                f"Handoff Note: {len(handoff_note)} Abschnitte; "
                f"Feedback pending: {feedback_pending} Zeilen."
            ),
            remaining_gap_de="Echtes Dozentenfeedback fehlt noch.",
            next_action_de="Nach Betreuung Feedback in DOZENTEN_FEEDBACK_LOG eintragen.",
        ),
        _audit_row(
            audit_id="goal_audit_10_final_qa",
            goal_requirement_de="Projektchecks, Status und Work Log bleiben vor Stopp aktuell.",
            current_status="project_control_ready",
            evidence_artifacts="STATUS.md; docs/project/WORK_LOG.md; data/results/thesis_final_gate_board.csv; docs/project/THESIS_FINAL_GATE_BOARD.md",
            key_evidence_de=(
                "Status, Review-Check und Work Log werden vor jedem Commit aktualisiert. "
                f"Final Gate Board: {final_gate_rows} gates; draft-allowed "
                f"{final_gate_draft_allowed}; final-ready {final_gate_ready}; "
                f"final-not-ready {final_gate_not_ready}; blocking-count "
                f"{final_gate_blocking_count}."
            ),
            remaining_gap_de="DOCX-Render-QA bleibt lokal blockiert, solange LibreOffice/soffice fehlt; Final Gate Board bleibt vor finaler Abgabe erneut zu pruefen.",
            next_action_de="Vor finalem Export Tests, review_check, Source Review, Swiss-Spelling und DOCX-Render-QA wiederholen.",
        ),
    ]
    return pd.DataFrame(rows, columns=AUDIT_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_goal_completion_audit(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _audit_row(
    *,
    audit_id: str,
    goal_requirement_de: str,
    current_status: str,
    evidence_artifacts: str,
    key_evidence_de: str,
    remaining_gap_de: str,
    next_action_de: str,
) -> dict[str, object]:
    return {
        "audit_id": audit_id,
        "goal_requirement_de": goal_requirement_de,
        "current_status": current_status,
        "evidence_artifacts": evidence_artifacts,
        "key_evidence_de": key_evidence_de,
        "remaining_gap_de": remaining_gap_de,
        "next_action_de": next_action_de,
    }


def _validate_audit(audit: pd.DataFrame, *, repo_root: Path) -> None:
    _require_columns(audit, AUDIT_COLUMNS, "goal completion audit")
    if audit["audit_id"].duplicated().any():
        raise ValueError("Goal completion audit contains duplicate audit_id values.")
    if len(audit) != 10:
        raise ValueError("Goal completion audit must contain exactly 10 rows.")
    for column in (
        "goal_requirement_de",
        "current_status",
        "evidence_artifacts",
        "key_evidence_de",
        "remaining_gap_de",
        "next_action_de",
    ):
        if audit[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Goal completion audit contains empty {column}.")
    for artifacts in audit["evidence_artifacts"].astype(str):
        for artifact in _split_semicolon(artifacts):
            if not (repo_root / artifact).exists():
                raise FileNotFoundError(f"Goal completion audit artifact missing: {artifact}")
    joined = "\n".join(audit.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Goal completion audit must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "final_blocked_official_result",
        "finale zitation",
        "soffice",
        "review-access bleibt pausiert",
        "runtime-agenten",
        "llm_audit_log",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Goal completion audit missing required terms: " + ", ".join(missing))


def _render_audit_doc(audit: pd.DataFrame) -> str:
    status_counts = audit["current_status"].value_counts().to_dict()
    return (
        "# Thesis Goal Completion Audit\n\n"
        "Dieses Audit prueft den aktuellen Stand des aktiven "
        "Konsolidierungsziels gegen belegbare Artefakte. Es ist kein neues "
        "empirisches Resultat und behauptet keine finale Zielerreichung, solange "
        "Source Review, Swiss Resultat-Gate oder DOCX-Render-QA offen sind.\n\n"
        "## Counts\n\n"
        f"- Audit rows: {len(audit)}\n"
        f"- Proved current artifacts: {int(status_counts.get('proved_current_artifact', 0))}\n"
        f"- Final blocked official result: {int(status_counts.get('final_blocked_official_result', 0))}\n"
        f"- Deferred future work: {int(status_counts.get('deferred_future_work_only', 0))}\n\n"
        "## Audit Rows\n\n"
        + _markdown_table(audit)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze dieses Audit als Stop-/Weiterarbeitskontrolle. Es darf nicht "
        "genutzt werden, um Source Review, Swiss Resultat-Gate, DOCX-Render-QA, "
        "Review-Access, Runtime-Agenten, MCP, Model Routing oder Trading-Pfade "
        "zu ueberspringen.\n"
    )


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required goal completion audit input missing: {path}")
    return pd.read_csv(path)


def _resolve_under(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _split_semicolon(value: str) -> list[str]:
    if value.lower() == "nan":
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def _markdown_table(frame: pd.DataFrame) -> str:
    columns = [str(column) for column in frame.columns]
    header = "| " + " | ".join(_escape_markdown_cell(column) for column in columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = []
    for record in frame.to_dict(orient="records"):
        rows.append(
            "| "
            + " | ".join(_escape_markdown_cell(record.get(column, "")) for column in columns)
            + " |"
        )
    return "\n".join([header, separator, *rows])


def _escape_markdown_cell(value: object) -> str:
    text = str(value).replace("\n", " ").strip()
    return text.replace("|", "\\|")


if __name__ == "__main__":
    raise SystemExit(main())
