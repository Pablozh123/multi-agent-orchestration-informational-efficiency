"""Build source coverage audit rows for methods and interpretations."""

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

COVERAGE_OUTPUT = "thesis_method_interpretation_source_coverage.csv"
COVERAGE_DOC_OUTPUT = "THESIS_METHOD_INTERPRETATION_SOURCE_COVERAGE.md"

COVERAGE_COLUMNS: tuple[str, ...] = (
    "coverage_id",
    "evidence_id",
    "thesis_area",
    "item_type",
    "thesis_readiness",
    "source_id",
    "source_known_in_literature_index",
    "source_status",
    "source_relevance",
    "final_citation_readiness",
    "primary_artifact",
    "primary_artifact_exists",
    "supporting_artifact_count",
    "supporting_artifact_exists_count",
    "limitation_present",
    "coverage_status",
    "thesis_use_gate_de",
)


@dataclass(frozen=True)
class MethodInterpretationSourceCoverageResult:
    """Generated method/interpretation source coverage paths and counts."""

    coverage_path: Path
    docs_path: Path
    coverage_rows: int
    thesis_facing_coverage_rows: int
    source_ids: int
    coverage_gap_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "coverage_path": str(self.coverage_path),
            "docs_path": str(self.docs_path),
            "coverage_rows": self.coverage_rows,
            "thesis_facing_coverage_rows": self.thesis_facing_coverage_rows,
            "source_ids": self.source_ids,
            "coverage_gap_rows": self.coverage_gap_rows,
        }


