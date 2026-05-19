# RESEARCH_SPEC.md

## Research Objective

The thesis evaluates the informational efficiency of decentralized prediction
markets, using Polymarket as the main case and comparing it with traditional
forecast or polling sources where the data are methodologically compatible.

The empirical focus is the 2024 US presidential election. The project asks
whether Polymarket prices are better calibrated, react faster to curated public
events, and whether wallet activity contains dataset-relative early signal
patterns.

## Operationalising Informational Efficiency

Informational efficiency is measured through deterministic proxy tests rather
than asserted directly. The thesis treats Polymarket's probability path as the
primary market time series and asks whether that path is accurate, responsive,
and preceded by observable wallet activity.

H1 measures forecast quality:

- Primary object: daily Polymarket probability for the 2024 US presidential
  election outcome.
- Comparison sources: FiveThirtyEight probability rows and deterministic
  baselines.
- Metric family: Brier Score, calibration/reliability where appropriate, and
  Diebold-Mariano comparison of loss series.
- Interpretation: lower loss supports better forecast quality over the tested
  overlap window, not faster information integration by itself.

H2 measures event-window response:

- Primary object: Polymarket daily probability changes around pre-curated
  public events.
- News handling: news articles are not interpreted freely by an LLM; they enter
  the empirical design only as curated, sourced events with fixed timestamps.
- Metric family: daily event-window abnormal changes and compact CAR-style
  summaries.
- Interpretation: event-window movement supports claims about daily reaction
  patterns, not intraday speed unless intraday prices are added later.

H3 measures early-signal structure:

- Primary object: dataset-relative wallet-tier activity before or around market
  price changes.
- Metric family: distribution-derived wallet tiers, daily activity panels,
  lead-time histograms, lead-lag correlations, and Granger tests.
- Interpretation: results can support predictive timing diagnostics under model
  assumptions, not proof of true causality or private information.

Context sources:

- Traditional polls and forecasts provide comparison signals when their
  probability interpretation is documented.
- GDELT/news sentiment remains contextual until a separate validation note
  justifies using it as a deterministic empirical variable.
- Literature from Perplexity, Zotero, or local PDFs informs theory and
  methodology. It is not an empirical result unless translated into a
  deterministic, tested data pipeline.

Strategy prototype boundary:

- A backtested strategy prototype may be included as a research extension after
  H1-H3 summaries are stable.
- Agents may propose signal hypotheses, but Python must validate, backtest, and
  calculate all results.
- No live trading, no profit guarantee, and no autonomous trading claims are in
  scope for the thesis.

## Thesis Methodology Outline

This outline is the working bridge from deterministic outputs and indexed
literature to the thesis methods chapter. It is not a new analysis pipeline.

### 1. Research Design

Core question:

- To what extent do decentralized prediction-market prices on Polymarket
  reflect, integrate, and anticipate information during the 2024 US election?

Operational design:

- Informational efficiency is not treated as directly observable.
- The thesis uses three deterministic proxy layers: H1 forecast quality, H2
  event-window response, and H3 wallet-tier timing diagnostics.
- Literature motivates the proxy choice; Python result artifacts provide the
  empirical evidence.

Literature anchors:

- `zotero_poly_001` for Polymarket-specific transaction accounting and market
  maturation context.
- `zotero_poly_002` for the prediction-market-versus-polling comparison frame.
- `zotero_poly_006` and `zotero_poly_007` for microstructure, volatility, bias,
  and risk caveats.
- `lit_emh_001` for the canonical efficient-market-hypothesis framing.
- `zotero_poly_004` is rejected and must not be cited.

### 2. Data Sources

Primary empirical sources:

- Daily Polymarket probabilities from `data/thesis.db`.
- FiveThirtyEight probability forecasts where rows are probability forecasts.
- Curated event seed from `data/events_timeline_seed.csv`.
- Wallet transaction extract from `data/thesis.db`, with BUY-only and upstream
  minimum-amount limitations documented.

