"""Build a manual source-review worksheet for thesis citation cleanup.

The worksheet is a deterministic project-control artifact. It does not promote
source status, does not call LLMs, and does not inspect source contents. It only
groups existing source-review packets into a compact manual work surface.
"""

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

WORKSHEET_OUTPUT = "thesis_source_review_worksheet.csv"
WORKSHEET_DOC_OUTPUT = "THESIS_SOURCE_REVIEW_WORKSHEET.md"

WORKSHEET_COLUMNS: tuple[str, ...] = (
    "worksheet_id",
    "source_id",
    "priority_order",
    "source_title",
    "source_status",
    "priority_band",
    "citation_risk",
    "thesis_area_focus",
    "linked_evidence_ids",
    "method_packet_count",
    "interpretation_packet_count",
    "must_confirm",
    "must_not_claim",
    "review_source_locator",
    "local_file_registered",
    "reviewer_page_or_section_note",
    "reviewer_decision",
    "reviewer_notes",
)


@dataclass(frozen=True)
class SourceReviewWorksheetResult:
    """Generated source-review worksheet paths and counts."""

    worksheet_path: Path
    docs_path: Path
    worksheet_rows: int
    priority_1_rows: int
    blocked_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "worksheet_path": str(self.worksheet_path),
            "docs_path": str(self.docs_path),
            "worksheet_rows": self.worksheet_rows,
            "priority_1_rows": self.priority_1_rows,
            "blocked_rows": self.blocked_rows,
        }


