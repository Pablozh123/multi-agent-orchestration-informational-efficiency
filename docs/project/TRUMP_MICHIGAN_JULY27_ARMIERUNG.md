# Armierungs-Runbook: Trump-Michigan-Rede, 27.07.2026 (Event 745732)

Status: gebaut und getestet (Suite 1062 gruen), **nicht scharf**.
Dry-Run ist Standardmodus. Erstellt 27.07.2026 ~15:30 CEST — die Rede
beginnt heute 21:00 CEST (15:00 ET, C-SPAN listet 14:50 ET; Trump-
typisch 30–60 min Verzug). Kontext und Marktdaten:
`RECHERCHE_EARNINGS_QUELLEN_2026-07-27.md` §4.

## 1. Was gebaut wurde (Branch feat/earnings-bot)

Profil `trump_michigan_july27` fuer den **earnings_bot** (Event ohne
Drop-Ereignis; Audio via Loopback). Sprechergebundene Events brauchen
gegenueber Earnings zwei zusaetzliche Gates, beide sind drin:

1. **Klausel-Gate ersetzt Anyone-Gate** (`sprecher_klausel_muster`):
   Maerkte sind nur aktiv, wenn die Beschreibung exakt "if Trump says
   the listed term" traegt. Earnings-Profile unveraendert (Regression
   getestet).
2. **ECAPA-Sprecher-Verifikation** (Infrastruktur von mrbeast_gaming/
   hotones wiederverwendet): jedes Transkript-Segment wird der
   Referenzstimme zugerechnet; **YES kauft nur aus Trump-zugerechneten
   Treffern** (ziel_count). Schwelle 0.50 (Praezision vor Recall).
   Referenz: `data/live/trump_michigan_july27/referenz_stimme.npy` —
   **Pflicht bei --live**, Dry-Run laeuft auch ohne (Warnung,
   Messbetrieb).
3. **Operator-Marker** `data/live/trump_michigan_july27/SPRECHER_AKTIV`:
   Bis die Datei existiert, zaehlt der Bot nur (Vorprogramm/Vorredner
   sichtbar im Log), kauft aber nie — auch Endcheck/Nachlauf nicht,
   falls der Marker nie gesetzt wird. Einmal gesetzt = frei (Latch);
   die Feinarbeit waehrend der Rede (Gaeste am Mikro, "Trump!"-Chants
   des Publikums) macht die ECAPA-Zurechnung je Segment.
4. **ASR-Zaehlfallen behoben** (markt_varianten_override):
   "Percent" 15+ zaehlt auch "%" (Whisper schreibt "50%") und
   "per cent"; "Drill, Baby, Drill" mit ASR-Kommas; USMCA/NAFTA mit
   Punkt-Schreibweisen. Oder-Brackets (Joe/Biden 12+, Oil/Gas 10+)
   summieren beide Begriffe — entspricht der kombinierten Zaehlung des
   Event-Mentions-PDF.
5. Unveraendert aus dem Earnings-Design: Trigger-Verify (large-v3,
   fail-closed) an, NO-Seite zu (0.0), Vorscan-Pause, Kill-Switch,
   Startwache, Event-ID-gebundener Refresh, not-air-Markt skip.
6. **Nachtrag 27.07. ~16:00 (User-Entscheide):** (a) Budget-Vorgabe:
   Fokus YES-Einzelwoerter, **Kappe 100 USD je Markt** (2 FAK-Clips a
   50 — grosse Clips, weil Asks nach dem Fall in Sekunden weg sind),
   Pool 400, Brackets laufen mit derselben Kappe. (b) **Fernstart**:
   `trump_michigan_start.py` loest die /live-URL (WhiteHouse -> RSBN ->
   FOX2Detroit) per yt-dlp auf, pollt bis der Stream live ist und
   startet den Bot mit `--stream` — kein Browser, kein Loopback.
   (c) **Auto-Marker**: 6 Trump-zugerechnete Segmente (>= 1 s) im
   rollenden 5-Chunk-Fenster setzen den Marker selbst (nur mit aktivem
   ECAPA-Verifier — ohne Referenz nie). Hand-Marker und STOP bleiben:
   `trump_michigan_marker.cmd`, `bot_stop.cmd` /
   `bot_stop_aufheben.cmd` im Repo-Root. (d) Beifang: allin_july24-
   Profil von main in die Branch-config uebernommen — der Watchdog
   haelt es bis 01.08. aktiv (E283 Fr 31.07.), die Handkopie vom
   24.07. haette einen All-In-Neustart mit KeyError sterben lassen.

