"""Convert monitor alert rows into reference-similarity candidate features."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.analysis.wallet_reference_pattern_features import (
    FEATURE_OUTPUT as REFERENCE_FEATURES_INPUT,
    PATTERN_LABELS,
)
from operations.analysis.wallet_reference_similarity import (
    SCORE_COLUMNS,
    SUMMARY_COLUMNS as SIMILARITY_SUMMARY_COLUMNS,
    build_reference_similarity_scores,
    build_reference_similarity_summary,
)
from operations.collectors.polymarket_rolling_history import ROLLING_ALERT_ROWS_OUTPUT


CANDIDATE_FEATURES_OUTPUT = RESULTS_DIR / "monitor_reference_candidate_features.csv"
CANDIDATE_SUMMARY_OUTPUT = RESULTS_DIR / "monitor_reference_candidate_summary.csv"
CANDIDATE_SIMILARITY_OUTPUT = RESULTS_DIR / "monitor_reference_candidate_similarity_scores.csv"
CANDIDATE_SIMILARITY_SUMMARY_OUTPUT = (
    RESULTS_DIR / "monitor_reference_candidate_similarity_summary.csv"
)
CANDIDATE_DASHBOARD_OUTPUT = RESULTS_DIR / "monitor_reference_candidate_dashboard.html"
CANDIDATE_METADATA_OUTPUT = RESULTS_DIR / "monitor_reference_candidate_metadata.json"

FEATURE_COLUMNS: tuple[str, ...] = (
    "case_id",
    "case_type",
    "pattern_label",
    "feature_status",
    "fact_source",
    "reason",
    "evidence_status",
    "claim_scope",
    "requires_human_review",
)

MONITOR_ALERT_COLUMNS: tuple[str, ...] = (
    "timestamp_utc",
    "market_id",
    "tier",
    "anomaly_family",
    "metric_name",
    "severity",
    "status",
    "event_candidate_id",
    "event_review_status",
    "evidence_refs",
    "limitation",
    "review_status",
    "claim_scope",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "summary_id",
    "source_alert_rows",
    "source_non_none_rows",
    "candidate_count",
    "candidate_feature_rows",
    "triggered_feature_rows",
    "similarity_comparison_rows",
    "max_similarity_score",
    "allowed_interpretation",
    "limitation",
)

EVENT_CONTEXT_STATUSES = {"accepted", "market_mapped"}


@dataclass(frozen=True)
class MonitorReferenceCandidateResult:
    """Summary of generated monitor reference-candidate artifacts."""

    candidate_features_path: Path
    candidate_summary_path: Path
    similarity_scores_path: Path
    similarity_summary_path: Path
    dashboard_path: Path
    metadata_path: Path
    candidate_count: int
    triggered_feature_rows: int
    similarity_comparison_rows: int
    max_similarity_score: float

    def to_dict(self) -> dict[str, float | int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "candidate_features_path": str(self.candidate_features_path),
            "candidate_summary_path": str(self.candidate_summary_path),
            "similarity_scores_path": str(self.similarity_scores_path),
            "similarity_summary_path": str(self.similarity_summary_path),
            "dashboard_path": str(self.dashboard_path),
            "metadata_path": str(self.metadata_path),
            "candidate_count": self.candidate_count,
            "triggered_feature_rows": self.triggered_feature_rows,
            "similarity_comparison_rows": self.similarity_comparison_rows,
            "max_similarity_score": self.max_similarity_score,
        }


def build_monitor_reference_candidate_features(alert_rows: pd.DataFrame) -> pd.DataFrame:
    """Return neutral reference-pattern candidate features from monitor rows."""

    _validate_monitor_alert_rows(alert_rows)
    active = alert_rows[alert_rows["severity"].astype(str) != "none"].copy()
    if active.empty:
        return pd.DataFrame(columns=FEATURE_COLUMNS)

    market_counts = active.groupby("market_id")["timestamp_utc"].nunique().to_dict()
    feature_rows: list[dict[str, object]] = []
    for (timestamp_utc, market_id), group in active.groupby(
        ["timestamp_utc", "market_id"],
        sort=True,
    ):
        candidate_id = _candidate_id(timestamp_utc, market_id)
        feature_rows.extend(
            _features_for_group(
                group,
                candidate_id=candidate_id,
                repeated_market_alerts=int(market_counts.get(market_id, 0)),
            )
        )
    return pd.DataFrame(feature_rows, columns=FEATURE_COLUMNS)


def generate_monitor_reference_candidates(
    *,
    alert_rows_path: Path = ROLLING_ALERT_ROWS_OUTPUT,
    reference_features_path: Path = REFERENCE_FEATURES_INPUT,
    candidate_features_path: Path = CANDIDATE_FEATURES_OUTPUT,
    candidate_summary_path: Path = CANDIDATE_SUMMARY_OUTPUT,
    similarity_scores_path: Path = CANDIDATE_SIMILARITY_OUTPUT,
    similarity_summary_path: Path = CANDIDATE_SIMILARITY_SUMMARY_OUTPUT,
    dashboard_path: Path = CANDIDATE_DASHBOARD_OUTPUT,
    metadata_path: Path = CANDIDATE_METADATA_OUTPUT,
) -> MonitorReferenceCandidateResult:
    """Write candidate features, similarity outputs, dashboard, and metadata."""

    alert_rows = _read_alert_rows(alert_rows_path)
    reference_features = _read_reference_features(reference_features_path)
    candidate_features = build_monitor_reference_candidate_features(alert_rows)
    similarity_scores = _similarity_scores(candidate_features, reference_features)
    similarity_summary = build_reference_similarity_summary(similarity_scores)
    candidate_summary = _candidate_summary(
        alert_rows=alert_rows,
        candidate_features=candidate_features,
        similarity_scores=similarity_scores,
    )

    _write_csv(candidate_features_path, candidate_features)
    _write_csv(candidate_summary_path, candidate_summary)
    _write_csv(similarity_scores_path, similarity_scores)
    _write_csv(similarity_summary_path, similarity_summary)
    _write_dashboard(
        candidate_summary=candidate_summary,
        candidate_features=candidate_features,
        similarity_summary=similarity_summary,
        similarity_scores=similarity_scores,
        dashboard_path=dashboard_path,
    )
    metadata = _metadata(
        alert_rows=alert_rows,
        candidate_features=candidate_features,
        candidate_summary=candidate_summary,
        similarity_scores=similarity_scores,
        alert_rows_path=alert_rows_path,
        reference_features_path=reference_features_path,
        candidate_features_path=candidate_features_path,
        candidate_summary_path=candidate_summary_path,
        similarity_scores_path=similarity_scores_path,
        similarity_summary_path=similarity_summary_path,
        dashboard_path=dashboard_path,
    )
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return MonitorReferenceCandidateResult(
        candidate_features_path=candidate_features_path,
        candidate_summary_path=candidate_summary_path,
        similarity_scores_path=similarity_scores_path,
        similarity_summary_path=similarity_summary_path,
        dashboard_path=dashboard_path,
        metadata_path=metadata_path,
        candidate_count=int(candidate_features["case_id"].nunique())
        if not candidate_features.empty
        else 0,
        triggered_feature_rows=int(
            (candidate_features["feature_status"] == "triggered").sum()
        )
        if not candidate_features.empty
        else 0,
        similarity_comparison_rows=int(len(similarity_scores)),
        max_similarity_score=_safe_similarity_max(similarity_scores),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--alert-rows", type=Path, default=ROLLING_ALERT_ROWS_OUTPUT)
    parser.add_argument("--reference-features", type=Path, default=REFERENCE_FEATURES_INPUT)
    parser.add_argument("--candidate-features-output", type=Path, default=CANDIDATE_FEATURES_OUTPUT)
    parser.add_argument("--candidate-summary-output", type=Path, default=CANDIDATE_SUMMARY_OUTPUT)
    parser.add_argument("--similarity-scores-output", type=Path, default=CANDIDATE_SIMILARITY_OUTPUT)
    parser.add_argument(
        "--similarity-summary-output",
        type=Path,
        default=CANDIDATE_SIMILARITY_SUMMARY_OUTPUT,
    )
    parser.add_argument("--dashboard-output", type=Path, default=CANDIDATE_DASHBOARD_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=CANDIDATE_METADATA_OUTPUT)
    args = parser.parse_args(argv)

    try:
        result = generate_monitor_reference_candidates(
            alert_rows_path=args.alert_rows,
            reference_features_path=args.reference_features,
            candidate_features_path=args.candidate_features_output,
            candidate_summary_path=args.candidate_summary_output,
            similarity_scores_path=args.similarity_scores_output,
            similarity_summary_path=args.similarity_summary_output,
            dashboard_path=args.dashboard_output,
            metadata_path=args.metadata_output,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _features_for_group(
    group: pd.DataFrame,
    *,
    candidate_id: str,
    repeated_market_alerts: int,
) -> list[dict[str, object]]:
    families = set(group["anomaly_family"].astype(str))
    metrics = set(group["metric_name"].astype(str))
    has_event_context = (
        group["event_candidate_id"].fillna("").astype(str).str.strip().ne("").any()
        and group["event_review_status"].astype(str).isin(EVENT_CONTEXT_STATUSES).any()
    )
    feature_status_by_label = {
        "large_trade_flow": (
            "triggered"
            if "wallet_tier_activity" in families
            and "log1p_total_observed_amount_usd" in metrics
            else "unknown"
        ),
        "market_concentration": "triggered" if "concentration" in families else "unknown",
        "event_proximity": "triggered" if has_event_context else "unknown",
        "fresh_wallet_or_short_history": "unknown",
        "cluster_link_reported": "unknown",
        "shared_funding_reported": "unknown",
        "high_reported_win_rate": "unknown",
        "same_theme_repeated_positions": (
            "triggered" if repeated_market_alerts > 1 else "unknown"
        ),
    }
    rows: list[dict[str, object]] = []
    for pattern_label in PATTERN_LABELS:
        status = feature_status_by_label[pattern_label]
        rows.append(
            {
                "case_id": candidate_id,
                "case_type": "monitor_alert_candidate",
                "pattern_label": pattern_label,
                "feature_status": status,
                "fact_source": "computed" if status == "triggered" else "unknown",
                "reason": _reason_for_label(pattern_label, status, group),
                "evidence_status": "pattern_computed" if status == "triggered" else "candidate",
                "claim_scope": "monitor_reference_candidate_only",
                "requires_human_review": True,
            }
        )
    return rows


def _reason_for_label(pattern_label: str, status: str, group: pd.DataFrame) -> str:
    if status != "triggered":
        return "source data unavailable in current monitor alert rows"
    if pattern_label == "large_trade_flow":
        return "monitor wallet-tier amount metric produced a non-none severity row"
    if pattern_label == "market_concentration":
        return "monitor concentration metric produced a non-none severity row"
    if pattern_label == "event_proximity":
        return "monitor alert row has reviewed event context"
    if pattern_label == "same_theme_repeated_positions":
        return "same market has non-none monitor rows at multiple timestamps"
    return "computed from monitor alert rows"


def _similarity_scores(
    candidate_features: pd.DataFrame,
    reference_features: pd.DataFrame,
) -> pd.DataFrame:
    if candidate_features.empty:
        return pd.DataFrame(columns=SCORE_COLUMNS)
    return build_reference_similarity_scores(candidate_features, reference_features)


def _candidate_summary(
    *,
    alert_rows: pd.DataFrame,
    candidate_features: pd.DataFrame,
    similarity_scores: pd.DataFrame,
) -> pd.DataFrame:
    source_non_none = int((alert_rows["severity"].astype(str) != "none").sum())
    candidate_count = (
        int(candidate_features["case_id"].nunique()) if not candidate_features.empty else 0
    )
    triggered_count = (
        int((candidate_features["feature_status"] == "triggered").sum())
        if not candidate_features.empty
        else 0
    )
    max_similarity = _safe_similarity_max(similarity_scores)
    return pd.DataFrame(
        [
            {
                "summary_id": "monitor_reference_candidates_current",
                "source_alert_rows": int(len(alert_rows)),
                "source_non_none_rows": source_non_none,
                "candidate_count": candidate_count,
                "candidate_feature_rows": int(len(candidate_features)),
                "triggered_feature_rows": triggered_count,
                "similarity_comparison_rows": int(len(similarity_scores)),
                "max_similarity_score": max_similarity,
                "allowed_interpretation": _summary_interpretation(candidate_count),
                "limitation": (
                    "Candidate features are derived only from non-none monitor "
                    "severity rows and aggregate monitor fields; no wallet "
                    "addresses are used."
                ),
            }
        ],
        columns=SUMMARY_COLUMNS,
    )


def _summary_interpretation(candidate_count: int) -> str:
    if candidate_count == 0:
        return "No monitor rows became reference-similarity candidates in this run."
    return "Monitor candidates were converted into neutral pattern labels for human review."


def _write_dashboard(
    *,
    candidate_summary: pd.DataFrame,
    candidate_features: pd.DataFrame,
    similarity_summary: pd.DataFrame,
    similarity_scores: pd.DataFrame,
    dashboard_path: Path,
) -> None:
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    summary = candidate_summary.iloc[0].to_dict()
    features_html = (
        "<p>No candidate features generated.</p>"
        if candidate_features.empty
        else _table(
            candidate_features[candidate_features["feature_status"] == "triggered"],
            ("case_id", "pattern_label", "fact_source", "reason", "evidence_status"),
        )
    )
    similarity_html = (
        "<p>No similarity comparisons generated.</p>"
        if similarity_summary.empty
        else _table(
            similarity_summary,
            (
                "candidate_id",
                "best_reference_case_id",
                "best_similarity_score",
                "matched_patterns",
                "match_label",
            ),
        )
    )
    all_scores_html = (
        "<p>No comparison rows.</p>"
        if similarity_scores.empty
        else _table(
            similarity_scores,
            (
                "candidate_id",
                "reference_case_id",
                "similarity_score",
                "matched_pattern_count",
                "reference_pattern_count",
                "match_label",
            ),
        )
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Monitor Reference Candidates</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 28px; color: #17202a; }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, minmax(130px, 1fr)); gap: 12px; }}
    .metric {{ border: 1px solid #d7dde5; border-radius: 6px; padding: 12px; background: #f8fafc; }}
    .metric strong {{ display: block; font-size: 22px; margin-top: 4px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; font-size: 13px; }}
    th, td {{ border: 1px solid #d7dde5; padding: 7px; text-align: left; vertical-align: top; }}
    th {{ background: #eef2f7; }}
    .note {{ background: #fff7e6; border: 1px solid #f0d08a; padding: 12px; border-radius: 6px; }}
  </style>
</head>
<body>
  <h1>Monitor Reference Candidates</h1>
  <p class="note">Read-only diagnostic dashboard. Candidate rows are review cues only, not probability, causality, tradeability, or profitability evidence.</p>
  <section class="metrics">
    <div class="metric">Source rows<strong>{summary["source_alert_rows"]}</strong></div>
    <div class="metric">Non-none rows<strong>{summary["source_non_none_rows"]}</strong></div>
    <div class="metric">Candidates<strong>{summary["candidate_count"]}</strong></div>
    <div class="metric">Max score<strong>{float(summary["max_similarity_score"]):.2f}</strong></div>
  </section>
  <h2>Interpretation</h2>
  <p>{escape(str(summary["allowed_interpretation"]))}</p>
  <p>{escape(str(summary["limitation"]))}</p>
  <h2>Triggered Candidate Features</h2>
  {features_html}
  <h2>Best Reference Matches</h2>
  {similarity_html}
  <h2>All Reference Comparisons</h2>
  {all_scores_html}
</body>
</html>
"""
    dashboard_path.write_text(html, encoding="utf-8")


