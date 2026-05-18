# CODE_REVIEW_CHECKLIST.md

## Scope Checks

- Does the change match the requested task?
- Are unrelated files untouched?
- Are agents, MCP, model routing, ML, and cloud deployment still deferred?
- Is the change small enough for an atomic commit?

## Tests

- Are new deterministic functions covered by focused tests?
- Do invalid examples fail where validation is expected?
- Do CLI paths run without crashing?
- Has the full test suite been run when code changed?
- If tests were not run, is the reason documented?

## Deterministic-Core Checks

- Are all statistical calculations in Python?
- Are LLMs limited to interpreting precomputed outputs?
- Is there no raw table dump into prompts?
- Is there no `SELECT *` without `LIMIT`?
- Are broad queries justified inside deterministic modules only?

## Data Assumptions

- Are source filters separated from analytical definitions?
- Are RCP rows excluded unless the transformation is documented and explicitly
  enabled?
- Are whale thresholds distribution-derived or clearly marked as legacy/source
  filters?
- Are event windows based on curated event rows?
- Are Granger results described without causal proof language?

## Documentation Checks

- Are methodology assumptions documented before analysis code uses them?
- Are blockers updated in project docs when they change?
- Does thesis-facing German use Swiss spelling?
- Are TODO placeholders clearly marked and not presented as real data?

## Commit Readiness

- Does `git diff --stat` show only intended files?
- Does `git status --short` reveal unrelated dirty files that should be left
  out of the commit?
- Are generated artifacts intentionally included or excluded?
- Does the commit message describe one coherent change?

