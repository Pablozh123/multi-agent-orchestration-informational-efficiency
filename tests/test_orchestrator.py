"""Tests for the deterministic-path freeze of the old orchestrator."""
from __future__ import annotations

import pytest

from operations.agents import orchestrator


@pytest.mark.asyncio
async def test_run_analysis_is_deferred() -> None:
    """The active orchestrator must not run multi-agent analysis."""
    with pytest.raises(RuntimeError, match=orchestrator.DEFERRED_MESSAGE):
        await orchestrator.run_analysis("Should not run before deterministic core.")


def test_orchestrator_main_is_deferred() -> None:
    """Command-style orchestrator execution is also blocked."""
    with pytest.raises(RuntimeError, match=orchestrator.DEFERRED_MESSAGE):
        orchestrator.main()
