"""Build chapter-to-source binding matrix from thesis consolidation artifacts."""

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

BINDINGS_OUTPUT = "thesis_chapter_source_bindings.csv"
BINDINGS_DOC_OUTPUT = "THESIS_CHAPTER_SOURCE_BINDINGS.md"

BINDING_COLUMNS: tuple[str, ...] = (
    "chapter_id",
    "chapter_title",
    "core_evidence_ids",
    "source_ids",
    "source_review_tasks",
    "table_figure_items",
    "primary_artifacts",
    "source_gate_de",
    "writing_gate_de",
)


@dataclass(frozen=True)
class ChapterSourceBindingsResult:
    """Generated chapter-source binding paths and counts."""

    bindings_path: Path
    docs_path: Path
    binding_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "bindings_path": str(self.bindings_path),
            "docs_path": str(self.docs_path),
            "binding_rows": self.binding_rows,
        }


def generate_chapter_source_bindings(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> ChapterSourceBindingsResult:
    """Generate chapter-source binding CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)
    chapter_plan = _read_csv(results_dir / "thesis_chapter_plan.csv")
    packets = _read_csv(results_dir / "thesis_citation_review_packets.csv")
    source_review = _read_csv(results_dir / "thesis_source_review_execution.csv")
    captions = _read_csv(results_dir / "thesis_table_figure_captions.csv")

    bindings = build_chapter_source_bindings(
        chapter_plan=chapter_plan,
        packets=packets,
        source_review=source_review,
        captions=captions,
    )
    _validate_bindings(bindings, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    bindings_path = results_dir / BINDINGS_OUTPUT
    docs_path = docs_dir / BINDINGS_DOC_OUTPUT
    bindings.to_csv(bindings_path, index=False)
    docs_path.write_text(_render_bindings_doc(bindings), encoding="utf-8")

    return ChapterSourceBindingsResult(
        bindings_path=bindings_path,
        docs_path=docs_path,
        binding_rows=len(bindings),
    )


def build_chapter_source_bindings(
    *,
    chapter_plan: pd.DataFrame,
    packets: pd.DataFrame,
    source_review: pd.DataFrame,
    captions: pd.DataFrame,
) -> pd.DataFrame:
    """Return one binding row per chapter in the chapter plan."""

    _require_columns(
        chapter_plan,
        (
            "chapter_id",
            "chapter_title",
            "core_evidence_ids",
            "recommended_tables",
            "recommended_figures",
            "primary_artifacts",
            "writing_status",
        ),
        "chapter plan",
    )
    _require_columns(packets, ("source_id", "evidence_id"), "citation review packets")
    _require_columns(source_review, ("source_id", "review_task_id", "review_stage"), "source review")
    _require_columns(captions, ("package_id", "thesis_label"), "table figure captions")

    sources_by_evidence = _sources_by_evidence(packets)
    task_by_source = {
        str(row["source_id"]): str(row["review_task_id"])
        for row in source_review.to_dict(orient="records")
    }
    stage_by_source = {
        str(row["source_id"]): str(row["review_stage"])
        for row in source_review.to_dict(orient="records")
    }
    caption_labels = {
        str(row["package_id"]): str(row["thesis_label"])
        for row in captions.to_dict(orient="records")
    }

    rows = []
    for row in chapter_plan.to_dict(orient="records"):
        evidence_ids = _split_list(str(row["core_evidence_ids"]))
        source_ids = sorted({source for evidence_id in evidence_ids for source in sources_by_evidence.get(evidence_id, [])})
        source_tasks = [task_by_source[source_id] for source_id in source_ids if source_id in task_by_source]
        review_stages = sorted({stage_by_source.get(source_id, "unknown") for source_id in source_ids})
        rows.append(
            {
                "chapter_id": str(row["chapter_id"]),
                "chapter_title": str(row["chapter_title"]),
                "core_evidence_ids": "; ".join(evidence_ids),
                "source_ids": "; ".join(source_ids) if source_ids else "none_mapped",
                "source_review_tasks": "; ".join(source_tasks) if source_tasks else "none_mapped",
                "table_figure_items": _table_figure_items(row, caption_labels),
                "primary_artifacts": str(row["primary_artifacts"]),
                "source_gate_de": _source_gate_de(review_stages),
                "writing_gate_de": _writing_gate_de(str(row["writing_status"])),
            }
        )
    return pd.DataFrame(rows, columns=BINDING_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_chapter_source_bindings(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _sources_by_evidence(packets: pd.DataFrame) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for evidence_id, group in packets.groupby("evidence_id"):
        mapping[str(evidence_id)] = sorted(group["source_id"].astype(str).unique().tolist())
    return mapping


def _table_figure_items(row: dict[str, object], caption_labels: dict[str, str]) -> str:
    items = _split_list(str(row.get("recommended_tables", ""))) + _split_list(
        str(row.get("recommended_figures", ""))
    )
    labels = []
    for item in items:
        label = caption_labels.get(item)
        labels.append(f"{item} ({label})" if label else item)
    return "; ".join(labels) if labels else "none"


def _source_gate_de(review_stages: list[str]) -> str:
    if not review_stages or review_stages == ["unknown"]:
        return "Keine finalen Source-Claims, bis Evidence-ID und Quellenreview-Aufgabe gemappt sind."
    if "metadata_only_blocked" in review_stages:
        return "Blocked/future-only Quellen nicht fuer thesis-facing Claims verwenden."
    if "defer_until_mapped" in review_stages:
        return "Deferred Quellen nicht zitieren, bis sie einer Evidence-ID zugeordnet und reviewt sind."
    return "Quellenstatus nicht automatisch hochstufen; finale Zitation erst nach Human Review."


def _writing_gate_de(writing_status: str) -> str:
    if writing_status == "source_review_needed":
        return "Kapitel erst finalisieren, wenn Seiten- oder Abschnittsnotizen eingetragen sind."
    if writing_status in {"result_ready_with_limits", "appendix_or_discussion_ready"}:
        return "Draft moeglich; Limitation und Source-Gate muessen direkt im Text stehen."
    if writing_status == "draft_ready":
        return "Draft moeglich; Methodengrenzen und Artefaktverweise sichtbar halten."
    return "Outline schreiben; finale Claims erst nach Quellenreview und Wording Guard."


def _validate_bindings(bindings: pd.DataFrame, *, repo_root: Path) -> None:
    _require_columns(bindings, BINDING_COLUMNS, "chapter source bindings")
    if bindings["chapter_id"].duplicated().any():
        raise ValueError("Chapter source bindings contain duplicate chapter_id values.")
    if len(bindings) == 0:
        raise ValueError("Chapter source bindings are empty.")
    if bindings["source_ids"].astype(str).eq("none_mapped").any():
        raise ValueError("Every chapter binding must map to at least one source.")
    for row in bindings.to_dict(orient="records"):
        for artifact in _split_list(str(row["primary_artifacts"])):
            if not (repo_root / artifact).exists():
                raise FileNotFoundError(f"Chapter binding primary artifact missing: {artifact}")
    joined = "\n".join(bindings.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Chapter source bindings must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "quellenstatus nicht automatisch hochstufen",
        "human review",
        "thesis-facing claims",
        "limitation",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Chapter source bindings missing required gates: " + ", ".join(missing))


def _render_bindings_doc(bindings: pd.DataFrame) -> str:
    display = bindings[
        [
            "chapter_id",
            "chapter_title",
            "core_evidence_ids",
            "source_ids",
            "source_review_tasks",
            "table_figure_items",
            "source_gate_de",
            "writing_gate_de",
        ]
    ]
    return (
        "# Thesis Chapter Source Bindings\n\n"
        "Diese Matrix verbindet jedes geplante BA-Kapitel mit Evidence-IDs, "
        "Quellen, Review-Aufgaben, Tabellen/Figuren und Schreib-Gates. Sie "
        "erzeugt keine neuen empirischen Resultate.\n\n"
        "## Counts\n\n"
        f"- Chapter binding rows: {len(bindings)}\n"
        f"- Chapters with source mapping: {int((bindings['source_ids'] != 'none_mapped').sum())}\n\n"
        "## Chapter Bindings\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze diese Matrix beim Schreiben der BA-Kapitel. Quellenstatus nicht "
        "automatisch hochstufen; keine thesis-facing Claims ohne Human Review, "
        "Artefaktverweis, Limitation und Wording Guard uebernehmen.\n"
    )


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required chapter binding input missing: {path}")
    return pd.read_csv(path)


def _resolve_under(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _split_list(value: str) -> list[str]:
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
