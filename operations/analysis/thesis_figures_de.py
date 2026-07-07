# -*- coding: utf-8 -*-
"""Baut Abb 15 (7 Ereignisse, Minutendaten), Abb 4 (beide Fenster), Abb 5, Abb 6 aus Repo-Artefakten."""
import csv, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = "/sessions/compassionate-gracious-babbage/mnt/ba-thesis"

def parse(s):
    return [(int(l.split()[0]), float(l.split()[1])) for l in s.strip().splitlines()]

ATTENTAT = parse("""
1720906202 0.595
1720909562 0.585
1720909742 0.590
1720909802 0.595
1720910162 0.605
1720910222 0.615
1720910282 0.640
1720910462 0.635
1720910522 0.650
1720910702 0.640
1720910762 0.645
1720910822 0.670
1720910882 0.650
1720910942 0.655
1720911002 0.645
1720911062 0.655
1720911182 0.660
1720911242 0.665
1720911782 0.655
1720912202 0.665
1720912382 0.685
1720912442 0.670
1720912502 0.665
1720912622 0.705
1720912742 0.680
1720913102 0.675
1720913162 0.680
1720913282 0.675
1720913342 0.665
1720913462 0.670
1720913522 0.675
1720913582 0.680
1720913702 0.675
1720913762 0.685
1720913942 0.680
1720914122 0.675
1720914302 0.685
1720914542 0.690
1720914602 0.680
1720914662 0.685
1720914842 0.695
1720914903 0.685
1720914962 0.695
1720915022 0.675
1720915382 0.670
1720915502 0.675
1720915862 0.665
1720916102 0.675
1720916282 0.690
1720916342 0.705
1720916402 0.690
1720917062 0.695
1720917122 0.685
1720917902 0.695
1720920542 0.695
""")
BIDEN = parse("""
1721581201 0.665
1721584321 0.655
1721584381 0.650
1721584561 0.645
1721584622 0.650
1721585082 0.645
1721585281 0.635
1721585341 0.630
1721585402 0.635
1721585701 0.630
1721585821 0.625
1721586001 0.630
1721586061 0.640
1721586121 0.645
1721586242 0.640
1721586301 0.645
1721586361 0.640
1721586601 0.650
1721586661 0.665
1721586721 0.650
1721586781 0.655
1721586961 0.645
1721587021 0.650
1721587082 0.655
1721587141 0.660
1721587261 0.655
1721587381 0.660
1721587441 0.655
1721588101 0.660
1721588221 0.655
1721588341 0.650
1721588401 0.645
1721588761 0.635
1721589721 0.655
1721589781 0.645
1721589901 0.635
1721590201 0.630
1721590321 0.625
1721590381 0.630
1721590501 0.635
1721590621 0.630
1721590681 0.635
1721590741 0.625
1721590981 0.635
1721591521 0.630
1721591581 0.635
1721591641 0.630
1721591821 0.635
1721591941 0.635
""")
DEBATTE1 = parse("""
1719534603 0.605
1719537002 0.610
1719537182 0.605
1719537242 0.610
1719537362 0.620
1719537483 0.630
1719537543 0.645
1719537603 0.635
1719537662 0.640
1719537782 0.635
1719537962 0.660
1719538082 0.665
1719538562 0.660
1719538682 0.665
1719539042 0.670
1719539103 0.665
1719539222 0.690
1719539282 0.675
1719539342 0.665
1719539402 0.655
1719539462 0.660
1719539642 0.655
1719539822 0.690
1719539942 0.685
1719540062 0.680
1719540122 0.675
1719540242 0.670
1719540422 0.665
1719540844 0.670
1719541262 0.665
1719541502 0.660
1719541562 0.655
1719541803 0.650
1719541922 0.655
1719541982 0.665
1719542042 0.655
1719542222 0.660
1719542282 0.650
1719542762 0.660
1719542882 0.670
1719542942 0.665
1719543062 0.670
1719543122 0.665
1719543782 0.655
1719543842 0.645
1719544262 0.635
1719544322 0.620
1719544562 0.640
1719544922 0.645
1719545102 0.635
1719545222 0.640
1719545342 0.640
""")
VERURTEILUNG = parse("""
1717101002 0.565
1717104842 0.560
1717104903 0.555
1717105803 0.550
1717105922 0.545
1717106642 0.535
1717106822 0.530
1717107182 0.545
1717107482 0.535
1717111742 0.535
""")
VANCE = parse("""
1721068203 0.705
1721072762 0.710
1721072822 0.715
1721073062 0.710
1721073122 0.715
1721073362 0.710
1721073422 0.705
1721073542 0.715
1721073603 0.710
1721073662 0.705
1721073902 0.715
1721074022 0.705
1721074202 0.715
1721074802 0.710
1721074862 0.715
1721074922 0.705
1721075222 0.715
1721075282 0.705
1721075462 0.715
1721075702 0.705
1721078942 0.705
""")
WALZ = parse("""
1722951001 0.525
1722954541 0.520
1722954782 0.515
1722954901 0.525
1722956101 0.515
1722956161 0.525
1722958141 0.515
1722958381 0.525
1722959701 0.515
1722961741 0.515
""")
HARRISDEB = parse("""
1726014602 0.518
1726017961 0.517
1726018022 0.516
1726018142 0.515
1726018322 0.5125
1726018382 0.511
1726018501 0.510
1726018682 0.508
1726018802 0.507
1726019102 0.505
1726019222 0.503
1726019282 0.5015
1726019402 0.4955
1726019582 0.4945
1726019641 0.4935
1726019702 0.4925
1726019821 0.4905
1726019881 0.4925
1726019942 0.4915
1726020001 0.4905
1726020061 0.489
1726020122 0.486
1726020182 0.485
1726020301 0.4885
1726020423 0.4905
1726020482 0.493
1726020781 0.4955
1726020842 0.498
1726021381 0.4965
1726021681 0.4935
1726021802 0.495
1726022342 0.492
1726022762 0.4905
1726022881 0.4885
1726023122 0.487
1726023422 0.4865
1726023721 0.4895
1726024202 0.4925
1726024322 0.4935
1726024562 0.4945
1726024742 0.493
1726024861 0.4915
1726025101 0.4875
1726025162 0.4865
1726025342 0.4885
""")

