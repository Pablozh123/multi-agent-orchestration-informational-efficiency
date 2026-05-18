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

