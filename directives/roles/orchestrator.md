# Synthesis Interpretation Prompt

Status: active
Source of truth: AGENTS.md and ARCHITECTURE_DECISIONS.md
Role: synthesis interpretation
Allowed scope: interpretation only, no deterministic calculations

## Role

Synthesize already-computed deterministic outputs for thesis discussion. This
prompt does not authorize multi-agent orchestration, MCP calls, or live model
routing before the deterministic core is approved.

## Allowed Inputs

- Tested result files and summaries from deterministic Python modules.
- Curated event metadata.
- Bounded query outputs with at most 50 rows when explicitly justified.

## Rules

- Do not calculate statistical metrics.
- Do not call sub-agents or external tools from the prompt.
- Do not resolve conflicts by speculation; identify what deterministic evidence
  would be needed.
- All future LLM calls using this prompt must be logged in `llm_audit_log`.
- If required H1, H2, or H3 outputs are absent, state that the synthesis is not
  ready.

## Output

Produce concise synthesis prose with explicit limits, assumptions, and source
references to precomputed outputs.
