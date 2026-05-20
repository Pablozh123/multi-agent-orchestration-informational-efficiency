"""Tests for the deterministic-path freeze of the old whale agent."""
from __future__ import annotations

import pytest

from operations.agents import whale_agent


def test_whale_agent_interpretation_is_deferred() -> None:
    """The active whale-agent path must not run before approval."""
    with pytest.raises(RuntimeError, match=whale_agent.DEFERRED_MESSAGE):
        whale_agent.run_interpretation("Should not run.")


def test_whale_agent_main_is_deferred() -> None:
    """Command-style whale-agent execution is also blocked."""
    with pytest.raises(RuntimeError, match=whale_agent.DEFERRED_MESSAGE):
        whale_agent.main()
