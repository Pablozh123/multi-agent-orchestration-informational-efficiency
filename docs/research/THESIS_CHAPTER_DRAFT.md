# Thesis Chapter Draft

Arbeitsfassung fuer die Bachelorarbeit. Dieser Text ist eine strukturierte Draft-Prosa aus der deterministischen Konsolidierungspipeline. Er ersetzt keine finale Quellenpruefung und fuehrt keine neuen Kennzahlen ein.

## 1. Einleitung und Forschungsfrage

Dezentrale Prognosemaerkte wie Polymarket verdichten Erwartungen vieler Marktteilnehmer zu handelbaren Wahrscheinlichkeiten. Die Bachelorarbeit untersucht, ob und in welchem Umfang solche Preise Informationen effizienter abbilden als traditionelle Prognose- und Umfragequellen. Informationelle Effizienz wird dabei nicht als direkt beobachtbare Eigenschaft behandelt, sondern ueber drei deterministische Proxy-Ebenen operationalisiert: Prognosequalitaet (H1), Ereignisfenster-Reaktionen (H2) und walletbasierte Timing-Diagnostik (H3). Die methodische Grundregel lautet, dass statistische Kennzahlen ausschliesslich in Python berechnet werden und jede Interpretation auf ein Artefakt oder eine Evidence-ID zurueckgefuehrt werden muss. Zentrale Einstiegsartefakte sind `data/results/thesis_evidence_map.csv` und `data/results/thesis_core_results_table.csv`.

Die leitende Forschungsfrage lautet: In welchem Ausmass zeigen Polymarket-Preise im US-Wahlkontext 2024 eine hoehere Prognosequalitaet, eine sichtbare Reaktion auf oeffentliche Ereignisse und fruehe walletbasierte Signalstrukturen im Vergleich zu traditionellen Prognosequellen? Die Antwort wird bewusst begrenzt formuliert: Die Arbeit kann Evidenz fuer bestimmte diagnostische Muster liefern, aber keine universelle Aussage ueber alle Prognosemaerkte, keine Intraday-Geschwindigkeitsbehauptung und keine Aussage ueber handelbare Gewinne.

## 2. Theorie und Literatur

Der theoretische Rahmen stuetzt sich auf die Idee informationeller Markteffizienz und auf Literatur zu Prognosemaerkten, Vorhersageguete, Ereignisstudien und walletbasierter Marktbeobachtung. Die aktuelle Quellensteuerung liegt in `data/results/thesis_citation_readiness.csv`. Diese Datei zeigt, dass 11 Quellen vor finaler Zitation noch vollstaendig geprueft werden muessen, waehrend eine Candidate-Quelle nicht fuer thesis-facing Claims verwendet werden darf. Fuer H1 sind `lit_brier_001`, `lit_dm_001` und `zotero_poly_002` die wesentlichen Quellenanker. Fuer H2 wird die Event-Study-Logik ueber `lit_eventstudy_001` gestuetzt. Fuer H3 dienen `lit_granger_001`, `zotero_poly_001` und `zotero_poly_005` als Rahmen fuer Timingdiagnostik und die vorsichtige Interpretation von Walletdaten.

Wichtig ist die Trennung zwischen Literaturrahmen und empirischem Befund. Literatur motiviert die Methode und begrenzt die Sprache, ersetzt aber keine lokalen Ergebnisartefakte. Deshalb sind Quellen mit Status `skimmed` fuer die Draft-Struktur nutzbar, aber vor finaler Abgabe noch nicht automatisch zitierfertig. Die Literaturmap und die Evidence-Map verhindern, dass spaeter unbelegte Theorieaussagen oder nicht gepruefte Quellen in die Thesis uebernommen werden.

## 3. Daten und Methodik

Die empirische Pipeline folgt dem Prinzip: Datenvalidierung, deterministische Analyse, danach erst Interpretation. H1 bewertet Prognosequalitaet ueber Brier-Verlust und den Diebold-Mariano-Vergleich vorberechneter Verlustreihen. Primaere Artefakte sind `data/results/thesis_h1_summary.csv` sowie `data/results/h1_brier_scores.csv` und `data/results/h1_diebold_mariano.json`. RCP wird nicht als native Wahrscheinlichkeitsprognose genutzt, solange keine dokumentierte Transformation vorliegt.

