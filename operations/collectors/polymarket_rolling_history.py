"""Run bounded read-only Polymarket collection into rolling-history files."""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

import httpx
import pandas as pd
from pydantic import ValidationError

from operations.analysis.monitor_v2_live_input_scoring import (
    DIAGNOSTIC_BASELINE_OBSERVATIONS,
    DIAGNOSTIC_MIN_BASELINE_OBSERVATIONS,
    generate_live_monitor_v2_scoring_outputs,
)
from operations.analysis.monitor_v2_polymarket_rolling_figures import (
    ROLLING_FIGURE_METADATA_OUTPUT,
    ROLLING_FIGURE_OUTPUT,
    generate_polymarket_rolling_history_figure,
)
from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.collectors.polymarket_readonly import (
    DEFAULT_BUCKET_MINUTES,
    DEFAULT_MAX_MARKETS,
    DEFAULT_TRADE_LIMIT,
    LIVE_EVENT_CANDIDATES_OUTPUT,
    LIVE_MARKET_SNAPSHOTS_OUTPUT,
    LIVE_METADATA_OUTPUT,
    LIVE_VALIDATION_REPORT_OUTPUT,
    LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT,
    LIVE_WATCHLIST_OUTPUT,
    collect_readonly_polymarket_inputs,
)


ROLLING_HISTORY_METADATA_OUTPUT = (
    RESULTS_DIR / "monitor_v2_polymarket_rolling_history_metadata.json"
)
ROLLING_SCORING_SNAPSHOTS_OUTPUT = (
    RESULTS_DIR / "monitor_v2_polymarket_rolling_scoring_snapshots.csv"
)
ROLLING_ALERT_ROWS_OUTPUT = RESULTS_DIR / "monitor_v2_polymarket_rolling_alert_rows.csv"
ROLLING_ALERT_SUMMARY_OUTPUT = RESULTS_DIR / "monitor_v2_polymarket_rolling_alert_summary.csv"
ROLLING_SCORING_VALIDATION_REPORT_OUTPUT = (
    RESULTS_DIR / "monitor_v2_polymarket_rolling_scoring_validation_report.json"
)
ROLLING_SCORING_METADATA_OUTPUT = (
    RESULTS_DIR / "monitor_v2_polymarket_rolling_scoring_metadata.json"
)


@dataclass(frozen=True)
class RollingHistoryResult:
    """Summary of a bounded rolling-history collector run."""

    metadata_path: Path
    watchlist_path: Path
    market_snapshots_path: Path
    wallet_tier_snapshots_path: Path
    event_candidates_path: Path
    scoring_rows_path: Path
    scoring_summary_path: Path
    figure_path: Path
    samples_requested: int
    samples_completed: int
    bucket_count: int
    alert_count: int
    baseline_readiness: str

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "metadata_path": str(self.metadata_path),
            "watchlist_path": str(self.watchlist_path),
            "market_snapshots_path": str(self.market_snapshots_path),
            "wallet_tier_snapshots_path": str(self.wallet_tier_snapshots_path),
            "event_candidates_path": str(self.event_candidates_path),
            "scoring_rows_path": str(self.scoring_rows_path),
            "scoring_summary_path": str(self.scoring_summary_path),
            "figure_path": str(self.figure_path),
            "samples_requested": self.samples_requested,
            "samples_completed": self.samples_completed,
            "bucket_count": self.bucket_count,
            "alert_count": self.alert_count,
            "baseline_readiness": self.baseline_readiness,
        }


