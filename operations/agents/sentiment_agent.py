"""Deferred sentiment-agent entry point.

The original implementation is preserved at:
    legacy/deferred_agents/sentiment_agent.py

Sentiment interpretation agents are deferred until bounded summary contracts,
`llm_audit_log` usage, and deterministic backtest outputs are explicitly
approved. This active module intentionally exposes only a runtime guard.
"""
from __future__ import annotations

from typing import NoReturn


DEFERRED_MESSAGE = "Deferred until deterministic analysis core is complete"


def run_interpretation(*args: object, **kwargs: object) -> NoReturn:
    """Block accidental sentiment-agent execution from the active code path."""
    raise RuntimeError(DEFERRED_MESSAGE)


def main() -> NoReturn:
    """Block command-style sentiment-agent execution from the active code path."""
    raise RuntimeError(DEFERRED_MESSAGE)


if __name__ == "__main__":
    main()
