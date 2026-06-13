from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from operations.project.build_h3_source_review_ledger_fill_guide import (
    GUIDE_COLUMNS,
    generate_h3_source_review_ledger_fill_guide,
)


def test_generate_h3_source_review_ledger_fill_guide_writes_eight_rows(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_h3_source_review_ledger_fill_guide(repo_root=tmp_path)

    guide = pd.read_csv(result.guide_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(guide.columns) == GUIDE_COLUMNS
    assert result.guide_rows == 8
    assert result.matched_ledger_rows == 8
    assert result.unique_sources == 4
    assert result.method_rows == 5
    assert result.interpretation_rows == 3
    assert result.final_release_ready_rows == 0
    assert guide["guide_order"].tolist() == list(range(1, 9))
    assert set(guide["thesis_area"]) == {"H3"}
    assert set(guide["selected_table"]) == {"T4"}
    assert set(guide["selected_figure"]) == {"F3"}
    assert set(guide["ledger_match_status"]) == {"matched_h3_worksheet_to_ledger"}
    assert guide["ready_for_manual_ledger_entry"].map(_as_bool).all()
    assert not guide["ready_for_final_release"].map(_as_bool).any()
    assert "H3 Source Review Ledger Fill Guide" in doc
    assert "Guide rows: 8" in doc
    assert "Matched ledger rows: 8" in doc
    assert "Final release ready rows: 0" in doc
    assert chr(223) not in doc


def test_h3_source_review_ledger_fill_guide_keeps_allowed_fields_visible(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_h3_source_review_ledger_fill_guide(repo_root=tmp_path)

    guide = pd.read_csv(result.guide_path)
    doc = result.docs_path.read_text(encoding="utf-8")
    boundary_text = (
        "\n".join(guide.fillna("").astype(str).agg(" ".join, axis=1).tolist())
        + "\n"
        + doc
    ).lower()

    assert "page-/section-note" in boundary_text
    assert "claim-support" in boundary_text
    assert "blocked-wording" in boundary_text
    assert "citation-use" in boundary_text
    assert "granger-grenze" in boundary_text
    assert "wallet-grenze" in boundary_text
    assert "review_status" in boundary_text
    assert "page_or_section_note" in boundary_text
    assert "claim_support_decision" in boundary_text
    assert "blocked_wording_check" in boundary_text
    assert "citation_use_decision" in boundary_text
    assert "reviewed_by" in boundary_text
    assert "reviewed_at" in boundary_text
    assert "review_comment_de" in boundary_text
    assert "preserved_manual_fields" in boundary_text
    assert "manual-only" in boundary_text
    assert "keine finale zitation" in boundary_text
    assert "keine quellenstatus-hochstufung" in boundary_text
    assert "keine kausalclaims" in boundary_text
    assert "keine private-information-beweise" in boundary_text
    assert "keine willkuerlichen whale-schwellen" in boundary_text
    assert "keine wallet-adressen" in boundary_text
    assert "keine trading-claims" in boundary_text
    assert "keine profitabilitaetsclaims" in boundary_text
    assert "keine runtime-agenten" in boundary_text
    assert "keine rohartefakt-dumps" in boundary_text
    assert "max 50 rows" in boundary_text
    assert "llm_audit_log" in boundary_text


def test_h3_source_review_ledger_fill_guide_rejects_missing_ledger_match(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)
    ledger_path = tmp_path / "data/results/thesis_source_review_progress_ledger.csv"
    ledger = pd.read_csv(ledger_path)
    ledger.loc[0, "evidence_id"] = "different_evidence_id"
    ledger.to_csv(ledger_path, index=False)

    with pytest.raises(ValueError, match="must match by source_id and evidence_id"):
        generate_h3_source_review_ledger_fill_guide(repo_root=tmp_path)


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    results.mkdir(parents=True)

    rows = [
        ("lit_granger_001", "method", "external_locator_review"),
        ("lit_granger_001", "interpretation", "external_locator_review"),
        ("zotero_poly_001", "method", "local_pdf_review"),
        ("zotero_poly_001", "interpretation", "local_pdf_review"),
        ("zotero_poly_005", "method", "local_pdf_review"),
        ("zotero_poly_005", "method", "local_pdf_review"),
        ("zotero_poly_005", "interpretation", "local_pdf_review"),
        ("zotero_poly_007", "method", "local_pdf_review"),
    ]
    worksheet_rows = [
        _worksheet_row(index, source_id, item_type, access_route)
        for index, (source_id, item_type, access_route) in enumerate(rows, start=1)
    ]
    pd.DataFrame(worksheet_rows).to_csv(
        results / "thesis_h3_source_review_batch_worksheet.csv",
        index=False,
    )
    pd.DataFrame([_ledger_row(row) for row in worksheet_rows]).to_csv(
        results / "thesis_source_review_progress_ledger.csv",
        index=False,
    )
    pd.DataFrame([_checklist_row(index) for index in range(1, 9)]).to_csv(
        results / "thesis_manual_source_review_update_checklist.csv",
        index=False,
    )
    pd.DataFrame([_alignment_row()]).to_csv(
        results / "thesis_h1_h2_h3_decision_queue_ledger_alignment.csv",
        index=False,
    )

    for index in range(1, 9):
        (results / f"artifact_{index:02d}.csv").write_text("fixture\n", encoding="utf-8")


def _worksheet_row(
    index: int,
    source_id: str,
    item_type: str,
    access_route: str,
) -> dict[str, object]:
    evidence_id = f"{item_type}_h3_{index:02d}"
    return {
        "worksheet_id": f"h3_source_review_{index:02d}_{source_id}__{evidence_id}",
        "worksheet_order": index,
        "thesis_area": "H3",
        "source_id": source_id,
        "evidence_id": evidence_id,
        "item_type": item_type,
        "access_route": access_route,
        "review_source_locator": "https://example.invalid/source",
        "deterministic_artifact": f"data/results/artifact_{index:02d}.csv",
        "selected_table": "T4",
        "selected_figure": "F3",
        "current_review_status": "pending_manual_review",
        "current_citation_use_decision": "blocked_pending_manual_review",
        "page_section_note_target_de": (
            "Manuell Quelle oeffnen und Page-/Section-Note eintragen; keine "
            "erfundene Seitenzahl."
        ),
        "claim_support_target_de": "Claim-Support manuell setzen.",
        "blocked_wording_target_de": "Blocked-Wording fuer H3 pruefen.",
        "granger_boundary_de": (
            "Granger-Grenze: keine Kausalclaims und keine "
            "Private-Information-Beweise."
        ),
        "wallet_boundary_de": (
            "Wallet-Grenze: keine willkuerlichen Whale-Schwellen, keine "
            "Wallet-Adressen, keine Trading-Claims und keine "
            "Profitabilitaetsclaims."
        ),
        "citation_use_target_de": "Citation-Use erst nach Manual Review setzen.",
        "reviewer_metadata_target_de": (
            "reviewed_by, reviewed_at und review_comment_de dokumentieren."
        ),
        "final_gate_de": (
            "Keine finale Zitation vor vollstaendigem manuellem Source Review."
        ),
        "blocked_actions_de": (
            "Keine finale Zitation, keine Quellenstatus-Hochstufung, keine "
            "Kausalclaims, keine Private-Information-Beweise, keine "
            "willkuerlichen Whale-Schwellen, keine Wallet-Adressen, keine "
            "Trading-Claims, keine Profitabilitaetsclaims, keine "
            "Runtime-Agenten, keine Rohartefakt-Dumps, max 50 rows und "
            "llm_audit_log."
        ),
        "ready_for_manual_entry": True,
        "ready_for_final_release": False,
    }


def _ledger_row(worksheet_row: dict[str, object]) -> dict[str, object]:
    return {
        "ledger_id": f"ledger_{worksheet_row['worksheet_id']}",
        "note_id": f"note_{worksheet_row['worksheet_id']}",
        "thesis_area": "H3",
        "source_id": worksheet_row["source_id"],
        "evidence_id": worksheet_row["evidence_id"],
        "item_type": worksheet_row["item_type"],
        "selected_table": "T4",
        "selected_figure": "F3",
        "deterministic_artifact": worksheet_row["deterministic_artifact"],
        "access_route": worksheet_row["access_route"],
        "review_status": "pending_manual_review",
        "page_or_section_note": "",
        "claim_support_decision": "pending",
        "blocked_wording_check": "pending",
        "citation_use_decision": "blocked_pending_manual_review",
        "reviewed_by": "",
        "reviewed_at": "",
        "review_comment_de": "",
        "review_progress_state": "pending_manual_review",
        "source_status_change_allowed": False,
        "final_citation_ready": False,
        "preserved_manual_fields": False,
    }


def _checklist_row(index: int) -> dict[str, object]:
    return {
        "check_order": index,
        "update_phase": f"phase_{index}",
        "manual_field_targets": "field",
        "ready_for_manual_update": True,
        "ready_for_final_citation_release": False,
    }


def _alignment_row() -> dict[str, object]:
    return {
        "slice_id": "H3",
        "ledger_rows": 8,
        "matched_rows": 8,
        "queue_missing_ledger_rows": 0,
        "ledger_missing_queue_rows": 0,
        "field_mismatch_rows": 0,
        "ledger_final_ready_rows": 0,
        "ledger_source_status_change_rows": 0,
        "selected_tables": "T4",
        "selected_figures": "F3",
        "alignment_status": "aligned_pending_manual_review",
    }


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"
