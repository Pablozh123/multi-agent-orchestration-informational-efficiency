"""Create a compact human-review report for strict monitor candidates."""
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

from operations.analysis.monitor_reference_candidates import (
    CANDIDATE_FEATURES_OUTPUT,
    CANDIDATE_SIMILARITY_SUMMARY_OUTPUT,
    MONITOR_ALERT_COLUMNS,
    monitor_candidate_id,
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
    "triggered_patterns",
    "best_reference_case_id",
    "best_similarity_score",
    "matched_patterns",
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

SEVERITY_RANK = {"none": 0, "info": 1, "watch": 2, "high": 3, "critical": 4}


@dataclass(frozen=True)
class HumanReviewReportResult:
    """Summary of generated human-review report artifacts."""

    report_path: Path
    dashboard_path: Path
    metadata_path: Path
    candidate_count: int
    high_priority_count: int
    max_similarity_score: float

    def to_dict(self) -> dict[str, float | int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "report_path": str(self.report_path),
            "dashboard_path": str(self.dashboard_path),
            "metadata_path": str(self.metadata_path),
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
    report_path: Path = REVIEW_REPORT_OUTPUT,
    dashboard_path: Path = REVIEW_DASHBOARD_OUTPUT,
    metadata_path: Path = REVIEW_METADATA_OUTPUT,
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

    report = build_human_review_report(
        alert_rows=alert_rows,
        watchlist=watchlist,
        market_snapshots=market_snapshots,
        wallet_tier_snapshots=wallet_tier_snapshots,
        similarity_summary=similarity_summary,
        candidate_features=candidate_features,
    )
    _write_csv(report_path, report)
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
        report_path=report_path,
        dashboard_path=dashboard_path,
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
    parser.add_argument("--report-output", type=Path, default=REVIEW_REPORT_OUTPUT)
    parser.add_argument("--dashboard-output", type=Path, default=REVIEW_DASHBOARD_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=REVIEW_METADATA_OUTPUT)
    args = parser.parse_args(argv)

    try:
        result = generate_monitor_candidate_human_review_report(
            alert_rows_path=args.alert_rows,
            watchlist_path=args.watchlist,
            market_snapshots_path=args.market_snapshots,
            wallet_tier_snapshots_path=args.wallet_tier_snapshots,
            similarity_summary_path=args.similarity_summary,
            candidate_features_path=args.candidate_features,
            report_path=args.report_output,
            dashboard_path=args.dashboard_output,
            metadata_path=args.metadata_output,
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
) -> dict[str, object]:
    families = sorted(set(group["anomaly_family"].astype(str)))
    metrics = sorted(set(group["metric_name"].astype(str)))
    max_severity = _max_severity(group["severity"])
    max_robust_z = _max_numeric(group["robust_z"])
    max_percentile = _max_numeric(group["rolling_percentile_rank"])
    best_similarity = _float_or_zero(similarity.get("best_similarity_score", 0.0))
    priority = _review_priority(
        max_severity=max_severity,
        best_similarity=best_similarity,
        patterns=triggered_patterns,
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
        "active_wallets": int(_float_or_zero(wallet.get("active_wallets", 0))),
        "trade_count": int(_float_or_zero(wallet.get("trade_count", 0))),
        "total_observed_amount_usd": round(
            _float_or_zero(wallet.get("total_observed_amount_usd", 0.0)),
            6,
        ),
        "triggered_patterns": ",".join(sorted(triggered_patterns)),
        "best_reference_case_id": similarity.get("best_reference_case_id", ""),
        "best_similarity_score": round(best_similarity, 6),
        "matched_patterns": similarity.get("matched_patterns", ""),
        "why_flagged": _why_flagged(group, triggered_patterns),
        "available_evidence": _available_evidence(group, wallet, market, similarity),
        "missing_evidence": _missing_evidence(group, triggered_patterns),
        "review_priority": priority,
        "recommended_next_step": _recommended_next_step(priority, triggered_patterns),
        "human_review_status": "needs_human_review",
        "allowed_interpretation": (
            "Strict monitor candidate for human review only; not proof, "
            "not a causal claim, and not a trading signal."
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


def _write_dashboard(report: pd.DataFrame, dashboard_path: Path) -> None:
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    if report.empty:
        body = "<p>No strict monitor candidates require review.</p>"
        candidate_count = 0
        high_priority = 0
    else:
        body = _table(
            report,
            (
                "question",
                "max_severity",
                "review_priority",
                "why_flagged",
                "available_evidence",
                "missing_evidence",
                "recommended_next_step",
            ),
        )
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
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; font-size: 13px; }}
    th, td {{ border: 1px solid #d7dde5; padding: 7px; text-align: left; vertical-align: top; }}
    th {{ background: #eef2f7; }}
    .note {{ background: #fff7e6; border: 1px solid #f0d08a; padding: 12px; border-radius: 6px; }}
  </style>
</head>
<body>
  <h1>Monitor Candidate Human Review</h1>
  <p class="note">Strict monitor candidates are review cues only. This report contains no wallet addresses, order instructions, PnL, or misconduct claim.</p>
  <section class="metrics">
    <div class="metric">Candidates<strong>{candidate_count}</strong></div>
    <div class="metric">High priority<strong>{high_priority}</strong></div>
    <div class="metric">Status<strong>needs review</strong></div>
  </section>
  <h2>Review Rows</h2>
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
    report_path: Path,
    dashboard_path: Path,
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
            "source_alert_rows": int(len(alert_rows)),
        },
        "outputs": {
            "report_path": str(report_path),
            "dashboard_path": str(dashboard_path),
            "candidate_count": int(len(report)),
            "high_priority_count": int((report["review_priority"] == "high").sum())
            if not report.empty
            else 0,
            "max_similarity_score": _max_report_similarity(report),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "limitations": {
            "human_review_required": True,
            "not_a_probability_model": True,
            "not_a_causal_test": True,
            "not_a_trade_or_profitability_signal": True,
            "not_a_misconduct_finding": True,
            "aggregate_monitor_fields_only": True,
        },
    }


def _max_report_similarity(report: pd.DataFrame) -> float:
    if report.empty:
        return 0.0
    return float(
        pd.to_numeric(report["best_similarity_score"], errors="coerce").fillna(0).max()
    )


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
