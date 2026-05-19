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

- Review the imported Zotero Polymarket sources one by one.
- Extract thesis-relevant notes with `source_id` references.
- Mark every imported Perplexity item as `candidate` until the underlying paper
  has been checked.
- Link each reviewed paper to H1, H2, H3, strategy prototype, or architecture.
