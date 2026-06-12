"""Build a focused H2 manual source-review follow-up worksheet."""

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

H2_FOLLOWUP_OUTPUT = "thesis_h2_manual_source_review_followup.csv"
H2_FOLLOWUP_DOC_OUTPUT = "THESIS_H2_MANUAL_SOURCE_REVIEW_FOLLOWUP.md"

H2_FOLLOWUP_COLUMNS: tuple[str, ...] = (
    "h2_followup_id",
    "review_order",
    "source_id",
    "source_title",
    "source_status",
    "source_priority_order",
    "evidence_id",
    "item_type",
    "deterministic_artifact",
    "selected_table",
    "selected_figure",
    "access_route",
    "review_source_locator",
    "manual_locator_task_de",
    "current_review_status",
    "page_or_section_note_status",
    "claim_support_decision",
    "blocked_wording_check",
    "citation_use_decision",
    "final_citation_ready",
    "source_status_change_allowed",
    "required_manual_fields_de",
    "allowed_claim_scope_de",
    "blocked_wording_check_de",
    "next_action_de",
    "guardrail_de",
)


@dataclass(frozen=True)
class H2ManualSourceReviewFollowupResult:
    """Generated H2 manual source-review follow-up paths and counts."""

    followup_path: Path
    docs_path: Path
    followup_rows: int
    unique_source_rows: int
    pending_rows: int
    final_ready_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "followup_path": str(self.followup_path),
            "docs_path": str(self.docs_path),
            "followup_rows": self.followup_rows,
            "unique_source_rows": self.unique_source_rows,
            "pending_rows": self.pending_rows,
            "final_ready_rows": self.final_ready_rows,
        }


