# -*- coding: utf-8 -*-
"""Rendert Abb 1, 3, 7, 8, 9, 11, 12, 13 deutsch aus Repo-Artefakten. Seitenverhaeltnisse wie im Docx."""
import csv, math, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

D = "/sessions/compassionate-gracious-babbage/mnt/ba-thesis/data/results"
BLAU, ROT, GRAU, ORANGE, GRUEN = "#2F63C7", "#C4372B", "#8E99A4", "#E58A2E", "#2E7D5B"

def rd(name):
    return list(csv.DictReader(open(f"{D}/{name}", encoding="utf-8")))

def foot(fig, text):
    fig.text(0.5, 0.012, text, ha="center", fontsize=8.6, color="0.35")

# ---------------- Abb 1 ----------------
try:
    rows = rd("h1_brier_scores.csv")
    pm = [float(r["bs_polymarket"]) for r in rows]
    fte = [float(r["bs_fivethirtyeight"]) for r in rows]
    a50 = [float(r["bs_always_50"]) for r in rows]
    prd = [float(r["bs_prior_day"]) for r in rows]
    fpm = [float(r["forecast_polymarket"]) for r in rows]
    ffte = [float(r["forecast_fivethirtyeight"]) for r in rows]
    dates = [r["date"] for r in rows]
    x = np.arange(len(rows))
    def hh(a, b):
        w = sum(1 for i in range(len(a)) if a[i] < b[i]); l = sum(1 for i in range(len(a)) if b[i] < a[i])
        return w, l, len(a) - w - l
    fig, ax = plt.subplots(2, 2, figsize=(12, 7.64), dpi=200)
    names = ["Polymarket", "FiveThirtyEight", "Konstant 50%", "Polymarket-Vortag"]
    means = [np.mean(pm), np.mean(fte), np.mean(a50), np.mean(prd)]
    b = ax[0][0].bar(names, means, color=[BLAU, ROT, GRAU, ORANGE], width=0.62)
    for bb, v in zip(b, means):
        ax[0][0].text(bb.get_x() + bb.get_width() / 2, v + 0.006, f"{v:.3f}", ha="center", fontsize=9.5)
    ax[0][0].set_title("Mittlerer Brier-Verlust (tiefer = besser)", fontsize=11)
    ax[0][0].tick_params(axis="x", labelsize=8.5, rotation=12); ax[0][0].set_ylim(0, 0.38)
    comps = [("FiveThirtyEight", fte), ("Konstant 50%", a50), ("Polymarket-Vortag", prd)]
    w_ = [hh(pm, c[1]) for c in comps]
    xx = np.arange(3)
    ax[0][1].bar(xx, [w[0] for w in w_], 0.6, label="Polymarket tiefer", color=BLAU)
    ax[0][1].bar(xx, [w[1] for w in w_], 0.6, bottom=[w[0] for w in w_], label="Vergleich tiefer", color=ROT)
    ax[0][1].bar(xx, [w[2] for w in w_], 0.6, bottom=[w[0] + w[1] for w in w_], label="unentschieden", color=GRAU)
    ax[0][1].set_xticks(xx, [c[0] for c in comps], fontsize=8.5)
    ax[0][1].set_title("Tag für Tag: wer hat den tieferen Verlust (194 Tage)", fontsize=11)
    ax[0][1].legend(fontsize=8, frameon=False)
    cum = np.cumsum(np.array(fte) - np.array(pm))
    ax[1][0].plot(x, cum, color=BLAU, lw=1.8)
    ax[1][0].set_title("Kumulierter Verlustvorteil gegenüber FiveThirtyEight", fontsize=11)
    ax[1][0].set_xlabel("Handelstag (März bis September 2024)", fontsize=9)
    ax[1][0].axhline(0, color="0.3", lw=0.8)
    ax[1][1].plot(x, fpm, color=BLAU, lw=1.6, label="Polymarket")
    ax[1][1].plot(x, ffte, color=ROT, lw=1.6, label="FiveThirtyEight")
    ax[1][1].axhline(0.5, color="0.4", ls="--", lw=1)
    ax[1][1].set_title("Prognose für den Gewinner-Ausgang (Trump-Siegwahrscheinlichkeit)", fontsize=11)
    ax[1][1].set_xlabel("Handelstag", fontsize=9); ax[1][1].legend(fontsize=8.5, frameon=False)
    for a in ax.flatten():
        for s in ("top", "right"): a.spines[s].set_visible(False)
        a.tick_params(labelsize=8.5)
    fig.suptitle("H1: Prognosequalität Polymarket gegen umfragebasierte Vergleichsmassstäbe (nationale Tagesreihe)",
                 fontsize=13, fontweight="bold")
    foot(fig, "Polymarket an 194 von 194 gemeinsamen Tagen mit tieferem Verlust als FiveThirtyEight; mittlerer Verlustvorteil 0.102. "
              "Wiederholte Prognosen für einen aufgelösten Markt. Quelle: h1_brier_scores.csv.")
    fig.tight_layout(rect=[0, 0.035, 1, 0.95]); fig.savefig("/tmp/abb1.png", facecolor="white"); print("Abb1 ok")
