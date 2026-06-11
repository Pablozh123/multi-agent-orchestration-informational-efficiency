# STATUS.md

<!-- PROJECT_STATUS:START -->
## Automation Snapshot

Generated: 2026-06-11 04:33

Current goal: `goal-swiss-referendum-efficiency-001` - Build Swiss 10-million referendum Polymarket-vs-polls comparison

Current roadmap phase: Phase 11: Swiss Referendum Efficiency Comparison

Test status: PASS

Pytest summary: `468 passed in 46.25s`

Git branch: `main`

Latest commit: `75636ed`

Git status:

```text
 M STATUS.md
 M docs/project/WORK_LOG.md
 M docs/research/RESEARCH_SPEC.md
 M requirements.txt
?? data/results/h1_270towin_poll_average.png
?? data/results/h1_270towin_poll_average_cases.csv
?? data/results/h1_270towin_poll_average_metadata.json
?? data/results/h1_270towin_poll_average_summary.csv
?? data/results/h1_270towin_state_forecast.png
?? data/results/h1_270towin_state_forecast_cases.csv
?? data/results/h1_270towin_state_forecast_metadata.json
?? data/results/h1_270towin_state_forecast_summary.csv
?? data/results/h1_calibration_diagnostic.png
?? data/results/h1_calibration_diagnostic_bins.csv
?? data/results/h1_calibration_diagnostic_cases.csv
?? data/results/h1_calibration_diagnostic_metadata.json
?? data/results/h1_calibration_diagnostic_pairwise.csv
?? data/results/h1_calibration_diagnostic_summary.csv
?? data/results/h1_claim_evidence_audit.csv
?? data/results/h1_claim_evidence_audit.png
?? data/results/h1_claim_evidence_audit_metadata.json
?? data/results/h1_claim_evidence_audit_summary.csv
?? data/results/h1_competitive_state_diagnostic.png
?? data/results/h1_competitive_state_diagnostic_cases.csv
?? data/results/h1_competitive_state_diagnostic_metadata.json
?? data/results/h1_competitive_state_diagnostic_summary.csv
?? data/results/h1_competitive_state_diagnostic_tiers.csv
?? data/results/h1_direct_poll_loss_decomposition.png
?? data/results/h1_direct_poll_loss_decomposition_cases.csv
?? data/results/h1_direct_poll_loss_decomposition_metadata.json
?? data/results/h1_direct_poll_loss_decomposition_summary.csv
?? data/results/h1_direct_poll_outlier_robustness.png
?? data/results/h1_direct_poll_outlier_robustness_metadata.json
?? data/results/h1_direct_poll_outlier_robustness_scenarios.csv
?? data/results/h1_direct_poll_outlier_robustness_summary.csv
?? data/results/h1_direct_poll_state_cluster_diagnostic.png
?? data/results/h1_direct_poll_state_cluster_diagnostic_metadata.json
?? data/results/h1_direct_poll_state_cluster_diagnostic_states.csv
?? data/results/h1_direct_poll_state_cluster_diagnostic_summary.csv
?? data/results/h1_evidence_scope.csv
?? data/results/h1_evidence_scope.png
?? data/results/h1_evidence_scope_metadata.json
?? data/results/h1_expansion_readiness.csv
?? data/results/h1_expansion_readiness.png
?? data/results/h1_expansion_readiness_metadata.json
?? data/results/h1_final_snapshot.png
?? data/results/h1_final_snapshot_cases.csv
?? data/results/h1_final_snapshot_metadata.json
?? data/results/h1_final_snapshot_summary.csv
?? data/results/h1_forecast_quality.png
?? data/results/h1_forecast_quality_metadata.json
?? data/results/h1_forecast_quality_pairwise.csv
?? data/results/h1_forecast_quality_sources.csv
?? data/results/h1_forecast_quality_synthesis.csv
?? data/results/h1_forecast_quality_synthesis.png
?? data/results/h1_forecast_quality_synthesis_metadata.json
?? data/results/h1_margin_threshold_readiness.csv
?? data/results/h1_margin_threshold_readiness.png
?? data/results/h1_margin_threshold_readiness_metadata.json
?? data/results/h1_poll_claim_readiness.csv
?? data/results/h1_poll_claim_readiness.png
?? data/results/h1_poll_claim_readiness_metadata.json
?? data/results/h1_poll_claim_readiness_summary.csv
?? data/results/h1_poll_comparison_result.csv
?? data/results/h1_poll_comparison_result.png
?? data/results/h1_poll_comparison_result_metadata.json
?? data/results/h1_poll_comparison_result_summary.csv
?? data/results/h1_poll_comparison_unit_robustness.png
?? data/results/h1_poll_comparison_unit_robustness_metadata.json
?? data/results/h1_poll_comparison_unit_robustness_summary.csv
?? data/results/h1_poll_comparison_unit_robustness_units.csv
?? data/results/h1_poll_decision_matrix.csv
?? data/results/h1_poll_decision_matrix.png
?? data/results/h1_poll_decision_matrix_metadata.json
?? data/results/h1_poll_decision_matrix_summary.csv
?? data/results/h1_poll_scope_frontier.csv
?? data/results/h1_poll_scope_frontier.png
?? data/results/h1_poll_scope_frontier_metadata.json
?? data/results/h1_poll_scope_frontier_summary.csv
?? data/results/h1_popular_vote.png
?? data/results/h1_popular_vote_cases.csv
?? data/results/h1_popular_vote_metadata.json
?? data/results/h1_popular_vote_summary.csv
?? data/results/h1_rieke_state_forecast.png
?? data/results/h1_rieke_state_forecast_cases.csv
?? data/results/h1_rieke_state_forecast_metadata.json
?? data/results/h1_rieke_state_forecast_summary.csv
?? data/results/h1_robust_poll_scope_quality.png
?? data/results/h1_robust_poll_scope_quality_bins.csv
?? data/results/h1_robust_poll_scope_quality_metadata.json
?? data/results/h1_robust_poll_scope_quality_pairwise.csv
?? data/results/h1_robust_poll_scope_quality_rows.csv
?? data/results/h1_robust_poll_scope_quality_summary.csv
?? data/results/h1_robust_poll_scope_unit_quality.png
?? data/results/h1_robust_poll_scope_unit_quality_metadata.json
?? data/results/h1_robust_poll_scope_unit_quality_summary.csv
?? data/results/h1_robust_poll_scope_unit_quality_units.csv
?? data/results/h1_state_poll_panel.png
?? data/results/h1_state_poll_panel_cases.csv
?? data/results/h1_state_poll_panel_competitiveness.png
?? data/results/h1_state_poll_panel_competitiveness_grid.csv
?? data/results/h1_state_poll_panel_competitiveness_metadata.json
?? data/results/h1_state_poll_panel_competitiveness_state.csv
?? data/results/h1_state_poll_panel_competitiveness_summary.csv
?? data/results/h1_state_poll_panel_coverage.csv
?? data/results/h1_state_poll_panel_horizon_claim_audit.csv
?? data/results/h1_state_poll_panel_horizon_diagnostic.png
?? data/results/h1_state_poll_panel_horizon_diagnostic_metadata.json
?? data/results/h1_state_poll_panel_horizon_state_summary.csv
?? data/results/h1_state_poll_panel_horizon_state_support.csv
?? data/results/h1_state_poll_panel_horizon_state_support.png
?? data/results/h1_state_poll_panel_horizon_state_support_metadata.json
?? data/results/h1_state_poll_panel_horizon_state_support_summary.csv
?? data/results/h1_state_poll_panel_horizon_summary.csv
?? data/results/h1_state_poll_panel_metadata.json
?? data/results/h1_state_poll_panel_near_window_quality.png
?? data/results/h1_state_poll_panel_near_window_quality_bins.csv
?? data/results/h1_state_poll_panel_near_window_quality_metadata.json
?? data/results/h1_state_poll_panel_near_window_quality_rows.csv
?? data/results/h1_state_poll_panel_near_window_quality_summary.csv
?? data/results/h1_state_poll_panel_state_significance.csv
?? data/results/h1_state_poll_panel_state_significance.png
?? data/results/h1_state_poll_panel_state_significance_metadata.json
?? data/results/h1_state_poll_panel_state_significance_summary.csv
?? data/results/h1_state_poll_panel_state_summary.csv
?? data/results/h1_state_poll_panel_summary.csv
?? data/results/h1_state_poll_panel_temporal_claim_audit.csv
?? data/results/h1_state_poll_panel_temporal_diagnostic.png
?? data/results/h1_state_poll_panel_temporal_diagnostic_metadata.json
?? data/results/h1_state_poll_panel_temporal_state_month.csv
?? data/results/h1_state_poll_panel_temporal_summary.csv
?? data/results/h1_state_poll_snapshot.png
?? data/results/h1_state_poll_snapshot_cases.csv
?? data/results/h1_state_poll_snapshot_coverage.csv
?? data/results/h1_state_poll_snapshot_coverage.png
?? data/results/h1_state_poll_snapshot_metadata.json
?? data/results/h1_state_poll_snapshot_sensitivity.csv
?? data/results/h1_state_poll_snapshot_sensitivity.png
?? data/results/h1_state_poll_snapshot_summary.csv
?? data/results/h1_state_source_consensus.png
?? data/results/h1_state_source_consensus_cases.csv
?? data/results/h1_state_source_consensus_metadata.json
?? data/results/h1_state_source_consensus_state_summary.csv
?? data/results/h1_state_source_consensus_summary.csv
?? docs/project/dozentenbericht_assets/
?? docs/project/dozentenbericht_ba_thesis.docx
?? docs/project/dozentenbericht_ba_thesis.html
?? docs/project/dozentenbericht_ba_thesis.md
?? docs/project/dozentenbericht_ba_thesis_h1_forecast_quality.docx
?? operations/analysis/h1_270towin_poll_average_extension.py
?? operations/analysis/h1_270towin_state_forecast_extension.py
?? operations/analysis/h1_calibration_diagnostic.py
?? operations/analysis/h1_claim_evidence_audit.py
?? operations/analysis/h1_competitive_state_diagnostic.py
?? operations/analysis/h1_direct_poll_loss_decomposition.py
?? operations/analysis/h1_direct_poll_outlier_robustness.py
?? operations/analysis/h1_direct_poll_state_cluster_diagnostic.py
?? operations/analysis/h1_evidence_scope.py
?? operations/analysis/h1_expansion_readiness.py
?? operations/analysis/h1_final_snapshot_extension.py
?? operations/analysis/h1_forecast_quality.py
?? operations/analysis/h1_forecast_quality_synthesis.py
?? operations/analysis/h1_margin_threshold_readiness.py
?? operations/analysis/h1_poll_claim_readiness.py
?? operations/analysis/h1_poll_comparison_result.py
?? operations/analysis/h1_poll_comparison_unit_robustness.py
?? operations/analysis/h1_poll_decision_matrix.py
?? operations/analysis/h1_poll_scope_frontier.py
?? operations/analysis/h1_popular_vote_extension.py
?? operations/analysis/h1_rieke_state_forecast_extension.py
?? operations/analysis/h1_robust_poll_scope_quality.py
?? operations/analysis/h1_robust_poll_scope_unit_quality.py
?? operations/analysis/h1_state_poll_panel_competitiveness_diagnostic.py
?? operations/analysis/h1_state_poll_panel_extension.py
?? operations/analysis/h1_state_poll_panel_horizon_diagnostic.py
?? operations/analysis/h1_state_poll_panel_horizon_state_diagnostic.py
?? operations/analysis/h1_state_poll_panel_near_window_quality.py
?? operations/analysis/h1_state_poll_panel_state_significance.py
?? operations/analysis/h1_state_poll_panel_temporal_diagnostic.py
?? operations/analysis/h1_state_poll_snapshot_extension.py
?? operations/analysis/h1_state_source_consensus.py
?? operations/project/build_dozenten_report.py
?? tests/test_dozenten_report.py
?? tests/test_h1_270towin_poll_average_extension.py
?? tests/test_h1_270towin_state_forecast_extension.py
?? tests/test_h1_calibration_diagnostic.py
?? tests/test_h1_claim_evidence_audit.py
?? tests/test_h1_competitive_state_diagnostic.py
?? tests/test_h1_direct_poll_loss_decomposition.py
?? tests/test_h1_direct_poll_outlier_robustness.py
?? tests/test_h1_direct_poll_state_cluster_diagnostic.py
?? tests/test_h1_evidence_scope.py
?? tests/test_h1_expansion_readiness.py
?? tests/test_h1_final_snapshot_extension.py
?? tests/test_h1_forecast_quality.py
?? tests/test_h1_forecast_quality_synthesis.py
?? tests/test_h1_margin_threshold_readiness.py
?? tests/test_h1_poll_claim_readiness.py
?? tests/test_h1_poll_comparison_result.py
?? tests/test_h1_poll_comparison_unit_robustness.py
?? tests/test_h1_poll_decision_matrix.py
?? tests/test_h1_poll_scope_frontier.py
?? tests/test_h1_popular_vote_extension.py
?? tests/test_h1_rieke_state_forecast_extension.py
?? tests/test_h1_robust_poll_scope_quality.py
?? tests/test_h1_robust_poll_scope_unit_quality.py
?? tests/test_h1_state_poll_panel_competitiveness_diagnostic.py
?? tests/test_h1_state_poll_panel_extension.py
?? tests/test_h1_state_poll_panel_horizon_diagnostic.py
?? tests/test_h1_state_poll_panel_horizon_state_diagnostic.py
?? tests/test_h1_state_poll_panel_near_window_quality.py
?? tests/test_h1_state_poll_panel_state_significance.py
?? tests/test_h1_state_poll_panel_temporal_diagnostic.py
?? tests/test_h1_state_poll_snapshot_extension.py
?? tests/test_h1_state_source_consensus.py
```

Git diff stat:

```text
 STATUS.md                      |  286 +++-
 docs/project/WORK_LOG.md       | 2865 ++++++++++++++++++++++++++++++++++++++++
 docs/research/RESEARCH_SPEC.md | 1333 ++++++++++++++++++-
 requirements.txt               |    3 +
 4 files changed, 4393 insertions(+), 94 deletions(-)
```

Blockers:

- Worktree has uncommitted changes that need review before commit.

Next recommended action:

- feat: add swiss referendum information response view
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