H2 nutzt vorab kuratierte Ereignisse und feste Tagesfenster. Die Methode ist in `data/results/h2_event_window_summary.csv` und `data/events_timeline_seed.csv` abgebildet. Ereignisse werden nicht nach Sichtung der Marktreaktion hinzugefuegt oder entfernt. Die H2-Aussagen bleiben auf Tagesdaten beschraenkt.

H3 bildet Walletgruppen nicht ueber fixe USD-Schwellen, sondern ueber dataset-relative Tiers. Die zugehoerigen Artefakte sind `data/results/h3_wallet_distribution_inventory.json`, `data/results/h3_wallet_tiers.csv`, `data/results/h3_lead_lag_correlations.csv` und `data/results/h3_granger_results.csv`. Die Granger-Ausgaben werden als predictive timing diagnostics gelesen, nicht als Kausalitaetsbeweis. Die wichtigste methodische Limitation bleibt die BUY-only-Quelle und die taegliche Aggregation.

## 4. H1: Prognosequalitaet

Das zentrale H1-Ergebnis lautet: Im begrenzten Poll-Vergleichsscope unterstuetzen die Artefakte eine Polymarket-Staerke. Der aktuelle Kernwert ist 262/285 State-Date-Zeilen (91.9%) mit niedrigerem Brier-Verlust fuer Polymarket. Die Aussage stuetzt sich auf `data/results/h1_poll_claim_readiness_summary.csv` und die Evidence-ID `interpretation_h1_bounded_advantage`. Damit ist eine begrenzte, scope-spezifische Polymarket-Staerke sichtbar.

Gleichzeitig ist die breite Ueberlegenheitsbehauptung nicht gedeckt. Der zugehoerige Kernwert lautet: 7/9 Aggregate-Zeilen unterstuetzen Polymarket; 3/9 Majority-Case-Zeilen unterstuetzen Polymarket; 0/9 Broad-Claim-Zeilen beweisen die breite Aussage; 5 Audit-Zeilen widersprechen der starken Aussage. Diese Grenze ist fuer die Thesis zentral, weil sie verhindert, dass ein einzelner unterstuetzter Scope zu einer allgemeinen Ueberlegenheitsbehauptung ausgedehnt wird. Die korrekte H1-Interpretation ist deshalb: Polymarket zeigt in definierten spaeten und kompatiblen Vergleichsfenstern bessere Brier-Verluste, aber die Gesamtevidenz bleibt gemischt und kontextabhaengig.

Empfohlene Darstellung: Tabelle `data/results/thesis_core_results_table.csv` und Abbildung `data/results/h1_poll_claim_readiness.png`. Die Limitation ist explizit zu nennen: unterschiedliche Vergleichseinheiten, transformierte Poll-Signale und wiederholte Tageszeilen sind keine unabhaengigen Wahlen.

## 5. H2: Ereignisfenster

Fuer H2 zeigt die aktuelle Kernzeile: Die groesste primaere Tagesfensterbewegung liegt im Trump-Shooting-Fenster. Der Wert ist evt_2024_07_13_trump_shooting 7.2 pp. Quelle ist `data/results/h2_event_window_summary.csv`, gestuetzt durch `interpretation_h2_daily_response`. Das Ergebnis zeigt, dass Polymarket-Preise um kuratierte oeffentliche Ereignisse sichtbare Tagesbewegungen aufweisen.

Die Interpretation bleibt jedoch eine Tagesfensterdiagnostik. Aus diesen Artefakten darf nicht abgeleitet werden, dass Polymarket innerhalb von Minuten oder Stunden schneller reagiert als andere Quellen. Fuer eine solche Aussage waeren validierte Intraday- oder Orderbuchdaten noetig. In der Thesis sollte H2 daher als Evidenz fuer beobachtbare Tagesreaktionen geschrieben werden, nicht als Beweis fuer unmittelbare Informationsverarbeitung.

Empfohlene Darstellung: Tabelle `data/results/h2_event_window_summary.csv` und Abbildung `data/results/thesis_h2_event_window_car.png`.

## 6. H3: Wallet-Timing

