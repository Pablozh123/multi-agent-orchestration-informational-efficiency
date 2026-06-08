"""Build a local wallet graph and bubblemap-style dashboard from public activity."""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.collectors.polymarket_public_activity import (
    PUBLIC_ACTIVITY_OUTPUT,
    validate_public_activity,
)


GRAPH_NODES_OUTPUT = RESULTS_DIR / "wallet_graph_nodes.csv"
GRAPH_EDGES_OUTPUT = RESULTS_DIR / "wallet_graph_edges.csv"
GRAPH_METRICS_OUTPUT = RESULTS_DIR / "wallet_graph_metrics.csv"
GRAPH_DASHBOARD_OUTPUT = RESULTS_DIR / "wallet_graph_dashboard.html"
GRAPH_METADATA_OUTPUT = RESULTS_DIR / "wallet_graph_metadata.json"

NODE_COLUMNS: tuple[str, ...] = (
    "proxy_wallet",
    "display_label",
    "total_usdc_size",
    "trade_count",
    "buy_count",
    "sell_count",
    "first_seen_utc",
    "last_seen_utc",
    "market_count",
    "topic_theme",
    "bubble_size",
    "claim_scope",
)

EDGE_COLUMNS: tuple[str, ...] = (
    "source_wallet",
    "target_wallet",
    "edge_type",
    "market_id",
    "shared_market_count",
    "shared_bucket_count",
    "shared_topic_count",
    "weight",
    "evidence_ref",
    "claim_scope",
)

METRIC_COLUMNS: tuple[str, ...] = (
    "proxy_wallet",
    "degree",
    "weighted_degree",
    "total_usdc_size",
    "trade_count",
    "market_count",
    "cluster_label",
    "claim_scope",
)


@dataclass(frozen=True)
class WalletGraphResult:
    nodes_path: Path
    edges_path: Path
    metrics_path: Path
    dashboard_path: Path
    metadata_path: Path
    node_count: int
    edge_count: int

    def to_dict(self) -> dict[str, int | str]:
        return {
            "nodes_path": str(self.nodes_path),
            "edges_path": str(self.edges_path),
            "metrics_path": str(self.metrics_path),
            "dashboard_path": str(self.dashboard_path),
            "metadata_path": str(self.metadata_path),
            "node_count": self.node_count,
            "edge_count": self.edge_count,
        }


