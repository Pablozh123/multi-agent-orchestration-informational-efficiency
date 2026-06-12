"""Build a deterministic traceability audit for thesis drafting."""

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

METHOD_TRACEABILITY_OUTPUT = "thesis_method_interpretation_traceability.csv"
RESULT_PACKAGE_TRACEABILITY_OUTPUT = "thesis_result_package_traceability.csv"
TRACEABILITY_DOC_OUTPUT = "THESIS_TRACEABILITY_AUDIT.md"

METHOD_TRACEABILITY_COLUMNS: tuple[str, ...] = (
    "evidence_id",
    "thesis_area",
    "item_type",
    "thesis_readiness",
    "primary_artifact",
    "primary_artifact_exists",
    "supporting_artifact_count",
    "supporting_artifact_exists_count",
    "literature_source_count",
    "known_literature_source_count",
    "sources_pending_full_review_count",
    "limitation_present",
    "allowed_wording_present",
    "blocked_wording_present",
    "traceability_status",
    "thesis_use_gate_de",
)

RESULT_PACKAGE_TRACEABILITY_COLUMNS: tuple[str, ...] = (
    "package_id",
    "package_type",
    "thesis_section",
    "include_in_core_package",
    "thesis_readiness",
    "primary_artifact",
    "primary_artifact_exists",
    "supporting_artifact_count",
    "supporting_artifact_exists_count",
    "linked_evidence_count",
    "linked_evidence_known_count",
    "caption_present",
    "source_note_present",
    "limitation_note_present",
    "package_traceability_status",
    "thesis_use_gate_de",
)


@dataclass(frozen=True)
class ThesisTraceabilityAuditResult:
    """Generated traceability audit paths and counts."""

    method_traceability_path: Path
    result_package_traceability_path: Path
    docs_path: Path
    method_traceability_rows: int
    thesis_facing_method_rows: int
    thesis_facing_interpretation_rows: int
    core_table_rows: int
    core_figure_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "method_traceability_path": str(self.method_traceability_path),
            "result_package_traceability_path": str(self.result_package_traceability_path),
            "docs_path": str(self.docs_path),
            "method_traceability_rows": self.method_traceability_rows,
            "thesis_facing_method_rows": self.thesis_facing_method_rows,
            "thesis_facing_interpretation_rows": self.thesis_facing_interpretation_rows,
            "core_table_rows": self.core_table_rows,
            "core_figure_rows": self.core_figure_rows,
        }


