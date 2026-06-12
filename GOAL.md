# GOAL.md

## Active Goal

goal_id: goal-thesis-consolidation-001
title: Consolidate thesis-ready evidence, results, and future agent design
status: active
phase: Phase 12: Thesis Consolidation And Evidence Mapping
why:
- H1-H3 deterministic baseline outputs exist and pass project tests.
- The advisor report is now strong enough as a written update, but the thesis
  still needs a cleaner high-level consolidation layer.
- Methods, claims, interpretations, tables, and figures must map explicitly to
  deterministic artifacts and scientific sources.
- The result presentation should become thesis-ready: a small number of strong
  tables and figures instead of many raw artifacts.
- Future agent improvements may be planned only at a high level while runtime
  agents, MCP tools, model routing, autonomous execution, and unlogged LLM
  interpretation remain deferred.
deliverables:
- Create a deterministic thesis evidence map that links each central method,
  result, interpretation, limitation, and thesis claim to source artifacts and,
  where needed, literature sources.
- Create a compact thesis-ready result package with a deliberately small set
  of selected tables and figures for H1, H2, H3, the monitor prototype, and the
  Swiss referendum side track.
- Mark which outputs are thesis-facing now, descriptive only, blocked, or
  pending later source/result review.
- Document a high-level agent improvement roadmap that respects the project
  guardrails: deterministic Python metrics first, bounded summaries only,
  `llm_audit_log` for later LLM calls, no raw table dumps, max 50 rows, no
  wallet-address exposure by default, no order/trading paths, and no active
  runtime agent implementation.
- Create a submission-readiness board that separates draft-ready thesis work,
  final submission blockers, and deferred future-work/agent items.
- Create a thesis drafting sequence that turns the current gates into the next
  ordered BA writing steps.
- Keep the Swiss referendum track in data-collection mode until the 14 June
  2026 vote result is available; do not add a final efficiency interpretation
  before the official result.
- Keep monitor anomaly review outputs as prototype/appendix material unless
  human review and thesis-use gates later approve them.
scope:
- `operations/analysis/thesis_result_summaries.py`.
- `operations/analysis/thesis_figures.py`.
- New or updated deterministic thesis-consolidation scripts under
  `operations/analysis/`.
- `data/literature/literature_index.csv`.
- `data/results/thesis_*`.
- `docs/research/`.
- `ROADMAP.md`.
- Project workflow docs/status/log updates required before stopping.
out_of_scope:
- Multi-agent orchestration.
- MCP demo implementation.
- Claude Desktop integration.
- Model routing.
- Self-consistency runs.
- Cloud deployment.
- Trading, order placement, order cancellation, authenticated user channels,
  trading credentials, strategy PnL, profitability claims, or autonomous
  execution.
- Calculating metrics with LLMs or agents.
- Exposing raw monitor rows, raw wallet addresses, unrestricted SQL, or more
  than 50 rows through any future default tool surface.
- Claiming causality, private information, misconduct, tradeability,
  profitability, or market inefficiency from monitor labels or Granger tests.
acceptance_criteria:
- Exactly one active goal remains in this file.
- Each thesis-facing method has a deterministic implementation artifact and at
  least one suitable source or methodology reference where needed.
- Each thesis-facing interpretation names the deterministic artifact that
  supports it and its main limitation.
- The curated result package contains a small explicit set of recommended
  tables and figures, not a raw dump of every generated artifact.
- H1/H2/H3 interpretations remain bounded to the deterministic outputs and do
  not rely on LLM-calculated metrics.
- Swiss referendum outputs remain descriptive until the official result is
  available.
- Monitor and agent content is framed as prototype, appendix, or future work
  unless deterministic thesis-use gates approve it.
- Future agent pipeline design remains documentation-only and does not activate
  runtime agents, MCP tools, model routing, or unlogged LLM interpretation.
- A future-agent control audit exists so later pipeline improvements are
  mapped to allowed inputs, outputs, audit gates, blocked actions, max-row
  limits, and 0 active runtime rows.
- Submission readiness clearly marks Source Review, Swiss result mapping, and
  DOCX render QA as final gates while allowing bounded draft writing to
  continue.
