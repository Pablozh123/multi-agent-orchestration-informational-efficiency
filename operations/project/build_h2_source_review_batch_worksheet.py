"""Build a manual worksheet for the H2 source-review batch."""

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

WORKSHEET_OUTPUT = "thesis_h2_source_review_batch_worksheet.csv"
WORKSHEET_DOC_OUTPUT = "THESIS_H2_SOURCE_REVIEW_BATCH_WORKSHEET.md"

WORKSHEET_COLUMNS: tuple[str, ...] = (
    "worksheet_id",
    "worksheet_order",
    "thesis_area",
    "execution_batch",
    "source_id",
    "source_title",
    "source_status",
    "evidence_id",
    "item_type",
    "access_route",
    "review_source_locator",
    "deterministic_artifact",
    "selected_table",
    "selected_figure",
    "current_review_status",
    "current_claim_support_decision",
    "current_blocked_wording_check",
    "current_citation_use_decision",
    "required_manual_fields_de",
    "page_section_note_target_de",
    "claim_support_target_de",
    "blocked_wording_target_de",
    "causal_claim_boundary_de",
    "citation_use_target_de",
    "reviewer_metadata_target_de",
    "final_gate_de",
    "blocked_actions_de",
    "next_action_de",
    "ready_for_manual_entry",
    "ready_for_final_release",
)

EXECUTION_REQUIRED_COLUMNS: tuple[str, ...] = (
    "execution_order",
    "execution_batch",
    "thesis_area",
    "source_id",
    "source_title",
    "source_status",
    "evidence_id",
    "item_type",
    "access_route",
    "review_source_locator",
    "deterministic_artifact",
    "selected_table",
    "selected_figure",
    "current_review_status",
    "current_claim_support_decision",
    "current_blocked_wording_check",
    "current_citation_use_decision",
    "source_status_change_allowed",
    "final_citation_ready",
    "manual_execution_instruction_de",
    "final_citation_gate_de",
    "do_not_claim_de",
)

BATCH_REQUIRED_COLUMNS: tuple[str, ...] = (
    "batch_plan_id",
    "thesis_area",
    "source_review_rows",
    "unique_sources",
    "method_rows",
    "interpretation_rows",
    "external_locator_rows",
    "local_pdf_rows",
    "pending_citation_rows",
    "final_ready_rows",
    "source_status_change_rows",
    "selected_tables",
    "selected_figures",
    "update_checklist_steps",
    "required_manual_fields_de",
    "ready_for_manual_execution",
    "ready_for_final_release",
)

CHECKLIST_REQUIRED_COLUMNS: tuple[str, ...] = (
    "check_order",
    "update_phase",
    "manual_field_targets",
    "ready_for_manual_update",
    "ready_for_final_citation_release",
)

H2_BATCH_ID = "batch_plan_h2"
H2_EXECUTION_BATCH = "batch_02_h2_event_window_source_review"


@dataclass(frozen=True)
class H2SourceReviewBatchWorksheetResult:
    """Generated H2 source-review worksheet paths and counts."""

    worksheet_path: Path
    docs_path: Path
    worksheet_rows: int
    unique_sources: int
    method_rows: int
    interpretation_rows: int
    pending_citation_rows: int
    final_release_ready_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "worksheet_path": str(self.worksheet_path),
            "docs_path": str(self.docs_path),
            "worksheet_rows": self.worksheet_rows,
            "unique_sources": self.unique_sources,
            "method_rows": self.method_rows,
            "interpretation_rows": self.interpretation_rows,
            "pending_citation_rows": self.pending_citation_rows,
            "final_release_ready_rows": self.final_release_ready_rows,
        }


