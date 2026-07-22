"""Referenzstimme aus BENANNTEN Quellen und Zeitspannen bauen.

Gegenstueck zu baue_referenz.py: Das dortige Verfahren mittelt die
Sekunden 1-9 der juengsten Kanal-Hauptvideos und setzt damit voraus,
dass die Zielperson ihre eigenen Videos eroeffnet (MrBeast-Fall). Fuer
Gaeste-Formate stimmt das nicht — auf Hot Ones spricht im Intro der Host
Sean Evans, nicht der Gast. Hier werden die Solo-Passagen deshalb von
Hand benannt.

Aufruf (Zeitspannen in Sekunden, mehrfach angebbar):

    python -m operations.pipeline.baue_referenz_quellen \
        --ziel data/live/hotones_july23/referenz_bernthal.npy \
        --clip "https://youtu.be/XXXX@120-150" \
        --clip "https://youtu.be/XXXX@400-430" \
        --clip "https://youtu.be/YYYY@75-105" \
        --test "https://youtu.be/ZZZZ@200-230" \
        --negativ "data/live/allin_july17/episode.mp3@1800-1830"

--clip   fliesst in die gemittelte Referenz ein.
--test   ungesehene Solo-Passage derselben Person (Positiv-Kontrolle).
--negativ  fremde Stimme (Host, anderer Podcast) als Negativ-Kontrolle;
         akzeptiert URLs UND lokale Audiodateien.

Downloads werden je Video einmal geholt und im Arbeitsverzeichnis
zwischengespeichert (--arbeitsdir, Standard: neben der Zieldatei).
Die Kalibrier-Ausgabe zeigt, ob Positiv- klar ueber und Negativ-Werte
klar unter der Schwelle liegen — erst dann ist das Profil scharf zu
schalten.
"""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

import numpy as np

from operations.pipeline import config

SAMPLE_RATE = 16_000
_SPANNE = re.compile(r"^(?P<quelle>.+)@(?P<start>\d+(?:\.\d+)?)-(?P<ende>\d+(?:\.\d+)?)$")


class QuellenFehler(SystemExit):
    pass


def parse_spanne(angabe: str) -> tuple[str, float, float]:
    """'quelle@start-ende' -> (quelle, start_s, ende_s)."""
    treffer = _SPANNE.match(angabe.strip())
    if not treffer:
        raise QuellenFehler(
            f"Ungueltige Angabe {angabe!r} — erwartet <quelle>@<start>-<ende> "
            "mit Sekunden, z.B. https://youtu.be/ABC@120-150"
        )
    start = float(treffer.group("start"))
    ende = float(treffer.group("ende"))
    if ende <= start:
        raise QuellenFehler(f"Ende <= Start in {angabe!r}")
    return treffer.group("quelle"), start, ende


def _ist_lokal(quelle: str) -> bool:
    return not quelle.lower().startswith(("http://", "https://"))


def hole_audio_pfad(quelle: str, arbeitsdir: Path) -> Path:
    """Lokale Datei durchreichen, YouTube/Web-Quelle einmalig laden."""
    if _ist_lokal(quelle):
        pfad = Path(quelle)
        if not pfad.is_absolute():
            pfad = config.REPO_ROOT / pfad
        if not pfad.exists():
            raise QuellenFehler(f"Datei fehlt: {pfad}")
        return pfad

    from operations.pipeline.transcription import YtDownloader

    schluessel = hashlib.sha1(quelle.encode("utf-8")).hexdigest()[:12]
    basis = arbeitsdir / f"quelle_{schluessel}"
    vorhanden = sorted(arbeitsdir.glob(basis.name + ".*"))
    if vorhanden:
        return vorhanden[0]

    print(f"  Lade {quelle} ...")
    dl = YtDownloader(quelle, basis)
    dl.start()
    dl.fertig.wait(timeout=1800)
    if dl.fehler or dl.pfad is None:
        raise QuellenFehler(f"Download-Fehler bei {quelle}: {dl.fehler}")
    return dl.pfad


