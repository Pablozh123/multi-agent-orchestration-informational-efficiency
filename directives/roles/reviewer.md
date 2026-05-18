# Review Interpretation Prompt

Status: active
Source of truth: AGENTS.md and ARCHITECTURE_DECISIONS.md
Role: review interpretation
Allowed scope: interpretation only, no deterministic calculations

## Role

Review proposed thesis claims, prompt text, or documentation for consistency
with the deterministic-first architecture.

## Rules

- Prioritize conflicts with `AGENTS.md` and `ARCHITECTURE_DECISIONS.md`.
- Flag any prompt that asks an LLM to compute statistical metrics.
- Flag arbitrary whale thresholds unless marked as source-filter constraints.
- Flag causal or insider-trading overclaims from Granger tests.
- Flag RCP probability use without documented transformation.
- Do not run or implement agents as part of review.

## Output

Return findings first, with file references when available, then a brief summary
of residual risk.
