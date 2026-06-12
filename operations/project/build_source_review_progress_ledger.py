"""Build a source-review progress ledger that preserves manual review fields."""

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

LEDGER_OUTPUT = "thesis_source_review_progress_ledger.csv"
LEDGER_DOC_OUTPUT = "THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md"

LEDGER_COLUMNS: tuple[str, ...] = (
    "ledger_id",
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
    "review_status",
    "page_or_section_note",
    "claim_support_decision",
    "blocked_wording_check",
    "citation_use_decision",
    "reviewed_by",
    "reviewed_at",
    "review_comment_de",
    "review_progress_state",
    "source_status_change_allowed",
    "final_citation_ready",
    "preserved_manual_fields",
    "do_not_claim_de",
    "next_action_de",
)

MANUAL_COLUMNS: tuple[str, ...] = (
    "review_status",
    "page_or_section_note",
    "claim_support_decision",
    "blocked_wording_check",
    "citation_use_decision",
    "reviewed_by",
    "reviewed_at",
    "review_comment_de",
)

CLAIM_SUPPORT_VALUES: frozenset[str] = frozenset(
    {
        "pending",
        "supports_allowed_wording",
        "supports_with_limitation",
        "does_not_support",
        "needs_more_review",
    }
)
BLOCKED_WORDING_VALUES: frozenset[str] = frozenset(
    {"pending", "passed", "failed", "needs_more_review"}
)
CITATION_USE_VALUES: frozenset[str] = frozenset(
    {
        "blocked_pending_manual_review",
        "approved_for_draft_citation_only",
        "approved_for_final_citation",
        "not_usable_for_claim",
        "needs_more_review",
    }
)
REVIEW_STATUS_VALUES: frozenset[str] = frozenset(
    {
        "pending_manual_review",
        "in_progress",
        "reviewed_manual_note_recorded",
        "reviewed_supports",
        "reviewed_supports_with_limitation",
        "reviewed_not_supported",
        "needs_more_review",
    }
)


@dataclass(frozen=True)
class SourceReviewProgressLedgerResult:
    """Generated source-review progress ledger paths and counts."""

    ledger_path: Path
    docs_path: Path
    ledger_rows: int
    pending_rows: int
    preserved_rows: int
    final_citation_ready_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "ledger_path": str(self.ledger_path),
            "docs_path": str(self.docs_path),
            "ledger_rows": self.ledger_rows,
            "pending_rows": self.pending_rows,
            "preserved_rows": self.preserved_rows,
            "final_citation_ready_rows": self.final_citation_ready_rows,
        }


