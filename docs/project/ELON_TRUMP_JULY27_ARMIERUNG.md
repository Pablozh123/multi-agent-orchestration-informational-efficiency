# Armierung Post-Woche 27.07.–02.08. — Elon (745693) und Trump (745692)

Stand 27.07.2026, ~20:30 UTC. Beide Profile sind gebaut, getestet und auf
`feat/elon-bot` committet. Dieses Dokument ist das Armierungs-Runbook für
**beide** Wochen-Bots plus die offenen Entscheidungen; es folgt dem Muster
von `ELON_JULY20_ARMIERUNG.md`.

**Besonderheit: Armierung an Tag 1.** Anders als in der Vorwoche (Einstieg
an Tag 4 von 7) beginnt die Marktwoche heute: Mo 27.07. 04:00 UTC bis
Mo 03.08. 03:59 UTC (02.08. 23:59 ET). Ein Start heute Abend deckt fast
die volle Woche ab; nur der angebrochene Montag muss per Startscan
nachgezogen werden.

## Was fertig ist (im Code, Branch `feat/elon-bot`)

- **Profil `elon_july27`** in `operations/pipeline/config.py`: Event
  `745693`, Slug `what-will-elon-post-this-week-july-27-august-2-…`,
  Periode `2026-07-27T04:00:00Z` bis `2026-08-03T03:59:59Z`, Account
  `44196397` (@elonmusk), `p_win 0.97` / `min_edge 0.03` → Ask-Deckel
  **0.94**, `x_poll_s 8.0`, eigenes `live_dir`. `startscan_seiten: 8`
  statt der 12 der Tag-4-Armierung: reine Reserve für den angebrochenen
  Montag (Elon schafft >80 Posts+Replies am Tag, der 4er-Default wäre
  knapp); der Scan bricht ohnehin am Periodenstart ab.
- **Profil `trump_july27`**: Event `745692`, Truth-Social-Quelle wie
  july13/july20 (`truth_watch.py`, curl_cffi-Impersonation, kein Login),
  `truth_poll_s 15.0`, gleiche Periode, gleicher Deckel 0.94.
  Abgrenzung bleibt im Profil-Kommentar: nur die Serie 11341
  „trump-post-weekly" (geschriebene Truths) handeln, nie die parallele
  „What will Trump SAY"-Serie (11277, nur Gesprochenes).
- **NUR YES** beide (User-Vorgabe 13.07., seither wöchentlich bestätigt);
  `elon_bot.py`/`trump_bot.py` haben keinen NO-Zweig.
- **Regeltext gegengelesen (27.07., per Diff statt von Hand):** Die
  Gamma-Beschreibungen beider neuer Events sind nach Normalisierung der
  Datumsangaben **wortgleich** zu den july20-Snapshots aus dem Live-Klon,
  und die Beschreibungs-Schablone ist innerhalb jedes Events über alle
  Märkte identisch (14/14 bzw. 17/17). Der Matcher trägt unverändert:
  Plural/Possessiv/Case zählen, Sigils (`#`/`@`/`$`) davor ok, Compounds
  zählen, Misspellings und Symbole *im* Wort disqualifizieren, eigener
  Text in Quote-/Reply-Posts zählt, zitierter Fremdtext und
  Reposts/ReTruths nicht, Bildtext nur klar ausgeschrieben.
- **Budget beider Profile: Vorwochen-Vorgabe übernommen** (400 gesamt,
  Sweep 50 USD je Clip / 40 Clips — User-Vorgabe 23.07.). Das ist bewusst
  eine Übernahme, keine neue Entscheidung: vor dem Scharfschalten am
  realen Wallet-Stand bestätigen (siehe offene Punkte).
- Suite grün: **1046 Tests** (+12 neue: `test_elon_july27_profil.py`,
  zwei july27-Tests in `test_trump_bot.py`), ruff auf den geänderten
  Dateien sauber (drei F401-Altlasten in `ingest/`/`init_db.py` bestehen
  unabhängig davon weiter).

## Marktlage beim Armieren (Gamma, 27.07. ~20:30 UTC)

**Elon 745693:** 14 Märkte, **alle offen** (kein Vorwochen-Vergleich: am
Tag 1 ist noch nichts aufgelöst). Event-Liquidität 3'113 USD, Volumen
4'553 USD. Wortliste hat rotiert — neu im Board: `Energy` (Ask 0.42),
`Nuclear` (0.20), `Claude` (0.33); raus sind Soccer, Football, Always,
Never, SpaceX. Billigste Kandidaten: `Crypto/Bitcoin` 0.14, `Iran/
Iranian` 0.18, `Nuclear` 0.20, `ChatGPT` 0.22; teuerste: `Tesla` 0.93,
`IPO` 0.84, `China` 0.82.

**Trump 745692:** 17 Märkte, alle offen. Liquidität 7'917 USD, Volumen
19'715 USD. Zwei Märkte sind praktisch durch (`Gold/Golden` Ask 1.00,
`Crime` 0.999 — Trump war schnell); billigste Kandidaten: `Pope` 0.21,
`Scam` 0.29, `Uranium` 0.31, `World Cup` 0.36, `Crypto/Bitcoin` 0.48.
Neu gegenüber der Vorwoche u.a. `President Xi` und `Lindsey/Graham`
(Mehrwort- bzw. Oder-Markt; Regel-Ableitung dafür getestet).

**Nicht erhoben:** die ausführbare CLOB-Tiefe unter dem 0.94-Deckel (die
Tabelle, die das july20-Runbook hatte). Optionaler Schritt vor dem Start;
für die Kauf-Entscheidung selbst holt der Bot das Buch ohnehin live.

## Der Kontext aus zwei Wochen: null Fills

