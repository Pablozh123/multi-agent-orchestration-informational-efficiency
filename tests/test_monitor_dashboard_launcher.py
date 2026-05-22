from __future__ import annotations

import json
from pathlib import Path

import pytest

from operations.tools.monitor_dashboard_launcher import describe_dashboard, main


def test_describe_dashboard_returns_local_readonly_entry_point(tmp_path: Path) -> None:
    dashboard, metadata = _write_dashboard_files(tmp_path)

    result = describe_dashboard(dashboard_path=dashboard, metadata_path=metadata)

    assert result.dashboard_uri.startswith("file:///")
    assert result.market_count == 12
    assert result.bucket_count == 20
    assert result.alert_count == 0
    assert result.opened_browser is False
    assert result.to_dict()["collects_data"] is False
    assert result.to_dict()["uses_agents_or_mcp"] is False
    assert result.to_dict()["contains_order_instructions"] is False


def test_describe_dashboard_rejects_order_instruction_metadata(
    tmp_path: Path,
) -> None:
    dashboard, metadata = _write_dashboard_files(
        tmp_path,
        contains_order_instructions=True,
    )

    with pytest.raises(ValueError, match="order instructions"):
        describe_dashboard(dashboard_path=dashboard, metadata_path=metadata)


def test_describe_dashboard_rejects_wallet_address_metadata(tmp_path: Path) -> None:
    dashboard, metadata = _write_dashboard_files(
        tmp_path,
        contains_wallet_addresses=True,
    )

    with pytest.raises(ValueError, match="wallet-address exposure"):
        describe_dashboard(dashboard_path=dashboard, metadata_path=metadata)


def test_dashboard_launcher_cli_prints_json(tmp_path: Path, capsys) -> None:
    dashboard, metadata = _write_dashboard_files(tmp_path)

    exit_code = main(
        [
            "--dashboard",
            str(dashboard),
            "--metadata",
            str(metadata),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "dashboard_uri" in captured.out
    assert "baseline_available_zero_mad_or_non_alerting" in captured.out


def _write_dashboard_files(
    root: Path,
    *,
    contains_wallet_addresses: bool = False,
    contains_order_instructions: bool = False,
) -> tuple[Path, Path]:
    dashboard = root / "dashboard.html"
    metadata = root / "dashboard_metadata.json"
    dashboard.write_text("<!doctype html><title>dashboard</title>", encoding="utf-8")
    metadata.write_text(
        json.dumps(
            {
                "outputs": {
                    "market_count": 12,
                    "bucket_count": 20,
                    "alert_count": 0,
                    "baseline_readiness": (
                        "baseline_available_zero_mad_or_non_alerting"
                    ),
                    "contains_wallet_addresses": contains_wallet_addresses,
                    "contains_order_instructions": contains_order_instructions,
                }
            }
        ),
        encoding="utf-8",
    )
    return dashboard, metadata
