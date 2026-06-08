"""Compare Swiss referendum Polymarket snapshots with curated poll values.

This module creates deterministic comparison artifacts for the 14 June 2026
Swiss 10-million initiative market. Poll shares are treated as survey shares,
not as a model-implied win probability. The optional decided-voter share is a
transparent normalization of reported Yes and No shares only.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pandas as pd

from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.collectors.swiss_referendum_polymarket import SNAPSHOT_OUTPUT


POLL_INPUT = Path("data/swiss_referendum_10mio_polls.csv")
POLYMARKET_HISTORY_INPUT = (
    RESULTS_DIR / "swiss_referendum_10mio_polymarket_price_history.csv"
)
COMPARISON_OUTPUT = RESULTS_DIR / "swiss_referendum_10mio_comparison.csv"
LATEST_SOURCE_COMPARISON_OUTPUT = (
    RESULTS_DIR / "swiss_referendum_10mio_latest_source_comparison.csv"
)
POLL_IMPACT_OUTPUT = RESULTS_DIR / "swiss_referendum_10mio_poll_impacts.csv"
POLL_REACTION_WINDOWS_OUTPUT = (
    RESULTS_DIR / "swiss_referendum_10mio_poll_reaction_windows.csv"
)
SOURCE_AUDIT_OUTPUT = RESULTS_DIR / "swiss_referendum_10mio_source_audit.csv"
FIGURE_OUTPUT = RESULTS_DIR / "swiss_referendum_10mio_efficiency.png"
REACTION_FIGURE_OUTPUT = RESULTS_DIR / "swiss_referendum_10mio_reaction_windows.png"
DASHBOARD_OUTPUT = RESULTS_DIR / "swiss_referendum_10mio_dashboard.html"
SUMMARY_OUTPUT = RESULTS_DIR / "swiss_referendum_10mio_latest_summary.md"
METADATA_OUTPUT = RESULTS_DIR / "swiss_referendum_10mio_efficiency_metadata.json"

POLL_COLUMNS: tuple[str, ...] = (
    "poll_id",
    "referendum_id",
    "source_name",
    "source_type",
    "fieldwork_start",
    "fieldwork_end",
    "published_at_utc",
    "published_time_precision",
    "yes_share",
    "no_share",
    "undecided_share",
    "sample_size",
    "margin_error",
    "source_url",
    "notes",
)

COMPARISON_COLUMNS: tuple[str, ...] = (
    "comparison_id",
    "comparison_status",
    "collected_at_utc",
    "polymarket_yes_probability",
    "polymarket_no_probability",
    "poll_id",
    "poll_source",
    "poll_published_at_utc",
    "poll_age_hours",
    "poll_yes_share",
    "poll_no_share",
    "poll_undecided_share",
    "poll_yes_decided_share",
    "raw_yes_gap",
    "decided_yes_gap",
    "divergence_label",
    "poll_proxy_valuation_label",
    "valuation_scope",
)

LATEST_SOURCE_COMPARISON_COLUMNS: tuple[str, ...] = (
    "source_name",
    "poll_id",
    "poll_published_at_utc",
    "poll_age_hours",
    "polymarket_snapshot_at_utc",
    "polymarket_yes_probability",
    "poll_yes_share",
    "poll_yes_decided_share",
    "raw_yes_gap",
    "decided_yes_gap",
    "divergence_label",
    "poll_proxy_valuation_label",
    "valuation_scope",
)

IMPACT_COLUMNS: tuple[str, ...] = (
    "poll_id",
    "poll_source",
    "poll_published_at_utc",
    "impact_status",
    "pre_snapshot_at_utc",
    "post_snapshot_at_utc",
    "hours_to_first_post_snapshot",
    "pre_yes_probability",
    "post_yes_probability",
    "yes_probability_change",
    "yes_probability_change_1h",
    "yes_probability_change_6h",
    "yes_probability_change_24h",
    "yes_probability_change_48h",
)

SOURCE_AUDIT_COLUMNS: tuple[str, ...] = (
    "source_id",
    "source_name",
    "source_role",
    "source_url",
    "has_voting_intention_values",
    "included_in_poll_catalog",
    "notes",
)

POLL_REACTION_WINDOW_COLUMNS: tuple[str, ...] = (
    "poll_id",
    "poll_source",
    "poll_published_at_utc",
    "window_hours",
    "window_end_at_utc",
    "reaction_status",
    "impact_status",
    "pre_snapshot_at_utc",
    "pre_yes_probability",
    "yes_probability_change",
    "interpretation_scope",
)


@dataclass(frozen=True)
class SwissReferendumEfficiencyResult:
    """Summary of generated referendum comparison artifacts."""

    comparison_path: Path
    latest_source_comparison_path: Path
    poll_impact_path: Path
    poll_reaction_windows_path: Path
    source_audit_path: Path
    figure_path: Path
    reaction_figure_path: Path
    dashboard_path: Path
    summary_path: Path
    metadata_path: Path
    comparison_row_count: int
    poll_impact_row_count: int
    latest_raw_yes_gap: float | None
    latest_decided_yes_gap: float | None
    latest_divergence_label: str

    def to_dict(self) -> dict[str, float | int | str | None]:
        """Return a JSON-friendly summary."""

        return {
            "comparison_path": str(self.comparison_path),
            "latest_source_comparison_path": str(self.latest_source_comparison_path),
            "poll_impact_path": str(self.poll_impact_path),
            "poll_reaction_windows_path": str(self.poll_reaction_windows_path),
            "source_audit_path": str(self.source_audit_path),
            "figure_path": str(self.figure_path),
            "reaction_figure_path": str(self.reaction_figure_path),
            "dashboard_path": str(self.dashboard_path),
            "summary_path": str(self.summary_path),
            "metadata_path": str(self.metadata_path),
            "comparison_row_count": self.comparison_row_count,
            "poll_impact_row_count": self.poll_impact_row_count,
            "latest_raw_yes_gap": self.latest_raw_yes_gap,
            "latest_decided_yes_gap": self.latest_decided_yes_gap,
            "latest_divergence_label": self.latest_divergence_label,
        }


@dataclass(frozen=True)
class DashboardVerificationResult:
    """Deterministic verification summary for the local HTML dashboard."""

    dashboard_path: Path
    figure_path: Path
    title: str
    h1: str
    h2_sections: tuple[str, ...]
    table_count: int
    table_row_count: int
    image_count: int
    checked_figure_count: int
    figure_shape: tuple[int, ...]
    extra_figure_paths: tuple[Path, ...]
    figure_nonblank: bool
    required_text_present: bool

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly verification summary."""

        return {
            "dashboard_path": str(self.dashboard_path),
            "figure_path": str(self.figure_path),
            "title": self.title,
            "h1": self.h1,
            "h2_sections": list(self.h2_sections),
            "table_count": self.table_count,
            "table_row_count": self.table_row_count,
            "image_count": self.image_count,
            "checked_figure_count": self.checked_figure_count,
            "figure_shape": list(self.figure_shape),
            "extra_figure_paths": [str(path) for path in self.extra_figure_paths],
            "figure_nonblank": self.figure_nonblank,
            "required_text_present": self.required_text_present,
        }


