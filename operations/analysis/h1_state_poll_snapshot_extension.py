"""Build an H1 state-level poll-snapshot extension.

This module compares Polymarket state winner probabilities with a documented
poll-derived probability transformation for the 2024 presidential election.
It uses the preserved FiveThirtyEight polling-average snapshot from
2024-09-12, transforms Republican polling margins into Republican win
probabilities, and compares them with Polymarket Republican-win prices at the
same timestamp.

The transformation is intentionally explicit and deterministic. It is not RCP,
does not use raw poll shares directly as probabilities, and does not fit the
error scale to 2024 outcomes.
"""
from __future__ import annotations

import argparse
import io
import json
import math
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

from operations.analysis.run_h2_event_windows import RESULTS_DIR


GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
CLOB_BASE_URL = "https://clob.polymarket.com"
FIVETHIRTYEIGHT_POLL_AVERAGES_URL = (
    "https://raw.githubusercontent.com/fivethirtyeight/data/master/"
    "polls/2024-averages/presidential_general_averages_2024-09-12_uncorrected.csv"
)
FIVETHIRTYEIGHT_POLL_ERROR_SOURCE_URL = (
    "https://abcnews.com/538/538s-final-forecasts-2024-election/story?id=115511051"
)

SNAPSHOT_DATE = "2024-09-12"
SNAPSHOT_TIMESTAMP_UTC = "2024-09-12T12:00:00Z"
POLL_ERROR_MAE_POINTS = 3.8
POLL_ERROR_MAE_SENSITIVITY_POINTS: tuple[float, ...] = (
    2.0,
    2.5,
    3.0,
    3.5,
    3.8,
    4.0,
    4.5,
    5.0,
    6.0,
    7.0,
    8.0,
    10.0,
)
MAX_PRICE_TIME_DISTANCE_SECONDS = 2 * 60 * 60

CASE_OUTPUT = RESULTS_DIR / "h1_state_poll_snapshot_cases.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_state_poll_snapshot_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_state_poll_snapshot.png"
SENSITIVITY_OUTPUT = RESULTS_DIR / "h1_state_poll_snapshot_sensitivity.csv"
SENSITIVITY_FIGURE_OUTPUT = RESULTS_DIR / "h1_state_poll_snapshot_sensitivity.png"
COVERAGE_OUTPUT = RESULTS_DIR / "h1_state_poll_snapshot_coverage.csv"
COVERAGE_FIGURE_OUTPUT = RESULTS_DIR / "h1_state_poll_snapshot_coverage.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_state_poll_snapshot_metadata.json"

