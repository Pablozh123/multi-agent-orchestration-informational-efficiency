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

Zentrale Unterscheidung: Ein Preisunterschied ist noch keine Arbitrage. Eine echte
risikofreie Cross-Venue-Arbitrage entsteht erst, wenn man YES auf der einen und NO
auf der anderen Boerse fuer denselben Ausgang zusammen fuer unter 1.00 kaufen kann
(Kosten = YES-Ask + NO-Ask, Brutto-Edge = 1 - Kosten, abzueglich Gebuehren). Ein
blosser Same-side-Spread ist nur ein Bewertungsunterschied, kein garantierter
Gewinn. Die Matching-Logik ist bewusst konservativ (kanonisches Event-/Outcome-
Modell, Ankerbegriffe, Aufloesungszeit und -regeln); mehrdeutige Paare landen in
einer Review-Liste statt automatisch als Arb.

Untersuchte Marktfaelle: Inflation (Kalshi-KXCPI vs. Polymarket) und Bitcoin
(Range/Bracket vs. ``ueber X'') ergaben keine sauberen gleichen Resolutionen;
Fed-Zinsmaerkte blieben mehrdeutig; nur das Somaliland-Paar war ein manuell
verifiziertes echtes Paar. Die echten historischen Faelle waren real, aber klein
und fragil:

| Datum | Paar | Kosten (YES+NO) | Brutto-Edge | Realistischer Max-Gewinn (tiefenbereinigt) |
|---|---|---|---|---|
| 2026-06-05 | Somaliland | 93.5c (10.5 + 83.0) | +6.5c | ca. 2.90 USD (100 Kontrakte; Tiefen-Schnitt YES 14.1c statt 10.5c) |
| 2026-06-08 | Somaliland | 98.3c (14.3 + 84.0) | +1.7c | ca. 0.71 USD |
| spaeter (inaktiv) | Somaliland | 98.8c (13.8 + 85.0) | +1.2c | ca. 0.18 USD |

Aktuell sind keine aktiven echten YES+NO-Arbitragen sichtbar, nur einige
Same-side-Spreads. Wichtig fuer die Einordnung: Solche Cross-Venue-Arbitragen sind
faktisch **Carry-Trades** -- man kauft beide Seiten und haelt die Position bis zur
Marktaufloesung, die teils Monate entfernt liegt (z.B. ``Somaliland before 2027'').
Der ohnehin kleine Edge verteilt sich damit ueber eine lange Haltedauer mit
gebundenem Kapital, was den annualisierten Ertrag ueberschaubar macht; Tiefe,
Gebuehren und Slippage verkleinern ihn zusaetzlich. Fazit: Rohe Ineffizienzen
erscheinen, ihre robuste, wirtschaftlich attraktive Ausnutzbarkeit ist aber
begrenzt -- genau das motivierte den Wechsel von der Ausnutzung zur Messung.

### Weitere getestete Strategien, Scanner-Lauf und Einschaetzung
Der Cross-Venue-Fall war nur eine von mehreren systematisch katalogisierten
Strategien. Der Scanner fuehrt einen Edge-Katalog mit Evidenz-Stufen (S =
strukturelle Arbitrage mit garantiertem Gewinn bei sauberer Ausfuehrung, A =
starker empirischer Edge, B = vielversprechend, C = blosse Hypothese, F = getestet
und gescheitert) und protokolliert je Strategie, was tatsaechlich beobachtbar war.
Forward-Replay- und Snapshot-Laeufe liefen lokal ueber rund zwei Wochen
(20. Mai bis 2. Juni 2026) auf gespeicherten Orderbook- und Snapshot-Daten.

| Strategie (Auswahl) | Evidenz | Beobachtung im Lauf |
|---|---|---|
| NEG_RISK Basket Sum-Arb (YES-Summe > 1) | S | meist 0 saubere Arbs (Beispiel: 42 Events gescannt, 0 Arbs); ein toter Leg macht den Basket unbaubar -- Markt grossteils effizient |
| Within-Market (YES + NO < 1) | S | naechste Faelle typisch bei Summe ~1.001 (~10 Bps), schliessen in Sekunden, sehr selten |
| Cross-Venue (Kalshi x Polymarket) | A | selten, nur um Katalysator-Events; Routine-Kadenz null (Somaliland-Faelle oben) |
| Cross-Market-Monotonie | A | real, aber duenne Tiefe (< 50 USD Kapazitaet, 5-7 pp Spread frisst den Edge) |
| Sum-Arb Lock-In | A | bester real beobachteter Edge; Baskets bei 1.025-1.030 v.a. in Wahlphasen |
| Tail-Fade / Premium Harvest | B | konstanter Klein-Edge; Haltedisziplin noetig (duenne Buecher beim Exit) |
| Whale-Following / Copy | B | Elite-Whales existieren (Profit-Faktor > 4 ueber 800+ Positionen); Kopieren nur als schwaches Zusatzsignal |
| Crypto Oracle-Divergence-Fade | B | N=28: Fade-Richtung 26W/2L (~93 %), aber Out-of-Sample-Bestaetigung offen |
| UMA-Dispute-Arb | F | verworfen: kategorie-gefilterte Backtests luegen (100 % -> ~40 % Trefferquote ohne Filter) |
| Temporal Anchoring | F | Null-Ergebnis; scheinbare Luecken waren Artefakte fast aufgeloester Monate |

