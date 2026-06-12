from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_h2_manual_source_review_followup import (
    H2_FOLLOWUP_COLUMNS,
    generate_h2_manual_source_review_followup,
)


def test_generate_h2_manual_source_review_followup_writes_h2_rows(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_h2_manual_source_review_followup(repo_root=tmp_path)

    followup = pd.read_csv(result.followup_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(followup.columns) == H2_FOLLOWUP_COLUMNS
    assert result.followup_rows == 5
    assert result.unique_source_rows == 3
    assert result.pending_rows == 5
    assert result.final_ready_rows == 0
    assert followup["review_order"].tolist() == list(range(1, 6))
    assert followup["item_type"].value_counts().to_dict() == {
        "method": 3,
        "interpretation": 2,
    }
    assert "H2 Manual Source Review Follow-up" in doc
    assert "H2 follow-up rows: 5" in doc
    assert "Final citation ready rows: 0" in doc
    assert chr(223) not in doc


def test_h2_manual_source_review_followup_keeps_manual_gates_visible(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_h2_manual_source_review_followup(repo_root=tmp_path)

    followup = pd.read_csv(result.followup_path)
    joined = "\n".join(followup.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert "method_h2_event_window" in joined
    assert "interpretation_h2_daily_response" in joined
    assert "page-/section-note" in joined
    assert "pending_page_or_section_note" in joined
    assert "claim-support" in joined
    assert "blocked-wording" in joined
    assert "citation-use" in joined
    assert "keine kausalclaims" in joined
    assert "keine quellenstatus-hochstufung" in joined
    assert "keine finale zitation" in joined
    assert "keine rohartefakt-dumps" in joined
    assert "keine runtime-agenten" in joined
    assert "llm_audit_log" in joined
    assert "max 50 rows" in joined
    assert followup["source_status_change_allowed"].astype(str).str.lower().eq("false").all()


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    results.mkdir(parents=True)

    rows = [
        _execution_row(1, "lit_brier_001", "method_h1_brier_dm", "method", "external_locator_review", thesis_area="H1"),
        _execution_row(11, "lit_emh_001", "method_h2_event_window", "method", "external_locator_review"),
        _execution_row(12, "lit_emh_001", "interpretation_h2_daily_response", "interpretation", "external_locator_review"),
        _execution_row(13, "lit_eventstudy_001", "method_h2_event_window", "method", "external_locator_review"),
        _execution_row(14, "lit_eventstudy_001", "interpretation_h2_daily_response", "interpretation", "external_locator_review"),
        _execution_row(15, "zotero_poly_001", "method_h2_event_window", "method", "local_pdf_review"),
    ]
    pd.DataFrame(rows).to_csv(
        results / "thesis_h1_h2_h3_manual_source_review_execution_pass.csv",
        index=False,
    )

    pd.DataFrame([_ledger_row(row["ledger_id"]) for row in rows]).to_csv(
        results / "thesis_source_review_progress_ledger.csv",
        index=False,
    )

    for artifact in [
        "data/results/thesis_h1_summary.csv",
        "data/results/h2_event_window_summary.csv",
    ]:
        path = root / artifact
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")


def _execution_row(
    order: int,
    source_id: str,
    evidence_id: str,
    item_type: str,
    access_route: str,
    *,
    thesis_area: str = "H2",
) -> dict[str, object]:
    deterministic_artifact = "data/results/h2_event_window_summary.csv"
    if thesis_area == "H1":
        deterministic_artifact = "data/results/thesis_h1_summary.csv"
    return {
        "execution_order": order,
        "thesis_area": thesis_area,
        "source_id": source_id,
        "source_title": f"Source title {source_id}",
        "source_status": "skimmed",
        "source_priority_order": order,
        "evidence_id": evidence_id,
        "item_type": item_type,
        "ledger_id": f"ledger_{source_id}__{evidence_id}",
        "deterministic_artifact": deterministic_artifact,
        "selected_table": "T3",
        "selected_figure": "F2",
        "access_route": access_route,
        "review_source_locator": "https://example.test/source",
        "manual_locator_task_de": "Quelle manuell oeffnen; Page-/Section-Note eintragen.",
        "current_review_status": "pending_manual_review",
        "current_claim_support_decision": "pending",
        "current_blocked_wording_check": "pending",
        "current_citation_use_decision": "blocked_pending_manual_review",
        "final_citation_ready": False,
        "source_status_change_allowed": False,
        "bounded_claim_check_de": f"Nur bounded pruefen: Evidence ID `{evidence_id}`.",
        "blocked_wording_check_de": "Blocked-Wording und Kausalclaim-Grenze pruefen.",
        "next_action_de": "Source Review manuell ausfuehren.",
    }


def _ledger_row(ledger_id: str) -> dict[str, object]:
    return {
        "ledger_id": ledger_id,
        "page_or_section_note": "",
        "claim_support_decision": "pending",
        "blocked_wording_check": "pending",
        "citation_use_decision": "blocked_pending_manual_review",
    }
