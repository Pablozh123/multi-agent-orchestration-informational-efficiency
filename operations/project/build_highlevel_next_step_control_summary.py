"""Build a high-level next-step control summary for thesis consolidation."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pandas as pd


DEFAULT_REPO_ROOT = Path(".")
DEFAULT_RESULTS_DIR = Path("data/results")
DEFAULT_DOCS_DIR = Path("docs/project")

SUMMARY_OUTPUT = "thesis_highlevel_next_step_control_summary.csv"
SUMMARY_DOC_OUTPUT = "THESIS_HIGHLEVEL_NEXT_STEP_CONTROL_SUMMARY.md"

SUMMARY_COLUMNS: tuple[str, ...] = (
    "control_id",
    "control_order",
    "control_area",
    "authoritative_inputs",
    "key_counts_de",
    "current_state_de",
    "next_action_de",
    "final_blocker_de",
    "agent_boundary_de",
    "ready_for_bounded_draft",
    "ready_for_final_release",
)

COVERAGE_REQUIRED_COLUMNS: tuple[str, ...] = (
    "evidence_id",
    "thesis_area",
    "item_type",
    "thesis_readiness",
    "source_id",
    "source_known_in_literature_index",
    "primary_artifact_exists",
    "limitation_present",
    "coverage_status",
)

RESULT_PACKAGE_REQUIRED_COLUMNS: tuple[str, ...] = (
    "package_id",
    "package_type",
    "thesis_section",
    "include_in_core_package",
    "primary_artifact_exists",
    "caption_present",
    "source_note_present",
    "limitation_note_present",
    "package_traceability_status",
)

CURATED_PACKAGE_REQUIRED_COLUMNS: tuple[str, ...] = (
    "package_id",
    "package_type",
    "include_in_core_package",
    "recommended_placement",
    "thesis_readiness",
)

BATCH_PLAN_REQUIRED_COLUMNS: tuple[str, ...] = (
    "batch_plan_id",
    "source_review_rows",
    "unique_sources",
    "method_rows",
    "interpretation_rows",
    "pending_citation_rows",
    "final_ready_rows",
    "source_status_change_rows",
    "ready_for_manual_execution",
    "ready_for_final_release",
)

CORE_SECTIONS_REQUIRED_COLUMNS: tuple[str, ...] = (
    "section_id",
    "hypothesis",
    "method_evidence_ids",
    "interpretation_evidence_ids",
    "deterministic_artifacts",
    "selected_tables",
    "selected_figures",
    "source_review_gate_de",
)

FINAL_GATE_REQUIRED_COLUMNS: tuple[str, ...] = (
    "gate_area",
    "current_status",
    "draft_use_allowed",
    "final_submission_ready",
    "evidence_count",
    "blocking_count",
    "required_next_action_de",
)

AGENT_SAFETY_REQUIRED_COLUMNS: tuple[str, ...] = (
    "safety_case_id",
    "future_agent_scope",
    "current_status",
)

AGENT_UPGRADE_REQUIRED_COLUMNS: tuple[str, ...] = (
    "upgrade_id",
    "future_assistance_role",
    "current_status",
)

NEXT_WORK_REQUIRED_COLUMNS: tuple[str, ...] = (
    "workstream_id",
    "priority_order",
    "workstream",
    "next_action",
    "guardrail",
)


@dataclass(frozen=True)
class HighlevelNextStepControlSummaryResult:
    """Generated high-level next-step control summary paths and counts."""

    summary_path: Path
    docs_path: Path
    summary_rows: int
    thesis_facing_method_count: int
    thesis_facing_interpretation_count: int
    core_table_count: int
    core_figure_count: int
    final_release_ready_rows: int
    active_runtime_agent_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "summary_path": str(self.summary_path),
            "docs_path": str(self.docs_path),
            "summary_rows": self.summary_rows,
            "thesis_facing_method_count": self.thesis_facing_method_count,
            "thesis_facing_interpretation_count": self.thesis_facing_interpretation_count,
            "core_table_count": self.core_table_count,
            "core_figure_count": self.core_figure_count,
            "final_release_ready_rows": self.final_release_ready_rows,
            "active_runtime_agent_rows": self.active_runtime_agent_rows,
        }


def generate_highlevel_next_step_control_summary(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> HighlevelNextStepControlSummaryResult:
    """Generate the high-level next-step control summary CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    coverage = _read_csv(results_dir / "thesis_method_interpretation_source_coverage.csv")
    result_package = _read_csv(results_dir / "thesis_result_package_traceability.csv")
    curated_package = _read_csv(results_dir / "thesis_curated_result_package.csv")
    batch_plan = _read_csv(results_dir / "thesis_source_review_batch_execution_plan.csv")
    core_sections = _read_csv(results_dir / "thesis_h1_h2_h3_core_sections.csv")
    final_gate = _read_csv(results_dir / "thesis_final_gate_board.csv")
    agent_safety = _read_csv(results_dir / "thesis_agent_pipeline_safety_case.csv")
    agent_upgrade = _read_csv(results_dir / "thesis_agent_pipeline_upgrade_plan.csv")
    next_work = _read_csv(results_dir / "thesis_next_work_plan.csv")

    summary = build_highlevel_next_step_control_summary(
        coverage=coverage,
        result_package=result_package,
        curated_package=curated_package,
        batch_plan=batch_plan,
        core_sections=core_sections,
        final_gate=final_gate,
        agent_safety=agent_safety,
        agent_upgrade=agent_upgrade,
        next_work=next_work,
    )
    _validate_summary(
        summary=summary,
        coverage=coverage,
        result_package=result_package,
        curated_package=curated_package,
        batch_plan=batch_plan,
        core_sections=core_sections,
        final_gate=final_gate,
        agent_safety=agent_safety,
        agent_upgrade=agent_upgrade,
        next_work=next_work,
        repo_root=repo_root,
    )

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    summary_path = results_dir / SUMMARY_OUTPUT
    docs_path = docs_dir / SUMMARY_DOC_OUTPUT
    summary.to_csv(summary_path, index=False)
    docs_path.write_text(_render_summary_doc(summary), encoding="utf-8")

    context = _context(
        coverage=coverage,
        result_package=result_package,
        curated_package=curated_package,
        batch_plan=batch_plan,
        core_sections=core_sections,
        final_gate=final_gate,
        agent_safety=agent_safety,
        agent_upgrade=agent_upgrade,
        next_work=next_work,
    )
    return HighlevelNextStepControlSummaryResult(
        summary_path=summary_path,
        docs_path=docs_path,
        summary_rows=len(summary),
        thesis_facing_method_count=int(context["thesis_methods"]),
        thesis_facing_interpretation_count=int(context["thesis_interpretations"]),
        core_table_count=int(context["core_tables"]),
        core_figure_count=int(context["core_figures"]),
        final_release_ready_rows=int(summary["ready_for_final_release"].map(_bool_value).sum()),
        active_runtime_agent_rows=int(context["active_agent_rows"]),
    )


