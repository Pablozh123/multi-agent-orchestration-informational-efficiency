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

- The next strategy-track extension is a politics/geopolitics anomaly monitor,
  not an immediate trading system.
- The monitor observes unusual combinations of market movement, wallet-tier
  activity, concentration, and sourced event context.
- The near-real-time v2 monitor is first specified as a read-only contract:
  watchlist inputs, market snapshots, wallet-tier snapshots, event-candidate
  review, robust rolling scores, alert levels, persistence, and bounded
  outputs.
- A backtested strategy prototype may be included later as historical
  validation after anomaly definitions are fixed.
- Agents may propose signal hypotheses later, but Python must validate,
  backtest, and calculate all results.
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

- Can H1-H3 outputs motivate a politics/geopolitics anomaly monitor and later
  bounded signal hypotheses that are tested in historical Python backtests?

Scope:

- Strategy work is a research extension after H1-H3, not the core proof of
  informational efficiency.
- The immediate prototype direction is an anomaly monitor for Polymarket
  politics/geopolitical markets.
- The monitor treats events such as arrests, conflicts, sanctions, court
  decisions, debates, or election shocks as candidates only after source and
  market mapping review.
- Existing US-election events remain the first historical validation bed.
- The v2 monitor contract is Polymarket-first: Gamma-style discovery for
  watchlists, public CLOB or Market WebSocket data for market snapshots, Data
  API or validated local ingestion for wallet/activity aggregates, and
  human-reviewed news/event candidates.
- The default alert design uses robust rolling baselines and empirical
  percentile ranks. It is descriptive and must not be written as alpha,
  insider evidence, a profit claim, or a causal proof.
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

Figure 1: H1 forecast-quality comparison

- Source artifact: `data/results/h1_forecast_quality.png`
- Supporting artifact: `data/results/h1_brier_scores.csv`
- Supporting artifact: `data/results/h1_forecast_quality_pairwise.csv`
- Thesis role: visualise Brier Score, head-to-head lower-loss counts, cumulative
  loss advantage, and forecast probabilities for H1.
- Status: ready.

Figure 2: H1 forecast-quality synthesis

- Source artifact: `data/results/h1_forecast_quality_synthesis.png`
- Supporting artifact: `data/results/h1_forecast_quality_synthesis.csv`
- Supporting artifact:
  `data/results/h1_forecast_quality_synthesis_metadata.json`
- Thesis role: synthesize all current H1 traditional-comparator evidence and
  separate aggregate mean Brier support from a broad many-cases proof.
- Status: ready; six of eight current H1 comparison rows support Polymarket on
  aggregate mean Brier, three support Polymarket by majority of individual
  cases, and zero prove the broad many-cases claim. The state-date poll panel
  and popular-vote extension are the current counterexample rows.

Figure 2b: H1 calibration diagnostic

- Source artifact: `data/results/h1_calibration_diagnostic.png`
- Supporting artifact: `data/results/h1_calibration_diagnostic_cases.csv`
- Supporting artifact: `data/results/h1_calibration_diagnostic_bins.csv`
- Supporting artifact: `data/results/h1_calibration_diagnostic_summary.csv`
- Supporting artifact: `data/results/h1_calibration_diagnostic_pairwise.csv`
- Supporting artifact:
  `data/results/h1_calibration_diagnostic_metadata.json`
- Thesis role: replace the weak one-outcome reliability curve with a
  scorecard-plus-sparse-bin diagnostic over resolved H1 case artifacts.
- Status: ready as a diagnostic; 192 forecast-case rows across 7 forecast
  sources produce 5 pairwise rows. All 5 pairwise rows support Polymarket on
  aggregate mean Brier, 2 support Polymarket by majority of individual cases,
  and 0 prove the broad many-cases claim. The figure does not connect sparse
  calibration bins; it shows reliability points only for sources with at least
  30 cases and keeps smaller case sets in the scorecard panels.

Figure 2c: H1 claim-evidence audit

- Source artifact: `data/results/h1_claim_evidence_audit.png`
- Supporting artifact: `data/results/h1_claim_evidence_audit.csv`
- Supporting artifact: `data/results/h1_claim_evidence_audit_summary.csv`
- Supporting artifact:
  `data/results/h1_claim_evidence_audit_metadata.json`
- Thesis role: combine the current H1 comparator evidence into one claim
  ledger that shows where Polymarket is supported, where the strong claim is
  contradicted, and whether the requested broad many-cases claim is proven.
- Status: ready; 16 of 22 audit rows support a bounded Polymarket advantage,
  5 rows contradict the strong claim, and the broad user claim remains
  `not_proven`. Among directly poll-related rows, 12 of 15 support Polymarket
  in bounded scopes. The full state-date poll panel, popular-vote extension,
  all-source state consensus, high-distance state-source subset, and late
  high-distance state-date subset remain counterexamples to the strong claim.

Figure 2d: H1 poll-comparison result

- Source artifact: `data/results/h1_poll_comparison_result.png`
- Supporting artifact: `data/results/h1_poll_comparison_result.csv`
- Supporting artifact: `data/results/h1_poll_comparison_result_summary.csv`
- Supporting artifact:
  `data/results/h1_poll_comparison_result_metadata.json`
- Thesis role: isolate the directly poll-related H1 result from the broader
  claim ledger and state exactly which poll-comparison statement is supported.
- Status: ready as a bounded thesis-facing result. In the primary
  `<=90_days_low_middle_poll_distance` scope, Polymarket has lower Brier loss
  in 262 of 285 state-date rows, while poll-derived probabilities have lower
  loss in 23 rows. Treating states as the diagnostic unit, Polymarket has
  majority lower-loss support in 9 of 9 states, with exact one-sided
  binomial `p = 0.001953125` and exact 95 percent lower confidence bound
  0.7169. The full state-date poll panel remains a counterexample:
  poll-derived probabilities have lower loss in 1360 of 1720 rows, and the
  late high-distance subset remains poll-derived 72 of 72. The broad H1
  objective remains `not_proven`.

Figure 2d-1: H1 poll-claim readiness

- Source artifact: `data/results/h1_poll_claim_readiness.png`
- Supporting artifact: `data/results/h1_poll_claim_readiness.csv`
- Supporting artifact:
  `data/results/h1_poll_claim_readiness_summary.csv`
- Supporting artifact:
  `data/results/h1_poll_claim_readiness_metadata.json`
- Thesis role: turn the poll-comparison evidence into explicit claim language:
  which bounded Polymarket statement is supported, which evidence is only
  mean-loss support without case/state majority, and which scopes remain
  counterexamples.
- Status: ready as a claim-readiness diagnostic. The bounded
  `<=90_days_low_middle_poll_distance` claim is supported: Polymarket has
  lower Brier loss in 262 of 285 state-date rows, 9 of 9 states, 17 of 17
  state-month units, and 17 of 17 state-horizon units. The state-month exact
  one-sided p-value is 0.0000076294 and the exact 95 percent lower confidence
  bound is 0.8384. The figure keeps the boundary visible: 5 counterexample
  scopes remain, including the full state-date panel, full state-month units,
  late high-distance rows and states, and the popular-vote daily rows. The
  correct thesis wording is therefore bounded: Polymarket is better in the
  late low/middle poll-distance scope, while the broad many-cases or
  many-elections claim remains `not_proven`.

Figure 2d-2: H1 poll-scope frontier

- Source artifact: `data/results/h1_poll_scope_frontier.png`
- Supporting artifact: `data/results/h1_poll_scope_frontier.csv`
- Supporting artifact:
  `data/results/h1_poll_scope_frontier_summary.csv`
- Supporting artifact:
  `data/results/h1_poll_scope_frontier_metadata.json`
- Thesis role: scan transparent forecast-horizon cutoffs and existing
  quantile-derived poll-distance tiers to show how far the
  Polymarket-supporting poll-comparison scope can be widened before
  counterexamples dominate.
- Status: ready as a scope-frontier diagnostic. The table contains 30
  horizon-by-poll-distance scopes and 8 meet the robust-support rule: row
  majority for Polymarket, positive mean loss advantage, and state-month exact
  one-sided p-value below 0.05. The largest robust scope is `<=120 days` plus
  low/middle poll distance: Polymarket has lower Brier loss in 313 of 433
  state-date rows across 11 states, with 18 of 26 state-month units supporting
  Polymarket and exact p-value 0.037759. The strongest bounded scope remains
  `<=90 days` plus low/middle poll distance with 262 of 285 rows and 17 of 17
  state-month units, exact p-value 0.0000076294. The boundary remains visible:
  `<=90 days` across all poll-distance tiers has row support, 262 of 357 rows,
  but state-month p-value 0.0758; the full panel still supports poll-derived
  probabilities in 1360 of 1720 rows. The broad H1 claim therefore remains
  `not_proven`.

Figure 2d-3: H1 poll-decision matrix

- Source artifact: `data/results/h1_poll_decision_matrix.png`
- Supporting artifact: `data/results/h1_poll_decision_matrix.csv`
- Supporting artifact:
  `data/results/h1_poll_decision_matrix_summary.csv`
- Supporting artifact:
  `data/results/h1_poll_decision_matrix_metadata.json`
- Thesis role: convert the H1 poll evidence into a single decision matrix that
  separates robust bounded yes rows, directional-but-not-robust rows,
  mean-loss support without case or unit majority, calibration context, and
  broad-claim counterexamples.
- Status: ready as the current H1 poll claim boundary. The decision table has 9
  rows. Two rows are robust bounded yes rows: the largest robust scope has
  Polymarket lower loss in 313 of 433 state-date rows and 18 of 26 state-month
  units, p-value 0.037759; the strongest robust scope has 262 of 285 rows and
  p-value 0.0000076294. Three rows are mean-loss support without majority, and
  two rows are counterexamples. The calibration context supports lower mean
  Polymarket Brier in 5 of 5 pairwise resolved-case rows, but only 2 of 5 also
  support Polymarket by case majority. The correct thesis statement is
  bounded: Polymarket is better in the robust late low/middle poll-distance
  scopes, while the broad many-cases or many-elections claim remains
  `not_proven`.

Figure 2d-4: H1 robust poll-scope quality

- Source artifact: `data/results/h1_robust_poll_scope_quality.png`
- Supporting artifact:
  `data/results/h1_robust_poll_scope_quality_rows.csv`
- Supporting artifact:
  `data/results/h1_robust_poll_scope_quality_bins.csv`
- Supporting artifact:
  `data/results/h1_robust_poll_scope_quality_summary.csv`
- Supporting artifact:
  `data/results/h1_robust_poll_scope_quality_pairwise.csv`
- Supporting artifact:
  `data/results/h1_robust_poll_scope_quality_metadata.json`
- Thesis role: show whether the robust bounded poll scopes also have better
  forecast-quality scores, not only more lower-loss rows.
- Status: ready as a bounded score-quality diagnostic. Across the two robust
  scopes there are 718 state-date cases and 1436 source forecast rows. In the
  largest robust scope (`<=120 days` plus low/middle poll distance),
  Polymarket has lower loss in 313 of 433 rows, lower mean Brier
  (0.198247 vs 0.255460), lower fixed-bin ECE (0.386824 vs 0.425098), and
  higher probability separation (0.218239 vs 0.139383). In the strongest
  robust scope (`<=90 days` plus low/middle poll distance), Polymarket has
  lower loss in 262 of 285 rows, lower mean Brier (0.221443 vs 0.314714), and
  lower fixed-bin ECE (0.452316 vs 0.536192). Probability separation is not
  defined in the strongest scope because all observed outcomes in that bounded
  subset are positive. The correct thesis statement remains bounded:
  Polymarket is better on these robust late low/middle poll-distance scopes,
  while the broad H1 claim remains `not_proven`.

Figure 2d-5: H1 robust poll-scope unit quality

- Source artifact: `data/results/h1_robust_poll_scope_unit_quality.png`
- Supporting artifact:
  `data/results/h1_robust_poll_scope_unit_quality_units.csv`