except Exception as e:
    print("SKIP Abb1:", e)

# ---------------- Abb 3 ----------------
try:
    pw = rd("h1_calibration_diagnostic_pairwise.csv")
    sm = rd("h1_calibration_diagnostic_summary.csv")
    LBL = {"Rieke poll-model forecast": "PM vs «Rieke»", "270toWin/JHK forecast": "PM vs 270/JHK"}
    def plbl(r):
        c = r["comparator_label"]
        if "Rieke" in c: return "PM vs Rieke"
        if "270" in c and "exact" in r["comparison_id"]: return "PM vs 270 exact"
        if "270" in c: return "PM vs 270/JHK"
        if "transform" in c.lower() or "poll" in c.lower(): return "PM vs Poll-Transform"
        return "PM vs 538 final"
    pw_sorted = sorted(pw, key=lambda r: float(r["mean_loss_advantage"]))
    fig, ax = plt.subplots(1, 3, figsize=(14, 4.75), dpi=200)
    y = np.arange(len(pw_sorted))
    adv = [float(r["mean_loss_advantage"]) for r in pw_sorted]
    ax[0].barh(y, adv, color=BLAU, height=0.6)
    ax[0].set_yticks(y, [plbl(r) for r in pw_sorted], fontsize=9)
    for yy, r, v in zip(y, pw_sorted, adv):
        maj = "PM-Mehrheit" if r["majority_cases_supports_polymarket"] == "True" else "keine PM-Mehrheit"
        ax[0].text(v + 0.001, yy, f"+{v:.3f} | PM {r['polymarket_lower_loss_count']}, Vgl. {r['comparator_lower_loss_count']}, unent. {r['tie_count']} | {maj}",
                   va="center", fontsize=7.4, color="0.2")
    ax[0].set_xlim(0, max(adv) * 2.6)
    ax[0].axvline(0, color="0.2", lw=1)
    ax[0].set_title("Aggregierter Brier-Vorteil je Vergleich", fontsize=10.5)
    ax[0].set_xlabel("Vergleichs-Brier minus PM-Brier", fontsize=9)
    tot = [int(r["case_count"]) for r in pw_sorted]
    pmw = [int(r["polymarket_lower_loss_count"]) for r in pw_sorted]
    cw = [int(r["comparator_lower_loss_count"]) for r in pw_sorted]
    tie = [int(r["tie_count"]) for r in pw_sorted]
    ax[1].barh(y, [p / t for p, t in zip(pmw, tot)], 0.6, color=BLAU, label="PM tiefer")
    ax[1].barh(y, [c / t for c, t in zip(cw, tot)], 0.6, left=[p / t for p, t in zip(pmw, tot)], color=ROT, label="Vergleich tiefer")
    ax[1].barh(y, [ti / t for ti, t in zip(tie, tot)], 0.6,
               left=[(p + c) / t for p, c, t in zip(pmw, cw, tot)], color=GRAU, label="unentschieden")
    ax[1].axvline(0.5, color="0.25", ls="--", lw=1)
    ax[1].set_yticks(y, ["" for _ in y]); ax[1].set_xlim(0, 1)
    ax[1].set_title("Anteil Einzelfälle mit tieferem Verlust", fontsize=10.5)
    ax[1].legend(fontsize=7.5, frameon=False, loc="lower right")
    labmap = [("Polymarket", BLAU), ("Rieke", GRUEN), ("270", ORANGE), ("538", ROT)]
    ylab, briers, eces, ns = [], [], [], []
    for r in sm:
        lbl = r["forecast_source_label"].replace("FiveThirtyEight", "538").replace(" state probability", "").replace(" forecast", "")
        ylab.append(f"{lbl} (n={r['case_count']})")
        briers.append(float(r["mean_brier_loss"])); eces.append(float(r["expected_calibration_error"])); ns.append(int(r["case_count"]))
    yy2 = np.arange(len(sm))
    ax[2].barh(yy2 + 0.2, briers, 0.38, color=BLAU, label="Mittlerer Brier")
    ax[2].barh(yy2 - 0.2, eces, 0.38, color=GRAU, label="ECE (fix gebinnt)")
    for yv, bv, ev in zip(yy2, briers, eces):
        ax[2].text(bv + 0.004, yv + 0.2, f"{bv:.3f}", va="center", fontsize=6.8)
        ax[2].text(ev + 0.004, yv - 0.2, f"{ev:.3f}", va="center", fontsize=6.8, color="0.35")
    ax[2].set_yticks(yy2, ylab, fontsize=7)
    ax[2].set_title("Mittlerer Brier und Kalibrierungsfehler je Quelle", fontsize=10.5)
    ax[2].legend(fontsize=7.5, frameon=False, loc="lower right")
    for a in ax:
        for s in ("top", "right"): a.spines[s].set_visible(False)
        a.tick_params(labelsize=8)
    fig.suptitle("H1: Prognosequalitäts-Scorecard über 192 aufgelöste Forecast-Fälle", fontsize=12.5, fontweight="bold")
    foot(fig, "Positiver Verlustvorteil heisst tieferer Polymarket-Brier. Quelle: h1_calibration_diagnostic_pairwise.csv und _summary.csv.")
    fig.tight_layout(rect=[0, 0.04, 1, 0.92]); fig.savefig("/tmp/abb3.png", facecolor="white"); print("Abb3 ok")