def collect_polymarket_rolling_history(
    *,
    source: str = "mock",
    samples: int = 1,
    delay_seconds: float = 0.0,
    reset_outputs: bool = False,
    bucket_minutes: int = DEFAULT_BUCKET_MINUTES,
    max_markets: int = DEFAULT_MAX_MARKETS,
    trade_limit: int = DEFAULT_TRADE_LIMIT,
    collected_at_utc: str | None = None,
    watchlist_path: Path = LIVE_WATCHLIST_OUTPUT,
    market_snapshots_path: Path = LIVE_MARKET_SNAPSHOTS_OUTPUT,
    wallet_tier_snapshots_path: Path = LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT,
    event_candidates_path: Path = LIVE_EVENT_CANDIDATES_OUTPUT,
    validation_report_path: Path = LIVE_VALIDATION_REPORT_OUTPUT,
    collector_metadata_path: Path = LIVE_METADATA_OUTPUT,
    scoring_snapshots_path: Path = ROLLING_SCORING_SNAPSHOTS_OUTPUT,
    scoring_rows_path: Path = ROLLING_ALERT_ROWS_OUTPUT,
    scoring_summary_path: Path = ROLLING_ALERT_SUMMARY_OUTPUT,
    scoring_validation_report_path: Path = ROLLING_SCORING_VALIDATION_REPORT_OUTPUT,
    scoring_metadata_path: Path = ROLLING_SCORING_METADATA_OUTPUT,
    figure_path: Path = ROLLING_FIGURE_OUTPUT,
    figure_metadata_path: Path = ROLLING_FIGURE_METADATA_OUTPUT,
    metadata_path: Path = ROLLING_HISTORY_METADATA_OUTPUT,
    baseline_observations: int = DIAGNOSTIC_BASELINE_OBSERVATIONS,
    min_baseline_observations: int = DIAGNOSTIC_MIN_BASELINE_OBSERVATIONS,
    client: httpx.Client | None = None,
) -> RollingHistoryResult:
    """Collect repeated closed buckets, score them, and write a figure."""

    if samples < 1:
        raise ValueError("samples must be >= 1")
    if delay_seconds < 0:
        raise ValueError("delay_seconds must be >= 0")
    if reset_outputs:
        _remove_outputs(
            (
                watchlist_path,
                market_snapshots_path,
                wallet_tier_snapshots_path,
                event_candidates_path,
                validation_report_path,
                collector_metadata_path,
                scoring_snapshots_path,
                scoring_rows_path,
                scoring_summary_path,
                scoring_validation_report_path,
                scoring_metadata_path,
                figure_path,
                figure_metadata_path,
                metadata_path,
            )
        )

    collection_runs: list[dict[str, Any]] = []
    for sample_index in range(samples):
        sample_time = _sample_collected_at(
            collected_at_utc=collected_at_utc,
            sample_index=sample_index,
            bucket_minutes=bucket_minutes,
        )
        result = collect_readonly_polymarket_inputs(
            source=source,
            watchlist_path=watchlist_path,
            market_snapshots_path=market_snapshots_path,
            wallet_tier_snapshots_path=wallet_tier_snapshots_path,
            event_candidates_path=event_candidates_path,
            validation_report_path=validation_report_path,
            metadata_path=collector_metadata_path,
            bucket_minutes=bucket_minutes,
            max_markets=max_markets,
            trade_limit=trade_limit,
            collected_at_utc=sample_time,
            append=True,
            client=client,
        )
        collection_runs.append(
            {
                "sample_index": sample_index,
                "collected_at_utc": "" if sample_time is None else sample_time,
                "watchlist_row_count": result.watchlist_row_count,
                "market_snapshot_row_count": result.market_snapshot_row_count,
                "wallet_tier_snapshot_row_count": result.wallet_tier_snapshot_row_count,
                "event_candidate_row_count": result.event_candidate_row_count,
            }
        )
        if sample_index < samples - 1 and delay_seconds > 0:
            time.sleep(delay_seconds)

    scoring_result = generate_live_monitor_v2_scoring_outputs(
        watchlist_path=watchlist_path,
        market_snapshots_path=market_snapshots_path,
        wallet_tier_snapshots_path=wallet_tier_snapshots_path,
        event_candidates_path=event_candidates_path,
        snapshots_path=scoring_snapshots_path,
        rows_path=scoring_rows_path,
        summary_path=scoring_summary_path,
        validation_report_path=scoring_validation_report_path,
        metadata_path=scoring_metadata_path,
        baseline_observations=baseline_observations,
        min_baseline_observations=min_baseline_observations,
    )
    figure_result = generate_polymarket_rolling_history_figure(
        watchlist_path=watchlist_path,
        market_snapshots_path=market_snapshots_path,
        wallet_tier_snapshots_path=wallet_tier_snapshots_path,
        scoring_metadata_path=scoring_metadata_path,
        figure_path=figure_path,
        metadata_path=figure_metadata_path,
    )
    scoring_metadata = _read_json(scoring_metadata_path)
    metadata = _build_metadata(
        source=source,
        samples=samples,
        delay_seconds=delay_seconds,
        reset_outputs=reset_outputs,
        bucket_minutes=bucket_minutes,
        max_markets=max_markets,
        trade_limit=trade_limit,
        collection_runs=collection_runs,
        scoring_metadata=scoring_metadata,
        scoring_result=scoring_result.to_dict(),
        figure_result=figure_result.to_dict(),
        paths={
            "watchlist_path": watchlist_path,
            "market_snapshots_path": market_snapshots_path,
            "wallet_tier_snapshots_path": wallet_tier_snapshots_path,
            "event_candidates_path": event_candidates_path,
            "validation_report_path": validation_report_path,
            "collector_metadata_path": collector_metadata_path,
            "scoring_snapshots_path": scoring_snapshots_path,
            "scoring_rows_path": scoring_rows_path,
            "scoring_summary_path": scoring_summary_path,
            "scoring_validation_report_path": scoring_validation_report_path,
            "scoring_metadata_path": scoring_metadata_path,
            "figure_path": figure_path,
            "figure_metadata_path": figure_metadata_path,
        },
    )
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return RollingHistoryResult(
        metadata_path=metadata_path,
        watchlist_path=watchlist_path,
        market_snapshots_path=market_snapshots_path,
        wallet_tier_snapshots_path=wallet_tier_snapshots_path,
        event_candidates_path=event_candidates_path,
        scoring_rows_path=scoring_rows_path,
        scoring_summary_path=scoring_summary_path,
        figure_path=figure_path,
        samples_requested=samples,
        samples_completed=len(collection_runs),
        bucket_count=figure_result.bucket_count,
        alert_count=scoring_result.alert_count,
        baseline_readiness=str(
            scoring_metadata.get("method", {}).get("baseline_readiness", "")
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("mock", "live"), default="mock")
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--delay-seconds", type=float, default=0.0)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--bucket-minutes", type=int, default=DEFAULT_BUCKET_MINUTES)
    parser.add_argument("--max-markets", type=int, default=DEFAULT_MAX_MARKETS)
    parser.add_argument("--trade-limit", type=int, default=DEFAULT_TRADE_LIMIT)
    parser.add_argument("--collected-at-utc", default=None)
    parser.add_argument("--watchlist-output", type=Path, default=LIVE_WATCHLIST_OUTPUT)
    parser.add_argument("--market-snapshots-output", type=Path, default=LIVE_MARKET_SNAPSHOTS_OUTPUT)
    parser.add_argument(
        "--wallet-tier-snapshots-output",
        type=Path,
        default=LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT,
    )
    parser.add_argument("--event-candidates-output", type=Path, default=LIVE_EVENT_CANDIDATES_OUTPUT)
    parser.add_argument("--validation-report-output", type=Path, default=LIVE_VALIDATION_REPORT_OUTPUT)
    parser.add_argument("--collector-metadata-output", type=Path, default=LIVE_METADATA_OUTPUT)
    parser.add_argument("--scoring-snapshots-output", type=Path, default=ROLLING_SCORING_SNAPSHOTS_OUTPUT)
    parser.add_argument("--scoring-rows-output", type=Path, default=ROLLING_ALERT_ROWS_OUTPUT)
    parser.add_argument("--scoring-summary-output", type=Path, default=ROLLING_ALERT_SUMMARY_OUTPUT)
    parser.add_argument(
        "--scoring-validation-report-output",
        type=Path,
        default=ROLLING_SCORING_VALIDATION_REPORT_OUTPUT,
    )
    parser.add_argument("--scoring-metadata-output", type=Path, default=ROLLING_SCORING_METADATA_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=ROLLING_FIGURE_OUTPUT)
    parser.add_argument("--figure-metadata-output", type=Path, default=ROLLING_FIGURE_METADATA_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=ROLLING_HISTORY_METADATA_OUTPUT)
    parser.add_argument("--baseline-observations", type=int, default=DIAGNOSTIC_BASELINE_OBSERVATIONS)
    parser.add_argument(
        "--min-baseline-observations",
        type=int,
        default=DIAGNOSTIC_MIN_BASELINE_OBSERVATIONS,
    )
    args = parser.parse_args(argv)

    try:
        result = collect_polymarket_rolling_history(
            source=args.source,
            samples=args.samples,
            delay_seconds=args.delay_seconds,
            reset_outputs=args.reset,
            bucket_minutes=args.bucket_minutes,
            max_markets=args.max_markets,
            trade_limit=args.trade_limit,
            collected_at_utc=args.collected_at_utc,
            watchlist_path=args.watchlist_output,
            market_snapshots_path=args.market_snapshots_output,
            wallet_tier_snapshots_path=args.wallet_tier_snapshots_output,
            event_candidates_path=args.event_candidates_output,
            validation_report_path=args.validation_report_output,
            collector_metadata_path=args.collector_metadata_output,
            scoring_snapshots_path=args.scoring_snapshots_output,
            scoring_rows_path=args.scoring_rows_output,
            scoring_summary_path=args.scoring_summary_output,
            scoring_validation_report_path=args.scoring_validation_report_output,
            scoring_metadata_path=args.scoring_metadata_output,
            figure_path=args.figure_output,
            figure_metadata_path=args.figure_metadata_output,
            metadata_path=args.metadata_output,
            baseline_observations=args.baseline_observations,
            min_baseline_observations=args.min_baseline_observations,
        )
    except (httpx.HTTPError, FileNotFoundError, ValidationError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _sample_collected_at(
    *,
    collected_at_utc: str | None,
    sample_index: int,
    bucket_minutes: int,
) -> str | None:
    if collected_at_utc is None or not str(collected_at_utc).strip():
        return None
    start = pd.Timestamp(str(collected_at_utc).replace("Z", "+00:00"))
    if start.tzinfo is None:
        raise ValueError("collected_at_utc must include a UTC offset")
    sample = start.tz_convert("UTC") + pd.Timedelta(
        minutes=sample_index * bucket_minutes,
    )
    return sample.strftime("%Y-%m-%dT%H:%M:%SZ")


def _remove_outputs(paths: Sequence[Path]) -> None:
    for path in paths:
        if path.exists():
            path.unlink()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_metadata(
    *,
    source: str,
    samples: int,
    delay_seconds: float,
    reset_outputs: bool,
    bucket_minutes: int,
    max_markets: int,
    trade_limit: int,
    collection_runs: list[dict[str, Any]],
    scoring_metadata: dict[str, Any],
    scoring_result: dict[str, int | str],
    figure_result: dict[str, int | str],
    paths: dict[str, Path],
) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "polymarket_readonly_rolling_history_collector",
            "source": source,
            "samples_requested": samples,
            "samples_completed": len(collection_runs),
            "delay_seconds": delay_seconds,
            "reset_outputs": reset_outputs,
            "bucket_minutes": bucket_minutes,
            "max_markets": max_markets,
            "trade_limit": trade_limit,
            "bounded_loop_not_daemon": True,
            "appends_and_deduplicates_outputs": True,
            "runs_scoring_after_collection": True,
            "runs_rolling_figure_after_collection": True,
            "baseline_readiness": scoring_metadata.get("method", {}).get(
                "baseline_readiness",
                "",
            ),
            "max_baseline_observations_available": scoring_metadata.get("method", {}).get(
                "max_baseline_observations_available",
                0,
            ),
        },
        "collection_runs": collection_runs,
        "outputs": {
            **{name: str(path) for name, path in paths.items()},
            "scoring_result": scoring_result,
            "figure_result": figure_result,
            "status_counts": scoring_metadata.get("outputs", {}).get("status_counts", {}),
            "severity_counts": scoring_metadata.get("outputs", {}).get("severity_counts", {}),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "limitations": {
            "read_only_public_endpoints_only": source == "live",
            "mock_source_available_for_tests": True,
            "not_a_background_daemon": True,
            "requires_enough_closed_buckets_for_alert_interpretation": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "does_not_use_rcp": True,
            "does_not_send_orders": True,
            "no_profitability_or_private_information_claim": True,
        },
    }


if __name__ == "__main__":
    raise SystemExit(main())
