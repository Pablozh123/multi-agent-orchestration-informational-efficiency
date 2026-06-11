from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_state_poll_panel_state_significance import (
    build_significance_summary,
    build_summary,
    generate_h1_state_poll_panel_state_significance_outputs,
    read_state_summary,
    validate_significance,
)


def test_state_significance_uses_exact_state_majority_test() -> None:
    significance = validate_significance(build_significance_summary(_state_frame()))
    summary = build_summary(significance)

    non_safe = _scope(significance, "late_non_safe_distance")
    high = _scope(significance, "late_high_distance")

    assert int(non_safe["state_count"]) == 4
    assert int(non_safe["polymarket_majority_state_count"]) == 4
    assert int(non_safe["poll_derived_majority_state_count"]) == 0
    assert float(non_safe["polymarket_exact_binomial_p_value_greater"]) == pytest.approx(
        0.0625
    )
    assert bool(non_safe["supports_polymarket_state_level"]) is False
    assert int(high["polymarket_majority_state_count"]) == 0
    assert int(high["poll_derived_majority_state_count"]) == 3
    assert float(high["poll_derived_exact_binomial_p_value_greater"]) == pytest.approx(
        0.125
    )
    assert int(_summary_value(summary, "late_non_safe_polymarket_majority_state_count")) == 4
    assert int(_summary_value(summary, "broad_many_cases_claim_supported_now")) == 0


def test_generate_state_significance_outputs(tmp_path: Path) -> None:
    state_path = tmp_path / "state.csv"
    _state_frame().to_csv(state_path, index=False)

    result = generate_h1_state_poll_panel_state_significance_outputs(
        state_input=state_path,
        significance_output=tmp_path / "significance.csv",
        summary_output=tmp_path / "summary.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    significance = pd.read_csv(tmp_path / "significance.csv")
    summary = pd.read_csv(tmp_path / "summary.csv")
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.late_non_safe_state_count == 4
    assert result.late_non_safe_polymarket_majority_state_count == 4
    assert result.late_non_safe_p_value == pytest.approx(0.0625)
    assert len(significance) == 2
    assert int(_summary_value(summary, "late_high_distance_poll_majority_state_count")) == 3
    assert metadata["method"]["does_not_use_llms"] is True
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["limitations"]["state_sign_test_is_bounded_not_broad_proof"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_read_state_summary_rejects_forbidden_columns(tmp_path: Path) -> None:
    state_path = tmp_path / "bad.csv"
    frame = _state_frame()
    frame["wallet_address"] = "0xabc"
    frame.to_csv(state_path, index=False)

    with pytest.raises(ValueError, match="forbidden columns"):
        read_state_summary(state_path)


def _state_frame() -> pd.DataFrame:
    rows = []
    for idx, advantage in enumerate([0.04, 0.06, 0.08, 0.10], start=1):
        rows.append(_state_row("late_non_safe_distance", f"PM State {idx}", advantage, True))
    for idx, advantage in enumerate([-0.01, -0.02, -0.03], start=1):
        rows.append(_state_row("late_high_distance", f"Poll State {idx}", advantage, False))
    return pd.DataFrame(rows)


def _state_row(
    scope_id: str,
    state: str,
    advantage: float,
    supports_pm: bool,
) -> dict[str, object]:
    pm_lower = 5 if supports_pm else 0
    poll_lower = 0 if supports_pm else 5
    return {
        "scope_id": scope_id,
        "state": state,
        "row_count": 5,
        "polymarket_lower_loss_count": pm_lower,
        "poll_derived_lower_loss_count": poll_lower,
        "tie_count": 0,
        "polymarket_better_share": pm_lower / 5,
        "mean_polymarket_brier": 0.10,
        "mean_poll_derived_brier": 0.10 + advantage,
        "mean_loss_advantage": advantage,
        "aggregate_mean_supports_polymarket": supports_pm,
        "majority_rows_support_polymarket": supports_pm,
    }


def _scope(frame: pd.DataFrame, scope_id: str) -> pd.Series:
    rows = frame.loc[frame["scope_id"] == scope_id]
    assert len(rows) == 1
    return rows.iloc[0]


def _summary_value(summary: pd.DataFrame, summary_id: str):
    row = summary.loc[summary["summary_id"] == summary_id, "value"]
    assert len(row) == 1
    return row.iloc[0]
