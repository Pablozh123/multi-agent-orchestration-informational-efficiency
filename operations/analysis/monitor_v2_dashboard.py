"""Generate a static read-only dashboard for monitor v2 outputs."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from operations.analysis.monitor_v2_polymarket_rolling_figures import (
    ROLLING_FIGURE_OUTPUT,
)
from operations.analysis.monitor_reference_candidates import (
    CANDIDATE_DASHBOARD_OUTPUT,
    CANDIDATE_METADATA_OUTPUT,
)
from operations.analysis.monitor_reference_candidate_sensitivity import (
    SENSITIVITY_DASHBOARD_OUTPUT,
    SENSITIVITY_METADATA_OUTPUT,
)
from operations.analysis.monitor_candidate_review_report import (
    REVIEW_DASHBOARD_OUTPUT,
    REVIEW_METADATA_OUTPUT,
)
from operations.analysis.monitor_literature_risk_scores import (
    RISK_SCORE_METADATA_OUTPUT,
    RISK_SCORE_SUMMARY_OUTPUT,
)
from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.analysis.wallet_reference_similarity import (
    SIMILARITY_DASHBOARD_OUTPUT,
    SIMILARITY_METADATA_OUTPUT,
)
from operations.collectors.polymarket_readonly import (
    LIVE_MARKET_SNAPSHOTS_OUTPUT,
    LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT,
    LIVE_WATCHLIST_OUTPUT,
)
from operations.collectors.polymarket_rolling_history import (
    ROLLING_ALERT_SUMMARY_OUTPUT,
    ROLLING_HISTORY_METADATA_OUTPUT,
    ROLLING_SCORING_METADATA_OUTPUT,
)


DASHBOARD_OUTPUT = RESULTS_DIR / "monitor_v2_polymarket_dashboard.html"
DASHBOARD_METADATA_OUTPUT = RESULTS_DIR / "monitor_v2_polymarket_dashboard_metadata.json"


@dataclass(frozen=True)
class DashboardResult:
    """Summary of generated dashboard artifacts."""

    dashboard_path: Path
    metadata_path: Path
    market_count: int
    bucket_count: int
    alert_count: int
    baseline_readiness: str

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "dashboard_path": str(self.dashboard_path),
            "metadata_path": str(self.metadata_path),
            "market_count": self.market_count,
            "bucket_count": self.bucket_count,
            "alert_count": self.alert_count,
            "baseline_readiness": self.baseline_readiness,
        }


def generate_monitor_v2_dashboard(
    *,
    watchlist_path: Path = LIVE_WATCHLIST_OUTPUT,
    market_snapshots_path: Path = LIVE_MARKET_SNAPSHOTS_OUTPUT,
    wallet_tier_snapshots_path: Path = LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT,
    alert_summary_path: Path = ROLLING_ALERT_SUMMARY_OUTPUT,
    scoring_metadata_path: Path = ROLLING_SCORING_METADATA_OUTPUT,
    rolling_metadata_path: Path = ROLLING_HISTORY_METADATA_OUTPUT,
    figure_path: Path = ROLLING_FIGURE_OUTPUT,
    reference_similarity_metadata_path: Path = SIMILARITY_METADATA_OUTPUT,
    reference_similarity_dashboard_path: Path = SIMILARITY_DASHBOARD_OUTPUT,
    reference_candidate_metadata_path: Path = CANDIDATE_METADATA_OUTPUT,
    reference_candidate_dashboard_path: Path = CANDIDATE_DASHBOARD_OUTPUT,
    reference_sensitivity_metadata_path: Path = SENSITIVITY_METADATA_OUTPUT,
    reference_sensitivity_dashboard_path: Path = SENSITIVITY_DASHBOARD_OUTPUT,
    human_review_metadata_path: Path = REVIEW_METADATA_OUTPUT,
    human_review_dashboard_path: Path = REVIEW_DASHBOARD_OUTPUT,
    literature_risk_metadata_path: Path = RISK_SCORE_METADATA_OUTPUT,
    literature_risk_summary_path: Path = RISK_SCORE_SUMMARY_OUTPUT,
    dashboard_path: Path = DASHBOARD_OUTPUT,
    metadata_path: Path = DASHBOARD_METADATA_OUTPUT,
) -> DashboardResult:
    """Generate a local HTML dashboard from bounded monitor output files."""

    watchlist = _read_csv(watchlist_path, "watchlist")
    market = _read_csv(market_snapshots_path, "market snapshots")
    wallets = _read_csv(wallet_tier_snapshots_path, "wallet-tier snapshots")
    alerts = _read_csv(alert_summary_path, "alert summary")
    scoring_metadata = _read_json(scoring_metadata_path, "scoring metadata")
    rolling_metadata = _read_json(rolling_metadata_path, "rolling metadata")
    reference_similarity_metadata = _read_optional_json(
        reference_similarity_metadata_path,
        "reference similarity metadata",
    )
    reference_candidate_metadata = _read_optional_json(
        reference_candidate_metadata_path,
        "reference candidate metadata",
    )
    reference_sensitivity_metadata = _read_optional_json(
        reference_sensitivity_metadata_path,
        "reference sensitivity metadata",
    )
    human_review_metadata = _read_optional_json(
        human_review_metadata_path,
        "human review metadata",
    )
    literature_risk_metadata = _read_optional_json(
        literature_risk_metadata_path,
        "literature-prior risk score metadata",
    )
    _assert_no_wallet_columns((watchlist, market, wallets, alerts))

    metrics = _dashboard_metrics(
        watchlist=watchlist,
        market=market,
        alerts=alerts,
        scoring_metadata=scoring_metadata,
        rolling_metadata=rolling_metadata,
        reference_similarity_metadata=reference_similarity_metadata,
        reference_candidate_metadata=reference_candidate_metadata,
        reference_sensitivity_metadata=reference_sensitivity_metadata,
        human_review_metadata=human_review_metadata,
        literature_risk_metadata=literature_risk_metadata,
    )
    _assert_reference_review_safe(metrics["reference_review"])
    html = _render_dashboard(
        watchlist=watchlist,
        market=market,
        wallets=wallets,
        alerts=alerts,
        metrics=metrics,
        figure_path=figure_path,
        reference_similarity_dashboard_path=reference_similarity_dashboard_path,
        reference_candidate_dashboard_path=reference_candidate_dashboard_path,
        reference_sensitivity_dashboard_path=reference_sensitivity_dashboard_path,
        human_review_dashboard_path=human_review_dashboard_path,
        literature_risk_summary_path=literature_risk_summary_path,
        source_paths={
            "watchlist": watchlist_path,
            "market snapshots": market_snapshots_path,
            "wallet-tier snapshots": wallet_tier_snapshots_path,
            "alert summary": alert_summary_path,
            "scoring metadata": scoring_metadata_path,
            "rolling metadata": rolling_metadata_path,
            "figure": figure_path,
            "wallet reference similarity dashboard": reference_similarity_dashboard_path,
            "monitor reference candidate dashboard": reference_candidate_dashboard_path,
            "diagnostic sensitivity candidate dashboard": reference_sensitivity_dashboard_path,
            "human review report": human_review_dashboard_path,
            "literature-prior risk score summary": literature_risk_summary_path,
        },
    )
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    dashboard_path.write_text(html, encoding="utf-8")
    metadata = {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "monitor_v2_static_dashboard",
            "read_only": True,
            "uses_bounded_local_files": True,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
        },
        "outputs": {
            **metrics,
            "dashboard_path": str(dashboard_path),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "source_paths": {name: str(path) for name, path in source_paths.items()}
        if (source_paths := {
            "watchlist": watchlist_path,
            "market_snapshots": market_snapshots_path,
            "wallet_tier_snapshots": wallet_tier_snapshots_path,
            "alert_summary": alert_summary_path,
            "scoring_metadata": scoring_metadata_path,
            "rolling_metadata": rolling_metadata_path,
            "figure": figure_path,
            "wallet_reference_similarity_metadata": reference_similarity_metadata_path,
            "monitor_reference_candidate_metadata": reference_candidate_metadata_path,
            "monitor_reference_candidate_sensitivity_metadata": reference_sensitivity_metadata_path,
            "monitor_candidate_human_review_metadata": human_review_metadata_path,
            "monitor_literature_risk_score_metadata": literature_risk_metadata_path,
        })
        else {},
        "limitations": {
            "descriptive_dashboard_only": True,
            "short_rolling_history": metrics["bucket_count"] < 20,
            "no_causal_or_profitability_claim": True,
        },
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return DashboardResult(
        dashboard_path=dashboard_path,
        metadata_path=metadata_path,
        market_count=int(metrics["market_count"]),
        bucket_count=int(metrics["bucket_count"]),
        alert_count=int(metrics["alert_count"]),
        baseline_readiness=str(metrics["baseline_readiness"]),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--watchlist", type=Path, default=LIVE_WATCHLIST_OUTPUT)
    parser.add_argument("--market-snapshots", type=Path, default=LIVE_MARKET_SNAPSHOTS_OUTPUT)
    parser.add_argument("--wallet-tier-snapshots", type=Path, default=LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT)
    parser.add_argument("--alert-summary", type=Path, default=ROLLING_ALERT_SUMMARY_OUTPUT)
    parser.add_argument("--scoring-metadata", type=Path, default=ROLLING_SCORING_METADATA_OUTPUT)
    parser.add_argument("--rolling-metadata", type=Path, default=ROLLING_HISTORY_METADATA_OUTPUT)
    parser.add_argument("--figure", type=Path, default=ROLLING_FIGURE_OUTPUT)
    parser.add_argument(
        "--reference-similarity-metadata",
        type=Path,
        default=SIMILARITY_METADATA_OUTPUT,
    )
    parser.add_argument(
        "--reference-similarity-dashboard",
        type=Path,
        default=SIMILARITY_DASHBOARD_OUTPUT,
    )
    parser.add_argument(
        "--reference-candidate-metadata",
        type=Path,
        default=CANDIDATE_METADATA_OUTPUT,
    )
    parser.add_argument(
        "--reference-candidate-dashboard",
        type=Path,
        default=CANDIDATE_DASHBOARD_OUTPUT,
    )
    parser.add_argument(
        "--reference-sensitivity-metadata",
        type=Path,
        default=SENSITIVITY_METADATA_OUTPUT,
    )
    parser.add_argument(
        "--reference-sensitivity-dashboard",
        type=Path,
        default=SENSITIVITY_DASHBOARD_OUTPUT,
    )
    parser.add_argument("--human-review-metadata", type=Path, default=REVIEW_METADATA_OUTPUT)
    parser.add_argument("--human-review-dashboard", type=Path, default=REVIEW_DASHBOARD_OUTPUT)
    parser.add_argument(
        "--literature-risk-metadata",
        type=Path,
        default=RISK_SCORE_METADATA_OUTPUT,
    )
    parser.add_argument(
        "--literature-risk-summary",
        type=Path,
        default=RISK_SCORE_SUMMARY_OUTPUT,
    )
    parser.add_argument("--dashboard-output", type=Path, default=DASHBOARD_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=DASHBOARD_METADATA_OUTPUT)
    args = parser.parse_args(argv)

    try:
        result = generate_monitor_v2_dashboard(
            watchlist_path=args.watchlist,
            market_snapshots_path=args.market_snapshots,
            wallet_tier_snapshots_path=args.wallet_tier_snapshots,
            alert_summary_path=args.alert_summary,
            scoring_metadata_path=args.scoring_metadata,
            rolling_metadata_path=args.rolling_metadata,
            figure_path=args.figure,
            reference_similarity_metadata_path=args.reference_similarity_metadata,
            reference_similarity_dashboard_path=args.reference_similarity_dashboard,
            reference_candidate_metadata_path=args.reference_candidate_metadata,
            reference_candidate_dashboard_path=args.reference_candidate_dashboard,
            reference_sensitivity_metadata_path=args.reference_sensitivity_metadata,
            reference_sensitivity_dashboard_path=args.reference_sensitivity_dashboard,
            human_review_metadata_path=args.human_review_metadata,
            human_review_dashboard_path=args.human_review_dashboard,
            literature_risk_metadata_path=args.literature_risk_metadata,
            literature_risk_summary_path=args.literature_risk_summary,
            dashboard_path=args.dashboard_output,
            metadata_path=args.metadata_output,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _dashboard_metrics(
    *,
    watchlist: pd.DataFrame,
    market: pd.DataFrame,
    alerts: pd.DataFrame,
    scoring_metadata: dict[str, Any],
    rolling_metadata: dict[str, Any],
    reference_similarity_metadata: dict[str, Any],
    reference_candidate_metadata: dict[str, Any],
    reference_sensitivity_metadata: dict[str, Any],
    human_review_metadata: dict[str, Any],
    literature_risk_metadata: dict[str, Any],
) -> dict[str, Any]:
    outputs = scoring_metadata.get("outputs", {})
    method = scoring_metadata.get("method", {})
    figure_result = rolling_metadata.get("outputs", {}).get("figure_result", {})
    bucket_count = int(figure_result.get("bucket_count", market["bucket_end_utc"].nunique()))
    latest_bucket = str(market["bucket_end_utc"].max())
    return {
        "market_count": int(watchlist["market_id"].nunique()),
        "bucket_count": bucket_count,
        "latest_bucket_utc": latest_bucket,
        "alert_count": int(outputs.get("alert_count", int(alerts["alert_count"].sum()))),
        "baseline_readiness": str(method.get("baseline_readiness", "")),
        "baseline_observations": int(method.get("baseline_observations", 0)),
        "min_baseline_observations": int(method.get("min_baseline_observations", 0)),
        "production_like_baseline_available": bool(
            method.get("production_like_baseline_available", False)
        ),
        "severity_counts": outputs.get("severity_counts", {}),
        "status_counts": outputs.get("status_counts", {}),
        "summary_row_count": int(outputs.get("summary_row_count", len(alerts))),
        "scoring_row_count": int(outputs.get("alert_row_count", 0)),
        "reference_review": _reference_review_metrics(
            reference_similarity_metadata,
            reference_candidate_metadata,
            reference_sensitivity_metadata,
            human_review_metadata,
            literature_risk_metadata,
        ),
    }


def _render_dashboard(
    *,
    watchlist: pd.DataFrame,
    market: pd.DataFrame,
    wallets: pd.DataFrame,
    alerts: pd.DataFrame,
    metrics: dict[str, Any],
    figure_path: Path,
    reference_similarity_dashboard_path: Path,
    reference_candidate_dashboard_path: Path,
    reference_sensitivity_dashboard_path: Path,
    human_review_dashboard_path: Path,
    literature_risk_summary_path: Path,
    source_paths: dict[str, Path],
) -> str:
    latest_market = _latest_market_table(watchlist, market, wallets)
    severity_table = _counts_table(metrics.get("severity_counts", {}))
    status_table = _counts_table(metrics.get("status_counts", {}))
    reference_review = metrics.get("reference_review", {})
    reference_review_html = _reference_review_section(
        reference_review=reference_review,
        reference_similarity_dashboard_path=reference_similarity_dashboard_path,
        reference_candidate_dashboard_path=reference_candidate_dashboard_path,
        reference_sensitivity_dashboard_path=reference_sensitivity_dashboard_path,
        human_review_dashboard_path=human_review_dashboard_path,
        literature_risk_summary_path=literature_risk_summary_path,
    )
    summary_rows = _table_rows(
        alerts.head(20),
        (
            "market_id",
            "tier",
            "anomaly_family",
            "metric_name",
            "row_count",
            "alert_count",
            "max_severity",
            "max_robust_z",
            "max_percentile_rank",
        ),
    )
    source_items = "\n".join(
        f"<li><code>{escape(name)}</code>: {escape(str(path))}</li>"
        for name, path in source_paths.items()
    )
    figure_html = (
        f'<img src="{escape(str(figure_path.name))}" alt="Rolling history figure">'
        if figure_path.exists()
        else "<p>Figure not found.</p>"
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Polymarket Politics/Geo Monitor</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 28px; color: #17202a; }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 12px; }}
    .metric {{ border: 1px solid #d7dde5; border-radius: 6px; padding: 12px; background: #f8fafc; }}
    .metric strong {{ display: block; font-size: 22px; margin-top: 4px; }}
    .two-col {{ display: grid; grid-template-columns: repeat(2, minmax(220px, 1fr)); gap: 16px; }}
    .link-grid {{ display: grid; grid-template-columns: repeat(2, minmax(220px, 1fr)); gap: 12px; }}
    .link-card {{ border: 1px solid #d7dde5; border-radius: 6px; padding: 12px; background: #f8fafc; }}
    .link-card a {{ color: #174f78; font-weight: bold; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; font-size: 13px; }}
    th, td {{ border: 1px solid #d7dde5; padding: 7px; text-align: left; vertical-align: top; }}
    th {{ background: #eef2f7; }}
    img {{ max-width: 100%; border: 1px solid #d7dde5; border-radius: 6px; }}
    code {{ background: #f1f5f9; padding: 2px 4px; border-radius: 4px; }}
    .note {{ background: #fff7e6; border: 1px solid #f0d08a; padding: 12px; border-radius: 6px; }}
  </style>
</head>
<body>
  <h1>Polymarket Politics/Geo Monitor</h1>
  <p class="note">Read-only diagnostic view. It describes current bounded monitor outputs and makes no causal, misconduct, or profitability claim.</p>
  <section class="metrics">
    <div class="metric">Markets<strong>{metrics["market_count"]}</strong></div>
    <div class="metric">Closed buckets<strong>{metrics["bucket_count"]}</strong></div>
    <div class="metric">Alerts<strong>{metrics["alert_count"]}</strong></div>
    <div class="metric">Baseline<strong>{escape(str(metrics["baseline_readiness"]))}</strong></div>
  </section>
  <h2>Run Context</h2>
  <table>
    <tbody>
      <tr><th>Latest bucket</th><td>{escape(str(metrics["latest_bucket_utc"]))}</td></tr>
      <tr><th>Baseline settings</th><td>{metrics["baseline_observations"]} observations, minimum {metrics["min_baseline_observations"]}</td></tr>
      <tr><th>Production-like baseline available</th><td>{escape(str(metrics["production_like_baseline_available"]))}</td></tr>
      <tr><th>Scoring rows</th><td>{metrics["scoring_row_count"]}</td></tr>
      <tr><th>Summary rows</th><td>{metrics["summary_row_count"]}</td></tr>
    </tbody>
  </table>
  <section class="two-col">
    <div>
      <h2>Severity Counts</h2>
      {severity_table}
    </div>
    <div>
      <h2>Status Counts</h2>
      {status_table}
    </div>
  </section>
  <h2>Interpretation Limits</h2>
  <p class="note">A zero-alert run means the selected Rule C alert condition did not trigger in this bounded window. It does not prove market efficiency, inefficiency, causality, private information, tradeability, or profitability.</p>
  {reference_review_html}
  <h2>Latest Market State</h2>
  {latest_market}
  <h2>Rolling Figure</h2>
  {figure_html}
  <h2>Alert Summary</h2>
  <table>
    <thead><tr><th>Market</th><th>Tier</th><th>Family</th><th>Metric</th><th>Rows</th><th>Alerts</th><th>Max severity</th><th>Max robust z</th><th>Max percentile</th></tr></thead>
    <tbody>{summary_rows}</tbody>
  </table>
  <h2>Source Artifacts</h2>
  <ul>{source_items}</ul>
</body>
</html>
"""


