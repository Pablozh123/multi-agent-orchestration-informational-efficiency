from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_advisor_source_review_followup import (
    FOLLOWUP_COLUMNS,
    generate_advisor_source_review_followup,
)


def test_generate_advisor_source_review_followup_writes_ordered_plan(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_advisor_source_review_followup(repo_root=tmp_path)

    followup = pd.read_csv(result.followup_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(followup.columns) == FOLLOWUP_COLUMNS
    assert result.followup_rows == 8
    assert result.manual_source_review_rows == 23
    assert result.pending_source_review_rows == 23
    assert result.final_ready_rows == 0
    assert followup["followup_order"].tolist() == list(range(1, 9))
    assert "Advisor Source Review Follow-up" in doc
    assert "Manual Source Review rows: 23" in doc
    assert "Manual Source Review final-ready rows: 0" in doc
    assert "Manual Source Review Follow-up Overview" in doc
    assert "23 offenen H1-H2-H3 Review-Zeilen" in doc
    assert "followup_03_h1_manual_source_review" in doc
    assert "followup_08_keep_agents_future_work" in doc
    assert chr(223) not in doc


def test_advisor_source_review_followup_keeps_manual_and_agent_boundaries(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_advisor_source_review_followup(repo_root=tmp_path)

    followup = pd.read_csv(result.followup_path)
    joined = "\n".join(followup.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert "pending_advisor_feedback" in joined
    assert "source review" in joined
    assert "manual source review follow-up overview" in joined
    assert "23 offene h1-h2-h3 review-zeilen" in joined
    assert "page-/section-note" in joined
    assert "claim-support" in joined
    assert "blocked-wording" in joined
    assert "citation-use" in joined
    assert "wenige gute tabellen/figuren" in joined
    assert "keine quellenstatus-hochstufung" in joined
    assert "keine finale zitation" in joined
    assert "review-access" in joined
    assert "keine runtime-agenten" in joined
    assert "llm_audit_log" in joined
    assert "keine rohartefakt-dumps" in joined
    assert "h1: 10 manual source review rows" in joined
    assert "h2: 5 manual source review rows" in joined
    assert "h3: 8 manual source review rows" in joined
    assert "9 eindeutige quellen" in joined


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs = root / "docs/project"
    research = root / "docs/research"
    results.mkdir(parents=True)
    docs.mkdir(parents=True)
    research.mkdir(parents=True)
    _write_required_artifacts(root)

    pd.DataFrame(
        [
            {
                "advisor_question_id": question_id,
                "topic": topic,
                "feedback_status": "pending_advisor_feedback",
                "required_evidence_check_de": "Jede Methode und jede Interpretation pruefen.",
                "small_commit_scope_de": f"docs: integrate {question_id}",
                "final_gate_de": "Finale Zitation erst nach Source Review.",
                "guardrail_de": "Keine Runtime-Agenten.",
            }
            for question_id, topic in [
                ("advisor_q01_h1_wording", "H1 bounded wording"),
                ("advisor_q02_source_depth", "Source review depth"),
                ("advisor_q03_h2_h3_scope", "H2/H3 scope"),
                ("advisor_q04_table_figure_package", "Tables and figures"),
                ("advisor_q05_monitor_appendix", "Monitor appendix"),
                ("advisor_q06_swiss_gate", "Swiss result gate"),
                ("advisor_q07_agent_outlook", "Agent outlook"),
                ("advisor_q08_final_qa", "Final QA"),
            ]
        ]
    ).to_csv(results / "thesis_advisor_feedback_integration_checklist.csv", index=False)

    pd.DataFrame(
        [
            _execution_row("H1", index)
            for index in range(1, 11)
        ]
        + [
            _execution_row("H2", index)
            for index in range(1, 6)
        ]
        + [
            _execution_row("H3", index)
            for index in range(1, 9)
        ]
    ).to_csv(results / "thesis_h1_h2_h3_manual_source_review_execution_pass.csv", index=False)

    pd.DataFrame(
        [
            _overview_row("H1", 10, 4, 10, 0),
            _overview_row("H2", 5, 3, 5, 0),
            _overview_row("H3", 8, 4, 8, 0),
        ]
    ).to_csv(results / "thesis_manual_source_review_followup_overview.csv", index=False)

    pd.DataFrame(
        [
            _final_gate("source_review", False, 23),
            _final_gate("h1_h2_h3_drafting", False, 3),
            _final_gate("result_package", False, 1),
            _final_gate("future_agents", True, 0),
        ]
    ).to_csv(results / "thesis_final_gate_board.csv", index=False)

    pd.DataFrame(
        [
            _package_row("T1", "table", True, "traceable"),
            _package_row("T2", "table", True, "traceable"),
            _package_row("T3", "table", True, "traceable"),
            _package_row("T4", "table", True, "traceable"),
            _package_row("T5", "table", True, "traceable"),
            _package_row("F1", "figure", True, "traceable"),
            _package_row("F2", "figure", True, "traceable"),
            _package_row("F3", "figure", True, "traceable"),
            _package_row("F4", "figure", True, "traceable"),
            _package_row("A1", "table", False, "traceable"),
        ]
    ).to_csv(results / "thesis_result_package_traceability.csv", index=False)

    pd.DataFrame(
        [
            {"upgrade_id": f"agent_{index}", "current_status": status}
            for index, status in enumerate(
                [
                    "future_documentation_only",
                    "future_documentation_only",
                    "future_documentation_only",
                    "future_documentation_only",
                    "future_documentation_only",
                    "future_documentation_only",
                    "future_deferred",
                ],
                start=1,
            )
        ]
    ).to_csv(results / "thesis_agent_pipeline_upgrade_plan.csv", index=False)


def _write_required_artifacts(root: Path) -> None:
    paths = [
        "docs/project/DOZENTEN_FEEDBACK_LOG.md",
        "docs/project/DOZENTEN_FEEDBACK_INTEGRATION_CHECKLIST.md",
        "docs/project/THESIS_SOURCE_REVIEW_PROGRESS_PROTOCOL.md",
        "docs/project/THESIS_MANUAL_SOURCE_REVIEW_FOLLOWUP_OVERVIEW.md",
        "docs/project/THESIS_FINAL_GATE_BOARD.md",
        "docs/project/THESIS_H1_H2_H3_MANUAL_SOURCE_REVIEW_EXECUTION_PASS.md",
        "docs/project/THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md",
        "docs/project/THESIS_AGENT_PIPELINE_CONTROL_AUDIT.md",
        "docs/research/THESIS_CHAPTER_DRAFT.md",
        "docs/research/THESIS_TABLE_FIGURE_CAPTIONS.md",
        "docs/research/THESIS_AGENT_PIPELINE_UPGRADE_PLAN.md",
        "STATUS.md",
        "docs/project/WORK_LOG.md",
        "data/results/thesis_advisor_feedback_integration_checklist.csv",
        "data/results/thesis_h1_h2_h3_manual_source_review_execution_pass.csv",
        "data/results/thesis_manual_source_review_followup_overview.csv",
        "data/results/thesis_final_gate_board.csv",
        "data/results/thesis_result_package_traceability.csv",
        "data/results/thesis_agent_pipeline_upgrade_plan.csv",
    ]
    for relative in paths:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")


def _execution_row(thesis_area: str, index: int) -> dict[str, object]:
    return {
        "execution_id": f"manual_exec_{thesis_area}_{index}",
        "thesis_area": thesis_area,
        "source_id": _source_id(thesis_area, index),
        "current_review_status": "pending_manual_review",
        "final_citation_ready": False,
        "ready_for_bounded_draft": True,
        "ready_for_final_submission": False,
        "source_status_change_allowed": False,
    }


def _source_id(thesis_area: str, index: int) -> str:
    if thesis_area == "H1":
        if index <= 3:
            return "lit_brier_001"
        if index <= 5:
            return "lit_dm_001"
        if index <= 7:
            return "lit_emh_001"
        return "zotero_poly_002"
    if thesis_area == "H2":
        if index <= 2:
            return "lit_emh_001"
        if index <= 4:
            return "lit_eventstudy_001"
        return "zotero_poly_001"
    if index <= 2:
        return "lit_granger_001"
    if index <= 4:
        return "zotero_poly_001"
    if index <= 7:
        return "zotero_poly_005"
    return "zotero_poly_007"


def _overview_row(
    slice_id: str,
    review_rows: int,
    unique_sources: int,
    pending_rows: int,
    final_ready_rows: int,
) -> dict[str, object]:
    return {
        "slice_id": slice_id,
        "review_rows": review_rows,
        "unique_sources": unique_sources,
        "pending_rows": pending_rows,
        "final_ready_rows": final_ready_rows,
        "manual_gate_de": "Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use.",
        "guardrail_de": "Keine Quellenstatus-Hochstufung und keine Runtime-Agenten.",
    }


def _final_gate(gate_area: str, final_submission_ready: bool, blocking_count: int) -> dict[str, object]:
    return {
        "gate_area": gate_area,
        "draft_use_allowed": True,
        "final_submission_ready": final_submission_ready,
        "blocking_count": blocking_count,
        "required_next_action_de": "Gate pruefen.",
    }


def _package_row(
    package_id: str,
    package_type: str,
    include_in_core_package: bool,
    package_traceability_status: str,
) -> dict[str, object]:
    return {
        "package_id": package_id,
        "package_type": package_type,
        "include_in_core_package": include_in_core_package,
        "package_traceability_status": package_traceability_status,
    }
