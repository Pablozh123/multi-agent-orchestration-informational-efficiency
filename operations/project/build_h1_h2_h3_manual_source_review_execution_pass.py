"""Build a manual H1-H2-H3 source-review execution pass."""

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

EXECUTION_PASS_OUTPUT = "thesis_h1_h2_h3_manual_source_review_execution_pass.csv"
EXECUTION_PASS_DOC_OUTPUT = "THESIS_H1_H2_H3_MANUAL_SOURCE_REVIEW_EXECUTION_PASS.md"

EXECUTION_PASS_COLUMNS: tuple[str, ...] = (
    "execution_id",
    "execution_order",
    "execution_batch",
    "thesis_area",
    "section_id",
    "chapter_title_de",
    "source_priority_order",
    "source_id",
    "source_title",
    "source_status",
    "source_relevance",
    "source_known_in_literature_index",
    "evidence_id",
    "item_type",
    "note_id",
    "ledger_id",
    "selected_table",
    "selected_figure",
    "table_figure_context_de",
    "deterministic_artifact",
    "primary_artifact_exists",
    "coverage_status",
    "access_route",
    "review_source_locator",
    "manual_locator_task_de",
    "review_focus_de",
    "bounded_claim_check_de",
    "blocked_wording_check_de",
    "current_review_status",
    "current_claim_support_decision",
    "current_blocked_wording_check",
    "current_citation_use_decision",
    "review_progress_state",
    "source_status_change_allowed",
    "final_citation_ready",
    "chapter_pending_review_rows",
    "required_reviewer_output_de",
    "manual_execution_instruction_de",
    "final_citation_gate_de",
    "ready_for_bounded_draft",
    "ready_for_final_submission",
    "do_not_claim_de",
    "next_action_de",
)

CORE_AREAS: tuple[str, ...] = ("H1", "H2", "H3")
AREA_ORDER: dict[str, int] = {area: index for index, area in enumerate(CORE_AREAS, start=1)}
ITEM_ORDER: dict[str, int] = {"method": 0, "interpretation": 1}


@dataclass(frozen=True)
class H1H2H3ManualSourceReviewExecutionPassResult:
    """Generated manual source-review execution pass paths and counts."""

    execution_pass_path: Path
    docs_path: Path
    execution_rows: int
    h1_rows: int
    h2_rows: int
    h3_rows: int
    unique_source_rows: int
    final_citation_ready_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "execution_pass_path": str(self.execution_pass_path),
            "docs_path": str(self.docs_path),
            "execution_rows": self.execution_rows,
            "h1_rows": self.h1_rows,
            "h2_rows": self.h2_rows,
            "h3_rows": self.h3_rows,
            "unique_source_rows": self.unique_source_rows,
            "final_citation_ready_rows": self.final_citation_ready_rows,
        }


