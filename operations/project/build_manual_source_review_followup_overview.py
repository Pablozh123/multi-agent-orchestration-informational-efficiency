"""Build a compact H1-H2-H3 manual source-review follow-up overview."""

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

OVERVIEW_OUTPUT = "thesis_manual_source_review_followup_overview.csv"
OVERVIEW_DOC_OUTPUT = "THESIS_MANUAL_SOURCE_REVIEW_FOLLOWUP_OVERVIEW.md"

OVERVIEW_COLUMNS: tuple[str, ...] = (
    "overview_id",
    "slice_id",
    "followup_doc",
    "followup_csv",
    "review_rows",
    "unique_sources",
    "method_rows",
    "interpretation_rows",
    "external_locator_rows",
    "local_pdf_rows",
    "pending_rows",
    "final_ready_rows",
    "selected_tables",
    "selected_figures",
    "manual_gate_de",
    "guardrail_de",
    "next_action_de",
)

COMMON_FOLLOWUP_COLUMNS: tuple[str, ...] = (
    "source_id",
    "item_type",
    "access_route",
    "current_review_status",
    "final_citation_ready",
    "selected_table",
    "selected_figure",
)

SLICE_CONFIGS: tuple[dict[str, str], ...] = (
    {
        "slice_id": "H1",
        "csv": "thesis_h1_manual_source_review_followup.csv",
        "doc": "THESIS_H1_MANUAL_SOURCE_REVIEW_FOLLOWUP.md",
        "manual_gate_de": "Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use fuer 10 H1-Zeilen.",
        "guardrail_de": "Keine finale Zitation, keine Quellenstatus-Hochstufung, keine Rohartefakt-Dumps und keine Runtime-Agenten.",
    },
    {
        "slice_id": "H2",
        "csv": "thesis_h2_manual_source_review_followup.csv",
        "doc": "THESIS_H2_MANUAL_SOURCE_REVIEW_FOLLOWUP.md",
        "manual_gate_de": "Page-/Section-Note, Claim-Support, Blocked-Wording, Citation-Use und Kausalclaim-Grenze fuer 5 H2-Zeilen.",
        "guardrail_de": "Keine finale Zitation, keine Kausalclaims, keine Quellenstatus-Hochstufung, keine Rohartefakt-Dumps und keine Runtime-Agenten.",
    },
    {
        "slice_id": "H3",
        "csv": "thesis_h3_manual_source_review_followup.csv",
        "doc": "THESIS_H3_MANUAL_SOURCE_REVIEW_FOLLOWUP.md",
        "manual_gate_de": "Page-/Section-Note, Claim-Support, Blocked-Wording, Citation-Use, Granger-Grenze und Wallet-Grenze fuer 8 H3-Zeilen.",
        "guardrail_de": "Granger nicht kausal, keine willkuerlichen Whale-Schwellen, keine Wallet-Adressen, keine Trading-Claims, keine Profitabilitaetsclaims und keine Runtime-Agenten.",
    },
)


@dataclass(frozen=True)
class ManualSourceReviewFollowupOverviewResult:
    """Generated overview paths and aggregate counts."""

    overview_path: Path
    docs_path: Path
    overview_rows: int
    total_review_rows: int
    total_unique_sources: int
    total_pending_rows: int
    total_final_ready_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "overview_path": str(self.overview_path),
            "docs_path": str(self.docs_path),
            "overview_rows": self.overview_rows,
            "total_review_rows": self.total_review_rows,
            "total_unique_sources": self.total_unique_sources,
            "total_pending_rows": self.total_pending_rows,
            "total_final_ready_rows": self.total_final_ready_rows,
        }


