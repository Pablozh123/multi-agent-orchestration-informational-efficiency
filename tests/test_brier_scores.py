"""Tests for deterministic Brier Score baseline helpers."""
from __future__ import annotations

import pandas as pd
import pytest

from operations.analysis.compute_brier_scores import (
    BrierDecomposition,
    brier_decomposition,
    brier_score,
    brier_score_frame,
    compute_brier_by_source,
)


def test_brier_score_perfect_forecasts() -> None:
    """Perfect probability forecasts have Brier Score 0."""
    result = brier_score([0.0, 1.0, 1.0], [0, 1, 1])

    assert result == pytest.approx(0.0)


def test_brier_score_known_toy_example() -> None:
    """Classic Brier Score is mean squared probability error."""
    result = brier_score([0.25, 0.75], [0, 1])

    assert result == pytest.approx(0.0625)


def test_brier_score_frame_uses_dataframe_columns() -> None:
    df = pd.DataFrame(
        {
            "forecast": [0.2, 0.8],
            "outcome": [0, 1],
        }
    )

    assert brier_score_frame(df) == pytest.approx(0.04)


def test_brier_score_rejects_non_probability_forecast() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        brier_score([0.2, 1.2], [0, 1])


def test_brier_score_rejects_non_binary_outcome() -> None:
    with pytest.raises(ValueError, match="binary"):
        brier_score([0.2, 0.8], [0, 2])


def test_brier_score_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError, match="same length"):
        brier_score([0.2], [0, 1])


def test_brier_decomposition_known_toy_example() -> None:
    """Murphy decomposition returns known reliability/resolution/uncertainty."""
    df = pd.DataFrame(
        {
            "forecast": [0.2, 0.2, 0.8, 0.8],
            "outcome": [0, 1, 1, 1],
        }
    )

    result = brier_decomposition(df, bins=[0.0, 0.5, 1.0])

    assert isinstance(result, BrierDecomposition)
    assert result.brier_score == pytest.approx(0.19)
    assert result.reliability == pytest.approx(0.065)
    assert result.resolution == pytest.approx(0.0625)
    assert result.uncertainty == pytest.approx(0.1875)
    assert result.reliability - result.resolution + result.uncertainty == pytest.approx(
        result.brier_score
    )
    assert result.row_count == 4
    assert result.bin_count == 2


def test_brier_decomposition_accepts_precomputed_bin_labels() -> None:
    df = pd.DataFrame(
        {
            "forecast": [0.2, 0.2, 0.8, 0.8],
            "outcome": [0, 1, 1, 1],
        }
    )
    bins = pd.Series(["low", "low", "high", "high"])

    result = brier_decomposition(df, bins=bins)

    assert result.bin_count == 2
    assert result.row_count == 4


def test_compute_brier_by_source_compares_probability_sources() -> None:
    df = pd.DataFrame(
        {
            "source": ["polymarket", "polymarket", "fivethirtyeight", "fivethirtyeight"],
            "forecast": [0.7, 0.8, 0.6, 0.6],
            "outcome": [1, 1, 1, 1],
        }
    )

    result = compute_brier_by_source(df)

    scores = dict(zip(result["source"], result["brier_score"]))
    assert set(scores) == {"polymarket", "fivethirtyeight"}
    assert scores["polymarket"] == pytest.approx(((0.3**2) + (0.2**2)) / 2)
    assert scores["fivethirtyeight"] == pytest.approx(0.16)


def test_compute_brier_by_source_excludes_rcp_without_documented_transform() -> None:
    df = pd.DataFrame(
        {
            "source": ["polymarket", "rcp"],
            "forecast": [0.8, 0.9],
            "outcome": [1, 1],
        }
    )

    result = compute_brier_by_source(df)

    assert list(result["source"]) == ["polymarket"]


def test_compute_brier_by_source_rcp_inclusion_fails_without_documentation() -> None:
    df = pd.DataFrame(
        {
            "source": ["polymarket", "rcp"],
            "forecast": [0.8, 0.9],
            "outcome": [1, 1],
        }
    )

    with pytest.raises(ValueError, match="RCP inclusion requires"):
        compute_brier_by_source(df, include_rcp=True)


def test_compute_brier_by_source_documentation_flag_alone_still_excludes_rcp() -> None:
    df = pd.DataFrame(
        {
            "source": ["polymarket", "rcp"],
            "forecast": [0.8, 0.9],
            "outcome": [1, 1],
        }
    )

    result = compute_brier_by_source(df, rcp_transformation_documented=True)

    assert list(result["source"]) == ["polymarket"]


def test_compute_brier_by_source_allowed_sources_cannot_silently_enable_rcp() -> None:
    df = pd.DataFrame(
        {
            "source": ["polymarket", "rcp"],
            "forecast": [0.8, 0.9],
            "outcome": [1, 1],
        }
    )

    result = compute_brier_by_source(df, allowed_sources=("polymarket", "rcp"))

    assert list(result["source"]) == ["polymarket"]


def test_compute_brier_by_source_can_include_documented_rcp_transform() -> None:
    df = pd.DataFrame(
        {
            "source": ["polymarket", "rcp"],
            "forecast": [0.8, 0.9],
            "outcome": [1, 1],
        }
    )

    result = compute_brier_by_source(
        df,
        include_rcp=True,
        rcp_transformation_documented=True,
    )

    assert set(result["source"]) == {"polymarket", "rcp"}


def test_missing_dataframe_columns_raise_clear_error() -> None:
    df = pd.DataFrame({"forecast": [0.8]})

    with pytest.raises(ValueError, match="missing required columns"):
        brier_score_frame(df)
