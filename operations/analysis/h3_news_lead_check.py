# -*- coding: utf-8 -*-
"""H3-Ergaenzung: Tier-1-Kaufvolumen in den 24h vor verifizierten Ereignis-Zeitstempeln
vs. mittleres Tagesvolumen des Basisfensters (-30d..-8d). Deskriptiv, BUY-only, alle Maerkte
des Whale-Extrakts. Schreibt data/results/h3_news_lead_check.csv. Erstellt 02.07.2026."""
import sqlite3, csv, statistics as st
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
c = sqlite3.connect(ROOT / "data" / "thesis.db")
tier1 = {r["wallet_address"] for r in csv.DictReader(open(ROOT / "data/results/h3_wallet_tiers.csv"))
         if r["tier"] == "tier_1_top_1pct"}

def ts(s):
    s = s.replace(" UTC", "").replace("+00:00", "").rstrip("Z").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            pass
    raise ValueError(s)

rows = c.execute("SELECT price_timestamp, wallet_address, amount_usd FROM whale_trades").fetchall()
data = [(ts(r[0]), r[1], float(r[2])) for r in rows]

EVENTS = [("Verurteilung", "2024-05-30T21:05"), ("Debatte 1", "2024-06-28T01:00"),
          ("Attentat", "2024-07-13T22:11"), ("Vance", "2024-07-15T19:09"),
          ("Biden-Rueckzug", "2024-07-21T17:46"), ("Walz", "2024-08-06T14:07"),
          ("Debatte 2", "2024-09-11T01:00")]
out = []
for name, iso in EVENTS:
    t0 = datetime.fromisoformat(iso).replace(tzinfo=timezone.utc).timestamp()
    pre = sum(a for t, w, a in data if w in tier1 and t0 - 86400 <= t < t0)
    pre_n = sum(1 for t, w, a in data if w in tier1 and t0 - 86400 <= t < t0)
    base = [sum(a for t, w, a in data if w in tier1 and t0 - d * 86400 <= t < t0 - (d - 1) * 86400)
            for d in range(8, 31)]
    bm, bmed = st.mean(base), st.median(base)
    out.append([name, iso + "Z", round(pre, 2), pre_n, round(bm, 2), round(bmed, 2),
                round(pre / bm, 3) if bm else None])
with open(ROOT / "data/results/h3_news_lead_check.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["event", "t0_utc", "tier1_buy_usd_pre24h", "tier1_trades_pre24h",
                "baseline_daily_mean_usd", "baseline_daily_median_usd", "ratio_pre24h_vs_baseline_mean"])
    w.writerows(out)
for o in out:
    print(o)
