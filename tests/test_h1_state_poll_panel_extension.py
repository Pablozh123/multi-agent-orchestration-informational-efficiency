from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_state_poll_panel_extension import (
    build_panel_cases,
    build_panel_summary,
    build_poll_panel,
    generate_h1_state_poll_panel_outputs,
    mock_history_by_state,
    mock_poll_average_rows,
    validate_panel_cases,
)


def test_build_state_poll_panel_marks_repeated_panel_rows() -> None:
    market_cases = _market_cases()
    poll_panel = build_poll_panel(
        poll_rows=mock_poll_average_rows(),
        market_cases=market_cases,
    )
    cases = validate_panel_cases(
        build_panel_cases(
            poll_panel=poll_panel,
            market_cases=market_cases,
            history_by_state=mock_history_by_state(poll_panel),
        )
    )
    summary = build_panel_summary(cases=cases, poll_panel=poll_panel)
    values = _summary_values(summary)

    assert len(poll_panel) == 6
    assert len(cases) == 6
    assert values["matched_case_count"] == 6
    assert values["independent_state_outcome_count"] == 3
    assert values["poll_derived_lower_loss_count"] == 6
    assert values["aggregate_mean_supports_polymarket"] == 0.0
    assert values["broad_many_cases_claim_supported"] == 0.0
    assert set(cases["row_unit"]) == {"state_date_forecast_pair"}


def test_generate_h1_state_poll_panel_outputs(tmp_path: Path) -> None:
    market_path = tmp_path / "markets.csv"
    _market_cases().reset_index(drop=True).to_csv(market_path, index=False)

    result = generate_h1_state_poll_panel_outputs(
        source="mock",
        market_case_input=market_path,
        cases_output=tmp_path / "cases.csv",
        summary_output=tmp_path / "summary.csv",
        state_summary_output=tmp_path / "state_summary.csv",
        coverage_output=tmp_path / "coverage.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    cases = pd.read_csv(tmp_path / "cases.csv")
    state_summary = pd.read_csv(tmp_path / "state_summary.csv")
    coverage = pd.read_csv(tmp_path / "coverage.csv")
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.case_count == 6
    assert result.state_count == 3
    assert result.date_count == 2
    assert metadata["method"]["raw_poll_average_used_directly_as_probability"] is False
    assert metadata["outputs"]["h1_goal_completion_status"] == "not_proven"
    assert metadata["limitations"]["panel_rows_are_not_independent_elections"] is True
    assert len(cases) == 6
    assert len(state_summary) == 3
    assert len(coverage) == 3
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_validate_panel_cases_rejects_wallet_columns() -> None:
    market_cases = _market_cases()
    poll_panel = build_poll_panel(
        poll_rows=mock_poll_average_rows(),
        market_cases=market_cases,
    )
    cases = build_panel_cases(
        poll_panel=poll_panel,
        market_cases=market_cases,
        history_by_state=mock_history_by_state(poll_panel),
    )
    cases["wallet_address"] = "0xabc"

    with pytest.raises(ValueError, match="forbidden raw-trade"):
        validate_panel_cases(cases)


def _market_cases() -> pd.DataFrame:
    frame = pd.DataFrame(
        [
            {
                "state": "Arizona",
                "target_token_id": "token-arizona",
                "outcome_value": 1.0,
                "polymarket_market_slug": "arizona-market",
                "polymarket_market_id": "1",
                "polymarket_condition_id": "condition-arizona",
            },
            {
                "state": "Michigan",
                "target_token_id": "token-michigan",
                "outcome_value": 1.0,
                "polymarket_market_slug": "michigan-market",
                "polymarket_market_id": "2",
                "polymarket_condition_id": "condition-michigan",
            },
            {
                "state": "Texas",
                "target_token_id": "token-texas",
                "outcome_value": 1.0,
                "polymarket_market_slug": "texas-market",
                "polymarket_market_id": "3",
                "polymarket_condition_id": "condition-texas",
            },
        ]
    )
    return frame.set_index("state", drop=False)


def _summary_values(summary: pd.DataFrame) -> dict[str, float]:
    return {
        str(row["summary_id"]): float(row["value"])
        for _, row in summary.iterrows()
    }
