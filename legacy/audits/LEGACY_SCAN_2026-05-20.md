# Legacy Scan 2026-05-20

## Purpose

This audit separates repository content that is no longer aligned with the
current deterministic-first thesis workflow. It does not delete or move active
files. It lists what should remain active, what is already archived, and what
should be moved, guarded, or rewritten in a later cleanup commit.

Current source of truth:

- `AGENTS.md`
- `ARCHITECTURE_DECISIONS.md`
- `GOAL.md`
- `ROADMAP.md`
- `docs/research/RESEARCH_SPEC.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`

Scan scope:

- Root documentation and control files.
- `directives/`
- `.claude/`
- `.planning/`
- `operations/`
- `tests/`
- `ingest/`
- `docs/`
- `legacy/`
- `logs/`
- tracked data/result metadata where relevant.

Excluded from semantic review:

- `.git/`
- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- binary figure files.
- SQLite database contents, except where referenced by active code.

## Separation Status

### A. Current Active Control Layer

These files match the current architecture and remain active.

| Path | Status | Reason |
| --- | --- | --- |
| `AGENTS.md` | active | Highest-level instruction file. |
| `ARCHITECTURE_DECISIONS.md` | active | Binding architecture decisions. |
| `GOAL.md` | active | Single active goal control. |
| `ROADMAP.md` | active | Current phase status and blockers. |
| `STATUS.md` | active/generated | Project-control snapshot. |
| `PROJECT_CONTEXT.md` | active | Current thesis context. |
| `docs/research/RESEARCH_SPEC.md` | active | Current H1-H2-H3 methodology and result prose. |
| `docs/research/EVENT_SELECTION.md` | active | Current H2 event-window rules. |
| `docs/research/WHALE_METHOD.md` | active | Current H3 wallet-tier method. |
| `docs/research/LITERATURE_MAP.md` | active | Current literature intake/RAG boundary. |
| `docs/research/STRATEGY_AGENT_ARCHITECTURE.md` | active | Future strategy-agent and backtest boundary. |
| `docs/project/*.md` | active | Current workflow, review, commit, and tool rules. |
| `operations/project/` | active | Current automation layer. |
| `operations/analysis/` except noted below | active | Deterministic H1-H2-H3/result modules. |
| `operations/validation/` | active | Validation foundation. |
| `operations/db/` | active | Idempotent schema migrations. |
| `operations/tools/event_catalog_audit.py` | active | Event audit CLI. |
| `operations/tools/load_events.py` | active | Event seed loader. |

### B. Already Separated Legacy Area

These files are already preserved under `legacy/` and should stay out of the
active workflow.

| Path | Status | Reason |
| --- | --- | --- |
| `legacy/prompts/` | archived | Preserved old prompts and Claude settings. |
| `legacy/deferred_agents/orchestrator.py` | archived | Original orchestrator code; active path is guarded. |
| `legacy/deferred_mcp/thesis_mcp_server.py` | archived | Original MCP server code; active path is guarded. |
| `legacy/audits/LEGACY_SCAN_2026-05-20.md` | active audit | This scan report. |

### C. Clear Legacy Still In Active Tree

These files remain in their old locations and no longer represent the current
project state. They should be moved to a legacy area or rewritten later.

