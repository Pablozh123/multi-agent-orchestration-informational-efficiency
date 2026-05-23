# Wallet Reference Cases

## Purpose

Wallet reference cases are used to learn neutral anomaly patterns for the
Polymarket politics/geopolitics monitor. They are not accusations and they are
not proof of misconduct.

The first registry contains two reference types:

- a publicly reported Iran/U.S. military-action cluster,
- a large-flow AdrianCronauer example in an Iran-related market.

All reference labels are descriptive. They mean `requires_human_review`, not
causal proof, private-information proof, tradeability, or profitability.

## Source Policy

- Public reporting is reference evidence, not final truth.
- Reported figures stay marked as `reported`.
- Python-computed facts must use `computed_*` wording or `fact_source=computed`.
- Unknown fields stay `unknown`; they must not be guessed.
- Wallet-address inputs may exist in curated source files but must not be
  pasted into LLM prompts or thesis-facing summaries.

## Current Reference Cases

`iran_cluster_2026_bubblemaps_reported`

- Type: publicly reported cluster.
- Primary source:
  `https://www.cbsnews.com/news/betting-on-iran-war-insider-trading-concerns-prediction-markets-60-minutes/`
- Supporting source:
  `https://cointelegraph.com/news/bubblemaps-polymarket-cluster-win-military-bets`
- Reported pattern:
  - nine connected accounts,
  - more than 80 U.S. military-action bets,
  - about USD 2.4 million reported profit,
  - about 98 percent reported win rate,
  - reported timing close to key developments,
  - reported funding timing and CEX routing.
- Interpretation: reference case for cluster/timing/outcome-pattern review,
  not a computed claim.

`adriancronauer_large_iran_flow_2026_05_14`

- Type: large concentrated flow reference.
- Source:
  `https://x.com/PolymarketStory/status/2051659961260753294`
- Public profile supplied by the user:
  `https://polymarket.com/de/@adriancronauer?via=history`
- Reported pattern:
  - USD 103248 BUY NO trade,
  - 87c reported price,
  - market: `US x Iran permanent peace deal by May 31 2026?`,
  - observed at `2026-05-14T08:56:00Z`.
- Interpretation: large-flow and theme-concentration reference, not a
  misconduct claim.

## Pattern Labels

`large_trade_flow`

- Large observed or reported trade size.
- First implementation uses reported amount if no local trade row exists.

`market_concentration`

- Position or case is concentrated in a politics/geopolitics theme such as
  Iran, ceasefire, military action, or regional escalation.

`event_proximity`

- Public source reports timing near a catalyst.
- A computed version requires timestamped event mapping and no-lookahead
  validation.

`fresh_wallet_or_short_history`

- Wallet appears new or has little history.
- Currently `unknown` unless source or on-chain data supports it.

`cluster_link_reported`

- Multiple accounts are reported as linked.
- Currently reported only for the Iran cluster.

`shared_funding_reported`

- Funding timing, exchange routing, or consolidation links are reported.
- Computed version requires direct on-chain funding data.

`high_reported_win_rate`

- A public source reports an extreme win rate.
- This must not be treated as computed unless full entry, exit, resolution,
  and position-history data are available.

`same_theme_repeated_positions`

- Repeated positions in the same theme are reported or computed.
- First implementation marks reported cases only.

## Review States

- `candidate`: proposed, not checked.
- `source_checked`: source URL and timestamp checked.
- `market_mapped`: relevant market identified.
- `wallet_verified`: public wallet/profile mapping checked.
- `pattern_computed`: deterministic features computed.
- `accepted_reference_case`: eligible as a reference case.
- `rejected_or_unverifiable`: insufficient or unreliable evidence.

## Outputs

- `data/reference_cases/wallet_reference_cases.csv`
- `data/reference_cases/wallet_reference_cases_metadata.json`
- `data/results/wallet_reference_case_audit.csv`
- `data/results/wallet_reference_case_audit_metadata.json`
- `data/results/wallet_reference_pattern_features.csv`
- `data/results/wallet_reference_pattern_features_metadata.json`
- `data/results/wallet_reference_similarity_scores.csv`
- `data/results/wallet_reference_similarity_summary.csv`
- `data/results/wallet_reference_similarity_matrix.png`
- `data/results/wallet_reference_similarity_dashboard.html`
- `data/results/wallet_reference_similarity_metadata.json`

Output policy:

- Audit and feature outputs do not expose wallet addresses.
- Similarity outputs do not expose wallet addresses.
- Outputs do not contain order instructions.
- Outputs do not use agents, MCP, ML, LLM calls, or database writes.

## Similarity Score

`reference_case_similarity_score` is implemented as a deterministic
equal-weight pattern-overlap score:

```text
matched triggered reference patterns / all triggered reference patterns
```

This means:

- `1.0` means the candidate contains every triggered pattern label from the
  reference profile.
- `0.0` means no triggered reference label overlaps.
- The score is directional. A small two-label large-flow case can overlap 50
  percent with another two-label large-flow profile, while the same case may
  cover only a small share of a broader six-label cluster profile.
- Self-matches in the current dashboard are calibration rows, not new evidence.

The first generated reference matrix shows:

- AdrianCronauer vs AdrianCronauer: `1.0`, self-profile calibration.
- Iran/U.S. cluster vs Iran/U.S. cluster: `1.0`, self-profile calibration.
- Iran/U.S. cluster vs AdrianCronauer reference: `0.5`, because it shares the
  `market_concentration` label but not `large_trade_flow`.
- AdrianCronauer vs Iran/U.S. cluster reference: `0.166667`, because it shares
  only `market_concentration` out of six triggered cluster labels.

Allowed interpretation: similarity is a review cue. It is not a probability,
causal test, trading signal, profitability estimate, or misconduct finding.

## Visual Review

Open the local dashboard:

```powershell
.\.venv\Scripts\python.exe -m operations.analysis.wallet_reference_similarity
```

Then open:

```text
data/results/wallet_reference_similarity_dashboard.html
```

The dashboard contains:

- best reference match per candidate,
- similarity matrix,
- triggered pattern profiles,
- all candidate/reference comparisons,
- interpretation limits.

## Next Step

Future live monitor alerts can reuse this reference taxonomy through bounded
candidate feature files. The score should expose only:

- pattern labels,
- source artifact references,
- review status,
- claim scope,
- limitations.

It must not expose raw wallet dumps or make misconduct, causal, tradeability,
or profitability claims.