def _latest_market_table(
    watchlist: pd.DataFrame,
    market: pd.DataFrame,
    wallets: pd.DataFrame,
) -> str:
    latest_bucket = market["bucket_end_utc"].max()
    latest_market = market[market["bucket_end_utc"] == latest_bucket].copy()
    latest_wallets = wallets[wallets["bucket_end_utc"] == wallets["bucket_end_utc"].max()].copy()
    market_groups = latest_market.groupby("market_id")["midpoint"].agg(["min", "max"]).reset_index()
    wallet_groups = latest_wallets.groupby("market_id").agg(
        {"active_wallets": "sum", "trade_count": "sum", "total_observed_amount_usd": "sum"}
    ).reset_index()
    merged = (
        watchlist[["market_id", "question", "category", "subcategory", "status"]]
        .merge(market_groups, on="market_id", how="left")
        .merge(wallet_groups, on="market_id", how="left")
        .fillna("")
    )
    return (
        "<table><thead><tr><th>Question</th><th>Category</th><th>Status</th>"
        "<th>Token midpoint min</th><th>Token midpoint max</th>"
        "<th>Active wallets</th><th>Trades</th><th>Observed amount</th></tr></thead>"
        f"<tbody>{_table_rows(merged, ('question', 'category', 'status', 'min', 'max', 'active_wallets', 'trade_count', 'total_observed_amount_usd'))}</tbody></table>"
    )


