from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_h1_h2_h3_decision_queue_overview import (
    OVERVIEW_COLUMNS,
    generate_h1_h2_h3_decision_queue_overview,
)


def test_generate_h1_h2_h3_decision_queue_overview_writes_three_rows(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_h1_h2_h3_decision_queue_overview(repo_root=tmp_path)

    overview = pd.read_csv(result.overview_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(overview.columns) == OVERVIEW_COLUMNS
    assert result.overview_rows == 3
    assert result.total_decision_rows == 23
    assert result.total_unique_sources == 9
    assert result.total_pending_queue_rows == 23
    assert result.total_final_ready_rows == 0
    assert result.source_status_change_rows == 0
    assert overview["slice_id"].tolist() == ["H1", "H2", "H3"]
    assert overview["decision_rows"].tolist() == [10, 5, 8]
    assert overview["selected_tables"].tolist() == ["T2", "T3", "T4"]
    assert overview["selected_figures"].tolist() == ["F1", "F2", "F3"]
    assert "H1-H2-H3 Decision Queue Overview" in doc
    assert "Total decision rows: 23" in doc
    assert "Final citation ready rows: 0" in doc
    assert "Source-status change rows: 0" in doc
    assert "Future Agent Boundary" in doc
    assert "maximal 50 rows" in doc
    assert "llm_audit_log" in doc
    assert chr(223) not in doc


def test_h1_h2_h3_decision_queue_overview_keeps_guardrails_visible(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_h1_h2_h3_decision_queue_overview(repo_root=tmp_path)

    overview = pd.read_csv(result.overview_path)
    joined = "\n".join(overview.fillna("").astype(str).agg(" ".join, axis=1).tolist())
    doc = result.docs_path.read_text(encoding="utf-8")

    assert "Page-/Section-Note" in joined
    assert "Claim-Support" in joined
    assert "Blocked-Wording" in joined
    assert "Citation-Use" in joined
    assert "Kausalclaim-Grenze" in joined
    assert "Granger-Grenze" in joined
    assert "Wallet-Grenze" in joined
    assert "keine finale Zitation" in joined
    assert "keine Quellenstatus-Hochstufung" in joined
    assert "keine Runtime-Agenten" in joined
    assert "keine Kennzahlen" in joined
    assert "keine Wallet-Adressen" in joined
    assert "keine Trading-Claims" in joined
    assert "keine Profitabilitaetsclaims" in joined
    assert "pending_manual_h1_source_review" in joined
    assert "pending_manual_h2_source_review" in joined
    assert "pending_manual_h3_source_review" in joined
    assert "alle 23 H1-H2-H3 Decision Rows final blockiert" in doc
    assert "keine Zitation freigeben" in doc


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs = root / "docs/project"
    results.mkdir(parents=True)
    docs.mkdir(parents=True)

    _write_queue(
        results / "thesis_h1_source_review_decision_queue.csv",
        "H1",
        [
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
        "T2",
        "F1",
        "pending_manual_h1_source_review",
        "Page-/Section-Note; Claim-Support; Blocked-Wording; Citation-Use.",
    )
    _write_queue(
        results / "thesis_h2_source_review_decision_queue.csv",
        "H2",
        [
            ("lit_emh_001", "method", "external_locator_review"),
            ("lit_emh_001", "interpretation", "external_locator_review"),
            ("lit_eventstudy_001", "method", "external_locator_review"),
            ("lit_eventstudy_001", "interpretation", "external_locator_review"),
            ("zotero_poly_001", "method", "local_pdf_review"),
        ],
        "T3",
        "F2",
        "pending_manual_h2_source_review",
        "Page-/Section-Note; Claim-Support; Blocked-Wording; Citation-Use; Kausalclaim-Grenze.",
    )
    _write_queue(
        results / "thesis_h3_source_review_decision_queue.csv",
        "H3",
        [
            ("lit_granger_001", "method", "external_locator_review"),
            ("lit_granger_001", "interpretation", "external_locator_review"),
            ("zotero_poly_001", "method", "local_pdf_review"),
            ("zotero_poly_001", "interpretation", "local_pdf_review"),
            ("zotero_poly_005", "method", "local_pdf_review"),
            ("zotero_poly_005", "method", "local_pdf_review"),
            ("zotero_poly_005", "interpretation", "local_pdf_review"),
            ("zotero_poly_007", "method", "local_pdf_review"),
        ],
        "T4",
        "F3",
        "pending_manual_h3_source_review",
        "Page-/Section-Note; Claim-Support; Blocked-Wording; Citation-Use; Granger-Grenze; Wallet-Grenze.",
    )

    for name in [
        "THESIS_H1_SOURCE_REVIEW_DECISION_QUEUE.md",
        "THESIS_H2_SOURCE_REVIEW_DECISION_QUEUE.md",
        "THESIS_H3_SOURCE_REVIEW_DECISION_QUEUE.md",
    ]:
        (docs / name).write_text("fixture\n", encoding="utf-8")


def _write_queue(
    path: Path,
    slice_id: str,
    rows: list[tuple[str, str, str]],
    selected_table: str,
    selected_figure: str,
    queue_status: str,
    manual_fields: str,
) -> None:
    records = []
    for index, (source_id, item_type, access_route) in enumerate(rows, start=1):
        records.append(
            {
                "decision_id": f"{slice_id.lower()}_decision_{index:02d}",
                "decision_order": index,
                "source_id": source_id,
                "evidence_id": f"{slice_id.lower()}_{item_type}_{index:02d}",
                "item_type": item_type,
                "access_route": access_route,
                "selected_table": selected_table,
                "selected_figure": selected_figure,
                "primary_artifact_exists": True,
                "current_review_status": "pending_manual_review",
                "required_manual_decision_fields_de": manual_fields,
                "agent_assist_boundary_de": (
                    "Spaetere Agentenhilfe darf nur fehlende Felder markieren; "
                    "keine Quelleninhalte bewerten, keine Zitation freigeben, "
                    "keine Kennzahlen berechnen, max 50 rows und llm_audit_log."
                ),
                "source_status_change_allowed": False,
                "final_citation_ready": False,
                "queue_status": queue_status,
            }
        )
    pd.DataFrame(records).to_csv(path, index=False)
