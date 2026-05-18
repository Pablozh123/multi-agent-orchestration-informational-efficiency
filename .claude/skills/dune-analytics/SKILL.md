---
name: dune-analytics
description: Interpret precomputed Dune or wallet-trade outputs. Do not define whale thresholds or fetch data from the prompt.
---

Status: active
Source of truth: AGENTS.md and ARCHITECTURE_DECISIONS.md
Role: Dune and wallet-data interpretation
Allowed scope: interpretation only, no deterministic calculations

# Dune And Wallet Data Interpretation

Use this skill only to interpret wallet or trade summaries already collected,
validated, and processed by deterministic Python code.

## Rules

- Do not run live Dune queries from prompt context.
- Do not define whales using arbitrary fixed thresholds.
- Treat any fixed source filter as an ingestion constraint, not as an analytical
  whale classification.
- Use only distribution-derived wallet tiers from deterministic outputs.
- Do not speculate about wallet owner identity.
- Do not describe wallet timing as proof of insider trading.

## Safe Interpretation Language

- "The distribution-derived top tier shows ..."
- "The timing pattern is consistent with a lead-lag signal under this model ..."
- "The result requires robustness checks before thesis-level claims ..."
