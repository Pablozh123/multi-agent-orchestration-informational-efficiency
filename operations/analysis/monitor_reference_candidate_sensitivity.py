"""Build diagnostic monitor candidates below the default Rule C alert line.

The sensitivity layer is deliberately separate from the strict monitor
reference-candidate adapter. It adds human-review cues for rows that did not
become alerts but are high-percentile zero-MAD observations.
"""
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

from operations.analysis.monitor_reference_candidates import (
    EVENT_CONTEXT_STATUSES,
    FEATURE_COLUMNS,
    MONITOR_ALERT_COLUMNS,
)
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


SENSITIVITY_CANDIDATE_ROWS_OUTPUT = (
    RESULTS_DIR / "monitor_reference_candidate_sensitivity_rows.csv"
)
SENSITIVITY_FEATURES_OUTPUT = (
    RESULTS_DIR / "monitor_reference_candidate_sensitivity_features.csv"
)
SENSITIVITY_SUMMARY_OUTPUT = (
    RESULTS_DIR / "monitor_reference_candidate_sensitivity_summary.csv"
)
SENSITIVITY_SIMILARITY_OUTPUT = (
    RESULTS_DIR / "monitor_reference_candidate_sensitivity_similarity_scores.csv"
)
SENSITIVITY_SIMILARITY_SUMMARY_OUTPUT = (
    RESULTS_DIR / "monitor_reference_candidate_sensitivity_similarity_summary.csv"
)
SENSITIVITY_DASHBOARD_OUTPUT = (
    RESULTS_DIR / "monitor_reference_candidate_sensitivity_dashboard.html"
)
SENSITIVITY_METADATA_OUTPUT = (
    RESULTS_DIR / "monitor_reference_candidate_sensitivity_metadata.json"
)

DEFAULT_SHADOW_PERCENTILE_THRESHOLD = 0.95
DEFAULT_SHADOW_MIN_BASELINE_OBSERVATIONS = 20

CANDIDATE_ROW_COLUMNS: tuple[str, ...] = (
    "candidate_id",
    "candidate_kind",
    "timestamp_utc",
    "market_id",
    "source_row_count",
    "anomaly_families",
    "metric_names",
    "max_percentile_rank",
    "max_baseline_observations",
    "has_wallet_amount_feature",
    "has_concentration_feature",
    "has_event_context",
    "market_only_diagnostic",
    "review_status",
    "claim_scope",
    "allowed_interpretation",
    "limitation",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "summary_id",
    "source_alert_rows",
    "source_strict_rows",
    "source_shadow_rows",
    "candidate_count",
    "strict_candidate_count",
    "shadow_candidate_count",
    "market_only_shadow_candidate_count",
    "candidate_feature_rows",
    "triggered_feature_rows",
    "similarity_comparison_rows",
    "max_similarity_score",
    "allowed_interpretation",
    "limitation",
)


@dataclass(frozen=True)
class MonitorReferenceCandidateSensitivityResult:
    """Summary of generated sensitivity artifacts."""

    candidate_rows_path: Path
    candidate_features_path: Path
    candidate_summary_path: Path
    similarity_scores_path: Path
    similarity_summary_path: Path
    dashboard_path: Path
    metadata_path: Path
    candidate_count: int
    shadow_candidate_count: int
    market_only_shadow_candidate_count: int
    similarity_comparison_rows: int
    max_similarity_score: float

    def to_dict(self) -> dict[str, float | int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "candidate_rows_path": str(self.candidate_rows_path),
            "candidate_features_path": str(self.candidate_features_path),
            "candidate_summary_path": str(self.candidate_summary_path),
            "similarity_scores_path": str(self.similarity_scores_path),
            "similarity_summary_path": str(self.similarity_summary_path),
            "dashboard_path": str(self.dashboard_path),
            "metadata_path": str(self.metadata_path),
            "candidate_count": self.candidate_count,
            "shadow_candidate_count": self.shadow_candidate_count,
            "market_only_shadow_candidate_count": self.market_only_shadow_candidate_count,
            "similarity_comparison_rows": self.similarity_comparison_rows,
            "max_similarity_score": self.max_similarity_score,
        }


