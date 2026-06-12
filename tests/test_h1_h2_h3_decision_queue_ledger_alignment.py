from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_h1_h2_h3_decision_queue_ledger_alignment import (
    ALIGNMENT_COLUMNS,
    generate_h1_h2_h3_decision_queue_ledger_alignment,
)


def test_generate_h1_h2_h3_decision_queue_ledger_alignment_writes_three_rows(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_h1_h2_h3_decision_queue_ledger_alignment(repo_root=tmp_path)

    alignment = pd.read_csv(result.alignment_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(alignment.columns) == ALIGNMENT_COLUMNS
    assert result.alignment_rows == 3
    assert result.total_queue_rows == 23
    assert result.total_ledger_rows == 23
    assert result.total_matched_rows == 23
    assert result.total_missing_rows == 0
    assert result.total_field_mismatch_rows == 0
    assert result.total_final_ready_rows == 0
    assert alignment["slice_id"].tolist() == ["H1", "H2", "H3"]
    assert alignment["decision_queue_rows"].tolist() == [10, 5, 8]
    assert alignment["ledger_rows"].tolist() == [10, 5, 8]
    assert alignment["matched_rows"].tolist() == [10, 5, 8]
    assert alignment["selected_tables"].tolist() == ["T2", "T3", "T4"]
    assert alignment["selected_figures"].tolist() == ["F1", "F2", "F3"]
    assert alignment["overview_count_match"].map(_as_bool).all()
    assert set(alignment["alignment_status"]) == {"aligned_pending_manual_review"}
    assert "H1-H2-H3 Decision Queue Ledger Alignment" in doc
    assert "Total decision queue rows: 23" in doc
    assert "Matched rows: 23" in doc
    assert "Field mismatch rows: 0" in doc
    assert "Ledger final-ready rows: 0" in doc
    assert chr(223) not in doc


def test_h1_h2_h3_decision_queue_ledger_alignment_keeps_manual_gates_visible(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_h1_h2_h3_decision_queue_ledger_alignment(repo_root=tmp_path)

    alignment = pd.read_csv(result.alignment_path)
    joined = "\n".join(alignment.fillna("").astype(str).agg(" ".join, axis=1).tolist())
    doc = result.docs_path.read_text(encoding="utf-8")

    assert "Page-/Section-Note" in joined
    assert "Claim-Support" in joined
    assert "Blocked-Wording" in joined
    assert "Citation-Use" in joined
    assert "Kausalclaim-Grenze" in joined
    assert "Granger-Grenze" in joined
    assert "Wallet-Grenze" in joined
    assert "keine Quellenstatus-Hochstufung" in doc
    assert "keine finale Zitation" in doc
    assert "keine Runtime-Agenten" in doc
    assert "maximal 50 rows" in doc
    assert "llm_audit_log" in doc
    assert "keine Kennzahlen" in doc
    assert "alle 23 Rows final blockiert" in doc


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs = root / "docs/project"
    results.mkdir(parents=True)
    docs.mkdir(parents=True)

    h1_rows = [
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
    ]
    h2_rows = [
        ("lit_emh_001", "method", "external_locator_review"),
        ("lit_emh_001", "interpretation", "external_locator_review"),
        ("lit_eventstudy_001", "method", "external_locator_review"),
        ("lit_eventstudy_001", "interpretation", "external_locator_review"),
        ("zotero_poly_001", "method", "local_pdf_review"),
    ]
    h3_rows = [
        ("lit_granger_001", "method", "external_locator_review"),
        ("lit_granger_001", "interpretation", "external_locator_review"),
        ("zotero_poly_001", "method", "local_pdf_review"),
        ("zotero_poly_001", "interpretation", "local_pdf_review"),
        ("zotero_poly_005", "method", "local_pdf_review"),
        ("zotero_poly_005", "method", "local_pdf_review"),
        ("zotero_poly_005", "interpretation", "local_pdf_review"),
        ("zotero_poly_007", "method", "local_pdf_review"),
    ]

    _write_queue(
        results / "thesis_h1_source_review_decision_queue.csv",
        "H1",
        h1_rows,
        "T2",
        "F1",
        "pending_manual_h1_source_review",
    )
    _write_queue(
        results / "thesis_h2_source_review_decision_queue.csv",
        "H2",
        h2_rows,
        "T3",
        "F2",
        "pending_manual_h2_source_review",
    )
    _write_queue(
        results / "thesis_h3_source_review_decision_queue.csv",
        "H3",
        h3_rows,
        "T4",
        "F3",
        "pending_manual_h3_source_review",
    )
    _write_overview(results / "thesis_h1_h2_h3_decision_queue_overview.csv")
    _write_ledger(
        results / "thesis_source_review_progress_ledger.csv",
        {"H1": h1_rows, "H2": h2_rows, "H3": h3_rows},
    )

    for name in [
        "THESIS_H1_SOURCE_REVIEW_DECISION_QUEUE.md",
        "THESIS_H2_SOURCE_REVIEW_DECISION_QUEUE.md",
        "THESIS_H3_SOURCE_REVIEW_DECISION_QUEUE.md",
        "THESIS_H1_H2_H3_DECISION_QUEUE_OVERVIEW.md",
        "THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md",
    ]:
        (docs / name).write_text("fixture\n", encoding="utf-8")


def _write_queue(
    path: Path,
    slice_id: str,
    rows: list[tuple[str, str, str]],
    selected_table: str,
    selected_figure: str,
    queue_status: str,
) -> None:
    records = []
    for index, (source_id, item_type, access_route) in enumerate(rows, start=1):
        records.append(
            {
                "decision_id": f"{slice_id.lower()}_decision_{index:02d}",
                "source_id": source_id,
                "evidence_id": f"{slice_id.lower()}_{item_type}_{index:02d}",
                "item_type": item_type,
                "access_route": access_route,
                "deterministic_artifact": f"data/results/{slice_id.lower()}_artifact.csv",
                "selected_table": selected_table,
                "selected_figure": selected_figure,
                "queue_status": queue_status,
                "source_status_change_allowed": False,
                "final_citation_ready": False,
                "agent_assist_boundary_de": (
                    "Spaetere Agentenhilfe darf nur fehlende Felder markieren; "
                    "keine Quelleninhalte bewerten, keine Zitation freigeben, "
                    "keine Kennzahlen berechnen, max 50 rows und llm_audit_log."
                ),
            }
        )
    pd.DataFrame(records).to_csv(path, index=False)


def _write_overview(path: Path) -> None:
    pd.DataFrame(
        [
            _overview("H1", 10, 10, "T2", "F1"),
            _overview("H2", 5, 5, "T3", "F2"),
            _overview("H3", 8, 8, "T4", "F3"),
        ]
    ).to_csv(path, index=False)


def _overview(
    slice_id: str,
    decision_rows: int,
    pending_rows: int,
    selected_tables: str,
    selected_figures: str,
) -> dict[str, object]:
    return {
        "slice_id": slice_id,
        "decision_rows": decision_rows,
        "pending_queue_rows": pending_rows,
        "final_ready_rows": 0,
        "source_status_change_rows": 0,
        "selected_tables": selected_tables,
        "selected_figures": selected_figures,
    }


def _write_ledger(
    path: Path,
    rows_by_slice: dict[str, list[tuple[str, str, str]]],
) -> None:
    table_by_slice = {"H1": "T2", "H2": "T3", "H3": "T4"}
    figure_by_slice = {"H1": "F1", "H2": "F2", "H3": "F3"}
    records = []
    for slice_id, rows in rows_by_slice.items():
        for index, (source_id, item_type, access_route) in enumerate(rows, start=1):
            evidence_id = f"{slice_id.lower()}_{item_type}_{index:02d}"
            records.append(
                {
                    "note_id": f"note_{slice_id.lower()}_{index:02d}",
                    "thesis_area": slice_id,
                    "source_id": source_id,
                    "evidence_id": evidence_id,
                    "item_type": item_type,
                    "access_route": access_route,
                    "deterministic_artifact": f"data/results/{slice_id.lower()}_artifact.csv",
                    "selected_table": table_by_slice[slice_id],
                    "selected_figure": figure_by_slice[slice_id],
                    "review_progress_state": "pending_manual_review",
                    "source_status_change_allowed": False,
                    "final_citation_ready": False,
                    "do_not_claim_de": (
                        "Keine Quellenstatus-Hochstufung, keine finale Zitation "
                        "und keine Runtime-Agenten ohne manuelle Source Review."
                    ),
                }
            )
    pd.DataFrame(records).to_csv(path, index=False)


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"
