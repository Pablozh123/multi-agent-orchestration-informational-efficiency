# STRATEGY_AGENT_ARCHITECTURE.md

## Purpose

This document specifies the future anomaly-monitor, strategy, agent, and MCP
layer for the thesis research prototype. It does not activate agents, MCP, live
trading, model routing, or autonomous execution.

The prototype is part of the thesis as a research design around information
monitoring and historical validation. It must not be presented as a guaranteed
profitable system.

## Boundary

Allowed:

- Agents propose signal hypotheses.
- Python validates signal specifications.
- Python runs historical backtests and computes risk metrics.
- MCP exposes bounded summaries and tested result objects.
- Every future LLM call is logged in `llm_audit_log`.

Not allowed:

- Agents calculating Brier, CAR, Granger, wallet tiers, PnL, drawdown, or risk
  metrics.
- Raw table dumps into prompts.
- Autonomous trading.
- Live order execution.
- Profit guarantees.
- Treating exploratory backtest output as proof that a strategy will work
  out-of-sample.

## Current Track: Politics/Geo Anomaly Monitor

anomaly_monitor_status: specification

The current prototype direction is a politics/geopolitics anomaly monitor for
prediction markets. It should detect and explain unusual combinations of market
movement, wallet-tier activity, volume, concentration, and sourced event
context. It is not an order-execution or portfolio-management system.

The monitor does not select one fixed event in advance. Cases such as a
political arrest, military escalation, sanctions announcement, election shock,
court decision, or leadership change are treated as event candidates only when
they have:

- a verifiable source URL,
- an event timestamp or defensible publication timestamp,
- an associated Polymarket market or market group,
- a pre-analysis rationale for the expected direction or uncertainty change.

v1 scope:

- Polymarket politics/geopolitical markets.
- Historical validation against existing deterministic outputs.
- Existing seven US-election events as the first validation bed.
- Aggregate wallet-tier and market-level outputs only.

Later extensions:

- Kalshi market comparison.
- Near-real-time market and news collection.
- Human-reviewed event-candidate queue.
- MCP summary tools after bounded outputs and audit logging exist.

Blocked:

- live trading,
- autonomous order execution,
- wallet-address prompt dumps,
- profit claims,
- event selection after inspecting price reactions,
- agent-computed metrics.

### Anomaly Families

`market_anomaly`

- Probability move relative to a rolling historical baseline.
- Volume or liquidity jump where validated data exist.
- Bid/ask-spread anomaly only if spread data are collected and validated.
- Interpretation: unusual market movement, not proof of inefficiency by itself.

`wallet_tier_anomaly`

- Dataset-relative wallet-tier activity spike.
- Active-wallet count spike by tier.
- Total observed `amount_usd` spike by tier.
- Interpretation: unusual aggregate wallet activity under the BUY-only source
  limitation.

`event_anomaly`

- Market and wallet activity around a verified event candidate.
- Historical v1 uses the curated US-election event seed.
- New politics/geo cases require source review before inclusion.
- Interpretation: event-centred timing pattern at the available data frequency.

`concentration_anomaly`

- Top-tier share of observed activity.
- HHI-style concentration summaries where meaningful.
- Interpretation: concentration of observed activity, not wallet profitability
  or misconduct.

### Historical Validation Path

Historical anomaly output status: complete for v1 daily baseline.

The first implementation after this specification is a deterministic historical
anomaly output, not a trading backtest. It produces:

- `h3_event_wallet_anomaly_rows.csv`
- `h3_event_wallet_anomaly_summary.csv`
- `h3_event_wallet_anomaly_metadata.json`

Implemented output fields:

- event or market identifier,
- anomaly type,
- tier or aggregate group,
- z-score or percentile-rank style diagnostic,
- baseline window and event window,
- source artifact,
- limitation,
- no causal, insider, or profit claim.

The v1 output contains 350 row-level diagnostics and 70 compact summary rows
for the seven curated US-election events. It includes market-move,
wallet-tier-amount, active-wallet, and top-tier-concentration diagnostics.

Historical anomaly outputs can later motivate a stricter backtest, but they are
first a monitoring and research-control layer.

### Historical Output Review

Review date: 2026-05-20

Review status: accepted for the first historical daily anomaly baseline.

Result summary:

- 350 row-level anomaly diagnostics and 70 compact summary rows were produced.
- Anomaly-day counts by family: 43 active-wallet anomalies, 40 wallet-tier
  amount anomalies, 5 market-move anomalies, and 4 top-tier concentration
  anomalies.
- The strongest event-level cluster is `evt_2024_07_21_biden_withdrawal` with
  30 anomaly days across the monitored families.
- Other visible clusters are `evt_2024_06_28_biden_trump_debate` with 16,
  `evt_2024_07_15_vance_vp_pick` with 13, and
  `evt_2024_09_11_harris_trump_debate` with 13.
- The clearest single diagnostic is active-wallet activity in the observed
  baseline tier around Biden withdrawal, with maximum z-score 13.68.

Figure:

- `data/results/thesis_h3_event_wallet_anomalies.png`

Interpretation:

- The output shows that the monitor can surface event-centred clusters where
  market movement and aggregate wallet-tier activity are unusual relative to a
  pre-event baseline.
- The Biden withdrawal cluster is the most salient historical validation case
  in the current US-election seed.
- The output is descriptive. It does not prove causality, private information,
  misconduct, or profitability.

v2 decision:

- The next contract should specify the near-real-time politics/geo monitor
  before implementation.
- v2 should define watchlist inputs, event-candidate intake, alert scoring,
  human review, persistence, and bounded summary outputs.
- Backtest validation remains a later step after the alert contract is fixed.

## Monitor V2 Contract

monitor_v2_contract_status: specified

The v2 monitor is a documentation and interface contract for a future
deterministic Python prototype. It is Polymarket-first, read-only, and
designed for politics/geopolitical markets. It does not implement agents, MCP,
ML, live trading, or order execution.

API and literature anchors:

- Polymarket API docs: `https://docs.polymarket.com/api-reference/introduction`
- Polymarket Market WebSocket:
  `https://polymarket-292d1b1b.mintlify.app/market-data/websocket/market-channel`
- PolyBench: `https://arxiv.org/abs/2604.14199`
- Polymarket order-book microstructure:
  `https://arxiv.org/abs/2604.24366`
- Per-market information-leakage and order-flow skill:
  `https://arxiv.org/abs/2605.02287`

Design implication:

- Use Gamma-style market/event discovery for watchlists and metadata.
- Use public CLOB endpoints or the Market WebSocket for prices, midpoints,
  spreads, orderbook updates, and trade events.
- Use Data API outputs or validated local ingestion for wallet/activity
  aggregates.
- Keep news and geopolitical events as sourced candidates until human review
  accepts the timestamp, source, and market mapping.
- Treat order-flow and trade-direction data as source-specific. Microstructure
  work must record whether a value came from orderbook feed, CLOB endpoint,
  on-chain trade record, or local aggregate artifact.

### V2 Input Contracts

`MarketWatchItem`

- `watch_id`
- `market_id`
- `condition_id`
- `token_ids`
- `question`
- `category`
- `subcategory`
- `status`
- `source`
- `created_at`
- `updated_at`

Purpose:

- Defines the markets monitored by v2.
- Must be created before alerts are evaluated.
- Must not be inferred from already-observed anomalies without being marked as
  a post-hoc diagnostic watch item.

`MarketSnapshot`

- `timestamp_utc`
- `market_id`
- `token_id`
- `price`
- `midpoint`
- `best_bid`
- `best_ask`
- `spread`
- `volume`
- `open_interest`
- `source`

Purpose:

- Captures market state at a reproducible timestamp or bucket.
- For the first implementation, replayed or polled snapshots are acceptable for
  testability before a live WebSocket collector exists.

`WalletTierSnapshot`

- `timestamp_utc`
- `market_id`
- `bucket`
- `tier`
- `active_wallets`
- `trade_count`
- `total_observed_amount_usd`
- `top_tier_share`
- `hhi_concentration`
- `source`
- `filter_metadata`

Purpose:

- Provides aggregate wallet-tier activity only.
- Must not expose wallet addresses in monitor-facing, MCP-facing, or
  LLM-facing outputs.
- `market_maker_exclusions.json` may be used as documented filter metadata,
  not as proof that all remaining wallets are organic or directional.

`EventCandidate`

- `event_candidate_id`
- `detected_at_utc`
- `published_at_utc`
- `title`
- `source_url`
- `event_type`
- `related_market_ids`
- `expected_effect`
- `review_status`
- `review_notes`

Purpose:

- Records political or geopolitical news/event candidates before canonical use.
- `data/events_catalog.json` remains legacy/context unless a later migration
  maps rows into this candidate contract.

`AlertRecord`

- `alert_id`
- `timestamp_utc`
- `market_id`
- `anomaly_family`
- `metric_name`
- `observed_value`
- `baseline_window`
- `baseline_observations`
- `robust_z`
- `rolling_percentile_rank`
- `severity`
- `evidence_refs`
- `limitations`
- `review_status`

Purpose:

- Stores descriptive monitor alerts and links them to deterministic evidence.
- Does not contain order instructions, profitability claims, or causal claims.

### V2 Scoring Contract

Default baseline:

- Use the last 30 completed observations or buckets.
- Require at least 20 baseline observations for production-like alerts.
- Lower baseline counts may produce diagnostic rows only, labelled
  `insufficient_baseline`.

Primary robust score:

- `robust_z = (value - rolling_median) / (1.4826 * MAD)`
- If `MAD` is zero or unavailable, the row must return a clear non-alert
  diagnostic status rather than silently falling back to an unstable score.

Secondary empirical score:

- rolling percentile rank within the baseline window.

Metric families:

- `market_move`: absolute midpoint or price change.
- `spread_liquidity`: spread widening or depth drop where validated data
  exist.
- `wallet_tier_activity`: `log1p(total_observed_amount_usd)`,
  active-wallet count, and trade-count changes by tier.
- `concentration`: top-tier share and HHI-style concentration summaries.
- `event_proximity`: proximity to a reviewed event candidate. Event proximity
  can upgrade context but must not create an anomaly by itself.

Alert levels:

- `info`: percentile at least 0.90 or robust z-score at least 1.5.
- `watch`: percentile at least 0.95 or robust z-score at least 2.0.
- `high`: at least two anomaly families at `watch`, or one family robust
  z-score at least 3.0.
- `critical`: market-move anomaly plus wallet or concentration anomaly plus a
  reviewed event candidate. This still remains a descriptive alert and not a
  trading, insider, misconduct, or profitability claim.

Default wording:

- Allowed: `unusual market activity`, `unusual wallet-tier activity`,
  `reviewed event context`, `descriptive alert`.
- Blocked: `alpha`, `insider`, `proof`, `profitable trade`,
  `causal manipulation`.

### Human Review Contract

Review statuses:

- `candidate`: machine-collected or manually proposed, not checked.
- `source_checked`: source URL and timestamp checked.
- `market_mapped`: related Polymarket market or token ids checked.
- `accepted`: eligible for canonical event or alert reporting.
- `rejected`: duplicate, weak source, irrelevant, or post-hoc.
- `needs_followup`: unclear timestamp, ambiguous market mapping, or source
  quality issue.

Human review questions:

- Is the event source credible?
- Is the timestamp defensible?
- Is the market mapping known before inspecting the alert result?
- Is the alert based only on data available at or before alert time?
- Does the wording avoid causality, misconduct, insider, and profitability
  claims?

### V2 Persistence And Output Contract

Future file-based prototype outputs:

- `data/results/monitor_v2_watchlist.csv`
- `data/results/monitor_v2_snapshots.csv`
- `data/results/monitor_v2_event_candidates.csv`
- `data/results/monitor_v2_alert_rows.csv`
- `data/results/monitor_v2_alert_summary.csv`
- `data/results/monitor_v2_metadata.json`

Persistence rules:

- Start file-based with recorded or mocked snapshots.
- Do not write to `analysis_summaries` until alert summary shape is reviewed.
- Do not add MCP tools until bounded summary outputs and `llm_audit_log`
  usage are specified.
- Do not send raw wallet addresses, unrestricted SQL, or row-level table dumps
  into LLM prompts.

Future implementation tests:

- robust rolling score on a toy time series with a known spike,
- no lookahead: alert at time `t` uses observations available at or before `t`,
- missing baseline returns `insufficient_baseline`,
- event candidate cannot become `accepted` without source URL and timestamp,
- monitor outputs contain no wallet addresses,
- market-maker exclusions are applied only as documented filter metadata,
- no order execution, agents, MCP, ML, or RCP probability use.

## Monitor V2 Snapshot Prototype

monitor_v2_snapshot_prototype_status: complete for mocked snapshots

Implemented prototype module:

- `operations/analysis/monitor_v2_snapshot.py`

Implemented test module:

- `tests/test_monitor_v2_snapshot.py`

Generated artifacts:

- `data/results/monitor_v2_alert_rows.csv`
- `data/results/monitor_v2_alert_summary.csv`
- `data/results/monitor_v2_metadata.json`

Prototype scope:

- Uses a deterministic built-in mock snapshot fixture by default.
- Also accepts a CSV snapshot file through the CLI for later recorded replay.
- Uses completed prior observations for rolling baselines.
- Computes robust z-scores with median absolute deviation and rolling
  percentile ranks.
- Emits descriptive alert severities only.
- Writes no database rows and calls no external API.

Current mock-output shape:

- 124 row-level diagnostics.
- 4 compact summary rows.
- 12 non-`none` alert rows.
- 4 `critical` rows on the final mock event day, where market movement,
  wallet-tier activity, active-wallet activity, concentration, and accepted
  event context coincide.

Interpretation:

- The prototype proves the v2 contract can be translated into deterministic
  Python outputs without live collection.
- It demonstrates explicit `insufficient_baseline`, `zero_mad`, robust-score,
  percentile-rank, event-review, and severity handling.

Review needed before real replay data:

