# GOAL.md

## Active Goal

goal_id: goal-overleaf-results-prose-001
title: Prepare Overleaf-ready results chapter draft
status: active
phase: Phase 9: Thesis Export
why:
- H1-H3 thesis-facing result summaries and figures now exist.
- The results narrative skeleton now states what was investigated, how the
  results were derived, what can be interpreted, and what remains open.
- The deterministic strategy prototype is now specified as a future historical
  backtest contract, not as an agent or live-trading system.
- The next step is to turn the accepted narrative skeleton into thesis-facing
  prose blocks that can later move to Overleaf.
deliverables:
- Draft thesis-facing results prose for H1, H2, and H3.
- Include short bridge text for the strategy prototype as future research.
- Tie prose to tables, figures, deterministic artifacts, and limitations.
- Keep wording suitable for Swiss German thesis style when German prose is
  added.
scope:
- Documentation-only thesis drafting.
- Existing deterministic result summaries, figures, and literature sources
  only.
- Result interpretation and limitation wording only.
out_of_scope:
- New statistical code, new event selection, or backtest implementation.
- Agents, MCP, model routing, ML, cloud deployment, and live trading.
- Treating Perplexity summaries as cited evidence.
acceptance_criteria:
- Exactly one active goal remains in this file.
- Draft prose separates evidence, interpretation, limitations, and further
  investigations.
- No causal, insider-trading, intraday, RCP-probability, live-trading, or profit
  guarantee claims are introduced.
- Every result statement points to a deterministic artifact or documented
  limitation.
- STATUS.md and WORK_LOG.md are updated before stopping work.
- Review checks pass before recommending a commit.
next_commit: docs: prepare overleaf results chapter draft

## Decision Inputs For This Goal

- Thesis-facing H1-H3 summaries and figures exist in `data/results/`.
- Thesis results narrative skeleton exists in `docs/research/RESEARCH_SPEC.md`.
- Deterministic strategy prototype specification exists in
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`.
- H1-H3 empirical baseline review exists in `docs/research/RESEARCH_SPEC.md`.
- Strategy prototype boundaries are recorded in `ARCHITECTURE_DECISIONS.md`,
  `ROADMAP.md`, and `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`.
- Literature intake structure exists in `docs/research/LITERATURE_MAP.md` and
  `data/literature/literature_index.csv`.
- ML scope and re-entry conditions are explicit in
  `docs/research/RESEARCH_SPEC.md`.
- Codex workflow roles are separate from deferred thesis runtime agents.

## Done Means

- H1, H2, and H3 prose blocks are ready for Overleaf drafting.
- Each block cites the intended table, figure, and source artifact.
- Limitations and further investigations are explicit in the draft.
- Project review checks still detect premature ML, agent, MCP, live-trading,
  or profit-guarantee work.

## Blocked Follow-Up Goals

- Runtime agents and MCP remain blocked until bounded summary contracts,
  `llm_audit_log` usage, and deterministic backtest outputs exist.
- ML remains blocked until deterministic H1-H3 outputs and any strategy
  prototype baseline have written methodology and review notes.

## Completed Goals

- Project synchronization documentation exists.
- Prompt and legacy instruction cleanup exists.
- Deterministic schema migrations, validation, data inventory, Brier baseline,
  RCP guardrails, agent/MCP deferral guards, event catalog tooling, and
  project-control automation exist.
- Deterministic H2 event-window CSV outputs exist and their shape is accepted.
- Compact H2 summaries are persisted idempotently into `analysis_summaries`,
  while full row-level H2 traces remain file-based.
- H3 wallet-tier method is selected as wallet-level cumulative observed
  `amount_usd` percentiles.
- H3 wallet distribution inventory exists with source-filter metadata,
  percentile thresholds, and tier counts.
- H3 wallet tier classification exists for observed wallets with compact
  metadata and deterministic tier counts.
- H3 tiered wallet activity series exists as a complete daily tier panel.
- H3 descriptive lead-time histograms exist and are reviewed as a daily
  descriptive timing baseline.
- H3 deterministic daily lead-lag correlations and Granger outputs exist with
  tests and compact metadata.
- H3 Granger interpretation limits, persistence decision, and sensitivity needs
  are documented.
- H1-H3 deterministic baseline package is reviewed for thesis readiness.
- Thesis-facing H1-H3 summary tables exist and are traceable to deterministic
  source artifacts.
- Literature intake structure and strategy-agent architecture are documented.
- Zotero Polymarket sources are indexed as candidate literature for RAG-ready
  review.
- Initial literature synthesis exists for skimmed source pages and local HTML
  files.
- Remaining local PDFs are reviewed: `zotero_poly_005` and `zotero_poly_007`
  are skimmed; `zotero_poly_004` is rejected until replaced by a verifiable EMH
  source.
- Literature-backed thesis methodology outline exists.
- Canonical EMH source is indexed; rejected local `EMH.pdf` remains non-citable.
- Thesis tables and figures plan exists.
- Thesis-ready H2 and H3 figure artifacts are generated from existing result
  files.
- Thesis results narrative skeleton exists and separates evidence,
  interpretation, limitations, and further investigations.
- Deterministic strategy prototype specification exists with candidate signal
  families, interface fields, risk assumptions, and rejection criteria.
- Strategy/agent guardrails are enforced by project review checks.