def _reference_review_metrics(
    reference_similarity_metadata: dict[str, Any],
    reference_candidate_metadata: dict[str, Any],
    reference_sensitivity_metadata: dict[str, Any],
    human_review_metadata: dict[str, Any],
    literature_risk_metadata: dict[str, Any],
) -> dict[str, Any]:
    similarity_outputs = reference_similarity_metadata.get("outputs", {})
    candidate_outputs = reference_candidate_metadata.get("outputs", {})
    sensitivity_outputs = reference_sensitivity_metadata.get("outputs", {})
    review_outputs = human_review_metadata.get("outputs", {})
    risk_outputs = literature_risk_metadata.get("outputs", {})
    return {
        "reference_case_count": int(similarity_outputs.get("reference_count", 0)),
        "reference_comparison_count": int(similarity_outputs.get("comparison_count", 0)),
        "max_reference_non_self_similarity": float(
            similarity_outputs.get("max_non_self_similarity", 0.0)
        ),
        "monitor_candidate_count": int(candidate_outputs.get("candidate_count", 0)),
        "monitor_candidate_similarity_rows": int(
            candidate_outputs.get("similarity_comparison_rows", 0)
        ),
        "monitor_candidate_max_similarity": float(
            candidate_outputs.get("max_similarity_score", 0.0)
        ),
        "diagnostic_sensitivity_candidate_count": int(
            sensitivity_outputs.get("candidate_count", 0)
        ),
        "diagnostic_sensitivity_shadow_candidate_count": int(
            sensitivity_outputs.get("shadow_candidate_count", 0)
        ),
        "diagnostic_sensitivity_market_only_shadow_count": int(
            sensitivity_outputs.get("market_only_shadow_candidate_count", 0)
        ),
        "diagnostic_sensitivity_similarity_rows": int(
            sensitivity_outputs.get("similarity_comparison_rows", 0)
        ),
        "diagnostic_sensitivity_max_similarity": float(
            sensitivity_outputs.get("max_similarity_score", 0.0)
        ),
        "human_review_candidate_count": int(review_outputs.get("candidate_count", 0)),
        "human_review_high_priority_count": int(
            review_outputs.get("high_priority_count", 0)
        ),
        "literature_risk_candidate_count": int(risk_outputs.get("candidate_count", 0)),
        "literature_risk_flagged_candidate_count": int(
            risk_outputs.get("flagged_candidate_count", 0)
        ),
        "literature_risk_unavailable_feature_count": int(
            risk_outputs.get("unavailable_feature_count", 0)
        ),
        "contains_wallet_addresses": bool(
            similarity_outputs.get("contains_wallet_addresses", False)
            or candidate_outputs.get("contains_wallet_addresses", False)
            or sensitivity_outputs.get("contains_wallet_addresses", False)
            or review_outputs.get("contains_wallet_addresses", False)
            or risk_outputs.get("contains_wallet_addresses", False)
        ),
        "contains_order_instructions": bool(
            similarity_outputs.get("contains_order_instructions", False)
            or candidate_outputs.get("contains_order_instructions", False)
            or sensitivity_outputs.get("contains_order_instructions", False)
            or review_outputs.get("contains_order_instructions", False)
            or risk_outputs.get("contains_order_instructions", False)
        ),
    }