def generate_h2_source_review_batch_worksheet(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> H2SourceReviewBatchWorksheetResult:
    """Generate the H2 source-review batch worksheet CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    execution_pass = _read_csv(
        results_dir / "thesis_h1_h2_h3_manual_source_review_execution_pass.csv"
    )
    batch_plan = _read_csv(results_dir / "thesis_source_review_batch_execution_plan.csv")
    update_checklist = _read_csv(results_dir / "thesis_manual_source_review_update_checklist.csv")

    worksheet = build_h2_source_review_batch_worksheet(
        execution_pass=execution_pass,
        batch_plan=batch_plan,
        update_checklist=update_checklist,
    )
    _validate_worksheet(
        worksheet=worksheet,
        execution_pass=execution_pass,
        batch_plan=batch_plan,
        update_checklist=update_checklist,
    )

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    worksheet_path = results_dir / WORKSHEET_OUTPUT
    docs_path = docs_dir / WORKSHEET_DOC_OUTPUT
    worksheet.to_csv(worksheet_path, index=False)
    docs_path.write_text(_render_worksheet_doc(worksheet, batch_plan), encoding="utf-8")

    return H2SourceReviewBatchWorksheetResult(
        worksheet_path=worksheet_path,
        docs_path=docs_path,
        worksheet_rows=len(worksheet),
        unique_sources=int(worksheet["source_id"].nunique()),
        method_rows=int((worksheet["item_type"] == "method").sum()),
        interpretation_rows=int((worksheet["item_type"] == "interpretation").sum()),
        pending_citation_rows=int(
            (worksheet["current_citation_use_decision"] == "blocked_pending_manual_review").sum()
        ),
        final_release_ready_rows=int(worksheet["ready_for_final_release"].map(_bool_value).sum()),
    )


def build_h2_source_review_batch_worksheet(
    *,
    execution_pass: pd.DataFrame,
    batch_plan: pd.DataFrame,
    update_checklist: pd.DataFrame,
) -> pd.DataFrame:
    """Return a 5-row H2 worksheet for manual source-review entry."""

    _require_columns(execution_pass, EXECUTION_REQUIRED_COLUMNS, "manual source-review execution pass")
    _require_columns(batch_plan, BATCH_REQUIRED_COLUMNS, "source review batch execution plan")
    _require_columns(update_checklist, CHECKLIST_REQUIRED_COLUMNS, "manual source-review update checklist")
    _validate_inputs(
        execution_pass=execution_pass,
        batch_plan=batch_plan,
        update_checklist=update_checklist,
    )

    h2_rows = execution_pass.loc[execution_pass["thesis_area"] == "H2"].copy()
    h2_rows = h2_rows.sort_values(
        by=["execution_order", "source_id", "item_type", "evidence_id"],
        kind="stable",
    )
    batch = _batch_row(batch_plan)
    manual_fields = _clean(batch["required_manual_fields_de"])
    rows: list[dict[str, object]] = []
    for order, row in enumerate(h2_rows.to_dict(orient="records"), start=1):
        source_id = _clean(row["source_id"])
        evidence_id = _clean(row["evidence_id"])
        item_type = _clean(row["item_type"])
        rows.append(
            {
                "worksheet_id": f"h2_source_review_{order:02d}_{source_id}__{evidence_id}",
                "worksheet_order": order,
                "thesis_area": "H2",
                "execution_batch": H2_EXECUTION_BATCH,
                "source_id": source_id,
                "source_title": _clean(row["source_title"]),
                "source_status": _clean(row["source_status"]),
                "evidence_id": evidence_id,
                "item_type": item_type,
                "access_route": _clean(row["access_route"]),
                "review_source_locator": _clean(row["review_source_locator"]),
                "deterministic_artifact": _clean(row["deterministic_artifact"]),
                "selected_table": _clean(row["selected_table"]),
                "selected_figure": _clean(row["selected_figure"]),
                "current_review_status": _clean(row["current_review_status"]),
                "current_claim_support_decision": _clean(row["current_claim_support_decision"]),
                "current_blocked_wording_check": _clean(row["current_blocked_wording_check"]),
                "current_citation_use_decision": _clean(row["current_citation_use_decision"]),
                "required_manual_fields_de": manual_fields,
                "page_section_note_target_de": (
                    "Manuell Quelle oeffnen und Page-/Section-Note fuer "
                    f"`{source_id}` / `{evidence_id}` eintragen; keine erfundene Seitenzahl."
                ),
                "claim_support_target_de": (
                    "Claim-Support manuell setzen: supports_allowed_wording, "
                    "supports_with_limitation, does_not_support oder needs_more_review."
                ),
                "blocked_wording_target_de": (
                    "Blocked-Wording pruefen: keine Intraday-"
                    "Geschwindigkeitsaussage, keine post-hoc Ereignisauswahl "
                    "und kein kausaler Ereignisbeweis."
                ),
                "causal_claim_boundary_de": (
                    "Kausalclaim-Grenze: H2 darf nur daily event-window movement "
                    "und deskriptive Reaktion im verfuegbaren Tagesraster beschreiben; "
                    "keine Kausalitaet und keine sofortige Marktreaktion behaupten."
                ),
                "citation_use_target_de": (
                    "Citation-Use erst nach Page-/Section-Note, Claim-Support, "
                    "Blocked-Wording und Kausalclaim-Grenze setzen; pending bleibt sichtbar blockiert."
                ),
                "reviewer_metadata_target_de": (
                    "reviewed_by, reviewed_at und review_comment_de erst nach "
                    "manueller Quellenpruefung ergaenzen."
                ),
                "final_gate_de": _clean(row["final_citation_gate_de"]),
                "blocked_actions_de": (
                    _clean(row["do_not_claim_de"])
                    + " Keine finale Zitation, keine Quellenstatus-Hochstufung, "
                    "keine Kausalclaims, keine Intraday-Ueberclaims, keine Runtime-Agenten, "
                    "keine Rohartefakt-Dumps, max 50 rows und llm_audit_log fuer spaetere Agentenhilfe."
                ),
                "next_action_de": _clean(row["manual_execution_instruction_de"]),
                "ready_for_manual_entry": True,
                "ready_for_final_release": False,
            }
        )
    return pd.DataFrame(rows, columns=WORKSHEET_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_h2_source_review_batch_worksheet(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_worksheet(
    *,
    worksheet: pd.DataFrame,
    execution_pass: pd.DataFrame,
    batch_plan: pd.DataFrame,
    update_checklist: pd.DataFrame,
) -> None:
    _require_columns(worksheet, WORKSHEET_COLUMNS, "H2 source-review batch worksheet")
    _validate_inputs(
        execution_pass=execution_pass,
        batch_plan=batch_plan,
        update_checklist=update_checklist,
    )
    if len(worksheet) != 5:
        raise ValueError("H2 source-review batch worksheet must contain 5 rows.")
    if worksheet["worksheet_order"].astype(int).tolist() != list(range(1, 6)):
        raise ValueError("H2 source-review batch worksheet must be ordered 1..5.")
    if worksheet["worksheet_id"].duplicated().any():
        raise ValueError("H2 source-review batch worksheet contains duplicate IDs.")
    if set(worksheet["thesis_area"].astype(str)) != {"H2"}:
        raise ValueError("H2 source-review batch worksheet must only contain H2 rows.")
    if set(worksheet["selected_table"].astype(str)) != {"T3"}:
        raise ValueError("H2 source-review batch worksheet must bind table T3.")
    if set(worksheet["selected_figure"].astype(str)) != {"F2"}:
        raise ValueError("H2 source-review batch worksheet must bind figure F2.")
    if int(worksheet["source_id"].nunique()) != 3:
        raise ValueError("H2 source-review batch worksheet expects 3 unique sources.")
    if int((worksheet["item_type"] == "method").sum()) != 3:
        raise ValueError("H2 source-review batch worksheet expects 3 method rows.")
    if int((worksheet["item_type"] == "interpretation").sum()) != 2:
        raise ValueError("H2 source-review batch worksheet expects 2 interpretation rows.")
    if int((worksheet["access_route"] == "external_locator_review").sum()) != 4:
        raise ValueError("H2 source-review batch worksheet expects 4 external locator rows.")
    if int((worksheet["access_route"] == "local_pdf_review").sum()) != 1:
        raise ValueError("H2 source-review batch worksheet expects 1 local PDF row.")
    if not worksheet["ready_for_manual_entry"].map(_bool_value).all():
        raise ValueError("H2 source-review batch worksheet must be ready for manual entry.")
    if worksheet["ready_for_final_release"].map(_bool_value).any():
        raise ValueError("H2 source-review batch worksheet must not be final-release-ready.")
    if set(worksheet["current_review_status"].astype(str)) != {"pending_manual_review"}:
        raise ValueError("H2 source-review batch worksheet expects pending manual review rows.")
    if set(worksheet["current_citation_use_decision"].astype(str)) != {"blocked_pending_manual_review"}:
        raise ValueError("H2 source-review batch worksheet expects blocked pending citation rows.")
    joined = "\n".join(worksheet.fillna("").astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("H2 source-review batch worksheet must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "page-/section-note",
        "claim-support",
        "blocked-wording",
        "citation-use",
        "kausalclaim-grenze",
        "reviewed_by",
        "reviewed_at",
        "review_comment_de",
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
        raise ValueError("H2 source-review batch worksheet missing required terms: " + ", ".join(missing))


def _validate_inputs(
    *,
    execution_pass: pd.DataFrame,
    batch_plan: pd.DataFrame,
    update_checklist: pd.DataFrame,
) -> None:
    _require_columns(execution_pass, EXECUTION_REQUIRED_COLUMNS, "manual source-review execution pass")
    _require_columns(batch_plan, BATCH_REQUIRED_COLUMNS, "source review batch execution plan")
    _require_columns(update_checklist, CHECKLIST_REQUIRED_COLUMNS, "manual source-review update checklist")
    batch = _batch_row(batch_plan)
    if not _bool_value(batch["ready_for_manual_execution"]):
        raise ValueError("H2 source-review batch worksheet requires manual-execution-ready H2 batch.")
    if _bool_value(batch["ready_for_final_release"]):
        raise ValueError("H2 source-review batch worksheet requires H2 batch not final-release-ready.")
    expected = {
        "source_review_rows": 5,
        "unique_sources": 3,
        "method_rows": 3,
        "interpretation_rows": 2,
        "external_locator_rows": 4,
        "local_pdf_rows": 1,
        "pending_citation_rows": 5,
        "final_ready_rows": 0,
        "source_status_change_rows": 0,
        "update_checklist_steps": 8,
    }
    for column, expected_value in expected.items():
        if int(batch[column]) != expected_value:
            raise ValueError(f"H2 batch plan expected {column}={expected_value}.")
    if _clean(batch["selected_tables"]) != "T3" or _clean(batch["selected_figures"]) != "F2":
        raise ValueError("H2 source-review batch worksheet expects T3/F2 binding.")
    h2_rows = execution_pass.loc[execution_pass["thesis_area"] == "H2"]
    if len(h2_rows) != 5:
        raise ValueError("H2 source-review batch worksheet expects 5 H2 execution rows.")
    if h2_rows["source_status_change_allowed"].map(_bool_value).any():
        raise ValueError("H2 source-review batch worksheet must not allow source-status changes.")
    if h2_rows["final_citation_ready"].map(_bool_value).any():
        raise ValueError("H2 source-review batch worksheet expects 0 final-ready execution rows.")
    if len(update_checklist) != 8:
        raise ValueError("H2 source-review batch worksheet expects 8 update checklist rows.")
    if not update_checklist["ready_for_manual_update"].map(_bool_value).all():
        raise ValueError("H2 source-review batch worksheet requires manual-update-ready checklist rows.")
    if update_checklist["ready_for_final_citation_release"].map(_bool_value).any():
        raise ValueError("H2 source-review batch worksheet requires no final-release-ready checklist rows.")


def _render_worksheet_doc(worksheet: pd.DataFrame, batch_plan: pd.DataFrame) -> str:
    batch = _batch_row(batch_plan)
    display = worksheet[
        [
            "worksheet_order",
            "source_id",
            "evidence_id",
            "item_type",
            "access_route",
            "selected_table",
            "selected_figure",
            "current_citation_use_decision",
            "causal_claim_boundary_de",
            "next_action_de",
        ]
    ]
    return (
        "# H2 Source Review Batch Worksheet\n\n"
        "Dieses Worksheet ist die manuelle Arbeitsliste fuer den zweiten H2 "
        "Source-Review-Batch. Es setzt keine Page-/Section-Notes, trifft keine "
        "Claim-Support-Entscheide, promotet keinen Quellenstatus und erzeugt "
        "keine finale Zitation.\n\n"
        "## Counts\n\n"
        f"- Worksheet rows: {len(worksheet)}\n"
        f"- Unique sources: {int(worksheet['source_id'].nunique())}\n"
        f"- Method rows: {int((worksheet['item_type'] == 'method').sum())}\n"
        f"- Interpretation rows: {int((worksheet['item_type'] == 'interpretation').sum())}\n"
        f"- External locator rows: {int((worksheet['access_route'] == 'external_locator_review').sum())}\n"
        f"- Local PDF rows: {int((worksheet['access_route'] == 'local_pdf_review').sum())}\n"
        f"- Pending citation rows: {int((worksheet['current_citation_use_decision'] == 'blocked_pending_manual_review').sum())}\n"
        f"- Final release ready rows: {int(worksheet['ready_for_final_release'].map(_bool_value).sum())}\n"
        f"- Selected table/figure: {_clean(batch['selected_tables'])}/{_clean(batch['selected_figures'])}\n"
        f"- Update checklist steps: {int(batch['update_checklist_steps'])}\n\n"
        "## Worksheet Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Arbeite H2 row-by-row: Quelle oeffnen, Page-/Section-Note eintragen, "
        "Claim-Support entscheiden, Blocked-Wording und Kausalclaim-Grenze "
        "pruefen, Citation-Use setzen und reviewer metadata dokumentieren. "
        "Erlaubte Ledger-Felder bleiben `review_status`, "
        "`page_or_section_note`, `claim_support_decision`, "
        "`blocked_wording_check`, `citation_use_decision`, `reviewed_by`, "
        "`reviewed_at` und `review_comment_de`. Keine finale Zitation, keine "
        "Quellenstatus-Hochstufung, keine Kausalclaims, keine "
        "Intraday-Ueberclaims, keine Rohartefakt-Dumps und keine "
        "Runtime-Agenten. Spaetere Agentenhilfe nur bounded mit max 50 rows "
        "und `llm_audit_log`.\n"
    )


def _batch_row(batch_plan: pd.DataFrame) -> pd.Series:
    rows = batch_plan.loc[batch_plan["batch_plan_id"] == H2_BATCH_ID]
    if len(rows) != 1:
        raise ValueError("H2 source-review batch worksheet requires one H2 batch-plan row.")
    return rows.iloc[0]


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required H2 source-review worksheet input missing: {path}")
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


def _clean(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


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