CASE_COLUMNS: tuple[str, ...] = (
    "case_id",
    "state",
    "forecast_timestamp_utc",
    "polymarket_observed_at_utc",
    "polymarket_time_distance_seconds",
    "polymarket_event_slug",
    "polymarket_market_slug",
    "polymarket_market_id",
    "polymarket_condition_id",
    "target_outcome",
    "target_token_id",
    "outcome_value",
    "poll_snapshot_date",
    "poll_republican_pct",
    "poll_democratic_pct",
    "poll_margin_republican_minus_democratic",
    "poll_error_mae_points",
    "poll_error_sigma_points",
    "poll_transform_name",
    "poll_derived_probability",
    "polymarket_probability",
    "polymarket_brier",
    "poll_derived_brier",
    "loss_advantage",
    "lower_loss_source",
    "poll_average_source_url",
    "poll_error_source_url",
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

SENSITIVITY_COLUMNS: tuple[str, ...] = (
    "poll_error_mae_points",
    "poll_error_sigma_points",
    "case_count",
    "polymarket_lower_loss_count",
    "poll_derived_lower_loss_count",
    "tie_count",
    "polymarket_better_share",
    "mean_polymarket_brier",
    "mean_poll_derived_brier",
    "mean_loss_advantage",
)

COVERAGE_COLUMNS: tuple[str, ...] = (
    "state",
    "polymarket_event_slug",
    "polymarket_market_slug",
    "polymarket_market_available",
    "poll_snapshot_has_rep_dem",
    "included_in_brier_comparison",
    "outcome_value",
    "coverage_status",
    "exclusion_reason",
)

ALL_US_STATES: tuple[str, ...] = (
    "Alabama",
    "Alaska",
    "Arizona",
    "Arkansas",
    "California",
    "Colorado",
    "Connecticut",
    "Delaware",
    "Florida",
    "Georgia",
    "Hawaii",
    "Idaho",
    "Illinois",
    "Indiana",
    "Iowa",
    "Kansas",
    "Kentucky",
    "Louisiana",
    "Maine",
    "Maryland",
    "Massachusetts",
    "Michigan",
    "Minnesota",
    "Mississippi",
    "Missouri",
    "Montana",
    "Nebraska",
    "Nevada",
    "New Hampshire",
    "New Jersey",
    "New Mexico",
    "New York",
    "North Carolina",
    "North Dakota",
    "Ohio",
    "Oklahoma",
    "Oregon",
    "Pennsylvania",
    "Rhode Island",
    "South Carolina",
    "South Dakota",
    "Tennessee",
    "Texas",
    "Utah",
    "Vermont",
    "Virginia",
    "Washington",
    "West Virginia",
    "Wisconsin",
    "Wyoming",
)

REPUBLICAN_WON_2024_STATES: frozenset[str] = frozenset(
    {
        "Alabama",
        "Alaska",
        "Arizona",
        "Arkansas",
        "Florida",
        "Georgia",
        "Idaho",
        "Indiana",
        "Iowa",
        "Kansas",
        "Kentucky",
        "Louisiana",
        "Michigan",
        "Mississippi",
        "Missouri",
        "Montana",
        "Nebraska",
        "Nevada",
        "North Carolina",
        "North Dakota",
        "Ohio",
        "Oklahoma",
        "Pennsylvania",
        "South Carolina",
        "South Dakota",
        "Tennessee",
        "Texas",
        "Utah",
        "West Virginia",
        "Wisconsin",
        "Wyoming",
    }
)

POLYMARKET_STATE_MARKET_SLUGS: dict[str, str] = {
    "Alabama": "will-a-republican-win-alabama-in-the-2024-us-presidential-election",
    "Alaska": "will-a-republican-win-alaska-in-the-2024-us-presidential-election",
    "Arizona": "will-a-republican-win-arizona-presidential-election",
    "Arkansas": "will-a-republican-win-arkansas-in-the-2024-us-presidential-election",
    "California": "will-a-republican-win-california-in-the-2024-us-presidential-election",
    "Colorado": "will-a-republican-win-colorado-in-the-2024-us-presidential-election",
    "Connecticut": "will-a-republican-win-connecticut-in-the-2024-us-presidential-election",
    "Delaware": "will-a-republican-win-delaware-presidential-election",
    "Florida": "will-a-republican-win-florida-in-the-2024-us-presidential-election",
    "Georgia": "will-a-republican-win-georgia-presidential-election",
    "Hawaii": "will-a-republican-win-hawaii-in-the-2024-us-presidential-election",
    "Idaho": "will-a-republican-win-idaho-in-the-2024-us-presidential-election",
    "Illinois": "will-a-republican-win-illinois-in-the-2024-us-presidential-election",
    "Indiana": "will-a-republican-win-indiana-in-the-2024-us-presidential-election",
    "Iowa": "will-a-republican-win-iowa-in-the-2024-us-presidential-election",
    "Kansas": "will-a-republican-win-kansas-in-the-2024-us-presidential-election",
    "Kentucky": "will-a-republican-win-kentucky-in-the-2024-us-presidential-election",
    "Louisiana": "will-a-republican-win-louisiana-in-the-2024-us-presidential-election",
    "Maine": "will-a-republican-win-maine-in-the-2024-us-presidential-election",
    "Maryland": "will-a-republican-win-maryland-in-the-2024-us-presidential-election",
    "Massachusetts": "will-a-republican-win-massachusetts-in-the-2024-us-presidential-election",
    "Michigan": "will-a-republican-win-michigan-presidential-election",
    "Minnesota": "will-a-republican-win-minnesota-in-the-2024-us-presidential-election",
    "Mississippi": "will-a-republican-win-mississippi-in-the-2024-us-presidential-election",
    "Missouri": "will-a-republican-win-missouri-in-the-2024-us-presidential-election",
    "Montana": "will-a-republican-win-montana-in-the-2024-us-presidential-election",
    "Nebraska": "will-a-republican-win-nebraska-in-the-2024-us-presidential-election",
    "Nevada": "will-a-republican-win-nevada-presidential-election",
    "New Hampshire": "will-a-republican-win-new-hampshire-in-the-2024-us-presidential-election",
    "New Jersey": "will-a-republican-win-new-jersey-in-the-2024-us-presidential-election",
    "New Mexico": "will-a-republican-win-new-mexico-presidential-election",
    "New York": "will-a-republican-win-new-york-presidential-election",
    "North Carolina": "will-a-republican-win-north-carolina-presidential-election",
    "North Dakota": "will-a-republican-win-north-dakota-in-the-2024-us-presidential-election",
    "Ohio": "will-a-republican-win-ohio-in-the-2024-us-presidential-election-2024",
    "Oklahoma": "will-a-republican-win-oklahoma-in-the-2024-us-presidential-election",
    "Oregon": "will-a-republican-win-oregon-in-the-2024-us-presidential-election",
    "Pennsylvania": "will-a-republican-win-pennsylvania-presidential-election",
    "Rhode Island": "will-a-republican-win-rhode-island-in-the-2024-us-presidential-election",
    "South Carolina": "will-a-republican-win-south-carolina-in-the-2024-us-presidential-election",
    "South Dakota": "will-a-republican-win-south-dakota-in-the-2024-us-presidential-election",
    "Tennessee": "will-a-republican-win-tennessee-in-the-2024-us-presidential-election",
    "Texas": "will-a-republican-win-texas-in-the-2024-us-presidential-election",
    "Utah": "will-a-republican-win-utah-in-the-2024-us-presidential-election",
    "Vermont": "will-a-republican-win-vermont-in-the-2024-us-presidential-election",
    "Virginia": "will-a-republican-win-virginia-in-the-2024-us-presidential-election",
    "Washington": "will-a-reoublican-win-washington-in-the-2024-us-presidential-election",
    "West Virginia": "will-a-republican-win-west-virginia-in-the-2024-us-presidential-election",
    "Wisconsin": "will-a-republican-win-wisconsin-presidential-election",
    "Wyoming": "will-a-republican-win-wyoming-in-the-2024-us-presidential-election",
}


@dataclass(frozen=True)
class StatePollSnapshotCaseSpec:
    """One state-level Republican-win comparison case."""

    state: str
    event_slug: str
    market_slug: str
    outcome_value: float

    @property
    def case_id(self) -> str:
        return f"us_2024_president_{_slugify_state(self.state)}_republican"


@dataclass(frozen=True)
class H1StatePollSnapshotResult:
    """Summary of generated state-poll H1 artifacts."""

    cases_path: Path
    summary_path: Path
    figure_path: Path
    sensitivity_path: Path
    sensitivity_figure_path: Path
    coverage_path: Path
    coverage_figure_path: Path
    metadata_path: Path
    case_count: int
    polymarket_lower_loss_count: int
    poll_derived_lower_loss_count: int
    mean_polymarket_brier: float
    mean_poll_derived_brier: float

    def to_dict(self) -> dict[str, float | int | str]:
        """Return a JSON-friendly summary."""

        return {
            "cases_path": str(self.cases_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "sensitivity_path": str(self.sensitivity_path),
            "sensitivity_figure_path": str(self.sensitivity_figure_path),
            "coverage_path": str(self.coverage_path),
            "coverage_figure_path": str(self.coverage_figure_path),
            "metadata_path": str(self.metadata_path),
            "case_count": self.case_count,
            "polymarket_lower_loss_count": self.polymarket_lower_loss_count,
            "poll_derived_lower_loss_count": self.poll_derived_lower_loss_count,
            "mean_polymarket_brier": self.mean_polymarket_brier,
            "mean_poll_derived_brier": self.mean_poll_derived_brier,
        }


STATE_POLL_SNAPSHOT_CASES: tuple[StatePollSnapshotCaseSpec, ...] = (
    StatePollSnapshotCaseSpec(
        state="Arizona",
        event_slug="arizona-presidential-election-winner",
        market_slug="will-a-republican-win-arizona-presidential-election",
        outcome_value=1.0,
    ),
    StatePollSnapshotCaseSpec(
        state="California",
        event_slug="california-presidential-election-winner",
        market_slug="will-a-republican-win-california-in-the-2024-us-presidential-election",
        outcome_value=0.0,
    ),
    StatePollSnapshotCaseSpec(
        state="Florida",
        event_slug="florida-presidential-election-winner",
        market_slug="will-a-republican-win-florida-in-the-2024-us-presidential-election",
        outcome_value=1.0,
    ),
    StatePollSnapshotCaseSpec(
        state="Georgia",
        event_slug="georgia-presidential-election-winner",
        market_slug="will-a-republican-win-georgia-presidential-election",
        outcome_value=1.0,
    ),
    StatePollSnapshotCaseSpec(
        state="Michigan",
        event_slug="michigan-presidential-election-winner",
        market_slug="will-a-republican-win-michigan-presidential-election",
        outcome_value=1.0,
    ),
    StatePollSnapshotCaseSpec(
        state="Minnesota",
        event_slug="minnesota-presidential-election-winner",
        market_slug="will-a-republican-win-minnesota-in-the-2024-us-presidential-election",
        outcome_value=0.0,
    ),
    StatePollSnapshotCaseSpec(
        state="Nevada",
        event_slug="nevada-presidential-election-winner",
        market_slug="will-a-republican-win-nevada-presidential-election",
        outcome_value=1.0,
    ),
    StatePollSnapshotCaseSpec(
        state="New Hampshire",
        event_slug="new-hampshire-presidential-election-winner",
        market_slug="will-a-republican-win-new-hampshire-in-the-2024-us-presidential-election",
        outcome_value=0.0,
    ),
    StatePollSnapshotCaseSpec(
        state="North Carolina",
        event_slug="north-carolina-presidential-election-winner",
        market_slug="will-a-republican-win-north-carolina-presidential-election",
        outcome_value=1.0,
    ),
    StatePollSnapshotCaseSpec(
        state="Ohio",
        event_slug="ohio-presidential-election-winner",
        market_slug="will-a-republican-win-ohio-in-the-2024-us-presidential-election-2024",
        outcome_value=1.0,
    ),
    StatePollSnapshotCaseSpec(
        state="Pennsylvania",
        event_slug="pennsylvania-presidential-election-winner",
        market_slug="will-a-republican-win-pennsylvania-presidential-election",
        outcome_value=1.0,
    ),
    StatePollSnapshotCaseSpec(
        state="Texas",
        event_slug="texas-presidential-election-winner",
        market_slug="will-a-republican-win-texas-in-the-2024-us-presidential-election",
        outcome_value=1.0,
    ),
    StatePollSnapshotCaseSpec(
        state="Wisconsin",
        event_slug="wisconsin-presidential-election-winner",
        market_slug="will-a-republican-win-wisconsin-presidential-election",
        outcome_value=1.0,
    ),
)


def generate_h1_state_poll_snapshot_outputs(
    *,
    source: str = "mock",
    cases_output: Path = CASE_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    sensitivity_output: Path = SENSITIVITY_OUTPUT,
    sensitivity_figure_output: Path = SENSITIVITY_FIGURE_OUTPUT,
    coverage_output: Path = COVERAGE_OUTPUT,
    coverage_figure_output: Path = COVERAGE_FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
    snapshot_timestamp_utc: str = SNAPSHOT_TIMESTAMP_UTC,
    client: httpx.Client | None = None,
) -> H1StatePollSnapshotResult:
    """Generate H1 state-poll snapshot cases, summary, figure, and metadata."""

    if source not in {"mock", "live"}:
        raise ValueError("source must be either 'mock' or 'live'")
    snapshot_ts = pd.Timestamp(snapshot_timestamp_utc).tz_convert("UTC")
    own_client = client is None
    http_client = client or httpx.Client(timeout=25.0)
    try:
        poll_rows = (
            mock_poll_average_rows()
            if source == "mock"
            else fetch_poll_average_rows(http_client)
        )
        poll_frame = parse_poll_average_snapshot(poll_rows)
        rows = [
            build_state_case_row(
                spec,
                source=source,
                poll_frame=poll_frame,
                snapshot_ts=snapshot_ts,
                client=http_client,
            )
            for spec in STATE_POLL_SNAPSHOT_CASES
        ]
    finally:
        if own_client:
            http_client.close()

    cases = validate_state_cases(pd.DataFrame(rows, columns=CASE_COLUMNS))
    summary = build_state_summary(cases)
    sensitivity = build_poll_transform_sensitivity(cases)
    coverage = build_state_coverage_audit(poll_frame=poll_frame)
    cases_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    sensitivity_output.parent.mkdir(parents=True, exist_ok=True)
    coverage_output.parent.mkdir(parents=True, exist_ok=True)
    cases.to_csv(cases_output, index=False)
    summary.to_csv(summary_output, index=False)
    sensitivity.to_csv(sensitivity_output, index=False)
    coverage.to_csv(coverage_output, index=False)
    write_state_poll_snapshot_figure(cases=cases, output_path=figure_output)
    write_poll_transform_sensitivity_figure(
        sensitivity=sensitivity,
        output_path=sensitivity_figure_output,
    )
    write_state_coverage_figure(coverage=coverage, output_path=coverage_figure_output)
    metadata = build_state_metadata(
        source=source,
        cases=cases,
        summary=summary,
        sensitivity=sensitivity,
        coverage=coverage,
        cases_output=cases_output,
        summary_output=summary_output,
        figure_output=figure_output,
        sensitivity_output=sensitivity_output,
        sensitivity_figure_output=sensitivity_figure_output,
        coverage_output=coverage_output,
        coverage_figure_output=coverage_figure_output,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    values = _summary_values(summary)
    return H1StatePollSnapshotResult(
        cases_path=cases_output,
        summary_path=summary_output,
        figure_path=figure_output,
        sensitivity_path=sensitivity_output,
        sensitivity_figure_path=sensitivity_figure_output,
        coverage_path=coverage_output,
        coverage_figure_path=coverage_figure_output,
        metadata_path=metadata_output,
        case_count=int(values["case_count"]),
        polymarket_lower_loss_count=int(values["polymarket_lower_loss_count"]),
        poll_derived_lower_loss_count=int(values["poll_derived_lower_loss_count"]),
        mean_polymarket_brier=float(values["mean_polymarket_brier"]),
        mean_poll_derived_brier=float(values["mean_poll_derived_brier"]),
    )


def fetch_poll_average_rows(client: httpx.Client) -> list[dict[str, Any]]:
    """Fetch official preserved FiveThirtyEight polling-average rows."""

    response = client.get(FIVETHIRTYEIGHT_POLL_AVERAGES_URL)
    response.raise_for_status()
    text = response.text
    if not text.lstrip().startswith("candidate,date,"):
        raise ValueError("538 polling-average response is not the expected CSV")
    return pd.read_csv(io.StringIO(text)).to_dict(orient="records")


def parse_poll_average_snapshot(rows: Sequence[dict[str, Any]]) -> pd.DataFrame:
    """Return validated 2024-09-12 Republican/Democratic polling rows."""

    frame = pd.DataFrame(rows)
    required = {"candidate", "date", "state", "cycle", "party", "pct_estimate"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"poll-average rows missing columns: {sorted(missing)}")
    filtered = frame.loc[
        (frame["cycle"].astype(int) == 2024)
        & (frame["date"].astype(str) == SNAPSHOT_DATE)
        & (frame["party"].astype(str).isin(["REP", "DEM"]))
    ].copy()
    expected_states = {spec.state for spec in STATE_POLL_SNAPSHOT_CASES}
    present_states = set(filtered["state"].astype(str))
    missing_states = sorted(expected_states - present_states)
    if missing_states:
        raise ValueError(f"poll-average snapshot missing states: {missing_states}")
    filtered["pct_estimate"] = pd.to_numeric(filtered["pct_estimate"], errors="raise")
    if not filtered["pct_estimate"].between(0.0, 100.0).all():
        raise ValueError("poll pct_estimate values must be percentages in [0, 100]")
    return filtered.reset_index(drop=True)


def build_state_case_row(
    spec: StatePollSnapshotCaseSpec,
    *,
    source: str,
    poll_frame: pd.DataFrame,
    snapshot_ts: pd.Timestamp,
    client: httpx.Client,
) -> dict[str, Any]:
    """Build one state-level poll-derived comparison row."""

    poll = poll_probability_for_state(poll_frame, spec.state)
    event = mock_gamma_event(spec) if source == "mock" else fetch_gamma_event(client, spec.event_slug)
    market = select_market(event, spec.market_slug)
    token_id = target_token_id(market, "Yes")
    price = (
        mock_price_point(spec, snapshot_ts=snapshot_ts)
        if source == "mock"
        else fetch_nearest_price(
            client,
            token_id=token_id,
            target_ts=snapshot_ts,
            max_distance_seconds=MAX_PRICE_TIME_DISTANCE_SECONDS,
        )
    )

    pm_probability = float(price["price"])
    poll_probability = float(poll["poll_derived_probability"])
    outcome = float(spec.outcome_value)
    pm_brier = (pm_probability - outcome) ** 2
    poll_brier = (poll_probability - outcome) ** 2
    if pm_brier < poll_brier:
        lower_loss_source = "polymarket"
    elif poll_brier < pm_brier:
        lower_loss_source = "poll_derived_forecast"
    else:
        lower_loss_source = "tie"

    observed_ts = pd.Timestamp(price["observed_at_utc"]).tz_convert("UTC")
    return {
        "case_id": spec.case_id,
        "state": spec.state,
        "forecast_timestamp_utc": _format_timestamp(snapshot_ts),
        "polymarket_observed_at_utc": _format_timestamp(observed_ts),
        "polymarket_time_distance_seconds": int(
            abs((observed_ts - snapshot_ts).total_seconds())
        ),
        "polymarket_event_slug": spec.event_slug,
        "polymarket_market_slug": str(market.get("slug", "")),
        "polymarket_market_id": str(market.get("id", "")),
        "polymarket_condition_id": str(market.get("conditionId", "")),
        "target_outcome": "Republican wins state",
        "target_token_id": token_id,
        "outcome_value": outcome,
        "poll_snapshot_date": SNAPSHOT_DATE,
        "poll_republican_pct": float(poll["republican_pct"]),
        "poll_democratic_pct": float(poll["democratic_pct"]),
        "poll_margin_republican_minus_democratic": float(poll["margin"]),
        "poll_error_mae_points": POLL_ERROR_MAE_POINTS,
        "poll_error_sigma_points": poll_error_sigma_points(),
        "poll_transform_name": "normal_margin_error_from_538_poll_mae",
        "poll_derived_probability": poll_probability,
        "polymarket_probability": pm_probability,
        "polymarket_brier": pm_brier,
        "poll_derived_brier": poll_brier,
        "loss_advantage": poll_brier - pm_brier,
        "lower_loss_source": lower_loss_source,
        "poll_average_source_url": FIVETHIRTYEIGHT_POLL_AVERAGES_URL,
        "poll_error_source_url": FIVETHIRTYEIGHT_POLL_ERROR_SOURCE_URL,
        "polymarket_source_url": f"https://polymarket.com/event/{spec.event_slug}",
        "price_history_source_url": f"{CLOB_BASE_URL}/prices-history",
        "allowed_interpretation": (
            "State-level Brier comparison between Polymarket Republican-win "
            "prices and a documented poll-derived Republican-win probability."
        ),
        "limitation": (
            "The poll-derived probability is a transparent transformation of "
            "538 polling averages, not an official 538 state win forecast and "
            "not raw poll shares."
        ),
    }


def poll_probability_for_state(frame: pd.DataFrame, state: str) -> dict[str, float]:
    """Transform a Republican polling margin into a win probability."""

    state_rows = frame.loc[frame["state"].astype(str) == state]
    rep = state_rows.loc[state_rows["party"] == "REP", "pct_estimate"]
    dem = state_rows.loc[state_rows["party"] == "DEM", "pct_estimate"]
    if rep.empty or dem.empty:
        raise ValueError(f"poll snapshot missing REP/DEM rows for {state}")
    republican_pct = float(rep.iloc[0])
    democratic_pct = float(dem.iloc[0])
    margin = republican_pct - democratic_pct
    probability = transformed_margin_probability(margin)
    return {
        "republican_pct": republican_pct,
        "democratic_pct": democratic_pct,
        "margin": margin,
        "poll_derived_probability": probability,
    }


def transformed_margin_probability(
    margin_points: float,
    *,
    mae_points: float = POLL_ERROR_MAE_POINTS,
) -> float:
    """Transform a Republican polling margin into a Republican-win probability."""

    return normal_cdf(margin_points / poll_error_sigma_points(mae_points))


def poll_error_sigma_points(mae_points: float = POLL_ERROR_MAE_POINTS) -> float:
    """Convert an expected absolute normal error into a normal sigma."""

    if mae_points <= 0:
        raise ValueError("mae_points must be positive")
    return mae_points / math.sqrt(2.0 / math.pi)


def normal_cdf(value: float) -> float:
    """Standard normal cumulative distribution function."""

    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def fetch_gamma_event(client: httpx.Client, event_slug: str) -> dict[str, Any]:
    """Fetch one public Gamma event by slug."""

    response = client.get(f"{GAMMA_BASE_URL}/events", params={"slug": event_slug})
    response.raise_for_status()
    payload = response.json()
    event = payload[0] if isinstance(payload, list) and payload else payload
    if not isinstance(event, dict):
        raise ValueError(f"Gamma event response for {event_slug!r} is not an object")
    return event


def select_market(event: dict[str, Any], market_slug: str) -> dict[str, Any]:
    """Select the target Republican-wins market from a Gamma event payload."""

    markets = event.get("markets")
    if not isinstance(markets, list):
        raise ValueError("Gamma event response must contain a markets list")
    for market in markets:
        if isinstance(market, dict) and str(market.get("slug", "")) == market_slug:
            return market
    raise ValueError(f"Market slug not found in Gamma event: {market_slug}")


def target_token_id(market: dict[str, Any], target_outcome: str) -> str:
    """Return the CLOB token ID for a target outcome label."""

    outcomes = _parse_json_list(market.get("outcomes"))
    tokens = _parse_json_list(market.get("clobTokenIds"))
    for idx, outcome in enumerate(outcomes):
        if outcome.strip().lower() == target_outcome.strip().lower():
            if idx >= len(tokens):
                raise ValueError("Gamma market is missing target CLOB token id")
            token = str(tokens[idx]).strip()
            if not token:
                raise ValueError("target token id must not be blank")
            return token
    raise ValueError(f"Target outcome not found: {target_outcome}")


def fetch_nearest_price(
    client: httpx.Client,
    *,
    token_id: str,
    target_ts: pd.Timestamp,
    max_distance_seconds: int,
) -> dict[str, Any]:
    """Fetch CLOB price history and return the nearest point to target_ts."""

    start_ts = target_ts - pd.Timedelta(seconds=max_distance_seconds)
    end_ts = target_ts + pd.Timedelta(seconds=max_distance_seconds)
    response = client.get(
        f"{CLOB_BASE_URL}/prices-history",
        params={
            "market": token_id,
            "startTs": int(start_ts.timestamp()),
            "endTs": int(end_ts.timestamp()),
            "fidelity": 60,
        },
    )
    response.raise_for_status()
    payload = response.json()
    history = payload.get("history") if isinstance(payload, dict) else None
    if not isinstance(history, list) or not history:
        raise ValueError(f"No CLOB price history returned for token {token_id}")

    candidates: list[dict[str, Any]] = []
    for point in history:
        if not isinstance(point, dict):
            continue
        timestamp_value = point.get("t", point.get("timestamp"))
        price_value = point.get("p", point.get("price"))
        if timestamp_value is None or price_value is None:
            continue
        observed_ts = _history_timestamp(timestamp_value)
        price = float(price_value)
        distance = abs((observed_ts - target_ts).total_seconds())
        if distance <= max_distance_seconds:
            candidates.append(
                {
                    "observed_at_utc": _format_timestamp(observed_ts),
                    "price": price,
                    "distance": distance,
                }
            )
    if not candidates:
        raise ValueError("No CLOB history point was close enough to snapshot timestamp")
    candidates.sort(key=lambda item: (float(item["distance"]), str(item["observed_at_utc"])))
    return candidates[0]


def validate_state_cases(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate state-level poll snapshot comparison rows."""

    missing = [column for column in CASE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"state poll snapshot cases missing required columns: {missing}")
    forbidden = [column for column in frame.columns if "wallet" in column.lower()]
    if forbidden:
        raise ValueError(f"state poll snapshot cases must not contain wallet columns: {forbidden}")
    normalized = frame.loc[:, list(CASE_COLUMNS)].copy()
    for column in (
        "outcome_value",
        "poll_republican_pct",
        "poll_democratic_pct",
        "poll_margin_republican_minus_democratic",
        "poll_error_mae_points",
        "poll_error_sigma_points",
        "poll_derived_probability",
        "polymarket_probability",
        "polymarket_brier",
        "poll_derived_brier",
        "loss_advantage",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    for column in ("outcome_value", "poll_derived_probability", "polymarket_probability"):
        if not normalized[column].between(0.0, 1.0).all():
            raise ValueError(f"{column} values must be in [0, 1]")
    for column in ("poll_republican_pct", "poll_democratic_pct"):
        if not normalized[column].between(0.0, 100.0).all():
            raise ValueError(f"{column} values must be percentages in [0, 100]")
    if (normalized["polymarket_brier"] < 0).any() or (
        normalized["poll_derived_brier"] < 0
    ).any():
        raise ValueError("Brier values must be non-negative")
    if (
        pd.to_numeric(
            normalized["polymarket_time_distance_seconds"],
            errors="raise",
        )
        > MAX_PRICE_TIME_DISTANCE_SECONDS
    ).any():
        raise ValueError("Polymarket price point is too far from snapshot timestamp")
    if normalized["case_id"].duplicated().any():
        raise ValueError("case_id values must be unique")
    if set(normalized["state"]) != {spec.state for spec in STATE_POLL_SNAPSHOT_CASES}:
        raise ValueError("state cases do not match the curated case set")
    for column in (
        "case_id",
        "state",
        "forecast_timestamp_utc",
        "polymarket_observed_at_utc",
        "target_outcome",
        "target_token_id",
        "poll_transform_name",
        "poll_average_source_url",
    ):
        if normalized[column].fillna("").astype(str).str.strip().eq("").any():
            raise ValueError(f"{column} must not be blank")
    return normalized.sort_values("state").reset_index(drop=True)


def build_state_summary(cases: pd.DataFrame) -> pd.DataFrame:
    """Build compact state-poll snapshot summary rows."""

    pm_lower = int((cases["lower_loss_source"] == "polymarket").sum())
    poll_lower = int((cases["lower_loss_source"] == "poll_derived_forecast").sum())
    ties = int((cases["lower_loss_source"] == "tie").sum())
    mean_pm = float(cases["polymarket_brier"].mean())
    mean_poll = float(cases["poll_derived_brier"].mean())
    rows = [
        ("case_count", len(cases), "cases", "Curated resolved state-level poll-snapshot outcomes."),
        (
            "independent_resolved_outcome_count",
            len(cases),
            "outcomes",
            "Each row is a distinct 2024 presidential state outcome.",
        ),
        (
            "polymarket_lower_loss_count",
            pm_lower,
            "cases",
            "Cases where Polymarket has lower Brier loss.",
        ),
        (
            "poll_derived_lower_loss_count",
            poll_lower,
            "cases",
            "Cases where the poll-derived probability has lower Brier loss.",
        ),
        ("tie_count", ties, "cases", "Cases with equal Brier loss."),
        (
            "polymarket_better_share",
            pm_lower / len(cases) if len(cases) else 0.0,
            "share",
            "Share of state cases where Polymarket loss is lower.",
        ),
        (
            "mean_polymarket_brier",
            mean_pm,
            "brier_score",
            "Mean Brier loss across Polymarket state snapshots.",
        ),
        (
            "mean_poll_derived_brier",
            mean_poll,
            "brier_score",
            "Mean Brier loss across transformed 538 poll-average probabilities.",
        ),
        (
            "mean_loss_advantage",
            mean_poll - mean_pm,
            "brier_score",
            "Positive values mean lower mean Polymarket loss.",
        ),
    ]
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def build_poll_transform_sensitivity(
    cases: pd.DataFrame,
    *,
    mae_values: Sequence[float] = POLL_ERROR_MAE_SENSITIVITY_POINTS,
) -> pd.DataFrame:
    """Evaluate the poll transform over a fixed error-assumption grid."""

    rows: list[dict[str, float | int]] = []
    for mae in mae_values:
        sigma = poll_error_sigma_points(float(mae))
        poll_probabilities = [
            transformed_margin_probability(float(margin), mae_points=float(mae))
            for margin in cases["poll_margin_republican_minus_democratic"]
        ]
        outcomes = cases["outcome_value"].astype(float).tolist()
        poll_brier = [
            (probability - outcome) ** 2
            for probability, outcome in zip(poll_probabilities, outcomes, strict=True)
        ]
        pm_brier = cases["polymarket_brier"].astype(float).tolist()
        pm_lower = sum(1 for pm, poll in zip(pm_brier, poll_brier, strict=True) if pm < poll)
        poll_lower = sum(1 for pm, poll in zip(pm_brier, poll_brier, strict=True) if poll < pm)
        ties = len(pm_brier) - pm_lower - poll_lower
        mean_pm = float(sum(pm_brier) / len(pm_brier))
        mean_poll = float(sum(poll_brier) / len(poll_brier))
        rows.append(
            {
                "poll_error_mae_points": float(mae),
                "poll_error_sigma_points": sigma,
                "case_count": len(cases),
                "polymarket_lower_loss_count": pm_lower,
                "poll_derived_lower_loss_count": poll_lower,
                "tie_count": ties,
                "polymarket_better_share": pm_lower / len(cases) if len(cases) else 0.0,
                "mean_polymarket_brier": mean_pm,
                "mean_poll_derived_brier": mean_poll,
                "mean_loss_advantage": mean_poll - mean_pm,
            }
        )
    sensitivity = pd.DataFrame(rows, columns=SENSITIVITY_COLUMNS)
    if sensitivity.empty:
        raise ValueError("poll transform sensitivity must contain at least one row")
    return sensitivity.sort_values("poll_error_mae_points").reset_index(drop=True)


def build_state_coverage_audit(*, poll_frame: pd.DataFrame) -> pd.DataFrame:
    """Build a 50-state compatibility audit for the state-poll extension."""

    poll_supported = _states_with_rep_dem_poll_rows(poll_frame)
    included_states = {spec.state for spec in STATE_POLL_SNAPSHOT_CASES}
    rows: list[dict[str, Any]] = []
    for state in ALL_US_STATES:
        market_slug = POLYMARKET_STATE_MARKET_SLUGS.get(state, "")
        has_market = bool(market_slug)
        has_poll = state in poll_supported
        included = state in included_states
        if included:
            status = "included_brier_pair"
            reason = ""
        elif has_market and not has_poll:
            status = "excluded_missing_538_poll_snapshot"
            reason = "No REP/DEM row in preserved 538 polling-average snapshot."
        elif has_poll and not has_market:
            status = "excluded_missing_polymarket_market"
            reason = "No curated Polymarket state-winner market slug found."
        else:
            status = "excluded_missing_both_sources"
            reason = "No curated Polymarket market and no REP/DEM 538 snapshot rows."
        rows.append(
            {
                "state": state,
                "polymarket_event_slug": (
                    f"{_state_slug(state)}-presidential-election-winner"
                    if has_market
                    else ""
                ),
                "polymarket_market_slug": market_slug,
                "polymarket_market_available": has_market,
                "poll_snapshot_has_rep_dem": has_poll,
                "included_in_brier_comparison": included,
                "outcome_value": 1.0 if state in REPUBLICAN_WON_2024_STATES else 0.0,
                "coverage_status": status,
                "exclusion_reason": reason,
            }
        )
    return validate_state_coverage(pd.DataFrame(rows, columns=COVERAGE_COLUMNS))


def validate_state_coverage(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate the state coverage audit output."""

    missing = [column for column in COVERAGE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"state coverage audit missing required columns: {missing}")
    forbidden = [column for column in frame.columns if "wallet" in column.lower()]
    if forbidden:
        raise ValueError(f"state coverage audit must not contain wallet columns: {forbidden}")
    normalized = frame.loc[:, list(COVERAGE_COLUMNS)].copy()
    if len(normalized) != len(ALL_US_STATES):
        raise ValueError("state coverage audit must contain exactly 50 state rows")
    if normalized["state"].duplicated().any():
        raise ValueError("state coverage audit states must be unique")
    if set(normalized["state"]) != set(ALL_US_STATES):
        raise ValueError("state coverage audit states do not match the 50-state universe")
    for column in (
        "polymarket_market_available",
        "poll_snapshot_has_rep_dem",
        "included_in_brier_comparison",
    ):
        normalized[column] = normalized[column].astype(bool)
    normalized["outcome_value"] = pd.to_numeric(
        normalized["outcome_value"],
        errors="raise",
    )
    if not normalized["outcome_value"].between(0.0, 1.0).all():
        raise ValueError("coverage outcome values must be in [0, 1]")
    included = normalized[normalized["included_in_brier_comparison"]]
    if set(included["state"]) != {spec.state for spec in STATE_POLL_SNAPSHOT_CASES}:
        raise ValueError("coverage included states do not match H1 state cases")
    if (
        included["polymarket_market_available"].eq(False).any()
        or included["poll_snapshot_has_rep_dem"].eq(False).any()
    ):
        raise ValueError("included coverage rows must have both required sources")
    return normalized.sort_values("state").reset_index(drop=True)


def write_state_poll_snapshot_figure(*, cases: pd.DataFrame, output_path: Path) -> Path:
    """Write a readable state-poll H1 extension figure."""

    ordered = cases.sort_values("loss_advantage", ascending=True).reset_index(drop=True)
    labels = ordered["state"].tolist()
    y = list(range(len(labels)))
    height = 0.36
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(13.8, 7.0),
        gridspec_kw={"width_ratios": [1.5, 1.0]},
    )
    fig.suptitle(
        "H1 State Poll-Snapshot Extension: Polymarket vs 538 Poll-Derived Probability",
        fontsize=13.5,
        fontweight="bold",
    )

    axes[0].barh(
        [idx - height / 2 for idx in y],
        ordered["polymarket_brier"],
        height=height,
        label="Polymarket",
        color="#2563eb",
    )
    axes[0].barh(
        [idx + height / 2 for idx in y],
        ordered["poll_derived_brier"],
        height=height,
        label="538 poll-derived",
        color="#7c3aed",
    )
    axes[0].set_yticks(y, labels)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("Brier loss for Republican-win event (lower is better)")
    axes[0].set_title("State-level Brier loss on 2024-09-12 snapshot")
    axes[0].legend(fontsize=8)

    counts = cases["lower_loss_source"].value_counts()
    axes[1].bar(
        ["Polymarket\nlower loss", "Poll-derived\nlower loss", "Tie"],
        [
            int(counts.get("polymarket", 0)),
            int(counts.get("poll_derived_forecast", 0)),
            int(counts.get("tie", 0)),
        ],
        color=["#2563eb", "#7c3aed", "#9ca3af"],
    )
    axes[1].set_ylim(0, max(4.2, float(len(cases)) + 0.8))
    axes[1].set_ylabel("States")
    axes[1].set_title("Head-to-head lower-loss count")
    for ax in axes:
        ax.grid(True, axis="x" if ax is axes[0] else "y", alpha=0.25)
    axes[1].text(
        0.5,
        -0.25,
        "Poll averages are transformed with a documented normal-error model; this is not raw polls.",
        transform=axes[1].transAxes,
        ha="center",
        fontsize=8.7,
        color="#374151",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.08, 1, 0.92))
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return output_path


def write_poll_transform_sensitivity_figure(
    *,
    sensitivity: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write the H1 poll-transform sensitivity figure."""

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(13.6, 4.9),
        gridspec_kw={"width_ratios": [1.15, 1.0]},
    )
    fig.suptitle(
        "H1 Poll-Transform Sensitivity: State Snapshot",
        fontsize=13.5,
        fontweight="bold",
    )

    x = sensitivity["poll_error_mae_points"]
    axes[0].plot(
        x,
        sensitivity["mean_polymarket_brier"],
        marker="o",
        label="Polymarket",
        color="#2563eb",
    )
    axes[0].plot(
        x,
        sensitivity["mean_poll_derived_brier"],
        marker="o",
        label="538 poll-derived",
        color="#7c3aed",
    )
    axes[0].axvline(POLL_ERROR_MAE_POINTS, color="#111827", linestyle="--", linewidth=1.0)
    axes[0].set_xlabel("Assumed expected absolute poll error (percentage points)")
    axes[0].set_ylabel("Mean Brier loss")
    axes[0].set_title("Mean loss across 13 state outcomes")
    axes[0].legend(fontsize=8)
    axes[0].grid(True, alpha=0.25)

    axes[1].bar(
        x.astype(str),
        sensitivity["polymarket_lower_loss_count"],
        color="#2563eb",
    )
    axes[1].set_ylim(0, max(13.8, float(sensitivity["case_count"].max()) + 0.8))
    axes[1].set_xlabel("Assumed poll error MAE")
    axes[1].set_ylabel("States where Polymarket has lower loss")
    axes[1].set_title("Head-to-head robustness")
    axes[1].tick_params(axis="x", rotation=45)
    axes[1].grid(True, axis="y", alpha=0.25)
    axes[1].text(
        0.5,
        -0.34,
        "Dashed line marks the documented 3.8 pp assumption; no parameter is fit to outcomes.",
        transform=axes[1].transAxes,
        ha="center",
        fontsize=8.7,
        color="#374151",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.12, 1, 0.9))
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return output_path


def write_state_coverage_figure(*, coverage: pd.DataFrame, output_path: Path) -> Path:
    """Write the H1 state-poll compatibility coverage figure."""

    market_count = int(coverage["polymarket_market_available"].sum())
    poll_count = int(coverage["poll_snapshot_has_rep_dem"].sum())
    included_count = int(coverage["included_in_brier_comparison"].sum())
    status_counts = coverage["coverage_status"].value_counts()

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(13.2, 4.9),
        gridspec_kw={"width_ratios": [1.0, 1.15]},
    )
    fig.suptitle(
        "H1 State-Poll Compatibility Audit",
        fontsize=13.5,
        fontweight="bold",
    )
    axes[0].bar(
        ["US states", "Polymarket\nstate markets", "538 poll\nsnapshot rows", "Valid Brier\npairs"],
        [len(ALL_US_STATES), market_count, poll_count, included_count],
        color=["#9ca3af", "#2563eb", "#7c3aed", "#059669"],
    )
    axes[0].set_ylabel("State count")
    axes[0].set_title("Source coverage funnel")
    axes[0].set_ylim(0, len(ALL_US_STATES) + 5)
    axes[0].grid(True, axis="y", alpha=0.25)
    for idx, value in enumerate([len(ALL_US_STATES), market_count, poll_count, included_count]):
        axes[0].text(idx, value + 1.2, str(value), ha="center", fontsize=9)

    labels = [
        "Included Brier pair",
        "Missing 538 poll snapshot",
        "Missing both sources",
        "Missing Polymarket market",
    ]
    keys = [
        "included_brier_pair",
        "excluded_missing_538_poll_snapshot",
        "excluded_missing_both_sources",
        "excluded_missing_polymarket_market",
    ]
    values = [int(status_counts.get(key, 0)) for key in keys]
    axes[1].barh(labels, values, color=["#059669", "#f59e0b", "#ef4444", "#64748b"])
    axes[1].invert_yaxis()
    axes[1].set_xlabel("State count")
    axes[1].set_title("Why 50 states become 13 H1 pairs")
    axes[1].grid(True, axis="x", alpha=0.25)
    for idx, value in enumerate(values):
        axes[1].text(value + 0.4, idx, str(value), va="center", fontsize=9)
    axes[1].text(
        0.5,
        -0.25,
        "Only states with both a Polymarket state market and REP/DEM rows in the preserved 538 snapshot enter Brier scoring.",
        transform=axes[1].transAxes,
        ha="center",
        fontsize=8.7,
        color="#374151",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.11, 1, 0.9))
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return output_path


def build_state_metadata(
    *,
    source: str,
    cases: pd.DataFrame,
    summary: pd.DataFrame,
    sensitivity: pd.DataFrame,
    coverage: pd.DataFrame,
    cases_output: Path,
    summary_output: Path,
    figure_output: Path,
    sensitivity_output: Path,
    sensitivity_figure_output: Path,
    coverage_output: Path,
    coverage_figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for state-poll snapshot H1 extension."""

    values = _summary_values(summary)
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_state_poll_snapshot_extension",
            "source": source,
            "snapshot_date": SNAPSHOT_DATE,
            "snapshot_timestamp_utc": SNAPSHOT_TIMESTAMP_UTC,
            "calculation_scope": "deterministic_python_from_transformed_538_poll_average_margins",
            "poll_transform_name": "normal_margin_error_from_538_poll_mae",
            "poll_error_mae_points": POLL_ERROR_MAE_POINTS,
            "poll_error_sigma_points": poll_error_sigma_points(),
            "poll_error_sigma_formula": "sigma = mae / sqrt(2/pi)",
            "poll_error_sensitivity_mae_points": list(POLL_ERROR_MAE_SENSITIVITY_POINTS),
            "target_event": "Republican wins state",
            "raw_poll_average_used_directly_as_probability": False,
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
            "polymarket_lower_loss_count": int(values["polymarket_lower_loss_count"]),
            "poll_derived_lower_loss_count": int(values["poll_derived_lower_loss_count"]),
            "polymarket_better_share": float(values["polymarket_better_share"]),
            "mean_polymarket_brier": float(values["mean_polymarket_brier"]),
            "mean_poll_derived_brier": float(values["mean_poll_derived_brier"]),
            "mean_loss_advantage": float(values["mean_loss_advantage"]),
            "sensitivity_row_count": int(len(sensitivity)),
            "sensitivity_min_polymarket_lower_loss_count": int(
                sensitivity["polymarket_lower_loss_count"].min()
            ),
            "sensitivity_max_polymarket_lower_loss_count": int(
                sensitivity["polymarket_lower_loss_count"].max()
            ),
            "sensitivity_min_mean_loss_advantage": float(
                sensitivity["mean_loss_advantage"].min()
            ),
            "sensitivity_max_mean_loss_advantage": float(
                sensitivity["mean_loss_advantage"].max()
            ),
            "coverage_state_universe_count": int(len(coverage)),
            "coverage_polymarket_market_count": int(
                coverage["polymarket_market_available"].sum()
            ),
            "coverage_poll_snapshot_rep_dem_count": int(
                coverage["poll_snapshot_has_rep_dem"].sum()
            ),
            "coverage_valid_brier_pair_count": int(
                coverage["included_in_brier_comparison"].sum()
            ),
            "coverage_excluded_missing_poll_count": int(
                (
                    coverage["coverage_status"]
                    == "excluded_missing_538_poll_snapshot"
                ).sum()
            ),
            "coverage_excluded_missing_both_count": int(
                (coverage["coverage_status"] == "excluded_missing_both_sources").sum()
            ),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
            "broad_many_cases_claim_supported_now": False,
        },
        "source_paths": {
            "cases": str(cases_output),
            "summary": str(summary_output),
            "figure": str(figure_output),
            "sensitivity": str(sensitivity_output),
            "sensitivity_figure": str(sensitivity_figure_output),
            "coverage": str(coverage_output),
            "coverage_figure": str(coverage_figure_output),
        },
        "source_urls": {
            "poll_average_source": FIVETHIRTYEIGHT_POLL_AVERAGES_URL,
            "poll_error_source": FIVETHIRTYEIGHT_POLL_ERROR_SOURCE_URL,
            "gamma_events": f"{GAMMA_BASE_URL}/events",
            "clob_prices_history": f"{CLOB_BASE_URL}/prices-history",
        },
        "case_ids": cases["case_id"].tolist(),
        "states": cases["state"].tolist(),
        "limitations": {
            "poll_transform_is_documented_but_model_assumption": True,
            "not_official_538_state_win_forecast": True,
            "not_raw_poll_comparison": True,
            "single_poll_snapshot_date": True,
            "sensitivity_varies_transform_error_assumption_only": True,
            "state_set_limited_to_538_snapshot_coverage": True,
            "coverage_audit_is_not_additional_brier_evidence": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def mock_poll_average_rows() -> list[dict[str, Any]]:
    """Return a deterministic 538-style polling-average fixture."""

    values = {
        "Arizona": (46.15125, 45.55990),
        "California": (34.41795, 58.30125),
        "Florida": (48.28725, 44.19405),
        "Georgia": (46.48275, 45.96245),
        "Michigan": (44.95310, 46.65590),
        "Minnesota": (41.85890, 48.99625),
        "Nevada": (45.45930, 45.75940),
        "New Hampshire": (43.50810, 50.14210),
        "North Carolina": (45.96250, 46.25900),
        "Ohio": (50.43690, 41.59105),
        "Pennsylvania": (45.54470, 46.40285),
        "Texas": (48.96565, 42.98080),
        "Wisconsin": (44.70555, 47.62660),
    }
    rows: list[dict[str, Any]] = []
    for state, (rep, dem) in values.items():
        rows.append(
            {
                "candidate": "Trump",
                "date": SNAPSHOT_DATE,
                "pct_trend_adjusted": "",
                "state": state,
                "cycle": 2024,
                "party": "REP",
                "pct_estimate": rep,
                "hi": rep + 1.0,
                "lo": rep - 1.0,
            }
        )
        rows.append(
            {
                "candidate": "Harris",
                "date": SNAPSHOT_DATE,
                "pct_trend_adjusted": "",
                "state": state,
                "cycle": 2024,
                "party": "DEM",
                "pct_estimate": dem,
                "hi": dem + 1.0,
                "lo": dem - 1.0,
            }
        )
    return rows


def mock_gamma_event(spec: StatePollSnapshotCaseSpec) -> dict[str, Any]:
    """Return a Gamma-like event fixture for one state case."""

    return {
        "slug": spec.event_slug,
        "markets": [
            {
                "id": f"market-{spec.case_id}",
                "slug": spec.market_slug,
                "conditionId": f"condition-{spec.case_id}",
                "outcomes": json.dumps(["Yes", "No"]),
                "clobTokenIds": json.dumps(
                    [f"token-{spec.case_id}-yes", f"token-{spec.case_id}-no"]
                ),
            }
        ],
    }


def mock_price_point(
    spec: StatePollSnapshotCaseSpec,
    *,
    snapshot_ts: pd.Timestamp,
) -> dict[str, Any]:
    """Return deterministic mock prices mirroring the live state snapshot."""

    prices = {
        "Arizona": 0.605,
        "California": 0.0185,
        "Florida": 0.83,
        "Georgia": 0.585,
        "Michigan": 0.42,
        "Minnesota": 0.075,
        "Nevada": 0.505,
        "New Hampshire": 0.145,
        "North Carolina": 0.595,
        "Ohio": 0.91,
        "Pennsylvania": 0.515,
        "Texas": 0.855,
        "Wisconsin": 0.415,
    }
    return {
        "observed_at_utc": _format_timestamp(snapshot_ts + pd.Timedelta(seconds=2)),
        "price": prices[spec.state],
    }


def _parse_json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    parsed = json.loads(str(value))
    if not isinstance(parsed, list):
        raise ValueError("Gamma list field must decode to a list")
    return [str(item) for item in parsed]


def _history_timestamp(value: Any) -> pd.Timestamp:
    timestamp = float(value)
    if timestamp > 10_000_000_000:
        timestamp = timestamp / 1000.0
    return pd.Timestamp(datetime.fromtimestamp(timestamp, tz=UTC))


def _format_timestamp(value: pd.Timestamp | datetime) -> str:
    return pd.Timestamp(value).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def _summary_values(summary: pd.DataFrame) -> dict[str, float]:
    return {
        str(row["summary_id"]): float(row["value"])
        for _, row in summary.iterrows()
    }


def _slugify_state(state: str) -> str:
    return state.lower().replace(" ", "_")


def _state_slug(state: str) -> str:
    return state.lower().replace(" ", "-")


def _states_with_rep_dem_poll_rows(poll_frame: pd.DataFrame) -> set[str]:
    supported: set[str] = set()
    for state, group in poll_frame.groupby("state"):
        parties = set(group["party"].astype(str))
        if {"REP", "DEM"}.issubset(parties):
            supported.add(str(state))
    return supported


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("mock", "live"), default="mock")
    parser.add_argument("--cases-output", type=Path, default=CASE_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--sensitivity-output", type=Path, default=SENSITIVITY_OUTPUT)
    parser.add_argument(
        "--sensitivity-figure-output",
        type=Path,
        default=SENSITIVITY_FIGURE_OUTPUT,
    )
    parser.add_argument("--coverage-output", type=Path, default=COVERAGE_OUTPUT)
    parser.add_argument(
        "--coverage-figure-output",
        type=Path,
        default=COVERAGE_FIGURE_OUTPUT,
    )
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    parser.add_argument("--snapshot-timestamp-utc", default=SNAPSHOT_TIMESTAMP_UTC)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_state_poll_snapshot_outputs(
            source=args.source,
            cases_output=args.cases_output,
            summary_output=args.summary_output,
            figure_output=args.figure_output,
            sensitivity_output=args.sensitivity_output,
            sensitivity_figure_output=args.sensitivity_figure_output,
            coverage_output=args.coverage_output,
            coverage_figure_output=args.coverage_figure_output,
            metadata_output=args.metadata_output,
            snapshot_timestamp_utc=args.snapshot_timestamp_utc,
        )
    except (httpx.HTTPError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
