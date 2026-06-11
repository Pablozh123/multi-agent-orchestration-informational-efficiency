from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_direct_poll_outlier_robustness import (
    build_scenarios,
    build_summary,
    generate_h1_direct_poll_outlier_robustness_outputs,
    read_state_clusters,
    validate_scenarios,
    validate_summary,
)


def test_outlier_summary_identifies_single_state_and_top_k_boundary(
    tmp_path: Path,
) -> None:
    states = read_state_clusters(_write_states(tmp_path / "states.csv"))
    scenarios = validate_scenarios(build_scenarios(states))
    summary = validate_summary(build_summary(states=states, scenarios=scenarios))

    assert int(_summary_value(summary, "state_count")) == 4
    assert float(_summary_value(summary, "full_mean_loss_advantage")) == pytest.approx(
        0.03
    )
    assert float(
        _summary_value(summary, "min_leave_one_out_mean_loss_advantage")
    ) == pytest.approx(0.0066666667)
    assert int(_summary_value(summary, "leave_one_out_all_positive")) == 1
    assert _summary_value(summary, "most_influential_removed_state") == "Arizona"
    assert int(_summary_value(summary, "max_top_positive_exclusion_k_with_positive_mean")) == 1
    assert int(_summary_value(summary, "first_nonpositive_top_positive_exclusion_k")) == 2
    assert float(
        _summary_value(summary, "first_nonpositive_top_positive_exclusion_mean")
    ) == pytest.approx(-0.015)
    assert int(_summary_value(summary, "outlier_robustness_supports_polymarket_mean")) == 1
    assert _summary_value(summary, "h1_goal_completion_status") == "not_proven"


def test_generate_outlier_outputs_writes_nonblank_figure(tmp_path: Path) -> None:
    states_path = _write_states(tmp_path / "states.csv")

    result = generate_h1_direct_poll_outlier_robustness_outputs(
        state_input=states_path,
        scenario_output=tmp_path / "scenarios.csv",
        summary_output=tmp_path / "summary.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.state_count == 4
    assert result.full_mean_loss_advantage == pytest.approx(0.03)
    assert result.min_leave_one_out_mean_loss_advantage == pytest.approx(0.0066666667)
    assert result.max_top_positive_exclusion_k_with_positive_mean == 1
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["broad_many_cases_claim_proven"] is False
    assert metadata["limitations"]["top_positive_exclusion_shows_concentration"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_outlier_input_rejects_forbidden_columns(tmp_path: Path) -> None:
    path = _write_states(tmp_path / "bad.csv")
    frame = pd.read_csv(path)
    frame["maker_address"] = "0xabc"
    frame.to_csv(path, index=False)

    with pytest.raises(ValueError, match="forbidden columns"):
        read_state_clusters(path)


def _write_states(path: Path) -> Path:
    frame = pd.DataFrame(
        [
            {"state": "Arizona", "mean_loss_advantage": 0.10},
            {"state": "Pennsylvania", "mean_loss_advantage": 0.05},
            {"state": "Ohio", "mean_loss_advantage": -0.02},
            {"state": "Florida", "mean_loss_advantage": -0.01},
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return path


def _summary_value(summary: pd.DataFrame, summary_id: str):
    row = summary.loc[summary["summary_id"] == summary_id, "value"]
    assert len(row) == 1
    return row.iloc[0]