def generate_h1_h2_h3_manual_source_review_execution_pass(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> H1H2H3ManualSourceReviewExecutionPassResult:
    """Generate the manual H1-H2-H3 source-review execution pass."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    notes = _read_csv(results_dir / "thesis_h1_h2_h3_source_review_notes.csv")
    ledger = _read_csv(results_dir / "thesis_source_review_progress_ledger.csv")
    decision_packets = _read_csv(results_dir / "thesis_source_review_decision_packets.csv")
    source_access = _read_csv(results_dir / "thesis_source_access_audit.csv")
    source_coverage = _read_csv(results_dir / "thesis_method_interpretation_source_coverage.csv")
    chapter_handoff = _read_csv(results_dir / "thesis_source_review_chapter_handoff.csv")
    captions = _read_csv(results_dir / "thesis_table_figure_captions.csv")

    execution_pass = build_h1_h2_h3_manual_source_review_execution_pass(
        notes=notes,
        ledger=ledger,
        decision_packets=decision_packets,
        source_access=source_access,
        source_coverage=source_coverage,
        chapter_handoff=chapter_handoff,
        captions=captions,
    )
    _validate_execution_pass(execution_pass)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    execution_pass_path = results_dir / EXECUTION_PASS_OUTPUT
    docs_path = docs_dir / EXECUTION_PASS_DOC_OUTPUT
    execution_pass.to_csv(execution_pass_path, index=False)
    docs_path.write_text(_render_execution_pass_doc(execution_pass), encoding="utf-8")

    area_counts = execution_pass["thesis_area"].value_counts().to_dict()
    return H1H2H3ManualSourceReviewExecutionPassResult(
        execution_pass_path=execution_pass_path,
        docs_path=docs_path,
        execution_rows=len(execution_pass),
        h1_rows=int(area_counts.get("H1", 0)),
        h2_rows=int(area_counts.get("H2", 0)),
        h3_rows=int(area_counts.get("H3", 0)),
        unique_source_rows=int(execution_pass["source_id"].nunique()),
        final_citation_ready_rows=int(
            execution_pass["final_citation_ready"].map(_bool_value).sum()
        ),
    )


def build_h1_h2_h3_manual_source_review_execution_pass(
    *,
    notes: pd.DataFrame,
    ledger: pd.DataFrame,
    decision_packets: pd.DataFrame,
    source_access: pd.DataFrame,
    source_coverage: pd.DataFrame,
    chapter_handoff: pd.DataFrame,
    captions: pd.DataFrame,
) -> pd.DataFrame:
    """Return one execution row per H1-H2-H3 source-review ledger row."""

    _require_columns(
        notes,
        (
            "note_id",
            "thesis_area",
            "section_id",
            "source_id",
            "evidence_id",
            "item_type",
            "selected_table",
            "selected_figure",
            "deterministic_artifact",
            "access_route",
            "manual_locator_task_de",
            "review_focus_de",
            "bounded_claim_check_de",
            "blocked_wording_check_de",
            "do_not_claim_de",
            "next_action_de",
        ),
        "H1-H2-H3 source review notes",
    )
    _require_columns(
        ledger,
        (
            "ledger_id",
            "note_id",
            "review_status",
            "claim_support_decision",
            "blocked_wording_check",
            "citation_use_decision",
            "review_progress_state",
            "source_status_change_allowed",
            "final_citation_ready",
        ),
        "source review progress ledger",
    )
    _require_columns(
        decision_packets,
        (
            "source_id",
            "evidence_id",
            "thesis_area",
            "item_type",
            "source_priority_order",
            "final_citation_gate",
            "required_manual_decision_de",
        ),
        "source review decision packets",
    )
    _require_columns(
        source_access,
        (
            "source_id",
            "source_title",
            "source_status",
            "review_source_locator",
        ),
        "source access audit",
    )
    _require_columns(
        source_coverage,
        (
            "evidence_id",
            "source_id",
            "source_known_in_literature_index",
            "source_relevance",
            "primary_artifact_exists",
            "coverage_status",
        ),
        "method interpretation source coverage",
    )
    _require_columns(
        chapter_handoff,
        (
            "thesis_area",
            "chapter_title_de",
            "pending_review_rows",
        ),
        "source review chapter handoff",
    )
    _require_columns(
        captions,
        (
            "package_id",
            "thesis_label",
            "caption_de",
            "include_in_core_package",
        ),
        "table figure captions",
    )

    notes_by_id = notes.set_index("note_id").to_dict(orient="index")
    decision_by_key = {
        (
            str(row["source_id"]),
            str(row["evidence_id"]),
            str(row["thesis_area"]),
            str(row["item_type"]),
        ): row
        for row in decision_packets.to_dict(orient="records")
    }
    access_by_source = source_access.set_index("source_id").to_dict(orient="index")
    coverage_by_key = {
        (str(row["source_id"]), str(row["evidence_id"])): row
        for row in source_coverage.to_dict(orient="records")
    }
    handoff_by_area = chapter_handoff.set_index("thesis_area").to_dict(orient="index")
    caption_by_id = captions.set_index("package_id").to_dict(orient="index")

    seeded_rows: list[dict[str, object]] = []
    for ledger_row in ledger.to_dict(orient="records"):
        note_id = str(ledger_row["note_id"])
        note = notes_by_id.get(note_id)
        if note is None:
            raise ValueError(f"Manual execution pass missing note row for {note_id}.")
        thesis_area = str(note["thesis_area"])
        source_id = str(note["source_id"])
        evidence_id = str(note["evidence_id"])
        item_type = str(note["item_type"])
        decision = decision_by_key.get((source_id, evidence_id, thesis_area, item_type))
        if decision is None:
            raise ValueError(
                "Manual execution pass missing decision packet for "
                f"{source_id}/{evidence_id}/{thesis_area}/{item_type}."
            )
        access = access_by_source.get(source_id)
        if access is None:
            raise ValueError(f"Manual execution pass missing source access row for {source_id}.")
        coverage = coverage_by_key.get((source_id, evidence_id))
        if coverage is None:
            raise ValueError(
                f"Manual execution pass missing source coverage row for {source_id}/{evidence_id}."
            )
        handoff = handoff_by_area.get(thesis_area)
        if handoff is None:
            raise ValueError(f"Manual execution pass missing chapter handoff row for {thesis_area}.")
        selected_table = _clean(note["selected_table"])
        selected_figure = _clean(note["selected_figure"])
        seeded_rows.append(
            {
                "_area_order": AREA_ORDER.get(thesis_area, 99),
                "_item_order": ITEM_ORDER.get(item_type, 9),
                "execution_batch": _execution_batch(thesis_area),
                "thesis_area": thesis_area,
                "section_id": _clean(note["section_id"]),
                "chapter_title_de": _clean(handoff["chapter_title_de"]),
                "source_priority_order": int(decision["source_priority_order"]),
                "source_id": source_id,
                "source_title": _clean(access["source_title"]),
                "source_status": _clean(access["source_status"]),
                "source_relevance": _clean(coverage["source_relevance"]),
                "source_known_in_literature_index": _bool_value(
                    coverage["source_known_in_literature_index"]
                ),
                "evidence_id": evidence_id,
                "item_type": item_type,
                "note_id": note_id,
                "ledger_id": _clean(ledger_row["ledger_id"]),
                "selected_table": selected_table,
                "selected_figure": selected_figure,
                "table_figure_context_de": _table_figure_context(
                    selected_table=selected_table,
                    selected_figure=selected_figure,
                    caption_by_id=caption_by_id,
                ),
                "deterministic_artifact": _clean(note["deterministic_artifact"]),
                "primary_artifact_exists": _bool_value(coverage["primary_artifact_exists"]),
                "coverage_status": _clean(coverage["coverage_status"]),
                "access_route": _clean(note["access_route"]),
                "review_source_locator": _clean(access["review_source_locator"]),
                "manual_locator_task_de": _clean(note["manual_locator_task_de"]),
                "review_focus_de": _clean(note["review_focus_de"]),
                "bounded_claim_check_de": _clean(note["bounded_claim_check_de"]),
                "blocked_wording_check_de": _clean(note["blocked_wording_check_de"]),
                "current_review_status": _clean(ledger_row["review_status"]),
                "current_claim_support_decision": _clean(ledger_row["claim_support_decision"]),
                "current_blocked_wording_check": _clean(ledger_row["blocked_wording_check"]),
                "current_citation_use_decision": _clean(ledger_row["citation_use_decision"]),
                "review_progress_state": _clean(ledger_row["review_progress_state"]),
                "source_status_change_allowed": _bool_value(
                    ledger_row["source_status_change_allowed"]
                ),
                "final_citation_ready": _bool_value(ledger_row["final_citation_ready"]),
                "chapter_pending_review_rows": int(handoff["pending_review_rows"]),
                "required_reviewer_output_de": _required_reviewer_output_de(
                    _clean(decision["required_manual_decision_de"])
                ),
                "manual_execution_instruction_de": _manual_execution_instruction_de(
                    thesis_area=thesis_area,
                    source_id=source_id,
                    evidence_id=evidence_id,
                    item_type=item_type,
                ),
                "final_citation_gate_de": _final_citation_gate_de(
                    _clean(decision["final_citation_gate"])
                ),
                "ready_for_bounded_draft": True,
                "ready_for_final_submission": _bool_value(ledger_row["final_citation_ready"]),
                "do_not_claim_de": _clean(note["do_not_claim_de"]),
                "next_action_de": _clean(note["next_action_de"]),
            }
        )

    sorted_rows = sorted(
        seeded_rows,
        key=lambda row: (
            int(row["_area_order"]),
            int(row["source_priority_order"]),
            str(row["source_id"]),
            int(row["_item_order"]),
            str(row["evidence_id"]),
        ),
    )
    rows: list[dict[str, object]] = []
    for order, row in enumerate(sorted_rows, start=1):
        public_row = {
            column: row[column]
            for column in EXECUTION_PASS_COLUMNS
            if column not in {"execution_id", "execution_order"}
        }
        public_row["execution_order"] = order
        public_row["execution_id"] = (
            f"manual_exec_{order:02d}_{str(row['thesis_area']).lower()}_"
            f"{row['source_id']}__{row['evidence_id']}"
        )
        rows.append(public_row)

    frame = pd.DataFrame(rows)
    return frame.loc[:, EXECUTION_PASS_COLUMNS]


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_h1_h2_h3_manual_source_review_execution_pass(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_execution_pass(execution_pass: pd.DataFrame) -> None:
    _require_columns(execution_pass, EXECUTION_PASS_COLUMNS, "manual source-review execution pass")
    if execution_pass.empty:
        raise ValueError("Manual source-review execution pass must not be empty.")
    if execution_pass["execution_id"].duplicated().any():
        raise ValueError("Manual source-review execution pass contains duplicate execution_id values.")
    if set(execution_pass["thesis_area"]) != set(CORE_AREAS):
        raise ValueError("Manual source-review execution pass must cover H1, H2, and H3.")
    expected_order = list(range(1, len(execution_pass) + 1))
    if execution_pass["execution_order"].astype(int).tolist() != expected_order:
        raise ValueError("Manual source-review execution pass has non-sequential execution_order.")
    if execution_pass["source_status_change_allowed"].map(_bool_value).any():
        raise ValueError("Manual source-review execution pass must not allow source-status changes.")
    if not execution_pass["ready_for_bounded_draft"].map(_bool_value).all():
        raise ValueError("Manual source-review execution pass must remain bounded-draft-ready.")
    for column in (
        "execution_batch",
        "section_id",
        "chapter_title_de",
        "source_id",
        "source_title",
        "source_status",
        "source_relevance",
        "evidence_id",
        "selected_table",
        "selected_figure",
        "table_figure_context_de",
        "deterministic_artifact",
        "coverage_status",
        "access_route",
        "review_source_locator",
        "manual_locator_task_de",
        "review_focus_de",
        "bounded_claim_check_de",
        "blocked_wording_check_de",
        "required_reviewer_output_de",
        "manual_execution_instruction_de",
        "final_citation_gate_de",
        "do_not_claim_de",
        "next_action_de",
    ):
        if execution_pass[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Manual source-review execution pass contains empty {column}.")
    if not execution_pass["source_known_in_literature_index"].map(_bool_value).all():
        raise ValueError("Manual source-review execution pass has unknown literature sources.")
    if not execution_pass["primary_artifact_exists"].map(_bool_value).all():
        raise ValueError("Manual source-review execution pass has missing deterministic artifacts.")
    if execution_pass["coverage_status"].astype(str).str.contains("gap", case=False).any():
        raise ValueError("Manual source-review execution pass contains coverage gaps.")
    if not (
        execution_pass.loc[
            execution_pass["final_citation_ready"].map(_bool_value),
            "ready_for_final_submission",
        ].map(_bool_value)
    ).all():
        raise ValueError("Final-citation rows must also be final-submission-ready at row level.")
    joined = "\n".join(execution_pass.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Manual source-review execution pass must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "manual source review",
        "page-/section-note",
        "claim-support",
        "blocked-wording",
        "keine quellenstatus-hochstufung",
        "keine finale zitation",
        "keine rohartefakt-dumps",
        "keine runtime-agenten",
        "llm_audit_log",
        "max 50 rows",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError(
            "Manual source-review execution pass missing required terms: " + ", ".join(missing)
        )


def _render_execution_pass_doc(execution_pass: pd.DataFrame) -> str:
    area_counts = execution_pass["thesis_area"].value_counts().to_dict()
    batch_counts = execution_pass["execution_batch"].value_counts().sort_index().to_dict()
    display = execution_pass[
        [
            "execution_order",
            "execution_batch",
            "thesis_area",
            "source_id",
            "evidence_id",
            "item_type",
            "selected_table",
            "selected_figure",
            "review_progress_state",
            "required_reviewer_output_de",
            "final_citation_gate_de",
        ]
    ]
    batch_lines = "\n".join(
        f"- {batch}: {count} rows" for batch, count in batch_counts.items()
    )
    return (
        "# H1-H2-H3 Manual Source Review Execution Pass\n\n"
        "Dieser Pass ordnet die manuelle Source Review fuer den empirischen "
        "BA-Kern H1, H2 und H3. Er verbindet Ledger, Source Notes, "
        "Decision Packets, Source Coverage, Chapter Handoff und Tabellen-/"
        "Figurenkontext. Er liest keine Quelleninhalte, promotet keinen "
        "Quellenstatus und erzeugt keine finale Zitation.\n\n"
        "## Counts\n\n"
        f"- Execution rows: {len(execution_pass)}\n"
        f"- H1 rows: {int(area_counts.get('H1', 0))}\n"
        f"- H2 rows: {int(area_counts.get('H2', 0))}\n"
        f"- H3 rows: {int(area_counts.get('H3', 0))}\n"
        f"- Unique sources: {int(execution_pass['source_id'].nunique())}\n"
        f"- Final citation ready rows: {int(execution_pass['final_citation_ready'].map(_bool_value).sum())}\n"
        f"- Source-status change allowed rows: {int(execution_pass['source_status_change_allowed'].map(_bool_value).sum())}\n\n"
        "## Batches\n\n"
        f"{batch_lines}\n\n"
        "## Execution Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Arbeite diese Liste manuell source-by-source ab: Quelle oeffnen, "
        "Page-/Section-Note festhalten, Claim-Support entscheiden, "
        "Blocked-Wording pruefen und Citation-Use erst danach setzen. "
        "Keine Quellenstatus-Hochstufung, keine finale Zitation, keine "
        "Rohartefakt-Dumps und keine neuen thesis-facing Claims aus dieser "
        "Liste. Runtime-Agenten, MCP, Model Routing, LLM-Metriken, "
        "Rohdatenzugriff, Wallet-Adress-Exposition und Trading-Pfade bleiben "
        "deaktiviert. Spaetere Agentenhilfe darf nur mit separatem Goal, "
        "bounded inputs, max 50 rows, Tests und llm_audit_log geplant werden.\n"
    )


def _execution_batch(thesis_area: str) -> str:
    if thesis_area == "H1":
        return "batch_01_h1_forecast_quality_source_review"
    if thesis_area == "H2":
        return "batch_02_h2_event_window_source_review"
    if thesis_area == "H3":
        return "batch_03_h3_wallet_timing_source_review"
    return "batch_99_other_source_review"


def _table_figure_context(
    *,
    selected_table: str,
    selected_figure: str,
    caption_by_id: dict[str, dict[str, object]],
) -> str:
    parts: list[str] = []
    for package_id in [selected_table, selected_figure]:
        caption = caption_by_id.get(package_id)
        if caption is None:
            raise ValueError(f"Manual execution pass missing caption row for {package_id}.")
        if not _bool_value(caption["include_in_core_package"]):
            raise ValueError(f"Manual execution pass package is not in core package: {package_id}.")
        parts.append(
            f"{package_id} `{_clean(caption['thesis_label'])}`: {_clean(caption['caption_de'])}"
        )
    return " | ".join(parts)


def _required_reviewer_output_de(required_manual_decision: str) -> str:
    return (
        "Manual Source Review Output: Page-/Section-Note, Claim-Support, "
        "Blocked-Wording und Citation-Use dokumentieren. "
        + required_manual_decision
    )


def _manual_execution_instruction_de(
    *,
    thesis_area: str,
    source_id: str,
    evidence_id: str,
    item_type: str,
) -> str:
    return (
        f"{thesis_area}: `{source_id}` fuer `{evidence_id}` ({item_type}) manuell "
        "pruefen. Erst nach Page-/Section-Note, Claim-Support und "
        "Blocked-Wording-Check darf die row fuer finale Zitation vorbereitet "
        "werden. Keine Rohartefakt-Dumps, keine Runtime-Agenten; spaetere "
        "Agentenhilfe nur bounded mit max 50 rows und llm_audit_log."
    )


def _final_citation_gate_de(final_citation_gate: str) -> str:
    if final_citation_gate == "full_source_review_required_before_final_citation":
        return (
            "Keine finale Zitation vor vollstaendigem manuellem Source Review; "
            "keine Quellenstatus-Hochstufung aus diesem Pass."
        )
    return (
        "Citation-Use bleibt blockiert, bis ein separates manuelles "
        f"Gate abgeschlossen ist: {final_citation_gate}."
    )


def _clean(value: object) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required manual source-review execution input missing: {path}")
    return pd.read_csv(path)


def _resolve_under(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "ja"}


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