def build_monitor_reference_candidate_sensitivity_rows(
    alert_rows: pd.DataFrame,
    *,
    shadow_percentile_threshold: float = DEFAULT_SHADOW_PERCENTILE_THRESHOLD,
    shadow_min_baseline_observations: int = DEFAULT_SHADOW_MIN_BASELINE_OBSERVATIONS,
) -> pd.DataFrame:
    """Return grouped strict and shadow diagnostic monitor candidates."""

    _validate_alert_rows(alert_rows)
    candidate_source = _candidate_source_rows(
        alert_rows,
        shadow_percentile_threshold=shadow_percentile_threshold,
        shadow_min_baseline_observations=shadow_min_baseline_observations,
    )
    if candidate_source.empty:
        return pd.DataFrame(columns=CANDIDATE_ROW_COLUMNS)

    rows: list[dict[str, object]] = []
    for (timestamp_utc, market_id, candidate_kind), group in candidate_source.groupby(
        ["timestamp_utc", "market_id", "candidate_kind"],
        sort=True,
    ):
        families = sorted(set(group["anomaly_family"].astype(str)))
        metrics = sorted(set(group["metric_name"].astype(str)))
        has_wallet_amount = (
            "wallet_tier_activity" in families
            and "log1p_total_observed_amount_usd" in metrics
        )
        has_concentration = "concentration" in families
        has_event_context = _has_event_context(group)
        market_only = candidate_kind == "shadow_percentile_candidate" and set(families) == {
            "market_move"
        }
        rows.append(
            {
                "candidate_id": _candidate_id(candidate_kind, timestamp_utc, market_id),
                "candidate_kind": candidate_kind,
                "timestamp_utc": timestamp_utc,
                "market_id": market_id,
                "source_row_count": int(len(group)),
                "anomaly_families": ",".join(families),
                "metric_names": ",".join(metrics),
                "max_percentile_rank": _max_numeric(group["rolling_percentile_rank"]),
                "max_baseline_observations": int(
                    _max_numeric(group["baseline_observations"])
                ),
                "has_wallet_amount_feature": bool(has_wallet_amount),
                "has_concentration_feature": bool(has_concentration),
                "has_event_context": bool(has_event_context),
                "market_only_diagnostic": bool(market_only),
                "review_status": "candidate",
                "claim_scope": "diagnostic_sensitivity_review_only",
                "allowed_interpretation": _candidate_interpretation(
                    candidate_kind,
                    market_only=market_only,
                ),
                "limitation": (
                    "Diagnostic sensitivity candidate only; not a Rule C alert, "
                    "not a probability model, and not a trading signal."
                ),
            }
        )
    return pd.DataFrame(rows, columns=CANDIDATE_ROW_COLUMNS)


def build_monitor_reference_candidate_sensitivity_features(
    alert_rows: pd.DataFrame,
    *,
    shadow_percentile_threshold: float = DEFAULT_SHADOW_PERCENTILE_THRESHOLD,
    shadow_min_baseline_observations: int = DEFAULT_SHADOW_MIN_BASELINE_OBSERVATIONS,
) -> pd.DataFrame:
    """Return neutral pattern features for sensitivity candidates."""

    _validate_alert_rows(alert_rows)
    candidate_source = _candidate_source_rows(
        alert_rows,
        shadow_percentile_threshold=shadow_percentile_threshold,
        shadow_min_baseline_observations=shadow_min_baseline_observations,
    )
    if candidate_source.empty:
        return pd.DataFrame(columns=FEATURE_COLUMNS)

    strict_market_counts = (
        candidate_source[candidate_source["candidate_kind"] == "strict_candidate"]
        .groupby("market_id")["timestamp_utc"]
        .nunique()
        .to_dict()
    )
    feature_rows: list[dict[str, object]] = []
    for (timestamp_utc, market_id, candidate_kind), group in candidate_source.groupby(
        ["timestamp_utc", "market_id", "candidate_kind"],
        sort=True,
    ):
        repeated_market_alerts = (
            int(strict_market_counts.get(market_id, 0))
            if candidate_kind == "strict_candidate"
            else 0
        )
        feature_rows.extend(
            _features_for_group(
                group,
                candidate_id=_candidate_id(candidate_kind, timestamp_utc, market_id),
                candidate_kind=str(candidate_kind),
                repeated_market_alerts=repeated_market_alerts,
            )
        )
    return pd.DataFrame(feature_rows, columns=FEATURE_COLUMNS)


