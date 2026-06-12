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

Status: paused after deterministic anomaly review queue and static access contract

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
- A read-only monitor-v2 summary access contract is specified in the strategy
  architecture document.
- The read-only monitor-v2 summary access contract is reviewed and accepted as
  the default monitor-v2 access boundary.
- Automated project checks enforce the monitor-v2 read-only access boundary,
  bounded summary artifacts, row limits, no wallet-address exposure, and
  blocked raw monitor files.
- A monitor-v2 live input collection contract is specified as read-only,
  replay-first, UTC timestamped, 15-minute bucketed for first live-capable
  alerts, validation-first, and no-lookahead.
- The monitor-v2 live input collection contract is reviewed and accepted for a
  replay-first validator/prototype path.
- Replay-first monitor-v2 live input validators exist for watchlist, market
  snapshots, wallet-tier snapshots, event candidates, timestamp fields, bucket
  boundaries, and wallet-address exclusion.
- The replay-first monitor-v2 live input validators are reviewed and accepted
  for a local batch prototype.
- A local replay-first monitor-v2 live input batch prototype exists and writes
  mocked live-style input files, a validation report, and metadata.
- The local replay-first monitor-v2 live input batch output shape is reviewed
  and accepted for a diagnostic deterministic local scoring bridge.
- A local replay-first monitor-v2 live input scoring bridge exists and writes
  diagnostic scoring snapshots, alert rows, alert summaries, validation
  report, and metadata from mocked local input files.
- The local replay-first monitor-v2 live input scoring output shape is
  reviewed and accepted as a pipeline diagnostic, not empirical evidence.
- The first real-data replay boundary is selected as
  `daily_recorded_replay_v1`, using existing recorded daily inputs and the v2
  30/20 baseline rule.
- Existing recorded daily replay outputs satisfy `daily_recorded_replay_v1`;
  no additional daily adapter is needed for this boundary.
- Read-only Polymarket live collector preflight is selected: Gamma discovery,
  CLOB midpoint/orderbook or market WebSocket, Data API trade aggregation,
  5-minute buckets first, and no order or authenticated trading path.
- A read-only Polymarket collector foundation exists for public Gamma market
  discovery, CLOB midpoint polling, Data API trade aggregation, validated
  monitor-v2 input files, a scoring bridge, and a simple snapshot figure.
- The first real live snapshot validates successfully, but scoring remains
  `insufficient_baseline` until repeated closed buckets exist.
- A bounded rolling-history collector exists and can append repeated closed
  buckets, validate inputs, run scoring, and generate a rolling-history figure.
- The first clean live rolling run produces 3 watchlist markets, 6 token
  midpoint rows, 3 aggregate wallet/activity rows, 12 scoring rows, and 0
  alerts with `insufficient_baseline`.
- The automatic Gamma filter now excludes category-only sport, entertainment,
  and court-noise cases, but the watchlist still needs curation before
  thesis-facing alert interpretation.
- A curated Polymarket live watchlist contract exists as a local CSV plus
  validator.
- The current curated watchlist seed contains 3 accepted rows, 0 candidate
  rows, and a validation report.
- Auto-discovered Gamma rows are explicitly not monitor-ready until reviewed
  and marked `accepted`.
- The read-only collector and rolling-history collector can use the accepted
  curated watchlist path.
- The first curated live collector run produced 3 watchlist rows, 6 token
  midpoint rows, 3 aggregate wallet/activity rows, 12 scoring rows, and 0
  alerts with `insufficient_baseline`.
- The next implementation step is operational rather than methodological:
  collect enough distinct closed curated buckets for diagnostic rolling
  baselines.
- Curated rolling-history collection produced 3 real closed 5-minute buckets,
  18 token midpoint rows, 9 aggregate wallet/activity rows, 48 scoring rows,
  0 alerts, and baseline readiness `diagnostic_scores_available`.
