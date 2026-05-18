# Coding Standards Directive

Status: active
Source of truth: AGENTS.md and ARCHITECTURE_DECISIONS.md
Role: repository coding guardrail
Allowed scope: interpretation only, no deterministic calculations

## Standards

- Keep modules small and typed.
- Prefer deterministic Python functions over prompt logic.
- Add tests where reasonable, especially for statistics, schema changes,
  source transformations, and query guardrails.
- Validate database writes where reasonable.
- Do not hide API calls inside analysis code.
- Do not use `SELECT *` without `LIMIT`.
- Keep tool-style query outputs bounded to 50 rows unless explicitly justified.
- Do not modify unrelated files.
- Keep commits atomic.
