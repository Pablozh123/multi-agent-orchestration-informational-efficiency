"""Open or describe the read-only Polymarket monitor dashboard."""
from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from operations.analysis.monitor_v2_dashboard import (
    DASHBOARD_METADATA_OUTPUT,
    DASHBOARD_OUTPUT,
)


@dataclass(frozen=True)
class DashboardLaunchInfo:
    """Structured description of the local dashboard entry point."""

    dashboard_path: Path
    dashboard_uri: str
    metadata_path: Path
    market_count: int
    bucket_count: int
    alert_count: int
    baseline_readiness: str
    opened_browser: bool

    def to_dict(self) -> dict[str, bool | int | str]:
        """Return a JSON-friendly launch summary."""

        return {
            "dashboard_path": str(self.dashboard_path),
            "dashboard_uri": self.dashboard_uri,
            "metadata_path": str(self.metadata_path),
            "market_count": self.market_count,
            "bucket_count": self.bucket_count,
            "alert_count": self.alert_count,
            "baseline_readiness": self.baseline_readiness,
            "opened_browser": self.opened_browser,
            "read_only": True,
            "collects_data": False,
            "writes_database": False,
            "uses_agents_or_mcp": False,
            "contains_order_instructions": False,
        }


def describe_dashboard(
    *,
    dashboard_path: Path = DASHBOARD_OUTPUT,
    metadata_path: Path = DASHBOARD_METADATA_OUTPUT,
    open_browser: bool = False,
) -> DashboardLaunchInfo:
    """Validate and optionally open the local monitor dashboard."""

    if not dashboard_path.exists():
        raise FileNotFoundError(f"dashboard file not found: {dashboard_path}")
    if not metadata_path.exists():
        raise FileNotFoundError(f"dashboard metadata file not found: {metadata_path}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    outputs = metadata.get("outputs", {})
    if outputs.get("contains_wallet_addresses") is True:
        raise ValueError("dashboard metadata reports wallet-address exposure")
    if outputs.get("contains_order_instructions") is True:
        raise ValueError("dashboard metadata reports order instructions")

    dashboard_uri = dashboard_path.resolve().as_uri()
    opened = False
    if open_browser:
        opened = webbrowser.open(dashboard_uri)

    return DashboardLaunchInfo(
        dashboard_path=dashboard_path,
        dashboard_uri=dashboard_uri,
        metadata_path=metadata_path,
        market_count=int(outputs.get("market_count", 0)),
        bucket_count=int(outputs.get("bucket_count", 0)),
        alert_count=int(outputs.get("alert_count", 0)),
        baseline_readiness=str(outputs.get("baseline_readiness", "")),
        opened_browser=opened,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dashboard", type=Path, default=DASHBOARD_OUTPUT)
    parser.add_argument("--metadata", type=Path, default=DASHBOARD_METADATA_OUTPUT)
    parser.add_argument("--open", action="store_true", dest="open_browser")
    args = parser.parse_args(argv)

    try:
        result = describe_dashboard(
            dashboard_path=args.dashboard,
            metadata_path=args.metadata,
            open_browser=args.open_browser,
        )
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
