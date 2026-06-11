"""Audit H1 readiness of Polymarket Trump margin-threshold markets.

Several Polymarket 2024 markets ask whether Trump would win a state by at
least a fixed margin. These are tempting H1 extension candidates because a
538 polling-average margin can be transformed into a threshold probability.

This module does not add Brier rows. It checks the precondition for doing so:
whether official 538 state polling-average rows and public Polymarket CLOB
history overlap in time for the same threshold market. If they do not overlap,
the candidate is documented as an exclusion rather than forced into H1.
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
    CLOB_BASE_URL,
    FIVETHIRTYEIGHT_POLL_AVERAGES_URL,
    GAMMA_BASE_URL,
)
from operations.analysis.run_h2_event_windows import RESULTS_DIR


POLL_WINDOW_START_FALLBACK = "2024-03-01"
POLL_WINDOW_END_FALLBACK = "2024-09-12"
LATE_CLOB_WINDOW_START = "2024-10-23"
LATE_CLOB_WINDOW_END = "2024-10-31"
HISTORY_FIDELITY_MINUTES = 1440
HISTORY_CHUNK_DAYS = 14

READINESS_OUTPUT = RESULTS_DIR / "h1_margin_threshold_readiness.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_margin_threshold_readiness.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_margin_threshold_readiness_metadata.json"

READINESS_COLUMNS: tuple[str, ...] = (
    "candidate_id",
    "state",
    "threshold_points",
    "market_slug",
    "question",
    "market_id",
    "condition_id",
    "yes_token_id",
    "outcome_value",
    "market_start_date",
    "market_end_date",
    "market_closed",
    "poll_pair_count",
    "poll_first_date",
    "poll_last_date",
    "clob_points_during_538_poll_window",
    "first_clob_during_538_poll_window",
    "last_clob_during_538_poll_window",
    "late_clob_points",
    "first_late_clob_timestamp_utc",
    "last_late_clob_timestamp_utc",
    "has_538_state_poll_rows",
    "has_clob_history_during_538_poll_window",
    "compatible_for_h1_brier_now",
    "status",
    "main_blocker",
    "required_next_step",
    "poll_average_source_url",
    "clob_source_url",
    "polymarket_source_url",
)


@dataclass(frozen=True)
class MarginThresholdSpec:
    """One reviewed Polymarket state-margin threshold candidate."""

    state: str
    threshold_points: int
    market_slug: str

    @property
    def candidate_id(self) -> str:
        return (
            f"us_2024_{self.state.lower().replace(' ', '_')}_"
            f"trump_by_{self.threshold_points}"
        )


@dataclass(frozen=True)
class MarginThresholdMarket:
    """Parsed Gamma metadata for one margin-threshold market."""

    spec: MarginThresholdSpec
    question: str
    market_id: str
    condition_id: str
    yes_token_id: str
    outcome_value: float
    market_start_date: str
    market_end_date: str
    market_closed: bool


@dataclass(frozen=True)
class H1MarginThresholdReadinessResult:
    """Summary of generated margin-threshold readiness artifacts."""

    readiness_path: Path
    figure_path: Path
    metadata_path: Path
    candidate_count: int
    candidates_with_538_state_polls: int
    candidates_with_clob_poll_window_history: int
    compatible_candidate_count: int

    def to_dict(self) -> dict[str, int | str]:
        return {
            "readiness_path": str(self.readiness_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "candidate_count": self.candidate_count,
            "candidates_with_538_state_polls": self.candidates_with_538_state_polls,
            "candidates_with_clob_poll_window_history": (
                self.candidates_with_clob_poll_window_history
            ),
            "compatible_candidate_count": self.compatible_candidate_count,
        }


MARGIN_THRESHOLD_SPECS: tuple[MarginThresholdSpec, ...] = (
    MarginThresholdSpec(
        state="Florida",
        threshold_points=8,
        market_slug="will-trump-win-florida-by-8-points",
    ),
    MarginThresholdSpec(
        state="Florida",
        threshold_points=12,
        market_slug="will-trump-win-florida-by-12-points",
    ),
    MarginThresholdSpec(
        state="Iowa",
        threshold_points=12,
        market_slug="will-trump-win-iowa-by-12-points",
    ),
    MarginThresholdSpec(
        state="Ohio",
        threshold_points=12,
        market_slug="will-trump-win-ohio-by-12-points",
    ),
    MarginThresholdSpec(
        state="Texas",
        threshold_points=10,
        market_slug="will-trump-win-texas-by-10-points",
    ),
    MarginThresholdSpec(
        state="Wyoming",
        threshold_points=50,
        market_slug="will-trump-win-wyoming-by-50-points",
    ),
    MarginThresholdSpec(
        state="Alabama",
        threshold_points=30,
        market_slug="will-trump-win-alabama-by-30-points",
    ),
)


def generate_h1_margin_threshold_readiness_outputs(
    *,
    source: str = "mock",
    readiness_output: Path = READINESS_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
    client: httpx.Client | None = None,
) -> H1MarginThresholdReadinessResult:
    """Generate margin-threshold readiness CSV, figure, and metadata."""

    if source not in {"mock", "live"}:
        raise ValueError("source must be either 'mock' or 'live'")
    own_client = client is None
    http_client = client or httpx.Client(timeout=30.0)
    try:
        poll_rows = (
            mock_poll_average_rows()
            if source == "mock"
            else fetch_poll_average_rows(client=http_client)
        )
        markets = (
            mock_margin_threshold_markets()
            if source == "mock"
            else fetch_margin_threshold_markets(client=http_client)
        )
        history_by_slug = (
            mock_history_by_slug()
            if source == "mock"
            else fetch_history_for_markets(client=http_client, markets=markets)
        )
    finally:
        if own_client:
            http_client.close()

    poll_pairs = build_state_poll_pair_coverage(poll_rows)
    readiness = validate_readiness_frame(
        build_readiness_frame(
            markets=markets,
            poll_pairs=poll_pairs,
            history_by_slug=history_by_slug,
        )
    )

    readiness_output.parent.mkdir(parents=True, exist_ok=True)
    readiness.to_csv(readiness_output, index=False)
    write_readiness_figure(readiness=readiness, output_path=figure_output)
    metadata = build_metadata(
        source=source,
        readiness=readiness,
        readiness_output=readiness_output,
        figure_output=figure_output,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    values = _summary_values(readiness)
    return H1MarginThresholdReadinessResult(
        readiness_path=readiness_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        candidate_count=values["candidate_count"],
        candidates_with_538_state_polls=values["with_538_polls"],
        candidates_with_clob_poll_window_history=values["with_poll_window_clob"],
        compatible_candidate_count=values["compatible"],
    )


def fetch_poll_average_rows(*, client: httpx.Client) -> list[dict[str, Any]]:
    """Fetch the official preserved 538 general-election polling averages."""

    response = client.get(FIVETHIRTYEIGHT_POLL_AVERAGES_URL)
    response.raise_for_status()
    text = response.text
    if not text.lstrip().startswith("candidate,date,"):
        raise ValueError("538 polling-average response is not the expected CSV")
    return pd.read_csv(io.StringIO(text)).to_dict(orient="records")


def fetch_margin_threshold_markets(*, client: httpx.Client) -> list[MarginThresholdMarket]:
    """Fetch reviewed margin-threshold markets from public Gamma events."""

    return [fetch_margin_threshold_market(client=client, spec=spec) for spec in MARGIN_THRESHOLD_SPECS]


def fetch_margin_threshold_market(
    *, client: httpx.Client, spec: MarginThresholdSpec
) -> MarginThresholdMarket:
    """Fetch and parse one public Gamma event by slug."""

    response = client.get(f"{GAMMA_BASE_URL}/events", params={"slug": spec.market_slug})
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"No Gamma event found for {spec.market_slug!r}")
    event = payload[0]
    if not isinstance(event, dict):
        raise ValueError("Gamma event response must contain objects")
    markets = event.get("markets")
    if not isinstance(markets, list) or not markets:
        raise ValueError(f"Gamma event has no markets for {spec.market_slug!r}")
    for market in markets:
        if isinstance(market, dict) and str(market.get("slug", "")) == spec.market_slug:
            return parse_margin_threshold_market(spec=spec, market=market)
    raise ValueError(f"Market slug {spec.market_slug!r} not found in Gamma event")


def parse_margin_threshold_market(
    *, spec: MarginThresholdSpec, market: dict[str, Any]
) -> MarginThresholdMarket:
    """Parse one Gamma market into the local readiness schema."""

    outcomes = _parse_json_list(market.get("outcomes"))
    prices = [_safe_float(value) for value in _parse_json_list(market.get("outcomePrices"))]
    token_ids = _parse_json_list(market.get("clobTokenIds"))
    yes_index = _outcome_index(outcomes, "Yes")
    if yes_index >= len(prices) or yes_index >= len(token_ids):
        raise ValueError("Gamma market is missing Yes outcome price or token id")
    outcome_value = 1.0 if float(prices[yes_index]) >= 0.5 else 0.0
    return MarginThresholdMarket(
        spec=spec,
        question=str(market.get("question", "")),
        market_id=str(market.get("id", "")),
        condition_id=str(market.get("conditionId", "")),
        yes_token_id=str(token_ids[yes_index]),
        outcome_value=outcome_value,
        market_start_date=_date_only(market.get("startDate") or market.get("startDateIso")),
        market_end_date=_date_only(market.get("endDate") or market.get("endDateIso")),
        market_closed=bool(market.get("closed")),
    )


def fetch_history_for_markets(
    *, client: httpx.Client, markets: Sequence[MarginThresholdMarket]
) -> dict[str, dict[str, pd.DataFrame]]:
    """Fetch bounded poll-window and late-window CLOB history for each market."""

    histories: dict[str, dict[str, pd.DataFrame]] = {}
    for market in markets:
        histories[market.spec.market_slug] = {
            "poll_window": fetch_history_window(
                client=client,
                token_id=market.yes_token_id,
                start_date=POLL_WINDOW_START_FALLBACK,
                end_date=POLL_WINDOW_END_FALLBACK,
            ),
            "late_window": fetch_history_window(
                client=client,
                token_id=market.yes_token_id,
                start_date=LATE_CLOB_WINDOW_START,
                end_date=LATE_CLOB_WINDOW_END,
            ),
        }
    return histories


def fetch_history_window(
    *,
    client: httpx.Client,
    token_id: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Fetch public CLOB price history for one bounded date interval."""

    start_ts = pd.Timestamp(f"{start_date}T00:00:00Z")
    end_ts = pd.Timestamp(f"{end_date}T23:59:59Z")
    rows = []
    cursor = start_ts
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
        if not isinstance(history, list):
            raise ValueError("CLOB price-history response must contain a history list")
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
    frame = pd.DataFrame(rows).drop_duplicates()
    frame["price"] = pd.to_numeric(frame["price"], errors="raise")
    if not frame["price"].between(0.0, 1.0).all():
        raise ValueError("CLOB history prices must be in [0, 1]")
    return frame.sort_values("observed_at_utc").reset_index(drop=True)


