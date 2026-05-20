from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from operations.analysis.monitor_v2_recorded_input_scoring import (
    build_recorded_scoring_snapshots,
    generate_recorded_monitor_v2_scoring_outputs,
    main,
)
from operations.analysis.monitor_v2_snapshot import SNAPSHOT_COLUMNS


def test_build_recorded_scoring_snapshots_from_validated_inputs() -> None:
    snapshots = build_recorded_scoring_snapshots(
        _watchlist(),
        _market_snapshots(),
        _wallet_tier_snapshots(),
        _event_candidates(),
    )

    assert tuple(snapshots.columns) == SNAPSHOT_COLUMNS
    assert "wallet_address" not in snapshots.columns
    assert set(snapshots["market_id"]) == {"toy_replay_market"}
    assert {"market_move", "wallet_tier_activity", "active_wallet_activity", "concentration"}.issubset(
        set(snapshots["anomaly_family"])
    )
    event_rows = snapshots[snapshots["event_candidate_id"] == "evt_spike"]
    assert not event_rows.empty
    assert set(event_rows["event_review_status"]) == {"accepted"}


def test_generate_recorded_scoring_outputs_writes_bounded_artifacts(tmp_path: Path) -> None:
    watchlist_path = tmp_path / "watchlist.csv"
    market_path = tmp_path / "market.csv"
    wallet_path = tmp_path / "wallet.csv"
    event_path = tmp_path / "events.csv"
    snapshots_path = tmp_path / "snapshots.csv"
    rows_path = tmp_path / "rows.csv"
    summary_path = tmp_path / "summary.csv"
    context_path = tmp_path / "context.csv"
    report_path = tmp_path / "validation_report.json"
    metadata_path = tmp_path / "metadata.json"
    _watchlist().to_csv(watchlist_path, index=False)
    _market_snapshots().to_csv(market_path, index=False)
    _wallet_tier_snapshots().to_csv(wallet_path, index=False)
    _event_candidates().to_csv(event_path, index=False)

    result = generate_recorded_monitor_v2_scoring_outputs(
        watchlist_path=watchlist_path,
        market_snapshots_path=market_path,
        wallet_tier_snapshots_path=wallet_path,
        event_candidates_path=event_path,
        snapshots_path=snapshots_path,
        rows_path=rows_path,
        summary_path=summary_path,
        context_rows_path=context_path,
        validation_report_path=report_path,
        metadata_path=metadata_path,
        baseline_observations=5,
        min_baseline_observations=5,
    )

    snapshots = pd.read_csv(snapshots_path)
    rows = pd.read_csv(rows_path)
    summary = pd.read_csv(summary_path)
    context = pd.read_csv(context_path)
    validation_report = json.loads(report_path.read_text(encoding="utf-8"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert result.snapshot_count == len(snapshots)
    assert result.alert_row_count == len(rows)
    assert result.summary_row_count == len(summary)
    assert result.context_row_count == len(context)
    assert validation_report["status"] == "pass"
    assert metadata["method"]["validates_inputs_before_scoring"] is True
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["contains_order_instructions"] is False
    assert metadata["limitations"]["no_live_websocket_or_api_collection"] is True
    assert metadata["limitations"]["does_not_use_agents_or_mcp"] is True
    assert "critical" in set(rows["severity"])
    assert "critical_proximity_candidate" in set(context["suggested_context_label"])
    for frame in (snapshots, rows, summary, context):
        assert "wallet_address" not in frame.columns


def test_wallet_address_is_rejected_before_scoring(tmp_path: Path) -> None:
    watchlist_path = tmp_path / "watchlist.csv"
    market_path = tmp_path / "market.csv"
    wallet_path = tmp_path / "wallet.csv"
    event_path = tmp_path / "events.csv"
    _watchlist().to_csv(watchlist_path, index=False)
    _market_snapshots().to_csv(market_path, index=False)
    wallets = _wallet_tier_snapshots()
    wallets["wallet_address"] = "0x" + "1" * 40
    wallets.to_csv(wallet_path, index=False)
    _event_candidates().to_csv(event_path, index=False)

    exit_code = main(
        [
            "--watchlist",
            str(watchlist_path),
            "--market-snapshots",
            str(market_path),
            "--wallet-tier-snapshots",
            str(wallet_path),
            "--event-candidates",
            str(event_path),
            "--snapshots-output",
            str(tmp_path / "snapshots.csv"),
            "--rows-output",
            str(tmp_path / "rows.csv"),
            "--summary-output",
            str(tmp_path / "summary.csv"),
            "--context-rows-output",
            str(tmp_path / "context.csv"),
            "--validation-report-output",
            str(tmp_path / "report.json"),
            "--metadata-output",
            str(tmp_path / "metadata.json"),
        ]
    )

    assert exit_code == 2
    assert not (tmp_path / "rows.csv").exists()


def test_cli_returns_clear_error_for_missing_input_file(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = main(
        [
            "--watchlist",
            str(tmp_path / "missing_watchlist.csv"),
            "--market-snapshots",
            str(tmp_path / "market.csv"),
            "--wallet-tier-snapshots",
            str(tmp_path / "wallet.csv"),
            "--event-candidates",
            str(tmp_path / "events.csv"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "ERROR: Recorded monitor v2 input file not found" in captured.err


def _watchlist() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "watch_id": "watch_toy",
                "market_id": "toy_replay_market",
                "condition_id": "condition_toy",
                "token_ids": "token_yes",
                "question": "Toy politics market",
                "category": "politics",
                "subcategory": "test",
                "status": "active",
                "source": "toy_fixture",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-08T00:00:00Z",
            }
        ]
    )


def _market_snapshots() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01T00:00:00Z", periods=8, freq="D")
    prices = [0.50, 0.51, 0.505, 0.515, 0.507, 0.516, 0.508, 0.70]
    return pd.DataFrame(
        [
            {
                "timestamp_utc": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "market_id": "toy_replay_market",
                "token_id": "token_yes",
                "price": price,
                "midpoint": price,
                "best_bid": None,
                "best_ask": None,
                "spread": None,
                "volume": None,
                "open_interest": None,
                "source": "toy_market_snapshots",
            }
            for timestamp, price in zip(dates, prices)
        ]
    )


def _wallet_tier_snapshots() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01T00:00:00Z", periods=8, freq="D")
    rows: list[dict[str, object]] = []
    for index, timestamp in enumerate(dates):
        for tier in (
            "tier_1_top_1pct",
            "tier_2_top_5pct",
            "tier_3_top_10pct",
            "tier_4_observed_baseline",
        ):
            is_event_day = timestamp.date().isoformat() == "2024-01-08"
            is_top_tier = tier == "tier_1_top_1pct"
            amount = 1000.0 + 20.0 * index
            active_wallets = 2
            top_tier_share = 0.25
            hhi = 0.25
            if is_event_day and is_top_tier:
                amount = 120000.0
                active_wallets = 30
                top_tier_share = 0.98
                hhi = 0.96
            elif is_event_day:
                amount = 100.0
                active_wallets = 1
                top_tier_share = 0.98
                hhi = 0.96
            rows.append(
                {
                    "timestamp_utc": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "market_id": "toy_replay_market",
                    "bucket": "daily",
                    "tier": tier,
                    "active_wallets": active_wallets,
                    "trade_count": 5,
                    "total_observed_amount_usd": amount,
                    "top_tier_share": top_tier_share,
                    "hhi_concentration": hhi,
                    "source": "toy_wallet_snapshots",
                    "filter_metadata": "buy_side_observed_extract",
                }
            )
    return pd.DataFrame(rows)


def _event_candidates() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "event_candidate_id": "evt_spike",
                "detected_at_utc": "2024-01-08T12:00:00Z",
                "published_at_utc": "2024-01-08T12:00:00Z",
                "title": "Toy event spike",
                "source_url": "https://example.com/toy-event",
                "event_type": "major_news",
                "related_market_ids": "toy_replay_market",
                "expected_effect": "uncertainty_change",
                "review_status": "accepted",
                "review_notes": "toy accepted candidate",
            }
        ]
    )