EVENTS = [
    ("Trump-Verurteilung", "30.05., 21:05 UTC", VERURTEILUNG, 1717101900, 0.565,
     "erste Abweichung +50 Min\nTief -3.5 pp (+82 Min)\n-1.0 pp nach 60 Min, -2.0 pp nach 24 h"),
    ("TV-Debatte Biden-Trump", "28.06., 01:00 UTC (Beginn)", DEBATTE1, 1719536400, 0.605,
     "Reaktion ab ca. +15 Min\n+8.0 pp nach 60 Min\n+2.0 pp nach 24 h"),
    ("Attentat auf Trump", "13.07., 22:11 UTC", ATTENTAT, 1720908660, 0.595,
     "Abweichung +15, Anstieg ab +25 Min\n+7.0 pp nach 60 Min\n+10.0 pp nach 24 h"),
    ("Vance als VP", "15.07., 19:09 UTC", VANCE, 1721069340, 0.705,
     "keine klare Reaktion (±1 pp)\n+1.0 pp nach 60 Min, 0.0 nach 24 h"),
    ("Biden-Rückzug", "21.07., 17:46 UTC", BIDEN, 1721583960, 0.665,
     "erste Reaktion +6 Min\nTief -4.0 pp (+31 Min)\n-1.0 pp nach 60 Min, -2.0 nach 24 h"),
    ("Walz als VP", "06.08., 14:07 UTC", WALZ, 1722952020, 0.525,
     "kurz -1 pp (+46 Min)\nanhaltend ab ca. +94 Min\n-1.0 pp nach 24 h"),
    ("TV-Debatte Harris-Trump", "11.09., 01:00 UTC (Beginn)", HARRISDEB, 1726016400, 0.518,
     "Rückgang ab ca. +30 Min\n-2.7 pp nach 60 Min\n-2.4 pp nach 24 h"),
]

fig, axes = plt.subplots(2, 4, figsize=(14.5, 8.0), dpi=200)
fig.suptitle("Intraday-Reaktion der Trump-Siegwahrscheinlichkeit auf die sieben kuratierten Ereignisse (Minutendaten, Polymarket CLOB)",
             fontsize=13.5, fontweight="bold", y=0.99)
