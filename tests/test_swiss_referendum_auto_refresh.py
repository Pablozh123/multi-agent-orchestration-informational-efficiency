from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from operations.collectors.swiss_referendum_auto_refresh import (
    main,
    run_swiss_referendum_auto_refresh,
)


def test_auto_refresh_runs_one_bounded_refresh_before_cutoff(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 6, 11, 12, 0, tzinfo=UTC)
    paths = _paths(tmp_path)
    calls: list[dict[str, Any]] = []

    def fake_refresh(**kwargs: Any) -> _FakeRefreshResult:
        calls.append(kwargs)
        _write_snapshot(paths["snapshots"], now)
        return _FakeRefreshResult(paths["snapshots"])

    result = run_swiss_referendum_auto_refresh(
        source="live",
        until_utc="2026-06-14T10:00:00Z",
        min_spacing_minutes=0,
        snapshots_path=paths["snapshots"],
        metadata_path=paths["metadata"],
        log_path=paths["log"],
        lock_path=paths["lock"],
        now_utc=now,
        refresh_kwargs={"collect_history": False},
        refresh_fn=fake_refresh,
    )

    metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
    log = pd.read_csv(paths["log"])
    assert result.status == "refreshed"
    assert result.refreshed is True
    assert result.snapshot_row_count == 1
    assert result.comparison_row_count == 7
    assert result.latest_yes_probability == 0.23
    assert calls == [{"collect_history": False, "source": "live"}]
    assert paths["lock"].exists() is False
    assert metadata["method"]["scheduler_invokes_one_shot"] is True
    assert metadata["method"]["not_a_background_daemon"] is True
    assert metadata["method"]["does_not_use_order_endpoints"] is True
    assert metadata["outputs"]["contains_order_instructions"] is False
    assert log.iloc[-1]["status"] == "refreshed"
    assert log.iloc[-1]["latest_divergence_label"] == (
        "polymarket_below_poll_yes_share"
    )


def test_auto_refresh_skips_after_cutoff_without_refresh(tmp_path: Path) -> None:
    now = datetime(2026, 6, 14, 10, 1, tzinfo=UTC)
    paths = _paths(tmp_path)

    result = run_swiss_referendum_auto_refresh(
        source="live",
        until_utc="2026-06-14T10:00:00Z",
        min_spacing_minutes=0,
        snapshots_path=paths["snapshots"],
        metadata_path=paths["metadata"],
        log_path=paths["log"],
        lock_path=paths["lock"],
        now_utc=now,
        refresh_fn=_failing_refresh,
    )

    metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
    log = pd.read_csv(paths["log"])
    assert result.status == "skipped_after_until"
    assert result.refreshed is False
    assert result.snapshot_row_count == 0
    assert metadata["status"]["message"].startswith("Schedule cutoff")
    assert log.iloc[-1]["status"] == "skipped_after_until"


def test_auto_refresh_skips_when_latest_snapshot_is_too_recent(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 6, 11, 12, 0, tzinfo=UTC)
    paths = _paths(tmp_path)
    _write_snapshot(paths["snapshots"], now - timedelta(minutes=30))

    result = run_swiss_referendum_auto_refresh(
        source="live",
        until_utc="2026-06-14T10:00:00Z",
        min_spacing_minutes=55,
        snapshots_path=paths["snapshots"],
        metadata_path=paths["metadata"],
        log_path=paths["log"],
        lock_path=paths["lock"],
        now_utc=now,
        refresh_fn=_failing_refresh,
    )

    metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
    assert result.status == "skipped_min_spacing"
    assert result.refreshed is False
    assert result.snapshot_row_count == 1
    assert metadata["status"]["latest_snapshot_at_utc"] == (
        "2026-06-11T11:30:00Z"
    )
    assert metadata["status"]["snapshot_age_minutes"] == 30.0


def test_auto_refresh_skips_when_lock_exists(tmp_path: Path) -> None:
    now = datetime(2026, 6, 11, 12, 0, tzinfo=UTC)
    paths = _paths(tmp_path)
    paths["lock"].write_text("2026-06-11T11:59:00+00:00\n", encoding="utf-8")

    result = run_swiss_referendum_auto_refresh(
        source="live",
        until_utc="2026-06-14T10:00:00Z",
        min_spacing_minutes=0,
        snapshots_path=paths["snapshots"],
        metadata_path=paths["metadata"],
        log_path=paths["log"],
        lock_path=paths["lock"],
        now_utc=now,
        refresh_fn=_failing_refresh,
    )

    assert result.status == "skipped_locked"
    assert result.refreshed is False
    assert paths["lock"].exists() is True


def test_auto_refresh_cli_writes_skip_metadata(tmp_path: Path, capsys) -> None:
    paths = _paths(tmp_path)

    exit_code = main(
        [
            "--source",
            "mock",
            "--until-utc",
            "2026-06-01T00:00:00Z",
            "--snapshots",
            str(paths["snapshots"]),
            "--metadata-output",
            str(paths["metadata"]),
            "--log-output",
            str(paths["log"]),
            "--lock-output",
            str(paths["lock"]),
        ]
    )

    captured = capsys.readouterr()
    metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
    assert exit_code == 0
    assert "skipped_after_until" in captured.out
    assert metadata["method"]["read_only"] is True
    assert metadata["method"]["does_not_use_agents_or_mcp"] is True


class _FakeRefreshResult:
    def __init__(self, snapshots_path: Path) -> None:
        self.snapshots_path = snapshots_path

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshots_path": str(self.snapshots_path),
            "comparison_row_count": 7,
            "latest_yes_probability": 0.23,
            "latest_raw_yes_gap": -0.22,
            "latest_decided_yes_gap": -0.233918,
            "latest_divergence_label": "polymarket_below_poll_yes_share",
        }


def _failing_refresh(**_: Any) -> _FakeRefreshResult:
    raise AssertionError("refresh function should not be called")


def _paths(root: Path) -> dict[str, Path]:
    return {
        "snapshots": root / "snapshots.csv",
        "metadata": root / "auto_metadata.json",
        "log": root / "auto_log.csv",
        "lock": root / "auto_refresh.lock",
    }


def _write_snapshot(path: Path, collected_at_utc: datetime) -> None:
    timestamp = collected_at_utc.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    pd.DataFrame([{"collected_at_utc": timestamp}]).to_csv(path, index=False)
