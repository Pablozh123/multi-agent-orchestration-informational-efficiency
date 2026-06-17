from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from operations.analysis.monitor_v2_polymarket_rolling_figures import (
    MAX_WALLET_BUCKET_LABELS,
    generate_polymarket_rolling_history_figure,
)
from operations.collectors.polymarket_rolling_history import (
    collect_polymarket_rolling_history,
    main,
)


COLLECTED_AT = "2026-05-22T12:07:30Z"


def test_collect_mock_rolling_history_scores_and_figures(tmp_path: Path) -> None:
    paths = _paths(tmp_path)

    result = collect_polymarket_rolling_history(
        source="mock",
        samples=4,
        delay_seconds=0,
        reset_outputs=True,
        collected_at_utc=COLLECTED_AT,
        **paths,
    )

    market = pd.read_csv(paths["market_snapshots_path"])
    wallets = pd.read_csv(paths["wallet_tier_snapshots_path"])
    alert_rows = pd.read_csv(paths["scoring_rows_path"])
    metadata = json.loads(paths["metadata_path"].read_text(encoding="utf-8"))
    scoring_metadata = json.loads(
        paths["scoring_metadata_path"].read_text(encoding="utf-8")
    )
    assert result.samples_completed == 4
    assert result.bucket_count == 4
    assert len(market) == 8
    assert len(wallets) == 4
    assert len(alert_rows) > 0
    assert paths["figure_path"].exists()
    assert paths["figure_path"].stat().st_size > 0
    assert metadata["method"]["bounded_loop_not_daemon"] is True
    assert metadata["method"]["appends_and_deduplicates_outputs"] is True
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["contains_order_instructions"] is False
    assert scoring_metadata["method"]["baseline_readiness"] in {
        "baseline_available_zero_mad_or_non_alerting",
        "diagnostic_scores_available",
    }
    assert set(alert_rows["status"]).issuperset({"insufficient_baseline"})
    assert "wallet_address" not in market.columns
    assert "wallet_address" not in wallets.columns