def generate_source_review_worksheet(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> SourceReviewWorksheetResult:
    """Generate the source-review worksheet CSV and Markdown guide."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)
    literature = _read_csv(repo_root / "data/literature/literature_index.csv")
    source_review_plan = _read_csv(results_dir / "thesis_source_review_plan.csv")
    packets = _read_csv(results_dir / "thesis_citation_review_packets.csv")

    worksheet = build_source_review_worksheet(
        literature=literature,
        source_review_plan=source_review_plan,
        citation_review_packets=packets,
    )
    _validate_source_review_worksheet(worksheet)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    worksheet_path = results_dir / WORKSHEET_OUTPUT
    docs_path = docs_dir / WORKSHEET_DOC_OUTPUT
    worksheet.to_csv(worksheet_path, index=False)
    docs_path.write_text(_render_worksheet_doc(worksheet), encoding="utf-8")

    return SourceReviewWorksheetResult(
        worksheet_path=worksheet_path,
        docs_path=docs_path,
        worksheet_rows=len(worksheet),
        priority_1_rows=int(
            (worksheet["priority_band"] == "priority_1_method_foundation_review").sum()
        ),
        blocked_rows=int((worksheet["priority_band"] == "blocked_or_future_work_only").sum()),
    )


def build_source_review_worksheet(
    *,
    literature: pd.DataFrame,
    source_review_plan: pd.DataFrame,
    citation_review_packets: pd.DataFrame,
) -> pd.DataFrame:
    """Return one manual review row per indexed source."""

    _require_columns(
        literature,
        ("source_id", "title", "status", "url", "local_file"),
        "literature index",
    )
    _require_columns(
        source_review_plan,
        (
            "source_id",
            "source_title",
            "source_status",
            "priority_band",
            "citation_risk",
            "method_packet_count",
            "interpretation_packet_count",
        ),
        "source review plan",
    )
    _require_columns(
        citation_review_packets,
        (
            "source_id",
            "thesis_area",
            "evidence_id",
            "item_type",
            "allowed_wording",
            "blocked_wording",
            "reviewer_decision",
        ),
        "citation review packets",
    )

    literature_by_id = literature.set_index("source_id").to_dict(orient="index")
    packet_groups = {
        source_id: group.copy()
        for source_id, group in citation_review_packets.groupby("source_id", sort=False)
    }
    ordered_plan = source_review_plan.assign(
        _priority_rank=source_review_plan["priority_band"].map(_priority_rank).fillna(99),
        _risk_rank=source_review_plan["citation_risk"].map(_risk_rank).fillna(99),
    ).sort_values(
        [
            "_priority_rank",
            "_risk_rank",
            "method_packet_count",
            "interpretation_packet_count",
            "source_id",
        ],
        ascending=[True, True, False, False, True],
    )

    rows: list[dict[str, object]] = []
    for priority_order, row in enumerate(ordered_plan.to_dict(orient="records"), start=1):
        source_id = str(row["source_id"])
        source = literature_by_id.get(source_id, {})
        packets = packet_groups.get(source_id, pd.DataFrame(columns=citation_review_packets.columns))
        thesis_areas = _joined_unique(packets.get("thesis_area", pd.Series(dtype=str)).astype(str))
        evidence_ids = _joined_unique(packets.get("evidence_id", pd.Series(dtype=str)).astype(str))
        allowed = _joined_unique(packets.get("allowed_wording", pd.Series(dtype=str)).astype(str))
        blocked = _joined_unique(packets.get("blocked_wording", pd.Series(dtype=str)).astype(str))
        priority_band = str(row["priority_band"])
        must_confirm = allowed or _confirm_instruction(priority_band)
        must_not_claim = blocked or _blocked_instruction(priority_band)
        if priority_band == "blocked_or_future_work_only" and "thesis-facing" not in must_not_claim.lower():
            must_not_claim = (
                f"{must_not_claim}; "
                "Do not use for thesis-facing claims without separate source-status review."
            )
        rows.append(
            {
                "worksheet_id": f"source_review_{priority_order:02d}_{source_id}",
                "source_id": source_id,
                "priority_order": priority_order,
                "source_title": str(row["source_title"]),
                "source_status": str(row["source_status"]),
                "priority_band": priority_band,
                "citation_risk": str(row["citation_risk"]),
                "thesis_area_focus": thesis_areas or "not_currently_mapped",
                "linked_evidence_ids": evidence_ids or "none_currently",
                "method_packet_count": int(row["method_packet_count"]),
                "interpretation_packet_count": int(row["interpretation_packet_count"]),
                "must_confirm": must_confirm,
                "must_not_claim": must_not_claim,
                "review_source_locator": _source_locator(source),
                "local_file_registered": _local_file_registered(source),
                "reviewer_page_or_section_note": "",
                "reviewer_decision": "pending",
                "reviewer_notes": "",
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
        result = generate_source_review_worksheet(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_source_review_worksheet(frame: pd.DataFrame) -> None:
    _require_columns(frame, WORKSHEET_COLUMNS, "source review worksheet")
    if frame["worksheet_id"].duplicated().any():
        raise ValueError("Source review worksheet contains duplicate worksheet_id values.")
    if frame["source_id"].duplicated().any():
        raise ValueError("Source review worksheet contains duplicate source_id values.")
    expected_order = list(range(1, len(frame) + 1))
    if frame["priority_order"].astype(int).tolist() != expected_order:
        raise ValueError("Source review worksheet priority_order is not contiguous.")
    if not frame["reviewer_decision"].eq("pending").all():
        raise ValueError("Source review worksheet must keep reviewer_decision pending.")
    for column in (
        "source_title",
        "priority_band",
        "must_confirm",
        "must_not_claim",
        "review_source_locator",
    ):
        if frame[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Source review worksheet contains empty {column}.")
    blocked = frame[frame["priority_band"] == "blocked_or_future_work_only"]
    if not blocked.empty and not blocked["must_not_claim"].astype(str).str.contains(
        "thesis-facing",
        case=False,
        regex=False,
    ).all():
        raise ValueError("Blocked worksheet rows must mention thesis-facing claim limits.")
    joined = "\n".join(frame.astype(str).agg(" ".join, axis=1).tolist()).lower()
    required_terms = (
        "pending",
        "bounded",
        "source",
        "do not",
        "thesis-facing",
    )
    missing_terms = [term for term in required_terms if term not in joined]
    if missing_terms:
        raise ValueError("Source review worksheet missing required terms: " + ", ".join(missing_terms))


def _render_worksheet_doc(worksheet: pd.DataFrame) -> str:
    display = worksheet[
        [
            "priority_order",
            "source_id",
            "source_status",
            "priority_band",
            "thesis_area_focus",
            "linked_evidence_ids",
            "must_confirm",
            "must_not_claim",
            "review_source_locator",
            "reviewer_decision",
        ]
    ]
    priority_1 = int((worksheet["priority_band"] == "priority_1_method_foundation_review").sum())
    blocked = int((worksheet["priority_band"] == "blocked_or_future_work_only").sum())
    return (
        "# Thesis Source Review Worksheet\n\n"
        "This worksheet translates the citation review plan into a manual source "
        "review surface. It does not change source status and does not make any "
        "source final-citation-ready.\n\n"
        "## Counts\n\n"
        f"- Worksheet rows: {len(worksheet)}\n"
        f"- Priority-1 method-foundation rows: {priority_1}\n"
        f"- Blocked or future-work-only rows: {blocked}\n\n"
        "## Manual Review Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Fill reviewer page or section notes manually. Do not promote skimmed or "
        "candidate sources automatically, do not use blocked rows for "
        "thesis-facing claims, and do not use this worksheet to add new empirical "
        "metrics.\n"
    )


def _priority_rank(priority_band: str) -> int:
    return {
        "priority_1_method_foundation_review": 1,
        "priority_2_core_interpretation_review": 2,
        "priority_3_context_or_appendix_review": 3,
        "format_and_page_note_check": 4,
        "blocked_or_future_work_only": 5,
        "not_currently_needed": 6,
    }.get(str(priority_band), 99)


def _risk_rank(citation_risk: str) -> int:
    return {"high": 1, "medium": 2, "low": 3}.get(str(citation_risk), 99)


def _source_locator(source: dict[str, object]) -> str:
    url = str(source.get("url", "")).strip()
    if url and url != "nan":
        return url
    if _local_file_registered(source):
        return "local_file_registered_review_manually"
    return "locator_missing_review_metadata"


def _local_file_registered(source: dict[str, object]) -> bool:
    local_file = str(source.get("local_file", "")).strip()
    return bool(local_file and local_file not in {"nan", "not_local", "not_verified"})


def _confirm_instruction(priority_band: str) -> str:
    if priority_band == "not_currently_needed":
        return "Confirm only if source becomes mapped to an evidence row."
    if priority_band == "blocked_or_future_work_only":
        return "Confirm metadata relevance only; do not support thesis-facing claims."
    return "Confirm bounded source support for the linked method or interpretation."


def _blocked_instruction(priority_band: str) -> str:
    if priority_band == "blocked_or_future_work_only":
        return "Do not use for thesis-facing claims without separate source-status review."
    if priority_band == "not_currently_needed":
        return "Do not cite until mapped to a thesis claim and reviewed."
    return "Do not extend beyond bounded wording or deterministic artifacts."


def _joined_unique(series: pd.Series) -> str:
    values = [
        str(value).strip()
        for value in series.tolist()
        if str(value).strip() and str(value).strip().lower() != "nan"
    ]
    return "; ".join(dict.fromkeys(values))


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required source review worksheet input missing: {path}")
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
