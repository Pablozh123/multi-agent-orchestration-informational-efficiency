# ROADMAP.md

## Roadmap Principles

- Deterministic Python analysis comes before agents, MCP, ML, or interpretation.
- Each phase must leave reproducible files, tests, and documented assumptions.
- RCP is treated as a polling signal until a probability transformation is
  documented and tested.
- Events must be curated before H2 event-window analysis.
- Whale thresholds must be distribution-derived, not arbitrary.
- Strategy and anomaly-monitor work is a research prototype only; no live
  trading, order execution, or profit guarantee belongs in the thesis.

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

Status: complete for initial daily baseline

Done criteria:

- Polymarket and FiveThirtyEight probability forecasts are compared with Brier
  Score and documented assumptions.
- Optional decomposition is implemented where sample size allows.
- RCP is excluded unless a documented transformation is explicitly enabled.
- Output tables or CSVs are reproducible and tested.

Blockers:

- RCP transformation is not defined.
- H1 should not be interpreted as a reaction-speed result; the current
  Polymarket and prior-day Polymarket Brier means are nearly identical.

## Phase 4: Event Catalog And H2 Method

Status: complete for initial daily H2 baseline

Done criteria:

- Canonical event catalog has `event_id`, `event_date`, `event_time_utc`,
  `title`, `description`, `event_type`, `source_url`, `expected_direction`, and
  `relevance_score`.
- Inclusion and exclusion criteria are documented before analysis.
- Window definitions are fixed before CAR code runs.
- Event audit reports no missing canonical fields for included events.

Blockers:

- Legacy event rows still have missing canonical fields, but the tracked seed
  CSV contains the curated H2 event set used for the first deterministic output.
- Any future event additions must be reviewed before H2 outputs are regenerated.

## Phase 5: H2 Event Study And CAR

Status: complete for initial daily baseline

Done criteria:

- CAR or equivalent abnormal-return calculation is deterministic Python.
- Event windows are pre-specified and tested on toy data.
- Outputs separate event-level movement, source timing, and limitations.
- No event is added or removed after seeing results without documentation.
- H2 output CSVs can be regenerated from tracked seed events and SQLite prices.
- H2 summary output shape is reviewed before database persistence.
- Compact H2 summaries are persisted idempotently into `analysis_summaries`.

Blockers:

- Full row-level H2 traces must remain file-based unless a separate storage
  decision is documented.
- Intraday reaction-speed claims remain blocked until intraday data are added
  and validated.

## Phase 6: H3 Whale Distribution And Classification

Status: complete for initial daily H3 tier inputs

Done criteria:

- Wallet and trade distributions are inventoried before thresholds are chosen.
- Tiers are dataset-relative and reproducible.
- Current source filters are documented separately from analytical tiers.
- BUY-only limitation is explicitly addressed.
- Primary tier method is selected before classification code.
- Wallet distribution inventory output exists before classification code.
- Wallet tier classification output exists before tiered timing inputs.
- Tiered daily wallet activity series exists before descriptive timing analysis.

Blockers:

- Current whale data appears BUY-only.
- Current minimum `amount_usd` is 10000, likely reflecting an upstream filter.
- Granger code must wait until descriptive timing outputs are implemented and
  reviewed.

## Phase 7: H3 Lead-Lag And Granger Tests

Status: complete and reviewed for initial daily H3 baseline

Done criteria:

- Lead-time histograms and Granger tests are implemented in deterministic
  Python.
- Tests use toy data with known timing patterns.
- Results are described as predictive lead-lag structure, not proof of insider
  trading or causal misconduct.
- Descriptive lead-time histograms exist and are reviewed before Granger code.
- Granger outputs use daily tiered activity and daily Polymarket price changes.
- H3 Granger interpretation limits and persistence decision are documented.

Blockers:

- Sell-side or directionality limitations need resolution or explicit scope.
- Intraday lead-lag claims remain blocked until intraday data are added and
  validated.
- Strong thesis conclusion wording remains blocked until multiple-testing and
  sensitivity checks are completed or explicitly scoped as limitations.

## Phase 8: Interpretation Layer

Status: deferred

Done criteria:

- Deterministic H1, H2, and H3 outputs exist and pass tests.
- LLM prompts use bounded precomputed summaries only.
- All LLM calls are logged in `llm_audit_log`.
- No raw table dumps enter prompts.

Blockers:

- Deterministic H1-H3 outputs now exist, but thesis-facing result tables and
  interpretation limits must be finalised first.
- Agent and MCP modules remain deferred until the interpretation layer has a
  bounded prompt design and `llm_audit_log` integration.

## Phase 9: Thesis Export

Status: complete for initial Overleaf-ready results prose

Done criteria:

- Figures, tables, and result summaries are reproducible.
- Method sections document assumptions, exclusions, and limitations.
- Thesis-facing German uses Swiss spelling.
- Overleaf export artifacts are traceable to deterministic outputs.
- The first results narrative skeleton separates evidence, interpretation,
  limitations, and further investigations for H1, H2, H3, and the strategy
  prototype boundary.
- Overleaf-ready draft prose exists for the H1, H2, H3, strategy bridge, and
  interim results conclusion.

Blockers:

- Final Overleaf integration and citation formatting are not done yet.
- Strong H3 conclusion wording remains limited by BUY-only source data, daily
  alignment, and multiple-testing sensitivity.

## Phase 10: Politics/Geo Anomaly Monitor Prototype

Status: active for monitor v2 read-only summary access contract

Done criteria:

- The prototype is specified first as a politics/geopolitics anomaly monitor,
  not as an immediate trading strategy.
- v1 market universe is Polymarket politics/geopolitical markets.
- Kalshi is documented as a later extension candidate, not part of v1.
- Historical validation starts with the existing curated US-election events.
- Future geopolitical cases require verifiable timestamps, source URLs, and
  market mappings before they enter analysis.
- The monitor separates market anomalies, wallet-tier anomalies, event
  anomalies, and concentration diagnostics.
- Wallet outputs used for interpretation are aggregate tier outputs, not raw
  wallet-address dumps.
- Agents are future signal generators and reviewers only, not autonomous
  traders or metric calculators.
- MCP tools expose read-only summaries and tested result objects, not raw table
  dumps or order-execution functions.
- Deterministic backtests remain a later validation path for monitor alerts and
  signal hypotheses.
- First deterministic historical anomaly outputs exist with row, summary, and
  metadata artifacts.
- Outputs include market-move, wallet-tier amount, active-wallet, and top-tier
  concentration diagnostics.
- The historical output shape is reviewed before v2 monitor design or backtest
  validation begins.
- The v2 contract defines watchlist inputs, event-candidate intake,
  deterministic alert scoring, human review, persistence, and bounded summary
  outputs before any collector implementation begins.
- The v2 contract is specified as Polymarket-first and read-only.
- The v2 scoring contract uses robust rolling baselines, percentile ranks,
  explicit insufficient-baseline statuses, and descriptive alert levels.
- Human review states are specified before canonical event or alert reporting.
- A deterministic snapshot prototype exists and generates mock/replay-style
  alert rows, summaries, and metadata.
- The snapshot output row and summary columns are reviewed and accepted for the
  first deterministic v2 prototype.
- Rule C, combined-family confirmation, is selected as the first default
  threshold rule.
- A first deterministic historical replay snapshot pipeline exists and
  generates snapshots, alert rows, summaries, and metadata from existing local
  artifacts.
- Historical replay outputs are reviewed and accepted as the first daily v2
  replay baseline.
- Zero `critical` rows are interpreted as strict same-day event-context
  behaviour, not as an implementation defect.
- Event-proximity sensitivity compares same-day context with `[-1d, +1d]`
  daily context.
- `[-1d, +1d]` is selected for reviewed daily event context in replay outputs.
- `event_watch` is selected as a separate descriptive label for reviewed
  event-proximity wallet clusters without market-move confirmation.
- Historical replay writes a proximity-aware context sidecar output that keeps
  `critical_proximity_candidate` separate from `event_watch_candidate`.
- Recorded input validators exist for watchlist, market snapshots,
  wallet-tier snapshots, and event candidates.
- Recorded input adapter outputs exist and pass validation:
  watchlist, market snapshots, wallet-tier snapshots, event candidates,
  validation report, and metadata.
- Recorded input output shape is reviewed and accepted for a deterministic
  validated-input scoring runner.
- The validated-input scoring runner exists and emits recorded scoring
  snapshots, alert rows, summaries, context rows, validation report, and
  metadata.
- Recorded scoring outputs are reviewed and accepted as bounded daily replay
  monitor outputs.
- A simple thesis-facing figure exists for severity counts and event-context
  labels.
- Compact bounded monitor-v2 summary artifacts exist and cite their source
  files.
- Compact bounded monitor-v2 summary artifacts are reviewed and accepted as
  the first monitor summary boundary.

Blockers:

- The Polybench PDF is indexed only as a candidate and needs review before it
  supports thesis wording.
- Real-time data collection is not implemented and is not required for v1.
- Bounded MCP contracts and `llm_audit_log` usage are not implemented yet.
- Live trading, automated order execution, and profit guarantees are out of
  scope.
- A read-only monitor-v2 summary access contract is not specified yet.
- MCP, agents, live collection, and strategy backtests remain blocked until
  the access contract and audit boundaries are specified and reviewed.
