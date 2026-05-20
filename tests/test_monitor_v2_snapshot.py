from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.monitor_v2_snapshot import (
    ALERT_ROW_COLUMNS,
    ALERT_SUMMARY_COLUMNS,
    build_mock_snapshot_frame,
    build_monitor_v2_alert_rows,
    generate_monitor_v2_snapshot_outputs,
    main,
    summarize_monitor_v2_alerts,
)


def test_robust_score_detects_spike_without_lookahead() -> None:
    snapshots = _single_metric_snapshots(
        baseline_values=[10.0, 10.2, 9.9, 10.1, 9.8],
        spike=30.0,
    )

    rows = build_monitor_v2_alert_rows(
        snapshots,
        baseline_observations=5,
        min_baseline_observations=5,
    )

    assert tuple(rows.columns) == ALERT_ROW_COLUMNS
    assert rows.iloc[4]["status"] == "insufficient_baseline"
    spike_row = rows.iloc[5]
    assert spike_row["status"] == "ok"
    assert spike_row["baseline_observations"] == 5
    assert spike_row["severity"] == "high"
    assert spike_row["robust_z"] > 3.0
    assert "wallet_address" not in rows.columns


def test_zero_mad_returns_diagnostic_not_false_alert() -> None:
    snapshots = _single_metric_snapshots(
        baseline_values=[10.0, 10.0, 10.0, 10.0, 10.0],
        spike=20.0,
    )

    rows = build_monitor_v2_alert_rows(
        snapshots,
        baseline_observations=5,
        min_baseline_observations=5,
    )

    spike_row = rows.iloc[5]
    assert spike_row["status"] == "zero_mad"
    assert pd.isna(spike_row["robust_z"])
    assert spike_row["severity"] == "none"


def test_critical_requires_reviewed_event_cluster() -> None:
    rows = build_monitor_v2_alert_rows(
        build_mock_snapshot_frame(),
        baseline_observations=30,
        min_baseline_observations=20,
    )

    final_day = rows["timestamp_utc"].max()
    final_rows = rows[rows["timestamp_utc"] == final_day]
    assert set(final_rows["severity"]) == {"critical"}
    assert set(final_rows["event_review_status"]) == {"accepted"}


def test_summarize_monitor_v2_alerts_compacts_outputs() -> None:
    rows = build_monitor_v2_alert_rows(
        build_mock_snapshot_frame(),
        baseline_observations=30,
        min_baseline_observations=20,
    )

    summary = summarize_monitor_v2_alerts(rows)

    assert tuple(summary.columns) == ALERT_SUMMARY_COLUMNS
    assert "wallet_address" not in summary.columns
    market_summary = summary[
        summary["metric_name"] == "absolute_midpoint_change"
    ].iloc[0]
    assert market_summary["alert_count"] >= 1
    assert market_summary["max_severity"] == "critical"
    assert market_summary["claim_scope"] == "descriptive_monitor_alert_summary_only"


def test_missing_required_snapshot_columns_fail_clearly() -> None:
    snapshots = build_mock_snapshot_frame().drop(columns=["evidence_ref"])

    with pytest.raises(ValueError, match="monitor v2 snapshots missing required columns"):
        build_monitor_v2_alert_rows(snapshots)


def test_wallet_address_column_is_rejected() -> None:
    snapshots = build_mock_snapshot_frame()
    snapshots["wallet_address"] = "0xnotallowed"

    with pytest.raises(ValueError, match="must not contain wallet_address"):
        build_monitor_v2_alert_rows(snapshots)


def test_generate_monitor_v2_snapshot_outputs_writes_files(tmp_path: Path) -> None:
    rows_path = tmp_path / "rows.csv"
    summary_path = tmp_path / "summary.csv"
    metadata_path = tmp_path / "metadata.json"

    result = generate_monitor_v2_snapshot_outputs(
        rows_path=rows_path,
        summary_path=summary_path,
        metadata_path=metadata_path,
    )

    rows = pd.read_csv(rows_path)
    summary = pd.read_csv(summary_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert result.row_count == len(rows)
    assert result.summary_row_count == len(summary)
    assert result.alert_count == int((rows["severity"] != "none").sum())
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["contains_order_instructions"] is False
    assert metadata["limitations"]["no_live_websocket_or_api_collection"] is True
    assert metadata["limitations"]["does_not_use_agents_or_mcp"] is True
    assert "wallet_address" not in rows.columns
    assert "wallet_address" not in summary.columns


def test_cli_returns_clear_error_for_missing_snapshot_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "--snapshots",
            str(tmp_path / "missing.csv"),
            "--rows-output",
            str(tmp_path / "rows.csv"),
            "--summary-output",
            str(tmp_path / "summary.csv"),
            "--metadata-output",
            str(tmp_path / "metadata.json"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "ERROR: Monitor v2 snapshot file not found" in captured.err


def _single_metric_snapshots(
    *,
    baseline_values: list[float],
    spike: float,
) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01T00:00:00Z", periods=len(baseline_values) + 1, freq="D")
    values = [*baseline_values, spike]
    return pd.DataFrame(
        [
            {
                "timestamp_utc": timestamp.isoformat().replace("+00:00", "Z"),
                "market_id": "mock_market",
                "tier": "market",
                "anomaly_family": "market_move",
                "metric_name": "absolute_midpoint_change",
                "observed_value": value,
                "event_candidate_id": "",
                "event_review_status": "",
                "evidence_ref": "toy_snapshot",
                "limitation": "toy data",
                "review_status": "candidate",
            }
            for timestamp, value in zip(dates, values)
        ]
    )
