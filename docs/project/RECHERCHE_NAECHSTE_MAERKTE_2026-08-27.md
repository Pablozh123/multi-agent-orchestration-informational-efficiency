# Recherche 27.08.2026: Welche Märkte als Nächstes — Befund, Thesen, Direktanalysen

Erhoben 27.08.2026 nachmittags/abends von der Tages-Session (Zweit-Klon).
Datenbasis: dokumentierte Read-only-Abfragen gegen Gamma- und Kalshi-Public-API
(Skripte im Session-Scratchpad: `markt_inventar.py`, `thesen_details.py`,
`curtis_basisraten.py`, `curtis_kontexte.py`, `jre_brackets.py`,
`curtis_regeln.py`), unsere archivierten Resolutions-Dateien
(`data/raw/live_runs/resolutions_*.json`, Stand 26.08.), Episodentranskripte
scrapsfromtheloft.com sowie zwei Web-Research-Durchgänge (Quellen in §7).
Keine Orders platziert, keine Wallet-Zugriffe.

## 1. Kurzbefund

**Die Mention-Märkte sind nicht weg — sie sind geschrumpft.** Die Klasse lebt
(Curtis E6, JRE-Wochenserie, Ulta/Dell/Robinhood-Earnings, Trump-NASA und
Warsh-Jackson-Hole morgen, Leavitt-Serie, Monatsaggregate), aber die
Liquidität ist kollabiert: All-In-Serie Januar ~415k$ → August ~5k$ je Event.
Treiber: US-Volumen wandert auf die regulierte US-Börse (dort sind
Mention-Märkte NICHT gelistet), seit ~März Taker-Gebühren auf fast allen
Kategorien, und seit 13.08. läuft eine CFTC-Prüfung der Mention-Märkte
(Insiderfall Perez, Trumps Teleprompter-Operator). **Konsequenz: die Kante
existiert weiter und passt zu unserer Kontogröße — aber nichts Großes mehr
nur für diese Klasse bauen; ernten mit vorhandener Infrastruktur, Maker-first,
und Venue-Risiko als erstklassiges Risiko führen.**

Bestbelegte nächste Ziele: **(T1) Curtis E6 bis Sonntag**, **(T2) All-In E287
Pre-Drop-Positionierung morgen früh**, **(T3) JRE-Wochenbrackets pre-drop**,
**(T4) Speech-SAY-Dauerstrecke** (morgen Warsh/NASA, ab jetzt Fed-Presser
16.09. auf Kalshi mit bereits bekannter Wortliste). Details und Zahlen unten.

## 2. Marktlage 27.08. (gemessen)

### 2.1 Offene Mention-/Serien-Events (Gamma, 27.08. abends)

| Event | ID | Ende | liq $ | vol24h $ |
| --- | --- | --- | --- | --- |
| Trump remarks at NASA | 906672 | 28.08. | 33 200 | 39 322 |
| Warsh Jackson-Hole-Speech | 870938 | 28.08. | 25 986 | 31 860 |
| President Curtis E6 | 913373 | 30.08. | 10 379 | 4 794 |
| Leavitt nächstes WH-Briefing | 759033 | 31.08. | 10 363 | 3 691 |
| Ulta Earnings-Call | 882986 | 27.08. | 5 635 | 4 602 |
| Dell Earnings-Call | 918384 | 01.09. | 4 390 | 4 567 |
| JRE erste Episode der Woche (31.08.) | 913395 | 06.09. | 4 293 | 897 |
| Trump say September (Monat) | 918328 | 30.09. | 11 173 | 3 264 |
| NYT-Front-Page-Woche (31.08.–06.09.) | 918355 | 06.09. | 3 112 | 1 980 |
| Elon # tweets (mehrere Fenster) | 868899 u. a. | rollierend | 660k–735k | 53k–890k |
| Big Brother Episoden (3×/Woche) | 913076 ff. | rollierend | 25–500 | 0–1 200 |

Kein offenes All-In-Event (E287 wird nach Serienmuster 1–3 Tage vor Drop
angelegt; Umschalt-Poller läuft, §6). MrBeast-Gaming (913372) läuft; Lemonade
Stand und Hot Ones seit Ende Juli ohne neue Events (schlafend, nicht
eingestellt). Emmys 14.09. mit Props („Will anyone insult Trump…“, liq 2 893).
VMAs (27.09.): noch nichts gelistet.

### 2.2 Strukturbrüche seit unserer Juli-Kalibrierung

1. **Liquiditätskollaps der Klasse:** All-In Jan 415k$ → 31.07. 8.0k$ →
   07.08. 18.9k$ → 14.08. 5.3k$ → 21.08. 4.9k$ (Serie 11300, bestätigt).
   Kapazität je Event für uns real: kleine Clips, Maker bevorzugt.
2. **Gebühren:** Polymarket ist nicht mehr gebührenfrei. Taker-Gebühr
   `Anteil·p·(1−p)` (Kategorie-Sätze ~0.04–0.05, Krypto 0.07; Geopolitik
   frei; US-Börse eigenes Schema mit Maker-Rebate). Maximum genau im
   Zweifel-Fenster p≈0.5 — dieselbe Rechnung wie in
   `KALSHI_MENTIONS_ANALYSE_2026-07-29.md` §3.2 gilt jetzt auch hier.
   Unsere On-chain-PnL (AXP +60.06 usw.) war bereits netto. Konsequenz in §3.
3. **Regulierung:** CFTC prüft Mention-Märkte seit ~13.08. (Auslöser: Fall
   Perez — ~90k$ Gewinn mit Vorwissen aus vorbereiteten Redetexten; von
   Kalshi selbst gemeldet). Kalshi hat alle SPORT-Mention-Märkte gezogen,
   politische/Earnings-Mentions laufen weiter. Polymarket führt Mentions nur
   im Offshore-Buch. **Delisting-Risiko ist der wahrscheinlichste
   Endzustand dieser Kante — nicht Wegarbitrierung** (Einordnung §5).
4. **Kalshi-Zugang Deutschland:** Laut Kalshi-Hilfeseite ist International-
   Zugang für ~143 Länder inkl. Deutschland offen (Frankreich/Spanien u. a.
   gesperrt). Das würde den offenen Blocker aus der Kalshi-Analyse lösen —
   vor Kontoeröffnung Member Agreement selbst prüfen (Phase 0 dort).

## 3. Edge-Profil: was bei uns belegt trägt — und was die Literatur dazu sagt

**Lebende Kanäle (eigene Messungen):**

1. **Basisraten vor dem Drop** (kein Latenzrennen): Curtis E3 — Taker-Fills
   Secret/Paranormal/Rick, Wallet-Delta der Periode +142.94 pUSD; Gegenseite
   nachweislich generische Bracket-MMs ohne Show-Wissen.
2. **Aufmerksamkeits-/Zweifel-Fenster live**: alle 3 Bot-Fills (AXP
   Luxury/Fraud +60.06, PayPal Users) aus Antizipierer-Irrtümern, nie aus
   Erst-Erkennung.
3. **Hybrid Mensch+Maschine**: Graham — 8/11 live verifiziert, User-Käufe im
   Stall-Blindfenster +6.90.

