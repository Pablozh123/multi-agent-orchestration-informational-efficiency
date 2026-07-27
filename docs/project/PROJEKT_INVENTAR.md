# Projekt-Inventar

Erhoben am 18.07.2026 von der Cowork-Session per direktem Lese-Zugriff auf die verbundenen Ordner (ba-thesis und Projects). Teil A (Punkte 1 bis 3, Vormittag) deckt das ba-thesis-Repo ab, Teil B (Punkte 4, 5, 7, 8, Nachmittag) das Terminal, den Alpha-Bot und die Klärung der Repo-Kopien. Gegenstück zum SYNC_KONTEXT_2026-07-16.md. Claude Code schreibt dieses Dokument bei jedem Meilenstein fort, die Studentin lädt es danach in die Cowork-Session hoch.

## 1. Projekt A: ba-thesis

**Module:** `operations/` mit agents, analysis, audit, collectors, db, mcp, pilot, pipeline, project, tools, validation. Dazu `ingest/`, `directives/`, `legacy/`, `tests/` und `data/` (events, live, raw, results, reference_cases, thesis.db). Steuerdokumente im Root: AGENTS.md, ARCHITECTURE_DECISIONS.md, CLAUDE.md, GOAL.md, ROADMAP.md, STATUS.md.

**Branches:** `main` (aktiv), `main-backup-2026-07-13`, `chore/ci-ruff-lint-gate`, `feat/live-bot-x-feed-ev-sizing`. Der Pilot wurde direkt auf main gebaut (kein separater Pilot-Branch).

**Tests:** 842 Testfunktionen per Zählung `def test_` unter tests/ (Thesis nennt «640 automatisierte Tests, Stand Juni 2026», die Zahl kann aktualisiert werden, exakte pytest-Sammlung vor Abgabe einmal laufen lassen).

**Zwei Arbeitskopien, ein Repo (geklärt am 18.07.):** `C:\Users\chole\ba-thesis` und `C:\Users\chole\Projects\multi-agent-orchestration-informational-efficiency` sind zwei Klone desselben GitHub-Repos (`Pablozh123/multi-agent-orchestration-informational-efficiency`). Stand 18.07. mittags stehen beide auf `main` beim selben Commit (62cb6f5), `pilot/signals.csv` ist in beiden identisch (94 Zeilen). Die jüngste Aktivität liegt in der Projects-Kopie (tests um 12:15 Uhr). Synchronisation läuft über git push und pull. Regel: aktiv gearbeitet wird nur in einer Kopie, die andere zieht per pull nach, nie in beiden gleichzeitig.

## 2. Echtgeld-Pilot (Feldtest gemäss Vorregistrierung)

Der Watcher läuft und setzt exakt die Parameter aus PILOT_PROTOKOLL_ECHTGELD_2026-07-11.md (Version 2) um: Arm 1 Entry höchstens 0.97, Arm 2 Preisfenster 0.90 bis 0.97 mit Restlaufzeit höchstens 21 Tage und Auflösung bis 02.08., Mindesttiefe 20 USDC (definiert als ausführbare Ask-Tiefe bis zur Preisobergrenze), höchstens ein Trade pro Markt, kein Order-Pfad (read-only, manueller Handel).

Stand letzter Lauf (18.07., 10:19 UTC): 1715 geprüfte Märkte, 42 aktive Signale. Kumuliert 93 Signal-Zeilen in `pilot/signals.csv` (91 Arm-2-Signale, 1 Arm-1-Kandidat mit Status «Referenz manuell prüfen», 1 Sonderstatus). Trichter-Statistik des Laufs: 715 Märkte bereits abgelaufen, 684 im Gamma-Vorfilter, 211 ausserhalb des Preisfensters, 49 bereits signalisiert, 9 mit unklarer Auflösungsregel, 2 unter Mindesttiefe, 2 mit laufendem Streit.

**Budget bestätigt:** Die Studentin hat das Budget von 100 USDC am 18.07. bestätigt. Das Protokoll in `docs/project/` ist in beiden Arbeitskopien bereits nachgeführt (Einsatz je Trade 10 USDC, maximal 10 Trades, Regel-Freeze am 18.07.2026). Das publizierte `pilot.json` auf der Website (Stand 18.07., 12:14 UTC) trägt dieselben Werte, Kennzeichnung «pilot/preregistered» mit explizitem Hinweis, dass Signale Regel-Treffer und keine Empfehlungen sind.

