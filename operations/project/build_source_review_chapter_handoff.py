"""Build a chapter-level handoff for H1-H2-H3 source review and drafting."""

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

HANDOFF_OUTPUT = "thesis_source_review_chapter_handoff.csv"
HANDOFF_DOC_OUTPUT = "THESIS_SOURCE_REVIEW_CHAPTER_HANDOFF.md"

HANDOFF_COLUMNS: tuple[str, ...] = (
    "handoff_id",
    "thesis_area",
    "section_id",
    "chapter_title_de",
    "method_evidence_ids",
    "interpretation_evidence_ids",
    "literature_source_ids",
    "deterministic_artifacts",
    "selected_tables",
    "selected_figures",
    "mapped_method_count",
    "mapped_interpretation_count",
    "literature_source_count",
    "source_review_rows",
    "pending_review_rows",
    "final_citation_ready_rows",
    "result_package_items",
    "coverage_status",
    "chapter_write_status",
    "required_source_review_de",
    "thesis_ready_result_de",
    "bounded_interpretation_de",
    "mandatory_limitation_de",
    "blocked_wording_de",
    "next_chapter_action_de",
    "future_agent_boundary_de",
)

CORE_AREAS: tuple[str, ...] = ("H1", "H2", "H3")


@dataclass(frozen=True)
class SourceReviewChapterHandoffResult:
    """Generated chapter handoff paths and counts."""

    handoff_path: Path
    docs_path: Path
    handoff_rows: int
    source_review_rows: int
    pending_review_rows: int
    final_citation_ready_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "handoff_path": str(self.handoff_path),
            "docs_path": str(self.docs_path),
            "handoff_rows": self.handoff_rows,
            "source_review_rows": self.source_review_rows,
            "pending_review_rows": self.pending_review_rows,
            "final_citation_ready_rows": self.final_citation_ready_rows,
        }