def build_state_poll_pair_coverage(poll_rows: Sequence[dict[str, Any]]) -> pd.DataFrame:
    """Return date-paired REP/DEM 538 polling-average coverage by state."""

    frame = pd.DataFrame(poll_rows)
    required = {"date", "state", "cycle", "party", "pct_estimate"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"poll rows missing columns: {missing}")
    frame = frame.loc[
        (pd.to_numeric(frame["cycle"], errors="raise") == 2024)
        & frame["party"].astype(str).isin(["REP", "DEM"])
    ].copy()
    frame["date"] = frame["date"].astype(str)
    frame = frame.loc[
        (frame["date"] >= POLL_WINDOW_START_FALLBACK)
        & (frame["date"] <= POLL_WINDOW_END_FALLBACK)
    ].copy()
    if frame.empty:
        return pd.DataFrame(columns=["state", "poll_pair_count", "poll_first_date", "poll_last_date"])
    pairs = (
        frame.pivot_table(
            index=["state", "date"],
            columns="party",
            values="pct_estimate",
            aggfunc="first",
        )
        .reset_index()
        .dropna(subset=["REP", "DEM"])
    )
    if pairs.empty:
        return pd.DataFrame(columns=["state", "poll_pair_count", "poll_first_date", "poll_last_date"])
    return (
        pairs.groupby("state", as_index=False)
        .agg(
            poll_pair_count=("date", "size"),
            poll_first_date=("date", "min"),
            poll_last_date=("date", "max"),
        )
        .sort_values("state")
        .reset_index(drop=True)
    )


