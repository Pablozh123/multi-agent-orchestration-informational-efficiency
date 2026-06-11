# Thesis Consolidation

## Purpose

This document is the high-level consolidation layer for the bachelor thesis. It reduces the many generated artifacts to a small thesis-ready package and keeps every central method and interpretation tied to deterministic evidence.

## Core Result Table

| result_id | thesis_area | headline_result | key_value | thesis_readiness |
| --- | --- | --- | --- | --- |
| core_h1_bounded_poll_scope | H1 | Bounded poll-comparison scope supports Polymarket. | 262/285 state-date rows (91.9%) lower Brier loss for Polymarket | thesis_facing_ready |
| core_h1_broad_claim_boundary | H1 | Broad Polymarket-superiority claim remains not proven. | 7/9 aggregate rows support Polymarket; 3/9 majority-case rows support Polymarket; 0/9 broad rows prove the claim; 5 audit rows contradict the strong claim | thesis_facing_ready |
| core_h2_largest_daily_event_window | H2 | The largest primary daily event-window move is the Trump shooting window. | evt_2024_07_13_trump_shooting 7.2 pp | thesis_facing_ready |
| core_h3_top_tier_timing | H3 | The top wallet tier has the clearest current timing diagnostic. | tier_1_top_1pct lag 1 correlation 0.1858; tier_1_top_1pct lag 1 Granger p=0.0012; 1216 aligned rows | thesis_facing_ready |
| core_monitor_review_queue_boundary | monitor_prototype | The monitor review queue is useful as workflow evidence, not empirical proof. | 3 review cases; 1 high; 2 medium; source_check_pending=3 | appendix_prototype_only |
| core_swiss_running_gap_pending | swiss_referendum | Swiss referendum market-poll divergence is descriptive until the result is known. | 26 snapshots; latest SRG/gfs.bern Polymarket Yes 22.0%, poll Yes 45.0%, raw gap -23.0 pp | descriptive_pending_result |

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

1. Evidence-reader agent over `thesis_evidence_map.csv` and curated summaries only.
2. Citation-check assistant that flags missing source status without writing thesis claims.
3. Interpretation-consistency assistant that compares draft prose against allowed and blocked wording.
4. Human-review assistant for monitor packets after manual source checks exist.
5. Only after audit logging exists: bounded MCP summary tools for read-only reviewed artifacts.

No runtime agent, MCP implementation, model routing, autonomous collector, or trading path is part of the current consolidation step.

## Generated Artifact Counts

- Evidence rows: 13
- Core result rows: 6
- Core tables: 5
- Core figures: 4