flat = axes.flatten()
for ax, (name, sub, pts, t0, base, note) in zip(flat, EVENTS):
    xs = [(t - t0) / 60.0 for t, _ in pts]
    ys = [p for _, p in pts]
    ax.step(xs, ys, where="post", color="#2F63C7", linewidth=1.5)
    ax.axvline(0, color="#C0392B", linestyle="--", linewidth=1.2)
    ax.axhline(base, color="0.45", linestyle=":", linewidth=1.0)
    ax.set_title(f"{name}\n{sub}", fontsize=9.8)
    ax.tick_params(labelsize=8.5)
    ax.text(0.03, 0.03, note, transform=ax.transAxes, va="bottom", ha="left", fontsize=7.6,
            color="0.15", bbox=dict(boxstyle="round,pad=0.3", fc="#F4F6FA", ec="0.7", lw=0.6))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
flat[7].axis("off")
flat[7].text(0.05, 0.6, "t = 0: dokumentierter\nEreigniszeitpunkt (rot)\nPunktlinie: Baseline\n\nQuelle: Polymarket CLOB\nprices-history (fidelity 1),\nAbruf 02.07.2026",
             fontsize=9.5, va="top", color="0.25")
for ax in axes[1]:
    ax.set_xlabel("Minuten relativ zum Ereignis", fontsize=9)
axes[0][0].set_ylabel("Preis", fontsize=9.5)
axes[1][0].set_ylabel("Preis", fontsize=9.5)
fig.tight_layout(rect=[0, 0.01, 1, 0.94])
fig.savefig("/tmp/abb15.png", facecolor="white")
print("Abb15 ok")

# Kennzahlen-Verifikation
def price_at(pts, ts):
    last = pts[0][1]
    for t, p in pts:
        if t > ts:
            break
        last = p
    return last
for name, _, pts, t0, base, _ in EVENTS:
    p60 = price_at(pts, t0 + 3600)
    first = None
    for t, p in pts:
        if t >= t0 and abs(p - base) >= 0.0099:
            first = (t - t0) / 60.0
            break
    lo = min(p for t, p in pts if t >= t0)
    print(f"{name}: base {base} | erste>=1pp {first if first else '-'} Min | +60min {100*(p60-base):+.1f} pp | Extrem {100*(lo-base):+.1f} pp")

# ---- Abb 4: beide Fenster aus Artefakt ----
rows = list(csv.DictReader(open(f"{REPO}/data/results/h2_event_window_rows.csv")))
final = {}
for r in rows:
    key = (r["event_id"], r["window_label"])
    final[key] = float(r["cumulative_abnormal_change"])  # letzter Eintrag je Fenster gewinnt
NAME = {
    "evt_2024_05_30_trump_conviction": "Trump-Verurteilung (30.05.)",
    "evt_2024_06_28_biden_trump_debate": "Biden-Trump-Debatte (28.06.)",
    "evt_2024_07_13_trump_shooting": "Attentat auf Trump (13.07.)",
    "evt_2024_07_15_vance_vp_pick": "Vance als VP (15.07.)",
    "evt_2024_07_21_biden_withdrawal": "Biden-Rückzug (21.07.)",
    "evt_2024_08_06_walz_vp_pick": "Walz als VP (06.08.)",
    "evt_2024_09_11_harris_trump_debate": "Harris-Trump-Debatte (11.09.)",
}
GERICHTET = {"evt_2024_05_30_trump_conviction", "evt_2024_07_13_trump_shooting", "evt_2024_07_21_biden_withdrawal"}
order = sorted(NAME, key=lambda e: -final[(e, "primary_0d_to_1d")])
import numpy as np
y = np.arange(len(order))[::-1]
prim = [100 * final[(e, "primary_0d_to_1d")] for e in order]
sec = [100 * final[(e, "secondary_minus_1d_to_3d")] for e in order]
fig, ax = plt.subplots(figsize=(12, 6), dpi=200)
ax.barh(y + 0.2, prim, height=0.38, color=["#2F63C7" if e in GERICHTET else "#9AA5B1" for e in order],
        label="Primärfenster (0 bis 1 Tag)")
ax.barh(y - 0.2, sec, height=0.38, color=["#9DBBEA" if e in GERICHTET else "#CBD2DA" for e in order],
        label="Sekundärfenster (-1 bis +3 Tage)")
ax.set_yticks(y)
ax.set_yticklabels([NAME[e] for e in order], fontsize=10.5)
ax.axvline(0, color="0.2", linewidth=1.1)
for yy, v in zip(y + 0.2, prim):
    ax.text(v + (0.25 if v >= 0 else -0.25), yy, f"{v:+.1f}", va="center",
            ha="left" if v >= 0 else "right", fontsize=9)
for yy, v in zip(y - 0.2, sec):
    ax.text(v + (0.25 if v >= 0 else -0.25), yy, f"{v:+.1f}", va="center",
            ha="left" if v >= 0 else "right", fontsize=9, color="0.35")
