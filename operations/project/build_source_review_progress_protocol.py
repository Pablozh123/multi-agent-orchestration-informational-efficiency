"""Build a source-review progress protocol for thesis consolidation gates."""

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

PROTOCOL_OUTPUT = "thesis_source_review_progress_protocol.csv"
PROTOCOL_DOC_OUTPUT = "THESIS_SOURCE_REVIEW_PROGRESS_PROTOCOL.md"

PROTOCOL_COLUMNS: tuple[str, ...] = (
    "protocol_id",
    "protocol_area",
    "source_artifact",
    "deterministic_evidence_de",
    "current_state",
    "required_manual_action_de",
    "thesis_use_rule_de",
    "blocked_actions_de",
    "next_safe_step_de",
)


@dataclass(frozen=True)
class SourceReviewProgressProtocolResult:
    """Generated source-review progress protocol paths and counts."""

    protocol_path: Path
    docs_path: Path
    protocol_rows: int
    method_rows: int
    interpretation_rows: int
    core_table_rows: int
    core_figure_rows: int
    active_agent_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "protocol_path": str(self.protocol_path),
            "docs_path": str(self.docs_path),
            "protocol_rows": self.protocol_rows,
            "method_rows": self.method_rows,
            "interpretation_rows": self.interpretation_rows,
            "core_table_rows": self.core_table_rows,
            "core_figure_rows": self.core_figure_rows,
            "active_agent_rows": self.active_agent_rows,
        }


