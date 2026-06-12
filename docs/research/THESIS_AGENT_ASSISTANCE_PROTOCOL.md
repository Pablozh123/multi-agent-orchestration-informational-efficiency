# Thesis Agent Assistance Protocol

This protocol documents how future agents could improve the thesis pipeline after deterministic artifacts and human review gates are stable. It does not activate runtime agents, MCP tools, model routing, or LLM interpretation.

## Counts

- Protocol rows: 7
- Documentation-only rows: 6
- Deferred rows: 1

## Protocol Rows

| protocol_id | pipeline_step | current_artifact_boundary | allowed_inputs | allowed_outputs | audit_gate | activation_status |
| --- | --- | --- | --- | --- | --- | --- |
| agent_protocol_01_source_review | Manual source review | thesis_source_review_plan.csv; thesis_citation_review_packets.csv; literature_index.csv | source_id; evidence_id; required_check; source metadata; reviewer notes selected by a human | bounded checklist; missing-page-note warnings; no status changes | llm_audit_log entry with source_ids, evidence_ids, prompt hash, model, and output path | future_documentation_only |
| agent_protocol_02_evidence_reader | Evidence-to-prose drafting | thesis_evidence_map.csv; thesis_core_results_table.csv; thesis_curated_result_package.csv | one selected evidence_id plus bounded linked artifact summaries | short draft note tied to the same evidence_id and primary_artifact | llm_audit_log entry with evidence_id, artifact versions, prompt hash, model, and output path | future_documentation_only |
| agent_protocol_03_wording_guard | Claim and wording review | draft paragraph; thesis_evidence_map.csv; thesis_chapter_plan.csv | human-selected paragraph; linked evidence rows; chapter id | bounded overclaim warnings and safer wording suggestions | llm_audit_log entry with draft hash, evidence_ids checked, prompt hash, model, and warnings path | future_documentation_only |
| agent_protocol_04_table_figure_checker | Table and figure package review | thesis_table_figure_captions.csv; thesis_curated_result_package.csv | caption registry rows; selected draft caption text | missing-artifact, missing-limitation, or extra-raw-artifact warnings | llm_audit_log entry with package_ids, draft hash, prompt hash, model, and warnings path | future_documentation_only |
| agent_protocol_05_advisor_update | Advisor update summarisation | dozentenbericht_ba_thesis.md; THESIS_CONSOLIDATION.md; STATUS.md | existing advisor report; consolidation docs; project status snapshot | meeting bullets, open questions, and next-step checklist | llm_audit_log entry with artifact paths, prompt hash, model, and summary path | future_documentation_only |
| agent_protocol_06_monitor_review_helper | Monitor appendix review | bounded monitor review packets; human review notes; no wallet addresses by default | bounded case_id summaries; reviewed source notes; aggregate tier labels | appendix review summary and unresolved-evidence checklist | llm_audit_log entry with case_ids, artifact versions, prompt hash, model, and output path | future_documentation_only |
| agent_protocol_07_bounded_mcp | Bounded MCP summary interface | reviewed summary CSV/JSON only; max 50 rows unless justified | reviewed summary artifacts; explicit row limits; no raw SQL by default | bounded read-only summaries with row counts and artifact paths | separate approved goal, access contract tests, and llm_audit_log integration | future_deferred |

## Activation Rule

No row may be implemented until a separate approved goal exists, `llm_audit_log` integration is tested, allowed inputs are bounded, and blocked behaviours remain enforced. Agents must not calculate thesis metrics, read raw table dumps, expose wallet addresses by default, or touch order or trading paths.