`elon_july13`, `elon_july20` **und** `trump_july20` schlossen alle mit
`fertig … "getradet": []` (die july20-Läufe heute 04:00 UTC, aus den
`bot_events.jsonl` im Live-Klon abgelesen). Die july13-Forensik
(ELON_JULY20_ARMIERUNG.md) gilt unverändert: Erkennung in 15–32 s, aber
beim Trigger verschwindet die Ask-Seite komplett — der Edge lebt davon,
dass ein **niedrig gepreistes** Wort fällt und die Leiter unter 0.94 die
ersten Sekunden übersteht. Eine Trigger-Forensik der july20-Woche steht
noch aus (Buchlogs liegen im Live-Klon). Diese Woche hat auf beiden
Boards mehrere Kandidaten unter 0.40 (Listen oben) — dieselbe offene
Frage wie zuletzt: hält die Leiter im Trigger-Moment.

## Armierungs-Runbook (im ba-thesis-Klon, wo die Bots laufen)

Der Code liegt im Worktree `Projects\wt-elon` auf `feat/elon-bot`.

1. **Mergen.** `feat/elon-bot` → PR → grüne CI → `main`, dann im
   ba-thesis-Klon `git pull`. **ACHTUNG:** In ba-thesis liegen derzeit
   *uncommittete* Änderungen einer anderen Session an
   `operations/pipeline/config.py` und `tests/test_trump_bot.py`
   (Profil `trump_michigan_july27`). Genau diese beiden Dateien fasst
   auch dieser Branch an — vor dem `git pull` muss die andere Session
   ihren Stand committen/mergen, sonst kollidiert der Pull. Nicht über
   ihre Änderungen hinweg stashen oder resetten.
2. **Cookies prüfen.** `X_AUTH_TOKEN` und `X_CT0` stehen in der `.env`
   (Schlüssel am 27.07. geprüft, Gültigkeit zeigt sich erst am laufenden
   Feed). Fehlen/verfallen sie, wartet der Elon-Bot und lädt `.env` jede
   Minute neu. Der Trump-Bot braucht keine Cookies.
3. **Watchdog-Einträge** in `data/live/watchdog.json` → `managed`; die
   beiden july20-Einträge dabei auf `"aktiv": false` (ihr `ende_utc` ist
   erreicht, sie sind sauber mit `fertig` ausgestiegen):
   ```json
   "elon_july27":  {"modul": "elon_bot",  "ende_utc": "2026-08-03T04:00:00Z", "aktiv": true},
   "trump_july27": {"modul": "trump_bot", "ende_utc": "2026-08-03T04:00:00Z", "aktiv": true}
   ```
4. **Startblöcke in `data/live/starte_bots.ps1`** (in den `try`-Teil,
   neben `mrbeast_gaming`/`allin_july24`; die july20-Blöcke raus):
   ```powershell
   # Post-Woche 27.07.-02.08.: beide beenden sich zum Periodenende selbst.
   Starte-Bot "elon_july27" "elon_bot" @("--refresh-rules", "--live")
   Starte-Bot "trump_july27" "trump_bot" @("--refresh-rules", "--live")
   ```
   `data/live/` ist gitignored und existiert nur im Live-Klon — diese
   Blöcke kommen nie über einen PR.
5. **Start — Echtgeld, DU führst das aus.** Immer über das Skript (nimmt
   den `watchdog.lock` gegen Doppelstart), nie `python -m …` von Hand:
   ```bash
   powershell -ExecutionPolicy Bypass -File data\live\starte_bots.ps1
   ```
6. **Erste Kontrolle** in `data/live/<profil>/bot_events.jsonl` je Bot:
   - `startscan` → `erreicht_periodenstart: true` (Elon; sonst
     `startscan_seiten` erhöhen und neu starten). Der Trump-Startscan
     paginiert von sich aus bis zum Periodenstart.
   - `start` → `aktive_maerkte: 14` (Elon) bzw. `17` (Trump).
   - `feed_modus` (Elon) → `reply_abdeckung: true` (siehe offene Punkte).

## Offene Entscheidungen

- **Budget bestätigen (übernommen, nicht neu entschieden).** Beide
  Profile stehen auf 400/50/40 wie in der Vorwoche. Das geteilte Wallet
  trägt parallel noch `mrbeast_gaming` (510) und `allin_july24` (bis
  01.08.); die Summe der Profil-Limits übersteigt den Pool bewusst
  (Vollpool-Prinzip), der Executor-Delta-Sync verhindert Überziehen —
  aber first-come-first-served: ein Trigger kann dem anderen Bot den
  Pool wegkaufen. Belegter Wallet-Stand ist weiterhin nur der vom
  18.07. (530.28) bzw. 23.07. (420.13 pUSD) — **vor dem Start real
  gegenprüfen.**
- **Reply-Abdeckung (Elon), unverändert offen seit dem 16.07.:** Wenn der
  Feed auf `nur UserTweets` degradiert, fehlen Fremd-Replies (zählen laut
  Regel). Selbstheilung probiert `UserTweetsAndReplies` bei jedem Poll
  zuerst; Tiefen-Fallback wäre `APIFY_REPLY_FALLBACK=1` + `APIFY_TOKEN`
  (kostet externe Apify-Läufe). Entscheidung offen.
- **july20-Forensik nachziehen (kein Blocker):** Trigger-Latenzen und
  Buchverhalten der Null-Fill-Woche aus `data/live/elon_july20/` und
  `trump_july20/` auswerten, wie für july13 geschehen — auch als
  Thesis-Material (Liquiditäts- vs. Latenz-Effizienz, Kapitel 4.8).
- **Buchlog-404s** (365/1'138 Runden in der Vorwoche, nur
  Analyse-Zeitreihe): unverändert offen, kein Blocker.
