"""Build an H1 270toWin state polling-average extension.

This module compares Polymarket Republican-win state probabilities with
270toWin's final 2024 state polling averages. The polling averages are margin
inputs, not win probabilities, so they are transformed with the same documented
normal-error model used by the existing H1 state-poll extension.

The Polymarket probabilities are read from the existing deterministic
50-state snapshot artifact. Live mode fetches only the public 270toWin poll
average JSON and does not call Polymarket, trading, order, wallet, agent, MCP,
LLM, ML, or database-write paths.
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
    FIVETHIRTYEIGHT_POLL_ERROR_SOURCE_URL,
    POLL_ERROR_MAE_POINTS,
    poll_error_sigma_points,
    transformed_margin_probability,
)
from operations.analysis.run_h2_event_windows import RESULTS_DIR


TWO_SEVENTY_POLL_AVERAGE_PAGE_URL = (
    "https://www.270towin.com/2024-presidential-election-polls/"
)
TWO_SEVENTY_POLL_AVERAGE_ENDPOINT = (
    "https://www.270towin.com/polls/php/get-polls-by-state.php"
)
TWO_SEVENTY_ENDPOINT_PARAMS: dict[str, str] = {
    "election_year": "2024",
    "candidate_name_dem": "Harris",
    "candidate_name_rep": "Trump",
    "sort_by": "date",
    "include_3Party": "false",
}
TWO_SEVENTY_HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 deterministic-thesis-audit",
    "Referer": TWO_SEVENTY_POLL_AVERAGE_PAGE_URL,
}

POLYMARKET_STATE_CASE_INPUT = RESULTS_DIR / "h1_rieke_state_forecast_cases.csv"
CASE_OUTPUT = RESULTS_DIR / "h1_270towin_poll_average_cases.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_270towin_poll_average_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_270towin_poll_average.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_270towin_poll_average_metadata.json"

CASE_COLUMNS: tuple[str, ...] = (
    "case_id",
    "state",
    "poll_date_label",
    "poll_date_timestamp_utc",
    "poll_sources_used",
    "poll_republican_pct",
    "poll_democratic_pct",
    "poll_margin_republican_minus_democratic",
    "poll_error_mae_points",
    "poll_error_sigma_points",
    "poll_transform_name",
    "poll_derived_probability",
    "polymarket_forecast_timestamp_utc",
    "polymarket_observed_at_utc",
    "polymarket_market_slug",
    "polymarket_market_id",
    "polymarket_condition_id",
    "target_outcome",
    "target_token_id",
    "outcome_value",
    "polymarket_probability",
    "polymarket_brier",
    "poll_derived_brier",
    "loss_advantage",
    "lower_loss_source",
    "poll_average_source_url",
    "poll_average_endpoint_url",
    "poll_error_source_url",
    "polymarket_source_url",
    "allowed_interpretation",
    "limitation",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "summary_id",
    "value",
    "unit",
    "description",
)

POLL_FRAME_COLUMNS: tuple[str, ...] = (
    "state",
    "poll_date_label",
    "poll_date_timestamp_utc",
    "poll_sources_used",
    "poll_republican_pct",
    "poll_democratic_pct",
    "poll_margin_republican_minus_democratic",
)


@dataclass(frozen=True)
class H1TwoSeventyPollAverageResult:
    """Summary of generated 270toWin polling-average H1 artifacts."""

    cases_path: Path
    summary_path: Path
    figure_path: Path
    metadata_path: Path
    case_count: int
    poll_average_state_rows: int
    polymarket_lower_loss_count: int
    poll_derived_lower_loss_count: int
    mean_polymarket_brier: float
    mean_poll_derived_brier: float

    def to_dict(self) -> dict[str, float | int | str]:
        return {
            "cases_path": str(self.cases_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "case_count": self.case_count,
            "poll_average_state_rows": self.poll_average_state_rows,
            "polymarket_lower_loss_count": self.polymarket_lower_loss_count,
            "poll_derived_lower_loss_count": self.poll_derived_lower_loss_count,
            "mean_polymarket_brier": self.mean_polymarket_brier,
            "mean_poll_derived_brier": self.mean_poll_derived_brier,
        }


MOCK_270TOWIN_STATE_POLL_AVERAGES: tuple[tuple[str, float, float, int, int], ...] = (
    ("Arizona", 48.47, 46.82, 17, 1730678400),
    ("California", 34.2, 59.0, 5, 1730678400),
    ("Florida", 51.13, 44.88, 8, 1730678400),
    ("Georgia", 48.73, 47.53, 15, 1730678400),
    ("Iowa", 50.0, 45.25, 4, 1730678400),
    ("Michigan", 46.78, 48.57, 23, 1730678400),
    ("Minnesota", 43.6, 49.8, 5, 1730678400),
    ("Missouri", 54.0, 39.0, 1, 1730678400),
    ("Nevada", 48.23, 47.62, 13, 1730678400),
    ("New Jersey", 38.33, 54.67, 3, 1730678400),
    ("New Mexico", 43.75, 49.75, 4, 1730678400),
    ("New York", 39.67, 57.33, 3, 1730678400),
    ("North Carolina", 48.56, 47.31, 16, 1730678400),
    ("Ohio", 52.0, 44.33, 6, 1730678400),
    ("Pennsylvania", 48.2, 48.24, 25, 1730678400),
    ("Virginia", 43.4, 49.2, 5, 1730678400),
    ("Washington", 36.5, 55.75, 4, 1730678400),
    ("Wisconsin", 47.71, 48.76, 17, 1730678400),
    ("Colorado", 42.5, 52.5, 2, 1730592000),
    ("Maine", 41.67, 50.33, 3, 1730592000),
    ("Maryland", 33.0, 60.2, 5, 1730592000),
    ("Massachusetts", 31.75, 59.5, 4, 1730592000),
    ("New Hampshire", 45.5, 50.5, 4, 1730592000),
    ("Rhode Island", 40.0, 54.0, 1, 1730592000),
    ("Texas", 51.8, 44.4, 5, 1730592000),
    ("Vermont", 31.0, 63.0, 1, 1730592000),
    ("Wyoming", 66.0, 27.5, 2, 1730419200),
    ("South Carolina", 53.67, 42.0, 3, 1730332800),
    ("Utah", 57.5, 32.0, 2, 1730246400),
    ("Nebraska", 55.0, 40.0, 2, 1730160000),
    ("Kansas", 48.0, 43.0, 1, 1730073600),
    ("Alaska", 51.0, 43.0, 1, 1729987200),
    ("Montana", 57.5, 39.5, 2, 1729987200),
    ("South Dakota", 60.5, 34.0, 2, 1729728000),
    ("Oregon", 41.0, 53.0, 1, 1729209600),
    ("Tennessee", 56.0, 35.0, 1, 1728950400),
    ("North Dakota", 59.0, 32.0, 1, 1727827200),
    ("Indiana", 56.0, 39.5, 2, 1727568000),
    ("Delaware", 36.5, 55.0, 2, 1727395200),
    ("Connecticut", 41.0, 57.0, 1, 1727049600),
    ("Arkansas", 55.0, 40.0, 1, 1726185600),
    ("Oklahoma", 56.0, 40.0, 1, 1725494400),
    ("West Virginia", 61.0, 34.0, 1, 1724976000),
)


def generate_h1_270towin_poll_average_outputs(
    *,
    source: str = "mock",
    polymarket_cases_input: Path = POLYMARKET_STATE_CASE_INPUT,
    cases_output: Path = CASE_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
    client: httpx.Client | None = None,
) -> H1TwoSeventyPollAverageResult:
    """Generate 270toWin poll-average cases, summary, figure, and metadata."""

    if source not in {"mock", "live"}:
        raise ValueError("source must be either 'mock' or 'live'")
    own_client = client is None
    http_client = client or httpx.Client(timeout=25.0)
    try:
        poll_rows = (
            mock_two_seventy_poll_average_rows()
            if source == "mock"
            else fetch_two_seventy_poll_average_rows(http_client)
        )
    finally:
        if own_client:
            http_client.close()

    poll_frame = parse_two_seventy_poll_average_rows(poll_rows)
    polymarket_cases = read_polymarket_state_cases(polymarket_cases_input)
    cases = build_270towin_poll_average_cases(
        poll_frame=poll_frame,
        polymarket_cases=polymarket_cases,
    )
    cases = validate_270towin_poll_average_cases(cases)
    summary = build_270towin_poll_average_summary(
        cases=cases,
        poll_frame=poll_frame,
        endpoint_row_count=len(poll_rows),
        polymarket_cases=polymarket_cases,
    )

    cases_output.parent.mkdir(parents=True, exist_ok=True)
    cases.to_csv(cases_output, index=False)
    summary.to_csv(summary_output, index=False)
    write_270towin_poll_average_figure(cases=cases, output_path=figure_output)
    metadata = build_270towin_poll_average_metadata(
        source=source,
        cases=cases,
        summary=summary,
        poll_frame=poll_frame,
        endpoint_row_count=len(poll_rows),
        polymarket_cases_input=polymarket_cases_input,
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
    return H1TwoSeventyPollAverageResult(
        cases_path=cases_output,
        summary_path=summary_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        case_count=int(values["case_count"]),
        poll_average_state_rows=int(values["poll_average_state_rows"]),
        polymarket_lower_loss_count=int(values["polymarket_lower_loss_count"]),
        poll_derived_lower_loss_count=int(values["poll_derived_lower_loss_count"]),
        mean_polymarket_brier=float(values["mean_polymarket_brier"]),
        mean_poll_derived_brier=float(values["mean_poll_derived_brier"]),
    )


def fetch_two_seventy_poll_average_rows(client: httpx.Client) -> list[dict[str, Any]]:
    """Fetch public 270toWin 2024 state polling-average rows."""

    response = client.get(
        TWO_SEVENTY_POLL_AVERAGE_ENDPOINT,
        params=TWO_SEVENTY_ENDPOINT_PARAMS,
        headers=TWO_SEVENTY_HEADERS,
    )
    response.raise_for_status()
    payload = response.json()
    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, dict) or not results:
        raise ValueError("270toWin poll-average response must contain results")
    rows: list[dict[str, Any]] = []
    for state, values in results.items():
        if isinstance(values, dict):
            rows.append({"state": str(state), **values})
    if not rows:
        raise ValueError("270toWin poll-average results did not contain object rows")
    return rows


def parse_two_seventy_poll_average_rows(rows: Sequence[dict[str, Any]]) -> pd.DataFrame:
    """Return validated 270toWin state polling-average rows."""

    frame = pd.DataFrame(rows)
    required = {
        "state",
        "poll_date",
        "poll_date_timestamp",
        "poll_rep_avg",
        "poll_dem_avg",
        "poll_sources_used",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"270toWin poll-average rows missing columns: {missing}")
    state_frame = frame.loc[
        frame["state"].astype(str).isin(set(ALL_US_STATES))
    ].copy()
    if state_frame.empty:
        raise ValueError("270toWin poll-average rows contain no 50-state rows")
    if state_frame["state"].duplicated().any():
        raise ValueError("270toWin poll-average state rows must be unique")
    for column in ("poll_rep_avg", "poll_dem_avg", "poll_sources_used"):
        state_frame[column] = pd.to_numeric(state_frame[column], errors="raise")
    state_frame["poll_date_timestamp"] = pd.to_numeric(
        state_frame["poll_date_timestamp"],
        errors="raise",
    ).astype("int64")
    for column in ("poll_rep_avg", "poll_dem_avg"):
        if not state_frame[column].between(0.0, 100.0).all():
            raise ValueError(f"{column} values must be percentages in [0, 100]")
    if (state_frame["poll_sources_used"] < 0).any():
        raise ValueError("poll_sources_used values must be non-negative")
    timestamps = pd.to_datetime(
        state_frame["poll_date_timestamp"],
        unit="s",
        utc=True,
    )
    normalized = pd.DataFrame(
        {
            "state": state_frame["state"].astype(str),
            "poll_date_label": state_frame["poll_date"].astype(str),
            "poll_date_timestamp_utc": timestamps.dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "poll_sources_used": state_frame["poll_sources_used"].astype(int),
            "poll_republican_pct": state_frame["poll_rep_avg"].astype(float),
            "poll_democratic_pct": state_frame["poll_dem_avg"].astype(float),
        }
    )
    normalized["poll_margin_republican_minus_democratic"] = (
        normalized["poll_republican_pct"] - normalized["poll_democratic_pct"]
    )
    return normalized.loc[:, list(POLL_FRAME_COLUMNS)].sort_values("state").reset_index(drop=True)


def read_polymarket_state_cases(path: Path) -> pd.DataFrame:
    """Read local deterministic Polymarket state snapshot cases."""

    if not path.exists():
        raise FileNotFoundError(f"Polymarket state case input not found: {path}")
    frame = pd.read_csv(path)
    required = {
        "state",
        "forecast_timestamp_utc",
        "polymarket_observed_at_utc",
        "polymarket_market_slug",
        "polymarket_market_id",
        "polymarket_condition_id",
        "target_outcome",
        "target_token_id",
        "outcome_value",
        "polymarket_probability",
        "polymarket_source_url",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Polymarket state cases missing columns: {missing}")
    forbidden = [
        column
        for column in frame.columns
        if "wallet" in column.lower() or "order" in column.lower()
    ]
    if forbidden:
        raise ValueError(f"Polymarket state cases must not contain forbidden columns: {forbidden}")
    normalized = frame.copy()
    normalized = normalized.loc[
        normalized["state"].astype(str).isin(set(ALL_US_STATES))
    ].copy()
    if normalized.empty:
        raise ValueError("Polymarket state case input contains no 50-state rows")
    if normalized["state"].duplicated().any():
        raise ValueError("Polymarket state case states must be unique")
    for column in ("outcome_value", "polymarket_probability"):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
        if not normalized[column].between(0.0, 1.0).all():
            raise ValueError(f"{column} values must be in [0, 1]")
    return normalized.sort_values("state").reset_index(drop=True)


def build_270towin_poll_average_cases(
    *,
    poll_frame: pd.DataFrame,
    polymarket_cases: pd.DataFrame,
) -> pd.DataFrame:
    """Build case rows for matched 270toWin polling averages and Polymarket states."""

    pm_by_state = polymarket_cases.set_index("state")
    rows: list[dict[str, Any]] = []
    for poll in poll_frame.itertuples(index=False):
        state = str(poll.state)
        if state not in pm_by_state.index:
            continue
        pm = pm_by_state.loc[state]
        outcome = float(pm["outcome_value"])
        pm_probability = float(pm["polymarket_probability"])
        poll_probability = transformed_margin_probability(
            float(poll.poll_margin_republican_minus_democratic)
        )
        pm_brier = (pm_probability - outcome) ** 2
        poll_brier = (poll_probability - outcome) ** 2
        if pm_brier < poll_brier:
            lower_loss_source = "polymarket"
        elif poll_brier < pm_brier:
            lower_loss_source = "poll_derived_forecast"
        else:
            lower_loss_source = "tie"
        rows.append(
            {
                "case_id": (
                    "us_2024_president_"
                    f"{_slugify_state(state)}_270towin_poll_average_republican"
                ),
                "state": state,
                "poll_date_label": str(poll.poll_date_label),
                "poll_date_timestamp_utc": str(poll.poll_date_timestamp_utc),
                "poll_sources_used": int(poll.poll_sources_used),
                "poll_republican_pct": float(poll.poll_republican_pct),
                "poll_democratic_pct": float(poll.poll_democratic_pct),
                "poll_margin_republican_minus_democratic": float(
                    poll.poll_margin_republican_minus_democratic
                ),
                "poll_error_mae_points": POLL_ERROR_MAE_POINTS,
                "poll_error_sigma_points": poll_error_sigma_points(),
                "poll_transform_name": "normal_margin_error_from_538_poll_mae",
                "poll_derived_probability": poll_probability,
                "polymarket_forecast_timestamp_utc": str(pm["forecast_timestamp_utc"]),
                "polymarket_observed_at_utc": str(pm["polymarket_observed_at_utc"]),
                "polymarket_market_slug": str(pm["polymarket_market_slug"]),
                "polymarket_market_id": str(pm["polymarket_market_id"]),
                "polymarket_condition_id": str(pm["polymarket_condition_id"]),
                "target_outcome": str(pm["target_outcome"]),
                "target_token_id": str(pm["target_token_id"]),
                "outcome_value": outcome,
                "polymarket_probability": pm_probability,
                "polymarket_brier": pm_brier,
                "poll_derived_brier": poll_brier,
                "loss_advantage": poll_brier - pm_brier,
                "lower_loss_source": lower_loss_source,
                "poll_average_source_url": TWO_SEVENTY_POLL_AVERAGE_PAGE_URL,
                "poll_average_endpoint_url": TWO_SEVENTY_POLL_AVERAGE_ENDPOINT,
                "poll_error_source_url": FIVETHIRTYEIGHT_POLL_ERROR_SOURCE_URL,
                "polymarket_source_url": str(pm["polymarket_source_url"]),
                "allowed_interpretation": (
                    "State-level Brier comparison between a Polymarket "
                    "Republican-win state snapshot and a 270toWin polling-average "
                    "margin transformed into a Republican-win probability."
                ),
                "limitation": (
                    "270toWin polling averages are transformed margin inputs, "
                    "not raw win probabilities; all states share one presidential "
                    "election context."
                ),
            }
        )
    if not rows:
        raise ValueError("No matched 270toWin poll-average and Polymarket state cases")
    return pd.DataFrame(rows, columns=CASE_COLUMNS)


def validate_270towin_poll_average_cases(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate generated 270toWin polling-average comparison cases."""

    missing = [column for column in CASE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"270toWin poll-average cases missing columns: {missing}")
    forbidden = [
        column
        for column in frame.columns
        if "wallet" in column.lower() or "order" in column.lower()
    ]
    if forbidden:
        raise ValueError(f"270toWin poll-average cases contain forbidden columns: {forbidden}")
    normalized = frame.loc[:, list(CASE_COLUMNS)].copy()
    for column in (
        "poll_sources_used",
        "poll_republican_pct",
        "poll_democratic_pct",
        "poll_margin_republican_minus_democratic",
        "poll_error_mae_points",
        "poll_error_sigma_points",
        "poll_derived_probability",
        "outcome_value",
        "polymarket_probability",
        "polymarket_brier",
        "poll_derived_brier",
        "loss_advantage",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    for column in ("poll_republican_pct", "poll_democratic_pct"):
        if not normalized[column].between(0.0, 100.0).all():
            raise ValueError(f"{column} values must be percentages in [0, 100]")
    for column in ("poll_derived_probability", "outcome_value", "polymarket_probability"):
        if not normalized[column].between(0.0, 1.0).all():
            raise ValueError(f"{column} values must be in [0, 1]")
    if (normalized["polymarket_brier"] < 0).any() or (
        normalized["poll_derived_brier"] < 0
    ).any():
        raise ValueError("Brier values must be non-negative")
    if normalized["case_id"].duplicated().any():
        raise ValueError("270toWin poll-average case ids must be unique")
    if normalized["state"].duplicated().any():
        raise ValueError("270toWin poll-average states must be unique")
    if not set(normalized["state"]).issubset(set(ALL_US_STATES)):
        raise ValueError("270toWin poll-average cases must be 50-state rows")
    for column in (
        "case_id",
        "state",
        "poll_date_timestamp_utc",
        "polymarket_observed_at_utc",
        "polymarket_market_slug",
        "target_token_id",
        "poll_transform_name",
        "poll_average_source_url",
    ):
        if normalized[column].fillna("").astype(str).str.strip().eq("").any():
            raise ValueError(f"{column} must not be blank")
    return normalized.sort_values("state").reset_index(drop=True)


def build_270towin_poll_average_summary(
    *,
    cases: pd.DataFrame,
    poll_frame: pd.DataFrame,
    endpoint_row_count: int,
    polymarket_cases: pd.DataFrame,
) -> pd.DataFrame:
    """Build compact summary rows for the 270toWin poll-average extension."""

    pm_lower = int((cases["lower_loss_source"] == "polymarket").sum())
    poll_lower = int((cases["lower_loss_source"] == "poll_derived_forecast").sum())
    ties = int((cases["lower_loss_source"] == "tie").sum())
    matched_states = set(cases["state"].astype(str))
    poll_states = set(poll_frame["state"].astype(str))
    pm_states = set(polymarket_cases["state"].astype(str))
    mean_pm = float(cases["polymarket_brier"].mean())
    mean_poll = float(cases["poll_derived_brier"].mean())
    rows = [
        ("case_count", len(cases), "cases", "Matched 270toWin poll-average state outcomes."),
        (
            "independent_resolved_outcome_count",
            len(cases),
            "outcomes",
            "Each row is a distinct 2024 presidential state outcome.",
        ),
        (
            "poll_average_endpoint_row_count",
            endpoint_row_count,
            "rows",
            "Rows returned by the 270toWin results object, including national and district rows.",
        ),
        (
            "poll_average_state_rows",
            len(poll_frame),
            "state rows",
            "Rows in the 270toWin results object that match the 50-state universe.",
        ),
        (
            "matched_state_count",
            len(matched_states),
            "states",
            "States with both a 270toWin polling average and a local Polymarket state case.",
        ),
        (
            "poll_average_missing_state_count",
            len(set(ALL_US_STATES) - poll_states),
            "states",
            "50-state rows absent from the 270toWin polling-average results object.",
        ),
        (
            "polymarket_missing_matched_state_count",
            len(poll_states - pm_states),
            "states",
            "270toWin state rows without a local Polymarket state case.",
        ),
        (
            "excluded_non_state_or_unmatched_poll_rows",
            endpoint_row_count - len(matched_states),
            "rows",
            "Endpoint rows that do not become matched state Brier cases.",
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
            "Cases where the transformed 270toWin polling average has lower Brier loss.",
        ),
        ("tie_count", ties, "cases", "Cases with equal Brier loss."),
        (
            "polymarket_better_share",
            pm_lower / len(cases) if len(cases) else 0.0,
            "share",
            "Share of matched cases where Polymarket loss is lower.",
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
            "Mean Brier loss across transformed 270toWin poll-average probabilities.",
        ),
        (
            "mean_loss_advantage",
            mean_poll - mean_pm,
            "brier_score",
            "Positive values mean lower mean Polymarket loss.",
        ),
    ]
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def write_270towin_poll_average_figure(
    *,
    cases: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write a readable figure for the 270toWin poll-average extension."""

    ordered = cases.sort_values("loss_advantage").reset_index(drop=True)
    colors = ordered["loss_advantage"].map(
        lambda value: "#2563eb" if value > 0 else "#7c3aed"
    )
    mean_rows = [
        ("Polymarket", float(cases["polymarket_brier"].mean()), "#2563eb"),
        ("270toWin\npoll-derived", float(cases["poll_derived_brier"].mean()), "#7c3aed"),
    ]
    counts = cases["lower_loss_source"].value_counts()

    fig, axes = plt.subplots(2, 2, figsize=(15.4, 11.4))
    fig.suptitle(
        "H1 270toWin Polling-Average Extension",
        fontsize=13.5,
        fontweight="bold",
    )

    axes[0, 0].bar(
        [row[0] for row in mean_rows],
        [row[1] for row in mean_rows],
        color=[row[2] for row in mean_rows],
    )
    axes[0, 0].set_ylabel("Mean Brier loss")
    axes[0, 0].set_title("Mean loss across matched state outcomes")
    axes[0, 0].set_ylim(0, max(row[1] for row in mean_rows) * 1.18)
    axes[0, 0].grid(True, axis="y", alpha=0.25)
    for idx, row in enumerate(mean_rows):
        axes[0, 0].text(idx, row[1] + 0.002, f"{row[1]:.4f}", ha="center", fontsize=9)

    count_labels = ["Polymarket\nlower loss", "Poll-derived\nlower loss", "Tie"]
    count_values = [
        int(counts.get("polymarket", 0)),
        int(counts.get("poll_derived_forecast", 0)),
        int(counts.get("tie", 0)),
    ]
    axes[0, 1].bar(count_labels, count_values, color=["#2563eb", "#7c3aed", "#9ca3af"])
    axes[0, 1].set_ylabel("States")
    axes[0, 1].set_title("Head-to-head lower-loss count")
    axes[0, 1].set_ylim(0, max(count_values) + 5)
    axes[0, 1].grid(True, axis="y", alpha=0.25)
    for idx, value in enumerate(count_values):
        axes[0, 1].text(idx, value + 0.7, str(value), ha="center", fontsize=9)

    y = range(len(ordered))
    axes[1, 0].barh(y, ordered["loss_advantage"], color=colors)
    axes[1, 0].set_yticks(list(y), ordered["state"], fontsize=7.0)
    axes[1, 0].axvline(0, color="#111827", linewidth=0.8)
    axes[1, 0].set_xlabel("270toWin poll-derived Brier minus Polymarket Brier")
    axes[1, 0].set_title("Per-state loss advantage")
    axes[1, 0].grid(True, axis="x", alpha=0.25)

    scatter_colors = cases["outcome_value"].map({1.0: "#2563eb", 0.0: "#f59e0b"})
    axes[1, 1].scatter(
        cases["poll_derived_probability"],
        cases["polymarket_probability"],
        c=scatter_colors,
        alpha=0.82,
        edgecolor="#111827",
        linewidth=0.35,
    )
    axes[1, 1].plot([0, 1], [0, 1], color="#6b7280", linestyle="--", linewidth=1.0)
    axes[1, 1].set_xlim(-0.03, 1.03)
    axes[1, 1].set_ylim(-0.03, 1.03)
    axes[1, 1].set_xlabel("270toWin poll-derived Republican-win probability")
    axes[1, 1].set_ylabel("Polymarket Republican-win probability")
    axes[1, 1].set_title("Probability comparison by resolved state outcome")
    axes[1, 1].grid(True, alpha=0.25)

    fig.text(
        0.5,
        0.012,
        (
            "270toWin polling averages are transformed with the documented "
            "normal-error model; this is a direct poll-derived comparison, "
            "not raw poll shares or an official win forecast."
        ),
        ha="center",
        fontsize=9,
        color="#374151",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return output_path


def build_270towin_poll_average_metadata(
    *,
    source: str,
    cases: pd.DataFrame,
    summary: pd.DataFrame,
    poll_frame: pd.DataFrame,
    endpoint_row_count: int,
    polymarket_cases_input: Path,
    cases_output: Path,
    summary_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for the 270toWin polling-average extension."""

    values = _summary_values(summary)
    poll_timestamps = pd.to_datetime(poll_frame["poll_date_timestamp_utc"], utc=True)
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_270towin_poll_average_extension",
            "source": source,
            "calculation_scope": (
                "deterministic_python_from_270towin_poll_average_margins_"
                "and_existing_polymarket_state_snapshot_cases"
            ),
            "target_event": "Republican wins state",
            "poll_transform_name": "normal_margin_error_from_538_poll_mae",
            "poll_error_mae_points": POLL_ERROR_MAE_POINTS,
            "poll_error_sigma_points": poll_error_sigma_points(),
            "poll_error_sigma_formula": "sigma = mae / sqrt(2/pi)",
            "raw_poll_average_used_directly_as_probability": False,
            "uses_raw_poll_shares_directly": False,
            "rcp_included": False,
            "uses_existing_polymarket_artifact": True,
            "collects_polymarket_live_data": False,
            "read_only_public_poll_endpoint": source == "live",
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
            "poll_average_endpoint_row_count": int(values["poll_average_endpoint_row_count"]),
            "poll_average_state_rows": int(values["poll_average_state_rows"]),
            "matched_state_count": int(values["matched_state_count"]),
            "poll_average_missing_state_count": int(
                values["poll_average_missing_state_count"]
            ),
            "polymarket_lower_loss_count": int(values["polymarket_lower_loss_count"]),
            "poll_derived_lower_loss_count": int(values["poll_derived_lower_loss_count"]),
            "tie_count": int(values["tie_count"]),
            "polymarket_better_share": float(values["polymarket_better_share"]),
            "mean_polymarket_brier": float(values["mean_polymarket_brier"]),
            "mean_poll_derived_brier": float(values["mean_poll_derived_brier"]),
            "mean_loss_advantage": float(values["mean_loss_advantage"]),
            "poll_date_min_utc": poll_timestamps.min().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "poll_date_max_utc": poll_timestamps.max().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
            "broad_many_cases_claim_supported_now": False,
        },
        "source_paths": {
            "polymarket_cases_input": str(polymarket_cases_input),
            "cases": str(cases_output),
            "summary": str(summary_output),
            "figure": str(figure_output),
        },
        "source_urls": {
            "two_seventy_poll_average_page": TWO_SEVENTY_POLL_AVERAGE_PAGE_URL,
            "two_seventy_poll_average_endpoint": TWO_SEVENTY_POLL_AVERAGE_ENDPOINT,
            "poll_error_source": FIVETHIRTYEIGHT_POLL_ERROR_SOURCE_URL,
        },
        "states": cases["state"].tolist(),
        "limitations": {
            "poll_transform_is_documented_but_model_assumption": True,
            "not_official_270towin_win_forecast": True,
            "not_raw_poll_comparison": True,
            "state_outcomes_share_one_election_context": True,
            "same_polymarket_snapshot_as_state_model_extensions": True,
            "mean_loss_advantage_not_same_as_majority_of_states": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def mock_two_seventy_poll_average_rows() -> list[dict[str, Any]]:
    """Return a deterministic 270toWin-style polling-average fixture."""

    rows = [
        {
            "state": "0",
            "poll_date": "Nov. 4",
            "poll_date_timestamp": 1730678400,
            "poll_rep_avg": 47.2,
            "poll_dem_avg": 48.44,
            "poll_sources_used": 25,
        },
        {
            "state": "Maine Dist. 1",
            "poll_date": "Nov. 3",
            "poll_date_timestamp": 1730592000,
            "poll_rep_avg": 36.0,
            "poll_dem_avg": 58.0,
            "poll_sources_used": 1,
        },
        {
            "state": "Maine Dist. 2",
            "poll_date": "Nov. 3",
            "poll_date_timestamp": 1730592000,
            "poll_rep_avg": 50.0,
            "poll_dem_avg": 43.0,
            "poll_sources_used": 1,
        },
        {
            "state": "Nebraska Dist. 1",
            "poll_date": "Oct. 29",
            "poll_date_timestamp": 1730160000,
            "poll_rep_avg": 54.0,
            "poll_dem_avg": 41.0,
            "poll_sources_used": 1,
        },
        {
            "state": "Nebraska Dist. 2",
            "poll_date": "Oct. 29",
            "poll_date_timestamp": 1730160000,
            "poll_rep_avg": 43.0,
            "poll_dem_avg": 51.0,
            "poll_sources_used": 1,
        },
        {
            "state": "Nebraska Dist. 3",
            "poll_date": "Oct. 29",
            "poll_date_timestamp": 1730160000,
            "poll_rep_avg": 69.0,
            "poll_dem_avg": 26.0,
            "poll_sources_used": 1,
        },
    ]
    for state, rep, dem, sources, timestamp in MOCK_270TOWIN_STATE_POLL_AVERAGES:
        rows.append(
            {
                "state": state,
                "poll_date": _poll_date_label(timestamp),
                "poll_date_timestamp": timestamp,
                "poll_rep_avg": rep,
                "poll_dem_avg": dem,
                "poll_sources_used": sources,
            }
        )
    return rows


def _summary_values(summary: pd.DataFrame) -> dict[str, float]:
    return {
        str(row["summary_id"]): float(row["value"])
        for _, row in summary.iterrows()
    }


def _poll_date_label(timestamp: int) -> str:
    value = pd.Timestamp(datetime.fromtimestamp(timestamp, tz=UTC))
    return f"{value.strftime('%b')}. {value.day}"


def _slugify_state(state: str) -> str:
    return state.lower().replace(" ", "_")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("mock", "live"), default="mock")
    parser.add_argument(
        "--polymarket-cases-input",
        type=Path,
        default=POLYMARKET_STATE_CASE_INPUT,
    )
    parser.add_argument("--cases-output", type=Path, default=CASE_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_270towin_poll_average_outputs(
            source=args.source,
            polymarket_cases_input=args.polymarket_cases_input,
            cases_output=args.cases_output,
            summary_output=args.summary_output,
            figure_output=args.figure_output,
            metadata_output=args.metadata_output,
        )
    except (httpx.HTTPError, FileNotFoundError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
