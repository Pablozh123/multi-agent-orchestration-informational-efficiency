"""Startwache: genau EINE Bot-Instanz je Profil (gegen Doppelstart).

Vorfall 22.7. 10:55:02-03Z: Watchdog-Tick und starte_bots.ps1 starteten
lemonade_july22 sekundengleich DOPPELT. Das Skript prueft je Profil nur
bot.pid — die schrieb der 1 s aeltere Watchdog-Start aber erst nach dem
Trading-Setup (Imports + Modell-Laden: zehn+ Sekunden Race-Fenster
zwischen Prozessstart und PID-Write). Jeder Starter-seitige Check kann
dieses Fenster nur verkleinern, nie schliessen — darum lebt die Wache
im BOT selbst: egal wer startet (Watchdog, Skript, Hand), die zweite
Instanz desselben Profils beendet sich, bevor sie das Trading-Setup
beruehrt. bot.pid wird atomar SOFORT nach dem Wache-Gewinn geschrieben.

Mechanik wie watchdog.instanz_lock (PR #18): OS-Dateilock
(msvcrt.locking unter Windows, flock sonst) auf
data/live/<profil>/start.lock. Der Handle bleibt bewusst bis zum
Prozessende offen; das OS gibt den Lock bei JEDEM Prozessende frei —
auch nach Kill oder Absturz. Bewusst KEIN O_CREAT|O_EXCL mit
Alters-Verwurf: eine liegengebliebene Datei blockiert so nie (kein
Lockout nach Crash), und es gibt kein Unlink/Neuanlegen-Fenster, in dem
zwei Starter dieselbe "verwaiste" Datei verwerfen und beide durchkommen.
Die Datei wird nie geloescht; ihr Inhalt (Halter-PID) ist reine
Forensik-Notiz. Nebenbei schuetzt der Lebenszeit-Lock nicht nur den
Start, sondern den GESAMTEN Lauf.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


class Startwache:
    """Exklusiver Profil-Lock auf <live_dir>/start.lock."""

    def __init__(self, live_dir: Path) -> None:
        self.lock_pfad = Path(live_dir) / "start.lock"
        self._fd: int | None = None

    def nehmen(self) -> bool:
        """Nimmt den Lock; False = andere Instanz dieses Profils lebt."""
        self.lock_pfad.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(self.lock_pfad), os.O_CREAT | os.O_RDWR)
        try:
            if sys.platform == "win32":
                import msvcrt
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(fd)
            return False
        try:  # Halter-PID als Forensik-Notiz (lesbar, sobald der Lock frei ist)
            os.ftruncate(fd, 0)
            os.write(fd, str(os.getpid()).encode("ascii"))
        except OSError:
            pass
        self._fd = fd
        return True

    def freigeben(self) -> None:
        """Gibt den Lock explizit frei (Tests; im Betrieb reicht Prozessende)."""
        if self._fd is None:
            return
        try:
            if sys.platform == "win32":
                import msvcrt
                os.lseek(self._fd, 0, os.SEEK_SET)
                msvcrt.locking(self._fd, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._fd, fcntl.LOCK_UN)
        except OSError:
            pass
        os.close(self._fd)
        self._fd = None


def bot_pid_schreiben(live_dir: Path) -> None:
    """Schreibt bot.pid atomar (tmp + os.replace): nie halb lesbar."""
    live_dir = Path(live_dir)
    tmp = live_dir / "bot.pid.tmp"
    tmp.write_text(str(os.getpid()), encoding="utf-8")
    os.replace(tmp, live_dir / "bot.pid")


_WACHE: Startwache | None = None


def wache_nehmen(live_dir: Path) -> bool:
    """Profil-Wache nehmen und bot.pid atomar schreiben.

    False = eine andere Instanz dieses Profils laeuft (oder startet)
    bereits — der Aufrufer beendet sich dann, OHNE bot.pid anzufassen.
    Der Gewinner haelt die Wache ueber die globale Referenz bis zum
    Prozessende.
    """
    global _WACHE
    wache = Startwache(live_dir)
    if not wache.nehmen():
        return False
    _WACHE = wache
    bot_pid_schreiben(Path(live_dir))
    return True


def wache_freigeben() -> None:
    """Gibt die globale Wache explizit frei (nur fuer Tests noetig)."""
    global _WACHE
    if _WACHE is not None:
        _WACHE.freigeben()
        _WACHE = None
