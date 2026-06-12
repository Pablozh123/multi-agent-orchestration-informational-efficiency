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
            purpose_de="Deutschsprachiger BA-Kapitelentwurf mit Source-Gated Integration fuer H1, H2 und H3.",
            use_now_de="Als Hauptentwurf fuer die empirischen BA-Kapitel nutzen.",
            gate_or_limit_de="Bounded Draft ja; finale Source Review, Zitation und Wording Guard bleiben offen.",
        ),
        _index_row(
            artifact_id="index_13_h1_h2_h3_bounded_chapter_draft",
            artifact_type="bounded_chapter_draft",
            path="docs/research/THESIS_H1_H2_H3_BOUNDED_CHAPTER_DRAFT.md; data/results/thesis_h1_h2_h3_bounded_chapter_draft.csv",
            purpose_de="Geordnete H1-H2-H3 Prosa-Bausteine fuer Methode, Resultat, Interpretation, Tabelle/Figur, Source-Gate und Future-Agent-Grenze.",
            use_now_de="Direkt als bounded Schreibvorlage fuer den empirischen BA-Kern nutzen.",
            gate_or_limit_de="Keine finale Zitation, keine Rohartefakt-Dumps, keine neuen Kennzahlen und keine Runtime-Agenten.",
        ),
        _index_row(
            artifact_id="index_13_h1_h2_h3_source_gated_writing_pass",
            artifact_type="source_gated_writing_pass",
            path="docs/research/THESIS_H1_H2_H3_SOURCE_GATED_WRITING_PASS.md; data/results/thesis_h1_h2_h3_source_gated_writing_pass.csv",
            purpose_de="Zusammenhaengender H1-H2-H3 Schreibpass aus bounded Draft, Source Coverage, wenigen Tabellen/Figuren und Source Review Gates.",
            use_now_de="Als unmittelbare Grundlage fuer die H1-H2-H3 Ergebniskapitel nutzen.",
            gate_or_limit_de="Bounded Draft ja; keine finale Zitation, keine Quellenstatus-Hochstufung und keine Runtime-Agenten.",
        ),
        _index_row(
            artifact_id="index_13_h1_h2_h3_source_gated_thesis_drafting_pass",
            artifact_type="source_gated_thesis_drafting_pass",
            path="docs/research/THESIS_H1_H2_H3_SOURCE_GATED_THESIS_DRAFTING_PASS.md; data/results/thesis_h1_h2_h3_source_gated_thesis_drafting_pass.csv",
            purpose_de="Paragraphenweise H1-H2-H3 BA-Schreibreihenfolge aus Source-Gated Writing Pass und Manual Source Review Execution Pass.",
            use_now_de="Als konkrete naechste Schreibreihenfolge fuer Methode/Resultat, Interpretation, Tabelle/Figur, Manual Source Review und Finalgate nutzen.",
            gate_or_limit_de="Bounded Draft ja; nicht final-submission-ready, keine finale Zitation, keine Rohartefakt-Dumps und keine Runtime-Agenten.",
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
            artifact_id="index_19_advisor_feedback_integration",
            artifact_type="advisor_feedback_integration",
            path="docs/project/DOZENTEN_FEEDBACK_INTEGRATION_CHECKLIST.md; data/results/thesis_advisor_feedback_integration_checklist.csv",
            purpose_de="Uebersetzt spaeteres Dozentenfeedback in kleine Folgecommits mit Quellen-, Artefakt-, Tabellen/Figuren- und Agent-Gates.",
            use_now_de="Nach ausgefuelltem Feedback-Log je Feedbackpunkt genau einen passenden Integrations-Scope waehlen.",
            gate_or_limit_de="Pending bis Feedback vorliegt; keine neuen Claims, keine Runtime-Agenten und keine Rohartefakt-Dumps.",
        ),
        _index_row(
            artifact_id="index_19_advisor_source_review_followup",
            artifact_type="advisor_source_review_followup",
            path="docs/project/THESIS_ADVISOR_SOURCE_REVIEW_FOLLOWUP.md; data/results/thesis_advisor_source_review_followup.csv",
            purpose_de="Ordnet Dozentenfeedback, Source-Review-Tiefe, H1-H2-H3 Manual Source Review, bounded Draft, Final-Gates und Agent-Future-Work in eine naechste Reihenfolge.",
            use_now_de="Nach dem Dozenten-Handoff als konkrete Follow-up-Reihenfolge nutzen.",
            gate_or_limit_de="Keine finale Zitation, keine Quellenstatus-Hochstufung, kein Review-Access und keine Runtime-Agenten.",
        ),
        _index_row(
            artifact_id="index_19_h1_manual_source_review_followup",
            artifact_type="h1_manual_source_review_followup",
            path="docs/project/THESIS_H1_MANUAL_SOURCE_REVIEW_FOLLOWUP.md; data/results/thesis_h1_manual_source_review_followup.csv",
            purpose_de="H1-spezifische manuelle Source-Review-Starterliste fuer 10 H1-Zeilen mit Quellen, Evidence IDs, Artefakten und offenen Reviewer-Feldern.",
            use_now_de="Als naechsten H1-Review-Slice nutzen: Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use je Zeile erfassen.",
            gate_or_limit_de="Keine finale Zitation, keine Quellenstatus-Hochstufung, keine Rohartefakt-Dumps und keine Runtime-Agenten.",
        ),
        _index_row(
            artifact_id="index_19_h1_source_review_decision_queue",
            artifact_type="h1_source_review_decision_queue",
            path="docs/project/THESIS_H1_SOURCE_REVIEW_DECISION_QUEUE.md; data/results/thesis_h1_source_review_decision_queue.csv",
            purpose_de="Verdichtet H1 auf 10 konkrete Review-Entscheidungszeilen mit Quelle, Evidence ID, Artefakt, T2/F1, Zugriffspfad und manuellen Entscheidungsfeldern.",
            use_now_de="Als direkte H1-Review-Queue nutzen, bevor H1 final zitiert oder in finale BA-Prosa ueberfuehrt wird.",
            gate_or_limit_de="Keine Quelleninhaltsinterpretation, keine finale Zitation, keine Quellenstatus-Hochstufung und keine Runtime-Agenten.",
        ),
        _index_row(
            artifact_id="index_19_h2_manual_source_review_followup",
            artifact_type="h2_manual_source_review_followup",
            path="docs/project/THESIS_H2_MANUAL_SOURCE_REVIEW_FOLLOWUP.md; data/results/thesis_h2_manual_source_review_followup.csv",
            purpose_de="H2-spezifische manuelle Source-Review-Starterliste fuer 5 H2-Zeilen mit Event-Window-Quelle, Evidence IDs, Artefakt und offenen Reviewer-Feldern.",
            use_now_de="Als naechsten H2-Review-Slice nutzen: Page-/Section-Note, Claim-Support, Blocked-Wording, Citation-Use und Kausalclaim-Grenze je Zeile erfassen.",
            gate_or_limit_de="Keine finale Zitation, keine Kausalclaims, keine Quellenstatus-Hochstufung, keine Rohartefakt-Dumps und keine Runtime-Agenten.",
        ),
        _index_row(
            artifact_id="index_19_h2_source_review_decision_queue",
            artifact_type="h2_source_review_decision_queue",
            path="docs/project/THESIS_H2_SOURCE_REVIEW_DECISION_QUEUE.md; data/results/thesis_h2_source_review_decision_queue.csv",
            purpose_de="Verdichtet H2 auf 5 konkrete Review-Entscheidungszeilen mit Quelle, Evidence ID, Artefakt, T3/F2, Zugriffspfad, Kausalclaim-Grenze und manuellen Entscheidungsfeldern.",
            use_now_de="Als direkte H2-Review-Queue nutzen, bevor H2 final zitiert oder in finale BA-Prosa ueberfuehrt wird.",
            gate_or_limit_de="Keine Intraday- oder Kausalclaims, keine Quelleninhaltsinterpretation, keine finale Zitation, keine Quellenstatus-Hochstufung und keine Runtime-Agenten.",
        ),
        _index_row(
            artifact_id="index_19_h3_manual_source_review_followup",
            artifact_type="h3_manual_source_review_followup",
            path="docs/project/THESIS_H3_MANUAL_SOURCE_REVIEW_FOLLOWUP.md; data/results/thesis_h3_manual_source_review_followup.csv",
            purpose_de="H3-spezifische manuelle Source-Review-Starterliste fuer 8 H3-Zeilen mit Wallet-, Granger-, Evidence-, Artefakt- und Reviewer-Gates.",
            use_now_de="Als naechsten H3-Review-Slice nutzen: Page-/Section-Note, Claim-Support, Blocked-Wording, Citation-Use, Granger-Grenze und Wallet-Grenze je Zeile erfassen.",
            gate_or_limit_de="Keine finale Zitation, keine Kausalclaims, keine willkuerlichen Whale-Schwellen, keine Wallet-Adressen, keine Trading-Claims und keine Runtime-Agenten.",
        ),
        _index_row(
            artifact_id="index_19_manual_source_review_followup_overview",
            artifact_type="manual_source_review_followup_overview",
            path="docs/project/THESIS_MANUAL_SOURCE_REVIEW_FOLLOWUP_OVERVIEW.md; data/results/thesis_manual_source_review_followup_overview.csv",
            purpose_de="Kompakte H1-H2-H3 Uebersicht ueber 23 manuelle Source-Review-Zeilen, Quellen, Methodik-/Interpretationszeilen und offene Finalgates.",
            use_now_de="Als Steuerungsuebersicht nutzen, bevor H1, H2 und H3 source-by-source im Ledger entschieden werden.",
            gate_or_limit_de="Alle 23 Zitationen bleiben final blockiert; keine Quellenstatus-Hochstufung, keine Kausalclaims, keine Runtime-Agenten und keine Rohartefakt-Dumps.",
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
            artifact_id="index_26_h1_h2_h3_manual_source_review_execution_pass",
            artifact_type="manual_source_review_execution_pass",
            path="docs/project/THESIS_H1_H2_H3_MANUAL_SOURCE_REVIEW_EXECUTION_PASS.md; data/results/thesis_h1_h2_h3_manual_source_review_execution_pass.csv",
            purpose_de="Geordnete manuelle H1-H2-H3 Source-Review-Ausfuehrungsliste aus Ledger, Notes, Decision Packets, Coverage, Handoff und Tabellen/Figurenkontext.",
            use_now_de="Als konkrete source-by-source Arbeitsliste fuer Page-/Section-Notes, Claim-Support, Blocked-Wording und Citation-Use nutzen.",
            gate_or_limit_de="Keine Quellenstatus-Hochstufung, keine finale Zitation, keine Rohartefakt-Dumps und keine Runtime-Agenten.",
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
            artifact_id="index_28_source_review_chapter_handoff",
            artifact_type="source_review_chapter_handoff",
            path="docs/project/THESIS_SOURCE_REVIEW_CHAPTER_HANDOFF.md; data/results/thesis_source_review_chapter_handoff.csv",
            purpose_de="Kapitelweiser Handoff fuer H1-H2-H3 mit Evidence IDs, Literatur IDs, Artefakten, Tabellen/Figuren und offenen Source-Review-Zeilen.",
            use_now_de="Beim Schreiben der empirischen Kapitel als kompakte Abnahme- und Uebergabeliste nutzen.",
            gate_or_limit_de="Keine finale Zitation, keine Rohartefakt-Dumps, keine Quellenstatus-Hochstufung und keine Runtime-Agenten.",
        ),
        _index_row(
            artifact_id="index_29_chapter_source_review_checklist",
            artifact_type="chapter_source_review_checklist",
            path="docs/project/THESIS_CHAPTER_SOURCE_REVIEW_CHECKLIST.md; data/results/thesis_chapter_source_review_checklist.csv",
            purpose_de="Kapitelweise manuelle Checkliste fuer H1-H2-H3 Coverage, Literaturreview, Resultatpaket, Wording, Zitation und Agentengrenze.",
            use_now_de="Als Abhakliste beim Schreiben und Pruefen der empirischen BA-Kapitel nutzen.",
            gate_or_limit_de="Bounded Draft ja; finale Zitation bleibt blockiert, solange Ledger-Zeilen pending sind.",
        ),
        _index_row(
            artifact_id="index_30_h1_h2_h3_drafting_checklist",
            artifact_type="h1_h2_h3_drafting_checklist",
            path="docs/project/THESIS_H1_H2_H3_DRAFTING_CHECKLIST.md; data/results/thesis_h1_h2_h3_drafting_checklist.csv",
            purpose_de="Konkrete Schreibreihenfolge fuer H1-H2-H3 mit Methode, Resultat, Interpretation, Tabelle/Figur, Source-Gate und Agentengrenze.",
            use_now_de="Als Drafting-Checkliste fuer die empirischen Kernkapitel nutzen.",
            gate_or_limit_de="Bounded Draft ja; keine neue Kennzahl, keine Rohartefakt-Dumps und keine finale Zitation vor Source Review.",
        ),
        _index_row(
            artifact_id="index_31_thesis_final_gate_board",
            artifact_type="final_gate_board",
            path="docs/project/THESIS_FINAL_GATE_BOARD.md; data/results/thesis_final_gate_board.csv",
            purpose_de="Highlevel-Stop-/Go-Board fuer bounded Draft, finale Abgabereife, Evidenzzaehlung und offene Finalgates.",
            use_now_de="Vor weiteren Completion-Claims pruefen: Source Review, Swiss Resultat, DOCX Render-QA, Projektchecks und Agentengrenzen.",
            gate_or_limit_de="Draft ja; finale Abgabe nein, solange Source Review, Swiss official result, DOCX-Render-QA oder finale Projektchecks offen sind.",
        ),
        _index_row(
            artifact_id="index_32_traceability_audit",
            artifact_type="traceability_audit",
            path="docs/project/THESIS_TRACEABILITY_AUDIT.md; data/results/thesis_method_interpretation_traceability.csv; data/results/thesis_result_package_traceability.csv",
            purpose_de="Draft-Kontrolle fuer Methoden, Interpretationen, Tabellen und Figuren.",
            use_now_de="Prueft Artefakt-, Quellen-, Limitation- und Caption-Mapping vor dem BA-Schreiben.",
            gate_or_limit_de="Keine finalen Zitationen ohne manuelle Quellenreview und keine neuen Kennzahlen.",
        ),
        _index_row(
            artifact_id="index_32_method_interpretation_source_coverage",
            artifact_type="method_interpretation_source_coverage",
            path="docs/project/THESIS_METHOD_INTERPRETATION_SOURCE_COVERAGE.md; data/results/thesis_method_interpretation_source_coverage.csv",
            purpose_de="Flaches Coverage-Audit fuer jede Methoden-/Interpretationsquelle gegen Literaturindex und deterministisches Primaerartefakt.",
            use_now_de="Vor BA-Schreiben und Dozentenfeedback-Follow-up pruefen, ob jede Methode und Interpretation Quellen-/Artefaktbindung behaelt.",
            gate_or_limit_de="Keine Quellenstatus-Hochstufung, keine Quelleninhaltsinterpretation und keine finale Zitation aus diesem Audit.",
        ),
        _index_row(
            artifact_id="index_33_h1_h2_h3_core_sections",
            artifact_type="core_writing_package",
            path="docs/research/THESIS_H1_H2_H3_CORE_SECTIONS.md; data/results/thesis_h1_h2_h3_core_sections.csv",
            purpose_de="Thesis-ready Kernfassung fuer H1, H2 und H3 mit Evidence-IDs, Quellen, Artefakten, Tabellen und Figuren.",
            use_now_de="Direkt als Schreibkern fuer die BA-Ergebniskapitel nutzen.",
            gate_or_limit_de="Keine finale Zitation ohne Source Review; keine Rohartefakt-Dumps und keine neuen Kennzahlen.",
        ),
        _index_row(
            artifact_id="index_34_agent_pipeline_upgrade_plan",
            artifact_type="future_agent_upgrade_plan",
            path="docs/research/THESIS_AGENT_PIPELINE_UPGRADE_PLAN.md; data/results/thesis_agent_pipeline_upgrade_plan.csv",
            purpose_de="Dokumentations-only Plan, wie spaetere Agenten Source Review, Drafting, Wording, Tabellen/Figuren, Advisor-Updates und Monitor-Appendix pruefen koennten.",
            use_now_de="Nur als Future-Work-Gedanke nach dem source-gated H1-H2-H3-Schreibkern nutzen; Human-Owner, Proof-Artifact und Failure-Mode beachten.",
            gate_or_limit_de="Keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken, bounded inputs, max 50 rows und llm_audit_log vor jeder Aktivierung.",
        ),
        _index_row(
            artifact_id="index_34_agent_pipeline_safety_case",
            artifact_type="future_agent_safety_case",
            path="docs/project/THESIS_AGENT_PIPELINE_SAFETY_CASE.md; data/results/thesis_agent_pipeline_safety_case.csv",
            purpose_de="Dokumentations-only Safety Case, der spaetere Agentenideen an Evidence Lock, Source Review, Tabellen/Figuren, Swiss-Gate, DOCX-QA und Access-Limits bindet.",
            use_now_de="Als Future-Work-Kontrollpunkt nutzen, bevor spaeter Prompt-, Access- oder Agentendesigns spezifiziert werden.",
            gate_or_limit_de="0 aktive Runtime-Rows; keine Runtime-Agenten, kein MCP, kein Model Routing, max 50 rows, llm_audit_log und separates Goal vor Aktivierung.",
        ),
        _index_row(
            artifact_id="index_35_goal_completion_audit",
            artifact_type="goal_completion_audit",
            path="docs/project/THESIS_GOAL_COMPLETION_AUDIT.md; data/results/thesis_goal_completion_audit.csv",
            purpose_de="Belegbarer Audit des aktiven Goals mit erreichten Punkten und offenen Gates.",
            use_now_de="Als Stop-/Weiterarbeitskontrolle vor finalen Abschlussclaims nutzen.",
            gate_or_limit_de="Kein Zielabschluss, solange Source Review, Swiss Resultat-Gate oder DOCX-Render-QA offen sind.",
        ),
        _index_row(
            artifact_id="index_36_status_and_log",
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
        "Advisor Feedback Integration Checklist, Advisor Source Review "
        "Follow-up, H1 Manual Source Review Follow-up, H2 Manual Source Review Follow-up, H3 Manual Source Review Follow-up, Manual Source Review Follow-up Overview, Submission Readiness Board, "
        "Drafting Sequence, Execution Checklist, Chapter Source Bindings, "
        "Source Review Execution, Source Access "
        "Audit, Source Structure Inventory, Source Review Decision Packets, "
        "H1-H2-H3 Source Review Notes, Source Review Progress Ledger, "
        "H1-H2-H3 Manual Source Review Execution Pass, Source Review "
        "Progress Protocol, Source Review Chapter Handoff, Chapter Source "
        "Review Checklist, H1-H2-H3 Drafting Checklist, "
        "H1-H2-H3 Bounded Chapter Draft, H1-H2-H3 Source-Gated Writing Pass, "
        "H1-H2-H3 Source-Gated Thesis Drafting Pass, Thesis Final Gate Board, Traceability Audit, Method/Interpretation Source Coverage, "
        "H1-H2-H3 Core Sections, Agent Pipeline Upgrade Plan, Goal Completion Audit, Agent Future-Work Handoff, Agent Pipeline Control Audit, Tabellen/Figuren und "
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
        "Chat-Vorlage. Nutze das Feedback-Log nach der Betreuung und die "
        "Feedback-Integration-Checklist, um daraus kleine Folgecommits mit "
        "Quellen-, Artefakt-, Tabellen/Figuren- und Agent-Gates abzuleiten. "
        "Nutze das Advisor Source Review Follow-up als direkte Reihenfolge "
        "fuer Feedback-Erfassung, Source-Review-Tiefe, H1-H2-H3 Manual Source "
        "Review, bounded Draft, Final-Gates und Agent-Future-Work-Grenze. "
        "Nutze das H1 Manual Source Review Follow-up als ersten konkreten "
        "H1-Review-Slice fuer Page-/Section-Note, Claim-Support, "
        "Blocked-Wording und Citation-Use. "
        "Nutze das H2 Manual Source Review Follow-up als naechsten konkreten "
        "H2-Review-Slice fuer Page-/Section-Note, Claim-Support, "
        "Blocked-Wording, Citation-Use und Kausalclaim-Grenze. "
        "Nutze das H3 Manual Source Review Follow-up als naechsten konkreten "
        "H3-Review-Slice fuer Page-/Section-Note, Claim-Support, "
        "Blocked-Wording, Citation-Use, Granger-Grenze und Wallet-Grenze. "
        "Nutze die Manual Source Review Follow-up Overview als kompakte "
        "H1-H2-H3 Steuerungsuebersicht fuer die 23 offenen Review-Zeilen. "
        "Nutze das Submission Readiness Board fuer die "
        "finalen Gates. Nutze die Drafting Sequence fuer die naechste "
        "Schreibreihenfolge. Nutze das Source Access Audit und Source Structure "
        "Inventory sowie Source Review Decision Packets vor der manuellen "
        "Quellenpruefung. Nutze die H1-H2-H3 Source Review Notes fuer den "
        "empirischen BA-Kern und den Source Review Progress Ledger fuer "
        "manuelle Fortschrittsentscheide. Nutze den H1-H2-H3 Manual Source "
        "Review Execution Pass als konkrete source-by-source Arbeitsliste "
        "fuer Page-/Section-Notes, Claim-Support, Blocked-Wording und "
        "Citation-Use. Nutze das Source Review Progress Protocol als "
        "Reihenfolge fuer Coverage, Resultatpaket, Source Review und "
        "Future-Agent-Grenzen. Nutze das Source Review Chapter Handoff "
        "als kapitelweise Uebergabe fuer H1-H2-H3 und die Chapter Source "
        "Review Checklist als Abhakliste. Nutze die H1-H2-H3 Drafting Checklist "
        "als konkrete Schreibreihenfolge, den H1-H2-H3 Bounded Chapter Draft als Prosa-Bausteine, den H1-H2-H3 Source-Gated Writing Pass als zusammenhaengenden Schreibstand und den H1-H2-H3 Source-Gated Thesis Drafting Pass als paragraphenweise naechste Schreibreihenfolge fuer den empirischen Kern. Nutze das Thesis Final Gate Board als Highlevel-Stop-/Go-Kontrolle. Nutze den Traceability Audit als BA-Schreibkontrolle. "
        "Nutze die Method/Interpretation Source Coverage als flachen Literaturindex- und Artefaktcheck vor jedem H1-H3-Schreibpass. "
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