def build_highlevel_next_step_control_summary(
    *,
    coverage: pd.DataFrame,
    result_package: pd.DataFrame,
    curated_package: pd.DataFrame,
    batch_plan: pd.DataFrame,
    core_sections: pd.DataFrame,
    final_gate: pd.DataFrame,
    agent_safety: pd.DataFrame,
    agent_upgrade: pd.DataFrame,
    next_work: pd.DataFrame,
) -> pd.DataFrame:
    """Return the current thesis next-step summary as seven control rows."""

    context = _context(
        coverage=coverage,
        result_package=result_package,
        curated_package=curated_package,
        batch_plan=batch_plan,
        core_sections=core_sections,
        final_gate=final_gate,
        agent_safety=agent_safety,
        agent_upgrade=agent_upgrade,
        next_work=next_work,
    )
    rows = [
        _row(
            control_id="next_step_01_evidence_source_mapping",
            control_order=1,
            control_area="evidence_source_mapping",
            authoritative_inputs=(
                "data/results/thesis_method_interpretation_source_coverage.csv; "
                "data/results/thesis_method_interpretation_traceability.csv"
            ),
            key_counts_de=(
                f"{context['thesis_methods']} thesis-facing Methoden, "
                f"{context['thesis_interpretations']} thesis-facing Interpretationen, "
                f"{context['h1_h2_h3_source_links']} H1-H2-H3 Source-Links, "
                f"{context['total_source_links']} total Methode-/Interpretation-Source-Links, "
                f"{context['thesis_unique_sources']} eindeutige H1-H2-H3 Quellen, "
                f"{context['coverage_gaps']} Coverage-Gaps."
            ),
            current_state_de=(
                "Jede thesis-facing Methode und Interpretation ist an mindestens "
                "eine bekannte Quelle, ein deterministisches Primaerartefakt und "
                "eine sichtbare Limitation gebunden."
            ),
            next_action_de=(
                "Beim Schreiben keine Methode oder Interpretation ohne Evidence ID, "
                "Artefaktpfad und Source-Review-Gate uebernehmen."
            ),
            final_blocker_de=(
                "Finale Zitation bleibt blockiert, bis die 23 H1-H2-H3 Source-"
                "Links manuell mit Page-/Section-Note, Claim-Support, "
                "Blocked-Wording und Citation-Use entschieden sind."
            ),
            agent_boundary_de=(
                "Spaetere Agenten duerfen nur fehlende Mapping-Felder markieren; "
                "keine LLM-Kennzahlen und keine Quellenstatus-Hochstufung."
            ),
        ),
        _row(
            control_id="next_step_02_compact_result_package",
            control_order=2,
            control_area="compact_result_package",
            authoritative_inputs=(
                "data/results/thesis_curated_result_package.csv; "
                "data/results/thesis_result_package_traceability.csv; "
                "docs/research/THESIS_TABLE_FIGURE_CAPTIONS.md"
            ),
            key_counts_de=(
                f"{context['core_tables']} Kern-Tabellen, {context['core_figures']} "
                f"Kern-Figuren, {context['appendix_packages']} appendix/future-work "
                f"Packages, {context['package_gaps']} Package-Gaps."
            ),
            current_state_de=(
                "Das Resultatpaket ist klein genug fuer die BA: T1-T5 und F1-F4 "
                "statt Rohartefakt-Dumps; A1 bleibt Future Work/Appendix."
            ),
            next_action_de=(
                "Nur die kuratierten Tabellen/Figuren in die Kapitel einbauen; "
                "Caption, Source Note und Limitation je Package beibehalten."
            ),
            final_blocker_de=(
                "Finale Nummerierung, Layout-QA und finale Zitation bleiben offen."
            ),
            agent_boundary_de=(
                "Spaetere Agenten duerfen nur Caption-/Limitation-/Artefaktpfad-"
                "Checks machen; keine neuen Tabellen/Figuren ohne Map-Update."
            ),
        ),
        _row(
            control_id="next_step_03_manual_source_review_batches",
            control_order=3,
            control_area="manual_source_review_batches",
            authoritative_inputs=(
                "data/results/thesis_source_review_batch_execution_plan.csv; "
                "docs/project/THESIS_SOURCE_REVIEW_BATCH_EXECUTION_PLAN.md"
            ),
            key_counts_de=(
                f"{context['batch_rows']} Batch rows: H1 {context['h1_review_rows']}, "
                f"H2 {context['h2_review_rows']}, H3 {context['h3_review_rows']}, "
                f"TOTAL {context['total_review_rows']}; "
                f"{context['pending_citation_rows']} pending citation rows, "
                f"{context['final_ready_rows']} final-ready rows, "
                f"{context['source_status_change_rows']} source-status change rows."
            ),
            current_state_de=(
                "Die manuelle Review-Reihenfolge ist operationalisiert: erst H1, "
                "dann H2, dann H3, danach Rebuild und Finalgate."
            ),
            next_action_de=(
                "Mit H1 Batch starten und die erlaubten Ledger-Felder aus der "
                "Manual Source Review Update Checklist pflegen."
            ),
            final_blocker_de=(
                "Keine finale Zitation und keine Quellenstatus-Hochstufung, solange "
                "auch nur eine required row pending bleibt."
            ),
            agent_boundary_de=(
                "Keine Runtime-Agenten; spaetere Hilfe nur als missing-field/to-do "
                "Liste mit max 50 rows und llm_audit_log."
            ),
        ),
        _row(
            control_id="next_step_04_h1_h2_h3_writing",
            control_order=4,
            control_area="h1_h2_h3_writing",
            authoritative_inputs=(
                "data/results/thesis_h1_h2_h3_core_sections.csv; "
                "data/results/thesis_next_work_plan.csv"
            ),
            key_counts_de=(
                f"{context['core_sections']} Core Sections, Tabellen "
                f"{context['core_section_tables']}, Figuren {context['core_section_figures']}, "
                f"{context['next_work_rows']} Next-Work rows."
            ),
            current_state_de=(
                "H1-H2-H3 duerfen als bounded Draft geschrieben werden: H1 "
                "begrenzt, H2 daily event-window, H3 Timing-Diagnostik."
            ),
            next_action_de=(
                "Kapitel entlang der Core-Section-Zeilen schreiben und jeden "
                "Absatz an Evidence IDs, Artefakte, Tabelle/Figur und Limitation binden."
            ),
            final_blocker_de=(
                "Finale Kapitel bleiben durch Source Review, Wording Guard und "
                "Final-QA blockiert."
            ),
            agent_boundary_de=(
                "Evidence-to-prose-Agenten bleiben Future Work; kein Drafttext "
                "aus unlogged LLM-Interpretation im finalen Kern."
            ),
        ),
        _row(
            control_id="next_step_05_swiss_monitor_boundaries",
            control_order=5,
            control_area="swiss_monitor_boundaries",
            authoritative_inputs=(
                "data/results/thesis_final_gate_board.csv; "
                "data/results/swiss_referendum_10mio_running_status.json; "
                "data/results/monitor_anomaly_review_summary.csv"
            ),
            key_counts_de=(
                f"Swiss Gate Status {context['swiss_gate_status']}, Swiss Snapshot "
                f"Rows {context['swiss_snapshot_rows']}, Monitor Gate Status "
                f"{context['monitor_gate_status']}."
            ),
            current_state_de=(
                "Swiss bleibt beschreibender Side Track bis zum offiziellen Resultat; "
                "Monitor bleibt Appendix/Prototype pending human review."
            ),
            next_action_de=(
                "Swiss nach offiziellem Resultat neu mappen; Monitor nur als "
                "Review-Workflow oder Appendix-Grenze erwaehnen."
            ),
            final_blocker_de=(
                "Keine finale Swiss-Effizienz-, Mispricing-, Tradeability- oder "
                "Monitor-Effizienzbehauptung vor Gate-Schluss."
            ),
            agent_boundary_de=(
                "Keine Wallet-Adressen, keine Trading-Claims, keine "
                "Profitabilitaetsclaims und keine Runtime-Agenten."
            ),
        ),
        _row(
            control_id="next_step_06_future_agent_pipeline",
            control_order=6,
            control_area="future_agent_pipeline",
            authoritative_inputs=(
                "data/results/thesis_agent_pipeline_safety_case.csv; "
                "data/results/thesis_agent_pipeline_upgrade_plan.csv"
            ),
            key_counts_de=(
                f"{context['safety_rows']} safety rows, {context['agent_upgrade_rows']} "
                f"upgrade rows, {context['documentation_only_rows']} documentation-only rows, "
                f"{context['deferred_rows']} deferred rows, "
                f"{context['active_agent_rows']} active runtime rows."
            ),
            current_state_de=(
                "Agentenideen duerfen als Pipeline-Ausblick beschrieben werden, "
                "aber nicht als Thesis-Runtime umgesetzt werden."
            ),
            next_action_de=(
                "Agentenabschnitt erst nach Source-Review-Pfad als Future Work "
                "schreiben: Source Review Helper, Evidence Drafting, Wording, "
                "Table/Figure QA, Advisor Summary, Monitor Appendix, bounded access."
            ),
            final_blocker_de=(
                "Keine Aktivierung ohne separates Goal, Tests, bounded inputs, "
                "Proof-Artefakt und llm_audit_log."
            ),
            agent_boundary_de=(
                "0 active runtime rows; keine Runtime-Agenten, kein MCP, kein "
                "Model Routing, keine LLM-Metriken, keine Rohdaten-Prompts, "
                "max 50 rows."
            ),
        ),
        _row(
            control_id="next_step_07_final_qa_and_control",
            control_order=7,
            control_area="final_qa_and_control",
            authoritative_inputs="data/results/thesis_final_gate_board.csv; STATUS.md; docs/project/WORK_LOG.md",
            key_counts_de=(
                f"{context['final_gate_rows']} Final-Gate rows, "
                f"{context['final_ready_gate_rows']} final-ready gate rows, "
                f"{context['final_not_ready_gate_rows']} final-not-ready gate rows."
            ),
            current_state_de=(
                "Bounded Draft ist erlaubt, aber finale BA-Abgabe ist nicht "
                "freigegeben."
            ),
            next_action_de=(
                "Nach jedem Slice update_status, WORK_LOG, review_check, "
                "commit_plan und Diff-Stat ausfuehren."
            ),
            final_blocker_de=(
                "Source Review, Swiss Resultat-Mapping, DOCX-Render-QA und finale "
                "Projektchecks muessen vor finaler Abgabebereitschaft geschlossen sein."
            ),
            agent_boundary_de=(
                "Projektsteuerung bleibt deterministisch; LLMs duerfen keine "
                "Metriken berechnen und muessen spaeter in llm_audit_log erfasst werden."
            ),
        ),
    ]
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_highlevel_next_step_control_summary(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _context(
    *,
    coverage: pd.DataFrame,
    result_package: pd.DataFrame,
    curated_package: pd.DataFrame,
    batch_plan: pd.DataFrame,
    core_sections: pd.DataFrame,
    final_gate: pd.DataFrame,
    agent_safety: pd.DataFrame,
    agent_upgrade: pd.DataFrame,
    next_work: pd.DataFrame,
) -> dict[str, int | str]:
    _require_columns(coverage, COVERAGE_REQUIRED_COLUMNS, "method interpretation source coverage")
    _require_columns(result_package, RESULT_PACKAGE_REQUIRED_COLUMNS, "result package traceability")
    _require_columns(curated_package, CURATED_PACKAGE_REQUIRED_COLUMNS, "curated result package")
    _require_columns(batch_plan, BATCH_PLAN_REQUIRED_COLUMNS, "source review batch execution plan")
    _require_columns(core_sections, CORE_SECTIONS_REQUIRED_COLUMNS, "H1-H2-H3 core sections")
    _require_columns(final_gate, FINAL_GATE_REQUIRED_COLUMNS, "final gate board")
    _require_columns(agent_safety, AGENT_SAFETY_REQUIRED_COLUMNS, "agent safety case")
    _require_columns(agent_upgrade, AGENT_UPGRADE_REQUIRED_COLUMNS, "agent upgrade plan")
    _require_columns(next_work, NEXT_WORK_REQUIRED_COLUMNS, "next work plan")

    thesis_coverage = coverage[coverage["thesis_readiness"].astype(str) == "thesis_facing_ready"]
    coverage_gaps = int(
        thesis_coverage["coverage_status"].astype(str).str.contains("gap", case=False, na=False).sum()
    )
    source_unknown = int((~thesis_coverage["source_known_in_literature_index"].map(_bool_value)).sum())
    artifacts_missing = int((~thesis_coverage["primary_artifact_exists"].map(_bool_value)).sum())
    limitations_missing = int((~thesis_coverage["limitation_present"].map(_bool_value)).sum())
    if coverage_gaps or source_unknown or artifacts_missing or limitations_missing:
        raise ValueError("High-level summary requires complete thesis-facing source/artifact/limitation coverage.")

    thesis_methods = int(
        thesis_coverage[thesis_coverage["item_type"].astype(str) == "method"]["evidence_id"].nunique()
    )
    thesis_interpretations = int(
        thesis_coverage[
            thesis_coverage["item_type"].astype(str) == "interpretation"
        ]["evidence_id"].nunique()
    )
    h1_h2_h3_source_links = int(len(thesis_coverage))
    thesis_unique_sources = int(thesis_coverage["source_id"].nunique())

    core_trace = result_package[result_package["include_in_core_package"].map(_bool_value)]
    core_tables = int((core_trace["package_type"].astype(str) == "table").sum())
    core_figures = int((core_trace["package_type"].astype(str) == "figure").sum())
    package_gaps = int(
        core_trace["package_traceability_status"].astype(str).str.contains("gap", case=False, na=False).sum()
    )
    package_missing = int(
        (
            ~core_trace["primary_artifact_exists"].map(_bool_value)
            | ~core_trace["caption_present"].map(_bool_value)
            | ~core_trace["source_note_present"].map(_bool_value)
            | ~core_trace["limitation_note_present"].map(_bool_value)
        ).sum()
    )
    if package_gaps or package_missing:
        raise ValueError("High-level summary requires complete core table/figure traceability.")

    curated_core = curated_package[curated_package["include_in_core_package"].map(_bool_value)]
    appendix_packages = int((~curated_package["include_in_core_package"].map(_bool_value)).sum())
    if set(curated_core["package_id"].astype(str)) != set(core_trace["package_id"].astype(str)):
        raise ValueError("Curated package and result-package traceability core IDs must match.")

    total_batch = _row_by_id(batch_plan, "batch_plan_id", "batch_plan_total_rebuild_gate")
    batch_rows = int(len(batch_plan))
    if batch_rows != 4:
        raise ValueError("High-level summary expects four source-review batch rows.")
    if batch_plan["ready_for_final_release"].map(_bool_value).any():
        raise ValueError("High-level summary must not mark source-review batches final-release-ready.")

    core_section_tables = _unique_join(core_sections["selected_tables"])
    core_section_figures = _unique_join(core_sections["selected_figures"])
    if len(core_sections) != 3:
        raise ValueError("High-level summary expects three H1-H2-H3 core sections.")

    gates = final_gate.set_index("gate_area").to_dict(orient="index")
    source_gate = gates.get("source_review", {})
    swiss_gate = gates.get("swiss_result_gate", {})
    monitor_gate = gates.get("monitor_appendix", {})
    docx_gate = gates.get("docx_render_qa", {})
    for gate_area, gate in (
        ("source_review", source_gate),
        ("swiss_result_gate", swiss_gate),
        ("docx_render_qa", docx_gate),
    ):
        if not gate:
            raise ValueError(f"High-level summary missing final gate row: {gate_area}")
        if _bool_value(gate.get("final_submission_ready")):
            raise ValueError(f"High-level summary requires {gate_area} to remain final-blocked.")

    active_agent_rows = int(
        agent_upgrade["current_status"].astype(str).str.contains("active", case=False, na=False).sum()
    )
    active_safety_rows = int(
        agent_safety["current_status"].astype(str).str.contains("active", case=False, na=False).sum()
    )
    if active_agent_rows or active_safety_rows:
        raise ValueError("High-level summary must not include active runtime agent rows.")
    documentation_only_rows = int(
        agent_safety["current_status"].astype(str).str.contains("documentation", case=False, na=False).sum()
    )
    deferred_rows = int(
        agent_safety["current_status"].astype(str).str.contains("deferred", case=False, na=False).sum()
    )

    final_ready_gate_rows = int(final_gate["final_submission_ready"].map(_bool_value).sum())
    final_gate_rows = int(len(final_gate))

    return {
        "thesis_methods": thesis_methods,
        "thesis_interpretations": thesis_interpretations,
        "h1_h2_h3_source_links": h1_h2_h3_source_links,
        "total_source_links": int(len(coverage)),
        "thesis_unique_sources": thesis_unique_sources,
        "coverage_gaps": coverage_gaps,
        "core_tables": core_tables,
        "core_figures": core_figures,
        "appendix_packages": appendix_packages,
        "package_gaps": package_gaps,
        "batch_rows": batch_rows,
        "h1_review_rows": int(_row_by_id(batch_plan, "batch_plan_id", "batch_plan_h1")["source_review_rows"]),
        "h2_review_rows": int(_row_by_id(batch_plan, "batch_plan_id", "batch_plan_h2")["source_review_rows"]),
        "h3_review_rows": int(_row_by_id(batch_plan, "batch_plan_id", "batch_plan_h3")["source_review_rows"]),
        "total_review_rows": int(total_batch["source_review_rows"]),
        "pending_citation_rows": int(total_batch["pending_citation_rows"]),
        "final_ready_rows": int(total_batch["final_ready_rows"]),
        "source_status_change_rows": int(total_batch["source_status_change_rows"]),
        "core_sections": int(len(core_sections)),
        "core_section_tables": core_section_tables,
        "core_section_figures": core_section_figures,
        "next_work_rows": int(len(next_work)),
        "swiss_gate_status": str(swiss_gate.get("current_status", "unknown")),
        "swiss_snapshot_rows": int(swiss_gate.get("evidence_count", 0)),
        "monitor_gate_status": str(monitor_gate.get("current_status", "unknown")),
        "safety_rows": int(len(agent_safety)),
        "agent_upgrade_rows": int(len(agent_upgrade)),
        "documentation_only_rows": documentation_only_rows,
        "deferred_rows": deferred_rows,
        "active_agent_rows": active_agent_rows + active_safety_rows,
        "final_gate_rows": final_gate_rows,
        "final_ready_gate_rows": final_ready_gate_rows,
        "final_not_ready_gate_rows": final_gate_rows - final_ready_gate_rows,
    }


def _validate_summary(
    *,
    summary: pd.DataFrame,
    coverage: pd.DataFrame,
    result_package: pd.DataFrame,
    curated_package: pd.DataFrame,
    batch_plan: pd.DataFrame,
    core_sections: pd.DataFrame,
    final_gate: pd.DataFrame,
    agent_safety: pd.DataFrame,
    agent_upgrade: pd.DataFrame,
    next_work: pd.DataFrame,
    repo_root: Path,
) -> None:
    _require_columns(summary, SUMMARY_COLUMNS, "high-level next-step control summary")
    context = _context(
        coverage=coverage,
        result_package=result_package,
        curated_package=curated_package,
        batch_plan=batch_plan,
        core_sections=core_sections,
        final_gate=final_gate,
        agent_safety=agent_safety,
        agent_upgrade=agent_upgrade,
        next_work=next_work,
    )
    if len(summary) != 7:
        raise ValueError("High-level next-step control summary must contain seven rows.")
    if summary["control_order"].astype(int).tolist() != list(range(1, 8)):
        raise ValueError("High-level next-step control summary must be ordered 1..7.")
    if summary["control_id"].duplicated().any():
        raise ValueError("High-level next-step control summary contains duplicate control_id values.")
    if not summary["ready_for_bounded_draft"].map(_bool_value).all():
        raise ValueError("High-level next-step control summary must allow bounded draft progress.")
    if summary["ready_for_final_release"].map(_bool_value).any():
        raise ValueError("High-level next-step control summary must not mark final release ready.")
    for artifacts in summary["authoritative_inputs"].astype(str):
        for artifact in _split_semicolon(artifacts):
            if not (repo_root / artifact).exists():
                raise FileNotFoundError(f"High-level summary input artifact missing: {artifact}")
    joined = "\n".join(summary.fillna("").astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("High-level next-step control summary must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "4 thesis-facing methoden",
        "4 thesis-facing interpretationen",
        "23 h1-h2-h3 source-links",
        "31 total methode-/interpretation-source-links",
        "5 kern-tabellen",
        "4 kern-figuren",
        "4 batch rows",
        "23 pending citation rows",
        "7 safety rows",
        "0 active runtime rows",
        "max 50 rows",
        "llm_audit_log",
        "keine runtime-agenten",
        "keine finale zitation",
        "swiss",
        "docx",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError(
            "High-level next-step control summary missing required terms: " + ", ".join(missing)
        )
    if int(context["thesis_methods"]) != 4 or int(context["thesis_interpretations"]) != 4:
        raise ValueError("High-level summary expects 4 thesis-facing methods and interpretations.")
    if int(context["h1_h2_h3_source_links"]) != 23 or int(context["total_source_links"]) != 31:
        raise ValueError("High-level summary expects 23 H1-H2-H3 links and 31 total links.")
    if int(context["core_tables"]) != 5 or int(context["core_figures"]) != 4:
        raise ValueError("High-level summary expects 5 core tables and 4 core figures.")
    if int(context["pending_citation_rows"]) != 23 or int(context["final_ready_rows"]) != 0:
        raise ValueError("High-level summary expects 23 pending and 0 final-ready citation rows.")
    if int(context["active_agent_rows"]) != 0:
        raise ValueError("High-level summary expects 0 active runtime agent rows.")


def _render_summary_doc(summary: pd.DataFrame) -> str:
    display = summary[
        [
            "control_order",
            "control_area",
            "key_counts_de",
            "current_state_de",
            "next_action_de",
            "final_blocker_de",
        ]
    ]
    return (
        "# Highlevel Next-Step Control Summary\n\n"
        "Diese Summary zeigt den naechsten Projektpfad aus den bestehenden "
        "deterministischen Kontrollartefakten. Sie ersetzt keine manuelle "
        "Source Review, liest keine Quelleninhalte, erzeugt keine neuen "
        "Kennzahlen und aktiviert keine Runtime-Agenten.\n\n"
        "## Counts\n\n"
        f"- Summary rows: {len(summary)}\n"
        f"- Bounded-draft ready rows: {int(summary['ready_for_bounded_draft'].map(_bool_value).sum())}\n"
        f"- Final-release ready rows: {int(summary['ready_for_final_release'].map(_bool_value).sum())}\n\n"
        "## Control Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze diese Reihenfolge als High-Level-Navigation: zuerst "
        "Evidence-/Source-Mapping stabil halten, dann nur das kompakte "
        "Tabellen-/Figurenpaket integrieren, danach Source Review in den "
        "Batches H1, H2, H3 und TOTAL abarbeiten, H1-H2-H3 bounded schreiben, "
        "Swiss/Monitor nur mit Gates fuehren, Agenten nur als Future Work "
        "beschreiben und vor jedem Stop Projektchecks ausfuehren. Keine finale "
        "Zitation, keine Quellenstatus-Hochstufung, keine Rohartefakt-Dumps, "
        "keine Runtime-Agenten, kein MCP, kein Model Routing, keine "
        "LLM-Metriken, max 50 rows und `llm_audit_log` fuer spaetere "
        "Agentenhilfe.\n"
    )


def _row(
    *,
    control_id: str,
    control_order: int,
    control_area: str,
    authoritative_inputs: str,
    key_counts_de: str,
    current_state_de: str,
    next_action_de: str,
    final_blocker_de: str,
    agent_boundary_de: str,
) -> dict[str, object]:
    return {
        "control_id": control_id,
        "control_order": control_order,
        "control_area": control_area,
        "authoritative_inputs": authoritative_inputs,
        "key_counts_de": key_counts_de,
        "current_state_de": current_state_de,
        "next_action_de": next_action_de,
        "final_blocker_de": final_blocker_de,
        "agent_boundary_de": agent_boundary_de,
        "ready_for_bounded_draft": True,
        "ready_for_final_release": False,
    }


def _row_by_id(frame: pd.DataFrame, column: str, value: str) -> pd.Series:
    rows = frame.loc[frame[column].astype(str) == value]
    if len(rows) != 1:
        raise ValueError(f"Expected one row where {column} == {value}.")
    return rows.iloc[0]


def _unique_join(values: pd.Series) -> str:
    return ", ".join(sorted({_clean(value) for value in values if _clean(value)}))


def _split_semicolon(value: str) -> list[str]:
    if value.lower() == "nan":
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required high-level summary input missing: {path}")
    return pd.read_csv(path)


def _resolve_under(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "ja", "y"}


def _clean(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


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


if __name__ == "__main__":
    raise SystemExit(main())
