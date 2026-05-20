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
