"""Deterministic Brier Score helpers for probability forecasts.

This module is intentionally small and data-frame oriented. It does not connect
to external APIs or databases and does not use LLMs.

RCP note:
    RCP polling averages are not native probability forecasts. Do not include
    RCP rows unless a separate, documented probability transformation exists.
    TODO: document and test the RCP polling-average-to-probability transform
    before enabling RCP comparisons.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Sequence

import numpy as np
import pandas as pd


DEFAULT_ALLOWED_SOURCES = ("polymarket", "fivethirtyeight")
RCP_SOURCE = "rcp"
RCP_TRANSFORMATION_ERROR = (
    "RCP inclusion requires include_rcp=True and "
    "rcp_transformation_documented=True because RCP polling averages are not "
    "native probability forecasts."
)


@dataclass(frozen=True)
class BrierDecomposition:
    """Murphy decomposition of the binary Brier Score."""

    brier_score: float
    reliability: float
    resolution: float
    uncertainty: float
    row_count: int
    bin_count: int

    def to_dict(self) -> dict[str, float | int]:
        """Return a JSON-friendly dictionary."""
        return asdict(self)


def _as_numeric_series(values: Iterable[float], name: str) -> pd.Series:
    """Convert values to a numeric Series and reject missing/non-numeric values."""
    series = pd.Series(values, name=name)
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.isna().any():
        raise ValueError(f"{name} contains missing or non-numeric values")
    return numeric.astype(float)


def _validate_probabilities(forecasts: pd.Series) -> None:
    """Raise if forecasts are not valid probabilities in [0, 1]."""
    if not forecasts.between(0.0, 1.0).all():
        raise ValueError("forecast probabilities must be between 0 and 1")


def _validate_binary_outcomes(outcomes: pd.Series) -> None:
    """Raise if outcomes are not binary 0/1 values."""
    values = set(outcomes.unique())
    if not values.issubset({0.0, 1.0}):
        raise ValueError("outcomes must be binary values 0 or 1")


def brier_score(
    forecasts: Iterable[float],
    outcomes: Iterable[float],
) -> float:
    """Return the classic mean Brier Score for binary probability forecasts.

    Args:
        forecasts: Probabilities in [0, 1].
        outcomes: Binary outcomes, encoded as 0 or 1.

    Returns:
        Mean squared forecast error.
    """
    forecast_series = _as_numeric_series(forecasts, "forecasts")
    outcome_series = _as_numeric_series(outcomes, "outcomes")

    if len(forecast_series) != len(outcome_series):
        raise ValueError("forecasts and outcomes must have the same length")
    if len(forecast_series) == 0:
        raise ValueError("forecasts and outcomes must not be empty")

    _validate_probabilities(forecast_series)
    _validate_binary_outcomes(outcome_series)

    errors = np.square(forecast_series.to_numpy() - outcome_series.to_numpy())
    return float(np.mean(errors))


def brier_score_frame(
    df: pd.DataFrame,
    forecast_col: str = "forecast",
    outcome_col: str = "outcome",
) -> float:
    """Return the Brier Score for forecast/outcome columns in a DataFrame."""
    _require_columns(df, (forecast_col, outcome_col))
    return brier_score(df[forecast_col], df[outcome_col])


def brier_decomposition(
    df: pd.DataFrame,
    bins: Sequence[float] | pd.Series,
    forecast_col: str = "forecast",
    outcome_col: str = "outcome",
) -> BrierDecomposition:
    """Return reliability, resolution, and uncertainty for binary forecasts.

    If `bins` is a sequence of numeric edges, forecasts are assigned with
    `pd.cut`. If `bins` is a Series, it is treated as precomputed bin labels and
    must be aligned row-for-row with `df`.
    """
    _require_columns(df, (forecast_col, outcome_col))
    forecasts = _as_numeric_series(df[forecast_col], forecast_col)
    outcomes = _as_numeric_series(df[outcome_col], outcome_col)
    _validate_probabilities(forecasts)
    _validate_binary_outcomes(outcomes)

    bin_labels = _make_bin_labels(forecasts, bins)
    work = pd.DataFrame(
        {"forecast": forecasts, "outcome": outcomes, "bin": bin_labels}
    ).dropna(subset=["bin"])
    if work.empty:
        raise ValueError("bins did not assign any forecasts to a bin")

    total = len(work)
    outcome_mean = float(work["outcome"].mean())
    grouped = work.groupby("bin", observed=True)

    reliability = 0.0
    resolution = 0.0
    for _, group in grouped:
        weight = len(group) / total
        mean_forecast = float(group["forecast"].mean())
        observed_frequency = float(group["outcome"].mean())
        reliability += weight * (mean_forecast - observed_frequency) ** 2
        resolution += weight * (observed_frequency - outcome_mean) ** 2

    uncertainty = outcome_mean * (1.0 - outcome_mean)
    return BrierDecomposition(
        brier_score=brier_score(work["forecast"], work["outcome"]),
        reliability=float(reliability),
        resolution=float(resolution),
        uncertainty=float(uncertainty),
        row_count=total,
        bin_count=int(work["bin"].nunique()),
    )


def compute_brier_by_source(
    df: pd.DataFrame,
    source_col: str = "source",
    forecast_col: str = "forecast",
    outcome_col: str = "outcome",
    allowed_sources: Sequence[str] = DEFAULT_ALLOWED_SOURCES,
    include_rcp: bool = False,
    rcp_transformation_documented: bool = False,
) -> pd.DataFrame:
    """Compute mean Brier Scores for approved probability forecast sources.

    Polymarket and FiveThirtyEight may be compared when both are represented as
    probabilities. RCP rows are excluded by default because RCP is not a native
    probability forecast source. RCP can only be included when both
    `include_rcp` and `rcp_transformation_documented` are true.
    """
    _require_columns(df, (source_col, forecast_col, outcome_col))

    allowed = {
        source.lower()
        for source in allowed_sources
        if source.lower() != RCP_SOURCE
    }
    if include_rcp and not rcp_transformation_documented:
        raise ValueError(RCP_TRANSFORMATION_ERROR)
    if include_rcp and rcp_transformation_documented:
        allowed.add(RCP_SOURCE)

    normalized = df.copy()
    normalized[source_col] = normalized[source_col].astype(str).str.lower()
    excluded_sources = set(normalized[source_col].unique()) - allowed
    if excluded_sources:
        normalized = normalized[normalized[source_col].isin(allowed)]

    if normalized.empty:
        raise ValueError("no allowed probability forecast sources available")

    rows: list[dict[str, float | int | str]] = []
    for source, group in normalized.groupby(source_col, sort=True):
        rows.append(
            {
                "source": str(source),
                "row_count": int(len(group)),
                "brier_score": brier_score(group[forecast_col], group[outcome_col]),
            }
        )
    return pd.DataFrame(rows, columns=["source", "row_count", "brier_score"])


def _make_bin_labels(
    forecasts: pd.Series,
    bins: Sequence[float] | pd.Series,
) -> pd.Series:
    """Return bin labels from bin edges or an aligned Series of labels."""
    if isinstance(bins, pd.Series):
        if len(bins) != len(forecasts):
            raise ValueError("bin label Series must match forecast length")
        return bins.reset_index(drop=True)

    if len(bins) < 2:
        raise ValueError("bin edges must contain at least two values")
    return pd.cut(
        forecasts.reset_index(drop=True),
        bins=list(bins),
        include_lowest=True,
        right=True,
    )


def _require_columns(df: pd.DataFrame, columns: Sequence[str]) -> None:
    """Raise a clear error if a DataFrame is missing required columns."""
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}")