def build_wallet_graph(
    activity: pd.DataFrame,
    *,
    bucket_minutes: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return wallet nodes, edges, and graph metrics."""

    if bucket_minutes < 1:
        raise ValueError("bucket_minutes must be >= 1")
    rows = validate_public_activity(activity)
    if rows.empty:
        return (
            pd.DataFrame(columns=NODE_COLUMNS),
            pd.DataFrame(columns=EDGE_COLUMNS),
            pd.DataFrame(columns=METRIC_COLUMNS),
        )
    rows = rows.copy()
    rows["timestamp"] = pd.to_datetime(rows["timestamp_utc"], utc=True, errors="raise")
    rows["bucket"] = rows["timestamp"].dt.floor(f"{bucket_minutes}min")
    nodes = _build_nodes(rows)
    edges = _build_edges(rows)
    metrics = _build_metrics(nodes, edges)
    return nodes, edges, metrics


def generate_wallet_graph_outputs(
    *,
    activity_path: Path = PUBLIC_ACTIVITY_OUTPUT,
    nodes_path: Path = GRAPH_NODES_OUTPUT,
    edges_path: Path = GRAPH_EDGES_OUTPUT,
    metrics_path: Path = GRAPH_METRICS_OUTPUT,
    dashboard_path: Path = GRAPH_DASHBOARD_OUTPUT,
    metadata_path: Path = GRAPH_METADATA_OUTPUT,
    bucket_minutes: int = 5,
) -> WalletGraphResult:
    """Write graph CSVs, local dashboard, and metadata."""

    if not activity_path.exists():
        raise FileNotFoundError(f"public wallet activity not found: {activity_path}")
    activity = pd.read_csv(activity_path, keep_default_na=False)
    nodes, edges, metrics = build_wallet_graph(activity, bucket_minutes=bucket_minutes)
    for path, frame in (
        (nodes_path, nodes),
        (edges_path, edges),
        (metrics_path, metrics),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)
    _write_dashboard(nodes, edges, metrics, dashboard_path)
    metadata = _metadata(
        activity=activity,
        nodes=nodes,
        edges=edges,
        activity_path=activity_path,
        nodes_path=nodes_path,
        edges_path=edges_path,
        metrics_path=metrics_path,
        dashboard_path=dashboard_path,
        bucket_minutes=bucket_minutes,
    )
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return WalletGraphResult(
        nodes_path=nodes_path,
        edges_path=edges_path,
        metrics_path=metrics_path,
        dashboard_path=dashboard_path,
        metadata_path=metadata_path,
        node_count=int(len(nodes)),
        edge_count=int(len(edges)),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activity", type=Path, default=PUBLIC_ACTIVITY_OUTPUT)
    parser.add_argument("--nodes-output", type=Path, default=GRAPH_NODES_OUTPUT)
    parser.add_argument("--edges-output", type=Path, default=GRAPH_EDGES_OUTPUT)
    parser.add_argument("--metrics-output", type=Path, default=GRAPH_METRICS_OUTPUT)
    parser.add_argument("--dashboard-output", type=Path, default=GRAPH_DASHBOARD_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=GRAPH_METADATA_OUTPUT)
    parser.add_argument("--bucket-minutes", type=int, default=5)
    args = parser.parse_args(argv)
    try:
        result = generate_wallet_graph_outputs(
            activity_path=args.activity,
            nodes_path=args.nodes_output,
            edges_path=args.edges_output,
            metrics_path=args.metrics_output,
            dashboard_path=args.dashboard_output,
            metadata_path=args.metadata_output,
            bucket_minutes=args.bucket_minutes,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _build_nodes(rows: pd.DataFrame) -> pd.DataFrame:
    grouped = rows.groupby("proxy_wallet", as_index=False).agg(
        total_usdc_size=("usdc_size", "sum"),
        trade_count=("proxy_wallet", "size"),
        buy_count=("side", lambda value: int((value == "BUY").sum())),
        sell_count=("side", lambda value: int((value == "SELL").sum())),
        first_seen_utc=("timestamp", "min"),
        last_seen_utc=("timestamp", "max"),
        market_count=("market_id", "nunique"),
        topic_theme=("event_slug", _mode_text),
        display_label=("pseudonym", _display_label),
    )
    grouped["display_label"] = grouped.apply(
        lambda row: row["display_label"] or row["proxy_wallet"],
        axis=1,
    )
    max_amount = max(float(grouped["total_usdc_size"].max()), 1.0)
    grouped["bubble_size"] = grouped["total_usdc_size"].apply(
        lambda value: round(18.0 + 42.0 * math.sqrt(float(value) / max_amount), 3)
    )
    grouped["first_seen_utc"] = grouped["first_seen_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    grouped["last_seen_utc"] = grouped["last_seen_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    grouped["claim_scope"] = "public_wallet_graph_forensic_review_only"
    return grouped.loc[:, list(NODE_COLUMNS)].sort_values(
        ["total_usdc_size", "proxy_wallet"],
        ascending=[False, True],
    ).reset_index(drop=True)


def _build_edges(rows: pd.DataFrame) -> pd.DataFrame:
    edge_map: dict[tuple[str, str, str], dict[str, object]] = {}
    for market_id, market_group in rows.groupby("market_id", sort=True):
        wallets = sorted(set(market_group["proxy_wallet"].astype(str)))
        for left, right in itertools.combinations(wallets, 2):
            key = (left, right, str(market_id))
            edge_map[key] = {
                "source_wallet": left,
                "target_wallet": right,
                "edge_type": "shared_market",
                "market_id": str(market_id),
                "shared_market_count": 1,
                "shared_bucket_count": 0,
                "shared_topic_count": 0,
                "weight": 1.0,
                "evidence_ref": "shared public Polymarket market activity",
                "claim_scope": "public_wallet_graph_forensic_review_only",
            }
    for (market_id, bucket), bucket_group in rows.groupby(["market_id", "bucket"], sort=True):
        wallets = sorted(set(bucket_group["proxy_wallet"].astype(str)))
        for left, right in itertools.combinations(wallets, 2):
            key = (left, right, str(market_id))
            edge = edge_map.setdefault(
                key,
                {
                    "source_wallet": left,
                    "target_wallet": right,
                    "edge_type": "shared_bucket",
                    "market_id": str(market_id),
                    "shared_market_count": 1,
                    "shared_bucket_count": 0,
                    "shared_topic_count": 0,
                    "weight": 0.0,
                    "evidence_ref": "shared public Polymarket time bucket activity",
                    "claim_scope": "public_wallet_graph_forensic_review_only",
                },
            )
            edge["shared_bucket_count"] = int(edge["shared_bucket_count"]) + 1
            edge["edge_type"] = "shared_market_and_bucket"
    for edge in edge_map.values():
        edge["weight"] = float(edge["shared_market_count"]) + 2.0 * float(
            edge["shared_bucket_count"]
        )
    edges = pd.DataFrame(edge_map.values(), columns=EDGE_COLUMNS)
    if edges.empty:
        return pd.DataFrame(columns=EDGE_COLUMNS)
    return edges.sort_values(["weight", "source_wallet", "target_wallet"], ascending=[False, True, True]).reset_index(drop=True)


def _build_metrics(nodes: pd.DataFrame, edges: pd.DataFrame) -> pd.DataFrame:
    degree: dict[str, int] = {wallet: 0 for wallet in nodes["proxy_wallet"].astype(str)}
    weighted: dict[str, float] = {wallet: 0.0 for wallet in nodes["proxy_wallet"].astype(str)}
    for edge in edges.to_dict(orient="records"):
        left = str(edge["source_wallet"])
        right = str(edge["target_wallet"])
        weight = float(edge["weight"])
        degree[left] = degree.get(left, 0) + 1
        degree[right] = degree.get(right, 0) + 1
        weighted[left] = weighted.get(left, 0.0) + weight
        weighted[right] = weighted.get(right, 0.0) + weight
    rows = []
    for node in nodes.to_dict(orient="records"):
        wallet = str(node["proxy_wallet"])
        rows.append(
            {
                "proxy_wallet": wallet,
                "degree": degree.get(wallet, 0),
                "weighted_degree": round(weighted.get(wallet, 0.0), 6),
                "total_usdc_size": node["total_usdc_size"],
                "trade_count": node["trade_count"],
                "market_count": node["market_count"],
                "cluster_label": _cluster_label(degree.get(wallet, 0), weighted.get(wallet, 0.0)),
                "claim_scope": "public_wallet_graph_forensic_review_only",
            }
        )
    return pd.DataFrame(rows, columns=METRIC_COLUMNS).sort_values(
        ["weighted_degree", "total_usdc_size"],
        ascending=[False, False],
    ).reset_index(drop=True)


def _write_dashboard(
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
    metrics: pd.DataFrame,
    dashboard_path: Path,
) -> None:
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    node_positions = _node_positions(nodes)
    svg_edges = _svg_edges(edges, node_positions)
    svg_nodes = _svg_nodes(nodes, metrics, node_positions)
    node_rows = _table_rows(
        nodes.head(50),
        ("proxy_wallet", "display_label", "total_usdc_size", "trade_count", "market_count", "topic_theme"),
    )
    edge_rows = _table_rows(
        edges.head(50),
        ("source_wallet", "target_wallet", "edge_type", "market_id", "shared_bucket_count", "weight"),
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Wallet Graph Forensic Dashboard</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 28px; color: #17202a; }}
    .note {{ background: #fff7e6; border: 1px solid #f0d08a; padding: 12px; border-radius: 6px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(3, minmax(120px, 1fr)); gap: 12px; }}
    .metric {{ border: 1px solid #d7dde5; border-radius: 6px; padding: 12px; background: #f8fafc; }}
    .metric strong {{ display: block; font-size: 22px; margin-top: 4px; }}
    svg {{ width: 100%; max-width: 980px; border: 1px solid #d7dde5; border-radius: 8px; background: #fbfcfe; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; font-size: 12px; }}
    th, td {{ border: 1px solid #d7dde5; padding: 6px; text-align: left; vertical-align: top; word-break: break-all; }}
    th {{ background: #eef2f7; }}
  </style>
</head>
<body>
  <h1>Wallet Graph Forensic Dashboard</h1>
  <p class="note">Local forensic view with public Polymarket wallet addresses. This is a review aid, not a misconduct finding, not a causal test, and not a trading signal.</p>
  <section class="metrics">
    <div class="metric">Wallet nodes<strong>{len(nodes)}</strong></div>
    <div class="metric">Graph edges<strong>{len(edges)}</strong></div>
    <div class="metric">Wallet addresses<strong>visible</strong></div>
  </section>
  <h2>Bubblemap View</h2>
  <svg viewBox="0 0 1000 680" role="img" aria-label="Wallet graph bubblemap">
    {svg_edges}
    {svg_nodes}
  </svg>
  <h2>Wallet Nodes</h2>
  <table><thead><tr><th>Wallet</th><th>Label</th><th>Total USD</th><th>Trades</th><th>Markets</th><th>Theme</th></tr></thead><tbody>{node_rows}</tbody></table>
  <h2>Wallet Edges</h2>
  <table><thead><tr><th>Source</th><th>Target</th><th>Type</th><th>Market</th><th>Shared buckets</th><th>Weight</th></tr></thead><tbody>{edge_rows}</tbody></table>
</body>
</html>
"""
    dashboard_path.write_text(html, encoding="utf-8")


def _node_positions(nodes: pd.DataFrame) -> dict[str, tuple[float, float]]:
    count = max(len(nodes), 1)
    center_x, center_y = 500.0, 330.0
    radius = 230.0
    positions: dict[str, tuple[float, float]] = {}
    for index, wallet in enumerate(nodes["proxy_wallet"].astype(str).tolist()):
        angle = (2.0 * math.pi * index) / count
        positions[wallet] = (center_x + radius * math.cos(angle), center_y + radius * math.sin(angle))
    return positions


def _svg_edges(edges: pd.DataFrame, positions: dict[str, tuple[float, float]]) -> str:
    lines = []
    for edge in edges.to_dict(orient="records"):
        left = positions.get(str(edge["source_wallet"]))
        right = positions.get(str(edge["target_wallet"]))
        if left is None or right is None:
            continue
        width = min(7.0, 1.0 + float(edge["weight"]))
        lines.append(
            f'<line x1="{left[0]:.1f}" y1="{left[1]:.1f}" x2="{right[0]:.1f}" y2="{right[1]:.1f}" stroke="#91a6b8" stroke-width="{width:.1f}" opacity="0.55" />'
        )
    return "\n    ".join(lines)


def _svg_nodes(
    nodes: pd.DataFrame,
    metrics: pd.DataFrame,
    positions: dict[str, tuple[float, float]],
) -> str:
    metric_lookup = {
        str(row["proxy_wallet"]): row for row in metrics.to_dict(orient="records")
    }
    circles = []
    for node in nodes.to_dict(orient="records"):
        wallet = str(node["proxy_wallet"])
        x, y = positions[wallet]
        size = float(node["bubble_size"])
        metric = metric_lookup.get(wallet, {})
        colour = "#d95f59" if metric.get("cluster_label") == "shared_bucket_cluster" else "#3d7ea6"
        circles.append(
            f"""<g>
      <circle cx="{x:.1f}" cy="{y:.1f}" r="{size:.1f}" fill="{colour}" opacity="0.82" />
      <title>{escape(wallet)} | USD {float(node["total_usdc_size"]):.2f} | trades {int(node["trade_count"])}</title>
      <text x="{x:.1f}" y="{y + size + 14:.1f}" text-anchor="middle" font-size="10">{escape(wallet[:8])}...</text>
    </g>"""
        )
    return "\n    ".join(circles)


def _table_rows(frame: pd.DataFrame, columns: Sequence[str]) -> str:
    if frame.empty:
        return ""
    rows = []
    for item in frame.loc[:, list(columns)].to_dict(orient="records"):
        cells = "".join(f"<td>{escape(_format_cell(item[column]))}</td>" for column in columns)
        rows.append(f"<tr>{cells}</tr>")
    return "\n".join(rows)


def _format_cell(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _mode_text(values: pd.Series) -> str:
    clean = [str(value).strip() for value in values if str(value).strip()]
    if not clean:
        return "unknown"
    return pd.Series(clean).mode().iloc[0]


def _display_label(values: pd.Series) -> str:
    for value in values:
        text = str(value).strip()
        if text:
            return text
    return ""


def _cluster_label(degree: int, weighted_degree: float) -> str:
    if degree <= 0:
        return "isolated_wallet"
    if weighted_degree >= 3:
        return "shared_bucket_cluster"
    return "shared_market_context"


def _metadata(
    *,
    activity: pd.DataFrame,
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
    activity_path: Path,
    nodes_path: Path,
    edges_path: Path,
    metrics_path: Path,
    dashboard_path: Path,
    bucket_minutes: int,
) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "monitor_wallet_graph",
            "edge_rules": ["shared_market", "shared_time_bucket"],
            "bucket_minutes": bucket_minutes,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
        },
        "inputs": {
            "activity_path": str(activity_path),
            "activity_rows": int(len(activity)),
        },
        "outputs": {
            "nodes_path": str(nodes_path),
            "edges_path": str(edges_path),
            "metrics_path": str(metrics_path),
            "dashboard_path": str(dashboard_path),
            "node_count": int(len(nodes)),
            "edge_count": int(len(edges)),
            "contains_public_wallet_addresses": True,
            "contains_order_instructions": False,
        },
        "limitations": {
            "local_forensic_dashboard_only": True,
            "not_a_funding_graph": True,
            "not_a_identity_cluster": True,
            "not_a_misconduct_finding": True,
        },
    }


if __name__ == "__main__":
    raise SystemExit(main())