Context sources:

- RCP remains a polling signal until a probability transformation exists.
- GDELT/news sentiment remains contextual until a separate validation note
  makes it an empirical variable.
- Literature and web articles are used for framing and hypothesis discipline,
  not as replacements for deterministic outputs.

### 3. H1 Forecast Quality

Question:

- Are Polymarket probabilities better calibrated or lower-loss forecasts than
  comparable traditional probability forecasts?

Deterministic artifacts:

- `data/results/h1_brier_scores.csv`
- `data/results/h1_diebold_mariano.json`
- `data/results/h1_reliability_curve.png`
- `data/results/thesis_h1_summary.csv`

Allowed claim type:

- Polymarket has lower or higher forecast loss over the tested overlap window.

Blocked claim type:

- H1 alone does not prove faster information integration.
- RCP must not enter H1 until its probability transformation is documented.

### 4. H2 Event-Window Response

Question:

- Do Polymarket probabilities move around pre-curated public events in the
  expected direction and within selected daily windows?

Deterministic artifacts:

- `data/events_timeline_seed.csv`
- `data/results/h2_event_window_rows.csv`
- `data/results/h2_event_window_summary.csv`
- `data/results/thesis_h2_summary.csv`

Allowed claim type:

- Daily event-window movements are consistent or inconsistent with fast public
  information integration at daily resolution.

Blocked claim type:

- No intraday reaction-speed claim is allowed without intraday data.
- Events must not be added or removed after inspecting Polymarket reactions.

### 5. H3 Wallet-Tier Timing Diagnostics

Question:

- Do dataset-relative wallet tiers show activity patterns before or around
  Polymarket price changes?

Deterministic artifacts:

- `data/results/h3_wallet_distribution_inventory.json`
- `data/results/h3_wallet_tiers.csv`
- `data/results/h3_tiered_wallet_activity_daily.csv`
- `data/results/h3_lead_time_histograms.csv`
- `data/results/h3_lead_lag_correlations.csv`
- `data/results/h3_granger_results.csv`
- `data/results/thesis_h3_summary.csv`

Allowed claim type:

- Wallet-tier activity contains descriptive timing patterns or predictive
  lead-lag diagnostics under the tested model.

Blocked claim type:

- No proof of true causality, private information, misconduct, or insider
  trading.
- No fixed USD whale threshold as the analytical tier definition.

### 6. Strategy Research Prototype

Question:

- Can H1-H3 outputs motivate bounded signal hypotheses that are later tested in
  historical Python backtests?

Scope:

- Strategy work is a research extension after H1-H3, not the core proof of
  informational efficiency.
- Agents may later draft `SignalSpec` hypotheses from bounded summaries.
- Python must validate all signal specs and calculate all backtest, PnL, and
  risk metrics.

Blocked claim type:

- No live trading, autonomous order execution, profit guarantee, or
  agent-calculated metrics.

### 7. Interpretation And Thesis Wording

Result interpretation must follow this hierarchy:

- Deterministic source artifact first.
- Method note and limitation second.
- Literature support third.
- LLM or agent interpretation only later, from bounded summaries and logged in
  `llm_audit_log`.

Approved thesis-facing wording remains:

- `forecast-quality comparison`
- `daily event-window response`
- `dataset-relative wallet tier`
- `descriptive timing pattern`
- `predictive timing diagnostic`
- `historical backtest prototype`

## Thesis Tables And Figures Plan

This plan lists the first thesis-facing tables and figures. It uses existing
deterministic artifacts only and does not request new calculations.

### Core Tables

Table 1: Data and source inventory

- Source artifact: `data/results/thesis_result_summary_metadata.json`
- Supporting artifacts: `data/events_timeline_seed.csv`,
  `data/literature/literature_index.csv`
- Thesis role: describe empirical sources, result artifacts, and literature
  source control.
- Status: ready as a compact descriptive table.

