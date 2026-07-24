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
2. **IR-Zeitverifikation** (Schritt 1) steht aus.
3. **NO-Seite und Gap-Verify** bleiben zu, bis die Capture-Abdeckung
   eines vollen Calls einmal belegt ist (Kandidat: dieser Lauf).
4. **Whisper-Umgebung**: Vollpfad laeuft nur im ba-thesis-Klon
   (.venv mit cuBLAS/cuDNN); dieser Klon hier hat kein faster_whisper —
   Tests und Read-only-Checks laufen, der Audio-Teil nicht.
