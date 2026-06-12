"""Build a chapter-level source-review checklist for H1-H2-H3 drafting."""

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

CHECKLIST_OUTPUT = "thesis_chapter_source_review_checklist.csv"
CHECKLIST_DOC_OUTPUT = "THESIS_CHAPTER_SOURCE_REVIEW_CHECKLIST.md"

CHECKLIST_COLUMNS: tuple[str, ...] = (
    "checklist_id",
    "thesis_area",
    "handoff_id",
    "check_order",
    "check_area",
    "source_artifact",
    "current_state",
    "completion_status",
    "required_evidence_de",
    "manual_action_de",
    "thesis_use_rule_de",
    "blocked_actions_de",
    "ready_for_bounded_draft",
    "ready_for_final_submission",
)

CORE_AREAS: tuple[str, ...] = ("H1", "H2", "H3")
CHECK_AREAS: tuple[str, ...] = (
    "method_interpretation_coverage",
    "literature_source_review",
    "result_package_integration",
    "limitation_blocked_wording",
    "final_citation_gate",
    "future_agent_boundary",
)


@dataclass(frozen=True)
class ChapterSourceReviewChecklistResult:
    """Generated chapter checklist paths and counts."""

    checklist_path: Path
    docs_path: Path
    checklist_rows: int
    bounded_draft_ready_rows: int
    final_submission_ready_rows: int
    final_blocked_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "checklist_path": str(self.checklist_path),
            "docs_path": str(self.docs_path),
            "checklist_rows": self.checklist_rows,
            "bounded_draft_ready_rows": self.bounded_draft_ready_rows,
            "final_submission_ready_rows": self.final_submission_ready_rows,
            "final_blocked_rows": self.final_blocked_rows,
        }


