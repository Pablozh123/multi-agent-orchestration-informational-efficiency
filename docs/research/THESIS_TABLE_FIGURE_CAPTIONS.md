# Thesis Table And Figure Captions

This register turns the curated result package into thesis-ready table and figure captions. It uses only the selected core package rows and keeps source notes, interpretation notes, and limitations separate.

## Counts

- Total caption rows: 10
- Core table captions: 5
- Core figure captions: 4

## Caption Register

| package_id | package_type | thesis_label | caption_de | primary_artifact | recommended_placement | thesis_readiness |
| --- | --- | --- | --- | --- | --- | --- |
| A1 | appendix_artifact | app:a1 | Deferred agent pipeline design | docs/research/THESIS_CONSOLIDATION.md | appendix_or_future_work | future_work_deferred |
| F1 | figure | fig:f1 | H1: Claim-Readiness des Poll-Vergleichs | data/results/h1_poll_claim_readiness.png | main_text | thesis_facing_ready |
| F2 | figure | fig:f2 | H2: Tagesbewegungen in kuratierten Ereignisfenstern | data/results/thesis_h2_event_window_car.png | main_text | thesis_facing_ready |
| F3 | figure | fig:f3 | H3: Granger-Diagnostik nach Wallet-Tier und Lag | data/results/thesis_h3_granger_pvalues.png | main_text | thesis_facing_ready |
| F4 | figure | fig:f4 | Schweizer 10-Millionen-Initiative: laufender Poll-Proxy-Vergleich | data/results/swiss_referendum_10mio_final_case_study.png | discussion_bounded_final_case | post_result_mapped_bounded |
| T1 | table | tab:t1 | Methoden-, Quellen- und Evidenzkarte der Thesis | data/results/thesis_evidence_map.csv | main_text | thesis_facing_ready |
| T2 | table | tab:t2 | H1: Prognosequalitaet und Poll-Vergleich | data/results/thesis_core_results_table.csv | main_text | thesis_facing_ready |
| T3 | table | tab:t3 | H2: Tagesbasierte Ereignisfenster um kuratierte oeffentliche Ereignisse | data/results/h2_event_window_summary.csv | main_text | thesis_facing_ready |
| T4 | table | tab:t4 | H3: Wallet-Tiers und Timingdiagnostik | data/results/thesis_h3_summary.csv | main_text | thesis_facing_ready |
| T5 | table | tab:t5 | Statusgrenzen fuer Monitor-Prototyp und Schweizer Abstimmungstrack | data/results/thesis_core_results_table.csv | appendix_or_discussion | mixed_appendix_and_bounded |

## Usage Rule

Use these captions with the exact linked artifacts. Do not replace the curated package with additional raw result files unless the evidence map and chapter plan are updated first.
