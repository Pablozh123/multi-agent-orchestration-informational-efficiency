# WHALE_METHOD.md

## Current Data Limitation

Current whale-trade inventory has two important limitations:

- Rows appear to be BUY-only.
- The minimum observed `amount_usd` is 10000.

These facts must be treated as data-source or ingestion constraints until
verified. They must not be silently converted into analytical whale definitions.

## Decision Status

- h3_tier_status: selected
- selected_tier_method: wallet_cumulative_amount_usd_percentiles
- lead_lag_status: blocked
- granger_status: blocked
- blocking_reason: lead-lag and Granger remain blocked until the selected
  wallet-tier method is implemented and tested.
- required_before_code: H3 wallet classification, lead-lag, or Granger
  implementation.

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

Wallet tiers must be derived from the actual observed distribution. The
selected primary method is wallet-level cumulative observed `amount_usd`
percentiles.

Tier field:

- Group rows by `wallet_address`.
- Compute `SUM(amount_usd)` per wallet over the observed H3 dataset.
- Compute percentile thresholds from that wallet-level distribution at runtime.
- Do not hardcode USD threshold values.

Selected tiers:

- `tier_1_top_1pct`: wallets at or above the 99th percentile.
- `tier_2_top_5pct`: wallets at or above the 95th percentile and below the
  99th percentile.
- `tier_3_top_10pct`: wallets at or above the 90th percentile and below the
  95th percentile.
- `tier_4_observed_baseline`: wallets below the 90th percentile.

Boundary rule:

- Ties at a percentile boundary are assigned to the higher tier.
- Thresholds are calculated from the observed wallet distribution in the
  filtered dataset used for H3, then documented in output metadata.

Diagnostics:

- `trade_count` and `max_trade_amount_usd` are retained as diagnostics for the
  first H3 implementation.
- They do not define tiers in the primary method.
- Combined rank scores may be considered later as sensitivity analysis, not as
  the primary H3 tier rule.

## Future Distribution-Derived Classification

Before H3 implementation:

- Inspect wallet-level distributions.
- Document whether sell-side rows are absent, unavailable, or filtered out.
- Separate source filters from analytical definitions.
- Compute tier thresholds from observed wallet-level cumulative `amount_usd`
  percentiles.
- Add tests for boundary cases.

Implementation must verify:

- the number of observed wallets,
- the direction distribution,
- the minimum observed `amount_usd` as source-filter metadata,
- percentile thresholds used for tiers,
- tier membership counts,
- boundary behavior for wallets exactly on threshold values.

## Distribution Inventory

Inventory status: complete for the initial observed H3 dataset.

Output file:

- `data/results/h3_wallet_distribution_inventory.json`

Observed inventory:

- trade rows: 25113
- wallets: 3006
- direction distribution: BUY-only in the current data extract
- minimum observed `amount_usd`: 10000.0, documented as source-filter
  metadata only

Runtime percentile thresholds from wallet-level cumulative observed
`amount_usd`:

- `p90`: 120698.45799999998
- `p95`: 234234.58379
- `p99`: 866859.93675

Resulting tier counts:

- `tier_1_top_1pct`: 32
- `tier_2_top_5pct`: 120
- `tier_3_top_10pct`: 150
- `tier_4_observed_baseline`: 2704

The inventory file is compact metadata and does not contain raw wallet address
lists.

## No Insider Wording

The thesis may discuss whether wallet data provide early signals. It must not
describe wallets as insiders, insider traders, or proof of insider activity
unless there is independent non-market evidence, which is not currently in
scope.