def generate_manual_source_review_followup_overview(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> ManualSourceReviewFollowupOverviewResult:
    """Generate a compact overview of the H1-H2-H3 manual review slices."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    overview, combined = build_manual_source_review_followup_overview(
        results_dir=results_dir,
        docs_dir=docs_dir,
    )
    _validate_overview(overview=overview, combined=combined, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    overview_path = results_dir / OVERVIEW_OUTPUT
    docs_path = docs_dir / OVERVIEW_DOC_OUTPUT
    overview.to_csv(overview_path, index=False)
    docs_path.write_text(_render_overview_doc(overview=overview, combined=combined), encoding="utf-8")

    return ManualSourceReviewFollowupOverviewResult(
        overview_path=overview_path,
        docs_path=docs_path,
        overview_rows=len(overview),
        total_review_rows=len(combined),
        total_unique_sources=int(combined["source_id"].nunique()),
        total_pending_rows=int((combined["current_review_status"] == "pending_manual_review").sum()),
        total_final_ready_rows=int(combined["final_citation_ready"].map(_bool_value).sum()),
    )


def build_manual_source_review_followup_overview(
    *,
    results_dir: Path,
    docs_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return the three-row overview and combined source-review rows."""

    rows: list[dict[str, object]] = []
    combined_parts: list[pd.DataFrame] = []

    for config in SLICE_CONFIGS:
        slice_id = config["slice_id"]
        followup_csv = results_dir / config["csv"]
        followup_doc = docs_dir / config["doc"]
        if not followup_doc.exists():
            raise FileNotFoundError(f"Manual source-review follow-up doc missing: {followup_doc}")
        frame = _read_csv(followup_csv)
        _require_columns(frame, COMMON_FOLLOWUP_COLUMNS, f"{slice_id} manual source-review follow-up")
        frame = frame.copy()
        frame["slice_id"] = slice_id
        combined_parts.append(frame)
        item_counts = frame["item_type"].value_counts().to_dict()
        access_counts = frame["access_route"].value_counts().to_dict()
        rows.append(
            {
                "overview_id": f"manual_source_review_followup_{slice_id.lower()}",
                "slice_id": slice_id,
                "followup_doc": str(Path("docs/project") / config["doc"]),
                "followup_csv": str(Path("data/results") / config["csv"]),
                "review_rows": len(frame),
                "unique_sources": int(frame["source_id"].nunique()),
                "method_rows": int(item_counts.get("method", 0)),
                "interpretation_rows": int(item_counts.get("interpretation", 0)),
                "external_locator_rows": int(access_counts.get("external_locator_review", 0)),
                "local_pdf_rows": int(access_counts.get("local_pdf_review", 0)),
                "pending_rows": int((frame["current_review_status"] == "pending_manual_review").sum()),
                "final_ready_rows": int(frame["final_citation_ready"].map(_bool_value).sum()),
                "selected_tables": _join_unique(frame["selected_table"]),
                "selected_figures": _join_unique(frame["selected_figure"]),
                "manual_gate_de": config["manual_gate_de"],
                "guardrail_de": config["guardrail_de"],
                "next_action_de": (
                    f"{slice_id} manuell source-by-source pruefen; erst danach "
                    "Ledger-Entscheide und bounded BA-Prosa aktualisieren."
                ),
            }
        )

    combined = pd.concat(combined_parts, ignore_index=True)
    return pd.DataFrame(rows, columns=OVERVIEW_COLUMNS), combined


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_manual_source_review_followup_overview(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_overview(
    *,
    overview: pd.DataFrame,
    combined: pd.DataFrame,
    repo_root: Path,
) -> None:
    _require_columns(overview, OVERVIEW_COLUMNS, "manual source-review follow-up overview")
    if len(overview) != 3:
        raise ValueError("Manual source-review follow-up overview must contain exactly 3 rows.")
    if overview["slice_id"].tolist() != ["H1", "H2", "H3"]:
        raise ValueError("Manual source-review follow-up overview must be ordered H1, H2, H3.")
    if len(combined) != 23:
        raise ValueError("Combined H1-H2-H3 follow-up rows must contain exactly 23 rows.")
    if combined["source_id"].nunique() != 9:
        raise ValueError("Combined H1-H2-H3 follow-up rows must contain exactly 9 unique sources.")
    item_counts = combined["item_type"].value_counts().to_dict()
    if item_counts.get("method", 0) != 12 or item_counts.get("interpretation", 0) != 11:
        raise ValueError("Combined H1-H2-H3 follow-up rows must contain 12 methods and 11 interpretations.")
    if (combined["current_review_status"] != "pending_manual_review").any():
        raise ValueError("All combined H1-H2-H3 follow-up rows must remain pending.")
    if combined["final_citation_ready"].map(_bool_value).any():
        raise ValueError("No combined H1-H2-H3 follow-up row may be final-citation-ready.")
    for row in overview.to_dict(orient="records"):
        for path_column in ("followup_doc", "followup_csv"):
            artifact = str(row[path_column])
            if not (repo_root / artifact).exists():
                raise FileNotFoundError(f"Overview artifact reference missing: {artifact}")
    joined = "\n".join(overview.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Manual source-review follow-up overview must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "page-/section-note",
        "claim-support",
        "blocked-wording",
        "citation-use",
        "keine finale zitation",
        "keine quellenstatus-hochstufung",
        "keine runtime-agenten",
        "granger nicht kausal",
        "keine willkuerlichen whale-schwellen",
        "keine wallet-adressen",
        "keine trading-claims",
        "keine profitabilitaetsclaims",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Manual source-review follow-up overview missing required terms: " + ", ".join(missing))


def _render_overview_doc(*, overview: pd.DataFrame, combined: pd.DataFrame) -> str:
    item_counts = combined["item_type"].value_counts().to_dict()
    access_counts = combined["access_route"].value_counts().to_dict()
    final_ready_rows = int(combined["final_citation_ready"].map(_bool_value).sum())
    display = overview[
        [
            "slice_id",
            "review_rows",
            "unique_sources",
            "method_rows",
            "interpretation_rows",
            "pending_rows",
            "final_ready_rows",
            "selected_tables",
            "selected_figures",
            "next_action_de",
        ]
    ]
    return (
        "# Manual Source Review Follow-up Overview\n\n"
        "Diese Uebersicht konsolidiert die drei H1-H2-H3 Source-Review-"
        "Starterlisten in eine kompakte Arbeitssteuerung. Sie liest nur die "
        "deterministisch erzeugten Follow-up CSVs, trifft keine "
        "Claim-Support-Entscheide, promotet keinen Quellenstatus und macht "
        "keine finale Zitation.\n\n"
        "## Counts\n\n"
        f"- Overview rows: {len(overview)}\n"
        f"- Total manual review rows: {len(combined)}\n"
        f"- Unique sources across H1-H2-H3: {int(combined['source_id'].nunique())}\n"
        f"- Method rows: {int(item_counts.get('method', 0))}\n"
        f"- Interpretation rows: {int(item_counts.get('interpretation', 0))}\n"
        f"- External locator rows: {int(access_counts.get('external_locator_review', 0))}\n"
        f"- Local PDF rows: {int(access_counts.get('local_pdf_review', 0))}\n"
        f"- Pending rows: {int((combined['current_review_status'] == 'pending_manual_review').sum())}\n"
        f"- Final citation ready rows: {final_ready_rows}\n\n"
        "## Slice Overview\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Arbeite die Review in der Reihenfolge H1, H2, H3 ab. Fuer jede Zeile "
        "in den Detaildateien muessen Page-/Section-Note, Claim-Support, "
        "Blocked-Wording und Citation-Use manuell gesetzt werden. H2 bleibt "
        "ohne Kausalclaims. H3 bleibt ohne kausale Granger-Deutung, ohne "
        "willkuerliche Whale-Schwellen, ohne Wallet-Adressen, ohne "
        "Trading-Claims und ohne Profitabilitaetsclaims. Bis die Ledger-Felder "
        "manuell belegt sind, bleiben alle 23 H1-H2-H3 Zitationen final "
        "blockiert. Keine Quellenstatus-Hochstufung, keine Rohartefakt-Dumps, "
        "keine Runtime-Agenten, kein MCP, kein Model Routing und keine "
        "LLM-Metriken.\n"
    )


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required manual source-review follow-up input missing: {path}")
    return pd.read_csv(path)


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "ja"}


def _join_unique(values: pd.Series) -> str:
    unique_values = [str(value).strip() for value in values.dropna().unique() if str(value).strip()]
    return ", ".join(unique_values)


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
