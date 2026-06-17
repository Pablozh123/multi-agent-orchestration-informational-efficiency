"""Open or describe the read-only Agenten-Review-Queue dashboard.

Mirrors ``operations/tools/monitor_dashboard_launcher.py`` but for the separate
agent-review-queue part of the site: it (re)generates the static page from the
bounded MCP outputs via the read-only review agents (deterministic mock LLM by
default) and opens it locally. It performs no trade, no order, and no network
call beyond opening a local ``file://`` URL in the browser.
"""
from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from operations.analysis.agent_review_queue_dashboard import (
    DASHBOARD_OUTPUT,
    generate_agent_review_queue_dashboard,
)


@dataclass(frozen=True)
class LaunchInfo:
    """Structured description of the launched agent-review-queue dashboard."""

    dashboard_path: Path
    dashboard_uri: str
    case_count: int
    high_count: int
    medium_count: int
    low_count: int
    backend: str
    opened_browser: bool

    def to_dict(self) -> dict[str, bool | int | str]:
        return {
            "dashboard_path": str(self.dashboard_path),
            "dashboard_uri": self.dashboard_uri,
            "case_count": self.case_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "backend": self.backend,
            "opened_browser": self.opened_browser,
        }


def launch_agent_review_queue_dashboard(
    *,
    open_browser: bool = True,
    dashboard_path: Path = DASHBOARD_OUTPUT,
) -> LaunchInfo:
    """Regenerate the page from bounded outputs and (optionally) open it."""
    result = generate_agent_review_queue_dashboard(dashboard_path=dashboard_path)
    uri = result.dashboard_path.resolve().as_uri()
    opened = False
    if open_browser:
        opened = webbrowser.open(uri)
    return LaunchInfo(
        dashboard_path=result.dashboard_path,
        dashboard_uri=uri,
        case_count=result.case_count,
        high_count=result.high_count,
        medium_count=result.medium_count,
        low_count=result.low_count,
        backend=result.backend,
        opened_browser=opened,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Regenerate and describe the page without opening a browser.",
    )
    parser.add_argument("--dashboard-output", type=Path, default=DASHBOARD_OUTPUT)
    args = parser.parse_args(argv)

    try:
        info = launch_agent_review_queue_dashboard(
            open_browser=not args.no_browser,
            dashboard_path=args.dashboard_output,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(info.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
