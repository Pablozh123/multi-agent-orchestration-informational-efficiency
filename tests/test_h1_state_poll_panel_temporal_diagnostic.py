from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_state_poll_panel_temporal_diagnostic import (
    build_claim_audit,
    build_temporal_summary,
    generate_h1_state_poll_panel_temporal_outputs,
    read_panel_cases,
)


def test_temporal_claim_audit_separates_supporting_months() -> None:
    cases = _toy_cases()
    temporal = build_temporal_summary(cases)
    claim_audit = build_claim_audit(cases, temporal)

    full = claim_audit.set_index("audit_scope").loc["full_panel"]
    supporting = claim_audit.set_index("audit_scope").loc["polymarket_supporting_months"]

    assert list(temporal["forecast_month"]) == ["2024-03", "2024-04"]
    assert int(temporal["aggregate_mean_supports_polymarket"].sum()) == 1
    assert int(temporal["majority_rows_support_polymarket"].sum()) == 1
    assert int(full["row_count"]) == 4
    assert int(full["polymarket_lower_loss_count"]) == 2
    assert int(full["poll_derived_lower_loss_count"]) == 2
    assert bool(full["aggregate_mean_supports_polymarket"]) is False
    assert supporting["included_months"] == "2024-04"
    assert int(supporting["row_count"]) == 2
    assert int(supporting["polymarket_lower_loss_count"]) == 2
    assert int(supporting["poll_derived_lower_loss_count"]) == 0
    assert bool(supporting["aggregate_mean_supports_polymarket"]) is True


def test_generate_temporal_outputs(tmp_path: Path) -> None:
    case_path = tmp_path / "cases.csv"
    _toy_cases().to_csv(case_path, index=False)

    result = generate_h1_state_poll_panel_temporal_outputs(
        case_input=case_path,
        temporal_summary_output=tmp_path / "temporal.csv",
        state_month_output=tmp_path / "state_month.csv",
        claim_audit_output=tmp_path / "claim_audit.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    temporal = pd.read_csv(tmp_path / "temporal.csv")
    state_month = pd.read_csv(tmp_path / "state_month.csv")
    claim_audit = pd.read_csv(tmp_path / "claim_audit.csv")
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.month_count == 2
    assert result.row_count == 4
    assert result.polymarket_supporting_month_count == 1
    assert result.polymarket_supporting_row_count == 2
    assert len(temporal) == 2
    assert len(state_month) == 4
    assert len(claim_audit) == 3
    assert metadata["outputs"]["h1_goal_completion_status"] == "not_proven"
    assert metadata["limitations"]["supporting_months_are_conditioned_diagnostic_subset"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_read_panel_cases_rejects_wallet_columns(tmp_path: Path) -> None:
    path = tmp_path / "cases.csv"
    cases = _toy_cases()
    cases["wallet_address"] = "0xabc"
    cases.to_csv(path, index=False)

    with pytest.raises(ValueError, match="forbidden raw-trade"):
        read_panel_cases(path)


def _toy_cases() -> pd.DataFrame:
    rows = []
    specs = [
        ("case-1", "Arizona", "2024-03-01", 1.0, 0.20, 0.80),
        ("case-2", "Michigan", "2024-03-01", 1.0, 0.20, 0.80),
        ("case-3", "Arizona", "2024-04-01", 1.0, 0.90, 0.60),
        ("case-4", "Michigan", "2024-04-01", 1.0, 0.90, 0.60),
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
