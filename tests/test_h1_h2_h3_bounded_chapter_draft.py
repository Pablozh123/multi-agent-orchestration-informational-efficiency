from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from operations.project.build_h1_h2_h3_bounded_chapter_draft import (
    DRAFT_COLUMNS,
    generate_h1_h2_h3_bounded_chapter_draft,
)


def test_generate_h1_h2_h3_bounded_chapter_draft_writes_ordered_rows(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_h1_h2_h3_bounded_chapter_draft(repo_root=tmp_path)

    draft = pd.read_csv(result.draft_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(draft.columns) == DRAFT_COLUMNS
    assert result.draft_rows == 18
    assert result.bounded_ready_rows == 18
    assert result.final_ready_rows == 0
    assert set(draft["thesis_area"].value_counts().to_dict().values()) == {6}
    assert "H1-H2-H3 Bounded Chapter Draft" in doc
    assert "Draft rows: 18" in doc
    assert "Final submission ready rows: 0" in doc
    assert "method_h1_brier_dm" in doc
    assert "interpretation_h1_bounded_advantage" in doc
    assert "lit_brier_001" in doc
    assert "data/results/thesis_h1_summary.csv" in doc
    assert "Source-Coverage: 10 Links" in doc
    assert "Coverage-Gaps: 0" in doc
    assert "wenige gute Tabellen" in doc
    assert "Keine finale Zitation" in doc
    assert "keine Runtime-Agenten" in doc
    assert "llm_audit_log" in doc
    assert chr(223) not in doc


def test_h1_h2_h3_bounded_chapter_draft_keeps_mapping_columns_complete(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_h1_h2_h3_bounded_chapter_draft(repo_root=tmp_path)

    draft = pd.read_csv(result.draft_path)
    joined = "\n".join(draft.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    for column in (
        "method_evidence_ids",
        "interpretation_evidence_ids",
        "literature_source_ids",
        "deterministic_artifacts",
    ):
        assert draft[column].astype(str).str.len().gt(0).all()
    assert "source review" in joined
    assert "keine finale zitation" in joined
    assert "keine rohartefakt-dumps" in joined
    assert "keine runtime-agenten" in joined
    assert "method_h3_granger_timing" in joined
    assert "interpretation_h3_top_tier_signal" in joined
    assert "source-coverage" in joined
    assert draft["source_coverage_gap_rows"].astype(int).eq(0).all()


def test_h1_h2_h3_bounded_chapter_draft_fails_on_missing_artifact(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    (tmp_path / "data/results/thesis_h1_summary.csv").unlink()

    with pytest.raises(FileNotFoundError, match="H1-H2-H3 draft artifact missing"):
        generate_h1_h2_h3_bounded_chapter_draft(repo_root=tmp_path)


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    data = root / "data"
    results.mkdir(parents=True)
    data.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(
        [
            _core_section(
                "core_section_h1",
                "H1",
                "H1: Prognosequalitaet",
                "method_h1_brier_dm",
                "interpretation_h1_bounded_advantage; interpretation_h1_broad_claim_not_proven",
                "lit_brier_001; lit_dm_001",
                "data/results/thesis_h1_summary.csv; data/results/h1_brier_scores.csv",
                "T2",
                "F1",
                "H1 Resultatseed.",
                "Polymarket nur in klar definierten Vergleichsscopes.",
                "H1 Limitation.",
                "allgemeine Ueberlegenheit",
            ),
            _core_section(
                "core_section_h2",
                "H2",
                "H2: Tagesbasierte Ereignisfenster",
                "method_h2_event_window",
                "interpretation_h2_daily_response",
                "lit_eventstudy_001; lit_emh_001",
                "data/results/h2_event_window_summary.csv; data/events_timeline_seed.csv",
                "T3",
                "F2",
                "H2 Resultatseed.",
                "Tagesbewegungen, keine Intraday-Aussage.",
                "H2 Limitation.",
                "Intraday-Geschwindigkeitsaussage",
            ),
            _core_section(
                "core_section_h3",
                "H3",
                "H3: Wallet-Timing-Diagnostik",
                "method_h3_wallet_tiers; method_h3_granger_timing",
                "interpretation_h3_top_tier_signal",
                "lit_granger_001; zotero_poly_001",
                "data/results/thesis_h3_summary.csv; data/results/h3_granger_results.csv",
                "T4",
                "F3",
                "H3 Resultatseed.",
                "Predictive timing diagnostic, kein Kausalbeweis.",
                "H3 Limitation.",
                "Profitabilitaetsbeweis",
            ),
        ]
    ).to_csv(results / "thesis_h1_h2_h3_core_sections.csv", index=False)
    pd.DataFrame(
        [
            _drafting_row(area, section_id, title, order, step, methods, interpretations, literature, artifacts, items)
            for area, section_id, title, methods, interpretations, literature, artifacts, items in [
                (
                    "H1",
                    "core_section_h1",
                    "H1: Prognosequalitaet",
                    "method_h1_brier_dm",
                    "interpretation_h1_bounded_advantage; interpretation_h1_broad_claim_not_proven",
                    "lit_brier_001; lit_dm_001",
                    "data/results/thesis_h1_summary.csv; data/results/h1_brier_scores.csv",
                    "T2; F1",
                ),
                (
                    "H2",
                    "core_section_h2",
                    "H2: Tagesbasierte Ereignisfenster",
                    "method_h2_event_window",
                    "interpretation_h2_daily_response",
                    "lit_eventstudy_001; lit_emh_001",
                    "data/results/h2_event_window_summary.csv; data/events_timeline_seed.csv",
                    "T3; F2",
                ),
                (
                    "H3",
                    "core_section_h3",
                    "H3: Wallet-Timing-Diagnostik",
                    "method_h3_wallet_tiers; method_h3_granger_timing",
                    "interpretation_h3_top_tier_signal",
                    "lit_granger_001; zotero_poly_001",
                    "data/results/thesis_h3_summary.csv; data/results/h3_granger_results.csv",
                    "T4; F3",
                ),
            ]
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
            )
        ]
    ).to_csv(results / "thesis_h1_h2_h3_drafting_checklist.csv", index=False)
    pd.DataFrame(
        [
            _handoff("H1", "T2; F1", 10),
            _handoff("H2", "T3; F2", 5),
            _handoff("H3", "T4; F3", 8),
        ]
    ).to_csv(results / "thesis_source_review_chapter_handoff.csv", index=False)
    pd.DataFrame(
        [
            _caption("T2", "tab:t2", "H1 caption", "data/results/thesis_core_results_table.csv"),
            _caption("F1", "fig:f1", "H1 figure", "data/results/h1_poll_claim_readiness.png"),
            _caption("T3", "tab:t3", "H2 caption", "data/results/h2_event_window_summary.csv"),
            _caption("F2", "fig:f2", "H2 figure", "data/results/thesis_h2_event_window_car.png"),
            _caption("T4", "tab:t4", "H3 caption", "data/results/thesis_h3_summary.csv"),
            _caption("F3", "fig:f3", "H3 figure", "data/results/thesis_h3_granger_pvalues.png"),
        ]
    ).to_csv(results / "thesis_table_figure_captions.csv", index=False)
    pd.DataFrame(
        [
            *[_source_coverage("H1", f"h1_source_{idx}") for idx in range(10)],
            *[_source_coverage("H2", f"h2_source_{idx}") for idx in range(5)],
            *[_source_coverage("H3", f"h3_source_{idx}") for idx in range(8)],
        ]
    ).to_csv(results / "thesis_method_interpretation_source_coverage.csv", index=False)

    for relative in [
        "data/results/thesis_h1_summary.csv",
        "data/results/h1_brier_scores.csv",
        "data/results/thesis_core_results_table.csv",
        "data/results/h1_poll_claim_readiness.png",
        "data/results/h2_event_window_summary.csv",
        "data/events_timeline_seed.csv",
        "data/results/thesis_h2_event_window_car.png",
        "data/results/thesis_h3_summary.csv",
        "data/results/h3_granger_results.csv",
        "data/results/thesis_h3_granger_pvalues.png",
    ]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")


def _core_section(
    section_id: str,
    hypothesis: str,
    title: str,
    methods: str,
    interpretations: str,
    literature: str,
    artifacts: str,
    table: str,
    figure: str,
    result: str,
    interpretation: str,
    limitation: str,
    blocked: str,
) -> dict[str, str]:
    return {
        "section_id": section_id,
        "hypothesis": hypothesis,
        "chapter_title_de": title,
        "method_evidence_ids": methods,
        "interpretation_evidence_ids": interpretations,
        "literature_source_ids": literature,
        "deterministic_artifacts": artifacts,
        "selected_tables": table,
        "selected_figures": figure,
        "thesis_ready_result_de": result,
        "bounded_interpretation_de": interpretation,
        "mandatory_limitation_de": limitation,
        "blocked_wording_de": blocked,
        "source_review_gate_de": "Keine finale Zitation ohne Source Review.",
    }


def _drafting_row(
    area: str,
    section_id: str,
    title: str,
    order: int,
    step: str,
    methods: str,
    interpretations: str,
    literature: str,
    artifacts: str,
    items: str,
) -> dict[str, object]:
    return {
        "draft_check_id": f"draft_{area.lower()}_{order:02d}_{step}",
        "thesis_area": area,
        "section_id": section_id,
        "chapter_title_de": title,
        "draft_order": order,
        "draft_step": step,
        "method_evidence_ids": methods,
        "interpretation_evidence_ids": interpretations,
        "literature_source_ids": literature,
        "deterministic_artifacts": artifacts,
        "result_package_items": items,
        "source_review_gate": f"{area}: Keine finale Zitation ohne Source Review.",
        "thesis_ready_text_seed_de": f"{area} Textseed fuer {step}.",
        "mandatory_limitation_de": f"{area} Limitation.",
        "blocked_wording_de": "Keine Rohartefakt-Dumps",
        "completion_status": (
            "final_blocked_source_review_pending"
            if step == "source_review_and_citation_gate"
            else "bounded_draft_ready"
        ),
        "ready_for_bounded_draft": True,
        "ready_for_final_submission": False,
        "future_agent_boundary_de": (
            "Agentenstatus bleibt future_documentation_only: keine Runtime-Agenten, "
            "kein MCP, kein Model Routing, keine LLM-Metriken, max 50 rows und llm_audit_log."
        ),
    }


def _handoff(area: str, items: str, review_rows: int) -> dict[str, object]:
    return {
        "thesis_area": area,
        "source_review_rows": review_rows,
        "pending_review_rows": review_rows,
        "final_citation_ready_rows": 0,
        "result_package_items": items,
        "required_source_review_de": f"{area}: Source Review pending.",
    }


def _caption(package_id: str, label: str, caption: str, artifact: str) -> dict[str, str]:
    return {
        "package_id": package_id,
        "thesis_label": label,
        "caption_de": caption,
        "primary_artifact": artifact,
        "limitation_note_de": "Fixture limitation.",
    }


def _source_coverage(area: str, source_id: str) -> dict[str, object]:
    return {
        "coverage_id": f"coverage_{area.lower()}_{source_id}",
        "evidence_id": f"method_{area.lower()}",
        "thesis_area": area,
        "item_type": "method",
        "thesis_readiness": "thesis_facing_ready",
        "source_id": source_id,
        "source_known_in_literature_index": True,
        "source_status": "skimmed",
        "source_relevance": "high",
        "final_citation_readiness": "needs_full_source_review_before_final_citation",
        "primary_artifact": "data/results/thesis_core_results_table.csv",
        "primary_artifact_exists": True,
        "supporting_artifact_count": 1,
        "supporting_artifact_exists_count": 1,
        "limitation_present": True,
        "coverage_status": "source_mapped_final_review_pending",
        "thesis_use_gate_de": "Draft nutzbar; keine finale Zitation ohne manuelle Source Review.",
    }