except Exception as e:
    print("SKIP Abb3:", e)

# ---------------- Abb 7 ----------------
try:
    rows = rd("h3_lead_time_histograms.csv")
    TL = {"tier_1_top_1pct": ("Top 1%", BLAU), "tier_2_top_5pct": ("Top 5%", GRUEN),
          "tier_3_top_10pct": ("Top 10%", ORANGE), "tier_4_observed_baseline": ("Basis", GRAU)}
    fig, ax = plt.subplots(figsize=(12, 7.2), dpi=200)
    for tier, (lbl, col) in TL.items():
        pts = sorted([(int(r["relative_day"]), float(r["total_amount_usd"]) / 1e6)
                      for r in rows if r["tier"] == tier])
        ax.plot([p[0] for p in pts], [p[1] for p in pts], marker="o", ms=3.5, lw=1.6, color=col, label=lbl)
    ax.axvline(0, color=ROT, ls="--", lw=1.2)
    ax.set_xlabel("Tage relativ zum kuratierten Ereignis (0 = Ereignistag)", fontsize=10.5)
    ax.set_ylabel("Whale-Kaufvolumen (Mio. USD, Summe über 7 Ereignisse)", fontsize=10.5)
    ax.set_title("H3: Whale-Aktivität vor den kuratierten Ereignissen (deskriptiv)", fontsize=12.5, fontweight="bold", pad=12)
    ax.legend(fontsize=9.5, frameon=False, title="Wallet-Tier", title_fontsize=9.5)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=9.5)
    foot(fig, "Rein beschreibend, keine Aussage zur Wirkungsrichtung. Quelle: h3_lead_time_histograms.csv (Fenster -14 bis 0 Tage relativ zu den sieben Ereignissen).")
    fig.tight_layout(rect=[0, 0.035, 1, 1]); fig.savefig("/tmp/abb7.png", facecolor="white"); print("Abb7 ok")