ax.set_xlabel("Kumulierte abnormale Veränderung, Prozentpunkte", fontsize=11)
ax.set_title("H2: Tagesreaktion auf die kuratierten Ereignisse (dunkel: gerichtet erwartet, hell: Sekundärfenster)",
             fontsize=12.5, fontweight="bold", pad=12)
ax.legend(loc="lower right", fontsize=9.5, frameon=False)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.text(0.5, 0.015, "Abnormal: Veränderung über das Vor-Ereignis-Normalverhalten hinaus (Schätzfenster, n = 13). Positive Werte begünstigen Trump.",
         ha="center", fontsize=8.8, color="0.35")
fig.tight_layout(rect=[0, 0.045, 1, 1])
fig.savefig("/tmp/abb4.png", facecolor="white")
print("Abb4 ok")

# ---- Abb 5: Tier-Besetzung ----
tiers = {}
for r in csv.DictReader(open(f"{REPO}/data/results/h3_wallet_tiers.csv")):
    tiers[r["tier"]] = tiers.get(r["tier"], 0) + 1
label = {"tier_1_top_1pct": "Top 1%", "tier_2_top_5pct": "Top 5%", "tier_3_top_10pct": "Top 10%",
         "tier_4_observed_baseline": "Basis (beobachtet)"}
keys = ["tier_1_top_1pct", "tier_2_top_5pct", "tier_3_top_10pct", "tier_4_observed_baseline"]
vals = [tiers.get(k, 0) for k in keys]
fig, ax = plt.subplots(figsize=(10.8, 6), dpi=200)
bars = ax.bar([label[k] for k in keys], vals, color="#2E7D5B", width=0.62)
ax.set_yscale("log")
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v * 1.12, f"{v}", ha="center", fontsize=11.5, color="0.15")
ax.set_ylabel("Anzahl Wallets (log-Skala)", fontsize=11)
ax.set_title("H3: Besetzung der datensatz-relativen Wallet-Tiers (BUY-only, ab 10 000 USD)",
             fontsize=12.5, fontweight="bold", pad=12)
ax.tick_params(labelsize=11)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.text(0.5, 0.02, "Tiers aus kumulierten Betragsperzentilen der beobachteten Wallet-Verteilung. Quelle: h3_wallet_tiers.csv.",
         ha="center", fontsize=8.8, color="0.35")
fig.tight_layout(rect=[0, 0.045, 1, 1])
fig.savefig("/tmp/abb5.png", facecolor="white")
print("Abb5 ok:", dict(zip(keys, vals)))

# ---- Abb 6: Granger-Heatmap mit Werten ----
import numpy as np
P = {}
for r in csv.DictReader(open(f"{REPO}/data/results/h3_granger_results.csv")):
    P[(r["tier"], int(r["lag_days"]))] = float(r["p_value"])
lags = list(range(1, 8))
mat = np.array([[P[(k, l)] for l in lags] for k in keys])
fig, ax = plt.subplots(figsize=(11.25, 6), dpi=200)
im = ax.imshow(mat, cmap="viridis_r", vmin=0, vmax=1, aspect="auto")
ax.set_xticks(range(7), [str(l) for l in lags], fontsize=10.5)
ax.set_yticks(range(4), [f"{label[k]}" for k in keys], fontsize=10.5)
ax.set_xlabel("Lag (Tage)", fontsize=11)
ax.set_title("H3: Granger-p-Werte je Wallet-Tier und Lag (n = 304 gemeinsame Handelstage)",
             fontsize=12.5, fontweight="bold", pad=12)
for i in range(4):
    for j in range(7):
        v = mat[i, j]
        ax.text(j, i, f"{v:.3f}" if v >= 0.001 else f"{v:.4f}", ha="center", va="center",
                fontsize=8.6, color="white" if v > 0.5 else "black")
cb = fig.colorbar(im, ax=ax)
cb.set_label("p-Wert (klein = prädiktiver Vorlauf)", fontsize=10)
fig.text(0.5, 0.015, "Nullhypothese: Tier-Aktivität verbessert die Vorhersage der Preisänderung nicht. Quelle: h3_granger_results.csv.",
         ha="center", fontsize=8.8, color="0.35")
fig.tight_layout(rect=[0, 0.04, 1, 1])
fig.savefig("/tmp/abb6.png", facecolor="white")
print("Abb6 ok")
