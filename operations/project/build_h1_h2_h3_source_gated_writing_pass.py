"""Build source-gated H1-H2-H3 writing pass sections."""

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

WRITING_PASS_OUTPUT = "thesis_h1_h2_h3_source_gated_writing_pass.csv"
WRITING_PASS_DOC_OUTPUT = "THESIS_H1_H2_H3_SOURCE_GATED_WRITING_PASS.md"

WRITING_PASS_COLUMNS: tuple[str, ...] = (
    "writing_pass_id",
    "thesis_area",
    "chapter_title_de",
    "method_evidence_ids",
    "interpretation_evidence_ids",
    "literature_source_ids",
    "deterministic_artifacts",
    "source_coverage_links",
    "source_coverage_unique_sources",
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
    "full_chapter_draft_de",
    "writing_pass_status",
    "ready_for_bounded_draft",
    "ready_for_final_submission",
)

STEP_TO_COLUMN: dict[str, str] = {
    "method_setup": "method_paragraph_de",
    "result_statement": "result_paragraph_de",
    "interpretation_boundary": "interpretation_paragraph_de",
    "table_figure_integration": "table_figure_paragraph_de",
    "source_review_and_citation_gate": "source_gate_paragraph_de",
    "future_agent_boundary": "future_agent_boundary_de",
}


@dataclass(frozen=True)
class H1H2H3SourceGatedWritingPassResult:
    """Generated source-gated writing pass paths and counts."""

    writing_pass_path: Path
    docs_path: Path
    writing_pass_rows: int
    bounded_ready_rows: int
    final_ready_rows: int
    source_coverage_gap_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "writing_pass_path": str(self.writing_pass_path),
            "docs_path": str(self.docs_path),
            "writing_pass_rows": self.writing_pass_rows,
            "bounded_ready_rows": self.bounded_ready_rows,
            "final_ready_rows": self.final_ready_rows,
            "source_coverage_gap_rows": self.source_coverage_gap_rows,
        }