`pilot/trades.csv` ist weiterhin leer (nur Kopfzeile): bisher kein manueller Pilot-Trade. Handelsfenster läuft bis 01.08.

## 3. Mentions-Bot: realer Handel seit 03.07.2026 (wichtig, für Cowork neu)

Der Mentions-Strang (Branch-Ursprung feat/live-bot-x-feed-ev-sizing) handelt real mit Kleinbeträgen. Steuerung über `data/live/watchdog.json`, Läufe und manuelle Einordnung in `data/live/run_annotationen.json`, Rohdaten je Lauf unter `data/live/<profil>/` und `data/raw/live_runs/`. Es existiert ein `deposit_wallet.json` (von Cowork bewusst nicht geöffnet).

Dokumentierte Läufe (Auszug aus den Annotationen): allin_july3 «echt», Erkennung 69 Minuten nach pubDate wegen Feed-Cache, 15 korrekte Signale waren bereits eingepreist, einziger Fill «Birth Tourism» (vom Markt übersehen, resolvete YES), realisierter PnL +10.50 USD. jre_july6 «echt», Erkennung 79 Sekunden nach pubDate, komplette Episode in 3.5 Minuten verarbeitet, 0 Trades, weil Market Maker beim Drop alle Asks zogen. allin_july10 «Fehltrigger» (Interview-Special ohne Playlist-Prüfung), PnL −3.00 USD, daraus gebaut: Playlist-Gate, Wallet-Delta-Buchhaltung, Erkenntnis Selbst-Trade-Falle beim Positionsabbau. Weitere Profile: jre_july13, elon_july13 (aktiv bis 20.07.), allin_july17, lemonade_july15, mrbeast_gaming, mrbeast_next.

Operative Lehren aus den Annotationen: Feed-Caches können eine Stunde nachhängen (MP3-URL-Prober gebaut), Market Maker sind schneller als jede Transkription, dünne Orderbücher bei Nischen-Podcasts. Dazu passt `data/results/wallet_abgleich_2026-07-18.json` (Wallet-Delta-Abgleich).

## 4. Tägliche Kette: publiziert ins Terminal-Repo (geklärt am 18.07.)

Die Vermutung aus Teil A stimmt. Die Kette rechnet im ba-thesis-Repo (`data/results/`, 432 Dateien, frische Stände vom 18.07., darunter die Monitor-Review-Pakete und die Mentions-Postmortems) und publiziert nach `prediction-market-terminal/public/data/`. Dort liegen neun JSON-Artefakte: meta, runs, queue, audit, kategorie_karte, mentions_latenz, postmortems, pipeline_forward, pilot. Letzter Kettenlauf 18.07., 09:16 UTC (Backend mock): Collector ok mit 40 Alerts, Monitor-Refresh 25 Queue-Zeilen, Review-Queue 25 Fälle. pilot.json und postmortems.json wurden am 18.07. um 12:14 UTC separat aktualisiert. Die Datumsstände in runs.json decken unter anderem den 10., 11., 14., 15. und 18.07. ab, die Kette lief also regelmässig, aber nicht lückenlos täglich. In der Thesis stehen sechs publizierte Artefakte, dazugekommen sind seither vermutlich pilot, pipeline_forward und postmortems.

## 5. Replay-Nachweis für Tabelle 6: geklärt, mit wichtiger Einschränkung (18.07.)

Claude Code hat den Befund bereits am 16.07. in `docs/project/REPLAY_NACHWEIS.md` dokumentiert (liegt in beiden Arbeitskopien), die Cowork-Erhebung vom 18.07. bestätigt ihn. Primärquelle der Einstufungen ist `prediction-alpha-bot/docs/playbook/EDGES.md`: Abschnitt 12 «Crypto Up/Down Fade / Oracle Divergence (Tier B)» mit dem wörtlichen Eintrag zu N=28 (normale Richtung 2 Treffer und 26 Fehler, invertiert 26 Treffer und 2 Fehler, 93 Prozent, Wilson-Untergrenze 77.4 Prozent, Vorbehalt «requires out-of-sample confirmation before live flip»). Abschnitt 7 «Tail-Fade / Premium Harvest (Tier B)» dokumentiert den Tail-Fade als konsistente Kleinbetrags-Kante mit Warnung vor Exit-Kosten in dünnen Büchern.