- The next implementation step is a local read-only dashboard/report view over
  the bounded monitor output files.
- First local read-only dashboard exists at
  `data/results/monitor_v2_polymarket_dashboard.html`.
- The dashboard reports 3 markets, 4 closed buckets, 0 alerts, baseline
  readiness `diagnostic_scores_available`, and links source artifacts.
- Bounded refresh runner exists and refreshed the dashboard from 4 real closed
  5-minute buckets with 0 alerts and baseline readiness
  `diagnostic_scores_available`.
- The next implementation step is an operator protocol that documents safe
  run commands, minimum bucket counts, and interpretation limits.
- Safe operator protocol is documented in the strategy architecture and tool
  usage docs.
- The first production-like live baseline has been collected with 21 real
  closed 5-minute buckets, 3 reviewed watchlist markets, 126 token midpoint
  rows, 63 aggregate wallet/activity rows, 372 scoring rows, 0 alerts, and v2
  `baseline_observations=30` / `min_baseline_observations=20` settings.
- The latest baseline readiness is
  `baseline_available_zero_mad_or_non_alerting`; scoring metadata marks
  `production_like_baseline_available=true`.
- The production-like baseline review is accepted: 0 alerts means Rule C did
  not trigger in the observed window, not that the broader market was quiet,
  efficient, inefficient, causal, or tradeable.
- Threshold-sensitivity outputs exist for the 21-bucket baseline. Default
  Rule C produced 0 alerts; the diagnostic 10/5 scenario produced 3 `watch`
  rows; the diagnostic rows do not justify changing the default rule.
- The reviewed Polymarket watchlist has been expanded from 3 to 12 accepted
  politics/geopolitics markets with 0 candidates, 0 rejected rows, and 0
  needs-followup rows.
- The expanded watchlist includes US election, US midterm control, China/Taiwan,
  Iran, Russia/Ukraine leadership, and Ukraine/Russia peace-process markets.
- A temporary collector verification produced 12 watchlist rows, 24 token
  midpoint rows, and 12 aggregate wallet/activity rows without modifying
  repository result artifacts.
- The expanded production-like live baseline has been collected with 20 real
  closed 5-minute buckets, 12 reviewed markets, 480 token midpoint rows, 240
  aggregate wallet/activity rows, 1'416 scoring rows, and 60 summary rows.
- The expanded baseline reports 0 alerts, severity counts of 1'416 `none`,
  status counts of 1'200 `insufficient_baseline` and 216 `zero_mad`, and
  baseline readiness `baseline_available_zero_mad_or_non_alerting`.
- The expanded-baseline review is accepted: the output shape is usable as a
  short-window prototype baseline, Rule C remains unchanged, and 0 alerts only
  means no Rule C trigger occurred in the observed window.
- The next empirical step is to improve the read-only monitor reporting layer
  so the latest live state can be understood without opening raw CSV/JSON
  files.
- The dashboard/reporting layer now surfaces run context, baseline settings,
  scoring row count, summary row count, severity counts, status counts, source
  artifact links, and zero-alert interpretation limits.
- The next implementation step is a small local read-only wrapper over the
  dashboard artifacts. It must not become a background daemon or trading
  surface.
- A local dashboard launcher exists and returns a structured `file://`
  dashboard URI plus read-only safety flags without collecting data or running
  continuously.
- The next empirical step is a second bounded expanded-watchlist live window
  so the first 12-market result is not treated as a one-off monitor state.
- The second bounded expanded-watchlist live window is collected with the same
  v2 30/20 settings and the same high-level result shape as the first expanded
  window: 12 markets, 20 buckets, 480 token midpoint rows, 240 aggregate
  wallet/activity rows, 1'416 scoring rows, 60 summary rows, 0 alerts, and
  baseline readiness `baseline_available_zero_mad_or_non_alerting`.
- The next implementation decision is how to preserve repeated live-window
  summaries before future refreshes overwrite the latest dashboard artifacts.
