"""Live-Sichtfenster P&G-Lauf: folgt bot_events.jsonl und zeigt je
Chunk die angeschlagenen Zaehler (Brackets!), Verify und Kaeufe.
Start per sichtfenster_pg.cmd (Doppelklick)."""
import json
import time
from pathlib import Path

PFAD = Path(__file__).parent / "data/live/earnings_pg_july29/bot_events.jsonl"

print(f"Folge {PFAD} (Strg+C beendet)...")
while not PFAD.exists():
    time.sleep(1)
f = open(PFAD, encoding="utf-8")
f.seek(0, 2)  # nur Neues
while True:
    zeile = f.readline()
    if not zeile:
        time.sleep(0.5)
        continue
    try:
        e = json.loads(zeile)
    except json.JSONDecodeError:
        continue
    art = str(e.get("art", ""))
    ts = str(e.get("wall_ts_utc", ""))[11:19]
    if art == "chunk":
        heiss = {k.split("say-")[-1][:24]: v
                 for k, v in (e.get("staende") or {}).items() if v}
        stand = ", ".join(f"{k}={v}" for k, v in heiss.items()) or "-"
        print(f"{ts}Z chunk {e.get('index')}: {stand}")
    elif art == "status":
        continue
    else:
        rest = {k: v for k, v in e.items() if k not in ("wall_ts_utc", "art")}
        text = json.dumps(rest, ensure_ascii=False)[:200]
        print(f"{ts}Z >>> {art} {text}")
