# Armierung Elon-Post-Woche 20.–26.07. (Event 715491)

Stand 23.07.2026. Profil `elon_july20` ist gebaut, getestet und committet
(Branch `feat/elon-bot`). Dieses Dokument ist der Armierungs-Runbook plus
die offenen Entscheidungen.

**Besonderheit: Armierung mitten in der Periode.** Die Marktwoche läuft
seit Mo 20.07. 04:00 UTC, sie endet Mo 27.07. 03:59 UTC (26.07. 23:59 ET).
Beim Scharfschalten am 23.07. sind rund dreieinhalb der sieben Tage schon
vorbei — der Bot deckt nur den Rest ab.

## Was fertig ist (im Code)

- **Profil `elon_july20`** in `operations/pipeline/config.py`: Event
  `715491`, Slug `what-will-elon-post-this-week-july-20-july-26-…`,
  Periode `2026-07-20T04:00:00Z` bis `2026-07-27T03:59:59Z`, Account
  `44196397` (@elonmusk), `p_win 0.97` / `min_edge 0.03` → **Ask-Deckel
  0.94**, `x_poll_s 8.0`, eigenes `live_dir` (Vorwochen-Events bleiben
  unberührt).
- **NUR YES** (User-Vorgabe 13.07., am 23.07. für diese Woche bestätigt).
  `elon_bot.py` hat gar keinen NO-Zweig — es gibt nichts zu sperren.
- **Regeltext gegengelesen.** Die Gamma-Beschreibung von Markt `2966514`
  ist am 23.07. wortgleich zur Vorwoche: Plural/Possessiv/Case zählen,
  Sigils (`#`/`@`/`$`) davor sind ok, Compounds zählen, Misspellings und
  Symbole *im* Wort disqualifizieren, eigener Text in Quote- und
  Reply-Posts zählt, zitierter Fremdtext und Reposts nicht, Bildtext nur
  klar ausgeschrieben. Der bestehende Matcher trägt unverändert.
