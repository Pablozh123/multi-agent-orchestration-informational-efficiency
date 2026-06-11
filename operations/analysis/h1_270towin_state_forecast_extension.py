"""Build an H1 270toWin/JHK 50-state forecast extension.

This module compares Polymarket Republican-win state probabilities with the
final 270toWin Battleground 270 state probabilities for 2024. The 270toWin
simulator is described as largely based on a JHK data-driven presidential
model. The source gives exact percentages for 22 states and censored
``>99.9%`` buckets for 28 safe states; bucketed rows are marked explicitly and
use conservative boundary probabilities for Brier scoring.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

import httpx
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from operations.analysis.h1_state_poll_snapshot_extension import (
    ALL_US_STATES,
    CLOB_BASE_URL,
    GAMMA_BASE_URL,
    MAX_PRICE_TIME_DISTANCE_SECONDS,
    POLYMARKET_STATE_MARKET_SLUGS,
    REPUBLICAN_WON_2024_STATES,
    fetch_nearest_price,
    target_token_id,
)
from operations.analysis.run_h2_event_windows import RESULTS_DIR


TWO_SEVENTY_TO_WIN_BATTLEGROUND_URL = (
    "https://www.270towin.com/2024-simulation/battleground-270/"
)
TWO_SEVENTY_TO_WIN_SIMULATION_URL = "https://www.270towin.com/2024-simulation/"
JHK_FORECAST_URL = "https://projects.jhkforecasts.com/2024/president/"

FORECAST_DATE = "2024-11-05"
FORECAST_TIMESTAMP_UTC = "2024-11-05T13:00:00Z"

CASE_OUTPUT = RESULTS_DIR / "h1_270towin_state_forecast_cases.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_270towin_state_forecast_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_270towin_state_forecast.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_270towin_state_forecast_metadata.json"

CASE_COLUMNS: tuple[str, ...] = (
    "case_id",
    "state",
    "forecast_date",
    "forecast_timestamp_utc",
    "forecast_timestamp_precision",
    "polymarket_observed_at_utc",
    "polymarket_time_distance_seconds",
    "polymarket_market_slug",
    "polymarket_market_id",
    "polymarket_condition_id",
    "target_outcome",
    "target_token_id",
    "outcome_value",
    "two_seventy_trump_win_probability",
    "two_seventy_probability_precision",
    "two_seventy_source_bucket",
    "polymarket_probability",
    "polymarket_brier",
    "two_seventy_brier",
    "loss_advantage",
    "lower_loss_source",
    "two_seventy_source_url",
    "two_seventy_simulation_source_url",
    "jhk_source_url",
    "polymarket_source_url",
    "price_history_source_url",
    "allowed_interpretation",
    "limitation",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "summary_id",
    "value",
    "unit",
    "description",
)


@dataclass(frozen=True)
class TwoSeventyStateProbability:
    """One curated 270toWin state probability row."""

    state: str
    trump_probability: float
    probability_precision: str
    source_bucket: str


@dataclass(frozen=True)
class H1TwoSeventyStateForecastResult:
    """Summary of generated 270toWin/JHK H1 artifacts."""

    cases_path: Path
    summary_path: Path
    figure_path: Path
    metadata_path: Path
    case_count: int
    exact_probability_case_count: int
    censored_boundary_case_count: int
    polymarket_lower_loss_count: int
    two_seventy_lower_loss_count: int
    mean_polymarket_brier: float
    mean_two_seventy_brier: float

    def to_dict(self) -> dict[str, float | int | str]:
        return {
            "cases_path": str(self.cases_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "case_count": self.case_count,
            "exact_probability_case_count": self.exact_probability_case_count,
            "censored_boundary_case_count": self.censored_boundary_case_count,
            "polymarket_lower_loss_count": self.polymarket_lower_loss_count,
            "two_seventy_lower_loss_count": self.two_seventy_lower_loss_count,
            "mean_polymarket_brier": self.mean_polymarket_brier,
            "mean_two_seventy_brier": self.mean_two_seventy_brier,
        }


TWO_SEVENTY_STATE_PROBABILITIES: tuple[TwoSeventyStateProbability, ...] = (
    TwoSeventyStateProbability("Alabama", 0.999, "censored_boundary_>99.9", "Trump >99.9%"),
    TwoSeventyStateProbability("Alaska", 0.982, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("Arizona", 0.693, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("Arkansas", 0.999, "censored_boundary_>99.9", "Trump >99.9%"),
    TwoSeventyStateProbability("California", 0.001, "censored_boundary_>99.9", "Harris >99.9%"),
    TwoSeventyStateProbability("Colorado", 0.024, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("Connecticut", 0.001, "censored_boundary_>99.9", "Harris >99.9%"),
    TwoSeventyStateProbability("Delaware", 0.010, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("Florida", 0.909, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("Georgia", 0.635, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("Hawaii", 0.001, "censored_boundary_>99.9", "Harris >99.9%"),
    TwoSeventyStateProbability("Idaho", 0.999, "censored_boundary_>99.9", "Trump >99.9%"),
    TwoSeventyStateProbability("Illinois", 0.014, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("Indiana", 0.999, "censored_boundary_>99.9", "Trump >99.9%"),
    TwoSeventyStateProbability("Iowa", 0.888, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("Kansas", 0.999, "censored_boundary_>99.9", "Trump >99.9%"),
    TwoSeventyStateProbability("Kentucky", 0.999, "censored_boundary_>99.9", "Trump >99.9%"),
    TwoSeventyStateProbability("Louisiana", 0.999, "censored_boundary_>99.9", "Trump >99.9%"),
    TwoSeventyStateProbability("Maine", 0.085, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("Maryland", 0.001, "censored_boundary_>99.9", "Harris >99.9%"),
    TwoSeventyStateProbability("Massachusetts", 0.001, "censored_boundary_>99.9", "Harris >99.9%"),
    TwoSeventyStateProbability("Michigan", 0.408, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("Minnesota", 0.095, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("Mississippi", 0.999, "censored_boundary_>99.9", "Trump >99.9%"),
    TwoSeventyStateProbability("Missouri", 0.999, "censored_boundary_>99.9", "Trump >99.9%"),
    TwoSeventyStateProbability("Montana", 0.999, "censored_boundary_>99.9", "Trump >99.9%"),
    TwoSeventyStateProbability("Nebraska", 0.999, "censored_boundary_>99.9", "Trump >99.9%"),
    TwoSeventyStateProbability("Nevada", 0.523, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("New Hampshire", 0.130, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("New Jersey", 0.013, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("New Mexico", 0.063, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("New York", 0.001, "censored_boundary_>99.9", "Harris >99.9%"),
    TwoSeventyStateProbability("North Carolina", 0.650, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("North Dakota", 0.999, "censored_boundary_>99.9", "Trump >99.9%"),
    TwoSeventyStateProbability("Ohio", 0.953, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("Oklahoma", 0.999, "censored_boundary_>99.9", "Trump >99.9%"),
    TwoSeventyStateProbability("Oregon", 0.016, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("Pennsylvania", 0.520, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("Rhode Island", 0.001, "censored_boundary_>99.9", "Harris >99.9%"),
    TwoSeventyStateProbability("South Carolina", 0.999, "censored_boundary_>99.9", "Trump >99.9%"),
    TwoSeventyStateProbability("South Dakota", 0.999, "censored_boundary_>99.9", "Trump >99.9%"),
    TwoSeventyStateProbability("Tennessee", 0.999, "censored_boundary_>99.9", "Trump >99.9%"),
    TwoSeventyStateProbability("Texas", 0.938, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("Utah", 0.999, "censored_boundary_>99.9", "Trump >99.9%"),
    TwoSeventyStateProbability("Vermont", 0.001, "censored_boundary_>99.9", "Harris >99.9%"),
    TwoSeventyStateProbability("Virginia", 0.082, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("Washington", 0.001, "censored_boundary_>99.9", "Harris >99.9%"),
    TwoSeventyStateProbability("West Virginia", 0.999, "censored_boundary_>99.9", "Trump >99.9%"),
    TwoSeventyStateProbability("Wisconsin", 0.453, "exact_percent", "Results by State"),
    TwoSeventyStateProbability("Wyoming", 0.999, "censored_boundary_>99.9", "Trump >99.9%"),
)


def generate_h1_270towin_state_forecast_outputs(
    *,
    source: str = "mock",
    cases_output: Path = CASE_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
    forecast_timestamp_utc: str = FORECAST_TIMESTAMP_UTC,
    client: httpx.Client | None = None,
) -> H1TwoSeventyStateForecastResult:
    """Generate the 50-state 270toWin/JHK-vs-Polymarket H1 extension."""

    if source not in {"mock", "live"}:
        raise ValueError("source must be either 'mock' or 'live'")
    probability_specs = validate_two_seventy_probability_specs(
        TWO_SEVENTY_STATE_PROBABILITIES
    )
    forecast_ts = pd.Timestamp(forecast_timestamp_utc).tz_convert("UTC")
    own_client = client is None
    http_client = client or httpx.Client(timeout=25.0)
    try:
        rows = [
            build_270towin_state_case_row(
                spec=spec,
                source=source,
                forecast_ts=forecast_ts,
                client=http_client,
            )
            for spec in probability_specs
        ]
    finally:
        if own_client:
            http_client.close()

    cases = validate_270towin_state_cases(pd.DataFrame(rows, columns=CASE_COLUMNS))
    summary = build_270towin_state_summary(cases)
    cases_output.parent.mkdir(parents=True, exist_ok=True)
    cases.to_csv(cases_output, index=False)
    summary.to_csv(summary_output, index=False)
    write_270towin_state_forecast_figure(cases=cases, output_path=figure_output)
    metadata = build_270towin_state_metadata(
        source=source,
        cases=cases,
        summary=summary,
        cases_output=cases_output,
        summary_output=summary_output,
        figure_output=figure_output,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    values = _summary_values(summary)
    return H1TwoSeventyStateForecastResult(
        cases_path=cases_output,
        summary_path=summary_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        case_count=int(values["case_count"]),
        exact_probability_case_count=int(values["exact_probability_case_count"]),
        censored_boundary_case_count=int(values["censored_boundary_case_count"]),
        polymarket_lower_loss_count=int(values["polymarket_lower_loss_count"]),
        two_seventy_lower_loss_count=int(values["two_seventy_lower_loss_count"]),
        mean_polymarket_brier=float(values["mean_polymarket_brier"]),
        mean_two_seventy_brier=float(values["mean_two_seventy_brier"]),
    )


def validate_two_seventy_probability_specs(
    specs: Sequence[TwoSeventyStateProbability],
) -> tuple[TwoSeventyStateProbability, ...]:
    """Validate the curated 270toWin state probability constants."""

    if len(specs) != len(ALL_US_STATES):
        raise ValueError("270toWin probability specs must contain 50 states")
    states = [spec.state for spec in specs]
    if set(states) != set(ALL_US_STATES):
        raise ValueError("270toWin probability specs do not match the 50-state universe")
    if len(states) != len(set(states)):
        raise ValueError("270toWin probability specs contain duplicate states")
    for spec in specs:
        if not 0.0 <= spec.trump_probability <= 1.0:
            raise ValueError("270toWin probabilities must be in [0, 1]")
        if spec.probability_precision not in {
            "exact_percent",
            "censored_boundary_>99.9",
        }:
            raise ValueError(f"unexpected probability precision: {spec.probability_precision}")
    return tuple(sorted(specs, key=lambda item: item.state))


def build_270towin_state_case_row(
    *,
    spec: TwoSeventyStateProbability,
    source: str,
    forecast_ts: pd.Timestamp,
    client: httpx.Client,
) -> dict[str, Any]:
    """Build one state-level 270toWin/JHK comparison row."""

    market = (
        mock_gamma_market(spec.state)
        if source == "mock"
        else fetch_gamma_market_by_slug(client, POLYMARKET_STATE_MARKET_SLUGS[spec.state])
    )
    token_id = target_token_id(market, "Yes")
    price = (
        mock_price_point(spec.state, forecast_ts=forecast_ts)
        if source == "mock"
        else fetch_nearest_price(
            client,
            token_id=token_id,
            target_ts=forecast_ts,
            max_distance_seconds=MAX_PRICE_TIME_DISTANCE_SECONDS,
        )
    )
    pm_probability = float(price["price"])
    outcome = 1.0 if spec.state in REPUBLICAN_WON_2024_STATES else 0.0
    two_seventy_probability = float(spec.trump_probability)
    pm_brier = (pm_probability - outcome) ** 2
    two_seventy_brier = (two_seventy_probability - outcome) ** 2
    if pm_brier < two_seventy_brier:
        lower_loss_source = "polymarket"
    elif two_seventy_brier < pm_brier:
        lower_loss_source = "two_seventy_jhk_forecast"
    else:
        lower_loss_source = "tie"
    observed_ts = pd.Timestamp(price["observed_at_utc"]).tz_convert("UTC")
    market_slug = str(market.get("slug", ""))
    return {
        "case_id": f"us_2024_president_{_slugify_state(spec.state)}_270towin_republican",
        "state": spec.state,
        "forecast_date": FORECAST_DATE,
        "forecast_timestamp_utc": _format_timestamp(forecast_ts),
        "forecast_timestamp_precision": "date_morning_assumption_no_exact_source_time",
        "polymarket_observed_at_utc": _format_timestamp(observed_ts),
        "polymarket_time_distance_seconds": int(
            abs((observed_ts - forecast_ts).total_seconds())
        ),
        "polymarket_market_slug": market_slug,
        "polymarket_market_id": str(market.get("id", "")),
        "polymarket_condition_id": str(market.get("conditionId", "")),
        "target_outcome": "Republican wins state",
        "target_token_id": token_id,
        "outcome_value": outcome,
        "two_seventy_trump_win_probability": two_seventy_probability,
        "two_seventy_probability_precision": spec.probability_precision,
        "two_seventy_source_bucket": spec.source_bucket,
        "polymarket_probability": pm_probability,
        "polymarket_brier": pm_brier,
        "two_seventy_brier": two_seventy_brier,
        "loss_advantage": two_seventy_brier - pm_brier,
        "lower_loss_source": lower_loss_source,
        "two_seventy_source_url": TWO_SEVENTY_TO_WIN_BATTLEGROUND_URL,
        "two_seventy_simulation_source_url": TWO_SEVENTY_TO_WIN_SIMULATION_URL,
        "jhk_source_url": JHK_FORECAST_URL,
        "polymarket_source_url": f"https://polymarket.com/market/{market_slug}",
        "price_history_source_url": f"{CLOB_BASE_URL}/prices-history",
        "allowed_interpretation": (
            "Final state-level Brier comparison between Polymarket Republican-win "
            "prices and 270toWin/JHK Republican-win probabilities."
        ),
        "limitation": (
            "270toWin gives exact state probabilities for 22 states and censored "
            ">99.9% buckets for 28 states; the page date is Nov 5 but no exact "
            "publication timestamp is provided."
        ),
    }


def fetch_gamma_market_by_slug(client: httpx.Client, market_slug: str) -> dict[str, Any]:
    """Fetch one public Gamma market by slug."""

    response = client.get(
        f"{GAMMA_BASE_URL}/markets",
        params={"slug": market_slug, "closed": "true", "limit": 5},
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError("Gamma market response must be a list")
    for market in payload:
        if isinstance(market, dict) and str(market.get("slug", "")) == market_slug:
            return market
    raise ValueError(f"Gamma market slug not found: {market_slug}")


def validate_270towin_state_cases(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate generated 270toWin/JHK state forecast cases."""

    missing = [column for column in CASE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"270toWin state forecast cases missing columns: {missing}")
    forbidden = [column for column in frame.columns if "wallet" in column.lower()]
    if forbidden:
        raise ValueError(f"270toWin state cases must not contain wallet columns: {forbidden}")
    normalized = frame.loc[:, list(CASE_COLUMNS)].copy()
    for column in (
        "outcome_value",
        "two_seventy_trump_win_probability",
        "polymarket_probability",
        "polymarket_brier",
        "two_seventy_brier",
        "loss_advantage",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    for column in (
        "outcome_value",
        "two_seventy_trump_win_probability",
        "polymarket_probability",
    ):
        if not normalized[column].between(0.0, 1.0).all():
            raise ValueError(f"{column} values must be in [0, 1]")
    if len(normalized) != len(ALL_US_STATES):
        raise ValueError("270toWin state forecast cases must contain 50 state rows")
    if set(normalized["state"]) != set(ALL_US_STATES):
        raise ValueError("270toWin state forecast cases do not match the 50-state universe")
    if normalized["case_id"].duplicated().any():
        raise ValueError("270toWin state forecast case ids must be unique")
    precision_counts = normalized["two_seventy_probability_precision"].value_counts()
    if int(precision_counts.get("exact_percent", 0)) != 22:
        raise ValueError("270toWin exact probability case count must be 22")
    if int(precision_counts.get("censored_boundary_>99.9", 0)) != 28:
        raise ValueError("270toWin censored boundary case count must be 28")
    if (
        pd.to_numeric(
            normalized["polymarket_time_distance_seconds"],
            errors="raise",
        )
        > MAX_PRICE_TIME_DISTANCE_SECONDS
    ).any():
        raise ValueError("Polymarket price point is too far from forecast timestamp")
    return normalized.sort_values("state").reset_index(drop=True)


def build_270towin_state_summary(cases: pd.DataFrame) -> pd.DataFrame:
    """Build compact summary rows for the 270toWin/JHK extension."""

    exact = cases[cases["two_seventy_probability_precision"] == "exact_percent"]
    censored = cases[
        cases["two_seventy_probability_precision"] == "censored_boundary_>99.9"
    ]
    rows = [
        ("case_count", len(cases), "cases", "Resolved 50-state final forecast outcomes."),
        (
            "exact_probability_case_count",
            len(exact),
            "cases",
            "States with exact 270toWin percentages shown in the source table.",
        ),
        (
            "censored_boundary_case_count",
            len(censored),
            "cases",
            "States represented by source >99.9% buckets and boundary probabilities.",
        ),
        (
            "independent_resolved_outcome_count",
            len(cases),
            "outcomes",
            "Each row is a distinct 2024 presidential state outcome.",
        ),
        (
            "polymarket_lower_loss_count",
            int((cases["lower_loss_source"] == "polymarket").sum()),
            "cases",
            "Cases where Polymarket has lower Brier loss.",
        ),
        (
            "two_seventy_lower_loss_count",
            int((cases["lower_loss_source"] == "two_seventy_jhk_forecast").sum()),
            "cases",
            "Cases where 270toWin/JHK has lower Brier loss.",
        ),
        (
            "tie_count",
            int((cases["lower_loss_source"] == "tie").sum()),
            "cases",
            "Cases with equal Brier loss.",
        ),
        (
            "exact_probability_polymarket_lower_loss_count",
            int((exact["lower_loss_source"] == "polymarket").sum()),
            "cases",
            "Exact-probability states where Polymarket has lower Brier loss.",
        ),
        (
            "exact_probability_two_seventy_lower_loss_count",
            int((exact["lower_loss_source"] == "two_seventy_jhk_forecast").sum()),
            "cases",
            "Exact-probability states where 270toWin/JHK has lower Brier loss.",
        ),
        (
            "exact_probability_tie_count",
            int((exact["lower_loss_source"] == "tie").sum()),
            "cases",
            "Exact-probability states with equal Brier loss.",
        ),
        (
            "polymarket_better_share",
            float((cases["lower_loss_source"] == "polymarket").mean()),
            "share",
            "Share of all 50 states where Polymarket loss is lower.",
        ),
        (
            "mean_polymarket_brier",
            float(cases["polymarket_brier"].mean()),
            "brier_score",
            "Mean Brier loss across Polymarket state snapshots.",
        ),
        (
            "mean_two_seventy_brier",
            float(cases["two_seventy_brier"].mean()),
            "brier_score",
            "Mean Brier loss across 270toWin/JHK state probabilities.",
        ),
        (
            "mean_loss_advantage",
            float(cases["two_seventy_brier"].mean() - cases["polymarket_brier"].mean()),
            "brier_score",
            "Positive values mean lower mean Polymarket loss.",
        ),
        (
            "exact_probability_mean_polymarket_brier",
            float(exact["polymarket_brier"].mean()),
            "brier_score",
            "Mean Polymarket Brier loss on the 22 exact-probability states.",
        ),
        (
            "exact_probability_mean_two_seventy_brier",
            float(exact["two_seventy_brier"].mean()),
            "brier_score",
            "Mean 270toWin/JHK Brier loss on the 22 exact-probability states.",
        ),
        (
            "exact_probability_mean_loss_advantage",
            float(exact["two_seventy_brier"].mean() - exact["polymarket_brier"].mean()),
            "brier_score",
            "Positive values mean lower mean Polymarket loss on exact states.",
        ),
    ]
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def write_270towin_state_forecast_figure(
    *,
    cases: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write the 270toWin/JHK H1 extension figure."""

    exact = cases[cases["two_seventy_probability_precision"] == "exact_percent"]
    censored = cases[
        cases["two_seventy_probability_precision"] == "censored_boundary_>99.9"
    ]
    mean_rows = [
        ("Full 50\nPM", float(cases["polymarket_brier"].mean()), "#2563eb"),
        ("Full 50\n270/JHK", float(cases["two_seventy_brier"].mean()), "#7c3aed"),
        ("Exact 22\nPM", float(exact["polymarket_brier"].mean()), "#60a5fa"),
        ("Exact 22\n270/JHK", float(exact["two_seventy_brier"].mean()), "#a78bfa"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(14.2, 8.4))
    fig.suptitle(
        "H1 270toWin/JHK State Forecast Extension",
        fontsize=13.5,
        fontweight="bold",
    )

    axes[0, 0].bar(
        [row[0] for row in mean_rows],
        [row[1] for row in mean_rows],
        color=[row[2] for row in mean_rows],
    )
    axes[0, 0].set_ylabel("Mean Brier loss")
    axes[0, 0].set_title("Mean loss by source and probability precision")
    axes[0, 0].grid(True, axis="y", alpha=0.25)
    for idx, row in enumerate(mean_rows):
        axes[0, 0].text(idx, row[1] + 0.002, f"{row[1]:.4f}", ha="center", fontsize=8.5)

    groups = [("Exact 22", exact), ("Censored 28", censored), ("Full 50", cases)]
    x = range(len(groups))
    pm_counts = [int((frame["lower_loss_source"] == "polymarket").sum()) for _, frame in groups]
    comp_counts = [
        int((frame["lower_loss_source"] == "two_seventy_jhk_forecast").sum())
        for _, frame in groups
    ]
    tie_counts = [int((frame["lower_loss_source"] == "tie").sum()) for _, frame in groups]
    axes[0, 1].bar(x, pm_counts, label="Polymarket lower loss", color="#2563eb")
    axes[0, 1].bar(x, comp_counts, bottom=pm_counts, label="270/JHK lower loss", color="#7c3aed")
    axes[0, 1].bar(
        x,
        tie_counts,
        bottom=[a + b for a, b in zip(pm_counts, comp_counts, strict=True)],
        label="Tie",
        color="#9ca3af",
    )
    axes[0, 1].set_xticks(list(x), [label for label, _ in groups])
    axes[0, 1].set_ylabel("States")
    axes[0, 1].set_title("Head-to-head lower-loss counts")
    axes[0, 1].legend(fontsize=8, loc="upper left")
    axes[0, 1].grid(True, axis="y", alpha=0.25)

    colors = exact["outcome_value"].map({1.0: "#2563eb", 0.0: "#f59e0b"})
    axes[1, 0].scatter(
        exact["two_seventy_trump_win_probability"],
        exact["polymarket_probability"],
        c=colors,
        alpha=0.84,
        edgecolor="#111827",
        linewidth=0.35,
    )
    axes[1, 0].plot([0, 1], [0, 1], color="#6b7280", linestyle="--", linewidth=1.0)
    axes[1, 0].set_xlim(-0.03, 1.03)
    axes[1, 0].set_ylim(-0.03, 1.03)
    axes[1, 0].set_xlabel("270toWin/JHK Republican-win probability")
    axes[1, 0].set_ylabel("Polymarket Republican-win probability")
    axes[1, 0].set_title("Exact source probabilities only")
    axes[1, 0].grid(True, alpha=0.25)

    ordered = exact.sort_values("loss_advantage").reset_index(drop=True)
    y = range(len(ordered))
    axes[1, 1].barh(
        y,
        ordered["loss_advantage"],
        color=ordered["loss_advantage"].map(lambda value: "#2563eb" if value > 0 else "#7c3aed"),
    )
    axes[1, 1].set_yticks(list(y), ordered["state"], fontsize=7.5)
    axes[1, 1].axvline(0, color="#111827", linewidth=0.8)
    axes[1, 1].set_xlabel("270/JHK Brier minus Polymarket Brier")
    axes[1, 1].set_title("Exact-state loss advantage")
    axes[1, 1].grid(True, axis="x", alpha=0.25)

    fig.text(
        0.5,
        0.012,
        "The source gives exact probabilities for 22 states and >99.9% buckets for 28 states; bucket rows use conservative boundary values.",
        ha="center",
        fontsize=9,
        color="#374151",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return output_path


def build_270towin_state_metadata(
    *,
    source: str,
    cases: pd.DataFrame,
    summary: pd.DataFrame,
    cases_output: Path,
    summary_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for the 270toWin/JHK extension."""

    values = _summary_values(summary)
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_270towin_state_forecast_extension",
            "source": source,
            "traditional_forecast_source": "270toWin Battleground 270 / JHK Forecasts",
            "target_event": "Republican wins state",
            "forecast_date": FORECAST_DATE,
            "forecast_timestamp_utc": FORECAST_TIMESTAMP_UTC,
            "forecast_timestamp_precision": "date_morning_assumption_no_exact_source_time",
            "uses_curated_source_values": True,
            "censored_boundary_probability_rule": (
                "Harris >99.9% -> Trump probability 0.001; "
                "Trump >99.9% -> Trump probability 0.999"
            ),
            "uses_raw_poll_shares_directly": False,
            "rcp_included": False,
            "read_only_public_endpoints": source == "live",
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
        },
        "outputs": {
            "case_count": int(values["case_count"]),
            "independent_resolved_outcome_count": int(
                values["independent_resolved_outcome_count"]
            ),
            "exact_probability_case_count": int(values["exact_probability_case_count"]),
            "censored_boundary_case_count": int(values["censored_boundary_case_count"]),
            "polymarket_lower_loss_count": int(values["polymarket_lower_loss_count"]),
            "two_seventy_lower_loss_count": int(values["two_seventy_lower_loss_count"]),
            "exact_probability_polymarket_lower_loss_count": int(
                values["exact_probability_polymarket_lower_loss_count"]
            ),
            "exact_probability_two_seventy_lower_loss_count": int(
                values["exact_probability_two_seventy_lower_loss_count"]
            ),
            "polymarket_better_share": float(values["polymarket_better_share"]),
            "mean_polymarket_brier": float(values["mean_polymarket_brier"]),
            "mean_two_seventy_brier": float(values["mean_two_seventy_brier"]),
            "mean_loss_advantage": float(values["mean_loss_advantage"]),
            "exact_probability_mean_polymarket_brier": float(
                values["exact_probability_mean_polymarket_brier"]
            ),
            "exact_probability_mean_two_seventy_brier": float(
                values["exact_probability_mean_two_seventy_brier"]
            ),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
            "broad_many_cases_claim_supported_now": False,
        },
        "source_paths": {
            "cases": str(cases_output),
            "summary": str(summary_output),
            "figure": str(figure_output),
        },
        "source_urls": {
            "two_seventy_battleground": TWO_SEVENTY_TO_WIN_BATTLEGROUND_URL,
            "two_seventy_simulation": TWO_SEVENTY_TO_WIN_SIMULATION_URL,
            "jhk_forecast": JHK_FORECAST_URL,
            "gamma_markets": f"{GAMMA_BASE_URL}/markets",
            "clob_prices_history": f"{CLOB_BASE_URL}/prices-history",
        },
        "states": cases["state"].tolist(),
        "limitations": {
            "state_outcomes_share_one_election_context": True,
            "twenty_eight_source_probabilities_are_censored_boundaries": True,
            "source_page_has_date_but_no_exact_publication_timestamp": True,
            "not_raw_poll_comparison": True,
            "mean_loss_advantage_not_same_as_majority_of_states": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def mock_gamma_market(state: str) -> dict[str, Any]:
    """Return a Gamma-like fixture for one state market."""

    market_slug = POLYMARKET_STATE_MARKET_SLUGS[state]
    return {
        "id": f"market-{_slugify_state(state)}",
        "slug": market_slug,
        "conditionId": f"condition-{_slugify_state(state)}",
        "outcomes": json.dumps(["Yes", "No"]),
        "clobTokenIds": json.dumps(
            [f"token-{_slugify_state(state)}-yes", f"token-{_slugify_state(state)}-no"]
        ),
    }


def mock_price_point(state: str, *, forecast_ts: pd.Timestamp) -> dict[str, Any]:
    """Return deterministic mock Polymarket prices for tests."""

    outcome = 1.0 if state in REPUBLICAN_WON_2024_STATES else 0.0
    price = 0.86 if outcome == 1.0 else 0.14
    return {
        "observed_at_utc": _format_timestamp(forecast_ts + pd.Timedelta(seconds=2)),
        "price": price,
        "distance": 2,
    }


def _summary_values(summary: pd.DataFrame) -> dict[str, float]:
    return {
        str(row["summary_id"]): float(row["value"])
        for _, row in summary.iterrows()
    }


def _format_timestamp(value: pd.Timestamp | datetime) -> str:
    return pd.Timestamp(value).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def _slugify_state(state: str) -> str:
    return state.lower().replace(" ", "_")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("mock", "live"), default="mock")
    parser.add_argument("--cases-output", type=Path, default=CASE_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    parser.add_argument("--forecast-timestamp-utc", default=FORECAST_TIMESTAMP_UTC)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_270towin_state_forecast_outputs(
            source=args.source,
            cases_output=args.cases_output,
            summary_output=args.summary_output,
            figure_output=args.figure_output,
            metadata_output=args.metadata_output,
            forecast_timestamp_utc=args.forecast_timestamp_utc,
        )
    except (httpx.HTTPError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