**Tote Kanäle (eigene Messungen):** reines Latenzrennen auf gehörte Wörter
(Markt 1–4 s, wir +17–20 s), Elon/Trump-Post-Wochen (3 Null-Fill-Wochen,
Ask-Seite verschwindet), ISW-Sofortreaktion (Buch in 6 s leergefegt,
dedizierte 5-s-Bots; Messstrecke läuft weiter unter Protokoll, N=4/10).

**Externe Evidenz 2025–2026, die das Profil stützt (Quellen §7):**

- **Maker-Ausführung ist die Meisterkante:** 222M-Trades-Studie — gute
  Prognostiker verlieren (kommen spät, zahlen Spreads), automatisierte
  Maker holen ~2.5 c/Kontrakt. Deckt sich mit unserem Curtis-Playbook.
  Regel ab jetzt: jeden Einstieg als ruhende Limit-Order versuchen.
- **NO-Seite/Longshot-Überpreisung ist real und dort am stärksten, wo wir
  handeln:** Polymarket-Dezil 0–10 c Rendite −0.23 %, 80–90 c +0.98 %;
  Kalshi-Käufer von Sub-10c-Kontrakten verlieren >60 %. Kurzlaufende
  wiederkehrende Märkte lösen das Carry-Problem der NO-Seite. Stützt die
  Late-NO-Kette (Nachbarschafts-Filter + Zwei-Methoden-Konsens bleiben
  Pflicht, Befund 28.07.).
- **Whale-Flow in Mention-Märkten hat NEGATIVE Kante** (Studie über 5 456
  Märkte): große aggressive Orders in unserer Klasse sind Kontra-Signal,
  kein Informationssignal. Operativ: nicht von großen Prints schrecken
  lassen; eher Gegenseite stellen.
- **Count-Ladders bleiben in Rändern schlagbar:** dokumentierter Retail-Fall
  118k$ über 1 943 Trades mit 1–2-c-Tails am Montag-Open; Pace-Bots preisen
  die Mitte, verpreisen aber Varianz/Regimewechsel und Ladder-Kohärenz.
- **Regelkanten („settlement lawyering“)** sind eine belegte eigene Klasse
  (Shutdown-Leiter: 97-c-Sprosse → 1 c wegen OPM-Quelldatum). Passt zu
  unserer Quellzeit-Disziplin; als Overlay hoch, als Standalone wegen
  UMA-Tail klein halten.

## 4. Thesen mit Direktanalyse

### T1 — President Curtis E6 (So 30.08., Event 913373): Basisraten schlagen Bracket-MMs — erneut

Transkripte E1–E5 gezogen und E6-Zielwörter deterministisch gezählt
(`curtis_basisraten.py`; exakte Wortgrenzen, case-insensitive), danach
Kontextfenster-Verifikation gegen Synopsis-Boilerplate (`curtis_kontexte.py`).
**Methodik-Vorbehalt:** Seiten enthalten Episoden-Synopsen der jeweils anderen
Episoden; Rohwerte sind Screening-Werte. Dialog-Kontrolle vor Orders bleibt
Pflicht (Prereg-Methode E3).

| Wort (Schwelle) | E1 | E2 | E3 | E4 | E5 | Kontext-Befund | Markt bid/ask 27.08. | Einschätzung |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Leprechaun (1) | 3 | 3 | 2 | 2 | 0 | **echt** — O'Doyle ist Half-Leprechaun (Running Gag) | 0.36 / 0.55 | **YES-Kandidat**, p̂≈0.7–0.8; vorher E6-Promo prüfen |
| God (5+) | 8 | 11 | 11 | 6 | 11 | echt (Dialog) | 0.28 / 0.86 | 5/5 über Schwelle; **Maker-Bid ~0.55–0.65**, Taker 0.86 dünn |
| President (10+) | 27 | 21 | 20 | 16 | 14 | inkl. ~4–6 Boilerplate/Seite → bereinigt ~22/16/15/11/9, fallender Trend | 0.55 / 0.57 | p̂≈0.6–0.7 → kleiner YES-Kauf vertretbar |
| Monster (1) | 3 | 24 | 4 | 2 | 4 | E4-Treffer = Boilerplate; sonst echt → 4/5 | 0.02 / 0.80 | **Maker-Bid ~0.40–0.50**; Taker 0.80 nein |
| White House (1) | 8 | 0 | 0 | 3 | 3 | echt, 3/5 | 0.08 / 0.98 | Maker-Bid ~0.30–0.35 (E3-Playbook) |
| Bank (5+) | 21 | 11 | 13 | 18 | 15 | **fast alles Figurenname „Banks“**; „bank“ singulär 0–1/Episode | 0.02 / 0.14 | **Regelkanten-Spekulation**: zählt der Resolver „Banks“ (Name, phonetisch = Plural)? Regeltext sagt nur „says the listed term“. Guidance/Agentic-Präzedenz = Resolver werten großzügig/phonetisch. Kleiner Clip, ausdrücklich Dispute-Risiko |
| CIA (1) | 18 | 1 | 1 | 1 | 1 | E2–E5 = Boilerplate (E1-Synopsis auf jeder Seite) → echte Rate 1/5 | 0.06 / 0.96 | kein Trade (bid fair) |
| Worm (1) | 0 | 3 | 0 | 0 | 0 | echt nur E2 | 0.934 / 0.998 | **nicht fadem** — 0.93 gegen Basisrate 1/5 = jemand kennt den E6-Inhalt (Presse-Screener existieren, E3-Lektion) |
| Security (1) | 2 | 1 | 2 | 1 | 1 | echt, 5/5 aber knapp | 0.83 / 0.97 | fair, kein Puffer |
| Hell (1) | 4 | 5 | 6 | 9 | 3 | echt, 5/5 | 0.996 / 1.00 | erledigt (Markt weiß es) |
| Rick (1) | 2 | 0 | 0 | 0 | 0 | echt nur E1 | 0.07 / 0.96 | kein Trade |
| Agent (5+) | 4 | 0 | 9 | 1 | 0 | echt, stark episodenabhängig (E3 = Secret-Service-Plot) | 0.20 / 0.92 | nur nach Promo-Info |

Regeltext E6 (gegen gelesen, `curtis_regeln.py`): Musik und
Recap/Preview-Segmente zählen nicht; Quelle ist der Initial-Release; „not
air“-Markt 0.005. Ablauf wie Prereg E3: **Promo-Clip zuerst** (Worm/Leprechaun
prüfen!), Taker nur bis Top-Level, Maker-Clips klein (adverse Selektion durch
Screener), Prereg-Tabelle VOR Orders einfrieren, Post-Air-Sweep Mo früh mit
Zwei-Methoden-Konsens. Kapitalrahmen analog E3 (~60–130 USD).

### T2 — All-In E287 (Drop Fr 28.08.): Pre-Drop-Basisraten statt Latenzrennen

Neu aus unseren eigenen Archiven (`jre_brackets.py` über
`resolutions_allin_*.json`, 6 Wochen): wiederkehrende Brackets haben stabile
YES-Quoten —

| Bracket | YES-Quote | Bracket | YES-Quote |
| --- | --- | --- | --- |
| Hundred/Thousand/Million 10+ | **5/5** | SpaceX 3+ | 4/5 |
| Software | **5/5** | NVIDIA | 4/5 |
| Innovation | **4/4** | Disruptive | **0/4** |
| IPO | **4/4** | Alignment | 0/3 |
| AI 35+ | **3/3** | Canada | 0/3 |
| Anthropic (1 bzw. 5+) | 2/2 und 2/2 | Stock Market | 1/5 |

