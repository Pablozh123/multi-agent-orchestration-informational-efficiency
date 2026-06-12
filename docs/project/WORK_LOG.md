# WORK_LOG.md

Append-only project work log. Add one entry before stopping work on a task.

## Entry Format

```markdown
## YYYY-MM-DD - goal_id

Task:

Files changed:

Tests:

Decision:

Next step:
```

## 2026-05-18 - goal-empirical-scope-001

Task:

- Implement project automation for goal-driven Codex work.

Files changed:

- `operations/project/`
- `tests/test_project_automation.py`
- project-control documentation

Tests:

- `.\.venv\Scripts\python.exe -m pytest -q` -> 124 passed.
- `python -m operations.project.update_status` -> PASS.
- `python -m operations.project.review_check` -> PASS, including pytest.

Decision:

- Keep automation standard-library only and scoped to project control.

Next step:

- Commit the project automation and control-doc updates as one coherent workflow change.

## 2026-05-18 - goal-empirical-scope-001

Task:

- Define the project goal system, workflow roles, empirical decision markers,
  and automated meta-logic using existing files only.

Files changed:

- `AGENTS.md`
- `GOAL.md`
- `docs/project/TOOL_USAGE.md`
- `docs/research/EVENT_SELECTION.md`
- `docs/research/WHALE_METHOD.md`
- `docs/research/RESEARCH_SPEC.md`
- `operations/project/review_check.py`
- `tests/test_project_automation.py`

Tests:

- `.\.venv\Scripts\python.exe -m pytest -q` -> 127 passed.
- `python -m operations.project.update_status` -> PASS.

Decision:

- Use existing files only for the goal system, research decision markers, and
  meta-model. Keep thesis runtime agents deferred.

Next step:

- Finalize H2 event selection and window specification before CAR code.

## 2026-05-18 - goal-empirical-scope-001

Task:

- Finalize H2 windows, curate and load canonical event seed rows, and add the
  first deterministic H2 event-window baseline.

Files changed:

- `docs/research/EVENT_SELECTION.md`
- `data/events_timeline_seed.csv`
- `operations/tools/load_events.py`
- `tests/test_event_catalog.py`
- `operations/analysis/event_study.py`
- `tests/test_event_study.py`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_event_catalog.py -q` -> 6 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_event_study.py -q` -> 5 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 132 passed.
- `python -m operations.tools.load_events` -> inserted 7, then updated 7 on rerun.
- `python -m operations.tools.event_catalog_audit` -> no duplicate canonical events and no invalid dates.

Decision:

- Use daily H2 windows for the current daily Polymarket price dataset.
- Keep intraday windows out of scope until intraday data are added and validated.

Next step:

- Generate H2 event-window result artifacts from the curated catalog and daily
  price series.

## 2026-05-18 - goal-empirical-scope-001

Task:

- Advance the active project goal from empirical scope definition to
  deterministic H2 event-window output generation.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  134 passed.

Decision:

- Treat the tracked curated seed CSV as the default event source for the first
  H2 output generator.

Next step:

- Implement the deterministic H2 output runner and generated CSV artifacts.

## 2026-05-18 - goal-empirical-scope-001

Task:

- Generate deterministic H2 event-window output CSVs from curated seed events
  and daily Polymarket prices.

Files changed:

- `operations/analysis/run_h2_event_windows.py`
- `tests/test_h2_event_window_runner.py`
- `data/results/h2_event_window_rows.csv`
- `data/results/h2_event_window_summary.csv`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_event_study.py tests/test_h2_event_window_runner.py -q` -> 11 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 140 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  140 passed.

Decision:

- Keep H2 output generation file-based for now; database persistence into
  `analysis_summaries` remains a later reviewed step.

Next step:

- Review the H2 output CSV shape and decide whether to persist compact H2
  summaries into `analysis_summaries`.

## 2026-05-18 - goal-empirical-scope-001

Task:

- Review the H2 output CSV shape and document the persistence decision.

Files changed:

- `docs/research/EVENT_SELECTION.md`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.tools.event_catalog_audit` -> PASS,
  27 rows, no duplicate canonical events, no invalid dates.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  140 passed.
- `.\.venv\Scripts\python.exe -m operations.project.review_check` -> PASS,
  140 passed.

Decision:

- Accept the H2 row-level CSV as the calculation trace and the H2 summary CSV
  as the compact thesis-facing result shape.
- Persist compact H2 summaries into `analysis_summaries` later; keep full
  row-level traces file-based.

Next step:

- Implement deterministic, idempotent H2 summary persistence into
  `analysis_summaries`.

## 2026-05-18 - goal-h2-summary-persistence-001

Task:

- Persist reviewed compact H2 event-window summaries into `analysis_summaries`.

Files changed:

- `operations/analysis/persist_h2_summaries.py`
- `tests/test_h2_summary_persistence.py`
- `docs/research/EVENT_SELECTION.md`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_h2_summary_persistence.py -q` -> 5 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 145 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.persist_h2_summaries` -> inserted 14, then deleted 14 and inserted 14 on rerun.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  145 passed.
- `.\.venv\Scripts\python.exe -m operations.project.review_check` -> PASS,
  145 passed.

Decision:

- Store one compact H2 summary record per event/window in
  `analysis_summaries`.
- Keep full row-level H2 traces file-based under `data/results/`.
- Advance the active goal to H3 wallet-tier method selection, not H3 code.

Next step:

- Select and document the H3 wallet-tier method before implementing wallet
  classification, lead-lag, or Granger analysis.

## 2026-05-18 - goal-h3-tier-method-001

Task:

- Select the H3 wallet-tier method before wallet classification code.

Files changed:

- `docs/research/WHALE_METHOD.md`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  145 passed.
- `.\.venv\Scripts\python.exe -m operations.project.review_check` -> PASS,
  145 passed and `h3_tier_status=selected`.

Decision:

- Use wallet-level cumulative observed `amount_usd` percentiles as the primary
  H3 tier method.
- Assign ties at percentile boundaries to the higher tier.
- Keep `trade_count` and `max_trade_amount_usd` as diagnostics, not primary
  tier fields.

Next step:

- Implement deterministic wallet distribution inventory for H3 tiering.

## 2026-05-18 - goal-h3-wallet-distribution-inventory-001

Task:

- Generate deterministic H3 wallet distribution inventory metadata.

Files changed:

- `operations/analysis/wallet_distribution_inventory.py`
- `tests/test_wallet_distribution_inventory.py`
- `data/results/h3_wallet_distribution_inventory.json`
- `docs/research/WHALE_METHOD.md`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_wallet_distribution_inventory.py -q` -> 5 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 150 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.wallet_distribution_inventory` -> 25113 trade rows and 3006 wallets.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  150 passed.
- `.\.venv\Scripts\python.exe -m operations.project.review_check` -> PASS,
  150 passed.

Decision:

- Write compact distribution metadata to
  `data/results/h3_wallet_distribution_inventory.json`.
- Do not output raw wallet address lists.
- Keep BUY-only and minimum observed amount as source-filter metadata, not tier
  definitions.

Next step:

- Implement deterministic H3 wallet tier classification from the selected
  percentile method.

## 2026-05-18 - goal-h3-wallet-tier-classification-001

Task:

- Classify observed wallets into deterministic H3 distribution tiers.

Files changed:

- `operations/analysis/classify_wallet_tiers.py`
- `tests/test_wallet_tier_classification.py`
- `data/results/h3_wallet_tiers.csv`
- `data/results/h3_wallet_tiers_metadata.json`
- `docs/research/WHALE_METHOD.md`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_wallet_tier_classification.py -q` -> 4 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 154 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.classify_wallet_tiers` -> 3006 wallets classified.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  154 passed.
- `.\.venv\Scripts\python.exe -m operations.project.review_check` -> PASS,
  154 passed.

Decision:

- Store wallet-level tier assignments in `data/results/h3_wallet_tiers.csv` for
  deterministic H3 timing inputs.
- Keep metadata compact in `data/results/h3_wallet_tiers_metadata.json`.
- Do not run lead-lag or Granger analysis in this step.

Next step:

- Prepare deterministic tiered wallet activity series by joining wallet tiers
  back to observed trade rows.

## 2026-05-18 - goal-h3-tiered-activity-series-001

Task:

- Prepare deterministic H3 tiered daily wallet activity series.

Files changed:

- `operations/analysis/tiered_wallet_activity.py`
- `tests/test_tiered_wallet_activity.py`
- `data/results/h3_tiered_wallet_activity_daily.csv`
- `data/results/h3_tiered_wallet_activity_metadata.json`
- `docs/research/WHALE_METHOD.md`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_tiered_wallet_activity.py -q` -> 6 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 160 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.tiered_wallet_activity` -> 1236 daily tier rows.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  160 passed.
- `.\.venv\Scripts\python.exe -m operations.project.review_check` -> PASS,
  160 passed.

Decision:

- Produce a complete daily tier panel with zero rows for tier-days without
  observed activity.
- Keep wallet addresses out of the daily activity output.
- Do not compute Granger statistics or make causal claims in this step.

Next step:

- Compute descriptive H3 lead-time histograms from curated events and the
  tiered activity series.

## 2026-05-18 - goal-h3-lead-time-histograms-001

Task:

- Compute and review descriptive H3 lead-time histograms.

Files changed:

- `operations/analysis/h3_lead_time_histograms.py`
- `tests/test_h3_lead_time_histograms.py`
- `data/results/h3_lead_time_event_rows.csv`
- `data/results/h3_lead_time_histograms.csv`
- `data/results/h3_lead_time_histograms_metadata.json`
- `docs/research/WHALE_METHOD.md`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_h3_lead_time_histograms.py tests/test_tiered_wallet_activity.py -q` -> 13 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 167 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.h3_lead_time_histograms` -> 420 event rows and 60 histogram rows.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  167 passed.

Decision:

- Accept the H3 lead-time output shape for the first daily descriptive timing
  baseline.
- Keep H3 timing CSV outputs file-based until the Granger result shape is
  stable and reviewed.
- Advance the active goal to deterministic daily lead-lag and Granger tests.

Next step:

- Compute deterministic H3 lead-lag correlations and Granger baseline outputs
  from daily tiered activity and Polymarket daily price changes.

## 2026-05-18 - goal-h3-granger-baseline-001

Task:

- Compute deterministic H3 lead-lag correlations and Granger baseline outputs.

Files changed:

- `operations/analysis/h3_granger_baseline.py`
- `tests/test_h3_granger_baseline.py`
- `data/results/h3_lead_lag_correlations.csv`
- `data/results/h3_granger_results.csv`
- `data/results/h3_granger_metadata.json`
- `docs/research/WHALE_METHOD.md`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_h3_granger_baseline.py tests/test_h3_lead_time_histograms.py -q` -> 13 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 173 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.h3_granger_baseline` -> 32 correlation rows and 28 Granger rows.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  173 passed.

Decision:

- Use daily Polymarket price changes as the H3 target measure.
- Use daily differences of `log1p(total_amount_usd)` by wallet tier as the
  first activity measure.
- Keep all Granger wording limited to predictive timing diagnostics under
  model assumptions.

Next step:

- Review H3 Granger outputs and interpretation limits before thesis-facing
  conclusions or interpretation-layer work.

## 2026-05-18 - goal-h3-granger-review-001

Task:

- Review H3 Granger baseline outputs before thesis interpretation.

Files changed:

- `docs/research/WHALE_METHOD.md`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  173 passed.

Decision:

- Accept the H3 lead-lag and Granger output shape for the first deterministic
  daily baseline.
- Keep full H3 timing and Granger outputs as CSV artifacts for now.
- Persist compact H3 summaries only in a later tested commit after the summary
  payload is specified.
- Require multiple-testing and sensitivity review before strong thesis
  conclusion wording.

Next step:

- Review H1, H2, and H3 deterministic baseline outputs as one empirical
  package before thesis export work.

## 2026-05-19 - goal-empirical-baseline-review-001

Task:

- Review H1, H2, and H3 deterministic baseline outputs as one empirical
  package before thesis export.

Files changed:

- `docs/research/RESEARCH_SPEC.md`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest -q` -> 173 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS.
- `.\.venv\Scripts\python.exe -m operations.project.review_check` -> PASS.

Decision:

- Accept H1-H3 as the first deterministic empirical baseline package.
- Treat H1 Brier, H2 daily event windows, and H3 daily timing diagnostics as
  thesis-ready baseline shapes.
- Keep RCP, intraday claims, strong H3 causal wording, and ML/agent/MCP layers
  out of scope.
- Do not persist compact H3 summaries until a tested summary payload is
  specified.

Next step:

- Prepare compact, traceable H1-H2-H3 result summary tables for thesis
  drafting.

## 2026-05-19 - goal-thesis-result-summaries-001

Task:

- Align thesis methodology, literature intake, result summaries, and strategy
  agent prototype architecture.

Files changed:

- `docs/research/RESEARCH_SPEC.md`
- `ARCHITECTURE_DECISIONS.md`
- `ROADMAP.md`
- `GOAL.md`
- `.gitignore`
- `data/literature/literature_index.csv`
- `docs/research/LITERATURE_MAP.md`
- `operations/analysis/thesis_result_summaries.py`
- `tests/test_thesis_result_summaries.py`
- `data/results/thesis_h1_summary.csv`
- `data/results/thesis_h2_summary.csv`
- `data/results/thesis_h3_summary.csv`
- `data/results/thesis_result_summary_metadata.json`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `operations/project/review_check.py`
- `tests/test_project_automation.py`
- `directives/roles/reviewer.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_thesis_result_summaries.py -q` -> 5 passed.
- `.\.venv\Scripts\python.exe -m pytest tests/test_project_automation.py -q` -> 17 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 181 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.thesis_result_summaries` -> H1 9 rows, H2 15 rows, H3 13 rows.
- `.\.venv\Scripts\python.exe -m operations.project.review_check` -> PASS.

Decision:

- Operationalise informationelle Effizienz through deterministic H1, H2, and
  H3 proxy tests.
- Treat the strategy component as a backtested research prototype within the
  thesis, not as live trading.
- Treat future agents as signal generators whose hypotheses are validated by
  Python backtests.
- Keep Perplexity as discovery input only until local papers are indexed and
  reviewed.

Next step:

- Import downloaded Perplexity/PDF literature sources locally and index them in
  `data/literature/literature_index.csv`.

## 2026-05-19 - goal-literature-intake-001

Task:

- Verify that the thesis-goal, literature-intake, strategy-agent, and
  backtest-prototype alignment plan is already implemented and current.

Files changed:

- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS.
- `.\.venv\Scripts\python.exe -m operations.project.review_check` -> 181 passed
  through the project guardrail check.
- `.\.venv\Scripts\python.exe -m operations.project.commit_plan` -> no
  unstaged file changes detected before the status/work-log refresh.

Decision:

- No additional architecture files are needed for this plan.
- The current active goal remains literature intake and source indexing.
- Do not invent literature rows; wait for actual local PDFs or Perplexity
  exports before filling `data/literature/literature_index.csv`.

Next step:

- Index the downloaded literature sources in
  `data/literature/literature_index.csv`.

## 2026-05-19 - goal-literature-intake-001

Task:

- Index the local Zotero Polymarket folder as a RAG-ready literature source map.

Files changed:

- `ARCHITECTURE_DECISIONS.md`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `data/literature/literature_index.csv`
- `docs/research/LITERATURE_MAP.md`
- `docs/project/WORK_LOG.md`

Tests:

- CSV validation check -> 9 indexed sources, no missing required mapping fields.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> 181
  passed through the project status run.

Decision:

- Treat `C:\Users\chole\Zotero\Polymarket` as the current local literature
  source folder.
- Keep all imported Zotero sources as `candidate` until the underlying source
  is reviewed.
- Allow future RAG-style use only through the tracked literature index; do not
  activate embeddings, agents, MCP, or thesis claims from unchecked sources.

Next step:

- Read and synthesize indexed sources into thesis-methodology notes with
  `source_id` references.

## 2026-05-19 - goal-literature-intake-001

Task:

- Create an initial thesis-methodology synthesis from indexed Zotero sources.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `data/literature/literature_index.csv`
- `docs/research/LITERATURE_MAP.md`
- `docs/project/WORK_LOG.md`

Tests:

- Literature CSV validation -> 9 rows, 5 `skimmed`, 4 `candidate`, no missing
  required fields.

Decision:

- Use skimmed arXiv, SSRN, and local HTML sources to frame H1-H3 and the
  strategy prototype.
- Keep remaining unverified local PDFs as `candidate`.
- Do not treat industry articles or AI-assisted articles as academic evidence.
- Keep RAG-style use index-bound and inactive until a future reviewed retrieval
  layer is specified.

Next step:

- Verify the remaining local PDFs and add source-level notes before citation.

## 2026-05-19 - goal-literature-intake-001

Task:

- Review remaining Zotero PDF sources and advance the active goal.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `data/literature/literature_index.csv`
- `docs/research/LITERATURE_MAP.md`
- `docs/project/WORK_LOG.md`

Tests:

- Literature CSV validation -> 9 rows, 7 `skimmed`, 1 `candidate`, 1
  `rejected`, no missing required fields.

Decision:

- `zotero_poly_005` is Robin Hanson's prediction-market insider-trading paper
  and is useful only for conceptual/legal H3 framing.
- `zotero_poly_007` is Pavel Rezabek's Charles University Polymarket diploma
  thesis and is useful for volatility, convergence, and bias framing.
- `zotero_poly_004` is rejected for thesis use because the local `EMH.pdf`
  could not be verified.

Next step:

- Draft the thesis methodology outline using deterministic outputs and indexed
  literature sources.

## 2026-05-19 - goal-methodology-outline-001

Task:

- Draft the literature-backed thesis methodology outline.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `docs/research/RESEARCH_SPEC.md`
- `docs/project/WORK_LOG.md`

Tests:

- Documentation-only change; project checks run after status refresh.

Decision:

- Structure the thesis methodology around H1 forecast quality, H2 daily
  event-window response, H3 wallet-tier timing diagnostics, and a separate
  historical strategy research prototype.
- Use deterministic artifacts as empirical evidence and indexed literature as
  motivation/context.
- Keep RCP, intraday H2, H3 causal wording, ML, agents, MCP, and live trading
  outside the current empirical method.

Next step:

- Add a canonical EMH literature source to replace the rejected local
  `EMH.pdf`.

## 2026-05-19 - goal-canonical-emh-source-001

Task:

- Add a canonical EMH source for thesis citation planning.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `data/literature/literature_index.csv`
- `docs/research/LITERATURE_MAP.md`
- `docs/research/RESEARCH_SPEC.md`
- `docs/project/WORK_LOG.md`

Tests:

- Literature CSV validation -> 10 rows, 8 `skimmed`, 1 `candidate`, 1
  `rejected`, no missing required fields.

Decision:

- Keep rejected local `EMH.pdf` non-citable.
- Add `lit_emh_001` for Fama's 1970 efficient capital markets review.
- Use EMH theory to frame the research question and proxy tests, not to assume
  that Polymarket is efficient.

Next step:

- Plan thesis-facing tables and figures from deterministic result artifacts.

## 2026-05-19 - goal-thesis-tables-figures-plan-001

Task:

- Prepare the thesis-facing tables and figures plan.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `docs/research/RESEARCH_SPEC.md`
- `docs/project/WORK_LOG.md`

Tests:

- Documentation-only change; project checks run after status refresh.

Decision:

- Core thesis tables are ready from existing H1-H2-H3 summary artifacts.
- Existing H1 reliability figure is ready.
- H2 movement, H3 tier distribution, H3 lead-time, and H3 diagnostic figures
  are optional future artifacts generated only from existing result files.
- RCP, intraday, wallet-address-level, and strategy PnL figures remain blocked
  or deferred.

Next step:

- Generate thesis-ready result figures from existing deterministic artifacts.

## 2026-05-19 - goal-thesis-figures-001

Task:

- Generate thesis-ready H2 and H3 figures from existing deterministic result
  artifacts.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `docs/research/RESEARCH_SPEC.md`
- `docs/project/WORK_LOG.md`
- `operations/analysis/thesis_figures.py`
- `tests/test_thesis_figures.py`
- `data/results/thesis_h2_event_window_car.png`
- `data/results/thesis_h3_wallet_tier_counts.png`
- `data/results/thesis_h3_lead_time_amount.png`
- `data/results/thesis_h3_granger_pvalues.png`
- `data/results/thesis_figures_metadata.json`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_thesis_figures.py -q` -> 2
  passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.thesis_figures` -> 4
  PNG figures and metadata generated.

Decision:

- Generate only visualisations from existing H2/H3 result artifacts.
- Do not calculate new statistics or alter empirical outputs.
- Keep figure interpretations bound to the existing daily-window, BUY-only,
  non-causal, and multiple-testing caveats.

Next step:

- Draft the thesis results narrative skeleton from the deterministic tables and
  figures.

## 2026-05-19 - goal-thesis-results-narrative-001

Task:

- Draft the thesis results narrative skeleton from existing deterministic H1,
  H2, and H3 result artifacts.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `docs/research/RESEARCH_SPEC.md`
- `docs/project/WORK_LOG.md`

Tests:

- Documentation-only change; project checks run after status refresh.

Decision:

- Explain the results chapter through four bounded blocks: H1 forecast quality,
  H2 daily event-window response, H3 wallet-tier timing diagnostics, and the
  strategy prototype boundary.
- Each block states what was investigated, how the result was derived, which
  artifacts to cite, allowed interpretation, required caution, and further
  investigations.
- Keep RCP, intraday H2, causal insider wording, live trading, and profit
  guarantees blocked.

Next step:

- Define the deterministic strategy prototype specification before any
  backtest, agent, or MCP implementation.

## 2026-05-19 - goal-strategy-prototype-spec-001

Task:

- Define the deterministic strategy prototype specification at the
  documentation level.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/project/WORK_LOG.md`

Tests:

- Documentation-only change; project checks run after status refresh.

Decision:

- Treat the first strategy prototype as a historical Python backtest design,
  not an agent or live-trading system.
- Candidate signal families are H1 forecast disagreement, H2 event
  follow-through, H3 wallet timing, and a later combined-summary signal.
- The first baseline recommendation is a simple H3-derived daily timing
  backtest because existing H3 artifacts already provide tier-level daily
  activity and diagnostic outputs.
- Future `SignalSpec`, `BacktestConfig`, and `BacktestResult` fields must be
  specified before strategy code exists.

Next step:

- Prepare Overleaf-ready results chapter prose from the accepted narrative
  skeleton.

## 2026-05-19 - goal-overleaf-results-prose-001

Task:

- Prepare Overleaf-ready results chapter prose from existing deterministic H1,
  H2, and H3 artifacts.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `docs/research/RESEARCH_SPEC.md`
- `docs/project/WORK_LOG.md`

Tests:

- Documentation-only change; project checks run after status refresh.

Decision:

- Draft German thesis-facing prose for the chapter opening, H1, H2, H3, the
  strategy-prototype bridge, and the interim conclusion.
- Include concrete values only from existing summary artifacts.
- Keep all claims bounded: H1 is forecast quality, H2 is daily event-window
  response, H3 is wallet-tier timing diagnostics, and strategy work remains a
  future historical backtest.

Next step:

- Plan the first deterministic strategy backtest baseline before writing any
  implementation code.

## 2026-05-19 - goal-strategy-backtest-plan-001

Task:

- Plan the first deterministic strategy backtest baseline before implementation.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/project/WORK_LOG.md`

Tests:

- Documentation-only change; project checks run after status refresh.

Decision:

- Select `h3_top_1pct_lag1_daily_timing_baseline` as the first minimal
  strategy baseline.
- Use previous-day `tier_1_top_1pct` activity change to avoid lookahead.
- Estimate the activity threshold from the chronological training split only
  and evaluate thesis-facing performance on the final split.
- Require explicit costs, slippage, position limits, benchmarks, drawdown,
  output metadata, and no-LLM/no-agent/no-MCP declarations.

Next step:

- Implement the deterministic H3 strategy backtest baseline in Python.

## 2026-05-20 - legacy-scan-before-strategy-backtest

Task:

- Scan the repository for legacy and stale architecture content before
  continuing with the strategy backtest implementation.

Files changed:

- `legacy/audits/LEGACY_SCAN_2026-05-20.md`
- `docs/legacy_inventory.md`
- `docs/project/WORK_LOG.md`

Tests:

- Documentation-only scan; project checks run after status refresh.

Decision:

- Create a separate legacy audit area instead of moving active files
  immediately.
- Classify `.planning/**`, old changelog output, old summary output, and active
  single-agent modules as the highest-risk legacy surfaces.
- Do not move active agent modules yet because current tests and imports still
  depend on them.

Next step:

- Decide whether to first archive `.planning/**` or hard-guard the remaining
  single-agent modules before implementing the H3 strategy backtest.

## 2026-05-20 - legacy-cleanup-after-scan

Task:

- Move currently unused legacy files into `legacy/` and guard active
  single-agent entry points.

Files changed:

- `.planning/**` -> `legacy/planning/.planning/**`
- `logs/changelog/**` -> `legacy/changelog/**`
- `data/summaries.json` -> `legacy/data/summaries.json`
- `directives/roles/*.md` -> `legacy/deferred_prompts/roles/*.md`
- `operations/agents/market_agent.py`
- `operations/agents/sentiment_agent.py`
- `operations/agents/whale_agent.py`
- `operations/project/review_check.py`
- `tests/test_market_agent.py`
- `tests/test_sentiment_agent.py`
- `tests/test_whale_agent.py`
- `tests/test_project_automation.py`
- `docs/legacy_inventory.md`
- `legacy/audits/LEGACY_SCAN_2026-05-20.md`

Tests:

- Run after cleanup before stopping work.

Decision:

- Keep only runtime guards in active single-agent modules.
- Preserve old Pydantic AI implementations and prompts in `legacy/`.
- Leave `directives/methodology.md` and `directives/coding_standards.md`
  active because they are support instructions, not runtime-agent prompts.

Next step:

- Continue with the deterministic H3 strategy backtest baseline after cleanup
  checks pass.

## 2026-05-20 - politics-geo-anomaly-monitor-pivot

Task:

- Pivot the active strategy track from immediate backtest implementation to a
  politics/geopolitics anomaly-monitor specification.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `ARCHITECTURE_DECISIONS.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`
- `docs/research/RESEARCH_SPEC.md`
- `docs/research/LITERATURE_MAP.md`
- `data/literature/literature_index.csv`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.project.update_status`
- Result: `172 passed in 12.48s`

Decision:

- Treat the next prototype as a Polymarket politics/geopolitics anomaly
  monitor, not as a live-trading or immediate strategy-backtest implementation.
- Use the existing seven US-election events as the first historical validation
  bed.
- Index the local Polybench PDF as a candidate source only; it needs review
  before it can support thesis-facing claims.

Next step:

- Review the anomaly-monitor specification and then plan the first
  deterministic historical anomaly output.

## 2026-05-20 - historical-anomaly-output-goal

Task:

- Advance the active goal from anomaly-monitor specification to the first
  deterministic historical anomaly output.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.project.update_status`
- Result: `172 passed in 5.10s`

Decision:

- Use the existing seven curated US-election events as the first historical
  validation bed.
- Keep the first implementation file-based and deterministic.
- Leave Kalshi, near-real-time collection, agents, MCP, and strategy backtests
  deferred.

Next step:

- Implement the historical event-centred anomaly output module and tests.

## 2026-05-20 - historical-politics-geo-anomaly-output

Task:

- Implement the first deterministic historical politics/geo anomaly output.

Files changed:

- `operations/analysis/h3_event_wallet_anomalies.py`
- `tests/test_h3_event_wallet_anomalies.py`
- `data/results/h3_event_wallet_anomaly_rows.csv`
- `data/results/h3_event_wallet_anomaly_summary.csv`
- `data/results/h3_event_wallet_anomaly_metadata.json`
- `GOAL.md`
- `ROADMAP.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_h3_event_wallet_anomalies.py -q`
- Result: `6 passed`
- `.\.venv\Scripts\python.exe -m pytest -q`
- Result: `178 passed in 5.20s`
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
- Result: `178 passed in 6.40s`

Decision:

- Use baseline window `[-30d, -8d]` and event window `[-1d, +3d]`.
- Score four descriptive anomaly families: market move, wallet-tier amount,
  active-wallet count, and top-tier concentration.
- Keep the output file-based and descriptive; no database write, no agents,
  no MCP, no RCP, and no order sending.

Next step:

- Review the output shape and decide whether v2 should be a near-real-time
  collector contract, an alert-threshold review, or a backtest validation
  contract.

## 2026-05-20 - historical-anomaly-output-review

Task:

- Review the historical anomaly outputs, interpret the result, generate a
  simple thesis-facing figure, and select the next v2 monitor direction.

Files changed:

- `AGENTS.md`
- `GOAL.md`
- `ROADMAP.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`
- `docs/research/RESEARCH_SPEC.md`
- `operations/analysis/thesis_figures.py`
- `tests/test_thesis_figures.py`
- `data/results/thesis_h3_event_wallet_anomalies.png`
- `data/results/thesis_figures_metadata.json`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_thesis_figures.py -q`
- Result: `2 passed`
- `.\.venv\Scripts\python.exe -m operations.analysis.thesis_figures`
- Result: generated `thesis_h3_event_wallet_anomalies.png`
- `.\.venv\Scripts\python.exe -m pytest -q`
- Result: `178 passed in 5.57s`
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
- Result: `178 passed in 8.40s`

Decision:

- Accept the historical anomaly output shape as a descriptive daily monitor
  diagnostic.
- Interpret the strongest current cluster as Biden withdrawal, with 30 anomaly
  days across monitored families.
- Set the next v2 direction to near-real-time monitor contract specification,
  before backtest validation or agent/MCP activation.

Next step:

- Specify the near-real-time politics/geo monitor v2 contract.

## 2026-05-20 - goal-monitor-v2-contract-001

Task:

- Specify the near-real-time Polymarket politics/geo anomaly monitor v2
  contract before implementation.

Files changed:

- `ARCHITECTURE_DECISIONS.md`
- `GOAL.md`
- `ROADMAP.md`
- `docs/research/RESEARCH_SPEC.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  178 passed.

Decision:

- Define v2 as a Polymarket-first, read-only, robust-score-based anomaly
  monitor contract.
- Specify watchlist inputs, market snapshots, wallet-tier snapshots,
  event-candidate review states, alert levels, persistence rules, and future
  output files.
- Keep live collection, agents, MCP, ML, order execution, RCP probability use,
  and profit claims out of scope.

Next step:

- Implement a deterministic v2 snapshot prototype using recorded or mocked
  inputs before any live collector.

## 2026-05-20 - goal-monitor-v2-snapshot-prototype-001

Task:

- Implement the deterministic monitor v2 snapshot prototype.

Files changed:

- `operations/analysis/monitor_v2_snapshot.py`
- `tests/test_monitor_v2_snapshot.py`
- `data/results/monitor_v2_alert_rows.csv`
- `data/results/monitor_v2_alert_summary.csv`
- `data/results/monitor_v2_metadata.json`
- `GOAL.md`
- `ROADMAP.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_monitor_v2_snapshot.py -q`
  -> 8 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_snapshot`
  -> 124 rows, 12 alerts, 4 summary rows.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 186 passed.

Decision:

- Keep the first v2 implementation on mocked or recorded snapshots only.
- Use completed prior observations for robust rolling scores and percentile
  ranks.
- Treat the current output as a contract prototype, not live monitoring or a
  trading signal.
- Review percentile-only `watch` behaviour before adding real replay data.

Next step:

- Review the monitor v2 snapshot output shape and threshold behaviour.

## 2026-05-20 - goal-monitor-v2-snapshot-review-001

Task:

- Review deterministic monitor v2 snapshot prototype outputs.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`
- `docs/project/WORK_LOG.md`

Tests:

- Output inspection of `data/results/monitor_v2_alert_rows.csv`.
- Output inspection of `data/results/monitor_v2_alert_summary.csv`.
- Output inspection of `data/results/monitor_v2_metadata.json`.

Decision:

- Accept the row and summary column shape for the first deterministic monitor
  v2 snapshot prototype.
- Keep the output as descriptive, mocked, aggregate-only, and not a live
  monitoring or trading signal.
- Treat percentile-only `watch` alerts as too sensitive for real replay data
  until deterministic threshold sensitivity is reviewed.

Next step:

- Compare current and stricter monitor v2 alert threshold rules before adding
  real replay data or live collection.

## 2026-05-20 - goal-monitor-v2-threshold-sensitivity-001

Task:

- Select and implement the monitor v2 threshold rule.

Files changed:

- `operations/analysis/monitor_v2_snapshot.py`
- `tests/test_monitor_v2_snapshot.py`
- `data/results/monitor_v2_alert_rows.csv`
- `data/results/monitor_v2_alert_summary.csv`
- `data/results/monitor_v2_metadata.json`
- `GOAL.md`
- `ROADMAP.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_monitor_v2_snapshot.py -q`
  -> 9 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_snapshot`
  -> 124 rows, 12 alerts, 4 summary rows.

Decision:

- Select Rule C: combined-family confirmation.
- Downgrade isolated single-family percentile-only `watch` rows to `info`.
- Keep `critical` restricted to market movement plus wallet or concentration
  anomaly plus reviewed event context.
- The current mock output still has 8 `watch` and 4 `critical` rows because the
  elevated mock timestamps contain all four families simultaneously.

Next step:

- Build deterministic historical replay snapshots from existing H2/H3
  artifacts before live collection.

## 2026-05-20 - goal-monitor-v2-historical-replay-snapshots-001

Task:

- Build deterministic monitor v2 historical replay snapshots from existing
  local artifacts.

Files changed:

- `operations/analysis/monitor_v2_historical_replay.py`
- `tests/test_monitor_v2_historical_replay.py`
- `data/results/monitor_v2_historical_replay_snapshots.csv`
- `data/results/monitor_v2_historical_replay_alert_rows.csv`
- `data/results/monitor_v2_historical_replay_alert_summary.csv`
- `data/results/monitor_v2_historical_replay_metadata.json`
- `GOAL.md`
- `ROADMAP.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_monitor_v2_historical_replay.py tests/test_monitor_v2_snapshot.py -q`
  -> 14 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_historical_replay`
  -> 3040 snapshots, 3040 alert rows, 512 non-`none` alerts, 10 summary rows.

Decision:

- Use existing curated events, daily Polymarket prices, and aggregate
  wallet-tier activity to build the first daily replay panel.
- Keep the replay file-based and aggregate-only.
- Keep Rule C as the alert rule.
- The first replay produces `info`, `watch`, and `high` rows, but no
  `critical` rows under the strict event-context rule.

Next step:

- Review historical replay outputs, especially zero `critical` rows and
  whether event proximity should be same-day only or a small window.

## 2026-05-20 - goal-monitor-v2-historical-replay-review-001

Task:

- Review monitor v2 historical replay outputs and set the next daily
  event-proximity sensitivity goal.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  192 passed.
- `.\.venv\Scripts\python.exe -m operations.project.review_check` -> PASS,
  192 passed.
- `.\.venv\Scripts\python.exe -m operations.project.commit_plan` -> grouped
  project-control docs and research docs, no risky mixed changes.

Decision:

- Accept the historical replay output shape as the first daily monitor v2
  replay baseline.
- Interpret zero `critical` rows as strict same-day event-context behaviour,
  not as an implementation defect.
- Keep `critical` strict and test a small event-proximity window before live
  collection.
- Evaluate a separate `event_watch` label for reviewed event-proximity wallet
  clusters without market-move confirmation.

Next step:

- Implement deterministic monitor v2 event-proximity sensitivity using existing
  replay artifacts.

## 2026-05-20 - goal-monitor-v2-event-proximity-sensitivity-001

Task:

- Compare same-day monitor v2 event context with a daily `[-1d, +1d]`
  event-proximity window.

Files changed:

- `operations/analysis/monitor_v2_event_proximity_sensitivity.py`
- `tests/test_monitor_v2_event_proximity_sensitivity.py`
- `data/results/monitor_v2_event_proximity_sensitivity_rows.csv`
- `data/results/monitor_v2_event_proximity_sensitivity_summary.csv`
- `data/results/monitor_v2_event_proximity_sensitivity_metadata.json`
- `GOAL.md`
- `ROADMAP.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_monitor_v2_event_proximity_sensitivity.py -q`
  -> 5 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_event_proximity_sensitivity`
  -> 210 rows, 21 summary rows, 0 same-day critical candidates, 6 proximity
  critical candidates, 6 event-watch candidates.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 197 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  197 passed.
- `.\.venv\Scripts\python.exe -m operations.project.review_check` -> PASS,
  197 passed.
- `.\.venv\Scripts\python.exe -m operations.project.commit_plan` -> grouped
  project-control docs, research docs, data files, deterministic analysis, and
  tests; mixed changes accepted as one coherent sensitivity-output commit.

Decision:

- Use `[-1d, +1d]` as the reviewed daily event-context window for replay
  outputs.
- Keep `critical` strict.
- Use `event_watch` as a separate descriptive label for wallet or
  concentration clusters near reviewed events without market-move
  confirmation.

Next step:

- Integrate proximity-aware labels into the historical replay output contract.

## 2026-05-20 - goal-monitor-v2-proximity-alert-labels-001

Task:

- Integrate selected event-proximity labels into the monitor v2 historical
  replay output contract.

Files changed:

- `operations/analysis/monitor_v2_historical_replay.py`
- `operations/analysis/monitor_v2_event_proximity_sensitivity.py`
- `tests/test_monitor_v2_historical_replay.py`
- `data/results/monitor_v2_historical_replay_context_rows.csv`
- `data/results/monitor_v2_historical_replay_metadata.json`
- `data/results/monitor_v2_event_proximity_sensitivity_rows.csv`
- `data/results/monitor_v2_event_proximity_sensitivity_summary.csv`
- `data/results/monitor_v2_event_proximity_sensitivity_metadata.json`
- `GOAL.md`
- `ROADMAP.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_monitor_v2_historical_replay.py tests/test_monitor_v2_event_proximity_sensitivity.py -q`
  -> 10 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_historical_replay`
  -> 3040 snapshots, 3040 alert rows, 512 non-`none` alerts, 10 alert summary
  rows, and 21 context rows.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_event_proximity_sensitivity`
  -> 210 rows, 21 summary rows.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 197 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  197 passed.
- `.\.venv\Scripts\python.exe -m operations.project.review_check` -> PASS,
  197 passed.
- `.\.venv\Scripts\python.exe -m operations.project.commit_plan` -> grouped
  project-control docs, data files, research docs, deterministic analysis, and
  tests; mixed changes accepted as one coherent replay-contract commit.

Decision:

- Keep the original replay alert severities unchanged.
- Add `monitor_v2_historical_replay_context_rows.csv` as the sidecar for
  proximity-aware context labels.
- Keep `critical_proximity_candidate` and `event_watch_candidate` separate.

Next step:

- Validate recorded monitor v2 input files before adding any live collector.

## 2026-05-20 - goal-monitor-v2-recorded-input-validation-001

Task:

- Add deterministic validators for recorded monitor v2 input files.

Files changed:

- `operations/analysis/monitor_v2_input_validation.py`
- `tests/test_monitor_v2_input_validation.py`
- `GOAL.md`
- `ROADMAP.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_monitor_v2_input_validation.py -q`
  -> 8 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 205 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  205 passed.
- `.\.venv\Scripts\python.exe -m operations.project.review_check` -> PASS,
  205 passed.
- `.\.venv\Scripts\python.exe -m operations.project.commit_plan` -> grouped
  project-control docs, research docs, deterministic analysis, and tests; mixed
  changes accepted as one coherent validation-boundary commit.

Decision:

- Validate four recorded input contracts before live collection:
  watchlist, market snapshots, wallet-tier snapshots, and event candidates.
- Keep validation file-based and deterministic.
- Reject wallet addresses in wallet-tier snapshots.
- Require source URLs and related market ids before an event candidate can be
  treated as accepted or market-mapped.

Next step:

- Build recorded monitor v2 input adapters from existing historical artifacts
  and validate the generated files.

## 2026-05-20 - goal-monitor-v2-recorded-input-adapter-001

Task:

- Generate recorded monitor v2 input files from existing historical artifacts
  and validate the generated files.

Files changed:

- `operations/analysis/monitor_v2_recorded_input_adapter.py`
- `tests/test_monitor_v2_recorded_input_adapter.py`
- `data/results/monitor_v2_recorded_watchlist.csv`
- `data/results/monitor_v2_recorded_market_snapshots.csv`
- `data/results/monitor_v2_recorded_wallet_tier_snapshots.csv`
- `data/results/monitor_v2_recorded_event_candidates.csv`
- `data/results/monitor_v2_recorded_input_validation_report.json`
- `data/results/monitor_v2_recorded_inputs_metadata.json`
- `GOAL.md`
- `ROADMAP.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_monitor_v2_recorded_input_adapter.py tests/test_monitor_v2_input_validation.py -q`
  -> 12 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_recorded_input_adapter`
  -> 1 watchlist row, 305 market snapshot rows, 1236 wallet-tier snapshot rows,
  7 event candidate rows, validation status `pass`.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 209 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  209 passed.
