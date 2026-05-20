# Feature Landscape

**Domain:** Academic prediction market efficiency analysis system (Polymarket vs FiveThirtyEight vs RealClearPolitics)
**Researched:** 2026-03-09
**Confidence:** MEDIUM-HIGH — well-established academic literature on forecasting evaluation and event studies;
  some Polymarket-specific API patterns based on training data (verify against current API docs).

---

## Table Stakes

Features where absence = academic rigor fails. A thesis committee will ask about every one of these.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Brier Score computation | Primary proper scoring rule for probabilistic forecasts; any comparison study must use it | Low | Formula: (1/n) * sum((f_t - o_t)^2); range 0.0–1.0 |
| Time-series Brier Score | Rolling window and cumulative BS over Jan–Nov 2024; single terminal BS is insufficient | Medium | Need daily/weekly granularity; Polymarket has continuous prices, polls are discrete |
| Calibration curve (reliability diagram) | Shows whether 70%-confidence predictions actually resolve 70% of the time | Medium | Bin predictions into deciles; plot observed frequency vs predicted probability |
| Sharpness / resolution decomposition | Decomposes BS into calibration + resolution + uncertainty (Murphy 1973 decomposition) | Medium | Separates "were you right on average" from "were you decisive" |
| Head-to-head comparison table | Direct Brier Score table: Polymarket vs 538 vs RCP over same time window | Low | The thesis core result; must be machine-reproducible |
| Statistical significance test | t-test or Diebold-Mariano test on forecast accuracy differences | Medium | Without p-values the comparison is anecdotal |
| Data caching layer (SQLite) | Reproducibility; rate-limit compliance; offline re-analysis | Medium | Already in project constraints; every API response timestamped + stored |
| Idempotent ingestion | Re-running pipeline must not duplicate records | Medium | Use upsert with (source, market_id, timestamp) primary key |
| UTC timestamp enforcement | Cross-source alignment requires canonical timezone | Low | Already in constraints; must be enforced at ingestion not post-hoc |
| Price interpolation / gap-filling | Polymarket prices are event-driven, not regular intervals; polls update ~weekly | Medium | Linear interpolation between ticks for event-window alignment |
| Event catalog | Structured list of key events (debate dates, Comey letter equiv., poll releases) with exact UTC timestamps | Medium | Required for event study; without a catalog there is no "event" to study |
| Data provenance metadata | Which API version, pull date, parameter set produced each table | Low | Required for reproducibility section of thesis |

---

## Differentiators

Features that make the thesis more than a Brier Score table — the "contribution" that justifies a full BA.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Event study: abnormal price reaction | Measures information integration speed: how many hours after Event X did each source reflect new information | High | Core H2 test; uses event window [-24h, +72h] around each event; cumulative abnormal change vs baseline |
| Event study: information half-life | Fit an exponential decay to post-event price adjustment; compare Polymarket vs poll update lag | High | Polymarket should show shorter half-life if informationally efficient |
| Whale trade detection | Flag transactions >$10k from single wallet in single direction within short window | High | Core H3 test; requires Dune Analytics queries on Polygon USDC transfers to Polymarket contract |
| Whale lead-time analysis | Compute median time delta: whale_trade_timestamp vs next significant price move (>2pp) | High | Tests if whales trade systematically before price moves; use Granger causality or simple lead-lag correlation |
| Sentiment-price correlation | GDELT/Reddit sentiment scores correlated with same-day Polymarket price delta | High | Establishes whether public sentiment drives or follows prices; supports efficiency discussion |
| Anomaly detection on price series | Flag sudden price jumps (>3 sigma) without corresponding news event in catalog | Medium | Evidence of market microstructure effects or insider knowledge |
| Volume-weighted price series | Use trade volume to weight price observations; pure TWAP is more informative than last-trade price | Medium | More accurate representation of market consensus |
| Baseline naive model | Always-predict-prior-day's-price model and always-predict-50% model as Brier Score floor | Low | Required to contextualize whether any model beats naive; very cheap to implement |
| Cross-event reproducibility | Run same analysis on multiple key events (primary debates, VP announcement, October surprises) | Medium | Single-event findings are anecdote; multi-event findings are evidence |
| Agent orchestrator divergence detection | Orchestrator identifies moments where market price and sentiment/polls diverge by >N pp | Medium | Enables Claude API calls to generate natural-language explanations of divergences for thesis text |

---

## Anti-Features