- The next writing sequence is explicit, artifact-linked, and separates
  bounded draft work, final blockers, appendix-only content, and future work.
- The advisor report contains the current submission-readiness and drafting
  sequence view so the high-level next steps are visible in the Word update.
- The advisor report includes the bounded H1-H2-H3 chapter draft view so the
  Word update shows the 18 prose blocks, method and interpretation mapping,
  literature/source gates, deterministic artifacts, compact table/figure
  package, limitations, and final blockers without claiming Source Review
  completion.
- The advisor report includes the source-gated H1-H2-H3 drafting sequence so
  the Word update shows 15 paragraph-level writing steps, 23 linked Manual
  Source Review rows, 0 final-ready rows, compact table/figure actions,
  final blockers, and inactive future-agent boundaries.
- A short advisor handoff note exists so the Word update can be sent with a
  clear subject, attachment order, discussion-order pointer, questions, and
  scope boundaries.
- A pending advisor feedback log exists so later feedback can be translated
  into small scoped follow-up commits.
- An advisor feedback integration checklist exists so later feedback is mapped
  to one small commit scope with required source/artifact checks, compact
  table/figure boundaries, Swiss/result gates, final QA, and inactive
  future-agent limits.
- The advisor handoff package is updated so the Word report, handoff note,
  readiness board, drafting sequence, feedback log, manual source-review
  follow-up overview, source review, and index appear in one consistent order.
- The advisor handoff note and package now point to the refreshed Word report
  with Source-Gated H1-H2-H3 Drafting Sequence, 15 paragraph-level writing
  steps, 23 linked Manual Source Review rows, 23 pending rows, 0 final-ready
  rows, and the boundary that Review-Access remains paused.
- The advisor handoff note and package now include the Manual Source Review
  Follow-up Overview so the Dozent can see the 23 open H1-H2-H3 review rows
  before Ledger decisions, final citations, or source-status changes.
- An advisor/source-review follow-up plan exists so the path after
  Dozenten-Handoff is explicit: capture feedback, confirm Source Review depth,
  manually review H1/H2/H3 source rows, update the bounded chapter draft,
  recheck final gates, and keep agents future-work-only. It now uses the
  Manual Source Review Follow-up Overview as the compact control point for
  23 open H1-H2-H3 review rows, 9 unique sources, 23 pending rows, 0
  final-ready rows, and no source-status promotion.
- A H1 manual source-review follow-up exists so the first empirical-core
  review slice is startable with 10 H1 source rows, 4 H1 sources, method and
  interpretation Evidence IDs, deterministic artifacts, Page-/Section-Note,
  Claim-Support, Blocked-Wording, Citation-Use, and no automatic source-status
  promotion.
- A H2 manual source-review follow-up exists so the second empirical-core
  review slice is startable with 5 H2 source rows, 3 H2 sources, method and
  interpretation Evidence IDs, deterministic artifacts, Page-/Section-Note,
  Claim-Support, Blocked-Wording, Citation-Use, Kausalclaim-Grenze, and no
  automatic source-status promotion.
- A H3 manual source-review follow-up exists so the third empirical-core
  review slice is startable with 8 H3 source rows, 4 H3 sources, wallet and
  Granger method Evidence IDs, interpretation Evidence IDs, deterministic
  artifacts, Page-/Section-Note, Claim-Support, Blocked-Wording,
  Citation-Use, Granger-Grenze, Wallet-Grenze, and no automatic source-status
  promotion.
- A consolidated H1-H2-H3 manual source-review follow-up overview exists so
  the 23 open empirical-core review rows are visible in one compact control
  artifact with 9 unique sources, method/interpretation counts, access-route
  counts, final citation blockers, and inactive future-agent boundaries.
- The high-level project view explicitly answers the path forward without
  Review-Access: advisor feedback, source review, H1-H3 writing,
  table/figure integration, Swiss result gate, and final QA.
- The advisor checklist contains a recommended discussion order for the next
  Betreuung so the high-level path can be discussed quickly.
- A goal-completion audit exists so achieved evidence and remaining final
  gates are separated before any completion claim. It now includes the
  future-agent safety case as proof that later agent ideas remain
  documentation-only/deferred with 7 safety rows, 0 active safety rows, max 50
  rows, bounded inputs, `llm_audit_log`, and no runtime activation.