def generate_thesis_traceability_audit(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> ThesisTraceabilityAuditResult:
    """Generate method/result traceability CSVs and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    evidence_map = _read_csv(results_dir / "thesis_evidence_map.csv")
    result_package = _read_csv(results_dir / "thesis_curated_result_package.csv")
    captions = _read_csv(results_dir / "thesis_table_figure_captions.csv")
    citation_readiness = _read_csv(results_dir / "thesis_citation_readiness.csv")
    literature = _read_csv(repo_root / "data/literature/literature_index.csv")

    method_traceability = build_method_interpretation_traceability(
        evidence_map=evidence_map,
        citation_readiness=citation_readiness,
        literature=literature,
        repo_root=repo_root,
    )
    result_package_traceability = build_result_package_traceability(
        result_package=result_package,
        captions=captions,
        evidence_map=evidence_map,
        repo_root=repo_root,
    )
    _validate_method_traceability(method_traceability)
    _validate_result_package_traceability(result_package_traceability)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    method_path = results_dir / METHOD_TRACEABILITY_OUTPUT
    package_path = results_dir / RESULT_PACKAGE_TRACEABILITY_OUTPUT
    docs_path = docs_dir / TRACEABILITY_DOC_OUTPUT
    method_traceability.to_csv(method_path, index=False)
    result_package_traceability.to_csv(package_path, index=False)
    docs_path.write_text(
        _render_traceability_doc(
            method_traceability=method_traceability,
            result_package_traceability=result_package_traceability,
        ),
        encoding="utf-8",
    )

    thesis_facing = method_traceability[
        method_traceability["thesis_readiness"] == "thesis_facing_ready"
    ]
    core_package = result_package_traceability[
        result_package_traceability["include_in_core_package"].astype(bool)
    ]
    return ThesisTraceabilityAuditResult(
        method_traceability_path=method_path,
        result_package_traceability_path=package_path,
        docs_path=docs_path,
        method_traceability_rows=len(method_traceability),
        thesis_facing_method_rows=int((thesis_facing["item_type"] == "method").sum()),
        thesis_facing_interpretation_rows=int(
            (thesis_facing["item_type"] == "interpretation").sum()
        ),
        core_table_rows=int((core_package["package_type"] == "table").sum()),
        core_figure_rows=int((core_package["package_type"] == "figure").sum()),
    )


def build_method_interpretation_traceability(
    *,
    evidence_map: pd.DataFrame,
    citation_readiness: pd.DataFrame,
    literature: pd.DataFrame,
    repo_root: Path,
) -> pd.DataFrame:
    """Return method/interpretation traceability rows."""

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
            "allowed_wording",
            "blocked_wording",
            "main_limitation",
        ),
        "evidence map",
    )
    _require_columns(literature, ("source_id",), "literature index")
    _require_columns(
        citation_readiness,
        ("source_id", "final_citation_readiness"),
        "citation readiness",
    )

    known_sources = set(literature["source_id"].astype(str))
    readiness_by_source = (
        citation_readiness.set_index("source_id")["final_citation_readiness"].astype(str).to_dict()
    )
    rows: list[dict[str, object]] = []
    auditable = evidence_map[
        evidence_map["item_type"].isin(["method", "interpretation"])
    ].copy()
    for row in auditable.sort_values(["thesis_area", "item_type", "evidence_id"]).to_dict(
        orient="records"
    ):
        sources = _split_list(row["literature_sources"])
        supporting_artifacts = _split_list(row["supporting_artifacts"])
        known_count = sum(1 for source in sources if source in known_sources)
        pending_review_count = sum(
            1
            for source in sources
            if readiness_by_source.get(source) == "needs_full_source_review_before_final_citation"
        )
        primary_artifact = str(row["primary_artifact"]).strip()
        primary_exists = _artifact_exists(repo_root, primary_artifact)
        supporting_exists_count = sum(
            1 for artifact in supporting_artifacts if _artifact_exists(repo_root, artifact)
        )
        limitation_present = _present(row["main_limitation"])
        allowed_present = _present(row["allowed_wording"])
        blocked_present = _present(row["blocked_wording"])
        has_gap = (
            not primary_exists
            or len(sources) == 0
            or known_count != len(sources)
            or supporting_exists_count != len(supporting_artifacts)
            or not limitation_present
            or not allowed_present
            or not blocked_present
        )
        status = _traceability_status(
            thesis_readiness=str(row["thesis_readiness"]),
            has_gap=has_gap,
        )
        rows.append(
            {
                "evidence_id": str(row["evidence_id"]),
                "thesis_area": str(row["thesis_area"]),
                "item_type": str(row["item_type"]),
                "thesis_readiness": str(row["thesis_readiness"]),
                "primary_artifact": primary_artifact,
                "primary_artifact_exists": primary_exists,
                "supporting_artifact_count": len(supporting_artifacts),
                "supporting_artifact_exists_count": supporting_exists_count,
                "literature_source_count": len(sources),
                "known_literature_source_count": known_count,
                "sources_pending_full_review_count": pending_review_count,
                "limitation_present": limitation_present,
                "allowed_wording_present": allowed_present,
                "blocked_wording_present": blocked_present,
                "traceability_status": status,
                "thesis_use_gate_de": _method_gate(
                    thesis_readiness=str(row["thesis_readiness"]),
                    pending_review_count=pending_review_count,
                ),
            }
        )
    return pd.DataFrame(rows, columns=METHOD_TRACEABILITY_COLUMNS)


def build_result_package_traceability(
    *,
    result_package: pd.DataFrame,
    captions: pd.DataFrame,
    evidence_map: pd.DataFrame,
    repo_root: Path,
) -> pd.DataFrame:
    """Return table/figure package traceability rows."""

    _require_columns(
        result_package,
        (
            "package_id",
            "package_type",
            "thesis_section",
            "include_in_core_package",
            "thesis_readiness",
            "primary_artifact",
            "supporting_artifacts",
            "evidence_ids",
        ),
        "curated result package",
    )
    _require_columns(
        captions,
        (
            "package_id",
            "caption_de",
            "source_note_de",
            "limitation_note_de",
        ),
        "table figure captions",
    )
    _require_columns(evidence_map, ("evidence_id",), "evidence map")

    known_evidence = set(evidence_map["evidence_id"].astype(str))
    captions_by_package = captions.set_index("package_id").to_dict(orient="index")
    rows: list[dict[str, object]] = []
    for row in result_package.sort_values(["package_type", "package_id"]).to_dict(orient="records"):
        package_id = str(row["package_id"])
        supporting_artifacts = _split_list(row["supporting_artifacts"])
        linked_evidence = _split_list(row["evidence_ids"])
        primary_artifact = str(row["primary_artifact"]).strip()
        caption = captions_by_package.get(package_id, {})
        primary_exists = _artifact_exists(repo_root, primary_artifact)
        supporting_exists_count = sum(
            1 for artifact in supporting_artifacts if _artifact_exists(repo_root, artifact)
        )
        linked_known_count = sum(1 for evidence_id in linked_evidence if evidence_id in known_evidence)
        caption_present = _present(caption.get("caption_de", ""))
        source_note_present = _present(caption.get("source_note_de", ""))
        limitation_note_present = _present(caption.get("limitation_note_de", ""))
        include_in_core = _bool_value(row["include_in_core_package"])
        has_gap = (
            not primary_exists
            or supporting_exists_count != len(supporting_artifacts)
            or len(linked_evidence) == 0
            or linked_known_count != len(linked_evidence)
            or not caption_present
            or not source_note_present
            or not limitation_note_present
        )
        status = _package_status(
            include_in_core=include_in_core,
            thesis_readiness=str(row["thesis_readiness"]),
            has_gap=has_gap,
        )
        rows.append(
            {
                "package_id": package_id,
                "package_type": str(row["package_type"]),
                "thesis_section": str(row["thesis_section"]),
                "include_in_core_package": include_in_core,
                "thesis_readiness": str(row["thesis_readiness"]),
                "primary_artifact": primary_artifact,
                "primary_artifact_exists": primary_exists,
                "supporting_artifact_count": len(supporting_artifacts),
                "supporting_artifact_exists_count": supporting_exists_count,
                "linked_evidence_count": len(linked_evidence),
                "linked_evidence_known_count": linked_known_count,
                "caption_present": caption_present,
                "source_note_present": source_note_present,
                "limitation_note_present": limitation_note_present,
                "package_traceability_status": status,
                "thesis_use_gate_de": _package_gate(
                    include_in_core=include_in_core,
                    thesis_readiness=str(row["thesis_readiness"]),
                ),
            }
        )
    return pd.DataFrame(rows, columns=RESULT_PACKAGE_TRACEABILITY_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_thesis_traceability_audit(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_method_traceability(frame: pd.DataFrame) -> None:
    _require_columns(frame, METHOD_TRACEABILITY_COLUMNS, "method interpretation traceability")
    if frame["evidence_id"].duplicated().any():
        raise ValueError("Method/interpretation traceability contains duplicate evidence_id values.")
    thesis_facing = frame[frame["thesis_readiness"] == "thesis_facing_ready"]
    if thesis_facing.empty:
        raise ValueError("Traceability audit must contain thesis-facing method/interpretation rows.")
    if not set(thesis_facing["item_type"]).issuperset({"method", "interpretation"}):
        raise ValueError("Traceability audit must cover thesis-facing methods and interpretations.")
    if (thesis_facing["primary_artifact_exists"] != True).any():  # noqa: E712
        raise ValueError("Thesis-facing rows must have existing primary artifacts.")
    if (thesis_facing["literature_source_count"].astype(int) <= 0).any():
        raise ValueError("Thesis-facing rows must have at least one literature source.")
    if (
        thesis_facing["literature_source_count"].astype(int)
        != thesis_facing["known_literature_source_count"].astype(int)
    ).any():
        raise ValueError("Thesis-facing rows reference unknown literature sources.")
    if (
        thesis_facing["supporting_artifact_count"].astype(int)
        != thesis_facing["supporting_artifact_exists_count"].astype(int)
    ).any():
        raise ValueError("Thesis-facing rows reference missing supporting artifacts.")
    for column in (
        "limitation_present",
        "allowed_wording_present",
        "blocked_wording_present",
    ):
        if (thesis_facing[column] != True).any():  # noqa: E712
            raise ValueError(f"Thesis-facing rows contain false {column}.")
    if thesis_facing["traceability_status"].eq("traceability_gap").any():
        raise ValueError("Thesis-facing rows contain traceability gaps.")
    joined = "\n".join(frame.astype(str).agg(" ".join, axis=1).tolist())
    _validate_common_text(joined, "method interpretation traceability")


def _validate_result_package_traceability(frame: pd.DataFrame) -> None:
    _require_columns(frame, RESULT_PACKAGE_TRACEABILITY_COLUMNS, "result package traceability")
    if frame["package_id"].duplicated().any():
        raise ValueError("Result package traceability contains duplicate package_id values.")
    core_package = frame[frame["include_in_core_package"].astype(bool)]
    core_tables = int((core_package["package_type"] == "table").sum())
    core_figures = int((core_package["package_type"] == "figure").sum())
    if core_tables > 5:
        raise ValueError("Core result package has more than five tables.")
    if core_figures > 4:
        raise ValueError("Core result package has more than four figures.")
    if (core_package["primary_artifact_exists"] != True).any():  # noqa: E712
        raise ValueError("Core package rows must have existing primary artifacts.")
    if (
        core_package["supporting_artifact_count"].astype(int)
        != core_package["supporting_artifact_exists_count"].astype(int)
    ).any():
        raise ValueError("Core package rows reference missing supporting artifacts.")
    if (
        core_package["linked_evidence_count"].astype(int)
        != core_package["linked_evidence_known_count"].astype(int)
    ).any():
        raise ValueError("Core package rows reference unknown evidence ids.")
    for column in ("caption_present", "source_note_present", "limitation_note_present"):
        if (core_package[column] != True).any():  # noqa: E712
            raise ValueError(f"Core package rows contain false {column}.")
    if core_package["package_traceability_status"].eq("package_traceability_gap").any():
        raise ValueError("Core package rows contain traceability gaps.")
    joined = "\n".join(frame.astype(str).agg(" ".join, axis=1).tolist())
    _validate_common_text(joined, "result package traceability")


def _render_traceability_doc(
    *,
    method_traceability: pd.DataFrame,
    result_package_traceability: pd.DataFrame,
) -> str:
    thesis_facing = method_traceability[
        method_traceability["thesis_readiness"] == "thesis_facing_ready"
    ]
    core_package = result_package_traceability[
        result_package_traceability["include_in_core_package"].astype(bool)
    ]
    method_display = method_traceability[
        [
            "evidence_id",
            "thesis_area",
            "item_type",
            "thesis_readiness",
            "primary_artifact_exists",
            "literature_source_count",
            "known_literature_source_count",
            "sources_pending_full_review_count",
            "traceability_status",
            "thesis_use_gate_de",
        ]
    ]
    package_display = result_package_traceability[
        [
            "package_id",
            "package_type",
            "thesis_section",
            "include_in_core_package",
            "primary_artifact_exists",
            "linked_evidence_count",
            "linked_evidence_known_count",
            "package_traceability_status",
            "thesis_use_gate_de",
        ]
    ]
    return (
        "# Thesis Traceability Audit\n\n"
        "Dieses Audit prueft deterministisch, ob Methoden, Interpretationen, "
        "Tabellen und Figuren fuer den BA-Entwurf traceable sind. Es erzeugt "
        "keine neuen Kennzahlen, interpretiert keine Quelleninhalte und ersetzt "
        "keine manuelle Quellenreview.\n\n"
        "## Counts\n\n"
        f"- Method/interpretation rows: {len(method_traceability)}\n"
        f"- Thesis-facing method rows: {int((thesis_facing['item_type'] == 'method').sum())}\n"
        f"- Thesis-facing interpretation rows: {int((thesis_facing['item_type'] == 'interpretation').sum())}\n"
        f"- Core table rows: {int((core_package['package_type'] == 'table').sum())}\n"
        f"- Core figure rows: {int((core_package['package_type'] == 'figure').sum())}\n\n"
        "## Method And Interpretation Traceability\n\n"
        + _markdown_table(method_display)
        + "\n\n"
        "## Result Package Traceability\n\n"
        + _markdown_table(package_display)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze dieses Audit als BA-Schreibkontrolle. Thesis-facing Aussagen "
        "duerfen nur aus den gemappten deterministischen Artefakten, "
        "Limitationen und Quellenpaketen formuliert werden. Finale Zitation "
        "bleibt von manueller Quellenreview mit Page-/Section-Notes abhaengig. "
        "Keine Runtime-Agenten, keine LLM-Metriken, keine Rohartefakt-Dumps und "
        "keine neuen Support-Claims aus Dateistruktur.\n"
    )


def _traceability_status(*, thesis_readiness: str, has_gap: bool) -> str:
    if has_gap:
        return "traceability_gap"
    if thesis_readiness == "thesis_facing_ready":
        return "draft_traceable_final_source_review_pending"
    if thesis_readiness == "appendix_prototype_only":
        return "appendix_traceable_pending_human_review"
    if thesis_readiness == "descriptive_pending_result":
        return "descriptive_traceable_result_pending"
    return "noncore_traceable"


def _package_status(*, include_in_core: bool, thesis_readiness: str, has_gap: bool) -> str:
    if has_gap:
        return "package_traceability_gap"
    if not include_in_core:
        return "deferred_package_documentation_only"
    if thesis_readiness == "descriptive_pending_result":
        return "core_package_descriptive_pending_result"
    if thesis_readiness == "mixed_appendix_and_pending":
        return "core_package_mixed_appendix_pending"
    return "core_package_ready_for_draft"


def _method_gate(*, thesis_readiness: str, pending_review_count: int) -> str:
    if thesis_readiness == "appendix_prototype_only":
        return "Nur Appendix/Prototype; keine finale Zitation ohne Human Review."
    if thesis_readiness == "descriptive_pending_result":
        return "Nur beschreibend nutzen; keine finale Zitation bis Resultat- oder Review-Gate geklaert ist."
    if pending_review_count > 0:
        return "Draft nutzbar; keine finale Zitation ohne manuelle Quellenreview mit Page-/Section-Notes."
    return "Draft nutzbar; keine finale Zitation ohne bestaetigte Quellenreview."


def _package_gate(*, include_in_core: bool, thesis_readiness: str) -> str:
    if not include_in_core:
        return "Nur Future Work oder Appendix; keine finale Zitation als BA-Kernpaket ohne manuelle Review."
    if thesis_readiness == "descriptive_pending_result":
        return "Nur beschreibend integrieren; keine finale Zitation bis Resultat-Gate und manuelle Review geschlossen sind."
    if thesis_readiness == "mixed_appendix_and_pending":
        return "Als Status-/Grenztabelle nutzbar; keine finale Zitation ohne manuelle Review und sichtbare Monitor-/Swiss-Limits."
    return "In BA-Entwurf nutzbar; keine finale Zitation ohne manuelle Review und sichtbare Quellen-/Resultat-Gates."


def _artifact_exists(repo_root: Path, artifact: str) -> bool:
    if not artifact:
        return False
    if artifact.startswith(("http://", "https://")):
        return True
    return (repo_root / artifact).exists()


def _validate_common_text(joined: str, name: str) -> None:
    if chr(223) in joined:
        raise ValueError(f"{name} must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "manuell",
        "keine",
        "zitation",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError(f"{name} missing required guardrail terms: {missing}")


def _split_list(value: object) -> list[str]:
    if pd.isna(value):
        return []
    return [item.strip() for item in str(value).split(";") if item.strip()]


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _present(value: object) -> bool:
    if pd.isna(value):
        return False
    return bool(str(value).strip())


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required traceability audit input missing: {path}")
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
