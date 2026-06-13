"""Build a batch execution plan for the manual H1-H2-H3 source review."""

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

BATCH_PLAN_OUTPUT = "thesis_source_review_batch_execution_plan.csv"
BATCH_PLAN_DOC_OUTPUT = "THESIS_SOURCE_REVIEW_BATCH_EXECUTION_PLAN.md"

BATCH_PLAN_COLUMNS: tuple[str, ...] = (
    "batch_plan_id",
    "batch_order",
    "batch_scope",
    "execution_batch",
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
    "batch_work_rule_de",
    "completion_gate_de",
    "blocked_actions_de",
    "next_action_de",
    "ready_for_manual_execution",
    "ready_for_final_release",
)

EXECUTION_REQUIRED_COLUMNS: tuple[str, ...] = (
    "execution_batch",
    "thesis_area",
    "source_id",
    "item_type",
    "access_route",
    "selected_table",
    "selected_figure",
    "source_status_change_allowed",
    "final_citation_ready",
)

CHECKLIST_REQUIRED_COLUMNS: tuple[str, ...] = (
    "check_order",
    "ready_for_manual_update",
    "ready_for_final_citation_release",
)

CITATION_GATE_REQUIRED_COLUMNS: tuple[str, ...] = (
    "scope_id",
    "ledger_rows",
    "unique_sources",
    "method_rows",
    "interpretation_rows",
    "blocked_pending_citation_rows",
    "final_citation_ready_rows",
    "source_status_change_rows",
    "selected_tables",
    "selected_figures",
)

ALIGNMENT_REQUIRED_COLUMNS: tuple[str, ...] = (
    "slice_id",
    "ledger_rows",
    "matched_rows",
    "queue_missing_ledger_rows",
    "ledger_missing_queue_rows",
    "field_mismatch_rows",
)

CORE_AREAS: tuple[str, ...] = ("H1", "H2", "H3")
AREA_BATCHES: dict[str, str] = {
    "H1": "batch_01_h1_forecast_quality_source_review",
    "H2": "batch_02_h2_event_window_source_review",
    "H3": "batch_03_h3_wallet_timing_source_review",
}
MANUAL_FIELDS_DE = (
    "`review_status`, `page_or_section_note`, `claim_support_decision`, "
    "`blocked_wording_check`, `citation_use_decision`, `reviewed_by`, "
    "`reviewed_at`, `review_comment_de`"
)


@dataclass(frozen=True)
class SourceReviewBatchExecutionPlanResult:
    """Generated source-review batch execution plan paths and counts."""

    batch_plan_path: Path
    docs_path: Path
    batch_plan_rows: int
    source_review_rows: int
    unique_sources: int
    pending_citation_rows: int
    final_ready_rows: int
    final_release_ready_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "batch_plan_path": str(self.batch_plan_path),
            "docs_path": str(self.docs_path),
            "batch_plan_rows": self.batch_plan_rows,
            "source_review_rows": self.source_review_rows,
            "unique_sources": self.unique_sources,
            "pending_citation_rows": self.pending_citation_rows,
            "final_ready_rows": self.final_ready_rows,
            "final_release_ready_rows": self.final_release_ready_rows,
        }


