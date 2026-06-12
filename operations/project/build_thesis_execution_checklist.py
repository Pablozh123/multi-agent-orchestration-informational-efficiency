"""Build a thesis execution checklist from existing consolidation artifacts."""

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

EXECUTION_OUTPUT = "thesis_execution_checklist.csv"
EXECUTION_DOC_OUTPUT = "THESIS_EXECUTION_CHECKLIST.md"

EXECUTION_COLUMNS: tuple[str, ...] = (
    "task_id",
    "chapter_id",
    "chapter_title",
    "execution_phase",
    "primary_inputs",
    "table_figure_items",
    "source_gate_de",
    "draft_action_de",
    "done_when_de",
    "guardrail_de",
    "advisor_question_ids",
)

CHAPTER_WORKSTREAMS: dict[str, tuple[str, ...]] = {
    "ch_01_intro": ("work_02_method_chapters",),
    "ch_02_theory_literature": ("work_01_source_review", "work_02_method_chapters"),
    "ch_03_data_method": ("work_02_method_chapters",),
    "ch_04_h1_results": ("work_03_h1_results",),
    "ch_05_h2_results": ("work_04_h2_h3_results",),
    "ch_06_h3_results": ("work_04_h2_h3_results",),
    "ch_07_extensions": ("work_06_monitor_appendix", "work_07_swiss_result_gate"),
    "ch_08_discussion_conclusion": ("work_08_agent_outlook", "work_10_final_qa"),
}

CHAPTER_DETAILS: dict[str, dict[str, str]] = {
    "ch_01_intro": {
        "execution_phase": "draft_frame",
        "source_gate_de": "Als Entwurf schreiben; finale Einordnung erst nach Quellenreview.",
        "draft_action_de": "Forschungsfrage, Scope Polymarket/US-Wahl und Proxy-Logik knapp formulieren.",
        "done_when_de": "Forschungsfrage, H1-H3-Logik und Nicht-Ziele sind sichtbar.",
        "advisor_question_ids": "advisor_q01_h1_wording; advisor_q08_final_qa",
    },
    "ch_02_theory_literature": {
        "execution_phase": "source_review_first",
        "source_gate_de": "Priority-1-Methodenquellen mit Seiten- oder Abschnittsnotizen reviewen.",
        "draft_action_de": "EMH, Prognosemaerkte, Event-Study und Wallet-Vorsicht quellengebunden ausarbeiten.",
        "done_when_de": "Jede Theorie- und Methodenbehauptung hat eine reviewte Quelle oder bleibt Draft.",
        "advisor_question_ids": "advisor_q02_source_depth",
    },
    "ch_03_data_method": {
        "execution_phase": "method_draft",
        "source_gate_de": "Methodenquellen pruefen; RCP-Transformation, Event-Kuration und Wallet-Tiers explizit abgrenzen.",
        "draft_action_de": "Datenpipeline, Artefakthierarchie und Python-only-Metrikregel als Methodik schreiben.",
        "done_when_de": "Alle Methoden verweisen auf deterministische Artefakte und passende Quellenanker.",
        "advisor_question_ids": "advisor_q02_source_depth; advisor_q03_h2_h3_scope",
    },
    "ch_04_h1_results": {
        "execution_phase": "result_draft",
        "source_gate_de": "Draft ist moeglich; finale H1-Zitation wartet auf Source Review.",
        "draft_action_de": "H1 als begrenzte Polymarket-Stuetze plus klare Grenze der breiten Behauptung schreiben.",
        "done_when_de": "Bounded H1-Claim, Gegenbeispiel und Limitation stehen direkt nebeneinander.",
        "advisor_question_ids": "advisor_q01_h1_wording; advisor_q04_table_figure_package",
    },
    "ch_05_h2_results": {
        "execution_phase": "result_draft",
        "source_gate_de": "Draft ist moeglich; Event-Study-Quelle und Event-Kuration vor finaler Fassung pruefen.",
        "draft_action_de": "H2 als Tagesfensterdiagnostik schreiben und Intraday-Speed ausschliessen.",
        "done_when_de": "Ereignisse, Tagesfenster und Tagesfrequenz-Limitation sind transparent.",
        "advisor_question_ids": "advisor_q03_h2_h3_scope; advisor_q04_table_figure_package",
    },
    "ch_06_h3_results": {
        "execution_phase": "result_draft",
        "source_gate_de": "Draft ist moeglich; Granger- und Wallet-Literatur vor finaler Interpretation pruefen.",
        "draft_action_de": "H3 als dataset-relative Timingdiagnostik schreiben, nicht als Kausal- oder Private-Information-Claim.",
        "done_when_de": "BUY-only, Tagesaggregation, Mehrfachtests und Nicht-Profitabilitaet sind genannt.",
        "advisor_question_ids": "advisor_q03_h2_h3_scope; advisor_q04_table_figure_package",
    },
    "ch_07_extensions": {
        "execution_phase": "appendix_or_discussion_gate",
        "source_gate_de": "Monitor bleibt Review-pending; Swiss bleibt bis zum offiziellen Resultat vom 14. Juni 2026 beschreibend.",
        "draft_action_de": "Monitor als Prototyp und Swiss als Side-Track knapp platzieren.",
        "done_when_de": "Review-Access bleibt pausiert und Swiss traegt keine finale Effizienzaussage.",
        "advisor_question_ids": "advisor_q05_monitor_appendix; advisor_q06_swiss_gate",
    },
    "ch_08_discussion_conclusion": {
        "execution_phase": "synthesis_after_core",
        "source_gate_de": "Erst nach H1-H3-Draft, Quellenreview und Swiss-/Appendix-Gates finalisieren.",
        "draft_action_de": "Fazit als begrenzte Evidenz fuer H1-H3 schreiben und Agenten nur als Future Work fuehren.",
        "done_when_de": "Keine finale Aussage geht ueber deterministische Artefakte und reviewte Quellen hinaus.",
        "advisor_question_ids": "advisor_q07_agent_outlook; advisor_q08_final_qa",
    },
}


