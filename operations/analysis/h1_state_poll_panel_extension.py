"""Build an H1 state-date poll panel extension.

The snapshot extension uses only the final preserved 538 polling-average date.
The same public 538 file also contains daily state polling averages from
2024-03-01 to 2024-09-12. This module transforms those daily state margins into
Republican-win probabilities with the documented normal-error model, matches
them to bounded Polymarket state-market price history, and reports the larger
state-date panel as repeated forecast rows.
"""
from __future__ import annotations

import argparse
import io
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
    FIVETHIRTYEIGHT_POLL_AVERAGES_URL,
    FIVETHIRTYEIGHT_POLL_ERROR_SOURCE_URL,
    POLL_ERROR_MAE_POINTS,
    poll_error_sigma_points,
    transformed_margin_probability,
)
from operations.analysis.run_h2_event_windows import RESULTS_DIR


MARKET_CASE_INPUT = RESULTS_DIR / "h1_rieke_state_forecast_cases.csv"
START_DATE = "2024-03-01"
END_DATE = "2024-09-12"
POLL_PANEL_TIMESTAMP_HOUR_UTC = 12
MAX_PANEL_PRICE_DISTANCE_SECONDS = 18 * 60 * 60
HISTORY_CHUNK_DAYS = 14
HISTORY_FIDELITY_MINUTES = 1440

CASE_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_cases.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_summary.csv"
STATE_SUMMARY_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_state_summary.csv"
COVERAGE_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_coverage.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_state_poll_panel.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_metadata.json"

CASE_COLUMNS: tuple[str, ...] = (
    "case_id",
    "state",
    "forecast_date",
    "forecast_timestamp_utc",
    "polymarket_observed_at_utc",
    "polymarket_time_distance_seconds",
    "polymarket_market_slug",
    "polymarket_market_id",
    "polymarket_condition_id",
    "target_outcome",
    "target_token_id",
    "outcome_value",
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
    "price_history_source_url",
    "row_unit",
    "allowed_interpretation",
    "limitation",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "summary_id",
    "value",
    "unit",
    "description",
)

STATE_SUMMARY_COLUMNS: tuple[str, ...] = (
    "state",
    "poll_pair_count",
    "matched_case_count",
    "matched_date_count",
    "polymarket_lower_loss_count",
    "poll_derived_lower_loss_count",
    "tie_count",
    "polymarket_better_share",
    "mean_polymarket_brier",
    "mean_poll_derived_brier",
    "mean_loss_advantage",
    "first_matched_date",
    "last_matched_date",
)

COVERAGE_COLUMNS: tuple[str, ...] = (
    "state",
    "poll_pair_count",
    "history_point_count",
    "matched_case_count",
    "unmatched_poll_pair_count",
    "first_history_timestamp_utc",
    "last_history_timestamp_utc",
    "coverage_status",
)


