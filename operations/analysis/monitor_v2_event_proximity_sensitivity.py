"""Compare same-day and event-proximity context for monitor v2 replay alerts.

This module reads existing historical replay alert rows and curated events. It
does not rescore market or wallet metrics. Instead, it tests how many reviewed
event contexts would be visible when daily data use a small event-proximity
window such as [-1d, +1d] instead of same-day matching only.
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

from operations.analysis.monitor_v2_snapshot import (
    ALERT_ROW_COLUMNS,
    SEVERITY_RANK,
    WALLET_OR_CONCENTRATION_FAMILIES,
    WATCH_OR_HIGH,
)
from operations.analysis.run_h2_event_windows import RESULTS_DIR, SEED_PATH, load_curated_events


ALERT_ROWS_OUTPUT = RESULTS_DIR / "monitor_v2_historical_replay_alert_rows.csv"
ROWS_OUTPUT = RESULTS_DIR / "monitor_v2_event_proximity_sensitivity_rows.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "monitor_v2_event_proximity_sensitivity_summary.csv"
METADATA_OUTPUT = RESULTS_DIR / "monitor_v2_event_proximity_sensitivity_metadata.json"

EVENT_COLUMNS: tuple[str, ...] = (
    "event_id",
    "event_date",
    "title",
    "event_type",
    "source_url",
)
SENSITIVITY_ROW_COLUMNS: tuple[str, ...] = (
    "event_id",
    "event_date",
    "proximity_date",
    "relative_day",
    "timestamp_utc",
    "market_id",
    "tier",
    "anomaly_family",
    "metric_name",
    "observed_value",
    "robust_z",
    "rolling_percentile_rank",
    "severity",
    "status",
    "same_day_context",
    "proximity_window",
    "market_watch_at_timestamp",
    "wallet_or_concentration_watch_at_timestamp",
    "proximity_critical_candidate",
    "event_watch_candidate",
    "suggested_context_label",
    "claim_scope",
)
SENSITIVITY_SUMMARY_COLUMNS: tuple[str, ...] = (
    "event_id",
    "event_date",
    "proximity_date",
    "relative_day",
    "market_id",
    "max_existing_severity",
    "watch_or_high_rows",
    "high_rows",
    "market_watch_at_timestamp",
    "wallet_or_concentration_watch_at_timestamp",
    "same_day_critical_candidate",
    "proximity_critical_candidate",
    "event_watch_candidate",
    "suggested_context_label",
)


@dataclass(frozen=True)
class EventProximitySensitivityResult:
    """Summary of generated event-proximity sensitivity artifacts."""

    rows_path: Path
    summary_path: Path
    metadata_path: Path
    row_count: int
    summary_row_count: int
    same_day_critical_candidates: int
    proximity_critical_candidates: int
    event_watch_candidates: int

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "rows_path": str(self.rows_path),
            "summary_path": str(self.summary_path),
            "metadata_path": str(self.metadata_path),
            "row_count": self.row_count,
            "summary_row_count": self.summary_row_count,
            "same_day_critical_candidates": self.same_day_critical_candidates,
            "proximity_critical_candidates": self.proximity_critical_candidates,
            "event_watch_candidates": self.event_watch_candidates,
        }


def generate_event_proximity_sensitivity(
    *,
    alert_rows_path: Path = ALERT_ROWS_OUTPUT,
    events_csv_path: Path = SEED_PATH,
    rows_path: Path = ROWS_OUTPUT,
    summary_path: Path = SUMMARY_OUTPUT,
    metadata_path: Path = METADATA_OUTPUT,
    days_before: int = 1,
    days_after: int = 1,
) -> EventProximitySensitivityResult:
    """Generate event-proximity sensitivity rows, summary, and metadata."""

    alert_rows = load_replay_alert_rows(alert_rows_path)
    events = load_curated_events(events_csv_path)
    rows, summary = build_event_proximity_sensitivity(
        alert_rows,
        events,
        days_before=days_before,
        days_after=days_after,
    )

    rows_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    rows.to_csv(rows_path, index=False)
    summary.to_csv(summary_path, index=False)
    metadata_path.write_text(
        json.dumps(
            _build_metadata(
                alert_rows=alert_rows,
                events=events,
                rows=rows,
                summary=summary,
                alert_rows_path=alert_rows_path,
                events_csv_path=events_csv_path,
                days_before=days_before,
                days_after=days_after,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return EventProximitySensitivityResult(
        rows_path=rows_path,
        summary_path=summary_path,
        metadata_path=metadata_path,
        row_count=len(rows),
        summary_row_count=len(summary),
        same_day_critical_candidates=int(summary["same_day_critical_candidate"].sum()),
        proximity_critical_candidates=int(summary["proximity_critical_candidate"].sum()),
        event_watch_candidates=int(summary["event_watch_candidate"].sum()),
    )


def build_event_proximity_sensitivity(
    alert_rows: pd.DataFrame,
    events: pd.DataFrame,
    *,
    days_before: int = 1,
    days_after: int = 1,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return row-level and date-level event-proximity sensitivity outputs."""

    if days_before < 0 or days_after < 0:
        raise ValueError("days_before and days_after must be >= 0")

    rows = validate_replay_alert_rows(alert_rows)
    event_windows = build_event_windows(
        validate_events(events),
        days_before=days_before,
        days_after=days_after,
    )
    merged = event_windows.merge(
        rows,
        left_on="proximity_date",
        right_on="alert_date",
        how="left",
    )
    merged = merged.drop(columns=["alert_date"])
    merged = merged[merged["market_id"].notna()].copy()
    if merged.empty:
        raise ValueError("No replay alert rows overlap the event-proximity windows")

    summary = summarize_event_proximity(merged)
    output_rows = merged.merge(
        summary[
            [
                "event_id",
                "proximity_date",
                "market_id",
                "market_watch_at_timestamp",
                "wallet_or_concentration_watch_at_timestamp",
                "proximity_critical_candidate",
                "event_watch_candidate",
                "suggested_context_label",
            ]
        ],
        on=["event_id", "proximity_date", "market_id"],
        how="left",
    )
    output_rows["same_day_context"] = output_rows["relative_day"].eq(0)
    output_rows["proximity_window"] = f"[-{days_before}d,+{days_after}d]"
    output_rows["claim_scope"] = "event_proximity_sensitivity_only"
    return (
        output_rows.loc[:, SENSITIVITY_ROW_COLUMNS]
        .sort_values(["event_date", "relative_day", "market_id", "anomaly_family", "tier"])
        .reset_index(drop=True),
        summary,
    )