def generate_source_review_progress_ledger(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> SourceReviewProgressLedgerResult:
    """Generate the progress ledger and Markdown summary."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)
    notes = _read_csv(results_dir / "thesis_h1_h2_h3_source_review_notes.csv")
    existing_path = results_dir / LEDGER_OUTPUT
    existing = pd.read_csv(existing_path) if existing_path.exists() else None

    ledger = build_source_review_progress_ledger(notes=notes, existing_ledger=existing)
    _validate_ledger(ledger)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = results_dir / LEDGER_OUTPUT
    docs_path = docs_dir / LEDGER_DOC_OUTPUT
    ledger.to_csv(ledger_path, index=False)
    docs_path.write_text(_render_ledger_doc(ledger), encoding="utf-8")

    return SourceReviewProgressLedgerResult(
        ledger_path=ledger_path,
        docs_path=docs_path,
        ledger_rows=len(ledger),
        pending_rows=int((ledger["review_progress_state"] == "pending_manual_review").sum()),
        preserved_rows=int(ledger["preserved_manual_fields"].astype(bool).sum()),
        final_citation_ready_rows=int(ledger["final_citation_ready"].astype(bool).sum()),
    )


def build_source_review_progress_ledger(
    *,
    notes: pd.DataFrame,
    existing_ledger: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Return a source-review progress ledger seeded from H1-H2-H3 notes."""

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
            "do_not_claim_de",
        ),
        "H1-H2-H3 source review notes",
    )
    existing_by_note: dict[str, dict[str, object]] = {}
    if existing_ledger is not None and not existing_ledger.empty:
        _require_columns(existing_ledger, ("note_id", *MANUAL_COLUMNS), "existing source review ledger")
        existing_by_note = existing_ledger.set_index("note_id").to_dict(orient="index")

    rows: list[dict[str, object]] = []
    for note in notes.sort_values(["thesis_area", "source_id", "evidence_id"]).to_dict(orient="records"):
        note_id = str(note["note_id"])
        preserved = existing_by_note.get(note_id, {})
        manual = _manual_defaults()
        for column in MANUAL_COLUMNS:
            preserved_value = preserved.get(column)
            if _present(preserved_value):
                manual[column] = str(preserved_value)
        progress_state = _progress_state(manual)
        final_ready = _final_citation_ready(manual)
        rows.append(
            {
                "ledger_id": f"ledger_{note_id.removeprefix('note_')}",
                "note_id": note_id,
                "thesis_area": str(note["thesis_area"]),
                "section_id": str(note["section_id"]),
                "source_id": str(note["source_id"]),
                "evidence_id": str(note["evidence_id"]),
                "item_type": str(note["item_type"]),
                "selected_table": str(note["selected_table"]),
                "selected_figure": str(note["selected_figure"]),
                "deterministic_artifact": str(note["deterministic_artifact"]),
                "access_route": str(note["access_route"]),
                "manual_locator_task_de": str(note["manual_locator_task_de"]),
                **manual,
                "review_progress_state": progress_state,
                "source_status_change_allowed": False,
                "final_citation_ready": final_ready,
                "preserved_manual_fields": bool(preserved),
                "do_not_claim_de": str(note["do_not_claim_de"]),
                "next_action_de": _next_action_de(progress_state, final_ready),
            }
        )
    return pd.DataFrame(rows, columns=LEDGER_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_source_review_progress_ledger(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_ledger(ledger: pd.DataFrame) -> None:
    _require_columns(ledger, LEDGER_COLUMNS, "source review progress ledger")
    if ledger.empty:
        raise ValueError("Source review progress ledger must not be empty.")
    if ledger["ledger_id"].duplicated().any():
        raise ValueError("Source review progress ledger contains duplicate ledger_id values.")
    if ledger["note_id"].duplicated().any():
        raise ValueError("Source review progress ledger contains duplicate note_id values.")
    if not set(ledger["thesis_area"]).issubset({"H1", "H2", "H3"}):
        raise ValueError("Source review progress ledger must only contain H1, H2, and H3 rows.")
    if not set(ledger["review_status"]).issubset(REVIEW_STATUS_VALUES):
        raise ValueError("Source review progress ledger has invalid review_status values.")
    if not set(ledger["claim_support_decision"]).issubset(CLAIM_SUPPORT_VALUES):
        raise ValueError("Source review progress ledger has invalid claim_support_decision values.")
    if not set(ledger["blocked_wording_check"]).issubset(BLOCKED_WORDING_VALUES):
        raise ValueError("Source review progress ledger has invalid blocked_wording_check values.")
    if not set(ledger["citation_use_decision"]).issubset(CITATION_USE_VALUES):
        raise ValueError("Source review progress ledger has invalid citation_use_decision values.")
    if ledger["source_status_change_allowed"].astype(bool).any():
        raise ValueError("Source review progress ledger must not allow source-status changes.")
    final_ready = ledger["final_citation_ready"].astype(bool)
    if (
        ledger.loc[final_ready, "citation_use_decision"] != "approved_for_final_citation"
    ).any():
        raise ValueError("Final citation ready rows must have approved citation-use decisions.")
    if (
        ledger.loc[final_ready, "review_progress_state"]
        != "manual_review_complete_final_citation_ready"
    ).any():
        raise ValueError("Final citation ready rows must have complete progress state.")
    for column in (
        "ledger_id",
        "note_id",
        "source_id",
        "evidence_id",
        "selected_table",
        "selected_figure",
        "deterministic_artifact",
        "manual_locator_task_de",
        "do_not_claim_de",
        "next_action_de",
    ):
        if ledger[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Source review progress ledger contains empty {column}.")
    joined = "\n".join(ledger.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Source review progress ledger must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "keine quellenstatus-hochstufung",
        "keine finale zitation",
        "source review",
        "manual",
        "page-/section-note",
        "claim-support",
        "blocked-wording",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Source review progress ledger missing required terms: " + ", ".join(missing))


def _render_ledger_doc(ledger: pd.DataFrame) -> str:
    progress_counts = ledger["review_progress_state"].value_counts().to_dict()
    area_counts = ledger["thesis_area"].value_counts().to_dict()
    display = ledger[
        [
            "ledger_id",
            "thesis_area",
            "source_id",
            "evidence_id",
            "review_progress_state",
            "claim_support_decision",
            "blocked_wording_check",
            "citation_use_decision",
            "final_citation_ready",
        ]
    ]
    return (
        "# Source Review Progress Ledger\n\n"
        "Dieses Ledger verfolgt den manuellen Fortschritt der H1-H2-H3 "
        "Source Review. Es wird aus den Source Review Notes initialisiert und "
        "bewahrt manuelle Felder beim Regenerieren per `note_id`. Es liest "
        "keine Quelleninhalte, promotet keinen Quellenstatus und ersetzt keine "
        "menschliche Page-/Section-Note.\n\n"
        "## Counts\n\n"
        f"- Ledger rows: {len(ledger)}\n"
        f"- H1 rows: {int(area_counts.get('H1', 0))}\n"
        f"- H2 rows: {int(area_counts.get('H2', 0))}\n"
        f"- H3 rows: {int(area_counts.get('H3', 0))}\n"
        f"- Pending rows: {int(progress_counts.get('pending_manual_review', 0))}\n"
        f"- Incomplete manual rows: {int(progress_counts.get('manual_review_incomplete', 0))}\n"
        f"- Recorded rows pending citation check: {int(progress_counts.get('manual_review_recorded_pending_final_citation_check', 0))}\n"
        f"- Complete final-citation rows: {int(progress_counts.get('manual_review_complete_final_citation_ready', 0))}\n"
        f"- Final citation ready rows: {int(ledger['final_citation_ready'].astype(bool).sum())}\n\n"
        f"- Preserved manual rows: {int(ledger['preserved_manual_fields'].astype(bool).sum())}\n\n"
        "## Ledger Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Manual Update Rule\n\n"
        "Manuelle Reviewer duerfen nur die Review-Felder aktualisieren: "
        "`review_status`, `page_or_section_note`, `claim_support_decision`, "
        "`blocked_wording_check`, `citation_use_decision`, `reviewed_by`, "
        "`reviewed_at`, und `review_comment_de`. Keine Quellenstatus-"
        "Hochstufung, keine finale Zitation und keine neuen thesis-facing "
        "Claims ohne abgeschlossene Source Review. Runtime-Agenten, MCP, Model "
        "Routing und LLM-Metriken bleiben deaktiviert.\n"
    )


def _manual_defaults() -> dict[str, str]:
    return {
        "review_status": "pending_manual_review",
        "page_or_section_note": "",
        "claim_support_decision": "pending",
        "blocked_wording_check": "pending",
        "citation_use_decision": "blocked_pending_manual_review",
        "reviewed_by": "",
        "reviewed_at": "",
        "review_comment_de": "",
    }


def _progress_state(manual: dict[str, str]) -> str:
    page_note = manual["page_or_section_note"].strip()
    claim = manual["claim_support_decision"]
    blocked = manual["blocked_wording_check"]
    status = manual["review_status"]
    citation_use = manual["citation_use_decision"]
    if claim == "does_not_support" or status == "reviewed_not_supported" or citation_use == "not_usable_for_claim":
        return "manual_review_rejected_or_not_supported"
    if (
        claim == "needs_more_review"
        or blocked == "needs_more_review"
        or status == "needs_more_review"
        or citation_use == "needs_more_review"
    ):
        return "manual_review_needs_more_review"
    if (
        page_note
        and claim in {"supports_allowed_wording", "supports_with_limitation"}
        and blocked == "passed"
        and citation_use == "approved_for_final_citation"
    ):
        return "manual_review_complete_final_citation_ready"
    if page_note and claim in {"supports_allowed_wording", "supports_with_limitation"} and blocked == "passed":
        return "manual_review_recorded_pending_final_citation_check"
    if any(manual[column] != default for column, default in _manual_defaults().items()):
        return "manual_review_incomplete"
    return "pending_manual_review"


def _final_citation_ready(manual: dict[str, str]) -> bool:
    return (
        bool(manual["page_or_section_note"].strip())
        and manual["claim_support_decision"] in {"supports_allowed_wording", "supports_with_limitation"}
        and manual["blocked_wording_check"] == "passed"
        and manual["citation_use_decision"] == "approved_for_final_citation"
    )


def _next_action_de(progress_state: str, final_ready: bool) -> str:
    if final_ready:
        return "Finale Zitation separat formatieren; Quellenstatus nicht automatisch hochstufen."
    if progress_state == "manual_review_recorded_pending_final_citation_check":
        return "Citation-Use-Entscheid und finalen Zitationsformat-Check manuell abschliessen."
    if progress_state == "manual_review_rejected_or_not_supported":
        return "Claim nicht mit dieser Quelle stuetzen; Ersatzquelle oder Formulierungsgrenze pruefen."
    if progress_state == "manual_review_needs_more_review":
        return "Weitere Source Review manuell planen und offene Locator- oder Claim-Frage klaeren."
    if progress_state == "manual_review_incomplete":
        return "Unvollstaendige Review-Felder ergaenzen: Page-/Section-Note, Claim-Support und Blocked-Wording."
    return "Source Review manuell starten: Page-/Section-Note, Claim-Support und Blocked-Wording erfassen."


def _present(value: object) -> bool:
    if value is None:
        return False
    if pd.isna(value):
        return False
    return str(value).strip() != ""


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required source review progress ledger input missing: {path}")
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