def generate_swiss_referendum_efficiency_outputs(
    *,
    poll_input_path: Path = POLL_INPUT,
    polymarket_snapshots_path: Path = SNAPSHOT_OUTPUT,
    polymarket_history_path: Path | None = POLYMARKET_HISTORY_INPUT,
    comparison_path: Path = COMPARISON_OUTPUT,
    latest_source_comparison_path: Path = LATEST_SOURCE_COMPARISON_OUTPUT,
    poll_impact_path: Path = POLL_IMPACT_OUTPUT,
    poll_reaction_windows_path: Path = POLL_REACTION_WINDOWS_OUTPUT,
    source_audit_path: Path = SOURCE_AUDIT_OUTPUT,
    figure_path: Path = FIGURE_OUTPUT,
    reaction_figure_path: Path = REACTION_FIGURE_OUTPUT,
    dashboard_path: Path = DASHBOARD_OUTPUT,
    summary_path: Path = SUMMARY_OUTPUT,
    metadata_path: Path = METADATA_OUTPUT,
    divergence_threshold: float = 0.05,
) -> SwissReferendumEfficiencyResult:
    """Generate comparison CSV, poll-impact CSV, figure, HTML, and metadata."""

    if divergence_threshold < 0:
        raise ValueError("divergence_threshold must be >= 0")
    polls = read_poll_catalog(poll_input_path)
    snapshots = read_polymarket_snapshots(polymarket_snapshots_path)
    history = read_optional_polymarket_price_history(polymarket_history_path)
    price_points = combine_polymarket_observations(snapshots=snapshots, history=history)
    comparisons = build_comparison_rows(
        snapshots=snapshots,
        polls=polls,
        divergence_threshold=divergence_threshold,
    )
    latest_source_comparisons = build_latest_source_comparison_rows(
        snapshots=snapshots,
        polls=polls,
        divergence_threshold=divergence_threshold,
    )
    impacts = build_poll_impact_rows(snapshots=price_points, polls=polls)
    reaction_windows = build_poll_reaction_window_rows(impacts)
    source_audit = build_source_audit_rows(polls)

    comparison_path.parent.mkdir(parents=True, exist_ok=True)
    latest_source_comparison_path.parent.mkdir(parents=True, exist_ok=True)
    poll_reaction_windows_path.parent.mkdir(parents=True, exist_ok=True)
    source_audit_path.parent.mkdir(parents=True, exist_ok=True)
    comparisons.to_csv(comparison_path, index=False)
    latest_source_comparisons.to_csv(latest_source_comparison_path, index=False)
    impacts.to_csv(poll_impact_path, index=False)
    reaction_windows.to_csv(poll_reaction_windows_path, index=False)
    source_audit.to_csv(source_audit_path, index=False)
    _write_figure(
        snapshots=snapshots,
        history=history,
        polls=polls,
        comparisons=comparisons,
        figure_path=figure_path,
    )
    _write_reaction_window_figure(
        reaction_windows=reaction_windows,
        figure_path=reaction_figure_path,
    )
    latest = _latest_comparison(comparisons)
    dashboard_path.write_text(
        _render_dashboard(
            polls=polls,
            snapshots=snapshots,
            comparisons=comparisons,
            latest_source_comparisons=latest_source_comparisons,
            impacts=impacts,
            reaction_windows=reaction_windows,
            source_audit=source_audit,
            figure_path=figure_path,
            reaction_figure_path=reaction_figure_path,
            source_paths={
                "poll_input": poll_input_path,
                "polymarket_snapshots": polymarket_snapshots_path,
                "comparison": comparison_path,
                "latest_source_comparison": latest_source_comparison_path,
                "poll_impacts": poll_impact_path,
                "poll_reaction_windows": poll_reaction_windows_path,
                "source_audit": source_audit_path,
                "figure": figure_path,
                "reaction_figure": reaction_figure_path,
            },
        ),
        encoding="utf-8",
    )
    dashboard_verification = verify_dashboard_artifact(
        dashboard_path=dashboard_path,
        figure_path=figure_path,
        extra_figure_paths=(reaction_figure_path,),
        required_text=(
            "Swiss 10-Million Referendum Efficiency View",
            "Poll Reaction Window Figure",
            "Poll proxy relation",
            "Source Boundary Audit",
            "BFS/admin.ch is used as official referendum",
            "Bundesamt fuer Statistik",
            str(latest.get("poll_proxy_valuation_label", "")),
        ),
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        _render_latest_summary(
            polls=polls,
            snapshots=snapshots,
            history=history,
            comparisons=comparisons,
            latest_source_comparisons=latest_source_comparisons,
            impacts=impacts,
            reaction_windows=reaction_windows,
            source_audit=source_audit,
            figure_path=figure_path,
            reaction_figure_path=reaction_figure_path,
            dashboard_path=dashboard_path,
        ),
        encoding="utf-8",
    )

    metadata = _build_metadata(
        poll_input_path=poll_input_path,
        polymarket_snapshots_path=polymarket_snapshots_path,
        polymarket_history_path=polymarket_history_path,
        comparison_path=comparison_path,
        latest_source_comparison_path=latest_source_comparison_path,
        poll_impact_path=poll_impact_path,
        poll_reaction_windows_path=poll_reaction_windows_path,
        source_audit_path=source_audit_path,
        figure_path=figure_path,
        reaction_figure_path=reaction_figure_path,
        dashboard_path=dashboard_path,
        summary_path=summary_path,
        polls=polls,
        snapshots=snapshots,
        history=history,
        comparisons=comparisons,
        latest_source_comparisons=latest_source_comparisons,
        impacts=impacts,
        reaction_windows=reaction_windows,
        source_audit=source_audit,
        dashboard_verification=dashboard_verification,
        divergence_threshold=divergence_threshold,
    )
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return SwissReferendumEfficiencyResult(
        comparison_path=comparison_path,
        latest_source_comparison_path=latest_source_comparison_path,
        poll_impact_path=poll_impact_path,
        poll_reaction_windows_path=poll_reaction_windows_path,
        source_audit_path=source_audit_path,
        figure_path=figure_path,
        reaction_figure_path=reaction_figure_path,
        dashboard_path=dashboard_path,
        summary_path=summary_path,
        metadata_path=metadata_path,
        comparison_row_count=int(len(comparisons)),
        poll_impact_row_count=int(len(impacts)),
        latest_raw_yes_gap=_optional_float(latest.get("raw_yes_gap")),
        latest_decided_yes_gap=_optional_float(latest.get("decided_yes_gap")),
        latest_divergence_label=str(latest.get("divergence_label", "")),
    )


def read_poll_catalog(path: Path = POLL_INPUT) -> pd.DataFrame:
    """Read and validate the curated poll catalog."""

    if not path.exists():
        raise FileNotFoundError(f"poll catalog not found: {path}")
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = [column for column in POLL_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"poll catalog missing required columns: {missing}")
    normalized = frame.loc[:, list(POLL_COLUMNS)].copy()
    for column in POLL_COLUMNS:
        normalized[column] = normalized[column].fillna("").astype(str).str.strip()
    for column in ("yes_share", "no_share", "undecided_share", "margin_error"):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    normalized["sample_size"] = pd.to_numeric(
        normalized["sample_size"],
        errors="raise",
        downcast="integer",
    )
    for column in ("yes_share", "no_share", "undecided_share", "margin_error"):
        if not normalized[column].between(0.0, 1.0).all():
            raise ValueError(f"poll column {column!r} values must be between 0 and 1")
    share_sum = normalized["yes_share"] + normalized["no_share"] + normalized["undecided_share"]
    if not share_sum.between(0.98, 1.02).all():
        raise ValueError("poll yes/no/undecided shares must sum to approximately 1")
    for column in ("fieldwork_start", "fieldwork_end", "published_at_utc"):
        pd.to_datetime(normalized[column], errors="raise", utc=True)
    invalid_source = normalized[normalized["source_type"] != "poll"]
    if not invalid_source.empty:
        raise ValueError("poll catalog source_type must be 'poll' for every row")
    if normalized["poll_id"].duplicated().any():
        raise ValueError("poll_id values must be unique")
    return normalized.sort_values(["published_at_utc", "poll_id"]).reset_index(drop=True)


