from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_h3_source_review_decision_queue import (
    QUEUE_COLUMNS,
    generate_h3_source_review_decision_queue,
)


def test_generate_h3_source_review_decision_queue_writes_pending_queue(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_h3_source_review_decision_queue(repo_root=tmp_path)

    queue = pd.read_csv(result.queue_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(queue.columns) == QUEUE_COLUMNS
    assert result.queue_rows == 8
    assert result.unique_sources == 4
    assert result.method_rows == 5
    assert result.interpretation_rows == 3
    assert result.external_rows == 2
    assert result.local_pdf_rows == 6
    assert result.final_ready_rows == 0
    assert queue["decision_order"].tolist() == list(range(1, 9))
    assert set(queue["selected_table"]) == {"T4"}
    assert set(queue["selected_figure"]) == {"F3"}
    assert queue["final_citation_ready"].astype(str).str.lower().eq("false").all()
    assert queue["source_status_change_allowed"].astype(str).str.lower().eq("false").all()
    assert "H3 Source Review Decision Queue" in doc
    assert "H3 decision rows: 8" in doc
    assert "Final citation ready rows: 0" in doc
    assert "H3 Boundary" in doc
    assert "Future Agent Boundary" in doc
    assert "max 50 rows" in doc
    assert "llm_audit_log" in doc
    assert chr(223) not in doc


def test_h3_source_review_decision_queue_keeps_wallet_and_granger_boundaries(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_h3_source_review_decision_queue(repo_root=tmp_path)

    queue = pd.read_csv(result.queue_path)
    joined = "\n".join(queue.fillna("").astype(str).agg(" ".join, axis=1).tolist())

    assert "Page-/Section-Note" in joined
    assert "Claim-Support" in joined
    assert "Blocked-Wording" in joined
    assert "Citation-Use" in joined
    assert "Granger-Grenze" in joined
    assert "Wallet-Grenze" in joined
    assert "keine Zitation freigeben" in joined
    assert "keine Kennzahlen" in joined
    assert "keine Kausal" in joined
    assert "keine willkuerlichen Whale-Schwellen" in joined
    assert "keine Wallet-Adressen" in joined
    assert "keine Trading-Claims" in joined
    assert "keine Profitabilitaetsclaims" in joined
    assert "pending_manual_h3_source_review" in joined
    assert "source_mapped_final_review_pending" in joined
    assert "needs_full_source_review_before_final_citation" in joined
    assert "Methodenanker" in joined
    assert "Interpretationsgrenze" in joined
    assert "local_pdf_structure_available" in joined
    assert "external_only" in joined


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    results.mkdir(parents=True)

    for relative in [
        "data/results/h3_granger_results.csv",
        "data/results/h3_wallet_distribution_inventory.json",
        "data/results/thesis_h3_summary.csv",
    ]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("id,value\nfixture,1\n", encoding="utf-8")

    rows = [
        _followup_row(1, "lit_granger_001", "method_h3_granger_timing", "method", "external_locator_review"),
        _followup_row(2, "lit_granger_001", "interpretation_h3_top_tier_signal", "interpretation", "external_locator_review"),
        _followup_row(3, "zotero_poly_001", "method_h3_wallet_tiers", "method", "local_pdf_review"),
        _followup_row(4, "zotero_poly_001", "interpretation_h3_top_tier_signal", "interpretation", "local_pdf_review"),
        _followup_row(5, "zotero_poly_005", "method_h3_granger_timing", "method", "local_pdf_review"),
        _followup_row(6, "zotero_poly_005", "method_h3_wallet_tiers", "method", "local_pdf_review"),
        _followup_row(7, "zotero_poly_005", "interpretation_h3_top_tier_signal", "interpretation", "local_pdf_review"),
        _followup_row(8, "zotero_poly_007", "method_h3_wallet_tiers", "method", "local_pdf_review"),
    ]
    pd.DataFrame(rows).to_csv(results / "thesis_h3_manual_source_review_followup.csv", index=False)

    pd.DataFrame(
        [
            _structure_row("lit_granger_001", "not_local", False, "external_only"),
            _structure_row("zotero_poly_001", "pdf", True, "local_pdf_structure_available"),
            _structure_row("zotero_poly_005", "pdf", True, "local_pdf_structure_available"),
            _structure_row("zotero_poly_007", "pdf", True, "local_pdf_structure_available"),
        ]
    ).to_csv(results / "thesis_source_structure_inventory.csv", index=False)

    pd.DataFrame([_coverage_row(row["source_id"], row["evidence_id"]) for row in rows]).to_csv(
        results / "thesis_method_interpretation_source_coverage.csv",
        index=False,
    )


def _followup_row(
    review_order: int,
    source_id: str,
    evidence_id: str,
    item_type: str,
    access_route: str,
) -> dict[str, object]:
    artifact_by_evidence = {
        "method_h3_granger_timing": "data/results/h3_granger_results.csv",
        "method_h3_wallet_tiers": "data/results/h3_wallet_distribution_inventory.json",
        "interpretation_h3_top_tier_signal": "data/results/thesis_h3_summary.csv",
    }
    return {
        "h3_followup_id": f"h3_followup_{review_order:02d}_{source_id}__{evidence_id}",
        "review_order": review_order,
        "source_id": source_id,
        "source_title": f"Source {source_id}",
        "source_status": "skimmed",
        "source_priority_order": review_order,
        "evidence_id": evidence_id,
        "item_type": item_type,
        "deterministic_artifact": artifact_by_evidence[evidence_id],
        "selected_table": "T4",
        "selected_figure": "F3",
        "access_route": access_route,
        "review_source_locator": "https://example.test/source",
        "manual_locator_task_de": "Quelle manuell oeffnen; Page-/Section-Note eintragen.",
        "current_review_status": "pending_manual_review",
        "allowed_claim_scope_de": f"Nur bounded pruefen: Evidence ID `{evidence_id}`.",
        "blocked_wording_check_de": "Pruefen: keine Kausal-, Trading- oder Private-Information-Claims.",
        "final_citation_ready": False,
        "source_status_change_allowed": False,
    }


def _structure_row(
    source_id: str,
    local_file_type: str,
    exists: bool,
    status: str,
) -> dict[str, object]:
    return {
        "source_id": source_id,
        "local_file_type": local_file_type,
        "local_file_exists": exists,
        "structure_inventory_status": status,
        "manual_review_instruction_de": "Page-/Section-Note manuell erfassen.",
    }


def _coverage_row(source_id: str, evidence_id: str) -> dict[str, object]:
    return {
        "source_id": source_id,
        "evidence_id": evidence_id,
        "thesis_area": "H3",
        "coverage_status": "source_mapped_final_review_pending",
        "final_citation_readiness": "needs_full_source_review_before_final_citation",
        "primary_artifact_exists": True,
    }