- A source-access audit exists so local PDF/HTML sources and external
  locator-review sources are separated before manual Source Review.
- A source-structure inventory exists so local source files can be prepared
  for manual Source Review without content interpretation, source-status
  promotion, or thesis-facing claims.
- Source-review decision packets exist so each Evidence-Source packet has a
  pending manual decision row for Page-/Section-Note, claim support,
  blocked-wording check, and final citation gate.
- A traceability audit exists so thesis-facing methods, interpretations,
  tables, and figures are checked against deterministic artifacts, literature
  IDs, limitations, captions, and final source-review gates before BA writing.
- A method/interpretation source coverage audit exists so every method and
  interpretation link is checked against `literature_index.csv`, citation
  readiness, deterministic primary artifacts, limitations, and remaining
  Source Review gates before BA writing.
- A H1-H2-H3 core writing package exists so each empirical core section binds
  methods, interpretations, literature IDs, deterministic artifacts, selected
  tables, selected figures, limitations, blocked wording, and Source Review
  gates before BA drafting.
- The thesis chapter draft integrates the H1-H2-H3 core mapping directly, so
  each empirical chapter shows method Evidence IDs, interpretation Evidence
  IDs, literature IDs, deterministic artifacts, selected table, selected
  figure, limitations, blocked wording, and Source Review gate in the prose
  draft.
- Bounded H1-H2-H3 source-review notes exist so the empirical core can be
  reviewed source-by-source with Page-/Section-Notes, Claim-Support decisions,
  Blocked-Wording checks, selected table/figure context, and no automatic
  source-status promotion.
- A source-review progress ledger exists so H1-H2-H3 manual review decisions
  can be preserved across regenerations without automatic source-status
  promotion or final citation claims.
- A H1-H2-H3 manual source-review execution pass exists so the empirical core
  has a source-by-source work order with Evidence IDs, selected tables/figures,
  deterministic artifacts, coverage checks, ledger states, Page-/Section-Note
  outputs, Claim-Support decisions, Blocked-Wording checks, Citation-Use gates,
  and no automatic source-status promotion.
- A source-review progress protocol exists so thesis-facing method coverage,
  interpretation coverage, compact result-package use, manual ledger flow,
  final citation gates, H1-H2-H3 drafting, and future-agent boundaries are
  ordered before continued BA writing. It now uses the Manual Source Review
  Follow-up Overview as the compact pre-Ledger control point for 23 open
  H1-H2-H3 review rows, 9 unique sources, 23 pending rows, 0 final-ready rows,
  and no source-status promotion.
- A source-review chapter handoff exists so H1-H2-H3 can be written chapter by
  chapter with Evidence IDs, literature IDs, deterministic artifacts, selected
  tables/figures, open Source Review rows, blocked wording, limitations, and
  future-agent boundaries visible before final citation. It now validates each
  chapter against the Manual Source Review Follow-up Overview before Ledger
  updates, keeping H1/H2/H3 detail-start files, pending rows, final-ready rows,
  and no source-status promotion visible.
- A chapter-level source-review checklist exists so H1-H2-H3 writing can be
  checked against coverage, literature review, result-package integration,
  limitations, blocked wording, final citation gates, and future-agent
  boundaries before final submission. It now uses the Manual Source Review
  Follow-up Overview in literature-review and final-citation checks, requiring
  the Overview-/Ledger-Abgleich before Ledger updates or final citation.
- A H1-H2-H3 drafting checklist exists so each empirical core chapter can be
  drafted in a fixed order: method setup, result statement, interpretation
  boundary, table/figure integration, Source Review citation gate, and
  future-agent boundary. It now carries the Manual Source Review Follow-up
  Overview-/Ledger-Abgleich into every source-review-and-citation drafting
  step before any final citation.
- A bounded H1-H2-H3 chapter draft exists so the empirical core has ordered
  prose blocks for method setup, result statement, interpretation boundary,
  table/figure integration, Source Review citation gate, and future-agent
  boundary without new metrics, raw artifact dumps, or final citation claims.
  It now carries the Manual Source Review Follow-up Overview-/Ledger-Abgleich
  into each H1/H2/H3 Source Review citation gate before final citation or
  source-status changes.
