---
name: polymarket-api
description: Interpret documented Polymarket source data and cached outputs. Do not make hidden live API calls from prompt context.
---

Status: active
Source of truth: AGENTS.md and ARCHITECTURE_DECISIONS.md
Role: Polymarket source-data interpretation
Allowed scope: interpretation only, no deterministic calculations

# Polymarket Source Interpretation

Use this skill only to interpret documented Polymarket data that has already
been collected, cached, validated, and processed by deterministic Python code.

## Rules

- Do not make hidden live Polymarket API calls.
- Do not treat incomplete price histories as complete without inventory checks.
- Do not calculate market metrics in the prompt.
- Use cached SQLite data and deterministic result artifacts as the source of
  truth.
- Keep claims bounded to the market, date range, and token represented in the
  precomputed output.

## Notes

Polymarket prices can be interpreted as market-implied probabilities only after
checking the relevant market, outcome token, timestamp coverage, and data
collection limitations.
