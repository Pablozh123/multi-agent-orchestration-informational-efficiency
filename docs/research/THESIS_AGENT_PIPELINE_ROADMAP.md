# Thesis Agent Pipeline Roadmap

This document is documentation-only. It does not implement, activate, or invoke agents, MCP tools, model routing, autonomous collectors, or trading paths.

## Guardrails

- Deterministic Python remains responsible for all metrics.
- Future LLM calls require `llm_audit_log` logging before use.
- No raw table dumps enter prompts.
- Future tool outputs stay bounded to at most 50 rows unless explicitly reviewed.
- Wallet-address exposure is blocked by default.
- Order placement, order cancellation, authenticated trading channels, and trading credentials stay out of scope.

## Roadmap Stages

| stage_id | stage_name | agent_role | allowed_inputs | allowed_outputs | blocked_actions | required_gate_before_activation | audit_requirement | implementation_status | thesis_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agent_stage_00_disabled_runtime | Keep runtime disabled | No runtime thesis agent is active. | None | Static architecture notes only | agent execution; MCP implementation; model routing; metric calculation | Deterministic thesis package committed and reviewed. | No LLM call before llm_audit_log integration exists. | current_required_state | Protects the deterministic thesis core. |
| agent_stage_01_evidence_reader | Evidence reader | Summarise existing evidence-map rows for drafting. | thesis_evidence_map.csv; thesis_core_results_table.csv; thesis_curated_result_package.csv | short prose notes tied to evidence_id values | reading raw tables; computing metrics; changing evidence rows | Bounded prompt template and llm_audit_log write path reviewed. | Log prompt hash, model, evidence ids, artifact versions, and output path. | future_documentation_only | Speeds drafting without weakening traceability. |
| agent_stage_02_citation_checker | Citation readiness checker | Flag sources that need review before final citation wording. | thesis_citation_readiness.csv; literature_index.csv | review checklist; missing-source warnings | promoting source status automatically; inventing citations; citing candidate sources as evidence | Human-readable source-status rules and no-write default reviewed. | Log source ids read and checklist output. | future_documentation_only | Keeps literature mapping honest before final writing. |
| agent_stage_03_wording_guard | Interpretation wording guard | Compare draft paragraphs with allowed and blocked wording. | draft paragraph; thesis_evidence_map.csv; thesis_chapter_plan.csv | bounded wording warnings and suggested safer phrasing | adding new claims; relaxing blocked wording; replacing deterministic artifacts | Draft text input must be manually selected and logged. | Log draft hash, evidence ids checked, and warnings. | future_documentation_only | Reduces overclaiming in H1-H3 discussion. |
| agent_stage_04_monitor_review_helper | Monitor review helper | Summarise source-check notes for monitor review packets after human review exists. | bounded monitor review packets; human status worksheets; source URLs | review-note summary; unresolved evidence checklist | accessing wallet addresses by default; declaring misconduct; creating trading signals | Human review worksheet contains reviewed statuses and source URLs. | Log case ids, artifact versions, and blocked-claim checks. | future_documentation_only | Could help appendix review without changing empirical results. |
| agent_stage_05_bounded_mcp_summaries | Bounded MCP summary tools | Expose reviewed summary artifacts to future assistants. | reviewed summary CSV/JSON files only; max 50 rows unless justified | bounded read-only summaries | raw SQL; raw monitor rows; wallet-address exposure by default; order or trading paths | Separate approved goal, tests, access contract, and llm_audit_log integration. | Log tool name, row count, artifact path, and user-visible output. | future_deferred | Creates a safe interface after the thesis core is stable. |

## Status

- Current required disabled stages: 1
- Future documentation-only stages: 4
- Future deferred stages: 1
