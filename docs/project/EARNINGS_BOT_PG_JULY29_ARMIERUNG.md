# Armierungs-Runbook: Earnings-Bot, P&G Q4 FY2026 (Event 715467)

Status: gebaut und getestet, **nicht scharf**. Dry-Run ist Standardmodus.
Erstellt: 24.07.2026. Gegenstuecke: `RECHERCHE_EARNINGS_CALL_MENTIONS_2026-07-22.md`
(wie schnell ist der Markt), `MESSPROTOKOLL_LIVESTREAM_LATENZ_2026-07-22.md`
(wie schnell sind wir, Zugangsblocker).

## 1. Was gebaut wurde

Die Polymarket-Verbindung fuer Live-Webcast-Events, als Abschluss der
Strecke Audio → Zaehlung → **Entscheidung → Order**:

- `operations/pipeline/earnings_bot.py`: Runner fuer Events ohne
  Drop-Ereignis. Audio via Loopback-Geraet (`--geraet`, Nutzer spielt den
  Webcast selbst ab), direkte Medien-URL (`--stream`) oder Datei
  (`--wav`, Trockenlauf). Wiederverwendet unveraendert: `build_rules`,
  `ChunkTranscriber`, `StreamingCounter`, `decision`, `execution`
  (Dry-Run/Live-Executor mit FAK-Sweep, Kill-Switch `data/live/STOP`,
  Startwache, Wallet-Delta-Sync).
- Profil `earnings_pg_july29` in `operations/pipeline/config.py`
  (additiv; alle anderen Profile unveraendert, belegt per Test).
- Earnings-Gates gegen die belegten Fallen:
  - **Anyone-Klausel je Markt**: aktiv nur mit "mentioned by anyone" in
    der Beschreibung. Die Elon-Serie filtert auf Markt-Ebene nach
    Sprecher (Recherche §2) — solche Maerkte gehen auf SKIP.
  - **Schwelle NUR aus dem Fragetext** ("N+ times"). Das Gamma-Feld
    `groupItemThreshold` ist ein Sortier-Index, KEINE Zaehlschwelle
    (AXP-Event: Einzelwort-Maerkte tragen 3/4/5, "Income 10+" traegt 0).
    Die Annahme aus Recherche §9, das Feld liefere die Brackets, war
    falsch — per Regressionstest festgenagelt.
  - **Kein Auto-Discovery-Rollover**: Earnings-Slugs sind Rolling Slugs;
    der Snapshot-Refresh bleibt an Event-ID 715467 gebunden.
  - Geschlossene Maerkte und der "not air"-Negationsmarkt: SKIP.
- Komposita-Overrides fuer "World Cup" und "Toilet paper"
  (Bindestrich-/Zusammenschreibung, Vorbild hotones_july23).
- Tests: `tests/test_earnings_bot.py` (13 Tests, offline gegen die
  echten market_ids/Fragen). Suite gesamt 1040 gruen, ruff sauber.

**Bewusst NICHT gebaut:** NO-Seite (`no_ask_obergrenze` 0.0) und
Gap-Verify. Live-Capture hat keine belegte Abdeckungsgarantie (spaeter
Einstieg, Quellen-Aussetzer) — der erweiterte Zaehler taugt dann nicht
als Abwesenheits-Proxy (E281-Lehre, verschaerft). Erst nach
Abdeckungs-Kalibrierung oeffnen. Ebenfalls nicht gebaut: automatisierter
Webcast-Login oder Registrierung (Zugang bleibt Handarbeit im Browser).

## 2. Zielmarkt (Gamma/CLOB, erhoben 24.07.2026)

Event 715467, 22 Maerkte, Liquiditaet 13'392 USD, Volumen 3'672 USD
(Stand Public-Search 24.07.). **8 Zaehl-Brackets**: Income/Quarter/
Fiscal/Innovation/Revenue/Consumer/Profit je 10+, Customer 5+ — mehr als
Tesla (5). Offene Ausgaenge (0.10–0.90) beim Erheben: Customer 5+ 0.220,
Trump 0.155, Valuation 0.160; dazu knapp darunter Income 10+ 0.060,
Revenue 10+ 0.080, Profit 10+ 0.059, World Cup 0.100, Toilet paper 0.040.
`--status`-Lauf 24.07.: 21 aktive Regeln, 1 Skip (not-air), 10 Buecher
mit YES-Ask <= 0.90.

