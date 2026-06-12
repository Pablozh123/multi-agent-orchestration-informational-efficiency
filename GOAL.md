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
- A short advisor handoff note exists so the Word update can be sent with a
  clear subject, attachment order, discussion-order pointer, questions, and
  scope boundaries.
- A pending advisor feedback log exists so later feedback can be translated
  into small scoped follow-up commits.
- The advisor handoff package is updated so the Word report, handoff note,
  readiness board, drafting sequence, feedback log, source review, and index
  appear in one consistent order.
- The high-level project view explicitly answers the path forward without
  Review-Access: advisor feedback, source review, H1-H3 writing,
  table/figure integration, Swiss result gate, and final QA.
- The advisor checklist contains a recommended discussion order for the next
  Betreuung so the high-level path can be discussed quickly.
- A goal-completion audit exists so achieved evidence and remaining final
  gates are separated before any completion claim.
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
- A future agent-pipeline upgrade plan exists so later source-review,
  evidence-drafting, wording, table/figure, advisor, monitor, and bounded MCP
  improvements are documented without activating runtime agents.
- Tests cover the generated evidence map and curated result package where
  reasonable.
- `STATUS.md` and `docs/project/WORK_LOG.md` are updated before stopping work.
- Review checks pass before recommending a commit.
next_commit: docs: draft source review progress protocol

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
