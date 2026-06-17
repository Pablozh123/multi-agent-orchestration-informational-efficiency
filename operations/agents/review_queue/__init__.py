"""Stage 3 multi-agent scaffold (read-only, mock-LLM, audited).

This package is a *scaffold* that belongs in the separate website repo. It sits
strictly on top of the Stage 2 read-only MCP tool layer and never computes any
metric itself. See ``STAGE3_HANDOFF.md`` for productionization and the
activation gate.

Hard, non-negotiable boundaries enforced throughout this package (mirrored from
AGENTS.md, ARCHITECTURE_DECISIONS, AGENT_TOOL_BLUEPRINT.md, and the
``future_agent_contract``):

    - Agents NEVER calculate metrics. They only read bounded summaries through
      the four MCP tools (see ``mcp_client``).
    - The only recommendations are *review* actions:
      ``{"watch", "check_source", "escalate_human"}``. Never buy/sell, never an
      order, never investment advice, never profitability.
    - No wallet addresses are emitted. The MCP layer redacts ``0x``+40-hex
      addresses; agents additionally re-assert this on their own outputs.
    - Every LLM call is audited (role, prompt_hash, ts_utc).
    - No real network / API calls. The LLM is a deterministic mock by default.
"""

from __future__ import annotations

#: The complete closed set of review recommendations the whole agent layer may
#: ever emit. Imported by every module that produces a recommendation so the
#: set cannot silently drift. There is intentionally no trade/order verb here.
ALLOWED_RECOMMENDATIONS = ("watch", "check_source", "escalate_human")

#: Closed set of case priorities the Orchestrator assigns.
ALLOWED_PRIORITIES = ("high", "medium", "low")

#: Field-name fragments that must NEVER appear as keys anywhere in agent output.
#: Used as a defensive guard (tests assert the queue contains none of these).
FORBIDDEN_OUTPUT_KEY_FRAGMENTS = (
    "order",
    "trade",
    "buy",
    "sell",
    "profit",
    "pnl",
    "position_size",
    "wallet_address",
)

__all__ = [
    "ALLOWED_RECOMMENDATIONS",
    "ALLOWED_PRIORITIES",
    "FORBIDDEN_OUTPUT_KEY_FRAGMENTS",
]
