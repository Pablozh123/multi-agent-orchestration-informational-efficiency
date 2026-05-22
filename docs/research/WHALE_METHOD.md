# WHALE_METHOD.md

## Current Data Limitation

Current whale-trade inventory has two important limitations:

- Rows appear to be BUY-only.
- The minimum observed `amount_usd` is 10000.

These facts must be treated as data-source or ingestion constraints until
verified. They must not be silently converted into analytical whale definitions.

## Decision Status

- h3_tier_status: selected
- selected_tier_method: wallet_cumulative_amount_usd_percentiles
- lead_time_histogram_status: complete
- lead_lag_status: complete
- granger_status: complete
- blocking_reason: none for the first deterministic daily baseline; result
  review is required before thesis interpretation.
- required_before_code: complete for the initial deterministic lead-lag and
  Granger baseline.

## Allowed Claims

Allowed language:

- Wallet activity shows timing patterns under the specified dataset and model.
- Certain dataset-relative wallet tiers precede or coincide with price movement.
- Granger tests indicate predictive lead-lag structure under model assumptions.
- Results are exploratory or supportive, subject to data limitations.

## Disallowed Claims

Do not claim:

- Proof of insider trading.
- Proof of causal manipulation.
- Proof that a wallet had private information.
- That `amount_usd >= 10000` defines a whale unless it is explicitly marked as
  an upstream source filter.
- That BUY-only data captures full wallet intent.

Avoid insider wording in empirical claims. Use neutral terms such as
`wallet timing`, `early signal`, `lead-lag pattern`, or `predictive structure`.

## Dataset-Relative Wallet Tiers

Wallet tiers must be derived from the actual observed distribution. The
selected primary method is wallet-level cumulative observed `amount_usd`
percentiles.

Tier field:

- Group rows by `wallet_address`.
- Compute `SUM(amount_usd)` per wallet over the observed H3 dataset.
- Compute percentile thresholds from that wallet-level distribution at runtime.
- Do not hardcode USD threshold values.

Selected tiers:

- `tier_1_top_1pct`: wallets at or above the 99th percentile.
- `tier_2_top_5pct`: wallets at or above the 95th percentile and below the
  99th percentile.
- `tier_3_top_10pct`: wallets at or above the 90th percentile and below the
  95th percentile.
- `tier_4_observed_baseline`: wallets below the 90th percentile.

Boundary rule:

- Ties at a percentile boundary are assigned to the higher tier.
- Thresholds are calculated from the observed wallet distribution in the
  filtered dataset used for H3, then documented in output metadata.

Diagnostics:

- `trade_count` and `max_trade_amount_usd` are retained as diagnostics for the
  first H3 implementation.
- They do not define tiers in the primary method.
- Combined rank scores may be considered later as sensitivity analysis, not as
  the primary H3 tier rule.

## Future Distribution-Derived Classification

Before H3 implementation:

- Inspect wallet-level distributions.
- Document whether sell-side rows are absent, unavailable, or filtered out.
- Separate source filters from analytical definitions.
- Compute tier thresholds from observed wallet-level cumulative `amount_usd`
  percentiles.
- Add tests for boundary cases.

Implementation must verify:

- the number of observed wallets,
- the direction distribution,
- the minimum observed `amount_usd` as source-filter metadata,
- percentile thresholds used for tiers,
- tier membership counts,
- boundary behavior for wallets exactly on threshold values.

## Distribution Inventory

Inventory status: complete for the initial observed H3 dataset.

Output file:

- `data/results/h3_wallet_distribution_inventory.json`

Observed inventory:

- trade rows: 25113
- wallets: 3006
- direction distribution: BUY-only in the current data extract
- minimum observed `amount_usd`: 10000.0, documented as source-filter
  metadata only

Runtime percentile thresholds from wallet-level cumulative observed
`amount_usd`:

- `p90`: 120698.45799999998
- `p95`: 234234.58379
- `p99`: 866859.93675

