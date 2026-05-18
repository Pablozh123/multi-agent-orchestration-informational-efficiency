# EVENT_SELECTION.md

## Purpose

This document controls event selection before H2 event-window and CAR analysis.
It exists to prevent cherry-picking and to keep the event study reproducible.

## Decision Status

- h2_window_status: selected
- selected_primary_window: [0d, +1d]
- selected_secondary_windows: [-1d, +3d]
- not_selected_windows: [-1h, +1h]
- decision_reason: current Polymarket price data are daily, so the primary H2
  event window must be daily rather than intraday.
- h2_output_shape_status: accepted
- h2_persistence_status: approved_for_compact_summary_only
- required_before_code: complete for initial daily event-window baseline.

## Inclusion Criteria

An event may be included only if it meets all criteria:

- It is relevant to the 2024 US presidential election market being studied.
- It has a specific public timestamp or a justified UTC approximation.
- It has at least one credible source URL.
- It can be assigned an event type before looking at market reaction.
- It has a pre-analysis expected direction or is explicitly marked neutral.
- It has a documented relevance score.
- It is entered in the canonical event catalog before CAR is run.

## Exclusion Criteria

Exclude events when:

- The timestamp cannot be bounded well enough for the selected event window.
- The source is unverifiable, anecdotal, or only available after the study
  period without contemporaneous evidence.
- The event is too broad, slow-moving, or continuous for a discrete window.
- The event is selected because a large price move was already observed.
- The expected direction cannot be stated without using later market reaction.
- The event duplicates another catalog entry without adding a distinct timestamp
  or information shock.

## Event Types

Allowed initial event types:

- `debate`
- `legal`
- `primary`
- `candidate_change`
- `endorsement`
- `poll_release`
- `election_administration`
- `major_news`
- `other_curated`

New event types require a short methodology note before use.

## Required Fields

Each canonical event row requires:

- `event_id`
- `event_date`
- `event_time_utc`
- `title`
- `description`
- `event_type`
- `source_url`
- `expected_direction`
- `relevance_score`

The tracked seed CSV contains the curated event set for the first deterministic
H2 output. Add events only after manual source review. Do not add, remove, or
reclassify events based on observed market reactions.

## Window Definitions

Window definitions must be fixed before CAR code runs.

Selected windows:

- Primary daily window: `[0d, +1d]`
- Secondary sensitivity window: `[-1d, +3d]`

Not selected for the current dataset:

- Intraday short window: `[-1h, +1h]`

Reason: current Polymarket price data are daily. Intraday windows require
intraday price observations and must not be used unless such data are added and
validated later.

## H2 Output Shape Review

Review date: 2026-05-18

Accepted output files:

- `data/results/h2_event_window_rows.csv`
- `data/results/h2_event_window_summary.csv`

The row-level output shape is accepted as the deterministic calculation trace.
It contains:

- event identifier and window label,
- event date and observed price date,
- relative day within the pre-specified window,
- observed daily price change,
- expected daily change from the estimation window,
- abnormal change,
- cumulative abnormal change,
- estimation observation count.

The summary output shape is accepted as the compact thesis-facing H2 result
table. It contains the canonical event metadata plus one final cumulative
abnormal change per event and selected window.

## Daily Window Limitations

The first H2 baseline uses daily Polymarket price observations. This means:

- `event_time_utc` is retained for source transparency, but calculations use
  the event calendar date.
- Same-day and next-day movement can be measured; intraday reaction speed
  cannot be measured.
- Events occurring after the daily price observation may partially appear in
  the following daily row.
- The `[-1h, +1h]` window remains out of scope until intraday prices are added
  and validated.
- Missing daily observations would reduce `observed_days`; the current output
  includes all expected days for the selected curated events.

## Persistence Decision

Persist compact H2 summaries later, not the full row-level trace.

Approved later target:

- Write deterministic, compact H2 summary records into `analysis_summaries`.
- Use the accepted summary CSV shape as the source of truth for the first
  persistence implementation.
- Store bounded JSON metrics and metadata only; do not dump raw row-level data
  into `analysis_summaries` or prompts.

Not approved:

- Persisting the full `h2_event_window_rows.csv` trace into
  `analysis_summaries`.
- Changing the curated event set during persistence.
- Using LLMs to calculate, transform, or validate CAR values.

## Source Quality Rules

Preferred sources:

- Official campaign, debate, court, election, or platform records.
- Major wire services or established newspapers.
- Archived pages where the live page may change.
- Timestamped public posts only when the timestamp is essential and verifiable.

Avoid:

- Unsourced summaries.
- Retrospective commentary without contemporaneous timestamp support.
- Social-media screenshots without accessible source URLs.

## No Cherry-Picking Rule

Events must be selected by predefined criteria before event-window results are
computed. If an event is added, removed, merged, or reclassified after seeing
market reactions, that change must be documented as a post-hoc sensitivity
decision and must not be presented as part of the primary specification.
