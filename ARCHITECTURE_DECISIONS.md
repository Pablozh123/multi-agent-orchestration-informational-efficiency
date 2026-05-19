# ARCHITECTURE_DECISIONS.md

## Status

Binding architecture decisions for the thesis codebase as of 2026-05-19.

If this file conflicts with older prompt contracts, roadmap notes, Claude
settings, or agent instructions, this file and `AGENTS.md` win.

## Decisions

### 1. Deterministic Core First

The deterministic analysis core must be implemented and tested before any agent
or MCP layer is extended. Agents may later interpret outputs, but they must not
be part of the statistical computation path.

Reason: the thesis must be reproducible, inspectable, and scientifically
defensible.

### 2. Python Owns All Statistics

Brier scores, calibration metrics, CAR calculations, Granger tests, whale
classification, lead-time histograms, and all other statistical metrics are
computed in Python.

Reason: deterministic code can be tested, reviewed, and rerun.

### 3. LLMs Interpret Only Precomputed Outputs

LLMs may summarize or interpret bounded, precomputed results. They must not
receive raw table dumps or be asked to calculate statistical metrics.

Reason: this preserves reproducibility and avoids hidden calculations in prose.

### 4. LLM Calls Require Audit Logging

All future LLM calls must be logged in `llm_audit_log` with enough metadata to
reconstruct the run context, prompt version, tools used, and output.

Reason: thesis claims that use LLM interpretation need a scientific audit trail.

### 5. Bounded Data Access

No `SELECT *` without `LIMIT`. Tool-style queries may return at most 50 rows
unless a specific deterministic module justifies a broader query internally.

Reason: agents and interpretation layers should see summaries, not uncontrolled
raw data.

### 6. SQLite And DuckDB Stay Central

SQLite remains the portable source database. DuckDB may be used for analytical
queries over SQLite or exported result files.

Reason: the project should remain local, simple, and reproducible for a bachelor
thesis.

### 7. Required Support Tables

The thesis support tables are:

- `events_timeline`
- `analysis_summaries`
- `llm_audit_log`

These tables must be created or migrated idempotently. Existing data must not be
deleted or rewritten during migrations, except additive metadata backfills such
as `created_at`.

Reason: support tables are needed for event analysis, result summarization, and
LLM auditability.

### 8. RCP Is Not A Native Probability Forecast

RCP polling averages must not be treated as probability forecasts unless the
transformation is explicitly documented and tested.

Until that transformation exists, RCP is treated as a polling signal only.
Brier, calibration, and comparison code must exclude RCP by default. Any
function that includes RCP must require both `include_rcp=True` and
`rcp_transformation_documented=True`.

Reason: RCP is a polling-average source, not a forecast probability model.

### 9. Events Must Be Curated Before Event Windows

Event-window analysis requires a curated event catalog with timestamps,
categories, and inclusion rationale before CAR or reaction-speed code is run.

Reason: pre-specification reduces researcher degrees of freedom.

### 10. Whale Thresholds Must Be Distribution-Derived

Whale tiers or filters must be derived from the observed wallet or trade
distribution. Fixed thresholds such as 10,000 USD are legacy unless clearly
marked as source-filter constraints rather than analytical definitions.

Reason: arbitrary thresholds weaken H3 and can bias the result.

### 11. Granger Tests Are Predictive, Not Proof Of Causality

Granger results may be described as evidence of lead-lag predictability under a
specified model. They must not be described as proof of insider trading or true
causal influence.

Reason: Granger causality is a statistical timing test, not a legal or causal
proof.

### 12. Validation Before Writes

Every database write should pass validation where reasonable, using pydantic,
pandera, constraints, or explicit checks appropriate to the table.

Reason: invalid rows are expensive to detect once downstream analysis depends on
them.

### 13. Tests Scale With Risk

Every module must have tests where reasonable. Statistical functions, schema
migrations, source transformations, and query guardrails require focused tests.

Reason: small deterministic tests are the main quality control mechanism.

### 14. Agents And MCP Are Deferred

Existing `operations/agents/`, `operations/mcp/`, `.claude/`, and directive
prompt files are treated as legacy or deferred until the deterministic core is
complete.

Reason: premature orchestration adds complexity before the empirical foundation
is trustworthy.

### 15. Atomic Commits

Commits should be small and focused. Do not mix documentation synchronization,
schema migrations, statistical pipelines, and agent changes in one commit.

Reason: atomic commits make thesis development auditable and easier to review.

### 16. Strategy Prototype Is Backtested Research Only

A strategy component may be included in the thesis only as a historical
backtest prototype. It must not execute live trades, manage real funds, or be
described as a guaranteed profitable system.

Required strategy backtest outputs include risk measures such as transaction
cost assumptions, slippage assumptions, position limits, and maximum drawdown.
Out-of-sample or walk-forward evaluation is required before any strategy claim
is thesis-facing.

Reason: a backtest can support research on signal usefulness, while live
trading would introduce operational, legal, and risk-management scope that is
too broad for the thesis.

### 17. Agents May Propose Signals But Python Decides

Future strategy agents may propose news, market-pattern, or wallet-signal
hypotheses. They must not calculate Brier scores, CAR, Granger tests, wallet
tiers, PnL, drawdown, or backtest metrics. Deterministic Python modules own
validation and backtesting.

Reason: this preserves reproducibility while still allowing an agent
orchestration layer to support research discovery.

### 18. Literature Intake Must Be Traceable

Perplexity output, local PDFs, Zotero notes, and other literature sources are
used for discovery and methodology support. Thesis claims must be traceable to
indexed papers or primary sources, not to unverified LLM summaries.

Reason: literature grounding needs citation discipline and should not become an
untracked prompt-memory dependency.
