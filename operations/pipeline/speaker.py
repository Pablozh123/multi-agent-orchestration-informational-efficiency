"""Sprecher-Verifikation je Transkript-Segment (ECAPA-Embeddings).

Fuer Maerkte, die nur Aussagen EINER Person werten ("if MrBeast says...").
Keine volle Diarisierung: je Whisper-Segment wird das Audio gegen eine
Referenzstimme verglichen (cosine similarity der ECAPA-Embeddings,
speechbrain/spkrec-ecapa-voxceleb, frei verfuegbar).

Konservative Zurechnung: Segmente unter der Mindestlaenge oder unter der
Similarity-Schwelle gelten als NICHT Zielsprecher. Ueberlappende Stimmen
druecken die Similarity -> Segment faellt raus (Undercount). Deshalb gilt
im Entscheidungsmodul: YES nur aus Zielsprecher-Treffern, NO nur aus dem
Gesamtzaehler aller Stimmen.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

SAMPLE_RATE = 16_000
SIMILARITY_SCHWELLE = 0.40  # kalibriert via kalibriere_schwelle.py
MIN_SEGMENT_S = 0.8         # kuerzere Segmente: keine verlaessliche Zurechnung


class SpeakerVerifier:
    """Vergleicht Audio-Segmente mit einer Referenzstimme."""

    def __init__(self, referenz_pfad: Path,
                 schwelle: float = SIMILARITY_SCHWELLE) -> None:
        from speechbrain.inference.speaker import EncoderClassifier

        self.model = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir=str(Path(referenz_pfad).parent / "ecapa_cache"),
        )
        self.referenz = np.load(referenz_pfad)
        self.referenz = self.referenz / np.linalg.norm(self.referenz)
        self.schwelle = schwelle

    def embedding(self, audio: np.ndarray) -> np.ndarray:
        import torch

        with torch.no_grad():
            t = torch.from_numpy(audio.astype("float32")).unsqueeze(0)
            emb = self.model.encode_batch(t).squeeze().cpu().numpy()
        return emb / np.linalg.norm(emb)

    def similarity(self, audio: np.ndarray) -> float:
        return float(np.dot(self.embedding(audio), self.referenz))

    def ist_zielsprecher(self, audio: np.ndarray) -> tuple[bool, float]:
        """(Zurechnung, Similarity). Zu kurze Segmente -> (False, -1)."""
        if len(audio) < int(MIN_SEGMENT_S * SAMPLE_RATE):
            return False, -1.0
        sim = self.similarity(audio)
        return sim >= self.schwelle, sim


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
        embs.append(e / np.linalg.norm(e))
    referenz = np.mean(embs, axis=0)
    referenz = referenz / np.linalg.norm(referenz)
    ziel_pfad.parent.mkdir(parents=True, exist_ok=True)
    np.save(ziel_pfad, referenz)
    return referenz