Erwartung aus den drei Messungen (Tesla Jan, GM, Tesla Jul): Einzelwort-
Maerkte repricen in ~4 s — dort ist mit 10–15 s Pfadlatenz kein Fill zu
erwarten. Der Anwendungsfall sind die **Brackets**, deren Zaehlstand sich
ueber 45–70 Minuten aufbaut (Verarbeitungs- statt Latenzvorsprung, GM-
Gegenbeispiel dokumentiert). Der Lauf produziert in jedem Fall den
vierten selbst erhobenen Reprice-Datenpunkt samt eigener Zaehl-Zeitreihe.

## 3. Armierungs-Schritte (im Live-Klon ba-thesis)

Der Branch wird wie ueblich per PR gemergt, dann im ba-thesis-Klon pullen.
Die Elon-/Trump-Wochenprofile enden 27.07. 03:59 UTC — der Call am 29.07.
kollidiert nicht mit deren GPU-Nutzung.

1. **Call-Zeit an der IR-Quelle pruefen** (pgim vestor.com bzw.
   P&G-Pressemitteilung). Polymarket sagt 29.07. 08:30 ET = 12:30 UTC.
   Dow-Falle: Beschreibung nannte 9 AM, die Firma 8 AM (Messprotokoll §8).
   Weicht die Zeit ab: `call_start_utc` im Profil korrigieren (nur Doku/
   Wartezeit; der Bot startet ohnehin manuell).
2. **Webcast-Zugang am Vortag pruefen**: offener Stream oder
   Registrierung? Registrierung macht der Nutzer selbst im Browser —
   der Bot hoert nur das Loopback-Geraet. ToS-Frage siehe §4.
3. **Audio-Strecke testen** (wie beim AXP-Paper-Lauf 24.07.):
   `--liste-geraete`, Webcast-Testton oder beliebiges Browser-Audio auf
   dasselbe Ausgabegeraet, Pegel im entstehenden `call_audio.wav` pruefen.
4. **Regeln gegenlesen**:
   `set BOT_PROFIL=earnings_pg_july29`
   `python -m operations.pipeline.earnings_bot --refresh-rules --status`
   — Skips, Brackets und Deckel muessen dem Erwartungsbild aus §2
   entsprechen; neue/geaenderte Maerkte fallen hier auf.
5. **Dry-Run-Probe** (Pflicht vor --live): kompletter Durchlauf mit
   `--wav <Testdatei>` oder `--geraet` und beliebigem Audio; prueft
   Chunks, Zaehler, Entscheidungslog, Finale und Nachlauf ohne Wallet.
6. **Budget-Entscheid der Studentin**: Profil traegt den Platzhalter
   `max_usd_gesamt` 100 mit Standard-Clips (15 USD / 10 je Markt).
   Vor --live bestaetigen oder anpassen; Wallet-Stand gegen parallele
   Profile pruefen (Executor-Delta-Sync verhindert Ueberziehen).
7. **Scharf** (nur nach 1–6): ~15 min vor Call-Start Webcast im Browser
   starten, dann
   `python -m operations.pipeline.earnings_bot --geraet "<Loopback>" --live`
   (braucht `.env` POLY_PRIVATE_KEY und eingerichtete Deposit-Wallet).
   Ohne `--ab`: Capture beginnt sofort; leere Vor-Call-Chunks kosten
   nichts und sichern den Call-Anfang.
8. **Call-Ende**: Ctrl+C ausloest das Finale (letzter YES-Blick,
   NO-Runde uebersprungen, 30 min Nachlauf). Notaus jederzeit:
   `data/live/STOP`.

## 4. Offene Punkte (vor produktivem Einsatz)