def build_readiness_frame(
    *,
    markets: Sequence[MarginThresholdMarket],
    poll_pairs: pd.DataFrame,
    history_by_slug: dict[str, dict[str, pd.DataFrame]],
) -> pd.DataFrame:
    """Build one readiness row per reviewed margin-threshold market."""

    poll_lookup = poll_pairs.set_index("state", drop=False) if not poll_pairs.empty else pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for market in markets:
        spec = market.spec
        if not poll_lookup.empty and spec.state in poll_lookup.index:
            poll = poll_lookup.loc[spec.state]
            poll_pair_count = int(poll["poll_pair_count"])
            poll_first_date = str(poll["poll_first_date"])
            poll_last_date = str(poll["poll_last_date"])
        else:
            poll_pair_count = 0
            poll_first_date = ""
            poll_last_date = ""

        histories = history_by_slug.get(spec.market_slug, {})
        poll_history = histories.get("poll_window", pd.DataFrame())
        late_history = histories.get("late_window", pd.DataFrame())
        has_polls = poll_pair_count > 0
        has_poll_window_history = not poll_history.empty
        compatible = has_polls and has_poll_window_history
        if compatible:
            status = "compatible_for_h1_brier"
            blocker = ""
            next_step = "Build a threshold-probability Brier comparison with the documented poll-margin transform."
        elif not has_polls:
            status = "blocked_by_missing_538_state_poll_rows"
            blocker = "The official preserved 538 general-election averages contain no REP/DEM state rows for this state in the reviewed window."
            next_step = "Exclude from H1 Brier scoring unless a source-compatible state polling average is curated and transformed."
        else:
            status = "blocked_by_no_temporal_overlap"
            blocker = "The reviewed Polymarket CLOB history begins after the preserved official 538 polling-average window."
            next_step = "Use only if a later traditional polling-average source is curated and the probability transform is documented before scoring."

        rows.append(
            {
                "candidate_id": spec.candidate_id,
                "state": spec.state,
                "threshold_points": spec.threshold_points,
                "market_slug": spec.market_slug,
                "question": market.question,
                "market_id": market.market_id,
                "condition_id": market.condition_id,
                "yes_token_id": market.yes_token_id,
                "outcome_value": market.outcome_value,
                "market_start_date": market.market_start_date,
                "market_end_date": market.market_end_date,
                "market_closed": market.market_closed,
                "poll_pair_count": poll_pair_count,
                "poll_first_date": poll_first_date,
                "poll_last_date": poll_last_date,
                "clob_points_during_538_poll_window": len(poll_history),
                "first_clob_during_538_poll_window": _first_timestamp(poll_history),
                "last_clob_during_538_poll_window": _last_timestamp(poll_history),
                "late_clob_points": len(late_history),
                "first_late_clob_timestamp_utc": _first_timestamp(late_history),
                "last_late_clob_timestamp_utc": _last_timestamp(late_history),
                "has_538_state_poll_rows": has_polls,
                "has_clob_history_during_538_poll_window": has_poll_window_history,
                "compatible_for_h1_brier_now": compatible,
                "status": status,
                "main_blocker": blocker,
                "required_next_step": next_step,
                "poll_average_source_url": FIVETHIRTYEIGHT_POLL_AVERAGES_URL,
                "clob_source_url": f"{CLOB_BASE_URL}/prices-history",
                "polymarket_source_url": f"https://polymarket.com/event/{spec.market_slug}",
            }
        )
    return pd.DataFrame(rows, columns=READINESS_COLUMNS)


