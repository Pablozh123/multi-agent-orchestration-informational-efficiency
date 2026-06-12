from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_source_structure_inventory import (
    INVENTORY_COLUMNS,
    generate_source_structure_inventory,
)


def test_generate_source_structure_inventory_writes_counts(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_source_structure_inventory(repo_root=tmp_path)

    inventory = pd.read_csv(result.inventory_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(inventory.columns) == INVENTORY_COLUMNS
    assert result.inventory_rows == 3
    assert result.local_pdf_rows == 1
    assert result.local_html_rows == 1
    assert result.external_only_rows == 1
    assert "Thesis Source Structure Inventory" in doc
    assert "Keine Inhaltsinterpretation" in doc
    assert chr(223) not in doc


def test_source_structure_inventory_keeps_manual_review_boundary(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_source_structure_inventory(repo_root=tmp_path)

    inventory = pd.read_csv(result.inventory_path)
    pdf = inventory[inventory["source_id"] == "pdf_source"].iloc[0]
    html = inventory[inventory["source_id"] == "html_source"].iloc[0]
    external = inventory[inventory["source_id"] == "external_source"].iloc[0]

    assert pdf["structure_inventory_status"] == "local_pdf_structure_available"
    assert int(pdf["pdf_page_count_estimate"]) == 2
    assert html["structure_inventory_status"] == "local_html_structure_available"
    assert int(html["html_heading_count"]) == 2
    assert int(html["html_word_count"]) > 0
    assert external["structure_inventory_status"] == "external_only"
    assert "keine Inhaltsinterpretation" in html["do_not_claim_de"]


def _write_fixture(root: Path) -> None:
    literature_dir = root / "data/literature"
    results_dir = root / "data/results"
    source_dir = root / "sources"
    literature_dir.mkdir(parents=True)
    results_dir.mkdir(parents=True)
    source_dir.mkdir(parents=True)
    pdf_path = source_dir / "paper.pdf"
    html_path = source_dir / "paper.htm"
    pdf_path.write_bytes(b"%PDF\n1 0 obj << /Type /Page >>\n2 0 obj << /Type /Page >>\n")
    html_path.write_text(
        "<html><head><title>Fixture</title></head><body>"
        "<h1>Intro</h1><p>Some review text.</p><h2>Method</h2></body></html>",
        encoding="utf-8",
    )

    pd.DataFrame(
        [
            {"source_id": "pdf_source", "local_file": str(pdf_path)},
            {"source_id": "html_source", "local_file": str(html_path)},
            {"source_id": "external_source", "local_file": "not_local"},
        ]
    ).to_csv(literature_dir / "literature_index.csv", index=False)

    pd.DataFrame(
        [
            _access_row("pdf_source", 1, True, "pdf", pdf_path.stat().st_size, "local_pdf_review"),
            _access_row("html_source", 2, True, "htm", html_path.stat().st_size, "local_html_context_review"),
            _access_row("external_source", 3, False, "not_local", 0, "external_locator_review"),
        ]
    ).to_csv(results_dir / "thesis_source_access_audit.csv", index=False)


def _access_row(
    source_id: str,
    priority_order: int,
    exists: bool,
    file_type: str,
    size: int,
    route: str,
) -> dict[str, object]:
    return {
        "source_id": source_id,
        "priority_order": priority_order,
        "priority_band": "priority_1_method_foundation_review",
        "local_file_exists": exists,
        "local_file_type": file_type,
        "local_file_size_bytes": size,
        "access_route": route,
    }