| Path | Status | Why it is legacy | Suggested next action |
| --- | --- | --- | --- |
| `.planning/PROJECT.md` | stale | Frames project as a multi-agent MCP system coordinated by Claude API. Uses H3 as "Whale Alpha" and references `>$10k` as an analytical threshold. | Move `.planning/` to `legacy/planning/` or rewrite as historical GSD archive. |
| `.planning/ROADMAP.md` | stale | Marks Pydantic agents and MCP demo as completed/live-tested and places agents before deterministic H2/H3. Treats RCP as probability rows. | Move to legacy; keep root `ROADMAP.md` as active. |
| `.planning/REQUIREMENTS.md` | stale | Contains old AGENT/MCP requirements and RCP-as-probability requirements. | Move to legacy or mark every section historical. |
| `.planning/STATE.md` | stale | Says Phase 1 is complete and ready for old Phase 2 agent layer. | Move to legacy. |
| `.planning/research/*.md` | stale/mixed | Contains old multi-agent architecture research and outdated implementation assumptions. | Move to legacy; salvage only manually reviewed notes. |
| `.planning/phases/01-data-foundation/*.md` | stale/mixed | Useful old implementation trace, but includes old RCP conversion, MCP, and `>$10k` whale framing. | Move as historical planning archive. |
| `logs/changelog/1b7be1de-9637-4012-9597-c0f81e6701c0.json` | stale output | Contains old orchestrator/agent run claims, wallet addresses, "Whale-Anomalie", and strong case-study interpretations. | Move to `legacy/changelog/` or mark non-thesis evidence. |
| `data/summaries.json` | stale output | Appears to be old prompt-context summary output for agents. | Move to `legacy/data/` or regenerate under current bounded-summary rules. |

### D. Active Code With Legacy Risk

These files are not safe to delete blindly because tests or imports still use
them. They should be guarded, rewritten, or moved in a dedicated code cleanup
commit if the project decides to remove active agent surfaces.

| Path | Status | Risk | Suggested next action |
| --- | --- | --- | --- |
| `operations/agents/market_agent.py` | active legacy risk | Instantiates a Pydantic AI agent and model id at import time. This is earlier than the current deferred runtime-agent strategy. | Either move to `legacy/deferred_agents/` and replace with runtime guard, or keep only after explicit approval of interpretation layer. |
| `operations/agents/sentiment_agent.py` | active legacy risk | Same active Pydantic AI surface; sentiment is currently contextual only. | Guard or move later. |
| `operations/agents/whale_agent.py` | active legacy risk | Exposes wallet tools and output fields such as `top_wallets`; thesis-facing layer should avoid wallet-address prompt outputs. | Guard or move later; never use for H3 calculations. |
| `tests/test_market_agent.py` | active legacy risk | Tests active agent instantiation and run via `TestModel`. | Replace with deferred-agent guard tests if agents are parked. |
| `tests/test_sentiment_agent.py` | active legacy risk | Tests active sentiment agent. | Replace with deferred-agent guard tests if agents are parked. |
| `tests/test_whale_agent.py` | active legacy risk | Tests active whale agent and wallet-address output. | Replace with deferred-agent guard tests if agents are parked. |
| `operations/audit/logger.py` | unclear legacy risk | Audit logging is needed later, but current design may belong to old agent layer. | Review when bounded LLM interpretation layer is implemented. |
| `operations/tools/db_tools.py` | unclear legacy risk | Agent-facing DB tools may still be useful, but they expose tool-style queries. | Keep only with strict row limits and no raw prompt dumps. |
| `operations/tools/api_clients.py` | unclear legacy risk | API client utilities may create hidden live-call pathways if reused casually. | Review before any deterministic ingestion change. |
| `operations/analysis/generate_summaries.py` | active legacy risk | Header says summaries are for prompt context of agents. Some whale anomaly logic predates the current H3 tier method. | Rewrite purpose or move after confirming no active dependency. |
| `ingest/dune.py` | active source-filter caveat | Uses `WHALE_THRESHOLD_USD = 10_000.0` as ingestion filter. This is acceptable only as source-filter metadata, not an analytical whale definition. | Rename/comment as source filter in a later ingest cleanup. |
| `ingest/rcp.py` | methodological caveat | Contains RCP poll-to-probability conversion code. Current analysis excludes RCP until transformation is documented and approved. | Keep inactive for H1 unless documented flags are added to the methodology. |
| `tests/test_ingest.py` | methodological caveat | Includes RCP probability conversion tests and Dune whale filtering tests from older foundation work. | Keep as ingestion tests but avoid treating them as analysis approval. |

### E. Prompt And Instruction Files

These files are not legacy conflicts because they were rewritten as
interpretation-only prompts. They are still not permission to activate runtime
agents.

