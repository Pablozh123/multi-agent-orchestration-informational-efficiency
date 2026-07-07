# -*- coding: utf-8 -*-
"""H3 Out-of-Sample-Fall: dokumentierter Insiderhandel (DOJ 23.04.2026, Operation Absolute Resolve).
Markt: 'Maduro out by January 31, 2026?' (conditionId 0x580adc13...f993, aufgeloest YES am 03.01.2026).
Rohdaten: data-api.polymarket.com/trades?market=<cid>&filterType=CASH&filterAmount=10000&side=BUY
(47 Trades, vollstaendig, Abruf 02.07.2026) -> data/results/h3_oos_maduro_case.csv.
Rechnet die Signatur-Kennzahlen aus der CSV nach (Fenster wie Abschnitt 2.2/2.5 der BA)."""
import csv
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
rows = list(csv.DictReader(open(ROOT / "data/results/h3_oos_maduro_case.csv", encoding="utf-8")))
for r in rows:
    r["dt"] = datetime.fromisoformat(r["timestamp_utc"])
    r["usd"] = float(r["usd"])

def win(a, b):
    A = datetime.fromisoformat(a).replace(tzinfo=timezone.utc)
    B = datetime.fromisoformat(b).replace(tzinfo=timezone.utc)
    return [r for r in rows if A <= r["dt"] < B]

base = win("2025-12-04T00:00:00", "2025-12-27T00:00:00")
ev = win("2026-01-02T00:00:00", "2026-01-07T00:00:00")
quiet = win("2025-12-22T00:00:00", "2025-12-27T00:00:00")
bw = {r["wallet"] for r in base}
ew = {r["wallet"] for r in ev}
base_daily = sum(r["usd"] for r in base) / 23.0
ev_daily = sum(r["usd"] for r in ev) / 5.0
top1 = max(sum(r["usd"] for r in ev if r["wallet"] == w) for w in ew)
yes_before = [r for r in rows if r["outcome"] == "Yes" and r["dt"] < datetime(2026, 1, 3, tzinfo=timezone.utc)]
print("neue Wallets:", len(ew - bw), "/", len(ew))
print("Volumen-Faktor:", round(ev_daily / base_daily))
print("Top-1-Konzentration:", round(100 * top1 / sum(r["usd"] for r in ev)), "%")
print("YES-Whale-Kaeufe vor 03.01.:", len(yes_before), "| Ruhefenster-Trades:", len(quiet))
