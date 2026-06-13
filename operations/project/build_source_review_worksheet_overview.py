"""Build a consolidated overview of H1-H2-H3 source-review worksheets."""

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

OVERVIEW_OUTPUT = "thesis_source_review_worksheet_overview.csv"
OVERVIEW_DOC_OUTPUT = "THESIS_SOURCE_REVIEW_WORKSHEET_OVERVIEW.md"

OVERVIEW_COLUMNS: tuple[str, ...] = (
    "overview_id",
    "overview_order",
    "thesis_area",
    "worksheet_artifact",
    "worksheet_rows",
    "unique_sources",
    "method_rows",
    "interpretation_rows",
    "external_locator_rows",
    "local_pdf_rows",
    "pending_citation_rows",
    "final_release_ready_rows",
    "selected_tables",
    "selected_figures",
    "boundary_terms_de",
    "manual_fields_de",
    "next_action_de",
    "blocked_actions_de",
    "ready_for_manual_entry",
    "ready_for_final_release",
)

WORKSHEET_REQUIRED_COLUMNS: tuple[str, ...] = (
    "worksheet_order",
    "thesis_area",
    "source_id",
    "item_type",
    "access_route",
    "selected_table",
    "selected_figure",
    "current_citation_use_decision",
    "required_manual_fields_de",
    "ready_for_manual_entry",
    "ready_for_final_release",
)

AREA_INPUTS: tuple[tuple[str, str, str], ...] = (
    (
        "H1",
        "data/results/thesis_h1_source_review_batch_worksheet.csv",
        "docs/project/THESIS_H1_SOURCE_REVIEW_BATCH_WORKSHEET.md",
    ),
    (
        "H2",
        "data/results/thesis_h2_source_review_batch_worksheet.csv",
        "docs/project/THESIS_H2_SOURCE_REVIEW_BATCH_WORKSHEET.md",
    ),
    (
        "H3",
        "data/results/thesis_h3_source_review_batch_worksheet.csv",
        "docs/project/THESIS_H3_SOURCE_REVIEW_BATCH_WORKSHEET.md",
    ),
)


@dataclass(frozen=True)
class SourceReviewWorksheetOverviewResult:
    """Generated source-review worksheet overview paths and counts."""

    overview_path: Path
    docs_path: Path
    overview_rows: int
    worksheet_rows: int
    unique_sources: int
    pending_citation_rows: int
    final_release_ready_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "overview_path": str(self.overview_path),
            "docs_path": str(self.docs_path),
            "overview_rows": self.overview_rows,
            "worksheet_rows": self.worksheet_rows,
            "unique_sources": self.unique_sources,
            "pending_citation_rows": self.pending_citation_rows,
            "final_release_ready_rows": self.final_release_ready_rows,
        }


