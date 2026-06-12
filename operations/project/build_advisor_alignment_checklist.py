"""Build an advisor alignment checklist from thesis consolidation artifacts."""

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

CHECKLIST_OUTPUT = "thesis_advisor_alignment_checklist.csv"
CHECKLIST_DOC_OUTPUT = "DOZENTEN_ABSPRACHE_CHECKLIST.md"

CHECKLIST_COLUMNS: tuple[str, ...] = (
    "question_id",
    "topic",
    "advisor_question_de",
    "current_project_position_de",
    "decision_needed_de",
    "source_artifacts",
    "guardrail",
    "next_action_after_feedback",
)


@dataclass(frozen=True)
class AdvisorChecklistResult:
    """Generated advisor checklist paths and counts."""

    checklist_path: Path
    docs_path: Path
    checklist_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "checklist_path": str(self.checklist_path),
            "docs_path": str(self.docs_path),
            "checklist_rows": self.checklist_rows,
        }


def generate_advisor_alignment_checklist(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> AdvisorChecklistResult:
    """Generate the advisor alignment checklist CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)
    project_view = _read_csv(results_dir / "thesis_project_highlevel_view.csv")
    next_work = _read_csv(results_dir / "thesis_next_work_plan.csv")
    source_worksheet = _read_csv(results_dir / "thesis_source_review_worksheet.csv")
    wording_guard = _read_csv(results_dir / "thesis_wording_guard.csv")

    checklist = build_advisor_alignment_checklist(
        project_view=project_view,
        next_work=next_work,
        source_worksheet=source_worksheet,
        wording_guard=wording_guard,
    )
    _validate_checklist(checklist)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    checklist_path = results_dir / CHECKLIST_OUTPUT
    docs_path = docs_dir / CHECKLIST_DOC_OUTPUT
    checklist.to_csv(checklist_path, index=False)
    docs_path.write_text(_render_checklist_doc(checklist), encoding="utf-8")

    return AdvisorChecklistResult(
        checklist_path=checklist_path,
        docs_path=docs_path,
        checklist_rows=len(checklist),
    )


def build_advisor_alignment_checklist(
    *,
    project_view: pd.DataFrame,
    next_work: pd.DataFrame,
    source_worksheet: pd.DataFrame,
    wording_guard: pd.DataFrame,
) -> pd.DataFrame:
    """Return the concrete advisor questions for the next discussion."""

    _require_columns(project_view, ("view_id", "current_decision", "next_gate"), "project view")
    _require_columns(next_work, ("workstream_id", "next_action", "guardrail"), "next work plan")
    _require_columns(
        source_worksheet,
        ("priority_band", "reviewer_decision"),
        "source review worksheet",
    )
    _require_columns(wording_guard, ("evidence_id", "final_use_gate"), "wording guard")

    priority_sources = int(
        (source_worksheet["priority_band"] == "priority_1_method_foundation_review").sum()
    )
    blocked_sources = int(
        (source_worksheet["priority_band"] == "blocked_or_future_work_only").sum()
    )
    pending_reviews = int((source_worksheet["reviewer_decision"] == "pending").sum())
    thesis_text_guards = int(
        (wording_guard["final_use_gate"] == "thesis_text_allowed_after_source_review").sum()
    )

    rows = [
        _checklist_row(
            question_id="advisor_q01_h1_wording",
            topic="H1 bounded wording",
            advisor_question_de=(
                "Ist die H1-Formulierung als begrenzte Polymarket-Stuetze in "
                "definierten Poll-Vergleichsscopes akzeptabel?"
            ),
            current_project_position_de=(
                f"{thesis_text_guards} Wording-Guard-Zeilen sind fuer Thesis-Text "
                "nach Source Review vorgesehen; H1 bleibt bounded, nicht universal."
            ),
            decision_needed_de="Bestaetigen, ob H1 als bounded result chapter geschrieben werden soll.",
            source_artifacts=[
                "data/results/thesis_wording_guard.csv",
                "data/results/thesis_core_results_table.csv",
            ],
            guardrail="Keine universelle Polymarket-Ueberlegenheit und keine RCP-Wahrscheinlichkeitsbehauptung.",
            next_action_after_feedback="H1-Kapitel mit erlaubtem Wording und Gegenbeispiel-Absatz schreiben.",
        ),
        _checklist_row(
            question_id="advisor_q02_source_depth",
            topic="Source review depth",
            advisor_question_de=(
                "Reicht fuer die Abgabe ein Full Review der Priority-1-Methodenquellen "
                "plus Seiten-/Abschnittsnotizen?"
            ),
            current_project_position_de=(
                f"Worksheet: {len(source_worksheet)} Quellenreview-Zeilen, "
                f"{priority_sources} Priority-1, {blocked_sources} blocked/future-only, "
                f"{pending_reviews} pending reviewer decisions."
            ),
            decision_needed_de="Festlegen, welche Quellen vor finaler Zitation voll reviewt werden muessen.",
            source_artifacts=[
                "data/results/thesis_source_review_worksheet.csv",
                "docs/research/THESIS_SOURCE_REVIEW_WORKSHEET.md",
            ],
            guardrail="Quellenstatus nicht automatisch hochstufen; candidate/rejected Quellen nicht fuer thesis-facing Claims nutzen.",
            next_action_after_feedback="Reviewer-Notizen in die Worksheet-Spalten eintragen und Literaturstatus separat pflegen.",
        ),
        _checklist_row(
            question_id="advisor_q03_h2_h3_scope",
            topic="H2/H3 scope",
            advisor_question_de=(
                "Soll H2/H3 als Tagesfenster- und Timingdiagnostik genuegen, "
                "ohne Intraday- und Kausalclaims?"
            ),
            current_project_position_de="H2 nutzt kuratierte Tagesfenster; H3 nutzt dataset-relative Wallet-Tiers und Granger nur diagnostisch.",
            decision_needed_de="Absegnen, dass Intraday-Speed, Kausalitaet und Profitabilitaet ausserhalb des aktuellen Scopes bleiben.",
            source_artifacts=[
                "data/results/thesis_wording_guard.csv",
                "data/results/thesis_h3_summary.csv",
                "data/results/h2_event_window_summary.csv",
            ],
            guardrail="Keine Intraday-, Granger-Kausalitaets-, Private-Information- oder Profitabilitaetsclaims.",
            next_action_after_feedback="H2- und H3-Kapitel mit expliziten Limitationen schreiben.",
        ),
        _checklist_row(
            question_id="advisor_q04_table_figure_package",
            topic="Tables and figures",
            advisor_question_de="Sind 5 Kern-Tabellen und 4 Kern-Figuren als kompakte Ergebnisdarstellung sinnvoll?",
            current_project_position_de="Das Thesis-Paket priorisiert wenige beschriftete Tabellen/Figuren statt Rohartefakt-Dumps.",
            decision_needed_de="Bestaetigen, ob diese Auswahl in den Haupttext darf und was in den Appendix geht.",
            source_artifacts=[
                "data/results/thesis_table_figure_captions.csv",
                "data/results/thesis_curated_result_package.csv",
            ],
            guardrail="Keine neuen Rohartefakte in den Haupttext ohne Evidence-Map- und Kapitelplan-Update.",
            next_action_after_feedback="Tabellen/Figuren in die Kapitelstruktur einfuegen und Nummerierung spaeter finalisieren.",
        ),
        _checklist_row(
            question_id="advisor_q05_monitor_appendix",
            topic="Monitor appendix",
            advisor_question_de="Soll der Monitor nur als Appendix-/Workflow-Prototyp gezeigt werden?",
            current_project_position_de="Review-Access bleibt pausiert; Monitor-Faelle sind source-check-pending und nicht thesis-facing.",
            decision_needed_de="Klaeren, ob ein kurzer Appendix reicht oder der Monitor im Haupttext nur erwaehnt wird.",
            source_artifacts=[
                "data/results/thesis_project_highlevel_view.csv",
                "data/results/monitor_anomaly_review_summary.csv",
            ],
            guardrail="Keine Wallet-Adress-Exposition, keine Order- oder Trading-Pfade, keine Kausal- oder Ineffizienzclaims.",
            next_action_after_feedback="Monitor-Abschnitt auf Prototyp, Review Queue und Grenzen kuerzen.",
        ),
        _checklist_row(
            question_id="advisor_q06_swiss_gate",
            topic="Swiss result gate",
            advisor_question_de="Wie soll der Swiss-Referendum-Track platziert werden, solange das finale Resultat noch Gate ist?",
            current_project_position_de="Swiss bleibt bis zur offiziellen Resultatzuordnung beschreibend und darf keine finale Effizienzaussage tragen.",
            decision_needed_de="Entscheiden, ob Swiss in Diskussion, Appendix oder als aktuelles Side-Example steht.",
            source_artifacts=[
                "data/results/swiss_referendum_10mio_latest_source_comparison.csv",
                "docs/research/THESIS_WORDING_GUARD.md",
            ],
            guardrail="Poll-Anteile sind keine Gewinnwahrscheinlichkeiten; keine finale Accuracy- oder Effizienzbehauptung vor Resultat.",
            next_action_after_feedback="Nach dem offiziellen 14. Juni 2026 Resultat Artefakte neu generieren und Wording pruefen.",
        ),
        _checklist_row(
            question_id="advisor_q07_agent_outlook",
            topic="Agent outlook",
            advisor_question_de="Soll die Agenten-Pipeline nur als Future-Work-Ausblick bleiben?",
            current_project_position_de="Agenten sind documentation-only; keine Runtime-Agenten, kein MCP, kein Model Routing.",
            decision_needed_de="Bestaetigen, dass Agenten nicht Teil des empirischen Kerns oder der Abgabe-Pipeline werden.",
            source_artifacts=[
                "data/results/thesis_agent_assistance_protocol.csv",
                "docs/research/THESIS_AGENT_ASSISTANCE_PROTOCOL.md",
            ],
            guardrail="Vor jeder spaeteren Aktivierung: separates Goal, bounded prompts, Tests und llm_audit_log.",
            next_action_after_feedback="Future-Work-Abschnitt knapp halten und keine Implementierung starten.",
        ),
        _checklist_row(
            question_id="advisor_q08_final_qa",
            topic="Final QA",
            advisor_question_de="Welche finale QA erwartet der Dozent vor Abgabe oder naechstem Entwurf?",
            current_project_position_de="Workplan endet mit Tests, Review-Checks, Citation Checks, Tabellen/Figuren und Swiss-Spelling.",
            decision_needed_de="Abklaeren, welche Checks der Dozent sehen moechte und welche Artefakte genuegen.",
            source_artifacts=[
                "data/results/thesis_next_work_plan.csv",
                "STATUS.md",
                "docs/project/WORK_LOG.md",
            ],
            guardrail="Keine finale Aussage darf ueber deterministische Artefakte und reviewte Quellen hinausgehen.",
            next_action_after_feedback="Feedback in kleinen Commit-Plan uebersetzen und Scope nicht erweitern.",
        ),
    ]
    return pd.DataFrame(rows, columns=CHECKLIST_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_advisor_alignment_checklist(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _checklist_row(
    *,
    question_id: str,
    topic: str,
    advisor_question_de: str,
    current_project_position_de: str,
    decision_needed_de: str,
    source_artifacts: list[str],
    guardrail: str,
    next_action_after_feedback: str,
) -> dict[str, object]:
    return {
        "question_id": question_id,
        "topic": topic,
        "advisor_question_de": advisor_question_de,
        "current_project_position_de": current_project_position_de,
        "decision_needed_de": decision_needed_de,
        "source_artifacts": "; ".join(source_artifacts),
        "guardrail": guardrail,
        "next_action_after_feedback": next_action_after_feedback,
    }


def _validate_checklist(checklist: pd.DataFrame) -> None:
    _require_columns(checklist, CHECKLIST_COLUMNS, "advisor checklist")
    if checklist["question_id"].duplicated().any():
        raise ValueError("Advisor checklist contains duplicate question_id values.")
    if len(checklist) != 8:
        raise ValueError("Advisor checklist must contain exactly 8 questions.")
    for column in (
        "advisor_question_de",
        "current_project_position_de",
        "decision_needed_de",
        "source_artifacts",
        "guardrail",
        "next_action_after_feedback",
    ):
        if checklist[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Advisor checklist contains empty {column}.")
    joined = "\n".join(checklist.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Advisor checklist must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "review-access bleibt pausiert",
        "llm_audit_log",
        "swiss",
        "h1",
        "keine runtime-agenten",
        "keine finale",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Advisor checklist missing required guardrail terms: " + ", ".join(missing))


def _render_checklist_doc(checklist: pd.DataFrame) -> str:
    display = checklist[
        [
            "question_id",
            "topic",
            "advisor_question_de",
            "current_project_position_de",
            "decision_needed_de",
            "guardrail",
        ]
    ]
    return (
        "# Dozenten-Absprache-Checklist\n\n"
        "Diese Checkliste uebersetzt den Highlevel-Projektstand in konkrete "
        "Fragen fuer die naechste Abstimmung mit dem Dozenten. Sie ist ein "
        "Projektmanagement-Artefakt und erzeugt keine neuen empirischen "
        "Resultate.\n\n"
        "## Counts\n\n"
        f"- Advisor questions: {len(checklist)}\n\n"
        "## Empfohlene Gespraechsreihenfolge\n\n"
        "1. Erst H1-H2-H3 Scope bestaetigen: bounded H1, H2 Tagesfenster, "
        "H3 Timingdiagnostik.\n"
        "2. Danach Source Review Tiefe festlegen: Priority-1-Quellen und "
        "Seiten-/Abschnittsnotizen.\n"
        "3. Dann Tabellen/Figuren und Kapitelintegration entscheiden.\n"
        "4. Monitor und Swiss nur als Appendix, Diskussion oder Side-Track "
        "abgrenzen; Review-Access bleibt pausiert.\n"
        "5. Agenten nur als Future Work bestaetigen und finale QA-Gates "
        "festlegen.\n\n"
        "## Questions\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Die Fragen sollen Scope und Wording klaeren. Sie duerfen nicht genutzt "
        "werden, um Review-Access, Agenten, MCP, Model Routing, Rohdatenzugriff "
        "oder Trading-Pfade zu aktivieren.\n"
    )


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required advisor checklist input missing: {path}")
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
