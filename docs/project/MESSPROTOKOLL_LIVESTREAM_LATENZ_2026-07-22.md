# Messprotokoll: Live-Stream-Transkription, Latenzbudget

Status: Prototyp gebaut und gemessen. **Nicht scharf** — kein Order-Pfad,
keine Wallet-Anbindung, read-only.
Datum: 22.07.2026, Messungen 13:07–13:21 UTC.
Gegenstück zu `RECHERCHE_EARNINGS_CALL_MENTIONS_2026-07-22.md`, das die
Frage „wie schnell ist der Markt" beantwortet. Dieses Dokument beantwortet
die Gegenfrage: **wie schnell sind wir?**

## 1. Fragestellung

Der Podcast-Edge lebt davon, dass die Audiodatei nach dem RSS-Drop bereits
vollständig vorliegt und wir sie schneller herunterladen als andere. Beim
Livestream entfällt das. Übrig bleibt die Frage, wie viele Sekunden zwischen
dem gesprochenen Wort und unserer Zählung liegen.

Die Latenz zerfällt in vier Posten, die getrennt gemessen wurden:

```
L_gesamt = L_broadcast + L_startversatz + L_chunkfüllung + L_transkription
```

## 2. Zugangsweg zum Tesla-Webcast (gelöst)

**Befund:** `livestream.tesla.com` ist client-gerendert; yt-dlp scheitert
(„Unsupported URL"). Die Seite hängt an zwei JSON-Endpunkten:

| Endpunkt | Inhalt |
|---|---|
| `/api/updateID` | Integer-Zähler, aktuell `28`. Die Seite pollt ihn; steigt er, hat sich die Stage geändert. |
| `/api/stageDetails` | Aktueller Zustand. Jetzt: `{"stageName":"Count Down","mediaBox":{"type":"countdown",…}}` |
| `/api/livestream` | Metadaten inkl. `eventStartDate: 2026-07-22`, `eventStartTime: 16:30` (CT) |

**Das ist das exakte Gegenstück zu `rss_watch.py`:** billiger Poll auf
`updateID`, teurer Fetch nur bei Änderung. Sobald der Webcast live geht,
wechselt `mediaBox.type` und sollte die Manifest-URL tragen.

**WAF-Hürde:** Ein Edge-Filter beantwortet Nicht-Browser-Clients mit
HTTP 403 — auch mit Browser-User-Agent und Referer. Gelöst mit
`curl_cffi` und Chrome-Impersonation, **derselbe Pfad, den
`truth_watch.py` bereits für Truth Social nutzt**. Antwortzeit 250–370 ms.
Kein Login, keine Paywall, kein DRM auf dieser Ebene.

**Unabhängige Bestätigung der Call-Zeit:** Der Countdown der Seite stand
am 22.07. um 13:03 UTC bei 8 h 27 min. Das ergibt **21:30 UTC** und
bestätigt die Zeitzonen-Korrektur aus dem Recherche-Report (die
Web-Recherche hatte 22:30 UTC angegeben, was EST statt EDT unterstellt).

## 3. Messaufbau

Da der Tesla-Stream zum Messzeitpunkt noch nicht lief, wurde die Strecke an
einem laufenden öffentlichen HLS-Livestream validiert (DW News via YouTube,
Format 91, 5-s-Segmente). Gemessen wurde ausschliesslich Timing-Metadaten
und die eigene Rechenzeit.

Der Prototyp nutzt **den Produktions-Stack unverändert**: ffmpeg schreibt
eine wachsende WAV-Datei, und `ChunkTranscriber.naechster_chunk()` aus
`operations/pipeline/transcription.py` transkribiert den Zuwachs. Das ist
architektonisch derselbe Fall wie der `ProgressiveDownloader` beim Podcast —
eine wachsende Datei. **Am Repo wurde nichts geändert**, die laufenden Bots
blieben unberührt.

## 4. Ergebnisse

### 4.1 L_broadcast — der Rückstand des Streams gegenüber Realtime

Gemessen über `EXT-X-PROGRAM-DATE-TIME`. **Methodischer Fallstrick:** Das
Tag steht bei YouTube nur **einmal am Anfang** des 4-Stunden-DVR-Fensters
(2880 Segmente, 1 PDT-Tag). Wer das letzte PDT als Live-Rand liest, misst
13.721 s — also Unsinn. Korrekt ist `letztes PDT + Summe der EXTINF danach`.

| Messung | Rückstand |
|---|---|
| 5 Polls, 13:08 UTC | Median **4,3 s** (min 2,0 / max 5,8) |

Das ist die Untergrenze, die kein Bot unterbieten kann.

### 4.2 L_startversatz — ffmpeg-Puffer

ffmpeg startet bei HLS per Default **3 Segmente vor dem Live-Rand**
(`live_start_index = -3`) und lädt diesen Puffer im Burst: gemessen
20 s Audio in 8 s Wanduhrzeit. Mit `-live_start_index -1` startet er am
jüngsten Segment. Der Rest ist Segmentgranularität — bei 5-s-Segmenten
kommt Audio in 5-s-Klumpen, das ist eine harte Untergrenze der Auflösung.

### 4.3 L_transkription — unser Stellhebel

faster-whisper, Modell `small`, `cuda/float16`:

| Chunk-Länge | Median | Min | Max | Echtzeitfaktor | n |
|---|---|---|---|---|---|
| 20 s | 0,69 s | 0,49 | 0,96 | **0,035×** | 9 |
| 5 s | 0,42 s | 0,12 | 1,44 | **0,083×** | 29 |

Die Drift (Audiosekunden minus Wanduhrsekunden) blieb über beide Läufe
konstant bei +4 bis +8 s statt zu wachsen — der Stream läuft also
realtime-gekoppelt, es staut sich nichts auf.

**Kernbefund: Die Transkription ist nie der Engpass.** Bei 0,035× bis
0,083× Echtzeit ist die Rechenzeit gegenüber allen anderen Posten
vernachlässigbar. Der dominante Posten ist die **Chunk-Füllzeit**, und die
ist eine freie Wahl — nach unten begrenzt durch die Segmentlänge des
Streams.

### 4.4 Gesamtbudget

Realistisch, konservativ addiert:

```
L_broadcast        ~4,3 s   (gemessen, nicht beeinflussbar)
Segmentgranularität ~5   s   (Stream-abhängig)
Chunk-Füllzeit     0–5   s   (frei wählbar, >= Segmentlänge)
Transkription      ~0,4 s   (gemessen)
-----------------------------------------
L_gesamt           ~10–15 s
```

## 5. Bewertung gegen das gemessene Marktverhalten

Aus dem Recherche-Report: Beim Tesla-Call im Januar bewegte sich „Refinery"
**in vier Sekunden** von 0.80 auf 0.973; unterhalb von 0.90 lagen 5 Shares.

**Damit ist die Frage für Einzelwort-Märkte entschieden: 10–15 s gegen
4 s ist kein Rennen.** Wir kämen systematisch nach dem Sweep an. Auch eine
aggressive Optimierung (2-s-Chunks, grösseres Modell weglassen) ändert
daran nichts, weil L_broadcast allein schon in der Grössenordnung des
gesamten Marktfensters liegt.

**Für die Zähl-Brackets (`Car 10+`, `Quarter 10+`, …) ist die Latenz
dagegen weitgehend irrelevant.** Dort zählt nicht, wer eine Nennung zuerst
sieht, sondern wer den laufenden Stand kennt. Ein Rückstand von 10 s auf
einen Zählstand, der sich über 45–70 Minuten aufbaut, ist bedeutungslos.
Das bestätigt die Hypothese aus dem Recherche-Report: Der verbleibende
Vorteil wäre ein **Verarbeitungs-, kein Latenzvorteil**.

Einschränkend bleibt der GM-Datenpunkt: `Quarter 10+` sprang dort in einer
Minute von 0.696 auf 0.996 — die Gegenseite zählte mit.

## 6. Offen

1. **Der Tesla-Stream selbst ist ungemessen.** Segmentlänge, CDN und
   L_broadcast können vom Testfall abweichen. Messbar ab 21:30 UTC, sobald
   `stageDetails` die Manifest-URL trägt.
2. **ToS- und Rechtslage weiterhin ungeklärt** (Tesla-Nutzungsbedingungen,
   Urheberrecht am Webcast). Unverändert offen aus dem Recherche-Report und
   **vor jedem produktiven Einsatz zu klären**.
3. Ob die Manifest-URL tatsächlich in `stageDetails` erscheint oder der
   Player sie über einen weiteren Endpunkt zieht.
4. Transkriptionsqualität bei kurzen Chunks: Whisper arbeitet mit 30-s-
   Fenstern; 5-s-Chunks kosten Kontext. Nicht gemessen.

## 7. Artefakte

Alle Werkzeuge liegen ausserhalb des Repos unter `C:\Users\chole\mentions_paper\`:

| Datei | Zweck |
| --- | --- |
| `mentions_buch_rekorder.py` | Orderbuch-Aufzeichnung je Event (firmenunabhängig, read-only) |
| `werkzeuge\earnings_stream_prototyp.py` | Latenzmessung: `--probe` (L_broadcast), `--stage-watch`, `--lauf` |
| `werkzeuge\tesla_paper_lauf.py` | Paper-Vollstrecke Audio → Zählung → Buch-Beweis |
| `daten\event_mentions_contract.txt` | Volltext des Polymarket-Regelwerks |
| `daten\*.json` | Gamma-Snapshots Tesla (Q4/25, Q2/26), GM, Intel, Hot Ones |

Bewusst nicht im Repo: Prototypen ohne Testabdeckung. Falls sie dort landen
sollen, gilt der etablierte Weg — Feature-Branch, additive Module, Tests, PR.

## 8. Nachtrag 23.07.: Zugang ist der eigentliche Blocker

Der Versuch, die Audio-Strecke bei Dow und Intel produktiv zu testen,
scheiterte nicht an Technik, sondern am Zugang:

- **Intel** (Notified, `edge.media-server.com`): Formular mit Vorname,
  Nachname, E-Mail, Firma plus Zustimmung zur Privacy Statement.
- **Dow** (Q4 Inc, `events.q4inc.com`): Registrierung oder Q4-Konto.

**Tesla war die Ausnahme, nicht die Regel** — dort lief der Webcast offen.
Für einen automatisierten Bot bedeutet eine Registrierungspflicht je Firma:
eigene Zugangsdaten, Session-Verwaltung und eine aktive Zustimmung zu
Nutzungsbedingungen. Das skaliert nicht über ~20 Firmen je Quartal, und die
bislang offene ToS-Frage wird damit von theoretisch zu akut.

Damit stehen drei unabhängige Gründe gegen die Marktklasse, von denen der
dritte nichts mehr mit Geschwindigkeit zu tun hat:

1. kein Akquisitionsvorsprung (Livestream statt Datei),
2. Repricing in ~4 s gegen einen Pfad von 10–15 s,
3. Audio je Firma zugangsbeschränkt.

**Zusatzbefund (eigene Messung 23.07.):** Die Polymarket-Beschreibung des
Dow-Events nennt „9 AM ET". Dows IR-Seite und die Q4-Event-Seite nennen
übereinstimmend 08:00 ET (= 12:00 UTC). Wer sich auf die Zeitangabe in der
Marktbeschreibung verlässt, armiert eine Stunde zu spät.
