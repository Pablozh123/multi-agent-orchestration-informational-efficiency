from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_submission_readiness_board import (
    READINESS_COLUMNS,
    generate_submission_readiness_board,
)


def test_generate_submission_readiness_board_writes_gates(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_submission_readiness_board(repo_root=tmp_path)

    board = pd.read_csv(result.board_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(board.columns) == READINESS_COLUMNS
    assert result.board_rows == 9
    assert "Thesis Submission Readiness Board" in doc
    assert "Readiness gates: 9" in doc
    assert "final_blocked_source_review" in doc
    assert chr(223) not in doc


def test_submission_readiness_board_keeps_final_blockers_visible(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_submission_readiness_board(repo_root=tmp_path)

    board = pd.read_csv(result.board_path)
    joined = "\n".join(board.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert "final_blocked_source_review" in joined
    assert "post_result_mapped_source_review_pending" in joined
    assert "keine runtime-agenten" in joined
    assert "soffice" in joined
    assert "keine roh" in joined
    assert "human review" in joined


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs = root / "docs/project"
    results.mkdir(parents=True)
    docs.mkdir(parents=True)
    _write_required_artifacts(root)

    pd.DataFrame(
        [{"deliverable_id": f"deliverable_{index}", "path": f"docs/project/file_{index}.md"} for index in range(7)]
    ).to_csv(results / "thesis_advisor_handoff_package.csv", index=False)

    pd.DataFrame(
        [
            {"review_stage": "review_now_priority_1"},
            {"review_stage": "metadata_only_blocked"},
        ]
    ).to_csv(results / "thesis_source_review_execution.csv", index=False)

    pd.DataFrame(
        [
            {"chapter_id": "ch_01_intro", "source_ids": "source_1"},
            {"chapter_id": "ch_02_theory", "source_ids": "source_2"},
        ]
    ).to_csv(results / "thesis_chapter_source_bindings.csv", index=False)

    pd.DataFrame(
        [
            {"status": "future_documentation_only"},
            {"status": "future_deferred"},
        ]
    ).to_csv(results / "thesis_agent_future_work_handoff.csv", index=False)


def _write_required_artifacts(root: Path) -> None:
    paths = [
        "data/results/thesis_advisor_handoff_package.csv",
        "data/results/thesis_chapter_source_bindings.csv",
        "data/results/thesis_source_review_execution.csv",
        "data/results/thesis_core_results_table.csv",
        "data/results/thesis_table_figure_captions.csv",
        "data/results/monitor_anomaly_review_summary.csv",
        "data/results/swiss_referendum_10mio_final_case_study.csv",
        "data/results/thesis_agent_future_work_handoff.csv",
        "STATUS.md",
        "docs/project/WORK_LOG.md",
    ]
    for relative in paths:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")