- **Tieferer Startscan** (neu): `startscan_seiten` ist als Profil-Knopf
  in `config.X_STARTSCAN_SEITEN` gelandet, Default bleibt 4, dieses Profil
  nimmt 12. Grund: Bei einem Start am Wochenanfang reichen 4 Seiten; wer
  an Tag 4 armiert, würde die Posts vom 20.–23.07. sonst nie prüfen — und
  damit einen vom Markt übersehenen Treffer verpassen (Fall „Birth
  Tourism", `allin_july3`). Das `startscan`-Event loggt jetzt
  `seiten_geblaettert`, `seiten_max` und `erreicht_periodenstart`.
- Suite grün (1006 Tests, vorher 990), ruff sauber.

## Marktlage beim Armieren (Gamma/CLOB, 23.07.)

17 Märkte, davon **4 bereits geschlossen** und auf 1.00 aufgelöst
(`Tesla`, `Video game`, `Claude`, `SpaceX`) — die überspringt
`baue_elon_rules` automatisch. Bleiben **13 offene Märkte**.
Event-Liquidität 2'552 USD, Volumen 15'150 USD.

Ausführbare YES-Tiefe **unter dem 0.94-Deckel** (Summe `Preis × Size`):

| Wort | bester Ask | USD ≤ 0.94 |
| --- | --- | --- |
| Soccer | 0.070 | 254.89 |
| IPO | 0.130 | 86.03 |
| Iran / Iranian | 0.110 | 85.66 |
| Trump | 0.160 | 74.85 |
| China | 0.590 | 70.30 |
| Football | 0.169 | 67.68 |
| President | 0.340 | 66.38 |
| Neuralink | 0.530 | 65.25 |
| Texas | 0.740 | 61.15 |
| Crypto / Bitcoin | 0.089 | 60.01 |
| ChatGPT | 0.810 | 59.56 |
| Never | 0.830 | 22.12 |
| Always | 0.830 | 22.12 |

Summe rund 1'096 USD. Über allen Büchern liegt ein wiederkehrendes
Angebot bei **0.95** — genau eine Stufe über unserem Deckel.

## Der Befund aus der Vorwoche: null Fills, und warum

`elon_july13` schloss mit `fertig … "getradet": []` — **kein einziger
Kauf** in sieben Tagen. Aus `data/live/elon_july13/bot_events.jsonl` und
`orderbook_log.csv` (nur im ba-thesis-Klon):

- **Die Erkennung war schnell genug.** Vier Trigger-Posts, Latenz
  Post → Erkennung: 15 s, 32 s, 14 s — und einmal 9,1 min (Texas,
  15.07.). Der Ausreißer war der Rate-Limit-Blackout, seit dem adaptiven
  Pacing vom 15.07. behoben.
- **Trotzdem gab es nichts zu kaufen.** Beim ersten Trigger („Always",
  13.07. 18:38) lautete die Entscheidung `kein_yes_ask` — 15 Sekunden nach
  dem Post hatte das YES-Buch **überhaupt keinen Ask mehr**. Der
  Buchlog zeigt: von 18:39 bis mindestens 20:56 keine einzige Ask-Zeile,
  während der Bid von 0.40 auf 0.96 stieg. Bei Texas dasselbe Muster
  (kein Ask von 15:27 bis 17:28+).
- **Und davor war es schon zu teuer.** Der letzte Ask *vor* dem Post lag
  bei beiden Märkten bei 0.95 — eine Stufe über dem 0.94-Deckel. Selbst
  mit Latenz null wäre kein Kauf zustande gekommen.
- Die späteren Einträge mit `yes_ask 0.998 > 0.94` sind Artefakte der
  21 Watchdog-Neustarts: Jeder Neustart spielt die Historie neu ein und
  triggert auf denselben alten Posts.

**Konsequenz für die Erwartung.** Der Edge lebt nicht davon, schnell zu
sein — das war der Bot. Er lebt davon, dass ein **niedrig gepreistes**
Wort fällt und die Ask-Leiter unter 0.94 die ersten Sekunden übersteht.
Letzte Woche waren alle drei getriggerten Wörter (`Always`, `Texas`,
`Tesla`) vorab teuer bzw. ohne Leiter. Diese Woche gibt es die Leiter
(Tabelle oben) — ob sie beim Trigger hält, ist die offene Frage. Vier der
sieben Tage sind zudem schon vorbei.

## Armierungs-Runbook (im ba-thesis-Klon, wo die Bots laufen)

Der Code liegt im Worktree `Projects\wt-elon`. Erst nach ba-thesis bringen:

1. **Mergen.** `feat/elon-bot` → PR → grüne CI → `main`, dann im
   ba-thesis-Klon `git pull`. Der Merge fasst `config.py` und
   `elon_bot.py` an. `config.py` importieren die laufenden Echtgeld-Bots
   (`mrbeast_gaming`, `lemonade_july22`, `hotones_july23`) — die neuen
   Felder sind rein additiv, gemeinsame Konstanten bleiben unberührt.
   `elon_bot.py` importiert derzeit kein laufender Bot.

2. **Cookies prüfen.** `X_AUTH_TOKEN` und `X_CT0` müssen in `.env`
   stehen. Fehlen sie, wartet der Bot und lädt `.env` jede Minute neu —
   er handelt dann automatisch los, sobald die Cookies da sind.

3. **Watchdog-Eintrag** in `data/live/watchdog.json` → `managed`
   (der alte `elon_july13`-Eintrag kann auf `aktiv: false` oder raus):
   ```json
   "elon_july20": {"modul": "elon_bot", "ende_utc": "2026-07-27T04:00:00Z", "aktiv": true}
   ```
   `ende_utc` eine Minute nach dem Periodenende — der Bot beendet sich
   ohnehin selbst mit `fertig`, sobald `PERIODE_ENDE_UTC` erreicht ist.

4. **Startblock in `data/live/starte_bots.ps1` ergänzen.** Die
   july-13-Blöcke für Elon und Trump wurden nach Fensterende entfernt;
   der neue kommt in den `try`-Teil, neben `mrbeast_gaming` und
   `lemonade_july22`. Modul ist **`elon_bot`**, nicht `bot`:
   ```powershell
   # Elon-Post-Woche 20.-26.07.: beendet sich zum Periodenende selbst.
   Starte-Bot "elon_july20" "elon_bot" @("--refresh-rules", "--live")
   ```
   `data/live/` ist gitignored und existiert nur im Live-Klon — dieser
   Block kommt nie über einen PR.

5. **Start — Echtgeld, DU führst das aus.** Der Bot holt den
   Gamma-Snapshot selbst und platziert live Orders auf Polymarket.
   Immer über das Skript starten, nie `python -m …` von Hand: nur das
   Skript nimmt den `watchdog.lock` und verhindert damit den
   Doppelstart gegen den Watchdog-Tick.
   ```bash
   powershell -ExecutionPolicy Bypass -File data\live\starte_bots.ps1
   ```

6. **Erste Kontrolle nach dem Start.** In
   `data/live/elon_july20/bot_events.jsonl` prüfen:
   - `startscan` → `erreicht_periodenstart: true`. Steht dort `false`,
     kam der Scan nicht bis 20.07. 04:00 UTC zurück; dann
     `startscan_seiten` erhöhen und neu starten.
   - `feed_modus` → `reply_abdeckung: true` (siehe offener Punkt unten).
   - `start` → `aktive_maerkte: 13`.

## Offene Entscheidungen

- **Budget.** `max_usd_gesamt` steht auf **170.0** — der Wert der
  Vorwoche, bewusst unverändert übernommen und **nicht** vom Nutzer für
  diese Woche bestätigt. Einordnung: Die gesamte Ask-Leiter unter 0.94
  über alle 13 Märkte ist rund 1'096 USD tief, realistisch triggern in
  dreieinhalb Restagen ein bis drei Märkte. Das Wallet ist mit
  `mrbeast_gaming` (510), `lemonade_july22` (510) und `hotones_july23`
  (400) geteilt; der Executor-Delta-Sync verhindert Überziehen, aber ein
  Profil kann dem anderen den Pool wegkaufen. Vor dem Scharfschalten am
  realen Wallet-Stand gegenprüfen.
- **Sweep-Größe.** Standard (15 USD je Clip, 10 Clips → 150 USD je
  Markt), wie `elon_july13`. Bei Buchtiefen von 22–255 USD je Markt ist
  das plausibel; wer die tiefen Bücher (Soccer 255) voll abräumen will,
  bräuchte `max_usd_pro_markt`/`max_clips_pro_markt` wie `allin_july17`
  (50/40).
- **Reply-Abdeckung.** In der Vorwoche loggte der Bot am 16.07. fünfmal
  `warnung … nur UserTweets aktiv — Fremd-Replies fehlen`. Elon
  antwortet viel, und Replies zählen laut Regel. Der Selbstheilungspfad
  existiert (bei jedem Poll wird `UserTweetsAndReplies` zuerst
  probiert); als Tiefen-Fallback gibt es `APIFY_REPLY_FALLBACK=1`
  zusammen mit `APIFY_TOKEN` — kostet dann aber externe Apify-Läufe.
  Entscheidung offen.
- **Buchlog-404s.** 365 der 1'138 Buchlog-Runden der Vorwoche endeten
  mit `404` von `clob.polymarket.com/book`. Betrifft nur die
  Analyse-Zeitreihe, nicht den Handel (der Fetch im Trigger-Pfad ist ein
  eigener Aufruf). Vermutlich tote Token aufgelöster Märkte; da
  `log_snapshots` bereits je Token abfängt, lohnt ein kurzer Blick, ob
  die 404 aus dem NO-Token geschlossener Märkte kommt. Kein Blocker.
