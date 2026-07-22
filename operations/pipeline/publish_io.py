"""Atomares Schreiben publizierter Artefakte.

Grund: ``Path.write_text`` schreibt in die Zieldatei selbst. Bricht der
Lauf mitten im Schreiben ab (Abmeldung, Task-Kill, voller Datentraeger)
oder liest die Website waehrenddessen, bleibt eine abgeschnittene, damit
ungueltige JSON-Datei zurueck. Genau das ist am 18.07.2026 mit
``runs.json`` passiert (30'072 Bytes, ungueltiges JSON).

Deshalb: erst vollstaendig in eine Temp-Datei im selben Verzeichnis
schreiben, flushen, dann per ``os.replace`` umbenennen. Das Umbenennen
ist auf einem Dateisystem atomar -- Leser sehen entweder den alten oder
den neuen vollstaendigen Stand, nie einen halben.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def schreibe_atomar(pfad: Path, text: str, *, encoding: str = "utf-8") -> Path:
    """Schreibt ``text`` vollstaendig oder gar nicht nach ``pfad``."""

    pfad.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        dir=str(pfad.parent), prefix=f".{pfad.name}.", suffix=".tmp"
    )
    temp_pfad = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_pfad, pfad)  # atomar, ueberschreibt auch unter Windows
    except BaseException:
        temp_pfad.unlink(missing_ok=True)
        raise
    return pfad