- The mock fixture also produces earlier `watch` alerts when percentile rank is
  high even though robust z-score is modest. This follows the documented
  contract, but it should be reviewed before real monitoring to decide whether
  percentile-only alerts need an additional minimum robust-z or combined-family
  condition.
- The next step should review output columns, severity behaviour, and
  threshold sensitivity before a live collector or real politics/geo replay
  input is added.

### Snapshot Prototype Output Review

Review date: 2026-05-20

Review status: accepted with threshold-sensitivity caveat.

Reviewed artifacts:

- `data/results/monitor_v2_alert_rows.csv`
- `data/results/monitor_v2_alert_summary.csv`
- `data/results/monitor_v2_metadata.json`

Accepted row shape:

- `timestamp_utc`
- `market_id`
- `tier`
- `anomaly_family`
- `metric_name`
- `observed_value`
- `baseline_window`
- `baseline_observations`
- `rolling_median`
- `rolling_mad`
- `robust_z`
- `rolling_percentile_rank`
- `severity`
- `status`
- `event_candidate_id`
- `event_review_status`
- `evidence_refs`
- `limitation`
- `review_status`
- `claim_scope`

Accepted summary shape:

- market and metric identifiers,
- row and alert counts,
- maximum severity,
- maximum robust z-score,
- maximum percentile rank,
- first and latest alert timestamps,
- limitation and claim scope.

Reviewed output:

- 124 row-level diagnostics.
- 4 compact summary rows.
- 112 `none` rows, 8 `watch` rows, and 4 `critical` rows.
- 80 rows have `insufficient_baseline`, which is expected because the mock run
  requires at least 20 prior observations.
- 44 rows have `ok` scoring status.
- The final mock event day has 4 `critical` alerts, one each for market move,
  wallet-tier activity, active-wallet activity, and concentration.

Interpretation:

- The prototype output shape is accepted for the first deterministic v2
  contract implementation.
- The metadata correctly states that the run uses mocked or recorded snapshots
  only, does not write to the database, does not use LLMs, agents, MCP, ML, or
  RCP, and contains no wallet addresses or order instructions.
- The final mock event-day cluster shows that the contract can represent a
  combined politics/geo anomaly alert when reviewed event context coincides
  with multiple metric families.

Threshold caveat:

- The 8 non-final `watch` rows are produced by percentile rank equal to 1.0
  while robust z-score is about 1.35.
- This is acceptable for a contract fixture, but likely too sensitive for real
  replay or live data.
- Before using real replay data, run a deterministic threshold-sensitivity
  review that compares the current rule with stricter alternatives, such as:
  minimum robust z-score for percentile-only alerts, combined-family
  confirmation for `watch`, or separate `percentile_info` labelling.

Decision:

- Accept the output columns and metadata.
- Do not add live collection yet.
- Do not add agents or MCP yet.
- Next step: deterministic threshold-sensitivity review on the existing mock
  snapshot output before real replay data is added.

### Threshold Sensitivity Decision

Review date: 2026-05-20

Selected rule: combined-family confirmation.

Rule C is selected for the first monitor v2 default:

- A single percentile-only `watch` row is downgraded to `info` if it is the only
  watch-or-higher family for the market and timestamp.
- `watch` requires at least two anomaly families at `watch` or higher in the
  same market and timestamp.
- A single very strong family can still remain `high`.
- `critical` still requires market movement plus wallet or concentration
  anomaly plus reviewed event context.

Reason:

- The monitor should avoid noisy single-metric percentile alerts.
- Family confirmation better fits the tool objective: detect unusual
  combinations of market movement, wallet-tier activity, concentration, and
  event context.
- The rule remains deterministic and testable before real replay data.

Implemented check:

- `tests/test_monitor_v2_snapshot.py` verifies that a single-family
  percentile-only row with robust z-score below 2.0 is downgraded to `info`.

Current mock-output effect:

- The default mock output still contains 8 `watch` rows and 4 `critical` rows,
  because the two early `watch` timestamps have all four anomaly families
  elevated together.
- This is acceptable: Rule C is not designed to remove all percentile alerts,
  but to prevent isolated single-family percentile alerts from becoming
  user-facing `watch` alerts.

Decision:

- Use Rule C as the default for the next deterministic replay prototype.
- Do not add live collection yet.
- Next step: build historical replay snapshots from existing deterministic
  artifacts before any real-time collector.

## Monitor V2 Historical Replay

monitor_v2_historical_replay_status: complete for first daily replay

Implemented replay module:

- `operations/analysis/monitor_v2_historical_replay.py`

Implemented test module:

- `tests/test_monitor_v2_historical_replay.py`

Generated artifacts:

- `data/results/monitor_v2_historical_replay_snapshots.csv`
- `data/results/monitor_v2_historical_replay_alert_rows.csv`
- `data/results/monitor_v2_historical_replay_alert_summary.csv`
- `data/results/monitor_v2_historical_replay_metadata.json`

Replay input scope:

- Curated event seed: `data/events_timeline_seed.csv`
- Daily Polymarket prices: `data/thesis.db`, table `polymarket_prices`
- Aggregate wallet-tier activity:
  `data/results/h3_tiered_wallet_activity_daily.csv`

Replay output shape:

- 3040 daily snapshot rows.
- 3040 scored alert rows.
- 10 compact summary rows.
- Date range: 2024-01-06 to 2024-11-04.
- 7 accepted event dates are marked from the curated seed.
- No wallet addresses and no order instructions are present.

Severity result:

- `none`: 2528 rows.
- `info`: 262 rows.
- `watch`: 173 rows.
- `high`: 77 rows.
- `critical`: 0 rows.

Interpretation:

- The replay shows that Rule C can score a historical daily monitor panel from
  existing deterministic artifacts without live collection.
- The absence of `critical` rows means that, under the current daily replay
  rule, no curated event date simultaneously has market movement, wallet or
  concentration anomaly, and accepted event context at the required severity.
- Several curated event dates still contain wallet-tier or active-wallet
  `watch` and `high` rows. These are descriptive monitoring signals, not
  trading instructions or proof of causality.

Review needed:

- Check whether the replay should use daily event-date matching only or allow a
  small event proximity window, such as `[-1d, +1d]`, before live collection.
- Check whether `critical` should remain strict or whether a separate
  `event_watch` label is needed for event dates with wallet clusters but no
  market-move confirmation.
- Do not add live WebSocket or API collection until this replay output is
  reviewed.

### Historical Replay Output Review

Review date: 2026-05-20

Review status: accepted for the first daily monitor v2 replay baseline, with
event-proximity sensitivity required before live collection.

Reviewed artifacts:

- `data/results/monitor_v2_historical_replay_snapshots.csv`
- `data/results/monitor_v2_historical_replay_alert_rows.csv`
- `data/results/monitor_v2_historical_replay_alert_summary.csv`
- `data/results/monitor_v2_historical_replay_metadata.json`

Accepted output shape:

- 3040 daily snapshot rows.
- 3040 scored alert rows.
- 10 compact summary rows.
- Date range: 2024-01-06 to 2024-11-04.
- 7 accepted event dates from the curated event seed.
- Aggregate-only output with no wallet addresses and no order instructions.

Severity result:

- `none`: 2528 rows.
- `info`: 262 rows.
- `watch`: 173 rows.
- `high`: 77 rows.
- `critical`: 0 rows.

Event-day observations:

- `evt_2024_06_28_biden_trump_debate`: one `high`, five `watch`, one `info`.
- `evt_2024_07_21_biden_withdrawal`: four `high`, three `watch`.
- `evt_2024_08_06_walz_vp_pick`: one `high`, two `watch`, one `info`.
- `evt_2024_09_11_harris_trump_debate`: three `high`, two `watch`, one
  `info`.

Interpretation:

- The replay confirms that Rule C can score a full historical daily monitor
  panel from existing deterministic artifacts.
- The absence of `critical` rows is not treated as an implementation defect.
  It reflects a strict same-day event-context rule combined with daily
  snapshots.
- Several curated event dates still show wallet-tier or active-wallet
  clusters at `watch` or `high` severity. These are descriptive monitoring
  signals, not claims of causality, private information, misconduct,
  profitability, or trade execution.

Decision:

- Accept the historical replay row, summary, and metadata shapes.
- Keep `critical` strict for now.
- Do not add live WebSocket/API collection, agents, MCP, ML, or order
  execution.
- Next step: run a deterministic event-proximity sensitivity check comparing
  same-day event context with a small daily proximity window, initially
  `[-1d, +1d]`.
- Evaluate whether a separate `event_watch` label is useful for reviewed
  event-proximity wallet clusters that do not also have confirmed market-move
  anomalies.

### Event-Proximity Sensitivity Review

Review date: 2026-05-20

Review status: accepted for daily replay rule selection.

Implemented sensitivity module:

- `operations/analysis/monitor_v2_event_proximity_sensitivity.py`

Implemented test module:

- `tests/test_monitor_v2_event_proximity_sensitivity.py`

Generated artifacts:

- `data/results/monitor_v2_event_proximity_sensitivity_rows.csv`
- `data/results/monitor_v2_event_proximity_sensitivity_summary.csv`
- `data/results/monitor_v2_event_proximity_sensitivity_metadata.json`

What was compared:

- Existing same-day event context from the historical replay alert rows.
- A small daily event-proximity window: `[-1d, +1d]`.
- The sensitivity does not rescore market or wallet values. It only maps
  existing replay alert rows to curated event proximity dates.

Result:

- Same-day `critical` candidates: 0.
- Event-proximity `critical` candidates: 6.
- Event-proximity `event_watch` candidates: 6.
- Row-level sensitivity rows: 210.
- Summary rows: 21.

Decision:

- Use `[-1d, +1d]` as the reviewed daily event-context window for the next
  historical replay contract.
- Keep `critical` strict: it still requires market movement plus wallet or
  concentration anomaly plus reviewed event context.
- Add or preserve a separate `event_watch` concept for wallet or concentration
  clusters near reviewed events when market-move confirmation is absent.
- `event_watch` is descriptive context, not a trading signal, not an order
  instruction, and not a severity upgrade to `critical`.

Interpretation:

- Daily snapshots are too coarse for same-day-only event matching. The
  sensitivity shows that meaningful reviewed event context appears one day
  before or after the curated date in several cases.
- The result supports a proximity-aware monitor output for daily replay, but it
  does not support intraday reaction-speed claims.

### Proximity Label Integration

Integration date: 2026-05-20

Integration status: complete for the historical daily replay contract.

Updated replay module:

- `operations/analysis/monitor_v2_historical_replay.py`

New replay sidecar output:

- `data/results/monitor_v2_historical_replay_context_rows.csv`

Updated metadata output:

- `data/results/monitor_v2_historical_replay_metadata.json`

Context label counts:

- `critical_proximity_candidate`: 6.
- `event_watch_candidate`: 6.
- `context_alert`: 1.
- `no_event_alert`: 8.

Decision:

- Keep row-level replay alert severities unchanged.
- Use the context sidecar to separate `critical_proximity_candidate` from
  `event_watch_candidate`.
- Treat `event_watch_candidate` as descriptive event context only. It is not a
  trading signal, not an order instruction, not evidence of causality, and not
  a private-information or misconduct claim.

Next implementation step:

- Build deterministic validation for recorded monitor v2 input files before
  any live API or WebSocket collector is added.

### Recorded Input Validation

Validation date: 2026-05-20

Validation status: complete for the first recorded-input contract.

Implemented validation module:

- `operations/analysis/monitor_v2_input_validation.py`

Implemented test module:

- `tests/test_monitor_v2_input_validation.py`

Validated file contracts:

- `MarketWatchItem`
- `MarketSnapshot`
- `WalletTierSnapshot`
- `EventCandidate`

Validation rules:

- Critical columns must exist.
- Timestamps must parse as datetimes.
- Market probabilities, midpoints, best bid, and best ask must be between 0
  and 1 when present.
- Best bid must not exceed best ask.
- Market snapshots require at least `price` or `midpoint`.
- Wallet-tier snapshots require non-negative counts and amounts.
- Wallet-tier snapshots must not contain `wallet_address`.
- Accepted or mapped event candidates require source URLs and related market
  ids.

Boundary:

- The validators read recorded CSV files only.
- They do not connect to Polymarket APIs, WebSockets, databases, LLMs, agents,
  MCP tools, ML systems, or order-execution paths.

Next implementation step:

- Build recorded monitor v2 input adapters from existing historical artifacts
  so the validator can run on replay-derived watchlist, market snapshot,
  wallet-tier snapshot, and event-candidate files before live collection.

### Recorded Input Adapter

Adapter date: 2026-05-20

Adapter status: complete for first historical replay-derived input files.

Implemented adapter module:

- `operations/analysis/monitor_v2_recorded_input_adapter.py`

Implemented test module:

- `tests/test_monitor_v2_recorded_input_adapter.py`

Generated recorded input files:

- `data/results/monitor_v2_recorded_watchlist.csv`
- `data/results/monitor_v2_recorded_market_snapshots.csv`
- `data/results/monitor_v2_recorded_wallet_tier_snapshots.csv`
- `data/results/monitor_v2_recorded_event_candidates.csv`

Generated validation and metadata files:

- `data/results/monitor_v2_recorded_input_validation_report.json`
- `data/results/monitor_v2_recorded_inputs_metadata.json`

Output shape:

- Watchlist rows: 1.
- Market snapshot rows: 305.
- Wallet-tier snapshot rows: 1236.
- Event candidate rows: 7.
- Validation status: `pass`.
- Wallet addresses: absent.
- Order instructions: absent.

Interpretation:

- The monitor now has a tested recorded-file input boundary before live
  collection exists.
- Market snapshots are daily replay snapshots from local Polymarket price
  data.
- Wallet-tier snapshots are aggregate tier-level rows from the H3 daily
  activity series.
- Event candidates are the seven curated seed events mapped to the replay
  market.

Next implementation step:

- Review the recorded input files and decide whether their shape is accepted
  before building a runner that scores validated recorded inputs.

### Recorded Input Output Review

Review date: 2026-05-20