Die Einschränkung: Die 28 Einzelfälle existieren nirgends als Rohdaten. EDGES.md wurde am 19.05.2026 im allerersten Commit des Repos angelegt und seither nicht geändert, die Auswertung stammt aus einer nicht archivierten Datenbank eines Vorgängersystems (VPS). Die forward-clean-Datenbanken und die basket-forward-replay-Reports im selben Repo belegen die strukturellen Scanner-Aussagen (Fenster 20.05. bis 10.06.), nicht die N=28-Zahl. Konsequenz gemäss REPLAY_NACHWEIS.md, Entscheidung bei der Studentin: entweder die Zahl behalten und als dokumentierte, nicht mehr reproduzierbare Auswertung des Vorgänger-Scanners ausweisen (dort empfohlen), oder auf die Zahl verzichten und nur ein vielversprechendes, unbestätigtes Muster nennen.

## 6. Thesis-Versionen (Divergenz-Gefahr)

Kanonisch ist die docx aus dem Chat-Workflow (aktuell Version 14 vom 18.07.). Im Repo liegen zusätzlich `thesis/` mit einer LaTeX-Fassung (chapters 01 bis 11, main.tex, references.bib), `thesis/Bachelorarbeit_FHNW.docx` vom 22.06. (veraltet) und `thesis_overleaf.zip`. Empfehlung: die Repo-Fassungen sichtbar als Archiv markieren (README-Zeile in thesis/), damit niemand versehentlich am alten Stand weiterschreibt.

## 7. Projekt B: Prediction-Market-Terminal (erhoben am 18.07.)

Pfad `C:\Users\chole\Projects\prediction-market-terminal`, GitHub `Pablozh123/prediction-market-terminal`, Branch main. Streamlit-Monolith `prediction_terminal.py` mit rund 11'000 Zeilen, dazu `app/`-Module (analysis_views, backtester, calibration, copy_fidelity, copy_follow, filters, microstructure_views, notify, quant, run_sim, signals, suspicion, track_record und weitere) und `src/`. 259 Unit-Tests grün gemäss docs/HANDOFF.md (Stand dort 12.06., die Juli-Arbeit ist über die publizierten Artefakte sichtbar). Deploy-Stack Docker, Caddy und Cloudflare, Plan-Dokumente LAUNCH_PLAN.md, LIVE_COPYTRADING_PLAN.md, PRODUCTION_READINESS.md. Copy-Trading bleibt paper-only, kein Order-Code im Terminal.

Die Website hat 24 Workspaces in sechs Navigationsgruppen: Overview, Gruppe Markets (Markets, Search, Live Trades, Resolved, Cross-Venue), Gruppe Traders (Traders, Wallets, Whale Flow, Suspicious, Track), Gruppe Trading (Backtester, Copy Trade, Portfolio), Gruppe Research (Review Queue, Category Efficiency, Mentions Latency, Live Runs, Microstructure, Pilot, Pipeline Forward, Methodology), Gruppe System (Monitor, Settings). Für die Thesis relevant: Die Research-Gruppe bildet die Kapitel-4-Artefakte direkt ab, und die Seiten Pilot und Pipeline Forward sind neu gegenüber dem Thesis-Text.

## 8. Projekt C: prediction-alpha-bot (erhoben am 18.07.)

