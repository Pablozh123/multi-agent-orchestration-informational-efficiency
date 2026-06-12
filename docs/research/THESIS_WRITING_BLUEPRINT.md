# Thesis Writing Blueprint

This blueprint translates the deterministic consolidation package into a chapter-by-chapter writing plan. It is a drafting guide, not a new empirical analysis.

## Source And Citation Work

- Sources needing full review before final citation: 11

- Candidate sources blocked from thesis-facing claims: 1

- Indexed sources not currently needed: 3

Use `data/results/thesis_citation_readiness.csv` as the source-review queue. Do not promote source status automatically.

## Core Writing Rule

Every paragraph that states a result should name one deterministic artifact or one evidence_id. Every paragraph that states a method should name the method source or explain why the artifact is sufficient.

## Einleitung und Forschungsfrage

Chapter role: Motivate decentralized prediction markets, Polymarket, and the efficiency question.

Writing status: `outline_ready`

Core evidence ids: `method_h1_brier_dm; method_h2_event_window; method_h3_wallet_tiers`

Recommended package items:

- `Method, source, and evidence map` from `data/results/thesis_evidence_map.csv` (main_text).

Limitation to state: Informational efficiency is operationalised through proxy tests, not observed directly.

Next writing action: Write concise problem statement and delimit Polymarket/US-election focus.

## Theorie und Literatur

Chapter role: Explain EMH, prediction-market forecast quality, event studies, and wallet/on-chain caution.

Writing status: `source_review_needed`

Core evidence ids: `method_h1_brier_dm; method_h2_event_window; method_h3_granger_timing`

Recommended package items:

- `Method, source, and evidence map` from `data/results/thesis_evidence_map.csv` (main_text).

Limitation to state: Draft mapping is ready, but final citation wording still needs source-by-source review.

Next writing action: Promote key method and Polymarket sources from skimmed to reviewed or cited after full-paper checks.

## Daten und Methodik

Chapter role: Document deterministic Python pipeline, artifact hierarchy, and method choices.

Writing status: `draft_ready`

Core evidence ids: `method_h1_brier_dm; method_h2_event_window; method_h3_wallet_tiers; method_h3_granger_timing`

Recommended package items:

- `Method, source, and evidence map` from `data/results/thesis_evidence_map.csv` (main_text).

Limitation to state: RCP remains excluded from probability metrics until transformation is documented.

Next writing action: Turn evidence-map rows into short method paragraphs with artifact citations.

## H1: Prognosequalitaet

Chapter role: Present bounded Brier and poll-comparison evidence.

Writing status: `result_ready_with_limits`

Core evidence ids: `interpretation_h1_bounded_advantage; interpretation_h1_broad_claim_not_proven`

Recommended package items:

- `H1 forecast-quality and poll-comparison result` from `data/results/thesis_core_results_table.csv` (main_text).

- `H1 poll-claim readiness` from `data/results/h1_poll_claim_readiness.png` (main_text).

Result statements to use:

- Bounded poll-comparison scope supports Polymarket. Key value: 262/285 state-date rows (91.9%) lower Brier loss for Polymarket Source: `data/results/h1_poll_claim_readiness_summary.csv`.

- Broad Polymarket-superiority claim remains not proven. Key value: 7/9 aggregate rows support Polymarket; 3/9 majority-case rows support Polymarket; 0/9 broad rows prove the claim; 5 audit rows contradict the strong claim Source: `data/results/h1_forecast_quality_synthesis.csv`.

Limitation to state: The broad Polymarket-superiority claim remains not proven.

Next writing action: Write H1 result as bounded support plus explicit counterexample paragraph.

## H2: Ereignisfenster

Chapter role: Present daily public-event response diagnostics.

Writing status: `result_ready_with_limits`

Core evidence ids: `interpretation_h2_daily_response`

Recommended package items:

- `H2 daily event-window result` from `data/results/h2_event_window_summary.csv` (main_text).

- `H2 daily event-window movements` from `data/results/thesis_h2_event_window_car.png` (main_text).

Result statements to use:

- The largest primary daily event-window move is the Trump shooting window. Key value: evt_2024_07_13_trump_shooting 7.2 pp Source: `data/results/h2_event_window_summary.csv`.

