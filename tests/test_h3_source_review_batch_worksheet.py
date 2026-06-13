from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from operations.project.build_h3_source_review_batch_worksheet import (
    WORKSHEET_COLUMNS,
    generate_h3_source_review_batch_worksheet,
)


def test_generate_h3_source_review_batch_worksheet_writes_eight_rows(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_h3_source_review_batch_worksheet(repo_root=tmp_path)

    worksheet = pd.read_csv(result.worksheet_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(worksheet.columns) == WORKSHEET_COLUMNS
    assert result.worksheet_rows == 8
    assert result.unique_sources == 4
    assert result.method_rows == 5
    assert result.interpretation_rows == 3
    assert result.pending_citation_rows == 8
    assert result.final_release_ready_rows == 0
    assert worksheet["worksheet_order"].tolist() == list(range(1, 9))
    assert set(worksheet["thesis_area"]) == {"H3"}
    assert set(worksheet["selected_table"]) == {"T4"}
    assert set(worksheet["selected_figure"]) == {"F3"}
    assert set(worksheet["current_review_status"]) == {"pending_manual_review"}
    assert set(worksheet["current_citation_use_decision"]) == {"blocked_pending_manual_review"}
    assert worksheet["ready_for_manual_entry"].map(_as_bool).all()
    assert not worksheet["ready_for_final_release"].map(_as_bool).any()
    assert "H3 Source Review Batch Worksheet" in doc
    assert "Worksheet rows: 8" in doc
    assert "Final release ready rows: 0" in doc
    assert chr(223) not in doc


def test_h3_source_review_batch_worksheet_keeps_granger_and_wallet_boundaries_visible(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_h3_source_review_batch_worksheet(repo_root=tmp_path)

    worksheet = pd.read_csv(result.worksheet_path)
    doc = result.docs_path.read_text(encoding="utf-8")
    joined = "\n".join(worksheet.fillna("").astype(str).agg(" ".join, axis=1).tolist())
    boundary_text = f"{joined}\n{doc}"

    assert "review_status" in boundary_text
    assert "page_or_section_note" in boundary_text
    assert "claim_support_decision" in boundary_text
    assert "blocked_wording_check" in boundary_text
    assert "citation_use_decision" in boundary_text
    assert "reviewed_by" in boundary_text
    assert "reviewed_at" in boundary_text
    assert "review_comment_de" in boundary_text
    assert "Page-/Section-Note" in boundary_text
    assert "Claim-Support" in boundary_text
    assert "Blocked-Wording" in boundary_text
    assert "Citation-Use" in boundary_text
    assert "Granger-Grenze" in boundary_text
    assert "Wallet-Grenze" in boundary_text
    assert "Keine finale Zitation" in boundary_text
    assert "keine Quellenstatus-Hochstufung" in boundary_text
    assert "keine Kausalclaims" in boundary_text
    assert "keine Private-Information-Beweise" in boundary_text
    assert "keine willkuerlichen Whale-Schwellen" in boundary_text
    assert "keine Wallet-Adressen" in boundary_text
    assert "keine Trading-Claims" in boundary_text
    assert "keine Profitabilitaetsclaims" in boundary_text
    assert "keine Runtime-Agenten" in boundary_text
    assert "keine Rohartefakt-Dumps" in boundary_text
    assert "max 50 rows" in boundary_text
    assert "llm_audit_log" in boundary_text


def test_h3_source_review_batch_worksheet_rejects_final_ready_execution_row(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)
    execution_path = tmp_path / "data/results/thesis_h1_h2_h3_manual_source_review_execution_pass.csv"
    execution = pd.read_csv(execution_path)
    execution.loc[0, "final_citation_ready"] = True
    execution.to_csv(execution_path, index=False)

    with pytest.raises(ValueError, match="0 final-ready execution rows"):
        generate_h3_source_review_batch_worksheet(repo_root=tmp_path)


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
    pd.DataFrame(
        [
            _execution_row(index, source_id, item_type, access_route)
            for index, (source_id, item_type, access_route) in enumerate(rows, start=1)
        ]
    ).to_csv(
        results / "thesis_h1_h2_h3_manual_source_review_execution_pass.csv",
        index=False,
    )
    pd.DataFrame(
        [
            {
                "batch_plan_id": "batch_plan_h3",
                "thesis_area": "H3",
                "source_review_rows": 8,
                "unique_sources": 4,
                "method_rows": 5,
                "interpretation_rows": 3,
                "external_locator_rows": 2,
                "local_pdf_rows": 6,
                "pending_citation_rows": 8,
                "final_ready_rows": 0,
                "source_status_change_rows": 0,
                "selected_tables": "T4",
                "selected_figures": "F3",
                "update_checklist_steps": 8,
                "required_manual_fields_de": (
                    "`review_status`, `page_or_section_note`, "
                    "`claim_support_decision`, `blocked_wording_check`, "
                    "`citation_use_decision`, `reviewed_by`, `reviewed_at`, "
                    "`review_comment_de`"
                ),
                "ready_for_manual_execution": True,
                "ready_for_final_release": False,
            }
        ]
    ).to_csv(results / "thesis_source_review_batch_execution_plan.csv", index=False)
    pd.DataFrame([_checklist_row(index) for index in range(1, 9)]).to_csv(
        results / "thesis_manual_source_review_update_checklist.csv",
        index=False,
    )


def _execution_row(
    index: int,
    source_id: str,
    item_type: str,
    access_route: str,
) -> dict[str, object]:
    evidence_id = f"{item_type}_h3_{index:02d}"
    return {
        "execution_order": index,
        "execution_batch": "batch_03_h3_wallet_timing_source_review",
        "thesis_area": "H3",
        "source_id": source_id,
        "source_title": f"Source {source_id}",
        "source_status": "skimmed",
        "evidence_id": evidence_id,
        "item_type": item_type,
        "access_route": access_route,
        "review_source_locator": "https://example.invalid/source",
        "deterministic_artifact": "data/results/thesis_h3_summary.csv",
        "selected_table": "T4",
        "selected_figure": "F3",
        "current_review_status": "pending_manual_review",
        "current_claim_support_decision": "pending",
        "current_blocked_wording_check": "pending",
        "current_citation_use_decision": "blocked_pending_manual_review",
        "source_status_change_allowed": False,
        "final_citation_ready": False,
        "manual_execution_instruction_de": (
            "H3: Quelle manuell pruefen. Erst nach Page-/Section-Note, "
            "Claim-Support und Blocked-Wording-Check darf Citation-Use vorbereitet "
            "werden. Keine Runtime-Agenten; max 50 rows und llm_audit_log."
        ),
        "final_citation_gate_de": (
            "Keine finale Zitation vor vollstaendigem manuellem Source Review; "
            "keine Quellenstatus-Hochstufung aus diesem Pass."
        ),
        "do_not_claim_de": (
            "Keine finale Zitation, keine Quellenstatus-Hochstufung, keine Kausalclaims, "
            "keine Private-Information-Beweise und keine thesis-facing Claims ohne manuelle Entscheidung."
        ),
    }


def _checklist_row(index: int) -> dict[str, object]:
    return {
        "check_order": index,
        "update_phase": f"phase_{index}",
        "manual_field_targets": "field",
        "ready_for_manual_update": True,
        "ready_for_final_citation_release": False,
    }


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"
