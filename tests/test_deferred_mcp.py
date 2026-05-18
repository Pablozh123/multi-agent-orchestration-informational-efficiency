"""Tests for the deterministic-path freeze of the MCP server."""
from __future__ import annotations

import pytest

from operations.mcp import thesis_mcp_server


@pytest.mark.asyncio
async def test_run_full_analysis_is_deferred() -> None:
    """The active MCP path must not trigger multi-agent analysis."""
    with pytest.raises(RuntimeError, match=thesis_mcp_server.DEFERRED_MESSAGE):
        await thesis_mcp_server.run_full_analysis("Should not run.")


def test_mcp_main_is_deferred() -> None:
    """The active MCP module must not start a server."""
    with pytest.raises(RuntimeError, match=thesis_mcp_server.DEFERRED_MESSAGE):
        thesis_mcp_server.main()