def generate_method_interpretation_source_coverage(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> MethodInterpretationSourceCoverageResult:
    """Generate method/interpretation source coverage CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    evidence_map = _read_csv(results_dir / "thesis_evidence_map.csv")
    literature = _read_csv(repo_root / "data/literature/literature_index.csv")
    citation_readiness = _read_csv(results_dir / "thesis_citation_readiness.csv")

    coverage = build_method_interpretation_source_coverage(
        evidence_map=evidence_map,
        literature=literature,
        citation_readiness=citation_readiness,
        repo_root=repo_root,
    )
    _validate_coverage(coverage)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    coverage_path = results_dir / COVERAGE_OUTPUT
    docs_path = docs_dir / COVERAGE_DOC_OUTPUT
    coverage.to_csv(coverage_path, index=False)
    docs_path.write_text(_render_coverage_doc(coverage), encoding="utf-8")

    thesis_facing = coverage[coverage["thesis_readiness"] == "thesis_facing_ready"]
    return MethodInterpretationSourceCoverageResult(
        coverage_path=coverage_path,
        docs_path=docs_path,
        coverage_rows=len(coverage),
        thesis_facing_coverage_rows=len(thesis_facing),
        source_ids=coverage["source_id"].nunique(),
        coverage_gap_rows=int((coverage["coverage_status"] == "coverage_gap").sum()),
    )


def build_method_interpretation_source_coverage(
    *,
    evidence_map: pd.DataFrame,
    literature: pd.DataFrame,
    citation_readiness: pd.DataFrame,
    repo_root: Path,
) -> pd.DataFrame:
    """Return one coverage row per evidence-source link."""

    _require_columns(
        evidence_map,
        (
            "evidence_id",
            "thesis_area",
            "item_type",
            "thesis_readiness",
            "primary_artifact",
            "supporting_artifacts",
            "literature_sources",
            "main_limitation",
        ),
        "evidence map",
    )
    _require_columns(
        literature,
        ("source_id", "status", "relevance", "topic"),
        "literature index",
    )
    _require_columns(
        citation_readiness,
        ("source_id", "final_citation_readiness"),
        "citation readiness",
    )

    literature_by_source = literature.set_index("source_id").to_dict(orient="index")
    readiness_by_source = (
        citation_readiness.set_index("source_id")["final_citation_readiness"].astype(str).to_dict()
    )
    rows: list[dict[str, object]] = []
    auditable = evidence_map[evidence_map["item_type"].isin(["method", "interpretation"])].copy()
    for evidence in auditable.sort_values(["thesis_area", "item_type", "evidence_id"]).to_dict(
        orient="records"
    ):
        source_ids = _split_semicolon(evidence["literature_sources"])
        primary_artifact = str(evidence["primary_artifact"]).strip()
        supporting_artifacts = _split_semicolon(evidence["supporting_artifacts"])
        primary_exists = _artifact_exists(repo_root, primary_artifact)
        supporting_exists_count = sum(
            1 for artifact in supporting_artifacts if _artifact_exists(repo_root, artifact)
        )
        limitation_present = _present(evidence["main_limitation"])
        if not source_ids:
            source_ids = [""]
        for source_id in source_ids:
            source = literature_by_source.get(source_id, {})
            source_known = bool(source)
            readiness = readiness_by_source.get(source_id, "missing_citation_readiness")
            has_gap = (
                not source_known
                or not primary_exists
                or supporting_exists_count != len(supporting_artifacts)
                or not limitation_present
            )
            coverage_status = _coverage_status(
                thesis_readiness=str(evidence["thesis_readiness"]),
                has_gap=has_gap,
            )
            rows.append(
                {
                    "coverage_id": f"coverage_{len(rows) + 1:03d}_{evidence['evidence_id']}_{source_id or 'missing_source'}",
                    "evidence_id": str(evidence["evidence_id"]),
                    "thesis_area": str(evidence["thesis_area"]),
                    "item_type": str(evidence["item_type"]),
                    "thesis_readiness": str(evidence["thesis_readiness"]),
                    "source_id": source_id,
                    "source_known_in_literature_index": source_known,
                    "source_status": str(source.get("status", "missing")),
                    "source_relevance": str(source.get("relevance", "missing")),
                    "final_citation_readiness": readiness,
                    "primary_artifact": primary_artifact,
                    "primary_artifact_exists": primary_exists,
                    "supporting_artifact_count": len(supporting_artifacts),
                    "supporting_artifact_exists_count": supporting_exists_count,
                    "limitation_present": limitation_present,
                    "coverage_status": coverage_status,
                    "thesis_use_gate_de": _thesis_use_gate(
                        thesis_readiness=str(evidence["thesis_readiness"]),
                        readiness=readiness,
                    ),
                }
            )
    return pd.DataFrame(rows, columns=COVERAGE_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_method_interpretation_source_coverage(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_coverage(coverage: pd.DataFrame) -> None:
    _require_columns(coverage, COVERAGE_COLUMNS, "method interpretation source coverage")
    if coverage["coverage_id"].duplicated().any():
        raise ValueError("Source coverage contains duplicate coverage_id values.")
    if coverage.empty:
        raise ValueError("Source coverage must not be empty.")
    thesis_facing = coverage[coverage["thesis_readiness"] == "thesis_facing_ready"]
    if thesis_facing.empty:
        raise ValueError("Source coverage must include thesis-facing rows.")
    if (thesis_facing["source_known_in_literature_index"] != True).any():  # noqa: E712
        raise ValueError("Thesis-facing source coverage references unknown source ids.")
    if (thesis_facing["primary_artifact_exists"] != True).any():  # noqa: E712
        raise ValueError("Thesis-facing source coverage references missing primary artifacts.")
    if (
        thesis_facing["supporting_artifact_count"].astype(int)
        != thesis_facing["supporting_artifact_exists_count"].astype(int)
    ).any():
        raise ValueError("Thesis-facing source coverage references missing supporting artifacts.")
    if (thesis_facing["limitation_present"] != True).any():  # noqa: E712
        raise ValueError("Thesis-facing source coverage rows must include limitations.")
    if thesis_facing["coverage_status"].eq("coverage_gap").any():
        raise ValueError("Thesis-facing source coverage contains coverage gaps.")
    joined = "\n".join(coverage.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Source coverage must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "source_mapped_final_review_pending",
        "keine finale zitation",
        "deterministische",
        "source review",
        "thesis_facing_ready",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Source coverage missing required terms: " + ", ".join(missing))


def _render_coverage_doc(coverage: pd.DataFrame) -> str:
    thesis_facing = coverage[coverage["thesis_readiness"] == "thesis_facing_ready"]
    by_area = thesis_facing["thesis_area"].value_counts().sort_index().to_dict()
    status_counts = coverage["coverage_status"].value_counts().sort_index().to_dict()
    display = coverage[
        [
            "evidence_id",
            "thesis_area",
            "item_type",
            "source_id",
            "source_status",
            "final_citation_readiness",
            "primary_artifact_exists",
            "coverage_status",
            "thesis_use_gate_de",
        ]
    ]
    return (
        "# Thesis Method/Interpretation Source Coverage\n\n"
        "Dieses Audit mappt jede Methoden- und Interpretationszeile aus der "
        "Evidence Map auf ihre Literaturquelle und ihr deterministisches "
        "Primaerartefakt. Es liest keine Quelleninhalte, stuft keinen "
        "Quellenstatus hoch und erzeugt keine neuen empirischen Kennzahlen.\n\n"
        "## Counts\n\n"
        f"- Coverage rows: {len(coverage)}\n"
        f"- Thesis-facing coverage rows: {len(thesis_facing)}\n"
        f"- Unique source IDs: {coverage['source_id'].nunique()}\n"
        f"- Coverage gap rows: {int((coverage['coverage_status'] == 'coverage_gap').sum())}\n"
        f"- H1 thesis-facing source links: {int(by_area.get('H1', 0))}\n"
        f"- H2 thesis-facing source links: {int(by_area.get('H2', 0))}\n"
        f"- H3 thesis-facing source links: {int(by_area.get('H3', 0))}\n"
        f"- Source mapped final review pending rows: {int(status_counts.get('source_mapped_final_review_pending', 0))}\n\n"
        "## Coverage Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze dieses Audit vor dem Schreiben und vor jedem Dozentenfeedback-"
        "Follow-up. Jede thesis-facing Methode und Interpretation muss eine "
        "bekannte Literaturquelle oder ein deterministisches Artefakt, eine "
        "Limitation und ein Source Review Gate behalten. Keine finale Zitation "
        "ohne manuelle Quellenreview mit Page-/Section-Notes; keine "
        "Quellenstatus-Hochstufung aus diesem Audit.\n"
    )


def _coverage_status(*, thesis_readiness: str, has_gap: bool) -> str:
    if has_gap:
        return "coverage_gap"
    if thesis_readiness == "thesis_facing_ready":
        return "source_mapped_final_review_pending"
    if thesis_readiness == "appendix_prototype_only":
        return "appendix_source_mapped_human_review_pending"
    if thesis_readiness == "descriptive_pending_result":
        return "descriptive_source_mapped_result_pending"
    return "source_mapped_noncore"


def _thesis_use_gate(*, thesis_readiness: str, readiness: str) -> str:
    if thesis_readiness == "appendix_prototype_only":
        return "Nur Appendix/Prototype; keine finale Zitation ohne Human Review und Source Review."
    if thesis_readiness == "descriptive_pending_result":
        return "Nur beschreibend; keine finale Zitation bis Resultat-Gate und Source Review geschlossen sind."
    if readiness == "not_allowed_for_thesis_facing_claims":
        return "Nicht fuer thesis-facing Claims nutzen; Quelle bleibt blockiert oder future-only."
    return "Draft nutzbar; keine finale Zitation ohne manuelle Source Review und deterministische Artefaktbindung."


def _artifact_exists(repo_root: Path, artifact: str) -> bool:
    if not artifact:
        return False
    if artifact.startswith(("http://", "https://")):
        return True
    return (repo_root / artifact).exists()


def _split_semicolon(value: object) -> list[str]:
    if pd.isna(value):
        return []
    return [item.strip() for item in str(value).split(";") if item.strip()]


def _present(value: object) -> bool:
    if pd.isna(value):
        return False
    return bool(str(value).strip())


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required source coverage input missing: {path}")
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
