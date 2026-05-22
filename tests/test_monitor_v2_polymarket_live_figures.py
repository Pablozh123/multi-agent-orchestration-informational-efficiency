from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from operations.analysis.monitor_v2_polymarket_live_figures import (
    generate_polymarket_live_snapshot_figure,
    main,
)
from operations.collectors.polymarket_readonly import collect_readonly_polymarket_inputs


COLLECTED_AT = "2026-05-22T12:10:00Z"


def test_generate_polymarket_live_snapshot_figure(tmp_path: Path) -> None:
    paths = _collector_paths(tmp_path / "collector")
    figure_path = tmp_path / "figure.png"
    figure_metadata_path = tmp_path / "figure_metadata.json"
    collect_readonly_polymarket_inputs(
        source="mock",
        collected_at_utc=COLLECTED_AT,
        **paths,
    )

    result = generate_polymarket_live_snapshot_figure(
        watchlist_path=paths["watchlist_path"],
        market_snapshots_path=paths["market_snapshots_path"],
        wallet_tier_snapshots_path=paths["wallet_tier_snapshots_path"],
        collector_metadata_path=paths["metadata_path"],
        figure_path=figure_path,
        metadata_path=figure_metadata_path,
    )

    metadata = json.loads(figure_metadata_path.read_text(encoding="utf-8"))
    assert result.market_count == 1
    assert result.token_snapshot_count == 2
    assert result.wallet_snapshot_count == 1
    assert figure_path.exists()
    assert figure_path.stat().st_size > 0
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["contains_order_instructions"] is False


def test_live_snapshot_figure_rejects_empty_inputs(tmp_path: Path) -> None:
    empty_path = tmp_path / "empty.csv"
    pd.DataFrame().to_csv(empty_path, index=False)

    exit_code = main(
        [
            "--watchlist",
            str(empty_path),
            "--market-snapshots",
            str(empty_path),
            "--wallet-tier-snapshots",
            str(empty_path),
            "--figure-output",
            str(tmp_path / "figure.png"),
            "--metadata-output",
            str(tmp_path / "metadata.json"),
        ]
    )

    assert exit_code == 2


def _collector_paths(root: Path) -> dict[str, Path]:
    return {
        "watchlist_path": root / "watchlist.csv",
        "market_snapshots_path": root / "market.csv",
        "wallet_tier_snapshots_path": root / "wallet.csv",
        "event_candidates_path": root / "events.csv",
        "validation_report_path": root / "report.json",
        "metadata_path": root / "collector_metadata.json",
    }
