from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.analysis.thesis_wording_guard import (
    WORDING_GUARD_COLUMNS,
    generate_wording_guard,
)


def test_generate_wording_guard_writes_german_guardrails(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_wording_guard(repo_root=tmp_path)

    guard = pd.read_csv(result.wording_guard_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(guard.columns) == WORDING_GUARD_COLUMNS
    assert result.guard_rows == 4
    assert result.thesis_facing_rows == 3
    assert result.deferred_rows == 1
    assert "Thesis Wording Guard" in doc
    assert "Nicht schreiben" in doc
    assert "llm_audit_log" in doc
    assert chr(223) not in doc


def test_wording_guard_blocks_overclaims_and_keeps_artifact_references(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_wording_guard(repo_root=tmp_path)

    guard = pd.read_csv(result.wording_guard_path)
    h3 = guard[guard["evidence_id"] == "interpretation_h3_top_tier_signal"].iloc[0]
    agents = guard[guard["evidence_id"] == "future_agent_pipeline_guarded"].iloc[0]

    assert "Insiderbeweis" in h3["blocked_thesis_wording_de"]
    assert "Timingdiagnostik" in h3["allowed_thesis_wording_de"]
    assert h3["required_artifact_reference"] == "data/results/thesis_h3_summary.csv"
    assert agents["final_use_gate"] == "future_work_or_appendix_only"
    assert "agentenberechnete Metriken" in agents["blocked_thesis_wording_de"]
    assert guard["required_artifact_reference"].str.len().gt(0).all()


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    results.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "evidence_id": "method_h1_brier_dm",
                "thesis_area": "H1",
                "item_type": "method",
                "claim_or_decision": "Forecast quality method.",
                "primary_artifact": "data/results/thesis_h1_summary.csv",
                "supporting_artifacts": "",
                "literature_sources": "lit_brier_001",
                "allowed_wording": "bounded",
                "blocked_wording": "overclaim",
                "main_limitation": "daily rows",
                "thesis_readiness": "thesis_facing_ready",
            },
            {
                "evidence_id": "interpretation_h2_daily_response",
                "thesis_area": "H2",
                "item_type": "interpretation",
                "claim_or_decision": "Daily event response.",
                "primary_artifact": "data/results/h2_event_window_summary.csv",
                "supporting_artifacts": "",
                "literature_sources": "lit_eventstudy_001",
                "allowed_wording": "bounded",
                "blocked_wording": "overclaim",
                "main_limitation": "daily frequency",
                "thesis_readiness": "thesis_facing_ready",
            },
            {
                "evidence_id": "interpretation_h3_top_tier_signal",
                "thesis_area": "H3",
                "item_type": "interpretation",
                "claim_or_decision": "Top tier timing.",
                "primary_artifact": "data/results/thesis_h3_summary.csv",
                "supporting_artifacts": "",
                "literature_sources": "lit_granger_001",
                "allowed_wording": "bounded",
                "blocked_wording": "overclaim",
                "main_limitation": "multiple testing",
                "thesis_readiness": "thesis_facing_ready",
            },
            {
                "evidence_id": "future_agent_pipeline_guarded",
                "thesis_area": "future_agents",
                "item_type": "future_work",
                "claim_or_decision": "Future agents.",
                "primary_artifact": "docs/research/STRATEGY_AGENT_ARCHITECTURE.md",
                "supporting_artifacts": "",
                "literature_sources": "zotero_poly_010",
                "allowed_wording": "future",
                "blocked_wording": "active",
                "main_limitation": "deferred",
                "thesis_readiness": "future_work_deferred",
            },
        ]
    ).to_csv(results / "thesis_evidence_map.csv", index=False)