@dataclass(frozen=True)
class ThesisExecutionChecklistResult:
    """Generated execution checklist paths and counts."""

    checklist_path: Path
    docs_path: Path
    checklist_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "checklist_path": str(self.checklist_path),
            "docs_path": str(self.docs_path),
            "checklist_rows": self.checklist_rows,
        }


def generate_thesis_execution_checklist(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> ThesisExecutionChecklistResult:
    """Generate the thesis execution checklist CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)
    chapter_plan = _read_csv(results_dir / "thesis_chapter_plan.csv")
    next_work = _read_csv(results_dir / "thesis_next_work_plan.csv")
    source_review_plan = _read_csv(results_dir / "thesis_source_review_plan.csv")
    table_figure_captions = _read_csv(results_dir / "thesis_table_figure_captions.csv")
    advisor_checklist = _read_csv(results_dir / "thesis_advisor_alignment_checklist.csv")

    checklist = build_thesis_execution_checklist(
        chapter_plan=chapter_plan,
        next_work=next_work,
        source_review_plan=source_review_plan,
        table_figure_captions=table_figure_captions,
        advisor_checklist=advisor_checklist,
    )
    _validate_checklist(checklist=checklist, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    checklist_path = results_dir / EXECUTION_OUTPUT
    docs_path = docs_dir / EXECUTION_DOC_OUTPUT
    checklist.to_csv(checklist_path, index=False)
    docs_path.write_text(_render_execution_doc(checklist), encoding="utf-8")

    return ThesisExecutionChecklistResult(
        checklist_path=checklist_path,
        docs_path=docs_path,
        checklist_rows=len(checklist),
    )


def build_thesis_execution_checklist(
    *,
    chapter_plan: pd.DataFrame,
    next_work: pd.DataFrame,
    source_review_plan: pd.DataFrame,
    table_figure_captions: pd.DataFrame,
    advisor_checklist: pd.DataFrame,
) -> pd.DataFrame:
    """Return one execution row per planned thesis chapter."""

    _require_columns(
        chapter_plan,
        (
            "chapter_id",
            "chapter_title",
            "primary_artifacts",
            "recommended_tables",
            "recommended_figures",
        ),
        "chapter plan",
    )
    _require_columns(next_work, ("workstream_id", "guardrail"), "next work plan")
    _require_columns(
        source_review_plan,
        ("priority_band", "final_citation_readiness"),
        "source review plan",
    )
    _require_columns(
        table_figure_captions,
        ("package_id", "thesis_label", "include_in_core_package"),
        "table figure captions",
    )
    _require_columns(advisor_checklist, ("question_id", "guardrail"), "advisor checklist")

    source_summary = _source_summary(source_review_plan)
    caption_labels = _caption_label_map(table_figure_captions)
    known_workstreams = _known_workstream_ids(next_work)
    known_questions = set(advisor_checklist["question_id"].astype(str))

    rows: list[dict[str, object]] = []
    for index, chapter in enumerate(chapter_plan.to_dict(orient="records"), start=1):
        chapter_id = str(chapter["chapter_id"])
        if chapter_id not in CHAPTER_DETAILS:
            raise ValueError(f"Chapter missing execution detail: {chapter_id}")
        details = CHAPTER_DETAILS[chapter_id]
        advisor_question_ids = str(details["advisor_question_ids"])
        _require_advisor_questions(advisor_question_ids, known_questions)
        workstream_ids = CHAPTER_WORKSTREAMS[chapter_id]
        _require_workstreams(workstream_ids, known_workstreams)
        guardrail = _global_guardrail_for_chapter(chapter_id, source_summary)
        rows.append(
            {
                "task_id": f"exec_{index:02d}_{chapter_id.removeprefix('ch_')}",
                "chapter_id": chapter_id,
                "chapter_title": chapter["chapter_title"],
                "execution_phase": details["execution_phase"],
                "primary_inputs": chapter["primary_artifacts"],
                "table_figure_items": _table_figure_items(chapter, caption_labels),
                "source_gate_de": _source_gate_with_summary(details["source_gate_de"], source_summary),
                "draft_action_de": details["draft_action_de"],
                "done_when_de": details["done_when_de"],
                "guardrail_de": guardrail,
                "advisor_question_ids": advisor_question_ids,
            }
        )

    return pd.DataFrame(rows, columns=EXECUTION_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_thesis_execution_checklist(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _source_summary(source_review_plan: pd.DataFrame) -> dict[str, int]:
    return {
        "priority_1": int(
            (source_review_plan["priority_band"] == "priority_1_method_foundation_review").sum()
        ),
        "needs_full_review": int(
            (
                source_review_plan["final_citation_readiness"]
                == "needs_full_source_review_before_final_citation"
            ).sum()
        ),
        "blocked_or_future": int(
            (source_review_plan["priority_band"] == "blocked_or_future_work_only").sum()
        ),
    }


def _caption_label_map(table_figure_captions: pd.DataFrame) -> dict[str, str]:
    return {
        str(row["package_id"]): str(row["thesis_label"])
        for row in table_figure_captions.to_dict(orient="records")
    }


def _known_workstream_ids(next_work: pd.DataFrame) -> set[str]:
    return set(next_work["workstream_id"].astype(str))


def _require_workstreams(workstream_ids: Sequence[str], known_workstreams: set[str]) -> None:
    missing = sorted(set(workstream_ids).difference(known_workstreams))
    if missing:
        raise ValueError("Next work plan missing required workstreams: " + ", ".join(missing))


def _require_advisor_questions(question_ids: str, known_questions: set[str]) -> None:
    missing = sorted(set(_split_list(question_ids)).difference(known_questions))
    if missing:
        raise ValueError("Advisor checklist missing required questions: " + ", ".join(missing))


def _table_figure_items(chapter: dict[str, object], caption_labels: dict[str, str]) -> str:
    items = _split_list(str(chapter.get("recommended_tables", ""))) + _split_list(
        str(chapter.get("recommended_figures", ""))
    )
    labels = []
    for item in items:
        label = caption_labels.get(item)
        if label:
            labels.append(f"{item} ({label})")
        else:
            labels.append(item)
    return "; ".join(labels) if labels else "none"


def _source_gate_with_summary(gate: str, source_summary: dict[str, int]) -> str:
    return (
        f"{gate} Aktueller Quellen-Gate: {source_summary['priority_1']} Priority-1-"
        f"Quellen und {source_summary['needs_full_review']} Quellen mit Full-Review-Bedarf; "
        f"{source_summary['blocked_or_future']} Quelle bleibt blocked/future-only."
    )


def _global_guardrail_for_chapter(chapter_id: str, source_summary: dict[str, int]) -> str:
    if chapter_id == "ch_07_extensions":
        return "Review-Access bleibt pausiert; keine finalen Effizienzclaims vor offizieller Swiss-Resultatzuordnung."
    if chapter_id == "ch_08_discussion_conclusion":
        return "Keine Runtime-Agenten, kein MCP, kein Model Routing und keine LLM-Metriken im Thesis-Kern."
    if chapter_id in {"ch_02_theory_literature", "ch_03_data_method"}:
        return (
            "Quellenstatus nicht automatisch hochstufen; "
            f"{source_summary['needs_full_review']} Full-Review-Gates bleiben sichtbar."
        )
    return "Keine Rohartefakt-Dumps und keine Claims ohne deterministisches Artefakt."


def _validate_checklist(*, checklist: pd.DataFrame, repo_root: Path) -> None:
    _require_columns(checklist, EXECUTION_COLUMNS, "thesis execution checklist")
    if checklist["task_id"].duplicated().any():
        raise ValueError("Thesis execution checklist contains duplicate task_id values.")
    if len(checklist) != len(CHAPTER_DETAILS):
        raise ValueError(f"Thesis execution checklist must contain {len(CHAPTER_DETAILS)} tasks.")
    for column in EXECUTION_COLUMNS:
        if checklist[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Thesis execution checklist contains empty {column}.")
    for row in checklist.to_dict(orient="records"):
        for artifact in _split_list(str(row["primary_inputs"])):
            if not (repo_root / artifact).exists():
                raise FileNotFoundError(f"Execution checklist input artifact is missing: {artifact}")

    joined = "\n".join(checklist.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Thesis execution checklist must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "review-access bleibt pausiert",
        "keine runtime-agenten",
        "keine roh",
        "quellenstatus nicht automatisch hochstufen",
        "14. juni 2026",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Thesis execution checklist missing required guardrails: " + ", ".join(missing))


def _render_execution_doc(checklist: pd.DataFrame) -> str:
    display = checklist[
        [
            "task_id",
            "chapter_title",
            "execution_phase",
            "table_figure_items",
            "source_gate_de",
            "draft_action_de",
            "done_when_de",
            "advisor_question_ids",
        ]
    ]
    return (
        "# Thesis Execution Checklist\n\n"
        "Diese Checkliste uebersetzt die Highlevel-View in konkrete "
        "Schreib- und Abnahmeaufgaben. Sie ist ein Projektsteuerungsartefakt "
        "und erzeugt keine neuen empirischen Resultate.\n\n"
        "## Counts\n\n"
        f"- Execution tasks: {len(checklist)}\n"
        f"- First task: {checklist.iloc[0]['task_id']}\n"
        f"- Final task: {checklist.iloc[-1]['task_id']}\n\n"
        "## Execution Tasks\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze diese Checkliste zum Schreiben der BA-Kapitel nach der "
        "Dozentenabstimmung. Review-Access bleibt pausiert. Runtime-Agenten, "
        "MCP, Model Routing, Rohartefakt-Dumps, Trading-Pfade und "
        "LLM-Metrikberechnung bleiben ausserhalb des aktiven Thesis-Kerns.\n"
    )


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required thesis execution input missing: {path}")
    return pd.read_csv(path)


def _resolve_under(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _split_list(value: str) -> list[str]:
    if value.lower() == "nan":
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def _join_unique(values: Sequence[str]) -> str:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        clean = value.strip()
        if clean and clean not in seen:
            seen.add(clean)
            output.append(clean)
    return " ".join(output)


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
