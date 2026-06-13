from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_thesis_consolidation_index import (
    INDEX_COLUMNS,
    generate_thesis_consolidation_index,
)


def test_generate_thesis_consolidation_index_writes_artifact_map(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_consolidation_index(repo_root=tmp_path)

    index = pd.read_csv(result.index_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(index.columns) == INDEX_COLUMNS
    assert result.index_rows == 62
    assert "Thesis Consolidation Index" in doc
    assert "Indexed artifacts: 62" in doc
    assert "dozentenbericht_ba_thesis.docx" in doc
    assert "THESIS_ADVISOR_HANDOFF_PACKAGE.md" in doc
    assert "THESIS_HIGHLEVEL_NEXT_STEP_CONTROL_SUMMARY.md" in doc
    assert "DOZENTEN_UEBERGABE_TEXT.md" in doc
    assert "DOZENTEN_FEEDBACK_LOG.md" in doc
    assert "DOZENTEN_FEEDBACK_INTEGRATION_CHECKLIST.md" in doc
    assert "THESIS_ADVISOR_SOURCE_REVIEW_FOLLOWUP.md" in doc
    assert "THESIS_H1_MANUAL_SOURCE_REVIEW_FOLLOWUP.md" in doc
    assert "THESIS_H1_SOURCE_REVIEW_DECISION_QUEUE.md" in doc
    assert "THESIS_H1_SOURCE_REVIEW_BATCH_WORKSHEET.md" in doc
    assert "THESIS_H2_MANUAL_SOURCE_REVIEW_FOLLOWUP.md" in doc
    assert "THESIS_H2_SOURCE_REVIEW_DECISION_QUEUE.md" in doc
    assert "THESIS_H2_SOURCE_REVIEW_BATCH_WORKSHEET.md" in doc
    assert "THESIS_H3_MANUAL_SOURCE_REVIEW_FOLLOWUP.md" in doc
    assert "THESIS_H3_SOURCE_REVIEW_DECISION_QUEUE.md" in doc
    assert "THESIS_H3_SOURCE_REVIEW_BATCH_WORKSHEET.md" in doc
    assert "THESIS_SOURCE_REVIEW_WORKSHEET_OVERVIEW.md" in doc
    assert "THESIS_H1_H2_H3_WORKSHEET_DRAFTING_BRIDGE.md" in doc
    assert "THESIS_H1_H2_H3_DECISION_QUEUE_OVERVIEW.md" in doc
    assert "THESIS_H1_H2_H3_DECISION_QUEUE_LEDGER_ALIGNMENT.md" in doc
    assert "THESIS_LEDGER_CITATION_GATE_SUMMARY.md" in doc
    assert "THESIS_MANUAL_SOURCE_REVIEW_UPDATE_CHECKLIST.md" in doc
    assert "THESIS_SOURCE_REVIEW_BATCH_EXECUTION_PLAN.md" in doc
    assert "THESIS_MANUAL_SOURCE_REVIEW_FOLLOWUP_OVERVIEW.md" in doc
    assert "THESIS_SUBMISSION_READINESS_BOARD.md" in doc
    assert "THESIS_DRAFTING_SEQUENCE.md" in doc
    assert "THESIS_SOURCE_ACCESS_AUDIT.md" in doc
    assert "THESIS_SOURCE_STRUCTURE_INVENTORY.md" in doc
    assert "THESIS_SOURCE_REVIEW_DECISION_PACKETS.md" in doc
    assert "THESIS_H1_H2_H3_SOURCE_REVIEW_NOTES.md" in doc
    assert "THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md" in doc
    assert "THESIS_H1_H2_H3_MANUAL_SOURCE_REVIEW_EXECUTION_PASS.md" in doc
    assert "THESIS_SOURCE_REVIEW_PROGRESS_PROTOCOL.md" in doc
    assert "THESIS_SOURCE_REVIEW_CHAPTER_HANDOFF.md" in doc
    assert "THESIS_CHAPTER_SOURCE_REVIEW_CHECKLIST.md" in doc
    assert "THESIS_H1_H2_H3_DRAFTING_CHECKLIST.md" in doc
    assert "THESIS_FINAL_GATE_BOARD.md" in doc
    assert "THESIS_TRACEABILITY_AUDIT.md" in doc
    assert "THESIS_METHOD_INTERPRETATION_SOURCE_COVERAGE.md" in doc
    assert "THESIS_H1_H2_H3_CORE_SECTIONS.md" in doc
    assert "THESIS_AGENT_PIPELINE_UPGRADE_PLAN.md" in doc
    assert "THESIS_AGENT_PIPELINE_SAFETY_CASE.md" in doc
    assert "THESIS_GOAL_COMPLETION_AUDIT.md" in doc
    assert "THESIS_EXECUTION_CHECKLIST.md" in doc
    assert "THESIS_CHAPTER_SOURCE_BINDINGS.md" in doc
    assert "THESIS_SOURCE_REVIEW_EXECUTION.md" in doc
    assert "THESIS_AGENT_FUTURE_WORK_HANDOFF.md" in doc
    assert "THESIS_AGENT_PIPELINE_CONTROL_AUDIT.md" in doc
    assert "THESIS_WORDING_GUARD.md" in doc
    assert "THESIS_H1_H2_H3_BOUNDED_CHAPTER_DRAFT.md" in doc
    assert "THESIS_H1_H2_H3_SOURCE_GATED_WRITING_PASS.md" in doc
    assert "THESIS_H1_H2_H3_SOURCE_GATED_THESIS_DRAFTING_PASS.md" in doc
    assert chr(223) not in doc


def test_thesis_consolidation_index_keeps_deferred_boundaries(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_consolidation_index(repo_root=tmp_path)

    index = pd.read_csv(result.index_path)
    joined = "\n".join(index.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert "review-access bleibt pausiert" in joined
    assert "keine runtime-agenten" in joined
    assert "quellenstatus nicht automatisch hochstufen" in joined
    assert "keine roh" in joined
    assert "trading-pfade" in joined
    assert "source_access_audit" in joined
    assert "source_structure_inventory" in joined
    assert "source_review_decision_packets" in joined
    assert "h1_h2_h3_source_review_notes" in joined
    assert "source_review_progress_ledger" in joined
    assert "manual_source_review_execution_pass" in joined
    assert "source_review_progress_protocol" in joined
    assert "source_review_chapter_handoff" in joined
    assert "chapter_source_review_checklist" in joined
    assert "h1_h2_h3_drafting_checklist" in joined
    assert "h1_h2_h3_bounded_chapter_draft" in joined
    assert "source_gated_writing_pass" in joined
    assert "source_gated_thesis_drafting_pass" in joined
    assert "final_gate_board" in joined
    assert "traceability_audit" in joined
    assert "method_interpretation_source_coverage" in joined
    assert "h1_h2_h3_core_sections" in joined
    assert "agent_pipeline_upgrade_plan" in joined
    assert "agent_pipeline_safety_case" in joined
    assert "agent_pipeline_control" in joined
    assert "goal_completion_audit" in joined
    assert "advisor_feedback_integration" in joined
    assert "highlevel_next_step_control_summary" in joined
    assert "7 control rows" in joined
    assert "4 thesis-facing methoden" in joined
    assert "4 thesis-facing interpretationen" in joined
    assert "5 kern-tabellen" in joined
    assert "4 kern-figuren" in joined
    assert "0 aktive runtime-agenten" in joined
    assert "advisor_source_review_followup" in joined
    assert "h1_manual_source_review_followup" in joined
    assert "h1_source_review_decision_queue" in joined
    assert "h1_source_review_batch_worksheet" in joined
    assert "10 h1 worksheet rows" in joined
    assert "0 final-release rows" in joined
    assert "h2_manual_source_review_followup" in joined
    assert "h2_source_review_decision_queue" in joined
    assert "h2_source_review_batch_worksheet" in joined
    assert "5 h2 worksheet rows" in joined
    assert "h3_manual_source_review_followup" in joined
    assert "h3_source_review_decision_queue" in joined
    assert "h3_source_review_batch_worksheet" in joined
    assert "8 h3 worksheet rows" in joined
    assert "source_review_worksheet_overview" in joined
    assert "4 overview rows" in joined
    assert "23 worksheet rows" in joined
    assert "h1_h2_h3_worksheet_drafting_bridge" in joined
    assert "15 drafting steps" in joined
    assert "0 source/artifact gaps" in joined
    assert "jede methode" in joined
    assert "jede interpretation" in joined
    assert "h1_h2_h3_decision_queue_overview" in joined
    assert "h1_h2_h3_decision_queue_ledger_alignment" in joined
    assert "23 matches" in joined
    assert "0 missing rows" in joined
    assert "0 feldabweichungen" in joined
    assert "ledger_citation_gate_summary" in joined
    assert "23 citation-blocked rows" in joined
    assert "manual_source_review_update_checklist" in joined
    assert "8 update-schritte" in joined
    assert "23 pending citation rows" in joined
    assert "0 final-ready rows" in joined
    assert "source_review_batch_execution_plan" in joined
    assert "4 batch rows" in joined
    assert "23 source review rows" in joined
    assert "0 final-release rows" in joined
    assert "manual_source_review_followup_overview" in joined
    assert "keine runtime-agenten" in joined


def _write_fixture(root: Path) -> None:
    paths = [
        "docs/project/dozentenbericht_ba_thesis.docx",
        "docs/project/dozentenbericht_ba_thesis.md",
        "docs/project/DOZENTEN_ABSPRACHE_CHECKLIST.md",
        "docs/research/THESIS_PROJECT_HIGHLEVEL_VIEW.md",
        "docs/research/THESIS_NEXT_WORK_PLAN.md",
        "docs/project/THESIS_HIGHLEVEL_NEXT_STEP_CONTROL_SUMMARY.md",
        "data/results/thesis_highlevel_next_step_control_summary.csv",
        "docs/project/THESIS_EXECUTION_CHECKLIST.md",
        "data/results/thesis_execution_checklist.csv",
        "docs/project/THESIS_CHAPTER_SOURCE_BINDINGS.md",
        "data/results/thesis_chapter_source_bindings.csv",
        "docs/research/THESIS_SOURCE_REVIEW_WORKSHEET.md",
        "docs/project/THESIS_SOURCE_REVIEW_EXECUTION.md",
        "data/results/thesis_source_review_execution.csv",
        "docs/research/THESIS_WORDING_GUARD.md",
        "docs/research/THESIS_TABLE_FIGURE_CAPTIONS.md",
        "docs/research/THESIS_CHAPTER_DRAFT.md",
        "docs/research/THESIS_H1_H2_H3_BOUNDED_CHAPTER_DRAFT.md",
        "data/results/thesis_h1_h2_h3_bounded_chapter_draft.csv",
        "docs/research/THESIS_H1_H2_H3_SOURCE_GATED_WRITING_PASS.md",
        "data/results/thesis_h1_h2_h3_source_gated_writing_pass.csv",
        "docs/research/THESIS_H1_H2_H3_SOURCE_GATED_THESIS_DRAFTING_PASS.md",
        "data/results/thesis_h1_h2_h3_source_gated_thesis_drafting_pass.csv",
        "docs/research/THESIS_SOURCE_REVIEW_PLAN.md",
        "docs/research/THESIS_AGENT_ASSISTANCE_PROTOCOL.md",
        "docs/project/THESIS_AGENT_FUTURE_WORK_HANDOFF.md",
        "data/results/thesis_agent_future_work_handoff.csv",
        "docs/project/THESIS_AGENT_PIPELINE_CONTROL_AUDIT.md",
        "data/results/thesis_agent_pipeline_control_audit.csv",
        "docs/project/THESIS_ADVISOR_HANDOFF_PACKAGE.md",
        "data/results/thesis_advisor_handoff_package.csv",
        "docs/project/DOZENTEN_UEBERGABE_TEXT.md",
        "data/results/thesis_advisor_handoff_note.csv",
        "docs/project/DOZENTEN_FEEDBACK_LOG.md",
        "data/results/thesis_advisor_feedback_log_template.csv",
        "docs/project/DOZENTEN_FEEDBACK_INTEGRATION_CHECKLIST.md",
        "data/results/thesis_advisor_feedback_integration_checklist.csv",
        "docs/project/THESIS_ADVISOR_SOURCE_REVIEW_FOLLOWUP.md",
        "data/results/thesis_advisor_source_review_followup.csv",
        "docs/project/THESIS_H1_MANUAL_SOURCE_REVIEW_FOLLOWUP.md",
        "data/results/thesis_h1_manual_source_review_followup.csv",
        "docs/project/THESIS_H1_SOURCE_REVIEW_DECISION_QUEUE.md",
        "data/results/thesis_h1_source_review_decision_queue.csv",
        "docs/project/THESIS_H1_SOURCE_REVIEW_BATCH_WORKSHEET.md",
        "data/results/thesis_h1_source_review_batch_worksheet.csv",
        "docs/project/THESIS_H2_MANUAL_SOURCE_REVIEW_FOLLOWUP.md",
        "data/results/thesis_h2_manual_source_review_followup.csv",
        "docs/project/THESIS_H2_SOURCE_REVIEW_DECISION_QUEUE.md",
        "data/results/thesis_h2_source_review_decision_queue.csv",
        "docs/project/THESIS_H2_SOURCE_REVIEW_BATCH_WORKSHEET.md",
        "data/results/thesis_h2_source_review_batch_worksheet.csv",
        "docs/project/THESIS_H3_MANUAL_SOURCE_REVIEW_FOLLOWUP.md",
        "data/results/thesis_h3_manual_source_review_followup.csv",
        "docs/project/THESIS_H3_SOURCE_REVIEW_DECISION_QUEUE.md",
        "data/results/thesis_h3_source_review_decision_queue.csv",
        "docs/project/THESIS_H3_SOURCE_REVIEW_BATCH_WORKSHEET.md",
        "data/results/thesis_h3_source_review_batch_worksheet.csv",
        "docs/project/THESIS_SOURCE_REVIEW_WORKSHEET_OVERVIEW.md",
        "data/results/thesis_source_review_worksheet_overview.csv",
        "docs/project/THESIS_H1_H2_H3_WORKSHEET_DRAFTING_BRIDGE.md",
        "data/results/thesis_h1_h2_h3_worksheet_drafting_bridge.csv",
        "docs/project/THESIS_H1_H2_H3_DECISION_QUEUE_OVERVIEW.md",
        "data/results/thesis_h1_h2_h3_decision_queue_overview.csv",
        "docs/project/THESIS_H1_H2_H3_DECISION_QUEUE_LEDGER_ALIGNMENT.md",
        "data/results/thesis_h1_h2_h3_decision_queue_ledger_alignment.csv",
        "docs/project/THESIS_LEDGER_CITATION_GATE_SUMMARY.md",
        "data/results/thesis_ledger_citation_gate_summary.csv",
        "docs/project/THESIS_MANUAL_SOURCE_REVIEW_UPDATE_CHECKLIST.md",
        "data/results/thesis_manual_source_review_update_checklist.csv",
        "docs/project/THESIS_SOURCE_REVIEW_BATCH_EXECUTION_PLAN.md",
        "data/results/thesis_source_review_batch_execution_plan.csv",
        "docs/project/THESIS_MANUAL_SOURCE_REVIEW_FOLLOWUP_OVERVIEW.md",
        "data/results/thesis_manual_source_review_followup_overview.csv",
        "docs/project/THESIS_SUBMISSION_READINESS_BOARD.md",
        "data/results/thesis_submission_readiness_board.csv",
        "docs/project/THESIS_DRAFTING_SEQUENCE.md",
        "data/results/thesis_drafting_sequence.csv",
        "docs/project/THESIS_SOURCE_ACCESS_AUDIT.md",
        "data/results/thesis_source_access_audit.csv",
        "docs/project/THESIS_SOURCE_STRUCTURE_INVENTORY.md",
        "data/results/thesis_source_structure_inventory.csv",
        "docs/project/THESIS_SOURCE_REVIEW_DECISION_PACKETS.md",
        "data/results/thesis_source_review_decision_packets.csv",
        "docs/project/THESIS_H1_H2_H3_SOURCE_REVIEW_NOTES.md",
        "data/results/thesis_h1_h2_h3_source_review_notes.csv",
        "docs/project/THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md",
        "data/results/thesis_source_review_progress_ledger.csv",
        "docs/project/THESIS_H1_H2_H3_MANUAL_SOURCE_REVIEW_EXECUTION_PASS.md",
        "data/results/thesis_h1_h2_h3_manual_source_review_execution_pass.csv",
        "docs/project/THESIS_SOURCE_REVIEW_PROGRESS_PROTOCOL.md",
        "data/results/thesis_source_review_progress_protocol.csv",
        "docs/project/THESIS_SOURCE_REVIEW_CHAPTER_HANDOFF.md",
        "data/results/thesis_source_review_chapter_handoff.csv",
        "docs/project/THESIS_CHAPTER_SOURCE_REVIEW_CHECKLIST.md",
        "data/results/thesis_chapter_source_review_checklist.csv",
        "docs/project/THESIS_H1_H2_H3_DRAFTING_CHECKLIST.md",
        "data/results/thesis_h1_h2_h3_drafting_checklist.csv",
        "docs/project/THESIS_FINAL_GATE_BOARD.md",
        "data/results/thesis_final_gate_board.csv",
        "docs/project/THESIS_TRACEABILITY_AUDIT.md",
        "data/results/thesis_method_interpretation_traceability.csv",
        "data/results/thesis_result_package_traceability.csv",
        "docs/project/THESIS_METHOD_INTERPRETATION_SOURCE_COVERAGE.md",
        "data/results/thesis_method_interpretation_source_coverage.csv",
        "docs/research/THESIS_H1_H2_H3_CORE_SECTIONS.md",
        "data/results/thesis_h1_h2_h3_core_sections.csv",
        "docs/research/THESIS_AGENT_PIPELINE_UPGRADE_PLAN.md",
        "data/results/thesis_agent_pipeline_upgrade_plan.csv",
        "docs/project/THESIS_AGENT_PIPELINE_SAFETY_CASE.md",
        "data/results/thesis_agent_pipeline_safety_case.csv",
        "docs/project/THESIS_GOAL_COMPLETION_AUDIT.md",
        "data/results/thesis_goal_completion_audit.csv",
        "STATUS.md",
        "docs/project/WORK_LOG.md",
    ]
    for relative in paths:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")