- A compact repeated-window registry exists:
  `data/results/monitor_v2_live_window_registry.csv` plus metadata.
- The registry stores compact summaries for `expanded_window_001` and
  `expanded_window_002`; both runs have 12 markets, 20 buckets, 0 alerts, and
  baseline readiness `baseline_available_zero_mad_or_non_alerting`.
- The next methodological step is an alert-review workflow for future non-zero
  monitor alerts.
- A wallet reference-case registry exists for public pattern-learning examples,
  including one reported Iran/U.S. cluster case and one AdrianCronauer
  large-flow case.
- Reference-case audit and feature outputs exist and expose only neutral
  pattern labels, fact-source status, claim scope, and review state.
- Reference-case outputs do not expose wallet addresses and do not convert
  reported public claims into computed facts.
- Reference-case similarity scores, summary, matrix figure, and local HTML
  dashboard exist as bounded human-review aids.
- Similarity is equal-weight pattern overlap and is documented as a review cue,
  not a probability model or hard label.
- A monitor reference-candidate adapter exists. It converts only monitor rows
  with `severity != none` into neutral candidate feature rows.
- The current latest monitor output has 1'416 rows, 0 non-none severity rows,
  0 reference candidates, and 0 candidate/reference similarity comparisons.
- The main monitor dashboard now includes a Reference Review section linking
  wallet reference similarity and current monitor reference-candidate views.
- Dashboard metadata records reference-review counts and confirms no wallet
  address or order-instruction exposure.
- A third bounded live update appended one new real bucket to the 12-market
  rolling history and produced 7 non-none Rule C rows, 3 strict monitor
  reference candidates, and updated diagnostic sensitivity outputs.
- The first non-none live rows are accepted only as human-review cues; they are
  not thesis-facing evidence of causality, private information, tradeability,
  profitability, or market efficiency.
- A compact human-review report now summarises the first 3 strict candidates,
  their trigger reasons, available evidence, missing evidence, review priority,
  and next review action.
- The human-review report now uses plain-language cards so the AOC-2028
  high-priority case can be understood from wallet amount, local baseline,
  concentration, and reference-overlap explanations without reading raw CSVs.
- The next review layer separates relative baseline strength from absolute
  economic materiality and reference-case scale.
- Insider-risk wording is allowed only as a human-review queue label, not as a
  computed wallet fact, misconduct claim, causal claim, or trading signal.
- Coordination context is needed so single-wallet/single-trade candidates are
  not confused with multi-wallet small-flow candidates.
- Literature-prior wallet and market risk scores are implemented as
  deterministic Python diagnostics over strict monitor candidates, not as an
  active Whale Agent.
- The literature-prior score layer keeps Rule C unchanged and marks missing
  wallet-age, true new-wallet-ratio, top-wallet concentration, and funding
  graph features as unavailable rather than guessed.
- Human-review cards and the main dashboard surface the literature-prior
  scores next to materiality and reference-review context.
- Public Polymarket wallet-level activity is collected from the public Data
  API and stored as a bounded local forensic artifact.
- Wallet graph nodes, edges, metrics, and a bubblemap-style local dashboard
  exist for public wallet-address review.
- Detection-backtest outputs check whether current monitor candidates have
  event, reference-case, or wallet-graph context.
- The detection-backtest is a review-quality test, not a PnL or trading
  strategy backtest.
- A deterministic anomaly review queue exists over bounded monitor artifacts.
- The queue writes compact case rows, a one-row summary, metadata, a local
  dashboard, and bounded case-review packets under `data/results/`.
- Queue rows expose review context, missing evidence, allowed interpretation,
  blocked claims, and human-review status without wallet-address columns.
- Case-review packets exist as
  `data/results/monitor_anomaly_case_review_packets.csv` and
  `data/results/monitor_anomaly_case_review_packets.json`; they provide a
  bounded per-case review surface for later human, MCP, or agent reading
  without activating MCP or agents.
