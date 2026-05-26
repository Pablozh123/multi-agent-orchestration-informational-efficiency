"""Create a compact human-review report for strict monitor candidates."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from math import expm1
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from operations.analysis.monitor_reference_candidates import (
    CANDIDATE_FEATURES_OUTPUT,
    CANDIDATE_SIMILARITY_SUMMARY_OUTPUT,
    MONITOR_ALERT_COLUMNS,
    monitor_candidate_id,
)
from operations.analysis.monitor_literature_risk_scores import (
    RISK_SCORE_SUMMARY_OUTPUT,
)
from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.collectors.polymarket_readonly import (
    LIVE_MARKET_SNAPSHOTS_OUTPUT,
    LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT,
    LIVE_WATCHLIST_OUTPUT,
)
from operations.collectors.polymarket_rolling_history import ROLLING_ALERT_ROWS_OUTPUT


REVIEW_REPORT_OUTPUT = RESULTS_DIR / "monitor_candidate_human_review_report.csv"
REVIEW_DASHBOARD_OUTPUT = RESULTS_DIR / "monitor_candidate_human_review_report.html"
REVIEW_METADATA_OUTPUT = RESULTS_DIR / "monitor_candidate_human_review_report_metadata.json"
MATERIALITY_CONTEXT_OUTPUT = RESULTS_DIR / "monitor_candidate_materiality_context.csv"
REFERENCE_CASES_INPUT = Path("data/reference_cases/wallet_reference_cases.csv")

REPORT_COLUMNS: tuple[str, ...] = (
    "candidate_id",
    "timestamp_utc",
    "market_id",
    "question",
    "category",
    "subcategory",
    "anomaly_row_count",
    "max_severity",
    "anomaly_families",
    "metric_names",
    "max_robust_z",
    "max_percentile_rank",
    "latest_midpoint_min",
    "latest_midpoint_max",
    "active_wallets",
    "trade_count",
    "total_observed_amount_usd",
    "amount_per_wallet",
    "amount_per_trade",
    "materiality_label",
    "reference_amount_usd",
    "reference_amount_ratio",
    "relative_signal_strength",
    "absolute_amount_context",
    "reference_scale_context",
    "coordination_label",
    "coordination_context",
    "insider_risk_review_label",
    "literature_wallet_risk_score",
    "literature_wallet_risk_flag",
    "literature_market_risk_score",
    "literature_market_risk_flag",
    "literature_risk_feature_status",
    "triggered_patterns",
    "best_reference_case_id",
    "best_similarity_score",
    "matched_patterns",
    "plain_language_summary",
    "wallet_amount_explanation",
    "concentration_explanation",
    "reference_overlap_explanation",
    "why_flagged",
    "available_evidence",
    "missing_evidence",
    "review_priority",
    "recommended_next_step",
    "human_review_status",
    "allowed_interpretation",
    "limitation",
    "source_artifacts",
)

MATERIALITY_CONTEXT_COLUMNS: tuple[str, ...] = (
    "candidate_id",
    "timestamp_utc",
    "market_id",
    "question",
    "review_priority",
    "insider_risk_review_label",
    "total_observed_amount_usd",
    "amount_per_wallet",
    "amount_per_trade",
    "materiality_label",
    "reference_amount_usd",
    "reference_amount_ratio",
    "coordination_label",
    "relative_signal_strength",
    "absolute_amount_context",
    "reference_scale_context",
    "coordination_context",
)

SEVERITY_RANK = {"none": 0, "info": 1, "watch": 2, "high": 3, "critical": 4}
REFERENCE_RATIO_UNKNOWN = -1.0
MIN_COORDINATION_WALLETS = 5
MIN_COORDINATION_TRADES = 5


@dataclass(frozen=True)
class HumanReviewReportResult:
    """Summary of generated human-review report artifacts."""

    report_path: Path
    dashboard_path: Path
    metadata_path: Path
    materiality_context_path: Path
    candidate_count: int
    high_priority_count: int
    max_similarity_score: float

    def to_dict(self) -> dict[str, float | int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "report_path": str(self.report_path),
            "dashboard_path": str(self.dashboard_path),
            "metadata_path": str(self.metadata_path),
            "materiality_context_path": str(self.materiality_context_path),
            "candidate_count": self.candidate_count,
            "high_priority_count": self.high_priority_count,
            "max_similarity_score": self.max_similarity_score,
        }


def build_human_review_report(
    *,
    alert_rows: pd.DataFrame,
    watchlist: pd.DataFrame,
    market_snapshots: pd.DataFrame,
    wallet_tier_snapshots: pd.DataFrame,
    similarity_summary: pd.DataFrame,
    candidate_features: pd.DataFrame,
    reference_cases: pd.DataFrame | None = None,
    risk_score_summary: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Return one human-review row per strict monitor candidate."""

    _validate_alert_rows(alert_rows)
    _reject_wallet_address_columns(
        (alert_rows, watchlist, market_snapshots, wallet_tier_snapshots),
    )
    active = alert_rows[alert_rows["severity"].astype(str) != "none"].copy()
    if active.empty:
        return pd.DataFrame(columns=REPORT_COLUMNS)

    watch_lookup = _watchlist_lookup(watchlist)
    market_latest = _latest_market_summary(market_snapshots)
    wallet_latest = _latest_wallet_summary(wallet_tier_snapshots)
    similarity_lookup = _similarity_lookup(similarity_summary)
    feature_lookup = _triggered_feature_lookup(candidate_features)
    reference_lookup = _reference_case_lookup(
        reference_cases if reference_cases is not None else pd.DataFrame()
    )
    risk_lookup = _risk_score_lookup(
        risk_score_summary if risk_score_summary is not None else pd.DataFrame()
    )

    report_rows: list[dict[str, object]] = []
    for (timestamp_utc, market_id), group in active.groupby(
        ["timestamp_utc", "market_id"],
        sort=True,
    ):
        candidate_id = monitor_candidate_id(timestamp_utc, market_id)
        watch = watch_lookup.get(str(market_id), {})
        market = market_latest.get(str(market_id), {})
        wallet = wallet_latest.get(str(market_id), {})
        similarity = similarity_lookup.get(candidate_id, {})
        triggered_patterns = feature_lookup.get(candidate_id, [])
        risk_score = risk_lookup.get(candidate_id, {})
        row = _report_row(
            candidate_id=candidate_id,
            timestamp_utc=str(timestamp_utc),
            market_id=str(market_id),
            group=group,
            watch=watch,
            market=market,
            wallet=wallet,
            similarity=similarity,
            triggered_patterns=triggered_patterns,
            reference_cases=reference_lookup,
            risk_score=risk_score,
        )
        report_rows.append(row)
    return pd.DataFrame(report_rows, columns=REPORT_COLUMNS)