Table 2: H1 forecast-quality summary

- Source artifact: `data/results/thesis_h1_summary.csv`
- Supporting artifacts: `data/results/h1_brier_scores.csv`,
  `data/results/h1_diebold_mariano.json`
- Thesis role: report Brier, baseline, and Diebold-Mariano comparison outputs.
- Status: ready with RCP exclusion caveat.

Table 3: H2 daily event-window summary

- Source artifact: `data/results/thesis_h2_summary.csv`
- Supporting artifacts: `data/results/h2_event_window_summary.csv`,
  `data/results/h2_event_window_rows.csv`
- Thesis role: report selected daily event-window responses and limitations.
- Status: ready with daily-window caveat.

Table 4: H3 wallet-tier and timing summary

- Source artifact: `data/results/thesis_h3_summary.csv`
- Supporting artifacts: `data/results/h3_wallet_distribution_inventory.json`,
  `data/results/h3_lead_time_histograms.csv`,
  `data/results/h3_lead_lag_correlations.csv`,
  `data/results/h3_granger_results.csv`
- Thesis role: report dataset-relative wallet tiers, timing patterns, and
  Granger diagnostic shape.
- Status: ready with BUY-only, daily-alignment, and non-causal caveats.

Table 5: Literature-to-methodology map

- Source artifact: `data/literature/literature_index.csv`
- Supporting artifact: `docs/research/LITERATURE_MAP.md`
- Thesis role: show which sources support H1, H2, H3, strategy prototype, and
  architecture framing.
- Status: ready for internal thesis planning; final citation table requires
  full-paper review before sources move from `skimmed` to `reviewed` or
  `cited`.

### Core Figures

Figure 1: H1 reliability curve

- Source artifact: `data/results/h1_reliability_curve.png`
- Supporting artifact: `data/results/h1_brier_scores.csv`
- Thesis role: visualise calibration/reliability for H1.
- Status: ready.

Figure 2: H2 event-window movement overview

- Figure artifact: `data/results/thesis_h2_event_window_car.png`
- Source artifact: `data/results/h2_event_window_summary.csv`
- Supporting artifact: `data/results/h2_event_window_rows.csv`
- Thesis role: visualise final CAR-style daily event-window movements.
- Status: ready.

Figure 3: H3 wallet-tier distribution

- Figure artifact: `data/results/thesis_h3_wallet_tier_counts.png`
- Source artifact: `data/results/h3_wallet_distribution_inventory.json`
- Supporting artifact: `data/results/h3_wallet_tiers.csv`
- Thesis role: visualise dataset-relative wallet tier cutoffs and counts.
- Status: ready.

Figure 4: H3 lead-time histogram

- Figure artifact: `data/results/thesis_h3_lead_time_amount.png`
- Source artifact: `data/results/h3_lead_time_histograms.csv`
- Supporting artifact: `data/results/h3_lead_time_event_rows.csv`
- Thesis role: visualise descriptive tier activity around selected movements or
  events.
- Status: ready; no new interpretation beyond descriptive timing patterns.

Figure 5: H3 lead-lag or Granger diagnostic overview

- Figure artifact: `data/results/thesis_h3_granger_pvalues.png`
- Source artifact: `data/results/h3_granger_results.csv`
- Supporting artifacts: `data/results/h3_lead_lag_correlations.csv`,
  `data/results/h3_granger_metadata.json`
- Thesis role: summarise predictive timing diagnostics.
- Status: ready; must include multiple-testing and non-causal caveats.

Figure metadata:

- Source artifact: `data/results/thesis_figures_metadata.json`
- Status: ready.

### Excluded Or Deferred Visuals

- No RCP probability-comparison figure until a probability transformation is
  documented.
- No intraday H2 reaction-speed figure until intraday Polymarket data are
  collected and validated.
- No wallet-address-level figure in the thesis-facing layer.
- No strategy PnL, drawdown, or agent-orchestration figure until a historical
  backtest prototype exists and is tested in Python.

