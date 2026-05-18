---
name: brier-score
description: Interpret precomputed Brier Score and calibration outputs for the thesis. Do not compute scores in the prompt.
---

Status: active
Source of truth: AGENTS.md and ARCHITECTURE_DECISIONS.md
Role: Brier Score interpretation
Allowed scope: interpretation only, no deterministic calculations

# Brier Score Interpretation

Use this skill only to interpret Brier Score, calibration, reliability, or
Diebold-Mariano outputs already computed by deterministic Python modules.

## Rules

- Do not calculate Brier scores, Brier Skill Scores, calibration bins, p-values,
  or reliability decompositions in the prompt.
- Do not invent missing benchmark values.
- Treat RCP results as valid only if the RCP probability transformation is
  documented.
- State sample-size and single-event limitations when interpreting calibration.
- Refer back to the result artifact or Python module that produced the value.

## Safe Interpretation Language

- "The precomputed Brier Score is lower for ..."
- "This suggests better forecast accuracy under the implemented metric ..."
- "This does not by itself prove broader market efficiency ..."
