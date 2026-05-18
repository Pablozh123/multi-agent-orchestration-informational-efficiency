# EVENT_SELECTION.md

## Purpose

This document controls event selection before H2 event-window and CAR analysis.
It exists to prevent cherry-picking and to keep the event study reproducible.

## Decision Status

- h2_window_status: blocked
- selected_primary_window: not_selected
- selected_secondary_windows: not_selected
- blocking_reason: canonical event catalog and final window choice are not yet
  reviewed.
- required_before_code: CAR or event-study implementation.

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

The current seed CSV is intentionally header-only. Do not invent real events to
fill it. Add events only after manual source review.

## Window Definitions

Window definitions must be fixed before CAR code runs.

Initial candidate windows for review:

- Intraday short window: `[-1h, +1h]`
- Same-day window: `[0h, +24h]`
- Multi-day window: `[-1d, +3d]`

The final analysis may use one or more of these windows, but the selected set
must be documented before results are inspected.

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