def build_source_audit_rows(polls: pd.DataFrame) -> pd.DataFrame:
    """Build an explicit source boundary audit for poll and context sources."""

    rows: list[dict[str, str | bool]] = [
        {
            "source_id": "admin_ch_referendum_context",
            "source_name": "admin.ch/Bundeskanzlei",
            "source_role": "official_referendum_context",
            "source_url": "https://www.admin.ch/de/nachhaltigkeitsinitiative",
            "has_voting_intention_values": False,
            "included_in_poll_catalog": False,
            "notes": "Official vote date and initiative context only.",
        },
        {
            "source_id": "bfs_population_scenarios_2025_2055",
            "source_name": "Bundesamt fuer Statistik",
            "source_role": "official_population_context",
            "source_url": "https://bevoelkerungsszenarien.bfs.admin.ch/",
            "has_voting_intention_values": False,
            "included_in_poll_catalog": False,
            "notes": "Population scenario context only; not a voting-intention poll.",
        },
    ]
    for _, row in polls.iterrows():
        rows.append(
            {
                "source_id": str(row["poll_id"]),
                "source_name": str(row["source_name"]),
                "source_role": "voting_intention_poll",
                "source_url": str(row["source_url"]),
                "has_voting_intention_values": True,
                "included_in_poll_catalog": True,
                "notes": "Curated poll row used for deterministic comparison.",
            }
        )
    audit = pd.DataFrame(rows, columns=SOURCE_AUDIT_COLUMNS)
    if audit["source_url"].fillna("").astype(str).str.strip().eq("").any():
        raise ValueError("source audit source_url values must not be blank")
    return audit


def verify_dashboard_artifact(
    *,
    dashboard_path: Path = DASHBOARD_OUTPUT,
    figure_path: Path = FIGURE_OUTPUT,
    extra_figure_paths: Sequence[Path] = (),
    required_text: Sequence[str] = (),
) -> DashboardVerificationResult:
    """Verify that the local dashboard and figure are present and coherent."""

    if not dashboard_path.exists():
        raise FileNotFoundError(f"dashboard not found: {dashboard_path}")
    checked_figure_paths = (figure_path, *tuple(extra_figure_paths))
    for checked_path in checked_figure_paths:
        if not checked_path.exists():
            raise FileNotFoundError(f"figure not found: {checked_path}")

    html = dashboard_path.read_text(encoding="utf-8")
    parser = _DashboardHtmlParser()
    parser.feed(html)
    figure = mpimg.imread(figure_path)
    figure_shape = tuple(int(value) for value in figure.shape)
    figure_nonblank = True
    for checked_path in checked_figure_paths:
        checked_figure = mpimg.imread(checked_path)
        if not bool(float(checked_figure.max()) > float(checked_figure.min())):
            figure_nonblank = False
    required_text_present = all(str(item) in html for item in required_text if str(item))

    if parser.title != "Swiss 10-Million Referendum Efficiency View":
        raise ValueError("dashboard title is missing or unexpected")
    if parser.h1 != "Swiss 10-Million Referendum Efficiency View":
        raise ValueError("dashboard h1 is missing or unexpected")
    if "Source Boundary Audit" not in parser.h2_sections:
        raise ValueError("dashboard missing Source Boundary Audit section")
    if parser.table_count < 4:
        raise ValueError("dashboard must contain at least four tables")
    if parser.image_count < 1:
        raise ValueError("dashboard must contain the comparison figure image")
    if not figure_nonblank:
        raise ValueError("dashboard figure appears blank")
    if not required_text_present:
        raise ValueError("dashboard missing required text")

    return DashboardVerificationResult(
        dashboard_path=dashboard_path,
        figure_path=figure_path,
        title=parser.title,
        h1=parser.h1,
        h2_sections=tuple(parser.h2_sections),
        table_count=parser.table_count,
        table_row_count=parser.table_row_count,
        image_count=parser.image_count,
        checked_figure_count=len(checked_figure_paths),
        figure_shape=figure_shape,
        extra_figure_paths=tuple(extra_figure_paths),
        figure_nonblank=figure_nonblank,
        required_text_present=required_text_present,
    )


def read_polymarket_snapshots(path: Path = SNAPSHOT_OUTPUT) -> pd.DataFrame:
    """Read and validate Swiss referendum Polymarket snapshots."""

    if not path.exists():
        raise FileNotFoundError(f"Polymarket snapshots not found: {path}")
    frame = pd.read_csv(path)
    required = (
        "collected_at_utc",
        "yes_probability",
        "no_probability",
        "source_url",
    )
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Polymarket snapshots missing required columns: {missing}")
    forbidden = [column for column in frame.columns if "wallet" in column.lower()]
    if forbidden:
        raise ValueError(f"Polymarket snapshots must not contain wallet columns: {forbidden}")
    normalized = frame.copy()
    normalized["collected_at_utc"] = normalized["collected_at_utc"].astype(str)
    for column in ("yes_probability", "no_probability"):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
        if not normalized[column].between(0.0, 1.0).all():
            raise ValueError(f"{column} values must be between 0 and 1")
    pd.to_datetime(normalized["collected_at_utc"], errors="raise", utc=True)
    return normalized.sort_values("collected_at_utc").reset_index(drop=True)


def read_optional_polymarket_price_history(path: Path | None) -> pd.DataFrame:
    """Read optional historical Polymarket price points."""

    columns = ("observed_at_utc", "yes_probability", "source_url")
    if path is None or not path.exists():
        return pd.DataFrame(columns=columns)
    frame = pd.read_csv(path)
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Polymarket price history missing required columns: {missing}")
    forbidden = [column for column in frame.columns if "wallet" in column.lower()]
    if forbidden:
        raise ValueError(f"Polymarket price history must not contain wallet columns: {forbidden}")
    normalized = frame.copy()
    normalized["observed_at_utc"] = normalized["observed_at_utc"].astype(str)
    normalized["yes_probability"] = pd.to_numeric(
        normalized["yes_probability"],
        errors="raise",
    )
    if not normalized["yes_probability"].between(0.0, 1.0).all():
        raise ValueError("history yes_probability values must be between 0 and 1")
    pd.to_datetime(normalized["observed_at_utc"], errors="raise", utc=True)
    return normalized.sort_values("observed_at_utc").reset_index(drop=True)


def combine_polymarket_observations(
    *,
    snapshots: pd.DataFrame,
    history: pd.DataFrame,
) -> pd.DataFrame:
    """Return one timestamp/probability stream for impact checks."""

    snapshot_points = snapshots[["collected_at_utc", "yes_probability", "source_url"]].rename(
        columns={"collected_at_utc": "observed_at_utc"}
    )
    if history.empty:
        combined = snapshot_points
    else:
        history_points = history[["observed_at_utc", "yes_probability", "source_url"]]
        combined = pd.concat([history_points, snapshot_points], ignore_index=True)
    combined["observed_at_utc"] = combined["observed_at_utc"].astype(str)
    combined["yes_probability"] = pd.to_numeric(combined["yes_probability"], errors="raise")
    return (
        combined.drop_duplicates(["observed_at_utc"], keep="last")
        .sort_values("observed_at_utc")
        .reset_index(drop=True)
    )


