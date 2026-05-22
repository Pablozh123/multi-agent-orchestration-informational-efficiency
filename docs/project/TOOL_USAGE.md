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
.\.venv\Scripts\python.exe -m operations.collectors.polymarket_monitor_refresh --source live --samples 1 --curated-watchlist-input data\monitor_v2_curated_watchlist.csv --max-markets 3
```

Diagnostic run:

```powershell
.\.venv\Scripts\python.exe -m operations.collectors.polymarket_monitor_refresh --source live --samples 3 --delay-seconds 305 --reset --curated-watchlist-input data\monitor_v2_curated_watchlist.csv --max-markets 3
```

Production-like baseline run:

```powershell
.\.venv\Scripts\python.exe -m operations.collectors.polymarket_monitor_refresh --source live --samples 20 --delay-seconds 305 --reset --curated-watchlist-input data\monitor_v2_curated_watchlist.csv --max-markets 3
```

The dashboard is written to:

```text
data/results/monitor_v2_polymarket_dashboard.html
```

Interpretation rule:

- fewer than 3 buckets: interface check only,
- 3 to 19 buckets: diagnostic only,
- 20 or more buckets: closer to the v2 baseline contract, still review before
  thesis-facing claims.

The monitor is descriptive. It must not be used for trading claims,
misconduct claims, or profitability claims.

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