@dataclass(frozen=True)
class H1StatePollPanelResult:
    """Summary of generated H1 state-date poll panel artifacts."""

    cases_path: Path
    summary_path: Path
    state_summary_path: Path
    coverage_path: Path
    figure_path: Path
    metadata_path: Path
    case_count: int
    state_count: int
    date_count: int
    polymarket_lower_loss_count: int
    poll_derived_lower_loss_count: int
    mean_polymarket_brier: float
    mean_poll_derived_brier: float

    def to_dict(self) -> dict[str, float | int | str]:
        return {
            "cases_path": str(self.cases_path),
            "summary_path": str(self.summary_path),
            "state_summary_path": str(self.state_summary_path),
            "coverage_path": str(self.coverage_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "case_count": self.case_count,
            "state_count": self.state_count,
            "date_count": self.date_count,
            "polymarket_lower_loss_count": self.polymarket_lower_loss_count,
            "poll_derived_lower_loss_count": self.poll_derived_lower_loss_count,
            "mean_polymarket_brier": self.mean_polymarket_brier,
            "mean_poll_derived_brier": self.mean_poll_derived_brier,
        }


def generate_h1_state_poll_panel_outputs(
    *,
    source: str = "mock",
    market_case_input: Path = MARKET_CASE_INPUT,
    cases_output: Path = CASE_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    state_summary_output: Path = STATE_SUMMARY_OUTPUT,
    coverage_output: Path = COVERAGE_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
    client: httpx.Client | None = None,
) -> H1StatePollPanelResult:
    """Generate the state-date poll panel outputs."""

    if source not in {"mock", "live"}:
        raise ValueError("source must be either 'mock' or 'live'")
    market_cases = read_market_cases(market_case_input)
    poll_rows = (
        mock_poll_average_rows()
        if source == "mock"
        else fetch_poll_average_rows(client=client)
    )
    poll_panel = build_poll_panel(poll_rows=poll_rows, market_cases=market_cases)
    own_client = client is None
    http_client = client or httpx.Client(timeout=30.0)
    try:
        history_by_state = (
            mock_history_by_state(poll_panel)
            if source == "mock"
            else fetch_history_by_state(client=http_client, poll_panel=poll_panel, market_cases=market_cases)
        )
    finally:
        if own_client:
            http_client.close()

    cases = validate_panel_cases(
        build_panel_cases(
            poll_panel=poll_panel,
            market_cases=market_cases,
            history_by_state=history_by_state,
        )
    )
    summary = build_panel_summary(cases=cases, poll_panel=poll_panel)
    state_summary = build_state_summary(cases=cases, poll_panel=poll_panel)
    coverage = build_coverage(
        poll_panel=poll_panel,
        cases=cases,
        history_by_state=history_by_state,
    )

    cases_output.parent.mkdir(parents=True, exist_ok=True)
    cases.to_csv(cases_output, index=False)
    summary.to_csv(summary_output, index=False)
    state_summary.to_csv(state_summary_output, index=False)
    coverage.to_csv(coverage_output, index=False)
    write_panel_figure(
        cases=cases,
        summary=summary,
        state_summary=state_summary,
        coverage=coverage,
        output_path=figure_output,
    )
    metadata = build_metadata(
        source=source,
        cases=cases,
        summary=summary,
        state_summary=state_summary,
        coverage=coverage,
        market_case_input=market_case_input,
        cases_output=cases_output,
        summary_output=summary_output,
        state_summary_output=state_summary_output,
        coverage_output=coverage_output,
        figure_output=figure_output,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    values = _summary_values(summary)
    return H1StatePollPanelResult(
        cases_path=cases_output,
        summary_path=summary_output,
        state_summary_path=state_summary_output,
        coverage_path=coverage_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        case_count=int(values["matched_case_count"]),
        state_count=int(values["matched_state_count"]),
        date_count=int(values["matched_date_count"]),
        polymarket_lower_loss_count=int(values["polymarket_lower_loss_count"]),
        poll_derived_lower_loss_count=int(values["poll_derived_lower_loss_count"]),
        mean_polymarket_brier=float(values["mean_polymarket_brier"]),
        mean_poll_derived_brier=float(values["mean_poll_derived_brier"]),
    )


def read_market_cases(path: Path) -> pd.DataFrame:
    """Read state market metadata from an existing deterministic H1 artifact."""

    if not path.exists():
        raise FileNotFoundError(f"market case input not found: {path}")
    frame = pd.read_csv(path)
    required = {
        "state",
        "target_token_id",
        "outcome_value",
        "polymarket_market_slug",
        "polymarket_market_id",
        "polymarket_condition_id",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"market case input missing columns: {missing}")
    normalized = frame.loc[:, sorted(required)].copy()
    if normalized["state"].duplicated().any():
        raise ValueError("market case input must contain one row per state")
    normalized["state"] = normalized["state"].astype(str).str.strip()
    normalized["outcome_value"] = pd.to_numeric(
        normalized["outcome_value"], errors="raise"
    )
    if not normalized["outcome_value"].isin([0.0, 1.0]).all():
        raise ValueError("market outcome values must be binary")
    return normalized.set_index("state", drop=False)


def fetch_poll_average_rows(*, client: httpx.Client | None = None) -> list[dict[str, Any]]:
    """Fetch the public 538 polling-average CSV."""

    own_client = client is None
    http_client = client or httpx.Client(timeout=30.0)
    try:
        response = http_client.get(FIVETHIRTYEIGHT_POLL_AVERAGES_URL)
        response.raise_for_status()
        return pd.read_csv(io.StringIO(response.text)).to_dict(orient="records")
    finally:
        if own_client:
            http_client.close()


def build_poll_panel(
    *, poll_rows: Sequence[dict[str, Any]], market_cases: pd.DataFrame
) -> pd.DataFrame:
    """Build valid state-date REP/DEM poll-derived probability rows."""

    frame = pd.DataFrame(poll_rows)
    required = {"date", "state", "cycle", "party", "pct_estimate"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"poll rows missing columns: {missing}")
    frame = frame.loc[
        (pd.to_numeric(frame["cycle"], errors="raise") == 2024)
        & frame["party"].astype(str).isin(["REP", "DEM"])
        & frame["state"].astype(str).isin(set(ALL_US_STATES))
        & frame["state"].astype(str).isin(set(market_cases.index))
    ].copy()
    frame["date"] = frame["date"].astype(str)
    frame = frame.loc[(frame["date"] >= START_DATE) & (frame["date"] <= END_DATE)]
    frame["pct_estimate"] = pd.to_numeric(frame["pct_estimate"], errors="raise")
    if not frame["pct_estimate"].between(0.0, 100.0).all():
        raise ValueError("poll pct_estimate values must be in [0, 100]")

    pivot = (
        frame.pivot_table(
            index=["date", "state"],
            columns="party",
            values="pct_estimate",
            aggfunc="first",
        )
        .reset_index()
        .rename(columns={"REP": "poll_republican_pct", "DEM": "poll_democratic_pct"})
    )
    pivot = pivot.dropna(subset=["poll_republican_pct", "poll_democratic_pct"]).copy()
    if pivot.empty:
        raise ValueError("poll panel has no state-date REP/DEM pairs")
    pivot["poll_margin_republican_minus_democratic"] = (
        pivot["poll_republican_pct"] - pivot["poll_democratic_pct"]
    )
    pivot["poll_derived_probability"] = pivot[
        "poll_margin_republican_minus_democratic"
    ].map(transformed_margin_probability)
    pivot["forecast_timestamp_utc"] = pivot["date"].map(_date_to_forecast_timestamp)
    pivot["poll_error_mae_points"] = POLL_ERROR_MAE_POINTS
    pivot["poll_error_sigma_points"] = poll_error_sigma_points()
    pivot["poll_transform_name"] = "normal_margin_error_from_538_poll_mae"
    return pivot.sort_values(["state", "date"]).reset_index(drop=True)


def fetch_history_by_state(
    *,
    client: httpx.Client,
    poll_panel: pd.DataFrame,
    market_cases: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Fetch bounded CLOB history chunks for each state in the poll panel."""

    histories: dict[str, pd.DataFrame] = {}
    for state in sorted(poll_panel["state"].unique()):
        token_id = str(market_cases.loc[state, "target_token_id"])
        histories[state] = fetch_history_for_token(
            client=client,
            token_id=token_id,
            start_date=str(poll_panel.loc[poll_panel["state"] == state, "date"].min()),
            end_date=str(poll_panel.loc[poll_panel["state"] == state, "date"].max()),
        )
    return histories


def fetch_history_for_token(
    *,
    client: httpx.Client,
    token_id: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Fetch price history in API-safe chunks for one CLOB token."""

    start_ts = pd.Timestamp(f"{start_date}T00:00:00Z")
    end_ts = pd.Timestamp(f"{end_date}T23:59:59Z")
    cursor = start_ts
    rows: list[dict[str, Any]] = []
    while cursor < end_ts:
        chunk_end = min(cursor + pd.Timedelta(days=HISTORY_CHUNK_DAYS), end_ts)
        response = client.get(
            f"{CLOB_BASE_URL}/prices-history",
            params={
                "market": token_id,
                "startTs": int(cursor.timestamp()),
                "endTs": int(chunk_end.timestamp()),
                "fidelity": HISTORY_FIDELITY_MINUTES,
            },
        )
        response.raise_for_status()
        payload = response.json()
        history = payload.get("history") if isinstance(payload, dict) else None
        if isinstance(history, list):
            for point in history:
                if not isinstance(point, dict):
                    continue
                timestamp_value = point.get("t", point.get("timestamp"))
                price_value = point.get("p", point.get("price"))
                if timestamp_value is None or price_value is None:
                    continue
                rows.append(
                    {
                        "observed_at_utc": _history_timestamp(timestamp_value),
                        "price": float(price_value),
                    }
                )
        cursor = chunk_end + pd.Timedelta(seconds=1)
    if not rows:
        return pd.DataFrame(columns=["observed_at_utc", "price"])
    history_frame = pd.DataFrame(rows).drop_duplicates()
    history_frame["price"] = pd.to_numeric(history_frame["price"], errors="raise")
    if not history_frame["price"].between(0.0, 1.0).all():
        raise ValueError("CLOB history prices must be in [0, 1]")
    return history_frame.sort_values("observed_at_utc").reset_index(drop=True)


def build_panel_cases(
    *,
    poll_panel: pd.DataFrame,
    market_cases: pd.DataFrame,
    history_by_state: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Match poll-derived rows to nearest Polymarket history points."""

    rows: list[dict[str, Any]] = []
    for _, poll in poll_panel.iterrows():
        state = str(poll["state"])
        history = history_by_state.get(state, pd.DataFrame())
        if history.empty:
            continue
        target_ts = pd.Timestamp(poll["forecast_timestamp_utc"]).tz_convert("UTC")
        nearest_idx = (history["observed_at_utc"] - target_ts).abs().idxmin()
        price = history.loc[nearest_idx]
        distance = abs((pd.Timestamp(price["observed_at_utc"]) - target_ts).total_seconds())
        if distance > MAX_PANEL_PRICE_DISTANCE_SECONDS:
            continue
        outcome = float(market_cases.loc[state, "outcome_value"])
        pm_probability = float(price["price"])
        poll_probability = float(poll["poll_derived_probability"])
        pm_brier = (pm_probability - outcome) ** 2
        poll_brier = (poll_probability - outcome) ** 2
        if pm_brier < poll_brier:
            lower = "polymarket"
        elif poll_brier < pm_brier:
            lower = "poll_derived_forecast"
        else:
            lower = "tie"
        forecast_date = str(poll["date"])
        rows.append(
            {
                "case_id": f"us_2024_{_slugify_state(state)}_{forecast_date}_rep_panel",
                "state": state,
                "forecast_date": forecast_date,
                "forecast_timestamp_utc": _format_timestamp(target_ts),
                "polymarket_observed_at_utc": _format_timestamp(price["observed_at_utc"]),
                "polymarket_time_distance_seconds": int(distance),
                "polymarket_market_slug": str(market_cases.loc[state, "polymarket_market_slug"]),
                "polymarket_market_id": str(market_cases.loc[state, "polymarket_market_id"]),
                "polymarket_condition_id": str(market_cases.loc[state, "polymarket_condition_id"]),
                "target_outcome": "Republican wins state",
                "target_token_id": str(market_cases.loc[state, "target_token_id"]),
                "outcome_value": outcome,
                "poll_republican_pct": float(poll["poll_republican_pct"]),
                "poll_democratic_pct": float(poll["poll_democratic_pct"]),
                "poll_margin_republican_minus_democratic": float(
                    poll["poll_margin_republican_minus_democratic"]
                ),
                "poll_error_mae_points": POLL_ERROR_MAE_POINTS,
                "poll_error_sigma_points": poll_error_sigma_points(),
                "poll_transform_name": "normal_margin_error_from_538_poll_mae",
                "poll_derived_probability": poll_probability,
                "polymarket_probability": pm_probability,
                "polymarket_brier": pm_brier,
                "poll_derived_brier": poll_brier,
                "loss_advantage": poll_brier - pm_brier,
                "lower_loss_source": lower,
                "poll_average_source_url": FIVETHIRTYEIGHT_POLL_AVERAGES_URL,
                "poll_error_source_url": FIVETHIRTYEIGHT_POLL_ERROR_SOURCE_URL,
                "price_history_source_url": f"{CLOB_BASE_URL}/prices-history",
                "row_unit": "state_date_forecast_pair",
                "allowed_interpretation": (
                    "Repeated state-date Brier comparison between Polymarket "
                    "Republican-win prices and transformed 538 polling averages."
                ),
                "limitation": (
                    "Panel rows repeat the same resolved state outcomes over "
                    "many dates; they are forecast rows, not independent elections."
                ),
            }
        )
    return pd.DataFrame(rows, columns=CASE_COLUMNS)


def validate_panel_cases(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate state-date panel case rows."""

    missing = sorted(set(CASE_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"panel cases missing columns: {missing}")
    forbidden = [
        column
        for column in frame.columns
        if any(token in column.lower() for token in ("wallet", "maker", "taker", "address"))
    ]
    if forbidden:
        raise ValueError(f"panel cases contain forbidden raw-trade columns: {forbidden}")
    normalized = frame.loc[:, list(CASE_COLUMNS)].copy()
    if normalized.empty:
        raise ValueError("panel cases must not be empty")
    for column in (
        "polymarket_time_distance_seconds",
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
    if not normalized["outcome_value"].isin([0.0, 1.0]).all():
        raise ValueError("outcome values must be binary")
    for column in ("poll_derived_probability", "polymarket_probability"):
        if not normalized[column].between(0.0, 1.0).all():
            raise ValueError(f"{column} values must be in [0, 1]")
    if (normalized["polymarket_time_distance_seconds"] > MAX_PANEL_PRICE_DISTANCE_SECONDS).any():
        raise ValueError("panel price match exceeds maximum distance")
    expected_pm = (normalized["polymarket_probability"] - normalized["outcome_value"]) ** 2
    expected_poll = (normalized["poll_derived_probability"] - normalized["outcome_value"]) ** 2
    if not (normalized["polymarket_brier"].sub(expected_pm).abs() <= 1e-12).all():
        raise ValueError("polymarket_brier must equal squared forecast error")
    if not (normalized["poll_derived_brier"].sub(expected_poll).abs() <= 1e-12).all():
        raise ValueError("poll_derived_brier must equal squared forecast error")
    if normalized["case_id"].duplicated().any():
        raise ValueError("panel case_id values must be unique")
    return normalized.sort_values(["state", "forecast_date"]).reset_index(drop=True)


def build_panel_summary(*, cases: pd.DataFrame, poll_panel: pd.DataFrame) -> pd.DataFrame:
    """Build compact state-date panel summary rows."""

    counts = cases["lower_loss_source"].value_counts()
    pm_lower = int(counts.get("polymarket", 0))
    poll_lower = int(counts.get("poll_derived_forecast", 0))
    ties = int(counts.get("tie", 0))
    case_count = int(len(cases))
    mean_pm = float(cases["polymarket_brier"].mean())
    mean_poll = float(cases["poll_derived_brier"].mean())
    rows = [
        _summary_row("poll_panel_candidate_pair_count", len(poll_panel), "state-date rows", "Valid 538 REP/DEM state-date pairs before price matching."),
        _summary_row("matched_case_count", case_count, "state-date rows", "State-date rows with a nearby Polymarket history point."),
        _summary_row("matched_state_count", cases["state"].nunique(), "states", "States represented in matched panel rows."),
        _summary_row("matched_date_count", cases["forecast_date"].nunique(), "dates", "Forecast dates represented in matched panel rows."),
        _summary_row("independent_state_outcome_count", cases["state"].nunique(), "states", "Resolved state outcomes represented; panel rows are repeated forecasts."),
        _summary_row("polymarket_lower_loss_count", pm_lower, "state-date rows", "Rows where Polymarket has lower Brier loss."),
        _summary_row("poll_derived_lower_loss_count", poll_lower, "state-date rows", "Rows where transformed 538 polling average has lower Brier loss."),
        _summary_row("tie_count", ties, "state-date rows", "Rows with equal Brier loss."),
        _summary_row("polymarket_better_share", pm_lower / case_count, "share", "Share of matched panel rows where Polymarket has lower loss."),
        _summary_row("mean_polymarket_brier", mean_pm, "brier", "Mean Polymarket Brier loss across matched panel rows."),
        _summary_row("mean_poll_derived_brier", mean_poll, "brier", "Mean transformed 538 poll-derived Brier loss across matched panel rows."),
        _summary_row("mean_loss_advantage", mean_poll - mean_pm, "brier", "Positive means Polymarket has lower mean Brier; negative means poll-derived has lower mean Brier."),
        _summary_row("aggregate_mean_supports_polymarket", float(mean_pm < mean_poll), "binary", "Whether aggregate mean Brier is lower for Polymarket."),
        _summary_row("majority_rows_support_polymarket", float(pm_lower > poll_lower and pm_lower > case_count / 2), "binary", "Whether Polymarket has lower loss in a majority of matched rows."),
        _summary_row("broad_many_cases_claim_supported", 0.0, "binary", "Repeated state-date rows do not prove broad independent many-cases support."),
    ]
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def build_state_summary(*, cases: pd.DataFrame, poll_panel: pd.DataFrame) -> pd.DataFrame:
    """Build per-state panel summaries."""

    poll_counts = poll_panel.groupby("state").size()
    rows: list[dict[str, Any]] = []
    for state, group in cases.groupby("state", sort=True):
        counts = group["lower_loss_source"].value_counts()
        case_count = int(len(group))
        pm_lower = int(counts.get("polymarket", 0))
        poll_lower = int(counts.get("poll_derived_forecast", 0))
        ties = int(counts.get("tie", 0))
        rows.append(
            {
                "state": state,
                "poll_pair_count": int(poll_counts.get(state, 0)),
                "matched_case_count": case_count,
                "matched_date_count": int(group["forecast_date"].nunique()),
                "polymarket_lower_loss_count": pm_lower,
                "poll_derived_lower_loss_count": poll_lower,
                "tie_count": ties,
                "polymarket_better_share": pm_lower / case_count,
                "mean_polymarket_brier": float(group["polymarket_brier"].mean()),
                "mean_poll_derived_brier": float(group["poll_derived_brier"].mean()),
                "mean_loss_advantage": float(group["loss_advantage"].mean()),
                "first_matched_date": str(group["forecast_date"].min()),
                "last_matched_date": str(group["forecast_date"].max()),
            }
        )
    return pd.DataFrame(rows, columns=STATE_SUMMARY_COLUMNS)


def build_coverage(
    *,
    poll_panel: pd.DataFrame,
    cases: pd.DataFrame,
    history_by_state: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Build state-level coverage diagnostics for the panel."""

    rows: list[dict[str, Any]] = []
    poll_counts = poll_panel.groupby("state").size()
    case_counts = cases.groupby("state").size()
    for state in sorted(set(poll_panel["state"])):
        history = history_by_state.get(state, pd.DataFrame())
        poll_count = int(poll_counts.get(state, 0))
        matched = int(case_counts.get(state, 0))
        if history.empty:
            first_history = ""
            last_history = ""
            history_count = 0
        else:
            first_history = _format_timestamp(history["observed_at_utc"].min())
            last_history = _format_timestamp(history["observed_at_utc"].max())
            history_count = int(len(history))
        rows.append(
            {
                "state": state,
                "poll_pair_count": poll_count,
                "history_point_count": history_count,
                "matched_case_count": matched,
                "unmatched_poll_pair_count": poll_count - matched,
                "first_history_timestamp_utc": first_history,
                "last_history_timestamp_utc": last_history,
                "coverage_status": "matched" if matched else "no_price_history_match",
            }
        )
    return pd.DataFrame(rows, columns=COVERAGE_COLUMNS)


def write_panel_figure(
    *,
    cases: pd.DataFrame,
    summary: pd.DataFrame,
    state_summary: pd.DataFrame,
    coverage: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write the state-date panel diagnostic figure."""

    values = _summary_values(summary)
    fig, axes = plt.subplots(2, 2, figsize=(14.2, 9.6))
    fig.suptitle(
        "H1 State-Date Poll Panel: Polymarket vs 538 Poll-Derived Probability",
        fontsize=14,
        fontweight="bold",
    )

    axes[0, 0].bar(
        ["Polymarket", "538 poll-derived"],
        [values["mean_polymarket_brier"], values["mean_poll_derived_brier"]],
        color=["#2563eb", "#7c3aed"],
    )
    axes[0, 0].set_ylabel("Mean Brier loss")
    axes[0, 0].set_title("Aggregate panel loss")
    axes[0, 0].grid(True, axis="y", alpha=0.25)
    for idx, value in enumerate([values["mean_polymarket_brier"], values["mean_poll_derived_brier"]]):
        axes[0, 0].text(idx, value + 0.004, f"{value:.4f}", ha="center", fontsize=9)

    count_values = [
        values["polymarket_lower_loss_count"],
        values["poll_derived_lower_loss_count"],
        values["tie_count"],
    ]
    axes[0, 1].bar(
        ["PM lower", "Poll-derived lower", "Tie"],
        count_values,
        color=["#2563eb", "#7c3aed", "#9ca3af"],
    )
    axes[0, 1].set_title("Lower-loss row counts")
    axes[0, 1].set_ylabel("State-date rows")
    axes[0, 1].grid(True, axis="y", alpha=0.25)
    for idx, value in enumerate(count_values):
        axes[0, 1].text(idx, value + max(count_values) * 0.015, f"{int(value)}", ha="center", fontsize=9)

    ordered = state_summary.sort_values("mean_loss_advantage")
    y = list(range(len(ordered)))
    axes[1, 0].barh(y, ordered["mean_loss_advantage"], color=[
        "#2563eb" if value > 0 else "#7c3aed" for value in ordered["mean_loss_advantage"]
    ])
    axes[1, 0].axvline(0, color="#111827", linewidth=0.9)
    axes[1, 0].set_yticks(y, ordered["state"])
    axes[1, 0].invert_yaxis()
    axes[1, 0].set_xlabel("Mean loss advantage (poll-derived Brier - PM Brier)")
    axes[1, 0].set_title("State-level aggregate advantage")
    axes[1, 0].grid(True, axis="x", alpha=0.25)

    coverage_ordered = coverage.sort_values("matched_case_count", ascending=True)
    axes[1, 1].barh(
        range(len(coverage_ordered)),
        coverage_ordered["matched_case_count"],
        color="#475569",
        alpha=0.82,
    )
    axes[1, 1].set_yticks(range(len(coverage_ordered)), coverage_ordered["state"])
    axes[1, 1].set_xlabel("Matched state-date rows")
    axes[1, 1].set_title("Panel coverage by state")
    axes[1, 1].grid(True, axis="x", alpha=0.25)

    fig.text(
        0.5,
        0.012,
        (
            "Rows are repeated forecasts for 15 resolved state outcomes. "
            "Poll averages are transformed with the documented normal-error model; "
            "this is not a raw-poll probability claim."
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


def build_metadata(
    *,
    source: str,
    cases: pd.DataFrame,
    summary: pd.DataFrame,
    state_summary: pd.DataFrame,
    coverage: pd.DataFrame,
    market_case_input: Path,
    cases_output: Path,
    summary_output: Path,
    state_summary_output: Path,
    coverage_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for the H1 state poll panel."""

    values = _summary_values(summary)
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_state_date_poll_panel_extension",
            "calculation_scope": "deterministic_python_from_538_poll_average_panel_and_public_clob_history",
            "source": source,
            "start_date": START_DATE,
            "end_date": END_DATE,
            "poll_error_mae_points": POLL_ERROR_MAE_POINTS,
            "poll_error_sigma_points": poll_error_sigma_points(),
            "poll_error_sigma_formula": "sigma = mae / sqrt(2/pi)",
            "poll_transform_name": "normal_margin_error_from_538_poll_mae",
            "raw_poll_average_used_directly_as_probability": False,
            "rcp_included": False,
            "price_history_chunk_days": HISTORY_CHUNK_DAYS,
            "price_history_fidelity_minutes": HISTORY_FIDELITY_MINUTES,
            "max_price_distance_seconds": MAX_PANEL_PRICE_DISTANCE_SECONDS,
            "read_only_public_endpoints": source == "live",
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
        },
        "outputs": {
            "poll_panel_candidate_pair_count": int(values["poll_panel_candidate_pair_count"]),
            "matched_case_count": int(values["matched_case_count"]),
            "matched_state_count": int(values["matched_state_count"]),
            "matched_date_count": int(values["matched_date_count"]),
            "independent_state_outcome_count": int(values["independent_state_outcome_count"]),
            "polymarket_lower_loss_count": int(values["polymarket_lower_loss_count"]),
            "poll_derived_lower_loss_count": int(values["poll_derived_lower_loss_count"]),
            "tie_count": int(values["tie_count"]),
            "mean_polymarket_brier": float(values["mean_polymarket_brier"]),
            "mean_poll_derived_brier": float(values["mean_poll_derived_brier"]),
            "mean_loss_advantage": float(values["mean_loss_advantage"]),
            "aggregate_mean_supports_polymarket": bool(values["aggregate_mean_supports_polymarket"]),
            "majority_rows_support_polymarket": bool(values["majority_rows_support_polymarket"]),
            "broad_many_cases_claim_supported": bool(values["broad_many_cases_claim_supported"]),
            "state_summary_rows": int(len(state_summary)),
            "coverage_rows": int(len(coverage)),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
            "h1_goal_completion_status": "not_proven",
        },
        "source_paths": {
            "market_case_input": str(market_case_input),
            "cases": str(cases_output),
            "summary": str(summary_output),
            "state_summary": str(state_summary_output),
            "coverage": str(coverage_output),
            "figure": str(figure_output),
        },
        "source_urls": {
            "poll_average_source": FIVETHIRTYEIGHT_POLL_AVERAGES_URL,
            "poll_error_source": FIVETHIRTYEIGHT_POLL_ERROR_SOURCE_URL,
            "clob_prices_history": f"{CLOB_BASE_URL}/prices-history",
        },
        "limitations": {
            "panel_rows_are_not_independent_elections": True,
            "state_rows_share_one_election_context": True,
            "poll_transform_is_documented_but_model_assumption": True,
            "not_official_538_state_win_forecast": True,
            "not_raw_poll_comparison": True,
            "no_causal_or_tradeability_claim": True,
            "goal_many_cases_claim_not_proven": True,
        },
    }


def mock_poll_average_rows() -> list[dict[str, Any]]:
    """Small poll-average fixture for tests and offline generation."""

    rows: list[dict[str, Any]] = []
    specs = [
        ("Arizona", "2024-03-08", 47.0, 45.0),
        ("Arizona", "2024-03-09", 47.2, 45.1),
        ("Michigan", "2024-03-08", 45.0, 46.0),
        ("Michigan", "2024-03-09", 45.2, 46.1),
        ("Texas", "2024-03-08", 50.0, 43.0),
        ("Texas", "2024-03-09", 50.2, 43.1),
    ]
    for state, date, rep, dem in specs:
        rows.append({"date": date, "state": state, "cycle": 2024, "party": "REP", "pct_estimate": rep})
        rows.append({"date": date, "state": state, "cycle": 2024, "party": "DEM", "pct_estimate": dem})
    return rows


def mock_history_by_state(poll_panel: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return deterministic daily price history for mock panel states."""

    prices = {"Arizona": 0.62, "Michigan": 0.40, "Texas": 0.85}
    histories: dict[str, pd.DataFrame] = {}
    for state, group in poll_panel.groupby("state"):
        rows = [
            {
                "observed_at_utc": pd.Timestamp(f"{date}T00:00:02Z"),
                "price": prices[str(state)],
            }
            for date in sorted(group["date"].unique())
        ]
        histories[str(state)] = pd.DataFrame(rows)
    return histories


def _summary_row(
    summary_id: str,
    value: float | int,
    unit: str,
    description: str,
) -> dict[str, Any]:
    return {
        "summary_id": summary_id,
        "value": value,
        "unit": unit,
        "description": description,
    }


def _summary_values(summary: pd.DataFrame) -> dict[str, float]:
    return {
        str(row["summary_id"]): float(row["value"])
        for _, row in summary.iterrows()
    }


def _date_to_forecast_timestamp(date_value: str) -> str:
    return f"{date_value}T{POLL_PANEL_TIMESTAMP_HOUR_UTC:02d}:00:00Z"


def _history_timestamp(value: Any) -> pd.Timestamp:
    timestamp = float(value)
    if timestamp > 10_000_000_000:
        timestamp = timestamp / 1000.0
    return pd.Timestamp(datetime.fromtimestamp(timestamp, tz=UTC))


def _format_timestamp(value: Any) -> str:
    return pd.Timestamp(value).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def _slugify_state(state: str) -> str:
    return state.lower().replace(" ", "_")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("mock", "live"), default="mock")
    parser.add_argument("--market-case-input", type=Path, default=MARKET_CASE_INPUT)
    parser.add_argument("--cases-output", type=Path, default=CASE_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--state-summary-output", type=Path, default=STATE_SUMMARY_OUTPUT)
    parser.add_argument("--coverage-output", type=Path, default=COVERAGE_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_state_poll_panel_outputs(
            source=args.source,
            market_case_input=args.market_case_input,
            cases_output=args.cases_output,
            summary_output=args.summary_output,
            state_summary_output=args.state_summary_output,
            coverage_output=args.coverage_output,
            figure_output=args.figure_output,
            metadata_output=args.metadata_output,
        )
    except (FileNotFoundError, ValueError, KeyError, httpx.HTTPError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
