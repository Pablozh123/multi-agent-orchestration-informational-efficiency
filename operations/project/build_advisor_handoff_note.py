"""Build a short advisor handoff note from current thesis-control artifacts."""

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

NOTE_OUTPUT = "thesis_advisor_handoff_note.csv"
NOTE_DOC_OUTPUT = "DOZENTEN_UEBERGABE_TEXT.md"

NOTE_COLUMNS: tuple[str, ...] = (
    "section_id",
    "section_title_de",
    "content_de",
    "source_artifacts",
    "do_not_imply_de",
)


@dataclass(frozen=True)
class AdvisorHandoffNoteResult:
    """Generated advisor handoff note paths and counts."""

    note_path: Path
    docs_path: Path
    note_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "note_path": str(self.note_path),
            "docs_path": str(self.docs_path),
            "note_rows": self.note_rows,
        }


def generate_advisor_handoff_note(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> AdvisorHandoffNoteResult:
    """Generate the advisor handoff note CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)
    handoff = _read_csv(results_dir / "thesis_advisor_handoff_package.csv")
    readiness = _read_csv(results_dir / "thesis_submission_readiness_board.csv")
    drafting = _read_csv(results_dir / "thesis_drafting_sequence.csv")
    source_gated_drafting = _read_csv(
        results_dir / "thesis_h1_h2_h3_source_gated_thesis_drafting_pass.csv"
    )
    advisor_questions = _read_csv(results_dir / "thesis_advisor_alignment_checklist.csv")

    note = build_advisor_handoff_note(
        handoff=handoff,
        readiness=readiness,
        drafting=drafting,
        source_gated_drafting=source_gated_drafting,
        advisor_questions=advisor_questions,
    )
    _validate_note(note=note, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    note_path = results_dir / NOTE_OUTPUT
    docs_path = docs_dir / NOTE_DOC_OUTPUT
    note.to_csv(note_path, index=False)
    docs_path.write_text(_render_note_doc(note), encoding="utf-8")

    return AdvisorHandoffNoteResult(
        note_path=note_path,
        docs_path=docs_path,
        note_rows=len(note),
    )


def build_advisor_handoff_note(
    *,
    handoff: pd.DataFrame,
    readiness: pd.DataFrame,
    drafting: pd.DataFrame,
    source_gated_drafting: pd.DataFrame,
    advisor_questions: pd.DataFrame,
) -> pd.DataFrame:
    """Return the short advisor-facing handoff note."""

    _require_columns(handoff, ("deliverable_id", "path"), "advisor handoff package")
    _require_columns(readiness, ("gate_area", "current_status"), "submission readiness board")
    _require_columns(drafting, ("draft_permission", "sequence_id"), "drafting sequence")
    _require_columns(
        source_gated_drafting,
        (
            "thesis_area",
            "manual_execution_rows",
            "manual_execution_pending_rows",
            "manual_execution_final_ready_rows",
            "ready_for_bounded_draft",
            "ready_for_final_submission",
        ),
        "source-gated thesis drafting pass",
    )
    _require_columns(
        advisor_questions,
        ("question_id", "advisor_question_de", "decision_needed_de"),
        "advisor checklist",
    )

    attachment_paths = _attachment_paths(handoff)
    source_status = _status_for_gate(readiness, "source_review")
    swiss_status = _status_for_gate(readiness, "swiss_result_gate")
    agent_status = _status_for_gate(readiness, "agent_future_work")
    draft_ready = int(readiness["current_status"].astype(str).str.startswith("ready_for").sum())
    final_blocked = int(
        readiness["current_status"].astype(str).str.startswith("final_blocked").sum()
    )
    write_now = int((drafting["draft_permission"] == "write_now_bounded").sum())
    future_only = int((drafting["draft_permission"] == "future_work_only").sum())
    source_gated_summary = _source_gated_drafting_summary(source_gated_drafting)
    selected_questions = _selected_questions(advisor_questions)

    rows = [
        _note_row(
            section_id="handoff_01_subject",
            section_title_de="Betreff",
            content_de=(
                "Zwischenstand Bachelorarbeit: Polymarket, Forecast-Vergleich, "
                "Event-Windows und naechste Gates"
            ),
            source_artifacts="GOAL.md; docs/project/dozentenbericht_ba_thesis.docx",
            do_not_imply_de="Nicht als finale Abgabe oder abgeschlossene Quellenreview darstellen.",
        ),
        _note_row(
            section_id="handoff_02_short_message",
            section_title_de="Kurznachricht",
            content_de=(
                "Ich habe den aktuellen Stand der Bachelorarbeit schriftlich "
                "aufbereitet. Der empirische Kern besteht aus H1 Forecast-"
                "Qualitaet, H2 taeglicher Event-Window-Analyse und H3 Wallet-"
                "Tier-Timing. Der Word-Bericht enthaelt jetzt die Source-Gated "
                "H1-H2-H3 Drafting Sequence. Review-Access bleibt pausiert; "
                "Monitor, Swiss und Agenten sind klar abgegrenzt."
            ),
            source_artifacts="docs/project/dozentenbericht_ba_thesis.docx; data/results/thesis_project_highlevel_view.csv; data/results/thesis_h1_h2_h3_source_gated_thesis_drafting_pass.csv",
            do_not_imply_de="Keine neuen empirischen Resultate oder Runtime-Agenten ankuendigen.",
        ),
        _note_row(
            section_id="handoff_03_attachments",
            section_title_de="Anhaenge",
            content_de=(
                "Als Einstieg reichen der Word-Bericht und die Absprache-"
                "Checklist. Der Bericht zeigt die Source-Gated H1-H2-H3 "
                "Drafting Sequence als naechste BA-Schreiblogik. Die Checklist "
                "startet mit einer empfohlenen "
                "Gespraechsreihenfolge: H1-H2-H3 Scope, Source Review Tiefe, "
                "Tabellen/Figuren, Monitor/Swiss Grenzen, Agenten-Future-Work "
                "und finale QA. Fuer die eigentliche Weiterarbeit liegen ausserdem "
                f"Submission Readiness Board und Drafting Sequence bereit. "
                f"Empfohlene Dateien: {', '.join(attachment_paths)}."
            ),
            source_artifacts="data/results/thesis_advisor_handoff_package.csv; data/results/thesis_consolidation_index.csv",
            do_not_imply_de="Die Zusatzdateien sind Steuerungsartefakte, keine neuen empirischen Tabellen.",
        ),
        _note_row(
            section_id="handoff_04_status",
            section_title_de="Aktueller Gate-Status",
            content_de=(
                f"Readiness: {draft_ready} draft-ready Gates und {final_blocked} "
                f"final blockierte Gates. Source Review: {source_status}; "
                f"Swiss: {swiss_status}; Agenten: {agent_status}. "
                f"Drafting Sequence: {write_now} bounded write-now Schritte "
                f"und {future_only} future-work-only Schritt. Source-Gated "
                f"H1-H2-H3 Drafting Sequence: {source_gated_summary['rows']} "
                f"Absatzschritte, {source_gated_summary['manual_rows_linked']} "
                "Manual Source Review Zeilen verlinkt, "
                f"{source_gated_summary['manual_pending_rows']} pending und "
                f"{source_gated_summary['manual_final_ready_rows']} final-ready."
            ),
            source_artifacts="data/results/thesis_submission_readiness_board.csv; data/results/thesis_drafting_sequence.csv; data/results/thesis_h1_h2_h3_source_gated_thesis_drafting_pass.csv",
            do_not_imply_de="Finale Abgabebereitschaft bleibt blockiert, solange Source Review, Swiss-Gate oder DOCX-Render-QA offen sind.",
        ),
        _note_row(
            section_id="handoff_05_questions",
            section_title_de="Fragen an den Dozenten",
            content_de=selected_questions,
            source_artifacts="data/results/thesis_advisor_alignment_checklist.csv",
            do_not_imply_de="Fragen klaeren Scope; sie aktivieren keine Empirie-Erweiterung.",
        ),
        _note_row(
            section_id="handoff_06_boundaries",
            section_title_de="Nicht-Ziele",
            content_de=(
                "Bitte den Bericht als Zwischenstand lesen: keine finale "
                "Effizienzbehauptung aus Swiss vor dem offiziellen Resultat, "
                "kein Monitor als Kernbeweis, keine Runtime-Agenten, kein MCP, "
                "kein Model Routing, keine LLM-Metriken und keine Trading-Pfade."
            ),
            source_artifacts="GOAL.md; docs/project/THESIS_SUBMISSION_READINESS_BOARD.md; docs/project/THESIS_DRAFTING_SEQUENCE.md",
            do_not_imply_de="Keine Kausalitaet, Private Information, Profitabilitaet oder Tradeability behaupten.",
        ),
    ]
    return pd.DataFrame(rows, columns=NOTE_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_advisor_handoff_note(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _note_row(
    *,
    section_id: str,
    section_title_de: str,
    content_de: str,
    source_artifacts: str,
    do_not_imply_de: str,
) -> dict[str, object]:
    return {
        "section_id": section_id,
        "section_title_de": section_title_de,
        "content_de": content_de,
        "source_artifacts": source_artifacts,
        "do_not_imply_de": do_not_imply_de,
    }


def _attachment_paths(handoff: pd.DataFrame) -> list[str]:
    wanted = {
        "docs/project/dozentenbericht_ba_thesis.docx",
        "docs/project/DOZENTEN_ABSPRACHE_CHECKLIST.md",
        "docs/project/THESIS_SUBMISSION_READINESS_BOARD.md",
        "docs/project/THESIS_DRAFTING_SEQUENCE.md",
    }
    paths = [str(path) for path in handoff["path"] if str(path) in wanted]
    for path in sorted(wanted.difference(paths)):
        paths.append(path)
    return paths


def _selected_questions(advisor_questions: pd.DataFrame) -> str:
    selected_ids = {
        "advisor_q01_h1_wording",
        "advisor_q02_source_depth",
        "advisor_q03_h2_h3_scope",
        "advisor_q06_swiss_gate",
        "advisor_q07_agent_outlook",
        "advisor_q08_final_qa",
    }
    rows = [
        row
        for row in advisor_questions.to_dict(orient="records")
        if str(row["question_id"]) in selected_ids
    ]
    if len(rows) != len(selected_ids):
        found = {str(row["question_id"]) for row in rows}
        missing = sorted(selected_ids.difference(found))
        raise ValueError("Advisor handoff note missing selected questions: " + ", ".join(missing))
    rows.sort(key=lambda row: str(row["question_id"]))
    return "\n".join(
        f"- {row['question_id']}: {row['advisor_question_de']} ({row['decision_needed_de']})"
        for row in rows
    )


def _source_gated_drafting_summary(source_gated_drafting: pd.DataFrame) -> dict[str, int]:
    grouped = source_gated_drafting.groupby("thesis_area", dropna=False)
    return {
        "rows": int(len(source_gated_drafting)),
        "bounded_ready_rows": int(
            source_gated_drafting["ready_for_bounded_draft"].astype(bool).sum()
        ),
        "final_submission_ready_rows": int(
            source_gated_drafting["ready_for_final_submission"].astype(bool).sum()
        ),
        "manual_rows_linked": int(grouped["manual_execution_rows"].max().sum()),
        "manual_pending_rows": int(grouped["manual_execution_pending_rows"].max().sum()),
        "manual_final_ready_rows": int(
            grouped["manual_execution_final_ready_rows"].max().sum()
        ),
    }


def _status_for_gate(readiness: pd.DataFrame, gate_area: str) -> str:
    rows = readiness.loc[readiness["gate_area"] == gate_area, "current_status"]
    if rows.empty:
        raise ValueError(f"Readiness gate missing: {gate_area}")
    return str(rows.iloc[0])


def _validate_note(*, note: pd.DataFrame, repo_root: Path) -> None:
    _require_columns(note, NOTE_COLUMNS, "advisor handoff note")
    if note["section_id"].duplicated().any():
        raise ValueError("Advisor handoff note contains duplicate section_id values.")
    if len(note) != 6:
        raise ValueError("Advisor handoff note must contain exactly 6 sections.")
    for artifact_group in note["source_artifacts"].astype(str):
        for artifact in _split_semicolon(artifact_group):
            if not (repo_root / artifact).exists():
                raise FileNotFoundError(f"Advisor handoff source artifact missing: {artifact}")
    joined = "\n".join(note.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Advisor handoff note must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "review-access bleibt pausiert",
        "source-gated h1-h2-h3 drafting sequence",
        "final blockierte gates",
        "keine runtime-agenten",
        "keine llm-metriken",
        "keine trading-pfade",
        "offiziellen resultat",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Advisor handoff note missing required terms: " + ", ".join(missing))


def _render_note_doc(note: pd.DataFrame) -> str:
    subject = _content(note, "handoff_01_subject")
    message = _content(note, "handoff_02_short_message")
    attachments = _content(note, "handoff_03_attachments")
    status = _content(note, "handoff_04_status")
    questions = _content(note, "handoff_05_questions")
    boundaries = _content(note, "handoff_06_boundaries")
    return (
        "# Dozenten-Uebergabetext\n\n"
        "Dieser Text ist als kurze Mail- oder Chat-Vorlage fuer die naechste "
        "Betreuung gedacht. Er erzeugt keine neuen empirischen Resultate.\n\n"
        f"**Betreff:** {subject}\n\n"
        "Hallo [Name des Dozenten]\n\n"
        f"{message}\n\n"
        f"{attachments}\n\n"
        f"{status}\n\n"
        "Die wichtigsten Fragen fuer die naechste Abstimmung sind:\n\n"
        f"{questions}\n\n"
        f"{boundaries}\n\n"
        "Viele Gruesse\n"
        "[Name]\n"
    )


def _content(note: pd.DataFrame, section_id: str) -> str:
    rows = note.loc[note["section_id"] == section_id, "content_de"]
    if rows.empty:
        raise ValueError(f"Advisor handoff note section missing: {section_id}")
    return str(rows.iloc[0])


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required advisor handoff note input missing: {path}")
    return pd.read_csv(path)


def _resolve_under(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _split_semicolon(value: str) -> list[str]:
    if value.lower() == "nan":
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


if __name__ == "__main__":
    raise SystemExit(main())
