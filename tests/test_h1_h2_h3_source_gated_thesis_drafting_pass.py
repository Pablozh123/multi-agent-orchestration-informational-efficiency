from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from operations.project.build_h1_h2_h3_source_gated_thesis_drafting_pass import (
    DRAFTING_PASS_COLUMNS,
    generate_h1_h2_h3_source_gated_thesis_drafting_pass,
)


def test_generate_source_gated_thesis_drafting_pass_writes_paragraph_rows(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_h1_h2_h3_source_gated_thesis_drafting_pass(repo_root=tmp_path)

    drafting = pd.read_csv(result.drafting_pass_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(drafting.columns) == DRAFTING_PASS_COLUMNS
    assert result.drafting_rows == 15
    assert result.h1_rows == 5
    assert result.h2_rows == 5
    assert result.h3_rows == 5
    assert result.manual_execution_rows == 6
    assert result.final_ready_rows == 0
    assert drafting["draft_sequence_order"].tolist() == list(range(1, 16))
    assert set(drafting["thesis_area"]) == {"H1", "H2", "H3"}
    assert drafting["ready_for_bounded_draft"].map(_as_bool).all()
    assert not drafting["ready_for_final_submission"].map(_as_bool).any()
    assert drafting["manual_execution_rows"].astype(int).gt(0).all()
    assert "manual_source_review_execution" in "\n".join(drafting["drafting_pass_id"])
    joined = "\n".join(drafting.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()
    assert "manual source review" in joined
    assert "manual source review follow-up overview" in joined
    assert "overview-/ledger-abgleich" in joined
    assert "page-/section-note" in joined
    assert "claim-support" in joined
    assert "blocked-wording" in joined
    assert "citation-use" in joined
    assert "wenige gute tabellen" in joined
    assert "keine finale zitation" in joined
    assert "keine quellenstatus-hochstufung" in joined
    assert "nicht final-submission-ready" in joined
    assert "llm_audit_log" in joined
    assert "H1-H2-H3 Source-Gated Thesis Drafting Pass" in doc
    assert "Drafting rows: 15" in doc
    assert "Manual execution rows linked once per chapter: 6" in doc
    assert "Final submission ready rows: 0" in doc
    assert "Manual Source Review Follow-up Overview" in doc
    assert "Overview-/Ledger-Abgleich" in doc
    assert chr(223) not in doc


def test_generate_source_gated_thesis_drafting_pass_rejects_missing_manual_rows(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)
    manual = pd.read_csv(
        tmp_path / "data/results/thesis_h1_h2_h3_manual_source_review_execution_pass.csv"
    )
    manual = manual[manual["thesis_area"] != "H3"]
    manual.to_csv(
        tmp_path / "data/results/thesis_h1_h2_h3_manual_source_review_execution_pass.csv",
        index=False,
    )

    with pytest.raises(ValueError, match="missing manual rows for H3"):
        generate_h1_h2_h3_source_gated_thesis_drafting_pass(repo_root=tmp_path)


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    results.mkdir(parents=True)

    for relative in [
        "data/results/h1.csv",
        "data/results/h2.csv",
        "data/results/h3.csv",
    ]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")

    pd.DataFrame(
        [
            _writing_pass("H1", "H1: Prognosequalitaet", "data/results/h1.csv", "T2", "F1"),
            _writing_pass("H2", "H2: Tagesbasierte Ereignisfenster", "data/results/h2.csv", "T3", "F2"),
            _writing_pass("H3", "H3: Wallet-Timing-Diagnostik", "data/results/h3.csv", "T4", "F3"),
        ]
    ).to_csv(results / "thesis_h1_h2_h3_source_gated_writing_pass.csv", index=False)
    pd.DataFrame(
        [
            _manual("exec_h1_a", "H1", "source_a", "method_h1"),
            _manual("exec_h1_b", "H1", "source_b", "interpretation_h1"),
            _manual("exec_h2_a", "H2", "source_c", "method_h2"),
            _manual("exec_h2_b", "H2", "source_d", "interpretation_h2"),
            _manual("exec_h3_a", "H3", "source_e", "method_h3"),
            _manual("exec_h3_b", "H3", "source_f", "interpretation_h3"),
        ]
    ).to_csv(
        results / "thesis_h1_h2_h3_manual_source_review_execution_pass.csv",
        index=False,
    )


def _writing_pass(
    area: str,
    title: str,
    artifact: str,
    table: str,
    figure: str,
) -> dict[str, object]:
    method = f"method_{area.lower()}"
    interpretation = f"interpretation_{area.lower()}"
    return {
        "writing_pass_id": f"writing_pass_{area.lower()}_source_gated",
        "thesis_area": area,
        "chapter_title_de": title,
        "method_evidence_ids": method,
        "interpretation_evidence_ids": interpretation,
        "literature_source_ids": "source_a; source_b",
        "deterministic_artifacts": artifact,
        "source_coverage_links": 2,
        "source_coverage_unique_sources": 2,
        "source_coverage_gap_rows": 0,
        "selected_tables": table,
        "selected_figures": figure,
        "method_paragraph_de": f"{area}: Methode bleibt source-gated.",
        "result_paragraph_de": f"{area}: Resultat nutzt wenige gute Tabellen.",
        "interpretation_paragraph_de": f"{area}: Interpretation bleibt bounded.",
        "table_figure_paragraph_de": f"{area}: Tabelle/Figur statt Rohartefakt-Dumps.",
        "source_gate_paragraph_de": (
            f"{area}: Keine finale Zitation ohne Source Review. "
            "Manual Source Review Follow-up Overview pruefen; "
            "Overview-/Ledger-Abgleich vor Citation Gate dokumentieren. "
            "Keine Quellenstatus-Hochstufung aus dem Draft."
        ),
        "future_agent_boundary_de": (
            f"{area}: keine Runtime-Agenten; llm_audit_log vor spaeterer Nutzung."
        ),
        "blocked_wording_de": "keine finale Zitation | keine Quellenstatus-Hochstufung",
        "full_chapter_draft_de": f"{area}: full draft.",
        "writing_pass_status": "source_gated_bounded_draft_ready_final_source_review_pending",
        "ready_for_bounded_draft": True,
        "ready_for_final_submission": False,
    }


def _manual(execution_id: str, area: str, source_id: str, evidence_id: str) -> dict[str, object]:
    return {
        "execution_id": execution_id,
        "thesis_area": area,
        "source_id": source_id,
        "evidence_id": evidence_id,
        "review_progress_state": "pending_manual_review",
        "final_citation_ready": False,
        "source_status_change_allowed": False,
    }


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"
