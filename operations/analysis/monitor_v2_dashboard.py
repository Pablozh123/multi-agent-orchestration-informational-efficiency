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
from operations.analysis.run_h2_event_windows import RESULTS_DIR
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
    _assert_no_wallet_columns((watchlist, market, wallets, alerts))

    metrics = _dashboard_metrics(
        watchlist=watchlist,
        market=market,
        alerts=alerts,
        scoring_metadata=scoring_metadata,
        rolling_metadata=rolling_metadata,
    )
    html = _render_dashboard(
        watchlist=watchlist,
        market=market,
        wallets=wallets,
        alerts=alerts,
        metrics=metrics,
        figure_path=figure_path,
        source_paths={
            "watchlist": watchlist_path,
            "market snapshots": market_snapshots_path,
            "wallet-tier snapshots": wallet_tier_snapshots_path,
            "alert summary": alert_summary_path,
            "scoring metadata": scoring_metadata_path,
            "rolling metadata": rolling_metadata_path,
            "figure": figure_path,
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
        "severity_counts": outputs.get("severity_counts", {}),
        "status_counts": outputs.get("status_counts", {}),
    }


def _render_dashboard(
    *,
    watchlist: pd.DataFrame,
    market: pd.DataFrame,
    wallets: pd.DataFrame,
    alerts: pd.DataFrame,
    metrics: dict[str, Any],
    figure_path: Path,
    source_paths: dict[str, Path],
) -> str:
    latest_market = _latest_market_table(watchlist, market, wallets)
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


def _table_rows(frame: pd.DataFrame, columns: Sequence[str]) -> str:
    rows: list[str] = []
    for item in frame.loc[:, list(columns)].to_dict(orient="records"):
        cells = "".join(f"<td>{escape(_format_cell(item[column]))}</td>" for column in columns)
        rows.append(f"<tr>{cells}</tr>")
    return "\n".join(rows)


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


def _assert_no_wallet_columns(frames: Sequence[pd.DataFrame]) -> None:
    for frame in frames:
        forbidden = [column for column in frame.columns if "wallet_address" in column.lower()]
        if forbidden:
            raise ValueError(f"dashboard inputs must not contain wallet-address columns: {forbidden}")


if __name__ == "__main__":
    raise SystemExit(main())
