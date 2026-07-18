"""Probedurchlauf der Transkriptions- und Zaehl-Pipeline (ohne Orders).

Laedt die ersten N Megabyte eines Podcast-MP3 (Range-Request), laesst
ChunkTranscriber + StreamingCounter mit den echten Marktregeln des
july-3-Events darueberlaufen und druckt je Chunk Dauer und Zaehlstaende.

Aufruf:
  python -m operations.pipeline.probelauf --url <mp3> [--mb 4]
Ohne --url wird die Audio-URL des neuesten Feed-Items genommen.
"""

from __future__ import annotations

import argparse
import time

from operations.pipeline import config
from operations.pipeline.counter_engine import StreamingCounter
from operations.pipeline.market_rules import lade_snapshot_rules
from operations.pipeline.rss_watch import fetch_feed_items


def lade_teilaudio(url: str, mb: float, ziel) -> int:
    import httpx

    ziel.parent.mkdir(parents=True, exist_ok=True)
    grenze = int(mb * 1024 * 1024)
    headers = dict(config.HTTP_HEADERS)
    headers["Range"] = f"bytes=0-{grenze - 1}"
    geladen = 0
    with httpx.stream("GET", url, headers=headers, timeout=60.0,
                      follow_redirects=True) as resp:
        resp.raise_for_status()
        with open(ziel, "wb") as f:
            for block in resp.iter_bytes(chunk_size=1 << 16):
                f.write(block)
                geladen += len(block)
                if geladen >= grenze:
                    break
    return geladen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", default=None, help="MP3-URL (Default: neuestes Feed-Item)")
    parser.add_argument("--mb", type=float, default=4.0, help="wieviel MB laden")
    argv = parser.parse_args()

    url = argv.url
    if url is None:
        item = fetch_feed_items(max_items=1)[0]
        url = item.audio_url
        print(f"Feed-Item: {item.title[:70]}")
    ziel = config.LIVE_DIR / "probelauf.mp3"

    t0 = time.time()
    geladen = lade_teilaudio(url, argv.mb, ziel)
    print(f"Download: {geladen / 1e6:.1f} MB in {time.time() - t0:.1f}s")

    from operations.pipeline.transcription import ChunkTranscriber

    t0 = time.time()
    tr = ChunkTranscriber()
    print(f"Modell geladen in {time.time() - t0:.1f}s")

    rules = [r for r in lade_snapshot_rules() if r.status == "active"]
    counters = {r.market_id: StreamingCounter(r) for r in rules}

    chunk_index = 0
    rest_versucht = False
    while True:
        t0 = time.time()
        segmente = tr.naechster_chunk(ziel, final=rest_versucht)
        if segmente is None or not segmente:
            if rest_versucht:
                break
            rest_versucht = True  # letzter Teil-Chunk (wie Download-Ende im Bot)
            continue
        chunk_index += 1
        dauer = time.time() - t0
        for r in rules:
            counters[r.market_id].ingest_chunk(chunk_index, segmente, "probelauf")
        treffer = {
            r.question.split('"')[1]: counters[r.market_id].count
            for r in rules if counters[r.market_id].count > 0
        }
        print(f"Chunk {chunk_index}: {dauer:.1f}s Rechenzeit, "
              f"~{config.CHUNK_SEKUNDEN}s Audio | Staende: {treffer}")
        print(f"  Beispieltext: {segmente[0].text[:100].strip()}"
              f" (Konfidenz {segmente[0].confidence:.2f})")

    print("\nEndstaende (nur Treffer):")
    for r in rules:
        c = counters[r.market_id]
        flags = sum(log.uebersprungen_homophon for log in c.logs)
        if c.count > 0 or flags > 0:
            print(f"  {r.question[:60]:60s} count={c.count} "
                  f"homophon_uebersprungen={flags}")


if __name__ == "__main__":
    main()