def _reference_review_section(
    *,
    reference_review: dict[str, Any],
    reference_similarity_dashboard_path: Path,
    reference_candidate_dashboard_path: Path,
    reference_sensitivity_dashboard_path: Path,
    human_review_dashboard_path: Path,
    literature_risk_summary_path: Path,
) -> str:
    return f"""
  <h2>Reference Review</h2>
  <p class="note">Reference review links the live monitor to curated wallet-pattern examples. It is a human-review aid, not a probability model or trading signal.</p>
  <section class="metrics">
    <div class="metric">Reference cases<strong>{reference_review.get("reference_case_count", 0)}</strong></div>
    <div class="metric">Reference comparisons<strong>{reference_review.get("reference_comparison_count", 0)}</strong></div>
    <div class="metric">Monitor candidates<strong>{reference_review.get("monitor_candidate_count", 0)}</strong></div>
    <div class="metric">Candidate max score<strong>{float(reference_review.get("monitor_candidate_max_similarity", 0.0)):.2f}</strong></div>
    <div class="metric">Sensitivity candidates<strong>{reference_review.get("diagnostic_sensitivity_candidate_count", 0)}</strong></div>
    <div class="metric">Market-only shadow<strong>{reference_review.get("diagnostic_sensitivity_market_only_shadow_count", 0)}</strong></div>
    <div class="metric">Human review rows<strong>{reference_review.get("human_review_candidate_count", 0)}</strong></div>
    <div class="metric">High priority<strong>{reference_review.get("human_review_high_priority_count", 0)}</strong></div>
    <div class="metric">Literature risk rows<strong>{reference_review.get("literature_risk_candidate_count", 0)}</strong></div>
    <div class="metric">Literature flags<strong>{reference_review.get("literature_risk_flagged_candidate_count", 0)}</strong></div>
  </section>
  <section class="link-grid">
    <div class="link-card">
      <a href="{escape(reference_similarity_dashboard_path.name)}">Open wallet reference similarity</a>
      <p>Compares curated reference profiles such as the Iran/U.S. reported cluster and AdrianCronauer large-flow example.</p>
    </div>
    <div class="link-card">
      <a href="{escape(reference_candidate_dashboard_path.name)}">Open monitor reference candidates</a>
      <p>Shows whether current non-none monitor rows became reference-similarity candidates.</p>
    </div>
    <div class="link-card">
      <a href="{escape(reference_sensitivity_dashboard_path.name)}">Open diagnostic sensitivity candidates</a>
      <p>Shows high-percentile zero-MAD shadow candidates below Rule C for human review.</p>
    </div>
    <div class="link-card">
      <a href="{escape(human_review_dashboard_path.name)}">Open human-review report</a>
      <p>Explains why strict monitor candidates were marked, what evidence exists, and what still needs checking.</p>
    </div>
    <div class="link-card">
      <a href="{escape(literature_risk_summary_path.name)}">Open literature-prior risk score summary</a>
      <p>Shows diagnostic literature-prior wallet and market risk scores plus missing feature counts.</p>
    </div>
  </section>
"""


