"""Align H1-H2-H3 decision queues with the source-review progress ledger."""

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

ALIGNMENT_OUTPUT = "thesis_h1_h2_h3_decision_queue_ledger_alignment.csv"
ALIGNMENT_DOC_OUTPUT = "THESIS_H1_H2_H3_DECISION_QUEUE_LEDGER_ALIGNMENT.md"

OVERVIEW_INPUT = "thesis_h1_h2_h3_decision_queue_overview.csv"
LEDGER_INPUT = "thesis_source_review_progress_ledger.csv"

ALIGNMENT_COLUMNS: tuple[str, ...] = (
    "alignment_id",
    "slice_id",
    "decision_queue_rows",
    "overview_decision_rows",
    "ledger_rows",
    "matched_rows",
    "queue_missing_ledger_rows",
    "ledger_missing_queue_rows",
    "field_mismatch_rows",
    "queue_pending_rows",
    "ledger_pending_rows",
    "queue_final_ready_rows",
    "ledger_final_ready_rows",
    "queue_source_status_change_rows",
    "ledger_source_status_change_rows",
    "selected_tables",
    "selected_figures",
    "overview_count_match",
    "alignment_status",
    "ledger_gate_de",
    "next_action_de",
)

QUEUE_REQUIRED_COLUMNS: tuple[str, ...] = (
    "source_id",
    "evidence_id",
    "item_type",
    "access_route",
    "deterministic_artifact",
    "selected_table",
    "selected_figure",
    "queue_status",
    "source_status_change_allowed",
    "final_citation_ready",
)

LEDGER_REQUIRED_COLUMNS: tuple[str, ...] = (
    "note_id",
    "thesis_area",
    "source_id",
    "evidence_id",
    "item_type",
    "access_route",
    "deterministic_artifact",
    "selected_table",
    "selected_figure",
    "review_progress_state",
    "source_status_change_allowed",
    "final_citation_ready",
)

OVERVIEW_REQUIRED_COLUMNS: tuple[str, ...] = (
    "slice_id",
    "decision_rows",
    "pending_queue_rows",
    "final_ready_rows",
    "source_status_change_rows",
    "selected_tables",
    "selected_figures",
)

MATCH_FIELDS: tuple[str, ...] = (
    "item_type",
    "access_route",
    "deterministic_artifact",
    "selected_table",
    "selected_figure",
)

SLICE_CONFIGS: tuple[dict[str, str], ...] = (
    {
        "slice_id": "H1",
        "csv": "thesis_h1_source_review_decision_queue.csv",
        "doc": "THESIS_H1_SOURCE_REVIEW_DECISION_QUEUE.md",
        "table": "T2",
        "figure": "F1",
        "gate": "H1 bleibt bis zur Ledger-Entscheidung fuer Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use final blockiert.",
    },
    {
        "slice_id": "H2",
        "csv": "thesis_h2_source_review_decision_queue.csv",
        "doc": "THESIS_H2_SOURCE_REVIEW_DECISION_QUEUE.md",
        "table": "T3",
        "figure": "F2",
        "gate": "H2 bleibt bis zur Ledger-Entscheidung fuer Page-/Section-Note, Claim-Support, Blocked-Wording, Citation-Use und Kausalclaim-Grenze final blockiert.",
    },
    {
        "slice_id": "H3",
        "csv": "thesis_h3_source_review_decision_queue.csv",
        "doc": "THESIS_H3_SOURCE_REVIEW_DECISION_QUEUE.md",
        "table": "T4",
        "figure": "F3",
        "gate": "H3 bleibt bis zur Ledger-Entscheidung fuer Page-/Section-Note, Claim-Support, Blocked-Wording, Citation-Use, Granger-Grenze und Wallet-Grenze final blockiert.",
    },
)


@dataclass(frozen=True)
class H1H2H3DecisionQueueLedgerAlignmentResult:
    """Generated alignment paths and aggregate counts."""

    alignment_path: Path
    docs_path: Path
    alignment_rows: int
    total_queue_rows: int
    total_ledger_rows: int
    total_matched_rows: int
    total_missing_rows: int
    total_field_mismatch_rows: int
    total_final_ready_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "alignment_path": str(self.alignment_path),
            "docs_path": str(self.docs_path),
            "alignment_rows": self.alignment_rows,
            "total_queue_rows": self.total_queue_rows,
            "total_ledger_rows": self.total_ledger_rows,
            "total_matched_rows": self.total_matched_rows,
            "total_missing_rows": self.total_missing_rows,
            "total_field_mismatch_rows": self.total_field_mismatch_rows,
            "total_final_ready_rows": self.total_final_ready_rows,
        }


