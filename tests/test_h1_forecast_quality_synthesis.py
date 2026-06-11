from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_forecast_quality_synthesis import (
    build_synthesis_table,
    generate_h1_forecast_quality_synthesis_outputs,
    validate_synthesis_table,
)


def test_build_synthesis_table_marks_aggregate_support_but_not_broad_proof() -> None:
    synthesis = build_synthesis_table(
        pairwise=_pairwise_frame(),
        final_snapshot=_summary_frame(
            {
                "case_count": 8,
                "polymarket_lower_loss_count": 5,
                "traditional_lower_loss_count": 3,
                "mean_polymarket_brier": 0.07837715625,
                "mean_traditional_brier": 0.09327890625,
            }
        ),
        state_poll=_summary_frame(
            {
                "case_count": 13,
                "polymarket_lower_loss_count": 8,
                "poll_derived_lower_loss_count": 5,
                "mean_polymarket_brier": 0.13355132692307695,
                "mean_poll_derived_brier": 0.17635906875132107,
            }
        ),
        state_poll_panel=_summary_frame(
            {
                "matched_case_count": 1720,
                "polymarket_lower_loss_count": 360,
                "poll_derived_lower_loss_count": 1360,
                "tie_count": 0,
                "mean_polymarket_brier": 0.15947981976744185,
                "mean_poll_derived_brier": 0.10260026775705648,
            }
        ),
        popular_vote=_summary_frame(
            {
                "case_count": 51,
                "polymarket_lower_loss_count": 21,
                "poll_derived_lower_loss_count": 30,
                "tie_count": 0,
                "mean_polymarket_brier": 0.5178593137254902,
                "mean_poll_derived_brier": 0.48244035524337675,
            }
        ),
        rieke=_summary_frame(
            {
                "case_count": 50,
                "polymarket_lower_loss_count": 12,
                "rieke_lower_loss_count": 38,
                "tie_count": 0,
                "mean_polymarket_brier": 0.026207745,
                "mean_rieke_brier": 0.0295807872,
            }
        ),
        two_seventy_poll_average=_summary_frame(
            {
                "case_count": 43,
                "polymarket_lower_loss_count": 14,
                "poll_derived_lower_loss_count": 29,
                "tie_count": 0,
                "mean_polymarket_brier": 0.03044131976744186,
                "mean_poll_derived_brier": 0.0415955678144349,
            }
        ),
        two_seventy=_summary_frame(
            {
                "case_count": 50,
                "exact_probability_case_count": 22,
                "polymarket_lower_loss_count": 9,
                "two_seventy_lower_loss_count": 40,
                "tie_count": 1,
                "mean_polymarket_brier": 0.026207745,
                "mean_two_seventy_brier": 0.03059892,
                "exact_probability_polymarket_lower_loss_count": 9,
                "exact_probability_two_seventy_lower_loss_count": 12,
                "exact_probability_tie_count": 1,
                "exact_probability_mean_polymarket_brier": 0.059292840909090906,
                "exact_probability_mean_two_seventy_brier": 0.06954172727272727,
            }
        ),
    )

    validated = validate_synthesis_table(synthesis)

    assert len(validated) == 9
    assert int(validated["aggregate_mean_supports_polymarket"].sum()) == 7
    assert int(validated["majority_cases_supports_polymarket"].sum()) == 3
    assert int(validated["broad_many_cases_claim_supported"].sum()) == 0
    panel = validated.loc[
        validated["evidence_id"] == "state_poll_panel_538_transform"
    ].iloc[0]
    assert panel["polymarket_lower_loss_count"] == 360
    assert panel["comparator_lower_loss_count"] == 1360
    assert bool(panel["aggregate_mean_supports_polymarket"]) is False
    popular_vote = validated.loc[
        validated["evidence_id"] == "popular_vote_538_transform"
    ].iloc[0]
    assert popular_vote["polymarket_lower_loss_count"] == 21
    assert popular_vote["comparator_lower_loss_count"] == 30
    assert bool(popular_vote["aggregate_mean_supports_polymarket"]) is False
    row = validated.loc[validated["evidence_id"] == "two_seventy_50_state"].iloc[0]
    assert row["polymarket_lower_loss_count"] == 9
    assert row["comparator_lower_loss_count"] == 40
    assert row["polymarket_lower_loss_share"] == pytest.approx(0.18)
    assert row["mean_loss_advantage"] == pytest.approx(0.004391175)
    poll_average = validated.loc[
        validated["evidence_id"] == "two_seventy_poll_average_transform"
    ].iloc[0]
    assert poll_average["polymarket_lower_loss_count"] == 14
    assert poll_average["comparator_lower_loss_count"] == 29
    assert poll_average["mean_loss_advantage"] == pytest.approx(0.011154248047)


