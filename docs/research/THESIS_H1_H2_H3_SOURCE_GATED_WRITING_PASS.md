# H1-H2-H3 Source-Gated Writing Pass

Dieses Dokument ist der naechste BA-Schreibpass fuer die empirischen Kernkapitel. Es baut ausschliesslich auf dem bounded chapter draft, der Source Coverage und den deterministischen Artefakten auf. Es liest keine Quelleninhalte, erzeugt keine neuen Kennzahlen und ersetzt keine finale Quellenreview.

## Counts

- Writing pass rows: 3

- Bounded draft ready rows: 3

- Final submission ready rows: 0

- Source coverage gap rows: 0

## H1: Prognosequalitaet

Methoden: `method_h1_brier_dm`

Interpretationen: `interpretation_h1_bounded_advantage; interpretation_h1_broad_claim_not_proven`

Literatur: `lit_brier_001; lit_dm_001; lit_emh_001; zotero_poly_002`

Tabellen/Figuren: `T2` / `F1`

Source-Coverage: 10 Links; 4 eindeutige Source-IDs; 0 Coverage-Gaps

### Source-gated Draft

H1: Prognosequalitaet

Source-gated Schreibpass: Der Abschnitt bleibt an Source Coverage, deterministische Artefakte und finale Source-Review-Gates gebunden.

Im Abschnitt `H1: Prognosequalitaet` wird H1 ueber die Methode `method_h1_brier_dm` aufgebaut. Die Methode ist an die Literatur-IDs `lit_brier_001; lit_dm_001; lit_emh_001; zotero_poly_002` und an deterministische Artefakte gebunden: `data/results/thesis_h1_summary.csv`; `data/results/h1_poll_claim_readiness_summary.csv`; `data/results/h1_forecast_quality_synthesis.csv`; `data/results/h1_brier_scores.csv`; plus 5 weitere gemappte Artefakte. Die Interpretation wird noch nicht erweitert; sie bleibt an die Evidence-IDs `interpretation_h1_bounded_advantage; interpretation_h1_broad_claim_not_proven` und an das Source-Review-Gate gebunden.

Der Resultatabschnitt nutzt ausschliesslich den vorbereiteten Textseed: H1 wird als zweigeteiltes Resultat geschrieben: begrenzter Support im Poll-Vergleichsscope mit `262/285 state-date rows (91.9%) lower Brier loss for Polymarket`; zugleich bleibt die breite Ueberlegenheitsbehauptung mit `7/9 aggregate rows support Polymarket; 3/9 majority-case rows support Polymarket; 0/9 broad rows prove the claim; 5 audit rows contradict the strong claim` nicht bewiesen. Diese Aussage ist das thesis-ready Ergebnis fuer H1 und wird nicht durch neue Kennzahlen, Rohartefakt-Dumps oder zusaetzliche Tabellen erweitert.

Die Interpretation fuer H1 lautet begrenzt: Polymarket darf nur in klar definierten Vergleichsscopes als besser gestuetzt beschrieben werden; die Gesamtaussage bleibt gemischt. Die zentrale Limitation ist: Wiederholte Tageszeilen und ein Wahlkontext begrenzen die Generalisierbarkeit. Diese Grenze verhindert Universal-, Intraday-, Kausalitaets-, Private-Information-, Profitabilitaets- oder Tradeability-Claims.

Die Ergebnisdarstellung fuer H1 nutzt nur die kuratierten Package-Items T2 (tab:t2): H1: Prognosequalitaet und Poll-Vergleich -> data/results/thesis_core_results_table.csv; Limitation: Vergleichseinheiten und Poll-Transformationen bleiben heterogen. | F1 (fig:f1): H1: Claim-Readiness des Poll-Vergleichs -> data/results/h1_poll_claim_readiness.png; Limitation: Die Darstellung ersetzt keine finale Quellenpruefung und keine Erweiterung auf mehrere Wahlen. Caption, Artefaktpfad und Limitation werden aus der Caption Registry uebernommen. Damit bleibt die Darstellung kompakt: wenige gute Tabellen und Figuren statt vieler Rohartefakte.