except Exception as e:
    print("SKIP Abb7:", e)

# ---------------- Abb 8 ----------------
try:
    rows = rd("h3_event_wallet_anomaly_summary.csv")
    EV = [("evt_2024_05_30_trump_conviction", "Verurteilung (30.05.)"),
          ("evt_2024_06_28_biden_trump_debate", "Debatte Biden-Trump (28.06.)"),
          ("evt_2024_07_13_trump_shooting", "Attentat (13.07.)"),
          ("evt_2024_07_15_vance_vp_pick", "Vance als VP (15.07.)"),
          ("evt_2024_07_21_biden_withdrawal", "Biden-Rückzug (21.07.)"),
          ("evt_2024_08_06_walz_vp_pick", "Walz als VP (06.08.)"),
          ("evt_2024_09_11_harris_trump_debate", "Debatte Harris-Trump (11.09.)")]
    FAM = [("active_wallet_anomaly", "aktive Wallets"), ("market_move_anomaly", "Marktbewegung"),
           ("top_tier_concentration_anomaly", "Top-Tier-Konzentration"), ("wallet_tier_amount_anomaly", "Tier-Betragssumme")]
    M = np.zeros((7, 4))
    for r in rows:
        for i, (eid, _) in enumerate(EV):
            if r["event_id"] == eid:
                for j, (fam, _) in enumerate(FAM):
                    if r["anomaly_type"] == fam:
                        M[i][j] += int(r["anomaly_day_count"])
    fig, ax = plt.subplots(figsize=(12.5, 6), dpi=200)
    im = ax.imshow(M, cmap="YlOrRd", aspect="auto", vmin=0)
    ax.set_xticks(range(4), [f[1] for f in FAM], fontsize=9.5)
    ax.set_yticks(range(7), [e[1] for e in EV], fontsize=9.5)
    for i in range(7):
        for j in range(4):
            ax.text(j, i, int(M[i][j]), ha="center", va="center", fontsize=9,
                    color="white" if M[i][j] > M.max() * 0.6 else "black")
    cb = fig.colorbar(im, ax=ax); cb.set_label("auffällige Tage im Ereignisfenster", fontsize=9.5)
    ax.set_title("H3: Ereignis-Wallet-Anomalien je Familie (auffällig: robuster z ≥ 2.0 oder Perzentilrang ≥ 0.95)",
                 fontsize=12, fontweight="bold", pad=12)
    foot(fig, "Summe auffälliger Tage über die Tiers, Fenster -1 bis +3 Tage gegen Basis -30 bis -8 Tage. Quelle: h3_event_wallet_anomaly_summary.csv.")
    fig.tight_layout(rect=[0, 0.035, 1, 1]); fig.savefig("/tmp/abb8.png", facecolor="white"); print("Abb8 ok")
except Exception as e:
    print("SKIP Abb8:", e)

