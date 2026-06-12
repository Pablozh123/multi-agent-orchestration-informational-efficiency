"""Build a source-gated thesis drafting pass for H1-H2-H3."""

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
DEFAULT_DOCS_DIR = Path("docs/research")

DRAFTING_PASS_OUTPUT = "thesis_h1_h2_h3_source_gated_thesis_drafting_pass.csv"
DRAFTING_PASS_DOC_OUTPUT = "THESIS_H1_H2_H3_SOURCE_GATED_THESIS_DRAFTING_PASS.md"

DRAFTING_PASS_COLUMNS: tuple[str, ...] = (
    "drafting_pass_id",
    "thesis_area",
    "chapter_title_de",
    "draft_sequence_order",
    "draft_section_de",
    "source_gated_writing_pass_id",
    "method_evidence_ids",
    "interpretation_evidence_ids",
    "literature_source_ids",
    "deterministic_artifacts",
    "selected_tables",
    "selected_figures",
    "manual_execution_rows",
    "manual_execution_pending_rows",
    "manual_execution_final_ready_rows",
    "manual_execution_source_ids",
    "manual_execution_evidence_ids",
    "paragraph_seed_de",
    "writer_action_de",
    "source_review_action_de",
    "table_figure_action_de",
    "final_gate_de",
    "blocked_wording_de",
    "ready_for_bounded_draft",
    "ready_for_final_submission",
    "draft_status",
)

CORE_AREAS: tuple[str, ...] = ("H1", "H2", "H3")
SECTION_SEQUENCE: tuple[tuple[str, str], ...] = (
    ("method_result_setup", "Methode und Resultat setzen"),
    ("interpretation_boundary", "Interpretation und Limitation setzen"),
    ("table_figure_integration", "Tabelle und Figur einbauen"),
    ("manual_source_review_execution", "Manual Source Review ausfuehren"),
    ("final_boundary_and_future_agents", "Finalgate und Future-Agent-Grenze setzen"),
)


@dataclass(frozen=True)
class H1H2H3SourceGatedThesisDraftingPassResult:
    """Generated source-gated thesis drafting pass paths and counts."""

    drafting_pass_path: Path
    docs_path: Path
    drafting_rows: int
    h1_rows: int
    h2_rows: int
    h3_rows: int
    manual_execution_rows: int
    final_ready_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "drafting_pass_path": str(self.drafting_pass_path),
            "docs_path": str(self.docs_path),
            "drafting_rows": self.drafting_rows,
            "h1_rows": self.h1_rows,
            "h2_rows": self.h2_rows,
            "h3_rows": self.h3_rows,
            "manual_execution_rows": self.manual_execution_rows,
            "final_ready_rows": self.final_ready_rows,
        }