def generate_h1_h2_h3_decision_queue_ledger_alignment(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> H1H2H3DecisionQueueLedgerAlignmentResult:
    """Generate the decision-queue-to-ledger alignment CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    alignment, combined_queue, ledger = build_h1_h2_h3_decision_queue_ledger_alignment(
        results_dir=results_dir,
        docs_dir=docs_dir,
    )
    _validate_alignment(
        alignment=alignment,
        combined_queue=combined_queue,
        ledger=ledger,
        repo_root=repo_root,
    )

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    alignment_path = results_dir / ALIGNMENT_OUTPUT
    docs_path = docs_dir / ALIGNMENT_DOC_OUTPUT
    alignment.to_csv(alignment_path, index=False)
    docs_path.write_text(
        _render_alignment_doc(alignment=alignment, combined_queue=combined_queue, ledger=ledger),
        encoding="utf-8",
    )

    return H1H2H3DecisionQueueLedgerAlignmentResult(
        alignment_path=alignment_path,
        docs_path=docs_path,
        alignment_rows=len(alignment),
        total_queue_rows=len(combined_queue),
        total_ledger_rows=len(ledger),
        total_matched_rows=int(alignment["matched_rows"].sum()),
        total_missing_rows=int(
            alignment["queue_missing_ledger_rows"].sum()
            + alignment["ledger_missing_queue_rows"].sum()
        ),
        total_field_mismatch_rows=int(alignment["field_mismatch_rows"].sum()),
        total_final_ready_rows=int(
            alignment["queue_final_ready_rows"].sum()
            + alignment["ledger_final_ready_rows"].sum()
        ),
    )


def build_h1_h2_h3_decision_queue_ledger_alignment(
    *,
    results_dir: Path,
    docs_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return slice alignment rows, combined queue rows, and ledger rows."""

    _required_file(docs_dir / "THESIS_H1_H2_H3_DECISION_QUEUE_OVERVIEW.md")
    _required_file(docs_dir / "THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md")
    overview = _read_csv(results_dir / OVERVIEW_INPUT)
    ledger = _read_csv(results_dir / LEDGER_INPUT)
    _require_columns(overview, OVERVIEW_REQUIRED_COLUMNS, "H1-H2-H3 decision queue overview")
    _require_columns(ledger, LEDGER_REQUIRED_COLUMNS, "source review progress ledger")

    combined_queue_parts: list[pd.DataFrame] = []
    for config in SLICE_CONFIGS:
        _required_file(docs_dir / config["doc"])
        frame = _read_csv(results_dir / config["csv"])
        _require_columns(frame, QUEUE_REQUIRED_COLUMNS, f"{config['slice_id']} decision queue")
        frame = frame.copy()
        frame["slice_id"] = config["slice_id"]
        combined_queue_parts.append(frame)

    combined_queue = pd.concat(combined_queue_parts, ignore_index=True)
    rows: list[dict[str, object]] = []
    overview_by_slice = overview.set_index("slice_id").to_dict(orient="index")

    for config in SLICE_CONFIGS:
        slice_id = config["slice_id"]
        queue_slice = combined_queue[combined_queue["slice_id"] == slice_id].copy()
        ledger_slice = ledger[ledger["thesis_area"] == slice_id].copy()
        overview_row = overview_by_slice.get(slice_id, {})
        matched, queue_missing, ledger_missing, field_mismatches = _match_slice(
            queue_slice=queue_slice,
            ledger_slice=ledger_slice,
        )
        overview_count_match = _overview_count_match(
            overview_row=overview_row,
            queue_slice=queue_slice,
        )
        queue_final = int(queue_slice["final_citation_ready"].map(_bool_value).sum())
        ledger_final = int(ledger_slice["final_citation_ready"].map(_bool_value).sum())
        rows.append(
            {
                "alignment_id": f"h1_h2_h3_decision_queue_ledger_{slice_id.lower()}",
                "slice_id": slice_id,
                "decision_queue_rows": len(queue_slice),
                "overview_decision_rows": int(overview_row.get("decision_rows", -1)),
                "ledger_rows": len(ledger_slice),
                "matched_rows": matched,
                "queue_missing_ledger_rows": queue_missing,
                "ledger_missing_queue_rows": ledger_missing,
                "field_mismatch_rows": field_mismatches,
                "queue_pending_rows": int(
                    queue_slice["queue_status"].astype(str).str.startswith("pending_manual_").sum()
                ),
                "ledger_pending_rows": int(
                    (ledger_slice["review_progress_state"] == "pending_manual_review").sum()
                ),
                "queue_final_ready_rows": queue_final,
                "ledger_final_ready_rows": ledger_final,
                "queue_source_status_change_rows": int(
                    queue_slice["source_status_change_allowed"].map(_bool_value).sum()
                ),
                "ledger_source_status_change_rows": int(
                    ledger_slice["source_status_change_allowed"].map(_bool_value).sum()
                ),
                "selected_tables": _join_unique(queue_slice["selected_table"]),
                "selected_figures": _join_unique(queue_slice["selected_figure"]),
                "overview_count_match": overview_count_match,
                "alignment_status": _alignment_status(
                    queue_missing=queue_missing,
                    ledger_missing=ledger_missing,
                    field_mismatches=field_mismatches,
                    queue_rows=len(queue_slice),
                    ledger_pending_rows=int(
                        (ledger_slice["review_progress_state"] == "pending_manual_review").sum()
                    ),
                    final_ready_rows=queue_final + ledger_final,
                ),
                "ledger_gate_de": config["gate"],
                "next_action_de": (
                    f"{slice_id}: Detail-Decision-Queue und Ledger sind ueber "
                    "`source_id` plus `evidence_id` abzugleichen; erst nach "
                    "manueller Ledger-Entscheidung bounded BA-Prosa aktualisieren. "
                    "Keine Runtime-Agenten."
                ),
            }
        )

    return pd.DataFrame(rows, columns=ALIGNMENT_COLUMNS), combined_queue, ledger


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_h1_h2_h3_decision_queue_ledger_alignment(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_alignment(
    *,
    alignment: pd.DataFrame,
    combined_queue: pd.DataFrame,
    ledger: pd.DataFrame,
    repo_root: Path,
) -> None:
    _require_columns(alignment, ALIGNMENT_COLUMNS, "H1-H2-H3 decision-queue ledger alignment")
    if len(alignment) != 3:
        raise ValueError("Decision-queue ledger alignment must contain exactly 3 rows.")
    if alignment["slice_id"].tolist() != ["H1", "H2", "H3"]:
        raise ValueError("Decision-queue ledger alignment must be ordered H1, H2, H3.")
    if len(combined_queue) != 23:
        raise ValueError("Combined decision queues must contain exactly 23 rows.")
    if len(ledger) != 23:
        raise ValueError("Source review progress ledger must contain exactly 23 rows.")
    if combined_queue["source_id"].nunique() != 9:
        raise ValueError("Combined decision queues must contain exactly 9 unique sources.")
    if ledger["source_id"].nunique() != 9:
        raise ValueError("Source review progress ledger must contain exactly 9 unique sources.")
    if int(alignment["matched_rows"].sum()) != 23:
        raise ValueError("All 23 decision rows must match ledger rows.")
    if int(alignment["queue_missing_ledger_rows"].sum()) != 0:
        raise ValueError("Decision rows are missing from the ledger.")
    if int(alignment["ledger_missing_queue_rows"].sum()) != 0:
        raise ValueError("Ledger rows are missing from decision queues.")
    if int(alignment["field_mismatch_rows"].sum()) != 0:
        raise ValueError("Decision queue and ledger field values are mismatched.")
    if not alignment["overview_count_match"].map(_bool_value).all():
        raise ValueError("Decision queue overview counts do not match detail queues.")
    if int(alignment["queue_final_ready_rows"].sum()) != 0:
        raise ValueError("Decision queues must not be final-citation-ready.")
    if int(alignment["ledger_final_ready_rows"].sum()) != 0:
        raise ValueError("Ledger rows must not be final-citation-ready for this control slice.")
    if int(alignment["queue_source_status_change_rows"].sum()) != 0:
        raise ValueError("Decision queues must not allow source-status changes.")
    if int(alignment["ledger_source_status_change_rows"].sum()) != 0:
        raise ValueError("Ledger rows must not allow source-status changes.")
    if set(alignment["alignment_status"]) != {"aligned_pending_manual_review"}:
        raise ValueError("All alignment rows must remain aligned and pending manual review.")

    for config in SLICE_CONFIGS:
        slice_id = config["slice_id"]
        row = alignment.loc[alignment["slice_id"] == slice_id].iloc[0]
        if row["selected_tables"] != config["table"]:
            raise ValueError(f"{slice_id} selected table mismatch.")
        if row["selected_figures"] != config["figure"]:
            raise ValueError(f"{slice_id} selected figure mismatch.")

    for artifact in (
        "docs/project/THESIS_H1_H2_H3_DECISION_QUEUE_OVERVIEW.md",
        "docs/project/THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md",
        f"docs/project/{ALIGNMENT_DOC_OUTPUT}",
        f"data/results/{ALIGNMENT_OUTPUT}",
    ):
        if artifact.endswith(ALIGNMENT_DOC_OUTPUT) or artifact.endswith(ALIGNMENT_OUTPUT):
            continue
        if not (repo_root / artifact).exists():
            raise FileNotFoundError(f"Alignment artifact reference missing: {artifact}")

    joined = "\n".join(
        [
            _join_frame_rows(alignment),
            _join_frame_rows(combined_queue),
            _join_frame_rows(ledger),
        ]
    )
    if chr(223) in joined:
        raise ValueError("Decision-queue ledger alignment must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "page-/section-note",
        "claim-support",
        "blocked-wording",
        "citation-use",
        "kausalclaim-grenze",
        "granger-grenze",
        "wallet-grenze",
        "keine quellenstatus-hochstufung",
        "keine finale zitation",
        "max 50 rows",
        "llm_audit_log",
        "keine kennzahlen",
        "keine runtime-agenten",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Decision-queue ledger alignment missing required terms: " + ", ".join(missing))


def _render_alignment_doc(
    *,
    alignment: pd.DataFrame,
    combined_queue: pd.DataFrame,
    ledger: pd.DataFrame,
) -> str:
    display = alignment[
        [
            "slice_id",
            "decision_queue_rows",
            "overview_decision_rows",
            "ledger_rows",
            "matched_rows",
            "queue_missing_ledger_rows",
            "ledger_missing_queue_rows",
            "field_mismatch_rows",
            "alignment_status",
            "next_action_de",
        ]
    ]
    return (
        "# H1-H2-H3 Decision Queue Ledger Alignment\n\n"
        "Dieses Artefakt gleicht die H1-H2-H3 Decision Queues, die "
        "Decision Queue Overview und das Source Review Progress Ledger "
        "strukturell ab. Es liest keine Quelleninhalte, trifft keine "
        "Claim-Support-Entscheide, setzt keine Page-/Section-Notes, promotet "
        "keinen Quellenstatus und macht keine finale Zitation.\n\n"
        "## Counts\n\n"
        f"- Alignment rows: {len(alignment)}\n"
        f"- Total decision queue rows: {len(combined_queue)}\n"
        f"- Total ledger rows: {len(ledger)}\n"
        f"- Matched rows: {int(alignment['matched_rows'].sum())}\n"
        f"- Queue rows missing ledger: {int(alignment['queue_missing_ledger_rows'].sum())}\n"
        f"- Ledger rows missing queue: {int(alignment['ledger_missing_queue_rows'].sum())}\n"
        f"- Field mismatch rows: {int(alignment['field_mismatch_rows'].sum())}\n"
        f"- Queue final-ready rows: {int(alignment['queue_final_ready_rows'].sum())}\n"
        f"- Ledger final-ready rows: {int(alignment['ledger_final_ready_rows'].sum())}\n"
        f"- Queue source-status change rows: {int(alignment['queue_source_status_change_rows'].sum())}\n"
        f"- Ledger source-status change rows: {int(alignment['ledger_source_status_change_rows'].sum())}\n\n"
        "## Alignment Overview\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze zuerst die H1-H2-H3 Decision Queue Overview fuer den "
        "3-Zeilen-Ueberblick, danach die Detail-Decision-Queues fuer die "
        "source-by-source Arbeit und dann das Source Review Progress Ledger "
        "zur dauerhaften Erfassung manueller Entscheidungen. Jede "
        "Ledger-Entscheidung braucht Page-/Section-Note, Claim-Support, "
        "Blocked-Wording und Citation-Use. H2 braucht zusaetzlich die "
        "Kausalclaim-Grenze; H3 braucht zusaetzlich Granger-Grenze und "
        "Wallet-Grenze. Bis die Ledger-Felder manuell belegt sind, bleiben "
        "alle 23 Rows final blockiert: keine finale Zitation, keine "
        "Quellenstatus-Hochstufung, keine Runtime-Agenten, keine "
        "Rohartefakt-Dumps und keine Kennzahlen aus LLMs.\n\n"
        "## Future Agent Boundary\n\n"
        "Spaetere Agentenhilfe darf nur fehlende Felder markieren, "
        "Alignment-Luecken melden oder kompakte To-do-Hinweise aus maximal "
        "50 rows erzeugen. Jede spaetere Nutzung braucht ein separates Goal, "
        "Tests und `llm_audit_log`. Agenten duerfen keine Quelleninhalte "
        "bewerten, keine Seitenzahlen erfinden, keine Kennzahlen berechnen, "
        "keine Zitation freigeben, keine Kausalclaims lockern, keine "
        "Wallet-Adressen ausgeben, keine Trading-Claims und keine "
        "Profitabilitaetsclaims formulieren.\n"
    )


def _match_slice(
    *,
    queue_slice: pd.DataFrame,
    ledger_slice: pd.DataFrame,
) -> tuple[int, int, int, int]:
    queue_keys = _row_keys(queue_slice, area_column="slice_id")
    ledger_keys = _row_keys(ledger_slice, area_column="thesis_area")
    matched_keys = queue_keys & ledger_keys
    queue_missing = len(queue_keys - ledger_keys)
    ledger_missing = len(ledger_keys - queue_keys)
    if not matched_keys:
        return 0, queue_missing, ledger_missing, 0

    queue_match = queue_slice.copy()
    ledger_match = ledger_slice.copy()
    queue_match["alignment_key"] = _key_series(queue_match, area_column="slice_id")
    ledger_match["alignment_key"] = _key_series(ledger_match, area_column="thesis_area")
    merged = queue_match.merge(
        ledger_match,
        on="alignment_key",
        how="inner",
        suffixes=("_queue", "_ledger"),
    )
    mismatch_mask = pd.Series(False, index=merged.index)
    for field in MATCH_FIELDS:
        mismatch_mask = mismatch_mask | (
            merged[f"{field}_queue"].fillna("").astype(str)
            != merged[f"{field}_ledger"].fillna("").astype(str)
        )
    return len(matched_keys), queue_missing, ledger_missing, int(mismatch_mask.sum())


def _overview_count_match(*, overview_row: dict[str, object], queue_slice: pd.DataFrame) -> bool:
    if not overview_row:
        return False
    return (
        int(overview_row.get("decision_rows", -1)) == len(queue_slice)
        and int(overview_row.get("pending_queue_rows", -1))
        == int(queue_slice["queue_status"].astype(str).str.startswith("pending_manual_").sum())
        and int(overview_row.get("final_ready_rows", -1))
        == int(queue_slice["final_citation_ready"].map(_bool_value).sum())
        and int(overview_row.get("source_status_change_rows", -1))
        == int(queue_slice["source_status_change_allowed"].map(_bool_value).sum())
        and str(overview_row.get("selected_tables", "")) == _join_unique(queue_slice["selected_table"])
        and str(overview_row.get("selected_figures", "")) == _join_unique(queue_slice["selected_figure"])
    )


def _alignment_status(
    *,
    queue_missing: int,
    ledger_missing: int,
    field_mismatches: int,
    queue_rows: int,
    ledger_pending_rows: int,
    final_ready_rows: int,
) -> str:
    if queue_missing or ledger_missing or field_mismatches:
        return "needs_alignment_review"
    if final_ready_rows:
        return "aligned_with_manual_progress"
    if ledger_pending_rows == queue_rows:
        return "aligned_pending_manual_review"
    return "aligned_with_partial_manual_progress"


def _row_keys(frame: pd.DataFrame, *, area_column: str) -> set[tuple[str, str, str]]:
    return set(_key_series(frame, area_column=area_column).tolist())


def _key_series(frame: pd.DataFrame, *, area_column: str) -> pd.Series:
    return frame.apply(
        lambda row: (
            str(row[area_column]),
            str(row["source_id"]),
            str(row["evidence_id"]),
        ),
        axis=1,
    )


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required decision-queue ledger alignment input missing: {path}")
    return pd.read_csv(path)


def _required_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Required decision-queue ledger alignment artifact missing: {path}")


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