## 2. Erwartungsbild (Gamma 27.07., ~13:00 UTC)

26 Maerkte, Liq 66.4k, Vol 115.1k — liquidestes Event der Serie, die
Crowd hoert live mit. Einzelwoerter gelten als verloren (Reprice ~4 s);
der Kanal sind die **6 Brackets**: Percent 15+ (0.665), Joe/Biden 12+
(0.495), Oil/Gas 10+ (0.445), Hell 7+ (0.695), Trump 5+ (0.745),
Job 20+ (neu seit 25.07.). YES ab Zaehler >= Schwelle + 2 (Puffer),
Deckel 0.90, je EIN Kauf pro Markt. `--status` muss zeigen:
25 aktive Regeln, 1 Skip (not air), sprecher_gebunden true.

## 3. Armierungs-Schritte (Live-Klon ba-thesis, heute)

0. Branch pullen: `git fetch && git checkout feat/earnings-bot && git pull`.
1. **Referenzstimme bauen** (~20 min, einzige neue Handarbeit).
   Quelle: beliebige juengere Rede mit langen Trump-Solo-Passagen auf
   YouTube; Sekunden-Spannen selbst waehlen (NUR Trump, keine Musik,
   kein Applaus-Teppich). Negativ-Kontrollen: Stimmen, die HEUTE vor
   ihm sprechen koennten (Lokalpolitiker/Moderator), ersatzweise ein
   beliebiger Fremdsprecher:
   ```
   set BOT_PROFIL=trump_michigan_july27
   python -m operations.pipeline.baue_referenz_quellen ^
     --ziel data/live/trump_michigan_july27/referenz_stimme.npy ^
     --clip "https://youtu.be/<REDE>@<s1>-<s2>" ^
     --clip "https://youtu.be/<REDE>@<s3>-<s4>" ^
     --clip "https://youtu.be/<REDE>@<s5>-<s6>" ^
     --test "https://youtu.be/<ANDERE_REDE>@<t1>-<t2>" ^
     --negativ "https://youtu.be/<FREMDSPRECHER>@<n1>-<n2>"
   ```
   Kalibrier-Ausgabe pruefen: Positiv klar UEBER 0.50, Negativ klar
   darunter. Trumps Stimme ist distinktiv — erwartbar unproblematisch.
2. **Regeln ziehen und gegenlesen**:
   `python -m operations.pipeline.earnings_bot --refresh-rules --status`
   (Erwartungsbild §2; neue Maerkte seit 25.07. fallen hier auf).
3. **Stream waehlen** (20:30): **kommentarfreier Feed ist Pflicht** —
   C-SPAN oder White House YouTube, NICHT Fox/CNN-Simulcasts (Anchor-
   Voiceover laeuft sonst in den Zaehler; ECAPA faengt das zwar, aber
   unnoetiges Risiko). RSBN taugt als Backup (waehrend der Rede clean,
   davor Host-Talk — Marker-Gate deckt das). Latenz ist fuer Brackets
   zweitrangig: Stabilitaet > 10 s Vorsprung. Zweiten Stream als
   Backup-Tab offen halten, stumm.
4. **Audio-Strecke testen** (20:30, wie AXP): Browser-Audio auf das
   Loopback-Geraet, `--liste-geraete`, Pegel in `call_audio.wav`.
5. **Budget-Entscheid** (Platzhalter 100 USD) + Wallet-Stand pruefen.
6. **Start ~20:45 CEST** (Capture VOR dem Vorprogramm schadet nicht,
   leere Chunks kosten nichts):
   `python -m operations.pipeline.earnings_bot --geraet "<Loopback>" --live`
   (Dry-Run/Messlauf: dasselbe ohne `--live`; laeuft auch ohne
   Referenz.) GPU-Last: small + large-v3 + ECAPA ~4–5 GB — die
   Wochenprofile sind seit 27.07. 03:59 UTC zu, GPU frei.
