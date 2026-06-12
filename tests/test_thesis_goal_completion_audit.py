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


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs_project = root / "docs/project"
    docs_research = root / "docs/research"
    results.mkdir(parents=True)
    docs_project.mkdir(parents=True)
    docs_research.mkdir(parents=True)

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