def summarize_event_proximity(proximity_rows: pd.DataFrame) -> pd.DataFrame:
    """Summarize event-proximity context at event-date-market level."""

    _require_columns(
        proximity_rows,
        (
            "event_id",
            "event_date",
            "proximity_date",
            "relative_day",
            "market_id",
            "anomaly_family",
            "severity",
        ),
        "event proximity rows",
    )
    summaries: list[dict[str, object]] = []
    group_columns = ["event_id", "event_date", "proximity_date", "relative_day", "market_id"]
    for keys, group in proximity_rows.groupby(group_columns, sort=True, dropna=False):
        values = dict(zip(group_columns, keys))
        watch_mask = group["severity"].isin(WATCH_OR_HIGH)
        market_watch = bool(((group["anomaly_family"] == "market_move") & watch_mask).any())
        wallet_watch = bool(
            (group["anomaly_family"].isin(WALLET_OR_CONCENTRATION_FAMILIES) & watch_mask).any()
        )
        same_day = int(values["relative_day"]) == 0
        proximity_critical = market_watch and wallet_watch
        event_watch = wallet_watch and not market_watch
        summaries.append(
            {
                **values,
                "max_existing_severity": _max_severity(group["severity"]),
                "watch_or_high_rows": int(watch_mask.sum()),
                "high_rows": int((group["severity"] == "high").sum()),
                "market_watch_at_timestamp": market_watch,
                "wallet_or_concentration_watch_at_timestamp": wallet_watch,
                "same_day_critical_candidate": same_day and proximity_critical,
                "proximity_critical_candidate": proximity_critical,
                "event_watch_candidate": event_watch,
                "suggested_context_label": _context_label(
                    proximity_critical=proximity_critical,
                    event_watch=event_watch,
                    watch_or_high_rows=int(watch_mask.sum()),
                ),
            }
        )
    return pd.DataFrame(summaries, columns=SENSITIVITY_SUMMARY_COLUMNS).sort_values(
        ["event_date", "relative_day", "market_id"]
    ).reset_index(drop=True)


def build_event_windows(
    events: pd.DataFrame,
    *,
    days_before: int = 1,
    days_after: int = 1,
) -> pd.DataFrame:
    """Return one row per event and date in the requested proximity window."""

    rows: list[dict[str, object]] = []
    for event in events.to_dict(orient="records"):
        event_date = pd.Timestamp(event["event_date"])
        for relative_day in range(-days_before, days_after + 1):
            rows.append(
                {
                    "event_id": event["event_id"],
                    "event_date": event_date.date().isoformat(),
                    "proximity_date": (event_date + pd.Timedelta(days=relative_day))
                    .date()
                    .isoformat(),
                    "relative_day": relative_day,
                }
            )
    return pd.DataFrame(rows)


def load_replay_alert_rows(path: Path) -> pd.DataFrame:
    """Load historical replay alert rows from CSV."""

    if not path.exists():
        raise FileNotFoundError(f"Monitor v2 replay alert rows not found: {path}")
    return pd.read_csv(path)


