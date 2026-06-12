# LITERATURE_MAP.md

## Purpose

This file maps external research sources to the thesis design. It exists so
Perplexity discoveries, local PDFs, Zotero notes, and later web research do not
become hidden project memory.

Perplexity may be used for discovery only. Thesis claims must be checked
against indexed papers, primary sources, or reproducible project outputs before
they are used in the thesis text.

## Local Intake Workflow

Use `data/literature/literature_index.csv` as the tracked source index.

Expected columns:

- `source_id`
- `title`
- `authors`
- `year`
- `venue`
- `url`
- `local_file`
- `topic`
- `hypothesis`
- `method`
- `relevance`
- `status`
- `notes`

Put downloaded PDFs, Perplexity exports, and other large local files in:

- `data/literature/raw/`

That folder is intentionally ignored by Git. The tracked index stores only file
names, metadata, and review notes.

The current Zotero source folder is:

- `C:\Users\chole\Zotero\Polymarket`

Files may stay in Zotero instead of being copied into the repository. In that
case, `data/literature/literature_index.csv` stores the local Zotero path and
the same review-status rules apply.

## RAG-Ready Use Policy

The literature index is the retrieval boundary for future RAG-style work. A
future literature assistant may retrieve from indexed sources, but it must obey
these limits:

- Only sources listed in `data/literature/literature_index.csv` are in scope.
- `candidate` sources may be used for discovery and question formation only.
- Thesis-facing claims require `reviewed` or `cited` status.
- Web articles and Perplexity exports are context sources, not academic proof.
- Retrieved snippets must be traced back to `source_id` and `local_file` or
  `url`.
- No vector database, embedding pipeline, agent orchestration, or MCP tool is
  active yet.

This gives the project a local RAG-ready source map without activating the
deferred agent and MCP layers.

## Current Thesis Consolidation Map

Current generated consolidation artifacts:

- `data/results/thesis_evidence_map.csv`
- `data/results/thesis_evidence_map.md`
- `data/results/thesis_core_results_table.csv`
- `data/results/thesis_curated_result_package.csv`
- `data/results/thesis_table_figure_captions.csv`
- `data/results/thesis_citation_readiness.csv`
- `data/results/thesis_source_review_plan.csv`
- `data/results/thesis_citation_review_packets.csv`
- `data/results/thesis_chapter_plan.csv`
- `data/results/thesis_agent_pipeline_roadmap.csv`
- `data/results/thesis_agent_assistance_protocol.csv`
- `docs/research/THESIS_CONSOLIDATION.md`
- `docs/research/THESIS_TABLE_FIGURE_CAPTIONS.md`
- `docs/research/THESIS_SOURCE_REVIEW_PLAN.md`
- `docs/research/THESIS_AGENT_PIPELINE_ROADMAP.md`
- `docs/research/THESIS_AGENT_ASSISTANCE_PROTOCOL.md`
- `docs/research/THESIS_CITATION_REVIEW_PACKETS.md`

These artifacts are the current thesis-draft bridge from deterministic outputs
to written argumentation. They do not replace final citation review. A row can
be draft-ready for thesis structure because it maps to deterministic artifacts
and non-rejected literature sources, while still requiring source-by-source
review before final submission citations are marked `reviewed` or `cited`.

Current mapping rule:

- Methods and interpretations must list at least one deterministic artifact.
- Methods and interpretations must list source IDs where literature framing is
  needed.
- `candidate` and `rejected` sources must not support thesis-facing H1-H2-H3
  method or interpretation rows.
- `skimmed` sources may support draft structure and source planning, but final
  thesis citation wording still requires review before submission.
- `thesis_citation_readiness.csv` is the current source-review queue. It does
  not promote sources automatically; it records whether a source is unused,
  draft-only, blocked from thesis-facing claims, or ready only after full
  review.
- `thesis_citation_review_packets.csv` is the row-level review worklist. It
  links one source to one Evidence ID and requires a human page or section note
  before any final thesis citation status is upgraded.
- `thesis_source_review_plan.csv` groups those packets by source and provides
  a manual review order. It does not approve citations automatically; it only
  states which sources need method-foundation review, which are unused, and
  which remain blocked or future-work-only.
- `thesis_table_figure_captions.csv` is the current table and figure registry.
  It keeps caption text, source notes, interpretation notes, and limitations
  linked to the curated result package.
- Monitor and Swiss rows must keep their status labels visible:
  prototype/appendix for monitor outputs and descriptive-pending-result for the
  Swiss referendum track.
- Agent-related rows remain future-work architecture only.
- `thesis_agent_assistance_protocol.csv` documents possible future helper
  roles over bounded artifacts. It does not activate runtime agents, MCP
  tools, model routing, or unlogged LLM interpretation.

## Initial Literature Synthesis

Review date: 2026-05-19

Review level: skimmed source pages and local HTML where available. Full-paper
claims remain blocked until each source is read and moved to `reviewed` or
`cited`.

High-relevance academic sources:

- `zotero_poly_001`: The Polymarket transaction-level paper is central for H3
  and useful for H2. Its main methodological value is that on-chain activity is
  not automatically equal to exchange-equivalent trading volume; minting,
  burning, conversion, and exchange activity need to be distinguished before
  strong wallet or volume claims are made. This supports the current caution
  around BUY-only wallet data and argues for careful source-filter metadata.
- `zotero_poly_002`: The betting-markets-versus-polling paper supports the H1
  comparison frame between market probabilities and traditional polling or
  forecast sources. It does not remove the project rule that RCP needs a
  documented probability transformation before Brier or calibration use.