- Supporting artifact:
  `data/results/h1_robust_poll_scope_unit_quality_summary.csv`
- Supporting artifact:
  `data/results/h1_robust_poll_scope_unit_quality_metadata.json`
- Thesis role: test whether the robust late low/middle poll-distance scopes
  remain Polymarket-supportive after aggregating repeated state-date rows into
  less repeated state, state-month, state-horizon, and horizon-tier units.
- Status: ready as a bounded unit-quality diagnostic. The figure summarises
  116 unit rows and 8 scope-by-unit summary rows across the two robust scopes.
  In the largest robust scope (`<=120 days` plus low/middle poll distance),
  Polymarket is supported in 10 of 11 states, 18 of 26 state-month units, and
  20 of 26 state-horizon units. The state-month exact one-sided binomial
  p-value is 0.037759 and the median state-month Brier advantage is 0.048385.
  In the strongest robust scope (`<=90 days` plus low/middle poll distance),
  Polymarket is supported in 9 of 9 states, 17 of 17 state-month units, and
  17 of 17 state-horizon units. The state-month exact one-sided binomial
  p-value is 0.0000076294 and the median state-month Brier advantage is
  0.072312. This reduces dependence on repeated state-date rows, but it still
  refers to bounded 2024 US-state poll scopes rather than many independent
  elections; therefore the broad H1 claim remains `not_proven`.

Figure 2e: H1 poll-comparison unit robustness

- Source artifact: `data/results/h1_poll_comparison_unit_robustness.png`
- Supporting artifact:
  `data/results/h1_poll_comparison_unit_robustness_units.csv`
- Supporting artifact:
  `data/results/h1_poll_comparison_unit_robustness_summary.csv`
- Supporting artifact:
  `data/results/h1_poll_comparison_unit_robustness_metadata.json`
- Thesis role: reduce dependence on repeated state-date rows by aggregating
  the primary H1 poll-comparison scope into state, state-month, state-horizon,
  and horizon-tier units.
- Status: ready as a robustness diagnostic. The primary
  `<=90_days_low_middle_poll_distance` result holds across all reported
  aggregation units: Polymarket is supported in 9 of 9 states, 17 of 17
  state-month units, 17 of 17 state-horizon units, and 4 of 4 horizon-tier
  units. For the state-month units, the exact one-sided binomial p-value is
  0.0000076294 and the exact 95 percent lower confidence bound is 0.8384.
  The artifact also keeps boundaries explicit: in the full panel,
  poll-derived probabilities are supported in 61 of 80 state-month units; in
  the late high-distance subset, poll-derived probabilities are supported in
  8 of 8 state-month units with exact one-sided p-value 0.00390625. These
  units are diagnostics, not independent elections, so the broad H1 objective
  remains `not_proven`.

Figure 2f: H1 direct poll loss decomposition

- Source artifact: `data/results/h1_direct_poll_loss_decomposition.png`
- Supporting artifact:
  `data/results/h1_direct_poll_loss_decomposition_cases.csv`
- Supporting artifact:
  `data/results/h1_direct_poll_loss_decomposition_summary.csv`
- Supporting artifact:
  `data/results/h1_direct_poll_loss_decomposition_metadata.json`
- Thesis role: explain why direct poll-transform comparisons can support
  Polymarket on aggregate mean Brier even when Polymarket does not win the
  majority of direct source-state cases.
- Status: ready as a loss-decomposition diagnostic. Across 56 direct
  poll-transform source-state cases, Polymarket has lower mean Brier
  0.0544 versus 0.0729 for poll-derived comparators. The case-count majority
  goes the other way: Polymarket has lower loss in 22 of 56 cases, while
  poll-derived comparators have lower loss in 34. The aggregate result is
  explained by effect size: Polymarket-winning cases have mean Brier
  advantage 0.0498, while poll-derived winning cases have mean absolute
  advantage 0.0018; the total positive Polymarket margin is about 18.2 times
  the total poll-derived winning margin. This supports a bounded aggregate
  forecast-quality statement, not a direct case-majority or broad
  many-elections claim.

Figure 2g: H1 direct poll state-cluster diagnostic

- Source artifact: `data/results/h1_direct_poll_state_cluster_diagnostic.png`
- Supporting artifact:
  `data/results/h1_direct_poll_state_cluster_diagnostic_states.csv`
- Supporting artifact:
  `data/results/h1_direct_poll_state_cluster_diagnostic_summary.csv`
- Supporting artifact:
  `data/results/h1_direct_poll_state_cluster_diagnostic_metadata.json`
- Thesis role: test whether the direct poll-transform aggregate loss advantage
  remains visible when states are treated as equal-weight diagnostic clusters.
- Status: ready as a state-cluster uncertainty diagnostic. Across 43 states
  with at least one direct poll-transform source, the equal-state mean loss
  advantage remains positive for Polymarket at 0.0122 Brier points. A
  deterministic state-cluster bootstrap gives a 95 percent interval from
  0.0041 to 0.0217, and the deterministic sign-flip p-value for a positive
  equal-state mean is 0.00455. The state-count majority remains a boundary:
  Polymarket has lower mean Brier in 13 of 43 states, while poll-derived
  comparators have lower mean Brier in 30 of 43 states; the exact one-sided
  binomial p-value for poll-derived state-count support is 0.00686. This
  supports the bounded mean-loss statement, not a state-majority or broad
  many-elections claim.

Figure 2h: H1 direct poll outlier robustness

- Source artifact: `data/results/h1_direct_poll_outlier_robustness.png`
- Supporting artifact:
  `data/results/h1_direct_poll_outlier_robustness_scenarios.csv`
- Supporting artifact:
  `data/results/h1_direct_poll_outlier_robustness_summary.csv`
- Supporting artifact:
  `data/results/h1_direct_poll_outlier_robustness_metadata.json`
- Thesis role: test whether the direct poll state-cluster mean advantage is
  only driven by one exceptional state, and show how concentrated the advantage
  is in the largest positive state contributions.
- Status: ready as an outlier robustness diagnostic. Across the 43 direct
  poll state clusters, the full equal-state mean loss advantage is 0.0122
  Brier points. Every leave-one-state-out scenario remains positive; the
  smallest remaining mean is 0.0095 after removing Wisconsin. This means the
  direct poll mean advantage is not created by a single state. The concentration
  boundary is still visible: when the largest positive state contributions are
  removed in order, the remaining mean stays positive through six removed
  states and first turns non-positive after seven removed states, at -0.0001.
  This supports the bounded mean-loss robustness statement, but it also shows
  concentration in the strongest positive states and therefore does not prove a
  state-majority or broad many-elections claim.

Figure 3: H1 evidence-scope audit

- Source artifact: `data/results/h1_evidence_scope.png`
- Supporting artifact: `data/results/h1_evidence_scope.csv`
- Thesis role: separate paired daily forecast rows from independent resolved
  H1 outcomes before any many-cases claim is made.
- Status: ready; current broad many-cases claim is not yet supported.

Figure 4: H1 expansion-readiness audit

- Source artifact: `data/results/h1_expansion_readiness.png`
- Supporting artifact: `data/results/h1_expansion_readiness.csv`
- Thesis role: show whether existing local data can extend H1 beyond the
  current paired forecast window without using untransformed poll shares.
- Status: ready; the audit finds 55 extra Polymarket daily rows, 0 compatible
  FiveThirtyEight probability rows after the current H1 end date, and 0 new
  H1 Brier pairs.

Figure 4a: H1 margin-threshold readiness audit

- Source artifact: `data/results/h1_margin_threshold_readiness.png`
- Supporting artifact: `data/results/h1_margin_threshold_readiness.csv`
- Supporting artifact: `data/results/h1_margin_threshold_readiness_metadata.json`
- Thesis role: document why reviewed Trump state-margin threshold markets are
  not added to H1 Brier scoring without a later compatible traditional
  polling-average source.
- Status: ready as an exclusion audit; seven Polymarket threshold markets were
  reviewed, four have compatible 538 state-poll rows, zero have CLOB history
  inside the preserved official 538 polling-average window, and zero add new
  H1 Brier rows.

Figure 5: H1 final-snapshot extension

- Source artifact: `data/results/h1_final_snapshot.png`
- Supporting artifact: `data/results/h1_final_snapshot_cases.csv`
- Supporting artifact: `data/results/h1_final_snapshot_summary.csv`
- Thesis role: compare eight resolved 2024 final-snapshot outcomes against
  the FiveThirtyEight final probability forecast without using raw polls.
- Status: ready as a small curated extension; Polymarket has lower loss in
  5 of 8 cases, but this is not a broad many-markets proof.

Figure 6: H1 state-poll-snapshot extension

- Source artifact: `data/results/h1_state_poll_snapshot.png`
- Supporting artifact: `data/results/h1_state_poll_snapshot_cases.csv`
- Supporting artifact: `data/results/h1_state_poll_snapshot_summary.csv`
- Thesis role: compare 13 resolved state-level Republican-win outcomes
  against a documented probability transformation of FiveThirtyEight
  polling-average margins.
- Status: ready as a poll-derived extension; Polymarket has lower loss in
  8 of 13 cases and mean Brier 0.1336 versus 0.1764 for the transformed
  poll-derived probabilities. This is not raw-poll Brier scoring and not an
  official FiveThirtyEight state win forecast.

Figure 6a: H1 popular-vote extension

- Source artifact: `data/results/h1_popular_vote.png`
- Supporting artifact: `data/results/h1_popular_vote_cases.csv`
- Supporting artifact: `data/results/h1_popular_vote_summary.csv`
- Supporting artifact: `data/results/h1_popular_vote_metadata.json`
- Thesis role: compare the Polymarket Trump popular-vote market against a
  documented probability transformation of national FiveThirtyEight
  Trump-minus-Harris polling-average margins.
- Status: ready as a counterexample extension; 51 national daily rows show
  Polymarket lower loss in 21 rows and the transformed poll-derived
  probability lower loss in 30 rows. Mean Brier is 0.5179 for Polymarket
  versus 0.4824 for the transformed poll-derived probabilities. This is one
  resolved popular-vote outcome with repeated daily rows, not an independent
  many-elections sample.

Figure 6b: H1 state-date poll panel

- Source artifact: `data/results/h1_state_poll_panel.png`
- Supporting artifact: `data/results/h1_state_poll_panel_cases.csv`
- Supporting artifact: `data/results/h1_state_poll_panel_summary.csv`
- Supporting artifact: `data/results/h1_state_poll_panel_state_summary.csv`
- Supporting artifact: `data/results/h1_state_poll_panel_coverage.csv`
- Supporting artifact: `data/results/h1_state_poll_panel_metadata.json`
- Thesis role: test the poll-derived comparison on the broader daily state
  polling-average panel inside the preserved FiveThirtyEight file.
- Status: ready as a larger repeated-row panel; 1,720 matched state-date rows
  across 15 states and 186 dates show Polymarket lower loss in 360 rows and
  the poll-derived transformation lower loss in 1,360 rows. Mean Brier is
  0.1595 for Polymarket versus 0.1026 for the transformed poll-derived
  probabilities. This does not support the strong Polymarket-better claim.

Figure 6c: H1 state-date poll panel temporal diagnostic

- Source artifact: `data/results/h1_state_poll_panel_temporal_diagnostic.png`
- Supporting artifact:
  `data/results/h1_state_poll_panel_temporal_summary.csv`
- Supporting artifact:
  `data/results/h1_state_poll_panel_temporal_state_month.csv`
- Supporting artifact:
  `data/results/h1_state_poll_panel_temporal_claim_audit.csv`
- Supporting artifact:
  `data/results/h1_state_poll_panel_temporal_diagnostic_metadata.json`
- Thesis role: show whether the large state-date panel's aggregate result is
  stable across time or concentrated in specific months of the preserved
  FiveThirtyEight polling-average window.
