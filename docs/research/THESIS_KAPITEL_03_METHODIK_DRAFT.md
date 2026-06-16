# Kapitel 3 — Daten und Methodik (Entwurf)

Status: bounded-draft-ready. Inhaltlich schreibbar, finale Zitation erst nach
manuellem Quellen-Review. Schweizer Orthografie (ss, keine scharfen s).

Zitier-Hinweis: Die Schlüssel `\citep{...}` entsprechen den `source_id` aus
`data/literature/literature_index.csv`. Vor Abgabe durch die Better-BibTeX-Keys
ersetzen. Quellen mit Status `skimmed`/`pending` sind hier Platzhalter und dürfen
erst nach Seiten-/Abschnittsnotiz im Ledger final zitiert werden.

Kapitelbindung: `ch_03_data_method`. Evidence-IDs: `method_h1_brier_dm`,
`method_h2_event_window`, `method_h3_wallet_tiers`, `method_h3_granger_timing`.
Tabelle: T1 (Daten- und Quelleninventar).

---

## 3.1 Forschungsdesign: deterministischer Kern vor Interpretation

Die Arbeit prüft informationelle Effizienz nicht als direkt beobachtbare
Eigenschaft, sondern über drei reproduzierbare Proxy-Tests: Prognosequalität (H1),
Ereignisreaktion (H2) und Wallet-Timing (H3). Diese Operationalisierung folgt dem
Effizienzbegriff der Markteffizienzhypothese \citep{lit_emh_001} und überträgt ihn
auf einen dezentralen Prognosemarkt, dessen Preispfad als primäre Zeitreihe
behandelt wird.

Methodisch gilt eine strikte Trennung: Alle statistischen Kennzahlen werden
deterministisch in Python berechnet, versioniert und als Artefakt (CSV, JSON, PNG)
abgelegt. Sprachmodelle oder Agenten berechnen keine Metriken; sie dürfen
ausschliesslich bereits berechnete, begrenzte Ergebnisse interpretieren, und auch
das erst nach dokumentierter Freigabe und Audit-Protokollierung. Diese Reihenfolge
— Datenvalidierung, deterministische Analyse, danach Interpretation — sichert
Nachvollziehbarkeit und schützt vor versteckten Berechnungen im Fliesstext.

## 3.2 Datenbasis

Die empirische Basis liegt in einer lokalen SQLite-Datenbank (`data/thesis.db`).
Tabelle T1 fasst Quellen, Zeilenzahlen und bekannte Einschränkungen zusammen; das
Inventar ist deterministisch aus `data/results/thesis_evidence_map.csv` und dem
Datenbestand abgeleitet.

| Quelle | Tabelle | Umfang | Rolle / Einschränkung |
| --- | --- | --- | --- |
| Polymarket CLOB/Gamma | `polymarket_prices` | 307 Tagespreise, 2024-01-05 bis 2024-11-06 | Primäre Marktzeitreihe |
| FiveThirtyEight | `poll_forecasts` | 245 Zeilen | Vergleichsquelle H1 (native Wahrscheinlichkeiten) |
| RealClearPolitics | `poll_forecasts` | 0 Zeilen | Standardmässig ausgeschlossen (siehe unten) |
| On-Chain-Wallets (Dune/Polygon) | `whale_trades` | 25'113 Zeilen | H3; nur BUY, quellseitiger Mindestbetrag 10'000 USD |
| GDELT | `sentiment_scores` | 310 Zeilen | Kontext, kein empirischer Kernparameter |
| Kuratierter Ereigniskatalog | `events_timeline` (Seed) | 7 kuratierte Ereignisse | H2-Eingabe, vorab fixiert |

Die Vergleichsquellen sind bewusst restriktiv gewählt. FiveThirtyEight liefert
native Wahrscheinlichkeiten und ist deshalb direkt vergleichbar
\citep{zotero_poly_002}. RealClearPolitics liefert Umfragedurchschnitte, keine
Prognosewahrscheinlichkeiten; diese Quelle bleibt aus allen Wahrscheinlichkeits-
und Kalibrierungsmetriken ausgeschlossen, solange die in
`docs/research/RCP_TRANSFORMATION.md` beschriebene Logit-Transformation nicht vom
Betreuer freigegeben ist. GDELT bleibt Kontext und wird erst nach gesonderter
Validierung zu einer empirischen Variable. Die Wallet-Daten tragen die
methodisch wichtigste Datenlimitation: Sie enthalten nur Kauftransaktionen und
sind quellseitig ab 10'000 USD gefiltert; beides bleibt Metadaten-Eigenschaft der
Rohquelle und ist keine analytische Schwellendefinition.

## 3.3 Operationalisierung der Hypothesen

### 3.3.1 H1 — Prognosequalität

H1 bewertet, ob Polymarket im überlappenden Vergleichsfenster bessere
Prognosequalität zeigt als vergleichbare traditionelle Wahrscheinlichkeits-
prognosen. Als Verlustmass dient der Brier-Score \citep{lit_brier_001}; der
paarweise Vergleich der Verlustreihen erfolgt mit dem Diebold-Mariano-Test
\citep{lit_dm_001}, ergänzt um Kalibrierungs- und Reliabilitätsdiagnostik, soweit
Stichprobengrösse und Methodik es zulassen. Erlaubt ist ausschliesslich die
Aussage eines *Prognosequalitäts-Vergleichs* (niedrigerer Brier-Verlust im
getesteten Überlappungsfenster). Nicht abgeleitet werden dürfen ein Beweis
höherer Reaktionsgeschwindigkeit, eine allgemeine Marktüberlegenheit oder eine
RCP-Wahrscheinlichkeitsaussage ohne dokumentierte Transformation.