Resultate des Forward-Replays: Die strukturellen Scanner fanden im
Beobachtungsfenster keine validierte, sauber ausfuehrbare Arbitrage (typisch 0
Arbs pro Lauf, am Schluss-Tag 0 Zeilen). Einzelne sehr grosse scheinbare Edges
(mehrere hundert Prozent) waren im Replay ausdruecklich als experimentell und
unverknuepft, mit unvollstaendiger Basket-Abdeckung oder veralteten Leg-Snapshots
markiert -- also Artefakte, keine echten Chancen. Eine Verknuepfung zu
aufgeloesten Maerkten oder echter PnL fehlt bislang; Live-Handel ist im aktuellen
Stand bewusst nicht moeglich.

Einschaetzung: Der Befund ist selbst ein Effizienz-Ergebnis. Saubere strukturelle
Arbitragen sind selten und schliessen schnell, empirische Edges sind duenn,
gebuehren- und tiefenlimitiert oder noch unbestaetigt, und mehrere zunaechst
attraktive Muster fielen bei ehrlicher, kategorie-fairer Pruefung in sich zusammen.
Genau diese begrenzte, schwer ausnutzbare Ineffizienz stuetzt die spaetere
Mess-Perspektive der Arbeit.

## Phase 2 -- Research-Terminal: prediction-market-terminal

### 2a -- Ausgangspunkt: Polymarket-Reddit-Sentiment-Analyse
Urspruenglich ein Data-Wrangling-Modulprojekt: Haengt die Reddit-Stimmung mit
Polymarket-Wahrscheinlichkeiten zusammen? Aufbau als ETL-Pipeline (Polymarket-API
-> Reddit-Suchbegriffe -> Posts -> Sentiment-Klassifikation -> pro Markt
aggregiert), zusaetzlich ein Zero-Shot-Stance-Score (DeBERTa-v3 NLI), der direkt
misst, ob ein Post das Eintreten des Ereignisses stuetzt. Stichprobe: 29
Live-Maerkte, 725 Reddit-Posts, 7 Subreddits (Bulk-Run 22. Mai).

| Modell | Pearson r | Spearman rho | Richtungstreffer |
|---|---|---|---|
| VADER (Baseline) | +0.069 | +0.115 | 27.6 % |
| Twitter-RoBERTa (final) | +0.079 | +0.151 | 44.8 % |

Wichtigste Erkenntnis: **kein statistisch signifikanter** Zusammenhang zwischen
Reddit-Sentiment und Polymarket-Wahrscheinlichkeit (schwach positiv, nicht
signifikant), Richtungstreffer nur 13 von 29 Maerkten (44.8 %). Der Stance-Score
korrelierte **nicht staerker** als reines Sentiment (F4). Ein methodischer
Kernpunkt: Sentiment misst Stimmung, nicht Zustimmung -- bei negativ gerahmten
Fragen (Rezession, Krieg, Verurteilung) kann positive Stimmung sogar gegen das
Ereignis sprechen, weshalb pro Marktfrage eine Polaritaets-Korrektur eingefuehrt
wurde. Fazit: Reddit-Stimmung allein ist kein robuster Praediktor fuer
Polymarket-Preise.

### 2b -- Ausbau zum Research-Terminal
Die Ausgangsfrage war, wie man profitable Polymarket-Trader und Whales erkennen und
verstehen kann. Daraus wurde eine Streamlit-Research-Plattform fuer Polymarket und
Kalshi mit mehreren Workspaces: Marktsuche, Trader-Leaderboard und Wallet-Profile,
Live-Trade-Flow, Whale Flow, Suspicious (Insider-Risiko), Cross-Venue, Backtester,
Paper-Copytrading, Monitor und Portfolio.

**Fallbeispiel Swisstony.** Als Testfall diente Swisstony, ein sehr profitabler
oeffentlicher Trader (ohne Adressnennung), an dem die ganze Pipeline erprobt wurde:
Trader-Erkennung, Backtesting und Paper-Copytrading. Es ging nicht darum, ihn als
``wichtigsten'' Trader auszuzeichnen, sondern an einem starken, realen Beispiel zu
messen, wie gut sich eine Quelle ueberhaupt analysieren und kopieren laesst. Die
Zahlen stammen aus lokaler Analyse oeffentlicher Daten und sind vor produktivem
Einsatz neu live zu pruefen:

| Kennzahl | Wert (lokale Analyse) |
|---|---|
| Berichtete PnL | ca. 9.6 Mio. USD |
| Cashflow-bereinigter ROI | ca. +200 % |
| Winrate | ca. 53 % |
| All-time-Volumen | ca. 867 Mio. USD |
| Sharpe-aehnlich (taeglich) | ca. 4.1 |
| Max. Drawdown | ca. -0.97 Mio. USD |

Interpretation des Edges: keine wenigen grossen Directional Bets, sondern
Marktselektion, Timing, hoher Turnover, kurze Event-Durations und sauberes
Kapital-Recycling. Eine Winrate um 53 % erklaert den Erfolg also nicht allein --
entscheidend sind Odds, Size und Umschlag.

**Paper-Copytrading** ist bewusst nur Papier: Es beobachtet oeffentliche Trades
einer Zielwallet, skaliert sie in ein lokales Portfolio und misst Latenz, Sizing,
Cash-Recycling, Skips, Settlement-Mapping und Fidelity. Keine echten Orders.

**Whale Flow und Suspicious.** Das Suspicious-Screening setzt auf Whale-Risiko-
Scores je Event und Wallet auf und ergaenzt Signale, die ein reiner Groessen-Score
allein nicht sieht. Eine Wallet wird also nicht schon wegen ihrer Groesse markiert,
sondern anhand einer Kombination konkreter Muster:

- **Fresh-Wallet-Cluster:** mehrere im Datensatz kaum gesehene Wallets (z.B. bis zu
  zwei Trades im Sample) mit Whale-Notional draengen im selben Markt auf dieselbe
  Seite -- das klassische Muster, das oeffentliche Insider-Screens beschreiben.
- **Konto-/Wallet-Alter:** das echte Alter einer Wallet (sofern abgefragt) fliesst
  als Zu- oder Abschlag in den Score ein (sehr neu und zugleich sehr gross = hoeher).
- **Co-Trading-/Louvain-Cluster:** Wallets, die wiederholt gemeinsam und zeitnah
  dieselben Ausgaenge handeln, werden ueber ein Netzwerk als moegliche koordinierte
  Gruppe (Syndikat) erkannt.
- **Handelsform als Etikett:** Contrarian (Wette gegen den Markt, z.B. < 40c),
  Trend-Follower (> 80c), Lottery-Ticket (< 20c) und Whale-Splash (sehr grosse
  Kostenbasis) -- beschreibende Labels, die das Verhalten einordnen.

Entscheidend ist die **Kontext-Gewichtung nach Marktart**: Sport, Asset-Preise und
Wetter gelten als wenig insider-plausibel (oeffentliche Odds bzw. modellgetriebene
Ausgaenge -> grosse Flows sind High-Roller, keine Insider), waehrend Politik, Awards
sowie Firmen- und interne Maerkte insider-anfaellig sind (asymmetrischer
Informationszugang; z.B. kennen Award-Jurys und Produktionsteams Resultate frueh).
Der resultierende Score wird in Baender gefasst (>= 70 hoch, >= 55 mittel, >= 40
erhoeht). Wichtig: Das ist ein best-effort Screen auf oeffentlichen Daten, kein
juristischer Nachweis. Dieses Screening ist der direkte Vorlaeufer von H3 und dem
Monitoring-Werkzeug der Arbeit. Bei Kalshi fehlen oeffentliche Trader-Wallets,
daher dort kein Wallet-Copytrading.

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

### Schweizer Referendum als Live-Fallstudie
Als aktueller, eigenstaendiger Vergleich ausserhalb der US-Wahl diente die
eidgenoessische Abstimmung vom 14. Juni 2026. Beim offiziellen Ja-Anteil von
45.21 % lag die finale Umfrage als Stimmenanteil naeher am Resultat, waehrend
Polymarket im lokalen Live-Fenster (Ja zuletzt 21.5 %) als binaere
Ablehnungswahrscheinlichkeit klarer auf der richtigen Seite lag. Wichtig:
Polymarket-Preise sind Annahmewahrscheinlichkeiten, Umfragen sind Stimmenanteile --
der Binaervergleich ist nur ein transparenter Proxy und kein Mispricing-,
Effizienz- oder Tradeability-Beweis. Die Fallstudie pruefte die Effizienz-
Perspektive an einem frischen, selbst beobachteten Ereignis und ist als begrenzte
Post-Resultat-Fallstudie eingeordnet.

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
