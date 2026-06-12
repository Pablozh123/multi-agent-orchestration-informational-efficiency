"""Build thesis-ready H1-H2-H3 core sections and future agent upgrade notes."""

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
DEFAULT_DOCS_DIR = Path("docs/research")

CORE_SECTIONS_OUTPUT = "thesis_h1_h2_h3_core_sections.csv"
CORE_SECTIONS_DOC_OUTPUT = "THESIS_H1_H2_H3_CORE_SECTIONS.md"
AGENT_UPGRADE_OUTPUT = "thesis_agent_pipeline_upgrade_plan.csv"
AGENT_UPGRADE_DOC_OUTPUT = "THESIS_AGENT_PIPELINE_UPGRADE_PLAN.md"

CORE_SECTION_COLUMNS: tuple[str, ...] = (
    "section_id",
    "hypothesis",
    "chapter_title_de",
    "method_evidence_ids",
    "interpretation_evidence_ids",
    "literature_source_ids",
    "deterministic_artifacts",
    "traceability_statuses",
    "selected_tables",
    "selected_figures",
    "thesis_ready_result_de",
    "bounded_interpretation_de",
    "mandatory_limitation_de",
    "blocked_wording_de",
    "source_review_gate_de",
    "draft_text_de",
)

AGENT_UPGRADE_COLUMNS: tuple[str, ...] = (
    "upgrade_id",
    "future_assistance_role",
    "sequence_after_core_de",
    "uses_current_core_sections",
    "allowed_input_boundary",
    "allowed_output_boundary",
    "mandatory_audit_gate",
    "blocked_actions_de",
    "required_preconditions_de",
    "current_status",
    "next_safe_step_de",
)


@dataclass(frozen=True)
class ThesisCoreWritingPackageResult:
    """Generated thesis-core writing package paths and counts."""

    core_sections_path: Path
    core_sections_docs_path: Path
    agent_upgrade_path: Path
    agent_upgrade_docs_path: Path
    core_section_rows: int
    agent_upgrade_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "core_sections_path": str(self.core_sections_path),
            "core_sections_docs_path": str(self.core_sections_docs_path),
            "agent_upgrade_path": str(self.agent_upgrade_path),
            "agent_upgrade_docs_path": str(self.agent_upgrade_docs_path),
            "core_section_rows": self.core_section_rows,
            "agent_upgrade_rows": self.agent_upgrade_rows,
        }


