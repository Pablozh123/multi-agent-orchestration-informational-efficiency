"""Sprecher-Verifikation mit MEHREREN Referenzstimmen (Union-Regel).

Hintergrund: Der Hot-Ones-Markt (Event 731776) wertet Aussagen von Jon
Bernthal ODER Tom Holland, waehrend der Host Sean Evans den groesseren
Redeanteil hat. Der Verifier muss deshalb gegen zwei Referenzen pruefen
und ein Segment schon dann zurechnen, wenn EINE davon die Schwelle
reisst — ohne dass die bestehenden Ein-Sprecher-Profile (mrbeast,
mrbeast_gaming) brechen.

speechbrain ist in der CI nicht installiert; der Encoder wird durch
einen Stub ersetzt, der die ersten drei Audio-Samples als Embedding
liest. Die Tests pruefen damit die Union-Logik, nicht das ECAPA-Modell.
"""

from __future__ import annotations

import sys
import types

import numpy as np
import pytest

from operations.pipeline import config
from operations.pipeline.baue_referenz_quellen import (
    QuellenFehler,
    parse_spanne,
)

EMB_DIM = 3


@pytest.fixture
def speechbrain_stub(monkeypatch):
    """Encoder-Stub: Embedding = erste EMB_DIM Samples des Audios.

    Der reale Embedding-Pfad (speaker.embedding) importiert torch; ohne
    torch (CI) werden diese Tests uebersprungen — wie die uebrigen
    ML-abhaengigen Tests des Repos (pytest.importorskip).
    """
    torch = pytest.importorskip("torch")

    class _Encoder:
        @classmethod
        def from_hparams(cls, source: str, savedir: str):  # noqa: ARG003
            return cls()

        def encode_batch(self, tensor):
            vek = tensor.squeeze()[:EMB_DIM].to(torch.float32)
            return vek.reshape(1, 1, EMB_DIM)

    modul = types.ModuleType("speechbrain")
    inference = types.ModuleType("speechbrain.inference")
    speaker = types.ModuleType("speechbrain.inference.speaker")
    speaker.EncoderClassifier = _Encoder
    inference.speaker = speaker
    modul.inference = inference
    monkeypatch.setitem(sys.modules, "speechbrain", modul)
    monkeypatch.setitem(sys.modules, "speechbrain.inference", inference)
    monkeypatch.setitem(sys.modules, "speechbrain.inference.speaker", speaker)
    return speaker


def _audio(richtung, laenge_s: float = 1.0) -> np.ndarray:
    """Audio, dessen erste Samples das gewuenschte Embedding kodieren."""
    from operations.pipeline.speaker import SAMPLE_RATE

    audio = np.zeros(int(laenge_s * SAMPLE_RATE), dtype="float32")
    audio[:EMB_DIM] = np.asarray(richtung, dtype="float32")
    return audio


def _referenz(tmp_path, name: str, richtung) -> object:
    pfad = tmp_path / f"referenz_{name}.npy"
    np.save(pfad, np.asarray(richtung, dtype="float32"))
    return pfad


# ------------------------------------------------ Union ueber zwei Stimmen


def test_union_rechnet_beide_zielsprecher_zu(speechbrain_stub, tmp_path) -> None:
    from operations.pipeline.speaker import SpeakerVerifier

    bernthal = _referenz(tmp_path, "bernthal", [1.0, 0.0, 0.0])
    holland = _referenz(tmp_path, "holland", [0.0, 1.0, 0.0])
    v = SpeakerVerifier([bernthal, holland], schwelle=0.5)

    assert v.namen == ["bernthal", "holland"]

    # Erste Zielstimme
    ziel, name, sim = v.zurechnung(_audio([1.0, 0.0, 0.0]))
    assert ziel is True and name == "bernthal" and sim == pytest.approx(1.0)
    # Zweite Zielstimme — die Union muss sie genauso zurechnen
    ziel, name, sim = v.zurechnung(_audio([0.0, 1.0, 0.0]))
    assert ziel is True and name == "holland" and sim == pytest.approx(1.0)
    # Host: orthogonal zu beiden Referenzen -> keine Zurechnung
    ziel, name, sim = v.zurechnung(_audio([0.0, 0.0, 1.0]))
    assert ziel is False and sim == pytest.approx(0.0)


def test_similarity_ist_das_maximum_ueber_die_referenzen(
        speechbrain_stub, tmp_path) -> None:
    from operations.pipeline.speaker import SpeakerVerifier

    v = SpeakerVerifier(
        [_referenz(tmp_path, "a", [1.0, 0.0, 0.0]),
         _referenz(tmp_path, "b", [0.0, 1.0, 0.0])],
        schwelle=0.5,
    )
    audio = _audio([0.8, 0.6, 0.0])  # naeher an a als an b
    werte = v.similarities(audio)
    assert werte["a"] == pytest.approx(0.8)
    assert werte["b"] == pytest.approx(0.6)
    assert v.similarity(audio) == pytest.approx(0.8)


