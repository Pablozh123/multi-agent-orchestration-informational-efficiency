"""Build a bounded final case study for the Swiss 10-million referendum.

The module maps the official 14 June 2026 result to local Polymarket and poll
artifacts. It calculates all comparison values deterministically in Python and
keeps the two interpretation modes separate:

* vote-share proximity to the official Yes share, and
* binary outcome proxy scoring for the rejected initiative.

Poll shares are survey shares, not true model-implied win probabilities.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from operations.analysis.run_h2_event_windows import RESULTS_DIR


OFFICIAL_RESULT_INPUT = Path("data/swiss_referendum_10mio_official_result.csv")
POLL_INPUT = Path("data/swiss_referendum_10mio_polls.csv")
COMPARISON_INPUT = RESULTS_DIR / "swiss_referendum_10mio_comparison.csv"
LATEST_SOURCE_COMPARISON_INPUT = (
    RESULTS_DIR / "swiss_referendum_10mio_latest_source_comparison.csv"
)
PRICE_HISTORY_INPUT = RESULTS_DIR / "swiss_referendum_10mio_polymarket_price_history.csv"

FINAL_CASE_STUDY_OUTPUT = RESULTS_DIR / "swiss_referendum_10mio_final_case_study.csv"
POLL_ACCURACY_OUTPUT = RESULTS_DIR / "swiss_referendum_10mio_poll_accuracy.csv"
LIVE_ACCURACY_OUTPUT = RESULTS_DIR / "swiss_referendum_10mio_live_accuracy_windows.csv"
HISTORY_ACCURACY_OUTPUT = RESULTS_DIR / "swiss_referendum_10mio_history_accuracy_windows.csv"
FIGURE_OUTPUT = RESULTS_DIR / "swiss_referendum_10mio_final_case_study.png"
METADATA_OUTPUT = RESULTS_DIR / "swiss_referendum_10mio_final_case_study_metadata.json"
DOC_OUTPUT = Path("docs/research/SWISS_REFERENDUM_FINAL_CASE_STUDY.md")

OFFICIAL_RESULT_COLUMNS: tuple[str, ...] = (
    "referendum_id",
    "proposal_id",
    "vote_number",
    "vote_date",
    "official_title",
    "outcome",
    "official_yes_share",
    "official_no_share",
    "no_share_derivation",
    "yes_cantonal_votes",
    "no_cantonal_votes",
    "turnout",
    "official_dashboard_url",
    "result_reference_url",
    "source_note",
)

POLL_ACCURACY_COLUMNS: tuple[str, ...] = (
    "poll_id",
    "source_name",
    "fieldwork_start",
    "fieldwork_end",
    "published_at_utc",
    "final_poll_for_source",
    "yes_share",
    "no_share",
    "undecided_share",
    "poll_yes_decided_share",
    "official_yes_share",
    "raw_yes_signed_error",
    "raw_yes_abs_error",
    "decided_yes_signed_error",
    "decided_yes_abs_error",
    "raw_binary_brier_proxy",
    "decided_binary_brier_proxy",
    "poll_direction_against_50pct",
    "interpretation_scope",
)

ACCURACY_COLUMNS: tuple[str, ...] = (
    "observation_id",
    "observation_source",
    "observed_at_utc",
    "matched_poll_id",
    "matched_poll_source",
    "polymarket_yes_probability",
    "poll_yes_share",
    "poll_yes_decided_share",
    "official_yes_share",
    "official_outcome",
    "official_market_yes_outcome",
    "polymarket_vote_share_signed_error",
    "polymarket_vote_share_abs_error",
    "poll_raw_vote_share_abs_error",
    "poll_decided_vote_share_abs_error",
    "polymarket_binary_brier",
    "poll_raw_binary_brier_proxy",
    "poll_decided_binary_brier_proxy",
    "polymarket_beats_poll_raw_vote_share",
    "polymarket_beats_poll_decided_vote_share",
    "polymarket_beats_poll_raw_binary_proxy",
    "polymarket_beats_poll_decided_binary_proxy",
    "vote_share_accuracy_label",
    "binary_proxy_accuracy_label",
    "interpretation_scope",
)

FINAL_CASE_STUDY_COLUMNS: tuple[str, ...] = (
    "referendum_id",
    "vote_date",
    "official_title",
    "official_outcome",
    "official_yes_share",
    "official_no_share",
    "turnout",
    "yes_cantonal_votes",
    "no_cantonal_votes",
    "official_dashboard_url",
    "result_reference_url",
    "poll_rows",
    "live_observation_rows",
    "history_observation_rows",
    "latest_live_observed_at_utc",
    "latest_live_polymarket_yes_probability",
    "latest_live_polymarket_vote_share_abs_error",
    "latest_live_matched_poll_id",
    "latest_live_matched_poll_source",
    "latest_live_poll_yes_share",
    "latest_live_poll_raw_vote_share_abs_error",
    "latest_live_poll_yes_decided_share",
    "latest_live_poll_decided_vote_share_abs_error",
    "latest_live_polymarket_binary_brier",
    "latest_live_poll_raw_binary_brier_proxy",
    "latest_live_poll_decided_binary_brier_proxy",
    "live_polymarket_beats_raw_vote_share_count",
    "live_polymarket_beats_raw_vote_share_share",
    "live_polymarket_beats_decided_vote_share_count",
    "live_polymarket_beats_decided_vote_share_share",
    "live_polymarket_beats_raw_binary_proxy_count",
    "live_polymarket_beats_raw_binary_proxy_share",
    "live_polymarket_beats_decided_binary_proxy_count",
    "live_polymarket_beats_decided_binary_proxy_share",
    "history_polymarket_beats_raw_vote_share_count",
    "history_polymarket_beats_raw_vote_share_share",
    "history_polymarket_beats_decided_vote_share_count",
    "history_polymarket_beats_decided_vote_share_share",
    "history_first_raw_vote_share_beat_at_utc",
    "history_last_raw_vote_share_beat_at_utc",
    "history_first_decided_vote_share_beat_at_utc",
    "history_last_decided_vote_share_beat_at_utc",
    "best_history_vote_share_observed_at_utc",
    "best_history_polymarket_yes_probability",
    "best_history_polymarket_vote_share_abs_error",
    "best_live_vote_share_observed_at_utc",
    "best_live_polymarket_yes_probability",
    "best_live_polymarket_vote_share_abs_error",
    "bounded_conclusion_de",
    "main_limitation_de",
)


@dataclass(frozen=True)
class SwissReferendumFinalCaseStudyResult:
    """Paths and key counts for the final Swiss referendum case study."""

    final_case_study_path: Path
    poll_accuracy_path: Path
    live_accuracy_path: Path
    history_accuracy_path: Path
    figure_path: Path
    metadata_path: Path
    docs_path: Path
    live_observation_rows: int
    history_observation_rows: int
    live_vote_share_better_count: int
    history_vote_share_better_count: int

    def to_dict(self) -> dict[str, int | str]:
        return {
            "final_case_study_path": str(self.final_case_study_path),
            "poll_accuracy_path": str(self.poll_accuracy_path),
            "live_accuracy_path": str(self.live_accuracy_path),
            "history_accuracy_path": str(self.history_accuracy_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "docs_path": str(self.docs_path),
            "live_observation_rows": self.live_observation_rows,
            "history_observation_rows": self.history_observation_rows,
            "live_vote_share_better_count": self.live_vote_share_better_count,
            "history_vote_share_better_count": self.history_vote_share_better_count,
        }


def generate_swiss_referendum_final_case_study_outputs(
    *,
    official_result_path: Path = OFFICIAL_RESULT_INPUT,
    poll_input_path: Path = POLL_INPUT,
    comparison_path: Path = COMPARISON_INPUT,
    latest_source_comparison_path: Path = LATEST_SOURCE_COMPARISON_INPUT,
    price_history_path: Path = PRICE_HISTORY_INPUT,
    final_case_study_path: Path = FINAL_CASE_STUDY_OUTPUT,
    poll_accuracy_path: Path = POLL_ACCURACY_OUTPUT,
    live_accuracy_path: Path = LIVE_ACCURACY_OUTPUT,
    history_accuracy_path: Path = HISTORY_ACCURACY_OUTPUT,
    figure_path: Path = FIGURE_OUTPUT,
    metadata_path: Path = METADATA_OUTPUT,
    docs_path: Path = DOC_OUTPUT,
) -> SwissReferendumFinalCaseStudyResult:
    """Generate deterministic final case study artifacts."""

    official = read_official_result(official_result_path)
    polls = _read_csv(poll_input_path, name="poll catalog")
    comparisons = _read_csv(comparison_path, name="live comparison")
    latest_source = _read_csv(latest_source_comparison_path, name="latest source comparison")
    history = _read_optional_csv(price_history_path)

    poll_accuracy = build_poll_accuracy_rows(polls=polls, official=official)
    live_accuracy = build_live_accuracy_rows(comparisons=comparisons, official=official)
    history_accuracy = build_history_accuracy_rows(
        history=history,
        polls=polls,
        official=official,
    )
    final_case = build_final_case_study_rows(
        official=official,
        poll_accuracy=poll_accuracy,
        live_accuracy=live_accuracy,
        history_accuracy=history_accuracy,
        latest_source=latest_source,
    )

    for path in (
        final_case_study_path,
        poll_accuracy_path,
        live_accuracy_path,
        history_accuracy_path,
        figure_path,
        metadata_path,
        docs_path,
    ):
        path.parent.mkdir(parents=True, exist_ok=True)

    final_case.to_csv(final_case_study_path, index=False)
    poll_accuracy.to_csv(poll_accuracy_path, index=False)
    live_accuracy.to_csv(live_accuracy_path, index=False)
    history_accuracy.to_csv(history_accuracy_path, index=False)
    _write_figure(
        poll_accuracy=poll_accuracy,
        live_accuracy=live_accuracy,
        history_accuracy=history_accuracy,
        figure_path=figure_path,
    )
    docs_path.write_text(
        _render_case_study_doc(
            final_case=final_case,
            poll_accuracy=poll_accuracy,
            live_accuracy=live_accuracy,
            history_accuracy=history_accuracy,
            figure_path=figure_path,
        ),
        encoding="utf-8",
    )
    metadata_path.write_text(
        json.dumps(
            _build_metadata(
                official_result_path=official_result_path,
                poll_input_path=poll_input_path,
                comparison_path=comparison_path,
                latest_source_comparison_path=latest_source_comparison_path,
                price_history_path=price_history_path,
                final_case_study_path=final_case_study_path,
                poll_accuracy_path=poll_accuracy_path,
                live_accuracy_path=live_accuracy_path,
                history_accuracy_path=history_accuracy_path,
                figure_path=figure_path,
                docs_path=docs_path,
                official=official,
                poll_accuracy=poll_accuracy,
                live_accuracy=live_accuracy,
                history_accuracy=history_accuracy,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return SwissReferendumFinalCaseStudyResult(
        final_case_study_path=final_case_study_path,
        poll_accuracy_path=poll_accuracy_path,
        live_accuracy_path=live_accuracy_path,
        history_accuracy_path=history_accuracy_path,
        figure_path=figure_path,
        metadata_path=metadata_path,
        docs_path=docs_path,
        live_observation_rows=int(len(live_accuracy)),
        history_observation_rows=int(len(history_accuracy)),
        live_vote_share_better_count=int(
            live_accuracy["polymarket_beats_poll_raw_vote_share"].sum()
        ),
        history_vote_share_better_count=int(
            history_accuracy["polymarket_beats_poll_raw_vote_share"].sum()
        ),
    )


def read_official_result(path: Path = OFFICIAL_RESULT_INPUT) -> dict[str, Any]:
    """Read and validate the curated official referendum result."""

    frame = _read_csv(path, name="official referendum result")
    missing = [column for column in OFFICIAL_RESULT_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"official result missing required columns: {missing}")
    if len(frame) != 1:
        raise ValueError("official result must contain exactly one row")
    row = frame.iloc[0].to_dict()
    for column in (
        "official_yes_share",
        "official_no_share",
        "turnout",
        "yes_cantonal_votes",
        "no_cantonal_votes",
    ):
        row[column] = float(row[column])
    for column in ("official_yes_share", "official_no_share", "turnout"):
        if not 0.0 <= row[column] <= 1.0:
            raise ValueError(f"official result {column} must be between 0 and 1")
    if abs(row["official_yes_share"] + row["official_no_share"] - 1.0) > 0.001:
        raise ValueError("official yes and no shares must sum to 1")
    if str(row["outcome"]) not in {"accepted", "rejected"}:
        raise ValueError("official outcome must be accepted or rejected")
    pd.to_datetime(str(row["vote_date"]), errors="raise")
    for column in ("official_dashboard_url", "result_reference_url"):
        if not str(row[column]).startswith("https://"):
            raise ValueError(f"official result {column} must be an https URL")
    return row


def build_poll_accuracy_rows(*, polls: pd.DataFrame, official: dict[str, Any]) -> pd.DataFrame:
    """Compare every curated poll row with the official Yes share."""

    required = {
        "poll_id",
        "source_name",
        "fieldwork_start",
        "fieldwork_end",
        "published_at_utc",
        "yes_share",
        "no_share",
        "undecided_share",
    }
    _require_columns(polls, required, "poll catalog")
    official_yes = float(official["official_yes_share"])
    outcome_binary = _official_market_yes_outcome(official)
    frame = polls.copy()
    for column in ("yes_share", "no_share", "undecided_share"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    frame["published_ts"] = pd.to_datetime(frame["published_at_utc"], utc=True)
    frame["poll_yes_decided_share"] = frame["yes_share"] / (
        frame["yes_share"] + frame["no_share"]
    )
    frame["final_poll_for_source"] = (
        frame["published_ts"]
        == frame.groupby("source_name")["published_ts"].transform("max")
    )
    frame["official_yes_share"] = official_yes
    frame["raw_yes_signed_error"] = frame["yes_share"] - official_yes
    frame["raw_yes_abs_error"] = frame["raw_yes_signed_error"].abs()
    frame["decided_yes_signed_error"] = frame["poll_yes_decided_share"] - official_yes
    frame["decided_yes_abs_error"] = frame["decided_yes_signed_error"].abs()
    frame["raw_binary_brier_proxy"] = (frame["yes_share"] - outcome_binary) ** 2
    frame["decided_binary_brier_proxy"] = (
        frame["poll_yes_decided_share"] - outcome_binary
    ) ** 2
    frame["poll_direction_against_50pct"] = frame["yes_share"].map(
        lambda value: "raw_yes_below_50pct_rejection_direction"
        if float(value) < 0.5
        else "raw_yes_at_or_above_50pct_acceptance_direction"
    )
    frame["interpretation_scope"] = (
        "poll_vote_share_accuracy_and_binary_proxy_not_true_win_probability"
    )
    return frame.loc[:, list(POLL_ACCURACY_COLUMNS)].sort_values(
        ["published_at_utc", "poll_id"]
    )


def build_live_accuracy_rows(
    *,
    comparisons: pd.DataFrame,
    official: dict[str, Any],
) -> pd.DataFrame:
    """Compare live comparison rows with the official result."""

    required = {
        "comparison_id",
        "collected_at_utc",
        "polymarket_yes_probability",
        "poll_id",
        "poll_source",
        "poll_yes_share",
        "poll_yes_decided_share",
    }
    _require_columns(comparisons, required, "live comparison")
    frame = comparisons.copy()
    frame = frame.rename(
        columns={
            "comparison_id": "observation_id",
            "collected_at_utc": "observed_at_utc",
            "poll_id": "matched_poll_id",
            "poll_source": "matched_poll_source",
        }
    )
    frame["observation_source"] = "live_snapshot"
    return _build_accuracy_frame(frame=frame, official=official)


def build_history_accuracy_rows(
    *,
    history: pd.DataFrame,
    polls: pd.DataFrame,
    official: dict[str, Any],
) -> pd.DataFrame:
    """Compare bounded Polymarket price-history rows with their poll window."""

    if history.empty:
        return pd.DataFrame(columns=ACCURACY_COLUMNS)
    _require_columns(
        history,
        {"observed_at_utc", "poll_id", "yes_probability"},
        "Polymarket price history",
    )
    _require_columns(polls, {"poll_id", "source_name", "yes_share", "no_share"}, "poll catalog")
    poll_fields = polls.loc[:, ["poll_id", "source_name", "yes_share", "no_share"]].copy()
    poll_fields = poll_fields.rename(columns={"source_name": "poll_source_name"})
    poll_fields["poll_yes_decided_share"] = pd.to_numeric(
        poll_fields["yes_share"], errors="raise"
    ) / (
        pd.to_numeric(poll_fields["yes_share"], errors="raise")
        + pd.to_numeric(poll_fields["no_share"], errors="raise")
    )
    merged = history.merge(poll_fields, on="poll_id", how="left", validate="many_to_one")
    if merged["poll_source_name"].isna().any():
        missing = sorted(set(merged.loc[merged["poll_source_name"].isna(), "poll_id"].astype(str)))
        raise ValueError(f"price history contains unknown poll_id values: {missing}")
    frame = pd.DataFrame(
        {
            "observation_id": [
                f"hist_{_timestamp_id(value)}_{poll_id}"
                for value, poll_id in zip(merged["observed_at_utc"], merged["poll_id"])
            ],
            "observation_source": "price_history_poll_window",
            "observed_at_utc": merged["observed_at_utc"],
            "matched_poll_id": merged["poll_id"],
            "matched_poll_source": merged["poll_source_name"],
            "polymarket_yes_probability": merged["yes_probability"],
            "poll_yes_share": merged["yes_share"],
            "poll_yes_decided_share": merged["poll_yes_decided_share"],
        }
    )
    return _build_accuracy_frame(frame=frame, official=official)


def build_final_case_study_rows(
    *,
    official: dict[str, Any],
    poll_accuracy: pd.DataFrame,
    live_accuracy: pd.DataFrame,
    history_accuracy: pd.DataFrame,
    latest_source: pd.DataFrame,
) -> pd.DataFrame:
    """Build the one-row final case study summary."""

    _require_columns(
        latest_source,
        {"source_name", "poll_id", "polymarket_snapshot_at_utc"},
        "latest source comparison",
    )
    if live_accuracy.empty:
        raise ValueError("live accuracy must contain at least one row")
    latest_live = live_accuracy.sort_values("observed_at_utc").iloc[-1]
    best_live = live_accuracy.sort_values(
        ["polymarket_vote_share_abs_error", "observed_at_utc"]
    ).iloc[0]
    if history_accuracy.empty:
        best_history = None
    else:
        best_history = history_accuracy.sort_values(
            ["polymarket_vote_share_abs_error", "observed_at_utc"]
        ).iloc[0]

    live_raw_count, live_raw_share = _count_and_share(
        live_accuracy, "polymarket_beats_poll_raw_vote_share"
    )
    live_decided_count, live_decided_share = _count_and_share(
        live_accuracy, "polymarket_beats_poll_decided_vote_share"
    )
    live_binary_raw_count, live_binary_raw_share = _count_and_share(
        live_accuracy, "polymarket_beats_poll_raw_binary_proxy"
    )
    live_binary_decided_count, live_binary_decided_share = _count_and_share(
        live_accuracy, "polymarket_beats_poll_decided_binary_proxy"
    )
    hist_raw_count, hist_raw_share = _count_and_share(
        history_accuracy, "polymarket_beats_poll_raw_vote_share"
    )
    hist_decided_count, hist_decided_share = _count_and_share(
        history_accuracy, "polymarket_beats_poll_decided_vote_share"
    )

    row = {
        "referendum_id": official["referendum_id"],
        "vote_date": official["vote_date"],
        "official_title": official["official_title"],
        "official_outcome": official["outcome"],
        "official_yes_share": official["official_yes_share"],
        "official_no_share": official["official_no_share"],
        "turnout": official["turnout"],
        "yes_cantonal_votes": official["yes_cantonal_votes"],
        "no_cantonal_votes": official["no_cantonal_votes"],
        "official_dashboard_url": official["official_dashboard_url"],
        "result_reference_url": official["result_reference_url"],
        "poll_rows": int(len(poll_accuracy)),
        "live_observation_rows": int(len(live_accuracy)),
        "history_observation_rows": int(len(history_accuracy)),
        "latest_live_observed_at_utc": latest_live["observed_at_utc"],
        "latest_live_polymarket_yes_probability": latest_live[
            "polymarket_yes_probability"
        ],
        "latest_live_polymarket_vote_share_abs_error": latest_live[
            "polymarket_vote_share_abs_error"
        ],
        "latest_live_matched_poll_id": latest_live["matched_poll_id"],
        "latest_live_matched_poll_source": latest_live["matched_poll_source"],
        "latest_live_poll_yes_share": latest_live["poll_yes_share"],
        "latest_live_poll_raw_vote_share_abs_error": latest_live[
            "poll_raw_vote_share_abs_error"
        ],
        "latest_live_poll_yes_decided_share": latest_live["poll_yes_decided_share"],
        "latest_live_poll_decided_vote_share_abs_error": latest_live[
            "poll_decided_vote_share_abs_error"
        ],
        "latest_live_polymarket_binary_brier": latest_live["polymarket_binary_brier"],
        "latest_live_poll_raw_binary_brier_proxy": latest_live[
            "poll_raw_binary_brier_proxy"
        ],
        "latest_live_poll_decided_binary_brier_proxy": latest_live[
            "poll_decided_binary_brier_proxy"
        ],
        "live_polymarket_beats_raw_vote_share_count": live_raw_count,
        "live_polymarket_beats_raw_vote_share_share": live_raw_share,
        "live_polymarket_beats_decided_vote_share_count": live_decided_count,
        "live_polymarket_beats_decided_vote_share_share": live_decided_share,
        "live_polymarket_beats_raw_binary_proxy_count": live_binary_raw_count,
        "live_polymarket_beats_raw_binary_proxy_share": live_binary_raw_share,
        "live_polymarket_beats_decided_binary_proxy_count": live_binary_decided_count,
        "live_polymarket_beats_decided_binary_proxy_share": live_binary_decided_share,
        "history_polymarket_beats_raw_vote_share_count": hist_raw_count,
        "history_polymarket_beats_raw_vote_share_share": hist_raw_share,
        "history_polymarket_beats_decided_vote_share_count": hist_decided_count,
        "history_polymarket_beats_decided_vote_share_share": hist_decided_share,
        "history_first_raw_vote_share_beat_at_utc": _first_timestamp(
            history_accuracy, "polymarket_beats_poll_raw_vote_share"
        ),
        "history_last_raw_vote_share_beat_at_utc": _last_timestamp(
            history_accuracy, "polymarket_beats_poll_raw_vote_share"
        ),
        "history_first_decided_vote_share_beat_at_utc": _first_timestamp(
            history_accuracy, "polymarket_beats_poll_decided_vote_share"
        ),
        "history_last_decided_vote_share_beat_at_utc": _last_timestamp(
            history_accuracy, "polymarket_beats_poll_decided_vote_share"
        ),
        "best_history_vote_share_observed_at_utc": ""
        if best_history is None
        else best_history["observed_at_utc"],
        "best_history_polymarket_yes_probability": ""
        if best_history is None
        else best_history["polymarket_yes_probability"],
        "best_history_polymarket_vote_share_abs_error": ""
        if best_history is None
        else best_history["polymarket_vote_share_abs_error"],
        "best_live_vote_share_observed_at_utc": best_live["observed_at_utc"],
        "best_live_polymarket_yes_probability": best_live["polymarket_yes_probability"],
        "best_live_polymarket_vote_share_abs_error": best_live[
            "polymarket_vote_share_abs_error"
        ],
        "bounded_conclusion_de": (
            "Als Stimmenanteilsvergleich waren die finalen Umfragen naeher am "
            "offiziellen Ja-Anteil; als binaere Ablehnungswahrscheinlichkeit "
            "lag Polymarket im lokalen Live-Fenster klarer auf der richtigen "
            "Ablehnungsseite."
        ),
        "main_limitation_de": (
            "Polymarket-Preise sind Annahmewahrscheinlichkeiten, Umfragen sind "
            "Stimmenanteile; die Binaerwerte fuer Umfragen sind deshalb nur "
            "Proxy-Vergleiche und kein Mispricing-, Tradeability- oder "
            "Effizienzbeweis."
        ),
    }
    return pd.DataFrame([row], columns=FINAL_CASE_STUDY_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official-result", type=Path, default=OFFICIAL_RESULT_INPUT)
    parser.add_argument("--poll-input", type=Path, default=POLL_INPUT)
    parser.add_argument("--comparison-input", type=Path, default=COMPARISON_INPUT)
    parser.add_argument(
        "--latest-source-comparison-input",
        type=Path,
        default=LATEST_SOURCE_COMPARISON_INPUT,
    )
    parser.add_argument("--price-history-input", type=Path, default=PRICE_HISTORY_INPUT)
    parser.add_argument("--final-case-output", type=Path, default=FINAL_CASE_STUDY_OUTPUT)
    parser.add_argument("--poll-accuracy-output", type=Path, default=POLL_ACCURACY_OUTPUT)
    parser.add_argument("--live-accuracy-output", type=Path, default=LIVE_ACCURACY_OUTPUT)
    parser.add_argument(
        "--history-accuracy-output",
        type=Path,
        default=HISTORY_ACCURACY_OUTPUT,
    )
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    parser.add_argument("--docs-output", type=Path, default=DOC_OUTPUT)
    args = parser.parse_args(argv)

    try:
        result = generate_swiss_referendum_final_case_study_outputs(
            official_result_path=args.official_result,
            poll_input_path=args.poll_input,
            comparison_path=args.comparison_input,
            latest_source_comparison_path=args.latest_source_comparison_input,
            price_history_path=args.price_history_input,
            final_case_study_path=args.final_case_output,
            poll_accuracy_path=args.poll_accuracy_output,
            live_accuracy_path=args.live_accuracy_output,
            history_accuracy_path=args.history_accuracy_output,
            figure_path=args.figure_output,
            metadata_path=args.metadata_output,
            docs_path=args.docs_output,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _build_accuracy_frame(*, frame: pd.DataFrame, official: dict[str, Any]) -> pd.DataFrame:
    official_yes = float(official["official_yes_share"])
    outcome_binary = _official_market_yes_outcome(official)
    normalized = frame.copy()
    for column in (
        "polymarket_yes_probability",
        "poll_yes_share",
        "poll_yes_decided_share",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
        if not normalized[column].between(0.0, 1.0).all():
            raise ValueError(f"{column} values must be between 0 and 1")
    normalized["observed_at_utc"] = pd.to_datetime(
        normalized["observed_at_utc"],
        utc=True,
    ).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    normalized["official_yes_share"] = official_yes
    normalized["official_outcome"] = str(official["outcome"])
    normalized["official_market_yes_outcome"] = outcome_binary
    normalized["polymarket_vote_share_signed_error"] = (
        normalized["polymarket_yes_probability"] - official_yes
    )
    normalized["polymarket_vote_share_abs_error"] = normalized[
        "polymarket_vote_share_signed_error"
    ].abs()
    normalized["poll_raw_vote_share_abs_error"] = (
        normalized["poll_yes_share"] - official_yes
    ).abs()
    normalized["poll_decided_vote_share_abs_error"] = (
        normalized["poll_yes_decided_share"] - official_yes
    ).abs()
    normalized["polymarket_binary_brier"] = (
        normalized["polymarket_yes_probability"] - outcome_binary
    ) ** 2
    normalized["poll_raw_binary_brier_proxy"] = (
        normalized["poll_yes_share"] - outcome_binary
    ) ** 2
    normalized["poll_decided_binary_brier_proxy"] = (
        normalized["poll_yes_decided_share"] - outcome_binary
    ) ** 2
    normalized["polymarket_beats_poll_raw_vote_share"] = (
        normalized["polymarket_vote_share_abs_error"]
        < normalized["poll_raw_vote_share_abs_error"]
    )
    normalized["polymarket_beats_poll_decided_vote_share"] = (
        normalized["polymarket_vote_share_abs_error"]
        < normalized["poll_decided_vote_share_abs_error"]
    )
    normalized["polymarket_beats_poll_raw_binary_proxy"] = (
        normalized["polymarket_binary_brier"]
        < normalized["poll_raw_binary_brier_proxy"]
    )
    normalized["polymarket_beats_poll_decided_binary_proxy"] = (
        normalized["polymarket_binary_brier"]
        < normalized["poll_decided_binary_brier_proxy"]
    )
    normalized["vote_share_accuracy_label"] = normalized.apply(
        lambda row: "polymarket_closer_to_official_yes_share"
        if row["polymarket_beats_poll_raw_vote_share"]
        else "matched_poll_raw_share_closer_to_official_yes_share",
        axis=1,
    )
    normalized["binary_proxy_accuracy_label"] = normalized.apply(
        lambda row: "polymarket_lower_binary_brier_than_poll_proxy"
        if row["polymarket_beats_poll_raw_binary_proxy"]
        else "poll_proxy_lower_binary_brier_than_polymarket",
        axis=1,
    )
    normalized["interpretation_scope"] = (
        "post_result_bounded_poll_proxy_not_true_mispricing_or_trade_signal"
    )
    return normalized.loc[:, list(ACCURACY_COLUMNS)].sort_values(
        ["observed_at_utc", "observation_id"]
    )


def _write_figure(
    *,
    poll_accuracy: pd.DataFrame,
    live_accuracy: pd.DataFrame,
    history_accuracy: pd.DataFrame,
    figure_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(11, 5.8))
    if not history_accuracy.empty:
        hist = history_accuracy.copy()
        hist["ts"] = pd.to_datetime(hist["observed_at_utc"], utc=True)
        ax.plot(
            hist["ts"],
            hist["polymarket_vote_share_abs_error"] * 100,
            color="#8ab6d6",
            linewidth=1.2,
            label="Polymarket history abs error",
        )
    live = live_accuracy.copy()
    live["ts"] = pd.to_datetime(live["observed_at_utc"], utc=True)
    ax.plot(
        live["ts"],
        live["polymarket_vote_share_abs_error"] * 100,
        color="#174a7c",
        linewidth=1.8,
        label="Polymarket live abs error",
    )
    polls = poll_accuracy.copy()
    polls["ts"] = pd.to_datetime(polls["published_at_utc"], utc=True)
    ax.scatter(
        polls["ts"],
        polls["raw_yes_abs_error"] * 100,
        marker="o",
        color="#d95f02",
        s=38,
        label="Poll raw Yes abs error",
        zorder=4,
    )
    ax.scatter(
        polls["ts"],
        polls["decided_yes_abs_error"] * 100,
        marker="^",
        color="#1b9e77",
        s=38,
        label="Poll decided Yes abs error",
        zorder=4,
    )
    ax.set_title("Swiss 10-million referendum: final vote-share error view")
    ax.set_ylabel("Absolute error vs official Yes share (percentage points)")
    ax.set_xlabel("Observation or poll publication time")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend(loc="upper left", frameon=False, fontsize=8)
    fig.autofmt_xdate(rotation=25)
    fig.tight_layout()
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)


def _render_case_study_doc(
    *,
    final_case: pd.DataFrame,
    poll_accuracy: pd.DataFrame,
    live_accuracy: pd.DataFrame,
    history_accuracy: pd.DataFrame,
    figure_path: Path,
) -> str:
    row = final_case.iloc[0]
    latest = live_accuracy.sort_values("observed_at_utc").iloc[-1]
    final_polls = poll_accuracy[poll_accuracy["final_poll_for_source"].astype(bool)]
    lines = [
        "# Swiss Referendum Final Case Study",
        "",
        "## Generated Or Inspected",
        "",
        (
            f"- Official result: {row['official_outcome']} on {row['vote_date']}; "
            f"official Yes share {_pct(row['official_yes_share'])}, "
            f"No share {_pct(row['official_no_share'])}, turnout {_pct(row['turnout'])}."
        ),
        (
            f"- Cantonal vote result: {row['yes_cantonal_votes']} Yes "
            f"and {row['no_cantonal_votes']} No cantonal votes."
        ),
        f"- Poll rows compared: {int(row['poll_rows'])}.",
        f"- Live Polymarket rows compared: {int(row['live_observation_rows'])}.",
        f"- Price-history rows compared: {int(row['history_observation_rows'])}.",
        (
            f"- Official sources: {row['result_reference_url']} and "
            f"{row['official_dashboard_url']}."
        ),
        "",
        "## Key Numerical Result",
        "",
        (
            f"- Latest live snapshot {row['latest_live_observed_at_utc']}: "
            f"Polymarket Yes {_pct(row['latest_live_polymarket_yes_probability'])}; "
            f"vote-share error {_pp(row['latest_live_polymarket_vote_share_abs_error'])}."
        ),
        (
            f"- Matched poll at latest live snapshot "
            f"({row['latest_live_matched_poll_source']} / "
            f"{row['latest_live_matched_poll_id']}): raw Yes "
            f"{_pct(row['latest_live_poll_yes_share'])}, raw error "
            f"{_pp(row['latest_live_poll_raw_vote_share_abs_error'])}; "
            f"decided Yes {_pct(row['latest_live_poll_yes_decided_share'])}, "
            f"decided error {_pp(row['latest_live_poll_decided_vote_share_abs_error'])}."
        ),
        (
            f"- Live vote-share comparison: Polymarket beats the matched raw poll "
            f"in {int(row['live_polymarket_beats_raw_vote_share_count'])}/"
            f"{int(row['live_observation_rows'])} rows and the matched decided-share "
            f"poll in {int(row['live_polymarket_beats_decided_vote_share_count'])}/"
            f"{int(row['live_observation_rows'])} rows."
        ),
        (
            f"- Live binary outcome proxy: Polymarket has lower Brier loss than "
            f"the raw poll proxy in "
            f"{int(row['live_polymarket_beats_raw_binary_proxy_count'])}/"
            f"{int(row['live_observation_rows'])} rows and than the decided-share "
            f"poll proxy in "
            f"{int(row['live_polymarket_beats_decided_binary_proxy_count'])}/"
            f"{int(row['live_observation_rows'])} rows."
        ),
        (
            f"- Historical price window: Polymarket is closer to the official "
            f"Yes share than the matched raw poll in "
            f"{int(row['history_polymarket_beats_raw_vote_share_count'])}/"
            f"{int(row['history_observation_rows'])} rows, first at "
            f"{row['history_first_raw_vote_share_beat_at_utc']} and last at "
            f"{row['history_last_raw_vote_share_beat_at_utc']}."
        ),
        (
            f"- Historical decided-share window: Polymarket beats the decided-share "
            f"poll proxy in {int(row['history_polymarket_beats_decided_vote_share_count'])}/"
            f"{int(row['history_observation_rows'])} rows, first at "
            f"{row['history_first_decided_vote_share_beat_at_utc']} and last at "
            f"{row['history_last_decided_vote_share_beat_at_utc']}."
        ),
        (
            f"- Best historical vote-share Polymarket point: "
            f"{row['best_history_vote_share_observed_at_utc']} with Yes "
            f"{_pct(row['best_history_polymarket_yes_probability'])} and error "
            f"{_pp(row['best_history_polymarket_vote_share_abs_error'])}."
        ),
        "",
        "## Final Poll Accuracy",
        "",
        *[
            (
                f"- {item['source_name']} final poll {item['poll_id']}: raw Yes "
                f"{_pct(item['yes_share'])}, raw error {_pp(item['raw_yes_abs_error'])}; "
                f"decided Yes {_pct(item['poll_yes_decided_share'])}, "
                f"decided error {_pp(item['decided_yes_abs_error'])}."
            )
            for item in final_polls.sort_values("source_name").to_dict(orient="records")
        ],
        "",
        "## Bounded Interpretation",
        "",
        (
            "- Stimmenanteilsvergleich: Die finalen Umfragen, besonders SRG/gfs.bern, "
            "lagen naeher am offiziellen Ja-Anteil von 45.21% als die spaeten "
            "Polymarket-Live-Snapshots. Deshalb darf das Fallbeispiel nicht als "
            "Beleg formuliert werden, dass Polymarket den Stimmenanteil genauer "
            "vorhergesagt hat."
        ),
        (
            "- Ergebnisrichtung: Die Initiative wurde abgelehnt. In der binaeren "
            "Proxy-Lesart zeigte Polymarket im lokalen Live-Fenster eine deutlich "
            "niedrigere Annahmewahrscheinlichkeit als die Umfrage-Ja-Anteile und "
            "damit ein staerkeres Ablehnungssignal."
        ),
        (
            "- Historisches Fenster: Vor dem spaeten Live-Fenster gab es einzelne "
            "Price-History-Zeilen, in denen Polymarket naeher am spaeteren "
            "Ja-Anteil lag als der jeweilige Poll-Proxy. Das ist ein begrenzter "
            "Timing-Befund, kein Effizienzbeweis."
        ),
        "",
        "## Main Limitation",
        "",
        (
            "- Polymarket-Preise messen eine Annahmewahrscheinlichkeit, Umfragen "
            "messen Stimmenanteile. Die Brier-Proxy-Zeilen fuer Umfragen sind "
            "deshalb nur ein transparenter Vergleichsmodus und keine echte "
            "Kalibrierungsstudie traditioneller Prognosemodelle."
        ),
        "",
        "## Figure",
        "",
        f"![Swiss final case study figure]({figure_path.name})",
    ]
    return "\n".join(lines) + "\n"


def _build_metadata(
    *,
    official_result_path: Path,
    poll_input_path: Path,
    comparison_path: Path,
    latest_source_comparison_path: Path,
    price_history_path: Path,
    final_case_study_path: Path,
    poll_accuracy_path: Path,
    live_accuracy_path: Path,
    history_accuracy_path: Path,
    figure_path: Path,
    docs_path: Path,
    official: dict[str, Any],
    poll_accuracy: pd.DataFrame,
    live_accuracy: pd.DataFrame,
    history_accuracy: pd.DataFrame,
) -> dict[str, Any]:
    final_case_summary = {
        "official_outcome": str(official["outcome"]),
        "official_yes_share": float(official["official_yes_share"]),
        "poll_rows": int(len(poll_accuracy)),
        "live_observation_rows": int(len(live_accuracy)),
        "history_observation_rows": int(len(history_accuracy)),
        "live_raw_vote_share_beats": int(
            live_accuracy["polymarket_beats_poll_raw_vote_share"].sum()
        ),
        "live_raw_binary_proxy_beats": int(
            live_accuracy["polymarket_beats_poll_raw_binary_proxy"].sum()
        ),
        "history_raw_vote_share_beats": int(
            history_accuracy["polymarket_beats_poll_raw_vote_share"].sum()
        ),
    }
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "swiss_referendum_final_case_study",
            "official_result_mapped": True,
            "vote_share_error_formula": "abs(predicted_yes_share_or_price - official_yes_share)",
            "binary_brier_formula": "(yes_probability_or_proxy - official_market_yes_outcome)^2",
            "official_market_yes_outcome": _official_market_yes_outcome(official),
            "poll_probability_transform": "none_for_vote_share; proxy_only_for_binary_outcome",
            "decided_share_formula": "yes_share / (yes_share + no_share)",
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_collect_external_data": True,
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "outputs": final_case_summary,
        "source_paths": {
            "official_result": str(official_result_path),
            "poll_input": str(poll_input_path),
            "comparison": str(comparison_path),
            "latest_source_comparison": str(latest_source_comparison_path),
            "price_history": str(price_history_path),
            "final_case_study": str(final_case_study_path),
            "poll_accuracy": str(poll_accuracy_path),
            "live_accuracy": str(live_accuracy_path),
            "history_accuracy": str(history_accuracy_path),
            "figure": str(figure_path),
            "docs": str(docs_path),
        },
        "limitations": {
            "polymarket_prices_are_not_vote_share_forecasts": True,
            "poll_shares_are_not_true_win_probabilities": True,
            "binary_poll_brier_is_proxy_only": True,
            "no_mispricing_claim": True,
            "no_tradeability_or_profitability_claim": True,
            "no_causal_claim_from_history_windows": True,
        },
    }


def _official_market_yes_outcome(official: dict[str, Any]) -> float:
    return 1.0 if str(official["outcome"]) == "accepted" else 0.0


def _count_and_share(frame: pd.DataFrame, column: str) -> tuple[int, float]:
    if frame.empty:
        return 0, 0.0
    count = int(frame[column].astype(bool).sum())
    return count, count / len(frame)


def _first_timestamp(frame: pd.DataFrame, column: str) -> str:
    if frame.empty:
        return ""
    selected = frame[frame[column].astype(bool)].sort_values("observed_at_utc")
    if selected.empty:
        return ""
    return str(selected.iloc[0]["observed_at_utc"])


def _last_timestamp(frame: pd.DataFrame, column: str) -> str:
    if frame.empty:
        return ""
    selected = frame[frame[column].astype(bool)].sort_values("observed_at_utc")
    if selected.empty:
        return ""
    return str(selected.iloc[-1]["observed_at_utc"])


def _timestamp_id(value: object) -> str:
    return pd.Timestamp(str(value)).tz_convert("UTC").strftime("%Y%m%dT%H%M%SZ")


def _pct(value: object) -> str:
    numeric = float(value)
    return f"{numeric * 100:.2f}%"


def _pp(value: object) -> str:
    numeric = float(value)
    return f"{numeric * 100:.2f} pp"


def _read_csv(path: Path, *, name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"{name} not found: {path}")
    return pd.read_csv(path)


def _read_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _require_columns(frame: pd.DataFrame, columns: set[str], name: str) -> None:
    missing = sorted(columns.difference(frame.columns))
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


if __name__ == "__main__":
    raise SystemExit(main())