Das Zitationsgate fuer H1 bleibt sichtbar: H1: 10 Source-Review-Zeilen im Ledger; 10 pending; 0 final-ready. Keine finale Zitation ohne abgeschlossene manuelle Review. Vor finaler Zitation Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use je Quelle dokumentieren. Im Handoff stehen 10 Source-Review-Zeilen, davon 10 pending und 0 final-ready. Der Source-Coverage-Audit weist 10 Quellenlinks, 4 eindeutige Source-IDs und 0 Coverage-Gaps fuer dieses Kapitel aus. Keine finale Zitation und keine Quellenstatus-Hochstufung erfolgen aus diesem Draft.

Die Agenten-Grenze fuer H1 bleibt Future Work: Agentenstatus bleibt `future_documentation_only`: keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken; spaeter nur mit separatem Goal, Tests, bounded inputs, max 50 rows und llm_audit_log. Der Abschnitt darf nur als Pipeline-Ausblick formuliert werden; keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken, kein Rohdaten-Prompt und keine Trading-Pfade.

Schreibgate: Dieser Abschnitt ist bounded-draft-ready, aber nicht final-submission-ready. Finale Zitation bleibt vom Source Review mit Page-/Section-Notes abhaengig.

Nicht schreiben: Reaktionsgeschwindigkeitsbeweis | allgemeiner Marktueberlegenheitsbeweis | RCP-Wahrscheinlichkeitsaussage ohne dokumentierte Transformation | Polymarket ist immer besser | Mehrwahl-Beweis | kausale Erklaerung | allgemeine Ueberlegenheit | universelle Prognosedominanz

## H2: Tagesbasierte Ereignisfenster

Methoden: `method_h2_event_window`

Interpretationen: `interpretation_h2_daily_response`

Literatur: `lit_eventstudy_001; lit_emh_001; zotero_poly_001`

Tabellen/Figuren: `T3` / `F2`

Source-Coverage: 5 Links; 3 eindeutige Source-IDs; 0 Coverage-Gaps

### Source-gated Draft

H2: Tagesbasierte Ereignisfenster

Source-gated Schreibpass: Der Abschnitt bleibt an Source Coverage, deterministische Artefakte und finale Source-Review-Gates gebunden.

Im Abschnitt `H2: Tagesbasierte Ereignisfenster` wird H2 ueber die Methode `method_h2_event_window` aufgebaut. Die Methode ist an die Literatur-IDs `lit_eventstudy_001; lit_emh_001; zotero_poly_001` und an deterministische Artefakte gebunden: `data/results/h2_event_window_summary.csv`; `data/events_timeline_seed.csv`; `data/results/h2_event_window_rows.csv`; `data/results/thesis_h2_summary.csv`; plus 1 weiteres gemapptes Artefakt. Die Interpretation wird noch nicht erweitert; sie bleibt an die Evidence-IDs `interpretation_h2_daily_response` und an das Source-Review-Gate gebunden.

Der Resultatabschnitt nutzt ausschliesslich den vorbereiteten Textseed: H2 berichtet eine sichtbare Tagesbewegung im kuratierten Ereignisfenster: `evt_2024_07_13_trump_shooting 7.2 pp`. Das ist ein Tagesfensterbefund, kein Intraday-Speed-Test. Diese Aussage ist das thesis-ready Ergebnis fuer H2 und wird nicht durch neue Kennzahlen, Rohartefakt-Dumps oder zusaetzliche Tabellen erweitert.

