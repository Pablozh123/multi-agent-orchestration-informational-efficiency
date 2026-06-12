from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_thesis_drafting_sequence import (
    DRAFTING_COLUMNS,
    generate_thesis_drafting_sequence,
)


def test_generate_thesis_drafting_sequence_writes_ordered_steps(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_drafting_sequence(repo_root=tmp_path)

    sequence = pd.read_csv(result.sequence_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(sequence.columns) == DRAFTING_COLUMNS
    assert result.sequence_rows == 10
    assert sequence["priority_order"].tolist() == list(range(1, 11))
    assert sequence["workstream_id"].tolist()[0] == "work_01_source_review"
    assert sequence["workstream_id"].tolist()[-1] == "work_10_final_qa"
    assert "Thesis Drafting Sequence" in doc
    assert "Drafting steps: 10" in doc
    assert chr(223) not in doc


def test_thesis_drafting_sequence_keeps_final_and_future_gates_visible(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_drafting_sequence(repo_root=tmp_path)

    sequence = pd.read_csv(result.sequence_path)
    joined = "\n".join(sequence.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert "review_now_final_blocked" in joined
    assert "descriptive_only_final_blocked" in joined
    assert "future_work_only" in joined
    assert "keine runtime-agenten" in joined
    assert "keine roh" in joined
    assert "review-access bleibt pausiert" in joined
    assert "14. juni 2026" in joined


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs = root / "docs/project"
    results.mkdir(parents=True)
    docs.mkdir(parents=True)
    _write_required_artifacts(root)

    pd.DataFrame(
        [
            _work_row(1, "work_01_source_review", "theory_literature", "data/results/thesis_source_review_execution.csv"),
            _work_row(2, "work_02_method_chapters", "chapters_01_to_03", "data/results/thesis_chapter_source_bindings.csv"),
            _work_row(3, "work_03_h1_results", "h1_results", "data/results/thesis_core_results_table.csv"),
            _work_row(4, "work_04_h2_h3_results", "h2_h3_results", "data/results/thesis_core_results_table.csv"),
            _work_row(5, "work_05_table_figure_integration", "results_and_appendix", "data/results/thesis_table_figure_captions.csv"),
            _work_row(6, "work_06_monitor_appendix", "appendix_or_discussion", "data/results/monitor_anomaly_review_summary.csv"),
            _work_row(7, "work_07_swiss_result_gate", "discussion_pending_final_result", "data/results/swiss_referendum_10mio_latest_source_comparison.csv"),
            _work_row(8, "work_08_agent_outlook", "future_work", "data/results/thesis_agent_future_work_handoff.csv"),
            _work_row(9, "work_09_advisor_iteration", "project_management", "data/results/thesis_advisor_handoff_package.csv"),
            _work_row(10, "work_10_final_qa", "whole_thesis", "STATUS.md; docs/project/WORK_LOG.md"),
        ]
    ).to_csv(results / "thesis_next_work_plan.csv", index=False)

    pd.DataFrame(
        [
            _gate("advisor_handoff", "ready_for_advisor_discussion", "data/results/thesis_advisor_handoff_package.csv", 7),
            _gate("chapter_source_mapping", "ready_for_draft", "data/results/thesis_chapter_source_bindings.csv", 8),
            _gate("source_review", "final_blocked_source_review", "data/results/thesis_source_review_execution.csv", 2),
            _gate("h1_h2_h3_results", "ready_for_bounded_result_draft", "data/results/thesis_core_results_table.csv", 3),
            _gate("table_figure_package", "ready_for_draft_integration", "data/results/thesis_table_figure_captions.csv", 9),
            _gate("monitor_appendix", "appendix_only_pending_human_review", "data/results/monitor_anomaly_review_summary.csv", 1),
            _gate("swiss_result_gate", "final_blocked_official_result", "data/results/swiss_referendum_10mio_latest_source_comparison.csv", 1),
            _gate("agent_future_work", "deferred_future_work_only", "data/results/thesis_agent_future_work_handoff.csv", 7),
            _gate("final_qa", "pending_after_draft", "STATUS.md; docs/project/WORK_LOG.md", 2),
        ]
    ).to_csv(results / "thesis_submission_readiness_board.csv", index=False)

    pd.DataFrame(
        [
            {"chapter_id": "ch_01_intro", "source_ids": "source_1"},
            {"chapter_id": "ch_02_theory", "source_ids": "source_2"},
        ]
    ).to_csv(results / "thesis_chapter_source_bindings.csv", index=False)

    pd.DataFrame(
        [
            {"review_stage": "review_now_priority_1"},
            {"review_stage": "review_now_priority_1"},
            {"review_stage": "metadata_only_blocked"},
        ]
    ).to_csv(results / "thesis_source_review_execution.csv", index=False)

    pd.DataFrame(
        [
            {"include_in_core_package": True},
            {"include_in_core_package": True},
            {"include_in_core_package": False},
        ]
    ).to_csv(results / "thesis_table_figure_captions.csv", index=False)


def _write_required_artifacts(root: Path) -> None:
    paths = [
        "data/results/thesis_source_review_execution.csv",
        "data/results/thesis_chapter_source_bindings.csv",
        "data/results/thesis_core_results_table.csv",
        "data/results/thesis_table_figure_captions.csv",
        "data/results/monitor_anomaly_review_summary.csv",
        "data/results/swiss_referendum_10mio_latest_source_comparison.csv",
        "data/results/thesis_agent_future_work_handoff.csv",
        "data/results/thesis_advisor_handoff_package.csv",
        "STATUS.md",
        "docs/project/WORK_LOG.md",
    ]
    for relative in paths:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")


def _work_row(
    priority_order: int,
    workstream_id: str,
    thesis_section: str,
    current_artifact: str,
) -> dict[str, object]:
    return {
        "workstream_id": workstream_id,
        "priority_order": priority_order,
        "thesis_section": thesis_section,
        "current_artifact": current_artifact,
        "next_action": f"Write {workstream_id}.",
        "done_when": f"{workstream_id} has artifact-linked draft evidence.",
        "blocked_until": "No blocker for draft; final gates remain visible.",
        "guardrail": "fixture guardrail",
    }


def _gate(
    gate_area: str,
    current_status: str,
    primary_artifact: str,
    evidence_or_control_count: int,
) -> dict[str, object]:
    return {
        "gate_area": gate_area,
        "current_status": current_status,
        "primary_artifact": primary_artifact,
        "evidence_or_control_count": evidence_or_control_count,
        "next_action_de": f"Gate action for {gate_area}.",
        "blocker_or_limit_de": f"Gate limit for {gate_area}.",
    }