Deliberate exclusions. Building these would waste thesis time or undermine academic credibility.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Real-time / live dashboard | Thesis is retrospective analysis of 2024 data; live system adds infra complexity with zero academic value | Batch analysis scripts that can be re-run deterministically |
| Copy-trading / execution system | Turns academic work into a product; raises IRB/ethics questions; out of scope per PROJECT.md | Mention as future application in thesis conclusion |
| Coverage of markets outside 2024 US election | Scope creep; different markets have different liquidity regimes that confound comparison | One well-analyzed market is better than five shallow ones |
| Automated thesis writing via Claude | Claude API is for analytical summarization of detected patterns, not ghostwriting | Use Claude to explain flagged anomalies in structured output, not to write thesis prose |
| Custom blockchain node / direct Polygon indexing | Dune Analytics already provides this with better DX; direct indexing adds weeks of work | Use Dune queries; document as methodology limitation |
| User authentication / multi-user access | Single-researcher system; security layer adds complexity with zero benefit | Single .env file, local execution |
| Real-time sentiment scoring | GDELT and Reddit APIs have historical access; live sentiment for past events is meaningless | Batch pull historical GDELT/Reddit data for Jan–Nov 2024 window |
| Percentage-point rounding to integers | Polymarket prices in [0.0, 1.0] must not be rounded; polls already suffer discrete update granularity | Preserve float precision throughout; round only at display layer |
| Per-trade P&L calculation | This is not a trading system; profit metrics are irrelevant and misleading in academic context | Focus on information efficiency metrics (BS, speed, calibration) exclusively |

---

## Feature Dependencies

The diagram below shows which features must exist before others can be built.

```
Data Caching Layer (SQLite)
    └── Idempotent Ingestion
        ├── Price interpolation / gap-filling
        │   ├── Time-series Brier Score
        │   │   ├── Brier Score head-to-head table
        │   │   ├── Calibration curve
        │   │   └── Murphy decomposition
        │   └── Volume-weighted price series
        │       └── Anomaly detection
        └── Event Catalog
            ├── Event study: abnormal price reaction
            │   └── Event study: information half-life
            └── Cross-event reproducibility

Whale trade detection (Dune Analytics)
    └── Whale lead-time analysis

Sentiment-price correlation
    └── Orchestrator divergence detection
        └── Claude API anomaly explanation

Baseline naive model  (independent — build early for sanity checks)
Statistical significance test  (depends on Brier Score head-to-head table)
```

---

## MVP Recommendation

A minimal thesis that would pass defense and test all three hypotheses:

**Phase 1 — Data foundation (build first, everything else blocks on this)**
1. Data caching layer with idempotent ingestion
2. UTC enforcement at ingest
3. Price interpolation / gap-filling
4. Event catalog (manually curated, ~20 key events)

**Phase 2 — H1 evidence (Brier Score / efficiency)**
5. Time-series Brier Score for all three sources
6. Calibration curves
7. Baseline naive model
8. Head-to-head comparison table + statistical significance test

**Phase 3 — H2 evidence (reaction speed)**
9. Event study: abnormal price reaction
10. Event study: information half-life

**Phase 4 — H3 evidence (whale alpha)**
11. Whale trade detection via Dune
12. Whale lead-time analysis

**Phase 5 — Supporting evidence**
13. Sentiment-price correlation
14. Anomaly detection
15. Orchestrator divergence detection + Claude explanations

**Defer unless time permits:**
- Murphy decomposition (nice-to-have, not required for H1-H3)
- Volume-weighted price series (can use simple TWAP)
- Cross-event reproducibility beyond top 5 events

---

## Academic Rigor Notes

These are methodological constraints that affect feature design, not just implementation.

- **Brier Score requires resolved outcomes.** Polymarket prices must be compared against final election outcome (Biden dropout, Harris nomination, Trump win) not against each other. Store resolution data explicitly.
- **Calibration requires sufficient sample size per bin.** With one election market and ~100 prediction points, calibration curves will have wide confidence intervals. Acknowledge this limitation explicitly in thesis.
- **Event study requires a "clean window" assumption.** Events must not overlap within the event window (+-72h). Flag overlapping events and exclude or handle carefully.
- **Whale analysis is correlational, not causal.** Granger causality can support H3 but cannot prove intent. Frame carefully — "systematic lead-time" not "insider trading."
- **FiveThirtyEight model vs poll averages are different products.** 538 model is a probability forecast (directly comparable to Polymarket). RCP poll average is not — it must be converted to implied probability (typically via a logistic or simple threshold). Document the conversion method.
- **Polymarket has liquidity constraints.** In low-volume periods, prices may not reflect true market probability. Consider filtering out observations with volume below a threshold (e.g., <$1k daily volume) or flagging them.

---

## Sources

- Brier, G.W. (1950). "Verification of forecasts expressed in terms of probability." Monthly Weather Review. — canonical BS definition, HIGH confidence
- Murphy, A.H. (1973). "A new vector partition of the probability score." — BS decomposition, HIGH confidence
- Standard event study methodology: Campbell, Lo, MacKinlay (1997) "The Econometrics of Financial Markets" Ch. 4 — HIGH confidence
- Wolfers & Zitzewitz (2004) "Prediction Markets" Journal of Economic Perspectives — canonical framework for comparing prediction markets to alternatives, HIGH confidence
- Manski (2006) "Interpreting the predictions of prediction markets" — on converting market prices to probabilities, MEDIUM confidence (verify interpretation still applies to Polymarket's CLOB structure)
- Diebold-Mariano test (1995) — standard test for comparing forecast accuracy, HIGH confidence