1. **ToS-/Rechtslage des Webcast-Mitschnitts** — aus Recherche §7/§10
   unveraendert offen und ausdruecklich VOR jedem scharfen Einsatz zu
   klaeren. Entscheid liegt bei der Studentin. Der Loopback-Weg vermeidet
   automatisierte Zugriffe, ersetzt die Klaerung aber nicht.
2. **IR-Zeitverifikation** (Schritt 1): erledigt 27.07. — P&G-PM vom
   01.07.2026 (us.pg.com/Businesswire) bestaetigt Mi 29.07., 8:30 a.m.
   ET, offener Live-Audio-Webcast auf pginvestor.com, keine
   Registrierung erwaehnt. `call_start_utc` 12:30 stimmt. Quellen in
   `RECHERCHE_EARNINGS_QUELLEN_2026-07-27.md`.
3. **NO-Seite und Gap-Verify** bleiben zu, bis die Capture-Abdeckung
   eines vollen Calls einmal belegt ist (Kandidat: dieser Lauf).
4. **Whisper-Umgebung**: Vollpfad laeuft nur im ba-thesis-Klon
   (.venv mit cuBLAS/cuDNN); dieser Klon hier hat kein faster_whisper —
   Tests und Read-only-Checks laufen, der Audio-Teil nicht.

## 5. Nachtrag 27.07.: AXP-Erstlauf (LIVE) und zwei Haertungen

**Erstlauf 24.07., American Express (Event 715475, Profil
`earnings_axp_july24`), auf User-Entscheid direkt scharf statt Dry-Run.**
Setup stand 90 s vor Call-Beginn (Whisper cuda/float16 nach 5 s), 470
Chunks ohne einen Fehler-Event, Ctrl+C-Finale sauber. Zwei Kaeufe, beide
per UMA YES aufgeloest: Luxury YES @0.56 (58.79 USD, 4 Clips) und Fraud
YES @0.52 (15 USD) — **realisierter PnL +60.06 USD** auf 73.79 Einsatz.
Die Bruecken-Befunde: Brackets waren vorgepreist (Quarter auf 25/10
gezaehlt, nie ein Ask unter 0.90), gefallene Einzelwoerter sofort tot —
der reale Kanal sind **mittelpreisige, von der Crowd nicht mitgehoerte
Woerter** (Aufmerksamkeits-, kein Latenz-Edge). Beide Kaeufe hingen an je
EINEM small-Treffer gegen einen zweifelnden Markt (Buecher nach Kauf bei
0.33/0.06) — richtig, aber strukturell E281-Risiko.

**Haertung 1 — Vorscan-Pause fuer tote Buecher:** 2029 von 2081
YES-Entscheidungen waren Wiederholungen auf Maerkten ohne Asks (1–2 s
unnoetige Roundtrips je Chunk im heissen Pfad). Leere Buecher pausieren
jetzt wie zu teure; Re-Check am Call-Ende bleibt.

**Haertung 2 — Trigger-Verifikation (`trigger_verify.py`):** Jeder
YES-Trigger wird vor dem Kauf mit large-v3 (warm geladen beim Start,
~1–3 s je Fenster) ohne VAD nachtranskribiert und strikt nachgezaehlt.
Fail-closed auf allen Kaufpfaden (Chunk, Endcheck, Nachlauf): keine
Bestaetigung -> kein Kauf; eine Ablehnung sperrt bis zum naechsten
neuen Treffer. Laedt das Modell nicht, bricht der Start ab (bewusst
ohne: `--ohne-trigger-verify`). Profile: `trigger_verify_aktiv` True
fuer beide Earnings-Profile, Podcast-Profile unveraendert.

**Terminal:** Die taegliche Kette hat den Lauf am 27.07. automatisch
publiziert (runs.json: 14 Runs, AXP mit Einsatz 73.79 / PnL +60.06);
Resolutions- und Tape-Cache liegen in `data/raw/live_runs/`. Die
versionierten Kurat-Kopien (`data/live_curated/`) sind auf alle 14
Laeufe aufgefrischt.

