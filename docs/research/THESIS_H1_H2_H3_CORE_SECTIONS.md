# Thesis H1-H2-H3 Core Sections

Dieses Artefakt macht aus Evidence Map, Core Results, Traceability Audit und kuratiertem Tabellen-/Figurenpaket eine thesis-ready Kernfassung fuer die drei empirischen Kapitel. Es berechnet keine neuen Kennzahlen und ersetzt keine manuelle Source Review.

## Counts

- Core sections: 3
- Scope: H1, H2, H3
- Use: BA-Draft, nicht finale Zitation

## Section Map

| section_id | hypothesis | chapter_title_de | method_evidence_ids | interpretation_evidence_ids | selected_tables | selected_figures | source_review_gate_de |
| --- | --- | --- | --- | --- | --- | --- | --- |
| core_section_h1 | H1 | H1: Prognosequalitaet | method_h1_brier_dm | interpretation_h1_bounded_advantage; interpretation_h1_broad_claim_not_proven | T2 | F1 | Draft nutzbar; finale Zitation erst nach Source Review mit Page-/Section-Notes und geprueften Claim-Support-Entscheiden. |
| core_section_h2 | H2 | H2: Tagesbasierte Ereignisfenster | method_h2_event_window | interpretation_h2_daily_response | T3 | F2 | Draft nutzbar; finale Zitation erst nach Source Review mit Page-/Section-Notes und geprueften Claim-Support-Entscheiden. |
| core_section_h3 | H3 | H3: Wallet-Timing-Diagnostik | method_h3_wallet_tiers; method_h3_granger_timing | interpretation_h3_top_tier_signal | T4 | F3 | Draft nutzbar; finale Zitation erst nach Source Review mit Page-/Section-Notes und geprueften Claim-Support-Entscheiden. |

## H1: Prognosequalitaet

**Evidence-IDs:** Methoden `method_h1_brier_dm`; Interpretationen `interpretation_h1_bounded_advantage; interpretation_h1_broad_claim_not_proven`.

**Literatur/Quellen:** `lit_brier_001; lit_dm_001; lit_emh_001; zotero_poly_002`.

**Deterministische Artefakte:** `data/results/thesis_h1_summary.csv; data/results/h1_poll_claim_readiness_summary.csv; data/results/h1_forecast_quality_synthesis.csv; data/results/h1_brier_scores.csv; data/results/h1_diebold_mariano.json; data/results/h1_poll_comparison_result_summary.csv; data/results/h1_claim_evidence_audit_summary.csv; data/results/thesis_core_results_table.csv; data/results/h1_poll_claim_readiness.png`.

**Tabelle/Figur:** Tabelle `T2`, Abbildung `F1`.

**Resultat:** H1 wird als zweigeteiltes Resultat geschrieben: begrenzter Support im Poll-Vergleichsscope mit `262/285 state-date rows (91.9%) lower Brier loss for Polymarket`; zugleich bleibt die breite Ueberlegenheitsbehauptung mit `7/9 aggregate rows support Polymarket; 3/9 majority-case rows support Polymarket; 0/9 broad rows prove the claim; 5 audit rows contradict the strong claim` nicht bewiesen.

**Interpretation:** Polymarket darf nur in klar definierten Vergleichsscopes als besser gestuetzt beschrieben werden; die Gesamtaussage bleibt gemischt.

**Limitation:** Wiederholte Tageszeilen und ein Wahlkontext begrenzen die Generalisierbarkeit. | Das volle State-Date-Panel und weitere Scopes bleiben Gegenbeispiele zur breiten Behauptung. | Die Evidenz mischt Tageszeilen, State-Outcomes, transformierte Poll-Signale und quellenspezifische Scopes. | Das volle Panel und weitere Scopes enthalten weiterhin Gegenbeispiele. | Die Evidenzeinheiten unterscheiden sich zwischen Tageszeilen, States und transformierten Poll-Scopes. | Vergleichseinheiten und Poll-Transformationen bleiben heterogen. | Die Darstellung ersetzt keine finale Quellenpruefung und keine Erweiterung auf mehrere Wahlen.

**Nicht schreiben:** Reaktionsgeschwindigkeitsbeweis | allgemeiner Marktueberlegenheitsbeweis | RCP-Wahrscheinlichkeitsaussage ohne dokumentierte Transformation | Polymarket ist immer besser | Mehrwahl-Beweis | kausale Erklaerung | allgemeine Ueberlegenheit | universelle Prognosedominanz

**Draft-Text:** Im H1-Kapitel wird Prognosequalitaet ueber Brier-Verlust und Diebold-Mariano-Vergleich beschrieben. Die Evidence-IDs `method_h1_brier_dm` und `interpretation_h1_bounded_advantage; interpretation_h1_broad_claim_not_proven` tragen die Aussage. Die Resultate werden kompakt in Tabelle T2 und Abbildung F1 gezeigt: ein begrenzter Poll-Vergleichsscope stuetzt Polymarket, waehrend die breite Ueberlegenheitsbehauptung nicht bewiesen ist.


## H2: Tagesbasierte Ereignisfenster

**Evidence-IDs:** Methoden `method_h2_event_window`; Interpretationen `interpretation_h2_daily_response`.

