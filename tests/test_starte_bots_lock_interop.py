"""Interop-Tests: PowerShell-Startskript vs. Watchdog-Instanz-Lock.

Vorfall 22.7.: data/live/starte_bots.ps1 (untrackt, privat) und der
Watchdog-Tick starteten lemonade_july22 sekundengleich doppelt — das
Skript kannte den Instanz-Lock des Watchdogs nicht. Fix: das Skript
haelt waehrend Pruefen+Starten DENSELBEN Lock (data/live/watchdog.lock).

Da das Skript selbst nicht im Repo liegt, ist dieser Test die
ausfuehrbare Spezifikation seiner Lock-Mechanik: .NET FileStream.Lock
auf Byte 0 (LockFile) interoperiert mit msvcrt.locking(LK_NBLCK, 1) des
Watchdogs — beide sperren dieselbe Byte-Region derselben Datei. Das
Snippet hier ist 1:1 die Mechanik im Live-Skript: OpenOrCreate +
FileShare.ReadWrite (damit beide Seiten die Datei parallel OEFFNEN
koennen und nur der Byte-Lock entscheidet), Datei wird nie geloescht.

Windows-only (CI/Linux skippt): im Feld existiert das Skript nur dort.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from operations.pipeline import watchdog

REPO_ROOT = Path(watchdog.__file__).resolve().parents[2]

pytestmark = pytest.mark.skipif(
    sys.platform != "win32",
    reason="PowerShell-Startskript und msvcrt-Lock gibt es nur unter Windows")


def _ps_snippet(lock_pfad: Path) -> str:
    """Exakt die Lock-Mechanik des Live-Skripts starte_bots.ps1."""
    return (
        "try { "
        f"$s = [System.IO.File]::Open('{lock_pfad}', "
        "[System.IO.FileMode]::OpenOrCreate, "
        "[System.IO.FileAccess]::ReadWrite, "
        "[System.IO.FileShare]::ReadWrite); "
        "$s.Lock(0, 1) "
        "} catch { "
        "[Console]::Out.WriteLine('FEHLGESCHLAGEN'); "
        "[Console]::Out.Flush(); exit 3 }; "
        "[Console]::Out.WriteLine('GEHALTEN'); [Console]::Out.Flush(); "
        "[Console]::In.ReadToEnd() | Out-Null; "
        "$s.Dispose()"
    )


def _ps_kind(lock_pfad: Path) -> subprocess.Popen:
    return subprocess.Popen(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command",
         _ps_snippet(lock_pfad)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True)


def test_powershell_lock_blockt_watchdog_und_wird_frei(tmp_path) -> None:
    # Skript haelt den Lock -> ein parallel feuernder Watchdog-Tick muss
    # sich still beenden (instanz_lock False). Nach Skript-Ende ist der
    # Lock frei, der naechste Tick laeuft normal.
    pfad = tmp_path / "watchdog.lock"
    kind = _ps_kind(pfad)
    try:
        assert kind.stdout.readline().strip() == "GEHALTEN", (
            kind.stderr.read())
        assert watchdog.instanz_lock(pfad) is False
        kind.stdin.close()
        kind.wait(timeout=60)
        assert watchdog.instanz_lock(pfad) is True
    finally:
        watchdog.instanz_lock_freigeben()
        if kind.poll() is None:
            kind.kill()


def test_watchdog_lock_blockt_powershell(tmp_path) -> None:
    # Watchdog-Tick laeuft (haelt den Lock) -> das Skript darf nicht
    # durchkommen, auch nicht die Datei kaputtmachen (kein Truncate).
    pfad = tmp_path / "watchdog.lock"
    assert watchdog.instanz_lock(pfad) is True
    try:
        kind = _ps_kind(pfad)
        try:
            assert kind.stdout.readline().strip() == "FEHLGESCHLAGEN", (
                kind.stderr.read())
            kind.stdin.close()
            kind.wait(timeout=60)
        finally:
            if kind.poll() is None:
                kind.kill()
    finally:
        watchdog.instanz_lock_freigeben()
    # Halter-PID-Notiz des Watchdogs blieb unangetastet.
    assert pfad.read_text(encoding="utf-8").strip().isdigit()