7. **Sobald Trump am Pult steht** — Marker setzen (zweites Terminal):
   `type nul > data\live\trump_michigan_july27\SPRECHER_AKTIV`
   Vorher kauft nichts, egal was der Zaehler zaehlt.
8. **Rede-Ende**: Ctrl+C -> Endcheck + 30 min Nachlauf. Notaus:
   `data/live/STOP`.

## 3b. Erledigt-Stand 27.07. ~16:30 CEST (alles im Live-Klon)

- Handkopie fortgeschrieben (Betriebsmodus des Live-Klons: main +
  Branch-Dateien; Hashes vorab verifiziert, keine fremde Arbeit
  ueberschrieben): config.py, earnings_bot.py, trump_michigan_start.py,
  vier .cmd im Root, Testdateien. **53/53 Kompatibilitaets-Tests gruen
  im Live-Klon** (Branch-Code gegen main-Module).
- **Referenzstimme gebaut und kalibriert**: Quelle WH-Ansprache
  16.07.2026 (iIlqG0untYM, 3x30 s Solo), Positiv-Kontrolle WH-Ansprache
  01.04.2026: **0.903**, Negativ-Kontrolle AXP-Call-Audio: **0.079** —
  Schwelle 0.50 liegt mittig mit grossem Abstand.
- **Smoke-Test bestanden** (Dry-Run gegen AXP-WAV): 25 aktive Maerkte,
  ECAPA/large-v3/small alle cuda, Zaehlkette belegt ("Percent" = 59
  auf dem Earnings-Audio — das %-Gate greift), **ausgegeben 0.00**:
  Marker nie gesetzt, Auto-Marker feuerte nicht (fremde Stimmen),
  alle Kaufsperren hielten trotz Zaehler weit ueber Schwelle.
- Zwei dabei gefundene Bugs gefixt (Commits 43d898e ff.): --wav-
  Trockenlauf bekam faelschlich Netz-Optionen (ffmpeg-Sofortabbruch);
  Fernstart brauchte Titel-Gate + is_live-Check, weil FOX2Detroit
  24/7 auf derselben /live-URL streamt (live verifiziert: Dauerstream
  wird abgelehnt).
- Scharf schalten macht der User: Scheduled Task oder Doppelklick auf
  `trump_michigan_start_live.cmd` (siehe Chat-Vorgabe); Notaus
  `bot_stop.cmd`, Hand-Marker `trump_michigan_marker.cmd`.

## 4. Risiken / bewusste Grenzen

- **ECAPA-Referenz heute frisch kalibriert** (nicht ueber Tage
  erprobt): Schwelle 0.50 + Trigger-Verify + Marker sind die drei
  Schichten; ein Rest-Risiko der Fehlzurechnung bleibt. Verpasster
  YES kostet 0 — im Zweifel lehnt das System ab (fail-closed ueberall).
- **Q&A/Zwischenrufe**: Reporterfragen zaehlen nicht als "Trump says";
  ECAPA rechnet sie nicht zu. Naechster Sprecher am selben Mikro
  mitten in der Rede: ECAPA-Fall, Marker bleibt gesetzt (Latch).
- **Startzeit-Chaos**: call_max_minuten 180; bei extremem Verzug
  `--minuten` erhoehen oder neu starten.
- **NO-Seite bleibt zu** — beim sprechergebundenen Event zusaetzlich
  begruendet: der Gesamtzaehler ist kein Abwesenheits-Proxy fuer den
  Zielsprecher (Hot-Ones-Lehre).
- **ToS/Mitschnitt**: oeffentlich ausgestrahlte Polit-Rede auf
  frei zugaenglichen Streams — weniger heikel als IR-Webcasts mit
  Registrierung, aber die generelle Mitschnitt-Frage (Recherche §7/
  §10) bleibt beim User.
- Morgen 14:00/16:30 CEST folgen PayPal + Boeing (Profile noch NICHT
  angelegt), Mittwoch 14:30 P&G — GPU-/Wallet-Planung beachten.