Review status: accepted for a validated-input scoring runner.

Reviewed artifacts:

- `data/results/monitor_v2_recorded_watchlist.csv`
- `data/results/monitor_v2_recorded_market_snapshots.csv`
- `data/results/monitor_v2_recorded_wallet_tier_snapshots.csv`
- `data/results/monitor_v2_recorded_event_candidates.csv`
- `data/results/monitor_v2_recorded_input_validation_report.json`
- `data/results/monitor_v2_recorded_inputs_metadata.json`

Accepted shape:

- Watchlist rows: 1.
- Market snapshot rows: 305.
- Wallet-tier snapshot rows: 1236.
- Event candidate rows: 7.
- Validation status: `pass`.
- Wallet addresses: absent.
- Order instructions: absent.

Decision:

- Accept the recorded input columns and validation report for the first
  validated-input scoring runner.
- Keep the boundary file-based and replay-derived before live collection.
- Treat market snapshots as daily replay snapshots, not intraday order-book
  or WebSocket data.
- Treat wallet-tier snapshots as aggregate BUY-side observed activity under
  the existing H3 source limitation.
- Treat event candidates as the seven curated seed events mapped to the replay
  market.
- Do not write these recorded input reviews to the database yet.

Interpretation:

- The monitor now has a reviewed, validated, replay-derived input boundary.
- This is enough to build a deterministic runner that validates the recorded
  files, applies the selected monitor v2 scoring contract, and writes bounded
  alert outputs.
- It is not evidence for live monitoring, intraday reaction speed, trading
  profitability, private information, or causal claims.

Next implementation step:

- Build a deterministic validated-input scoring runner that reads the recorded
  input files, validates them before scoring, emits file-based alert rows,
  summaries, context rows, and metadata, and keeps all outputs aggregate-only.

### Recorded Input Scoring Runner

Runner date: 2026-05-20

Runner status: complete for first validated recorded-input scoring outputs.

Implemented module:

- `operations/analysis/monitor_v2_recorded_input_scoring.py`

Implemented test module:

- `tests/test_monitor_v2_recorded_input_scoring.py`

Generated artifacts:

- `data/results/monitor_v2_recorded_scoring_snapshots.csv`
- `data/results/monitor_v2_recorded_alert_rows.csv`
- `data/results/monitor_v2_recorded_alert_summary.csv`
- `data/results/monitor_v2_recorded_context_rows.csv`
- `data/results/monitor_v2_recorded_scoring_validation_report.json`
- `data/results/monitor_v2_recorded_scoring_metadata.json`

Output counts:

- Scoring snapshots: 3394.
- Alert rows: 3394.
- Non-`none` alert rows: 581.
- Summary rows: 11.
- Event-context rows: 21.
- Severity counts: 2813 `none`, 334 `info`, 169 `watch`, 78 `high`.
- Context labels: 3 `critical_proximity_candidate`, 8
  `event_watch_candidate`, 1 `context_alert`, and 9 `no_event_alert`.

Implemented metric families:

- `market_move`: absolute daily midpoint or price change.
- `wallet_tier_activity`: `log1p(total_observed_amount_usd)` by wallet tier.
- `active_wallet_activity`: active wallet count by wallet tier.
- `concentration`: top-tier share and HHI-style concentration.

Interpretation:

- The runner proves that reviewed recorded input files can be converted into
  bounded monitor v2 alert outputs without live collection.
- There are no direct `critical` severities in the scored alert rows, because
  the strict alert rule still requires same-timestamp event context.
- The context sidecar finds three `critical_proximity_candidate` dates under
  the reviewed daily `[-1d, +1d]` event-context window.
- The eight `event_watch_candidate` rows identify event-adjacent wallet or
  concentration clusters without market-move confirmation.
- These outputs are descriptive monitor diagnostics. They are not trading
  signals, order instructions, private-information evidence, profitability
  evidence, or causal claims.

Next implementation step:

- Review the recorded scoring outputs before any live collector, MCP surface,
  agent layer, or strategy backtest uses them.

### Recorded Scoring Output Review

Review date: 2026-05-20

Review status: accepted as a bounded recorded monitor output.

Reviewed artifacts:

- `data/results/monitor_v2_recorded_scoring_snapshots.csv`
- `data/results/monitor_v2_recorded_alert_rows.csv`
- `data/results/monitor_v2_recorded_alert_summary.csv`
- `data/results/monitor_v2_recorded_context_rows.csv`
- `data/results/monitor_v2_recorded_scoring_validation_report.json`
- `data/results/monitor_v2_recorded_scoring_metadata.json`

Figure:

- `data/results/thesis_monitor_v2_recorded_scoring.png`

Accepted output shape:

- Row-level diagnostics stay in `monitor_v2_recorded_alert_rows.csv`.
- Compact metric summaries stay in `monitor_v2_recorded_alert_summary.csv`.
- Daily event-context labels stay in
  `monitor_v2_recorded_context_rows.csv`.
- Validation evidence stays in
  `monitor_v2_recorded_scoring_validation_report.json`.
- Method, limitation, and output-count metadata stay in
  `monitor_v2_recorded_scoring_metadata.json`.

Reviewed output:

- 3394 scoring snapshots and 3394 alert rows were produced.
- 581 rows have non-`none` alert severity.
- Direct severity counts are 334 `info`, 169 `watch`, 78 `high`, and 0
  `critical`.
- Context labels include 3 `critical_proximity_candidate`, 8
  `event_watch_candidate`, 1 `context_alert`, and 9 `no_event_alert`.
- The validation report status is `pass`.
- Outputs contain no wallet addresses and no order instructions.

Interpretation:

- The output shape is accepted for a first bounded monitor-v2 recorded scoring
  baseline.
- Direct alert severity and event-proximity context remain separate. This is
  important because daily data can show event-adjacent clusters without
  proving same-timestamp reaction speed.
- The absence of direct `critical` rows is not a defect. It reflects the
  stricter same-timestamp event requirement.
- The three `critical_proximity_candidate` rows are descriptive daily-context
  candidates only. They are not trading signals, profitability evidence,
  private-information evidence, or causal claims.
- The eight `event_watch_candidate` rows indicate event-adjacent wallet or
  concentration clusters without market-move confirmation.

Limitations:

- The output is daily replay, not live or intraday monitoring.
- Wallet metrics use aggregate observed BUY-side tier activity.
- Event candidates are the seven curated US-election seed events only.
- Spread, depth, and true real-time order-book dynamics are not represented in
  this recorded baseline.

Next implementation step:

- Create a compact bounded monitor-v2 result summary from the accepted scoring
  outputs before any future LLM, MCP, agent, or live collector reads monitor
  information.

### Bounded Monitor V2 Summary Generator

Generator date: 2026-05-20

Generator status: complete for first bounded monitor-v2 summaries.

Implemented module:

- `operations/analysis/monitor_v2_result_summaries.py`

Implemented test module:

- `tests/test_monitor_v2_result_summaries.py`

Generated artifacts:

- `data/results/monitor_v2_bounded_summary.csv`
- `data/results/monitor_v2_bounded_summary_metadata.json`

Output shape:

- Summary rows: 19.
- Columns: `summary_id`, `summary_type`, `label`, `metric`, `value`,
  `source_artifact`, `allowed_interpretation`, `limitation`, and
  `claim_scope`.
- Source artifacts are explicitly referenced in each row.
- Metadata records that the summary does not use LLMs, agents, MCP, ML, live
  collection, database writes, or execution paths.

Included summary types:

- `validation`: validation status for the recorded input scoring run.
- `coverage`: snapshot and alert-row counts.
- `direct_severity_count`: counts for `none`, `info`, `watch`, `high`, and
  `critical`.
- `event_context_label_count`: counts for daily event-context labels.
- `metric_family`: alert counts by monitor family.
- `strongest_metric`: the three largest robust-score diagnostics in the
  compact metric summary.

Result summary:

- The bounded summary preserves the recorded scoring result: 3394 scoring
  snapshots, 3394 alert rows, and validation status `pass`.
- It records 581 non-`none` alert diagnostics indirectly through severity
  counts.
- It records 3 `critical_proximity_candidate` and 8
  `event_watch_candidate` context rows.
- Active-wallet activity is the largest alert-count family with 259 alert
  rows.
- The largest robust-score diagnostic is `market_move |
  absolute_midpoint_change` with maximum robust z-score 20.91.

Boundary:

- Full row-level monitor outputs remain file-based.
- Later LLM, MCP, or agent layers must use bounded summaries, not raw alert
  rows.
- The bounded summary is descriptive. It does not create trading signals,
  private-information claims, source-attribution claims, or future-performance
  claims.

Next implementation step:

- Review and accept or revise the bounded summary shape before any read-only
  access contract, MCP contract, agent interpretation layer, or live collector
  design uses monitor-v2 outputs.

### Bounded Summary Output Review

Review date: 2026-05-20

Review status: accepted as the first monitor-v2 summary boundary.

Reviewed artifacts:

- `data/results/monitor_v2_bounded_summary.csv`
- `data/results/monitor_v2_bounded_summary_metadata.json`

Accepted shape:

- The CSV contains 19 compact rows.
- Each row contains a stable `summary_id`, `summary_type`, human-readable
  label, metric name, value, source artifact, allowed interpretation,
  limitation, and claim scope.
- The metadata records the source artifacts, summary columns, row count, and
  non-use of LLMs, agents, MCP, ML, live collection, and database writes.
- The summary includes validation, coverage, direct severity counts,
  event-context label counts, metric-family counts, and strongest metric
  diagnostics.

Review result:

- Validation status is `pass`.
- Summary coverage records 3394 scoring snapshots and 3394 alert rows.
- Direct severity counts remain 2813 `none`, 334 `info`, 169 `watch`, 78
  `high`, and 0 `critical`.
- Event-context labels remain 9 `no_event_alert`, 1 `context_alert`, 8
  `event_watch_candidate`, and 3 `critical_proximity_candidate`.
- Metric-family counts show active-wallet activity as the largest family with
  259 alert rows, followed by wallet-tier activity with 187, concentration
  with 107, and market movement with 28.
- The largest robust-score diagnostic is market movement, but this remains a
  descriptive recorded-value diagnostic.

Decision:

- Accept the bounded summary shape for future read-only access contracts.
- Treat `monitor_v2_bounded_summary.csv` as the default monitor-v2
  interpretation surface.
- Keep `monitor_v2_recorded_alert_rows.csv` and other row-level outputs as
  deterministic source artifacts, not prompt-facing defaults.
- Do not expose unrestricted raw alert rows through future MCP or agent tools.

Limitations:

- The summary is daily replay, not live monitoring.
- It uses aggregate observed BUY-side wallet-tier activity.
- Event context is a daily `[-1d, +1d]` proximity label, not intraday
  reaction-speed evidence.
- The accepted summary does not support trading, private-information,
  misconduct, causality, or future-performance claims.

Next implementation step:

- Specify a read-only monitor-v2 summary access contract that describes which
  bounded files a future MCP or agent layer may read, while keeping the actual
  MCP and agent implementations deferred.

### Read-Only Monitor V2 Summary Access Contract

Contract date: 2026-05-20

Contract status: specified, implementation deferred.

Purpose:

- Define the narrow monitor-v2 output surface that future read-only tools,
  MCP contracts, or agent interpretation layers may use.
- Keep the deterministic monitor outputs useful without exposing raw alert
  dumps, wallet-level data, unrestricted SQL, or execution paths.
- Preserve the thesis boundary: descriptive anomaly monitoring, not live
  trading, not private-information detection, not causality, and not
  profitability evidence.

Default allowed artifacts:

- `data/results/monitor_v2_bounded_summary.csv`
- `data/results/monitor_v2_bounded_summary_metadata.json`
- `data/results/thesis_monitor_v2_recorded_scoring.png`
- `data/results/thesis_figures_metadata.json`

Allowed by default:

- Read the full bounded summary CSV because it contains 19 compact rows.
- Read the bounded summary metadata.
- Read the thesis-facing monitor-v2 figure.
- Return row counts, severity counts, event-context label counts,
  metric-family counts, source-artifact references, allowed interpretations,
  limitations, and claim scopes.
- Summarise the daily replay limitation, BUY-side observed activity limitation,
  and no-live-collection limitation.

Blocked by default:

- Raw row-level alert dumps.
- Scoring snapshots.
- Recorded input watchlist, market snapshots, wallet-tier snapshots, and event
  candidate CSVs.
- Direct reads from `data/thesis.db`.
- Wallet-address fields or wallet-level exports.
- Unrestricted SQL or `SELECT *` interfaces.
- Live API, WebSocket, orderbook, or order-execution calls.
- PnL, drawdown, profitability, strategy, or execution outputs.

Conditional access:

- Row-level source artifacts may be inspected by a human or development
  workflow only for debugging or method review.
- Any future tool access to row-level artifacts must be explicitly justified,
  limited to at most 50 rows, and logged.
- Row-level artifacts must never become the default prompt-facing or
  MCP-facing output surface.

Future read-only tool contract:

- `list_monitor_v2_summary_artifacts`
  - returns bounded artifact paths and metadata paths only.
- `get_monitor_v2_bounded_summary`
  - returns the 19-row bounded summary and no row-level alert dump.
- `get_monitor_v2_summary_metadata`
  - returns source artifacts, limitations, and output columns.
- `get_monitor_v2_figure`
  - returns the thesis-facing figure path or rendered image reference.

These names are contracts only. They do not activate MCP, agents, model
routing, or live collectors.

Maximum exposure rules:

- Default summary response: at most 50 rows.
- Current bounded summary: 19 rows, accepted.
- Raw source rows: blocked by default.
- Any exception must include a reason, row limit, source artifact, and audit
  note.

Allowed interpretation wording:

- `descriptive daily replay monitor summary`
- `bounded monitor-v2 summary`
- `event-proximity context label`
- `aggregate wallet-tier activity`
- `recorded scoring diagnostic`
- `requires human review before canonical alert use`

Blocked interpretation wording:

- `trade now`
- `live signal`
- `private information`
- `misconduct`
- `causal proof`
- `profitable strategy`
- `guaranteed predictive edge`
- `autonomous trading`

Future audit requirements:

- Any future LLM, MCP, or agent access must log the call in `llm_audit_log`
  once the interpretation layer is implemented.
- Audit records must include the system prompt version or hash, user prompt,
  bounded artifact names, tools called, and a compact tool-result summary.
- Prompts must cite bounded summary artifact paths, not paste raw alert rows.
- Outputs must preserve source limitations and claim boundaries.

Decision:

- Accept `monitor_v2_bounded_summary.csv` as the default read-only monitor-v2
  access surface.
- Keep raw monitor output files as deterministic source artifacts only.
- Keep actual MCP, agent, live collector, strategy backtest, and audit-log
  implementation deferred.

Next implementation step:

- Review this access contract and decide whether the next phase should be
  documentation-only MCP/agent contract drafting, deterministic backtest
  baseline planning, or live-collector input specification.

### Read-Only Summary Access Contract Review

Review date: 2026-05-20

Review status: accepted as the monitor-v2 read-only access boundary.

Reviewed contract:

- `Read-Only Monitor V2 Summary Access Contract`

Accepted defaults:

- `data/results/monitor_v2_bounded_summary.csv`
- `data/results/monitor_v2_bounded_summary_metadata.json`
- `data/results/thesis_monitor_v2_recorded_scoring.png`
- `data/results/thesis_figures_metadata.json`

Accepted restrictions:

- Bounded summaries are the default access surface.
- Raw row-level alert dumps are blocked by default.
- Scoring snapshots and recorded input files are blocked by default.
- Direct database reads are blocked by default.
- Wallet addresses, unrestricted SQL, live API/WebSocket access, execution
  paths, PnL, drawdown, and strategy outputs are blocked by default.
- Conditional source-row access requires explicit justification, at most 50
  rows, source artifact naming, and future audit logging.

Accepted interpretation boundary:

- Allowed wording remains descriptive: `daily replay`, `bounded summary`,
  `event-proximity context`, `aggregate wallet-tier activity`, and `recorded
  scoring diagnostic`.
- Blocked wording remains any phrasing that implies trading action, live
  signal status, private information, misconduct, causality, guaranteed
  prediction, or profitability.

Decision:

- Accept the read-only access contract.
- Keep MCP, agents, model routing, live collection, strategy backtests, and
  audit-log integration deferred.
- Treat `monitor_v2_bounded_summary.csv` as the only default monitor-v2 data
  surface for future interpretation work.
- Do not draft or implement MCP tools until the access contract is enforceable
  by project checks.

Next phase selected:

- Add automated project guardrails for the monitor-v2 read-only summary access
  contract before moving to MCP/agent contract drafting, deterministic
  backtest implementation, or live-collector input specification.

### Read-Only Access Guardrail Enforcement

Review date: 2026-05-20

Review status: enforced by project checks.

Implemented check:

- `operations/project/review_check.py` now verifies the monitor-v2 read-only
  access boundary.

Enforced boundary:

- Required bounded artifacts must exist:
  `data/results/monitor_v2_bounded_summary.csv`,
  `data/results/monitor_v2_bounded_summary_metadata.json`,
  `data/results/thesis_monitor_v2_recorded_scoring.png`, and
  `data/results/thesis_figures_metadata.json`.
- The bounded summary must stay at or below the default 50-row exposure limit.
- The bounded summary must not expose wallet-address columns or
  wallet-address-like values.
- Metadata must declare that the bounded summary contains no wallet addresses
  and no order instructions.
- Raw monitor alert rows, scoring snapshots, recorded input files, direct
  database reads, and source replay files must not appear in the default
  allowed-artifact block.
- Agents, MCP, model routing, live collection, strategy backtests, audit-log
  integration, and execution paths remain deferred.

Tests:

- `tests/test_project_automation.py` covers the passing bounded-summary case,
  missing bounded artifacts, accidental raw-artifact exposure, and accidental
  wallet-address exposure.

Decision:

- The read-only access contract is now enforceable by automation.
- The next safe step is a documentation-only live-input collection contract
  that defines future source inputs, timestamp rules, replay storage,
  validation, and mock/replay tests before any live collector is implemented.

## Monitor V2 Live Input Collection Contract

live_input_collection_contract_status: specified, implementation deferred

Contract date: 2026-05-20

Purpose:

- Define how a future running Polymarket politics/geo anomaly monitor may
  collect read-only inputs.
- Keep the first live-capable design replay-first, testable, and auditable.
- Prevent collector implementation from deciding API scope, timestamp policy,
  bucket cadence, validation, or no-lookahead behaviour during coding.

Verification note:

- API endpoints, authentication requirements, rate limits, and response fields
  must be re-verified against official Polymarket documentation on the
  implementation date.
- This contract fixes source classes and data boundaries, not a hidden
  dependency on the current shape of any live endpoint.

### Allowed Source Classes

`market_discovery`

- Purpose: build and refresh the monitored politics/geopolitical watchlist.
- Allowed source class: Polymarket market/event discovery metadata, such as
  Gamma-style market and event records.
- Output contract: `MarketWatchItem` rows.
- Implementation rule: watchlist membership must be recorded before alerts are
  scored; post-hoc additions must be labelled as diagnostics.

`market_state`

- Purpose: observe market probability, midpoint, best bid/ask, spread, volume,
  open interest, and orderbook-derived diagnostics where validated.
- Allowed source class: public market-state, CLOB, or Market WebSocket data.
- Output contract: `MarketSnapshot` rows.
- Implementation rule: no order placement, no private key, no authenticated
  trading route, and no execution endpoint may be used.

`wallet_activity`

- Purpose: observe aggregate tier-level wallet activity, not individual wallet
  identities.
- Allowed source class: validated local aggregates, Data API style activity
  exports, or later deterministic on-chain aggregation.
- Output contract: `WalletTierSnapshot` rows.
- Implementation rule: alert-facing outputs must never expose wallet-address
  fields. Market-maker exclusions may be filter metadata only.

`event_candidates`

- Purpose: track political/geopolitical news items that may provide reviewed
  event context.
- Allowed source class: manually reviewed sources, news feeds, or later
  discovery agents that produce sourced candidates.
- Output contract: `EventCandidate` rows.
- Implementation rule: machine-collected candidates start as `candidate`.
  They cannot become `accepted` without a source URL, timestamp, and market
  mapping checked before alert interpretation.

### Timestamp And Bucket Policy

Required timestamp fields:

- `collector_received_at_utc`: when the local collector received or wrote the
  observation.
- `source_timestamp_utc`: timestamp supplied by the source, if available.
- `bucket_start_utc` and `bucket_end_utc`: deterministic aggregation window.
- `timestamp_source`: one of `source`, `collector`, or `derived`.

Default bucket cadence:

- First live-capable prototype: 15-minute buckets for alert scoring.
- Daily buckets remain the bridge to current thesis outputs.
- Lower-latency buckets, such as 1-minute or 5-minute market-state snapshots,
  may be recorded as diagnostics only until rate limits, missingness, and
  microstructure interpretation are reviewed.

No-lookahead rule:

- A score for bucket `t` may use the observed value from bucket `t` only after
  that bucket is closed.
- The rolling baseline for bucket `t` must use completed buckets strictly
  before `t`.
- Event candidates may provide context only if their `published_at_utc` or
  `detected_at_utc` is at or before the alert bucket.
- Open buckets may be stored as diagnostics, but they must not produce
  production-like alert severities.

### Replay Storage Contract

The first implementation after this contract should still write recorded files
before any live collector is enabled.

Future replay-first input files:

- `data/results/monitor_v2_live_watchlist.csv`
- `data/results/monitor_v2_live_market_snapshots.csv`
- `data/results/monitor_v2_live_wallet_tier_snapshots.csv`
- `data/results/monitor_v2_live_event_candidates.csv`
- `data/results/monitor_v2_live_input_validation_report.json`
- `data/results/monitor_v2_live_inputs_metadata.json`

Storage rules:

- Files are append-capable source artifacts, not prompt-facing outputs.
- Every row must include source class, source name, timestamp fields, and
  bucket fields.
- Duplicate source rows must be resolved by deterministic primary keys, not by
  row order.
- Collector metadata must record whether rows are mocked, replayed, polled, or
  streamed.
- Raw live input files remain blocked by default under the read-only access
  contract. Future LLM, MCP, or agent layers may read bounded summaries only.

### Validation Contract

`MarketWatchItem` validation:

- market identifiers and token identifiers must be present where available,
  status must be known, and politics/geo category tagging must be explicit.

`MarketSnapshot` validation:

- timestamps must parse to UTC,
- prices, midpoints, and probabilities must be between 0 and 1,
- best bid must not exceed best ask when both are present,
- spread must be non-negative,
- market id and source must be present.

`WalletTierSnapshot` validation:

- timestamp and bucket fields must parse to UTC,
- tier must be one of the documented dataset-relative tiers or an explicit
  aggregate tier,
- active-wallet count, trade count, amount, and concentration fields must be
  non-negative,
- no `wallet_address` field is allowed in monitor-facing input or output
  contracts.

`EventCandidate` validation:

- title, source URL, timestamp, event type, related market ids, and review
  status must be present before the candidate can be used as alert context.
- `accepted` candidates require source and market mapping review.

Validation output:

- validation reports must count accepted rows, rejected rows, duplicates,
  missing fields, invalid timestamps, and invalid numeric ranges.
- invalid rows are excluded from scoring and preserved only as validation
  diagnostics.

### Mock And Replay Test Strategy

Tests required before live collection:

- mocked market snapshots produce known robust-score and percentile outputs,
- repeated replay of the same input files is deterministic,
- baseline windows use only completed prior buckets,
- open buckets cannot produce production-like alerts,
- event candidates after the alert bucket cannot upgrade alert context,
- invalid rows fail validation clearly,
- wallet-address columns fail validation,
- missing baseline returns `insufficient_baseline`,
- no raw live input file becomes a default read-only summary surface.

### Implementation Gate

Before any live API or WebSocket collector is implemented:

- this contract must be reviewed and accepted,
- official API documentation must be checked on the implementation date,
- mock/replay tests must exist,
- validator functions must run without external calls,
- collector output must be replayable from files,
- no order endpoint, private key, trading credential, MCP tool, runtime agent,
  ML model, or strategy backtest may be activated.

Next phase selected:

- Review this live-input collection contract, then decide whether to implement
  a replay-first input batch prototype or to draft the MCP/agent summary
  contract.

### Live Input Collection Contract Review

Review date: 2026-05-20

Review status: accepted for replay-first implementation planning.

Reviewed contract:

- `Monitor V2 Live Input Collection Contract`

Accepted decisions:

- Source classes are accepted: `market_discovery`, `market_state`,
  `wallet_activity`, and `event_candidates`.
- The first live-capable alert-scoring bucket is 15 minutes.
- Daily buckets remain the bridge to current thesis outputs and historical
  validation.
- UTC timestamp fields, bucket boundaries, timestamp-source labels, and source
  metadata are mandatory for future input rows.
- Raw input files stay source artifacts and remain blocked by default for
  prompt-facing, MCP-facing, or agent-facing access.
- No-lookahead is accepted: bucket `t` uses completed prior buckets for its
  rolling baseline, and event context must be detected or published no later
  than the alert bucket.
- Validation rules are specific enough for implementation planning across
  watchlist rows, market snapshots, wallet-tier snapshots, and event
  candidates.

Accepted limitations:

- This review does not verify current live API response fields.
- Official Polymarket documentation must be checked again on the actual
  implementation date.
- The first implementation should validate mocked or replayed files only; it
  should not connect to live APIs or WebSockets.
- Lower-latency market-state observations may be collected only as diagnostics
  until missingness, rate limits, and microstructure interpretation are
  reviewed.

Go/no-go decision:

- Go for a deterministic replay-first input validator/prototype.
- No-go for live API collection, WebSocket streaming, MCP tools, runtime
  agents, strategy backtests, order execution, or trading credentials.

Next phase selected:

- Implement replay-first monitor-v2 live input validators and tests using
  mocked or local fixture files only.

### Live Input Validator Implementation

live_input_validator_status: complete for mocked or local replay files

Implemented module:

- `operations/analysis/monitor_v2_live_input_validation.py`

Implemented tests:

- `tests/test_monitor_v2_live_input_validation.py`

Implemented validation scope:

- `MarketWatchItem` live rows.
- `MarketSnapshot` live rows.
- `WalletTierSnapshot` live rows.
- `EventCandidate` live rows.

Validated contract fields:

- `collector_received_at_utc`
- `source_timestamp_utc`
- `bucket_start_utc`
- `bucket_end_utc`
- `timestamp_source`
- `bucket_status`
- `source_class`
- `source_name`

Validation behaviour:

- Required fields must be present.
- Timestamp fields must parse as timezone-aware UTC-compatible datetimes.
- Bucket start must be before bucket end.
- Closed buckets require collector receipt at or after bucket end.
- `timestamp_source=source` requires a source timestamp.
- Market prices, midpoints, bids, asks, and probabilities must be between 0
  and 1 where present.
- Bid must not exceed ask.
- Counts, amounts, concentration, and liquidity fields must be non-negative.
- Wallet-address fields are rejected in every live input surface.
- Accepted or mapped event candidates require source URLs and related market
  ids.
- Validators return structured reports and can write
  `data/results/monitor_v2_live_input_validation_report.json`.

Boundary:

- The implementation validates local CSV files only.
- It does not call external APIs, WebSockets, databases, LLMs, agents, MCP
  tools, ML systems, order endpoints, or trading credentials.
- It does not generate live data and does not score alerts.

Next phase selected:

- Review the validator shape and decide whether to build a replay-first live
  input batch prototype using local mocked files.

### Live Input Validator Review

Review date: 2026-05-20

Review status: accepted for local replay-first batch prototype.

Reviewed implementation:

- `operations/analysis/monitor_v2_live_input_validation.py`
- `tests/test_monitor_v2_live_input_validation.py`

