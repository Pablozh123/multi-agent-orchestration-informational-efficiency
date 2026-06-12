from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_thesis_goal_completion_audit import (
    AUDIT_COLUMNS,
    generate_goal_completion_audit,
)


def test_generate_goal_completion_audit_writes_remaining_gates(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_goal_completion_audit(repo_root=tmp_path)

    audit = pd.read_csv(result.audit_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(audit.columns) == AUDIT_COLUMNS
    assert result.audit_rows == 10
    assert "Thesis Goal Completion Audit" in doc
    assert "Audit rows: 10" in doc
    assert "keine finale Zielerreichung" in doc
    assert "thesis_source_access_audit.csv" in doc
    assert "thesis_source_structure_inventory.csv" in doc
    assert "thesis_source_review_decision_packets.csv" in doc
    assert "thesis_h1_h2_h3_source_review_notes.csv" in doc
    assert "THESIS_H1_H2_H3_SOURCE_REVIEW_NOTES.md" in doc
    assert "thesis_source_review_progress_ledger.csv" in doc
    assert "THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md" in doc
    assert "thesis_h1_h2_h3_manual_source_review_execution_pass.csv" in doc
    assert "THESIS_H1_H2_H3_MANUAL_SOURCE_REVIEW_EXECUTION_PASS.md" in doc
    assert "thesis_source_review_progress_protocol.csv" in doc
    assert "THESIS_SOURCE_REVIEW_PROGRESS_PROTOCOL.md" in doc
    assert "thesis_method_interpretation_traceability.csv" in doc
    assert "thesis_result_package_traceability.csv" in doc
    assert "thesis_method_interpretation_source_coverage.csv" in doc
    assert "THESIS_METHOD_INTERPRETATION_SOURCE_COVERAGE.md" in doc
    assert "thesis_h1_h2_h3_core_sections.csv" in doc
    assert "THESIS_H1_H2_H3_CORE_SECTIONS.md" in doc
    assert "thesis_source_review_chapter_handoff.csv" in doc
    assert "THESIS_SOURCE_REVIEW_CHAPTER_HANDOFF.md" in doc
    assert "thesis_chapter_source_review_checklist.csv" in doc
    assert "THESIS_CHAPTER_SOURCE_REVIEW_CHECKLIST.md" in doc
    assert "thesis_h1_h2_h3_drafting_checklist.csv" in doc
    assert "THESIS_H1_H2_H3_DRAFTING_CHECKLIST.md" in doc
    assert "thesis_h1_h2_h3_bounded_chapter_draft.csv" in doc
    assert "THESIS_H1_H2_H3_BOUNDED_CHAPTER_DRAFT.md" in doc
    assert "thesis_h1_h2_h3_source_gated_writing_pass.csv" in doc
    assert "THESIS_H1_H2_H3_SOURCE_GATED_WRITING_PASS.md" in doc
    assert "THESIS_CHAPTER_DRAFT.md" in doc
    assert "thesis_agent_pipeline_control_audit.csv" in doc
    assert "THESIS_AGENT_PIPELINE_CONTROL_AUDIT.md" in doc
    assert "thesis_agent_pipeline_upgrade_plan.csv" in doc
    assert "THESIS_AGENT_PIPELINE_UPGRADE_PLAN.md" in doc
    assert "thesis_final_gate_board.csv" in doc
    assert "THESIS_FINAL_GATE_BOARD.md" in doc
    assert "Source Review" in doc
    assert chr(223) not in doc


def test_goal_completion_audit_keeps_open_gates_visible(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_goal_completion_audit(repo_root=tmp_path)

    audit = pd.read_csv(result.audit_path)
    joined = "\n".join(audit.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert "final_blocked_official_result" in set(audit["current_status"])
    assert "appendix_only_pending_human_review" in set(audit["current_status"])
    assert "deferred_future_work_only" in set(audit["current_status"])
    assert "finale zitation" in joined
    assert "soffice" in joined
    assert "review-access bleibt pausiert" in joined
    assert "runtime-agenten" in joined
    assert "llm_audit_log" in joined
    assert "source structure: 1 pdf, 1 html, 1 external-only zeilen" in joined
    assert "source decisions: 2 pakete; full review: 1; metadata-only: 1; pending: 2" in joined
    assert "h1-h2-h3 source notes: 3 zeilen; h1: 1; h2: 1; h3: 1; pending: 3" in joined
    assert "source progress ledger: 3 zeilen; pending: 3; final-ready: 0" in joined
    assert "source-status changes erlaubt: 0" in joined
    assert "manual execution pass: 3 zeilen; h1: 1; h2: 1; h3: 1; unique sources: 3" in joined
    assert "bounded-draft-ready: 3; final-ready: 0; source-status changes erlaubt: 0; coverage gaps: 0; unknown sources: 0; missing artifacts: 0" in joined
    assert "source progress protocol: 6 zeilen in 6 bereichen" in joined
    assert "traceability: 1 methoden, 1 interpretationen, 0 gaps" in joined
    assert "source coverage: 3 links; thesis-facing: 3; unique sources: 2; h1: 3; h2: 0; h3: 0; coverage gaps: 0" in joined
    assert "traceability-kernpaket: 5 tabellen, 4 figuren, 0 gaps" in joined
    assert "h1-h2-h3 core sections: 3 zeilen (h1; h2; h3)" in joined
    assert "chapter handoff: 3 kapitel; coverage-ready: 3; review rows: 3; pending: 3; final-ready: 0" in joined
    assert "chapter checklist: 18 checks; bounded-draft-ready: 18; final-ready: 0; final-blocked: 3" in joined
    assert "h1-h2-h3 drafting checklist: 18 checks; bounded-draft-ready: 18; final-ready: 0; final-blocked: 3" in joined
    assert "h1-h2-h3 bounded chapter draft: 18 bausteine (h1; h2; h3)" in joined
    assert "bounded-draft-ready: 18; final-ready: 0" in joined
    assert "source-gated writing pass: 3 kapitel; bounded-draft-ready: 3; final-ready: 0; coverage gaps: 0" in joined
    assert "main chapter draft: source-gated integration fuer h1, h2 und h3" in joined
    assert "h1-h3 kapitel gegen source review, wording guard" in joined
    assert "agent control: 2 rollen; documentation-only: 1; deferred: 1; aktiv: 0" in joined
    assert "agent upgrade plan: 2 reihen; aktive upgrade-reihen: 0" in joined
    assert "human-owner, proof-artifact, failure-mode" in joined
    assert "max 50 rows" in joined
    assert "final gate board: 8 gates; draft-allowed 8; final-ready 1" in joined
    assert "final-not-ready 7; blocking-count 10" in joined


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs_project = root / "docs/project"
    docs_research = root / "docs/research"
    results.mkdir(parents=True)
    docs_project.mkdir(parents=True)
    docs_research.mkdir(parents=True)

    (docs_research / "THESIS_CHAPTER_DRAFT.md").write_text(
        "Source-Gated Integration fuer H1, H2 und H3\n",
        encoding="utf-8",
    )

    pd.DataFrame(
        [
            _evidence("method_h1", "method", "thesis_facing_ready"),
            _evidence("interpretation_h1", "interpretation", "thesis_facing_ready"),
            _evidence("future_agent", "future_work", "future_work_deferred"),
        ]
    ).to_csv(results / "thesis_evidence_map.csv", index=False)

    package_rows = [
        {"package_type": "table", "include_in_core_package": True, "thesis_readiness": "thesis_facing_ready"}
        for _ in range(5)
    ] + [
        {"package_type": "figure", "include_in_core_package": True, "thesis_readiness": "thesis_facing_ready"}
        for _ in range(4)
    ] + [
        {"package_type": "table", "include_in_core_package": False, "thesis_readiness": "future_work_deferred"}
    ]
    pd.DataFrame(package_rows).to_csv(results / "thesis_curated_result_package.csv", index=False)

    pd.DataFrame(
        [
            _gate("advisor_handoff", "ready_for_advisor_discussion"),
            _gate("source_review", "final_blocked_source_review"),
            _gate("h1_h2_h3_results", "ready_for_bounded_result_draft"),
            _gate("table_figure_package", "ready_for_draft_integration"),
            _gate("monitor_appendix", "appendix_only_pending_human_review"),
            _gate("swiss_result_gate", "final_blocked_official_result"),
            _gate("agent_future_work", "deferred_future_work_only"),
            _gate("final_qa", "pending_after_draft"),
            _gate("chapter_source_mapping", "ready_for_draft"),
        ]
    ).to_csv(results / "thesis_submission_readiness_board.csv", index=False)

    pd.DataFrame(
        [
            {"sequence_id": f"draft_{idx}", "draft_permission": "write_now_bounded"}
            for idx in range(4)
        ]
        + [{"sequence_id": "draft_future", "draft_permission": "future_work_only"}]
    ).to_csv(results / "thesis_drafting_sequence.csv", index=False)
    pd.DataFrame(
        [
            {
                "source_id": f"source_{idx}",
                "priority_band": "priority_1_method_foundation_review",
                "local_file_exists": idx < 2,
                "access_route": "local_pdf_review" if idx < 2 else "external_locator_review",
            }
            for idx in range(3)
        ]
    ).to_csv(results / "thesis_source_access_audit.csv", index=False)
    pd.DataFrame(
        [
            {"source_id": "source_0", "structure_inventory_status": "local_pdf_structure_available"},
            {"source_id": "source_1", "structure_inventory_status": "local_html_structure_available"},
            {"source_id": "source_2", "structure_inventory_status": "external_only"},
        ]
    ).to_csv(results / "thesis_source_structure_inventory.csv", index=False)
    pd.DataFrame(
        [
            {
                "decision_packet_id": "decision_01",
                "final_citation_gate": "full_source_review_required_before_final_citation",
                "reviewer_decision": "pending",
            },
            {
                "decision_packet_id": "decision_02",
                "final_citation_gate": "metadata_and_relevance_review_before_future_work_use",
                "reviewer_decision": "pending",
            },
        ]
    ).to_csv(results / "thesis_source_review_decision_packets.csv", index=False)
    pd.DataFrame(
        [
            _source_note("note_h1", "H1", "T2", "F1"),
            _source_note("note_h2", "H2", "T3", "F2"),
            _source_note("note_h3", "H3", "T4", "F3"),
        ]
    ).to_csv(results / "thesis_h1_h2_h3_source_review_notes.csv", index=False)
    pd.DataFrame(
        [
            _ledger("ledger_h1", "H1"),
            _ledger("ledger_h2", "H2"),
            _ledger("ledger_h3", "H3"),
        ]
    ).to_csv(results / "thesis_source_review_progress_ledger.csv", index=False)
    pd.DataFrame(
        [
            _manual_execution("manual_h1", "H1", "source_a", "method_h1"),
            _manual_execution("manual_h2", "H2", "source_b", "method_h2"),
            _manual_execution("manual_h3", "H3", "source_c", "method_h3"),
        ]
    ).to_csv(
        results / "thesis_h1_h2_h3_manual_source_review_execution_pass.csv",
        index=False,
    )
    pd.DataFrame(
        [
            _protocol("protocol_01", "evidence_mapping"),
            _protocol("protocol_02", "result_package"),
            _protocol("protocol_03", "source_review_ledger"),
            _protocol("protocol_04", "final_citation_gate"),
            _protocol("protocol_05", "h1_h2_h3_drafting"),
            _protocol("protocol_06", "future_agents"),
        ]
    ).to_csv(results / "thesis_source_review_progress_protocol.csv", index=False)
    pd.DataFrame(
        [
            {
                "item_type": "method",
                "thesis_readiness": "thesis_facing_ready",
                "traceability_status": "draft_traceable_final_source_review_pending",
            },
            {
                "item_type": "interpretation",
                "thesis_readiness": "thesis_facing_ready",
                "traceability_status": "draft_traceable_final_source_review_pending",
            },
        ]
    ).to_csv(results / "thesis_method_interpretation_traceability.csv", index=False)
    pd.DataFrame(
        [
            _source_coverage("method_h1", "H1", "source_a"),
            _source_coverage("method_h1", "H1", "source_b"),
            _source_coverage("interpretation_h1", "H1", "source_a"),
        ]
    ).to_csv(results / "thesis_method_interpretation_source_coverage.csv", index=False)
    pd.DataFrame(
        [
            {
                "package_type": "table",
                "include_in_core_package": True,
                "package_traceability_status": "core_package_ready_for_draft",
            }
            for _ in range(5)
        ]
        + [
            {
                "package_type": "figure",
                "include_in_core_package": True,
                "package_traceability_status": "core_package_ready_for_draft",
            }
            for _ in range(4)
        ]
    ).to_csv(results / "thesis_result_package_traceability.csv", index=False)
    pd.DataFrame(
        [
            {
                "hypothesis": hypothesis,
                "method_evidence_ids": f"method_{hypothesis.lower()}",
                "interpretation_evidence_ids": f"interpretation_{hypothesis.lower()}",
                "literature_source_ids": "lit_a",
                "deterministic_artifacts": "data/results/thesis_core_results_table.csv",
                "selected_tables": "T2",
                "selected_figures": "F1",
            }
            for hypothesis in ["H1", "H2", "H3"]
        ]
    ).to_csv(results / "thesis_h1_h2_h3_core_sections.csv", index=False)
    pd.DataFrame(
        [
            _chapter_handoff("handoff_h1", "H1", "T2; F1"),
            _chapter_handoff("handoff_h2", "H2", "T3; F2"),
            _chapter_handoff("handoff_h3", "H3", "T4; F3"),
        ]
    ).to_csv(results / "thesis_source_review_chapter_handoff.csv", index=False)
    pd.DataFrame(
        [
            _chapter_check(check_idx, area, is_final_gate=(check_idx == 5))
            for area in ("H1", "H2", "H3")
            for check_idx in range(1, 7)
        ]
    ).to_csv(results / "thesis_chapter_source_review_checklist.csv", index=False)
    pd.DataFrame(
        [
            _drafting_check(check_idx, area, is_final_gate=(check_idx == 5))
            for area in ("H1", "H2", "H3")
            for check_idx in range(1, 7)
        ]
    ).to_csv(results / "thesis_h1_h2_h3_drafting_checklist.csv", index=False)
    pd.DataFrame(
        [
            _bounded_chapter_draft(check_idx, area)
            for area in ("H1", "H2", "H3")
            for check_idx in range(1, 7)
        ]
    ).to_csv(results / "thesis_h1_h2_h3_bounded_chapter_draft.csv", index=False)
    pd.DataFrame(
        [_source_gated_writing_pass(area) for area in ("H1", "H2", "H3")]
    ).to_csv(results / "thesis_h1_h2_h3_source_gated_writing_pass.csv", index=False)
    pd.DataFrame(
        [
            {
                "control_id": "agent_control_01",
                "current_activation_state": "future_documentation_only",
            },
            {
                "control_id": "agent_control_02",
                "current_activation_state": "future_deferred",
            },
        ]
    ).to_csv(results / "thesis_agent_pipeline_control_audit.csv", index=False)
    pd.DataFrame(
        [
            {"upgrade_id": "agent_upgrade_01", "current_status": "future_documentation_only"},
            {"upgrade_id": "agent_upgrade_02", "current_status": "future_deferred"},
        ]
    ).to_csv(results / "thesis_agent_pipeline_upgrade_plan.csv", index=False)
    pd.DataFrame(
        [
            _final_gate("final_gate_01_source_review", True, False, 3),
            _final_gate("final_gate_02_h1_h2_h3_drafting", True, False, 3),
            _final_gate("final_gate_03_result_package", True, False, 1),
            _final_gate("final_gate_04_swiss_result_mapping", True, False, 1),
            _final_gate("final_gate_05_monitor_appendix", True, False, 1),
            _final_gate("final_gate_06_future_agents", True, True, 0),
            _final_gate("final_gate_07_docx_render_qa", True, False, 1),
            _final_gate("final_gate_08_project_control", True, False, 0),
        ]
    ).to_csv(results / "thesis_final_gate_board.csv", index=False)

    pd.DataFrame(
        [
            {"deliverable_id": f"deliverable_{idx}", "path": f"docs/project/file_{idx}.md"}
            for idx in range(11)
        ]
    ).to_csv(results / "thesis_advisor_handoff_package.csv", index=False)
    pd.DataFrame([{"section_id": f"section_{idx}"} for idx in range(6)]).to_csv(
        results / "thesis_advisor_handoff_note.csv",
        index=False,
    )
    pd.DataFrame(
        [
            {"feedback_id": f"feedback_{idx}", "advisor_feedback_status": "pending_advisor_feedback"}
            for idx in range(8)
        ]
    ).to_csv(results / "thesis_advisor_feedback_log_template.csv", index=False)

    for relative in [
        "GOAL.md",
        "STATUS.md",
        "docs/project/WORK_LOG.md",
        "docs/project/DOZENTEN_UEBERGABE_TEXT.md",
        "docs/project/DOZENTEN_ABSPRACHE_CHECKLIST.md",
        "docs/project/DOZENTEN_FEEDBACK_LOG.md",
        "docs/research/THESIS_PROJECT_HIGHLEVEL_VIEW.md",
        "docs/research/THESIS_WORDING_GUARD.md",
        "docs/research/THESIS_AGENT_ASSISTANCE_PROTOCOL.md",
        "data/results/thesis_citation_readiness.csv",
        "data/results/thesis_table_figure_captions.csv",
        "data/results/thesis_core_results_table.csv",
        "data/results/swiss_referendum_10mio_latest_source_comparison.csv",
        "data/results/monitor_anomaly_review_summary.csv",
        "data/results/thesis_project_highlevel_view.csv",
        "data/results/thesis_agent_assistance_protocol.csv",
        "docs/project/THESIS_AGENT_PIPELINE_CONTROL_AUDIT.md",
        "docs/project/THESIS_H1_H2_H3_SOURCE_REVIEW_NOTES.md",
        "docs/project/THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md",
        "docs/project/THESIS_H1_H2_H3_MANUAL_SOURCE_REVIEW_EXECUTION_PASS.md",
        "docs/project/THESIS_SOURCE_REVIEW_PROGRESS_PROTOCOL.md",
        "docs/project/THESIS_METHOD_INTERPRETATION_SOURCE_COVERAGE.md",
        "docs/research/THESIS_H1_H2_H3_CORE_SECTIONS.md",
        "docs/project/THESIS_SOURCE_REVIEW_CHAPTER_HANDOFF.md",
        "docs/project/THESIS_CHAPTER_SOURCE_REVIEW_CHECKLIST.md",
        "docs/project/THESIS_H1_H2_H3_DRAFTING_CHECKLIST.md",
        "docs/research/THESIS_H1_H2_H3_BOUNDED_CHAPTER_DRAFT.md",
        "docs/research/THESIS_H1_H2_H3_SOURCE_GATED_WRITING_PASS.md",
        "docs/research/THESIS_AGENT_PIPELINE_UPGRADE_PLAN.md",
        "docs/project/THESIS_FINAL_GATE_BOARD.md",
    ]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")


def _evidence(evidence_id: str, item_type: str, readiness: str) -> dict[str, str]:
    return {
        "evidence_id": evidence_id,
        "item_type": item_type,
        "thesis_readiness": readiness,
        "primary_artifact": "data/results/thesis_core_results_table.csv",
        "literature_sources": "lit_a; lit_b",
    }


def _gate(gate_area: str, current_status: str) -> dict[str, str]:
    return {
        "gate_area": gate_area,
        "current_status": current_status,
    }


def _source_note(note_id: str, area: str, table: str, figure: str) -> dict[str, str]:
    return {
        "note_id": note_id,
        "thesis_area": area,
        "note_status": "pending_manual_source_review",
        "selected_table": table,
        "selected_figure": figure,
    }


def _source_coverage(evidence_id: str, area: str, source_id: str) -> dict[str, object]:
    return {
        "coverage_id": f"coverage_{evidence_id}_{source_id}",
        "evidence_id": evidence_id,
        "thesis_area": area,
        "item_type": "method" if evidence_id.startswith("method") else "interpretation",
        "thesis_readiness": "thesis_facing_ready",
        "source_id": source_id,
        "source_known_in_literature_index": True,
        "source_status": "skimmed",
        "source_relevance": "high",
        "final_citation_readiness": "needs_full_source_review_before_final_citation",
        "primary_artifact": "data/results/thesis_core_results_table.csv",
        "primary_artifact_exists": True,
        "supporting_artifact_count": 1,
        "supporting_artifact_exists_count": 1,
        "limitation_present": True,
        "coverage_status": "source_mapped_final_review_pending",
        "thesis_use_gate_de": "Draft nutzbar; keine finale Zitation ohne manuelle Source Review.",
    }


def _ledger(ledger_id: str, area: str) -> dict[str, object]:
    return {
        "ledger_id": ledger_id,
        "thesis_area": area,
        "review_progress_state": "pending_manual_review",
        "final_citation_ready": False,
        "source_status_change_allowed": False,
    }


def _manual_execution(
    execution_id: str,
    area: str,
    source_id: str,
    evidence_id: str,
) -> dict[str, object]:
    return {
        "execution_id": execution_id,
        "thesis_area": area,
        "source_id": source_id,
        "evidence_id": evidence_id,
        "source_known_in_literature_index": True,
        "primary_artifact_exists": True,
        "coverage_status": "source_mapped_final_review_pending",
        "source_status_change_allowed": False,
        "final_citation_ready": False,
        "ready_for_bounded_draft": True,
    }


def _final_gate(
    final_gate_id: str,
    draft_use_allowed: bool,
    final_submission_ready: bool,
    blocking_count: int,
) -> dict[str, object]:
    return {
        "final_gate_id": final_gate_id,
        "draft_use_allowed": draft_use_allowed,
        "final_submission_ready": final_submission_ready,
        "blocking_count": blocking_count,
    }


def _protocol(protocol_id: str, area: str) -> dict[str, str]:
    return {
        "protocol_id": protocol_id,
        "protocol_area": area,
        "current_state": "fixture_state",
        "deterministic_evidence_de": "Fixture evidence.",
    }


def _chapter_handoff(handoff_id: str, area: str, package_items: str) -> dict[str, object]:
    return {
        "handoff_id": handoff_id,
        "thesis_area": area,
        "coverage_status": "covered_artifact_source_package_ready",
        "source_review_rows": 1,
        "pending_review_rows": 1,
        "final_citation_ready_rows": 0,
        "result_package_items": package_items,
    }


def _chapter_check(check_idx: int, area: str, *, is_final_gate: bool) -> dict[str, object]:
    return {
        "checklist_id": f"check_{area.lower()}_{check_idx}",
        "thesis_area": area,
        "check_area": "final_citation_gate" if is_final_gate else "fixture_check",
        "completion_status": (
            "final_blocked_source_review_pending" if is_final_gate else "bounded_draft_ready"
        ),
        "ready_for_bounded_draft": True,
        "ready_for_final_submission": False,
    }


def _drafting_check(check_idx: int, area: str, *, is_final_gate: bool) -> dict[str, object]:
    return {
        "draft_check_id": f"draft_{area.lower()}_{check_idx}",
        "thesis_area": area,
        "draft_step": "source_review_and_citation_gate" if is_final_gate else "fixture_step",
        "completion_status": (
            "final_blocked_source_review_pending" if is_final_gate else "bounded_draft_ready"
        ),
        "ready_for_bounded_draft": True,
        "ready_for_final_submission": False,
    }


def _bounded_chapter_draft(check_idx: int, area: str) -> dict[str, object]:
    return {
        "chapter_draft_id": f"chapter_draft_{area.lower()}_{check_idx}",
        "thesis_area": area,
        "draft_step": f"draft_step_{check_idx}",
        "method_evidence_ids": f"method_{area.lower()}",
        "interpretation_evidence_ids": f"interpretation_{area.lower()}",
        "literature_source_ids": "lit_a",
        "deterministic_artifacts": "data/results/thesis_core_results_table.csv",
        "selected_tables": "T2",
        "selected_figures": "F1",
        "ready_for_bounded_draft": True,
        "ready_for_final_submission": False,
    }


def _source_gated_writing_pass(area: str) -> dict[str, object]:
    return {
        "writing_pass_id": f"writing_pass_{area.lower()}_source_gated",
        "thesis_area": area,
        "chapter_title_de": f"{area}: Fixture",
        "method_evidence_ids": f"method_{area.lower()}",
        "interpretation_evidence_ids": f"interpretation_{area.lower()}",
        "literature_source_ids": "lit_a",
        "deterministic_artifacts": "data/results/thesis_core_results_table.csv",
        "source_coverage_links": 1,
        "source_coverage_unique_sources": 1,
        "source_coverage_gap_rows": 0,
        "selected_tables": "T2",
        "selected_figures": "F1",
        "method_paragraph_de": "Method paragraph.",
        "result_paragraph_de": "Result paragraph.",
        "interpretation_paragraph_de": "Interpretation paragraph.",
        "table_figure_paragraph_de": "Table figure paragraph.",
        "source_gate_paragraph_de": "Source gate paragraph.",
        "future_agent_boundary_de": "Future-agent boundary.",
        "blocked_wording_de": "Blocked wording.",
        "full_chapter_draft_de": "Full chapter draft.",
        "writing_pass_status": "source_gated_bounded_draft_ready_final_source_review_pending",
        "ready_for_bounded_draft": True,
        "ready_for_final_submission": False,
    }
