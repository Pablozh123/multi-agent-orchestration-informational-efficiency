from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from operations.analysis.monitor_v2_live_window_registry import (
    main,
    update_live_window_registry,
)


def test_update_live_window_registry_writes_compact_row(tmp_path: Path) -> None:
    paths = _write_metadata(tmp_path)

    result = update_live_window_registry(**paths, run_id="window_001", run_label="first")

    rows = _read_rows(paths["registry_path"])
    metadata = json.loads(paths["metadata_path"].read_text(encoding="utf-8"))
    assert result.row_count == 1
    assert rows[0]["run_id"] == "window_001"
    assert rows[0]["market_count"] == "12"
    assert rows[0]["bucket_count"] == "20"
    assert rows[0]["alert_count"] == "0"
    assert rows[0]["severity_counts_json"] == '{"none": 1416}'
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["method"]["does_not_collect_external_data"] is True


def test_update_live_window_registry_upserts_by_run_id(tmp_path: Path) -> None:
    paths = _write_metadata(tmp_path)

    update_live_window_registry(**paths, run_id="window_001", run_label="first")
    update_live_window_registry(**paths, run_id="window_001", run_label="renamed")

    rows = _read_rows(paths["registry_path"])
    assert len(rows) == 1
    assert rows[0]["run_label"] == "renamed"


def test_update_live_window_registry_rejects_unsafe_metadata(tmp_path: Path) -> None:
    paths = _write_metadata(tmp_path, contains_order_instructions=True)

    with pytest.raises(ValueError, match="order instructions"):
        update_live_window_registry(**paths, run_id="window_001")


def test_live_window_registry_cli_prints_summary(tmp_path: Path, capsys) -> None:
    paths = _write_metadata(tmp_path)

    exit_code = main(
        [
            "--refresh-metadata",
            str(paths["refresh_metadata_path"]),
            "--scoring-metadata",
            str(paths["scoring_metadata_path"]),
            "--dashboard-metadata",
            str(paths["dashboard_metadata_path"]),
            "--registry-output",
            str(paths["registry_path"]),
            "--metadata-output",
            str(paths["metadata_path"]),
            "--run-id",
            "window_001",
            "--run-label",
            "first",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "window_001" in captured.out
    assert paths["registry_path"].exists()


def _write_metadata(
    root: Path,
    *,
    contains_order_instructions: bool = False,
) -> dict[str, Path]:
    paths = {
        "refresh_metadata_path": root / "refresh.json",
        "scoring_metadata_path": root / "scoring.json",
        "dashboard_metadata_path": root / "dashboard.json",
        "registry_path": root / "registry.csv",
        "metadata_path": root / "registry_metadata.json",
    }
    paths["refresh_metadata_path"].write_text(
        json.dumps(
            {
                "generated_at_utc": "2026-05-22T22:15:31+00:00",
                "method": {
                    "source": "live",
                    "baseline_observations": 30,
                    "min_baseline_observations": 20,
                },
                "outputs": {
                    "bucket_count": 20,
                    "alert_count": 0,
                    "baseline_readiness": (
                        "baseline_available_zero_mad_or_non_alerting"
                    ),
                    "contains_wallet_addresses": False,
                    "contains_order_instructions": contains_order_instructions,
                },
            }
        ),
        encoding="utf-8",
    )
    paths["scoring_metadata_path"].write_text(
        json.dumps(
            {
                "inputs": {
                    "watchlist_row_count": 12,
                    "market_snapshot_row_count": 480,
                    "wallet_tier_snapshot_row_count": 240,
                },
                "method": {
                    "baseline_readiness": (
                        "baseline_available_zero_mad_or_non_alerting"
                    ),
                    "production_like_baseline_available": True,
                },
                "outputs": {
                    "alert_count": 0,
                    "alert_row_count": 1416,
                    "summary_row_count": 60,
                    "severity_counts": {"none": 1416},
                    "status_counts": {
                        "insufficient_baseline": 1200,
                        "zero_mad": 216,
                    },
                    "contains_wallet_addresses": False,
                    "contains_order_instructions": False,
                },
            }
        ),
        encoding="utf-8",
    )
    paths["dashboard_metadata_path"].write_text(
        json.dumps(
            {
                "outputs": {
                    "market_count": 12,
                    "bucket_count": 20,
                    "summary_row_count": 60,
                    "contains_wallet_addresses": False,
                    "contains_order_instructions": False,
                }
            }
        ),
        encoding="utf-8",
    )
    return paths


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