Pfad `C:\Users\chole\Projects\prediction-alpha-bot`. TypeScript/Node-Scanner, laut docs/PROJECT_STATUS.md (Stand 19.05.) paper-only ohne Order-Clients, ohne Wallet- und Key-Code. Implementierte Scanner damals: NEG_RISK Bracket Sum-Arb und Within-Market YES+NO unter 1. `docs/playbook/` ist die Wissensbasis mit PLAYBOOK, EDGES, METHODOLOGY, ANTIPATTERNS, ARCHITECTURE, APIS und NEG_RISK_NO_CARRY. `docs/reports/` enthält die datierten Artefakte (basket-forward-replay 22.05. bis 02.06., coverage-reports, cross-venue-arb 02.06. bis 10.06. mit HTML-Dashboards, detailed-paper-run-report 21.05., neg-risk-diagnostics). `docs/CROSS_VENUE_ARB.md` und `docs/paper-only.md` beschreiben die Betriebsregeln. `logs/` enthält die forward-clean-Datenbanken (siehe Punkt 5) und 24h-Bot-Archive vom 20. und 21.05.

## 9. Konsequenzen für die Thesis (Arbeitsliste Cowork, nach Freigabe)

Freigabe-Stand 18.07.: Die Studentin hat entschieden, alle Punkte gesammelt nach dem Pilot-Fenster umzusetzen (Auswertung 02. bis 03.08., Einbau bis 05.08., zusammen mit der Ergebnis-Box). Für Punkt 5 ist die Variante «Zahl behalten und Quelle ausweisen» beschlossen.

1. 4.8 aktualisieren: aus «zwei dokumentierten Live-Läufen» ist ein realer Betrieb mit mehreren Profilen und dokumentierten Echtgeld-Ergebnissen geworden (kleine PnL, operative Lehren, Fehltrigger-Fall). Das ist starke Feld-Evidenz für die Effizienz-Aussage («Market Maker schneller als jede Transkription», «15 Signale bereits eingepreist»).
2. 4.1 präzisieren: Die Kapitel-4-Werkzeuge bleiben im Paper-Betrieb, der Mentions-Bot handelt seit 03.07. real mit Kleinbeträgen (vom Betreuer sanktioniert). Die Abgrenzung muss im Text sauber stehen, sonst widerspricht 4.1 dem Repo-Stand.
3. 4.2 ergänzen: vorregistrierter Feldtest läuft (Watcher, Signal-Trichter, bestätigtes Budget 100 USDC, Regel-Freeze 18.07.), Ergebnis-Box nach Fensterende (Auswertung 02. bis 03.08.).
4. Testzahl und Stand-Angaben aktualisieren: 842 statt 640 im ba-thesis-Repo, 259 im Terminal, Datumsstände.
5. Tabelle 6: Entscheid gemäss REPLAY_NACHWEIS.md nötig. Empfehlung dort: Zahl behalten und als dokumentierte, nicht mehr reproduzierbare Auswertung des Vorgänger-Scanners ausweisen (Playbook-Eintrag vom 19.05.2026, Out-of-sample offen). Alternative: auf die Zahl verzichten. Formulierungsvorschlag liefert Cowork nach dem Entscheid.
6. 4.3 und 4.5 nachführen: 24 Workspaces mit Research-Gruppe, neun publizierte JSON-Artefakte, Kettenstand 18.07. mit Zahlen aus Punkt 4.

## 10. Fortschreibung

Claude Code aktualisiert dieses Inventar bei jedem Meilenstein (neuer Abschnitt «Update TT.MM.» genügt). Die Studentin lädt die Datei danach in die Cowork-Session hoch. Nichts aus diesem Inventar gelangt ungeprüft in die Thesis, Zahlen immer gegen die Artefakte.

## Update 22.07.2026: pipeline_forward.json gefüllt

**Befund.** Das publizierte `pipeline_forward.json` war leer, mit eigenem Hinweis «Source decisions_log.jsonl not present on this machine». Zwei Ursachen: die tägliche Kette läuft in der Projects-Arbeitskopie, deren `data/live/` gitignored und leer ist (die Rohdaten liegen nur im ba-thesis-Checkout), und der Publish-Schritt kannte nur die feste Profil-Liste `("allin_july3", "jre_july6")`.

**Behoben, beide Varianten des Auftrags kombiniert.**

