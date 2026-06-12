"""Build a compact H2 source-review decision queue."""

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

QUEUE_OUTPUT = "thesis_h2_source_review_decision_queue.csv"
QUEUE_DOC_OUTPUT = "THESIS_H2_SOURCE_REVIEW_DECISION_QUEUE.md"

QUEUE_COLUMNS: tuple[str, ...] = (
    "decision_id",
    "decision_order",
    "source_id",
    "source_title",
    "source_status",
    "source_priority_order",
    "evidence_id",
    "item_type",
    "decision_focus_de",
    "access_route",
    "local_file_type",
    "local_file_exists",
    "structure_inventory_status",
    "review_source_locator",
    "deterministic_artifact",
    "primary_artifact_exists",
    "selected_table",
    "selected_figure",
    "coverage_status",
    "final_citation_readiness",
    "current_review_status",
    "required_manual_decision_fields_de",
    "manual_review_action_de",
    "allowed_claim_scope_de",
    "blocked_wording_check_de",
    "h2_causal_boundary_de",
    "chapter_write_use_de",
    "agent_assist_boundary_de",
    "source_status_change_allowed",
    "final_citation_ready",
    "queue_status",
)


@dataclass(frozen=True)
class H2SourceReviewDecisionQueueResult:
    """Generated H2 decision queue paths and counts."""

    queue_path: Path
    docs_path: Path
    queue_rows: int
    unique_sources: int
    method_rows: int
    interpretation_rows: int
    local_pdf_rows: int
    external_rows: int
    final_ready_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "queue_path": str(self.queue_path),
            "docs_path": str(self.docs_path),
            "queue_rows": self.queue_rows,
            "unique_sources": self.unique_sources,
            "method_rows": self.method_rows,
            "interpretation_rows": self.interpretation_rows,
            "local_pdf_rows": self.local_pdf_rows,
            "external_rows": self.external_rows,
            "final_ready_rows": self.final_ready_rows,
        }


