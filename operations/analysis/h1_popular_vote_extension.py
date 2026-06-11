"""Build an H1 popular-vote extension from 538 poll shares and Polymarket.

This module compares the Polymarket Trump popular-vote market with a documented
poll-share-to-probability transformation. It uses the local FiveThirtyEight
national Trump/Harris shares already stored in ``poll_forecasts`` and transforms
the Trump-minus-Harris margin into a Trump popular-vote win probability with a
fixed symmetric normal polling-error model.

The output is a bounded daily panel for one resolved outcome. It is not a raw
RCP import, not an official 538 popular-vote probability forecast, and not an
independent-many-elections sample.
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
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


DB_PATH = Path("data/thesis.db")
GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
CLOB_BASE_URL = "https://clob.polymarket.com"
POPULAR_VOTE_EVENT_SLUG = "presidential-election-popular-vote-winner-2024"
TRUMP_POPULAR_VOTE_MARKET_SLUG = (
    "will-donald-trump-win-the-popular-vote-in-the-2024-presidential-election"
)
TARGET_OUTCOME = "Yes"
OUTCOME_VALUE = 1.0
FIVETHIRTYEIGHT_SOURCE = "fivethirtyeight"
FIVETHIRTYEIGHT_POLL_AVERAGES_URL = (
    "https://raw.githubusercontent.com/fivethirtyeight/data/master/"
    "polls/2024-averages/presidential_general_averages_2024-09-12_uncorrected.csv"
)
FIVETHIRTYEIGHT_POLL_ERROR_SOURCE_URL = (
    "https://abcnews.com/538/538s-final-forecasts-2024-election/story?id=115511051"
)
OUTCOME_SOURCE_URL = "https://www.presidency.ucsb.edu/statistics/elections/2024"
POLL_ERROR_MAE_POINTS = 3.8
CLOB_CHUNK_DAYS = 7
CLOB_FIDELITY_MINUTES = 60

CASE_OUTPUT = RESULTS_DIR / "h1_popular_vote_cases.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_popular_vote_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_popular_vote.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_popular_vote_metadata.json"

CASE_COLUMNS: tuple[str, ...] = (
    "date",
    "polymarket_observed_at_utc",
    "polymarket_event_slug",
    "polymarket_market_slug",
    "polymarket_market_id",
    "polymarket_condition_id",
    "target_outcome",
    "target_token_id",
    "outcome_value",
    "poll_trump_share",
    "poll_harris_share",
    "poll_margin_trump_minus_harris_points",
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
    "outcome_source_url",
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
class H1PopularVoteResult:
    """Summary of generated popular-vote extension artifacts."""

    cases_path: Path
    summary_path: Path
    figure_path: Path
    metadata_path: Path
    case_count: int
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
            "polymarket_lower_loss_count": self.polymarket_lower_loss_count,
            "poll_derived_lower_loss_count": self.poll_derived_lower_loss_count,
            "mean_polymarket_brier": self.mean_polymarket_brier,
            "mean_poll_derived_brier": self.mean_poll_derived_brier,
        }


def generate_h1_popular_vote_outputs(
    *,
    source: str = "mock",
    db_path: Path = DB_PATH,
    cases_output: Path = CASE_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
    client: httpx.Client | None = None,
) -> H1PopularVoteResult:
    """Generate popular-vote cases, summary, figure, and metadata."""

    if source not in {"mock", "live"}:
        raise ValueError("source must be either 'mock' or 'live'")
    poll_rows = read_national_poll_shares(db_path)
    own_client = client is None
    http_client = client or httpx.Client(timeout=25.0)
    try:
        event = mock_gamma_event() if source == "mock" else fetch_gamma_event(http_client)
        market = select_market(event, TRUMP_POPULAR_VOTE_MARKET_SLUG)
        token_id = target_token_id(market, TARGET_OUTCOME)
        prices = (
            mock_daily_prices(poll_rows["date"].tolist())
            if source == "mock"
            else fetch_daily_prices(
                http_client,
                token_id=token_id,
                start_date=str(poll_rows["date"].min()),
                end_date=str(poll_rows["date"].max()),
            )
        )
    finally:
        if own_client:
            http_client.close()

    cases = validate_cases(
        build_cases(
            poll_rows=poll_rows,
            prices=prices,
            market=market,
            token_id=token_id,
        )
    )
    summary = build_summary(cases)
    cases_output.parent.mkdir(parents=True, exist_ok=True)
    cases.to_csv(cases_output, index=False)
    summary.to_csv(summary_output, index=False)
    write_popular_vote_figure(cases=cases, output_path=figure_output)
    metadata = build_metadata(
        source=source,
        cases=cases,
        summary=summary,
        db_path=db_path,
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
    return H1PopularVoteResult(
        cases_path=cases_output,
        summary_path=summary_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        case_count=int(values["case_count"]),
        polymarket_lower_loss_count=int(values["polymarket_lower_loss_count"]),
        poll_derived_lower_loss_count=int(values["poll_derived_lower_loss_count"]),
        mean_polymarket_brier=float(values["mean_polymarket_brier"]),
        mean_poll_derived_brier=float(values["mean_poll_derived_brier"]),
    )


def read_national_poll_shares(db_path: Path) -> pd.DataFrame:
    """Read local 538 Trump/Harris national shares and return one row per date."""

    if not db_path.exists():
        raise FileNotFoundError(f"database not found: {db_path}")
    with sqlite3.connect(db_path) as conn:
        frame = pd.read_sql_query(
            """
            SELECT date, candidate, probability
            FROM poll_forecasts
            WHERE source = ?
              AND lower(candidate) IN ('trump', 'harris')
            ORDER BY date, candidate
            """,
            conn,
            params=(FIVETHIRTYEIGHT_SOURCE,),
        )
    if frame.empty:
        raise ValueError("poll_forecasts has no 538 Trump/Harris rows")
    frame["date"] = frame["date"].astype(str)
    frame["candidate"] = frame["candidate"].astype(str).str.lower()
    frame["probability"] = pd.to_numeric(frame["probability"], errors="raise")
    if not frame["probability"].between(0.0, 1.0).all():
        raise ValueError("poll shares must be probabilities in [0, 1]")
    pivot = frame.pivot_table(
        index="date",
        columns="candidate",
        values="probability",
        aggfunc="mean",
    )
    missing_candidates = {"trump", "harris"} - set(str(column) for column in pivot.columns)
    if missing_candidates:
        raise ValueError("no overlapping 538 Trump/Harris dates found")
    pivot = pivot.dropna(subset=["trump", "harris"]).reset_index()
    if pivot.empty:
        raise ValueError("no overlapping 538 Trump/Harris dates found")
    return pivot.loc[:, ["date", "trump", "harris"]].sort_values("date").reset_index(drop=True)


def build_cases(
    *,
    poll_rows: pd.DataFrame,
    prices: pd.DataFrame,
    market: dict[str, Any],
    token_id: str,
) -> pd.DataFrame:
    """Build daily popular-vote comparison rows."""

    merged = poll_rows.merge(prices, on="date", how="inner")
    if merged.empty:
        raise ValueError("no overlapping dates between poll rows and Polymarket prices")
    sigma = poll_error_sigma_points(POLL_ERROR_MAE_POINTS)
    rows: list[dict[str, Any]] = []
    for _, row in merged.iterrows():
        margin_points = (float(row["trump"]) - float(row["harris"])) * 100.0
        poll_probability = poll_margin_to_probability(
            margin_points,
            mae_points=POLL_ERROR_MAE_POINTS,
        )
        pm_probability = float(row["polymarket_probability"])
        pm_brier = (pm_probability - OUTCOME_VALUE) ** 2
        poll_brier = (poll_probability - OUTCOME_VALUE) ** 2
        if pm_brier < poll_brier:
            lower = "polymarket"
        elif pm_brier > poll_brier:
            lower = "poll_derived"
        else:
            lower = "tie"
        rows.append(
            {
                "date": str(row["date"]),
                "polymarket_observed_at_utc": str(row["polymarket_observed_at_utc"]),
                "polymarket_event_slug": POPULAR_VOTE_EVENT_SLUG,
                "polymarket_market_slug": str(market.get("slug", "")),
                "polymarket_market_id": str(market.get("id", "")),
                "polymarket_condition_id": str(market.get("conditionId", "")),
                "target_outcome": TARGET_OUTCOME,
                "target_token_id": token_id,
                "outcome_value": OUTCOME_VALUE,
                "poll_trump_share": float(row["trump"]),
                "poll_harris_share": float(row["harris"]),
                "poll_margin_trump_minus_harris_points": margin_points,
                "poll_error_mae_points": POLL_ERROR_MAE_POINTS,
                "poll_error_sigma_points": sigma,
                "poll_transform_name": "normal_margin_error_from_538_mae",
                "poll_derived_probability": poll_probability,
                "polymarket_probability": pm_probability,
                "polymarket_brier": pm_brier,
                "poll_derived_brier": poll_brier,
                "loss_advantage": poll_brier - pm_brier,
                "lower_loss_source": lower,
                "poll_average_source_url": FIVETHIRTYEIGHT_POLL_AVERAGES_URL,
                "poll_error_source_url": FIVETHIRTYEIGHT_POLL_ERROR_SOURCE_URL,
                "outcome_source_url": OUTCOME_SOURCE_URL,
                "polymarket_source_url": f"https://polymarket.com/event/{POPULAR_VOTE_EVENT_SLUG}",
                "price_history_source_url": f"{CLOB_BASE_URL}/prices-history",
                "allowed_interpretation": (
                    "Daily comparison for one resolved popular-vote outcome using "
                    "a documented poll-margin probability transform."
                ),
                "limitation": (
                    "Repeated daily rows for one outcome; the poll transform is "
                    "model-dependent and not an official 538 popular-vote forecast."
                ),
            }
        )
    return pd.DataFrame(rows, columns=CASE_COLUMNS)


def poll_error_sigma_points(mae_points: float) -> float:
    """Convert normal absolute-error MAE into a standard deviation."""

    if mae_points <= 0:
        raise ValueError("mae_points must be positive")
    return float(mae_points * math.sqrt(math.pi / 2.0))


def poll_margin_to_probability(
    margin_points: float,
    *,
    mae_points: float = POLL_ERROR_MAE_POINTS,
) -> float:
    """Transform a Trump-minus-Harris poll margin into P(Trump wins popular vote)."""

    sigma = poll_error_sigma_points(mae_points)
    z = float(margin_points) / sigma
    probability = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    return min(1.0, max(0.0, float(probability)))


def fetch_gamma_event(client: httpx.Client) -> dict[str, Any]:
    """Fetch the public Polymarket popular-vote event."""

    response = client.get(f"{GAMMA_BASE_URL}/events", params={"slug": POPULAR_VOTE_EVENT_SLUG})
    response.raise_for_status()
    payload = response.json()
    event = payload[0] if isinstance(payload, list) and payload else payload
    if not isinstance(event, dict):
        raise ValueError("Gamma popular-vote response is not an object")
    return event


def select_market(event: dict[str, Any], market_slug: str) -> dict[str, Any]:
    """Select one market from a Gamma event payload."""

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


def fetch_daily_prices(
    client: httpx.Client,
    *,
    token_id: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Fetch bounded CLOB hourly history and return daily last prices."""

    start_ts = pd.Timestamp(start_date, tz="UTC")
    end_ts = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    points: list[dict[str, Any]] = []
    cursor = start_ts
    while cursor < end_ts:
        chunk_end = min(cursor + pd.Timedelta(days=CLOB_CHUNK_DAYS), end_ts)
        response = client.get(
            f"{CLOB_BASE_URL}/prices-history",
            params={
                "market": token_id,
                "startTs": int(cursor.timestamp()),
                "endTs": int(chunk_end.timestamp()),
                "fidelity": CLOB_FIDELITY_MINUTES,
            },
        )
        response.raise_for_status()
        payload = response.json()
        history = payload.get("history") if isinstance(payload, dict) else None
        if not isinstance(history, list):
            raise ValueError("CLOB price-history response must contain a history list")
        points.extend(point for point in history if isinstance(point, dict))
        cursor = chunk_end
    if not points:
        raise ValueError(f"No CLOB price history returned for token {token_id}")

    rows: list[dict[str, Any]] = []
    for point in points:
        timestamp_value = point.get("t", point.get("timestamp"))
        price_value = point.get("p", point.get("price"))
        if timestamp_value is None or price_value is None:
            continue
        observed_ts = _history_timestamp(timestamp_value)
        price = float(price_value)
        rows.append(
            {
                "date": observed_ts.date().isoformat(),
                "polymarket_observed_at_utc": _format_timestamp(observed_ts),
                "polymarket_probability": price,
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError("CLOB history contained no parseable price points")
    frame = frame.sort_values(["date", "polymarket_observed_at_utc"])
    daily = frame.groupby("date", as_index=False).last()
    return validate_prices(daily)


def mock_gamma_event() -> dict[str, Any]:
    """Return a Gamma-like fixture for the Trump popular-vote market."""

    return {
        "slug": POPULAR_VOTE_EVENT_SLUG,
        "markets": [
            {
                "id": "market-us-2024-popular-vote-trump",
                "slug": TRUMP_POPULAR_VOTE_MARKET_SLUG,
                "conditionId": "condition-us-2024-popular-vote-trump",
                "outcomes": json.dumps(["Yes", "No"]),
                "clobTokenIds": json.dumps(["token-popular-vote-trump-yes", "token-popular-vote-trump-no"]),
            }
        ],
    }


def mock_daily_prices(dates: Sequence[str]) -> pd.DataFrame:
    """Return deterministic daily price fixtures for tests and offline runs."""

    rows = []
    for idx, date in enumerate(sorted(str(value) for value in dates)):
        price = 0.28 + (0.04 if idx % 3 == 0 else 0.0) + min(idx, 20) * 0.001
        rows.append(
            {
                "date": date,
                "polymarket_observed_at_utc": f"{date}T23:00:00Z",
                "polymarket_probability": round(price, 6),
            }
        )
    return validate_prices(pd.DataFrame(rows))


def validate_prices(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate daily Polymarket price rows."""

    required = {"date", "polymarket_observed_at_utc", "polymarket_probability"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Polymarket price rows missing columns: {missing}")
    normalized = frame.loc[:, ["date", "polymarket_observed_at_utc", "polymarket_probability"]].copy()
    normalized["date"] = normalized["date"].astype(str)
    normalized["polymarket_observed_at_utc"] = normalized["polymarket_observed_at_utc"].astype(str)
    normalized["polymarket_probability"] = pd.to_numeric(
        normalized["polymarket_probability"],
        errors="raise",
    )
    if not normalized["polymarket_probability"].between(0.0, 1.0).all():
        raise ValueError("Polymarket probabilities must be in [0, 1]")
    return normalized.sort_values("date").reset_index(drop=True)


def validate_cases(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate popular-vote comparison cases."""

    missing = [column for column in CASE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"popular-vote cases missing columns: {missing}")
    forbidden = [column for column in frame.columns if "wallet" in column.lower()]
    if forbidden:
        raise ValueError(f"popular-vote cases must not contain wallet columns: {forbidden}")
    normalized = frame.loc[:, list(CASE_COLUMNS)].copy()
    for column in (
        "outcome_value",
        "poll_trump_share",
        "poll_harris_share",
        "poll_derived_probability",
        "polymarket_probability",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
        if not normalized[column].between(0.0, 1.0).all():
            raise ValueError(f"{column} must be in [0, 1]")
    for column in (
        "poll_margin_trump_minus_harris_points",
        "poll_error_mae_points",
        "poll_error_sigma_points",
        "polymarket_brier",
        "poll_derived_brier",
        "loss_advantage",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    allowed = {"polymarket", "poll_derived", "tie"}
    if not set(normalized["lower_loss_source"].unique()).issubset(allowed):
        raise ValueError("lower_loss_source contains unexpected values")
    return normalized.sort_values("date").reset_index(drop=True)


def build_summary(cases: pd.DataFrame) -> pd.DataFrame:
    """Build compact summary rows for the popular-vote extension."""

    counts = cases["lower_loss_source"].value_counts()
    case_count = int(len(cases))
    pm_lower = int(counts.get("polymarket", 0))
    poll_lower = int(counts.get("poll_derived", 0))
    ties = int(counts.get("tie", 0))
    rows = [
        _summary_row("case_count", case_count, "daily rows", "Matched daily rows."),
        _summary_row(
            "independent_resolved_outcome_count",
            1,
            "outcomes",
            "Trump popular-vote outcome.",
        ),
        _summary_row(
            "polymarket_lower_loss_count",
            pm_lower,
            "daily rows",
            "Rows where Polymarket has lower Brier loss.",
        ),
        _summary_row(
            "poll_derived_lower_loss_count",
            poll_lower,
            "daily rows",
            "Rows where the transformed 538 poll margin has lower Brier loss.",
        ),
        _summary_row("tie_count", ties, "daily rows", "Rows with equal Brier loss."),
        _summary_row(
            "polymarket_better_share",
            pm_lower / case_count,
            "share",
            "Share of rows where Polymarket has lower Brier loss.",
        ),
        _summary_row(
            "mean_polymarket_brier",
            float(cases["polymarket_brier"].mean()),
            "Brier loss",
            "Mean Polymarket Brier loss.",
        ),
        _summary_row(
            "mean_poll_derived_brier",
            float(cases["poll_derived_brier"].mean()),
            "Brier loss",
            "Mean transformed-poll Brier loss.",
        ),
        _summary_row(
            "mean_loss_advantage",
            float(cases["loss_advantage"].mean()),
            "Brier loss difference",
            "Mean poll-derived Brier minus Polymarket Brier.",
        ),
    ]
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def write_popular_vote_figure(*, cases: pd.DataFrame, output_path: Path) -> Path:
    """Write the popular-vote extension figure."""

    x = pd.to_datetime(cases["date"])
    fig, axes = plt.subplots(2, 1, figsize=(12.8, 7.6), sharex=True)
    fig.suptitle(
        "H1 Popular-Vote Extension: Polymarket vs 538 Poll Transform",
        fontsize=13.5,
        fontweight="bold",
    )

    axes[0].plot(x, cases["polymarket_probability"], label="Polymarket Trump popular vote", color="#2563eb", linewidth=2)
    axes[0].plot(x, cases["poll_derived_probability"], label="538 poll-margin transform", color="#dc2626", linewidth=2)
    axes[0].set_ylabel("P(Trump wins popular vote)")
    axes[0].set_ylim(0, 0.62)
    axes[0].set_title("Forecast probability by day")
    axes[0].legend(fontsize=8)
    axes[0].grid(True, alpha=0.25)

    axes[1].plot(x, cases["polymarket_brier"], label="Polymarket Brier", color="#2563eb", linewidth=2)
    axes[1].plot(x, cases["poll_derived_brier"], label="Poll-derived Brier", color="#dc2626", linewidth=2)
    axes[1].axhline(0, color="#111827", linewidth=0.8)
    axes[1].set_ylabel("Brier loss (outcome = Trump popular vote)")
    axes[1].set_title("Daily Brier loss")
    axes[1].legend(fontsize=8)
    axes[1].grid(True, alpha=0.25)

    counts = cases["lower_loss_source"].value_counts()
    footer = (
        f"Rows: {len(cases)} | PM lower loss: {int(counts.get('polymarket', 0))} | "
        f"Poll-transform lower loss: {int(counts.get('poll_derived', 0))}. "
        "One resolved outcome; repeated daily rows."
    )
    fig.text(0.5, 0.015, footer, ha="center", fontsize=9, color="#374151")
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
    db_path: Path,
    cases_output: Path,
    summary_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for the popular-vote extension."""

    values = _summary_values(summary)
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_popular_vote_extension",
            "source": source,
            "calculation_scope": "deterministic_python_from_local_538_poll_shares_and_public_polymarket_history",
            "poll_transform": "normal_margin_error_from_538_mae",
            "poll_error_mae_points": POLL_ERROR_MAE_POINTS,
            "poll_error_sigma_points": poll_error_sigma_points(POLL_ERROR_MAE_POINTS),
            "trump_margin_probability_formula": "Phi((trump_share_minus_harris_share_points) / sigma_points)",
            "read_only_public_endpoints": source == "live",
            "rcp_included": False,
            "uses_raw_poll_shares_directly_as_probabilities": False,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
        },
        "outputs": {
            "case_count": int(values["case_count"]),
            "independent_resolved_outcome_count": int(values["independent_resolved_outcome_count"]),
            "polymarket_lower_loss_count": int(values["polymarket_lower_loss_count"]),
            "poll_derived_lower_loss_count": int(values["poll_derived_lower_loss_count"]),
            "tie_count": int(values["tie_count"]),
            "polymarket_better_share": float(values["polymarket_better_share"]),
            "mean_polymarket_brier": float(values["mean_polymarket_brier"]),
            "mean_poll_derived_brier": float(values["mean_poll_derived_brier"]),
            "mean_loss_advantage": float(values["mean_loss_advantage"]),
            "first_date": str(cases["date"].min()),
            "last_date": str(cases["date"].max()),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
            "supports_broad_polymarket_claim": False,
        },
        "source_paths": {
            "database": str(db_path),
            "cases": str(cases_output),
            "summary": str(summary_output),
            "figure": str(figure_output),
        },
        "source_urls": {
            "poll_average_source": FIVETHIRTYEIGHT_POLL_AVERAGES_URL,
            "poll_error_source": FIVETHIRTYEIGHT_POLL_ERROR_SOURCE_URL,
            "outcome_source": OUTCOME_SOURCE_URL,
            "polymarket_event": f"https://polymarket.com/event/{POPULAR_VOTE_EVENT_SLUG}",
            "gamma_events": f"{GAMMA_BASE_URL}/events",
            "clob_prices_history": f"{CLOB_BASE_URL}/prices-history",
        },
        "limitations": {
            "one_resolved_popular_vote_outcome": True,
            "daily_rows_are_repeated_forecasts": True,
            "poll_transform_is_model_dependent": True,
            "not_official_538_popular_vote_probability": True,
            "no_causal_or_tradeability_claim": True,
        },
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


def _summary_row(
    summary_id: str,
    value: int | float,
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("mock", "live"), default="mock")
    parser.add_argument("--db-path", type=Path, default=DB_PATH)
    parser.add_argument("--cases-output", type=Path, default=CASE_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_popular_vote_outputs(
            source=args.source,
            db_path=args.db_path,
            cases_output=args.cases_output,
            summary_output=args.summary_output,
            figure_output=args.figure_output,
            metadata_output=args.metadata_output,
        )
    except (FileNotFoundError, ValueError, KeyError, json.JSONDecodeError, httpx.HTTPError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