> Belege: `method_h1_brier_dm` → `data/results/thesis_h1_summary.csv`,
> `h1_brier_scores.csv`, `h1_diebold_mariano.json`. Limitation: wiederholte
> Tageszeilen und ein einzelner Wahlkontext begrenzen die Generalisierbarkeit.

### 3.3.2 H2 — Ereignisfenster

H2 prüft, ob sich Polymarket-Wahrscheinlichkeiten um vorab kuratierte öffentliche
Ereignisse in plausibler Richtung und innerhalb fester Tagesfenster bewegen. Die
Ereignisse werden vor der Analyse mit Zeitstempel, Quelle und erwarteter Richtung
fixiert; sie werden nach Sichtung der Marktreaktion weder hinzugefügt noch
entfernt. Das Design folgt der Ereignisstudien-Methodik \citep{lit_eventstudy_001}
und nutzt tägliche Fenster mit CAR-ähnlichen Bewegungssummen. Nachrichten gehen
nicht als frei interpretierter Text ein, sondern nur als kuratierte, belegte
Ereignisse. Erlaubt ist die Aussage einer *täglichen Ereignisfenster-Reaktion*;
ein Intraday-Geschwindigkeitsanspruch oder eine nachträgliche Ereignisauswahl
sind ausgeschlossen.

> Belege: `method_h2_event_window` → `data/results/h2_event_window_summary.csv`,
> `data/events_timeline_seed.csv`, `h2_event_window_rows.csv`. Limitation:
> Tagespreise können keine Intraday-Reaktionszeit identifizieren.

### 3.3.3 H3 — Wallet-Timing

H3 untersucht, ob dataset-relative Wallet-Tiers zeitliche Aktivitätsmuster vor
oder um Polymarket-Preisbewegungen zeigen. Die Tiers werden nicht über eine
willkürliche USD-Schwelle definiert, sondern aus den beobachteten kumulierten
Betragsperzentilen der Wallet-Verteilung abgeleitet. Die Timing-Diagnostik
kombiniert deskriptive Lead-Time-Histogramme, Lead-Lag-Korrelationen und
Granger-Tests \citep{lit_granger_001}. Die Granger-Ausgaben werden ausdrücklich
als prädiktive Timing-Diagnostik unter Modellannahmen gelesen, nicht als
Kausalitätsbeweis; die konzeptionelle und rechtliche Vorsicht gegenüber
Insider-Interpretationen stützt sich auf \citep{zotero_poly_005}. Ausgeschlossen
bleiben Aussagen zu Kausalität, privater Information, Fehlverhalten oder
Profitabilität.

> Belege: `method_h3_wallet_tiers` → `data/results/h3_wallet_distribution_inventory.json`,
> `h3_wallet_tiers.csv`; `method_h3_granger_timing` → `h3_granger_results.csv`,
> `h3_lead_lag_correlations.csv`. Limitation: BUY-only-Quelle, tägliche
> Aggregation und multiples Testen begrenzen die Schlusskraft.

## 3.4 Reproduzierbarkeit und Guardrails

Die Trennung zwischen Berechnung und Interpretation ist durch technische
Leitplanken abgesichert. Quelldaten liegen portabel in SQLite; analytische
Abfragen nutzen zusätzlich DuckDB. Jede Datenbankschreiboperation wird, wo
sinnvoll, validiert (pydantic/pandera). Der deterministische Kern ist getestet:
zum Stand dieses Entwurfs bestehen 640 Tests. Der Datenzugriff für spätere
Interpretationsschichten ist begrenzt (kein `SELECT *` ohne `LIMIT`, maximal 50
Zeilen pro werkzeugartiger Abfrage), und jeder spätere Sprachmodell-Aufruf muss
in `llm_audit_log` protokolliert werden. Commits bleiben klein und thematisch
getrennt. Diese Disziplin ist kein Selbstzweck: Sie macht jede thesis-relevante
Kennzahl rerunnbar und prüfbar und ist damit selbst ein methodischer Beitrag.

## 3.5 Beleg-Hierarchie und Zitiergate

Jede Ergebnisaussage der Arbeit folgt derselben Hierarchie: zuerst das
deterministische Artefakt, dann Methodennote und Limitation, dann die
Literaturstütze, und erst zuletzt — und nur aus begrenzten Zusammenfassungen —
eine protokollierte Interpretationsschicht. Für die Methodenquellen dieses
Kapitels (`lit_brier_001`, `lit_dm_001`, `lit_emh_001`, `lit_eventstudy_001`,
`lit_granger_001` sowie die Polymarket-Quellen `zotero_poly_001`, `_002`, `_005`,
`_007`) gilt: Die Zitierschlüssel stehen, aber die finale Zitation erfolgt erst
nach manueller Seiten-/Abschnittsprüfung im Quellen-Ledger
(`data/results/thesis_source_review_progress_ledger.csv`). Bis dahin bleibt dieser
Entwurf bounded-draft-ready, nicht abgabereif.