Accepted coverage:

- Watchlist rows validate source class, market identifiers, token identifiers,
  category, status, timestamp fields, and bucket boundaries.
- Market snapshots validate source class, market and token identifiers,
  probabilities, midpoints, bid/ask values, spread, volume, open interest,
  timestamp fields, and bucket boundaries.
- Wallet-tier snapshots validate aggregate tier fields, non-negative counts
  and amounts, concentration ranges, source/filter metadata, timestamp fields,
  bucket boundaries, and wallet-address exclusion.
- Event candidates validate source class, source URL and market mapping
  requirements for checked or accepted candidates, review states, timestamp
  fields, and bucket boundaries.
- Structured reports record row counts, source classes, bucket-status counts,
  and no-live/no-agent/no-MCP/no-order limitations.

Accepted limitations:

- The validators do not verify current live API response fields.
- The validators do not enforce cross-file market consistency yet; that can be
  added in the local replay-first batch prototype.
- The validators do not score alerts and do not generate market or wallet
  observations.
- Live API/WebSocket collection remains blocked.

Go/no-go decision:

- Go for a local replay-first input batch prototype that generates mocked or
  fixture-based live-style input files, validates them, and writes structured
  metadata.
- No-go for live API calls, WebSocket streaming, MCP tools, runtime agents,
  strategy backtests, order execution, trading credentials, or live alerting.

Next phase selected:

- Implement a local replay-first monitor-v2 input batch prototype that writes
  `monitor_v2_live_*` input files from mocked or fixture data and validates
  them with the accepted validators.

### Local Live Input Batch Prototype

live_input_batch_status: complete for mocked local fixture

Implemented module:

- `operations/analysis/monitor_v2_live_input_batch.py`

Implemented tests:

- `tests/test_monitor_v2_live_input_batch.py`

Generated artifacts:

- `data/results/monitor_v2_live_watchlist.csv`
- `data/results/monitor_v2_live_market_snapshots.csv`
- `data/results/monitor_v2_live_wallet_tier_snapshots.csv`
- `data/results/monitor_v2_live_event_candidates.csv`
- `data/results/monitor_v2_live_input_validation_report.json`
- `data/results/monitor_v2_live_inputs_metadata.json`

Output shape:

- 1 mocked politics/geo watchlist row.
- 4 mocked 15-minute market-state snapshot rows.
- 8 mocked 15-minute aggregate wallet-tier snapshot rows.
- 1 mocked reviewed event-candidate row.
- Validation report status: `pass`.

Implemented safeguards:

- Generated rows use closed 15-minute buckets.
- Generated rows include UTC timestamp fields, source classes, source names,
  bucket boundaries, and bucket status.
- Generated outputs are validated immediately by
  `monitor_v2_live_input_validation.py`.
- Cross-file market consistency is checked so market snapshots, wallet-tier
  snapshots, and accepted event candidates reference watchlist markets.
- Metadata states that the batch uses mocked local fixture data only.

Boundary:

- The prototype does not call Polymarket APIs, WebSockets, databases, LLMs,
  agents, MCP tools, ML systems, order endpoints, or trading credentials.
- It does not score alerts.
- Generated `monitor_v2_live_*` files are source artifacts only and remain
  blocked by default for prompt-facing or MCP-facing access.

Next phase selected:

- Review the local batch output shape before connecting these live-style input
  files to scoring or before drafting any collector implementation.

### Local Live Input Batch Review

Review date: 2026-05-20

Review status: accepted for local deterministic scoring bridge.

Reviewed artifacts:

- `data/results/monitor_v2_live_watchlist.csv`
- `data/results/monitor_v2_live_market_snapshots.csv`
- `data/results/monitor_v2_live_wallet_tier_snapshots.csv`
- `data/results/monitor_v2_live_event_candidates.csv`
- `data/results/monitor_v2_live_input_validation_report.json`
- `data/results/monitor_v2_live_inputs_metadata.json`

Accepted output shape:

- 1 mocked politics/geo watchlist row.
- 4 closed 15-minute market-state snapshot rows.
- 8 closed 15-minute aggregate wallet-tier snapshot rows.
- 1 mocked reviewed event-candidate row.
- Validation report status: `pass`.
- Metadata confirms mocked local fixture data, no external API calls, no
  WebSocket connection, no database write, no LLMs, no agents, no MCP, no ML,
  no order endpoint, and no profitability or private-information claim.

Accepted limitations:

- The generated files are source artifacts for local replay only.
- The fixture is too small for production-like rolling-baseline alerts.
- Any scoring bridge built from this fixture must be labelled diagnostic and
  must not be interpreted as market evidence.
- Real API field verification, WebSocket streaming, scheduling, credentials,
  persistence, MCP access, runtime agents, strategy backtesting, and order
  execution remain blocked.

Decision:

- The output shape is sufficient for a local deterministic scoring bridge.
- The next implementation may convert closed live-style buckets into bounded
  scoring snapshots and produce diagnostic alert artifacts.
- The next implementation must still use local files only, validate inputs
  before scoring, expose no wallet addresses, and keep raw `monitor_v2_live_*`
  input files blocked from prompt-facing or MCP-facing access.

Next phase selected:

- Build a local monitor-v2 live-input scoring bridge that reads the validated
  mocked input files and writes diagnostic scoring outputs without connecting
  to live sources.

### Local Live Input Scoring Bridge

live_input_scoring_status: complete for diagnostic local fixture

Implemented module:

- `operations/analysis/monitor_v2_live_input_scoring.py`

Implemented tests:

- `tests/test_monitor_v2_live_input_scoring.py`

Generated artifacts:

- `data/results/monitor_v2_live_scoring_snapshots.csv`
- `data/results/monitor_v2_live_alert_rows.csv`
- `data/results/monitor_v2_live_alert_summary.csv`
- `data/results/monitor_v2_live_scoring_validation_report.json`
- `data/results/monitor_v2_live_scoring_metadata.json`

Output shape:

- 35 diagnostic scoring snapshot rows.
- 35 diagnostic alert rows.
- 9 compact summary rows.
- 6 non-`none` alert rows in the mocked fixture:
  4 `high`, 1 `watch`, and 1 `info`.

Implementation behaviour:

- Validates all local live-style input files before scoring.
- Uses closed buckets only.
- Converts 15-minute live-style buckets into monitor-v2 scoring snapshots.
- Uses Rule C combined-family confirmation from the existing monitor-v2
  snapshot scorer.
- Uses a deliberately small diagnostic baseline
  (`baseline_observations=3`, `min_baseline_observations=2`) because the
  mocked fixture has only 4 buckets.
- Event candidates annotate only buckets at or after `published_at_utc`, so
  event context is not applied to earlier buckets.

Boundary:

- The output is a diagnostic fixture result, not market evidence.
- It does not call Polymarket APIs, WebSockets, databases, LLMs, agents, MCP
  tools, ML systems, order endpoints, or trading credentials.
- It does not write to the database.
- It contains no wallet addresses and no order instructions.
- Production-like alerts still require at least 20 baseline observations under
  the v2 contract.

Next phase selected:

- Review the local scoring output shape before any replayed real data,
  collector design, MCP access, runtime agent, strategy backtest, or
  order-execution path is added.

### Local Live Input Scoring Review

Review date: 2026-05-20

Review status: accepted for selecting the first real-data replay boundary.

Reviewed artifacts:

- `data/results/monitor_v2_live_scoring_snapshots.csv`
- `data/results/monitor_v2_live_alert_rows.csv`
- `data/results/monitor_v2_live_alert_summary.csv`
- `data/results/monitor_v2_live_scoring_validation_report.json`
- `data/results/monitor_v2_live_scoring_metadata.json`

Observed output:

- 35 scoring snapshot rows.
- 35 alert rows.
- 9 compact summary rows.
- 6 non-`none` diagnostic alerts:
  4 `high`, 1 `watch`, and 1 `info`.
- Alert-row status counts:
  18 `insufficient_baseline`, 11 `ok`, and 6 `zero_mad`.

Interpretation:

- The bridge successfully validates local live-style files, converts closed
  15-minute buckets into scoring snapshots, applies deterministic Rule C
  scoring, and writes bounded row/summary/metadata artifacts.
- The mocked fixture intentionally contains a visible wallet/volume activity
  cluster around `2026-05-20T00:45:00Z`, so the non-`none` alerts demonstrate
  pipeline behaviour rather than empirical Polymarket evidence.
- Event context is applied only from buckets at or after the mocked event
  publication timestamp, preserving the no-lookahead boundary.

Accepted limitations:

- The fixture has only 4 buckets and therefore uses a diagnostic baseline of
  3 observations with minimum 2 baseline observations.
- Production-like monitor alerts still require at least 20 baseline
  observations under the v2 contract.
- Constant concentration and spread values produce `zero_mad` diagnostic rows,
  which is expected for a tiny fixture.
- The output is not evidence of market inefficiency, wallet skill,
  private information, misconduct, profitability, or live readiness.

Decision:

- Accept the local scoring output columns, metadata, and no-lookahead event
  annotation rule.
- Do not add live API or WebSocket collection yet.
- Do not expose raw live input files through prompts, MCP, or runtime agents.
- The next step should specify the first real-data replay boundary before any
  new adapter or collector implementation.

Next phase selected:

- Specify which real or recorded source artifacts may be replayed through the
  live-style contract, what bucket frequency is allowed, and what minimum
  baseline is required before user-facing alert levels can be interpreted.

### First Real-Data Replay Boundary

real_data_replay_boundary_status: selected

Selected boundary:

- `daily_recorded_replay_v1`

Allowed source artifacts:

- `data/results/monitor_v2_recorded_watchlist.csv`
- `data/results/monitor_v2_recorded_market_snapshots.csv`
- `data/results/monitor_v2_recorded_wallet_tier_snapshots.csv`
- `data/results/monitor_v2_recorded_event_candidates.csv`
- `data/results/monitor_v2_recorded_input_validation_report.json`
- `data/results/monitor_v2_recorded_inputs_metadata.json`

Source provenance:

- Market snapshots are derived from `data/thesis.db`, table
  `polymarket_prices`, through the existing recorded-input adapter.
- Wallet-tier snapshots are derived from
  `data/results/h3_tiered_wallet_activity_daily.csv`.
- Event candidates are derived from the existing curated US-election seed.
- No new real events, external APIs, WebSockets, credentials, or live
  collection are added by this boundary.

Bucket frequency:

- Use daily closed replay buckets for the first real-data boundary.
- Do not call this intraday or near-real-time monitoring.
- The 15-minute live-style fixture remains a shape test only until real
  15-minute market and wallet inputs exist with source provenance.

Baseline requirements:

- Use the v2 production-like defaults for daily recorded replay:
  30 prior completed observations and minimum 20 baseline observations.
- If fewer than 20 prior observations exist for a metric, the output must
  report `insufficient_baseline`, not a user-facing production-like alert.
- Diagnostic lower-baseline settings may be used only in tests or mocked
  fixtures and must be labelled diagnostic.

Allowed implementation after this boundary:

- A deterministic Python review or wrapper may compare existing recorded
  scoring outputs against this boundary.
- A future adapter may transform recorded daily inputs into live-style closed
  bucket rows only if it clearly labels the bucket frequency as daily.
- Outputs may be file-based rows, summaries, validation report, metadata, and
  thesis-facing figures.

Blocked after this boundary:

- Live Polymarket API polling.
- WebSocket streaming.
- Runtime agents.
- MCP tools.
- Strategy backtests.
- Order execution or trading credentials.
- Intraday response-speed claims.
- Profitability, causal, insider, private-information, or misconduct claims.

Interpretation:

- The first real-data replay boundary evaluates whether the monitor design can
  reproduce bounded, historical daily alerts from already validated local
  artifacts.
- It is a bridge from thesis evidence to tool design, not a live anomaly
  detector yet.

Next phase selected:

- Review existing recorded daily replay/scoring outputs against
  `daily_recorded_replay_v1` and decide whether the boundary is already
  satisfied or whether a small daily live-style adapter is needed.

### Real-Data Replay Boundary Review

Review date: 2026-05-20

Review status: accepted; existing recorded daily replay satisfies
`daily_recorded_replay_v1`.

Reviewed artifacts:

- `data/results/monitor_v2_recorded_watchlist.csv`
- `data/results/monitor_v2_recorded_market_snapshots.csv`
- `data/results/monitor_v2_recorded_wallet_tier_snapshots.csv`
- `data/results/monitor_v2_recorded_event_candidates.csv`
- `data/results/monitor_v2_recorded_scoring_snapshots.csv`
- `data/results/monitor_v2_recorded_alert_rows.csv`
- `data/results/monitor_v2_recorded_alert_summary.csv`
- `data/results/monitor_v2_recorded_context_rows.csv`
- `data/results/monitor_v2_recorded_scoring_validation_report.json`
- `data/results/monitor_v2_recorded_scoring_metadata.json`

Boundary fit:

- Input validation status: `pass`.
- Watchlist rows: 1.
- Market snapshot rows: 305.
- Wallet-tier snapshot rows: 1236.
- Event candidate rows: 7.
- Baseline: 30 prior completed observations.
- Minimum baseline: 20 prior observations.
- Frequency: daily recorded replay.
- No live API, WebSocket, database write, LLM, agent, MCP, ML, RCP, or order
  execution path.

Recorded scoring output:

- 3394 scoring snapshot rows.
- 3394 alert rows.
- 11 compact alert summary rows.
- 581 non-`none` alert rows.
- Severity counts: 78 `high`, 169 `watch`, 334 `info`, and 2813 `none`.
- Event-context sidecar labels:
  3 `critical_proximity_candidate`, 8 `event_watch_candidate`,
  1 `context_alert`, and 9 `no_event_alert`.

Decision:

- Existing recorded daily replay outputs already satisfy the selected
  real-data replay boundary.
- No daily live-style adapter is needed for the current boundary.
- The local 15-minute live-style fixture remains useful as an interface test,
  while the recorded daily replay remains the real-data evidence bridge.