def generate_source_review_batch_execution_plan(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> SourceReviewBatchExecutionPlanResult:
    """Generate the source-review batch execution plan CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    execution_pass = _read_csv(
        results_dir / "thesis_h1_h2_h3_manual_source_review_execution_pass.csv"
    )
    update_checklist = _read_csv(results_dir / "thesis_manual_source_review_update_checklist.csv")
    citation_gate = _read_csv(results_dir / "thesis_ledger_citation_gate_summary.csv")
    alignment = _read_csv(
        results_dir / "thesis_h1_h2_h3_decision_queue_ledger_alignment.csv"
    )

    batch_plan = build_source_review_batch_execution_plan(
        execution_pass=execution_pass,
        update_checklist=update_checklist,
        citation_gate=citation_gate,
        alignment=alignment,
    )
    _validate_batch_plan(
        batch_plan=batch_plan,
        execution_pass=execution_pass,
        update_checklist=update_checklist,
        citation_gate=citation_gate,
        alignment=alignment,
    )

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    batch_plan_path = results_dir / BATCH_PLAN_OUTPUT
    docs_path = docs_dir / BATCH_PLAN_DOC_OUTPUT
    batch_plan.to_csv(batch_plan_path, index=False)
    docs_path.write_text(_render_batch_plan_doc(batch_plan), encoding="utf-8")

    total = _plan_row(batch_plan, "batch_plan_total_rebuild_gate")
    return SourceReviewBatchExecutionPlanResult(
        batch_plan_path=batch_plan_path,
        docs_path=docs_path,
        batch_plan_rows=len(batch_plan),
        source_review_rows=int(total["source_review_rows"]),
        unique_sources=int(total["unique_sources"]),
        pending_citation_rows=int(total["pending_citation_rows"]),
        final_ready_rows=int(total["final_ready_rows"]),
        final_release_ready_rows=int(
            batch_plan["ready_for_final_release"].map(_bool_value).sum()
        ),
    )


def build_source_review_batch_execution_plan(
    *,
    execution_pass: pd.DataFrame,
    update_checklist: pd.DataFrame,
    citation_gate: pd.DataFrame,
    alignment: pd.DataFrame,
) -> pd.DataFrame:
    """Return four manual execution batches from the current source-review gates."""

    _require_columns(execution_pass, EXECUTION_REQUIRED_COLUMNS, "manual source-review execution pass")
    _require_columns(update_checklist, CHECKLIST_REQUIRED_COLUMNS, "manual source-review update checklist")
    _require_columns(citation_gate, CITATION_GATE_REQUIRED_COLUMNS, "ledger citation gate summary")
    _require_columns(alignment, ALIGNMENT_REQUIRED_COLUMNS, "decision queue ledger alignment")
    _validate_inputs(
        execution_pass=execution_pass,
        update_checklist=update_checklist,
        citation_gate=citation_gate,
        alignment=alignment,
    )

    checklist_steps = int(update_checklist["check_order"].nunique())
    rows = [
        _area_plan_row(
            area="H1",
            batch_order=1,
            execution_pass=execution_pass,
            citation_gate=citation_gate,
            checklist_steps=checklist_steps,
            batch_work_rule_de=(
                "H1 zuerst abarbeiten: Forecast-quality Quellen manuell oeffnen, "
                "Page-/Section-Note, Claim-Support, Blocked-Wording und "
                "Citation-Use je Decision Row setzen; T2/F1 bleiben der "
                "Tabellen-/Figurenkontext."
            ),
            completion_gate_de=(
                "H1 ist nur fuer finale Zitation bereit, wenn alle 10 H1 rows "
                "manuell abgeschlossen sind; aktuell 10 pending citation rows "
                "und 0 final-ready rows."
            ),
            blocked_actions_de=(
                "Keine finale Zitation, keine Quellenstatus-Hochstufung, "
                "keine Reaktionsgeschwindigkeits- oder allgemeine "
                "Marktueberlegenheitsclaims, keine Runtime-Agenten."
            ),
            next_action_de="H1 Batch manuell gegen die Update Checklist starten.",
        ),
        _area_plan_row(
            area="H2",
            batch_order=2,
            execution_pass=execution_pass,
            citation_gate=citation_gate,
            checklist_steps=checklist_steps,
            batch_work_rule_de=(
                "H2 danach abarbeiten: Event-Window Quellen manuell pruefen, "
                "Page-/Section-Note, Claim-Support, Blocked-Wording und "
                "Citation-Use setzen; die Kausalclaim-Grenze bleibt bei jeder "
                "row sichtbar, T3/F2 bleiben der Tabellen-/Figurenkontext."
            ),
            completion_gate_de=(
                "H2 ist nur fuer finale Zitation bereit, wenn alle 5 H2 rows "
                "manuell abgeschlossen sind; aktuell 5 pending citation rows "
                "und 0 final-ready rows."
            ),
            blocked_actions_de=(
                "Keine finale Zitation, keine Kausalclaims, keine Intraday-"
                "Ueberclaims, keine Quellenstatus-Hochstufung und keine "
                "Runtime-Agenten."
            ),
            next_action_de="Nach H1 den H2 Batch mit Kausalclaim-Grenze manuell abarbeiten.",
        ),
        _area_plan_row(
            area="H3",
            batch_order=3,
            execution_pass=execution_pass,
            citation_gate=citation_gate,
            checklist_steps=checklist_steps,
            batch_work_rule_de=(
                "H3 zuletzt im empirischen Kern abarbeiten: Wallet-, Granger- "
                "und Timing-Quellen manuell pruefen, Page-/Section-Note, "
                "Claim-Support, Blocked-Wording und Citation-Use setzen; "
                "Granger-Grenze und Wallet-Grenze bleiben in jeder Entscheidung "
                "sichtbar, T4/F3 bleiben der Tabellen-/Figurenkontext."
            ),
            completion_gate_de=(
                "H3 ist nur fuer finale Zitation bereit, wenn alle 8 H3 rows "
                "manuell abgeschlossen sind; aktuell 8 pending citation rows "
                "und 0 final-ready rows."
            ),
            blocked_actions_de=(
                "Keine finale Zitation, keine Kausalclaims, keine "
                "Private-Information-Beweise, keine willkuerlichen "
                "Whale-Schwellen, keine Wallet-Adressen, keine Trading-Claims, "
                "keine Profitabilitaetsclaims, keine Quellenstatus-Hochstufung "
                "und keine Runtime-Agenten."
            ),
            next_action_de="Nach H2 den H3 Batch mit Granger-Grenze und Wallet-Grenze abarbeiten.",
        ),
        _total_plan_row(
            execution_pass=execution_pass,
            citation_gate=citation_gate,
            checklist_steps=checklist_steps,
        ),
    ]
    return pd.DataFrame(rows, columns=BATCH_PLAN_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_source_review_batch_execution_plan(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _area_plan_row(
    *,
    area: str,
    batch_order: int,
    execution_pass: pd.DataFrame,
    citation_gate: pd.DataFrame,
    checklist_steps: int,
    batch_work_rule_de: str,
    completion_gate_de: str,
    blocked_actions_de: str,
    next_action_de: str,
) -> dict[str, object]:
    area_rows = execution_pass.loc[execution_pass["thesis_area"] == area]
    gate = _gate_row(citation_gate, area)
    return _base_plan_row(
        batch_plan_id=f"batch_plan_{area.lower()}",
        batch_order=batch_order,
        batch_scope=f"{area}_manual_source_review",
        execution_batch=AREA_BATCHES[area],
        thesis_area=area,
        source_review_rows=len(area_rows),
        unique_sources=int(area_rows["source_id"].nunique()),
        method_rows=int((area_rows["item_type"] == "method").sum()),
        interpretation_rows=int((area_rows["item_type"] == "interpretation").sum()),
        external_locator_rows=int((area_rows["access_route"] == "external_locator_review").sum()),
        local_pdf_rows=int((area_rows["access_route"] == "local_pdf_review").sum()),
        pending_citation_rows=int(gate["blocked_pending_citation_rows"]),
        final_ready_rows=int(gate["final_citation_ready_rows"]),
        source_status_change_rows=int(gate["source_status_change_rows"]),
        selected_tables=_unique_join(area_rows["selected_table"]),
        selected_figures=_unique_join(area_rows["selected_figure"]),
        update_checklist_steps=checklist_steps,
        batch_work_rule_de=batch_work_rule_de,
        completion_gate_de=completion_gate_de,
        blocked_actions_de=blocked_actions_de,
        next_action_de=next_action_de,
    )


def _total_plan_row(
    *,
    execution_pass: pd.DataFrame,
    citation_gate: pd.DataFrame,
    checklist_steps: int,
) -> dict[str, object]:
    gate = _gate_row(citation_gate, "TOTAL")
    return _base_plan_row(
        batch_plan_id="batch_plan_total_rebuild_gate",
        batch_order=4,
        batch_scope="TOTAL_rebuild_and_finalgate",
        execution_batch="batch_04_rebuild_and_finalgate",
        thesis_area="TOTAL",
        source_review_rows=len(execution_pass),
        unique_sources=int(execution_pass["source_id"].nunique()),
        method_rows=int((execution_pass["item_type"] == "method").sum()),
        interpretation_rows=int((execution_pass["item_type"] == "interpretation").sum()),
        external_locator_rows=int(
            (execution_pass["access_route"] == "external_locator_review").sum()
        ),
        local_pdf_rows=int((execution_pass["access_route"] == "local_pdf_review").sum()),
        pending_citation_rows=int(gate["blocked_pending_citation_rows"]),
        final_ready_rows=int(gate["final_citation_ready_rows"]),
        source_status_change_rows=int(gate["source_status_change_rows"]),
        selected_tables=_unique_join(execution_pass["selected_table"]),
        selected_figures=_unique_join(execution_pass["selected_figure"]),
        update_checklist_steps=checklist_steps,
        batch_work_rule_de=(
            "Nach H1, H2 und H3 alle erlaubten manuellen Ledger-Felder "
            "preservieren, Ledger, Citation Gate Summary, Batch Plan und Index "
            "regenerieren; danach review_check, commit_plan und Diff-Stat "
            "ausfuehren."
        ),
        completion_gate_de=(
            "Finale Freigabe erst, wenn alle benoetigten rows Page-/Section-Note, "
            "Claim-Support, Blocked-Wording und Citation-Use abgeschlossen haben; "
            "aktuell 23 pending citation rows, 0 final-ready rows und "
            "0 source-status change rows."
        ),
        blocked_actions_de=(
            "Keine finale Zitation, keine Quellenstatus-Hochstufung, keine "
            "Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken, "
            "keine Rohdaten-Prompts, keine Wallet-Adressen, keine Trading-Claims, "
            "keine Profitabilitaetsclaims; spaetere Agentenhilfe nur bounded mit "
            "max 50 rows und llm_audit_log."
        ),
        next_action_de=(
            "Nach manuellen Ledger-Aenderungen Generatoren neu ausfuehren und "
            "erst bei gruenen Gates bounded BA-Prosa aktualisieren."
        ),
    )


def _base_plan_row(
    *,
    batch_plan_id: str,
    batch_order: int,
    batch_scope: str,
    execution_batch: str,
    thesis_area: str,
    source_review_rows: int,
    unique_sources: int,
    method_rows: int,
    interpretation_rows: int,
    external_locator_rows: int,
    local_pdf_rows: int,
    pending_citation_rows: int,
    final_ready_rows: int,
    source_status_change_rows: int,
    selected_tables: str,
    selected_figures: str,
    update_checklist_steps: int,
    batch_work_rule_de: str,
    completion_gate_de: str,
    blocked_actions_de: str,
    next_action_de: str,
) -> dict[str, object]:
    return {
        "batch_plan_id": batch_plan_id,
        "batch_order": batch_order,
        "batch_scope": batch_scope,
        "execution_batch": execution_batch,
        "thesis_area": thesis_area,
        "source_review_rows": source_review_rows,
        "unique_sources": unique_sources,
        "method_rows": method_rows,
        "interpretation_rows": interpretation_rows,
        "external_locator_rows": external_locator_rows,
        "local_pdf_rows": local_pdf_rows,
        "pending_citation_rows": pending_citation_rows,
        "final_ready_rows": final_ready_rows,
        "source_status_change_rows": source_status_change_rows,
        "selected_tables": selected_tables,
        "selected_figures": selected_figures,
        "update_checklist_steps": update_checklist_steps,
        "required_manual_fields_de": MANUAL_FIELDS_DE,
        "batch_work_rule_de": batch_work_rule_de,
        "completion_gate_de": completion_gate_de,
        "blocked_actions_de": blocked_actions_de,
        "next_action_de": next_action_de,
        "ready_for_manual_execution": True,
        "ready_for_final_release": False,
    }


def _validate_batch_plan(
    *,
    batch_plan: pd.DataFrame,
    execution_pass: pd.DataFrame,
    update_checklist: pd.DataFrame,
    citation_gate: pd.DataFrame,
    alignment: pd.DataFrame,
) -> None:
    _require_columns(batch_plan, BATCH_PLAN_COLUMNS, "source-review batch execution plan")
    _validate_inputs(
        execution_pass=execution_pass,
        update_checklist=update_checklist,
        citation_gate=citation_gate,
        alignment=alignment,
    )
    if len(batch_plan) != 4:
        raise ValueError("Source-review batch execution plan must contain 4 rows.")
    if batch_plan["batch_order"].astype(int).tolist() != [1, 2, 3, 4]:
        raise ValueError("Source-review batch execution plan order must be H1, H2, H3, TOTAL.")
    if batch_plan["batch_plan_id"].duplicated().any():
        raise ValueError("Source-review batch execution plan contains duplicate IDs.")
    if not batch_plan["ready_for_manual_execution"].map(_bool_value).all():
        raise ValueError("Source-review batch execution plan must be ready for manual execution.")
    if batch_plan["ready_for_final_release"].map(_bool_value).any():
        raise ValueError("Source-review batch execution plan must not be final-release-ready.")

    h1 = _plan_row(batch_plan, "batch_plan_h1")
    h2 = _plan_row(batch_plan, "batch_plan_h2")
    h3 = _plan_row(batch_plan, "batch_plan_h3")
    total = _plan_row(batch_plan, "batch_plan_total_rebuild_gate")
    expected = {
        "batch_plan_h1": (10, 4, 4, 6, 7, 3, 10, 0, "T2", "F1"),
        "batch_plan_h2": (5, 3, 3, 2, 4, 1, 5, 0, "T3", "F2"),
        "batch_plan_h3": (8, 4, 5, 3, 2, 6, 8, 0, "T4", "F3"),
        "batch_plan_total_rebuild_gate": (23, 9, 12, 11, 13, 10, 23, 0, "T2, T3, T4", "F1, F2, F3"),
    }
    for row in (h1, h2, h3, total):
        expected_values = expected[str(row["batch_plan_id"])]
        actual_values = (
            int(row["source_review_rows"]),
            int(row["unique_sources"]),
            int(row["method_rows"]),
            int(row["interpretation_rows"]),
            int(row["external_locator_rows"]),
            int(row["local_pdf_rows"]),
            int(row["pending_citation_rows"]),
            int(row["final_ready_rows"]),
            str(row["selected_tables"]),
            str(row["selected_figures"]),
        )
        if actual_values != expected_values:
            raise ValueError(
                "Source-review batch execution plan has unexpected counts for "
                f"{row['batch_plan_id']}: {actual_values} != {expected_values}."
            )
        if int(row["source_status_change_rows"]) != 0:
            raise ValueError("Source-review batch execution plan must not include status changes.")
        if int(row["update_checklist_steps"]) != 8:
            raise ValueError("Source-review batch execution plan expects 8 checklist steps.")

    joined = "\n".join(batch_plan.fillna("").astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Source-review batch execution plan must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "page-/section-note",
        "claim-support",
        "blocked-wording",
        "citation-use",
        "kausalclaim-grenze",
        "granger-grenze",
        "wallet-grenze",
        "keine finale zitation",
        "keine quellenstatus-hochstufung",
        "keine runtime-agenten",
        "max 50 rows",
        "llm_audit_log",
        "keine wallet-adressen",
        "keine trading-claims",
        "keine profitabilitaetsclaims",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError(
            "Source-review batch execution plan missing required terms: " + ", ".join(missing)
        )


def _validate_inputs(
    *,
    execution_pass: pd.DataFrame,
    update_checklist: pd.DataFrame,
    citation_gate: pd.DataFrame,
    alignment: pd.DataFrame,
) -> None:
    _require_columns(execution_pass, EXECUTION_REQUIRED_COLUMNS, "manual source-review execution pass")
    _require_columns(update_checklist, CHECKLIST_REQUIRED_COLUMNS, "manual source-review update checklist")
    _require_columns(citation_gate, CITATION_GATE_REQUIRED_COLUMNS, "ledger citation gate summary")
    _require_columns(alignment, ALIGNMENT_REQUIRED_COLUMNS, "decision queue ledger alignment")

    if len(execution_pass) != 23:
        raise ValueError("Source-review batch execution plan expects 23 execution rows.")
    if set(execution_pass["thesis_area"]) != set(CORE_AREAS):
        raise ValueError("Source-review batch execution plan expects H1, H2, and H3 rows.")
    area_counts = execution_pass["thesis_area"].value_counts().to_dict()
    if area_counts.get("H1", 0) != 10 or area_counts.get("H2", 0) != 5 or area_counts.get("H3", 0) != 8:
        raise ValueError("Source-review batch execution plan expects 10 H1, 5 H2, and 8 H3 rows.")
    if int(execution_pass["source_id"].nunique()) != 9:
        raise ValueError("Source-review batch execution plan expects 9 unique sources.")
    if int((execution_pass["item_type"] == "method").sum()) != 12:
        raise ValueError("Source-review batch execution plan expects 12 method rows.")
    if int((execution_pass["item_type"] == "interpretation").sum()) != 11:
        raise ValueError("Source-review batch execution plan expects 11 interpretation rows.")
    if int((execution_pass["access_route"] == "external_locator_review").sum()) != 13:
        raise ValueError("Source-review batch execution plan expects 13 external locator rows.")
    if int((execution_pass["access_route"] == "local_pdf_review").sum()) != 10:
        raise ValueError("Source-review batch execution plan expects 10 local PDF rows.")
    if execution_pass["source_status_change_allowed"].map(_bool_value).any():
        raise ValueError("Source-review batch execution plan must not include source-status changes.")
    if execution_pass["final_citation_ready"].map(_bool_value).any():
        raise ValueError("Source-review batch execution plan expects 0 final-ready execution rows.")

    if len(update_checklist) != 8:
        raise ValueError("Source-review batch execution plan expects 8 update checklist rows.")
    if not update_checklist["ready_for_manual_update"].map(_bool_value).all():
        raise ValueError("Source-review batch execution plan requires manual-update-ready checklist rows.")
    if update_checklist["ready_for_final_citation_release"].map(_bool_value).any():
        raise ValueError("Source-review batch execution plan requires no final-release-ready checklist rows.")

    total_gate = _gate_row(citation_gate, "TOTAL")
    if int(total_gate["ledger_rows"]) != 23 or int(total_gate["unique_sources"]) != 9:
        raise ValueError("Source-review batch execution plan expects TOTAL gate with 23 rows and 9 sources.")
    if int(total_gate["method_rows"]) != 12 or int(total_gate["interpretation_rows"]) != 11:
        raise ValueError("Source-review batch execution plan expects TOTAL gate with 12 method and 11 interpretation rows.")
    if int(total_gate["blocked_pending_citation_rows"]) != 23:
        raise ValueError("Source-review batch execution plan expects 23 pending citation rows.")
    if int(total_gate["final_citation_ready_rows"]) != 0:
        raise ValueError("Source-review batch execution plan expects 0 final-ready rows.")
    if int(total_gate["source_status_change_rows"]) != 0:
        raise ValueError("Source-review batch execution plan expects 0 source-status change rows.")

    if int(alignment["matched_rows"].sum()) != 23:
        raise ValueError("Source-review batch execution plan expects 23 alignment matches.")
    if int(alignment["ledger_rows"].sum()) != 23:
        raise ValueError("Source-review batch execution plan expects 23 aligned ledger rows.")
    if int(alignment["queue_missing_ledger_rows"].sum()) != 0:
        raise ValueError("Source-review batch execution plan alignment has queue rows missing ledger.")
    if int(alignment["ledger_missing_queue_rows"].sum()) != 0:
        raise ValueError("Source-review batch execution plan alignment has ledger rows missing queue.")
    if int(alignment["field_mismatch_rows"].sum()) != 0:
        raise ValueError("Source-review batch execution plan alignment has field mismatches.")


def _render_batch_plan_doc(batch_plan: pd.DataFrame) -> str:
    total = _plan_row(batch_plan, "batch_plan_total_rebuild_gate")
    display = batch_plan[
        [
            "batch_order",
            "execution_batch",
            "thesis_area",
            "source_review_rows",
            "unique_sources",
            "pending_citation_rows",
            "final_ready_rows",
            "selected_tables",
            "selected_figures",
            "completion_gate_de",
            "next_action_de",
        ]
    ]
    return (
        "# Source Review Batch Execution Plan\n\n"
        "Dieser Plan ordnet die 23 offenen H1-H2-H3 Source-Review-Zeilen in "
        "drei manuelle Review-Batches und einen Rebuild-/Finalgate-Batch. Er "
        "liest keine Quelleninhalte, trifft keine Claim-Support-Entscheide, "
        "setzt keine Page-/Section-Notes, promotet keinen Quellenstatus und "
        "erzeugt keine finale Zitation.\n\n"
        "## Counts\n\n"
        f"- Plan rows: {len(batch_plan)}\n"
        f"- Source review rows: {int(total['source_review_rows'])}\n"
        f"- Unique sources: {int(total['unique_sources'])}\n"
        f"- Method rows: {int(total['method_rows'])}\n"
        f"- Interpretation rows: {int(total['interpretation_rows'])}\n"
        f"- External locator rows: {int(total['external_locator_rows'])}\n"
        f"- Local PDF rows: {int(total['local_pdf_rows'])}\n"
        f"- Pending citation rows: {int(total['pending_citation_rows'])}\n"
        f"- Final ready rows: {int(total['final_ready_rows'])}\n"
        f"- Source-status change rows: {int(total['source_status_change_rows'])}\n"
        f"- Update checklist steps: {int(total['update_checklist_steps'])}\n"
        f"- Final release ready rows: {int(batch_plan['ready_for_final_release'].map(_bool_value).sum())}\n\n"
        "## Batch Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Arbeite die Batches in dieser Reihenfolge ab: H1, H2, H3, danach "
        "TOTAL Rebuild und Finalgate. Vor jeder Ledger-Aenderung gilt die "
        "Manual Source Review Update Checklist. Erlaubte manuelle Felder sind "
        f"{MANUAL_FIELDS_DE}. "
        "Alle 23 rows bleiben bis zur manuellen Page-/Section-Note, "
        "Claim-Support-, Blocked-Wording- und Citation-Use-Entscheidung "
        "citation-blocked. Keine finale Zitation, keine "
        "Quellenstatus-Hochstufung, keine Runtime-Agenten, kein MCP, kein "
        "Model Routing, keine Rohdaten-Prompts, keine Wallet-Adressen, keine "
        "Trading-Claims und keine Profitabilitaetsclaims. Spaetere "
        "Agentenhilfe ist nur als missing-field oder to-do-Unterstuetzung mit "
        "max 50 rows, Tests und llm_audit_log zulaessig.\n"
    )


def _gate_row(citation_gate: pd.DataFrame, scope_id: str) -> pd.Series:
    rows = citation_gate.loc[citation_gate["scope_id"] == scope_id]
    if len(rows) != 1:
        raise ValueError(f"Source-review batch execution plan requires one {scope_id} gate row.")
    return rows.iloc[0]


def _plan_row(batch_plan: pd.DataFrame, batch_plan_id: str) -> pd.Series:
    rows = batch_plan.loc[batch_plan["batch_plan_id"] == batch_plan_id]
    if len(rows) != 1:
        raise ValueError(f"Source-review batch execution plan requires one {batch_plan_id} row.")
    return rows.iloc[0]


def _unique_join(values: pd.Series) -> str:
    unique_values = sorted({_clean(value) for value in values if _clean(value)})
    return ", ".join(unique_values)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required source-review batch execution plan input missing: {path}")
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