**Fuer den P&G-Call unveraendert offen:** Budget-Entscheid (Platzhalter
100 USD), ToS-Frage (§4.1); IR-Zeitverifikation am 27.07. erledigt
(§4.2, Webcast offen auf pginvestor.com).
Neu zu beachten: large-v3 laeuft beim Call zusaetzlich zum
small-Transcriber auf der GPU (zusammen ~4–5 GB VRAM; auf der
Maschine bereits am 18.07. fuer Gap-Verify gemessen).

## 6. Lauf-Ergebnis 29.07. (Nachtrag)

Start 14:29 CEST (T-1 min; Budget-Entscheid User 650/50x40 kam
14:25, Ein-Zeilen-Deploy fb07bd7 vor dem Start; Dry-Run-Probe §3.5
entfiel bewusst — zwei saubere Live-Laeufe derselben Codebasis am
Vortag). Loopback CABLE Output, erster large-v3-Hauptlauf der
Earnings-Strecke, **582 Chunks / 97 min LUECKENLOS (null Stalls —
erste belegte Vollabdeckung eines kompletten Calls, §4.3-Vorbehalt
damit erfuellt)**. Ende per STOP-Datei 16:04, sauberes fertig-Event,
STOP wieder aufgehoben.

**0 Fills bei 10 Verifys (0 Fehltrigger).** Vier Brackets ueber
Schwelle — Consumer 33, Quarter 25, Fiscal 23, Innovation 11 —
alle vorgepreist (Quarter-Entscheid 12:38: ask 0.996). Die
Zweifel-Brackets (Customer 5+ 0.22, Income/Revenue/Profit 10+
0.06-0.08) erreichten die Schwelle NIE (Endstaende 2/1/0/1) — der
Markt lag mit seinem Zweifel richtig. **Vierter Beleg der
Bracket-These, und eine Verschaerfung: Das Bracket-Fenster braucht
ein vom Markt UNTERSCHAETZTES Bracket; heute existierte keins.**

**Valuation-Fall (Kalibrierpunkt, laufende UMA-Beobachtung):** Markt
stand nach Call-Ende bei 0.495 (vor Call 0.16); User-Ohr meinte
"gehoert". Durchgehender VAD-freier large-v3-Vollpass ueber das
GANZE Band: valuation 0, evaluation/validation 0, nacktes "value"
19x. Nach den Late-Regeln vom 28.07. in BEIDE Richtungen
unhandelbar (Nachbarform-Risiko: 19 value-Kandidaten; kein
Zwei-Methoden-Konsens, Ohr widerspricht). Das UMA-Endergebnis
kalibriert die Resolver-Wertung von value/valuation
(Guidance-Analogie).

**Aufgeklaert per Wort-Zeitstempel + On-chain-Abgleich:** Die
Verhoerer-Stelle ist Band 1546-1551s — "the next S-curve of growth
and VALUE CREATION for P&G" (phonetisch ≈ valuation); der manuelle
User-Kauf YES @0.274 (15 USD) kam 5 s spaeter (12:53:47Z,
on-chain). Der Markt-Sprung 0.16→0.50 ist ein KOLLEKTIVER
Verhoerer — erster vollstaendig dokumentierter Fall (Audio +
Zeitstempel + Kaufzeit + Marktreaktion). Zweiter manueller Trade
des Tages: Fiscal-10+-NO @0.044 (10 USD) gegen Endstand 23 →
verloren (Lehre: vor Bracket-Lotterien den Sichtfenster-Stand
pruefen).

**Weitere Zweifelsfaelle nach Call-Ende (Vollpass-Transkript
`vollpass_durchgehend_large_v3.txt` im Lauf-Ordner):** World Cup
Markt 0.45 bei Vollpass-0 OHNE Verhoerer-Anker (nicht mal
"world-class" fiel) — Marktzweifel ohne Audio-Basis; Customer 5+
Markt 0.595 bei exakt 2x "customers" (Vollpass = Bot-Zaehler) —
resolvet das YES, ist es nach Guidance der zweite harte
Resolver-Fehler-Kandidat. Erste Proposals 17:0x eingelaufen, alle
eindeutigen Faelle konsistent.