def _table_rows(frame: pd.DataFrame, columns: Sequence[str]) -> str:
    rows: list[str] = []
    for item in frame.loc[:, list(columns)].to_dict(orient="records"):
        cells = "".join(f"<td>{escape(_format_cell(item[column]))}</td>" for column in columns)
        rows.append(f"<tr>{cells}</tr>")
    return "\n".join(rows)


def _counts_table(counts: object) -> str:
    if not isinstance(counts, dict) or not counts:
        return "<p>No counts reported.</p>"
    rows = "\n".join(
        f"<tr><td>{escape(str(label))}</td><td>{escape(str(value))}</td></tr>"
        for label, value in sorted(counts.items())
    )
    return (
        "<table><thead><tr><th>Label</th><th>Count</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def _format_cell(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _read_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"{label} file not found: {path}")
    frame = pd.read_csv(path)
    if frame.empty:
        raise ValueError(f"{label} file is empty: {path}")
    return frame


def _read_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"{label} file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _read_optional_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} file is not valid JSON: {path}") from exc


def _assert_no_wallet_columns(frames: Sequence[pd.DataFrame]) -> None:
    for frame in frames:
        forbidden = [column for column in frame.columns if "wallet_address" in column.lower()]
        if forbidden:
            raise ValueError(f"dashboard inputs must not contain wallet-address columns: {forbidden}")


def _assert_reference_review_safe(reference_review: dict[str, Any]) -> None:
    if reference_review.get("contains_wallet_addresses", False):
        raise ValueError("reference review metadata reports wallet-address exposure")
    if reference_review.get("contains_order_instructions", False):
        raise ValueError("reference review metadata reports order instructions")


if __name__ == "__main__":
    raise SystemExit(main())
