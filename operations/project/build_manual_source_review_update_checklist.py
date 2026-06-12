"""Build a manual update checklist for H1-H2-H3 source-review ledger fields."""

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

CHECKLIST_OUTPUT = "thesis_manual_source_review_update_checklist.csv"
CHECKLIST_DOC_OUTPUT = "THESIS_MANUAL_SOURCE_REVIEW_UPDATE_CHECKLIST.md"

CHECKLIST_COLUMNS: tuple[str, ...] = (
    "check_id",
    "check_order",
    "update_phase",
    "source_artifacts",
    "ledger_rows_in_scope",
    "unique_sources_in_scope",
    "external_locator_rows",
    "local_pdf_rows",
    "pending_citation_rows",
    "final_ready_rows",
    "manual_field_targets",
    "allowed_values_or_format_de",
    "required_evidence_de",
    "completion_test_de",
    "blocked_actions_de",
    "next_action_de",
    "ready_for_manual_update",
    "ready_for_final_citation_release",
)

LEDGER_REQUIRED_COLUMNS: tuple[str, ...] = (
    "ledger_id",
    "note_id",
    "thesis_area",
    "source_id",
    "evidence_id",
    "item_type",
    "access_route",
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
)

CITATION_GATE_REQUIRED_COLUMNS: tuple[str, ...] = (
    "scope_id",
    "ledger_rows",
    "blocked_pending_citation_rows",
    "page_note_missing_rows",
    "claim_support_pending_rows",
    "blocked_wording_pending_rows",
    "citation_use_pending_rows",
    "final_citation_ready_rows",
    "source_status_change_rows",
    "citation_gate_status",
)

ALIGNMENT_REQUIRED_COLUMNS: tuple[str, ...] = (
    "slice_id",
    "ledger_rows",
    "matched_rows",
    "queue_missing_ledger_rows",
    "ledger_missing_queue_rows",
    "field_mismatch_rows",
)


@dataclass(frozen=True)
class ManualSourceReviewUpdateChecklistResult:
    """Generated manual update checklist paths and counts."""

    checklist_path: Path
    docs_path: Path
    checklist_rows: int
    ledger_rows: int
    pending_citation_rows: int
    final_ready_rows: int
    final_release_ready_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "checklist_path": str(self.checklist_path),
            "docs_path": str(self.docs_path),
            "checklist_rows": self.checklist_rows,
            "ledger_rows": self.ledger_rows,
            "pending_citation_rows": self.pending_citation_rows,
            "final_ready_rows": self.final_ready_rows,
            "final_release_ready_rows": self.final_release_ready_rows,
        }


