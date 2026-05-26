"""Generate literature-prior diagnostic risk scores for monitor candidates.

The scores in this module are deterministic review aids. They do not replace
Rule C, do not activate agents or MCP, and do not create a trading signal.
Unavailable literature features are marked explicitly instead of guessed.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from operations.analysis.monitor_reference_candidates import MONITOR_ALERT_COLUMNS
from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.collectors.polymarket_readonly import (
    LIVE_MARKET_SNAPSHOTS_OUTPUT,
    LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT,
)
from operations.collectors.polymarket_rolling_history import ROLLING_ALERT_ROWS_OUTPUT


HUMAN_REVIEW_REPORT_INPUT = RESULTS_DIR / "monitor_candidate_human_review_report.csv"
RISK_SCORE_ROWS_OUTPUT = RESULTS_DIR / "monitor_literature_risk_score_rows.csv"
RISK_SCORE_SUMMARY_OUTPUT = RESULTS_DIR / "monitor_literature_risk_score_summary.csv"
RISK_SCORE_METADATA_OUTPUT = RESULTS_DIR / "monitor_literature_risk_score_metadata.json"

WALLET_SCORE_THRESHOLD = 6.0
MARKET_RISK_THRESHOLD = 0.65

WALLET_FEATURE_WEIGHTS: dict[str, float] = {
    "new_wallet_penalty": 2.0,
    "volume_spike_ratio": 1.5,
    "timing_proximity_to_reviewed_event_or_resolution": 2.5,
    "cluster_correlation_proxy": 1.8,
}
MARKET_FEATURE_WEIGHTS: dict[str, float] = {
    "new_wallet_ratio": 1.0,
    "price_velocity": 1.0,
    "volume_concentration": 1.0,
}

RISK_ROW_COLUMNS: tuple[str, ...] = (
    "candidate_id",
    "timestamp_utc",
    "market_id",
    "question",
    "score_family",
    "feature_name",
    "feature_value",
    "feature_status",
    "feature_weight",
    "weighted_value",
    "evidence_ref",
    "limitation",
)
RISK_SUMMARY_COLUMNS: tuple[str, ...] = (
    "candidate_id",
    "timestamp_utc",
    "market_id",
    "question",
    "max_severity",
    "review_priority",
    "insider_risk_review_label",
    "materiality_label",
    "coordination_label",
    "literature_wallet_risk_score",
    "literature_wallet_risk_flag",
    "literature_market_risk_score",
    "literature_market_risk_flag",
    "available_feature_count",
    "unavailable_feature_count",
    "feature_status_summary",
    "allowed_interpretation",
    "limitation",
    "claim_scope",
)


@dataclass(frozen=True)
class LiteratureRiskScoreResult:
    """Summary of generated literature-prior risk score artifacts."""

    rows_path: Path
    summary_path: Path
    metadata_path: Path
    candidate_count: int
    flagged_candidate_count: int
    unavailable_feature_count: int

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "rows_path": str(self.rows_path),
            "summary_path": str(self.summary_path),
            "metadata_path": str(self.metadata_path),
            "candidate_count": self.candidate_count,
            "flagged_candidate_count": self.flagged_candidate_count,
            "unavailable_feature_count": self.unavailable_feature_count,
        }


def build_literature_risk_scores(
    *,
    review_report: pd.DataFrame,
    alert_rows: pd.DataFrame,
    market_snapshots: pd.DataFrame,
    wallet_tier_snapshots: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return row-level feature scores and compact candidate summaries."""

    _validate_review_report(review_report)
    _validate_alert_rows(alert_rows)
    _validate_market_snapshots(market_snapshots)
    _validate_wallet_snapshots(wallet_tier_snapshots)
    _reject_wallet_address_columns(
        (review_report, alert_rows, market_snapshots, wallet_tier_snapshots)
    )

    velocity_lookup = _price_velocity_lookup(market_snapshots)
    concentration_lookup = _concentration_lookup(wallet_tier_snapshots)
    row_items: list[dict[str, object]] = []
    summary_items: list[dict[str, object]] = []
    for candidate in review_report.to_dict(orient="records"):
        candidate_id = str(candidate["candidate_id"])
        timestamp_utc = str(candidate["timestamp_utc"])
        market_id = str(candidate["market_id"])
        candidate_alerts = alert_rows[
            (alert_rows["timestamp_utc"].astype(str) == timestamp_utc)
            & (alert_rows["market_id"].astype(str) == market_id)
        ]
        features = _candidate_feature_rows(
            candidate=candidate,
            candidate_alerts=candidate_alerts,
            price_velocity=velocity_lookup.get((market_id, timestamp_utc)),
            volume_concentration=concentration_lookup.get((market_id, timestamp_utc)),
        )
        row_items.extend(features)
        summary_items.append(_candidate_summary(candidate, features))

    rows = pd.DataFrame(row_items, columns=RISK_ROW_COLUMNS)
    summary = pd.DataFrame(summary_items, columns=RISK_SUMMARY_COLUMNS)
    return rows, summary


