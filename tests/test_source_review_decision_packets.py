from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_source_review_decision_packets import (
    DECISION_COLUMNS,
    generate_source_review_decision_packets,
)


def test_generate_source_review_decision_packets_writes_pending_rows(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_source_review_decision_packets(repo_root=tmp_path)

    decisions = pd.read_csv(result.decision_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(decisions.columns) == DECISION_COLUMNS
    assert result.decision_rows == 2
    assert result.full_review_rows == 1
    assert result.metadata_only_rows == 1
    assert result.pending_rows == 2
    assert "Thesis Source Review Decision Packets" in doc
    assert "Decision packets: 2" in doc
    assert "Keine finale Zitation" in doc
    assert chr(223) not in doc


def test_source_review_decision_packets_keep_final_use_blocked(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_source_review_decision_packets(repo_root=tmp_path)

    decisions = pd.read_csv(result.decision_path)
    full_review = decisions[decisions["evidence_id"] == "evidence_method"].iloc[0]
    metadata_only = decisions[decisions["evidence_id"] == "future_agent"].iloc[0]
    joined = "\n".join(decisions.fillna("").astype(str).agg(" ".join, axis=1).tolist())

    assert decisions["reviewer_decision"].eq("pending").all()
    assert decisions["reviewer_claim_support_decision"].eq("pending").all()
    assert decisions["final_thesis_use_status"].str.startswith("blocked_").all()
    assert bool(full_review["primary_artifact_exists"])
    assert full_review["final_thesis_use_status"] == "blocked_final_citation_pending_manual_review"
    assert "supports_allowed_wording" in full_review["decision_options_de"]
    assert metadata_only["final_thesis_use_status"] == "blocked_future_work_metadata_only"
    assert "future_work_metadata_ok" in metadata_only["decision_options_de"]
    assert "Keine Quellenstatus-Hochstufung" in joined


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    results.mkdir(parents=True)
    artifact = results / "artifact.csv"
    artifact.write_text("fixture\n", encoding="utf-8")

    pd.DataFrame(
        [
            _packet(
                packet_id="source_a__evidence_method",
                source_id="source_a",
                evidence_id="evidence_method",
                final_gate="full_source_review_required_before_final_citation",
                draft_use_allowed=True,
            ),
            _packet(
                packet_id="source_b__future_agent",
                source_id="source_b",
                evidence_id="future_agent",
                final_gate="metadata_and_relevance_review_before_future_work_use",
                draft_use_allowed=False,
            ),
        ]
    ).to_csv(results / "thesis_citation_review_packets.csv", index=False)
    pd.DataFrame(
        [
            _access("source_a", 1, "priority_1_method_foundation_review", "local_pdf_review"),
            _access("source_b", 2, "blocked_or_future_work_only", "external_locator_review"),
        ]
    ).to_csv(results / "thesis_source_access_audit.csv", index=False)
    pd.DataFrame(
        [
            _structure("source_a", "local_pdf_structure_available"),
            _structure("source_b", "external_only"),
        ]
    ).to_csv(results / "thesis_source_structure_inventory.csv", index=False)


def _packet(
    *,
    packet_id: str,
    source_id: str,
    evidence_id: str,
    final_gate: str,
    draft_use_allowed: bool,
) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "source_id": source_id,
        "source_status": "skimmed",
        "source_title": f"Title {source_id}",
        "final_citation_readiness": "needs_full_source_review_before_final_citation",
        "citation_risk": "medium",
        "evidence_id": evidence_id,
        "thesis_area": "H1",
        "item_type": "method",
        "claim_or_decision": "Fixture claim",
        "primary_artifact": "data/results/artifact.csv",
        "allowed_wording": "bounded wording",
        "blocked_wording": "overclaim",
        "main_limitation": "fixture limitation",
        "review_question": "Does it support the bounded wording?",
        "required_check": "Read source and record page note.",
        "draft_use_allowed": draft_use_allowed,
        "final_citation_gate": final_gate,
        "reviewer_page_or_section_note": "",
        "reviewer_decision": "pending",
        "reviewer_notes": "",
    }


def _access(source_id: str, priority_order: int, priority_band: str, access_route: str) -> dict[str, object]:
    return {
        "source_id": source_id,
        "priority_order": priority_order,
        "priority_band": priority_band,
        "access_route": access_route,
        "do_not_claim_de": "Keine Quellenstatus-Hochstufung.",
    }


def _structure(source_id: str, status: str) -> dict[str, object]:
    return {
        "source_id": source_id,
        "structure_inventory_status": status,
        "manual_review_instruction_de": "Page-/Section-Note manuell eintragen.",
    }
