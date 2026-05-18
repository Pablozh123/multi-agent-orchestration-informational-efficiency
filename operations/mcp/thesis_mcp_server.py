"""Deferred MCP server entry point.

The original implementation is preserved at:
    legacy/deferred_mcp/thesis_mcp_server.py

MCP exposure is deferred until the deterministic H1-H3 analysis core is
complete and validated. This active module intentionally keeps only guards so no
command can accidentally start the MCP server or trigger multi-agent analysis.
"""
from __future__ import annotations

from typing import NoReturn


DEFERRED_MESSAGE = "Deferred until deterministic analysis core is complete"


async def run_full_analysis(question: str) -> NoReturn:
    """Block accidental multi-agent execution through the MCP path."""
    raise RuntimeError(DEFERRED_MESSAGE)


def main() -> NoReturn:
    """Block accidental MCP server startup from the active code path."""
    raise RuntimeError(DEFERRED_MESSAGE)


if __name__ == "__main__":
    main()