Resulting tier counts:

- `tier_1_top_1pct`: 32
- `tier_2_top_5pct`: 120
- `tier_3_top_10pct`: 150
- `tier_4_observed_baseline`: 2704

The inventory file is compact metadata and does not contain raw wallet address
lists.

## Wallet Tier Classification

Classification status: complete for the initial observed H3 dataset.

Output files:

- `data/results/h3_wallet_tiers.csv`
- `data/results/h3_wallet_tiers_metadata.json`

The classification CSV contains one row per observed wallet with:

- `wallet_address`,
- assigned `tier`,
- wallet-level cumulative observed `amount_usd`,
- `trade_count`,
- `max_trade_amount_usd`,
- first and last observed trade timestamps.

This file is a deterministic H3 analysis input and may contain wallet
addresses. It must not be pasted into LLM prompts or treated as a raw prompt
source. Use compact summaries or bounded aggregates for interpretation layers.

Classification metadata confirms:

- wallets classified: 3006
- trade rows represented: 25113
- tier method: wallet-level cumulative observed `amount_usd` percentiles
- tie policy: thresholds assign ties to the higher tier
- source-filter minimum observed `amount_usd`: 10000.0, not an analytical
  threshold

Resulting tier counts:

- `tier_1_top_1pct`: 32
- `tier_2_top_5pct`: 120
- `tier_3_top_10pct`: 150
- `tier_4_observed_baseline`: 2704

## Tiered Wallet Activity Series

Activity series status: complete for the initial observed H3 dataset.

Output files:

- `data/results/h3_tiered_wallet_activity_daily.csv`
- `data/results/h3_tiered_wallet_activity_metadata.json`

The daily activity series joins deterministic wallet tiers back to observed
trade rows and aggregates by `date` and `tier`. It is a complete daily tier
panel, so tier-days without observed activity are represented with zero values.

Columns:

- `date`
- `tier`
- `trade_rows`
- `active_wallets`
- `total_amount_usd`
- `buy_amount_usd`
- `sell_amount_usd`
- `net_amount_usd`

Metadata confirms:

- trade rows represented: 25113
- wallets with tiers: 3006
- date range: 2024-01-01 to 2024-11-04
- daily tier rows: 1236
- wallet addresses are not present in the daily activity output
- BUY-only source limitation remains documented

This series is an input for later descriptive H3 timing work. It does not
contain Granger tests, causal claims, or proof of misconduct.

## Lead-Time Histograms

Lead-time histogram status: complete for the initial daily H3 timing baseline.

Output files:

- `data/results/h3_lead_time_event_rows.csv`
- `data/results/h3_lead_time_histograms.csv`
- `data/results/h3_lead_time_histograms_metadata.json`

The lead-time outputs align the tiered daily wallet activity series to the
curated H2 event catalog. The selected descriptive window is `[-14d, 0d]`
relative to each curated event date.

The event-row trace contains:

- `event_id`,
- `event_date`,
- activity date,
- `relative_day`,
- wallet tier,
- availability and activity indicators,
- daily tier activity aggregates.

The histogram output aggregates across curated events by wallet tier and
relative day. It includes:

- event count,
- available event-days,
- active event-days,
- active event share,
- total trade rows,
- summed active-wallet observations,
- total and average amount measures.

Limitations:

- The output uses daily alignment only.
- The current activity input is BUY-only under the observed source extract.
- Results are descriptive timing patterns and do not establish causality.
- Granger and lead-lag tests may proceed only as deterministic predictive
  timing tests with the limitations above.

## Lead-Time Output Review

Review date: 2026-05-18

Review status: accepted for the first deterministic daily H3 timing baseline.

Accepted shape:

- 7 curated events from the tracked H2 event seed.
- 4 deterministic wallet tiers.
- 15 daily relative-day bins from `-14` through `0`.
- 420 event-tier-day trace rows.
- 60 tier-by-relative-day histogram rows.
- No wallet addresses in the H3 lead-time outputs.

