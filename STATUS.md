# STATUS.md

<!-- PROJECT_STATUS:START -->
## Automation Snapshot

Generated: 2026-07-03 10:19

Current goal: `goal-h3-informed-trading-signature-001` - Build tested H3 informed-trading signature diagnostics

Current roadmap phase: Phase 13: H3 Informed-Trading Signature Diagnostics

Test status: FAIL

Pytest summary: `1 failed, 711 passed in 61.63s (0:01:01)`

Git branch: `main`

Latest commit: `0a7dd25`

Git status:

```text
 M .claude/settings.local.json
 M GOAL.md
 M data/results/h1_calibration_diagnostic.png
 M data/results/h1_calibration_diagnostic_bins.csv
 M data/results/h1_calibration_diagnostic_cases.csv
 M data/results/h1_calibration_diagnostic_metadata.json
 M data/results/h1_calibration_diagnostic_pairwise.csv
 M data/results/h1_calibration_diagnostic_summary.csv
 M docs/project/FHNW_ACADEMICGUIDE_RULES.md
 M docs/project/WORK_LOG.md
 M docs/project/dozentenbericht_ba_thesis.docx
 M docs/project/dozentenbericht_ba_thesis.html
 M docs/project/dozentenbericht_ba_thesis.md
 M operations/analysis/h1_calibration_diagnostic.py
 M thesis/Bachelorarbeit_FHNW.docx
 M thesis/chapters/01_einleitung.tex
 M thesis/chapters/02_theorie.tex
 M thesis/chapters/03_methodik.tex
 M thesis/chapters/04_h1.tex
 M thesis/chapters/05_h2.tex
 M thesis/chapters/06_h3.tex
 M thesis/chapters/07_erweiterungen.tex
 M thesis/chapters/08_diskussion.tex
 M thesis/chapters/09_ausblick.tex
 M thesis/chapters/10_einschraenkungen.tex
 M thesis/figures/h1_calibration_diagnostic.png
 M thesis/main.tex
 M thesis/references.bib
?? data/.fuse_hidden0000000500000001
?? data/.fuse_hidden0000000500000002
?? data/.fuse_hidden0000000500000003
?? data/.fuse_hidden0000000700000001
?? data/.fuse_hidden0000000700000002
?? data/.fuse_hidden0000000700000003
?? data/.fuse_hidden0000000900000001
?? data/.fuse_hidden0000018400000001
?? data/raw/category_efficiency/
?? data/raw/mentions_latency/trades_southpark_s27e6.json
?? data/results/agent_review_queue_eval_metrics.csv
?? data/results/agent_review_queue_eval_summary.json
?? data/results/agent_review_queue_eval_summary_llm.json
?? data/results/agent_review_queue_llm_audit_log_real.jsonl
?? data/results/category_efficiency_de.png
?? data/results/category_efficiency_summary.csv
?? data/results/h1_calibration_diagnostic_de.png
?? data/results/h1_claim_readiness_de.png
?? data/results/h1_forecast_quality_de.png
?? data/results/h1_horizon_diagnostic_de.png
?? data/results/h1_outlier_robustness_de.png
?? data/results/h2_event_window_de.png
?? data/results/h2_intraday_reaction.png
?? data/results/h3_event_wallet_anomalies_de.png
?? data/results/h3_granger_pvalues_de.png
?? data/results/h3_informed_trading_signature_de.png
?? data/results/h3_lead_time_de.png
?? data/results/h3_news_lead_check.csv
?? data/results/h3_oos_maduro_case.csv
?? data/results/h3_wallet_tier_counts_de.png
?? data/results/rcp_logit_scaling_sensitivity.png
?? data/results/southpark_e6_window_trades.csv
?? data/results/southpark_e6_window_trades_metadata.json
?? data/results/stage3_llm_audit_log.jsonl
?? data/results/swiss_referendum_10mio_case_study_de.png
?? docs/project/PROZESS_ZUSAMMENFASSUNG_DOZENT.docx
?? operations/analysis/agent_review_queue_eval.py
?? operations/analysis/agent_review_queue_llm_run.py
?? operations/analysis/category_efficiency_snapshot.py
?? operations/analysis/h3_news_lead_check.py
?? operations/analysis/h3_oos_maduro_case.py
?? operations/analysis/southpark_window_trades.py
?? operations/analysis/thesis_figures_de.py
?? operations/analysis/thesis_figures_de_rest.py
?? tests/test_agent_review_queue_eval.py
?? tests/test_category_efficiency_snapshot.py
?? tests/test_southpark_window_trades.py
?? thesis/chapters/11_anhang.tex
?? thesis/figures/agent_orchestration_architecture.png
?? thesis/figures/h1_direct_poll_outlier_robustness.png
?? thesis/figures/h1_state_poll_panel_horizon_diagnostic.png
?? thesis/figures/monitor_v2_polymarket_rolling_history.png
?? thesis_overleaf.zip
```

Git diff stat:

```text
 .claude/settings.local.json                        |   3 +-
 GOAL.md                                            |  57 ++-
 data/results/h1_calibration_diagnostic.png         | Bin 255226 -> 191785 bytes
 data/results/h1_calibration_diagnostic_bins.csv    |  54 +--
 data/results/h1_calibration_diagnostic_cases.csv   | 386 ++++++++++-----------
 .../h1_calibration_diagnostic_metadata.json        | 128 +++----
 .../results/h1_calibration_diagnostic_pairwise.csv |  12 +-
 data/results/h1_calibration_diagnostic_summary.csv |  16 +-
 docs/project/FHNW_ACADEMICGUIDE_RULES.md           |  14 +-
 docs/project/WORK_LOG.md                           |  52 +++
 docs/project/dozentenbericht_ba_thesis.docx        | Bin 7455425 -> 7428741 bytes
 docs/project/dozentenbericht_ba_thesis.html        |  10 +-
 docs/project/dozentenbericht_ba_thesis.md          |   8 +-
 operations/analysis/h1_calibration_diagnostic.py   |  29 +-
 thesis/Bachelorarbeit_FHNW.docx                    | Bin 1547968 -> 2484630 bytes
 thesis/chapters/01_einleitung.tex                  | 114 +++---
 thesis/chapters/02_theorie.tex                     |  52 ++-
 thesis/chapters/03_methodik.tex                    |   7 +-
 thesis/chapters/04_h1.tex                          |  36 +-
 thesis/chapters/05_h2.tex                          |   5 +-
 thesis/chapters/06_h3.tex                          |  12 +-
 thesis/chapters/07_erweiterungen.tex               | 303 ++++++++++++----
 thesis/chapters/08_diskussion.tex                  |  56 ++-
 thesis/chapters/09_ausblick.tex                    |  43 ++-
 thesis/chapters/10_einschraenkungen.tex            |  41 ++-
 thesis/figures/h1_calibration_diagnostic.png       | Bin 268080 -> 191785 bytes
 thesis/main.tex                                    |   2 +
 thesis/references.bib                              |  12 +
 28 files changed, 918 insertions(+), 534 deletions(-)
```

Blockers:

- Worktree has uncommitted changes that need review before commit.
- Pytest is failing; inspect output before continuing.

Next recommended action:

- feat: add h3 informed trading signature diagnostics
<!-- PROJECT_STATUS:END -->

## Current Status

Status date: 2026-05-18

The project now has deterministic daily H1, H2, and H3 baseline outputs, and
the empirical baseline package has been reviewed in
`docs/research/RESEARCH_SPEC.md`. The active work is preparing compact
thesis-facing result summaries before Overleaf export or interpretation-layer
work.

Current implemented foundation and H2 baseline:

- SQLite schema support tables exist or are migrated idempotently.
- Validation foundation exists for core row types.
- Data inventory module exists.
- First deterministic Brier baseline exists.
- RCP usage in Brier and calibration code is guarded by explicit flags.
- Agent and MCP entry points are deferred.
- Canonical event catalog audit and loader exist.
- Project-control automation exists for goal-driven Codex work.
- Deterministic H2 event-window CSV outputs exist under `data/results/`.
- The H2 row-level and summary CSV shapes are accepted for the initial daily
  baseline.
- Compact H2 summaries are persisted idempotently into `analysis_summaries`.
- H3 wallet-tier method is selected as wallet-level cumulative observed
  `amount_usd` percentiles.
- H3 wallet distribution inventory exists under `data/results/`.
- H3 wallet tier classification exists under `data/results/`.
- H3 tiered daily wallet activity series exists under `data/results/`.
- H3 descriptive lead-time histograms exist under `data/results/`.
- H3 daily lead-lag correlations and Granger outputs exist under
  `data/results/`.
- H3 Granger interpretation limits and sensitivity needs are documented.
- H1-H3 empirical baseline review is documented in
  `docs/research/RESEARCH_SPEC.md`.

## Event Catalog Audit Result

Current command:

```powershell
.\.venv\Scripts\python.exe -m operations.tools.event_catalog_audit
```

Current result against `data/thesis.db`:

| Check | Result |
| --- | ---: |
| Row count | 27 |
| Missing `event_id` | 20 |
| Missing `event_date` | 20 |
| Missing `title` | 20 |
| Missing `source_url` | 20 |
| Missing `expected_direction` | 20 |
| Missing `relevance_score` | 20 |
| Invalid canonical dates | 0 |
| Detectable duplicate `event_id` | 0 |
| Detectable duplicate canonical keys | 0 |
| Detectable duplicate legacy keys | 0 |

Interpretation: 20 legacy event rows remain without canonical fields, while
the tracked seed CSV contains the curated 7-event H2 set used for deterministic
output generation. The legacy rows are preserved but are not the default source
for H2 outputs.

## Current Blockers

- RCP is not a native probability forecast. It remains a polling signal until a
  documented and tested probability transformation exists.
- H3 wallet data currently has a BUY-only limitation and a minimum observed
  `amount_usd` of 10000, which remain source-filter metadata rather than
  analytical tier thresholds.
- Thesis-facing H1-H3 result summary tables are not prepared yet.
- Agent and MCP layers remain deferred.

## Next Recommended Commits

1. `docs: review h1 h2 h3 empirical baseline`
   - Commit the empirical baseline review and next active thesis-summary goal.
   - Acceptance: thesis-ready result tables and sensitivity gaps are explicit.

2. `docs: prepare h1 h2 h3 thesis result summaries`
   - Prepare compact, traceable result summaries for thesis drafting.
   - Acceptance: each summary maps to deterministic source artifacts.

3. `docs: document h2 thesis interpretation limits`
   - Document daily-window interpretation, event timing limitations, and
     accepted wording for H2.
   - Acceptance: thesis-facing text stays aligned with deterministic outputs.
