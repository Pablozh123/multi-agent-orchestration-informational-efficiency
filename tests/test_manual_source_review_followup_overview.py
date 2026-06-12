from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_manual_source_review_followup_overview import (
    OVERVIEW_COLUMNS,
    generate_manual_source_review_followup_overview,
)


def test_generate_manual_source_review_followup_overview_writes_three_rows(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_manual_source_review_followup_overview(repo_root=tmp_path)

    overview = pd.read_csv(result.overview_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(overview.columns) == OVERVIEW_COLUMNS
    assert result.overview_rows == 3
    assert result.total_review_rows == 23
    assert result.total_unique_sources == 9
    assert result.total_pending_rows == 23
    assert result.total_final_ready_rows == 0
    assert overview["slice_id"].tolist() == ["H1", "H2", "H3"]
    assert overview["review_rows"].tolist() == [10, 5, 8]
    assert "Manual Source Review Follow-up Overview" in doc
    assert "Total manual review rows: 23" in doc
    assert "Final citation ready rows: 0" in doc
    assert chr(223) not in doc


def test_manual_source_review_followup_overview_keeps_core_gates_visible(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_manual_source_review_followup_overview(repo_root=tmp_path)

    overview = pd.read_csv(result.overview_path)
    joined = "\n".join(overview.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()
    doc = result.docs_path.read_text(encoding="utf-8").lower()

    assert "page-/section-note" in joined
    assert "claim-support" in joined
    assert "blocked-wording" in joined
    assert "citation-use" in joined
    assert "keine finale zitation" in joined
    assert "keine quellenstatus-hochstufung" in joined
    assert "keine runtime-agenten" in joined
    assert "granger nicht kausal" in joined
    assert "keine willkuerlichen whale-schwellen" in joined
    assert "keine wallet-adressen" in joined
    assert "keine trading-claims" in joined
    assert "keine profitabilitaetsclaims" in joined
    assert "alle 23 h1-h2-h3 zitationen final blockiert" in doc


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs = root / "docs/project"
    results.mkdir(parents=True)
    docs.mkdir(parents=True)

    _write_followup(
        results / "thesis_h1_manual_source_review_followup.csv",
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
    )
    _write_followup(
        results / "thesis_h2_manual_source_review_followup.csv",
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
    )
    _write_followup(
        results / "thesis_h3_manual_source_review_followup.csv",
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
    )

    for name in [
        "THESIS_H1_MANUAL_SOURCE_REVIEW_FOLLOWUP.md",
        "THESIS_H2_MANUAL_SOURCE_REVIEW_FOLLOWUP.md",
        "THESIS_H3_MANUAL_SOURCE_REVIEW_FOLLOWUP.md",
    ]:
        (docs / name).write_text("fixture\n", encoding="utf-8")


def _write_followup(
    path: Path,
    slice_id: str,
    rows: list[tuple[str, str, str]],
    selected_table: str,
    selected_figure: str,
) -> None:
    records = []
    for index, (source_id, item_type, access_route) in enumerate(rows, start=1):
        records.append(
            {
                f"{slice_id.lower()}_followup_id": f"{slice_id.lower()}_{index:02d}",
                "source_id": source_id,
                "item_type": item_type,
                "access_route": access_route,
                "current_review_status": "pending_manual_review",
                "final_citation_ready": False,
                "selected_table": selected_table,
                "selected_figure": selected_figure,
            }
        )
    pd.DataFrame(records).to_csv(path, index=False)