def validate_readiness_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate the margin-threshold readiness artifact."""

    missing = sorted(set(READINESS_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"readiness frame missing columns: {missing}")
    forbidden = [
        column
        for column in frame.columns
        if any(token in column.lower() for token in ("wallet", "maker", "taker", "address"))
    ]
    if forbidden:
        raise ValueError(f"readiness frame contains forbidden raw-trade columns: {forbidden}")
    normalized = frame.loc[:, list(READINESS_COLUMNS)].copy()
    if normalized.empty:
        raise ValueError("readiness frame must not be empty")
    if normalized["candidate_id"].duplicated().any():
        raise ValueError("readiness candidate IDs must be unique")
    for column in (
        "threshold_points",
        "outcome_value",
        "poll_pair_count",
        "clob_points_during_538_poll_window",
        "late_clob_points",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    for column in (
        "market_closed",
        "has_538_state_poll_rows",
        "has_clob_history_during_538_poll_window",
        "compatible_for_h1_brier_now",
    ):
        normalized[column] = normalized[column].astype(bool)
    if not normalized["outcome_value"].isin([0.0, 1.0]).all():
        raise ValueError("outcome_value must be binary")
    compatible = normalized["compatible_for_h1_brier_now"]
    if (
        normalized.loc[compatible, "has_538_state_poll_rows"].eq(False).any()
        or normalized.loc[compatible, "has_clob_history_during_538_poll_window"].eq(False).any()
    ):
        raise ValueError("compatible rows must have both poll rows and CLOB overlap")
    if normalized["status"].fillna("").astype(str).str.strip().eq("").any():
        raise ValueError("readiness status must not be blank")
    return normalized.sort_values(["state", "threshold_points"]).reset_index(drop=True)


def write_readiness_figure(*, readiness: pd.DataFrame, output_path: Path) -> Path:
    """Write a compact readiness diagnostic figure."""

    candidate_count = len(readiness)
    with_polls = int(readiness["has_538_state_poll_rows"].sum())
    with_poll_window_clob = int(readiness["has_clob_history_during_538_poll_window"].sum())
    compatible = int(readiness["compatible_for_h1_brier_now"].sum())

    fig, axes = plt.subplots(1, 2, figsize=(13.8, 5.5), gridspec_kw={"width_ratios": [1.0, 1.25]})
    fig.suptitle("H1 Margin-Threshold Market Readiness", fontsize=14, fontweight="bold")

    labels = [
        "Reviewed\nmarkets",
        "With 538\nstate polls",
        "With CLOB\npoll-window points",
        "Brier-compatible\nnow",
    ]
    values = [candidate_count, with_polls, with_poll_window_clob, compatible]
    axes[0].bar(labels, values, color=["#475569", "#7c3aed", "#f59e0b", "#059669"])
    axes[0].set_ylabel("Market count")
    axes[0].set_title("Compatibility funnel")
    axes[0].set_ylim(0, max(values) + 1.2)
    axes[0].grid(True, axis="y", alpha=0.25)
    for idx, value in enumerate(values):
        axes[0].text(idx, value + 0.12, str(value), ha="center", fontsize=9)

    timeline = readiness.sort_values(["state", "threshold_points"]).reset_index(drop=True)
    y = list(range(len(timeline)))
    axes[1].barh(
        y,
        timeline["poll_pair_count"],
        color=["#7c3aed" if value else "#d1d5db" for value in timeline["poll_pair_count"]],
    )
    axes[1].set_yticks(
        y,
        [f"{row.state} +{int(row.threshold_points)}" for row in timeline.itertuples()],
    )
    axes[1].invert_yaxis()
    axes[1].set_xlabel("538 REP/DEM poll-average date pairs through 2024-09-12")
    axes[1].set_title("Poll rows exist, but CLOB overlap is absent")
    max_pairs = float(timeline["poll_pair_count"].max()) if not timeline.empty else 1.0
    axes[1].set_xlim(0, max_pairs + 35.0)
    axes[1].grid(True, axis="x", alpha=0.25)
    for idx, row in enumerate(timeline.itertuples()):
        late = int(row.late_clob_points)
        text = f"late CLOB: {late}"
        axes[1].text(
            max(float(row.poll_pair_count), 1.0) + 2.0,
            idx,
            text,
            va="center",
            fontsize=8.5,
        )

    fig.text(
        0.5,
        0.015,
        (
            "No candidate has CLOB history inside the official preserved 538 polling-average window; "
            "therefore no new H1 Brier cases are added."
        ),
        ha="center",
        fontsize=9,
        color="#374151",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.06, 1, 0.92))
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return output_path


def build_metadata(
    *,
    source: str,
    readiness: pd.DataFrame,
    readiness_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for the margin-threshold readiness audit."""

    values = _summary_values(readiness)
    statuses = readiness["status"].value_counts().to_dict()
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_margin_threshold_readiness_audit",
            "calculation_scope": "deterministic_python_source_compatibility_audit",
            "source": source,
            "poll_window_start": POLL_WINDOW_START_FALLBACK,
            "poll_window_end": POLL_WINDOW_END_FALLBACK,
            "late_clob_window_start": LATE_CLOB_WINDOW_START,
            "late_clob_window_end": LATE_CLOB_WINDOW_END,
            "history_fidelity_minutes": HISTORY_FIDELITY_MINUTES,
            "history_chunk_days": HISTORY_CHUNK_DAYS,
            "does_not_compute_brier_scores": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "does_not_use_order_endpoints": True,
        },
        "outputs": {
            "candidate_count": values["candidate_count"],
            "candidates_with_538_state_polls": values["with_538_polls"],
            "candidates_with_clob_poll_window_history": values["with_poll_window_clob"],
            "compatible_candidate_count": values["compatible"],
            "late_clob_candidate_count": int((readiness["late_clob_points"] > 0).sum()),
            "status_counts": {str(key): int(value) for key, value in statuses.items()},
            "brier_rows_added": 0,
            "broad_many_cases_claim_supported_now": False,
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "source_paths": {
            "readiness": str(readiness_output),
            "figure": str(figure_output),
        },
        "source_urls": {
            "poll_average_source": FIVETHIRTYEIGHT_POLL_AVERAGES_URL,
            "gamma_events": f"{GAMMA_BASE_URL}/events",
            "clob_prices_history": f"{CLOB_BASE_URL}/prices-history",
        },
        "limitations": {
            "audits_reviewed_threshold_candidates_only": True,
            "no_new_brier_evidence_without_temporal_overlap": True,
            "official_538_preserved_file_ends_before_late_threshold_market_history": True,
            "later_traditional_poll_source_would_need_new_documented_transform": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def mock_margin_threshold_markets() -> list[MarginThresholdMarket]:
    """Return deterministic market metadata for tests and offline generation."""

    rows: list[MarginThresholdMarket] = []
    for spec in MARGIN_THRESHOLD_SPECS:
        outcome = 0.0 if spec.state in {"Ohio", "Wyoming"} else 1.0
        rows.append(
            MarginThresholdMarket(
                spec=spec,
                question=f"Will Trump win {spec.state} by {spec.threshold_points}+ points?",
                market_id=f"mock-{spec.candidate_id}",
                condition_id=f"condition-{spec.candidate_id}",
                yes_token_id=f"token-{spec.candidate_id}-yes",
                outcome_value=outcome,
                market_start_date="2024-10-24",
                market_end_date="2024-11-05",
                market_closed=True,
            )
        )
    return rows


def mock_poll_average_rows() -> list[dict[str, Any]]:
    """Return a small 538-style fixture with partial state coverage."""

    specs = [
        ("Florida", "2024-09-11", 48.0, 44.0),
        ("Florida", "2024-09-12", 48.2, 44.1),
        ("Ohio", "2024-09-11", 50.0, 42.0),
        ("Ohio", "2024-09-12", 50.3, 41.8),
        ("Texas", "2024-09-11", 49.0, 43.0),
        ("Texas", "2024-09-12", 49.1, 42.8),
    ]
    rows: list[dict[str, Any]] = []
    for state, date, rep, dem in specs:
        rows.append({"date": date, "state": state, "cycle": 2024, "party": "REP", "pct_estimate": rep})
        rows.append({"date": date, "state": state, "cycle": 2024, "party": "DEM", "pct_estimate": dem})
    return rows


def mock_history_by_slug() -> dict[str, dict[str, pd.DataFrame]]:
    """Return no poll-window overlap and some late CLOB points."""

    histories: dict[str, dict[str, pd.DataFrame]] = {}
    for spec in MARGIN_THRESHOLD_SPECS:
        late = pd.DataFrame(
            [
                {
                    "observed_at_utc": pd.Timestamp("2024-10-25T00:00:03Z"),
                    "price": 0.6,
                }
            ]
        )
        histories[spec.market_slug] = {
            "poll_window": pd.DataFrame(columns=["observed_at_utc", "price"]),
            "late_window": late,
        }
    return histories


def _summary_values(readiness: pd.DataFrame) -> dict[str, int]:
    return {
        "candidate_count": int(len(readiness)),
        "with_538_polls": int(readiness["has_538_state_poll_rows"].sum()),
        "with_poll_window_clob": int(readiness["has_clob_history_during_538_poll_window"].sum()),
        "compatible": int(readiness["compatible_for_h1_brier_now"].sum()),
    }


def _parse_json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value is None:
        return []
    parsed = json.loads(str(value))
    if not isinstance(parsed, list):
        raise ValueError("Gamma list field must decode to a list")
    return [str(item) for item in parsed]


def _outcome_index(outcomes: Sequence[str], label: str) -> int:
    for index, outcome in enumerate(outcomes):
        if str(outcome).strip().lower() == label.lower():
            return index
    raise ValueError(f"Gamma market is missing {label!r} outcome")


def _safe_float(value: Any) -> float:
    if value is None or str(value).strip() == "":
        return float("nan")
    return float(value)


def _date_only(value: Any) -> str:
    if value is None or str(value).strip() == "":
        return ""
    return pd.Timestamp(str(value)).date().isoformat()


def _history_timestamp(value: Any) -> pd.Timestamp:
    timestamp = float(value)
    if timestamp > 10_000_000_000:
        timestamp = timestamp / 1000.0
    return pd.Timestamp(datetime.fromtimestamp(timestamp, tz=UTC))


def _first_timestamp(frame: pd.DataFrame) -> str:
    if frame.empty:
        return ""
    return _format_timestamp(frame["observed_at_utc"].min())


def _last_timestamp(frame: pd.DataFrame) -> str:
    if frame.empty:
        return ""
    return _format_timestamp(frame["observed_at_utc"].max())


def _format_timestamp(value: Any) -> str:
    return pd.Timestamp(value).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("mock", "live"), default="mock")
    parser.add_argument("--readiness-output", type=Path, default=READINESS_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_margin_threshold_readiness_outputs(
            source=args.source,
            readiness_output=args.readiness_output,
            figure_output=args.figure_output,
            metadata_output=args.metadata_output,
        )
    except (httpx.HTTPError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
