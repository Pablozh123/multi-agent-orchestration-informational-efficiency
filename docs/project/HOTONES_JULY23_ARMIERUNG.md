# Armierung Hot Ones — Bernthal ODER Holland (Event 731776)

Stand 23.07.2026 (nachts). Profil `hotones_july23` ist gebaut, getestet und
committet (Branch `feat/hotones-zwei-zielsprecher`). Dieses Dokument ist der
Armierungs-Runbook plus die offenen Entscheidungen. Drop-Erwartung:
**Do 23.07. 15:00 UTC** (11:00 ET), Watcher muss vor ~14:45 UTC laufen.

## Was schon fertig ist (im Code)

- **Zwei Zielsprecher (Union).** `speaker.SpeakerVerifier` nimmt jetzt eine
  Referenzliste; ein Segment gilt ab EINER Referenz über der Schwelle als
  Ziel. YES zählt nur aus Bernthal/Holland-Treffern, der Host (Sean Evans)
  fällt raus. Einzelreferenz-Profile (mrbeast\*) unverändert.
- **Profil `hotones_july23`** in `operations/pipeline/config.py`: YouTube-only
  (@FirstWeFeast `UCPD_bxCRGpmmeQcbe2kpPaA`), enge Event-Bindung
  (`discovery_slug_filter = jon-bernthal-or-tom-holland`, weil die Serie
  monatlich ist und sonst im August auf einen anderen Gast rollt),
  `titel_muster = spicy wings|bernthal|holland`, `titel_verboten` gegen
  Versus/Heat Eaters/Pro Moves/Slice Joint/Hot Kitchen/Wing Pong,
  `yt_min_dauer_s = 1000` (echte Folgen 1244–1596 s).
- **Zähler-Korrekturen (profil-lokal, ohne Wirkung auf andere Profile):**
  Spider/Spider-man-Doppelzählung behoben (`3026024 → ["Spider","Spiderman"]`),
  Bindestrich/Zusammenschreibung für Ice Cream / World Cup / Pit bull,
  ASR-Variante Morocco/Marocco. Homophon-Set je Profil
  (`mate/soccer/wedding/brother`).
- Suite grün (990 Tests), ruff sauber.

## Armierungs-Runbook (im ba-thesis-Klon, wo die Bots laufen)

Der Code liegt hier im Projects-Klon. Erst nach ba-thesis bringen:

1. **Mergen.** `feat/hotones-zwei-zielsprecher` → PR → grüne CI → `main`,
   dann im ba-thesis-Klon `git pull`. Achtung: der Merge fasst
   `speaker.py`/`config.py`/`bot.py` an — Module, die die zwei laufenden
   Echtgeld-Bots (mrbeast_gaming, lemonade_july22) importieren. Nach dem
   Pull **keinen** Watchdog-Neustart dieser Bots in einer Unruhephase
   erzwingen; sie beenden sich ohnehin selbst.

2. **Zwei Referenzstimmen bauen** (ECAPA ist lokal gecacht → nur Downloads,
   kein Modell-Download). Die Fenster wurden aus den Video-Captions
   abgeleitet (Holland: manuelle Captions mit Sprecher-Labels `Tom:`/`Sean:`
   → punktgenau; Bernthal: Auto-Captions, seine langen Antwortblöcke —
   Anfang kurz gegenhören und ggf. 1–2 s trimmen). Fenster = `@start-ende`
   in Sekunden. Kommandos für die ba-thesis-`.venv`:

   **Holland** (alle aus seinem Hot Ones `qxGmGGmvFD8`, reines Tom
   verifiziert; Sean-Evans-Fenster derselben Folge + lokale Männerstimmen
   als Negativ):
   ```bash
   BOT_PROFIL=hotones_july23 .venv/Scripts/python -m operations.pipeline.baue_referenz_quellen \
     --ziel data/live/hotones_july23/referenz_holland.npy \
     --clip "https://youtu.be/qxGmGGmvFD8@55-83" \
     --clip "https://youtu.be/qxGmGGmvFD8@160-188" \
     --clip "https://youtu.be/qxGmGGmvFD8@286-314" \
     --clip "https://youtu.be/qxGmGGmvFD8@497-525" \
     --clip "https://youtu.be/qxGmGGmvFD8@838-866" \
     --test "https://youtu.be/qxGmGGmvFD8@1230-1258" \
     --negativ "https://youtu.be/qxGmGGmvFD8@15-35" \
     --negativ "https://youtu.be/qxGmGGmvFD8@1372-1400" \
     --negativ "data/live/jre_july6/episode.mp3@1800-1830" \
     --negativ "data/live/allin_july17/episode.mp3@1800-1830"
   ```

   **Bernthal** (vier Fenster aus seinem Hot Ones `KCVjsbmVi0E` + Cold-Open
   aus `REAL ONES` `76Ypt7CmYsI` für Aufnahme-Varianz; Positiv-Test =
   ausgehaltenes Hot-Ones-Fenster):
   ```bash
   BOT_PROFIL=hotones_july23 .venv/Scripts/python -m operations.pipeline.baue_referenz_quellen \
     --ziel data/live/hotones_july23/referenz_bernthal.npy \
     --clip "https://youtu.be/KCVjsbmVi0E@250-278" \
     --clip "https://youtu.be/KCVjsbmVi0E@402-430" \
     --clip "https://youtu.be/KCVjsbmVi0E@667-695" \
     --clip "https://youtu.be/KCVjsbmVi0E@824-852" \
     --clip "https://youtu.be/76Ypt7CmYsI@1-19" \
     --test "https://youtu.be/KCVjsbmVi0E@588-614" \
     --negativ "https://youtu.be/qxGmGGmvFD8@15-35" \
     --negativ "data/live/jre_july6/episode.mp3@1800-1830" \
     --negativ "data/live/allin_july17/episode.mp3@1800-1830"
   ```

   Inhalte der Fenster (zum schnellen Gegenhören):
   - Holland `@55` Nando's/spicy · `@160` Puppeteer-Arme · `@286` Downey/Marty ·
     `@497` „Spider-Man suit" · `@838` Water-Tank-Set · `@1230` (Test) Drama-School/Downey
   - Bernthal `@250` „nowhere to hide" (Theater) · `@402` „you buy it" (Fights) ·
     `@667` Dogs on set · `@824` Masculinity · `76Ypt…@1` Cold-Open „violence scale" ·
     `KCV…@588` (Test) Sweatpants-Story

   Empfehlung: 15–30 s je Clip (ECAPA degradiert unter ~3 s). Positiv-Test
   soll klar über 0.50 liegen, alle Negative klar darunter.