def _metadata(
    *,
    alert_rows: pd.DataFrame,
    candidate_features: pd.DataFrame,
    candidate_summary: pd.DataFrame,
    similarity_scores: pd.DataFrame,
    alert_rows_path: Path,
    reference_features_path: Path,
    candidate_features_path: Path,
    candidate_summary_path: Path,
    similarity_scores_path: Path,
    similarity_summary_path: Path,
    dashboard_path: Path,
) -> dict[str, Any]:
    summary = candidate_summary.iloc[0].to_dict()
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "monitor_reference_candidate_features",
            "candidate_filter": "severity != none",
            "uses_existing_files_only": True,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "does_not_use_rcp": True,
        },
        "inputs": {
            "alert_rows_path": str(alert_rows_path),
            "reference_features_path": str(reference_features_path),
            "source_alert_rows": int(len(alert_rows)),
        },
        "outputs": {
            "candidate_features_path": str(candidate_features_path),
            "candidate_summary_path": str(candidate_summary_path),
            "similarity_scores_path": str(similarity_scores_path),
            "similarity_summary_path": str(similarity_summary_path),
            "dashboard_path": str(dashboard_path),
            "candidate_count": int(summary["candidate_count"]),
            "triggered_feature_rows": int(summary["triggered_feature_rows"]),
            "similarity_comparison_rows": int(len(similarity_scores)),
            "max_similarity_score": _safe_similarity_max(similarity_scores),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "limitations": {
            "empty_output_when_no_non_none_monitor_rows": True,
            "aggregate_monitor_fields_only": True,
            "not_a_probability_model": True,
            "not_a_causal_test": True,
            "not_a_trade_or_profitability_signal": True,
            "requires_human_review": True,
        },
    }