Interpretation:

- The recorded replay demonstrates that the monitor can score validated daily
  Polymarket and aggregate wallet-tier artifacts with the v2 30/20 baseline
  rule.
- It does not support intraday reaction-speed claims, live monitoring claims,
  wallet profitability claims, private-information claims, misconduct claims,
  or order-execution decisions.

Next phase selected:

- Specify live collector preflight requirements with mocked API/WebSocket
  contracts before any real external Polymarket collection is implemented.

### Read-Only Polymarket Live Collector Preflight

live_collector_preflight_status: selected

Objective:

- Move monitor v2 from historical daily replay and mocked live-style fixtures
  toward real read-only Polymarket data.
- Keep the collector observational: no orders, no authenticated trading
  channel, no execution, no strategy backtest, and no profitability claim.

Candidate Polymarket sources:

- Gamma API, `https://gamma-api.polymarket.com/markets`, for market discovery,
  politics/geopolitics watchlist construction, market questions, condition ids,
  token ids, categories, activity flags, and metadata.
- CLOB public REST, `https://clob.polymarket.com/midpoint`, for token midpoint
  polling where a simple first minute-bucket collector is sufficient.
- CLOB public orderbook or market WebSocket,
  `wss://ws-subscriptions-clob.polymarket.com/ws/market`, for later best bid,
  ask, spread, orderbook, price-change, and trade-event updates.
- Data API, `https://data-api.polymarket.com/trades`, for public trade rows
  by condition id. Trade rows may be aggregated into wallet/activity
  snapshots, but raw wallet-address values must not become monitor-facing or
  prompt-facing outputs.
- Dune may support scheduled historical or on-chain validation, but it is not
  the first minute-level live source.

Minute-bucket decision:

- First implementation bucket: 5 minutes.
- Optional later bucket: 1 minute, only after the 5-minute collector is stable.
- Daily replay remains the thesis evidence bridge; minute buckets are for the
  running monitor prototype.

Required mocked fixtures before each live connector:

- Gamma market-discovery mock response with active politics/geopolitics
  markets and `clobTokenIds`.
- CLOB midpoint/orderbook mock response with token id, price or midpoint, bid,
  ask, spread, volume where available.
- Data API trade mock response with condition id, side, size, price,
  timestamp, and proxy wallet values that are aggregated away before monitor
  outputs.
- WebSocket message mock fixture before any WebSocket loop is implemented.

Validation and persistence rules:

- Every collector output must pass the existing monitor-v2 live input
  validators or a stricter successor.
- Timestamps must be UTC and include collector receipt time, source time when
  available, bucket start, bucket end, source name, source class, and bucket
  status.
- Open buckets may be recorded as diagnostics only; alert scoring uses closed
  buckets.
- Raw source responses may be written only as optional local audit artifacts
  outside prompt/MCP defaults.
- Default monitor-facing outputs remain:
  watchlist rows, market snapshots, aggregate wallet-tier or all-tier
  snapshots, validation reports, metadata, alert rows, summaries, and figures.

Stop/go rules:

- Stop if Polymarket returns geoblock, malformed responses, missing token ids,
  unknown timestamp semantics, or inconsistent market ids.
- Stop if any output contains order instructions or authenticated trading
  fields.
- Stop if wallet-address fields would enter monitor-facing or prompt-facing
  outputs.
- Proceed only when mock tests pass, live calls are read-only, validation
  passes, and metadata states the exact source endpoints and limitations.

Next phase selected:

- Implement a mocked read-only Polymarket collector contract, then a small
  read-only REST collector for Gamma discovery, CLOB midpoint snapshots, and
  Data API trade aggregation.

### Read-Only Polymarket Live Collector Foundation

collector_foundation_status: implemented for first public REST snapshot

Implementation date: 2026-05-22

Implemented modules:

- `operations/collectors/polymarket_readonly.py`
- `operations/analysis/monitor_v2_polymarket_live_figures.py`

Implemented outputs:

- `data/results/monitor_v2_polymarket_live_watchlist.csv`
- `data/results/monitor_v2_polymarket_live_market_snapshots.csv`
- `data/results/monitor_v2_polymarket_live_wallet_tier_snapshots.csv`
- `data/results/monitor_v2_polymarket_live_event_candidates.csv`
- `data/results/monitor_v2_polymarket_live_input_validation_report.json`
- `data/results/monitor_v2_polymarket_live_collection_metadata.json`
- `data/results/monitor_v2_polymarket_live_snapshot.png`
- `data/results/monitor_v2_polymarket_live_figure_metadata.json`

First live run:

- Source mode: `live`.
- Bucket cadence: 5 minutes.
- Public endpoints used: Gamma market discovery, CLOB midpoint, and Data API
  trades.
- Watchlist rows: 2.
- Token midpoint snapshot rows: 4.
- Aggregate wallet/activity rows: 2.
- Event-candidate rows: 0.
- Validation status: pass.

First live scoring bridge output:

- `data/results/monitor_v2_polymarket_live_scoring_snapshots.csv`
- `data/results/monitor_v2_polymarket_live_alert_rows.csv`
- `data/results/monitor_v2_polymarket_live_alert_summary.csv`
- `data/results/monitor_v2_polymarket_live_scoring_validation_report.json`
- `data/results/monitor_v2_polymarket_live_scoring_metadata.json`

Scoring result:

- Snapshot rows: 8.
- Alert rows: 8.
- Alert count: 0.
- Status: all rows are `insufficient_baseline`.

Interpretation:

- The collector can now fetch real public Polymarket market metadata,
  midpoint probabilities, and aggregate trade activity into the monitor-v2
  file boundary.
- The first scoring bridge is a technical pipeline check only. It does not yet
  detect an anomaly because a rolling baseline requires repeated closed
  buckets.
- The current Gamma filter can still surface novelty politics/geopolitics
  markets, so the watchlist needs human review or a stricter curated market
  universe before thesis-facing monitoring.

Limitations:

- REST polling only; no market WebSocket loop yet.
- No best-bid, best-ask, spread, depth, or orderbook fields yet.
- No accepted event candidates in the first live output.
- Wallet activity is aggregate `all_tiers`; no live dataset-relative wallet
  tier universe is selected yet.
- No database writes, runtime agents, MCP tools, ML, strategy backtest, order
  path, profitability claim, or private-information claim.

Next phase selected:

- Build a short rolling read-only history so robust baseline scores can move
  from `insufficient_baseline` to interpretable diagnostic alert states.

### Read-Only Polymarket Rolling History Collector

rolling_history_status: implemented for bounded local runs

Implementation date: 2026-05-22

Implemented modules:

- `operations/collectors/polymarket_rolling_history.py`
- `operations/analysis/monitor_v2_polymarket_rolling_figures.py`

Implemented or updated outputs:

- `data/results/monitor_v2_polymarket_live_watchlist.csv`
- `data/results/monitor_v2_polymarket_live_market_snapshots.csv`
- `data/results/monitor_v2_polymarket_live_wallet_tier_snapshots.csv`
- `data/results/monitor_v2_polymarket_live_event_candidates.csv`
- `data/results/monitor_v2_polymarket_rolling_scoring_snapshots.csv`
- `data/results/monitor_v2_polymarket_rolling_alert_rows.csv`
- `data/results/monitor_v2_polymarket_rolling_alert_summary.csv`
- `data/results/monitor_v2_polymarket_rolling_scoring_validation_report.json`
- `data/results/monitor_v2_polymarket_rolling_scoring_metadata.json`
- `data/results/monitor_v2_polymarket_rolling_history.png`
- `data/results/monitor_v2_polymarket_rolling_history_figure_metadata.json`
- `data/results/monitor_v2_polymarket_rolling_history_metadata.json`

What changed:

- The collector can now run a bounded number of samples and append each closed
  bucket into validated monitor-v2 input files.
- Appended rows are deduplicated by deterministic keys, including long token
  ids that may be read back from CSV with inconsistent dtypes.
- The rolling run automatically validates inputs, scores the current history,
  writes scoring metadata, and generates a rolling-history figure.
- Scoring metadata now records `baseline_readiness` and
  `max_baseline_observations_available`.

First real rolling run:

- Source mode: `live`.
- Bounded samples: 1.
- Bucket cadence: 5 minutes.
- Watchlist rows: 3.
- Token midpoint rows: 6.
- Aggregate wallet/activity rows: 3.
- Event-candidate rows: 0.
- Scoring rows: 12.
- Alert count: 0.
- Baseline readiness: `insufficient_baseline`.

First live watchlist candidates:

- `Xi Jinping out before 2027?`
- `Will Gavin Newsom win the 2028 Democratic presidential nomination?`
- `Will Alexandria Ocasio-Cortez win the 2028 Democratic presidential nomination?`

Interpretation:

- The project now has a real read-only path from Polymarket public data to
  rolling monitor files, scoring diagnostics, and a figure.
- The first tracked run still has only one real closed bucket, so no anomaly
  interpretation is allowed yet.
- Mock tests prove repeated bucket appending and scoring work without network
  access.

Watchlist lesson:

- Gamma market discovery is noisy. Category labels alone can surface sport,
  entertainment, or court-related markets as politics.
- The first collector therefore uses stricter keyword and exclusion filters,
  but a curated live watchlist is still needed before alerts are
  thesis-facing.

Next phase selected:

- Define a curated Polymarket politics/geopolitics watchlist contract before
  interpreting live alert output or expanding to WebSocket/orderbook fields.

### Curated Polymarket Live Watchlist Contract

watchlist_curation_status: implemented as local CSV contract and validator

Implementation date: 2026-05-22

Implemented files:

- `data/monitor_v2_curated_watchlist.csv`
- `data/results/monitor_v2_curated_watchlist_validation_report.json`
- `operations/collectors/polymarket_watchlist.py`
- `tests/test_polymarket_watchlist.py`

Contract columns:

- `watch_id`
- `market_id`
- `condition_id`
- `token_ids`
- `question`
- `category`
- `subcategory`
- `monitoring_scope`
- `review_status`
- `source_url`
- `inclusion_reason`
- `exclusion_reason`
- `reviewed_by`
- `reviewed_at_utc`
- `notes`

Allowed review states:

- `candidate`: auto-discovered or proposed, not monitor-ready.
- `source_checked`: market/source URL checked, but not fully accepted.
- `market_mapped`: market ids and token ids checked.
- `accepted`: eligible for live monitor interpretation.
- `rejected`: explicitly out of scope.
- `needs_followup`: unclear scope, source, or mapping.

Accepted-market requirements:

- source URL is present,
- `reviewed_by` is present,
- `reviewed_at_utc` is present and timezone-aware,
- inclusion reason is present,
- market id, condition id, token ids, question, category, and monitoring
  scope are present,
- question text does not contain excluded sport, entertainment, celebrity,
  religion, or court-noise terms.

Inclusion criteria:

- politics, geopolitics, election, leadership, policy, conflict, or
  international-relations scope,
- clearly mapped Polymarket condition id and token ids,
- monitor relevance is known before inspecting alert output,
- watchlist membership is recorded before alert interpretation.

Exclusion criteria:

- sport competitions or team outcomes,
- entertainment, album, celebrity, religion, or meme markets,
- isolated court/legal markets without a politics/geopolitics link,
- ambiguous or category-only `politics` labels,
- post-hoc additions motivated by an observed alert.

Current seed result:

- Row count: 3.
- Accepted rows: 3.
- Candidate rows: 0.
- Accepted scopes: 2 election, 1 leadership.
- Rows were accepted against official public Gamma market metadata only.

Current accepted rows:

- `Xi Jinping out before 2027?`
- `Will Gavin Newsom win the 2028 Democratic presidential nomination?`
- `Will Alexandria Ocasio-Cortez win the 2028 Democratic presidential nomination?`

Interpretation:

- The live monitor now has a validation-ready watchlist contract.
- The current rows are monitor-ready watchlist rows, but they are not thesis
  event evidence and do not imply any anomaly, signal, or strategy result.
- Gamma discovery remains useful for finding candidates, not for automatically
  defining the monitored universe.

Next phase selected:

- Integrate accepted curated watchlist rows into the read-only collector so
  rolling live collection uses the reviewed universe instead of automatic Gamma
  discovery by default.

### Curated Watchlist Collector Integration

curated_collector_status: implemented

Implementation date: 2026-05-22

Implemented behaviour:

- `operations/collectors/polymarket_readonly.py` accepts an optional
  `curated_watchlist_path`.
- `operations/collectors/polymarket_rolling_history.py` can pass the same
  curated watchlist path into bounded rolling-history collection.
- Only `review_status=accepted` rows from the curated watchlist enter the
  monitor-ready collection output.
- Candidate, rejected, and needs-followup rows remain excluded from
  monitor-ready files.
- Automatic Gamma discovery remains available for candidate discovery and
  tests, but curated rows are the reviewed monitor universe.

Latest curated live run:

- Watchlist rows: 3.
- Token midpoint rows: 6.
- Aggregate wallet/activity rows: 3.
- Event candidate rows: 0.
- Scoring rows: 12.
- Alerts: 0.
- Scoring status: `insufficient_baseline`.

Interpretation:

- The monitor now collects from a reviewed Polymarket politics/geopolitics
  universe.
- The output is a live-data input and scoring shape check, not empirical alert
  evidence yet.
- More closed buckets are needed before rolling-baseline alert interpretation.

Next phase selected:

- Collect bounded rolling-history samples from the accepted curated watchlist
  until metadata shows whether diagnostic baseline scoring is ready.

### Curated Rolling-History Baseline Sample

curated_rolling_baseline_status: diagnostic scores available

Implementation date: 2026-05-22

Latest curated rolling run:

- Source: read-only public Polymarket endpoints.
- Watchlist source: accepted curated watchlist CSV.
- Closed 5-minute buckets: 3.
- Market count: 3.
- Token midpoint rows: 18.
- Aggregate wallet/activity rows: 9.
- Scoring rows: 48.
- Alerts: 0.
- Baseline readiness: `diagnostic_scores_available`.
- Figure: `data/results/monitor_v2_polymarket_rolling_history.png`.