1. *Quellpfad konfigurierbar.* `live_roots()` in `operations/pipeline/daily_review_run.py` löst die Wurzel in fester Reihenfolge auf: `--live-root`, dann `THESIS_LIVE_ROOT`, dann `data/live`, zuletzt `data/live_curated`. Der Task-Wrapper `daily_review_task.cmd` reicht die Live-Wurzel (Parameter %2, bisher nur ans Dashboard) auch an den Tageslauf; fehlt %2, bleibt das Flag weg.
2. *Kuratierte Kopien versioniert.* `operations/pipeline/kuratiere_live_laeufe.py` schreibt nach `data/live_curated/<profil>/` und kopiert ausschliesslich die ohnehin publizierten Felder: `action`, `reason`, `limit_price`, `size_usd`, Buch-Preise und die Wortzähler-Ereignisse. Draussen bleiben `token_id`, `market_id`, `outcome`, `status`/`detail`/`size_shares` (das `detail` enthält gekürzte Wallet-Ids), Buch-Grössen, `deposit_wallet.json`, Orderbuch-CSV, Bot-Logs sowie Audio und Video. Vor dem Schreiben läuft dasselbe Redaktions-Gate wie im Publish-Schritt. Aus 1.4 GB Rohdaten werden 188 KB.
3. *Eine Liste je Lauf.* Neu ist das additive Feld `laeufe` mit einem Eintrag je Lauf (`profil`, `n_eintraege`, `n_kaeufe`, `eintraege`, `wortzaehler_endstaende`), jüngster zuerst nach dem letzten Entscheidungs-Zeitstempel. Die obersten Felder `eintraege`/`wortzaehler_endstaende` bleiben unverändert und spiegeln jetzt den jüngsten Lauf **mit Käufen** (`allin_july17`) statt `allin_july3`; bestehende Leser laufen unverändert weiter.

**Unverändert geblieben:** Schema-Grundform und Feld-Whitelist, Kennzeichnung `observed/paper`, keine Wallet-Daten, keine Rendite-Aussage, Redaktions-Gate. Ein Test hält die Whitelist jetzt auch innerhalb von `laeufe` fest.

**Stand nach Kettenlauf vom 22.07.2026, 11:43 UTC** (Backend mock, Collector ok mit 46 Alerts, Monitor-Refresh und Review-Queue je 28 Fälle):

| Lauf | Entscheidungen | davon Käufe | Wortzähler-Endstände |
| --- | --- | --- | --- |
| jre_july20 | 35 | 0 | 20 |
| allin_july17 | 31 | 6 | 21 |
| elon_july13 | 24 | 0 | 0 |
| lemonade_july15 | 39 | 1 | 20 |
| jre_july13 | 38 | 0 | 25 |
| allin_july10 | 71 | 37 | 19 |
| jre_july6 | 35 | 0 | 21 |
| allin_july3 | 35 | 1 | 20 |
| **Summe** | **308** | **45** | -- |

Der Schritt-Vermerk in `meta.json` lautet jetzt `ok (8 laeufe, 308 eintraege)` statt `quelle_fehlt`. Artefakt-Grösse 77.8 KB, Redaktions-Gate bestanden. `elon_july13` ist der X-Feed-Lauf und führt keine Wortzähler.

**Terminal-Seite.** Die Seite «Pipeline Forward» hat einen Run-Auswähler über alle acht Läufe; vorausgewählt ist der Lauf, den der Artefakt-Hinweis nennt. Ältere Artefakte ohne `laeufe` rendern weiter als einzelner Lauf.

**Tests.** ba-thesis 920 grün (vorher 842, neu unter anderem `tests/test_kuratiere_live_laeufe.py` und die Fallback-Tests für den Quellpfad), Terminal 446 grün.

**Offen.** Die kuratierten Kopien sind ein Stand vom 22.07. Nach neuen abgeschlossenen Läufen muss `kuratiere_live_laeufe.py` erneut laufen, sonst publiziert die Kette auf einer Maschine ohne `data/live` weiterhin nur diese acht Läufe.

## Update 22.07.2026 (zweite Session): Pilot-Watcher in der Kette, Torn Write behoben

Ergänzt den Abschnitt oben; beide Arbeitspakete liefen am selben Tag parallel (siehe die Notiz zur Doppelarbeit am Ende).

