# Legacy Inventory

This file identifies older prompts, system instructions, agent files, and
architecture notes that existed before the deterministic-first synchronization.
Nothing listed here is deleted by this documentation pass.

Latest full scan:

- `legacy/audits/LEGACY_SCAN_2026-05-20.md`

The latest scan separates active control files, archived legacy files, stale
planning documents, active code with legacy risk, prompt files, Claude-specific
tooling, and recommended cleanup order.

## Status Legend

- `keep`: still aligned with the current architecture.
- `update`: useful, but must be edited to match `AGENTS.md`.
- `move to legacy later`: should be archived or renamed after documentation is
  stable.
- `delete later`: likely removable after confirming it is not needed.
- `unclear`: needs a focused review before deciding.

## Instruction And Prompt Sources

| Path | Type | Status | Reason | Next action |
| --- | --- | --- | --- | --- |
| `AGENTS.md` | Highest-level agent instruction | keep | New source of truth for deterministic-first work. | Keep active and update only with binding project rules. |
| `PROJECT_CONTEXT.md` | Project context | keep | Current thesis and implementation context. | Keep active. |
| `ARCHITECTURE_DECISIONS.md` | Architecture decisions | keep | Binding decisions that override old prompts. | Keep active. |
| `CLAUDE.md` | Old prompt contract | move to legacy later | Contains useful validation and audit ideas, but is agent-first and model-routing heavy. | Archive or rewrite after deterministic docs settle. |
| `.planning/PROJECT.md` | Old project description | update | Describes the project as a multi-agent system and includes arbitrary whale threshold language. | Rewrite as deterministic-first project summary. |
| `.planning/ROADMAP.md` | Old roadmap | update | Marks agent/MCP phase as complete and places agents too early. | Replace with deterministic-first roadmap. |
| `.planning/phases/**` | Detailed old phase plans | unclear | Contains useful ingestion and validation notes, but many plans are agent/MCP oriented or stale. | Review before reuse; mark stale sections explicitly. |
| `.planning/**` | Old GSD planning tree | move to legacy later | Full 2026-05-20 scan found agent-first roadmap, RCP-as-probability assumptions, and fixed whale-threshold wording. | Move to `legacy/planning/` or add stale warnings in a focused cleanup commit. |
| `directives/roles/market_agent.md` | Former agent role prompt | moved to legacy | Moved to `legacy/deferred_prompts/roles/market_agent.md` on 2026-05-20. | Keep archived until interpretation layer is redesigned. |
| `directives/roles/sentiment_agent.md` | Former agent role prompt | moved to legacy | Moved to `legacy/deferred_prompts/roles/sentiment_agent.md` on 2026-05-20. | Keep archived until interpretation layer is redesigned. |
| `directives/roles/whale_agent.md` | Former agent role prompt | moved to legacy | Moved to `legacy/deferred_prompts/roles/whale_agent.md` on 2026-05-20. | Keep archived until interpretation layer is redesigned. |
| `directives/roles/orchestrator.md` | Former agent role prompt | moved to legacy | Moved to `legacy/deferred_prompts/roles/orchestrator.md` on 2026-05-20. | Keep archived until interpretation layer is redesigned. |
| `directives/roles/reviewer.md` | Former agent role prompt | moved to legacy | Moved to `legacy/deferred_prompts/roles/reviewer.md` on 2026-05-20. | Keep archived until interpretation layer is redesigned. |
| `legacy/deferred_prompts/roles/*.md` | Deferred role prompts | keep | Active `directives/roles/*.md` files were moved here on 2026-05-20. | Keep as historical prompt references until interpretation layer is redesigned. |
| `directives/methodology.md` | Methodology instruction | update | May contain useful scientific guardrails but must align with deterministic-first rules. | Review and reconcile with architecture decisions. |
| `directives/coding_standards.md` | Coding standards stub | update | Minimal stub references old reviewer-agent architecture. | Replace with repo-wide deterministic coding standards later. |
| `.claude/settings.json` | Claude Code permissions/settings | move to legacy later | Contains permissions for older MCP/server scaffolding. | Archive or replace after active workflow is decided. |
| `.claude/settings.local.json` | Local Claude settings | unclear | Local tooling may be user-specific and should not be blindly edited. | Review manually before changing. |
| `.claude/skills/brier-score/SKILL.md` | Claude skill | update | Useful formula notes, but LLM must not compute the metric. | Rewrite as interpretation-only guidance later. |
| `.claude/skills/dune-analytics/SKILL.md` | Claude skill | update | Useful source notes, but threshold framing must avoid arbitrary whale definitions. | Rewrite after wallet distribution method is defined. |
| `.claude/skills/fastmcp-server/SKILL.md` | Claude skill | move to legacy later | MCP is deferred. | Archive until MCP demo layer is approved. |
| `.claude/skills/polymarket-api/SKILL.md` | Claude skill | update | Potentially useful source notes. | Review for hidden live-call or stale API assumptions. |
| `legacy/planning/.planning/**` | Old GSD planning tree | keep | Active `.planning/**` was moved here on 2026-05-20. | Historical reference only; root `ROADMAP.md` and `GOAL.md` are active. |