Persistence decision:

- Keep the row-level trace and histogram outputs as versioned CSV artifacts
  under `data/results/`.
- Do not write H3 timing outputs into `analysis_summaries` until the Granger
  result shape is stable and reviewed.

Decision:

- Proceed to a deterministic daily lead-lag and Granger baseline.
- Use tier-level daily activity measures and daily Polymarket price changes.
- Treat results as predictive timing diagnostics under model assumptions.
- Do not describe results as proof of misconduct or true causal mechanism.

## Lead-Lag And Granger Baseline

Baseline status: complete for the first deterministic daily H3 output.

Output files:

- `data/results/h3_lead_lag_correlations.csv`
- `data/results/h3_granger_results.csv`
- `data/results/h3_granger_metadata.json`

Method:

- Price measure: daily Polymarket price change.
- Activity measure: daily difference of `log1p(total_amount_usd)` by wallet
  tier.
- Lead-lag correlations: activity changes lagged from 0 through 7 days against
  same-day price changes.
- Granger baseline: tier activity change is tested as a predictor of later
  price change for lags 1 through 7.

Output shape:

- 1216 aligned model rows.
- 32 lead-lag correlation rows.
- 28 Granger result rows.
- All generated Granger rows have status `ok`.
- No wallet addresses are present in the output files.

Interpretation limits:

- The output is a deterministic daily baseline, not an intraday reaction-speed
  test.
- The current activity input remains BUY-only under the observed source
  extract.
- Granger p-values indicate predictive timing structure under model
  assumptions. They must not be written as proof of true causality,
  manipulation, or misconduct.
- Multiple-testing and sensitivity choices must be reviewed before thesis
  conclusion wording is finalised.

## Granger Output Review

Review date: 2026-05-18

Review status: accepted for methodological use in the first daily H3 baseline.

Accepted thesis wording:

- The daily H3 baseline tests whether tier-level wallet activity changes have
  predictive timing structure relative to later Polymarket price changes.
- Results may be described as exploratory lead-lag evidence under the chosen
  model and dataset.
- Stronger claims require additional sensitivity checks and, ideally, richer
  trade direction or intraday data.

Disallowed thesis wording:

- Do not write that Granger results prove true causality.
- Do not write that Granger results prove manipulation or misconduct.
- Do not write that BUY-only tier activity captures complete wallet intent.

Persistence decision:

- Keep full H3 lead-lag and Granger outputs as versioned CSV files under
  `data/results/`.
- Do not persist full H3 row-level outputs into `analysis_summaries`.
- A later commit may persist compact H3 summary records after the exact summary
  payload is specified and tested.

Required sensitivity review before final thesis conclusions:

- Multiple-testing treatment across tiers and lags.
- Robustness to different maximum lag windows.
- Robustness to alternative activity measures such as trade-row changes.
- Whether event days should be excluded or modelled separately.
- Whether missing sell-side rows materially limit H3 interpretation.
- Whether intraday data are needed for stronger timing claims.

## V2 Wallet Monitor Contract

wallet_monitor_v2_status: specified

The near-real-time monitor uses wallet information only as aggregate,
dataset-relative tier activity. It must not monitor or expose individual wallet
addresses in alert summaries, LLM-facing outputs, or future MCP tools.

Inputs:

- `WalletTierSnapshot` rows with timestamp bucket, market id, tier,
  active-wallet count, trade count, total observed amount, top-tier share, and
  concentration fields.
- Source-filter metadata, including the current BUY-only limitation and any
  market-maker exclusion list used in the run.
- Market-maker exclusion data from `data/market_maker_exclusions.json` may be
  used as a filter input after validation. It is not evidence that every
  remaining wallet is organic, directional, or informed.

Default transformations:

- Amount activity uses `log1p(total_observed_amount_usd)`.
- Active-wallet and trade-count measures remain count variables.
- Top-tier share and HHI-style concentration are aggregate diagnostics.
- All scoring uses rolling baselines computed from completed prior buckets, or
  from the explicitly documented replay window in historical tests.

