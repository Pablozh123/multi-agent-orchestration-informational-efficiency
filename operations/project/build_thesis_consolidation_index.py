"""Build a compact index of thesis-consolidation deliverables."""

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

INDEX_OUTPUT = "thesis_consolidation_index.csv"
INDEX_DOC_OUTPUT = "THESIS_CONSOLIDATION_INDEX.md"

INDEX_COLUMNS: tuple[str, ...] = (
    "artifact_id",
    "artifact_type",
    "path",
    "purpose_de",
    "use_now_de",
    "gate_or_limit_de",
)


@dataclass(frozen=True)
class ThesisConsolidationIndexResult:
    """Generated index paths and counts."""

    index_path: Path
    docs_path: Path
    index_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "index_path": str(self.index_path),
            "docs_path": str(self.docs_path),
            "index_rows": self.index_rows,
        }


def generate_thesis_consolidation_index(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> ThesisConsolidationIndexResult:
    """Generate the thesis-consolidation index CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)
    index = build_thesis_consolidation_index()
    _validate_index(index, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    index_path = results_dir / INDEX_OUTPUT
    docs_path = docs_dir / INDEX_DOC_OUTPUT
    index.to_csv(index_path, index=False)
    docs_path.write_text(_render_index_doc(index), encoding="utf-8")

    return ThesisConsolidationIndexResult(
        index_path=index_path,
        docs_path=docs_path,
        index_rows=len(index),
    )


def build_thesis_consolidation_index() -> pd.DataFrame:
    """Return the curated index of current thesis-consolidation artifacts."""

    rows = [
        _index_row(
            artifact_id="index_01_advisor_report_docx",
            artifact_type="advisor_deliverable",
            path="docs/project/dozentenbericht_ba_thesis.docx",
            purpose_de="Schriftlicher Zwischenstand fuer den Dozenten.",
            use_now_de="Direkt als Word-Update geben.",
            gate_or_limit_de="DOCX-Render-QA lokal nur moeglich, wenn LibreOffice/soffice verfuegbar ist.",
        ),
        _index_row(
            artifact_id="index_02_advisor_report_md",
            artifact_type="advisor_review_source",
            path="docs/project/dozentenbericht_ba_thesis.md",
            purpose_de="Transparente Markdown-Quelle des Dozentenberichts.",
            use_now_de="Inhalt schnell pruefen oder nach Word uebertragen.",
            gate_or_limit_de="Keine neuen Claims ohne Update der deterministischen Artefakte.",
        ),
        _index_row(
            artifact_id="index_03_advisor_questions",
            artifact_type="advisor_alignment",
            path="docs/project/DOZENTEN_ABSPRACHE_CHECKLIST.md",
            purpose_de="Acht konkrete Fragen fuer die naechste Dozentenabstimmung.",
            use_now_de="Als Gespraechsagenda nutzen.",
            gate_or_limit_de="Dient Scope-Klaerung, nicht Empirie-Erweiterung.",
        ),
        _index_row(
            artifact_id="index_04_highlevel_view",
            artifact_type="project_status",
            path="docs/research/THESIS_PROJECT_HIGHLEVEL_VIEW.md",
            purpose_de="Statusmatrix ueber Projektteile, Entscheidungen und Gates.",
            use_now_de="Highlevel-Orientierung fuer Projektfortschritt.",
            gate_or_limit_de="Review-Access bleibt pausiert; Agenten bleiben documentation-only.",
        ),
        _index_row(
            artifact_id="index_05_next_work_plan",
            artifact_type="work_plan",
            path="docs/research/THESIS_NEXT_WORK_PLAN.md",
            purpose_de="Priorisierte Workstreams von Source Review bis finaler QA.",
            use_now_de="Naechste Arbeitsschritte sequenzieren.",
            gate_or_limit_de="Kein Scope-Ausbau vor geschriebenem H1-H3-Kern.",
        ),
        _index_row(
            artifact_id="index_06_execution_checklist",
            artifact_type="execution_plan",
            path="docs/project/THESIS_EXECUTION_CHECKLIST.md; data/results/thesis_execution_checklist.csv",
            purpose_de="Kapitelweise Schreib- und Abnahmecheckliste aus der Highlevel-View.",
            use_now_de="Nach Dozentenfeedback Kapitel, Inputs, Gates und Done-Kriterien abarbeiten.",
            gate_or_limit_de="Review-Access bleibt pausiert; keine Runtime-Agenten oder Rohartefakt-Dumps.",
        ),
        _index_row(
            artifact_id="index_07_chapter_source_bindings",
            artifact_type="chapter_source_bindings",
            path="docs/project/THESIS_CHAPTER_SOURCE_BINDINGS.md; data/results/thesis_chapter_source_bindings.csv",
            purpose_de="Kapitel-zu-Evidence-zu-Quelle-Matrix fuer die BA-Gliederung.",
            use_now_de="Beim Schreiben je Kapitel Quellen, Artefakte, Tabellen/Figuren und Gates pruefen.",
            gate_or_limit_de="Keine thesis-facing Claims ohne Human Review, Artefaktverweis, Limitation und Wording Guard.",
        ),
        _index_row(
            artifact_id="index_08_source_worksheet",
            artifact_type="source_review",
            path="docs/research/THESIS_SOURCE_REVIEW_WORKSHEET.md",
            purpose_de="Manuelle Quellenreview-Zeilen mit Evidence IDs und Pending-Feldern.",
            use_now_de="Quellen mit Seiten-/Abschnittsnotizen pruefen.",
            gate_or_limit_de="Quellenstatus nicht automatisch hochstufen.",
        ),
        _index_row(
            artifact_id="index_09_source_review_execution",
            artifact_type="source_review_execution",
            path="docs/project/THESIS_SOURCE_REVIEW_EXECUTION.md; data/results/thesis_source_review_execution.csv",
            purpose_de="Manuelle Reihenfolge fuer Quellenreview, Output und Completion Gates.",
            use_now_de="Priority-1-Quellen source-by-source abarbeiten.",
            gate_or_limit_de="Quellenstatus nicht automatisch hochstufen; blocked Quellen nicht fuer thesis-facing Claims nutzen.",
        ),
        _index_row(
            artifact_id="index_10_wording_guard",
            artifact_type="drafting_guard",
            path="docs/research/THESIS_WORDING_GUARD.md",
            purpose_de="Erlaubtes und blockiertes deutsches Thesis-Wording je Evidence ID.",
            use_now_de="Beim Schreiben der Kapitel als Claim-Grenze nutzen.",
            gate_or_limit_de="Keine Formulierung ohne Artefakt und Limitation uebernehmen.",
        ),
        _index_row(
            artifact_id="index_11_table_figure_captions",
            artifact_type="result_package",
            path="docs/research/THESIS_TABLE_FIGURE_CAPTIONS.md",
            purpose_de="Beschriftungen, Quellen- und Limitationstexte fuer Tabellen/Figuren.",
            use_now_de="5 Kern-Tabellen und 4 Kern-Figuren in die Thesis einbauen.",
            gate_or_limit_de="Keine Rohartefakt-Dumps in den Haupttext.",
        ),
        _index_row(
            artifact_id="index_12_chapter_draft",
            artifact_type="chapter_draft",
            path="docs/research/THESIS_CHAPTER_DRAFT.md",
            purpose_de="Erster deutschsprachiger Kapitelentwurf aus der Konsolidierung.",
            use_now_de="Als Rohfassung fuer BA-Kapitel nutzen.",
            gate_or_limit_de="Vor finaler Abgabe Quellenreview und Wording Guard anwenden.",
        ),
        _index_row(
            artifact_id="index_13_source_review_plan",
            artifact_type="source_review",
            path="docs/research/THESIS_SOURCE_REVIEW_PLAN.md",
            purpose_de="Priorisierte Quellenreview-Planung nach Quelle.",
            use_now_de="Quelle-fuer-Quelle abarbeiten.",
            gate_or_limit_de="Candidate/rejected Quellen nicht fuer thesis-facing Claims nutzen.",
        ),
        _index_row(
            artifact_id="index_14_agent_protocol",
            artifact_type="future_work",
            path="docs/research/THESIS_AGENT_ASSISTANCE_PROTOCOL.md",
            purpose_de="Dokumentations-only Agenten-Ausblick mit erlaubten Rollen und Gates.",
            use_now_de="Nur als Future-Work-Abschnitt nutzen.",
            gate_or_limit_de="Keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken und keine Trading-Pfade.",
        ),
        _index_row(
            artifact_id="index_15_agent_future_handoff",
            artifact_type="future_work",
            path="docs/project/THESIS_AGENT_FUTURE_WORK_HANDOFF.md; data/results/thesis_agent_future_work_handoff.csv",
            purpose_de="Future-Work-Handoff fuer spaetere Assistenz-Agenten nach Gates.",
            use_now_de="Nur als Highlevel-Ausblick fuer Pipeline-Verbesserungen nutzen.",
            gate_or_limit_de="Keine Aktivierung ohne separates Goal, Tests, bounded inputs und llm_audit_log.",
        ),
        _index_row(
            artifact_id="index_16_agent_pipeline_control",
            artifact_type="agent_pipeline_control",
            path="docs/project/THESIS_AGENT_PIPELINE_CONTROL_AUDIT.md; data/results/thesis_agent_pipeline_control_audit.csv",
            purpose_de="Kontrollaudit fuer spaetere Agentenrollen ohne Runtime-Aktivierung.",
            use_now_de="Zeigt, wie Agenten spaeter Source Review, Drafting und Wording pruefen koennten.",
            gate_or_limit_de="0 aktive Zeilen; keine Runtime-Agenten, kein MCP, kein Model Routing und keine LLM-Metriken.",
        ),
        _index_row(
            artifact_id="index_17_advisor_handoff_package",
            artifact_type="advisor_handoff",
            path="docs/project/THESIS_ADVISOR_HANDOFF_PACKAGE.md; data/results/thesis_advisor_handoff_package.csv",
            purpose_de="Geordnete Liste der Dateien fuer Dozentenabgabe und Abstimmung.",
            use_now_de="Zeigt, was dem Dozenten zuerst gegeben und womit danach gearbeitet wird.",
            gate_or_limit_de="Handoff-Uebersicht, kein neues empirisches Resultat.",
        ),
        _index_row(
            artifact_id="index_18_advisor_handoff_note",
            artifact_type="advisor_handoff_note",
            path="docs/project/DOZENTEN_UEBERGABE_TEXT.md; data/results/thesis_advisor_handoff_note.csv",
            purpose_de="Kurzer Mail- oder Chat-Text fuer die Dozentenuebergabe.",
            use_now_de="Als Begleittext zum Word-Bericht und zur Absprache-Checklist nutzen.",
            gate_or_limit_de="Zwischenstand, kein finales Abgabe- oder Quellenreview-Signal.",
        ),
        _index_row(
            artifact_id="index_19_advisor_feedback_log",
            artifact_type="advisor_feedback_log",
            path="docs/project/DOZENTEN_FEEDBACK_LOG.md; data/results/thesis_advisor_feedback_log_template.csv",
            purpose_de="Pending-Log fuer Dozentenfeedback, Entscheidungen und Folgecommits.",
            use_now_de="Nach der Betreuung Feedback, Entscheidung und kleine Folgeaktion eintragen.",
            gate_or_limit_de="Alle Eintraege bleiben pending, bis der Dozent Feedback gegeben hat.",
        ),
        _index_row(
            artifact_id="index_20_submission_readiness",
            artifact_type="submission_readiness",
            path="docs/project/THESIS_SUBMISSION_READINESS_BOARD.md; data/results/thesis_submission_readiness_board.csv",
            purpose_de="Gate-Board fuer draft-ready, final-blocked und deferred Thesis-Schritte.",
            use_now_de="Vor finalem Export Source Review, Swiss Resultat, DOCX Render-QA und Agentenstatus pruefen.",
            gate_or_limit_de="Finale Abgabe bleibt blockiert, solange Source Review, Swiss-Gate oder Render-QA offen sind.",
        ),
        _index_row(
            artifact_id="index_21_drafting_sequence",
            artifact_type="drafting_sequence",
            path="docs/project/THESIS_DRAFTING_SEQUENCE.md; data/results/thesis_drafting_sequence.csv",
            purpose_de="Konkrete Schreibreihenfolge aus Work Plan, Readiness Board und Kapitelbindungen.",
            use_now_de="Als naechste Arbeitsreihenfolge nach Dozenten-Handoff und Highlevel-View nutzen.",
            gate_or_limit_de="Trennt Draft-Arbeit von Source Review, Swiss-Gate, DOCX-Render-QA und Future-Work-Agenten.",
        ),
        _index_row(
            artifact_id="index_22_source_access_audit",
            artifact_type="source_access_audit",
            path="docs/project/THESIS_SOURCE_ACCESS_AUDIT.md; data/results/thesis_source_access_audit.csv",
            purpose_de="Zugriffs-Audit fuer lokale und externe Quellen vor manueller Quellenpruefung.",
            use_now_de="Zeigt, welche Priority-1-Quellen lokal geoeffnet und welche extern geprueft werden muessen.",
            gate_or_limit_de="Keine Quellenstatus-Hochstufung, keine automatischen Page Notes und keine finale Zitation.",
        ),
        _index_row(
            artifact_id="index_23_source_structure_inventory",
            artifact_type="source_structure_inventory",
            path="docs/project/THESIS_SOURCE_STRUCTURE_INVENTORY.md; data/results/thesis_source_structure_inventory.csv",
            purpose_de="Lokales Strukturinventar fuer PDF/HTML-Quellen vor manueller Quellenpruefung.",
            use_now_de="Zeigt Seiten- und Strukturhinweise, ohne Quelleninhalte zu interpretieren.",
            gate_or_limit_de="Keine Inhaltsinterpretation, keine Quellenstatus-Hochstufung und keine thesis-facing Claims.",
        ),
        _index_row(
            artifact_id="index_24_source_review_decision_packets",
            artifact_type="source_review_decision_packets",
            path="docs/project/THESIS_SOURCE_REVIEW_DECISION_PACKETS.md; data/results/thesis_source_review_decision_packets.csv",
            purpose_de="Manuelle Entscheidungspakete fuer Evidence-Source-Zeilen vor finaler Zitation.",
            use_now_de="Fuehrt Page-/Section-Note, Claim-Support-Entscheid und Blocked-Wording-Check je Paket.",
            gate_or_limit_de="Alle Zeilen bleiben pending; keine finale Zitation und keine Quellenstatus-Hochstufung.",
        ),
        _index_row(
            artifact_id="index_25_h1_h2_h3_source_review_notes",
            artifact_type="h1_h2_h3_source_review_notes",
            path="docs/project/THESIS_H1_H2_H3_SOURCE_REVIEW_NOTES.md; data/results/thesis_h1_h2_h3_source_review_notes.csv",
            purpose_de="Bounded Source-Review-Notizen fuer den empirischen BA-Kern H1, H2 und H3.",
            use_now_de="Page-/Section-Notes, Claim-Support-Entscheide und Blocked-Wording-Checks fuer H1-H2-H3 priorisieren.",
            gate_or_limit_de="Keine Quellenstatus-Hochstufung, keine finale Zitation und keine neuen Claims aus Metadaten oder Dateistruktur.",
        ),
        _index_row(
            artifact_id="index_26_source_review_progress_ledger",
            artifact_type="source_review_progress_ledger",
            path="docs/project/THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md; data/results/thesis_source_review_progress_ledger.csv",
            purpose_de="Fortschrittsledger fuer manuelle H1-H2-H3 Source-Review-Entscheide.",
            use_now_de="Manuelle Page-/Section-Notes, Claim-Support, Blocked-Wording und Citation-Use-Entscheide ueber Regenerationen erhalten.",
            gate_or_limit_de="Keine Quellenstatus-Hochstufung, keine finale Zitation durch den Ledger und keine automatisierte Quelleninterpretation.",
        ),
        _index_row(
            artifact_id="index_27_source_review_progress_protocol",
            artifact_type="source_review_progress_protocol",
            path="docs/project/THESIS_SOURCE_REVIEW_PROGRESS_PROTOCOL.md; data/results/thesis_source_review_progress_protocol.csv",
            purpose_de="Deterministisches Protokoll fuer Coverage, Resultatpaket, Ledger, finale Zitation und Agent-Grenzen.",
            use_now_de="Als Reihenfolge fuer H1-H2-H3 Source Review, Tabellen/Figuren-Integration und spaetere Agenten-Future-Work nutzen.",
            gate_or_limit_de="Keine Quelleninterpretation, keine Quellenstatus-Hochstufung, keine finale Zitation und keine Runtime-Agenten.",
        ),
        _index_row(
            artifact_id="index_28_traceability_audit",
            artifact_type="traceability_audit",
            path="docs/project/THESIS_TRACEABILITY_AUDIT.md; data/results/thesis_method_interpretation_traceability.csv; data/results/thesis_result_package_traceability.csv",
            purpose_de="Draft-Kontrolle fuer Methoden, Interpretationen, Tabellen und Figuren.",
            use_now_de="Prueft Artefakt-, Quellen-, Limitation- und Caption-Mapping vor dem BA-Schreiben.",
            gate_or_limit_de="Keine finalen Zitationen ohne manuelle Quellenreview und keine neuen Kennzahlen.",
        ),
        _index_row(
            artifact_id="index_29_h1_h2_h3_core_sections",
            artifact_type="core_writing_package",
            path="docs/research/THESIS_H1_H2_H3_CORE_SECTIONS.md; data/results/thesis_h1_h2_h3_core_sections.csv",
            purpose_de="Thesis-ready Kernfassung fuer H1, H2 und H3 mit Evidence-IDs, Quellen, Artefakten, Tabellen und Figuren.",
            use_now_de="Direkt als Schreibkern fuer die BA-Ergebniskapitel nutzen.",
            gate_or_limit_de="Keine finale Zitation ohne Source Review; keine Rohartefakt-Dumps und keine neuen Kennzahlen.",
        ),
        _index_row(
            artifact_id="index_30_agent_pipeline_upgrade_plan",
            artifact_type="future_agent_upgrade_plan",
            path="docs/research/THESIS_AGENT_PIPELINE_UPGRADE_PLAN.md; data/results/thesis_agent_pipeline_upgrade_plan.csv",
            purpose_de="Dokumentations-only Plan, wie spaetere Agenten Source Review, Drafting, Wording und Tabellen/Figuren pruefen koennten.",
            use_now_de="Nur als Future-Work-Gedanke nach dem H1-H2-H3-Schreibkern nutzen.",
            gate_or_limit_de="Keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken, bounded inputs und llm_audit_log vor jeder Aktivierung.",
        ),
        _index_row(
            artifact_id="index_31_goal_completion_audit",
            artifact_type="goal_completion_audit",
            path="docs/project/THESIS_GOAL_COMPLETION_AUDIT.md; data/results/thesis_goal_completion_audit.csv",
            purpose_de="Belegbarer Audit des aktiven Goals mit erreichten Punkten und offenen Gates.",
            use_now_de="Als Stop-/Weiterarbeitskontrolle vor finalen Abschlussclaims nutzen.",
            gate_or_limit_de="Kein Zielabschluss, solange Source Review, Swiss Resultat-Gate oder DOCX-Render-QA offen sind.",
        ),
        _index_row(
            artifact_id="index_32_status_and_log",
            artifact_type="project_control",
            path="STATUS.md; docs/project/WORK_LOG.md",
            purpose_de="Automatisierter Projektstatus und append-only Arbeitslog.",
            use_now_de="Vor jedem Stop und Commit pruefen.",
            gate_or_limit_de="Nicht behaupten, dass Phase bereit ist, wenn Checks fehlschlagen.",
        ),
    ]
    return pd.DataFrame(rows, columns=INDEX_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_thesis_consolidation_index(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _index_row(
    *,
    artifact_id: str,
    artifact_type: str,
    path: str,
    purpose_de: str,
    use_now_de: str,
    gate_or_limit_de: str,
) -> dict[str, object]:
    return {
        "artifact_id": artifact_id,
        "artifact_type": artifact_type,
        "path": path,
        "purpose_de": purpose_de,
        "use_now_de": use_now_de,
        "gate_or_limit_de": gate_or_limit_de,
    }


def _validate_index(index: pd.DataFrame, *, repo_root: Path) -> None:
    _require_columns(index, INDEX_COLUMNS, "thesis consolidation index")
    if index["artifact_id"].duplicated().any():
        raise ValueError("Thesis consolidation index contains duplicate artifact_id values.")
    for row in index.to_dict(orient="records"):
        for path in str(row["path"]).split(";"):
            clean_path = path.strip()
            if clean_path and not (repo_root / clean_path).exists():
                raise FileNotFoundError(f"Indexed artifact is missing: {clean_path}")
    joined = "\n".join(index.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Thesis consolidation index must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "dozentenbericht",
        "review-access bleibt pausiert",
        "keine runtime-agenten",
        "quellenstatus nicht automatisch hochstufen",
        "keine roh",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Thesis consolidation index missing required terms: " + ", ".join(missing))


def _render_index_doc(index: pd.DataFrame) -> str:
    return (
        "# Thesis Consolidation Index\n\n"
        "Dieser Index zeigt, welche Artefakte fuer den aktuellen Highlevel-"
        "Projektstand, den Dozentenbericht, Source Review, Wording Guard, "
        "Advisor Handoff Package, Advisor Handoff Note, Advisor Feedback Log, "
        "Submission Readiness Board, Drafting Sequence, Execution Checklist, "
        "Chapter Source Bindings, Source Review Execution, Source Access "
        "Audit, Source Structure Inventory, Source Review Decision Packets, "
        "H1-H2-H3 Source Review Notes, Source Review Progress Ledger, "
        "Source Review Progress Protocol, Traceability Audit, H1-H2-H3 Core Sections, Agent Pipeline Upgrade "
        "Plan, Goal Completion Audit, Agent Future-Work Handoff, Agent Pipeline Control Audit, Tabellen/Figuren und "
        "Future-Work-Agenten relevant sind.\n\n"
        "## Counts\n\n"
        f"- Indexed artifacts: {len(index)}\n\n"
        "## Artifact Index\n\n"
        + _markdown_table(index)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze zuerst den Dozentenbericht und die Absprache-Checklist fuer die "
        "Betreuung. Nutze das Advisor Handoff Package als Abgabe- und "
        "Gespraechsreihenfolge. Nutze den Uebergabetext als kurze Mail- oder "
        "Chat-Vorlage. Nutze das Feedback-Log nach der Betreuung. Nutze das "
        "Submission Readiness Board fuer die "
        "finalen Gates. Nutze die Drafting Sequence fuer die naechste "
        "Schreibreihenfolge. Nutze das Source Access Audit und Source Structure "
        "Inventory sowie Source Review Decision Packets vor der manuellen "
        "Quellenpruefung. Nutze die H1-H2-H3 Source Review Notes fuer den "
        "empirischen BA-Kern und den Source Review Progress Ledger fuer "
        "manuelle Fortschrittsentscheide. Nutze das Source Review Progress "
        "Protocol als Reihenfolge fuer Coverage, Resultatpaket, Source Review "
        "und Future-Agent-Grenzen. Nutze den Traceability Audit als BA-Schreibkontrolle. "
        "Nutze die H1-H2-H3 Core Sections als Schreibkern und den Agent "
        "Pipeline Upgrade Plan nur als Future-Work-Gedanke. Nutze das Goal Completion Audit als Stop- und "
        "Weiterarbeitskontrolle. Nutze danach Execution Checklist, Source "
        "Worksheet, Chapter Source Bindings, Source Review Execution, Agent "
        "Future-Work Handoff, Agent Pipeline Control Audit, Wording Guard und Next Work Plan fuer das "
        "Schreiben. "
        "Review-Access, Runtime-Agenten, MCP, Model Routing, Rohdatenzugriff "
        "und Trading-Pfade bleiben deaktiviert.\n"
    )


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
