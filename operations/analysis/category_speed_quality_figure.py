# -*- coding: utf-8 -*-
"""Abbildung: Vorhersageguete (Brier T-7) vs. Einpreisungs-Geschwindigkeit je Kategorie.

Liest ausschliesslich data/results/category_efficiency_summary_v2.csv und
data/results/category_latency_examples.csv. Zeitachse mit lesbaren Ticks
(1 Min bis 8 Std) statt Zehnerpotenzen. Stand 03.07.2026, rein deskriptiv.
Speed-Werte: Krypto/Sport/Popkultur je 1 kuratiertes Ereignis, Politik aus
Tabelle A1 der Thesis (Spannenmitte 60 Min), Mentions Median aus 12 Maerkten.
Sport/Popkultur enthalten konstruktionsbedingt Spiel- bzw. Zeremoniedauer.
"""
import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("data/results/category_efficiency_summary_v2.csv")
brier = dict(zip(df["kategorie"], df["brier_t7"]))
n7 = dict(zip(df["kategorie"], df["n_t7"]))
speed = {"Krypto": 1.0, "Sport": 180.4, "Popkultur": 220.4, "Politik": 60.0, "Mentions": 260.7}
note = {"Krypto": "vor Ereignis eingepreist,\nUntergrenze 1 Min", "Sport": "enthält Spieldauer*",
        "Popkultur": "enthält Zeremoniedauer*", "Politik": "Tabelle A1, Spannenmitte", "Mentions": "Median, 12 Märkte"}

fig, ax = plt.subplots(figsize=(11.5, 7.0))
fig.suptitle("Vorhersagegüte und Einpreisungs-Geschwindigkeit je Polymarket-Kategorie",
             fontsize=14, fontweight="bold", y=0.985)
fig.text(0.5, 0.905, "x: mittlerer Brier-Score sieben Tage vor Auflösung (60 bis 81 Märkte je Kategorie).\n"
         "y: Zeit, bis der Preis nach dem Informationsereignis dauerhaft auf der richtigen Seite von 0.9 bzw. 0.1 lag.\n"
         "*t0 = Beginn des Ereignisses, Wert enthält Spiel- bzw. Zeremoniedauer. Datenstand 03.07.2026, rein deskriptiv.",
         ha="center", fontsize=8.5, color="#444444")

pos = {"Sport": (-0.012, 0.52, "right", "center"), "Popkultur": (0.012, 0.52, "left", "center"),
       "Mentions": (0.012, 1.6, "left", "center"), "Politik": (0.0, 1.45, "center", "bottom"),
       "Krypto": (0.014, 1.0, "left", "center")}
for k in speed:
    x, y = brier[k], speed[k]
    ax.scatter(x, y, s=260, color="#3d6e9e", zorder=3)
    dx, fy, ha, va = pos[k]
    ax.annotate(f"{k}\n({note[k]})", (x, y), xytext=(x + dx, y * fy), ha=ha, va=va, fontsize=9.5, color="#1f3d57")

ax.set_yscale("log")
ticks = [1, 10, 60, 240, 480]
ax.set_yticks(ticks)
ax.set_yticklabels(["1 Min", "10 Min", "1 Std", "4 Std", "8 Std"])
ax.set_ylim(0.5, 900)
ax.set_xlim(-0.02, 0.42)
ax.set_xlabel("Mittlerer Brier-Score sieben Tage vor Auflösung (tiefer = besser vorhersagbar)")
ax.set_ylabel("Zeit bis zur Einpreisung des Ereignisses")
ax.grid(True, linestyle=":", alpha=0.5); ax.set_axisbelow(True)
for s in ("top", "right"): ax.spines[s].set_visible(False)
plt.tight_layout(rect=[0, 0, 1, 0.845])
plt.savefig("data/results/category_speed_quality_de.png", dpi=150)
print("Abbildung neu gerendert mit Zeit-Ticks")
