"""Streaming-Transkription: progressiver Download + Chunk-Transkription.

faster-whisper small, bevorzugt GPU (CUDA float16, ~30x Echtzeit auf
RTX 3060), CPU-int8-Fallback. Der Downloader schreibt das Audio
fortlaufend auf Platte; der Transkriptor dekodiert nur bei
Dateiwachstum neu (Cache statt O(n^2)-Redecodierung), transkribiert den
Zuwachs in Bloecken von CHUNK_SEKUNDEN mit OVERLAP_S Ueberlappung und
dedupliziert ueber Wort-Zeitstempel: gezaehlt werden nur Woerter, deren
Startzeit hinter der Chunk-Grenze liegt. Der finale Rest (nach
Download-Ende) laeuft als ein grosser Batch-Durchlauf.

Zusaetzlich: YouTube-Audio-Download (yt-dlp) und Metadaten-Check fuer
die Voll-Episoden-Erkennung (Clips < 30 Min. und Livestreams sind keine
Episoden-Drops).
"""

from __future__ import annotations

import json
import math
import subprocess
import threading
from pathlib import Path

from operations.pipeline import config
from operations.pipeline.counter_engine import Segment

SAMPLE_RATE = 16_000


class ProgressiveDownloader:
    """Laedt eine Audio-URL streamend in eine Datei (eigener Thread)."""

    def __init__(self, url: str, ziel: Path) -> None:
        self.url = url
        self.ziel = ziel
        self.fertig = threading.Event()
        self.fehler: Exception | None = None
        self._thread = threading.Thread(target=self._lauf, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def _lauf(self) -> None:
        import httpx

        try:
            self.ziel.parent.mkdir(parents=True, exist_ok=True)
            with httpx.stream(
                "GET", self.url, headers=config.HTTP_HEADERS,
                timeout=60.0, follow_redirects=True,
            ) as resp:
                resp.raise_for_status()
                with open(self.ziel, "wb") as f:
                    for block in resp.iter_bytes(chunk_size=1 << 16):
                        f.write(block)
                        f.flush()
        except Exception as ex:  # noqa: BLE001 - Fehler wird im Bot gemeldet
            self.fehler = ex
        finally:
            self.fertig.set()


class YtDownloader:
    """Laedt das Audio eines YouTube-Videos via yt-dlp (eigener Thread).

    Kein progressives Dekodieren: MP4/M4A ist vor Download-Ende nicht
    dekodierbar (moov-Atom am Ende). Der Bot wartet auf `fertig` und
    verarbeitet dann per Batch-Durchlauf.
    """

    def __init__(self, video_url: str, ziel_basis: Path) -> None:
        self.video_url = video_url
        self.ziel_basis = ziel_basis  # ohne Endung; yt-dlp ergaenzt sie
        self.pfad: Path | None = None
        self.fertig = threading.Event()
        self.fehler: Exception | None = None
        self._thread = threading.Thread(target=self._lauf, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def _lauf(self) -> None:
        try:
            self.ziel_basis.parent.mkdir(parents=True, exist_ok=True)
            for alt in self.ziel_basis.parent.glob(self.ziel_basis.name + ".*"):
                alt.unlink()
            import sys

            subprocess.run(
                [sys.executable, "-m", "yt_dlp", "-f", "bestaudio",
                 "--no-playlist", "--no-part",
                 "-o", str(self.ziel_basis) + ".%(ext)s", self.video_url],
                check=True, capture_output=True, timeout=1800,
            )
            treffer = list(self.ziel_basis.parent.glob(self.ziel_basis.name + ".*"))
            if not treffer:
                raise RuntimeError("yt-dlp lieferte keine Datei")
            self.pfad = treffer[0]
        except Exception as ex:  # noqa: BLE001
            self.fehler = ex
        finally:
            self.fertig.set()


def yt_metadata(video_url: str) -> dict:
    """Dauer/Live-Status eines Videos ohne Download (yt-dlp --dump-json)."""
    import sys

    r = subprocess.run(
        [sys.executable, "-m", "yt_dlp", "--dump-single-json", "--no-download",
         "--no-playlist", video_url],
        check=True, capture_output=True, timeout=120,
    )
    d = json.loads(r.stdout)
    return {
        "titel": d.get("title"),
        "dauer_s": d.get("duration"),
        "is_live": bool(d.get("is_live")),
        "live_status": d.get("live_status"),
        "upload_date": d.get("upload_date"),  # YYYYMMDD
        "release_timestamp": d.get("release_timestamp"),
    }


def playlist_ids(playlist_id: str) -> set[str]:
    """Alle Video-IDs einer Playlist (yt-dlp, flach)."""
    import sys

    r = subprocess.run(
        [sys.executable, "-m", "yt_dlp", "--flat-playlist",
         "--dump-single-json",
         f"https://www.youtube.com/playlist?list={playlist_id}"],
        check=True, capture_output=True, timeout=120,
    )
    d = json.loads(r.stdout)
    return {e.get("id") for e in d.get("entries", []) if e.get("id")}


def in_playlist(video_id: str, playlist_id: str) -> bool:
    """Prueft via yt-dlp, ob ein Video in einer Playlist enthalten ist."""
    return video_id in playlist_ids(playlist_id)


def ist_voll_episode(meta: dict) -> tuple[bool, str]:
    """Voll-Episode: nicht live, lang genug und FRISCH (max. 48h alt)."""
    if meta.get("is_live") or meta.get("live_status") in ("is_live", "is_upcoming"):
        return False, f"livestream ({meta.get('live_status')})"
    upload = meta.get("upload_date")
    if upload:
        from datetime import datetime, timedelta, timezone

        alter = datetime.now(timezone.utc) - datetime.strptime(
            upload, "%Y%m%d").replace(tzinfo=timezone.utc)
        if alter > timedelta(hours=48):
            return False, f"upload {upload} aelter als 48h (kein frischer Drop)"
    dauer = meta.get("dauer_s")
    if dauer is None:
        return False, "keine dauer in metadaten"
    if dauer < config.YT_MIN_DAUER_S:
        return False, f"nur {dauer}s, unter {config.YT_MIN_DAUER_S}s (Clip)"
    return True, f"dauer {dauer}s"


def _cuda_dlls_einbinden() -> None:
    """Macht die pip-installierten cuBLAS/cuDNN-DLLs fuer ctranslate2 auffindbar."""
    import os

    for sub in ("cublas", "cudnn"):
        p = config.REPO_ROOT / ".venv" / "Lib" / "site-packages" / "nvidia" / sub / "bin"
        if p.is_dir():
            os.add_dll_directory(str(p))
            os.environ["PATH"] = str(p) + os.pathsep + os.environ.get("PATH", "")


def segmente_mit_wort_dedup(fw_segmente, grenze_s: float) -> list[Segment]:
    """Baut Segmente nur aus Woertern mit Startzeit >= grenze_s.

    fw_segmente sind faster-whisper-Segmente mit word_timestamps
    (Woerter tragen absolute Zeiten relativ zum transkribierten
    Ausschnitt; der Aufrufer rechnet den Ausschnitt-Offset auf die
    Grenze um). Deduplication fuer ueberlappende Chunks.
    """
    out: list[Segment] = []
    for s in fw_segmente:
        konf = math.exp(s.avg_logprob) if s.avg_logprob is not None else 0.0
        konf = max(0.0, min(1.0, konf))
        woerter = getattr(s, "words", None)
        if woerter is None:
            if s.start >= grenze_s:
                out.append(Segment(text=s.text, confidence=konf,
                                   start_s=s.start, end_s=s.end))
            continue
        behalten = [w for w in woerter if w.start >= grenze_s - 1e-6]
        if not behalten:
            continue
        text = "".join(w.word for w in behalten)
        out.append(Segment(
            text=text, confidence=konf,
            start_s=behalten[0].start, end_s=behalten[-1].end,
        ))
    return out


class ChunkTranscriber:
    """Transkribiert den Zuwachs einer wachsenden Audiodatei blockweise.

    Dekodiert die Datei nur bei Groessenaenderung neu (Cache). Chunks
    ueberlappen um OVERLAP_S; doppelte Woerter werden ueber
    Wort-Zeitstempel entfernt. Der finale Rest laeuft als ein grosser
    Durchlauf (auf GPU batched, falls verfuegbar).
    """

    def __init__(self, model_size: str = "small", verifier=None) -> None:
        from faster_whisper import WhisperModel

        # Optionaler SpeakerVerifier: rechnet jedes Segment dem
        # Zielsprecher zu (Segment.ist_ziel) oder nicht.
        self.verifier = verifier
        _cuda_dlls_einbinden()
        try:
            self.model = WhisperModel(model_size, device="cuda",
                                      compute_type="float16")
            import numpy as np

            probe, _ = self.model.transcribe(
                np.zeros(SAMPLE_RATE, dtype="float32"), language="en", beam_size=1
            )
            list(probe)
            self.geraet = "cuda/float16"
        except Exception:  # noqa: BLE001 - CPU-Fallback ist gewollt
            self.model = WhisperModel(model_size, device="cpu",
                                      compute_type="int8")
            self.geraet = "cpu/int8"
        self._batched = None
        self.verarbeitete_samples = 0
        self._audio_cache = None
        self._cache_groesse = -1

    def _decode(self, pfad: Path):
        """Dekodiert nur neu, wenn die Datei gewachsen ist (Cache)."""
        from faster_whisper.audio import decode_audio

        groesse = pfad.stat().st_size
        if self._audio_cache is None or groesse != self._cache_groesse:
            self._audio_cache = decode_audio(str(pfad), sampling_rate=SAMPLE_RATE)
            self._cache_groesse = groesse
        return self._audio_cache

    def dekodiertes_audio(self, pfad: Path):
        """Volles dekodiertes Audio (Cache) — fuer den Gap-Verify-Nachpass."""
        return self._decode(pfad)

    def neue_quelle(self) -> None:
        """Auf eine NEUE wachsende Datei umschalten (Stream-Reconnect).

        Position und Dekodier-Cache nullen; die Markt-Zaehler des
        Aufrufers bleiben unberuehrt — genau der Zweck des In-Prozess-
        Reconnects (Michigan-Lauf 27.07.: zwei Manifest-Rotationen
        haetten sonst je einen Prozess-Neustart mit Zaehlerverlust
        erzwungen).
        """
        self.verarbeitete_samples = 0
        self._audio_cache = None
        self._cache_groesse = -1

    def _transkribiere(self, ausschnitt, batched: bool):
        if batched and self.geraet.startswith("cuda"):
            if self._batched is None:
                from faster_whisper import BatchedInferencePipeline

                self._batched = BatchedInferencePipeline(model=self.model)
            segs, _ = self._batched.transcribe(
                ausschnitt, language="en", beam_size=1,
                word_timestamps=True, batch_size=8,
            )
        else:
            segs, _ = self.model.transcribe(
                ausschnitt, language="en", beam_size=1,
                vad_filter=True, word_timestamps=True,
            )
        return segs

    def naechster_chunk(self, pfad: Path, final: bool = False) -> list[Segment] | None:
        """Segmente des naechsten Chunks (mit Overlap-Dedup) oder None."""
        # Download-Start-Race: Datei existiert evtl. noch nicht oder ist
        # noch zu klein zum Dekodieren (E279-Befund).
        if not pfad.exists() or pfad.stat().st_size < 65536:
            return None
        audio = self._decode(pfad)
        verfuegbar = len(audio) - self.verarbeitete_samples
        chunk_samples = config.CHUNK_SEKUNDEN * SAMPLE_RATE
        if verfuegbar < chunk_samples and not (final and verfuegbar > 0):
            return None
        nimm = verfuegbar if final else chunk_samples
        start = self.verarbeitete_samples
        overlap = min(int(config.OVERLAP_S * SAMPLE_RATE), start)
        ausschnitt = audio[start - overlap:start + nimm]
        self.verarbeitete_samples = start + nimm

        # Grosser finaler Rest: batched deutlich schneller auf GPU.
        gross = nimm > 3 * chunk_samples
        fw_segs = self._transkribiere(ausschnitt, batched=(final and gross))

        offset_s = (start - overlap) / SAMPLE_RATE
        grenze_s = start / SAMPLE_RATE

        class _SegAdapter:
            """Verschiebt Segment/Wort-Zeiten um den Ausschnitt-Offset."""

            def __init__(self, seg):
                self.avg_logprob = seg.avg_logprob
                self.text = seg.text
                self.start = seg.start + offset_s
                self.end = seg.end + offset_s
                worte = getattr(seg, "words", None)
                self.words = None
                if worte:
                    self.words = [
                        type("W", (), {"word": w.word,
                                       "start": w.start + offset_s,
                                       "end": w.end + offset_s})()
                        for w in worte
                    ]

        adaptiert = [_SegAdapter(s) for s in fw_segs]
        segmente = segmente_mit_wort_dedup(adaptiert, grenze_s)
        if self.verifier is not None:
            for seg in segmente:
                a = int(seg.start_s * SAMPLE_RATE)
                b = int(seg.end_s * SAMPLE_RATE)
                ausschnitt_seg = audio[max(0, a):min(len(audio), b)]
                seg.ist_ziel, _sim = self.verifier.ist_zielsprecher(ausschnitt_seg)
        return segmente
