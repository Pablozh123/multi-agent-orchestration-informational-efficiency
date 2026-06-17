# Prozess-Zusammenfassung der Bachelorarbeit (fuer die Betreuung)

Informeller Ueberblick ueber den Arbeitsverlauf seit Beginn -- vom ersten
Explorieren bis zur fokussierten Arbeit. Bewusst ohne formale Vorlage, als
ehrliche Darstellung des Wegs, der Werkzeuge und der Iterationen. Die groben
Zeitraeume stammen aus den Git-Historien der drei Projekte; es geht um den
Ueberblick, nicht um eine taggenaue Dokumentation.

## Der rote Faden in einem Satz
Die Arbeit begann mit der praktischen Frage, ob sich auf Prognosemaerkten
Ineffizienzen ausnutzen lassen, und entwickelte sich zur wissenschaftlichen
Frage, wie informationseffizient diese Maerkte ueberhaupt sind -- die Ausnutzungs-
Perspektive wurde zur Mess-Perspektive.

## Phase 0 -- Themenfindung und Quellenrecherche
- Erste Recherche zu Prognose- und Wettmaerkten, Fokus Polymarket.
- Quellensuche unter anderem mit Perplexity, danach Aufbau einer Literaturbasis
  (spaeter in Zotero gepflegt).
- Ergebnis: Themeneingrenzung auf informationelle Effizienz dezentraler
  Prognosemaerkte am Beispiel Polymarket.

## Phase 1 -- Arbitrage-Exploration: prediction-alpha-bot (ab Mitte Mai 2026)
Paper-only TypeScript/Node-Scanner, read-only, ohne Live-Trading und ohne
Wallet-/Schluessel-Code (zentrale `executeOrPaper`-Grenze, lokale SQLite-Journale).

Untersuchte Arbitrage-Chancen:
- **Within-Market YES+NO < 1:** Wenn YES- und NO-Preis desselben Marktes zusammen
  unter 1 liegen (Schwelle konservativ bei 0.98 fuer Gebuehren/Slippage), ist das
  ein rechnerischer Sofort-Edge.
- **NEG_RISK Bracket Sum-Arb:** In Neg-Risk-Ereignissen (mehrere sich
  ausschliessende Ausgaenge) wird geprueft, ob die Summe der YES-Preise von 1
  abweicht.
- **Cross-Venue-Arbitrage (Kalshi vs. Polymarket):** Gleiche Ausgaenge auf zwei
  Boersen, Netto-Edge nach angenommenen Gebuehren, tiefenbewusste Sizing entlang
  beider Ask-Ladders, konservatives Matching (Match-Score-Schwelle, gemeinsame
  Anker-Begriffe, Pruefung der Aufloesungszeit).

Resultate und Erkenntnis:
- Eine Machbarkeitsanalyse (20. Mai) flaggte rund **305 Kandidaten-Chancen**, plus
  ein Forward-Replay der Basket-Chancen ueber mehrere Tage (22.--27. Mai).
- Wichtig und bewusst dokumentiert: Diese Chancen blieben **paper-only und
  diagnostisch** und wurden **nicht als ausfuehrbar validiert** -- es fehlten
  Orderbuch-Tiefe, echte Gebuehren/Latenz und eine PnL-Grundwahrheit (der
  NEG_RISK-Scanner nutzte nur Gamma-Metadaten, der Within-Market-Scanner
  Testdaten).
- Fazit der Phase: Rohe Preis-Ineffizienzen erscheinen, ihre robuste
  Ausnutzbarkeit ist aber begrenzt. Genau das motivierte den Wechsel von der
  Ausnutzung zur Messung der Effizienz.

## Phase 2 -- Research-Terminal: prediction-market-terminal (Ende Mai bis Mitte Juni 2026, 146 Commits)

### 2a -- Ausgangspunkt: Polymarket-Reddit-Sentiment-Analyse
Urspruenglich ein Data-Wrangling-Modulprojekt, das explorativ prueft, ob die
Reddit-Stimmung mit Polymarket-Wahrscheinlichkeiten zusammenhaengt.
- **Aufbau (ETL):** aktive Polymarket-Maerkte per Gamma/CLOB-API laden, aus den
  Marktfragen Reddit-Suchbegriffe ableiten, passende Posts sammeln, mit
  Twitter-RoBERTa (`cardiffnlp/twitter-roberta-base-sentiment-latest`) als
  positiv/neutral/negativ klassifizieren, pro Markt zu einem Sentiment-Score
  aggregieren. Zusaetzlich ein Zero-Shot-Stance-Score (DeBERTa-v3 NLI), der direkt
  misst, ob ein Post das Eintreten des Ereignisses stuetzt (`P(ja) - P(nein)`).
- **Stichprobe:** finaler Bulk-Run vom 22. Mai mit 29 Live-Maerkten und 725
  Reddit-Posts (keine Demo-Daten).
- **Wichtigste Erkenntnis:** **Kein statistisch signifikanter** linearer
  Zusammenhang zwischen Reddit-Sentiment und Polymarket-Wahrscheinlichkeit, auch
  die Rangkorrelation nicht signifikant; die Richtung stimmt nur in **13 von 29
  Maerkten (44.8 Prozent)** ueberein. Ein Relevanz-Audit zeigte zudem, dass die
  Reddit-Treffer inhaltlich verrauscht sind. Reddit-Stimmung allein ist also kein
  robuster Praediktor fuer Polymarket-Preise -- ein methodisch sauberer, bewusst
  vorsichtiger Befund.

### 2b -- Ausbau zum Research-Terminal
Aus dieser Basis wurde ein Streamlit-Research-Terminal fuer Polymarket und Kalshi.
Was gebaut wurde und warum:
- **Whale- und Insider-Risiko-Screening:** Suspicion-Scoring, Fresh-Wallet-Cluster,
  Co-Trading-Netzwerkgraph mit Louvain-Communities (Syndikat-Erkennung),
  kategorie-bewusste Insider-Plausibilitaet. Motiv: sichtbar machen, welche Wallets
  auffaellig agieren -- der direkte Vorlaeufer von H3 und dem Monitoring-Werkzeug.
- **Anomalie- und Ranking-Werkzeuge:** Volumen-Anomalie (1h gegen 24h-Baseline),
  Smart- und Speed-Trader-Ranking, Insider-Picks-Feed, Markt- und Trader-Uebersichten.
- **Backtesting:** Equity-Kurven, Copy-Trade-Backtest-Engine mit Gebuehren,
  Fade-Strategie-Backtester -- um Strategie-Ideen historisch zu pruefen.
- **Paper-Copy-Trading:** Multi-Trader-Verwaltung, portfolio-relative Sizing,
  WebSocket-Sub-Sekunden-Erkennung, ehrliche Copy-Buchhaltung (keine erfundene
  PnL), on-chain Reconciliation, clock-korrigierte Latenz-Telemetrie. Bewusst nur
  Papier, kein Live-Handel.
- **Infrastruktur:** Kalshi-Integration in alle Ebenen, echte Authentifizierung
  (Google OIDC), Produktions-Readiness inklusive Schweizer Rechts-Checkliste.

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
  Wallet-Tier-Aktivitaet, Konzentration, Ereigniskontext, Anomalie-Hinweise) --
  die fokussierte, akademisch saubere Fortsetzung des Terminals.
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
