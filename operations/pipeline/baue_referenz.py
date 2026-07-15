"""Referenzstimme fuer die Sprecher-Verifikation bauen und kalibrieren.

MrBeast-Standard: Die Intros seiner Hauptvideos (Sekunden 1-9) spricht
praktisch immer er selbst — daraus wird das Referenz-Embedding gemittelt
(3 Videos), ein weiteres Video dient als Positiv-Test. Negativ-Tests
kommen aus vorhandenem Fremd-Audio (JRE-/All-In-Episoden auf Platte).

Gibt die Similarity-Verteilung aus, damit die Schwelle in speaker.py
(SIMILARITY_SCHWELLE) beurteilt werden kann.

Aufruf: python -m operations.pipeline.baue_referenz
(nutzt das aktive Profil; Ziel-Pfad = config.ZIELSPRECHER_REFERENZ)
"""

from __future__ import annotations

import numpy as np

from operations.pipeline import config
from operations.pipeline.rss_watch import fetch_yt_videos
from operations.pipeline.transcription import YtDownloader, ist_voll_episode, yt_metadata

SAMPLE_RATE = 16_000
INTRO_START_S, INTRO_ENDE_S = 1.0, 9.0


def lade_audio(pfad) -> np.ndarray:
    from faster_whisper.audio import decode_audio

    return decode_audio(str(pfad), sampling_rate=SAMPLE_RATE)


def intro_clip(pfad) -> np.ndarray:
    audio = lade_audio(pfad)
    return audio[int(INTRO_START_S * SAMPLE_RATE):int(INTRO_ENDE_S * SAMPLE_RATE)]


def main() -> None:
    if config.ZIELSPRECHER_REFERENZ is None:
        raise SystemExit("Aktives Profil hat keine zielsprecher_referenz.")

    print("Suche Hauptvideos des Kanals ...")
    kandidaten = []
    for v in fetch_yt_videos(max_items=15):
        try:
            meta = yt_metadata(v.url)
        except Exception:  # noqa: BLE001
            continue
        ok, grund = ist_voll_episode(meta)
        print(f"  {v.video_id} {grund} | {str(meta.get('titel'))[:50]}")
        if ok:
            kandidaten.append(v)
        if len(kandidaten) >= 4:
            break
    if len(kandidaten) < 3:
        raise SystemExit("Zu wenige Hauptvideos gefunden (mind. 3).")

    clips = []
    for i, v in enumerate(kandidaten):
        print(f"Lade Audio {i + 1}/{len(kandidaten)}: {v.video_id} ...")
        dl = YtDownloader(v.url, config.LIVE_DIR / f"referenz_{i}")
        dl.start()
        dl.fertig.wait(timeout=600)
        if dl.fehler:
            raise SystemExit(f"Download-Fehler: {dl.fehler}")
        clips.append(intro_clip(dl.pfad))

    from operations.pipeline.speaker import SpeakerVerifier, baue_referenz

    n_ref = len(clips) - 1  # letztes Video = Positiv-Test
    print(f"Baue Referenz aus {n_ref} Intros (letztes Video = Positiv-Test) ...")
    baue_referenz(clips[:n_ref], config.ZIELSPRECHER_REFERENZ)

    verifier = SpeakerVerifier(config.ZIELSPRECHER_REFERENZ)
    print("\nKalibrierung:")
    pos = verifier.similarity(clips[-1])
    print(f"  Positiv (ungesehenes MrBeast-Intro): {pos:+.3f}")

    negativ_quellen = [
        config.REPO_ROOT / "data" / "live" / "jre_july6" / "episode.mp3",
        config.REPO_ROOT / "data" / "live" / "allin_july3" / "episode.mp3",
    ]
    for q in negativ_quellen:
        if not q.exists():
            continue
        audio = lade_audio(q)
        for offset_min in (10, 30, 50):
            a = int(offset_min * 60 * SAMPLE_RATE)
            if a + 8 * SAMPLE_RATE > len(audio):
                continue
            sim = verifier.similarity(audio[a:a + 8 * SAMPLE_RATE])
            print(f"  Negativ ({q.parent.name} @{offset_min}min): {sim:+.3f}")

    print(f"\nSchwelle aktuell: {verifier.schwelle} — Positiv sollte klar "
          "darueber, Negative klar darunter liegen.")
    print(f"Geschrieben: {config.ZIELSPRECHER_REFERENZ}")


if __name__ == "__main__":
    main()
