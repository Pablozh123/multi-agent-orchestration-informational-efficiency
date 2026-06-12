from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from operations.project.build_chapter_source_review_checklist import (
    CHECK_AREAS,
    CHECKLIST_COLUMNS,
    generate_chapter_source_review_checklist,
)


def test_generate_chapter_source_review_checklist_writes_six_checks_per_chapter(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_chapter_source_review_checklist(repo_root=tmp_path)

    checklist = pd.read_csv(result.checklist_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(checklist.columns) == CHECKLIST_COLUMNS
    assert result.checklist_rows == 18
    assert result.bounded_draft_ready_rows == 18
    assert result.final_submission_ready_rows == 0
    assert result.final_blocked_rows == 3
    assert set(checklist["thesis_area"]) == {"H1", "H2", "H3"}
    for _, group in checklist.groupby("thesis_area"):
        assert tuple(group.sort_values("check_order")["check_area"]) == CHECK_AREAS
    assert "Chapter Source Review Checklist" in doc
    assert "Checklist rows: 18" in doc
    assert "Final submission ready rows: 0" in doc
    assert "Keine finale Zitation" in doc
    assert "Runtime-Agenten" in doc
    assert chr(223) not in doc


def test_generate_chapter_source_review_checklist_rejects_unexpected_area(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)
    handoff = pd.read_csv(tmp_path / "data/results/thesis_source_review_chapter_handoff.csv")
    handoff.loc[handoff["thesis_area"] == "H3", "thesis_area"] = "H4"
    handoff.to_csv(tmp_path / "data/results/thesis_source_review_chapter_handoff.csv", index=False)

    with pytest.raises(ValueError, match="Unexpected thesis area"):
        generate_chapter_source_review_checklist(repo_root=tmp_path)


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    results.mkdir(parents=True)
    pd.DataFrame(
        [
            _handoff("H1", "method_h1", "interpretation_h1", "lit_a; lit_b", "T2; F1", 2),
            _handoff("H2", "method_h2", "interpretation_h2", "lit_c", "T3; F2", 2),
            _handoff("H3", "method_h3", "interpretation_h3", "lit_d", "T4; F3", 2),
        ]
    ).to_csv(results / "thesis_source_review_chapter_handoff.csv", index=False)


def _handoff(
    area: str,
    method_ids: str,
    interpretation_ids: str,
    literature_ids: str,
    result_items: str,
    review_rows: int,
) -> dict[str, object]:
    return {
        "handoff_id": f"handoff_{area.lower()}",
        "thesis_area": area,
        "method_evidence_ids": method_ids,
        "interpretation_evidence_ids": interpretation_ids,
        "literature_source_ids": literature_ids,
        "selected_tables": result_items.split(";")[0].strip(),
        "selected_figures": result_items.split(";")[1].strip(),
        "mapped_method_count": 1,
        "mapped_interpretation_count": 1,
        "literature_source_count": len(literature_ids.split(";")),
        "source_review_rows": review_rows,
        "pending_review_rows": review_rows,
        "final_citation_ready_rows": 0,
        "result_package_items": result_items,
        "coverage_status": "covered_artifact_source_package_ready",
        "chapter_write_status": "bounded_draft_ready_final_source_review_pending",
        "required_source_review_de": (
            f"{area}: {review_rows} Source-Review-Zeilen; keine finale Zitation "
            "ohne manuelle Review."
        ),
        "mandatory_limitation_de": f"{area} Limitation.",
        "blocked_wording_de": "Kausalitaetsclaim",
        "future_agent_boundary_de": (
            "Agentenstatus bleibt `future_documentation_only`: keine Runtime-Agenten, "
            "max 50 rows und llm_audit_log."
        ),
    }
