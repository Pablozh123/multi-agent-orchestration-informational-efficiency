# STATUS.md

<!-- PROJECT_STATUS:START -->
## Automation Snapshot

Generated: 2026-07-03 07:16

Current goal: `goal-h3-informed-trading-signature-001` - Build tested H3 informed-trading signature diagnostics

Current roadmap phase: Phase 13: H3 Informed-Trading Signature Diagnostics

Test status: FAIL

Pytest summary: `1 failed, 699 passed in 71.83s (0:01:11)`

Git branch: `main`

Latest commit: `e231dee`

Git status:

```text
D  .claude/settings.json
D  .claude/settings.local.json
D  .claude/skills/brier-score/SKILL.md
D  .claude/skills/dune-analytics/SKILL.md
D  .claude/skills/fastmcp-server/SKILL.md
D  .claude/skills/polymarket-api/SKILL.md
D  .gitignore
D  AGENTS.md
D  ARCHITECTURE_DECISIONS.md
D  CLAUDE.md
D  GOAL.md
D  PROJECT_CONTEXT.md
D  PROJEKT_SYNC_2026-06-16.md
D  ROADMAP.md
D  SCHREIBFAHRPLAN.md
D  STATUS.md
D  data/events_catalog.json
D  data/events_timeline_seed.csv
D  data/literature/literature_index.csv
D  data/market_maker_exclusions.json
D  data/monitor_anomaly_review_decisions.csv
D  data/monitor_anomaly_review_status_updates.csv
D  data/monitor_v2_curated_watchlist.csv
D  data/reference_cases/wallet_reference_cases.csv
D  data/reference_cases/wallet_reference_cases_metadata.json
D  data/results/agent_review_queue_dashboard.html
D  data/results/agent_review_queue_dashboard_metadata.json
D  data/results/h1_270towin_poll_average.png
D  data/results/h1_270towin_poll_average_cases.csv
D  data/results/h1_270towin_poll_average_metadata.json
D  data/results/h1_270towin_poll_average_summary.csv
D  data/results/h1_270towin_state_forecast.png
D  data/results/h1_270towin_state_forecast_cases.csv
D  data/results/h1_270towin_state_forecast_metadata.json
D  data/results/h1_270towin_state_forecast_summary.csv
D  data/results/h1_brier_scores.csv
D  data/results/h1_calibration_diagnostic.png
D  data/results/h1_calibration_diagnostic_bins.csv
D  data/results/h1_calibration_diagnostic_cases.csv
D  data/results/h1_calibration_diagnostic_metadata.json
D  data/results/h1_calibration_diagnostic_pairwise.csv
D  data/results/h1_calibration_diagnostic_summary.csv
D  data/results/h1_claim_evidence_audit.csv
D  data/results/h1_claim_evidence_audit.png
D  data/results/h1_claim_evidence_audit_metadata.json
D  data/results/h1_claim_evidence_audit_summary.csv
D  data/results/h1_competitive_state_diagnostic.png
D  data/results/h1_competitive_state_diagnostic_cases.csv
D  data/results/h1_competitive_state_diagnostic_metadata.json
D  data/results/h1_competitive_state_diagnostic_summary.csv
D  data/results/h1_competitive_state_diagnostic_tiers.csv
D  data/results/h1_diebold_mariano.json
D  data/results/h1_direct_poll_loss_decomposition.png
D  data/results/h1_direct_poll_loss_decomposition_cases.csv
D  data/results/h1_direct_poll_loss_decomposition_metadata.json
D  data/results/h1_direct_poll_loss_decomposition_summary.csv
D  data/results/h1_direct_poll_outlier_robustness.png
D  data/results/h1_direct_poll_outlier_robustness_metadata.json
D  data/results/h1_direct_poll_outlier_robustness_scenarios.csv
D  data/results/h1_direct_poll_outlier_robustness_summary.csv
D  data/results/h1_direct_poll_state_cluster_diagnostic.png
D  data/results/h1_direct_poll_state_cluster_diagnostic_metadata.json
D  data/results/h1_direct_poll_state_cluster_diagnostic_states.csv
D  data/results/h1_direct_poll_state_cluster_diagnostic_summary.csv
D  data/results/h1_evidence_scope.csv
D  data/results/h1_evidence_scope.png
D  data/results/h1_evidence_scope_metadata.json
D  data/results/h1_expansion_readiness.csv
D  data/results/h1_expansion_readiness.png
D  data/results/h1_expansion_readiness_metadata.json
D  data/results/h1_final_snapshot.png
D  data/results/h1_final_snapshot_cases.csv
D  data/results/h1_final_snapshot_metadata.json
D  data/results/h1_final_snapshot_summary.csv
D  data/results/h1_forecast_quality.png
D  data/results/h1_forecast_quality_metadata.json
D  data/results/h1_forecast_quality_pairwise.csv
D  data/results/h1_forecast_quality_sources.csv
D  data/results/h1_forecast_quality_synthesis.csv
D  data/results/h1_forecast_quality_synthesis.png
D  data/results/h1_forecast_quality_synthesis_metadata.json
D  data/results/h1_margin_threshold_readiness.csv
D  data/results/h1_margin_threshold_readiness.png
D  data/results/h1_margin_threshold_readiness_metadata.json
D  data/results/h1_poll_claim_readiness.csv
D  data/results/h1_poll_claim_readiness.png
D  data/results/h1_poll_claim_readiness_metadata.json
D  data/results/h1_poll_claim_readiness_summary.csv
D  data/results/h1_poll_comparison_result.csv
D  data/results/h1_poll_comparison_result.png
D  data/results/h1_poll_comparison_result_metadata.json
D  data/results/h1_poll_comparison_result_summary.csv
D  data/results/h1_poll_comparison_unit_robustness.png
D  data/results/h1_poll_comparison_unit_robustness_metadata.json
D  data/results/h1_poll_comparison_unit_robustness_summary.csv
D  data/results/h1_poll_comparison_unit_robustness_units.csv
D  data/results/h1_poll_decision_matrix.csv
D  data/results/h1_poll_decision_matrix.png
D  data/results/h1_poll_decision_matrix_metadata.json
D  data/results/h1_poll_decision_matrix_summary.csv
D  data/results/h1_poll_scope_frontier.csv
D  data/results/h1_poll_scope_frontier.png
D  data/results/h1_poll_scope_frontier_metadata.json
D  data/results/h1_poll_scope_frontier_summary.csv
D  data/results/h1_popular_vote.png
D  data/results/h1_popular_vote_cases.csv
D  data/results/h1_popular_vote_metadata.json
D  data/results/h1_popular_vote_summary.csv
D  data/results/h1_reliability_curve.png
D  data/results/h1_rieke_state_forecast.png
D  data/results/h1_rieke_state_forecast_cases.csv
D  data/results/h1_rieke_state_forecast_metadata.json
D  data/results/h1_rieke_state_forecast_summary.csv
D  data/results/h1_robust_poll_scope_quality.png
D  data/results/h1_robust_poll_scope_quality_bins.csv
D  data/results/h1_robust_poll_scope_quality_metadata.json
D  data/results/h1_robust_poll_scope_quality_pairwise.csv
D  data/results/h1_robust_poll_scope_quality_rows.csv
D  data/results/h1_robust_poll_scope_quality_summary.csv
D  data/results/h1_robust_poll_scope_unit_quality.png
D  data/results/h1_robust_poll_scope_unit_quality_metadata.json
D  data/results/h1_robust_poll_scope_unit_quality_summary.csv
D  data/results/h1_robust_poll_scope_unit_quality_units.csv
D  data/results/h1_state_poll_panel.png
D  data/results/h1_state_poll_panel_cases.csv
D  data/results/h1_state_poll_panel_competitiveness.png
D  data/results/h1_state_poll_panel_competitiveness_grid.csv
D  data/results/h1_state_poll_panel_competitiveness_metadata.json
D  data/results/h1_state_poll_panel_competitiveness_state.csv
D  data/results/h1_state_poll_panel_competitiveness_summary.csv
D  data/results/h1_state_poll_panel_coverage.csv
D  data/results/h1_state_poll_panel_horizon_claim_audit.csv
D  data/results/h1_state_poll_panel_horizon_diagnostic.png
D  data/results/h1_state_poll_panel_horizon_diagnostic_metadata.json
D  data/results/h1_state_poll_panel_horizon_state_summary.csv
D  data/results/h1_state_poll_panel_horizon_state_support.csv
D  data/results/h1_state_poll_panel_horizon_state_support.png
D  data/results/h1_state_poll_panel_horizon_state_support_metadata.json
D  data/results/h1_state_poll_panel_horizon_state_support_summary.csv
D  data/results/h1_state_poll_panel_horizon_summary.csv
D  data/results/h1_state_poll_panel_metadata.json
D  data/results/h1_state_poll_panel_near_window_quality.png
D  data/results/h1_state_poll_panel_near_window_quality_bins.csv
D  data/results/h1_state_poll_panel_near_window_quality_metadata.json
D  data/results/h1_state_poll_panel_near_window_quality_rows.csv
D  data/results/h1_state_poll_panel_near_window_quality_summary.csv
D  data/results/h1_state_poll_panel_state_significance.csv
D  data/results/h1_state_poll_panel_state_significance.png
D  data/results/h1_state_poll_panel_state_significance_metadata.json
D  data/results/h1_state_poll_panel_state_significance_summary.csv
D  data/results/h1_state_poll_panel_state_summary.csv
D  data/results/h1_state_poll_panel_summary.csv
D  data/results/h1_state_poll_panel_temporal_claim_audit.csv
D  data/results/h1_state_poll_panel_temporal_diagnostic.png
D  data/results/h1_state_poll_panel_temporal_diagnostic_metadata.json
D  data/results/h1_state_poll_panel_temporal_state_month.csv
D  data/results/h1_state_poll_panel_temporal_summary.csv
D  data/results/h1_state_poll_snapshot.png
D  data/results/h1_state_poll_snapshot_cases.csv
D  data/results/h1_state_poll_snapshot_coverage.csv
D  data/results/h1_state_poll_snapshot_coverage.png
D  data/results/h1_state_poll_snapshot_metadata.json
D  data/results/h1_state_poll_snapshot_sensitivity.csv
D  data/results/h1_state_poll_snapshot_sensitivity.png
D  data/results/h1_state_poll_snapshot_summary.csv
D  data/results/h1_state_source_consensus.png
D  data/results/h1_state_source_consensus_cases.csv
D  data/results/h1_state_source_consensus_metadata.json
D  data/results/h1_state_source_consensus_state_summary.csv
D  data/results/h1_state_source_consensus_summary.csv
D  data/results/h2_event_window_rows.csv
D  data/results/h2_event_window_summary.csv
D  data/results/h3_event_wallet_anomaly_metadata.json
D  data/results/h3_event_wallet_anomaly_rows.csv
D  data/results/h3_event_wallet_anomaly_summary.csv
D  data/results/h3_event_wallet_profile_exploratory.csv
D  data/results/h3_granger_metadata.json
D  data/results/h3_granger_results.csv
D  data/results/h3_informed_trading_profile.png
D  data/results/h3_informed_trading_signature.csv
D  data/results/h3_informed_trading_signature.png
D  data/results/h3_informed_trading_signature_metadata.json
D  data/results/h3_lead_lag_correlations.csv
D  data/results/h3_lead_time_event_rows.csv
D  data/results/h3_lead_time_histograms.csv
D  data/results/h3_lead_time_histograms_metadata.json
D  data/results/h3_tiered_wallet_activity_daily.csv
D  data/results/h3_tiered_wallet_activity_metadata.json
D  data/results/h3_wallet_distribution_inventory.json
D  data/results/h3_wallet_tiers.csv
D  data/results/h3_wallet_tiers_metadata.json
D  data/results/monitor_anomaly_case_review_packets.csv
D  data/results/monitor_anomaly_case_review_packets.json
D  data/results/monitor_anomaly_review_access_contract.json
D  data/results/monitor_anomaly_review_dashboard.html
D  data/results/monitor_anomaly_review_decision_readiness.csv
D  data/results/monitor_anomaly_review_decision_readiness.json
D  data/results/monitor_anomaly_review_metadata.json
D  data/results/monitor_anomaly_review_queue.csv
D  data/results/monitor_anomaly_review_status_transitions.csv
D  data/results/monitor_anomaly_review_status_transitions.json
D  data/results/monitor_anomaly_review_summary.csv
D  data/results/monitor_candidate_human_review_report.csv
D  data/results/monitor_candidate_human_review_report.html
D  data/results/monitor_candidate_human_review_report_metadata.json
D  data/results/monitor_candidate_materiality_context.csv
D  data/results/monitor_detection_backtest_cases.csv
D  data/results/monitor_detection_backtest_dashboard.html
D  data/results/monitor_detection_backtest_metadata.json
D  data/results/monitor_detection_backtest_summary.csv
D  data/results/monitor_literature_risk_score_metadata.json
D  data/results/monitor_literature_risk_score_rows.csv
D  data/results/monitor_literature_risk_score_summary.csv
D  data/results/monitor_reference_candidate_dashboard.html
D  data/results/monitor_reference_candidate_features.csv
D  data/results/monitor_reference_candidate_metadata.json
D  data/results/monitor_reference_candidate_sensitivity_dashboard.html
D  data/results/monitor_reference_candidate_sensitivity_features.csv
D  data/results/monitor_reference_candidate_sensitivity_metadata.json
D  data/results/monitor_reference_candidate_sensitivity_rows.csv
D  data/results/monitor_reference_candidate_sensitivity_similarity_scores.csv
D  data/results/monitor_reference_candidate_sensitivity_similarity_summary.csv
D  data/results/monitor_reference_candidate_sensitivity_summary.csv
D  data/results/monitor_reference_candidate_similarity_scores.csv
D  data/results/monitor_reference_candidate_similarity_summary.csv
D  data/results/monitor_reference_candidate_summary.csv
D  data/results/monitor_v2_alert_rows.csv
D  data/results/monitor_v2_alert_summary.csv
D  data/results/monitor_v2_bounded_summary.csv
D  data/results/monitor_v2_bounded_summary_metadata.json
D  data/results/monitor_v2_curated_watchlist_validation_report.json
D  data/results/monitor_v2_event_proximity_sensitivity_metadata.json
D  data/results/monitor_v2_event_proximity_sensitivity_rows.csv
D  data/results/monitor_v2_event_proximity_sensitivity_summary.csv
D  data/results/monitor_v2_historical_replay_alert_rows.csv
D  data/results/monitor_v2_historical_replay_alert_summary.csv
D  data/results/monitor_v2_historical_replay_context_rows.csv
D  data/results/monitor_v2_historical_replay_metadata.json
D  data/results/monitor_v2_historical_replay_snapshots.csv
D  data/results/monitor_v2_live_alert_rows.csv
D  data/results/monitor_v2_live_alert_summary.csv
D  data/results/monitor_v2_live_event_candidates.csv
D  data/results/monitor_v2_live_input_validation_report.json
D  data/results/monitor_v2_live_inputs_metadata.json
D  data/results/monitor_v2_live_market_snapshots.csv
D  data/results/monitor_v2_live_scoring_metadata.json
D  data/results/monitor_v2_live_scoring_snapshots.csv
D  data/results/monitor_v2_live_scoring_validation_report.json
D  data/results/monitor_v2_live_wallet_tier_snapshots.csv
D  data/results/monitor_v2_live_watchlist.csv
D  data/results/monitor_v2_live_window_registry.csv
D  data/results/monitor_v2_live_window_registry_metadata.json
D  data/results/monitor_v2_metadata.json
D  data/results/monitor_v2_polymarket_dashboard.html
D  data/results/monitor_v2_polymarket_dashboard_metadata.json
D  data/results/monitor_v2_polymarket_live_alert_rows.csv
D  data/results/monitor_v2_polymarket_live_alert_summary.csv
D  data/results/monitor_v2_polymarket_live_collection_metadata.json
D  data/results/monitor_v2_polymarket_live_event_candidates.csv
D  data/results/monitor_v2_polymarket_live_figure_metadata.json
D  data/results/monitor_v2_polymarket_live_input_validation_report.json
D  data/results/monitor_v2_polymarket_live_market_snapshots.csv
D  data/results/monitor_v2_polymarket_live_scoring_metadata.json
D  data/results/monitor_v2_polymarket_live_scoring_snapshots.csv
D  data/results/monitor_v2_polymarket_live_scoring_validation_report.json
D  data/results/monitor_v2_polymarket_live_snapshot.png
D  data/results/monitor_v2_polymarket_live_wallet_tier_snapshots.csv
D  data/results/monitor_v2_polymarket_live_watchlist.csv
D  data/results/monitor_v2_polymarket_public_wallet_activity.csv
D  data/results/monitor_v2_polymarket_public_wallet_activity_metadata.json
D  data/results/monitor_v2_polymarket_refresh_metadata.json
D  data/results/monitor_v2_polymarket_rolling_alert_rows.csv
D  data/results/monitor_v2_polymarket_rolling_alert_summary.csv
D  data/results/monitor_v2_polymarket_rolling_history.png
D  data/results/monitor_v2_polymarket_rolling_history_figure_metadata.json
D  data/results/monitor_v2_polymarket_rolling_history_metadata.json
D  data/results/monitor_v2_polymarket_rolling_scoring_metadata.json
D  data/results/monitor_v2_polymarket_rolling_scoring_snapshots.csv
D  data/results/monitor_v2_polymarket_rolling_scoring_validation_report.json
D  data/results/monitor_v2_polymarket_threshold_sensitivity.csv
D  data/results/monitor_v2_polymarket_threshold_sensitivity.png
D  data/results/monitor_v2_polymarket_threshold_sensitivity_by_family.csv
D  data/results/monitor_v2_polymarket_threshold_sensitivity_metadata.json
D  data/results/monitor_v2_recorded_alert_rows.csv
D  data/results/monitor_v2_recorded_alert_summary.csv
D  data/results/monitor_v2_recorded_context_rows.csv
D  data/results/monitor_v2_recorded_event_candidates.csv
D  data/results/monitor_v2_recorded_input_validation_report.json
D  data/results/monitor_v2_recorded_inputs_metadata.json
D  data/results/monitor_v2_recorded_market_snapshots.csv
D  data/results/monitor_v2_recorded_scoring_metadata.json
D  data/results/monitor_v2_recorded_scoring_snapshots.csv
D  data/results/monitor_v2_recorded_scoring_validation_report.json
D  data/results/monitor_v2_recorded_wallet_tier_snapshots.csv
D  data/results/monitor_v2_recorded_watchlist.csv
D  data/results/swiss_referendum_10mio_auto_refresh_log.csv
D  data/results/swiss_referendum_10mio_auto_refresh_metadata.json
D  data/results/swiss_referendum_10mio_comparison.csv
D  data/results/swiss_referendum_10mio_dashboard.html
D  data/results/swiss_referendum_10mio_efficiency.png
D  data/results/swiss_referendum_10mio_efficiency_metadata.json
D  data/results/swiss_referendum_10mio_final_case_study.csv
D  data/results/swiss_referendum_10mio_final_case_study.png
D  data/results/swiss_referendum_10mio_final_case_study_metadata.json
D  data/results/swiss_referendum_10mio_history_accuracy_windows.csv
D  data/results/swiss_referendum_10mio_information_response.csv
D  data/results/swiss_referendum_10mio_information_response.png
D  data/results/swiss_referendum_10mio_latest_source_comparison.csv
D  data/results/swiss_referendum_10mio_latest_summary.md
D  data/results/swiss_referendum_10mio_live_accuracy_windows.csv
D  data/results/swiss_referendum_10mio_poll_accuracy.csv
D  data/results/swiss_referendum_10mio_poll_impacts.csv
D  data/results/swiss_referendum_10mio_poll_reaction_windows.csv
D  data/results/swiss_referendum_10mio_polymarket_price_history.csv
D  data/results/swiss_referendum_10mio_polymarket_price_history_metadata.json
D  data/results/swiss_referendum_10mio_polymarket_snapshot_metadata.json
D  data/results/swiss_referendum_10mio_polymarket_snapshots.csv
D  data/results/swiss_referendum_10mio_reaction_windows.png
D  data/results/swiss_referendum_10mio_refresh_metadata.json
D  data/results/swiss_referendum_10mio_running_status.json
D  data/results/swiss_referendum_10mio_source_audit.csv
D  data/results/thesis_advisor_alignment_checklist.csv
D  data/results/thesis_advisor_feedback_integration_checklist.csv
D  data/results/thesis_advisor_feedback_log_template.csv
D  data/results/thesis_advisor_handoff_note.csv
D  data/results/thesis_advisor_handoff_package.csv
D  data/results/thesis_advisor_source_review_followup.csv
D  data/results/thesis_agent_assistance_protocol.csv
D  data/results/thesis_agent_future_work_handoff.csv
D  data/results/thesis_agent_pipeline_control_audit.csv
D  data/results/thesis_agent_pipeline_roadmap.csv
D  data/results/thesis_agent_pipeline_safety_case.csv
D  data/results/thesis_agent_pipeline_upgrade_plan.csv
D  data/results/thesis_chapter_plan.csv
D  data/results/thesis_chapter_source_bindings.csv
D  data/results/thesis_chapter_source_review_checklist.csv
D  data/results/thesis_citation_readiness.csv
D  data/results/thesis_citation_review_packets.csv
D  data/results/thesis_consolidation_index.csv
D  data/results/thesis_consolidation_metadata.json
D  data/results/thesis_core_results_table.csv
D  data/results/thesis_curated_result_package.csv
D  data/results/thesis_drafting_sequence.csv
D  data/results/thesis_evidence_map.csv
D  data/results/thesis_evidence_map.md
D  data/results/thesis_execution_checklist.csv
D  data/results/thesis_figures_metadata.json
D  data/results/thesis_final_gate_board.csv
D  data/results/thesis_goal_completion_audit.csv
D  data/results/thesis_h1_h2_h3_bounded_chapter_draft.csv
D  data/results/thesis_h1_h2_h3_core_sections.csv
D  data/results/thesis_h1_h2_h3_decision_queue_ledger_alignment.csv
D  data/results/thesis_h1_h2_h3_decision_queue_overview.csv
D  data/results/thesis_h1_h2_h3_drafting_checklist.csv
D  data/results/thesis_h1_h2_h3_manual_source_review_execution_pass.csv
D  data/results/thesis_h1_h2_h3_source_gated_thesis_drafting_pass.csv
D  data/results/thesis_h1_h2_h3_source_gated_writing_pass.csv
D  data/results/thesis_h1_h2_h3_source_review_notes.csv
D  data/results/thesis_h1_h2_h3_worksheet_drafting_bridge.csv
D  data/results/thesis_h1_manual_source_review_followup.csv
D  data/results/thesis_h1_source_review_batch_worksheet.csv
D  data/results/thesis_h1_source_review_decision_queue.csv
D  data/results/thesis_h1_source_review_ledger_fill_guide.csv
D  data/results/thesis_h1_summary.csv
D  data/results/thesis_h2_event_window_car.png
D  data/results/thesis_h2_manual_source_review_followup.csv
D  data/results/thesis_h2_source_review_batch_worksheet.csv
D  data/results/thesis_h2_source_review_decision_queue.csv
D  data/results/thesis_h2_source_review_ledger_fill_guide.csv
D  data/results/thesis_h2_summary.csv
D  data/results/thesis_h3_event_wallet_anomalies.png
D  data/results/thesis_h3_granger_pvalues.png
D  data/results/thesis_h3_lead_time_amount.png
D  data/results/thesis_h3_manual_source_review_followup.csv
D  data/results/thesis_h3_source_review_batch_worksheet.csv
D  data/results/thesis_h3_source_review_decision_queue.csv
D  data/results/thesis_h3_source_review_ledger_fill_guide.csv
D  data/results/thesis_h3_summary.csv
D  data/results/thesis_h3_wallet_tier_counts.png
D  data/results/thesis_highlevel_next_step_control_summary.csv
D  data/results/thesis_highlevel_thesis_writing_handoff.csv
D  data/results/thesis_ledger_citation_gate_summary.csv
D  data/results/thesis_manual_source_review_followup_overview.csv
D  data/results/thesis_manual_source_review_update_checklist.csv
D  data/results/thesis_method_interpretation_source_coverage.csv
D  data/results/thesis_method_interpretation_traceability.csv
D  data/results/thesis_monitor_v2_recorded_scoring.png
D  data/results/thesis_next_work_plan.csv
D  data/results/thesis_project_highlevel_view.csv
D  data/results/thesis_result_package_traceability.csv
D  data/results/thesis_result_summary_metadata.json
D  data/results/thesis_source_access_audit.csv
D  data/results/thesis_source_review_batch_execution_plan.csv
D  data/results/thesis_source_review_chapter_handoff.csv
D  data/results/thesis_source_review_decision_packets.csv
D  data/results/thesis_source_review_execution.csv
D  data/results/thesis_source_review_ledger_FILLED_DRAFT.csv
D  data/results/thesis_source_review_plan.csv
D  data/results/thesis_source_review_progress_ledger.csv
D  data/results/thesis_source_review_progress_protocol.csv
D  data/results/thesis_source_review_worksheet.csv
D  data/results/thesis_source_review_worksheet_overview.csv
D  data/results/thesis_source_structure_inventory.csv
D  data/results/thesis_submission_readiness_board.csv
D  data/results/thesis_table_figure_captions.csv
D  data/results/thesis_wording_guard.csv
D  data/results/wallet_graph_dashboard.html
D  data/results/wallet_graph_edges.csv
D  data/results/wallet_graph_metadata.json
D  data/results/wallet_graph_metrics.csv
D  data/results/wallet_graph_nodes.csv
D  data/results/wallet_reference_case_audit.csv
D  data/results/wallet_reference_case_audit_metadata.json
D  data/results/wallet_reference_pattern_features.csv
D  data/results/wallet_reference_pattern_features_metadata.json
D  data/results/wallet_reference_similarity_dashboard.html
D  data/results/wallet_reference_similarity_matrix.png
D  data/results/wallet_reference_similarity_metadata.json
D  data/results/wallet_reference_similarity_scores.csv
D  data/results/wallet_reference_similarity_summary.csv
D  data/swiss_referendum_10mio_official_result.csv
D  data/swiss_referendum_10mio_polls.csv
D  directives/coding_standards.md
D  directives/methodology.md
D  docs/legacy_inventory.md
D  docs/project/AGENT_TOOL_BLUEPRINT.md
D  docs/project/CODE_REVIEW_CHECKLIST.md
D  docs/project/COMMIT_PROTOCOL.md
D  docs/project/DOZENTEN_ABSPRACHE_CHECKLIST.md
D  docs/project/DOZENTEN_FEEDBACK_INTEGRATION_CHECKLIST.md
D  docs/project/DOZENTEN_FEEDBACK_LOG.md
D  docs/project/DOZENTEN_UEBERGABE_TEXT.md
D  docs/project/FHNW_ACADEMICGUIDE_RULES.md
D  docs/project/FHNW_VORGABEN.md
D  docs/project/NEXT_GOAL_informed_trading_signature.md
D  docs/project/PROJEKT_KONSOLIDIERUNG_2026-06-17.md
D  docs/project/PROZESS_ZUSAMMENFASSUNG_DOZENT.md
D  docs/project/QUELLEN_REVIEW_ABHAKLISTE.md
D  docs/project/QUELLEN_VORSCHLAEGE_UND_REVIEW.md
D  docs/project/SOURCE_REVIEW_LOG.md
D  docs/project/SOURCE_REVIEW_PACK.md
D  docs/project/THESIS_ADVISOR_HANDOFF_PACKAGE.md
D  docs/project/THESIS_ADVISOR_SOURCE_REVIEW_FOLLOWUP.md
D  docs/project/THESIS_AGENT_FUTURE_WORK_HANDOFF.md
D  docs/project/THESIS_AGENT_PIPELINE_CONTROL_AUDIT.md
D  docs/project/THESIS_AGENT_PIPELINE_SAFETY_CASE.md
D  docs/project/THESIS_CHAPTER_SOURCE_BINDINGS.md
D  docs/project/THESIS_CHAPTER_SOURCE_REVIEW_CHECKLIST.md
D  docs/project/THESIS_CONSOLIDATION_INDEX.md
D  docs/project/THESIS_DRAFTING_SEQUENCE.md
D  docs/project/THESIS_EXECUTION_CHECKLIST.md
D  docs/project/THESIS_FINAL_GATE_BOARD.md
D  docs/project/THESIS_GOAL_COMPLETION_AUDIT.md
D  docs/project/THESIS_H1_H2_H3_DECISION_QUEUE_LEDGER_ALIGNMENT.md
D  docs/project/THESIS_H1_H2_H3_DECISION_QUEUE_OVERVIEW.md
D  docs/project/THESIS_H1_H2_H3_DRAFTING_CHECKLIST.md
D  docs/project/THESIS_H1_H2_H3_MANUAL_SOURCE_REVIEW_EXECUTION_PASS.md
D  docs/project/THESIS_H1_H2_H3_SOURCE_REVIEW_NOTES.md
D  docs/project/THESIS_H1_H2_H3_WORKSHEET_DRAFTING_BRIDGE.md
D  docs/project/THESIS_H1_MANUAL_SOURCE_REVIEW_FOLLOWUP.md
D  docs/project/THESIS_H1_SOURCE_REVIEW_BATCH_WORKSHEET.md
D  docs/project/THESIS_H1_SOURCE_REVIEW_DECISION_QUEUE.md
D  docs/project/THESIS_H1_SOURCE_REVIEW_LEDGER_FILL_GUIDE.md
D  docs/project/THESIS_H2_MANUAL_SOURCE_REVIEW_FOLLOWUP.md
D  docs/project/THESIS_H2_SOURCE_REVIEW_BATCH_WORKSHEET.md
D  docs/project/THESIS_H2_SOURCE_REVIEW_DECISION_QUEUE.md
D  docs/project/THESIS_H2_SOURCE_REVIEW_LEDGER_FILL_GUIDE.md
D  docs/project/THESIS_H3_MANUAL_SOURCE_REVIEW_FOLLOWUP.md
D  docs/project/THESIS_H3_SOURCE_REVIEW_BATCH_WORKSHEET.md
D  docs/project/THESIS_H3_SOURCE_REVIEW_DECISION_QUEUE.md
D  docs/project/THESIS_H3_SOURCE_REVIEW_LEDGER_FILL_GUIDE.md
D  docs/project/THESIS_HIGHLEVEL_NEXT_STEP_CONTROL_SUMMARY.md
D  docs/project/THESIS_HIGHLEVEL_THESIS_WRITING_HANDOFF.md
D  docs/project/THESIS_LEDGER_CITATION_GATE_SUMMARY.md
D  docs/project/THESIS_MANUAL_SOURCE_REVIEW_FOLLOWUP_OVERVIEW.md
D  docs/project/THESIS_MANUAL_SOURCE_REVIEW_UPDATE_CHECKLIST.md
D  docs/project/THESIS_METHOD_INTERPRETATION_SOURCE_COVERAGE.md
D  docs/project/THESIS_SOURCE_ACCESS_AUDIT.md
D  docs/project/THESIS_SOURCE_REVIEW_BATCH_EXECUTION_PLAN.md
D  docs/project/THESIS_SOURCE_REVIEW_CHAPTER_HANDOFF.md
D  docs/project/THESIS_SOURCE_REVIEW_DECISION_PACKETS.md
D  docs/project/THESIS_SOURCE_REVIEW_EXECUTION.md
D  docs/project/THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md
D  docs/project/THESIS_SOURCE_REVIEW_PROGRESS_PROTOCOL.md
D  docs/project/THESIS_SOURCE_REVIEW_WORKSHEET_OVERVIEW.md
D  docs/project/THESIS_SOURCE_STRUCTURE_INVENTORY.md
D  docs/project/THESIS_STRUKTUR_FHNW_VORSCHLAG.md
D  docs/project/THESIS_SUBMISSION_READINESS_BOARD.md
D  docs/project/THESIS_TRACEABILITY_AUDIT.md
D  docs/project/TOOL_USAGE.md
D  docs/project/WORK_LOG.md
D  docs/project/dozentenbericht_assets/project_pipeline_overview.png
D  docs/project/dozentenbericht_ba_thesis.docx
D  docs/project/dozentenbericht_ba_thesis.html
D  docs/project/dozentenbericht_ba_thesis.md
D  docs/project/dozentenbericht_ba_thesis_h1_forecast_quality.docx
D  docs/project/templates/HSW-FHNW_Dokumentvorlage-studentische-Arbeit-2023.docx
D  docs/research/EVENT_SELECTION.md
D  docs/research/LITERATURE_MAP.md
D  docs/research/RCP_TRANSFORMATION.md
D  docs/research/RESEARCH_SPEC.md
D  docs/research/STRATEGY_AGENT_ARCHITECTURE.md
D  docs/research/SWISS_REFERENDUM_EFFICIENCY.md
D  docs/research/SWISS_REFERENDUM_FINAL_CASE_STUDY.md
D  docs/research/THESIS_AGENT_ASSISTANCE_PROTOCOL.md
D  docs/research/THESIS_AGENT_PIPELINE_ROADMAP.md
D  docs/research/THESIS_AGENT_PIPELINE_UPGRADE_PLAN.md
D  docs/research/THESIS_CHAPTER_DRAFT.md
D  docs/research/THESIS_CITATION_REVIEW_PACKETS.md
D  docs/research/THESIS_CONSOLIDATION.md
D  docs/research/THESIS_H1_H2_H3_BOUNDED_CHAPTER_DRAFT.md
D  docs/research/THESIS_H1_H2_H3_CORE_SECTIONS.md
D  docs/research/THESIS_H1_H2_H3_SOURCE_GATED_THESIS_DRAFTING_PASS.md
D  docs/research/THESIS_H1_H2_H3_SOURCE_GATED_WRITING_PASS.md
D  docs/research/THESIS_KAPITEL_03_METHODIK_DRAFT.md
D  docs/research/THESIS_NEXT_WORK_PLAN.md
D  docs/research/THESIS_PROJECT_HIGHLEVEL_VIEW.md
D  docs/research/THESIS_SOURCE_REVIEW_PLAN.md
D  docs/research/THESIS_SOURCE_REVIEW_WORKSHEET.md
D  docs/research/THESIS_TABLE_FIGURE_CAPTIONS.md
D  docs/research/THESIS_WORDING_GUARD.md
D  docs/research/THESIS_WRITING_BLUEPRINT.md
D  docs/research/WALLET_REFERENCE_CASES.md
D  docs/research/WHALE_METHOD.md
D  ingest/__init__.py
D  ingest/dune.py
D  ingest/events.py
D  ingest/fivethirtyeight.py
D  ingest/gdelt.py
D  ingest/polymarket.py
D  ingest/rcp.py
D  init_db.py
D  legacy/audits/LEGACY_SCAN_2026-05-20.md
D  legacy/changelog/1b7be1de-9637-4012-9597-c0f81e6701c0.json
D  legacy/data/summaries.json
D  legacy/deferred_agents/market_agent.py
D  legacy/deferred_agents/orchestrator.py
D  legacy/deferred_agents/sentiment_agent.py
D  legacy/deferred_agents/whale_agent.py
D  legacy/deferred_mcp/thesis_mcp_server.py
D  legacy/deferred_prompts/roles/market_agent.md
D  legacy/deferred_prompts/roles/orchestrator.md
D  legacy/deferred_prompts/roles/reviewer.md
D  legacy/deferred_prompts/roles/sentiment_agent.md
D  legacy/deferred_prompts/roles/whale_agent.md
D  legacy/planning/.planning/PROJECT.md
D  legacy/planning/.planning/REQUIREMENTS.md
D  legacy/planning/.planning/ROADMAP.md
D  legacy/planning/.planning/STATE.md
D  legacy/planning/.planning/config.json
D  legacy/planning/.planning/phases/01-data-foundation/01-00-PLAN.md
D  legacy/planning/.planning/phases/01-data-foundation/01-00-SUMMARY.md
D  legacy/planning/.planning/phases/01-data-foundation/01-01-PLAN.md
D  legacy/planning/.planning/phases/01-data-foundation/01-01-SUMMARY.md
D  legacy/planning/.planning/phases/01-data-foundation/01-02-PLAN.md
D  legacy/planning/.planning/phases/01-data-foundation/01-02-SUMMARY.md
D  legacy/planning/.planning/phases/01-data-foundation/01-03-PLAN.md
D  legacy/planning/.planning/phases/01-data-foundation/01-03-SUMMARY.md
D  legacy/planning/.planning/phases/01-data-foundation/01-04-PLAN.md
D  legacy/planning/.planning/phases/01-data-foundation/01-04-SUMMARY.md
D  legacy/planning/.planning/phases/01-data-foundation/01-05-PLAN.md
D  legacy/planning/.planning/phases/01-data-foundation/01-05-SUMMARY.md
D  legacy/planning/.planning/phases/01-data-foundation/01-06-PLAN.md
D  legacy/planning/.planning/phases/01-data-foundation/01-06-SUMMARY.md
D  legacy/planning/.planning/phases/01-data-foundation/01-07-PLAN.md
D  legacy/planning/.planning/phases/01-data-foundation/01-08-PLAN.md
D  legacy/planning/.planning/phases/01-data-foundation/01-RESEARCH.md
D  legacy/planning/.planning/phases/01-data-foundation/01-VALIDATION.md
D  legacy/planning/.planning/phases/01-data-foundation/01-VERIFICATION.md
D  legacy/planning/.planning/research/ARCHITECTURE.md
D  legacy/planning/.planning/research/FEATURES.md
D  legacy/planning/.planning/research/PITFALLS.md
D  legacy/planning/.planning/research/STACK.md
D  legacy/planning/.planning/research/SUMMARY.md
D  legacy/prompts/.claude/settings.json
D  legacy/prompts/.claude/settings.local.json
D  legacy/prompts/.claude/skills/brier-score/SKILL.md
D  legacy/prompts/.claude/skills/dune-analytics/SKILL.md
D  legacy/prompts/.claude/skills/fastmcp-server/SKILL.md
D  legacy/prompts/.claude/skills/polymarket-api/SKILL.md
D  legacy/prompts/CLAUDE.md
D  legacy/prompts/README.md
D  legacy/prompts/directives/roles/market_agent.md
D  legacy/prompts/directives/roles/orchestrator.md
D  legacy/prompts/directives/roles/reviewer.md
D  legacy/prompts/directives/roles/sentiment_agent.md
D  legacy/prompts/directives/roles/whale_agent.md
D  operations/__init__.py
D  operations/agents/__init__.py
D  operations/agents/market_agent.py
D  operations/agents/orchestrator.py
D  operations/agents/review_queue/__init__.py
D  operations/agents/review_queue/_vendored_monitor_readonly.py
D  operations/agents/review_queue/case_narrative.py
D  operations/agents/review_queue/event_scout.py
D  operations/agents/review_queue/llm.py
D  operations/agents/review_queue/mcp_client.py
D  operations/agents/review_queue/orchestrator.py
D  operations/agents/review_queue/skeptic_reviewer.py
D  operations/agents/sentiment_agent.py
D  operations/agents/whale_agent.py
D  operations/analysis/__init__.py
D  operations/analysis/agent_review_queue_dashboard.py
D  operations/analysis/brier_score.py
D  operations/analysis/calibrate.py
D  operations/analysis/classify_wallet_tiers.py
D  operations/analysis/compute_brier_scores.py
D  operations/analysis/data_inventory.py
D  operations/analysis/event_study.py
D  operations/analysis/generate_summaries.py
D  operations/analysis/h1_270towin_poll_average_extension.py
D  operations/analysis/h1_270towin_state_forecast_extension.py
D  operations/analysis/h1_calibration_diagnostic.py
D  operations/analysis/h1_claim_evidence_audit.py
D  operations/analysis/h1_competitive_state_diagnostic.py
D  operations/analysis/h1_direct_poll_loss_decomposition.py
D  operations/analysis/h1_direct_poll_outlier_robustness.py
D  operations/analysis/h1_direct_poll_state_cluster_diagnostic.py
D  operations/analysis/h1_evidence_scope.py
D  operations/analysis/h1_expansion_readiness.py
D  operations/analysis/h1_final_snapshot_extension.py
D  operations/analysis/h1_forecast_quality.py
D  operations/analysis/h1_forecast_quality_synthesis.py
D  operations/analysis/h1_margin_threshold_readiness.py
D  operations/analysis/h1_poll_claim_readiness.py
D  operations/analysis/h1_poll_comparison_result.py
D  operations/analysis/h1_poll_comparison_unit_robustness.py
D  operations/analysis/h1_poll_decision_matrix.py
D  operations/analysis/h1_poll_scope_frontier.py
D  operations/analysis/h1_popular_vote_extension.py
D  operations/analysis/h1_rieke_state_forecast_extension.py
D  operations/analysis/h1_robust_poll_scope_quality.py
D  operations/analysis/h1_robust_poll_scope_unit_quality.py
D  operations/analysis/h1_state_poll_panel_competitiveness_diagnostic.py
D  operations/analysis/h1_state_poll_panel_extension.py
D  operations/analysis/h1_state_poll_panel_horizon_diagnostic.py
D  operations/analysis/h1_state_poll_panel_horizon_state_diagnostic.py
D  operations/analysis/h1_state_poll_panel_near_window_quality.py
D  operations/analysis/h1_state_poll_panel_state_significance.py
D  operations/analysis/h1_state_poll_panel_temporal_diagnostic.py
D  operations/analysis/h1_state_poll_snapshot_extension.py
D  operations/analysis/h1_state_source_consensus.py
D  operations/analysis/h3_event_wallet_anomalies.py
D  operations/analysis/h3_granger_baseline.py
D  operations/analysis/h3_lead_time_histograms.py
D  operations/analysis/informed_trading_signature.py
D  operations/analysis/monitor_anomaly_review_queue.py
D  operations/analysis/monitor_candidate_review_report.py
D  operations/analysis/monitor_detection_backtest.py
D  operations/analysis/monitor_literature_risk_scores.py
D  operations/analysis/monitor_reference_candidate_sensitivity.py
D  operations/analysis/monitor_reference_candidates.py
D  operations/analysis/monitor_v2_dashboard.py
D  operations/analysis/monitor_v2_event_proximity_sensitivity.py
D  operations/analysis/monitor_v2_historical_replay.py
D  operations/analysis/monitor_v2_input_validation.py
D  operations/analysis/monitor_v2_live_input_batch.py
D  operations/analysis/monitor_v2_live_input_scoring.py
D  operations/analysis/monitor_v2_live_input_validation.py
D  operations/analysis/monitor_v2_live_window_registry.py
D  operations/analysis/monitor_v2_polymarket_live_figures.py
D  operations/analysis/monitor_v2_polymarket_rolling_figures.py
D  operations/analysis/monitor_v2_recorded_input_adapter.py
D  operations/analysis/monitor_v2_recorded_input_scoring.py
D  operations/analysis/monitor_v2_result_summaries.py
D  operations/analysis/monitor_v2_snapshot.py
D  operations/analysis/monitor_v2_threshold_sensitivity.py
D  operations/analysis/monitor_wallet_graph.py
D  operations/analysis/persist_h2_summaries.py
D  operations/analysis/run_h2_event_windows.py
D  operations/analysis/swiss_referendum_efficiency.py
D  operations/analysis/swiss_referendum_final_case_study.py
D  operations/analysis/thesis_consolidation.py
D  operations/analysis/thesis_figures.py
D  operations/analysis/thesis_result_summaries.py
D  operations/analysis/thesis_source_review_worksheet.py
D  operations/analysis/thesis_wording_guard.py
D  operations/analysis/tiered_wallet_activity.py
D  operations/analysis/wallet_distribution_inventory.py
D  operations/analysis/wallet_reference_case_audit.py
D  operations/analysis/wallet_reference_pattern_features.py
D  operations/analysis/wallet_reference_similarity.py
D  operations/audit/__init__.py
D  operations/audit/logger.py
D  operations/collectors/__init__.py
D  operations/collectors/polymarket_monitor_refresh.py
D  operations/collectors/polymarket_public_activity.py
D  operations/collectors/polymarket_readonly.py
D  operations/collectors/polymarket_rolling_history.py
D  operations/collectors/polymarket_watchlist.py
D  operations/collectors/swiss_referendum_auto_refresh.py
D  operations/collectors/swiss_referendum_history.py
D  operations/collectors/swiss_referendum_polymarket.py
D  operations/collectors/swiss_referendum_refresh.py
D  operations/db/__init__.py
D  operations/db/migrations.py
D  operations/mcp/__init__.py
D  operations/mcp/monitor_readonly.py
D  operations/mcp/server.py
D  operations/mcp/thesis_mcp_server.py
D  operations/project/__init__.py
D  operations/project/build_advisor_alignment_checklist.py
D  operations/project/build_advisor_feedback_integration_checklist.py
D  operations/project/build_advisor_feedback_log.py
D  operations/project/build_advisor_handoff_note.py
D  operations/project/build_advisor_handoff_package.py
D  operations/project/build_advisor_source_review_followup.py
D  operations/project/build_agent_future_work_handoff.py
D  operations/project/build_agent_pipeline_control_audit.py
D  operations/project/build_agent_pipeline_safety_case.py
D  operations/project/build_chapter_source_bindings.py
D  operations/project/build_chapter_source_review_checklist.py
D  operations/project/build_dozenten_report.py
D  operations/project/build_h1_h2_h3_bounded_chapter_draft.py
D  operations/project/build_h1_h2_h3_decision_queue_ledger_alignment.py
D  operations/project/build_h1_h2_h3_decision_queue_overview.py
D  operations/project/build_h1_h2_h3_drafting_checklist.py
D  operations/project/build_h1_h2_h3_manual_source_review_execution_pass.py
D  operations/project/build_h1_h2_h3_source_gated_thesis_drafting_pass.py
D  operations/project/build_h1_h2_h3_source_gated_writing_pass.py
D  operations/project/build_h1_h2_h3_source_review_notes.py
D  operations/project/build_h1_h2_h3_worksheet_drafting_bridge.py
D  operations/project/build_h1_manual_source_review_followup.py
D  operations/project/build_h1_source_review_batch_worksheet.py
D  operations/project/build_h1_source_review_decision_queue.py
D  operations/project/build_h1_source_review_ledger_fill_guide.py
D  operations/project/build_h2_manual_source_review_followup.py
D  operations/project/build_h2_source_review_batch_worksheet.py
D  operations/project/build_h2_source_review_decision_queue.py
D  operations/project/build_h2_source_review_ledger_fill_guide.py
D  operations/project/build_h3_manual_source_review_followup.py
D  operations/project/build_h3_source_review_batch_worksheet.py
D  operations/project/build_h3_source_review_decision_queue.py
D  operations/project/build_h3_source_review_ledger_fill_guide.py
D  operations/project/build_highlevel_next_step_control_summary.py
D  operations/project/build_highlevel_thesis_writing_handoff.py
D  operations/project/build_ledger_citation_gate_summary.py
D  operations/project/build_manual_source_review_followup_overview.py
D  operations/project/build_manual_source_review_update_checklist.py
D  operations/project/build_method_interpretation_source_coverage.py
D  operations/project/build_source_access_audit.py
D  operations/project/build_source_review_batch_execution_plan.py
D  operations/project/build_source_review_chapter_handoff.py
D  operations/project/build_source_review_decision_packets.py
D  operations/project/build_source_review_execution_guide.py
D  operations/project/build_source_review_progress_ledger.py
D  operations/project/build_source_review_progress_protocol.py
D  operations/project/build_source_review_worksheet_overview.py
D  operations/project/build_source_structure_inventory.py
D  operations/project/build_submission_readiness_board.py
D  operations/project/build_thesis_consolidation_index.py
D  operations/project/build_thesis_core_writing_package.py
D  operations/project/build_thesis_drafting_sequence.py
D  operations/project/build_thesis_execution_checklist.py
D  operations/project/build_thesis_final_gate_board.py
D  operations/project/build_thesis_goal_completion_audit.py
D  operations/project/build_thesis_traceability_audit.py
D  operations/project/commit_plan.py
D  operations/project/init.py
D  operations/project/review_check.py
D  operations/project/update_status.py
D  operations/tools/__init__.py
D  operations/tools/agent_review_queue_launcher.py
D  operations/tools/api_clients.py
D  operations/tools/db_tools.py
D  operations/tools/event_catalog_audit.py
D  operations/tools/load_events.py
D  operations/tools/monitor_dashboard_launcher.py
D  operations/validation/__init__.py
D  operations/validation/pandera_schemas.py
D  operations/validation/report.py
D  operations/validation/schemas.py
D  operations/validation/validators.py
D  pytest.ini
D  requirements.txt
D  tests/__init__.py
D  tests/conftest.py
D  tests/fixtures/data/results/monitor_anomaly_case_review_packets.csv
D  tests/fixtures/data/results/monitor_anomaly_review_decision_readiness.csv
D  tests/fixtures/data/results/monitor_anomaly_review_metadata.json
D  tests/fixtures/data/results/monitor_anomaly_review_queue.csv
D  tests/fixtures/data/results/monitor_anomaly_review_status_transitions.csv
D  tests/fixtures/data/results/monitor_anomaly_review_summary.csv
D  tests/test_advisor_alignment_checklist.py
D  tests/test_advisor_feedback_integration_checklist.py
D  tests/test_advisor_feedback_log.py
D  tests/test_advisor_handoff_note.py
D  tests/test_advisor_handoff_package.py
D  tests/test_advisor_source_review_followup.py
D  tests/test_agent_future_work_handoff.py
D  tests/test_agent_pipeline_control_audit.py
D  tests/test_agent_pipeline_safety_case.py
D  tests/test_agent_review_queue_dashboard.py
D  tests/test_brier_score.py
D  tests/test_brier_scores.py
D  tests/test_chapter_source_bindings.py
D  tests/test_chapter_source_review_checklist.py
D  tests/test_data_inventory.py
D  tests/test_deferred_mcp.py
D  tests/test_dozenten_report.py
D  tests/test_event_catalog.py
D  tests/test_event_study.py
D  tests/test_h1_270towin_poll_average_extension.py
D  tests/test_h1_270towin_state_forecast_extension.py
D  tests/test_h1_calibration_diagnostic.py
D  tests/test_h1_claim_evidence_audit.py
D  tests/test_h1_competitive_state_diagnostic.py
D  tests/test_h1_direct_poll_loss_decomposition.py
D  tests/test_h1_direct_poll_outlier_robustness.py
D  tests/test_h1_direct_poll_state_cluster_diagnostic.py
D  tests/test_h1_evidence_scope.py
D  tests/test_h1_expansion_readiness.py
D  tests/test_h1_final_snapshot_extension.py
D  tests/test_h1_forecast_quality.py
D  tests/test_h1_forecast_quality_synthesis.py
D  tests/test_h1_h2_h3_bounded_chapter_draft.py
D  tests/test_h1_h2_h3_decision_queue_ledger_alignment.py
D  tests/test_h1_h2_h3_decision_queue_overview.py
D  tests/test_h1_h2_h3_drafting_checklist.py
D  tests/test_h1_h2_h3_manual_source_review_execution_pass.py
D  tests/test_h1_h2_h3_source_gated_thesis_drafting_pass.py
D  tests/test_h1_h2_h3_source_gated_writing_pass.py
D  tests/test_h1_h2_h3_source_review_notes.py
D  tests/test_h1_h2_h3_worksheet_drafting_bridge.py
D  tests/test_h1_manual_source_review_followup.py
D  tests/test_h1_margin_threshold_readiness.py
D  tests/test_h1_poll_claim_readiness.py
D  tests/test_h1_poll_comparison_result.py
D  tests/test_h1_poll_comparison_unit_robustness.py
D  tests/test_h1_poll_decision_matrix.py
D  tests/test_h1_poll_scope_frontier.py
D  tests/test_h1_popular_vote_extension.py
D  tests/test_h1_rieke_state_forecast_extension.py
D  tests/test_h1_robust_poll_scope_quality.py
D  tests/test_h1_robust_poll_scope_unit_quality.py
D  tests/test_h1_source_review_batch_worksheet.py
D  tests/test_h1_source_review_decision_queue.py
D  tests/test_h1_source_review_ledger_fill_guide.py
D  tests/test_h1_state_poll_panel_competitiveness_diagnostic.py
D  tests/test_h1_state_poll_panel_extension.py
D  tests/test_h1_state_poll_panel_horizon_diagnostic.py
D  tests/test_h1_state_poll_panel_horizon_state_diagnostic.py
D  tests/test_h1_state_poll_panel_near_window_quality.py
D  tests/test_h1_state_poll_panel_state_significance.py
D  tests/test_h1_state_poll_panel_temporal_diagnostic.py
D  tests/test_h1_state_poll_snapshot_extension.py
D  tests/test_h1_state_source_consensus.py
D  tests/test_h2_event_window_runner.py
D  tests/test_h2_manual_source_review_followup.py
D  tests/test_h2_source_review_batch_worksheet.py
D  tests/test_h2_source_review_decision_queue.py
D  tests/test_h2_source_review_ledger_fill_guide.py
D  tests/test_h2_summary_persistence.py
D  tests/test_h3_event_wallet_anomalies.py
D  tests/test_h3_granger_baseline.py
D  tests/test_h3_lead_time_histograms.py
D  tests/test_h3_manual_source_review_followup.py
D  tests/test_h3_source_review_batch_worksheet.py
D  tests/test_h3_source_review_decision_queue.py
D  tests/test_h3_source_review_ledger_fill_guide.py
D  tests/test_highlevel_next_step_control_summary.py
D  tests/test_highlevel_thesis_writing_handoff.py
D  tests/test_informed_trading_signature.py
D  tests/test_ingest.py
D  tests/test_ledger_citation_gate_summary.py
D  tests/test_manual_source_review_followup_overview.py
D  tests/test_manual_source_review_update_checklist.py
D  tests/test_market_agent.py
D  tests/test_method_interpretation_source_coverage.py
D  tests/test_migrations.py
D  tests/test_monitor_anomaly_review_queue.py
D  tests/test_monitor_candidate_review_report.py
D  tests/test_monitor_dashboard_launcher.py
D  tests/test_monitor_detection_backtest.py
D  tests/test_monitor_literature_risk_scores.py
D  tests/test_monitor_mcp_readonly.py
D  tests/test_monitor_reference_candidate_sensitivity.py
D  tests/test_monitor_reference_candidates.py
D  tests/test_monitor_v2_dashboard.py
D  tests/test_monitor_v2_event_proximity_sensitivity.py
D  tests/test_monitor_v2_historical_replay.py
D  tests/test_monitor_v2_input_validation.py
D  tests/test_monitor_v2_live_input_batch.py
D  tests/test_monitor_v2_live_input_scoring.py
D  tests/test_monitor_v2_live_input_validation.py
D  tests/test_monitor_v2_live_window_registry.py
D  tests/test_monitor_v2_polymarket_live_figures.py
D  tests/test_monitor_v2_recorded_input_adapter.py
D  tests/test_monitor_v2_recorded_input_scoring.py
D  tests/test_monitor_v2_result_summaries.py
D  tests/test_monitor_v2_snapshot.py
D  tests/test_monitor_v2_threshold_sensitivity.py
D  tests/test_monitor_wallet_graph.py
D  tests/test_orchestrator.py
D  tests/test_polymarket_monitor_refresh.py
D  tests/test_polymarket_public_activity.py
D  tests/test_polymarket_readonly_collector.py
D  tests/test_polymarket_rolling_history.py
D  tests/test_polymarket_watchlist.py
D  tests/test_project_automation.py
D  tests/test_schema.py
D  tests/test_sentiment_agent.py
D  tests/test_source_access_audit.py
D  tests/test_source_review_batch_execution_plan.py
D  tests/test_source_review_chapter_handoff.py
D  tests/test_source_review_decision_packets.py
D  tests/test_source_review_execution_guide.py
D  tests/test_source_review_progress_ledger.py
D  tests/test_source_review_progress_protocol.py
D  tests/test_source_review_worksheet_overview.py
D  tests/test_source_structure_inventory.py
D  tests/test_submission_readiness_board.py
D  tests/test_swiss_referendum_auto_refresh.py
D  tests/test_swiss_referendum_efficiency.py
D  tests/test_swiss_referendum_final_case_study.py
D  tests/test_swiss_referendum_history.py
D  tests/test_swiss_referendum_polymarket.py
D  tests/test_swiss_referendum_refresh.py
D  tests/test_thesis_consolidation.py
D  tests/test_thesis_consolidation_index.py
D  tests/test_thesis_core_writing_package.py
D  tests/test_thesis_drafting_sequence.py
D  tests/test_thesis_execution_checklist.py
D  tests/test_thesis_figures.py
D  tests/test_thesis_final_gate_board.py
D  tests/test_thesis_goal_completion_audit.py
D  tests/test_thesis_result_summaries.py
D  tests/test_thesis_source_review_worksheet.py
D  tests/test_thesis_traceability_audit.py
D  tests/test_thesis_wording_guard.py
D  tests/test_tiered_wallet_activity.py
D  tests/test_validation.py
D  tests/test_wallet_distribution_inventory.py
D  tests/test_wallet_reference_cases.py
D  tests/test_wallet_reference_similarity.py
D  tests/test_wallet_tier_classification.py
D  tests/test_whale_agent.py
D  thesis/.gitignore
D  thesis/Bachelorarbeit_FHNW.docx
D  thesis/README.md
D  thesis/chapters/01_einleitung.tex
D  thesis/chapters/02_theorie.tex
D  thesis/chapters/03_methodik.tex
D  thesis/chapters/04_h1.tex
D  thesis/chapters/05_h2.tex
D  thesis/chapters/06_h3.tex
D  thesis/chapters/07_erweiterungen.tex
D  thesis/chapters/08_diskussion.tex
D  thesis/chapters/09_ausblick.tex
D  thesis/chapters/10_einschraenkungen.tex
D  thesis/figures/h1_calibration_diagnostic.png
D  thesis/figures/h1_forecast_quality.png
D  thesis/figures/h1_poll_claim_readiness.png
D  thesis/figures/h3_informed_trading_profile.png
D  thesis/figures/swiss_referendum_10mio_final_case_study.png
D  thesis/figures/thesis_h2_event_window_car.png
D  thesis/figures/thesis_h3_event_wallet_anomalies.png
D  thesis/figures/thesis_h3_granger_pvalues.png
D  thesis/figures/thesis_h3_lead_time_amount.png
D  thesis/figures/thesis_h3_wallet_tier_counts.png
D  thesis/main.tex
D  thesis/references.bib
?? .claude/
?? .gitignore
?? AGENTS.md
?? ARCHITECTURE_DECISIONS.md
?? CLAUDE.md
?? GOAL.md
?? PROJECT_CONTEXT.md
?? PROJEKT_SYNC_2026-06-16.md
?? ROADMAP.md
?? SCHREIBFAHRPLAN.md
?? STATUS.md
?? data/
?? directives/
?? docs/
?? ingest/
?? init_db.py
?? legacy/
?? operations/
?? pytest.ini
?? requirements.txt
?? tests/
?? thesis/
?? thesis_overleaf.zip
```

Git diff stat:

```text
no unstaged diff
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