Alert families:

- `wallet_tier_activity`: unusual amount, count, or trade-row activity by tier.
- `active_wallet_activity`: unusual active-wallet count by tier.
- `concentration_activity`: unusual top-tier share or HHI-style concentration.
- `wallet_market_cluster`: wallet-tier anomaly combined with a market-move
  anomaly in the same timestamp bucket or review window.

Required limitations in every v2 wallet metadata file:

- Current H3 wallet source is BUY-only unless a later ingestion proves
  otherwise.
- Current source has an upstream minimum observed `amount_usd` of 10000; this
  is not an analytical whale threshold.
- Wallet tiers are dataset-relative and must be recomputed for the monitored
  universe or replay dataset.
- No wallet profitability, private-information, misconduct, or insider wording
  is allowed.
- No individual wallet address may appear in monitor-facing summaries.

Implementation gate:

- The first v2 implementation should use recorded or mocked snapshots before a
  live collector.
- Alert scoring must be deterministic Python and tested on toy data before it
  reads live or replayed Polymarket snapshots.

Live input contract:

- Wallet inputs for any future running monitor must remain aggregate
  `WalletTierSnapshot` rows.
- The default alert-scoring bucket for a first live-capable prototype is 15
  minutes, but daily buckets remain the bridge to current thesis outputs.
- Wallet-tier snapshots must include `collector_received_at_utc`,
  `source_timestamp_utc` when available, `bucket_start_utc`, `bucket_end_utc`,
  `timestamp_source`, `market_id`, `tier`, `active_wallets`, `trade_count`,
  `total_observed_amount_usd`, concentration fields, source, and
  filter-metadata references.
- Any live or replayed wallet row containing a `wallet_address` field must fail
  monitor-facing validation.
- Baselines for bucket `t` must use completed prior buckets only; open buckets
  may be recorded as diagnostics but must not produce production-like alert
  severities.
- Raw wallet snapshot files remain source artifacts and must not become
  prompt-facing or MCP-facing defaults.

Live input contract review:

- Review status: accepted for replay-first implementation planning.
- The wallet portion of the contract is accepted because it preserves the
  aggregate tier boundary and blocks wallet-address fields in future
  monitor-facing inputs.
- The 15-minute default alert bucket is acceptable for a first live-capable
  prototype, while daily buckets remain the bridge to the current thesis
  outputs.
- A future validator must reject wallet-address columns, invalid timestamps,
  negative counts or amounts, and open-bucket rows used as production-like
  alerts.
- Live API or WebSocket collection remains blocked until mocked or replayed
  input validators exist and pass tests.

Live wallet input validator status:

- Validator module:
  `operations/analysis/monitor_v2_live_input_validation.py`.
- Test module:
  `tests/test_monitor_v2_live_input_validation.py`.
- Wallet-tier live inputs are validated as aggregate `WalletTierSnapshot`
  rows.
- The validator rejects wallet-address fields, invalid timestamp or bucket
  fields, unknown tiers, negative active-wallet counts, negative trade counts,
  negative observed amount, and out-of-range concentration fields.
- The validator returns structured reports and does not connect to external
  APIs, WebSockets, databases, agents, MCP tools, or order paths.

Live wallet input validator review:

- Review status: accepted for local replay-first batch prototype.
- The validator is sufficient for aggregate `WalletTierSnapshot` fixture rows
  because it preserves tier-level monitoring and rejects wallet-address
  exposure.
- Remaining gap: cross-file market consistency should be checked in the local
  batch prototype so wallet snapshots cannot reference markets absent from the
  watchlist.
- Live wallet ingestion remains blocked until the local batch prototype
  validates mocked or fixture files deterministically.

Live wallet input batch status:

- Batch module:
  `operations/analysis/monitor_v2_live_input_batch.py`.
- Batch output:
  `data/results/monitor_v2_live_wallet_tier_snapshots.csv`.
