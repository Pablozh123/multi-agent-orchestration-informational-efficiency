from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_source_review_progress_ledger import (
    LEDGER_COLUMNS,
    generate_source_review_progress_ledger,
)


def test_generate_source_review_progress_ledger_initialises_pending_rows(tmp_path: Path) -> None:
    _write_notes_fixture(tmp_path)

    result = generate_source_review_progress_ledger(repo_root=tmp_path)

    ledger = pd.read_csv(result.ledger_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(ledger.columns) == LEDGER_COLUMNS
    assert result.ledger_rows == 3
    assert result.pending_rows == 3
    assert result.preserved_rows == 0
    assert result.final_citation_ready_rows == 0
    assert set(ledger["thesis_area"]) == {"H1", "H2", "H3"}
    assert set(ledger["review_progress_state"]) == {"pending_manual_review"}
    assert not ledger["source_status_change_allowed"].map(_as_bool).any()
    assert not ledger["final_citation_ready"].map(_as_bool).any()
    assert "Source Review Progress Ledger" in doc
    assert "Ledger rows: 3" in doc
    assert "Preserved manual rows: 0" in doc
    assert "Runtime-Agenten" in doc
    assert chr(223) not in doc


def test_generate_source_review_progress_ledger_preserves_manual_fields(tmp_path: Path) -> None:
    _write_notes_fixture(tmp_path)
    existing = pd.DataFrame(
        [
            {
                "note_id": "note_h1",
                "review_status": "reviewed_manual_note_recorded",
                "page_or_section_note": "S. 12 Methodenabschnitt",
                "claim_support_decision": "supports_allowed_wording",
                "blocked_wording_check": "passed",
                "citation_use_decision": "approved_for_final_citation",
                "reviewed_by": "manual",
                "reviewed_at": "2026-06-12",
                "review_comment_de": "Manuell geprueft.",
            }
        ]
    )
    existing.to_csv(
        tmp_path / "data/results/thesis_source_review_progress_ledger.csv",
        index=False,
    )

    result = generate_source_review_progress_ledger(repo_root=tmp_path)

    ledger = pd.read_csv(result.ledger_path)
    h1 = ledger.loc[ledger["note_id"] == "note_h1"].iloc[0]
    pending = ledger.loc[ledger["note_id"] != "note_h1"]

    assert result.preserved_rows == 1
    assert result.final_citation_ready_rows == 1
    assert h1["review_status"] == "reviewed_manual_note_recorded"
    assert h1["page_or_section_note"] == "S. 12 Methodenabschnitt"
    assert h1["review_progress_state"] == "manual_review_complete_final_citation_ready"
    assert _as_bool(h1["final_citation_ready"])
    assert _as_bool(h1["preserved_manual_fields"])
    assert not _as_bool(h1["source_status_change_allowed"])
    assert set(pending["review_progress_state"]) == {"pending_manual_review"}
    assert not pending["final_citation_ready"].map(_as_bool).any()


def _write_notes_fixture(root: Path) -> None:
    results = root / "data/results"
    results.mkdir(parents=True)
    pd.DataFrame(
        [
            _note("note_h1", "H1", "core_section_h1", "source_a", "method_h1", "T2", "F1"),
            _note("note_h2", "H2", "core_section_h2", "source_b", "method_h2", "T3", "F2"),
            _note("note_h3", "H3", "core_section_h3", "source_c", "method_h3", "T4", "F3"),
        ]
    ).to_csv(results / "thesis_h1_h2_h3_source_review_notes.csv", index=False)


def _note(
    note_id: str,
    area: str,
    section: str,
    source: str,
    evidence: str,
    table: str,
    figure: str,
) -> dict[str, str]:
    return {
        "note_id": note_id,
        "thesis_area": area,
        "section_id": section,
        "source_id": source,
        "evidence_id": evidence,
        "item_type": "method",
        "selected_table": table,
        "selected_figure": figure,
        "deterministic_artifact": "data/results/thesis_core_results_table.csv",
        "access_route": "local_pdf_review",
        "manual_locator_task_de": (
            "Source Review manuell starten: Page-/Section-Note, Claim-Support "
            "und Blocked-Wording erfassen."
        ),
        "do_not_claim_de": (
            "Keine Quellenstatus-Hochstufung, keine finale Zitation und keine "
            "thesis-facing Claims ohne manual Source Review."
        ),
    }


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"