def generate_source_review_chapter_handoff(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> SourceReviewChapterHandoffResult:
    """Generate the chapter handoff CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    core_sections = _read_csv(results_dir / "thesis_h1_h2_h3_core_sections.csv")
    traceability = _read_csv(results_dir / "thesis_method_interpretation_traceability.csv")
    package = _read_csv(results_dir / "thesis_result_package_traceability.csv")
    ledger = _read_csv(results_dir / "thesis_source_review_progress_ledger.csv")
    protocol = _read_csv(results_dir / "thesis_source_review_progress_protocol.csv")
    manual_followup_overview = _read_csv(
        results_dir / "thesis_manual_source_review_followup_overview.csv"
    )

    handoff = build_source_review_chapter_handoff(
        core_sections=core_sections,
        traceability=traceability,
        package=package,
        ledger=ledger,
        protocol=protocol,
        manual_followup_overview=manual_followup_overview,
    )
    _validate_handoff(handoff)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    handoff_path = results_dir / HANDOFF_OUTPUT
    docs_path = docs_dir / HANDOFF_DOC_OUTPUT
    handoff.to_csv(handoff_path, index=False)
    docs_path.write_text(_render_handoff_doc(handoff), encoding="utf-8")

    return SourceReviewChapterHandoffResult(
        handoff_path=handoff_path,
        docs_path=docs_path,
        handoff_rows=len(handoff),
        source_review_rows=int(handoff["source_review_rows"].sum()),
        pending_review_rows=int(handoff["pending_review_rows"].sum()),
        final_citation_ready_rows=int(handoff["final_citation_ready_rows"].sum()),
    )


def build_source_review_chapter_handoff(
    *,
    core_sections: pd.DataFrame,
    traceability: pd.DataFrame,
    package: pd.DataFrame,
    ledger: pd.DataFrame,
    protocol: pd.DataFrame,
    manual_followup_overview: pd.DataFrame,
) -> pd.DataFrame:
    """Return one handoff row per empirical core chapter."""

    _require_columns(
        core_sections,
        (
            "section_id",
            "hypothesis",
            "chapter_title_de",
            "method_evidence_ids",
            "interpretation_evidence_ids",
            "literature_source_ids",
            "deterministic_artifacts",
            "selected_tables",
            "selected_figures",
            "thesis_ready_result_de",
            "bounded_interpretation_de",
            "mandatory_limitation_de",
            "blocked_wording_de",
        ),
        "H1-H2-H3 core sections",
    )
    _require_columns(
        traceability,
        (
            "evidence_id",
            "item_type",
            "thesis_readiness",
            "primary_artifact_exists",
            "literature_source_count",
            "known_literature_source_count",
            "limitation_present",
            "traceability_status",
        ),
        "method interpretation traceability",
    )
    _require_columns(
        package,
        ("package_id", "package_type", "include_in_core_package", "package_traceability_status"),
        "result package traceability",
    )
    _require_columns(
        ledger,
        (
            "thesis_area",
            "review_progress_state",
            "source_status_change_allowed",
            "final_citation_ready",
        ),
        "source review progress ledger",
    )
    _require_columns(protocol, ("protocol_id", "current_state"), "source review progress protocol")
    _require_columns(
        manual_followup_overview,
        (
            "slice_id",
            "review_rows",
            "pending_rows",
            "final_ready_rows",
            "followup_doc",
            "followup_csv",
        ),
        "manual source-review follow-up overview",
    )

    evidence_by_id = traceability.set_index("evidence_id").to_dict(orient="index")
    package_by_id = package.set_index("package_id").to_dict(orient="index")
    protocol_by_id = protocol.set_index("protocol_id").to_dict(orient="index")
    overview_by_area = manual_followup_overview.set_index("slice_id").to_dict(orient="index")
    future_agent_state = str(
        protocol_by_id.get("protocol_06_future_agent_upgrade_boundary", {}).get(
            "current_state", "future_documentation_only"
        )
    )

    rows: list[dict[str, object]] = []
    for core in core_sections.sort_values("hypothesis").to_dict(orient="records"):
        area = str(core["hypothesis"])
        method_ids = _split_semicolon(str(core["method_evidence_ids"]))
        interpretation_ids = _split_semicolon(str(core["interpretation_evidence_ids"]))
        literature_ids = _split_semicolon(str(core["literature_source_ids"]))
        table_ids = _split_semicolon(str(core["selected_tables"]))
        figure_ids = _split_semicolon(str(core["selected_figures"]))
        package_ids = [*table_ids, *figure_ids]
        _validate_evidence_ids(
            evidence_by_id=evidence_by_id,
            evidence_ids=method_ids,
            expected_type="method",
            require_limitation=False,
            area=area,
        )
        _validate_evidence_ids(
            evidence_by_id=evidence_by_id,
            evidence_ids=interpretation_ids,
            expected_type="interpretation",
            require_limitation=True,
            area=area,
        )
        _validate_package_ids(package_by_id=package_by_id, package_ids=package_ids, area=area)

        ledger_rows = ledger[ledger["thesis_area"] == area]
        if ledger_rows.empty:
            raise ValueError(f"Chapter handoff missing source-review ledger rows for {area}.")
        if ledger_rows["source_status_change_allowed"].map(_bool_value).any():
            raise ValueError(f"Chapter handoff must not allow source-status changes for {area}.")
        source_review_rows = int(len(ledger_rows))
        pending_review_rows = int((ledger_rows["review_progress_state"] == "pending_manual_review").sum())
        final_ready_rows = int(ledger_rows["final_citation_ready"].map(_bool_value).sum())
        overview_row = overview_by_area.get(area)
        if overview_row is None:
            raise ValueError(f"Chapter handoff missing manual follow-up overview row for {area}.")
        _validate_overview_match(
            area=area,
            overview_row=overview_row,
            source_review_rows=source_review_rows,
            pending_review_rows=pending_review_rows,
            final_ready_rows=final_ready_rows,
        )
        coverage_status = _coverage_status(
            method_ids=method_ids,
            interpretation_ids=interpretation_ids,
            literature_ids=literature_ids,
            package_ids=package_ids,
        )
        chapter_write_status = (
            "bounded_draft_ready_final_source_review_pending"
            if final_ready_rows < source_review_rows
            else "final_citation_review_complete"
        )
        rows.append(
            {
                "handoff_id": f"handoff_{area.lower()}_source_review_chapter",
                "thesis_area": area,
                "section_id": str(core["section_id"]),
                "chapter_title_de": str(core["chapter_title_de"]),
                "method_evidence_ids": "; ".join(method_ids),
                "interpretation_evidence_ids": "; ".join(interpretation_ids),
                "literature_source_ids": "; ".join(literature_ids),
                "deterministic_artifacts": str(core["deterministic_artifacts"]),
                "selected_tables": "; ".join(table_ids),
                "selected_figures": "; ".join(figure_ids),
                "mapped_method_count": len(method_ids),
                "mapped_interpretation_count": len(interpretation_ids),
                "literature_source_count": len(literature_ids),
                "source_review_rows": source_review_rows,
                "pending_review_rows": pending_review_rows,
                "final_citation_ready_rows": final_ready_rows,
                "result_package_items": "; ".join(package_ids),
                "coverage_status": coverage_status,
                "chapter_write_status": chapter_write_status,
                "required_source_review_de": (
                    f"{area}: {source_review_rows} Source-Review-Zeilen im Ledger "
                    "und in der Manual Source Review Follow-up Overview; "
                    f"{pending_review_rows} pending; {final_ready_rows} final-ready. "
                    "Keine finale Zitation ohne abgeschlossene manuelle Review. "
                    f"Detailstart: {overview_row['followup_doc']} und "
                    f"{overview_row['followup_csv']}. "
                    "Vor finaler Zitation Page-/Section-Note, Claim-Support, "
                    "Blocked-Wording und Citation-Use je Quelle dokumentieren."
                ),
                "thesis_ready_result_de": str(core["thesis_ready_result_de"]),
                "bounded_interpretation_de": str(core["bounded_interpretation_de"]),
                "mandatory_limitation_de": str(core["mandatory_limitation_de"]),
                "blocked_wording_de": str(core["blocked_wording_de"]),
                "next_chapter_action_de": (
                    f"{area}: Kapitel mit Evidence IDs, Literatur IDs, "
                    f"{'; '.join(package_ids)} und sichtbarem Source-Review-Gate "
                    "schreiben; vorher Manual Source Review Follow-up Overview "
                    "pruefen; keine Rohartefakt-Dumps."
                ),
                "future_agent_boundary_de": (
                    f"Agentenstatus bleibt `{future_agent_state}`: keine Runtime-Agenten, "
                    "kein MCP, kein Model Routing, keine LLM-Metriken; spaeter nur "
                    "mit separatem Goal, Tests, bounded inputs, max 50 rows und llm_audit_log."
                ),
            }
        )
    return pd.DataFrame(rows, columns=HANDOFF_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_source_review_chapter_handoff(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_handoff(handoff: pd.DataFrame) -> None:
    _require_columns(handoff, HANDOFF_COLUMNS, "source review chapter handoff")
    if len(handoff) != 3:
        raise ValueError("Source review chapter handoff must contain exactly 3 rows.")
    if set(handoff["thesis_area"]) != set(CORE_AREAS):
        raise ValueError("Source review chapter handoff must cover H1, H2, and H3.")
    if handoff["handoff_id"].duplicated().any():
        raise ValueError("Source review chapter handoff contains duplicate handoff_id values.")
    for column in HANDOFF_COLUMNS:
        if handoff[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Source review chapter handoff contains empty {column}.")
    if not handoff["mapped_method_count"].astype(int).gt(0).all():
        raise ValueError("Every chapter handoff row needs at least one mapped method.")
    if not handoff["mapped_interpretation_count"].astype(int).gt(0).all():
        raise ValueError("Every chapter handoff row needs at least one mapped interpretation.")
    if not handoff["literature_source_count"].astype(int).gt(0).all():
        raise ValueError("Every chapter handoff row needs at least one literature source.")
    if not handoff["source_review_rows"].astype(int).gt(0).all():
        raise ValueError("Every chapter handoff row needs source-review rows.")
    if not handoff["coverage_status"].eq("covered_artifact_source_package_ready").all():
        raise ValueError("Every chapter handoff row must be coverage-ready.")
    joined = "\n".join(handoff.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Source review chapter handoff must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "evidence ids",
        "literatur ids",
        "source-review-gate",
        "manual source review follow-up overview",
        "keine rohartefakt-dumps",
        "keine runtime-agenten",
        "llm_audit_log",
        "max 50 rows",
        "keine finale zitation",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Source review chapter handoff missing required terms: " + ", ".join(missing))


def _validate_overview_match(
    *,
    area: str,
    overview_row: dict[str, object],
    source_review_rows: int,
    pending_review_rows: int,
    final_ready_rows: int,
) -> None:
    overview_review_rows = int(overview_row["review_rows"])
    overview_pending_rows = int(overview_row["pending_rows"])
    overview_final_ready_rows = int(overview_row["final_ready_rows"])
    if overview_review_rows != source_review_rows:
        raise ValueError(f"{area} overview review rows do not match ledger rows.")
    if overview_pending_rows != pending_review_rows:
        raise ValueError(f"{area} overview pending rows do not match ledger rows.")
    if overview_final_ready_rows != final_ready_rows:
        raise ValueError(f"{area} overview final-ready rows do not match ledger rows.")


def _render_handoff_doc(handoff: pd.DataFrame) -> str:
    return (
        "# Source Review Chapter Handoff\n\n"
        "Dieses Handoff uebersetzt das Source Review Progress Protocol auf die "
        "drei empirischen BA-Kapitel H1, H2 und H3. Es zeigt pro Kapitel die "
        "gemappten Methoden, Interpretationen, Literaturquellen, deterministischen "
        "Artefakte, wenigen Tabellen/Figuren und offenen Source-Review-Zeilen. "
        "Die Manual Source Review Follow-up Overview bleibt pro Kapitel der "
        "Pre-Ledger-Kontrollpunkt fuer Detailstart, Pending-Zeilen und finale "
        "Zitierblockade. "
        "Es liest keine Quelleninhalte, promotet keinen Quellenstatus und "
        "aktiviert keine Runtime-Agenten.\n\n"
        "## Counts\n\n"
        f"- Chapter handoff rows: {len(handoff)}\n"
        f"- Source-review rows: {int(handoff['source_review_rows'].sum())}\n"
        f"- Pending review rows: {int(handoff['pending_review_rows'].sum())}\n"
        f"- Final citation ready rows: {int(handoff['final_citation_ready_rows'].sum())}\n"
        f"- Selected result items: {_join_unique(handoff['result_package_items'])}\n\n"
        "## Handoff Rows\n\n"
        + _markdown_table(
            handoff[
                [
                    "handoff_id",
                    "thesis_area",
                    "method_evidence_ids",
                    "interpretation_evidence_ids",
                    "literature_source_ids",
                    "result_package_items",
                    "source_review_rows",
                    "pending_review_rows",
                    "chapter_write_status",
                    "next_chapter_action_de",
                ]
            ]
        )
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze dieses Handoff beim Schreiben der empirischen Kapitel. Jede "
        "Methode und Interpretation bleibt an ein deterministisches Artefakt, "
        "Literatur IDs, Limitationen und ein Source-Review-Gate gebunden. "
        "Resultate werden als wenige Tabellen/Figuren eingebaut, nicht als "
        "Rohartefakt-Dumps. Keine finale Zitation, keine Quellenstatus-"
        "Hochstufung, keine Runtime-Agenten, kein MCP, kein Model Routing, "
        "keine LLM-Metriken und keine Trading-Pfade.\n"
    )


def _validate_evidence_ids(
    *,
    evidence_by_id: dict[str, dict[str, object]],
    evidence_ids: list[str],
    expected_type: str,
    require_limitation: bool,
    area: str,
) -> None:
    if not evidence_ids:
        raise ValueError(f"{area} has no {expected_type} evidence ids.")
    for evidence_id in evidence_ids:
        evidence = evidence_by_id.get(evidence_id)
        if evidence is None:
            raise ValueError(f"{area} evidence id missing traceability row: {evidence_id}")
        if str(evidence["item_type"]) != expected_type:
            raise ValueError(f"{area} evidence id has wrong item_type: {evidence_id}")
        if str(evidence["thesis_readiness"]) != "thesis_facing_ready":
            raise ValueError(f"{area} evidence id is not thesis-facing ready: {evidence_id}")
        if not _bool_value(evidence["primary_artifact_exists"]):
            raise ValueError(f"{area} evidence id lacks deterministic artifact: {evidence_id}")
        if int(evidence["literature_source_count"]) <= 0:
            raise ValueError(f"{area} evidence id lacks literature source: {evidence_id}")
        if int(evidence["known_literature_source_count"]) <= 0:
            raise ValueError(f"{area} evidence id lacks known literature source: {evidence_id}")
        if require_limitation and not _bool_value(evidence["limitation_present"]):
            raise ValueError(f"{area} interpretation lacks limitation: {evidence_id}")
        if str(evidence["traceability_status"]) == "traceability_gap":
            raise ValueError(f"{area} evidence id has traceability gap: {evidence_id}")


def _validate_package_ids(
    *,
    package_by_id: dict[str, dict[str, object]],
    package_ids: list[str],
    area: str,
) -> None:
    if not package_ids:
        raise ValueError(f"{area} has no selected result package items.")
    for package_id in package_ids:
        package = package_by_id.get(package_id)
        if package is None:
            raise ValueError(f"{area} package id missing traceability row: {package_id}")
        if not _bool_value(package["include_in_core_package"]):
            raise ValueError(f"{area} package id is not in core package: {package_id}")
        if "gap" in str(package["package_traceability_status"]).lower():
            raise ValueError(f"{area} package id has traceability gap: {package_id}")


def _coverage_status(
    *,
    method_ids: list[str],
    interpretation_ids: list[str],
    literature_ids: list[str],
    package_ids: list[str],
) -> str:
    if method_ids and interpretation_ids and literature_ids and package_ids:
        return "covered_artifact_source_package_ready"
    return "coverage_gap"


def _join_unique(series: pd.Series) -> str:
    values: list[str] = []
    for value in series.astype(str):
        values.extend(_split_semicolon(value))
    return "; ".join(dict.fromkeys(values))


def _split_semicolon(value: str) -> list[str]:
    if value.lower() == "nan":
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "ja"}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required source review chapter handoff input missing: {path}")
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
