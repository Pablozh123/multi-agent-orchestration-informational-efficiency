"""All-In Live-Bot: RSS-Drop -> Streaming-Transkription -> Entscheidungen.

Ablauf:
1. Marktregeln aus dem Gamma-Snapshot laden (per --refresh-rules neu).
2. RSS-Baseline setzen; Poll alle 60 s.
3. Orderbuch-Logger alle BUCH_LOG_INTERVALL_S fuer alle aktiven Outcomes.
4. Bei Episoden-Drop: progressiver Download, Transkription in
   2-Minuten-Chunks, laufende Zaehler, YES-Entscheidungen live.
5. Nach vollstaendigem Transkript: NO-Entscheidungen.
6. Kill-Switch: data/live/STOP beendet alles.

Standard ist Dry-Run. Scharf NUR mit --live (braucht POLY_PRIVATE_KEY in
.env und einmalig gesetzte Allowances, siehe set_allowances.py).

Aufruf:
  python -m operations.pipeline.bot --status   (einmaliger Statusbericht)
  python -m operations.pipeline.bot            (Dry-Run-Loop)
  python -m operations.pipeline.bot --live     (echte Orders, kleine Limits)
"""

from __future__ import annotations

import argparse
import json
import re
import time

from operations.pipeline import config
from operations.pipeline.counter_engine import StreamingCounter
from operations.pipeline.decision import (
    entscheide_no,
    entscheide_yes,
    nach_edge_sortiert,
)
from operations.pipeline.market_rules import lade_snapshot_rules
from operations.pipeline.orderbook import best_ask, fetch_book, log_snapshots, now_utc_iso
from operations.pipeline.rss_watch import (
    FeedItem,
    Mp3UrlProber,
    RssWatcher,
    YouTubeWatcher,
    naechste_episoden_nummer,
)


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


def finde_offenes_allin_event() -> dict | None:
    """Sucht das neueste offene All-In-Mentions-Event auf Gamma."""
    import httpx

    r = httpx.get(
        "https://gamma-api.polymarket.com/events",
        params={"tag_id": 100343, "closed": "false", "limit": 50,
                "order": "startDate", "ascending": "false"},
        headers=config.HTTP_HEADERS, timeout=60,
    )
    r.raise_for_status()
    for e in r.json():
        if config.DISCOVERY_SLUG_FILTER in (e.get("slug") or ""):
            return e
    return None


def refresh_rules_von_gamma() -> None:
    """Aktualisiert den Gamma-Snapshot; wechselt automatisch auf das
    neueste offene All-In-Event, falls das konfigurierte zu/abgelaufen ist."""
    import httpx

    r = httpx.get(config.GAMMA_EVENT_URL, headers=config.HTTP_HEADERS, timeout=60)
    r.raise_for_status()
    e = r.json()
    maerkte_offen = [m for m in e.get("markets", []) if not m.get("closed")]
    if e.get("closed") or not maerkte_offen:
        neues = finde_offenes_allin_event()
        if neues is not None and str(neues.get("id")) != config.EVENT_ID:
            print(f"Event {config.EVENT_ID} zu — wechsle auf "
                  f"{neues.get('id')} ({neues.get('slug')})")
            r = httpx.get(
                f"https://gamma-api.polymarket.com/events/{neues.get('id')}",
                headers=config.HTTP_HEADERS, timeout=60,
            )
            r.raise_for_status()
            e = r.json()
    felder = ["id", "slug", "question", "conditionId", "description",
              "outcomes", "outcomePrices", "clobTokenIds", "bestAsk",
              "bestBid", "closed", "umaResolutionStatus"]
    snap = {
        "event_id": str(e.get("id") or config.EVENT_ID),
        "slug": e.get("slug"),
        "abgerufen_am_utc": now_utc_iso(),
        "markets": [{k: m.get(k) for k in felder} for m in e.get("markets", [])],
    }
    config.GAMMA_SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    with open(config.GAMMA_SNAPSHOT, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=1)