- Deterministic status-transition gates exist as
  `data/results/monitor_anomaly_review_status_transitions.csv` and
  `data/results/monitor_anomaly_review_status_transitions.json`; they specify
  allowed next review states and thesis-use gates without automatically
  accepting, excluding, or upgrading any case.
- A curated final decision worksheet exists at
  `data/monitor_anomaly_review_decisions.csv`, with validated readiness
  outputs at `data/results/monitor_anomaly_review_decision_readiness.csv` and
  `data/results/monitor_anomaly_review_decision_readiness.json`.
- Current decision readiness rows are all `no_decision_recorded`, so all
  current cases remain blocked from thesis-facing use.
- A static future-access contract exists at
  `data/results/monitor_anomaly_review_access_contract.json`; it lists allowed
  bounded artifacts and future tool names but does not implement MCP, agents,
  raw SQL, wallet-address exposure, or order/trading paths.
- A curated manual review-status worksheet exists at
  `data/monitor_anomaly_review_status_updates.csv`; it can update queued cases
  with review status, reviewer, source URL, event URL, and review notes.
- All 3 current anomaly-review candidates now have `source_check_pending`
  entries with public Polymarket market URLs and public context URLs; these
  record source-check progress only and do not create causal,
  private-information, misconduct, or thesis-facing evidence.
- Future agent and MCP integration is documented as contract-only: bounded
  summaries, max 50 rows, no raw SQL, no wallet-address exposure by default,
  no order or trading paths, and later `llm_audit_log` logging.

Blockers:

- The Polybench PDF is indexed only as a candidate and needs review before it
  supports thesis wording.
- Read-only live data collection is now implemented only as bounded public
  REST polling and file outputs; it is not a background daemon.
- Bounded MCP contracts and `llm_audit_log` usage are not implemented yet.
- Live trading, automated order execution, and profit guarantees are out of
  scope.
- MCP, agents, strategy backtests, authenticated user channels, and order
  execution remain blocked while the read-only collector is built.
- Thesis-facing live-alert wording remains blocked until the expanded
  12-market baseline is compared with at least one later window or documented
  only as a short-window prototype result.
- Threshold changes are blocked; Rule C remains the default until a later
  reviewed sensitivity decision says otherwise.
- Any read-only UI/server wrapper must remain local, bounded, and manual; it
  must not collect data automatically or expose order/authentication paths.
- Repeated live windows are time-consuming because they require real closed
  5-minute buckets; do not synthesize timestamps for production-like claims.
- Current live-window files are latest-run artifacts. A storage/comparison
  structure is needed before building a longer repeated-run evidence base.
- Non-zero live alerts remain thesis-facing blocked until review states,
  evidence fields, and rejection criteria are documented.
- No current live-window reference candidates exist because Rule C produced no
  non-none severity rows in the latest 12-market window.
- Public reference cases remain evidence for pattern design, not proof of
  misconduct, private information, tradeability, or profitability.
- The first non-none live candidates require human review before any
  thesis-facing alert wording or strategy hypothesis.
- Current human-review candidates still need repeat-bucket confirmation,
  fuller event mapping, and human acceptance or exclusion before any
  thesis-facing use.
- Current strict candidates have small observed amounts versus the
  AdrianCronauer USD 103'248 reference trade, so materiality context must be
  shown before they are used as informed-flow examples.
- Literature-prior score weights and thresholds are heuristic priors until
  calibrated against broader Polymarket distributions and reference cases.
- Wallet graph v1 is based on shared market and shared time-bucket activity;
  it is not an on-chain funding graph or identity cluster.
- The next user-facing step is still manual review of the three
  `source_check_pending` cases; no further runtime MCP or agent work should
  start before final human decisions or a separate approved goal.

## Phase 11: Swiss Referendum Efficiency Comparison

Status: running data collection until the 14 June 2026 vote; final analysis
pending after the official result

