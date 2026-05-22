"""Validate curated Polymarket politics/geopolitics watchlists.

This module checks local CSV watchlist files only. It does not call external
APIs, write databases, score alerts, use LLMs, agents, MCP tools, or place any
market instruction.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from operations.analysis.run_h2_event_windows import RESULTS_DIR


CURATED_WATCHLIST_PATH = Path("data/monitor_v2_curated_watchlist.csv")
CURATED_WATCHLIST_REPORT_OUTPUT = (
    RESULTS_DIR / "monitor_v2_curated_watchlist_validation_report.json"
)

CURATED_WATCHLIST_COLUMNS: tuple[str, ...] = (
    "watch_id",
    "market_id",
    "condition_id",
    "token_ids",
    "question",
    "category",
    "subcategory",
    "monitoring_scope",
    "review_status",
    "source_url",
    "inclusion_reason",
    "exclusion_reason",
    "reviewed_by",
    "reviewed_at_utc",
    "notes",
)

WATCHLIST_REVIEW_STATUSES = {
    "candidate",
    "source_checked",
    "market_mapped",
    "accepted",
    "rejected",
    "needs_followup",
}
ACCEPTED_SCOPES = {
    "politics",
    "geopolitics",
    "election",
    "leadership",
    "policy",
    "conflict",
    "international_relations",
}
ACCEPTED_REQUIRED_FIELDS = (
    "source_url",
    "inclusion_reason",
    "reviewed_by",
    "reviewed_at_utc",
)
FORBIDDEN_ACCEPTED_TERMS = (
    "fifa",
    "world cup",
    "nba",
    "nhl",
    "nfl",
    "stanley cup",
    "super bowl",
    "champions league",
    "album",
    "rihanna",
    "playboi",
    "carti",
    "jesus christ",
    "harvey",
    "weinstein",
)


@dataclass(frozen=True)
class WatchlistValidationResult:
    """Summary of a curated watchlist validation run."""

    input_path: Path
    report_path: Path
    row_count: int
    accepted_count: int
    candidate_count: int
    rejected_count: int
    needs_followup_count: int

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "input_path": str(self.input_path),
            "report_path": str(self.report_path),
            "row_count": self.row_count,
            "accepted_count": self.accepted_count,
            "candidate_count": self.candidate_count,
            "rejected_count": self.rejected_count,
            "needs_followup_count": self.needs_followup_count,
        }


def read_curated_watchlist(path: Path = CURATED_WATCHLIST_PATH) -> pd.DataFrame:
    """Read a curated watchlist CSV and validate the header."""

    if not path.exists():
        raise FileNotFoundError(f"Curated watchlist CSV not found: {path}")
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = [column for column in CURATED_WATCHLIST_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"curated watchlist missing required columns: {missing}")
    return frame.loc[:, list(CURATED_WATCHLIST_COLUMNS)].copy()


def validate_curated_watchlist(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize curated watchlist rows."""

    missing = [column for column in CURATED_WATCHLIST_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"curated watchlist missing required columns: {missing}")
    normalized = frame.loc[:, list(CURATED_WATCHLIST_COLUMNS)].copy()
    for column in CURATED_WATCHLIST_COLUMNS:
        normalized[column] = normalized[column].fillna("").astype(str).str.strip()
    _assert_no_wallet_address_fields(normalized)
    for row_number, row in enumerate(normalized.to_dict(orient="records"), start=1):
        _validate_row(row, row_number)
    return normalized


