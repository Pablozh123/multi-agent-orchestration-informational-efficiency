"""Fernstart fuer sprechergebundene Live-Events: Stream aufloesen, Bot starten.

Fuer den unbeaufsichtigten Start (Scheduled Task oder Doppelklick auf
trump_michigan_start_live.cmd), wenn niemand am Rechner sitzt: loest die
/live-URLs der hinterlegten YouTube-Kanaele per yt-dlp auf (pollt, bis
ein Stream wirklich live ist) und startet dann earnings_bot mit
--stream — ganz ohne Browser und Loopback-Geraet. Reihenfolge =
Praeferenz: kommentarfreie Feeds zuerst (White House), Lokalsender als
Backup. Abbruch jederzeit ueber die STOP-Datei (data/live/STOP), auch
schon waehrend des Wartens.

    set BOT_PROFIL=trump_michigan_july27
    python -m operations.pipeline.trump_michigan_start [--live] [--minuten 165]

Ohne --live laeuft der Bot im Dry-Run (Messlauf). --live setzt die
kalibrierte Zielsprecher-Referenz voraus (fail-closed im earnings_bot)
sowie .env-Keys und Deposit-Wallet. Der Auto-Marker des Profils
(sprecher_marker_auto_segmente) gibt den Kaufpfad frei, sobald der
Zielsprecher nachweislich spricht — es braucht keinen Handklick mehr;
ein manueller Marker (SPRECHER_AKTIV anlegen) geht trotzdem jederzeit.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time

from operations.pipeline import config

#: /live-Kanalseiten in Praeferenz-Reihenfolge. Kommentarfrei zuerst:
#: Anchor-Voiceover eines News-Simulcasts liefe sonst in den Zaehler
#: (ECAPA faengt Fremdstimmen, aber die Quelle soll sauber sein).
KANAELE = [
    "https://www.youtube.com/@WhiteHouse/live",
    "https://www.youtube.com/@RSBN/live",
    "https://www.youtube.com/@FOX2Detroit/live",
]
POLL_S = 60
#: Wartefenster: Rede offiziell 15:00 ET, Trump-typisch +30-60 min —
#: 150 min Polling decken auch einen groben Verzug ab.
MAX_WARTE_MINUTEN = 150.0


def stream_url(watch_url: str) -> str | None:
    """Direkte Medien-URL des Livestreams oder None (noch nicht live)."""
    p = subprocess.run(
        [sys.executable, "-m", "yt_dlp", "-g", "-f", "bestaudio/best",
         "--no-warnings", watch_url],
        capture_output=True, text=True, timeout=90)
    zeilen = [z.strip() for z in (p.stdout or "").splitlines() if z.strip()]
    if p.returncode == 0 and zeilen and zeilen[0].startswith("http"):
        return zeilen[0]
    return None


def warte_auf_stream(max_minuten: float = MAX_WARTE_MINUTEN) -> str | None:
    frist = time.time() + max_minuten * 60
    while time.time() < frist:
        if config.STOP_FILE.exists():
            print("STOP-Datei — Abbruch vor dem Start.")
            return None
        for kanal in KANAELE:
            try:
                url = stream_url(kanal)
            except Exception as ex:  # noqa: BLE001 - Kanal weiterprobieren
                print(f"  {kanal}: {ex}")
                url = None
            if url:
                print(f"Stream live: {kanal}")
                return url
        print(f"noch kein Stream live — naechster Versuch in {POLL_S}s "
              f"(Rest {round((frist - time.time()) / 60)} min)")
        time.sleep(POLL_S)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--live", action="store_true",
                        help="ECHTE Orders (sonst Dry-Run-Messlauf)")
    parser.add_argument("--minuten", type=float, default=165.0,
                        help="Zeitlimit ab Capture-Start (Default 165)")
    a = parser.parse_args()

    if config.CALL_START_UTC is None:
        raise SystemExit("BOT_PROFIL ist kein Live-Event-Profil "
                         "(call_start_utc fehlt).")
    quelle = warte_auf_stream()
    if quelle is None:
        raise SystemExit("Kein Stream gefunden (oder STOP) — Bot wurde "
                         "NICHT gestartet.")
    cmd = [sys.executable, "-m", "operations.pipeline.earnings_bot",
           "--refresh-rules", "--stream", quelle,
           "--minuten", str(a.minuten)]
    if a.live:
        cmd.append("--live")
    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