- `.\.venv\Scripts\python.exe -m operations.project.review_check` -> PASS,
  209 passed.
- `.\.venv\Scripts\python.exe -m operations.project.commit_plan` -> grouped
  project-control docs, research docs, deterministic analysis, data files, and
  tests; mixed changes accepted as one coherent recorded-input adapter commit.

Decision:

- Generate replay-derived recorded inputs before any live collector exists.
- Use local Polymarket prices, curated seed events, and aggregate H3 tiered
  wallet activity only.
- Keep generated inputs aggregate-only and free of wallet addresses or order
  instructions.

Next step:

- Review recorded monitor v2 input outputs before building a validated-input
  scoring runner.

## 2026-05-20 - goal-monitor-v2-recorded-input-review-001

Task:

- Review monitor v2 recorded input adapter outputs and decide whether the
  recorded file shape is ready for validated-input scoring.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- Direct CSV and JSON inspection of recorded monitor v2 input artifacts.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
- `.\.venv\Scripts\python.exe -m operations.project.review_check`
- `.\.venv\Scripts\python.exe -m operations.project.commit_plan`

Decision:

- Accept the recorded input shape for a deterministic validated-input scoring
  runner.
- Keep the boundary replay-derived, daily, aggregate-only, and file-based.
- Treat wallet-tier snapshots as BUY-side observed aggregate activity and
  event candidates as the seven curated seed events only.

Next step:

- Build the deterministic validated-input scoring runner before any live API,
  WebSocket, agent, MCP, ML, database-write, or order-execution path.

## 2026-05-20 - goal-monitor-v2-validated-input-scoring-runner-001

Task:

- Build and run the deterministic monitor v2 scoring runner for validated
  recorded input files.

Files changed:

- `operations/analysis/monitor_v2_recorded_input_scoring.py`
- `tests/test_monitor_v2_recorded_input_scoring.py`
- `data/results/monitor_v2_recorded_scoring_snapshots.csv`
- `data/results/monitor_v2_recorded_alert_rows.csv`
- `data/results/monitor_v2_recorded_alert_summary.csv`
- `data/results/monitor_v2_recorded_context_rows.csv`
- `data/results/monitor_v2_recorded_scoring_validation_report.json`
- `data/results/monitor_v2_recorded_scoring_metadata.json`
- `GOAL.md`
- `ROADMAP.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_monitor_v2_recorded_input_scoring.py tests/test_monitor_v2_input_validation.py tests/test_monitor_v2_snapshot.py -q`
  -> 21 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_recorded_input_scoring`
  -> 3394 snapshots, 3394 alert rows, 581 non-`none` alerts, 11 summary rows,
  and 21 context rows.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 213 passed.

Decision:

- Score only reviewed recorded input files and validate all inputs before
  scoring.
- Reuse the monitor v2 Rule C scoring implementation.
- Keep event proximity in the context sidecar rather than converting it into
  order or trading instructions.

Next step:

- Review the recorded scoring outputs and decide whether the shape is accepted
  before live collection, MCP, agents, ML, or strategy backtest work.

## 2026-05-20 - goal-monitor-v2-recorded-scoring-review-001

Task:

- Review monitor v2 recorded scoring outputs and generate a simple
  thesis-facing figure.

Files changed:

- `operations/analysis/thesis_figures.py`
- `tests/test_thesis_figures.py`
- `data/results/thesis_monitor_v2_recorded_scoring.png`
- `data/results/thesis_figures_metadata.json`
- `GOAL.md`
- `ROADMAP.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_thesis_figures.py -q`
  -> 2 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.thesis_figures`
  -> generated `thesis_monitor_v2_recorded_scoring.png`.

Decision:

- Accept the recorded scoring output shape as a bounded daily replay monitor
  output.
- Separate direct alert severities from event-proximity context labels.
- Interpret 3 `critical_proximity_candidate` rows and 8
  `event_watch_candidate` rows as descriptive daily-context labels only.

Next step:

- Generate compact bounded monitor-v2 summary artifacts before live collection,
  MCP, agents, ML, or strategy backtest work.

## 2026-05-20 - goal-monitor-v2-bounded-summary-output-001

Task:

- Generate compact bounded monitor-v2 summaries from accepted recorded scoring
  outputs.

Files changed:

- `operations/analysis/monitor_v2_result_summaries.py`
- `tests/test_monitor_v2_result_summaries.py`
- `data/results/monitor_v2_bounded_summary.csv`
- `data/results/monitor_v2_bounded_summary_metadata.json`
- `GOAL.md`
- `ROADMAP.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_monitor_v2_result_summaries.py -q`
  -> 4 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_result_summaries`
  -> 19 bounded summary rows.

Decision:

- Create a compact monitor-v2 summary boundary before any future LLM, MCP,
  agent, live collector, or strategy backtest reads monitor outputs.
- Keep row-level alert files separate and not prompt-facing by default.

Next step:

- Review the bounded monitor-v2 summary shape and decide whether it is
  accepted for future read-only access contracts.

## 2026-05-20 - goal-monitor-v2-bounded-summary-review-001

Task:

- Review bounded monitor-v2 summary outputs and accept the summary boundary.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- Direct review of `data/results/monitor_v2_bounded_summary.csv`.
- Direct review of `data/results/monitor_v2_bounded_summary_metadata.json`.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
- `.\.venv\Scripts\python.exe -m operations.project.review_check`

Decision:

- Accept `monitor_v2_bounded_summary.csv` as the default monitor-v2
  interpretation surface.
- Keep row-level alert files deterministic and file-based, but not
  prompt-facing by default.
- Require a read-only access contract before MCP, agents, live collection, or
  strategy backtest work.

Next step:

- Specify the read-only monitor-v2 summary access contract.

## 2026-05-20 - goal-monitor-v2-readonly-summary-access-contract-001

Task:

- Specify a docs-only read-only access contract for monitor-v2 bounded
  summaries.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.project.update_status`
- `.\.venv\Scripts\python.exe -m operations.project.review_check`
- `.\.venv\Scripts\python.exe -m operations.project.commit_plan`

Decision:

- Allow `monitor_v2_bounded_summary.csv`, its metadata, and the
  thesis-facing monitor figure as the default read-only access surface.
- Block raw row-level alert dumps, scoring snapshots, recorded input files,
  direct database reads, wallet-address exports, live collection, and
  execution paths by default.
- Keep MCP, agents, live collection, strategy backtests, and audit-log
  implementation deferred.

Next step:

- Review the read-only monitor-v2 summary access contract and select the next
  phase.

## 2026-05-20 - goal-monitor-v2-readonly-summary-access-review-001

Task:

- Review and accept the monitor-v2 read-only summary access contract.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.project.update_status`
- `.\.venv\Scripts\python.exe -m operations.project.review_check`
- `.\.venv\Scripts\python.exe -m operations.project.commit_plan`

Decision:

- Accept `monitor_v2_bounded_summary.csv` as the default monitor-v2 access
  surface.
- Keep raw row-level alert files, scoring snapshots, recorded input files, and
  direct database reads blocked by default.
- Select automated project guardrail enforcement as the next phase before MCP,
  agents, live collection, or strategy backtest work.

Next step:

- Enforce the monitor-v2 read-only access boundary in project review checks.

## 2026-05-20 - goal-monitor-v2-access-guardrail-checks-001

Task:

- Enforce the monitor-v2 read-only summary access boundary through project
  review checks.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `operations/project/review_check.py`
- `tests/test_project_automation.py`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_project_automation.py -q`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m operations.project.update_status`

Decision:

- Project checks now require the bounded monitor-v2 summary artifacts, enforce
  the 50-row default exposure limit, reject wallet-address exposure, and reject
  raw monitor files in the default allowed-artifact block.
- The read-only access contract is now enforceable before MCP, agents, live
  collection, strategy backtests, or interpretation tooling can be added.

Next step:

- Specify the monitor-v2 live input collection contract as a documentation-only
  step before any collector implementation.

## 2026-05-20 - goal-monitor-v2-live-input-contract-001

Task:

- Specify the monitor-v2 live input collection contract before any live
  collector, API client, WebSocket loop, MCP tool, runtime agent, or strategy
  backtest is implemented.

Files changed:

- `ARCHITECTURE_DECISIONS.md`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.project.review_check --skip-pytest "docs-only contract update; full pytest will run via update_status"`
- `.\.venv\Scripts\python.exe -m operations.project.update_status`

Decision:

- The live-input contract is read-only and replay-first.
- The first live-capable alert-scoring bucket is 15 minutes, while daily
  buckets remain the bridge to current thesis outputs.
- Every future input row must carry UTC timestamp fields, deterministic bucket
  boundaries, source metadata, and validation status.
- Scoring for bucket `t` must use completed prior buckets for the rolling
  baseline and may only use event context available at or before `t`.
- Raw live input files remain source artifacts, not prompt-facing or
  MCP-facing defaults.

Next step:

- Review and accept, revise, or block the live-input collection contract
  before any replay-first input batch prototype is implemented.

## 2026-05-20 - goal-monitor-v2-live-input-contract-review-001

Task:

- Review the monitor-v2 live input collection contract and decide the next
  implementation path.

Files changed:

- `ARCHITECTURE_DECISIONS.md`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.project.review_check --skip-pytest "docs-only live-input contract review; full pytest will run via update_status"`
- `.\.venv\Scripts\python.exe -m operations.project.update_status`

Decision:

- Accept the live-input contract for replay-first implementation planning.
- Keep the first live-capable alert-scoring bucket at 15 minutes, with daily
  buckets as the bridge to current thesis outputs.
- Require UTC timestamp fields, source metadata, deterministic bucket
  boundaries, validation status, and no-lookahead behaviour.
- Block live API collection, WebSocket streaming, MCP, agents, strategy
  backtests, order execution, and trading credentials.

Next step:

- Implement replay-first monitor-v2 live input validators with local mocked or
  fixture files only.

## 2026-05-20 - goal-monitor-v2-live-input-validators-001

Task:

- Implement deterministic replay-first monitor-v2 live input validators.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`
- `operations/analysis/monitor_v2_live_input_validation.py`
- `tests/test_monitor_v2_live_input_validation.py`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_monitor_v2_live_input_validation.py tests/test_monitor_v2_input_validation.py -q`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m operations.project.update_status`

Decision:

- Add local CSV validators for future live-capable watchlist, market snapshot,
  wallet-tier snapshot, and event-candidate inputs.
- Validators enforce UTC-compatible timestamps, bucket boundaries, source
  metadata, price/probability ranges, non-negative counts and amounts,
  accepted event review requirements, and wallet-address exclusion.
- Validators return structured reports and do not call external APIs,
  WebSockets, databases, LLMs, agents, MCP tools, ML systems, or order paths.

Next step:

- Review the validator shape before building a local replay-first input batch
  prototype.

## 2026-05-20 - goal-monitor-v2-live-input-validator-review-001

Task:

- Review replay-first monitor-v2 live input validators and decide the next
  implementation path.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.project.review_check --skip-pytest "docs-only validator review; full pytest will run via update_status"`
- `.\.venv\Scripts\python.exe -m operations.project.update_status`

Decision:

- Accept the validator shape for a local replay-first input batch prototype.
- Validator coverage is sufficient for watchlist rows, market snapshots,
  wallet-tier snapshots, event candidates, timestamp fields, bucket
  boundaries, and wallet-address exclusion.
- Cross-file market consistency should be handled by the local batch
  prototype.
- Live API collection, WebSocket streaming, MCP, agents, strategy backtests,
  order execution, and trading credentials remain blocked.

Next step:

- Build a local replay-first monitor-v2 live input batch prototype from mocked
  or fixture data only.

## 2026-05-20 - goal-monitor-v2-live-input-batch-prototype-001

Task:

- Build a local replay-first monitor-v2 live input batch prototype from mocked
  fixture data.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`
- `operations/analysis/monitor_v2_live_input_batch.py`
- `tests/test_monitor_v2_live_input_batch.py`
- `data/results/monitor_v2_live_watchlist.csv`
- `data/results/monitor_v2_live_market_snapshots.csv`
- `data/results/monitor_v2_live_wallet_tier_snapshots.csv`
- `data/results/monitor_v2_live_event_candidates.csv`
- `data/results/monitor_v2_live_input_validation_report.json`
- `data/results/monitor_v2_live_inputs_metadata.json`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_monitor_v2_live_input_batch.py tests/test_monitor_v2_live_input_validation.py -q`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m operations.project.update_status`

Decision:

- Add a deterministic local fixture batch that writes live-style watchlist,
  market snapshot, wallet-tier snapshot, and event-candidate input files.
- Generated files use closed 15-minute buckets, UTC timestamp fields, source
  metadata, and structured validation metadata.
- The batch validates generated files with the accepted live-input validators
  and checks cross-file market consistency.
- It does not call APIs, WebSockets, databases, LLMs, agents, MCP tools, ML
  systems, order endpoints, or trading credentials.

Next step:

- Review the generated local live input batch output shape before connecting
  the files to deterministic scoring.

## 2026-05-20 - goal-monitor-v2-live-input-batch-review-001

Task:

- Review the local replay-first monitor-v2 live input batch output shape and
  decide whether it is safe to connect to deterministic scoring.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.project.update_status`
- `.\.venv\Scripts\python.exe -m operations.project.review_check`

Decision:

- Accept the generated local live input batch shape for a diagnostic
  deterministic scoring bridge.
- The reviewed batch contains 1 mocked watchlist row, 4 closed 15-minute
  market snapshots, 8 aggregate wallet-tier snapshots, 1 accepted mocked event
  candidate, and validation status `pass`.
- The files remain local source artifacts only and are not prompt-facing,
  MCP-facing, or live-collection outputs.
- Live API/WebSocket collection, runtime agents, MCP, strategy backtests,
  order execution, trading credentials, and profitability claims remain
  blocked.

Next step:

- Build a local monitor-v2 live-input scoring bridge from the validated mocked
  files.

## 2026-05-20 - goal-monitor-v2-live-input-scoring-bridge-001

Task:

- Build a deterministic local monitor-v2 live-input scoring bridge from the
  validated mocked live-style files.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`
- `operations/analysis/monitor_v2_live_input_scoring.py`
- `tests/test_monitor_v2_live_input_scoring.py`
- `data/results/monitor_v2_live_scoring_snapshots.csv`
- `data/results/monitor_v2_live_alert_rows.csv`
- `data/results/monitor_v2_live_alert_summary.csv`
- `data/results/monitor_v2_live_scoring_validation_report.json`
- `data/results/monitor_v2_live_scoring_metadata.json`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_monitor_v2_live_input_scoring.py tests/test_monitor_v2_live_input_batch.py tests/test_monitor_v2_live_input_validation.py -q`
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_live_input_scoring`

Decision:

- Add a deterministic scoring bridge that validates local live-style input
  files, scores closed 15-minute buckets, and writes diagnostic monitor-v2
  snapshots, alert rows, alert summaries, validation report, and metadata.
- The bridge uses only local files, does not call APIs or WebSockets, does not
  write to the database, and does not use LLMs, agents, MCP, ML, or order
  paths.
- The generated fixture output has 35 scoring snapshot rows, 35 alert rows, 9
  summary rows, and 6 non-`none` diagnostic alerts. These are pipeline-shape
  diagnostics, not market evidence.

Next step:

- Review the local live-input scoring output shape before selecting the next
  real-data replay boundary.

## 2026-05-20 - goal-monitor-v2-live-input-scoring-review-001

Task:

- Review the local replay-first monitor-v2 live input scoring bridge output
  shape and decide the next boundary.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.project.update_status`
- `.\.venv\Scripts\python.exe -m operations.project.review_check`

Decision:

- Accept the local live-input scoring output columns, metadata, and event
  no-lookahead annotation rule.
- The output has 35 scoring snapshot rows, 35 alert rows, 9 summary rows, and
  6 non-`none` diagnostic alerts.
- Interpret the 6 alerts as mocked fixture pipeline diagnostics only, not as
  empirical Polymarket evidence or live-readiness evidence.
- Keep live API/WebSocket collection, runtime agents, MCP, strategy backtests,
  order execution, and trading credentials blocked.

Next step:

- Specify the first real-data replay boundary before implementing another
  adapter or collector.

## 2026-05-20 - goal-monitor-v2-real-data-replay-boundary-001

Task:

- Specify the first real-data replay boundary for monitor v2.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.project.update_status`
- `.\.venv\Scripts\python.exe -m operations.project.review_check`

Decision:

- Select `daily_recorded_replay_v1` as the first real-data replay boundary.
- Allowed source artifacts are the existing recorded watchlist, market
  snapshots, wallet-tier snapshots, event candidates, validation report, and
  metadata under `data/results/`.
- Allowed bucket frequency is daily closed replay buckets.
- Production-like interpretation requires the v2 30 prior observations and
  minimum 20 baseline observations rule.
- Live API polling, WebSocket streaming, MCP, runtime agents, strategy
  backtests, order execution, intraday claims, and profitability claims remain
  blocked.

Next step:

- Review whether the existing recorded daily replay/scoring outputs already
  satisfy `daily_recorded_replay_v1`.

## 2026-05-20 - goal-monitor-v2-real-data-replay-boundary-review-001

Task:

- Review existing recorded daily replay/scoring outputs against the selected
  monitor v2 real-data replay boundary.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.project.update_status`
- `.\.venv\Scripts\python.exe -m operations.project.review_check`

Decision:

- Accept that existing recorded daily replay outputs satisfy
  `daily_recorded_replay_v1`.
- Reviewed recorded scoring metadata: validation `pass`, 1 watchlist row, 305
  market snapshot rows, 1236 wallet-tier snapshot rows, 7 event candidates,
  3394 scoring rows, 11 summary rows, and v2 30/20 baseline settings.
- No daily live-style adapter is needed for the current boundary.
- Intraday claims, live API/WebSocket collection, runtime agents, MCP,
  strategy backtests, order execution, and trading credentials remain blocked.

Next step:

- Specify live collector preflight requirements with mocked API/WebSocket
  contracts before any external collection code is attempted.

## 2026-05-22 - goal-polymarket-live-readonly-collector-001

Task:

- Expand the active goal from preflight-only to a read-only Polymarket live
  collector foundation.

Files changed:

- `AGENTS.md`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`

Tests:

- Pending in the implementation steps that follow this documentation update.

Decision:

- Allow real public Polymarket live data collection for monitor v2, but only
  read-only and only through mocked/tested connector boundaries.
- First live-capable bucket is 5 minutes; 1-minute buckets can come later.
- Gamma discovery, CLOB midpoint or market-state endpoints, and Data API trade
  rows are in scope.
- Authenticated user channels, order endpoints, trading credentials, agents,
  MCP, strategy backtests, database writes, and profitability claims remain
  blocked.

Next step:

- Implement mocked collector tests and the read-only collector foundation.

## 2026-05-22 - goal-polymarket-live-readonly-collector-001 implementation

Task:

- Implement the read-only Polymarket live collector foundation, first real
  snapshot, validation, scoring bridge check, and visualisation.

Files changed:

- `AGENTS.md`
- `GOAL.md`
- `ROADMAP.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`
- `operations/collectors/polymarket_readonly.py`
- `operations/analysis/monitor_v2_polymarket_live_figures.py`
- `operations/analysis/monitor_v2_live_input_scoring.py`
- `tests/test_polymarket_readonly_collector.py`
- `tests/test_monitor_v2_polymarket_live_figures.py`
- `tests/test_monitor_v2_live_input_scoring.py`
- `data/results/monitor_v2_polymarket_live_*`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_polymarket_readonly_collector.py tests/test_monitor_v2_polymarket_live_figures.py tests/test_monitor_v2_live_input_validation.py tests/test_monitor_v2_live_input_scoring.py -q` -> 27 passed.
- Full test suite pending after status refresh.

Decision:

- Accept the first read-only public REST collector foundation.
- First live run produced 2 watchlist rows, 4 token midpoint rows, 2 aggregate
  wallet/activity rows, 0 event candidates, validation `pass`, and a simple
  snapshot figure.
- First live scoring bridge produced 8 scoring rows and 0 alerts; all rows are
  `insufficient_baseline`, which is expected with only one closed bucket.
- No wallet-address columns, order instructions, database writes, runtime
  agents, MCP, ML, strategy backtest, or trading credentials were introduced.

Next step:

- Build rolling history collection so repeated closed 5-minute buckets can
  support diagnostic baseline scoring.

## 2026-05-22 - goal-polymarket-live-rolling-history-001

Task:

- Implement bounded read-only Polymarket rolling-history collection, scoring,
  figure generation, and live watchlist filter hardening.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`
- `operations/collectors/polymarket_readonly.py`
- `operations/collectors/polymarket_rolling_history.py`
- `operations/analysis/monitor_v2_live_input_scoring.py`
- `operations/analysis/monitor_v2_polymarket_rolling_figures.py`
- `tests/test_polymarket_readonly_collector.py`
- `tests/test_monitor_v2_live_input_scoring.py`
- `tests/test_polymarket_rolling_history.py`
- `data/results/monitor_v2_polymarket_live_*`
- `data/results/monitor_v2_polymarket_rolling_*`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_polymarket_readonly_collector.py tests/test_polymarket_rolling_history.py tests/test_monitor_v2_live_input_scoring.py tests/test_monitor_v2_polymarket_live_figures.py -q` -> 21 passed.
- Full test suite pending after status refresh.

Decision:

- Accept the bounded rolling-history collector as a local operator path, not a
  background daemon.
- The collector appends closed buckets and deduplicates deterministic keys,
  including long token ids read back from CSV.
- The first clean live run produced 3 watchlist rows, 6 token midpoint rows, 3
  aggregate wallet/activity rows, 12 scoring rows, 0 alerts, and
  `insufficient_baseline`.
- The automatic Gamma watchlist filter was hardened after live discovery
  surfaced noisy category-labelled markets.

Next step:

- Define a curated Polymarket politics/geopolitics watchlist contract before
  interpreting live alerts.

## 2026-05-22 - goal-polymarket-live-watchlist-curation-001

Task:

- Define and implement a local curated Polymarket politics/geopolitics
  watchlist contract before interpreting live alert output.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `data/monitor_v2_curated_watchlist.csv`
- `data/results/monitor_v2_curated_watchlist_validation_report.json`
- `operations/collectors/polymarket_watchlist.py`
- `tests/test_polymarket_watchlist.py`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_polymarket_watchlist.py tests/test_polymarket_readonly_collector.py -q` -> 17 passed.
- Full test suite pending after status refresh.

Decision:

- Accept the curated watchlist contract and validator as the boundary between
  automatic Gamma discovery and thesis-facing monitor interpretation.
- Keep the current 3 auto-discovered rows as `candidate`; the validation
  report has 0 accepted rows and marks them not monitor-ready.
- Accepted rows must include source URL, inclusion reason, reviewer, and
  timezone-aware review timestamp.
- Rejected rows must include an exclusion reason.

Next step:

- Review the current candidates and mark the first accepted, rejected, or
  needs-followup watchlist rows.

## 2026-05-22 - goal-polymarket-live-watchlist-review-001

Task:

- Review the first curated Polymarket politics/geopolitics watchlist rows
  against public Gamma market metadata.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `data/monitor_v2_curated_watchlist.csv`
- `data/results/monitor_v2_curated_watchlist_validation_report.json`

Tests:

- `.\.venv\Scripts\python.exe -m operations.collectors.polymarket_watchlist` -> 3 accepted rows, 0 candidate rows.
- Full test suite pending after status refresh.

Decision:

- Accept the three current rows for monitor-watchlist use only, based on
  official public Gamma metadata and clear politics, leadership, or election
  scope.
- This acceptance does not create thesis event evidence, anomaly evidence,
  signal evidence, or strategy evidence.
- Keep automatic Gamma discovery as candidate discovery, not as the reviewed
  monitor universe.

Next step:

- Integrate accepted curated watchlist rows into the read-only collector.

## 2026-05-22 - goal-polymarket-live-curated-collector-001

Task:

- Integrate the accepted curated Polymarket watchlist into the read-only
  collector and bounded rolling-history path.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `operations/collectors/polymarket_readonly.py`
- `operations/collectors/polymarket_rolling_history.py`
- `operations/analysis/monitor_v2_live_input_scoring.py`
- `tests/test_polymarket_readonly_collector.py`
- `tests/test_polymarket_rolling_history.py`
- `data/results/monitor_v2_polymarket_live_*`
- `data/results/monitor_v2_live_*`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_polymarket_readonly_collector.py tests/test_polymarket_rolling_history.py tests/test_polymarket_watchlist.py -q` -> 23 passed.
- `.\.venv\Scripts\python.exe -m pytest tests/test_polymarket_readonly_collector.py tests/test_polymarket_rolling_history.py tests/test_monitor_v2_live_input_scoring.py -q` -> 22 passed.
- `.\.venv\Scripts\python.exe -m operations.collectors.polymarket_readonly --source live --curated-watchlist-input data\monitor_v2_curated_watchlist.csv --max-markets 3` -> 3 watchlist rows, 6 market snapshot rows, 3 aggregate wallet/activity rows.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_live_input_scoring ...` -> 12 scoring rows, 0 alerts.
- Full test suite pending after status refresh.

Decision:

- The collector now supports a curated watchlist path and only accepted rows
  enter the monitor-ready output.
- Automatic Gamma discovery remains available for candidate discovery and
  tests, but the reviewed monitor universe should come from the curated CSV.
- The first curated live scoring run still has `insufficient_baseline`, so 0
  alerts should be interpreted as baseline-not-ready, not market quietness.

Next step:

- Collect bounded curated rolling-history samples until baseline readiness can
  be assessed.

## 2026-05-22 - goal-polymarket-curated-rolling-baseline-001

Task:

- Run the first curated read-only Polymarket rolling-history sample and record
  baseline readiness.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `data/results/monitor_v2_polymarket_live_*`
- `data/results/monitor_v2_polymarket_rolling_*`

Tests:

- `.\.venv\Scripts\python.exe -m operations.collectors.polymarket_rolling_history --source live --samples 1 --reset --curated-watchlist-input data\monitor_v2_curated_watchlist.csv --max-markets 3` -> first bucket collected.
- Two additional real closed 5-minute buckets were appended with the same command without `--reset`.
- Final rolling output -> 3 buckets, 48 scoring rows, 0 alerts, `diagnostic_scores_available`.
- Full test suite pending after status refresh.

Decision:

- Accept the first 3-bucket curated rolling-history sample as an end-to-end
  real-data diagnostic baseline check.
- Do not interpret 0 alerts as market quietness; it means Rule C did not
  trigger on this short observed window.
- Do not synthesize future timestamps for empirical live-baseline claims; more
  real elapsed time is needed.

Next step:

- Build a local read-only dashboard/report view over the bounded monitor
  outputs.

## 2026-05-22 - goal-polymarket-live-dashboard-001

Task:

- Build a static local read-only dashboard over the curated Polymarket monitor
  outputs.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `operations/analysis/monitor_v2_dashboard.py`
- `tests/test_monitor_v2_dashboard.py`
- `data/results/monitor_v2_polymarket_dashboard.html`
- `data/results/monitor_v2_polymarket_dashboard_metadata.json`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_monitor_v2_dashboard.py -q` -> 3 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_dashboard` -> 3 markets, 3 buckets, 0 alerts, `diagnostic_scores_available`.
- Full test suite pending after status refresh.

Decision:

- Accept the static HTML dashboard as the first human-readable local monitor
  view.
- The dashboard reads bounded local artifacts only and contains no wallet
  addresses, no trading controls, and no causal or profitability claim.

Next step:

- Add a bounded refresh runner that collects future buckets and regenerates the
  dashboard.

## 2026-05-22 - goal-polymarket-live-refresh-loop-001

Task:

- Add a bounded refresh runner that collects rolling monitor inputs and
  regenerates the static dashboard.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `operations/collectors/polymarket_monitor_refresh.py`
- `tests/test_polymarket_monitor_refresh.py`
- `data/results/monitor_v2_polymarket_refresh_metadata.json`
- `data/results/monitor_v2_polymarket_dashboard.html`
- `data/results/monitor_v2_polymarket_dashboard_metadata.json`
- `data/results/monitor_v2_polymarket_live_*`
- `data/results/monitor_v2_polymarket_rolling_*`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_polymarket_monitor_refresh.py tests/test_monitor_v2_dashboard.py -q` -> 5 passed.
- `.\.venv\Scripts\python.exe -m operations.collectors.polymarket_monitor_refresh --source live --samples 1 --curated-watchlist-input data\monitor_v2_curated_watchlist.csv --max-markets 3` -> 4 buckets, 0 alerts, `diagnostic_scores_available`.
- Full test suite pending after status refresh.

Decision:

- Accept the refresh runner as the first practical local operation path.
- Keep it bounded by explicit sample count and delay; it is not a background
  daemon.
- Four real closed buckets remain diagnostic only, below the v2
  production-like minimum of 20 closed buckets.

Next step:

- Document the safe live monitor operator protocol and interpretation rules.

## 2026-05-22 - goal-polymarket-live-operator-protocol-001

Task:

- Document safe live monitor run commands and interpretation rules.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`
- `docs/project/WORK_LOG.md`
- `docs/project/TOOL_USAGE.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`

Tests:

- Full test suite pending after status refresh.

Decision:

- Use the bounded refresh runner as the safe operator command.
- Treat fewer than 3 buckets as interface checks, 3 to 19 buckets as
  diagnostic, and 20 or more closed 5-minute buckets as the current
  production-like baseline threshold.
- Keep all outputs descriptive and read-only.

Next step:

- Collect a 20-bucket live monitor baseline if enough real elapsed time is
  available.

## 2026-05-22 - goal-polymarket-live-production-baseline-001

Task:

- Collect and document the first production-like Polymarket live monitor
  baseline under the v2 30/20 rolling-baseline contract.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `docs/project/TOOL_USAGE.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `operations/collectors/polymarket_monitor_refresh.py`
- `operations/analysis/monitor_v2_live_input_scoring.py`
- `tests/test_polymarket_monitor_refresh.py`
- `tests/test_monitor_v2_live_input_scoring.py`
- `data/results/monitor_v2_polymarket_*`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_monitor_v2_live_input_scoring.py tests/test_polymarket_monitor_refresh.py -q` -> 9 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 276 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  276 passed through the status run.

Decision:

- Accept the 21 real closed 5-minute buckets as the first production-like
  live monitor baseline according to the current v2 contract.
- The run produced 3 reviewed markets, 126 token midpoint rows, 63 aggregate
  wallet/activity rows, 372 scoring rows, 0 alerts, and baseline readiness
  `baseline_available_zero_mad_or_non_alerting`.
- Interpret `alert_count=0` only as "Rule C did not trigger in this observed
  window"; it is not evidence that the broader market was quiet, efficient, or
  inefficient.

Next step:

- Review the production-like baseline output shape and interpretation before
  threshold sensitivity, watchlist expansion, or a read-only UI/server wrapper.

## 2026-05-22 - goal-polymarket-live-production-baseline-001 review

Task:

- Review the 21-bucket production-like Polymarket live monitor baseline and
  choose the next active goal.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.project.review_check` -> PASS,
  276 passed through the project guardrail check before the review commit.

Decision:

- Accept the baseline as the first production-like read-only live monitor
  baseline.
- The observed result remains descriptive: 0 alerts means Rule C did not
  trigger in this window. It does not prove that the broader market was quiet,
  efficient, inefficient, causal, or tradeable.
- The next useful empirical step is threshold sensitivity on the existing
  bounded artifacts before changing Rule C, expanding the watchlist, or
  building a read-only UI/server wrapper.

Next step:

- Build a deterministic monitor threshold-sensitivity report over the existing
  21-bucket production-like baseline files.

## 2026-05-22 - goal-polymarket-live-threshold-sensitivity-001

Task:

- Generate and review deterministic threshold sensitivity on the 21-bucket
  production-like Polymarket live baseline.

Files changed:

- `operations/analysis/monitor_v2_threshold_sensitivity.py`
- `tests/test_monitor_v2_threshold_sensitivity.py`
- `data/results/monitor_v2_polymarket_threshold_sensitivity.csv`
- `data/results/monitor_v2_polymarket_threshold_sensitivity_by_family.csv`
- `data/results/monitor_v2_polymarket_threshold_sensitivity.png`
- `data/results/monitor_v2_polymarket_threshold_sensitivity_metadata.json`
- `GOAL.md`
- `ROADMAP.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_monitor_v2_threshold_sensitivity.py -q` -> 3 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_threshold_sensitivity` -> 4 scenarios, default alert count 0.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 279 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  279 passed through the status run.

Decision:

- Keep Rule C unchanged for now.
- Default 30/20 Rule C produced 0 alerts; diagnostic 30/10 produced 0 alerts;
  diagnostic 10/5 produced 3 `watch` rows; diagnostic 5/3 produced 0 alerts.
- The 10/5 rows are diagnostic only and are not enough to justify changing the
  default monitor rule.
- The next useful step is broader reviewed watchlist coverage, not threshold
  relaxation.

Next step:

- Expand the curated Polymarket politics/geopolitics watchlist before the next
  production-like live baseline run.

## 2026-05-22 - goal-polymarket-live-watchlist-expansion-001

Task:

- Expand the reviewed Polymarket politics/geopolitics watchlist before the next
  production-like live baseline run.

Files changed:

- `data/monitor_v2_curated_watchlist.csv`
- `data/results/monitor_v2_curated_watchlist_validation_report.json`
- `GOAL.md`
- `ROADMAP.md`
- `docs/project/TOOL_USAGE.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.collectors.polymarket_watchlist` -> 12 accepted rows, 0 candidates, 0 rejected rows, 0 needs-followup rows.
- Temporary read-only collector verification outside the repo with `--max-markets 12` -> 12 watchlist rows, 24 token midpoint rows, 12 aggregate wallet/activity rows.
- `.\.venv\Scripts\python.exe -m pytest tests/test_polymarket_watchlist.py tests/test_polymarket_readonly_collector.py -q` -> 19 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 279 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  279 passed through the status run.

Decision:

- Expand the accepted monitor universe from 3 to 12 markets.
- Added coverage: US presidential election, US midterm House control,
  China/Taiwan conflict, Iran conflict/regime risk, Russia/Ukraine leadership,
  and Ukraine/Russia peace-process risk.
- These rows are monitor-ready universe entries only. They are not thesis event
  evidence, anomaly evidence, signal evidence, or strategy evidence.
- Rule C thresholds remain unchanged.

Next step:

- Collect a production-like live baseline using the expanded 12-market
  watchlist and v2 30/20 scoring settings.

## 2026-05-22 - goal-polymarket-expanded-live-baseline-001

Task:

- Collect a production-like live baseline using the expanded 12-market
  Polymarket politics/geopolitics watchlist.

Files changed:

- `data/results/monitor_v2_curated_watchlist_validation_report.json`
- `data/results/monitor_v2_polymarket_dashboard.html`
- `data/results/monitor_v2_polymarket_dashboard_metadata.json`
- `data/results/monitor_v2_polymarket_live_collection_metadata.json`
- `data/results/monitor_v2_polymarket_live_input_validation_report.json`
- `data/results/monitor_v2_polymarket_live_market_snapshots.csv`
- `data/results/monitor_v2_polymarket_live_wallet_tier_snapshots.csv`
- `data/results/monitor_v2_polymarket_live_watchlist.csv`
- `data/results/monitor_v2_polymarket_refresh_metadata.json`
- `data/results/monitor_v2_polymarket_rolling_alert_rows.csv`
- `data/results/monitor_v2_polymarket_rolling_alert_summary.csv`
- `data/results/monitor_v2_polymarket_rolling_history.png`
- `data/results/monitor_v2_polymarket_rolling_history_figure_metadata.json`
- `data/results/monitor_v2_polymarket_rolling_history_metadata.json`
- `data/results/monitor_v2_polymarket_rolling_scoring_metadata.json`
- `data/results/monitor_v2_polymarket_rolling_scoring_snapshots.csv`
- `data/results/monitor_v2_polymarket_rolling_scoring_validation_report.json`
- `GOAL.md`
- `ROADMAP.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.collectors.polymarket_watchlist` -> 12 accepted rows, 0 candidates, 0 rejected rows, 0 needs-followup rows.
- `.\.venv\Scripts\python.exe -m operations.collectors.polymarket_monitor_refresh --source live --samples 20 --delay-seconds 305 --reset --curated-watchlist-input data\monitor_v2_curated_watchlist.csv --max-markets 12 --baseline-observations 30 --min-baseline-observations 20` -> 20 buckets, 0 alerts.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  279 passed through the status run.

Decision:

- Accept the expanded live collection as a production-like 12-market baseline
  input for review.
- The run produced 480 token midpoint rows, 240 aggregate wallet/activity rows,
  1'416 scoring rows, 60 summary rows, and 0 alerts.
- Baseline readiness is `baseline_available_zero_mad_or_non_alerting`.
- The 0-alert result means Rule C did not trigger in this short window. It is
  not evidence of market efficiency, inefficiency, causality, private
  information, tradeability, or profitability.

Next step:

- Review the expanded-baseline output shape and interpretation before changing
  thresholds, adding a read-only wrapper, or using live-monitor wording in the
  thesis.

## 2026-05-22 - goal-polymarket-expanded-baseline-review-001

Task:

- Review the expanded 12-market live baseline output shape and interpretation.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`

Tests:

- Inspected `data/results/monitor_v2_polymarket_refresh_metadata.json`.
- Inspected `data/results/monitor_v2_polymarket_rolling_scoring_metadata.json`.
- Inspected `data/results/monitor_v2_polymarket_dashboard_metadata.json`.
- Inspected row counts and counts by status/severity from
  `data/results/monitor_v2_polymarket_rolling_alert_rows.csv`,
  `data/results/monitor_v2_polymarket_rolling_scoring_snapshots.csv`, and
  `data/results/monitor_v2_polymarket_rolling_alert_summary.csv`.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  279 passed through the status run.

Decision:

- Accept the expanded-baseline output shape for the first 12-market live
  monitor prototype.
- Keep Rule C unchanged.
- Interpret 0 alerts as no Rule C trigger in the observed short window only.
- Do not use this result as proof of market efficiency, inefficiency,
  causality, private information, tradeability, or profitability.
- Select reporting/dashboard clarity as the next implementation step.

Next step:

- Improve the read-only live monitor dashboard/reporting layer so the latest
  monitor state is understandable from one entry point.

## 2026-05-22 - goal-polymarket-live-dashboard-reporting-001

Task:

- Improve the read-only live monitor dashboard/reporting layer.

Files changed:

- `operations/analysis/monitor_v2_dashboard.py`
- `tests/test_monitor_v2_dashboard.py`
- `data/results/monitor_v2_polymarket_dashboard.html`
- `data/results/monitor_v2_polymarket_dashboard_metadata.json`
- `GOAL.md`
- `ROADMAP.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_monitor_v2_dashboard.py tests\test_polymarket_monitor_refresh.py -q` -> 5 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_dashboard` -> dashboard regenerated with 12 markets, 20 buckets, 0 alerts.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  279 passed through the status run.

Decision:

- Add run context, baseline settings, scoring row count, summary row count,
  severity counts, status counts, and zero-alert interpretation limits to the
  static dashboard.
- Keep the dashboard descriptive, local, file-based, and read-only.
- Keep Rule C thresholds unchanged.

Next step:

- Add a small local read-only wrapper or launcher for the latest dashboard
  artifacts without creating a daemon, trading surface, agent interface, or MCP
  server.

## 2026-05-22 - goal-polymarket-readonly-local-wrapper-001

Task:

- Add a local read-only launcher for the latest monitor dashboard artifacts.

Files changed:

- `operations/tools/monitor_dashboard_launcher.py`
- `tests/test_monitor_dashboard_launcher.py`
- `GOAL.md`
- `ROADMAP.md`
- `docs/project/TOOL_USAGE.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_monitor_dashboard_launcher.py -q` -> 4 passed.
- `.\.venv\Scripts\python.exe -m operations.tools.monitor_dashboard_launcher` -> reports the local dashboard URI, 12 markets, 20 buckets, 0 alerts, and read-only flags.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  283 passed through the status run.

Decision:

- Use a launcher instead of a continuously running local server for this step.
- The launcher describes and can open the local dashboard without collecting
  data, writing the database, using agents or MCP, or exposing order
  instructions.
- It rejects metadata that reports wallet-address exposure or order
  instructions.

Next step:

- Collect a second bounded expanded-watchlist live window later and compare it
  with the first 12-market baseline.

## 2026-05-23 - goal-polymarket-repeat-live-window-001

Task:

- Collect a second bounded expanded-watchlist live monitor window for stability
  comparison.

Files changed:

- `data/results/monitor_v2_curated_watchlist_validation_report.json`
- `data/results/monitor_v2_polymarket_dashboard.html`
- `data/results/monitor_v2_polymarket_dashboard_metadata.json`
- `data/results/monitor_v2_polymarket_live_collection_metadata.json`
- `data/results/monitor_v2_polymarket_live_input_validation_report.json`
- `data/results/monitor_v2_polymarket_live_market_snapshots.csv`
- `data/results/monitor_v2_polymarket_live_wallet_tier_snapshots.csv`
- `data/results/monitor_v2_polymarket_live_watchlist.csv`
- `data/results/monitor_v2_polymarket_refresh_metadata.json`
- `data/results/monitor_v2_polymarket_rolling_alert_rows.csv`
- `data/results/monitor_v2_polymarket_rolling_alert_summary.csv`
- `data/results/monitor_v2_polymarket_rolling_history.png`
- `data/results/monitor_v2_polymarket_rolling_history_figure_metadata.json`
- `data/results/monitor_v2_polymarket_rolling_history_metadata.json`
- `data/results/monitor_v2_polymarket_rolling_scoring_metadata.json`
- `data/results/monitor_v2_polymarket_rolling_scoring_snapshots.csv`
- `data/results/monitor_v2_polymarket_rolling_scoring_validation_report.json`
- `GOAL.md`
- `ROADMAP.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.collectors.polymarket_watchlist` -> 12 accepted rows, 0 candidates, 0 rejected rows, 0 needs-followup rows.
- `.\.venv\Scripts\python.exe -m operations.collectors.polymarket_monitor_refresh --source live --samples 20 --delay-seconds 305 --reset --curated-watchlist-input data\monitor_v2_curated_watchlist.csv --max-markets 12 --baseline-observations 30 --min-baseline-observations 20` -> 20 buckets, 0 alerts.
- `.\.venv\Scripts\python.exe -m operations.tools.monitor_dashboard_launcher` -> reports local dashboard URI, 12 markets, 20 buckets, 0 alerts, read-only flags.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  283 passed through the status run.

Decision:

- Accept the second bounded live window as a stability comparison input.
- The second window matches the first expanded baseline shape at the summary
  level: 12 markets, 20 buckets, 480 token midpoint rows, 240 aggregate
  wallet/activity rows, 1'416 scoring rows, 60 summary rows, 0 alerts,
  severity counts of 1'416 `none`, status counts of 1'200
  `insufficient_baseline` and 216 `zero_mad`, and baseline readiness
  `baseline_available_zero_mad_or_non_alerting`.
- This supports operational stability of the collector/dashboard path, not a
  market-efficiency, causality, private-information, tradeability, or
  profitability claim.

Next step:

- Decide how repeated live-window summaries should be stored and compared
  before more long live windows overwrite latest-run artifacts.

## 2026-05-23 - goal-polymarket-live-window-storage-001

Task:

- Implement compact repeated live-window registry and storage decision.

Files changed:

- `operations/analysis/monitor_v2_live_window_registry.py`
- `tests/test_monitor_v2_live_window_registry.py`
- `data/results/monitor_v2_live_window_registry.csv`
- `data/results/monitor_v2_live_window_registry_metadata.json`
- `GOAL.md`
- `ROADMAP.md`
- `docs/project/TOOL_USAGE.md`
- `docs/project/WORK_LOG.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_monitor_v2_live_window_registry.py -q` -> 4 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_live_window_registry --run-id expanded_window_001 --run-label "first expanded 12-market baseline"` -> registry row written from archived first-window metadata.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_live_window_registry --run-id expanded_window_002 --run-label "second expanded 12-market baseline"` -> registry row written from latest-window metadata.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  287 passed through the status run.

Decision:

- Store repeated live windows as compact registry rows rather than copying
  large latest-run CSV files for every window.
- Registry rows preserve counts, baseline settings, severity/status summaries,
  and metadata paths.
- The registry contains `expanded_window_001` and `expanded_window_002`; both
  report 12 markets, 20 buckets, 0 alerts, and baseline readiness
  `baseline_available_zero_mad_or_non_alerting`.
- No wallet addresses, order instructions, agents, MCP, ML, database writes, or
  trading credentials are involved.

Next step:

- Specify a human alert-review workflow for future non-zero monitor alerts.

## 2026-05-23 - goal-polymarket-alert-review-workflow-001

Task:

- Add wallet reference-case registry, audit, and neutral pattern features for
  public Polymarket pattern-learning examples.

Files changed:

- `data/reference_cases/wallet_reference_cases.csv`
- `data/reference_cases/wallet_reference_cases_metadata.json`
- `operations/analysis/wallet_reference_case_audit.py`
- `operations/analysis/wallet_reference_pattern_features.py`
- `tests/test_wallet_reference_cases.py`
- `data/results/wallet_reference_case_audit.csv`
- `data/results/wallet_reference_case_audit_metadata.json`
- `data/results/wallet_reference_pattern_features.csv`
- `data/results/wallet_reference_pattern_features_metadata.json`
- `docs/research/WALLET_REFERENCE_CASES.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`
- `docs/project/TOOL_USAGE.md`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_wallet_reference_cases.py -q` -> 6 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.wallet_reference_case_audit` -> 2 cases, 0 failed.
- `.\.venv\Scripts\python.exe -m operations.analysis.wallet_reference_pattern_features` -> 2 cases, 16 features.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 293 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  293 passed through the status run.

Decision:

- Treat the Iran/U.S. reported cluster and AdrianCronauer as reference cases
  for neutral pattern-learning, not as accusations or computed proof.
- Separate `reported`, `computed`, and `unknown` feature sources.
- Keep wallet addresses out of audit and feature outputs.

Next step:

- Design a bounded `reference_case_similarity_score` for future monitor watch
  candidates, still without agents, MCP, ML, trading, or misconduct claims.

## 2026-05-23 - goal-polymarket-alert-review-workflow-001

Task:

- Add bounded wallet reference-case similarity scoring and a local dashboard.

Files changed:

- `operations/analysis/wallet_reference_similarity.py`
- `tests/test_wallet_reference_similarity.py`
- `data/results/wallet_reference_similarity_scores.csv`
- `data/results/wallet_reference_similarity_summary.csv`
- `data/results/wallet_reference_similarity_matrix.png`
- `data/results/wallet_reference_similarity_dashboard.html`
- `data/results/wallet_reference_similarity_metadata.json`
- `docs/research/WALLET_REFERENCE_CASES.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`
- `docs/project/TOOL_USAGE.md`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_wallet_reference_cases.py tests\test_wallet_reference_similarity.py -q` -> 11 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.wallet_reference_similarity` -> 2 candidates, 4 comparisons, max non-self score 0.5.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 298 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  298 passed through the status run.

Decision:

- Use equal-weight triggered-pattern overlap as the first
  `reference_case_similarity_score`.
- Treat self-profile rows as calibration rows.
- Use the HTML dashboard and PNG matrix as the primary human review view.

Next step:

- Decide how future live monitor alert rows become candidate feature rows for
  the reference similarity dashboard.

## 2026-05-23 - goal-polymarket-alert-review-workflow-001

Task:

- Add a monitor reference-candidate adapter that converts non-none monitor
  rows into neutral reference-pattern features.

Files changed:

- `operations/analysis/monitor_reference_candidates.py`
- `tests/test_monitor_reference_candidates.py`
- `data/results/monitor_reference_candidate_features.csv`
- `data/results/monitor_reference_candidate_summary.csv`
- `data/results/monitor_reference_candidate_similarity_scores.csv`
- `data/results/monitor_reference_candidate_similarity_summary.csv`
- `data/results/monitor_reference_candidate_dashboard.html`
- `data/results/monitor_reference_candidate_metadata.json`
- `docs/research/WALLET_REFERENCE_CASES.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `docs/research/WHALE_METHOD.md`
- `docs/project/TOOL_USAGE.md`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_monitor_reference_candidates.py tests\test_wallet_reference_similarity.py tests\test_wallet_reference_cases.py -q` -> 17 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_reference_candidates` -> 1'416 source rows, 0 candidates, 0 similarity comparisons.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 304 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  304 passed through the status run.

Decision:

- Convert only `severity != none` monitor rows into reference candidates.
- Keep current 0-candidate output as a valid conservative result.
- Do not synthesize candidates from `none`, `insufficient_baseline`, or
  `zero_mad` rows.

Next step:

- Decide whether to collect another bounded live window or link the main
  monitor dashboard to the reference-candidate dashboard.

## 2026-05-23 - goal-polymarket-alert-review-workflow-001

Task:

- Link reference-review dashboards from the main monitor dashboard.

Files changed:

- `operations/analysis/monitor_v2_dashboard.py`
- `tests/test_monitor_v2_dashboard.py`
- `data/results/monitor_v2_polymarket_dashboard.html`
- `data/results/monitor_v2_polymarket_dashboard_metadata.json`
- `docs/project/TOOL_USAGE.md`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_monitor_v2_dashboard.py tests\test_monitor_dashboard_launcher.py -q` -> 7 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_dashboard` -> 12 markets, 20 buckets, 0 alerts.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 304 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  304 passed through the status run.

Decision:

- Keep the main monitor dashboard as the central local entry point.
- Add Reference Review counts and links without collecting data, writing the
  database, exposing wallet addresses, or activating agents/MCP.

Next step:

- Run another bounded live monitor window or add a launcher convenience path
  for opening the central dashboard.

## 2026-05-23 - goal-polymarket-alert-review-workflow-001

Task:

- Add a diagnostic sensitivity layer for monitor candidates below Rule C.

Files changed:

- `operations/analysis/monitor_reference_candidate_sensitivity.py`
- `operations/analysis/monitor_v2_dashboard.py`
- `tests/test_monitor_reference_candidate_sensitivity.py`
- `tests/test_monitor_v2_dashboard.py`
- `data/results/monitor_reference_candidate_sensitivity_*.csv`
- `data/results/monitor_reference_candidate_sensitivity_*.json`
- `data/results/monitor_reference_candidate_sensitivity_dashboard.html`
- `data/results/monitor_v2_polymarket_dashboard.html`
- `data/results/monitor_v2_polymarket_dashboard_metadata.json`
- `GOAL.md`
- `STATUS.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_monitor_reference_candidate_sensitivity.py tests/test_monitor_reference_candidates.py tests/test_monitor_v2_dashboard.py -q` -> 15 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_reference_candidate_sensitivity` -> 90 diagnostic shadow candidates, all market-only, max similarity 0.0.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_dashboard` -> 12 markets, 20 buckets, 0 alerts.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 310 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  310 passed through the status run.

Decision:

- Keep Rule C unchanged.
- Treat the 90 high-percentile zero-MAD rows as market-only diagnostic review
  cues, not alerts, wallet anomalies, efficiency evidence, or trading signals.
- Keep strict candidates and diagnostic sensitivity candidates in separate
  output files and dashboards.

Next step:

- Review whether a longer bounded live window creates wallet/concentration
  sensitivity candidates before considering any rule change.

## 2026-05-23 - goal-polymarket-alert-review-workflow-001

Task:

- Append one bounded live Polymarket bucket and refresh monitor candidate
  review outputs.

Files changed:

- `data/results/monitor_v2_polymarket_live_*.csv`
- `data/results/monitor_v2_polymarket_rolling_*.csv`
- `data/results/monitor_v2_polymarket_*metadata.json`
- `data/results/monitor_reference_candidate_*.csv`
- `data/results/monitor_reference_candidate_*.json`
- `data/results/monitor_reference_candidate_*.html`
- `data/results/monitor_v2_live_window_registry.csv`
- `data/results/monitor_v2_live_window_registry_metadata.json`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.collectors.polymarket_monitor_refresh --source live --samples 1 --curated-watchlist-input data\monitor_v2_curated_watchlist.csv --max-markets 12 --baseline-observations 30 --min-baseline-observations 20` -> 21 buckets, 7 alerts.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_reference_candidates` -> 3 strict candidates, max similarity 1.0.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_reference_candidate_sensitivity` -> 105 diagnostic candidates, 102 shadow candidates, 96 market-only shadow candidates.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_dashboard` -> 12 markets, 21 buckets, 7 alerts.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_live_window_registry --run-id expanded_window_003 --run-label "third appended 12-market live bucket with candidate review"` -> 3 registry rows.

Decision:

- Treat the first 7 non-none live monitor rows as human-review cues only.
- Do not change Rule C.
- Do not interpret the 1.0 AdrianCronauer reference overlap as evidence of
  misconduct, private information, causality, profitability, or tradeability.

Next step:

- Build or document a compact human-review report for the first non-none live
  candidates, then decide whether to collect another bounded bucket.

## 2026-05-24 - goal-polymarket-alert-review-workflow-001

Task:

- Build a compact human-review report for the first strict monitor candidates.

Files changed:

- `operations/analysis/monitor_candidate_review_report.py`
- `operations/analysis/monitor_reference_candidates.py`
- `operations/analysis/monitor_v2_dashboard.py`
- `tests/test_monitor_candidate_review_report.py`
- `tests/test_monitor_v2_dashboard.py`
- `data/results/monitor_candidate_human_review_report.csv`
- `data/results/monitor_candidate_human_review_report.html`
- `data/results/monitor_candidate_human_review_report_metadata.json`
- `data/results/monitor_v2_polymarket_dashboard.html`
- `data/results/monitor_v2_polymarket_dashboard_metadata.json`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_monitor_candidate_review_report.py tests/test_monitor_v2_dashboard.py tests/test_monitor_reference_candidates.py -q` -> 13 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_candidate_review_report` -> 3 candidates, 1 high priority, max similarity 1.0.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_dashboard` -> 12 markets, 21 buckets, 7 alerts.

Decision:

- Treat the human-review report as an explanation and triage layer over strict
  monitor candidates.
- Keep the report descriptive: no wallet addresses, no order instructions, no
  misconduct claim, no causality claim, no profitability claim, and no trading
  signal.

Next step:

- Manually source-check the high-priority AOC-2028 candidate or collect one
  more bounded live bucket to see whether the pattern repeats.

## 2026-05-26 - goal-polymarket-alert-review-workflow-001

Task:

- Make the human-review report easier to understand and visualise.

Files changed:

- `operations/analysis/monitor_candidate_review_report.py`
- `data/results/monitor_candidate_human_review_report.csv`
- `data/results/monitor_candidate_human_review_report.html`
- `data/results/monitor_candidate_human_review_report_metadata.json`
- `data/results/monitor_v2_polymarket_dashboard.html`
- `data/results/monitor_v2_polymarket_dashboard_metadata.json`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_monitor_candidate_review_report.py -q` -> 4 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_candidate_review_report` -> 3 candidates, 1 high priority, max similarity 1.0.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_dashboard` -> 12 markets, 21 buckets, 7 alerts.

Decision:

- Explain candidate priority in plain language with amount, baseline,
  concentration, and reference-overlap cards.
- Explicitly state that the AOC-2028 high-priority mark is relative to a short
  local baseline and not an economic-size, misconduct, causality,
  profitability, or trading claim.

Next step:

- Manually source-check the AOC-2028 high-priority candidate or collect
  another bounded live bucket to see whether the pattern repeats.

## 2026-05-26 - goal-monitor-insider-risk-review-materiality-001

Task:

- Add insider-risk materiality and coordination context to strict monitor
  candidate review.

Files changed:

- `operations/analysis/monitor_candidate_review_report.py`
- `operations/project/review_check.py`
- `tests/test_monitor_candidate_review_report.py`
- `tests/test_project_automation.py`
- `data/results/monitor_candidate_human_review_report.csv`
- `data/results/monitor_candidate_human_review_report.html`
- `data/results/monitor_candidate_human_review_report_metadata.json`
- `data/results/monitor_candidate_materiality_context.csv`
- `data/results/monitor_v2_polymarket_dashboard_metadata.json`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_monitor_candidate_review_report.py tests/test_project_automation.py -q` -> 28 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_candidate_review_report` -> 3 candidates, 1 high priority, materiality context written.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_dashboard` -> 12 markets, 21 buckets, 7 alerts.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 318 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> 318 passed.

Decision:

- Allow `insider-risk review candidate` as a human-review queue label, while
  still blocking confirmed-insider, misconduct, causality, profitability, and
  trading claims.
- Separate relative Rule-C anomaly strength from absolute amount, reference
  scale, and coordination context.
- Treat AOC-2028 as a high relative anomaly with low reference-scale
  materiality and a single-wallet/single-trade context.

Next step:

- Review whether the same candidate repeats in later bounded buckets or add
  manual source-check fields for reviewed insider-risk candidates.

## 2026-05-26 - goal-monitor-literature-risk-score-integration-001

Task:

- Integrate literature-prior wallet and market risk scores into the monitor
  review layer without activating a Whale Agent.

Files changed:

- `operations/analysis/monitor_literature_risk_scores.py`
- `operations/analysis/monitor_candidate_review_report.py`
- `operations/analysis/monitor_v2_dashboard.py`
- `tests/test_monitor_literature_risk_scores.py`
- `tests/test_monitor_candidate_review_report.py`
- `tests/test_monitor_v2_dashboard.py`
- `data/results/monitor_literature_risk_score_rows.csv`
- `data/results/monitor_literature_risk_score_summary.csv`
- `data/results/monitor_literature_risk_score_metadata.json`
- `data/results/monitor_candidate_human_review_report.csv`
- `data/results/monitor_candidate_human_review_report.html`
- `data/results/monitor_candidate_human_review_report_metadata.json`
- `data/results/monitor_v2_polymarket_dashboard.html`
- `data/results/monitor_v2_polymarket_dashboard_metadata.json`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_monitor_literature_risk_scores.py tests/test_monitor_candidate_review_report.py tests/test_monitor_v2_dashboard.py -q` -> 15 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_literature_risk_scores` -> 3 candidates, 3 literature-prior flags, 9 unavailable features.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_candidate_review_report` -> 3 candidates, 1 high priority, max similarity 1.0.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_dashboard` -> 12 markets, 21 buckets, 7 alerts.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 324 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> 324 passed.

Decision:

- Treat the proposed literature formula as a diagnostic prior, not as a
  replacement for Rule C.
- Show available versus unavailable features explicitly: price velocity,
  aggregate volume spike, concentration, and coordination proxy are available;
  wallet age, true new-wallet ratio, top-5 wallet concentration, and funding
  graph evidence remain unavailable in v1.
- Current strict candidates receive market-risk literature flags, but no
  wallet-risk literature flag. That supports human review, not a stronger
  informed-wallet claim.

Next step:

- Decide whether to enrich the monitor with per-wallet aggregate inputs or
  first add manual source-check fields for the current reviewed candidates.

## 2026-05-26 - goal-monitor-detection-backtest-wallet-graph-001

Task:

- Add a historical detection-backtest layer and public-wallet graph dashboard
  for Polymarket politics/geopolitics monitor candidates.

Files changed:

- `operations/collectors/polymarket_public_activity.py`
- `operations/analysis/monitor_wallet_graph.py`
- `operations/analysis/monitor_detection_backtest.py`
- `operations/analysis/monitor_v2_dashboard.py`
- `tests/test_polymarket_public_activity.py`
- `tests/test_monitor_wallet_graph.py`
- `tests/test_monitor_detection_backtest.py`
- `tests/test_monitor_v2_dashboard.py`
- `data/results/monitor_v2_polymarket_public_wallet_activity.csv`
- `data/results/monitor_v2_polymarket_public_wallet_activity_metadata.json`
- `data/results/wallet_graph_nodes.csv`
- `data/results/wallet_graph_edges.csv`
- `data/results/wallet_graph_metrics.csv`
- `data/results/wallet_graph_dashboard.html`
- `data/results/wallet_graph_metadata.json`
- `data/results/monitor_detection_backtest_cases.csv`
- `data/results/monitor_detection_backtest_summary.csv`
- `data/results/monitor_detection_backtest_dashboard.html`
- `data/results/monitor_detection_backtest_metadata.json`
- `data/results/monitor_v2_polymarket_dashboard.html`
- `data/results/monitor_v2_polymarket_dashboard_metadata.json`
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`
- `GOAL.md`
- `ROADMAP.md`
- `STATUS.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests/test_polymarket_public_activity.py tests/test_monitor_wallet_graph.py tests/test_monitor_detection_backtest.py tests/test_monitor_v2_dashboard.py -q` -> 13 passed.
- `.\.venv\Scripts\python.exe -m operations.collectors.polymarket_public_activity --source live --watchlist data\results\monitor_v2_polymarket_live_watchlist.csv --limit 500` -> 500 public activity rows, 238 public wallets, 12 markets.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_wallet_graph` -> 238 wallet nodes, 7'966 co-activity edges.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_detection_backtest` -> 3 candidates, 0 event hits, 1 reference-pattern hit.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_dashboard` -> 12 markets, 21 buckets, 7 alerts.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 334 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> 334 passed.

Decision:

- Evaluate monitor quality as detection/review context first, not as PnL or
  strategy profitability.
- Use public Polymarket Data API activity rows for the first wallet-level
  graph before adding Dune or Polygonscan funding enrichment.
- Allow full public wallet addresses only in the local forensic graph
  dashboard; compact thesis, LLM, and summary outputs remain bounded and
  review-oriented.

Next step:

- Open and inspect the wallet graph and detection-backtest dashboards, then
  decide whether to add Dune/Polygonscan enrichment, recurrence tracking across
  live windows, or manual review fields for current candidates.

## 2026-06-08 - goal-swiss-referendum-efficiency-001

Task:

- Start a deterministic Swiss 10-million referendum efficiency comparison
  between Polymarket probabilities and curated public poll shares.

Files changed:

- `GOAL.md`
- `ROADMAP.md`
- `data/swiss_referendum_10mio_polls.csv`
- `operations/collectors/swiss_referendum_polymarket.py`
- `operations/analysis/swiss_referendum_efficiency.py`
- `tests/test_swiss_referendum_polymarket.py`
- `tests/test_swiss_referendum_efficiency.py`
- `docs/research/SWISS_REFERENDUM_EFFICIENCY.md`
- `data/results/swiss_referendum_10mio_*`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_polymarket.py tests\test_swiss_referendum_efficiency.py -q` -> 11 passed.
- `.\.venv\Scripts\python.exe -m operations.collectors.swiss_referendum_polymarket --source live --append` -> 1 snapshot, Yes 0.225, No 0.775.
- `.\.venv\Scripts\python.exe -m operations.analysis.swiss_referendum_efficiency` -> 1 comparison row, 3 poll-impact rows.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 345 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS, 345 passed.

Decision:

- Treat BFS/admin.ch as official referendum and population-context evidence,
  not as the source of current voting-intention poll shares.
- Compare Polymarket Yes probability with raw poll Yes share and decided-voter
  Yes share only as descriptive deterministic gaps.
- Mark poll-release impact rows incomplete until local snapshots exist before
  and after poll publication.

Next step:

- Collect additional bounded Polymarket snapshots before interpreting poll
  publication timing effects.

## 2026-06-08 - goal-swiss-referendum-efficiency-001

Task:

- Add a one-command bounded refresh runner for the Swiss 10-million referendum
  comparison dashboard.

Files changed:

- `operations/collectors/swiss_referendum_refresh.py`
- `tests/test_swiss_referendum_refresh.py`
- `GOAL.md`
- `ROADMAP.md`
- `docs/research/SWISS_REFERENDUM_EFFICIENCY.md`
- `data/results/swiss_referendum_10mio_*`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_polymarket.py tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q` -> 14 passed.
- `.\.venv\Scripts\python.exe -m operations.collectors.swiss_referendum_refresh --source live` -> 2 snapshot rows, 2 comparison rows, 3 poll-impact rows, latest Yes 0.225.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 348 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS, 348 passed.

Decision:

- Use a manual bounded refresh command for the running view instead of a daemon
  or scheduler.
- Preserve poll-release impact rows as incomplete until local snapshot history
  contains both pre- and post-publication observations.

Next step:

- Run the bounded refresh command at later times to build enough local
  Polymarket history for poll-publication impact checks.

## 2026-06-08 - goal-swiss-referendum-efficiency-001

Task:

- Add bounded public Polymarket CLOB price-history windows around curated poll
  releases so poll-publication impact rows can use real pre/post observations.

Files changed:

- `operations/collectors/swiss_referendum_history.py`
- `operations/collectors/swiss_referendum_refresh.py`
- `operations/analysis/swiss_referendum_efficiency.py`
- `tests/test_swiss_referendum_history.py`
- `tests/test_swiss_referendum_refresh.py`
- `tests/test_swiss_referendum_efficiency.py`
- `GOAL.md`
- `ROADMAP.md`
- `docs/research/SWISS_REFERENDUM_EFFICIENCY.md`
- `data/results/swiss_referendum_10mio_*`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_polymarket.py tests\test_swiss_referendum_history.py tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q` -> 18 passed.
- `.\.venv\Scripts\python.exe -m operations.collectors.swiss_referendum_refresh --source live` -> 3 snapshot rows, 216 price-history rows, 3 comparison rows, 3 poll-impact rows.
- `.\.venv\Scripts\python.exe -m operations.analysis.swiss_referendum_efficiency` -> 3 comparison rows, 3 poll-impact rows.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 352 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS, 352 passed.

Decision:

- Use bounded public CLOB `prices-history` windows around curated poll release
  timestamps rather than chart scraping.
- Treat the first pre/post change around poll publication as descriptive
  timing context only, with no causal, mispricing, tradeability, or
  profitability claim.

Next step:

- Continue refreshing bounded snapshots and add future poll releases to the
  curated poll catalog only after source checks.

## 2026-06-08 - goal-swiss-referendum-efficiency-001

Task:

- Add explicit poll-proxy over/under relation labels for the Swiss referendum
  dashboard without turning them into mispricing or trading claims.

Files changed:

- `operations/analysis/swiss_referendum_efficiency.py`
- `tests/test_swiss_referendum_efficiency.py`
- `docs/research/SWISS_REFERENDUM_EFFICIENCY.md`
- `data/results/swiss_referendum_10mio_*`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_polymarket.py tests\test_swiss_referendum_history.py tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q` -> 18 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.swiss_referendum_efficiency` -> 3 comparison rows, 3 poll-impact rows.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 352 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS, 352 passed.

Decision:

- Use `above_poll_proxy`, `near_poll_proxy`, and `below_poll_proxy` for the
  user's over/under question.
- Keep the label scoped as a descriptive poll-proxy relation, not true
  valuation, mispricing, causality, or tradeability evidence.

Next step:

- Keep collecting bounded refresh snapshots and curate any new poll releases
  before rerunning the comparison.

## 2026-06-08 - goal-swiss-referendum-efficiency-001

Task:

- Refresh the Swiss 10-million referendum running view and verify the current
  deterministic outputs before stopping work.

Files changed:

- `data/results/swiss_referendum_10mio_*`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.collectors.swiss_referendum_refresh --source live` -> 4 snapshot rows, 216 price-history rows, 4 comparison rows, 3 poll-impact rows.
- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_polymarket.py tests\test_swiss_referendum_history.py tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q` -> 18 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 352 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS, 352 passed.

Decision:

- Keep the refreshed live Polymarket snapshot as another bounded local
  observation for the running dashboard.
- Continue reporting the latest poll relation as descriptive
  `below_poll_proxy`, not as a proven mispricing, causal effect, or trade
  signal.

Next step:

- Commit the Swiss referendum comparison separately from the paused monitor and
  wallet-graph work.

## 2026-06-08 - goal-swiss-referendum-efficiency-001

Task:

- Add the second Tamedia/LeeWas poll wave and an explicit source-boundary audit
  for BFS/admin.ch context versus voting-intention poll sources.

Files changed:

- `data/swiss_referendum_10mio_polls.csv`
- `operations/analysis/swiss_referendum_efficiency.py`
- `tests/test_swiss_referendum_efficiency.py`
- `docs/research/SWISS_REFERENDUM_EFFICIENCY.md`
- `GOAL.md`
- `data/results/swiss_referendum_10mio_*`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_efficiency.py -q` -> 7 passed.
- `.\.venv\Scripts\python.exe -m operations.collectors.swiss_referendum_refresh --source live` -> 5 snapshot rows, 288 price-history rows, 5 comparison rows, 4 poll-impact rows.
- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_polymarket.py tests\test_swiss_referendum_history.py tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q` -> 19 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 353 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS, 353 passed.

Decision:

- Include Tamedia/20 Minuten/LeeWas wave 2 as a curated poll row with date
  precision because the public source gives the publication date but no exact
  publication time.
- Generate `swiss_referendum_10mio_source_audit.csv` so BFS/admin.ch sources
  are explicitly marked as context only and not voting-intention inputs.

Next step:

- Commit the Swiss referendum comparison as a separate atomic change and keep
  future poll additions source-checked before refresh.

## 2026-06-08 - goal-swiss-referendum-efficiency-001

Task:

- Verify the generated Swiss referendum dashboard as a local HTML artifact and
  record the remaining browser-environment limitation.

Files changed:

- `docs/project/WORK_LOG.md`
- `STATUS.md`

Tests:

- Local dashboard structure check -> title present, 4 tables, 23 table rows
  including headers, 1 figure image, nonblank PNG shape 880 x 1600 x 4.
- Output metadata check -> 4 polls, 5 snapshots, 288 bounded price-history
  rows, 4 poll-impact rows, 6 source-audit rows.
- Output guardrail check -> `contains_wallet_addresses=false` and
  `contains_order_instructions=false` in Swiss referendum metadata.

Decision:

- Treat the dashboard as locally verifiable from deterministic files because
  the in-app browser target `iab` was not available in this session.
- Keep Chrome marked as an environment setup issue: Google Chrome is installed
  but not running, the Codex Chrome Extension is not installed/enabled in the
  selected profile, and the native-host registry key is missing.

Next step:

- Repair the Chrome plugin/extension setup if Chrome-backed visual inspection
  is required; otherwise commit the deterministic Swiss referendum comparison.

## 2026-06-08 - goal-swiss-referendum-efficiency-001

Task:

- Add deterministic verification for the generated Swiss referendum dashboard
  and figure so the running view is testable without relying on browser
  availability.

Files changed:

- `operations/analysis/swiss_referendum_efficiency.py`
- `tests/test_swiss_referendum_efficiency.py`
- `docs/research/SWISS_REFERENDUM_EFFICIENCY.md`
- `GOAL.md`
- `data/results/swiss_referendum_10mio_*`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_efficiency.py -q` -> 9 passed.
- `.\.venv\Scripts\python.exe -m operations.collectors.swiss_referendum_refresh --source live` -> 6 snapshot rows, 288 price-history rows, 6 comparison rows, 4 poll-impact rows.
- Dashboard verification metadata -> 4 tables, 24 table rows including headers,
  1 image, nonblank PNG shape 880 x 1600 x 4, required text present.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 355 passed.

Decision:

- Store the dashboard-verification result under `dashboard_verification` in
  `swiss_referendum_10mio_efficiency_metadata.json`.
- Keep Chrome-backed visual verification separate because the local Chrome
  extension/native-host setup is still unavailable.

Next step:

- Commit the Swiss referendum comparison and deterministic dashboard verifier
  as one coherent feature change.

## 2026-06-08 - goal-swiss-referendum-efficiency-001

Task:

- Add a deterministic latest-summary report for the Swiss referendum running
  view so thesis-facing result reporting is generated from local artifacts.

Files changed:

- `operations/analysis/swiss_referendum_efficiency.py`
- `operations/collectors/swiss_referendum_refresh.py`
- `tests/test_swiss_referendum_efficiency.py`
- `tests/test_swiss_referendum_refresh.py`
- `docs/research/SWISS_REFERENDUM_EFFICIENCY.md`
- `GOAL.md`
- `data/results/swiss_referendum_10mio_*`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q` -> 12 passed.
- `.\.venv\Scripts\python.exe -m operations.collectors.swiss_referendum_refresh --source live` -> 7 snapshot rows, 288 price-history rows, 7 comparison rows, 4 poll-impact rows, latest summary written.
- `data/results/swiss_referendum_10mio_latest_summary.md` -> includes generated/inspected counts, latest numerical result, bounded interpretation, main limitation, source boundary, and figure link.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 355 passed.

Decision:

- Render the latest summary in deterministic Python from comparison, impact,
  source-audit, and figure artifacts rather than writing an LLM-authored result
  narrative.
- Keep the poll-proxy relation descriptive and avoid causal, tradeability, or
  true-mispricing claims.

Next step:

- Commit the Swiss referendum comparison artifacts, including the latest
  summary report, as a separate feature change.

## 2026-06-08 - goal-swiss-referendum-efficiency-001

Task:

- Add a deterministic running-status artifact for the Swiss referendum view so
  local output presence and snapshot recency are explicit after each refresh.

Files changed:

- `operations/collectors/swiss_referendum_refresh.py`
- `tests/test_swiss_referendum_refresh.py`
- `docs/research/SWISS_REFERENDUM_EFFICIENCY.md`
- `GOAL.md`
- `data/results/swiss_referendum_10mio_*`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_refresh.py -q` -> 4 passed.
- `.\.venv\Scripts\python.exe -m operations.collectors.swiss_referendum_refresh --source live` -> 8 snapshot rows, 288 price-history rows, 8 comparison rows, 4 poll-impact rows, running status written.
- `data/results/swiss_referendum_10mio_running_status.json` -> all required local outputs exist, latest snapshot age 0.017 minutes, snapshot_recency_status fresh, ready_for_running_view true.
- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_polymarket.py tests\test_swiss_referendum_history.py tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q` -> 22 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 356 passed.

Decision:

- Treat running status as a local artifact-recency check only. It does not
  imply market-data completeness and does not add causal, tradeability, or
  valuation claims.

Next step:

- Commit the Swiss referendum comparison with the running-status artifact as a
  separate feature change.

## 2026-06-08 - goal-swiss-referendum-efficiency-001

Task:

- Extend Swiss referendum poll-impact rows with deterministic 1h, 6h, 24h, and
  48h post-publication reaction-window changes.

Files changed:

- `operations/analysis/swiss_referendum_efficiency.py`
- `tests/test_swiss_referendum_efficiency.py`
- `docs/research/SWISS_REFERENDUM_EFFICIENCY.md`
- `GOAL.md`
- `data/results/swiss_referendum_10mio_*`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_efficiency.py -q` -> 10 passed.
- `.\.venv\Scripts\python.exe -m operations.collectors.swiss_referendum_refresh --source live` -> 9 snapshot rows, 288 price-history rows, 9 comparison rows, 4 poll-impact rows.
- Latest SRG/gfs.bern wave 2 reaction windows -> 1h 0.0 pp, 6h -1.0 pp, 24h -4.0 pp, 48h -5.0 pp.
- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_polymarket.py tests\test_swiss_referendum_history.py tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q` -> 23 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 357 passed.

Decision:

- Compute reaction-window changes as descriptive changes from the closest
  pre-publication observation to the last local observation inside each
  post-publication window.
- Keep these values as timing descriptors only, with no causal, efficiency,
  tradeability, or true-mispricing claim.

Next step:

- Commit the Swiss referendum comparison with reaction-window impact metrics as
  a separate feature change.

## 2026-06-08 - goal-swiss-referendum-efficiency-001

Task:

- Add a tidy poll-reaction-window CSV so each poll/window combination can be
  filtered, charted, or used in thesis tables without reshaping the wide
  impact table.

Files changed:

- `operations/analysis/swiss_referendum_efficiency.py`
- `operations/collectors/swiss_referendum_refresh.py`
- `tests/test_swiss_referendum_efficiency.py`
- `tests/test_swiss_referendum_refresh.py`
- `docs/research/SWISS_REFERENDUM_EFFICIENCY.md`
- `GOAL.md`
- `data/results/swiss_referendum_10mio_*`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q` -> 15 passed.
- `.\.venv\Scripts\python.exe -m operations.collectors.swiss_referendum_refresh --source live` -> 10 snapshot rows, 288 price-history rows, 10 comparison rows, 4 poll-impact rows, 16 tidy reaction-window rows.
- `data/results/swiss_referendum_10mio_poll_reaction_windows.csv` -> 16 rows, 4 windows per curated poll, descriptive no-causality interpretation scope.
- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_polymarket.py tests\test_swiss_referendum_history.py tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q` -> 24 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 358 passed.