- `zotero_poly_006`: The Kalshi microstructure paper is most useful for the
  later strategy prototype and risk discussion. Its maker/taker and
  favourite-longshot framing supports adding microstructure caveats before any
  backtested strategy claim.

Context and discovery sources:

- `zotero_poly_003`: Useful as a non-academic industry framing source for why
  prediction markets are often compared with polls. It should not be used as
  evidence for H1.
- `zotero_poly_008`: Useful mainly as a warning example. The article contains
  strong claims about whales, insider information, and profits, so it reinforces
  the repository rule that H3 language must stay with predictive timing
  diagnostics rather than misconduct or profitability claims.
- `zotero_poly_009`: Useful for contextual framing of Polymarket as an
  information-discovery product and for product/market background. It is not a
  substitute for peer-reviewed or primary-source evidence.
- `zotero_poly_010`: Local Polybench PDF candidate discovered in the Zotero
  Polymarket folder. It appears relevant to LLM/news-context forecasting and
  market baselines, but its metadata and claims have not yet been extracted.
  Until reviewed, it can only shape questions about whether LLM/news systems
  add value beyond market prices; it cannot support thesis claims.

Rejected or blocked local PDFs:

- `zotero_poly_004` is rejected for thesis use in its current form. The local
  `EMH.pdf` metadata/text could not be reliably read, so it must not be cited.
  It is replaced for citation planning by `lit_emh_001`.

Canonical theory source:

- `lit_emh_001`: Fama's 1970 review is the canonical EMH source for defining
  informational market efficiency. In this thesis it should be used to motivate
  the research question and proxy-test logic, not to assume that Polymarket is
  efficient. The empirical evidence remains the deterministic H1-H2-H3 output
  package.

Core method sources added for the consolidation layer:

- `lit_brier_001`: Method reference for probability forecast verification and
  Brier Score interpretation in H1.
- `lit_dm_001`: Method reference for predictive-accuracy comparison of
  precomputed loss series in H1.
- `lit_eventstudy_001`: Method reference for H2 event-window design and the
  discipline of pre-specified event samples.
- `lit_granger_001`: Method reference for H3 lead-lag diagnostics. It must be
  used with the project rule that Granger output is not causal proof.

Remaining PDF review:

- `zotero_poly_005`: Robin Hanson's insider-trading and prediction-market paper
  is relevant as conceptual/legal background for H3. It reinforces the need to
  distinguish information aggregation from legal or misconduct claims. It does
  not justify calling observed wallet timing `insider trading`.
- `zotero_poly_007`: The Charles University diploma thesis on Polymarket
  convergence, volatility, and biases is useful for positioning this project
  against prior Polymarket research. It supports keeping volatility,
  behavioural-bias, and risk-management caveats visible in H1/H2/strategy
  wording. It does not replace this project's deterministic outputs.

Methodological implications:

- H1 remains a forecast-quality comparison. Literature can motivate the
  Polymarket-versus-polls question, but deterministic Brier and Diebold-Mariano
  outputs remain the evidence.
- H2 remains event-window analysis over curated events. Literature may explain
  why events matter, but it must not be used to add or remove events after
  seeing the Polymarket reaction.
- H3 remains a dataset-relative timing analysis. Literature on whale episodes
  and transaction accounting supports caution, not stronger causal wording.
- Strategy work remains a historical backtest prototype with explicit risk and
  microstructure assumptions.
- The current strategy-track pivot should be framed as an anomaly-monitor
  research prototype: literature may motivate monitoring and RAG questions, but
  Python must still define, score, and validate every anomaly.

## Topic Categories

Use one primary topic per source:

- `prediction_market_efficiency`
- `polymarket_kalshi_decentralized_markets`
- `event_studies`
- `market_microstructure`
- `wallet_onchain_signal_detection`
- `llm_agent_research_workflows`
- `backtesting_risk_management`

## Thesis Mapping

Map each source to at least one research role:

- `H1`: forecast accuracy, calibration, Brier Score, benchmark comparisons.
- `H2`: event studies, information integration, public-news reactions.
- `H3`: wallet timing, on-chain signals, lead-lag structure, Granger methods.
- `strategy_prototype`: backtesting, risk management, signal evaluation.
- `architecture`: LLM/agent orchestration, MCP, auditability, reproducibility.
- `anomaly_monitor`: market, wallet-tier, event, and concentration anomaly
  detection for politics/geopolitical prediction markets.

## Review Status Values

Use these `status` values in the CSV:

- `candidate`: discovered but not checked.
- `skimmed`: read quickly, relevance likely.
- `reviewed`: claims checked against the paper.
- `cited`: ready for thesis citation.
- `rejected`: not useful or methodologically weak.

## Claim Rules

- Do not cite Perplexity as evidence.
- Do not use a paper claim unless the indexed source was read or checked.
- Do not import literature claims into statistical results.
- Do not use literature to justify changing event selections after seeing
  Polymarket reactions.
- Keep strategy claims separate from H1-H3 evidence unless a deterministic
  backtest result supports them.

## Initial Open Tasks

- Extract metadata and first-pass notes from `zotero_poly_010` before using it
  beyond question formation.
- Convert the literature synthesis into the thesis methodology outline.
- Extract full-paper notes for high-relevance academic sources before marking
  them `reviewed` or `cited`.
- Keep every thesis-facing literature claim traceable to `source_id`.
