"""Build a H2 guide for manually filling source-review ledger fields."""

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

GUIDE_OUTPUT = "thesis_h2_source_review_ledger_fill_guide.csv"
GUIDE_DOC_OUTPUT = "THESIS_H2_SOURCE_REVIEW_LEDGER_FILL_GUIDE.md"

GUIDE_COLUMNS: tuple[str, ...] = (
    "guide_id",
    "guide_order",
    "thesis_area",
    "source_id",
    "evidence_id",
    "item_type",
    "worksheet_id",
    "ledger_id",
    "note_id",
    "access_route",
    "review_source_locator",
    "deterministic_artifact",
    "selected_table",
    "selected_figure",
    "current_ledger_review_status",
    "current_ledger_progress_state",
    "current_ledger_citation_use_decision",
    "ledger_match_status",
    "allowed_ledger_fields",
    "fill_sequence_de",
    "page_section_note_instruction_de",
    "claim_support_instruction_de",
    "blocked_wording_instruction_de",
    "citation_use_instruction_de",
    "reviewer_metadata_instruction_de",
    "preservation_check_de",
    "final_gate_de",
    "blocked_actions_de",
    "ready_for_manual_ledger_entry",
    "ready_for_final_release",
)

WORKSHEET_REQUIRED_COLUMNS: tuple[str, ...] = (
    "worksheet_id",
    "worksheet_order",
    "thesis_area",
    "source_id",
    "evidence_id",
    "item_type",
    "access_route",
    "review_source_locator",
    "deterministic_artifact",
    "selected_table",
    "selected_figure",
    "current_review_status",
    "current_citation_use_decision",
    "page_section_note_target_de",
    "claim_support_target_de",
    "blocked_wording_target_de",
    "causal_claim_boundary_de",
    "citation_use_target_de",
    "reviewer_metadata_target_de",
    "final_gate_de",
    "blocked_actions_de",
    "ready_for_manual_entry",
    "ready_for_final_release",
)

LEDGER_REQUIRED_COLUMNS: tuple[str, ...] = (
    "ledger_id",
    "note_id",
    "thesis_area",
    "source_id",
    "evidence_id",
    "item_type",
    "selected_table",
    "selected_figure",
    "deterministic_artifact",
    "access_route",
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
)

CHECKLIST_REQUIRED_COLUMNS: tuple[str, ...] = (
    "check_order",
    "update_phase",
    "manual_field_targets",
    "ready_for_manual_update",
    "ready_for_final_citation_release",
)

ALIGNMENT_REQUIRED_COLUMNS: tuple[str, ...] = (
    "slice_id",
    "ledger_rows",
    "matched_rows",
    "queue_missing_ledger_rows",
    "ledger_missing_queue_rows",
    "field_mismatch_rows",
    "ledger_final_ready_rows",
    "ledger_source_status_change_rows",
    "selected_tables",
    "selected_figures",
    "alignment_status",
)

ALLOWED_LEDGER_FIELDS = (
    "review_status",
    "page_or_section_note",
    "claim_support_decision",
    "blocked_wording_check",
    "citation_use_decision",
    "reviewed_by",
    "reviewed_at",
    "review_comment_de",
)


@dataclass(frozen=True)
class H2SourceReviewLedgerFillGuideResult:
    """Generated H2 ledger-fill guide paths and counts."""

    guide_path: Path
    docs_path: Path
    guide_rows: int
    matched_ledger_rows: int
    unique_sources: int
    method_rows: int
    interpretation_rows: int
    final_release_ready_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "guide_path": str(self.guide_path),
            "docs_path": str(self.docs_path),
            "guide_rows": self.guide_rows,
            "matched_ledger_rows": self.matched_ledger_rows,
            "unique_sources": self.unique_sources,
            "method_rows": self.method_rows,
            "interpretation_rows": self.interpretation_rows,
            "final_release_ready_rows": self.final_release_ready_rows,
        }


