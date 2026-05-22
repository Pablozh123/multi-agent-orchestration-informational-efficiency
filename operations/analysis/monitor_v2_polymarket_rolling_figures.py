"""Create rolling-history figures from read-only Polymarket collector outputs."""
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

from operations.analysis.monitor_v2_live_input_scoring import LIVE_SCORING_METADATA_OUTPUT
from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.collectors.polymarket_readonly import (
    LIVE_MARKET_SNAPSHOTS_OUTPUT,
    LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT,
    LIVE_WATCHLIST_OUTPUT,
)


ROLLING_FIGURE_OUTPUT = RESULTS_DIR / "monitor_v2_polymarket_rolling_history.png"
ROLLING_FIGURE_METADATA_OUTPUT = (
    RESULTS_DIR / "monitor_v2_polymarket_rolling_history_figure_metadata.json"
)


@dataclass(frozen=True)
class RollingFigureResult:
    """Summary of generated rolling-history figure artifacts."""

    figure_path: Path
    metadata_path: Path
    market_count: int
    bucket_count: int
    token_snapshot_count: int
    wallet_snapshot_count: int

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "market_count": self.market_count,
            "bucket_count": self.bucket_count,
            "token_snapshot_count": self.token_snapshot_count,
            "wallet_snapshot_count": self.wallet_snapshot_count,
        }


