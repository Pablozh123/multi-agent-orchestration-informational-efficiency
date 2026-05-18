---
name: fastmcp-server
description: Deferred MCP reference for this thesis repository. Do not implement or extend MCP before the deterministic core is approved.
---

Status: active
Source of truth: AGENTS.md and ARCHITECTURE_DECISIONS.md
Role: deferred MCP reference
Allowed scope: interpretation only, no deterministic calculations

# MCP Deferred

MCP is not part of the current implementation priority for this repository.
The deterministic analysis core must be stable, tested, and explicitly approved
before any MCP demo layer is implemented or extended.

## Rules

- Do not create MCP servers.
- Do not add Claude Desktop integration.
- Do not expose raw database tables through MCP tools.
- Do not use MCP as a statistical calculation path.
- If asked for MCP work before approval, point back to `AGENTS.md` and
  `ARCHITECTURE_DECISIONS.md`.
