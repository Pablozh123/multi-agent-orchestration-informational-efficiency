from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.thesis_figures import generate_figures


def _write_inputs(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "event_id": "evt_2024_a",
                "window_label": "primary_0d_to_1d",
                "final_cumulative_abnormal_change": 0.03,
            },
            {
                "event_id": "evt_2024_a",
                "window_label": "secondary_minus_1d_to_3d",
                "final_cumulative_abnormal_change": -0.01,
            },
        ]
    ).to_csv(path / "h2_event_window_summary.csv", index=False)
    (path / "h3_wallet_distribution_inventory.json").write_text(
        json.dumps(
            {
                "tier_counts": {
                    "tier_1_top_1pct": 2,
                    "tier_2_top_5pct": 3,
                    "tier_3_top_10pct": 4,
                    "tier_4_observed_baseline": 40,
                }
            }
        ),
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "window_label": "lead_minus_14d_to_0d",
                "tier": "tier_1_top_1pct",
                "relative_day": -1,
                "total_amount_usd": 1000.0,
            },
            {
                "window_label": "lead_minus_14d_to_0d",
                "tier": "tier_1_top_1pct",
                "relative_day": 0,
                "total_amount_usd": 1500.0,
            },
            {
                "window_label": "lead_minus_14d_to_0d",
                "tier": "tier_4_observed_baseline",
                "relative_day": -1,
                "total_amount_usd": 100.0,
            },
        ]
    ).to_csv(path / "h3_lead_time_histograms.csv", index=False)
    pd.DataFrame(
        [
            {
                "tier": "tier_1_top_1pct",
                "lag_days": 1,
                "p_value": 0.03,
                "status": "ok",
            },
            {
                "tier": "tier_4_observed_baseline",
                "lag_days": 1,
                "p_value": 0.6,
                "status": "ok",
            },
        ]
    ).to_csv(path / "h3_granger_results.csv", index=False)
    pd.DataFrame(
        [
            {
                "event_date": "2024-01-01",
                "event_id": "evt_2024_a",
                "anomaly_type": "market_move_anomaly",
                "anomaly_day_count": 1,
            },
            {
                "event_date": "2024-01-01",
                "event_id": "evt_2024_a",
                "anomaly_type": "wallet_tier_amount_anomaly",
                "anomaly_day_count": 2,
            },
            {
                "event_date": "2024-01-02",
                "event_id": "evt_2024_b",
                "anomaly_type": "active_wallet_anomaly",
                "anomaly_day_count": 3,
            },
        ]
    ).to_csv(path / "h3_event_wallet_anomaly_summary.csv", index=False)
    pd.DataFrame(
        [
            {"severity": "none"},
            {"severity": "info"},
            {"severity": "watch"},
            {"severity": "high"},
        ]
    ).to_csv(path / "monitor_v2_recorded_alert_rows.csv", index=False)
    pd.DataFrame(
        [
            {"suggested_context_label": "no_event_alert"},
            {"suggested_context_label": "event_watch_candidate"},
            {"suggested_context_label": "critical_proximity_candidate"},
        ]
    ).to_csv(path / "monitor_v2_recorded_context_rows.csv", index=False)


def test_generate_figures_writes_pngs_and_metadata(tmp_path: Path) -> None:
    _write_inputs(tmp_path)
    output_dir = tmp_path / "figures"

    figures = generate_figures(input_dir=tmp_path, output_dir=output_dir)

    assert set(figures) == {
        "h2_event_window_car",
        "h3_wallet_tier_counts",
        "h3_lead_time_amount",
        "h3_granger_pvalues",
        "h3_event_wallet_anomalies",
        "monitor_v2_recorded_scoring",
        "metadata",
    }
    for path_text in figures.values():
        path = Path(path_text)
        assert path.exists()
        assert path.stat().st_size > 0

    metadata = json.loads(Path(figures["metadata"]).read_text(encoding="utf-8"))
    assert "no new statistical metrics" in metadata["calculation_note"]


def test_generate_figures_fails_for_missing_source(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Required source artifact is missing"):
        generate_figures(input_dir=tmp_path, output_dir=tmp_path / "figures")