- Status: ready as a temporal diagnostic, not a new independent evidence row.
  The full panel remains negative for Polymarket, but the months 2024-08 and
  2024-09 support Polymarket: 280 of 387 matched rows have lower Polymarket
  loss, poll-derived forecasts are lower in 107 rows, and mean Brier is
  0.1842 for Polymarket versus 0.2543 for the transformed poll-derived
  probabilities. This late-window result is conditioned on the observed
  monthly split and does not prove the broad many-independent-cases claim.

Figure 6d: H1 state-date poll panel forecast-horizon diagnostic

- Source artifact: `data/results/h1_state_poll_panel_horizon_diagnostic.png`
- Supporting artifact:
  `data/results/h1_state_poll_panel_horizon_summary.csv`
- Supporting artifact:
  `data/results/h1_state_poll_panel_horizon_state_summary.csv`
- Supporting artifact:
  `data/results/h1_state_poll_panel_horizon_claim_audit.csv`
- Supporting artifact:
  `data/results/h1_state_poll_panel_horizon_diagnostic_metadata.json`
- Thesis role: test whether the panel result changes by forecast horizon,
  measured as days before the 2024-11-05 election.
- Status: ready as a forecast-horizon diagnostic. The full panel remains
  negative for Polymarket, but the <=90-day window supports Polymarket:
  262 of 357 matched rows have lower Polymarket loss, poll-derived forecasts
  are lower in 95 rows, and mean Brier is 0.1799 for Polymarket versus 0.2520
  for the transformed poll-derived probabilities. This is still repeated
  forecast-row evidence from one election context.

Figure 6e: H1 <=90-day state-level support

- Source artifact: `data/results/h1_state_poll_panel_horizon_state_support.png`
- Supporting artifact:
  `data/results/h1_state_poll_panel_horizon_state_support.csv`
- Supporting artifact:
  `data/results/h1_state_poll_panel_horizon_state_support_summary.csv`
- Supporting artifact:
  `data/results/h1_state_poll_panel_horizon_state_support_metadata.json`
- Thesis role: aggregate the <=90-day forecast-horizon result to the state
  level so the late-window support is not only a repeated-row count.
- Status: ready as a state-level diagnostic. Within the <=90-day window,
  Polymarket has lower mean Brier in 8 of 13 states and also a majority of
  lower-loss rows in 8 of 13 states. Across the same window, Polymarket has
  lower loss in 262 of 357 state-date rows and mean Brier 0.1799 versus
  0.2520 for the poll-derived transformation. The 13 states still belong to
  one election context.

Figure 6f: H1 <=90-day score-quality diagnostic

- Source artifact: `data/results/h1_state_poll_panel_near_window_quality.png`
- Supporting artifact:
  `data/results/h1_state_poll_panel_near_window_quality_rows.csv`
- Supporting artifact:
  `data/results/h1_state_poll_panel_near_window_quality_bins.csv`
- Supporting artifact:
  `data/results/h1_state_poll_panel_near_window_quality_summary.csv`
- Supporting artifact:
  `data/results/h1_state_poll_panel_near_window_quality_metadata.json`
- Thesis role: visualize the same <=90-day window as forecast-quality and
  calibration evidence, using fixed calibration bins, mean Brier, ECE,
  probability separation, and lower-loss row counts.
- Status: ready as a score-quality diagnostic. The long-form output contains
  714 forecast rows from 357 state-date cases and two sources. Polymarket has
  lower mean Brier (0.1799 vs 0.2520), lower fixed-bin ECE (0.3797 vs 0.4391),
  and slightly higher probability separation (0.4560 vs 0.4366). This supports
  Polymarket forecast quality in the late window but remains repeated
  state-date evidence from one election context.

Figure 6g: H1 state-date competitiveness x horizon diagnostic

- Source artifact: `data/results/h1_state_poll_panel_competitiveness.png`
- Supporting artifact:
  `data/results/h1_state_poll_panel_competitiveness_grid.csv`
- Supporting artifact:
  `data/results/h1_state_poll_panel_competitiveness_state.csv`
- Supporting artifact:
  `data/results/h1_state_poll_panel_competitiveness_summary.csv`
- Supporting artifact:
  `data/results/h1_state_poll_panel_competitiveness_metadata.json`
- Thesis role: show how the state-date poll panel result changes jointly by
  forecast horizon and the poll-derived probability distance to 0.5, using
  quantile-derived distance terciles.
- Status: ready as a diagnostic. In the <=90-day low/middle-distance subset,
  Polymarket has lower loss in 262 of 285 state-date rows and all 9 covered
  states have a Polymarket lower-loss majority. In the <=90-day high-distance
  subset, Polymarket has lower loss in 0 of 72 rows while poll-derived
  probabilities are lower-loss in all 72. This is a strong late competitive
  poll-transform result, but the rows repeat resolved states inside one
  election context and do not prove a broad many-independent-elections claim.

Figure 6h: H1 state-level significance diagnostic

- Source artifact: `data/results/h1_state_poll_panel_state_significance.png`
- Supporting artifact:
  `data/results/h1_state_poll_panel_state_significance.csv`
- Supporting artifact:
  `data/results/h1_state_poll_panel_state_significance_summary.csv`
- Supporting artifact:
  `data/results/h1_state_poll_panel_state_significance_metadata.json`
- Thesis role: check whether the late low/middle-distance state-date result
  also holds when each state is treated as one diagnostic unit.
- Status: ready as a bounded state-level sign test. In the <=90-day
  low/middle-distance scope, Polymarket has a lower-loss majority in 9 of 9
  covered states. The exact one-sided binomial p-value is 0.001953125 and the
  exact 95 percent lower confidence bound for the Polymarket state-support
  share is 0.7169. In the <=90-day high-distance scope, poll-derived
  probabilities have a lower-loss majority in 5 of 5 states. This supports a
  bounded state-level late competitive-poll statement, not a broad
  many-independent-elections proof.

Figure 7: H1 poll-transform sensitivity

- Source artifact: `data/results/h1_state_poll_snapshot_sensitivity.png`
- Supporting artifact:
  `data/results/h1_state_poll_snapshot_sensitivity.csv`
- Thesis role: show whether the state-poll extension depends on the single
  3.8 percentage-point poll-error assumption used in the probability
  transformation.
- Status: ready as a robustness check; across MAE assumptions from 2.0 to
  10.0 percentage points, Polymarket keeps a lower mean Brier in all 12
  parameter rows, with a lower-loss count range of 7 to 12 out of 13 state
  outcomes. This varies only the transform error assumption and does not add
  new independent events.

Figure 8: H1 state-poll coverage audit

- Source artifact: `data/results/h1_state_poll_snapshot_coverage.png`
- Supporting artifact: `data/results/h1_state_poll_snapshot_coverage.csv`
- Thesis role: explain why broader public Polymarket state-market coverage
  does not automatically become broader H1 Brier evidence without compatible
  poll-derived probability inputs.
- Status: ready as a compatibility audit; across 50 US states, 50 have a
  curated Polymarket Republican-wins state market slug, but only 13 have
  REP/DEM rows in the preserved 2024-09-12 FiveThirtyEight polling-average
  snapshot. The audit is not additional Brier evidence.

Figure 9: H1 Rieke 50-state forecast extension

- Source artifact: `data/results/h1_rieke_state_forecast.png`
- Supporting artifact: `data/results/h1_rieke_state_forecast_cases.csv`
- Supporting artifact: `data/results/h1_rieke_state_forecast_summary.csv`
- Supporting artifact: `data/results/h1_rieke_state_forecast_metadata.json`
- Thesis role: compare all 50 resolved 2024 presidential state outcomes
  against an independent poll-based Rieke forecast model, using the complement
  of Harris win probability as Republican-win probability.
- Status: ready as a broad state-level forecast-quality extension; Polymarket
  has lower mean Brier loss, 0.0262 versus 0.0296 for Rieke, but lower
  individual loss in only 12 of 50 states while Rieke is lower in 38 of 50.
  This supports only an aggregate Brier statement, not a claim that Polymarket
  is better in most state cases.

Figure 10a: H1 270toWin polling-average extension

- Source artifact: `data/results/h1_270towin_poll_average.png`
- Supporting artifact: `data/results/h1_270towin_poll_average_cases.csv`
- Supporting artifact: `data/results/h1_270towin_poll_average_summary.csv`
- Supporting artifact: `data/results/h1_270towin_poll_average_metadata.json`
- Thesis role: compare Polymarket Republican-win state probabilities with
  270toWin final 2024 state polling averages, after transforming Republican
  minus Democratic polling margins into Republican-win probabilities with the
  documented normal-error poll model used elsewhere in H1.
- Status: ready as a direct poll-derived state extension; 43 states match both
  a 270toWin polling-average row and a local Polymarket state snapshot.
  Polymarket has lower mean Brier loss, 0.0304 versus 0.0416 for the
  transformed 270toWin polling average, but lower individual loss in only 14
  of 43 states while the poll-derived probability is lower in 29 of 43. This
  supports only an aggregate Brier statement and remains limited by the
  probability transformation plus one-election state-outcome dependence.

Figure 10: H1 270toWin/JHK 50-state forecast extension

- Source artifact: `data/results/h1_270towin_state_forecast.png`
- Supporting artifact: `data/results/h1_270towin_state_forecast_cases.csv`
- Supporting artifact: `data/results/h1_270towin_state_forecast_summary.csv`
- Supporting artifact: `data/results/h1_270towin_state_forecast_metadata.json`
- Thesis role: compare all 50 resolved 2024 presidential state outcomes
  against the 270toWin Battleground 270/JHK forecast probabilities, while
  separating 22 exact source probabilities from 28 censored `>99.9%`
  boundary values.
- Status: ready as a second broad state-level forecast-quality extension;
  Polymarket has lower mean Brier loss, 0.0262 versus 0.0306 for 270toWin/JHK,
  but lower individual loss in only 9 of 50 states while 270toWin/JHK is lower
  in 40 of 50 and one state ties. This supports only an aggregate Brier
  statement and is limited by source censoring plus the missing exact
  publication timestamp.

Figure 10b: H1 state-source consensus diagnostic

- Source artifact: `data/results/h1_state_source_consensus.png`
- Supporting artifact: `data/results/h1_state_source_consensus_cases.csv`
- Supporting artifact:
  `data/results/h1_state_source_consensus_state_summary.csv`
- Supporting artifact: `data/results/h1_state_source_consensus_summary.csv`
- Supporting artifact:
  `data/results/h1_state_source_consensus_metadata.json`
- Thesis role: aggregate existing H1 state-level artifacts across source-state
  comparisons and show whether the Polymarket advantage is stable across
  direct poll transforms and poll-model sources.
- Status: ready as a diagnostic, not as a new independent evidence source.
  It contains 156 source-state comparisons across 50 states. Polymarket has
  lower loss in 43 source-state rows, while traditional comparators have lower
  loss in 112 and one row ties. In the all-source state consensus, Polymarket
  is ahead in 9 states, comparators in 37 states, and 4 states tie. Among the
  13 states covered by both direct poll-transform sources, Polymarket is ahead
  in 8, comparators in 4, and one ties. This supports a bounded direct-poll
  statement but contradicts a broad all-source state-majority claim.

Figure 10c: H1 competitive-state diagnostic

- Source artifact: `data/results/h1_competitive_state_diagnostic.png`
- Supporting artifact: `data/results/h1_competitive_state_diagnostic_cases.csv`
- Supporting artifact: `data/results/h1_competitive_state_diagnostic_tiers.csv`
- Supporting artifact:
  `data/results/h1_competitive_state_diagnostic_summary.csv`
- Supporting artifact:
  `data/results/h1_competitive_state_diagnostic_metadata.json`
- Thesis role: separate source-state cases by the comparator probability's
  observed distance to 0.5, using quantile-derived tiers rather than arbitrary
  competitiveness thresholds.
- Status: ready as a diagnostic, not as independent proof. In the lowest
  distance tercile, Polymarket has lower loss in 35 of 52 all-source cases and
  18 of 19 direct poll-transform cases. In the highest distance tercile,
  Polymarket has lower loss in 0 of 40 all-source cases while comparators have
  lower loss in all 40. This supports a bounded competitive-state exception
  and preserves the broader not-proven status.

