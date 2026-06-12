# Thesis Consolidation

## Purpose

This document is the high-level consolidation layer for the bachelor thesis. It reduces the many generated artifacts to a small thesis-ready package and keeps every central method and interpretation tied to deterministic evidence.

## Project Highlevel View

`data/results/thesis_project_highlevel_view.csv` summarises the current project layers, decisions, next gates, and thesis-use boundaries. It keeps review access paused and does not add new empirical metrics.

| view_id | project_layer | status | current_decision | next_gate | thesis_use |
| --- | --- | --- | --- | --- | --- |
| project_00_current_frame | Current high-level frame | active_thesis_core | Use 6 core result rows, 5 core tables, and 4 core figures as the main thesis package. | Complete source review and turn the chapter plan into thesis prose. | main_text_project_overview |
| project_01_h1_forecast_quality | H1 forecast quality | thesis_facing_ready | Write H1 as bounded support in compatible poll-comparison scopes, not as universal Polymarket superiority. | Final citation wording after source review confirms method and interpretation support. | main_text_results |
| project_02_h2_event_windows | H2 event-window response | thesis_facing_ready | Use H2 as daily event-window evidence, not as an intraday reaction-speed claim. | Draft result text with event curation and daily-resolution limitation explicit. | main_text_results |
| project_03_h3_wallet_timing | H3 wallet timing diagnostics | thesis_facing_ready_with_limits | Use top-tier timing diagnostics as predictive pattern evidence, not causal or misconduct evidence. | Draft H3 with BUY-only, daily aggregation, and multiple-testing limitations visible. | main_text_results_with_limits |
| project_04_source_review_gate | Sources and citations | active_gate | Treat 11 sources as requiring full review, including 11 priority-1 method-foundation rows. | Record page or section notes and human decisions before final thesis citation. | theory_methods_citation_gate |
| project_05_table_figure_package | Compact tables and figures | thesis_facing_package | Use 5 core tables and 4 core figures, with generated captions and limitation notes. | Integrate the selected package into draft chapters and appendix placement. | main_text_and_appendix |
| project_06_monitor_review_access | Monitor prototype and review access | paused_appendix_only | Review access remains paused; no further runtime MCP or agent layer is part of the current thesis consolidation. | Human source review of monitor cases or a separate approved goal before any renewed access work. | appendix_or_discussion_only |
| project_07_swiss_referendum | Swiss referendum side track | descriptive_pending_result | Keep the Swiss material descriptive until the official 14 June 2026 vote result is available. | Regenerate Swiss artifacts after official result mapping. | discussion_pending_final_result |
| project_08_future_agents | Future agent-assisted pipeline | documentation_only_deferred | Keep 6 roadmap stages and 6 documentation-only assistance rows inactive. | Separate approved goal with bounded prompts, tests, and llm_audit_log integration. | future_work_only |
| project_09_advisor_iteration | Advisor communication | project_management_ready | Use the Dozentenbericht to align on bounded H1 wording, source-review depth, Swiss placement, and appendix scope. | Advisor feedback is received and logged into the next small commit plan. | advisor_update |

## Core Result Table

| result_id | thesis_area | headline_result | key_value | thesis_readiness |
| --- | --- | --- | --- | --- |
| core_h1_bounded_poll_scope | H1 | Bounded poll-comparison scope supports Polymarket. | 262/285 state-date rows (91.9%) lower Brier loss for Polymarket | thesis_facing_ready |
| core_h1_broad_claim_boundary | H1 | Broad Polymarket-superiority claim remains not proven. | 7/9 aggregate rows support Polymarket; 3/9 majority-case rows support Polymarket; 0/9 broad rows prove the claim; 5 audit rows contradict the strong claim | thesis_facing_ready |
| core_h2_largest_daily_event_window | H2 | The largest primary daily event-window move is the Trump shooting window. | evt_2024_07_13_trump_shooting 7.2 pp | thesis_facing_ready |
| core_h3_top_tier_timing | H3 | The top wallet tier has the clearest current timing diagnostic. | tier_1_top_1pct lag 1 correlation 0.1858; tier_1_top_1pct lag 1 Granger p=0.0012; 1216 aligned rows | thesis_facing_ready |
| core_monitor_review_queue_boundary | monitor_prototype | The monitor review queue is useful as workflow evidence, not empirical proof. | 3 review cases; 1 high; 2 medium; source_check_pending=3 | appendix_prototype_only |
| core_swiss_running_gap_pending | swiss_referendum | Swiss referendum market-poll divergence is descriptive until the result is known. | 28 snapshots; latest SRG/gfs.bern Polymarket Yes 22.0%, poll Yes 45.0%, raw gap -23.0 pp | descriptive_pending_result |

