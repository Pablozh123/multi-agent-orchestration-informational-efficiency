# Methodology Directive

Status: active
Source of truth: AGENTS.md and ARCHITECTURE_DECISIONS.md
Role: shared methodology guardrail
Allowed scope: interpretation only, no deterministic calculations

## Purpose

Use this directive only to frame interpretation of deterministic outputs that
already exist. It must not be used to compute metrics, choose thresholds after
seeing results, or replace Python analysis code.

## Rules

- Treat Python outputs as the only source for Brier scores, calibration metrics,
  CAR, Granger tests, wallet classifications, and statistical summaries.
- Interpret Granger results as lead-lag predictability under a specified model,
  not proof of insider trading or true causal influence.
- Treat RCP as a polling-average source unless a documented probability
  transformation is present.
- Interpret event-window results only after the event catalog and windows are
  curated.
- Clearly separate empirical results, assumptions, and limitations.
- Use Swiss spelling in thesis-facing German text.
