"""Persist reviewed H2 event-window summaries into analysis_summaries.

This module writes compact summary records only. It reads the accepted
`h2_event_window_summary.csv` artifact and intentionally ignores the row-level
H2 trace so detailed calculation rows remain file-based.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.db.migrations import DB_PATH


SUMMARY_CSV_PATH = RESULTS_DIR / "h2_event_window_summary.csv"
RUN_ID = "h2_event_window_baseline_v1"
SUMMARY_TYPE = "h2_event_window_summary"
TABLE_NAME = "h2_event_window_summary"
METRIC_NAME = "final_cumulative_abnormal_change"

REQUIRED_COLUMNS: tuple[str, ...] = (
    "event_id",
    "event_date",
    "event_time_utc",
    "title",
    "description",
    "event_type",
    "source_url",
    "expected_direction",
    "relevance_score",
    "window_label",
    "observed_days",
    "final_cumulative_abnormal_change",
    "estimation_observations",
)

INPUT_TABLES = (
    "data/results/h2_event_window_summary.csv",
    "data/events_timeline_seed.csv",
    "polymarket_prices",
)


@dataclass(frozen=True)
class PersistH2Result:
    """Summary of an H2 summary persistence run."""

    deleted: int
    inserted: int
    run_id: str
    summary_type: str

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "deleted": self.deleted,
            "inserted": self.inserted,
            "run_id": self.run_id,
            "summary_type": self.summary_type,
        }


def load_h2_summary_csv(csv_path: Path = SUMMARY_CSV_PATH) -> pd.DataFrame:
    """Load and validate the accepted H2 summary CSV artifact."""

    if not csv_path.exists():
        raise FileNotFoundError(f"H2 summary CSV not found: {csv_path}")

    frame = pd.read_csv(csv_path)
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"H2 summary CSV is missing columns: {missing}")
    if frame.empty:
        raise ValueError(f"H2 summary CSV has no rows: {csv_path}")

    required_frame = frame.loc[:, REQUIRED_COLUMNS].copy()
    for column in (
        "event_id",
        "event_date",
        "event_time_utc",
        "title",
        "event_type",
        "source_url",
        "expected_direction",
        "window_label",
    ):
        if required_frame[column].isna().any() or (
            required_frame[column].astype(str).str.strip() == ""
        ).any():
            raise ValueError(f"H2 summary CSV contains blank values in {column}")

    required_frame["event_date"] = pd.to_datetime(
        required_frame["event_date"],
        errors="raise",
    ).dt.date.astype(str)
    required_frame["relevance_score"] = pd.to_numeric(
        required_frame["relevance_score"],
        errors="raise",
    )
    required_frame["observed_days"] = pd.to_numeric(
        required_frame["observed_days"],
        errors="raise",
    ).astype(int)
    required_frame["final_cumulative_abnormal_change"] = pd.to_numeric(
        required_frame["final_cumulative_abnormal_change"],
        errors="raise",
    )
    required_frame["estimation_observations"] = pd.to_numeric(
        required_frame["estimation_observations"],
        errors="raise",
    ).astype(int)

    duplicate_keys = required_frame.duplicated(["event_id", "window_label"])
    if duplicate_keys.any():
        duplicates = required_frame.loc[
            duplicate_keys,
            ["event_id", "window_label"],
        ].to_dict(orient="records")
        raise ValueError(f"H2 summary CSV has duplicate event/window rows: {duplicates}")

    return required_frame.sort_values(["event_date", "event_id", "window_label"]).reset_index(
        drop=True
    )


def build_h2_summary_records(
    summary_frame: pd.DataFrame,
    *,
    computed_at: str | None = None,
) -> list[dict[str, Any]]:
    """Build compact analysis_summaries records from accepted H2 summaries."""

    missing = [column for column in REQUIRED_COLUMNS if column not in summary_frame.columns]
    if missing:
        raise ValueError(f"H2 summary frame is missing columns: {missing}")

    timestamp = computed_at or _now_utc()
    records: list[dict[str, Any]] = []
    input_tables_json = _json_dumps(list(INPUT_TABLES))
    for row in summary_frame.to_dict(orient="records"):
        event_id = str(row["event_id"])
        window_label = str(row["window_label"])
        event = {
            "event_id": event_id,
            "event_date": str(row["event_date"]),
            "event_time_utc": str(row["event_time_utc"]),
            "title": str(row["title"]),
            "description": str(row["description"]),
            "event_type": str(row["event_type"]),
            "source_url": str(row["source_url"]),
            "expected_direction": str(row["expected_direction"]),
            "relevance_score": float(row["relevance_score"]),
        }
        metrics = {
            "window_label": window_label,
            "observed_days": int(row["observed_days"]),
            "final_cumulative_abnormal_change": float(
                row["final_cumulative_abnormal_change"]
            ),
            "estimation_observations": int(row["estimation_observations"]),
        }
        payload = {
            "run_id": RUN_ID,
            "summary_type": SUMMARY_TYPE,
            "event": event,
            "metrics": metrics,
        }
        records.append(
            {
                "summary_id": f"{SUMMARY_TYPE}:{event_id}:{window_label}",
                "run_id": RUN_ID,
                "summary_type": SUMMARY_TYPE,
                "date_range_start": event["event_date"],
                "date_range_end": event["event_date"],
                "input_tables": input_tables_json,
                "metrics_json": _json_dumps(metrics),
                "summary_json": _json_dumps(payload),
                "table_name": TABLE_NAME,
                "metric_name": METRIC_NAME,
                "value_json": _json_dumps(payload),
                "computed_at": timestamp,
            }
        )
    return records


def persist_h2_summary_records(
    conn: sqlite3.Connection,
    records: Sequence[dict[str, Any]],
) -> PersistH2Result:
    """Persist compact H2 summaries idempotently by run and summary type."""

    if not records:
        raise ValueError("No H2 summary records to persist")

    for record in records:
        if record.get("run_id") != RUN_ID or record.get("summary_type") != SUMMARY_TYPE:
            raise ValueError("H2 summary records must use the configured run and type")

    with conn:
        deleted = conn.execute(
            """
            DELETE FROM analysis_summaries
            WHERE run_id = ?
              AND summary_type = ?
            """,
            (RUN_ID, SUMMARY_TYPE),
        ).rowcount
        conn.executemany(
            """
            INSERT INTO analysis_summaries
                (summary_id, run_id, summary_type, date_range_start,
                 date_range_end, input_tables, metrics_json, summary_json,
                 table_name, metric_name, value_json, computed_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            [
                (
                    record["summary_id"],
                    record["run_id"],
                    record["summary_type"],
                    record["date_range_start"],
                    record["date_range_end"],
                    record["input_tables"],
                    record["metrics_json"],
                    record["summary_json"],
                    record["table_name"],
                    record["metric_name"],
                    record["value_json"],
                    record["computed_at"],
                )
                for record in records
            ],
        )

    return PersistH2Result(
        deleted=max(deleted, 0),
        inserted=len(records),
        run_id=RUN_ID,
        summary_type=SUMMARY_TYPE,
    )


def persist_h2_summaries(
    *,
    db_path: Path = DB_PATH,
    summary_csv_path: Path = SUMMARY_CSV_PATH,
    computed_at: str | None = None,
) -> PersistH2Result:
    """Load accepted H2 summaries and persist compact records into SQLite."""

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    summary_frame = load_h2_summary_csv(summary_csv_path)
    records = build_h2_summary_records(summary_frame, computed_at=computed_at)
    conn = sqlite3.connect(db_path)
    try:
        return persist_h2_summary_records(conn, records)
    finally:
        conn.close()


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--summary-csv", type=Path, default=SUMMARY_CSV_PATH)
    args = parser.parse_args(argv)

    try:
        result = persist_h2_summaries(
            db_path=args.db,
            summary_csv_path=args.summary_csv,
        )
    except (FileNotFoundError, ValueError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _json_dumps(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


if __name__ == "__main__":
    raise SystemExit(main())
