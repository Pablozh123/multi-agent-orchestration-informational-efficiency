from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from operations.analysis.monitor_v2_threshold_sensitivity import (
    SensitivityScenario,
    generate_threshold_sensitivity_report,
    main,
)


def test_threshold_sensitivity_writes_aggregate_reports(tmp_path: Path) -> None:
    snapshots_path = tmp_path / "snapshots.csv"
    summary_path = tmp_path / "summary.csv"
    by_family_path = tmp_path / "by_family.csv"
    figure_path = tmp_path / "figure.png"
    metadata_path = tmp_path / "metadata.json"
    _constant_snapshots(periods=21).to_csv(snapshots_path, index=False)

    result = generate_threshold_sensitivity_report(
        snapshots_path=snapshots_path,
        summary_path=summary_path,
        by_family_path=by_family_path,
        figure_path=figure_path,
        metadata_path=metadata_path,
    )

    summary = pd.read_csv(summary_path)
    by_family = pd.read_csv(by_family_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert result.scenario_count == 4
    assert result.default_alert_count == 0
    assert figure_path.exists()
    assert "default_rule_c_30_20" in set(summary["scenario_id"])
    assert "wallet_address" not in summary.columns
    assert "wallet_address" not in by_family.columns
    assert metadata["method"]["default_rule_unchanged"] is True
    assert metadata["method"]["non_default_scenarios_are_diagnostic_only"] is True
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["contains_order_instructions"] is False
    assert metadata["limitations"]["does_not_use_agents_or_mcp"] is True


def test_diagnostic_scenario_can_surface_relaxed_alerts(tmp_path: Path) -> None:
    snapshots_path = tmp_path / "snapshots.csv"
    summary_path = tmp_path / "summary.csv"
    _spike_snapshots().to_csv(snapshots_path, index=False)

    generate_threshold_sensitivity_report(
        snapshots_path=snapshots_path,
        summary_path=summary_path,
        by_family_path=tmp_path / "by_family.csv",
        figure_path=tmp_path / "figure.png",
        metadata_path=tmp_path / "metadata.json",
        scenarios=(
            SensitivityScenario(
                scenario_id="toy_rule_c_5_5",
                scenario_type="diagnostic_sensitivity",
                baseline_observations=5,
                min_baseline_observations=5,
                rule_label="toy diagnostic",
            ),
        ),
    )

    summary = pd.read_csv(summary_path)
    row = summary.iloc[0]
    assert row["alert_count"] == 1
    assert row["high_count"] == 1
    assert row["likely_driver"] == "diagnostic_alerts_under_relaxed_baseline"


def test_cli_returns_clear_error_for_missing_snapshot_file(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = main(
        [
            "--snapshots",
            str(tmp_path / "missing.csv"),
            "--summary-output",
            str(tmp_path / "summary.csv"),
            "--by-family-output",
            str(tmp_path / "by_family.csv"),
            "--figure-output",
            str(tmp_path / "figure.png"),
            "--metadata-output",
            str(tmp_path / "metadata.json"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "ERROR: Monitor v2 snapshot file not found" in captured.err


def _constant_snapshots(periods: int) -> pd.DataFrame:
    timestamps = pd.date_range("2026-01-01T00:00:00Z", periods=periods, freq="5min")
    return pd.DataFrame(
        [
            {
                "timestamp_utc": timestamp.isoformat().replace("+00:00", "Z"),
                "market_id": "toy_market",
                "tier": "all_tiers",
                "anomaly_family": "active_wallet_activity",
                "metric_name": "active_wallets",
                "observed_value": 0.0,
                "event_candidate_id": "",
                "event_review_status": "",
                "evidence_ref": "toy_snapshot",
                "limitation": "toy data",
                "review_status": "candidate",
            }
            for timestamp in timestamps
        ]
    )


def _spike_snapshots() -> pd.DataFrame:
    timestamps = pd.date_range("2026-01-01T00:00:00Z", periods=6, freq="5min")
    values = [10.0, 10.2, 9.9, 10.1, 9.8, 30.0]
    return pd.DataFrame(
        [
            {
                "timestamp_utc": timestamp.isoformat().replace("+00:00", "Z"),
                "market_id": "toy_market",
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
            for timestamp, value in zip(timestamps, values)
        ]
    )
