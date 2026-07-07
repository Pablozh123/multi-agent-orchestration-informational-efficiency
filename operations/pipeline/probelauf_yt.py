"""Voll-Probelauf des YouTube-Pfads: Download + Batch-Transkription + Zaehler.

Simuliert exakt den Bot-Ablauf bei einem YouTube-Drop (Video-Drop, kein
Livestream): Metadaten-Check, yt-dlp-Audio-Download, ein grosser
Batch-Transkriptionsdurchlauf, Zaehlstaende mit den echten july-3-Regeln.
Keine Orders. Misst die Dauer jedes Schritts.

Aufruf: python -m operations.pipeline.probelauf_yt [--url <video>]
Ohne --url wird die neueste Voll-Episode des All-In-Kanals genommen.
"""

from __future__ import annotations

import argparse
import time

from operations.pipeline import config
from operations.pipeline.counter_engine import StreamingCounter
from operations.pipeline.market_rules import lade_snapshot_rules
from operations.pipeline.rss_watch import fetch_yt_videos
from operations.pipeline.transcription import (
    ChunkTranscriber,
    YtDownloader,
    ist_voll_episode,
    yt_metadata,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", default=None)
    argv = parser.parse_args()

    gesamt_t0 = time.time()

    url = argv.url
    if url is None:
        for video in fetch_yt_videos(max_items=10):
            t0 = time.time()
            meta = yt_metadata(video.url)
            ok, grund = ist_voll_episode(meta)
            print(f"Kandidat: {video.title[:55]} -> {grund} "
                  f"(Metadaten-Check {time.time() - t0:.1f}s)")
            if ok:
                url = video.url
                break
    if url is None:
        raise SystemExit("Keine Voll-Episode im Feed gefunden.")

    t0 = time.time()
    dl = YtDownloader(url, config.LIVE_DIR / "probelauf_yt")
    dl.start()
    dl.fertig.wait(timeout=1800)
    if dl.fehler:
        raise SystemExit(f"Download-Fehler: {dl.fehler}")
    dauer_dl = time.time() - t0
    groesse_mb = dl.pfad.stat().st_size / 1e6
    print(f"Download: {groesse_mb:.1f} MB in {dauer_dl:.1f}s -> {dl.pfad.name}")

    t0 = time.time()
    tr = ChunkTranscriber()
    print(f"Whisper geladen ({tr.geraet}) in {time.time() - t0:.1f}s")

    rules = [r for r in lade_snapshot_rules() if r.status == "active"]
    counters = {r.market_id: StreamingCounter(r) for r in rules}

    t0 = time.time()
    segmente = tr.naechster_chunk(dl.pfad, final=True)
    dauer_tx = time.time() - t0
    audio_min = tr.verarbeitete_samples / 16000 / 60
    print(f"Transkription: {audio_min:.1f} Min. Audio in {dauer_tx:.1f}s "
          f"({audio_min * 60 / dauer_tx:.0f}x Echtzeit), "
          f"{len(segmente or [])} Segmente")

    t0 = time.time()
    for r in rules:
        counters[r.market_id].ingest_chunk(1, segmente or [], "probelauf_yt")
    print(f"Zaehler: {time.time() - t0:.2f}s")

    print(f"\nGESAMT (Metadaten + Download + Laden + Transkription + Zaehlen): "
          f"{time.time() - gesamt_t0:.1f}s")
    print("\nZaehlstaende (nur Treffer), Schwelle in Klammern:")
    for r in sorted(rules, key=lambda x: -counters[x.market_id].count):
        c = counters[r.market_id]
        if c.count > 0:
            flags = sum(log.uebersprungen_homophon for log in c.logs)
            print(f"  {r.question[:58]:58s} ({r.schwelle:>2d}+) count={c.count}"
                  + (f" homophon_uebersprungen={flags}" if flags else ""))


if __name__ == "__main__":
    main()
