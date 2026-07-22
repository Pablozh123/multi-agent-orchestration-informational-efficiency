"""Tests fuer das atomare Schreiben publizierter Artefakte."""

from __future__ import annotations

import json

import pytest

from operations.pipeline.publish_io import schreibe_atomar


def test_schreibt_inhalt_und_legt_verzeichnis_an(tmp_path) -> None:
    ziel = tmp_path / "tief" / "runs.json"
    schreibe_atomar(ziel, '{"a": 1}\n')
    assert json.loads(ziel.read_text(encoding="utf-8")) == {"a": 1}


def test_ueberschreibt_bestehende_datei(tmp_path) -> None:
    ziel = tmp_path / "runs.json"
    ziel.write_text("alt", encoding="utf-8")
    schreibe_atomar(ziel, "neu")
    assert ziel.read_text(encoding="utf-8") == "neu"


def test_fehler_laesst_alten_stand_unangetastet(tmp_path, monkeypatch) -> None:
    """Kernfall Torn Write: bricht das Schreiben ab, bleibt der alte Stand."""

    ziel = tmp_path / "runs.json"
    ziel.write_text('{"vollstaendig": true}\n', encoding="utf-8")

    def kaputt(*args, **kwargs):
        raise OSError("Datentraeger voll")

    monkeypatch.setattr("operations.pipeline.publish_io.os.replace", kaputt)
    with pytest.raises(OSError):
        schreibe_atomar(ziel, '{"halb":')

    assert json.loads(ziel.read_text(encoding="utf-8")) == {"vollstaendig": True}
    # Keine Temp-Leichen im Publish-Ordner.
    assert [p.name for p in tmp_path.iterdir()] == ["runs.json"]


def test_keine_temp_dateien_nach_erfolg(tmp_path) -> None:
    schreibe_atomar(tmp_path / "a.json", "{}")
    schreibe_atomar(tmp_path / "b.json", "{}")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["a.json", "b.json"]


def test_zeilenenden_bleiben_lf(tmp_path) -> None:
    """Website-Artefakte sind LF; kein CRLF durch Windows-Textmodus."""

    ziel = tmp_path / "runs.json"
    schreibe_atomar(ziel, '{\n "a": 1\n}\n')
    assert b"\r\n" not in ziel.read_bytes()