Interpretation:

- This proves the curated rolling-history path can run end to end on real
  public Polymarket data.
- The first diagnostic rolling scores are available, but the baseline is still
  very short and below production-like interpretation standards.
- Zero alerts means Rule C did not trigger on this short observed window; it is
  not evidence that the broader market is quiet.
- Additional real elapsed time remains useful; synthetic timestamp shifting
  should not be used for empirical live-baseline claims.

Next phase selected:

- Build a local read-only dashboard/report view that makes the current
  monitor state understandable without exposing raw wallet data or adding
  trading controls.

### Local Read-Only Dashboard

dashboard_status: implemented

Implementation date: 2026-05-22

Output:

- `data/results/monitor_v2_polymarket_dashboard.html`
- `data/results/monitor_v2_polymarket_dashboard_metadata.json`

Dashboard content:

- market count,
- closed bucket count,
- alert count,
- baseline readiness,
- latest market/token midpoint ranges,
- aggregate wallet/activity diagnostics,
- rolling-history figure,
- alert summary table,
- source artifact references.

Latest dashboard state:

- Markets: 3.
- Closed buckets: 21.
- Alerts: 0.
- Baseline readiness: `baseline_available_zero_mad_or_non_alerting`.
- Latest bucket: `2026-05-22T16:40:00Z`.

Interpretation:

- The dashboard is a local read-only diagnostic view over bounded artifacts.
- It contains no wallet addresses and no trading controls.
- It makes no causal, misconduct, or profitability claim.

Next phase selected:

- Add a bounded refresh runner that collects a configured number of future
  buckets and regenerates the dashboard without becoming a background daemon.

### Bounded Monitor Refresh Runner

refresh_runner_status: implemented

Implementation date: 2026-05-22

Implemented file:

- `operations/collectors/polymarket_monitor_refresh.py`

Output:

- `data/results/monitor_v2_polymarket_refresh_metadata.json`

Behaviour:

- Runs bounded rolling-history collection.
- Regenerates scoring outputs, rolling figure, and static dashboard.
- Requires explicit `samples` and `delay_seconds`.
- Remains a local operator command, not a background daemon.
- Uses accepted curated watchlist rows when configured.

Latest refresh result:

- Source: read-only public Polymarket endpoints.
- Samples completed: 1.
- Closed buckets after refresh: 21.
- Alerts: 0.
- Baseline readiness: `baseline_available_zero_mad_or_non_alerting`.
- Baseline settings: `baseline_observations=30`,
  `min_baseline_observations=20`.
- Production-like baseline available:
  `production_like_baseline_available=true`.
- Dashboard: `data/results/monitor_v2_polymarket_dashboard.html`.

Interpretation:

- The runner is the first practical local operation path for the monitor.
- Twenty-one real closed buckets satisfy the current minimum production-like
  baseline count for review, but the result still needs methodical
  interpretation before thesis-facing live-alert wording.
- Zero alerts means Rule C did not trigger in the observed window, not that the
  broader market is quiet.

Next phase selected:

- Review the 21-bucket production-like baseline before threshold sensitivity,
  watchlist expansion, or a read-only UI/server wrapper.

### Live Monitor Operator Protocol

operator_protocol_status: documented

Implementation date: 2026-05-22

Safe preflight:

```powershell
.\.venv\Scripts\python.exe -m operations.collectors.polymarket_watchlist
```

Single-bucket refresh:

```powershell
.\.venv\Scripts\python.exe -m operations.collectors.polymarket_monitor_refresh --source live --samples 1 --curated-watchlist-input data\monitor_v2_curated_watchlist.csv --max-markets 12
```

Short diagnostic run:

```powershell
.\.venv\Scripts\python.exe -m operations.collectors.polymarket_monitor_refresh --source live --samples 3 --delay-seconds 305 --reset --curated-watchlist-input data\monitor_v2_curated_watchlist.csv --max-markets 12
```

Production-like baseline run from the current v2 contract:

```powershell
.\.venv\Scripts\python.exe -m operations.collectors.polymarket_monitor_refresh --source live --samples 20 --delay-seconds 305 --reset --curated-watchlist-input data\monitor_v2_curated_watchlist.csv --max-markets 12 --baseline-observations 30 --min-baseline-observations 20
```

Dashboard output:

- `data/results/monitor_v2_polymarket_dashboard.html`

Minimum bucket interpretation:

- 1-2 closed buckets: interface and validation check only.
- 3-19 closed buckets: diagnostic rolling scores only.
- 20 or more closed buckets: production-like alert interpretation becomes
  methodologically closer to the v2 contract, but still requires review.

Alert interpretation:

- `alert_count=0` means Rule C did not trigger in the observed window.
- It does not mean the broader market is quiet.
- It does not imply forecast efficiency or inefficiency by itself.
- It does not support causal, misconduct, or profitability claims.

Required review after each run:

- Check `baseline_readiness`.
- Check `bucket_count`.
- Check `severity_counts` and `status_counts`.
- Open the dashboard HTML.
- Inspect whether the watchlist still represents the intended politics/geo
  universe.
- Record notable decisions in `docs/project/WORK_LOG.md` before committing.

### Production-Like Live Monitor Baseline

production_like_live_baseline_status: reviewed

Collection date: 2026-05-22

Review date: 2026-05-22

Review status: accepted as the first production-like read-only live monitor
baseline, with threshold sensitivity required before changing Rule C or making
thesis-facing live-alert claims.

Source:

- Read-only public Polymarket endpoints.
- Reviewed local watchlist:
  `data/monitor_v2_curated_watchlist.csv`.

Reviewed artifacts:

- `data/results/monitor_v2_polymarket_live_market_snapshots.csv`
- `data/results/monitor_v2_polymarket_live_wallet_tier_snapshots.csv`
- `data/results/monitor_v2_polymarket_rolling_scoring_snapshots.csv`
- `data/results/monitor_v2_polymarket_rolling_alert_rows.csv`
- `data/results/monitor_v2_polymarket_rolling_alert_summary.csv`
- `data/results/monitor_v2_polymarket_rolling_scoring_metadata.json`
- `data/results/monitor_v2_polymarket_dashboard.html`
- `data/results/monitor_v2_polymarket_dashboard_metadata.json`
- `data/results/monitor_v2_polymarket_refresh_metadata.json`

Result summary:

- Closed buckets: 21 real 5-minute buckets.
- Reviewed markets: 3.
- Market snapshot rows: 126 token midpoint rows.
- Wallet/activity rows: 63 aggregate tier rows.
- Scoring rows: 372.
- Alerts: 0.
- Severity counts: 372 `none`.
- Status counts: 300 `insufficient_baseline`, 72 `zero_mad`.
- Baseline settings: `baseline_observations=30`,
  `min_baseline_observations=20`.
- Baseline readiness: `baseline_available_zero_mad_or_non_alerting`.
- Production-like baseline available:
  `production_like_baseline_available=true`.

Interpretation:

- The output is the first production-like read-only live baseline under the
  current monitor-v2 30/20 contract.
- `alert_count=0` means Rule C did not trigger in this observed window.
- The result does not prove that the broader market was quiet, efficient, or
  inefficient.
- The result does not support causal, misconduct, private-information, trading,
  or profitability claims.
- The `zero_mad` rows show that some monitored metrics were flat within the
  available baseline; this should be reviewed before threshold changes.

Next phase selected:

- Run threshold sensitivity on the existing bounded production-like artifacts.
- Keep the default Rule C unchanged until the sensitivity output is reviewed.
- Defer watchlist expansion and read-only UI/server wrapper work until the
  threshold-sensitivity report explains whether zero alerts mainly reflect
  strict combined-family confirmation, zero-MAD rows, limited movement, or
  watchlist scope.

### Production-Like Threshold Sensitivity

threshold_sensitivity_status: reviewed

Review date: 2026-05-22

Reviewed artifacts:

- `data/results/monitor_v2_polymarket_threshold_sensitivity.csv`
- `data/results/monitor_v2_polymarket_threshold_sensitivity_by_family.csv`
- `data/results/monitor_v2_polymarket_threshold_sensitivity.png`
- `data/results/monitor_v2_polymarket_threshold_sensitivity_metadata.json`

Result summary:

- Default Rule C with 30/20 settings produced 0 alerts.
- Default rows: 372 total, 300 `insufficient_baseline`, 72 `zero_mad`, and 0
  `ok`.
- The default likely driver is `zero_mad_after_baseline_available`.
- Diagnostic 30/10 produced 0 alerts.
- Diagnostic 10/5 produced 3 `watch` rows.
- Diagnostic 5/3 produced 0 alerts.
- The 10/5 diagnostic watch rows came from active-wallet and concentration
  metrics, not from market-move confirmation.
- Robust z-scores in the diagnostic alerts were below 1; the watch labels were
  driven by percentile rank in a short baseline.

Interpretation:

- The default Rule C should remain unchanged for now.
- The zero-alert result is better explained by flat or sparse short-window
  metrics plus zero-MAD behaviour than by evidence of market quietness.
- Percentile-only shadow rows are useful for diagnostics but should not become
  production-like alerts without a separate reviewed rule change.
- The current three-market watchlist is probably too narrow for the next
  monitor iteration.

Next phase selected:

- Expand the reviewed Polymarket politics/geopolitics watchlist before running
  another production-like live baseline.
- Do not change Rule C thresholds in the watchlist-expansion step.

### Expanded Polymarket Watchlist Review

expanded_watchlist_status: accepted

Review date: 2026-05-22

Reviewed artifacts:

- `data/monitor_v2_curated_watchlist.csv`
- `data/results/monitor_v2_curated_watchlist_validation_report.json`

Source:

- Public Polymarket Gamma market metadata.
- Review was done before any new expanded-watchlist live alert interpretation.

Result summary:

- Accepted watchlist rows increased from 3 to 12.
- Candidate rows: 0.
- Rejected rows: 0.
- Needs-followup rows: 0.
- Validation status: `pass`.
- Temporary read-only collector verification produced 12 watchlist rows, 24
  token midpoint rows, and 12 aggregate wallet/activity rows outside the
  repository result artifacts.

Added monitor coverage:

- US election and midterm control:
  - Republicans win the 2028 US Presidential Election.
  - Democratic Party controls the House after the 2026 midterm elections.
  - Republican Party controls the House after the 2026 midterm elections.
- China/Taiwan:
  - China invades Taiwan by end of 2026.
- Iran:
  - U.S. invades Iran before 2027.
  - Iranian regime falls before 2027.
- Russia/Ukraine:
  - Putin out as President of Russia by December 31 2026.
  - Zelenskyy out as Ukraine president by end of 2026.
  - Ukraine signs peace deal with Russia before 2027.

Interpretation:

- The expanded watchlist improves monitor coverage across electoral politics
  and geopolitical risk.
- These rows are monitor-ready market-universe entries only. They are not
  thesis event evidence, anomaly evidence, signal evidence, or strategy
  evidence.
- Rule C thresholds remain unchanged.

Next phase selected:

- Collect a production-like live baseline using the expanded 12-market
  watchlist and v2 30/20 scoring settings.
- Use `--max-markets 12` for the next expanded-watchlist run.

### Expanded 12-Market Live Baseline

expanded_live_baseline_status: reviewed accepted

Run contract:

- Source: public read-only Polymarket endpoints through the bounded refresh
  runner.
- Watchlist: `data/monitor_v2_curated_watchlist.csv`.
- Market count: 12 reviewed politics/geopolitics markets.
- Samples: 20 real closed 5-minute buckets.
- Baseline settings: `baseline_observations=30`,
  `min_baseline_observations=20`.
- Rule: Rule C combined-family confirmation.
- Database writes: none.
- Agents, MCP, ML, RCP, order execution, and trading credentials: not used.

Latest expanded run:

- Output dashboard:
  `data/results/monitor_v2_polymarket_dashboard.html`.
- Market snapshots:
  `data/results/monitor_v2_polymarket_live_market_snapshots.csv`.
- Wallet/activity snapshots:
  `data/results/monitor_v2_polymarket_live_wallet_tier_snapshots.csv`.
- Scoring rows:
  `data/results/monitor_v2_polymarket_rolling_alert_rows.csv`.
- Summary rows:
  `data/results/monitor_v2_polymarket_rolling_alert_summary.csv`.
- Buckets: 20.
- Token midpoint rows: 480.
- Aggregate wallet/activity rows: 240.
- Scoring rows: 1'416.
- Summary rows: 60.
- Alerts: 0.
- Severity counts: 1'416 `none`.
- Status counts: 1'200 `insufficient_baseline`, 216 `zero_mad`.
- Baseline readiness: `baseline_available_zero_mad_or_non_alerting`.
- Dashboard market count: 12.

Interpretation:

- The expanded live path works end to end on a broader reviewed
  politics/geopolitics universe.
- The zero-alert result means Rule C did not find a combined-family alert in
  this short observed window.
- The result does not prove that Polymarket was efficient, inefficient,
  quiet, tradeable, causal, or driven by private information.
- `insufficient_baseline` remains expected for early rows because each metric
  needs completed prior observations.
- `zero_mad` means the robust baseline was flat for that metric in the
  available window; it should be reviewed as a data/market-state diagnostic,
  not as evidence of absence of activity.

Review decision:

- Accept the expanded-baseline output shape for the first 12-market live
  monitor prototype.
- Keep Rule C unchanged.
- Treat the result as a short-window operational baseline, not as thesis
  evidence about broad Polymarket efficiency.
- Do not relax thresholds only because the baseline produced 0 alerts.
- Improve the read-only reporting/dashboard layer before adding a local server
  wrapper or making thesis-facing live-monitor claims.

Next phase selected:

- Add a small read-only local wrapper over the latest dashboard artifacts.
- Keep refresh collection explicit and manual; the wrapper must not become a
  background daemon, trading surface, agent interface, or MCP implementation.

### Live Dashboard Reporting Refinement

dashboard_reporting_status: improved

