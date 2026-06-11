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
        "data/results/thesis_consolidation_metadata.json",
        "docs/research/THESIS_CONSOLIDATION.md",
    }
)

EVIDENCE_MAP_OUTPUT = "thesis_evidence_map.csv"
EVIDENCE_MAP_MD_OUTPUT = "thesis_evidence_map.md"
CORE_RESULTS_OUTPUT = "thesis_core_results_table.csv"
CURATED_PACKAGE_OUTPUT = "thesis_curated_result_package.csv"
METADATA_OUTPUT = "thesis_consolidation_metadata.json"
DOC_OUTPUT = "THESIS_CONSOLIDATION.md"

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


@dataclass(frozen=True)
class ThesisConsolidationResult:
    """Generated thesis consolidation artifact paths and counts."""

    evidence_map_path: Path
    evidence_map_md_path: Path
    core_results_path: Path
    curated_package_path: Path
    metadata_path: Path
    docs_path: Path
    evidence_rows: int
    core_result_rows: int
    package_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "evidence_map_path": str(self.evidence_map_path),
            "evidence_map_md_path": str(self.evidence_map_md_path),
            "core_results_path": str(self.core_results_path),
            "curated_package_path": str(self.curated_package_path),
            "metadata_path": str(self.metadata_path),
            "docs_path": str(self.docs_path),
            "evidence_rows": self.evidence_rows,
            "core_result_rows": self.core_result_rows,
            "package_rows": self.package_rows,
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

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    evidence_map_path = results_dir / EVIDENCE_MAP_OUTPUT
    evidence_map_md_path = results_dir / EVIDENCE_MAP_MD_OUTPUT
    core_results_path = results_dir / CORE_RESULTS_OUTPUT
    curated_package_path = results_dir / CURATED_PACKAGE_OUTPUT
    metadata_path = results_dir / METADATA_OUTPUT
    docs_path = docs_dir / DOC_OUTPUT

    evidence_map.to_csv(evidence_map_path, index=False)
    core_results.to_csv(core_results_path, index=False)
    curated_package.to_csv(curated_package_path, index=False)
    evidence_map_md_path.write_text(
        _render_evidence_markdown(evidence_map),
        encoding="utf-8",
    )

    metadata = _build_metadata(
        evidence_map=evidence_map,
        core_results=core_results,
        curated_package=curated_package,
    )
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    docs_path.write_text(
        _render_consolidation_doc(
            evidence_map=evidence_map,
            core_results=core_results,
            curated_package=curated_package,
            metadata=metadata,
        ),
        encoding="utf-8",
    )

    return ThesisConsolidationResult(
        evidence_map_path=evidence_map_path,
        evidence_map_md_path=evidence_map_md_path,
        core_results_path=core_results_path,
        curated_package_path=curated_package_path,
        metadata_path=metadata_path,
        docs_path=docs_path,
        evidence_rows=len(evidence_map),
        core_result_rows=len(core_results),
        package_rows=len(curated_package),
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
            "core_table_count": int((core["package_type"] == "table").sum()),
            "core_figure_count": int((core["package_type"] == "figure").sum()),
            "max_core_tables": 5,
            "max_core_figures": 4,
        },
        "readiness_counts": {
            str(key): int(value)
            for key, value in evidence_map["thesis_readiness"].value_counts().sort_index().items()
        },
        "guardrails": {
            "every_method_and_interpretation_has_artifact": True,
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
    metadata: dict[str, object],
) -> str:
    core = curated_package[curated_package["include_in_core_package"].astype(bool)].copy()
    tables = core[core["package_type"] == "table"]
    figures = core[core["package_type"] == "figure"]
    agent_row = evidence_map[evidence_map["evidence_id"] == "future_agent_pipeline_guarded"].iloc[0]

    return (
        "# Thesis Consolidation\n\n"
        "## Purpose\n\n"
        "This document is the high-level consolidation layer for the bachelor thesis. "
        "It reduces the many generated artifacts to a small thesis-ready package and "
        "keeps every central method and interpretation tied to deterministic evidence.\n\n"
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
        "1. Evidence-reader agent over `thesis_evidence_map.csv` and curated summaries only.\n"
        "2. Citation-check assistant that flags missing source status without writing thesis claims.\n"
        "3. Interpretation-consistency assistant that compares draft prose against allowed and blocked wording.\n"
        "4. Human-review assistant for monitor packets after manual source checks exist.\n"
        "5. Only after audit logging exists: bounded MCP summary tools for read-only reviewed artifacts.\n\n"
        "No runtime agent, MCP implementation, model routing, autonomous collector, or trading path "
        "is part of the current consolidation step.\n\n"
        "## Generated Artifact Counts\n\n"
        f"- Evidence rows: {metadata['outputs']['evidence_rows']}\n"
        f"- Core result rows: {metadata['outputs']['core_result_rows']}\n"
        f"- Core tables: {metadata['outputs']['core_table_count']}\n"
        f"- Core figures: {metadata['outputs']['core_figure_count']}\n"
    )


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
