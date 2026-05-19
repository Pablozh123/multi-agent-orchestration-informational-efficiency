# STRATEGY_AGENT_ARCHITECTURE.md

## Purpose

This document specifies the future agent and MCP layer for the thesis strategy
research prototype. It does not activate agents, MCP, live trading, model
routing, or autonomous execution.

The prototype is part of the thesis only as a historical backtest and research
design. It must not be presented as a guaranteed profitable system.

## Boundary

Allowed:

- Agents propose signal hypotheses.
- Python validates signal specifications.
- Python runs historical backtests and computes risk metrics.
- MCP exposes bounded summaries and tested result objects.
- Every future LLM call is logged in `llm_audit_log`.

Not allowed:

- Agents calculating Brier, CAR, Granger, wallet tiers, PnL, drawdown, or risk
  metrics.
- Raw table dumps into prompts.
- Autonomous trading.
- Live order execution.
- Profit guarantees.
- Treating exploratory backtest output as proof that a strategy will work
  out-of-sample.

## First Prototype Specification

strategy_prototype_status: specified

The first prototype is a deterministic historical research backtest design. It
does not implement a strategy yet. It defines what a later Python module must
accept, reject, compute, and report before any agent or MCP layer can use the
result.

Primary objective:

- Test whether bounded signal hypotheses derived from H1, H2, or H3 summaries
  have historical predictive value under explicit transaction-cost, slippage,
  position-limit, and evaluation-split assumptions.

Non-objectives:

- No live trading.
- No autonomous execution.
- No guarantee of profitability.
- No agent-computed PnL, drawdown, or risk metrics.
- No use of raw wallet addresses or unrestricted SQL in prompts.

### Candidate Signal Families

These are candidate families for future specification and review. They are not
implemented and are not thesis conclusions.

`h1_forecast_disagreement_signal`

- Source summaries: `data/results/thesis_h1_summary.csv`,
  `data/results/h1_brier_scores.csv`.
- Idea: compare Polymarket probability with a compatible probability forecast
  such as FiveThirtyEight.
- Guardrail: RCP remains excluded until a probability transformation is
  documented and tested.
- Main risk: forecast disagreement may reflect model timing or source
  construction rather than tradable inefficiency.

`h2_event_follow_through_signal`

- Source summaries: `data/results/thesis_h2_summary.csv`,
  `data/results/h2_event_window_summary.csv`.
- Idea: test whether pre-curated event classes produce daily follow-through or
  reversal patterns after the selected event windows.
- Guardrail: no events may be added after looking at returns unless the run is
  explicitly marked as a new sensitivity analysis.
- Main risk: small event count and daily data make overfitting easy.

`h3_wallet_timing_signal`

- Source summaries: `data/results/thesis_h3_summary.csv`,
  `data/results/h3_lead_lag_correlations.csv`,
  `data/results/h3_granger_results.csv`.
- Idea: test whether dataset-relative tier activity predicts next-day or
  multi-day Polymarket probability changes.
- Guardrail: use tier-level aggregates only, not wallet-address-level prompts.
- Main risk: BUY-only source data, daily alignment, and multiple testing.

`combined_summary_signal`

- Source summaries: H1, H2, and H3 thesis summaries only.
- Idea: combine one H1 disagreement condition, one H2 event condition, and one
  H3 tier-activity condition into a sparse hypothesis.
- Guardrail: this is a later sensitivity candidate, not the first baseline.
- Main risk: too many degrees of freedom for the current sample.

### First Baseline Recommendation

The first future backtest should be the simplest H3-derived daily timing
baseline:

- input: tier-level daily activity and daily Polymarket price changes,
- trigger: one pre-specified tier-activity condition,
- horizon: next daily close-to-close probability change,
- benchmark: no-position baseline plus simple always-exposed benchmark if
  methodologically justified,
- output: deterministic `BacktestResult` with costs, slippage, position limit,
  maximum drawdown, and observation count.

Reason:

- H3 already has tier-level daily activity, lead-lag, and Granger diagnostic
  artifacts.
- This avoids introducing RCP, new event selection, intraday data, ML, or raw
  wallet-address prompts.