# ---------------- Abb 9 ----------------
try:
    rows = rd("h3_informed_trading_signature.csv")
    EVID = {"evt_2024_05_30_trump_conviction": "Verurteilung", "evt_2024_06_28_biden_trump_debate": "Debatte 1",
            "evt_2024_07_13_trump_shooting": "Attentat", "evt_2024_07_15_vance_vp_pick": "Vance",
            "evt_2024_07_21_biden_withdrawal": "Biden-Rückzug", "evt_2024_08_06_walz_vp_pick": "Walz",
            "evt_2024_09_11_harris_trump_debate": "Debatte 2"}
    rows = [r for r in rows if r["event_id"] in EVID]
    lbl = [EVID[r["event_id"]] for r in rows]
    nws = [100 * float(r["new_wallet_share"]) for r in rows]
    top1 = [100 * float(r["top1_concentration"]) for r in rows]
    vol = [float(r["total_amount_usd"]) / 1e6 for r in rows]
    x = np.arange(len(rows))
    fig, ax = plt.subplots(1, 3, figsize=(11.7, 6), dpi=200)
    for a, vals, ttl, col, fmt in ((ax[0], nws, "Anteil neuer Wallets (%)", BLAU, "{:.0f}"),
                                   (ax[1], top1, "Top-1-Konzentration (%)", ORANGE, "{:.0f}"),
                                   (ax[2], vol, "Fenster-Volumen (Mio. USD)", GRUEN, "{:.1f}")):
        a.bar(x, vals, color=col, width=0.62)
        for xi, v in zip(x, vals):
            a.text(xi, v * 1.02, fmt.format(v), ha="center", fontsize=8)
        a.set_xticks(x, lbl, rotation=45, ha="right", fontsize=8)
        a.set_title(ttl, fontsize=10.5)
        for s in ("top", "right"): a.spines[s].set_visible(False)
        a.tick_params(labelsize=8.5)
    fig.suptitle("H3: Signatur-Profil je Ereignisfenster (BUY-only, ab 10 000 USD)", fontsize=12.5, fontweight="bold")
    foot(fig, "Fenster -1 bis +3 Tage. Neu: im Fenster erstmals aktive Wallets. Quelle: h3_informed_trading_signature.csv.")
    fig.tight_layout(rect=[0, 0.03, 1, 0.92]); fig.savefig("/tmp/abb9.png", facecolor="white"); print("Abb9 ok")
except Exception as e:
    print("SKIP Abb9:", e)

