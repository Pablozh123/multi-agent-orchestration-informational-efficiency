# Swiss 10-Million Referendum Efficiency Comparison

This note defines the deterministic comparison track for the 14 June 2026 Swiss
popular vote on the initiative `Keine 10-Millionen-Schweiz`.

## Scope

- Polymarket market:
  `switzerlands-june-referendum-what-will-pass`, submarket
  `will-the-no-to-ten-million-switzerland-initiative-be-approved-in-switzerlands-june-14-2026-popular-vote`.
- Poll input:
  `data/swiss_referendum_10mio_polls.csv`.
- Output artifacts:
  `data/results/swiss_referendum_10mio_*`.
- Source-boundary audit:
  `data/results/swiss_referendum_10mio_source_audit.csv`.
- Latest summary:
  `data/results/swiss_referendum_10mio_latest_summary.md`.
- Running status:
  `data/results/swiss_referendum_10mio_running_status.json`.
- Auto-refresh metadata:
  `data/results/swiss_referendum_10mio_auto_refresh_metadata.json`.
- Auto-refresh log:
  `data/results/swiss_referendum_10mio_auto_refresh_log.csv`.
- Tidy reaction-window rows:
  `data/results/swiss_referendum_10mio_poll_reaction_windows.csv`.
- Latest poll-source comparison:
  `data/results/swiss_referendum_10mio_latest_source_comparison.csv`.
- Information-response rows:
  `data/results/swiss_referendum_10mio_information_response.csv`.
- Reaction-window figure:
  `data/results/swiss_referendum_10mio_reaction_windows.png`.
- Information-response figure:
  `data/results/swiss_referendum_10mio_information_response.png`.

## Source Boundary

BFS/admin.ch is used as official referendum and population-context evidence.
The current voting-intention shares are not BFS values. They are curated from
SRG/gfs.bern, Tamedia/LeeWas, and YouGov Schweiz public releases.

The comparison must not state that BFS published the voting-intention poll
shares unless a future official BFS poll table is added and source-checked.

The source audit records this boundary explicitly: admin.ch/Bundeskanzlei and
BFS rows are context rows without voting-intention values, while SRG/gfs.bern,
Tamedia/LeeWas, and YouGov Schweiz rows are poll inputs used for the
deterministic comparison.

YouGov documents that its MRP model uses known population proportions from BFS
for poststratification. This does not make the reported vote-intention shares
BFS values; they remain YouGov poll/model outputs in the curated catalog.

## Poll Share Handling

Poll values are survey shares, not model-implied win probabilities.

The deterministic outputs report two poll-side values:

- `poll_yes_share`: the reported Yes share including undecided respondents in
  the denominator.
- `poll_yes_decided_share`: `yes_share / (yes_share + no_share)`.

`poll_yes_decided_share` is only a transparent decided-voter normalization. It
is not a probability model, not RCP, and not a forecast transformation.

## Divergence Handling

For each Polymarket snapshot, the pipeline attaches the latest poll with
`published_at_utc <= collected_at_utc` and computes:

- `raw_yes_gap = polymarket_yes_probability - poll_yes_share`.
- `decided_yes_gap = polymarket_yes_probability - poll_yes_decided_share`.

The first dashboard label uses `raw_yes_gap` with a default 5 percentage-point
threshold:

- `polymarket_above_poll_yes_share`
- `near_poll_yes_share`
- `polymarket_below_poll_yes_share`

The dashboard also exposes a simpler poll-proxy relation:

- `above_poll_proxy`
- `near_poll_proxy`
- `below_poll_proxy`

These labels answer whether the Polymarket Yes probability sits above, near, or
below the latest poll Yes share. They are descriptive labels only. They are not
true valuation labels, mispricing proof, market efficiency proof, causality, or
a trading signal.

Because several poll sources are curated, the pipeline also writes
`data/results/swiss_referendum_10mio_latest_source_comparison.csv`. This file
compares the latest local Polymarket snapshot with the newest prior poll from
each source. It is a cross-source poll-proxy view only; it is not a poll
average, forecast model, valuation model, or true-mispricing test.

## Poll Release Impact Rows

Poll-impact rows compare the closest local Polymarket observation before a poll
publication with the first local Polymarket observation at or after
publication. Observations can come from bounded live snapshots or bounded
public CLOB price-history windows around curated poll publication timestamps.

If a pre or post observation is missing, the row is marked as incomplete.
Missing history must not be filled by guessing or by scraping chart pixels.

For each poll release, the deterministic output also reports descriptive
changes from the closest pre-publication observation to the last available
local observation inside 1h, 6h, 24h, and 48h post-publication windows. These
reaction-window values are timing descriptors only; they are not causal poll
effects and are not efficiency, tradeability, or true-mispricing evidence.

The same window values are also written in tidy form to
`data/results/swiss_referendum_10mio_poll_reaction_windows.csv`, with one row
per poll and window. This format is intended for later filtering, charting, and
thesis tables without changing the methodology.

The dashboard also includes
`data/results/swiss_referendum_10mio_reaction_windows.png`, a deterministic bar
chart of the same 1h, 6h, 24h, and 48h descriptive changes.