Figure 11: H2 event-window movement overview

- Figure artifact: `data/results/thesis_h2_event_window_car.png`
- Source artifact: `data/results/h2_event_window_summary.csv`
- Supporting artifact: `data/results/h2_event_window_rows.csv`
- Thesis role: visualise final CAR-style daily event-window movements.
- Status: ready.

Figure 12: H3 wallet-tier distribution

- Figure artifact: `data/results/thesis_h3_wallet_tier_counts.png`
- Source artifact: `data/results/h3_wallet_distribution_inventory.json`
- Supporting artifact: `data/results/h3_wallet_tiers.csv`
- Thesis role: visualise dataset-relative wallet tier cutoffs and counts.
- Status: ready.

Figure 13: H3 lead-time histogram

- Figure artifact: `data/results/thesis_h3_lead_time_amount.png`
- Source artifact: `data/results/h3_lead_time_histograms.csv`
- Supporting artifact: `data/results/h3_lead_time_event_rows.csv`
- Thesis role: visualise descriptive tier activity around selected movements or
  events.
- Status: ready; no new interpretation beyond descriptive timing patterns.

Figure 14: H3 lead-lag or Granger diagnostic overview

- Figure artifact: `data/results/thesis_h3_granger_pvalues.png`
- Source artifact: `data/results/h3_granger_results.csv`
- Supporting artifacts: `data/results/h3_lead_lag_correlations.csv`,
  `data/results/h3_granger_metadata.json`
- Thesis role: summarise predictive timing diagnostics.
- Status: ready; must include multiple-testing and non-causal caveats.

Figure 15: Historical politics/geo anomaly diagnostics

- Figure artifact: `data/results/thesis_h3_event_wallet_anomalies.png`
- Source artifact: `data/results/h3_event_wallet_anomaly_summary.csv`
- Supporting artifact: `data/results/h3_event_wallet_anomaly_metadata.json`
- Thesis role: visualise which curated events show clusters of market,
  wallet-tier, active-wallet, and concentration anomalies.
- Status: ready as a descriptive monitor prototype figure; not evidence of
  causality, private information, misconduct, or profitability.

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
  comparisons, pairwise lower-loss counts, and the forecast-quality figure.
- Python also audited whether the local H1 baseline can be expanded beyond the
  current overlap window.
- Python added a curated final-snapshot extension for eight resolved 2024
  election outcomes where both a Polymarket final-time probability and a
  FiveThirtyEight final probability forecast are available.
- Python added a state-level poll-snapshot extension for 13 resolved 2024
  presidential state outcomes. The extension transforms FiveThirtyEight
  polling-average Republican margins into Republican-win probabilities with a
  documented normal-error model before Brier loss is calculated.
- Python added two 50-state model-forecast extensions, Rieke and
  270toWin/JHK. Both compare Polymarket Republican-win state prices with
  traditional model probabilities and keep state-context limitations explicit.
- Python added a fixed-bin H1 calibration diagnostic from resolved case
  artifacts. It excludes the 194 daily national rows from calibration claims
  because those rows repeat one resolved election outcome, and the figure uses
  unconnected sparse-bin reliability points rather than a smooth curve.
- Python added a larger H1 state-date poll panel from the daily 538
  state-polling-average rows and bounded Polymarket CLOB history. The panel is
  repeated forecast-row evidence and currently contradicts the strong
  Polymarket-better claim.
- Python added a temporal diagnostic for that panel. It shows that the full
  panel is negative for Polymarket, while August and September 2024 form a
  late diagnostic subset where Polymarket has lower loss in most rows.
- Python added a forecast-horizon diagnostic for that panel. It shows that the
  <=90-day window before the 2024 election supports Polymarket, while the
  earlier horizons explain the negative full-panel result.
- Python added a state-level support diagnostic for the <=90-day horizon. It
  shows Polymarket support in 8 of 13 states by mean Brier and row majority.
- Python added a <=90-day score-quality diagnostic for the same panel window.
  It shows lower Polymarket mean Brier, lower fixed-bin ECE, and slightly
  higher probability separation, while keeping the one-election-context
  limitation explicit.
- Python added a H1 claim-evidence audit. It joins the current H1 outputs into
  one claim ledger: 16 of 22 audit rows support bounded Polymarket advantage,
  5 rows contradict the strong claim, 12 of 15 directly poll-related rows
  support bounded Polymarket claims, and the broad many-cases claim remains
  unproven.
- Python added a focused H1 poll-comparison result scorecard. It states the
  directly poll-related result as a bounded claim: 262 of 285 late
  low/middle-distance state-date rows and 9 of 9 states support Polymarket,
  while the full panel and high-distance rows remain explicit counterexamples.
- Python added a H1 poll-scope frontier diagnostic. It scans six horizon
  cutoffs and five poll-distance scopes, producing 30 scope rows. Eight scopes
  meet the robust-support rule. The largest robust scope is <=120 days plus
  low/middle poll distance with 313 of 433 state-date rows supporting
  Polymarket and 18 of 26 state-month units supporting Polymarket
  (exact p=0.037759), while the full panel remains a poll-derived
  counterexample.
- Python added a H1 poll-comparison unit-robustness diagnostic. It aggregates
  the same primary scope into coarser units: 9 of 9 states, 17 of 17
  state-month units, 17 of 17 state-horizon units, and 4 of 4 horizon-tier
  units support Polymarket. The state-month exact one-sided p-value is
  0.0000076294 with exact 95 percent lower support-share bound 0.8384, while
  full-panel and high-distance state-month counterexamples remain visible.
- Python added a H1 state-source consensus diagnostic. It shows that the
  all-source state consensus favours traditional comparators in 37 of 50
  states, while the narrower two-direct-poll-transform subset favours
  Polymarket in 8 of 13 states.
- Python added a H1 competitive-state diagnostic. It uses quantile-derived
  comparator-distance tiers and shows a bounded Polymarket advantage in the
  lowest-distance subset, while the highest-distance subset remains a clear
  counterexample to a broad claim.
- Python added a H1 state-date competitiveness x horizon diagnostic. It shows
  that the <=90-day Polymarket advantage is concentrated in low/middle
  poll-distance rows: 262 of 285 such rows support Polymarket, while the
  <=90-day high-distance rows support poll-derived probabilities in 72 of 72
  rows.
- Python added a H1 state-level significance diagnostic for that same
  low/middle-distance scope. Treating each state as one diagnostic unit,
  Polymarket has lower-loss majority support in 9 of 9 states; the exact
  one-sided binomial p-value is 0.001953125.
- RCP remains excluded because no RCP-specific probability transformation is
  documented.

Evidence to cite:

- Table 2: H1 forecast-quality summary.
- Figure 1: H1 forecast-quality comparison.
- Figure 2: H1 forecast-quality synthesis.
- Figure 2b: H1 calibration diagnostic.
- Figure 2c: H1 claim-evidence audit.
- Figure 2d: H1 poll-comparison result.
- Figure 2d-1: H1 poll-claim readiness.
- Figure 2d-2: H1 poll-scope frontier.
- Figure 2d-3: H1 poll-decision matrix.
- Figure 2d-4: H1 robust poll-scope quality.
- Figure 2d-5: H1 robust poll-scope unit quality.
- Figure 2e: H1 poll-comparison unit robustness.
- Figure 3: H1 evidence-scope audit.
- Figure 4: H1 expansion-readiness audit.
- Figure 5: H1 final-snapshot extension.
- Figure 6: H1 state-poll-snapshot extension.
- Figure 6a: H1 popular-vote extension.
- Figure 6b: H1 state-date poll panel.
- Figure 6c: H1 state-date poll panel temporal diagnostic.
- Figure 6d: H1 state-date poll panel forecast-horizon diagnostic.
- Figure 6e: H1 <=90-day state-level support.
- Figure 6f: H1 <=90-day score-quality diagnostic.
- Figure 6g: H1 state-date competitiveness x horizon diagnostic.
- Figure 6h: H1 state-level significance diagnostic.
- Figure 7: H1 poll-transform sensitivity.
- Figure 8: H1 state-poll coverage audit.
- Figure 8a: H1 margin-threshold readiness audit.
- Figure 9: H1 Rieke 50-state forecast extension.
- Figure 10a: H1 270toWin polling-average extension.
- Figure 10: H1 270toWin/JHK 50-state forecast extension.
- Figure 10b: H1 state-source consensus diagnostic.
- Figure 10c: H1 competitive-state diagnostic.
- `data/results/thesis_h1_summary.csv`.
- `data/results/h1_brier_scores.csv`.
- `data/results/h1_diebold_mariano.json`.
- `data/results/h1_forecast_quality_pairwise.csv`.
- `data/results/h1_forecast_quality_synthesis.csv`.
- `data/results/h1_calibration_diagnostic_summary.csv`.
- `data/results/h1_calibration_diagnostic_pairwise.csv`.
- `data/results/h1_expansion_readiness.csv`.
- `data/results/h1_final_snapshot_cases.csv`.
- `data/results/h1_final_snapshot_summary.csv`.
- `data/results/h1_state_poll_snapshot_cases.csv`.
- `data/results/h1_state_poll_snapshot_summary.csv`.
- `data/results/h1_270towin_poll_average_cases.csv`.
- `data/results/h1_270towin_poll_average_summary.csv`.
- `data/results/h1_popular_vote_cases.csv`.
- `data/results/h1_popular_vote_summary.csv`.
- `data/results/h1_state_poll_panel_cases.csv`.
- `data/results/h1_state_poll_panel_summary.csv`.
- `data/results/h1_state_poll_panel_state_summary.csv`.
- `data/results/h1_state_poll_panel_temporal_summary.csv`.
- `data/results/h1_state_poll_panel_temporal_claim_audit.csv`.
- `data/results/h1_state_poll_panel_horizon_summary.csv`.
- `data/results/h1_state_poll_panel_horizon_claim_audit.csv`.
- `data/results/h1_state_poll_panel_horizon_state_support.csv`.
- `data/results/h1_state_poll_panel_horizon_state_support_summary.csv`.
- `data/results/h1_state_poll_panel_near_window_quality_summary.csv`.
- `data/results/h1_state_poll_panel_near_window_quality_bins.csv`.
- `data/results/h1_state_poll_panel_near_window_quality_rows.csv`.
- `data/results/h1_rieke_state_forecast_cases.csv`.
- `data/results/h1_rieke_state_forecast_summary.csv`.
- `data/results/h1_270towin_state_forecast_cases.csv`.
- `data/results/h1_270towin_state_forecast_summary.csv`.

Allowed interpretation:

- The current baseline supports a forecast-quality comparison over the tested
  overlap window.
- A lower Brier Score indicates lower squared forecast error in that window.

Required caution:

- H1 is not a reaction-speed test.
- The Polymarket and prior-day Polymarket Brier means are nearly identical in
  the current output, so H1 should not be used as evidence of faster
  information integration.
- The expansion-readiness audit shows that local Polymarket has additional
  daily prices after the current H1 end date, but no compatible local
  FiveThirtyEight probability rows for those days. These extra market prices
  therefore do not create additional paired Brier comparisons.
- The final-snapshot extension has only eight resolved outcomes from the same
  2024 election-day context. It is a small compatibility check, not a daily
  time series and not a broad many-markets proof.
- The state-poll-snapshot extension has 13 resolved state outcomes from one
  polling-average snapshot date. It increases the independent H1 case count,
  but it is a poll-derived probability transformation, not an official
  FiveThirtyEight state win forecast and not a raw-poll Brier comparison.
- The Rieke and 270toWin/JHK 50-state extensions support lower aggregate mean
  Polymarket Brier loss, but neither supports a claim that Polymarket has lower
  loss in most state-level cases. The 270toWin/JHK source also has 28 censored
  `>99.9%` bucket values and no exact publication timestamp.

Further investigations:

- Add further state or market snapshots only when the probability
  transformation is documented before use.
- Document and test an RCP-specific probability transformation before adding
  RCP to H1.
- Add sensitivity checks for alternative forecast horizons or market
  definitions if additional probability series become available.
- Add further resolved markets only when each has Polymarket probability
  history and a compatible traditional probability forecast or a documented
  poll-share-to-probability transformation.

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
- Figure 11: H2 event-window movement overview.
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
- Figure 12: H3 wallet-tier distribution.
- Figure 13: H3 lead-time histogram.
- Figure 14: H3 Granger diagnostic overview.
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
- First define deterministic anomaly outputs and review their shape.
- Then start with one deterministic historical backtest baseline and compare
  it against simple benchmarks.

### Chapter Closing

The first empirical package should close with a balanced statement:

- H1 provides forecast-quality evidence.
- H2 provides daily event-window response evidence.
- H3 provides wallet-tier timing diagnostics.
- Together, these layers support a structured discussion of informational
  efficiency in the studied Polymarket case, but they do not prove universal
  market efficiency, insider activity, intraday speed, or strategy
  profitability.

## Overleaf-Ready Results Chapter Draft

This draft is thesis-facing prose prepared for later Overleaf transfer. It uses
Swiss spelling conventions and keeps the interpretation tied to deterministic
source artifacts. Table and figure references are placeholders and should be
renumbered in the final LaTeX document.

### Kapitelauftakt

Die empirische Analyse operationalisiert informationelle Effizienz nicht als
direkt beobachtbare Eigenschaft, sondern ueber drei nachvollziehbare
Teilperspektiven. Erstens wird geprueft, ob die Polymarket-Wahrscheinlichkeiten
im untersuchten Ueberlappungszeitraum eine geringere Prognoseabweichung
aufweisen als vergleichbare traditionelle Prognosequellen. Zweitens wird
untersucht, ob sich die Polymarket-Wahrscheinlichkeiten in taeglichen
Event-Fenstern um vorab kuratierte politische Ereignisse in plausibler Weise
bewegen. Drittens wird analysiert, ob aggregierte Wallet-Aktivitaet
dataset-relativer Wallet-Tiers zeitliche Muster vor oder um Preisbewegungen
zeigt.

Alle Resultate in diesem Kapitel stammen aus deterministischen Python-Outputs
unter `data/results/`. Die verwendeten Tabellen und Abbildungen sind deshalb
nicht als freie Interpretation eines Sprachmodells zu verstehen, sondern als
kompakte Darstellung reproduzierbarer Artefakte. Die Resultate erlauben eine
strukturierte Diskussion der informationellen Effizienz im Fall Polymarket
waehrend der US-Wahl 2024. Sie beweisen jedoch nicht, dass Polymarket allgemein,
in allen Maerkten oder in zukuenftigen Wahlzyklen effizient ist.

### H1: Prognosequalitaet

Die erste Hypothese vergleicht die Prognosequalitaet von Polymarket mit
FiveThirtyEight und einfachen deterministischen Baselines. Grundlage ist ein
taeglicher Ueberlappungszeitraum von 194 Beobachtungen zwischen dem
1. Maerz 2024 und dem 12. September 2024. Fuer jede Quelle wurde der Brier
Score als quadrierter Prognosefehler berechnet; zusaetzlich wurden
Diebold-Mariano-Vergleiche der Verlustreihen erstellt. Die entsprechenden
Artefakte sind `data/results/thesis_h1_summary.csv`,
`data/results/h1_brier_scores.csv`, `data/results/h1_diebold_mariano.json` und
`data/results/h1_forecast_quality.png`.

Im aktuellen Baseline-Output liegt der mittlere Brier Score von Polymarket bei
0.2303, waehrend FiveThirtyEight bei 0.3324 liegt. Die einfache 50-Prozent-
Baseline liegt bei 0.2500. Damit zeigt die erste Auswertung, dass Polymarket im
getesteten Ueberlappungszeitraum eine tiefere quadratische
Prognoseabweichung aufweist als FiveThirtyEight und auch besser abschneidet als
die konstante 50-Prozent-Baseline. Der Diebold-Mariano-Vergleich zwischen
Polymarket und FiveThirtyEight weist im Output einen sehr kleinen p-Wert aus
(`6.71e-61`), was auf deutliche Unterschiede in den berechneten Verlustreihen
hinweist. Die neue paarweise H1-Auswertung zeigt zusaetzlich, dass Polymarket
an 194 von 194 taeglichen Paaren einen niedrigeren Brier-Verlust als
FiveThirtyEight hatte; der mittlere Verlustvorteil betraegt 0.1021
Brier-Punkte.

Diese Evidenz stuetzt eine vorsichtige Aussage zur Prognosequalitaet:
Polymarket hatte im untersuchten Zeitraum gemaess Brier Score tiefere
Prognoseverluste als die beruecksichtigte FiveThirtyEight-Reihe. FiveThirtyEight
ist dabei eine poll-basierte Probability-Forecast-Reihe, kein Rohpoll. Daraus
folgt jedoch noch keine Aussage zur Reaktionsgeschwindigkeit. Besonders wichtig
ist, dass der Brier Score der
Vortags-Polymarket-Baseline mit 0.2303 nahezu identisch zum aktuellen
Polymarket-Wert ist; der Diebold-Mariano-Vergleich zwischen Polymarket und der
Vortags-Baseline ist entsprechend nicht auffaellig (`p = 0.9822`). H1 sollte
daher als Prognosequalitaetsvergleich und nicht als Speed-Test interpretiert
werden. RealClearPolitics bleibt in dieser Auswertung ausgeschlossen, bis eine
dokumentierte und getestete Wahrscheinlichkeitstransformation vorliegt.
Eine klassische Reliability- oder Kalibrierungskurve bleibt fuer diesen
Baseline-Stand nur eingeschraenkt aussagekraeftig, weil die 194 Zeilen
wiederholte Tagesprognosen fuer ein einziges geloestes Wahlereignis und nicht
194 unabhaengige Wahlereignisse sind.
Die neue Cross-Source-Synthesis in
`data/results/h1_forecast_quality_synthesis.csv` und
`data/results/h1_forecast_quality_synthesis.png` macht diese Grenze in einer
Uebersicht sichtbar: 6 von 7 aktuellen H1-Vergleichszeilen zeigen einen
niedrigeren mittleren Polymarket-Brier, aber nur 3 von 7 zeigen auch eine
Mehrheit niedrigerer Einzelfallverluste. Keine der 7 Zeilen traegt derzeit
den breiten Viele-Faelle-Beweis. Die neue siebte Zeile ist das
State-Date-Poll-Panel und spricht gegen den starken Polymarket-Claim.
Die neue Kalibrierungsdiagnostik in
`data/results/h1_calibration_diagnostic_summary.csv`,
`data/results/h1_calibration_diagnostic_pairwise.csv` und
`data/results/h1_calibration_diagnostic.png` zieht die Kalibrierungsfrage aus
den geloesten Fallartefakten statt aus der 194-Tage-Ein-Outcome-Kurve. Sie
umfasst 192 Forecast-Case-Zeilen aus 7 Forecast-Quellen, 26 belegte feste
20-Prozentpunkt-Bins und 5 Pairwise-Reihen. In diesen 5 Pairwise-Reihen hat
Polymarket jeweils den niedrigeren mittleren Brier Score, aber nur 2 von 5
Reihen zeigen auch eine Mehrheit niedrigerer Einzelfallverluste und 0 von 5
stuetzen den breiten Viele-Faelle-Beweis. Im 50-State-Set liegt Polymarket
beim Mean Brier bei 0.0262, Rieke bei 0.0296 und 270toWin/JHK bei 0.0306; bei
der Fixed-Bin-ECE liegt Polymarket jedoch bei 0.0838 gegenueber 0.0774 fuer
Rieke und 0.0802 fuer 270toWin/JHK. Deshalb ist die saubere Aussage: bessere
aggregierte Forecast-Qualitaet nach Brier, aber kein klarer
Kalibrierungssieg.

Das State-Date-Poll-Panel in `data/results/h1_state_poll_panel_cases.csv`,
`data/results/h1_state_poll_panel_summary.csv` und
`data/results/h1_state_poll_panel.png` nutzt dieselbe dokumentierte
Normalfehler-Transformation auf alle gueltigen 538-State-Date-REP/DEM-Paare
zwischen dem 1. Maerz 2024 und dem 12. September 2024 und matched diese gegen
bounded Polymarket-CLOB-History. Es entstehen 1,720 gematchte State-Date-Zeilen
ueber 15 States und 186 Daten. In diesem Panel hat Polymarket in 360 Zeilen
den niedrigeren Brier-Verlust, die poll-derived 538-Transformation in 1,360
Zeilen. Der mittlere Brier Score liegt bei 0.1595 fuer Polymarket und 0.1026
fuer die poll-derived Transformation. Dieses groessere Panel ist deshalb ein
Gegenbefund zur These, dass Polymarket in vielen poll-derived Faellen besser
sei. Es bleibt dennoch eine wiederholte Forecast-Row-Auswertung und keine
1,720 unabhaengigen Wahlen.
Die Temporal-Diagnose in
`data/results/h1_state_poll_panel_temporal_summary.csv`,
`data/results/h1_state_poll_panel_temporal_claim_audit.csv` und
`data/results/h1_state_poll_panel_temporal_diagnostic.png` zeigt, dass dieser
Gegenbefund zeitlich nicht gleichfoermig ist. Von 7 Monatsfenstern stuetzen 2
Monate Polymarket: In August und September 2024 hat Polymarket in 280 von
387 gematchten State-Date-Zeilen den niedrigeren Verlust, die poll-derived
Transformation in 107 Zeilen. Der mittlere Brier Score liegt in diesen
stuetzenden Monaten bei 0.1842 fuer Polymarket und 0.2543 fuer die
poll-derived Transformation. Dieser spaete Teilbefund ist wichtig fuer die
Interpretation der Forecast-Qualitaet, bleibt aber ein konditionierter
Teilbereich desselben Panels und hebt den negativen Vollpanel-Befund nicht auf.
Die Forecast-Horizon-Diagnose in
`data/results/h1_state_poll_panel_horizon_summary.csv`,
`data/results/h1_state_poll_panel_horizon_claim_audit.csv` und
`data/results/h1_state_poll_panel_horizon_diagnostic.png` strukturiert
denselben Befund nach Tagen bis zur Wahl am 5. November 2024. Im
<=90-Tage-Fenster hat Polymarket in 262 von 357 gematchten Zeilen den
niedrigeren Verlust, die poll-derived Transformation in 95 Zeilen. Der
mittlere Brier Score liegt bei 0.1799 fuer Polymarket und 0.2520 fuer die
poll-derived Transformation. Ueber 90 Tage vor der Wahl kehrt sich dies um:
Polymarket liegt nur in 98 von 1,363 Zeilen vorne. Die belastbare
Interpretation ist deshalb ein Horizon-Muster, nicht ein allgemeiner
Vollpanel-Sieg.
Die State-Level-Horizon-Diagnose in
`data/results/h1_state_poll_panel_horizon_state_support.csv`,
`data/results/h1_state_poll_panel_horizon_state_support_summary.csv` und
`data/results/h1_state_poll_panel_horizon_state_support.png` aggregiert das
<=90-Tage-Fenster auf States. Polymarket hat in 8 von 13 States den
niedrigeren mittleren Brier Score und ebenfalls in 8 von 13 States eine
Mehrheit niedrigerer Tagesverluste. Damit ist der spaete Polymarket-Vorteil
nicht nur ein Zeilenartefakt, sondern auch auf State-Ebene sichtbar. Die
Einschraenkung bleibt: Diese 13 States gehoeren zum selben Wahlkontext.
Die Score-Quality-Diagnose in
`data/results/h1_state_poll_panel_near_window_quality_summary.csv`,
`data/results/h1_state_poll_panel_near_window_quality_bins.csv` und
`data/results/h1_state_poll_panel_near_window_quality.png` visualisiert
dasselbe <=90-Tage-Fenster als Kalibrierungs- und Forecast-Qualitaetsansicht.
Sie umfasst 714 Forecast-Zeilen aus 357 State-Date-Faellen und zwei Quellen.
Polymarket hat niedrigeren Mean Brier (0.1799 vs 0.2520), niedrigeren
Fixed-Bin-ECE (0.3797 vs 0.4391) und hoehere Probability-Separation (0.4560
vs 0.4366). Diese Werte stuetzen das spaete Polymarket-Forecast-Quality-
Argument, beweisen aber keinen breiten Viele-Faelle-Claim.
Der zusaetzliche Scope-Audit in `data/results/h1_evidence_scope.csv` und
`data/results/h1_evidence_scope.png` haelt diese Grenze explizit fest:
Der aktuelle H1-Brier-Stand enthaelt 194 taegliche Paarvergleiche, aber nur
ein unabhaengiges geloestes H1-Outcome. Die Schweizer Referendumsdaten sind
vor dem Abstimmungstag noch nicht geloest und bleiben deshalb eine
poll-proxy-deskriptive Analyse, keine Brier-Score-Erweiterung. Die sieben
kuratierten H2-Ereignisse sind Ereignisfenster innerhalb desselben
Praesidentschaftsmarkts und duerfen nicht als eigene H1-Forecast-Faelle
gezaehlt werden.