## Thesis Results Narrative Skeleton

This skeleton defines how the first results chapter can explain what was
investigated, how the result was derived, what the thesis may conclude, and
which follow-up analyses remain open. It does not add new empirical results.

### Results Chapter Opening

Purpose:

- State that informational efficiency is evaluated through three deterministic
  proxy layers rather than assumed directly.
- Explain that Polymarket's daily probability path is the primary market
  series, while FiveThirtyEight, curated events, and wallet activity provide
  comparison, information-integration, and timing-diagnostic views.
- Emphasise that all reported metrics come from versioned Python outputs under
  `data/results/`.

Evidence to cite:

- Table 1: data and source inventory.
- `data/results/thesis_result_summary_metadata.json`.
- Literature anchors `lit_emh_001`, `zotero_poly_001`, `zotero_poly_002`, and
  `zotero_poly_006`.

Allowed interpretation:

- The thesis tests observable efficiency proxies in one election case study.

Limitation:

- The design does not prove that Polymarket is efficient in all markets or
  future elections.

### H1 Results: Forecast Quality

What was investigated:

- Whether Polymarket daily probabilities have lower forecast loss than
  comparable probability forecasts and deterministic baselines.

How the result was derived:

- Daily Polymarket and FiveThirtyEight probability rows were aligned over the
  overlapping 2024 window.
- Python computed Brier loss series, mean Brier Scores, Diebold-Mariano
  comparisons, and the reliability figure.
- RCP was excluded because no probability transformation is documented.

Evidence to cite:

- Table 2: H1 forecast-quality summary.
- Figure 1: H1 reliability curve.
- `data/results/thesis_h1_summary.csv`.
- `data/results/h1_brier_scores.csv`.
- `data/results/h1_diebold_mariano.json`.

Allowed interpretation:

- The current baseline supports a forecast-quality comparison over the tested
  overlap window.
- A lower Brier Score indicates lower squared forecast error in that window.

Required caution:

- H1 is not a reaction-speed test.
- The Polymarket and prior-day Polymarket Brier means are nearly identical in
  the current output, so H1 should not be used as evidence of faster
  information integration.

Further investigations:

- Document and test an RCP probability transformation before adding RCP to H1.
- Add sensitivity checks for alternative forecast horizons or market
  definitions if additional probability series become available.

### H2 Results: Daily Event-Window Response

What was investigated:

- Whether Polymarket probabilities moved in the expected direction around
  pre-curated public events.

How the result was derived:

- Seven source-backed events were fixed in `data/events_timeline_seed.csv`
  before the first H2 output run.
- Python generated daily event-window rows and compact CAR-style summaries for
  the selected `[0d, +1d]` primary window and `[-1d, +3d]` sensitivity window.
- Full row-level traces remain file-based, while compact H2 summaries are
  persisted in `analysis_summaries`.

Evidence to cite:

- Table 3: H2 daily event-window summary.
- Figure 2: H2 event-window movement overview.
- `data/results/thesis_h2_summary.csv`.
- `data/results/h2_event_window_summary.csv`.
- `data/results/h2_event_window_rows.csv`.

Allowed interpretation:

- H2 can describe daily market movement around pre-curated public events.
- Results may be discussed as daily event-window response patterns.

Required caution:

- Daily data cannot support intraday reaction-speed claims.
- Events must not be added or removed after inspecting price reactions unless
  the change is documented as a new sensitivity run.

Further investigations:

- Add intraday Polymarket price data before making intraday speed claims.
- Expand the event catalog only through pre-specified inclusion rules and
  source review.
- Compare event responses with validated polling or news-sentiment variables
  only after their transformations are documented.

### H3 Results: Wallet-Tier Timing Diagnostics

What was investigated:

- Whether dataset-relative wallet tiers show observable activity before or
  around Polymarket price changes.

How the result was derived:

