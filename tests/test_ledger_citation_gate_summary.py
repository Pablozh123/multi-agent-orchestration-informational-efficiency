from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from operations.project.build_ledger_citation_gate_summary import (
    SUMMARY_COLUMNS,
    generate_ledger_citation_gate_summary,
)


def test_generate_ledger_citation_gate_summary_writes_h1_h2_h3_total(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_ledger_citation_gate_summary(repo_root=tmp_path)

    summary = pd.read_csv(result.summary_path)
    doc = result.docs_path.read_text(encoding="utf-8")
    total = summary.loc[summary["scope_id"] == "TOTAL"].iloc[0]

    assert tuple(summary.columns) == SUMMARY_COLUMNS
    assert result.summary_rows == 4
    assert result.ledger_rows == 23
    assert result.final_citation_ready_rows == 0
    assert result.blocked_pending_citation_rows == 23
    assert result.source_status_change_rows == 0
    assert summary["scope_id"].tolist() == ["H1", "H2", "H3", "TOTAL"]
    assert summary["ledger_rows"].tolist() == [10, 5, 8, 23]
    assert summary["final_citation_ready_rows"].tolist() == [0, 0, 0, 0]
    assert summary["blocked_pending_citation_rows"].tolist() == [10, 5, 8, 23]
    assert summary["page_note_missing_rows"].tolist() == [10, 5, 8, 23]
    assert int(total["unique_sources"]) == 9
    assert int(total["method_rows"]) == 12
    assert int(total["interpretation_rows"]) == 11
    assert int(total["deterministic_artifact_rows"]) == 23
    assert set(summary["citation_gate_status"]) == {"final_blocked_pending_manual_source_review"}
    assert "Ledger Citation Gate Summary" in doc
    assert "Ledger rows: 23" in doc
    assert "Final citation ready rows: 0" in doc
    assert "Source-status change rows: 0" in doc
    assert chr(223) not in doc


def test_ledger_citation_gate_summary_keeps_final_citation_guards_visible(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_ledger_citation_gate_summary(repo_root=tmp_path)

    summary = pd.read_csv(result.summary_path)
    joined = "\n".join(summary.fillna("").astype(str).agg(" ".join, axis=1).tolist())
    doc = result.docs_path.read_text(encoding="utf-8")

    assert "Page-/Section-Note" in joined
    assert "Claim-Support" in joined
    assert "Blocked-Wording" in joined
    assert "Citation-Use" in joined
    assert "keine finale Zitation" in joined
    assert "keine Quellenstatus-Hochstufung" in joined
    assert "Keine Runtime-Agenten" in joined
    assert "alle 23 Ledger-Zeilen final blockiert" in doc
    assert "max 50 rows" in doc
    assert "llm_audit_log" in doc


def test_ledger_citation_gate_summary_rejects_alignment_gaps(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    alignment = pd.read_csv(
        tmp_path / "data/results/thesis_h1_h2_h3_decision_queue_ledger_alignment.csv"
    )
    alignment.loc[0, "field_mismatch_rows"] = 1
    alignment.to_csv(
        tmp_path / "data/results/thesis_h1_h2_h3_decision_queue_ledger_alignment.csv",
        index=False,
    )

    with pytest.raises(ValueError, match="field mismatches"):
        generate_ledger_citation_gate_summary(repo_root=tmp_path)


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs = root / "docs/project"
    results.mkdir(parents=True)
    docs.mkdir(parents=True)

    rows_by_scope = {
        "H1": [
            ("lit_brier_001", "method"),
            ("lit_brier_001", "interpretation"),
            ("lit_brier_001", "interpretation"),
            ("lit_dm_001", "method"),
            ("lit_dm_001", "interpretation"),
            ("lit_emh_001", "method"),
            ("lit_emh_001", "interpretation"),
            ("zotero_poly_002", "method"),
            ("zotero_poly_002", "interpretation"),
            ("zotero_poly_002", "interpretation"),
        ],
        "H2": [
            ("lit_emh_001", "method"),
            ("lit_emh_001", "interpretation"),
            ("lit_eventstudy_001", "method"),
            ("lit_eventstudy_001", "interpretation"),
            ("zotero_poly_001", "method"),
        ],
        "H3": [
            ("lit_granger_001", "method"),
            ("lit_granger_001", "interpretation"),
            ("zotero_poly_001", "method"),
            ("zotero_poly_001", "interpretation"),
            ("zotero_poly_005", "method"),
            ("zotero_poly_005", "method"),
            ("zotero_poly_005", "interpretation"),
            ("zotero_poly_007", "method"),
        ],
    }
    pd.DataFrame(
        [
            _ledger_row(scope_id, index, source_id, item_type)
            for scope_id, rows in rows_by_scope.items()
            for index, (source_id, item_type) in enumerate(rows, start=1)
        ]
    ).to_csv(results / "thesis_source_review_progress_ledger.csv", index=False)
    pd.DataFrame(
        [
            _alignment_row("H1", 10),
            _alignment_row("H2", 5),
            _alignment_row("H3", 8),
        ]
    ).to_csv(results / "thesis_h1_h2_h3_decision_queue_ledger_alignment.csv", index=False)

    (docs / "THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md").write_text("fixture\n", encoding="utf-8")
    (docs / "THESIS_H1_H2_H3_DECISION_QUEUE_LEDGER_ALIGNMENT.md").write_text(
        "fixture\n",
        encoding="utf-8",
    )


def _ledger_row(scope_id: str, index: int, source_id: str, item_type: str) -> dict[str, object]:
    table_by_scope = {"H1": "T2", "H2": "T3", "H3": "T4"}
    figure_by_scope = {"H1": "F1", "H2": "F2", "H3": "F3"}
    return {
        "thesis_area": scope_id,
        "source_id": source_id,
        "evidence_id": f"{scope_id.lower()}_{item_type}_{index:02d}",
        "item_type": item_type,
        "selected_table": table_by_scope[scope_id],
        "selected_figure": figure_by_scope[scope_id],
        "deterministic_artifact": f"data/results/{scope_id.lower()}_artifact.csv",
        "review_progress_state": "pending_manual_review",
        "page_or_section_note": "",
        "claim_support_decision": "pending",
        "blocked_wording_check": "pending",
        "citation_use_decision": "blocked_pending_manual_review",
        "source_status_change_allowed": False,
        "final_citation_ready": False,
        "do_not_claim_de": "Keine Quellenstatus-Hochstufung und keine finale Zitation.",
    }


def _alignment_row(scope_id: str, rows: int) -> dict[str, object]:
    return {
        "slice_id": scope_id,
        "decision_queue_rows": rows,
        "ledger_rows": rows,
        "matched_rows": rows,
        "queue_missing_ledger_rows": 0,
        "ledger_missing_queue_rows": 0,
        "field_mismatch_rows": 0,
    }
