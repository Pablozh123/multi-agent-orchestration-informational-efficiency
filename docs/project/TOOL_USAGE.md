# TOOL_USAGE.md

## Codex Usage

Use Codex for repository work:

- Reading and editing code or documentation.
- Running tests.
- Creating small deterministic modules.
- Reviewing diffs and commit boundaries.
- Keeping changes aligned with `AGENTS.md` and `ARCHITECTURE_DECISIONS.md`.

Codex must not use LLM reasoning to compute statistical metrics. Metrics belong
in deterministic Python code.

Before stopping, Codex must run the project-control workflow:

1. `python -m operations.project.update_status`
2. add an entry to `docs/project/WORK_LOG.md`
3. `python -m operations.project.review_check`
4. `python -m operations.project.commit_plan`
5. show `git diff --stat`

Use `--skip-pytest "reason"` only when the user explicitly accepts skipping
tests or when running pytest would be misleading.

## Codex Workflow Roles

Codex may operate in these development-process roles:

- Planner: converts the active goal into an implementation plan without editing
  files unless execution is explicitly requested.
- Implementer: makes scoped code or documentation changes for the active goal.
- Reviewer: checks diffs, tests, deterministic-core rules, data assumptions, and
  commit boundaries.
- Verifier: runs tests and project-control checks before stopping.

These roles are workflow modes for repository work. They are not thesis runtime
agents, do not replace deterministic Python analysis, and must not activate MCP,
model routing, or multi-agent interpretation.

## Superpowers Usage

Use Superpowers for planning discipline and execution structure when helpful:

- Breaking work into small phases.
- Tracking blockers.
- Keeping implementation commits atomic.
- Reviewing whether a task belongs in deterministic core or deferred layers.

Do not use it to bypass the deterministic-core rule.

## Perplexity Usage

Use Perplexity only for literature discovery, source discovery, and high-level
research orientation. Verify important academic claims against primary sources
before thesis use.

Do not use Perplexity outputs as empirical results.

## Zotero Usage

Use Zotero for citation management:

- Store academic papers.
- Track source metadata.
- Attach PDFs and notes.
- Export BibTeX for Overleaf.

Zotero is not an analysis tool.

## Obsidian Usage

Use Obsidian for research notes, concept maps, and thesis-writing structure.

Keep empirical claims traceable to deterministic outputs or cited sources.

## MCP Deferred Strategy

MCP is deferred until the deterministic H1, H2, and H3 outputs exist and pass
tests. Existing MCP code must remain guarded or parked in legacy paths.

No MCP server should run multi-agent analysis before the deterministic core is
complete.

## Live Monitor Operator Usage

Use the live monitor only through bounded, read-only commands.

Preflight:

```powershell
.\.venv\Scripts\python.exe -m operations.collectors.polymarket_watchlist
```

Single refresh:

```powershell
.\.venv\Scripts\python.exe -m operations.collectors.polymarket_monitor_refresh --source live --samples 1 --curated-watchlist-input data\monitor_v2_curated_watchlist.csv --max-markets 12
```

Diagnostic run:

```powershell
.\.venv\Scripts\python.exe -m operations.collectors.polymarket_monitor_refresh --source live --samples 3 --delay-seconds 305 --reset --curated-watchlist-input data\monitor_v2_curated_watchlist.csv --max-markets 12
```

Production-like baseline run:

```powershell
.\.venv\Scripts\python.exe -m operations.collectors.polymarket_monitor_refresh --source live --samples 20 --delay-seconds 305 --reset --curated-watchlist-input data\monitor_v2_curated_watchlist.csv --max-markets 12 --baseline-observations 30 --min-baseline-observations 20
```

The dashboard is written to:

```text
data/results/monitor_v2_polymarket_dashboard.html
```

The main dashboard now includes:

- live monitor status,
- rolling-history summary,
- reference-case similarity link,
- monitor reference-candidate link.

Open or describe the latest dashboard entry point:

```powershell
.\.venv\Scripts\python.exe -m operations.tools.monitor_dashboard_launcher
```

Open it in the default browser:

```powershell
.\.venv\Scripts\python.exe -m operations.tools.monitor_dashboard_launcher --open
```

Update the compact repeated-window registry from the latest bounded run:

```powershell
.\.venv\Scripts\python.exe -m operations.analysis.monitor_v2_live_window_registry --run-id expanded_window_002 --run-label "second expanded 12-market baseline"
```

Validate and score wallet reference cases:

```powershell
.\.venv\Scripts\python.exe -m operations.analysis.wallet_reference_case_audit
.\.venv\Scripts\python.exe -m operations.analysis.wallet_reference_pattern_features
.\.venv\Scripts\python.exe -m operations.analysis.wallet_reference_similarity
.\.venv\Scripts\python.exe -m operations.analysis.monitor_reference_candidates
```

Generate the bounded anomaly review queue:

```powershell
.\.venv\Scripts\python.exe -m operations.analysis.monitor_anomaly_review_queue
```

Manual anomaly review statuses are curated in:

```text
data/monitor_anomaly_review_status_updates.csv
```

Allowed status values are `needs_human_review`, `source_check_pending`,
`reviewed_false_context`, `reviewed_keep_candidate`, and `thesis_excluded`.
The queue generator validates this worksheet and merges its status, reviewer,
source URL, event URL, and review note fields into
`data/results/monitor_anomaly_review_queue.csv`.

The same generator also writes bounded case-review packets for later human
review or future audited MCP/agent access:

```text
data/results/monitor_anomaly_case_review_packets.csv
data/results/monitor_anomaly_case_review_packets.json
```

These packet artifacts are summaries only. They must not be treated as proof of
private information, misconduct, causality, tradeability, profitability, or
market inefficiency.

The generator also writes deterministic review-status transition gates:

```text
data/results/monitor_anomaly_review_status_transitions.csv
data/results/monitor_anomaly_review_status_transitions.json
```

Transition gates define allowed next manual statuses and thesis-use blocking
rules. They do not automatically accept, reject, or upgrade any case.

Final anomaly-review decisions are curated manually in:

```text
data/monitor_anomaly_review_decisions.csv
```

The generator validates this worksheet against the transition gates and writes
readiness artifacts:

```text
data/results/monitor_anomaly_review_decision_readiness.csv
data/results/monitor_anomaly_review_decision_readiness.json
```

`reviewed_keep_candidate` requires documented limitations and a thesis-use
scope. Decision-readiness outputs do not apply decisions automatically.

The generator also writes a static future-access contract:

```text
data/results/monitor_anomaly_review_access_contract.json
```

This contract lists bounded artifacts and future tool names only. It does not
implement MCP, agents, raw SQL, wallet-address access, or order/trading paths.

Open the reference similarity dashboard:

```text
data/results/wallet_reference_similarity_dashboard.html
```

Open the current monitor reference-candidate dashboard:

```text
data/results/monitor_reference_candidate_dashboard.html
```

Interpretation rule:

- fewer than 3 buckets: interface check only,
- 3 to 19 buckets: diagnostic only,
- 20 or more buckets: closer to the v2 baseline contract, still review before
  thesis-facing claims.

The monitor is descriptive. It must not be used for trading claims,
misconduct claims, or profitability claims.

The anomaly review queue is also descriptive. Future agents and MCP tools may
read only bounded queue/summary artifacts after audit logging exists; they must
not calculate metrics, expose wallet addresses by default, run raw SQL, or
create trading instructions.

## ChatGPT And Claude Role

ChatGPT and Claude may help:

- Explain deterministic outputs.
- Draft thesis prose from bounded summaries.
- Review methodology for clarity.
- Suggest literature search terms.

They must not:

- Calculate Brier, CAR, Granger, wallet tiers, or statistical metrics.
- Receive raw table dumps.
- Invent events, data, or sources.
- Make causal insider-trading claims.
