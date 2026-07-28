"""Preisspur-Rekorder fuer Kalshi-Mentions-Events (read-only, kein Konto).

Laeuft parallel zu einem Polymarket-Bot auf demselben Call und schreibt
die Kalshi-Seite mit. Ziel sind drei Messgroessen, die wir bisher nur
schaetzen (siehe `docs/project/KALSHI_MENTIONS_ANALYSE_2026-07-29.md` §6):

1. **Reaktionslatenz je Venue** — wann preist Kalshi ein gefallenes Wort
   ein, verglichen mit Polymarket und unserer eigenen Verify-Zeit?
2. **Nach-Call-Fenster** — wie lange bleiben die Maerkte nach Call-Ende
   offen? Beim PayPal-Call am 28.07. waren es 52 Minuten (Call-Ende
   13:01:11Z, Kalshi-Close 13:53:31Z), aber das ist ein einziger
   Datenpunkt und Ops-abhaengig.
3. **Gebuehrenbereinigte Edge** — welche Spanne bliebe nach der
   Taker-Gebuehr uebrig?

Der Rekorder handelt nicht und braucht keine Zugangsdaten.

Aufruf:

    python -m operations.pipeline.kalshi_recorder \
        --event KXEARNINGSMENTIONMETA-26JUL29 --dauer-min 180
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from operations.pipeline import config, kalshi_client
from operations.pipeline.kalshi_rules import build_rules

FELDER = [
    "wall_ts_utc", "event_ticker", "ticker", "wort", "status",
    "yes_bid", "yes_ask", "last_price", "spread", "gebuehr_yes_ask",
    "volume", "open_interest", "close_time",
]


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def zeile_aus_markt(markt: dict, wall_ts_utc: str) -> dict:
    """Eine CSV-Zeile aus einem Kalshi-Marktobjekt (reine Funktion)."""
    z = kalshi_client.zahl
    yes_bid = z(markt.get("yes_bid_dollars"))
    yes_ask = z(markt.get("yes_ask_dollars"))
    strike = markt.get("custom_strike") or {}
    spread = None
    if yes_bid is not None and yes_ask is not None:
        spread = round(yes_ask - yes_bid, 4)
    return {
        "wall_ts_utc": wall_ts_utc,
        "event_ticker": markt.get("event_ticker"),
        "ticker": markt.get("ticker"),
        "wort": strike.get("Word") or markt.get("yes_sub_title"),
        "status": markt.get("status"),
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "last_price": z(markt.get("last_price_dollars")),
        "spread": spread,
        "gebuehr_yes_ask": (
            None if yes_ask is None else kalshi_client.gebuehr(yes_ask)
        ),
        "volume": z(markt.get("volume_fp")),
        "open_interest": z(markt.get("open_interest_fp")),
        "close_time": markt.get("close_time"),
    }


def schreibe_zeilen(pfad: Path, zeilen: list[dict]) -> None:
    """Haengt Zeilen an die CSV an und legt bei Bedarf den Header an."""
    if not zeilen:
        return
    pfad.parent.mkdir(parents=True, exist_ok=True)
    neu = not pfad.exists()
    with open(pfad, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FELDER)
        if neu:
            writer.writeheader()
        for zeile in zeilen:
            writer.writerow({k: zeile.get(k) for k in FELDER})


def statuswechsel(
    vorher: dict[str, str], zeilen: list[dict]
) -> list[dict]:
    """Statusuebergaenge je Markt — daraus faellt die Fensterlaenge ab."""
    ereignisse = []
    for zeile in zeilen:
        ticker = zeile["ticker"]
        alt = vorher.get(ticker)
        neu = zeile["status"]
        if alt is not None and alt != neu:
            ereignisse.append({
                "wall_ts_utc": zeile["wall_ts_utc"],
                "art": "statuswechsel",
                "ticker": ticker,
                "wort": zeile["wort"],
                "von": alt,
                "nach": neu,
                "last_price": zeile["last_price"],
            })
        vorher[ticker] = neu
    return ereignisse


def schreibe_ereignisse(pfad: Path, ereignisse: list[dict]) -> None:
    if not ereignisse:
        return
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "a", encoding="utf-8") as f:
        for e in ereignisse:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def einmal(
    events: list[str], ziel: Path, vorher: dict[str, str], hole=None
) -> list[dict]:
    """Ein Abtastdurchlauf ueber alle Events; gibt die Zeilen zurueck."""
    hole = hole or kalshi_client.hole_maerkte
    wall = now_utc_iso()
    alle: list[dict] = []
    for event in events:
        try:
            maerkte = hole(event)
        except Exception as fehler:  # noqa: BLE001 - ein toter Event darf
            # den Rekorder nicht beenden; er laeuft neben einem Live-Bot.
            schreibe_ereignisse(ziel / "kalshi_ereignisse.jsonl", [{
                "wall_ts_utc": wall, "art": "fehler",
                "event_ticker": event, "meldung": str(fehler)[:300],
            }])
            continue
        alle.extend(zeile_aus_markt(m, wall) for m in maerkte)
    schreibe_zeilen(ziel / "kalshi_preisspur.csv", alle)
    schreibe_ereignisse(
        ziel / "kalshi_ereignisse.jsonl", statuswechsel(vorher, alle)
    )
    return alle


def lauf(
    events: list[str], ziel: Path, intervall_s: float, dauer_min: float
) -> None:
    """Abtastschleife bis Zeitablauf, STOP-Datei oder Ende aller Maerkte."""
    ende = time.monotonic() + dauer_min * 60.0
    vorher: dict[str, str] = {}

    # Regelableitung einmal protokollieren: belegt, welche Maerkte der
    # Bot spaeter handeln duerfte und welche als SKIP rausfallen (NQE).
    start_maerkte: list[dict] = []
    for event in events:
        try:
            start_maerkte.extend(kalshi_client.hole_maerkte(event))
        except Exception as fehler:  # noqa: BLE001
            print(f"[warnung] {event}: {fehler}")
    regeln = build_rules(start_maerkte)
    ziel.mkdir(parents=True, exist_ok=True)
    (ziel / "kalshi_regeln.json").write_text(
        json.dumps(
            [{"ticker": r.market_id, "wort": r.extra.get("wort"),
              "varianten": r.varianten, "status": r.status,
              "skip_grund": r.skip_grund} for r in regeln],
            indent=1, ensure_ascii=False),
        encoding="utf-8",
    )
    aktiv = sum(1 for r in regeln if r.status == "active")
    print(f"[start] {len(events)} Event(s), {len(regeln)} Maerkte, "
          f"{aktiv} aktiv -> {ziel}")

    while time.monotonic() < ende:
        if config.STOP_FILE.exists():
            print("[stop] STOP-Datei gesetzt")
            break
        zeilen = einmal(events, ziel, vorher)
        offen = [z for z in zeilen if z["status"] in ("active", "open")]
        print(f"[{now_utc_iso()}] {len(zeilen)} Zeilen, {len(offen)} offen")
        if zeilen and not offen:
            print("[ende] alle Maerkte geschlossen")
            break
        time.sleep(intervall_s)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--event", action="append", required=True,
                   help="Kalshi-Event-Ticker, mehrfach angebbar")
    p.add_argument("--ziel", default=None,
                   help="Ausgabeordner (Default: LIVE_DIR des Profils)")
    p.add_argument("--intervall", type=float, default=5.0,
                   help="Sekunden zwischen zwei Abtastungen")
    p.add_argument("--dauer-min", type=float, default=240.0,
                   help="Laufzeit in Minuten")
    p.add_argument("--einmal", action="store_true",
                   help="nur eine Abtastung, dann beenden")
    args = p.parse_args()

    ziel = Path(args.ziel) if args.ziel else config.LIVE_DIR
    if args.einmal:
        zeilen = einmal(args.event, ziel, {})
        print(f"{len(zeilen)} Zeilen -> {ziel / 'kalshi_preisspur.csv'}")
        return
    lauf(args.event, ziel, args.intervall, args.dauer_min)


if __name__ == "__main__":
    main()
