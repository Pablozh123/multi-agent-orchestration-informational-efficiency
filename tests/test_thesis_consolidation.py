from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.thesis_consolidation import (
    EVIDENCE_COLUMNS,
    generate_thesis_consolidation,
)


def test_generate_thesis_consolidation_writes_traceable_outputs(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_consolidation(repo_root=tmp_path)

    evidence = pd.read_csv(result.evidence_map_path)
    core = pd.read_csv(result.core_results_path)
    package = pd.read_csv(result.curated_package_path)
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(evidence.columns) == EVIDENCE_COLUMNS
    assert result.evidence_rows == 13
    assert result.core_result_rows == 6
    assert metadata["method"]["does_not_use_llms"] is True
    assert metadata["method"]["does_not_use_agents_or_mcp"] is True
    assert metadata["guardrails"]["future_agents_documentation_only"] is True
    assert metadata["outputs"]["core_table_count"] <= metadata["outputs"]["max_core_tables"]
    assert metadata["outputs"]["core_figure_count"] <= metadata["outputs"]["max_core_figures"]
    assert "Deferred Agent Pipeline Idea" in doc
    assert core["bounded_interpretation"].str.len().gt(0).all()
    assert package["main_limitation"].str.len().gt(0).all()


def test_thesis_facing_evidence_has_artifacts_and_ready_sources(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_consolidation(repo_root=tmp_path)

    evidence = pd.read_csv(result.evidence_map_path)
    literature = pd.read_csv(tmp_path / "data/literature/literature_index.csv")
    source_status = literature.set_index("source_id")["status"].to_dict()
    thesis_facing = evidence[evidence["thesis_readiness"] == "thesis_facing_ready"]

    assert set(thesis_facing["item_type"]).issuperset({"method", "interpretation"})
    for row in thesis_facing.to_dict(orient="records"):
        assert row["primary_artifact"]
        assert row["literature_sources"]
        for source_id in _split_sources(row["literature_sources"]):
            assert source_status[source_id] not in {"candidate", "rejected"}


def test_curated_package_keeps_agents_deferred(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_consolidation(repo_root=tmp_path)

    package = pd.read_csv(result.curated_package_path)
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    future = package[package["thesis_section"] == "future_agents"]

    assert len(future) == 1
    assert future.iloc[0]["include_in_core_package"] in {False, "False", "false"}
    assert future.iloc[0]["thesis_readiness"] == "future_work_deferred"
    assert metadata["guardrails"]["llm_audit_log_required_before_future_llm_calls"] is True
    assert metadata["guardrails"]["no_order_or_trading_paths"] is True


def test_missing_source_artifact_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Required thesis consolidation source artifact"):
        generate_thesis_consolidation(repo_root=tmp_path)


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs = root / "docs/research"
    literature_dir = root / "data/literature"
    results.mkdir(parents=True)
    docs.mkdir(parents=True)
    literature_dir.mkdir(parents=True)

    _write_literature(literature_dir / "literature_index.csv")
    (docs / "RESEARCH_SPEC.md").write_text("research spec\n", encoding="utf-8")
    (docs / "STRATEGY_AGENT_ARCHITECTURE.md").write_text("agent architecture\n", encoding="utf-8")
    (docs / "SWISS_REFERENDUM_EFFICIENCY.md").write_text("swiss note\n", encoding="utf-8")
    (root / "data").mkdir(exist_ok=True)
    pd.DataFrame({"event_id": ["evt_1"]}).to_csv(root / "data/events_timeline_seed.csv", index=False)
    pd.DataFrame({"poll_id": ["poll_1"]}).to_csv(
        root / "data/swiss_referendum_10mio_polls.csv",
        index=False,
    )

    pd.DataFrame({"summary_id": ["h1"], "value": [1]}).to_csv(
        results / "thesis_h1_summary.csv",
        index=False,
    )
    pd.DataFrame({"date": ["2024-01-01"], "bs_polymarket": [0.1]}).to_csv(
        results / "h1_brier_scores.csv",
        index=False,
    )
    (results / "h1_diebold_mariano.json").write_text("[]\n", encoding="utf-8")
    pd.DataFrame(
        {
            "evidence_id": ["a", "b"],
            "aggregate_mean_supports_polymarket": [True, False],
            "majority_cases_supports_polymarket": [True, False],
            "broad_many_cases_claim_supported": [False, False],
        }
    ).to_csv(results / "h1_forecast_quality_synthesis.csv", index=False)
    pd.DataFrame(
        {
            "summary_id": ["contradiction_row_count"],
            "value": [1],
            "unit": ["rows"],
            "description": ["toy"],
        }
    ).to_csv(results / "h1_claim_evidence_audit_summary.csv", index=False)
    pd.DataFrame(
        {
            "summary_id": [
                "primary_polymarket_support_count",
                "primary_comparison_count",
                "primary_polymarket_support_share",
            ],
            "value": [8, 10, 0.8],
            "unit": ["rows", "rows", "share"],
            "description": ["toy", "toy", "toy"],
        }
    ).to_csv(results / "h1_poll_claim_readiness_summary.csv", index=False)
    pd.DataFrame({"summary_id": ["h1_poll"], "value": [1]}).to_csv(
        results / "h1_poll_comparison_result_summary.csv",
        index=False,
    )
    _write_binary(results / "h1_poll_claim_readiness.png")

    pd.DataFrame(
        {
            "event_id": ["evt_1"],
            "window_label": ["primary_0d_to_1d"],
            "final_cumulative_abnormal_change": [0.05],
        }
    ).to_csv(results / "h2_event_window_summary.csv", index=False)
    pd.DataFrame({"event_id": ["evt_1"]}).to_csv(results / "h2_event_window_rows.csv", index=False)
    pd.DataFrame({"summary_id": ["h2"], "value": [1]}).to_csv(
        results / "thesis_h2_summary.csv",
        index=False,
    )
    _write_binary(results / "thesis_h2_event_window_car.png")

    (results / "h3_wallet_distribution_inventory.json").write_text(
        json.dumps({"tier_counts": {"tier_1_top_1pct": 1}}),
        encoding="utf-8",
    )
    pd.DataFrame({"tier": ["tier_1_top_1pct"]}).to_csv(results / "h3_wallet_tiers.csv", index=False)
    pd.DataFrame({"tier": ["tier_1_top_1pct"]}).to_csv(
        results / "h3_tiered_wallet_activity_daily.csv",
        index=False,
    )
    pd.DataFrame({"tier": ["tier_1_top_1pct"], "lag_days": [1]}).to_csv(
        results / "h3_granger_results.csv",
        index=False,
    )
    pd.DataFrame({"tier": ["tier_1_top_1pct"], "lag_days": [1]}).to_csv(
        results / "h3_lead_lag_correlations.csv",
        index=False,
    )
    pd.DataFrame(
        {
            "summary_id": [
                "h3_model_row_count",
                "h3_top_abs_correlation_tier_1_top_1pct",
                "h3_min_granger_p_value_tier_1_top_1pct",
            ],
            "label": [
                "daily rows",
                "tier_1_top_1pct lag 1",
                "tier_1_top_1pct lag 1",
            ],
            "value": [20, 0.2, 0.03],
        }
    ).to_csv(results / "thesis_h3_summary.csv", index=False)
    _write_binary(results / "thesis_h3_granger_pvalues.png")

    pd.DataFrame(
        {
            "queue_row_count": [2],
            "high_priority_count": [1],
            "medium_priority_count": [1],
            "human_review_status_counts": ["source_check_pending=2"],
        }
    ).to_csv(results / "monitor_anomaly_review_summary.csv", index=False)
    pd.DataFrame({"case_id": ["c1"]}).to_csv(results / "monitor_anomaly_review_queue.csv", index=False)
    pd.DataFrame({"case_id": ["c1"]}).to_csv(
        results / "monitor_anomaly_review_decision_readiness.csv",
        index=False,
    )
    pd.DataFrame({"case_id": ["c1"]}).to_csv(
        results / "monitor_anomaly_case_review_packets.csv",
        index=False,
    )
    (results / "monitor_anomaly_review_dashboard.html").write_text("dashboard\n", encoding="utf-8")

    pd.DataFrame(
        {
            "polymarket_yes_probability": [0.22],
            "poll_yes_share": [0.45],
        }
    ).to_csv(results / "swiss_referendum_10mio_comparison.csv", index=False)
    pd.DataFrame(
        {
            "source_name": ["source"],
            "polymarket_yes_probability": [0.22],
            "poll_yes_share": [0.45],
            "raw_yes_gap": [-0.23],
        }
    ).to_csv(results / "swiss_referendum_10mio_latest_source_comparison.csv", index=False)
    _write_binary(results / "swiss_referendum_10mio_efficiency.png")


def _write_literature(path: Path) -> None:
    source_ids = [
        ("lit_emh_001", "skimmed"),
        ("lit_brier_001", "skimmed"),
        ("lit_dm_001", "skimmed"),
        ("lit_eventstudy_001", "skimmed"),
        ("lit_granger_001", "skimmed"),
        ("zotero_poly_001", "skimmed"),
        ("zotero_poly_002", "skimmed"),
        ("zotero_poly_005", "skimmed"),
        ("zotero_poly_006", "skimmed"),
        ("zotero_poly_007", "skimmed"),
        ("zotero_poly_009", "skimmed"),
        ("zotero_poly_010", "candidate"),
    ]
    pd.DataFrame(
        [
            {
                "source_id": source_id,
                "title": f"Title {source_id}",
                "authors": "Author",
                "year": "2026",
                "venue": "Venue",
                "url": "https://example.com",
                "local_file": "",
                "topic": "topic",
                "hypothesis": "H1",
                "method": "method",
                "relevance": "relevance",
                "status": status,
                "notes": "notes",
            }
            for source_id, status in source_ids
        ]
    ).to_csv(path, index=False)


def _write_binary(path: Path) -> None:
    path.write_bytes(b"not-empty")


def _split_sources(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]
