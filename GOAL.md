# GOAL.md

## Active Goal

goal_id: goal-swiss-referendum-efficiency-001
title: Build Swiss 10-million referendum Polymarket-vs-polls comparison
status: active
phase: Phase 11: Swiss Referendum Efficiency Comparison
why:
- H1-H3 deterministic baseline outputs and thesis-facing summaries exist.
- The read-only Polymarket collector foundation exists and can be reused
  without authenticated channels, trading credentials, agents, MCP runtime
  layers, ML, database writes, or order endpoints.
- The 14 June 2026 Swiss vote on `Keine 10-Millionen-Schweiz` is a current
  referendum with a live Polymarket market and several public poll releases.
- The research question is now a bounded efficiency comparison: how Polymarket
  approval probabilities for the initiative differ from curated poll shares
  and whether poll publications are followed by observable Polymarket moves.
- BFS/admin.ch provides official referendum and population context. The
  currently curated voting-intention values come from SRG/gfs.bern,
  Tamedia/LeeWas, and YouGov Schweiz, not from BFS.
deliverables:
- Add a curated poll catalog for the 10-million initiative with source URLs,
  fieldwork windows, publication timestamps, Yes/No/undecided shares, sample
  sizes, and uncertainty metadata where available.
- Add a read-only Polymarket snapshot collector for the exact 10-million
  initiative market under `switzerlands-june-referendum-what-will-pass`.
- Add deterministic comparison outputs that match each Polymarket snapshot to
  the latest prior poll.
- Add a latest-by-source comparison output that compares the latest local
  Polymarket snapshot with the newest prior poll from each curated poll source.
- Compute descriptive raw and decided-voter Yes gaps in Python.
- Add bounded public CLOB price-history collection around curated poll release
  timestamps.
- Add poll-release impact rows that require pre- and post-publication
  Polymarket snapshots before any timing statement is made.
- Add descriptive 1h, 6h, 24h, and 48h post-publication reaction-window
  changes where local Polymarket observations exist.
- Add a tidy poll-reaction-window output with one row per poll and window for
  later filtering, charting, and thesis tables.
- Add a deterministic reaction-window figure so post-publication Polymarket
  movement windows are visible in the local dashboard.
- Add a deterministic information-response output that compares each new poll
  signal direction with Polymarket reaction-window directions.
- Add a deterministic information-response figure so faster, delayed, or
  different Polymarket processing is visible in the local dashboard.
- Generate a local HTML dashboard and a simple figure from deterministic local
  artifacts.
- Generate a deterministic latest-summary report for thesis-facing result
  reporting from the same local artifacts.
- Verify the generated dashboard and figure deterministically so the local
  running view is testable even when browser tooling is unavailable.
- Add a bounded one-command refresh runner that collects one new snapshot and
  regenerates the local dashboard without running continuously.
- Add a deterministic running-status artifact that reports local output
  presence and snapshot recency for the current view.
- Add an explicit source-boundary audit so BFS/admin.ch context sources cannot
  be mistaken for voting-intention poll sources.
- Document that poll shares are not model-implied win probabilities and that
  the decided-voter share is only `yes_share / (yes_share + no_share)`.
- Keep the old monitor/wallet graph work untouched while this separate
  referendum comparison track is built.
scope:
- `data/swiss_referendum_10mio_polls.csv`.
- `operations/collectors/swiss_referendum_polymarket.py`.
- `operations/collectors/swiss_referendum_history.py`.
- `operations/collectors/swiss_referendum_refresh.py`.
- `operations/analysis/swiss_referendum_efficiency.py`.
- `data/results/swiss_referendum_10mio_*`.
- `data/results/swiss_referendum_10mio_source_audit.csv`.
- `docs/research/SWISS_REFERENDUM_EFFICIENCY.md`.
- Focused tests for the new collector and comparison builder.
out_of_scope:
- Trading, order placement, order cancellation, authenticated user channels,
  trading credentials, PnL, profitability claims, strategy backtests, cloud
  deployment, runtime agents, MCP demo layers, model routing, ML, and database
  writes.
- Treating BFS as the source of voting-intention poll shares unless a future
  source-checked BFS poll table exists.
- Claiming causality from a poll release to a Polymarket price movement.
- Interpreting divergence labels as proven overvaluation, undervaluation,
  inefficiency, tradeability, or private-information evidence.
acceptance_criteria:
- Exactly one active goal remains in this file.
- New Polymarket collection is read-only and uses only public market metadata.
- Poll input rows include source URLs and publication timestamps or explicit
  timestamp precision.
- Poll shares and Polymarket probabilities are compared only by deterministic
  Python code.
