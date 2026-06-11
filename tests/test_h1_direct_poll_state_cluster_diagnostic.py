from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_direct_poll_state_cluster_diagnostic import (
    build_state_table,
    build_summary,
    generate_h1_direct_poll_state_cluster_diagnostic_outputs,
    read_cases,
    validate_state_table,
)


def test_state_cluster_summary_counts_and_mean() -> None:
    cases = read_cases(_write_cases())
    states = validate_state_table(build_state_table(cases))
    summary = build_summary(
        cases=cases,
        states=states,
        bootstrap_iterations=500,
        random_seed=123,
    )

    assert int(_summary_value(summary, "source_state_case_count")) == 6
    assert int(_summary_value(summary, "state_count")) == 4
    assert int(_summary_value(summary, "state_mean_polymarket_support_count")) == 2
    assert int(_summary_value(summary, "state_mean_poll_support_count")) == 2
    assert float(_summary_value(summary, "equal_state_mean_loss_advantage")) == pytest.approx(
        0.02625
    )
    assert float(_summary_value(summary, "equal_state_median_loss_advantage")) == pytest.approx(
        0.01
    )
    assert int(_summary_value(summary, "state_cluster_mean_supports_polymarket")) == 1
    assert int(_summary_value(summary, "state_count_majority_supports_polymarket")) == 0
    assert int(_summary_value(summary, "broad_many_cases_claim_proven")) == 0
    assert _summary_value(summary, "h1_goal_completion_status") == "not_proven"


def test_generate_state_cluster_outputs(tmp_path: Path) -> None:
    cases_path = _write_cases(tmp_path / "cases.csv")

    result = generate_h1_direct_poll_state_cluster_diagnostic_outputs(
        cases_input=cases_path,
        state_output=tmp_path / "states.csv",
        summary_output=tmp_path / "summary.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
        bootstrap_iterations=500,
        random_seed=123,
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.state_count == 4
    assert result.state_mean_polymarket_support_count == 2
    assert result.state_mean_poll_support_count == 2
    assert result.equal_state_mean_loss_advantage == pytest.approx(0.02625)
    assert result.bootstrap_ci_low < result.equal_state_mean_loss_advantage
    assert result.bootstrap_ci_high > result.equal_state_mean_loss_advantage
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["broad_many_cases_claim_proven"] is False
    assert metadata["limitations"]["states_are_not_independent_elections"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_state_cluster_rejects_forbidden_columns(tmp_path: Path) -> None:
    path = _write_cases(tmp_path / "bad.csv")
    frame = pd.read_csv(path)
    frame["maker_address"] = "0xabc"
    frame.to_csv(path, index=False)

    with pytest.raises(ValueError, match="forbidden columns"):
        read_cases(path)


def _write_cases(path: Path | None = None) -> Path:
    if path is None:
        import tempfile

        path = Path(tempfile.mkdtemp()) / "cases.csv"
    rows = [
        _row("source_a", "538 poll snapshot", "Arizona", 0.04, 0.16),
        _row("source_b", "270toWin poll average", "Arizona", 0.09, 0.17),
        _row("source_a", "538 poll snapshot", "Florida", 0.09, 0.07),
        _row("source_b", "270toWin poll average", "Florida", 0.04, 0.03),
        _row("source_a", "538 poll snapshot", "Georgia", 0.09, 0.12),
        _row("source_a", "538 poll snapshot", "Ohio", 0.04, 0.03),
    ]
    frame = pd.DataFrame(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return path


def _row(
    source_id: str,
    source_label: str,
    state: str,
    pm_brier: float,
    comparator_brier: float,
) -> dict[str, object]:
    if pm_brier < comparator_brier:
        lower_loss_source = "polymarket"
    elif comparator_brier < pm_brier:
        lower_loss_source = "comparator"
    else:
        lower_loss_source = "tie"
    return {
        "source_id": source_id,
        "source_label": source_label,
        "state": state,
        "case_id": f"{source_id}_{state.lower()}",
        "polymarket_brier": pm_brier,
        "comparator_brier": comparator_brier,
        "loss_advantage": comparator_brier - pm_brier,
        "lower_loss_source": lower_loss_source,
    }


def _summary_value(summary: pd.DataFrame, summary_id: str):
    row = summary.loc[summary["summary_id"] == summary_id, "value"]
    assert len(row) == 1
    return row.iloc[0]