## Existing Agent And MCP Code

| Path | Type | Status | Reason | Next action |
| --- | --- | --- | --- | --- |
| `operations/agents/` | Deferred guard stubs | keep | Active single-agent files now raise runtime guards; originals are archived. | Keep blocked until bounded interpretation layer is approved. |
| `operations/agents/market_agent.py` | Active guard stub | keep | Original Pydantic AI agent moved to `legacy/deferred_agents/market_agent.py`. | Keep guard. |
| `operations/agents/sentiment_agent.py` | Active guard stub | keep | Original Pydantic AI agent moved to `legacy/deferred_agents/sentiment_agent.py`. | Keep guard. |
| `operations/agents/whale_agent.py` | Active guard stub | keep | Original Pydantic AI agent moved to `legacy/deferred_agents/whale_agent.py`. | Keep guard. |
| `operations/mcp/` | FastMCP demo server | move to legacy later | MCP demo is explicitly deferred. | Do not extend or invoke. Archive later. |
| `operations/agents/orchestrator.py` | Active guard stub | keep | Multi-agent entry point now raises a runtime guard. Original code preserved in `legacy/deferred_agents/orchestrator.py`. | Keep blocked until H1-H3 deterministic outputs exist and are validated. |
| `operations/mcp/thesis_mcp_server.py` | Active guard stub | keep | MCP server startup and multi-agent MCP path now raise runtime guards. Original code preserved in `legacy/deferred_mcp/thesis_mcp_server.py`. | Keep blocked until deterministic core is complete and MCP is explicitly approved. |
| `legacy/deferred_agents/orchestrator.py` | Preserved old agent code | keep | Historical reference only; not active. | Review and rewrite before any future agent layer. |
| `legacy/deferred_mcp/thesis_mcp_server.py` | Preserved old MCP code | keep | Historical reference only; not active. | Review and rewrite before any future MCP layer. |
| `operations/audit/` | LLM audit logger | unclear | Audit logging is required later, but current implementation belongs to old agent layer. | Review when LLM interpretation layer is designed. |
| `operations/tools/db_tools.py` | Agent-facing bounded DB tools | unclear | Contains useful row limits, but exists for deferred agents/MCP. | Reuse only after deterministic query contracts are specified. |
| `operations/tools/api_clients.py` | API clients | unclear | Source clients may be useful, but hidden API calls must be controlled. | Review before reuse in deterministic ingestion. |
| `tests/test_market_agent.py` | Guard test | keep | Rewritten to verify the market-agent runtime guard. | Keep. |
| `tests/test_sentiment_agent.py` | Guard test | keep | Rewritten to verify the sentiment-agent runtime guard. | Keep. |
| `tests/test_whale_agent.py` | Guard test | keep | Rewritten to verify the whale-agent runtime guard. | Keep. |
| `legacy/changelog/*.json` | Old agent output | keep | Old `logs/changelog/*.json` moved here on 2026-05-20. | Historical reference only; not thesis evidence. |
| `legacy/data/summaries.json` | Old prompt-context output | keep | Old `data/summaries.json` moved here on 2026-05-20. | Historical reference only. |

## Deterministic Code To Keep Active

| Path | Type | Status | Reason | Next action |
| --- | --- | --- | --- | --- |
| `operations/analysis/data_inventory.py` | Deterministic inventory | keep | Supports schema and data inspection. | Keep tested. |
| `operations/analysis/brier_score.py` | Deterministic H1 baseline | keep | Supports first Brier Score baseline. | Continue with methodology and tests. |
| `operations/analysis/calibrate.py` | Deterministic calibration | keep | Supports H1 calibration analysis. | Review sample-size and interpretation limits. |
| `operations/analysis/generate_summaries.py` | Precomputed summaries | update | Useful concept, but summary definitions must be validated and avoid arbitrary thresholds. | Tighten tests and methodology before agent use. |
| `ingest/dune.py` | Dune ingest | update | Contains a fixed `WHALE_THRESHOLD_USD = 10_000.0`; acceptable only as source-filter metadata, not H3 tier logic. | Rename/comment as source-filter metadata in a later ingest cleanup. |
| `ingest/rcp.py` | RCP ingest | update | Contains poll-to-probability conversion code while current analysis excludes RCP until the transformation is documented. | Keep out of H1/H2 analysis until transformation is approved. |
| `operations/validation/` | Validation pipeline | keep | Aligns with deterministic-first architecture. | Ensure every DB write uses validation where reasonable. |
| `operations/db/` | Schema migration layer | keep | Supports required support tables and idempotent migrations. | Commit separately from documentation. |

## Legacy Concepts To Avoid Until Reapproved

- Agent-first project framing.
- MCP as a core data or analysis pipeline.
- Claude Desktop integration before deterministic outputs are stable.
- Model routing and self-consistency runs before an LLM interpretation layer is
  explicitly designed.
- Raw table dumps into prompts.
- Arbitrary whale thresholds used as analytical definitions.
- Treating RCP polling averages as native probabilities.
- Describing Granger results as proof of insider trading.
