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
