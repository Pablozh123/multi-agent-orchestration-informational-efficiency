# Legacy Prompt Inventory

This directory preserves prompt and instruction files that predate the current
deterministic-first architecture.

Files were moved here because their original versions encouraged one or more of
the following patterns:

- Agent-first or multi-agent orchestration before the deterministic core is
  complete.
- MCP or Claude Desktop integration before deterministic outputs are stable.
- Prompt-side statistical calculation.
- Arbitrary whale thresholds.
- RCP probability use without explicit transformation requirements.
- Granger or wallet-timing language that could be read as causal proof.
- Broad Claude settings that enabled old agent-team or MCP workflows.

The active source of truth is now:

- `AGENTS.md`
- `ARCHITECTURE_DECISIONS.md`
- `PROJECT_CONTEXT.md`

Legacy prompts are kept for auditability and historical context only. Do not
invoke them for current thesis work unless they are explicitly reviewed and
rewritten to obey the active architecture.