def validate_replay_alert_rows(alert_rows: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize replay alert rows for sensitivity analysis."""

    _require_columns(alert_rows, ALERT_ROW_COLUMNS, "monitor v2 replay alert rows")
    if "wallet_address" in alert_rows.columns:
        raise ValueError("event-proximity sensitivity must not receive wallet_address")
    frame = alert_rows.loc[:, ALERT_ROW_COLUMNS].copy()
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="raise")
    frame["alert_date"] = frame["timestamp_utc"].dt.date.astype(str)
    frame["timestamp_utc"] = frame["timestamp_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    for column in ("market_id", "tier", "anomaly_family", "metric_name", "severity", "status"):
        if frame[column].isna().any() or (
            frame[column].astype(str).str.strip() == ""
        ).any():
            raise ValueError(f"monitor v2 replay alert rows contain blank values in {column}")
        frame[column] = frame[column].astype(str).str.strip()
    unknown = sorted(set(frame["severity"]) - set(SEVERITY_RANK))
    if unknown:
        raise ValueError(f"monitor v2 replay alert rows contain unknown severity values: {unknown}")
    return frame


def validate_events(events: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize curated events for sensitivity analysis."""

    _require_columns(events, EVENT_COLUMNS, "events")
    frame = events.loc[:, EVENT_COLUMNS].copy()
    for column in ("event_id", "title", "event_type", "source_url"):
        if frame[column].isna().any() or (
            frame[column].astype(str).str.strip() == ""
        ).any():
            raise ValueError(f"events contain blank values in {column}")
        frame[column] = frame[column].astype(str).str.strip()
    frame["event_date"] = pd.to_datetime(frame["event_date"], errors="raise").dt.date
    if frame["event_id"].duplicated().any():
        duplicates = sorted(frame.loc[frame["event_id"].duplicated(), "event_id"].unique())
        raise ValueError(f"events contain duplicate event_id values: {duplicates}")
    return frame.sort_values(["event_date", "event_id"]).reset_index(drop=True)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--alert-rows", type=Path, default=ALERT_ROWS_OUTPUT)
    parser.add_argument("--events", type=Path, default=SEED_PATH)
    parser.add_argument("--rows-output", type=Path, default=ROWS_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    parser.add_argument("--days-before", type=int, default=1)
    parser.add_argument("--days-after", type=int, default=1)
    args = parser.parse_args(argv)

    try:
        result = generate_event_proximity_sensitivity(
            alert_rows_path=args.alert_rows,
            events_csv_path=args.events,
            rows_path=args.rows_output,
            summary_path=args.summary_output,
            metadata_path=args.metadata_output,
            days_before=args.days_before,
            days_after=args.days_after,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _build_metadata(
    *,
    alert_rows: pd.DataFrame,
    events: pd.DataFrame,
    rows: pd.DataFrame,
    summary: pd.DataFrame,
    alert_rows_path: Path,
    events_csv_path: Path,
    days_before: int,
    days_after: int,
) -> dict[str, Any]:
    same_day_critical = int(summary["same_day_critical_candidate"].sum())
    proximity_critical = int(summary["proximity_critical_candidate"].sum())
    event_watch = int(summary["event_watch_candidate"].sum())
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "monitor_v2_event_proximity_sensitivity",
            "input_mode": "existing_historical_replay_alert_rows",
            "event_window": f"[-{days_before}d,+{days_after}d]",
            "does_not_rescore_alert_rows": True,
            "critical_rule": (
                "proximity critical candidate requires market_move and wallet/"
                "concentration watch-or-higher rows in the event-proximity window"
            ),
            "event_watch_rule": (
                "event_watch candidate marks wallet/concentration watch-or-higher "
                "event-proximity clusters without market_move confirmation"
            ),
        },
        "inputs": {
            "alert_rows_path": str(alert_rows_path),
            "events_csv_path": str(events_csv_path),
            "alert_row_count": int(len(alert_rows)),
            "event_count": int(events["event_id"].nunique()),
        },
        "outputs": {
            "row_count": int(len(rows)),
            "summary_row_count": int(len(summary)),
            "same_day_critical_candidates": same_day_critical,
            "proximity_critical_candidates": proximity_critical,
            "event_watch_candidates": event_watch,
            "row_columns": list(SENSITIVITY_ROW_COLUMNS),
            "summary_columns": list(SENSITIVITY_SUMMARY_COLUMNS),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "decision": {
            "use_event_proximity_window": proximity_critical > same_day_critical,
            "recommended_event_window": f"[-{days_before}d,+{days_after}d]",
            "event_watch_decision": (
                "use_as_separate_descriptive_label_not_severity_upgrade"
                if event_watch > 0
                else "not_needed_in_current_replay"
            ),
            "keep_critical_strict": True,
        },
        "limitations": {
            "daily_replay_only": True,
            "uses_existing_replay_alert_rows": True,
            "uses_existing_curated_events": True,
            "does_not_write_database": True,
            "does_not_use_live_websocket_or_api_collection": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "does_not_use_rcp": True,
            "does_not_send_orders": True,
            "no_profitability_or_private_information_claim": True,
        },
    }


def _context_label(
    *,
    proximity_critical: bool,
    event_watch: bool,
    watch_or_high_rows: int,
) -> str:
    if proximity_critical:
        return "critical_proximity_candidate"
    if event_watch:
        return "event_watch_candidate"
    if watch_or_high_rows > 0:
        return "context_alert"
    return "no_event_alert"


def _max_severity(values: pd.Series) -> str:
    return max((str(value) for value in values), key=lambda value: SEVERITY_RANK[value])


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


if __name__ == "__main__":
    raise SystemExit(main())
