from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_advisor_handoff_package import (
    PACKAGE_COLUMNS,
    generate_advisor_handoff_package,
)


def test_generate_advisor_handoff_package_writes_ordered_deliverables(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_advisor_handoff_package(repo_root=tmp_path)

    package = pd.read_csv(result.package_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(package.columns) == PACKAGE_COLUMNS
    assert result.package_rows == 12
    assert package["deliverable_id"].tolist()[0] == "advisor_handoff_note"
    assert package["deliverable_id"].tolist()[-1] == "consolidation_index"
    assert "Thesis Advisor Handoff Package" in doc
    assert "Package deliverables: 12" in doc
    assert "Source-Gated H1-H2-H3 Drafting Sequence" in doc
    assert "15 Absatzschritte" in doc
    assert "23 Manual Source Review Zeilen" in doc
    assert "manual_source_review_followup_overview" in package["deliverable_id"].tolist()
    assert chr(223) not in doc


def test_advisor_handoff_package_preserves_boundaries(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_advisor_handoff_package(repo_root=tmp_path)

    package = pd.read_csv(result.package_path)
    joined = "\n".join(package.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert "dozentenbericht_ba_thesis.docx" in joined
    assert "dozenten_uebergabe_text.md" in joined
    assert "dozenten_feedback_log.md" in joined
    assert "thesis_manual_source_review_followup_overview.md" in joined
    assert "23 offene review-zeilen" in joined
    assert "review-access bleibt pausiert" in joined
    assert "source-gated h1-h2-h3 drafting sequence" in joined
    assert "nicht final-submission-ready" in joined
    assert "quellenstatus nicht automatisch hochstufen" in joined
    assert "keine runtime-agenten" in joined
    assert "thesis-facing claims" in joined


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs = root / "docs/project"
    results.mkdir(parents=True)
    docs.mkdir(parents=True)

    paths = [
        "docs/project/DOZENTEN_UEBERGABE_TEXT.md",
        "docs/project/dozentenbericht_ba_thesis.docx",
        "docs/project/DOZENTEN_ABSPRACHE_CHECKLIST.md",
        "docs/project/THESIS_SUBMISSION_READINESS_BOARD.md",
        "docs/project/THESIS_DRAFTING_SEQUENCE.md",
        "docs/project/THESIS_EXECUTION_CHECKLIST.md",
        "docs/project/THESIS_CHAPTER_SOURCE_BINDINGS.md",
        "docs/project/THESIS_SOURCE_REVIEW_EXECUTION.md",
        "docs/project/THESIS_MANUAL_SOURCE_REVIEW_FOLLOWUP_OVERVIEW.md",
        "docs/project/THESIS_AGENT_FUTURE_WORK_HANDOFF.md",
        "docs/project/DOZENTEN_FEEDBACK_LOG.md",
        "docs/project/THESIS_CONSOLIDATION_INDEX.md",
    ]
    for relative in paths:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")

    pd.DataFrame(
        [
            {"artifact_id": f"idx_{index:02d}", "path": path}
            for index, path in enumerate(paths, start=1)
        ]
    ).to_csv(results / "thesis_consolidation_index.csv", index=False)

    pd.DataFrame(
        [
            _followup_overview_row("H1", 10, 4, 10, 0),
            _followup_overview_row("H2", 5, 3, 5, 0),
            _followup_overview_row("H3", 8, 4, 8, 0),
        ]
    ).to_csv(results / "thesis_manual_source_review_followup_overview.csv", index=False)

    pd.DataFrame(
        [
            _source_gated_row("H1", index, 10, 10, 0)
            for index in range(1, 6)
        ]
        + [
            _source_gated_row("H2", index, 5, 5, 0)
            for index in range(1, 6)
        ]
        + [
            _source_gated_row("H3", index, 8, 8, 0)
            for index in range(1, 6)
        ]
    ).to_csv(results / "thesis_h1_h2_h3_source_gated_thesis_drafting_pass.csv", index=False)


def _source_gated_row(
    thesis_area: str,
    row_index: int,
    manual_execution_rows: int,
    manual_pending_rows: int,
    manual_final_ready_rows: int,
) -> dict[str, object]:
    return {
        "thesis_area": thesis_area,
        "draft_step_order": row_index,
        "manual_execution_rows": manual_execution_rows,
        "manual_execution_pending_rows": manual_pending_rows,
        "manual_execution_final_ready_rows": manual_final_ready_rows,
        "ready_for_bounded_draft": True,
        "ready_for_final_submission": False,
    }


def _followup_overview_row(
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
    }