def status_bericht() -> dict:
    """Einmaliger Blick: Regeln, RSS-Stand, Orderbuecher (keine Orders)."""
    rules = lade_snapshot_rules()
    aktive = [r for r in rules if r.status == "active"]
    skips = [(r.slug, r.skip_grund) for r in rules if r.status != "active"]

    watcher = RssWatcher()
    neuestes = watcher.initialisiere()

    buecher = []
    for r in aktive:
        book = fetch_book(r.yes_token_id)
        buecher.append({
            "slug": r.slug.replace(
                "-be-said-during-the-next-episode-of-the-all-in-podcast", ""
            ),
            "schwelle": r.schwelle,
            "varianten": r.varianten,
            "yes_best_ask": best_ask(book),
        })

    bericht = {
        "wall_ts_utc": now_utc_iso(),
        "aktive_maerkte": len(aktive),
        "skip_maerkte": skips,
        "rss_neuestes_item": {
            "titel": neuestes.title if neuestes else None,
            "pubdate_utc": neuestes.pubdate_utc if neuestes else None,
            "guid": (neuestes.guid[:60] if neuestes else None),
            "audio_url_vorhanden": bool(neuestes and neuestes.audio_url),
        },
        "drop_erkannt": False,
        "buecher_yes": buecher,
    }
    _schreibe_event("status", bericht)
    return bericht


