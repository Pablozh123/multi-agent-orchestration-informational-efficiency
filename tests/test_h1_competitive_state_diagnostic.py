from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_competitive_state_diagnostic import (
    build_competitive_cases,
    build_summary,
    build_tier_summary,
    generate_h1_competitive_state_diagnostic_outputs,
    read_consensus_cases,
    validate_competitive_cases,
)


def test_competitive_state_diagnostic_splits_by_observed_distance() -> None:
    cases = validate_competitive_cases(build_competitive_cases(_consensus_frame()))
    tiers = build_tier_summary(cases)
    summary = build_summary(cases=cases, tiers=tiers)

    all_low = _tier(tiers, "all_sources", "all", "low_distance_tercile")
    all_high = _tier(tiers, "all_sources", "all", "high_distance_tercile")
    direct_low = _tier(
        tiers,
        "within_source_family",
        "direct_poll_transform",
        "low_distance_tercile",
    )

    assert int(all_low["case_count"]) == 4
    assert int(all_low["polymarket_lower_loss_count"]) == 4
    assert int(all_low["comparator_lower_loss_count"]) == 0
    assert int(all_high["polymarket_lower_loss_count"]) == 0
    assert int(all_high["comparator_lower_loss_count"]) == 4
    assert int(direct_low["polymarket_lower_loss_count"]) == 2
    assert int(direct_low["comparator_lower_loss_count"]) == 0
    assert int(_summary_value(summary, "all_low_distance_polymarket_lower_loss_count")) == 4
    assert int(_summary_value(summary, "direct_low_distance_polymarket_lower_loss_count")) == 2
    assert int(_summary_value(summary, "broad_many_cases_claim_supported_now")) == 0


def test_generate_competitive_state_diagnostic_outputs(tmp_path: Path) -> None:
    input_path = tmp_path / "consensus.csv"
    _consensus_frame().to_csv(input_path, index=False)

    result = generate_h1_competitive_state_diagnostic_outputs(
        consensus_cases_input=input_path,
        cases_output=tmp_path / "cases.csv",
        tiers_output=tmp_path / "tiers.csv",
        summary_output=tmp_path / "summary.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    summary = pd.read_csv(tmp_path / "summary.csv")
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.case_count == 12
    assert result.all_low_distance_pm_lower_loss_count == 4
    assert result.all_low_distance_comparator_lower_loss_count == 0
    assert result.direct_low_distance_pm_lower_loss_count == 2
    assert result.direct_low_distance_comparator_lower_loss_count == 0
    assert metadata["method"]["uses_fixed_competitiveness_thresholds"] is False
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["competitive_subset_supports_polymarket"] is True
    assert int(_summary_value(summary, "safe_state_subset_contradicts_strong_claim")) == 1
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_read_consensus_cases_rejects_forbidden_columns(tmp_path: Path) -> None:
    input_path = tmp_path / "bad.csv"
    frame = _consensus_frame()
    frame["taker_address"] = "0xabc"
    frame.to_csv(input_path, index=False)

    with pytest.raises(ValueError, match="forbidden columns"):
        read_consensus_cases(input_path)


def _consensus_frame() -> pd.DataFrame:
    rows = []
    direct_distances = [0.02, 0.03, 0.20, 0.25, 0.47, 0.48]
    model_distances = [0.04, 0.05, 0.22, 0.26, 0.49, 0.50]
    for family, source_id, distances in (
        ("direct_poll_transform", "direct_source", direct_distances),
        ("poll_model_forecast", "model_source", model_distances),
    ):
        for idx, distance in enumerate(distances):
            outcome = 1.0
            pm_probability = 0.70 if idx < 4 else 0.80
            comparator_probability = 0.5 + distance
            # In low-distance rows, make Polymarket better except one model row.
            if idx < 2:
                comparator_probability = 0.58 if family == "direct_poll_transform" else 0.68
            rows.append(
                {
                    "source_id": source_id,
                    "source_label": source_id,
                    "source_family": family,
                    "source_artifact": f"{source_id}.csv",
                    "case_id": f"{source_id}_{idx}",
                    "state": f"State {idx}",
                    "outcome_value": outcome,
                    "polymarket_probability": pm_probability,
                    "comparator_probability": comparator_probability,
                    "polymarket_brier": (pm_probability - outcome) ** 2,
                    "comparator_brier": (comparator_probability - outcome) ** 2,
                    "loss_advantage": (comparator_probability - outcome) ** 2
                    - (pm_probability - outcome) ** 2,
                    "lower_loss_source": (
                        "polymarket"
                        if (pm_probability - outcome) ** 2
                        < (comparator_probability - outcome) ** 2
                        else "comparator"
                    ),
                }
            )
    return pd.DataFrame(rows)


def _tier(
    tiers: pd.DataFrame,
    tier_scope: str,
    source_family: str,
    competitiveness_tier: str,
) -> pd.Series:
    rows = tiers.loc[
        (tiers["tier_scope"] == tier_scope)
        & (tiers["source_family"] == source_family)
        & (tiers["competitiveness_tier"] == competitiveness_tier)
    ]
    assert len(rows) == 1
    return rows.iloc[0]


def _summary_value(summary: pd.DataFrame, summary_id: str):
    row = summary.loc[summary["summary_id"] == summary_id, "value"]
    assert len(row) == 1
    return row.iloc[0]
