from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from operations.project.build_h1_h2_h3_source_gated_writing_pass import (
    WRITING_PASS_COLUMNS,
    generate_h1_h2_h3_source_gated_writing_pass,
)


def test_generate_h1_h2_h3_source_gated_writing_pass_writes_three_rows(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_h1_h2_h3_source_gated_writing_pass(repo_root=tmp_path)

    writing_pass = pd.read_csv(result.writing_pass_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(writing_pass.columns) == WRITING_PASS_COLUMNS
    assert result.writing_pass_rows == 3
    assert result.bounded_ready_rows == 3
    assert result.final_ready_rows == 0
    assert result.source_coverage_gap_rows == 0
    assert set(writing_pass["thesis_area"]) == {"H1", "H2", "H3"}
    assert "H1-H2-H3 Source-Gated Writing Pass" in doc
    assert "Writing pass rows: 3" in doc
    assert "Final submission ready rows: 0" in doc
    assert "Source coverage gap rows: 0" in doc
    assert "method_h1_brier_dm" in doc
    assert "interpretation_h3_top_tier_signal" in doc
    assert "keine Runtime-Agenten" in doc
    assert "llm_audit_log" in doc
    assert chr(223) not in doc


def test_h1_h2_h3_source_gated_writing_pass_preserves_gates(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_h1_h2_h3_source_gated_writing_pass(repo_root=tmp_path)

    writing_pass = pd.read_csv(result.writing_pass_path)
    joined = "\n".join(writing_pass.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert writing_pass["writing_pass_status"].eq(
        "source_gated_bounded_draft_ready_final_source_review_pending"
    ).all()
    assert writing_pass["ready_for_bounded_draft"].astype(bool).all()
    assert not writing_pass["ready_for_final_submission"].astype(bool).any()
    assert writing_pass["source_coverage_gap_rows"].astype(int).eq(0).all()
    assert "source-gated" in joined
    assert "keine finale zitation" in joined
    assert "wenige gute tabellen" in joined
    assert "nicht final-submission-ready" in joined
    assert "keine rohartefakt-dumps" in joined


def test_h1_h2_h3_source_gated_writing_pass_fails_on_missing_artifact(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)
    (tmp_path / "data/results/h3_granger_results.csv").unlink()

    with pytest.raises(FileNotFoundError, match="Source-gated writing pass artifact missing"):
        generate_h1_h2_h3_source_gated_writing_pass(repo_root=tmp_path)


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    results.mkdir(parents=True)

    artifact_paths = [
        "data/results/thesis_h1_summary.csv",
        "data/results/h2_event_window_summary.csv",
        "data/results/h3_granger_results.csv",
    ]
    for relative in artifact_paths:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")

    rows = []
    for area, title, methods, interpretations, literature, artifacts, table, figure, links in [
        (
            "H1",
            "H1: Prognosequalitaet",
            "method_h1_brier_dm",
            "interpretation_h1_bounded_advantage",
            "lit_brier_001",
            "data/results/thesis_h1_summary.csv",
            "T2",
            "F1",
            10,
        ),
        (
            "H2",
            "H2: Tagesbasierte Ereignisfenster",
            "method_h2_event_window",
            "interpretation_h2_daily_response",
            "lit_eventstudy_001",
            "data/results/h2_event_window_summary.csv",
            "T3",
            "F2",
            5,
        ),
        (
            "H3",
            "H3: Wallet-Timing-Diagnostik",
            "method_h3_granger_timing",
            "interpretation_h3_top_tier_signal",
            "lit_granger_001",
            "data/results/h3_granger_results.csv",
            "T4",
            "F3",
            8,
        ),
    ]:
        for order, step in enumerate(
            [
                "method_setup",
                "result_statement",
                "interpretation_boundary",
                "table_figure_integration",
                "source_review_and_citation_gate",
                "future_agent_boundary",
            ],
            start=1,
        ):
            rows.append(
                {
                    "chapter_draft_id": f"chapter_draft_{area.lower()}_{order:02d}_{step}",
                    "thesis_area": area,
                    "section_id": f"core_section_{area.lower()}",
                    "chapter_title_de": title,
                    "draft_order": order,
                    "draft_step": step,
                    "draft_subsection_de": step,
                    "method_evidence_ids": methods,
                    "interpretation_evidence_ids": interpretations,
                    "literature_source_ids": literature,
                    "deterministic_artifacts": artifacts,
                    "selected_tables": table,
                    "selected_figures": figure,
                    "selected_result_package_items": f"{table}; {figure}",
                    "source_review_gate_de": f"{area}: Keine finale Zitation ohne Source Review.",
                    "source_coverage_links": links,
                    "source_coverage_unique_sources": 3,
                    "source_coverage_gap_rows": 0,
                    "chapter_paragraph_de": _paragraph(area, step),
                    "mandatory_limitation_de": f"{area} Limitation.",
                    "blocked_wording_de": "keine Rohartefakt-Dumps | keine finale Zitation",
                    "future_agent_boundary_de": "keine Runtime-Agenten; llm_audit_log vor spaeterer Nutzung.",
                    "draft_status": "bounded_draft_ready",
                    "ready_for_bounded_draft": True,
                    "ready_for_final_submission": False,
                }
            )
    pd.DataFrame(rows).to_csv(results / "thesis_h1_h2_h3_bounded_chapter_draft.csv", index=False)


def _paragraph(area: str, step: str) -> str:
    if step == "method_setup":
        return f"{area} Methode mit Evidence IDs und deterministischem Artefakt."
    if step == "result_statement":
        return f"{area} Resultat mit wenigen guten Tabellen und Figuren."
    if step == "interpretation_boundary":
        return f"{area} Interpretation bleibt bounded und limitiert."
    if step == "table_figure_integration":
        return f"{area} nutzt wenige gute Tabellen/Figuren statt Rohartefakt-Dumps."
    if step == "source_review_and_citation_gate":
        return f"{area} bleibt source-gated: keine finale Zitation ohne Source Review."
    if step == "future_agent_boundary":
        return f"{area}: keine Runtime-Agenten, kein MCP, llm_audit_log fuer spaeter."
    raise AssertionError(step)
