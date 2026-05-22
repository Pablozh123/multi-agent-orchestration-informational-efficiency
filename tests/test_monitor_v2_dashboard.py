from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.monitor_v2_dashboard import (
    generate_monitor_v2_dashboard,
    main,
)


def test_generate_monitor_v2_dashboard_writes_html_and_metadata(tmp_path: Path) -> None:
    paths = _write_inputs(tmp_path)

    result = generate_monitor_v2_dashboard(**paths)

    html = paths["dashboard_path"].read_text(encoding="utf-8")
    metadata = json.loads(paths["metadata_path"].read_text(encoding="utf-8"))
    assert result.market_count == 1
    assert result.bucket_count == 3
    assert result.alert_count == 0
    assert "Polymarket Politics/Geo Monitor" in html
    assert "diagnostic_scores_available" in html
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["contains_order_instructions"] is False


def test_generate_monitor_v2_dashboard_rejects_wallet_address_columns(
    tmp_path: Path,
) -> None:
    paths = _write_inputs(tmp_path)
    market = pd.read_csv(paths["market_snapshots_path"])
    market["wallet_address"] = "0x" + "a" * 40
    market.to_csv(paths["market_snapshots_path"], index=False)

    with pytest.raises(ValueError, match="wallet-address columns"):
        generate_monitor_v2_dashboard(**paths)


def test_dashboard_cli_writes_outputs(tmp_path: Path, capsys) -> None:
    paths = _write_inputs(tmp_path)

    exit_code = main(
        [
            "--watchlist",
            str(paths["watchlist_path"]),
            "--market-snapshots",
            str(paths["market_snapshots_path"]),
            "--wallet-tier-snapshots",
            str(paths["wallet_tier_snapshots_path"]),
            "--alert-summary",
            str(paths["alert_summary_path"]),
            "--scoring-metadata",
            str(paths["scoring_metadata_path"]),
            "--rolling-metadata",
            str(paths["rolling_metadata_path"]),
            "--figure",
            str(paths["figure_path"]),
            "--dashboard-output",
            str(paths["dashboard_path"]),
            "--metadata-output",
            str(paths["metadata_path"]),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "baseline_readiness" in captured.out
    assert paths["dashboard_path"].exists()


def _write_inputs(root: Path) -> dict[str, Path]:
    paths = {
        "watchlist_path": root / "watchlist.csv",
        "market_snapshots_path": root / "market.csv",
        "wallet_tier_snapshots_path": root / "wallets.csv",
        "alert_summary_path": root / "summary.csv",
        "scoring_metadata_path": root / "scoring_metadata.json",
        "rolling_metadata_path": root / "rolling_metadata.json",
        "figure_path": root / "figure.png",
        "dashboard_path": root / "dashboard.html",
        "metadata_path": root / "dashboard_metadata.json",
    }
    pd.DataFrame(
        [
            {
                "market_id": "0x" + "a" * 64,
                "question": "Will a politics market resolve yes?",
                "category": "politics",
                "subcategory": "example",
                "status": "active",
            }
        ]
    ).to_csv(paths["watchlist_path"], index=False)
    pd.DataFrame(
        [
            {
                "bucket_end_utc": "2026-05-22T15:00:00Z",
                "market_id": "0x" + "a" * 64,
                "midpoint": 0.42,
            },
            {
                "bucket_end_utc": "2026-05-22T15:00:00Z",
                "market_id": "0x" + "a" * 64,
                "midpoint": 0.58,
            },
        ]
    ).to_csv(paths["market_snapshots_path"], index=False)
    pd.DataFrame(
        [
            {
                "bucket_end_utc": "2026-05-22T15:00:00Z",
                "market_id": "0x" + "a" * 64,
                "active_wallets": 2,
                "trade_count": 3,
                "total_observed_amount_usd": 12.5,
            }
        ]
    ).to_csv(paths["wallet_tier_snapshots_path"], index=False)
    pd.DataFrame(
        [
            {
                "market_id": "0x" + "a" * 64,
                "tier": "all_tiers",
                "anomaly_family": "wallet_tier_activity",
                "metric_name": "log1p_total_observed_amount_usd",
                "row_count": 3,
                "alert_count": 0,
                "max_severity": "none",
                "max_robust_z": 0.0,
                "max_percentile_rank": 0.5,
            }
        ]
    ).to_csv(paths["alert_summary_path"], index=False)
    paths["scoring_metadata_path"].write_text(
        json.dumps(
            {
                "method": {"baseline_readiness": "diagnostic_scores_available"},
                "outputs": {
                    "alert_count": 0,
                    "severity_counts": {"none": 1},
                    "status_counts": {"ok": 1},
                },
            }
        ),
        encoding="utf-8",
    )
    paths["rolling_metadata_path"].write_text(
        json.dumps({"outputs": {"figure_result": {"bucket_count": 3}}}),
        encoding="utf-8",
    )
    paths["figure_path"].write_bytes(b"not-a-real-png-but-present")
    return paths
