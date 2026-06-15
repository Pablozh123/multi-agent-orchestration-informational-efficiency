"""Build a checklist for turning advisor feedback into scoped follow-up work."""

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

INTEGRATION_OUTPUT = "thesis_advisor_feedback_integration_checklist.csv"
INTEGRATION_DOC_OUTPUT = "DOZENTEN_FEEDBACK_INTEGRATION_CHECKLIST.md"

INTEGRATION_COLUMNS: tuple[str, ...] = (
    "integration_id",
    "advisor_question_id",
    "topic",
    "feedback_status",
    "decision_to_capture_de",
    "affected_artifacts",
    "required_evidence_check_de",
    "small_commit_scope_de",
    "final_gate_de",
    "guardrail_de",
)


@dataclass(frozen=True)
class AdvisorFeedbackIntegrationResult:
    """Generated advisor feedback integration paths and counts."""

    integration_path: Path
    docs_path: Path
    integration_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "integration_path": str(self.integration_path),
            "docs_path": str(self.docs_path),
            "integration_rows": self.integration_rows,
        }


def generate_advisor_feedback_integration_checklist(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> AdvisorFeedbackIntegrationResult:
    """Generate the advisor feedback integration CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)
    feedback_log = _read_csv(results_dir / "thesis_advisor_feedback_log_template.csv")

    integration = build_advisor_feedback_integration_checklist(feedback_log=feedback_log)
    _validate_integration(integration)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    integration_path = results_dir / INTEGRATION_OUTPUT
    docs_path = docs_dir / INTEGRATION_DOC_OUTPUT
    integration.to_csv(integration_path, index=False)
    docs_path.write_text(_render_integration_doc(integration), encoding="utf-8")

    return AdvisorFeedbackIntegrationResult(
        integration_path=integration_path,
        docs_path=docs_path,
        integration_rows=len(integration),
    )


def build_advisor_feedback_integration_checklist(*, feedback_log: pd.DataFrame) -> pd.DataFrame:
    """Return pending integration rows derived from the advisor feedback log."""

    _require_columns(
        feedback_log,
        (
            "feedback_id",
            "advisor_question_id",
            "topic",
            "advisor_feedback_status",
            "advisor_feedback_de",
            "resulting_action_de",
            "guardrail_de",
        ),
        "advisor feedback log",
    )
    ordered = feedback_log.sort_values("advisor_question_id")
    rows = []
    for index, feedback in enumerate(ordered.to_dict(orient="records"), start=1):
        question_id = str(feedback["advisor_question_id"])
        rows.append(
            _integration_row(
                integration_id=f"integration_{index:02d}_{question_id}",
                advisor_question_id=question_id,
                topic=str(feedback["topic"]),
                feedback_status=str(feedback["advisor_feedback_status"]),
                **_integration_spec_for_question(question_id=question_id),
            )
        )
    return pd.DataFrame(rows, columns=INTEGRATION_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_advisor_feedback_integration_checklist(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _integration_spec_for_question(question_id: str) -> dict[str, str]:
    specs = {
        "advisor_q01_h1_wording": {
            "decision_to_capture_de": "H1-Wording-Entscheid als bounded support, Gegenbeispiel oder weiter blockierter Claim erfassen.",
            "affected_artifacts": "docs/research/THESIS_H1_H2_H3_BOUNDED_CHAPTER_DRAFT.md; docs/research/THESIS_WORDING_GUARD.md; docs/project/THESIS_TRACEABILITY_AUDIT.md",
            "required_evidence_check_de": "Vor Textaenderung pruefen, dass method_h1_brier_dm und die H1-Interpretationen deterministische Artefakte, Literatur-IDs, Limitationen und Source Review Gates tragen.",
            "small_commit_scope_de": "docs: integrate advisor h1 wording feedback",
            "final_gate_de": "Finale H1-Zitation erst nach Source Review und Wording-Guard-Abgleich.",
            "guardrail_de": "Keine universelle Polymarket-Ueberlegenheit, keine RCP-Wahrscheinlichkeitsbehauptung und keine neuen Metriken.",
        },
        "advisor_q02_source_depth": {
            "decision_to_capture_de": "Festhalten, welche Priority-1-Quellen voll reviewt werden muessen und welche nur Appendix/Future Work bleiben.",
            "affected_artifacts": "docs/project/THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md; docs/project/THESIS_H1_H2_H3_SOURCE_REVIEW_NOTES.md; data/literature/literature_index.csv",
            "required_evidence_check_de": "Jede Methode und jede Interpretation braucht vor finaler Nutzung eine reviewte Quelle oder ein deterministisches Artefakt plus Page-/Section-Note im Source Review Ledger.",
            "small_commit_scope_de": "docs: integrate advisor source review depth feedback",
            "final_gate_de": "Keine Quellenstatus-Hochstufung ohne manuelle Claim-Support-Entscheidung.",
            "guardrail_de": "Quellenstatus nicht automatisch hochstufen; candidate/rejected Quellen nicht fuer thesis-facing Claims nutzen.",
        },
        "advisor_q03_h2_h3_scope": {
            "decision_to_capture_de": "Entscheid erfassen, ob H2 als Tagesfensterdiagnostik und H3 als Timingdiagnostik ohne Kausalclaim genuegt.",
            "affected_artifacts": "docs/research/THESIS_H1_H2_H3_CORE_SECTIONS.md; docs/project/THESIS_H1_H2_H3_DRAFTING_CHECKLIST.md; docs/project/THESIS_TRACEABILITY_AUDIT.md",
            "required_evidence_check_de": "H2/H3-Methoden und Interpretationen muessen auf deterministische Artefakte, Literatur-IDs, Limitationen und blockiertes Wording verweisen.",
            "small_commit_scope_de": "docs: integrate advisor h2 h3 scope feedback",
            "final_gate_de": "Finale H2/H3-Aussagen erst nach Source Review und Limitationscheck.",
            "guardrail_de": "Keine Intraday-, Granger-Kausalitaets-, Private-Information- oder Profitabilitaetsclaims.",
        },
        "advisor_q04_table_figure_package": {
            "decision_to_capture_de": "Entscheid erfassen, welche Kern-Tabellen und Figuren im Haupttext bleiben und was in den Appendix wandert.",
            "affected_artifacts": "docs/research/THESIS_TABLE_FIGURE_CAPTIONS.md; data/results/thesis_curated_result_package.csv; data/results/thesis_result_package_traceability.csv",
            "required_evidence_check_de": "Nur wenige gute Tabellen/Figuren verwenden: jede Tabelle/Figur braucht Caption, deterministisches Artefakt, Interpretation, Limitation und Source-Review-Bezug.",
            "small_commit_scope_de": "docs: integrate advisor table figure feedback",
            "final_gate_de": "Finale Nummerierung und Platzierung erst im Thesis-Layout.",
            "guardrail_de": "Keine Rohartefakt-Dumps und keine neuen Tabellen/Figuren ohne Evidence-Map- und Kapitelplan-Update.",
        },
        "advisor_q05_monitor_appendix": {
            "decision_to_capture_de": "Entscheid erfassen, ob der Monitor nur Appendix, Diskussion oder komplett Future Work bleibt.",
            "affected_artifacts": "docs/research/THESIS_PROJECT_HIGHLEVEL_VIEW.md; docs/project/THESIS_FINAL_GATE_BOARD.md; data/results/monitor_anomaly_review_summary.csv",
            "required_evidence_check_de": "Monitor-Inhalte nur als Prototyp verwenden und keine thesis-facing Interpretation ohne Human Review, Source Check und bounded Summary.",
            "small_commit_scope_de": "docs: integrate advisor monitor appendix feedback",
            "final_gate_de": "Monitor bleibt appendix-only, bis Human Review und Thesis-Use-Gate abgeschlossen sind.",
            "guardrail_de": "Review-Access bleibt pausiert; keine Wallet-Adress-Exposition, keine Order- oder Trading-Pfade und keine Kausalclaims.",
        },
        "advisor_q06_swiss_gate": {
            "decision_to_capture_de": "Swiss-Platzierung als bounded Post-Resultat-Fallstudie erfassen.",
            "affected_artifacts": "data/results/swiss_referendum_10mio_final_case_study.csv; docs/research/SWISS_REFERENDUM_FINAL_CASE_STUDY.md; docs/project/THESIS_FINAL_GATE_BOARD.md",
            "required_evidence_check_de": "Swiss nutzt nur deterministisch generierte Final-Case-Artefakte und klare Poll-Proxy-Limitationen.",
            "small_commit_scope_de": "docs: integrate advisor swiss placement feedback",
            "final_gate_de": "Keine finale Swiss-Zitation ohne Source Review und Poll-Proxy-Limitation.",
            "guardrail_de": "Poll-Anteile sind keine Gewinnwahrscheinlichkeiten; keine Effizienz-, Mispricing- oder Tradeability-Behauptung.",
        },
        "advisor_q07_agent_outlook": {
            "decision_to_capture_de": "Entscheid erfassen, ob Agenten nur als Future-Work-Ausblick oder als spaeterer separater Track beschrieben werden.",
            "affected_artifacts": "docs/research/THESIS_AGENT_PIPELINE_UPGRADE_PLAN.md; docs/project/THESIS_AGENT_PIPELINE_CONTROL_AUDIT.md; docs/project/THESIS_AGENT_FUTURE_WORK_HANDOFF.md",
            "required_evidence_check_de": "Agenten duerfen nur documentation-only bleiben: spaetere Nutzung braucht separate Freigabe, bounded inputs, Tests, max 50 rows und llm_audit_log.",
            "small_commit_scope_de": "docs: integrate advisor agent outlook feedback",
            "final_gate_de": "0 aktive Runtime-Agenten, bis ein separates spaeteres Goal alle Gates erfuellt.",
            "guardrail_de": "Keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken und keine Trading-Pfade.",
        },
        "advisor_q08_final_qa": {
            "decision_to_capture_de": "Finale QA-Erwartung als konkrete Checkliste und kleine Folgecommits erfassen.",
            "affected_artifacts": "STATUS.md; docs/project/WORK_LOG.md; docs/project/THESIS_FINAL_GATE_BOARD.md",
            "required_evidence_check_de": "Vor jedem Completion-Claim Tests, Review-Checks, Source Review, Swiss-Spelling, DOCX-Render-QA und offene Finalgates nachweisen.",
            "small_commit_scope_de": "docs: integrate advisor final qa feedback",
            "final_gate_de": "Kein Zielabschluss, solange Source Review, Swiss official result oder DOCX-Render-QA offen sind.",
            "guardrail_de": "Keine finale Aussage darf ueber deterministische Artefakte und reviewte Quellen hinausgehen.",
        },
    }
    try:
        return specs[question_id]
    except KeyError as exc:
        raise ValueError(f"Unsupported advisor question id for integration: {question_id}") from exc


def _integration_row(
    *,
    integration_id: str,
    advisor_question_id: str,
    topic: str,
    feedback_status: str,
    decision_to_capture_de: str,
    affected_artifacts: str,
    required_evidence_check_de: str,
    small_commit_scope_de: str,
    final_gate_de: str,
    guardrail_de: str,
) -> dict[str, object]:
    return {
        "integration_id": integration_id,
        "advisor_question_id": advisor_question_id,
        "topic": topic,
        "feedback_status": feedback_status,
        "decision_to_capture_de": decision_to_capture_de,
        "affected_artifacts": affected_artifacts,
        "required_evidence_check_de": required_evidence_check_de,
        "small_commit_scope_de": small_commit_scope_de,
        "final_gate_de": final_gate_de,
        "guardrail_de": guardrail_de,
    }


def _validate_integration(integration: pd.DataFrame) -> None:
    _require_columns(integration, INTEGRATION_COLUMNS, "advisor feedback integration checklist")
    if integration["integration_id"].duplicated().any():
        raise ValueError("Advisor feedback integration checklist contains duplicate integration_id values.")
    if len(integration) != 8:
        raise ValueError("Advisor feedback integration checklist must contain exactly 8 rows.")
    if not integration["feedback_status"].eq("pending_advisor_feedback").all():
        raise ValueError("Advisor feedback integration rows must remain pending.")
    for column in (
        "decision_to_capture_de",
        "affected_artifacts",
        "required_evidence_check_de",
        "small_commit_scope_de",
        "final_gate_de",
        "guardrail_de",
    ):
        if integration[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Advisor feedback integration checklist contains empty {column}.")
    joined = "\n".join(integration.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Advisor feedback integration checklist must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "pending_advisor_feedback",
        "deterministische artefakte",
        "source review",
        "wenige gute tabellen",
        "keine roh",
        "review-access bleibt pausiert",
        "keine runtime-agenten",
        "llm_audit_log",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError(
            "Advisor feedback integration checklist missing required terms: "
            + ", ".join(missing)
        )


def _render_integration_doc(integration: pd.DataFrame) -> str:
    display = integration[
        [
            "integration_id",
            "advisor_question_id",
            "topic",
            "feedback_status",
            "required_evidence_check_de",
            "small_commit_scope_de",
            "final_gate_de",
            "guardrail_de",
        ]
    ]
    return (
        "# Dozenten-Feedback-Integration-Checklist\n\n"
        "Diese Checkliste sagt, wie spaeteres Dozentenfeedback in kleine, "
        "pruefbare Folgecommits uebersetzt wird. Sie ist pending, bis der "
        "Dozent geantwortet hat, und erzeugt keine neuen empirischen "
        "Resultate.\n\n"
        "## Counts\n\n"
        f"- Integration rows: {len(integration)}\n"
        "- Feedback status: pending_advisor_feedback\n"
        "- Active runtime agents: 0\n\n"
        "## Integration Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Nach der Betreuung zuerst die passende Feedback-Zeile im "
        "`DOZENTEN_FEEDBACK_LOG.md` ausfuellen. Danach genau eine passende "
        "Integration-Zeile aus dieser Checkliste waehlen und als kleinen "
        "Commit-Scope bearbeiten. Jede Methode und jede Interpretation muss "
        "weiterhin eine reviewte Quelle oder ein deterministisches Artefakt, "
        "eine Limitation und ein Source Review Gate haben. Das Resultatpaket "
        "bleibt bei wenigen guten Tabellen/Figuren; Rohartefakt-Dumps, "
        "Review-Access, Runtime-Agenten, MCP, Model Routing, LLM-Metriken und "
        "Trading-Pfade bleiben deaktiviert.\n"
    )


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required advisor integration input missing: {path}")
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