**Playbook morgen früh:** Sobald der Umschalt-Poller das echte E287-Event
gezogen hat (Verifikation §6), Opening-Quotes gegen diese Tabelle stellen:
YES kaufen, wo Dauerbrenner unter ~0.75–0.80 quotiert sind (E3-Curtis-Muster:
MMs seeden generische Priors); NO nur, wo Nullraten-Wörter über ~0.30 stehen.
Kleine Clips (Serien-Volumen nur noch ~5k$), Maker bevorzugt. Der Bot deckt
danach den Drop selbst ab (Zweifel-Fenster-Kanal). Kein neuer Code nötig.

### T3 — JRE ist zurück (Event 913395, Woche 31.08.): dieselbe Pre-Drop-Logik

Unsere 4 archivierten JRE-Wochen geben Basisraten; aktuelle Quotes dagegen:

| Bracket | Historie | Markt 27.08. | Lesart |
| --- | --- | --- | --- |
| People 200+ | 2/4 | 0.28 / 0.30 | **YES-Kandidat** p̂≈0.5 (n=4! kleine Clips), stark gast-/längenabhängig |
| People 100+ | 4/4 | 0.84 / 0.89 | Maker-Bid ~0.85; Taker dünn |
| Alien | 3/4 | 0.39 / 0.70 | Maker-Bid ~0.45–0.50; Gast-abhängig |
| Left / Right | je 4/4 | 0.90–0.99 | fair |
| Trump 10+ | 0/4 | 0.11 / 0.13 | fair |
| Dude 20+ | 1/4 | 0.26 / 0.41 | fair |
| Spy, Microsoft, Obsolete | 0/4, 0/2, 0/3 | 0.03–0.11 Asks | fair |
| Fuck/Fucking 10+ | 2/3 | 0.79 / 0.92 | über Basisrate — kein YES |

Die Preise sind deutlich vernünftiger als bei Curtis — Kante klein, aber
vorhanden; Haupthebel ist die **Gast-Konditionierung** (Gast bekannt →
Basisraten je Gast-Typ aus unseren Tapes/Transkripten). Drop meist Di;
Orders davor. Latenzrennen am Drop bleibt tot (jre_july6-Befund).

### T4 — Speech-SAY-Dauerstrecke: das ganzjährige Substitut für die Earnings-Saison

Die sprechergebundene earnings_bot-Strecke (ECAPA, Stall-Selbstheilung,
Fenster-Modus, Hybrid) ist gebaut und validiert — der Kalender liefert
laufend Events:

1. **Morgen 28.08.:** Trump-NASA (33k liq — mittelpreisige Trump-Klassiker:
   Flag 0.57/0.79, Century 0.50/0.56, Far Side 0.43/0.49) und Warsh-Jackson-
   Hole (26k liq — Framework 0.71/0.74, Regime 0.68/0.73, Productivity
   0.76/0.78). Kapazität beachten: All-In-Drop ist am selben Tag. Vorschlag:
   NASA als Bot-/Hybrid-Lauf (Trump-Profil trägt), **Warsh nur als
   Rekorder + Messexperiment**: die Fed publiziert Redetexte zum
   Redebeginn — messen, ob/wie schnell die Bücher auf den TEXT-Drop
   reagieren (Analogie ISW-Krasnoiarske). Ergebnis füttert direkt T4.2.
   Vorher Redezeiten an der Quelle verifizieren (Memory-Regel Drop-Zeit).
2. **Fed-Pressekonferenz 16.09. (FOMC):** Kalshi `KXFEDMENTION-26SEP` ist
   bereits offen, 46 Wortmärkte bekannt (Shutdown, Stagflation, Recession,
   Balance Sheet, Truflation, …), Bücher noch leer. Drei Wochen Zeit für
   Basisraten aus den Warsh-Pressers/Reden (Transkripte federalreserve.gov)
   — dann Erstquotes gegen Priors handeln, sobald geseedet; Polymarket legt
   sein Pendant erfahrungsgemäß näher am Termin an. Juli-Messung: Fed-Event
   war das volumenstärkste Mention-Objekt auf Kalshi (300k+ Kontrakte).
   Kalshi-Zugang: §2.2 Punkt 4 (Deutschland wohl möglich, selbst
   verifizieren; sonst Polymarket-only + Kalshi read-only als
   Divergenz-Signal, Phase-1-Recorder existiert).
3. **Leavitt-Briefing-Serie (759033):** strukturell attraktiv (wiederkehrend,
   10k liq), aber aktuell dominiert der Meta-Markt „no briefing by Aug 31“
   (bid 0.65) alle Wortpreise — die Serie ist gerade eine Terminwette.
   Beobachten; scharf erst, wenn Briefings wieder regelmäßig laufen.
   Info-Kante für Handarbeit: das WH-Tagesprogramm kündigt Briefings
   morgens an → Wortmärkte repricen dann massiv.
4. **Monatsaggregate** („What will Trump say in September“ 918328, 11k liq;
   companies/places-Varianten): Basisraten aus 2 Monaten Reden/Transkripten
   berechenbar, Monatshorizont = kein Latenzdruck. Mittlere Priorität,
   saubere Quant-Hausaufgabe.
5. **Emmys 14.09.** (Props inkl. „insult Trump“ 2.9k liq): Live-Broadcast +
   unsere Live-Strecke; klein, Kalender-Eintrag genügt. VMAs 27.09. noch
   leer.

### T5 — Elon-#tweets-Ladders: Screen ernüchternd, dokumentierte Restkante notiert

Eigener Konsistenz-Screen (`thesen_details.py`, Mittelpunktmethode über 5
parallele Fenster): implizite Raten 26–31 Tweets/Tag über alle Fenster,
Bracket-Summen 0.98–1.02 — **die Mitte ist straff und konsistent gepreist**
(vol24h bis 890k$, klar Bot-dominiert). Kein Einstieg auf Mittel-Brackets.
Dokumentierte Restkanten (extern): 1–2-c-**Tails am Montag-Open** (dünne
Bücher vor Pace-Information), Varianz-/Regime-Fehlpreisung der Pace-Bots,
Ladder-Kohärenz. Unser X-Poller könnte einen Live-Count liefern; trotzdem
nur Beobachtungsliste — Konkurrenz dort ist professionell, unsere
komparative Stärke liegt in T1–T4.

### T6 — Screens verworfen bzw. Backlog

- **Weather/Temperatur** (auch München 78k$/Tag): Public-Data-Modellspiel,
  Kanten 2023 ~10 pp → 2026 ~3 pp, Open-Source-Bots dominieren. Kein Fit.
- **Sports/Esports/Krypto-Preisleitern:** Stadion-Feeds bzw. CEX-Latenz —
  strukturell verloren für uns. (Randnotiz Kalshi-„Endgame-Insurance“
  ist belegt, aber neue Venue + neues Feld — Backlog.)
- **Big Brother Mentions:** Liquidität 25–500$ — zu dünn.
- **NYT-Front-Page-Woche** (918355, 3.1k liq): deterministische Textquelle,
  Basisraten aus Front-Page-Archiven berechenbar („Fear“ 0.52/0.89!),
  hübsche Mini-Quant-Aufgabe — Backlog hinter T1–T4.
