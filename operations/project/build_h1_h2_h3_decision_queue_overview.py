"""Build a compact H1-H2-H3 source-review decision-queue overview."""

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

OVERVIEW_OUTPUT = "thesis_h1_h2_h3_decision_queue_overview.csv"
OVERVIEW_DOC_OUTPUT = "THESIS_H1_H2_H3_DECISION_QUEUE_OVERVIEW.md"

OVERVIEW_COLUMNS: tuple[str, ...] = (
    "overview_id",
    "slice_id",
    "decision_queue_doc",
    "decision_queue_csv",
    "decision_rows",
    "unique_sources",
    "method_rows",
    "interpretation_rows",
    "external_locator_rows",
    "local_pdf_rows",
    "pending_queue_rows",
    "final_ready_rows",
    "source_status_change_rows",
    "selected_tables",
    "selected_figures",
    "queue_statuses",
    "manual_decision_fields_de",
    "decision_gate_de",
    "guardrail_de",
    "next_action_de",
)

COMMON_QUEUE_COLUMNS: tuple[str, ...] = (
    "source_id",
    "evidence_id",
    "item_type",
    "access_route",
    "selected_table",
    "selected_figure",
    "primary_artifact_exists",
    "current_review_status",
    "required_manual_decision_fields_de",
    "agent_assist_boundary_de",
    "source_status_change_allowed",
    "final_citation_ready",
    "queue_status",
)

SLICE_CONFIGS: tuple[dict[str, object], ...] = (
    {
        "slice_id": "H1",
        "csv": "thesis_h1_source_review_decision_queue.csv",
        "doc": "THESIS_H1_SOURCE_REVIEW_DECISION_QUEUE.md",
        "expected_rows": 10,
        "selected_table": "T2",
        "selected_figure": "F1",
        "expected_status": "pending_manual_h1_source_review",
        "decision_gate_de": (
            "H1 erst nach manueller Page-/Section-Note, Claim-Support, "
            "Blocked-Wording und Citation-Use in finale BA-Prosa ueberfuehren."
        ),
        "guardrail_de": (
            "Keine finale Zitation, keine Quellenstatus-Hochstufung, keine "
            "Runtime-Agenten, keine Rohartefakt-Dumps und keine Kennzahlen "
            "aus LLMs."
        ),
    },
    {
        "slice_id": "H2",
        "csv": "thesis_h2_source_review_decision_queue.csv",
        "doc": "THESIS_H2_SOURCE_REVIEW_DECISION_QUEUE.md",
        "expected_rows": 5,
        "selected_table": "T3",
        "selected_figure": "F2",
        "expected_status": "pending_manual_h2_source_review",
        "decision_gate_de": (
            "H2 erst nach manueller Page-/Section-Note, Claim-Support, "
            "Blocked-Wording, Citation-Use und Kausalclaim-Grenze final "
            "verwenden."
        ),
        "guardrail_de": (
            "Keine Intraday-Claims, keine Kausalclaims, keine finale "
            "Zitation, keine Quellenstatus-Hochstufung, keine Runtime-Agenten "
            "und keine Kennzahlen aus LLMs."
        ),
    },
    {
        "slice_id": "H3",
        "csv": "thesis_h3_source_review_decision_queue.csv",
        "doc": "THESIS_H3_SOURCE_REVIEW_DECISION_QUEUE.md",
        "expected_rows": 8,
        "selected_table": "T4",
        "selected_figure": "F3",
        "expected_status": "pending_manual_h3_source_review",
        "decision_gate_de": (
            "H3 erst nach manueller Page-/Section-Note, Claim-Support, "
            "Blocked-Wording, Citation-Use, Granger-Grenze und Wallet-Grenze "
            "final verwenden."
        ),
        "guardrail_de": (
            "Granger nicht kausal deuten; keine willkuerlichen "
            "Whale-Schwellen, keine Wallet-Adressen, keine Trading-Claims, "
            "keine Profitabilitaetsclaims, keine finale Zitation und keine "
            "Runtime-Agenten."
        ),
    },
)