Decision:

- Keep the wide `poll_impacts.csv` for dashboard readability and add
  `poll_reaction_windows.csv` for downstream filtering and plotting.
- Preserve the same descriptive pre/post no-causality scope in the tidy file.

Next step:

- Commit the Swiss referendum comparison with tidy reaction-window output as a
  separate feature change.

## 2026-06-08 - goal-swiss-referendum-efficiency-001

Task:

- Add and verify the deterministic poll-reaction-window figure for the Swiss
  referendum dashboard and rerun the live bounded refresh.

Files changed:

- `operations/analysis/swiss_referendum_efficiency.py`
- `operations/collectors/swiss_referendum_refresh.py`
- `tests/test_swiss_referendum_efficiency.py`
- `tests/test_swiss_referendum_refresh.py`
- `docs/research/SWISS_REFERENDUM_EFFICIENCY.md`
- `GOAL.md`
- `data/results/swiss_referendum_10mio_*`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.collectors.swiss_referendum_refresh --source live` -> 11 snapshot rows, 288 price-history rows, 11 comparison rows, 4 poll-impact rows, 16 tidy reaction-window rows.
- `data/results/swiss_referendum_10mio_reaction_windows.png` -> nonblank figure with shape 832 x 1600 x 4.
- `data/results/swiss_referendum_10mio_efficiency_metadata.json` -> dashboard verification sees 2 images, 5 tables, and 16 poll-reaction-window rows under `outputs`.
- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_polymarket.py tests\test_swiss_referendum_history.py tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q` -> 24 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 358 passed.

Decision:

- Keep the reaction-window graphic as a deterministic dashboard artifact derived
  only from local `poll_reaction_windows.csv` rows.
- Continue to label all poll-window movements as descriptive pre/post changes,
  not causal poll effects or trade signals.

Next step:

- Commit the Swiss referendum comparison with dashboard reaction-window figure
  support as a separate feature change.

## 2026-06-08 - goal-swiss-referendum-efficiency-001

Task:

- Fix Swiss refresh output routing so the source-boundary audit is written to
  the explicit refresh output path instead of falling back to the default path.

Files changed:

- `operations/collectors/swiss_referendum_refresh.py`
- `tests/test_swiss_referendum_refresh.py`
- `data/results/swiss_referendum_10mio_*`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- Chrome plugin check -> unavailable: Chrome installed but not running; Codex
  Chrome Extension not installed/enabled in selected profile; native-host
  registry entry missing.
- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_refresh.py -q` -> 4 passed.
- `.\.venv\Scripts\python.exe -m operations.collectors.swiss_referendum_refresh --source live` -> 12 snapshot rows, 288 price-history rows, 12 comparison rows, 4 poll-impact rows, 16 tidy reaction-window rows, explicit source-audit output path.
- `data/results/swiss_referendum_10mio_source_audit.csv` -> 6 rows matching `outputs.source_audit_row_count` in efficiency metadata.
- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_polymarket.py tests\test_swiss_referendum_history.py tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q` -> 24 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 358 passed.

Decision:

- Treat the source-boundary audit as a required refresh artifact, like the
  dashboard, comparison, impact, and reaction-window outputs.
- Keep Chrome verification out of the claim until the user repairs the Codex
  Chrome Extension/native-host setup.

Next step:

- Commit the Swiss referendum comparison with explicit source-audit refresh
  routing as part of the same feature change.

## 2026-06-08 - goal-swiss-referendum-efficiency-001

Task:

- Add first-glance running-view context to the Swiss referendum dashboard.

Files changed:

- `operations/analysis/swiss_referendum_efficiency.py`
- `tests/test_swiss_referendum_efficiency.py`
- `data/results/swiss_referendum_10mio_*`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- Chrome plugin check -> unavailable: Extension connection failed after retry;
  Chrome installed but not running; Codex Chrome Extension not installed/enabled
  in selected profile; native-host registry entry missing.
- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q` -> 15 passed.
- `.\.venv\Scripts\python.exe -m operations.collectors.swiss_referendum_refresh --source live` -> 13 snapshot rows, 288 price-history rows, 13 comparison rows, 4 poll-impact rows, 16 tidy reaction-window rows.
- Dashboard verification -> 2 images, 5 tables, 48 table rows, 12 metric blocks, nonblank figure.
- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_polymarket.py tests\test_swiss_referendum_history.py tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q` -> 24 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 358 passed.

Decision:

- Show latest local snapshot time, latest matched poll, matched poll publication
  time, and manual bounded refresh mode in the dashboard metrics.
- Keep these as display fields from deterministic comparison rows, not new
  statistical metrics.

Next step:

- Commit the Swiss referendum comparison with dashboard running-context metrics
  as part of the same feature change.

## 2026-06-08 - goal-swiss-referendum-efficiency-001

Task:

- Add a deterministic poll-release timing summary to answer, per curated poll,
  when the first post-release Polymarket observation appeared and how the
  1h/6h/24h/48h windows moved.

Files changed:

- `operations/analysis/swiss_referendum_efficiency.py`
- `tests/test_swiss_referendum_efficiency.py`
- `data/results/swiss_referendum_10mio_*`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- Chrome plugin check -> unavailable after retry; Chrome installed but not
  running; Codex Chrome Extension not installed/enabled in selected profile;
  native-host registry entry missing.
- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q` -> 15 passed.
- `.\.venv\Scripts\python.exe -m operations.collectors.swiss_referendum_refresh --source live` -> 14 snapshot rows, 288 price-history rows, 14 comparison rows, 4 poll-impact rows, 16 tidy reaction-window rows.
- `data/results/swiss_referendum_10mio_latest_summary.md` -> contains `Poll Release Timing Summary` with four poll-level timing bullets and descriptive no-causality scope.
- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_polymarket.py tests\test_swiss_referendum_history.py tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q` -> 24 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 358 passed.

Decision:

- Render poll-release timing as a readable summary derived from `poll_impacts.csv`.
- Keep the timing summary descriptive and bounded to existing local
  observations; do not infer causality, efficiency, tradeability, or true
  mispricing.

Next step:

- Commit the Swiss referendum comparison with poll-release timing summaries as
  part of the same feature change.

## 2026-06-08 - goal-swiss-referendum-efficiency-001

Task:

- Add YouGov Schweiz Stimmungsbarometer releases to the curated Swiss
  referendum poll catalog after source-freshness checking.

Files changed:

- `data/swiss_referendum_10mio_polls.csv`
- `operations/analysis/swiss_referendum_efficiency.py`
- `tests/test_swiss_referendum_efficiency.py`
- `docs/research/SWISS_REFERENDUM_EFFICIENCY.md`
- `GOAL.md`
- `data/results/swiss_referendum_10mio_*`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- Chrome plugin check -> unavailable after retry; Chrome installed but not
  running; Codex Chrome Extension not installed/enabled in selected profile;
  native-host registry entry missing.
- Web source check -> YouGov Schweiz articles show wave 1 on 2026-05-05
  with 45% Yes, 46% No, 8% undecided; interim wave 2 on 2026-05-27 with 43%
  Yes, 51% No, 6% undecided; final wave 2 on 2026-06-02 with 38% Yes, 55%
  No, 7% undecided.
- `.\.venv\Scripts\python.exe -m operations.collectors.swiss_referendum_refresh --source live` -> 15 snapshot rows, 504 price-history rows, 15 comparison rows, 7 poll-impact rows, 28 tidy reaction-window rows.
- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q` -> 16 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_polymarket.py tests\test_swiss_referendum_history.py tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q` -> 25 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 359 passed.

Decision:

- Treat YouGov Schweiz as a curated voting-intention source, separate from
  BFS/admin.ch context.
- Document that YouGov's MRP use of BFS population proportions does not make
  the reported vote-intention shares BFS values.

Next step:

- Commit the Swiss referendum comparison with YouGov poll releases included as
  part of the same feature change.

## 2026-06-08 - goal-swiss-referendum-efficiency-001

Task:

- Add a latest-by-source poll comparison output for the newest prior poll from
  each curated source.

Files changed:

- `operations/analysis/swiss_referendum_efficiency.py`
- `operations/collectors/swiss_referendum_refresh.py`
- `tests/test_swiss_referendum_efficiency.py`
- `tests/test_swiss_referendum_refresh.py`
- `docs/research/SWISS_REFERENDUM_EFFICIENCY.md`
- `GOAL.md`
- `data/results/swiss_referendum_10mio_*`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- Chrome plugin check -> unavailable after retry; Chrome installed but not
  running; Codex Chrome Extension not installed/enabled in selected profile;
  native-host registry entry missing.
- `.\.venv\Scripts\python.exe -m operations.collectors.swiss_referendum_refresh --source live` -> 16 snapshot rows, 504 price-history rows, 16 comparison rows, 7 poll-impact rows, 28 tidy reaction-window rows, 3 latest-source comparison rows.
- `data/results/swiss_referendum_10mio_latest_source_comparison.csv` -> latest Polymarket Yes 23.0% compared to SRG/gfs.bern 45.0%, Tamedia/LeeWas 47.0%, and YouGov Schweiz 38.0%; all labelled `below_poll_proxy`.
- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_polymarket.py tests\test_swiss_referendum_history.py tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q` -> 26 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 360 passed.

Decision:

- Store the cross-source comparison in
  `data/results/swiss_referendum_10mio_latest_source_comparison.csv` and render
  it in the dashboard and latest summary.
- Keep the table as a descriptive poll-proxy view only; it is not a poll
  average, forecast model, valuation model, or true-mispricing test.

Next step:

- Commit the Swiss referendum comparison with latest-by-source poll comparison
  as part of the same feature change.

## 2026-06-08 - goal-swiss-referendum-efficiency-001

Task:

- Make the "faster, slower, or different" Polymarket processing question more
  visible for the Swiss 10-million referendum comparison.

Files changed:

- `operations/analysis/swiss_referendum_efficiency.py`
- `operations/collectors/swiss_referendum_refresh.py`
- `tests/test_swiss_referendum_efficiency.py`
- `tests/test_swiss_referendum_refresh.py`
- `docs/research/SWISS_REFERENDUM_EFFICIENCY.md`
- `GOAL.md`
- `data/results/swiss_referendum_10mio_*`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q` -> 18 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_polymarket.py tests\test_swiss_referendum_history.py tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q` -> 27 passed.
- `.\.venv\Scripts\python.exe -m operations.collectors.swiss_referendum_refresh --source live` -> 18 snapshot rows, 504 price-history rows, 18 comparison rows, 7 poll-impact rows, 7 information-response rows.
- `.\.venv\Scripts\python.exe -m pytest -q` -> 361 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS, 361 passed.

Decision:

- Define the poll signal as the change in decided Yes share versus the
  immediately previous curated poll release.
- Compare that poll-signal direction with Polymarket movements in 1h, 6h,
  24h, and 48h post-publication windows.
- Use direction-only labels such as `delayed_same_direction_6h` and
  `no_same_direction_within_48h`; these are descriptive alignment labels, not
  causality, statistical significance, tradeability, or market-efficiency proof.

Next step:

- Commit the Swiss referendum information-response dashboard extension as a
  separate change from the paused monitor and wallet-graph work.

## 2026-06-08 - goal-swiss-referendum-efficiency-001

Task:

- Inspect current project state and prepare a supervisor-facing overview of
  completed thesis work and current Swiss referendum comparison outputs.

Files changed:

- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  361 passed.

Decision:

- Use `GOAL.md`, `STATUS.md`, `ROADMAP.md`, `docs/project/WORK_LOG.md`, and
  generated deterministic result artifacts as the source for the overview.
- Treat the latest Swiss referendum comparison as descriptive poll-proxy
  evidence only; no causal, tradeability, or true-mispricing claim is made.

Next step:

- Share the supervisor-facing project overview and decide whether to commit
  the status/work-log maintenance update separately.

## 2026-06-08 - goal-swiss-referendum-efficiency-001

Task:

- Expand the supervisor-facing overview to cover the full project before the
  Swiss referendum track, including H1-H3 methods, deterministic results,
  thesis figures, and the paused monitor prototype.

Files changed:

- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- Pending final project-control checks after the overview inspection.

Decision:

- Present H1 as forecast-quality comparison, H2 as daily event-window response,
  H3 as wallet-tier timing diagnostics, and monitor-v2 as a paused read-only
  research prototype rather than thesis-core causal evidence.
- Keep Swiss referendum outputs separate as the active current goal.

Next step:

- Run project-control checks and report the expanded overview with limitations.

## 2026-06-10 - goal-swiss-referendum-efficiency-001

Task:

- Assess `warproxxx/poly_data` for possible usefulness to the active Swiss
  referendum Polymarket-vs-polls comparison pipeline.

Files changed:

- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `python -m operations.project.update_status` -> PASS for status update, but
  recorded pytest as FAIL because `C:\Python314\python.exe` has no `pytest`
  module.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  361 passed.
- `.\.venv\Scripts\python.exe -m operations.project.review_check` -> PASS,
  361 passed.

Decision:

- Treat `poly_data` as a useful reference for read-only on-chain trade-event
  backfill and maker/taker trade structuring, not as a drop-in dependency for
  the current referendum dashboard.
- Do not import or vendor GPL-covered code without a separate license decision;
  reuse concepts only.

Next step:

- If trade-level microstructure is added later, implement a narrow,
  tested collector behind the existing deterministic artifact boundary and
  keep wallet-address outputs out of default thesis-facing views.

## 2026-06-10 - goal-swiss-referendum-efficiency-001

Task:

- Build an easy-to-read supervisor report covering the full project folder
  contents, methodological rationale, deterministic H1-H3 results, paused
  monitor work, active Swiss referendum track, and visual artifacts.

Files changed:

- `requirements.txt`
- `operations/project/build_dozenten_report.py`
- `tests/test_dozenten_report.py`
- `docs/project/dozentenbericht_ba_thesis.md`
- `docs/project/dozentenbericht_ba_thesis.html`
- `docs/project/dozentenbericht_ba_thesis.docx`
- `docs/project/dozentenbericht_assets/project_pipeline_overview.png`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_dozenten_report.py -q`
  -> PASS, 1 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> PASS, 362 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  362 passed.

QA:

- DOCX structural check found 65 paragraphs, 14 tables, 10 sections, and 10
  embedded images.
- HTML structural check found 10 image references and no missing local image
  paths.
- `render_docx.py` could not complete because the local machine has no
  available Office/LibreOffice conversion executable after renderer dependency
  setup; visual DOCX render QA remains unavailable on this machine.

Decision:

- Deliver the DOCX as the Word-facing document and the HTML/Markdown files as
  readable/reviewable companion artifacts.
- Keep all claims tied to deterministic local artifacts and preserve the
  no-causality, no-tradeability, no-profitability, no-agent-runtime scope.

Next step:

- Use `docs/project/dozentenbericht_ba_thesis.docx` for the Dozenten meeting;
  open the HTML companion if a browser-readable version is easier to present.

## 2026-06-10 - goal-swiss-referendum-efficiency-001

Task:

- Reassess `warproxxx/poly_data` against the active deterministic Swiss
  referendum pipeline and current project guardrails.

Files changed:

- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  362 passed.

Decision:

- The repository is useful as a reference for read-only on-chain `OrderFilled`
  backfills and trade-level microstructure, but not as a drop-in dependency for
  the active referendum dashboard.
- Current Swiss referendum work should continue to use bounded Gamma/CLOB
  snapshot and price-history artifacts; any future trade collector should be a
  narrow, tested local adapter with explicit wallet/privacy boundaries.

Next step:

- If trade-level microstructure becomes part of the accepted scope, draft a
  separate implementation goal before adding a new collector.

## 2026-06-10 - H1 forecast-quality continuation

Task:

- Replace the weak H1 reliability/calibration presentation with a clearer
  deterministic forecast-quality output for Polymarket versus FiveThirtyEight
  and simple baselines.

Files changed:

- `operations/analysis/h1_forecast_quality.py`
- `tests/test_h1_forecast_quality.py`
- `operations/project/build_dozenten_report.py`
- `tests/test_dozenten_report.py`
- `docs/research/RESEARCH_SPEC.md`
- `data/results/h1_forecast_quality_sources.csv`
- `data/results/h1_forecast_quality_pairwise.csv`
- `data/results/h1_forecast_quality_metadata.json`
- `data/results/h1_forecast_quality.png`
- `docs/project/dozentenbericht_ba_thesis.md`
- `docs/project/dozentenbericht_ba_thesis.html`
- `docs/project/dozentenbericht_ba_thesis_h1_forecast_quality.docx`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_forecast_quality.py -q`
  -> PASS, 2 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_dozenten_report.py -q`
  -> PASS, 1 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> PASS, 364 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  364 passed.

Key output:

- H1 paired daily rows: 194, from 2024-03-01 to 2024-09-12.
- Polymarket lower Brier loss than FiveThirtyEight: 194 of 194 paired days.
- Mean Brier Polymarket: 0.2303.
- Mean Brier FiveThirtyEight: 0.3324.
- Mean loss advantage versus FiveThirtyEight: 0.1021 Brier points.
- Polymarket lower Brier loss than the 50-percent baseline: 121 of 194 days.
- Polymarket and prior-day Polymarket remain effectively tied; current
  Polymarket is lower on 55 days, prior-day lower on 57 days, with 82 ties.

Decision:

- Use `data/results/h1_forecast_quality.png` as the H1 visual instead of the
  old reliability curve in the supervisor report and research spec.
- Keep wording bounded: FiveThirtyEight is a poll-based probability forecast,
  not a raw poll share; the daily rows are repeated forecasts for one resolved
  election, not independent election outcomes.

Limitation:

- The result supports a forecast-quality claim for the tested overlap window
  only. It does not prove reaction speed, causality, tradeability, or general
  superiority across all Polymarket markets.

Note:

- The existing default DOCX report could not be overwritten because the file
  was locked locally. The updated Word output was written to
  `docs/project/dozentenbericht_ba_thesis_h1_forecast_quality.docx`.

Next step:

- Review the new H1 figure and decide whether to add more independent
  probability-forecast events before making broader thesis claims.

## 2026-06-10 - H1 evidence-scope audit continuation

Task:

- Add a deterministic audit that separates H1 daily forecast rows from
  independent resolved forecast-quality cases.

Files changed:

- `operations/analysis/h1_evidence_scope.py`
- `tests/test_h1_evidence_scope.py`
- `operations/project/build_dozenten_report.py`
- `tests/test_dozenten_report.py`
- `docs/research/RESEARCH_SPEC.md`
- `data/results/h1_evidence_scope.csv`
- `data/results/h1_evidence_scope_metadata.json`
- `data/results/h1_evidence_scope.png`
- `docs/project/dozentenbericht_ba_thesis.md`
- `docs/project/dozentenbericht_ba_thesis.html`
- `docs/project/dozentenbericht_ba_thesis_h1_forecast_quality.docx`
- `STATUS.md`
- `docs/project/WORK_LOG.md`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_evidence_scope.py -q`
  -> PASS, 3 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_dozenten_report.py -q`
  -> PASS, 1 passed.
- `.\.venv\Scripts\python.exe -m pytest -q` -> PASS, 367 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status` -> PASS,
  367 passed.

Key output:

- Eligible Brier-computable H1 independent resolved outcome count: 1.
- Eligible daily paired forecast rows: 194.
- Polymarket lower Brier loss than FiveThirtyEight inside the eligible case:
  194 of 194 paired daily rows.
- Swiss 10-million referendum local poll rows: 7, but unresolved as of
  2026-06-10 and therefore not Brier-computable.
- Curated H2 event rows: 7, but they are event windows inside one presidential
  market and not independent H1 forecast outcomes.

Decision:

- Do not claim that H1 already proves Polymarket is better in many independent
  cases. The current deterministic evidence supports a strong one-case
  forecast-quality finding and identifies the data needed for a broader claim.
- Include `data/results/h1_evidence_scope.png` in the Dozentenbericht so the
  methodological boundary is visible next to the H1 forecast-quality figure.

Next step:

- For a broader H1 claim, collect or curate additional resolved markets with
  Polymarket probability history and compatible probability forecasts, or
  document a poll-to-probability transformation before using raw poll shares in
  Brier scoring.

## 2026-06-10 - External poly_data repository review

Task:

- Review `warproxxx/poly_data` for possible use in the local Polymarket data
  pipeline.

Files changed:

- `docs/project/WORK_LOG.md`
- `STATUS.md`

Checks:

- Repository reviewed from a temporary clone at commit
  `bda27941c0c7e1bab05539b9fd195dc567e85edc`.
- Local project goal checked: exactly one active goal remains in `GOAL.md`.

Decision:

- Do not vendor or directly depend on `poly_data` now. Its on-chain
  `OrderFilled` approach is useful as a reference for future fill-side trade
  collection, but it is not a drop-in improvement for the active Swiss
  referendum probability-vs-polls pipeline.
- Reuse only ideas after reimplementation with local validation, tests,
  bounded outputs, no wallet exposure by default, and explicit read-only
  guardrails.

Limitation:

- No live RPC backfill was run. The review inspected source code, project
  metadata, official Polymarket documentation, and the local collector scope.

## 2026-06-10 - H1 expansion-readiness audit

Task:

- Audit whether the current H1 forecast-quality baseline can be expanded from
  existing local artifacts before claiming that Polymarket is better across
  many cases.

Files changed:

- `operations/analysis/h1_expansion_readiness.py`
- `tests/test_h1_expansion_readiness.py`
- `operations/project/build_dozenten_report.py`
- `tests/test_dozenten_report.py`
- `docs/research/RESEARCH_SPEC.md`
- `data/results/h1_expansion_readiness.csv`
- `data/results/h1_expansion_readiness_metadata.json`
- `data/results/h1_expansion_readiness.png`
- `docs/project/dozentenbericht_ba_thesis.md`
- `docs/project/dozentenbericht_ba_thesis.html`
- `docs/project/dozentenbericht_ba_thesis_h1_forecast_quality.docx`

Tests:

- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_expansion_readiness.py -q`
  -> PASS, 3 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_expansion_readiness.py tests\test_h1_forecast_quality.py tests\test_h1_evidence_scope.py tests\test_dozenten_report.py -q`
  -> PASS, 9 passed.

Key output:

- Current H1 paired daily Brier rows: 194.
- Eligible independent resolved H1 outcomes: 1.
- Local Polymarket daily rows after the current H1 end date 2024-09-12: 55.
- Local FiveThirtyEight probability rows after 2024-09-12: 0.
- Additional compatible H1 Brier pairs available now: 0.

Decision:

- Do not extend H1 with Polymarket-only tail rows or raw polling averages.
- Keep the broad many-cases Polymarket-better-than-polls claim unsupported
  until additional resolved markets with compatible probability forecasts are
  curated, or until a poll-share-to-probability transformation is documented
  and tested.

Next step:

- Search for additional resolved markets with both Polymarket probability
  history and a traditional probability forecast, not only poll vote shares.

## 2026-06-10 - H1 final-snapshot report integration

Task:

- Integrate the curated H1 final-snapshot extension into the Dozentenbericht
  and research specification so the additional resolved outcomes are visible
  without overstating them as a broad many-markets proof.

Files changed:

- `operations/project/build_dozenten_report.py`
- `tests/test_dozenten_report.py`
- `docs/research/RESEARCH_SPEC.md`
- `docs/project/dozentenbericht_ba_thesis.md`
- `docs/project/dozentenbericht_ba_thesis.html`
- `docs/project/dozentenbericht_ba_thesis_h1_forecast_quality.docx`
- `docs/project/WORK_LOG.md`

Checks:

- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report --docx-output docs\project\dozentenbericht_ba_thesis_h1_forecast_quality.docx`
  -> PASS, 13 report figures.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_final_snapshot_extension.py tests\test_h1_expansion_readiness.py tests\test_h1_forecast_quality.py tests\test_h1_evidence_scope.py tests\test_dozenten_report.py -q`
  -> PASS, 12 passed.
- `data/results/h1_final_snapshot.png` inspected; nonblank image size
  2176x833, luma standard deviation 62.14.

Key output:

- H1 final-snapshot extension covers 3 resolved 2024 election outcomes.
- Polymarket has lower Brier loss in 2 of 3 outcomes; FiveThirtyEight final
  forecast has lower loss in 1 of 3 outcomes.
- Mean Brier is 0.1393 for Polymarket and 0.1740 for FiveThirtyEight, with a
  mean Polymarket loss advantage of 0.0347 Brier points.

Decision:

- Treat the final-snapshot extension as a small compatibility check that
  strengthens the H1 forecast-quality direction, not as a daily time series,
  raw-poll comparison, reaction-speed result, or broad many-markets proof.

Next step:

- Continue expanding H1 only through additional resolved markets with
  compatible probability forecasts, or through a documented and tested
  poll-share-to-probability transformation before raw poll shares enter Brier
  scoring.

## 2026-06-10 - H1 final-snapshot extension to eight cases

Task:

- Expand the H1 final-snapshot extension beyond the three national/control
  outcomes by adding compatible 538 final forecast probabilities and
  Polymarket final-time prices for five 2024 Senate state races.

Files changed:

- `operations/analysis/h1_final_snapshot_extension.py`
- `tests/test_h1_final_snapshot_extension.py`
- `operations/project/build_dozenten_report.py`
- `tests/test_dozenten_report.py`
- `docs/research/RESEARCH_SPEC.md`
- `data/results/h1_final_snapshot_cases.csv`
- `data/results/h1_final_snapshot_summary.csv`
- `data/results/h1_final_snapshot_metadata.json`
- `data/results/h1_final_snapshot.png`
- `docs/project/dozentenbericht_ba_thesis.md`
- `docs/project/dozentenbericht_ba_thesis.html`
- `docs/project/dozentenbericht_ba_thesis_h1_forecast_quality.docx`
- `docs/project/WORK_LOG.md`

Checks:

- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_final_snapshot_extension.py -q`
  -> PASS, 3 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.h1_final_snapshot_extension --source live`
  -> PASS, 8 cases generated from public Gamma/CLOB endpoints.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report --docx-output docs\project\dozentenbericht_ba_thesis_h1_forecast_quality.docx`
  -> PASS, 13 report figures.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_final_snapshot_extension.py tests\test_h1_expansion_readiness.py tests\test_h1_forecast_quality.py tests\test_h1_evidence_scope.py tests\test_dozenten_report.py -q`
  -> PASS, 12 passed.
- `data/results/h1_final_snapshot.png` inspected; nonblank image size
  2244x1054, luma standard deviation 53.83. Labels are horizontal and
  readable for 8 cases.

Key output:

- H1 final-snapshot extension now covers 8 resolved 2024 election outcomes:
  president, Senate control, House control, and Republican Senate wins in
  Montana, Ohio, West Virginia, Florida, and Texas.
- Polymarket has lower Brier loss in 5 of 8 outcomes; FiveThirtyEight final
  forecast has lower loss in 3 of 8 outcomes.
- Mean Brier is 0.0784 for Polymarket and 0.0933 for FiveThirtyEight, with a
  mean Polymarket loss advantage of 0.0149 Brier points.

Decision:

- Treat the expanded final-snapshot extension as stronger H1 forecast-quality
  evidence than the earlier 3-case check, but still not as a broad
  many-markets proof because all cases share one 2024 election-day context and
  are not a daily multi-market panel.

Next step:

- Continue searching for additional resolved markets with compatible
  probability forecasts or implement a documented poll-share-to-probability
  transformation before raw polls enter H1 Brier comparisons.

## 2026-06-10 - External poly_data repository assessment

Task:

- Assess whether `warproxxx/poly_data` could improve this project's
  Polymarket data analysis pipeline.

Files changed:

- `docs/project/WORK_LOG.md`

Checks:

- Inspected `GOAL.md` and confirmed one active goal:
  `goal-swiss-referendum-efficiency-001`.
- Reviewed the external repository in a temporary clone outside the project
  workspace.
- Compared its Gamma, Polygon RPC, and trade-processing stages with the local
  read-only Gamma/CLOB/Data API collectors.

Decision:

- `poly_data` is potentially useful as a reference for a future on-chain
  fill-level trade archive, but it should not be imported or run as part of the
  active deterministic thesis pipeline without a local adapter, tests,
  validation gates, bounded scope, and licence review.

Next step:

- If fill-level on-chain data becomes a goal, implement a small local
  proof-of-concept adapter against one curated market and one bounded block
  interval rather than vendoring the external pipeline.

## 2026-06-10 - H1 state-poll snapshot extension

Task:

- Expand H1 forecast-quality evidence beyond the 8-case final-snapshot check
  with additional resolved state-level 2024 presidential outcomes.

Files changed:

- `operations/analysis/h1_state_poll_snapshot_extension.py`
- `tests/test_h1_state_poll_snapshot_extension.py`
- `operations/project/build_dozenten_report.py`
- `tests/test_dozenten_report.py`
- `docs/research/RESEARCH_SPEC.md`
- `data/results/h1_state_poll_snapshot_cases.csv`
- `data/results/h1_state_poll_snapshot_summary.csv`
- `data/results/h1_state_poll_snapshot_metadata.json`
- `data/results/h1_state_poll_snapshot.png`
- `docs/project/dozentenbericht_ba_thesis.md`
- `docs/project/dozentenbericht_ba_thesis.html`
- `docs/project/dozentenbericht_ba_thesis_h1_forecast_quality.docx`
- `docs/project/WORK_LOG.md`

Checks:

- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_snapshot_extension.py -q`
  -> PASS, 5 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.h1_state_poll_snapshot_extension --source live`
  -> PASS, 13 state cases generated from public 538 GitHub raw data and public
  Polymarket Gamma/CLOB endpoints.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_snapshot_extension.py tests\test_h1_final_snapshot_extension.py tests\test_h1_expansion_readiness.py tests\test_h1_forecast_quality.py tests\test_h1_evidence_scope.py tests\test_dozenten_report.py -q`
  -> PASS, 17 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report --docx-output docs\project\dozentenbericht_ba_thesis_h1_forecast_quality.docx`
  -> PASS, 14 report figures.
- `data/results/h1_state_poll_snapshot.png` inspected; nonblank image size
  2346x1190, luma standard deviation 52.97.

Key output:

- The state-poll snapshot extension covers 13 resolved 2024 presidential state
  outcomes from the preserved 538 polling-average snapshot on 2024-09-12.
- Poll margins are transformed to Republican-win probabilities with a
  documented normal-error model using a 3.8 percentage-point expected absolute
  poll error; raw poll shares are not used directly as probabilities.
- Polymarket has lower Brier loss in 8 of 13 state outcomes; the poll-derived
  probability has lower loss in 5 of 13.
- Mean Brier is 0.1336 for Polymarket and 0.1764 for the transformed
  poll-derived probabilities, with a mean Polymarket loss advantage of 0.0428
  Brier points.
- Together with the 8-case final-snapshot extension, the H1 supplementary
  checks now cover 21 resolved outcomes, 13 with lower Polymarket loss. These
  two supplementary checks remain methodologically separate.

Decision:

- Treat this as stronger H1 forecast-quality evidence and a concrete expansion
  toward the requested many-case comparison, but not as final proof of broad
  prediction-market superiority because the state cases share one election and
  the poll-derived probabilities depend on a documented model assumption.

Next step:

- Search for additional compatible probability forecasts or additional
  resolved non-US-election markets before making a broad scientific claim.

## 2026-06-10 - External Polymarket pipeline review

Goal context:

- Active project goal remains `goal-swiss-referendum-efficiency-001`.
- Reviewed `warproxxx/poly_data` as a possible read-only Polymarket data
  source for the current deterministic Swiss referendum pipeline.

Work performed:

- Read `GOAL.md` and confirmed exactly one active goal.
- Inspected the external GitHub repository README and cloned source in a
  temporary directory for static review.
- Checked the pipeline structure: Gamma market metadata collection, Polygon
  `OrderFilled` log collection, and processing to labeled trade CSV rows.
- Ran `python -m compileall -q .` in the temporary clone.

Findings:

- The repository is useful as a design reference for read-only on-chain fill
  collection and market metadata joining.
- It is not a drop-in replacement for the current Swiss referendum comparison,
  because the current project needs bounded poll-window snapshots and outputs
  without wallet addresses.
- The external pipeline writes maker/taker addresses and trade-level rows, so
  it would need an aggregation and validation adapter before any thesis-facing
  artifact can use it.
- The external repository has a license inconsistency: README/LICENSE indicate
  GPL-3.0 while `pyproject.toml` declares MIT.

Decision:

- Do not vendor or invoke the external pipeline now.
- If trade-flow evidence becomes necessary, implement a small local adapter
  inspired by the architecture, with mocks, bounded windows, no raw wallet
  outputs, and project-native validation.

## 2026-06-10 - H1 poll-transform sensitivity surfaced in report

Goal context:

- Continued the H1 forecast-quality thread objective: improve the visual and
  numerical evidence for whether Polymarket shows lower Brier loss than
  traditional forecast or poll-derived benchmarks.
- `GOAL.md` still contains exactly one active project goal; this H1 work is
  an explicit thread-level continuation and does not activate agents, MCP, ML,
  database writes, or trading paths.

Work performed:

- Integrated `data/results/h1_state_poll_snapshot_sensitivity.csv` into
  `operations/project/build_dozenten_report.py`.
- Added the sensitivity figure
  `data/results/h1_state_poll_snapshot_sensitivity.png` to the report figure
  list.
- Updated `docs/research/RESEARCH_SPEC.md` so the H1 figure catalog and
  narrative describe the MAE sensitivity grid.
- Updated `tests/test_dozenten_report.py` to verify the rendered report
  includes the sensitivity figure and key numeric ranges.
- Regenerated the Dozentenbericht with
  `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report --docx-output docs\project\dozentenbericht_ba_thesis_h1_forecast_quality.docx`.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_snapshot_extension.py tests\test_dozenten_report.py -q`
  -> PASS, 7 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_snapshot_extension.py tests\test_h1_final_snapshot_extension.py tests\test_h1_expansion_readiness.py tests\test_h1_forecast_quality.py tests\test_h1_evidence_scope.py tests\test_dozenten_report.py -q`
  -> PASS, 18 passed.
- Regenerated report has 15 figures and includes
  `h1_state_poll_snapshot_sensitivity.png`.
- Sensitivity PNG checked as nonblank: 2312x833 pixels, luma standard
  deviation 51.85.

Key output:

- The State-Poll extension base row remains 13 resolved state outcomes, with
  Polymarket lower loss in 8 of 13, mean Brier 0.1336 versus 0.1764 for the
  transformed poll-derived probabilities.
- The sensitivity grid spans MAE 2.0 to 10.0 percentage points across 12
  parameter rows.
- Polymarket keeps the lower mean Brier in every sensitivity row.
- The Polymarket lower-loss count ranges from 7 to 12 of 13 state outcomes,
  depending on the MAE assumption.

Decision:

- Treat this as stronger robustness evidence for the H1 state-poll extension,
  not as additional independent markets. The broader H1 objective remains
  active until additional compatible independent markets or forecast sources
  make the many-cases claim scientifically stronger.

## 2026-06-10 - H1 state-poll coverage audit added

Goal context:

- Continued the H1 forecast-quality objective by checking whether the
  state-poll extension can be expanded beyond 13 cases with existing public
  Polymarket markets and the preserved FiveThirtyEight polling-average
  snapshot.

Work performed:

- Probed public Polymarket Gamma event slugs for 2024 presidential state-winner
  markets.
- Confirmed that 47 of 50 US states have a curated Polymarket Republican-wins
  state market slug in the current audit set.
- Confirmed that the preserved FiveThirtyEight 2024-09-12 polling-average
  snapshot has REP/DEM rows for only the existing 13 states.
- Added `data/results/h1_state_poll_snapshot_coverage.csv` and
  `data/results/h1_state_poll_snapshot_coverage.png` to
  `operations/analysis/h1_state_poll_snapshot_extension.py`.
- Added coverage metadata fields to
  `data/results/h1_state_poll_snapshot_metadata.json`.
- Added the coverage figure and numeric coverage summary to the Dozentenbericht.
- Updated `docs/research/RESEARCH_SPEC.md` and focused tests.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_snapshot_extension.py -q`
  -> PASS, 8 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.h1_state_poll_snapshot_extension --source live`
  -> PASS, regenerated cases, sensitivity, coverage, figures, and metadata.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_snapshot_extension.py tests\test_dozenten_report.py -q`
  -> PASS, 9 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report --docx-output docs\project\dozentenbericht_ba_thesis_h1_forecast_quality.docx`
  -> PASS, 16 report figures.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_snapshot_extension.py tests\test_h1_final_snapshot_extension.py tests\test_h1_expansion_readiness.py tests\test_h1_forecast_quality.py tests\test_h1_evidence_scope.py tests\test_dozenten_report.py -q`
  -> PASS, 20 passed.
- `data/results/h1_state_poll_snapshot_coverage.png` inspected as nonblank:
  2244x833 pixels, luma standard deviation 48.97.

Key output:

- State universe audited: 50 US states.
- Curated Polymarket Republican-wins state markets: 47.
- States with REP/DEM rows in the preserved 538 polling-average snapshot: 13.
- Valid H1 state-poll Brier pairs: 13.
- Excluded because 538 snapshot poll rows are missing: 34.
- Excluded because both source classes are missing in the audit set: 3.

Decision:

- Do not expand the Brier case count to 47 without compatible poll-derived
  probability inputs. The coverage audit improves scientific transparency but
  does not complete the broader many-cases H1 objective.

## 2026-06-10 - H1 Rieke 50-state forecast extension integrated

Goal context:

- Continued the active H1 forecast-quality objective by adding a broader
  poll-based state forecast comparator and by correcting the state-poll coverage
  audit after all 50 Polymarket state markets were identified.

Work performed:

- Added and regenerated the Rieke 50-state forecast extension outputs:
  `data/results/h1_rieke_state_forecast_cases.csv`,
  `data/results/h1_rieke_state_forecast_summary.csv`,
  `data/results/h1_rieke_state_forecast.png`, and
  `data/results/h1_rieke_state_forecast_metadata.json`.
- Integrated the Rieke summary, figure, and limitation text into the
  Dozentenbericht markdown, HTML, and DOCX generation.
- Corrected the state-poll coverage interpretation from 47 Polymarket markets
  and 34 missing-poll exclusions to 50 Polymarket markets and 37 missing-poll
  exclusions.
- Updated `docs/research/RESEARCH_SPEC.md` with the Rieke figure, source
  artifacts, corrected coverage numbers, and the bounded interpretation.