Die Interpretation fuer H2 lautet begrenzt: Die Ergebnisse zeigen oeffentliche Ereignisreaktionen im Tagesraster, aber keine minutengenaue oder kausale Informationsverarbeitung. Die zentrale Limitation ist: Tagespreise koennen Intraday-Reaktionstiming nicht identifizieren. Diese Grenze verhindert Universal-, Intraday-, Kausalitaets-, Private-Information-, Profitabilitaets- oder Tradeability-Claims.

Die Ergebnisdarstellung fuer H2 nutzt nur die kuratierten Package-Items T3 (tab:t3): H2: Tagesbasierte Ereignisfenster um kuratierte oeffentliche Ereignisse -> data/results/h2_event_window_summary.csv; Limitation: Eventauswahl und Tagesfrequenz begrenzen die Interpretation. | F2 (fig:f2): H2: Tagesbewegungen in kuratierten Ereignisfenstern -> data/results/thesis_h2_event_window_car.png; Limitation: Die Abbildung darf nicht als Intraday-Reaktionsnachweis gelesen werden. Caption, Artefaktpfad und Limitation werden aus der Caption Registry uebernommen. Damit bleibt die Darstellung kompakt: wenige gute Tabellen und Figuren statt vieler Rohartefakte.

Das Zitationsgate fuer H2 bleibt sichtbar: H2: 5 Source-Review-Zeilen im Ledger; 5 pending; 0 final-ready. Keine finale Zitation ohne abgeschlossene manuelle Review. Vor finaler Zitation Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use je Quelle dokumentieren. Im Handoff stehen 5 Source-Review-Zeilen, davon 5 pending und 0 final-ready. Der Source-Coverage-Audit weist 5 Quellenlinks, 3 eindeutige Source-IDs und 0 Coverage-Gaps fuer dieses Kapitel aus. Keine finale Zitation und keine Quellenstatus-Hochstufung erfolgen aus diesem Draft.

Die Agenten-Grenze fuer H2 bleibt Future Work: Agentenstatus bleibt `future_documentation_only`: keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken; spaeter nur mit separatem Goal, Tests, bounded inputs, max 50 rows und llm_audit_log. Der Abschnitt darf nur als Pipeline-Ausblick formuliert werden; keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken, kein Rohdaten-Prompt und keine Trading-Pfade.

Schreibgate: Dieser Abschnitt ist bounded-draft-ready, aber nicht final-submission-ready. Finale Zitation bleibt vom Source Review mit Page-/Section-Notes abhaengig.

Nicht schreiben: Intraday-Geschwindigkeitsaussage | post-hoc Ereignisauswahl | sofortige Marktreaktion | kausaler Ereignisbeweis

## H3: Wallet-Timing-Diagnostik

Methoden: `method_h3_wallet_tiers; method_h3_granger_timing`

Interpretationen: `interpretation_h3_top_tier_signal`

Literatur: `zotero_poly_001; zotero_poly_005; zotero_poly_007; lit_granger_001`

Tabellen/Figuren: `T4` / `F3`

Source-Coverage: 8 Links; 4 eindeutige Source-IDs; 0 Coverage-Gaps

### Source-gated Draft

H3: Wallet-Timing-Diagnostik

Source-gated Schreibpass: Der Abschnitt bleibt an Source Coverage, deterministische Artefakte und finale Source-Review-Gates gebunden.

Im Abschnitt `H3: Wallet-Timing-Diagnostik` wird H3 ueber die Methode `method_h3_wallet_tiers; method_h3_granger_timing` aufgebaut. Die Methode ist an die Literatur-IDs `zotero_poly_001; zotero_poly_005; zotero_poly_007; lit_granger_001` und an deterministische Artefakte gebunden: `data/results/h3_wallet_distribution_inventory.json`; `data/results/h3_granger_results.csv`; `data/results/thesis_h3_summary.csv`; `data/results/h3_wallet_tiers.csv`; plus 3 weitere gemappte Artefakte. Die Interpretation wird noch nicht erweitert; sie bleibt an die Evidence-IDs `interpretation_h3_top_tier_signal` und an das Source-Review-Gate gebunden.

