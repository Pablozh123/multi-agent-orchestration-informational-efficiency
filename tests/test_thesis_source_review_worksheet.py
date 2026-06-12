from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.analysis.thesis_source_review_worksheet import (
    WORKSHEET_COLUMNS,
    generate_source_review_worksheet,
)


def test_generate_source_review_worksheet_writes_manual_review_surface(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_source_review_worksheet(repo_root=tmp_path)

    worksheet = pd.read_csv(result.worksheet_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(worksheet.columns) == WORKSHEET_COLUMNS
    assert result.worksheet_rows == 3
    assert result.priority_1_rows == 1
    assert result.blocked_rows == 1
    assert worksheet["priority_order"].tolist() == [1, 2, 3]
    assert worksheet["reviewer_decision"].eq("pending").all()
    assert worksheet["reviewer_page_or_section_note"].fillna("").eq("").all()
    assert "Thesis Source Review Worksheet" in doc
    assert "does not change source status" in doc
    assert "Do not promote skimmed or candidate sources automatically" in doc


def test_source_review_worksheet_keeps_blocked_sources_out_of_thesis_claims(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_source_review_worksheet(repo_root=tmp_path)

    worksheet = pd.read_csv(result.worksheet_path)
    blocked = worksheet[worksheet["source_id"] == "candidate_001"].iloc[0]
    priority = worksheet[worksheet["source_id"] == "method_001"].iloc[0]

    assert blocked["priority_band"] == "blocked_or_future_work_only"
    assert "thesis-facing" in blocked["must_not_claim"]
    assert blocked["review_source_locator"] == "https://example.com/candidate"
    assert priority["priority_band"] == "priority_1_method_foundation_review"
    assert "bounded method support" in priority["must_confirm"]
    assert "local_file_registered" not in priority["review_source_locator"]


def _write_fixture(root: Path) -> None:
    literature_dir = root / "data/literature"
    results_dir = root / "data/results"
    literature_dir.mkdir(parents=True)
    results_dir.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "source_id": "method_001",
                "title": "Method Source",
                "status": "skimmed",
                "url": "https://example.com/method",
                "local_file": "not_local",
            },
            {
                "source_id": "candidate_001",
                "title": "Candidate Source",
                "status": "candidate",
                "url": "https://example.com/candidate",
                "local_file": "C:/tmp/candidate.pdf",
            },
            {
                "source_id": "unused_001",
                "title": "Unused Source",
                "status": "skimmed",
                "url": "",
                "local_file": "not_local",
            },
        ]
    ).to_csv(literature_dir / "literature_index.csv", index=False)
    pd.DataFrame(
        [
            {
                "source_id": "method_001",
                "source_title": "Method Source",
                "source_status": "skimmed",
                "final_citation_readiness": "needs_full_source_review_before_final_citation",
                "citation_risk": "medium",
                "evidence_packet_count": 1,
                "h1_h2_h3_packet_count": 1,
                "method_packet_count": 1,
                "interpretation_packet_count": 0,
                "priority_band": "priority_1_method_foundation_review",
                "required_review_output": "page_or_section_note",
                "thesis_use_boundary": "draft_structure_only_until_full_source_review",
                "next_action": "Review method source.",
            },
            {
                "source_id": "candidate_001",
                "source_title": "Candidate Source",
                "source_status": "candidate",
                "final_citation_readiness": "not_allowed_for_thesis_facing_claims",
                "citation_risk": "high",
                "evidence_packet_count": 1,
                "h1_h2_h3_packet_count": 0,
                "method_packet_count": 0,
                "interpretation_packet_count": 0,
                "priority_band": "blocked_or_future_work_only",
                "required_review_output": "metadata_only",
                "thesis_use_boundary": "not_allowed_for_thesis_facing_claims",
                "next_action": "Do not use.",
            },
            {
                "source_id": "unused_001",
                "source_title": "Unused Source",
                "source_status": "skimmed",
                "final_citation_readiness": "not_currently_needed",
                "citation_risk": "low",
                "evidence_packet_count": 0,
                "h1_h2_h3_packet_count": 0,
                "method_packet_count": 0,
                "interpretation_packet_count": 0,
                "priority_band": "not_currently_needed",
                "required_review_output": "none",
                "thesis_use_boundary": "not_used_in_current_thesis_map",
                "next_action": "No action.",
            },
        ]
    ).to_csv(results_dir / "thesis_source_review_plan.csv", index=False)
    pd.DataFrame(
        [
            {
                "source_id": "method_001",
                "thesis_area": "H1",
                "evidence_id": "method_h1",
                "item_type": "method",
                "allowed_wording": "bounded method support",
                "blocked_wording": "universal claim",
                "reviewer_decision": "pending",
            },
            {
                "source_id": "candidate_001",
                "thesis_area": "future_agents",
                "evidence_id": "future_agent",
                "item_type": "future_work",
                "allowed_wording": "future-work context only",
                "blocked_wording": "thesis-facing empirical claim",
                "reviewer_decision": "pending",
            },
        ]
    ).to_csv(results_dir / "thesis_citation_review_packets.csv", index=False)
