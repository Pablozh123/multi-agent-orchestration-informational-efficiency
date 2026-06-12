from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from operations.project.build_manual_source_review_update_checklist import (
    CHECKLIST_COLUMNS,
    generate_manual_source_review_update_checklist,
)


def test_generate_manual_source_review_update_checklist_writes_eight_steps(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_manual_source_review_update_checklist(repo_root=tmp_path)

    checklist = pd.read_csv(result.checklist_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(checklist.columns) == CHECKLIST_COLUMNS
    assert result.checklist_rows == 8
    assert result.ledger_rows == 23
    assert result.pending_citation_rows == 23
    assert result.final_ready_rows == 0
    assert result.final_release_ready_rows == 0
    assert checklist["check_order"].tolist() == list(range(1, 9))
    assert checklist["ledger_rows_in_scope"].unique().tolist() == [23]
    assert checklist["unique_sources_in_scope"].unique().tolist() == [9]
    assert checklist["external_locator_rows"].unique().tolist() == [13]
    assert checklist["local_pdf_rows"].unique().tolist() == [10]
    assert checklist["pending_citation_rows"].unique().tolist() == [23]
    assert checklist["final_ready_rows"].unique().tolist() == [0]
    assert checklist["ready_for_manual_update"].map(_as_bool).all()
    assert not checklist["ready_for_final_citation_release"].map(_as_bool).any()
    assert "Manual Source Review Update Checklist" in doc
    assert "Checklist rows: 8" in doc
    assert "Ledger rows in scope: 23" in doc
    assert "Final ready rows: 0" in doc
    assert chr(223) not in doc


def test_manual_source_review_update_checklist_keeps_allowed_fields_and_guards_visible(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_manual_source_review_update_checklist(repo_root=tmp_path)

    checklist = pd.read_csv(result.checklist_path)
    joined = "\n".join(checklist.fillna("").astype(str).agg(" ".join, axis=1).tolist())
    doc = result.docs_path.read_text(encoding="utf-8")

    assert "page_or_section_note" in joined
    assert "claim_support_decision" in joined
    assert "blocked_wording_check" in joined
    assert "citation_use_decision" in joined
    assert "reviewed_by" in joined
    assert "reviewed_at" in joined
    assert "review_comment_de" in joined
    assert "approved_for_final_citation" in joined
    assert "blocked_pending_manual_review" in joined
    assert "Page-/Section-Note" in joined
    assert "Claim-Support" in joined
    assert "Blocked-Wording" in joined
    assert "Citation-Use" in joined
    assert "keine finale Zitation" in joined
    assert "keine Quellenstatus-Hochstufung" in joined
    assert "Keine Runtime-Agenten" in joined
    assert "max 50 rows" in joined
    assert "llm_audit_log" in joined
    assert "Die einzigen manuell zu pflegenden Ledger-Felder" in doc


def test_manual_source_review_update_checklist_rejects_alignment_gap(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)
    alignment = pd.read_csv(
        tmp_path / "data/results/thesis_h1_h2_h3_decision_queue_ledger_alignment.csv"
    )
    alignment.loc[0, "queue_missing_ledger_rows"] = 1
    alignment.to_csv(
        tmp_path / "data/results/thesis_h1_h2_h3_decision_queue_ledger_alignment.csv",
        index=False,
    )

    with pytest.raises(ValueError, match="queue rows missing ledger"):
        generate_manual_source_review_update_checklist(repo_root=tmp_path)


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs = root / "docs/project"
    results.mkdir(parents=True)
    docs.mkdir(parents=True)

    rows_by_scope = {
        "H1": [
            ("lit_brier_001", "method", "external_locator_review"),
            ("lit_brier_001", "interpretation", "external_locator_review"),
            ("lit_brier_001", "interpretation", "external_locator_review"),
            ("lit_dm_001", "method", "external_locator_review"),
            ("lit_dm_001", "interpretation", "external_locator_review"),
            ("lit_emh_001", "method", "external_locator_review"),
            ("lit_emh_001", "interpretation", "external_locator_review"),
            ("zotero_poly_002", "method", "local_pdf_review"),
            ("zotero_poly_002", "interpretation", "local_pdf_review"),
            ("zotero_poly_002", "interpretation", "local_pdf_review"),
        ],
        "H2": [
            ("lit_emh_001", "method", "external_locator_review"),
            ("lit_emh_001", "interpretation", "external_locator_review"),
            ("lit_eventstudy_001", "method", "external_locator_review"),
            ("lit_eventstudy_001", "interpretation", "external_locator_review"),
            ("zotero_poly_001", "method", "local_pdf_review"),
        ],
        "H3": [
            ("lit_granger_001", "method", "external_locator_review"),
            ("lit_granger_001", "interpretation", "external_locator_review"),
            ("zotero_poly_001", "method", "local_pdf_review"),
            ("zotero_poly_001", "interpretation", "local_pdf_review"),
            ("zotero_poly_005", "method", "local_pdf_review"),
            ("zotero_poly_005", "method", "local_pdf_review"),
            ("zotero_poly_005", "interpretation", "local_pdf_review"),
            ("zotero_poly_007", "method", "local_pdf_review"),
        ],
    }
    pd.DataFrame(
        [
            _ledger_row(scope_id, index, source_id, item_type, access_route)
            for scope_id, rows in rows_by_scope.items()
            for index, (source_id, item_type, access_route) in enumerate(rows, start=1)
        ]
    ).to_csv(results / "thesis_source_review_progress_ledger.csv", index=False)
    pd.DataFrame(
        [
            _citation_gate("H1", 10, 4, 4, 6, 10),
            _citation_gate("H2", 5, 3, 3, 2, 5),
            _citation_gate("H3", 8, 4, 5, 3, 8),
            _citation_gate("TOTAL", 23, 9, 12, 11, 23),
        ]
    ).to_csv(results / "thesis_ledger_citation_gate_summary.csv", index=False)
    pd.DataFrame(
        [
            _alignment_row("H1", 10),
            _alignment_row("H2", 5),
            _alignment_row("H3", 8),
        ]
    ).to_csv(results / "thesis_h1_h2_h3_decision_queue_ledger_alignment.csv", index=False)

    for name in [
        "THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md",
        "THESIS_LEDGER_CITATION_GATE_SUMMARY.md",
        "THESIS_H1_H2_H3_DECISION_QUEUE_LEDGER_ALIGNMENT.md",
    ]:
        (docs / name).write_text("fixture\n", encoding="utf-8")


def _ledger_row(
    scope_id: str,
    index: int,
    source_id: str,
    item_type: str,
    access_route: str,
) -> dict[str, object]:
    return {
        "ledger_id": f"ledger_{scope_id.lower()}_{index:02d}",
        "note_id": f"note_{scope_id.lower()}_{index:02d}",
        "thesis_area": scope_id,
        "source_id": source_id,
        "evidence_id": f"{scope_id.lower()}_{item_type}_{index:02d}",
        "item_type": item_type,
        "access_route": access_route,
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
        "do_not_claim_de": "Keine Quellenstatus-Hochstufung und keine finale Zitation.",
    }


def _citation_gate(
    scope_id: str,
    rows: int,
    unique_sources: int,
    method_rows: int,
    interpretation_rows: int,
    pending_rows: int,
) -> dict[str, object]:
    return {
        "scope_id": scope_id,
        "ledger_rows": rows,
        "unique_sources": unique_sources,
        "method_rows": method_rows,
        "interpretation_rows": interpretation_rows,
        "blocked_pending_citation_rows": pending_rows,
        "page_note_missing_rows": pending_rows,
        "claim_support_pending_rows": pending_rows,
        "blocked_wording_pending_rows": pending_rows,
        "citation_use_pending_rows": pending_rows,
        "final_citation_ready_rows": 0,
        "source_status_change_rows": 0,
        "citation_gate_status": "final_blocked_pending_manual_source_review",
    }


def _alignment_row(scope_id: str, rows: int) -> dict[str, object]:
    return {
        "slice_id": scope_id,
        "ledger_rows": rows,
        "matched_rows": rows,
        "queue_missing_ledger_rows": 0,
        "ledger_missing_queue_rows": 0,
        "field_mismatch_rows": 0,
    }


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"
