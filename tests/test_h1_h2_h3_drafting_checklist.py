from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from operations.project.build_h1_h2_h3_drafting_checklist import (
    DRAFTING_COLUMNS,
    DRAFT_STEPS,
    generate_h1_h2_h3_drafting_checklist,
)


def test_generate_h1_h2_h3_drafting_checklist_writes_six_steps_per_chapter(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_h1_h2_h3_drafting_checklist(repo_root=tmp_path)

    checklist = pd.read_csv(result.checklist_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(checklist.columns) == DRAFTING_COLUMNS
    assert result.checklist_rows == 18
    assert result.bounded_draft_ready_rows == 18
    assert result.final_submission_ready_rows == 0
    assert result.final_blocked_rows == 3
    assert set(checklist["thesis_area"]) == {"H1", "H2", "H3"}
    for _, group in checklist.groupby("thesis_area"):
        assert tuple(group.sort_values("draft_order")["draft_step"]) == DRAFT_STEPS
    assert set(checklist["caption_labels"]) == {"tab:t2; fig:f1", "tab:t3; fig:f2", "tab:t4; fig:f3"}
    assert "H1-H2-H3 Drafting Checklist" in doc
    assert "Drafting rows: 18" in doc
    assert "Final submission ready rows: 0" in doc
    assert "Manual Source Review Follow-up Overview" in doc
    assert "Overview-/Ledger-Abgleich" in doc
    assert "Keine neue Kennzahl" in doc
    assert "Runtime-Agenten" in doc
    assert chr(223) not in doc


def test_generate_h1_h2_h3_drafting_checklist_rejects_missing_caption(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)
    captions = pd.read_csv(tmp_path / "data/results/thesis_table_figure_captions.csv")
    captions = captions[captions["package_id"] != "F3"]
    captions.to_csv(tmp_path / "data/results/thesis_table_figure_captions.csv", index=False)

    with pytest.raises(ValueError, match="Missing table/figure caption row"):
        generate_h1_h2_h3_drafting_checklist(repo_root=tmp_path)


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    results.mkdir(parents=True)
    pd.DataFrame(
        [
            _core("H1", "T2", "F1", "method_h1", "interpretation_h1"),
            _core("H2", "T3", "F2", "method_h2", "interpretation_h2"),
            _core("H3", "T4", "F3", "method_h3", "interpretation_h3"),
        ]
    ).to_csv(results / "thesis_h1_h2_h3_core_sections.csv", index=False)
    pd.DataFrame(
        [
            _handoff("H1", "T2; F1"),
            _handoff("H2", "T3; F2"),
            _handoff("H3", "T4; F3"),
        ]
    ).to_csv(results / "thesis_source_review_chapter_handoff.csv", index=False)
    pd.DataFrame(
        [
            _source_check("H1", idx, is_final_gate=idx == 5)
            for idx in range(1, 7)
        ]
        + [
            _source_check("H2", idx, is_final_gate=idx == 5)
            for idx in range(1, 7)
        ]
        + [
            _source_check("H3", idx, is_final_gate=idx == 5)
            for idx in range(1, 7)
        ]
    ).to_csv(results / "thesis_chapter_source_review_checklist.csv", index=False)
    pd.DataFrame(
        [
            _caption("T2", "tab:t2"),
            _caption("F1", "fig:f1"),
            _caption("T3", "tab:t3"),
            _caption("F2", "fig:f2"),
            _caption("T4", "tab:t4"),
            _caption("F3", "fig:f3"),
        ]
    ).to_csv(results / "thesis_table_figure_captions.csv", index=False)


def _core(
    area: str,
    table: str,
    figure: str,
    method_id: str,
    interpretation_id: str,
) -> dict[str, str]:
    return {
        "section_id": f"core_section_{area.lower()}",
        "hypothesis": area,
        "chapter_title_de": f"{area}: Kapitel",
        "method_evidence_ids": method_id,
        "interpretation_evidence_ids": interpretation_id,
        "literature_source_ids": f"lit_{area.lower()}",
        "deterministic_artifacts": "data/results/core.csv",
        "selected_tables": table,
        "selected_figures": figure,
        "draft_text_de": f"{area}: Draft seed mit Evidence IDs.",
        "thesis_ready_result_de": f"{area}: thesis-ready Resultat ohne neue Kennzahl.",
        "bounded_interpretation_de": f"{area}: bounded Interpretation.",
        "mandatory_limitation_de": f"{area}: Limitation.",
        "blocked_wording_de": "Kausalitaetsclaim",
    }


def _handoff(area: str, package_items: str) -> dict[str, str]:
    return {
        "handoff_id": f"handoff_{area.lower()}",
        "thesis_area": area,
        "result_package_items": package_items,
        "required_source_review_de": (
            f"{area}: Source-Gate offen; keine finale Zitation ohne Page-/Section-Note."
        ),
        "future_agent_boundary_de": (
            "Agentenstatus bleibt future_documentation_only mit bounded inputs und llm_audit_log."
        ),
    }


def _source_check(area: str, idx: int, *, is_final_gate: bool) -> dict[str, object]:
    is_literature_review = idx == 2
    check_area = "final_citation_gate" if is_final_gate else "literature_source_review" if is_literature_review else "fixture_check"
    source_artifact = "data/results/thesis_source_review_chapter_handoff.csv"
    required_evidence = f"{area}: fixture evidence."
    manual_action = "Fixture pruefen."
    if is_literature_review or is_final_gate:
        source_artifact = (
            "data/results/thesis_manual_source_review_followup_overview.csv; "
            f"data/results/thesis_{area.lower()}_manual_source_review_followup.csv"
        )
        required_evidence = (
            f"{area}: Manual Source Review Follow-up Overview; "
            "Overview-/Ledger-Abgleich pending."
        )
        manual_action = (
            "Manual Source Review Follow-up Overview pruefen und "
            "Overview-/Ledger-Abgleich dokumentieren."
        )
    return {
        "thesis_area": area,
        "check_area": check_area,
        "source_artifact": source_artifact,
        "completion_status": (
            "final_blocked_source_review_pending" if is_final_gate else "bounded_draft_ready"
        ),
        "required_evidence_de": required_evidence,
        "manual_action_de": manual_action,
        "ready_for_bounded_draft": True,
        "ready_for_final_submission": False,
    }


def _caption(package_id: str, thesis_label: str) -> dict[str, object]:
    return {
        "package_id": package_id,
        "thesis_label": thesis_label,
        "caption_de": f"{package_id}: Caption.",
        "source_note_de": f"{package_id}: Source Note.",
        "limitation_note_de": f"{package_id}: Limitation.",
        "include_in_core_package": True,
    }