- Updated report tests to assert the Rieke figure and the corrected coverage
  counts.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_rieke_state_forecast_extension.py tests\test_h1_state_poll_snapshot_extension.py tests\test_dozenten_report.py -q`
  -> PASS, 13 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_rieke_state_forecast_extension.py tests\test_h1_state_poll_snapshot_extension.py tests\test_h1_final_snapshot_extension.py tests\test_h1_expansion_readiness.py tests\test_h1_forecast_quality.py tests\test_h1_evidence_scope.py tests\test_dozenten_report.py -q`
  -> PASS, 24 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report --docx-output docs\project\dozentenbericht_ba_thesis_h1_forecast_quality.docx`
  -> PASS, 17 report figures.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 385 passed in 30.02s.
- `data/results/h1_rieke_state_forecast.png` inspected as nonblank and
  correctly labelled: aggregate mean Brier panel plus head-to-head lower-loss
  panel.

Key output:

- Rieke extension case count: 50 resolved 2024 presidential state outcomes.
- Polymarket mean Brier: 0.0262.
- Rieke mean Brier: 0.0296.
- Polymarket lower individual Brier loss: 12 of 50 states.
- Rieke lower individual Brier loss: 38 of 50 states.
- Corrected state-poll coverage: 50 US states audited, 50 Polymarket state
  markets, 13 valid 538 snapshot Brier pairs, and 37 exclusions due to missing
  538 snapshot poll rows.

Decision:

- The H1 evidence is stronger on aggregate forecast quality, but the Rieke
  extension does not prove that Polymarket is better in most state cases. The
  objective remains active because the scientifically strongest final claim
  still needs careful wording and, ideally, additional independent markets or
  compatible forecast sources beyond one election context.

## 2026-06-10 - External poly_data repository reviewed

Goal context:

- Reviewed `warproxxx/poly_data` as a possible read-only Polymarket data
  source for the active Swiss referendum comparison and future monitor inputs.

Work performed:

- Inspected the GitHub repository, README, package metadata, license, and
  Python source in a temporary clone outside the thesis workspace.
- Compared its V2 on-chain OrderFilled/Gamma market pipeline with the current
  local Swiss referendum Gamma snapshot and bounded CLOB price-history
  collectors.
- Checked that the external source compiles syntactically, while noting that it
  has no test suite or thesis-specific validation.

Decision:

- The pipeline is useful as a reference for public, read-only, trade-fill
  ingestion after Polymarket CLOB/CTF V2, especially for validating executed
  trade activity and aggregate volume around poll releases.
- It should not replace the current deterministic price/probability collectors.
  Any future use should be reimplemented or isolated behind our own tested
  validators, bounded windows, and wallet-address stripping before thesis-facing
  outputs.

## 2026-06-10 - H1 270toWin/JHK state forecast extension added

Goal context:

- Continued the active H1 forecast-quality objective by adding another
  traditional forecast comparator for the 2024 presidential state outcomes.

Work performed:

- Added `operations/analysis/h1_270towin_state_forecast_extension.py`.
- Added focused tests in
  `tests/test_h1_270towin_state_forecast_extension.py`.
- Generated deterministic local artifacts:
  `data/results/h1_270towin_state_forecast_cases.csv`,
  `data/results/h1_270towin_state_forecast_summary.csv`,
  `data/results/h1_270towin_state_forecast.png`, and
  `data/results/h1_270towin_state_forecast_metadata.json`.
- Integrated the new summary and figure into the Dozentenbericht generator,
  regenerated the markdown, HTML, and DOCX report, and updated the report test.
- Updated `docs/research/RESEARCH_SPEC.md` with the new H1 figure and artifact
  references.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_270towin_state_forecast_extension.py -q`
  -> PASS, 5 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_270towin_state_forecast_extension.py tests\test_dozenten_report.py -q`
  -> PASS, 6 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_270towin_state_forecast_extension.py tests\test_h1_rieke_state_forecast_extension.py tests\test_h1_state_poll_snapshot_extension.py tests\test_h1_final_snapshot_extension.py tests\test_h1_expansion_readiness.py tests\test_h1_forecast_quality.py tests\test_h1_evidence_scope.py tests\test_dozenten_report.py -q`
  -> PASS, 29 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report --docx-output docs\project\dozentenbericht_ba_thesis_h1_forecast_quality.docx`
  -> PASS, 18 report figures.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 390 passed in 31.68s.

Key output:

- 270toWin/JHK extension case count: 50 resolved 2024 presidential state
  outcomes.
- Exact 270toWin probability rows: 22.
- Censored `>99.9%` boundary rows: 28.
- Polymarket mean Brier: 0.0262.
- 270toWin/JHK mean Brier: 0.0306.
- Polymarket lower individual Brier loss: 9 of 50 states.
- 270toWin/JHK lower individual Brier loss: 40 of 50 states.
- One exact-probability state ties.

Decision:

- The 270toWin/JHK extension strengthens the aggregate H1 Brier evidence
  because Polymarket again has lower mean Brier loss against a traditional
  forecast source.
- It still does not prove that Polymarket is better in most state cases. The
  main defensible claim remains aggregate forecast-quality support, limited by
  one election context, censored safe-state source probabilities, and the
  missing exact 270toWin publication timestamp.

## 2026-06-10 - H1 forecast-quality synthesis added

Goal context:

- Continued the active H1 forecast-quality objective by consolidating the
  fragmented H1 evidence into one deterministic claim-audit table and figure.

Work performed:

- Added `operations/analysis/h1_forecast_quality_synthesis.py`.
- Added focused tests in `tests/test_h1_forecast_quality_synthesis.py`.
- Generated deterministic local artifacts:
  `data/results/h1_forecast_quality_synthesis.csv`,
  `data/results/h1_forecast_quality_synthesis.png`, and
  `data/results/h1_forecast_quality_synthesis_metadata.json`.
- Integrated the synthesis table and figure into the Dozentenbericht generator
  and regenerated markdown, HTML, and DOCX outputs.
- Updated `docs/research/RESEARCH_SPEC.md` so the Synthesis is the second H1
  core figure and so later figure references remain consistent.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_forecast_quality_synthesis.py -q`
  -> PASS, 3 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_forecast_quality_synthesis.py tests\test_dozenten_report.py -q`
  -> PASS, 4 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_forecast_quality_synthesis.py tests\test_h1_270towin_state_forecast_extension.py tests\test_h1_rieke_state_forecast_extension.py tests\test_h1_state_poll_snapshot_extension.py tests\test_h1_final_snapshot_extension.py tests\test_h1_expansion_readiness.py tests\test_h1_forecast_quality.py tests\test_h1_evidence_scope.py tests\test_dozenten_report.py -q`
  -> PASS, 32 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report --docx-output docs\project\dozentenbericht_ba_thesis_h1_forecast_quality.docx`
  -> PASS, 19 report figures.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 393 passed in 36.28s.

Key output:

- Evidence rows synthesized: 6.
- Rows with lower aggregate Polymarket mean Brier: 6 of 6.
- Rows where Polymarket has a majority of lower individual losses: 3 of 6.
- Rows supporting the broad many-cases completion claim: 0 of 6.

Decision:

- The improved visualization now states the H1 boundary directly: the current
  evidence supports lower aggregate Polymarket Brier across all current
  traditional-comparator rows, but it does not prove that Polymarket is better
  in most individual cases across a scientifically broad set.
- The user-requested completion condition remains unmet, so the H1 objective
  should remain active.

## 2026-06-10 - External `warproxxx/poly_data` repository reviewed

Goal context:

- User asked whether `https://github.com/warproxxx/poly_data` could improve
  Polymarket data analysis for the project.
- Active project goal remains the Swiss referendum efficiency comparison; no
  external code was integrated.

Work performed:

- Reviewed the GitHub README and cloned the repository into a temporary
  directory outside the thesis workspace for read-only inspection.
- Inspected `update.py`, `update_utils/update_markets.py`,
  `update_utils/update_chain.py`, `update_utils/process_live.py`,
  `poly_utils/utils.py`, `pyproject.toml`, and `LICENSE`.
- Compared the repository's full-market/on-chain trade backfill approach with
  the local bounded Gamma snapshot, CLOB price-history, and public activity
  collectors.

Key findings:

- The external pipeline fetches Gamma market metadata and decodes v2
  `OrderFilled` events directly from Polygon JSON-RPC, then joins them into
  labelled trade CSVs.
- It could be useful later as a reference for historical on-chain trade
  reconstruction, especially if the monitor or wallet-signal track needs
  fuller maker/taker orderflow than the public Data API returns.
- It is not a drop-in replacement for the active referendum pipeline, which
  intentionally uses bounded public snapshots and bounded price-history
  windows around curated poll releases.
- Direct reuse is risky because the repo has no visible tests, performs broad
  full-market backfills, exposes maker/taker wallet addresses in outputs, uses
  OS-dependent `tail`, and has a license inconsistency: README/LICENSE indicate
  GPL-3.0 while `pyproject.toml` declares MIT.

Decision:

- Do not vendor or import this pipeline now.
- If needed later, borrow only the design idea in a clean-room, project-native,
  tested, bounded collector that preserves the current read-only and
  no-order-instruction guardrails.

## 2026-06-10 - H1 calibration diagnostic added

Goal context:

- User asked to continue improving the H1 Polymarket forecast-quality baseline,
  especially calibration visualisation, until any claim about Polymarket
  outperforming polling sources is supported by numbers and correct figures.
- The active repository goal file still lists the Swiss referendum track, but
  this work followed the user's explicit H1 continuation request.

Work performed:

- Added `operations/analysis/h1_calibration_diagnostic.py`.
- Generated deterministic local artifacts:
  `data/results/h1_calibration_diagnostic_cases.csv`,
  `data/results/h1_calibration_diagnostic_bins.csv`,
  `data/results/h1_calibration_diagnostic_summary.csv`,
  `data/results/h1_calibration_diagnostic_pairwise.csv`,
  `data/results/h1_calibration_diagnostic.png`, and
  `data/results/h1_calibration_diagnostic_metadata.json`.
- Integrated the calibration diagnostic into the Dozentenbericht generator and
  regenerated Markdown, HTML, and DOCX report outputs.
- Updated `docs/research/RESEARCH_SPEC.md` so the calibration diagnostic is
  documented as Figure 2b and so the one-outcome daily reliability curve is no
  longer treated as the main calibration evidence.
- Added focused tests in `tests/test_h1_calibration_diagnostic.py` and updated
  `tests/test_dozenten_report.py`.

Key output:

- Forecast-case rows: 192.
- Forecast sources: 7.
- Nonempty fixed calibration bins: 26.
- Pairwise Polymarket-vs-traditional rows: 5.
- Rows with lower aggregate Polymarket mean Brier: 5 of 5.
- Rows where Polymarket has a majority of lower individual losses: 2 of 5.
- Rows supporting the broad many-cases completion claim: 0 of 5.
- In the 50-state diagnostic, Polymarket mean Brier is 0.0262, Rieke is 0.0296,
  and 270toWin/JHK is 0.0306. Fixed-bin ECE is 0.0838 for Polymarket, 0.0774
  for Rieke, and 0.0802 for 270toWin/JHK.

Decision:

- The new visualization fixes the weak calibration presentation by using
  resolved case artifacts instead of a repeated one-outcome daily reliability
  curve.
- The H1 evidence supports lower aggregate Polymarket Brier across the current
  pairwise rows, but it does not support a clear calibration win or the broad
  user-requested many-cases claim yet.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.h1_calibration_diagnostic`
  -> PASS, generated 192 forecast-case rows and 5 pairwise rows.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_calibration_diagnostic.py -q`
  -> PASS, 3 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_calibration_diagnostic.py tests\test_dozenten_report.py -q`
  -> PASS, 4 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_calibration_diagnostic.py tests\test_h1_forecast_quality_synthesis.py tests\test_h1_270towin_state_forecast_extension.py tests\test_h1_rieke_state_forecast_extension.py tests\test_h1_state_poll_snapshot_extension.py tests\test_h1_final_snapshot_extension.py tests\test_dozenten_report.py -q`
  -> PASS, 27 passed.

## 2026-06-10 - External Polymarket Pipeline Review

Goal context: `goal-swiss-referendum-efficiency-001`.

Reviewed `warproxxx/poly_data` at commit
`bda27941c0c7e1bab05539b9fd195dc567e85edc` as a possible Polymarket data
pipeline reference for the active thesis project.

Findings:

- The repository is a read-only Polymarket v2 data retriever using Gamma market
  metadata and Polygon `eth_getLogs` for CTF Exchange V2 `OrderFilled` events.
- It can be useful as a reference for future raw trade-tape collection, maker
  side interpretation, incremental block cursors, and token-to-market joins.
- It is not a drop-in replacement for the current bounded Swiss referendum
  comparison because it backfills all v2 order events and outputs maker/taker
  addresses and transaction hashes.
- Direct code reuse should be avoided unless the license inconsistency is
  resolved: `LICENSE` and README state GPL-3.0, while `pyproject.toml` states
  MIT.
- No code or data from the external repository was imported into this project.

## 2026-06-10 - H1 State-Date Panel Temporal Diagnostic

Goal context: user-requested continuation of H1 forecast-quality and
calibration baseline work.

Generated a temporal diagnostic for the H1 state-date poll panel so the large
poll-derived comparison is no longer only reported as one aggregate result.

Changed artifacts:

- Added `operations/analysis/h1_state_poll_panel_temporal_diagnostic.py`.
- Added `tests/test_h1_state_poll_panel_temporal_diagnostic.py`.
- Generated:
  - `data/results/h1_state_poll_panel_temporal_summary.csv`.
  - `data/results/h1_state_poll_panel_temporal_state_month.csv`.
  - `data/results/h1_state_poll_panel_temporal_claim_audit.csv`.
  - `data/results/h1_state_poll_panel_temporal_diagnostic.png`.
  - `data/results/h1_state_poll_panel_temporal_diagnostic_metadata.json`.
- Updated the Dozentenbericht generator and regenerated Markdown, HTML, and
  DOCX outputs.
- Updated `docs/research/RESEARCH_SPEC.md` with Figure 6c and the temporal
  interpretation.

Key output:

- Full panel remains negative for Polymarket: 360 of 1,720 rows lower loss for
  Polymarket, 1,360 for the poll-derived transformation; mean Brier 0.1595 vs
  0.1026.
- The temporal diagnostic identifies 2 Polymarket-supporting months:
  2024-08 and 2024-09.
- In those months, 280 of 387 rows have lower Polymarket loss and 107 have
  lower poll-derived loss; mean Brier is 0.1842 for Polymarket vs 0.2543 for
  the poll-derived transformation.

Decision:

- The late-window result gives a defensible "Polymarket better in many rows"
  subset, but it is conditioned on month-level diagnostics and does not prove
  the broad many-independent-cases claim.
- The H1 completion claim remains not proven because the full state-date panel
  still contradicts the strong Polymarket-better assertion.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.h1_state_poll_panel_temporal_diagnostic`
  -> PASS, generated 7 monthly rows and 3 claim-audit rows.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_panel_temporal_diagnostic.py -q`
  -> PASS, 3 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_panel_temporal_diagnostic.py tests\test_h1_state_poll_panel_extension.py tests\test_h1_forecast_quality_synthesis.py tests\test_dozenten_report.py -q`
  -> PASS, 10 passed.

## 2026-06-11 - External `warproxxx/poly_data` pipeline assessment

Scope:

- Inspected the external GitHub repository `warproxxx/poly_data` in a temporary
  clone.
- Compared its collector and processor shape with the active Swiss referendum
  Polymarket-vs-polls goal.

Findings:

- The repository implements a read-only Polymarket v2 data pipeline using Gamma
  market metadata, Polygon `OrderFilled` logs, and a trade-labeling join.
- The pipeline writes broad raw artifacts including market metadata, raw order
  fills, maker/taker wallet addresses, transaction hashes, prices, USD amounts,
  and trade direction.
- It is useful as a technical reference for on-chain trade reconstruction and
  possible future aggregate wallet-flow research.
- It should not be imported directly into the active Swiss referendum pipeline,
  because the active goal only needs bounded public snapshot and price-history
  artifacts and explicitly avoids raw wallet exposure, global chain backfills,
  unbounded live ingestion, and unvalidated external schemas.

Limitations:

- The inspected repository has no visible test suite.
- The README and code describe a long first-run backfill from the v2 genesis
  block, which is disproportionate for the current single-market referendum
  comparison.
- Licensing metadata is inconsistent: `pyproject.toml` declares MIT while the
  repository license file is GPL-3.0 text, so copying code into this project
  would require a license decision first.

Recommendation:

- Do not adopt `poly_data` as a project dependency now.
- Optionally create a later, isolated and tested adapter that reads only the
  exact referendum market token, aggregates trades into bounded time buckets,
  strips wallet addresses, validates output schemas, and writes deterministic
  local artifacts before analysis.

## 2026-06-11 - H1 poll decision matrix

Scope:

- Added a deterministic H1 poll-decision matrix that converts existing
  poll-related forecast-quality artifacts into a thesis-facing claim boundary.
- Integrated the new figure and summary into the Dozentenbericht and research
  specification.

Generated artifacts:

- `operations/analysis/h1_poll_decision_matrix.py`
- `tests/test_h1_poll_decision_matrix.py`
- `data/results/h1_poll_decision_matrix.csv`
- `data/results/h1_poll_decision_matrix_summary.csv`
- `data/results/h1_poll_decision_matrix.png`
- `data/results/h1_poll_decision_matrix_metadata.json`

Key output:

- Decision rows: 9.
- Robust bounded-yes rows: 2.
- Directional but not robust rows: 1.
- Mean-loss-only rows: 3.
- Counterexample rows: 2.
- Largest robust scope: `lte_120_days_low_middle_distance`.
- Largest robust scope Polymarket lower loss: 313 of 433 state-date rows
  (72.3 percent).
- Largest robust scope state-month support: 18 of 26 units, p=0.037759.
- Strongest robust scope: `lte_90_days_low_middle_distance`, 262 of 285 rows,
  p=0.0000076294.
- Calibration context: 5 of 5 pairwise rows support Polymarket in mean Brier,
  2 of 5 also support Polymarket by case majority.
- Full-panel counterexample: poll-derived lower loss in 1360 of 1720
  state-date rows.

Interpretation:

- The H1 poll evidence now has a clearer visual claim boundary. A bounded poll
  claim is ready for late low/middle poll-distance scopes.
- The broad many-cases or many-elections claim remains `not_proven` because
  full-panel and direct-poll case/state-majority counterexamples remain.

Figure:

- `data/results/h1_poll_decision_matrix.png` shows decision checks, poll-scope
  lower-loss counts, mean Brier support versus case support, and the final
  bounded/not-proven status.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.h1_poll_decision_matrix`
  -> PASS, regenerated CSV, PNG, and metadata outputs.
- `data/results/h1_poll_decision_matrix.png` inspected; figure is nonblank and
  readable after layout adjustment.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_poll_decision_matrix.py tests\test_dozenten_report.py -q`
  -> PASS, 4 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown/HTML/DOCX with 41 figures.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, full suite 462 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_panel_temporal_diagnostic.py tests\test_h1_state_poll_panel_extension.py tests\test_h1_state_poll_snapshot_extension.py tests\test_h1_calibration_diagnostic.py tests\test_h1_forecast_quality_synthesis.py tests\test_dozenten_report.py -q`
  -> PASS, 21 passed.

## 2026-06-10 - H1 State-Date Panel Forecast-Horizon Diagnostic

Goal context: user-requested continuation of H1 forecast-quality and
calibration baseline work.

Generated a forecast-horizon diagnostic for the H1 state-date poll panel. This
keeps the negative full-panel result visible while testing whether Polymarket's
advantage appears closer to election day.

Changed artifacts:

- Added `operations/analysis/h1_state_poll_panel_horizon_diagnostic.py`.
- Added `tests/test_h1_state_poll_panel_horizon_diagnostic.py`.
- Generated:
  - `data/results/h1_state_poll_panel_horizon_summary.csv`.
  - `data/results/h1_state_poll_panel_horizon_state_summary.csv`.
  - `data/results/h1_state_poll_panel_horizon_claim_audit.csv`.
  - `data/results/h1_state_poll_panel_horizon_diagnostic.png`.
  - `data/results/h1_state_poll_panel_horizon_diagnostic_metadata.json`.
- Updated the Dozentenbericht generator and regenerated Markdown, HTML, and
  DOCX outputs.
- Updated `docs/research/RESEARCH_SPEC.md` with Figure 6d and the horizon
  interpretation.

Key output:

- Full panel remains negative for Polymarket: 360 of 1,720 rows lower loss for
  Polymarket and 1,360 for the poll-derived transformation.
- The <=90-day forecast-horizon window supports Polymarket: 262 of 357 rows
  have lower Polymarket loss and 95 have lower poll-derived loss.
- In the <=90-day window, mean Brier is 0.1799 for Polymarket versus 0.2520
  for the poll-derived transformation.
- More than 90 days before election day, Polymarket has lower loss in only
  98 of 1,363 rows.

Decision:

- The horizon diagnostic makes the late-window Polymarket advantage more
  methodically interpretable than a month-only split.
- The H1 completion claim remains not proven because the full state-date panel
  still contradicts the broad Polymarket-better assertion and all panel rows
  repeat one election context.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.h1_state_poll_panel_horizon_diagnostic`
  -> PASS, generated 6 horizon rows and 3 claim-audit rows.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_panel_horizon_diagnostic.py -q`
  -> PASS, 3 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_panel_horizon_diagnostic.py tests\test_h1_state_poll_panel_temporal_diagnostic.py tests\test_h1_state_poll_panel_extension.py tests\test_h1_forecast_quality_synthesis.py tests\test_dozenten_report.py -q`
  -> PASS, 13 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_panel_horizon_diagnostic.py tests\test_h1_state_poll_panel_temporal_diagnostic.py tests\test_h1_state_poll_panel_extension.py tests\test_h1_state_poll_snapshot_extension.py tests\test_h1_calibration_diagnostic.py tests\test_h1_forecast_quality_synthesis.py tests\test_dozenten_report.py -q`
  -> PASS, 24 passed.

## 2026-06-10 - H1 <=90-Day State-Level Support Diagnostic

Goal context: user-requested continuation of H1 forecast-quality and
calibration baseline work.

Generated a state-level support diagnostic for the <=90-day forecast-horizon
window. This converts the repeated row-level Polymarket advantage into a
state-level count while keeping the shared election-context limitation.

Changed artifacts:

- Added `operations/analysis/h1_state_poll_panel_horizon_state_diagnostic.py`.
- Added `tests/test_h1_state_poll_panel_horizon_state_diagnostic.py`.
- Generated:
  - `data/results/h1_state_poll_panel_horizon_state_support.csv`.
  - `data/results/h1_state_poll_panel_horizon_state_support_summary.csv`.
  - `data/results/h1_state_poll_panel_horizon_state_support.png`.
  - `data/results/h1_state_poll_panel_horizon_state_support_metadata.json`.
- Updated the Dozentenbericht generator and regenerated Markdown, HTML, and
  DOCX outputs.
- Updated `docs/research/RESEARCH_SPEC.md` with Figure 6e and the state-level
  support interpretation.

Key output:

- In the <=90-day window, Polymarket has lower loss in 262 of 357 state-date
  rows and the poll-derived transformation in 95 rows.
- Aggregated to states, Polymarket has lower mean Brier in 8 of 13 states.
- Polymarket also has a majority of lower-loss rows in 8 of 13 states.
- Five of 13 states do not support Polymarket in this <=90-day window.

Decision:

- This is the strongest current H1 support statement because it is not only a
  repeated-row count; it also appears at the state aggregation level.
- The H1 completion claim remains not proven because all 13 states are still
  one election context and the full state-date panel remains negative for
  Polymarket.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.h1_state_poll_panel_horizon_state_diagnostic`
  -> PASS, generated 13 state-support rows and 13 summary rows.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_panel_horizon_state_diagnostic.py -q`
  -> PASS, 3 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_panel_horizon_state_diagnostic.py tests\test_h1_state_poll_panel_horizon_diagnostic.py tests\test_h1_state_poll_panel_temporal_diagnostic.py tests\test_dozenten_report.py -q`
  -> PASS, 10 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_panel_horizon_state_diagnostic.py tests\test_h1_state_poll_panel_horizon_diagnostic.py tests\test_h1_state_poll_panel_temporal_diagnostic.py tests\test_h1_state_poll_panel_extension.py tests\test_h1_state_poll_snapshot_extension.py tests\test_h1_calibration_diagnostic.py tests\test_h1_forecast_quality_synthesis.py tests\test_dozenten_report.py -q`
  -> PASS, 27 passed.

## 2026-06-10 - External poly_data Repository Review

Goal context: user-requested assessment of `warproxxx/poly_data` for possible
use in the Polymarket data pipeline.

Inspected the external repository at commit
`bda27941c0c7e1bab05539b9fd195dc567e85edc` in a temporary directory outside
the thesis workspace.

Findings:

- The repository collects Polymarket Gamma market metadata and Polygon
  CTF Exchange V2 `OrderFilled` logs, then joins them into trade-level CSVs.
- It is useful as a reference for future read-only on-chain trade-tape or
  wallet-signal collection.
- It is not a drop-in dependency for the active Swiss referendum comparison,
  which currently needs bounded snapshot and price-history artifacts without
  wallet-address exposure.
- Direct reuse would require local wrappers, mocks, validators, bounded
  windows, explicit raw-address handling, and license review before any code is
  copied or vendored.

Verification:

- `git ls-remote https://github.com/warproxxx/poly_data.git HEAD`
  -> `bda27941c0c7e1bab05539b9fd195dc567e85edc`.
- `git clone --depth 1 https://github.com/warproxxx/poly_data.git ...`
  -> PASS, repository inspected read-only from temp storage.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, status updated and project tests reported `408 passed`.

## 2026-06-10 - H1 <=90-Day Score-Quality Diagnostic

Goal context: user-requested continuation of H1 forecast-quality and
calibration baseline work.

Generated and integrated a score-quality diagnostic for the <=90-day
state-date poll-panel window. This uses the existing deterministic panel cases
and does not collect new external data.

Changed artifacts:

- Updated `operations/analysis/h1_state_poll_panel_near_window_quality.py`.
- Added `tests/test_h1_state_poll_panel_near_window_quality.py`.
- Generated:
  - `data/results/h1_state_poll_panel_near_window_quality_rows.csv`.
  - `data/results/h1_state_poll_panel_near_window_quality_bins.csv`.
  - `data/results/h1_state_poll_panel_near_window_quality_summary.csv`.
  - `data/results/h1_state_poll_panel_near_window_quality.png`.
  - `data/results/h1_state_poll_panel_near_window_quality_metadata.json`.
- Updated `operations/project/build_dozenten_report.py` and regenerated the
  Markdown, HTML, and DOCX report outputs.
- Updated `docs/research/RESEARCH_SPEC.md` with Figure 6f and the new
  score-quality interpretation.

Key output:

- The diagnostic contains 714 long-form forecast rows from 357 state-date
  cases and two forecast sources.
- Polymarket mean Brier is 0.1799 versus 0.2520 for the poll-derived
  transformation in the <=90-day window.
- Polymarket fixed-bin ECE is 0.3797 versus 0.4391 for the poll-derived
  transformation.
- Polymarket probability separation is 0.4560 versus 0.4366 for the
  poll-derived transformation.
- Lower-loss rows remain 262 for Polymarket versus 95 for the poll-derived
  transformation in the same <=90-day window.

Decision:

- This strengthens the late-window H1 forecast-quality statement because
  Polymarket is better on mean Brier, fixed-bin ECE, probability separation,
  lower-loss row counts, and 8 of 13 state aggregates.
- The H1 completion claim remains not proven because the full state-date panel
  is still negative for Polymarket and all rows share one election context.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.h1_state_poll_panel_near_window_quality`
  -> PASS, generated 714 forecast rows, 10 calibration-bin rows, and 2 summary
  rows.
- `data/results/h1_state_poll_panel_near_window_quality.png` inspected;
  figure is nonblank and labels are readable after annotation cleanup.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_panel_near_window_quality.py -q`
  -> PASS, 3 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_panel_near_window_quality.py tests\test_h1_state_poll_panel_horizon_state_diagnostic.py tests\test_dozenten_report.py -q`
  -> PASS, 7 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_panel_near_window_quality.py tests\test_h1_state_poll_panel_horizon_state_diagnostic.py tests\test_h1_state_poll_panel_horizon_diagnostic.py tests\test_h1_state_poll_panel_temporal_diagnostic.py tests\test_h1_state_poll_panel_extension.py tests\test_h1_state_poll_snapshot_extension.py tests\test_h1_calibration_diagnostic.py tests\test_h1_forecast_quality_synthesis.py tests\test_dozenten_report.py -q`
  -> PASS, 30 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, status updated and project tests reported `411 passed`.

## 2026-06-10 - External `warproxxx/poly_data` repository review

Context:

- Reviewed `https://github.com/warproxxx/poly_data` as a possible source of
  ideas for improving Polymarket data collection and analysis.
- Confirmed the active local goal remains
  `goal-swiss-referendum-efficiency-001`; the review was limited to
  read-only data-collection relevance for that goal.
- No external source code was copied into this repository.

Inspection:

- Temporarily cloned the external repository at commit
  `bda27941c0c7e1bab05539b9fd195dc567e85edc` outside the project workspace.
- Reviewed `README.md`, `update.py`, `update_utils/update_markets.py`,
  `update_utils/update_chain.py`, `update_utils/process_live.py`,
  `poly_utils/utils.py`, `pyproject.toml`, and `LICENSE`.
- The external pipeline fetches Gamma market metadata, reads Polygon
  `OrderFilled` events from the Polymarket CTF Exchange V2 contract, and writes
  local CSV artifacts.

Decision:

- The repository is useful as a technical reference for a future bounded
  read-only trade collector, especially for CTF Exchange V2 log decoding and
  market-token joins.
- It should not be adopted directly for the current Swiss referendum pipeline
  because it collects global trades, emits maker/taker wallet addresses, lacks
  local schema validation/tests, is not scoped to curated poll windows, and has
  a GPL/MIT license metadata inconsistency.
- Any reuse should be a clean-room, tested implementation limited to the exact
  market token IDs and poll-release block/time windows, with wallet columns
  dropped before project outputs.

Verification:

- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, status updated and project tests reported `411 passed`.

## 2026-06-10 - H1 claim-evidence audit

Context:

- Continued the active thread objective for H1 forecast quality and calibration:
  make the Polymarket-vs-polls claim auditable with numbers and correctly
  rendered visualizations.
- Kept the implementation deterministic and limited to precomputed H1 Python
  artifacts. No LLM, agent, MCP, ML, database write, RCP transformation, live
  collection, or raw trade/wallet data was used.

Changes:

- Added `operations/analysis/h1_claim_evidence_audit.py`.
- Added `tests/test_h1_claim_evidence_audit.py`.
- Generated:
  - `data/results/h1_claim_evidence_audit.csv`.
  - `data/results/h1_claim_evidence_audit_summary.csv`.
  - `data/results/h1_claim_evidence_audit.png`.
  - `data/results/h1_claim_evidence_audit_metadata.json`.
- Integrated the new audit summary and figure into
  `operations/project/build_dozenten_report.py`,
  `tests/test_dozenten_report.py`, and `docs/research/RESEARCH_SPEC.md`.
- Regenerated the Dozentenbericht Markdown, HTML, and DOCX outputs.

Key output:

- The claim audit contains 12 audit rows and 23 columns.
- 10 of 12 audit rows support a bounded Polymarket advantage.
- 1 audit row contradicts the strong Polymarket advantage claim: the full
  state-date poll panel has 360 Polymarket-lower-loss rows versus 1,360
  poll-derived-lower-loss rows.
- Among directly poll-related audit rows, 7 of 8 support bounded Polymarket
  claims, while the full state-date poll panel remains the counterexample.
- The <=90-day state-date window contains 357 rows; Polymarket has lower loss
  in 262 rows versus 95 for the poll-derived transformation.
- The broad user claim remains `not_proven` / `0` because the largest
  poll-derived panel contradicts it and the supportive late-window evidence is
  still repeated rows from one election context.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.h1_claim_evidence_audit`
  -> PASS, generated 12 audit rows, 13 summary rows, a PNG figure, and
  metadata with `h1_goal_completion_status=not_proven`.
- `data/results/h1_claim_evidence_audit.png` inspected; figure is nonblank and
  labels are readable.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown/HTML/DOCX with 26 figures.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_claim_evidence_audit.py -q`
  -> PASS, 3 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_claim_evidence_audit.py tests\test_dozenten_report.py -q`
  -> PASS, 4 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_claim_evidence_audit.py tests\test_h1_state_poll_panel_near_window_quality.py tests\test_h1_state_poll_panel_horizon_state_diagnostic.py tests\test_h1_state_poll_panel_horizon_diagnostic.py tests\test_h1_state_poll_panel_temporal_diagnostic.py tests\test_h1_state_poll_panel_extension.py tests\test_h1_state_poll_snapshot_extension.py tests\test_h1_calibration_diagnostic.py tests\test_h1_forecast_quality_synthesis.py tests\test_dozenten_report.py -q`
  -> PASS, 33 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, status updated and project tests reported `414 passed`.

## 2026-06-10 - H1 popular-vote counterexample extension

Context:

- Continued the H1 forecast-quality thread with a new resolved 2024 outcome:
  the Polymarket market for Trump winning the national popular vote.
- Kept the implementation deterministic, read-only, and bounded. The module
  reads local FiveThirtyEight Trump/Harris poll shares, fetches public
  Polymarket Gamma/CLOB history when run with `--source live`, applies an
  explicit poll-margin probability transform in Python, and writes local CSV,
  PNG, and metadata artifacts. No wallet, order, RCP, LLM, agent, MCP, ML, or
  database write path was used.

Changes:

- Added `operations/analysis/h1_popular_vote_extension.py`.
- Added `tests/test_h1_popular_vote_extension.py`.
- Generated:
  - `data/results/h1_popular_vote_cases.csv`.
  - `data/results/h1_popular_vote_summary.csv`.
  - `data/results/h1_popular_vote.png`.
  - `data/results/h1_popular_vote_metadata.json`.
- Integrated the popular-vote summary into:
  - `operations/analysis/h1_forecast_quality_synthesis.py`.
  - `operations/analysis/h1_claim_evidence_audit.py`.
  - `operations/project/build_dozenten_report.py`.
  - `docs/research/RESEARCH_SPEC.md`.
  - `tests/test_h1_forecast_quality_synthesis.py`.
  - `tests/test_h1_claim_evidence_audit.py`.
  - `tests/test_dozenten_report.py`.
- Regenerated the H1 synthesis, claim-audit, and Dozentenbericht artifacts.

Key output:

- The popular-vote extension contains 51 matched national daily rows and 1
  resolved outcome.
- Polymarket has lower Brier loss in 21 of 51 rows; the transformed
  poll-derived probability has lower loss in 30 of 51 rows.
- Mean Brier is 0.517859 for Polymarket versus 0.482440 for the transformed
  poll-derived probability.
- The H1 synthesis now has 8 evidence rows: 6 support Polymarket on aggregate
  mean Brier, 3 support Polymarket by majority of individual cases, and 0
  prove the broad many-cases claim.
- The claim audit now has 13 rows: 10 bounded support rows, 2 rows
  contradicting the strong claim, and `h1_goal_completion_status=not_proven`.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_popular_vote_extension.py -q`
  -> PASS, 5 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.h1_popular_vote_extension --source live`
  -> PASS, generated 51 rows and the PNG/metadata outputs.
- `data/results/h1_popular_vote.png`, `data/results/h1_forecast_quality_synthesis.png`,
  and `data/results/h1_claim_evidence_audit.png` inspected; figures are
  nonblank and labels are readable.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_popular_vote_extension.py tests\test_h1_forecast_quality_synthesis.py tests\test_h1_claim_evidence_audit.py tests\test_dozenten_report.py -q`
  -> PASS, 12 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown/HTML/DOCX with 27 figures.

## 2026-06-10 - External poly_data repository assessment

Context:

- Reviewed `warproxxx/poly_data` as a possible Polymarket data pipeline input
  for the thesis project.
- Kept the review outside the project workspace by cloning the repository into
  a temporary inspection directory only.
- Checked the active project goal before review; exactly one active goal remains
  in `GOAL.md`.

Assessment:

- The external repository is useful as a reference for read-only Polymarket
  market metadata collection and CTF Exchange V2 `OrderFilled` event decoding.
- It is not a drop-in dependency for the current deterministic Swiss referendum
  comparison or H1 forecast-quality work because it produces trade-level and
  wallet-address data, depends on a Polygon RPC backfill, has no local tests,
  and has a license mismatch between `LICENSE` and `pyproject.toml`.
- No code from the external repository was copied into the thesis project.

## 2026-06-10 - H1 margin-threshold readiness audit

Context:

- Continued the H1 forecast-quality objective by checking whether additional
  Polymarket Trump state-margin threshold markets can responsibly expand the
  poll-derived H1 comparison.
- Kept the work deterministic and read-only. The module reads official
  FiveThirtyEight preserved polling averages, public Gamma event metadata, and
  public CLOB price-history windows. It does not compute new Brier scores,
  does not write a database, and does not use wallet, order, LLM, agent, MCP,
  ML, or RCP paths.

Changes:

- Added `operations/analysis/h1_margin_threshold_readiness.py`.
- Added `tests/test_h1_margin_threshold_readiness.py`.
- Generated:
  - `data/results/h1_margin_threshold_readiness.csv`.
  - `data/results/h1_margin_threshold_readiness.png`.
  - `data/results/h1_margin_threshold_readiness_metadata.json`.
- Integrated the figure and key numbers into:
  - `operations/project/build_dozenten_report.py`.
  - `tests/test_dozenten_report.py`.
  - `docs/research/RESEARCH_SPEC.md`.
- Regenerated the Dozentenbericht Markdown/HTML/DOCX artifacts.

Key output:

- 7 Polymarket Trump state-margin threshold markets were reviewed.
- 4 markets have compatible preserved 538 state polling-average rows.
- 0 markets have CLOB history inside the preserved official 538
  polling-average window.
- 0 markets are currently compatible for H1 Brier scoring.
- 4 candidates are blocked by no temporal overlap; 3 are blocked by missing
  preserved 538 state-poll rows.
- The audit therefore adds 0 new H1 Brier rows and keeps the broad H1 claim
  unproven.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_margin_threshold_readiness.py -q`
  -> PASS, 3 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.h1_margin_threshold_readiness --source live`
  -> PASS, generated 7 readiness rows and the PNG/metadata outputs.
- `data/results/h1_margin_threshold_readiness.png` inspected; figure is
  nonblank and labels are readable.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_margin_threshold_readiness.py tests\test_dozenten_report.py -q`
  -> PASS, 4 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown/HTML/DOCX with 28 figures.

## 2026-06-10 - H1 270toWin polling-average extension

Context:

- Continued the explicit H1 forecast-quality follow-up by adding another
  direct poll-derived state comparison.
- Kept the work deterministic and read-only. Live mode fetches only the public
  270toWin 2024 polling-average JSON endpoint. Polymarket probabilities are
  read from the existing local 50-state snapshot artifact; no Polymarket live
  endpoint, wallet, order, LLM, agent, MCP, ML, database write, or RCP path is
  used.
- The polling averages are not used as probabilities directly. Republican
  minus Democratic polling margins are transformed with the documented
  normal-error model already used in the H1 state-poll extension.

Changes:

- Added `operations/analysis/h1_270towin_poll_average_extension.py`.
- Added `tests/test_h1_270towin_poll_average_extension.py`.
- Generated:
  - `data/results/h1_270towin_poll_average_cases.csv`.
  - `data/results/h1_270towin_poll_average_summary.csv`.
  - `data/results/h1_270towin_poll_average.png`.
  - `data/results/h1_270towin_poll_average_metadata.json`.
- Integrated the new summary into:
  - `operations/analysis/h1_forecast_quality_synthesis.py`.
  - `operations/analysis/h1_claim_evidence_audit.py`.
  - `operations/project/build_dozenten_report.py`.
  - `docs/research/RESEARCH_SPEC.md`.
  - The related focused tests.
