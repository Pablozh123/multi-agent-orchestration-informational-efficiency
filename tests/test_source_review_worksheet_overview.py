from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from operations.project.build_source_review_worksheet_overview import (
    OVERVIEW_COLUMNS,
    generate_source_review_worksheet_overview,
)


def test_generate_source_review_worksheet_overview_writes_h1_h2_h3_and_total(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_source_review_worksheet_overview(repo_root=tmp_path)

    overview = pd.read_csv(result.overview_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(overview.columns) == OVERVIEW_COLUMNS
    assert result.overview_rows == 4
    assert result.worksheet_rows == 23
    assert result.unique_sources == 9
    assert result.pending_citation_rows == 23
    assert result.final_release_ready_rows == 0
    assert overview["overview_order"].tolist() == [1, 2, 3, 4]
    assert overview["thesis_area"].tolist() == ["H1", "H2", "H3", "TOTAL"]
    assert overview["worksheet_rows"].tolist() == [10, 5, 8, 23]
    assert overview["unique_sources"].tolist() == [4, 3, 4, 9]
    assert overview["method_rows"].tolist() == [4, 3, 5, 12]
    assert overview["interpretation_rows"].tolist() == [6, 2, 3, 11]
    assert overview["external_locator_rows"].tolist() == [7, 4, 2, 13]
    assert overview["local_pdf_rows"].tolist() == [3, 1, 6, 10]
    assert overview["pending_citation_rows"].tolist() == [10, 5, 8, 23]
    assert overview["final_release_ready_rows"].tolist() == [0, 0, 0, 0]
    assert "Source Review Worksheet Overview" in doc
    assert "Worksheet rows: 23" in doc
    assert "Final release ready rows: 0" in doc
    assert chr(223) not in doc


def test_source_review_worksheet_overview_keeps_boundaries_visible(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_source_review_worksheet_overview(repo_root=tmp_path)

    overview = pd.read_csv(result.overview_path)
    doc = result.docs_path.read_text(encoding="utf-8")
    joined = "\n".join(overview.fillna("").astype(str).agg(" ".join, axis=1).tolist())
    boundary_text = f"{joined}\n{doc}"

    assert "Page-/Section-Note" in boundary_text
    assert "Claim-Support" in boundary_text
    assert "Blocked-Wording" in boundary_text
    assert "Citation-Use" in boundary_text
    assert "Kausalclaim-Grenze" in boundary_text
    assert "Granger-Grenze" in boundary_text
    assert "Wallet-Grenze" in boundary_text
    assert "Keine finale Zitation" in boundary_text
    assert "keine Quellenstatus-Hochstufung" in boundary_text
    assert "keine Wallet-Adressen" in boundary_text
    assert "keine Trading-Claims" in boundary_text
    assert "keine Profitabilitaetsclaims" in boundary_text
    assert "keine Runtime-Agenten" in boundary_text


def test_source_review_worksheet_overview_rejects_final_ready_row(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    h3_path = tmp_path / "data/results/thesis_h3_source_review_batch_worksheet.csv"
    h3 = pd.read_csv(h3_path)
    h3.loc[0, "ready_for_final_release"] = True
    h3.to_csv(h3_path, index=False)

    with pytest.raises(ValueError, match="must not be final-release-ready"):
        generate_source_review_worksheet_overview(repo_root=tmp_path)


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs = root / "docs/project"
    results.mkdir(parents=True)
    docs.mkdir(parents=True)

    _write_worksheet(
        results / "thesis_h1_source_review_batch_worksheet.csv",
        "H1",
        "T2",
        "F1",
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
    )
    _write_worksheet(
        results / "thesis_h2_source_review_batch_worksheet.csv",
        "H2",
        "T3",
        "F2",
        [
            ("lit_emh_001", "method", "external_locator_review"),
            ("lit_emh_001", "interpretation", "external_locator_review"),
            ("lit_eventstudy_001", "method", "external_locator_review"),
            ("lit_eventstudy_001", "interpretation", "external_locator_review"),
            ("zotero_poly_001", "method", "local_pdf_review"),
        ],
    )
    _write_worksheet(
        results / "thesis_h3_source_review_batch_worksheet.csv",
        "H3",
        "T4",
        "F3",
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
    )
    for name in [
        "THESIS_H1_SOURCE_REVIEW_BATCH_WORKSHEET.md",
        "THESIS_H2_SOURCE_REVIEW_BATCH_WORKSHEET.md",
        "THESIS_H3_SOURCE_REVIEW_BATCH_WORKSHEET.md",
    ]:
        (docs / name).write_text("fixture\n", encoding="utf-8")


def _write_worksheet(
    path: Path,
    thesis_area: str,
    selected_table: str,
    selected_figure: str,
    rows: list[tuple[str, str, str]],
) -> None:
    pd.DataFrame(
        [
            {
                "worksheet_order": index,
                "thesis_area": thesis_area,
                "source_id": source_id,
                "item_type": item_type,
                "access_route": access_route,
                "selected_table": selected_table,
                "selected_figure": selected_figure,
                "current_citation_use_decision": "blocked_pending_manual_review",
                "required_manual_fields_de": (
                    "Page-/Section-Note; Claim-Support; Blocked-Wording; "
                    "Citation-Use; reviewed_by; reviewed_at; review_comment_de"
                ),
                "ready_for_manual_entry": True,
                "ready_for_final_release": False,
            }
            for index, (source_id, item_type, access_route) in enumerate(rows, start=1)
        ]
    ).to_csv(path, index=False)
