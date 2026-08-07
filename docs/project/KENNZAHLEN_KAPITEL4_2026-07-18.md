# Kennzahlenblatt Kapitel 4 (Stand 18.07.2026)

Zweck: Jede Zahl, die in den Kapitel-4-Ausbau einfliesst, steht hier mit Fundstelle. Erhoben von der Cowork-Session am 18.07.2026 direkt aus den verbundenen Ordnern (ba-thesis, prediction-market-terminal, prediction-alpha-bot). Regel: Nichts gelangt aus dem Gedächtnis in die Thesis, nur aus diesem Blatt. Nicht verifizierbare Angaben sind unten in Punkt 12 markiert.

## 1. Feldtest Mentions-Bot: Bilanz (Wallet-Massstab)

Quelle: `data/results/wallet_abgleich_2026-07-18.json` (Abschrift der Autorin aus dem Polymarket-Aktivitätsverlauf, ohne Adressen).

Gesamteinzahlungen 339.83 USD, Käufe gesamt 492.51 USD, Nettogewinn gesamt 175.09 USD. Je Event: allin_july3 +5.11 (einziger Fill «Birth Tourism», dazu ein manueller Kauf vor dem Drop), jre_july6 0 (keine Fills, Kandidaten eingepreist), allin_july10 +48.24 (IPO, SpaceX, AI, Nvidia, vier manuelle vorzeitige Teilverkäufe, Käufe teils Bot teils manuell nicht trennscharf), jre_july13 0, lemonade_july15 +1.90 (Korea NO), elon_july13 0 (keine Käufe), allin_july17 +119.84 auf 288.09 Einsatz über sechs Märkte, alle Käufe vom Bot (Blue +55.97, Stock Market +45.35, Midterm +24.11, Alignment +13.60, Regulator +2.92, Tension −22.11 als einzige verlorene Wette).