def lade_ausschnitt(quelle: str, start_s: float, ende_s: float,
                    arbeitsdir: Path) -> np.ndarray:
    from faster_whisper.audio import decode_audio

    pfad = hole_audio_pfad(quelle, arbeitsdir)
    audio = decode_audio(str(pfad), sampling_rate=SAMPLE_RATE)
    a, b = int(start_s * SAMPLE_RATE), int(ende_s * SAMPLE_RATE)
    if a >= len(audio):
        raise QuellenFehler(
            f"Startzeit {start_s}s liegt hinter dem Ende von {pfad.name} "
            f"({len(audio) / SAMPLE_RATE:.0f}s)."
        )
    return audio[a:min(b, len(audio))]


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ziel", required=True,
                   help="Zielpfad der .npy-Referenz (relativ zum Repo erlaubt)")
    p.add_argument("--clip", action="append", default=[], metavar="QUELLE@START-ENDE",
                   help="Solo-Passage der Zielperson (mehrfach angebbar)")
    p.add_argument("--test", action="append", default=[], metavar="QUELLE@START-ENDE",
                   help="ungesehene Solo-Passage derselben Person (Positiv-Kontrolle)")
    p.add_argument("--negativ", action="append", default=[], metavar="QUELLE@START-ENDE",
                   help="fremde Stimme (Negativ-Kontrolle)")
    p.add_argument("--arbeitsdir", default=None,
                   help="Cache fuer Downloads (Standard: <ziel-ordner>/referenz_quellen)")
    p.add_argument("--schwelle", type=float, default=None,
                   help="Schwelle fuer die Kalibrier-Ausgabe (Standard: Profilwert)")
    args = p.parse_args(argv)

    if not args.clip:
        raise QuellenFehler("Mindestens ein --clip noetig.")

    ziel = Path(args.ziel)
    if not ziel.is_absolute():
        ziel = config.REPO_ROOT / ziel
    arbeitsdir = (Path(args.arbeitsdir) if args.arbeitsdir
                  else ziel.parent / "referenz_quellen")
    arbeitsdir.mkdir(parents=True, exist_ok=True)

    print(f"Baue Referenz {ziel.name} aus {len(args.clip)} Clip(s):")
    clips = []
    for angabe in args.clip:
        quelle, start_s, ende_s = parse_spanne(angabe)
        clip = lade_ausschnitt(quelle, start_s, ende_s, arbeitsdir)
        print(f"  + {start_s:.0f}-{ende_s:.0f}s ({len(clip) / SAMPLE_RATE:.1f}s) "
              f"aus {quelle}")
        clips.append(clip)

    from operations.pipeline.speaker import SIMILARITY_SCHWELLE, SpeakerVerifier, baue_referenz

    baue_referenz(clips, ziel)
    schwelle = args.schwelle
    if schwelle is None:
        schwelle = getattr(config, "SPRECHER_SCHWELLE", SIMILARITY_SCHWELLE)
    verifier = SpeakerVerifier(ziel, schwelle=schwelle)

    print("\nKalibrierung (Schwelle "
          f"{schwelle:.2f} — Positiv sollte klar darueber, Negativ klar darunter):")
    for angabe in args.test:
        quelle, start_s, ende_s = parse_spanne(angabe)
        clip = lade_ausschnitt(quelle, start_s, ende_s, arbeitsdir)
        print(f"  Positiv {quelle} @{start_s:.0f}-{ende_s:.0f}s: "
              f"{verifier.similarity(clip):+.3f}")
    for angabe in args.negativ:
        quelle, start_s, ende_s = parse_spanne(angabe)
        clip = lade_ausschnitt(quelle, start_s, ende_s, arbeitsdir)
        print(f"  Negativ {quelle} @{start_s:.0f}-{ende_s:.0f}s: "
              f"{verifier.similarity(clip):+.3f}")
    if not args.test and not args.negativ:
        print("  (keine Kontrollen angegeben — Schwelle bleibt unbelegt)")

    print(f"\nGeschrieben: {ziel}")


if __name__ == "__main__":
    main()