def test_kurze_segmente_werden_nie_zugerechnet(speechbrain_stub, tmp_path) -> None:
    from operations.pipeline.speaker import MIN_SEGMENT_S, SpeakerVerifier

    v = SpeakerVerifier([_referenz(tmp_path, "a", [1.0, 0.0, 0.0])], schwelle=0.5)
    kurz = _audio([1.0, 0.0, 0.0], laenge_s=MIN_SEGMENT_S / 2)
    ziel, name, sim = v.zurechnung(kurz)
    assert ziel is False and name is None and sim == -1.0
    assert v.ist_zielsprecher(kurz) == (False, -1.0)


def test_einzelreferenz_bleibt_rueckwaertskompatibel(
        speechbrain_stub, tmp_path) -> None:
    """Bestehende Profile uebergeben EINEN Pfad — Verhalten unveraendert."""
    from operations.pipeline.speaker import SpeakerVerifier

    pfad = _referenz(tmp_path, "mrbeast", [1.0, 0.0, 0.0])
    v = SpeakerVerifier(pfad, schwelle=0.5)  # kein Listen-Wrapping noetig
    assert v.referenz.shape == (EMB_DIM,)
    assert v.similarity(_audio([1.0, 0.0, 0.0])) == pytest.approx(1.0)
    assert v.ist_zielsprecher(_audio([1.0, 0.0, 0.0]))[0] is True
    assert v.ist_zielsprecher(_audio([0.0, 1.0, 0.0]))[0] is False


def test_referenz_wird_normiert_geladen(speechbrain_stub, tmp_path) -> None:
    """Ungenormte .npy-Referenzen duerfen die Similarity nicht verzerren."""
    from operations.pipeline.speaker import SpeakerVerifier

    v = SpeakerVerifier([_referenz(tmp_path, "gross", [5.0, 0.0, 0.0])],
                        schwelle=0.5)
    assert v.similarity(_audio([1.0, 0.0, 0.0])) == pytest.approx(1.0)


# ------------------------------------------------ Config-Ableitung


def test_config_leitet_referenzliste_aus_beiden_keys_ab() -> None:
    """zielsprecher_referenz (einzeln) und _referenzen (Liste) gemeinsam."""

    def refs(profil: dict) -> list[str]:
        einzeln = profil.get("zielsprecher_referenz")
        liste = list(profil.get("zielsprecher_referenzen", []))
        if einzeln and einzeln not in liste:
            liste.insert(0, einzeln)
        return liste

    # Bestehende Ein-Sprecher-Profile: genau eine Referenz.
    assert len(refs(config.PROFILE["mrbeast_gaming"])) == 1
    assert len(refs(config.PROFILE["mrbeast"])) == 1
    # Profile ohne Verifikation: leer -> ZIELSPRECHER_REFERENZ bleibt None.
    assert refs(config.PROFILE["allin_july17"]) == []


def test_config_exportiert_liste_und_einzelpfad_konsistent() -> None:
    """ZIELSPRECHER_REFERENZ ist immer das erste Element der Liste."""
    if config.ZIELSPRECHER_REFERENZEN:
        assert config.ZIELSPRECHER_REFERENZ == config.ZIELSPRECHER_REFERENZEN[0]
    else:
        assert config.ZIELSPRECHER_REFERENZ is None


# ------------------------------------------------ Quellen-Parser


def test_parse_spanne_liest_quelle_und_sekunden() -> None:
    quelle, start, ende = parse_spanne("https://youtu.be/aB_c-1@120-150.5")
    assert quelle == "https://youtu.be/aB_c-1"
    assert start == pytest.approx(120.0)
    assert ende == pytest.approx(150.5)


def test_parse_spanne_akzeptiert_lokale_pfade_mit_bindestrich() -> None:
    quelle, start, ende = parse_spanne("data/live/jre_july20/episode.mp3@1800-1830")
    assert quelle == "data/live/jre_july20/episode.mp3"
    assert (start, ende) == (1800.0, 1830.0)


@pytest.mark.parametrize("angabe", [
    "https://youtu.be/ABC",          # keine Spanne
    "https://youtu.be/ABC@150-120",  # Ende vor Start
    "https://youtu.be/ABC@120-120",  # leere Spanne
])
def test_parse_spanne_weist_unbrauchbare_angaben_ab(angabe: str) -> None:
    with pytest.raises(QuellenFehler):
        parse_spanne(angabe)
