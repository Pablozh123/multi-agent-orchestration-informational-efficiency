from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_direct_poll_loss_decomposition import (
    build_summary,
    generate_h1_direct_poll_loss_decomposition_outputs,
    read_direct_poll_cases,
    validate_direct_poll_cases,
)


def test_direct_poll_loss_decomposition_summary() -> None:
    cases = validate_direct_poll_cases(read_direct_poll_cases(_write_consensus()))
    summary = build_summary(cases, _unit_summary())

    assert int(_summary_value(summary, "direct_poll_case_count")) == 4
    assert int(_summary_value(summary, "direct_poll_polymarket_lower_loss_count")) == 2
    assert int(_summary_value(summary, "direct_poll_comparator_lower_loss_count")) == 2
    assert float(_summary_value(summary, "direct_poll_mean_polymarket_brier")) == pytest.approx(
        0.065
    )
    assert float(_summary_value(summary, "direct_poll_mean_poll_derived_brier")) == pytest.approx(
        0.0925
    )
    assert float(_summary_value(summary, "direct_poll_mean_loss_advantage")) == pytest.approx(
        0.0275
    )
    assert float(_summary_value(summary, "polymarket_win_total_loss_advantage")) == pytest.approx(
        0.19
    )
    assert float(
        _summary_value(summary, "comparator_win_total_loss_advantage_abs")
    ) == pytest.approx(0.08)
    assert int(_summary_value(summary, "direct_poll_aggregate_mean_supports_polymarket")) == 1
    assert int(_summary_value(summary, "direct_poll_case_majority_supports_polymarket")) == 0
    assert _summary_value(summary, "h1_goal_completion_status") == "not_proven"
    assert int(float(_summary_value(summary, "bounded_primary_row_count"))) == 10


def test_generate_direct_poll_loss_decomposition_outputs(tmp_path: Path) -> None:
    consensus = _write_consensus(tmp_path / "consensus.csv")
    unit_summary = tmp_path / "unit_summary.csv"
    _unit_summary().to_csv(unit_summary, index=False)

    result = generate_h1_direct_poll_loss_decomposition_outputs(
        consensus_input=consensus,
        unit_robustness_summary_input=unit_summary,
        cases_output=tmp_path / "cases.csv",
        summary_output=tmp_path / "summary.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.direct_poll_case_count == 4
    assert result.polymarket_lower_loss_count == 2
    assert result.comparator_lower_loss_count == 2
    assert result.aggregate_mean_supports_polymarket is True
    assert result.case_majority_supports_polymarket is False
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["broad_many_cases_claim_proven"] is False
    assert metadata["limitations"]["direct_poll_rows_are_not_independent_elections"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_direct_poll_loss_decomposition_rejects_forbidden_columns(tmp_path: Path) -> None:
    path = _write_consensus(tmp_path / "bad.csv")
    frame = pd.read_csv(path)
    frame["wallet_address"] = "0xabc"
    frame.to_csv(path, index=False)

    with pytest.raises(ValueError, match="forbidden columns"):
        read_direct_poll_cases(path)


def _write_consensus(path: Path | None = None) -> Path:
    if path is None:
        import tempfile

        path = Path(tempfile.mkdtemp()) / "consensus.csv"
    rows = [
        _row("source_a", "538 poll snapshot", "direct_poll_transform", "Arizona", 1.0, 0.8, 0.6),
        _row("source_a", "538 poll snapshot", "direct_poll_transform", "Florida", 1.0, 0.7, 0.8),
        _row("source_b", "270toWin poll average", "direct_poll_transform", "Arizona", 1.0, 0.8, 0.9),
        _row("source_b", "270toWin poll average", "direct_poll_transform", "Michigan", 0.0, 0.3, 0.4),
        _row("source_c", "model forecast", "poll_model_forecast", "Texas", 1.0, 0.9, 0.8),
    ]
    frame = pd.DataFrame(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return path


def _row(
    source_id: str,
    source_label: str,
    source_family: str,
    state: str,
    outcome: float,
    pm_probability: float,
    comparator_probability: float,
) -> dict[str, object]:
    pm_brier = (pm_probability - outcome) ** 2
    comparator_brier = (comparator_probability - outcome) ** 2
    if pm_brier < comparator_brier:
        lower_loss_source = "polymarket"
    elif comparator_brier < pm_brier:
        lower_loss_source = "comparator"
    else:
        lower_loss_source = "tie"
    return {
        "source_id": source_id,
        "source_label": source_label,
        "source_family": source_family,
        "state": state,
        "case_id": f"{source_id}_{state.lower()}",
        "outcome_value": outcome,
        "polymarket_probability": pm_probability,
        "comparator_probability": comparator_probability,
        "polymarket_brier": pm_brier,
        "comparator_brier": comparator_brier,
        "loss_advantage": comparator_brier - pm_brier,
        "lower_loss_source": lower_loss_source,
    }


def _unit_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _summary("primary_row_count", 10, "state-date rows"),
            _summary("primary_polymarket_lower_loss_count", 8, "state-date rows"),
            _summary("primary_state_month_unit_count", 4, "state_month units"),
            _summary("primary_state_month_polymarket_support_count", 4, "state_month units"),
            _summary(
                "primary_state_month_polymarket_exact_binomial_p_value_greater",
                0.0625,
                "p_value",
            ),
            _summary("primary_state_month_polymarket_exact_95_ci_low", 0.4729, "share"),
        ]
    )


def _summary(summary_id: str, value: object, unit: str) -> dict[str, object]:
    return {
        "summary_id": summary_id,
        "value": value,
        "unit": unit,
        "description": summary_id,
    }


def _summary_value(summary: pd.DataFrame, summary_id: str):
    row = summary.loc[summary["summary_id"] == summary_id, "value"]
    assert len(row) == 1
    return row.iloc[0]
