"""Build a small H1 final-snapshot extension from public forecast cases.

This module compares Polymarket prices with the final 538 probability forecast
for resolved 2024 election outcomes: president, Senate control, House control,
and five Senate state races explicitly discussed in 538's final forecast
article. It is intentionally scoped as a final-snapshot extension, not a daily
time-series replacement and not a raw-poll comparison.
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

from operations.analysis.run_h2_event_windows import RESULTS_DIR


GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
CLOB_BASE_URL = "https://clob.polymarket.com"
FIVETHIRTYEIGHT_FINAL_FORECAST_URL = (
    "https://abcnews.com/538/538s-final-forecasts-2024-election/story?id=115511051"
)

CASE_OUTPUT = RESULTS_DIR / "h1_final_snapshot_cases.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_final_snapshot_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_final_snapshot.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_final_snapshot_metadata.json"

FINAL_FORECAST_TIMESTAMP_UTC = "2024-11-05T11:00:00Z"
MAX_PRICE_TIME_DISTANCE_SECONDS = 2 * 60 * 60

CASE_COLUMNS: tuple[str, ...] = (
    "case_id",
    "case_label",
    "forecast_timestamp_utc",
    "polymarket_observed_at_utc",
    "polymarket_time_distance_seconds",
    "polymarket_event_slug",
    "polymarket_market_slug",
    "polymarket_market_id",
    "polymarket_condition_id",
    "target_outcome",
    "target_token_id",
    "resolved_outcome",
    "outcome_value",
    "polymarket_probability",
    "traditional_source",
    "traditional_probability",
    "polymarket_brier",
    "traditional_brier",
    "loss_advantage",
    "lower_loss_source",
    "forecast_source_url",
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
class FinalSnapshotCaseSpec:
    """Curated final-snapshot case definition."""

    case_id: str
    case_label: str
    event_slug: str
    market_slug: str
    target_outcome: str
    traditional_probability: float
    resolved_outcome: str
    outcome_value: float = 1.0


@dataclass(frozen=True)
class H1FinalSnapshotResult:
    """Summary of generated H1 final-snapshot artifacts."""

    cases_path: Path
    summary_path: Path
    figure_path: Path
    metadata_path: Path
    case_count: int
    polymarket_lower_loss_count: int
    traditional_lower_loss_count: int
    mean_polymarket_brier: float
    mean_traditional_brier: float

    def to_dict(self) -> dict[str, float | int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "cases_path": str(self.cases_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "case_count": self.case_count,
            "polymarket_lower_loss_count": self.polymarket_lower_loss_count,
            "traditional_lower_loss_count": self.traditional_lower_loss_count,
            "mean_polymarket_brier": self.mean_polymarket_brier,
            "mean_traditional_brier": self.mean_traditional_brier,
        }


FINAL_SNAPSHOT_CASES: tuple[FinalSnapshotCaseSpec, ...] = (
    FinalSnapshotCaseSpec(
        case_id="us_2024_president_trump",
        case_label="2024 presidential election: Trump wins",
        event_slug="presidential-election-winner-2024",
        market_slug="will-donald-trump-win-the-2024-us-presidential-election",
        target_outcome="Yes",
        traditional_probability=0.4945,
        resolved_outcome="Yes",
    ),
    FinalSnapshotCaseSpec(
        case_id="us_2024_senate_republican_control",
        case_label="2024 Senate control: Republicans",
        event_slug="which-party-will-control-the-us-senate-after-the-2024-election",
        market_slug="which-party-will-control-the-us-senate-after-the-2024-election",
        target_outcome="Republicans",
        traditional_probability=0.92,
        resolved_outcome="Republicans",
    ),
    FinalSnapshotCaseSpec(
        case_id="us_2024_house_republican_control",
        case_label="2024 House control: Republicans",
        event_slug="house-control-after-2024-election",
        market_slug="house-control-after-2024-election",
        target_outcome="Republican",
        traditional_probability=0.49,
        resolved_outcome="Republican",
    ),
    FinalSnapshotCaseSpec(
        case_id="us_2024_senate_montana_republican",
        case_label="2024 Montana Senate: Republican wins",
        event_slug="montana-us-senate-election-winner",
        market_slug="will-a-republican-win-montana-us-senate-election",
        target_outcome="Yes",
        traditional_probability=0.93,
        resolved_outcome="Yes",
    ),
    FinalSnapshotCaseSpec(
        case_id="us_2024_senate_ohio_republican",
        case_label="2024 Ohio Senate: Republican wins",
        event_slug="ohio-us-senate-election-winner",
        market_slug="will-a-republican-win-ohio-us-senate-election",
        target_outcome="Yes",
        traditional_probability=0.59,
        resolved_outcome="Yes",
    ),
    FinalSnapshotCaseSpec(
        case_id="us_2024_senate_west_virginia_republican",
        case_label="2024 West Virginia Senate: Republican wins",
        event_slug="west-virginia-us-senate-election-winner",
        market_slug="will-a-republican-win-west-virginia-us-senate-election",
        target_outcome="Yes",
        traditional_probability=0.999,
        resolved_outcome="Yes",
    ),
    FinalSnapshotCaseSpec(
        case_id="us_2024_senate_florida_republican",
        case_label="2024 Florida Senate: Republican wins",
        event_slug="florida-us-senate-election-winner",
        market_slug="will-a-republican-win-florida-us-senate-election",
        target_outcome="Yes",
        traditional_probability=0.84,
        resolved_outcome="Yes",
    ),
    FinalSnapshotCaseSpec(
        case_id="us_2024_senate_texas_republican",
        case_label="2024 Texas Senate: Republican wins",
        event_slug="texas-us-senate-election-winner",
        market_slug="will-a-republican-win-texas-us-senate-election",
        target_outcome="Yes",
        traditional_probability=0.84,
        resolved_outcome="Yes",
    ),
)


def generate_h1_final_snapshot_outputs(
    *,
    source: str = "mock",
    cases_output: Path = CASE_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
    forecast_timestamp_utc: str = FINAL_FORECAST_TIMESTAMP_UTC,
    client: httpx.Client | None = None,
) -> H1FinalSnapshotResult:
    """Generate final-snapshot H1 cases, summary, figure, and metadata."""

    if source not in {"mock", "live"}:
        raise ValueError("source must be either 'mock' or 'live'")
    forecast_ts = pd.Timestamp(forecast_timestamp_utc).tz_convert("UTC")
    own_client = client is None
    http_client = client or httpx.Client(timeout=25.0)
    try:
        rows = [
            build_case_row(
                spec,
                source=source,
                forecast_ts=forecast_ts,
                client=http_client,
            )
            for spec in FINAL_SNAPSHOT_CASES
        ]
    finally:
        if own_client:
            http_client.close()

    cases = validate_cases(pd.DataFrame(rows, columns=CASE_COLUMNS))
    summary = build_summary(cases)
    cases_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    cases.to_csv(cases_output, index=False)
    summary.to_csv(summary_output, index=False)
    write_final_snapshot_figure(cases=cases, output_path=figure_output)
    metadata = build_metadata(
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
    return H1FinalSnapshotResult(
        cases_path=cases_output,
        summary_path=summary_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        case_count=int(values["case_count"]),
        polymarket_lower_loss_count=int(values["polymarket_lower_loss_count"]),
        traditional_lower_loss_count=int(values["traditional_lower_loss_count"]),
        mean_polymarket_brier=float(values["mean_polymarket_brier"]),
        mean_traditional_brier=float(values["mean_traditional_brier"]),
    )


def build_case_row(
    spec: FinalSnapshotCaseSpec,
    *,
    source: str,
    forecast_ts: pd.Timestamp,
    client: httpx.Client,
) -> dict[str, Any]:
    """Build one final-snapshot comparison row."""

    event = mock_gamma_event(spec) if source == "mock" else fetch_gamma_event(client, spec.event_slug)
    market = select_market(event, spec.market_slug)
    token_id = target_token_id(market, spec.target_outcome)
    price = (
        mock_price_point(spec, forecast_ts=forecast_ts)
        if source == "mock"
        else fetch_nearest_price(
            client,
            token_id=token_id,
            target_ts=forecast_ts,
            max_distance_seconds=MAX_PRICE_TIME_DISTANCE_SECONDS,
        )
    )
    pm_probability = float(price["price"])
    traditional_probability = float(spec.traditional_probability)
    outcome = float(spec.outcome_value)
    pm_brier = (pm_probability - outcome) ** 2
    traditional_brier = (traditional_probability - outcome) ** 2
    if pm_brier < traditional_brier:
        lower_loss_source = "polymarket"
    elif pm_brier > traditional_brier:
        lower_loss_source = "traditional_forecast"
    else:
        lower_loss_source = "tie"

    observed_ts = pd.Timestamp(price["observed_at_utc"]).tz_convert("UTC")
    return {
        "case_id": spec.case_id,
        "case_label": spec.case_label,
        "forecast_timestamp_utc": _format_timestamp(forecast_ts),
        "polymarket_observed_at_utc": _format_timestamp(observed_ts),
        "polymarket_time_distance_seconds": int(
            abs((observed_ts - forecast_ts).total_seconds())
        ),
        "polymarket_event_slug": spec.event_slug,
        "polymarket_market_slug": str(market.get("slug", "")),
        "polymarket_market_id": str(market.get("id", "")),
        "polymarket_condition_id": str(market.get("conditionId", "")),
        "target_outcome": spec.target_outcome,
        "target_token_id": token_id,
        "resolved_outcome": spec.resolved_outcome,
        "outcome_value": outcome,
        "polymarket_probability": pm_probability,
        "traditional_source": "FiveThirtyEight final 2024 forecast",
        "traditional_probability": traditional_probability,
        "polymarket_brier": pm_brier,
        "traditional_brier": traditional_brier,
        "loss_advantage": traditional_brier - pm_brier,
        "lower_loss_source": lower_loss_source,
        "forecast_source_url": FIVETHIRTYEIGHT_FINAL_FORECAST_URL,
        "polymarket_source_url": f"https://polymarket.com/event/{spec.event_slug}",
        "price_history_source_url": f"{CLOB_BASE_URL}/prices-history",
        "allowed_interpretation": (
            "Final-snapshot Brier comparison for one resolved 2024 election "
            "outcome using the selected target probability."
        ),
        "limitation": (
            "Small curated final-snapshot extension; not a daily time series, "
            "not raw polls, and not enough cases for a broad many-markets claim."
        ),
    }


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
    """Select the target market from a Gamma event payload."""

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
        raise ValueError("No CLOB history point was close enough to forecast timestamp")
    candidates.sort(key=lambda item: (float(item["distance"]), str(item["observed_at_utc"])))
    return candidates[0]


def validate_cases(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate final-snapshot comparison rows."""

    missing = [column for column in CASE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"final snapshot cases missing required columns: {missing}")
    forbidden = [column for column in frame.columns if "wallet" in column.lower()]
    if forbidden:
        raise ValueError(f"final snapshot cases must not contain wallet columns: {forbidden}")
    normalized = frame.loc[:, list(CASE_COLUMNS)].copy()
    for column in (
        "outcome_value",
        "polymarket_probability",
        "traditional_probability",
        "polymarket_brier",
        "traditional_brier",
        "loss_advantage",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    for column in ("outcome_value", "polymarket_probability", "traditional_probability"):
        if not normalized[column].between(0.0, 1.0).all():
            raise ValueError(f"{column} values must be in [0, 1]")
    if (normalized["polymarket_brier"] < 0).any() or (normalized["traditional_brier"] < 0).any():
        raise ValueError("Brier values must be non-negative")
    if (
        pd.to_numeric(
            normalized["polymarket_time_distance_seconds"],
            errors="raise",
        )
        > MAX_PRICE_TIME_DISTANCE_SECONDS
    ).any():
        raise ValueError("Polymarket price point is too far from forecast timestamp")
    for column in (
        "case_id",
        "case_label",
        "forecast_timestamp_utc",
        "polymarket_observed_at_utc",
        "target_outcome",
        "target_token_id",
        "traditional_source",
        "forecast_source_url",
    ):
        if normalized[column].fillna("").astype(str).str.strip().eq("").any():
            raise ValueError(f"{column} must not be blank")
    return normalized.sort_values("case_id").reset_index(drop=True)


def build_summary(cases: pd.DataFrame) -> pd.DataFrame:
    """Build compact final-snapshot summary rows."""

    pm_lower = int((cases["lower_loss_source"] == "polymarket").sum())
    traditional_lower = int((cases["lower_loss_source"] == "traditional_forecast").sum())
    ties = int((cases["lower_loss_source"] == "tie").sum())
    mean_pm = float(cases["polymarket_brier"].mean())
    mean_traditional = float(cases["traditional_brier"].mean())
    rows = [
        ("case_count", len(cases), "cases", "Curated resolved final-snapshot outcomes."),
        (
            "independent_resolved_outcome_count",
            len(cases),
            "outcomes",
            "Each row is a distinct resolved 2024 election outcome.",
        ),
        (
            "polymarket_lower_loss_count",
            pm_lower,
            "cases",
            "Cases where Polymarket has lower Brier loss.",
        ),
        (
            "traditional_lower_loss_count",
            traditional_lower,
            "cases",
            "Cases where the 538 final forecast has lower Brier loss.",
        ),
        ("tie_count", ties, "cases", "Cases with equal Brier loss."),
        (
            "polymarket_better_share",
            pm_lower / len(cases) if len(cases) else 0.0,
            "share",
            "Share of final-snapshot cases where Polymarket loss is lower.",
        ),
        (
            "mean_polymarket_brier",
            mean_pm,
            "brier_score",
            "Mean Brier loss across Polymarket final snapshots.",
        ),
        (
            "mean_traditional_brier",
            mean_traditional,
            "brier_score",
            "Mean Brier loss across 538 final probabilities.",
        ),
        (
            "mean_loss_advantage",
            mean_traditional - mean_pm,
            "brier_score",
            "Positive values mean lower mean Polymarket loss.",
        ),
    ]
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def write_final_snapshot_figure(*, cases: pd.DataFrame, output_path: Path) -> Path:
    """Write final-snapshot H1 extension figure."""

    labels = [_short_case_label(label) for label in cases["case_label"].tolist()]
    y = list(range(len(labels)))
    height = 0.36
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(13.2, 6.2),
        gridspec_kw={"width_ratios": [1.35, 1.0]},
    )
    fig.suptitle("H1 Final-Snapshot Extension: Polymarket vs 538", fontsize=14, fontweight="bold")

    axes[0].barh(
        [idx - height / 2 for idx in y],
        cases["polymarket_brier"],
        height=height,
        label="Polymarket",
        color="#2563eb",
    )
    axes[0].barh(
        [idx + height / 2 for idx in y],
        cases["traditional_brier"],
        height=height,
        label="538 final forecast",
        color="#dc2626",
    )
    axes[0].set_yticks(y, labels)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("Brier loss (lower is better)")
    axes[0].set_title("Final-snapshot Brier loss by resolved outcome")
    axes[0].legend(fontsize=8)

    counts = cases["lower_loss_source"].value_counts()
    axes[1].bar(
        ["Polymarket\nlower loss", "538\nlower loss", "Tie"],
        [
            int(counts.get("polymarket", 0)),
            int(counts.get("traditional_forecast", 0)),
            int(counts.get("tie", 0)),
        ],
        color=["#2563eb", "#dc2626", "#9ca3af"],
    )
    axes[1].set_ylim(0, max(3.2, float(len(cases)) + 0.4))
    axes[1].set_ylabel("Cases")
    axes[1].set_title("Head-to-head lower-loss count")
    for ax in axes:
        ax.grid(True, axis="x" if ax is axes[0] else "y", alpha=0.25)
    axes[1].text(
        0.5,
        -0.28,
        "Curated final snapshots only; not raw polls and not a broad many-markets proof.",
        transform=axes[1].transAxes,
        ha="center",
        fontsize=8.8,
        color="#374151",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.08, 1, 0.92))
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return output_path


