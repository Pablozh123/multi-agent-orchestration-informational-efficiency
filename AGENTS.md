AGENTS.md

Project

Bachelor thesis project on informational efficiency of decentralized prediction markets, focused on Polymarket, traditional forecast sources, and wallet-based early signal detection.

Core rule

Deterministic calculations must be done in Python. LLMs may only interpret precomputed results. LLMs must not calculate Brier scores, CAR, Granger tests, wallet classifications, or statistical metrics.

Current priority

Build the deterministic analysis foundation before implementing agents.

Existing deferred code

The repository may already contain agent, MCP, audit, and routing scaffolding from earlier architecture work. Treat those modules as parked. Do not extend, invoke, or depend on them until the deterministic analysis pipeline is stable and tested.

Do not implement yet

multi-agent orchestration
MCP demo layer
Claude Desktop integration
model routing
self-consistency runs
cloud deployment

Preferred stack

Python
SQLite
DuckDB
pandas
numpy
scipy
statsmodels
pydantic
pandera
tenacity
pytest

Coding rules

small files
typed functions
no hidden API calls
no SELECT * without LIMIT
no raw data dumps into LLM prompts
every analysis function must be testable
every database write must pass validation
use Swiss spelling in thesis-facing text, ss instead of ß

First implementation target

Create a reproducible deterministic pipeline:

inspect existing SQLite tables
validate schema
generate data inventory
create event catalog structure
compute first Brier Score baseline
create tests

Gib Codex nicht alles auf einmal