- **Longshot-Mean-Reversion-Basket** (QuantPedia 04/2026, +19–22 % CAR,
  kapazitätsbeschränkt = kontogrößen-passend): systematisch, latenzfrei —
  Backlog, braucht eigenen kleinen Backtest.

## 5. Risiken (neu bewerten, bevor irgendwo aufgestockt wird)

1. **Delisting-/Regulierungsrisiko:** CFTC-Prüfung läuft; Kalshi zog Sport-
   Mentions bereits. Unsere Kante kann per Federstrich enden → keine
   Investitionen, die sich nur über Monate amortisieren; Strecken bevorzugen,
   die vorhandene Infra nutzen (T1–T4 tun das).
2. **Compliance-Hygiene:** Der Perez-Fall definiert die Grenze — Vorwissen
   aus nicht-öffentlichen Quellen. Unsere Kanäle nutzen ausschließlich
   öffentliche Quellen (Transkripte, offizielle Promos, publizierte Karten,
   veröffentlichte Redetexte); das so dokumentiert halten (Prereg-Stil).
3. **UMA-/Regelkanten-Tail:** Bank/„Banks“-Trade nur als bewusste
   Kleinst-Spekulation; Streitmärkte grundsätzlich meiden (Domer-Regel),
   Kalibrier-Lektionen Guidance/Agentic gelten weiter.
4. **Kapazität & Gebühren:** 5k$-Events vertragen keine 100er-Clips als
   Taker; Maker-first ist jetzt auch gebührenseitig geboten (Taker-Fee-
   Maximum bei p≈0.5 = genau unser Zweifel-Fenster).
5. **Basisraten-Stichproben sind klein** (n=3–6): Clip-Größen entsprechend;
   Prereg vor Orders einfrieren, damit die Brier-Auswertung sauber bleibt.
6. **EU-Rahmen:** Frankreich/Belgien blocken Polymarket bereits; DAC8 macht
   On-Ramp-Flüsse ab 2026 steuerlich sichtbar. Kein akuter Blocker für
   Deutschland, aber im Blick behalten.

## 6. Nächste Schritte (datiert)

1. **Heute/Fr früh:** All-In-Verifikation vor dem Drop —
   `gamma_event_snapshot.json` muss event_id ≠ 873145 und einen
   „august-28“-Slug zeigen (Poller PID 27636 lief heute 17:30 an; Stand
   heute Abend erwartungsgemäß noch Platzhalter, kein neues Event gelistet).
   Dann T2-Playbook: Opening-Quotes gegen die Basisraten-Tabelle.
2. **Fr:** Entscheidung NASA-Lauf (Bot/Hybrid) + Warsh-Rekorder-Experiment;
   Redezeiten an der Quelle verifizieren.
3. **Fr/Sa:** Curtis-E6-Prereg schreiben (Promo-Clip zuerst; Kandidaten
   Leprechaun, God-Maker, President-10+ klein, Monster-Maker, White-House-
   Maker; Bank-Regelkante nur bewusst klein) — Orders vor So-Abend.
4. **Mo früh (31.08.):** Curtis Post-Air-Sweep (Zwei-Methoden-Konsens);
   danach JRE-Orders für die 31.08.-Woche (People-200+-Kandidat, Maker-Bids)
   vor dem Di-Drop.
5. **Bis 16.09.:** Fed-Presser-Basisraten aus Warsh-Transkripten rechnen;
   Kalshi-Member-Agreement (Deutschland) prüfen → Phase 3b (API-Key/Demo)
   oder Polymarket-only-Pfad festlegen.

## 7. Quellen der Web-Recherche (Auswahl, geprüft 27.08.)

Regulierung/Landschaft: NPR 13.08. (CFTC-Prüfung, Fall Perez), CNBC
14./20.08., crypto.news 14.08., CFTC Enforcement Advisory 9185-26 (Feb 2026,
Insider-Präzedenz Event-Contracts), Shift-Markets-August-Brief (US- vs.
Offshore-Volumen), docs.polymarket.us/fees + /changelog (US-Gebühren seit
01.07.), crypticorn.com/predictionhunt.com (Offshore-Gebühren seit Jan/März).
Evidenz Edges: arXiv 2606.04217 (Polymarket-v1, Dezil-Renditen, Fee-Rollout),
Whelan UCD/GWU (Kalshi FLB, Maker vs. Taker), SSRN 5910522, arXiv 2602.19520
(Kalibrierung nach Horizont/Domäne), Benzinga zu Della Vedova 2026
(Ausführung schlägt Prognose, 2.5 c/Kontrakt), Klement/SSRN 6322678
(Whale-Flow in Mention-Märkten negativ), Bitget (Prexpect-Tails 118k$),
arXiv 2508.03474 (Sum-to-one-Arb), QuantPedia 04/2026 (Longshot-Mean-
Reversion), OddsShopper (Settlement-Regeln, Shutdown-Fall), Kalshi-Help
(International-Zugang). Vollständige Links in den Agent-Reports der Session.

## 8. Erweiterung 28.08.: Nicht-Mention-Klassen — das Quellen-Watching-Muster verallgemeinert

Auftrag Autorin 27./28.08.: Aktionsradius über Mentions hinaus, Vorbild
ISW-Kartenänderung. Datenbasis: Gamma-Inventar + Regeltexte
(`nicht_mention_inventar.py`, `regeln_nicht_mention.py`, `capture_familie.py`)
und ein Evidenz-Research-Durchgang (Quellen in §8.6). Das Muster: **ein Markt
löst über eine spezifische öffentliche Quelle auf, die zu erkennbaren
Momenten aktualisiert; wer die Quelle schneller pollt ODER besser liest,
gewinnt die Überraschungsfälle.** Wichtigster externer Befund: In
SCOTUS-Drops, NHC-Recon, TSE-Brasilien und Court-Dockets ist **kein einziger
dokumentierter Bot-Sniper** auffindbar — das sind belegte Märkte mit
pollbaren Quellen, aber (noch) unbesetzte Nischen. Gegenwarnung: In
Ankündigungsmärkten kann die „Überraschungsseite" des Buchs aus Insidern
bestehen (Nobel-2025-Fall: Käufe ab 11 h vor der Verkündung, Leck-Ermittlung).

### N1 — DeepState-Vorlauf in der ukraine-map-Familie (unsere Strecke, neuer Hebel)

Direkt verifiziert: Die großen „Will Russia capture [Stadt] by…"-Leitern
(**Kostyantynivka liq 199k**, Sumy 16.8k, Lyman 22.7k, Shevchenko vol24h
16.3k) tragen den Tag `ukraine-map`, lösen über die **ISW-Karte** auf — und
nennen **DeepStateMap als offiziellen Fallback**. DeepState aktualisiert
mehrmals täglich, Stunden vor dem ISW-Tagesupdate. Unsere Stinky-Forensik
zeigt: Der Markt lag 90 min flach und sprang erst in der
ISW-Publikationsminute — **den DeepState-Vorlauf handelt bisher niemand**
(n=1-Beleg). Das Rennen findet an der falschen Quelle statt.