Der neue Erweiterungs-Audit in
`data/results/h1_expansion_readiness.csv` und
`data/results/h1_expansion_readiness.png` prueft, ob die bestehende lokale
Datenbasis H1 sofort ausweiten kann. Das Ergebnis ist negativ: Die lokale
Polymarket-Reihe enthaelt zwar 55 weitere Tagespreise nach dem 12. September
2024, aber die lokale FiveThirtyEight-Probability-Reihe enthaelt 0 passende
Tageswerte nach diesem Datum. Daraus entstehen aktuell 0 zusaetzliche H1-
Brier-Paare. Offizielle Polling-Averages oder Rohpolls duerfen nicht als
Gewinnwahrscheinlichkeiten in den Brier Score eingehen, solange keine
dokumentierte und getestete Transformation vorliegt.

Als kleine kompatible Erweiterung wurde zusaetzlich ein Final-Snapshot-Check
fuer acht geloeste 2024-Outcomes erstellt: Praesidentschaft Trump,
Senatskontrolle Republikaner, House-Kontrolle Republikaner sowie fuenf
Senatsrennen in Montana, Ohio, West Virginia, Florida und Texas. Grundlage
sind Polymarket-Wahrscheinlichkeiten zum Zeitpunkt des FiveThirtyEight final
forecast am 5. November 2024 um 11:00 UTC. In diesen acht Faellen hat
Polymarket in 5 von 8 Outcomes einen niedrigeren Brier-Verlust als der
538-Final-Forecast. Der mittlere Brier Score liegt bei 0.0784 fuer
Polymarket und 0.0933 fuer FiveThirtyEight; der mittlere Verlustvorteil
betraegt 0.0149 Brier-Punkte. Diese Erweiterung erhoeht die Zahl der
kuratierten geloesten H1-Final-Snapshot-Outcomes auf acht, bleibt aber klein,
liegt im selben Election-Day-Kontext und ist keine wissenschaftlich
tragfaehige Viele-Maerkte-Erweiterung.

Als weitere H1-Erweiterung wurde ein State-Poll-Snapshot-Check fuer 13
geloeste Praesidentschafts-State-Outcomes erstellt. Grundlage sind die im
FiveThirtyEight-Datenrepository bewahrten Presidential General Polling
Averages vom 12. September 2024. Fuer jeden State wird die Republican-minus-
Democratic Polling-Marge mit einem vorab dokumentierten Normalfehler-Modell in
eine Republican-Win-Wahrscheinlichkeit transformiert. Der Fehlerparameter
nutzt die FiveThirtyEight-Aussage, dass das Modell im Durchschnitt mit einem
Poll-Fehler von 3.8 Prozentpunkten rechnet; im Code wird daraus unter einer
symmetrischen Normalfehlerannahme `sigma = mae / sqrt(2/pi)` abgeleitet. In
diesen 13 State-Faellen hat Polymarket in 8 Faellen einen niedrigeren
Brier-Verlust als die poll-derived Wahrscheinlichkeit; die transformierte
Poll-Wahrscheinlichkeit hat in 5 Faellen den niedrigeren Verlust. Der mittlere
Brier Score liegt bei 0.1336 fuer Polymarket und 0.1764 fuer die
poll-derived Wahrscheinlichkeiten; der mittlere Verlustvorteil betraegt
0.0428 Brier-Punkte. Diese Erweiterung ist methodisch wichtiger als ein
Rohpoll-Vergleich, weil Polling-Averages nicht direkt als
Gewinnwahrscheinlichkeiten verwendet werden. Sie bleibt dennoch eine
modellabhaengige Transformation und ist kein offizieller FiveThirtyEight
State-Win-Forecast.

Die Poll-Transform-Sensitivitaet prueft dieselben 13 State-Outcomes ueber
eine explizite MAE-Grid von 2.0 bis 10.0 Prozentpunkten. In allen 12
Parameterzeilen bleibt der mittlere Brier Score fuer Polymarket niedriger als
fuer die transformierten poll-derived Wahrscheinlichkeiten. Die Zahl der
State-Outcomes mit niedrigerem Polymarket-Einzelfallverlust liegt je nach
MAE-Annahme zwischen 7 und 12 von 13. Dieser Robustheitscheck variiert nur die
Fehlerannahme der Poll-Margin-Transformation; er fuegt keine neuen
unabhaengigen Maerkte hinzu und darf nicht als zusaetzliche Fallzahl gezaehlt
werden.

Der State-Poll-Coverage-Audit zeigt, warum die Fallzahl nicht einfach aus der
Polymarket-Abdeckung heraus ausgeweitet wurde. Fuer alle 50 US-States ist ein
Polymarket-State-Markt im kuratierten Slug-Satz vorhanden. Der bewahrte
FiveThirtyEight-Polling-Average-Snapshot enthaelt aber nur fuer 13 dieser
States REP/DEM-Zeilen. Deshalb entstehen 13 valide H1-Brier-Paare; 37 States
fallen wegen fehlender 538-Snapshot-Pollwerte aus und kein State wegen
fehlender beider Quellen. Dieser Audit ist eine Abdeckungs- und
Methodikvisualisierung, kein zusaetzlicher Forecast-Qualitaetsbeleg.

Als weitere externe Forecast-Quelle wurde das oeffentliche Rieke-2024-POTUS-
Modell ausgewertet. Dieses Modell berichtet State-Win-Wahrscheinlichkeiten fuer
Harris; fuer den Vergleich wird deterministisch die Komplementwahrscheinlichkeit
als Republican-Win-Forecast verwendet. Die Erweiterung umfasst alle 50
geloesten State-Outcomes. Polymarket hat einen leicht niedrigeren mittleren
Brier Score als Rieke, 0.0262 gegen 0.0296, liegt aber nur in 12 von 50
Einzelstaaten vor; Rieke liegt in 38 von 50 Einzelstaaten vor. Diese Evidenz
stuetzt deshalb eine aggregierte Brier-Aussage fuer Polymarket, aber nicht die
staerkere Behauptung, Polymarket sei in den meisten State-Faellen besser.
Zudem teilen alle State-Faelle denselben Election-Kontext und sind nicht wie
50 unabhaengige Wahlereignisse zu interpretieren.

Weitere Untersuchungen sollten pruefen, ob die H1-Resultate bei anderen
Zeitraeumen, alternativen Forecast-Horizonten oder zusaetzlichen kompatiblen
Probability-Forecasts stabil bleiben. Eine Erweiterung um RCP ist erst sinnvoll,
wenn klar dokumentiert ist, wie Polling-Averages in Wahrscheinlichkeiten
ueberfuehrt werden.

### H2: Taegliche Event-Window-Reaktion

Die zweite Hypothese untersucht, ob Polymarket-Wahrscheinlichkeiten um
vorab kuratierte politische Ereignisse herum reagieren. Fuer den ersten
Baseline-Lauf wurden sieben Ereignisse in `data/events_timeline_seed.csv`
festgelegt. Die Analyse verwendet zwei taegliche Fenster: ein primaeres Fenster
von `[0d, +1d]` und ein Sensitivitaetsfenster von `[-1d, +3d]`. Die Ergebnisse
liegen in `data/results/thesis_h2_summary.csv`,
`data/results/h2_event_window_summary.csv`,
`data/results/h2_event_window_rows.csv` und der Abbildung
`data/results/thesis_h2_event_window_car.png`.

Die Resultate zeigen, dass die Polymarket-Zeitreihe um mehrere Ereignisse
messbare taegliche Bewegungen aufweist. Beispielsweise ist fuer das Ereignis
`evt_2024_07_13_trump_shooting` im primaeren Fenster ein finaler kumulierter
abnormaler Change von 0.0719 dokumentiert. Fuer `evt_2024_07_15_vance_vp_pick`
liegt der Wert im Sensitivitaetsfenster bei 0.0915. Andere Ereignisse weisen
negative Bewegungen aus, etwa `evt_2024_05_30_trump_conviction` mit -0.0408 im
primaeren Fenster und `evt_2024_09_11_harris_trump_debate` mit -0.0293 im
primaeren Fenster.

Diese Befunde duerfen als taegliche Event-Window-Reaktionen interpretiert
werden. Sie zeigen, dass die Markt-Wahrscheinlichkeiten in den definierten
Fenstern nicht statisch bleiben und dass einzelne kuratierte Ereignisse mit
erkennbaren Bewegungen in der Polymarket-Zeitreihe verbunden sind. Die Analyse
belegt jedoch keine Intraday-Reaktionsgeschwindigkeit, weil die aktuelle
Zeitreihe taeglich aggregiert ist. Ebenso duerfen Ereignisse nicht nachtraeglich
auf Basis beobachteter Preisreaktionen hinzugefuegt oder entfernt werden, ohne
einen separaten Sensitivitaetslauf zu dokumentieren.

Weitere Untersuchungen koennten die Event-Auswahl erweitern, sofern die
Inklusionsregeln vorab festgelegt werden. Fuer echte Aussagen zur
Reaktionsgeschwindigkeit waeren intraday Polymarket-Daten notwendig. Zusaetzlich
koennte spaeter geprueft werden, ob validierte News- oder Sentiment-Variablen
die taeglichen Event-Reaktionen erklaeren oder ergaenzen.

### H3: Wallet-Tier-Timing-Diagnostik

Die dritte Hypothese untersucht, ob aggregierte Wallet-Aktivitaet zeitliche
Muster vor oder um Polymarket-Preisbewegungen zeigt. Die Wallets werden nicht
ueber fixe USD-Grenzen klassifiziert, sondern ueber dataset-relative
Perzentile der kumulierten beobachteten `amount_usd` je Wallet. Dadurch bleibt
die Tier-Definition an die beobachtete Verteilung gebunden. Die zentralen
Artefakte sind `data/results/thesis_h3_summary.csv`,
`data/results/h3_wallet_distribution_inventory.json`,
`data/results/h3_wallet_tiers.csv`,
`data/results/h3_tiered_wallet_activity_daily.csv`,
`data/results/h3_lead_time_histograms.csv`,
`data/results/h3_lead_lag_correlations.csv` und
`data/results/h3_granger_results.csv`.

Der aktuelle Output unterscheidet vier Wallet-Tiers. Das oberste
`tier_1_top_1pct` enthaelt 32 Wallets, `tier_2_top_5pct` enthaelt 120 Wallets,
`tier_3_top_10pct` enthaelt 150 Wallets und die beobachtete Baseline darunter
enthaelt 2704 Wallets. Fuer die Modellierung wurden 1216 taeglich alignierte
Beobachtungen zwischen Tier-Aktivitaet und Polymarket-Preisveraenderungen
verwendet. Die staerkste absolute Lead-Lag-Korrelation im aktuellen
Summary-Output liegt beim obersten Tier bei Lag 1 und betraegt 0.1858. Im
Granger-Output weist dasselbe Tier bei Lag 1 den kleinsten dokumentierten
p-Wert von 0.0012 auf.

