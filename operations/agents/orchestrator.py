"""Deferred multi-agent orchestrator entry point.

The original implementation is preserved at:
    legacy/deferred_agents/orchestrator.py

This active module intentionally exposes only a hard runtime guard. Multi-agent
analysis is deferred until H1, H2, and H3 deterministic outputs exist and are
validated.
"""
from __future__ import annotations

from pathlib import Path
from typing import NoReturn


DEFERRED_MESSAGE = "Deferred until deterministic analysis core is complete"
CHANGELOG_DIR = Path("logs/changelog")


async def run_analysis(question: str, run_id: str | None = None) -> NoReturn:
    """Block accidental multi-agent execution from the active code path."""
    raise RuntimeError(DEFERRED_MESSAGE)


def main() -> NoReturn:
    """Block command-style orchestrator execution from the active code path."""
    raise RuntimeError(DEFERRED_MESSAGE)


if __name__ == "__main__":
    main()