**Literatur/Quellen:** `lit_eventstudy_001; lit_emh_001; zotero_poly_001`.

**Deterministische Artefakte:** `data/results/h2_event_window_summary.csv; data/events_timeline_seed.csv; data/results/h2_event_window_rows.csv; data/results/thesis_h2_summary.csv; data/results/thesis_h2_event_window_car.png`.

**Tabelle/Figur:** Tabelle `T3`, Abbildung `F2`.

**Resultat:** H2 berichtet eine sichtbare Tagesbewegung im kuratierten Ereignisfenster: `evt_2024_07_13_trump_shooting 7.2 pp`. Das ist ein Tagesfensterbefund, kein Intraday-Speed-Test.

**Interpretation:** Die Ergebnisse zeigen oeffentliche Ereignisreaktionen im Tagesraster, aber keine minutengenaue oder kausale Informationsverarbeitung.

**Limitation:** Tagespreise koennen Intraday-Reaktionstiming nicht identifizieren. | Richtung und Groesse sind Ereignisfensterdiagnostik, keine Intraday-Kausalschaetzung. | Tagesdaten stuetzen keine Intraday-Reaktionsgeschwindigkeitsclaims. | Eventauswahl und Tagesfrequenz begrenzen die Interpretation. | Die Abbildung darf nicht als Intraday-Reaktionsnachweis gelesen werden.

**Nicht schreiben:** Intraday-Geschwindigkeitsaussage | post-hoc Ereignisauswahl | sofortige Marktreaktion | kausaler Ereignisbeweis

**Draft-Text:** Im H2-Kapitel werden vorab kuratierte oeffentliche Ereignisse mit fixen Tagesfenstern untersucht. Die Evidence-IDs `method_h2_event_window` und `interpretation_h2_daily_response` verweisen auf die deterministischen Artefakte. Tabelle T3 und Abbildung F2 zeigen Tagesbewegungen, nicht Intraday-Reaktionsgeschwindigkeit.


## H3: Wallet-Timing-Diagnostik

**Evidence-IDs:** Methoden `method_h3_wallet_tiers; method_h3_granger_timing`; Interpretationen `interpretation_h3_top_tier_signal`.

**Literatur/Quellen:** `zotero_poly_001; zotero_poly_005; zotero_poly_007; lit_granger_001`.

**Deterministische Artefakte:** `data/results/h3_wallet_distribution_inventory.json; data/results/h3_granger_results.csv; data/results/thesis_h3_summary.csv; data/results/h3_wallet_tiers.csv; data/results/h3_tiered_wallet_activity_daily.csv; data/results/h3_lead_lag_correlations.csv; data/results/thesis_h3_granger_pvalues.png`.

**Tabelle/Figur:** Tabelle `T4`, Abbildung `F3`.

**Resultat:** H3 berichtet die staerkste aktuelle Wallet-Timingdiagnostik fuer das oberste Tier: `tier_1_top_1pct lag 1 correlation 0.1858; tier_1_top_1pct lag 1 Granger p=0.0012; 1216 aligned rows`.

**Interpretation:** Top-tier Wallet-Aktivitaet ist eine predictive timing diagnostic, aber kein Beweis fuer Kausalitaet, private Information oder Tradeability.

**Limitation:** Die beobachteten Walletdaten sind BUY-only und quellengefiltert. | Taegliche Ausrichtung, Mehrfachtests und BUY-only-Extraktion begrenzen die Schlussstaerke. | Die Signalstaerke ist diagnostisch und braucht Sensitivitaets- und Mehrfachtest-Vorsicht. | BUY-only-Quelldaten, taegliche Ausrichtung und Mehrfachtest-Vorsicht begrenzen die Aussage. | BUY-only-Quelle, taegliche Aggregation und Mehrfachtests begrenzen die Aussage. | Granger-Diagnostik ist kein Kausalitaets-, private-information- oder Profitabilitaetsnachweis.

**Nicht schreiben:** willkuerliche Whale-Schwelle | identifizierte Private-Information-Wallets | Kausalitaetsbeweis | Private-Information-Beweis | Profitabilitaetsbeweis | Private-Information-Beweis | kausales Fehlverhalten | handelbare Strategie

**Draft-Text:** Im H3-Kapitel werden Wallet-Tiers dataset-relativ gebildet und mit Lead-Lag- sowie Granger-Diagnostik ausgewertet. Die Evidence-IDs `method_h3_wallet_tiers; method_h3_granger_timing` und `interpretation_h3_top_tier_signal` binden die Methode und Interpretation. Tabelle T4 und Abbildung F3 zeigen das Top-tier Timingmuster unter BUY-only-, Tagesfrequenz- und Mehrfachtest-Limitationen.


## Use Rule

Nutze diese Abschnitte als Schreibkern. Jede Methode und jede Interpretation bleibt an Evidence-ID, Quelle oder deterministisches Artefakt gebunden. Nutze wenige gute Tabellen/Figuren: T2/F1 fuer H1, T3/F2 fuer H2 und T4/F3 fuer H3. Keine Rohartefakt-Dumps, keine LLM-Metriken und keine finale Zitation ohne Source Review.
