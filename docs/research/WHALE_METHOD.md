# WHALE_METHOD.md

## Current Data Limitation

Current whale-trade inventory has two important limitations:

- Rows appear to be BUY-only.
- The minimum observed `amount_usd` is 10000.

These facts must be treated as data-source or ingestion constraints until
verified. They must not be silently converted into analytical whale definitions.

## Allowed Claims

Allowed language:

- Wallet activity shows timing patterns under the specified dataset and model.
- Certain dataset-relative wallet tiers precede or coincide with price movement.
- Granger tests indicate predictive lead-lag structure under model assumptions.
- Results are exploratory or supportive, subject to data limitations.

## Disallowed Claims

Do not claim:

- Proof of insider trading.
- Proof of causal manipulation.
- Proof that a wallet had private information.
- That `amount_usd >= 10000` defines a whale unless it is explicitly marked as
  an upstream source filter.
- That BUY-only data captures full wallet intent.

Avoid insider wording in empirical claims. Use neutral terms such as
`wallet timing`, `early signal`, `lead-lag pattern`, or `predictive structure`.

## Dataset-Relative Wallet Tiers

Wallet tiers must be derived from the actual observed distribution. Candidate
approaches for later implementation:

- Percentile tiers by cumulative `amount_usd`.
- Percentile tiers by trade count.
- Percentile tiers by maximum single-trade size.
- Combined rank score across volume, count, and concentration.

The final tier method must be deterministic, documented, and tested before H3
lead-lag or Granger analysis.

## Future Distribution-Derived Classification

Before H3 implementation:

- Inspect wallet-level distributions.
- Document whether sell-side rows are absent, unavailable, or filtered out.
- Separate source filters from analytical definitions.
- Choose tier thresholds from observed percentiles or another reproducible
  distribution-based rule.
- Add tests for boundary cases.

## No Insider Wording

The thesis may discuss whether wallet data provide early signals. It must not
describe wallets as insiders, insider traders, or proof of insider activity
unless there is independent non-market evidence, which is not currently in
scope.

