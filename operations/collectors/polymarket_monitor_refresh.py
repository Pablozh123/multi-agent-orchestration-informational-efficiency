"""Run a bounded read-only monitor refresh and regenerate the dashboard."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

import httpx
from pydantic import ValidationError

from operations.analysis.monitor_v2_dashboard import (
    DASHBOARD_METADATA_OUTPUT,
    DASHBOARD_OUTPUT,
    generate_monitor_v2_dashboard,
)
from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.collectors.polymarket_readonly import (
    DEFAULT_BUCKET_MINUTES,
    DEFAULT_MAX_MARKETS,
    DEFAULT_TRADE_LIMIT,
)
from operations.collectors.polymarket_rolling_history import (
    DIAGNOSTIC_BASELINE_OBSERVATIONS,
    DIAGNOSTIC_MIN_BASELINE_OBSERVATIONS,
    ROLLING_ALERT_SUMMARY_OUTPUT,
    ROLLING_HISTORY_METADATA_OUTPUT,
    ROLLING_SCORING_METADATA_OUTPUT,
    collect_polymarket_rolling_history,
)


REFRESH_METADATA_OUTPUT = RESULTS_DIR / "monitor_v2_polymarket_refresh_metadata.json"


@dataclass(frozen=True)
class RefreshResult:
    """Summary of a bounded monitor refresh run."""

    metadata_path: Path
    dashboard_path: Path
    samples_completed: int
    bucket_count: int
    alert_count: int
    baseline_readiness: str

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "metadata_path": str(self.metadata_path),
            "dashboard_path": str(self.dashboard_path),
            "samples_completed": self.samples_completed,
            "bucket_count": self.bucket_count,
            "alert_count": self.alert_count,
            "baseline_readiness": self.baseline_readiness,
        }


def run_polymarket_monitor_refresh(
    *,
    source: str = "mock",
    samples: int = 1,
    delay_seconds: float = 0.0,
    reset_outputs: bool = False,
    bucket_minutes: int = DEFAULT_BUCKET_MINUTES,
    max_markets: int = DEFAULT_MAX_MARKETS,
    trade_limit: int = DEFAULT_TRADE_LIMIT,
    collected_at_utc: str | None = None,
    curated_watchlist_path: Path | None = None,
    baseline_observations: int = DIAGNOSTIC_BASELINE_OBSERVATIONS,
    min_baseline_observations: int = DIAGNOSTIC_MIN_BASELINE_OBSERVATIONS,
    dashboard_path: Path = DASHBOARD_OUTPUT,
    dashboard_metadata_path: Path = DASHBOARD_METADATA_OUTPUT,
    metadata_path: Path = REFRESH_METADATA_OUTPUT,
    client: httpx.Client | None = None,
) -> RefreshResult:
    """Collect bounded rolling inputs, score them, and refresh the dashboard."""

    rolling = collect_polymarket_rolling_history(
        source=source,
        samples=samples,
        delay_seconds=delay_seconds,
        reset_outputs=reset_outputs,
        bucket_minutes=bucket_minutes,
        max_markets=max_markets,
        trade_limit=trade_limit,
        collected_at_utc=collected_at_utc,
        curated_watchlist_path=curated_watchlist_path,
        baseline_observations=baseline_observations,
        min_baseline_observations=min_baseline_observations,
        client=client,
    )
    dashboard = generate_monitor_v2_dashboard(
        alert_summary_path=ROLLING_ALERT_SUMMARY_OUTPUT,
        scoring_metadata_path=ROLLING_SCORING_METADATA_OUTPUT,
        rolling_metadata_path=ROLLING_HISTORY_METADATA_OUTPUT,
        dashboard_path=dashboard_path,
        metadata_path=dashboard_metadata_path,
    )
    metadata = {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "polymarket_monitor_bounded_refresh",
            "source": source,
            "samples_requested": samples,
            "samples_completed": rolling.samples_completed,
            "delay_seconds": delay_seconds,
            "bucket_minutes": bucket_minutes,
            "baseline_observations": baseline_observations,
            "min_baseline_observations": min_baseline_observations,
            "reset_outputs": reset_outputs,
            "bounded_runner_not_daemon": True,
            "uses_curated_watchlist": curated_watchlist_path is not None,
            "curated_watchlist_path": (
                "" if curated_watchlist_path is None else str(curated_watchlist_path)
            ),
            "read_only": True,
        },
        "outputs": {
            "rolling_metadata_path": str(rolling.metadata_path),
            "dashboard_path": str(dashboard.dashboard_path),
            "dashboard_metadata_path": str(dashboard.metadata_path),
            "bucket_count": dashboard.bucket_count,
            "alert_count": dashboard.alert_count,
            "baseline_readiness": dashboard.baseline_readiness,
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "limitations": {
            "bounded_local_operator_command": True,
            "not_a_background_daemon": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "no_causal_or_profitability_claim": True,
        },
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return RefreshResult(
        metadata_path=metadata_path,
        dashboard_path=dashboard.dashboard_path,
        samples_completed=rolling.samples_completed,
        bucket_count=dashboard.bucket_count,
        alert_count=dashboard.alert_count,
        baseline_readiness=dashboard.baseline_readiness,
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
    parser.add_argument("--curated-watchlist-input", type=Path, default=None)
    parser.add_argument("--baseline-observations", type=int, default=DIAGNOSTIC_BASELINE_OBSERVATIONS)
    parser.add_argument(
        "--min-baseline-observations",
        type=int,
        default=DIAGNOSTIC_MIN_BASELINE_OBSERVATIONS,
    )
    parser.add_argument("--dashboard-output", type=Path, default=DASHBOARD_OUTPUT)
    parser.add_argument("--dashboard-metadata-output", type=Path, default=DASHBOARD_METADATA_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=REFRESH_METADATA_OUTPUT)
    args = parser.parse_args(argv)

    try:
        result = run_polymarket_monitor_refresh(
            source=args.source,
            samples=args.samples,
            delay_seconds=args.delay_seconds,
            reset_outputs=args.reset,
            bucket_minutes=args.bucket_minutes,
            max_markets=args.max_markets,
            trade_limit=args.trade_limit,
            collected_at_utc=args.collected_at_utc,
            curated_watchlist_path=args.curated_watchlist_input,
            baseline_observations=args.baseline_observations,
            min_baseline_observations=args.min_baseline_observations,
            dashboard_path=args.dashboard_output,
            dashboard_metadata_path=args.dashboard_metadata_output,
            metadata_path=args.metadata_output,
        )
    except (httpx.HTTPError, FileNotFoundError, ValidationError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