def validate_curated_watchlist_file(
    *,
    input_path: Path = CURATED_WATCHLIST_PATH,
    report_path: Path = CURATED_WATCHLIST_REPORT_OUTPUT,
) -> WatchlistValidationResult:
    """Validate a curated watchlist CSV and write a structured report."""

    frame = validate_curated_watchlist(read_curated_watchlist(input_path))
    report = build_watchlist_report(frame, input_path=input_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return WatchlistValidationResult(
        input_path=input_path,
        report_path=report_path,
        row_count=int(len(frame)),
        accepted_count=int((frame["review_status"] == "accepted").sum()),
        candidate_count=int((frame["review_status"] == "candidate").sum()),
        rejected_count=int((frame["review_status"] == "rejected").sum()),
        needs_followup_count=int((frame["review_status"] == "needs_followup").sum()),
    )


def build_watchlist_report(frame: pd.DataFrame, *, input_path: Path) -> dict[str, Any]:
    """Build a compact validation report for a curated watchlist."""

    status_counts = _value_counts(frame, "review_status")
    scope_counts = _value_counts(frame, "monitoring_scope")
    accepted = frame[frame["review_status"] == "accepted"].copy()
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "input_path": str(input_path),
        "status": "pass",
        "row_count": int(len(frame)),
        "accepted_count": int(len(accepted)),
        "candidate_count": int(status_counts.get("candidate", 0)),
        "rejected_count": int(status_counts.get("rejected", 0)),
        "needs_followup_count": int(status_counts.get("needs_followup", 0)),
        "status_counts": status_counts,
        "scope_counts": scope_counts,
        "accepted_market_ids": sorted(accepted["market_id"].astype(str).tolist()),
        "auto_discovered_rows_are_monitor_ready": False,
        "monitor_ready_rule": "review_status must be accepted",
        "contains_wallet_addresses": False,
        "contains_order_instructions": False,
        "limitations": {
            "local_csv_contract_only": True,
            "does_not_call_external_apis": True,
            "does_not_write_database": True,
            "does_not_score_alerts": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "candidate_rows_require_human_review": True,
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=CURATED_WATCHLIST_PATH)
    parser.add_argument("--report-output", type=Path, default=CURATED_WATCHLIST_REPORT_OUTPUT)
    args = parser.parse_args(argv)

    try:
        result = validate_curated_watchlist_file(
            input_path=args.input,
            report_path=args.report_output,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_row(row: dict[str, str], row_number: int) -> None:
    required = (
        "watch_id",
        "market_id",
        "condition_id",
        "token_ids",
        "question",
        "category",
        "monitoring_scope",
        "review_status",
    )
    missing = [column for column in required if _is_blank(row[column])]
    if missing:
        raise ValueError(f"watchlist row {row_number} missing required fields: {missing}")
    if row["review_status"] not in WATCHLIST_REVIEW_STATUSES:
        raise ValueError(
            f"watchlist row {row_number} has invalid review_status: {row['review_status']!r}"
        )
    if row["monitoring_scope"] not in ACCEPTED_SCOPES:
        raise ValueError(
            f"watchlist row {row_number} has invalid monitoring_scope: {row['monitoring_scope']!r}"
        )
    if len(_parse_list_field(row["token_ids"])) == 0:
        raise ValueError(f"watchlist row {row_number} token_ids must contain at least one id")
    if row["review_status"] == "accepted":
        missing_review = [
            column for column in ACCEPTED_REQUIRED_FIELDS
            if _is_blank(row[column])
        ]
        if missing_review:
            raise ValueError(
                f"accepted watchlist row {row_number} missing review fields: {missing_review}"
            )
        _validate_reviewed_at(row["reviewed_at_utc"], row_number)
        _validate_source_url(row["source_url"], row_number)
        _reject_forbidden_accepted_terms(row["question"], row_number)
    if row["review_status"] == "rejected" and _is_blank(row["exclusion_reason"]):
        raise ValueError(f"rejected watchlist row {row_number} requires exclusion_reason")


def _reject_forbidden_accepted_terms(question: str, row_number: int) -> None:
    text = question.lower()
    matches = [term for term in FORBIDDEN_ACCEPTED_TERMS if term in text]
    if matches:
        raise ValueError(
            f"accepted watchlist row {row_number} contains excluded market terms: {matches}"
        )


def _validate_reviewed_at(value: str, row_number: int) -> None:
    candidate = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(
            f"watchlist row {row_number} has invalid reviewed_at_utc: {value!r}"
        ) from exc
    if parsed.tzinfo is None:
        raise ValueError(f"watchlist row {row_number} reviewed_at_utc must include UTC offset")


def _validate_source_url(value: str, row_number: int) -> None:
    if not (value.startswith("https://") or value.startswith("http://")):
        raise ValueError(f"watchlist row {row_number} source_url must be an http URL")


def _assert_no_wallet_address_fields(frame: pd.DataFrame) -> None:
    forbidden = [column for column in frame.columns if "wallet_address" in column.lower()]
    if forbidden:
        raise ValueError(f"curated watchlist must not contain wallet-address fields: {forbidden}")


def _parse_list_field(value: str) -> list[str]:
    candidate = value.strip()
    if not candidate:
        return []
    return [item.strip() for item in candidate.replace(";", ",").split(",") if item.strip()]


def _value_counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    counts = frame[column].value_counts().sort_index()
    return {str(key): int(value) for key, value in counts.items()}


def _is_blank(value: object) -> bool:
    return value is None or str(value).strip() == ""


if __name__ == "__main__":
    raise SystemExit(main())