@dataclass(frozen=True)
class H1H2H3DecisionQueueOverviewResult:
    """Generated overview paths and aggregate counts."""

    overview_path: Path
    docs_path: Path
    overview_rows: int
    total_decision_rows: int
    total_unique_sources: int
    total_pending_queue_rows: int
    total_final_ready_rows: int
    source_status_change_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "overview_path": str(self.overview_path),
            "docs_path": str(self.docs_path),
            "overview_rows": self.overview_rows,
            "total_decision_rows": self.total_decision_rows,
            "total_unique_sources": self.total_unique_sources,
            "total_pending_queue_rows": self.total_pending_queue_rows,
            "total_final_ready_rows": self.total_final_ready_rows,
            "source_status_change_rows": self.source_status_change_rows,
        }


def generate_h1_h2_h3_decision_queue_overview(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> H1H2H3DecisionQueueOverviewResult:
    """Generate the H1-H2-H3 decision-queue overview CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    overview, combined = build_h1_h2_h3_decision_queue_overview(
        results_dir=results_dir,
        docs_dir=docs_dir,
    )
    _validate_overview(overview=overview, combined=combined, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    overview_path = results_dir / OVERVIEW_OUTPUT
    docs_path = docs_dir / OVERVIEW_DOC_OUTPUT
    overview.to_csv(overview_path, index=False)
    docs_path.write_text(
        _render_overview_doc(overview=overview, combined=combined),
        encoding="utf-8",
    )

    return H1H2H3DecisionQueueOverviewResult(
        overview_path=overview_path,
        docs_path=docs_path,
        overview_rows=len(overview),
        total_decision_rows=len(combined),
        total_unique_sources=int(combined["source_id"].nunique()),
        total_pending_queue_rows=int(combined["queue_status"].str.startswith("pending_manual_").sum()),
        total_final_ready_rows=int(combined["final_citation_ready"].map(_bool_value).sum()),
        source_status_change_rows=int(combined["source_status_change_allowed"].map(_bool_value).sum()),
    )


def build_h1_h2_h3_decision_queue_overview(
    *,
    results_dir: Path,
    docs_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return a three-row overview and combined decision-queue rows."""

    rows: list[dict[str, object]] = []
    combined_parts: list[pd.DataFrame] = []

    for config in SLICE_CONFIGS:
        slice_id = str(config["slice_id"])
        queue_csv = results_dir / str(config["csv"])
        queue_doc = docs_dir / str(config["doc"])
        if not queue_doc.exists():
            raise FileNotFoundError(f"Decision queue doc missing: {queue_doc}")

        frame = _read_csv(queue_csv)
        _require_columns(frame, COMMON_QUEUE_COLUMNS, f"{slice_id} source-review decision queue")
        frame = frame.copy()
        frame["slice_id"] = slice_id
        combined_parts.append(frame)

        item_counts = frame["item_type"].value_counts().to_dict()
        access_counts = frame["access_route"].value_counts().to_dict()
        rows.append(
            {
                "overview_id": f"h1_h2_h3_decision_queue_{slice_id.lower()}",
                "slice_id": slice_id,
                "decision_queue_doc": str(Path("docs/project") / str(config["doc"])),
                "decision_queue_csv": str(Path("data/results") / str(config["csv"])),
                "decision_rows": len(frame),
                "unique_sources": int(frame["source_id"].nunique()),
                "method_rows": int(item_counts.get("method", 0)),
                "interpretation_rows": int(item_counts.get("interpretation", 0)),
                "external_locator_rows": int(access_counts.get("external_locator_review", 0)),
                "local_pdf_rows": int(access_counts.get("local_pdf_review", 0)),
                "pending_queue_rows": int(frame["queue_status"].str.startswith("pending_manual_").sum()),
                "final_ready_rows": int(frame["final_citation_ready"].map(_bool_value).sum()),
                "source_status_change_rows": int(
                    frame["source_status_change_allowed"].map(_bool_value).sum()
                ),
                "selected_tables": _join_unique(frame["selected_table"]),
                "selected_figures": _join_unique(frame["selected_figure"]),
                "queue_statuses": _join_unique(frame["queue_status"]),
                "manual_decision_fields_de": _join_unique(frame["required_manual_decision_fields_de"]),
                "decision_gate_de": str(config["decision_gate_de"]),
                "guardrail_de": str(config["guardrail_de"]),
                "next_action_de": (
                    f"{slice_id} Decision Queue source-by-source manuell bearbeiten; "
                    "danach Ledger und bounded BA-Prosa aktualisieren, aber keine "
                    "Zitation freigeben, solange Reviewfelder offen sind."
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
        result = generate_h1_h2_h3_decision_queue_overview(
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
    _require_columns(overview, OVERVIEW_COLUMNS, "H1-H2-H3 decision-queue overview")
    if len(overview) != 3:
        raise ValueError("H1-H2-H3 decision-queue overview must contain exactly 3 rows.")
    if overview["slice_id"].tolist() != ["H1", "H2", "H3"]:
        raise ValueError("H1-H2-H3 decision-queue overview must be ordered H1, H2, H3.")
    if len(combined) != 23:
        raise ValueError("Combined H1-H2-H3 decision rows must contain exactly 23 rows.")
    if combined["source_id"].nunique() != 9:
        raise ValueError("Combined H1-H2-H3 decision rows must contain exactly 9 unique sources.")

    for config in SLICE_CONFIGS:
        slice_id = str(config["slice_id"])
        slice_frame = combined[combined["slice_id"] == slice_id]
        if len(slice_frame) != int(config["expected_rows"]):
            raise ValueError(f"{slice_id} decision queue row count does not match expected rows.")
        if set(slice_frame["selected_table"].astype(str)) != {str(config["selected_table"])}:
            raise ValueError(f"{slice_id} decision queue selected table drifted.")
        if set(slice_frame["selected_figure"].astype(str)) != {str(config["selected_figure"])}:
            raise ValueError(f"{slice_id} decision queue selected figure drifted.")
        if set(slice_frame["queue_status"].astype(str)) != {str(config["expected_status"])}:
            raise ValueError(f"{slice_id} decision queue status drifted.")

    item_counts = combined["item_type"].value_counts().to_dict()
    if item_counts.get("method", 0) != 12 or item_counts.get("interpretation", 0) != 11:
        raise ValueError("Combined H1-H2-H3 decision rows must contain 12 methods and 11 interpretations.")
    access_counts = combined["access_route"].value_counts().to_dict()
    if access_counts.get("external_locator_review", 0) != 13:
        raise ValueError("Combined H1-H2-H3 decision rows must contain 13 external locator rows.")
    if access_counts.get("local_pdf_review", 0) != 10:
        raise ValueError("Combined H1-H2-H3 decision rows must contain 10 local PDF rows.")
    if not combined["queue_status"].astype(str).str.startswith("pending_manual_").all():
        raise ValueError("All combined H1-H2-H3 decision rows must remain pending.")
    if combined["final_citation_ready"].map(_bool_value).any():
        raise ValueError("No combined H1-H2-H3 decision row may be final-citation-ready.")
    if combined["source_status_change_allowed"].map(_bool_value).any():
        raise ValueError("No combined H1-H2-H3 decision row may allow source-status changes.")
    if not combined["primary_artifact_exists"].map(_bool_value).all():
        raise ValueError("Combined H1-H2-H3 decision rows contain missing deterministic artifacts.")

    for row in overview.to_dict(orient="records"):
        for path_column in ("decision_queue_doc", "decision_queue_csv"):
            artifact = str(row[path_column])
            if not (repo_root / artifact).exists():
                raise FileNotFoundError(f"Overview artifact reference missing: {artifact}")

    joined = "\n".join([_join_frame_rows(overview), _join_frame_rows(combined)])
    if chr(223) in joined:
        raise ValueError("H1-H2-H3 decision-queue overview must use Swiss spelling without sharp-s.")
    required_terms = (
        "Page-/Section-Note",
        "Claim-Support",
        "Blocked-Wording",
        "Citation-Use",
        "Kausalclaim-Grenze",
        "Granger-Grenze",
        "Wallet-Grenze",
        "keine finale Zitation",
        "keine Quellenstatus-Hochstufung",
        "keine Runtime-Agenten",
        "max 50 rows",
        "llm_audit_log",
        "keine Kennzahlen",
        "keine Zitation freigeben",
        "keine Wallet-Adressen",
        "keine Trading-Claims",
        "keine Profitabilitaetsclaims",
    )
    missing = [term for term in required_terms if term not in joined]
    if missing:
        raise ValueError("H1-H2-H3 decision-queue overview missing required terms: " + ", ".join(missing))


def _render_overview_doc(*, overview: pd.DataFrame, combined: pd.DataFrame) -> str:
    item_counts = combined["item_type"].value_counts().to_dict()
    access_counts = combined["access_route"].value_counts().to_dict()
    final_ready_rows = int(combined["final_citation_ready"].map(_bool_value).sum())
    source_status_change_rows = int(combined["source_status_change_allowed"].map(_bool_value).sum())
    display = overview[
        [
            "slice_id",
            "decision_rows",
            "unique_sources",
            "method_rows",
            "interpretation_rows",
            "pending_queue_rows",
            "final_ready_rows",
            "source_status_change_rows",
            "selected_tables",
            "selected_figures",
            "queue_statuses",
            "next_action_de",
        ]
    ]
    return (
        "# H1-H2-H3 Decision Queue Overview\n\n"
        "Diese Uebersicht konsolidiert die drei H1-H2-H3 Source Review "
        "Decision Queues in ein kompaktes Steuerungsartefakt. Sie liest nur "
        "deterministisch erzeugte Queue-CSVs, liest keine Quelleninhalte, "
        "setzt keine Page-/Section-Notes, trifft keine Claim-Support-"
        "Entscheide, promotet keinen Quellenstatus und macht keine finale "
        "Zitation.\n\n"
        "## Counts\n\n"
        f"- Overview rows: {len(overview)}\n"
        f"- Total decision rows: {len(combined)}\n"
        f"- Unique sources across H1-H2-H3: {int(combined['source_id'].nunique())}\n"
        f"- Method rows: {int(item_counts.get('method', 0))}\n"
        f"- Interpretation rows: {int(item_counts.get('interpretation', 0))}\n"
        f"- External locator rows: {int(access_counts.get('external_locator_review', 0))}\n"
        f"- Local PDF rows: {int(access_counts.get('local_pdf_review', 0))}\n"
        f"- Pending queue rows: {int(combined['queue_status'].str.startswith('pending_manual_').sum())}\n"
        f"- Final citation ready rows: {final_ready_rows}\n"
        f"- Source-status change rows: {source_status_change_rows}\n\n"
        "## Queue Overview\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Arbeite die Review in der Reihenfolge H1, H2, H3 ab. Jede Queue-Zeile "
        "braucht manuell gesetzte Page-/Section-Note, Claim-Support, "
        "Blocked-Wording und Citation-Use. H2 braucht zusaetzlich die "
        "Kausalclaim-Grenze. H3 braucht zusaetzlich Granger-Grenze und "
        "Wallet-Grenze. Bis diese Felder belegt und im Ledger kontrolliert "
        "sind, bleiben alle 23 H1-H2-H3 Decision Rows final blockiert: keine "
        "finale Zitation, keine Quellenstatus-Hochstufung, keine "
        "Rohartefakt-Dumps, keine Runtime-Agenten, kein MCP, kein Model "
        "Routing und keine LLM-Metriken.\n\n"
        "## Future Agent Boundary\n\n"
        "Spaetere Agentenhilfe darf nur fehlende Felder markieren, Evidence "
        "IDs spiegeln oder kompakte To-do-Hinweise aus maximal 50 rows "
        "erzeugen. Jede spaetere Nutzung braucht ein separates Goal, Tests "
        "und `llm_audit_log`. Agenten duerfen keine Quelleninhalte bewerten, "
        "keine Seitenzahlen erfinden, keine Kennzahlen berechnen, keine "
        "Zitation freigeben, keine Kausalclaims lockern, keine "
        "Wallet-Adressen ausgeben, keine Trading-Claims und keine "
        "Profitabilitaetsclaims formulieren.\n"
    )


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required decision-queue input missing: {path}")
    return pd.read_csv(path)


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "ja", "y"}


def _join_unique(values: pd.Series) -> str:
    unique_values = [str(value).strip() for value in values.dropna().unique() if str(value).strip()]
    return ", ".join(unique_values)


def _join_frame_rows(frame: pd.DataFrame) -> str:
    return "\n".join(
        " ".join(str(value) for value in row)
        for row in frame.fillna("").to_numpy(dtype=object)
    )


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
