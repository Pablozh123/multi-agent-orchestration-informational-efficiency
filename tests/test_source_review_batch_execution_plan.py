from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from operations.project.build_source_review_batch_execution_plan import (
    BATCH_PLAN_COLUMNS,
    generate_source_review_batch_execution_plan,
)


def test_generate_source_review_batch_execution_plan_writes_batches(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_source_review_batch_execution_plan(repo_root=tmp_path)

    plan = pd.read_csv(result.batch_plan_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(plan.columns) == BATCH_PLAN_COLUMNS
    assert result.batch_plan_rows == 4
    assert result.source_review_rows == 23
    assert result.unique_sources == 9
    assert result.pending_citation_rows == 23
    assert result.final_ready_rows == 0
    assert result.final_release_ready_rows == 0
    assert plan["batch_order"].tolist() == [1, 2, 3, 4]
    assert plan["batch_plan_id"].tolist() == [
        "batch_plan_h1",
        "batch_plan_h2",
        "batch_plan_h3",
        "batch_plan_total_rebuild_gate",
    ]
    assert plan["source_review_rows"].tolist() == [10, 5, 8, 23]
    assert plan["unique_sources"].tolist() == [4, 3, 4, 9]
    assert plan["method_rows"].tolist() == [4, 3, 5, 12]
    assert plan["interpretation_rows"].tolist() == [6, 2, 3, 11]
    assert plan["external_locator_rows"].tolist() == [7, 4, 2, 13]
    assert plan["local_pdf_rows"].tolist() == [3, 1, 6, 10]
    assert plan["pending_citation_rows"].tolist() == [10, 5, 8, 23]
    assert plan["final_ready_rows"].tolist() == [0, 0, 0, 0]
    assert plan["source_status_change_rows"].tolist() == [0, 0, 0, 0]
    assert plan["selected_tables"].tolist() == ["T2", "T3", "T4", "T2, T3, T4"]
    assert plan["selected_figures"].tolist() == ["F1", "F2", "F3", "F1, F2, F3"]
    assert plan["ready_for_manual_execution"].map(_as_bool).all()
    assert not plan["ready_for_final_release"].map(_as_bool).any()
    assert "Source Review Batch Execution Plan" in doc
    assert "Plan rows: 4" in doc
    assert "Source review rows: 23" in doc
    assert "Final release ready rows: 0" in doc
    assert chr(223) not in doc


def test_source_review_batch_execution_plan_keeps_boundaries_visible(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_source_review_batch_execution_plan(repo_root=tmp_path)

    plan = pd.read_csv(result.batch_plan_path)
    doc = result.docs_path.read_text(encoding="utf-8")
    joined = "\n".join(plan.fillna("").astype(str).agg(" ".join, axis=1).tolist())
    boundary_text = f"{joined}\n{doc}"

    assert "review_status" in boundary_text
    assert "page_or_section_note" in boundary_text
    assert "claim_support_decision" in boundary_text
    assert "blocked_wording_check" in boundary_text
    assert "citation_use_decision" in boundary_text
    assert "Page-/Section-Note" in boundary_text
    assert "Claim-Support" in boundary_text
    assert "Blocked-Wording" in boundary_text
    assert "Citation-Use" in boundary_text
    assert "Kausalclaim-Grenze" in boundary_text
    assert "Granger-Grenze" in boundary_text
    assert "Wallet-Grenze" in boundary_text
    assert "keine finale Zitation" in boundary_text
    assert "keine Quellenstatus-Hochstufung" in boundary_text
    assert "keine Runtime-Agenten" in boundary_text
    assert "max 50 rows" in boundary_text
    assert "llm_audit_log" in boundary_text
    assert "keine Wallet-Adressen" in boundary_text
    assert "keine Trading-Claims" in boundary_text
    assert "keine Profitabilitaetsclaims" in boundary_text


def test_source_review_batch_execution_plan_rejects_alignment_gap(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    alignment_path = tmp_path / "data/results/thesis_h1_h2_h3_decision_queue_ledger_alignment.csv"
    alignment = pd.read_csv(alignment_path)
    alignment.loc[0, "field_mismatch_rows"] = 1
    alignment.to_csv(alignment_path, index=False)

    with pytest.raises(ValueError, match="field mismatches"):
        generate_source_review_batch_execution_plan(repo_root=tmp_path)


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    results.mkdir(parents=True)

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
    execution_rows = [
        _execution_row(scope_id, index, source_id, item_type, access_route)
        for scope_id, rows in rows_by_scope.items()
        for index, (source_id, item_type, access_route) in enumerate(rows, start=1)
    ]
    pd.DataFrame(execution_rows).to_csv(
        results / "thesis_h1_h2_h3_manual_source_review_execution_pass.csv",
        index=False,
    )
    pd.DataFrame([_checklist_row(index) for index in range(1, 9)]).to_csv(
        results / "thesis_manual_source_review_update_checklist.csv",
        index=False,
    )
    pd.DataFrame(
        [
            _citation_gate("H1", 10, 4, 4, 6, 10, "T2", "F1"),
            _citation_gate("H2", 5, 3, 3, 2, 5, "T3", "F2"),
            _citation_gate("H3", 8, 4, 5, 3, 8, "T4", "F3"),
            _citation_gate("TOTAL", 23, 9, 12, 11, 23, "T2, T3, T4", "F1, F2, F3"),
        ]
    ).to_csv(results / "thesis_ledger_citation_gate_summary.csv", index=False)
    pd.DataFrame(
        [
            _alignment_row("H1", 10),
            _alignment_row("H2", 5),
            _alignment_row("H3", 8),
        ]
    ).to_csv(results / "thesis_h1_h2_h3_decision_queue_ledger_alignment.csv", index=False)


def _execution_row(
    scope_id: str,
    index: int,
    source_id: str,
    item_type: str,
    access_route: str,
) -> dict[str, object]:
    table_by_scope = {"H1": "T2", "H2": "T3", "H3": "T4"}
    figure_by_scope = {"H1": "F1", "H2": "F2", "H3": "F3"}
    return {
        "execution_batch": {
            "H1": "batch_01_h1_forecast_quality_source_review",
            "H2": "batch_02_h2_event_window_source_review",
            "H3": "batch_03_h3_wallet_timing_source_review",
        }[scope_id],
        "thesis_area": scope_id,
        "source_id": source_id,
        "item_type": item_type,
        "access_route": access_route,
        "selected_table": table_by_scope[scope_id],
        "selected_figure": figure_by_scope[scope_id],
        "source_status_change_allowed": False,
        "final_citation_ready": False,
        "execution_order": index,
    }


def _checklist_row(index: int) -> dict[str, object]:
    return {
        "check_order": index,
        "ready_for_manual_update": True,
        "ready_for_final_citation_release": False,
    }


def _citation_gate(
    scope_id: str,
    rows: int,
    unique_sources: int,
    method_rows: int,
    interpretation_rows: int,
    pending_rows: int,
    selected_tables: str,
    selected_figures: str,
) -> dict[str, object]:
    return {
        "scope_id": scope_id,
        "ledger_rows": rows,
        "unique_sources": unique_sources,
        "method_rows": method_rows,
        "interpretation_rows": interpretation_rows,
        "blocked_pending_citation_rows": pending_rows,
        "final_citation_ready_rows": 0,
        "source_status_change_rows": 0,
        "selected_tables": selected_tables,
        "selected_figures": selected_figures,
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