def lauf(live: bool) -> None:
    """Hauptschleife des Bots."""
    from operations.pipeline.execution import DryRunExecutor, LiveExecutor

    executor = LiveExecutor() if live else DryRunExecutor()
    modus = "LIVE" if live else "DRY_RUN"
    verifier = None
    if config.ZIELSPRECHER_REFERENZ is not None:
        if not config.ZIELSPRECHER_REFERENZ.exists():
            raise SystemExit(
                f"Zielsprecher-Referenz fehlt: {config.ZIELSPRECHER_REFERENZ} — "
                "zuerst operations.pipeline.baue_referenz ausfuehren."
            )
        from operations.pipeline.speaker import SpeakerVerifier

        verifier = SpeakerVerifier(config.ZIELSPRECHER_REFERENZ,
                                   schwelle=config.SPRECHER_SCHWELLE)
        print(f"Sprecher-Verifikation aktiv (Schwelle {config.SPRECHER_SCHWELLE}, "
              "YES nur aus Zielsprecher-Treffern).")
    rules = lade_snapshot_rules()
    aktive = [r for r in rules if r.status == "active"]
    counters = {r.market_id: StreamingCounter(r) for r in aktive}
    getradet_yes: set[str] = set()
    # Vorscan: Maerkte, deren YES-Ask zuletzt ueber der Obergrenze lag,
    # werden im heissen Chunk-Pfad bis zum genannten Chunk-Index nicht
    # gefetcht (spart Book-Roundtrips fuer eingepreiste Maerkte wie
    # "China" @0.92, deren Wort oft faellt). Buchlog pflegt die Pausen.
    yes_pause: dict[str, int] = {}

    watcher, baseline = None, None
    if config.RSS_FEED_URL:
        watcher = RssWatcher()
        baseline = watcher.initialisiere()
    yt_watcher = YouTubeWatcher()
    yt_baseline = yt_watcher.initialisiere()
    # Positiv-Identifikation: Baseline der offiziellen Playlist. Ein
    # YouTube-Drop wird NUR akzeptiert, wenn ein Video NEU zur Playlist
    # hinzukommt (Diff) — Playlist = Resolutionsquelle. Verhindert per
    # Konstruktion alte Episoden (in Baseline) und Specials (nie drin).
    playlist_baseline: set[str] | None = None
    if config.YT_PLAYLIST_ID:
        from operations.pipeline.transcription import playlist_ids

        try:
            playlist_baseline = playlist_ids(config.YT_PLAYLIST_ID)
        except Exception as ex:  # noqa: BLE001
            _schreibe_event("fehler", {"wo": "playlist_baseline",
                                       "fehler": str(ex)})
    naechste_nr, prober = None, None
    if config.MP3_PROBE_MUSTER:
        try:
            naechste_nr = naechste_episoden_nummer()
            prober = Mp3UrlProber(naechste_nr)
        except Exception as ex:  # noqa: BLE001
            _schreibe_event("fehler", {"wo": "prober_init", "fehler": str(ex)})
    import os as _os

    # PID-Datei fuer den Watchdog (erkennt haengende Instanzen).
    (config.LIVE_DIR / "bot.pid").write_text(str(_os.getpid()), encoding="utf-8")
    _schreibe_event("start", {
        "modus": modus,
        "aktive_maerkte": len(aktive),
        "baseline_guid": baseline.guid[:60] if baseline else None,
        "baseline_titel": baseline.title if baseline else None,
        "yt_baseline_videos": yt_baseline,
        "prober_naechste_episode": naechste_nr,
    })
    print(f"[{modus}] Bot gestartet. Aktive Maerkte: {len(aktive)}. "
          f"Baseline: {baseline.title if baseline else '?'}")

    letzter_buchlog = 0.0
    drop_item = None
    downloader = None
    # Modell schon jetzt laden (GPU-Warmup), damit beim Drop keine
    # Ladezeit anfaellt.
    from operations.pipeline.transcription import ChunkTranscriber

    transcriber = ChunkTranscriber(verifier=verifier)
    _schreibe_event("whisper_bereit", {"geraet": transcriber.geraet,
                                       "sprecher_verifikation": verifier is not None})
    print(f"Whisper bereit ({transcriber.geraet}).")
    audio_pfad = config.LIVE_DIR / "episode.mp3"
    chunk_index = 0
    no_entschieden = False

    while True:
        if _stop():
            _schreibe_event("stop", {"grund": "STOP-Datei"})
            print("Kill-Switch aktiv, beende.")
            return

        jetzt = time.time()
        if jetzt - letzter_buchlog >= config.BUCH_LOG_INTERVALL_S:
            try:
                zeilen = log_snapshots(aktive, now_utc_iso())
                yes_tot = []
                for z in zeilen:
                    if z.get("outcome") != "Yes" or z.get("best_ask") is None:
                        continue
                    mid = z.get("market_id")
                    if z["best_ask"] > config.ASK_OBERGRENZE:
                        yes_pause[mid] = chunk_index + config.VORSCAN_PAUSE_CHUNKS
                        yes_tot.append(z.get("slug"))
                    else:
                        yes_pause.pop(mid, None)
                _schreibe_event("buchlog", {
                    "n_zeilen": len(zeilen), "yes_tot": yes_tot,
                    "yes_handelbar": max(0, len(aktive) - len(yes_tot)),
                })
            except Exception as ex:  # noqa: BLE001
                _schreibe_event("fehler", {"wo": "buchlog", "fehler": str(ex)})
            letzter_buchlog = jetzt

        if drop_item is None:
            # Quelle 0 (schnellste): direkter CDN-Prober auf die
            # vorhersagbare MP3-URL der naechsten Hauptepisode.
            if prober is not None:
                probe_url = prober.poll()
                if probe_url:
                    drop_item = FeedItem(
                        guid=probe_url, title=f"ALLIN-E{naechste_nr} (URL-Prober)",
                        pubdate_utc=now_utc_iso(), audio_url=probe_url,
                    )
                    _schreibe_event("drop_erkannt", {
                        "quelle": "mp3_url_prober", "titel": drop_item.title,
                        "audio_url": probe_url,
                    })
                    print(f"DROP (Prober): {probe_url}")
                    from operations.pipeline.transcription import ProgressiveDownloader

                    downloader = ProgressiveDownloader(probe_url, audio_pfad)
                    downloader.start()
                    continue

            # Feed-Quellen nur jede dritte Runde (Prober laeuft alle 5s).
            poll_runde = int(time.time()) // config.PROBER_POLL_S
            if poll_runde % 3 != 0:
                time.sleep(config.PROBER_POLL_S)
                continue

            # Quelle 1: Podcast-RSS (progressiver MP3-Download), falls vorhanden.
            neu = None
            if watcher is not None:
                try:
                    neu = watcher.poll()
                except Exception as ex:  # noqa: BLE001
                    _schreibe_event("fehler", {"wo": "rss_poll", "fehler": str(ex)})
            if neu is not None and neu.audio_url and config.RSS_NUR_MUSTER:
                if not re.search(config.RSS_NUR_MUSTER, neu.audio_url):
                    _schreibe_event("rss_kandidat_verworfen", {
                        "titel": neu.title, "audio_url": neu.audio_url,
                        "grund": "kein Hauptepisoden-Muster (Special)",
                    })
                    neu = None
            # Pflicht-Titel-Muster (z.B. Lemonade Stand: nur Videos mit
            # "Lemonade Stand" im Titel qualifizieren laut Marktregel).
            if neu is not None and config.TITEL_MUSTER:
                if not re.search(config.TITEL_MUSTER, neu.title or "",
                                 re.IGNORECASE):
                    _schreibe_event("rss_kandidat_verworfen", {
                        "titel": neu.title, "audio_url": neu.audio_url,
                        "grund": "titel ohne Pflichtmuster",
                    })
                    neu = None
            # Verbots-Muster (z.B. JRE "MMA Show" zaehlt laut Regel nicht).
            if neu is not None and config.TITEL_VERBOTEN:
                if re.search(config.TITEL_VERBOTEN, neu.title or "",
                             re.IGNORECASE):
                    _schreibe_event("rss_kandidat_verworfen", {
                        "titel": neu.title, "audio_url": neu.audio_url,
                        "grund": "titel matcht Verbotsmuster",
                    })
                    neu = None
            if neu is not None and neu.audio_url:
                drop_item = neu
                drop_quelle = "libsyn_rss"
                _schreibe_event("drop_erkannt", {
                    "quelle": drop_quelle, "titel": neu.title,
                    "pubdate_utc": neu.pubdate_utc, "audio_url": neu.audio_url,
                })
                print(f"DROP (libsyn): {neu.title} ({neu.pubdate_utc})")
                from operations.pipeline.transcription import ProgressiveDownloader

                downloader = ProgressiveDownloader(neu.audio_url, audio_pfad)
                downloader.start()
                continue

            # Quelle 2: YouTube-Kanal (nur Voll-Episoden, keine Clips/Livestreams).
            try:
                yt_neue = yt_watcher.poll()
            except Exception as ex:  # noqa: BLE001
                _schreibe_event("fehler", {"wo": "yt_poll", "fehler": str(ex)})
                yt_neue = []
            for video in yt_neue:
                from operations.pipeline.transcription import (
                    YtDownloader,
                    ist_voll_episode,
                    yt_metadata,
                )

                try:
                    meta = yt_metadata(video.url)
                except Exception as ex:  # noqa: BLE001
                    _schreibe_event("fehler", {"wo": f"yt_meta:{video.video_id}",
                                               "fehler": str(ex)})
                    continue
                ok, grund = ist_voll_episode(meta)
                # Pflicht-Titel-Muster als Positiv-Identifikation (Marktregel
                # Lemonade Stand: jedes Kanal-Video mit "Lemonade Stand" im
                # Titel qualifiziert — Daily-Clips tragen das Muster nie).
                if ok and config.TITEL_MUSTER:
                    titel_meta = str(meta.get("titel") or "")
                    if not re.search(config.TITEL_MUSTER, titel_meta,
                                     re.IGNORECASE):
                        ok, grund = False, "titel ohne Pflichtmuster (qualifiziert nicht)"
                # Verbots-Muster (JRE: "MMA Show" zaehlt laut Regel nicht).
                if ok and config.TITEL_VERBOTEN:
                    titel_meta = str(meta.get("titel") or "")
                    if re.search(config.TITEL_VERBOTEN, titel_meta,
                                 re.IGNORECASE):
                        ok, grund = False, "titel matcht Verbotsmuster (z.B. MMA Show)"
                if ok and config.YT_PLAYLIST_ID:
                    # Positiv-Identifikation: NEU in der Playlist noetig.
                    from operations.pipeline.transcription import playlist_ids

                    try:
                        aktuelle = playlist_ids(config.YT_PLAYLIST_ID)
                        if video.video_id not in aktuelle:
                            ok, grund = False, "nicht in offizieller Playlist (Special)"
                        elif (playlist_baseline is not None
                              and video.video_id in playlist_baseline):
                            ok, grund = False, "bereits vor Start in Playlist (alte Episode)"
                    except Exception as ex:  # noqa: BLE001
                        ok, grund = False, f"playlist-check fehlgeschlagen: {ex}"
                _schreibe_event("yt_kandidat", {
                    "video_id": video.video_id, "titel": video.title,
                    "voll_episode": ok, "grund": grund,
                })
                if not ok:
                    continue
                drop_item = video
                drop_quelle = "youtube"
                audio_pfad = None  # wird nach Download-Ende gesetzt
                _schreibe_event("drop_erkannt", {
                    "quelle": drop_quelle, "titel": video.title,
                    "pubdate_utc": video.published_utc, "video_id": video.video_id,
                })
                print(f"DROP (youtube): {video.title}")
                downloader = YtDownloader(
                    video.url, config.LIVE_DIR / "episode_yt")
                downloader.start()
                break
            if drop_item is None:
                time.sleep(config.PROBER_POLL_S)
                continue
            continue

        # Ab hier: Episode laeuft, Chunks verarbeiten sobald verfuegbar.
        download_fertig = downloader.fertig.is_set()
        if downloader.fehler is not None:
            _schreibe_event("fehler", {"wo": "download",
                                       "fehler": str(downloader.fehler)})
            print(f"Download-Fehler: {downloader.fehler}")
            return
        if audio_pfad is None:  # YouTube: Datei erst nach Download-Ende lesbar
            if not download_fertig:
                time.sleep(2)
                continue
            audio_pfad = downloader.pfad
        try:
            segmente = transcriber.naechster_chunk(audio_pfad, final=download_fertig)
        except Exception as ex:  # noqa: BLE001
            _schreibe_event("fehler", {"wo": "transkription", "fehler": str(ex)})
            time.sleep(10)
            continue

        if segmente is None:
            if download_fertig and not no_entschieden:
                # Letzter YES-Blick: Maerkte mit erreichtem Ziel, die wegen
                # Vorscan-Pause oder zu teurem Buch nie gekauft wurden —
                # ein finaler Book-Fetch, falls sich das Fenster geoeffnet hat.
                for r in aktive:
                    if r.market_id in getradet_yes:
                        continue
                    c = counters[r.market_id]
                    ziel = (1 if r.schwelle <= 1
                            else r.schwelle + config.YES_SCHWELLE_PUFFER)
                    if c.ziel_count < ziel:
                        continue
                    try:
                        book = fetch_book(r.yes_token_id)
                        d = entscheide_yes(r, c.ziel_count, best_ask(book))
                        res = executor.place(d, book)
                        if d.action == "YES":
                            getradet_yes.add(r.market_id)
                        _schreibe_event("yes_endcheck", {
                            "markt": r.slug, "count": c.count,
                            "action": d.action, "status": res.status,
                            "grund": d.reason,
                        })
                    except Exception as ex:  # noqa: BLE001
                        _schreibe_event("fehler", {"wo": f"yes_endcheck:{r.slug}",
                                                   "fehler": str(ex)})
                # Vollstaendiges Transkript: NO-Runde. Konservativ zaehlt
                # der erweiterte Zaehler (inkl. Komposita-Verdacht, PDF-
                # Regel "Compound Words"): kein NO, wenn schon die
                # grosszuegigste Lesart die Schwelle reissen koennte.
                gefuellt = {"dry_run_fill", "live_fill", "live_partial"}
                getradet_no: set[str] = set()
                for r in aktive:
                    if r.market_id in getradet_yes:
                        continue
                    try:
                        book = fetch_book(r.no_token_id)
                        no_ask = best_ask(book)
                        c = counters[r.market_id]
                        d = entscheide_no(r, c.erweitert_count, no_ask)
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
                no_entschieden = True

                # Nachlauf: MMs ziehen beim Drop die Quotes und stellen sie
                # erst Minuten spaeter wieder rein (JRE #2523: alle Asks
                # gepullt; E280: NOs nach unserer Runde noch zu 0.50-0.70
                # gehandelt). Offene Kandidaten weiter pollen, solange
                # Budget und Zeitfenster reichen.
                nachlauf_kaeufe = 0
                ende_ts = time.time() + config.NACHLAUF_MINUTEN * 60
                _schreibe_event("nachlauf_start", {
                    "minuten": config.NACHLAUF_MINUTEN,
                    "poll_s": config.NACHLAUF_POLL_S,
                })
                while time.time() < ende_ts and not _stop():
                    # Kandidaten samt Buch/Ask sammeln, dann edge-sortiert
                    # (billigster Ask zuerst) aus dem geteilten Pool kaufen.
                    offene = []
                    for r in aktive:
                        if (r.market_id in getradet_yes
                                or r.market_id in getradet_no):
                            continue
                        c = counters[r.market_id]
                        ziel = (1 if r.schwelle <= 1
                                else r.schwelle + config.YES_SCHWELLE_PUFFER)
                        seite = None
                        if c.ziel_count >= ziel:
                            seite = "YES"
                        elif c.erweitert_count <= config.NO_ANTEIL * r.schwelle:
                            seite = "NO"
                        if seite is None:
                            continue
                        tok = r.yes_token_id if seite == "YES" else r.no_token_id
                        try:
                            book = fetch_book(tok)
                        except Exception as ex:  # noqa: BLE001
                            _schreibe_event("fehler", {
                                "wo": f"nachlauf_fetch:{r.slug}",
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
                                d = entscheide_yes(r, c.ziel_count,
                                                   k["best_ask"])
                            else:
                                d = entscheide_no(r, c.erweitert_count,
                                                  k["best_ask"])
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
                                    "markt": r.slug, "seite": seite,
                                    "count": c.count, "status": res.status,
                                    "preis": res.limit_price,
                                    "usd": res.size_usd,
                                })
                                print(f"NACHLAUF {seite}: {r.slug[:40]} "
                                      f"@ {res.limit_price}")
                        except Exception as ex:  # noqa: BLE001
                            _schreibe_event("fehler", {
                                "wo": f"nachlauf:{r.slug}", "fehler": str(ex)})
                    if budget_leer:
                        _schreibe_event("nachlauf_ende", {"grund": "budget"})
                        break
                    time.sleep(config.NACHLAUF_POLL_S)

                _schreibe_event("fertig", {
                    "endstaende": {r.slug: counters[r.market_id].count
                                   for r in aktive},
                    "nachlauf_kaeufe": nachlauf_kaeufe,
                    "ausgegeben_usd": executor.ausgegeben_usd,
                })
                print("Episode vollstaendig verarbeitet, NO-Runde und "
                      f"Nachlauf abgeschlossen ({nachlauf_kaeufe} Nachkaeufe).")
                return
            time.sleep(5)
            continue

        chunk_index += 1
        ts = now_utc_iso()
        staende = {}
        # Phase 1: alle Zaehler aktualisieren und kaufbereite Maerkte samt
        # Buch/Ask sammeln (noch nicht kaufen).
        bereit = []
        for r in aktive:
            log = counters[r.market_id].ingest_chunk(chunk_index, segmente, ts)
            staende[r.slug] = log.count_total
            if r.market_id in getradet_yes:
                continue
            # YES ausschliesslich aus Zielsprecher-Treffern (ohne
            # Verifikation identisch mit dem Gesamtzaehler).
            ziel = 1 if r.schwelle <= 1 else r.schwelle + config.YES_SCHWELLE_PUFFER
            if log.ziel_count_total >= ziel:
                # Vorscan-Pause: Buch zuletzt ueber der Obergrenze -> den
                # Roundtrip im heissen Pfad sparen (Re-Check am Ende).
                if chunk_index < yes_pause.get(r.market_id, 0):
                    continue
                try:
                    book = fetch_book(r.yes_token_id)
                    bereit.append({"rule": r, "book": book,
                                   "best_ask": best_ask(book),
                                   "count": log.ziel_count_total,
                                   "count_total": log.count_total})
                except Exception as ex:  # noqa: BLE001
                    _schreibe_event("fehler", {"wo": f"yes_fetch:{r.slug}",
                                               "fehler": str(ex)})
        # Phase 2: Edge-Priorisierung — bei mehreren gleichzeitig
        # ausgeloesten Maerkten zuerst die mit dem billigsten Ask kaufen
        # (hoechster Grenzgewinn je Dollar), damit ein teurer Markt nicht
        # in Listen-Reihenfolge den geteilten Pool leerkauft.
        for k in nach_edge_sortiert(bereit):
            r, book, ask = k["rule"], k["book"], k["best_ask"]
            try:
                d = entscheide_yes(r, k["count"], ask)
                res = executor.place(d, book)
                if d.action == "YES":
                    getradet_yes.add(r.market_id)
                elif ask is not None and ask > config.ASK_OBERGRENZE:
                    yes_pause[r.market_id] = (
                        chunk_index + config.VORSCAN_PAUSE_CHUNKS)
                _schreibe_event("yes_entscheidung", {
                    "markt": r.slug, "count": k["count_total"],
                    "best_ask": ask, "action": d.action,
                    "status": res.status, "grund": d.reason,
                })
            except Exception as ex:  # noqa: BLE001
                _schreibe_event("fehler", {"wo": f"yes:{r.slug}",
                                           "fehler": str(ex)})
        _schreibe_event("chunk", {"index": chunk_index, "staende": staende})
        print(f"Chunk {chunk_index}: " + ", ".join(
            f"{k.split('will-')[-1][:20]}={v}" for k, v in list(staende.items())[:6]
        ))


def main() -> None:
    # Windows-Konsolen/Logdateien sind oft cp1252: Episodentitel mit Emoji
    # (Lemonade Stand 🍋) wuerden print() mitten im Drop crashen.
    import sys

    for strom in (sys.stdout, sys.stderr):
        try:
            strom.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001 - z.B. ersetzte Streams in Tests
            pass

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--status", action="store_true",
                        help="einmaliger Statusbericht, keine Schleife")
    parser.add_argument("--live", action="store_true",
                        help="ECHTE Orders (sonst Dry-Run)")
    parser.add_argument("--refresh-rules", action="store_true",
                        help="Gamma-Snapshot vor dem Start aktualisieren")
    argv = parser.parse_args()

    if argv.refresh_rules or not config.GAMMA_SNAPSHOT.exists():
        refresh_rules_von_gamma()

    if argv.status:
        print(json.dumps(status_bericht(), ensure_ascii=False, indent=1))
        return
    lauf(live=argv.live)


if __name__ == "__main__":
    main()