def generate_chapter_source_review_checklist(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> ChapterSourceReviewChecklistResult:
    """Generate the chapter checklist CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    handoff = _read_csv(results_dir / "thesis_source_review_chapter_handoff.csv")
    checklist = build_chapter_source_review_checklist(handoff=handoff)
    _validate_checklist(checklist)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    checklist_path = results_dir / CHECKLIST_OUTPUT
    docs_path = docs_dir / CHECKLIST_DOC_OUTPUT
    checklist.to_csv(checklist_path, index=False)
    docs_path.write_text(_render_checklist_doc(checklist), encoding="utf-8")

    return ChapterSourceReviewChecklistResult(
        checklist_path=checklist_path,
        docs_path=docs_path,
        checklist_rows=len(checklist),
        bounded_draft_ready_rows=int(checklist["ready_for_bounded_draft"].map(_bool_value).sum()),
        final_submission_ready_rows=int(
            checklist["ready_for_final_submission"].map(_bool_value).sum()
        ),
        final_blocked_rows=int(
            checklist["completion_status"].astype(str).str.startswith("final_blocked").sum()
        ),
    )


def build_chapter_source_review_checklist(*, handoff: pd.DataFrame) -> pd.DataFrame:
    """Return six checklist rows per empirical chapter handoff row."""

    _require_columns(
        handoff,
        (
            "handoff_id",
            "thesis_area",
            "method_evidence_ids",
            "interpretation_evidence_ids",
            "literature_source_ids",
            "selected_tables",
            "selected_figures",
            "mapped_method_count",
            "mapped_interpretation_count",
            "literature_source_count",
            "source_review_rows",
            "pending_review_rows",
            "final_citation_ready_rows",
            "result_package_items",
            "coverage_status",
            "chapter_write_status",
            "required_source_review_de",
            "mandatory_limitation_de",
            "blocked_wording_de",
            "future_agent_boundary_de",
        ),
        "source review chapter handoff",
    )

    rows: list[dict[str, object]] = []
    for chapter in handoff.sort_values("thesis_area").to_dict(orient="records"):
        area = str(chapter["thesis_area"])
        handoff_id = str(chapter["handoff_id"])
        pending_reviews = int(chapter["pending_review_rows"])
        review_rows = int(chapter["source_review_rows"])
        final_ready_rows = int(chapter["final_citation_ready_rows"])
        rows.extend(
            [
                _checklist_row(
                    chapter=chapter,
                    check_order=1,
                    check_area="method_interpretation_coverage",
                    source_artifact="data/results/thesis_source_review_chapter_handoff.csv",
                    current_state=str(chapter["coverage_status"]),
                    completion_status="bounded_draft_ready_coverage_checked",
                    required_evidence_de=(
                        f"{area}: Methoden `{chapter['method_evidence_ids']}` "
                        f"und Interpretationen `{chapter['interpretation_evidence_ids']}` "
                        "sind mit deterministischen Artefakten und Literatur IDs gemappt."
                    ),
                    manual_action_de="Beim Schreiben Evidence IDs sichtbar halten und keine neuen Claims hinzufuegen.",
                    thesis_use_rule_de="Bounded Draft erlaubt; finale Zitation bleibt Source-Review-abhaengig.",
                    blocked_actions_de=(
                        "Keine Methode oder Interpretation ohne deterministisches Artefakt, "
                        "Literatur ID und Limitation verwenden."
                    ),
                    ready_for_bounded_draft=True,
                    ready_for_final_submission=False,
                ),
                _checklist_row(
                    chapter=chapter,
                    check_order=2,
                    check_area="literature_source_review",
                    source_artifact="data/results/thesis_source_review_progress_ledger.csv",
                    current_state="manual_source_review_pending",
                    completion_status=(
                        "pending_manual_source_review"
                        if pending_reviews > 0
                        else "manual_source_review_recorded"
                    ),
                    required_evidence_de=(
                        f"{area}: {review_rows} Ledger-Zeilen; {pending_reviews} pending; "
                        f"{final_ready_rows} final-ready; Literatur IDs `{chapter['literature_source_ids']}`."
                    ),
                    manual_action_de=(
                        "Page-/Section-Note, Claim-Support, Blocked-Wording, Citation-Use, "
                        "Reviewer und Kommentar pro Quelle im Ledger erfassen."
                    ),
                    thesis_use_rule_de=(
                        "Draft darf Pending-Status zeigen; finale Quellenzitation erst nach "
                        "vollstaendiger manueller Review."
                    ),
                    blocked_actions_de="Keine Quellenstatus-Hochstufung und keine automatische Page Note.",
                    ready_for_bounded_draft=True,
                    ready_for_final_submission=pending_reviews == 0 and final_ready_rows == review_rows,
                ),
                _checklist_row(
                    chapter=chapter,
                    check_order=3,
                    check_area="result_package_integration",
                    source_artifact="data/results/thesis_result_package_traceability.csv",
                    current_state="core_package_ready_for_bounded_draft",
                    completion_status="bounded_draft_ready_result_package_checked",
                    required_evidence_de=(
                        f"{area}: Nur `{chapter['result_package_items']}` als Tabellen/Figuren "
                        "in den Kern integrieren."
                    ),
                    manual_action_de="Caption, Quelle, Limitation und Evidence IDs je Tabelle/Figur pruefen.",
                    thesis_use_rule_de=(
                        "Resultate thesis-ready als wenige starke Tabellen/Figuren schreiben; "
                        "Rohartefakte bleiben Nachweis oder Anhang."
                    ),
                    blocked_actions_de=(
                        "Keine Rohartefakt-Dumps, keine neuen Kennzahlen und keine zusaetzlichen "
                        "Tabellen/Figuren ohne aktualisierte Maps."
                    ),
                    ready_for_bounded_draft=True,
                    ready_for_final_submission=False,
                ),
                _checklist_row(
                    chapter=chapter,
                    check_order=4,
                    check_area="limitation_blocked_wording",
                    source_artifact="data/results/thesis_source_review_chapter_handoff.csv",
                    current_state="wording_guard_required",
                    completion_status="bounded_draft_ready_wording_guard_required",
                    required_evidence_de=(
                        f"{area}: Limitation `{chapter['mandatory_limitation_de']}`; "
                        f"blocked wording `{chapter['blocked_wording_de']}`."
                    ),
                    manual_action_de="Kapitelabschnitt gegen Limitation und blockiertes Wording pruefen.",
                    thesis_use_rule_de="Nur bounded wording verwenden und Limitation im Kapitel sichtbar halten.",
                    blocked_actions_de=(
                        "Keine Universal-, Intraday-, Kausalitaets-, Private-Information-, "
                        "Profitabilitaets- oder Tradeability-Claims."
                    ),
                    ready_for_bounded_draft=True,
                    ready_for_final_submission=False,
                ),
                _checklist_row(
                    chapter=chapter,
                    check_order=5,
                    check_area="final_citation_gate",
                    source_artifact="data/results/thesis_source_review_progress_ledger.csv",
                    current_state=str(chapter["chapter_write_status"]),
                    completion_status=(
                        "final_citation_ready"
                        if pending_reviews == 0 and final_ready_rows == review_rows
                        else "final_blocked_source_review_pending"
                    ),
                    required_evidence_de=str(chapter["required_source_review_de"]),
                    manual_action_de="Erst nach abgeschlossener manueller Review finale Zitation formatieren.",
                    thesis_use_rule_de="Keine finale Zitation, solange Ledger-Zeilen pending sind.",
                    blocked_actions_de=(
                        "Keine finale Zitation, keine Candidate-Quellen als Thesis-Evidence "
                        "und keine stillschweigende Entfernung offener Gates."
                    ),
                    ready_for_bounded_draft=True,
                    ready_for_final_submission=pending_reviews == 0 and final_ready_rows == review_rows,
                ),
                _checklist_row(
                    chapter=chapter,
                    check_order=6,
                    check_area="future_agent_boundary",
                    source_artifact="data/results/thesis_agent_pipeline_upgrade_plan.csv",
                    current_state="future_documentation_only",
                    completion_status="future_documentation_only_no_runtime_activation",
                    required_evidence_de=str(chapter["future_agent_boundary_de"]),
                    manual_action_de="Agentenideen nur als Future Work notieren; kein Laufzeitpfad im BA-Kern.",
                    thesis_use_rule_de="Agentenpipeline darf nur als spaeterer, auditierter Ausblick erscheinen.",
                    blocked_actions_de=(
                        "Keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken, "
                        "keine Rohdaten-Prompts, keine Wallet-Adress-Exposition und keine Trading-Pfade."
                    ),
                    ready_for_bounded_draft=True,
                    ready_for_final_submission=False,
                ),
            ]
        )
        if area not in CORE_AREAS:
            raise ValueError(f"Unexpected thesis area in chapter checklist: {area}")
        if not handoff_id:
            raise ValueError(f"Missing handoff id for {area}.")
    return pd.DataFrame(rows, columns=CHECKLIST_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_chapter_source_review_checklist(
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
    chapter: dict[str, object],
    check_order: int,
    check_area: str,
    source_artifact: str,
    current_state: str,
    completion_status: str,
    required_evidence_de: str,
    manual_action_de: str,
    thesis_use_rule_de: str,
    blocked_actions_de: str,
    ready_for_bounded_draft: bool,
    ready_for_final_submission: bool,
) -> dict[str, object]:
    area = str(chapter["thesis_area"])
    return {
        "checklist_id": f"check_{area.lower()}_{check_order:02d}_{check_area}",
        "thesis_area": area,
        "handoff_id": str(chapter["handoff_id"]),
        "check_order": check_order,
        "check_area": check_area,
        "source_artifact": source_artifact,
        "current_state": current_state,
        "completion_status": completion_status,
        "required_evidence_de": required_evidence_de,
        "manual_action_de": manual_action_de,
        "thesis_use_rule_de": thesis_use_rule_de,
        "blocked_actions_de": blocked_actions_de,
        "ready_for_bounded_draft": ready_for_bounded_draft,
        "ready_for_final_submission": ready_for_final_submission,
    }


def _validate_checklist(checklist: pd.DataFrame) -> None:
    _require_columns(checklist, CHECKLIST_COLUMNS, "chapter source review checklist")
    if len(checklist) != len(CORE_AREAS) * len(CHECK_AREAS):
        raise ValueError("Chapter source review checklist must contain 18 rows.")
    if checklist["checklist_id"].duplicated().any():
        raise ValueError("Chapter source review checklist contains duplicate checklist_id values.")
    if set(checklist["thesis_area"]) != set(CORE_AREAS):
        raise ValueError("Chapter source review checklist must cover H1, H2, and H3.")
    for area, group in checklist.groupby("thesis_area"):
        if tuple(group.sort_values("check_order")["check_area"]) != CHECK_AREAS:
            raise ValueError(f"Chapter source review checklist has wrong check areas for {area}.")
    for column in CHECKLIST_COLUMNS:
        if checklist[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Chapter source review checklist contains empty {column}.")
    final_ready = checklist["ready_for_final_submission"].map(_bool_value)
    if final_ready.any():
        ready_status = checklist.loc[final_ready, "completion_status"]
        if not ready_status.eq("final_citation_ready").all():
            raise ValueError("Final-ready checklist rows must have final_citation_ready status.")
    joined = "\n".join(checklist.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Chapter source review checklist must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "source-review",
        "keine finale zitation",
        "keine quellenstatus-hochstufung",
        "keine rohartefakt-dumps",
        "keine runtime-agenten",
        "llm_audit_log",
        "max 50 rows",
        "page-/section-note",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Chapter source review checklist missing required terms: " + ", ".join(missing))


def _render_checklist_doc(checklist: pd.DataFrame) -> str:
    status_counts = checklist["completion_status"].value_counts().to_dict()
    display = checklist[
        [
            "checklist_id",
            "thesis_area",
            "check_order",
            "check_area",
            "completion_status",
            "ready_for_bounded_draft",
            "ready_for_final_submission",
            "manual_action_de",
        ]
    ]
    return (
        "# Chapter Source Review Checklist\n\n"
        "Diese Checkliste macht aus dem H1-H2-H3 Chapter Handoff konkrete "
        "manuelle Abnahmeschritte. Sie liest keine Quelleninhalte, berechnet "
        "keine Kennzahlen, promotet keinen Quellenstatus und aktiviert keine "
        "Runtime-Agenten. Sie ist eine Schreib- und Review-Kontrolle fuer den "
        "BA-Draft, nicht die finale Quellenfreigabe.\n\n"
        "## Counts\n\n"
        f"- Checklist rows: {len(checklist)}\n"
        f"- Bounded draft ready rows: {int(checklist['ready_for_bounded_draft'].map(_bool_value).sum())}\n"
        f"- Final submission ready rows: {int(checklist['ready_for_final_submission'].map(_bool_value).sum())}\n"
        f"- Final blocked source review rows: {int(status_counts.get('final_blocked_source_review_pending', 0))}\n"
        f"- Pending manual source review rows: {int(status_counts.get('pending_manual_source_review', 0))}\n"
        f"- Future documentation-only rows: {int(status_counts.get('future_documentation_only_no_runtime_activation', 0))}\n\n"
        "## Checklist Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze die Checkliste beim Schreiben und Kontrollieren von H1, H2 und "
        "H3. Jeder Kapitelteil muss Evidence IDs, Literatur IDs, Artefakte, "
        "kuratierte Tabellen/Figuren, Limitationen und Source-Review-Gates "
        "sichtbar halten. Keine finale Zitation ohne manuelle Ledger-Review. "
        "Keine Rohartefakt-Dumps, keine Quellenstatus-Hochstufung, keine "
        "Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken, "
        "keine Wallet-Adress-Exposition und keine Trading-Pfade.\n"
    )


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "ja"}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required chapter source review checklist input missing: {path}")
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
