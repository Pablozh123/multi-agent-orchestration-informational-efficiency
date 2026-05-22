from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.monitor_v2_live_input_batch import (
    build_mock_live_event_candidates,
    build_mock_live_market_snapshots,
    build_mock_live_wallet_tier_snapshots,
    build_mock_live_watchlist,
    generate_local_live_input_batch,
)
from operations.analysis.monitor_v2_live_input_scoring import (
    build_live_scoring_snapshots,
    generate_live_monitor_v2_scoring_outputs,
    main,
)
from operations.analysis.monitor_v2_snapshot import SNAPSHOT_COLUMNS


def test_build_live_scoring_snapshots_from_validated_inputs() -> None:
    snapshots = build_live_scoring_snapshots(
        build_mock_live_watchlist(),
        build_mock_live_market_snapshots(),
        build_mock_live_wallet_tier_snapshots(),
        build_mock_live_event_candidates(),
    )

    assert tuple(snapshots.columns) == SNAPSHOT_COLUMNS
    assert "wallet_address" not in snapshots.columns
    assert set(snapshots["market_id"]) == {"mock_polymarket_politics_geo_001"}
    assert {"market_move", "wallet_tier_activity", "active_wallet_activity", "concentration"}.issubset(
        set(snapshots["anomaly_family"])
    )
    before_event = snapshots[snapshots["timestamp_utc"] == "2026-05-20T00:15:00Z"]
    after_event = snapshots[snapshots["timestamp_utc"] == "2026-05-20T00:30:00Z"]
    assert set(before_event["event_candidate_id"]) == {""}
    assert set(after_event["event_candidate_id"]) == {"event_candidate_mock_geo_001"}


def test_generate_live_scoring_outputs_writes_diagnostic_artifacts(tmp_path: Path) -> None:
    input_paths = _input_paths(tmp_path / "inputs")
    output_paths = _output_paths(tmp_path / "outputs")
    _write_live_input_batch(input_paths, tmp_path / "batch")

    result = generate_live_monitor_v2_scoring_outputs(**input_paths, **output_paths)

    snapshots = pd.read_csv(output_paths["snapshots_path"])
    rows = pd.read_csv(output_paths["rows_path"])
    summary = pd.read_csv(output_paths["summary_path"])
    validation_report = json.loads(
        output_paths["validation_report_path"].read_text(encoding="utf-8")
    )
    metadata = json.loads(output_paths["metadata_path"].read_text(encoding="utf-8"))
    assert result.snapshot_count == len(snapshots)
    assert result.alert_row_count == len(rows)
    assert result.summary_row_count == len(summary)
    assert validation_report["status"] == "pass"
    assert metadata["method"]["validates_inputs_before_scoring"] is True
    assert metadata["method"]["scores_closed_buckets_only"] is True
    assert metadata["method"]["diagnostic_file_baseline_only"] is True
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["contains_order_instructions"] is False
    assert metadata["limitations"]["does_not_collect_external_data"] is True
    assert metadata["limitations"]["input_files_may_be_mock_or_read_only_collector"] is True
    assert metadata["limitations"]["does_not_use_agents_or_mcp"] is True
    for frame in (snapshots, rows, summary):
        assert "wallet_address" not in frame.columns
    assert set(rows["status"]).issuperset({"insufficient_baseline", "ok"})


def test_live_scoring_outputs_are_deterministic_except_metadata(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    _write_live_input_batch(_input_paths(first / "inputs"), first / "batch")
    _write_live_input_batch(_input_paths(second / "inputs"), second / "batch")

    generate_live_monitor_v2_scoring_outputs(
        **_input_paths(first / "inputs"),
        **_output_paths(first / "outputs"),
    )
    generate_live_monitor_v2_scoring_outputs(
        **_input_paths(second / "inputs"),
        **_output_paths(second / "outputs"),
    )

    for name in ("snapshots.csv", "rows.csv", "summary.csv"):
        assert (first / "outputs" / name).read_text(encoding="utf-8") == (
            second / "outputs" / name
        ).read_text(encoding="utf-8")


def test_wallet_address_is_rejected_before_live_scoring(tmp_path: Path) -> None:
    input_paths = _input_paths(tmp_path / "inputs")
    output_paths = _output_paths(tmp_path / "outputs")
    _write_live_input_batch(input_paths, tmp_path / "batch")
    wallet_frame = pd.read_csv(input_paths["wallet_tier_snapshots_path"])
    wallet_frame["wallet_address"] = "0x" + "1" * 40
    wallet_frame.to_csv(input_paths["wallet_tier_snapshots_path"], index=False)

    exit_code = main(_cli_args(input_paths, output_paths))

    assert exit_code == 2
    assert not output_paths["rows_path"].exists()


def test_unknown_market_is_rejected_before_live_scoring(tmp_path: Path) -> None:
    input_paths = _input_paths(tmp_path / "inputs")
    output_paths = _output_paths(tmp_path / "outputs")
    _write_live_input_batch(input_paths, tmp_path / "batch")
    market_frame = pd.read_csv(input_paths["market_snapshots_path"])
    market_frame.loc[0, "market_id"] = "unknown_market"
    market_frame.to_csv(input_paths["market_snapshots_path"], index=False)

    with pytest.raises(ValueError, match="outside watchlist"):
        generate_live_monitor_v2_scoring_outputs(**input_paths, **output_paths)


def test_cli_returns_clear_error_for_missing_live_input_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_paths = _input_paths(tmp_path / "missing")
    output_paths = _output_paths(tmp_path / "outputs")

    exit_code = main(_cli_args(input_paths, output_paths))

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "ERROR: Monitor v2 live input file not found" in captured.err


def _input_paths(root: Path) -> dict[str, Path]:
    return {
        "watchlist_path": root / "watchlist.csv",
        "market_snapshots_path": root / "market.csv",
        "wallet_tier_snapshots_path": root / "wallet.csv",
        "event_candidates_path": root / "events.csv",
    }


def _output_paths(root: Path) -> dict[str, Path]:
    return {
        "snapshots_path": root / "snapshots.csv",
        "rows_path": root / "rows.csv",
        "summary_path": root / "summary.csv",
        "validation_report_path": root / "report.json",
        "metadata_path": root / "metadata.json",
    }


def _write_live_input_batch(input_paths: dict[str, Path], report_root: Path) -> None:
    generate_local_live_input_batch(
        **input_paths,
        validation_report_path=report_root / "report.json",
        metadata_path=report_root / "metadata.json",
        generated_at_utc="2026-05-20T12:00:00Z",
    )


def _cli_args(input_paths: dict[str, Path], output_paths: dict[str, Path]) -> list[str]:
    return [
        "--watchlist",
        str(input_paths["watchlist_path"]),
        "--market-snapshots",
        str(input_paths["market_snapshots_path"]),
        "--wallet-tier-snapshots",
        str(input_paths["wallet_tier_snapshots_path"]),
        "--event-candidates",
        str(input_paths["event_candidates_path"]),
        "--snapshots-output",
        str(output_paths["snapshots_path"]),
        "--rows-output",
        str(output_paths["rows_path"]),
        "--summary-output",
        str(output_paths["summary_path"]),
        "--validation-report-output",
        str(output_paths["validation_report_path"]),
        "--metadata-output",
        str(output_paths["metadata_path"]),
    ]