The static dashboard now exposes the main monitor state from one read-only
entry point:

- current market count,
- bucket count,
- latest bucket,
- baseline readiness,
- baseline observation settings,
- production-like baseline flag,
- scoring row count,
- summary row count,
- alert count,
- severity counts,
- status counts,
- source artifact links,
- zero-alert interpretation limits.

Interpretation:

- The dashboard is now easier to inspect without opening raw CSV/JSON files.
- It remains descriptive and local.
- It still does not collect data, write the database, use agents or MCP, use
  ML, expose wallet addresses, or provide order instructions.

Next phase selected:

- Add a local read-only wrapper or launcher so the latest dashboard can be
  opened consistently without turning the monitor into a live trading or
  background automation system.

## First Prototype Specification

strategy_prototype_status: specified

The strategy prototype remains a deterministic historical research backtest
design. It is now a later validation path after the anomaly-monitor
specification and first historical anomaly outputs. It defines what a later
Python module must accept, reject, compute, and report before any agent or MCP
layer can use the result.

Primary objective:

- Test whether bounded signal hypotheses derived from H1, H2, or H3 summaries
  have historical predictive value under explicit transaction-cost, slippage,
  position-limit, and evaluation-split assumptions.

Non-objectives:

- No live trading.
- No autonomous execution.
- No guarantee of profitability.
- No agent-computed PnL, drawdown, or risk metrics.
- No use of raw wallet addresses or unrestricted SQL in prompts.

### Candidate Signal Families

These are candidate families for future specification and review. They are not
implemented and are not thesis conclusions.

`h1_forecast_disagreement_signal`

- Source summaries: `data/results/thesis_h1_summary.csv`,
  `data/results/h1_brier_scores.csv`.
- Idea: compare Polymarket probability with a compatible probability forecast
  such as FiveThirtyEight.
- Guardrail: RCP remains excluded until a probability transformation is
  documented and tested.
- Main risk: forecast disagreement may reflect model timing or source
  construction rather than tradable inefficiency.

`h2_event_follow_through_signal`

- Source summaries: `data/results/thesis_h2_summary.csv`,
  `data/results/h2_event_window_summary.csv`.
- Idea: test whether pre-curated event classes produce daily follow-through or
  reversal patterns after the selected event windows.
- Guardrail: no events may be added after looking at returns unless the run is
  explicitly marked as a new sensitivity analysis.
- Main risk: small event count and daily data make overfitting easy.

`h3_wallet_timing_signal`

- Source summaries: `data/results/thesis_h3_summary.csv`,
  `data/results/h3_lead_lag_correlations.csv`,
  `data/results/h3_granger_results.csv`.
- Idea: test whether dataset-relative tier activity predicts next-day or
  multi-day Polymarket probability changes.
- Guardrail: use tier-level aggregates only, not wallet-address-level prompts.
- Main risk: BUY-only source data, daily alignment, and multiple testing.

`combined_summary_signal`

- Source summaries: H1, H2, and H3 thesis summaries only.
- Idea: combine one H1 disagreement condition, one H2 event condition, and one
  H3 tier-activity condition into a sparse hypothesis.
- Guardrail: this is a later sensitivity candidate, not the first baseline.
- Main risk: too many degrees of freedom for the current sample.

### First Baseline Recommendation

The first future backtest, after anomaly outputs exist, should be the simplest
H3-derived daily timing baseline:

- input: tier-level daily activity and daily Polymarket price changes,
- trigger: one pre-specified tier-activity condition,
- horizon: next daily close-to-close probability change,
- benchmark: no-position baseline plus simple always-exposed benchmark if
  methodologically justified,
- output: deterministic `BacktestResult` with costs, slippage, position limit,
  maximum drawdown, and observation count.

Reason:

- H3 already has tier-level daily activity, lead-lag, and Granger diagnostic
  artifacts.
- This avoids introducing RCP, new event selection, intraday data, ML, or raw
  wallet-address prompts.

### Rejection Criteria

A proposed signal specification must be rejected before backtesting if it:

- uses information unavailable at the simulated decision time,
- depends on raw table dumps or wallet-address prompt inspection,
- uses RCP as a probability without the documented transformation flags,
- changes event inclusion after inspecting returns,
- omits transaction costs, slippage, position limits, or evaluation split,
- requires live order execution,
- asks an agent or LLM to calculate metrics,
- cannot cite the deterministic source artifacts it depends on.

## First Deterministic Backtest Baseline Plan

backtest_baseline_status: planned

The first implementation should be a small H3-derived daily timing baseline. It
is a historical research backtest, not a live strategy. The purpose is to test
whether one pre-specified wallet-tier activity signal has out-of-sample
predictive value under explicit assumptions.

### Baseline Name

`h3_top_1pct_lag1_daily_timing_baseline`

### Research Question

Does yesterday's activity change in `tier_1_top_1pct` predict today's daily
Polymarket probability change strongly enough to survive a simple historical
backtest with costs, slippage, position limits, and chronological evaluation?

### Source Artifacts

Required inputs:

- `data/results/h3_tiered_wallet_activity_daily.csv`
- `data/thesis.db`, table `polymarket_prices`

Supporting diagnostics:

- `data/results/h3_lead_lag_correlations.csv`
- `data/results/h3_granger_results.csv`
- `data/results/h3_granger_metadata.json`
- `data/results/thesis_h3_summary.csv`

The implementation must read explicit columns only. It must not use
`SELECT *`, unrestricted SQL, agents, MCP, LLMs, RCP, event catalogs, or raw
wallet-address prompt data.

### Required Input Fields

From `h3_tiered_wallet_activity_daily.csv`:

- `date`
- `tier`
- `total_amount_usd`
- `active_wallets`
- `trade_rows`

From `polymarket_prices`:

- `price_timestamp`
- `price`
- `market_id` only if needed to disambiguate the series.

Derived deterministic fields:

- `daily_price`: one daily closing or last observed Polymarket price per date.
- `price_change`: `daily_price_t - daily_price_t_minus_1`.
- `activity_log`: `log1p(total_amount_usd)`.
- `activity_change`: `activity_log_t - activity_log_t_minus_1`.
- `signal_activity_change`: previous day's `activity_change` shifted forward by
  one day to prevent lookahead.

### Signal Rule

The first baseline is long-only and tier-specific:

- tier: `tier_1_top_1pct`
- signal family: `h3_wallet_timing_signal`
- signal direction: long Trump/YES probability exposure
- decision date: date `t`
- information allowed at decision: activity and price data available through
  date `t-1`
- trigger: `signal_activity_change_t >= training_activity_threshold`
- threshold source: 90th percentile of non-missing `activity_change` values in
  the training split only
- position: `1.0` unit when triggered, otherwise `0.0`
- holding period: one daily close-to-close interval
- outcome: `price_change_t`

The threshold is not a whale threshold. It is a backtest signal threshold
estimated only from the training period. The implementation must report the
threshold value and the split used to estimate it.

### Evaluation Split

The first baseline should use a chronological split:

- training window: first 70 percent of aligned observations,
- evaluation window: final 30 percent of aligned observations,
- threshold estimation: training window only,
- thesis-facing performance summary: evaluation window only,
- optional diagnostic rows: training and full-period rows may be emitted only if
  clearly labelled as diagnostics.

If the evaluation window has too few observations or too few signal days, the
run must return a clear status instead of a strong performance claim.

### Cost, Slippage, And Position Rules

The implementation must make costs explicit and configurable. The first output
should report both gross and net variants:

- gross result: no cost or slippage deducted,
- net result: deduct configured transaction cost and slippage assumptions,
- transaction cost field: `transaction_cost_bps`,
- slippage field: `slippage_probability_points`,
- max position: `1.0` unit exposure,
- no leverage,
- no compounding,
- no short exposure in the first baseline,
- no overlapping positions because holding period is one daily interval.

If no empirically justified cost and slippage assumptions are available, the
metadata must label them as sensitivity assumptions rather than market facts.

### Benchmarks

Required benchmarks:

- `no_position`: always zero exposure and zero PnL.
- `always_long`: one unit exposure over the same evaluation dates.

Optional benchmark:

- `random_signal_same_frequency`, only if a fixed seed is specified and the
  output is clearly labelled as a diagnostic robustness check.

### Required Outputs

Future output artifacts:

- `data/results/strategy_h3_wallet_timing_backtest_rows.csv`
- `data/results/strategy_h3_wallet_timing_backtest_summary.csv`
- `data/results/strategy_h3_wallet_timing_backtest_metadata.json`

Required row-level columns:

- `date`
- `split`
- `daily_price`
- `price_change`
- `signal_activity_change`
- `training_activity_threshold`
- `position`
- `gross_pnl`
- `transaction_cost`
- `slippage_cost`
- `net_pnl`
- `benchmark_always_long_pnl`

Required summary fields:

- `signal_id`
- `split`
- `observation_count`
- `signal_day_count`
- `gross_total_pnl`
- `net_total_pnl`
- `benchmark_always_long_total_pnl`
- `hit_rate`
- `mean_net_pnl`
- `max_drawdown`
- `turnover`
- `transaction_cost_bps`
- `slippage_probability_points`
- `training_activity_threshold`
- `status`
- `limitation`

Required metadata fields:

- source artifact paths,
- generation timestamp,
- code version or latest git commit if available,
- split dates,
- cost and slippage assumptions,
- lookahead prevention rule,
- no-LLM/no-agent/no-MCP declaration,
- BUY-only and daily-alignment limitations.

### Focused Tests For Future Implementation

The future module should add `tests/test_strategy_backtest_baseline.py` and
cover:

- toy data where a previous-day activity spike triggers the next-day position,
- no lookahead: same-day activity must not affect same-day position,
- threshold is estimated from training rows only,
- missing required columns fail with clear errors,
- net PnL is lower than gross PnL when costs or slippage are positive,
- max drawdown is deterministic on a known PnL sequence,
- no signal days produce a clear non-claim status,
- output rows contain no wallet addresses,
- outputs are deterministic across repeated runs.

### Thesis Interpretation Boundary

Allowed wording after implementation:

- `historical daily backtest baseline`
- `exploratory H3-derived signal test`
- `net result under stated cost and slippage assumptions`
- `out-of-sample evaluation window`

Blocked wording:

- `profitable strategy`
- `live trading ready`
- `agent-discovered alpha`
- `proof that whales have private information`
- `guaranteed predictive edge`

The first baseline can support a thesis statement about whether a simple H3
wallet-tier timing signal survives a constrained historical test. It cannot
prove future profitability or autonomous agent value.

## Agent Roles

Agent role type: `Signal Generator`.

`NewsResearchAgent`

- Proposes event or news candidates with source URLs.
- May use Perplexity or web search for discovery.
- Must not add events directly to the canonical event catalog.
- Output: sourced candidate list for human review and deterministic loader.

`MarketPatternAgent`

- Reads bounded H1/H2/H3 thesis summaries.
- Proposes market-pattern hypotheses such as event-window asymmetry or lag
  sensitivity candidates.
- Must not inspect raw Polymarket tables directly.

`WalletSignalAgent`

- Reads wallet-tier summaries, not wallet-address dumps.
- Proposes signal hypotheses based on tier-level timing patterns.
- Must preserve the BUY-only and daily-alignment caveats.

`RiskReviewerAgent`

- Reviews proposed signal specifications for overfitting, lookahead bias,
  excessive degrees of freedom, and forbidden thesis claims.
- Must flag missing transaction-cost, slippage, position-limit, and drawdown
  assumptions.

`Orchestrator`

- Collects candidate signal specifications from agents.
- Sends only validated `SignalSpec` objects to Python backtests.
- Summarises deterministic backtest outputs.
- Logs every LLM call and tool result in `llm_audit_log`.

## MCP Tool Contracts

Future MCP tools must be bounded and summary-first:

- `get_h1_summary`
- `get_h2_summary`
- `get_h3_summary`
- `list_result_artifacts`
- `get_literature_map`
- `submit_signal_spec`
- `get_backtest_result`

Tool rules:

- Summary tools return thesis-facing summaries, not raw tables.
- `submit_signal_spec` validates a proposed signal but does not execute live
  trades.
- `get_backtest_result` returns deterministic backtest outputs that already
  exist or are generated by Python.
- No MCP tool may expose unrestricted SQL or more than 50 raw rows.

## Future Python Interfaces

The future strategy track should define typed interfaces before implementation:

`SignalSpec`

- signal identifier,
- signal family,
- hypothesis statement,
- deterministic source artifacts,
- input summary sources,
- market side or probability direction,
- trigger rule,
- holding or exit rule,
- maximum position size,
- evaluation window,
- lookahead prevention rule,
- rejection criteria,
- assumptions.

`BacktestConfig`

- date range,
- transaction-cost assumption,
- slippage assumption,
- position limit,
- evaluation split,
- benchmark,
- minimum observation count,
- treatment of missing prices or missing signal days,
- random seed if needed.

`BacktestResult`

- signal identifier,
- observation count,
- gross and net return,
- maximum drawdown,
- hit rate,
- turnover,
- cost impact,
- benchmark comparison,
- out-of-sample or walk-forward summary if configured,
- limitations,
- source artifact references.

## Research Workflow

1. Literature and existing thesis summaries define candidate signal families.
2. Agents propose bounded `SignalSpec` drafts.
3. Human review accepts or rejects candidate specs before backtesting.
4. Python validates accepted specs.
5. Python runs historical backtests and writes result artifacts.
6. Agents may interpret only compact backtest summaries.
7. Risk reviewer checks wording and overfitting risks before thesis use.

## Claim Rules

Allowed wording:

- `historical backtest prototype`
- `signal hypothesis`
- `risk-adjusted backtest result`
- `exploratory strategy evidence`
- `under the tested assumptions`

Disallowed wording:

- `guaranteed profitable`
- `live trading ready`
- `autonomous trader`
- `proof of alpha`
- `risk-free`

The thesis may discuss whether the deterministic signals have historical
predictive value. It must not claim that the agent system itself proves market
inefficiency or future profitability.
