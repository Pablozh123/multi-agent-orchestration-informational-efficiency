"""One-shot auto-refresh wrapper for the Swiss referendum comparison.

This module is designed for a local scheduler to call periodically. Each
invocation runs at most one bounded read-only refresh and exits. It is not a
daemon and does not use authenticated channels, order endpoints, agents, MCP
tools, ML, LLMs, or database writes.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Sequence

import httpx
import pandas as pd

from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.collectors.swiss_referendum_polymarket import SNAPSHOT_OUTPUT
from operations.collectors.swiss_referendum_refresh import (
    SwissReferendumRefreshResult,
    refresh_swiss_referendum_comparison,
)


DEFAULT_UNTIL_UTC = "2026-06-14T10:00:00Z"
AUTO_METADATA_OUTPUT = (
    RESULTS_DIR / "swiss_referendum_10mio_auto_refresh_metadata.json"
)
AUTO_LOG_OUTPUT = RESULTS_DIR / "swiss_referendum_10mio_auto_refresh_log.csv"
AUTO_LOCK_OUTPUT = RESULTS_DIR / "swiss_referendum_10mio_auto_refresh.lock"

AUTO_LOG_COLUMNS: tuple[str, ...] = (
    "generated_at_utc",
    "status",
    "source",
    "until_utc",
    "min_spacing_minutes",
    "latest_snapshot_at_utc",
    "snapshot_age_minutes",
    "snapshot_row_count",
    "comparison_row_count",
    "latest_yes_probability",
    "latest_raw_yes_gap",
    "latest_decided_yes_gap",
    "latest_divergence_label",
    "message",
)


RefreshCallable = Callable[..., SwissReferendumRefreshResult]


@dataclass(frozen=True)
class SwissReferendumAutoRefreshResult:
    """Summary of one scheduler-safe auto-refresh invocation."""

    status: str
    metadata_path: Path
    log_path: Path
    refreshed: bool
    message: str
    snapshot_row_count: int
    comparison_row_count: int
    latest_yes_probability: float | None
    latest_raw_yes_gap: float | None
    latest_decided_yes_gap: float | None
    latest_divergence_label: str

    def to_dict(self) -> dict[str, bool | float | int | str | None]:
        """Return a JSON-friendly result."""

        return {
            "status": self.status,
            "metadata_path": str(self.metadata_path),
            "log_path": str(self.log_path),
            "refreshed": self.refreshed,
            "message": self.message,
            "snapshot_row_count": self.snapshot_row_count,
            "comparison_row_count": self.comparison_row_count,
            "latest_yes_probability": self.latest_yes_probability,
            "latest_raw_yes_gap": self.latest_raw_yes_gap,
            "latest_decided_yes_gap": self.latest_decided_yes_gap,
            "latest_divergence_label": self.latest_divergence_label,
        }


def run_swiss_referendum_auto_refresh(
    *,
    source: str = "live",
    until_utc: str = DEFAULT_UNTIL_UTC,
    min_spacing_minutes: int = 55,
    snapshots_path: Path = SNAPSHOT_OUTPUT,
    metadata_path: Path = AUTO_METADATA_OUTPUT,
    log_path: Path = AUTO_LOG_OUTPUT,
    lock_path: Path = AUTO_LOCK_OUTPUT,
    now_utc: datetime | None = None,
    refresh_kwargs: dict[str, Any] | None = None,
    refresh_fn: RefreshCallable = refresh_swiss_referendum_comparison,
) -> SwissReferendumAutoRefreshResult:
    """Run at most one bounded refresh when schedule gates allow it."""

    if source not in {"mock", "live"}:
        raise ValueError("source must be either 'mock' or 'live'")
    if min_spacing_minutes < 0:
        raise ValueError("min_spacing_minutes must be >= 0")

    now = (now_utc or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)
    until = _parse_utc(until_utc)
    snapshot_info = _latest_snapshot_info(
        snapshots_path=snapshots_path,
        now_utc=now,
    )

    if now > until:
        return _write_result(
            status="skipped_after_until",
            source=source,
            until_utc=until,
            min_spacing_minutes=min_spacing_minutes,
            now_utc=now,
            metadata_path=metadata_path,
            log_path=log_path,
            snapshot_info=snapshot_info,
            message="Schedule cutoff has passed; no refresh was collected.",
        )

    if _is_too_recent(snapshot_info, min_spacing_minutes=min_spacing_minutes):
        return _write_result(
            status="skipped_min_spacing",
            source=source,
            until_utc=until,
            min_spacing_minutes=min_spacing_minutes,
            now_utc=now,
            metadata_path=metadata_path,
            log_path=log_path,
            snapshot_info=snapshot_info,
            message="Latest snapshot is newer than the configured spacing.",
        )

    lock_handle = _acquire_lock(lock_path, now)
    if lock_handle is None:
        return _write_result(
            status="skipped_locked",
            source=source,
            until_utc=until,
            min_spacing_minutes=min_spacing_minutes,
            now_utc=now,
            metadata_path=metadata_path,
            log_path=log_path,
            snapshot_info=snapshot_info,
            message="Another auto-refresh invocation is already running.",
        )

    try:
        kwargs = dict(refresh_kwargs or {})
        kwargs.setdefault("source", source)
        result = refresh_fn(**kwargs)
    finally:
        _release_lock(lock_handle, lock_path)

    result_dict = result.to_dict()
    refreshed_snapshot_info = _latest_snapshot_info(
        snapshots_path=Path(result_dict.get("snapshots_path", snapshots_path)),
        now_utc=now,
    )
    return _write_result(
        status="refreshed",
        source=source,
        until_utc=until,
        min_spacing_minutes=min_spacing_minutes,
        now_utc=now,
        metadata_path=metadata_path,
        log_path=log_path,
        snapshot_info=refreshed_snapshot_info,
        refresh_result=result_dict,
        message="Collected one bounded read-only refresh and exited.",
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("mock", "live"), default="live")
    parser.add_argument("--until-utc", default=DEFAULT_UNTIL_UTC)
    parser.add_argument("--min-spacing-minutes", type=int, default=55)
    parser.add_argument("--snapshots", type=Path, default=SNAPSHOT_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=AUTO_METADATA_OUTPUT)
    parser.add_argument("--log-output", type=Path, default=AUTO_LOG_OUTPUT)
    parser.add_argument("--lock-output", type=Path, default=AUTO_LOCK_OUTPUT)
    args = parser.parse_args(argv)

    try:
        result = run_swiss_referendum_auto_refresh(
            source=args.source,
            until_utc=args.until_utc,
            min_spacing_minutes=args.min_spacing_minutes,
            snapshots_path=args.snapshots,
            metadata_path=args.metadata_output,
            log_path=args.log_output,
            lock_path=args.lock_output,
        )
    except (httpx.HTTPError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _write_result(
    *,
    status: str,
    source: str,
    until_utc: datetime,
    min_spacing_minutes: int,
    now_utc: datetime,
    metadata_path: Path,
    log_path: Path,
    snapshot_info: dict[str, Any],
    message: str,
    refresh_result: dict[str, Any] | None = None,
) -> SwissReferendumAutoRefreshResult:
    refresh = refresh_result or {}
    output = {
        "generated_at_utc": now_utc.isoformat(),
        "method": {
            "name": "swiss_referendum_10mio_auto_refresh_one_shot",
            "source": source,
            "until_utc": until_utc.isoformat(),
            "min_spacing_minutes": min_spacing_minutes,
            "scheduler_invokes_one_shot": True,
            "not_a_background_daemon": True,
            "read_only": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "does_not_use_order_endpoints": True,
        },
        "status": {
            "status": status,
            "refreshed": status == "refreshed",
            "message": message,
            **snapshot_info,
        },
        "refresh_result": refresh,
        "outputs": {
            "metadata_path": str(metadata_path),
            "log_path": str(log_path),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "limitations": {
            "scheduled_collection_is_local_and_time_bounded": True,
            "each_invocation_collects_at_most_one_snapshot": True,
            "no_causal_claim_from_refresh": True,
            "no_profitability_or_tradeability_claim": True,
        },
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    row = _log_row(
        status=status,
        source=source,
        until_utc=until_utc,
        min_spacing_minutes=min_spacing_minutes,
        now_utc=now_utc,
        snapshot_info=snapshot_info,
        refresh_result=refresh,
        message=message,
    )
    _append_log_row(log_path, row)
    return SwissReferendumAutoRefreshResult(
        status=status,
        metadata_path=metadata_path,
        log_path=log_path,
        refreshed=status == "refreshed",
        message=message,
        snapshot_row_count=int(snapshot_info["snapshot_row_count"]),
        comparison_row_count=_optional_int(refresh.get("comparison_row_count")),
        latest_yes_probability=_optional_float(refresh.get("latest_yes_probability")),
        latest_raw_yes_gap=_optional_float(refresh.get("latest_raw_yes_gap")),
        latest_decided_yes_gap=_optional_float(refresh.get("latest_decided_yes_gap")),
        latest_divergence_label=str(refresh.get("latest_divergence_label", "")),
    )


def _latest_snapshot_info(*, snapshots_path: Path, now_utc: datetime) -> dict[str, Any]:
    if not snapshots_path.exists():
        return {
            "latest_snapshot_at_utc": "",
            "snapshot_age_minutes": None,
            "snapshot_row_count": 0,
        }
    frame = pd.read_csv(snapshots_path, dtype=str, keep_default_na=False)
    if frame.empty:
        return {
            "latest_snapshot_at_utc": "",
            "snapshot_age_minutes": None,
            "snapshot_row_count": 0,
        }
    if "collected_at_utc" not in frame.columns:
        raise ValueError("snapshot file missing collected_at_utc column")
    collected = pd.to_datetime(frame["collected_at_utc"], errors="raise", utc=True)
    latest = collected.max()
    now = pd.Timestamp(now_utc).tz_convert("UTC")
    age_minutes = max(0.0, (now - latest).total_seconds() / 60.0)
    return {
        "latest_snapshot_at_utc": latest.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "snapshot_age_minutes": round(age_minutes, 3),
        "snapshot_row_count": int(len(frame)),
    }


def _is_too_recent(
    snapshot_info: dict[str, Any],
    *,
    min_spacing_minutes: int,
) -> bool:
    age = snapshot_info.get("snapshot_age_minutes")
    if age is None:
        return False
    return float(age) < float(min_spacing_minutes)


def _parse_utc(value: str) -> datetime:
    candidate = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(candidate)
    if parsed.tzinfo is None:
        raise ValueError("until_utc must include a UTC offset")
    return parsed.astimezone(UTC).replace(microsecond=0)


def _acquire_lock(path: Path, now_utc: datetime):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return None
    with os.fdopen(handle, "w", encoding="utf-8", closefd=False) as file:
        file.write(now_utc.isoformat() + "\n")
    return handle


def _release_lock(handle, path: Path) -> None:
    os.close(handle)
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _log_row(
    *,
    status: str,
    source: str,
    until_utc: datetime,
    min_spacing_minutes: int,
    now_utc: datetime,
    snapshot_info: dict[str, Any],
    refresh_result: dict[str, Any],
    message: str,
) -> dict[str, Any]:
    return {
        "generated_at_utc": now_utc.isoformat(),
        "status": status,
        "source": source,
        "until_utc": until_utc.isoformat(),
        "min_spacing_minutes": min_spacing_minutes,
        "latest_snapshot_at_utc": snapshot_info["latest_snapshot_at_utc"],
        "snapshot_age_minutes": "" if snapshot_info["snapshot_age_minutes"] is None else snapshot_info["snapshot_age_minutes"],
        "snapshot_row_count": snapshot_info["snapshot_row_count"],
        "comparison_row_count": refresh_result.get("comparison_row_count", ""),
        "latest_yes_probability": refresh_result.get("latest_yes_probability", ""),
        "latest_raw_yes_gap": refresh_result.get("latest_raw_yes_gap", ""),
        "latest_decided_yes_gap": refresh_result.get("latest_decided_yes_gap", ""),
        "latest_divergence_label": refresh_result.get("latest_divergence_label", ""),
        "message": message,
    }


def _append_log_row(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=AUTO_LOG_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow({column: row.get(column, "") for column in AUTO_LOG_COLUMNS})


def _optional_int(value: Any) -> int:
    try:
        if value is None or str(value).strip() == "":
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def _optional_float(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(numeric):
        return None
    return numeric


if __name__ == "__main__":
    raise SystemExit(main())