def generate_polymarket_rolling_history_figure(
    *,
    watchlist_path: Path = LIVE_WATCHLIST_OUTPUT,
    market_snapshots_path: Path = LIVE_MARKET_SNAPSHOTS_OUTPUT,
    wallet_tier_snapshots_path: Path = LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT,
    scoring_metadata_path: Path = LIVE_SCORING_METADATA_OUTPUT,
    figure_path: Path = ROLLING_FIGURE_OUTPUT,
    metadata_path: Path = ROLLING_FIGURE_METADATA_OUTPUT,
) -> RollingFigureResult:
    """Generate a compact rolling-history market and wallet/activity figure."""

    watchlist = _read_csv(watchlist_path, "watchlist")
    market = _read_csv(market_snapshots_path, "market snapshots")
    wallets = _read_csv(wallet_tier_snapshots_path, "wallet-tier snapshots")
    scoring_metadata = _read_optional_json(scoring_metadata_path)

    market_view = market.merge(
        watchlist[["market_id", "question"]],
        on="market_id",
        how="left",
    )
    market_view["timestamp_utc"] = pd.to_datetime(
        market_view["bucket_end_utc"],
        utc=True,
        errors="raise",
    )
    market_view["midpoint"] = pd.to_numeric(market_view["midpoint"], errors="coerce")
    market_view["series_label"] = market_view.apply(_market_label, axis=1)
    wallet_view = wallets.merge(
        watchlist[["market_id", "question"]],
        on="market_id",
        how="left",
    )
    wallet_view["timestamp_utc"] = pd.to_datetime(
        wallet_view["bucket_end_utc"],
        utc=True,
        errors="raise",
    )
    wallet_view["total_observed_amount_usd"] = pd.to_numeric(
        wallet_view["total_observed_amount_usd"],
        errors="coerce",
    ).fillna(0.0)
    wallet_view["active_wallets"] = pd.to_numeric(
        wallet_view["active_wallets"],
        errors="coerce",
    ).fillna(0)
    wallet_view["short_question"] = wallet_view["question"].fillna(wallet_view["market_id"]).map(_shorten)

    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), constrained_layout=True)

    plotted = 0
    for label, group in market_view.groupby("series_label", sort=True):
        if plotted >= 8:
            break
        ordered = group.sort_values("timestamp_utc")
        axes[0].plot(
            ordered["timestamp_utc"],
            ordered["midpoint"],
            marker="o",
            linewidth=1.4,
            label=label,
        )
        plotted += 1
    axes[0].set_ylim(0, 1)
    axes[0].set_ylabel("Midpoint probability")
    axes[0].set_title("Read-only Polymarket rolling midpoint history")
    axes[0].legend(loc="best", fontsize=7)

    amount_by_bucket = (
        wallet_view.groupby("timestamp_utc", as_index=False)
        .agg(
            {
                "total_observed_amount_usd": "sum",
                "active_wallets": "sum",
            }
        )
        .sort_values("timestamp_utc")
    )
    axes[1].bar(
        amount_by_bucket["timestamp_utc"],
        amount_by_bucket["total_observed_amount_usd"],
        color="#8a5a44",
        width=0.003,
    )
    axes[1].set_ylabel("Observed amount USD")
    axes[1].set_title("Aggregate public trade activity by closed bucket")
    for row in amount_by_bucket.itertuples():
        axes[1].text(
            row.timestamp_utc,
            float(row.total_observed_amount_usd),
            f"wallets={int(row.active_wallets)}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    for axis in axes:
        axis.tick_params(axis="x", rotation=20)

    fig.savefig(figure_path, dpi=150)
    plt.close(fig)

    bucket_count = int(market_view["bucket_end_utc"].nunique())
    metadata = {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "monitor_v2_polymarket_rolling_history_figure",
            "input_mode": "read_only_polymarket_collector_history",
        },
        "inputs": {
            "watchlist_path": str(watchlist_path),
            "market_snapshots_path": str(market_snapshots_path),
            "wallet_tier_snapshots_path": str(wallet_tier_snapshots_path),
            "scoring_metadata_path": str(scoring_metadata_path),
            "baseline_readiness": scoring_metadata.get("method", {}).get(
                "baseline_readiness",
                "",
            ),
        },
        "outputs": {
            "figure_path": str(figure_path),
            "market_count": int(watchlist["market_id"].nunique()),
            "bucket_count": bucket_count,
            "token_snapshot_count": int(len(market)),
            "wallet_snapshot_count": int(len(wallets)),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "limitations": {
            "read_only_history_only": True,
            "not_a_strategy_or_performance_figure": True,
            "requires_repeated_closed_buckets_for_alert_interpretation": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_llms": True,
            "does_not_use_ml": True,
            "does_not_send_orders": True,
        },
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return RollingFigureResult(
        figure_path=figure_path,
        metadata_path=metadata_path,
        market_count=int(watchlist["market_id"].nunique()),
        bucket_count=bucket_count,
        token_snapshot_count=len(market),
        wallet_snapshot_count=len(wallets),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--watchlist", type=Path, default=LIVE_WATCHLIST_OUTPUT)
    parser.add_argument("--market-snapshots", type=Path, default=LIVE_MARKET_SNAPSHOTS_OUTPUT)
    parser.add_argument("--wallet-tier-snapshots", type=Path, default=LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT)
    parser.add_argument("--scoring-metadata", type=Path, default=LIVE_SCORING_METADATA_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=ROLLING_FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=ROLLING_FIGURE_METADATA_OUTPUT)
    args = parser.parse_args(argv)

    try:
        result = generate_polymarket_rolling_history_figure(
            watchlist_path=args.watchlist,
            market_snapshots_path=args.market_snapshots,
            wallet_tier_snapshots_path=args.wallet_tier_snapshots,
            scoring_metadata_path=args.scoring_metadata,
            figure_path=args.figure_output,
            metadata_path=args.metadata_output,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _read_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"{label} file not found: {path}")
    frame = pd.read_csv(path)
    if frame.empty:
        raise ValueError(f"{label} file is empty: {path}")
    return frame


def _read_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _market_label(row: pd.Series) -> str:
    question = _shorten(str(row.get("question") or row["market_id"]))
    token_id = str(row["token_id"])
    return f"{question} | {token_id[:6]}"


def _shorten(value: str, max_length: int = 38) -> str:
    text = str(value)
    if len(text) <= max_length:
        return text
    return text[: max_length - 1] + "..."


if __name__ == "__main__":
    raise SystemExit(main())
