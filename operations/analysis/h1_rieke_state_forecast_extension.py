"""Build an H1 50-state final forecast extension.

This module compares Polymarket Republican-win state probabilities with a
poll-based traditional forecast from Mark Rieke's 2024 presidential forecast.
The Rieke model output reports Harris' probability of winning each state; this
module compares the complement to Republican-wins Polymarket markets at the
forecast run timestamp.
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
    GAMMA_BASE_URL,
    MAX_PRICE_TIME_DISTANCE_SECONDS,
    POLYMARKET_STATE_MARKET_SLUGS,
    REPUBLICAN_WON_2024_STATES,
    fetch_nearest_price,
    target_token_id,
)
from operations.analysis.run_h2_event_windows import RESULTS_DIR


RIEKE_REPO_URL = "https://github.com/markjrieke/2024-potus"
RIEKE_WIN_STATE_URL = (
    "https://raw.githubusercontent.com/markjrieke/2024-potus/main/"
    "out/polls/win_state.csv"
)
RIEKE_MODEL_LOG_URL = (
    "https://raw.githubusercontent.com/markjrieke/2024-potus/main/out/model_log.csv"
)

CASE_OUTPUT = RESULTS_DIR / "h1_rieke_state_forecast_cases.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_rieke_state_forecast_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_rieke_state_forecast.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_rieke_state_forecast_metadata.json"

CASE_COLUMNS: tuple[str, ...] = (
    "case_id",
    "state",
    "forecast_timestamp_utc",
    "rieke_run_date",
    "polymarket_observed_at_utc",
    "polymarket_time_distance_seconds",
    "polymarket_market_slug",
    "polymarket_market_id",
    "polymarket_condition_id",
    "target_outcome",
    "target_token_id",
    "outcome_value",
    "rieke_harris_win_probability",
    "rieke_republican_win_probability",
    "polymarket_probability",
    "polymarket_brier",
    "rieke_brier",
    "loss_advantage",
    "lower_loss_source",
    "rieke_win_state_source_url",
    "rieke_model_log_source_url",
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
class H1RiekeStateForecastResult:
    """Summary of generated Rieke state-forecast H1 artifacts."""

    cases_path: Path
    summary_path: Path
    figure_path: Path
    metadata_path: Path
    case_count: int
    polymarket_lower_loss_count: int
    rieke_lower_loss_count: int
    mean_polymarket_brier: float
    mean_rieke_brier: float

    def to_dict(self) -> dict[str, float | int | str]:
        return {
            "cases_path": str(self.cases_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "case_count": self.case_count,
            "polymarket_lower_loss_count": self.polymarket_lower_loss_count,
            "rieke_lower_loss_count": self.rieke_lower_loss_count,
            "mean_polymarket_brier": self.mean_polymarket_brier,
            "mean_rieke_brier": self.mean_rieke_brier,
        }


def generate_h1_rieke_state_forecast_outputs(
    *,
    source: str = "mock",
    cases_output: Path = CASE_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
    run_date: str | None = None,
    client: httpx.Client | None = None,
) -> H1RiekeStateForecastResult:
    """Generate the 50-state Rieke-vs-Polymarket final forecast extension."""

    if source not in {"mock", "live"}:
        raise ValueError("source must be either 'mock' or 'live'")
    own_client = client is None
    http_client = client or httpx.Client(timeout=25.0)
    try:
        win_state_rows = (
            mock_rieke_win_state_rows()
            if source == "mock"
            else fetch_rieke_win_state_rows(http_client)
        )
        model_log_rows = (
            mock_rieke_model_log_rows()
            if source == "mock"
            else fetch_rieke_model_log_rows(http_client)
        )
        win_state = parse_rieke_win_state(win_state_rows)
        model_log = parse_rieke_model_log(model_log_rows)
        selected_run_date = run_date or str(win_state["run_date"].max())
        forecast_ts = rieke_forecast_timestamp(model_log, selected_run_date)
        rows = [
            build_rieke_state_case_row(
                state=state,
                source=source,
                win_state=win_state,
                run_date=selected_run_date,
                forecast_ts=forecast_ts,
                client=http_client,
            )
            for state in ALL_US_STATES
        ]
    finally:
        if own_client:
            http_client.close()

    cases = validate_rieke_state_cases(pd.DataFrame(rows, columns=CASE_COLUMNS))
    summary = build_rieke_state_summary(cases)
    cases_output.parent.mkdir(parents=True, exist_ok=True)
    cases.to_csv(cases_output, index=False)
    summary.to_csv(summary_output, index=False)
    write_rieke_state_forecast_figure(cases=cases, output_path=figure_output)
    metadata = build_rieke_state_metadata(
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
    return H1RiekeStateForecastResult(
        cases_path=cases_output,
        summary_path=summary_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        case_count=int(values["case_count"]),
        polymarket_lower_loss_count=int(values["polymarket_lower_loss_count"]),
        rieke_lower_loss_count=int(values["rieke_lower_loss_count"]),
        mean_polymarket_brier=float(values["mean_polymarket_brier"]),
        mean_rieke_brier=float(values["mean_rieke_brier"]),
    )


def fetch_rieke_win_state_rows(client: httpx.Client) -> list[dict[str, Any]]:
    response = client.get(RIEKE_WIN_STATE_URL)
    response.raise_for_status()
    return pd.read_csv(io.StringIO(response.text)).to_dict(orient="records")


def fetch_rieke_model_log_rows(client: httpx.Client) -> list[dict[str, Any]]:
    response = client.get(RIEKE_MODEL_LOG_URL)
    response.raise_for_status()
    return pd.read_csv(io.StringIO(response.text)).to_dict(orient="records")


def parse_rieke_win_state(rows: Sequence[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    required = {"state", "p_win", "run_date"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Rieke win_state rows missing columns: {missing}")
    normalized = frame.loc[:, ["state", "p_win", "run_date"]].copy()
    normalized["state"] = normalized["state"].astype(str).str.strip()
    normalized["p_win"] = pd.to_numeric(normalized["p_win"], errors="raise")
    if not normalized["p_win"].between(0.0, 1.0).all():
        raise ValueError("Rieke p_win values must be in [0, 1]")
    normalized["run_date"] = normalized["run_date"].astype(str).str.strip()
    return normalized


def parse_rieke_model_log(rows: Sequence[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    required = {"model_name", "end_ts", "run_date"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Rieke model_log rows missing columns: {missing}")
    normalized = frame.loc[:, ["model_name", "end_ts", "run_date"]].copy()
    normalized["model_name"] = normalized["model_name"].astype(str).str.strip()
    normalized["run_date"] = normalized["run_date"].astype(str).str.strip()
    pd.to_datetime(normalized["end_ts"], errors="raise", utc=True)
    return normalized


def rieke_forecast_timestamp(model_log: pd.DataFrame, run_date: str) -> pd.Timestamp:
    rows = model_log.loc[
        (model_log["model_name"] == "polls") & (model_log["run_date"] == run_date)
    ].copy()
    if rows.empty:
        raise ValueError(f"No Rieke polls model_log row found for run_date={run_date}")
    rows["end_ts_parsed"] = pd.to_datetime(rows["end_ts"], utc=True)
    return pd.Timestamp(rows.sort_values("end_ts_parsed").iloc[-1]["end_ts_parsed"])


def build_rieke_state_case_row(
    *,
    state: str,
    source: str,
    win_state: pd.DataFrame,
    run_date: str,
    forecast_ts: pd.Timestamp,
    client: httpx.Client,
) -> dict[str, Any]:
    state_rows = win_state.loc[
        (win_state["state"] == state) & (win_state["run_date"] == run_date)
    ]
    if len(state_rows) != 1:
        raise ValueError(f"Expected one Rieke state row for {state} on {run_date}")
    rieke_harris = float(state_rows.iloc[0]["p_win"])
    rieke_republican = 1.0 - rieke_harris
    market = (
        mock_gamma_market(state)
        if source == "mock"
        else fetch_gamma_market_by_slug(client, POLYMARKET_STATE_MARKET_SLUGS[state])
    )
    token_id = target_token_id(market, "Yes")
    price = (
        mock_price_point(state, forecast_ts=forecast_ts)
        if source == "mock"
        else fetch_nearest_price(
            client,
            token_id=token_id,
            target_ts=forecast_ts,
            max_distance_seconds=MAX_PRICE_TIME_DISTANCE_SECONDS,
        )
    )
    pm_probability = float(price["price"])
    outcome = 1.0 if state in REPUBLICAN_WON_2024_STATES else 0.0
    pm_brier = (pm_probability - outcome) ** 2
    rieke_brier = (rieke_republican - outcome) ** 2
    if pm_brier < rieke_brier:
        lower_loss_source = "polymarket"
    elif rieke_brier < pm_brier:
        lower_loss_source = "rieke_forecast"
    else:
        lower_loss_source = "tie"
    observed_ts = pd.Timestamp(price["observed_at_utc"]).tz_convert("UTC")
    market_slug = str(market.get("slug", ""))
    return {
        "case_id": f"us_2024_president_{_slugify_state(state)}_rieke_republican",
        "state": state,
        "forecast_timestamp_utc": _format_timestamp(forecast_ts),
        "rieke_run_date": run_date,
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
        "rieke_harris_win_probability": rieke_harris,
        "rieke_republican_win_probability": rieke_republican,
        "polymarket_probability": pm_probability,
        "polymarket_brier": pm_brier,
        "rieke_brier": rieke_brier,
        "loss_advantage": rieke_brier - pm_brier,
        "lower_loss_source": lower_loss_source,
        "rieke_win_state_source_url": RIEKE_WIN_STATE_URL,
        "rieke_model_log_source_url": RIEKE_MODEL_LOG_URL,
        "polymarket_source_url": f"https://polymarket.com/market/{market_slug}",
        "price_history_source_url": f"{CLOB_BASE_URL}/prices-history",
        "allowed_interpretation": (
            "Final-snapshot state-level Brier comparison between Polymarket "
            "Republican-win prices and the complement of Rieke Harris-win "
            "state probabilities."
        ),
        "limitation": (
            "Rieke is an independent poll-based forecast model, not an official "
            "538 forecast and not raw poll shares; state outcomes share one "
            "election context."
        ),
    }


def fetch_gamma_market_by_slug(client: httpx.Client, market_slug: str) -> dict[str, Any]:
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


def validate_rieke_state_cases(frame: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in CASE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Rieke state forecast cases missing columns: {missing}")
    forbidden = [column for column in frame.columns if "wallet" in column.lower()]
    if forbidden:
        raise ValueError(f"Rieke state cases must not contain wallet columns: {forbidden}")
    normalized = frame.loc[:, list(CASE_COLUMNS)].copy()
    for column in (
        "outcome_value",
        "rieke_harris_win_probability",
        "rieke_republican_win_probability",
        "polymarket_probability",
        "polymarket_brier",
        "rieke_brier",
        "loss_advantage",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    for column in (
        "outcome_value",
        "rieke_harris_win_probability",
        "rieke_republican_win_probability",
        "polymarket_probability",
    ):
        if not normalized[column].between(0.0, 1.0).all():
            raise ValueError(f"{column} values must be in [0, 1]")
    if len(normalized) != len(ALL_US_STATES):
        raise ValueError("Rieke state forecast cases must contain 50 state rows")
    if set(normalized["state"]) != set(ALL_US_STATES):
        raise ValueError("Rieke state forecast cases do not match the 50-state universe")
    if normalized["case_id"].duplicated().any():
        raise ValueError("Rieke state forecast case ids must be unique")
    if (
        pd.to_numeric(
            normalized["polymarket_time_distance_seconds"],
            errors="raise",
        )
        > MAX_PRICE_TIME_DISTANCE_SECONDS
    ).any():
        raise ValueError("Polymarket price point is too far from forecast timestamp")
    return normalized.sort_values("state").reset_index(drop=True)


def build_rieke_state_summary(cases: pd.DataFrame) -> pd.DataFrame:
    pm_lower = int((cases["lower_loss_source"] == "polymarket").sum())
    rieke_lower = int((cases["lower_loss_source"] == "rieke_forecast").sum())
    ties = int((cases["lower_loss_source"] == "tie").sum())
    mean_pm = float(cases["polymarket_brier"].mean())
    mean_rieke = float(cases["rieke_brier"].mean())
    rows = [
        ("case_count", len(cases), "cases", "Resolved 50-state final forecast outcomes."),
        (
            "independent_resolved_outcome_count",
            len(cases),
            "outcomes",
            "Each row is a distinct 2024 presidential state outcome.",
        ),
        ("polymarket_lower_loss_count", pm_lower, "cases", "Cases where Polymarket has lower Brier loss."),
        ("rieke_lower_loss_count", rieke_lower, "cases", "Cases where Rieke forecast has lower Brier loss."),
        ("tie_count", ties, "cases", "Cases with equal Brier loss."),
        ("polymarket_better_share", pm_lower / len(cases), "share", "Share of states where Polymarket loss is lower."),
        ("mean_polymarket_brier", mean_pm, "brier_score", "Mean Brier loss across Polymarket state snapshots."),
        ("mean_rieke_brier", mean_rieke, "brier_score", "Mean Brier loss across Rieke state probabilities."),
        ("mean_loss_advantage", mean_rieke - mean_pm, "brier_score", "Positive values mean lower mean Polymarket loss."),
    ]
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def write_rieke_state_forecast_figure(*, cases: pd.DataFrame, output_path: Path) -> Path:
    counts = cases["lower_loss_source"].value_counts()
    mean_pm = float(cases["polymarket_brier"].mean())
    mean_rieke = float(cases["rieke_brier"].mean())
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(13.6, 5.2),
        gridspec_kw={"width_ratios": [0.9, 1.25]},
    )
    fig.suptitle(
        "H1 50-State Final Forecast: Polymarket vs Rieke Poll-Based Model",
        fontsize=13.5,
        fontweight="bold",
    )
    axes[0].bar(
        ["Mean Brier\nPolymarket", "Mean Brier\nRieke"],
        [mean_pm, mean_rieke],
        color=["#2563eb", "#7c3aed"],
    )
    axes[0].set_ylabel("Mean Brier loss")
    axes[0].set_title("Aggregate loss across 50 states")
    axes[0].grid(True, axis="y", alpha=0.25)
    axes[0].text(0, mean_pm + 0.001, f"{mean_pm:.4f}", ha="center", fontsize=9)
    axes[0].text(1, mean_rieke + 0.001, f"{mean_rieke:.4f}", ha="center", fontsize=9)

    colors = cases["outcome_value"].map({1.0: "#2563eb", 0.0: "#f59e0b"})
    axes[1].scatter(
        cases["rieke_republican_win_probability"],
        cases["polymarket_probability"],
        c=colors,
        alpha=0.82,
        edgecolor="#111827",
        linewidth=0.35,
    )
    axes[1].plot([0, 1], [0, 1], color="#6b7280", linestyle="--", linewidth=1.0)
    axes[1].set_xlim(-0.03, 1.03)
    axes[1].set_ylim(-0.03, 1.03)
    axes[1].set_xlabel("Rieke Republican-win probability")
    axes[1].set_ylabel("Polymarket Republican-win probability")
    axes[1].set_title(
        "Head-to-head lower loss: "
        f"PM {int(counts.get('polymarket', 0))}, "
        f"Rieke {int(counts.get('rieke_forecast', 0))}"
    )
    axes[1].grid(True, alpha=0.25)
    axes[1].text(
        0.5,
        -0.23,
        "Blue points resolved Republican; orange points resolved Democratic. Lower mean loss does not imply lower loss in most states.",
        transform=axes[1].transAxes,
        ha="center",
        fontsize=8.7,
        color="#374151",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.1, 1, 0.9))
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return output_path


def build_rieke_state_metadata(
    *,
    source: str,
    cases: pd.DataFrame,
    summary: pd.DataFrame,
    cases_output: Path,
    summary_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    values = _summary_values(summary)
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_rieke_state_forecast_extension",
            "source": source,
            "target_event": "Republican wins state",
            "traditional_forecast_source": "markjrieke_2024_potus",
            "probability_transform": "republican_probability = 1 - harris_state_win_probability",
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
            "polymarket_lower_loss_count": int(values["polymarket_lower_loss_count"]),
            "rieke_lower_loss_count": int(values["rieke_lower_loss_count"]),
            "polymarket_better_share": float(values["polymarket_better_share"]),
            "mean_polymarket_brier": float(values["mean_polymarket_brier"]),
            "mean_rieke_brier": float(values["mean_rieke_brier"]),
            "mean_loss_advantage": float(values["mean_loss_advantage"]),
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
            "rieke_repository": RIEKE_REPO_URL,
            "rieke_win_state": RIEKE_WIN_STATE_URL,
            "rieke_model_log": RIEKE_MODEL_LOG_URL,
            "gamma_markets": f"{GAMMA_BASE_URL}/markets",
            "clob_prices_history": f"{CLOB_BASE_URL}/prices-history",
        },
        "states": cases["state"].tolist(),
        "limitations": {
            "state_outcomes_share_one_election_context": True,
            "rieke_model_is_independent_not_official_538": True,
            "not_raw_poll_comparison": True,
            "mean_loss_advantage_not_same_as_majority_of_states": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def mock_rieke_win_state_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for state in ALL_US_STATES:
        harris_probability = 0.2 if state in REPUBLICAN_WON_2024_STATES else 0.8
        rows.append({"state": state, "p_win": harris_probability, "run_date": "2024-11-05"})
    return rows


def mock_rieke_model_log_rows() -> list[dict[str, Any]]:
    return [
        {
            "model_name": "polls",
            "end_ts": "2024-11-05T13:22:58Z",
            "run_date": "2024-11-05",
        }
    ]


def mock_gamma_market(state: str) -> dict[str, Any]:
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
    parser.add_argument("--run-date", default=None)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_rieke_state_forecast_outputs(
            source=args.source,
            cases_output=args.cases_output,
            summary_output=args.summary_output,
            figure_output=args.figure_output,
            metadata_output=args.metadata_output,
            run_date=args.run_date,
        )
    except (httpx.HTTPError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