Done criteria:

- The Swiss referendum comparison is separate from the politics/geo wallet
  anomaly monitor and remains in data-collection mode until the vote result is
  available.
- A curated poll catalog exists for the 10-million initiative and records
  source URLs, fieldwork windows, publication timestamps, timestamp precision,
  Yes/No/undecided shares, sample sizes, and uncertainty metadata.
- A read-only Polymarket collector targets the exact 10-million initiative
  market and writes bounded local snapshot rows.
- Comparison outputs attach the latest prior poll to each Polymarket snapshot.
- The deterministic gap outputs include raw Yes gap and decided-voter Yes gap.
- Bounded public CLOB price-history windows exist around curated poll releases.
- The methodology note states that poll shares are not model-implied win
  probabilities and that decided-voter normalization is not RCP.
- Poll-release impact rows require a local snapshot before and after poll
  publication before any timing interpretation is made.
- The local HTML dashboard and PNG figure are generated from local
  deterministic artifacts.
- A bounded one-command refresh runner can collect one new Polymarket snapshot
  and regenerate the local comparison dashboard without running continuously.
- A scheduler-safe one-shot auto-refresh wrapper can be called periodically
  until the 2026-06-14 voting-day cutoff, respects minimum snapshot spacing and
  a lock file, collects at most one bounded snapshot per invocation, and exits.
- Tests cover poll validation, Polymarket snapshot extraction, comparison
  matching, divergence labels, impact rows, refresh behavior, auto-refresh
  schedule gates, and output generation.

Blockers:

- Chrome automation is unavailable until the Codex Chrome Extension/native host
  setup is repaired; current source verification uses public web access and
  official/source pages instead.
- More bounded Polymarket snapshots are required before poll-release impact
  timing can be interpreted.
- Scheduled local collection is allowed only as a time-bounded one-shot command
  runner; it must not become a resident daemon, agent, trading surface,
  authenticated collector, or database writer.
- BFS/admin.ch is context evidence only unless a future source-checked BFS poll
  table exists.
- No causal, profitability, tradeability, or mispricing proof may be claimed
  from the current descriptive divergence labels.

## Phase 12: Thesis Consolidation And Evidence Mapping

Status: active

Done criteria:

- The active goal is thesis consolidation, not additional review-access work.
- Every central thesis-facing method maps to deterministic source artifacts and
  suitable literature references.
- Every central thesis-facing interpretation maps to deterministic artifacts,
  accepted wording, blocked wording, and a main limitation.
- A deliberately small thesis-ready package exists instead of a raw artifact
  dump: at most five core tables and at most four core figures.
- H1, H2, and H3 remain the empirical core.
- Monitor outputs are labelled as prototype or appendix material unless human
  review gates later approve them for thesis-facing use.
- The Swiss referendum side track remains descriptive until the official
  14 June 2026 vote result is available.
- Future agent improvements are documented only as a guarded architecture over
  bounded deterministic summaries; no runtime agents, MCP tools, model
  routing, autonomous collectors, trading paths, or unlogged LLM interpretation
  are activated.

Current implemented consolidation:

- `operations/analysis/thesis_consolidation.py` generates the consolidation
  layer from existing local artifacts.
- `data/results/thesis_evidence_map.csv` links methods, interpretations,
  limitations, artifacts, source references, allowed wording, and blocked
  wording.
- `data/results/thesis_core_results_table.csv` reduces the current empirical
  story to six central rows: bounded H1 support, H1 broad-claim boundary, H2
  largest daily event-window response, H3 top-tier timing diagnostic, monitor
  review-queue boundary, and Swiss running-gap boundary.
- `data/results/thesis_curated_result_package.csv` selects five core tables
  and four core figures for thesis drafting.
- `data/results/thesis_table_figure_captions.csv` and
  `docs/research/THESIS_TABLE_FIGURE_CAPTIONS.md` turn that curated package
  into thesis-ready labels, captions, source notes, interpretation notes, and
  limitation notes without adding extra raw result files.