Diese Ergebnisse koennen als erste Timing-Diagnostik gelesen werden: Bestimmte
dataset-relative Wallet-Tiers, insbesondere das oberste Tier, zeigen im
aktuellen Baseline-Output messbare zeitliche Zusammenhaenge mit taeglichen
Polymarket-Preisveraenderungen. Die Formulierung muss jedoch streng bleiben.
Korrelationen und Granger-Tests zeigen keine echte Kausalitaet, keine private
Information und kein Fehlverhalten. Sie zeigen nur, dass die getesteten
Zeitreihen unter den Modellannahmen eine predictive timing diagnostic liefern
koennen.

Die wichtigsten Einschraenkungen sind die BUY-only-Struktur des aktuellen
Wallet-Extracts, die taegliche Aggregation und die Gefahr multipler Tests.
Deshalb sollten H3-Resultate vor starken Schlussfolgerungen mit
Multiple-Testing-Korrekturen, alternativen Lag-Spezifikationen und wenn
moeglich vollstaendigerer Kauf-/Verkaufsrichtung geprueft werden. Ein weiterer
naheliegender Schritt ist ein historischer Backtest, der testet, ob
Tier-Aktivitaet ausserhalb der Stichprobe eine verwertbare Signalinformation
enthaelt.

### Bruecke Zum Strategie-Prototyp

Die bisherigen Resultate liefern noch keine Handelsstrategie. Sie liefern aber
drei Arten von geprueften Inputs fuer einen spaeteren historischen
Research-Prototyp: Prognosequalitaet aus H1, taegliche Event-Reaktionen aus H2
und Wallet-Timing-Diagnostik aus H3. Ein solcher Prototyp darf nur als
historischer Backtest formuliert werden. Agenten koennten spaeter
Signalhypothesen vorschlagen, aber Python muss jede Signal-Spezifikation
validieren und alle Backtest-, PnL-, Drawdown- und Risikometriken berechnen.

Fuer die Thesis ist deshalb zentral, den Strategie-Prototyp nicht als
Live-Trading-System und nicht als Profitversprechen zu praesentieren. Ein
wissenschaftlich sauberer naechster Schritt waere ein deterministischer
Backtest mit expliziten Transaktionskosten, Slippage-Annahmen, Positionslimits
und Out-of-Sample- oder Walk-forward-Auswertung. Erst danach waere eine
Interpretation moeglich, ob die beobachteten Signale historisch nutzbare
predictive information enthalten.

### Zwischenfazit Fuer Das Resultatkapitel

Zusammenfassend zeigt die erste empirische Baseline drei komplementaere
Perspektiven auf informationelle Effizienz. H1 spricht fuer eine bessere
Forecast-Qualitaet von Polymarket im getesteten Ueberlappungsfenster, darf aber
nicht als Speed-Test interpretiert werden. H2 dokumentiert taegliche
Event-Window-Reaktionen um kuratierte politische Ereignisse, erlaubt jedoch
keine Intraday-Aussage. H3 zeigt dataset-relative Wallet-Timing-Diagnostik,
bleibt aber durch BUY-only-Daten, taegliche Aggregation und
Multiple-Testing-Fragen eingeschraenkt. Gemeinsam bilden diese Resultate eine
reproduzierbare Grundlage fuer die Diskussion, ob und in welcher Form
Polymarket im untersuchten Wahlmarkt Informationen widerspiegelt, integriert
oder vorwegnimmt.

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
- H1 forecast-quality summary:
  `data/results/h1_forecast_quality_pairwise.csv`
- H1 forecast-quality figure: `data/results/h1_forecast_quality.png`
- H1 forecast-quality synthesis:
  `data/results/h1_forecast_quality_synthesis.csv`
- H1 forecast-quality synthesis figure:
  `data/results/h1_forecast_quality_synthesis.png`
- H1 forecast-quality synthesis metadata:
  `data/results/h1_forecast_quality_synthesis_metadata.json`
- H1 claim-evidence audit: `data/results/h1_claim_evidence_audit.csv`
- H1 claim-evidence audit summary:
  `data/results/h1_claim_evidence_audit_summary.csv`
- H1 claim-evidence audit figure:
  `data/results/h1_claim_evidence_audit.png`
- H1 claim-evidence audit metadata:
  `data/results/h1_claim_evidence_audit_metadata.json`
- H1 poll-comparison result:
  `data/results/h1_poll_comparison_result.csv`
- H1 poll-comparison result summary:
  `data/results/h1_poll_comparison_result_summary.csv`
- H1 poll-comparison result figure:
  `data/results/h1_poll_comparison_result.png`
- H1 poll-comparison result metadata:
  `data/results/h1_poll_comparison_result_metadata.json`
- H1 poll-claim readiness:
  `data/results/h1_poll_claim_readiness.csv`
- H1 poll-claim readiness summary:
  `data/results/h1_poll_claim_readiness_summary.csv`
- H1 poll-claim readiness figure:
  `data/results/h1_poll_claim_readiness.png`
- H1 poll-claim readiness metadata:
  `data/results/h1_poll_claim_readiness_metadata.json`
- H1 poll-scope frontier:
  `data/results/h1_poll_scope_frontier.csv`
- H1 poll-scope frontier summary:
  `data/results/h1_poll_scope_frontier_summary.csv`
- H1 poll-scope frontier figure:
  `data/results/h1_poll_scope_frontier.png`
- H1 poll-scope frontier metadata:
  `data/results/h1_poll_scope_frontier_metadata.json`
- H1 poll-decision matrix:
  `data/results/h1_poll_decision_matrix.csv`
- H1 poll-decision matrix summary:
  `data/results/h1_poll_decision_matrix_summary.csv`
- H1 poll-decision matrix figure:
  `data/results/h1_poll_decision_matrix.png`
- H1 poll-decision matrix metadata:
  `data/results/h1_poll_decision_matrix_metadata.json`
- H1 robust poll-scope quality rows:
  `data/results/h1_robust_poll_scope_quality_rows.csv`
- H1 robust poll-scope quality bins:
  `data/results/h1_robust_poll_scope_quality_bins.csv`
- H1 robust poll-scope quality summary:
  `data/results/h1_robust_poll_scope_quality_summary.csv`
- H1 robust poll-scope quality pairwise:
  `data/results/h1_robust_poll_scope_quality_pairwise.csv`
- H1 robust poll-scope quality figure:
  `data/results/h1_robust_poll_scope_quality.png`
- H1 robust poll-scope quality metadata:
  `data/results/h1_robust_poll_scope_quality_metadata.json`
- H1 robust poll-scope unit quality units:
  `data/results/h1_robust_poll_scope_unit_quality_units.csv`
- H1 robust poll-scope unit quality summary:
  `data/results/h1_robust_poll_scope_unit_quality_summary.csv`
- H1 robust poll-scope unit quality figure:
  `data/results/h1_robust_poll_scope_unit_quality.png`
- H1 robust poll-scope unit quality metadata:
  `data/results/h1_robust_poll_scope_unit_quality_metadata.json`
- H1 poll-comparison unit robustness:
  `data/results/h1_poll_comparison_unit_robustness_units.csv`
- H1 poll-comparison unit robustness summary:
  `data/results/h1_poll_comparison_unit_robustness_summary.csv`
- H1 poll-comparison unit robustness figure:
  `data/results/h1_poll_comparison_unit_robustness.png`
- H1 poll-comparison unit robustness metadata:
  `data/results/h1_poll_comparison_unit_robustness_metadata.json`
- H1 calibration diagnostic cases:
  `data/results/h1_calibration_diagnostic_cases.csv`
- H1 calibration diagnostic bins:
  `data/results/h1_calibration_diagnostic_bins.csv`
- H1 calibration diagnostic summary:
  `data/results/h1_calibration_diagnostic_summary.csv`
- H1 calibration diagnostic pairwise table:
  `data/results/h1_calibration_diagnostic_pairwise.csv`
- H1 calibration diagnostic figure:
  `data/results/h1_calibration_diagnostic.png`
- H1 calibration diagnostic metadata:
  `data/results/h1_calibration_diagnostic_metadata.json`
- H1 evidence-scope audit: `data/results/h1_evidence_scope.csv`
- H1 evidence-scope figure: `data/results/h1_evidence_scope.png`
- H1 expansion-readiness audit:
  `data/results/h1_expansion_readiness.csv`
- H1 expansion-readiness figure: `data/results/h1_expansion_readiness.png`
- H1 margin-threshold readiness audit:
  `data/results/h1_margin_threshold_readiness.csv`
- H1 margin-threshold readiness figure:
  `data/results/h1_margin_threshold_readiness.png`
- H1 margin-threshold readiness metadata:
  `data/results/h1_margin_threshold_readiness_metadata.json`
- H1 final-snapshot cases: `data/results/h1_final_snapshot_cases.csv`
- H1 final-snapshot summary: `data/results/h1_final_snapshot_summary.csv`
- H1 final-snapshot figure: `data/results/h1_final_snapshot.png`
- H1 final-snapshot metadata: `data/results/h1_final_snapshot_metadata.json`
- H1 state-poll snapshot cases:
  `data/results/h1_state_poll_snapshot_cases.csv`
- H1 state-poll snapshot summary:
  `data/results/h1_state_poll_snapshot_summary.csv`
- H1 state-poll snapshot figure:
  `data/results/h1_state_poll_snapshot.png`
- H1 state-poll snapshot metadata:
  `data/results/h1_state_poll_snapshot_metadata.json`
- H1 popular-vote cases: `data/results/h1_popular_vote_cases.csv`
- H1 popular-vote summary: `data/results/h1_popular_vote_summary.csv`
- H1 popular-vote figure: `data/results/h1_popular_vote.png`
- H1 popular-vote metadata: `data/results/h1_popular_vote_metadata.json`
- H1 state-poll panel cases:
  `data/results/h1_state_poll_panel_cases.csv`
- H1 state-poll panel summary:
  `data/results/h1_state_poll_panel_summary.csv`
- H1 state-poll panel state summary:
  `data/results/h1_state_poll_panel_state_summary.csv`
- H1 state-poll panel coverage:
  `data/results/h1_state_poll_panel_coverage.csv`
- H1 state-poll panel figure:
  `data/results/h1_state_poll_panel.png`
- H1 state-poll panel metadata:
  `data/results/h1_state_poll_panel_metadata.json`
- H1 state-poll panel temporal summary:
  `data/results/h1_state_poll_panel_temporal_summary.csv`
- H1 state-poll panel temporal state-month summary:
  `data/results/h1_state_poll_panel_temporal_state_month.csv`
- H1 state-poll panel temporal claim audit:
  `data/results/h1_state_poll_panel_temporal_claim_audit.csv`
- H1 state-poll panel temporal diagnostic figure:
  `data/results/h1_state_poll_panel_temporal_diagnostic.png`
- H1 state-poll panel temporal diagnostic metadata:
  `data/results/h1_state_poll_panel_temporal_diagnostic_metadata.json`
- H1 state-poll panel horizon summary:
  `data/results/h1_state_poll_panel_horizon_summary.csv`
- H1 state-poll panel horizon state summary:
  `data/results/h1_state_poll_panel_horizon_state_summary.csv`
- H1 state-poll panel horizon claim audit:
  `data/results/h1_state_poll_panel_horizon_claim_audit.csv`
- H1 state-poll panel horizon diagnostic figure:
  `data/results/h1_state_poll_panel_horizon_diagnostic.png`
- H1 state-poll panel horizon diagnostic metadata:
  `data/results/h1_state_poll_panel_horizon_diagnostic_metadata.json`
- H1 state-poll panel horizon state support:
  `data/results/h1_state_poll_panel_horizon_state_support.csv`