def _candidate_id(timestamp_utc: object, market_id: object) -> str:
    return monitor_candidate_id(timestamp_utc, market_id)


def monitor_candidate_id(timestamp_utc: object, market_id: object) -> str:
    """Return the stable monitor candidate id for a timestamp and market."""

    raw = f"{timestamp_utc}|{market_id}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    timestamp = str(timestamp_utc).replace(":", "").replace("-", "").replace("Z", "")
    timestamp = timestamp.replace("T", "_")
    return f"monitor_candidate_{timestamp}_{digest}"


def _table(frame: pd.DataFrame, columns: Sequence[str]) -> str:
    rows: list[str] = []
    for item in frame.loc[:, list(columns)].to_dict(orient="records"):
        cells = "".join(f"<td>{escape(_format_cell(item[column]))}</td>" for column in columns)
        rows.append(f"<tr>{cells}</tr>")
    header = "".join(f"<th>{escape(column)}</th>" for column in columns)
    return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def _format_cell(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _safe_similarity_max(scores: pd.DataFrame) -> float:
    if scores.empty:
        return 0.0
    return float(pd.to_numeric(scores["similarity_score"], errors="coerce").fillna(0).max())


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _read_alert_rows(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"monitor alert rows file not found: {path}")
    frame = pd.read_csv(path, keep_default_na=False)
    _validate_monitor_alert_rows(frame)
    return frame


def _read_reference_features(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"reference features file not found: {path}")
    frame = pd.read_csv(path, keep_default_na=False)
    if frame.empty:
        raise ValueError(f"reference features file is empty: {path}")
    return frame


def _validate_monitor_alert_rows(frame: pd.DataFrame) -> None:
    missing = [column for column in MONITOR_ALERT_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"monitor alert rows missing required columns: {missing}")
    forbidden = [column for column in frame.columns if "wallet_address" in column.lower()]
    if forbidden:
        raise ValueError(f"monitor alert rows must not contain wallet-address columns: {forbidden}")
    invalid = sorted(set(frame["severity"].astype(str)) - {"none", "info", "watch", "high", "critical"})
    if invalid:
        raise ValueError(f"monitor alert rows contain invalid severity values: {invalid}")


if __name__ == "__main__":
    raise SystemExit(main())
