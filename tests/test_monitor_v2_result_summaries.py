from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.monitor_v2_result_summaries import (
    SUMMARY_COLUMNS,
    generate_monitor_v2_bounded_summaries,
    main,
)


def test_generate_monitor_v2_bounded_summaries_writes_traceable_outputs(
    tmp_path: Path,
) -> None:
    _write_source_artifacts(tmp_path)

    result = generate_monitor_v2_bounded_summaries(
        alert_rows_path=tmp_path / "alert_rows.csv",
        alert_summary_path=tmp_path / "alert_summary.csv",
        context_rows_path=tmp_path / "context_rows.csv",
        validation_report_path=tmp_path / "validation_report.json",
        scoring_metadata_path=tmp_path / "scoring_metadata.json",
        summary_path=tmp_path / "bounded_summary.csv",
        metadata_path=tmp_path / "bounded_metadata.json",
    )

    summary = pd.read_csv(result.summary_path)
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    assert tuple(summary.columns) == SUMMARY_COLUMNS
    assert result.row_count == len(summary)
    assert summary["source_artifact"].str.len().gt(0).all()
    assert summary["allowed_interpretation"].str.len().gt(0).all()
    assert summary["limitation"].str.len().gt(0).all()
    assert metadata["method"]["does_not_use_llms"] is True
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["contains_order_instructions"] is False
    assert "monitor_v2_severity_high" in set(summary["summary_id"])
    assert "monitor_v2_context_critical_proximity_candidate" in set(summary["summary_id"])


def test_bounded_summary_contains_no_wallet_addresses(tmp_path: Path) -> None:
    _write_source_artifacts(tmp_path)

    result = generate_monitor_v2_bounded_summaries(
        alert_rows_path=tmp_path / "alert_rows.csv",
        alert_summary_path=tmp_path / "alert_summary.csv",
        context_rows_path=tmp_path / "context_rows.csv",
        validation_report_path=tmp_path / "validation_report.json",
        scoring_metadata_path=tmp_path / "scoring_metadata.json",
        summary_path=tmp_path / "bounded_summary.csv",
        metadata_path=tmp_path / "bounded_metadata.json",
    )

    text = result.summary_path.read_text(encoding="utf-8")
    summary = pd.read_csv(result.summary_path)
    assert "wallet_address" not in summary.columns
    assert "0x" not in text


def test_wallet_address_column_is_rejected(tmp_path: Path) -> None:
    _write_source_artifacts(tmp_path)
    rows = pd.read_csv(tmp_path / "alert_rows.csv")
    rows["wallet_address"] = "0x" + "1" * 40
    rows.to_csv(tmp_path / "alert_rows.csv", index=False)

    with pytest.raises(ValueError, match="must not contain wallet_address"):
        generate_monitor_v2_bounded_summaries(
            alert_rows_path=tmp_path / "alert_rows.csv",
            alert_summary_path=tmp_path / "alert_summary.csv",
            context_rows_path=tmp_path / "context_rows.csv",
            validation_report_path=tmp_path / "validation_report.json",
            scoring_metadata_path=tmp_path / "scoring_metadata.json",
            summary_path=tmp_path / "bounded_summary.csv",
            metadata_path=tmp_path / "bounded_metadata.json",
        )


def test_cli_returns_clear_error_for_missing_artifacts(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "--alert-rows",
            str(tmp_path / "missing.csv"),
            "--alert-summary",
            str(tmp_path / "alert_summary.csv"),
            "--context-rows",
            str(tmp_path / "context_rows.csv"),
            "--validation-report",
            str(tmp_path / "validation_report.json"),
            "--scoring-metadata",
            str(tmp_path / "scoring_metadata.json"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "ERROR: Required monitor v2 summary source artifact missing" in captured.err


def _write_source_artifacts(path: Path) -> None:
    pd.DataFrame(
        [
            {
                "severity": "none",
                "anomaly_family": "market_move",
                "metric_name": "absolute_midpoint_change",
                "claim_scope": "descriptive_monitor_alert_only",
            },
            {
                "severity": "high",
                "anomaly_family": "wallet_tier_activity",
                "metric_name": "log1p_total_observed_amount_usd",
                "claim_scope": "descriptive_monitor_alert_only",
            },
        ]
    ).to_csv(path / "alert_rows.csv", index=False)
    pd.DataFrame(
        [
            {
                "anomaly_family": "wallet_tier_activity",
                "metric_name": "log1p_total_observed_amount_usd",
                "alert_count": 5,
                "max_severity": "high",
                "max_robust_z": 3.2,
            },
            {
                "anomaly_family": "market_move",
                "metric_name": "absolute_midpoint_change",
                "alert_count": 2,
                "max_severity": "watch",
                "max_robust_z": 2.1,
            },
        ]
    ).to_csv(path / "alert_summary.csv", index=False)
    pd.DataFrame(
        [
            {"suggested_context_label": "critical_proximity_candidate"},
            {"suggested_context_label": "event_watch_candidate"},
        ]
    ).to_csv(path / "context_rows.csv", index=False)
    (path / "validation_report.json").write_text(
        json.dumps({"status": "pass"}),
        encoding="utf-8",
    )
    (path / "scoring_metadata.json").write_text(
        json.dumps(
            {
                "outputs": {
                    "snapshot_count": 2,
                    "alert_row_count": 2,
                    "summary_row_count": 2,
                    "context_row_count": 2,
                }
            }
        ),
        encoding="utf-8",
    )