- The mocked batch emits 8 aggregate wallet-tier rows across 4 closed
  15-minute buckets and 2 tiers.
- The batch validates all wallet-tier rows with the accepted live input
  validator and checks cross-file market consistency against the watchlist.
- The generated wallet-tier file contains no wallet-address columns and is a
  source artifact only, not a prompt-facing or MCP-facing default.

Live wallet input batch review:

- Review status: accepted for local deterministic scoring bridge.
- The wallet-tier output shape is sufficient for diagnostic local scoring
  because it contains aggregate tier rows, closed 15-minute bucket boundaries,
  UTC collection/source timestamps, non-negative counts and amounts, and
  concentration fields.
- The fixture is not evidence about real wallet behaviour because it is mocked
  and contains only 4 time buckets.
- Any scoring bridge must label outputs as diagnostic fixture results, keep
  BUY-only and source-filter limitations visible, and expose no wallet
  addresses.
- Live wallet ingestion, raw wallet prompt access, wallet profitability,
  private-information wording, MCP access, agents, and order execution remain
  blocked.

Live wallet input scoring status:

- Scoring module:
  `operations/analysis/monitor_v2_live_input_scoring.py`.
- Scoring output:
  `data/results/monitor_v2_live_alert_rows.csv`.
- The diagnostic scoring bridge converts closed aggregate wallet-tier buckets
  into monitor-v2 snapshot rows and scores them with deterministic Rule C
  alert logic.
- The mocked fixture produces wallet-related diagnostic alerts, but these are
  pipeline-shape tests only because the input data are mocked and have only 4
  buckets.
- The output contains no wallet addresses and makes no wallet profitability,
  private-information, misconduct, insider, or live-trading claim.

Live wallet input scoring review:

- Review status: accepted for selecting the first real-data replay boundary.
- The wallet-related diagnostic alerts in the mocked fixture show that the
  bridge can score aggregate tier activity and active-wallet counts at
  15-minute bucket granularity.
- These alerts are not evidence about real wallet behaviour because the inputs
  are mocked, the baseline is deliberately small, and only 4 buckets exist.
- Production-like wallet alert wording remains blocked until a replay or live
  dataset has at least the v2 minimum baseline observations and reviewed source
  provenance.
- The next boundary must decide whether wallet activity can be replayed from
  daily H3 aggregates, a recorded local ingestion file, or a future validated
  Data API/CLOB-derived aggregate. It must not expose raw wallet addresses.

First wallet real-data replay boundary:

- Selected boundary: `daily_recorded_replay_v1`.
- Allowed wallet source:
  `data/results/monitor_v2_recorded_wallet_tier_snapshots.csv`, derived from
  `data/results/h3_tiered_wallet_activity_daily.csv`.
- Allowed bucket frequency: daily closed replay buckets only.
- Minimum baseline: 20 prior completed daily observations for
  production-like alert interpretation.
- The replay remains aggregate and tier-level. It does not expose wallet
  addresses.
- The BUY-only source limitation and upstream minimum observed `amount_usd`
  remain visible as source-filter metadata, not analytical whale thresholds.
- Future 15-minute wallet monitoring requires a separately validated aggregate
  wallet ingestion source. It cannot be inferred from the current daily H3
  panel.

Wallet real-data replay boundary review:

- Review status: accepted for daily recorded replay.
- Existing `data/results/monitor_v2_recorded_wallet_tier_snapshots.csv`
  satisfies the first wallet boundary because it is daily, aggregate,
  tier-level, validated, and contains no wallet-address columns.
- Existing recorded scoring keeps BUY-only and source-filter limitations in
  metadata and summary limitations.
- No additional daily wallet adapter is needed for the current boundary.
- Future live or 15-minute wallet monitoring remains blocked until a validated
  aggregate source can provide timestamped tier snapshots without exposing raw
  wallet addresses.

Read-only live wallet source decision:

- First live-capable source candidate: Polymarket Data API trade rows queried
  by condition id.