- Regenerated the H1 synthesis, H1 claim audit, and Dozentenbericht artifacts.

Key output:

- 270toWin endpoint rows inspected: 49.
- 50-state polling-average rows retained: 43.
- Matched state Brier cases: 43.
- Missing 50-state polling-average rows: 7.
- Polymarket lower individual Brier loss: 14 of 43 cases.
- 270toWin poll-derived probability lower individual Brier loss: 29 of 43
  cases.
- Mean Brier Polymarket: 0.0304.
- Mean Brier transformed 270toWin polling average: 0.0416.
- Mean loss advantage: 0.0112 Brier points in Polymarket's favour.
- Updated H1 synthesis: 7 of 9 evidence rows support Polymarket by aggregate
  mean Brier, 3 of 9 support Polymarket by case majority, and 0 of 9 prove the
  broad many-cases claim.
- Updated H1 claim audit: 11 of 14 rows support bounded Polymarket evidence, 2
  contradict the strong claim, and the broad user claim remains `not_proven`.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_270towin_poll_average_extension.py`
  -> PASS, 5 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.h1_270towin_poll_average_extension --source live`
  -> PASS, generated 43 matched state cases and the PNG/metadata outputs.
- `data/results/h1_270towin_poll_average.png` inspected; figure is nonblank and
  readable.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_270towin_poll_average_extension.py tests\test_h1_forecast_quality_synthesis.py tests\test_h1_claim_evidence_audit.py tests\test_dozenten_report.py`
  -> PASS, 12 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown/HTML/DOCX with 29 figures.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, `427 passed in 39.77s`.

## 2026-06-10 - External poly_data repository assessment

Context:

- Reviewed `warproxxx/poly_data` as a candidate Polymarket data pipeline for
  this project after the user asked whether it could improve Polymarket data
  analysis.
- Kept the assessment read-only. The external repository was cloned only into a
  temporary directory and no external code was imported into this repository.
- Confirmed the active project context still has exactly one active goal in
  `GOAL.md`.

Findings:

- The external repository is a compact v2 Polymarket trade-data pipeline:
  Gamma keyset market metadata, direct Polygon JSON-RPC `OrderFilled` log
  backfill, and a processor that joins raw order events to market metadata.
- It appears to use public read-only data paths only. No authenticated trading,
  order placement, cancellation, signature, or wallet-credential path was found
  in the reviewed files.
- It could be useful as a reference for future raw trade reconstruction,
  maker/taker direction handling, token-to-market joins, and post-hoc
  wallet/trade research once deterministic thesis outputs permit that scope.
- It is not suitable to vendor or run as-is for the active Swiss referendum
  track because it performs unbounded all-v2 trade backfills, writes raw
  maker/taker addresses, lacks local tests, uses current-working-directory
  relative paths, retries forever on rate limits, and has a license mismatch:
  `LICENSE`/README indicate GPL-3.0 while `pyproject.toml` says MIT.
- For current project use, the safer path is selective reimplementation of
  small ideas behind our existing bounded, tested, read-only collector
  interfaces rather than importing the package.

Verification:

- Inspected the upstream README and source files from a temporary clone.
- Checked for tests, authenticated endpoints, order-placement/cancellation
  paths, and license indicators.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, `427 passed in 37.86s`.

## 2026-06-10 - H1 state-source consensus diagnostic

Context:

- Continued the explicit H1 forecast-quality objective by improving the
  state-level visualization and audit boundary for Polymarket versus
  poll-derived or poll-model comparator sources.
- The new diagnostic reads only existing deterministic H1 state-level case
  artifacts and does not collect live data, query a database, use LLMs, agents,
  MCP, ML, wallet fields, order fields, or raw poll shares.
- The diagnostic is not counted as a new independent H1 evidence source because
  it re-aggregates existing state artifacts from one 2024 presidential election
  context.

Changes:

- Added `operations/analysis/h1_state_source_consensus.py`.
- Added `tests/test_h1_state_source_consensus.py`.
- Generated:
  - `data/results/h1_state_source_consensus_cases.csv`.
  - `data/results/h1_state_source_consensus_state_summary.csv`.
  - `data/results/h1_state_source_consensus_summary.csv`.
  - `data/results/h1_state_source_consensus.png`.
  - `data/results/h1_state_source_consensus_metadata.json`.
- Integrated the consensus summary into:
  - `operations/analysis/h1_claim_evidence_audit.py`.
  - `operations/project/build_dozenten_report.py`.
  - `tests/test_h1_claim_evidence_audit.py`.
  - `tests/test_dozenten_report.py`.
  - `docs/research/RESEARCH_SPEC.md`.
- Regenerated the H1 claim audit and Dozentenbericht artifacts.

Key output:

- Source-state comparisons: 156.
- Comparator sources: 4.
- Covered resolved state outcomes: 50.
- Source-state lower-loss rows: Polymarket 43, comparators 112, ties 1.
- Mean Brier across source-state rows: Polymarket 0.0363, comparators 0.0455.
- All-source state consensus: Polymarket 9 states, comparators 37 states,
  ties 4 states.
- Direct poll-transform source-state rows: Polymarket 22, comparators 34.
- States covered by both direct poll-transform sources: 13.
- Two-direct-source state consensus: Polymarket 8 states, comparators 4
  states, tie 1 state.
- Updated H1 claim audit: 12 of 16 audit rows support bounded Polymarket
  evidence, 3 contradict the strong claim, 9 of 11 direct poll-related rows
  support bounded Polymarket evidence, and the broad many-cases claim remains
  `not_proven`.

Interpretation:

- The new figure makes the current H1 boundary clearer. Polymarket has lower
  mean Brier in the re-aggregated state-source rows, but the all-source
  state-majority consensus favours traditional comparator sources in most
  states.
- The narrower two-direct-poll-transform subset still supports Polymarket in
  8 of 13 states.
- This is useful H1 evidence, but it does not prove the requested broad
  many-cases claim because the all-source consensus and the larger state-date
  poll panel remain counterexamples.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_source_consensus.py -q`
  -> PASS, 3 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.h1_state_source_consensus`
  -> PASS, generated 156 source-state rows and the PNG/metadata outputs.
- `data/results/h1_state_source_consensus.png` inspected; figure is nonblank
  and readable.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_source_consensus.py tests\test_h1_claim_evidence_audit.py tests\test_dozenten_report.py -q`
  -> PASS, 7 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown/HTML/DOCX with 30 figures.
- `data/results/h1_claim_evidence_audit.png` inspected; figure is nonblank and
  readable.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, `430 passed in 38.62s`.

## 2026-06-11 - H1 competitive-state diagnostic

Context:

- Continued the explicit H1 forecast-quality objective by testing where the
  state-source result is conditional on source competitiveness.
- The diagnostic uses only existing deterministic H1 state-source artifacts.
  It does not collect live data, query a database, use LLMs, agents, MCP, ML,
  wallet fields, order fields, or raw poll shares.
- Competitiveness tiers are derived from the observed comparator probability
  distance to 0.5 with quantiles, not arbitrary thresholds.

Changes:

- Added `operations/analysis/h1_competitive_state_diagnostic.py`.
- Added `tests/test_h1_competitive_state_diagnostic.py`.
- Generated:
  - `data/results/h1_competitive_state_diagnostic_cases.csv`.
  - `data/results/h1_competitive_state_diagnostic_tiers.csv`.
  - `data/results/h1_competitive_state_diagnostic_summary.csv`.
  - `data/results/h1_competitive_state_diagnostic.png`.
  - `data/results/h1_competitive_state_diagnostic_metadata.json`.
- Integrated the diagnostic into:
  - `operations/analysis/h1_claim_evidence_audit.py`.
  - `operations/project/build_dozenten_report.py`.
  - `tests/test_h1_claim_evidence_audit.py`.
  - `tests/test_dozenten_report.py`.
  - `docs/research/RESEARCH_SPEC.md`.
- Regenerated the H1 claim audit and Dozentenbericht artifacts.

Key output:

- Input source-state comparisons: 156 across 50 states.
- Lowest-distance all-source tercile: Polymarket lower loss in 35 of 52
  source-state cases, comparators lower loss in 17 of 52, mean loss advantage
  0.0284 Brier points.
- Lowest-distance direct poll-transform tercile: Polymarket lower loss in 18
  of 19 source-state cases, poll-derived comparators lower loss in 1 of 19,
  mean loss advantage 0.0567 Brier points.
- Highest-distance all-source tercile: Polymarket lower loss in 0 of 40
  source-state cases, comparators lower loss in 40 of 40.
- Updated H1 claim audit: 14 of 19 audit rows support bounded Polymarket
  evidence, 4 contradict the strong claim, 10 of 12 direct poll-related rows
  support bounded Polymarket evidence, and the broad many-cases claim remains
  `not_proven`.

Interpretation:

- The new figure supports a bounded statement: Polymarket is better in the
  most competitive lowest-distance state-source subset, especially among
  direct poll-transform cases.
- It does not prove the broad user claim. Safer/high-distance states remain a
  strong counterexample, and all rows still come from one election context.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_competitive_state_diagnostic.py tests\test_h1_claim_evidence_audit.py tests\test_dozenten_report.py -q`
  -> PASS, 7 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.h1_competitive_state_diagnostic`
  -> PASS, generated 156 diagnostic cases and the PNG/metadata outputs.
- `.\.venv\Scripts\python.exe -m operations.analysis.h1_claim_evidence_audit`
  -> PASS, regenerated 19 audit rows, the summary, figure, and metadata.
- `data/results/h1_competitive_state_diagnostic.png` inspected; figure is
  nonblank and readable.
- `data/results/h1_claim_evidence_audit.png` inspected after layout update;
  figure is nonblank and readable.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown/HTML/DOCX with 31 figures.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, `433 passed in 44.92s`.

## 2026-06-11 - H1 state-date competitiveness x horizon diagnostic

Context:

- Continued the explicit H1 forecast-quality objective by improving the
  largest poll-derived H1 panel visualization.
- The new diagnostic uses only existing deterministic H1 state-date panel
  rows. It does not collect live data, query a database, use LLMs, agents,
  MCP, ML, wallet fields, order fields, or raw poll shares.
- Competitiveness tiers are derived from the observed poll-derived probability
  distance to 0.5 with quantiles, not arbitrary thresholds.

Changes:

- Added `operations/analysis/h1_state_poll_panel_competitiveness_diagnostic.py`.
- Added `tests/test_h1_state_poll_panel_competitiveness_diagnostic.py`.
- Generated:
  - `data/results/h1_state_poll_panel_competitiveness_grid.csv`.
  - `data/results/h1_state_poll_panel_competitiveness_state.csv`.
  - `data/results/h1_state_poll_panel_competitiveness_summary.csv`.
  - `data/results/h1_state_poll_panel_competitiveness.png`.
  - `data/results/h1_state_poll_panel_competitiveness_metadata.json`.
- Integrated the diagnostic into:
  - `operations/analysis/h1_claim_evidence_audit.py`.
  - `operations/project/build_dozenten_report.py`.
  - `tests/test_h1_claim_evidence_audit.py`.
  - `tests/test_dozenten_report.py`.
  - `docs/research/RESEARCH_SPEC.md`.
- Regenerated the H1 claim audit and Dozentenbericht artifacts.

Key output:

- Input panel rows: 1,720 state-date forecast rows across 15 states.
- Late window: 357 rows in the <=90-day pre-election window.
- Late low/middle poll-distance terciles: Polymarket lower loss in 262 of 285
  state-date rows, poll-derived lower loss in 23 of 285, mean loss advantage
  0.0933 Brier points.
- Late low/middle poll-distance state support: Polymarket has a lower-loss
  majority in 9 of 9 covered states.
- Late high poll-distance tercile: Polymarket lower loss in 0 of 72
  state-date rows, poll-derived lower loss in 72 of 72.
- Updated H1 claim audit: 15 of 21 audit rows support bounded Polymarket
  evidence, 5 contradict the strong claim, 11 of 14 direct poll-related rows
  support bounded Polymarket evidence, and the broad many-cases claim remains
  `not_proven`.

Interpretation:

- The new figure gives a stronger and cleaner bounded result: in late
  competitive or semi-competitive poll-derived state-date rows, Polymarket is
  lower-loss in most rows and all covered states.
- It still does not complete the broad user claim. The full state-date panel,
  late high-distance rows, and high-distance state-source cases remain
  counterexamples, and the panel rows repeat one election context.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_panel_competitiveness_diagnostic.py tests\test_h1_claim_evidence_audit.py tests\test_dozenten_report.py -q`
  -> PASS, 6 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.h1_state_poll_panel_competitiveness_diagnostic`
  -> PASS, generated 1,720 panel diagnostic rows and the PNG/metadata outputs.
- `.\.venv\Scripts\python.exe -m operations.analysis.h1_claim_evidence_audit`
  -> PASS, regenerated 21 audit rows, the summary, figure, and metadata.
- `data/results/h1_state_poll_panel_competitiveness.png` inspected; figure is
  nonblank and readable.
- `data/results/h1_claim_evidence_audit.png` inspected after label update;
  figure is nonblank and readable.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown/HTML/DOCX with 32 figures.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, `435 passed in 40.44s`.

## 2026-06-11 - H1 state-level significance diagnostic

Context:

- Continued the explicit H1 forecast-quality objective by checking whether the
  strong late low/middle poll-distance panel result also holds when each state
  is treated as one diagnostic unit.
- The new diagnostic reads only the existing deterministic
  `h1_state_poll_panel_competitiveness_state.csv` artifact. It does not
  collect live data, query a database, use LLMs, agents, MCP, ML, wallet
  fields, order fields, or raw poll shares.
- The exact binomial test is implemented in Python and interpreted only as a
  bounded state-as-unit diagnostic because all states come from one election
  context.

Changes:

- Added `operations/analysis/h1_state_poll_panel_state_significance.py`.
- Added `tests/test_h1_state_poll_panel_state_significance.py`.
- Generated:
  - `data/results/h1_state_poll_panel_state_significance.csv`.
  - `data/results/h1_state_poll_panel_state_significance_summary.csv`.
  - `data/results/h1_state_poll_panel_state_significance.png`.
  - `data/results/h1_state_poll_panel_state_significance_metadata.json`.
- Integrated the diagnostic into:
  - `operations/analysis/h1_claim_evidence_audit.py`.
  - `operations/project/build_dozenten_report.py`.
  - `tests/test_h1_claim_evidence_audit.py`.
  - `tests/test_dozenten_report.py`.
  - `docs/research/RESEARCH_SPEC.md`.
- Regenerated the H1 claim audit and Dozentenbericht artifacts.

Key output:

- Late low/middle poll-distance state scope: Polymarket has lower-loss
  majority support in 9 of 9 states.
- Exact one-sided binomial p-value for Polymarket state-majority support:
  0.001953125.
- Exact 95 percent lower confidence bound for the Polymarket state-support
  share: 0.7169.
- Late high poll-distance state scope: poll-derived probabilities have
  lower-loss majority support in 5 of 5 states; this remains a bounded
  counterexample.
- Updated H1 claim audit: 16 of 22 audit rows support bounded Polymarket
  evidence, 5 contradict the strong claim, 12 of 15 direct poll-related rows
  support bounded Polymarket evidence, and the broad many-cases claim remains
  `not_proven`.

Interpretation:

- This materially strengthens the bounded late competitive-poll result:
  Polymarket is not only lower-loss in 262 of 285 repeated rows, but also in
  all 9 covered states when states are used as the diagnostic unit.
- It still does not complete the broad user claim. The test is not a
  many-independent-elections proof, and high-distance state scopes still
  support poll-derived comparators.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_panel_state_significance.py -q`
  -> PASS, 3 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.h1_state_poll_panel_state_significance`
  -> PASS, generated the exact sign-test CSV, summary, PNG, and metadata.
- `data/results/h1_state_poll_panel_state_significance.png` inspected; figure
  is nonblank and readable.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_state_poll_panel_state_significance.py tests\test_h1_claim_evidence_audit.py tests\test_dozenten_report.py -q`
  -> PASS, 7 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.h1_claim_evidence_audit`
  -> PASS, regenerated 22 audit rows, the summary, figure, and metadata.
- `data/results/h1_claim_evidence_audit.png` inspected; figure is nonblank
  and readable with the new `<=90d sign` audit scope.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown/HTML/DOCX with 33 figures.

## 2026-06-11 - H1 direct poll outlier robustness diagnostic

Context:

- Continued the H1 forecast-quality objective by checking whether the positive
  direct poll state-cluster mean is driven by one or a few exceptional states.
- Kept the work deterministic: Python only, no live data collection, no
  database writes, no LLM metrics, no agents/MCP, no ML, no wallet fields, and
  no order endpoints.

Changes:

- Added `operations/analysis/h1_direct_poll_outlier_robustness.py`.
- Generated:
  - `data/results/h1_direct_poll_outlier_robustness_scenarios.csv`
  - `data/results/h1_direct_poll_outlier_robustness_summary.csv`
  - `data/results/h1_direct_poll_outlier_robustness.png`
  - `data/results/h1_direct_poll_outlier_robustness_metadata.json`
- Added `tests/test_h1_direct_poll_outlier_robustness.py`.
- Integrated the result into `operations/project/build_dozenten_report.py`,
  `tests/test_dozenten_report.py`, and `docs/research/RESEARCH_SPEC.md`.
- Regenerated the Dozentenbericht artifacts.

Key output:

- Direct poll state clusters: 43.
- Full equal-state mean loss advantage: 0.0122 Brier points.
- Minimum leave-one-state-out mean: 0.0095 after removing Wisconsin.
- All 43 leave-one-state-out means remain positive.
- The mean remains positive after removing the top 6 positive state
  contributions and first turns non-positive after removing 7, at -0.0001.
- Largest positive state contribution: Wisconsin, 0.1248 Brier points.

Interpretation:

- The bounded direct poll mean-loss advantage is not created by a single state.
- The advantage is still concentrated in the largest positive state
  contributions, so this strengthens robustness of the mean-loss statement but
  does not prove a state-majority, many-election, or broad many-cases claim.
- The H1 objective remains incomplete because the user-requested broad claim
  still needs stronger independent evidence or a narrower thesis claim.

Figure:

- `data/results/h1_direct_poll_outlier_robustness.png` shows leave-one-state-out
  means, top-k positive-state exclusions, state-level contributions, and the
  bounded interpretation.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.h1_direct_poll_outlier_robustness`
  -> PASS, regenerated CSV, PNG, and metadata outputs.
- `data/results/h1_direct_poll_outlier_robustness.png` inspected; figure is
  nonblank and readable.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_direct_poll_outlier_robustness.py -q`
  -> PASS, 3 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown/HTML/DOCX with 38 figures.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_direct_poll_outlier_robustness.py tests\test_h1_direct_poll_state_cluster_diagnostic.py tests\test_h1_direct_poll_loss_decomposition.py tests\test_dozenten_report.py -q`
  -> PASS, 10 passed.

## 2026-06-11 - H1 robust poll-scope unit quality diagnostic

Context:

- Continued the H1 forecast-quality objective by reducing dependence on
  repeated state-date rows in the two robust late low/middle poll-distance
  scopes.
- Kept the work deterministic: Python only, no live data collection, no
  database writes, no LLM metrics, no agents/MCP, no ML, no wallet fields, and
  no order endpoints.

Changes:

- Added `operations/analysis/h1_robust_poll_scope_unit_quality.py`.
- Generated `data/results/h1_robust_poll_scope_unit_quality_units.csv`,
  `data/results/h1_robust_poll_scope_unit_quality_summary.csv`,
  `data/results/h1_robust_poll_scope_unit_quality.png`, and
  `data/results/h1_robust_poll_scope_unit_quality_metadata.json`.
- Added `tests/test_h1_robust_poll_scope_unit_quality.py`.
- Integrated the result into `operations/project/build_dozenten_report.py`,
  `tests/test_dozenten_report.py`, and `docs/research/RESEARCH_SPEC.md`.
- Regenerated the Dozentenbericht artifacts.

Key output:

- Unit rows: 116; summary rows: 8.
- Largest robust scope (`<=120 days` plus low/middle poll distance):
  Polymarket support in 10 of 11 states, 18 of 26 state-month units, and
  20 of 26 state-horizon units. State-month exact one-sided p-value:
  0.037759; median state-month Brier advantage: 0.048385.
- Strongest robust scope (`<=90 days` plus low/middle poll distance):
  Polymarket support in 9 of 9 states, 17 of 17 state-month units, and
  17 of 17 state-horizon units. State-month exact one-sided p-value:
  0.0000076294; median state-month Brier advantage: 0.072312.
- Broad H1 claim status remains `not_proven`.

Interpretation:

- The robust late low/middle poll-distance H1 finding remains visible after
  aggregation to less repeated units.
- This strengthens the bounded statement that Polymarket is better in those
  robust scoped cases, but it still does not prove a broad many-elections or
  general many-cases claim.

Figure:

- `data/results/h1_robust_poll_scope_unit_quality.png` shows unit support,
  state-month paired Brier scatter, unit advantage distribution, and bounded
  interpretation.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.h1_robust_poll_scope_unit_quality`
  -> PASS, regenerated CSV, PNG, and metadata outputs.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_robust_poll_scope_unit_quality.py tests\test_h1_robust_poll_scope_quality.py tests\test_dozenten_report.py -q`
  -> PASS, 7 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown/HTML/DOCX with 43 figures.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 468 passed in 46.25s.

## 2026-06-11 - Swiss referendum bounded live refresh after H1 commit

Context:

- Committed the completed H1 forecast-quality diagnostic block as
  `b91f9bf feat: add h1 forecast quality diagnostics`.
- Moved to the active Phase 11 Swiss referendum comparison after H1 intensive
  work.
- Ran one manual bounded read-only Polymarket refresh. No background daemon,
  authenticated endpoint, order path, trading credential, LLM, agent, MCP, ML,
  database write, causal claim, tradeability claim, profitability claim, or
  mispricing proof was used.

Generated or updated:

- `data/results/swiss_referendum_10mio_polymarket_snapshots.csv`
- `data/results/swiss_referendum_10mio_comparison.csv`
- `data/results/swiss_referendum_10mio_latest_source_comparison.csv`
- `data/results/swiss_referendum_10mio_poll_impacts.csv`
- `data/results/swiss_referendum_10mio_information_response.csv`
- `data/results/swiss_referendum_10mio_efficiency.png`
- `data/results/swiss_referendum_10mio_dashboard.html`
- `data/results/swiss_referendum_10mio_latest_summary.md`
- `data/results/swiss_referendum_10mio_refresh_metadata.json`
- `data/results/swiss_referendum_10mio_running_status.json`

Key output:

- Snapshot rows: 19.
- Comparison rows: 19.
- Bounded price-history rows: 504.
- Poll-impact rows: 7, all `observed_pre_post`.
- Information-response rows: 7.
- Latest local Polymarket Yes probability: 0.23.
- Latest matched poll: `srg_gfs_bern_2026_w2`.
- Latest poll Yes share: 0.45.
- Raw Yes gap: -0.22.
- Decided-voter Yes gap: -0.2339175258.
- Latest divergence label: `polymarket_below_poll_yes_share`.
- Running status: all outputs exist; snapshot recency status `fresh`.

Interpretation:

- The latest local Polymarket probability is below the latest curated poll Yes
  share and below the decided-voter normalization.
- This is a descriptive poll-proxy comparison only. It does not prove
  undervaluation, overvaluation, inefficiency, causality, tradeability, or
  profitability.

Figure:

- `data/results/swiss_referendum_10mio_efficiency.png` shows the latest
  Polymarket probability against curated poll shares from the local artifacts.

Verification:

- `.\.venv\Scripts\python.exe -m operations.collectors.swiss_referendum_refresh --source live`
  -> PASS, generated one bounded live snapshot and regenerated local outputs.
- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_polymarket.py tests\test_swiss_referendum_history.py tests\test_swiss_referendum_efficiency.py tests\test_swiss_referendum_refresh.py -q`
  -> PASS, 27 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 468 passed in 52.45s.

## 2026-06-11 - H1 robust poll-scope quality diagnostic

Context:

- Continued the H1 forecast-quality objective by adding a score-quality view
  for the robust late low/middle poll-distance scopes identified by the
  poll-scope frontier and decision matrix.
- Kept the work deterministic: Python only, no live data collection, no
  database writes, no LLM metrics, no agents/MCP, no ML, no wallet fields, and
  no order endpoints.

Changes:

- Added and regenerated `operations/analysis/h1_robust_poll_scope_quality.py`.
- Generated `data/results/h1_robust_poll_scope_quality_rows.csv`,
  `data/results/h1_robust_poll_scope_quality_bins.csv`,
  `data/results/h1_robust_poll_scope_quality_summary.csv`,
  `data/results/h1_robust_poll_scope_quality_pairwise.csv`,
  `data/results/h1_robust_poll_scope_quality.png`, and
  `data/results/h1_robust_poll_scope_quality_metadata.json`.
- Added `tests/test_h1_robust_poll_scope_quality.py`.
- Integrated the result into `operations/project/build_dozenten_report.py`,
  `tests/test_dozenten_report.py`, and `docs/research/RESEARCH_SPEC.md`.
- Regenerated the Dozentenbericht artifacts.

Key output:

- Robust scopes covered: 2.
- Forecast rows: 1436, from 718 source-scope state-date cases.
- Largest robust scope (`<=120 days` plus low/middle poll distance):
  Polymarket lower loss in 313 of 433 rows, mean Brier 0.1982 vs
  poll-derived 0.2555, fixed-bin ECE 0.3868 vs 0.4251, probability separation
  0.2182 vs 0.1394.
- Strongest robust scope (`<=90 days` plus low/middle poll distance):
  Polymarket lower loss in 262 of 285 rows, mean Brier 0.2214 vs
  poll-derived 0.3147, fixed-bin ECE 0.4523 vs 0.5362.
- The strongest robust scope has only positive outcomes, so probability
  separation is not defined there.

Interpretation:

- The robust bounded poll scopes now have direct forecast-quality evidence:
  Polymarket has lower mean Brier and lower fixed-bin ECE in both selected
  robust scopes, plus higher probability separation in the largest robust
  scope where both outcome classes occur.
- This strengthens the bounded statement that Polymarket is better in robust
  late low/middle poll-distance scopes.
- It still does not complete the broad user claim because the full panel and
  high-distance subsets remain counterexamples, and the robust scopes reuse
  state-date rows from one election context.

Figure:

- `data/results/h1_robust_poll_scope_quality.png` shows score bars,
  calibration bins for the largest robust scope, lower-loss counts, and a
  statement box with the bounded status.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.h1_robust_poll_scope_quality`
  -> PASS, regenerated CSV, PNG, and metadata outputs.
- `data/results/h1_robust_poll_scope_quality.png` inspected; figure is
  nonblank and readable after the reliability panel and footer were revised.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_robust_poll_scope_quality.py tests\test_dozenten_report.py -q`
  -> PASS, 4 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown/HTML/DOCX with 42 figures.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, `465 passed in 45.98s`.

## 2026-06-11 - External poly_data repository assessment

Context:

- Reviewed `warproxxx/poly_data` after the user asked whether its Polymarket
  v2 data pipeline would be useful for the thesis project.
- Kept the assessment read-only: no live data collection, no database writes,
  no authenticated endpoints, no order placement/cancellation, no runtime
  agents, no MCP use, no LLM metric calculation, and no raw table dumps.

Findings:

- The repository is useful as a design reference for direct Polygon
  `OrderFilled` ingestion and Gamma market metadata joining.
- It is not suitable for direct adoption into the active deterministic pipeline
  without a local wrapper, fixtures, schema validation, bounded windows, and
  aggregate-only outputs.
- Key risks are raw maker/taker wallet-address columns, CSV-only persistence,
  no local tests in the reviewed repository, long RPC backfills, a Windows
  portability issue in the resume logic, and a license mismatch between the
  GPL README/LICENSE and the MIT `pyproject.toml` metadata.

Verification:

- `GOAL.md` checked; exactly one project goal remains active.
- External repository cloned to a temporary directory for inspection only.
- `python -m compileall -q $env:TEMP\poly_data_review` -> PASS.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, `462 passed in 47.97s`.

## 2026-06-11 - H1 poll-scope frontier diagnostic

Context:

- Continued the H1 forecast-quality objective by testing how far the
  Polymarket-supporting poll-comparison scope can be widened before
  counterexamples dominate.
- Kept the work deterministic: Python only, no live data collection, no
  database writes, no LLM metrics, no agents/MCP, no ML, no wallet fields, and
  no order endpoints.

Changes:

- Added `operations/analysis/h1_poll_scope_frontier.py`.
- Generated `data/results/h1_poll_scope_frontier.csv`,
  `data/results/h1_poll_scope_frontier_summary.csv`,
  `data/results/h1_poll_scope_frontier.png`, and
  `data/results/h1_poll_scope_frontier_metadata.json`.
- Added `tests/test_h1_poll_scope_frontier.py`.
- Integrated the result into `operations/project/build_dozenten_report.py`,
  `tests/test_dozenten_report.py`, and `docs/research/RESEARCH_SPEC.md`.
- Regenerated the Dozentenbericht artifacts.

Key output:

- Frontier rows: 30 horizon-by-poll-distance scopes.
- Robust-support scopes: 8.
- Largest robust scope: `lte_120_days_low_middle_distance`.
- Largest robust scope row result: Polymarket lower loss in 313 of 433
  state-date rows, poll-derived lower loss in 120 rows.
- Largest robust scope unit result: 18 of 26 state-month units support
  Polymarket, exact one-sided p-value 0.03775934875011444.
- Strongest robust scope: `lte_90_days_low_middle_distance`, 285 rows, 17 of
  17 state-month units, exact one-sided p-value 0.00000762939453125.
- Boundary: `lte_90_days_all_distances` has Polymarket row support in 262 of
  357 rows, but state-month p-value 0.07579481601715088.
- Full panel remains a counterexample: Polymarket lower loss in 360 of 1720
  rows, poll-derived lower loss in 1360 of 1720 rows.

Interpretation:

- The bounded poll-comparison statement can be widened from the strongest
  <=90-day low/middle-distance scope to a largest robust <=120-day
  low/middle-distance scope.
- The high-distance and full-panel counterexamples remain visible, so the
  broad many-cases or many-elections claim remains `not_proven`.
- This supports more precise H1 thesis wording, not a general calibration win,
  causal claim, tradeability claim, or independent many-election proof.

Figure:

- `data/results/h1_poll_scope_frontier.png` shows row-support and state-month
  support heatmaps, robust scopes by coverage, and the bounded conclusion.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.h1_poll_scope_frontier`
  -> PASS, regenerated CSV, PNG, summary, and metadata outputs.
- `data/results/h1_poll_scope_frontier.png` inspected; figure is nonblank,
  readable, and shows the boundary conditions.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown/HTML/DOCX with 40 figures.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_poll_scope_frontier.py tests\test_dozenten_report.py -q`
  -> PASS, 4 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, updated `STATUS.md` and recorded `459 passed in 49.57s`.

## 2026-06-11 - External review of warproxxx/poly_data

Context:

- Reviewed `https://github.com/warproxxx/poly_data` as a possible Polymarket
  data-collection reference for the active Swiss referendum comparison goal.
- No project code, deterministic outputs, database tables, or local data
  artifacts were changed for this assessment, except this workflow log and the
  required status refresh.
- Kept the review within current project guardrails: no trading, no order
  placement or cancellation, no authenticated channels, no LLM metric
  calculation, no runtime agents/MCP, no ML, and no database writes.

Assessment:

- The repository is potentially useful as a reference for a future read-only
  trade-level collector because it combines Gamma market metadata with Polygon
  CTF Exchange V2 `OrderFilled` events and produces labeled trade CSVs.
- It is not a drop-in fit for the current Swiss referendum track because our
  active pipeline intentionally uses bounded Gamma/CLOB snapshots without
  wallet addresses, whereas `poly_data` writes raw maker/taker wallet fields.
- The highest-value reusable ideas are keyset market pagination, resumable
  block cursors, event decoding, token-to-market joining, and bounded chunked
  processing.
- Any adoption should be by re-implementing a small, tested, thesis-scoped
  collector behind our existing validators and metadata contracts, not by
  vendoring or invoking the full upstream pipeline.

Risks:

- The repository has no test files in the reviewed checkout.
- License metadata is inconsistent: the repository contains a GPL-3.0 license
  file while `pyproject.toml` declares MIT.
- Full-chain backfill is operationally heavy and RPC-dependent; the README
  notes that initial chain backfill can take hours on public RPC.
- Raw wallet-level outputs are outside the current referendum comparison output
  contract unless explicitly scoped, minimized, validated, and documented.

Verification:

- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, `STATUS.md` updated, full pytest summary `456 passed in 46.69s`.
- Cloned the external repository into a temporary directory only and inspected
  README, `pyproject.toml`, `update.py`, `update_utils/update_markets.py`,
  `update_utils/update_chain.py`, `update_utils/process_live.py`, and
  `poly_utils/utils.py`.

## 2026-06-11 - External poly_data usefulness reassessment

Context:

- Reassessed `https://github.com/warproxxx/poly_data` after the user asked
  whether that pipeline would help this project analyse Polymarket data better.
- Confirmed `GOAL.md` still has exactly one active goal:
  `goal-swiss-referendum-efficiency-001`.
- The external repository was cloned only into a temporary directory and no
  external code was imported into this repository.

Findings:

- `poly_data` v2 collects Gamma market metadata, reads Polygon CTF Exchange V2
  `OrderFilled` logs through JSON-RPC, and joins the result into labelled trade
  CSVs.
- This is useful as a reference for future fill-level trade reconstruction,
  especially after the Polymarket v2 contract migration.
- It is not a drop-in improvement for the active Swiss referendum comparison,
  which needs bounded probability snapshots and bounded CLOB history around
  curated poll releases rather than broad maker/taker wallet-level backfills.
- Direct dependency or vendoring is unattractive because the repository has
  GPL-3.0 licensing in `LICENSE` and README while `pyproject.toml` declares MIT.

Recommendation:

- Do not add `poly_data` as a dependency now.
- Keep the active pipeline on the existing tested Gamma/CLOB collectors.
- If future H3 or monitor work needs fill-level data, reimplement a small
  internal read-only collector with bounded block windows, validation, metadata,
  mocks, and explicit wallet-address scope.

Verification:

- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, `450 passed in 44.56s`.

## 2026-06-11 - External poly_data repository assessment

Context:

- Reviewed `https://github.com/warproxxx/poly_data` as a possible source of
  Polymarket data-pipeline ideas for the current deterministic Polymarket
  analysis work.
- The repository was cloned to a temporary directory outside this project and
  was not imported, executed against live endpoints, or added as a dependency.

Findings:

- `poly_data` v2 fetches Gamma market metadata, reads CTF Exchange V2
  `OrderFilled` events directly from Polygon JSON-RPC, and joins them into
  labelled trade CSVs.
- The useful gap for this thesis project is historical on-chain trade coverage
  after Polymarket's 2026 v2 contract migration, especially if we later need
  transaction-level trade reconstruction beyond the public Data API rows.
- It is not a drop-in replacement for the existing collectors because our
  active pipeline already validates bounded Gamma/CLOB snapshots, keeps
  Swiss-referendum windows scoped to curated poll timestamps, and writes
  metadata/validation reports.
- The reviewed repo has no tests in the cloned source, writes broad CSVs
  directly, uses unbounded retry loops for rate limits, depends on external RPC
  availability, exposes wallet addresses in trade outputs, and has inconsistent
  license metadata (`LICENSE`/README GPL-3.0, `pyproject.toml` MIT).

Interpretation:

- Treat `poly_data` as a reference implementation for a future, narrowly scoped
  read-only on-chain trade collector, not as a pipeline to vendor or run inside
  the thesis project.
- Any adoption should reimplement only the deterministic primitives we need:
  bounded block-window collection, explicit validation, provenance metadata,
  mock fixtures, tests, no order endpoints, and no automated interpretation
  layer.

Verification:

- `python -m compileall -q .` inside the temporary clone -> PASS.
- No tests or test directories were found in the cloned repository.

## 2026-06-11 - H1 direct poll loss decomposition

Context:

- Continued the persistent H1 forecast-quality objective by improving the
  thesis-facing explanation of direct Polymarket-vs-poll comparisons.
- The existing state-source consensus showed a mixed result: Polymarket has
  lower aggregate mean Brier in direct poll-transform rows, but poll-derived
  comparators win more individual source-state cases.
- The change uses only existing deterministic H1 artifacts and does not collect
  live data, query raw tables, use LLMs, agents, MCP, ML, wallet fields, order
  endpoints, or database writes.

Changes:

- Added `operations/analysis/h1_direct_poll_loss_decomposition.py`.
- Added `tests/test_h1_direct_poll_loss_decomposition.py`.
- Generated:
  - `data/results/h1_direct_poll_loss_decomposition_cases.csv`
  - `data/results/h1_direct_poll_loss_decomposition_summary.csv`
  - `data/results/h1_direct_poll_loss_decomposition.png`
  - `data/results/h1_direct_poll_loss_decomposition_metadata.json`
- Integrated the new result into `operations/project/build_dozenten_report.py`
  and `tests/test_dozenten_report.py`.
- Documented Figure 2f in `docs/research/RESEARCH_SPEC.md`.

Key output:

- Direct poll-transform source-state cases: 56.
- Polymarket lower-loss cases: 22 of 56.
- Poll-derived lower-loss cases: 34 of 56.
- Mean Brier: Polymarket 0.0544 versus poll-derived 0.0729.
- Polymarket-winning cases have mean Brier advantage 0.0498.
- Poll-derived winning cases have mean absolute Brier advantage 0.0018.
- Total Polymarket-winning margin is 18.2 times the total poll-derived winning
  margin.
- Bounded late poll-panel context remains: Polymarket 262 of 285 state-date
  rows and 17 of 17 state-month units.

Interpretation:

- The new artifact explains the aggregate Brier advantage without hiding the
  case-count boundary. Polymarket's direct poll-transform advantage comes from
  fewer but much larger avoided poll losses.
