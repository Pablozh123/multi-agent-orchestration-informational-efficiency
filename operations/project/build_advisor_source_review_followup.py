"""Build the advisor-feedback and source-review follow-up plan."""

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

FOLLOWUP_OUTPUT = "thesis_advisor_source_review_followup.csv"
FOLLOWUP_DOC_OUTPUT = "THESIS_ADVISOR_SOURCE_REVIEW_FOLLOWUP.md"

FOLLOWUP_COLUMNS: tuple[str, ...] = (
    "followup_id",
    "followup_order",
    "workstream_de",
    "trigger_de",
    "input_artifacts",
    "current_evidence_de",
    "advisor_feedback_status",
    "source_review_rows",
    "source_review_pending_rows",
    "final_ready_rows",
    "bounded_draft_allowed",
    "final_submission_ready",
    "required_next_action_de",
    "done_when_de",
    "guardrail_de",
)


@dataclass(frozen=True)
class AdvisorSourceReviewFollowupResult:
    """Generated advisor/source-review follow-up paths and counts."""

    followup_path: Path
    docs_path: Path
    followup_rows: int
    manual_source_review_rows: int
    pending_source_review_rows: int
    final_ready_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "followup_path": str(self.followup_path),
            "docs_path": str(self.docs_path),
            "followup_rows": self.followup_rows,
            "manual_source_review_rows": self.manual_source_review_rows,
            "pending_source_review_rows": self.pending_source_review_rows,
            "final_ready_rows": self.final_ready_rows,
        }


