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

### 19. Literature RAG Is Index-Bounded

Future RAG-style literature use must retrieve only from sources listed in
`data/literature/literature_index.csv`. Candidate sources may support discovery
and question formation, but thesis-facing claims require reviewed or cited
status. Retrieved snippets must remain traceable to `source_id`, local file, or
URL.

No vector database, embedding pipeline, agent orchestration, or MCP literature
tool is active until the deterministic result summaries and audit boundaries are
stable.

Reason: local literature can support research without becoming an uncontrolled
or unverifiable memory layer.

### 20. Politics/Geo Anomaly Monitor Is A Research Prototype

The next strategy-track direction is a politics/geopolitics anomaly monitor for
prediction markets, not a live trading system. Its first version should observe
Polymarket politics/geopolitical markets and historical validation artifacts.
Kalshi and near-real-time monitoring are later extensions.

The monitor may combine four deterministic signal families:

- market anomalies, such as unusual probability moves or volume changes,
- wallet-tier anomalies, using aggregate tier activity only,
- event anomalies, using sourced political or geopolitical event candidates,
- concentration diagnostics, such as top-tier share or HHI-style summaries.

It must not hardcode a single event, infer events from price movement alone, or
produce order-execution instructions. Event candidates such as geopolitical
shocks require a verifiable timestamp, source URL, and market mapping before
they are analysed.

Reason: an anomaly monitor fits the thesis question about informational
efficiency while keeping empirical claims deterministic, auditable, and
separate from autonomous trading or profit promises.

### 21. Near-Real-Time Monitor V2 Starts As A Contract

The near-real-time politics/geopolitics monitor must be specified as a
read-only contract before collector or alert code is implemented. The contract
defines watchlist inputs, market snapshots, wallet-tier snapshots,
event-candidate review states, rolling robust scores, alert levels, persistence
rules, and bounded output files.

The default scoring design uses a 30-observation rolling baseline, a minimum of
20 baseline observations for production-like alerts, robust z-scores based on
median absolute deviation, and rolling percentile ranks. Missing or unstable
baselines return explicit diagnostic statuses rather than false alerts.

The monitor may use Polymarket Gamma, Data, CLOB, and Market WebSocket sources
as read-only inputs, but order placement, autonomous execution, live trading,
profit claims, and insider/misconduct claims remain out of scope. Agents and
MCP tools remain deferred until deterministic monitor outputs exist and bounded
summary contracts plus audit logging are specified.

Reason: the monitor should become a reproducible empirical instrument, not an
uncontrolled live-trading or agent-orchestration layer.

### 22. Live Monitor Inputs Are Replay-First

Future monitor-v2 live input collection must be specified, validated, and
replayable before any collector is implemented. The first live-capable design
uses read-only source classes only: market discovery metadata, market-state or
orderbook observations, aggregate wallet-tier activity, and sourced event
candidates.

Required input rows must carry UTC timestamps, deterministic bucket boundaries,
source-class metadata, and validation status. The first live-capable prototype
uses 15-minute alert-scoring buckets, while daily buckets remain the bridge to
the current thesis outputs. Lower-latency market-state observations may be
recorded as diagnostics only until rate limits, missingness, and microstructure
interpretation are reviewed.

Scoring must avoid lookahead: bucket `t` may be scored only after the bucket is
closed, rolling baselines for `t` use completed prior buckets, and event
context may only use candidates detected or published at or before the alert
bucket.

The initial implementation path remains file-based and replay-first. Raw live
input files are source artifacts, not prompt-facing or MCP-facing outputs.
Future LLM, MCP, or agent access may use bounded summaries only and must
preserve audit and claim boundaries.

Reason: a running monitor is only scientifically useful if its inputs can be
replayed, validated, and checked for lookahead before any interpretation or
automation layer depends on it.

Review status as of 2026-05-20: accepted for replay-first implementation
planning. Live API collection, WebSocket streaming, MCP access, runtime agents,
strategy backtests, order execution, and trading credentials remain blocked
until mocked or replayed input validators exist and pass tests.