def test_collect_mock_rolling_history_accepts_curated_watchlist(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    curated_path = _curated_watchlist_path(tmp_path)

    result = collect_polymarket_rolling_history(
        source="mock",
        samples=2,
        delay_seconds=0,
        reset_outputs=True,
        collected_at_utc=COLLECTED_AT,
        curated_watchlist_path=curated_path,
        **paths,
    )

    watchlist = pd.read_csv(paths["watchlist_path"])
    metadata = json.loads(paths["metadata_path"].read_text(encoding="utf-8"))
    assert result.samples_completed == 2
    assert len(watchlist) == 1
    assert watchlist.iloc[0]["watch_id"] == "accepted_001"
    assert metadata["method"]["uses_curated_watchlist"] is True
    assert metadata["method"]["curated_watchlist_path"] == str(curated_path)


def test_rolling_history_figure_labels_only_top_six_wallet_buckets(tmp_path: Path) -> None:
    watchlist_path = tmp_path / "watchlist.csv"
    market_path = tmp_path / "market.csv"
    wallet_path = tmp_path / "wallet.csv"
    figure_path = tmp_path / "rolling.png"
    metadata_path = tmp_path / "figure_metadata.json"
    scoring_metadata_path = tmp_path / "scoring_metadata.json"
    timestamps = pd.date_range("2026-05-22T12:00:00Z", periods=8, freq="15min")
    amounts = [10.0, 70.0, 30.0, 90.0, 20.0, 80.0, 40.0, 60.0]

    pd.DataFrame(
        [
            {
                "market_id": "market_001",
                "question": "Fixture market with repeated rolling buckets",
            }
        ]
    ).to_csv(watchlist_path, index=False)
    pd.DataFrame(
        [
            {
                "market_id": "market_001",
                "token_id": "token_yes",
                "bucket_end_utc": timestamp.isoformat(),
                "midpoint": 0.45 + index * 0.01,
            }
            for index, timestamp in enumerate(timestamps)
        ]
    ).to_csv(market_path, index=False)
    pd.DataFrame(
        [
            {
                "market_id": "market_001",
                "bucket_end_utc": timestamp.isoformat(),
                "total_observed_amount_usd": amount,
                "active_wallets": index + 1,
            }
            for index, (timestamp, amount) in enumerate(zip(timestamps, amounts))
        ]
    ).to_csv(wallet_path, index=False)
    scoring_metadata_path.write_text(
        json.dumps({"method": {"baseline_readiness": "fixture"}}),
        encoding="utf-8",
    )

    generate_polymarket_rolling_history_figure(
        watchlist_path=watchlist_path,
        market_snapshots_path=market_path,
        wallet_tier_snapshots_path=wallet_path,
        scoring_metadata_path=scoring_metadata_path,
        figure_path=figure_path,
        metadata_path=metadata_path,
    )

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    labels = metadata["outputs"]["wallet_bucket_labels"]
    labeled_amounts = [label["total_observed_amount_usd"] for label in labels]

    assert figure_path.exists()
    assert metadata["outputs"]["wallet_bucket_label_count"] == MAX_WALLET_BUCKET_LABELS
    assert metadata["outputs"]["wallet_bucket_label_max_count"] == MAX_WALLET_BUCKET_LABELS
    assert metadata["outputs"]["wallet_bucket_label_rule"] == (
        "top_6_by_total_observed_amount_usd_tie_timestamp_ascending"
    )
    assert metadata["outputs"]["wallet_bucket_label_layout"] == (
        "rank_staggered_offsets_points"
    )
    assert set(labeled_amounts) == {30.0, 40.0, 60.0, 70.0, 80.0, 90.0}
    assert 10.0 not in labeled_amounts
    assert 20.0 not in labeled_amounts
    assert metadata["outputs"]["figure_aspect_ratio"] == 12.0 / 7.0
    assert metadata["outputs"]["contains_wallet_addresses"] is False


def test_rolling_history_rejects_zero_samples(tmp_path: Path) -> None:
    paths = _paths(tmp_path)

    exit_code = main(
        [
            "--source",
            "mock",
            "--samples",
            "0",
            "--metadata-output",
            str(paths["metadata_path"]),
        ]
    )

    assert exit_code == 2
    assert not paths["metadata_path"].exists()


def test_rolling_history_cli_writes_outputs(tmp_path: Path, capsys) -> None:
    paths = _paths(tmp_path)

    exit_code = main(
        [
            "--source",
            "mock",
            "--samples",
            "3",
            "--reset",
            "--collected-at-utc",
            COLLECTED_AT,
            *_cli_paths(paths),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "baseline_readiness" in captured.out
    assert paths["metadata_path"].exists()


def _paths(root: Path) -> dict[str, Path]:
    return {
        "watchlist_path": root / "watchlist.csv",
        "market_snapshots_path": root / "market.csv",
        "wallet_tier_snapshots_path": root / "wallet.csv",
        "event_candidates_path": root / "events.csv",
        "validation_report_path": root / "validation_report.json",
        "collector_metadata_path": root / "collector_metadata.json",
        "scoring_snapshots_path": root / "scoring_snapshots.csv",
        "scoring_rows_path": root / "scoring_rows.csv",
        "scoring_summary_path": root / "scoring_summary.csv",
        "scoring_validation_report_path": root / "scoring_validation_report.json",
        "scoring_metadata_path": root / "scoring_metadata.json",
        "figure_path": root / "rolling.png",
        "figure_metadata_path": root / "figure_metadata.json",
        "metadata_path": root / "rolling_metadata.json",
    }


def _curated_watchlist_path(root: Path) -> Path:
    path = root / "curated_watchlist.csv"
    pd.DataFrame(
        [
            {
                "watch_id": "accepted_001",
                "market_id": "0x" + "a" * 64,
                "condition_id": "0x" + "a" * 64,
                "token_ids": "111,222",
                "question": "Will a major election market resolve yes?",
                "category": "politics",
                "subcategory": "major-election-market",
                "monitoring_scope": "election",
                "review_status": "accepted",
                "source_url": "https://gamma-api.polymarket.com/markets?id=accepted_001",
                "inclusion_reason": "official_gamma_active_us_election_market",
                "exclusion_reason": "",
                "reviewed_by": "codex_test",
                "reviewed_at_utc": "2026-05-22T12:00:00Z",
                "notes": "fixture",
            }
        ]
    ).to_csv(path, index=False)
    return path


def _cli_paths(paths: dict[str, Path]) -> list[str]:
    return [
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
        "--collector-metadata-output",
        str(paths["collector_metadata_path"]),
        "--scoring-snapshots-output",
        str(paths["scoring_snapshots_path"]),
        "--scoring-rows-output",
        str(paths["scoring_rows_path"]),
        "--scoring-summary-output",
        str(paths["scoring_summary_path"]),
        "--scoring-validation-report-output",
        str(paths["scoring_validation_report_path"]),
        "--scoring-metadata-output",
        str(paths["scoring_metadata_path"]),
        "--figure-output",
        str(paths["figure_path"]),
        "--figure-metadata-output",
        str(paths["figure_metadata_path"]),
        "--metadata-output",
        str(paths["metadata_path"]),
    ]