def generate_advisor_source_review_followup(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> AdvisorSourceReviewFollowupResult:
    """Generate the follow-up CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    feedback = _read_csv(results_dir / "thesis_advisor_feedback_integration_checklist.csv")
    execution = _read_csv(results_dir / "thesis_h1_h2_h3_manual_source_review_execution_pass.csv")
    final_gates = _read_csv(results_dir / "thesis_final_gate_board.csv")
    result_package = _read_csv(results_dir / "thesis_result_package_traceability.csv")
    agent_upgrade = _read_csv(results_dir / "thesis_agent_pipeline_upgrade_plan.csv")
    manual_followup_overview = _read_csv(
        results_dir / "thesis_manual_source_review_followup_overview.csv"
    )

    followup = build_advisor_source_review_followup(
        feedback=feedback,
        execution=execution,
        final_gates=final_gates,
        result_package=result_package,
        agent_upgrade=agent_upgrade,
        manual_followup_overview=manual_followup_overview,
    )
    _validate_followup(followup, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    followup_path = results_dir / FOLLOWUP_OUTPUT
    docs_path = docs_dir / FOLLOWUP_DOC_OUTPUT
    followup.to_csv(followup_path, index=False)
    docs_path.write_text(_render_followup_doc(followup), encoding="utf-8")

    totals = _manual_totals(execution)
    return AdvisorSourceReviewFollowupResult(
        followup_path=followup_path,
        docs_path=docs_path,
        followup_rows=len(followup),
        manual_source_review_rows=totals["rows"],
        pending_source_review_rows=totals["pending"],
        final_ready_rows=totals["final_ready"],
    )


def build_advisor_source_review_followup(
    *,
    feedback: pd.DataFrame,
    execution: pd.DataFrame,
    final_gates: pd.DataFrame,
    result_package: pd.DataFrame,
    agent_upgrade: pd.DataFrame,
    manual_followup_overview: pd.DataFrame,
) -> pd.DataFrame:
    """Return the ordered follow-up plan after advisor handoff."""

    _require_columns(
        feedback,
        (
            "advisor_question_id",
            "topic",
            "feedback_status",
            "required_evidence_check_de",
            "small_commit_scope_de",
            "final_gate_de",
            "guardrail_de",
        ),
        "advisor feedback integration checklist",
    )
    _require_columns(
        execution,
        (
            "thesis_area",
            "current_review_status",
            "final_citation_ready",
            "ready_for_bounded_draft",
            "ready_for_final_submission",
            "source_status_change_allowed",
        ),
        "H1-H2-H3 manual source review execution pass",
    )
    _require_columns(
        final_gates,
        (
            "gate_area",
            "draft_use_allowed",
            "final_submission_ready",
            "blocking_count",
            "required_next_action_de",
        ),
        "thesis final gate board",
    )
    _require_columns(
        result_package,
        (
            "package_type",
            "include_in_core_package",
            "package_traceability_status",
        ),
        "result package traceability",
    )
    _require_columns(agent_upgrade, ("current_status",), "agent pipeline upgrade plan")
    _require_columns(
        manual_followup_overview,
        (
            "slice_id",
            "review_rows",
            "unique_sources",
            "pending_rows",
            "final_ready_rows",
            "manual_gate_de",
            "guardrail_de",
        ),
        "manual source-review follow-up overview",
    )

    feedback_summary = _feedback_summary(feedback)
    manual_by_area = _manual_by_area(execution)
    manual_totals = _manual_totals(execution)
    overview_summary = _overview_summary(manual_followup_overview)
    package_summary = _package_summary(result_package)
    final_gate_summary = _final_gate_summary(final_gates)
    agent_summary = _agent_summary(agent_upgrade)

    rows = [
        _followup_row(
            followup_id="followup_01_capture_advisor_feedback",
            followup_order=1,
            workstream_de="Dozentenfeedback erfassen",
            trigger_de="Nach Betreuung oder schriftlicher Rueckmeldung.",
            input_artifacts=(
                "docs/project/DOZENTEN_FEEDBACK_LOG.md; "
                "docs/project/DOZENTEN_FEEDBACK_INTEGRATION_CHECKLIST.md; "
                "data/results/thesis_advisor_feedback_integration_checklist.csv"
            ),
            current_evidence_de=(
                f"Feedback-Integration: {feedback_summary['rows']} Rows; "
                f"pending: {feedback_summary['pending_rows']}; kleine Commit-Scopes: "
                f"{feedback_summary['small_commit_scope_rows']}."
            ),
            advisor_feedback_status=feedback_summary["status_label"],
            source_review_rows=0,
            source_review_pending_rows=0,
            final_ready_rows=0,
            bounded_draft_allowed=True,
            final_submission_ready=False,
            required_next_action_de=(
                "Dozentenantwort in das Feedback-Log eintragen und genau einen "
                "passenden kleinen Integrations-Scope waehlen."
            ),
            done_when_de=(
                "Feedback-Zeile enthaelt Entscheidung, resultierende Aktion und "
                "keinen Scope-Ausbau."
            ),
            guardrail_de=(
                "Keine neuen empirischen Claims, kein Review-Access, keine "
                "Runtime-Agenten und keine Rohartefakt-Dumps aus Feedback ableiten."
            ),
        ),
        _followup_row(
            followup_id="followup_02_confirm_source_review_depth",
            followup_order=2,
            workstream_de="Source-Review-Tiefe festlegen",
            trigger_de="Wenn der Dozent die Review-Tiefe oder Prioritaeten bestaetigt.",
            input_artifacts=(
                "docs/project/THESIS_SOURCE_REVIEW_PROGRESS_PROTOCOL.md; "
                "docs/project/THESIS_MANUAL_SOURCE_REVIEW_FOLLOWUP_OVERVIEW.md; "
                "data/results/thesis_manual_source_review_followup_overview.csv; "
                "docs/project/THESIS_FINAL_GATE_BOARD.md; "
                "data/results/thesis_h1_h2_h3_manual_source_review_execution_pass.csv"
            ),
            current_evidence_de=(
                f"Manual Source Review: {manual_totals['rows']} Rows; "
                f"pending: {manual_totals['pending']}; final-ready: "
                f"{manual_totals['final_ready']}; Quellenstatus-Aenderungen erlaubt: "
                f"{manual_totals['source_status_change_allowed']}. Manual Source "
                "Review Follow-up Overview: "
                f"{overview_summary['slice_rows']} Slices; "
                f"{overview_summary['review_rows']} offene H1-H2-H3 Review-Zeilen; "
                f"{manual_totals['unique_sources']} eindeutige Quellen; "
                f"{overview_summary['pending_rows']} pending; "
                f"{overview_summary['final_ready_rows']} final-ready."
            ),
            advisor_feedback_status=feedback_summary["status_label"],
            source_review_rows=manual_totals["rows"],
            source_review_pending_rows=manual_totals["pending"],
            final_ready_rows=manual_totals["final_ready"],
            bounded_draft_allowed=True,
            final_submission_ready=False,
            required_next_action_de=(
                "Review-Tiefe gegen Source Review Protocol und Final Gate Board "
                "festlegen, ohne Quellenstatus automatisch hochzustufen."
            ),
            done_when_de=(
                "Priorisierte H1-H2-H3 Review-Reihenfolge ist bestaetigt und "
                "die Manual Source Review Follow-up Overview bleibt als "
                "kompakter Kontrollpunkt sichtbar."
            ),
            guardrail_de=(
                "Keine finale Zitation, keine Quellenstatus-Hochstufung und keine "
                "Candidate-Quelle fuer thesis-facing Claims."
            ),
        ),
        _chapter_followup_row(3, "H1", manual_by_area, feedback_summary["status_label"]),
        _chapter_followup_row(4, "H2", manual_by_area, feedback_summary["status_label"]),
        _chapter_followup_row(5, "H3", manual_by_area, feedback_summary["status_label"]),
        _followup_row(
            followup_id="followup_06_update_bounded_chapter_draft",
            followup_order=6,
            workstream_de="Bounded H1-H2-H3 Draft aktualisieren",
            trigger_de="Nach Feedback und waehrend Manual Source Review fortschreitet.",
            input_artifacts=(
                "docs/research/THESIS_CHAPTER_DRAFT.md; "
                "docs/research/THESIS_TABLE_FIGURE_CAPTIONS.md; "
                "data/results/thesis_result_package_traceability.csv"
            ),
            current_evidence_de=(
                f"Kernpaket: {package_summary['core_tables']} Tabellen und "
                f"{package_summary['core_figures']} Figuren; Package gaps: "
                f"{package_summary['package_gaps']}."
            ),
            advisor_feedback_status=feedback_summary["status_label"],
            source_review_rows=manual_totals["rows"],
            source_review_pending_rows=manual_totals["pending"],
            final_ready_rows=manual_totals["final_ready"],
            bounded_draft_allowed=True,
            final_submission_ready=False,
            required_next_action_de=(
                "Nur erlaubtes, source-gated Wording und wenige gute Tabellen/"
                "Figuren in den BA-Draft uebernehmen."
            ),
            done_when_de=(
                "H1-H2-H3 Draft nennt Evidence IDs, Artefakte, Limitationen, "
                "Tabelle/Figur und Source-Review-Gate je Abschnitt."
            ),
            guardrail_de=(
                "Keine neuen Kennzahlen, keine Rohartefakt-Dumps, keine "
                "Universal-, Intraday-, Kausalitaets- oder Profitabilitaetsclaims."
            ),
        ),
        _followup_row(
            followup_id="followup_07_recheck_final_gates",
            followup_order=7,
            workstream_de="Final-Gates erneut pruefen",
            trigger_de="Nach jedem Draft- oder Source-Review-Slice.",
            input_artifacts=(
                "docs/project/THESIS_FINAL_GATE_BOARD.md; "
                "data/results/thesis_final_gate_board.csv; STATUS.md; "
                "docs/project/WORK_LOG.md"
            ),
            current_evidence_de=(
                f"Final Gate Board: {final_gate_summary['rows']} Rows; "
                f"final-ready: {final_gate_summary['final_ready_rows']}; "
                f"final-blocked: {final_gate_summary['final_blocked_rows']}; "
                f"blocking count total: {final_gate_summary['blocking_total']}."
            ),
            advisor_feedback_status=feedback_summary["status_label"],
            source_review_rows=manual_totals["rows"],
            source_review_pending_rows=manual_totals["pending"],
            final_ready_rows=manual_totals["final_ready"],
            bounded_draft_allowed=True,
            final_submission_ready=False,
            required_next_action_de=(
                "Source Review, Swiss Source-/Citation-Gate, DOCX-Render-QA, "
                "review_check und commit_plan vor jedem Abschlussclaim erneut laufen lassen."
            ),
            done_when_de=(
                "Alle verpflichtenden Projektchecks sind gruen und offene Finalgates "
                "werden nicht versteckt."
            ),
            guardrail_de=(
                "Keine finale Abgabebereitschaft behaupten, solange Source Review, "
                "Swiss-Gate oder DOCX-Render-QA offen sind."
            ),
        ),
        _followup_row(
            followup_id="followup_08_keep_agents_future_work",
            followup_order=8,
            workstream_de="Agenten nur als Future Work halten",
            trigger_de="Erst nach stabilem H1-H2-H3 Draft und separater Freigabe.",
            input_artifacts=(
                "docs/research/THESIS_AGENT_PIPELINE_UPGRADE_PLAN.md; "
                "docs/project/THESIS_AGENT_PIPELINE_CONTROL_AUDIT.md; "
                "data/results/thesis_agent_pipeline_upgrade_plan.csv"
            ),
            current_evidence_de=(
                f"Agent Upgrade Rows: {agent_summary['rows']}; active: "
                f"{agent_summary['active_rows']}; inactive/deferred: "
                f"{agent_summary['inactive_rows']}."
            ),
            advisor_feedback_status=feedback_summary["status_label"],
            source_review_rows=0,
            source_review_pending_rows=0,
            final_ready_rows=0,
            bounded_draft_allowed=True,
            final_submission_ready=True,
            required_next_action_de=(
                "Agentenverbesserungen nur dokumentieren; eine Aktivierung braucht "
                "spaeter ein separates Goal, Tests, bounded inputs und llm_audit_log."
            ),
            done_when_de="Future-Work-Abschnitt bleibt kurz, geprueft und inaktiv.",
            guardrail_de=(
                "Keine Runtime-Agenten, kein MCP, kein Model Routing, keine "
                "LLM-Metriken, kein Rohdatenzugriff und keine Trading-Pfade."
            ),
        ),
    ]
    return pd.DataFrame(rows, columns=FOLLOWUP_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_advisor_source_review_followup(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _chapter_followup_row(
    order: int,
    thesis_area: str,
    manual_by_area: dict[str, dict[str, int]],
    feedback_status: str,
) -> dict[str, object]:
    summary = manual_by_area[thesis_area]
    return _followup_row(
        followup_id=f"followup_{order:02d}_{thesis_area.lower()}_manual_source_review",
        followup_order=order,
        workstream_de=f"{thesis_area} Manual Source Review ausfuehren",
        trigger_de=f"Nach bestaetigter Review-Tiefe fuer {thesis_area}.",
        input_artifacts=(
            "docs/project/THESIS_H1_H2_H3_MANUAL_SOURCE_REVIEW_EXECUTION_PASS.md; "
            "docs/project/THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md; "
            "data/results/thesis_h1_h2_h3_manual_source_review_execution_pass.csv"
        ),
        current_evidence_de=(
            f"{thesis_area}: {summary['rows']} Manual Source Review Rows; "
            f"pending: {summary['pending']}; final-ready: {summary['final_ready']}; "
            f"bounded-draft-ready: {summary['bounded_ready']}; "
            f"final-submission-ready: {summary['final_submission_ready']}."
        ),
        advisor_feedback_status=feedback_status,
        source_review_rows=summary["rows"],
        source_review_pending_rows=summary["pending"],
        final_ready_rows=summary["final_ready"],
        bounded_draft_allowed=True,
        final_submission_ready=False,
        required_next_action_de=(
            f"{thesis_area}: Quelle oeffnen, Page-/Section-Note, Claim-Support, "
            "Blocked-Wording und Citation-Use im Ledger erfassen."
        ),
        done_when_de=(
            f"{thesis_area}: jede Review-Zeile hat eine manuelle Entscheidung, "
            "keine blockierte Formulierung und ein klares Citation-Use-Gate."
        ),
        guardrail_de=(
            "Keine Quellenstatus-Hochstufung, keine finale Zitation, keine "
            "automatischen Page Notes und keine thesis-facing Claims ohne "
            "manuelle Entscheidung."
        ),
    )


def _feedback_summary(feedback: pd.DataFrame) -> dict[str, int | str]:
    pending_rows = int((feedback["feedback_status"] == "pending_advisor_feedback").sum())
    unique_statuses = sorted(set(feedback["feedback_status"].astype(str)))
    return {
        "rows": int(len(feedback)),
        "pending_rows": pending_rows,
        "small_commit_scope_rows": int(feedback["small_commit_scope_de"].astype(str).str.len().gt(0).sum()),
        "status_label": "; ".join(unique_statuses),
    }


def _manual_by_area(execution: pd.DataFrame) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for thesis_area, rows in execution.groupby("thesis_area", sort=True):
        result[str(thesis_area)] = {
            "rows": int(len(rows)),
            "pending": int((rows["current_review_status"] == "pending_manual_review").sum()),
            "final_ready": int(rows["final_citation_ready"].map(_bool_value).sum()),
            "bounded_ready": int(rows["ready_for_bounded_draft"].map(_bool_value).sum()),
            "final_submission_ready": int(rows["ready_for_final_submission"].map(_bool_value).sum()),
        }
    missing = sorted({"H1", "H2", "H3"}.difference(result))
    if missing:
        raise ValueError("Manual source review execution pass missing thesis areas: " + ", ".join(missing))
    return result


def _manual_totals(execution: pd.DataFrame) -> dict[str, int]:
    _require_columns(execution, ("source_id",), "H1-H2-H3 manual source review execution pass")
    return {
        "rows": int(len(execution)),
        "unique_sources": int(execution["source_id"].nunique()),
        "pending": int((execution["current_review_status"] == "pending_manual_review").sum()),
        "final_ready": int(execution["final_citation_ready"].map(_bool_value).sum()),
        "source_status_change_allowed": int(
            execution["source_status_change_allowed"].map(_bool_value).sum()
        ),
    }


def _overview_summary(manual_followup_overview: pd.DataFrame) -> dict[str, int]:
    return {
        "slice_rows": int(len(manual_followup_overview)),
        "review_rows": int(manual_followup_overview["review_rows"].astype(int).sum()),
        "pending_rows": int(manual_followup_overview["pending_rows"].astype(int).sum()),
        "final_ready_rows": int(manual_followup_overview["final_ready_rows"].astype(int).sum()),
    }


def _package_summary(result_package: pd.DataFrame) -> dict[str, int]:
    core_package = result_package[result_package["include_in_core_package"].map(_bool_value)]
    return {
        "core_tables": int((core_package["package_type"] == "table").sum()),
        "core_figures": int((core_package["package_type"] == "figure").sum()),
        "package_gaps": int(
            result_package["package_traceability_status"]
            .astype(str)
            .str.contains("gap", case=False, na=False)
            .sum()
        ),
    }


def _final_gate_summary(final_gates: pd.DataFrame) -> dict[str, int]:
    final_ready = final_gates["final_submission_ready"].map(_bool_value)
    return {
        "rows": int(len(final_gates)),
        "final_ready_rows": int(final_ready.sum()),
        "final_blocked_rows": int((~final_ready).sum()),
        "blocking_total": int(pd.to_numeric(final_gates["blocking_count"], errors="coerce").fillna(0).sum()),
    }


def _agent_summary(agent_upgrade: pd.DataFrame) -> dict[str, int]:
    allowed_statuses = {
        "future_documentation_only",
        "future_deferred",
        "deferred_future_work_only",
    }
    statuses = agent_upgrade["current_status"].astype(str).str.strip()
    active_rows = int((~statuses.isin(allowed_statuses)).sum())
    return {
        "rows": int(len(agent_upgrade)),
        "active_rows": active_rows,
        "inactive_rows": int(len(agent_upgrade) - active_rows),
    }


def _followup_row(
    *,
    followup_id: str,
    followup_order: int,
    workstream_de: str,
    trigger_de: str,
    input_artifacts: str,
    current_evidence_de: str,
    advisor_feedback_status: str,
    source_review_rows: int,
    source_review_pending_rows: int,
    final_ready_rows: int,
    bounded_draft_allowed: bool,
    final_submission_ready: bool,
    required_next_action_de: str,
    done_when_de: str,
    guardrail_de: str,
) -> dict[str, object]:
    return {
        "followup_id": followup_id,
        "followup_order": followup_order,
        "workstream_de": workstream_de,
        "trigger_de": trigger_de,
        "input_artifacts": input_artifacts,
        "current_evidence_de": current_evidence_de,
        "advisor_feedback_status": advisor_feedback_status,
        "source_review_rows": source_review_rows,
        "source_review_pending_rows": source_review_pending_rows,
        "final_ready_rows": final_ready_rows,
        "bounded_draft_allowed": bounded_draft_allowed,
        "final_submission_ready": final_submission_ready,
        "required_next_action_de": required_next_action_de,
        "done_when_de": done_when_de,
        "guardrail_de": guardrail_de,
    }


def _validate_followup(followup: pd.DataFrame, *, repo_root: Path) -> None:
    _require_columns(followup, FOLLOWUP_COLUMNS, "advisor source-review follow-up")
    if len(followup) != 8:
        raise ValueError("Advisor source-review follow-up must contain exactly 8 rows.")
    if followup["followup_id"].duplicated().any():
        raise ValueError("Advisor source-review follow-up contains duplicate followup_id values.")
    if sorted(followup["followup_order"].astype(int).tolist()) != list(range(1, 9)):
        raise ValueError("Advisor source-review follow-up orders must be 1..8.")
    for column in FOLLOWUP_COLUMNS:
        if followup[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Advisor source-review follow-up contains empty {column}.")
    for column in ("source_review_rows", "source_review_pending_rows", "final_ready_rows"):
        if pd.to_numeric(followup[column], errors="coerce").fillna(-1).lt(0).any():
            raise ValueError(f"Advisor source-review follow-up contains negative {column}.")
    for artifacts in followup["input_artifacts"].astype(str):
        for artifact in _split_semicolon(artifacts):
            if not (repo_root / artifact).exists():
                raise FileNotFoundError(f"Advisor source-review follow-up artifact missing: {artifact}")
    joined = "\n".join(followup.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Advisor source-review follow-up must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "pending_advisor_feedback",
        "source review",
        "manual source review follow-up overview",
        "23 offene h1-h2-h3 review-zeilen",
        "page-/section-note",
        "claim-support",
        "blocked-wording",
        "citation-use",
        "wenige gute tabellen/figuren",
        "keine quellenstatus-hochstufung",
        "keine finale zitation",
        "review-access",
        "keine runtime-agenten",
        "llm_audit_log",
        "keine rohartefakt-dumps",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Advisor source-review follow-up missing required terms: " + ", ".join(missing))


def _render_followup_doc(followup: pd.DataFrame) -> str:
    total_source_rows = int(followup["source_review_rows"].max())
    total_pending_rows = int(followup["source_review_pending_rows"].max())
    total_final_ready = int(followup["final_ready_rows"].max())
    final_ready_rows = int(followup["final_submission_ready"].map(_bool_value).sum())
    display = followup[
        [
            "followup_order",
            "followup_id",
            "workstream_de",
            "current_evidence_de",
            "required_next_action_de",
            "guardrail_de",
        ]
    ]
    return (
        "# Advisor Source Review Follow-up\n\n"
        "Dieses Artefakt ordnet die naechsten Schritte nach Dozenten-Handoff: "
        "Feedback erfassen, Source-Review-Tiefe festlegen, H1-H2-H3 manuell "
        "reviewen, bounded Draft aktualisieren, Final-Gates erneut pruefen und "
        "Agenten nur als Future Work halten. Die Manual Source Review "
        "Follow-up Overview bleibt der kompakte Kontrollpunkt fuer die 23 "
        "offenen H1-H2-H3 Review-Zeilen. Es erzeugt keine neuen "
        "empirischen Resultate und interpretiert keine Quelleninhalte.\n\n"
        "## Counts\n\n"
        f"- Follow-up rows: {len(followup)}\n"
        f"- Manual Source Review rows: {total_source_rows}\n"
        f"- Manual Source Review pending rows: {total_pending_rows}\n"
        f"- Manual Source Review final-ready rows: {total_final_ready}\n"
        f"- Final-submission-ready follow-up rows: {final_ready_rows}\n\n"
        "## Follow-up Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Nach dem Dozentenfeedback zuerst das Feedback-Log ausfuellen. Danach "
        "die Manual Source Review Follow-up Overview pruefen und Source Review "
        "manuell je H1-H2-H3-Zeile ausfuehren: Page-/Section-Note, "
        "Claim-Support, Blocked-Wording und Citation-Use erfassen. Erst danach "
        "bounded Draft und wenige gute Tabellen/Figuren aktualisieren. Finale "
        "Zitation, Quellenstatus-Hochstufung, finale Abgabebereitschaft, "
        "Review-Access, Runtime-Agenten, MCP, Model Routing, LLM-Metriken, "
        "Rohartefakt-Dumps und Trading-Pfade bleiben blockiert, bis die "
        "jeweiligen Gates belegt geschlossen sind.\n"
    )


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "ja"}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required advisor source-review follow-up input missing: {path}")
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