# ---------------- Abb 11 ----------------
try:
    r = rd("swiss_referendum_10mio_final_case_study.csv")[0]
    off = 100 * float(r["official_yes_share"])
    poll_raw = 100 * float(r["latest_live_poll_yes_share"])
    poll_dec = 100 * float(r["latest_live_poll_yes_decided_share"])
    pm = 100 * float(r["latest_live_polymarket_yes_probability"])
    b_pm = float(r["latest_live_polymarket_binary_brier"])
    b_raw = float(r["latest_live_poll_raw_binary_brier_proxy"])
    b_dec = float(r["latest_live_poll_decided_binary_brier_proxy"])
    fig, ax = plt.subplots(1, 2, figsize=(11.4, 6), dpi=200)
    names = ["Offizielles Resultat", "Finale Umfrage (roh)", "Finale Umfrage (Entschiedene)", "Polymarket (Annahme-W'keit)"]
    vals = [off, poll_raw, poll_dec, pm]
    cols = ["0.25", GRUEN, GRUEN, BLAU]
    b = ax[0].bar(names, vals, color=cols, width=0.62)
    ax[0].axhline(50, color=ROT, ls="--", lw=1.2)
    ax[0].text(3.45, 50.8, "50%-Schwelle", fontsize=8, color=ROT, ha="right")
    for bb, v in zip(b, vals):
        ax[0].text(bb.get_x() + bb.get_width() / 2, v + 0.8, f"{v:.1f}%", ha="center", fontsize=9.5)
    ax[0].set_xticklabels(names, rotation=18, ha="right", fontsize=8)
    ax[0].set_ylabel("Ja-Anteil bzw. Annahmewahrscheinlichkeit (%)", fontsize=9.5)
    ax[0].set_title("Stimmenanteil-Sicht: Umfragen näher am Resultat", fontsize=10.5)
    names2 = ["Polymarket", "Umfrage roh (Proxy)", "Umfrage Entschiedene (Proxy)"]
    vals2 = [b_pm, b_raw, b_dec]
    b2 = ax[1].bar(names2, vals2, color=[BLAU, GRUEN, GRUEN], width=0.55)
    for bb, v in zip(b2, vals2):
        ax[1].text(bb.get_x() + bb.get_width() / 2, v + 0.004, f"{v:.3f}", ha="center", fontsize=9.5)
    ax[1].set_xticklabels(names2, rotation=12, ha="right", fontsize=8)
    ax[1].set_ylabel("Binärer Brier-Verlust (tiefer = besser)", fontsize=9.5)
    ax[1].set_title("Binäre Sicht: Polymarket klar auf der Ablehnungsseite", fontsize=10.5)
    for a in ax:
        for s in ("top", "right"): a.spines[s].set_visible(False)
        a.tick_params(labelsize=8.5)
    fig.suptitle("Schweizer Referendum vom 14.06.2026 (10-Millionen-Initiative): zwei Sichten auf denselben Fall",
                 fontsize=12, fontweight="bold")
    foot(fig, "Umfrage-Binärwerte sind nur Proxys (Stimmenanteile, keine Gewinnwahrscheinlichkeiten). "
              "Quelle: swiss_referendum_10mio_final_case_study.csv (SRG/gfs.bern-Schlussumfrage).")
    fig.tight_layout(rect=[0, 0.04, 1, 0.92]); fig.savefig("/tmp/abb11.png", facecolor="white"); print("Abb11 ok")
except Exception as e:
    print("SKIP Abb11:", e)

# ---------------- Abb 12 ----------------
try:
    rows = rd("h1_state_poll_panel_horizon_summary.csv")
    print("Abb12 Spalten:", list(rows[0].keys()))
    def pick(r, *cands):
        for c in cands:
            if c in r: return r[c]
        return None
    labs, shares, nums, dens, advs = [], [], [], [], []
    for r in rows:
        lab = pick(r, "horizon_bin", "bin_label", "horizon_bucket", "bucket")
        num = pick(r, "polymarket_lower_loss_count", "pm_lower_count", "polymarket_lower_count")
        den = pick(r, "row_count", "case_count", "total_rows", "n_rows")
        adv = pick(r, "mean_loss_advantage", "mean_advantage")
        if lab is None or num is None or den is None: continue
        labs.append(str(lab)); nums.append(int(float(num))); dens.append(int(float(den)))
        advs.append(float(adv) if adv is not None else float("nan"))
    y = np.arange(len(labs))[::-1]
    fig, ax = plt.subplots(1, 2, figsize=(12.8, 8), dpi=200)
    sh = [100 * n / d for n, d in zip(nums, dens)]
    ax[0].barh(y, sh, color=[BLAU if s >= 50 else "#8B5CF6" for s in sh], height=0.6)
    ax[0].axvline(50, color="0.25", ls="--", lw=1.2)
    ax[0].set_yticks(y, labs, fontsize=9)
    for yy, s, n, d in zip(y, sh, nums, dens):
        ax[0].text(max(s + 1.5, 3), yy, f"{n}/{d}", va="center", fontsize=8.5)
    ax[0].set_xlabel("Anteil Zeilen mit tieferem Polymarket-Brier (%)", fontsize=9.5)
    ax[0].set_title("Lower-Loss-Anteil je Prognosehorizont-Bin", fontsize=10.5)
    ax[1].barh(y, advs, color=[BLAU if a >= 0 else "#8B5CF6" for a in advs], height=0.6)
    ax[1].axvline(0, color="0.2", lw=1)
    ax[1].set_yticks(y, ["" for _ in y])
    ax[1].set_xlabel("Mittlerer Verlustvorteil (Poll-Brier minus PM-Brier)", fontsize=9.5)
    ax[1].set_title("Mittlere Verlustdifferenz je Bin", fontsize=10.5)
    for a in ax:
        for s in ("top", "right"): a.spines[s].set_visible(False)
        a.tick_params(labelsize=8.5)
    fig.suptitle("H1-Robustheit nach Prognosehorizont: der Vorteil hängt am Fenster bis 90 Tage",
                 fontsize=12.5, fontweight="bold")
    foot(fig, "Blau: stützt Polymarket, violett: Gegenrichtung. Quelle: h1_state_poll_panel_horizon_summary.csv.")
    fig.tight_layout(rect=[0, 0.03, 1, 0.93]); fig.savefig("/tmp/abb12.png", facecolor="white"); print("Abb12 ok")