### Rejection Criteria

A proposed signal specification must be rejected before backtesting if it:

- uses information unavailable at the simulated decision time,
- depends on raw table dumps or wallet-address prompt inspection,
- uses RCP as a probability without the documented transformation flags,
- changes event inclusion after inspecting returns,
- omits transaction costs, slippage, position limits, or evaluation split,
- requires live order execution,
- asks an agent or LLM to calculate metrics,
- cannot cite the deterministic source artifacts it depends on.

## Agent Roles

Agent role type: `Signal Generator`.

`NewsResearchAgent`

- Proposes event or news candidates with source URLs.
- May use Perplexity or web search for discovery.
- Must not add events directly to the canonical event catalog.
- Output: sourced candidate list for human review and deterministic loader.

`MarketPatternAgent`

- Reads bounded H1/H2/H3 thesis summaries.
- Proposes market-pattern hypotheses such as event-window asymmetry or lag
  sensitivity candidates.
- Must not inspect raw Polymarket tables directly.

`WalletSignalAgent`

- Reads wallet-tier summaries, not wallet-address dumps.
- Proposes signal hypotheses based on tier-level timing patterns.
- Must preserve the BUY-only and daily-alignment caveats.

`RiskReviewerAgent`

- Reviews proposed signal specifications for overfitting, lookahead bias,
  excessive degrees of freedom, and forbidden thesis claims.
- Must flag missing transaction-cost, slippage, position-limit, and drawdown
  assumptions.

`Orchestrator`

- Collects candidate signal specifications from agents.
- Sends only validated `SignalSpec` objects to Python backtests.
- Summarises deterministic backtest outputs.
- Logs every LLM call and tool result in `llm_audit_log`.

## MCP Tool Contracts

Future MCP tools must be bounded and summary-first:

- `get_h1_summary`
- `get_h2_summary`
- `get_h3_summary`
- `list_result_artifacts`
- `get_literature_map`
- `submit_signal_spec`
- `get_backtest_result`

Tool rules:

- Summary tools return thesis-facing summaries, not raw tables.
- `submit_signal_spec` validates a proposed signal but does not execute live
  trades.
- `get_backtest_result` returns deterministic backtest outputs that already
  exist or are generated by Python.
- No MCP tool may expose unrestricted SQL or more than 50 raw rows.

## Future Python Interfaces

The future strategy track should define typed interfaces before implementation:

`SignalSpec`

- signal identifier,
- signal family,
- hypothesis statement,
- deterministic source artifacts,
- input summary sources,
- market side or probability direction,
- trigger rule,
- holding or exit rule,
- maximum position size,
- evaluation window,
- lookahead prevention rule,
- rejection criteria,
- assumptions.

`BacktestConfig`

- date range,
- transaction-cost assumption,
- slippage assumption,
- position limit,
- evaluation split,
- benchmark,
- minimum observation count,
- treatment of missing prices or missing signal days,
- random seed if needed.

`BacktestResult`

- signal identifier,
- observation count,
- gross and net return,
- maximum drawdown,
- hit rate,
- turnover,
- cost impact,
- benchmark comparison,
- out-of-sample or walk-forward summary if configured,
- limitations,
- source artifact references.

## Research Workflow

1. Literature and existing thesis summaries define candidate signal families.
2. Agents propose bounded `SignalSpec` drafts.
3. Human review accepts or rejects candidate specs before backtesting.
4. Python validates accepted specs.
5. Python runs historical backtests and writes result artifacts.
6. Agents may interpret only compact backtest summaries.
7. Risk reviewer checks wording and overfitting risks before thesis use.

## Claim Rules

Allowed wording:

- `historical backtest prototype`
- `signal hypothesis`
- `risk-adjusted backtest result`
- `exploratory strategy evidence`
- `under the tested assumptions`

Disallowed wording:

- `guaranteed profitable`
- `live trading ready`
- `autonomous trader`
- `proof of alpha`
- `risk-free`

The thesis may discuss whether the deterministic signals have historical
predictive value. It must not claim that the agent system itself proves market
inefficiency or future profitability.
