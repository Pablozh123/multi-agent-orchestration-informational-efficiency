"""Create simple figures from read-only Polymarket live collector outputs."""
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

from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.collectors.polymarket_readonly import (
    LIVE_MARKET_SNAPSHOTS_OUTPUT,
    LIVE_METADATA_OUTPUT,
    LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT,
    LIVE_WATCHLIST_OUTPUT,
)


FIGURE_OUTPUT = RESULTS_DIR / "monitor_v2_polymarket_live_snapshot.png"
FIGURE_METADATA_OUTPUT = RESULTS_DIR / "monitor_v2_polymarket_live_figure_metadata.json"


@dataclass(frozen=True)
class LiveFigureResult:
    """Summary of generated Polymarket live figure artifacts."""

    figure_path: Path
    metadata_path: Path
    market_count: int
    token_snapshot_count: int
    wallet_snapshot_count: int

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "market_count": self.market_count,
            "token_snapshot_count": self.token_snapshot_count,
            "wallet_snapshot_count": self.wallet_snapshot_count,
        }


def generate_polymarket_live_snapshot_figure(
    *,
    watchlist_path: Path = LIVE_WATCHLIST_OUTPUT,
    market_snapshots_path: Path = LIVE_MARKET_SNAPSHOTS_OUTPUT,
    wallet_tier_snapshots_path: Path = LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT,
    collector_metadata_path: Path = LIVE_METADATA_OUTPUT,
    figure_path: Path = FIGURE_OUTPUT,
    metadata_path: Path = FIGURE_METADATA_OUTPUT,
) -> LiveFigureResult:
    """Generate a compact figure from current read-only collector outputs."""

    watchlist = _read_csv(watchlist_path, "watchlist")
    market = _read_csv(market_snapshots_path, "market snapshots")
    wallets = _read_csv(wallet_tier_snapshots_path, "wallet-tier snapshots")
    collector_metadata = _read_optional_json(collector_metadata_path)

    merged = market.merge(
        watchlist[["market_id", "question"]],
        on="market_id",
        how="left",
    )
    merged["short_question"] = merged["question"].fillna(merged["market_id"]).map(_shorten)
    merged["midpoint"] = pd.to_numeric(merged["midpoint"], errors="coerce")
    wallets["total_observed_amount_usd"] = pd.to_numeric(
        wallets["total_observed_amount_usd"],
        errors="coerce",
    ).fillna(0.0)
    wallets["active_wallets"] = pd.to_numeric(
        wallets["active_wallets"],
        errors="coerce",
    ).fillna(0.0)
    wallet_view = wallets.merge(
        watchlist[["market_id", "question"]],
        on="market_id",
        how="left",
    )
    wallet_view["short_question"] = wallet_view["question"].fillna(wallet_view["market_id"]).map(_shorten)

    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), constrained_layout=True)

    midpoint_view = merged.sort_values(["short_question", "token_id"]).reset_index(drop=True)
    axes[0].barh(
        [f"{row.short_question} | {str(row.token_id)[0:6]}" for row in midpoint_view.itertuples()],
        midpoint_view["midpoint"],
        color="#2f6f9f",
    )
    axes[0].set_xlim(0, 1)
    axes[0].set_xlabel("Midpoint probability")
    axes[0].set_title("Read-only Polymarket live midpoint snapshot")

    x_labels = list(wallet_view["short_question"])
    axes[1].bar(x_labels, wallet_view["total_observed_amount_usd"], color="#8a5a44")
    axes[1].set_ylabel("Observed trade amount USD")
    axes[1].set_title("Aggregate public Data API trade activity in closed bucket")
    axes[1].tick_params(axis="x", rotation=20)
    for index, row in enumerate(wallet_view.itertuples()):
        axes[1].text(
            index,
            float(row.total_observed_amount_usd),
            f"wallets={int(row.active_wallets)}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    fig.savefig(figure_path, dpi=150)
    plt.close(fig)

    metadata = {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "monitor_v2_polymarket_live_snapshot_figure",
            "input_mode": "read_only_polymarket_collector_outputs",
        },
        "inputs": {
            "watchlist_path": str(watchlist_path),
            "market_snapshots_path": str(market_snapshots_path),
            "wallet_tier_snapshots_path": str(wallet_tier_snapshots_path),
            "collector_metadata_path": str(collector_metadata_path),
            "collector_source": collector_metadata.get("method", {}).get("source", ""),
            "bucket_minutes": collector_metadata.get("method", {}).get("bucket_minutes", ""),
        },
        "outputs": {
            "figure_path": str(figure_path),
            "market_count": int(watchlist["market_id"].nunique()),
            "token_snapshot_count": int(len(market)),
            "wallet_snapshot_count": int(len(wallets)),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "limitations": {
            "read_only_snapshot_only": True,
            "not_a_strategy_or_performance_figure": True,
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
    return LiveFigureResult(
        figure_path=figure_path,
        metadata_path=metadata_path,
        market_count=int(watchlist["market_id"].nunique()),
        token_snapshot_count=len(market),
        wallet_snapshot_count=len(wallets),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--watchlist", type=Path, default=LIVE_WATCHLIST_OUTPUT)
    parser.add_argument("--market-snapshots", type=Path, default=LIVE_MARKET_SNAPSHOTS_OUTPUT)
    parser.add_argument("--wallet-tier-snapshots", type=Path, default=LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT)
    parser.add_argument("--collector-metadata", type=Path, default=LIVE_METADATA_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=FIGURE_METADATA_OUTPUT)
    args = parser.parse_args(argv)

    try:
        result = generate_polymarket_live_snapshot_figure(
            watchlist_path=args.watchlist,
            market_snapshots_path=args.market_snapshots,
            wallet_tier_snapshots_path=args.wallet_tier_snapshots,
            collector_metadata_path=args.collector_metadata,
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


def _shorten(value: str, max_length: int = 42) -> str:
    text = str(value)
    if len(text) <= max_length:
        return text
    return text[: max_length - 1] + "..."


if __name__ == "__main__":
    raise SystemExit(main())
