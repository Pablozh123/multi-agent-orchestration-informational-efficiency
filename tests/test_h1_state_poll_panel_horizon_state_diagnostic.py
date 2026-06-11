from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_state_poll_panel_horizon_diagnostic import add_horizon_columns
from operations.analysis.h1_state_poll_panel_horizon_state_diagnostic import (
    build_state_support,
    build_summary,
    generate_h1_state_poll_panel_horizon_state_outputs,
)
from operations.analysis.h1_state_poll_panel_temporal_diagnostic import read_panel_cases


def test_state_horizon_support_counts_states_not_only_rows() -> None:
    cases = add_horizon_columns(_toy_cases())
    near = cases.loc[cases["days_to_election"] <= 90]
    state_support = build_state_support(near)
    summary = build_summary(state_support, near)
    values = _summary_values(summary)

    assert values["state_count"] == 3
    assert values["row_count"] == 6
    assert values["polymarket_lower_loss_count"] == 4
    assert values["poll_derived_lower_loss_count"] == 2
    assert values["polymarket_mean_support_state_count"] == 2
    assert values["polymarket_majority_support_state_count"] == 2
    assert values["broad_many_cases_claim_supported"] == 0.0
    assert set(state_support["support_label"]) == {
        "polymarket_mean_and_majority",
        "poll_derived_or_no_polymarket_support",
    }


def test_generate_state_horizon_outputs(tmp_path: Path) -> None:
    case_path = tmp_path / "cases.csv"
    _toy_cases().to_csv(case_path, index=False)

    result = generate_h1_state_poll_panel_horizon_state_outputs(
        case_input=case_path,
        state_support_output=tmp_path / "state_support.csv",
        summary_output=tmp_path / "summary.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    state_support = pd.read_csv(tmp_path / "state_support.csv")
    summary = pd.read_csv(tmp_path / "summary.csv")
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.state_count == 3
    assert result.polymarket_mean_support_state_count == 2
    assert result.polymarket_majority_support_state_count == 2
    assert result.row_count == 6
    assert len(state_support) == 3
    assert "state_count" in set(summary["summary_id"])
    assert metadata["outputs"]["h1_goal_completion_status"] == "not_proven"
    assert metadata["limitations"]["state_rows_share_one_election_context"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_state_horizon_input_rejects_wallet_columns(tmp_path: Path) -> None:
    path = tmp_path / "cases.csv"
    cases = _toy_cases()
    cases["wallet_address"] = "0xabc"
    cases.to_csv(path, index=False)

    with pytest.raises(ValueError, match="forbidden raw-trade"):
        read_panel_cases(path)


def _toy_cases() -> pd.DataFrame:
    rows = []
    specs = [
        ("case-1", "Arizona", "2024-08-20", 1.0, 0.90, 0.60),
        ("case-2", "Arizona", "2024-09-10", 1.0, 0.88, 0.58),
        ("case-3", "Michigan", "2024-08-20", 1.0, 0.91, 0.55),
        ("case-4", "Michigan", "2024-09-10", 1.0, 0.89, 0.59),
        ("case-5", "Texas", "2024-08-20", 1.0, 0.60, 0.85),
        ("case-6", "Texas", "2024-09-10", 1.0, 0.58, 0.86),
        ("case-7", "Arizona", "2024-05-01", 1.0, 0.20, 0.80),
    ]
    for case_id, state, date, outcome, pm_probability, poll_probability in specs:
        pm_brier = (pm_probability - outcome) ** 2
        poll_brier = (poll_probability - outcome) ** 2
        rows.append(
            {
                "case_id": case_id,
                "state": state,
                "forecast_date": date,
                "outcome_value": outcome,
                "polymarket_probability": pm_probability,
                "poll_derived_probability": poll_probability,
                "polymarket_brier": pm_brier,
                "poll_derived_brier": poll_brier,
                "loss_advantage": poll_brier - pm_brier,
                "lower_loss_source": (
                    "polymarket"
                    if pm_brier < poll_brier
                    else "poll_derived_forecast"
                ),
            }
        )
    return pd.DataFrame(rows)


def _summary_values(summary: pd.DataFrame) -> dict[str, float]:
    return {
        str(row["summary_id"]): float(row["value"])
        for _, row in summary.iterrows()
    }