Limitation to state: Daily event-window results do not identify intraday reaction speed.

Next writing action: Write event-by-event result table narrative and daily-resolution limitation.

## H3: Wallet-Timing

Chapter role: Present distribution-derived tiers and predictive timing diagnostics.

Writing status: `result_ready_with_limits`

Core evidence ids: `method_h3_wallet_tiers; interpretation_h3_top_tier_signal`

Recommended package items:

- `H3 wallet-tier timing diagnostics` from `data/results/thesis_h3_summary.csv` (main_text).

- `H3 Granger diagnostic p-values` from `data/results/thesis_h3_granger_pvalues.png` (main_text).

Result statements to use:

- The top wallet tier has the clearest current timing diagnostic. Key value: tier_1_top_1pct lag 1 correlation 0.1858; tier_1_top_1pct lag 1 Granger p=0.0012; 1216 aligned rows Source: `data/results/thesis_h3_summary.csv`.

Limitation to state: BUY-only source data, daily alignment, and multiple testing limit claim strength.

Next writing action: Write H3 as timing diagnostics, not causality or private-information evidence.

## Erweiterungen: Monitor und Schweizer Abstimmung

Chapter role: Place monitor prototype and Swiss side track outside the core proof.

Writing status: `appendix_or_discussion_ready`

Core evidence ids: `interpretation_monitor_review_queue; interpretation_swiss_gap_pending`

Recommended package items:

- `Prototype and Swiss side-track boundary table` from `data/results/thesis_core_results_table.csv` (appendix_or_discussion).

- `Swiss referendum running poll-proxy comparison` from `data/results/swiss_referendum_10mio_efficiency.png` (discussion_pending_final_result).

Result statements to use:

- The monitor review queue is useful as workflow evidence, not empirical proof. Key value: 3 review cases; 1 high; 2 medium; source_check_pending=3 Source: `data/results/monitor_anomaly_review_summary.csv`.

- Swiss referendum market-poll divergence is descriptive until the result is known. Key value: 32 snapshots; latest SRG/gfs.bern Polymarket Yes 21.5%, poll Yes 45.0%, raw gap -23.5 pp Source: `data/results/swiss_referendum_10mio_latest_source_comparison.csv`.

Limitation to state: Monitor cases need human review; Swiss interpretation needs official result.

Next writing action: Keep both as bounded discussion or appendix until final gates change.

## Diskussion, Limitationen und Fazit

Chapter role: Integrate H1-H3 evidence and state what remains unproven.

Writing status: `outline_ready`

Core evidence ids: `interpretation_h1_broad_claim_not_proven; interpretation_h2_daily_response; interpretation_h3_top_tier_signal; future_agent_pipeline_guarded`

Result statements to use:

- Bounded poll-comparison scope supports Polymarket. Key value: 262/285 state-date rows (91.9%) lower Brier loss for Polymarket Source: `data/results/h1_poll_claim_readiness_summary.csv`.

- Broad Polymarket-superiority claim remains not proven. Key value: 7/9 aggregate rows support Polymarket; 3/9 majority-case rows support Polymarket; 0/9 broad rows prove the claim; 5 audit rows contradict the strong claim Source: `data/results/h1_forecast_quality_synthesis.csv`.

- The largest primary daily event-window move is the Trump shooting window. Key value: evt_2024_07_13_trump_shooting 7.2 pp Source: `data/results/h2_event_window_summary.csv`.

- The top wallet tier has the clearest current timing diagnostic. Key value: tier_1_top_1pct lag 1 correlation 0.1858; tier_1_top_1pct lag 1 Granger p=0.0012; 1216 aligned rows Source: `data/results/thesis_h3_summary.csv`.

Limitation to state: The thesis supports bounded diagnostics, not universal market efficiency or strategy claims.

Next writing action: Write final answer around bounded evidence, limitations, and future agent-assisted workflow.

## Agent-Assisted Pipeline Outlook

Use this only as future work. Later agents may help read the evidence map, check citation readiness, and compare draft paragraphs with allowed or blocked wording. They must not calculate metrics, read raw tables by default, expose wallet-address rows, or create order/trading paths. Future LLM calls require `llm_audit_log` first.