def build_comparison_rows(
    *,
    snapshots: pd.DataFrame,
    polls: pd.DataFrame,
    divergence_threshold: float = 0.05,
) -> pd.DataFrame:
    """Attach the latest available poll to each Polymarket snapshot."""

    poll_records = _poll_records_with_timestamps(polls)
    rows: list[dict[str, Any]] = []
    for snapshot in snapshots.to_dict(orient="records"):
        snapshot_ts = pd.Timestamp(str(snapshot["collected_at_utc"])).tz_convert("UTC")
        prior_polls = [poll for poll in poll_records if poll["published_ts"] <= snapshot_ts]
        base = {
            "comparison_id": f"cmp_{snapshot_ts.strftime('%Y%m%dT%H%M%SZ')}",
            "collected_at_utc": _format_timestamp(snapshot_ts),
            "polymarket_yes_probability": float(snapshot["yes_probability"]),
            "polymarket_no_probability": float(snapshot["no_probability"]),
        }
        if not prior_polls:
            rows.append(
                {
                    **base,
                    "comparison_status": "no_prior_poll",
                    "poll_id": "",
                    "poll_source": "",
                    "poll_published_at_utc": "",
                    "poll_age_hours": float("nan"),
                    "poll_yes_share": float("nan"),
                    "poll_no_share": float("nan"),
                    "poll_undecided_share": float("nan"),
                    "poll_yes_decided_share": float("nan"),
                    "raw_yes_gap": float("nan"),
                    "decided_yes_gap": float("nan"),
                    "divergence_label": "unclassified",
                    "poll_proxy_valuation_label": "unclassified",
                    "valuation_scope": "no_prior_poll",
                }
            )
            continue
        poll = prior_polls[-1]
        yes_share = float(poll["yes_share"])
        no_share = float(poll["no_share"])
        decided_yes = yes_share / (yes_share + no_share)
        raw_gap = float(snapshot["yes_probability"]) - yes_share
        decided_gap = float(snapshot["yes_probability"]) - decided_yes
        rows.append(
            {
                **base,
                "comparison_status": "matched_latest_prior_poll",
                "poll_id": poll["poll_id"],
                "poll_source": poll["source_name"],
                "poll_published_at_utc": _format_timestamp(poll["published_ts"]),
                "poll_age_hours": round(
                    (snapshot_ts - poll["published_ts"]).total_seconds() / 3600.0,
                    3,
                ),
                "poll_yes_share": yes_share,
                "poll_no_share": no_share,
                "poll_undecided_share": float(poll["undecided_share"]),
                "poll_yes_decided_share": decided_yes,
                "raw_yes_gap": raw_gap,
                "decided_yes_gap": decided_gap,
                "divergence_label": _divergence_label(raw_gap, divergence_threshold),
                "poll_proxy_valuation_label": _poll_proxy_valuation_label(
                    raw_gap,
                    divergence_threshold,
                ),
                "valuation_scope": (
                    "descriptive_poll_proxy_not_true_mispricing_or_trade_signal"
                ),
            }
        )
    return pd.DataFrame(rows, columns=COMPARISON_COLUMNS)


def build_latest_source_comparison_rows(
    *,
    snapshots: pd.DataFrame,
    polls: pd.DataFrame,
    divergence_threshold: float = 0.05,
) -> pd.DataFrame:
    """Compare the latest local Polymarket snapshot with each poll source."""

    if snapshots.empty:
        return pd.DataFrame(columns=LATEST_SOURCE_COMPARISON_COLUMNS)
    latest_snapshot = snapshots.copy()
    latest_snapshot["_snapshot_ts"] = pd.to_datetime(
        latest_snapshot["collected_at_utc"],
        errors="raise",
        utc=True,
    )
    snapshot = latest_snapshot.sort_values("_snapshot_ts").iloc[-1]
    snapshot_ts = pd.Timestamp(snapshot["_snapshot_ts"]).tz_convert("UTC")
    snapshot_yes = float(snapshot["yes_probability"])
    rows: list[dict[str, Any]] = []
    source_names = sorted(str(item) for item in polls["source_name"].unique())
    for source_name in source_names:
        source_polls = [
            poll
            for poll in _poll_records_with_timestamps(polls[polls["source_name"] == source_name])
            if poll["published_ts"] <= snapshot_ts
        ]
        if not source_polls:
            continue
        poll = source_polls[-1]
        yes_share = float(poll["yes_share"])
        no_share = float(poll["no_share"])
        decided_yes = yes_share / (yes_share + no_share)
        raw_gap = snapshot_yes - yes_share
        decided_gap = snapshot_yes - decided_yes
        rows.append(
            {
                "source_name": source_name,
                "poll_id": poll["poll_id"],
                "poll_published_at_utc": _format_timestamp(poll["published_ts"]),
                "poll_age_hours": round(
                    (snapshot_ts - poll["published_ts"]).total_seconds() / 3600.0,
                    3,
                ),
                "polymarket_snapshot_at_utc": _format_timestamp(snapshot_ts),
                "polymarket_yes_probability": snapshot_yes,
                "poll_yes_share": yes_share,
                "poll_yes_decided_share": decided_yes,
                "raw_yes_gap": raw_gap,
                "decided_yes_gap": decided_gap,
                "divergence_label": _divergence_label(raw_gap, divergence_threshold),
                "poll_proxy_valuation_label": _poll_proxy_valuation_label(
                    raw_gap,
                    divergence_threshold,
                ),
                "valuation_scope": (
                    "descriptive_latest_source_poll_proxy_not_true_mispricing_or_trade_signal"
                ),
            }
        )
    return pd.DataFrame(rows, columns=LATEST_SOURCE_COMPARISON_COLUMNS)


def build_poll_impact_rows(
    *,
    snapshots: pd.DataFrame,
    polls: pd.DataFrame,
) -> pd.DataFrame:
    """Describe observable Polymarket moves around each poll release."""

    snapshot_records = _snapshot_records_with_timestamps(snapshots)
    rows: list[dict[str, Any]] = []
    for poll in _poll_records_with_timestamps(polls):
        published_ts = poll["published_ts"]
        pre = [snap for snap in snapshot_records if snap["snapshot_ts"] < published_ts]
        post = [snap for snap in snapshot_records if snap["snapshot_ts"] >= published_ts]
        if not pre and not post:
            status = "no_snapshots"
            pre_snapshot = None
            post_snapshot = None
        elif not pre:
            status = "no_pre_snapshot"
            pre_snapshot = None
            post_snapshot = post[0] if post else None
        elif not post:
            status = "no_post_snapshot"
            pre_snapshot = pre[-1]
            post_snapshot = None
        else:
            status = "observed_pre_post"
            pre_snapshot = pre[-1]
            post_snapshot = post[0]
        pre_probability = (
            float("nan")
            if pre_snapshot is None
            else float(pre_snapshot["yes_probability"])
        )
        post_probability = (
            float("nan")
            if post_snapshot is None
            else float(post_snapshot["yes_probability"])
        )
        window_changes = {
            f"yes_probability_change_{hours}h": _post_window_change(
                snapshot_records=snapshot_records,
                published_ts=published_ts,
                pre_probability=pre_probability,
                hours=hours,
            )
            for hours in (1, 6, 24, 48)
        }
        rows.append(
            {
                "poll_id": poll["poll_id"],
                "poll_source": poll["source_name"],
                "poll_published_at_utc": _format_timestamp(published_ts),
                "impact_status": status,
                "pre_snapshot_at_utc": (
                    "" if pre_snapshot is None else _format_timestamp(pre_snapshot["snapshot_ts"])
                ),
                "post_snapshot_at_utc": (
                    "" if post_snapshot is None else _format_timestamp(post_snapshot["snapshot_ts"])
                ),
                "hours_to_first_post_snapshot": (
                    float("nan")
                    if post_snapshot is None
                    else round(
                        (post_snapshot["snapshot_ts"] - published_ts).total_seconds() / 3600.0,
                        3,
                    )
                ),
                "pre_yes_probability": pre_probability,
                "post_yes_probability": post_probability,
                "yes_probability_change": (
                    float("nan")
                    if pre_snapshot is None or post_snapshot is None
                    else post_probability - pre_probability
                ),
                **window_changes,
            }
        )
    return pd.DataFrame(rows, columns=IMPACT_COLUMNS)