except Exception as e:
    print("SKIP Abb12:", e)

# ---------------- Abb 13 ----------------
try:
    rows = rd("h1_direct_poll_outlier_robustness_scenarios.csv")
    full = [r for r in rows if r["scenario_type"] == "full"][0]
    full_adv = float(full["mean_loss_advantage"])
    loso = [r for r in rows if r["scenario_type"] == "leave_one_state_out"]
    other = {}
    for r in rows:
        if r["scenario_type"] not in ("full", "leave_one_state_out"):
            other.setdefault(r["scenario_type"], []).append(r)
    loso_sorted = sorted(loso, key=lambda r: float(r["mean_loss_advantage"]))
    contrib = [(r["removed_states"], full_adv - float(r["mean_loss_advantage"])) for r in loso_sorted]
    fig, ax = plt.subplots(1, 2, figsize=(13, 8), dpi=200)
    vals = [float(r["mean_loss_advantage"]) for r in loso_sorted]
    y = np.arange(len(loso_sorted))
    ax[0].barh(y, vals, color=BLAU, height=0.65)
    ax[0].axvline(full_adv, color=ROT, ls="--", lw=1.2)
    ax[0].axvline(0, color="0.2", lw=1)
    ax[0].set_yticks(y, [r["removed_states"] for r in loso_sorted], fontsize=6.2)
    ax[0].set_xlabel("Mittlerer Verlustvorteil ohne diesen Staat", fontsize=9.5)
    ax[0].set_title(f"Leave-one-state-out (rote Linie: alle Staaten, {full_adv:.4f})", fontsize=10.5)
    top = sorted(contrib, key=lambda c: -c[1])[:12]
    y2 = np.arange(len(top))[::-1]
    ax[1].barh(y2, [c[1] for c in top], color=ORANGE, height=0.6)
    ax[1].axvline(0, color="0.2", lw=1)
    ax[1].set_yticks(y2, [c[0] for c in top], fontsize=8.5)
    ax[1].set_xlabel("Beitrag zum Gesamtvorteil (Differenz bei Entfernen)", fontsize=9.5)
    ax[1].set_title("Grösste Einzelbeiträge je Bundesstaat (Top 12)", fontsize=10.5)
    for a in ax:
        for s in ("top", "right"): a.spines[s].set_visible(False)
        a.tick_params(labelsize=8)
    fig.suptitle("H1-Robustheit gegenüber Ausreissern: kein einzelner Staat trägt den Vorteil allein",
                 fontsize=12.5, fontweight="bold")
    foot(fig, "Gleicher Wahlkontext 2024, keine unabhängigen Stichproben. Quelle: h1_direct_poll_outlier_robustness_scenarios.csv.")
    fig.tight_layout(rect=[0, 0.03, 1, 0.93]); fig.savefig("/tmp/abb13.png", facecolor="white"); print("Abb13 ok")
except Exception as e:
    print("SKIP Abb13:", e)
