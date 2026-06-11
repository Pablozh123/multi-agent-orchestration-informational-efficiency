from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_state_source_consensus import (
    SOURCE_SPECS,
    build_consensus_cases,
    build_state_summary,
    build_summary,
    generate_h1_state_source_consensus_outputs,
    read_source_cases,
    validate_consensus_cases,
)


def test_build_state_source_consensus_counts() -> None:
    cases = _fixture_cases()
    state_summary = build_state_summary(cases)
    summary = build_summary(cases=cases, state_summary=state_summary)

    arizona = state_summary.loc[state_summary["state"] == "Arizona"].iloc[0]
    florida = state_summary.loc[state_summary["state"] == "Florida"].iloc[0]

    assert len(cases) == 11
    assert arizona["state_consensus_winner"] == "polymarket"
    assert florida["state_consensus_winner"] == "comparator"
    assert int(_summary_value(summary, "source_state_case_count")) == 11
    assert int(_summary_value(summary, "state_count")) == 3
    assert int(_summary_value(summary, "all_source_polymarket_lower_loss_count")) == 5
    assert int(_summary_value(summary, "all_source_comparator_lower_loss_count")) == 5
    assert int(_summary_value(summary, "all_source_tie_count")) == 1
    assert int(_summary_value(summary, "all_source_polymarket_majority_state_count")) == 2
    assert int(_summary_value(summary, "all_source_comparator_majority_state_count")) == 1
    assert int(_summary_value(summary, "direct_poll_two_source_state_count")) == 2
    assert int(_summary_value(summary, "direct_poll_two_source_tie_state_count")) == 2
    assert int(_summary_value(summary, "broad_many_cases_claim_supported_now")) == 0


def test_generate_state_source_consensus_outputs(tmp_path: Path) -> None:
    paths = _write_source_inputs(tmp_path)

    result = generate_h1_state_source_consensus_outputs(
        state_poll_input=paths["five_thirty_eight_poll_snapshot"],
        two_seventy_poll_average_input=paths["two_seventy_poll_average"],
        rieke_input=paths["rieke_poll_model"],
        two_seventy_input=paths["two_seventy_jhk_model"],
        cases_output=tmp_path / "cases.csv",
        state_summary_output=tmp_path / "state_summary.csv",
        summary_output=tmp_path / "summary.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    summary = pd.read_csv(tmp_path / "summary.csv")
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.source_state_case_count == 11
    assert result.state_count == 3
    assert result.all_source_polymarket_majority_state_count == 2
    assert result.all_source_comparator_majority_state_count == 1
    assert result.direct_poll_two_source_polymarket_majority_state_count == 0
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["broad_many_cases_claim_supported_now"] is False
    assert metadata["limitations"]["state_sources_are_not_independent_elections"] is True
    assert float(_summary_value(summary, "all_source_mean_loss_advantage")) == pytest.approx(
        0.019090909090909
    )
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_read_source_cases_rejects_forbidden_columns(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    frame = _source_frame(
        states=("Arizona",),
        outcomes=(1.0,),
        pm_probabilities=(0.8,),
        comparator_probabilities=(0.6,),
        comparator_column="poll_derived_probability",
        comparator_brier_column="poll_derived_brier",
    )
    frame["maker_address"] = "0xabc"
    frame.to_csv(path, index=False)

    with pytest.raises(ValueError, match="forbidden columns"):
        read_source_cases(path, spec=SOURCE_SPECS[0])


def _fixture_cases() -> pd.DataFrame:
    paths = _memory_sources()
    frames = {
        spec.source_id: read_source_cases(path, spec=spec)
        for spec, path in zip(SOURCE_SPECS, paths, strict=True)
    }
    return validate_consensus_cases(build_consensus_cases(frames))


def _memory_sources() -> list[Path]:
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    return list(_write_source_inputs(tmp).values())


def _write_source_inputs(tmp_path: Path) -> dict[str, Path]:
    inputs = {
        "five_thirty_eight_poll_snapshot": _source_frame(
            states=("Arizona", "Florida", "Michigan"),
            outcomes=(1.0, 1.0, 0.0),
            pm_probabilities=(0.8, 0.7, 0.3),
            comparator_probabilities=(0.6, 0.8, 0.4),
            comparator_column="poll_derived_probability",
            comparator_brier_column="poll_derived_brier",
        ),
        "two_seventy_poll_average": _source_frame(
            states=("Arizona", "Florida"),
            outcomes=(1.0, 1.0),
            pm_probabilities=(0.8, 0.7),
            comparator_probabilities=(0.9, 0.6),
            comparator_column="poll_derived_probability",
            comparator_brier_column="poll_derived_brier",
        ),
        "rieke_poll_model": _source_frame(
            states=("Arizona", "Florida", "Michigan"),
            outcomes=(1.0, 1.0, 0.0),
            pm_probabilities=(0.8, 0.7, 0.3),
            comparator_probabilities=(0.7, 0.8, 0.2),
            comparator_column="rieke_republican_win_probability",
            comparator_brier_column="rieke_brier",
        ),
        "two_seventy_jhk_model": _source_frame(
            states=("Arizona", "Florida", "Michigan"),
            outcomes=(1.0, 1.0, 0.0),
            pm_probabilities=(0.8, 0.7, 0.3),
            comparator_probabilities=(0.8, 0.9, 0.5),
            comparator_column="two_seventy_trump_win_probability",
            comparator_brier_column="two_seventy_brier",
        ),
    }
    paths: dict[str, Path] = {}
    for key, frame in inputs.items():
        path = tmp_path / f"{key}.csv"
        frame.to_csv(path, index=False)
        paths[key] = path
    return paths


def _source_frame(
    *,
    states: tuple[str, ...],
    outcomes: tuple[float, ...],
    pm_probabilities: tuple[float, ...],
    comparator_probabilities: tuple[float, ...],
    comparator_column: str,
    comparator_brier_column: str,
) -> pd.DataFrame:
    rows = []
    for state, outcome, pm_probability, comparator_probability in zip(
        states,
        outcomes,
        pm_probabilities,
        comparator_probabilities,
        strict=True,
    ):
        rows.append(
            {
                "case_id": f"case_{state.lower()}",
                "state": state,
                "outcome_value": outcome,
                "polymarket_probability": pm_probability,
                "polymarket_brier": (pm_probability - outcome) ** 2,
                comparator_column: comparator_probability,
                comparator_brier_column: (comparator_probability - outcome) ** 2,
            }
        )
    return pd.DataFrame(rows)


def _summary_value(summary: pd.DataFrame, summary_id: str):
    row = summary.loc[summary["summary_id"] == summary_id, "value"]
    assert len(row) == 1
    return row.iloc[0]