def generate_h2_manual_source_review_followup(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> H2ManualSourceReviewFollowupResult:
    """Generate the H2 manual source-review follow-up CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    execution = _read_csv(results_dir / "thesis_h1_h2_h3_manual_source_review_execution_pass.csv")
    ledger = _read_csv(results_dir / "thesis_source_review_progress_ledger.csv")

    followup = build_h2_manual_source_review_followup(execution=execution, ledger=ledger)
    _validate_followup(followup, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    followup_path = results_dir / H2_FOLLOWUP_OUTPUT
    docs_path = docs_dir / H2_FOLLOWUP_DOC_OUTPUT
    followup.to_csv(followup_path, index=False)
    docs_path.write_text(_render_followup_doc(followup), encoding="utf-8")

    return H2ManualSourceReviewFollowupResult(
        followup_path=followup_path,
        docs_path=docs_path,
        followup_rows=len(followup),
        unique_source_rows=int(followup["source_id"].nunique()),
        pending_rows=int((followup["current_review_status"] == "pending_manual_review").sum()),
        final_ready_rows=int(followup["final_citation_ready"].map(_bool_value).sum()),
    )


def build_h2_manual_source_review_followup(
    *,
    execution: pd.DataFrame,
    ledger: pd.DataFrame,
) -> pd.DataFrame:
    """Return the H2-only manual source-review starter list."""

    _require_columns(
        execution,
        (
            "execution_order",
            "thesis_area",
            "source_id",
            "source_title",
            "source_status",
            "source_priority_order",
            "evidence_id",
            "item_type",
            "ledger_id",
            "deterministic_artifact",
            "selected_table",
            "selected_figure",
            "access_route",
            "review_source_locator",
            "manual_locator_task_de",
            "current_review_status",
            "current_claim_support_decision",
            "current_blocked_wording_check",
            "current_citation_use_decision",
            "final_citation_ready",
            "source_status_change_allowed",
            "bounded_claim_check_de",
            "blocked_wording_check_de",
            "next_action_de",
        ),
        "manual source-review execution pass",
    )
    _require_columns(
        ledger,
        (
            "ledger_id",
            "page_or_section_note",
            "claim_support_decision",
            "blocked_wording_check",
            "citation_use_decision",
        ),
        "source review progress ledger",
    )

    ledger_by_id = ledger.set_index("ledger_id").to_dict(orient="index")
    h2_rows = execution[execution["thesis_area"] == "H2"].sort_values("execution_order")
    rows: list[dict[str, object]] = []
    for review_order, row in enumerate(h2_rows.to_dict(orient="records"), start=1):
        ledger_id = str(row["ledger_id"])
        ledger_row = ledger_by_id.get(ledger_id)
        if ledger_row is None:
            raise ValueError(f"H2 follow-up missing ledger row for {ledger_id}.")
        page_note = _clean(ledger_row.get("page_or_section_note", ""))
        rows.append(
            {
                "h2_followup_id": f"h2_followup_{review_order:02d}_{row['source_id']}__{row['evidence_id']}",
                "review_order": review_order,
                "source_id": _clean(row["source_id"]),
                "source_title": _clean(row["source_title"]),
                "source_status": _clean(row["source_status"]),
                "source_priority_order": int(row["source_priority_order"]),
                "evidence_id": _clean(row["evidence_id"]),
                "item_type": _clean(row["item_type"]),
                "deterministic_artifact": _clean(row["deterministic_artifact"]),
                "selected_table": _clean(row["selected_table"]),
                "selected_figure": _clean(row["selected_figure"]),
                "access_route": _clean(row["access_route"]),
                "review_source_locator": _clean(row["review_source_locator"]),
                "manual_locator_task_de": _clean(row["manual_locator_task_de"]),
                "current_review_status": _clean(row["current_review_status"]),
                "page_or_section_note_status": (
                    "recorded_manual_page_or_section_note"
                    if page_note
                    else "pending_page_or_section_note"
                ),
                "claim_support_decision": _clean(ledger_row["claim_support_decision"])
                or _clean(row["current_claim_support_decision"]),
                "blocked_wording_check": _clean(ledger_row["blocked_wording_check"])
                or _clean(row["current_blocked_wording_check"]),
                "citation_use_decision": _clean(ledger_row["citation_use_decision"])
                or _clean(row["current_citation_use_decision"]),
                "final_citation_ready": _bool_value(row["final_citation_ready"]),
                "source_status_change_allowed": _bool_value(row["source_status_change_allowed"]),
                "required_manual_fields_de": (
                    "Reviewer muss Page-/Section-Note, Claim-Support, "
                    "Blocked-Wording und Citation-Use manuell erfassen."
                ),
                "allowed_claim_scope_de": _clean(row["bounded_claim_check_de"]),
                "blocked_wording_check_de": _clean(row["blocked_wording_check_de"]),
                "next_action_de": _clean(row["next_action_de"]),
                "guardrail_de": (
                    "H2 bleibt bounded: Event-Window nur deskriptiv, keine "
                    "Kausalclaims, keine Quellenstatus-Hochstufung, keine "
                    "finale Zitation, keine Rohartefakt-Dumps, keine "
                    "Runtime-Agenten; spaetere Agentenhilfe nur mit separatem "
                    "Goal, max 50 rows, Tests und llm_audit_log."
                ),
            }
        )
    return pd.DataFrame(rows, columns=H2_FOLLOWUP_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_h2_manual_source_review_followup(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_followup(followup: pd.DataFrame, *, repo_root: Path) -> None:
    _require_columns(followup, H2_FOLLOWUP_COLUMNS, "H2 manual source-review follow-up")
    if len(followup) != 5:
        raise ValueError("H2 manual source-review follow-up must contain exactly 5 rows.")
    if followup["h2_followup_id"].duplicated().any():
        raise ValueError("H2 manual source-review follow-up contains duplicate IDs.")
    if followup["review_order"].astype(int).tolist() != list(range(1, 6)):
        raise ValueError("H2 manual source-review follow-up must be ordered 1..5.")
    if followup["source_status_change_allowed"].map(_bool_value).any():
        raise ValueError("H2 manual source-review follow-up must not allow source-status changes.")
    for column in H2_FOLLOWUP_COLUMNS:
        if followup[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"H2 manual source-review follow-up contains empty {column}.")
    for artifact in followup["deterministic_artifact"].astype(str):
        if not (repo_root / artifact).exists():
            raise FileNotFoundError(f"H2 deterministic artifact missing: {artifact}")
    joined = "\n".join(followup.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("H2 manual source-review follow-up must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "h2",
        "page-/section-note",
        "claim-support",
        "blocked-wording",
        "citation-use",
        "pending_page_or_section_note",
        "keine kausalclaims",
        "keine quellenstatus-hochstufung",
        "keine finale zitation",
        "keine rohartefakt-dumps",
        "keine runtime-agenten",
        "llm_audit_log",
        "max 50 rows",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("H2 manual source-review follow-up missing required terms: " + ", ".join(missing))


def _render_followup_doc(followup: pd.DataFrame) -> str:
    item_counts = followup["item_type"].value_counts().to_dict()
    access_counts = followup["access_route"].value_counts().to_dict()
    final_ready_rows = int(followup["final_citation_ready"].map(_bool_value).sum())
    display = followup[
        [
            "review_order",
            "source_id",
            "evidence_id",
            "item_type",
            "access_route",
            "page_or_section_note_status",
            "claim_support_decision",
            "citation_use_decision",
            "next_action_de",
        ]
    ]
    return (
        "# H2 Manual Source Review Follow-up\n\n"
        "Dieses Artefakt startet den H2-Teil der manuellen Source Review. Es "
        "filtert die bestehende H1-H2-H3 Execution-Liste auf H2, verbindet sie "
        "mit dem Progress Ledger und zeigt die manuell auszufuellenden Gates. "
        "Es liest keine Quelleninhalte, trifft keinen Claim-Support-Entscheid "
        "und promotet keinen Quellenstatus. H2 bleibt als Event-Window-Befund "
        "deskriptiv und darf nicht kausal formuliert werden.\n\n"
        "## Counts\n\n"
        f"- H2 follow-up rows: {len(followup)}\n"
        f"- Unique H2 sources: {int(followup['source_id'].nunique())}\n"
        f"- Method rows: {int(item_counts.get('method', 0))}\n"
        f"- Interpretation rows: {int(item_counts.get('interpretation', 0))}\n"
        f"- External locator rows: {int(access_counts.get('external_locator_review', 0))}\n"
        f"- Local PDF rows: {int(access_counts.get('local_pdf_review', 0))}\n"
        f"- Final citation ready rows: {final_ready_rows}\n\n"
        "## Review Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Arbeite H2 manuell in dieser Reihenfolge ab. Fuer jede Zeile: Quelle "
        "oeffnen, Page-/Section-Note erfassen, Claim-Support entscheiden, "
        "Blocked-Wording pruefen und Citation-Use setzen. Bis diese Felder "
        "belegt sind, bleiben H2-Zitationen final blockiert. Keine "
        "Kausalclaims, keine Quellenstatus-Hochstufung, keine finale Zitation, "
        "keine Rohartefakt-Dumps, keine Runtime-Agenten, kein MCP, kein Model "
        "Routing, keine LLM-Metriken und keine Trading-Pfade.\n"
    )


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "ja"}


def _clean(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required H2 manual source-review follow-up input missing: {path}")
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