- Wallet tiers were defined from wallet-level cumulative observed `amount_usd`
  percentiles, not fixed USD thresholds.
- Python generated wallet distribution inventory, tier classifications, daily
  tier activity, lead-time histograms, lead-lag correlations, and Granger
  diagnostic outputs.
- Wallet-address-level raw rows are not part of the thesis-facing narrative.

Evidence to cite:

- Table 4: H3 wallet-tier and timing summary.
- Figure 3: H3 wallet-tier distribution.
- Figure 4: H3 lead-time histogram.
- Figure 5: H3 Granger diagnostic overview.
- `data/results/thesis_h3_summary.csv`.
- `data/results/h3_wallet_distribution_inventory.json`.
- `data/results/h3_lead_time_histograms.csv`.
- `data/results/h3_lead_lag_correlations.csv`.
- `data/results/h3_granger_results.csv`.

Allowed interpretation:

- H3 can report descriptive timing patterns and predictive timing diagnostics
  under the tested daily model.
- Granger outputs may be discussed as lead-lag diagnostics, not as proof of true
  causality.

Required caution:

- The current wallet extract is BUY-only and daily-aligned.
- Granger results require multiple-testing and sensitivity discussion before
  any strong thesis wording.
- No result proves insider trading, misconduct, private information, or future
  profitability.

Further investigations:

- Add sell-side or directionally complete wallet activity if available.
- Run multiple-testing adjustments and robustness checks across lag choices.
- Test whether wallet-tier signals remain informative in out-of-sample or
  walk-forward strategy backtests.

### Strategy Prototype Boundary

What was investigated so far:

- The thesis has not yet backtested a trading strategy.
- The current strategy work is an architecture and research-design boundary:
  agents may later propose signal hypotheses, but Python must validate and
  backtest them.

Evidence to cite:

- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`.
- `ARCHITECTURE_DECISIONS.md`.

Allowed interpretation:

- H1-H3 outputs can motivate future bounded signal hypotheses.
- A later strategy prototype may test whether those hypotheses have historical
  predictive value under explicit cost, slippage, position-limit, and
  evaluation-split assumptions.

Required caution:

- No live trading, autonomous execution, profit guarantee, or agent-computed
  metric belongs in the thesis.

Further investigations:

- Define `SignalSpec`, `BacktestConfig`, and `BacktestResult` before writing
  strategy code.
- Start with one deterministic historical backtest baseline and compare it
  against simple benchmarks.

### Chapter Closing

The first empirical package should close with a balanced statement:

- H1 provides forecast-quality evidence.
- H2 provides daily event-window response evidence.
- H3 provides wallet-tier timing diagnostics.
- Together, these layers support a structured discussion of informational
  efficiency in the studied Polymarket case, but they do not prove universal
  market efficiency, insider activity, intraday speed, or strategy
  profitability.

## Hypotheses

H1: Brier Score calibration

Polymarket probability forecasts may be better calibrated than comparable
traditional probability forecasts. FiveThirtyEight can be compared when its rows
represent probabilities. RCP cannot be treated as a probability forecast unless
a transformation is documented and tested.

H2: Information integration speed

Polymarket may integrate public information faster than traditional forecast or
polling sources. This requires a curated event catalog and pre-specified event
windows before CAR or reaction-speed analysis.

H3: Wallet-based early signal detection

Large or influential wallets may show lead-lag patterns relative to market price
movements. Any classification must be derived from the observed wallet or trade
distribution. Granger tests can support predictive timing claims, not proof of
true causality.

## Non-Goals

- No agent implementation before deterministic H1, H2, and H3 outputs exist.
- No MCP demo layer before the deterministic core is complete.
- No ML scope yet.
- No causal insider-trading claims.
- No arbitrary whale thresholds.
- No RCP probability comparison without documented transformation.
- No raw table dumps into LLM prompts.

## Deterministic-Core Rule

All statistical calculations are implemented in Python. LLMs may only interpret
precomputed outputs and must not calculate Brier scores, CAR, Granger tests,
wallet classifications, whale scores, or statistical metrics.

## RCP Rule

RCP is treated as a polling signal until a probability transformation is
documented, tested, and explicitly enabled in deterministic code.

Any function that includes RCP in Brier or calibration comparisons must require:

- `include_rcp=True`
- `rcp_transformation_documented=True`

## ML Scope Rule

Machine learning is not in scope yet. Do not add ML models, feature stores,
training pipelines, embeddings, vector databases, or automated classifiers until
the deterministic empirical pipeline is complete and reviewed.

- ml_scope_status: deferred
- ml_reentry_condition: deterministic H1, H2, and H3 outputs exist, pass tests,
  and have written methodology notes.

## Agent And MCP Deferred Rule

Agents and MCP are interpretation and demo layers only. They remain deferred
until deterministic H1, H2, and H3 outputs exist, pass tests, and have written
methodology notes.

Signal-generating agents may be specified as a thesis research prototype only
after the deterministic summaries and bounded tool contracts exist. They may
suggest hypotheses for Python backtests; they must not calculate metrics or
execute trades.

## Empirical Baseline Review

Review date: 2026-05-19

Review status: accepted as the first deterministic empirical baseline package.

Reviewed outputs:

- H1 Brier time series: `data/results/h1_brier_scores.csv`
- H1 Diebold-Mariano summary: `data/results/h1_diebold_mariano.json`
- H1 reliability figure: `data/results/h1_reliability_curve.png`
- H2 event-window trace: `data/results/h2_event_window_rows.csv`
- H2 event-window summary: `data/results/h2_event_window_summary.csv`
- H3 wallet distribution inventory:
  `data/results/h3_wallet_distribution_inventory.json`
- H3 wallet tiers: `data/results/h3_wallet_tiers.csv`
- H3 tiered daily activity:
  `data/results/h3_tiered_wallet_activity_daily.csv`
- H3 lead-time histograms: `data/results/h3_lead_time_histograms.csv`
- H3 lead-lag correlations: `data/results/h3_lead_lag_correlations.csv`
- H3 Granger baseline: `data/results/h3_granger_results.csv`

Baseline shape:

- H1 contains 194 overlapping daily observations from 2024-03-01 to
  2024-09-12.
- H2 contains 7 curated events and 2 selected daily windows, for 14 compact
  summary rows.
- H3 contains 4 dataset-relative wallet tiers, 420 lead-time event-tier-day
  rows, 60 lead-time histogram rows, 32 lead-lag correlation rows, and 28
  Granger result rows.

Thesis-ready for the first baseline:

- H1 Brier comparison between Polymarket, FiveThirtyEight, and deterministic
  baselines.
- H2 daily event-window summary table using the curated event seed.
- H3 wallet-tier definition, tier counts, daily activity panel, descriptive
  timing histograms, lead-lag correlations, and Granger baseline result shape.

Needs caution before final thesis conclusions:

- H1 Polymarket and prior-day Polymarket Brier means are nearly identical in
  the current output, so H1 should not be framed as a reaction-speed result.
- RCP remains excluded from probability comparisons until a documented
  transformation exists.
- H2 uses daily windows only and cannot support intraday reaction-speed claims.
- H3 uses a BUY-only observed activity extract and daily alignment.
- H3 Granger results require multiple-testing and sensitivity discussion before
  strong conclusion wording.

Persistence decision:

- H2 compact summaries are already persisted into `analysis_summaries`.
- Full H2 and H3 row-level traces remain file-based.
- Compact H3 summaries should not be persisted until the exact summary payload
  is specified and tested.

Approved thesis wording:

- Use `deterministic baseline`, `daily event-window result`, `dataset-relative
  wallet tier`, `descriptive timing pattern`, and `predictive timing
  diagnostic`.
- Do not write that Granger tests prove true causality, misconduct, or private
  information.
