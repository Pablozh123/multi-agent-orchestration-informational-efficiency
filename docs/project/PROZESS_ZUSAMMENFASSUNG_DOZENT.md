# Prozess-Zusammenfassung der Bachelorarbeit (fuer die Betreuung)

Informeller Ueberblick ueber den Arbeitsverlauf seit Beginn -- vom ersten
Explorieren bis zur fokussierten Arbeit. Bewusst ohne formale Vorlage, als
ehrliche Darstellung des Wegs, der Werkzeuge und der Iterationen. Die groben Zeitraeume stammen aus den Git-Historien der drei Projekte;
es geht um den Ueberblick, nicht um eine taggenaue Dokumentation.

## Der rote Faden in einem Satz
Die Arbeit begann mit der praktischen Frage, ob sich auf Prognosemaerkten
Ineffizienzen ausnutzen lassen, und entwickelte sich zur wissenschaftlichen
Frage, wie informationseffizient diese Maerkte ueberhaupt sind -- die Ausnutzungs-
Perspektive wurde zur Mess-Perspektive.

## Phase 0 -- Themenfindung und Quellenrecherche
- Erste Recherche zu Prognose- und Wettmaerkten, Fokus Polymarket.
- Quellensuche unter anderem mit Perplexity, danach Aufbau einer
  Literaturbasis (spaeter in Zotero gepflegt).
- Ergebnis: Themeneingrenzung auf informationelle Effizienz dezentraler
  Prognosemaerkte am Beispiel Polymarket.

## Phase 1 -- Arbitrage-Exploration: prediction-alpha-bot (19.--20. Mai 2026)
- Paper-only TypeScript/Node-Scanner fuer moegliche Markt-Chancen, ohne
  Live-Trading, ohne Wallet-/Schluessel-Code (zentrale `executeOrPaper`-Grenze,
  lokale SQLite-Journale).
- Implementierte Scanner: NEG_RISK-Bracket-Sum-Arbitrage, Within-Market
  YES+NO < 1 und ein Cross-Venue-Arbitrage-Scanner fuer gematchte Kalshi-/
  Polymarket-Ausgaenge.
- Erkenntnis: Wo und in welcher Form treten ueberhaupt Preis-Ineffizienzen auf?
  Das motivierte die spaetere Effizienz-Fragestellung.

## Phase 2 -- Research-Terminal: prediction-market-terminal (29. Mai--12. Juni 2026, 146 Commits)
- Aus einem Data-Wrangling-Vorprojekt (Reddit-Sentiment vs. Polymarket,
  Bulk-Run 22. Mai 2026: 29 Maerkte, 725 Reddit-Posts) zu einem Streamlit-
  Research-Terminal ausgebaut.
- Funktionen: Marktentdeckung, Trader-/Wallet-Research, Live-Public-Flow,
  Whale-/Insider-Risiko-Screening, Backtesting, Alerts, Tracking sowie ein
  paper-only Copy-Trading-Modul. Alle Daten aus oeffentlichen APIs (Polymarket
  Gamma/Data/CLOB, Kalshi). Live-Trading deaktiviert, Copy-Trading nur Papier.
- Erkenntnis: Wie laesst sich Markt- und Wallet-Aktivitaet read-only sichtbar
  machen? Das wurde zur Grundlage des spaeteren Monitoring-Werkzeugs der Arbeit.

## Phase 3 -- Fokussierung auf die Forschungsfrage
- Wechsel von der Ausnutzungs- zur Mess-Perspektive: Statt Chancen zu handeln,
  wird die informationelle Effizienz reproduzierbar geprueft.
- Definition dreier Proxy-Hypothesen: H1 Prognosequalitaet (Brier,
  Diebold-Mariano), H2 Ereignisreaktion (Ereignisstudie), H3 Wallet-Timing
  (Lead-Lag, Granger, Anomalie- und Signatur-Diagnostik).

## Phase 4 -- Deterministischer Analyse-Kern (ba-thesis, Juni 2026)
- Vollstaendig deterministischer, getesteter Python-Analysepfad: alle Kennzahlen
  werden berechnet, bevor sie interpretiert werden. LLMs interpretieren nur
  begrenzte, vorab berechnete Zusammenfassungen.
- Ergebnisse zu H1--H3 inklusive Abbildungen und Tabellen.

## Phase 5 -- Loesung und Orchestrierung
- Aus der Untersuchung hervorgegangenes read-only Monitoring-Werkzeug, das die
  Effizienz-Perspektive operationalisiert (Marktbewegung, aggregierte
  Wallet-Tier-Aktivitaet, Konzentration, Ereigniskontext, Anomalie-Hinweise).
- Multiagenten-Orchestrierung als Entwicklungs- und Review-Methode: EventScout,
  CaseNarrative, SkepticReviewer, Orchestrator ueber einer read-only MCP-Schicht;
  nur Pruef-Empfehlungen, kein Handel, jede LLM-Interaktion protokolliert.

## Phase 6 -- Verschriftlichung
- Aufbau nach FHNW-Vorlage Projekt- und Bachelorarbeiten (Analyse der Situation,
  Schlussfolgerung, Loesung, allgemeine Schlussfolgerung, naechste Schritte).
- Quellen-Review (deutsche APA 7) und Umsetzung in der FHNW-Word-Vorlage,
  Quellenverwaltung mit Zotero.

## Eingesetzte Werkzeuge
- Recherche: Perplexity, Zotero (Quellenverwaltung).
- Entwicklung/Analyse: Python, TypeScript/Node, Streamlit, Git.
- KI-Unterstuetzung: Claude (inkl. Cowork) und OpenAI Codex fuer Code- und
  Textunterstuetzung. Details im Hilfsmittelverzeichnis der Arbeit.

## Eigenleistung und Integritaet
- Beide Vorprojekte sind ausdruecklich paper-only und read-only: kein
  Live-Trading, keine echten Orders, keine Wallet-/Schluessel-Verwaltung, keine
  Anlageberatung.
- Das Research-Terminal ist teilweise aus einem Data-Wrangling-Modulprojekt
  hervorgegangen. Eine Wiederverwendung von Teilen daraus in der Bachelorarbeit
  ist nur zulaessig, wenn sie mit der Betreuung abgesprochen und in der Arbeit
  ausgewiesen wird (Eigenstaendigkeitserklaerung). [Mit Betreuung klaeren.]
