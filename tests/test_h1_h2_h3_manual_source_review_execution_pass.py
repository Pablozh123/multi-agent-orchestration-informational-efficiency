from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from operations.project.build_h1_h2_h3_manual_source_review_execution_pass import (
    EXECUTION_PASS_COLUMNS,
    generate_h1_h2_h3_manual_source_review_execution_pass,
)


def test_generate_manual_source_review_execution_pass_writes_ordered_rows(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_h1_h2_h3_manual_source_review_execution_pass(repo_root=tmp_path)

    execution = pd.read_csv(result.execution_pass_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(execution.columns) == EXECUTION_PASS_COLUMNS
    assert result.execution_rows == 4
    assert result.h1_rows == 2
    assert result.h2_rows == 1
    assert result.h3_rows == 1
    assert result.unique_source_rows == 3
    assert result.final_citation_ready_rows == 0
    assert execution["execution_order"].tolist() == [1, 2, 3, 4]
    assert execution["thesis_area"].tolist() == ["H1", "H1", "H2", "H3"]
    assert execution.iloc[0]["item_type"] == "method"
    assert execution.iloc[1]["item_type"] == "interpretation"
    assert execution["source_known_in_literature_index"].map(_as_bool).all()
    assert execution["primary_artifact_exists"].map(_as_bool).all()
    assert not execution["source_status_change_allowed"].map(_as_bool).any()
    assert not execution["ready_for_final_submission"].map(_as_bool).any()
    assert execution["ready_for_bounded_draft"].map(_as_bool).all()
    assert set(execution["coverage_status"]) == {"source_mapped_final_review_pending"}
    assert "Manual Source Review Output" in execution.iloc[0]["required_reviewer_output_de"]
    assert "Page-/Section-Note" in execution.iloc[0]["manual_execution_instruction_de"]
    assert "max 50 rows" in execution.iloc[0]["manual_execution_instruction_de"]
    assert "H1-H2-H3 Manual Source Review Execution Pass" in doc
    assert "Execution rows: 4" in doc
    assert "Unique sources: 3" in doc
    assert "batch_01_h1_forecast_quality_source_review: 2 rows" in doc
    assert "keine finale Zitation" in doc
    assert "llm_audit_log" in doc
    assert chr(223) not in doc


def test_generate_manual_source_review_execution_pass_rejects_missing_coverage(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)
    coverage = pd.read_csv(tmp_path / "data/results/thesis_method_interpretation_source_coverage.csv")
    coverage = coverage[coverage["evidence_id"] != "interpretation_h1"]
    coverage.to_csv(
        tmp_path / "data/results/thesis_method_interpretation_source_coverage.csv",
        index=False,
    )

    with pytest.raises(ValueError, match="missing source coverage row"):
        generate_h1_h2_h3_manual_source_review_execution_pass(repo_root=tmp_path)


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    results.mkdir(parents=True)

    notes = [
        _note("note_h1_method", "H1", "source_a", "method_h1", "method", "T2", "F1"),
        _note(
            "note_h1_interpretation",
            "H1",
            "source_a",
            "interpretation_h1",
            "interpretation",
            "T2",
            "F1",
        ),
        _note("note_h2_method", "H2", "source_b", "method_h2", "method", "T3", "F2"),
        _note("note_h3_method", "H3", "source_c", "method_h3", "method", "T4", "F3"),
    ]
    pd.DataFrame(notes).to_csv(
        results / "thesis_h1_h2_h3_source_review_notes.csv",
        index=False,
    )
    pd.DataFrame(
        [
            _ledger("ledger_h1_method", "note_h1_method"),
            _ledger("ledger_h1_interpretation", "note_h1_interpretation"),
            _ledger("ledger_h2_method", "note_h2_method"),
            _ledger("ledger_h3_method", "note_h3_method"),
        ]
    ).to_csv(results / "thesis_source_review_progress_ledger.csv", index=False)
    pd.DataFrame(
        [
            _decision("source_a", "method_h1", "H1", "method", 1),
            _decision("source_a", "interpretation_h1", "H1", "interpretation", 1),
            _decision("source_b", "method_h2", "H2", "method", 2),
            _decision("source_c", "method_h3", "H3", "method", 3),
        ]
    ).to_csv(results / "thesis_source_review_decision_packets.csv", index=False)
    pd.DataFrame(
        [
            _source_access("source_a", "Source A"),
            _source_access("source_b", "Source B"),
            _source_access("source_c", "Source C"),
        ]
    ).to_csv(results / "thesis_source_access_audit.csv", index=False)
    pd.DataFrame(
        [
            _coverage("source_a", "method_h1"),
            _coverage("source_a", "interpretation_h1"),
            _coverage("source_b", "method_h2"),
            _coverage("source_c", "method_h3"),
        ]
    ).to_csv(results / "thesis_method_interpretation_source_coverage.csv", index=False)
    pd.DataFrame(
        [
            _handoff("H1", "H1: Kapitel", 2),
            _handoff("H2", "H2: Kapitel", 1),
            _handoff("H3", "H3: Kapitel", 1),
        ]
    ).to_csv(results / "thesis_source_review_chapter_handoff.csv", index=False)
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


def _note(
    note_id: str,
    area: str,
    source_id: str,
    evidence_id: str,
    item_type: str,
    selected_table: str,
    selected_figure: str,
) -> dict[str, object]:
    return {
        "note_id": note_id,
        "thesis_area": area,
        "section_id": f"core_section_{area.lower()}",
        "source_id": source_id,
        "evidence_id": evidence_id,
        "item_type": item_type,
        "selected_table": selected_table,
        "selected_figure": selected_figure,
        "deterministic_artifact": "data/results/thesis_core_results_table.csv",
        "access_route": "external_locator_review",
        "manual_locator_task_de": "Quelle manuell oeffnen und passende Page-/Section-Note eintragen.",
        "review_focus_de": f"{area}: Source Review Fokus fuer {evidence_id}.",
        "bounded_claim_check_de": "Claim nur gegen deterministisches Artefakt und Literatur pruefen.",
        "blocked_wording_check_de": "Blocked-Wording pruefen.",
        "do_not_claim_de": (
            "Keine Quellenstatus-Hochstufung, keine finale Zitation und keine "
            "thesis-facing Claims ohne manuelle Entscheidung."
        ),
        "next_action_de": "Source Review manuell starten.",
    }


def _ledger(ledger_id: str, note_id: str) -> dict[str, object]:
    return {
        "ledger_id": ledger_id,
        "note_id": note_id,
        "review_status": "pending_manual_review",
        "claim_support_decision": "pending",
        "blocked_wording_check": "pending",
        "citation_use_decision": "blocked_pending_manual_review",
        "review_progress_state": "pending_manual_review",
        "source_status_change_allowed": False,
        "final_citation_ready": False,
    }


def _decision(
    source_id: str,
    evidence_id: str,
    area: str,
    item_type: str,
    source_priority_order: int,
) -> dict[str, object]:
    return {
        "source_id": source_id,
        "evidence_id": evidence_id,
        "thesis_area": area,
        "item_type": item_type,
        "source_priority_order": source_priority_order,
        "final_citation_gate": "full_source_review_required_before_final_citation",
        "required_manual_decision_de": (
            "Manuelle Full-Source-Review: Page-/Section-Note, Claim-Support "
            "und Blocked-Wording-Check."
        ),
    }


def _source_access(source_id: str, source_title: str) -> dict[str, str]:
    return {
        "source_id": source_id,
        "source_title": source_title,
        "source_status": "skimmed",
        "review_source_locator": "https://example.invalid/source",
    }


def _coverage(source_id: str, evidence_id: str) -> dict[str, object]:
    return {
        "evidence_id": evidence_id,
        "source_id": source_id,
        "source_known_in_literature_index": True,
        "source_relevance": "high",
        "primary_artifact_exists": True,
        "coverage_status": "source_mapped_final_review_pending",
    }


def _handoff(area: str, chapter_title: str, pending_rows: int) -> dict[str, object]:
    return {
        "thesis_area": area,
        "chapter_title_de": chapter_title,
        "pending_review_rows": pending_rows,
    }


def _caption(package_id: str, label: str) -> dict[str, object]:
    return {
        "package_id": package_id,
        "thesis_label": label,
        "caption_de": f"Caption fuer {package_id}.",
        "include_in_core_package": True,
    }


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"
