# PROJECT_CONTEXT.md

## Thesis Context

This repository supports a bachelor thesis on the informational efficiency of
decentralized prediction markets. The empirical focus is the 2024 US
presidential election, especially the divergence between Polymarket prices and
traditional forecast or polling sources during the Trump/Harris race.

The central research question is whether a decentralized prediction market
integrates information faster or more accurately than traditional forecast
sources, and whether large wallet activity can be treated as an early warning
signal without making unsupported insider-trading claims.

The thesis-facing language is German with Swiss orthography. Use `ss` instead
of German sharp s in thesis-facing prose.

## Hypotheses

H1 - Brier Score calibration:
Polymarket delivers better-calibrated forecasts than FiveThirtyEight and RCP.
The deterministic method is Brier Score comparison, with decomposition or
calibration analysis only where sample size and methodology allow it.

H2 - Information integration speed:
Polymarket integrates new information faster than traditional sources. The
deterministic method is event-window analysis around curated events, including
CAR-style price movement summaries and documented update timing.

H3 - Whale alpha / early signal detection:
Large wallet activity may precede price movements. The deterministic method is
distribution-derived wallet classification, lead-time histograms, and Granger
tests. Granger results may be described only as predictive temporal structure,
not proof of causal insider trading.

## Data Sources

- Polymarket CLOB/Gamma APIs for market prices and metadata.
- FiveThirtyEight historical forecast or polling CSV data.
- RealClearPolitics polling averages, only usable as probability forecasts after
  an explicitly documented transformation.
- Dune Analytics and Polygon-related sources for wallet and trade data.
- GDELT for daily news tone and volume.
- Manually curated event catalog for event-window analysis.

## Current Data State

The current SQLite database path is `data/thesis.db`.

Read-only inventory on 2026-05-17 found these tables:

| Table | Rows | Notes |
| --- | ---: | --- |
| `polymarket_prices` | 307 | Daily Polymarket prices from 2024-01-05 to 2024-11-06. |
| `whale_trades` | 25,113 | Wallet trade data; current rows are all `BUY`. |
| `poll_forecasts` | 245 | FiveThirtyEight rows only in current inventory; RCP remains unresolved. |
| `sentiment_scores` | 310 | GDELT daily sentiment rows. |
| `events_timeline` | 20 | Curated events exist and need methodological review before H2. |
| `analysis_summaries` | 6 | Precomputed summaries exist; treat as deterministic outputs only after tests. |
| `llm_audit_log` | 4 | Early audit entries exist from prior agent experiments. |
| `market_maker_exclusions` | 5 | Exclusion list used for whale-trade filtering. |

## Current Implementation State

The deterministic foundation has begun:

- `operations/analysis/data_inventory.py` inventories SQLite tables.
- `operations/analysis/brier_score.py` computes an initial H1 baseline.
- `operations/analysis/calibrate.py` contains calibration and comparison logic.
- `operations/validation/` contains validation models and report helpers.
- `data/results/` contains H1 result artifacts, including Brier scores,
  Diebold-Mariano output, and a reliability curve image.

The repository also contains early agent, MCP, tool, and audit modules from an
older architecture. These are parked until the deterministic core is stable.

Known gaps:

- RCP probability transformation must be documented and populated before use in
  H1 comparisons.
- Event-window methodology must be written before H2 analysis.
- CAR/reaction-speed pipeline is not yet implemented.
- Distribution-derived whale classification is not yet implemented.
- Whale timing and Granger pipelines are not yet implemented.
- Agent interpretation must wait until deterministic outputs are validated.

## Near-Term Priority

Synchronize documentation first, then continue with small deterministic commits:
schema migration, source-of-truth cleanup, RCP methodology, event-window
specification, wallet distribution inventory, and only then H2/H3 pipelines.
