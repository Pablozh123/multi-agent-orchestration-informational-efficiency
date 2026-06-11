from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_forecast_quality import (
    generate_h1_forecast_quality_outputs,
    read_h1_brier_rows,
)


def _write_brier_rows(path: Path) -> None:
    pd.DataFrame(
        [
            {
                "date": "2024-01-01",
                "bs_polymarket": 0.09,
                "bs_fivethirtyeight": 0.36,
                "bs_always_50": 0.25,
                "bs_prior_day": 0.25,
                "forecast_polymarket": 0.70,
                "forecast_fivethirtyeight": 0.40,
                "forecast_always_50": 0.50,
                "forecast_prior_day": 0.50,
            },
            {
                "date": "2024-01-02",
                "bs_polymarket": 0.04,
                "bs_fivethirtyeight": 0.3025,
                "bs_always_50": 0.25,
                "bs_prior_day": 0.09,
                "forecast_polymarket": 0.80,
                "forecast_fivethirtyeight": 0.45,
                "forecast_always_50": 0.50,
                "forecast_prior_day": 0.70,
            },
            {
                "date": "2024-01-03",
                "bs_polymarket": 0.16,
                "bs_fivethirtyeight": 0.4225,
                "bs_always_50": 0.25,
                "bs_prior_day": 0.04,
                "forecast_polymarket": 0.60,
                "forecast_fivethirtyeight": 0.35,
                "forecast_always_50": 0.50,
                "forecast_prior_day": 0.80,
            },
        ]
    ).to_csv(path, index=False)


def test_generate_h1_forecast_quality_outputs(tmp_path: Path) -> None:
    brier_path = tmp_path / "h1_brier_scores.csv"
    dm_path = tmp_path / "h1_diebold_mariano.json"
    source_path = tmp_path / "sources.csv"
    pairwise_path = tmp_path / "pairwise.csv"
    figure_path = tmp_path / "figure.png"
    metadata_path = tmp_path / "metadata.json"
    _write_brier_rows(brier_path)
    dm_path.write_text(
        json.dumps(
            [
                {
                    "source_1": "Polymarket",
                    "source_2": "FiveThirtyEight",
                    "p_value": 0.01,
                }
            ]
        ),
        encoding="utf-8",
    )

    result = generate_h1_forecast_quality_outputs(
        brier_input=brier_path,
        dm_input=dm_path,
        source_summary_output=source_path,
        pairwise_output=pairwise_path,
        figure_output=figure_path,
        metadata_output=metadata_path,
    )

    assert result.source_row_count == 4
    assert result.pairwise_row_count == 3
    assert result.fivethirtyeight_polymarket_better_count == 3
    assert result.fivethirtyeight_comparison_count == 3
    assert result.fivethirtyeight_polymarket_better_share == pytest.approx(1.0)
    assert result.fivethirtyeight_mean_loss_advantage == pytest.approx(
        ((0.36 + 0.3025 + 0.4225) / 3) - ((0.09 + 0.04 + 0.16) / 3)
    )

    pairwise = pd.read_csv(pairwise_path)
    fte = pairwise[pairwise["comparator"] == "fivethirtyeight"].iloc[0]
    assert int(fte["polymarket_lower_loss_count"]) == 3
    assert int(fte["comparator_lower_loss_count"]) == 0
    assert float(fte["dm_p_value"]) == pytest.approx(0.01)

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["method"]["raw_poll_average_probability_transform_used"] is False
    assert metadata["limitations"]["single_resolved_event_limits_true_calibration_curve"]
    assert metadata["limitations"]["fivethirtyeight_is_poll_based_probability_not_raw_poll_share"]

    image = mpimg.imread(figure_path)
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_read_h1_brier_rows_rejects_invalid_probabilities(tmp_path: Path) -> None:
    brier_path = tmp_path / "h1_brier_scores.csv"
    _write_brier_rows(brier_path)
    frame = pd.read_csv(brier_path)
    frame.loc[0, "forecast_polymarket"] = 1.2
    frame.to_csv(brier_path, index=False)

    with pytest.raises(ValueError, match="forecast_polymarket"):
        read_h1_brier_rows(brier_path)