- The methodology note explains the poll-share handling before outputs are
  interpreted.
- The dashboard shows current Polymarket Yes probability, latest matched poll
  value, raw gap, decided-voter gap, poll-impact status, source files, and
  limitations.
- The latest-summary report states what was generated, the key numerical
  result, a bounded interpretation, the main limitation, and links the figure.
- The dashboard and metadata show a source-boundary audit that marks BFS/admin.ch
  as context and SRG/gfs.bern, Tamedia/LeeWas, and YouGov Schweiz as poll
  sources.
- Metadata includes a deterministic dashboard verification block for the HTML
  structure and nonblank figure.
- The refresh runner can be called manually to collect exactly one bounded
  Polymarket snapshot and regenerate comparison outputs.
- The running-status artifact reports latest snapshot age, local output
  presence, and whether the local view is fresh under a configured threshold.
- Poll-impact rows are incomplete unless a local snapshot exists before and
  after the poll release.
- Reaction-window changes remain descriptive pre/post comparisons and must not
  be interpreted as causal poll effects.
- The tidy reaction-window output uses the same descriptive no-causality scope
  as the wide poll-impact table.
- Information-response labels remain direction-only descriptors and must not be
  interpreted as statistical significance, causality, tradeability, or proven
  market efficiency.
- Historical Polymarket price points are fetched only for bounded windows
  around curated poll publication timestamps.
- Outputs contain no wallet addresses and no order instructions.
- No LLM, agent, MCP, ML, database write, authenticated endpoint, or order path
  is activated.
- Tests cover the new collector, poll validation, comparison matching,
  divergence labels, and output generation.
- `STATUS.md` and `docs/project/WORK_LOG.md` are updated before stopping work.
- Review checks pass before recommending a commit.
next_commit: feat: add swiss referendum information response view

## Decision Inputs For This Goal

- Polymarket event page:
  `https://polymarket.com/de/event/switzerlands-june-referendum-what-will-pass`.
- Gamma event slug:
  `switzerlands-june-referendum-what-will-pass`.
- 10-million market slug:
  `will-the-no-to-ten-million-switzerland-initiative-be-approved-in-switzerlands-june-14-2026-popular-vote`.
- Public Gamma metadata on 2026-06-08 reported the 10-million market with
  `outcomePrices` around Yes 0.225 and No 0.775.
- The Polymarket page on 2026-06-08 showed `No to ten million Switzerland` at
  about 23 percent with about USD 247k market volume.
- SRG/gfs.bern wave 1, published 2026-05-08, reported 47 percent Yes,
  47 percent No, and 6 percent undecided.
- Tamedia/20 Minuten/LeeWas wave 1, published 2026-04-29, reported 52 percent
  Yes, 46 percent No, and 2 percent undecided.
- YouGov Schweiz wave 1, published 2026-05-05, reported 45 percent Yes,
  46 percent No, and 8 percent undecided.
- YouGov Schweiz wave 2 interim, published 2026-05-27, reported 43 percent
  Yes, 51 percent No, and 6 percent undecided.
- YouGov Schweiz wave 2 final, published 2026-06-02, reported 38 percent Yes,
  55 percent No, and 7 percent undecided.
- Tamedia/20 Minuten/LeeWas wave 2, published 2026-06-03, reported 47 percent
  Yes, 52 percent No, and 1 percent undecided.
- SRG/gfs.bern wave 2, published 2026-06-03, reported 45 percent Yes,
  52 percent No, and 3 percent undecided.
- admin.ch states that the vote is on 2026-06-14 and explains the official
  initiative context.
- BFS-related population scenarios are context evidence, not current
  voting-intention poll probabilities.

## Done Means

- The local dashboard can be regenerated from the curated poll catalog and
  bounded Polymarket snapshots.
- One manual refresh command can update the local dashboard while preserving
  bounded snapshot history.
- The latest comparison can state, descriptively, whether the Polymarket Yes
  probability is above, near, or below the latest poll Yes share.
- The latest source-level comparison can state, descriptively, whether the
  Polymarket Yes probability is above, near, or below each curated source's
  newest prior poll Yes share.
- The information-response table can state, descriptively, whether Polymarket
  moved in the same direction as a new poll signal immediately, with delay, or
  not within the bounded 48h window.
- The project can collect additional bounded snapshots later and rerun the same
  deterministic comparison without changing methodology.
- Poll-publication impact rows can use bounded public CLOB price history to
  show the first observable pre/post Polymarket move around curated poll
  releases.

## Paused Previous Goal

- `goal-monitor-detection-backtest-wallet-graph-001` is paused by this explicit
  goal change. Its generated artifacts and uncommitted worktree changes are not
  reverted by this goal.