def generate_source_review_progress_protocol(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> SourceReviewProgressProtocolResult:
    """Generate the protocol CSV and Markdown summary."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    traceability = _read_csv(results_dir / "thesis_method_interpretation_traceability.csv")
    package = _read_csv(results_dir / "thesis_result_package_traceability.csv")
    ledger = _read_csv(results_dir / "thesis_source_review_progress_ledger.csv")
    core_sections = _read_csv(results_dir / "thesis_h1_h2_h3_core_sections.csv")
    agent_upgrade = _read_csv(results_dir / "thesis_agent_pipeline_upgrade_plan.csv")

    protocol = build_source_review_progress_protocol(
        traceability=traceability,
        package=package,
        ledger=ledger,
        core_sections=core_sections,
        agent_upgrade=agent_upgrade,
    )
    _validate_protocol(protocol)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    protocol_path = results_dir / PROTOCOL_OUTPUT
    docs_path = docs_dir / PROTOCOL_DOC_OUTPUT
    protocol.to_csv(protocol_path, index=False)
    docs_path.write_text(_render_protocol_doc(protocol), encoding="utf-8")

    summary = _summary(
        traceability=traceability,
        package=package,
        ledger=ledger,
        core_sections=core_sections,
        agent_upgrade=agent_upgrade,
    )
    return SourceReviewProgressProtocolResult(
        protocol_path=protocol_path,
        docs_path=docs_path,
        protocol_rows=len(protocol),
        method_rows=summary["method_rows"],
        interpretation_rows=summary["interpretation_rows"],
        core_table_rows=summary["core_table_rows"],
        core_figure_rows=summary["core_figure_rows"],
        active_agent_rows=summary["active_agent_rows"],
    )


def build_source_review_progress_protocol(
    *,
    traceability: pd.DataFrame,
    package: pd.DataFrame,
    ledger: pd.DataFrame,
    core_sections: pd.DataFrame,
    agent_upgrade: pd.DataFrame,
) -> pd.DataFrame:
    """Return protocol rows that bind evidence, result package, review, and agents."""

    summary = _summary(
        traceability=traceability,
        package=package,
        ledger=ledger,
        core_sections=core_sections,
        agent_upgrade=agent_upgrade,
    )
    _validate_summary(summary)

    rows = [
        _protocol_row(
            protocol_id="protocol_01_method_interpretation_mapping",
            protocol_area="evidence_mapping",
            source_artifact="data/results/thesis_method_interpretation_traceability.csv",
            deterministic_evidence_de=(
                f"Thesis-facing Methoden: {summary['method_ready_rows']}/{summary['method_rows']} "
                "mit deterministischem Artefakt und Quelle; "
                f"Interpretationen: {summary['interpretation_ready_rows']}/{summary['interpretation_rows']} "
                "mit deterministischem Artefakt, Quelle und Limitation; "
                f"Traceability gaps: {summary['traceability_gap_rows']}."
            ),
            current_state="draft_traceable_final_source_review_pending",
            required_manual_action_de=(
                "Source Review je Evidence ID fortsetzen: Page-/Section-Note, "
                "Claim-Support und Blocked-Wording-Check im Ledger erfassen."
            ),
            thesis_use_rule_de=(
                "BA-Draft darf die gemappten Methoden und Interpretationen nutzen; "
                "keine finale Zitation ohne manuelle Source Review."
            ),
            blocked_actions_de=(
                "Keine Quellenstatus-Hochstufung, keine finale Zitation und keine "
                "neuen Methoden- oder Interpretationsclaims ohne Artefakt, Quelle "
                "und Limitation."
            ),
            next_safe_step_de="H1-H2-H3 Source-Review-Zeilen nach Evidence ID abarbeiten.",
        ),
        _protocol_row(
            protocol_id="protocol_02_compact_result_package",
            protocol_area="result_package",
            source_artifact=(
                "data/results/thesis_curated_result_package.csv; "
                "data/results/thesis_result_package_traceability.csv"
            ),
            deterministic_evidence_de=(
                f"Kernpaket: {summary['core_table_rows']} Tabellen und "
                f"{summary['core_figure_rows']} Figuren; Package gaps: "
                f"{summary['package_gap_rows']}; nicht alle Rohartefakte werden "
                "in den Haupttext uebernommen."
            ),
            current_state="core_package_ready_for_bounded_draft",
            required_manual_action_de=(
                "Nur die kuratierten Tabellen/Figuren in den BA-Text integrieren "
                "und Caption, Quelle, Limitation sowie Evidence IDs gegenpruefen."
            ),
            thesis_use_rule_de=(
                "Resultate thesis-ready als wenige starke Tabellen und Figuren "
                "schreiben; Rohartefakte bleiben im Anhang oder als Nachweis."
            ),
            blocked_actions_de=(
                "Keine Rohartefakt-Dumps, keine neuen Kennzahlen und keine "
                "zusaetzlichen Tabellen/Figuren ohne Update der deterministischen Maps."
            ),
            next_safe_step_de="T2-F1, T3-F2 und T4-F3 im H1-H2-H3-Kern platzieren.",
        ),
        _protocol_row(
            protocol_id="protocol_03_ledger_review_flow",
            protocol_area="source_review_ledger",
            source_artifact="data/results/thesis_source_review_progress_ledger.csv",
            deterministic_evidence_de=(
                f"Ledger rows: {summary['ledger_rows']}; pending: {summary['ledger_pending_rows']}; "
                f"final-ready: {summary['ledger_final_ready_rows']}; source-status changes "
                f"erlaubt: {summary['ledger_source_status_change_rows']}."
            ),
            current_state="manual_review_pending",
            required_manual_action_de=(
                "Nur die manuellen Ledger-Felder aktualisieren: Page-/Section-Note, "
                "Claim-Support, Blocked-Wording, Citation-Use, Reviewer und Kommentar."
            ),
            thesis_use_rule_de=(
                "Ledger dokumentiert Fortschritt; er ersetzt keine Quellenlekture "
                "und keine finale Zitierentscheidung."
            ),
            blocked_actions_de=(
                "Keine Quellenstatus-Hochstufung, keine automatische Page Note, "
                "keine finale Zitation und keine Quelleninterpretation durch das Skript."
            ),
            next_safe_step_de="Priority-1-Quellen manuell oeffnen und Ledger-Felder pflegen.",
        ),
        _protocol_row(
            protocol_id="protocol_04_final_citation_gate",
            protocol_area="final_citation_gate",
            source_artifact=(
                "data/results/thesis_source_review_progress_ledger.csv; "
                "docs/project/THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md"
            ),
            deterministic_evidence_de=(
                f"Final citation ready rows: {summary['ledger_final_ready_rows']}; "
                f"preserved manual rows: {summary['ledger_preserved_rows']}; "
                "finale Zitation bleibt manuell blockiert, bis jede Quelle freigegeben ist."
            ),
            current_state="final_citation_blocked_until_manual_review",
            required_manual_action_de=(
                "Erst nach belegter Page-/Section-Note, Claim-Support, bestandenem "
                "Blocked-Wording-Check und Citation-Use-Entscheid zitieren."
            ),
            thesis_use_rule_de=(
                "Draft-Zitationen bleiben Pending-Marker; finale Zitation erst nach "
                "vollstaendigem Source Review."
            ),
            blocked_actions_de=(
                "Keine finale Zitation, keine Candidate-Quellen als Thesis-Evidence "
                "und keine stillschweigende Entfernung offener Gates."
            ),
            next_safe_step_de="Nach manueller Review citation_use_decision je Quelle setzen.",
        ),
        _protocol_row(
            protocol_id="protocol_05_core_chapter_sequence",
            protocol_area="h1_h2_h3_drafting",
            source_artifact="data/results/thesis_h1_h2_h3_core_sections.csv",
            deterministic_evidence_de=(
                f"Core Sections: {summary['core_section_rows']} "
                f"({summary['core_hypotheses']}); selected tables: "
                f"{summary['core_selected_tables']}; selected figures: "
                f"{summary['core_selected_figures']}."
            ),
            current_state="bounded_chapter_draft_allowed",
            required_manual_action_de=(
                "H1, H2 und H3 entlang der Core Sections schreiben und die Source "
                "Review Gates sichtbar im Draft halten."
            ),
            thesis_use_rule_de=(
                "Kapitel duerfen thesis-ready vorbereitet werden, solange "
                "Limitationen, Artefakte und Pending-Quellenstatus sichtbar bleiben."
            ),
            blocked_actions_de=(
                "Keine Universal-, Intraday-, Kausalitaets-, Private-Information-, "
                "Profitabilitaets- oder Tradeability-Claims."
            ),
            next_safe_step_de="H1-H2-H3 Prosa mit Evidence IDs und kuratiertem Resultatpaket verdichten.",
        ),
        _protocol_row(
            protocol_id="protocol_06_future_agent_upgrade_boundary",
            protocol_area="future_agents",
            source_artifact="data/results/thesis_agent_pipeline_upgrade_plan.csv",
            deterministic_evidence_de=(
                f"Future agent upgrade rows: {summary['agent_upgrade_rows']}; "
                f"active: {summary['active_agent_rows']}; documentation-only/deferred: "
                f"{summary['inactive_agent_rows']}. Max 50 rows, bounded inputs und "
                "llm_audit_log bleiben Pflicht."
            ),
            current_state="future_documentation_only",
            required_manual_action_de=(
                "Agentenverbesserungen nur als spaeteres separates Goal spezifizieren, "
                "nach stabiler Source Review und mit Tests."
            ),
            thesis_use_rule_de=(
                "Im aktuellen BA-Kern nur als Future-Work-Pipeline beschreiben, "
                "nicht ausfuehren."
            ),
            blocked_actions_de=(
                "Keine Runtime-Agenten, kein MCP, kein Model Routing, keine "
                "LLM-Metriken, keine Rohdaten-Prompts, keine Wallet-Adress-Exposition "
                "und keine Trading-Pfade."
            ),
            next_safe_step_de="Nach H1-H3 Draft ein separates Agenten-Audit-Design schreiben.",
        ),
    ]
    return pd.DataFrame(rows, columns=PROTOCOL_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_source_review_progress_protocol(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _summary(
    *,
    traceability: pd.DataFrame,
    package: pd.DataFrame,
    ledger: pd.DataFrame,
    core_sections: pd.DataFrame,
    agent_upgrade: pd.DataFrame,
) -> dict[str, int | str]:
    _require_columns(
        traceability,
        (
            "item_type",
            "thesis_readiness",
            "primary_artifact_exists",
            "literature_source_count",
            "known_literature_source_count",
            "limitation_present",
            "traceability_status",
        ),
        "method interpretation traceability",
    )
    _require_columns(
        package,
        (
            "package_type",
            "include_in_core_package",
            "package_traceability_status",
        ),
        "result package traceability",
    )
    _require_columns(
        ledger,
        (
            "ledger_id",
            "review_progress_state",
            "source_status_change_allowed",
            "final_citation_ready",
            "preserved_manual_fields",
        ),
        "source review progress ledger",
    )
    _require_columns(
        core_sections,
        ("hypothesis", "selected_tables", "selected_figures"),
        "H1-H2-H3 core sections",
    )
    _require_columns(agent_upgrade, ("upgrade_id", "current_status"), "agent upgrade plan")

    thesis_facing = traceability[traceability["thesis_readiness"] == "thesis_facing_ready"]
    methods = thesis_facing[thesis_facing["item_type"] == "method"]
    interpretations = thesis_facing[thesis_facing["item_type"] == "interpretation"]
    method_ready = methods[
        _bool_series(methods["primary_artifact_exists"])
        & _positive_int_series(methods["literature_source_count"])
        & _positive_int_series(methods["known_literature_source_count"])
    ]
    interpretation_ready = interpretations[
        _bool_series(interpretations["primary_artifact_exists"])
        & _positive_int_series(interpretations["literature_source_count"])
        & _positive_int_series(interpretations["known_literature_source_count"])
        & _bool_series(interpretations["limitation_present"])
    ]
    core_package = package[_bool_series(package["include_in_core_package"])]
    active_agents = agent_upgrade[
        agent_upgrade["current_status"].astype(str).str.contains("active", case=False, na=False)
    ]
    inactive_agent_rows = int(len(agent_upgrade) - len(active_agents))
    core_hypotheses = "; ".join(core_sections["hypothesis"].astype(str).tolist())
    core_selected_tables = "; ".join(core_sections["selected_tables"].astype(str).tolist())
    core_selected_figures = "; ".join(core_sections["selected_figures"].astype(str).tolist())

    return {
        "method_rows": int(len(methods)),
        "method_ready_rows": int(len(method_ready)),
        "interpretation_rows": int(len(interpretations)),
        "interpretation_ready_rows": int(len(interpretation_ready)),
        "traceability_gap_rows": int((traceability["traceability_status"] == "traceability_gap").sum()),
        "core_table_rows": int((core_package["package_type"] == "table").sum()),
        "core_figure_rows": int((core_package["package_type"] == "figure").sum()),
        "package_gap_rows": int(
            package["package_traceability_status"].astype(str).str.contains("gap", case=False, na=False).sum()
        ),
        "ledger_rows": int(len(ledger)),
        "ledger_pending_rows": int((ledger["review_progress_state"] == "pending_manual_review").sum()),
        "ledger_final_ready_rows": int(_bool_series(ledger["final_citation_ready"]).sum()),
        "ledger_source_status_change_rows": int(
            _bool_series(ledger["source_status_change_allowed"]).sum()
        ),
        "ledger_preserved_rows": int(_bool_series(ledger["preserved_manual_fields"]).sum()),
        "core_section_rows": int(len(core_sections)),
        "core_hypotheses": core_hypotheses,
        "core_selected_tables": core_selected_tables,
        "core_selected_figures": core_selected_figures,
        "agent_upgrade_rows": int(len(agent_upgrade)),
        "active_agent_rows": int(len(active_agents)),
        "inactive_agent_rows": inactive_agent_rows,
    }


def _validate_summary(summary: dict[str, int | str]) -> None:
    if summary["method_rows"] == 0:
        raise ValueError("Source review protocol requires at least one thesis-facing method.")
    if summary["interpretation_rows"] == 0:
        raise ValueError("Source review protocol requires at least one thesis-facing interpretation.")
    if summary["method_ready_rows"] != summary["method_rows"]:
        raise ValueError("Not every thesis-facing method has artifact and source coverage.")
    if summary["interpretation_ready_rows"] != summary["interpretation_rows"]:
        raise ValueError("Not every thesis-facing interpretation has artifact, source, and limitation coverage.")
    if summary["traceability_gap_rows"] != 0:
        raise ValueError("Source review protocol cannot proceed with traceability gaps.")
    if summary["package_gap_rows"] != 0:
        raise ValueError("Source review protocol cannot proceed with result-package gaps.")
    if summary["core_table_rows"] == 0 or summary["core_figure_rows"] == 0:
        raise ValueError("Source review protocol requires curated core tables and figures.")
    if summary["ledger_rows"] == 0:
        raise ValueError("Source review protocol requires ledger rows.")
    if summary["ledger_source_status_change_rows"] != 0:
        raise ValueError("Source review protocol must not allow source-status changes.")
    if summary["core_section_rows"] != 3:
        raise ValueError("Source review protocol expects exactly H1, H2, and H3 core sections.")
    if summary["active_agent_rows"] != 0:
        raise ValueError("Source review protocol must not activate agent upgrade rows.")


def _validate_protocol(protocol: pd.DataFrame) -> None:
    _require_columns(protocol, PROTOCOL_COLUMNS, "source review progress protocol")
    if len(protocol) != 6:
        raise ValueError("Source review progress protocol must contain exactly 6 rows.")
    if protocol["protocol_id"].duplicated().any():
        raise ValueError("Source review progress protocol contains duplicate protocol_id values.")
    for column in PROTOCOL_COLUMNS:
        if protocol[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Source review progress protocol contains empty {column}.")
    joined = "\n".join(protocol.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Source review progress protocol must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "methoden",
        "interpretationen",
        "tabellen",
        "figuren",
        "source review",
        "keine quellenstatus-hochstufung",
        "keine finale zitation",
        "keine runtime-agenten",
        "llm_audit_log",
        "max 50 rows",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Source review progress protocol missing required terms: " + ", ".join(missing))


def _render_protocol_doc(protocol: pd.DataFrame) -> str:
    by_area = protocol["protocol_area"].value_counts().to_dict()
    return (
        "# Source Review Progress Protocol\n\n"
        "Dieses Protokoll ist eine deterministische Arbeitsanweisung fuer den "
        "Highlevel-Projektfortschritt. Es liest keine Quelleninhalte, berechnet "
        "keine Kennzahlen, promotet keinen Quellenstatus und aktiviert keine "
        "Runtime-Agenten. Es bindet Methoden, Interpretationen, Tabellen/Figuren, "
        "Source Review und spaetere Agentenverbesserungen an bestehende Artefakte.\n\n"
        "## Counts\n\n"
        f"- Protocol rows: {len(protocol)}\n"
        f"- Evidence mapping rows: {int(by_area.get('evidence_mapping', 0))}\n"
        f"- Result package rows: {int(by_area.get('result_package', 0))}\n"
        f"- Source review rows: {int(by_area.get('source_review_ledger', 0))}\n"
        f"- Final citation gate rows: {int(by_area.get('final_citation_gate', 0))}\n"
        f"- H1-H2-H3 drafting rows: {int(by_area.get('h1_h2_h3_drafting', 0))}\n"
        f"- Future agent rows: {int(by_area.get('future_agents', 0))}\n\n"
        "## Protocol Rows\n\n"
        + _markdown_table(protocol)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze dieses Protokoll als Reihenfolge fuer die naechste BA-Arbeit: "
        "erst Coverage pruefen, dann wenige Tabellen/Figuren einsetzen, dann "
        "Source Review im Ledger manuell fuehren, danach finale Zitationen "
        "freigeben und Agenten nur als Future Work beschreiben. Review-Access, "
        "Runtime-Agenten, MCP, Model Routing, Rohdaten-Prompts, Wallet-Adress-"
        "Exposition und Trading-Pfade bleiben deaktiviert.\n"
    )


def _protocol_row(
    *,
    protocol_id: str,
    protocol_area: str,
    source_artifact: str,
    deterministic_evidence_de: str,
    current_state: str,
    required_manual_action_de: str,
    thesis_use_rule_de: str,
    blocked_actions_de: str,
    next_safe_step_de: str,
) -> dict[str, object]:
    return {
        "protocol_id": protocol_id,
        "protocol_area": protocol_area,
        "source_artifact": source_artifact,
        "deterministic_evidence_de": deterministic_evidence_de,
        "current_state": current_state,
        "required_manual_action_de": required_manual_action_de,
        "thesis_use_rule_de": thesis_use_rule_de,
        "blocked_actions_de": blocked_actions_de,
        "next_safe_step_de": next_safe_step_de,
    }


def _bool_series(series: pd.Series) -> pd.Series:
    return series.map(_bool_value)


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "ja"}


def _positive_int_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0).astype(int).gt(0)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required source review progress protocol input missing: {path}")
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