- First monitor-facing aggregation: `all_tiers` aggregate wallet/activity
  rows, because dataset-relative wallet tiers for new live markets are not yet
  established.
- Allowed aggregate fields: active-wallet count, trade count, observed amount,
  top-wallet share, and HHI-style concentration computed inside Python and
  emitted without wallet addresses.
- Dune can later validate or enrich historical/on-chain activity, but it is
  not the first minute-level source.
- Raw wallet addresses may be used transiently inside Python for aggregation
  but must not be written to monitor-facing CSVs, bounded summaries, prompts,
  MCP tools, or figures.
- Future tiered live wallet monitoring requires a documented market-universe
  tiering rule or a reviewed wallet-tier map. It must not reuse the current
  H3 election-wallet tier thresholds as universal Polymarket thresholds.

Snapshot prototype status:

- A first deterministic snapshot prototype exists in
  `operations/analysis/monitor_v2_snapshot.py`.
- It produces aggregate mock wallet-tier, active-wallet, and concentration
  diagnostics without wallet addresses.
- Output files are:
  `data/results/monitor_v2_alert_rows.csv`,
  `data/results/monitor_v2_alert_summary.csv`, and
  `data/results/monitor_v2_metadata.json`.
- The current output is a mocked contract test, not a real-time wallet monitor
  and not evidence of wallet performance.

Snapshot output review:

- The wallet-facing output shape is accepted for aggregate monitor use.
- Wallet-related monitor rows stay at tier or concentration level.
- No wallet addresses appear in monitor v2 row or summary outputs.
- The current mock output contains percentile-only `watch` alerts. Before
  wallet-tier replay data are used, threshold sensitivity must decide whether
  percentile-only wallet alerts need a minimum robust z-score or confirmation
  from another anomaly family.

Threshold decision:

- Rule C, combined-family confirmation, is selected for the first monitor v2
  default.
- Isolated single-family percentile-only wallet alerts are downgraded to
  `info`.
- Wallet-related `watch` alerts should be interpreted only when confirmed by
  another anomaly family in the same market and timestamp, unless the wallet
  family is itself a very strong `high` row.
- This reduces isolated wallet-noise risk before real replay or live data.

Historical replay status:

- A first daily historical replay exists and uses aggregate wallet-tier
  activity only.
- Replay artifacts:
  `data/results/monitor_v2_historical_replay_snapshots.csv`,
  `data/results/monitor_v2_historical_replay_alert_rows.csv`,
  `data/results/monitor_v2_historical_replay_alert_summary.csv`, and
  `data/results/monitor_v2_historical_replay_metadata.json`.
- The replay produces wallet-facing `info`, `watch`, and `high` rows, but no
  `critical` rows under the strict Rule C event-context requirement.
- The replay output shape is reviewed and accepted for the first daily
  historical monitor baseline.
- Zero `critical` rows are interpreted as strict same-day event-context
  behaviour, not as proof that no meaningful event-adjacent wallet clusters
  exist.
- Event-day wallet clusters appear in aggregate tier rows around the Biden-
  Trump debate, Biden withdrawal, Walz VP pick, and Harris-Trump debate.
- Before any live wallet monitoring, a deterministic event-proximity
  sensitivity check should compare same-day event context with a small daily
  proximity window, initially `[-1d, +1d]`.
- A separate `event_watch` label may be useful for reviewed event-proximity
  wallet clusters that do not also have confirmed market-move anomalies.
- No wallet addresses may appear in monitor-facing summaries.

Event-proximity sensitivity status:

- Sensitivity module:
  `operations/analysis/monitor_v2_event_proximity_sensitivity.py`.
- Output files:
  `data/results/monitor_v2_event_proximity_sensitivity_rows.csv`,
  `data/results/monitor_v2_event_proximity_sensitivity_summary.csv`, and
  `data/results/monitor_v2_event_proximity_sensitivity_metadata.json`.
