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

- Add the downloaded Polymarket, Kalshi, prediction-market, and backtesting
  papers to `data/literature/raw/`.
- Fill `data/literature/literature_index.csv` with one row per source.
- Mark every imported Perplexity item as `candidate` until the underlying paper
  has been checked.
- Link each reviewed paper to H1, H2, H3, strategy prototype, or architecture.