def build_poll_reaction_window_rows(impacts: pd.DataFrame) -> pd.DataFrame:
    """Return one reaction-window row per poll and post-publication window."""

    rows: list[dict[str, Any]] = []
    for impact in impacts.to_dict(orient="records"):
        published_at = str(impact["poll_published_at_utc"])
        published_ts = pd.Timestamp(published_at).tz_convert("UTC")
        for hours in (1, 6, 24, 48):
            change = _optional_float(impact.get(f"yes_probability_change_{hours}h"))
            rows.append(
                {
                    "poll_id": impact["poll_id"],
                    "poll_source": impact["poll_source"],
                    "poll_published_at_utc": published_at,
                    "window_hours": hours,
                    "window_end_at_utc": _format_timestamp(
                        published_ts + pd.Timedelta(hours=hours)
                    ),
                    "reaction_status": (
                        "observed_window_change"
                        if change is not None
                        else "missing_window_observation"
                    ),
                    "impact_status": impact["impact_status"],
                    "pre_snapshot_at_utc": impact["pre_snapshot_at_utc"],
                    "pre_yes_probability": impact["pre_yes_probability"],
                    "yes_probability_change": (
                        float("nan") if change is None else change
                    ),
                    "interpretation_scope": (
                        "descriptive_pre_post_window_no_causality_or_trade_signal"
                    ),
                }
            )
    return pd.DataFrame(rows, columns=POLL_REACTION_WINDOW_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--poll-input", type=Path, default=POLL_INPUT)
    parser.add_argument("--polymarket-snapshots", type=Path, default=SNAPSHOT_OUTPUT)
    parser.add_argument(
        "--polymarket-history",
        type=Path,
        default=POLYMARKET_HISTORY_INPUT,
    )
    parser.add_argument("--comparison-output", type=Path, default=COMPARISON_OUTPUT)
    parser.add_argument(
        "--latest-source-comparison-output",
        type=Path,
        default=LATEST_SOURCE_COMPARISON_OUTPUT,
    )
    parser.add_argument("--poll-impact-output", type=Path, default=POLL_IMPACT_OUTPUT)
    parser.add_argument(
        "--poll-reaction-windows-output",
        type=Path,
        default=POLL_REACTION_WINDOWS_OUTPUT,
    )
    parser.add_argument("--source-audit-output", type=Path, default=SOURCE_AUDIT_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--reaction-figure-output", type=Path, default=REACTION_FIGURE_OUTPUT)
    parser.add_argument("--dashboard-output", type=Path, default=DASHBOARD_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    parser.add_argument("--divergence-threshold", type=float, default=0.05)
    args = parser.parse_args(argv)

    try:
        result = generate_swiss_referendum_efficiency_outputs(
            poll_input_path=args.poll_input,
            polymarket_snapshots_path=args.polymarket_snapshots,
            polymarket_history_path=args.polymarket_history,
            comparison_path=args.comparison_output,
            latest_source_comparison_path=args.latest_source_comparison_output,
            poll_impact_path=args.poll_impact_output,
            poll_reaction_windows_path=args.poll_reaction_windows_output,
            source_audit_path=args.source_audit_output,
            figure_path=args.figure_output,
            reaction_figure_path=args.reaction_figure_output,
            dashboard_path=args.dashboard_output,
            summary_path=args.summary_output,
            metadata_path=args.metadata_output,
            divergence_threshold=args.divergence_threshold,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _write_figure(
    *,
    snapshots: pd.DataFrame,
    history: pd.DataFrame,
    polls: pd.DataFrame,
    comparisons: pd.DataFrame,
    figure_path: Path,
) -> None:
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5.5), constrained_layout=True)
    price_line = combine_polymarket_observations(snapshots=snapshots, history=history)
    snapshot_dates = pd.to_datetime(price_line["observed_at_utc"], utc=True)
    if history.empty:
        ax.plot(
            snapshot_dates,
            price_line["yes_probability"].astype(float),
            marker="o",
            color="#1f77b4",
            label="Polymarket Yes probability",
        )
    else:
        ax.scatter(
            snapshot_dates,
            price_line["yes_probability"].astype(float),
            marker="o",
            s=24,
            color="#1f77b4",
            alpha=0.85,
            label="Polymarket Yes probability",
        )
        local_snapshot_dates = pd.to_datetime(snapshots["collected_at_utc"], utc=True)
        ax.scatter(
            local_snapshot_dates,
            snapshots["yes_probability"].astype(float),
            marker="D",
            s=46,
            color="#174f78",
            label="Local refresh snapshots",
        )
    poll_dates = pd.to_datetime(polls["published_at_utc"], utc=True)
    ax.scatter(
        poll_dates,
        polls["yes_share"].astype(float),
        marker="s",
        color="#2ca02c",
        label="Poll Yes share",
    )
    decided = polls["yes_share"].astype(float) / (
        polls["yes_share"].astype(float) + polls["no_share"].astype(float)
    )
    ax.scatter(
        poll_dates,
        decided,
        marker="^",
        color="#ff7f0e",
        label="Poll Yes share among decided",
    )
    if not comparisons.empty and "poll_published_at_utc" in comparisons.columns:
        for _, row in comparisons.tail(5).iterrows():
            if str(row.get("poll_published_at_utc", "")).strip():
                ax.vlines(
                    pd.Timestamp(str(row["poll_published_at_utc"])),
                    ymin=0,
                    ymax=1,
                    colors="#888888",
                    linestyles="dotted",
                    linewidth=0.8,
                    alpha=0.5,
                )
    ax.set_ylim(0, 1)
    ax.set_ylabel("Approval probability/share")
    ax.set_title("Swiss 10-million initiative: Polymarket vs polls")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="best")
    fig.autofmt_xdate()
    fig.savefig(figure_path, dpi=160)
    plt.close(fig)


def _write_reaction_window_figure(
    *,
    reaction_windows: pd.DataFrame,
    figure_path: Path,
) -> None:
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5.2), constrained_layout=True)
    if reaction_windows.empty:
        ax.text(0.5, 0.5, "No reaction-window rows", ha="center", va="center")
        ax.set_axis_off()
    else:
        frame = reaction_windows.copy()
        frame["window_hours"] = pd.to_numeric(frame["window_hours"], errors="raise")
        frame["yes_probability_change"] = pd.to_numeric(
            frame["yes_probability_change"],
            errors="coerce",
        )
        pivot = frame.pivot_table(
            index="poll_id",
            columns="window_hours",
            values="yes_probability_change",
            aggfunc="first",
        ).sort_index()
        pivot = pivot.reindex(columns=[1, 6, 24, 48])
        x_positions = range(len(pivot.index))
        width = 0.18
        offsets = (-1.5 * width, -0.5 * width, 0.5 * width, 1.5 * width)
        colors = {
            1: "#4c78a8",
            6: "#f58518",
            24: "#54a24b",
            48: "#b279a2",
        }
        for offset, window in zip(offsets, [1, 6, 24, 48], strict=True):
            values = pivot[window].astype(float) * 100.0
            ax.bar(
                [position + offset for position in x_positions],
                values,
                width=width,
                label=f"{window}h",
                color=colors[window],
            )
        ax.axhline(0, color="#333333", linewidth=0.8)
        ax.set_xticks(list(x_positions))
        ax.set_xticklabels(pivot.index, rotation=20, ha="right")
        ax.set_ylabel("Yes probability change, percentage points")
        ax.set_title("Polymarket movement after curated poll publications")
        ax.grid(axis="y", alpha=0.25)
        ax.legend(title="Window")
    fig.savefig(figure_path, dpi=160)
    plt.close(fig)


class _DashboardHtmlParser(HTMLParser):
    """Small structural parser for the generated dashboard HTML."""

    def __init__(self) -> None:
        super().__init__()
        self._stack: list[str] = []
        self._title_parts: list[str] = []
        self._h1_parts: list[str] = []
        self.h2_sections: list[str] = []
        self.table_count = 0
        self.table_row_count = 0
        self.image_count = 0

    @property
    def title(self) -> str:
        return " ".join(self._title_parts)

    @property
    def h1(self) -> str:
        return " ".join(self._h1_parts)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        self._stack.append(tag)
        if tag == "table":
            self.table_count += 1
        elif tag == "tr":
            self.table_row_count += 1
        elif tag == "img":
            self.image_count += 1

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index] == tag:
                del self._stack[index:]
                return

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text or not self._stack:
            return
        current = self._stack[-1]
        if current == "title":
            self._title_parts.append(text)
        elif current == "h1":
            self._h1_parts.append(text)
        elif current == "h2":
            self.h2_sections.append(text)