3. **Schwelle prüfen.** Start bei `sprecher_schwelle = 0.50`. Wenn der
   Positiv-Test nur knapp über 0.50 und Evans nah dran liegt: anheben. Zwei
   Referenzen = zwei Chancen auf Fehlzurechnung, deshalb eher zu hoch als
   zu tief.

4. **Watchdog-Eintrag** in `data/live/watchdog.json` → `managed`:
   ```json
   "hotones_july23": {"modul": "bot", "ende_utc": "2026-07-25T04:00:00Z", "aktiv": true}
   ```
   `ende_utc` an die **Regel-Deadline** (24.07. 23:59 ET = 25.07. 03:59 UTC)
   hängen, NICHT an das Gamma-`endDate` (23.07. 23:59 UTC) — sonst killt der
   Watchdog den Bot vor einem verspäteten Upload.

5. **Start — Echtgeld, DU führst das aus** (der Bot holt den Gamma-Snapshot
   selbst und platziert live Orders auf Polymarket). Vor ~14:45 UTC starten:
   ```bash
   BOT_PROFIL=hotones_july23 .venv/Scripts/python -m operations.pipeline.bot --refresh-rules --live
   ```
   Direkt nach dem Trigger den Folgen-Titel manuell gegenchecken — der Titel
   der Duo-Folge ist bis zum Upload unbekannt (Wikipedia-Eintrag ist
   Platzhalter), und YouTube testet Titel live gegeneinander.

## Offene Entscheidungen (bewusst konservativ vorbelegt)

- **NO-Seite ist AUS** (`no_ask_obergrenze = 0.0`, nur YES). Der NO-Zweig
  entscheidet auf dem Gesamtzähler aller Stimmen — auf einem Host-dominierten
  Gast-Markt untauglich. Im Februar löste die Serie 13/22 Märkte zu NO auf;
  wer NO handeln will, braucht zuerst einen **gast-only erweiterten Zähler**
  (erweitert_count nur aus `ist_ziel`-Segmenten) + Kalibrierung — echter
  Code-Eingriff mit Testbedarf, nicht heute Nacht blind scharf schalten.
- **Budget** `max_usd_gesamt = 400`, Standard-Sweep `50`/Markt, `40` Clips
  (User-Vorgabe 23.07., „Ausführung wie immer" = wie `allin_july17`).
  Achtung dünne Bücher (Serien-Liquidität ~2000 USD, mehrere Märkte nur
  8–17 USD Tiefe unter dem Deckel) → 50/Markt kann slippen. Geteiltes
  Wallet mit mrbeast_gaming; vor dem Scharfschalten am realen Wallet-Stand
  gegenprüfen (belegt ist nur der 18.07.-Stand ~340 USD Einzahlung — 400
  kann den Pool je nach parallelem Bot übersteigen; der Executor-Delta-Sync
  verhindert Überziehen, aber ein Profil kann dem anderen den Pool wegkaufen).
- **Homophon-Gate** kann YES auf soccer/wedding/brother abschalten, wenn die
  Segment-Konfidenz auf Hot-Ones-Audio (Essen, Lachen, Husten) oft < 0.8
  liegt. Auf der Radcliffe-Folge (Serie 12334, Event 214212) einmal messen.
- **Timothy** (`3026031`) bewusst OHNE Override: ob der Resolver „Timothée"
  (Chalamet) als „Timothy" wertet, ist offen. Kein YES darauf ohne Klärung.

## Bekannte Baustellen im geteilten Code (separater PR, nicht dieser Lauf)

Die profil-lokalen Overrides umgehen zwei generische Zähler-Fehler; die
richtige Lösung fasst geteilten Code an und braucht eigene Tests:
- `counter_engine.compile_patterns` behandelt Bindestriche nur bei
  Mehrwort-Begriffen korrekt, wenn eine hyphenierte Variante gelistet ist
  (Fix: `\ ` → `[\s\-]+`).
- Präfix-Doppelzählung (`Spider`+`Spider-man`) generisch in `build_rule`
  entschärfen statt je Markt.
- `basisraten.wort_schluessel` matcht bei Gast-wechselnden Serien-Slugs nie
  (Hot-Ones-/Radcliffe-Klasse) — die Basisraten-Schicht ist hier wirkungslos.