def generate_h2_source_review_decision_queue(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> H2SourceReviewDecisionQueueResult:
    """Generate the H2 source-review decision queue CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    h2_followup = _read_csv(results_dir / "thesis_h2_manual_source_review_followup.csv")
    source_structure = _read_csv(results_dir / "thesis_source_structure_inventory.csv")
    source_coverage = _read_csv(results_dir / "thesis_method_interpretation_source_coverage.csv")

    queue = build_h2_source_review_decision_queue(
        h2_followup=h2_followup,
        source_structure=source_structure,
        source_coverage=source_coverage,
    )
    _validate_queue(queue, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    queue_path = results_dir / QUEUE_OUTPUT
    docs_path = docs_dir / QUEUE_DOC_OUTPUT
    queue.to_csv(queue_path, index=False)
    docs_path.write_text(_render_queue_doc(queue), encoding="utf-8")

    return H2SourceReviewDecisionQueueResult(
        queue_path=queue_path,
        docs_path=docs_path,
        queue_rows=len(queue),
        unique_sources=int(queue["source_id"].nunique()),
        method_rows=int((queue["item_type"] == "method").sum()),
        interpretation_rows=int((queue["item_type"] == "interpretation").sum()),
        local_pdf_rows=int((queue["access_route"] == "local_pdf_review").sum()),
        external_rows=int((queue["access_route"] == "external_locator_review").sum()),
        final_ready_rows=int(queue["final_citation_ready"].map(_bool_value).sum()),
    )


def build_h2_source_review_decision_queue(
    *,
    h2_followup: pd.DataFrame,
    source_structure: pd.DataFrame,
    source_coverage: pd.DataFrame,
) -> pd.DataFrame:
    """Return a compact H2 source-review decision queue."""

    _require_columns(
        h2_followup,
        (
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
            "allowed_claim_scope_de",
            "blocked_wording_check_de",
            "final_citation_ready",
            "source_status_change_allowed",
        ),
        "H2 manual source review follow-up",
    )
    _require_columns(
        source_structure,
        (
            "source_id",
            "local_file_type",
            "local_file_exists",
            "structure_inventory_status",
            "manual_review_instruction_de",
        ),
        "source structure inventory",
    )
    _require_columns(
        source_coverage,
        (
            "source_id",
            "evidence_id",
            "thesis_area",
            "coverage_status",
            "final_citation_readiness",
            "primary_artifact_exists",
        ),
        "method interpretation source coverage",
    )

    structure_by_source = source_structure.set_index("source_id").to_dict(orient="index")
    coverage_by_pair = {
        (str(row["source_id"]), str(row["evidence_id"])): row
        for row in source_coverage.to_dict(orient="records")
        if str(row.get("thesis_area", "")) == "H2"
    }

    rows: list[dict[str, object]] = []
    for row in h2_followup.sort_values("review_order").to_dict(orient="records"):
        source_id = str(row["source_id"])
        evidence_id = str(row["evidence_id"])
        structure = structure_by_source.get(source_id, {})
        coverage = coverage_by_pair.get((source_id, evidence_id), {})
        item_type = str(row["item_type"])
        rows.append(
            {
                "decision_id": f"h2_decision_{int(row['review_order']):02d}_{source_id}__{evidence_id}",
                "decision_order": int(row["review_order"]),
                "source_id": source_id,
                "source_title": str(row["source_title"]),
                "source_status": str(row["source_status"]),
                "source_priority_order": int(row["source_priority_order"]),
                "evidence_id": evidence_id,
                "item_type": item_type,
                "decision_focus_de": _decision_focus(evidence_id=evidence_id, item_type=item_type),
                "access_route": str(row["access_route"]),
                "local_file_type": str(structure.get("local_file_type", "unknown")),
                "local_file_exists": _bool_value(structure.get("local_file_exists", False)),
                "structure_inventory_status": str(
                    structure.get("structure_inventory_status", "missing_structure_inventory")
                ),
                "review_source_locator": str(row["review_source_locator"]),
                "deterministic_artifact": str(row["deterministic_artifact"]),
                "primary_artifact_exists": _bool_value(
                    coverage.get("primary_artifact_exists", True)
                ),
                "selected_table": str(row["selected_table"]),
                "selected_figure": str(row["selected_figure"]),
                "coverage_status": str(
                    coverage.get("coverage_status", "source_mapped_final_review_pending")
                ),
                "final_citation_readiness": str(
                    coverage.get(
                        "final_citation_readiness",
                        "needs_full_source_review_before_final_citation",
                    )
                ),
                "current_review_status": str(row["current_review_status"]),
                "required_manual_decision_fields_de": (
                    "Page-/Section-Note; Claim-Support; Blocked-Wording; "
                    "Citation-Use; Kausalclaim-Grenze; Reviewer-Kommentar."
                ),
                "manual_review_action_de": _manual_review_action(
                    access_route=str(row["access_route"]),
                    locator_task=str(row["manual_locator_task_de"]),
                ),
                "allowed_claim_scope_de": str(row["allowed_claim_scope_de"]),
                "blocked_wording_check_de": str(row["blocked_wording_check_de"]),
                "h2_causal_boundary_de": (
                    "H2 darf nur als taegliche Event-Window-Evidenz formuliert "
                    "werden: keine Intraday-Geschwindigkeitsaussage, keine "
                    "kausale Ereigniswirkung, keine post-hoc Ereignisauswahl."
                ),
                "chapter_write_use_de": _chapter_write_use(
                    evidence_id=evidence_id,
                    item_type=item_type,
                ),
                "agent_assist_boundary_de": (
                    "Spaetere Agentenhilfe darf nur fehlende Felder markieren; "
                    "keine Quelleninhalte bewerten, keine Kausalclaims lockern, "
                    "keine Zitation freigeben, keine Kennzahlen berechnen, "
                    "max 50 rows und llm_audit_log."
                ),
                "source_status_change_allowed": False,
                "final_citation_ready": False,
                "queue_status": "pending_manual_h2_source_review",
            }
        )

    return pd.DataFrame(rows, columns=QUEUE_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_h2_source_review_decision_queue(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _decision_focus(*, evidence_id: str, item_type: str) -> str:
    if item_type == "method":
        return "Methodenanker: Quelle gegen H2 Event-Window-Design und Ereigniskuration pruefen."
    if evidence_id == "interpretation_h2_daily_response":
        return "Interpretationsgrenze: sichtbare Tagesbewegung ohne Intraday- oder Kausalclaim pruefen."
    return "H2 Entscheidungsgrenze manuell gegen Evidence ID pruefen."


def _manual_review_action(*, access_route: str, locator_task: str) -> str:
    if access_route == "local_pdf_review":
        return (
            "Lokales PDF manuell oeffnen; relevante Seite oder Abschnitt notieren; "
            "danach Claim-Support, Blocked-Wording, Citation-Use und "
            f"Kausalclaim-Grenze setzen. Locator-Hinweis: {locator_task}"
        )
    return (
        "Externe DOI/JSTOR/URL manuell oeffnen; relevante Seite oder Abschnitt "
        "notieren; danach Claim-Support, Blocked-Wording, Citation-Use und "
        f"Kausalclaim-Grenze setzen. Locator-Hinweis: {locator_task}"
    )


def _chapter_write_use(*, evidence_id: str, item_type: str) -> str:
    if item_type == "method":
        return (
            "Nach manueller Review als H2-Methodenanker fuer vorkuratierte "
            "Ereignisse und fixe Tagesfenster verwenden; Ergebniswert bleibt "
            "im deterministischen Artefakt."
        )
    if evidence_id == "interpretation_h2_daily_response":
        return (
            "Nach manueller Review fuer sichtbare Tagesbewegungen um kuratierte "
            "oeffentliche Ereignisse nutzen; keine Intraday-Reaktion oder "
            "kausale Ereigniswirkung formulieren."
        )
    return "Nach manueller Review nur im passenden H2-Abschnitt verwenden."


def _validate_queue(queue: pd.DataFrame, *, repo_root: Path) -> None:
    _require_columns(queue, QUEUE_COLUMNS, "H2 source-review decision queue")
    if queue["decision_id"].duplicated().any():
        raise ValueError("H2 decision queue contains duplicate decision_id values.")
    if queue["decision_order"].tolist() != list(range(1, len(queue) + 1)):
        raise ValueError("H2 decision queue order must be contiguous.")
    if len(queue) != 5:
        raise ValueError(f"H2 decision queue expected 5 rows, found {len(queue)}.")
    if queue["source_id"].nunique() != 3:
        raise ValueError("H2 decision queue must cover exactly three H2 sources.")
    if set(queue["item_type"]) != {"method", "interpretation"}:
        raise ValueError("H2 decision queue must cover method and interpretation rows.")
    if queue["selected_table"].nunique() != 1 or queue["selected_table"].iloc[0] != "T3":
        raise ValueError("H2 decision queue must stay bound to selected table T3.")
    if queue["selected_figure"].nunique() != 1 or queue["selected_figure"].iloc[0] != "F2":
        raise ValueError("H2 decision queue must stay bound to selected figure F2.")
    if int((queue["item_type"] == "method").sum()) != 3:
        raise ValueError("H2 decision queue expected 3 method rows.")
    if int((queue["item_type"] == "interpretation").sum()) != 2:
        raise ValueError("H2 decision queue expected 2 interpretation rows.")
    if queue["final_citation_ready"].map(_bool_value).any():
        raise ValueError("H2 decision queue must not mark rows final-citation-ready.")
    if queue["source_status_change_allowed"].map(_bool_value).any():
        raise ValueError("H2 decision queue must not allow source-status changes.")
    if not queue["primary_artifact_exists"].map(_bool_value).all():
        raise ValueError("H2 decision queue contains missing deterministic artifacts.")
    joined = "\n".join(queue.astype(str).agg(" ".join, axis=1).tolist())
    required_terms = (
        "Page-/Section-Note",
        "Claim-Support",
        "Blocked-Wording",
        "Citation-Use",
        "Kausalclaim-Grenze",
        "llm_audit_log",
        "max 50 rows",
        "keine Kennzahlen",
        "keine Zitation freigeben",
        "keine Intraday",
        "keine Kausal",
    )
    missing_terms = [term for term in required_terms if term not in joined]
    if missing_terms:
        raise ValueError("H2 decision queue missing required terms: " + ", ".join(missing_terms))
    if chr(223) in joined:
        raise ValueError("H2 decision queue contains German sharp-s.")
    for artifact in queue["deterministic_artifact"].astype(str).unique():
        _required_file(repo_root / artifact)


def _render_queue_doc(queue: pd.DataFrame) -> str:
    display = queue[
        [
            "decision_order",
            "source_id",
            "evidence_id",
            "item_type",
            "access_route",
            "decision_focus_de",
            "queue_status",
        ]
    ]
    return (
        "# H2 Source Review Decision Queue\n\n"
        "Dieses Artefakt verdichtet die H2 Source Review auf eine konkrete "
        "Entscheidungsqueue. Es liest keine Quelleninhalte, setzt keine "
        "Page-/Section-Notes, trifft keinen Claim-Support-Entscheid und "
        "promotet keinen Quellenstatus.\n\n"
        "## Counts\n\n"
        f"- H2 decision rows: {len(queue)}\n"
        f"- Unique H2 sources: {queue['source_id'].nunique()}\n"
        f"- Method rows: {(queue['item_type'] == 'method').sum()}\n"
        f"- Interpretation rows: {(queue['item_type'] == 'interpretation').sum()}\n"
        f"- External locator rows: {(queue['access_route'] == 'external_locator_review').sum()}\n"
        f"- Local PDF rows: {(queue['access_route'] == 'local_pdf_review').sum()}\n"
        f"- Final citation ready rows: {queue['final_citation_ready'].map(_bool_value).sum()}\n\n"
        "## Decision Queue\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Arbeite die Queue in `decision_order` ab. Fuer jede Zeile muss ein "
        "Mensch die Quelle oeffnen und Page-/Section-Note, Claim-Support, "
        "Blocked-Wording, Citation-Use, Kausalclaim-Grenze und "
        "Reviewer-Kommentar erfassen. Bis diese Felder belegt sind, bleibt H2 "
        "final blockiert: keine finale Zitation, keine Quellenstatus-Hochstufung, "
        "keine Rohartefakt-Dumps, keine Runtime-Agenten, kein MCP, kein Model "
        "Routing, keine LLM-Metriken und keine Trading-Pfade.\n\n"
        "## H2 Boundary\n\n"
        "H2 darf nur als taegliche Event-Window-Evidenz ueber vorkuratierte "
        "oeffentliche Ereignisse und fixe Fenster formuliert werden. Die Queue "
        "blockiert Intraday-Geschwindigkeitsaussagen, Kausalclaims und "
        "post-hoc Ereignisauswahl.\n\n"
        "## Future Agent Boundary\n\n"
        "Spaetere Agenten duerfen nur fehlende Felder markieren oder "
        "Evidence-ID, Quelle und Artefakt spiegeln. Sie duerfen keine "
        "Quelleninhalte bewerten, keine Seitenzahlen erfinden, keine "
        "Kausalclaim-Grenze lockern, keine Zitation freigeben und keine "
        "Kennzahlen berechnen. Jede spaetere Nutzung braucht ein separates Goal, "
        "bounded inputs mit max 50 rows, Tests und `llm_audit_log`.\n"
    )


def _markdown_table(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in frame.to_dict(orient="records"):
        values = [str(row[column]).replace("\n", " ") for column in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def _require_columns(frame: pd.DataFrame, columns: tuple[str, ...], label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def _required_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Required H2 decision queue artifact missing: {path}")


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required H2 decision queue input missing: {path}")
    return pd.read_csv(path)


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"true", "1", "yes", "y"}


def _resolve_under(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


if __name__ == "__main__":
    raise SystemExit(main())