def generate_h1_h2_h3_source_gated_writing_pass(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> H1H2H3SourceGatedWritingPassResult:
    """Generate source-gated H1-H2-H3 writing pass CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    bounded_draft = _read_csv(results_dir / "thesis_h1_h2_h3_bounded_chapter_draft.csv")
    writing_pass = build_h1_h2_h3_source_gated_writing_pass(bounded_draft=bounded_draft)
    _validate_writing_pass(writing_pass, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    writing_pass_path = results_dir / WRITING_PASS_OUTPUT
    docs_path = docs_dir / WRITING_PASS_DOC_OUTPUT
    writing_pass.to_csv(writing_pass_path, index=False)
    docs_path.write_text(_render_writing_pass_doc(writing_pass), encoding="utf-8")

    return H1H2H3SourceGatedWritingPassResult(
        writing_pass_path=writing_pass_path,
        docs_path=docs_path,
        writing_pass_rows=len(writing_pass),
        bounded_ready_rows=int(writing_pass["ready_for_bounded_draft"].map(_bool_value).sum()),
        final_ready_rows=int(writing_pass["ready_for_final_submission"].map(_bool_value).sum()),
        source_coverage_gap_rows=int(writing_pass["source_coverage_gap_rows"].astype(int).sum()),
    )


def build_h1_h2_h3_source_gated_writing_pass(*, bounded_draft: pd.DataFrame) -> pd.DataFrame:
    """Return one source-gated writing row for each H1-H2-H3 chapter."""

    _require_columns(
        bounded_draft,
        (
            "thesis_area",
            "chapter_title_de",
            "draft_order",
            "draft_step",
            "method_evidence_ids",
            "interpretation_evidence_ids",
            "literature_source_ids",
            "deterministic_artifacts",
            "source_coverage_links",
            "source_coverage_unique_sources",
            "source_coverage_gap_rows",
            "selected_tables",
            "selected_figures",
            "chapter_paragraph_de",
            "blocked_wording_de",
            "ready_for_bounded_draft",
            "ready_for_final_submission",
        ),
        "H1-H2-H3 bounded chapter draft",
    )
    rows: list[dict[str, object]] = []
    for area in ("H1", "H2", "H3"):
        area_rows = bounded_draft[bounded_draft["thesis_area"] == area].sort_values("draft_order")
        if len(area_rows) != 6:
            raise ValueError(f"Source-gated writing pass requires 6 bounded draft rows for {area}.")
        paragraphs = _paragraphs_by_step(area_rows)
        first = area_rows.iloc[0]
        full_chapter = _full_chapter_text(area=area, first=first, paragraphs=paragraphs)
        rows.append(
            {
                "writing_pass_id": f"writing_pass_{area.lower()}_source_gated",
                "thesis_area": area,
                "chapter_title_de": str(first["chapter_title_de"]),
                "method_evidence_ids": str(first["method_evidence_ids"]),
                "interpretation_evidence_ids": str(first["interpretation_evidence_ids"]),
                "literature_source_ids": str(first["literature_source_ids"]),
                "deterministic_artifacts": str(first["deterministic_artifacts"]),
                "source_coverage_links": int(first["source_coverage_links"]),
                "source_coverage_unique_sources": int(first["source_coverage_unique_sources"]),
                "source_coverage_gap_rows": int(first["source_coverage_gap_rows"]),
                "selected_tables": str(first["selected_tables"]),
                "selected_figures": str(first["selected_figures"]),
                "method_paragraph_de": paragraphs["method_paragraph_de"],
                "result_paragraph_de": paragraphs["result_paragraph_de"],
                "interpretation_paragraph_de": paragraphs["interpretation_paragraph_de"],
                "table_figure_paragraph_de": paragraphs["table_figure_paragraph_de"],
                "source_gate_paragraph_de": paragraphs["source_gate_paragraph_de"],
                "future_agent_boundary_de": paragraphs["future_agent_boundary_de"],
                "blocked_wording_de": _join_unique(area_rows["blocked_wording_de"].astype(str).tolist()),
                "full_chapter_draft_de": full_chapter,
                "writing_pass_status": "source_gated_bounded_draft_ready_final_source_review_pending",
                "ready_for_bounded_draft": bool(
                    area_rows["ready_for_bounded_draft"].map(_bool_value).all()
                ),
                "ready_for_final_submission": bool(
                    area_rows["ready_for_final_submission"].map(_bool_value).all()
                ),
            }
        )
    return pd.DataFrame(rows, columns=WRITING_PASS_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_h1_h2_h3_source_gated_writing_pass(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _paragraphs_by_step(area_rows: pd.DataFrame) -> dict[str, str]:
    paragraphs: dict[str, str] = {}
    for row in area_rows.to_dict(orient="records"):
        step = str(row["draft_step"])
        column = STEP_TO_COLUMN.get(step)
        if column is None:
            raise ValueError(f"Unsupported writing pass draft step: {step}")
        paragraphs[column] = _clean_sentence_spacing(str(row["chapter_paragraph_de"]))
    missing = [column for column in STEP_TO_COLUMN.values() if column not in paragraphs]
    if missing:
        raise ValueError("Source-gated writing pass missing paragraphs: " + ", ".join(missing))
    return paragraphs


def _full_chapter_text(
    *,
    area: str,
    first: pd.Series,
    paragraphs: dict[str, str],
) -> str:
    return "\n\n".join(
        [
            str(first["chapter_title_de"]),
            "Source-gated Schreibpass: Der Abschnitt bleibt an Source Coverage, "
            "deterministische Artefakte, Manual Source Review Follow-up "
            "Overview-/Ledger-Abgleich und finale Source-Review-Gates gebunden.",
            paragraphs["method_paragraph_de"],
            paragraphs["result_paragraph_de"],
            paragraphs["interpretation_paragraph_de"],
            paragraphs["table_figure_paragraph_de"],
            paragraphs["source_gate_paragraph_de"],
            paragraphs["future_agent_boundary_de"],
            (
                "Schreibgate: Dieser Abschnitt ist bounded-draft-ready, aber "
                "nicht final-submission-ready. Finale Zitation bleibt vom "
                "Source Review mit Manual Source Review Follow-up Overview, "
                "Overview-/Ledger-Abgleich und Page-/Section-Notes abhaengig."
            ),
        ]
    )


def _validate_writing_pass(writing_pass: pd.DataFrame, *, repo_root: Path) -> None:
    _require_columns(writing_pass, WRITING_PASS_COLUMNS, "H1-H2-H3 source-gated writing pass")
    if len(writing_pass) != 3:
        raise ValueError("H1-H2-H3 source-gated writing pass must contain exactly 3 rows.")
    if writing_pass["writing_pass_id"].duplicated().any():
        raise ValueError("H1-H2-H3 source-gated writing pass contains duplicate IDs.")
    if set(writing_pass["thesis_area"]) != {"H1", "H2", "H3"}:
        raise ValueError("H1-H2-H3 source-gated writing pass must cover H1, H2, and H3.")
    if not writing_pass["ready_for_bounded_draft"].map(_bool_value).all():
        raise ValueError("All source-gated writing pass rows must be bounded-draft-ready.")
    if writing_pass["ready_for_final_submission"].map(_bool_value).any():
        raise ValueError("Source-gated writing pass rows must not be final-submission-ready.")
    if (writing_pass["source_coverage_gap_rows"].astype(int) != 0).any():
        raise ValueError("Source-gated writing pass rows must have zero source coverage gaps.")
    for artifact_list in writing_pass["deterministic_artifacts"].astype(str):
        for artifact in _split_semicolon(artifact_list):
            if not (repo_root / artifact).exists():
                raise FileNotFoundError(f"Source-gated writing pass artifact missing: {artifact}")
    for column in WRITING_PASS_COLUMNS:
        if writing_pass[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Source-gated writing pass contains empty {column}.")
    joined = "\n".join(writing_pass.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Source-gated writing pass must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "method_h1_brier_dm",
        "interpretation_h3_top_tier_signal",
        "source review",
        "source-gated",
        "manual source review follow-up overview",
        "overview-/ledger-abgleich",
        "keine finale zitation",
        "keine quellenstatus-hochstufung",
        "wenige gute tabellen",
        "keine runtime-agenten",
        "llm_audit_log",
        "nicht final-submission-ready",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Source-gated writing pass missing terms: " + ", ".join(missing))
    for area, area_rows in writing_pass.groupby("thesis_area"):
        gate_text = "\n".join(
            area_rows[["source_gate_paragraph_de", "full_chapter_draft_de"]]
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
                f"Source-gated writing pass missing source-gate terms for {area}: "
                + ", ".join(missing_gate_terms)
            )


def _render_writing_pass_doc(writing_pass: pd.DataFrame) -> str:
    bounded_ready = int(writing_pass["ready_for_bounded_draft"].map(_bool_value).sum())
    final_ready = int(writing_pass["ready_for_final_submission"].map(_bool_value).sum())
    gap_rows = int(writing_pass["source_coverage_gap_rows"].astype(int).sum())
    sections = [
        "# H1-H2-H3 Source-Gated Writing Pass\n",
        "Dieses Dokument ist der naechste BA-Schreibpass fuer die empirischen "
        "Kernkapitel. Es baut ausschliesslich auf dem bounded chapter draft, "
        "der Source Coverage und den deterministischen Artefakten auf. Es "
        "liest keine Quelleninhalte, erzeugt keine neuen Kennzahlen und "
        "ersetzt keine finale Quellenreview. Die Source-Gate-Paragraphen "
        "uebernehmen den Manual Source Review Follow-up Overview-/Ledger-"
        "Abgleich aus dem bounded chapter draft.\n",
        "## Counts\n",
        f"- Writing pass rows: {len(writing_pass)}\n",
        f"- Bounded draft ready rows: {bounded_ready}\n",
        f"- Final submission ready rows: {final_ready}\n",
        f"- Source coverage gap rows: {gap_rows}\n",
    ]
    for record in writing_pass.to_dict(orient="records"):
        sections.extend(
            [
                f"## {record['chapter_title_de']}\n",
                f"Methoden: `{record['method_evidence_ids']}`\n",
                f"Interpretationen: `{record['interpretation_evidence_ids']}`\n",
                f"Literatur: `{record['literature_source_ids']}`\n",
                f"Tabellen/Figuren: `{record['selected_tables']}` / `{record['selected_figures']}`\n",
                (
                    "Source-Coverage: "
                    f"{int(record['source_coverage_links'])} Links; "
                    f"{int(record['source_coverage_unique_sources'])} eindeutige Source-IDs; "
                    f"{int(record['source_coverage_gap_rows'])} Coverage-Gaps\n"
                ),
                "### Source-gated Draft\n",
                f"{record['full_chapter_draft_de']}\n",
                f"Nicht schreiben: {record['blocked_wording_de']}\n",
            ]
        )
    sections.extend(
        [
            "## Use Rule\n",
            "Nutze diesen Schreibpass als unmittelbare Grundlage fuer die "
            "H1-H2-H3-Ergebniskapitel. Jede Methode und Interpretation bleibt "
            "an Evidence IDs, Literatur-IDs, deterministische Artefakte, wenige "
            "gute Tabellen/Figuren, Limitationen und Source Review Gates "
            "gebunden. Keine finale Zitation, keine Rohartefakt-Dumps, keine "
            "neuen Kennzahlen, keine Quellenstatus-Hochstufung, keine "
            "Runtime-Agenten, kein MCP, kein Model Routing und keine "
            "LLM-Metriken. Der Manual Source Review Follow-up Overview-/"
            "Ledger-Abgleich bleibt vor dem Citation Gate sichtbar.\n",
        ]
    )
    return "\n".join(sections)


def _join_unique(values: list[str]) -> str:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        for item in _split_pipe(value):
            if item not in seen:
                seen.add(item)
                result.append(item)
    return " | ".join(result)


def _clean_sentence_spacing(value: str) -> str:
    return value.replace("..", ".").replace(" .", ".").strip()


def _split_pipe(value: str) -> list[str]:
    if value.lower() == "nan":
        return []
    return [item.strip() for item in value.split("|") if item.strip()]


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
        raise FileNotFoundError(f"Required source-gated writing pass input missing: {path}")
    return pd.read_csv(path)


def _resolve_under(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


if __name__ == "__main__":
    raise SystemExit(main())
