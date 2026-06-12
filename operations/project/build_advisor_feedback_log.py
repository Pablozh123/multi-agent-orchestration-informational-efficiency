"""Build an advisor feedback log template from the advisor question checklist."""

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

FEEDBACK_OUTPUT = "thesis_advisor_feedback_log_template.csv"
FEEDBACK_DOC_OUTPUT = "DOZENTEN_FEEDBACK_LOG.md"

FEEDBACK_COLUMNS: tuple[str, ...] = (
    "feedback_id",
    "advisor_question_id",
    "topic",
    "advisor_question_de",
    "current_project_position_de",
    "decision_needed_de",
    "advisor_feedback_status",
    "advisor_feedback_de",
    "resulting_action_de",
    "commit_scope_de",
    "guardrail_de",
)


@dataclass(frozen=True)
class AdvisorFeedbackLogResult:
    """Generated advisor feedback log paths and counts."""

    feedback_path: Path
    docs_path: Path
    feedback_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "feedback_path": str(self.feedback_path),
            "docs_path": str(self.docs_path),
            "feedback_rows": self.feedback_rows,
        }


def generate_advisor_feedback_log(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> AdvisorFeedbackLogResult:
    """Generate the advisor feedback log template CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)
    advisor_questions = _read_csv(results_dir / "thesis_advisor_alignment_checklist.csv")

    feedback = build_advisor_feedback_log(advisor_questions=advisor_questions)
    _validate_feedback(feedback)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    feedback_path = results_dir / FEEDBACK_OUTPUT
    docs_path = docs_dir / FEEDBACK_DOC_OUTPUT
    feedback.to_csv(feedback_path, index=False)
    docs_path.write_text(_render_feedback_doc(feedback), encoding="utf-8")

    return AdvisorFeedbackLogResult(
        feedback_path=feedback_path,
        docs_path=docs_path,
        feedback_rows=len(feedback),
    )


def build_advisor_feedback_log(*, advisor_questions: pd.DataFrame) -> pd.DataFrame:
    """Return pending feedback rows without applying any decision."""

    _require_columns(
        advisor_questions,
        (
            "question_id",
            "topic",
            "advisor_question_de",
            "current_project_position_de",
            "decision_needed_de",
            "guardrail",
        ),
        "advisor alignment checklist",
    )
    ordered = advisor_questions.sort_values("question_id")
    rows = [
        {
            "feedback_id": f"feedback_{index:02d}_{row['question_id']}",
            "advisor_question_id": str(row["question_id"]),
            "topic": str(row["topic"]),
            "advisor_question_de": str(row["advisor_question_de"]),
            "current_project_position_de": str(row["current_project_position_de"]),
            "decision_needed_de": str(row["decision_needed_de"]),
            "advisor_feedback_status": "pending_advisor_feedback",
            "advisor_feedback_de": "pending",
            "resulting_action_de": "pending",
            "commit_scope_de": "Nach Feedback in kleinen Commit-Plan uebersetzen.",
            "guardrail_de": str(row["guardrail"]),
        }
        for index, row in enumerate(ordered.to_dict(orient="records"), start=1)
    ]
    return pd.DataFrame(rows, columns=FEEDBACK_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_advisor_feedback_log(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_feedback(feedback: pd.DataFrame) -> None:
    _require_columns(feedback, FEEDBACK_COLUMNS, "advisor feedback log")
    if feedback["feedback_id"].duplicated().any():
        raise ValueError("Advisor feedback log contains duplicate feedback_id values.")
    if len(feedback) != 8:
        raise ValueError("Advisor feedback log must contain exactly 8 rows.")
    if not feedback["advisor_feedback_status"].eq("pending_advisor_feedback").all():
        raise ValueError("Advisor feedback log must keep all statuses pending.")
    joined = "\n".join(feedback.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Advisor feedback log must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "pending_advisor_feedback",
        "nach feedback in kleinen commit-plan",
        "review-access",
        "keine runtime-agenten",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Advisor feedback log missing required terms: " + ", ".join(missing))


def _render_feedback_doc(feedback: pd.DataFrame) -> str:
    display = feedback[
        [
            "feedback_id",
            "topic",
            "advisor_question_de",
            "advisor_feedback_status",
            "advisor_feedback_de",
            "resulting_action_de",
            "guardrail_de",
        ]
    ]
    return (
        "# Dozenten-Feedback-Log\n\n"
        "Dieses Log ist eine Vorlage fuer die naechste Betreuung. Alle "
        "Entscheidungen bleiben pending, bis der Dozent Feedback gegeben hat. "
        "Es erzeugt keine neuen empirischen Resultate.\n\n"
        "## Counts\n\n"
        f"- Feedback rows: {len(feedback)}\n"
        "- Current status: pending_advisor_feedback\n\n"
        "## Feedback Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Nach dem Gespraech jede Antwort in `advisor_feedback_de` eintragen, "
        "daraus eine kleine Folgeaktion ableiten und nur passende kleine "
        "Commits planen. Review-Access, Runtime-Agenten, MCP, Model Routing, "
        "LLM-Metriken und Trading-Pfade bleiben deaktiviert, solange kein "
        "separates Goal sie ausdruecklich erlaubt.\n"
    )


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required advisor feedback input missing: {path}")
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