- This strengthens the forecast-quality visualization and result narrative, but
  it does not complete the broad user objective. The direct case-majority claim
  and broad many-elections claim remain `not_proven`.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.h1_direct_poll_loss_decomposition`
  -> PASS, generated new CSV, PNG, and metadata artifacts.
- `data/results/h1_direct_poll_loss_decomposition.png` inspected; figure is
  nonblank and readable.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_direct_poll_loss_decomposition.py -q`
  -> PASS, 3 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown/HTML/DOCX with 36 figures.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_direct_poll_loss_decomposition.py tests\test_dozenten_report.py -q`
  -> PASS, 4 passed.

## 2026-06-11 - H1 direct poll state-cluster diagnostic

Context:

- Continued the persistent H1 forecast-quality objective by testing whether
  the direct poll-transform aggregate loss advantage survives state-level
  clustering.
- The previous direct-poll decomposition showed a lower aggregate mean Brier
  for Polymarket, but poll-derived comparators won more individual
  source-state rows.
- The change uses only existing deterministic H1 direct-poll artifacts and does
  not collect live data, query raw tables, use LLMs, agents, MCP, ML, wallet
  fields, order endpoints, or database writes.

Changes:

- Added `operations/analysis/h1_direct_poll_state_cluster_diagnostic.py`.
- Added `tests/test_h1_direct_poll_state_cluster_diagnostic.py`.
- Generated:
  - `data/results/h1_direct_poll_state_cluster_diagnostic_states.csv`
  - `data/results/h1_direct_poll_state_cluster_diagnostic_summary.csv`
  - `data/results/h1_direct_poll_state_cluster_diagnostic.png`
  - `data/results/h1_direct_poll_state_cluster_diagnostic_metadata.json`
- Integrated the new state-cluster result into the Dozentenbericht and report
  tests.
- Documented Figure 2g in `docs/research/RESEARCH_SPEC.md`.

Key output:

- Input direct poll-transform source-state cases: 56.
- State clusters: 43.
- Equal-state mean loss advantage: 0.0122 Brier points for Polymarket.
- Deterministic state-cluster bootstrap 95 percent interval: 0.0041 to 0.0217.
- Deterministic sign-flip p-value for positive equal-state mean: 0.00455.
- State mean lower-loss count: Polymarket 13 of 43 states, poll-derived 30 of
  43 states.
- Exact one-sided binomial p-value for poll-derived state-count support:
  0.00686.

Interpretation:

- The direct poll-transform aggregate advantage remains visible after
  equal-weight state clustering, so the mean-loss evidence is not only a raw
  source-state-row artifact.
- The state-count majority still favours poll-derived comparators. This keeps
  the bounded claim honest: Polymarket has a positive mean-loss advantage in
  this direct poll diagnostic, but a broad state-majority or many-elections
  claim remains `not_proven`.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.h1_direct_poll_state_cluster_diagnostic`
  -> PASS, generated state, summary, PNG, and metadata artifacts.
- `data/results/h1_direct_poll_state_cluster_diagnostic.png` inspected; figure
  is nonblank and readable.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_direct_poll_state_cluster_diagnostic.py -q`
  -> PASS, 3 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown/HTML/DOCX with 37 figures.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_direct_poll_state_cluster_diagnostic.py tests\test_h1_direct_poll_loss_decomposition.py tests\test_dozenten_report.py -q`
  -> PASS, 7 passed.

## 2026-06-11 - H1 poll-comparison result integrated into report

Context:

- Continued the explicit H1 forecast-quality objective by turning the focused
  poll-comparison scorecard into a reportable thesis artifact.
- The work uses only existing deterministic H1 artifacts. It does not collect
  data, query a database, use LLMs, agents, MCP, ML, wallet fields, order
  fields, or raw table dumps.

Changes:

- Polished `data/results/h1_poll_comparison_result.png` so the primary count
  labels have more right-side plot space.
- Updated `operations/project/build_dozenten_report.py` to read
  `h1_poll_comparison_result_summary.csv` and expose the focused H1
  poll-comparison result in Markdown, HTML, DOCX, appendix artifacts, and the
  figure list.
- Updated `tests/test_dozenten_report.py` to assert the new figure, headline,
  primary count, state-level count, full-panel counterexample, and
  `not_proven` status.
- Updated `docs/research/RESEARCH_SPEC.md` with Figure 2d, artifact links,
  evidence-to-cite entries, and a bounded result interpretation.

Key output:

- `h1_poll_comparison_result.csv` contains 6 result rows.
- Primary bounded scope: Polymarket lower loss in 262 of 285 late low/middle
  poll-distance state-date rows, versus poll-derived lower loss in 23.
- State-as-unit confirmation: Polymarket support in 9 of 9 states, exact
  one-sided binomial p-value 0.001953125, exact 95 percent lower bound 0.7169.
- Direct poll audit ledger: 12 of 15 directly poll-related audit rows support
  bounded Polymarket evidence.
- Counterexamples remain explicit: the full state-date poll panel supports
  poll-derived probabilities in 1360 of 1720 rows, and the late high-distance
  subset supports poll-derived probabilities in 72 of 72 rows.

Interpretation:

- The report can now state a bounded H1 poll-comparison result: Polymarket is
  better in the late low/middle poll-distance scope and in all 9 covered states
  under that diagnostic.
- The broad user objective is still not proven because the full panel and
  high-distance subset contradict a general Polymarket-better claim.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.h1_poll_comparison_result`
  -> PASS, regenerated result CSV, summary CSV, PNG, and metadata.
- `data/results/h1_poll_comparison_result.png` inspected; figure is nonblank
  and readable with the bounded statement and counterexamples separated.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown/HTML/DOCX with 34 figures.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_poll_comparison_result.py tests\test_dozenten_report.py -q`
  -> PASS, 4 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, `441 passed in 42.07s`.

## 2026-06-11 - H1 poll-comparison unit robustness

Context:

- Continued the H1 forecast-quality objective by reducing dependence on
  repeated state-date rows in the primary poll-comparison result.
- The work reads only `h1_state_poll_panel_cases.csv` and reuses the existing
  deterministic horizon bins plus quantile-derived poll-distance terciles.
- It does not collect external data, query a database, use LLMs, agents, MCP,
  ML, wallet fields, order fields, fixed competitiveness thresholds, or raw
  table dumps.

Changes:

- Added `operations/analysis/h1_poll_comparison_unit_robustness.py`.
- Added `tests/test_h1_poll_comparison_unit_robustness.py`.
- Generated:
  - `data/results/h1_poll_comparison_unit_robustness_units.csv`.
  - `data/results/h1_poll_comparison_unit_robustness_summary.csv`.
  - `data/results/h1_poll_comparison_unit_robustness.png`.
  - `data/results/h1_poll_comparison_unit_robustness_metadata.json`.
- Integrated the robustness summary and figure into
  `operations/project/build_dozenten_report.py`.
- Updated `tests/test_dozenten_report.py`.
- Updated `docs/research/RESEARCH_SPEC.md` with Figure 2e, artifact links,
  and the bounded interpretation.

Key output:

- The robustness table contains 255 unit rows.
- In the primary late low/middle poll-distance scope, Polymarket is supported
  in:
  - 262 of 285 state-date rows,
  - 9 of 9 states,
  - 17 of 17 state-month units,
  - 17 of 17 state-horizon units,
  - 4 of 4 horizon-tier units.
- Boundaries remain explicit:
  - full-panel state-month units support poll-derived probabilities in 61 of
    80 units,
  - late high-distance state-month units support poll-derived probabilities in
    8 of 8 units.

Interpretation:

- This strengthens the bounded H1 poll-comparison statement because the
  primary Polymarket result survives aggregation beyond daily rows.
- It still does not complete the broad user objective: all unit aggregations
  remain within one election context, and the full panel plus high-distance
  subset are counterexamples.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.h1_poll_comparison_unit_robustness`
  -> PASS, regenerated unit CSV, summary CSV, PNG, and metadata.
- `data/results/h1_poll_comparison_unit_robustness.png` inspected; figure is
  nonblank and separates primary support from boundary counterexamples.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown/HTML/DOCX with 35 figures.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_poll_comparison_result.py tests\test_h1_poll_comparison_unit_robustness.py tests\test_dozenten_report.py -q`
  -> PASS, 7 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, `444 passed in 43.03s`.

## 2026-06-11 - H1 unit-robustness exact sign tests

Context:

- Continued the H1 forecast-quality objective by adding exact sign-test
  diagnostics to the unit-robustness artifact.
- This keeps the robust 17/17 State-Month result from being only a count. It
  now has deterministic p-values and exact lower confidence bounds in the same
  style as the existing state-level H1 significance diagnostic.

Changes:

- Updated `operations/analysis/h1_poll_comparison_unit_robustness.py` to add
  exact one-sided binomial p-values and exact 95 percent lower bounds for
  primary unit-support counts, plus exact poll-derived p-values for the late
  high-distance boundary scope.
- Updated `tests/test_h1_poll_comparison_unit_robustness.py`.
- Regenerated `data/results/h1_poll_comparison_unit_robustness.*`.
- Updated `operations/project/build_dozenten_report.py` and
  `tests/test_dozenten_report.py` so the Dozentenbericht reports the
  State-Month p-value and confidence lower bound.
- Updated `docs/research/RESEARCH_SPEC.md` with the new p-values and exact
  lower bound.

Key output:

- Primary State-Month support remains Polymarket 17 of 17.
- Exact one-sided State-Month binomial p-value: 0.0000076294.
- Exact 95 percent lower confidence bound for the State-Month support share:
  0.8384.
- Late high-distance State-Month boundary remains poll-derived 8 of 8 with
  exact one-sided p-value 0.00390625.

Interpretation:

- The bounded H1 poll-comparison statement is now supported by row counts,
  coarser unit counts, and exact sign-test diagnostics on the State-Month
  aggregation.
- The broad user objective remains unproven because the units are still from
  one election context and the full-panel/high-distance boundaries remain
  counterexamples.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.h1_poll_comparison_unit_robustness`
  -> PASS, regenerated unit robustness artifacts.
- `data/results/h1_poll_comparison_unit_robustness.png` inspected; figure is
  nonblank and the p-value text fits inside the statement box.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown/HTML/DOCX with 35 figures.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_poll_comparison_result.py tests\test_h1_poll_comparison_unit_robustness.py tests\test_dozenten_report.py -q`
  -> PASS, 7 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, `444 passed in 40.74s`.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, `438 passed in 46.69s`.

## 2026-06-11 - External poly_data pipeline usefulness review

Context:

- Evaluated `warproxxx/poly_data` as a possible Polymarket data-source
  reference for the active deterministic analysis work.
- Inspected the public GitHub repository and cloned the current `main` branch
  into a temporary directory for read-only code review. No external pipeline
  code was imported into this repository.
- Confirmed that the repository implements a Polymarket v2 trade ingestion
  flow, not a forecast-quality or poll-comparison pipeline.

Inspected:

- README and repository metadata.
- `update.py`.
- `update_utils/update_markets.py`.
- `update_utils/update_chain.py`.
- `update_utils/process_live.py`.
- `poly_utils/utils.py`.
- `pyproject.toml` and `LICENSE`.

Assessment:

- Useful as a technical reference for future read-only on-chain trade
  ingestion, especially `OrderFilled` log decoding, market-token joins,
  resumable cursors, and missing-token backfill.
- Not suitable for direct adoption in the active Swiss referendum comparison
  because the current goal needs bounded market snapshots and bounded
  price-history windows, while `poly_data` performs broad on-chain trade
  backfill and emits maker/taker wallet-address-level data.
- Direct code reuse is also unattractive because the repository carries GPL-3.0
  licensing in `LICENSE` and README while `pyproject.toml` declares MIT, so
  any reuse would need license review and likely clean-room reimplementation of
  only the relevant concepts.

Recommendation:

- Do not add `poly_data` as a dependency.
- Keep the active Swiss referendum pipeline based on existing bounded
  Gamma/CLOB collectors.
- If later H3 or monitor work needs trade-level data, implement a small,
  tested, read-only internal collector that borrows the idea of Polygon
  `OrderFilled` log ingestion but writes validated bounded artifacts and keeps
  wallet-address exposure explicitly scoped.

Verification:

- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, `438 passed in 49.52s`.

## 2026-06-11 - H1 calibration figure readability revision

Context:

- Continued the explicit H1 forecast-quality objective by revising the
  calibration visualization that previously drew sparse fixed-bin reliability
  rows as connected curves.
- The change keeps all statistical calculations in Python and uses only
  existing deterministic H1 case artifacts. It does not collect new data, query
  a database, use LLMs, agents, MCP, ML, wallet fields, order fields, or raw
  table dumps.

Changes:

- Updated `operations/analysis/h1_calibration_diagnostic.py` so
  `h1_calibration_diagnostic.png` is now a scorecard-plus-sparse-bin figure.
- The figure now separates:
  - aggregate Brier advantage by pairwise comparison,
  - individual lower-loss counts,
  - unconnected sparse reliability-bin points for sources with at least 30
    cases,
  - mean Brier and fixed-bin ECE.
- Added visualization metadata for `sparse_reliability_points_not_connected`
  and `reliability_panel_min_case_count`.
- Updated `tests/test_h1_calibration_diagnostic.py`.
- Updated `docs/research/RESEARCH_SPEC.md`.
- Regenerated `data/results/h1_calibration_diagnostic.*` and the Dozentenbericht
  artifacts.

Key output:

- H1 calibration diagnostic still contains 192 forecast-case rows across 7
  forecast sources and 5 pairwise rows.
- Polymarket has lower aggregate mean Brier in 5 of 5 pairwise rows.
- Polymarket has majority lower individual loss in 2 of 5 pairwise rows.
- Broad many-cases support remains 0 of 5 and `not_proven`.

Interpretation:

- The revised visualization makes the current H1 evidence easier to read and
  avoids implying a continuous calibration curve from sparse bins.
- It strengthens thesis-facing reporting quality but does not complete the
  broad claim. More independent resolved markets or a stronger scoped claim are
  still needed before saying Polymarket is generally better than poll-based
  comparators.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.h1_calibration_diagnostic`
  -> PASS, regenerated calibration CSVs, PNG, and metadata.
- `data/results/h1_calibration_diagnostic.png` inspected; figure is nonblank
  and readable with the revised scorecard layout.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_calibration_diagnostic.py -q`
  -> PASS, 3 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown/HTML/DOCX with 33 figures.

## 2026-06-11 - H1 direct poll outlier robustness diagnostic

Context:

- Continued the H1 forecast-quality objective by checking whether the positive
  direct poll state-cluster mean is driven by one or a few exceptional states.
- Kept the work deterministic: Python only, no live data collection, no
  database writes, no LLM metrics, no agents/MCP, no ML, no wallet fields, and
  no order endpoints.

Changes:

- Added `operations/analysis/h1_direct_poll_outlier_robustness.py`.
- Generated `data/results/h1_direct_poll_outlier_robustness_scenarios.csv`,
  `data/results/h1_direct_poll_outlier_robustness_summary.csv`,
  `data/results/h1_direct_poll_outlier_robustness.png`, and
  `data/results/h1_direct_poll_outlier_robustness_metadata.json`.
- Added `tests/test_h1_direct_poll_outlier_robustness.py`.
- Integrated the result into `operations/project/build_dozenten_report.py`,
  `tests/test_dozenten_report.py`, and `docs/research/RESEARCH_SPEC.md`.
- Regenerated the Dozentenbericht artifacts.

Key output:

- Direct poll state clusters: 43.
- Full equal-state mean loss advantage: 0.0122 Brier points.
- Minimum leave-one-state-out mean: 0.0095 after removing Wisconsin.
- All 43 leave-one-state-out means remain positive.
- The mean remains positive after removing the top 6 positive state
  contributions and first turns non-positive after removing 7, at -0.0001.
- Largest positive state contribution: Wisconsin, 0.1248 Brier points.

Interpretation:

- The bounded direct poll mean-loss advantage is not created by a single state.
- The advantage is still concentrated in the largest positive state
  contributions, so this strengthens robustness of the mean-loss statement but
  does not prove a state-majority, many-election, or broad many-cases claim.
- The H1 objective remains incomplete because the user-requested broad claim
  still needs stronger independent evidence or a narrower thesis claim.

Figure:

- `data/results/h1_direct_poll_outlier_robustness.png` shows leave-one-state-out
  means, top-k positive-state exclusions, state-level contributions, and the
  bounded interpretation.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.h1_direct_poll_outlier_robustness`
  -> PASS, regenerated CSV, PNG, and metadata outputs.
- `data/results/h1_direct_poll_outlier_robustness.png` inspected; figure is
  nonblank and readable.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_direct_poll_outlier_robustness.py -q`
  -> PASS, 3 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown/HTML/DOCX with 38 figures.
- `.\.venv\Scripts\python.exe -m pytest tests\test_h1_direct_poll_outlier_robustness.py tests\test_h1_direct_poll_state_cluster_diagnostic.py tests\test_h1_direct_poll_loss_decomposition.py tests\test_dozenten_report.py -q`
  -> PASS, 10 passed.

## 2026-06-11 - Swiss referendum auto-refresh scheduler

Context:

- Continued the active Swiss 10-million referendum comparison goal after the
  user requested additional snapshots until the vote.
- Kept the runtime boundary narrow: read-only public Polymarket refreshes,
  file outputs only, no database writes, no LLM metrics, no agents/MCP, no ML,
  no authenticated channels, and no order endpoints.

Changes:

- Added `operations/collectors/swiss_referendum_auto_refresh.py` as a
  scheduler-safe one-shot wrapper around the bounded refresh runner.
- Added `tests/test_swiss_referendum_auto_refresh.py` for successful refresh,
  cutoff skip, minimum-spacing skip, lock skip, and CLI skip metadata.
- Updated `GOAL.md`, `ROADMAP.md`, and
  `docs/research/SWISS_REFERENDUM_EFFICIENCY.md` to document local scheduled
  collection until 2026-06-14T10:00:00Z.
- Updated Swiss referendum running-status metadata so the refresh command is
  described as single-invocation and manual or scheduler-invoked, not manual
  only.
- Registered local Windows task
  `BA-Thesis-Swiss-Referendum-Auto-Refresh` for hourly one-shot invocations
  until 2026-06-14 12:00 Europe/Zurich.

Key output:

- The first manual auto-refresh probe, the scheduler-triggered verification
  run, and the first scheduled hourly run all wrote `skipped_min_spacing`
  because the latest local snapshot was still newer than the configured
  55-minute spacing.
- Auto-refresh log rows: 3.
- Snapshot rows remained 19, with latest snapshot timestamp
  2026-06-11T15:43:35Z.
- Scheduled task verification returned `LastTaskResult = 0`.

Interpretation:

- Additional collection is now automated locally without creating a resident
  daemon. Each scheduled invocation can collect at most one bounded snapshot
  and otherwise writes explicit skip metadata.
- Poll-release timing interpretation remains blocked until enough local
  pre/post observations exist.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_auto_refresh.py -q`
  -> PASS, 5 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_swiss_referendum_auto_refresh.py tests\test_swiss_referendum_refresh.py -q`
  -> PASS, 9 passed.
- `.\.venv\Scripts\python.exe -m operations.collectors.swiss_referendum_auto_refresh --source live --until-utc 2026-06-14T10:00:00Z --min-spacing-minutes 55`
  -> PASS, wrote `skipped_min_spacing` metadata.
- Windows Scheduled Task controlled run and first scheduled hourly run -> PASS,
  task state `Ready`, `LastTaskResult = 0`.
- `.\.venv\Scripts\python.exe -m pytest -q`
  -> PASS, 473 passed.
## 2026-06-11 - Monitor anomaly review queue

Context:

- Switched the active implementation goal away from new Swiss referendum
  interpretation work while that track continues collecting bounded snapshots
  until the 14 June 2026 vote.
- Implemented the first deterministic anomaly review queue over existing
  politics/geopolitics monitor artifacts.
- Kept agents and MCP as future contract-only access layers; no runtime agent,
  MCP server, LLM metric calculation, ML, database write, authenticated
  channel, or order path was activated.

Changes:

- Added `operations/analysis/monitor_anomaly_review_queue.py`.
- Added `tests/test_monitor_anomaly_review_queue.py`.
- Generated `data/results/monitor_anomaly_review_queue.csv`,
  `data/results/monitor_anomaly_review_summary.csv`,
  `data/results/monitor_anomaly_review_metadata.json`, and
  `data/results/monitor_anomaly_review_dashboard.html`.
- Updated `GOAL.md`, `ROADMAP.md`, `docs/project/TOOL_USAGE.md`, and
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`.

Key output:

- Queue rows: 3.
- High-priority rows: 1.
- Medium-priority rows: 2.
- Low-priority rows: 0.
- Review label counts: `insider_risk_review_candidate=1`;
  `insider_risk_watch_cue=2`.
- Reference-overlap counts: `reference_hit=1`,
  `partial_reference_overlap=1`, `no_reference_overlap=1`.

Interpretation:

- The queue is a deterministic human-review surface over bounded monitor
  artifacts. It identifies review-worthy cases and missing evidence.
- It does not prove private information, misconduct, causality, tradeability,
  profitability, future performance, or market inefficiency.
- Future agent and MCP integration is documented only as a bounded-summary
  contract with max 50 rows, no raw SQL, no wallet-address exposure by default,
  no order/trading paths, and later `llm_audit_log` logging.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_monitor_anomaly_review_queue.py -q`
  -> PASS, 6 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_anomaly_review_queue`
  -> PASS, generated 3 queue rows and 1 high-priority row.
- `.\.venv\Scripts\python.exe -m pytest tests\test_monitor_anomaly_review_queue.py tests\test_monitor_candidate_review_report.py tests\test_monitor_reference_candidates.py tests\test_monitor_detection_backtest.py tests\test_monitor_literature_risk_scores.py -q`
  -> PASS, 28 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 479 passed in 51.18s.

## 2026-06-11 - Anomaly review status worksheet

Context:

- Continued the deterministic monitor anomaly-review goal after committing the
  first queue layer.
- Added a curated manual status worksheet so human source checks can be tracked
  without activating runtime agents, MCP, LLM metric calculation, ML, database
  writes, order paths, or raw wallet exposure.

Changes:

- Added `data/monitor_anomaly_review_status_updates.csv`.
- Extended `operations/analysis/monitor_anomaly_review_queue.py` to read,
  validate, and merge optional review updates.
- Extended the queue output with reviewer, review source URL, event source URL,
  and review note fields.
- Updated `tests/test_monitor_anomaly_review_queue.py`,
  `docs/project/TOOL_USAGE.md`, `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`,
  `GOAL.md`, and `ROADMAP.md`.
- Regenerated `data/results/monitor_anomaly_review_queue.csv`,
  `data/results/monitor_anomaly_review_metadata.json`, and
  `data/results/monitor_anomaly_review_dashboard.html`.

Key output:

- Review worksheet rows: 3.
- Queue rows after merge: 3.
- Current human-review statuses: `needs_human_review`.
- High-priority rows remain 1; medium-priority rows remain 2.

Interpretation:

- The worksheet is a manual review-control surface, not an automated judgement.
- Current rows deliberately do not invent source checks; they remain
  `needs_human_review` until manually reviewed.
- Future status values can mark source-check progress or exclusion while
  keeping blocked claims explicit in the generated queue.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_monitor_anomaly_review_queue.py -q`
  -> PASS, 8 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_anomaly_review_queue`
  -> PASS, merged 3 review-update rows into 3 queue rows.
- `.\.venv\Scripts\python.exe -m pytest tests\test_monitor_anomaly_review_queue.py tests\test_monitor_candidate_review_report.py tests\test_monitor_reference_candidates.py -q`
  -> PASS, 20 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 481 passed in 57.83s.

## 2026-06-11 - Anomaly review source-check seed

Context:

- Continued the deterministic monitor anomaly-review queue by recording the
  first manual source-check progress for the current high-priority review
  candidate.
- Kept the Swiss referendum track as running data collection and did not add a
  new referendum interpretation decision.
- Kept agents, MCP, LLM metric calculation, ML, database writes, trading
  paths, and wallet-address prompt exposure out of scope.

Changes:

- Updated `data/monitor_anomaly_review_status_updates.csv` for
  `monitor_candidate_20260523_192500_c6370fa4e8c9` from
  `needs_human_review` to `source_check_pending`.
- Recorded public Polymarket market context and FairVote/Lake 2028 primary
  poll context as source-check follow-up fields.
- Regenerated `data/results/monitor_anomaly_review_queue.csv`,
  `data/results/monitor_anomaly_review_summary.csv`,
  `data/results/monitor_anomaly_review_metadata.json`, and
  `data/results/monitor_anomaly_review_dashboard.html`.
- Updated `GOAL.md`, `ROADMAP.md`, and
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md` to reflect the new review
  status without upgrading it to thesis-facing evidence.

Key output:

- Queue rows after merge: 3.
- High-priority rows: 1.
- Current human-review statuses: `needs_human_review=2`;
  `source_check_pending=1`.
- Metadata still records future MCP row cap 50, no wallet-address output, no
  order instructions, and contract-only agent/MCP status.

Interpretation:

- The first source-check entry records that public market and public polling
  context were identified for the high-priority case.
- It remains a human-review cue only. It does not prove event causality,
  private information, misconduct, tradeability, profitability, future
  performance, or market inefficiency.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_anomaly_review_queue`
  -> PASS, generated 3 queue rows and 1 high-priority row.
- `.\.venv\Scripts\python.exe -m pytest tests\test_monitor_anomaly_review_queue.py -q`
  -> PASS, 8 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 481 passed in 53.64s.

## 2026-06-11 - Queued anomaly cases source-checked

Context:

- Continued the deterministic monitor anomaly-review queue after recording the
  first high-priority source-check seed.
- Source-checked the two remaining medium-priority queue cases manually with
  public market and context URLs.
- Kept the result as review progress only; no agent, MCP, LLM metric
  calculation, ML, database write, order path, wallet-address exposure, or
  thesis-facing claim was introduced.

Changes:

- Updated `data/monitor_anomaly_review_status_updates.csv` so all 3 current
  queue rows are now `source_check_pending`.
- Added public source-check URLs for the U.S.-Iran and China-Taiwan medium
  cases.
- Regenerated `data/results/monitor_anomaly_review_queue.csv`,
  `data/results/monitor_anomaly_review_summary.csv`,
  `data/results/monitor_anomaly_review_metadata.json`, and
  `data/results/monitor_anomaly_review_dashboard.html`.
- Updated `GOAL.md`, `ROADMAP.md`, and
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md` to reflect that all current
  queue cases have source-check progress but still need human acceptance or
  exclusion.

Key output:

- Queue rows after merge: 3.
- High-priority rows: 1.
- Medium-priority rows: 2.
- Current human-review statuses: `source_check_pending=3`.
- Summary still records future agent and MCP readiness as contract-only, with
  bounded summaries, max 50 rows, no raw SQL, no wallet-address exposure by
  default, and no order/trading paths.

Interpretation:

- Public market/context URLs are now attached to all current review cases.
- The cases remain human-review cues only. They do not prove event causality,
  private information, misconduct, tradeability, profitability, future
  performance, or market inefficiency.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_anomaly_review_queue`
  -> PASS, generated 3 queue rows and 1 high-priority row.
- `.\.venv\Scripts\python.exe -m pytest tests\test_monitor_anomaly_review_queue.py -q`
  -> PASS, 8 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 481 passed in 47.57s.

## 2026-06-11 - Bounded anomaly case review packets

Context:

- Continued the deterministic monitor anomaly-review queue after all current
  queued cases received `source_check_pending` status.
- Added a bounded per-case review surface for later human review and future
  audited MCP/agent reading.
- Kept MCP tools, runtime agents, LLM metric calculation, ML, database writes,
  order paths, wallet-address exposure, and thesis-facing evidence claims out
  of scope.

Changes:

- Extended `operations/analysis/monitor_anomaly_review_queue.py` to build
  case-review packets from the validated anomaly review queue.
- Added `data/results/monitor_anomaly_case_review_packets.csv`.
- Added `data/results/monitor_anomaly_case_review_packets.json`.
- Updated metadata to record packet paths, packet row count, wallet-address
  safety, order-instruction safety, and contract-only MCP/agent status.
- Extended `tests/test_monitor_anomaly_review_queue.py` with packet-level
  assertions.
- Updated `GOAL.md`, `ROADMAP.md`, `docs/project/TOOL_USAGE.md`, and
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`.

Key output:

- Case-review packet rows: 3.
- Queue rows remain 3.
- High-priority rows remain 1.
- All packet rows are bounded summaries with source-check status, source
  context, evidence status, missing evidence, next review step, allowed
  interpretation, blocked claims, and future MCP/agent contract notes.
- Metadata records `case_packets_contain_wallet_addresses=false` and
  `case_packets_contain_order_instructions=false`.

Interpretation:

- The packet output is a controlled review interface over deterministic queue
  artifacts.
- It prepares a future read-only MCP/agent access contract but does not
  activate MCP or agents.
- Packets do not prove event causality, private information, misconduct,
  tradeability, profitability, future performance, or market inefficiency.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_monitor_anomaly_review_queue.py -q`
  -> PASS, 9 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_anomaly_review_queue`
  -> PASS, generated 3 queue rows and 3 case-review packet rows.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 482 passed in 67.36s.

## 2026-06-11 - Anomaly review status transitions

Context:

- Continued the deterministic monitor anomaly-review queue after adding
  bounded case-review packets.
- Added deterministic transition gates for manual review status changes.
- Kept all current cases in `source_check_pending`; no case was automatically
  accepted, rejected, upgraded, or made thesis-facing.
- No MCP tool, runtime agent, LLM metric calculation, ML, database write,
  order path, wallet-address exposure, or thesis-facing evidence claim was
  introduced.

Changes:

- Extended `operations/analysis/monitor_anomaly_review_queue.py` to build
  status-transition rows from bounded case-review packets.
- Added `data/results/monitor_anomaly_review_status_transitions.csv`.
- Added `data/results/monitor_anomaly_review_status_transitions.json`.
- Updated metadata to record transition paths, transition row count,
  wallet-address safety, order-instruction safety, and contract-only
  MCP/agent status.
- Extended `tests/test_monitor_anomaly_review_queue.py` with transition-gate
  assertions.
- Updated `GOAL.md`, `ROADMAP.md`, `docs/project/TOOL_USAGE.md`, and
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`.

Key output:

- Status-transition rows: 3.
- Current statuses: `source_check_pending=3`.
- Allowed next statuses for current rows:
  `reviewed_keep_candidate`, `reviewed_false_context`, or
  `thesis_excluded`.
- Thesis-use gate: blocked until a human reviewer marks
  `reviewed_keep_candidate` and documents limitations.
- Metadata records `status_transitions_contain_wallet_addresses=false` and
  `status_transitions_contain_order_instructions=false`.

Interpretation:

- Transition rows formalise manual review gates; they do not make review
  decisions.
- The current cases remain human-review cues only and are not thesis-facing
  evidence.
- The outputs do not prove event causality, private information, misconduct,
  tradeability, profitability, future performance, or market inefficiency.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_monitor_anomaly_review_queue.py -q`
  -> PASS, 10 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_anomaly_review_queue`
  -> PASS, generated 3 transition rows.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 483 passed in 51.35s.

## 2026-06-11 - Anomaly review decision readiness

Context:

- Continued the deterministic monitor anomaly-review queue after adding
  status-transition gates.
- Added a curated final decision worksheet and validation output for manual
  keep, false-context, or thesis-exclusion decisions.
- Kept all current real cases without a final decision; no case was accepted,
  rejected, upgraded, or made thesis-facing.
- No MCP tool, runtime agent, LLM metric calculation, ML, database write,
  order path, wallet-address exposure, or thesis-facing evidence claim was
  introduced.

Changes:

- Added `data/monitor_anomaly_review_decisions.csv` with the three current
  case IDs and blank target decisions.
- Extended `operations/analysis/monitor_anomaly_review_queue.py` to validate
  final review decisions against deterministic status-transition gates.
- Added `data/results/monitor_anomaly_review_decision_readiness.csv`.
- Added `data/results/monitor_anomaly_review_decision_readiness.json`.
- Updated metadata to record decision worksheet path, decision row count,
  readiness row count, wallet-address safety, and order-instruction safety.
- Extended `tests/test_monitor_anomaly_review_queue.py` with valid and invalid
  decision-readiness scenarios.
- Updated `GOAL.md`, `ROADMAP.md`, `docs/project/TOOL_USAGE.md`, and
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`.

Key output:

- Review decision worksheet rows: 3.
- Decision-readiness rows: 3.
- Current decision validation statuses: `no_decision_recorded=3`.
- `reviewed_keep_candidate` is blocked unless limitations and thesis-use
  scope are documented.
- Metadata records `decision_readiness_contains_wallet_addresses=false` and
  `decision_readiness_contains_order_instructions=false`.

Interpretation:

- Decision-readiness outputs validate whether a manual target status is
  admissible; they do not apply decisions automatically.
- The current cases remain human-review cues only and are not thesis-facing
  evidence.
- The outputs do not prove event causality, private information, misconduct,
  tradeability, profitability, future performance, or market inefficiency.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_monitor_anomaly_review_queue.py -q`
  -> PASS, 14 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_anomaly_review_queue`
  -> PASS, generated 3 decision-readiness rows.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 487 passed in 49.26s.

## 2026-06-11 - Anomaly review access contract

Context:

- Continued the deterministic monitor anomaly-review queue after adding
  decision-readiness outputs.
- Added a static future-access contract for later audited MCP/agent reading of
  bounded anomaly-review artifacts.
- Did not implement or activate any MCP server, runtime agent, model routing,
  LLM metric calculation, ML, database write, order path, wallet-address
  exposure, or thesis-facing evidence claim.

Changes:

- Extended `operations/analysis/monitor_anomaly_review_queue.py` to write
  `data/results/monitor_anomaly_review_access_contract.json`.
- The access contract lists allowed bounded artifacts, future tool names,
  max-row limits, blocked-by-default artifact classes, and runtime guards.
- Updated metadata to include the access-contract path.
- Extended `tests/test_monitor_anomaly_review_queue.py` with static access
  contract assertions.
- Updated `GOAL.md`, `ROADMAP.md`, `docs/project/TOOL_USAGE.md`, and
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`.

Key output:

- Access-contract rows are JSON-only metadata, not runtime tools.
- Future tool names remain contract-only:
  `get_anomaly_review_summary`, `get_anomaly_case`,
  `list_monitor_artifacts`, and `get_method_limits`.
- The contract records max default rows 50, raw SQL blocked, wallet-address
  exposure blocked by default, order/trading paths blocked, runtime MCP server
  not implemented, and runtime agents not implemented.

Interpretation:

- The contract is a read-only design artifact for future audited access.
- It does not activate MCP or agents and does not change any empirical result
  or case decision.
- The current cases remain human-review cues only and are not thesis-facing
  evidence.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_monitor_anomaly_review_queue.py -q`
  -> PASS, 15 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.monitor_anomaly_review_queue`
  -> PASS, generated the access-contract artifact.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 488 passed in 50.55s.

## 2026-06-11 - Anomaly review goal completion audit

Context:

- Audited the active deterministic anomaly-review queue goal after queue,
  source-check, packet, transition, decision-readiness, and static access
  contract layers were committed.
- Did not add MCP tools, runtime agents, model routing, LLM metric
  calculation, ML, database writes, order paths, wallet-address exposure, or
  thesis-facing anomaly claims.

Evidence checked:

- `data/results/monitor_anomaly_review_queue.csv`: 3 rows, 24 columns.
- `data/results/monitor_anomaly_review_summary.csv`: 1 row with
  `source_check_pending=3`.
- `data/results/monitor_anomaly_case_review_packets.csv`: 3 bounded packets.
- `data/results/monitor_anomaly_review_status_transitions.csv`: 3 transition
  rows.
- `data/results/monitor_anomaly_review_decision_readiness.csv`: 3 rows, all
  `no_decision_recorded`.
- `data/results/monitor_anomaly_review_metadata.json`: wallet-address and
  order-instruction safety flags are false for queue, packets, transitions,
  and decision-readiness outputs.
- `data/results/monitor_anomaly_review_access_contract.json`: status is
  `contract_only_not_implemented`, max default rows is 50, raw SQL is blocked,
  wallet-address exposure is blocked by default, order/trading paths are
  blocked, and runtime MCP/agents are not implemented.

Interpretation:

- The deterministic anomaly-review layer is complete for the current bounded
  monitor candidates.
- The current cases remain human-review cues only and are not thesis-facing
  evidence because no final manual decision has been recorded.
- Future MCP/agent access is specified only as a static contract and remains
  deferred.

Verification:

- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 488 passed in 46.16s.

## 2026-06-11 - Dozentenbericht BA thesis structure update

Context:

- Reworked the supervisor-facing report into a Bachelorarbeit-style interim
  document while preserving deterministic result sourcing.
- Used only local result artifacts, the local literature index, and existing
  project documentation.
- Did not calculate statistical metrics with an LLM and did not activate
  agents, MCP tools, live trading paths, model routing, ML, or database writes.

Changes:

- Extended `operations/project/build_dozenten_report.py` with front-matter
  sections for research question, BA-style structure, scientific source
  framing, method design, data basis, and guardrails.
- Added a bounded literature table from `data/literature/literature_index.csv`
  covering Fama, Polymarket transaction/context work, prediction-market vs
  polling framing, information-advantage/prediction-market conceptual context, Kalshi
  microstructure, and Polymarket convergence/volatility context.
- Added current anomaly-review queue counts to the Monitor section:
  3 cases, 1 high priority, 2 medium priority, 0 low priority, all
  `source_check_pending`.
- Regenerated `docs/project/dozentenbericht_ba_thesis.md`,
  `docs/project/dozentenbericht_ba_thesis.html`, and
  `docs/project/dozentenbericht_ba_thesis.docx`.
- Tightened DOCX table geometry so generated rows carry explicit table cell
  widths.

Key output:

- The report now starts with a BA-like arc: Kurzfazit, Aufbau,
  Forschungsfrage/Hypothesen, wissenschaftlicher Quellenrahmen, methodisches
  Design, project structure, H1/H2/H3 results, monitor, Swiss referendum,
  visualisations, presentation plan, and artifact appendix.
- Current generated report includes 43 embedded figures.
- Current generated Swiss side-track values in the report: 7 curated polls,
  22 Polymarket snapshots, latest Polymarket Yes 22.0 percent, latest matched
  poll Yes 45.0 percent, raw gap -23.0 percentage points, decided-voter gap
  -24.4 percentage points.

Interpretation:

- The report is now more suitable as a written advisor update because it
  connects thesis framing, sources, deterministic methods, outputs, limits,
  and next steps.
- Literature rows remain a source frame. Detail claims still need full source
  review before final thesis citation status.
- The anomaly-review queue remains a human-review cue and not thesis-facing
  evidence of private information, misconduct, causality, tradeability,
  profitability, or future performance.

Verification:

- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, generated Markdown, HTML, DOCX, and 43 figures.
- `.\.venv\Scripts\python.exe -m pytest tests\test_dozenten_report.py`
  -> PASS, 1 passed.
- DOCX structural audit -> PASS, 13 headings, 20 tables, 43 inline shapes,
  43 media files, 0 missing table width fields.
- DOCX PNG render QA -> BLOCKED because LibreOffice/`soffice` is not installed
  or available in PATH on this machine.
- `.\.venv\Scripts\python.exe -m pytest`
  -> PASS, 488 passed in 48.50s.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 488 passed in 49.02s.

## 2026-06-12 - Expanded advisor report with interpretation synthesis

Goal context:

- Active user goal: make the advisor update strong enough for written handoff
  by adding Erkenntnisse, Begruendungen, Interpretationen, and scientific
  context from the available thesis artifacts and source index.
- Worked only on the written report and its deterministic source framing.
- Did not calculate metrics with an LLM and did not activate runtime agents,
  MCP demo layers, model routing, trading paths, or database writes.

Changes:

- Added four method references to `data/literature/literature_index.csv`:
  Brier forecast verification, Diebold-Mariano predictive-accuracy comparison,
  Granger temporal predictability framing, and event-study methodology.
- Extended `operations/project/build_dozenten_report.py` with deterministic
  synthesis helpers for central findings, method decisions, source roles, and
  bounded interpretation notes.
- Added report sections for central findings, method justification, and
  Gesamtinterpretation across Markdown, HTML, and DOCX outputs.
- Regenerated `docs/project/dozentenbericht_ba_thesis.md`,
  `docs/project/dozentenbericht_ba_thesis.html`, and
  `docs/project/dozentenbericht_ba_thesis.docx`.

Key output:

- Literature index now contains 15 rows; the advisor report uses 10 selected
  core sources as the explicit scientific frame.
- H1 interpretation now states that a broad superiority claim is not proven,
  while deterministic artifacts show a bounded Polymarket advantage in selected
  late and competitive windows: primary Brier 0.2303 versus 0.3324; aggregate
  synthesis support in 7 of 9 cases and fallmehrheit support in 3 of 9 cases.
- H2 interpretation now highlights the largest primary event-window movement:
  `07_13_trump_shooting`, plus 7.2 percentage points. This remains a daily
  event-window result, not an intraday speed claim.
- H3 interpretation now reports the strongest deterministic wallet timing
  pattern as `tier_1_top_1pct` at lag 1 with correlation 0.1858 and minimum
  Granger p-value 0.0012 over 1216 panel rows, without causal wording.
- Monitor interpretation now reports 3 current review cases, 1 high and
  2 medium, all `source_check_pending`; the queue is framed as a methodology
  guardrail, not evidence of causes, rule violations, tradeability,
  profitability, or future outcomes.
- Swiss side-track interpretation now uses 25 snapshots, latest Polymarket Yes
  21.5 percent, latest poll Yes 45.0 percent, and a raw gap of -23.5 percentage
  points, with no final efficiency interpretation before the official result.

Verification:

- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, generated Markdown, HTML, DOCX, and 43 figures.
- DOCX structural audit -> PASS, 14 headings, 23 tables, 43 inline shapes,
  43 media files, 0 missing table width fields.
- DOCX PNG render QA -> BLOCKED because LibreOffice/`soffice` is not installed
  or available in PATH on this machine.
- `.\.venv\Scripts\python.exe -m pytest tests\test_dozenten_report.py`
  -> PASS, 1 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_thesis_result_summaries.py tests\test_monitor_anomaly_review_queue.py`
  -> PASS, 20 passed.