## Recommended Tables

| package_id | title | primary_artifact | recommended_placement | thesis_readiness |
| --- | --- | --- | --- | --- |
| T1 | Method, source, and evidence map | data/results/thesis_evidence_map.csv | main_text | thesis_facing_ready |
| T2 | H1 forecast-quality and poll-comparison result | data/results/thesis_core_results_table.csv | main_text | thesis_facing_ready |
| T3 | H2 daily event-window result | data/results/h2_event_window_summary.csv | main_text | thesis_facing_ready |
| T4 | H3 wallet-tier timing diagnostics | data/results/thesis_h3_summary.csv | main_text | thesis_facing_ready |
| T5 | Prototype and Swiss side-track boundary table | data/results/thesis_core_results_table.csv | appendix_or_discussion | mixed_appendix_and_pending |

## Recommended Figures

| package_id | title | primary_artifact | recommended_placement | thesis_readiness |
| --- | --- | --- | --- | --- |
| F1 | H1 poll-claim readiness | data/results/h1_poll_claim_readiness.png | main_text | thesis_facing_ready |
| F2 | H2 daily event-window movements | data/results/thesis_h2_event_window_car.png | main_text | thesis_facing_ready |
| F3 | H3 Granger diagnostic p-values | data/results/thesis_h3_granger_pvalues.png | main_text | thesis_facing_ready |
| F4 | Swiss referendum running poll-proxy comparison | data/results/swiss_referendum_10mio_efficiency.png | discussion_pending_final_result | descriptive_pending_result |

## Citation Readiness

This table is a source-control view, not a promotion of source status. Sources marked `skimmed` can guide draft structure, but final thesis citation wording still needs source-by-source review.

| source_id | status | used_by_thesis_areas | final_citation_readiness | citation_risk |
| --- | --- | --- | --- | --- |
| lit_brier_001 | skimmed | H1; swiss_referendum | needs_full_source_review_before_final_citation | medium |
| lit_dm_001 | skimmed | H1 | needs_full_source_review_before_final_citation | medium |
| lit_emh_001 | skimmed | H1; H2 | needs_full_source_review_before_final_citation | medium |
| lit_eventstudy_001 | skimmed | H2 | needs_full_source_review_before_final_citation | medium |
| lit_granger_001 | skimmed | H3 | needs_full_source_review_before_final_citation | medium |
| zotero_poly_001 | skimmed | H2; H3; monitor_prototype | needs_full_source_review_before_final_citation | medium |
| zotero_poly_002 | skimmed | H1; swiss_referendum | needs_full_source_review_before_final_citation | medium |
| zotero_poly_005 | skimmed | H3 | needs_full_source_review_before_final_citation | medium |
| zotero_poly_006 | skimmed | future_agents; monitor_prototype | needs_full_source_review_before_final_citation | medium |
| zotero_poly_007 | skimmed | H3 | needs_full_source_review_before_final_citation | medium |
| zotero_poly_009 | skimmed | monitor_prototype | needs_full_source_review_before_final_citation | medium |
| zotero_poly_010 | candidate | future_agents | not_allowed_for_thesis_facing_claims | high |

## Citation Review Packets

`data/results/thesis_citation_review_packets.csv` breaks the source review into source-evidence packets. Each row links one source to one Evidence ID, the deterministic artifact, allowed wording, blocked wording, review question, and final citation gate. The packet file is a worklist, not a source-status promotion.

## Source Review Plan

`data/results/thesis_source_review_plan.csv` groups the citation packets by source and assigns manual review bands. It has 15 source rows and remains a human review queue, not an automatic source-status promotion.

## Agent Assistance Protocol

