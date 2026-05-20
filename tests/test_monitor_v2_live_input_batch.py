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
    main,
    validate_live_batch_consistency,
)
from operations.analysis.monitor_v2_live_input_validation import validate_live_input_files


def test_generate_local_live_input_batch_writes_and_validates_files(tmp_path: Path) -> None:
    paths = _paths(tmp_path)

    result = generate_local_live_input_batch(**paths, generated_at_utc="2026-05-20T12:00:00Z")

    assert result.watchlist_row_count == 1
    assert result.market_snapshot_row_count == 4
    assert result.wallet_tier_snapshot_row_count == 8
    assert result.event_candidate_row_count == 1
    for path in paths.values():
        if isinstance(path, Path):
            assert path.exists()

    report = json.loads(paths["validation_report_path"].read_text(encoding="utf-8"))
    metadata = json.loads(paths["metadata_path"].read_text(encoding="utf-8"))
    assert report["status"] == "pass"
    assert report["generated_at_utc"] == "2026-05-20T12:00:00Z"
    assert metadata["method"]["bucket_minutes"] == 15
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["limitations"]["does_not_call_external_apis"] is True
    assert metadata["limitations"]["does_not_connect_to_websocket"] is True


def test_generated_live_input_files_are_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"

    generate_local_live_input_batch(
        **_paths(first),
        generated_at_utc="2026-05-20T12:00:00Z",
    )
    generate_local_live_input_batch(
        **_paths(second),
        generated_at_utc="2026-05-20T12:00:00Z",
    )

    for name in (
        "watchlist.csv",
        "market.csv",
        "wallet.csv",
        "events.csv",
    ):
        assert (first / name).read_text(encoding="utf-8") == (
            second / name
        ).read_text(encoding="utf-8")


def test_generated_live_inputs_validate_through_validator(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    generate_local_live_input_batch(**paths)

    report = validate_live_input_files(
        watchlist_path=paths["watchlist_path"],
        market_snapshots_path=paths["market_snapshots_path"],
        wallet_tier_snapshots_path=paths["wallet_tier_snapshots_path"],
        event_candidates_path=paths["event_candidates_path"],
        report_output_path=None,
    )

    assert report["status"] == "pass"
    assert report["validated_inputs"]["wallet_tier_snapshots"]["row_count"] == 8


def test_generated_live_inputs_do_not_emit_wallet_address_fields(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    generate_local_live_input_batch(**paths)

    for path_key in (
        "watchlist_path",
        "market_snapshots_path",
        "wallet_tier_snapshots_path",
        "event_candidates_path",
    ):
        frame = pd.read_csv(paths[path_key])
        assert not any("wallet_address" in column.lower() for column in frame.columns)


def test_live_batch_consistency_rejects_unknown_market_reference() -> None:
    watchlist = build_mock_live_watchlist()
    market = build_mock_live_market_snapshots()
    wallets = build_mock_live_wallet_tier_snapshots(market_id="unknown_market")
    events = build_mock_live_event_candidates()

    with pytest.raises(ValueError, match="outside watchlist"):
        validate_live_batch_consistency(
            watchlist=watchlist,
            market_snapshots=market,
            wallet_tier_snapshots=wallets,
            event_candidates=events,
        )


def test_live_batch_consistency_rejects_unmapped_accepted_event() -> None:
    watchlist = build_mock_live_watchlist()
    market = build_mock_live_market_snapshots()
    wallets = build_mock_live_wallet_tier_snapshots()
    events = build_mock_live_event_candidates()
    events.loc[0, "related_market_ids"] = "unknown_market"

    with pytest.raises(ValueError, match="watchlist market"):
        validate_live_batch_consistency(
            watchlist=watchlist,
            market_snapshots=market,
            wallet_tier_snapshots=wallets,
            event_candidates=events,
        )


def test_cli_writes_local_live_batch(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    paths = _paths(tmp_path)

    exit_code = main(
        [
            "--watchlist-output",
            str(paths["watchlist_path"]),
            "--market-snapshots-output",
            str(paths["market_snapshots_path"]),
            "--wallet-tier-snapshots-output",
            str(paths["wallet_tier_snapshots_path"]),
            "--event-candidates-output",
            str(paths["event_candidates_path"]),
            "--validation-report-output",
            str(paths["validation_report_path"]),
            "--metadata-output",
            str(paths["metadata_path"]),
            "--generated-at-utc",
            "2026-05-20T12:00:00Z",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "watchlist_row_count" in captured.out
    assert paths["metadata_path"].exists()


def _paths(root: Path) -> dict[str, Path]:
    return {
        "watchlist_path": root / "watchlist.csv",
        "market_snapshots_path": root / "market.csv",
        "wallet_tier_snapshots_path": root / "wallet.csv",
        "event_candidates_path": root / "events.csv",
        "validation_report_path": root / "report.json",
        "metadata_path": root / "metadata.json",
    }
