"""Build a compact citation-gate summary from the source-review progress ledger."""

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

SUMMARY_OUTPUT = "thesis_ledger_citation_gate_summary.csv"
SUMMARY_DOC_OUTPUT = "THESIS_LEDGER_CITATION_GATE_SUMMARY.md"

SUMMARY_COLUMNS: tuple[str, ...] = (
    "gate_id",
    "scope_id",
    "ledger_rows",
    "unique_sources",
    "method_rows",
    "interpretation_rows",
    "deterministic_artifact_rows",
    "pending_manual_review_rows",
    "manual_review_incomplete_rows",
    "recorded_pending_citation_check_rows",
    "final_citation_ready_rows",
    "blocked_pending_citation_rows",
    "draft_citation_only_rows",
    "not_usable_for_claim_rows",
    "needs_more_review_rows",
    "source_status_change_rows",
    "page_note_missing_rows",
    "claim_support_pending_rows",
    "blocked_wording_pending_rows",
    "citation_use_pending_rows",
    "selected_tables",
    "selected_figures",
    "citation_gate_status",
    "draft_use_rule_de",
    "final_use_rule_de",
    "next_action_de",
)

LEDGER_REQUIRED_COLUMNS: tuple[str, ...] = (
    "thesis_area",
    "source_id",
    "evidence_id",
    "item_type",
    "selected_table",
    "selected_figure",
    "deterministic_artifact",
    "review_progress_state",
    "page_or_section_note",
    "claim_support_decision",
    "blocked_wording_check",
    "citation_use_decision",
    "source_status_change_allowed",
    "final_citation_ready",
)

ALIGNMENT_REQUIRED_COLUMNS: tuple[str, ...] = (
    "slice_id",
    "decision_queue_rows",
    "ledger_rows",
    "matched_rows",
    "queue_missing_ledger_rows",
    "ledger_missing_queue_rows",
    "field_mismatch_rows",
)

SCOPE_ORDER: tuple[str, ...] = ("H1", "H2", "H3", "TOTAL")


@dataclass(frozen=True)
class LedgerCitationGateSummaryResult:
    """Generated citation-gate summary paths and counts."""

    summary_path: Path
    docs_path: Path
    summary_rows: int
    ledger_rows: int
    final_citation_ready_rows: int
    blocked_pending_citation_rows: int
    source_status_change_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "summary_path": str(self.summary_path),
            "docs_path": str(self.docs_path),
            "summary_rows": self.summary_rows,
            "ledger_rows": self.ledger_rows,
            "final_citation_ready_rows": self.final_citation_ready_rows,
            "blocked_pending_citation_rows": self.blocked_pending_citation_rows,
            "source_status_change_rows": self.source_status_change_rows,
        }