- `.\.venv\Scripts\python.exe -m pytest`
  -> PASS, 488 passed in 51.38s.

## 2026-06-12 - Commit cleanup for advisor report handoff

Goal context:

- User requested committing the completed advisor-report update and keeping the
  worktree clean.
- Confirmed `GOAL.md` still has exactly one active goal and that the Swiss
  referendum track remains a running side goal.

Changes:

- Removed the untracked Word temporary lock file for the advisor report.
- Prepared the report/literature/builder updates and the Swiss running
  artifacts for separate commits so the written handoff and live side-track
  refresh remain reviewable as distinct changes.

Verification plan:

- Re-run project status automation, review checks, and commit planning before
  creating the final commits.

## 2026-06-12 - Thesis consolidation evidence map and curated result package

Goal context:

- User paused further review-access work and requested a high-level thesis
  consolidation: literature should be mapped cleanly, every method and
  interpretation should have a source or deterministic artifact, results should
  become thesis-ready through a few strong tables/figures, and future agent
  improvements should be planned only after the deterministic package is
  stable.
- Updated `GOAL.md` to `goal-thesis-consolidation-001` and made Phase 12 the
  active roadmap phase.
- Kept agents, MCP tools, model routing, live trading, autonomous execution,
  and LLM-calculated metrics out of scope.

Changes:

- Added `operations/analysis/thesis_consolidation.py`.
- Generated `data/results/thesis_evidence_map.csv` and
  `data/results/thesis_evidence_map.md`.
- Generated `data/results/thesis_core_results_table.csv`.
- Generated `data/results/thesis_curated_result_package.csv`.
- Generated `data/results/thesis_consolidation_metadata.json`.
- Added `docs/research/THESIS_CONSOLIDATION.md`.
- Updated `docs/research/LITERATURE_MAP.md` with the current consolidation
  map, method-source mapping, and the distinction between draft-ready mapping
  and final citation review.
- Updated `ROADMAP.md`: Phase 10 is paused after the deterministic review queue
  and static access contract; Phase 12 is active for thesis consolidation.
- Added `tests/test_thesis_consolidation.py`.

Key output:

- Evidence map rows: 13.
- Method rows: 6.
- Interpretation rows: 6.
- Core result rows: 6.
- Curated package rows: 10.
- Core thesis package: 5 tables and 4 figures.
- Current core result values:
  - H1 bounded poll-comparison scope: 262 of 285 state-date rows, 91.9 percent,
    lower Brier loss for Polymarket.
  - H1 broad claim boundary: 7 of 9 aggregate rows support Polymarket, 3 of 9
    majority-case rows support Polymarket, 0 of 9 prove the broad claim, and
    5 audit rows contradict the strong claim.
  - H2 largest primary daily event-window move:
    `evt_2024_07_13_trump_shooting`, plus 7.2 percentage points.
  - H3 top-tier timing diagnostic: `tier_1_top_1pct` lag 1 correlation 0.1858,
    Granger p-value 0.0012, and 1216 aligned rows.
  - Monitor boundary: 3 review cases, 1 high, 2 medium,
    `source_check_pending=3`; appendix/prototype only.
  - Swiss boundary: 26 snapshots, latest SRG/gfs.bern comparison shows
    Polymarket Yes 22.0 percent, poll Yes 45.0 percent, raw gap -23.0
    percentage points; descriptive pending final result.

Agent pipeline note:

- `docs/research/THESIS_CONSOLIDATION.md` documents only a deferred agent
  roadmap: evidence-reader, citation-check, interpretation-consistency, human
  review, and later bounded MCP summary tools.
- It explicitly keeps metric calculation in Python, requires future
  `llm_audit_log` logging, blocks raw table dumps, keeps future tool outputs
  bounded to 50 rows by default, blocks wallet-address exposure by default, and
  blocks order/trading paths.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.thesis_consolidation`
  -> PASS, generated evidence map, core table, curated package, metadata, and
  consolidation documentation.
- `.\.venv\Scripts\python.exe -m pytest tests\test_thesis_consolidation.py tests\test_thesis_result_summaries.py tests\test_thesis_figures.py`
  -> PASS, 11 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 492 passed in 51.23s.

## 2026-06-12 - Thesis citation readiness, chapter plan, and deferred agent roadmap

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Expanded the consolidation layer beyond the first evidence map so it now
  also controls final citation readiness, BA chapter planning, and a more
  concrete future agent-pipeline roadmap.
- Kept all new agent material documentation-only; no runtime agents, MCP
  tools, model routing, LLM interpretation, live trading paths, or metric
  calculations were activated.

Changes:

- Extended `operations/analysis/thesis_consolidation.py` to generate three
  additional deterministic artifacts:
  `data/results/thesis_citation_readiness.csv`,
  `data/results/thesis_chapter_plan.csv`, and
  `data/results/thesis_agent_pipeline_roadmap.csv`.
- Added `docs/research/THESIS_AGENT_PIPELINE_ROADMAP.md`.
- Extended `docs/research/THESIS_CONSOLIDATION.md` with citation readiness,
  chapter plan, and staged agent roadmap sections.
- Updated `docs/research/LITERATURE_MAP.md` so the citation-readiness artifact
  is documented as the current source-review queue.
- Updated `ROADMAP.md` and `GOAL.md` to reflect the new next commit scope.
- Extended `tests/test_thesis_consolidation.py` to cover citation-readiness
  blocking rules, curated-package chapter references, and documentation-only
  agent stages.

Key output:

- Citation-readiness rows: 15.
- Citation-readiness counts: 11 sources need full source review before final
  citation, 1 candidate source is not allowed for thesis-facing claims, and
  3 indexed sources are not currently needed.
- Chapter-plan rows: 8, covering introduction, theory/literature, data/method,
  H1, H2, H3, extensions, and discussion/conclusion.
- Agent roadmap stages: 6.
- Agent roadmap statuses: 1 current required disabled state,
  4 future documentation-only stages, and 1 future-deferred bounded MCP stage.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.thesis_consolidation`
  -> PASS, generated the expanded consolidation artifact set.
- `.\.venv\Scripts\python.exe -m pytest tests\test_thesis_consolidation.py tests\test_thesis_result_summaries.py tests\test_thesis_figures.py`
  -> PASS, 14 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 495 passed in 48.91s.

## 2026-06-12 - Thesis writing blueprint

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Turned the consolidation package into a chapter-by-chapter writing blueprint
  so the selected tables, figures, evidence IDs, limitations, and source-review
  tasks can directly guide BA drafting.

Changes:

- Extended `operations/analysis/thesis_consolidation.py` with
  `docs/research/THESIS_WRITING_BLUEPRINT.md` generation.
- The blueprint uses `thesis_chapter_plan.csv`,
  `thesis_core_results_table.csv`, `thesis_curated_result_package.csv`, and
  `thesis_citation_readiness.csv`.
- Result statements are kept out of the introduction, theory, and methodology
  front matter; they begin in the H1-H3, extensions, and discussion chapters.
- Updated tests to verify that the blueprint is generated and that front matter
  stays method-focused.
- Updated `GOAL.md` and `ROADMAP.md` for the writing-blueprint slice.

Key output:

- New document: `docs/research/THESIS_WRITING_BLUEPRINT.md`.
- The blueprint covers source/citation work, the core writing rule, eight BA
  chapter sections, recommended package items, result statements, limitations,
  and next writing actions.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.thesis_consolidation`
  -> PASS, generated the writing blueprint.
- `.\.venv\Scripts\python.exe -m pytest tests\test_thesis_consolidation.py tests\test_thesis_result_summaries.py tests\test_thesis_figures.py`
  -> PASS, 15 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 496 passed in 47.23s.

## 2026-06-12 - Thesis chapter draft prose

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Converted the deterministic consolidation package into a first German/Swiss
  spelling thesis-prose draft with artifact references, Evidence IDs, bounded
  wording, and limitations.
- A running Swiss referendum refresh updated the latest side-track artifacts
  during this work; those data changes remain separate from new thesis-draft
  code but the thesis core table now reflects the latest snapshot count.

Changes:

- Extended `operations/analysis/thesis_consolidation.py` with generated
  `docs/research/THESIS_CHAPTER_DRAFT.md`.
- Added German draft sections for introduction, theory/literature,
  data/methodology, H1, H2, H3, monitor/Swiss extensions, discussion/fazit,
  and agent-pipeline outlook.
- The draft uses deterministic core result values only and keeps source
  review, RCP, H2 daily resolution, H3 BUY-only/daily alignment, monitor
  review status, Swiss pending-result status, and agent deferral visible.
- Extended tests to assert draft generation, traceability to Evidence IDs and
  artifacts, no German sharp-s, no English H1 method placeholder, and
  continued `llm_audit_log` agent guardrail wording.
- Updated `GOAL.md` and `ROADMAP.md` for the chapter-draft slice.

Key output:

- New document: `docs/research/THESIS_CHAPTER_DRAFT.md`.
- Latest Swiss side-track count reflected in the thesis core table and draft:
  27 snapshots, Polymarket Yes 22.0 percent, SRG/gfs.bern poll Yes 45.0
  percent, raw gap -23.0 percentage points.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.thesis_consolidation`
  -> PASS, generated the chapter draft.
- `.\.venv\Scripts\python.exe -m pytest tests\test_thesis_consolidation.py tests\test_thesis_result_summaries.py tests\test_thesis_figures.py`
  -> PASS, 16 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 497 passed in 48.49s.

## 2026-06-12 - Thesis citation review packets

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Moved from source-status mapping to row-level citation review packets so
  every source used by a method, interpretation, or future-work row is linked
  to the exact Evidence ID, artifact, wording boundary, and human review gate.

Changes:

- Extended `operations/analysis/thesis_consolidation.py` with generated
  `data/results/thesis_citation_review_packets.csv`.
- Added `docs/research/THESIS_CITATION_REVIEW_PACKETS.md`.
- Updated `docs/research/THESIS_CONSOLIDATION.md` to explain the packet
  worklist.
- Updated `docs/research/LITERATURE_MAP.md`, `ROADMAP.md`, and `GOAL.md`.
- Extended `tests/test_thesis_consolidation.py` to validate packet columns,
  packet uniqueness, pending reviewer state, H1-H3 candidate-source exclusion,
  and the future-work-only gate for `zotero_poly_010`.

Key output:

- Citation review packets: 33.
- Pending reviewer packets: 33.
- Draft-use allowed packets: 32.
- Blocked or future-only packets: 1.
- Full source review required packets: 32.
- `zotero_poly_010` remains candidate/future-work only and cannot support
  thesis-facing claims.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.thesis_consolidation`
  -> PASS, generated citation review packets and documentation.
- `.\.venv\Scripts\python.exe -m pytest tests\test_thesis_consolidation.py tests\test_thesis_result_summaries.py tests\test_thesis_figures.py`
  -> PASS, 17 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 498 passed in 49.06s.

## 2026-06-12 - Thesis table and figure captions

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Left review-access work paused and focused on the high-level thesis view:
  the curated result package now has thesis-ready labels, captions, source
  notes, interpretation notes, and limitation notes.

Changes:

- Extended `operations/analysis/thesis_consolidation.py` with generated
  `data/results/thesis_table_figure_captions.csv`.
- Added `docs/research/THESIS_TABLE_FIGURE_CAPTIONS.md`.
- Updated `ROADMAP.md`, `GOAL.md`, and `docs/research/LITERATURE_MAP.md` to
  include the caption registry in the Phase 12 consolidation layer.
- Extended `tests/test_thesis_consolidation.py` to validate caption columns,
  core table/figure counts, unique thesis labels, non-empty source and
  limitation notes, and Swiss spelling guards.

Key output:

- Caption registry rows: 10.
- Core table captions: 5.
- Core figure captions: 4.
- Appendix/future-work captions: 1.
- The registry is generated only from `thesis_curated_result_package.csv`; it
  does not add additional raw result files to the thesis core package.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.thesis_consolidation`
  -> PASS, generated the table and figure caption registry.
- `.\.venv\Scripts\python.exe -m pytest tests\test_thesis_consolidation.py -q`
  -> PASS, 11 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 499 passed in 50.24s.

## 2026-06-12 - Advisor highlevel project view

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Left review-access implementation paused and updated the advisor-facing
  project view so the current Phase 12 thesis-consolidation state is visible
  before the detailed H1-H2-H3 result sections.

Changes:

- Extended `operations/project/build_dozenten_report.py` to read
  `data/results/thesis_consolidation_metadata.json` and
  `data/results/thesis_table_figure_captions.csv`.
- Added a generated Highlevel-Projektstand section to
  `docs/project/dozentenbericht_ba_thesis.md`,
  `docs/project/dozentenbericht_ba_thesis.html`, and
  `docs/project/dozentenbericht_ba_thesis.docx`.
- Updated the report cover phase from Phase 10 to Phase 12.
- Updated `tests/test_dozenten_report.py` to assert the high-level section,
  paused review access, Phase 12 wording, five core tables, four core figures,
  and the caption registry link.
- Updated `GOAL.md` and `ROADMAP.md` for the advisor high-level update slice.

Key output:

- Dozentenbericht now opens with the practical project view: H1-H3 as the
  empirical core, Monitor and Swiss as bounded side tracks, citation-review
  gates still pending, and agents as inactive future work.
- The report states the current compact thesis package: 5 core tables, 4 core
  figures, 10 caption rows, 13 Evidence rows, 6 central result rows, 8 chapter
  plan rows, and 33 citation review packets.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_dozenten_report.py -q`
  -> PASS, 1 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_dozenten_report.py tests\test_thesis_consolidation.py -q`
  -> PASS, 12 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown, HTML, and DOCX; figure_count=43.
- DOCX render QA with the Documents `render_docx.py` helper -> BLOCKED by
  `WinError 2`, consistent with missing local LibreOffice/`soffice`.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 499 passed in 49.39s.

## 2026-06-12 - Thesis source review plan

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Converted the existing source-evidence citation packets into a source-level
  manual review plan. This keeps review-access implementation paused while
  making the next literature work explicit.

Changes:

- Extended `operations/analysis/thesis_consolidation.py` with generated
  `data/results/thesis_source_review_plan.csv`.
- Added `docs/research/THESIS_SOURCE_REVIEW_PLAN.md`.
- Updated `docs/research/THESIS_CONSOLIDATION.md`,
  `docs/research/LITERATURE_MAP.md`, `ROADMAP.md`, and `GOAL.md`.
- Extended `tests/test_thesis_consolidation.py` to validate source-review
  columns, source uniqueness, packet-count consistency, manual review actions,
  method-foundation priority bands, and candidate-source blocking.

Key output:

- Real literature index source-review rows: 15.
- Priority-1 method-foundation review sources: 11.
- Currently unused sources: 3.
- Blocked or future-work-only sources: 1.
- Citation review packets covered by the source plan: 33.
- Full-source-review-required packets: 32.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.thesis_consolidation`
  -> PASS, generated source review plan and documentation.
- `.\.venv\Scripts\python.exe -m pytest tests\test_thesis_consolidation.py tests\test_dozenten_report.py -q`
  -> PASS, 13 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 500 passed in 48.97s.

## 2026-06-12 - Thesis agent assistance protocol

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Turned the future-agent idea into a concrete documentation-only protocol
  while keeping runtime agents, MCP tools, model routing, and unlogged LLM
  interpretation inactive.

Changes:

- Extended `operations/analysis/thesis_consolidation.py` with generated
  `data/results/thesis_agent_assistance_protocol.csv`.
- Added `docs/research/THESIS_AGENT_ASSISTANCE_PROTOCOL.md`.
- Updated `docs/research/THESIS_CONSOLIDATION.md`,
  `docs/research/LITERATURE_MAP.md`, `ROADMAP.md`, and `GOAL.md`.
- Extended `tests/test_thesis_consolidation.py` to validate activation
  statuses, protocol uniqueness, `llm_audit_log` gates, no raw table access,
  no metric calculation, no order/trading paths, and no automatic source
  status changes.

Key output:

- Agent assistance protocol rows: 7.
- Future-documentation-only rows: 6.
- Future-deferred rows: 1.
- Covered future helper roles: source review, evidence-to-prose drafting,
  wording guard, table/figure checking, advisor updates, monitor appendix
  review, and bounded MCP summary interface.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.thesis_consolidation`
  -> PASS, generated agent assistance protocol and documentation.
- `.\.venv\Scripts\python.exe -m pytest tests\test_thesis_consolidation.py tests\test_dozenten_report.py -q`
  -> PASS, 14 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 501 passed in 49.23s.

## 2026-06-12 - Thesis next work plan

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Converted the high-level "how to continue" view into an ordered thesis work
  plan, after leaving review-access implementation paused and keeping agents
  documentation-only.

Changes:

- Extended `operations/analysis/thesis_consolidation.py` with generated
  `data/results/thesis_next_work_plan.csv`.
- Added `docs/research/THESIS_NEXT_WORK_PLAN.md`.
- Updated `docs/research/THESIS_CONSOLIDATION.md`,
  `docs/research/LITERATURE_MAP.md`, `ROADMAP.md`, and `GOAL.md`.
- Extended `tests/test_thesis_consolidation.py` to validate workstream
  uniqueness, contiguous priority order, non-empty next actions, blockers,
  done criteria, guardrails, and key gates for source review, agents, Swiss,
  and final QA.

Key output:

- Next-work plan rows: 10.
- First priority: `work_01_source_review`.
- Final priority: `work_10_final_qa`.
- Workstreams: source review, front-matter/method chapters, H1, H2/H3,
  compact tables/figures, monitor appendix, Swiss result gate, agent outlook,
  advisor iteration, and final thesis QA.

Verification:

- `.\.venv\Scripts\python.exe -m operations.analysis.thesis_consolidation`
  -> PASS, generated next-work plan and documentation.
- `.\.venv\Scripts\python.exe -m pytest tests\test_thesis_consolidation.py tests\test_dozenten_report.py -q`
  -> PASS, 15 passed.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 502 passed in 50.00s.

## 2026-06-12 - Advisor next-work section

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Integrated the new thesis next-work plan into the advisor-facing
  Dozentenbericht so the report now explains both project state and the next
  ordered workstreams.

Changes:

- Extended `operations/project/build_dozenten_report.py` to read
  `data/results/thesis_next_work_plan.csv`.
- Added a German `Naechste Arbeitsschritte` section to
  `docs/project/dozentenbericht_ba_thesis.md`,
  `docs/project/dozentenbericht_ba_thesis.html`, and
  `docs/project/dozentenbericht_ba_thesis.docx`.
- Updated `tests/test_dozenten_report.py` to verify the new section and the
  first and final workstream IDs.
- Updated `GOAL.md` and `ROADMAP.md`.

Key output:

- The advisor report now shows 10 ordered workstreams, starting with
  `work_01_source_review` and ending with `work_10_final_qa`.
- The rendered report table uses German labels and keeps the guardrails
  visible for source review, chapter drafting, Swiss, Monitor, agents, and
  final QA.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_dozenten_report.py -q`
  -> PASS, 1 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_dozenten_report.py tests\test_thesis_consolidation.py -q`
  -> PASS, 15 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown, HTML, and DOCX; figure_count=43.
- DOCX render QA with the Documents `render_docx.py` helper -> BLOCKED by
  `WinError 2`, consistent with missing local LibreOffice/`soffice`.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 502 passed in 48.77s.

## 2026-06-12 - Thesis project highlevel view

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Kept review-access work paused and turned the "how next at high level"
  question into a deterministic project-status matrix for advisor discussion
  and thesis sequencing.

Changes:

- Extended `operations/analysis/thesis_consolidation.py` with generated
  `data/results/thesis_project_highlevel_view.csv`.
- Added `docs/research/THESIS_PROJECT_HIGHLEVEL_VIEW.md`.
- Embedded the high-level project matrix into
  `docs/research/THESIS_CONSOLIDATION.md`.
- Updated metadata, tests, `ROADMAP.md`, and `GOAL.md`.
- Regenerated dependent thesis docs; the Swiss running snapshot count now
  reflects 28 local snapshots in the derived consolidation text.

Key output:

- Project rows: 10.
- Thesis-facing empirical rows: 3.
- Paused appendix rows: 1.
- Documentation-only rows: 1.
- Core decision: H1-H3 stay the thesis core, source review is the active gate,
  monitor review access stays paused, Swiss remains pending final result, and
  agents remain documentation-only.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_thesis_consolidation.py tests\test_dozenten_report.py -q`
  -> PASS, 16 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.thesis_consolidation`
  -> PASS, generated 10 high-level project rows.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 503 passed in 51.38s.

## 2026-06-12 - Advisor project matrix

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Moved the generated project highlevel view into the advisor-facing
  Dozentenbericht so the next discussion has a direct status, decision, and
  gate matrix.

Changes:

- Extended `operations/project/build_dozenten_report.py` to read
  `data/results/thesis_project_highlevel_view.csv`.
- Added `Projektmatrix fuer die naechste Abstimmung` to
  `docs/project/dozentenbericht_ba_thesis.md`,
  `docs/project/dozentenbericht_ba_thesis.html`, and
  `docs/project/dozentenbericht_ba_thesis.docx`.
- Updated `tests/test_dozenten_report.py`, `GOAL.md`, and `ROADMAP.md`.

Key output:

- The advisor report now shows 10 project layers with German labels, status,
  current decision, and next gate.
- The matrix explicitly keeps Monitor Review-Access paused, Swiss pending the
  official result, and agents documentation-only with `llm_audit_log` as a
  future activation gate.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_dozenten_report.py -q`
  -> PASS, 1 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_dozenten_report.py tests\test_thesis_consolidation.py -q`
  -> PASS, 16 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown, HTML, and DOCX; figure_count=43.
- DOCX render QA with the Documents `render_docx.py` helper -> BLOCKED by
  `WinError 2`, consistent with missing local LibreOffice/`soffice`.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 503 passed in 49.07s.

## 2026-06-12 - Thesis source review worksheet

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Added a manual source-review work surface so the literature can be checked
  source by source before final thesis citation, without automatically
  promoting any source status.

Changes:

- Added `operations/analysis/thesis_source_review_worksheet.py`.
- Generated `data/results/thesis_source_review_worksheet.csv`.
- Added `docs/research/THESIS_SOURCE_REVIEW_WORKSHEET.md`.
- Added `tests/test_thesis_source_review_worksheet.py`.
- Updated `GOAL.md` and `ROADMAP.md`.

Key output:

- Worksheet rows: 15.
- Priority-1 method-foundation rows: 11.
- Blocked or future-work-only rows: 1.
- Every row keeps `reviewer_decision=pending` and provides linked Evidence IDs,
  wording to confirm, wording not to claim, source locator, and manual reviewer
  fields.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_thesis_source_review_worksheet.py -q`
  -> PASS, 2 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_thesis_source_review_worksheet.py tests\test_thesis_consolidation.py tests\test_dozenten_report.py -q`
  -> PASS, 18 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.thesis_source_review_worksheet`
  -> PASS, generated 15 worksheet rows.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 505 passed in 48.37s.

## 2026-06-12 - Advisor source worksheet summary

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Integrated the new manual source-review worksheet into the advisor-facing
  Dozentenbericht so the literature section shows what still needs review
  before final thesis citation.

Changes:

- Extended `operations/project/build_dozenten_report.py` to read
  `data/results/thesis_source_review_worksheet.csv`.
- Added a source-review worksheet summary to
  `docs/project/dozentenbericht_ba_thesis.md`,
  `docs/project/dozentenbericht_ba_thesis.html`, and
  `docs/project/dozentenbericht_ba_thesis.docx`.
- Updated `tests/test_dozenten_report.py`, `GOAL.md`, and `ROADMAP.md`.

Key output:

- Advisor report literature section now states 15 manual review rows, 11
  Priority-1 method-foundation sources, 1 blocked/future-work-only source, and
  pending reviewer decisions.
- The section makes clear that the worksheet is a review gate, not automatic
  source promotion.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_dozenten_report.py tests\test_thesis_source_review_worksheet.py -q`
  -> PASS, 3 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, regenerated Markdown, HTML, and DOCX; figure_count=43.
- DOCX render QA with the Documents `render_docx.py` helper -> BLOCKED by
  `WinError 2`, consistent with missing local LibreOffice/`soffice`.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 505 passed in 50.93s.

## 2026-06-12 - Thesis wording guard

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Added a German thesis-writing guard so each Evidence ID has explicit allowed
  wording, blocked overclaims, artifact reference, limitation, and use gate.

Changes:

- Added `operations/analysis/thesis_wording_guard.py`.
- Generated `data/results/thesis_wording_guard.csv`.
- Added `docs/research/THESIS_WORDING_GUARD.md`.
- Added `tests/test_thesis_wording_guard.py`.
- Updated `GOAL.md` and `ROADMAP.md`.

Key output:

- Wording-guard rows: 13.
- Thesis-text rows allowed after source review: 8.
- Draft rows allowed only with explicit source-review/result gate: 4.
- Future-work or appendix-only rows: 1.
- The guard blocks broad superiority, Intraday-speed, causality,
  private-information, profit, mispricing, trading, raw table, and unlogged LLM
  claims.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_thesis_wording_guard.py tests\test_thesis_source_review_worksheet.py tests\test_thesis_consolidation.py -q`
  -> PASS, 19 passed.
- `.\.venv\Scripts\python.exe -m operations.analysis.thesis_wording_guard`
  -> PASS, generated 13 guard rows.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 507 passed in 49.22s.

## 2026-06-12 - Advisor alignment checklist

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Turned the high-level project view into concrete advisor questions for the
  next discussion.

Changes:

- Added `operations/project/build_advisor_alignment_checklist.py`.
- Generated `data/results/thesis_advisor_alignment_checklist.csv`.
- Added `docs/project/DOZENTEN_ABSPRACHE_CHECKLIST.md`.
- Added `tests/test_advisor_alignment_checklist.py`.
- Updated `GOAL.md` and `ROADMAP.md`.

Key output:

- Advisor questions: 8.
- Topics: H1 bounded wording, source-review depth, H2/H3 scope, compact
  table/figure package, monitor appendix, Swiss result gate, agent outlook, and
  final QA.
- The checklist keeps Review-Access paused, agents documentation-only, Swiss
  pending official result mapping, and no trading/runtime-agent paths.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_advisor_alignment_checklist.py tests\test_dozenten_report.py tests\test_thesis_wording_guard.py -q`
  -> PASS, 5 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_advisor_alignment_checklist`
  -> PASS, generated 8 advisor questions.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 509 passed in 49.86s.

## 2026-06-12 - Thesis consolidation index

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Added a compact navigation index over the current advisor, thesis drafting,
  source review, wording, table/figure, agent-outlook, status, and work-log
  artifacts.

Changes:

- Added `operations/project/build_thesis_consolidation_index.py`.
- Generated `data/results/thesis_consolidation_index.csv`.
- Added `docs/project/THESIS_CONSOLIDATION_INDEX.md`.
- Added `tests/test_thesis_consolidation_index.py`.
- Updated `GOAL.md` and `ROADMAP.md`.

Key output:

- Indexed artifacts: 12.
- The index points first to the Dozentenbericht and Absprache-Checklist, then
  to highlevel view, next work plan, source worksheet, wording guard,
  table/figure captions, chapter draft, source review plan, agent protocol,
  status, and work log.
- It keeps Review-Access paused, runtime agents/MCP/model routing disabled,
  source-status promotion manual, and raw artifact dumps out of the core
  thesis text.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_thesis_consolidation_index.py tests\test_advisor_alignment_checklist.py -q`
  -> PASS, 4 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_thesis_consolidation_index`
  -> PASS, generated 12 indexed artifacts.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 511 passed in 52.18s.
- `.\.venv\Scripts\python.exe -m operations.project.review_check`
  -> PASS, 511 passed in 50.66s.
- `.\.venv\Scripts\python.exe -m operations.project.commit_plan`
  -> PASS, recommends reviewing one coherent docs/data/automation slice.

## 2026-06-12 - Advisor handoff package

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Added a compact package view showing which files should be given to or used
  with the advisor first.

Changes:

- Added `operations/project/build_advisor_handoff_package.py`.
- Generated `data/results/thesis_advisor_handoff_package.csv`.
- Added `docs/project/THESIS_ADVISOR_HANDOFF_PACKAGE.md`.
- Added `tests/test_advisor_handoff_package.py`.
- Updated the thesis consolidation index to include the package.
- Updated `GOAL.md` and `ROADMAP.md`.

Key output:

- Advisor package deliverables: 7.
- First deliverable: `advisor_report_docx`.
- Final deliverable: `consolidation_index`.
- The package orders the Word report, advisor questions, execution checklist,
  chapter source bindings, source review execution, agent future-work handoff,
  and consolidation index.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_advisor_handoff_package.py tests\test_thesis_consolidation_index.py -q`
  -> PASS, 4 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_advisor_handoff_package`
  -> PASS, generated 7 advisor handoff rows.
- `.\.venv\Scripts\python.exe -m operations.project.build_thesis_consolidation_index`
  -> PASS, generated 17 indexed artifacts.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 521 passed in 48.69s.
- `.\.venv\Scripts\python.exe -m operations.project.review_check`
  -> PASS, 521 passed in 50.71s.
- `.\.venv\Scripts\python.exe -m operations.project.commit_plan`
  -> PASS, recommends reviewing one coherent docs/data/automation slice.

## 2026-06-12 - Chapter source bindings

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Added a chapter-level binding matrix so each planned BA chapter can be
  checked against Evidence IDs, source IDs, review tasks, artifacts, tables,
  figures, limitations, and writing gates.

Changes:

- Added `operations/project/build_chapter_source_bindings.py`.
- Generated `data/results/thesis_chapter_source_bindings.csv`.
- Added `docs/project/THESIS_CHAPTER_SOURCE_BINDINGS.md`.
- Added `tests/test_chapter_source_bindings.py`.
- Updated the thesis consolidation index to include the binding matrix.
- Updated `GOAL.md` and `ROADMAP.md`.

Key output:

- Chapter binding rows: 8.
- Chapters with source mapping: 8.
- H1, H2, H3, Swiss/Monitor, and discussion chapters now show their source
  IDs and source-review gates explicitly.
- The matrix keeps final thesis claims blocked until Human Review, artifact
  references, limitations, and Wording Guard are satisfied.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_chapter_source_bindings.py tests\test_thesis_consolidation_index.py -q`
  -> PASS, 4 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_chapter_source_bindings`
  -> PASS, generated 8 chapter binding rows.
- `.\.venv\Scripts\python.exe -m operations.project.build_thesis_consolidation_index`
  -> PASS, generated 16 indexed artifacts.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 519 passed in 49.71s.
- `.\.venv\Scripts\python.exe -m operations.project.review_check`
  -> PASS, 519 passed in 48.88s.
- `.\.venv\Scripts\python.exe -m operations.project.commit_plan`
  -> PASS, recommends reviewing one coherent docs/data/automation slice.

## 2026-06-12 - Agent future-work handoff

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Documented how agents could later improve the thesis pipeline without
  implementing or activating runtime agents, MCP, model routing, or LLM metric
  calculation.

Changes:

- Added `operations/project/build_agent_future_work_handoff.py`.
- Generated `data/results/thesis_agent_future_work_handoff.csv`.
- Added `docs/project/THESIS_AGENT_FUTURE_WORK_HANDOFF.md`.
- Added `tests/test_agent_future_work_handoff.py`.
- Updated the thesis consolidation index to include the handoff.
- Updated `GOAL.md` and `ROADMAP.md`.

Key output:

- Future handoff rows: 7.
- Documentation-only rows: 6.
- Deferred rows: 1.
- The handoff maps future source-review, evidence-reader, wording-guard,
  table/figure-checker, advisor-update, monitor-review, and bounded-MCP support
  to required gates.
- Every row keeps runtime agents, MCP, model routing, LLM metrics, raw-data
  prompts, wallet-address exposure by default, and trading paths disabled.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_agent_future_work_handoff.py tests\test_thesis_consolidation_index.py -q`
  -> PASS, 4 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_agent_future_work_handoff`
  -> PASS, generated 7 future-work handoff rows.
- `.\.venv\Scripts\python.exe -m operations.project.build_thesis_consolidation_index`
  -> PASS, generated 15 indexed artifacts.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 517 passed in 49.30s.
- `.\.venv\Scripts\python.exe -m operations.project.review_check`
  -> PASS, 517 passed in 50.20s.
- `.\.venv\Scripts\python.exe -m operations.project.commit_plan`
  -> PASS, recommends reviewing one coherent docs/data/automation slice.

## 2026-06-12 - Advisor report execution section

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Moved the new high-level execution checklist into the Dozentenbericht so the
  advisor-facing Word/HTML/Markdown report shows what happens next by chapter.

Changes:

- Updated `operations/project/build_dozenten_report.py`.
- Regenerated `docs/project/dozentenbericht_ba_thesis.md`.
- Regenerated `docs/project/dozentenbericht_ba_thesis.html`.
- Regenerated `docs/project/dozentenbericht_ba_thesis.docx`.
- Updated `tests/test_dozenten_report.py`.
- Updated `GOAL.md` and `ROADMAP.md`.

Key output:

- Added `Kapitelweise Umsetzungscheckliste` to the Dozentenbericht.
- The section shows 8 chapter tasks, including H1 result writing and the
  Swiss/monitor extension gate with advisor-question IDs.
- It keeps the report framed as a project-control and thesis-writing view, not
  a new empirical result.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_dozenten_report.py tests\test_thesis_execution_checklist.py -q`
  -> PASS, 3 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_dozenten_report`
  -> PASS, generated MD, HTML, DOCX, and 43 figures.
- `.\.venv\Scripts\python.exe C:\Users\chole\.codex\plugins\cache\openai-primary-runtime\documents\26.601.10930\skills\documents\render_docx.py docs/project/dozentenbericht_ba_thesis.docx --output_dir %TEMP%\dozentenbericht_render_20260612`
  -> BLOCKED, LibreOffice/soffice is missing (`FileNotFoundError: [WinError 2]`).
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 513 passed in 50.84s.
- `.\.venv\Scripts\python.exe -m operations.project.review_check`
  -> PASS, 513 passed in 51.14s.
- `.\.venv\Scripts\python.exe -m operations.project.commit_plan`
  -> PASS, recommends reviewing one coherent report/update slice.

## 2026-06-12 - Source review execution guide

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Turned the source-review worksheet into a concrete manual execution order
  without changing any source status.

Changes:

- Added `operations/project/build_source_review_execution_guide.py`.
- Generated `data/results/thesis_source_review_execution.csv`.
- Added `docs/project/THESIS_SOURCE_REVIEW_EXECUTION.md`.
- Added `tests/test_source_review_execution_guide.py`.
- Updated the thesis consolidation index to include the new guide.
- Updated `GOAL.md` and `ROADMAP.md`.

Key output:

- Source review tasks: 15.
- Review now priority 1: 11.
- Metadata only blocked: 1.
- Defer until mapped: 3.
- Completion gates require Human Review before final citation or source-status
  promotion.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_source_review_execution_guide.py tests\test_thesis_consolidation_index.py -q`
  -> PASS, 4 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_source_review_execution_guide`
  -> PASS, generated 15 source-review tasks.
- `.\.venv\Scripts\python.exe -m operations.project.build_thesis_consolidation_index`
  -> PASS, generated 14 indexed artifacts.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 515 passed in 49.83s.
- `.\.venv\Scripts\python.exe -m operations.project.review_check`
  -> PASS, 515 passed in 48.96s.
- `.\.venv\Scripts\python.exe -m operations.project.commit_plan`
  -> PASS, recommends reviewing one coherent docs/data/automation slice.

## 2026-06-12 - Thesis execution checklist

Goal context:

- Continued `goal-thesis-consolidation-001`.
- Left Review-Access paused and turned the high-level project view into a
  chapter-level writing and acceptance checklist.

Changes:

- Added `operations/project/build_thesis_execution_checklist.py`.
- Generated `data/results/thesis_execution_checklist.csv`.
- Added `docs/project/THESIS_EXECUTION_CHECKLIST.md`.
- Added `tests/test_thesis_execution_checklist.py`.
- Updated the thesis consolidation index to include the execution checklist.
- Updated `GOAL.md` and `ROADMAP.md`.

Key output:

- Execution tasks: 8.
- The checklist maps each thesis chapter to primary inputs, table/figure items,
  source gates, draft action, done-when criterion, and advisor-question IDs.
- It keeps Review-Access paused, Swiss descriptive until the official 14 June
  2026 result mapping, runtime agents/MCP/model routing disabled, and raw
  artifact dumps out of the active thesis core.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_thesis_execution_checklist.py tests\test_thesis_consolidation_index.py -q`
  -> PASS, 4 passed.
- `.\.venv\Scripts\python.exe -m operations.project.build_thesis_execution_checklist`
  -> PASS, generated 8 execution tasks.
- `.\.venv\Scripts\python.exe -m operations.project.build_thesis_consolidation_index`
  -> PASS, generated 13 indexed artifacts.
- `.\.venv\Scripts\python.exe -m operations.project.update_status`
  -> PASS, 513 passed in 49.26s.
- `.\.venv\Scripts\python.exe -m operations.project.review_check`
  -> PASS, 513 passed in 50.51s.
- `.\.venv\Scripts\python.exe -m operations.project.commit_plan`
  -> PASS, recommends reviewing one coherent docs/data/automation slice.