`data/results/thesis_agent_assistance_protocol.csv` documents how future agents could help with source review, wording checks, advisor updates, and bounded summaries. It is documentation-only and does not activate runtime agents, MCP tools, model routing, or unlogged LLM interpretation.

## Next Work Plan

`data/results/thesis_next_work_plan.csv` orders the remaining workstreams from source review through final thesis QA. It is a planning artifact and does not change empirical results.

## Chapter Plan

| chapter_id | chapter_title | writing_status | recommended_tables | recommended_figures | next_action |
| --- | --- | --- | --- | --- | --- |
| ch_01_intro | Einleitung und Forschungsfrage | outline_ready | T1 |  | Write concise problem statement and delimit Polymarket/US-election focus. |
| ch_02_theory_literature | Theorie und Literatur | source_review_needed | T1 |  | Promote key method and Polymarket sources from skimmed to reviewed or cited after full-paper checks. |
| ch_03_data_method | Daten und Methodik | draft_ready | T1 |  | Turn evidence-map rows into short method paragraphs with artifact citations. |
| ch_04_h1_results | H1: Prognosequalitaet | result_ready_with_limits | T2 | F1 | Write H1 result as bounded support plus explicit counterexample paragraph. |
| ch_05_h2_results | H2: Ereignisfenster | result_ready_with_limits | T3 | F2 | Write event-by-event result table narrative and daily-resolution limitation. |
| ch_06_h3_results | H3: Wallet-Timing | result_ready_with_limits | T4 | F3 | Write H3 as timing diagnostics, not causality or private-information evidence. |
| ch_07_extensions | Erweiterungen: Monitor und Schweizer Abstimmung | appendix_or_discussion_ready | T5 | F4 | Keep both as bounded discussion or appendix until final gates change. |
| ch_08_discussion_conclusion | Diskussion, Limitationen und Fazit | outline_ready |  |  | Write final answer around bounded evidence, limitations, and future agent-assisted workflow. |

## Interpretation Discipline

- Deterministic artifacts come first.
- Literature supports method framing and interpretation limits.
- H1 can be written as bounded support, not broad superiority.
- H2 can be written as daily event-window response, not intraday speed.
- H3 can be written as predictive timing diagnostics, not causality or private-information evidence.
- Monitor outputs stay prototype or appendix material until human review gates approve them.
- Swiss referendum outputs stay descriptive until the official result is available.

## Deferred Agent Pipeline Idea

Primary evidence: `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`.

Later agents can improve the workflow only after the thesis-ready deterministic package is stable. The useful agent roles are documentation assistants, source-check triage helpers, reviewer-note summarizers, and consistency checkers over bounded summaries. They must not calculate Brier, CAR, Granger, wallet tiers, whale scores, PnL, or risk metrics. They must not receive raw table dumps or wallet-address rows. Every future LLM call must be logged in `llm_audit_log`, and future tool outputs must stay bounded to at most 50 rows unless a reviewed exception is documented.

Recommended staged architecture:

| stage_id | stage_name | implementation_status | required_gate_before_activation |
| --- | --- | --- | --- |
| agent_stage_00_disabled_runtime | Keep runtime disabled | current_required_state | Deterministic thesis package committed and reviewed. |
| agent_stage_01_evidence_reader | Evidence reader | future_documentation_only | Bounded prompt template and llm_audit_log write path reviewed. |
| agent_stage_02_citation_checker | Citation readiness checker | future_documentation_only | Human-readable source-status rules and no-write default reviewed. |
| agent_stage_03_wording_guard | Interpretation wording guard | future_documentation_only | Draft text input must be manually selected and logged. |
| agent_stage_04_monitor_review_helper | Monitor review helper | future_documentation_only | Human review worksheet contains reviewed statuses and source URLs. |
| agent_stage_05_bounded_mcp_summaries | Bounded MCP summary tools | future_deferred | Separate approved goal, tests, access contract, and llm_audit_log integration. |

No runtime agent, MCP implementation, model routing, autonomous collector, or trading path is part of the current consolidation step.

## Generated Artifact Counts

- Evidence rows: 13
- Core result rows: 6
- Citation-readiness rows: 15
- Chapter rows: 8
- Agent-stage rows: 6
- Core tables: 5
- Core figures: 4
