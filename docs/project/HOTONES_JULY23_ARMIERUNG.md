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
   kein Modell-Download). Solo-Quellen (Metadaten verifiziert; Sekunden-
   Fenster VOR dem Bauen kurz gegenhören — sie sind Format-Heuristik):

   Bernthal — Refs aus `REAL ONES w/ Jon Bernthal` (`76Ypt7CmYsI`,
   `hC07aVjdRC8`) und JRE #1916 (`mfXxdBMkvhs`); Positiv-Test =
   sein eigenes Hot Ones (`KCVjsbmVi0E`, gleiche Studio-Akustik).

   Holland — Refs aus Rich Roll (`zfyU30zrHHI`), Jay Shetty (`GOqEl4ADyVk`),
   Amy Poehler (`muM7YcClWeU`); Positiv-Test = sein eigenes Hot Ones
   (`qxGmGGmvFD8`).

   Negativ = Sean Evans (`RHEgCocqOM8`) plus lokale `data/live/*/episode.mp3`.

   ```bash
   BOT_PROFIL=hotones_july23 python -m operations.pipeline.baue_referenz_quellen \
     --ziel data/live/hotones_july23/referenz_bernthal.npy \
     --clip "https://youtu.be/76Ypt7CmYsI@START-ENDE" \
     --clip "https://youtu.be/hC07aVjdRC8@START-ENDE" \
     --clip "https://youtu.be/mfXxdBMkvhs@START-ENDE" \
     --test "https://youtu.be/KCVjsbmVi0E@START-ENDE" \
     --negativ "https://youtu.be/RHEgCocqOM8@START-ENDE"
   ```

   Empfehlung: 4–6 Clips à 15–30 s je Person (ECAPA degradiert unter ~3 s).
   Positiv soll klar über 0.50 liegen, Sean-Evans-Negativ klar darunter.
   Für Holland analog mit `referenz_holland.npy`.

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

5. **Start** (der Bot holt den Gamma-Snapshot selbst):
   ```bash
   BOT_PROFIL=hotones_july23 python -m operations.pipeline.bot --refresh-rules --live
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
- **Budget** `max_usd_gesamt = 90` (geteiltes Wallet mit mrbeast_gaming).
  Vor dem Scharfschalten an den realen Wallet-Stand anpassen (belegt ist nur
  der 18.07.-Stand ~340 USD Einzahlung).
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
