from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.thesis_consolidation import (
    AGENT_ASSISTANCE_PROTOCOL_COLUMNS,
    AGENT_PIPELINE_COLUMNS,
    CHAPTER_PLAN_COLUMNS,
    CITATION_READINESS_COLUMNS,
    CITATION_REVIEW_PACKET_COLUMNS,
    EVIDENCE_COLUMNS,
    NEXT_WORK_PLAN_COLUMNS,
    PROJECT_HIGHLEVEL_VIEW_COLUMNS,
    SOURCE_REVIEW_PLAN_COLUMNS,
    TABLE_FIGURE_CAPTION_COLUMNS,
    generate_thesis_consolidation,
)


def test_generate_thesis_consolidation_writes_traceable_outputs(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_consolidation(repo_root=tmp_path)

    evidence = pd.read_csv(result.evidence_map_path)
    core = pd.read_csv(result.core_results_path)
    package = pd.read_csv(result.curated_package_path)
    citations = pd.read_csv(result.citation_readiness_path)
    citation_packets = pd.read_csv(result.citation_review_packets_path)
    captions = pd.read_csv(result.table_figure_captions_path)
    source_review_plan = pd.read_csv(result.source_review_plan_path)
    agent_protocol = pd.read_csv(result.agent_assistance_protocol_path)
    next_work_plan = pd.read_csv(result.next_work_plan_path)
    project_highlevel = pd.read_csv(result.project_highlevel_view_path)
    chapters = pd.read_csv(result.chapter_plan_path)
    agents = pd.read_csv(result.agent_pipeline_path)
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    doc = result.docs_path.read_text(encoding="utf-8")
    agent_doc = result.agent_docs_path.read_text(encoding="utf-8")
    writing_blueprint = result.writing_blueprint_path.read_text(encoding="utf-8")
    chapter_draft = result.chapter_draft_path.read_text(encoding="utf-8")
    citation_packet_doc = result.citation_review_docs_path.read_text(encoding="utf-8")
    caption_doc = result.table_figure_captions_docs_path.read_text(encoding="utf-8")
    source_review_doc = result.source_review_plan_docs_path.read_text(encoding="utf-8")
    agent_protocol_doc = result.agent_assistance_protocol_docs_path.read_text(encoding="utf-8")
    next_work_doc = result.next_work_plan_docs_path.read_text(encoding="utf-8")
    project_highlevel_doc = result.project_highlevel_view_docs_path.read_text(encoding="utf-8")

    assert tuple(evidence.columns) == EVIDENCE_COLUMNS
    assert tuple(citations.columns) == CITATION_READINESS_COLUMNS
    assert tuple(citation_packets.columns) == CITATION_REVIEW_PACKET_COLUMNS
    assert tuple(captions.columns) == TABLE_FIGURE_CAPTION_COLUMNS
    assert tuple(source_review_plan.columns) == SOURCE_REVIEW_PLAN_COLUMNS
    assert tuple(agent_protocol.columns) == AGENT_ASSISTANCE_PROTOCOL_COLUMNS
    assert tuple(next_work_plan.columns) == NEXT_WORK_PLAN_COLUMNS
    assert tuple(project_highlevel.columns) == PROJECT_HIGHLEVEL_VIEW_COLUMNS
    assert tuple(chapters.columns) == CHAPTER_PLAN_COLUMNS
    assert tuple(agents.columns) == AGENT_PIPELINE_COLUMNS
    assert result.evidence_rows == 13
    assert result.core_result_rows == 6
    assert result.citation_rows == 12
    assert result.citation_review_packet_rows == 33
    assert result.table_figure_caption_rows == 10
    assert result.source_review_plan_rows == 12
    assert result.agent_assistance_protocol_rows == 7
    assert result.next_work_plan_rows == 10
    assert result.project_highlevel_view_rows == 10
    assert result.chapter_rows == 8
    assert result.agent_stage_rows == 6
    assert metadata["method"]["does_not_use_llms"] is True
    assert metadata["method"]["does_not_use_agents_or_mcp"] is True
    assert metadata["guardrails"]["citation_readiness_is_status_mapping_not_source_promotion"] is True
    assert metadata["guardrails"]["chapter_plan_uses_curated_package"] is True
    assert metadata["guardrails"]["future_agents_documentation_only"] is True
    assert metadata["outputs"]["core_table_count"] <= metadata["outputs"]["max_core_tables"]
    assert metadata["outputs"]["core_figure_count"] <= metadata["outputs"]["max_core_figures"]
    assert metadata["outputs"]["writing_blueprint_generated"] is True
    assert metadata["outputs"]["chapter_draft_generated"] is True
    assert metadata["outputs"]["citation_review_packet_rows"] == 33
    assert metadata["outputs"]["table_figure_caption_rows"] == 10
    assert metadata["outputs"]["source_review_plan_rows"] == 12
    assert metadata["outputs"]["agent_assistance_protocol_rows"] == 7
    assert metadata["outputs"]["next_work_plan_rows"] == 10
    assert metadata["outputs"]["project_highlevel_view_rows"] == 10
    assert metadata["table_figure_caption_counts"]["core_table_captions"] == 5
    assert metadata["table_figure_caption_counts"]["core_figure_captions"] == 4
    assert metadata["guardrails"]["citation_review_packets_are_pending_human_review"] is True
    assert metadata["guardrails"]["table_figure_captions_use_curated_package_only"] is True
    assert metadata["guardrails"]["source_review_plan_is_manual_review_queue"] is True
    assert metadata["guardrails"]["agent_assistance_protocol_is_documentation_only"] is True
    assert metadata["guardrails"]["next_work_plan_is_guardrail_bound"] is True
    assert metadata["guardrails"]["project_highlevel_view_keeps_review_access_paused"] is True
    assert metadata["project_highlevel_view_counts"]["paused_rows"] == 1
    assert metadata["project_highlevel_view_counts"]["documentation_only_rows"] == 1
    assert "Deferred Agent Pipeline Idea" in doc
    assert "Project Highlevel View" in doc
    assert "Citation Readiness" in doc
    assert "Citation Review Packets" in doc
    assert "Thesis Agent Pipeline Roadmap" in agent_doc
    assert "Thesis Writing Blueprint" in writing_blueprint
    assert "Agent-Assisted Pipeline Outlook" in writing_blueprint
    assert "Thesis Chapter Draft" in chapter_draft
    assert "keine neuen Kennzahlen" in chapter_draft
    assert "Thesis Citation Review Packets" in citation_packet_doc
    assert "Thesis Table And Figure Captions" in caption_doc
    assert "Thesis Source Review Plan" in source_review_doc
    assert "Thesis Agent Assistance Protocol" in agent_protocol_doc
    assert "Thesis Next Work Plan" in next_work_doc
    assert "Thesis Project Highlevel View" in project_highlevel_doc
    assert "review access remains paused" in project_highlevel_doc
    assert "Review-Access bleibt pausiert" in project_highlevel_doc
    assert "Dozentenpaket senden" in project_highlevel_doc
    assert "Source Structure Inventory und Traceability Audit nur" in project_highlevel_doc
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


def test_citation_readiness_blocks_candidate_sources_from_thesis_claims(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_consolidation(repo_root=tmp_path)

    citations = pd.read_csv(result.citation_readiness_path)
    candidate = citations[citations["source_id"] == "zotero_poly_010"].iloc[0]
    thesis_sources = citations[citations["used_by_thesis_areas"].fillna("").str.contains("H")]

    assert candidate["final_citation_readiness"] == "not_allowed_for_thesis_facing_claims"
    assert candidate["citation_risk"] == "high"
    assert not thesis_sources["status"].isin({"candidate", "rejected"}).any()


def test_citation_review_packets_link_sources_to_evidence_and_keep_pending(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_consolidation(repo_root=tmp_path)

    packets = pd.read_csv(result.citation_review_packets_path)
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    candidate = packets[packets["source_id"] == "zotero_poly_010"].iloc[0]
    h_rows = packets[packets["thesis_area"].isin(["H1", "H2", "H3"])]

    assert packets["packet_id"].is_unique
    assert packets["reviewer_decision"].eq("pending").all()
    assert packets["review_question"].str.len().gt(0).all()
    assert packets["primary_artifact"].str.len().gt(0).all()
    assert not h_rows["source_status"].isin({"candidate", "rejected"}).any()
    assert candidate["draft_use_allowed"] in {False, "False", "false"}
    assert candidate["final_citation_gate"] == "metadata_and_relevance_review_before_future_work_use"
    assert metadata["citation_review_packet_counts"]["pending_packets"] == len(packets)


def test_source_review_plan_prioritises_manual_source_checks(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_consolidation(repo_root=tmp_path)

    citations = pd.read_csv(result.citation_readiness_path)
    plan = pd.read_csv(result.source_review_plan_path)
    packets = pd.read_csv(result.citation_review_packets_path)
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    core_priorities = {
        "priority_1_method_foundation_review",
        "priority_2_core_interpretation_review",
    }

    assert set(plan["source_id"]) == set(citations["source_id"])
    assert plan["source_id"].is_unique
    assert plan["evidence_packet_count"].sum() == len(packets)
    assert plan["priority_band"].str.len().gt(0).all()
    assert plan["required_review_output"].str.len().gt(0).all()
    assert plan["thesis_use_boundary"].str.len().gt(0).all()
    assert plan["next_action"].str.len().gt(0).all()
    assert metadata["source_review_plan_counts"]["blocked_or_future_work_only"] == 1

    method_sources = plan[plan["method_packet_count"] > 0]
    assert method_sources["priority_band"].eq("priority_1_method_foundation_review").all()

    risky_core = plan[
        plan["priority_band"].isin(core_priorities)
        & plan["source_status"].isin({"candidate", "rejected"})
    ]
    assert risky_core.empty

    candidate = plan[plan["source_id"] == "zotero_poly_010"].iloc[0]
    assert candidate["priority_band"] == "blocked_or_future_work_only"
    assert candidate["thesis_use_boundary"] == "not_allowed_for_thesis_facing_claims"


def test_chapter_plan_uses_curated_package_ids(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_consolidation(repo_root=tmp_path)

    package = pd.read_csv(result.curated_package_path)
    chapters = pd.read_csv(result.chapter_plan_path)
    known_package_ids = set(package["package_id"])
    referenced_ids: set[str] = set()
    for row in chapters.to_dict(orient="records"):
        referenced_ids.update(_split_sources(row.get("recommended_tables", "")))
        referenced_ids.update(_split_sources(row.get("recommended_figures", "")))

    assert referenced_ids
    assert referenced_ids.issubset(known_package_ids)
    assert chapters["main_limitation_to_state"].str.len().gt(0).all()


def test_table_figure_captions_cover_curated_core_package(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_consolidation(repo_root=tmp_path)

    package = pd.read_csv(result.curated_package_path)
    captions = pd.read_csv(result.table_figure_captions_path)
    core_package = package[package["include_in_core_package"].astype(bool)]
    core_captions = captions[captions["include_in_core_package"].astype(bool)]

    assert set(captions["package_id"]) == set(package["package_id"])
    assert set(core_captions["package_id"]) == set(core_package["package_id"])
    assert captions["thesis_label"].is_unique
    assert (core_captions["package_type"] == "table").sum() == 5
    assert (core_captions["package_type"] == "figure").sum() == 4
    for column in (
        "caption_de",
        "source_note_de",
        "interpretation_note_de",
        "limitation_note_de",
    ):
        assert captions[column].astype(str).str.len().gt(0).all()
        assert not captions[column].astype(str).str.contains(chr(195) + chr(376), regex=False).any()


def test_agent_pipeline_is_documentation_only_and_audited(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_consolidation(repo_root=tmp_path)

    agents = pd.read_csv(result.agent_pipeline_path)
    joined = "\n".join(agents.fillna("").astype(str).agg(" ".join, axis=1).tolist())

    assert set(agents["implementation_status"]).issubset(
        {"current_required_state", "future_documentation_only", "future_deferred"}
    )
    assert "llm_audit_log" in joined
    assert "raw table" in joined
    assert "wallet-address" in joined
    assert "order or trading paths" in joined


def test_agent_assistance_protocol_is_documentation_only(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_consolidation(repo_root=tmp_path)

    protocol = pd.read_csv(result.agent_assistance_protocol_path)
    joined = "\n".join(protocol.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert set(protocol["activation_status"]).issubset(
        {"future_documentation_only", "future_deferred"}
    )
    assert protocol["protocol_id"].is_unique
    assert "llm_audit_log" in joined
    assert "raw table" in joined
    assert "order or trading paths" in joined
    assert "calculating metrics" in joined
    assert "no status changes" in joined
    assert metadata["agent_assistance_protocol_counts"]["future_documentation_only"] == 6
    assert metadata["agent_assistance_protocol_counts"]["future_deferred"] == 1


def test_next_work_plan_orders_remaining_work_with_guardrails(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_consolidation(repo_root=tmp_path)

    plan = pd.read_csv(result.next_work_plan_path)
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    joined = "\n".join(plan.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert plan["workstream_id"].is_unique
    assert plan["priority_order"].tolist() == list(range(1, len(plan) + 1))
    assert plan.iloc[0]["workstream_id"] == "work_01_source_review"
    assert plan.iloc[-1]["workstream_id"] == "work_10_final_qa"
    assert plan["next_action"].str.len().gt(0).all()
    assert plan["done_when"].str.len().gt(0).all()
    assert plan["blocked_until"].str.len().gt(0).all()
    assert plan["guardrail"].str.len().gt(0).all()
    assert "llm_audit_log" in joined
    assert "no order or trading paths" in joined
    assert "official 14 june 2026 vote result" in joined
    assert "deterministic artifacts" in joined
    assert metadata["next_work_plan_counts"]["highest_priority"] == "work_01_source_review"
    assert metadata["next_work_plan_counts"]["final_priority"] == "work_10_final_qa"


def test_project_highlevel_view_keeps_paused_and_deferred_boundaries(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_consolidation(repo_root=tmp_path)

    view = pd.read_csv(result.project_highlevel_view_path)
    monitor = view[view["view_id"] == "project_06_monitor_review_access"].iloc[0]
    swiss = view[view["view_id"] == "project_07_swiss_referendum"].iloc[0]
    agents = view[view["view_id"] == "project_08_future_agents"].iloc[0]
    joined = "\n".join(view.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert monitor["status"] == "paused_appendix_only"
    assert "review access remains paused" in monitor["current_decision"].lower()
    assert "draft writing" in monitor["current_decision"].lower()
    assert "no order or trading paths" in monitor["guardrail"].lower()
    assert swiss["status"] == "descriptive_pending_result"
    assert "official 14 june 2026 vote result" in swiss["current_decision"].lower()
    assert agents["status"] == "documentation_only_deferred"
    assert "llm_audit_log" in agents["next_gate"]
    assert "no runtime agents" in agents["guardrail"].lower()
    assert "reactivate review access" in joined
    assert "deterministic python artifacts" in joined
    assert "do not infer support claims from file structure" in joined
    assert set(view["status"]).issuperset(
        {
            "thesis_facing_ready",
            "paused_appendix_only",
            "documentation_only_deferred",
        }
    )


def test_writing_blueprint_keeps_front_matter_method_focused(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_consolidation(repo_root=tmp_path)

    blueprint = result.writing_blueprint_path.read_text(encoding="utf-8")
    front_matter = blueprint.split("## H1: Prognosequalitaet", maxsplit=1)[0]

    assert "Result statements to use:" not in front_matter
    assert "Core Writing Rule" in front_matter
    assert "data/results/thesis_citation_readiness.csv" in front_matter


def test_chapter_draft_is_traceable_and_uses_swiss_spelling(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_consolidation(repo_root=tmp_path)

    draft = result.chapter_draft_path.read_text(encoding="utf-8")

    assert chr(223) not in draft
    assert chr(195) + chr(376) not in draft
    assert "Forecast quality is evaluated" not in draft
    assert "interpretation_h1_bounded_advantage" in draft
    assert "data/results/h2_event_window_summary.csv" in draft
    assert "llm_audit_log" in draft
    assert "keine universelle Aussage" in draft


def test_missing_source_artifact_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Required thesis consolidation source artifact"):
        generate_thesis_consolidation(repo_root=tmp_path)


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs = root / "docs/research"
    project_docs = root / "docs/project"
    literature_dir = root / "data/literature"
    results.mkdir(parents=True)
    docs.mkdir(parents=True)
    project_docs.mkdir(parents=True)
    literature_dir.mkdir(parents=True)

    _write_literature(literature_dir / "literature_index.csv")
    (docs / "RESEARCH_SPEC.md").write_text("research spec\n", encoding="utf-8")
    (docs / "STRATEGY_AGENT_ARCHITECTURE.md").write_text("agent architecture\n", encoding="utf-8")
    (docs / "SWISS_REFERENDUM_EFFICIENCY.md").write_text("swiss note\n", encoding="utf-8")
    (project_docs / "dozentenbericht_ba_thesis.md").write_text("advisor report\n", encoding="utf-8")
    _write_binary(project_docs / "dozentenbericht_ba_thesis.docx")
    (project_docs / "THESIS_ADVISOR_HANDOFF_PACKAGE.md").write_text(
        "advisor package\n",
        encoding="utf-8",
    )
    (project_docs / "DOZENTEN_FEEDBACK_LOG.md").write_text(
        "feedback log\n",
        encoding="utf-8",
    )
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
    (results / "monitor_anomaly_review_access_contract.json").write_text("{}\n", encoding="utf-8")

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


def _split_sources(value: object) -> list[str]:
    if pd.isna(value):
        return []
    return [item.strip() for item in str(value).split(";") if item.strip()]
