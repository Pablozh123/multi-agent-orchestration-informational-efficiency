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
import time
from datetime import datetime, timezone

from operations.pipeline import config
from operations.pipeline.counter_engine import StreamingCounter
from operations.pipeline.decision import entscheide_no, entscheide_yes
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
    rules = lade_snapshot_rules()
    aktive = [r for r in rules if r.status == "active"]
    counters = {r.market_id: StreamingCounter(r) for r in aktive}
    getradet_yes: set[str] = set()

    watcher = RssWatcher()
    baseline = watcher.initialisiere()
    yt_watcher = YouTubeWatcher()
    yt_baseline = yt_watcher.initialisiere()
    naechste_nr, prober = None, None
    if config.MP3_PROBE_MUSTER:
        try:
            naechste_nr = naechste_episoden_nummer()
            prober = Mp3UrlProber(naechste_nr)
        except Exception as ex:  # noqa: BLE001
            _schreibe_event("fehler", {"wo": "prober_init", "fehler": str(ex)})
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

    transcriber = ChunkTranscriber()
    _schreibe_event("whisper_bereit", {"geraet": transcriber.geraet})
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
                _schreibe_event("buchlog", {"n_zeilen": len(zeilen)})
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

            # Quelle 1: libsyn-RSS (progressiver MP3-Download).
            try:
                neu = watcher.poll()
            except Exception as ex:  # noqa: BLE001
                _schreibe_event("fehler", {"wo": "rss_poll", "fehler": str(ex)})
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
                # Vollstaendiges Transkript: NO-Runde.
                for r in aktive:
                    if r.market_id in getradet_yes:
                        continue
                    try:
                        book = fetch_book(r.no_token_id)
                        no_ask = best_ask(book)
                        d = entscheide_no(r, counters[r.market_id].count, no_ask)
                        res = executor.place(d, book)
                        _schreibe_event("no_runde", {
                            "markt": r.slug, "count": counters[r.market_id].count,
                            "action": d.action, "status": res.status,
                        })
                    except Exception as ex:  # noqa: BLE001
                        _schreibe_event("fehler", {"wo": f"no:{r.slug}",
                                                   "fehler": str(ex)})
                no_entschieden = True
                _schreibe_event("fertig", {
                    "endstaende": {r.slug: counters[r.market_id].count
                                   for r in aktive},
                    "ausgegeben_usd": executor.ausgegeben_usd,
                })
                print("Episode vollstaendig verarbeitet, NO-Runde abgeschlossen.")
                return
            time.sleep(5)
            continue

        chunk_index += 1
        ts = now_utc_iso()
        staende = {}
        for r in aktive:
            log = counters[r.market_id].ingest_chunk(chunk_index, segmente, ts)
            staende[r.slug] = log.count_total
            if r.market_id in getradet_yes:
                continue
            ziel = 1 if r.schwelle <= 1 else r.schwelle + config.YES_SCHWELLE_PUFFER
            if log.count_total >= ziel:
                try:
                    book = fetch_book(r.yes_token_id)
                    d = entscheide_yes(r, log.count_total, best_ask(book))
                    res = executor.place(d, book)
                    if d.action == "YES":
                        getradet_yes.add(r.market_id)
                    _schreibe_event("yes_entscheidung", {
                        "markt": r.slug, "count": log.count_total,
                        "action": d.action, "status": res.status,
                        "grund": d.reason,
                    })
                except Exception as ex:  # noqa: BLE001
                    _schreibe_event("fehler", {"wo": f"yes:{r.slug}",
                                               "fehler": str(ex)})
        _schreibe_event("chunk", {"index": chunk_index, "staende": staende})
        print(f"Chunk {chunk_index}: " + ", ".join(
            f"{k.split('will-')[-1][:20]}={v}" for k, v in list(staende.items())[:6]
        ))


def main() -> None:
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