Log-Rekonstruktion versus Wallet: `runs.json` setzt den Deckelpreis an, wo der FAK-Order-Status keinen Fill-Preis lieferte. Log-basiert ergeben sich Einsatz 626.68 und realisierter PnL 45.02 (ROI 7.2 Prozent), Wallet-basiert 175.09 netto. Beispiel Blue E281: Log 147.06 Shares zu 132.36 USD, Wallet real 179.8 Shares zu 123.84 USD. E281-Einsatz: Log rund 360, Wallet 288.09. Der Vorfall ist dokumentiert (Postmortem «Log reconstruction diverged from the wallet statement», Fix: Wallet-Abgleich als Overlay, künftig Fills aus der FAK-Post-Antwort, PR #12).

## 2. Läufe im Detail

Quelle: `prediction-market-terminal/public/data/runs.json` (Aggregat- und Wetten-Felder per Skript extrahiert, Werte gegen Wallet-Overlay konsistent). Achtung: Die publizierte Datei ist aktuell am Ende abgeschnitten (Torn Write, 30'072 Bytes, ungültiges JSON). Zahlen unten stammen aus dem lesbaren Teil, der alle 15 Wetten enthält. Claude Code soll die Datei neu publizieren.

Aggregat: 7 Runs, 15 Wetten, 14 gewonnen, 1 verloren, 0 offen. Sichtbare Ask-Tiefe bis zum Kaufdeckel an den Auslösezeitpunkten summiert 929.87 USD, Einsatz zu sichtbarer Tiefe 67.4 Prozent. Wetten je Run: allin_july3 1, allin_july10 7 (auf 4 Märkten), lemonade_july15 1, allin_july17 6. Märkte mit Position: 12 (1+4+1+6), davon 11 für die gehaltene Seite aufgelöst, 1 dagegen (Tension, NO-Wette, E281).

## 3. Latenzen und Race

Quelle: runs.json Run-Level-Felder (log-basiert, laut Wallet-Abgleich-Hinweis korrekt).

Erkennungslatenz nach pubDate: jre_july13 48 s, jre_july6 79 s, allin_july10 122 s. Ausreisser allin_july3 4162 s (rund 69 Minuten Feed-Cache, danach wurde der URL-Prober gebaut). Erste Entscheidung nach Drop-Erkennung: 52 bis 152 s je Run (allin_july10 52, allin_july3 70, allin_july17 70, jre_july13 104, jre_july6 110, lemonade 152). Erster Fill nach Drop-Erkennung: allin_july10 64 s, allin_july17 70 s, allin_july3 75 s, lemonade_july15 941 s (YouTube-Batch-Pfad, einmalig).

Race gegen das öffentliche Trade-Tape: Bei 11 von 15 Wetten war der Bot der erste Käufer der gehandelten Seite (tape_rang 1). allin_july17: alle 6 von 6, Median-Abstand des nächsten fremden Käufers 1087 s (rund 18 Minuten), Spanne 376 bis 9793 s. allin_july10: 4 von 7, Median-Verfolger 334 s. Nachrückende Liquidität: einzelne Sweeps füllten mehr als die anfangs sichtbare Tiefe (Beleg Blue E281: 179.8 Wallet-Shares gegenüber 147.06 im Log-Snapshot), der geloggte Tiefen-Snapshot ist eine Untergrenze.

## 4. Nicht-Handeln als Befund

elon_july13 (X-Post-Profil): 24 regelkonforme Kaufprüfungen, alle 24 am bereits eingepreisten Ask gescheitert, null Käufe (runs.json zaehler.no_action=24, eingepreist=24, bestätigt im Wallet-Abgleich). jre_july6: 35 No-Action-Entscheidungen (20 eingepreist), 0 Trades, Market Maker zogen die Asks beim Drop. jre_july13: 38 No-Action (24 eingepreist), 0 Trades.

## 5. Vorfall-Liste (kuratierte Postmortems)

Quelle: `data/results/mentions_run_postmortems.json` (9+ Einträge, je mit Auswirkung, verifiziertem Fix und Referenz). Auswahl: Fehltrigger Special-Episode Cerebras/BFL (Fix: Playlist-Positiv-Identifikation, nur NEU zur offiziellen Playlist hinzugefügte Drops zählen, RSS nur Muster ALLIN-E<n>). Budget-Schätzung blockierte fünf regelkonforme NO-Chancen (Fix: Budget-Sync gegen echten Wallet-Saldo plus 3 Prozent Fee-Puffer). Market Maker ziehen Quotes beim Drop (Fix: 45-Minuten-Nachlauffenster, Re-Check alle 90 s). Stille Bot-Tode bei Sleep/Session-Ende (Fix: Watchdog als Scheduled Task im 5-Minuten-Takt, PR #2). Watchdog-Fehl-Kill im stillen Nachlauf (Fix: Heartbeat-Events, Commit 8af07d6). Fortran-Runtime-Abbruch beim einzigen Bot mit Sprecher-Verifikation (Fix: Env-Variable, PR #8). Log-Wallet-Divergenz (Fix: Wallet-Overlay, PR #12). Buchlog-Ausfall durch 404 eines aufgelösten Markts, rund 30 h Lücke (Fix: Fehler je Token isoliert, PR #5). Gamma-Limit-Kappung beim Pilot-Watcher (Fix: Zwei-Fenster-Fetch mit Pagination).

## 6. Regelwerk der Pipeline (Fundstellen operations/pipeline/)

Module: bot.py (Hauptschleife), config.py (Profile und Konstanten), counter_engine.py (deterministische Zählung), decision.py, execution.py (FAK, Budget-Sync), market_rules.py, orderbook.py, rss_watch.py (Prober und RSS), x_watch.py (X-GraphQL), transcription.py, speaker.py und baue_referenz.py (Sprecher), sizing_analyse.py, watchdog.py, elon_bot.py (Post-Profil), run_dashboard.py (Auswertung), dashboard.py.

Konstanten (config.py, Zeilennummern Stand 18.07.): HARD_ASK_DECKEL 0.97 und ASK_OBERGRENZE = min(0.97, p_win − min_edge), Default p_win 0.93 und min_edge 0.03, also EV-Deckel 0.90 (Z. 264 bis 267). NO_ASK_OBERGRENZE 0.80 als separater NO-Deckel, NO nur bei Endstand höchstens 70 Prozent der Schwelle, YES ab Zähler Schwelle plus Puffer 2 (Z. 273 bis 275). ASR_KONFIDENZ_HOMOPHON 0.8, HOMOPHON_BEGRIFFE red/read, blue/blew, right/write (Z. 276, 352). Komposita zählen mit (konservativ, schützt die NO-Seite, Kommentar Z. 155), Akronym- und Varianten-Regeln in config.py (VARIANTEN_MAP Z. 360). Clips: MAX_USD_PRO_MARKT 15, MAX_CLIPS_PRO_MARKT 10 (FAK-Sweeps), MAX_USD_GESAMT je Profil, Default 130 (Z. 284 bis 286). Detection: PROBER_POLL_S 5 (CDN-URL-Prober), RSS_POLL_S 15, YouTube-Feed und Kanalseite, X_POLL_S 16 fürs Post-Profil, Transkription in CHUNK_SEKUNDEN 20 auf GPU (cuda/float16 laut Postmortem-Verifikation) (Z. 292 bis 339). Risiko: STOP-Datei data/live/STOP als Kill-Switch (Z. 9), NACHLAUF_MINUTEN 45 mit NACHLAUF_POLL_S 90 (Z. 347 f.), Watchdog 5-Minuten-Takt mit Neustart-Schutz (watchdog.py, Postmortems), BUCH_LOG_INTERVALL_S 120 als Orderbuch-Recorder (Z. 328).

## 7. Sprecher-Verifikation (Differenzierungsmerkmal)

speaker.py mit speechbrain-Stimm-Embeddings, Referenzaufbau in baue_referenz.py, SPRECHER_SCHWELLE 0.40 (config.py Z. 313 bis 316). Aktiv beim Einzelsprecher-Profil (mrbeast_gaming, laut Postmortem «the only bot with speaker verification», dort auch der behobene Fortran-Vorfall). Zweck: Treffer werden bei Einzelsprecher-Märkten dem Zielsprecher zugerechnet.

## 8. Mikrostruktur (Terminal-Repo)

Recorder: `src/book_recorder.py` plus Recorder-Status im Workspace Microstructure. Imbalance-Studie: `docs/research/imbalance_study_2026-05-30.md`: Basis forward-clean-2026-05-30.db, 173 Tokens, 455'914 gefilterte Snapshots, 451'636 5-Minuten-Paare. Richtungs-Bucket 0.6 bis 0.8: Hit-Rate 62.8 Prozent, Wilson-Untergrenze 56.4 Prozent (n 1590, bewegt 14.5 Prozent). Ausdrücklicher Caveat: ask-lastiges Universum aus dem Arb-Replay, Selektions-Bias, saubere Wiederholung läuft auf Recorder-Daten. MM-Simulator: `docs/research/mm_sim_2026-05-30.md`: 217 Tokens, ehrlich negativer Befund: Spread-Ertrag +1.31 bis +1.43 Cent je Fill wird vom 5-Minuten-Markout −0.78 bis −0.87 aufgefressen (Adverse Selection), Endwert mark-to-mid −54.71 (Skew aus) bzw. −68.30 USD (Skew an), konservative Fill-Regel dokumentiert. Benannter Fix-Pfad: Wiederholung auf den Recorder-Daten (beide Reports), Inventar-Skew nach Avellaneda-Stoikov-Logik bereits implementiert.

## 9. Website-Stand (prediction_terminal.py, WORKSPACES Z. 103 ff.)

24 Workspaces in sechs Navigationsgruppen: Overview; Markets (Markets, Search, Live Trades, Resolved, Cross-Venue); Traders (Traders, Wallets, Whale Flow, Suspicious, Track); Trading (Backtester, Copy Trade, Portfolio); Research (Review Queue, Category Efficiency, Mentions Latency, Live Runs, Microstructure, Pilot, Pipeline Forward, Methodology); System (Monitor, Settings). Hilfetexte (WORKSPACE_HELP) belegen die Funktionen, u.a. Live Runs («bets, latencies, results of our own bot runs, plus sizing simulation and entry calibration»), Microstructure (Recorder-Status, rollende Imbalance, eingefrorene Mai-Studie inkl. MM-Sim), Pilot (vorregistrierter Feldtest, read-only). Neu gegenüber dem Thesis-Text: die Seiten Pilot und Pipeline Forward, die Research-Gruppe als Ganzes. Publikation: `public/data/` mit neun JSON-Artefakten (meta, runs, queue, audit, kategorie_karte, mentions_latenz, postmortems, pipeline_forward, pilot). Letzter Kettenlauf 18.07., 09:16 UTC (Backend mock): Collector ok mit 40 Alerts, Monitor-Refresh und Review-Queue je 25 Fälle. Terminal-Neuerungen laut docs/HANDOFF.md: WebSocket-Fast-Copy für das Paper-Copytrading (PR #26/#27, dedizierter Apply-Worker nach ehrlich dokumentiertem Befund «WS-Median 105 s, API-Fallback überholte den schnellen Pfad»), echtes Google-Login mit fail-closed Settings-Gate, Deploy-Stack Docker/Caddy/Cloudflare.

## 10. Engineering-Reife

ba-thesis: 844 Testfunktionen (`def test_`) in 164 Dateien unter tests/, Stand 18.07. (vor Abgabe exakte pytest-Sammlung laufen lassen, Thesis nennt bisher 640). CI: `.github/workflows/ci.yml` mit ruff-Lint-Gate. PR-Flow belegt durch referenzierte Pull Requests in den Postmortems (PR #2, #5, #8, #12) und im Terminal-HANDOFF (PR #26, #27). Terminal: 442 Testmethoden in 19 Dateien (HANDOFF vom 12.06. nannte 259, seither gewachsen). Betrieb über drei Windows Scheduled Tasks (Terminal, Copy-Daemon, Alert-Scanner) plus Watchdog-Task der Pipeline.

## 11. Arb-Pilot (für die 4.2-Ankündigung)

`public/data/pilot.json` (Stand 18.07., 12:14 UTC): Kennzeichnung «pilot/preregistered», Budget 100 USDC, Einsatz 10 USDC je Trade, Regel-Freeze 18.07.2026, Quelle Protokoll V2, expliziter Hinweis «Signals are rule matches, not recommendations; all trading decisions are made manually by the author». Letzter Watcher-Lauf 10:19 UTC: 1715 geprüfte Märkte, 42 aktive Signale, trades leer. Beispiel-Signale: Halbzeitshow-Verneinungen zu 0.94 bis 0.97 mit Buchtiefe 165 bis 2904 USD, GDP-Bänder, Musk-Tweet-Bänder.

## 12. Datenqualität und offene Punkte

1. runs.json ist als publizierte Datei abgeschnitten (Torn Write). Auftrag an Claude Code: neu publizieren. Der Einbau ist nicht blockiert, alle Zahlen oben stammen aus dem lesbaren Teil plus Wallet-Abgleich.
2. «E281 nachts in etwa einer Minute verarbeitet»: belegbar ist erste Entscheidung und erster Fill 70 s nach Drop-Erkennung (Erkennungslatenz für diesen Run ohne pubDate nicht berechnet). Formulierung entsprechend vorsichtig wählen.
3. HANDOFF.md nennt teils veraltete Stände (15 Workspaces, 259 Tests). Massgeblich sind die direkt erhobenen Werte oben.
4. allin_july10 enthält neben den Bot-Sweeps manuelle Käufe (nicht trennscharf) und vier manuelle Teilverkäufe. In der Thesis als solches ausweisen.
5. Die Kategorien-Latenz-Messung (mentions_latency_metadata.json, 13 Märkte, 12 ausgewertet, Ausschluss allin_next_episode) ist die Mess-Seite von 4.8.3 und bleibt vom Feldtest getrennt.

## Nachtrag vom 29.07.2026: zweite Feldtest-Strecke (Live-Ereignisse 24.-29.07.)

Quelle für alle folgenden Zahlen: docs/project/THESIS_ERKENNTNISSE_LIVE_MENTIONS_2026-07-29.md (Thesen 1 bis 16), dahinter die Runbooks (*_ARMIERUNG.md), UEBERGABE_2026-07-28_LIVE_MENTIONS.md (§4-Kalibriertabellen) und die Event-Logs je data/live/-Ordner. Ereignisse: Earnings-Calls American Express, PayPal, Boeing, Procter & Gamble, Gedenkrede Graham (Trump-Auftritt), Messlauf Michigan-Rede.

Verwendete Zahlen im Text (4.7.4 Phase-2-Block, Kapitel 5.3, Kapitel 6): Markt-Reprice live gehörtes Wort 1-4 s, Mensch 5-8 s, Bot 15-25 s (These 1). Eigenes Audio ~20 s vor YouTube-Ton, Wörter ~20 s vor uns ausverkauft (These 1, Graham). Boeing 485 Shares beim Outlook-Thema, Restpreise 0.94-0.999 (These 2). Vier Bot-Fills: AXP Luxury/Fraud zusammen +60.06 USD, PayPal Users +9 USD, Verify-Präzision 100% bei 27+ Verifikationen (These 3). Brackets: sichere Ask 0.996, vier Messtage ohne unterschätztes Bracket (These 4). Slippage-Illustration erste ~100 USD zu 0.50, nächste zu 0.95 (These 5). UMA: Bond 750 USDC, 2-h-Challenge, 48-h-DVM, Positionsgrössen 10-100 USD, Kalibrier-Datensatz 62+22 Märkte, PayPal 19/19, Boeing 20/20, Graham 23/23, Proposer-Reihenfolge als Ambiguitäts-Signal (Thesen 7-9). ASR-Fälle agentic commerce/guidance/valuation, Valuation-Sprung 0.16 auf 0.50 (Thesen 10, 12). Nachgerüstete NO-Filter: durchgehender Pass, phonetischer Nachbarschafts-Check, Zwei-Methoden-Konsens (These 11, Preisdeckel im Text unverändert 0.80, spätere Anpassung nach NO-Winrate offen). Betrieb: Graham-Stall 54 s = drei Misses, Michigan 65 min blind, Stall-Detektor 12-s-Reconnect (These 13). ECAPA: Forever-Zähler 2 Fremdredner, verhinderter Fehlkauf ~75 USD, Studio-Referenz max 0.396 (These 14). Hybrid: zwei manuelle Ja-Käufe +6.90 USD, zwei Bauch-NOs je -10 USD (These 15). Kalshi-Vergleich (These 16). Kein Phasen-Total gebildet, da im Quelldokument keines steht. Die Phase-1-Zahlen (Stand 22.07.) bleiben unverändert eingefroren.

## Nachtrag vom 03.08.2026: E283-Absatz (4.7.4)

Quelle: docs/project/ALLIN_JULY31_LAUF.md (Lauf allin_july31, Event 758791). Verwendete Zahlen: E282-Vorwoche sieben Fills, Median-Spread Ja-Seite 0.05 konstant, E283 null Käufe, Spread-Reihe 0.23 auf 0.62 vor dem Drop, Bid-Seite intakt, Gamma-Gegenprobe, vier kontrafaktisch kaufbare Märkte (alle Ja), Basisraten-Veto zweimal korrekt (SpaceX, Blue). Hypothese MM-Anpassung analog Rogan-Läufen, Gegenhypothese Zufall, Vergleichstest E284 angelegt.
