# AGENTS.md

This is the highest-level instruction file for all AI coding agents working in
this repository. If another prompt, roadmap, skill, or legacy instruction
conflicts with this file, follow this file.

## Project

Bachelor thesis project on informational efficiency of decentralized prediction
markets, focused on Polymarket, traditional forecast sources, and wallet-based
early signal detection.

Working thesis title:

Informationelle Effizienz dezentraler Prognosemaerkte am Beispiel Polymarket im
Vergleich zu traditionellen Prognosequellen.

## Core Rule

The deterministic analysis core comes before all agents.

All statistical calculations are implemented in Python. LLMs only interpret
precomputed outputs. LLMs must not calculate Brier scores, CAR, Granger tests,
wallet classifications, whale scores, or statistical metrics.

## Binding Rules

- The deterministic analysis core comes before all agents.
- All statistical calculations are implemented in Python.
- LLMs only interpret precomputed outputs.
- All LLM calls must later be logged in `llm_audit_log`.
- No raw table dumps into prompts.
- No `SELECT *` without `LIMIT`.
- Maximum 50 rows per tool query unless explicitly justified.
- No arbitrary whale thresholds.
- Whale thresholds must be derived from the actual wallet or trade distribution.
- No causal claims from Granger tests.
- RCP probability transformation must be documented before use.
- Events must be curated before event-window analysis.
- Every module must have tests where reasonable.
- Keep commits atomic.
- Do not modify unrelated files.

## Current Priority

Build the deterministic analysis foundation before implementing or extending
agent systems.

The repository may contain agent, MCP, audit, and model-routing scaffolding from
an earlier architecture. Treat those modules as parked legacy/deferred code. Do
not extend, invoke, or depend on them until the deterministic pipeline is stable,
tested, and documented.

Deferred agent and MCP modules must not be used before deterministic H1, H2, and
H3 outputs exist, pass tests, and have written methodology notes. Active
multi-agent or MCP entry points must raise:
`RuntimeError("Deferred until deterministic analysis core is complete")`.

Codex workflow roles such as planner, implementer, reviewer, and verifier are
allowed as development-process roles. They are not thesis runtime agents and
must not call tools, route models, or interpret thesis outputs as an automated
agent layer.

Future thesis runtime agents may only be specified at a high level while the
deterministic core is incomplete. Do not implement or activate them before H1,
H2, and H3 deterministic outputs exist.

## Do Not Implement Yet

- Multi-agent orchestration
- MCP demo layer
- Claude Desktop integration
- Model routing
- Self-consistency runs
- Cloud deployment

## Read-Only Live Data Rule

Read-only Polymarket live data collection is allowed for the monitor-v2 track
when `GOAL.md` explicitly scopes it.

Allowed live-data work:

- public market discovery,
- public price, midpoint, spread, orderbook, or market WebSocket data,
- public trade/activity data aggregated into validated monitor inputs,
- mocked API/WebSocket fixtures before new live connectors,
- file-based outputs with validation reports and metadata.

Blocked live-data work:

- order placement,
- order cancellation,
- authenticated user trading channels,
- trading credentials,
- autonomous execution,
- profitability guarantees,
- runtime agents or MCP tools that can access raw live inputs by default.

Live collectors must be read-only, tested with mocks, and must write bounded
validated artifacts before any interpretation layer may use their outputs.

## Preferred Stack

- Python
- SQLite
- DuckDB
- pandas
- numpy
- scipy
- statsmodels
- pydantic
- pandera
- tenacity
- pytest

## Coding Rules

- Use small files.
- Use typed functions.
- Avoid hidden API calls.
- Keep deterministic analysis functions testable.
- Validate every database write where reasonable.
- Prefer structured APIs and parsers over ad hoc string parsing.
- Use Swiss spelling in thesis-facing text: `ss` instead of German sharp s.
- Keep generated prompts and LLM inputs small and auditable.

## Mandatory Project Workflow

Before starting work:

1. Read `GOAL.md`.
2. Confirm there is exactly one active goal.
3. Work only on the active goal unless the user explicitly changes it.
4. Use planning, TDD, and review discipline where available.

Before stopping work:

1. Update `STATUS.md` with `python -m operations.project.update_status`.
2. Add an append-only entry to `docs/project/WORK_LOG.md`.
3. Run `python -m operations.project.review_check`.
4. Run `python -m operations.project.commit_plan`.
5. Show `git diff --stat`.
6. Recommend the exact next commit.

If a check fails, report the failure and do not claim the repository is ready
for the next empirical phase.

## Result Reporting Rule

For empirical or result-producing work, always report:

1. What was generated or inspected.
2. The key numerical result or output shape.
3. A bounded interpretation tied to deterministic artifacts.
4. The main limitation.
5. A simple figure when it makes the result easier to understand.

Figures must be generated from existing deterministic artifacts or tested
Python code. Do not use figures to introduce unreviewed metrics or stronger
claims than the source artifacts support.

## First Implementation Target

Create a reproducible deterministic pipeline:

1. Inspect existing SQLite tables.
2. Validate schema.
3. Generate data inventory.
4. Create event catalog structure.
5. Compute first Brier Score baseline.
6. Create tests.
