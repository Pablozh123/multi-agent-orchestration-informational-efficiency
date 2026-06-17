# Prozess-Zusammenfassung der Bachelorarbeit (fuer die Betreuung)

Informeller Ueberblick ueber den Arbeitsverlauf seit Beginn -- vom ersten
Explorieren bis zur fokussierten Arbeit. Bewusst ohne formale Vorlage, als
ehrliche Darstellung des Wegs, der Werkzeuge und der Iterationen. Es geht um den
Ueberblick, nicht um eine taggenaue Dokumentation.

## Der rote Faden in einem Satz
Die Arbeit begann mit der praktischen Frage, ob sich auf Prognosemaerkten
Ineffizienzen ausnutzen lassen, und entwickelte sich zur wissenschaftlichen
Frage, wie informationseffizient diese Maerkte ueberhaupt sind -- die Ausnutzungs-
Perspektive wurde zur Mess-Perspektive.

## Phase 0 -- Themenfindung und Quellenrecherche
Erste Recherche zu Prognose- und Wettmaerkten mit Fokus Polymarket, unter anderem
mit Perplexity, danach Aufbau einer Literaturbasis (spaeter in Zotero gepflegt).
Daraus die Themeneingrenzung: informationelle Effizienz dezentraler
Prognosemaerkte am Beispiel Polymarket.

## Phase 1 -- Arbitrage-Exploration: prediction-alpha-bot
Ein paper-only TypeScript/Node-Scanner, der Markt- und Orderbook-Daten liest,
moegliche Chancen erkennt und Reports schreibt. Schwerpunkt: Cross-Venue zwischen
Kalshi und Polymarket.

Zentrale Unterscheidung des Projekts: Ein Preisunterschied ist noch keine
Arbitrage. Eine echte risikofreie Cross-Venue-Arbitrage entsteht erst, wenn man
YES auf der einen und NO auf der anderen Boerse fuer denselben Ausgang zusammen
fuer unter 1.00 kaufen kann (Kosten = YES-Ask + NO-Ask, Brutto-Edge =
(1 - Kosten), abzueglich Gebuehren). Ein blosser Same-side-Spread ist nur ein
Bewertungsunterschied, kein garantierter Gewinn. Die Matching-Logik ist bewusst
konservativ (kanonisches Event-/Outcome-Modell, Ankerbegriffe, Aufloesungszeit und
-regeln); mehrdeutige Paare landen in einer Review-Liste statt automatisch als Arb.

Untersuchte Marktfaelle: Inflation (Kalshi-KXCPI vs. Polymarket) und Bitcoin
(Range/Bracket vs. ``ueber X'') ergaben keine sauberen gleichen Resolutionen und
wuerden eine Basket-/Bracket-Logik brauchen; Fed-Zinsmaerkte blieben mehrdeutig;
nur das Somaliland-Paar war ein manuell verifiziertes echtes Paar.

Ergebnis und Erkenntnis: Aktuell sind keine aktiven echten YES+NO-Arbitragen
sichtbar, nur einige Same-side-Spreads. Die historischen echten Faelle
(Somaliland) waren real, aber klein und fragil -- ein Top-of-book-Edge von rund
6.5 Cent schrumpfte tiefenbereinigt auf wenige Dollar Maximalgewinn, spaetere
Faelle lagen bei nur 1 bis 2 Cent. Wichtig fuer die Einordnung: Solche
Cross-Venue-Arbitragen sind faktisch **Carry-Trades** -- man kauft beide Seiten und
haelt die Position bis zur Marktaufloesung, die teils Monate entfernt liegt (z.B.
``Somaliland before 2027''). Der ohnehin kleine Edge verteilt sich damit ueber eine
lange Haltedauer mit gebundenem Kapital, was den annualisierten Ertrag
ueberschaubar macht; Tiefe, Gebuehren und Slippage verkleinern ihn zusaetzlich.
Fazit der Phase: Rohe Ineffizienzen erscheinen, ihre robuste, wirtschaftlich
attraktive Ausnutzbarkeit ist aber begrenzt -- genau das motivierte den Wechsel von
der Ausnutzung zur Messung der Effizienz.

## Phase 2 -- Research-Terminal: prediction-market-terminal

### 2a -- Ausgangspunkt: Polymarket-Reddit-Sentiment-Analyse
Urspruenglich ein Data-Wrangling-Modulprojekt, das explorativ prueft, ob die
Reddit-Stimmung mit Polymarket-Wahrscheinlichkeiten zusammenhaengt.
- Aufbau (ETL): aktive Polymarket-Maerkte per API laden, aus den Marktfragen
  Reddit-Suchbegriffe ableiten, Posts sammeln, mit Twitter-RoBERTa als
  positiv/neutral/negativ klassifizieren, pro Markt aggregieren; zusaetzlich ein
  Zero-Shot-Stance-Score (DeBERTa-v3 NLI), der direkt misst, ob ein Post das
  Eintreten des Ereignisses stuetzt.
- Stichprobe: 29 Live-Maerkte und 725 Reddit-Posts (Bulk-Run 22. Mai).
- Wichtigste Erkenntnis: **kein statistisch signifikanter** Zusammenhang zwischen
  Reddit-Sentiment und Polymarket-Wahrscheinlichkeit; die Richtung stimmt nur in
  **13 von 29 Maerkten (44.8 Prozent)** ueberein, und die Reddit-Treffer sind
  inhaltlich verrauscht. Reddit-Stimmung allein ist also kein robuster Praediktor.