- Same-day `critical` candidates: 0.
- `[-1d, +1d]` event-proximity `critical` candidates: 6.
- `[-1d, +1d]` event-proximity `event_watch` candidates: 6.

Decision:

- Use `[-1d, +1d]` as the daily event-context window for reviewed replay
  outputs.
- Keep `critical` strict and require market movement plus wallet or
  concentration anomaly plus reviewed event context.
- Use `event_watch` only as a separate descriptive label for wallet or
  concentration clusters near reviewed events without market-move
  confirmation.
- Do not treat `event_watch` as evidence of causality, misconduct,
  profitability, or private information.

Proximity label integration status:

- Historical replay now writes
  `data/results/monitor_v2_historical_replay_context_rows.csv`.
- Metadata records context label counts:
  6 `critical_proximity_candidate`, 6 `event_watch_candidate`, 1
  `context_alert`, and 8 `no_event_alert` rows.
- The original replay alert severity rows remain unchanged; the context file is
  a sidecar for event-proximity interpretation.

## Event-Centred Wallet Anomaly Monitor

Anomaly-monitor status: complete for the first historical daily output.

The H3-adjacent monitor does not start with wallet-level profitability. The
current data are BUY-only and lack complete exit, sell-side, and position
information. The safe first step is therefore an event-centred anomaly monitor
over aggregate wallet-tier activity.

Primary question:

- Do dataset-relative wallet tiers show unusual aggregate activity around
  sourced politics/geopolitical event candidates or unusual market moves?

Allowed inputs:

- `data/results/h3_tiered_wallet_activity_daily.csv`
- `data/results/h3_lead_time_histograms.csv`
- `data/results/h3_lead_lag_correlations.csv`
- curated event files with source URLs and timestamps
- daily Polymarket price/probability series

Allowed diagnostics:

- tier-level z-score or percentile-rank activity spikes,
- active-wallet count anomalies by tier,
- total observed amount anomalies by tier,
- top-tier share and concentration summaries,
- event-window alignment at the available daily frequency.

Required limitations:

- BUY-only source limitation remains visible in every metadata file.
- No wallet addresses in monitor-facing or LLM-facing summaries.
- No wallet profitability metric until complete position and exit data exist.
- No private-information, misconduct, or insider wording.
- No intraday timing claim unless intraday data are collected and validated.

The monitor may later feed a deterministic backtest, but only after the
anomaly definition, baseline windows, alert thresholds, and validation windows
are specified before inspecting results.

Implemented v1 output files:

- `data/results/h3_event_wallet_anomaly_rows.csv`
- `data/results/h3_event_wallet_anomaly_summary.csv`
- `data/results/h3_event_wallet_anomaly_metadata.json`

Implemented v1 shape:

- 7 curated US-election events.
- 5 daily event-window days from `-1` through `+3`.
- Baseline window `[-30d, -8d]`, separated from the event window.
- 350 row-level diagnostics.
- 70 compact summary rows.
- No wallet addresses in the output files.

Implemented v1 diagnostic families:

- market-move anomaly,
- wallet-tier amount anomaly,
- active-wallet anomaly,
- top-tier concentration anomaly.

The output is descriptive and historical. It is not a near-real-time collector,
not a backtest, and not evidence of wallet profitability.

## Read-Only Live Wallet Activity Foundation

Implementation date: 2026-05-22

Status: implemented for first aggregate Polymarket Data API snapshot.

Implemented artifact:

- `data/results/monitor_v2_polymarket_live_wallet_tier_snapshots.csv`

Current live monitor-facing wallet fields:

- `market_id`
- `tier`
- `active_wallets`
- `trade_count`
- `total_observed_amount_usd`
- `top_tier_share`
- `hhi_concentration`
- `filter_metadata`

First live run:

- Source: public Polymarket Data API trades endpoint.
- Bucket cadence: 5 minutes.
- Market rows: 2.
- Tier value: `all_tiers`.
- Active wallets in the collected bucket: 0 for both selected markets.
- Trade count in the collected bucket: 0 for both selected markets.
- Wallet-address columns: none.

