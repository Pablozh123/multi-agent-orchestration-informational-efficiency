"""Build a high-level BA writing handoff without review access."""

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

HANDOFF_OUTPUT = "thesis_highlevel_thesis_writing_handoff.csv"
HANDOFF_DOC_OUTPUT = "THESIS_HIGHLEVEL_THESIS_WRITING_HANDOFF.md"

HANDOFF_COLUMNS: tuple[str, ...] = (
    "handoff_id",
    "handoff_order",
    "handoff_area",
    "authoritative_inputs",
    "allowed_ba_action_de",
    "required_binding_de",
    "compact_output_de",
    "open_gate_de",
    "forbidden_action_de",
    "next_human_action_de",
    "ready_for_bounded_draft",
    "ready_for_final_submission",
)

HIGHLEVEL_REQUIRED_COLUMNS: tuple[str, ...] = (
    "control_id",
    "control_order",
    "control_area",
    "authoritative_inputs",
    "ready_for_bounded_draft",
    "ready_for_final_release",
)

CORE_SECTION_REQUIRED_COLUMNS: tuple[str, ...] = (
    "section_id",
    "hypothesis",
    "chapter_title_de",
    "method_evidence_ids",
    "interpretation_evidence_ids",
    "literature_source_ids",
    "deterministic_artifacts",
    "selected_tables",
    "selected_figures",
    "thesis_ready_result_de",
    "bounded_interpretation_de",
    "mandatory_limitation_de",
    "source_review_gate_de",
)

BRIDGE_REQUIRED_COLUMNS: tuple[str, ...] = (
    "thesis_area",
    "worksheet_rows",
    "method_rows",
    "interpretation_rows",
    "unique_sources",
    "method_interpretation_source_artifact_gap_rows",
    "pending_citation_rows",
    "final_release_ready_rows",
    "drafting_steps",
    "selected_tables",
    "selected_figures",
    "source_artifact_rule_de",
    "writing_bridge_action_de",
    "final_blocker_de",
    "future_agent_boundary_de",
    "ready_for_bounded_drafting",
    "ready_for_final_release",
)

DRAFTING_PASS_REQUIRED_COLUMNS: tuple[str, ...] = (
    "drafting_pass_id",
    "thesis_area",
    "draft_sequence_order",
    "ready_for_bounded_draft",
    "ready_for_final_submission",
    "draft_status",
)

CURATED_PACKAGE_REQUIRED_COLUMNS: tuple[str, ...] = (
    "package_id",
    "package_type",
    "include_in_core_package",
    "recommended_placement",
    "thesis_readiness",
)

FINAL_GATE_REQUIRED_COLUMNS: tuple[str, ...] = (
    "gate_area",
    "current_status",
    "draft_use_allowed",
    "final_submission_ready",
    "evidence_count",
    "blocking_count",
)

AGENT_UPGRADE_REQUIRED_COLUMNS: tuple[str, ...] = (
    "upgrade_id",
    "future_assistance_role",
    "current_status",
)

CORE_AREAS: tuple[str, ...] = ("H1", "H2", "H3")


@dataclass(frozen=True)
class HighlevelThesisWritingHandoffResult:
    """Generated high-level thesis writing handoff paths and counts."""

    handoff_path: Path
    docs_path: Path
    handoff_rows: int
    bounded_draft_rows: int
    final_submission_ready_rows: int
    core_table_count: int
    core_figure_count: int
    active_runtime_agent_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "handoff_path": str(self.handoff_path),
            "docs_path": str(self.docs_path),
            "handoff_rows": self.handoff_rows,
            "bounded_draft_rows": self.bounded_draft_rows,
            "final_submission_ready_rows": self.final_submission_ready_rows,
            "core_table_count": self.core_table_count,
            "core_figure_count": self.core_figure_count,
            "active_runtime_agent_rows": self.active_runtime_agent_rows,
        }