Der Resultatabschnitt nutzt ausschliesslich den vorbereiteten Textseed: H3 berichtet die staerkste aktuelle Wallet-Timingdiagnostik fuer das oberste Tier: `tier_1_top_1pct lag 1 correlation 0.1858; tier_1_top_1pct lag 1 Granger p=0.0012; 1216 aligned rows`. Diese Aussage ist das thesis-ready Ergebnis fuer H3 und wird nicht durch neue Kennzahlen, Rohartefakt-Dumps oder zusaetzliche Tabellen erweitert.

Die Interpretation fuer H3 lautet begrenzt: Top-tier Wallet-Aktivitaet ist eine predictive timing diagnostic, aber kein Beweis fuer Kausalitaet, private Information oder Tradeability. Die zentrale Limitation ist: Die beobachteten Walletdaten sind BUY-only und quellengefiltert. Diese Grenze verhindert Universal-, Intraday-, Kausalitaets-, Private-Information-, Profitabilitaets- oder Tradeability-Claims.

Die Ergebnisdarstellung fuer H3 nutzt nur die kuratierten Package-Items T4 (tab:t4): H3: Wallet-Tiers und Timingdiagnostik -> data/results/thesis_h3_summary.csv; Limitation: BUY-only-Quelle, taegliche Aggregation und Mehrfachtests begrenzen die Aussage. | F3 (fig:f3): H3: Granger-Diagnostik nach Wallet-Tier und Lag -> data/results/thesis_h3_granger_pvalues.png; Limitation: Granger-Diagnostik ist kein Kausalitaets-, private-information- oder Profitabilitaetsnachweis. Caption, Artefaktpfad und Limitation werden aus der Caption Registry uebernommen. Damit bleibt die Darstellung kompakt: wenige gute Tabellen und Figuren statt vieler Rohartefakte.

Das Zitationsgate fuer H3 bleibt sichtbar: H3: 8 Source-Review-Zeilen im Ledger; 8 pending; 0 final-ready. Keine finale Zitation ohne abgeschlossene manuelle Review. Vor finaler Zitation Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use je Quelle dokumentieren. Im Handoff stehen 8 Source-Review-Zeilen, davon 8 pending und 0 final-ready. Der Source-Coverage-Audit weist 8 Quellenlinks, 4 eindeutige Source-IDs und 0 Coverage-Gaps fuer dieses Kapitel aus. Keine finale Zitation und keine Quellenstatus-Hochstufung erfolgen aus diesem Draft.

Die Agenten-Grenze fuer H3 bleibt Future Work: Agentenstatus bleibt `future_documentation_only`: keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken; spaeter nur mit separatem Goal, Tests, bounded inputs, max 50 rows und llm_audit_log. Der Abschnitt darf nur als Pipeline-Ausblick formuliert werden; keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken, kein Rohdaten-Prompt und keine Trading-Pfade.

Schreibgate: Dieser Abschnitt ist bounded-draft-ready, aber nicht final-submission-ready. Finale Zitation bleibt vom Source Review mit Page-/Section-Notes abhaengig.

Nicht schreiben: willkuerliche Whale-Schwelle | identifizierte Private-Information-Wallets | Kausalitaetsbeweis | Private-Information-Beweis | Profitabilitaetsbeweis | kausales Fehlverhalten | handelbare Strategie

## Use Rule

Nutze diesen Schreibpass als unmittelbare Grundlage fuer die H1-H2-H3-Ergebniskapitel. Jede Methode und Interpretation bleibt an Evidence IDs, Literatur-IDs, deterministische Artefakte, wenige gute Tabellen/Figuren, Limitationen und Source Review Gates gebunden. Keine finale Zitation, keine Rohartefakt-Dumps, keine neuen Kennzahlen, keine Quellenstatus-Hochstufung, keine Runtime-Agenten, kein MCP, kein Model Routing und keine LLM-Metriken.
