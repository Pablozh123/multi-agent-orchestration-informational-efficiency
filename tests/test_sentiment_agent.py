"""Tests for the deterministic-path freeze of the old sentiment agent."""
from __future__ import annotations

import pytest

from operations.agents import sentiment_agent


def test_sentiment_agent_interpretation_is_deferred() -> None:
    """The active sentiment-agent path must not run before approval."""
    with pytest.raises(RuntimeError, match=sentiment_agent.DEFERRED_MESSAGE):
        sentiment_agent.run_interpretation("Should not run.")


def test_sentiment_agent_main_is_deferred() -> None:
    """Command-style sentiment-agent execution is also blocked."""
    with pytest.raises(RuntimeError, match=sentiment_agent.DEFERRED_MESSAGE):
        sentiment_agent.main()
