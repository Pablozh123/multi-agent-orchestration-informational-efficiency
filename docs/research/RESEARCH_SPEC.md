# RESEARCH_SPEC.md

## Research Objective

The thesis evaluates the informational efficiency of decentralized prediction
markets, using Polymarket as the main case and comparing it with traditional
forecast or polling sources where the data are methodologically compatible.

The empirical focus is the 2024 US presidential election. The project asks
whether Polymarket prices are better calibrated, react faster to curated public
events, and whether wallet activity contains dataset-relative early signal
patterns.

## Hypotheses

H1: Brier Score calibration

Polymarket probability forecasts may be better calibrated than comparable
traditional probability forecasts. FiveThirtyEight can be compared when its rows
represent probabilities. RCP cannot be treated as a probability forecast unless
a transformation is documented and tested.

H2: Information integration speed

Polymarket may integrate public information faster than traditional forecast or
polling sources. This requires a curated event catalog and pre-specified event
windows before CAR or reaction-speed analysis.

H3: Wallet-based early signal detection

Large or influential wallets may show lead-lag patterns relative to market price
movements. Any classification must be derived from the observed wallet or trade
distribution. Granger tests can support predictive timing claims, not proof of
true causality.

## Non-Goals

- No agent implementation before deterministic H1, H2, and H3 outputs exist.
- No MCP demo layer before the deterministic core is complete.
- No ML scope yet.
- No causal insider-trading claims.
- No arbitrary whale thresholds.
- No RCP probability comparison without documented transformation.
- No raw table dumps into LLM prompts.

## Deterministic-Core Rule

All statistical calculations are implemented in Python. LLMs may only interpret
precomputed outputs and must not calculate Brier scores, CAR, Granger tests,
wallet classifications, whale scores, or statistical metrics.

## RCP Rule

RCP is treated as a polling signal until a probability transformation is
documented, tested, and explicitly enabled in deterministic code.

Any function that includes RCP in Brier or calibration comparisons must require:

- `include_rcp=True`
- `rcp_transformation_documented=True`

## ML Scope Rule

Machine learning is not in scope yet. Do not add ML models, feature stores,
training pipelines, embeddings, vector databases, or automated classifiers until
the deterministic empirical pipeline is complete and reviewed.

## Agent And MCP Deferred Rule

Agents and MCP are interpretation and demo layers only. They remain deferred
until deterministic H1, H2, and H3 outputs exist, pass tests, and have written
methodology notes.

