# ROADMAP.md

## Roadmap Principles

- Deterministic Python analysis comes before agents, MCP, ML, or interpretation.
- Each phase must leave reproducible files, tests, and documented assumptions.
- RCP is treated as a polling signal until a probability transformation is
  documented and tested.
- Events must be curated before H2 event-window analysis.
- Whale thresholds must be distribution-derived, not arbitrary.

## Phase 1: Project Synchronization And Foundation

Status: in progress

Done criteria:

- `AGENTS.md`, project context, architecture decisions, and control docs align.
- Deferred agent and MCP entry points cannot run accidentally.
- Tests pass.
- Foundation changes are committed in atomic slices.
- Goal-driven project automation can update status, run review checks, and
  propose commit groups.

Blockers:

- Project-control automation is not committed yet.
- `STATUS.md` and `WORK_LOG.md` must be updated before stopping each work turn.

## Phase 2: Database Schema And Validation

Status: in progress

Done criteria:

- Required support tables exist: `events_timeline`, `analysis_summaries`,
  `llm_audit_log`.
- Migrations can run repeatedly without deleting or rewriting source data.
- Validation exists for prices, wallet rows, sentiment, polls, and events.
- Database writes pass validation where reasonable.

Blockers:

- Canonical event rows still need curation.
- Validation coverage should be expanded when new deterministic modules appear.

## Phase 3: H1 Forecast Calibration

Status: started

Done criteria:

- Polymarket and FiveThirtyEight probability forecasts are compared with Brier
  Score and documented assumptions.
- Optional decomposition is implemented where sample size allows.
- RCP is excluded unless a documented transformation is explicitly enabled.
- Output tables or CSVs are reproducible and tested.

Blockers:

- RCP transformation is not defined.
- Existing H1 result artifacts should be regenerated only after commit cleanup.

## Phase 4: Event Catalog And H2 Method

Status: blocked

Done criteria:

- Canonical event catalog has `event_id`, `event_date`, `event_time_utc`,
  `title`, `description`, `event_type`, `source_url`, `expected_direction`, and
  `relevance_score`.
- Inclusion and exclusion criteria are documented before analysis.
- Window definitions are fixed before CAR code runs.
- Event audit reports no missing canonical fields for included events.

Blockers:

- Current event audit reports 20 missing values for each required canonical
  field.
- Source URLs and expected directions are not curated.
- Active goal remains research-scope definition before H2/H3 implementation.

## Phase 5: H2 Event Study And CAR

Status: not started

Done criteria:

- CAR or equivalent abnormal-return calculation is deterministic Python.
- Event windows are pre-specified and tested on toy data.
- Outputs separate event-level movement, source timing, and limitations.
- No event is added or removed after seeing results without documentation.

Blockers:

- Phase 4 is not complete.

## Phase 6: H3 Whale Distribution And Classification

Status: blocked

Done criteria:

- Wallet and trade distributions are inventoried before thresholds are chosen.
- Tiers are dataset-relative and reproducible.
- Current source filters are documented separately from analytical tiers.
- BUY-only limitation is explicitly addressed.

Blockers:

- Current whale data appears BUY-only.
- Current minimum `amount_usd` is 10000, likely reflecting an upstream filter.
- Distribution-derived classification is not implemented.

## Phase 7: H3 Lead-Lag And Granger Tests

Status: not started

Done criteria:

- Lead-time histograms and Granger tests are implemented in deterministic
  Python.
- Tests use toy data with known timing patterns.
- Results are described as predictive lead-lag structure, not proof of insider
  trading or causal misconduct.

Blockers:

- Phase 6 is not complete.
- Sell-side or directionality limitations need resolution or explicit scope.

## Phase 8: Interpretation Layer

Status: deferred

Done criteria:

- Deterministic H1, H2, and H3 outputs exist and pass tests.
- LLM prompts use bounded precomputed summaries only.
- All LLM calls are logged in `llm_audit_log`.
- No raw table dumps enter prompts.

Blockers:

- Deterministic core is incomplete.
- Agent and MCP modules remain deferred.

## Phase 9: Thesis Export

Status: not started

Done criteria:

- Figures, tables, and result summaries are reproducible.
- Method sections document assumptions, exclusions, and limitations.
- Thesis-facing German uses Swiss spelling.
- Overleaf export artifacts are traceable to deterministic outputs.

Blockers:

- Empirical scope and H2/H3 outputs are not yet finalized.
