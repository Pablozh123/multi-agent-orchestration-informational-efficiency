"""Tests for the deterministic-path freeze of the old market agent."""
from __future__ import annotations

import pytest

from operations.agents import market_agent


def test_market_agent_interpretation_is_deferred() -> None:
    """The active market-agent path must not run before approval."""
    with pytest.raises(RuntimeError, match=market_agent.DEFERRED_MESSAGE):
        market_agent.run_interpretation("Should not run.")


def test_market_agent_main_is_deferred() -> None:
    """Command-style market-agent execution is also blocked."""
    with pytest.raises(RuntimeError, match=market_agent.DEFERRED_MESSAGE):
        market_agent.main()
