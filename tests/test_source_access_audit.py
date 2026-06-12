from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_source_access_audit import (
    AUDIT_COLUMNS,
    generate_source_access_audit,
)


def test_generate_source_access_audit_writes_access_routes(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_source_access_audit(repo_root=tmp_path)

    audit = pd.read_csv(result.audit_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(audit.columns) == AUDIT_COLUMNS
    assert result.audit_rows == 4
    assert result.priority_1_rows == 2
    assert result.local_available_rows == 2
    assert result.external_review_rows == 2
    assert "Thesis Source Access Audit" in doc
    assert "keine Quelle final zitierfaehig" in doc
    assert chr(223) not in doc


def test_source_access_audit_keeps_blocked_sources_from_claims(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_source_access_audit(repo_root=tmp_path)

    audit = pd.read_csv(result.audit_path)
    pdf = audit[audit["source_id"] == "method_pdf"].iloc[0]
    external = audit[audit["source_id"] == "method_external"].iloc[0]
    blocked = audit[audit["source_id"] == "candidate_html"].iloc[0]

    assert pdf["access_route"] == "local_pdf_review"
    assert int(pdf["local_file_size_bytes"]) > 0
    assert external["access_route"] == "external_locator_review"
    assert blocked["access_route"] == "local_html_context_review"
    assert "Keine thesis-facing Claims" in blocked["do_not_claim_de"]
    assert "Nur Metadaten" in blocked["review_action_de"]


def _write_fixture(root: Path) -> None:
    literature_dir = root / "data/literature"
    results_dir = root / "data/results"
    source_dir = root / "sources"
    literature_dir.mkdir(parents=True)
    results_dir.mkdir(parents=True)
    source_dir.mkdir(parents=True)
    pdf_path = source_dir / "method.pdf"
    html_path = source_dir / "candidate.htm"
    pdf_path.write_bytes(b"%PDF fixture")
    html_path.write_text("<html>fixture</html>\n", encoding="utf-8")

    pd.DataFrame(
        [
            _literature_row("method_pdf", "Method PDF", str(pdf_path), "https://example.com/pdf", "skimmed"),
            _literature_row("method_external", "External Method", "not_local", "https://doi.org/example", "skimmed"),
            _literature_row("candidate_html", "Candidate HTML", str(html_path), "https://example.com/html", "candidate"),
            _literature_row("unused", "Unused Source", "not_local", "https://example.com/unused", "skimmed"),
        ]
    ).to_csv(literature_dir / "literature_index.csv", index=False)

    pd.DataFrame(
        [
            _plan_row("method_pdf", "Method PDF", "skimmed", "priority_1_method_foundation_review"),
            _plan_row("method_external", "External Method", "skimmed", "priority_1_method_foundation_review"),
            _plan_row("candidate_html", "Candidate HTML", "candidate", "blocked_or_future_work_only"),
            _plan_row("unused", "Unused Source", "skimmed", "not_currently_needed"),
        ]
    ).to_csv(results_dir / "thesis_source_review_plan.csv", index=False)


def _literature_row(
    source_id: str,
    title: str,
    local_file: str,
    url: str,
    status: str,
) -> dict[str, str]:
    return {
        "source_id": source_id,
        "title": title,
        "status": status,
        "url": url,
        "local_file": local_file,
    }


def _plan_row(
    source_id: str,
    source_title: str,
    source_status: str,
    priority_band: str,
) -> dict[str, str]:
    readiness = (
        "not_allowed_for_thesis_facing_claims"
        if priority_band == "blocked_or_future_work_only"
        else "needs_full_source_review_before_final_citation"
    )
    return {
        "source_id": source_id,
        "source_title": source_title,
        "source_status": source_status,
        "final_citation_readiness": readiness,
        "priority_band": priority_band,
        "next_action": "Review manually.",
    }