def generate_source_review_worksheet_overview(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> SourceReviewWorksheetOverviewResult:
    """Generate the consolidated worksheet overview CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    worksheets = {
        area: _read_csv(_resolve_under(repo_root, Path(csv_path)))
        for area, csv_path, _doc_path in AREA_INPUTS
    }
    overview = build_source_review_worksheet_overview(worksheets=worksheets)
    _validate_overview(overview=overview, worksheets=worksheets, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    overview_path = results_dir / OVERVIEW_OUTPUT
    docs_path = docs_dir / OVERVIEW_DOC_OUTPUT
    overview.to_csv(overview_path, index=False)
    docs_path.write_text(_render_overview_doc(overview), encoding="utf-8")

    total = _overview_row(overview, "TOTAL")
    return SourceReviewWorksheetOverviewResult(
        overview_path=overview_path,
        docs_path=docs_path,
        overview_rows=len(overview),
        worksheet_rows=int(total["worksheet_rows"]),
        unique_sources=int(total["unique_sources"]),
        pending_citation_rows=int(total["pending_citation_rows"]),
        final_release_ready_rows=int(overview["ready_for_final_release"].map(_bool_value).sum()),
    )


def build_source_review_worksheet_overview(
    *,
    worksheets: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Return one overview row for H1, H2, H3, and TOTAL."""

    rows: list[dict[str, object]] = []
    ordered_frames: list[pd.DataFrame] = []
    for order, (area, csv_path, _doc_path) in enumerate(AREA_INPUTS, start=1):
        worksheet = worksheets.get(area)
        if worksheet is None:
            raise ValueError(f"Missing worksheet input for {area}.")
        _require_columns(worksheet, WORKSHEET_REQUIRED_COLUMNS, f"{area} worksheet")
        area_rows = worksheet.loc[worksheet["thesis_area"].astype(str) == area]
        if len(area_rows) != len(worksheet):
            raise ValueError(f"{area} worksheet contains rows from another thesis area.")
        rows.append(
            _row(
                overview_id=f"worksheet_overview_{area.lower()}",
                overview_order=order,
                thesis_area=area,
                worksheet_artifact=csv_path,
                frame=worksheet,
                boundary_terms_de=_boundary_terms(area),
                next_action_de=_next_action(area),
                blocked_actions_de=_blocked_actions(area),
            )
        )
        ordered_frames.append(worksheet)
    total_frame = pd.concat(ordered_frames, ignore_index=True)
    rows.append(
        _row(
            overview_id="worksheet_overview_total",
            overview_order=4,
            thesis_area="TOTAL",
            worksheet_artifact="; ".join(csv_path for _area, csv_path, _doc_path in AREA_INPUTS),
            frame=total_frame,
            boundary_terms_de=(
                "H1 broad-claim boundary; H2 Kausalclaim-Grenze; H3 Granger-Grenze "
                "und Wallet-Grenze."
            ),
            next_action_de=(
                "Worksheets H1, H2 und H3 manuell abarbeiten, danach Ledger, "
                "Citation Gate Summary, Batch Plan, Worksheet Overview und Index regenerieren."
            ),
            blocked_actions_de=(
                "Keine finale Zitation, keine Quellenstatus-Hochstufung, keine "
                "Kausalclaims, keine Wallet-Adressen, keine Trading-Claims, "
                "keine Profitabilitaetsclaims und keine Runtime-Agenten."
            ),
        )
    )
    return pd.DataFrame(rows, columns=OVERVIEW_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_source_review_worksheet_overview(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _row(
    *,
    overview_id: str,
    overview_order: int,
    thesis_area: str,
    worksheet_artifact: str,
    frame: pd.DataFrame,
    boundary_terms_de: str,
    next_action_de: str,
    blocked_actions_de: str,
) -> dict[str, object]:
    return {
        "overview_id": overview_id,
        "overview_order": overview_order,
        "thesis_area": thesis_area,
        "worksheet_artifact": worksheet_artifact,
        "worksheet_rows": len(frame),
        "unique_sources": int(frame["source_id"].nunique()),
        "method_rows": int((frame["item_type"] == "method").sum()),
        "interpretation_rows": int((frame["item_type"] == "interpretation").sum()),
        "external_locator_rows": int((frame["access_route"] == "external_locator_review").sum()),
        "local_pdf_rows": int((frame["access_route"] == "local_pdf_review").sum()),
        "pending_citation_rows": int(
            (frame["current_citation_use_decision"] == "blocked_pending_manual_review").sum()
        ),
        "final_release_ready_rows": int(frame["ready_for_final_release"].map(_bool_value).sum()),
        "selected_tables": _unique_join(frame["selected_table"]),
        "selected_figures": _unique_join(frame["selected_figure"]),
        "boundary_terms_de": boundary_terms_de,
        "manual_fields_de": _unique_join(frame["required_manual_fields_de"]),
        "next_action_de": next_action_de,
        "blocked_actions_de": blocked_actions_de,
        "ready_for_manual_entry": bool(frame["ready_for_manual_entry"].map(_bool_value).all()),
        "ready_for_final_release": False,
    }


def _validate_overview(
    *,
    overview: pd.DataFrame,
    worksheets: dict[str, pd.DataFrame],
    repo_root: Path,
) -> None:
    _require_columns(overview, OVERVIEW_COLUMNS, "source-review worksheet overview")
    if len(overview) != 4:
        raise ValueError("Source-review worksheet overview must contain 4 rows.")
    if overview["overview_order"].astype(int).tolist() != [1, 2, 3, 4]:
        raise ValueError("Source-review worksheet overview order must be H1, H2, H3, TOTAL.")
    if overview["overview_id"].duplicated().any():
        raise ValueError("Source-review worksheet overview contains duplicate IDs.")
    if not overview["ready_for_manual_entry"].map(_bool_value).all():
        raise ValueError("Source-review worksheet overview must be ready for manual entry.")
    if overview["ready_for_final_release"].map(_bool_value).any():
        raise ValueError("Source-review worksheet overview must not be final-release-ready.")
    if int(overview["final_release_ready_rows"].astype(int).sum()) != 0:
        raise ValueError("Source-review worksheet overview must not be final-release-ready.")
    for _area, csv_path, doc_path in AREA_INPUTS:
        for artifact in (csv_path, doc_path):
            if not (repo_root / artifact).exists():
                raise FileNotFoundError(f"Source-review worksheet overview artifact missing: {artifact}")
    expected = {
        "H1": (10, 4, 4, 6, 7, 3, 10, 0, "T2", "F1"),
        "H2": (5, 3, 3, 2, 4, 1, 5, 0, "T3", "F2"),
        "H3": (8, 4, 5, 3, 2, 6, 8, 0, "T4", "F3"),
        "TOTAL": (23, 9, 12, 11, 13, 10, 23, 0, "T2, T3, T4", "F1, F2, F3"),
    }
    for area, expected_values in expected.items():
        row = _overview_row(overview, area)
        actual_values = (
            int(row["worksheet_rows"]),
            int(row["unique_sources"]),
            int(row["method_rows"]),
            int(row["interpretation_rows"]),
            int(row["external_locator_rows"]),
            int(row["local_pdf_rows"]),
            int(row["pending_citation_rows"]),
            int(row["final_release_ready_rows"]),
            str(row["selected_tables"]),
            str(row["selected_figures"]),
        )
        if actual_values != expected_values:
            raise ValueError(
                f"Unexpected source-review worksheet overview counts for {area}: "
                f"{actual_values} != {expected_values}."
            )
    joined = "\n".join(overview.fillna("").astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Source-review worksheet overview must use Swiss spelling without sharp-s.")
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
        "keine wallet-adressen",
        "keine trading-claims",
        "keine profitabilitaetsclaims",
        "keine runtime-agenten",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError(
            "Source-review worksheet overview missing required terms: " + ", ".join(missing)
        )


def _render_overview_doc(overview: pd.DataFrame) -> str:
    total = _overview_row(overview, "TOTAL")
    display = overview[
        [
            "overview_order",
            "thesis_area",
            "worksheet_rows",
            "unique_sources",
            "pending_citation_rows",
            "final_release_ready_rows",
            "selected_tables",
            "selected_figures",
            "boundary_terms_de",
            "next_action_de",
        ]
    ]
    return (
        "# Source Review Worksheet Overview\n\n"
        "Diese Uebersicht konsolidiert die H1-, H2- und H3-Worksheets fuer "
        "die manuelle Source Review. Sie liest keine Quelleninhalte, trifft "
        "keine Claim-Support-Entscheide, promotet keinen Quellenstatus und "
        "erzeugt keine finale Zitation.\n\n"
        "## Counts\n\n"
        f"- Overview rows: {len(overview)}\n"
        f"- Worksheet rows: {int(total['worksheet_rows'])}\n"
        f"- Unique sources: {int(total['unique_sources'])}\n"
        f"- Method rows: {int(total['method_rows'])}\n"
        f"- Interpretation rows: {int(total['interpretation_rows'])}\n"
        f"- External locator rows: {int(total['external_locator_rows'])}\n"
        f"- Local PDF rows: {int(total['local_pdf_rows'])}\n"
        f"- Pending citation rows: {int(total['pending_citation_rows'])}\n"
        f"- Final release ready rows: {int(total['final_release_ready_rows'])}\n\n"
        "## Overview Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Arbeite die Worksheets in der Reihenfolge H1, H2, H3 und danach "
        "TOTAL-Rebuild ab. Jede Zeile braucht Page-/Section-Note, "
        "Claim-Support, Blocked-Wording, Citation-Use und Reviewer-Metadaten. "
        "H2 behaelt die Kausalclaim-Grenze; H3 behaelt Granger-Grenze und "
        "Wallet-Grenze. Keine finale Zitation, keine Quellenstatus-Hochstufung, "
        "keine Wallet-Adressen, keine Trading-Claims, keine "
        "Profitabilitaetsclaims und keine Runtime-Agenten.\n"
    )


def _boundary_terms(area: str) -> str:
    if area == "H1":
        return (
            "Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use; "
            "H1 broad-claim boundary; keine allgemeine Marktueberlegenheit."
        )
    if area == "H2":
        return (
            "Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use; "
            "H2 Kausalclaim-Grenze; keine Intraday- oder Kausalclaims."
        )
    if area == "H3":
        return (
            "Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use; "
            "H3 Granger-Grenze und Wallet-Grenze; keine Wallet-Adressen oder Trading-Claims."
        )
    return ""


def _next_action(area: str) -> str:
    if area == "H1":
        return "H1 Worksheet row-by-row manuell ausfuellen."
    if area == "H2":
        return "H2 Worksheet mit Kausalclaim-Grenze row-by-row manuell ausfuellen."
    if area == "H3":
        return "H3 Worksheet mit Granger-Grenze und Wallet-Grenze row-by-row manuell ausfuellen."
    return ""


def _blocked_actions(area: str) -> str:
    base = "Keine finale Zitation, keine Quellenstatus-Hochstufung und keine Runtime-Agenten."
    if area == "H1":
        return base + " Keine allgemeine Marktueberlegenheit."
    if area == "H2":
        return base + " Keine Kausalclaims und keine Intraday-Ueberclaims."
    if area == "H3":
        return (
            base
            + " Keine Kausalclaims, keine Wallet-Adressen, keine Trading-Claims "
            "und keine Profitabilitaetsclaims."
        )
    return base


def _overview_row(overview: pd.DataFrame, thesis_area: str) -> pd.Series:
    rows = overview.loc[overview["thesis_area"] == thesis_area]
    if len(rows) != 1:
        raise ValueError(f"Expected one worksheet overview row for {thesis_area}.")
    return rows.iloc[0]


def _unique_join(values: pd.Series) -> str:
    return ", ".join(sorted({_clean(value) for value in values if _clean(value)}))


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required source-review worksheet overview input missing: {path}")
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
