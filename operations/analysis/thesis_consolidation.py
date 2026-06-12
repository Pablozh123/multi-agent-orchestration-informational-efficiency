"""Build thesis consolidation artifacts from deterministic outputs.

This module creates a small thesis-facing evidence and result package. It reads
only existing local artifacts, does not call LLMs, does not activate agents or
MCP tools, and does not calculate thesis metrics outside Python.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import pandas as pd


DEFAULT_REPO_ROOT = Path(".")
DEFAULT_RESULTS_DIR = Path("data/results")
DEFAULT_DOCS_DIR = Path("docs/research")
GENERATED_ARTIFACTS: frozenset[str] = frozenset(
    {
        "data/results/thesis_evidence_map.csv",
        "data/results/thesis_evidence_map.md",
        "data/results/thesis_core_results_table.csv",
        "data/results/thesis_curated_result_package.csv",
        "data/results/thesis_citation_readiness.csv",
        "data/results/thesis_chapter_plan.csv",
        "data/results/thesis_agent_pipeline_roadmap.csv",
        "data/results/thesis_citation_review_packets.csv",
        "data/results/thesis_table_figure_captions.csv",
        "data/results/thesis_source_review_plan.csv",
        "data/results/thesis_agent_assistance_protocol.csv",
        "data/results/thesis_next_work_plan.csv",
        "data/results/thesis_project_highlevel_view.csv",
        "data/results/thesis_consolidation_metadata.json",
        "docs/research/THESIS_CONSOLIDATION.md",
        "docs/research/THESIS_AGENT_PIPELINE_ROADMAP.md",
        "docs/research/THESIS_WRITING_BLUEPRINT.md",
        "docs/research/THESIS_CHAPTER_DRAFT.md",
        "docs/research/THESIS_CITATION_REVIEW_PACKETS.md",
        "docs/research/THESIS_TABLE_FIGURE_CAPTIONS.md",
        "docs/research/THESIS_SOURCE_REVIEW_PLAN.md",
        "docs/research/THESIS_AGENT_ASSISTANCE_PROTOCOL.md",
        "docs/research/THESIS_NEXT_WORK_PLAN.md",
        "docs/research/THESIS_PROJECT_HIGHLEVEL_VIEW.md",
    }
)

EVIDENCE_MAP_OUTPUT = "thesis_evidence_map.csv"
EVIDENCE_MAP_MD_OUTPUT = "thesis_evidence_map.md"
CORE_RESULTS_OUTPUT = "thesis_core_results_table.csv"
CURATED_PACKAGE_OUTPUT = "thesis_curated_result_package.csv"
CITATION_READINESS_OUTPUT = "thesis_citation_readiness.csv"
CHAPTER_PLAN_OUTPUT = "thesis_chapter_plan.csv"
AGENT_PIPELINE_OUTPUT = "thesis_agent_pipeline_roadmap.csv"
CITATION_REVIEW_PACKETS_OUTPUT = "thesis_citation_review_packets.csv"
TABLE_FIGURE_CAPTIONS_OUTPUT = "thesis_table_figure_captions.csv"
SOURCE_REVIEW_PLAN_OUTPUT = "thesis_source_review_plan.csv"
AGENT_ASSISTANCE_PROTOCOL_OUTPUT = "thesis_agent_assistance_protocol.csv"
NEXT_WORK_PLAN_OUTPUT = "thesis_next_work_plan.csv"
PROJECT_HIGHLEVEL_VIEW_OUTPUT = "thesis_project_highlevel_view.csv"
METADATA_OUTPUT = "thesis_consolidation_metadata.json"
DOC_OUTPUT = "THESIS_CONSOLIDATION.md"
AGENT_DOC_OUTPUT = "THESIS_AGENT_PIPELINE_ROADMAP.md"
WRITING_BLUEPRINT_OUTPUT = "THESIS_WRITING_BLUEPRINT.md"
CHAPTER_DRAFT_OUTPUT = "THESIS_CHAPTER_DRAFT.md"
CITATION_REVIEW_DOC_OUTPUT = "THESIS_CITATION_REVIEW_PACKETS.md"
TABLE_FIGURE_CAPTIONS_DOC_OUTPUT = "THESIS_TABLE_FIGURE_CAPTIONS.md"
SOURCE_REVIEW_PLAN_DOC_OUTPUT = "THESIS_SOURCE_REVIEW_PLAN.md"
AGENT_ASSISTANCE_PROTOCOL_DOC_OUTPUT = "THESIS_AGENT_ASSISTANCE_PROTOCOL.md"
NEXT_WORK_PLAN_DOC_OUTPUT = "THESIS_NEXT_WORK_PLAN.md"
PROJECT_HIGHLEVEL_VIEW_DOC_OUTPUT = "THESIS_PROJECT_HIGHLEVEL_VIEW.md"

EVIDENCE_COLUMNS: tuple[str, ...] = (
    "evidence_id",
    "thesis_area",
    "item_type",
    "claim_or_decision",
    "primary_artifact",
    "supporting_artifacts",
    "literature_sources",
    "allowed_wording",
    "blocked_wording",
    "main_limitation",
    "thesis_readiness",
)

CORE_RESULT_COLUMNS: tuple[str, ...] = (
    "result_id",
    "thesis_area",
    "recommended_table",
    "headline_result",
    "key_value",
    "primary_artifact",
    "supporting_artifacts",
    "evidence_ids",
    "bounded_interpretation",
    "main_limitation",
    "thesis_readiness",
)

PACKAGE_COLUMNS: tuple[str, ...] = (
    "package_id",
    "package_type",
    "thesis_section",
    "title",
    "primary_artifact",
    "supporting_artifacts",
    "evidence_ids",
    "recommended_placement",
    "include_in_core_package",
    "thesis_message",
    "main_limitation",
    "thesis_readiness",
)

CITATION_READINESS_COLUMNS: tuple[str, ...] = (
    "source_id",
    "title",
    "status",
    "used_by_evidence_ids",
    "used_by_thesis_areas",
    "used_by_item_types",
    "draft_mapping_role",
    "final_citation_readiness",
    "required_next_action",
    "citation_risk",
)

CHAPTER_PLAN_COLUMNS: tuple[str, ...] = (
    "chapter_id",
    "chapter_title",
    "chapter_role",
    "core_evidence_ids",
    "recommended_tables",
    "recommended_figures",
    "primary_artifacts",
    "writing_status",
    "main_limitation_to_state",
    "next_action",
)

AGENT_PIPELINE_COLUMNS: tuple[str, ...] = (
    "stage_id",
    "stage_name",
    "agent_role",
    "allowed_inputs",
    "allowed_outputs",
    "blocked_actions",
    "required_gate_before_activation",
    "audit_requirement",
    "implementation_status",
    "thesis_value",
)

CITATION_REVIEW_PACKET_COLUMNS: tuple[str, ...] = (
    "packet_id",
    "source_id",
    "source_status",
    "source_title",
    "final_citation_readiness",
    "citation_risk",
    "evidence_id",
    "thesis_area",
    "item_type",
    "claim_or_decision",
    "primary_artifact",
    "allowed_wording",
    "blocked_wording",
    "main_limitation",
    "review_question",
    "required_check",
    "draft_use_allowed",
    "final_citation_gate",
    "reviewer_page_or_section_note",
    "reviewer_decision",
    "reviewer_notes",
)

TABLE_FIGURE_CAPTION_COLUMNS: tuple[str, ...] = (
    "package_id",
    "package_type",
    "thesis_label",
    "caption_de",
    "primary_artifact",
    "supporting_artifacts",
    "evidence_ids",
    "source_note_de",
    "interpretation_note_de",
    "limitation_note_de",
    "recommended_placement",
    "include_in_core_package",
    "thesis_readiness",
)

SOURCE_REVIEW_PLAN_COLUMNS: tuple[str, ...] = (
    "source_id",
    "source_title",
    "source_status",
    "final_citation_readiness",
    "citation_risk",
    "evidence_packet_count",
    "h1_h2_h3_packet_count",
    "method_packet_count",
    "interpretation_packet_count",
    "priority_band",
    "required_review_output",
    "thesis_use_boundary",
    "next_action",
)

AGENT_ASSISTANCE_PROTOCOL_COLUMNS: tuple[str, ...] = (
    "protocol_id",
    "pipeline_step",
    "current_artifact_boundary",
    "future_agent_help",
    "allowed_inputs",
    "allowed_outputs",
    "audit_gate",
    "blocked_behaviour",
    "activation_status",
    "thesis_value",
)

NEXT_WORK_PLAN_COLUMNS: tuple[str, ...] = (
    "workstream_id",
    "priority_order",
    "workstream",
    "thesis_section",
    "current_artifact",
    "next_action",
    "done_when",
    "blocked_until",
    "guardrail",
)

PROJECT_HIGHLEVEL_VIEW_COLUMNS: tuple[str, ...] = (
    "view_id",
    "project_layer",
    "status",
    "role_in_thesis",
    "primary_artifacts",
    "evidence_or_workstream_ids",
    "current_decision",
    "next_gate",
    "guardrail",
    "thesis_use",
)


@dataclass(frozen=True)
class ThesisConsolidationResult:
    """Generated thesis consolidation artifact paths and counts."""

    evidence_map_path: Path
    evidence_map_md_path: Path
    core_results_path: Path
    curated_package_path: Path
    citation_readiness_path: Path
    chapter_plan_path: Path
    agent_pipeline_path: Path
    citation_review_packets_path: Path
    table_figure_captions_path: Path
    source_review_plan_path: Path
    agent_assistance_protocol_path: Path
    next_work_plan_path: Path
    project_highlevel_view_path: Path
    metadata_path: Path
    docs_path: Path
    agent_docs_path: Path
    writing_blueprint_path: Path
    chapter_draft_path: Path
    citation_review_docs_path: Path
    table_figure_captions_docs_path: Path
    source_review_plan_docs_path: Path
    agent_assistance_protocol_docs_path: Path
    next_work_plan_docs_path: Path
    project_highlevel_view_docs_path: Path
    evidence_rows: int
    core_result_rows: int
    package_rows: int
    citation_rows: int
    chapter_rows: int
    agent_stage_rows: int
    citation_review_packet_rows: int
    table_figure_caption_rows: int
    source_review_plan_rows: int
    agent_assistance_protocol_rows: int
    next_work_plan_rows: int
    project_highlevel_view_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "evidence_map_path": str(self.evidence_map_path),
            "evidence_map_md_path": str(self.evidence_map_md_path),
            "core_results_path": str(self.core_results_path),
            "curated_package_path": str(self.curated_package_path),
            "citation_readiness_path": str(self.citation_readiness_path),
            "chapter_plan_path": str(self.chapter_plan_path),
            "agent_pipeline_path": str(self.agent_pipeline_path),
            "citation_review_packets_path": str(self.citation_review_packets_path),
            "table_figure_captions_path": str(self.table_figure_captions_path),
            "source_review_plan_path": str(self.source_review_plan_path),
            "agent_assistance_protocol_path": str(self.agent_assistance_protocol_path),
            "next_work_plan_path": str(self.next_work_plan_path),
            "project_highlevel_view_path": str(self.project_highlevel_view_path),
            "metadata_path": str(self.metadata_path),
            "docs_path": str(self.docs_path),
            "agent_docs_path": str(self.agent_docs_path),
            "writing_blueprint_path": str(self.writing_blueprint_path),
            "chapter_draft_path": str(self.chapter_draft_path),
            "citation_review_docs_path": str(self.citation_review_docs_path),
            "table_figure_captions_docs_path": str(self.table_figure_captions_docs_path),
            "source_review_plan_docs_path": str(self.source_review_plan_docs_path),
            "agent_assistance_protocol_docs_path": str(self.agent_assistance_protocol_docs_path),
            "next_work_plan_docs_path": str(self.next_work_plan_docs_path),
            "project_highlevel_view_docs_path": str(self.project_highlevel_view_docs_path),
            "evidence_rows": self.evidence_rows,
            "core_result_rows": self.core_result_rows,
            "package_rows": self.package_rows,
            "citation_rows": self.citation_rows,
            "chapter_rows": self.chapter_rows,
            "agent_stage_rows": self.agent_stage_rows,
            "citation_review_packet_rows": self.citation_review_packet_rows,
            "table_figure_caption_rows": self.table_figure_caption_rows,
            "source_review_plan_rows": self.source_review_plan_rows,
            "agent_assistance_protocol_rows": self.agent_assistance_protocol_rows,
            "next_work_plan_rows": self.next_work_plan_rows,
            "project_highlevel_view_rows": self.project_highlevel_view_rows,
        }


def generate_thesis_consolidation(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> ThesisConsolidationResult:
    """Generate evidence, result, package, metadata, and documentation files."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)
    literature_path = _required_file(repo_root / "data/literature/literature_index.csv")
    literature = pd.read_csv(literature_path)
    _require_columns(
        literature,
        ("source_id", "status", "hypothesis", "method", "title", "url"),
        str(literature_path),
    )

    _require_source_ids(
        literature,
        {
            "lit_emh_001",
            "lit_brier_001",
            "lit_dm_001",
            "lit_eventstudy_001",
            "lit_granger_001",
            "zotero_poly_001",
            "zotero_poly_002",
            "zotero_poly_005",
            "zotero_poly_006",
            "zotero_poly_007",
            "zotero_poly_009",
            "zotero_poly_010",
        },
    )

    _require_artifacts(
        repo_root,
        {
            "data/events_timeline_seed.csv",
            "data/results/h1_brier_scores.csv",
            "data/results/h1_diebold_mariano.json",
            "data/results/h1_forecast_quality_synthesis.csv",
            "data/results/h1_claim_evidence_audit_summary.csv",
            "data/results/h1_poll_claim_readiness_summary.csv",
            "data/results/h1_poll_comparison_result_summary.csv",
            "data/results/h1_poll_claim_readiness.png",
            "data/results/h2_event_window_summary.csv",
            "data/results/thesis_h2_event_window_car.png",
            "data/results/h3_granger_results.csv",
            "data/results/h3_lead_lag_correlations.csv",
            "data/results/thesis_h3_summary.csv",
            "data/results/thesis_h3_granger_pvalues.png",
            "data/results/monitor_anomaly_review_summary.csv",
            "data/results/monitor_anomaly_review_dashboard.html",
            "data/results/swiss_referendum_10mio_comparison.csv",
            "data/results/swiss_referendum_10mio_latest_source_comparison.csv",
            "data/results/swiss_referendum_10mio_efficiency.png",
            "docs/research/RESEARCH_SPEC.md",
            "docs/research/STRATEGY_AGENT_ARCHITECTURE.md",
        },
    )

    evidence_map = build_evidence_map()
    _validate_evidence_map(evidence_map, repo_root=repo_root, literature=literature)

    core_results = build_core_results_table(results_dir=results_dir)
    _validate_core_results(core_results, evidence_map)

    curated_package = build_curated_result_package()
    _validate_curated_package(curated_package, evidence_map, repo_root=repo_root)
    citation_readiness = build_citation_readiness(
        evidence_map=evidence_map,
        literature=literature,
    )
    _validate_citation_readiness(citation_readiness)
    chapter_plan = build_chapter_plan(curated_package=curated_package)
    _validate_chapter_plan(chapter_plan, curated_package)
    agent_pipeline = build_agent_pipeline_roadmap()
    _validate_agent_pipeline(agent_pipeline)
    citation_review_packets = build_citation_review_packets(
        evidence_map=evidence_map,
        citation_readiness=citation_readiness,
        literature=literature,
    )
    _validate_citation_review_packets(citation_review_packets, evidence_map)
    table_figure_captions = build_table_figure_captions(curated_package=curated_package)
    _validate_table_figure_captions(table_figure_captions, repo_root=repo_root)
    source_review_plan = build_source_review_plan(
        citation_readiness=citation_readiness,
        citation_review_packets=citation_review_packets,
    )
    _validate_source_review_plan(source_review_plan)
    agent_assistance_protocol = build_agent_assistance_protocol()
    _validate_agent_assistance_protocol(agent_assistance_protocol)
    next_work_plan = build_next_work_plan(
        chapter_plan=chapter_plan,
        source_review_plan=source_review_plan,
        table_figure_captions=table_figure_captions,
        agent_assistance_protocol=agent_assistance_protocol,
    )
    _validate_next_work_plan(next_work_plan)
    project_highlevel_view = build_project_highlevel_view(
        evidence_map=evidence_map,
        core_results=core_results,
        curated_package=curated_package,
        citation_readiness=citation_readiness,
        source_review_plan=source_review_plan,
        agent_pipeline=agent_pipeline,
        agent_assistance_protocol=agent_assistance_protocol,
        next_work_plan=next_work_plan,
    )
    _validate_project_highlevel_view(project_highlevel_view, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    evidence_map_path = results_dir / EVIDENCE_MAP_OUTPUT
    evidence_map_md_path = results_dir / EVIDENCE_MAP_MD_OUTPUT
    core_results_path = results_dir / CORE_RESULTS_OUTPUT
    curated_package_path = results_dir / CURATED_PACKAGE_OUTPUT
    citation_readiness_path = results_dir / CITATION_READINESS_OUTPUT
    chapter_plan_path = results_dir / CHAPTER_PLAN_OUTPUT
    agent_pipeline_path = results_dir / AGENT_PIPELINE_OUTPUT
    citation_review_packets_path = results_dir / CITATION_REVIEW_PACKETS_OUTPUT
    table_figure_captions_path = results_dir / TABLE_FIGURE_CAPTIONS_OUTPUT
    source_review_plan_path = results_dir / SOURCE_REVIEW_PLAN_OUTPUT
    agent_assistance_protocol_path = results_dir / AGENT_ASSISTANCE_PROTOCOL_OUTPUT
    next_work_plan_path = results_dir / NEXT_WORK_PLAN_OUTPUT
    project_highlevel_view_path = results_dir / PROJECT_HIGHLEVEL_VIEW_OUTPUT
    metadata_path = results_dir / METADATA_OUTPUT
    docs_path = docs_dir / DOC_OUTPUT
    agent_docs_path = docs_dir / AGENT_DOC_OUTPUT
    writing_blueprint_path = docs_dir / WRITING_BLUEPRINT_OUTPUT
    chapter_draft_path = docs_dir / CHAPTER_DRAFT_OUTPUT
    citation_review_docs_path = docs_dir / CITATION_REVIEW_DOC_OUTPUT
    table_figure_captions_docs_path = docs_dir / TABLE_FIGURE_CAPTIONS_DOC_OUTPUT
    source_review_plan_docs_path = docs_dir / SOURCE_REVIEW_PLAN_DOC_OUTPUT
    agent_assistance_protocol_docs_path = docs_dir / AGENT_ASSISTANCE_PROTOCOL_DOC_OUTPUT
    next_work_plan_docs_path = docs_dir / NEXT_WORK_PLAN_DOC_OUTPUT
    project_highlevel_view_docs_path = docs_dir / PROJECT_HIGHLEVEL_VIEW_DOC_OUTPUT

    evidence_map.to_csv(evidence_map_path, index=False)
    core_results.to_csv(core_results_path, index=False)
    curated_package.to_csv(curated_package_path, index=False)
    citation_readiness.to_csv(citation_readiness_path, index=False)
    chapter_plan.to_csv(chapter_plan_path, index=False)
    agent_pipeline.to_csv(agent_pipeline_path, index=False)
    citation_review_packets.to_csv(citation_review_packets_path, index=False)
    table_figure_captions.to_csv(table_figure_captions_path, index=False)
    source_review_plan.to_csv(source_review_plan_path, index=False)
    agent_assistance_protocol.to_csv(agent_assistance_protocol_path, index=False)
    next_work_plan.to_csv(next_work_plan_path, index=False)
    project_highlevel_view.to_csv(project_highlevel_view_path, index=False)
    evidence_map_md_path.write_text(
        _render_evidence_markdown(evidence_map),
        encoding="utf-8",
    )

    metadata = _build_metadata(
        evidence_map=evidence_map,
        core_results=core_results,
        curated_package=curated_package,
        citation_readiness=citation_readiness,
        chapter_plan=chapter_plan,
        agent_pipeline=agent_pipeline,
        citation_review_packets=citation_review_packets,
        table_figure_captions=table_figure_captions,
        source_review_plan=source_review_plan,
        agent_assistance_protocol=agent_assistance_protocol,
        next_work_plan=next_work_plan,
        project_highlevel_view=project_highlevel_view,
    )
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    docs_path.write_text(
        _render_consolidation_doc(
            evidence_map=evidence_map,
            core_results=core_results,
            curated_package=curated_package,
            citation_readiness=citation_readiness,
            chapter_plan=chapter_plan,
            agent_pipeline=agent_pipeline,
            project_highlevel_view=project_highlevel_view,
            metadata=metadata,
        ),
        encoding="utf-8",
    )
    agent_docs_path.write_text(
        _render_agent_pipeline_doc(agent_pipeline=agent_pipeline, metadata=metadata),
        encoding="utf-8",
    )
    writing_blueprint_path.write_text(
        _render_writing_blueprint(
            core_results=core_results,
            curated_package=curated_package,
            citation_readiness=citation_readiness,
            chapter_plan=chapter_plan,
        ),
        encoding="utf-8",
    )
    chapter_draft_path.write_text(
        _render_chapter_draft(
            evidence_map=evidence_map,
            core_results=core_results,
            curated_package=curated_package,
            citation_readiness=citation_readiness,
            chapter_plan=chapter_plan,
        ),
        encoding="utf-8",
    )
    citation_review_docs_path.write_text(
        _render_citation_review_packets_doc(
            citation_review_packets=citation_review_packets,
            metadata=metadata,
        ),
        encoding="utf-8",
    )
    table_figure_captions_docs_path.write_text(
        _render_table_figure_captions_doc(
            table_figure_captions=table_figure_captions,
            metadata=metadata,
        ),
        encoding="utf-8",
    )
    source_review_plan_docs_path.write_text(
        _render_source_review_plan_doc(
            source_review_plan=source_review_plan,
            metadata=metadata,
        ),
        encoding="utf-8",
    )
    agent_assistance_protocol_docs_path.write_text(
        _render_agent_assistance_protocol_doc(
            agent_assistance_protocol=agent_assistance_protocol,
            metadata=metadata,
        ),
        encoding="utf-8",
    )
    next_work_plan_docs_path.write_text(
        _render_next_work_plan_doc(
            next_work_plan=next_work_plan,
            metadata=metadata,
        ),
        encoding="utf-8",
    )
    project_highlevel_view_docs_path.write_text(
        _render_project_highlevel_view_doc(
            project_highlevel_view=project_highlevel_view,
            metadata=metadata,
        ),
        encoding="utf-8",
    )

    return ThesisConsolidationResult(
        evidence_map_path=evidence_map_path,
        evidence_map_md_path=evidence_map_md_path,
        core_results_path=core_results_path,
        curated_package_path=curated_package_path,
        citation_readiness_path=citation_readiness_path,
        chapter_plan_path=chapter_plan_path,
        agent_pipeline_path=agent_pipeline_path,
        citation_review_packets_path=citation_review_packets_path,
        table_figure_captions_path=table_figure_captions_path,
        source_review_plan_path=source_review_plan_path,
        agent_assistance_protocol_path=agent_assistance_protocol_path,
        next_work_plan_path=next_work_plan_path,
        project_highlevel_view_path=project_highlevel_view_path,
        metadata_path=metadata_path,
        docs_path=docs_path,
        agent_docs_path=agent_docs_path,
        writing_blueprint_path=writing_blueprint_path,
        chapter_draft_path=chapter_draft_path,
        citation_review_docs_path=citation_review_docs_path,
        table_figure_captions_docs_path=table_figure_captions_docs_path,
        source_review_plan_docs_path=source_review_plan_docs_path,
        agent_assistance_protocol_docs_path=agent_assistance_protocol_docs_path,
        next_work_plan_docs_path=next_work_plan_docs_path,
        project_highlevel_view_docs_path=project_highlevel_view_docs_path,
        evidence_rows=len(evidence_map),
        core_result_rows=len(core_results),
        package_rows=len(curated_package),
        citation_rows=len(citation_readiness),
        chapter_rows=len(chapter_plan),
        agent_stage_rows=len(agent_pipeline),
        citation_review_packet_rows=len(citation_review_packets),
        table_figure_caption_rows=len(table_figure_captions),
        source_review_plan_rows=len(source_review_plan),
        agent_assistance_protocol_rows=len(agent_assistance_protocol),
        next_work_plan_rows=len(next_work_plan),
        project_highlevel_view_rows=len(project_highlevel_view),
    )


def build_evidence_map() -> pd.DataFrame:
    """Return the thesis evidence map linking claims to artifacts and sources."""

    rows = [
        _evidence_row(
            evidence_id="method_h1_brier_dm",
            thesis_area="H1",
            item_type="method",
            claim_or_decision="Forecast quality is evaluated with Brier loss and Diebold-Mariano loss-series comparison.",
            primary_artifact="data/results/thesis_h1_summary.csv",
            supporting_artifacts=[
                "data/results/h1_brier_scores.csv",
                "data/results/h1_diebold_mariano.json",
                "data/results/h1_forecast_quality_synthesis.csv",
            ],
            literature_sources=[
                "lit_brier_001",
                "lit_dm_001",
                "lit_emh_001",
                "zotero_poly_002",
            ],
            allowed_wording="forecast-quality comparison; lower Brier loss in the tested overlap window",
            blocked_wording="reaction speed proof; broad market superiority proof; RCP probability claim without transformation",
            main_limitation="Repeated daily rows and one election context limit generalisation.",
            thesis_readiness="thesis_facing_ready",
        ),
        _evidence_row(
            evidence_id="interpretation_h1_bounded_advantage",
            thesis_area="H1",
            item_type="interpretation",
            claim_or_decision="A bounded Polymarket advantage is supported in selected late and compatible poll-comparison scopes.",
            primary_artifact="data/results/h1_poll_claim_readiness_summary.csv",
            supporting_artifacts=[
                "data/results/h1_poll_comparison_result_summary.csv",
                "data/results/h1_claim_evidence_audit_summary.csv",
            ],
            literature_sources=[
                "lit_brier_001",
                "lit_dm_001",
                "zotero_poly_002",
            ],
            allowed_wording="bounded H1 support in defined scope",
            blocked_wording="Polymarket is always better; many-election proof; causal explanation",
            main_limitation="The full state-date panel and other scopes remain counterexamples to the broad claim.",
            thesis_readiness="thesis_facing_ready",
        ),
        _evidence_row(
            evidence_id="interpretation_h1_broad_claim_not_proven",
            thesis_area="H1",
            item_type="interpretation",
            claim_or_decision="The broad claim that Polymarket generally beats traditional sources is not proven.",
            primary_artifact="data/results/h1_forecast_quality_synthesis.csv",
            supporting_artifacts=["data/results/h1_claim_evidence_audit_summary.csv"],
            literature_sources=["lit_brier_001", "zotero_poly_002", "lit_emh_001"],
            allowed_wording="mixed H1 evidence; broad superiority not proven",
            blocked_wording="general superiority; universal forecast dominance",
            main_limitation="The available evidence mixes daily rows, state outcomes, transformed polls, and source-specific scopes.",
            thesis_readiness="thesis_facing_ready",
        ),
        _evidence_row(
            evidence_id="method_h2_event_window",
            thesis_area="H2",
            item_type="method",
            claim_or_decision="Daily public-event response is evaluated with pre-curated events and fixed event windows.",
            primary_artifact="data/results/h2_event_window_summary.csv",
            supporting_artifacts=[
                "data/events_timeline_seed.csv",
                "data/results/h2_event_window_rows.csv",
            ],
            literature_sources=["lit_eventstudy_001", "lit_emh_001", "zotero_poly_001"],
            allowed_wording="daily event-window response around pre-curated public events",
            blocked_wording="intraday speed claim; post-hoc event selection",
            main_limitation="Daily prices cannot identify intraday reaction timing.",
            thesis_readiness="thesis_facing_ready",
        ),
        _evidence_row(
            evidence_id="interpretation_h2_daily_response",
            thesis_area="H2",
            item_type="interpretation",
            claim_or_decision="Curated events show visible daily Polymarket movement, strongest in the Trump shooting primary window.",
            primary_artifact="data/results/h2_event_window_summary.csv",
            supporting_artifacts=["data/results/thesis_h2_summary.csv"],
            literature_sources=["lit_eventstudy_001", "lit_emh_001"],
            allowed_wording="visible daily event-window movement",
            blocked_wording="instant market reaction; causal event proof",
            main_limitation="Direction and magnitude are event-window diagnostics, not intraday causal estimates.",
            thesis_readiness="thesis_facing_ready",
        ),
        _evidence_row(
            evidence_id="method_h3_wallet_tiers",
            thesis_area="H3",
            item_type="method",
            claim_or_decision="Wallet groups are defined by dataset-relative cumulative amount percentiles, not fixed whale thresholds.",
            primary_artifact="data/results/h3_wallet_distribution_inventory.json",
            supporting_artifacts=[
                "data/results/h3_wallet_tiers.csv",
                "data/results/h3_tiered_wallet_activity_daily.csv",
            ],
            literature_sources=["zotero_poly_001", "zotero_poly_005", "zotero_poly_007"],
            allowed_wording="dataset-relative wallet tiers",
            blocked_wording="arbitrary whale threshold; identified private-information wallets",
            main_limitation="Observed wallet data are BUY-only and source-filtered.",
            thesis_readiness="thesis_facing_ready",
        ),
        _evidence_row(
            evidence_id="method_h3_granger_timing",
            thesis_area="H3",
            item_type="method",
            claim_or_decision="Lead-lag correlations and Granger tests are used as predictive timing diagnostics.",
            primary_artifact="data/results/h3_granger_results.csv",
            supporting_artifacts=[
                "data/results/h3_lead_lag_correlations.csv",
                "data/results/thesis_h3_summary.csv",
            ],
            literature_sources=["lit_granger_001", "zotero_poly_005"],
            allowed_wording="predictive timing diagnostic under model assumptions",
            blocked_wording="causality proof; private information proof; profitability proof",
            main_limitation="Daily alignment, multiple testing, and BUY-only extraction limit conclusion strength.",
            thesis_readiness="thesis_facing_ready",
        ),
        _evidence_row(
            evidence_id="interpretation_h3_top_tier_signal",
            thesis_area="H3",
            item_type="interpretation",
            claim_or_decision="The top wallet tier shows the clearest deterministic timing pattern in the current H3 baseline.",
            primary_artifact="data/results/thesis_h3_summary.csv",
            supporting_artifacts=[
                "data/results/h3_granger_results.csv",
                "data/results/h3_lead_lag_correlations.csv",
            ],
            literature_sources=["lit_granger_001", "zotero_poly_005", "zotero_poly_001"],
            allowed_wording="top-tier timing pattern; predictive diagnostic",
            blocked_wording="private-information proof; causal misconduct; tradable strategy",
            main_limitation="Signal strength is diagnostic and needs sensitivity/multiple-testing caution.",
            thesis_readiness="thesis_facing_ready",
        ),
        _evidence_row(
            evidence_id="method_monitor_prototype",
            thesis_area="monitor_prototype",
            item_type="method",
            claim_or_decision="The monitor prototype combines market movement, aggregate wallet-tier activity, concentration, and event context as review cues.",
            primary_artifact="data/results/monitor_anomaly_review_summary.csv",
            supporting_artifacts=[
                "data/results/monitor_anomaly_review_queue.csv",
                "data/results/monitor_anomaly_review_dashboard.html",
                "docs/research/STRATEGY_AGENT_ARCHITECTURE.md",
            ],
            literature_sources=["zotero_poly_001", "zotero_poly_006", "zotero_poly_009"],
            allowed_wording="deterministic human-review cue; prototype monitor",
            blocked_wording="thesis evidence before review; private information proof; trading signal",
            main_limitation="Current cases remain source-check pending and blocked from thesis-facing use.",
            thesis_readiness="appendix_prototype_only",
        ),
        _evidence_row(
            evidence_id="interpretation_monitor_review_queue",
            thesis_area="monitor_prototype",
            item_type="interpretation",
            claim_or_decision="The queue is useful as a review workflow but not as evidence of causes or market inefficiency.",
            primary_artifact="data/results/monitor_anomaly_review_summary.csv",
            supporting_artifacts=[
                "data/results/monitor_anomaly_review_decision_readiness.csv",
                "data/results/monitor_anomaly_case_review_packets.csv",
            ],
            literature_sources=["zotero_poly_006", "zotero_poly_009"],
            allowed_wording="human-review workflow and appendix material",
            blocked_wording="causal claim; misconduct claim; efficiency conclusion; profit claim",
            main_limitation="All current cases remain pending manual source and thesis-use review.",
            thesis_readiness="appendix_prototype_only",
        ),
        _evidence_row(
            evidence_id="method_swiss_running_comparison",
            thesis_area="swiss_referendum",
            item_type="method",
            claim_or_decision="Swiss referendum snapshots compare Polymarket prices with curated poll shares descriptively until the vote result is known.",
            primary_artifact="data/results/swiss_referendum_10mio_comparison.csv",
            supporting_artifacts=[
                "data/results/swiss_referendum_10mio_latest_source_comparison.csv",
                "data/swiss_referendum_10mio_polls.csv",
                "docs/research/SWISS_REFERENDUM_EFFICIENCY.md",
            ],
            literature_sources=["zotero_poly_002", "lit_brier_001"],
            allowed_wording="descriptive poll-proxy comparison before final result",
            blocked_wording="mispricing proof; final efficiency conclusion; trade signal",
            main_limitation="Poll shares are not true win probabilities and the official result is still pending.",
            thesis_readiness="descriptive_pending_result",
        ),
        _evidence_row(
            evidence_id="interpretation_swiss_gap_pending",
            thesis_area="swiss_referendum",
            item_type="interpretation",
            claim_or_decision="Current Swiss divergence values are descriptive and cannot decide informational efficiency before the official result.",
            primary_artifact="data/results/swiss_referendum_10mio_latest_source_comparison.csv",
            supporting_artifacts=["data/results/swiss_referendum_10mio_efficiency.png"],
            literature_sources=["zotero_poly_002"],
            allowed_wording="running descriptive divergence against poll proxy",
            blocked_wording="final accuracy result; efficiency proof before the vote result",
            main_limitation="Final outcome and source-checked post-vote interpretation are missing.",
            thesis_readiness="descriptive_pending_result",
        ),
        _evidence_row(
            evidence_id="future_agent_pipeline_guarded",
            thesis_area="future_agents",
            item_type="future_work",
            claim_or_decision="Future agents may improve drafting, review triage, and source-check workflows only from bounded deterministic summaries.",
            primary_artifact="docs/research/STRATEGY_AGENT_ARCHITECTURE.md",
            supporting_artifacts=[
                "data/results/thesis_evidence_map.csv",
                "data/results/thesis_curated_result_package.csv",
            ],
            literature_sources=["zotero_poly_006", "zotero_poly_010"],
            allowed_wording="future audited assistant layer over bounded summaries",
            blocked_wording="agent-computed metrics; raw table prompts; autonomous trading; unlogged LLM interpretation",
            main_limitation="Implementation remains deferred until deterministic thesis package and audit logging are complete.",
            thesis_readiness="future_work_deferred",
        ),
    ]
    return pd.DataFrame(rows, columns=EVIDENCE_COLUMNS)


def build_core_results_table(*, results_dir: Path) -> pd.DataFrame:
    """Build a compact thesis-ready table of central results."""

    h1_synthesis = _read_csv(results_dir / "h1_forecast_quality_synthesis.csv")
    h1_audit = _read_summary_csv(results_dir / "h1_claim_evidence_audit_summary.csv")
    h1_claim = _read_summary_csv(results_dir / "h1_poll_claim_readiness_summary.csv")
    h2_summary = _read_csv(results_dir / "h2_event_window_summary.csv")
    h3_summary = _read_csv(results_dir / "thesis_h3_summary.csv")
    monitor = _read_csv(results_dir / "monitor_anomaly_review_summary.csv")
    swiss_comparison = _read_csv(results_dir / "swiss_referendum_10mio_comparison.csv")
    swiss_latest = _read_csv(results_dir / "swiss_referendum_10mio_latest_source_comparison.csv")

    primary_support_count = int(_summary_value(h1_claim, "primary_polymarket_support_count"))
    primary_comparison_count = int(_summary_value(h1_claim, "primary_comparison_count"))
    primary_support_share = float(_summary_value(h1_claim, "primary_polymarket_support_share"))
    aggregate_support = int(_bool_series(h1_synthesis["aggregate_mean_supports_polymarket"]).sum())
    majority_support = int(_bool_series(h1_synthesis["majority_cases_supports_polymarket"]).sum())
    broad_support = int(_bool_series(h1_synthesis["broad_many_cases_claim_supported"]).sum())
    synthesis_rows = len(h1_synthesis)
    contradiction_rows = int(_summary_value(h1_audit, "contradiction_row_count"))

    h2_primary = h2_summary[h2_summary["window_label"] == "primary_0d_to_1d"].copy()
    if h2_primary.empty:
        raise ValueError("H2 summary contains no primary_0d_to_1d rows.")
    h2_primary["abs_move"] = h2_primary["final_cumulative_abnormal_change"].abs()
    strongest_h2 = h2_primary.sort_values(["abs_move", "event_id"], ascending=[False, True]).iloc[0]

    h3_top_corr = _summary_row_by_id(h3_summary, "h3_top_abs_correlation_tier_1_top_1pct")
    h3_min_granger = _summary_row_by_id(h3_summary, "h3_min_granger_p_value_tier_1_top_1pct")
    h3_row_count = _summary_row_by_id(h3_summary, "h3_model_row_count")

    monitor_row = monitor.iloc[0]
    swiss_latest_row = swiss_latest.iloc[0]

    rows = [
        _core_result_row(
            result_id="core_h1_bounded_poll_scope",
            thesis_area="H1",
            recommended_table="T2 H1 forecast-quality and poll-comparison result",
            headline_result="Bounded poll-comparison scope supports Polymarket.",
            key_value=(
                f"{primary_support_count}/{primary_comparison_count} state-date rows "
                f"({primary_support_share:.1%}) lower Brier loss for Polymarket"
            ),
            primary_artifact="data/results/h1_poll_claim_readiness_summary.csv",
            supporting_artifacts=[
                "data/results/h1_poll_comparison_result_summary.csv",
                "data/results/h1_claim_evidence_audit_summary.csv",
            ],
            evidence_ids=["method_h1_brier_dm", "interpretation_h1_bounded_advantage"],
            bounded_interpretation="Use as bounded H1 support in the specified late low/middle poll-distance scope.",
            main_limitation="The full panel and other scopes still contain counterexamples.",
            thesis_readiness="thesis_facing_ready",
        ),
        _core_result_row(
            result_id="core_h1_broad_claim_boundary",
            thesis_area="H1",
            recommended_table="T2 H1 forecast-quality and poll-comparison result",
            headline_result="Broad Polymarket-superiority claim remains not proven.",
            key_value=(
                f"{aggregate_support}/{synthesis_rows} aggregate rows support Polymarket; "
                f"{majority_support}/{synthesis_rows} majority-case rows support Polymarket; "
                f"{broad_support}/{synthesis_rows} broad rows prove the claim; "
                f"{contradiction_rows} audit rows contradict the strong claim"
            ),
            primary_artifact="data/results/h1_forecast_quality_synthesis.csv",
            supporting_artifacts=["data/results/h1_claim_evidence_audit_summary.csv"],
            evidence_ids=["interpretation_h1_broad_claim_not_proven"],
            bounded_interpretation="State the H1 conclusion as mixed with a bounded advantage, not as general dominance.",
            main_limitation="Evidence units differ across daily rows, states, and transformed poll scopes.",
            thesis_readiness="thesis_facing_ready",
        ),
        _core_result_row(
            result_id="core_h2_largest_daily_event_window",
            thesis_area="H2",
            recommended_table="T3 H2 daily event-window result",
            headline_result="The largest primary daily event-window move is the Trump shooting window.",
            key_value=(
                f"{strongest_h2['event_id']} "
                f"{float(strongest_h2['final_cumulative_abnormal_change']) * 100:.1f} pp"
            ),
            primary_artifact="data/results/h2_event_window_summary.csv",
            supporting_artifacts=["data/results/thesis_h2_summary.csv"],
            evidence_ids=["method_h2_event_window", "interpretation_h2_daily_response"],
            bounded_interpretation="Use as daily event-window response evidence for public-event sensitivity.",
            main_limitation="Daily data do not support intraday reaction-speed claims.",
            thesis_readiness="thesis_facing_ready",
        ),
        _core_result_row(
            result_id="core_h3_top_tier_timing",
            thesis_area="H3",
            recommended_table="T4 H3 wallet-tier timing diagnostics",
            headline_result="The top wallet tier has the clearest current timing diagnostic.",
            key_value=(
                f"{h3_top_corr['label']} correlation {float(h3_top_corr['value']):.4f}; "
                f"{h3_min_granger['label']} Granger p={float(h3_min_granger['value']):.4f}; "
                f"{int(float(h3_row_count['value']))} aligned rows"
            ),
            primary_artifact="data/results/thesis_h3_summary.csv",
            supporting_artifacts=[
                "data/results/h3_granger_results.csv",
                "data/results/h3_lead_lag_correlations.csv",
            ],
            evidence_ids=[
                "method_h3_wallet_tiers",
                "method_h3_granger_timing",
                "interpretation_h3_top_tier_signal",
            ],
            bounded_interpretation="Use as predictive timing diagnostic, not causal or trading evidence.",
            main_limitation="BUY-only source data, daily alignment, and multiple-testing caution.",
            thesis_readiness="thesis_facing_ready",
        ),
        _core_result_row(
            result_id="core_monitor_review_queue_boundary",
            thesis_area="monitor_prototype",
            recommended_table="T5 Appendix prototype boundary",
            headline_result="The monitor review queue is useful as workflow evidence, not empirical proof.",
            key_value=(
                f"{int(monitor_row['queue_row_count'])} review cases; "
                f"{int(monitor_row['high_priority_count'])} high; "
                f"{int(monitor_row['medium_priority_count'])} medium; "
                f"{monitor_row['human_review_status_counts']}"
            ),
            primary_artifact="data/results/monitor_anomaly_review_summary.csv",
            supporting_artifacts=["data/results/monitor_anomaly_review_dashboard.html"],
            evidence_ids=["method_monitor_prototype", "interpretation_monitor_review_queue"],
            bounded_interpretation="Use as appendix/prototype workflow showing bounded review discipline.",
            main_limitation="Cases remain source-check pending and blocked from thesis-facing evidence.",
            thesis_readiness="appendix_prototype_only",
        ),
        _core_result_row(
            result_id="core_swiss_running_gap_pending",
            thesis_area="swiss_referendum",
            recommended_table="T5 Swiss running comparison pending final result",
            headline_result="Swiss referendum market-poll divergence is descriptive until the result is known.",
            key_value=(
                f"{len(swiss_comparison)} snapshots; latest {swiss_latest_row['source_name']} "
                f"Polymarket Yes {float(swiss_latest_row['polymarket_yes_probability']):.1%}, "
                f"poll Yes {float(swiss_latest_row['poll_yes_share']):.1%}, "
                f"raw gap {float(swiss_latest_row['raw_yes_gap']) * 100:.1f} pp"
            ),
            primary_artifact="data/results/swiss_referendum_10mio_latest_source_comparison.csv",
            supporting_artifacts=["data/results/swiss_referendum_10mio_comparison.csv"],
            evidence_ids=[
                "method_swiss_running_comparison",
                "interpretation_swiss_gap_pending",
            ],
            bounded_interpretation="Use only as running descriptive context before the official vote result.",
            main_limitation="Poll shares are not true probabilities and final outcome is pending.",
            thesis_readiness="descriptive_pending_result",
        ),
    ]
    return pd.DataFrame(rows, columns=CORE_RESULT_COLUMNS)


def build_curated_result_package() -> pd.DataFrame:
    """Return the deliberately small table/figure package for thesis drafting."""

    rows = [
        _package_row(
            package_id="T1",
            package_type="table",
            thesis_section="method_and_evidence",
            title="Method, source, and evidence map",
            primary_artifact="data/results/thesis_evidence_map.csv",
            supporting_artifacts=[
                "data/literature/literature_index.csv",
                "docs/research/RESEARCH_SPEC.md",
            ],
            evidence_ids=[
                "method_h1_brier_dm",
                "method_h2_event_window",
                "method_h3_wallet_tiers",
                "method_h3_granger_timing",
            ],
            recommended_placement="main_text",
            include_in_core_package=True,
            thesis_message="Every thesis-facing method and interpretation is linked to deterministic artifacts and sources.",
            main_limitation="Some literature rows are skimmed rather than final citation-reviewed.",
            thesis_readiness="thesis_facing_ready",
        ),
        _package_row(
            package_id="T2",
            package_type="table",
            thesis_section="H1",
            title="H1 forecast-quality and poll-comparison result",
            primary_artifact="data/results/thesis_core_results_table.csv",
            supporting_artifacts=[
                "data/results/h1_poll_claim_readiness_summary.csv",
                "data/results/h1_forecast_quality_synthesis.csv",
            ],
            evidence_ids=[
                "method_h1_brier_dm",
                "interpretation_h1_bounded_advantage",
                "interpretation_h1_broad_claim_not_proven",
            ],
            recommended_placement="main_text",
            include_in_core_package=True,
            thesis_message="H1 supports a bounded advantage, while the broad claim remains not proven.",
            main_limitation="Evidence scope differs across comparison units.",
            thesis_readiness="thesis_facing_ready",
        ),
        _package_row(
            package_id="T3",
            package_type="table",
            thesis_section="H2",
            title="H2 daily event-window result",
            primary_artifact="data/results/h2_event_window_summary.csv",
            supporting_artifacts=["data/results/thesis_h2_summary.csv"],
            evidence_ids=["method_h2_event_window", "interpretation_h2_daily_response"],
            recommended_placement="main_text",
            include_in_core_package=True,
            thesis_message="Curated public events show daily market movements at the available frequency.",
            main_limitation="No intraday speed claim.",
            thesis_readiness="thesis_facing_ready",
        ),
        _package_row(
            package_id="T4",
            package_type="table",
            thesis_section="H3",
            title="H3 wallet-tier timing diagnostics",
            primary_artifact="data/results/thesis_h3_summary.csv",
            supporting_artifacts=[
                "data/results/h3_granger_results.csv",
                "data/results/h3_lead_lag_correlations.csv",
            ],
            evidence_ids=[
                "method_h3_wallet_tiers",
                "method_h3_granger_timing",
                "interpretation_h3_top_tier_signal",
            ],
            recommended_placement="main_text",
            include_in_core_package=True,
            thesis_message="Top-tier wallet activity has a deterministic timing pattern under clear limits.",
            main_limitation="No causality, private-information, or trading claim.",
            thesis_readiness="thesis_facing_ready",
        ),
        _package_row(
            package_id="T5",
            package_type="table",
            thesis_section="appendix_or_side_track",
            title="Prototype and Swiss side-track boundary table",
            primary_artifact="data/results/thesis_core_results_table.csv",
            supporting_artifacts=[
                "data/results/monitor_anomaly_review_summary.csv",
                "data/results/swiss_referendum_10mio_latest_source_comparison.csv",
            ],
            evidence_ids=[
                "method_monitor_prototype",
                "interpretation_monitor_review_queue",
                "method_swiss_running_comparison",
                "interpretation_swiss_gap_pending",
            ],
            recommended_placement="appendix_or_discussion",
            include_in_core_package=True,
            thesis_message="Monitor and Swiss material are useful but need clear status labels.",
            main_limitation="Monitor cases need human review; Swiss needs the official result.",
            thesis_readiness="mixed_appendix_and_pending",
        ),
        _package_row(
            package_id="F1",
            package_type="figure",
            thesis_section="H1",
            title="H1 poll-claim readiness",
            primary_artifact="data/results/h1_poll_claim_readiness.png",
            supporting_artifacts=["data/results/h1_poll_claim_readiness_summary.csv"],
            evidence_ids=[
                "interpretation_h1_bounded_advantage",
                "interpretation_h1_broad_claim_not_proven",
            ],
            recommended_placement="main_text",
            include_in_core_package=True,
            thesis_message="Shows supported bounded H1 scope and counterexample scopes in one visual.",
            main_limitation="Does not turn poll shares into native forecast probabilities beyond documented transforms.",
            thesis_readiness="thesis_facing_ready",
        ),
        _package_row(
            package_id="F2",
            package_type="figure",
            thesis_section="H2",
            title="H2 daily event-window movements",
            primary_artifact="data/results/thesis_h2_event_window_car.png",
            supporting_artifacts=["data/results/h2_event_window_summary.csv"],
            evidence_ids=["method_h2_event_window", "interpretation_h2_daily_response"],
            recommended_placement="main_text",
            include_in_core_package=True,
            thesis_message="Shows event-window movement magnitudes for the curated events.",
            main_limitation="Daily resolution only.",
            thesis_readiness="thesis_facing_ready",
        ),
        _package_row(
            package_id="F3",
            package_type="figure",
            thesis_section="H3",
            title="H3 Granger diagnostic p-values",
            primary_artifact="data/results/thesis_h3_granger_pvalues.png",
            supporting_artifacts=["data/results/h3_granger_results.csv"],
            evidence_ids=["method_h3_granger_timing", "interpretation_h3_top_tier_signal"],
            recommended_placement="main_text",
            include_in_core_package=True,
            thesis_message="Shows the wallet-tier timing diagnostic without causal wording.",
            main_limitation="Multiple-testing and BUY-only limitations stay visible in text.",
            thesis_readiness="thesis_facing_ready",
        ),
        _package_row(
            package_id="F4",
            package_type="figure",
            thesis_section="swiss_referendum",
            title="Swiss referendum running poll-proxy comparison",
            primary_artifact="data/results/swiss_referendum_10mio_efficiency.png",
            supporting_artifacts=[
                "data/results/swiss_referendum_10mio_latest_source_comparison.csv",
                "data/results/swiss_referendum_10mio_comparison.csv",
            ],
            evidence_ids=[
                "method_swiss_running_comparison",
                "interpretation_swiss_gap_pending",
            ],
            recommended_placement="discussion_pending_final_result",
            include_in_core_package=True,
            thesis_message="Shows the running divergence as descriptive context before the vote result.",
            main_limitation="No final efficiency claim before official result.",
            thesis_readiness="descriptive_pending_result",
        ),
        _package_row(
            package_id="A1",
            package_type="appendix_artifact",
            thesis_section="future_agents",
            title="Deferred agent pipeline design",
            primary_artifact="docs/research/THESIS_CONSOLIDATION.md",
            supporting_artifacts=["docs/research/STRATEGY_AGENT_ARCHITECTURE.md"],
            evidence_ids=["future_agent_pipeline_guarded"],
            recommended_placement="appendix_or_future_work",
            include_in_core_package=False,
            thesis_message="Agents may later improve review and drafting, but only over bounded audited summaries.",
            main_limitation="No runtime agents or MCP implementation belongs in the current thesis core.",
            thesis_readiness="future_work_deferred",
        ),
    ]
    return pd.DataFrame(rows, columns=PACKAGE_COLUMNS)


def build_citation_readiness(
    *,
    evidence_map: pd.DataFrame,
    literature: pd.DataFrame,
) -> pd.DataFrame:
    """Build source-by-source citation readiness from the evidence map."""

    rows: list[dict[str, object]] = []
    for source in literature.sort_values("source_id").to_dict(orient="records"):
        source_id = str(source["source_id"])
        usage = evidence_map[
            evidence_map["literature_sources"].astype(str).map(
                lambda value: source_id in _split_list(value)
            )
        ]
        status = str(source["status"])
        if usage.empty:
            draft_role = "not_used_in_current_core_map"
            readiness = "not_currently_needed"
            required_action = "No immediate thesis action unless the source is added to a claim."
            citation_risk = "low"
        elif status in {"reviewed", "cited"}:
            draft_role = "supports_current_mapped_claims"
            readiness = "final_citation_ready" if status == "cited" else "reviewed_not_final_citation"
            required_action = "Check citation formatting and page-specific notes before final submission."
            citation_risk = "low"
        elif status == "skimmed":
            draft_role = "supports_draft_mapping_only"
            readiness = "needs_full_source_review_before_final_citation"
            required_action = (
                "Read the source against the mapped evidence rows, extract page or section notes, "
                "and then mark reviewed or cited only after claim wording is checked."
            )
            citation_risk = "medium"
        elif status == "candidate":
            draft_role = "question_or_future_work_only"
            readiness = "not_allowed_for_thesis_facing_claims"
            required_action = (
                "Verify metadata and relevance before using beyond future-work or question framing."
            )
            citation_risk = "high"
        elif status == "rejected":
            draft_role = "blocked"
            readiness = "do_not_cite"
            required_action = "Do not cite unless the source is replaced or re-reviewed under a new source_id."
            citation_risk = "blocked"
        else:
            draft_role = "unknown_status"
            readiness = "needs_status_review"
            required_action = "Assign a recognised literature status before thesis use."
            citation_risk = "high"

        rows.append(
            {
                "source_id": source_id,
                "title": str(source["title"]),
                "status": status,
                "used_by_evidence_ids": "; ".join(usage["evidence_id"].tolist()),
                "used_by_thesis_areas": "; ".join(sorted(set(usage["thesis_area"].tolist()))),
                "used_by_item_types": "; ".join(sorted(set(usage["item_type"].tolist()))),
                "draft_mapping_role": draft_role,
                "final_citation_readiness": readiness,
                "required_next_action": required_action,
                "citation_risk": citation_risk,
            }
        )
    return pd.DataFrame(rows, columns=CITATION_READINESS_COLUMNS)


def build_chapter_plan(*, curated_package: pd.DataFrame) -> pd.DataFrame:
    """Build a thesis chapter plan tied to the curated package."""

    package_by_id = curated_package.set_index("package_id")

    rows = [
        _chapter_row(
            chapter_id="ch_01_intro",
            chapter_title="Einleitung und Forschungsfrage",
            chapter_role="Motivate decentralized prediction markets, Polymarket, and the efficiency question.",
            core_evidence_ids=[
                "method_h1_brier_dm",
                "method_h2_event_window",
                "method_h3_wallet_tiers",
            ],
            recommended_tables=["T1"],
            recommended_figures=[],
            primary_artifacts=[
                str(package_by_id.loc["T1", "primary_artifact"]),
                "docs/research/RESEARCH_SPEC.md",
            ],
            writing_status="outline_ready",
            main_limitation_to_state="Informational efficiency is operationalised through proxy tests, not observed directly.",
            next_action="Write concise problem statement and delimit Polymarket/US-election focus.",
        ),
        _chapter_row(
            chapter_id="ch_02_theory_literature",
            chapter_title="Theorie und Literatur",
            chapter_role="Explain EMH, prediction-market forecast quality, event studies, and wallet/on-chain caution.",
            core_evidence_ids=[
                "method_h1_brier_dm",
                "method_h2_event_window",
                "method_h3_granger_timing",
            ],
            recommended_tables=["T1"],
            recommended_figures=[],
            primary_artifacts=[
                "data/results/thesis_citation_readiness.csv",
                "data/literature/literature_index.csv",
            ],
            writing_status="source_review_needed",
            main_limitation_to_state="Draft mapping is ready, but final citation wording still needs source-by-source review.",
            next_action="Promote key method and Polymarket sources from skimmed to reviewed or cited after full-paper checks.",
        ),
        _chapter_row(
            chapter_id="ch_03_data_method",
            chapter_title="Daten und Methodik",
            chapter_role="Document deterministic Python pipeline, artifact hierarchy, and method choices.",
            core_evidence_ids=[
                "method_h1_brier_dm",
                "method_h2_event_window",
                "method_h3_wallet_tiers",
                "method_h3_granger_timing",
            ],
            recommended_tables=["T1"],
            recommended_figures=[],
            primary_artifacts=[
                "data/results/thesis_evidence_map.csv",
                "data/results/thesis_curated_result_package.csv",
            ],
            writing_status="draft_ready",
            main_limitation_to_state="RCP remains excluded from probability metrics until transformation is documented.",
            next_action="Turn evidence-map rows into short method paragraphs with artifact citations.",
        ),
        _chapter_row(
            chapter_id="ch_04_h1_results",
            chapter_title="H1: Prognosequalitaet",
            chapter_role="Present bounded Brier and poll-comparison evidence.",
            core_evidence_ids=[
                "interpretation_h1_bounded_advantage",
                "interpretation_h1_broad_claim_not_proven",
            ],
            recommended_tables=["T2"],
            recommended_figures=["F1"],
            primary_artifacts=[
                str(package_by_id.loc["T2", "primary_artifact"]),
                str(package_by_id.loc["F1", "primary_artifact"]),
            ],
            writing_status="result_ready_with_limits",
            main_limitation_to_state="The broad Polymarket-superiority claim remains not proven.",
            next_action="Write H1 result as bounded support plus explicit counterexample paragraph.",
        ),
        _chapter_row(
            chapter_id="ch_05_h2_results",
            chapter_title="H2: Ereignisfenster",
            chapter_role="Present daily public-event response diagnostics.",
            core_evidence_ids=["interpretation_h2_daily_response"],
            recommended_tables=["T3"],
            recommended_figures=["F2"],
            primary_artifacts=[
                str(package_by_id.loc["T3", "primary_artifact"]),
                str(package_by_id.loc["F2", "primary_artifact"]),
            ],
            writing_status="result_ready_with_limits",
            main_limitation_to_state="Daily event-window results do not identify intraday reaction speed.",
            next_action="Write event-by-event result table narrative and daily-resolution limitation.",
        ),
        _chapter_row(
            chapter_id="ch_06_h3_results",
            chapter_title="H3: Wallet-Timing",
            chapter_role="Present distribution-derived tiers and predictive timing diagnostics.",
            core_evidence_ids=[
                "method_h3_wallet_tiers",
                "interpretation_h3_top_tier_signal",
            ],
            recommended_tables=["T4"],
            recommended_figures=["F3"],
            primary_artifacts=[
                str(package_by_id.loc["T4", "primary_artifact"]),
                str(package_by_id.loc["F3", "primary_artifact"]),
            ],
            writing_status="result_ready_with_limits",
            main_limitation_to_state="BUY-only source data, daily alignment, and multiple testing limit claim strength.",
            next_action="Write H3 as timing diagnostics, not causality or private-information evidence.",
        ),
        _chapter_row(
            chapter_id="ch_07_extensions",
            chapter_title="Erweiterungen: Monitor und Schweizer Abstimmung",
            chapter_role="Place monitor prototype and Swiss side track outside the core proof.",
            core_evidence_ids=[
                "interpretation_monitor_review_queue",
                "interpretation_swiss_gap_pending",
            ],
            recommended_tables=["T5"],
            recommended_figures=["F4"],
            primary_artifacts=[
                str(package_by_id.loc["T5", "primary_artifact"]),
                str(package_by_id.loc["F4", "primary_artifact"]),
            ],
            writing_status="appendix_or_discussion_ready",
            main_limitation_to_state="Monitor cases need human review; Swiss interpretation needs official result.",
            next_action="Keep both as bounded discussion or appendix until final gates change.",
        ),
        _chapter_row(
            chapter_id="ch_08_discussion_conclusion",
            chapter_title="Diskussion, Limitationen und Fazit",
            chapter_role="Integrate H1-H3 evidence and state what remains unproven.",
            core_evidence_ids=[
                "interpretation_h1_broad_claim_not_proven",
                "interpretation_h2_daily_response",
                "interpretation_h3_top_tier_signal",
                "future_agent_pipeline_guarded",
            ],
            recommended_tables=[],
            recommended_figures=[],
            primary_artifacts=[
                "data/results/thesis_core_results_table.csv",
                "docs/research/THESIS_AGENT_PIPELINE_ROADMAP.md",
            ],
            writing_status="outline_ready",
            main_limitation_to_state="The thesis supports bounded diagnostics, not universal market efficiency or strategy claims.",
            next_action="Write final answer around bounded evidence, limitations, and future agent-assisted workflow.",
        ),
    ]
    return pd.DataFrame(rows, columns=CHAPTER_PLAN_COLUMNS)


def build_agent_pipeline_roadmap() -> pd.DataFrame:
    """Build a documentation-only roadmap for later guarded agent support."""

    rows = [
        _agent_stage_row(
            stage_id="agent_stage_00_disabled_runtime",
            stage_name="Keep runtime disabled",
            agent_role="No runtime thesis agent is active.",
            allowed_inputs="None",
            allowed_outputs="Static architecture notes only",
            blocked_actions="agent execution; MCP implementation; model routing; metric calculation",
            required_gate_before_activation="Deterministic thesis package committed and reviewed.",
            audit_requirement="No LLM call before llm_audit_log integration exists.",
            implementation_status="current_required_state",
            thesis_value="Protects the deterministic thesis core.",
        ),
        _agent_stage_row(
            stage_id="agent_stage_01_evidence_reader",
            stage_name="Evidence reader",
            agent_role="Summarise existing evidence-map rows for drafting.",
            allowed_inputs="thesis_evidence_map.csv; thesis_core_results_table.csv; thesis_curated_result_package.csv",
            allowed_outputs="short prose notes tied to evidence_id values",
            blocked_actions="reading raw tables; computing metrics; changing evidence rows",
            required_gate_before_activation="Bounded prompt template and llm_audit_log write path reviewed.",
            audit_requirement="Log prompt hash, model, evidence ids, artifact versions, and output path.",
            implementation_status="future_documentation_only",
            thesis_value="Speeds drafting without weakening traceability.",
        ),
        _agent_stage_row(
            stage_id="agent_stage_02_citation_checker",
            stage_name="Citation readiness checker",
            agent_role="Flag sources that need review before final citation wording.",
            allowed_inputs="thesis_citation_readiness.csv; literature_index.csv",
            allowed_outputs="review checklist; missing-source warnings",
            blocked_actions="promoting source status automatically; inventing citations; citing candidate sources as evidence",
            required_gate_before_activation="Human-readable source-status rules and no-write default reviewed.",
            audit_requirement="Log source ids read and checklist output.",
            implementation_status="future_documentation_only",
            thesis_value="Keeps literature mapping honest before final writing.",
        ),
        _agent_stage_row(
            stage_id="agent_stage_03_wording_guard",
            stage_name="Interpretation wording guard",
            agent_role="Compare draft paragraphs with allowed and blocked wording.",
            allowed_inputs="draft paragraph; thesis_evidence_map.csv; thesis_chapter_plan.csv",
            allowed_outputs="bounded wording warnings and suggested safer phrasing",
            blocked_actions="adding new claims; relaxing blocked wording; replacing deterministic artifacts",
            required_gate_before_activation="Draft text input must be manually selected and logged.",
            audit_requirement="Log draft hash, evidence ids checked, and warnings.",
            implementation_status="future_documentation_only",
            thesis_value="Reduces overclaiming in H1-H3 discussion.",
        ),
        _agent_stage_row(
            stage_id="agent_stage_04_monitor_review_helper",
            stage_name="Monitor review helper",
            agent_role="Summarise source-check notes for monitor review packets after human review exists.",
            allowed_inputs="bounded monitor review packets; human status worksheets; source URLs",
            allowed_outputs="review-note summary; unresolved evidence checklist",
            blocked_actions="accessing wallet addresses by default; declaring misconduct; creating trading signals",
            required_gate_before_activation="Human review worksheet contains reviewed statuses and source URLs.",
            audit_requirement="Log case ids, artifact versions, and blocked-claim checks.",
            implementation_status="future_documentation_only",
            thesis_value="Could help appendix review without changing empirical results.",
        ),
        _agent_stage_row(
            stage_id="agent_stage_05_bounded_mcp_summaries",
            stage_name="Bounded MCP summary tools",
            agent_role="Expose reviewed summary artifacts to future assistants.",
            allowed_inputs="reviewed summary CSV/JSON files only; max 50 rows unless justified",
            allowed_outputs="bounded read-only summaries",
            blocked_actions="raw SQL; raw monitor rows; wallet-address exposure by default; order or trading paths",
            required_gate_before_activation="Separate approved goal, tests, access contract, and llm_audit_log integration.",
            audit_requirement="Log tool name, row count, artifact path, and user-visible output.",
            implementation_status="future_deferred",
            thesis_value="Creates a safe interface after the thesis core is stable.",
        ),
    ]
    return pd.DataFrame(rows, columns=AGENT_PIPELINE_COLUMNS)


def build_agent_assistance_protocol() -> pd.DataFrame:
    """Build documentation-only protocol rows for later agent-assisted workflow."""

    rows = [
        _agent_protocol_row(
            protocol_id="agent_protocol_01_source_review",
            pipeline_step="Manual source review",
            current_artifact_boundary="thesis_source_review_plan.csv; thesis_citation_review_packets.csv; literature_index.csv",
            future_agent_help="Prepare a checklist of page or section evidence still missing for each source.",
            allowed_inputs="source_id; evidence_id; required_check; source metadata; reviewer notes selected by a human",
            allowed_outputs="bounded checklist; missing-page-note warnings; no status changes",
            audit_gate="llm_audit_log entry with source_ids, evidence_ids, prompt hash, model, and output path",
            blocked_behaviour="promoting source status; inventing page numbers; citing candidate sources as thesis evidence",
            activation_status="future_documentation_only",
            thesis_value="Accelerates literature review while keeping final citation approval human-owned.",
        ),
        _agent_protocol_row(
            protocol_id="agent_protocol_02_evidence_reader",
            pipeline_step="Evidence-to-prose drafting",
            current_artifact_boundary="thesis_evidence_map.csv; thesis_core_results_table.csv; thesis_curated_result_package.csv",
            future_agent_help="Summarise allowed wording and limitations for a selected Evidence ID.",
            allowed_inputs="one selected evidence_id plus bounded linked artifact summaries",
            allowed_outputs="short draft note tied to the same evidence_id and primary_artifact",
            audit_gate="llm_audit_log entry with evidence_id, artifact versions, prompt hash, model, and output path",
            blocked_behaviour="calculating metrics; reading raw table dumps; adding claims outside allowed wording",
            activation_status="future_documentation_only",
            thesis_value="Turns deterministic evidence into draftable notes without weakening traceability.",
        ),
        _agent_protocol_row(
            protocol_id="agent_protocol_03_wording_guard",
            pipeline_step="Claim and wording review",
            current_artifact_boundary="draft paragraph; thesis_evidence_map.csv; thesis_chapter_plan.csv",
            future_agent_help="Compare draft wording against allowed and blocked wording.",
            allowed_inputs="human-selected paragraph; linked evidence rows; chapter id",
            allowed_outputs="bounded overclaim warnings and safer wording suggestions",
            audit_gate="llm_audit_log entry with draft hash, evidence_ids checked, prompt hash, model, and warnings path",
            blocked_behaviour="relaxing blocked wording; making causal, private-information, profitability, or tradeability claims",
            activation_status="future_documentation_only",
            thesis_value="Reduces overclaiming in H1, H2, H3, Monitor, Swiss, and agent-outlook text.",
        ),
        _agent_protocol_row(
            protocol_id="agent_protocol_04_table_figure_checker",
            pipeline_step="Table and figure package review",
            current_artifact_boundary="thesis_table_figure_captions.csv; thesis_curated_result_package.csv",
            future_agent_help="Check whether each draft table or figure caption names a source artifact, interpretation, and limitation.",
            allowed_inputs="caption registry rows; selected draft caption text",
            allowed_outputs="missing-artifact, missing-limitation, or extra-raw-artifact warnings",
            audit_gate="llm_audit_log entry with package_ids, draft hash, prompt hash, model, and warnings path",
            blocked_behaviour="adding new tables or figures beyond the curated package without updating deterministic maps",
            activation_status="future_documentation_only",
            thesis_value="Keeps the thesis result presentation compact and source-linked.",
        ),
        _agent_protocol_row(
            protocol_id="agent_protocol_05_advisor_update",
            pipeline_step="Advisor update summarisation",
            current_artifact_boundary="dozentenbericht_ba_thesis.md; THESIS_CONSOLIDATION.md; STATUS.md",
            future_agent_help="Summarise the current project state for a meeting agenda.",
            allowed_inputs="existing advisor report; consolidation docs; project status snapshot",
            allowed_outputs="meeting bullets, open questions, and next-step checklist",
            audit_gate="llm_audit_log entry with artifact paths, prompt hash, model, and summary path",
            blocked_behaviour="changing empirical claims; hiding unresolved source-review or Swiss-result gates",
            activation_status="future_documentation_only",
            thesis_value="Makes supervisor communication faster without changing evidence.",
        ),
        _agent_protocol_row(
            protocol_id="agent_protocol_06_monitor_review_helper",
            pipeline_step="Monitor appendix review",
            current_artifact_boundary="bounded monitor review packets; human review notes; no wallet addresses by default",
            future_agent_help="Summarise reviewed monitor cases after human source checks exist.",
            allowed_inputs="bounded case_id summaries; reviewed source notes; aggregate tier labels",
            allowed_outputs="appendix review summary and unresolved-evidence checklist",
            audit_gate="llm_audit_log entry with case_ids, artifact versions, prompt hash, model, and output path",
            blocked_behaviour="declaring misconduct; exposing wallet addresses by default; creating trading signals",
            activation_status="future_documentation_only",
            thesis_value="Keeps monitor material useful as appendix workflow, not core proof.",
        ),
        _agent_protocol_row(
            protocol_id="agent_protocol_07_bounded_mcp",
            pipeline_step="Bounded MCP summary interface",
            current_artifact_boundary="reviewed summary CSV/JSON only; max 50 rows unless justified",
            future_agent_help="Expose reviewed summaries to assistants through read-only tools.",
            allowed_inputs="reviewed summary artifacts; explicit row limits; no raw SQL by default",
            allowed_outputs="bounded read-only summaries with row counts and artifact paths",
            audit_gate="separate approved goal, access contract tests, and llm_audit_log integration",
            blocked_behaviour="raw table access; SELECT star; wallet-address exposure; order or trading paths",
            activation_status="future_deferred",
            thesis_value="Provides a later safe interface after the deterministic core and review gates are stable.",
        ),
    ]
    return pd.DataFrame(rows, columns=AGENT_ASSISTANCE_PROTOCOL_COLUMNS)


def build_next_work_plan(
    *,
    chapter_plan: pd.DataFrame,
    source_review_plan: pd.DataFrame,
    table_figure_captions: pd.DataFrame,
    agent_assistance_protocol: pd.DataFrame,
) -> pd.DataFrame:
    """Build the next thesis workstreams from generated planning artifacts."""

    priority_source_count = int(
        (
            source_review_plan["priority_band"]
            == "priority_1_method_foundation_review"
        ).sum()
    )
    core_tables = int(
        (
            table_figure_captions["include_in_core_package"].astype(bool)
            & (table_figure_captions["package_type"] == "table")
        ).sum()
    )
    core_figures = int(
        (
            table_figure_captions["include_in_core_package"].astype(bool)
            & (table_figure_captions["package_type"] == "figure")
        ).sum()
    )
    return pd.DataFrame(
        [
            _next_work_row(
                workstream_id="work_01_source_review",
                priority_order=1,
                workstream="Core source review",
                thesis_section="theory_literature_and_methods",
                current_artifact="data/results/thesis_source_review_plan.csv",
                next_action=f"Review the {priority_source_count} priority-1 method-foundation sources and record page or section notes.",
                done_when="All priority-1 rows have reviewer page or section notes and status decisions are updated by a human.",
                blocked_until="Full source review is completed for method and core interpretation sources.",
                guardrail="Do not promote skimmed or candidate sources automatically.",
            ),
            _next_work_row(
                workstream_id="work_02_method_chapters",
                priority_order=2,
                workstream="Write introduction, theory, and methods",
                thesis_section="chapters_01_to_03",
                current_artifact="data/results/thesis_chapter_plan.csv",
                next_action=f"Use the {len(chapter_plan)} chapter-plan rows to draft the front matter and methods chapters.",
                done_when="Each method paragraph names a deterministic artifact and a reviewed or pending-reviewed source boundary.",
                blocked_until="Core method source review is at least page-note complete.",
                guardrail="RCP transformation, H2 event curation, H3 tier construction, and agent deferral must stay explicit.",
            ),
            _next_work_row(
                workstream_id="work_03_h1_results",
                priority_order=3,
                workstream="Write H1 result chapter",
                thesis_section="h1_results",
                current_artifact="data/results/thesis_core_results_table.csv; data/results/h1_poll_claim_readiness_summary.csv",
                next_action="Write H1 as bounded Polymarket support plus explicit broad-claim boundary.",
                done_when="The chapter states supported scope, counterexample scopes, and why the broad claim remains not proven.",
                blocked_until="No blocker for draft; final citation wording waits for source review.",
                guardrail="Do not state universal Polymarket superiority or RCP probability claims.",
            ),
            _next_work_row(
                workstream_id="work_04_h2_h3_results",
                priority_order=4,
                workstream="Write H2 and H3 result chapters",
                thesis_section="h2_h3_results",
                current_artifact="data/results/h2_event_window_summary.csv; data/results/thesis_h3_summary.csv",
                next_action="Draft H2 as daily event-window response and H3 as wallet-tier timing diagnostics.",
                done_when="Both chapters include the main deterministic result, artifact path, and limitation paragraph.",
                blocked_until="No blocker for draft; sensitivity and final wording can be refined after source review.",
                guardrail="No intraday speed claim, no Granger causality claim, no private-information or profitability claim.",
            ),
            _next_work_row(
                workstream_id="work_05_table_figure_integration",
                priority_order=5,
                workstream="Integrate compact tables and figures",
                thesis_section="results_and_appendix",
                current_artifact="data/results/thesis_table_figure_captions.csv",
                next_action=f"Use {core_tables} core tables and {core_figures} core figures with the generated captions and limitation notes.",
                done_when="Every inserted table or figure has label, source artifact, interpretation note, and limitation note.",
                blocked_until="No blocker for draft; final numbering waits for thesis layout.",
                guardrail="Do not add raw result files to the core package without updating evidence map and chapter plan.",
            ),
            _next_work_row(
                workstream_id="work_06_monitor_appendix",
                priority_order=6,
                workstream="Keep monitor as appendix prototype",
                thesis_section="appendix_or_discussion",
                current_artifact="data/results/monitor_anomaly_review_summary.csv",
                next_action="Mention monitor only as read-only prototype and review workflow.",
                done_when="Monitor text says review cases are cues, not causal, trading, or thesis-facing efficiency proof.",
                blocked_until="Human source review of monitor cases exists.",
                guardrail="No wallet-address exposure by default and no order or trading paths.",
            ),
            _next_work_row(
                workstream_id="work_07_swiss_result_gate",
                priority_order=7,
                workstream="Finalize Swiss side track after result",
                thesis_section="discussion_pending_final_result",
                current_artifact="data/results/swiss_referendum_10mio_latest_source_comparison.csv",
                next_action="Keep the Swiss comparison descriptive until the official vote result is available and mapped.",
                done_when="Official result is recorded, deterministic Swiss artifacts are regenerated, and wording remains bounded.",
                blocked_until="Official 14 June 2026 vote result is available.",
                guardrail="Poll shares are not win probabilities and cannot support a final efficiency claim before result mapping.",
            ),
            _next_work_row(
                workstream_id="work_08_agent_outlook",
                priority_order=8,
                workstream="Keep agent pipeline as future work",
                thesis_section="future_work",
                current_artifact="data/results/thesis_agent_assistance_protocol.csv",
                next_action=f"Use the {len(agent_assistance_protocol)} protocol rows only as a future-work design section.",
                done_when="The thesis names useful future roles but states activation gates and blocked actions.",
                blocked_until="Separate approved goal, llm_audit_log integration, bounded prompts, and tests exist.",
                guardrail="Do not implement runtime agents, MCP tools, model routing, or LLM metric calculation now.",
            ),
            _next_work_row(
                workstream_id="work_09_advisor_iteration",
                priority_order=9,
                workstream="Use advisor feedback to narrow scope",
                thesis_section="project_management",
                current_artifact="docs/project/dozentenbericht_ba_thesis.docx",
                next_action="Ask the advisor to approve the bounded H1 wording, source-review depth, Swiss placement, and appendix scope.",
                done_when="Advisor feedback is logged and translated into a small next commit plan.",
                blocked_until="Advisor feedback is received.",
                guardrail="Do not expand empirical scope before current thesis core is written.",
            ),
            _next_work_row(
                workstream_id="work_10_final_qa",
                priority_order=10,
                workstream="Final thesis QA",
                thesis_section="whole_thesis",
                current_artifact="STATUS.md; docs/project/WORK_LOG.md",
                next_action="Run full tests, review checks, citation checks, table/figure checks, and Swiss spelling scan before export.",
                done_when="Review checks pass, final citations are approved, and the thesis export has no unsupported claims.",
                blocked_until="Draft chapters, source review, and final result gates are complete.",
                guardrail="No final submission claim may exceed deterministic artifacts and reviewed sources.",
            ),
        ],
        columns=NEXT_WORK_PLAN_COLUMNS,
    )


def build_project_highlevel_view(
    *,
    evidence_map: pd.DataFrame,
    core_results: pd.DataFrame,
    curated_package: pd.DataFrame,
    citation_readiness: pd.DataFrame,
    source_review_plan: pd.DataFrame,
    agent_pipeline: pd.DataFrame,
    agent_assistance_protocol: pd.DataFrame,
    next_work_plan: pd.DataFrame,
) -> pd.DataFrame:
    """Build a compact high-level project view from consolidation artifacts."""

    core_package = curated_package[curated_package["include_in_core_package"].astype(bool)]
    core_table_count = int((core_package["package_type"] == "table").sum())
    core_figure_count = int((core_package["package_type"] == "figure").sum())
    priority_source_count = int(
        (
            source_review_plan["priority_band"]
            == "priority_1_method_foundation_review"
        ).sum()
    )
    full_source_review_count = int(
        (
            citation_readiness["final_citation_readiness"]
            == "needs_full_source_review_before_final_citation"
        ).sum()
    )
    first_workstream = str(next_work_plan.sort_values("priority_order").iloc[0]["workstream_id"])
    final_workstream = str(next_work_plan.sort_values("priority_order").iloc[-1]["workstream_id"])
    agent_documentation_rows = int(
        (agent_assistance_protocol["activation_status"] == "future_documentation_only").sum()
    )
    agent_stage_rows = int(len(agent_pipeline))

    return pd.DataFrame(
        [
            _project_view_row(
                view_id="project_00_current_frame",
                project_layer="Current high-level frame",
                status="active_thesis_core",
                role_in_thesis="Frames the BA thesis around deterministic H1, H2, and H3 evidence, with monitor and Swiss material kept bounded.",
                primary_artifacts=[
                    "data/results/thesis_evidence_map.csv",
                    "data/results/thesis_core_results_table.csv",
                    "data/results/thesis_curated_result_package.csv",
                ],
                evidence_or_workstream_ids=[
                    "method_h1_brier_dm",
                    "method_h2_event_window",
                    "method_h3_wallet_tiers",
                    first_workstream,
                    final_workstream,
                ],
                current_decision=f"Without review access, use {len(core_results)} core result rows, {core_table_count} core tables, and {core_figure_count} core figures as the main thesis package.",
                next_gate="Complete source review and turn the chapter plan into thesis prose.",
                guardrail="Deterministic Python artifacts first; no LLM metric calculation, no raw table dumps, and no runtime agents.",
                thesis_use="main_text_project_overview",
            ),
            _project_view_row(
                view_id="project_01_h1_forecast_quality",
                project_layer="H1 forecast quality",
                status="thesis_facing_ready",
                role_in_thesis="Core empirical result on forecast quality and bounded Polymarket support.",
                primary_artifacts=[
                    "data/results/thesis_core_results_table.csv",
                    "data/results/h1_poll_claim_readiness_summary.csv",
                    "data/results/h1_poll_claim_readiness.png",
                ],
                evidence_or_workstream_ids=[
                    "interpretation_h1_bounded_advantage",
                    "interpretation_h1_broad_claim_boundary",
                    "work_03_h1_results",
                ],
                current_decision="Write H1 as bounded support in compatible poll-comparison scopes, not as universal Polymarket superiority.",
                next_gate="Final citation wording after source review confirms method and interpretation support.",
                guardrail="No RCP probability claim and no broad superiority claim beyond deterministic artifacts.",
                thesis_use="main_text_results",
            ),
            _project_view_row(
                view_id="project_02_h2_event_windows",
                project_layer="H2 event-window response",
                status="thesis_facing_ready",
                role_in_thesis="Core empirical result on visible daily Polymarket moves around curated public events.",
                primary_artifacts=[
                    "data/results/h2_event_window_summary.csv",
                    "data/results/thesis_h2_event_window_car.png",
                    "data/events_timeline_seed.csv",
                ],
                evidence_or_workstream_ids=[
                    "method_h2_event_window",
                    "interpretation_h2_daily_response",
                    "work_04_h2_h3_results",
                ],
                current_decision="Use H2 as daily event-window evidence, not as an intraday reaction-speed claim.",
                next_gate="Draft result text with event curation and daily-resolution limitation explicit.",
                guardrail="No intraday speed claim and no event selection after seeing the response.",
                thesis_use="main_text_results",
            ),
            _project_view_row(
                view_id="project_03_h3_wallet_timing",
                project_layer="H3 wallet timing diagnostics",
                status="thesis_facing_ready_with_limits",
                role_in_thesis="Core empirical result on dataset-relative wallet-tier timing diagnostics.",
                primary_artifacts=[
                    "data/results/thesis_h3_summary.csv",
                    "data/results/h3_granger_results.csv",
                    "data/results/thesis_h3_granger_pvalues.png",
                ],
                evidence_or_workstream_ids=[
                    "method_h3_wallet_tiers",
                    "interpretation_h3_predictive_diagnostic",
                    "work_04_h2_h3_results",
                ],
                current_decision="Use top-tier timing diagnostics as predictive pattern evidence, not causal or misconduct evidence.",
                next_gate="Draft H3 with BUY-only, daily aggregation, and multiple-testing limitations visible.",
                guardrail="No Granger causality claim, no private-information claim, and no profitability claim.",
                thesis_use="main_text_results_with_limits",
            ),
            _project_view_row(
                view_id="project_04_source_review_gate",
                project_layer="Sources and citations",
                status="active_gate",
                role_in_thesis="Controls which literature can support final method and interpretation wording.",
                primary_artifacts=[
                    "data/results/thesis_source_review_plan.csv",
                    "data/results/thesis_citation_review_packets.csv",
                    "data/literature/literature_index.csv",
                ],
                evidence_or_workstream_ids=["work_01_source_review"],
                current_decision=f"Treat {full_source_review_count} sources as requiring full review, including {priority_source_count} priority-1 method-foundation rows. Use access, structure, and traceability audits only to prepare manual review and BA drafting.",
                next_gate="Record page or section notes, structure checks, and human decisions before final thesis citation.",
                guardrail="Source review is manual; do not promote skimmed or candidate sources automatically and do not infer support claims from file structure.",
                thesis_use="theory_methods_citation_gate",
            ),
            _project_view_row(
                view_id="project_05_table_figure_package",
                project_layer="Compact tables and figures",
                status="thesis_facing_package",
                role_in_thesis="Keeps the thesis readable by selecting a small number of strong tables and figures.",
                primary_artifacts=[
                    "data/results/thesis_table_figure_captions.csv",
                    "data/results/thesis_curated_result_package.csv",
                ],
                evidence_or_workstream_ids=["work_05_table_figure_integration"],
                current_decision=f"Use {core_table_count} core tables and {core_figure_count} core figures, with generated captions and limitation notes.",
                next_gate="Integrate the selected package into draft chapters and appendix placement.",
                guardrail="Do not add raw result artifacts to the core package without updating evidence map and chapter plan.",
                thesis_use="main_text_and_appendix",
            ),
            _project_view_row(
                view_id="project_06_monitor_review_access",
                project_layer="Monitor prototype and review access",
                status="paused_appendix_only",
                role_in_thesis="Shows a read-only prototype and review workflow only if kept in appendix or discussion.",
                primary_artifacts=[
                    "data/results/monitor_anomaly_review_summary.csv",
                    "data/results/monitor_anomaly_review_access_contract.json",
                    "data/results/monitor_anomaly_review_dashboard.html",
                ],
                evidence_or_workstream_ids=["work_06_monitor_appendix"],
                current_decision="Review access remains paused; continue with advisor feedback, source review, and draft writing instead of access work.",
                next_gate="Human source review of monitor cases and a separate approved goal before any renewed access work.",
                guardrail="No wallet-address exposure by default, no raw monitor rows, no order or trading paths, and no causal claims.",
                thesis_use="appendix_or_discussion_only",
            ),
            _project_view_row(
                view_id="project_07_swiss_referendum",
                project_layer="Swiss referendum side track",
                status="descriptive_pending_result",
                role_in_thesis="Provides a bounded side comparison until the official vote outcome can be mapped.",
                primary_artifacts=[
                    "data/results/swiss_referendum_10mio_latest_source_comparison.csv",
                    "data/results/swiss_referendum_10mio_efficiency.png",
                ],
                evidence_or_workstream_ids=[
                    "interpretation_swiss_descriptive_pending_result",
                    "work_07_swiss_result_gate",
                ],
                current_decision="Keep the Swiss material descriptive until the official 14 June 2026 vote result is available.",
                next_gate="Regenerate Swiss artifacts after official result mapping.",
                guardrail="Poll shares are not win probabilities and cannot support final efficiency claims before result mapping.",
                thesis_use="discussion_pending_final_result",
            ),
            _project_view_row(
                view_id="project_08_future_agents",
                project_layer="Future agent-assisted pipeline",
                status="documentation_only_deferred",
                role_in_thesis="Outlook on how bounded assistants could support source review and wording checks later.",
                primary_artifacts=[
                    "data/results/thesis_agent_pipeline_roadmap.csv",
                    "data/results/thesis_agent_assistance_protocol.csv",
                ],
                evidence_or_workstream_ids=[
                    "future_agent_pipeline_guarded",
                    "work_08_agent_outlook",
                ],
                current_decision=f"Keep {agent_stage_rows} roadmap stages and {agent_documentation_rows} documentation-only assistance rows inactive.",
                next_gate="Separate approved goal with bounded prompts, tests, and llm_audit_log integration.",
                guardrail="No runtime agents, no MCP tools, no model routing, no raw table access, and no LLM metric calculation now.",
                thesis_use="future_work_only",
            ),
            _project_view_row(
                view_id="project_09_advisor_iteration",
                project_layer="Advisor communication",
                status="project_management_ready",
                role_in_thesis="Gives the advisor a concise written project view and decision points.",
                primary_artifacts=[
                    "docs/project/dozentenbericht_ba_thesis.docx",
                    "docs/project/dozentenbericht_ba_thesis.md",
                    "docs/project/THESIS_ADVISOR_HANDOFF_PACKAGE.md",
                    "docs/project/DOZENTEN_FEEDBACK_LOG.md",
                ],
                evidence_or_workstream_ids=["work_09_advisor_iteration"],
                current_decision="Use the Dozentenbericht to align on bounded H1 wording, source-review depth, Swiss placement, and appendix scope.",
                next_gate="Advisor feedback is received, logged in DOZENTEN_FEEDBACK_LOG, and translated into the next small commit plan.",
                guardrail="Do not expand empirical scope or reactivate review access before the current deterministic thesis core is written.",
                thesis_use="advisor_update",
            ),
        ],
        columns=PROJECT_HIGHLEVEL_VIEW_COLUMNS,
    )


def build_citation_review_packets(
    *,
    evidence_map: pd.DataFrame,
    citation_readiness: pd.DataFrame,
    literature: pd.DataFrame,
) -> pd.DataFrame:
    """Build source-evidence packets for final citation review."""

    literature_by_id = literature.set_index("source_id").to_dict(orient="index")
    readiness_by_id = citation_readiness.set_index("source_id").to_dict(orient="index")
    rows: list[dict[str, object]] = []
    for evidence_row in evidence_map.sort_values(["thesis_area", "evidence_id"]).to_dict(orient="records"):
        evidence_id = str(evidence_row["evidence_id"])
        for source_id in _split_list(str(evidence_row["literature_sources"])):
            source = literature_by_id[source_id]
            readiness = readiness_by_id[source_id]
            source_status = str(source["status"])
            thesis_readiness = str(evidence_row["thesis_readiness"])
            if source_status in {"reviewed", "cited"}:
                draft_use_allowed = True
                final_gate = "citation_format_and_page_note_check"
                required_check = "Confirm page or section note and final citation formatting."
            elif source_status == "skimmed":
                draft_use_allowed = True
                final_gate = "full_source_review_required_before_final_citation"
                required_check = (
                    "Read the source against this evidence row, record page or section support, "
                    "and confirm the source supports the allowed wording without blocked claims."
                )
            elif source_status == "candidate" and thesis_readiness == "future_work_deferred":
                draft_use_allowed = False
                final_gate = "metadata_and_relevance_review_before_future_work_use"
                required_check = (
                    "Verify metadata, source quality, and relevance before using this source beyond "
                    "future-work question framing."
                )
            elif source_status == "candidate":
                draft_use_allowed = False
                final_gate = "not_allowed_for_thesis_facing_claims"
                required_check = "Do not use for thesis-facing claims unless re-reviewed under a new status."
            else:
                draft_use_allowed = False
                final_gate = "do_not_cite"
                required_check = "Do not cite this source for the mapped evidence row."

            rows.append(
                {
                    "packet_id": f"{source_id}__{evidence_id}",
                    "source_id": source_id,
                    "source_status": source_status,
                    "source_title": str(source["title"]),
                    "final_citation_readiness": str(readiness["final_citation_readiness"]),
                    "citation_risk": str(readiness["citation_risk"]),
                    "evidence_id": evidence_id,
                    "thesis_area": str(evidence_row["thesis_area"]),
                    "item_type": str(evidence_row["item_type"]),
                    "claim_or_decision": str(evidence_row["claim_or_decision"]),
                    "primary_artifact": str(evidence_row["primary_artifact"]),
                    "allowed_wording": str(evidence_row["allowed_wording"]),
                    "blocked_wording": str(evidence_row["blocked_wording"]),
                    "main_limitation": str(evidence_row["main_limitation"]),
                    "review_question": _citation_review_question(evidence_row),
                    "required_check": required_check,
                    "draft_use_allowed": draft_use_allowed,
                    "final_citation_gate": final_gate,
                    "reviewer_page_or_section_note": "",
                    "reviewer_decision": "pending",
                    "reviewer_notes": "",
                }
            )
    return pd.DataFrame(rows, columns=CITATION_REVIEW_PACKET_COLUMNS)


def build_source_review_plan(
    *,
    citation_readiness: pd.DataFrame,
    citation_review_packets: pd.DataFrame,
) -> pd.DataFrame:
    """Build a source-level manual review plan from citation packets."""

    packet_groups = {
        source_id: rows
        for source_id, rows in citation_review_packets.groupby("source_id", sort=False)
    }
    rows: list[dict[str, object]] = []
    for source in citation_readiness.sort_values("source_id").to_dict(orient="records"):
        source_id = str(source["source_id"])
        packets = packet_groups.get(
            source_id,
            pd.DataFrame(columns=CITATION_REVIEW_PACKET_COLUMNS),
        )
        evidence_packet_count = int(len(packets))
        h1_h2_h3_packet_count = int(
            packets["thesis_area"].astype(str).isin({"H1", "H2", "H3"}).sum()
        )
        method_packet_count = int((packets["item_type"].astype(str) == "method").sum())
        interpretation_packet_count = int(
            (packets["item_type"].astype(str) == "interpretation").sum()
        )
        readiness = str(source["final_citation_readiness"])
        source_status = str(source["status"])
        priority_band = _source_review_priority_band(
            source_status=source_status,
            readiness=readiness,
            method_packet_count=method_packet_count,
            h1_h2_h3_packet_count=h1_h2_h3_packet_count,
            evidence_packet_count=evidence_packet_count,
        )
        rows.append(
            {
                "source_id": source_id,
                "source_title": str(source["title"]),
                "source_status": source_status,
                "final_citation_readiness": readiness,
                "citation_risk": str(source["citation_risk"]),
                "evidence_packet_count": evidence_packet_count,
                "h1_h2_h3_packet_count": h1_h2_h3_packet_count,
                "method_packet_count": method_packet_count,
                "interpretation_packet_count": interpretation_packet_count,
                "priority_band": priority_band,
                "required_review_output": _source_review_required_output(priority_band),
                "thesis_use_boundary": _source_review_use_boundary(readiness),
                "next_action": _source_review_next_action(priority_band, readiness),
            }
        )
    return pd.DataFrame(rows, columns=SOURCE_REVIEW_PLAN_COLUMNS)


def build_table_figure_captions(*, curated_package: pd.DataFrame) -> pd.DataFrame:
    """Build thesis-ready captions and source notes for curated package rows."""

    caption_overrides = {
        "T1": (
            "Methoden-, Quellen- und Evidenzkarte der Thesis",
            "Diese Tabelle verknuepft zentrale Methoden und Interpretationen mit Evidence-IDs, Artefakten und Quellenstatus.",
            "Die Tabelle zeigt die Nachvollziehbarkeit der Argumentation, nicht neue empirische Ergebnisse.",
            "Einige Quellen sind noch nicht final zitierbereit und muessen gemaess Citation-Review-Paketen geprueft werden.",
        ),
        "T2": (
            "H1: Prognosequalitaet und Poll-Vergleich",
            "Diese Tabelle fasst den begrenzten H1-Support und die Grenze der breiten Ueberlegenheitsbehauptung zusammen.",
            "Polymarket wird nur fuer klar definierte Vergleichsscopes als unterstuetzt beschrieben.",
            "Vergleichseinheiten und Poll-Transformationen bleiben heterogen.",
        ),
        "T3": (
            "H2: Tagesbasierte Ereignisfenster um kuratierte oeffentliche Ereignisse",
            "Diese Tabelle berichtet die deterministischen H2-Ereignisfensterwerte aus den vorab kuratierten Events.",
            "Die Werte zeigen Tagesbewegungen um Ereignisse, keine Intraday-Reaktionsgeschwindigkeit.",
            "Eventauswahl und Tagesfrequenz begrenzen die Interpretation.",
        ),
        "T4": (
            "H3: Wallet-Tiers und Timingdiagnostik",
            "Diese Tabelle fasst dataset-relative Wallet-Tiers, Korrelationen und Granger-Diagnostik zusammen.",
            "Die Tabelle unterstuetzt eine vorsichtige Timingdiagnostik fuer das oberste Tier.",
            "BUY-only-Quelle, taegliche Aggregation und Mehrfachtests begrenzen die Aussage.",
        ),
        "T5": (
            "Statusgrenzen fuer Monitor-Prototyp und Schweizer Abstimmungstrack",
            "Diese Tabelle trennt Appendix-/Prototypmaterial und pending Swiss-Ergebnisse vom H1-H3-Kern.",
            "Monitor und Swiss sind nuetzliche Erweiterungen, aber noch keine finalen Kernergebnisse.",
            "Monitor-Faelle brauchen Human Review; Swiss braucht das offizielle Resultat.",
        ),
        "F1": (
            "H1: Claim-Readiness des Poll-Vergleichs",
            "Die Abbildung zeigt den unterstuetzten begrenzten H1-Scope und Gegenbeispiele zur breiten Behauptung.",
            "Die Abbildung hilft, die H1-Aussage begrenzt statt pauschal zu formulieren.",
            "Die Darstellung ersetzt keine finale Quellenpruefung und keine Erweiterung auf mehrere Wahlen.",
        ),
        "F2": (
            "H2: Tagesbewegungen in kuratierten Ereignisfenstern",
            "Die Abbildung visualisiert die H2-Bewegungen aus `h2_event_window_summary.csv`.",
            "Sie zeigt, welche Ereignisfenster im Tagesraster die groessten Bewegungen aufweisen.",
            "Die Abbildung darf nicht als Intraday-Reaktionsnachweis gelesen werden.",
        ),
        "F3": (
            "H3: Granger-Diagnostik nach Wallet-Tier und Lag",
            "Die Abbildung visualisiert p-Werte der H3-Granger-Diagnostik fuer erfolgreiche Tests.",
            "Sie macht sichtbar, wo die Timingdiagnostik am staerksten ausfaellt.",
            "Granger-Diagnostik ist kein Kausalitaets-, private-information- oder Profitabilitaetsnachweis.",
        ),
        "F4": (
            "Schweizer 10-Millionen-Initiative: laufender Poll-Proxy-Vergleich",
            "Die Abbildung zeigt den laufenden Vergleich von Polymarket-Snapshots mit kuratierten Poll-Proxies.",
            "Sie dient als beschreibender Side-Track bis zum offiziellen Abstimmungsresultat.",
            "Poll-Anteile sind keine echten Gewinnwahrscheinlichkeiten und erlauben vor dem Resultat keine finale Effizienzaussage.",
        ),
    }
    label_prefix = {"table": "tab", "figure": "fig", "appendix_artifact": "app"}
    rows: list[dict[str, object]] = []
    for row in curated_package.sort_values("package_id").to_dict(orient="records"):
        package_id = str(row["package_id"])
        caption, source_note, interpretation_note, limitation_note = caption_overrides.get(
            package_id,
            (
                str(row["title"]),
                f"Quelle: `{row['primary_artifact']}`.",
                str(row["thesis_message"]),
                str(row["main_limitation"]),
            ),
        )
        package_type = str(row["package_type"])
        label = f"{label_prefix.get(package_type, 'art')}:{package_id.lower()}"
        rows.append(
            {
                "package_id": package_id,
                "package_type": package_type,
                "thesis_label": label,
                "caption_de": caption,
                "primary_artifact": str(row["primary_artifact"]),
                "supporting_artifacts": str(row["supporting_artifacts"]),
                "evidence_ids": str(row["evidence_ids"]),
                "source_note_de": source_note,
                "interpretation_note_de": interpretation_note,
                "limitation_note_de": limitation_note,
                "recommended_placement": str(row["recommended_placement"]),
                "include_in_core_package": bool(row["include_in_core_package"]),
                "thesis_readiness": str(row["thesis_readiness"]),
            }
        )
    return pd.DataFrame(rows, columns=TABLE_FIGURE_CAPTION_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_thesis_consolidation(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _evidence_row(
    *,
    evidence_id: str,
    thesis_area: str,
    item_type: str,
    claim_or_decision: str,
    primary_artifact: str,
    supporting_artifacts: list[str],
    literature_sources: list[str],
    allowed_wording: str,
    blocked_wording: str,
    main_limitation: str,
    thesis_readiness: str,
) -> dict[str, object]:
    return {
        "evidence_id": evidence_id,
        "thesis_area": thesis_area,
        "item_type": item_type,
        "claim_or_decision": claim_or_decision,
        "primary_artifact": primary_artifact,
        "supporting_artifacts": "; ".join(supporting_artifacts),
        "literature_sources": "; ".join(literature_sources),
        "allowed_wording": allowed_wording,
        "blocked_wording": blocked_wording,
        "main_limitation": main_limitation,
        "thesis_readiness": thesis_readiness,
    }


def _core_result_row(
    *,
    result_id: str,
    thesis_area: str,
    recommended_table: str,
    headline_result: str,
    key_value: str,
    primary_artifact: str,
    supporting_artifacts: list[str],
    evidence_ids: list[str],
    bounded_interpretation: str,
    main_limitation: str,
    thesis_readiness: str,
) -> dict[str, object]:
    return {
        "result_id": result_id,
        "thesis_area": thesis_area,
        "recommended_table": recommended_table,
        "headline_result": headline_result,
        "key_value": key_value,
        "primary_artifact": primary_artifact,
        "supporting_artifacts": "; ".join(supporting_artifacts),
        "evidence_ids": "; ".join(evidence_ids),
        "bounded_interpretation": bounded_interpretation,
        "main_limitation": main_limitation,
        "thesis_readiness": thesis_readiness,
    }


def _package_row(
    *,
    package_id: str,
    package_type: str,
    thesis_section: str,
    title: str,
    primary_artifact: str,
    supporting_artifacts: list[str],
    evidence_ids: list[str],
    recommended_placement: str,
    include_in_core_package: bool,
    thesis_message: str,
    main_limitation: str,
    thesis_readiness: str,
) -> dict[str, object]:
    return {
        "package_id": package_id,
        "package_type": package_type,
        "thesis_section": thesis_section,
        "title": title,
        "primary_artifact": primary_artifact,
        "supporting_artifacts": "; ".join(supporting_artifacts),
        "evidence_ids": "; ".join(evidence_ids),
        "recommended_placement": recommended_placement,
        "include_in_core_package": include_in_core_package,
        "thesis_message": thesis_message,
        "main_limitation": main_limitation,
        "thesis_readiness": thesis_readiness,
    }


def _chapter_row(
    *,
    chapter_id: str,
    chapter_title: str,
    chapter_role: str,
    core_evidence_ids: list[str],
    recommended_tables: list[str],
    recommended_figures: list[str],
    primary_artifacts: list[str],
    writing_status: str,
    main_limitation_to_state: str,
    next_action: str,
) -> dict[str, object]:
    return {
        "chapter_id": chapter_id,
        "chapter_title": chapter_title,
        "chapter_role": chapter_role,
        "core_evidence_ids": "; ".join(core_evidence_ids),
        "recommended_tables": "; ".join(recommended_tables),
        "recommended_figures": "; ".join(recommended_figures),
        "primary_artifacts": "; ".join(primary_artifacts),
        "writing_status": writing_status,
        "main_limitation_to_state": main_limitation_to_state,
        "next_action": next_action,
    }


def _agent_stage_row(
    *,
    stage_id: str,
    stage_name: str,
    agent_role: str,
    allowed_inputs: str,
    allowed_outputs: str,
    blocked_actions: str,
    required_gate_before_activation: str,
    audit_requirement: str,
    implementation_status: str,
    thesis_value: str,
) -> dict[str, object]:
    return {
        "stage_id": stage_id,
        "stage_name": stage_name,
        "agent_role": agent_role,
        "allowed_inputs": allowed_inputs,
        "allowed_outputs": allowed_outputs,
        "blocked_actions": blocked_actions,
        "required_gate_before_activation": required_gate_before_activation,
        "audit_requirement": audit_requirement,
        "implementation_status": implementation_status,
        "thesis_value": thesis_value,
    }


def _agent_protocol_row(
    *,
    protocol_id: str,
    pipeline_step: str,
    current_artifact_boundary: str,
    future_agent_help: str,
    allowed_inputs: str,
    allowed_outputs: str,
    audit_gate: str,
    blocked_behaviour: str,
    activation_status: str,
    thesis_value: str,
) -> dict[str, object]:
    return {
        "protocol_id": protocol_id,
        "pipeline_step": pipeline_step,
        "current_artifact_boundary": current_artifact_boundary,
        "future_agent_help": future_agent_help,
        "allowed_inputs": allowed_inputs,
        "allowed_outputs": allowed_outputs,
        "audit_gate": audit_gate,
        "blocked_behaviour": blocked_behaviour,
        "activation_status": activation_status,
        "thesis_value": thesis_value,
    }


def _next_work_row(
    *,
    workstream_id: str,
    priority_order: int,
    workstream: str,
    thesis_section: str,
    current_artifact: str,
    next_action: str,
    done_when: str,
    blocked_until: str,
    guardrail: str,
) -> dict[str, object]:
    return {
        "workstream_id": workstream_id,
        "priority_order": priority_order,
        "workstream": workstream,
        "thesis_section": thesis_section,
        "current_artifact": current_artifact,
        "next_action": next_action,
        "done_when": done_when,
        "blocked_until": blocked_until,
        "guardrail": guardrail,
    }


def _project_view_row(
    *,
    view_id: str,
    project_layer: str,
    status: str,
    role_in_thesis: str,
    primary_artifacts: list[str],
    evidence_or_workstream_ids: list[str],
    current_decision: str,
    next_gate: str,
    guardrail: str,
    thesis_use: str,
) -> dict[str, object]:
    return {
        "view_id": view_id,
        "project_layer": project_layer,
        "status": status,
        "role_in_thesis": role_in_thesis,
        "primary_artifacts": "; ".join(primary_artifacts),
        "evidence_or_workstream_ids": "; ".join(evidence_or_workstream_ids),
        "current_decision": current_decision,
        "next_gate": next_gate,
        "guardrail": guardrail,
        "thesis_use": thesis_use,
    }


def _read_csv(path: Path) -> pd.DataFrame:
    _required_file(path)
    return pd.read_csv(path)


def _read_summary_csv(path: Path) -> pd.DataFrame:
    frame = _read_csv(path)
    _require_columns(frame, ("summary_id", "value"), str(path))
    return frame


def _summary_value(frame: pd.DataFrame, summary_id: str) -> Any:
    match = frame[frame["summary_id"] == summary_id]
    if match.empty:
        raise KeyError(f"Missing summary_id {summary_id!r}")
    return match.iloc[0]["value"]


def _summary_row_by_id(frame: pd.DataFrame, summary_id: str) -> pd.Series:
    _require_columns(frame, ("summary_id", "label", "value"), "summary frame")
    match = frame[frame["summary_id"] == summary_id]
    if match.empty:
        raise KeyError(f"Missing summary_id {summary_id!r}")
    return match.iloc[0]


def _validate_evidence_map(
    frame: pd.DataFrame,
    *,
    repo_root: Path,
    literature: pd.DataFrame,
) -> None:
    _require_columns(frame, EVIDENCE_COLUMNS, "evidence map")
    if frame["evidence_id"].duplicated().any():
        raise ValueError("Evidence map contains duplicate evidence_id values.")
    source_status = literature.set_index("source_id")["status"].to_dict()
    for row in frame.to_dict(orient="records"):
        _validate_artifact_list(repo_root, [str(row["primary_artifact"])])
        _validate_artifact_list(repo_root, _split_list(str(row["supporting_artifacts"])))
        literature_sources = _split_list(str(row["literature_sources"]))
        if not literature_sources:
            raise ValueError(f"{row['evidence_id']} has no literature_sources.")
        missing_sources = [sid for sid in literature_sources if sid not in source_status]
        if missing_sources:
            raise ValueError(f"{row['evidence_id']} has unknown literature sources: {missing_sources}")
        if row["thesis_readiness"] == "thesis_facing_ready":
            rejected = [sid for sid in literature_sources if source_status[sid] == "rejected"]
            candidate_only = [sid for sid in literature_sources if source_status[sid] == "candidate"]
            if rejected or candidate_only:
                raise ValueError(
                    f"{row['evidence_id']} thesis-facing row uses non-ready sources: "
                    f"rejected={rejected}, candidate={candidate_only}"
                )
        if not str(row["main_limitation"]).strip():
            raise ValueError(f"{row['evidence_id']} is missing a main limitation.")
        if not str(row["allowed_wording"]).strip() or not str(row["blocked_wording"]).strip():
            raise ValueError(f"{row['evidence_id']} is missing wording guardrails.")


def _validate_core_results(core_results: pd.DataFrame, evidence_map: pd.DataFrame) -> None:
    _require_columns(core_results, CORE_RESULT_COLUMNS, "core results table")
    if core_results["result_id"].duplicated().any():
        raise ValueError("Core results table contains duplicate result_id values.")
    known_evidence = set(evidence_map["evidence_id"])
    for row in core_results.to_dict(orient="records"):
        missing = [eid for eid in _split_list(str(row["evidence_ids"])) if eid not in known_evidence]
        if missing:
            raise ValueError(f"{row['result_id']} references unknown evidence ids: {missing}")
        if not str(row["bounded_interpretation"]).strip():
            raise ValueError(f"{row['result_id']} is missing bounded interpretation.")
        if not str(row["main_limitation"]).strip():
            raise ValueError(f"{row['result_id']} is missing limitation.")


def _validate_curated_package(
    package: pd.DataFrame,
    evidence_map: pd.DataFrame,
    *,
    repo_root: Path,
) -> None:
    _require_columns(package, PACKAGE_COLUMNS, "curated result package")
    if package["package_id"].duplicated().any():
        raise ValueError("Curated package contains duplicate package_id values.")
    known_evidence = set(evidence_map["evidence_id"])
    for row in package.to_dict(orient="records"):
        _validate_artifact_list(repo_root, [str(row["primary_artifact"])])
        _validate_artifact_list(repo_root, _split_list(str(row["supporting_artifacts"])))
        missing = [eid for eid in _split_list(str(row["evidence_ids"])) if eid not in known_evidence]
        if missing:
            raise ValueError(f"{row['package_id']} references unknown evidence ids: {missing}")
    core = package[package["include_in_core_package"].astype(bool)]
    core_tables = core[core["package_type"] == "table"]
    core_figures = core[core["package_type"] == "figure"]
    if len(core_tables) > 5:
        raise ValueError("Core package has more than five tables.")
    if len(core_figures) > 4:
        raise ValueError("Core package has more than four figures.")


def _validate_citation_readiness(frame: pd.DataFrame) -> None:
    _require_columns(frame, CITATION_READINESS_COLUMNS, "citation readiness")
    if frame["source_id"].duplicated().any():
        raise ValueError("Citation readiness contains duplicate source_id values.")
    thesis_used = frame[frame["used_by_evidence_ids"].astype(str).str.len() > 0]
    invalid_ready = thesis_used[
        thesis_used["final_citation_readiness"].isin(
            {"final_citation_ready", "reviewed_not_final_citation"}
        )
        & thesis_used["status"].isin({"candidate", "rejected"})
    ]
    if not invalid_ready.empty:
        raise ValueError("Candidate or rejected sources cannot be citation-ready.")
    risky_used = thesis_used[thesis_used["status"].isin({"candidate", "rejected"})]
    invalid_risky = risky_used[
        ~risky_used["final_citation_readiness"].isin(
            {"not_allowed_for_thesis_facing_claims", "do_not_cite"}
        )
    ]
    if not invalid_risky.empty:
        raise ValueError("Candidate or rejected sources must be blocked from thesis-facing citation.")
    if thesis_used["required_next_action"].astype(str).str.len().eq(0).any():
        raise ValueError("Used citation-readiness rows require next actions.")


def _validate_chapter_plan(chapter_plan: pd.DataFrame, curated_package: pd.DataFrame) -> None:
    _require_columns(chapter_plan, CHAPTER_PLAN_COLUMNS, "chapter plan")
    if chapter_plan["chapter_id"].duplicated().any():
        raise ValueError("Chapter plan contains duplicate chapter_id values.")
    known_package_ids = set(curated_package["package_id"])
    for row in chapter_plan.to_dict(orient="records"):
        refs = _split_list(str(row["recommended_tables"])) + _split_list(
            str(row["recommended_figures"])
        )
        missing = [ref for ref in refs if ref not in known_package_ids]
        if missing:
            raise ValueError(f"{row['chapter_id']} references unknown package ids: {missing}")
        if not str(row["main_limitation_to_state"]).strip():
            raise ValueError(f"{row['chapter_id']} is missing a limitation.")
        if not str(row["next_action"]).strip():
            raise ValueError(f"{row['chapter_id']} is missing next action.")


def _validate_agent_pipeline(agent_pipeline: pd.DataFrame) -> None:
    _require_columns(agent_pipeline, AGENT_PIPELINE_COLUMNS, "agent pipeline roadmap")
    if agent_pipeline["stage_id"].duplicated().any():
        raise ValueError("Agent pipeline roadmap contains duplicate stage_id values.")
    joined = "\n".join(agent_pipeline.astype(str).agg(" ".join, axis=1).tolist()).lower()
    required_terms = (
        "llm_audit_log",
        "metric calculation",
        "raw table",
        "wallet-address",
        "order or trading paths",
        "future_documentation_only",
    )
    missing_terms = [term for term in required_terms if term not in joined]
    if missing_terms:
        raise ValueError("Agent pipeline roadmap missing guardrail terms: " + ", ".join(missing_terms))
    active_like = agent_pipeline[
        ~agent_pipeline["implementation_status"].isin(
            {"current_required_state", "future_documentation_only", "future_deferred"}
        )
    ]
    if not active_like.empty:
        raise ValueError("Agent pipeline contains an active implementation status.")


def _validate_agent_assistance_protocol(protocol: pd.DataFrame) -> None:
    _require_columns(protocol, AGENT_ASSISTANCE_PROTOCOL_COLUMNS, "agent assistance protocol")
    if protocol["protocol_id"].duplicated().any():
        raise ValueError("Agent assistance protocol contains duplicate protocol_id values.")
    allowed_statuses = {"future_documentation_only", "future_deferred"}
    if not set(protocol["activation_status"]).issubset(allowed_statuses):
        raise ValueError("Agent assistance protocol contains active activation status.")
    joined = "\n".join(protocol.astype(str).agg(" ".join, axis=1).tolist()).lower()
    required_terms = (
        "llm_audit_log",
        "raw table",
        "wallet",
        "order or trading paths",
        "calculating metrics",
        "no status changes",
    )
    missing_terms = [term for term in required_terms if term not in joined]
    if missing_terms:
        raise ValueError("Agent assistance protocol missing guardrail terms: " + ", ".join(missing_terms))
    blocked = protocol["blocked_behaviour"].astype(str).str.len().eq(0)
    if blocked.any():
        raise ValueError("Agent assistance protocol requires blocked_behaviour for every row.")


def _validate_next_work_plan(plan: pd.DataFrame) -> None:
    _require_columns(plan, NEXT_WORK_PLAN_COLUMNS, "next work plan")
    if plan["workstream_id"].duplicated().any():
        raise ValueError("Next work plan contains duplicate workstream_id values.")
    if plan["priority_order"].duplicated().any():
        raise ValueError("Next work plan contains duplicate priority_order values.")
    expected_order = list(range(1, len(plan) + 1))
    actual_order = sorted(int(value) for value in plan["priority_order"].tolist())
    if actual_order != expected_order:
        raise ValueError("Next work plan priority_order must be contiguous from 1.")
    for column in ("next_action", "done_when", "blocked_until", "guardrail"):
        if plan[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Next work plan contains empty {column}.")
    joined = "\n".join(plan.astype(str).agg(" ".join, axis=1).tolist()).lower()
    required_terms = (
        "source review",
        "bounded",
        "llm_audit_log",
        "no order or trading paths",
        "official 14 june 2026 vote result",
        "deterministic artifacts",
    )
    missing_terms = [term for term in required_terms if term not in joined]
    if missing_terms:
        raise ValueError("Next work plan missing guardrail terms: " + ", ".join(missing_terms))


def _validate_project_highlevel_view(frame: pd.DataFrame, *, repo_root: Path) -> None:
    _require_columns(frame, PROJECT_HIGHLEVEL_VIEW_COLUMNS, "project highlevel view")
    if frame["view_id"].duplicated().any():
        raise ValueError("Project highlevel view contains duplicate view_id values.")
    allowed_statuses = {
        "active_thesis_core",
        "thesis_facing_ready",
        "thesis_facing_ready_with_limits",
        "active_gate",
        "thesis_facing_package",
        "paused_appendix_only",
        "descriptive_pending_result",
        "documentation_only_deferred",
        "project_management_ready",
    }
    unknown_statuses = sorted(set(frame["status"]).difference(allowed_statuses))
    if unknown_statuses:
        raise ValueError(f"Project highlevel view contains unknown statuses: {unknown_statuses}")
    for column in (
        "project_layer",
        "role_in_thesis",
        "primary_artifacts",
        "current_decision",
        "next_gate",
        "guardrail",
        "thesis_use",
    ):
        if frame[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Project highlevel view contains empty {column}.")
    for row in frame.to_dict(orient="records"):
        _validate_artifact_list(repo_root, _split_list(str(row["primary_artifacts"])))
    ids = set(frame["view_id"])
    required_ids = {
        "project_00_current_frame",
        "project_01_h1_forecast_quality",
        "project_02_h2_event_windows",
        "project_03_h3_wallet_timing",
        "project_06_monitor_review_access",
        "project_07_swiss_referendum",
        "project_08_future_agents",
    }
    missing_ids = sorted(required_ids.difference(ids))
    if missing_ids:
        raise ValueError(f"Project highlevel view missing required rows: {missing_ids}")
    joined = "\n".join(frame.astype(str).agg(" ".join, axis=1).tolist()).lower()
    required_terms = (
        "review access remains paused",
        "source review is manual",
        "llm_audit_log",
        "official 14 june 2026 vote result",
        "no order or trading paths",
        "deterministic python artifacts",
    )
    missing_terms = [term for term in required_terms if term not in joined]
    if missing_terms:
        raise ValueError("Project highlevel view missing guardrail terms: " + ", ".join(missing_terms))


def _validate_citation_review_packets(
    packets: pd.DataFrame,
    evidence_map: pd.DataFrame,
) -> None:
    _require_columns(packets, CITATION_REVIEW_PACKET_COLUMNS, "citation review packets")
    if packets["packet_id"].duplicated().any():
        raise ValueError("Citation review packets contain duplicate packet_id values.")
    known_evidence = set(evidence_map["evidence_id"])
    unknown = sorted(set(packets["evidence_id"]).difference(known_evidence))
    if unknown:
        raise ValueError(f"Citation review packets reference unknown evidence ids: {unknown}")
    thesis_facing_candidate = packets[
        (packets["source_status"].isin({"candidate", "rejected"}))
        & (packets["thesis_area"].isin({"H1", "H2", "H3"}))
    ]
    if not thesis_facing_candidate.empty:
        raise ValueError("Candidate or rejected sources appear in H1-H3 citation packets.")
    risky_allowed = packets[
        (packets["source_status"].isin({"candidate", "rejected"}))
        & (packets["draft_use_allowed"].astype(bool))
    ]
    if not risky_allowed.empty:
        raise ValueError("Candidate or rejected sources cannot be draft-use allowed.")
    if packets["review_question"].astype(str).str.len().eq(0).any():
        raise ValueError("Citation review packets require review questions.")
    if packets["required_check"].astype(str).str.len().eq(0).any():
        raise ValueError("Citation review packets require check instructions.")


def _validate_source_review_plan(frame: pd.DataFrame) -> None:
    _require_columns(frame, SOURCE_REVIEW_PLAN_COLUMNS, "source review plan")
    if frame["source_id"].duplicated().any():
        raise ValueError("Source review plan contains duplicate source_id values.")
    for column in (
        "priority_band",
        "required_review_output",
        "thesis_use_boundary",
        "next_action",
    ):
        if frame[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Source review plan contains empty {column}.")
    blocked = frame[
        frame["final_citation_readiness"].isin(
            {"not_allowed_for_thesis_facing_claims", "do_not_cite"}
        )
    ]
    if not blocked["priority_band"].eq("blocked_or_future_work_only").all():
        raise ValueError("Blocked sources must remain blocked or future-work only.")
    core_priority = frame["priority_band"].isin(
        {
            "priority_1_method_foundation_review",
            "priority_2_core_interpretation_review",
        }
    )
    risky_core = frame[core_priority & frame["source_status"].isin({"candidate", "rejected"})]
    if not risky_core.empty:
        raise ValueError("Candidate or rejected sources cannot be core source-review priorities.")
    joined = " ".join(frame.fillna("").astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Source review plan contains German sharp-s.")


def _validate_table_figure_captions(
    captions: pd.DataFrame,
    *,
    repo_root: Path,
) -> None:
    _require_columns(captions, TABLE_FIGURE_CAPTION_COLUMNS, "table and figure captions")
    if captions["package_id"].duplicated().any():
        raise ValueError("Table and figure captions contain duplicate package_id values.")
    core = captions[captions["include_in_core_package"].astype(bool)]
    if (core["package_type"] == "table").sum() > 5:
        raise ValueError("Caption registry has more than five core tables.")
    if (core["package_type"] == "figure").sum() > 4:
        raise ValueError("Caption registry has more than four core figures.")
    for row in captions.to_dict(orient="records"):
        _validate_artifact_list(repo_root, [str(row["primary_artifact"])])
        _validate_artifact_list(repo_root, _split_list(str(row["supporting_artifacts"])))
        for column in (
            "thesis_label",
            "caption_de",
            "source_note_de",
            "interpretation_note_de",
            "limitation_note_de",
        ):
            if not str(row[column]).strip():
                raise ValueError(f"{row['package_id']} is missing {column}.")
        joined = " ".join(str(row[column]) for column in TABLE_FIGURE_CAPTION_COLUMNS)
        if chr(223) in joined:
            raise ValueError(f"{row['package_id']} caption contains German sharp-s.")


def _validate_artifact_list(repo_root: Path, artifacts: Iterable[str]) -> None:
    for artifact in artifacts:
        if not artifact:
            continue
        if artifact in GENERATED_ARTIFACTS:
            continue
        _required_file(repo_root / artifact)


def _build_metadata(
    *,
    evidence_map: pd.DataFrame,
    core_results: pd.DataFrame,
    curated_package: pd.DataFrame,
    citation_readiness: pd.DataFrame,
    chapter_plan: pd.DataFrame,
    agent_pipeline: pd.DataFrame,
    citation_review_packets: pd.DataFrame,
    table_figure_captions: pd.DataFrame,
    source_review_plan: pd.DataFrame,
    agent_assistance_protocol: pd.DataFrame,
    next_work_plan: pd.DataFrame,
    project_highlevel_view: pd.DataFrame,
) -> dict[str, object]:
    core = curated_package[curated_package["include_in_core_package"].astype(bool)]
    return {
        "method": {
            "name": "thesis_consolidation_evidence_mapping",
            "calculation_scope": "selection_and_mapping_of_existing_deterministic_artifacts",
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_write_database": True,
            "does_not_call_external_api": True,
        },
        "outputs": {
            "evidence_rows": int(len(evidence_map)),
            "core_result_rows": int(len(core_results)),
            "package_rows": int(len(curated_package)),
            "citation_readiness_rows": int(len(citation_readiness)),
            "chapter_rows": int(len(chapter_plan)),
            "agent_stage_rows": int(len(agent_pipeline)),
            "citation_review_packet_rows": int(len(citation_review_packets)),
            "table_figure_caption_rows": int(len(table_figure_captions)),
            "source_review_plan_rows": int(len(source_review_plan)),
            "agent_assistance_protocol_rows": int(len(agent_assistance_protocol)),
            "next_work_plan_rows": int(len(next_work_plan)),
            "project_highlevel_view_rows": int(len(project_highlevel_view)),
            "writing_blueprint_generated": True,
            "chapter_draft_generated": True,
            "core_table_count": int((core["package_type"] == "table").sum()),
            "core_figure_count": int((core["package_type"] == "figure").sum()),
            "max_core_tables": 5,
            "max_core_figures": 4,
        },
        "readiness_counts": {
            str(key): int(value)
            for key, value in evidence_map["thesis_readiness"].value_counts().sort_index().items()
        },
        "citation_readiness_counts": {
            str(key): int(value)
            for key, value in citation_readiness["final_citation_readiness"]
            .value_counts()
            .sort_index()
            .items()
        },
        "chapter_status_counts": {
            str(key): int(value)
            for key, value in chapter_plan["writing_status"].value_counts().sort_index().items()
        },
        "agent_stage_status_counts": {
            str(key): int(value)
            for key, value in agent_pipeline["implementation_status"]
            .value_counts()
            .sort_index()
            .items()
        },
        "citation_review_packet_counts": {
            "pending_packets": int((citation_review_packets["reviewer_decision"] == "pending").sum()),
            "draft_use_allowed_packets": int(citation_review_packets["draft_use_allowed"].astype(bool).sum()),
            "blocked_or_future_only_packets": int((~citation_review_packets["draft_use_allowed"].astype(bool)).sum()),
            "full_review_required_packets": int(
                (
                    citation_review_packets["final_citation_gate"]
                    == "full_source_review_required_before_final_citation"
                ).sum()
            ),
        },
        "table_figure_caption_counts": {
            "core_table_captions": int(
                (
                    table_figure_captions["include_in_core_package"].astype(bool)
                    & (table_figure_captions["package_type"] == "table")
                ).sum()
            ),
            "core_figure_captions": int(
                (
                    table_figure_captions["include_in_core_package"].astype(bool)
                    & (table_figure_captions["package_type"] == "figure")
                ).sum()
            ),
            "total_caption_rows": int(len(table_figure_captions)),
        },
        "source_review_plan_counts": {
            str(key): int(value)
            for key, value in source_review_plan["priority_band"]
            .value_counts()
            .sort_index()
            .items()
        },
        "agent_assistance_protocol_counts": {
            str(key): int(value)
            for key, value in agent_assistance_protocol["activation_status"]
            .value_counts()
            .sort_index()
            .items()
        },
        "next_work_plan_counts": {
            "workstreams": int(len(next_work_plan)),
            "highest_priority": str(
                next_work_plan.sort_values("priority_order").iloc[0]["workstream_id"]
            ),
            "final_priority": str(
                next_work_plan.sort_values("priority_order").iloc[-1]["workstream_id"]
            ),
        },
        "project_highlevel_view_counts": {
            "rows": int(len(project_highlevel_view)),
            "paused_rows": int((project_highlevel_view["status"] == "paused_appendix_only").sum()),
            "documentation_only_rows": int(
                (project_highlevel_view["status"] == "documentation_only_deferred").sum()
            ),
            "thesis_facing_rows": int(
                project_highlevel_view["status"]
                .isin({"thesis_facing_ready", "thesis_facing_ready_with_limits"})
                .sum()
            ),
        },
        "guardrails": {
            "every_method_and_interpretation_has_artifact": True,
            "citation_readiness_is_status_mapping_not_source_promotion": True,
            "citation_review_packets_are_pending_human_review": True,
            "table_figure_captions_use_curated_package_only": True,
            "source_review_plan_is_manual_review_queue": True,
            "agent_assistance_protocol_is_documentation_only": True,
            "next_work_plan_is_guardrail_bound": True,
            "project_highlevel_view_is_status_summary_not_result_metric": True,
            "project_highlevel_view_keeps_review_access_paused": True,
            "chapter_plan_uses_curated_package": True,
            "thesis_facing_rows_avoid_candidate_or_rejected_sources": True,
            "swiss_final_efficiency_interpretation_pending": True,
            "monitor_review_cases_not_thesis_evidence": True,
            "future_agents_documentation_only": True,
            "llm_audit_log_required_before_future_llm_calls": True,
            "no_raw_table_dumps": True,
            "max_future_tool_rows": 50,
            "no_wallet_address_exposure_by_default": True,
            "no_order_or_trading_paths": True,
        },
    }


def _render_evidence_markdown(evidence_map: pd.DataFrame) -> str:
    display = evidence_map[
        [
            "evidence_id",
            "thesis_area",
            "item_type",
            "primary_artifact",
            "literature_sources",
            "thesis_readiness",
        ]
    ]
    return (
        "# Thesis Evidence Map\n\n"
        "This map links thesis-facing methods and interpretations to deterministic "
        "artifacts and source references. It is generated by "
        "`python -m operations.analysis.thesis_consolidation`.\n\n"
        + _markdown_table(display)
        + "\n"
    )


def _render_consolidation_doc(
    *,
    evidence_map: pd.DataFrame,
    core_results: pd.DataFrame,
    curated_package: pd.DataFrame,
    citation_readiness: pd.DataFrame,
    chapter_plan: pd.DataFrame,
    agent_pipeline: pd.DataFrame,
    project_highlevel_view: pd.DataFrame,
    metadata: dict[str, object],
) -> str:
    core = curated_package[curated_package["include_in_core_package"].astype(bool)].copy()
    tables = core[core["package_type"] == "table"]
    figures = core[core["package_type"] == "figure"]
    agent_row = evidence_map[evidence_map["evidence_id"] == "future_agent_pipeline_guarded"].iloc[0]
    citation_display = citation_readiness[
        citation_readiness["used_by_evidence_ids"].astype(str).str.len() > 0
    ][
        [
            "source_id",
            "status",
            "used_by_thesis_areas",
            "final_citation_readiness",
            "citation_risk",
        ]
    ]
    highlevel_display = project_highlevel_view[
        [
            "view_id",
            "project_layer",
            "status",
            "current_decision",
            "next_gate",
            "thesis_use",
        ]
    ]

    return (
        "# Thesis Consolidation\n\n"
        "## Purpose\n\n"
        "This document is the high-level consolidation layer for the bachelor thesis. "
        "It reduces the many generated artifacts to a small thesis-ready package and "
        "keeps every central method and interpretation tied to deterministic evidence.\n\n"
        "## Project Highlevel View\n\n"
        "`data/results/thesis_project_highlevel_view.csv` summarises the current "
        "project layers, decisions, next gates, and thesis-use boundaries. It keeps "
        "review access paused and does not add new empirical metrics.\n\n"
        + _markdown_table(highlevel_display)
        + "\n\n"
        "## Core Result Table\n\n"
        + _markdown_table(
            core_results[
            [
                "result_id",
                "thesis_area",
                "headline_result",
                "key_value",
                "thesis_readiness",
            ]
            ]
        )
        + "\n\n"
        "## Recommended Tables\n\n"
        + _markdown_table(
            tables[
            [
                "package_id",
                "title",
                "primary_artifact",
                "recommended_placement",
                "thesis_readiness",
            ]
            ]
        )
        + "\n\n"
        "## Recommended Figures\n\n"
        + _markdown_table(
            figures[
            [
                "package_id",
                "title",
                "primary_artifact",
                "recommended_placement",
                "thesis_readiness",
            ]
            ]
        )
        + "\n\n"
        "## Citation Readiness\n\n"
        "This table is a source-control view, not a promotion of source status. "
        "Sources marked `skimmed` can guide draft structure, but final thesis citation "
        "wording still needs source-by-source review.\n\n"
        + _markdown_table(citation_display)
        + "\n\n"
        "## Citation Review Packets\n\n"
        "`data/results/thesis_citation_review_packets.csv` breaks the source "
        "review into source-evidence packets. Each row links one source to one "
        "Evidence ID, the deterministic artifact, allowed wording, blocked wording, "
        "review question, and final citation gate. The packet file is a worklist, "
        "not a source-status promotion.\n\n"
        "## Source Review Plan\n\n"
        "`data/results/thesis_source_review_plan.csv` groups the citation packets "
        "by source and assigns manual review bands. It has "
        f"{metadata['outputs']['source_review_plan_rows']} source rows and remains "
        "a human review queue, not an automatic source-status promotion.\n\n"
        "## Agent Assistance Protocol\n\n"
        "`data/results/thesis_agent_assistance_protocol.csv` documents how future "
        "agents could help with source review, wording checks, advisor updates, "
        "and bounded summaries. It is documentation-only and does not activate "
        "runtime agents, MCP tools, model routing, or unlogged LLM interpretation.\n\n"
        "## Next Work Plan\n\n"
        "`data/results/thesis_next_work_plan.csv` orders the remaining workstreams "
        "from source review through final thesis QA. It is a planning artifact and "
        "does not change empirical results.\n\n"
        "## Chapter Plan\n\n"
        + _markdown_table(
            chapter_plan[
                [
                    "chapter_id",
                    "chapter_title",
                    "writing_status",
                    "recommended_tables",
                    "recommended_figures",
                    "next_action",
                ]
            ]
        )
        + "\n\n"
        "## Interpretation Discipline\n\n"
        "- Deterministic artifacts come first.\n"
        "- Literature supports method framing and interpretation limits.\n"
        "- H1 can be written as bounded support, not broad superiority.\n"
        "- H2 can be written as daily event-window response, not intraday speed.\n"
        "- H3 can be written as predictive timing diagnostics, not causality or private-information evidence.\n"
        "- Monitor outputs stay prototype or appendix material until human review gates approve them.\n"
        "- Swiss referendum outputs stay descriptive until the official result is available.\n\n"
        "## Deferred Agent Pipeline Idea\n\n"
        f"Primary evidence: `{agent_row['primary_artifact']}`.\n\n"
        "Later agents can improve the workflow only after the thesis-ready deterministic "
        "package is stable. The useful agent roles are documentation assistants, source-check "
        "triage helpers, reviewer-note summarizers, and consistency checkers over bounded "
        "summaries. They must not calculate Brier, CAR, Granger, wallet tiers, whale scores, "
        "PnL, or risk metrics. They must not receive raw table dumps or wallet-address rows. "
        "Every future LLM call must be logged in `llm_audit_log`, and future tool outputs "
        "must stay bounded to at most 50 rows unless a reviewed exception is documented.\n\n"
        "Recommended staged architecture:\n\n"
        + _markdown_table(
            agent_pipeline[
                [
                    "stage_id",
                    "stage_name",
                    "implementation_status",
                    "required_gate_before_activation",
                ]
            ]
        )
        + "\n\n"
        "No runtime agent, MCP implementation, model routing, autonomous collector, or trading path "
        "is part of the current consolidation step.\n\n"
        "## Generated Artifact Counts\n\n"
        f"- Evidence rows: {metadata['outputs']['evidence_rows']}\n"
        f"- Core result rows: {metadata['outputs']['core_result_rows']}\n"
        f"- Citation-readiness rows: {metadata['outputs']['citation_readiness_rows']}\n"
        f"- Chapter rows: {metadata['outputs']['chapter_rows']}\n"
        f"- Agent-stage rows: {metadata['outputs']['agent_stage_rows']}\n"
        f"- Core tables: {metadata['outputs']['core_table_count']}\n"
        f"- Core figures: {metadata['outputs']['core_figure_count']}\n"
    )


def _render_agent_pipeline_doc(
    *,
    agent_pipeline: pd.DataFrame,
    metadata: dict[str, object],
) -> str:
    return (
        "# Thesis Agent Pipeline Roadmap\n\n"
        "This document is documentation-only. It does not implement, activate, or "
        "invoke agents, MCP tools, model routing, autonomous collectors, or trading paths.\n\n"
        "## Guardrails\n\n"
        "- Deterministic Python remains responsible for all metrics.\n"
        "- Future LLM calls require `llm_audit_log` logging before use.\n"
        "- No raw table dumps enter prompts.\n"
        "- Future tool outputs stay bounded to at most 50 rows unless explicitly reviewed.\n"
        "- Wallet-address exposure is blocked by default.\n"
        "- Order placement, order cancellation, authenticated trading channels, and trading credentials stay out of scope.\n\n"
        "## Roadmap Stages\n\n"
        + _markdown_table(agent_pipeline)
        + "\n\n"
        "## Status\n\n"
        f"- Current required disabled stages: {metadata['agent_stage_status_counts'].get('current_required_state', 0)}\n"
        f"- Future documentation-only stages: {metadata['agent_stage_status_counts'].get('future_documentation_only', 0)}\n"
        f"- Future deferred stages: {metadata['agent_stage_status_counts'].get('future_deferred', 0)}\n"
    )


def _render_citation_review_packets_doc(
    *,
    citation_review_packets: pd.DataFrame,
    metadata: dict[str, object],
) -> str:
    focus = citation_review_packets[
        citation_review_packets["source_status"].isin({"skimmed", "candidate"})
    ][
        [
            "source_id",
            "evidence_id",
            "thesis_area",
            "item_type",
            "citation_risk",
            "final_citation_gate",
            "review_question",
        ]
    ].head(50)
    source_summary = (
        citation_review_packets.groupby(["source_id", "source_status", "citation_risk"], dropna=False)
        .agg(packet_count=("packet_id", "count"))
        .reset_index()
        .sort_values(["citation_risk", "source_id"])
    )
    return (
        "# Thesis Citation Review Packets\n\n"
        "This document is generated from the evidence map, literature index, and "
        "citation-readiness table. It is a human-review worklist. It does not "
        "promote any source to `reviewed` or `cited`.\n\n"
        "## Packet Counts\n\n"
        f"- Total packets: {metadata['outputs']['citation_review_packet_rows']}\n"
        f"- Pending packets: {metadata['citation_review_packet_counts']['pending_packets']}\n"
        f"- Draft-use allowed packets: {metadata['citation_review_packet_counts']['draft_use_allowed_packets']}\n"
        f"- Blocked or future-only packets: {metadata['citation_review_packet_counts']['blocked_or_future_only_packets']}\n"
        f"- Full source review required packets: {metadata['citation_review_packet_counts']['full_review_required_packets']}\n\n"
        "## Source Summary\n\n"
        + _markdown_table(source_summary)
        + "\n\n"
        "## Review Worklist\n\n"
        + _markdown_table(focus)
        + "\n\n"
        "## Manual Review Rule\n\n"
        "For each packet, record page or section evidence before final citation. "
        "Candidate sources remain future-work or question-framing material only. "
        "Do not use packet rows to strengthen a claim beyond the linked "
        "deterministic artifact and allowed wording.\n"
    )


def _render_table_figure_captions_doc(
    *,
    table_figure_captions: pd.DataFrame,
    metadata: dict[str, object],
) -> str:
    display = table_figure_captions[
        [
            "package_id",
            "package_type",
            "thesis_label",
            "caption_de",
            "primary_artifact",
            "recommended_placement",
            "thesis_readiness",
        ]
    ]
    return (
        "# Thesis Table And Figure Captions\n\n"
        "This register turns the curated result package into thesis-ready table "
        "and figure captions. It uses only the selected core package rows and "
        "keeps source notes, interpretation notes, and limitations separate.\n\n"
        "## Counts\n\n"
        f"- Total caption rows: {metadata['table_figure_caption_counts']['total_caption_rows']}\n"
        f"- Core table captions: {metadata['table_figure_caption_counts']['core_table_captions']}\n"
        f"- Core figure captions: {metadata['table_figure_caption_counts']['core_figure_captions']}\n\n"
        "## Caption Register\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Usage Rule\n\n"
        "Use these captions with the exact linked artifacts. Do not replace the "
        "curated package with additional raw result files unless the evidence map "
        "and chapter plan are updated first.\n"
    )


def _render_source_review_plan_doc(
    *,
    source_review_plan: pd.DataFrame,
    metadata: dict[str, object],
) -> str:
    display = source_review_plan[
        [
            "source_id",
            "source_status",
            "priority_band",
            "evidence_packet_count",
            "h1_h2_h3_packet_count",
            "method_packet_count",
            "interpretation_packet_count",
            "thesis_use_boundary",
        ]
    ]
    priority_summary = (
        source_review_plan.groupby("priority_band", dropna=False)
        .size()
        .reset_index(name="source_count")
        .sort_values("priority_band")
    )
    return (
        "# Thesis Source Review Plan\n\n"
        "This plan groups the citation review packets by source. It is a manual "
        "source-review queue, not an automatic citation approval step.\n\n"
        "## Counts\n\n"
        f"- Source review rows: {metadata['outputs']['source_review_plan_rows']}\n"
        f"- Citation review packets: {metadata['outputs']['citation_review_packet_rows']}\n"
        f"- Full source review required packets: {metadata['citation_review_packet_counts']['full_review_required_packets']}\n\n"
        "## Priority Summary\n\n"
        + _markdown_table(priority_summary)
        + "\n\n"
        "## Source Review Queue\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Manual Review Rule\n\n"
        "For each priority source, record page or section support before final "
        "citation. Candidate or blocked sources remain unavailable for "
        "thesis-facing claims unless their metadata and status are reviewed "
        "under a separate source update.\n"
    )


def _render_agent_assistance_protocol_doc(
    *,
    agent_assistance_protocol: pd.DataFrame,
    metadata: dict[str, object],
) -> str:
    display = agent_assistance_protocol[
        [
            "protocol_id",
            "pipeline_step",
            "current_artifact_boundary",
            "allowed_inputs",
            "allowed_outputs",
            "audit_gate",
            "activation_status",
        ]
    ]
    return (
        "# Thesis Agent Assistance Protocol\n\n"
        "This protocol documents how future agents could improve the thesis "
        "pipeline after deterministic artifacts and human review gates are stable. "
        "It does not activate runtime agents, MCP tools, model routing, or LLM "
        "interpretation.\n\n"
        "## Counts\n\n"
        f"- Protocol rows: {metadata['outputs']['agent_assistance_protocol_rows']}\n"
        f"- Documentation-only rows: {metadata['agent_assistance_protocol_counts'].get('future_documentation_only', 0)}\n"
        f"- Deferred rows: {metadata['agent_assistance_protocol_counts'].get('future_deferred', 0)}\n\n"
        "## Protocol Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Activation Rule\n\n"
        "No row may be implemented until a separate approved goal exists, "
        "`llm_audit_log` integration is tested, allowed inputs are bounded, and "
        "blocked behaviours remain enforced. Agents must not calculate thesis "
        "metrics, read raw table dumps, expose wallet addresses by default, or "
        "touch order or trading paths.\n"
    )


def _render_next_work_plan_doc(
    *,
    next_work_plan: pd.DataFrame,
    metadata: dict[str, object],
) -> str:
    display = next_work_plan[
        [
            "priority_order",
            "workstream_id",
            "workstream",
            "thesis_section",
            "current_artifact",
            "next_action",
            "blocked_until",
            "guardrail",
        ]
    ].sort_values("priority_order")
    return (
        "# Thesis Next Work Plan\n\n"
        "This plan orders the remaining thesis work after the consolidation "
        "package. It is a project-control artifact, not a new empirical analysis.\n\n"
        "## Counts\n\n"
        f"- Workstreams: {metadata['outputs']['next_work_plan_rows']}\n"
        f"- First priority: {metadata['next_work_plan_counts']['highest_priority']}\n"
        f"- Final priority: {metadata['next_work_plan_counts']['final_priority']}\n\n"
        "## Ordered Workstreams\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Use this file to sequence the thesis work. Do not expand empirical scope, "
        "activate agents, add raw result files to the core package, or make final "
        "Swiss efficiency claims before the relevant gates are cleared.\n"
    )


def _render_project_highlevel_view_doc(
    *,
    project_highlevel_view: pd.DataFrame,
    metadata: dict[str, object],
) -> str:
    display = project_highlevel_view[
        [
            "view_id",
            "project_layer",
            "status",
            "role_in_thesis",
            "current_decision",
            "next_gate",
            "guardrail",
            "thesis_use",
        ]
    ]
    counts = metadata["project_highlevel_view_counts"]
    return (
        "# Thesis Project Highlevel View\n\n"
        "This generated status matrix gives the project-level answer to what "
        "happens next: the thesis core is H1-H3, review access remains paused, "
        "monitor material stays appendix/prototype only, Swiss remains pending "
        "until the official result, and future agents stay documentation-only.\n\n"
        "## Kurzantwort: Weiter Ohne Review-Access\n\n"
        "- Review-Access bleibt pausiert; der naechste Fortschritt kommt aus "
        "Schreiben und Review-Gates.\n"
        "- Zuerst Dozentenpaket senden und Feedback im Log festhalten.\n"
        "- Danach Source Review prioritaer abarbeiten, H1-H3 Kapitel schreiben "
        "und Tabellen/Figuren integrieren.\n"
        "- Access Audit, Source Structure Inventory und Traceability Audit nur "
        "als Vorbereitung nutzen: keine Quellenstatus-Hochstufung und keine "
        "Support-Claims aus Dateistruktur.\n"
        "- Swiss bleibt bis zum offiziellen Resultat am 14. Juni 2026 "
        "beschreibend.\n"
        "- Agenten bleiben Future Work; keine Runtime-Agenten, MCP, Model "
        "Routing oder LLM-Metriken.\n\n"
        "## Counts\n\n"
        f"- Project rows: {counts['rows']}\n"
        f"- Thesis-facing empirical rows: {counts['thesis_facing_rows']}\n"
        f"- Paused appendix rows: {counts['paused_rows']}\n"
        f"- Documentation-only rows: {counts['documentation_only_rows']}\n\n"
        "## Project Matrix\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Use this file for advisor discussion and thesis sequencing. It is a "
        "status and boundary summary, not a new empirical result. It must not be "
        "used to reactivate review access, agents, MCP tools, model routing, raw "
        "table access, wallet-address exposure, or order/trading paths.\n"
    )


def _render_writing_blueprint(
    *,
    core_results: pd.DataFrame,
    curated_package: pd.DataFrame,
    citation_readiness: pd.DataFrame,
    chapter_plan: pd.DataFrame,
) -> str:
    package_lookup = curated_package.set_index("package_id").to_dict(orient="index")
    core_by_area = {
        area: rows.to_dict(orient="records")
        for area, rows in core_results.groupby("thesis_area", sort=True)
    }
    citation_counts = citation_readiness["final_citation_readiness"].value_counts().to_dict()
    sections: list[str] = [
        "# Thesis Writing Blueprint\n",
        "This blueprint translates the deterministic consolidation package into a "
        "chapter-by-chapter writing plan. It is a drafting guide, not a new "
        "empirical analysis.\n",
        "## Source And Citation Work\n",
        f"- Sources needing full review before final citation: "
        f"{int(citation_counts.get('needs_full_source_review_before_final_citation', 0))}\n",
        f"- Candidate sources blocked from thesis-facing claims: "
        f"{int(citation_counts.get('not_allowed_for_thesis_facing_claims', 0))}\n",
        f"- Indexed sources not currently needed: "
        f"{int(citation_counts.get('not_currently_needed', 0))}\n",
        "Use `data/results/thesis_citation_readiness.csv` as the source-review queue. "
        "Do not promote source status automatically.\n",
        "## Core Writing Rule\n",
        "Every paragraph that states a result should name one deterministic artifact "
        "or one evidence_id. Every paragraph that states a method should name the "
        "method source or explain why the artifact is sufficient.\n",
    ]

    for row in chapter_plan.to_dict(orient="records"):
        tables = _split_list(str(row["recommended_tables"]))
        figures = _split_list(str(row["recommended_figures"]))
        evidence_ids = _split_list(str(row["core_evidence_ids"]))
        package_refs = [package_lookup[item] for item in [*tables, *figures] if item in package_lookup]
        areas = _areas_for_evidence_ids(evidence_ids)
        include_result_statements = str(row["chapter_id"]) in {
            "ch_04_h1_results",
            "ch_05_h2_results",
            "ch_06_h3_results",
            "ch_07_extensions",
            "ch_08_discussion_conclusion",
        }
        result_rows = (
            [
                result
                for area in areas
                for result in core_by_area.get(area, [])
            ]
            if include_result_statements
            else []
        )
        sections.append(f"## {row['chapter_title']}\n")
        sections.append(f"Chapter role: {row['chapter_role']}\n")
        sections.append(f"Writing status: `{row['writing_status']}`\n")
        sections.append(f"Core evidence ids: `{'; '.join(evidence_ids)}`\n")
        if package_refs:
            sections.append("Recommended package items:\n")
            for ref in package_refs:
                sections.append(
                    f"- `{ref['title']}` from `{ref['primary_artifact']}` "
                    f"({ref['recommended_placement']}).\n"
                )
        if result_rows:
            sections.append("Result statements to use:\n")
            for result in result_rows:
                sections.append(
                    f"- {result['headline_result']} Key value: {result['key_value']} "
                    f"Source: `{result['primary_artifact']}`.\n"
                )
        sections.append(f"Limitation to state: {row['main_limitation_to_state']}\n")
        sections.append(f"Next writing action: {row['next_action']}\n")

    sections.extend(
        [
            "## Agent-Assisted Pipeline Outlook\n",
            "Use this only as future work. Later agents may help read the evidence map, "
            "check citation readiness, and compare draft paragraphs with allowed or "
            "blocked wording. They must not calculate metrics, read raw tables by "
            "default, expose wallet-address rows, or create order/trading paths. "
            "Future LLM calls require `llm_audit_log` first.\n",
        ]
    )
    return "\n".join(sections)


def _render_chapter_draft(
    *,
    evidence_map: pd.DataFrame,
    core_results: pd.DataFrame,
    curated_package: pd.DataFrame,
    citation_readiness: pd.DataFrame,
    chapter_plan: pd.DataFrame,
) -> str:
    evidence = evidence_map.set_index("evidence_id").to_dict(orient="index")
    package = curated_package.set_index("package_id").to_dict(orient="index")
    core = core_results.set_index("result_id").to_dict(orient="index")
    citation_counts = citation_readiness["final_citation_readiness"].value_counts().to_dict()

    h1_bounded = core["core_h1_bounded_poll_scope"]
    h1_boundary = core["core_h1_broad_claim_boundary"]
    h2_result = core["core_h2_largest_daily_event_window"]
    h3_result = core["core_h3_top_tier_timing"]
    monitor_result = core["core_monitor_review_queue_boundary"]
    swiss_result = core["core_swiss_running_gap_pending"]

    return "\n".join(
        [
            "# Thesis Chapter Draft\n",
            "Arbeitsfassung fuer die Bachelorarbeit. Dieser Text ist eine "
            "strukturierte Draft-Prosa aus der deterministischen "
            "Konsolidierungspipeline. Er ersetzt keine finale Quellenpruefung "
            "und fuehrt keine neuen Kennzahlen ein.\n",
            "## 1. Einleitung und Forschungsfrage\n",
            "Dezentrale Prognosemaerkte wie Polymarket verdichten Erwartungen "
            "vieler Marktteilnehmer zu handelbaren Wahrscheinlichkeiten. Die "
            "Bachelorarbeit untersucht, ob und in welchem Umfang solche Preise "
            "Informationen effizienter abbilden als traditionelle Prognose- und "
            "Umfragequellen. Informationelle Effizienz wird dabei nicht als "
            "direkt beobachtbare Eigenschaft behandelt, sondern ueber drei "
            "deterministische Proxy-Ebenen operationalisiert: Prognosequalitaet "
            "(H1), Ereignisfenster-Reaktionen (H2) und walletbasierte "
            "Timing-Diagnostik (H3). Die methodische Grundregel lautet, dass "
            "statistische Kennzahlen ausschliesslich in Python berechnet werden "
            "und jede Interpretation auf ein Artefakt oder eine Evidence-ID "
            "zurueckgefuehrt werden muss. Zentrale Einstiegsartefakte sind "
            f"`{package['T1']['primary_artifact']}` und "
            "`data/results/thesis_core_results_table.csv`.\n",
            "Die leitende Forschungsfrage lautet: In welchem Ausmass zeigen "
            "Polymarket-Preise im US-Wahlkontext 2024 eine hoehere "
            "Prognosequalitaet, eine sichtbare Reaktion auf oeffentliche "
            "Ereignisse und fruehe walletbasierte Signalstrukturen im Vergleich "
            "zu traditionellen Prognosequellen? Die Antwort wird bewusst "
            "begrenzt formuliert: Die Arbeit kann Evidenz fuer bestimmte "
            "diagnostische Muster liefern, aber keine universelle Aussage ueber "
            "alle Prognosemaerkte, keine Intraday-Geschwindigkeitsbehauptung "
            "und keine Aussage ueber handelbare Gewinne.\n",
            "## 2. Theorie und Literatur\n",
            "Der theoretische Rahmen stuetzt sich auf die Idee informationeller "
            "Markteffizienz und auf Literatur zu Prognosemaerkten, "
            "Vorhersageguete, Ereignisstudien und walletbasierter "
            "Marktbeobachtung. Die aktuelle Quellensteuerung liegt in "
            "`data/results/thesis_citation_readiness.csv`. Diese Datei zeigt, "
            f"dass {int(citation_counts.get('needs_full_source_review_before_final_citation', 0))} "
            "Quellen vor finaler Zitation noch vollstaendig geprueft werden "
            "muessen, waehrend eine Candidate-Quelle nicht fuer "
            "thesis-facing Claims verwendet werden darf. Fuer H1 sind "
            "`lit_brier_001`, `lit_dm_001` und `zotero_poly_002` die "
            "wesentlichen Quellenanker. Fuer H2 wird die Event-Study-Logik "
            "ueber `lit_eventstudy_001` gestuetzt. Fuer H3 dienen "
            "`lit_granger_001`, `zotero_poly_001` und `zotero_poly_005` als "
            "Rahmen fuer Timingdiagnostik und die vorsichtige Interpretation "
            "von Walletdaten.\n",
            "Wichtig ist die Trennung zwischen Literaturrahmen und empirischem "
            "Befund. Literatur motiviert die Methode und begrenzt die Sprache, "
            "ersetzt aber keine lokalen Ergebnisartefakte. Deshalb sind "
            "Quellen mit Status `skimmed` fuer die Draft-Struktur nutzbar, "
            "aber vor finaler Abgabe noch nicht automatisch zitierfertig. Die "
            "Literaturmap und die Evidence-Map verhindern, dass spaeter "
            "unbelegte Theorieaussagen oder nicht gepruefte Quellen in die "
            "Thesis uebernommen werden.\n",
            "## 3. Daten und Methodik\n",
            "Die empirische Pipeline folgt dem Prinzip: Datenvalidierung, "
            "deterministische Analyse, danach erst Interpretation. H1 bewertet "
            "Prognosequalitaet ueber Brier-Verlust und den "
            "Diebold-Mariano-Vergleich vorberechneter Verlustreihen. "
            f"Primaere Artefakte sind `{evidence['method_h1_brier_dm']['primary_artifact']}` "
            "sowie `data/results/h1_brier_scores.csv` und "
            "`data/results/h1_diebold_mariano.json`. RCP wird nicht als native "
            "Wahrscheinlichkeitsprognose genutzt, solange keine dokumentierte "
            "Transformation vorliegt.\n",
            "H2 nutzt vorab kuratierte Ereignisse und feste Tagesfenster. "
            f"Die Methode ist in `{evidence['method_h2_event_window']['primary_artifact']}` "
            "und `data/events_timeline_seed.csv` abgebildet. Ereignisse werden "
            "nicht nach Sichtung der Marktreaktion hinzugefuegt oder entfernt. "
            "Die H2-Aussagen bleiben auf Tagesdaten beschraenkt.\n",
            "H3 bildet Walletgruppen nicht ueber fixe USD-Schwellen, sondern "
            "ueber dataset-relative Tiers. Die zugehoerigen Artefakte sind "
            "`data/results/h3_wallet_distribution_inventory.json`, "
            "`data/results/h3_wallet_tiers.csv`, "
            "`data/results/h3_lead_lag_correlations.csv` und "
            "`data/results/h3_granger_results.csv`. Die Granger-Ausgaben "
            "werden als predictive timing diagnostics gelesen, nicht als "
            "Kausalitaetsbeweis. Die wichtigste methodische Limitation bleibt "
            "die BUY-only-Quelle und die taegliche Aggregation.\n",
            "## 4. H1: Prognosequalitaet\n",
            "Das zentrale H1-Ergebnis lautet: Im begrenzten "
            "Poll-Vergleichsscope unterstuetzen die Artefakte eine "
            "Polymarket-Staerke. "
            f"Der aktuelle Kernwert ist {_de_key_value(h1_bounded['key_value'])}. Die Aussage "
            f"stuetzt sich auf `{h1_bounded['primary_artifact']}` und die "
            "Evidence-ID `interpretation_h1_bounded_advantage`. Damit ist eine "
            "begrenzte, scope-spezifische Polymarket-Staerke sichtbar.\n",
            "Gleichzeitig ist die breite Ueberlegenheitsbehauptung nicht "
            "gedeckt. Der zugehoerige Kernwert lautet: "
            f"{_de_key_value(h1_boundary['key_value'])}. Diese Grenze ist fuer die Thesis "
            "zentral, weil sie verhindert, dass ein einzelner unterstuetzter "
            "Scope zu einer allgemeinen Ueberlegenheitsbehauptung ausgedehnt "
            "wird. Die korrekte H1-Interpretation ist deshalb: Polymarket zeigt "
            "in definierten spaeten und kompatiblen Vergleichsfenstern bessere "
            "Brier-Verluste, aber die Gesamtevidenz bleibt gemischt und "
            "kontextabhaengig.\n",
            f"Empfohlene Darstellung: Tabelle `{package['T2']['primary_artifact']}` "
            f"und Abbildung `{package['F1']['primary_artifact']}`. Die "
            "Limitation ist explizit zu nennen: unterschiedliche "
            "Vergleichseinheiten, transformierte Poll-Signale und wiederholte "
            "Tageszeilen sind keine unabhaengigen Wahlen.\n",
            "## 5. H2: Ereignisfenster\n",
            "Fuer H2 zeigt die aktuelle Kernzeile: Die groesste primaere "
            "Tagesfensterbewegung liegt im Trump-Shooting-Fenster. "
            f"Der Wert ist {_de_key_value(h2_result['key_value'])}. Quelle ist "
            f"`{h2_result['primary_artifact']}`, gestuetzt durch "
            "`interpretation_h2_daily_response`. Das Ergebnis zeigt, dass "
            "Polymarket-Preise um kuratierte oeffentliche Ereignisse sichtbare "
            "Tagesbewegungen aufweisen.\n",
            "Die Interpretation bleibt jedoch eine Tagesfensterdiagnostik. Aus "
            "diesen Artefakten darf nicht abgeleitet werden, dass Polymarket "
            "innerhalb von Minuten oder Stunden schneller reagiert als andere "
            "Quellen. Fuer eine solche Aussage waeren validierte Intraday- oder "
            "Orderbuchdaten noetig. In der Thesis sollte H2 daher als Evidenz "
            "fuer beobachtbare Tagesreaktionen geschrieben werden, nicht als "
            "Beweis fuer unmittelbare Informationsverarbeitung.\n",
            f"Empfohlene Darstellung: Tabelle `{package['T3']['primary_artifact']}` "
            f"und Abbildung `{package['F2']['primary_artifact']}`.\n",
            "## 6. H3: Wallet-Timing\n",
            "Das zentrale H3-Ergebnis lautet: Das oberste Wallet-Tier zeigt "
            "die klarste aktuelle Timingdiagnostik. "
            f"Der aktuelle Kernwert ist {_de_key_value(h3_result['key_value'])}. Die Aussage "
            f"stuetzt sich auf `{h3_result['primary_artifact']}`, "
            "`data/results/h3_granger_results.csv` und "
            "`data/results/h3_lead_lag_correlations.csv`. H3 zeigt damit eine "
            "auffaellige top-tier Timingdiagnostik, aber keinen "
            "Kausalitaetsnachweis und keine Aussage ueber private Informationen "
            "oder Profitabilitaet.\n",
            "Fuer die Thesis ist die Formulierung entscheidend. Erlaubt ist: "
            "dataset-relative Wallet-Tiers zeigen unter taeglicher Aggregation "
            "Timingmuster, die als predictive diagnostics gelesen werden "
            "koennen. Nicht erlaubt ist: identifizierte Wallets belegen "
            "Fehlverhalten, private Informationsnutzung oder eine handelbare "
            "Strategie. Die Limitationen BUY-only, taegliche Frequenz, "
            "Mehrfachtests und moegliche Upstream-Filter gehoeren direkt in den "
            "Ergebnistext.\n",
            f"Empfohlene Darstellung: Tabelle `{package['T4']['primary_artifact']}` "
            f"und Abbildung `{package['F3']['primary_artifact']}`.\n",
            "## 7. Erweiterungen: Monitor und Schweizer Abstimmung\n",
            "Der Monitor-Prototyp ist nuetzlich als Workflow- und "
            "Appendix-Material, aber nicht als empirischer Beweis. "
            f"Kernwert: {_de_key_value(monitor_result['key_value'])}. Die zugehoerigen "
            "Artefakte bleiben reviewgebunden und sind keine thesis-facing "
            "Evidenz fuer Ursachen, Regelverstoesse, Marktineffizienz, "
            "Handelbarkeit oder Gewinne.\n",
            "Der Schweizer Abstimmungstrack bleibt bis zum offiziellen "
            "Resultat beschreibend. "
            f"Kernwert: {_de_key_value(swiss_result['key_value'])}. Die aktuelle Figur "
            f"`{package['F4']['primary_artifact']}` darf als laufender "
            "Poll-Proxy-Vergleich genutzt werden, aber nicht als finaler "
            "Effizienzbefund. Poll-Anteile sind keine echten "
            "Modellwahrscheinlichkeiten.\n",
            "## 8. Diskussion und Fazit\n",
            "Die bisherigen Ergebnisse sprechen fuer eine differenzierte "
            "Antwort. H1 liefert in einem abgegrenzten Vergleichsscope starke "
            "Unterstuetzung fuer Polymarket, waehrend eine breite "
            "Ueberlegenheitsbehauptung nicht bewiesen ist. H2 zeigt sichtbare "
            "Tagesbewegungen um kuratierte Ereignisse, ohne Intraday-Aussagen "
            "zu erlauben. H3 zeigt eine top-tier Wallet-Timingdiagnostik, die "
            "als fruehes Signal interpretiert werden kann, aber keine "
            "Kausalitaet, keine private Informationsnutzung und keine "
            "Profitabilitaet belegt.\n",
            "Das Fazit sollte deshalb nicht lauten, dass Polymarket generell "
            "effizienter ist als traditionelle Prognosequellen. Praeziser ist: "
            "Die Arbeit findet in klar definierten Ausschnitten Hinweise auf "
            "bessere Prognosequalitaet, sichtbare Ereignisreaktionen und "
            "walletbasierte Timingmuster. Gleichzeitig bleiben "
            "Datenfrequenz, Quellenstatus, Poll-Transformation, BUY-only "
            "Walletdaten und fehlende finale Swiss-Auswertung zentrale "
            "Limitationen.\n",
            "## 9. Agenten-Pipeline als Ausblick\n",
            "Die Agenten-Pipeline ist ein spaeterer Arbeitsausblick, nicht Teil "
            "des aktiven empirischen Kerns. Sinnvolle Agentenrollen waeren "
            "Evidence Reader, Citation Checker, Wording Guard und "
            "Monitor-Review-Helfer. Alle Rollen duerfen nur bounded summaries "
            "lesen, muessen in `llm_audit_log` protokolliert werden und duerfen "
            "keine Kennzahlen berechnen. MCP-Zugriff waere erst nach separatem "
            "Ziel, Tests, Access Contract und Audit-Logging vertretbar. "
            "Order- oder Tradingpfade bleiben ausgeschlossen.\n",
        ]
    )


def _areas_for_evidence_ids(evidence_ids: list[str]) -> list[str]:
    areas: list[str] = []
    for evidence_id in evidence_ids:
        if "_h1_" in evidence_id or evidence_id.endswith("_h1_brier_dm"):
            areas.append("H1")
        elif "_h2_" in evidence_id:
            areas.append("H2")
        elif "_h3_" in evidence_id:
            areas.append("H3")
        elif "monitor" in evidence_id:
            areas.append("monitor_prototype")
        elif "swiss" in evidence_id:
            areas.append("swiss_referendum")
    return sorted(set(areas))


def _de_key_value(value: object) -> str:
    text = str(value)
    replacements = {
        "state-date rows": "State-Date-Zeilen",
        "lower Brier loss for Polymarket": "mit niedrigerem Brier-Verlust fuer Polymarket",
        "aggregate rows support Polymarket": "Aggregate-Zeilen unterstuetzen Polymarket",
        "majority-case rows support Polymarket": "Majority-Case-Zeilen unterstuetzen Polymarket",
        "broad rows prove the claim": "Broad-Claim-Zeilen beweisen die breite Aussage",
        "audit rows contradict the strong claim": "Audit-Zeilen widersprechen der starken Aussage",
        "correlation": "Korrelation",
        "aligned rows": "alignierte Zeilen",
        "review cases": "Review-Faelle",
        "high": "hoch",
        "medium": "mittel",
        "snapshots": "Snapshots",
        "latest": "aktuell",
        "Polymarket Yes": "Polymarket-Yes",
        "poll Yes": "Poll-Yes",
        "raw gap": "Raw-Gap",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _citation_review_question(evidence_row: dict[str, object]) -> str:
    item_type = str(evidence_row["item_type"])
    thesis_area = str(evidence_row["thesis_area"])
    claim = str(evidence_row["claim_or_decision"])
    allowed = str(evidence_row["allowed_wording"])
    blocked = str(evidence_row["blocked_wording"])
    if item_type == "method":
        return (
            f"Does this source justify the {thesis_area} method choice '{claim}' "
            f"and support the allowed wording '{allowed}' without implying '{blocked}'?"
        )
    if item_type == "interpretation":
        return (
            f"Does this source support the interpretation boundary for {thesis_area} "
            f"without extending beyond deterministic artifact evidence or implying '{blocked}'?"
        )
    return (
        f"Is this source suitable only for the planned {thesis_area} future-work framing, "
        "without supporting active thesis metrics or runtime agents?"
    )


def _source_review_priority_band(
    *,
    source_status: str,
    readiness: str,
    method_packet_count: int,
    h1_h2_h3_packet_count: int,
    evidence_packet_count: int,
) -> str:
    if readiness in {"not_allowed_for_thesis_facing_claims", "do_not_cite"}:
        return "blocked_or_future_work_only"
    if evidence_packet_count == 0:
        return "not_currently_needed"
    if source_status in {"reviewed", "cited"}:
        return "format_and_page_note_check"
    if method_packet_count > 0:
        return "priority_1_method_foundation_review"
    if h1_h2_h3_packet_count > 0:
        return "priority_2_core_interpretation_review"
    return "priority_3_context_or_appendix_review"


def _source_review_required_output(priority_band: str) -> str:
    if priority_band == "not_currently_needed":
        return "none_until_source_is_added_to_an_evidence_row"
    if priority_band == "blocked_or_future_work_only":
        return "metadata_and_relevance_note_only_no_thesis_claim_use"
    if priority_band == "format_and_page_note_check":
        return "page_or_section_note_and_final_citation_format_check"
    return "page_or_section_note_claim_support_check_and_blocked_wording_check"


def _source_review_use_boundary(readiness: str) -> str:
    if readiness == "final_citation_ready":
        return "may_be_used_after_format_and_page_note_check"
    if readiness == "reviewed_not_final_citation":
        return "reviewed_but_final_citation_format_still_needed"
    if readiness == "needs_full_source_review_before_final_citation":
        return "draft_structure_only_until_full_source_review"
    if readiness == "not_currently_needed":
        return "not_used_in_current_thesis_map"
    return "not_allowed_for_thesis_facing_claims"


def _source_review_next_action(priority_band: str, readiness: str) -> str:
    if priority_band == "priority_1_method_foundation_review":
        return "Review method sections first and record page or section notes before final methodology citation."
    if priority_band == "priority_2_core_interpretation_review":
        return "Review evidence-specific passages and confirm allowed wording before final result discussion."
    if priority_band == "priority_3_context_or_appendix_review":
        return "Review only after H1-H3 method and interpretation sources are cleared."
    if priority_band == "format_and_page_note_check":
        return "Check citation formatting and record final page or section support."
    if priority_band == "blocked_or_future_work_only":
        return "Do not use for thesis-facing claims unless metadata and status are re-reviewed."
    if readiness == "not_currently_needed":
        return "No action unless this source becomes mapped to a thesis claim."
    return "Assign a recognised source status before thesis use."


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _require_source_ids(literature: pd.DataFrame, source_ids: set[str]) -> None:
    known = set(literature["source_id"].astype(str))
    missing = sorted(source_ids.difference(known))
    if missing:
        raise ValueError(f"Literature index missing required source_id values: {missing}")


def _require_artifacts(repo_root: Path, paths: set[str]) -> None:
    missing = sorted(path for path in paths if not (repo_root / path).exists())
    if missing:
        raise FileNotFoundError(f"Required thesis consolidation artifacts are missing: {missing}")


def _required_file(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Required thesis consolidation source artifact not found: {path}")
    return path


def _resolve_under(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


def _split_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def _markdown_table(frame: pd.DataFrame) -> str:
    columns = [str(column) for column in frame.columns]
    header = "| " + " | ".join(_escape_markdown_cell(column) for column in columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = []
    for record in frame.to_dict(orient="records"):
        rows.append(
            "| "
            + " | ".join(_escape_markdown_cell(record.get(column, "")) for column in columns)
            + " |"
        )
    return "\n".join([header, separator, *rows])


def _escape_markdown_cell(value: object) -> str:
    text = str(value).replace("\n", " ").strip()
    return text.replace("|", "\\|")


def _bool_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series
    return series.astype(str).str.strip().str.lower().map(
        {"true": True, "false": False, "1": True, "0": False}
    ).fillna(False)


if __name__ == "__main__":
    raise SystemExit(main())