def test_generate_h1_forecast_quality_synthesis_outputs(tmp_path: Path) -> None:
    pairwise_path = tmp_path / "pairwise.csv"
    final_path = tmp_path / "final.csv"
    state_path = tmp_path / "state.csv"
    state_panel_path = tmp_path / "state_panel.csv"
    popular_vote_path = tmp_path / "popular_vote.csv"
    rieke_path = tmp_path / "rieke.csv"
    two_seventy_poll_average_path = tmp_path / "two_seventy_poll_average.csv"
    two_seventy_path = tmp_path / "two_seventy.csv"
    _pairwise_frame().to_csv(pairwise_path, index=False)
    _summary_frame(
        {
            "case_count": 8,
            "polymarket_lower_loss_count": 5,
            "traditional_lower_loss_count": 3,
            "mean_polymarket_brier": 0.07837715625,
            "mean_traditional_brier": 0.09327890625,
        }
    ).to_csv(final_path, index=False)
    _summary_frame(
        {
            "case_count": 13,
            "polymarket_lower_loss_count": 8,
            "poll_derived_lower_loss_count": 5,
            "mean_polymarket_brier": 0.13355132692307695,
            "mean_poll_derived_brier": 0.17635906875132107,
        }
    ).to_csv(state_path, index=False)
    _summary_frame(
        {
            "matched_case_count": 1720,
            "polymarket_lower_loss_count": 360,
            "poll_derived_lower_loss_count": 1360,
            "tie_count": 0,
            "mean_polymarket_brier": 0.15947981976744185,
            "mean_poll_derived_brier": 0.10260026775705648,
        }
    ).to_csv(state_panel_path, index=False)
    _summary_frame(
        {
            "case_count": 51,
            "polymarket_lower_loss_count": 21,
            "poll_derived_lower_loss_count": 30,
            "tie_count": 0,
            "mean_polymarket_brier": 0.5178593137254902,
            "mean_poll_derived_brier": 0.48244035524337675,
        }
    ).to_csv(popular_vote_path, index=False)
    _summary_frame(
        {
            "case_count": 50,
            "polymarket_lower_loss_count": 12,
            "rieke_lower_loss_count": 38,
            "tie_count": 0,
            "mean_polymarket_brier": 0.026207745,
            "mean_rieke_brier": 0.0295807872,
        }
    ).to_csv(rieke_path, index=False)
    _summary_frame(
        {
            "case_count": 43,
            "polymarket_lower_loss_count": 14,
            "poll_derived_lower_loss_count": 29,
            "tie_count": 0,
            "mean_polymarket_brier": 0.03044131976744186,
            "mean_poll_derived_brier": 0.0415955678144349,
        }
    ).to_csv(two_seventy_poll_average_path, index=False)
    _summary_frame(
        {
            "case_count": 50,
            "exact_probability_case_count": 22,
            "polymarket_lower_loss_count": 9,
            "two_seventy_lower_loss_count": 40,
            "tie_count": 1,
            "mean_polymarket_brier": 0.026207745,
            "mean_two_seventy_brier": 0.03059892,
            "exact_probability_polymarket_lower_loss_count": 9,
            "exact_probability_two_seventy_lower_loss_count": 12,
            "exact_probability_tie_count": 1,
            "exact_probability_mean_polymarket_brier": 0.059292840909090906,
            "exact_probability_mean_two_seventy_brier": 0.06954172727272727,
        }
    ).to_csv(two_seventy_path, index=False)

    result = generate_h1_forecast_quality_synthesis_outputs(
        pairwise_input=pairwise_path,
        final_snapshot_input=final_path,
        state_poll_input=state_path,
        state_poll_panel_input=state_panel_path,
        popular_vote_input=popular_vote_path,
        rieke_input=rieke_path,
        two_seventy_input=two_seventy_path,
        two_seventy_poll_average_input=two_seventy_poll_average_path,
        synthesis_output=tmp_path / "synthesis.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.evidence_row_count == 9
    assert result.aggregate_support_row_count == 7
    assert result.majority_support_row_count == 3
    assert result.broad_many_cases_support_row_count == 0
    assert metadata["outputs"]["h1_goal_completion_status"] == "not_proven"
    assert metadata["outputs"]["broad_many_cases_support_row_count"] == 0
    assert metadata["limitations"]["state_poll_panel_rows_are_repeated_forecasts"] is True
    assert metadata["limitations"]["aggregate_mean_loss_not_same_as_majority_of_cases"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_validate_synthesis_table_rejects_count_mismatch() -> None:
    frame = pd.DataFrame(
        [
            {
                "evidence_id": "bad",
                "evidence_label": "Bad",
                "comparator_label": "Comparator",
                "case_count": 2,
                "case_unit": "resolved_outcomes",
                "polymarket_lower_loss_count": 2,
                "comparator_lower_loss_count": 1,
                "tie_count": 0,
                "polymarket_lower_loss_share": 1.0,
                "mean_polymarket_brier": 0.1,
                "mean_comparator_brier": 0.2,
                "mean_loss_advantage": 0.1,
                "aggregate_mean_supports_polymarket": True,
                "majority_cases_supports_polymarket": True,
                "broad_many_cases_claim_supported": False,
                "evidence_scope": "test",
                "limitation": "test",
            }
        ]
    )

    with pytest.raises(ValueError, match="add to case_count"):
        validate_synthesis_table(frame)


def _pairwise_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "comparator": "fivethirtyeight",
                "comparison_row_count": 194,
                "polymarket_lower_loss_count": 194,
                "comparator_lower_loss_count": 0,
                "tie_count": 0,
                "mean_polymarket_brier": 0.2303476739690721,
                "mean_comparator_brier": 0.3324239300244639,
                "mean_loss_advantage": 0.1020762560553918,
            }
        ]
    )


def _summary_frame(values: dict[str, float | int]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"summary_id": key, "value": value, "unit": "", "description": ""}
            for key, value in values.items()
        ]
    )