def generate_ledger_citation_gate_summary(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> LedgerCitationGateSummaryResult:
    """Generate the ledger citation-gate summary CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    ledger = _read_csv(results_dir / "thesis_source_review_progress_ledger.csv")
    alignment = _read_csv(results_dir / "thesis_h1_h2_h3_decision_queue_ledger_alignment.csv")
    summary = build_ledger_citation_gate_summary(ledger=ledger, alignment=alignment)
    _validate_summary(summary=summary, ledger=ledger, alignment=alignment, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    summary_path = results_dir / SUMMARY_OUTPUT
    docs_path = docs_dir / SUMMARY_DOC_OUTPUT
    summary.to_csv(summary_path, index=False)
    docs_path.write_text(_render_summary_doc(summary), encoding="utf-8")

    total = summary.loc[summary["scope_id"] == "TOTAL"].iloc[0]
    return LedgerCitationGateSummaryResult(
        summary_path=summary_path,
        docs_path=docs_path,
        summary_rows=len(summary),
        ledger_rows=int(total["ledger_rows"]),
        final_citation_ready_rows=int(total["final_citation_ready_rows"]),
        blocked_pending_citation_rows=int(total["blocked_pending_citation_rows"]),
        source_status_change_rows=int(total["source_status_change_rows"]),
    )


def build_ledger_citation_gate_summary(
    *,
    ledger: pd.DataFrame,
    alignment: pd.DataFrame,
) -> pd.DataFrame:
    """Return H1/H2/H3/TOTAL citation-gate rows from the ledger."""

    _require_columns(ledger, LEDGER_REQUIRED_COLUMNS, "source review progress ledger")
    _require_columns(alignment, ALIGNMENT_REQUIRED_COLUMNS, "decision queue ledger alignment")
    _validate_alignment_input(alignment)

    rows = [
        _scope_row(scope_id=scope_id, frame=ledger[ledger["thesis_area"] == scope_id])
        for scope_id in ("H1", "H2", "H3")
    ]
    rows.append(_scope_row(scope_id="TOTAL", frame=ledger))
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_ledger_citation_gate_summary(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _scope_row(*, scope_id: str, frame: pd.DataFrame) -> dict[str, object]:
    ledger_rows = len(frame)
    final_ready_rows = int(frame["final_citation_ready"].map(_bool_value).sum())
    source_status_change_rows = int(frame["source_status_change_allowed"].map(_bool_value).sum())
    blocked_pending = int((frame["citation_use_decision"] == "blocked_pending_manual_review").sum())
    missing_page_notes = int(frame["page_or_section_note"].fillna("").astype(str).str.strip().eq("").sum())
    claim_pending = int((frame["claim_support_decision"] == "pending").sum())
    blocked_wording_pending = int((frame["blocked_wording_check"] == "pending").sum())
    citation_pending = int((frame["citation_use_decision"] == "blocked_pending_manual_review").sum())
    status = _citation_gate_status(
        ledger_rows=ledger_rows,
        final_ready_rows=final_ready_rows,
        source_status_change_rows=source_status_change_rows,
        blocked_pending_rows=blocked_pending,
    )
    return {
        "gate_id": f"citation_gate_{scope_id.lower()}",
        "scope_id": scope_id,
        "ledger_rows": ledger_rows,
        "unique_sources": int(frame["source_id"].nunique()),
        "method_rows": int((frame["item_type"] == "method").sum()),
        "interpretation_rows": int((frame["item_type"] == "interpretation").sum()),
        "deterministic_artifact_rows": int(frame["deterministic_artifact"].fillna("").astype(str).str.len().gt(0).sum()),
        "pending_manual_review_rows": int((frame["review_progress_state"] == "pending_manual_review").sum()),
        "manual_review_incomplete_rows": int((frame["review_progress_state"] == "manual_review_incomplete").sum()),
        "recorded_pending_citation_check_rows": int(
            (frame["review_progress_state"] == "manual_review_recorded_pending_final_citation_check").sum()
        ),
        "final_citation_ready_rows": final_ready_rows,
        "blocked_pending_citation_rows": blocked_pending,
        "draft_citation_only_rows": int((frame["citation_use_decision"] == "approved_for_draft_citation_only").sum()),
        "not_usable_for_claim_rows": int((frame["citation_use_decision"] == "not_usable_for_claim").sum()),
        "needs_more_review_rows": int(
            (
                (frame["review_progress_state"] == "manual_review_needs_more_review")
                | (frame["citation_use_decision"] == "needs_more_review")
                | (frame["claim_support_decision"] == "needs_more_review")
                | (frame["blocked_wording_check"] == "needs_more_review")
            ).sum()
        ),
        "source_status_change_rows": source_status_change_rows,
        "page_note_missing_rows": missing_page_notes,
        "claim_support_pending_rows": claim_pending,
        "blocked_wording_pending_rows": blocked_wording_pending,
        "citation_use_pending_rows": citation_pending,
        "selected_tables": _join_unique(frame["selected_table"]),
        "selected_figures": _join_unique(frame["selected_figure"]),
        "citation_gate_status": status,
        "draft_use_rule_de": _draft_use_rule(scope_id=scope_id),
        "final_use_rule_de": _final_use_rule(status=status),
        "next_action_de": _next_action(scope_id=scope_id, status=status),
    }


def _validate_summary(
    *,
    summary: pd.DataFrame,
    ledger: pd.DataFrame,
    alignment: pd.DataFrame,
    repo_root: Path,
) -> None:
    _require_columns(summary, SUMMARY_COLUMNS, "ledger citation gate summary")
    if summary["scope_id"].tolist() != list(SCOPE_ORDER):
        raise ValueError("Ledger citation gate summary must be ordered H1, H2, H3, TOTAL.")
    if len(ledger) != 23:
        raise ValueError("Ledger citation gate summary expects 23 ledger rows.")
    total = summary.loc[summary["scope_id"] == "TOTAL"].iloc[0]
    if int(total["ledger_rows"]) != len(ledger):
        raise ValueError("TOTAL citation gate row must match ledger row count.")
    if int(total["unique_sources"]) != 9:
        raise ValueError("TOTAL citation gate row must cover 9 unique sources.")
    if int(total["method_rows"]) != 12 or int(total["interpretation_rows"]) != 11:
        raise ValueError("TOTAL citation gate row must cover 12 method and 11 interpretation rows.")
    if int(total["deterministic_artifact_rows"]) != 23:
        raise ValueError("Every ledger row must retain a deterministic artifact.")
    if int(total["final_citation_ready_rows"]) != 0:
        raise ValueError("Current ledger citation gate must keep final-ready rows at 0.")
    if int(total["source_status_change_rows"]) != 0:
        raise ValueError("Current ledger citation gate must not allow source-status changes.")
    if int(total["blocked_pending_citation_rows"]) != 23:
        raise ValueError("All current ledger rows must remain blocked pending manual review.")
    if int(total["page_note_missing_rows"]) != 23:
        raise ValueError("All current ledger rows must still miss manual Page-/Section-Notes.")
    if int(total["claim_support_pending_rows"]) != 23:
        raise ValueError("All current ledger rows must still have pending Claim-Support decisions.")
    if int(total["blocked_wording_pending_rows"]) != 23:
        raise ValueError("All current ledger rows must still have pending Blocked-Wording checks.")
    if int(total["citation_use_pending_rows"]) != 23:
        raise ValueError("All current ledger rows must still have blocked pending Citation-Use decisions.")
    if set(summary["citation_gate_status"]) != {"final_blocked_pending_manual_source_review"}:
        raise ValueError("All citation gate rows must remain final-blocked pending manual review.")
    expected_counts = {"H1": 10, "H2": 5, "H3": 8}
    for scope_id, expected in expected_counts.items():
        row = summary.loc[summary["scope_id"] == scope_id].iloc[0]
        if int(row["ledger_rows"]) != expected:
            raise ValueError(f"{scope_id} citation gate row count drifted.")
    _validate_alignment_input(alignment)
    _required_file(repo_root / "docs/project/THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md")
    _required_file(repo_root / "docs/project/THESIS_H1_H2_H3_DECISION_QUEUE_LEDGER_ALIGNMENT.md")

    joined = "\n".join([_join_frame_rows(summary), _join_frame_rows(ledger)])
    if chr(223) in joined:
        raise ValueError("Ledger citation gate summary must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "page-/section-note",
        "claim-support",
        "blocked-wording",
        "citation-use",
        "keine finale zitation",
        "keine quellenstatus-hochstufung",
        "keine runtime-agenten",
        "llm_audit_log",
        "max 50 rows",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Ledger citation gate summary missing required terms: " + ", ".join(missing))


def _validate_alignment_input(alignment: pd.DataFrame) -> None:
    if int(alignment["matched_rows"].sum()) != int(alignment["ledger_rows"].sum()):
        raise ValueError("Decision queue ledger alignment must have all ledger rows matched.")
    if int(alignment["queue_missing_ledger_rows"].sum()) != 0:
        raise ValueError("Decision queue ledger alignment has queue rows missing ledger.")
    if int(alignment["ledger_missing_queue_rows"].sum()) != 0:
        raise ValueError("Decision queue ledger alignment has ledger rows missing queue.")
    if int(alignment["field_mismatch_rows"].sum()) != 0:
        raise ValueError("Decision queue ledger alignment has field mismatches.")


def _render_summary_doc(summary: pd.DataFrame) -> str:
    total = summary.loc[summary["scope_id"] == "TOTAL"].iloc[0]
    display = summary[
        [
            "scope_id",
            "ledger_rows",
            "unique_sources",
            "method_rows",
            "interpretation_rows",
            "blocked_pending_citation_rows",
            "page_note_missing_rows",
            "final_citation_ready_rows",
            "citation_gate_status",
            "next_action_de",
        ]
    ]
    return (
        "# Ledger Citation Gate Summary\n\n"
        "Diese Uebersicht verdichtet das Source Review Progress Ledger zu "
        "einem kleinen Citation-Gate-Artefakt fuer H1, H2, H3 und TOTAL. Sie "
        "liest keine Quelleninhalte, trifft keine Claim-Support-Entscheide, "
        "setzt keine Page-/Section-Notes, promotet keinen Quellenstatus und "
        "macht keine finale Zitation.\n\n"
        "## Counts\n\n"
        f"- Summary rows: {len(summary)}\n"
        f"- Ledger rows: {int(total['ledger_rows'])}\n"
        f"- Unique sources: {int(total['unique_sources'])}\n"
        f"- Method rows: {int(total['method_rows'])}\n"
        f"- Interpretation rows: {int(total['interpretation_rows'])}\n"
        f"- Deterministic artifact rows: {int(total['deterministic_artifact_rows'])}\n"
        f"- Blocked pending citation rows: {int(total['blocked_pending_citation_rows'])}\n"
        f"- Page-note missing rows: {int(total['page_note_missing_rows'])}\n"
        f"- Claim-support pending rows: {int(total['claim_support_pending_rows'])}\n"
        f"- Blocked-wording pending rows: {int(total['blocked_wording_pending_rows'])}\n"
        f"- Citation-use pending rows: {int(total['citation_use_pending_rows'])}\n"
        f"- Final citation ready rows: {int(total['final_citation_ready_rows'])}\n"
        f"- Source-status change rows: {int(total['source_status_change_rows'])}\n\n"
        "## Citation Gate Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze diese Summary als letzte kompakte Kontrolle vor jeder "
        "Zitationsfreigabe im H1-H2-H3-Kern. Solange Page-/Section-Note, "
        "Claim-Support, Blocked-Wording und Citation-Use pending sind, bleiben "
        "alle 23 Ledger-Zeilen final blockiert: keine finale Zitation, keine "
        "Quellenstatus-Hochstufung, keine Runtime-Agenten, kein MCP, kein "
        "Model Routing, keine Kennzahlen aus LLMs, max 50 rows fuer spaetere "
        "Agentenhilfe und `llm_audit_log` vor jeder spaeteren LLM-Nutzung.\n"
    )


def _citation_gate_status(
    *,
    ledger_rows: int,
    final_ready_rows: int,
    source_status_change_rows: int,
    blocked_pending_rows: int,
) -> str:
    if source_status_change_rows:
        return "blocked_source_status_change_detected"
    if final_ready_rows == ledger_rows and ledger_rows > 0:
        return "final_citation_ready_after_manual_review"
    if blocked_pending_rows:
        return "final_blocked_pending_manual_source_review"
    return "citation_gate_needs_manual_review"


def _draft_use_rule(*, scope_id: str) -> str:
    return (
        f"{scope_id}: Draft-Nutzung ist nur mit sichtbarem Pending-Gate erlaubt; "
        "keine finale Zitation und keine Quellenstatus-Hochstufung. Spaetere "
        "Agentenhilfe nur mit max 50 rows und llm_audit_log."
    )


def _final_use_rule(*, status: str) -> str:
    if status == "final_citation_ready_after_manual_review":
        return "Finale Zitation separat formatieren und finalen Citation-Style pruefen."
    return (
        "Finale Zitation bleibt blockiert, bis Page-/Section-Note, "
        "Claim-Support, Blocked-Wording und Citation-Use manuell abgeschlossen sind."
    )


def _next_action(*, scope_id: str, status: str) -> str:
    if status == "final_citation_ready_after_manual_review":
        return f"{scope_id}: finalen Zitationsstil pruefen; Quellenstatus nicht automatisch hochstufen."
    return (
        f"{scope_id}: manuelle Source Review starten oder fortsetzen; "
        "Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use erfassen. "
        "Keine Runtime-Agenten."
    )


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required ledger citation gate summary input missing: {path}")
    return pd.read_csv(path)


def _required_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Required ledger citation gate summary artifact missing: {path}")


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "ja", "y"}


def _join_unique(values: pd.Series) -> str:
    unique_values = [str(value).strip() for value in values.dropna().unique() if str(value).strip()]
    return ", ".join(unique_values)


def _join_frame_rows(frame: pd.DataFrame) -> str:
    return "\n".join(
        " ".join(str(value) for value in row)
        for row in frame.fillna("").to_numpy(dtype=object)
    )


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