- `data/results/thesis_citation_readiness.csv` maps every indexed source to
  evidence usage, current source status, citation risk, and the next review
  action before final thesis citation.
- `data/results/thesis_source_review_plan.csv` and
  `docs/research/THESIS_SOURCE_REVIEW_PLAN.md` group citation packets by
  source into a manual review queue: 11 priority-1 method-foundation sources,
  3 currently unused sources, and 1 blocked/future-work-only source in the
  current real literature index.
- `data/results/thesis_chapter_plan.csv` maps the BA chapter structure to
  curated tables, figures, evidence IDs, artifacts, limitations, and next
  writing actions.
- `data/results/thesis_agent_pipeline_roadmap.csv` defines documentation-only
  future agent stages and their activation gates.
- `data/results/thesis_agent_assistance_protocol.csv` and
  `docs/research/THESIS_AGENT_ASSISTANCE_PROTOCOL.md` translate the agent
  outlook into seven documentation-only assistance protocols for source
  review, evidence drafting, wording guardrails, table/figure checks, advisor
  updates, monitor appendix review, and a deferred bounded MCP summary
  interface.
- `data/results/thesis_next_work_plan.csv` and
  `docs/research/THESIS_NEXT_WORK_PLAN.md` order the remaining thesis work into
  ten guardrail-bound workstreams: source review, front-matter/method chapters,
  H1, H2/H3, compact table/figure integration, monitor appendix, Swiss result
  gate, agent outlook, advisor iteration, and final QA.
- `data/results/thesis_consolidation_metadata.json` records guardrails:
  no LLM use, no agents or MCP, no database writes, no external API calls,
  no raw table dumps, max future tool rows of 50, no wallet-address exposure
  by default, and no order or trading paths.
- `docs/research/THESIS_CONSOLIDATION.md` gives the high-level project view
  and a deferred agent-pipeline roadmap.
- `docs/research/THESIS_AGENT_PIPELINE_ROADMAP.md` documents the future
  agent stages as inactive architecture only.
- `docs/research/THESIS_WRITING_BLUEPRINT.md` translates the consolidation
  package into a chapter-by-chapter writing plan with source-review counts,
  package placements, result statements, limitations, and next writing actions.
- `docs/research/THESIS_CHAPTER_DRAFT.md` provides a first thesis-prose draft
  in German/Swiss spelling from the deterministic consolidation artifacts,
  including artifact references, Evidence IDs, bounded result wording,
  limitations, and a documentation-only agent outlook.
- `docs/project/dozentenbericht_ba_thesis.md`,
  `docs/project/dozentenbericht_ba_thesis.html`, and
  `docs/project/dozentenbericht_ba_thesis.docx` now start with a Phase 12
  high-level project view for the advisor: review access paused, H1-H3 as
  empirical core, five core tables, four core figures, citation-review gates,
  Monitor/Swiss boundaries, and agents as inactive future work.
- The same Dozentenbericht now includes `Naechste Arbeitsschritte`, a concise
  German rendering of the ten workstreams from `thesis_next_work_plan.csv`.
- `data/results/thesis_citation_review_packets.csv` and
  `docs/research/THESIS_CITATION_REVIEW_PACKETS.md` break citation readiness
  into source-evidence review packets with review questions, required checks,
  allowed wording, blocked wording, final citation gates, and pending reviewer
  fields.

Blockers:

- Some literature entries remain `skimmed` or `candidate`; final thesis
  citation status still needs source-by-source review before submission.
- Swiss referendum efficiency cannot be interpreted finally before the
  official result is available and mapped to the collected snapshots.
- The monitor review queue remains blocked from thesis-facing use while cases
  are only `source_check_pending`.
- Future agent support requires a separate approved goal, bounded prompt
  design, and `llm_audit_log` integration before implementation.