def generate_highlevel_thesis_writing_handoff(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> HighlevelThesisWritingHandoffResult:
    """Generate the high-level thesis writing handoff CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    highlevel = _read_csv(results_dir / "thesis_highlevel_next_step_control_summary.csv")
    core_sections = _read_csv(results_dir / "thesis_h1_h2_h3_core_sections.csv")
    bridge = _read_csv(results_dir / "thesis_h1_h2_h3_worksheet_drafting_bridge.csv")
    drafting_pass = _read_csv(
        results_dir / "thesis_h1_h2_h3_source_gated_thesis_drafting_pass.csv"
    )
    curated_package = _read_csv(results_dir / "thesis_curated_result_package.csv")
    final_gate = _read_csv(results_dir / "thesis_final_gate_board.csv")
    agent_upgrade = _read_csv(results_dir / "thesis_agent_pipeline_upgrade_plan.csv")

    handoff = build_highlevel_thesis_writing_handoff(
        highlevel=highlevel,
        core_sections=core_sections,
        bridge=bridge,
        drafting_pass=drafting_pass,
        curated_package=curated_package,
        final_gate=final_gate,
        agent_upgrade=agent_upgrade,
    )
    _validate_handoff(
        handoff=handoff,
        highlevel=highlevel,
        core_sections=core_sections,
        bridge=bridge,
        drafting_pass=drafting_pass,
        curated_package=curated_package,
        final_gate=final_gate,
        agent_upgrade=agent_upgrade,
        repo_root=repo_root,
    )

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    handoff_path = results_dir / HANDOFF_OUTPUT
    docs_path = docs_dir / HANDOFF_DOC_OUTPUT
    handoff.to_csv(handoff_path, index=False)
    docs_path.write_text(_render_handoff_doc(handoff), encoding="utf-8")

    context = _context(
        highlevel=highlevel,
        core_sections=core_sections,
        bridge=bridge,
        drafting_pass=drafting_pass,
        curated_package=curated_package,
        final_gate=final_gate,
        agent_upgrade=agent_upgrade,
        repo_root=repo_root,
    )
    return HighlevelThesisWritingHandoffResult(
        handoff_path=handoff_path,
        docs_path=docs_path,
        handoff_rows=len(handoff),
        bounded_draft_rows=int(handoff["ready_for_bounded_draft"].map(_bool_value).sum()),
        final_submission_ready_rows=int(
            handoff["ready_for_final_submission"].map(_bool_value).sum()
        ),
        core_table_count=int(context["core_table_count"]),
        core_figure_count=int(context["core_figure_count"]),
        active_runtime_agent_rows=int(context["active_agent_rows"]),
    )


def build_highlevel_thesis_writing_handoff(
    *,
    highlevel: pd.DataFrame,
    core_sections: pd.DataFrame,
    bridge: pd.DataFrame,
    drafting_pass: pd.DataFrame,
    curated_package: pd.DataFrame,
    final_gate: pd.DataFrame,
    agent_upgrade: pd.DataFrame,
) -> pd.DataFrame:
    """Return the high-level handoff rows for BA writing without review access."""

    context = _context(
        highlevel=highlevel,
        core_sections=core_sections,
        bridge=bridge,
        drafting_pass=drafting_pass,
        curated_package=curated_package,
        final_gate=final_gate,
        agent_upgrade=agent_upgrade,
        repo_root=None,
    )
    core_by_area = core_sections.set_index("hypothesis").to_dict(orient="index")
    bridge_by_area = bridge.set_index("thesis_area").to_dict(orient="index")
    rows = [
        _handoff_row(
            handoff_id="writing_handoff_01_project_frame",
            handoff_order=1,
            handoff_area="project_frame_without_review_access",
            authoritative_inputs=(
                "data/results/thesis_highlevel_next_step_control_summary.csv; "
                "data/results/thesis_h1_h2_h3_worksheet_drafting_bridge.csv; "
                "data/results/thesis_final_gate_board.csv"
            ),
            allowed_ba_action_de=(
                "Review-Access bleibt pausiert; jetzt ist nur bounded BA-Schreiben "
                "erlaubt. Der empirische Kern wird aus H1, H2 und H3 aufgebaut, "
                "waehrend Source Review, Swiss Resultat und DOCX-QA als Gates offen "
                "bleiben."
            ),
            required_binding_de=(
                "Jede Methode und jede Interpretation muss Source ID, Evidence ID, "
                "deterministisches Artefakt, Limitation, Source-Review-Gate und "
                "kompakte Tabelle/Figur behalten."
            ),
            compact_output_de=(
                f"High-Level Handoff: {context['handoff_rows']} Schreibzeilen aus "
                f"{context['bridge_worksheet_rows']} worksheet rows, "
                f"{context['bridge_method_rows']} method rows, "
                f"{context['bridge_interpretation_rows']} interpretation rows, "
                "0 source/artifact gaps, "
                f"{context['bridge_drafting_steps']} drafting steps, "
                f"{context['core_table_count']} Kern-Tabellen und "
                f"{context['core_figure_count']} Kern-Figuren."
            ),
            open_gate_de=(
                f"Offen: {context['pending_citation_rows']} pending citation rows, "
                "0 final-release-ready rows, Swiss offizielles Resultat, "
                "DOCX-Render-QA und finale Projektchecks."
            ),
            forbidden_action_de=(
                "Keine finale Zitation, keine Quellenstatus-Hochstufung, keine "
                "Rohartefakt-Dumps, kein Review-Access-Ausbau, keine Runtime-Agenten, "
                "kein MCP, kein Model Routing und keine LLM-Metriken."
            ),
            next_human_action_de=(
                "Mit dem H1-H2-H3 Draft entlang dieses Handoffs starten und vor "
                "finaler Freigabe die 23 manuellen Source-Review-Zeilen entscheiden."
            ),
        )
    ]

    for order, area in enumerate(CORE_AREAS, start=2):
        core_row = core_by_area.get(area)
        bridge_row = bridge_by_area.get(area)
        if core_row is None or bridge_row is None:
            raise ValueError(f"Writing handoff missing core/bridge row for {area}.")
        rows.append(_chapter_row(order=order, area=area, core_row=core_row, bridge_row=bridge_row))

    rows.extend(
        [
            _handoff_row(
                handoff_id="writing_handoff_05_compact_tables_figures",
                handoff_order=5,
                handoff_area="compact_table_figure_integration",
                authoritative_inputs=(
                    "data/results/thesis_curated_result_package.csv; "
                    "docs/research/THESIS_TABLE_FIGURE_CAPTIONS.md; "
                    "data/results/thesis_h1_h2_h3_core_sections.csv"
                ),
                allowed_ba_action_de=(
                    "Resultate thesis-ready darstellen: wenige gute Tabellen und "
                    "Figuren nutzen, nicht viele Artefakte. H1-H3 bekommt T2/F1, "
                    "T3/F2 und T4/F3; T1 rahmt die Methoden-/Evidence-Map, T5/F4 "
                    "bleiben kompakte Zusatzsicht."
                ),
                required_binding_de=(
                    "Jede Tabelle/Figur braucht Package ID, Caption, Artefaktpfad, "
                    "Source Note, Limitation und passende Evidence IDs."
                ),
                compact_output_de=(
                    f"Kompaktes Paket: {context['core_table_count']} Kern-Tabellen "
                    f"({context['core_table_ids']}) und {context['core_figure_count']} "
                    f"Kern-Figuren ({context['core_figure_ids']}); keine "
                    "Rohartefakt-Dumps im Haupttext."
                ),
                open_gate_de=(
                    "Finale Nummerierung, Layout, finale Zitation und DOCX-Render-QA "
                    "bleiben offen."
                ),
                forbidden_action_de=(
                    "Keine zusaetzlichen Tabellen/Figuren ohne Update von "
                    "Traceability, Caption Registry und Result Package."
                ),
                next_human_action_de=(
                    "Beim Kapitelentwurf nur T1-T5 und F1-F4 referenzieren und "
                    "Caption/Limitation vor dem Finalgate erneut pruefen."
                ),
            ),
            _handoff_row(
                handoff_id="writing_handoff_06_source_review_citation_gate",
                handoff_order=6,
                handoff_area="manual_source_review_and_citation_gate",
                authoritative_inputs=(
                    "data/results/thesis_source_review_batch_execution_plan.csv; "
                    "data/results/thesis_source_review_progress_ledger.csv; "
                    "data/results/thesis_ledger_citation_gate_summary.csv"
                ),
                allowed_ba_action_de=(
                    "Manual Source Review bleibt der naechste menschliche Gate: "
                    "H1 10 rows, H2 5 rows, H3 8 rows, danach TOTAL rebuild."
                ),
                required_binding_de=(
                    "Review-Felder bleiben Pflicht: review_status, "
                    "page_or_section_note, claim_support_decision, "
                    "blocked_wording_check, citation_use_decision, reviewed_by, "
                    "reviewed_at und review_comment_de."
                ),
                compact_output_de=(
                    f"Source Review Gate: {context['bridge_worksheet_rows']} "
                    f"worksheet rows, {context['pending_citation_rows']} pending "
                    "citation rows, 0 final-ready rows, 0 source-status change rows."
                ),
                open_gate_de=(
                    "Finale Zitation bleibt blockiert, bis jede H1-H2-H3 Zeile "
                    "manuell entschieden ist."
                ),
                forbidden_action_de=(
                    "Keine erfundenen Seitenzahlen, keine Candidate-Quelle als "
                    "Thesis-Evidenz, keine automatische Quellenstatus-Hochstufung."
                ),
                next_human_action_de=(
                    "H1-Batch starten, Page-/Section-Notes und Claim-Support "
                    "row-by-row eintragen, dann Gates regenerieren."
                ),
            ),
            _handoff_row(
                handoff_id="writing_handoff_07_agents_swiss_final_qa",
                handoff_order=7,
                handoff_area="agents_swiss_monitor_final_qa",
                authoritative_inputs=(
                    "data/results/thesis_agent_pipeline_upgrade_plan.csv; "
                    "data/results/thesis_agent_pipeline_safety_case.csv; "
                    "data/results/thesis_final_gate_board.csv"
                ),
                allowed_ba_action_de=(
                    "Agenten nur als Pipeline-Ausblick beschreiben; Swiss bleibt "
                    "deskriptiver Side Track bis zum offiziellen Resultat; Monitor "
                    "bleibt Appendix/Prototype pending human review."
                ),
                required_binding_de=(
                    "Spaetere Agentenhilfe braucht separates Goal, bounded inputs, "
                    "Proof-Artefakt, max 50 rows und llm_audit_log. Swiss braucht "
                    "offizielles Resultat; DOCX braucht Render-QA."
                ),
                compact_output_de=(
                    f"Agentenplan: {context['agent_upgrade_rows']} rows, "
                    f"{context['documentation_only_rows']} documentation-only, "
                    f"{context['deferred_agent_rows']} deferred, "
                    f"{context['active_agent_rows']} active runtime rows."
                ),
                open_gate_de=(
                    "Offen bleiben Source Review, Swiss Resultat-Mapping, "
                    "Monitor Human Review, DOCX-Render-QA und finale Projektchecks."
                ),
                forbidden_action_de=(
                    "Keine Runtime-Agenten, kein MCP, kein Model Routing, keine "
                    "LLM-Kennzahlen, keine Wallet-Adress-Exposition, keine Trading- "
                    "oder Profitabilitaetsclaims."
                ),
                next_human_action_de=(
                    "Agentenabschnitt nur als Future Work formulieren und alle "
                    "empirischen Aussagen an deterministische Artefakte binden."
                ),
            ),
        ]
    )
    return pd.DataFrame(rows, columns=HANDOFF_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_highlevel_thesis_writing_handoff(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _chapter_row(
    *,
    order: int,
    area: str,
    core_row: dict[str, object],
    bridge_row: dict[str, object],
) -> dict[str, object]:
    return _handoff_row(
        handoff_id=f"writing_handoff_{order:02d}_{area.lower()}_chapter",
        handoff_order=order,
        handoff_area=f"{area.lower()}_empirical_chapter",
        authoritative_inputs=(
            "data/results/thesis_h1_h2_h3_core_sections.csv; "
            "data/results/thesis_h1_h2_h3_source_gated_thesis_drafting_pass.csv; "
            "data/results/thesis_h1_h2_h3_worksheet_drafting_bridge.csv"
        ),
        allowed_ba_action_de=(
            f"{area}: bounded BA-Prosa schreiben mit Kapitel `{core_row['chapter_title_de']}`. "
            f"Resultatseed: {core_row['thesis_ready_result_de']} Interpretation "
            f"bounded halten: {core_row['bounded_interpretation_de']}"
        ),
        required_binding_de=(
            f"{area}: Methoden `{core_row['method_evidence_ids']}`, Interpretationen "
            f"`{core_row['interpretation_evidence_ids']}`, Literatur "
            f"`{core_row['literature_source_ids']}`, deterministische Artefakte, "
            f"Limitation `{core_row['mandatory_limitation_de']}`, "
            f"{core_row['source_review_gate_de']}"
        ),
        compact_output_de=(
            f"{area}: nur {bridge_row['selected_tables']}/{bridge_row['selected_figures']} "
            f"einbauen; {int(bridge_row['worksheet_rows'])} worksheet rows, "
            f"{int(bridge_row['method_rows'])} method rows, "
            f"{int(bridge_row['interpretation_rows'])} interpretation rows, "
            f"{int(bridge_row['pending_citation_rows'])} pending citation rows."
        ),
        open_gate_de=str(bridge_row["final_blocker_de"]),
        forbidden_action_de=(
            f"{area}: keine neue Kennzahl, keine Rohartefakt-Dumps, keine finale "
            "Zitation, keine Quellenstatus-Hochstufung und kein Claim ausserhalb "
            "des Wording Guards."
        ),
        next_human_action_de=str(bridge_row["writing_bridge_action_de"]),
    )


def _context(
    *,
    highlevel: pd.DataFrame,
    core_sections: pd.DataFrame,
    bridge: pd.DataFrame,
    drafting_pass: pd.DataFrame,
    curated_package: pd.DataFrame,
    final_gate: pd.DataFrame,
    agent_upgrade: pd.DataFrame,
    repo_root: Path | None,
) -> dict[str, int | str]:
    _require_columns(highlevel, HIGHLEVEL_REQUIRED_COLUMNS, "high-level next-step control summary")
    _require_columns(core_sections, CORE_SECTION_REQUIRED_COLUMNS, "H1-H2-H3 core sections")
    _require_columns(bridge, BRIDGE_REQUIRED_COLUMNS, "H1-H2-H3 worksheet drafting bridge")
    _require_columns(drafting_pass, DRAFTING_PASS_REQUIRED_COLUMNS, "source-gated drafting pass")
    _require_columns(curated_package, CURATED_PACKAGE_REQUIRED_COLUMNS, "curated result package")
    _require_columns(final_gate, FINAL_GATE_REQUIRED_COLUMNS, "final gate board")
    _require_columns(agent_upgrade, AGENT_UPGRADE_REQUIRED_COLUMNS, "agent upgrade plan")

    if len(highlevel) != 7 or highlevel["ready_for_final_release"].map(_bool_value).any():
        raise ValueError("Writing handoff requires seven high-level rows and no final release.")
    if len(core_sections) != 3 or set(core_sections["hypothesis"].astype(str)) != set(CORE_AREAS):
        raise ValueError("Writing handoff requires H1, H2, and H3 core sections.")
    if len(drafting_pass) != 15:
        raise ValueError("Writing handoff requires 15 source-gated drafting pass rows.")
    if drafting_pass["ready_for_final_submission"].map(_bool_value).any():
        raise ValueError("Writing handoff must not consume final-ready drafting pass rows.")
    if not drafting_pass["ready_for_bounded_draft"].map(_bool_value).all():
        raise ValueError("Writing handoff requires bounded-draft-ready drafting pass rows.")

    total_bridge = _row_by_id(bridge, "thesis_area", "TOTAL")
    if int(total_bridge["worksheet_rows"]) != 23:
        raise ValueError("Writing handoff expects 23 worksheet rows.")
    if int(total_bridge["method_rows"]) != 12 or int(total_bridge["interpretation_rows"]) != 11:
        raise ValueError("Writing handoff expects 12 method and 11 interpretation rows.")
    if int(total_bridge["method_interpretation_source_artifact_gap_rows"]) != 0:
        raise ValueError("Writing handoff requires 0 source/artifact gaps.")
    if int(total_bridge["final_release_ready_rows"]) != 0:
        raise ValueError("Writing handoff must not be final-release-ready.")
    if int(total_bridge["drafting_steps"]) != 15:
        raise ValueError("Writing handoff expects 15 drafting steps.")

    core_package = curated_package[curated_package["include_in_core_package"].map(_bool_value)]
    core_tables = sorted(
        core_package.loc[core_package["package_type"].astype(str) == "table", "package_id"]
        .astype(str)
        .tolist()
    )
    core_figures = sorted(
        core_package.loc[core_package["package_type"].astype(str) == "figure", "package_id"]
        .astype(str)
        .tolist()
    )
    if len(core_tables) != 5 or len(core_figures) != 4:
        raise ValueError("Writing handoff expects 5 core tables and 4 core figures.")

    gates = final_gate.set_index("gate_area").to_dict(orient="index")
    for gate_area in ("source_review", "swiss_result_gate", "docx_render_qa"):
        gate = gates.get(gate_area)
        if gate is None:
            raise ValueError(f"Writing handoff missing final gate: {gate_area}.")
        if _bool_value(gate.get("final_submission_ready")):
            raise ValueError(f"Writing handoff requires {gate_area} to remain final-blocked.")

    active_agent_rows = int(
        agent_upgrade["current_status"].astype(str).str.contains("active", case=False, na=False).sum()
    )
    if active_agent_rows:
        raise ValueError("Writing handoff must not include active runtime agents.")
    documentation_only_rows = int(
        agent_upgrade["current_status"]
        .astype(str)
        .str.contains("documentation", case=False, na=False)
        .sum()
    )
    deferred_agent_rows = int(
        agent_upgrade["current_status"].astype(str).str.contains("deferred", case=False, na=False).sum()
    )

    if repo_root is not None:
        for artifact_list in core_sections["deterministic_artifacts"].astype(str):
            for artifact in _split_semicolon(artifact_list):
                if artifact.startswith("plus "):
                    continue
                if not (repo_root / artifact).exists():
                    raise FileNotFoundError(f"Writing handoff missing deterministic artifact: {artifact}")

    return {
        "handoff_rows": 7,
        "bridge_worksheet_rows": int(total_bridge["worksheet_rows"]),
        "bridge_method_rows": int(total_bridge["method_rows"]),
        "bridge_interpretation_rows": int(total_bridge["interpretation_rows"]),
        "bridge_unique_sources": int(total_bridge["unique_sources"]),
        "pending_citation_rows": int(total_bridge["pending_citation_rows"]),
        "bridge_drafting_steps": int(total_bridge["drafting_steps"]),
        "core_table_count": len(core_tables),
        "core_figure_count": len(core_figures),
        "core_table_ids": ", ".join(core_tables),
        "core_figure_ids": ", ".join(core_figures),
        "agent_upgrade_rows": int(len(agent_upgrade)),
        "documentation_only_rows": documentation_only_rows,
        "deferred_agent_rows": deferred_agent_rows,
        "active_agent_rows": active_agent_rows,
    }


def _validate_handoff(
    *,
    handoff: pd.DataFrame,
    highlevel: pd.DataFrame,
    core_sections: pd.DataFrame,
    bridge: pd.DataFrame,
    drafting_pass: pd.DataFrame,
    curated_package: pd.DataFrame,
    final_gate: pd.DataFrame,
    agent_upgrade: pd.DataFrame,
    repo_root: Path,
) -> None:
    _require_columns(handoff, HANDOFF_COLUMNS, "high-level thesis writing handoff")
    context = _context(
        highlevel=highlevel,
        core_sections=core_sections,
        bridge=bridge,
        drafting_pass=drafting_pass,
        curated_package=curated_package,
        final_gate=final_gate,
        agent_upgrade=agent_upgrade,
        repo_root=repo_root,
    )
    if len(handoff) != 7:
        raise ValueError("Writing handoff must contain seven rows.")
    if handoff["handoff_order"].astype(int).tolist() != list(range(1, 8)):
        raise ValueError("Writing handoff rows must be ordered 1..7.")
    if handoff["handoff_id"].duplicated().any():
        raise ValueError("Writing handoff contains duplicate IDs.")
    if not handoff["ready_for_bounded_draft"].map(_bool_value).all():
        raise ValueError("Writing handoff must allow bounded BA drafting.")
    if handoff["ready_for_final_submission"].map(_bool_value).any():
        raise ValueError("Writing handoff must not mark final submission ready.")
    for artifacts in handoff["authoritative_inputs"].astype(str):
        for artifact in _split_semicolon(artifacts):
            if not (repo_root / artifact).exists():
                raise FileNotFoundError(f"Writing handoff input artifact missing: {artifact}")
    joined = "\n".join(handoff.fillna("").astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Writing handoff must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "review-access bleibt pausiert",
        "jede methode",
        "jede interpretation",
        "source id",
        "evidence id",
        "deterministisches artefakt",
        "23 worksheet rows",
        "12 method rows",
        "11 interpretation rows",
        "0 source/artifact gaps",
        "15 drafting steps",
        "5 kern-tabellen",
        "4 kern-figuren",
        "t2/f1",
        "t3/f2",
        "t4/f3",
        "23 pending citation rows",
        "keine finale zitation",
        "keine runtime-agenten",
        "0 active runtime rows",
        "max 50 rows",
        "llm_audit_log",
        "swiss",
        "docx",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Writing handoff missing required terms: " + ", ".join(missing))
    if int(context["active_agent_rows"]) != 0:
        raise ValueError("Writing handoff expects 0 active runtime rows.")


def _render_handoff_doc(handoff: pd.DataFrame) -> str:
    display = handoff[
        [
            "handoff_order",
            "handoff_area",
            "allowed_ba_action_de",
            "compact_output_de",
            "open_gate_de",
            "next_human_action_de",
        ]
    ]
    return (
        "# Highlevel Thesis Writing Handoff Ohne Review-Access\n\n"
        "Dieses Handoff ist die operative Schreibsicht fuer die BA, solange "
        "Review-Access pausiert bleibt. Es verdichtet nur bestehende "
        "deterministische Artefakte, liest keine Quelleninhalte, berechnet "
        "keine neuen Kennzahlen und aktiviert keine Runtime-Agenten.\n\n"
        "## Counts\n\n"
        f"- Handoff rows: {len(handoff)}\n"
        f"- Bounded-draft ready rows: {int(handoff['ready_for_bounded_draft'].map(_bool_value).sum())}\n"
        f"- Final-submission ready rows: {int(handoff['ready_for_final_submission'].map(_bool_value).sum())}\n\n"
        "## Handoff Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze dieses Handoff als Schreibsteuerung: zuerst den Projektframe "
        "ohne Review-Access halten, dann H1, H2 und H3 mit Evidence IDs, "
        "Source IDs, deterministischen Artefakten, Limitationen und "
        "T2/F1, T3/F2, T4/F3 schreiben. Danach nur das kompakte Paket mit "
        "5 Kern-Tabellen und 4 Kern-Figuren integrieren, die 23 Worksheet "
        "Rows manuell fuer Page-/Section-Note, Claim-Support, "
        "Blocked-Wording und Citation-Use entscheiden und Agenten nur als "
        "Future Work mit max 50 rows und `llm_audit_log` beschreiben. Keine "
        "finale Zitation, keine Quellenstatus-Hochstufung, keine "
        "Rohartefakt-Dumps, keine Runtime-Agenten, kein MCP, kein Model "
        "Routing, keine LLM-Metriken, keine Swiss-Finalinterpretation vor "
        "offiziellem Resultat und keine DOCX-Finalfreigabe ohne Render-QA.\n"
    )


def _handoff_row(
    *,
    handoff_id: str,
    handoff_order: int,
    handoff_area: str,
    authoritative_inputs: str,
    allowed_ba_action_de: str,
    required_binding_de: str,
    compact_output_de: str,
    open_gate_de: str,
    forbidden_action_de: str,
    next_human_action_de: str,
) -> dict[str, object]:
    return {
        "handoff_id": handoff_id,
        "handoff_order": handoff_order,
        "handoff_area": handoff_area,
        "authoritative_inputs": authoritative_inputs,
        "allowed_ba_action_de": allowed_ba_action_de,
        "required_binding_de": required_binding_de,
        "compact_output_de": compact_output_de,
        "open_gate_de": open_gate_de,
        "forbidden_action_de": forbidden_action_de,
        "next_human_action_de": next_human_action_de,
        "ready_for_bounded_draft": True,
        "ready_for_final_submission": False,
    }


def _row_by_id(frame: pd.DataFrame, column: str, value: str) -> pd.Series:
    rows = frame.loc[frame[column].astype(str) == value]
    if len(rows) != 1:
        raise ValueError(f"Expected one row where {column} == {value}.")
    return rows.iloc[0]


def _split_semicolon(value: str) -> list[str]:
    if value.lower() == "nan":
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required writing handoff input missing: {path}")
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