## Information Response Handling

To make the "faster, slower, or different" question visible, the pipeline also
builds an information-response table. For each curated poll release after the
first one, it computes a direction-only poll signal:

- `poll_decided_yes_signal_change`: current poll decided Yes share minus the
  immediately previous curated poll decided Yes share.
- `poll_signal_direction`: `up`, `down`, or `unchanged`.

The table then compares that poll-signal direction with Polymarket movements in
the 1h, 6h, 24h, and 48h post-publication windows. The resulting
`information_processing_label` is interpreted as follows:

- `immediate_same_direction_1h`: Polymarket moved in the same direction within
  the first hour.
- `delayed_same_direction_6h`, `delayed_same_direction_24h`, or
  `delayed_same_direction_48h`: Polymarket moved in the same direction only in
  a later window.
- `no_same_direction_within_48h`: no same-direction Polymarket move was
  observed within the bounded 48h window.
- `no_prior_poll_signal`: the first curated poll has no previous poll baseline.

This is not a statistical significance test and not causal evidence. It only
shows whether the sign of the Polymarket move is aligned with the sign of the
new poll signal, and how quickly that alignment first appears in the locally
observed windows.

## Refresh And Scheduled Collection

The local running view can be refreshed with one explicit bounded command:

```powershell
.\.venv\Scripts\python.exe -m operations.collectors.swiss_referendum_refresh --source live
```

This collects one public Polymarket snapshot, appends it to the local snapshot
history, fetches bounded public CLOB price-history windows around the curated
poll releases, and regenerates the comparison CSV, poll-impact CSV, figure,
dashboard, source audit, and metadata. It is not a background daemon.

For local scheduled collection until the vote, use the scheduler-safe
one-shot wrapper:

```powershell
.\.venv\Scripts\python.exe -m operations.collectors.swiss_referendum_auto_refresh --source live --until-utc 2026-06-14T10:00:00Z --min-spacing-minutes 55
```

This command is designed for Windows Task Scheduler or a manual invocation.
Each invocation checks the cutoff, latest local snapshot age, and lock file. If
collection is allowed, it runs exactly one bounded read-only refresh and exits.
If the vote cutoff has passed, a recent snapshot already exists, or another
invocation is locked, it writes skip metadata and exits without collecting.

The default cutoff `2026-06-14T10:00:00Z` corresponds to 12:00 Europe/Zurich on
voting day. Scheduled collection remains local and time-bounded; it is not a
resident daemon and does not add agents, MCP tooling, ML, LLM interpretation,
database writes, authenticated channels, or order endpoints.

The local Windows task used for this collection is named
`BA-Thesis-Swiss-Referendum-Auto-Refresh`. It can be removed with:

```powershell
Unregister-ScheduledTask -TaskName "BA-Thesis-Swiss-Referendum-Auto-Refresh" -Confirm:$false
```

## Dashboard Verification

Every generated dashboard is checked by deterministic Python code. The verifier
requires the expected title, the source-boundary audit section, at least four
tables, an embedded figure reference, a nonblank PNG figure, and required
dashboard text such as the current poll-proxy relation.

The verification summary is written to
`data/results/swiss_referendum_10mio_efficiency_metadata.json` under
`dashboard_verification`.

## Latest Summary

Each run also writes
`data/results/swiss_referendum_10mio_latest_summary.md`. The report is rendered
by deterministic Python from the local comparison artifacts. It includes what
was generated, the key numerical result, a bounded interpretation, the main
limitation, and a Markdown link to the generated figure.

## Running Status

Each refresh writes
`data/results/swiss_referendum_10mio_running_status.json`. This local status
file reports the latest snapshot timestamp, its age in minutes, the configured
freshness threshold, whether required output artifacts exist, and whether the
current local view is fresh under that configured threshold.

The status is only an artifact-recency check. It does not imply market-data
completeness and does not add any causal, tradeability, or valuation claim.

## Current Curated Poll Releases

- Tamedia/20 Minuten/LeeWas wave 1, published 2026-04-29: 52 percent Yes,
  46 percent No, 2 percent undecided.
- YouGov Schweiz wave 1, published 2026-05-05: 45 percent Yes, 46 percent No,
  8 percent undecided.
- SRG/gfs.bern wave 1, published 2026-05-08: 47 percent Yes, 47 percent No,
  6 percent undecided.
- YouGov Schweiz wave 2 interim, published 2026-05-27: 43 percent Yes,
  51 percent No, 6 percent undecided.
- YouGov Schweiz wave 2 final, published 2026-06-02: 38 percent Yes,
  55 percent No, 7 percent undecided.
- Tamedia/20 Minuten/LeeWas wave 2, published 2026-06-03: 47 percent Yes,
  52 percent No, 1 percent undecided.
- SRG/gfs.bern wave 2, published 2026-06-03: 45 percent Yes, 52 percent No,
  3 percent undecided.

## Limits

- No LLM calculates any metric.
- No database write is performed.
- No agents, MCP runtime layer, ML, authenticated channel, or order endpoint is
  used.
- More bounded Polymarket snapshots are required before publication-impact
  timing can be interpreted.
