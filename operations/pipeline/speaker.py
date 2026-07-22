"""Sprecher-Verifikation je Transkript-Segment (ECAPA-Embeddings).

Fuer Maerkte, die nur Aussagen BESTIMMTER Personen werten ("if MrBeast
says...", "if Jon Bernthal or Tom Holland say..."). Keine volle
Diarisierung: je Whisper-Segment wird das Audio gegen eine oder mehrere
Referenzstimmen verglichen (cosine similarity der ECAPA-Embeddings,
speechbrain/spkrec-ecapa-voxceleb, frei verfuegbar).

Mehrere Referenzen = ODER-Verknuepfung (Union): Ein Segment gilt als
Ziel, sobald EINE Referenz die Schwelle reisst. Das bildet Maerkte ab,
die mehrere Personen zusammenfassen ("Bernthal ODER Holland"), und es
haelt die Referenzen getrennt — eine gemittelte Sammel-Referenz ueber
zwei Stimmen liegt zwischen beiden und trifft am Ende keine von beiden.
Achtung: Die Union erhoeht die Falsch-Positiv-Rate (zwei Chancen, einen
Fremdsprecher faelschlich zuzurechnen) -> Schwelle je Profil pruefen.

Konservative Zurechnung: Segmente unter der Mindestlaenge oder unter der
Similarity-Schwelle gelten als NICHT Zielsprecher. Ueberlappende Stimmen
druecken die Similarity -> Segment faellt raus (Undercount). Deshalb gilt
im Entscheidungsmodul: YES nur aus Zielsprecher-Treffern, NO nur aus dem
Gesamtzaehler aller Stimmen.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np

SAMPLE_RATE = 16_000
SIMILARITY_SCHWELLE = 0.40  # kalibriert via kalibriere_schwelle.py
MIN_SEGMENT_S = 0.8         # kuerzere Segmente: keine verlaessliche Zurechnung


def _normiere(vektor: np.ndarray) -> np.ndarray:
    return vektor / np.linalg.norm(vektor)


class SpeakerVerifier:
    """Vergleicht Audio-Segmente mit einer oder mehreren Referenzstimmen."""

    def __init__(self, referenz_pfad: Path | str | Sequence[Path | str],
                 schwelle: float = SIMILARITY_SCHWELLE) -> None:
        from speechbrain.inference.speaker import EncoderClassifier

        pfade = (
            [Path(referenz_pfad)]
            if isinstance(referenz_pfad, (str, Path))
            else [Path(p) for p in referenz_pfad]
        )
        if not pfade:
            raise ValueError("Mindestens eine Referenzstimme noetig.")

        self.model = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir=str(pfade[0].parent / "ecapa_cache"),
        )
        self.pfade = pfade
        # Sprechername = Dateiname ohne Endung (referenz_bernthal.npy ->
        # "bernthal"); nur fuer Logging/Diagnose, nie fuer Entscheidungen.
        self.namen = [p.stem.replace("referenz_", "") or p.stem for p in pfade]
        self.referenzen = np.stack([_normiere(np.load(p)) for p in pfade])
        # Rueckwaertskompatibel: einzelne Referenz bleibt als Vektor lesbar.
        self.referenz = self.referenzen[0]
        self.schwelle = schwelle

    def embedding(self, audio: np.ndarray) -> np.ndarray:
        import torch

        with torch.no_grad():
            t = torch.from_numpy(audio.astype("float32")).unsqueeze(0)
            emb = self.model.encode_batch(t).squeeze().cpu().numpy()
        return _normiere(emb)

    def similarities(self, audio: np.ndarray) -> dict[str, float]:
        """Similarity je Referenzstimme (ein Embedding-Durchlauf)."""
        werte = self.referenzen @ self.embedding(audio)
        return {name: float(w) for name, w in zip(self.namen, werte)}

    def similarity(self, audio: np.ndarray) -> float:
        """Beste Similarity ueber alle Referenzen (Union-Regel)."""
        return float(np.max(self.referenzen @ self.embedding(audio)))

    def zurechnung(self, audio: np.ndarray) -> tuple[bool, str | None, float]:
        """(Zurechnung, bester Sprechername, beste Similarity).

        Zu kurze Segmente -> (False, None, -1.0).
        """
        if len(audio) < int(MIN_SEGMENT_S * SAMPLE_RATE):
            return False, None, -1.0
        werte = self.similarities(audio)
        name = max(werte, key=werte.get)
        sim = werte[name]
        return sim >= self.schwelle, name, sim

    def ist_zielsprecher(self, audio: np.ndarray) -> tuple[bool, float]:
        """(Zurechnung, Similarity). Zu kurze Segmente -> (False, -1)."""
        ziel, _name, sim = self.zurechnung(audio)
        return ziel, sim


def baue_referenz(clips: list[np.ndarray], ziel_pfad: Path) -> np.ndarray:
    """Mittelt Embeddings mehrerer Solo-Clips zur Referenzstimme."""
    from speechbrain.inference.speaker import EncoderClassifier
    import torch

    model = EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        savedir=str(Path(ziel_pfad).parent / "ecapa_cache"),
    )
    embs = []
    for clip in clips:
        with torch.no_grad():
            t = torch.from_numpy(clip.astype("float32")).unsqueeze(0)
            e = model.encode_batch(t).squeeze().cpu().numpy()
        embs.append(_normiere(e))
    referenz = _normiere(np.mean(embs, axis=0))
    ziel_pfad.parent.mkdir(parents=True, exist_ok=True)
    np.save(ziel_pfad, referenz)
    return referenz
