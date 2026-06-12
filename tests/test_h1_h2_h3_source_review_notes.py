from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_h1_h2_h3_source_review_notes import (
    NOTE_COLUMNS,
    generate_h1_h2_h3_source_review_notes,
)


def test_generate_h1_h2_h3_source_review_notes_filters_core_packets(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_h1_h2_h3_source_review_notes(repo_root=tmp_path)

    notes = pd.read_csv(result.notes_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(notes.columns) == NOTE_COLUMNS
    assert result.note_rows == 3
    assert result.h1_rows == 1
    assert result.h2_rows == 1
    assert result.h3_rows == 1
    assert result.pending_rows == 3
    assert set(notes["thesis_area"]) == {"H1", "H2", "H3"}
    joined = "\n".join(notes.fillna("").astype(str).apply(lambda row: " ".join(row), axis=1))
    assert "monitor" not in joined.lower()
    assert "H1-H2-H3 Source Review Notes" in doc
    assert "Review note rows: 3" in doc
    assert chr(223) not in doc


def test_source_review_notes_preserve_manual_final_citation_gate(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_h1_h2_h3_source_review_notes(repo_root=tmp_path)

    notes = pd.read_csv(result.notes_path)
    h1 = notes[notes["thesis_area"] == "H1"].iloc[0]
    joined = "\n".join(notes.fillna("").astype(str).apply(lambda row: " ".join(row), axis=1)).lower()

    assert h1["section_id"] == "core_section_h1"
    assert h1["selected_table"] == "T2"
    assert h1["selected_figure"] == "F1"
    assert h1["reviewer_page_or_section_note"] != h1["reviewer_page_or_section_note"]
    assert set(notes["note_status"]) == {"pending_manual_source_review"}
    assert set(notes["reviewer_claim_support_decision"]) == {"pending"}
    assert set(notes["reviewer_blocked_wording_check"]) == {"pending"}
    assert "keine quellenstatus-hochstufung" in joined
    assert "keine finale zitation" in joined
    assert "source review manuell" in joined
    assert "page-/section-note" in joined
    assert "blocked-wording-check" in joined


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    results.mkdir(parents=True)

    pd.DataFrame(
        [
            _core_row("H1", "core_section_h1", "T2", "F1"),
            _core_row("H2", "core_section_h2", "T3", "F2"),
            _core_row("H3", "core_section_h3", "T4", "F3"),
        ]
    ).to_csv(results / "thesis_h1_h2_h3_core_sections.csv", index=False)
    pd.DataFrame(
        [
            _evidence_row("method_h1", "Fixture H1 claim", "bounded H1", "reaction speed proof"),
            _evidence_row("method_h2", "Fixture H2 claim", "bounded H2", "intraday speed claim"),
            _evidence_row("method_h3", "Fixture H3 claim", "bounded H3", "causality proof"),
            _evidence_row("method_monitor", "Fixture monitor claim", "bounded monitor", "causal claim"),
        ]
    ).to_csv(results / "thesis_evidence_map.csv", index=False)
    pd.DataFrame(
        [
            _packet_row("H1", "source_h1", "method_h1", "local_pdf_review"),
            _packet_row("H2", "source_h2", "method_h2", "external_locator_review"),
            _packet_row("H3", "source_h3", "method_h3", "local_pdf_review"),
            _packet_row("monitor_prototype", "source_monitor", "method_monitor", "local_pdf_review"),
        ]
    ).to_csv(results / "thesis_source_review_decision_packets.csv", index=False)


def _core_row(area: str, section_id: str, table: str, figure: str) -> dict[str, str]:
    return {
        "hypothesis": area,
        "section_id": section_id,
        "selected_tables": table,
        "selected_figures": figure,
    }


def _evidence_row(
    evidence_id: str,
    claim: str,
    allowed: str,
    blocked: str,
) -> dict[str, str]:
    return {
        "evidence_id": evidence_id,
        "claim_or_decision": claim,
        "allowed_wording": allowed,
        "blocked_wording": blocked,
        "main_limitation": "Fixture limitation",
    }


def _packet_row(
    area: str,
    source_id: str,
    evidence_id: str,
    access_route: str,
) -> dict[str, object]:
    return {
        "decision_packet_id": f"decision_{source_id}_{evidence_id}",
        "source_id": source_id,
        "evidence_id": evidence_id,
        "thesis_area": area,
        "item_type": "method",
        "source_priority_order": 1,
        "access_route": access_route,
        "structure_inventory_status": (
            "local_pdf_structure_available"
            if access_route == "local_pdf_review"
            else "external_only"
        ),
        "primary_artifact": f"data/results/{area.lower()}_artifact.csv",
        "reviewer_decision": "pending",
        "final_citation_gate": "full_source_review_required_before_final_citation",
        "do_not_claim_de": (
            "Keine Quellenstatus-Hochstufung und keine finale Zitation ohne manuelle Page-/Section-Note."
        ),
    }