### 2b -- Ausbau zum Research-Terminal
Die Ausgangsfrage war, wie man profitable Polymarket-Trader und Whales erkennen
und verstehen kann. Daraus wurde eine Streamlit-Research-Plattform fuer Polymarket
und Kalshi mit mehreren Workspaces: Marktsuche, Trader-Leaderboard und
Wallet-Profile, Live-Trade-Flow, Whale Flow, Suspicious (Insider-Risiko),
Cross-Venue, Backtester, Paper-Copytrading, Monitor und Portfolio.

- **Fallstudie Swisstony:** wichtigster analysierter Trader (oeffentliche Wallet,
  ohne Adressnennung). Aus lokaler Analyse oeffentlicher Daten: sehr starke
  historische Performance (berichtete PnL in zweistelliger Millionenhoehe,
  cashflow-bereinigter ROI rund +200 Prozent bei einer Winrate um 53 Prozent, hohe
  risikoadjustierte Kennzahlen). Interpretation des Edges: keine wenigen grossen
  Directional Bets, sondern Marktselektion, Timing, hoher Turnover, kurze
  Event-Durations und sauberes Kapital-Recycling. Eine Winrate um 53 Prozent
  erklaert den Erfolg also nicht allein -- entscheidend sind Odds, Size und
  Umschlag. Die Zahlen sind vor einem produktiven Einsatz neu live zu pruefen.
- **Paper-Copytrading:** bewusst nur Papier. Es beobachtet oeffentliche Trades
  einer Zielwallet, skaliert sie in ein lokales simuliertes Portfolio und misst,
  wie gut sich eine Quelle ueberhaupt kopieren laesst: Latenz, Sizing,
  Cash-Recycling, Skips, Settlement-Mapping und Fidelity gegenueber der Source.
  Keine echten Orders.
- **Whale Flow und Suspicious:** fuehren Kontext, Timing, Wallet-Historie und
  Verhalten zusammen (Suspicion-Scoring, Fresh-Wallet- und Louvain-Cluster,
  Co-Trading-Netzwerk). Wichtig: Sport- und Wettermaerkte sind nicht automatisch
  insider-riskant, weil viel oeffentlich modellierbar ist; hoeheres Risiko entsteht
  eher bei politischen, juristischen oder internen Maerkten mit asymmetrischem
  Informationszugang. Dieses Screening ist der direkte Vorlaeufer von H3 und dem
  Monitoring-Werkzeug der Arbeit.
- **Kalshi-Grenze:** Kalshi veroeffentlicht keine oeffentlichen Trader-Wallets,
  daher sind dort Markt- und Cross-Venue-Analysen moeglich, aber kein
  Wallet-Copytrading wie bei Polymarket.

## Phase 3 -- Fokussierung auf die Forschungsfrage
Wechsel von der Ausnutzungs- zur Mess-Perspektive: Statt Chancen zu handeln, wird
die informationelle Effizienz reproduzierbar geprueft. Definition dreier
Proxy-Hypothesen: H1 Prognosequalitaet (Brier, Diebold-Mariano), H2
Ereignisreaktion (Ereignisstudie), H3 Wallet-Timing (Lead-Lag, Granger, Anomalie-
und Signatur-Diagnostik).

## Phase 4 -- Deterministischer Analyse-Kern (ba-thesis)
Vollstaendig deterministischer, getesteter Python-Analysepfad: alle Kennzahlen
werden berechnet, bevor sie interpretiert werden. LLMs interpretieren nur
begrenzte, vorab berechnete Zusammenfassungen. Ergebnisse zu H1--H3 inklusive
Abbildungen und Tabellen.

## Phase 5 -- Loesung und Orchestrierung
Aus der Untersuchung hervorgegangenes read-only Monitoring-Werkzeug, das die
Effizienz-Perspektive operationalisiert (Marktbewegung, aggregierte
Wallet-Tier-Aktivitaet, Konzentration, Ereigniskontext, Anomalie-Hinweise) -- die
fokussierte, akademisch saubere Fortsetzung des Terminals. Dazu eine
Multiagenten-Orchestrierung als Entwicklungs- und Review-Methode (EventScout,
CaseNarrative, SkepticReviewer, Orchestrator ueber einer read-only Schicht): nur
Pruef-Empfehlungen, kein Handel, jede LLM-Interaktion protokolliert.

## Phase 6 -- Verschriftlichung
Aufbau nach FHNW-Vorlage Projekt- und Bachelorarbeiten (Analyse der Situation,
Schlussfolgerung, Loesung, allgemeine Schlussfolgerung, naechste Schritte),
Quellen-Review nach deutscher APA 7, Umsetzung in der FHNW-Word-Vorlage,
Quellenverwaltung mit Zotero.

## Eingesetzte Werkzeuge
Recherche: Perplexity, Zotero. Entwicklung und Analyse: Python, TypeScript/Node,
Streamlit. KI-Unterstuetzung: Claude (inkl. Cowork) und OpenAI Codex fuer Code- und
Textunterstuetzung (Details im Hilfsmittelverzeichnis der Arbeit).

## Eigenleistung und Integritaet
Alle Teilprojekte sind paper-only und read-only: kein Live-Trading, keine echten
Orders, keine Wallet- oder Schluessel-Verwaltung, keine Anlageberatung, keine
Secrets im Code. Das Research-Terminal ist teilweise aus einem
Data-Wrangling-Modulprojekt hervorgegangen; eine Wiederverwendung von Teilen daraus
in der Bachelorarbeit ist nur zulaessig, wenn sie mit der Betreuung abgesprochen und
in der Arbeit ausgewiesen wird (Eigenstaendigkeitserklaerung). [Mit Betreuung klaeren.]
