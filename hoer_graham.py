"""Schnelles Ohr: Graham-Stream direkt in ffplay (Minimal-Puffer).

Loest die Live-URL (Kathedrale, Fallback C-SPAN) auf und startet
ffplay nur mit Audio. Beenden: q im ffplay-Fenster oder Strg+C.
"""
import shutil
import subprocess
import sys

KANAELE = [
    "https://www.youtube.com/@WNCathedral/live",
    "https://www.youtube.com/@cspan/live",
]


def stream_url(kanal: str) -> str | None:
    print(f"Loese auf: {kanal} ...")
    p = subprocess.run(
        [sys.executable, "-m", "yt_dlp", "-g", "-f", "bestaudio/best",
         "--no-warnings", kanal],
        capture_output=True, text=True, timeout=90)
    if p.returncode != 0:
        print((p.stderr or "").strip()[:300] or "yt-dlp Fehler")
        return None
    zeilen = [z for z in (p.stdout or "").splitlines() if z.startswith("http")]
    return zeilen[0] if zeilen else None


def main() -> int:
    ffplay = shutil.which("ffplay")
    if not ffplay:
        print("ffplay nicht im PATH gefunden!")
        return 1
    for kanal in KANAELE:
        url = stream_url(kanal)
        if not url:
            continue
        print("Stream gefunden — Audio startet (beenden mit q).")
        return subprocess.call(
            [ffplay, "-nodisp", "-fflags", "nobuffer", "-flags", "low_delay",
             "-loglevel", "warning", "-i", url])
    print("Kein Stream aufloesbar.")
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(0)
