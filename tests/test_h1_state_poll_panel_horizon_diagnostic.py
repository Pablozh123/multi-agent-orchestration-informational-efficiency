from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_state_poll_panel_horizon_diagnostic import (
    add_horizon_columns,
    build_claim_audit,
    build_horizon_summary,
    generate_h1_state_poll_panel_horizon_outputs,
)
from operations.analysis.h1_state_poll_panel_temporal_diagnostic import read_panel_cases


def test_horizon_claim_audit_marks_within_90_day_support() -> None:
    cases = add_horizon_columns(_toy_cases())
    horizon = build_horizon_summary(cases)
    claim_audit = build_claim_audit(cases).set_index("audit_scope")

    assert set(horizon["horizon_bin"]) == {"181_plus_days", "61_90_days", "0_60_days"}
    full = claim_audit.loc["full_panel"]
    near = claim_audit.loc["within_90_days_before_election"]
    far = claim_audit.loc["more_than_90_days_before_election"]

    assert int(full["row_count"]) == 6
    assert int(full["polymarket_lower_loss_count"]) == 4
    assert int(full["poll_derived_lower_loss_count"]) == 2
    assert int(near["row_count"]) == 4
    assert int(near["polymarket_lower_loss_count"]) == 4
    assert int(near["poll_derived_lower_loss_count"]) == 0
    assert bool(near["aggregate_mean_supports_polymarket"]) is True
    assert bool(near["majority_rows_support_polymarket"]) is True
    assert int(far["row_count"]) == 2
    assert int(far["polymarket_lower_loss_count"]) == 0
    assert int(far["poll_derived_lower_loss_count"]) == 2


def test_generate_horizon_outputs(tmp_path: Path) -> None:
    case_path = tmp_path / "cases.csv"
    _toy_cases().to_csv(case_path, index=False)

    result = generate_h1_state_poll_panel_horizon_outputs(
        case_input=case_path,
        horizon_summary_output=tmp_path / "horizon.csv",
        state_horizon_output=tmp_path / "state_horizon.csv",
        claim_audit_output=tmp_path / "claim_audit.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    horizon = pd.read_csv(tmp_path / "horizon.csv")
    state_horizon = pd.read_csv(tmp_path / "state_horizon.csv")
    claim_audit = pd.read_csv(tmp_path / "claim_audit.csv")
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.horizon_bin_count == 3
    assert result.row_count == 6
    assert result.within_90_row_count == 4
    assert result.within_90_pm_lower_loss_count == 4
    assert len(horizon) == 3
    assert len(state_horizon) == 6
    assert len(claim_audit) == 3
    assert metadata["outputs"]["h1_goal_completion_status"] == "not_proven"
    assert metadata["limitations"]["within_90_days_is_horizon_diagnostic_subset"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_horizon_input_rejects_wallet_columns(tmp_path: Path) -> None:
    path = tmp_path / "cases.csv"
    cases = _toy_cases()
    cases["wallet_address"] = "0xabc"
    cases.to_csv(path, index=False)

    with pytest.raises(ValueError, match="forbidden raw-trade"):
        read_panel_cases(path)


def _toy_cases() -> pd.DataFrame:
    rows = []
    specs = [
        ("case-1", "Arizona", "2024-05-01", 1.0, 0.20, 0.80),
        ("case-2", "Michigan", "2024-05-01", 1.0, 0.20, 0.80),
        ("case-3", "Arizona", "2024-08-20", 1.0, 0.90, 0.60),
        ("case-4", "Michigan", "2024-08-20", 1.0, 0.90, 0.60),
        ("case-5", "Arizona", "2024-09-10", 1.0, 0.88, 0.58),
        ("case-6", "Michigan", "2024-09-10", 1.0, 0.88, 0.58),
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
