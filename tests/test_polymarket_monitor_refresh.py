from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.collectors.polymarket_monitor_refresh import (
    main,
    run_polymarket_monitor_refresh,
)
from operations.collectors.polymarket_watchlist import CURATED_WATCHLIST_COLUMNS


COLLECTED_AT = "2026-05-22T12:07:30Z"


def test_run_polymarket_monitor_refresh_writes_dashboard_and_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    curated_path = _curated_watchlist_path(tmp_path)

    result = run_polymarket_monitor_refresh(
        source="mock",
        samples=3,
        reset_outputs=True,
        collected_at_utc=COLLECTED_AT,
        curated_watchlist_path=curated_path,
        baseline_observations=30,
        min_baseline_observations=20,
    )

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    scoring_metadata = json.loads(
        Path("data/results/monitor_v2_polymarket_rolling_scoring_metadata.json").read_text(
            encoding="utf-8",
        )
    )
    assert result.samples_completed == 3
    assert result.bucket_count == 3
    assert result.dashboard_path.exists()
    assert metadata["method"]["bounded_runner_not_daemon"] is True
    assert metadata["method"]["uses_curated_watchlist"] is True
    assert metadata["method"]["baseline_observations"] == 30
    assert metadata["method"]["min_baseline_observations"] == 20
    assert scoring_metadata["method"]["baseline_observations"] == 30
    assert scoring_metadata["method"]["min_baseline_observations"] == 20
    assert metadata["outputs"]["contains_wallet_addresses"] is False


def test_monitor_refresh_cli_writes_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    curated_path = _curated_watchlist_path(tmp_path)

    exit_code = main(
        [
            "--source",
            "mock",
            "--samples",
            "2",
            "--reset",
            "--collected-at-utc",
            COLLECTED_AT,
            "--curated-watchlist-input",
            str(curated_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "dashboard_path" in captured.out
    assert Path("data/results/monitor_v2_polymarket_dashboard.html").exists()


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
        ],
        columns=CURATED_WATCHLIST_COLUMNS,
    ).to_csv(path, index=False)
    return path
