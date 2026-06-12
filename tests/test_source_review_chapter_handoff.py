from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from operations.project.build_source_review_chapter_handoff import (
    HANDOFF_COLUMNS,
    generate_source_review_chapter_handoff,
)


def test_generate_source_review_chapter_handoff_writes_h1_h2_h3_rows(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_source_review_chapter_handoff(repo_root=tmp_path)

    handoff = pd.read_csv(result.handoff_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(handoff.columns) == HANDOFF_COLUMNS
    assert result.handoff_rows == 3
    assert result.source_review_rows == 6
    assert result.pending_review_rows == 6
    assert result.final_citation_ready_rows == 0
    assert set(handoff["thesis_area"]) == {"H1", "H2", "H3"}
    assert handoff["coverage_status"].eq("covered_artifact_source_package_ready").all()
    assert handoff["chapter_write_status"].eq(
        "bounded_draft_ready_final_source_review_pending"
    ).all()
    assert "Source Review Chapter Handoff" in doc
    assert "Chapter handoff rows: 3" in doc
    assert "Selected result items: T2; F1; T3; F2; T4; F3" in doc
    assert "Keine finale Zitation" in doc
    assert "Runtime-Agenten" in doc
    assert chr(223) not in doc


def test_generate_source_review_chapter_handoff_rejects_missing_package_item(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)
    package = pd.read_csv(tmp_path / "data/results/thesis_result_package_traceability.csv")
    package = package[package["package_id"] != "F3"]
    package.to_csv(tmp_path / "data/results/thesis_result_package_traceability.csv", index=False)

    with pytest.raises(ValueError, match="package id missing traceability row"):
        generate_source_review_chapter_handoff(repo_root=tmp_path)


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    results.mkdir(parents=True)
    pd.DataFrame(
        [
            _core("H1", "T2", "F1", "method_h1", "interpretation_h1", "lit_a; lit_b"),
            _core("H2", "T3", "F2", "method_h2", "interpretation_h2", "lit_c"),
            _core("H3", "T4", "F3", "method_h3", "interpretation_h3", "lit_d"),
        ]
    ).to_csv(results / "thesis_h1_h2_h3_core_sections.csv", index=False)
    pd.DataFrame(
        [
            _traceability("method_h1", "method"),
            _traceability("method_h2", "method"),
            _traceability("method_h3", "method"),
            _traceability("interpretation_h1", "interpretation"),
            _traceability("interpretation_h2", "interpretation"),
            _traceability("interpretation_h3", "interpretation"),
        ]
    ).to_csv(results / "thesis_method_interpretation_traceability.csv", index=False)
    pd.DataFrame(
        [
            _package("T2", "table"),
            _package("F1", "figure"),
            _package("T3", "table"),
            _package("F2", "figure"),
            _package("T4", "table"),
            _package("F3", "figure"),
        ]
    ).to_csv(results / "thesis_result_package_traceability.csv", index=False)
    pd.DataFrame(
        [
            _ledger("H1", "ledger_h1_a"),
            _ledger("H1", "ledger_h1_b"),
            _ledger("H2", "ledger_h2_a"),
            _ledger("H2", "ledger_h2_b"),
            _ledger("H3", "ledger_h3_a"),
            _ledger("H3", "ledger_h3_b"),
        ]
    ).to_csv(results / "thesis_source_review_progress_ledger.csv", index=False)
    pd.DataFrame(
        [
            {
                "protocol_id": "protocol_06_future_agent_upgrade_boundary",
                "current_state": "future_documentation_only",
            }
        ]
    ).to_csv(results / "thesis_source_review_progress_protocol.csv", index=False)


def _core(
    area: str,
    table: str,
    figure: str,
    method_id: str,
    interpretation_id: str,
    literature_ids: str,
) -> dict[str, str]:
    return {
        "section_id": f"core_section_{area.lower()}",
        "hypothesis": area,
        "chapter_title_de": f"{area}: Kapitel",
        "method_evidence_ids": method_id,
        "interpretation_evidence_ids": interpretation_id,
        "literature_source_ids": literature_ids,
        "deterministic_artifacts": "data/results/core.csv",
        "selected_tables": table,
        "selected_figures": figure,
        "thesis_ready_result_de": f"{area} Resultat.",
        "bounded_interpretation_de": f"{area} bounded Interpretation.",
        "mandatory_limitation_de": f"{area} Limitation.",
        "blocked_wording_de": "Kausalitaetsclaim",
    }


def _traceability(evidence_id: str, item_type: str) -> dict[str, object]:
    return {
        "evidence_id": evidence_id,
        "item_type": item_type,
        "thesis_readiness": "thesis_facing_ready",
        "primary_artifact_exists": True,
        "literature_source_count": 1,
        "known_literature_source_count": 1,
        "limitation_present": True,
        "traceability_status": "draft_traceable_final_source_review_pending",
    }


def _package(package_id: str, package_type: str) -> dict[str, object]:
    return {
        "package_id": package_id,
        "package_type": package_type,
        "include_in_core_package": True,
        "package_traceability_status": "core_package_ready_for_draft",
    }


def _ledger(area: str, ledger_id: str) -> dict[str, object]:
    return {
        "thesis_area": area,
        "ledger_id": ledger_id,
        "review_progress_state": "pending_manual_review",
        "source_status_change_allowed": False,
        "final_citation_ready": False,
    }
