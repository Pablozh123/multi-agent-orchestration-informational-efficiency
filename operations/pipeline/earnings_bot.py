"""Earnings-Call Live-Bot: Live-Audio -> Zaehlung -> Entscheidungen.

Gegenstueck zu bot.py fuer Events OHNE Drop-Ereignis: Der Call startet
zur bekannten Uhrzeit als Live-Webcast. Audio kommt wahlweise von

  --geraet "<dshow-Name>"   Loopback-Geraet (Stereomix/CABLE Output).
        Der Nutzer spielt den Webcast selbst im Browser ab, der Bot
        hoert nur mit. Kein automatisierter Login, keine Zugangsdaten.
  --stream <URL>            direkte Medien-URL (HLS/MP3), falls offen.
  --wav <Datei>             vorhandene Aufnahme (Trockenlauf).

Wiederverwendet unveraendert aus der Produktion: market_rules.build_rules,
transcription.ChunkTranscriber, counter_engine.StreamingCounter,
decision/execution (inkl. Kill-Switch data/live/STOP und Startwache).

Earnings-spezifische Gates gegenueber bot.py:
- Anyone-Klausel: Ein Markt ist nur aktiv, wenn seine Beschreibung
  "mentioned by anyone" traegt. Die Elon-Serie ("What will Elon Musk say
  during Tesla ... earnings call?") filtert auf Markt-Ebene nach
  Sprecher — ohne Diarisierung waere unser Zaehler dort systematisch
  falsch (Recherche 22.07., §2). Fehlt die Klausel -> SKIP.
- SPRECHERGEBUNDENE Events (Profil setzt sprecher_klausel_muster, z.B.
  trump_michigan_july27 "if Trump says the listed term"): Das Anyone-
  Gate wird durch das Profil-Klauselmuster ERSETZT, und zwei Schutz-
  schichten kommen dazu: (1) ECAPA-Sprecher-Verifikation — YES zaehlt
  nur Trump-zugerechnete Treffer (ziel_count, Referenz Pflicht bei
  --live); (2) Operator-Marker config.SPRECHER_MARKER — der Kaufpfad
  bleibt gesperrt, bis die Datei existiert (Redebeginn), denn
  Vorprogramm und Vorredner laufen auf demselben Stream.
- Schwelle NUR aus dem Fragetext ("N+ times", parse_schwelle). Das
  Gamma-Feld groupItemThreshold ist ein SORTIER-Index der Event-Gruppe,
  keine Zaehlschwelle (AXP-Event 715475: Einzelwort-Maerkte tragen
  3,4,5..., der "Income 10+"-Markt traegt 0) — nie als Schwelle lesen.
- Geschlossene Maerkte -> SKIP (Vorbild baue_elon_rules).

Standard ist Dry-Run. Scharf NUR mit --live (POLY_PRIVATE_KEY in .env,
Deposit-Wallet eingerichtet, siehe setup_deposit_wallet.py).

Aufruf (Profil via Umgebung, z.B. earnings_pg_july29):
  python -m operations.pipeline.earnings_bot --liste-geraete
  python -m operations.pipeline.earnings_bot --status
  python -m operations.pipeline.earnings_bot --geraet "CABLE Output (...)" \
      --ab 2026-07-29T12:15:00Z
  python -m operations.pipeline.earnings_bot --geraet "..." --live
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from operations.pipeline import config, startwache
from operations.pipeline.counter_engine import StreamingCounter
from operations.pipeline.decision import (
    entscheide_no,
    entscheide_yes,
    nach_edge_sortiert,
    no_sperre,
)
from operations.pipeline.market_rules import MarketRule, build_rules
from operations.pipeline.orderbook import (
    best_ask,
    fetch_book,
    log_snapshots,
    now_utc_iso,
)

# Byte-identische Template-Klausel aller Earnings-Mentions-Maerkte
# (AXP 715475, P&G 715467, Tesla 701009: je EINE Description pro Event).
_ANYONE_KLAUSEL = re.compile(r"mentioned\s+by\s+anyone", re.IGNORECASE)


def _schreibe_event(art: str, daten: dict) -> None:
    pfad = config.LIVE_DIR / "bot_events.jsonl"
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "a", encoding="utf-8") as f:
        f.write(json.dumps(
            {"wall_ts_utc": now_utc_iso(), "art": art, **daten},
            ensure_ascii=False,
        ) + "\n")


def _stop() -> bool:
    return config.STOP_FILE.exists()


def refresh_snapshot() -> None:
    """Aktualisiert den Gamma-Snapshot des konfigurierten Events.

    Bewusst OHNE Auto-Discovery-Wechsel (anders als bot.py): Earnings-
    Slugs sind Rolling Slugs — der naechste Quartals-Call wuerde sonst
    mit den alten Parametern uebernommen (Recherche §4, Zitier-Lehre:
    immer Event-ID, nie Slug).
    """
    import httpx

    r = httpx.get(config.GAMMA_EVENT_URL, headers=config.HTTP_HEADERS,
                  timeout=60)
    r.raise_for_status()
    e = r.json()
    felder = ["id", "slug", "question", "conditionId", "description",
              "outcomes", "outcomePrices", "clobTokenIds", "bestAsk",
              "bestBid", "closed", "umaResolutionStatus"]
    snap = {
        "event_id": str(e.get("id") or config.EVENT_ID),
        "slug": e.get("slug"),
        "titel": e.get("title"),
        "abgerufen_am_utc": now_utc_iso(),
        "markets": [{k: m.get(k) for k in felder} for m in e.get("markets", [])],
    }
    config.GAMMA_SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    with open(config.GAMMA_SNAPSHOT, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=1)


def baue_earnings_rules() -> list[MarketRule]:
    """Regeln aus dem Snapshot plus Earnings-Gates (siehe Moduldocstring)."""
    with open(config.GAMMA_SNAPSHOT, encoding="utf-8") as f:
        snap = json.load(f)
    maerkte = snap["markets"]
    rules = build_rules(maerkte)
    nach_id = {str(m.get("id")): m for m in maerkte}
    # Sprechergebundenes Profil: Das Anyone-Gate wird durch das exakte
    # Klausel-Muster des Profils ersetzt (die Beschreibung MUSS die
    # sprechergebundene Resolution tragen — schuetzt auch gegen einen
    # versehentlichen Event-/Profil-Mix nach einem Slug-Roll).
    sprecher_klausel = (
        re.compile(config.SPRECHER_KLAUSEL_MUSTER, re.IGNORECASE)
        if config.SPRECHER_KLAUSEL_MUSTER else None)
    for r in rules:
        if r.status != "active":
            continue
        m = nach_id.get(r.market_id, {})
        if m.get("closed"):
            r.status, r.skip_grund = "skip", "markt_geschlossen"
            continue
        if sprecher_klausel is not None:
            if not sprecher_klausel.search(m.get("description") or ""):
                r.status, r.skip_grund = "skip", "sprecher_klausel_fehlt"
            continue
        if not _ANYONE_KLAUSEL.search(m.get("description") or ""):
            r.status = "skip"
            r.skip_grund = "keine_anyone_klausel_sprecherfilter_moeglich"
    return rules


def _snapshot_preis(markt: dict) -> float | None:
    try:
        return float(json.loads(markt.get("outcomePrices") or '["0"]')[0])
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


# ----------------------------------------------------------------- Audio
def liste_geraete() -> None:
    """Zeigt die von ffmpeg sichtbaren Audio-Eingaenge (dshow)."""
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-list_devices", "true", "-f", "dshow",
         "-i", "dummy"],
        capture_output=True, timeout=60)
    text = (p.stderr or b"").decode("utf-8", "replace")
    print("Sichtbare Audio-Eingaenge:\n")
    for zeile in text.splitlines():
        if "(audio)" in zeile:
            name = zeile.split('"')[1] if '"' in zeile else zeile
            print(f'  --geraet "{name}"')
    print("\nFehlt ein Loopback ('Stereomix', 'CABLE Output')? In mmsys.cpl"
          " -> Aufnahme -> deaktivierte Geraete anzeigen -> aktivieren.")
    print("ACHTUNG: Stereomix nimmt nur auf, was DIESELBE Soundkarte "
          "abspielt (nicht Bluetooth).")


def ffmpeg_befehl(quelle: str, art: str, wav: Path) -> list[str]:
    """ffmpeg-Kommando: dshow-Geraet oder Stream/Datei -> wachsende WAV."""
    basis = ["ffmpeg", "-hide_banner", "-loglevel", "warning"]
    if art == "geraet":
        eingabe = ["-f", "dshow", "-i", f"audio={quelle}"]
    elif quelle.lower().startswith(("http://", "https://")):
        # -live_start_index -1: am juengsten HLS-Segment starten statt
        # 3 Segmente hinter dem Live-Rand (Messprotokoll §4.2).
        eingabe = ["-user_agent", config.HTTP_HEADERS["User-Agent"],
                   "-live_start_index", "-1", "-i", quelle]
    else:
        # Lokale Datei (--wav Trockenlauf): Datei-Demuxer kennen die
        # Netz-Optionen nicht — "Option user_agent not found" beendete
        # ffmpeg sofort (Smoke-Test 27.07.).
        eingabe = ["-i", quelle]
    return basis + eingabe + [
        "-vn", "-ac", "1", "-ar", "16000", "-acodec", "pcm_s16le",
        "-f", "wav", "-y", str(wav)]


def starte_ffmpeg(quelle: str, art: str, wav: Path) -> subprocess.Popen:
    return subprocess.Popen(
        ffmpeg_befehl(quelle, art, wav),
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def _stream_reconnect(wav_index: int):
    """Frische Live-URL aufloesen und ffmpeg auf NEUE WAV starten.

    Michigan-Lehre 27.07.: YouTube rotiert das HLS-Manifest (Redebeginn,
    Sender-Umschaltung) — ffmpeg stirbt dann oft nicht, sondern haengt
    still am toten Manifest; die WAV friert ein und der Bot ist blind,
    waehrend die Schleife weiterlaeuft. Der Reconnect loest die
    /live-Kanalseiten neu auf (Titel-Gate wie beim Start) und beginnt
    eine neue Datei; der Aufrufer schaltet den Transcriber um
    (neue_quelle) — die Markt-Zaehler bleiben erhalten.

    (proc, wav) oder None (kein passender Stream live).
    """
    import re as _re

    from operations.pipeline.trump_michigan_start import stream_url

    muster = _re.compile(config.STREAM_TITEL_MUSTER, _re.IGNORECASE)
    for kanal in config.RECONNECT_KANAELE:
        try:
            treffer = stream_url(kanal, muster)
        except Exception as ex:  # noqa: BLE001 - naechsten Kanal probieren
            _schreibe_event("fehler", {"wo": f"reconnect:{kanal}",
                                       "fehler": str(ex)})
            treffer = None
        if not treffer:
            continue
        url, titel = treffer
        wav_neu = config.LIVE_DIR / f"call_audio_{wav_index}.wav"
        if wav_neu.exists():
            wav_neu.unlink()
        proc = starte_ffmpeg(url, "stream", wav_neu)
        _schreibe_event("stream_reconnect", {
            "kanal": kanal, "titel": titel[:90], "wav": wav_neu.name})
        print(f"RECONNECT auf {titel[:60]!r} -> {wav_neu.name}")
        return proc, wav_neu
    return None


def warte_bis(iso_utc: str) -> None:
    """Blockiert bis zum Zielzeitpunkt (Armierung vor Call-Start)."""
    ziel = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
    while True:
        rest = (ziel - datetime.now(timezone.utc)).total_seconds()
        if rest <= 0 or _stop():
            return
        if rest > 120:
            print(f"warte bis {ziel.strftime('%H:%M')} UTC ({rest / 60:.0f} min)")
        time.sleep(min(30.0, rest))


# ------------------------------------------------------------------ Lauf
def status_bericht() -> dict:
    """Einmaliger Blick: Regeln, offene Ausgaenge, YES-Buecher (keine Orders)."""
    rules = baue_earnings_rules()
    aktive = [r for r in rules if r.status == "active"]
    skips = [(r.slug, r.skip_grund) for r in rules if r.status != "active"]
    with open(config.GAMMA_SNAPSHOT, encoding="utf-8") as f:
        snap = json.load(f)
    preise = {str(m.get("id")): _snapshot_preis(m) for m in snap["markets"]}

    buecher = []
    for r in aktive:
        try:
            ask = best_ask(fetch_book(r.yes_token_id))
        except Exception:  # noqa: BLE001 - Status soll nie am Buch scheitern
            ask = None
        buecher.append({
            "frage": r.question, "schwelle": r.schwelle,
            "varianten": r.varianten, "snapshot_preis": preise.get(r.market_id),
            "yes_best_ask": ask,
        })

    bericht = {
        "wall_ts_utc": now_utc_iso(),
        "event_id": config.EVENT_ID,
        "call_start_utc": config.CALL_START_UTC,
        "ask_obergrenze": config.ASK_OBERGRENZE,
        "no_ask_obergrenze": config.NO_ASK_OBERGRENZE,
        "trigger_verify": config.TRIGGER_VERIFY_AKTIV,
        "sprecher_gebunden": bool(config.SPRECHER_KLAUSEL_MUSTER),
        "sprecher_referenz_vorhanden": (
            all(p.exists() for p in config.ZIELSPRECHER_REFERENZEN)
            if config.ZIELSPRECHER_REFERENZEN else None),
        "sprecher_marker": (str(config.SPRECHER_MARKER)
                            if config.SPRECHER_KLAUSEL_MUSTER else None),
        "aktive_maerkte": len(aktive),
        "zaehl_brackets": sorted(
            r.question for r in aktive if r.schwelle > 1),
        "offene_ausgaenge_010_090": sorted(
            (r.question for r in aktive
             if preise.get(r.market_id) is not None
             and 0.10 < preise[r.market_id] < 0.90),
        ),
        "skip_maerkte": skips,
        "buecher_yes": buecher,
    }
    _schreibe_event("status", bericht)
    return bericht


def _segment_fenster(segmente) -> tuple[float, float] | None:
    """(fruehester Start, spaetestes Ende) der Chunk-Segmente, sonst None."""
    starts = [s.start_s for s in segmente if s.end_s > s.start_s]
    enden = [s.end_s for s in segmente if s.end_s > s.start_s]
    if not enden:
        return None
    return (min(starts), max(enden))


def _auto_marker_treffer(segmente) -> int:
    """Zielsprecher-zugerechnete Segmente tragfaehiger Laenge im Chunk.

    Fuer den Auto-Marker (Fernstart): Kurze Schnipsel unter 1 s liefern
    keine verlaessliche ECAPA-Zurechnung (speaker.MIN_SEGMENT_S) und
    zaehlen nicht — sonst koennte ein einzelner Fehl-Frame im
    Vorprogramm den Kaufpfad oeffnen. ist_ziel None (Verifikation
    inaktiv) zaehlt bewusst NICHT: ohne Referenz nie ein Auto-Marker.
    """
    return sum(1 for s in segmente
               if s.ist_ziel is True and (s.end_s - s.start_s) >= 1.0)


def _yes_phase(
    aktive: list[MarketRule],
    counters: dict[str, StreamingCounter],
    segmente,
    chunk_index: int,
    ts: str,
    executor,
    getradet_yes: set[str],
    yes_pause: dict[str, int],
    verifikation=None,
    audio_holen=None,
    verify_ok: set[str] | None = None,
    verify_abgelehnt: dict[str, int] | None = None,
    kauf_gesperrt: bool = False,
    nutze_gesamtzaehler: bool = False,
) -> dict[str, int]:
    """Zaehler aktualisieren, dann edge-sortiert kaufen (wie bot.py).

    Mit aktiver Trigger-Verifikation wird jeder Schwellen-Trigger EINMAL
    durch das grosse Modell bestaetigt, bevor ueberhaupt ein Buch geholt
    wird (fail-closed). Eine Ablehnung sperrt den Markt, bis ein NEUER
    Treffer den Zaehler erhoeht; eine Bestaetigung gilt fuer den Rest
    des Laufs (auch Endcheck und Nachlauf kaufen nur bestaetigt).

    kauf_gesperrt=True (sprechergebundenes Event vor dem Operator-
    Marker): Zaehler laufen normal weiter, aber weder Verifikation noch
    Buch-Roundtrips noch Kaeufe — das Vorprogramm soll zaehlbar im Log
    stehen, ohne je einen Trade ausloesen zu koennen.

    nutze_gesamtzaehler=True (Fenster-Modus): Der Trigger laeuft auf
    count_total statt ziel_count_total — die Sprecherbindung leistet
    dann das OPERATOR-Fenster (Chunks ausserhalb des Markers werden gar
    nicht erst ingestiert), nicht die ECAPA-Zurechnung.
    """
    verify_ok = verify_ok if verify_ok is not None else set()
    verify_abgelehnt = verify_abgelehnt if verify_abgelehnt is not None else {}
    staende: dict[str, int] = {}
    bereit = []
    for r in aktive:
        log = counters[r.market_id].ingest_chunk(chunk_index, segmente, ts)
        staende[r.slug] = log.count_total
        if kauf_gesperrt or r.market_id in getradet_yes:
            continue
        ziel = 1 if r.schwelle <= 1 else r.schwelle + config.YES_SCHWELLE_PUFFER
        relevanter_count = (log.count_total if nutze_gesamtzaehler
                            else log.ziel_count_total)
        if relevanter_count < ziel:
            continue
        # Trigger-Verifikation VOR der Buch-Pause: so wird jeder Markt
        # genau einmal geprueft, und Endcheck/Nachlauf koennen sich auf
        # verify_ok verlassen (auch wenn das Buch beim Trigger tot war).
        if verifikation is not None and r.market_id not in verify_ok:
            if relevanter_count <= verify_abgelehnt.get(r.market_id, -1):
                continue  # kein neuer Treffer seit der Ablehnung
            try:
                urteil = verifikation.pruefe(
                    r, audio_holen(), _segment_fenster(segmente))
            except Exception as ex:  # noqa: BLE001 - fail-closed: kein Kauf,
                # naechster Chunk versucht es erneut.
                _schreibe_event("fehler", {"wo": f"trigger_verify:{r.slug}",
                                           "fehler": str(ex)})
                continue
            _schreibe_event("trigger_verifikation", {
                "markt": r.slug, "count": relevanter_count, **urteil})
            if not urteil["bestaetigt"]:
                verify_abgelehnt[r.market_id] = relevanter_count
                print(f"  VERIFY LEHNT AB: {r.varianten[0]!r} — kein Kauf "
                      f"({urteil.get('text', '')[:60]!r})")
                continue
            verify_ok.add(r.market_id)
            print(f"  VERIFY OK: {r.varianten[0]!r} "
                  f"({urteil['treffer']} Treffer, {urteil['dauer_s']}s)")
        # Vorscan-Pause: Buch zuletzt ueber der Obergrenze ODER ohne
        # Asks -> Roundtrip im heissen Pfad sparen (Re-Check am Ende).
        if chunk_index < yes_pause.get(r.market_id, 0):
            continue
        try:
            book = fetch_book(r.yes_token_id)
            bereit.append({"rule": r, "book": book,
                           "best_ask": best_ask(book),
                           "count": relevanter_count,
                           "count_total": log.count_total})
        except Exception as ex:  # noqa: BLE001
            _schreibe_event("fehler", {"wo": f"yes_fetch:{r.slug}",
                                       "fehler": str(ex)})
    for k in nach_edge_sortiert(bereit):
        r, book, ask = k["rule"], k["book"], k["best_ask"]
        try:
            d = entscheide_yes(r, k["count"], ask)
            res = executor.place(d, book)
            if d.action == "YES":
                getradet_yes.add(r.market_id)
            elif ask is None or ask > config.ASK_OBERGRENZE:
                # Totes Buch (keine Asks) genauso pausieren wie ein zu
                # teures: beim AXP-Lauf erzeugten leere Buecher 2029
                # sinnlose Entscheidungs-Roundtrips (1-2 s je Chunk im
                # heissen Pfad). Der Re-Check am Call-Ende bleibt.
                yes_pause[r.market_id] = (
                    chunk_index + config.VORSCAN_PAUSE_CHUNKS)
            _schreibe_event("yes_entscheidung", {
                "markt": r.slug, "count": k["count_total"],
                "best_ask": ask, "action": d.action,
                "status": res.status, "grund": d.reason,
            })
        except Exception as ex:  # noqa: BLE001
            _schreibe_event("fehler", {"wo": f"yes:{r.slug}", "fehler": str(ex)})
    return staende


def _finale(
    aktive: list[MarketRule],
    counters: dict[str, StreamingCounter],
    executor,
    getradet_yes: set[str],
    verifikation=None,
    verify_ok: set[str] | None = None,
    nutze_gesamtzaehler: bool = False,
) -> None:
    """Nach Call-Ende: letzter YES-Blick, NO-Runde, Nachlauf (wie bot.py)."""
    verify_ok = verify_ok if verify_ok is not None else set()

    def _zaehler(c: StreamingCounter) -> int:
        return c.count if nutze_gesamtzaehler else c.ziel_count

    def _verify_fehlt(r: MarketRule) -> bool:
        """Fail-closed auch nach dem Call: unbestaetigte Trigger kaufen nie."""
        if verifikation is None or r.market_id in verify_ok:
            return False
        _schreibe_event("yes_uebersprungen", {
            "markt": r.slug, "grund": "trigger_nicht_verifiziert"})
        return True

    gefuellt = {"dry_run_fill", "live_fill", "live_partial"}
    for r in aktive:
        if r.market_id in getradet_yes:
            continue
        c = counters[r.market_id]
        ziel = 1 if r.schwelle <= 1 else r.schwelle + config.YES_SCHWELLE_PUFFER
        if _zaehler(c) < ziel:
            continue
        if _verify_fehlt(r):
            continue
        try:
            book = fetch_book(r.yes_token_id)
            d = entscheide_yes(r, _zaehler(c), best_ask(book))
            res = executor.place(d, book)
            if d.action == "YES":
                getradet_yes.add(r.market_id)
            _schreibe_event("yes_endcheck", {
                "markt": r.slug, "count": c.count, "action": d.action,
                "status": res.status, "grund": d.reason,
            })
        except Exception as ex:  # noqa: BLE001
            _schreibe_event("fehler", {"wo": f"yes_endcheck:{r.slug}",
                                       "fehler": str(ex)})

    # NO-Runde nur bei geoeffneter NO-Seite. Erste Earnings-Armierung
    # laeuft YES-only (Profil no_ask_obergrenze 0.0): Live-Capture hat
    # keine belegte Abdeckungsgarantie — ein spaeter Einstieg oder ein
    # Quellen-Aussetzer macht den erweiterten Zaehler als Abwesenheits-
    # Proxy wertlos (E281-Lehre, verschaerft).
    getradet_no: set[str] = set()
    if config.NO_ASK_OBERGRENZE > 0:
        for r in aktive:
            if r.market_id in getradet_yes:
                continue
            try:
                book = fetch_book(r.no_token_id)
                c = counters[r.market_id]
                d = entscheide_no(r, c.erweitert_count, best_ask(book))
                res = executor.place(d, book)
                if res.status in gefuellt:
                    getradet_no.add(r.market_id)
                _schreibe_event("no_runde", {
                    "markt": r.slug, "count": c.count,
                    "erweitert_count": c.erweitert_count,
                    "action": d.action, "status": res.status,
                })
            except Exception as ex:  # noqa: BLE001
                _schreibe_event("fehler", {"wo": f"no:{r.slug}",
                                           "fehler": str(ex)})
    else:
        _schreibe_event("no_runde_uebersprungen", {
            "grund": "no_ask_obergrenze 0.0 (YES-only, Abdeckung "
                     "der Live-Quelle nicht kalibriert)",
        })

    # Nachlauf: MMs stellen Quotes oft erst Minuten nach dem Ereignis
    # wieder rein (JRE #2523, E280). Offene Kandidaten weiter pollen.
    nachlauf_kaeufe = 0
    ende_ts = time.time() + config.NACHLAUF_MINUTEN * 60
    _schreibe_event("nachlauf_start", {"minuten": config.NACHLAUF_MINUTEN,
                                       "poll_s": config.NACHLAUF_POLL_S})
    while time.time() < ende_ts and not _stop():
        _schreibe_event("nachlauf_tick", {
            "rest_min": round((ende_ts - time.time()) / 60, 1),
            "kaeufe": nachlauf_kaeufe})
        offene = []
        for r in aktive:
            if r.market_id in getradet_yes or r.market_id in getradet_no:
                continue
            c = counters[r.market_id]
            ziel = (1 if r.schwelle <= 1
                    else r.schwelle + config.YES_SCHWELLE_PUFFER)
            seite = None
            if _zaehler(c) >= ziel:
                if verifikation is not None and r.market_id not in verify_ok:
                    continue  # fail-closed auch im Nachlauf
                seite = "YES"
            elif (config.NO_ASK_OBERGRENZE > 0
                    and c.erweitert_count <= config.NO_ANTEIL * r.schwelle
                    and no_sperre(r) is None):
                seite = "NO"
            if seite is None:
                continue
            tok = r.yes_token_id if seite == "YES" else r.no_token_id
            try:
                book = fetch_book(tok)
            except Exception as ex:  # noqa: BLE001
                _schreibe_event("fehler", {"wo": f"nachlauf_fetch:{r.slug}",
                                           "fehler": str(ex)})
                continue
            offene.append({"rule": r, "seite": seite, "book": book,
                           "best_ask": best_ask(book)})
        if not offene:
            break
        budget_leer = True
        for k in nach_edge_sortiert(offene):
            r, seite, book = k["rule"], k["seite"], k["book"]
            c = counters[r.market_id]
            try:
                if seite == "YES":
                    d = entscheide_yes(r, _zaehler(c), k["best_ask"])
                else:
                    d = entscheide_no(r, c.erweitert_count, k["best_ask"])
                if d.action == "NONE":
                    budget_leer = False
                    continue
                res = executor.place(d, book)
                if res.status != "skipped_budget":
                    budget_leer = False
                if res.status in gefuellt:
                    nachlauf_kaeufe += 1
                    (getradet_yes if seite == "YES"
                     else getradet_no).add(r.market_id)
                    _schreibe_event("nachlauf_kauf", {
                        "markt": r.slug, "seite": seite, "count": c.count,
                        "status": res.status, "preis": res.limit_price,
                        "usd": res.size_usd,
                    })
                    print(f"NACHLAUF {seite}: {r.slug[:40]} @ {res.limit_price}")
            except Exception as ex:  # noqa: BLE001
                _schreibe_event("fehler", {"wo": f"nachlauf:{r.slug}",
                                           "fehler": str(ex)})
        if budget_leer:
            _schreibe_event("nachlauf_ende", {"grund": "budget"})
            break
        time.sleep(config.NACHLAUF_POLL_S)

    _schreibe_event("fertig", {
        "endstaende": {r.slug: counters[r.market_id].count for r in aktive},
        "nachlauf_kaeufe": nachlauf_kaeufe,
        "ausgegeben_usd": executor.ausgegeben_usd,
    })
    print("Call verarbeitet, NO-Runde und Nachlauf abgeschlossen "
          f"({nachlauf_kaeufe} Nachkaeufe).")


def lauf(live: bool, quelle: str, art: str, minuten: float,
         ohne_verify: bool = False, fenster_modus: bool = False) -> None:
    """Hauptschleife: Capture -> Chunks -> YES live -> Finale.

    fenster_modus=True (sprechergebundene Events, Operator-gefuehrt):
    Die Sprecherbindung leistet das MARKER-FENSTER statt der ECAPA-
    Zurechnung — Chunks ohne Marker werden nicht ingestiert, Trigger
    laufen auf dem Gesamtzaehler, der Marker ist KEIN Latch (loeschen
    pausiert Zaehlung und Kaeufe wieder). Fuer Zeremonien mit vielen
    Fremdrednern, deren Akustik die Referenz-Zurechnung verschiebt
    (Michigan-Messung 27.07.: Studio-Referenz auf PA-Audio max 0.396).
    """
    if not startwache.wache_nehmen(config.LIVE_DIR):
        _schreibe_event("doppelstart_abgebrochen", {
            "grund": "start.lock belegt — andere Instanz laeuft/startet",
        })
        print("Startwache belegt (andere Instanz laeuft) — beende.")
        return
    from operations.pipeline.execution import DryRunExecutor, LiveExecutor

    executor = LiveExecutor() if live else DryRunExecutor()
    modus = "LIVE" if live else "DRY_RUN"

    rules = baue_earnings_rules()
    aktive = [r for r in rules if r.status == "active"]
    counters = {r.market_id: StreamingCounter(r) for r in aktive}
    getradet_yes: set[str] = set()
    yes_pause: dict[str, int] = {}
    verify_ok: set[str] = set()
    verify_abgelehnt: dict[str, int] = {}

    # Sprechergebundenes Event: ECAPA-Verifier laden (YES zaehlt nur
    # Zielsprecher-Treffer). Fail-closed bei --live: ohne kalibrierte
    # Referenz kein Echtgeld — der Gesamtzaehler wuerde Vorredner und
    # Publikums-Chants dem Zielsprecher zurechnen. Im Dry-Run laeuft
    # der Messbetrieb auch ohne Referenz (ziel_count == count), mit
    # deutlicher Warnung.
    sprecher_gebunden = bool(config.SPRECHER_KLAUSEL_MUSTER)
    verifier = None
    if config.ZIELSPRECHER_REFERENZEN:
        fehlend = [p for p in config.ZIELSPRECHER_REFERENZEN
                   if not p.exists()]
        if not fehlend:
            from operations.pipeline.speaker import SpeakerVerifier

            verifier = SpeakerVerifier(config.ZIELSPRECHER_REFERENZEN,
                                       schwelle=config.SPRECHER_SCHWELLE)
            _schreibe_event("sprecher_verifikation", {
                "schwelle": config.SPRECHER_SCHWELLE,
                "pfade": [str(p) for p in config.ZIELSPRECHER_REFERENZEN],
            })
            print(f"Sprecher-Verifikation aktiv (Schwelle "
                  f"{config.SPRECHER_SCHWELLE}, YES nur aus "
                  "Zielsprecher-Treffern).")
        elif live and sprecher_gebunden and not fenster_modus:
            raise SystemExit(
                "Zielsprecher-Referenz fehlt: "
                + ", ".join(str(p) for p in fehlend)
                + " — sprechergebundenes Event ohne Referenz nicht "
                "scharf. Bauen: python -m operations.pipeline."
                "baue_referenz_quellen (Solo-Clips + Kontrollen), "
                "oder Dry-Run als Messlauf / --fenster-modus.")
        else:
            _schreibe_event("sprecher_referenz_fehlt", {
                "pfade": [str(p) for p in fehlend]})
            print("WARNUNG: Zielsprecher-Referenz fehlt — ziel_count "
                  "zaehlt ALLE Stimmen (nur als Messlauf tauglich).")
    if sprecher_gebunden and fenster_modus:
        print("FENSTER-MODUS: Zaehlung und Kaeufe laufen NUR, solange "
              f"der Marker existiert: {config.SPRECHER_MARKER}\n"
              "  Marker anlegen, wenn der Zielsprecher beginnt; "
              "LOESCHEN, sobald er endet (kein Latch!). Die "
              "Sprecherbindung liegt beim Operator.")
    elif sprecher_gebunden:
        print("SPRECHERGEBUNDEN: Kaufpfad gesperrt, bis der Marker "
              f"existiert: {config.SPRECHER_MARKER}\n"
              "  Marker setzen, sobald der Zielsprecher am Pult ist "
              "(Datei anlegen genuegt).")

    verify_gewollt = config.TRIGGER_VERIFY_AKTIV and not ohne_verify
    _schreibe_event("start", {
        "modus": modus, "event_id": config.EVENT_ID,
        "call_start_utc": config.CALL_START_UTC,
        "aktive_maerkte": len(aktive),
        "skips": [(r.slug, r.skip_grund) for r in rules if r.status != "active"],
        "quelle_art": art, "chunk_s": config.CHUNK_SEKUNDEN,
        "ask_obergrenze": config.ASK_OBERGRENZE,
        "no_ask_obergrenze": config.NO_ASK_OBERGRENZE,
        "trigger_verify": verify_gewollt,
        "sprecher_gebunden": sprecher_gebunden,
        "sprecher_verifikation": verifier is not None,
        "fenster_modus": fenster_modus,
        "reconnect_kanaele": len(config.RECONNECT_KANAELE),
    })
    print(f"[{modus}] Earnings-Bot: {len(aktive)} aktive Maerkte, "
          f"Quelle {art}, Chunk {config.CHUNK_SEKUNDEN}s.")

    # GPU-Warmup mit Wiederholung: laufen parallel andere Bots auf der
    # GPU, faellt ChunkTranscriber still auf cpu/int8 zurueck (~10x
    # langsamer) — mehrere Anlaeufe, bevor CPU akzeptiert wird.
    from operations.pipeline.transcription import ChunkTranscriber

    transcriber = None
    for versuch in range(1, 5):
        transcriber = ChunkTranscriber(config.TRANSCRIBER_MODELL,
                                       verifier=verifier)
        if transcriber.geraet.startswith("cuda"):
            break
        print(f"  Versuch {versuch}: nur {transcriber.geraet} — "
              "GPU vermutlich belegt, neuer Anlauf in 5s")
        del transcriber
        transcriber = None
        time.sleep(5.0)
    if transcriber is None:
        transcriber = ChunkTranscriber(config.TRANSCRIBER_MODELL,
                                       verifier=verifier)

    # Trigger-Verifikation: fail-closed ist Absicht; bewusst ohne laufen
    # geht nur explizit via --ohne-trigger-verify. Ist das Verify-Modell
    # identisch zum Haupt-Transcriber (large-v3-Betrieb), wird dessen
    # Instanz GETEILT — der Verify-Blick bleibt trotzdem eigenstaendig:
    # VAD-frei uebers groessere Fenster (der Agentic-Fall 28.07. fiel
    # genau in ein VAD-Loch des gefilterten Pfads).
    verifikation = None
    if verify_gewollt:
        from operations.pipeline.trigger_verify import TriggerVerifikation

        try:
            if config.TRIGGER_VERIFY_MODELL == config.TRANSCRIBER_MODELL:
                def _vadfrei(ausschnitt, _m=transcriber.model):
                    segs, _ = _m.transcribe(
                        ausschnitt, language="en", beam_size=1,
                        vad_filter=False, word_timestamps=False)
                    return " ".join(s.text for s in segs).strip()

                verifikation = TriggerVerifikation(
                    modell=f"{config.TRANSCRIBER_MODELL}/geteilte-instanz",
                    transkribiere_fn=_vadfrei)
            else:
                verifikation = TriggerVerifikation()
        except Exception as ex:  # noqa: BLE001
            _schreibe_event("fehler", {"wo": "trigger_verify_laden",
                                       "fehler": str(ex)})
            raise SystemExit(
                f"Trigger-Verifikation laedt nicht ({ex}) — Abbruch. "
                "Bewusst ohne: --ohne-trigger-verify."
            ) from ex
        _schreibe_event("trigger_verify_bereit", {
            "modell": verifikation.modell_name,
            "geraet": verifikation.geraet})
        print(f"Trigger-Verifikation bereit ({verifikation.modell_name}, "
              f"{verifikation.geraet}).")
    _schreibe_event("whisper_bereit", {"geraet": transcriber.geraet})
    print(f"Whisper bereit ({transcriber.geraet}).")

    wav = config.LIVE_DIR / "call_audio.wav"
    if wav.exists():
        wav.unlink()
    proc = starte_ffmpeg(quelle, art, wav)

    frist = time.time() + 90
    while (not wav.exists() or wav.stat().st_size < 65536) and time.time() < frist:
        if proc.poll() is not None:
            err = (proc.stderr.read() or b"").decode("utf-8", "replace")
            _schreibe_event("fehler", {"wo": "ffmpeg_start", "fehler": err[:900]})
            print(f"ffmpeg beendet sich sofort:\n{err[:900]}")
            return
        time.sleep(1.0)
    if not wav.exists() or wav.stat().st_size < 65536:
        _schreibe_event("fehler", {"wo": "audio", "fehler": "kein Audio nach 90s"})
        print("Kein Audio — Abbruch. Laeuft die Quelle (Webcast im Browser)?")
        proc.terminate()
        return
    _schreibe_event("audio_laeuft", {"wav": wav.name})
    print("Audio laeuft — Zaehlung aktiv. Call-Ende: Ctrl+C, STOP-Datei "
          f"oder nach {minuten:.0f} min.")

    ende_grund = "zeitlimit"
    chunk_index = 0
    letzter_buchlog = 0.0
    # Latch: einmal gesetzt bleibt der Kaufpfad frei (die Feinarbeit —
    # Gaeste am Mikro, Chants — macht die ECAPA-Zurechnung je Segment).
    # Im Fenster-Modus gilt stattdessen der MOMENTANE Marker-Zustand.
    sprecher_frei = not sprecher_gebunden
    # Auto-Marker (Fernstart ohne Operator): rollendes Chunk-Fenster der
    # Zielsprecher-Segmente; nur mit aktivem Verifier, nie im
    # Fenster-Modus (dort fuehrt der Operator).
    auto_fenster = (
        deque(maxlen=5)
        if (sprecher_gebunden and verifier is not None
            and config.SPRECHER_MARKER_AUTO_SEGMENTE > 0
            and not fenster_modus)
        else None)
    # Stall-Detektor (Michigan-Lehre): nur fuer http-Stream-Quellen mit
    # konfigurierten Reconnect-Kanaelen.
    reconnect_aktiv = (art == "stream"
                       and str(quelle).lower().startswith(("http://", "https://"))
                       and bool(config.RECONNECT_KANAELE))
    wav_index = 1
    letzte_wav_groesse = 0
    letzte_wav_zunahme = time.time()

    def _reconnect_versuchen(grund: str):
        """Alte Quelle beenden, Rest flushen, neue Quelle anbinden."""
        nonlocal proc, wav, wav_index, letzte_wav_groesse, letzte_wav_zunahme
        _schreibe_event("stream_stall", {"grund": grund, "wav": wav.name})
        print(f"STREAM TOT ({grund}) — Reconnect laeuft.")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        # Rest-Audio der alten Datei noch zaehlen (unterhalb Chunk-Groesse).
        try:
            rest = transcriber.naechster_chunk(wav, final=True)
        except Exception:  # noqa: BLE001 - Reconnect geht vor
            rest = None
        if rest:
            _yes_phase(aktive, counters, rest, chunk_index, now_utc_iso(),
                       executor, getradet_yes, yes_pause, verifikation,
                       lambda: transcriber.dekodiertes_audio(wav),
                       verify_ok, verify_abgelehnt,
                       kauf_gesperrt=not sprecher_frei,
                       nutze_gesamtzaehler=fenster_modus)
        neu = _stream_reconnect(wav_index + 1)
        if neu is None:
            _schreibe_event("stream_reconnect_fehlgeschlagen", {})
            print("  kein passender Stream live — neuer Versuch folgt.")
            time.sleep(20.0)
            letzte_wav_zunahme = time.time() - config.STREAM_STALL_S
            return False
        proc, wav = neu
        wav_index += 1
        transcriber.neue_quelle()
        letzte_wav_groesse = 0
        letzte_wav_zunahme = time.time() + 60.0  # Anlauf-Schonfrist
        return True

    ende_ts = time.time() + minuten * 60
    try:
        while time.time() < ende_ts:
            if _stop():
                ende_grund = "stop_datei"
                break
            if proc.poll() is not None:
                if not reconnect_aktiv or not _reconnect_versuchen("prozess_beendet"):
                    if not reconnect_aktiv:
                        ende_grund = "quelle_beendet"
                        break
                    continue
            if fenster_modus:
                sprecher_frei = config.SPRECHER_MARKER.exists()
            elif not sprecher_frei and config.SPRECHER_MARKER.exists():
                sprecher_frei = True
                _schreibe_event("sprecher_marker_gesetzt",
                                {"chunk_index": chunk_index})
                print("Sprecher-Marker gesetzt — Kaufpfad frei.")
            jetzt = time.time()
            if reconnect_aktiv:
                groesse = wav.stat().st_size if wav.exists() else 0
                if groesse > letzte_wav_groesse:
                    letzte_wav_groesse = groesse
                    letzte_wav_zunahme = jetzt
                elif jetzt - letzte_wav_zunahme > config.STREAM_STALL_S:
                    _reconnect_versuchen(
                        f"wav_eingefroren_{int(jetzt - letzte_wav_zunahme)}s")
                    continue
            if jetzt - letzter_buchlog >= config.BUCH_LOG_INTERVALL_S:
                try:
                    zeilen = log_snapshots(aktive, now_utc_iso())
                    _schreibe_event("buchlog", {"n_zeilen": len(zeilen)})
                except Exception as ex:  # noqa: BLE001
                    _schreibe_event("fehler", {"wo": "buchlog", "fehler": str(ex)})
                letzter_buchlog = jetzt
            try:
                segmente = transcriber.naechster_chunk(wav)
            except Exception as ex:  # noqa: BLE001
                _schreibe_event("fehler", {"wo": "transkription", "fehler": str(ex)})
                time.sleep(5)
                continue
            if segmente is None:
                time.sleep(0.3)
                continue
            chunk_index += 1
            if fenster_modus and not sprecher_frei:
                # Fenster zu: nichts zaehlen, nichts kaufen — nur die
                # Sichtlinie fuer den Operator, damit er den Redebeginn
                # erkennt und den Marker setzt.
                _schreibe_event("chunk_fenster_zu", {"index": chunk_index})
                text = " ".join(s.text for s in segmente).strip()
                if text:
                    print(f"Chunk {chunk_index} [Fenster ZU]: {text[:105]}")
                continue
            if not sprecher_frei and auto_fenster is not None:
                auto_fenster.append(_auto_marker_treffer(segmente))
                if sum(auto_fenster) >= config.SPRECHER_MARKER_AUTO_SEGMENTE:
                    config.SPRECHER_MARKER.parent.mkdir(parents=True,
                                                        exist_ok=True)
                    config.SPRECHER_MARKER.touch()
                    sprecher_frei = True
                    _schreibe_event("sprecher_marker_gesetzt", {
                        "chunk_index": chunk_index, "auto": True,
                        "segmente_im_fenster": sum(auto_fenster)})
                    print("Auto-Marker: Zielsprecher erkannt — "
                          "Kaufpfad frei.")
            staende = _yes_phase(aktive, counters, segmente, chunk_index,
                                 now_utc_iso(), executor, getradet_yes,
                                 yes_pause, verifikation,
                                 lambda: transcriber.dekodiertes_audio(wav),
                                 verify_ok, verify_abgelehnt,
                                 kauf_gesperrt=not sprecher_frei,
                                 nutze_gesamtzaehler=fenster_modus)
            _schreibe_event("chunk", {"index": chunk_index, "staende": staende})
            heiss = {k: v for k, v in staende.items() if v}
            print(f"Chunk {chunk_index}: " + (", ".join(
                f"{k.split('say-')[-1][:18]}={v}"
                for k, v in list(heiss.items())[:8]) or "-"))
            # Sichtpruefung fuer den Operator: leere Zeilen bei laufendem
            # Call bedeuten kaputtes Audio-Routing (Loopback-Falle).
            text = " ".join(s.text for s in segmente).strip()
            if text:
                print(f"    {text[:110]}")
    except KeyboardInterrupt:
        ende_grund = "manuell_ctrl_c"
        print("Call-Ende manuell gemeldet — Finale laeuft.")

    _schreibe_event("call_ende", {"grund": ende_grund, "chunks": chunk_index})
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()

    # Marker koennte erst kurz vor Ctrl+C gesetzt worden sein.
    if fenster_modus:
        sprecher_frei = config.SPRECHER_MARKER.exists()
    elif not sprecher_frei and config.SPRECHER_MARKER.exists():
        sprecher_frei = True
        _schreibe_event("sprecher_marker_gesetzt",
                        {"chunk_index": chunk_index, "beim_finale": True})

    # Rest-Audio unterhalb der Chunk-Groesse flushen (final=True), damit
    # die letzten Sekunden des Calls noch in Zaehler und YES-Phase gehen.
    # Im Fenster-Modus nur bei offenem Marker (sonst zaehlte der Rest
    # Fremdredner nach Trumps Ende in die Zaehler).
    while not (fenster_modus and not sprecher_frei):
        try:
            segmente = transcriber.naechster_chunk(wav, final=True)
        except Exception as ex:  # noqa: BLE001
            _schreibe_event("fehler", {"wo": "final_chunk", "fehler": str(ex)})
            break
        if not segmente:
            break
        chunk_index += 1
        _yes_phase(aktive, counters, segmente, chunk_index, now_utc_iso(),
                   executor, getradet_yes, yes_pause, verifikation,
                   lambda: transcriber.dekodiertes_audio(wav),
                   verify_ok, verify_abgelehnt,
                   kauf_gesperrt=not sprecher_frei,
                   nutze_gesamtzaehler=fenster_modus)

    if not fenster_modus and not sprecher_frei:
        # Marker wurde nie gesetzt (Event abgesagt/verschoben oder
        # Operator-Abbruch): Endcheck und Nachlauf duerfen dann genauso
        # wenig kaufen wie die Chunk-Phase — nur Endstaende festhalten.
        _schreibe_event("fertig", {
            "endstaende": {r.slug: counters[r.market_id].count
                           for r in aktive},
            "nachlauf_kaeufe": 0,
            "ausgegeben_usd": executor.ausgegeben_usd,
            "hinweis": "kaeufe_gesperrt_sprecher_marker_nie_gesetzt",
        })
        print("Sprecher-Marker wurde nie gesetzt — Finale ohne Kaeufe "
              "beendet.")
        return

    # Im Fenster-Modus tragen die Zaehler ausschliesslich Material aus
    # offenen Marker-Fenstern — Endcheck/Nachlauf laufen deshalb auch
    # bei momentan geschlossenem Marker (die Rede ist vorbei, die
    # gesammelten Staende sind sprecherbereinigt).
    _finale(aktive, counters, executor, getradet_yes, verifikation,
            verify_ok, nutze_gesamtzaehler=fenster_modus)


def main() -> None:
    import sys

    for strom in (sys.stdout, sys.stderr):
        try:
            strom.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001 - ersetzte Streams in Tests
            pass

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--liste-geraete", action="store_true",
                        help="sichtbare dshow-Audioeingaenge zeigen")
    parser.add_argument("--status", action="store_true",
                        help="einmaliger Statusbericht, keine Schleife")
    parser.add_argument("--live", action="store_true",
                        help="ECHTE Orders (sonst Dry-Run)")
    parser.add_argument("--refresh-rules", action="store_true",
                        help="Gamma-Snapshot vor dem Start aktualisieren")
    parser.add_argument("--geraet", help="dshow-Audioeingang (Loopback)")
    parser.add_argument("--stream", help="direkte Medien-URL")
    parser.add_argument("--wav", help="vorhandene Datei (Trockenlauf)")
    parser.add_argument("--ab", metavar="ISO_UTC",
                        help="bis dahin warten (Armierung vor Call-Start)")
    parser.add_argument("--minuten", type=float, default=None,
                        help="Zeitlimit ab Capture-Start (Default: "
                             "call_max_minuten + 30)")
    parser.add_argument("--ohne-trigger-verify", action="store_true",
                        help="Trigger-Verifikation bewusst abschalten "
                             "(Kaeufe dann ohne large-v3-Bestaetigung)")
    parser.add_argument("--fenster-modus", action="store_true",
                        help="Sprecherbindung ueber das Operator-Fenster "
                             "statt ECAPA: gezaehlt und gekauft wird NUR "
                             "bei existierender Marker-Datei (kein Latch)")
    a = parser.parse_args()

    if a.liste_geraete:
        liste_geraete()
        return
    if config.CALL_START_UTC is None:
        raise SystemExit(
            f"Profil {config.PROFIL!r} ist kein Earnings-Profil "
            "(call_start_utc fehlt) — BOT_PROFIL setzen, z.B. "
            "earnings_pg_july29."
        )
    if a.refresh_rules or not config.GAMMA_SNAPSHOT.exists():
        refresh_snapshot()
    if a.status:
        print(json.dumps(status_bericht(), ensure_ascii=False, indent=1))
        return

    quelle, art = ((a.geraet, "geraet") if a.geraet else
                   (a.stream, "stream") if a.stream else
                   (a.wav, "stream") if a.wav else (None, None))
    if not quelle:
        parser.error("--geraet, --stream oder --wav noetig")
    if a.ab:
        warte_bis(a.ab)
    minuten = a.minuten if a.minuten else config.CALL_MAX_MINUTEN + 30.0
    lauf(live=a.live, quelle=quelle, art=art, minuten=minuten,
         ohne_verify=a.ohne_trigger_verify, fenster_modus=a.fenster_modus)


if __name__ == "__main__":
    main()