**Der Feldtest stand still.** Der Pilot-Watcher hatte nie einen Scheduled Task. Letzter Lauf war der 18.07., 10:19 UTC — die tägliche Kette publizierte seither denselben alten Signalstand, obwohl das Handelsfenster bis 01.08. läuft. `run_dashboard` führt den read-only Watcher jetzt vor dem Bauen von `pilot.json` aus. Bewusst ohne Änderung am bestehenden Scheduled Task: Der Schritt ist datumsgebunden an `handelsfenster_bis` aus dem Protokoll, entfällt nach dem 01.08. von selbst und lässt sich mit `--kein-pilot-watcher` abschalten. Fehler sind fail-soft, dann bleibt der letzte Stand publiziert. Weiterhin kein Order-Pfad und keine Keys: gehandelt wird manuell.

Erster Lauf über die Kette am 22.07., 12:11 UTC: 1655 geprüfte Märkte, kumuliert 143 Signal-Zeilen in `pilot/signals.csv` (142 Arm-2-Signale, 1 Arm-1-Kandidat). `pilot/trades.csv` bleibt leer — bis zum Fensterende am 01.08. ist kein manueller Trade erfasst. Ohne Trades wird die Ergebnis-Box in Kapitel 4 ein dokumentierter Null-Fall (Signale, Hindernisse, keine Ausführungsdaten).