def generate_monitor_candidate_human_review_report(
    *,
    alert_rows_path: Path = ROLLING_ALERT_ROWS_OUTPUT,
    watchlist_path: Path = LIVE_WATCHLIST_OUTPUT,
    market_snapshots_path: Path = LIVE_MARKET_SNAPSHOTS_OUTPUT,
    wallet_tier_snapshots_path: Path = LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT,
    similarity_summary_path: Path = CANDIDATE_SIMILARITY_SUMMARY_OUTPUT,
    candidate_features_path: Path = CANDIDATE_FEATURES_OUTPUT,
    reference_cases_path: Path = REFERENCE_CASES_INPUT,
    risk_score_summary_path: Path = RISK_SCORE_SUMMARY_OUTPUT,
    report_path: Path = REVIEW_REPORT_OUTPUT,
    dashboard_path: Path = REVIEW_DASHBOARD_OUTPUT,
    metadata_path: Path = REVIEW_METADATA_OUTPUT,
    materiality_context_path: Path = MATERIALITY_CONTEXT_OUTPUT,
) -> HumanReviewReportResult:
    """Write CSV, HTML, and metadata for strict monitor candidate review."""

    alert_rows = _read_csv(alert_rows_path, "alert rows")
    watchlist = _read_csv(watchlist_path, "watchlist")
    market_snapshots = _read_csv(market_snapshots_path, "market snapshots")
    wallet_tier_snapshots = _read_csv(
        wallet_tier_snapshots_path,
        "wallet-tier snapshots",
    )
    similarity_summary = _read_optional_csv(similarity_summary_path)
    candidate_features = _read_optional_csv(candidate_features_path)
    reference_cases = _read_optional_csv(reference_cases_path)
    risk_score_summary = _read_optional_csv(risk_score_summary_path)

    report = build_human_review_report(
        alert_rows=alert_rows,
        watchlist=watchlist,
        market_snapshots=market_snapshots,
        wallet_tier_snapshots=wallet_tier_snapshots,
        similarity_summary=similarity_summary,
        candidate_features=candidate_features,
        reference_cases=reference_cases,
        risk_score_summary=risk_score_summary,
    )
    _write_csv(report_path, report)
    _write_csv(materiality_context_path, _materiality_context(report))
    _write_dashboard(report, dashboard_path)
    metadata = _metadata(
        report=report,
        alert_rows=alert_rows,
        alert_rows_path=alert_rows_path,
        watchlist_path=watchlist_path,
        market_snapshots_path=market_snapshots_path,
        wallet_tier_snapshots_path=wallet_tier_snapshots_path,
        similarity_summary_path=similarity_summary_path,
        candidate_features_path=candidate_features_path,
        reference_cases_path=reference_cases_path,
        risk_score_summary_path=risk_score_summary_path,
        report_path=report_path,
        dashboard_path=dashboard_path,
        materiality_context_path=materiality_context_path,
    )
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return HumanReviewReportResult(
        report_path=report_path,
        dashboard_path=dashboard_path,
        metadata_path=metadata_path,
        materiality_context_path=materiality_context_path,
        candidate_count=int(len(report)),
        high_priority_count=int((report["review_priority"] == "high").sum())
        if not report.empty
        else 0,
        max_similarity_score=_max_report_similarity(report),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--alert-rows", type=Path, default=ROLLING_ALERT_ROWS_OUTPUT)
    parser.add_argument("--watchlist", type=Path, default=LIVE_WATCHLIST_OUTPUT)
    parser.add_argument("--market-snapshots", type=Path, default=LIVE_MARKET_SNAPSHOTS_OUTPUT)
    parser.add_argument(
        "--wallet-tier-snapshots",
        type=Path,
        default=LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT,
    )
    parser.add_argument(
        "--similarity-summary",
        type=Path,
        default=CANDIDATE_SIMILARITY_SUMMARY_OUTPUT,
    )
    parser.add_argument("--candidate-features", type=Path, default=CANDIDATE_FEATURES_OUTPUT)
    parser.add_argument("--reference-cases", type=Path, default=REFERENCE_CASES_INPUT)
    parser.add_argument(
        "--risk-score-summary",
        type=Path,
        default=RISK_SCORE_SUMMARY_OUTPUT,
    )
    parser.add_argument("--report-output", type=Path, default=REVIEW_REPORT_OUTPUT)
    parser.add_argument("--dashboard-output", type=Path, default=REVIEW_DASHBOARD_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=REVIEW_METADATA_OUTPUT)
    parser.add_argument(
        "--materiality-context-output",
        type=Path,
        default=MATERIALITY_CONTEXT_OUTPUT,
    )
    args = parser.parse_args(argv)

    try:
        result = generate_monitor_candidate_human_review_report(
            alert_rows_path=args.alert_rows,
            watchlist_path=args.watchlist,
            market_snapshots_path=args.market_snapshots,
            wallet_tier_snapshots_path=args.wallet_tier_snapshots,
            similarity_summary_path=args.similarity_summary,
            candidate_features_path=args.candidate_features,
            reference_cases_path=args.reference_cases,
            risk_score_summary_path=args.risk_score_summary,
            report_path=args.report_output,
            dashboard_path=args.dashboard_output,
            metadata_path=args.metadata_output,
            materiality_context_path=args.materiality_context_output,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _report_row(
    *,
    candidate_id: str,
    timestamp_utc: str,
    market_id: str,
    group: pd.DataFrame,
    watch: dict[str, object],
    market: dict[str, object],
    wallet: dict[str, object],
    similarity: dict[str, object],
    triggered_patterns: Sequence[str],
    reference_cases: dict[str, dict[str, object]],
    risk_score: dict[str, object],
) -> dict[str, object]:
    families = sorted(set(group["anomaly_family"].astype(str)))
    metrics = sorted(set(group["metric_name"].astype(str)))
    max_severity = _max_severity(group["severity"])
    max_robust_z = _max_numeric(group["robust_z"])
    max_percentile = _max_numeric(group["rolling_percentile_rank"])
    best_similarity = _float_or_zero(similarity.get("best_similarity_score", 0.0))
    active_wallets = int(_float_or_zero(wallet.get("active_wallets", 0)))
    trade_count = int(_float_or_zero(wallet.get("trade_count", 0)))
    total_amount = _float_or_zero(wallet.get("total_observed_amount_usd", 0.0))
    amount_per_wallet = _safe_divide(total_amount, active_wallets)
    amount_per_trade = _safe_divide(total_amount, trade_count)
    best_reference_id = str(similarity.get("best_reference_case_id", ""))
    reference_amount = _float_or_zero(
        reference_cases.get(best_reference_id, {}).get("amount_usd", 0.0)
    )
    reference_amount_ratio = _reference_amount_ratio(total_amount, reference_amount)
    materiality_label = _materiality_label(reference_amount_ratio, reference_amount)
    coordination_label = _coordination_label(
        active_wallets=active_wallets,
        trade_count=trade_count,
        materiality_label=materiality_label,
    )
    priority = _review_priority(
        max_severity=max_severity,
        best_similarity=best_similarity,
        patterns=triggered_patterns,
    )
    insider_risk_label = _insider_risk_review_label(
        priority=priority,
        materiality_label=materiality_label,
        coordination_label=coordination_label,
    )
    return {
        "candidate_id": candidate_id,
        "timestamp_utc": timestamp_utc,
        "market_id": market_id,
        "question": watch.get("question", ""),
        "category": watch.get("category", ""),
        "subcategory": watch.get("subcategory", ""),
        "anomaly_row_count": int(len(group)),
        "max_severity": max_severity,
        "anomaly_families": ",".join(families),
        "metric_names": ",".join(metrics),
        "max_robust_z": round(max_robust_z, 6),
        "max_percentile_rank": round(max_percentile, 6),
        "latest_midpoint_min": _format_number(market.get("latest_midpoint_min", "")),
        "latest_midpoint_max": _format_number(market.get("latest_midpoint_max", "")),
        "active_wallets": active_wallets,
        "trade_count": trade_count,
        "total_observed_amount_usd": round(total_amount, 6),
        "amount_per_wallet": round(amount_per_wallet, 6),
        "amount_per_trade": round(amount_per_trade, 6),
        "materiality_label": materiality_label,
        "reference_amount_usd": round(reference_amount, 6),
        "reference_amount_ratio": round(
            reference_amount_ratio if reference_amount_ratio >= 0 else 0.0,
            9,
        ),
        "relative_signal_strength": _relative_signal_strength(group),
        "absolute_amount_context": _absolute_amount_context(
            total_amount=total_amount,
            active_wallets=active_wallets,
            trade_count=trade_count,
            amount_per_wallet=amount_per_wallet,
            amount_per_trade=amount_per_trade,
        ),
        "reference_scale_context": _reference_scale_context(
            total_amount=total_amount,
            reference_id=best_reference_id,
            reference_amount=reference_amount,
            reference_amount_ratio=reference_amount_ratio,
            materiality_label=materiality_label,
        ),
        "coordination_label": coordination_label,
        "coordination_context": _coordination_context(
            active_wallets=active_wallets,
            trade_count=trade_count,
            total_amount=total_amount,
            amount_per_wallet=amount_per_wallet,
            amount_per_trade=amount_per_trade,
            coordination_label=coordination_label,
        ),
        "insider_risk_review_label": insider_risk_label,
        "literature_wallet_risk_score": round(
            _float_or_zero(risk_score.get("literature_wallet_risk_score", 0.0)),
            6,
        ),
        "literature_wallet_risk_flag": str(
            risk_score.get("literature_wallet_risk_flag", "not_available")
        ),
        "literature_market_risk_score": round(
            _float_or_zero(risk_score.get("literature_market_risk_score", 0.0)),
            6,
        ),
        "literature_market_risk_flag": str(
            risk_score.get("literature_market_risk_flag", "not_available")
        ),
        "literature_risk_feature_status": str(
            risk_score.get("feature_status_summary", "not_available")
        ),
        "triggered_patterns": ",".join(sorted(triggered_patterns)),
        "best_reference_case_id": best_reference_id,
        "best_similarity_score": round(best_similarity, 6),
        "matched_patterns": similarity.get("matched_patterns", ""),
        "plain_language_summary": _plain_language_summary(
            group=group,
            max_severity=max_severity,
            triggered_patterns=triggered_patterns,
            total_amount=total_amount,
            materiality_label=materiality_label,
            insider_risk_label=insider_risk_label,
        ),
        "wallet_amount_explanation": _wallet_amount_explanation(group),
        "concentration_explanation": _concentration_explanation(group),
        "reference_overlap_explanation": _reference_overlap_explanation(
            similarity=similarity,
            triggered_patterns=triggered_patterns,
            reference_amount=reference_amount,
            reference_amount_ratio=reference_amount_ratio,
        ),
        "why_flagged": _why_flagged(group, triggered_patterns),
        "available_evidence": _available_evidence(group, wallet, market, similarity),
        "missing_evidence": _missing_evidence(group, triggered_patterns),
        "review_priority": priority,
        "recommended_next_step": _recommended_next_step(priority, triggered_patterns),
        "human_review_status": "needs_human_review",
        "allowed_interpretation": (
            "Insider-risk review candidate for human review only; not proof, "
            "not a computed insider label, not a causal claim, and not a "
            "trading signal."
        ),
        "limitation": (
            "Uses aggregate local monitor artifacts only and contains no "
            "wallet addresses, order instructions, PnL, or claim of misconduct."
        ),
        "source_artifacts": (
            "monitor_v2_polymarket_rolling_alert_rows.csv;"
            "monitor_reference_candidate_similarity_summary.csv;"
            "monitor_v2_polymarket_live_watchlist.csv"
        ),
    }


def _why_flagged(group: pd.DataFrame, triggered_patterns: Sequence[str]) -> str:
    pieces: list[str] = []
    for family in sorted(set(group["anomaly_family"].astype(str))):
        metrics = sorted(
            set(group[group["anomaly_family"] == family]["metric_name"].astype(str))
        )
        severity = _max_severity(group[group["anomaly_family"] == family]["severity"])
        pieces.append(f"{family} triggered {severity} on {','.join(metrics)}")
    if triggered_patterns:
        pieces.append(f"reference-pattern labels: {','.join(sorted(triggered_patterns))}")
    return "; ".join(pieces)


def _plain_language_summary(
    *,
    group: pd.DataFrame,
    max_severity: str,
    triggered_patterns: Sequence[str],
    total_amount: float,
    materiality_label: str,
    insider_risk_label: str,
) -> str:
    families = set(group["anomaly_family"].astype(str))
    if max_severity == "high" and {
        "wallet_tier_activity",
        "concentration",
    }.issubset(families):
        return (
            f"{insider_risk_label}: wallet amount and concentration were both "
            f"unusual in the same 5-minute bucket. The observed aggregate "
            f"amount was about USD {total_amount:.2f}. This is large relative "
            "to the short rolling baseline, but its reference-scale context is "
            f"`{materiality_label}` and must be reviewed manually."
        )
    if "concentration" in families:
        return (
            "Marked because activity was concentrated in the current bucket. "
            "This can happen in thin markets, so repetition and market-page "
            "context matter."
        )
    if "active_wallet_activity" in families:
        return (
            "Marked because the active-wallet count was above its local "
            "baseline. This is a weak cue unless it repeats or combines with "
            "amount or concentration evidence."
        )
    if triggered_patterns:
        return "Marked because neutral reference-pattern labels were triggered."
    return "Marked by the strict monitor rule and requires human review."


def _wallet_amount_explanation(group: pd.DataFrame) -> str:
    amount_rows = group[
        (group["anomaly_family"].astype(str) == "wallet_tier_activity")
        & (group["metric_name"].astype(str) == "log1p_total_observed_amount_usd")
    ]
    if amount_rows.empty:
        return "No wallet-amount metric triggered for this candidate."
    row = amount_rows.sort_values(
        ["severity", "rolling_percentile_rank"],
        ascending=[False, False],
    ).iloc[0]
    observed = _amount_from_log_metric(row.get("observed_value", 0.0))
    baseline = _amount_from_log_metric(row.get("rolling_median", 0.0))
    percentile = _float_or_zero(row.get("rolling_percentile_rank", 0.0))
    robust_z = _float_or_zero(row.get("robust_z", 0.0))
    severity = str(row.get("severity", ""))
    return (
        f"Wallet amount: observed about USD {observed:.2f}; rolling baseline "
        f"median about USD {baseline:.2f}; percentile {percentile:.2f}; "
        f"robust z {robust_z:.2f}; severity {severity}. The very high robust "
        "z can be inflated when the recent baseline is tiny, so absolute size "
        "must be checked manually."
    )


def _concentration_explanation(group: pd.DataFrame) -> str:
    concentration = group[group["anomaly_family"].astype(str) == "concentration"]
    if concentration.empty:
        return "No concentration metric triggered for this candidate."
    parts: list[str] = []
    for _, row in concentration.sort_values("metric_name").iterrows():
        metric = str(row.get("metric_name", ""))
        observed = _float_or_zero(row.get("observed_value", 0.0))
        baseline = _float_or_zero(row.get("rolling_median", 0.0))
        percentile = _float_or_zero(row.get("rolling_percentile_rank", 0.0))
        severity = str(row.get("severity", ""))
        parts.append(
            f"{metric}: observed {observed:.2f}, baseline median {baseline:.2f}, "
            f"percentile {percentile:.2f}, severity {severity}"
        )
    return "; ".join(parts)


def _reference_overlap_explanation(
    *,
    similarity: dict[str, object],
    triggered_patterns: Sequence[str],
    reference_amount: float,
    reference_amount_ratio: float,
) -> str:
    score = _float_or_zero(similarity.get("best_similarity_score", 0.0))
    reference = str(similarity.get("best_reference_case_id", ""))
    matched = str(similarity.get("matched_patterns", "")).strip()
    if score == 0:
        return (
            "Reference overlap 0.0 means this candidate does not share the "
            "triggered neutral labels of the current reference profiles."
        )
    matched_count = len([value for value in matched.split(",") if value])
    amount_context = ""
    if reference_amount > 0 and reference_amount_ratio >= 0:
        amount_context = (
            f" The observed amount is {reference_amount_ratio:.3%} of the "
            f"reference amount USD {reference_amount:.2f}."
        )
    return (
        f"Reference overlap {score:.1f} against {reference} means the candidate "
        f"shares {matched_count} neutral pattern label(s): {matched}. It does "
        "not mean same wallet, same amount, same event, same outcome, or "
        f"misconduct; it is only a review shortcut.{amount_context}"
    )


def _available_evidence(
    group: pd.DataFrame,
    wallet: dict[str, object],
    market: dict[str, object],
    similarity: dict[str, object],
) -> str:
    return (
        f"{len(group)} non-none monitor rows; "
        f"active_wallets={int(_float_or_zero(wallet.get('active_wallets', 0)))}; "
        f"trade_count={int(_float_or_zero(wallet.get('trade_count', 0)))}; "
        f"observed_amount_usd={_float_or_zero(wallet.get('total_observed_amount_usd', 0.0)):.2f}; "
        f"midpoint_range={_format_number(market.get('latest_midpoint_min', ''))}-"
        f"{_format_number(market.get('latest_midpoint_max', ''))}; "
        f"reference_similarity={_float_or_zero(similarity.get('best_similarity_score', 0.0)):.2f}"
    )


def _relative_signal_strength(group: pd.DataFrame) -> str:
    families = ",".join(sorted(set(group["anomaly_family"].astype(str))))
    metrics = ",".join(sorted(set(group["metric_name"].astype(str))))
    return (
        f"max_severity={_max_severity(group['severity'])}; "
        f"max_robust_z={_max_numeric(group['robust_z']):.2f}; "
        f"max_percentile={_max_numeric(group['rolling_percentile_rank']):.2f}; "
        f"families={families}; metrics={metrics}"
    )


def _absolute_amount_context(
    *,
    total_amount: float,
    active_wallets: int,
    trade_count: int,
    amount_per_wallet: float,
    amount_per_trade: float,
) -> str:
    return (
        f"observed_amount_usd={total_amount:.2f}; "
        f"active_wallets={active_wallets}; trade_count={trade_count}; "
        f"amount_per_wallet_usd={amount_per_wallet:.2f}; "
        f"amount_per_trade_usd={amount_per_trade:.2f}"
    )


def _reference_scale_context(
    *,
    total_amount: float,
    reference_id: str,
    reference_amount: float,
    reference_amount_ratio: float,
    materiality_label: str,
) -> str:
    if reference_amount <= 0 or reference_amount_ratio < 0:
        return (
            f"observed_amount_usd={total_amount:.2f}; no comparable reference "
            "amount is available for the best reference case."
        )
    return (
        f"observed_amount_usd={total_amount:.2f}; reference_case={reference_id}; "
        f"reference_amount_usd={reference_amount:.2f}; "
        f"reference_amount_ratio={reference_amount_ratio:.6f}; "
        f"materiality_label={materiality_label}"
    )


def _coordination_context(
    *,
    active_wallets: int,
    trade_count: int,
    total_amount: float,
    amount_per_wallet: float,
    amount_per_trade: float,
    coordination_label: str,
) -> str:
    return (
        f"coordination_label={coordination_label}; active_wallets={active_wallets}; "
        f"trade_count={trade_count}; total_amount_usd={total_amount:.2f}; "
        f"amount_per_wallet_usd={amount_per_wallet:.2f}; "
        f"amount_per_trade_usd={amount_per_trade:.2f}"
    )


def _reference_amount_ratio(amount: float, reference_amount: float) -> float:
    if reference_amount <= 0:
        return REFERENCE_RATIO_UNKNOWN
    return max(0.0, amount / reference_amount)


def _materiality_label(reference_amount_ratio: float, reference_amount: float) -> str:
    if reference_amount <= 0 or reference_amount_ratio < 0:
        return "reference_scale_unknown"
    if reference_amount_ratio >= 1:
        return "at_or_above_reference_amount"
    if reference_amount_ratio >= 0.10:
        return "same_order_below_reference"
    if reference_amount_ratio >= 0.01:
        return "one_to_ten_percent_of_reference"
    return "below_one_percent_of_reference"


def _coordination_label(
    *,
    active_wallets: int,
    trade_count: int,
    materiality_label: str,
) -> str:
    if active_wallets <= 1 and trade_count <= 1:
        return "single_wallet_single_trade"
    if (
        active_wallets >= MIN_COORDINATION_WALLETS
        and trade_count >= MIN_COORDINATION_TRADES
        and materiality_label
        in {"below_one_percent_of_reference", "reference_scale_unknown"}
    ):
        return "coordinated_small_flow_candidate"
    if active_wallets >= MIN_COORDINATION_WALLETS or trade_count >= MIN_COORDINATION_TRADES:
        return "multi_wallet_or_trade_review_candidate"
    return "few_wallet_or_trade_context"


def _insider_risk_review_label(
    *,
    priority: str,
    materiality_label: str,
    coordination_label: str,
) -> str:
    if coordination_label == "coordinated_small_flow_candidate":
        return "insider-risk review candidate: coordinated small-flow hypothesis"
    if priority == "high" and materiality_label in {
        "at_or_above_reference_amount",
        "same_order_below_reference",
        "one_to_ten_percent_of_reference",
    }:
        return "insider-risk review candidate: material flow hypothesis"
    if priority == "high":
        return "insider-risk review candidate: relative anomaly, low materiality"
    return "insider-risk watch cue: weak or incomplete evidence"


def _missing_evidence(group: pd.DataFrame, triggered_patterns: Sequence[str]) -> str:
    missing = [
        "manual Polymarket market page review",
        "independent news/event timestamp check",
        "repeat-bucket confirmation",
        "directional position or exit data",
    ]
    if "large_trade_flow" in triggered_patterns:
        missing.append("trade-size context against longer rolling volume")
    if group["event_candidate_id"].fillna("").astype(str).str.strip().eq("").all():
        missing.append("reviewed event candidate mapping")
    return "; ".join(missing)


def _recommended_next_step(priority: str, triggered_patterns: Sequence[str]) -> str:
    if priority == "high":
        return (
            "Open the market page, verify current context, and collect another "
            "bounded bucket before any thesis-facing use."
        )
    if triggered_patterns:
        return "Check whether the same pattern repeats in the next bounded bucket."
    return "Low-context cue: keep in registry and review only if repeated."


def _review_priority(
    *,
    max_severity: str,
    best_similarity: float,
    patterns: Sequence[str],
) -> str:
    if max_severity in {"high", "critical"} and (
        best_similarity >= 0.75 or len(patterns) >= 2
    ):
        return "high"
    if max_severity == "watch" or patterns:
        return "medium"
    return "low"


def _watchlist_lookup(watchlist: pd.DataFrame) -> dict[str, dict[str, object]]:
    _require_columns(watchlist, ("market_id", "question", "category", "subcategory"), "watchlist")
    return {
        str(row["market_id"]): row
        for row in watchlist[
            ["market_id", "question", "category", "subcategory"]
        ].to_dict(orient="records")
    }


def _latest_market_summary(frame: pd.DataFrame) -> dict[str, dict[str, object]]:
    _require_columns(frame, ("bucket_end_utc", "market_id", "midpoint"), "market snapshots")
    latest_bucket = str(frame["bucket_end_utc"].max())
    latest = frame[frame["bucket_end_utc"].astype(str) == latest_bucket].copy()
    grouped = latest.groupby("market_id")["midpoint"].agg(["min", "max"]).reset_index()
    return {
        str(row["market_id"]): {
            "latest_midpoint_min": row["min"],
            "latest_midpoint_max": row["max"],
        }
        for row in grouped.to_dict(orient="records")
    }


def _latest_wallet_summary(frame: pd.DataFrame) -> dict[str, dict[str, object]]:
    _require_columns(
        frame,
        ("bucket_end_utc", "market_id", "active_wallets", "trade_count", "total_observed_amount_usd"),
        "wallet-tier snapshots",
    )
    latest_bucket = str(frame["bucket_end_utc"].max())
    latest = frame[frame["bucket_end_utc"].astype(str) == latest_bucket].copy()
    grouped = (
        latest.groupby("market_id")
        .agg(
            active_wallets=("active_wallets", "sum"),
            trade_count=("trade_count", "sum"),
            total_observed_amount_usd=("total_observed_amount_usd", "sum"),
        )
        .reset_index()
    )
    return {
        str(row["market_id"]): row
        for row in grouped.to_dict(orient="records")
    }


def _similarity_lookup(frame: pd.DataFrame) -> dict[str, dict[str, object]]:
    if frame.empty:
        return {}
    _require_columns(
        frame,
        (
            "candidate_id",
            "best_reference_case_id",
            "best_similarity_score",
            "matched_patterns",
        ),
        "similarity summary",
    )
    return {
        str(row["candidate_id"]): row
        for row in frame.to_dict(orient="records")
    }


def _triggered_feature_lookup(frame: pd.DataFrame) -> dict[str, list[str]]:
    if frame.empty:
        return {}
    _require_columns(
        frame,
        ("case_id", "pattern_label", "feature_status"),
        "candidate features",
    )
    triggered = frame[frame["feature_status"].astype(str) == "triggered"].copy()
    return {
        str(case_id): sorted(group["pattern_label"].astype(str).tolist())
        for case_id, group in triggered.groupby("case_id", sort=True)
    }


def _reference_case_lookup(frame: pd.DataFrame) -> dict[str, dict[str, object]]:
    if frame.empty:
        return {}
    _require_columns(frame, ("case_id", "amount_usd"), "reference cases")
    optional_columns = [column for column in ("handle", "case_type") if column in frame.columns]
    slim = frame[["case_id", "amount_usd", *optional_columns]].copy()
    slim["amount_usd"] = pd.to_numeric(slim["amount_usd"], errors="coerce").fillna(0.0)
    return {
        str(row["case_id"]): row
        for row in slim.to_dict(orient="records")
    }


def _materiality_context(report: pd.DataFrame) -> pd.DataFrame:
    if report.empty:
        return pd.DataFrame(columns=MATERIALITY_CONTEXT_COLUMNS)
    return report.loc[:, list(MATERIALITY_CONTEXT_COLUMNS)].copy()


def _write_dashboard(report: pd.DataFrame, dashboard_path: Path) -> None:
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    if report.empty:
        body = "<p>No strict monitor candidates require review.</p>"
        candidate_count = 0
        high_priority = 0
    else:
        body = _candidate_cards(report)
        candidate_count = len(report)
        high_priority = int((report["review_priority"] == "high").sum())
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Monitor Candidate Human Review</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 28px; color: #17202a; }}
    .metrics {{ display: grid; grid-template-columns: repeat(3, minmax(130px, 1fr)); gap: 12px; }}
    .metric {{ border: 1px solid #d7dde5; border-radius: 6px; padding: 12px; background: #f8fafc; }}
    .metric strong {{ display: block; font-size: 22px; margin-top: 4px; }}
    .candidate {{ border: 1px solid #cfd8e3; border-radius: 8px; padding: 16px; margin: 18px 0; background: #ffffff; }}
    .candidate h3 {{ margin: 0 0 8px; }}
    .pill {{ display: inline-block; padding: 3px 8px; border-radius: 999px; background: #eef2f7; margin-right: 6px; font-size: 12px; }}
    .pill.high {{ background: #ffe7d6; }}
    .pill.medium {{ background: #fff7cc; }}
    .pill.low {{ background: #e9f7ef; }}
    .explain-grid {{ display: grid; grid-template-columns: repeat(2, minmax(240px, 1fr)); gap: 12px; }}
    .box {{ border: 1px solid #e1e7ef; border-radius: 6px; padding: 12px; background: #fbfcfe; }}
    .bar {{ height: 10px; border-radius: 999px; background: #e6ebf2; overflow: hidden; margin-top: 6px; }}
    .bar span {{ display: block; height: 100%; background: #366f9f; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; font-size: 13px; }}
    th, td {{ border: 1px solid #d7dde5; padding: 7px; text-align: left; vertical-align: top; }}
    th {{ background: #eef2f7; }}
    .note {{ background: #fff7e6; border: 1px solid #f0d08a; padding: 12px; border-radius: 6px; }}
  </style>
</head>
<body>
  <h1>Insider-Risk Candidate Human Review</h1>
  <p class="note">Strict monitor candidates are insider-risk review cues only. This report contains no wallet addresses, order instructions, PnL, computed insider label, or misconduct claim.</p>
  <section class="metrics">
    <div class="metric">Candidates<strong>{candidate_count}</strong></div>
    <div class="metric">High priority<strong>{high_priority}</strong></div>
    <div class="metric">Status<strong>needs review</strong></div>
  </section>
  <h2>Review Cards</h2>
  {body}
</body>
</html>
"""
    dashboard_path.write_text(html, encoding="utf-8")


def _metadata(
    *,
    report: pd.DataFrame,
    alert_rows: pd.DataFrame,
    alert_rows_path: Path,
    watchlist_path: Path,
    market_snapshots_path: Path,
    wallet_tier_snapshots_path: Path,
    similarity_summary_path: Path,
    candidate_features_path: Path,
    reference_cases_path: Path,
    risk_score_summary_path: Path,
    report_path: Path,
    dashboard_path: Path,
    materiality_context_path: Path,
) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "monitor_candidate_human_review_report",
            "candidate_filter": "severity != none grouped by timestamp_utc and market_id",
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
            "watchlist_path": str(watchlist_path),
            "market_snapshots_path": str(market_snapshots_path),
            "wallet_tier_snapshots_path": str(wallet_tier_snapshots_path),
            "similarity_summary_path": str(similarity_summary_path),
            "candidate_features_path": str(candidate_features_path),
            "reference_cases_path": str(reference_cases_path),
            "risk_score_summary_path": str(risk_score_summary_path),
            "source_alert_rows": int(len(alert_rows)),
        },
        "outputs": {
            "report_path": str(report_path),
            "dashboard_path": str(dashboard_path),
            "materiality_context_path": str(materiality_context_path),
            "candidate_count": int(len(report)),
            "high_priority_count": int((report["review_priority"] == "high").sum())
            if not report.empty
            else 0,
            "max_similarity_score": _max_report_similarity(report),
            "max_literature_wallet_risk_score": _max_report_numeric(
                report,
                "literature_wallet_risk_score",
            ),
            "max_literature_market_risk_score": _max_report_numeric(
                report,
                "literature_market_risk_score",
            ),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
            "contains_computed_insider_label": False,
        },
        "limitations": {
            "human_review_required": True,
            "not_a_probability_model": True,
            "not_a_causal_test": True,
            "not_a_trade_or_profitability_signal": True,
            "not_a_misconduct_finding": True,
            "not_a_computed_insider_label": True,
            "aggregate_monitor_fields_only": True,
        },
    }


def _candidate_cards(report: pd.DataFrame) -> str:
    cards: list[str] = []
    sorted_report = report.sort_values(
        ["review_priority", "max_severity", "best_similarity_score"],
        ascending=[True, False, False],
    )
    priority_order = {"high": 0, "medium": 1, "low": 2}
    sorted_report = sorted_report.assign(
        _priority_order=sorted_report["review_priority"].map(priority_order).fillna(9)
    ).sort_values(["_priority_order", "best_similarity_score"], ascending=[True, False])
    for item in sorted_report.drop(columns=["_priority_order"]).to_dict(orient="records"):
        priority = str(item["review_priority"])
        percentile = _float_or_zero(item.get("max_percentile_rank", 0.0))
        similarity = _float_or_zero(item.get("best_similarity_score", 0.0))
        amount = _float_or_zero(item.get("total_observed_amount_usd", 0.0))
        wallet_risk = _float_or_zero(item.get("literature_wallet_risk_score", 0.0))
        market_risk = _float_or_zero(item.get("literature_market_risk_score", 0.0))
        cards.append(
            f"""
  <article class="candidate">
    <h3>{escape(str(item["question"]))}</h3>
    <p>
      <span class="pill {escape(priority)}">priority: {escape(priority)}</span>
      <span class="pill">severity: {escape(str(item["max_severity"]))}</span>
      <span class="pill">rows: {escape(str(item["anomaly_row_count"]))}</span>
    </p>
    <p><strong>In plain words:</strong> {escape(str(item["plain_language_summary"]))}</p>
    <section class="explain-grid">
      <div class="box">
        <strong>Wallet amount</strong>
        <p>{escape(str(item["wallet_amount_explanation"]))}</p>
      </div>
      <div class="box">
        <strong>Concentration</strong>
        <p>{escape(str(item["concentration_explanation"]))}</p>
      </div>
      <div class="box">
        <strong>Reference overlap</strong>
        <p>{escape(str(item["reference_overlap_explanation"]))}</p>
      </div>
      <div class="box">
        <strong>Reference scale</strong>
        <p>{escape(str(item["reference_scale_context"]))}</p>
      </div>
      <div class="box">
        <strong>Coordination</strong>
        <p>{escape(str(item["coordination_context"]))}</p>
      </div>
      <div class="box">
        <strong>Literature-prior risk</strong>
        <p>Wallet score: {wallet_risk:.2f}
        ({escape(str(item.get("literature_wallet_risk_flag", "not_available")))})<br>
        Market score: {market_risk:.2f}
        ({escape(str(item.get("literature_market_risk_flag", "not_available")))})<br>
        Feature status: {escape(str(item.get("literature_risk_feature_status", "not_available")))}</p>
      </div>
      <div class="box">
        <strong>Quick numbers</strong>
        <p>Observed amount: USD {amount:.2f}<br>
        Active wallets: {escape(str(item["active_wallets"]))}<br>
        Trades: {escape(str(item["trade_count"]))}<br>
        Amount per wallet: USD {_float_or_zero(item.get("amount_per_wallet", 0.0)):.2f}<br>
        Amount per trade: USD {_float_or_zero(item.get("amount_per_trade", 0.0)):.2f}<br>
        Materiality: {escape(str(item["materiality_label"]))}<br>
        Review label: {escape(str(item["insider_risk_review_label"]))}<br>
        Max percentile: {percentile:.2f}<br>
        Reference score: {similarity:.2f}</p>
        <div class="bar"><span style="width:{_percent_width(percentile)}%"></span></div>
      </div>
    </section>
    <p><strong>Why flagged:</strong> {escape(str(item["why_flagged"]))}</p>
    <p><strong>Still missing:</strong> {escape(str(item["missing_evidence"]))}</p>
    <p><strong>Next step:</strong> {escape(str(item["recommended_next_step"]))}</p>
  </article>
"""
        )
    return "\n".join(cards)


def _percent_width(value: float) -> int:
    return max(0, min(100, int(round(value * 100))))


def _max_report_similarity(report: pd.DataFrame) -> float:
    if report.empty:
        return 0.0
    return float(
        pd.to_numeric(report["best_similarity_score"], errors="coerce").fillna(0).max()
    )


def _max_report_numeric(report: pd.DataFrame, column: str) -> float:
    if report.empty or column not in report.columns:
        return 0.0
    return float(pd.to_numeric(report[column], errors="coerce").fillna(0).max())


def _risk_score_lookup(frame: pd.DataFrame) -> dict[str, dict[str, object]]:
    if frame.empty:
        return {}
    _require_columns(
        frame,
        (
            "candidate_id",
            "literature_wallet_risk_score",
            "literature_wallet_risk_flag",
            "literature_market_risk_score",
            "literature_market_risk_flag",
            "feature_status_summary",
        ),
        "literature risk score summary",
    )
    return {
        str(row["candidate_id"]): row
        for row in frame.to_dict(orient="records")
    }


def _table(frame: pd.DataFrame, columns: Sequence[str]) -> str:
    header = "".join(f"<th>{escape(column)}</th>" for column in columns)
    rows: list[str] = []
    for item in frame.loc[:, list(columns)].to_dict(orient="records"):
        cells = "".join(f"<td>{escape(_format_cell(item[column]))}</td>" for column in columns)
        rows.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def _format_cell(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _format_number(value: object) -> object:
    if value == "":
        return ""
    return round(_float_or_zero(value), 6)


def _max_severity(values: pd.Series) -> str:
    labels = [str(value) for value in values.tolist()]
    return max(labels, key=lambda label: SEVERITY_RANK.get(label, -1))


def _max_numeric(series: pd.Series) -> float:
    return float(pd.to_numeric(series, errors="coerce").fillna(0).max())


def _float_or_zero(value: object) -> float:
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_divide(numerator: float, denominator: int | float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / float(denominator)


def _amount_from_log_metric(value: object) -> float:
    try:
        numeric = _float_or_zero(value)
        return max(0.0, float(expm1(numeric)))
    except OverflowError:
        return 0.0


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _read_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"{label} file not found: {path}")
    frame = pd.read_csv(path, keep_default_na=False)
    if frame.empty:
        raise ValueError(f"{label} file is empty: {path}")
    return frame


def _read_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, keep_default_na=False)


def _validate_alert_rows(frame: pd.DataFrame) -> None:
    missing = [column for column in MONITOR_ALERT_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"alert rows missing required columns: {missing}")
    invalid = sorted(set(frame["severity"].astype(str)) - set(SEVERITY_RANK))
    if invalid:
        raise ValueError(f"alert rows contain invalid severity values: {invalid}")
    _reject_wallet_address_columns((frame,))


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def _reject_wallet_address_columns(frames: Sequence[pd.DataFrame]) -> None:
    for frame in frames:
        forbidden = [column for column in frame.columns if "wallet_address" in column.lower()]
        if forbidden:
            raise ValueError(f"review report inputs must not contain wallet-address columns: {forbidden}")


if __name__ == "__main__":
    raise SystemExit(main())