def generate_manual_source_review_update_checklist(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> ManualSourceReviewUpdateChecklistResult:
    """Generate the manual source-review update checklist CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    ledger = _read_csv(results_dir / "thesis_source_review_progress_ledger.csv")
    citation_gate = _read_csv(results_dir / "thesis_ledger_citation_gate_summary.csv")
    alignment = _read_csv(results_dir / "thesis_h1_h2_h3_decision_queue_ledger_alignment.csv")
    checklist = build_manual_source_review_update_checklist(
        ledger=ledger,
        citation_gate=citation_gate,
        alignment=alignment,
    )
    _validate_checklist(
        checklist=checklist,
        ledger=ledger,
        citation_gate=citation_gate,
        alignment=alignment,
        repo_root=repo_root,
    )

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    checklist_path = results_dir / CHECKLIST_OUTPUT
    docs_path = docs_dir / CHECKLIST_DOC_OUTPUT
    checklist.to_csv(checklist_path, index=False)
    docs_path.write_text(_render_checklist_doc(checklist), encoding="utf-8")

    total = _total_gate(citation_gate)
    return ManualSourceReviewUpdateChecklistResult(
        checklist_path=checklist_path,
        docs_path=docs_path,
        checklist_rows=len(checklist),
        ledger_rows=int(total["ledger_rows"]),
        pending_citation_rows=int(total["blocked_pending_citation_rows"]),
        final_ready_rows=int(total["final_citation_ready_rows"]),
        final_release_ready_rows=int(checklist["ready_for_final_citation_release"].map(_bool_value).sum()),
    )


def build_manual_source_review_update_checklist(
    *,
    ledger: pd.DataFrame,
    citation_gate: pd.DataFrame,
    alignment: pd.DataFrame,
) -> pd.DataFrame:
    """Return the manual update checklist from current ledger gate state."""

    _require_columns(ledger, LEDGER_REQUIRED_COLUMNS, "source review progress ledger")
    _require_columns(citation_gate, CITATION_GATE_REQUIRED_COLUMNS, "ledger citation gate summary")
    _require_columns(alignment, ALIGNMENT_REQUIRED_COLUMNS, "decision queue ledger alignment")
    _validate_alignment_input(alignment)

    totals = _summary_counts(ledger=ledger, citation_gate=citation_gate)
    rows = [
        _check_row(
            check_order=1,
            update_phase="preflight_alignment_and_gate_check",
            source_artifacts=(
                "data/results/thesis_h1_h2_h3_decision_queue_ledger_alignment.csv; "
                "data/results/thesis_ledger_citation_gate_summary.csv"
            ),
            totals=totals,
            manual_field_targets="none",
            allowed_values_or_format_de=(
                "Nur pruefen: 23 Matches, 0 Missing Rows, 0 Feldabweichungen, "
                "23 citation-blocked rows, 0 final-ready rows."
            ),
            required_evidence_de=(
                "Alignment und Citation-Gate Summary muessen vor jeder manuellen "
                "Ledger-Aenderung konsistent sein."
            ),
            completion_test_de=(
                "`matched_rows=23`, `field_mismatch_rows=0`, "
                "`blocked_pending_citation_rows=23`, `final_citation_ready_rows=0`."
            ),
            blocked_actions_de="Keine Ledger-Aenderung, wenn Alignment oder Gate counts driften.",
            next_action_de="Mit Source Access und Page-/Section-Note-Erfassung beginnen.",
        ),
        _check_row(
            check_order=2,
            update_phase="source_access_and_locator_review",
            source_artifacts=(
                "data/results/thesis_source_review_progress_ledger.csv; "
                "docs/project/THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md"
            ),
            totals=totals,
            manual_field_targets="page_or_section_note",
            allowed_values_or_format_de=(
                "Freitext mit Seite, Abschnitt, DOI/URL-Locator oder klarer "
                "Nichtauffindbarkeitsnotiz; keine erfundenen Seitenzahlen."
            ),
            required_evidence_de=(
                "Quelle manuell oeffnen; relevante Seite oder Abschnitt fuer "
                "Evidence ID und Claim-Grenze notieren."
            ),
            completion_test_de="`page_or_section_note` ist nicht leer und bezieht sich auf die konkrete Evidence ID.",
            blocked_actions_de="Keine automatische Page Note und keine Quelleninhaltsinterpretation durch Skript.",
            next_action_de="Nach Page-/Section-Note Claim-Support entscheiden.",
        ),
        _check_row(
            check_order=3,
            update_phase="claim_support_decision",
            source_artifacts="data/results/thesis_source_review_progress_ledger.csv",
            totals=totals,
            manual_field_targets="claim_support_decision; review_status",
            allowed_values_or_format_de=(
                "`supports_allowed_wording`, `supports_with_limitation`, "
                "`does_not_support`, `needs_more_review`; review_status passend setzen."
            ),
            required_evidence_de=(
                "Manuell pruefen, ob die Quelle den erlaubten Methoden- oder "
                "Interpretationssatz stuetzt."
            ),
            completion_test_de="Claim-Support ist nicht `pending`; Begrenzung bleibt im Review-Kommentar sichtbar.",
            blocked_actions_de="Keine neuen thesis-facing Claims und keine Source-Status-Hochstufung.",
            next_action_de="Danach Blocked-Wording gegen Quelle und Limitation pruefen.",
        ),
        _check_row(
            check_order=4,
            update_phase="blocked_wording_check",
            source_artifacts="data/results/thesis_source_review_progress_ledger.csv",
            totals=totals,
            manual_field_targets="blocked_wording_check; review_comment_de",
            allowed_values_or_format_de="`passed`, `failed`, `needs_more_review`; Kommentar bei failed oder needs_more_review.",
            required_evidence_de=(
                "Pruefen, ob der geplante Text keine Universal-, Intraday-, "
                "Kausalitaets-, Private-Information-, Profitabilitaets- oder "
                "Tradeability-Claims enthaelt."
            ),
            completion_test_de="Blocked-Wording ist nicht `pending`; problematische Formulierungen sind notiert.",
            blocked_actions_de="Keine Ueberclaims und keine Entfernung offener Gates.",
            next_action_de="Danach Citation-Use als Draft, final, not usable oder needs_more_review setzen.",
        ),
        _check_row(
            check_order=5,
            update_phase="citation_use_decision",
            source_artifacts=(
                "data/results/thesis_source_review_progress_ledger.csv; "
                "data/results/thesis_ledger_citation_gate_summary.csv"
            ),
            totals=totals,
            manual_field_targets="citation_use_decision; final_citation_ready",
            allowed_values_or_format_de=(
                "`blocked_pending_manual_review`, `approved_for_draft_citation_only`, "
                "`approved_for_final_citation`, `not_usable_for_claim`, "
                "`needs_more_review`. Final-ready nur bei Page-/Section-Note, "
                "support, passed wording und approved final citation."
            ),
            required_evidence_de=(
                "Citation-Use erst setzen, nachdem Page-/Section-Note, Claim-Support "
                "und Blocked-Wording abgeschlossen sind."
            ),
            completion_test_de=(
                "Final-ready Rows haben `approved_for_final_citation`; alle anderen "
                "Rows bleiben sichtbar blockiert."
            ),
            blocked_actions_de="Keine finale Zitation aus pending, draft-only oder not-usable rows.",
            next_action_de="Reviewer-Metadaten und Kommentar ergaenzen.",
        ),
        _check_row(
            check_order=6,
            update_phase="reviewer_metadata_and_comment",
            source_artifacts="data/results/thesis_source_review_progress_ledger.csv",
            totals=totals,
            manual_field_targets="reviewed_by; reviewed_at; review_comment_de",
            allowed_values_or_format_de=(
                "`reviewed_by`: Name/Kuerzel; `reviewed_at`: ISO-Date; "
                "`review_comment_de`: kurze Begruendung fuer Claim-Support und Citation-Use."
            ),
            required_evidence_de="Reviewer, Datum und Kommentar machen die manuelle Entscheidung nachvollziehbar.",
            completion_test_de="Reviewer-Metadaten sind gesetzt, wenn eine row nicht mehr `pending_manual_review` ist.",
            blocked_actions_de="Keine anonymen finalen Freigaben und keine stillen Ledger-Aenderungen.",
            next_action_de="Ledger regenerieren und Preservation pruefen.",
        ),
        _check_row(
            check_order=7,
            update_phase="regenerate_and_preserve_manual_fields",
            source_artifacts=(
                "operations/project/build_source_review_progress_ledger.py; "
                "operations/project/build_ledger_citation_gate_summary.py"
            ),
            totals=totals,
            manual_field_targets="preserved_manual_fields; review_progress_state",
            allowed_values_or_format_de=(
                "Regeneration muss manuelle Felder per `note_id` bewahren; "
                "Progress State wird deterministisch aus manuellen Feldern abgeleitet."
            ),
            required_evidence_de=(
                "Nach Ledger-Aenderungen Generatoren erneut ausfuehren und Counts "
                "gegen Citation-Gate Summary pruefen."
            ),
            completion_test_de="`preserved_manual_fields=True` fuer geaenderte rows; Citation-Gate Summary aktualisiert.",
            blocked_actions_de="Keine manuelle Feldueberschreibung durch Regeneration.",
            next_action_de="Nach erfolgreichem Rebuild Source Review Checks und Index aktualisieren.",
        ),
        _check_row(
            check_order=8,
            update_phase="final_release_guard",
            source_artifacts=(
                "data/results/thesis_ledger_citation_gate_summary.csv; "
                "docs/project/THESIS_LEDGER_CITATION_GATE_SUMMARY.md"
            ),
            totals=totals,
            manual_field_targets="final_citation_ready",
            allowed_values_or_format_de=(
                "Final release nur, wenn alle benoetigten rows final-ready sind "
                "und keine source_status_change_allowed row existiert."
            ),
            required_evidence_de=(
                "H1/H2/H3/TOTAL Gate muss die finalen Freigaben zeigen; offene "
                "Rows bleiben im BA-Text als Pending-Gate sichtbar."
            ),
            completion_test_de=(
                "Vor finaler BA-Abgabe: 0 pending required rows, 0 source-status "
                "changes, review_check gruen."
            ),
            blocked_actions_de=(
                "keine finale Zitation, keine Quellenstatus-Hochstufung. Keine "
                "Runtime-Agenten, kein MCP, kein Model Routing, keine Kennzahlen "
                "aus LLMs, keine Rohdaten-Prompts und keine Trading-Pfade. "
                "Spaetere Agentenhilfe nur mit max 50 rows und llm_audit_log."
            ),
            next_action_de="Bis dahin bounded Draft fortsetzen und Source Review manuell abarbeiten.",
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
        result = generate_manual_source_review_update_checklist(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_checklist(
    *,
    checklist: pd.DataFrame,
    ledger: pd.DataFrame,
    citation_gate: pd.DataFrame,
    alignment: pd.DataFrame,
    repo_root: Path,
) -> None:
    _require_columns(checklist, CHECKLIST_COLUMNS, "manual source-review update checklist")
    if len(checklist) != 8:
        raise ValueError("Manual source-review update checklist must contain 8 rows.")
    if checklist["check_order"].astype(int).tolist() != list(range(1, 9)):
        raise ValueError("Manual source-review update checklist order must be 1..8.")
    if checklist["check_id"].duplicated().any():
        raise ValueError("Manual source-review update checklist contains duplicate check_id values.")
    if not checklist["ready_for_manual_update"].map(_bool_value).all():
        raise ValueError("Manual source-review update checklist must be ready for manual update.")
    if checklist["ready_for_final_citation_release"].map(_bool_value).any():
        raise ValueError("Manual source-review update checklist must not be ready for final citation release.")
    totals = _summary_counts(ledger=ledger, citation_gate=citation_gate)
    if totals["ledger_rows"] != 23:
        raise ValueError("Manual source-review update checklist expects 23 ledger rows.")
    if totals["unique_sources"] != 9:
        raise ValueError("Manual source-review update checklist expects 9 unique sources.")
    if totals["method_rows"] != 12 or totals["interpretation_rows"] != 11:
        raise ValueError("Manual source-review update checklist expects 12 method and 11 interpretation rows.")
    if totals["external_locator_rows"] != 13 or totals["local_pdf_rows"] != 10:
        raise ValueError("Manual source-review update checklist expects 13 external and 10 local PDF rows.")
    if totals["pending_citation_rows"] != 23 or totals["final_ready_rows"] != 0:
        raise ValueError("Manual source-review update checklist expects 23 pending and 0 final-ready rows.")
    if totals["source_status_change_rows"] != 0:
        raise ValueError("Manual source-review update checklist must not allow source-status changes.")
    _validate_alignment_input(alignment)
    for artifact in (
        "docs/project/THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md",
        "docs/project/THESIS_LEDGER_CITATION_GATE_SUMMARY.md",
        "docs/project/THESIS_H1_H2_H3_DECISION_QUEUE_LEDGER_ALIGNMENT.md",
    ):
        _required_file(repo_root / artifact)
    joined = "\n".join([_join_frame_rows(checklist), _join_frame_rows(ledger)])
    if chr(223) in joined:
        raise ValueError("Manual source-review update checklist must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "page-/section-note",
        "claim-support",
        "blocked-wording",
        "citation-use",
        "approved_for_final_citation",
        "blocked_pending_manual_review",
        "keine finale zitation",
        "keine quellenstatus-hochstufung",
        "keine runtime-agenten",
        "max 50 rows",
        "llm_audit_log",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Manual source-review update checklist missing required terms: " + ", ".join(missing))


def _render_checklist_doc(checklist: pd.DataFrame) -> str:
    total = checklist.iloc[0]
    display = checklist[
        [
            "check_order",
            "update_phase",
            "manual_field_targets",
            "pending_citation_rows",
            "final_ready_rows",
            "completion_test_de",
            "next_action_de",
        ]
    ]
    return (
        "# Manual Source Review Update Checklist\n\n"
        "Diese Checkliste beschreibt, wie die manuellen Felder im Source "
        "Review Progress Ledger aktualisiert werden duerfen. Sie liest keine "
        "Quelleninhalte, trifft keine Claim-Support-Entscheide, setzt keine "
        "Page-/Section-Notes, promotet keinen Quellenstatus und macht keine "
        "finale Zitation.\n\n"
        "## Counts\n\n"
        f"- Checklist rows: {len(checklist)}\n"
        f"- Ledger rows in scope: {int(total['ledger_rows_in_scope'])}\n"
        f"- Unique sources in scope: {int(total['unique_sources_in_scope'])}\n"
        f"- External locator rows: {int(total['external_locator_rows'])}\n"
        f"- Local PDF rows: {int(total['local_pdf_rows'])}\n"
        f"- Pending citation rows: {int(total['pending_citation_rows'])}\n"
        f"- Final ready rows: {int(total['final_ready_rows'])}\n"
        f"- Final citation release ready checklist rows: {int(checklist['ready_for_final_citation_release'].map(_bool_value).sum())}\n\n"
        "## Checklist Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Arbeite diese acht Schritte vor jeder manuellen Ledger-Aenderung ab. "
        "Die einzigen manuell zu pflegenden Ledger-Felder sind "
        "`review_status`, `page_or_section_note`, `claim_support_decision`, "
        "`blocked_wording_check`, `citation_use_decision`, `reviewed_by`, "
        "`reviewed_at` und `review_comment_de`. Finale Zitation bleibt "
        "blockiert, solange Page-/Section-Note, Claim-Support, "
        "Blocked-Wording und Citation-Use nicht abgeschlossen sind. Keine "
        "Quellenstatus-Hochstufung, keine Runtime-Agenten, kein MCP, kein "
        "Model Routing, keine Kennzahlen aus LLMs, keine Rohdaten-Prompts, "
        "max 50 rows und `llm_audit_log` fuer spaetere Agentenhilfe.\n"
    )


def _check_row(
    *,
    check_order: int,
    update_phase: str,
    source_artifacts: str,
    totals: dict[str, int],
    manual_field_targets: str,
    allowed_values_or_format_de: str,
    required_evidence_de: str,
    completion_test_de: str,
    blocked_actions_de: str,
    next_action_de: str,
) -> dict[str, object]:
    return {
        "check_id": f"manual_source_review_update_{check_order:02d}_{update_phase}",
        "check_order": check_order,
        "update_phase": update_phase,
        "source_artifacts": source_artifacts,
        "ledger_rows_in_scope": totals["ledger_rows"],
        "unique_sources_in_scope": totals["unique_sources"],
        "external_locator_rows": totals["external_locator_rows"],
        "local_pdf_rows": totals["local_pdf_rows"],
        "pending_citation_rows": totals["pending_citation_rows"],
        "final_ready_rows": totals["final_ready_rows"],
        "manual_field_targets": manual_field_targets,
        "allowed_values_or_format_de": allowed_values_or_format_de,
        "required_evidence_de": required_evidence_de,
        "completion_test_de": completion_test_de,
        "blocked_actions_de": blocked_actions_de,
        "next_action_de": next_action_de,
        "ready_for_manual_update": True,
        "ready_for_final_citation_release": False,
    }


def _summary_counts(*, ledger: pd.DataFrame, citation_gate: pd.DataFrame) -> dict[str, int]:
    total = _total_gate(citation_gate)
    return {
        "ledger_rows": int(total["ledger_rows"]),
        "unique_sources": int(ledger["source_id"].nunique()),
        "method_rows": int((ledger["item_type"] == "method").sum()),
        "interpretation_rows": int((ledger["item_type"] == "interpretation").sum()),
        "external_locator_rows": int((ledger["access_route"] == "external_locator_review").sum()),
        "local_pdf_rows": int((ledger["access_route"] == "local_pdf_review").sum()),
        "pending_citation_rows": int(total["blocked_pending_citation_rows"]),
        "final_ready_rows": int(total["final_citation_ready_rows"]),
        "source_status_change_rows": int(total["source_status_change_rows"]),
    }


def _total_gate(citation_gate: pd.DataFrame) -> pd.Series:
    total = citation_gate.loc[citation_gate["scope_id"] == "TOTAL"]
    if len(total) != 1:
        raise ValueError("Manual source-review update checklist requires one TOTAL citation-gate row.")
    return total.iloc[0]


def _validate_alignment_input(alignment: pd.DataFrame) -> None:
    if int(alignment["matched_rows"].sum()) != int(alignment["ledger_rows"].sum()):
        raise ValueError("Manual update checklist requires all ledger rows matched to decision queues.")
    if int(alignment["queue_missing_ledger_rows"].sum()) != 0:
        raise ValueError("Manual update checklist alignment has queue rows missing ledger.")
    if int(alignment["ledger_missing_queue_rows"].sum()) != 0:
        raise ValueError("Manual update checklist alignment has ledger rows missing queue.")
    if int(alignment["field_mismatch_rows"].sum()) != 0:
        raise ValueError("Manual update checklist alignment has field mismatches.")


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required manual source-review update checklist input missing: {path}")
    return pd.read_csv(path)


def _required_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Required manual source-review update checklist artifact missing: {path}")


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "ja", "y"}


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