**Torn Write an der Wurzel behoben.** `runs.json` war am 18.07. abgeschnitten (30'072 Bytes, ungültiges JSON), weil `write_text` in die Zieldatei selbst schreibt und die Website denselben Ordner live liest. Alle Publizierpfade schreiben jetzt atomar (Temp-Datei im Zielordner, `fsync`, `os.replace`): `publish_runs`, `publish_payloads`, der Tageslauf und die Kopie in den Website-Ordner (`shutil.copy2` war derselbe Fall). `runs.json` ist neu publiziert und wieder gültiges JSON — 32'758 Bytes, 8 Runs, 15 Wetten, Einsatz 626.68, PnL 45.02 (log-basiert). Damit ist Punkt 12.1 des Kennzahlenblatts vom 18.07. erledigt.

**Doppelarbeit-Notiz (für die Sync-Regeln).** Der CC-Auftrag «Pipeline-Forward füllen» wurde am 22.07. von zwei Claude-Code-Sessions gleichzeitig bearbeitet. PR #25 (kuratierte Läufe im Repo, Liste je Lauf) wurde zuerst gemergt und ist die gültige Lösung; die zweite Session hat ihre eigene, schwächere Quellpfad-Variante verworfen und nur ihre eindeutigen Beiträge (Watcher-Kettenschritt, atomares Schreiben) auf den gemergten Stand neu aufgebaut. Lehre für die Sync-Regeln in `SYNC_KONTEXT_2026-07-16.md`: Ein Auftrag aus `docs/project/` gehört an genau eine Session; vor Arbeitsbeginn `git fetch` und die offenen PRs prüfen.

## Update 23.07.2026: Elon-Post-Woche 20.–26.07. armiert (Profil `elon_july20`)

**Neues Profil.** `elon_july20` in `operations/pipeline/config.py`, Event `715491` („What will Elon post this week? (July 20 – July 26)"), Periode 20.07. 04:00 UTC bis 27.07. 03:59 UTC, nur YES, Ask-Deckel 0.94 (p_win 0.97 − min_edge 0.03), Budget 400 USD mit dem großen Sweep der Vollprofile (50 USD je Clip, 40 Clips; User-Vorgabe 23.07.). Der Regeltext der Serie ist am 23.07. an der Gamma-Beschreibung gegengelesen und wortgleich zur Vorwoche — der Matcher aus `elon_bot.py` trägt unverändert. Runbook und offene Entscheidungen in `docs/project/ELON_JULY20_ARMIERUNG.md`. Tests 1006 grün (vorher 990), ruff sauber.

**Ein Code-Eingriff.** Der Startscan blätterte fest 4 Seiten zurück. Das reicht für einen Start am Wochenanfang, nicht für eine Armierung an Tag 4 von 7. Neuer additiver Profil-Knopf `startscan_seiten` → `config.X_STARTSCAN_SEITEN` (Default bleibt 4, `elon_july20` nimmt 12); das `startscan`-Event loggt jetzt `seiten_geblaettert`, `seiten_max` und `erreicht_periodenstart`.

**Auswertung der Vorwoche `elon_july13` (belegt aus `data/live/elon_july13/`, nur im ba-thesis-Klon).** Der Lauf schloss mit `fertig … "getradet": []` — **null Käufe in sieben Tagen**, bei 21 Watchdog-Neustarts und 24 `yes_entscheidung`-Einträgen (alle `no_action`). Vier verschiedene Trigger-Posts, Latenz Post → Erkennung 15 s, 32 s, 14 s und einmal 9,1 min (Texas, 15.07. — der Rate-Limit-Blackout, seither durch adaptives Pacing behoben). Die Erkennung war also nicht das Problem: Beim ersten Trigger („Always", 13.07. 18:38) hatte das YES-Buch 15 Sekunden nach dem Post **gar keinen Ask mehr**, der `orderbook_log.csv` zeigt von 18:39 bis 20:56 keine einzige Ask-Zeile bei steigendem Bid (0.40 → 0.96); bei Texas dasselbe Muster. Der letzte Ask *vor* dem Post lag bei beiden Märkten bei 0.95 — eine Stufe über dem Deckel. Auch mit Latenz null wäre kein Fill zustande gekommen.

**Konsequenz für die Effizienz-Aussage (Kapitel 4.8).** Der Mentions-Befund „Market Maker sind schneller als jede Transkription" hat hier ein Gegenstück ohne Transkription: Bei reinem Text-Matching auf einem verifizierten Account liegt die Erkennung bei 15–32 Sekunden, und der Markt ist trotzdem vorher weg — die Ask-Seite verschwindet, statt sich nur zu verteuern. Das ist Feld-Evidenz für Effizienz auf der *Liquiditäts*-, nicht der Latenz-Dimension. Die Zahlen sind aus den Live-Artefakten belegt und für 4.8 zitierfähig.

**Marktlage beim Armieren (Gamma/CLOB, 23.07.).** 17 Märkte, 4 davon bereits zu 1.00 aufgelöst (`Tesla`, `Video game`, `Claude`, `SpaceX`) und von `baue_elon_rules` automatisch übersprungen; 13 offen. Event-Liquidität 2'552 USD, Volumen 15'150 USD. Ausführbare YES-Tiefe unter dem 0.94-Deckel: 22–255 USD je Markt, Summe rund 1'096 USD. Über allen Büchern liegt ein wiederkehrendes Angebot bei 0.95, genau eine Stufe über dem Deckel.

**Offen.** Reply-Abdeckung (Vorwoche: fünfmal `nur UserTweets aktiv — Fremd-Replies fehlen`; Fallback `APIFY_REPLY_FALLBACK=1` kostet externe Apify-Läufe), sowie 365 von 1'138 Buchlog-Runden mit CLOB-404 (betrifft nur die Analyse-Zeitreihe, nicht den Handelspfad).

## Update 24.07.2026: Earnings-Bot — Polymarket-Verbindung gebaut (Branch feat/earnings-bot)

**Anlass.** Die Live-Transkriptions-Strecke für Webcasts ist seit dem AXP-Paper-Lauf (24.07., `mentions_paper_lauf.py` ausserhalb des Repos) einsatzbereit; es fehlte die Verbindung zu Polymarket (Entscheidung + Order). Die ist jetzt gebaut, als produktisierter Abschluss der Strecke Audio → Zählung → Entscheidung → Order.

**Neu im Repo (additiv).** `operations/pipeline/earnings_bot.py` (Runner für Events ohne Drop-Ereignis: Audio via Loopback-Gerät/Stream-URL/WAV; wiederverwendet build_rules, ChunkTranscriber, StreamingCounter, decision, execution samt Startwache, Kill-Switch, FAK-Sweep), Profil `earnings_pg_july29` in `config.py` (Event 715467, P&G-Call 29.07. 12:30 UTC laut Gamma — an IR-Quelle gegenzuprüfen), `tests/test_earnings_bot.py` (13 Tests), Runbook `docs/project/EARNINGS_BOT_PG_JULY29_ARMIERUNG.md`. Suite 1040 grün, ruff sauber.

**Drei festgenagelte Fallen.** (1) Anyone-Klausel je Markt-Beschreibung als Gate gegen die Sprecherfilter-Serie („What will Elon Musk say during Tesla … earnings call?"). (2) `groupItemThreshold` ist ein Sortier-Index, KEINE Zählschwelle (AXP-Event: Einzelwort-Märkte tragen 3/4/5, „Income 10+" trägt 0) — die Annahme aus der Recherche §9 war falsch, Schwelle kommt ausschliesslich aus dem Fragetext. (3) Kein Auto-Discovery-Rollover: Earnings-Slugs sind Rolling Slugs, der Refresh bleibt an der Event-ID.

**Bewusst zu:** NO-Seite (`no_ask_obergrenze` 0.0) und Gap-Verify, bis die Capture-Abdeckung eines vollen Calls belegt ist; kein automatisierter Webcast-Login (Zugang bleibt Handarbeit im Browser). **Offen vor scharfem Einsatz:** ToS-/Rechtslage des Mitschnitts (Recherche §7/§10), IR-Zeitverifikation, Budget-Entscheid (Platzhalter 100 USD). Details und Armierungs-Schritte im Runbook.

## Update 27.07.2026: AXP-Erstlauf +60.06 USD, Trigger-Verifikation gebaut

**Erstlauf 24.07. (LIVE, User-Entscheid):** Profil `earnings_axp_july24`, Event 715475. 470 Chunks ohne Fehler-Event; zwei Kaeufe auf vom Markt uebersehene Woerter — Luxury YES @0.56 (58.79 USD), Fraud YES @0.52 (15 USD) — beide per UMA YES aufgeloest: **+60.06 USD realisiert** (bester Einzellauf des Mentions-Strangs). Befund: Brackets vorgepreist (Quarter 25/10 gezaehlt, nie Ask < 0.90), gefallene Einzelwoerter sofort tot; der reale Kanal ist ein Aufmerksamkeits-Edge auf mittelpreisige Woerter. Die taegliche Kette publizierte den Lauf am 27.07. automatisch ins Terminal (runs.json, 14 Runs).

**Zwei Haertungen fuer P&G (29.07.):** (1) Vorscan-Pause auch fuer Buecher ohne Asks (AXP: 2029 von 2081 Entscheidungen waren tote Wiederholungen, 1–2 s Latenz je Chunk). (2) Neues Modul `operations/pipeline/trigger_verify.py`: jeder YES-Trigger wird vor dem Kauf mit warm geladenem large-v3 nachtranskribiert und strikt nachgezaehlt — fail-closed auf allen Kaufpfaden (Chunk/Endcheck/Nachlauf), Ablehnung sperrt bis zum naechsten neuen Treffer, Abschalten nur explizit via `--ohne-trigger-verify`. Tests 1046 gruen, ruff sauber. `data/live_curated/` auf alle 14 Laeufe aufgefrischt (inkl. sechs neuer Lauf-Ordner).

**Nachmittag 27.07.: sprechergebundene Events + Quellen-Recherche.** Neue Notiz `RECHERCHE_EARNINGS_QUELLEN_2026-07-27.md`: drei Earnings-Kandidaten IR-verifiziert (PayPal 28.07. 12:00 UTC, Event 745733, Q4-Inc-Registrierung; Boeing 28.07. 14:30 UTC, 745748; P&G 29.07. 12:30 UTC bestaetigt — Runbook-Schritt 1 damit erledigt). Dazu auf User-Entscheid gebaut: Profil `trump_michigan_july27` (Event 745732, Rede GM Proving Ground 19:00 UTC) — der earnings_bot kann jetzt sprechergebundene Events ("if Trump says"): Profil-Klauselmuster ersetzt das Anyone-Gate, ECAPA-Sprecher-Verifikation traegt die YES-Entscheidung (ziel_count, Referenz Pflicht bei --live), Operator-Marker `SPRECHER_AKTIV` sperrt den Kaufpfad bis zum Redebeginn; ASR-Zaehlfallen "%"/"Drill, baby, drill"/USMCA per Override. Tests 1062 gruen (+16, inkl. geschaerftem Abgrenzungstest Text- vs. Audio-Profile), ruff sauber. Runbook `TRUMP_MICHIGAN_JULY27_ARMIERUNG.md`; Referenzstimme und Livelauf stehen aus.
