"""Build the next thesis drafting sequence from current project gates."""

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

DRAFTING_OUTPUT = "thesis_drafting_sequence.csv"
DRAFTING_DOC_OUTPUT = "THESIS_DRAFTING_SEQUENCE.md"

DRAFTING_COLUMNS: tuple[str, ...] = (
    "sequence_id",
    "priority_order",
    "workstream_id",
    "thesis_section",
    "readiness_gate_area",
    "current_status",
    "draft_permission",
    "primary_artifact",
    "supporting_count",
    "writing_action_de",
    "acceptance_evidence_de",
    "blocker_or_gate_de",
    "must_not_claim_de",
)

WORKSTREAM_GATE_AREAS: dict[str, str] = {
    "work_01_source_review": "source_review",
    "work_02_method_chapters": "chapter_source_mapping",
    "work_03_h1_results": "h1_h2_h3_results",
    "work_04_h2_h3_results": "h1_h2_h3_results",
    "work_05_table_figure_integration": "table_figure_package",
    "work_06_monitor_appendix": "monitor_appendix",
    "work_07_swiss_result_gate": "swiss_result_gate",
    "work_08_agent_outlook": "agent_future_work",
    "work_09_advisor_iteration": "advisor_handoff",
    "work_10_final_qa": "final_qa",
}

MUST_NOT_CLAIM: dict[str, str] = {
    "work_01_source_review": "Quellenstatus nicht automatisch hochstufen und keine finale Zitation ohne Human Review.",
    "work_02_method_chapters": "Keine Methodenbehauptung ohne deterministisches Artefakt, reviewte Quelle oder sichtbaren Pending-Status.",
    "work_03_h1_results": "Keine universelle Polymarket-Ueberlegenheit und keine RCP-Wahrscheinlichkeitsclaims.",
    "work_04_h2_h3_results": "Keine Intraday-Speed-, Granger-Kausalitaets-, Private-Information- oder Profitabilitaetsclaims.",
    "work_05_table_figure_integration": "Keine Rohartefakt-Dumps und keine neuen Tabellen/Figuren ohne Evidence-Map-Update.",
    "work_06_monitor_appendix": "Review-Access bleibt pausiert; keine Wallet-Adress-Exposition, keine Order-/Trading-Pfade und keine thesis-facing Alert-Evidenz.",
    "work_07_swiss_result_gate": "Offizielles Resultat vom 14. Juni 2026 ist gemappt; keine Effizienz-, Mispricing-, Tradeability- oder Vote-Share-Superiority-Claims.",
    "work_08_agent_outlook": "Keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken und keine Trading-Pfade.",
    "work_09_advisor_iteration": "Keinen Scope-Ausbau starten, bevor der H1-H2-H3-Kern geschrieben und abgestimmt ist.",
    "work_10_final_qa": "Keine finale Abgabebereitschaft behaupten, solange Source Review, Swiss-Gate oder DOCX-Render-QA offen sind.",
}


@dataclass(frozen=True)
class ThesisDraftingSequenceResult:
    """Generated drafting-sequence paths and counts."""

    sequence_path: Path
    docs_path: Path
    sequence_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "sequence_path": str(self.sequence_path),
            "docs_path": str(self.docs_path),
            "sequence_rows": self.sequence_rows,
        }


