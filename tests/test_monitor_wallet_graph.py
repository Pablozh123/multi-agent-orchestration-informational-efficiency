from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.monitor_wallet_graph import build_wallet_graph, generate_wallet_graph_outputs
from operations.collectors.polymarket_public_activity import PUBLIC_ACTIVITY_COLUMNS


def test_build_wallet_graph_connects_wallets_in_same_bucket() -> None:
    nodes, edges, metrics = build_wallet_graph(_activity_rows())

    assert len(nodes) == 3
    assert len(edges) == 1
    edge = edges.iloc[0]
    assert edge["edge_type"] == "shared_market_and_bucket"
    assert edge["shared_bucket_count"] == 1
    assert edge["weight"] == pytest.approx(3.0)
    assert set(metrics["cluster_label"]) == {"shared_bucket_cluster", "isolated_wallet"}


def test_build_wallet_graph_leaves_single_wallet_isolated() -> None:
    nodes, edges, metrics = build_wallet_graph(_activity_rows().iloc[[0]])

    assert len(nodes) == 1
    assert edges.empty
    assert metrics.iloc[0]["cluster_label"] == "isolated_wallet"


def test_generate_wallet_graph_outputs_writes_dashboard_with_addresses(tmp_path: Path) -> None:
    activity_path = tmp_path / "activity.csv"
    _activity_rows().to_csv(activity_path, index=False)

    result = generate_wallet_graph_outputs(
        activity_path=activity_path,
        nodes_path=tmp_path / "nodes.csv",
        edges_path=tmp_path / "edges.csv",
        metrics_path=tmp_path / "metrics.csv",
        dashboard_path=tmp_path / "dashboard.html",
        metadata_path=tmp_path / "metadata.json",
    )

    dashboard = result.dashboard_path.read_text(encoding="utf-8")
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    assert "Wallet Graph Forensic Dashboard" in dashboard
    assert "0x1111111111111111111111111111111111111111" in dashboard
    assert "order instructions" not in dashboard.lower()
    assert metadata["outputs"]["contains_public_wallet_addresses"] is True
    assert metadata["outputs"]["contains_order_instructions"] is False


def _activity_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _row("0x" + "1" * 40, "2026-05-26T10:00:00Z", 500.0, "market_a"),
            _row("0x" + "2" * 40, "2026-05-26T10:01:00Z", 300.0, "market_a"),
            _row("0x" + "3" * 40, "2026-05-26T11:00:00Z", 50.0, "market_b"),
        ],
        columns=PUBLIC_ACTIVITY_COLUMNS,
    )


def _row(wallet: str, timestamp: str, amount: float, market_id: str) -> dict[str, object]:
    return {
        "collected_at_utc": "2026-05-26T12:00:00Z",
        "source_name": "toy",
        "market_id": market_id,
        "condition_id": market_id,
        "timestamp_utc": timestamp,
        "proxy_wallet": wallet,
        "side": "BUY",
        "usdc_size": amount,
        "price": 0.5,
        "outcome": "YES",
        "transaction_hash": "0x" + "a" * 64,
        "name": "",
        "pseudonym": "",
        "title": "toy market",
        "slug": "toy-market",
        "event_slug": "toy-event",
        "claim_scope": "public_polymarket_wallet_activity_forensic_review",
    }
