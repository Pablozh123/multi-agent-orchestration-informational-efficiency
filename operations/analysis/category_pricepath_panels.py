# -*- coding: utf-8 -*-
"""Vier Preispfade um den Informationszeitpunkt t0 (Abbildung fuer Kapitel 4).

Liest NUR gespeicherte Rohserien: South Park E6 (Mentions, fidelity=1),
Attentat 13.07.2024 (Politik, fidelity=10), Super Bowl LX (Sport, fidelity=10),
BTC-100k (Krypto, fidelity=10). Zeigt, dass t0 je Regime anderes bedeutet:
verfuegbare Wahrheit (A, B), live entstehende Information (C), mechanische
Aufloesung (D). Stand 03.07.2026, rein deskriptiv.
"""
import json, datetime as dt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def load(path, t0_iso):
    d = json.load(open(path))
    h = d["history"]
    t0 = dt.datetime.fromisoformat(t0_iso.replace("Z", "+00:00")).timestamp()
    return [((p["t"] - t0) / 3600.0, float(p["p"])) for p in h]

sp = load("data/raw/mentions_latency/prices_southpark_s27e6.json", "2025-10-16T02:00:00Z")
att = load("data/raw/category_latency/politics_attentat_trump2024.json", "2024-07-13T22:11:00Z")
sb = load("data/raw/category_latency/sports_superbowl_lx.json", "2026-02-08T23:30:00Z")
btc = load("data/raw/category_latency/crypto_btc100k.json", "2024-12-05T03:24:00Z")

fig, axs = plt.subplots(2, 2, figsize=(12.5, 8.2))
fig.suptitle("Vier Preispfade um den Informationszeitpunkt t0", fontsize=15, fontweight="bold", y=0.985)
fig.text(0.5, 0.935, "Was t0 bedeutet, unterscheidet sich je Regime: vollständig verfügbare Wahrheit (A, B), live entstehende Information (C), mechanische Auflösung (D).\n"
         "YES-Preis des jeweiligen Markts, Minutendaten der öffentlichen API; Serien und Quellen in Tabelle A3. Rein deskriptive Darstellung.",
         ha="center", fontsize=9, color="#444444")

C = "#3d6e9e"; CT = "#a33f3f"

def panel(ax, data, xlim, ylim, title, t0label, note, notexy):
    xs = [x for x, _ in data if xlim[0] <= x <= xlim[1]]
    ys = [p for x, p in data if xlim[0] <= x <= xlim[1]]
    ax.plot(xs, ys, color=C, linewidth=1.8)
    ax.axvline(0, color=CT, linestyle="--", linewidth=1.2)
    ax.text(0.04, ylim[1] - (ylim[1]-ylim[0])*0.07, t0label, color=CT, fontsize=8.2)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.set_title(title, fontsize=10.5, loc="left")
    ax.annotate(note, xy=notexy, fontsize=8.4, color="#1f3d57",
                bbox=dict(boxstyle="round,pad=0.3", fc="#eef3f8", ec="none"))
    ax.grid(True, linestyle=":", alpha=0.5); ax.set_axisbelow(True)
    for sp_ in ("top", "right"): ax.spines[sp_].set_visible(False)
    ax.set_xlabel("Stunden relativ zu t0", fontsize=8.5)
    ax.set_ylabel("YES-Preis", fontsize=8.5)

panel(axs[0][0], sp, (-1, 18), (0, 1.06),
      "A  Mentions: South-Park-Episode (Wortnennung 3+, YES)",
      "t0: Episode veröffentlicht,\nWahrheit vollständig verfügbar",
      "16 Std bis dauerhaft über 0.9,\nobwohl ab t0 maschinell zählbar", (6.5, 0.28))
panel(axs[0][1], att, (-2, 9.5), (0.5, 0.8),
      "B  Politik: Attentat 13.07.2024 (Trump-Wahlmarkt, YES)",
      "t0: Erstmeldung 22:11 UTC",
      "Erste Reaktion nach 29 Min,\nneues Niveau (+10 Punkte) binnen einer Stunde", (2.2, 0.56))
panel(axs[1][0], sb, (-1, 4.6), (0.5, 1.06),
      "C  Sport: Super Bowl LX (Seahawks, YES)",
      "t0: Kickoff, Information\nentsteht laufend im Spiel",
      "Preis läuft mit dem Spielstand und rastet\nzum Spielende ein; keine Nachlauf-Lücke", (0.9, 0.585))
panel(axs[1][1], btc, (-1.9, 1.3), (0.7, 1.03),
      "D  Krypto: Bitcoin über 100000 USD (YES)",
      "t0: Kurs kreuzt Schwelle\n(Binance-Referenz)",
      "Auflösungsreferenz kreuzte früher:\nschon 44 Min vor t0 eingerastet", (-1.8, 0.76))

plt.tight_layout(rect=[0, 0, 1, 0.9])
plt.savefig("data/results/category_pricepaths_de.png", dpi=150)
print("Panel-Abbildung gerendert")