Das zentrale H3-Ergebnis lautet: Das oberste Wallet-Tier zeigt die klarste aktuelle Timingdiagnostik. Der aktuelle Kernwert ist tier_1_top_1pct lag 1 Korrelation 0.1858; tier_1_top_1pct lag 1 Granger p=0.0012; 1216 alignierte Zeilen. Die Aussage stuetzt sich auf `data/results/thesis_h3_summary.csv`, `data/results/h3_granger_results.csv` und `data/results/h3_lead_lag_correlations.csv`. H3 zeigt damit eine auffaellige top-tier Timingdiagnostik, aber keinen Kausalitaetsnachweis und keine Aussage ueber private Informationen oder Profitabilitaet.

Fuer die Thesis ist die Formulierung entscheidend. Erlaubt ist: dataset-relative Wallet-Tiers zeigen unter taeglicher Aggregation Timingmuster, die als predictive diagnostics gelesen werden koennen. Nicht erlaubt ist: identifizierte Wallets belegen Fehlverhalten, private Informationsnutzung oder eine handelbare Strategie. Die Limitationen BUY-only, taegliche Frequenz, Mehrfachtests und moegliche Upstream-Filter gehoeren direkt in den Ergebnistext.

Empfohlene Darstellung: Tabelle `data/results/thesis_h3_summary.csv` und Abbildung `data/results/thesis_h3_granger_pvalues.png`.

## 7. Erweiterungen: Monitor und Schweizer Abstimmung

Der Monitor-Prototyp ist nuetzlich als Workflow- und Appendix-Material, aber nicht als empirischer Beweis. Kernwert: 3 Review-Faelle; 1 hoch; 2 mittel; source_check_pending=3. Die zugehoerigen Artefakte bleiben reviewgebunden und sind keine thesis-facing Evidenz fuer Ursachen, Regelverstoesse, Marktineffizienz, Handelbarkeit oder Gewinne.

Der Schweizer Abstimmungstrack bleibt bis zum offiziellen Resultat beschreibend. Kernwert: 31 Snapshots; aktuell SRG/gfs.bern Polymarket-Yes 21.5%, Poll-Yes 45.0%, Raw-Gap -23.5 pp. Die aktuelle Figur `data/results/swiss_referendum_10mio_efficiency.png` darf als laufender Poll-Proxy-Vergleich genutzt werden, aber nicht als finaler Effizienzbefund. Poll-Anteile sind keine echten Modellwahrscheinlichkeiten.

## 8. Diskussion und Fazit

Die bisherigen Ergebnisse sprechen fuer eine differenzierte Antwort. H1 liefert in einem abgegrenzten Vergleichsscope starke Unterstuetzung fuer Polymarket, waehrend eine breite Ueberlegenheitsbehauptung nicht bewiesen ist. H2 zeigt sichtbare Tagesbewegungen um kuratierte Ereignisse, ohne Intraday-Aussagen zu erlauben. H3 zeigt eine top-tier Wallet-Timingdiagnostik, die als fruehes Signal interpretiert werden kann, aber keine Kausalitaet, keine private Informationsnutzung und keine Profitabilitaet belegt.

Das Fazit sollte deshalb nicht lauten, dass Polymarket generell effizienter ist als traditionelle Prognosequellen. Praeziser ist: Die Arbeit findet in klar definierten Ausschnitten Hinweise auf bessere Prognosequalitaet, sichtbare Ereignisreaktionen und walletbasierte Timingmuster. Gleichzeitig bleiben Datenfrequenz, Quellenstatus, Poll-Transformation, BUY-only Walletdaten und fehlende finale Swiss-Auswertung zentrale Limitationen.

## 9. Agenten-Pipeline als Ausblick

Die Agenten-Pipeline ist ein spaeterer Arbeitsausblick, nicht Teil des aktiven empirischen Kerns. Sinnvolle Agentenrollen waeren Evidence Reader, Citation Checker, Wording Guard und Monitor-Review-Helfer. Alle Rollen duerfen nur bounded summaries lesen, muessen in `llm_audit_log` protokolliert werden und duerfen keine Kennzahlen berechnen. MCP-Zugriff waere erst nach separatem Ziel, Tests, Access Contract und Audit-Logging vertretbar. Order- oder Tradingpfade bleiben ausgeschlossen.