def generate_thesis_drafting_sequence(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> ThesisDraftingSequenceResult:
    """Generate the thesis drafting sequence CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)
    next_work = _read_csv(results_dir / "thesis_next_work_plan.csv")
    readiness = _read_csv(results_dir / "thesis_submission_readiness_board.csv")
    chapter_bindings = _read_csv(results_dir / "thesis_chapter_source_bindings.csv")
    source_review = _read_csv(results_dir / "thesis_source_review_execution.csv")
    table_figure_captions = _read_csv(results_dir / "thesis_table_figure_captions.csv")

    sequence = build_thesis_drafting_sequence(
        next_work=next_work,
        readiness=readiness,
        chapter_bindings=chapter_bindings,
        source_review=source_review,
        table_figure_captions=table_figure_captions,
    )
    _validate_sequence(sequence=sequence, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    sequence_path = results_dir / DRAFTING_OUTPUT
    docs_path = docs_dir / DRAFTING_DOC_OUTPUT
    sequence.to_csv(sequence_path, index=False)
    docs_path.write_text(_render_sequence_doc(sequence), encoding="utf-8")

    return ThesisDraftingSequenceResult(
        sequence_path=sequence_path,
        docs_path=docs_path,
        sequence_rows=len(sequence),
    )


def build_thesis_drafting_sequence(
    *,
    next_work: pd.DataFrame,
    readiness: pd.DataFrame,
    chapter_bindings: pd.DataFrame,
    source_review: pd.DataFrame,
    table_figure_captions: pd.DataFrame,
) -> pd.DataFrame:
    """Return one ordered drafting decision per workstream."""

    _require_columns(
        next_work,
        (
            "workstream_id",
            "priority_order",
            "thesis_section",
            "current_artifact",
            "next_action",
            "done_when",
            "blocked_until",
            "guardrail",
        ),
        "next work plan",
    )
    _require_columns(
        readiness,
        (
            "gate_area",
            "current_status",
            "primary_artifact",
            "evidence_or_control_count",
            "next_action_de",
            "blocker_or_limit_de",
        ),
        "submission readiness board",
    )
    _require_columns(chapter_bindings, ("chapter_id", "source_ids"), "chapter bindings")
    _require_columns(source_review, ("review_stage",), "source review execution")
    _require_columns(
        table_figure_captions,
        ("include_in_core_package",),
        "table figure captions",
    )

    readiness_by_area = _readiness_by_area(readiness)
    chapter_count = len(chapter_bindings)
    priority_source_count = int((source_review["review_stage"] == "review_now_priority_1").sum())
    core_table_figure_count = _core_table_figure_count(table_figure_captions)

    rows: list[dict[str, object]] = []
    ordered = next_work.sort_values("priority_order", kind="stable")
    for next_row in ordered.to_dict(orient="records"):
        workstream_id = str(next_row["workstream_id"])
        gate_area = WORKSTREAM_GATE_AREAS.get(workstream_id)
        if gate_area is None:
            raise ValueError(f"Drafting sequence missing gate mapping for workstream: {workstream_id}")
        gate = readiness_by_area[gate_area]
        supporting_count = _supporting_count(
            gate_area=gate_area,
            gate=gate,
            chapter_count=chapter_count,
            priority_source_count=priority_source_count,
            core_table_figure_count=core_table_figure_count,
        )
        rows.append(
            {
                "sequence_id": f"draft_{int(next_row['priority_order']):02d}_{workstream_id.removeprefix('work_')}",
                "priority_order": int(next_row["priority_order"]),
                "workstream_id": workstream_id,
                "thesis_section": next_row["thesis_section"],
                "readiness_gate_area": gate_area,
                "current_status": gate["current_status"],
                "draft_permission": _draft_permission(str(gate["current_status"])),
                "primary_artifact": _primary_artifact_for_sequence(next_row, gate),
                "supporting_count": supporting_count,
                "writing_action_de": _writing_action(next_row, gate),
                "acceptance_evidence_de": _acceptance_evidence(next_row, gate),
                "blocker_or_gate_de": _blocker_or_gate(next_row, gate),
                "must_not_claim_de": MUST_NOT_CLAIM[workstream_id],
            }
        )

    return pd.DataFrame(rows, columns=DRAFTING_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_thesis_drafting_sequence(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _readiness_by_area(readiness: pd.DataFrame) -> dict[str, dict[str, object]]:
    duplicated = readiness["gate_area"].duplicated()
    if duplicated.any():
        duplicate_areas = sorted(readiness.loc[duplicated, "gate_area"].astype(str).unique())
        raise ValueError("Readiness board contains duplicate gate areas: " + ", ".join(duplicate_areas))
    by_area = {
        str(row["gate_area"]): row
        for row in readiness.to_dict(orient="records")
    }
    missing = sorted(set(WORKSTREAM_GATE_AREAS.values()).difference(by_area))
    if missing:
        raise ValueError("Readiness board missing gate areas: " + ", ".join(missing))
    return by_area


def _core_table_figure_count(table_figure_captions: pd.DataFrame) -> int:
    values = table_figure_captions["include_in_core_package"]
    if values.dtype == bool:
        return int(values.sum())
    return int(values.astype(str).str.lower().isin({"true", "1", "yes"}).sum())


def _supporting_count(
    *,
    gate_area: str,
    gate: dict[str, object],
    chapter_count: int,
    priority_source_count: int,
    core_table_figure_count: int,
) -> int:
    if gate_area == "source_review":
        return priority_source_count
    if gate_area == "chapter_source_mapping":
        return chapter_count
    if gate_area == "table_figure_package":
        return core_table_figure_count
    return int(gate["evidence_or_control_count"])


def _draft_permission(status: str) -> str:
    if status in {"ready_for_draft", "ready_for_bounded_result_draft", "ready_for_draft_integration"}:
        return "write_now_bounded"
    if status == "ready_for_advisor_discussion":
        return "advisor_discussion_now"
    if status == "final_blocked_source_review":
        return "review_now_final_blocked"
    if status == "appendix_only_pending_human_review":
        return "appendix_only_pending_review"
    if status == "final_blocked_official_result":
        return "descriptive_only_final_blocked"
    if status == "post_result_mapped_source_review_pending":
        return "write_now_bounded"
    if status == "deferred_future_work_only":
        return "future_work_only"
    if status == "pending_after_draft":
        return "qa_after_draft"
    raise ValueError(f"Unsupported readiness status: {status}")


def _primary_artifact_for_sequence(
    next_row: dict[str, object],
    gate: dict[str, object],
) -> str:
    artifacts = _split_semicolon(str(next_row["current_artifact"]))
    gate_artifacts = _split_semicolon(str(gate["primary_artifact"]))
    return "; ".join(_dedupe([*artifacts, *gate_artifacts]))


def _writing_action(next_row: dict[str, object], gate: dict[str, object]) -> str:
    return f"{next_row['next_action']} Gate-Aktion: {gate['next_action_de']}"


def _acceptance_evidence(next_row: dict[str, object], gate: dict[str, object]) -> str:
    return f"{next_row['done_when']} Statusnachweis: {gate['current_status']}."


def _blocker_or_gate(next_row: dict[str, object], gate: dict[str, object]) -> str:
    return f"{next_row['blocked_until']} Gate: {gate['blocker_or_limit_de']}"


def _validate_sequence(*, sequence: pd.DataFrame, repo_root: Path) -> None:
    _require_columns(sequence, DRAFTING_COLUMNS, "thesis drafting sequence")
    if sequence["sequence_id"].duplicated().any():
        raise ValueError("Thesis drafting sequence contains duplicate sequence_id values.")
    if len(sequence) != len(WORKSTREAM_GATE_AREAS):
        raise ValueError(f"Thesis drafting sequence must contain {len(WORKSTREAM_GATE_AREAS)} steps.")
    if sequence["priority_order"].tolist() != sorted(sequence["priority_order"].tolist()):
        raise ValueError("Thesis drafting sequence must be sorted by priority_order.")
    for column in DRAFTING_COLUMNS:
        if sequence[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Thesis drafting sequence contains empty {column}.")
    for artifact_group in sequence["primary_artifact"].astype(str):
        for artifact in _split_semicolon(artifact_group):
            if not (repo_root / artifact).exists():
                raise FileNotFoundError(f"Drafting sequence artifact is missing: {artifact}")

    joined = "\n".join(sequence.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Thesis drafting sequence must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "review_now_final_blocked",
        "post_result_mapped_source_review_pending",
        "future_work_only",
        "keine runtime-agenten",
        "keine roh",
        "review-access bleibt pausiert",
        "14. juni 2026",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Thesis drafting sequence missing required gates: " + ", ".join(missing))


def _render_sequence_doc(sequence: pd.DataFrame) -> str:
    permission_counts = sequence["draft_permission"].value_counts().to_dict()
    display = sequence[
        [
            "sequence_id",
            "thesis_section",
            "draft_permission",
            "current_status",
            "supporting_count",
            "writing_action_de",
            "blocker_or_gate_de",
            "must_not_claim_de",
        ]
    ]
    return (
        "# Thesis Drafting Sequence\n\n"
        "Diese Sequenz beantwortet die Highlevel-Frage, wie das Projekt jetzt "
        "weitergeht. Sie ordnet die vorhandenen Workstreams nach Schreibreihenfolge "
        "und trennt Draft-Arbeit, finale Blocker und Future-Work. Sie erzeugt "
        "keine neuen empirischen Resultate.\n\n"
        "## Counts\n\n"
        f"- Drafting steps: {len(sequence)}\n"
        f"- Bounded write-now steps: {int(permission_counts.get('write_now_bounded', 0))}\n"
        f"- Final-blocked review steps: {int(permission_counts.get('review_now_final_blocked', 0))}\n"
        f"- Descriptive-only final-blocked steps: {int(permission_counts.get('descriptive_only_final_blocked', 0))}\n"
        f"- Future-work-only steps: {int(permission_counts.get('future_work_only', 0))}\n\n"
        "## Drafting Steps\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze diese Sequenz als naechste Arbeitsreihenfolge nach dem "
        "Dozenten-Handoff. Review-Access bleibt pausiert. Source Review, Swiss "
        "Source-/Citation-Gate und DOCX-Render-QA bleiben finale Gates; Runtime-Agenten, "
        "MCP, Model Routing, Rohartefakt-Dumps und Trading-Pfade bleiben "
        "ausserhalb des aktiven Thesis-Kerns.\n"
    )


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required thesis drafting input missing: {path}")
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


def _dedupe(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        clean = value.strip()
        if clean and clean not in seen:
            seen.add(clean)
            output.append(clean)
    return output


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