| Path | Status | Reason |
| --- | --- | --- |
| `CLAUDE.md` | active pointer | Now points back to `AGENTS.md` and deterministic-core rules. |
| `directives/roles/market_agent.md` | active prompt, deferred use | Interpretation-only; no deterministic calculations. |
| `directives/roles/sentiment_agent.md` | active prompt, deferred use | Interpretation-only; no live news fetching or sentiment calculations. |
| `directives/roles/whale_agent.md` | active prompt, deferred use | Interpretation-only; rejects arbitrary whale thresholds and Granger overclaims. |
| `directives/roles/orchestrator.md` | active prompt, deferred use | Synthesis-only; does not authorize orchestration. |
| `directives/roles/reviewer.md` | active prompt, deferred use | Review-only. |
| `directives/methodology.md` | active support | Aligns with deterministic methodology rules. |
| `directives/coding_standards.md` | active support | Aligns with deterministic coding rules. |

### F. Claude-Specific Tooling

These files are not the current Codex control layer. They can remain as
tool-specific settings, but should not override repository architecture.

| Path | Status | Reason | Suggested next action |
| --- | --- | --- | --- |
| `.claude/settings.json` | tool config | Allows local Claude commands and points to `.claude/skills`. | Keep only if still used; otherwise move to `legacy/prompts/.claude/`. |
| `.claude/settings.local.json` | local tool config | User-specific permissions. | Do not edit blindly; review manually. |
| `.claude/skills/brier-score/SKILL.md` | active/deferred skill | Interpretation-only and aligned. | Keep if Claude workflow is still used. |
| `.claude/skills/dune-analytics/SKILL.md` | active/deferred skill | Interpretation-only and aligned. | Keep if Claude workflow is still used. |
| `.claude/skills/polymarket-api/SKILL.md` | active/deferred skill | Interpretation-only and aligned. | Keep if Claude workflow is still used. |
| `.claude/skills/fastmcp-server/SKILL.md` | deferred skill | MCP is deferred. | Keep only as deferred reference. |

## Highest-Risk Legacy Conflicts

1. `.planning/ROADMAP.md` still says the agent/MCP layer is complete and
   live-tested.
2. `.planning/PROJECT.md` still frames the project as a multi-agent MCP system.
3. Active `operations/agents/market_agent.py`, `sentiment_agent.py`, and
   `whale_agent.py` can still be imported and run with a model override.
4. `logs/changelog/*.json` contains old agent-generated case-study claims and
   wallet addresses.
5. `data/summaries.json` appears to be old agent prompt context.
6. `operations/analysis/generate_summaries.py` still describes summaries as
   prompt context for agents.
7. `ingest/dune.py` uses a fixed 10,000 USD filter; this must remain documented
   as source-filter metadata, not an analytical whale threshold.
8. RCP conversion code and tests exist, while the current thesis analysis
   excludes RCP until the transformation is documented.

## Recommended Cleanup Order

1. Move `.planning/` to `legacy/planning/` or add a top-level stale warning to
   every `.planning/*.md` entry point.
2. Move `logs/changelog/` old agent outputs to `legacy/changelog/`.
3. Move or regenerate `data/summaries.json` under current bounded-summary rules.
4. Decide whether single-agent modules should be hard-guarded like the
   orchestrator and MCP server.
5. If agents are hard-guarded, update `tests/test_market_agent.py`,
   `tests/test_sentiment_agent.py`, and `tests/test_whale_agent.py` to test the
   guards instead of active agent runs.
6. Rewrite `operations/analysis/generate_summaries.py` so it is clearly a
   deterministic summary generator, not an agent prompt context producer.
7. Rename/comment the Dune 10,000 USD constant as source-filter metadata.
8. Keep RCP code inactive for H1 until the transformation is fully documented.

## Current Recommendation

Do not physically move active code in this scan commit. The safest immediate
step is to keep this report as the separate legacy area, then perform one
focused cleanup commit at a time. The first cleanup should target `.planning/`
because it is clearly stale documentation and is not part of the current
runtime path.