def _short_case_label(label: str) -> str:
    text = label.replace("2024 ", "")
    text = text.replace("presidential election: Trump wins", "President: Trump")
    text = text.replace("House control: Republicans", "House control: R")
    text = text.replace("Senate control: Republicans", "Senate control: R")
    text = text.replace("Senate: Republican wins", "Senate: R")
    return text


def build_metadata(
    *,
    source: str,
    cases: pd.DataFrame,
    summary: pd.DataFrame,
    cases_output: Path,
    summary_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for final-snapshot H1 extension."""

    values = _summary_values(summary)
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_final_snapshot_extension",
            "source": source,
            "forecast_timestamp_utc": FINAL_FORECAST_TIMESTAMP_UTC,
            "calculation_scope": "deterministic_python_from_curated_probability_forecasts",
            "traditional_source": "FiveThirtyEight final 2024 forecast article",
            "raw_poll_average_probability_transform_used": False,
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
            "traditional_lower_loss_count": int(values["traditional_lower_loss_count"]),
            "polymarket_better_share": float(values["polymarket_better_share"]),
            "mean_polymarket_brier": float(values["mean_polymarket_brier"]),
            "mean_traditional_brier": float(values["mean_traditional_brier"]),
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
            "forecast_source": FIVETHIRTYEIGHT_FINAL_FORECAST_URL,
            "gamma_events": f"{GAMMA_BASE_URL}/events",
            "clob_prices_history": f"{CLOB_BASE_URL}/prices-history",
        },
        "case_ids": cases["case_id"].tolist(),
        "traditional_probability_notes": {
            "us_2024_president_trump": "538 final forecast reports Trump at 49.45 percent.",
            "us_2024_senate_republican_control": "538 final forecast reports Republicans at 92-in-100 for Senate control.",
            "us_2024_house_republican_control": "538 final forecast reports Republicans at 49-in-100 for House control.",
            "us_2024_senate_montana_republican": "538 final forecast reports Republicans at 93-in-100 in Montana Senate.",
            "us_2024_senate_ohio_republican": "538 final forecast reports Democrat Sherrod Brown at 41-in-100; Republican target probability is 59-in-100.",
            "us_2024_senate_west_virginia_republican": "538 final forecast reports Democrat Glenn Elliott at 1-in-1,000; Republican target probability is 999-in-1,000.",
            "us_2024_senate_florida_republican": "538 final forecast reports Democrats at 16-in-100 in Florida Senate; Republican target probability is 84-in-100.",
            "us_2024_senate_texas_republican": "538 final forecast reports Democrats at 16-in-100 in Texas Senate; Republican target probability is 84-in-100.",
        },
        "limitations": {
            "small_curated_final_snapshot_set": True,
            "not_daily_time_series": True,
            "not_raw_poll_comparison": True,
            "same_election_day_outcomes_not_many_markets": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def mock_gamma_event(spec: FinalSnapshotCaseSpec) -> dict[str, Any]:
    """Return a Gamma-like event fixture for one case."""

    if spec.target_outcome == "Yes":
        outcomes = ["Yes", "No"]
        token_ids = [f"token-{spec.case_id}-yes", f"token-{spec.case_id}-no"]
    elif spec.target_outcome == "Republicans":
        outcomes = ["Democrats", "Republicans"]
        token_ids = [f"token-{spec.case_id}-democrats", f"token-{spec.case_id}-republicans"]
    else:
        outcomes = ["Democratic", "Republican"]
        token_ids = [f"token-{spec.case_id}-democratic", f"token-{spec.case_id}-republican"]
    return {
        "slug": spec.event_slug,
        "markets": [
            {
                "id": f"market-{spec.case_id}",
                "slug": spec.market_slug,
                "conditionId": f"condition-{spec.case_id}",
                "outcomes": json.dumps(outcomes),
                "clobTokenIds": json.dumps(token_ids),
            }
        ],
    }


def mock_price_point(spec: FinalSnapshotCaseSpec, *, forecast_ts: pd.Timestamp) -> dict[str, Any]:
    """Return deterministic mock prices mirroring the live final-snapshot shape."""

    prices = {
        "us_2024_president_trump": 0.63,
        "us_2024_senate_republican_control": 0.81,
        "us_2024_house_republican_control": 0.51,
        "us_2024_senate_montana_republican": 0.83,
        "us_2024_senate_ohio_republican": 0.615,
        "us_2024_senate_west_virginia_republican": 0.981,
        "us_2024_senate_florida_republican": 0.905,
        "us_2024_senate_texas_republican": 0.85,
    }
    return {
        "observed_at_utc": _format_timestamp(forecast_ts + pd.Timedelta(seconds=2)),
        "price": prices[spec.case_id],
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


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("mock", "live"), default="mock")
    parser.add_argument("--cases-output", type=Path, default=CASE_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    parser.add_argument("--forecast-timestamp-utc", default=FINAL_FORECAST_TIMESTAMP_UTC)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_final_snapshot_outputs(
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