- H1 state-poll panel horizon state support summary:
  `data/results/h1_state_poll_panel_horizon_state_support_summary.csv`
- H1 state-poll panel horizon state support figure:
  `data/results/h1_state_poll_panel_horizon_state_support.png`
- H1 state-poll panel horizon state support metadata:
  `data/results/h1_state_poll_panel_horizon_state_support_metadata.json`
- H1 state-poll panel <=90-day score-quality rows:
  `data/results/h1_state_poll_panel_near_window_quality_rows.csv`
- H1 state-poll panel <=90-day score-quality bins:
  `data/results/h1_state_poll_panel_near_window_quality_bins.csv`
- H1 state-poll panel <=90-day score-quality summary:
  `data/results/h1_state_poll_panel_near_window_quality_summary.csv`
- H1 state-poll panel <=90-day score-quality figure:
  `data/results/h1_state_poll_panel_near_window_quality.png`
- H1 state-poll panel <=90-day score-quality metadata:
  `data/results/h1_state_poll_panel_near_window_quality_metadata.json`
- H1 state-poll transform sensitivity:
  `data/results/h1_state_poll_snapshot_sensitivity.csv`
- H1 state-poll transform sensitivity figure:
  `data/results/h1_state_poll_snapshot_sensitivity.png`
- H1 state-poll coverage audit:
  `data/results/h1_state_poll_snapshot_coverage.csv`
- H1 state-poll coverage figure:
  `data/results/h1_state_poll_snapshot_coverage.png`
- H1 Rieke state-forecast cases:
  `data/results/h1_rieke_state_forecast_cases.csv`
- H1 Rieke state-forecast summary:
  `data/results/h1_rieke_state_forecast_summary.csv`
- H1 Rieke state-forecast figure:
  `data/results/h1_rieke_state_forecast.png`
- H1 Rieke state-forecast metadata:
  `data/results/h1_rieke_state_forecast_metadata.json`
- H1 270toWin polling-average cases:
  `data/results/h1_270towin_poll_average_cases.csv`
- H1 270toWin polling-average summary:
  `data/results/h1_270towin_poll_average_summary.csv`
- H1 270toWin polling-average figure:
  `data/results/h1_270towin_poll_average.png`
- H1 270toWin polling-average metadata:
  `data/results/h1_270towin_poll_average_metadata.json`
- H1 270toWin/JHK state-forecast cases:
  `data/results/h1_270towin_state_forecast_cases.csv`
- H1 270toWin/JHK state-forecast summary:
  `data/results/h1_270towin_state_forecast_summary.csv`
- H1 270toWin/JHK state-forecast figure:
  `data/results/h1_270towin_state_forecast.png`
- H1 270toWin/JHK state-forecast metadata:
  `data/results/h1_270towin_state_forecast_metadata.json`
- H1 state-source consensus cases:
  `data/results/h1_state_source_consensus_cases.csv`
- H1 state-source consensus state summary:
  `data/results/h1_state_source_consensus_state_summary.csv`
- H1 state-source consensus summary:
  `data/results/h1_state_source_consensus_summary.csv`
- H1 state-source consensus figure:
  `data/results/h1_state_source_consensus.png`
- H1 state-source consensus metadata:
  `data/results/h1_state_source_consensus_metadata.json`
- H1 competitive-state diagnostic cases:
  `data/results/h1_competitive_state_diagnostic_cases.csv`
- H1 competitive-state diagnostic tiers:
  `data/results/h1_competitive_state_diagnostic_tiers.csv`
- H1 competitive-state diagnostic summary:
  `data/results/h1_competitive_state_diagnostic_summary.csv`
- H1 competitive-state diagnostic figure:
  `data/results/h1_competitive_state_diagnostic.png`
- H1 competitive-state diagnostic metadata:
  `data/results/h1_competitive_state_diagnostic_metadata.json`
- H1 state-poll panel competitiveness grid:
  `data/results/h1_state_poll_panel_competitiveness_grid.csv`
- H1 state-poll panel competitiveness state summary:
  `data/results/h1_state_poll_panel_competitiveness_state.csv`
- H1 state-poll panel competitiveness summary:
  `data/results/h1_state_poll_panel_competitiveness_summary.csv`
- H1 state-poll panel competitiveness figure:
  `data/results/h1_state_poll_panel_competitiveness.png`
- H1 state-poll panel competitiveness metadata:
  `data/results/h1_state_poll_panel_competitiveness_metadata.json`
- H1 state-poll panel state-level significance:
  `data/results/h1_state_poll_panel_state_significance.csv`
- H1 state-poll panel state-level significance summary:
  `data/results/h1_state_poll_panel_state_significance_summary.csv`
- H1 state-poll panel state-level significance figure:
  `data/results/h1_state_poll_panel_state_significance.png`
- H1 state-poll panel state-level significance metadata:
  `data/results/h1_state_poll_panel_state_significance_metadata.json`
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
- H1 expansion-readiness identifies 55 additional local Polymarket daily prices
  after 2024-09-12, 0 compatible local FiveThirtyEight probability rows after
  that date, and therefore 0 additional paired H1 Brier rows now.
- H1 margin-threshold readiness reviews 7 Trump state-margin markets. Four have
  preserved 538 state polling-average rows, but zero have CLOB history inside
  the preserved official 538 polling-average window. The audit therefore adds
  0 H1 Brier rows and documents 4 no-overlap exclusions plus 3 missing-poll
  exclusions.
- H1 final-snapshot extension contains 8 resolved 2024 election outcomes,
  with Polymarket lower loss in 5 cases and FiveThirtyEight lower loss in 3
  cases. Mean Brier is 0.0784 for Polymarket and 0.0933 for FiveThirtyEight.
- H1 state-poll-snapshot extension contains 13 resolved 2024 presidential
  state outcomes from the 2024-09-12 FiveThirtyEight polling-average snapshot.
  Polymarket has lower loss in 8 cases and the poll-derived probability has
  lower loss in 5 cases. Mean Brier is 0.1336 for Polymarket and 0.1764 for
  the transformed poll-derived probabilities.
- H1 state-poll panel extension contains 1,720 matched state-date forecast rows
  across 15 resolved state outcomes and 186 dates. Polymarket has lower loss
  in 360 rows and the poll-derived probability has lower loss in 1,360 rows.
  Mean Brier is 0.1595 for Polymarket and 0.1026 for the transformed
  poll-derived probabilities.
- H1 state-poll panel temporal diagnostic separates the panel by month. The
  full panel remains negative for Polymarket, but the Polymarket-supporting
  months 2024-08 and 2024-09 contain 387 rows across 13 states; Polymarket has
  lower loss in 280 rows, poll-derived probabilities in 107 rows, and mean
  Brier is 0.1842 versus 0.2543.
- H1 state-poll panel forecast-horizon diagnostic separates the same panel by
  days to the 2024-11-05 election. In the <=90-day window, Polymarket has
  lower loss in 262 of 357 rows across 13 states and mean Brier 0.1799 versus
  0.2520. More than 90 days before the election, Polymarket has lower loss in
  only 98 of 1,363 rows.
- H1 <=90-day state-level support diagnostic aggregates that same late window
  by state: Polymarket has lower mean Brier in 8 of 13 states and a majority
  of lower-loss rows in 8 of 13 states; 5 of 13 states do not support
  Polymarket.
- H1 <=90-day score-quality diagnostic contains 714 forecast rows from 357
  state-date cases and two sources. Polymarket has lower mean Brier
  (0.1799 vs 0.2520), lower fixed-bin ECE (0.3797 vs 0.4391), and higher
  probability separation (0.4560 vs 0.4366).
- H1 state-source consensus diagnostic contains 156 source-state comparisons
  across 50 states. Polymarket has lower loss in 43 source-state rows,
  comparators in 112, and one ties. In the all-source state consensus,
  Polymarket leads 9 states, comparators lead 37, and 4 tie. Among 13 states
  covered by both direct poll-transform sources, Polymarket leads 8,
  comparators lead 4, and one ties.
- H1 competitive-state diagnostic uses quantile-derived tiers from the
  comparator probability distance to 0.5. In the lowest-distance tercile,
  Polymarket has lower loss in 35 of 52 all-source cases and 18 of 19 direct
  poll-transform cases. In the highest-distance tercile, Polymarket has lower
  loss in 0 of 40 all-source cases and comparators have lower loss in 40 of
  40.
- H1 state-date competitiveness x horizon diagnostic uses quantile-derived
  tiers from the poll-derived probability distance to 0.5. In the <=90-day
  low/middle-distance subset, Polymarket has lower loss in 262 of 285
  state-date rows and all 9 covered states have a Polymarket lower-loss
  majority. In the <=90-day high-distance subset, Polymarket has lower loss in
  0 of 72 rows and poll-derived probabilities have lower loss in all 72.
- H1 state-level significance diagnostic applies an exact binomial sign test
  to the same late low/middle-distance state scope. Polymarket has lower-loss
  majority support in 9 of 9 states, one-sided p-value 0.001953125, and exact
  95 percent lower support-share bound 0.7169. The late high-distance scope
  remains a counterexample with poll-derived majority support in 5 of 5
  states.
- H1 claim-evidence audit contains 22 audit rows. Polymarket is supported in
  16 bounded rows, 5 rows contradict the strong claim, 12 of 15 directly
  poll-related rows support bounded Polymarket claims, and the broad user
  claim remains 0/not proven.
- H1 poll-comparison result contains 6 result rows. The primary late
  low/middle poll-distance scope supports Polymarket in 262 of 285 state-date
  rows and 9 of 9 states; the exact one-sided state-level p-value is
  0.001953125. Direct poll-related audit rows are 12 of 15 supportive, but the
  full state-date poll panel remains a counterexample with poll-derived
  support in 1360 of 1720 rows and the high-distance late subset remains
  poll-derived 72 of 72. Current H1 goal status is `not_proven`.
- H1 poll-comparison unit robustness contains 255 unit rows. In the primary
  late low/middle poll-distance scope, Polymarket is supported in 9 of 9
  states, 17 of 17 state-month units, 17 of 17 state-horizon units, and 4 of
  4 horizon-tier units. The state-month exact one-sided p-value is
  0.0000076294 and the exact 95 percent lower bound is 0.8384. The full panel
  remains a boundary with poll-derived support in 61 of 80 state-month units,
  and the late high-distance subset remains poll-derived 8 of 8 state-month
  units with exact one-sided p-value 0.00390625. Current H1 goal status is
  still `not_proven`.
- H1 calibration diagnostic contains 192 forecast-case rows across 7 forecast
  sources, 26 nonempty fixed bins, and 5 pairwise rows. Polymarket has lower
  mean Brier in 5 of 5 pairwise rows, majority lower individual loss in 2 of
  5, and broad many-cases support in 0 of 5. Its figure now separates
  aggregate Brier advantage, individual lower-loss counts, and sparse
  calibration points.
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
- The H1 final-snapshot extension is a small same-election-day compatibility
  check, not a daily time series and not evidence for a broad many-markets
  claim.
- The H1 claim-evidence audit supports a bounded late-window statement, but it
  explicitly leaves the broad many-cases user claim unproven because the full
  state-date poll panel, high-distance state-source subset, and late
  high-distance state-date subset contradict the strong claim.
- The H1 state-poll-snapshot extension increases the number of independent
  resolved outcomes, but it is based on one poll snapshot date and a documented
  model assumption. It must not be described as raw polls directly beating or
  losing to Polymarket.
- The H1 state-poll panel is much larger, but its rows are repeated forecasts
  for 15 state outcomes. It should be reported as a counterexample to the broad
  Polymarket-better claim, not as 1,720 independent elections.
- The H1 calibration diagnostic shows lower aggregate Polymarket Brier but
  does not show a clear fixed-bin calibration advantage in the 50-state case
  set; do not describe it as a general calibration win. The <=90-day
  state-date score-quality diagnostic is a narrower late-window exception, not
  a full-panel calibration result.
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