def generate_h2_source_review_ledger_fill_guide(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> H2SourceReviewLedgerFillGuideResult:
    """Generate the H2 ledger-fill guide CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    worksheet = _read_csv(results_dir / "thesis_h2_source_review_batch_worksheet.csv")
    ledger = _read_csv(results_dir / "thesis_source_review_progress_ledger.csv")
    update_checklist = _read_csv(results_dir / "thesis_manual_source_review_update_checklist.csv")
    alignment = _read_csv(results_dir / "thesis_h1_h2_h3_decision_queue_ledger_alignment.csv")

    guide = build_h2_source_review_ledger_fill_guide(
        worksheet=worksheet,
        ledger=ledger,
        update_checklist=update_checklist,
        alignment=alignment,
    )
    _validate_guide(
        guide=guide,
        worksheet=worksheet,
        ledger=ledger,
        update_checklist=update_checklist,
        alignment=alignment,
        repo_root=repo_root,
    )

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    guide_path = results_dir / GUIDE_OUTPUT
    docs_path = docs_dir / GUIDE_DOC_OUTPUT
    guide.to_csv(guide_path, index=False)
    docs_path.write_text(_render_guide_doc(guide), encoding="utf-8")

    return H2SourceReviewLedgerFillGuideResult(
        guide_path=guide_path,
        docs_path=docs_path,
        guide_rows=len(guide),
        matched_ledger_rows=int((guide["ledger_match_status"] == "matched_h2_worksheet_to_ledger").sum()),
        unique_sources=int(guide["source_id"].nunique()),
        method_rows=int((guide["item_type"] == "method").sum()),
        interpretation_rows=int((guide["item_type"] == "interpretation").sum()),
        final_release_ready_rows=int(guide["ready_for_final_release"].map(_bool_value).sum()),
    )


def build_h2_source_review_ledger_fill_guide(
    *,
    worksheet: pd.DataFrame,
    ledger: pd.DataFrame,
    update_checklist: pd.DataFrame,
    alignment: pd.DataFrame,
) -> pd.DataFrame:
    """Return a 5-row guide for filling H2 ledger rows manually."""

    _require_columns(worksheet, WORKSHEET_REQUIRED_COLUMNS, "H2 source-review worksheet")
    _require_columns(ledger, LEDGER_REQUIRED_COLUMNS, "source-review progress ledger")
    _require_columns(update_checklist, CHECKLIST_REQUIRED_COLUMNS, "manual update checklist")
    _require_columns(alignment, ALIGNMENT_REQUIRED_COLUMNS, "decision queue ledger alignment")
    _validate_inputs(
        worksheet=worksheet,
        ledger=ledger,
        update_checklist=update_checklist,
        alignment=alignment,
    )

    h2_worksheet = worksheet.loc[worksheet["thesis_area"].astype(str) == "H2"].copy()
    h2_ledger = ledger.loc[ledger["thesis_area"].astype(str) == "H2"].copy()
    ledger_by_key = {
        (str(row["source_id"]), str(row["evidence_id"])): row
        for row in h2_ledger.to_dict(orient="records")
    }
    rows: list[dict[str, object]] = []
    allowed_fields = "; ".join(ALLOWED_LEDGER_FIELDS)
    for order, worksheet_row in enumerate(
        h2_worksheet.sort_values("worksheet_order").to_dict(orient="records"),
        start=1,
    ):
        key = (str(worksheet_row["source_id"]), str(worksheet_row["evidence_id"]))
        ledger_row = ledger_by_key.get(key)
        if ledger_row is None:
            raise ValueError(f"H2 worksheet row has no matching ledger row: {key}.")
        rows.append(
            {
                "guide_id": f"h2_ledger_fill_{order:02d}_{key[0]}__{key[1]}",
                "guide_order": order,
                "thesis_area": "H2",
                "source_id": key[0],
                "evidence_id": key[1],
                "item_type": str(worksheet_row["item_type"]),
                "worksheet_id": str(worksheet_row["worksheet_id"]),
                "ledger_id": str(ledger_row["ledger_id"]),
                "note_id": str(ledger_row["note_id"]),
                "access_route": str(worksheet_row["access_route"]),
                "review_source_locator": str(worksheet_row["review_source_locator"]),
                "deterministic_artifact": str(worksheet_row["deterministic_artifact"]),
                "selected_table": str(worksheet_row["selected_table"]),
                "selected_figure": str(worksheet_row["selected_figure"]),
                "current_ledger_review_status": str(ledger_row["review_status"]),
                "current_ledger_progress_state": str(ledger_row["review_progress_state"]),
                "current_ledger_citation_use_decision": str(ledger_row["citation_use_decision"]),
                "ledger_match_status": "matched_h2_worksheet_to_ledger",
                "allowed_ledger_fields": allowed_fields,
                "fill_sequence_de": (
                    "1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; "
                    "3 Blocked-Wording pruefen; 4 H2 Kausalclaim-Grenze pruefen; "
                    "5 Citation-Use setzen; 6 reviewed_by, reviewed_at und "
                    "review_comment_de dokumentieren; 7 Ledger regenerieren und "
                    "preserved_manual_fields pruefen."
                ),
                "page_section_note_instruction_de": str(
                    worksheet_row["page_section_note_target_de"]
                ),
                "claim_support_instruction_de": str(worksheet_row["claim_support_target_de"]),
                "blocked_wording_instruction_de": (
                    str(worksheet_row["blocked_wording_target_de"])
                    + " H2-spezifisch: "
                    + str(worksheet_row["causal_claim_boundary_de"])
                ),
                "citation_use_instruction_de": str(worksheet_row["citation_use_target_de"]),
                "reviewer_metadata_instruction_de": str(
                    worksheet_row["reviewer_metadata_target_de"]
                ),
                "preservation_check_de": (
                    "Nach manueller Eingabe `operations.project.build_source_review_progress_ledger` "
                    "regenerieren; geaenderte rows muessen `preserved_manual_fields=True` "
                    "und einen passenden `review_progress_state` behalten."
                ),
                "final_gate_de": str(worksheet_row["final_gate_de"]),
                "blocked_actions_de": (
                    str(worksheet_row["blocked_actions_de"])
                    + " Ledger-Fill ist manual-only: keine erfundene Page-/Section-Note, "
                    "keine automatische Claim-Support-Entscheidung, keine finale Zitation, "
                    "keine Quellenstatus-Hochstufung, keine Kausalclaims, keine "
                    "Intraday-Ueberclaims, keine Rohartefakt-Dumps, keine Runtime-Agenten, "
                    "kein MCP, kein Model Routing, keine LLM-Metriken, max 50 rows "
                    "und llm_audit_log fuer spaetere Agentenhilfe."
                ),
                "ready_for_manual_ledger_entry": True,
                "ready_for_final_release": False,
            }
        )
    return pd.DataFrame(rows, columns=GUIDE_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_h2_source_review_ledger_fill_guide(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_guide(
    *,
    guide: pd.DataFrame,
    worksheet: pd.DataFrame,
    ledger: pd.DataFrame,
    update_checklist: pd.DataFrame,
    alignment: pd.DataFrame,
    repo_root: Path,
) -> None:
    _require_columns(guide, GUIDE_COLUMNS, "H2 source-review ledger fill guide")
    _validate_inputs(
        worksheet=worksheet,
        ledger=ledger,
        update_checklist=update_checklist,
        alignment=alignment,
    )
    if len(guide) != 5:
        raise ValueError("H2 ledger-fill guide must contain 5 rows.")
    if guide["guide_order"].astype(int).tolist() != list(range(1, 6)):
        raise ValueError("H2 ledger-fill guide must be ordered 1..5.")
    if guide["guide_id"].duplicated().any():
        raise ValueError("H2 ledger-fill guide contains duplicate IDs.")
    if set(guide["thesis_area"].astype(str)) != {"H2"}:
        raise ValueError("H2 ledger-fill guide must only contain H2 rows.")
    if set(guide["ledger_match_status"].astype(str)) != {"matched_h2_worksheet_to_ledger"}:
        raise ValueError("H2 ledger-fill guide requires all rows matched to the ledger.")
    if int(guide["source_id"].nunique()) != 3:
        raise ValueError("H2 ledger-fill guide expects 3 unique sources.")
    if int((guide["item_type"] == "method").sum()) != 3:
        raise ValueError("H2 ledger-fill guide expects 3 method rows.")
    if int((guide["item_type"] == "interpretation").sum()) != 2:
        raise ValueError("H2 ledger-fill guide expects 2 interpretation rows.")
    if int((guide["access_route"] == "external_locator_review").sum()) != 4:
        raise ValueError("H2 ledger-fill guide expects 4 external locator rows.")
    if int((guide["access_route"] == "local_pdf_review").sum()) != 1:
        raise ValueError("H2 ledger-fill guide expects 1 local PDF row.")
    if set(guide["selected_table"].astype(str)) != {"T3"}:
        raise ValueError("H2 ledger-fill guide must bind table T3.")
    if set(guide["selected_figure"].astype(str)) != {"F2"}:
        raise ValueError("H2 ledger-fill guide must bind figure F2.")
    if not guide["ready_for_manual_ledger_entry"].map(_bool_value).all():
        raise ValueError("H2 ledger-fill guide must be ready for manual ledger entry.")
    if guide["ready_for_final_release"].map(_bool_value).any():
        raise ValueError("H2 ledger-fill guide must not be final-release-ready.")
    if set(guide["current_ledger_progress_state"].astype(str)) != {"pending_manual_review"}:
        raise ValueError("H2 ledger-fill guide expects pending ledger progress.")
    if set(guide["current_ledger_citation_use_decision"].astype(str)) != {
        "blocked_pending_manual_review"
    }:
        raise ValueError("H2 ledger-fill guide expects blocked pending citation rows.")
    for artifact in guide["deterministic_artifact"].astype(str):
        if artifact and artifact.lower() != "nan" and not (repo_root / artifact).exists():
            raise FileNotFoundError(f"H2 ledger-fill guide artifact missing: {artifact}")
    joined = "\n".join(guide.fillna("").astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("H2 ledger-fill guide must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "page-/section-note",
        "claim-support",
        "blocked-wording",
        "citation-use",
        "kausalclaim-grenze",
        "review_status",
        "page_or_section_note",
        "claim_support_decision",
        "blocked_wording_check",
        "citation_use_decision",
        "reviewed_by",
        "reviewed_at",
        "review_comment_de",
        "preserved_manual_fields",
        "manual-only",
        "keine finale zitation",
        "keine quellenstatus-hochstufung",
        "keine kausalclaims",
        "keine intraday-ueberclaims",
        "keine runtime-agenten",
        "keine rohartefakt-dumps",
        "max 50 rows",
        "llm_audit_log",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("H2 ledger-fill guide missing required terms: " + ", ".join(missing))


def _validate_inputs(
    *,
    worksheet: pd.DataFrame,
    ledger: pd.DataFrame,
    update_checklist: pd.DataFrame,
    alignment: pd.DataFrame,
) -> None:
    _require_columns(worksheet, WORKSHEET_REQUIRED_COLUMNS, "H2 source-review worksheet")
    _require_columns(ledger, LEDGER_REQUIRED_COLUMNS, "source-review progress ledger")
    _require_columns(update_checklist, CHECKLIST_REQUIRED_COLUMNS, "manual update checklist")
    _require_columns(alignment, ALIGNMENT_REQUIRED_COLUMNS, "decision queue ledger alignment")

    h2_worksheet = worksheet.loc[worksheet["thesis_area"].astype(str) == "H2"]
    h2_ledger = ledger.loc[ledger["thesis_area"].astype(str) == "H2"]
    if len(h2_worksheet) != 5:
        raise ValueError("H2 ledger-fill guide expects 5 H2 worksheet rows.")
    if len(h2_ledger) != 5:
        raise ValueError("H2 ledger-fill guide expects 5 H2 ledger rows.")
    worksheet_keys = _keys(h2_worksheet)
    ledger_keys = _keys(h2_ledger)
    if worksheet_keys != ledger_keys:
        raise ValueError("H2 worksheet and ledger rows must match by source_id and evidence_id.")
    if h2_worksheet["ready_for_final_release"].map(_bool_value).any():
        raise ValueError("H2 worksheet must not be final-release-ready.")
    if h2_ledger["source_status_change_allowed"].map(_bool_value).any():
        raise ValueError("H2 ledger-fill guide must not allow source-status changes.")
    if h2_ledger["final_citation_ready"].map(_bool_value).any():
        raise ValueError("H2 ledger-fill guide expects 0 final-ready ledger rows.")
    h2_alignment = alignment.loc[alignment["slice_id"].astype(str) == "H2"]
    if len(h2_alignment) != 1:
        raise ValueError("H2 ledger-fill guide requires one H2 alignment row.")
    row = h2_alignment.iloc[0]
    if int(row["ledger_rows"]) != 5 or int(row["matched_rows"]) != 5:
        raise ValueError("H2 ledger-fill guide requires 5 matched H2 ledger rows.")
    for column in ("queue_missing_ledger_rows", "ledger_missing_queue_rows", "field_mismatch_rows"):
        if int(row[column]) != 0:
            raise ValueError("H2 ledger-fill guide requires 0 alignment gaps.")
    if int(row["ledger_final_ready_rows"]) != 0:
        raise ValueError("H2 ledger-fill guide expects 0 final-ready H2 ledger rows.")
    if int(row["ledger_source_status_change_rows"]) != 0:
        raise ValueError("H2 ledger-fill guide expects 0 H2 source-status change rows.")
    if str(row["selected_tables"]) != "T3" or str(row["selected_figures"]) != "F2":
        raise ValueError("H2 ledger-fill guide expects T3/F2 alignment.")
    if len(update_checklist) != 8:
        raise ValueError("H2 ledger-fill guide expects 8 manual update checklist rows.")
    if not update_checklist["ready_for_manual_update"].map(_bool_value).all():
        raise ValueError("H2 ledger-fill guide requires manual-update-ready checklist rows.")
    if update_checklist["ready_for_final_citation_release"].map(_bool_value).any():
        raise ValueError("H2 ledger-fill guide requires no final-release-ready checklist rows.")


def _render_guide_doc(guide: pd.DataFrame) -> str:
    display = guide[
        [
            "guide_order",
            "source_id",
            "evidence_id",
            "item_type",
            "ledger_id",
            "access_route",
            "current_ledger_progress_state",
            "fill_sequence_de",
        ]
    ]
    return (
        "# H2 Source Review Ledger Fill Guide\n\n"
        "Dieser Guide zeigt, wie die fuenf H2 Worksheet-Zeilen manuell in den "
        "Source Review Progress Ledger uebertragen werden. Er schreibt keine "
        "Ledger-Felder, liest keine Quelleninhalte, setzt keine Page-/Section-"
        "Notes, entscheidet keinen Claim-Support, promotet keinen Quellenstatus "
        "und erzeugt keine finale Zitation. Die H2 Kausalclaim-Grenze bleibt "
        "pro Zeile sichtbar.\n\n"
        "## Counts\n\n"
        f"- Guide rows: {len(guide)}\n"
        f"- Matched ledger rows: {int((guide['ledger_match_status'] == 'matched_h2_worksheet_to_ledger').sum())}\n"
        f"- Unique sources: {int(guide['source_id'].nunique())}\n"
        f"- Method rows: {int((guide['item_type'] == 'method').sum())}\n"
        f"- Interpretation rows: {int((guide['item_type'] == 'interpretation').sum())}\n"
        f"- External locator rows: {int((guide['access_route'] == 'external_locator_review').sum())}\n"
        f"- Local PDF rows: {int((guide['access_route'] == 'local_pdf_review').sum())}\n"
        f"- Final release ready rows: {int(guide['ready_for_final_release'].map(_bool_value).sum())}\n"
        "- Selected table/figure: T3/F2\n\n"
        "## Fill Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Arbeite die Guide-Zeilen in `guide_order` ab. Pro Zeile nur diese "
        "Ledger-Felder manuell pflegen: `review_status`, "
        "`page_or_section_note`, `claim_support_decision`, "
        "`blocked_wording_check`, `citation_use_decision`, `reviewed_by`, "
        "`reviewed_at` und `review_comment_de`. Fuer H2 zusaetzlich die "
        "Kausalclaim-Grenze pruefen: keine Kausalitaet, keine sofortige "
        "Marktreaktion und keine Intraday-Ueberclaims aus daily Event-Windows. "
        "Danach den Ledger regenerieren und pruefen, ob "
        "`preserved_manual_fields=True` und der `review_progress_state` "
        "plausibel gesetzt ist. Keine finale Zitation, keine "
        "Quellenstatus-Hochstufung, keine Kausalclaims, keine "
        "Rohartefakt-Dumps, keine Runtime-Agenten, kein MCP, kein Model "
        "Routing, keine LLM-Metriken, max 50 rows und `llm_audit_log` fuer "
        "spaetere Agentenhilfe.\n"
    )


def _keys(frame: pd.DataFrame) -> set[tuple[str, str]]:
    return set(
        zip(
            frame["source_id"].astype(str),
            frame["evidence_id"].astype(str),
            strict=True,
        )
    )


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required H2 ledger-fill guide input missing: {path}")
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
    return str(value).strip().lower() in {"true", "1", "yes", "ja", "y"}


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