def generate_h1_h2_h3_source_gated_thesis_drafting_pass(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> H1H2H3SourceGatedThesisDraftingPassResult:
    """Generate the source-gated thesis drafting pass CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    source_gated = _read_csv(results_dir / "thesis_h1_h2_h3_source_gated_writing_pass.csv")
    manual_execution = _read_csv(
        results_dir / "thesis_h1_h2_h3_manual_source_review_execution_pass.csv"
    )

    drafting_pass = build_h1_h2_h3_source_gated_thesis_drafting_pass(
        source_gated=source_gated,
        manual_execution=manual_execution,
    )
    _validate_drafting_pass(drafting_pass, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    drafting_path = results_dir / DRAFTING_PASS_OUTPUT
    docs_path = docs_dir / DRAFTING_PASS_DOC_OUTPUT
    drafting_pass.to_csv(drafting_path, index=False)
    docs_path.write_text(_render_drafting_pass_doc(drafting_pass), encoding="utf-8")

    area_counts = drafting_pass["thesis_area"].value_counts().to_dict()
    return H1H2H3SourceGatedThesisDraftingPassResult(
        drafting_pass_path=drafting_path,
        docs_path=docs_path,
        drafting_rows=len(drafting_pass),
        h1_rows=int(area_counts.get("H1", 0)),
        h2_rows=int(area_counts.get("H2", 0)),
        h3_rows=int(area_counts.get("H3", 0)),
        manual_execution_rows=int(
            manual_execution["execution_id"].astype(str).nunique()
        ),
        final_ready_rows=int(drafting_pass["ready_for_final_submission"].map(_bool_value).sum()),
    )


def build_h1_h2_h3_source_gated_thesis_drafting_pass(
    *,
    source_gated: pd.DataFrame,
    manual_execution: pd.DataFrame,
) -> pd.DataFrame:
    """Return paragraph-level source-gated drafting rows for H1-H2-H3."""

    _require_columns(
        source_gated,
        (
            "writing_pass_id",
            "thesis_area",
            "chapter_title_de",
            "method_evidence_ids",
            "interpretation_evidence_ids",
            "literature_source_ids",
            "deterministic_artifacts",
            "source_coverage_gap_rows",
            "selected_tables",
            "selected_figures",
            "method_paragraph_de",
            "result_paragraph_de",
            "interpretation_paragraph_de",
            "table_figure_paragraph_de",
            "source_gate_paragraph_de",
            "future_agent_boundary_de",
            "blocked_wording_de",
            "writing_pass_status",
            "ready_for_bounded_draft",
            "ready_for_final_submission",
        ),
        "H1-H2-H3 source-gated writing pass",
    )
    _require_columns(
        manual_execution,
        (
            "execution_id",
            "thesis_area",
            "source_id",
            "evidence_id",
            "review_progress_state",
            "final_citation_ready",
            "source_status_change_allowed",
        ),
        "H1-H2-H3 manual source review execution pass",
    )

    rows: list[dict[str, object]] = []
    source_gated_by_area = source_gated.set_index("thesis_area").to_dict(orient="index")
    for area_index, area in enumerate(CORE_AREAS, start=1):
        source_row = source_gated_by_area.get(area)
        if source_row is None:
            raise ValueError(f"Source-gated thesis drafting pass missing area: {area}.")
        manual_rows = manual_execution[manual_execution["thesis_area"] == area].copy()
        if manual_rows.empty:
            raise ValueError(f"Source-gated thesis drafting pass missing manual rows for {area}.")
        if manual_rows["source_status_change_allowed"].map(_bool_value).any():
            raise ValueError(f"Manual execution rows must not allow source-status changes for {area}.")
        manual_count = int(len(manual_rows))
        manual_pending = int(
            (manual_rows["review_progress_state"].astype(str) == "pending_manual_review").sum()
        )
        manual_final_ready = int(manual_rows["final_citation_ready"].map(_bool_value).sum())
        manual_source_ids = _join_unique(manual_rows["source_id"].astype(str).tolist())
        manual_evidence_ids = _join_unique(manual_rows["evidence_id"].astype(str).tolist())

        for section_index, (section_id, section_label) in enumerate(SECTION_SEQUENCE, start=1):
            sequence_order = (area_index - 1) * len(SECTION_SEQUENCE) + section_index
            rows.append(
                {
                    "drafting_pass_id": f"thesis_draft_{area.lower()}_{section_index:02d}_{section_id}",
                    "thesis_area": area,
                    "chapter_title_de": str(source_row["chapter_title_de"]),
                    "draft_sequence_order": sequence_order,
                    "draft_section_de": section_label,
                    "source_gated_writing_pass_id": str(source_row["writing_pass_id"]),
                    "method_evidence_ids": str(source_row["method_evidence_ids"]),
                    "interpretation_evidence_ids": str(source_row["interpretation_evidence_ids"]),
                    "literature_source_ids": str(source_row["literature_source_ids"]),
                    "deterministic_artifacts": str(source_row["deterministic_artifacts"]),
                    "selected_tables": str(source_row["selected_tables"]),
                    "selected_figures": str(source_row["selected_figures"]),
                    "manual_execution_rows": manual_count,
                    "manual_execution_pending_rows": manual_pending,
                    "manual_execution_final_ready_rows": manual_final_ready,
                    "manual_execution_source_ids": manual_source_ids,
                    "manual_execution_evidence_ids": manual_evidence_ids,
                    "paragraph_seed_de": _paragraph_seed(
                        source_row=source_row,
                        section_id=section_id,
                        manual_count=manual_count,
                        manual_pending=manual_pending,
                    ),
                    "writer_action_de": _writer_action(
                        area=area,
                        section_id=section_id,
                        selected_tables=str(source_row["selected_tables"]),
                        selected_figures=str(source_row["selected_figures"]),
                    ),
                    "source_review_action_de": _source_review_action(
                        area=area,
                        manual_count=manual_count,
                        manual_pending=manual_pending,
                        manual_final_ready=manual_final_ready,
                    ),
                    "table_figure_action_de": _table_figure_action(
                        area=area,
                        selected_tables=str(source_row["selected_tables"]),
                        selected_figures=str(source_row["selected_figures"]),
                    ),
                    "final_gate_de": _final_gate(
                        area=area,
                        source_coverage_gap_rows=int(source_row["source_coverage_gap_rows"]),
                        manual_final_ready=manual_final_ready,
                    ),
                    "blocked_wording_de": str(source_row["blocked_wording_de"]),
                    "ready_for_bounded_draft": _bool_value(source_row["ready_for_bounded_draft"]),
                    "ready_for_final_submission": False,
                    "draft_status": "source_gated_thesis_draft_ready_final_source_review_pending",
                }
            )
    return pd.DataFrame(rows, columns=DRAFTING_PASS_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_h1_h2_h3_source_gated_thesis_drafting_pass(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_drafting_pass(drafting_pass: pd.DataFrame, *, repo_root: Path) -> None:
    _require_columns(drafting_pass, DRAFTING_PASS_COLUMNS, "source-gated thesis drafting pass")
    if len(drafting_pass) != 15:
        raise ValueError("Source-gated thesis drafting pass must contain 15 rows.")
    if drafting_pass["drafting_pass_id"].duplicated().any():
        raise ValueError("Source-gated thesis drafting pass contains duplicate IDs.")
    if set(drafting_pass["thesis_area"]) != set(CORE_AREAS):
        raise ValueError("Source-gated thesis drafting pass must cover H1, H2, and H3.")
    expected_order = list(range(1, len(drafting_pass) + 1))
    if drafting_pass["draft_sequence_order"].astype(int).tolist() != expected_order:
        raise ValueError("Source-gated thesis drafting pass has non-sequential order.")
    if not drafting_pass["ready_for_bounded_draft"].map(_bool_value).all():
        raise ValueError("All source-gated thesis drafting rows must be bounded-draft-ready.")
    if drafting_pass["ready_for_final_submission"].map(_bool_value).any():
        raise ValueError("Source-gated thesis drafting rows must not be final-submission-ready.")
    if drafting_pass["manual_execution_rows"].astype(int).le(0).any():
        raise ValueError("Every source-gated thesis drafting row needs manual execution rows.")
    if drafting_pass["manual_execution_final_ready_rows"].astype(int).sum() != 0:
        raise ValueError("Current drafting pass must not claim final citation readiness.")
    for artifact_list in drafting_pass["deterministic_artifacts"].astype(str):
        for artifact in _split_semicolon(artifact_list):
            if not (repo_root / artifact).exists():
                raise FileNotFoundError(f"Source-gated thesis drafting artifact missing: {artifact}")
    for column in (
        "chapter_title_de",
        "draft_section_de",
        "source_gated_writing_pass_id",
        "method_evidence_ids",
        "interpretation_evidence_ids",
        "literature_source_ids",
        "deterministic_artifacts",
        "selected_tables",
        "selected_figures",
        "manual_execution_source_ids",
        "manual_execution_evidence_ids",
        "paragraph_seed_de",
        "writer_action_de",
        "source_review_action_de",
        "table_figure_action_de",
        "final_gate_de",
        "blocked_wording_de",
        "draft_status",
    ):
        if drafting_pass[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Source-gated thesis drafting pass contains empty {column}.")
    joined = "\n".join(drafting_pass.fillna("").astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Source-gated thesis drafting pass must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "source-gated",
        "manual source review",
        "manual source review follow-up overview",
        "overview-/ledger-abgleich",
        "page-/section-note",
        "claim-support",
        "blocked-wording",
        "citation-use",
        "wenige gute tabellen",
        "keine finale zitation",
        "keine quellenstatus-hochstufung",
        "keine runtime-agenten",
        "llm_audit_log",
        "nicht final-submission-ready",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError(
            "Source-gated thesis drafting pass missing required terms: " + ", ".join(missing)
        )
    for area, area_rows in drafting_pass.groupby("thesis_area"):
        gate_text = "\n".join(
            area_rows[["paragraph_seed_de", "source_review_action_de", "final_gate_de"]]
            .astype(str)
            .agg(" ".join, axis=1)
            .tolist()
        ).lower()
        gate_terms = (
            "manual source review follow-up overview",
            "overview-/ledger-abgleich",
            "keine finale zitation",
            "keine quellenstatus-hochstufung",
        )
        missing_gate_terms = [term for term in gate_terms if term not in gate_text]
        if missing_gate_terms:
            raise ValueError(
                f"Source-gated thesis drafting pass missing source-gate terms for {area}: "
                + ", ".join(missing_gate_terms)
            )


def _render_drafting_pass_doc(drafting_pass: pd.DataFrame) -> str:
    area_counts = drafting_pass["thesis_area"].value_counts().to_dict()
    manual_execution_total = int(
        drafting_pass.drop_duplicates("thesis_area")["manual_execution_rows"].astype(int).sum()
    )
    display = drafting_pass[
        [
            "draft_sequence_order",
            "thesis_area",
            "draft_section_de",
            "selected_tables",
            "selected_figures",
            "manual_execution_rows",
            "manual_execution_pending_rows",
            "draft_status",
        ]
    ]
    sections = [
        "# H1-H2-H3 Source-Gated Thesis Drafting Pass\n",
        "Dieser Pass ist eine paragraphenweise BA-Schreibreihenfolge fuer H1, "
        "H2 und H3. Er nutzt nur den bestehenden Source-Gated Writing Pass und "
        "die Manual Source Review Execution-Liste. Er liest keine Quelleninhalte, "
        "berechnet keine Kennzahlen und ersetzt keine finale Source Review. "
        "Der Manual Source Review Follow-up Overview-/Ledger-Abgleich bleibt "
        "in den Review- und Finalgate-Zeilen sichtbar.\n",
        "## Counts\n",
        f"- Drafting rows: {len(drafting_pass)}\n",
        f"- H1 rows: {int(area_counts.get('H1', 0))}\n",
        f"- H2 rows: {int(area_counts.get('H2', 0))}\n",
        f"- H3 rows: {int(area_counts.get('H3', 0))}\n",
        f"- Manual execution rows linked once per chapter: {manual_execution_total}\n",
        "- Final submission ready rows: 0\n",
        "## Drafting Sequence\n",
        _markdown_table(display),
    ]
    for area in CORE_AREAS:
        area_rows = drafting_pass[drafting_pass["thesis_area"] == area].sort_values(
            "draft_sequence_order"
        )
        first = area_rows.iloc[0]
        sections.extend(
            [
                f"## {first['chapter_title_de']}\n",
                f"Methoden: `{first['method_evidence_ids']}`\n",
                f"Interpretationen: `{first['interpretation_evidence_ids']}`\n",
                f"Literatur: `{first['literature_source_ids']}`\n",
                f"Tabellen/Figuren: `{first['selected_tables']}` / `{first['selected_figures']}`\n",
                f"Manual Source Review: {int(first['manual_execution_rows'])} rows, "
                f"{int(first['manual_execution_pending_rows'])} pending, "
                f"{int(first['manual_execution_final_ready_rows'])} final-ready.\n",
            ]
        )
        for row in area_rows.to_dict(orient="records"):
            sections.append(
                f"### {int(row['draft_sequence_order'])}. {row['draft_section_de']}\n\n"
                f"{row['paragraph_seed_de']}\n\n"
                f"Writer action: {row['writer_action_de']}\n\n"
                f"Gate: {row['final_gate_de']}\n"
            )
    sections.extend(
        [
            "## Use Rule\n",
            "Nutze diesen Pass als konkrete Reihenfolge fuer den naechsten "
            "H1-H2-H3 Thesis-Draft. Jede Zeile bleibt source-gated: Evidence "
            "IDs, Literatur-IDs, deterministische Artefakte, wenige gute "
            "Tabellen/Figuren, Manual Source Review, Page-/Section-Note, "
            "Claim-Support, Blocked-Wording, Citation-Use und Manual Source "
            "Review Follow-up Overview-/Ledger-Abgleich bleiben sichtbar. "
            "Keine finale Zitation, keine Quellenstatus-Hochstufung, keine "
            "Rohartefakt-Dumps, keine neuen Kennzahlen, keine Runtime-Agenten, "
            "kein MCP, kein Model Routing, keine LLM-Metriken und keine "
            "Trading-Pfade.\n",
        ]
    )
    return "\n".join(sections)


def _paragraph_seed(
    *,
    source_row: dict[str, object],
    section_id: str,
    manual_count: int,
    manual_pending: int,
) -> str:
    if section_id == "method_result_setup":
        return (
            f"{source_row['method_paragraph_de']} {source_row['result_paragraph_de']} "
            "Dieser Absatz bleibt source-gated und nutzt keine neuen Kennzahlen."
        )
    if section_id == "interpretation_boundary":
        return (
            f"{source_row['interpretation_paragraph_de']} Nicht final-submission-ready: "
            "Die Interpretation bleibt bounded und braucht finale Source Review."
        )
    if section_id == "table_figure_integration":
        return (
            f"{source_row['table_figure_paragraph_de']} Die Ergebnisdarstellung bleibt "
            "auf wenige gute Tabellen/Figuren begrenzt."
        )
    if section_id == "manual_source_review_execution":
        return (
            f"Manual Source Review fuer dieses Kapitel: {manual_count} Execution-Zeilen, "
            f"{manual_pending} pending. Page-/Section-Note, Claim-Support, "
            "Blocked-Wording und Citation-Use muessen manuell gesetzt werden. "
            "Der Manual Source Review Follow-up Overview-/Ledger-Abgleich ist "
            "vor Ledger-Entscheidungen zu pruefen."
        )
    if section_id == "final_boundary_and_future_agents":
        return (
            f"{source_row['source_gate_paragraph_de']} {source_row['future_agent_boundary_de']} "
            "Keine Runtime-Agenten, kein MCP, kein Model Routing und keine LLM-Metriken."
        )
    raise ValueError(f"Unknown drafting section: {section_id}")


def _writer_action(
    *,
    area: str,
    section_id: str,
    selected_tables: str,
    selected_figures: str,
) -> str:
    if section_id == "method_result_setup":
        return (
            f"{area}: Methoden- und Resultatabsatz aus dem Source-Gated Writing Pass "
            "in den BA-Entwurf uebernehmen; Evidence IDs sichtbar halten."
        )
    if section_id == "interpretation_boundary":
        return (
            f"{area}: Interpretation nur bounded formulieren und Limitation direkt "
            "nach dem Resultat platzieren."
        )
    if section_id == "table_figure_integration":
        return (
            f"{area}: Nur Tabelle {selected_tables} und Abbildung {selected_figures} "
            "einbauen; keine Rohartefakt-Dumps."
        )
    if section_id == "manual_source_review_execution":
        return (
            f"{area}: Manual Source Review Execution Pass abarbeiten und "
            "Manual Source Review Follow-up Overview-/Ledger-Abgleich, "
            "Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use erfassen."
        )
    if section_id == "final_boundary_and_future_agents":
        return (
            f"{area}: Finalgate sichtbar lassen und Agenten nur als Future-Work-Grenze "
            "mit llm_audit_log-Vorbedingung erwaehnen."
        )
    raise ValueError(f"Unknown drafting section: {section_id}")


def _source_review_action(
    *,
    area: str,
    manual_count: int,
    manual_pending: int,
    manual_final_ready: int,
) -> str:
    return (
        f"{area}: Manual Source Review hat {manual_count} rows, {manual_pending} pending "
        f"und {manual_final_ready} final-ready. Manual Source Review Follow-up "
        "Overview-/Ledger-Abgleich bleibt vor jeder Entscheidung sichtbar. "
        "Keine finale Zitation und keine Quellenstatus-Hochstufung ohne "
        "vollstaendige manuelle Entscheidung."
    )


def _table_figure_action(*, area: str, selected_tables: str, selected_figures: str) -> str:
    return (
        f"{area}: Ergebnisdarstellung auf {selected_tables}/{selected_figures} begrenzen; "
        "Caption, Artefaktpfad und Limitation gegen Caption Registry pruefen."
    )


def _final_gate(*, area: str, source_coverage_gap_rows: int, manual_final_ready: int) -> str:
    return (
        f"{area}: Source-Coverage-Gaps {source_coverage_gap_rows}; final-ready "
        f"Manual-Execution rows {manual_final_ready}. Bounded Draft ja, aber nicht "
        "final-submission-ready. Manual Source Review Follow-up Overview-/Ledger-"
        "Abgleich vor Citation Gate sichtbar halten. Keine finale Zitation, "
        "keine Rohartefakt-Dumps, keine Runtime-Agenten und keine LLM-Metriken."
    )


def _join_unique(values: Sequence[object]) -> str:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if text and text.lower() != "nan" and text not in seen:
            seen.add(text)
            result.append(text)
    return "; ".join(result)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required source-gated thesis drafting input missing: {path}")
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


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "ja"}


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