Interpretation:

- The live collector can now create monitor-facing aggregate wallet/activity
  rows without exposing wallet addresses.
- The first bucket contains no observed trades for the selected watchlist, so
  it is a pipeline validation result, not evidence about wallet behaviour.
- Live wallet tiers are not yet globally defined. The historical H3 election
  percentile tiers must not be reused for arbitrary new markets without a
  documented live-tier universe or reviewed tier map.

Next methodological requirement:

- Repeated closed buckets are needed before wallet activity can be scored
  against a rolling baseline.
- A stricter watchlist or human-reviewed market universe is needed before
  wallet anomalies are interpreted in thesis-facing language.

## Read-Only Rolling Wallet Activity Review

Review date: 2026-05-22

Review status: accepted as a collector-path diagnostic, not as wallet
evidence.

Reviewed artifact:

- `data/results/monitor_v2_polymarket_live_wallet_tier_snapshots.csv`

Current live run:

- Bucket cadence: 5 minutes.
- Watchlist markets: 3.
- Aggregate wallet/activity rows: 3.
- Tier value: `all_tiers`.
- Active-wallet rows with observed activity: 1 of 3.
- Largest observed amount in the bucket: 52.92104 USD.
- Wallet-address columns: none.

Interpretation:

- The rolling collector can carry public trade activity into aggregate
  wallet/activity rows.
- The first clean watchlist run is still too short for a rolling wallet
  baseline.

Limitation:

- `all_tiers` remains a temporary live-monitor aggregate.
- Dataset-relative wallet tiers for arbitrary live markets are not selected
  yet.
- No wallet-level performance, private-information, or misconduct claim is
  allowed.

## Historical Anomaly Output Review

Review date: 2026-05-20

Review status: accepted as the first historical daily anomaly diagnostic.

Reviewed artifacts:

- `data/results/h3_event_wallet_anomaly_rows.csv`
- `data/results/h3_event_wallet_anomaly_summary.csv`
- `data/results/h3_event_wallet_anomaly_metadata.json`
- `data/results/thesis_h3_event_wallet_anomalies.png`

What was investigated:

- Whether the seven curated US-election events show unusual daily market moves,
  wallet-tier amount activity, active-wallet counts, or top-tier concentration
  relative to a separated pre-event baseline.

How it was derived:

- Baseline window: `[-30d, -8d]`.
- Event window: `[-1d, +3d]`.
- Anomaly flag: upper-tail z-score at least 2.0 or percentile rank at least
  0.95 with observed value above baseline mean.
- Inputs: daily Polymarket prices and aggregated tiered wallet activity.

Key results:

- Total anomaly-day counts: active-wallet 43, wallet-tier amount 40,
  market-move 5, top-tier concentration 4.
- Event-level anomaly totals: Biden withdrawal 30, Biden-Trump debate 16,
  Vance VP pick 13, Harris-Trump debate 13, Walz VP pick 9, Trump shooting 6,
  Trump conviction 5.
- Strongest single row: Biden withdrawal day 0 in observed-baseline active
  wallets, maximum z-score 13.68.
- Strong market-move rows appear around Trump shooting and Vance VP pick, each
  reflecting an absolute daily Polymarket price change of about 0.08.

Allowed interpretation:

- The historical monitor can identify days and events where aggregate wallet
  activity or market movement is unusual relative to a pre-event baseline.
- Biden withdrawal is the strongest multi-family anomaly cluster in the
  current curated event set.

Limitations:

- Daily alignment only.
- BUY-only wallet activity extract.
- Small seven-event validation set.
- No proof of causality, private information, misconduct, wallet
  profitability, or future tradability.

## No Insider Wording

The thesis may discuss whether wallet data provide early signals. It must not
describe wallets as insiders, insider traders, or proof of insider activity
unless there is independent non-market evidence, which is not currently in
scope.