- The H1-H2-H3 bounded chapter draft carries source-coverage counts per
  chapter so each writing pass sees source links, unique source IDs, zero
  coverage gaps, and final Source Review blockers before prose is expanded.
- A H1-H2-H3 source-gated writing pass exists so the empirical core has three
  connected chapter drafts that preserve Evidence IDs, source coverage,
  deterministic artifacts, compact table/figure choices, limitations,
  blocked wording, Source Review gates, and inactive future-agent boundaries.
  It now carries the Manual Source Review Follow-up Overview-/Ledger-Abgleich
  through all three connected chapter drafts before final citation or
  source-status changes.
- A H1-H2-H3 source-gated thesis drafting pass exists so the empirical core
  has a paragraph-level writing sequence for method/result setup,
  interpretation/limitation, table/figure integration, manual Source Review
  execution, final gates, and future-agent boundaries while linking the 23
  manual Source Review rows and preserving 0 final-submission-ready rows. It
  now keeps the Manual Source Review Follow-up Overview-/Ledger-Abgleich
  visible in all review-action and finalgate rows.
- The main thesis chapter draft contains Source-Gated Integration blocks for
  H1, H2, and H3, so each empirical chapter now shows method binding,
  interpretation binding, literature IDs, deterministic artifacts, source
  coverage counts, selected table/figure IDs, final citation blockers, and
  inactive future-agent boundaries in the BA prose draft.
- The main thesis chapter draft also contains Source-Gated Drafting Sequence
  blocks for H1, H2, and H3, so the 15 paragraph-level steps, Manual Source
  Review counts, Page-/Section-Note, Claim-Support, Blocked-Wording,
  Citation-Use, compact table/figure integration, final blockers, and inactive
  future-agent boundaries are visible in the BA prose draft. It now carries
  the Manual Source Review Follow-up Overview-/Ledger-Abgleich through the
  H1/H2/H3 Quellengate, Source Review action, Manual Source Review execution,
  Finalgate, and Status lines.
- A future agent-pipeline upgrade plan exists so later source-review,
  evidence-drafting, wording, table/figure, advisor, monitor, and bounded MCP
  improvements are documented without activating runtime agents.
- The future agent-pipeline upgrade plan remains documentation-only but now
  names the post-source-gated sequence, Human-Owner, safe value,
  Proof-Artifact, Failure-Mode, bounded input/output limits, max 50 rows,
  `llm_audit_log`, and blocked actions for every future assistance role.
- A future-agent safety case exists so later agent ideas are checked against
  the current deterministic evidence lock: 4 thesis-facing methods, 4
  thesis-facing interpretations, 23 H1-H2-H3 Source-Links, 31 total
  method/interpretation Source-Links including Monitor/Swiss, 23 open manual
  Source Review rows, 5 core tables, 4 core figures, Swiss/result gates,
  DOCX-QA, bounded access, max 50 rows, `llm_audit_log`, and 0 active runtime
  rows before any future activation.
- A thesis final gate board exists so bounded draft permission, final
  submission readiness, evidence counts, blockers, Source Review, Swiss
  official result, DOCX render QA, project checks, and future-agent boundaries
  are separated in one highlevel artifact.
- Tests cover the generated evidence map and curated result package where
  reasonable.
- `STATUS.md` and `docs/project/WORK_LOG.md` are updated before stopping work.
- Review checks pass before recommending a commit.
next_commit: docs: refresh goal completion audit after safety case

## Running Side Goal

- `goal-swiss-referendum-efficiency-001` remains a running data-collection
  track until the 14 June 2026 vote. Do not add final referendum efficiency
  interpretation before the official result is available.

## Paused Previous Goal

- `goal-monitor-anomaly-review-queue-001` remains paused. Its deterministic
  queue and static access contract exist, but further review-access work is
  intentionally deferred while the thesis is consolidated.

- `goal-monitor-detection-backtest-wallet-graph-001` remains paused as a broad
  monitor expansion goal.