**Vorschlag (read-only, protokollkonform):** DeepState-Rekorder als
Mess-Amendment neben `isw_ukraine` — DeepState-Änderungen mit Zeitstempel
loggen, gegen die spätere ISW-Publikation matchen, Vorlaufzeit + Trefferquote
+ Fehlalarmrate messen. Zusätzlich die capture-all-of-Klasse (bisher bewusst
`nicht_auswertbar`, 16/18 Ablehnungen des Papier-Executors) in die Auswertung
aufnehmen — dort liegt die Liquidität. Beides sind Protokoll-Änderungen →
Entscheidung Autorin (ISW_VORLAUF_MESSPROTOKOLL, Amendment A2). Kein Handel
vor Messphase.

### N2 — Tropen-/Hurrikan-Märkte: der strukturelle ISW-Klon (Saison läuft JETZT)

Mechanik (belegt): NHC-Advisories im festen Takt 03/09/15/21 UTC,
Zwischen-Advisories 3-stündlich bei Landgefahr, **Specials ungeplant**;
Polymarket-Regel: Auflösung über das **initiale Advisory** („regardless of
any later retraction"). Vor-Quelle existiert öffentlich: Recon-Vortex-Daten
(Tropical Tidbits /recon, **10-min-Takt während Missionen**) laufen dem
Advisory um Stunden voraus. Dokumentierte Bots: nur in Temperatur-Märkten,
**keine in Tropen-Märkten**. Aktuell gelistet (27.08.): TS Saudel
Landfall-Where (liq 9.9k), Dolly/Karina/Lowell strengthen (je 0.25–0.4k),
Cat-4-Landfall US (1.5k), Hawaii (5.8k), Saison-Zählmärkte. Polymarket-Bücher
dünn, Kalshi tiefer (Zugangsfrage §2.2/4).

**Plan:** Kleiner NHC-/Recon-Poller (Advisory-Seiten + Vortex-Texte) im
Rekorder-Stil, zuerst Messphase über 2–3 Stürme (Vorlauf Recon→Advisory→
Markt-Reprice), dann Kleinst-Clips auf Intensitäts-/Landfall-Sprossen im
Überraschungsfall. Saisonfenster bis November; 24-h-Zyklus passt zu
EU-Zeiten. Aufwand: Poller ~1 Tag auf Rekorder-Basis.
**Dämpfer (28.08.):** NOAA-Saisonprognose ist auf „below normal" revidiert
(El-Niño-Scherung, 7–13 benannte Stürme, 0–2 Majors); Dolly degeneriert
voraussichtlich. Ereignisangebot diese Saison also dünn → Poller-Bau
aufschieben, bis ein realer Landfall-Kandidat existiert; Cat-4-Markt (17.5 %
YES) wirkt eher reich als billig, Buch aber nur 1.5k tief.

### N3 — Shutdown-Komplex 30.09.: Definitionspaar + OPM-Präzedenz (episodisch, hochwertig)

Regeltexte gezogen (28.08.): **801502** „Federal Appropriations Lapse on
October 1?" — Lapse **jeder Dauer, jedes Teilbereichs, ausdrücklich ohne
operative Wirkung nötig** (bid/ask 0.10/0.13, liq 9.9k). **580520**
„Government shutdown by October 1?" — verlangt Lapse **plus** Suspendierung/
Furloughs (0.10/0.14, liq 16.7k). Logisch gilt P(Lapse) ≥ P(Shutdown);
aktuell preisen beide fast identisch — noch keine handelbare Inversion, aber
das Paar wird im September auseinanderlaufen (vol24h heute nur 13 bzw. 0:
Frühphase). Präzedenz Nov 2025 (belegt): „Ende"-Leiter löste über das
**OPM-Website-Datum** auf, die 97-c-Sprosse der Bill-Signing-Nacht ging auf
~1 c, 30M$ Volumen in vier Tagen — Regel-Lesen + OPM-Poller war der ganze
Edge. **Plan:** (a) Paar-Monitor (täglich, trivial), Einstieg nur bei
materieller Definitions-Inversion; (b) WENN Lapse eintritt: Die dann
gelistete End-Datum-Leiter ist unser Spielfeld — opm.gov-Poller steht in
einer Stunde, Regeltext zuerst; Konkurrenz wird größer sein als 2025 (Fall
ist publik), aber Intraday-Granularität + Regel-Literalismus bleiben.

**Lage-Update (28.08., belegt):** Beide Kammern haben bereits Clean-CRs
verabschiedet (House 21.07. → 04.12.; Senat 08.08., 90–6 → 11.12.),
Reconciliation nach dem 31.08.; beide Seiten wollen keinen Shutdown vor den
Midterms. Konsequenz: (a) Die 30.09.-Sprossen (~11.5–12 % YES) sind eher
Zerfallskandidaten — NO bei 0.86–0.90 liegt genau im belegten
Favoriten-Dezil (+0.98 %), kleine Position vertretbar, Restrisiko
Reconciliation-Streit; (b) **die echte Klippe wandert auf den 04./11.12.** —
dieselbe OPM-Falle, mit Vorlauf zum Vorbereiten (Poller + Regeltexte).

### N4 — Brasilien-Komplex 04.10. (+ Stichwahl 25.10.): Basisraten + TSE-Nacht

Polymarket löst **ausschließlich über TSE** auf; TSE publiziert über
öffentliche JSON-Endpunkte, 2022-Präzedenz ~2 h bis Fast-Vollzählung,
Zählung ~20–23 Uhr MEZ — EU-freundlich. Kein dokumentiertes TSE-Sniping
2022. Heute gelistet: Hauptmarkt 45915 (**liq 14.6M**, vol24h 3.6M),
**Staaten-Leitern „1st Place in [Staat]" je liq 100–160k bei vol24h unter
5k** — dünn gehandelte Nebenmärkte mit dicker Liquidität, „Outright-Win
erste Runde" 76k, Bank-of-Brazil-Entscheid 15.09. (26k). Zweistufiger Plan:
**(a) Wochen vorher:** Basisraten je Staat aus brasilianischen
State-Crosstabs (Quaest/Datafolha/AtlasIntel) gegen die Staaten-Leitern —
reine Curtis-Logik, keine Latenz. **(b) Wahlnacht:** TSE-JSON-Poller
(Rekorder-Muster) auf Staatsebene; obskure Staaten sind effektiv entschieden,
bevor dünne Bücher reagieren. Bekannte Zähl-Dynamik (frühe Tallies regional
verzerrt) ist eine „besser lesen"-Kante obendrauf. Konkurrenz im Hauptmarkt
sicher, in Staaten-Leitern unbekannt/dünn.

**Lage (28.08., belegt):** Hauptmarkt inzwischen 137M$ Volumen; Preise Lula
59.5 % vs. Flávio Bolsonaro 35.25 % (Jair unwählbar, Registrierung seit
15.08. zu). Quaest 10.–13.08.: 1. Runde Lula 38 / F. Bolsonaro 31;
Stichwahl-Simulation nur noch 43–40 — Richtung statistisches Patt, während
der Markt 59.5 preist. Die 2022-Dynamik (frühe Auszählung verzerrt Richtung
Bolsonaro, kippt spät zu Lula) wiederholt die Crowd erfahrungsgemäß jede
Runde — ein regionen-gewichtetes Live-Modell auf dem TSE-Feed schlägt sie.
Zweiter unterschätzter Ausgang: Outright-Sieg >50 % in Runde 1 beendet
alles am 04.10. (Markt 45924, 76k liq).

### N5 — Ankündigungs-Familie am Truth-/WH-Poller (vorhandene Infra, gebührenfrei)

Geopolitik/Politik ist die **gebührenfreie** Kategorie. Bestand (28.08.):
Iran-Blockade-Ende-Leiter **liq 810k, vol24h 723k** (Sep 0.27/0.28, Okt
0.50/0.52, Dez 0.69) — Auflösung „US-Regierung oder autorisierter Vertreter
verkündet öffentlich" = Truth-Post zählt mutmaßlich; US-Iran-Ceasefire-
continues 491k; Mobilisierungs-Leiter 133k (straff gepreist); **Pardon-Märkte:
„Who will Trump pardon before 2027" liq 317k; „pardon anyone by…"-Leiter mit
toten Curtis-Spreads: Sep 0.18/0.84, Okt 0.34/0.74**. Auflösung Pardons:
offizielle US-Quellen + „consensus of credible reporting"; Ankündigungen
laufen Truth-Social-first → unser 15–32-s-Poller ist direkt wiederverwendbar.

**Ehrliche Einordnung:** Das Latenz-Sniping der Ankündigung selbst ist
derselbe verlorene Kanal wie bei Elon-Posts (Asks verschwinden). Die
handelbaren Kanäle sind: (a) **Basisraten auf die toten Spreads** — Achtung,
erster Check (28.08.) zeigt Spannung: Trump ist historischer Rekord-Begnadiger
(70+ Fraud-Clemencies, DOJ-Liste zuletzt 06.07. aktualisiert), aber die Leiter
impliziert ~8 Wochen Pause (Juli-Sprosse NO, Aug 0.03/0.06). Hypothese
Wahlkampf-Pause bis nach den Midterms 03.11. — die DOJ-Grant-Daten 2026
auszählen (Inter-Arrival-Verteilung, 30-min-Aufgabe) BEVOR die Okt-Sprosse
0.34/0.74 als billig gilt; die DOJ-Seite selbst ist die pollbare Quelle; (b) **NO-Theta auf nahe Sprossen** ohne
Newsflow-Anzeichen; (c) **Regelkanten** (welche Quelle zählt wann — der
OPM-Fall als Vorbild). **Meiden:** Nominierungs-Märkte (Leak-getrieben,
Warsh-Fall: 31→81 % am Abend vor der offiziellen Verkündung).

**Klausel-Detail Iran-Ceasefire (871083, gezogen):** Bruch nur durch
US-Schlag direkt auf iranisches Territorium/Binnengewässer; Marine-Zwischen-
fälle, Proxy-Schläge, Cyber, Abfangaktionen zählen NICHT — Headline-Spikes
auf der NO-Seite sind regelmäßig falsch → Klausel-Literalismus als
Fade-Kanal. Legs aktuell: 15.09. 88 %, 30.09. 79 %, 31.10. 71 %.
UNGA-Woche 22.–28.09. ist das Katalysatorfenster der Iran-Legs.

**Sofort-Check gefunden:** Zwei Ukraine-Ceasefire-Events preisen dieselbe
Okt-31-Deadline **8.5 % (478472, „agreement") vs. 15 % (486199)** — vor
jedem Arb-Gedanken beide Regeltexte diffen (Definitionsunterschied
wahrscheinlich; wenn nicht → echte Inkohärenz).

**Nobel-Friedenspreis 09.10., 11:00:00 MESZ (Event 60182, liq 2.0M):**
Zwiespältige Evidenz — kein Favorit über 9 %, sekundengenauer Livestream-
Drop um 5 Uhr ET (US-Crowd schläft), nominell 50 Jahre Geheimhaltung; ABER
Okt-2025-Präzedenz: frische Konten kauften die Siegerin ab ~11 h vorher
(Leck-Ermittlung). Handelbar allenfalls klein: Livestream-Latenz +
Fade der politisch motivierten Trump-YES-Pumps; nie gegen späten
Konten-Zufluss halten (kann Leck sein).

### N6 — Backlog mit Datum bzw. Venue-Bedingung

- **SCOTUS-Opinion-Days ab Oktober:** Termine vorab bekannt, PDFs ab 10:00 ET
  im ~10-min-Takt, Ergebnis auf Syllabus-Seite 1 parsebar; Markt-Repricing
  lief 2025/26 über Menschen (Liveblogs). Poller + Syllabus-Parse =
  Zehner-Sekunden-Vorsprung. Bauen, wenn der Herbst-Docket-Marktbestand
  steht. Emergency-Docket nebenbei per 60-s-Orders-Poller.
- **Kalshi-Klassen hinter der Zugangsfrage:** Rotten-Tomatoes-Embargo-Lifts
  (manuelle Crowd, echtes Volumen, reines Seiten-Polling — bester Neuzugang
  laut Evidenz), Court-Docket-Märkte via CourtListener-Webhooks.
  Charts-Märkte (Spotify/Billboard) nur mit Manipulations-Bewusstsein
  („Earrings"-Fall: 3M$-Markt auf gefakten Streams settled).
- **App-Store-Ranking-Märkte** (täglich, deterministische Chart-Quelle, liq
  ~9k): Mikro-Kandidat für einen Feierabend-Poller.
- **GTA-VI-Delay-Zerfall (74872, 750k vol, 8.5 % YES, Ende 19.11.):** Beide
  bisherigen Verschiebungen wurden ≥5 Monate vorher verkündet; <3 Monate vor
  Release ist ein neuer Delay historisch präzedenzlos → NO @~0.915 mit
  planbarem Zerfall über Gone-Gold-/Preload-Signale (Rockstar-Newswire-
  Poller = unsere Mechanik). Klein, sauber.
- **„Will Trump publicly insult…"-Monatsserie (759201, 948k vol!):** kein
  fester Termin, aber mechanisch identisch mit unserer Transkript-Zähl-
  Nische — als Füller zwischen Terminen prüfen (gehört inhaltlich zu T4.4).
- **Time Person of the Year (Mitte Dez, 528018):** nur 38k Volumen bei
  **628k Liquidität** = Maker-freundliches tiefes Buch; Leak-anfällig
  (Morning-Show-Reveal). Dezember-Backlog.
- **Ballon d'Or 26.10. (48361, 31M vol):** Leak-Orbit der französischen
  Presse ist eine echte Latenz-Kante am Wochenende 24.–26.10., aber
  Leak-Klasse = fremdes Terrain; Kane 64 % Favorit. Beobachten, klein.
- **Apple-Keynote 09.09.:** Die laufenden Apple-Märkte sagen „release",
  nicht „announce" — der Keynote-Pop auf Announce-Headlines ist ein
  dokumentierter Fade (release≠announce-Klauseln zuerst lesen).
- **FDA/PDUFA** (dünn, insider-geprägt), **OPEC** (Delegierten-Leaks),
  **WHO** (zu dünn), **CPI-Bucket-Märkte** (nur 10k dünn, Nowcast-Spiel):
  verworfen.

### 8.5 Kalender der planbaren Auflösungsmomente (Sep–Dez, verifiziert 28.08.)

| Datum | Ereignis | Mechanik / Kante | Für uns |
| --- | --- | --- | --- |
| 09.09. | Apple-Keynote | release≠announce-Fade | klein |
| 11.09. 14:30 MESZ | CPI Aug (BLS, sekundengenau) | Kontext für FOMC-Legs | beobachten |
| 14.09. | **Emmys** (~20 Kategorien à 30–55k) | sequenzielle Reveals, Precursor-Basisraten, Kapital rotiert live | mittel, Live-Abend |
| 16.09. 20:00 MESZ | **FOMC + SEP + Presser** — echte Hike-Debatte (Markt: Hold 68.5 / Hike 30.5) | Statement-Latenz gehört den Profis; für uns: Presser-Wortmärkte (T4.2) werden dadurch volatil/wertvoll | **Fed-Mention-Vorbereitung** |
| 22.–28.09. | UNGA-Woche New York | Katalysatorfenster aller Iran-Legs | Klausel-Fades |
| 27.09. | VMAs (Fan-Vote) | Listings kommen erst; Vote-Tracking-Basisraten | beobachten |
| 30.09./01.10. | **Shutdown-Paar** + Iran-Blockade-Sep-Leg (27.5 %) | CR-Lage → Zerfallskandidat; Klippe real erst Dez | NO-Klein + Monitor |
| 04.10. 22:00 MESZ | **Brasilien Runde 1** (TSE-JSON) | Staaten-Leitern + Mirage-Dynamik | **Hauptereignis Okt** |
| 05.10. | SCOTUS-Termbeginn (Suncor 05.10.) | Opinion-Poller bauen, wenn Markt-Bestand da | Backlog |
| 05.–12.10. | Nobelwoche (Peace **09.10. 11:00:00 MESZ**) | Livestream-Latenz + Hype-Fade; Leck-Tail! | klein |
| 25.10. | Brasilien Stichwahl | wie 04.10.; Markt 59.5 vs. Quaest 43–40 | **Hauptereignis** |
| 26.10. | Ballon d'Or London | Leak-Orbit franz. Presse | beobachten |
| 28.10. 19:00 MEZ | FOMC #2 (kein SEP) | wie 16.09. | Fed-Mentions |
| 03.11. | **US-Midterms** — Senat 50.5 % Coinflip, House Dem 88.5 % | Red-Mirage/Blue-Shift-Choreografie; Down-Ballot-Board füllt sich Sep–Okt; County-Benchmark-Modelle | vorbereiten ab Okt |
| 19.11. | GTA-VI-Release | Delay-NO-Zerfall (N6) | klein |
| 04./11.12. | **CR-Klippe (die echte)** | OPM-Falle, mit Vorlauf | **vormerken** |
| 08.–09.12. | FOMC #3 (SEP) · Mitte Dez: Time PotY (628k-Maker-Buch) | | Dez-Backlog |

### 8.6 Gemeinsame Infrastruktur (ein Bau, viele Klassen)

1. **Listing-Wächter verallgemeinern:** Der All-In-Umschalt-Poller als
   generischer Neu-Event-Watcher je Tag/Serie (mentions, ukraine-map,
   Brasilien, shutdown): neue Events binnen Minuten melden → Erstquotes
   gegen vorbereitete Priors (Prexpect-Muster; MMs seeden generisch).
2. **Quellen-Poller-Framework:** ISW-Rekorder-Muster (Takt, Cache-Buster,
   Herzschlag, Wachkontrolle) auf neue Quellen klonen: DeepState, NHC/Recon,
   opm.gov, TSE, supremecourt.gov, DOJ-Pardon-Liste. Die Sechs-stille-
   Fehler-Lektion gilt: jede neue Quelle erst mit Probeläufen gegen den
   echten Endpunkt + „kein Fehler, nur Schweigen"-Checks.
3. **Messen vor Handeln** bleibt Standard: jede neue Klasse startet als
   Rekorder mit Vorregistrierung (Curtis/ISW-Stil), Papier vor Live.

### 8.7 Quellen §8 (Auswahl, geprüft 28.08.)

U. Chicago Law Review „When the Market Watches the Court" (SCOTUS-Repricing);
CRS LSB11391 (Emergency Docket); free.law (RECAP-Alerts/Webhooks); The
Defiant (OPM-Shutdown-Drama Nov 2025, BTC-Reserve-EO-Stall); cryptonews/
tipranks (Shutdown-Quoten Aug 2026); NHC/MIAREPNT2 + tropicaltidbits/recon
(Recon-Takt); pillarlab (Kalshi-Tropen-Tiefe); Kalshi-News (Rotten-Tomatoes-
Kit, Biotech-Pilot 16.07.26); musicbusinessworldwide („Earrings"-Manipulation);
tradetheoutcome (TSE-sole-source); theblock (AP-Konsens-Resolution 2024);
thehill (Midterms ~200M$); Forbes/CoinDesk (Nobel-Insider-Fall); DOJ SDNY
23.04.26 (erste Insider-Anklage Prediction Markets); Finance Magnates
(Bot-Playground, 14/20-Wallets); arXiv 2603.03136 (Arb-Halbwertszeiten).

## 9. Nachtrag 04.09.2026: Thesentests, Daten, Aufbauten

Eine Woche nach der Recherche. Zwischenzeitlich von anderen Sessions
umgesetzt: DeepState-Rekorder (Amendment A2, PR #56), Basis-Anker +
capture-all-of informativ (PR #58), Basisraten-Veto im All-In-Bot und
E288-Armierung (PR #61). Diese Session hat die Thesen gegen echte Outcomes
getestet, die Datenbasis vergroessert und zwei Messwerkzeuge aufgesetzt.
Alle Zahlen: dokumentierte Read-only-Abfragen (Gamma, CLOB
`prices-history`, federalreserve.gov, scrapsfromtheloft), Skripte im
Session-Scratchpad; keine Orders.

### 9.1 Curtis E6 (T1) — Thesentest mit Outcomes

Brier ueber 12 Wortmaerkte: **unser p̂ 0.143 vs. Markt-Mid 0.183**. Aber
der Vergleich gegen Mids toter Spreads (0.02/0.98 → Mid 0.50) schmeichelt:
Gegen die vorgeschlagenen ORDERS gerechnet verloren alle drei Taker-Legs
(Leprechaun YES @0.55 → NO; President 10+ @0.57 → NO; Bank 5+ @0.14 → NO),
gewonnen haetten nur die Maker-Legs (God 5+ YES bei Mid 0.57; Monster YES
bei Mid 0.41), sofern gefuellt. Drei Lehren, die in
`PREREG_CURTIS_E7_2026-09-04.md` eingebaut sind: (1) **Rezenz schlaegt
Gesamtquote** — Leprechaun war 4/5, aber 0/2 zuletzt (Running Gag
ausgelaufen); (2) **„Banks" (Figurenname) zaehlte NICHT als „Bank"** —
die Regelkanten-These aus §4/T1 ist falsifiziert, UMA wertete strikt;
(3) **Rohzaehlungen mit Titel-Boilerplate sind unbrauchbar** — „President"
roh 21 in E6, Markt resolvte NO (<10 im Dialog). E7 „Ghosts" laeuft
So 06.09.; Kandidaten nur Maker: God 5+ (3/3, Bid 0.42), Hell (3/3, Bid
0.52), optional Monster/President-Lincoln-Plot/Worm-Malware-Plot.

### 9.2 Warsh Jackson Hole (T4) — Text-Drop-These BESTAETIGT

Retro ueber CLOB-Minutenhistorie (28.08., 13:30–15:30 UTC) und die
Fed-Redeseite: **Text online 14:00:11 UTC** (Feed-Eintrag 10:00:00 AM,
`Last-Modified` 14:00:11 GMT), **Text-Prognose 20/22 Maerkte korrekt**
(Abweichungen: „Good Morning" = Begruessung ausserhalb des Manuskripts;
„Bitcoin/Crypto" im Text, aber nicht gesprochen/Fussnote). Der Markt
preiste trotzdem **Wort fuer Wort beim Sprechen**: CapEx 0.69 → 0.49 um
14:05 → erst 14:20 auf 0.99; Bank/Asset 10+ Sprung 14:28; Regime 14:11;
„Framework" (0.74, nicht im Text) zerfiel erst ab 14:26 auf 0.045; sieben
mittelpreisige NO-Woerter (Independent 0.53, Too Late 0.565, Payment System
0.48, Community 0.45, Ingenuity 0.40, Gold 0.47, Framework 0.74) waren um
14:00:11 aus dem Text erkennbar. **Das ist die Gegenlage zu Earnings/
Trump-Live (1–4 s): eine Textquelle mit Minuten Vorlauf, die niemand
liest.** Aufgesetzt: `operations/pipeline/fed_text_rekorder.py` (read-only,
Feed- oder URL-Modus, Buch-Nachlauf, `--auswerte`; 11 Tests). Naechste
Gelegenheiten: FOMC 16.09. — Statement 14:00 ET, Eroeffnungs-Statement der
Pressekonferenz 14:30 ET (PDF), jede Warsh-Rede mit Polymarket-Event.
Aufruf im Modul-Docstring; Messphase zuerst (Protokoll wie ISW), kein
Order-Pfad.

### 9.3 Basisraten mit echtem n (T2/T3) — Harvester

`operations/analysis/mention_basisraten.py` (13 Tests) zieht je Gamma-Serie
bis 50 aufgeloeste Events und vergleicht mit dem offenen Event (Laplace,
letzte 3, Screening-Label). Ergebnisse 04.09. in
`data/results/mention_basisraten_{jre,allin,curtis}_2026-09-04.json`:

- **JRE (Serie 11275, 32 Wochen):** People 200+ 5/13 (0.40) vs. 0.30/0.32,
  Alien 10/18 (0.55) vs. 0.49/0.52, People 100+ 16/18 vs. 0.86/0.88 —
  **alle 16 Maerkte „fair"**. Die n=4-Kandidaten aus §4/T3 waren
  Stichprobenrauschen. JRE bleibt Beobachtung, kein Handel.
- **All-In (Serie 11300, 31 Wochen):** Software 14/14, Anthropic 12/12,
  Hundred/Thousand/Million 10+ 9/9, IPO 8/8 (E287 brach mit 0 die Serie —
  Polymarket legte fuer den 28.08. nie ein Event an, der Bot zaehlte auf
  dem E286-Brett, 0 Kaeufe). E288 (942921) hat nur liq 392: Maker-Kandidaten
  Nvidia 17/24 (Bid 0.36), SpaceX 3+ 8/9 (Bid 0.32), Blue 7/9 (Bid 0.41);
  Dauerbrenner stehen bei Asks 0.97–0.996 (fair). Nebenbefund: das
  Bot-Veto schluesselt ohne Schwelle (AI 35+/50+ vereint) — als
  Folgeaufgabe geflaggt.
- **Curtis (Serie 12413, 5 Wochen):** siehe 9.1/Prereg E7.

### 9.4 Fed-Presser 16.09. — Prioren aus Warsh-Transkripten

Kalshi `KXFEDMENTION-26SEP` (46 Woerter) ist weiter ungequotet, kein
Polymarket-Pendant gelistet. Aus den Pressekonferenz-Transkripten 17.06. und
29.07.2026 (nur CHAIR-WARSH-Passagen, Kalshi-Variantenregel) — 2/2:
Good Day (nicht „Good Afternoon" 0/2!), Productivity, Balance Sheet,
Restrictive, AI, **Family Fight/Feud** (3 und 4), Central Bank, Shock
(1 und 10), Uncertainty; 1/2: President, Dollar, Oil, Credit, Projection
(nur SEP-Sitzung → 16.09. hat SEP), Pandemic, Egg; 0/2 u. a. Shutdown,
Dissent, Recession, Stagflation, Trump, Bitcoin, Gold, Iran, Japan.
Kontext: FOMC-Markt preist Hike 30.5 % — Dissent/Restrictive/Shutdown
(30.09.) sind topikalitaetsgetrieben, Prioren nur Startpunkt. Aufgabe fuer
die Autorin, sobald Kalshi seedet: Erstquotes gegen diese Tabelle
(Skript `fed_priors.py` im Scratchpad, Ergebnis `fed_priors.json`).

### 9.5 Kleinere Abschluesse

- **Ukraine-Paar** (§8/N5): definitorisch erklaert — 478472 zaehlt eine
  vereinbarte Waffenruhe, 486199 verlangt In-Kraft-Treten plus 10 Tage
  Bestand; 0.135 vs. 0.065 ist konsistent, keine Inkohaerenz.
- **Shutdown-Paar** (N3): auf 0.04/0.06 (Lapse) und 0.016/0.029
  (Shutdown) kollabiert — der NO-Klein-Gedanke der Vorwoche haette 5–8 c
  gebracht; Ordnung Lapse ≥ Shutdown stimmt jetzt. Dezember-Klippe bleibt
  vorgemerkt.
- **Ops:** Wachkontrolle 2/2 wach, All-In-E288-Bot lebt seit 03:41 auf
  Event 942921 (Drop heute Nacht).

### 9.6 Naechste Schritte (Stand 04.09. abends)

1. **Sa/So:** Curtis-E7-Prereg ausfuehren (Promo zuerst, nur Maker).
2. **Sa frueh:** All-In-E288 nach dem Drop annotieren (Memory-Auftrag).
3. **Bis 15.09.:** Fed-Text-Rekorder fuer den 16.09. vorbereiten — sobald
   Polymarket ein Warsh-Presser-Event listet: Event-ID eintragen,
   `--feed-sprecher Warsh --feed-datum 9/16/2026 --ab 2026-09-16T17:55:00Z`
   (Statement 18:00 UTC) als Task im Betriebsordner; parallel Kalshi-
   Erstquotes gegen 9.4.
4. **Wochenlich:** `mention_basisraten` vor jedem All-In-/JRE-/Curtis-
   Listing laufen lassen; Handel nur bei Maker-Kandidaten.
5. **Dez:** CR-Klippe 04./11.12. mit OPM-Poller (N3) vorbereiten.

---

*Methodik-Notiz: Alle Preis-/Volumenangaben sind Snapshots vom 27.08. abends
(CEST), Screening-Qualität. Basisraten-Zählungen deterministisch per Skript;
Boilerplate-Korrekturen wie in §4/T1 ausgewiesen. Keine Kausalaussagen; alle
Wahrscheinlichkeits-Schätzungen (p̂) sind Basisraten-Heuristiken mit kleinem n,
keine kalibrierten Modelle. Vor jeder Order gilt das jeweilige
Prereg-/Runbook-Protokoll.*