def generate_literature_risk_score_outputs(
    *,
    review_report_path: Path = HUMAN_REVIEW_REPORT_INPUT,
    alert_rows_path: Path = ROLLING_ALERT_ROWS_OUTPUT,
    market_snapshots_path: Path = LIVE_MARKET_SNAPSHOTS_OUTPUT,
    wallet_tier_snapshots_path: Path = LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT,
    rows_path: Path = RISK_SCORE_ROWS_OUTPUT,
    summary_path: Path = RISK_SCORE_SUMMARY_OUTPUT,
    metadata_path: Path = RISK_SCORE_METADATA_OUTPUT,
) -> LiteratureRiskScoreResult:
    """Write literature-prior risk score CSVs and metadata."""

    review_report = _read_csv(review_report_path, "human review report")
    alert_rows = _read_csv(alert_rows_path, "alert rows")
    market_snapshots = _read_csv(market_snapshots_path, "market snapshots")
    wallet_tier_snapshots = _read_csv(wallet_tier_snapshots_path, "wallet snapshots")
    rows, summary = build_literature_risk_scores(
        review_report=review_report,
        alert_rows=alert_rows,
        market_snapshots=market_snapshots,
        wallet_tier_snapshots=wallet_tier_snapshots,
    )

    _write_csv(rows_path, rows)
    _write_csv(summary_path, summary)
    metadata = _metadata(
        rows=rows,
        summary=summary,
        review_report_path=review_report_path,
        alert_rows_path=alert_rows_path,
        market_snapshots_path=market_snapshots_path,
        wallet_tier_snapshots_path=wallet_tier_snapshots_path,
        rows_path=rows_path,
        summary_path=summary_path,
    )
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return LiteratureRiskScoreResult(
        rows_path=rows_path,
        summary_path=summary_path,
        metadata_path=metadata_path,
        candidate_count=int(len(summary)),
        flagged_candidate_count=int(
            (
                (summary["literature_wallet_risk_flag"] == "literature_prior_flag")
                | (summary["literature_market_risk_flag"] == "literature_prior_flag")
            ).sum()
        )
        if not summary.empty
        else 0,
        unavailable_feature_count=int((rows["feature_status"] == "unavailable").sum())
        if not rows.empty
        else 0,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-report", type=Path, default=HUMAN_REVIEW_REPORT_INPUT)
    parser.add_argument("--alert-rows", type=Path, default=ROLLING_ALERT_ROWS_OUTPUT)
    parser.add_argument("--market-snapshots", type=Path, default=LIVE_MARKET_SNAPSHOTS_OUTPUT)
    parser.add_argument(
        "--wallet-tier-snapshots",
        type=Path,
        default=LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT,
    )
    parser.add_argument("--rows-output", type=Path, default=RISK_SCORE_ROWS_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=RISK_SCORE_SUMMARY_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=RISK_SCORE_METADATA_OUTPUT)
    args = parser.parse_args(argv)

    try:
        result = generate_literature_risk_score_outputs(
            review_report_path=args.review_report,
            alert_rows_path=args.alert_rows,
            market_snapshots_path=args.market_snapshots,
            wallet_tier_snapshots_path=args.wallet_tier_snapshots,
            rows_path=args.rows_output,
            summary_path=args.summary_output,
            metadata_path=args.metadata_output,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _candidate_feature_rows(
    *,
    candidate: dict[str, object],
    candidate_alerts: pd.DataFrame,
    price_velocity: float | None,
    volume_concentration: float | None,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    rows.append(
        _feature_row(
            candidate,
            "wallet",
            "new_wallet_penalty",
            None,
            "unavailable",
            WALLET_FEATURE_WEIGHTS["new_wallet_penalty"],
            "wallet-first-seen data unavailable",
            "Requires per-wallet age from longer local history, Dune, or Polygonscan.",
        )
    )
    rows.append(_volume_spike_feature(candidate, candidate_alerts))
    rows.append(_timing_feature(candidate, candidate_alerts))
    rows.append(_cluster_proxy_feature(candidate))
    rows.append(
        _feature_row(
            candidate,
            "market",
            "new_wallet_ratio",
            None,
            "unavailable",
            MARKET_FEATURE_WEIGHTS["new_wallet_ratio"],
            "new-wallet volume share unavailable",
            "Requires per-wallet volume and first-seen metadata.",
        )
    )
    rows.append(
        _feature_row(
            candidate,
            "market",
            "price_velocity",
            price_velocity,
            "computed_proxy" if price_velocity is not None else "unavailable",
            MARKET_FEATURE_WEIGHTS["price_velocity"],
            "CLOB midpoint bucket-to-bucket absolute token change",
            "Uses public midpoint snapshots; not an order-book impact model.",
        )
    )
    rows.append(
        _feature_row(
            candidate,
            "market",
            "volume_concentration",
            volume_concentration,
            "computed_proxy" if volume_concentration is not None else "unavailable",
            MARKET_FEATURE_WEIGHTS["volume_concentration"],
            "max(top_tier_share, hhi_concentration)",
            "Uses aggregate Data API activity; no top-5 wallet table is exposed.",
        )
    )
    return rows


def _volume_spike_feature(
    candidate: dict[str, object],
    candidate_alerts: pd.DataFrame,
) -> dict[str, object]:
    amount_rows = candidate_alerts[
        (candidate_alerts["anomaly_family"].astype(str) == "wallet_tier_activity")
        & (
            candidate_alerts["metric_name"].astype(str)
            == "log1p_total_observed_amount_usd"
        )
    ]
    if amount_rows.empty:
        return _feature_row(
            candidate,
            "wallet",
            "volume_spike_ratio",
            None,
            "unavailable",
            WALLET_FEATURE_WEIGHTS["volume_spike_ratio"],
            "no wallet amount anomaly row for this candidate",
            "Current candidate did not trigger the amount-spike metric.",
        )
    value = _clip01(
        pd.to_numeric(amount_rows["rolling_percentile_rank"], errors="coerce")
        .fillna(0.0)
        .max()
    )
    return _feature_row(
        candidate,
        "wallet",
        "volume_spike_ratio",
        value,
        "computed_proxy",
        WALLET_FEATURE_WEIGHTS["volume_spike_ratio"],
        "wallet amount rolling percentile proxy",
        "Aggregate bucket proxy, not per-wallet volume history.",
    )


def _timing_feature(
    candidate: dict[str, object],
    candidate_alerts: pd.DataFrame,
) -> dict[str, object]:
    if candidate_alerts.empty:
        accepted = False
    else:
        status = candidate_alerts["event_review_status"].fillna("").astype(str)
        event_id = candidate_alerts["event_candidate_id"].fillna("").astype(str)
        accepted = status.isin({"accepted", "market_mapped"}).any() and event_id.str.strip().ne("").any()
    return _feature_row(
        candidate,
        "wallet",
        "timing_proximity_to_reviewed_event_or_resolution",
        1.0 if accepted else None,
        "computed_proxy" if accepted else "unavailable",
        WALLET_FEATURE_WEIGHTS["timing_proximity_to_reviewed_event_or_resolution"],
        "reviewed event or resolution proximity",
        "Unavailable until a candidate has reviewed event/resolution context.",
    )


def _cluster_proxy_feature(candidate: dict[str, object]) -> dict[str, object]:
    label = str(candidate.get("coordination_label", ""))
    value = {
        "coordinated_small_flow_candidate": 1.0,
        "multi_wallet_or_trade_review_candidate": 0.7,
        "few_wallet_or_trade_context": 0.35,
        "single_wallet_single_trade": 0.0,
    }.get(label, 0.0)
    return _feature_row(
        candidate,
        "wallet",
        "cluster_correlation_proxy",
        value,
        "computed_proxy",
        WALLET_FEATURE_WEIGHTS["cluster_correlation_proxy"],
        f"coordination_label={label or 'unknown'}",
        "Aggregate coordination proxy; not a funding graph or identity cluster.",
    )


def _feature_row(
    candidate: dict[str, object],
    score_family: str,
    feature_name: str,
    feature_value: float | None,
    feature_status: str,
    feature_weight: float,
    evidence_ref: str,
    limitation: str,
) -> dict[str, object]:
    numeric_value = 0.0 if feature_value is None else _clip01(float(feature_value))
    return {
        "candidate_id": candidate["candidate_id"],
        "timestamp_utc": candidate["timestamp_utc"],
        "market_id": candidate["market_id"],
        "question": candidate.get("question", ""),
        "score_family": score_family,
        "feature_name": feature_name,
        "feature_value": "" if feature_value is None else round(numeric_value, 6),
        "feature_status": feature_status,
        "feature_weight": feature_weight,
        "weighted_value": round(numeric_value * feature_weight, 6)
        if feature_status != "unavailable"
        else 0.0,
        "evidence_ref": evidence_ref,
        "limitation": limitation,
    }


def _candidate_summary(
    candidate: dict[str, object],
    features: list[dict[str, object]],
) -> dict[str, object]:
    frame = pd.DataFrame(features)
    wallet_score = _score_family(frame, "wallet")
    market_score = _score_family(frame, "market")
    available = int((frame["feature_status"] != "unavailable").sum())
    unavailable = int((frame["feature_status"] == "unavailable").sum())
    return {
        "candidate_id": candidate["candidate_id"],
        "timestamp_utc": candidate["timestamp_utc"],
        "market_id": candidate["market_id"],
        "question": candidate.get("question", ""),
        "max_severity": candidate.get("max_severity", ""),
        "review_priority": candidate.get("review_priority", ""),
        "insider_risk_review_label": candidate.get("insider_risk_review_label", ""),
        "materiality_label": candidate.get("materiality_label", ""),
        "coordination_label": candidate.get("coordination_label", ""),
        "literature_wallet_risk_score": round(wallet_score, 6),
        "literature_wallet_risk_flag": _flag(wallet_score, WALLET_SCORE_THRESHOLD),
        "literature_market_risk_score": round(market_score, 6),
        "literature_market_risk_flag": _flag(market_score, MARKET_RISK_THRESHOLD),
        "available_feature_count": available,
        "unavailable_feature_count": unavailable,
        "feature_status_summary": _feature_status_summary(frame),
        "allowed_interpretation": (
            "Literature-prior diagnostic score for human review only; not a "
            "Rule C replacement and not a trading signal."
        ),
        "limitation": (
            "Several literature features are unavailable without per-wallet "
            "history, Dune, or Polygonscan enrichment."
        ),
        "claim_scope": "literature_prior_monitor_review_only",
    }


def _price_velocity_lookup(market_snapshots: pd.DataFrame) -> dict[tuple[str, str], float]:
    frame = market_snapshots.copy()
    frame["bucket_end_utc"] = pd.to_datetime(frame["bucket_end_utc"], utc=True, errors="raise")
    frame["midpoint"] = pd.to_numeric(frame["midpoint"], errors="raise")
    grouped = (
        frame.groupby(["market_id", "bucket_end_utc"], as_index=False)
        .agg(midpoint_min=("midpoint", "min"), midpoint_max=("midpoint", "max"))
        .sort_values(["market_id", "bucket_end_utc"])
    )
    lookup: dict[tuple[str, str], float] = {}
    for market_id, group in grouped.groupby("market_id", sort=True):
        ordered = group.reset_index(drop=True)
        prev_min = ordered["midpoint_min"].shift(1)
        prev_max = ordered["midpoint_max"].shift(1)
        velocity = pd.concat(
            [
                (ordered["midpoint_min"] - prev_min).abs(),
                (ordered["midpoint_max"] - prev_max).abs(),
            ],
            axis=1,
        ).max(axis=1).fillna(0.0)
        for row, value in zip(ordered.to_dict(orient="records"), velocity.tolist()):
            lookup[(str(market_id), _iso_z(row["bucket_end_utc"]))] = _clip01(float(value))
    return lookup


def _concentration_lookup(wallet_snapshots: pd.DataFrame) -> dict[tuple[str, str], float]:
    frame = wallet_snapshots.copy()
    frame["bucket_end_utc"] = pd.to_datetime(frame["bucket_end_utc"], utc=True, errors="raise")
    for column in ("top_tier_share", "hhi_concentration"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)
    grouped = (
        frame.groupby(["market_id", "bucket_end_utc"], as_index=False)
        .agg(top_tier_share=("top_tier_share", "max"), hhi_concentration=("hhi_concentration", "max"))
    )
    return {
        (str(row["market_id"]), _iso_z(row["bucket_end_utc"])): _clip01(
            max(float(row["top_tier_share"]), float(row["hhi_concentration"]))
        )
        for row in grouped.to_dict(orient="records")
    }


def _score_family(frame: pd.DataFrame, score_family: str) -> float:
    family = frame[frame["score_family"] == score_family]
    if family.empty:
        return 0.0
    return float(pd.to_numeric(family["weighted_value"], errors="coerce").fillna(0.0).sum())


def _flag(score: float, threshold: float) -> str:
    return "literature_prior_flag" if score > threshold else "no_literature_prior_flag"


def _feature_status_summary(frame: pd.DataFrame) -> str:
    parts: list[str] = []
    for status, group in frame.groupby("feature_status", sort=True):
        parts.append(f"{status}={len(group)}")
    return "; ".join(parts)


def _metadata(
    *,
    rows: pd.DataFrame,
    summary: pd.DataFrame,
    review_report_path: Path,
    alert_rows_path: Path,
    market_snapshots_path: Path,
    wallet_tier_snapshots_path: Path,
    rows_path: Path,
    summary_path: Path,
) -> dict[str, Any]:
    flagged_count = int(
        (
            (summary["literature_wallet_risk_flag"] == "literature_prior_flag")
            | (summary["literature_market_risk_flag"] == "literature_prior_flag")
        ).sum()
    ) if not summary.empty else 0
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "monitor_literature_risk_scores",
            "score_status": "literature_prior_diagnostic",
            "wallet_score_threshold": WALLET_SCORE_THRESHOLD,
            "market_risk_threshold": MARKET_RISK_THRESHOLD,
            "wallet_feature_weights": WALLET_FEATURE_WEIGHTS,
            "market_feature_weights": MARKET_FEATURE_WEIGHTS,
            "does_not_replace_rule_c": True,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
        },
        "inputs": {
            "review_report_path": str(review_report_path),
            "alert_rows_path": str(alert_rows_path),
            "market_snapshots_path": str(market_snapshots_path),
            "wallet_tier_snapshots_path": str(wallet_tier_snapshots_path),
        },
        "outputs": {
            "rows_path": str(rows_path),
            "summary_path": str(summary_path),
            "candidate_count": int(len(summary)),
            "row_count": int(len(rows)),
            "flagged_candidate_count": flagged_count,
            "unavailable_feature_count": int((rows["feature_status"] == "unavailable").sum())
            if not rows.empty
            else 0,
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "limitations": {
            "human_review_required": True,
            "not_a_rule_c_replacement": True,
            "not_a_trading_signal": True,
            "not_a_causal_test": True,
            "per_wallet_age_unavailable_in_v1": True,
            "funding_graph_unavailable_in_v1": True,
        },
    }


def _validate_review_report(frame: pd.DataFrame) -> None:
    _require_columns(
        frame,
        (
            "candidate_id",
            "timestamp_utc",
            "market_id",
            "question",
            "max_severity",
            "review_priority",
            "insider_risk_review_label",
            "materiality_label",
            "coordination_label",
        ),
        "human review report",
    )


def _validate_alert_rows(frame: pd.DataFrame) -> None:
    _require_columns(frame, MONITOR_ALERT_COLUMNS, "alert rows")


def _validate_market_snapshots(frame: pd.DataFrame) -> None:
    _require_columns(frame, ("bucket_end_utc", "market_id", "midpoint"), "market snapshots")


def _validate_wallet_snapshots(frame: pd.DataFrame) -> None:
    _require_columns(
        frame,
        ("bucket_end_utc", "market_id", "top_tier_share", "hhi_concentration"),
        "wallet snapshots",
    )


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def _reject_wallet_address_columns(frames: Sequence[pd.DataFrame]) -> None:
    for frame in frames:
        forbidden = [column for column in frame.columns if "wallet_address" in column.lower()]
        if forbidden:
            raise ValueError(f"risk score inputs must not contain wallet-address columns: {forbidden}")


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _iso_z(value: object) -> str:
    return pd.Timestamp(value).tz_convert("UTC").isoformat().replace("+00:00", "Z")


def _read_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"{label} file not found: {path}")
    frame = pd.read_csv(path, keep_default_na=False)
    if frame.empty:
        raise ValueError(f"{label} file is empty: {path}")
    return frame


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


if __name__ == "__main__":
    raise SystemExit(main())