def generate_monitor_reference_candidate_sensitivity(
    *,
    alert_rows_path: Path = ROLLING_ALERT_ROWS_OUTPUT,
    reference_features_path: Path = REFERENCE_FEATURES_INPUT,
    candidate_rows_path: Path = SENSITIVITY_CANDIDATE_ROWS_OUTPUT,
    candidate_features_path: Path = SENSITIVITY_FEATURES_OUTPUT,
    candidate_summary_path: Path = SENSITIVITY_SUMMARY_OUTPUT,
    similarity_scores_path: Path = SENSITIVITY_SIMILARITY_OUTPUT,
    similarity_summary_path: Path = SENSITIVITY_SIMILARITY_SUMMARY_OUTPUT,
    dashboard_path: Path = SENSITIVITY_DASHBOARD_OUTPUT,
    metadata_path: Path = SENSITIVITY_METADATA_OUTPUT,
    shadow_percentile_threshold: float = DEFAULT_SHADOW_PERCENTILE_THRESHOLD,
    shadow_min_baseline_observations: int = DEFAULT_SHADOW_MIN_BASELINE_OBSERVATIONS,
) -> MonitorReferenceCandidateSensitivityResult:
    """Write sensitivity rows, similarity outputs, dashboard, and metadata."""

    alert_rows = _read_alert_rows(alert_rows_path)
    reference_features = _read_reference_features(reference_features_path)
    candidate_rows = build_monitor_reference_candidate_sensitivity_rows(
        alert_rows,
        shadow_percentile_threshold=shadow_percentile_threshold,
        shadow_min_baseline_observations=shadow_min_baseline_observations,
    )
    candidate_features = build_monitor_reference_candidate_sensitivity_features(
        alert_rows,
        shadow_percentile_threshold=shadow_percentile_threshold,
        shadow_min_baseline_observations=shadow_min_baseline_observations,
    )
    similarity_scores = _similarity_scores(candidate_features, reference_features)
    similarity_summary = build_reference_similarity_summary(similarity_scores)
    candidate_summary = _candidate_summary(
        alert_rows=alert_rows,
        candidate_rows=candidate_rows,
        candidate_features=candidate_features,
        similarity_scores=similarity_scores,
        shadow_percentile_threshold=shadow_percentile_threshold,
        shadow_min_baseline_observations=shadow_min_baseline_observations,
    )

    _write_csv(candidate_rows_path, candidate_rows)
    _write_csv(candidate_features_path, candidate_features)
    _write_csv(candidate_summary_path, candidate_summary)
    _write_csv(similarity_scores_path, similarity_scores)
    _write_csv(similarity_summary_path, similarity_summary)
    _write_dashboard(
        candidate_summary=candidate_summary,
        candidate_rows=candidate_rows,
        candidate_features=candidate_features,
        similarity_summary=similarity_summary,
        similarity_scores=similarity_scores,
        dashboard_path=dashboard_path,
    )
    metadata = _metadata(
        alert_rows=alert_rows,
        candidate_rows=candidate_rows,
        candidate_features=candidate_features,
        candidate_summary=candidate_summary,
        similarity_scores=similarity_scores,
        alert_rows_path=alert_rows_path,
        reference_features_path=reference_features_path,
        candidate_rows_path=candidate_rows_path,
        candidate_features_path=candidate_features_path,
        candidate_summary_path=candidate_summary_path,
        similarity_scores_path=similarity_scores_path,
        similarity_summary_path=similarity_summary_path,
        dashboard_path=dashboard_path,
        shadow_percentile_threshold=shadow_percentile_threshold,
        shadow_min_baseline_observations=shadow_min_baseline_observations,
    )
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = candidate_summary.iloc[0].to_dict()
    return MonitorReferenceCandidateSensitivityResult(
        candidate_rows_path=candidate_rows_path,
        candidate_features_path=candidate_features_path,
        candidate_summary_path=candidate_summary_path,
        similarity_scores_path=similarity_scores_path,
        similarity_summary_path=similarity_summary_path,
        dashboard_path=dashboard_path,
        metadata_path=metadata_path,
        candidate_count=int(summary["candidate_count"]),
        shadow_candidate_count=int(summary["shadow_candidate_count"]),
        market_only_shadow_candidate_count=int(
            summary["market_only_shadow_candidate_count"]
        ),
        similarity_comparison_rows=int(summary["similarity_comparison_rows"]),
        max_similarity_score=float(summary["max_similarity_score"]),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--alert-rows", type=Path, default=ROLLING_ALERT_ROWS_OUTPUT)
    parser.add_argument("--reference-features", type=Path, default=REFERENCE_FEATURES_INPUT)
    parser.add_argument("--candidate-rows-output", type=Path, default=SENSITIVITY_CANDIDATE_ROWS_OUTPUT)
    parser.add_argument("--candidate-features-output", type=Path, default=SENSITIVITY_FEATURES_OUTPUT)
    parser.add_argument("--candidate-summary-output", type=Path, default=SENSITIVITY_SUMMARY_OUTPUT)
    parser.add_argument("--similarity-scores-output", type=Path, default=SENSITIVITY_SIMILARITY_OUTPUT)
    parser.add_argument(
        "--similarity-summary-output",
        type=Path,
        default=SENSITIVITY_SIMILARITY_SUMMARY_OUTPUT,
    )
    parser.add_argument("--dashboard-output", type=Path, default=SENSITIVITY_DASHBOARD_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=SENSITIVITY_METADATA_OUTPUT)
    parser.add_argument(
        "--shadow-percentile-threshold",
        type=float,
        default=DEFAULT_SHADOW_PERCENTILE_THRESHOLD,
    )
    parser.add_argument(
        "--shadow-min-baseline-observations",
        type=int,
        default=DEFAULT_SHADOW_MIN_BASELINE_OBSERVATIONS,
    )
    args = parser.parse_args(argv)

    try:
        result = generate_monitor_reference_candidate_sensitivity(
            alert_rows_path=args.alert_rows,
            reference_features_path=args.reference_features,
            candidate_rows_path=args.candidate_rows_output,
            candidate_features_path=args.candidate_features_output,
            candidate_summary_path=args.candidate_summary_output,
            similarity_scores_path=args.similarity_scores_output,
            similarity_summary_path=args.similarity_summary_output,
            dashboard_path=args.dashboard_output,
            metadata_path=args.metadata_output,
            shadow_percentile_threshold=args.shadow_percentile_threshold,
            shadow_min_baseline_observations=args.shadow_min_baseline_observations,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _candidate_source_rows(
    alert_rows: pd.DataFrame,
    *,
    shadow_percentile_threshold: float,
    shadow_min_baseline_observations: int,
) -> pd.DataFrame:
    rows = alert_rows.copy()
    rows["_rolling_percentile_numeric"] = pd.to_numeric(
        rows["rolling_percentile_rank"],
        errors="coerce",
    )
    rows["_baseline_observations_numeric"] = pd.to_numeric(
        rows["baseline_observations"],
        errors="coerce",
    )
    strict = rows[rows["severity"].astype(str) != "none"].copy()
    strict["candidate_kind"] = "strict_candidate"
    shadow = rows[
        (rows["severity"].astype(str) == "none")
        & (rows["status"].astype(str) == "zero_mad")
        & (rows["_rolling_percentile_numeric"] >= shadow_percentile_threshold)
        & (rows["_baseline_observations_numeric"] >= shadow_min_baseline_observations)
    ].copy()
    shadow["candidate_kind"] = "shadow_percentile_candidate"
    return pd.concat([strict, shadow], ignore_index=True)


def _features_for_group(
    group: pd.DataFrame,
    *,
    candidate_id: str,
    candidate_kind: str,
    repeated_market_alerts: int,
) -> list[dict[str, object]]:
    families = set(group["anomaly_family"].astype(str))
    metrics = set(group["metric_name"].astype(str))
    has_event_context = _has_event_context(group)
    market_only_shadow = candidate_kind == "shadow_percentile_candidate" and families == {
        "market_move"
    }
    feature_status_by_label = {
        "large_trade_flow": (
            "triggered"
            if not market_only_shadow
            and "wallet_tier_activity" in families
            and "log1p_total_observed_amount_usd" in metrics
            else "unknown"
        ),
        "market_concentration": (
            "triggered"
            if not market_only_shadow and "concentration" in families
            else "unknown"
        ),
        "event_proximity": (
            "triggered" if not market_only_shadow and has_event_context else "unknown"
        ),
        "fresh_wallet_or_short_history": "unknown",
        "cluster_link_reported": "unknown",
        "shared_funding_reported": "unknown",
        "high_reported_win_rate": "unknown",
        "same_theme_repeated_positions": (
            "triggered"
            if candidate_kind == "strict_candidate" and repeated_market_alerts > 1
            else "unknown"
        ),
    }
    rows: list[dict[str, object]] = []
    for pattern_label in PATTERN_LABELS:
        status = feature_status_by_label[pattern_label]
        rows.append(
            {
                "case_id": candidate_id,
                "case_type": (
                    "monitor_strict_candidate"
                    if candidate_kind == "strict_candidate"
                    else "monitor_shadow_percentile_candidate"
                ),
                "pattern_label": pattern_label,
                "feature_status": status,
                "fact_source": "computed" if status == "triggered" else "unknown",
                "reason": _reason_for_label(pattern_label, status, candidate_kind),
                "evidence_status": "pattern_computed" if status == "triggered" else "candidate",
                "claim_scope": "diagnostic_sensitivity_review_only",
                "requires_human_review": True,
            }
        )
    return rows


def _reason_for_label(pattern_label: str, status: str, candidate_kind: str) -> str:
    if status != "triggered":
        if candidate_kind == "shadow_percentile_candidate":
            return "not triggered by diagnostic shadow candidate inputs"
        return "source data unavailable in current monitor alert rows"
    if pattern_label == "large_trade_flow":
        return "wallet-tier amount metric met candidate criteria"
    if pattern_label == "market_concentration":
        return "concentration metric met candidate criteria"
    if pattern_label == "event_proximity":
        return "candidate row has reviewed event context"
    if pattern_label == "same_theme_repeated_positions":
        return "same market has strict monitor candidates at multiple timestamps"
    return "computed from monitor candidate rows"


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
    candidate_rows: pd.DataFrame,
    candidate_features: pd.DataFrame,
    similarity_scores: pd.DataFrame,
    shadow_percentile_threshold: float,
    shadow_min_baseline_observations: int,
) -> pd.DataFrame:
    strict_source_rows = int((alert_rows["severity"].astype(str) != "none").sum())
    source_shadow = _candidate_source_rows(
        alert_rows,
        shadow_percentile_threshold=shadow_percentile_threshold,
        shadow_min_baseline_observations=shadow_min_baseline_observations,
    )
    shadow_source_rows = int(
        (source_shadow["candidate_kind"] == "shadow_percentile_candidate").sum()
    )
    candidate_count = int(len(candidate_rows))
    strict_candidates = int(
        (candidate_rows["candidate_kind"] == "strict_candidate").sum()
    ) if not candidate_rows.empty else 0
    shadow_candidates = int(
        (candidate_rows["candidate_kind"] == "shadow_percentile_candidate").sum()
    ) if not candidate_rows.empty else 0
    market_only_shadow = int(
        candidate_rows["market_only_diagnostic"].astype(bool).sum()
    ) if not candidate_rows.empty else 0
    triggered_count = (
        int((candidate_features["feature_status"] == "triggered").sum())
        if not candidate_features.empty
        else 0
    )
    return pd.DataFrame(
        [
            {
                "summary_id": "monitor_reference_candidate_sensitivity_current",
                "source_alert_rows": int(len(alert_rows)),
                "source_strict_rows": strict_source_rows,
                "source_shadow_rows": shadow_source_rows,
                "candidate_count": candidate_count,
                "strict_candidate_count": strict_candidates,
                "shadow_candidate_count": shadow_candidates,
                "market_only_shadow_candidate_count": market_only_shadow,
                "candidate_feature_rows": int(len(candidate_features)),
                "triggered_feature_rows": triggered_count,
                "similarity_comparison_rows": int(len(similarity_scores)),
                "max_similarity_score": _safe_similarity_max(similarity_scores),
                "allowed_interpretation": _summary_interpretation(
                    candidate_count,
                    market_only_shadow,
                ),
                "limitation": (
                    "Sensitivity candidates are review cues below or at the "
                    "monitor candidate boundary; Rule C remains unchanged."
                ),
            }
        ],
        columns=SUMMARY_COLUMNS,
    )


def _summary_interpretation(candidate_count: int, market_only_shadow_count: int) -> str:
    if candidate_count == 0:
        return "No strict or diagnostic shadow candidates were generated."
    if candidate_count == market_only_shadow_count:
        return (
            "All diagnostic candidates are market-only shadow rows; they require "
            "human review and do not imply wallet anomalies."
        )
    return "Diagnostic sensitivity candidates were generated for human review only."


def _candidate_interpretation(candidate_kind: object, *, market_only: bool) -> str:
    if candidate_kind == "strict_candidate":
        return "Strict monitor candidate from non-none severity rows."
    if market_only:
        return "Market-only diagnostic shadow candidate; no wallet-pattern label is triggered."
    return "Diagnostic shadow candidate below Rule C; review evidence before use."


def _write_dashboard(
    *,
    candidate_summary: pd.DataFrame,
    candidate_rows: pd.DataFrame,
    candidate_features: pd.DataFrame,
    similarity_summary: pd.DataFrame,
    similarity_scores: pd.DataFrame,
    dashboard_path: Path,
) -> None:
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    summary = candidate_summary.iloc[0].to_dict()
    candidates_html = (
        "<p>No sensitivity candidates generated.</p>"
        if candidate_rows.empty
        else _table(
            candidate_rows,
            (
                "candidate_id",
                "candidate_kind",
                "timestamp_utc",
                "anomaly_families",
                "max_percentile_rank",
                "market_only_diagnostic",
            ),
        )
    )
    triggered = (
        candidate_features[candidate_features["feature_status"] == "triggered"]
        if not candidate_features.empty
        else candidate_features
    )
    features_html = (
        "<p>No triggered wallet/reference pattern labels.</p>"
        if triggered.empty
        else _table(
            triggered,
            ("case_id", "case_type", "pattern_label", "fact_source", "reason"),
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
  <title>Diagnostic Monitor Candidate Sensitivity</title>
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
  <h1>Diagnostic Monitor Candidate Sensitivity</h1>
  <p class="note">Read-only diagnostic layer. Shadow candidates are human-review cues only. Rule C remains unchanged.</p>
  <section class="metrics">
    <div class="metric">Candidates<strong>{summary["candidate_count"]}</strong></div>
    <div class="metric">Shadow candidates<strong>{summary["shadow_candidate_count"]}</strong></div>
    <div class="metric">Market-only shadow<strong>{summary["market_only_shadow_candidate_count"]}</strong></div>
    <div class="metric">Max score<strong>{float(summary["max_similarity_score"]):.2f}</strong></div>
  </section>
  <h2>Interpretation</h2>
  <p>{escape(str(summary["allowed_interpretation"]))}</p>
  <p>{escape(str(summary["limitation"]))}</p>
  <h2>Candidate Rows</h2>
  {candidates_html}
  <h2>Triggered Pattern Features</h2>
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
    candidate_rows: pd.DataFrame,
    candidate_features: pd.DataFrame,
    candidate_summary: pd.DataFrame,
    similarity_scores: pd.DataFrame,
    alert_rows_path: Path,
    reference_features_path: Path,
    candidate_rows_path: Path,
    candidate_features_path: Path,
    candidate_summary_path: Path,
    similarity_scores_path: Path,
    similarity_summary_path: Path,
    dashboard_path: Path,
    shadow_percentile_threshold: float,
    shadow_min_baseline_observations: int,
) -> dict[str, Any]:
    summary = candidate_summary.iloc[0].to_dict()
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "monitor_reference_candidate_diagnostic_sensitivity",
            "strict_candidate_filter": "severity != none",
            "shadow_candidate_filter": (
                "severity == none and status == zero_mad and "
                f"rolling_percentile_rank >= {shadow_percentile_threshold} and "
                f"baseline_observations >= {shadow_min_baseline_observations}"
            ),
            "default_rule_c_unchanged": True,
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
            "candidate_rows_path": str(candidate_rows_path),
            "candidate_features_path": str(candidate_features_path),
            "candidate_summary_path": str(candidate_summary_path),
            "similarity_scores_path": str(similarity_scores_path),
            "similarity_summary_path": str(similarity_summary_path),
            "dashboard_path": str(dashboard_path),
            "candidate_count": int(summary["candidate_count"]),
            "strict_candidate_count": int(summary["strict_candidate_count"]),
            "shadow_candidate_count": int(summary["shadow_candidate_count"]),
            "market_only_shadow_candidate_count": int(
                summary["market_only_shadow_candidate_count"]
            ),
            "candidate_feature_rows": int(len(candidate_features)),
            "triggered_feature_rows": int(summary["triggered_feature_rows"]),
            "similarity_comparison_rows": int(len(similarity_scores)),
            "max_similarity_score": _safe_similarity_max(similarity_scores),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "limitations": {
            "diagnostic_shadow_candidates_only": True,
            "strict_alert_rule_unchanged": True,
            "market_only_shadow_candidates_are_not_wallet_anomalies": True,
            "not_a_probability_model": True,
            "not_a_causal_test": True,
            "not_a_trade_or_profitability_signal": True,
            "requires_human_review": True,
        },
        "quality_checks": {
            "candidate_rows": int(len(candidate_rows)),
            "candidate_features": int(len(candidate_features)),
            "wallet_address_columns_present": False,
        },
    }


def _candidate_id(candidate_kind: object, timestamp_utc: object, market_id: object) -> str:
    raw = f"{candidate_kind}|{timestamp_utc}|{market_id}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    timestamp = str(timestamp_utc).replace(":", "").replace("-", "").replace("Z", "")
    timestamp = timestamp.replace("T", "_")
    prefix = (
        "monitor_strict_candidate"
        if candidate_kind == "strict_candidate"
        else "monitor_shadow_candidate"
    )
    return f"{prefix}_{timestamp}_{digest}"


def _has_event_context(group: pd.DataFrame) -> bool:
    return (
        group["event_candidate_id"].fillna("").astype(str).str.strip().ne("").any()
        and group["event_review_status"].astype(str).isin(EVENT_CONTEXT_STATUSES).any()
    )


def _max_numeric(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    return float(pd.to_numeric(series, errors="coerce").fillna(0).max())


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
    _validate_alert_rows(frame)
    return frame


def _read_reference_features(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"reference features file not found: {path}")
    frame = pd.read_csv(path, keep_default_na=False)
    if frame.empty:
        raise ValueError(f"reference features file is empty: {path}")
    return frame


def _validate_alert_rows(frame: pd.DataFrame) -> None:
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