def _render_dashboard(
    *,
    polls: pd.DataFrame,
    snapshots: pd.DataFrame,
    comparisons: pd.DataFrame,
    latest_source_comparisons: pd.DataFrame,
    impacts: pd.DataFrame,
    reaction_windows: pd.DataFrame,
    source_audit: pd.DataFrame,
    figure_path: Path,
    reaction_figure_path: Path,
    source_paths: dict[str, Path],
) -> str:
    latest = _latest_comparison(comparisons)
    latest_poll_text = (
        "No prior poll matched"
        if latest.get("comparison_status") != "matched_latest_prior_poll"
        else (
            f"{_pct(float(latest['poll_yes_share']))} raw Yes, "
            f"{_pct(float(latest['poll_yes_decided_share']))} decided Yes"
        )
    )
    latest_snapshot_at = str(latest.get("collected_at_utc", "")).strip()
    latest_poll_id = str(latest.get("poll_id", "")).strip()
    latest_poll_published_at = str(latest.get("poll_published_at_utc", "")).strip()
    timing_summary_items = "\n".join(
        f"<li>{escape(item)}</li>" for item in _poll_release_timing_summary(impacts)
    )
    impact_rows = _table_rows(
        impacts,
        (
            "poll_id",
            "poll_source",
            "poll_published_at_utc",
            "impact_status",
            "hours_to_first_post_snapshot",
            "yes_probability_change",
            "yes_probability_change_1h",
            "yes_probability_change_6h",
            "yes_probability_change_24h",
            "yes_probability_change_48h",
        ),
        max_rows=20,
    )
    comparison_rows = _table_rows(
        comparisons.tail(20),
        (
            "collected_at_utc",
            "polymarket_yes_probability",
            "poll_id",
            "poll_yes_share",
            "poll_yes_decided_share",
            "raw_yes_gap",
            "decided_yes_gap",
            "divergence_label",
            "poll_proxy_valuation_label",
        ),
        max_rows=20,
    )
    latest_source_rows = _table_rows(
        latest_source_comparisons,
        (
            "source_name",
            "poll_id",
            "poll_published_at_utc",
            "polymarket_yes_probability",
            "poll_yes_share",
            "poll_yes_decided_share",
            "raw_yes_gap",
            "decided_yes_gap",
            "poll_proxy_valuation_label",
        ),
        max_rows=20,
    )
    poll_rows = _table_rows(
        polls,
        (
            "poll_id",
            "source_name",
            "fieldwork_start",
            "fieldwork_end",
            "published_at_utc",
            "yes_share",
            "no_share",
            "undecided_share",
        ),
        max_rows=20,
    )
    reaction_window_rows = _table_rows(
        reaction_windows,
        (
            "poll_id",
            "window_hours",
            "window_end_at_utc",
            "reaction_status",
            "yes_probability_change",
            "interpretation_scope",
        ),
        max_rows=40,
    )
    source_audit_rows = _table_rows(
        source_audit,
        (
            "source_id",
            "source_name",
            "source_role",
            "has_voting_intention_values",
            "included_in_poll_catalog",
            "notes",
        ),
        max_rows=30,
    )
    source_items = "\n".join(
        f"<li><code>{escape(name)}</code>: {escape(str(path))}</li>"
        for name, path in source_paths.items()
    )
    figure_html = (
        f'<img src="{escape(figure_path.name)}" alt="Swiss referendum comparison figure">'
        if figure_path.exists()
        else "<p>Figure not found.</p>"
    )
    reaction_figure_html = (
        f'<img src="{escape(reaction_figure_path.name)}" alt="Swiss referendum reaction-window figure">'
        if reaction_figure_path.exists()
        else "<p>Reaction-window figure not found.</p>"
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Swiss 10-Million Referendum Efficiency View</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 28px; color: #17202a; }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, minmax(140px, 1fr)); gap: 12px; }}
    .metric {{ border: 1px solid #d7dde5; border-radius: 6px; padding: 12px; background: #f8fafc; }}
    .metric strong {{ display: block; font-size: 22px; margin-top: 4px; }}
    .metric.compact strong {{ font-size: 13px; line-height: 1.35; overflow-wrap: anywhere; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; font-size: 13px; }}
    th, td {{ border: 1px solid #d7dde5; padding: 7px; text-align: left; vertical-align: top; }}
    th {{ background: #eef2f7; }}
    img {{ max-width: 100%; border: 1px solid #d7dde5; border-radius: 6px; }}
    code {{ background: #f1f5f9; padding: 2px 4px; border-radius: 4px; }}
    .note {{ background: #fff7e6; border: 1px solid #f0d08a; padding: 12px; border-radius: 6px; }}
  </style>
</head>
<body>
  <h1>Swiss 10-Million Referendum Efficiency View</h1>
  <p class="note">Read-only deterministic comparison. Poll shares are survey shares, not model-implied win probabilities. Divergence labels are descriptive and make no causal, trading, or profitability claim.</p>
  <section class="metrics">
    <div class="metric">Snapshots<strong>{len(snapshots)}</strong></div>
    <div class="metric">Polls<strong>{len(polls)}</strong></div>
    <div class="metric">Latest Polymarket Yes<strong>{_pct(float(latest.get("polymarket_yes_probability", float("nan"))))}</strong></div>
    <div class="metric">Latest poll comparison<strong>{escape(latest_poll_text)}</strong></div>
    <div class="metric">Raw Yes gap<strong>{_pct_points(latest.get("raw_yes_gap"))}</strong></div>
    <div class="metric">Decided Yes gap<strong>{_pct_points(latest.get("decided_yes_gap"))}</strong></div>
    <div class="metric">Label<strong>{escape(str(latest.get("divergence_label", "")))}</strong></div>
    <div class="metric">Poll proxy relation<strong>{escape(str(latest.get("poll_proxy_valuation_label", "")))}</strong></div>
    <div class="metric compact">Latest local snapshot<strong>{escape(latest_snapshot_at)}</strong></div>
    <div class="metric compact">Latest matched poll<strong>{escape(latest_poll_id)}</strong></div>
    <div class="metric compact">Matched poll published<strong>{escape(latest_poll_published_at)}</strong></div>
    <div class="metric compact">Refresh mode<strong>manual bounded refresh</strong></div>
  </section>
  <h2>Figure</h2>
  {figure_html}
  <h2>Poll Reaction Window Figure</h2>
  {reaction_figure_html}
  <h2>Comparison Rows</h2>
  <table>
    <thead><tr><th>Snapshot</th><th>Polymarket Yes</th><th>Poll</th><th>Poll Yes</th><th>Poll decided Yes</th><th>Raw gap</th><th>Decided gap</th><th>Label</th><th>Poll proxy relation</th></tr></thead>
    <tbody>{comparison_rows}</tbody>
  </table>
  <h2>Latest Poll-Source Comparison</h2>
  <p class="note">This table compares the latest local Polymarket snapshot with the newest prior poll from each curated poll source. It is a cross-source poll-proxy view, not a model average or mispricing test.</p>
  <table>
    <thead><tr><th>Source</th><th>Poll</th><th>Published</th><th>Polymarket Yes</th><th>Poll Yes</th><th>Poll decided Yes</th><th>Raw gap</th><th>Decided gap</th><th>Poll proxy relation</th></tr></thead>
    <tbody>{latest_source_rows}</tbody>
  </table>
  <h2>Poll Release Impact Checks</h2>
  <p class="note">Impact rows require at least one local Polymarket observation before and after the poll publication time. Observations can come from bounded snapshots or bounded public CLOB price-history windows.</p>
  <h3>Poll Release Timing Summary</h3>
  <ul>{timing_summary_items}</ul>
  <table>
    <thead><tr><th>Poll</th><th>Source</th><th>Published</th><th>Status</th><th>Hours to first post observation</th><th>First change</th><th>1h change</th><th>6h change</th><th>24h change</th><th>48h change</th></tr></thead>
    <tbody>{impact_rows}</tbody>
  </table>
  <h2>Curated Poll Inputs</h2>
  <table>
    <thead><tr><th>Poll</th><th>Source</th><th>Fieldwork start</th><th>Fieldwork end</th><th>Published</th><th>Yes</th><th>No</th><th>Undecided</th></tr></thead>
    <tbody>{poll_rows}</tbody>
  </table>
  <h2>Poll Reaction Window Rows</h2>
  <p class="note">Reaction-window rows are descriptive changes from the closest pre-publication observation to the last local observation inside each post-publication window. They are not causal claims.</p>
  <table>
    <thead><tr><th>Poll</th><th>Window hours</th><th>Window end</th><th>Status</th><th>Yes probability change</th><th>Scope</th></tr></thead>
    <tbody>{reaction_window_rows}</tbody>
  </table>
  <h2>Limitations</h2>
  <p class="note">BFS/admin.ch is used as official referendum and population-context evidence. The curated poll values currently come from SRG/gfs.bern, Tamedia/LeeWas, and YouGov Schweiz, because BFS does not appear to publish voting-intention poll shares for this referendum.</p>
  <ul>
    <li>No statistical event-window or causal test is run here.</li>
    <li>Poll publication impact uses bounded local Polymarket observations before and after each release.</li>
    <li>Poll proxy relation labels describe over/under the latest poll share only; they are not true valuation, mispricing, or trading labels.</li>
    <li>The decided-voter value is only yes_share / (yes_share + no_share).</li>
  </ul>
  <h2>Source Boundary Audit</h2>
  <table>
    <thead><tr><th>Source ID</th><th>Source</th><th>Role</th><th>Voting-intention values</th><th>In poll catalog</th><th>Notes</th></tr></thead>
    <tbody>{source_audit_rows}</tbody>
  </table>
  <h2>Source Artifacts</h2>
  <ul>{source_items}</ul>
</body>
</html>
"""


def _render_latest_summary(
    *,
    polls: pd.DataFrame,
    snapshots: pd.DataFrame,
    history: pd.DataFrame,
    comparisons: pd.DataFrame,
    latest_source_comparisons: pd.DataFrame,
    impacts: pd.DataFrame,
    reaction_windows: pd.DataFrame,
    source_audit: pd.DataFrame,
    figure_path: Path,
    reaction_figure_path: Path,
    dashboard_path: Path,
) -> str:
    latest = _latest_comparison(comparisons)
    impact_counts = impacts["impact_status"].value_counts().sort_index()
    impact_summary = ", ".join(f"{key}: {int(value)}" for key, value in impact_counts.items())
    reaction_window_summary = _reaction_window_summary(impacts)
    poll_source_names = ", ".join(sorted(str(item) for item in polls["source_name"].unique()))
    latest_poll = str(latest.get("poll_id", ""))
    latest_poll_source = str(latest.get("poll_source", ""))
    latest_snapshot_at = str(latest.get("collected_at_utc", ""))
    timing_summary = _poll_release_timing_summary(impacts)
    latest_source_summary = _latest_source_comparison_summary(latest_source_comparisons)
    lines = [
        "# Swiss 10-Million Referendum Latest Summary",
        "",
        "## Generated Or Inspected",
        "",
        f"- Comparison rows: {len(comparisons)}.",
        f"- Polymarket snapshot rows: {len(snapshots)}.",
        f"- Bounded price-history rows: {len(history)}.",
        f"- Curated poll rows: {len(polls)} from {poll_source_names}.",
        f"- Poll-impact rows: {len(impacts)} ({impact_summary}).",
        f"- Poll reaction-window rows: {len(reaction_windows)}.",
        f"- Poll reaction windows: {reaction_window_summary}.",
        f"- Latest poll-source comparison rows: {len(latest_source_comparisons)}.",
        f"- Source-audit rows: {len(source_audit)}.",
        "",
        "## Poll Release Timing Summary",
        "",
        *[f"- {item}" for item in timing_summary],
        "",
        "## Latest Poll-Source Comparison",
        "",
        *[f"- {item}" for item in latest_source_summary],
        "",
        "## Key Numerical Result",
        "",
        f"- Latest snapshot: {latest_snapshot_at}.",
        f"- Latest matched poll: {latest_poll} ({latest_poll_source}).",
        f"- Polymarket Yes probability: {_pct(float(latest.get('polymarket_yes_probability', float('nan'))))}.",
        f"- Latest poll Yes share: {_pct(float(latest.get('poll_yes_share', float('nan'))))}.",
        f"- Latest poll decided Yes share: {_pct(float(latest.get('poll_yes_decided_share', float('nan'))))}.",
        f"- Raw Yes gap: {_pct_points(latest.get('raw_yes_gap'))}.",
        f"- Decided Yes gap: {_pct_points(latest.get('decided_yes_gap'))}.",
        f"- Poll-proxy relation: {latest.get('poll_proxy_valuation_label', '')}.",
        "",
        "## Bounded Interpretation",
        "",
        (
            "- The latest local Polymarket Yes probability is below the latest "
            "curated poll Yes share under the deterministic poll-proxy label. "
            "This is a descriptive comparison only."
        ),
        "",
        "## Main Limitation",
        "",
        (
            "- Poll shares are survey shares, not model-implied win probabilities. "
            "The decided-voter value is only yes_share / (yes_share + no_share). "
            "Poll-impact rows describe first observable pre/post Polymarket points "
            "and do not identify causality, market efficiency, tradeability, or "
            "true mispricing."
        ),
        "",
        "## Figure",
        "",
        f"![Swiss referendum comparison figure]({figure_path.name})",
        "",
        "## Reaction Window Figure",
        "",
        f"![Swiss referendum reaction-window figure]({reaction_figure_path.name})",
        "",
        "## Source Boundary",
        "",
        (
            "- BFS/admin.ch rows are context sources only. Current voting-intention "
            "poll inputs are SRG/gfs.bern, Tamedia/LeeWas, and YouGov Schweiz "
            "rows in the curated poll catalog."
        ),
        "",
        "## Local Artifacts",
        "",
        f"- Dashboard: `{dashboard_path}`.",
        f"- Figure: `{figure_path}`.",
    ]
    return "\n".join(lines) + "\n"


def _build_metadata(
    *,
    poll_input_path: Path,
    polymarket_snapshots_path: Path,
    polymarket_history_path: Path | None,
    comparison_path: Path,
    latest_source_comparison_path: Path,
    poll_impact_path: Path,
    poll_reaction_windows_path: Path,
    source_audit_path: Path,
    figure_path: Path,
    reaction_figure_path: Path,
    dashboard_path: Path,
    summary_path: Path,
    polls: pd.DataFrame,
    snapshots: pd.DataFrame,
    history: pd.DataFrame,
    comparisons: pd.DataFrame,
    latest_source_comparisons: pd.DataFrame,
    impacts: pd.DataFrame,
    reaction_windows: pd.DataFrame,
    source_audit: pd.DataFrame,
    dashboard_verification: DashboardVerificationResult,
    divergence_threshold: float,
) -> dict[str, Any]:
    latest = _latest_comparison(comparisons)
    impact_counts = impacts["impact_status"].value_counts().sort_index()
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "swiss_referendum_10mio_efficiency_comparison",
            "divergence_threshold": divergence_threshold,
            "poll_probability_transform": "none",
            "decided_share_formula": "yes_share / (yes_share + no_share)",
            "latest_prior_poll_matching": True,
            "poll_impact_requires_pre_and_post_snapshot": True,
            "uses_polymarket_price_history_for_impacts": not history.empty,
            "read_only": True,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
        },
        "outputs": {
            "poll_count": int(len(polls)),
            "snapshot_count": int(len(snapshots)),
            "history_row_count": int(len(history)),
            "comparison_row_count": int(len(comparisons)),
            "latest_source_comparison_row_count": int(len(latest_source_comparisons)),
            "poll_impact_row_count": int(len(impacts)),
            "poll_reaction_window_row_count": int(len(reaction_windows)),
            "source_audit_row_count": int(len(source_audit)),
            "impact_status_counts": {str(k): int(v) for k, v in impact_counts.items()},
            "latest_raw_yes_gap": _optional_float(latest.get("raw_yes_gap")),
            "latest_decided_yes_gap": _optional_float(latest.get("decided_yes_gap")),
            "latest_divergence_label": str(latest.get("divergence_label", "")),
            "latest_poll_proxy_valuation_label": str(
                latest.get("poll_proxy_valuation_label", "")
            ),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "dashboard_verification": dashboard_verification.to_dict(),
        "source_paths": {
            "poll_input": str(poll_input_path),
            "polymarket_snapshots": str(polymarket_snapshots_path),
            "polymarket_history": (
                "" if polymarket_history_path is None else str(polymarket_history_path)
            ),
            "comparison": str(comparison_path),
            "latest_source_comparison": str(latest_source_comparison_path),
            "poll_impacts": str(poll_impact_path),
            "poll_reaction_windows": str(poll_reaction_windows_path),
            "source_audit": str(source_audit_path),
            "figure": str(figure_path),
            "reaction_figure": str(reaction_figure_path),
            "dashboard": str(dashboard_path),
            "summary": str(summary_path),
        },
        "limitations": {
            "polls_are_not_win_probability_model": True,
            "decided_share_is_not_a_forecast_model": True,
            "bfs_is_context_not_poll_source": True,
            "source_audit_confirms_bfs_context_only": True,
            "no_causal_claim_from_poll_release_rows": True,
            "no_profitability_or_tradeability_claim": True,
            "requires_more_snapshots_for_release_impact_analysis": bool(
                (impacts["impact_status"] != "observed_pre_post").any()
            ),
        },
    }


def _poll_records_with_timestamps(polls: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in polls.to_dict(orient="records"):
        record = dict(item)
        record["published_ts"] = pd.Timestamp(str(item["published_at_utc"])).tz_convert("UTC")
        records.append(record)
    return sorted(records, key=lambda item: (item["published_ts"], item["poll_id"]))


def _snapshot_records_with_timestamps(snapshots: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in snapshots.to_dict(orient="records"):
        record = dict(item)
        timestamp_value = item.get("observed_at_utc", item.get("collected_at_utc"))
        record["snapshot_ts"] = pd.Timestamp(str(timestamp_value)).tz_convert("UTC")
        records.append(record)
    return sorted(records, key=lambda item: item["snapshot_ts"])


def _post_window_change(
    *,
    snapshot_records: list[dict[str, Any]],
    published_ts: pd.Timestamp,
    pre_probability: float,
    hours: int,
) -> float:
    if pd.isna(pre_probability):
        return float("nan")
    target_ts = published_ts + pd.Timedelta(hours=hours)
    candidates = [
        snap
        for snap in snapshot_records
        if published_ts <= snap["snapshot_ts"] <= target_ts
    ]
    if not candidates:
        return float("nan")
    last_point = candidates[-1]
    return float(last_point["yes_probability"]) - pre_probability


def _reaction_window_summary(impacts: pd.DataFrame) -> str:
    parts: list[str] = []
    for column, label in (
        ("yes_probability_change_1h", "1h"),
        ("yes_probability_change_6h", "6h"),
        ("yes_probability_change_24h", "24h"),
        ("yes_probability_change_48h", "48h"),
    ):
        if column not in impacts.columns:
            continue
        observed = pd.to_numeric(impacts[column], errors="coerce").dropna()
        if observed.empty:
            parts.append(f"{label}: no observed window")
        else:
            parts.append(f"{label}: latest observed {_pct_points(observed.iloc[-1])}")
    return "; ".join(parts) if parts else "not available"


def _poll_release_timing_summary(impacts: pd.DataFrame) -> list[str]:
    if impacts.empty:
        return ["No poll-impact rows available."]
    ordered = impacts.sort_values(["poll_published_at_utc", "poll_id"])
    rows: list[str] = []
    for item in ordered.to_dict(orient="records"):
        window_parts = [
            f"{label} {_pct_points(item.get(column)) or 'not observed'}"
            for column, label in (
                ("yes_probability_change_1h", "1h"),
                ("yes_probability_change_6h", "6h"),
                ("yes_probability_change_24h", "24h"),
                ("yes_probability_change_48h", "48h"),
            )
        ]
        first_change = _pct_points(item.get("yes_probability_change")) or "not observed"
        first_delay = _hours(item.get("hours_to_first_post_snapshot")) or "not observed"
        rows.append(
            f"{item.get('poll_id', '')} ({item.get('poll_source', '')}, "
            f"{item.get('poll_published_at_utc', '')}): first post observation after "
            f"{first_delay}, first change {first_change}; "
            f"windows {', '.join(window_parts)}; "
            f"status {item.get('impact_status', '')}; descriptive no-causality scope."
        )
    return rows


def _latest_source_comparison_summary(comparisons: pd.DataFrame) -> list[str]:
    if comparisons.empty:
        return ["No source-level comparison rows available."]
    rows: list[str] = []
    for item in comparisons.sort_values("source_name").to_dict(orient="records"):
        rows.append(
            f"{item.get('source_name', '')}: {item.get('poll_id', '')} "
            f"published {item.get('poll_published_at_utc', '')}; "
            f"poll Yes {_pct(float(item.get('poll_yes_share', float('nan'))))}, "
            f"decided Yes {_pct(float(item.get('poll_yes_decided_share', float('nan'))))}, "
            f"raw gap {_pct_points(item.get('raw_yes_gap'))}, "
            f"decided gap {_pct_points(item.get('decided_yes_gap'))}; "
            f"{item.get('poll_proxy_valuation_label', '')}."
        )
    return rows


def _latest_comparison(comparisons: pd.DataFrame) -> dict[str, Any]:
    if comparisons.empty:
        return {}
    return comparisons.sort_values("collected_at_utc").iloc[-1].to_dict()


def _divergence_label(gap: float, threshold: float) -> str:
    if pd.isna(gap):
        return "unclassified"
    if gap > threshold:
        return "polymarket_above_poll_yes_share"
    if gap < -threshold:
        return "polymarket_below_poll_yes_share"
    return "near_poll_yes_share"


def _poll_proxy_valuation_label(gap: float, threshold: float) -> str:
    if pd.isna(gap):
        return "unclassified"
    if gap > threshold:
        return "above_poll_proxy"
    if gap < -threshold:
        return "below_poll_proxy"
    return "near_poll_proxy"


def _table_rows(frame: pd.DataFrame, columns: Sequence[str], *, max_rows: int) -> str:
    rows: list[str] = []
    for item in frame.loc[:, list(columns)].head(max_rows).to_dict(orient="records"):
        cells = "".join(f"<td>{escape(_format_cell(item[column]))}</td>" for column in columns)
        rows.append(f"<tr>{cells}</tr>")
    return "\n".join(rows)


def _format_cell(value: object) -> str:
    if isinstance(value, float):
        if pd.isna(value):
            return ""
        if -1 <= value <= 1:
            return f"{value:.3f}"
        return f"{value:.2f}"
    return str(value)


def _pct(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"{value * 100:.1f}%"


def _pct_points(value: object) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return ""
    if pd.isna(numeric):
        return ""
    return f"{numeric * 100:+.1f} pp"


def _hours(value: object) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return ""
    if pd.isna(numeric):
        return ""
    return f"{numeric:.1f} h"


def _optional_float(value: object) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(numeric):
        return None
    return numeric


def _format_timestamp(value: pd.Timestamp | datetime) -> str:
    return pd.Timestamp(value).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    raise SystemExit(main())