def generate_thesis_core_writing_package(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> ThesisCoreWritingPackageResult:
    """Generate H1-H2-H3 core writing package and future agent upgrade plan."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    evidence_map = _read_csv(results_dir / "thesis_evidence_map.csv")
    core_results = _read_csv(results_dir / "thesis_core_results_table.csv")
    curated_package = _read_csv(results_dir / "thesis_curated_result_package.csv")
    captions = _read_csv(results_dir / "thesis_table_figure_captions.csv")
    method_traceability = _read_csv(results_dir / "thesis_method_interpretation_traceability.csv")
    agent_control = _read_csv(results_dir / "thesis_agent_pipeline_control_audit.csv")
    literature = _read_csv(repo_root / "data/literature/literature_index.csv")

    core_sections = build_core_sections(
        evidence_map=evidence_map,
        core_results=core_results,
        curated_package=curated_package,
        captions=captions,
        method_traceability=method_traceability,
        literature=literature,
        repo_root=repo_root,
    )
    agent_upgrade = build_agent_upgrade_plan(
        agent_control=agent_control,
        core_sections=core_sections,
    )
    _validate_core_sections(core_sections, repo_root=repo_root)
    _validate_agent_upgrade_plan(agent_upgrade)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    core_path = results_dir / CORE_SECTIONS_OUTPUT
    core_docs_path = docs_dir / CORE_SECTIONS_DOC_OUTPUT
    agent_path = results_dir / AGENT_UPGRADE_OUTPUT
    agent_docs_path = docs_dir / AGENT_UPGRADE_DOC_OUTPUT

    core_sections.to_csv(core_path, index=False)
    agent_upgrade.to_csv(agent_path, index=False)
    core_docs_path.write_text(_render_core_sections_doc(core_sections), encoding="utf-8")
    agent_docs_path.write_text(_render_agent_upgrade_doc(agent_upgrade), encoding="utf-8")

    return ThesisCoreWritingPackageResult(
        core_sections_path=core_path,
        core_sections_docs_path=core_docs_path,
        agent_upgrade_path=agent_path,
        agent_upgrade_docs_path=agent_docs_path,
        core_section_rows=len(core_sections),
        agent_upgrade_rows=len(agent_upgrade),
    )


def build_core_sections(
    *,
    evidence_map: pd.DataFrame,
    core_results: pd.DataFrame,
    curated_package: pd.DataFrame,
    captions: pd.DataFrame,
    method_traceability: pd.DataFrame,
    literature: pd.DataFrame,
    repo_root: Path,
) -> pd.DataFrame:
    """Return one thesis-ready writing row for each empirical core hypothesis."""

    _require_columns(
        evidence_map,
        (
            "evidence_id",
            "thesis_area",
            "item_type",
            "primary_artifact",
            "supporting_artifacts",
            "literature_sources",
            "allowed_wording",
            "blocked_wording",
            "main_limitation",
            "thesis_readiness",
        ),
        "evidence map",
    )
    _require_columns(
        core_results,
        (
            "result_id",
            "thesis_area",
            "key_value",
            "primary_artifact",
            "supporting_artifacts",
            "evidence_ids",
            "main_limitation",
            "thesis_readiness",
        ),
        "core results",
    )
    _require_columns(
        curated_package,
        (
            "package_id",
            "package_type",
            "thesis_section",
            "include_in_core_package",
            "primary_artifact",
            "supporting_artifacts",
            "evidence_ids",
        ),
        "curated result package",
    )
    _require_columns(captions, ("package_id", "caption_de"), "table figure captions")
    _require_columns(
        method_traceability,
        ("evidence_id", "traceability_status", "thesis_readiness"),
        "method interpretation traceability",
    )
    _require_columns(literature, ("source_id",), "literature index")

    known_sources = set(literature["source_id"].astype(str))
    traceability_by_evidence = (
        method_traceability.set_index("evidence_id")["traceability_status"].astype(str).to_dict()
    )
    rows: list[dict[str, object]] = []
    for hypothesis in ("H1", "H2", "H3"):
        evidence = evidence_map[
            (evidence_map["thesis_area"] == hypothesis)
            & (evidence_map["thesis_readiness"] == "thesis_facing_ready")
            & evidence_map["item_type"].isin(["method", "interpretation"])
        ].copy()
        if evidence.empty:
            raise ValueError(f"No thesis-facing evidence rows for {hypothesis}.")

        methods = evidence[evidence["item_type"] == "method"]
        interpretations = evidence[evidence["item_type"] == "interpretation"]
        if methods.empty or interpretations.empty:
            raise ValueError(f"{hypothesis} needs at least one method and one interpretation row.")

        hypothesis_results = core_results[core_results["thesis_area"] == hypothesis].copy()
        hypothesis_package = curated_package[
            curated_package["include_in_core_package"].map(_bool_value)
            & (curated_package["thesis_section"] == hypothesis)
        ].copy()
        if hypothesis_results.empty:
            raise ValueError(f"No core result rows for {hypothesis}.")
        if hypothesis_package.empty:
            raise ValueError(f"No curated package rows for {hypothesis}.")

        method_ids = methods["evidence_id"].astype(str).tolist()
        interpretation_ids = interpretations["evidence_id"].astype(str).tolist()
        evidence_ids = method_ids + interpretation_ids
        source_ids = _unique_from_semicolon(evidence["literature_sources"])
        unknown_sources = [source_id for source_id in source_ids if source_id not in known_sources]
        if unknown_sources:
            raise ValueError(f"{hypothesis} references unknown literature sources: {unknown_sources}")

        artifacts = _collect_artifacts(
            evidence=evidence,
            results=hypothesis_results,
            package=hypothesis_package,
        )
        tables = hypothesis_package[hypothesis_package["package_type"] == "table"]["package_id"].astype(str).tolist()
        figures = hypothesis_package[
            hypothesis_package["package_type"] == "figure"
        ]["package_id"].astype(str).tolist()
        traceability_statuses = _unique_text(
            traceability_by_evidence.get(evidence_id, "missing_traceability")
            for evidence_id in evidence_ids
        )

        rows.append(
            {
                "section_id": f"core_section_{hypothesis.lower()}",
                "hypothesis": hypothesis,
                "chapter_title_de": _chapter_title(hypothesis),
                "method_evidence_ids": "; ".join(method_ids),
                "interpretation_evidence_ids": "; ".join(interpretation_ids),
                "literature_source_ids": "; ".join(source_ids),
                "deterministic_artifacts": "; ".join(artifacts),
                "traceability_statuses": "; ".join(traceability_statuses),
                "selected_tables": "; ".join(tables),
                "selected_figures": "; ".join(figures),
                "thesis_ready_result_de": _result_text(hypothesis, hypothesis_results),
                "bounded_interpretation_de": _bounded_interpretation(hypothesis),
                "mandatory_limitation_de": _combined_limitations(
                    evidence=evidence,
                    results=hypothesis_results,
                    captions=captions,
                    package=hypothesis_package,
                ),
                "blocked_wording_de": _blocked_wording(evidence),
                "source_review_gate_de": (
                    "Draft nutzbar; finale Zitation erst nach Source Review mit "
                    "Page-/Section-Notes und geprueften Claim-Support-Entscheiden."
                ),
                "draft_text_de": _draft_text(
                    hypothesis=hypothesis,
                    results=hypothesis_results,
                    methods=methods,
                    interpretations=interpretations,
                    package=hypothesis_package,
                ),
            }
        )
    return pd.DataFrame(rows, columns=CORE_SECTION_COLUMNS)


def build_agent_upgrade_plan(
    *,
    agent_control: pd.DataFrame,
    core_sections: pd.DataFrame,
) -> pd.DataFrame:
    """Return a documentation-only future agent upgrade sequence."""

    _require_columns(agent_control, AGENT_UPGRADE_SOURCE_COLUMNS, "agent control audit")
    _require_columns(core_sections, ("section_id", "hypothesis"), "core sections")

    rows: list[dict[str, object]] = []
    for index, row in enumerate(agent_control.sort_values("control_id").to_dict(orient="records"), start=1):
        role = str(row["future_assistance_role"])
        rows.append(
            {
                "upgrade_id": f"agent_upgrade_{index:02d}",
                "future_assistance_role": role,
                "sequence_after_core_de": _agent_sequence_text(role),
                "uses_current_core_sections": (
                    "Ja, nur als bounded context: "
                    + "; ".join(core_sections["section_id"].astype(str).tolist())
                    + ". Keine Rohartefakt-Dumps."
                ),
                "allowed_input_boundary": str(row["allowed_input_boundary"]),
                "allowed_output_boundary": str(row["allowed_output_boundary"]),
                "mandatory_audit_gate": str(row["mandatory_audit_gate"]),
                "blocked_actions_de": str(row["blocked_actions_de"]),
                "required_preconditions_de": str(row["required_preconditions_de"]),
                "current_status": str(row["current_activation_state"]),
                "next_safe_step_de": str(row["next_safe_step_de"]),
            }
        )
    return pd.DataFrame(rows, columns=AGENT_UPGRADE_COLUMNS)


AGENT_UPGRADE_SOURCE_COLUMNS: tuple[str, ...] = (
    "control_id",
    "future_assistance_role",
    "current_activation_state",
    "allowed_input_boundary",
    "allowed_output_boundary",
    "mandatory_audit_gate",
    "blocked_actions_de",
    "required_preconditions_de",
    "next_safe_step_de",
)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_thesis_core_writing_package(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_core_sections(core_sections: pd.DataFrame, *, repo_root: Path) -> None:
    _require_columns(core_sections, CORE_SECTION_COLUMNS, "core sections")
    if tuple(core_sections["hypothesis"].tolist()) != ("H1", "H2", "H3"):
        raise ValueError("Core sections must contain H1, H2, and H3 in order.")
    if core_sections["section_id"].duplicated().any():
        raise ValueError("Core sections contain duplicate section_id values.")
    for column in (
        "method_evidence_ids",
        "interpretation_evidence_ids",
        "literature_source_ids",
        "deterministic_artifacts",
        "selected_tables",
        "selected_figures",
        "thesis_ready_result_de",
        "bounded_interpretation_de",
        "mandatory_limitation_de",
        "blocked_wording_de",
        "draft_text_de",
    ):
        if core_sections[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Core sections contain empty {column}.")
    for artifacts in core_sections["deterministic_artifacts"].astype(str):
        for artifact in _split_semicolon(artifacts):
            if artifact.startswith(("http://", "https://")):
                continue
            if not (repo_root / artifact).exists():
                raise FileNotFoundError(f"Core section artifact missing: {artifact}")
    joined = "\n".join(core_sections.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Core sections must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "evidence-id",
        "source review",
        "brier",
        "tages",
        "granger",
        "tabelle",
        "abbildung",
        "keine",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Core sections missing required terms: " + ", ".join(missing))
    if lower_joined.count("keine finale zitation") < 3 and "finale zitation erst" not in lower_joined:
        raise ValueError("Core sections must keep final citation gate visible.")


def _validate_agent_upgrade_plan(agent_upgrade: pd.DataFrame) -> None:
    _require_columns(agent_upgrade, AGENT_UPGRADE_COLUMNS, "agent upgrade plan")
    if agent_upgrade["upgrade_id"].duplicated().any():
        raise ValueError("Agent upgrade plan contains duplicate upgrade_id values.")
    if len(agent_upgrade) == 0:
        raise ValueError("Agent upgrade plan is empty.")
    active = agent_upgrade[agent_upgrade["current_status"].astype(str).str.contains("active")]
    if not active.empty:
        raise ValueError("Agent upgrade plan must not contain active runtime rows.")
    joined = "\n".join(agent_upgrade.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Agent upgrade plan must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "llm_audit_log",
        "bounded",
        "keine runtime-agenten",
        "keine llm-metriken",
        "keine trading-pfade",
        "keine rohartefakt-dumps",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Agent upgrade plan missing required guardrails: " + ", ".join(missing))


def _render_core_sections_doc(core_sections: pd.DataFrame) -> str:
    display = core_sections[
        [
            "section_id",
            "hypothesis",
            "chapter_title_de",
            "method_evidence_ids",
            "interpretation_evidence_ids",
            "selected_tables",
            "selected_figures",
            "source_review_gate_de",
        ]
    ]
    sections = []
    for row in core_sections.to_dict(orient="records"):
        sections.append(
            f"## {row['chapter_title_de']}\n\n"
            f"**Evidence-IDs:** Methoden `{row['method_evidence_ids']}`; "
            f"Interpretationen `{row['interpretation_evidence_ids']}`.\n\n"
            f"**Literatur/Quellen:** `{row['literature_source_ids']}`.\n\n"
            f"**Deterministische Artefakte:** `{row['deterministic_artifacts']}`.\n\n"
            f"**Tabelle/Figur:** Tabelle `{row['selected_tables']}`, "
            f"Abbildung `{row['selected_figures']}`.\n\n"
            f"**Resultat:** {row['thesis_ready_result_de']}\n\n"
            f"**Interpretation:** {row['bounded_interpretation_de']}\n\n"
            f"**Limitation:** {row['mandatory_limitation_de']}\n\n"
            f"**Nicht schreiben:** {row['blocked_wording_de']}\n\n"
            f"**Draft-Text:** {row['draft_text_de']}\n"
        )
    return (
        "# Thesis H1-H2-H3 Core Sections\n\n"
        "Dieses Artefakt macht aus Evidence Map, Core Results, Traceability "
        "Audit und kuratiertem Tabellen-/Figurenpaket eine thesis-ready "
        "Kernfassung fuer die drei empirischen Kapitel. Es berechnet keine "
        "neuen Kennzahlen und ersetzt keine manuelle Source Review.\n\n"
        "## Counts\n\n"
        f"- Core sections: {len(core_sections)}\n"
        "- Scope: H1, H2, H3\n"
        "- Use: BA-Draft, nicht finale Zitation\n\n"
        "## Section Map\n\n"
        + _markdown_table(display)
        + "\n\n"
        + "\n\n".join(sections)
        + "\n\n## Use Rule\n\n"
        "Nutze diese Abschnitte als Schreibkern. Jede Methode und jede "
        "Interpretation bleibt an Evidence-ID, Quelle oder deterministisches "
        "Artefakt gebunden. Nutze wenige gute Tabellen/Figuren: T2/F1 fuer H1, "
        "T3/F2 fuer H2 und T4/F3 fuer H3. Keine Rohartefakt-Dumps, keine "
        "LLM-Metriken und keine finale Zitation ohne Source Review.\n"
    )


def _render_agent_upgrade_doc(agent_upgrade: pd.DataFrame) -> str:
    status_counts = agent_upgrade["current_status"].value_counts().to_dict()
    display = agent_upgrade[
        [
            "upgrade_id",
            "future_assistance_role",
            "sequence_after_core_de",
            "current_status",
            "next_safe_step_de",
        ]
    ]
    return (
        "# Thesis Agent Pipeline Upgrade Plan\n\n"
        "Dieses Dokument beschreibt nur, wie die Pipeline spaeter mit "
        "Assistenz-Agenten verbessert werden koennte. Es implementiert, "
        "aktiviert und nutzt keine Runtime-Agenten, kein MCP, kein Model "
        "Routing und keine LLM-Metriken.\n\n"
        "## Counts\n\n"
        f"- Upgrade rows: {len(agent_upgrade)}\n"
        f"- Documentation-only rows: {int(status_counts.get('future_documentation_only', 0))}\n"
        f"- Deferred rows: {int(status_counts.get('future_deferred', 0))}\n\n"
        "## Upgrade Sequence\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Guardrail Matrix\n\n"
        + _markdown_table(agent_upgrade)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze diesen Plan erst nach dem H1-H2-H3-Draft als Future-Work-"
        "Gedanken. Vor Aktivierung braucht jede Rolle ein separates "
        "genehmigtes Goal, Tests, bounded inputs, Output-Limits und "
        "`llm_audit_log`. Bis dahin bleiben Runtime-Agenten, MCP, Model "
        "Routing, LLM-Metriken, Rohartefakt-Dumps, Wallet-Adress-Exposition by "
        "default und Trading-Pfade deaktiviert.\n"
    )


def _chapter_title(hypothesis: str) -> str:
    titles = {
        "H1": "H1: Prognosequalitaet",
        "H2": "H2: Tagesbasierte Ereignisfenster",
        "H3": "H3: Wallet-Timing-Diagnostik",
    }
    return titles[hypothesis]


def _result_text(hypothesis: str, results: pd.DataFrame) -> str:
    result_by_id = {str(row["result_id"]): row for row in results.to_dict(orient="records")}
    if hypothesis == "H1":
        bounded = result_by_id.get("core_h1_bounded_poll_scope", {})
        broad = result_by_id.get("core_h1_broad_claim_boundary", {})
        return (
            "H1 wird als zweigeteiltes Resultat geschrieben: begrenzter Support im "
            f"Poll-Vergleichsscope mit `{bounded.get('key_value', '')}`; zugleich "
            f"bleibt die breite Ueberlegenheitsbehauptung mit `{broad.get('key_value', '')}` "
            "nicht bewiesen."
        )
    if hypothesis == "H2":
        row = results.iloc[0]
        return (
            "H2 berichtet eine sichtbare Tagesbewegung im kuratierten Ereignisfenster: "
            f"`{row['key_value']}`. Das ist ein Tagesfensterbefund, kein Intraday-Speed-Test."
        )
    if hypothesis == "H3":
        row = results.iloc[0]
        return (
            "H3 berichtet die staerkste aktuelle Wallet-Timingdiagnostik fuer das "
            f"oberste Tier: `{row['key_value']}`."
        )
    raise ValueError(f"Unknown hypothesis: {hypothesis}")


def _bounded_interpretation(hypothesis: str) -> str:
    interpretations = {
        "H1": (
            "Polymarket darf nur in klar definierten Vergleichsscopes als besser "
            "gestuetzt beschrieben werden; die Gesamtaussage bleibt gemischt."
        ),
        "H2": (
            "Die Ergebnisse zeigen oeffentliche Ereignisreaktionen im Tagesraster, "
            "aber keine minutengenaue oder kausale Informationsverarbeitung."
        ),
        "H3": (
            "Top-tier Wallet-Aktivitaet ist eine predictive timing diagnostic, aber "
            "kein Beweis fuer Kausalitaet, private Information oder Tradeability."
        ),
    }
    return interpretations[hypothesis]


def _draft_text(
    *,
    hypothesis: str,
    results: pd.DataFrame,
    methods: pd.DataFrame,
    interpretations: pd.DataFrame,
    package: pd.DataFrame,
) -> str:
    method_ids = "; ".join(methods["evidence_id"].astype(str).tolist())
    interpretation_ids = "; ".join(interpretations["evidence_id"].astype(str).tolist())
    tables = "; ".join(package[package["package_type"] == "table"]["package_id"].astype(str).tolist())
    figures = "; ".join(package[package["package_type"] == "figure"]["package_id"].astype(str).tolist())
    if hypothesis == "H1":
        return (
            "Im H1-Kapitel wird Prognosequalitaet ueber Brier-Verlust und "
            "Diebold-Mariano-Vergleich beschrieben. Die Evidence-IDs "
            f"`{method_ids}` und `{interpretation_ids}` tragen die Aussage. "
            f"Die Resultate werden kompakt in Tabelle {tables} und Abbildung {figures} "
            "gezeigt: ein begrenzter Poll-Vergleichsscope stuetzt Polymarket, "
            "waehrend die breite Ueberlegenheitsbehauptung nicht bewiesen ist."
        )
    if hypothesis == "H2":
        return (
            "Im H2-Kapitel werden vorab kuratierte oeffentliche Ereignisse mit "
            "fixen Tagesfenstern untersucht. Die Evidence-IDs "
            f"`{method_ids}` und `{interpretation_ids}` verweisen auf die "
            f"deterministischen Artefakte. Tabelle {tables} und Abbildung {figures} "
            "zeigen Tagesbewegungen, nicht Intraday-Reaktionsgeschwindigkeit."
        )
    if hypothesis == "H3":
        return (
            "Im H3-Kapitel werden Wallet-Tiers dataset-relativ gebildet und mit "
            "Lead-Lag- sowie Granger-Diagnostik ausgewertet. Die Evidence-IDs "
            f"`{method_ids}` und `{interpretation_ids}` binden die Methode und "
            f"Interpretation. Tabelle {tables} und Abbildung {figures} zeigen "
            "das Top-tier Timingmuster unter BUY-only-, Tagesfrequenz- und "
            "Mehrfachtest-Limitationen."
        )
    raise ValueError(f"Unknown hypothesis: {hypothesis}")


def _combined_limitations(
    *,
    evidence: pd.DataFrame,
    results: pd.DataFrame,
    captions: pd.DataFrame,
    package: pd.DataFrame,
) -> str:
    limitations = _unique_text(
        [
            *evidence["main_limitation"].astype(str).tolist(),
            *results["main_limitation"].astype(str).tolist(),
        ]
    )
    caption_by_id = captions.set_index("package_id").to_dict(orient="index")
    for package_id in package["package_id"].astype(str).tolist():
        limitation = str(caption_by_id.get(package_id, {}).get("limitation_note_de", "")).strip()
        if limitation:
            limitations.append(limitation)
    return " | ".join(_translate_known_phrase(item) for item in _unique_text(limitations))


def _blocked_wording(evidence: pd.DataFrame) -> str:
    return " | ".join(
        _translate_known_phrase(item) for item in _unique_from_semicolon(evidence["blocked_wording"])
    )


def _agent_sequence_text(role: str) -> str:
    role_lower = role.lower()
    if "source" in role_lower:
        return "Nach H1-H2-H3-Kern: fehlende Page-/Section-Notes und Claim-Support-Felder vorbereiten."
    if "draft" in role_lower or "evidence" in role_lower:
        return "Nach stabiler Core-Section-CSV: Evidence-IDs in kurze Entwurfsnotizen uebersetzen."
    if "wording" in role_lower or "claim" in role_lower:
        return "Nach erstem Kapiteltext: Absatzweise gegen allowed/blocked wording pruefen."
    if "table" in role_lower or "figure" in role_lower:
        return "Nach Tabellen-/Figurenintegration: Caption, Artefakt und Limitation abgleichen."
    if "advisor" in role_lower or "dozent" in role_lower:
        return "Nach Dozentenfeedback: Status und offene Entscheidungen knapp zusammenfassen."
    if "monitor" in role_lower:
        return "Erst nach Human Review: Monitor-Appendix als Review-Workflow zusammenfassen."
    if "mcp" in role_lower:
        return "Erst nach separatem Access-Goal: read-only Summary Interface spezifizieren."
    return "Nur nach separatem Goal und Audit-Logging als Future-Work pruefen."


def _collect_artifacts(
    *,
    evidence: pd.DataFrame,
    results: pd.DataFrame,
    package: pd.DataFrame,
) -> list[str]:
    artifacts: list[str] = []
    for frame in (evidence, results, package):
        for column in ("primary_artifact", "supporting_artifacts"):
            if column in frame:
                artifacts.extend(_unique_from_semicolon(frame[column]))
    return _unique_text(artifacts)


def _unique_from_semicolon(values: pd.Series | Sequence[object]) -> list[str]:
    collected: list[str] = []
    for value in values:
        collected.extend(_split_semicolon(value))
    return _unique_text(collected)


def _unique_text(values: Sequence[object]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text.lower() == "nan" or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _translate_known_phrase(text: str) -> str:
    translations = {
        "Repeated daily rows and one election context limit generalisation.": (
            "Wiederholte Tageszeilen und ein Wahlkontext begrenzen die Generalisierbarkeit."
        ),
        "The full state-date panel and other scopes remain counterexamples to the broad claim.": (
            "Das volle State-Date-Panel und weitere Scopes bleiben Gegenbeispiele zur breiten Behauptung."
        ),
        "The available evidence mixes daily rows, state outcomes, transformed polls, and source-specific scopes.": (
            "Die Evidenz mischt Tageszeilen, State-Outcomes, transformierte Poll-Signale und quellenspezifische Scopes."
        ),
        "The full panel and other scopes still contain counterexamples.": (
            "Das volle Panel und weitere Scopes enthalten weiterhin Gegenbeispiele."
        ),
        "Evidence units differ across daily rows, states, and transformed poll scopes.": (
            "Die Evidenzeinheiten unterscheiden sich zwischen Tageszeilen, States und transformierten Poll-Scopes."
        ),
        "Daily prices cannot identify intraday reaction timing.": (
            "Tagespreise koennen Intraday-Reaktionstiming nicht identifizieren."
        ),
        "Direction and magnitude are event-window diagnostics, not intraday causal estimates.": (
            "Richtung und Groesse sind Ereignisfensterdiagnostik, keine Intraday-Kausalschaetzung."
        ),
        "Daily data do not support intraday reaction-speed claims.": (
            "Tagesdaten stuetzen keine Intraday-Reaktionsgeschwindigkeitsclaims."
        ),
        "Observed wallet data are BUY-only and source-filtered.": (
            "Die beobachteten Walletdaten sind BUY-only und quellengefiltert."
        ),
        "Daily alignment, multiple testing, and BUY-only extraction limit conclusion strength.": (
            "Taegliche Ausrichtung, Mehrfachtests und BUY-only-Extraktion begrenzen die Schlussstaerke."
        ),
        "Signal strength is diagnostic and needs sensitivity/multiple-testing caution.": (
            "Die Signalstaerke ist diagnostisch und braucht Sensitivitaets- und Mehrfachtest-Vorsicht."
        ),
        "BUY-only source data, daily alignment, and multiple-testing caution.": (
            "BUY-only-Quelldaten, taegliche Ausrichtung und Mehrfachtest-Vorsicht begrenzen die Aussage."
        ),
        "reaction speed proof": "Reaktionsgeschwindigkeitsbeweis",
        "broad market superiority proof": "allgemeiner Marktueberlegenheitsbeweis",
        "RCP probability claim without transformation": (
            "RCP-Wahrscheinlichkeitsaussage ohne dokumentierte Transformation"
        ),
        "Polymarket is always better": "Polymarket ist immer besser",
        "many-election proof": "Mehrwahl-Beweis",
        "causal explanation": "kausale Erklaerung",
        "general superiority": "allgemeine Ueberlegenheit",
        "universal forecast dominance": "universelle Prognosedominanz",
        "intraday speed claim": "Intraday-Geschwindigkeitsaussage",
        "post-hoc event selection": "post-hoc Ereignisauswahl",
        "instant market reaction": "sofortige Marktreaktion",
        "causal event proof": "kausaler Ereignisbeweis",
        "arbitrary whale threshold": "willkuerliche Whale-Schwelle",
        "identified private-information wallets": "identifizierte Private-Information-Wallets",
        "causality proof": "Kausalitaetsbeweis",
        "private information proof": "Private-Information-Beweis",
        "profitability proof": "Profitabilitaetsbeweis",
        "private-information proof": "Private-Information-Beweis",
        "causal misconduct": "kausales Fehlverhalten",
        "tradable strategy": "handelbare Strategie",
    }
    return translations.get(text, text)


def _split_semicolon(value: object) -> list[str]:
    if pd.isna(value):
        return []
    return [item.strip() for item in str(value).split(";") if item.strip()]


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required thesis core writing input missing: {path}")
    return pd.read_csv(path)


def _resolve_under(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


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
