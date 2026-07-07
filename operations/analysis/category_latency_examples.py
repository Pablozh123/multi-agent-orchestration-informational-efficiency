"""Einpreisungs-Geschwindigkeit je Kategorie an kuratierten Beispielen.

Zweck
-----
Misst fuer drei kuratierte Informationsereignisse (Krypto: Bitcoin
ueberschreitet erstmals 100000 USD; Sport: Super Bowl LX; Popkultur:
Oscars 2026 Best Picture), wie schnell der jeweils passende aufgeloeste
Polymarket-Markt reagierte und zum korrekten Outcome konvergierte, und
stellt die Werte den bestehenden Vergleichsgroessen fuer Politik
(Tabelle A1 der Thesis) und Mentions (Median der Status-ok-Zeilen aus
data/results/mentions_latency.csv) gegenueber. Rein deskriptive
Auswertung: keine Handels-, Strategie- oder Kausalaussagen.

Dieses Skript rechnet AUSSCHLIESSLICH aus gespeicherten Dateien
(kein Netzzugriff):
  - data/events/category_latency_seed.csv        (kuratierte Ereignisse)
  - data/raw/category_latency/<rohdatei>         (CLOB-Preisreihen)
  - data/results/mentions_latency.csv            (Status-ok-Zeilen)
  - data/results/category_efficiency_summary_v2.csv (Brier T-7, Abbildung)

Methode (identisch zu operations/analysis/mentions_latency.py)
--------------------------------------------------------------
- Preisreihen: CLOB /prices-history mit fidelity=10 (10-Minuten-Punkte),
  Fenster von 2 h vor t0 bis 72 h nach t0, YES-Token des korrekt
  aufgeloesten Markts (Abruf dokumentiert in den meta-Bloecken der
  Rohdateien, Abrufdatum 03.07.2026).
- Baseline: Medianpreis der 60 Minuten vor t0.
- Erste Reaktion: erster Zeitpunkt t >= t0, an dem der Preis mehr als
  1 Prozentpunkt von der Baseline abweicht.
- Konvergenz: erster Zeitpunkt, ab dem der Preis dauerhaft (bis zum Ende
  der Reihe) auf der richtigen Seite von 0.9 (YES) bzw. 0.1 (NO) bleibt.
Die Kennzahlen-Funktionen sind WORTGLEICH aus mentions_latency.py
uebernommen (dort ausfuehrlich dokumentiert); Kopie statt Import, damit
dieses Skript unabhaengig lauffaehig ist. Unterschied zur
Mentions-Auswertung: fidelity=10 statt 1, d. h. Reaktions- und
Konvergenzzeiten sind hier auf dem 10-Minuten-Raster beobachtete
Obergrenzen.

Vergleichswerte ohne Neuberechnung
----------------------------------
- Politik: Tabelle A1 der Thesis (US-Wahlmarkt 2024, Ereignisfenster):
  erste Reaktion im Minutenbereich, anhaltende Preisniveaus binnen ca.
  26 bis 94 Minuten bei den reagierenden Ereignissen. Fuer die Abbildung
  wird die Spannenmitte 60 Minuten angesetzt (dokumentierte Konvention).
  Quelle: thesis_tabelle_a1.
- Mentions: Median der Status-ok-Zeilen aus mentions_latency.csv
  (fidelity=1, Drop = Beginn der Uebertragung; n wird dynamisch aus der
  Datei bestimmt).

Interpretations-Hinweise (siehe Spalte praezisions_hinweis)
-----------------------------------------------------------
- Krypto: Der Markt loest ueber das Coinbase-1-Minuten-High auf; die
  Referenzboerse kreuzte 100000 USD ca. 50 Minuten vor dem
  Binance-basierten t0 der Aufgabenstellung. Der Preis stand bei t0
  bereits ueber 0.99; die Konvergenz liegt damit VOR t0 (negativer Wert).
  Die Abbildung setzt dafuer die Untergrenze 1 Minute
  ('vor Ereignis eingepreist').
- Sport und Popkultur: t0 ist Kickoff bzw. Zeremonie-Beginn (die einzig
  belegbaren Zeitpunkte); die Konvergenzzeit enthaelt deshalb die Spiel-
  bzw. Zeremoniedauer bis zur Entscheidung.

Ausgaben
--------
- data/results/category_latency_examples.csv (Kategorie, Ereignis,
  Markt-Frage, t0, Minuten bis erste Reaktion, Minuten bis Konvergenz,
  Praezisions-Hinweis)
- data/results/category_speed_quality_de.png (deutsch, ss statt scharfem
  S, keine Gedankenstriche): Brier T-7 (x) gegen Median-Minuten bis
  Konvergenz (y, logarithmisch), ein Punkt je Kategorie.

Aufruf: python -m operations.analysis.category_latency_examples
"""

from __future__ import annotations

import csv
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = REPO_ROOT / "data" / "events" / "category_latency_seed.csv"
RAW_DIR = REPO_ROOT / "data" / "raw" / "category_latency"
RESULTS_DIR = REPO_ROOT / "data" / "results"
MENTIONS_CSV = RESULTS_DIR / "mentions_latency.csv"
SUMMARY_V2_CSV = RESULTS_DIR / "category_efficiency_summary_v2.csv"

DATENSTAND = "03.07.2026"

# Vergleichswert Politik aus Tabelle A1 der Thesis (keine Neuberechnung).
POLITIK_A1 = {
    "spanne_minuten": (26, 94),
    "median_minuten": 60.0,  # Spannenmitte, dokumentierte Konvention
    "quelle": "thesis_tabelle_a1",
}

# Anzeigenamen (identisch zur kategorie-Spalte in summary_v2)
KATEGORIE_DE = {
    "crypto": "Krypto",
    "sports": "Sport",
    "pop-culture": "Popkultur",
    "politics": "Politik",
    "mentions": "Mentions",
}

EREIGNIS_DE = {
    "btc_100k_first_cross": "Bitcoin ueberschreitet erstmals 100000 USD (05.12.2024)",
    "superbowl_lx": "Super Bowl LX, Sieg Seattle Seahawks (08.02.2026, t0 = Kickoff)",
    "oscars2026_best_picture": (
        "Oscars 2026, Best Picture fuer One Battle After Another "
        "(15.03.2026, t0 = Zeremonie-Beginn)"
    ),
}

# ---------------------------------------------------------------- Kennzahlen
# Wortgleich uebernommen aus operations/analysis/mentions_latency.py
# (identische Methode; dort dokumentiert). Nicht veraendern.

BASELINE_FENSTER_S = 3600
REAKTIONS_SCHWELLE = 0.01
KONVERGENZ_BAND = 0.9

Punkt = tuple[int, float]  # (Epoch-Sekunden UTC, Preis des YES-Tokens)


def baseline_median(
    punkte: list[Punkt], drop_epoch: int, fenster_s: int = BASELINE_FENSTER_S
) -> float | None:
    """Medianpreis im Fenster [drop - fenster_s, drop). None ohne Punkte."""
    preise = [p for t, p in punkte if drop_epoch - fenster_s <= t < drop_epoch]
    if not preise:
        return None
    return float(statistics.median(preise))


def erste_reaktion_epoch(
    punkte: list[Punkt],
    drop_epoch: int,
    baseline: float,
    schwelle: float = REAKTIONS_SCHWELLE,
) -> int | None:
    """Erster Zeitpunkt t >= drop mit |Preis - Baseline| > schwelle.

    Kleine Gleitkomma-Toleranz, damit eine Abweichung von exakt einem
    Prozentpunkt nicht faelschlich als Ueberschreitung zaehlt.
    """
    for t, p in punkte:
        if t >= drop_epoch and abs(p - baseline) - schwelle > 1e-9:
            return t
    return None


def konvergenz_epoch(
    punkte: list[Punkt], outcome_yes: bool, band: float = KONVERGENZ_BAND
) -> int | None:
    """Beginn des laengsten End-Suffixes, in dem jeder Preis auf der
    richtigen Seite liegt (>= band bei YES, <= 1 - band bei NO).

    None, wenn schon der letzte Punkt auf der falschen Seite liegt oder
    die Reihe leer ist.
    """
    if not punkte:
        return None

    def korrekt(p: float) -> bool:
        return p >= band if outcome_yes else p <= 1.0 - band

    start: int | None = None
    for t, p in reversed(punkte):
        if korrekt(p):
            start = t
        else:
            break
    return start


def minuten_nach_drop(epoch: int, drop_epoch: int) -> float:
    """Minuten zwischen Drop und Zeitpunkt (negativ = vor dem Drop)."""
    return round((epoch - drop_epoch) / 60.0, 1)


def stunden_im_band(
    punkte: list[Punkt],
    drop_epoch: int,
    unteres: float = 1.0 - KONVERGENZ_BAND,
    oberes: float = KONVERGENZ_BAND,
) -> float:
    """Stunden nach dem Drop, in denen der Preis strikt zwischen den
    Bandgrenzen lag (Standard: zwischen 0.1 und 0.9).

    Summiert die Dauer zwischen aufeinanderfolgenden Beobachtungen, deren
    linker Punkt im Band liegt und bei/nach dem Drop beobachtet wurde.
    Rein deskriptive Fenstergroesse auf Beobachtungsraster-Ebene.
    """
    punkte = sorted(punkte)
    sekunden = 0
    for (t0, p0), (t1, _) in zip(punkte, punkte[1:]):
        # Epsilon gegen Gleitkomma-Artefakte an den Bandgrenzen
        if t0 >= drop_epoch and p0 - unteres > 1e-9 and oberes - p0 > 1e-9:
            sekunden += t1 - t0
    return round(sekunden / 3600.0, 2)


def bewerte_markt(punkte: list[Punkt], drop_epoch: int, outcome_yes: bool) -> dict:
    """Berechnet alle Kennzahlen fuer eine Preisreihe (deterministisch)."""
    punkte = sorted(punkte)
    baseline = baseline_median(punkte, drop_epoch)
    n_baseline = len(
        [1 for t, _ in punkte if drop_epoch - BASELINE_FENSTER_S <= t < drop_epoch]
    )

    reaktion = None
    if baseline is not None:
        reaktion = erste_reaktion_epoch(punkte, drop_epoch, baseline)
    konvergenz = konvergenz_epoch(punkte, outcome_yes)

    status_teile: list[str] = []
    if baseline is None:
        status_teile.append("keine_baseline")
    elif reaktion is None:
        status_teile.append("keine_reaktion_im_fenster")
    if konvergenz is None:
        status_teile.append("keine_konvergenz_im_fenster")
    elif konvergenz <= drop_epoch:
        status_teile.append("bereits_vor_drop_konvergiert")
    status = ";".join(status_teile) if status_teile else "ok"

    return {
        "n_punkte": len(punkte),
        "n_punkte_baseline": n_baseline,
        "baseline_preis": round(baseline, 4) if baseline is not None else None,
        "erste_reaktion_epoch": reaktion,
        "minuten_bis_erste_reaktion": (
            minuten_nach_drop(reaktion, drop_epoch) if reaktion is not None else None
        ),
        "konvergenz_epoch": konvergenz,
        "minuten_bis_konvergenz": (
            minuten_nach_drop(konvergenz, drop_epoch) if konvergenz is not None else None
        ),
        "stunden_im_handelbaren_fenster": stunden_im_band(punkte, drop_epoch),
        "endpreis": round(punkte[-1][1], 4) if punkte else None,
        "status": status,
    }


def parse_ts_utc(wert: str) -> int:
    """ISO-8601-Zeitstempel (Z oder +00:00) -> Epoch-Sekunden UTC."""
    dt = datetime.fromisoformat(wert.strip().replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError(f"Zeitstempel ohne Zeitzone: {wert!r}")
    return int(dt.astimezone(timezone.utc).timestamp())


# ------------------------------------------------------------------- Eingaben


def lese_seed() -> list[dict]:
    if not SEED_PATH.exists():
        raise FileNotFoundError(
            f"Seed-Datei fehlt: {SEED_PATH}. Events muessen vor der Analyse "
            "kuratiert werden (Zeitstempel + Quelle)."
        )
    with open(SEED_PATH, encoding="utf-8") as f:
        zeilen = list(csv.DictReader(f))
    if not zeilen:
        raise ValueError(f"Seed-Datei ist leer: {SEED_PATH}")
    return zeilen


def lade_punkte(rohdatei: str) -> list[Punkt]:
    with open(RAW_DIR / rohdatei, encoding="utf-8") as f:
        daten = json.load(f)
    return sorted((int(h["t"]), float(h["p"])) for h in daten["history"])


def mentions_mediane() -> tuple[float, float, int]:
    """(Median Konvergenz, Median erste Reaktion, n) der Status-ok-Zeilen."""
    with open(MENTIONS_CSV, encoding="utf-8") as f:
        zeilen = [z for z in csv.DictReader(f) if (z.get("status") or "") == "ok"]
    konv = [float(z["minuten_bis_konvergenz"]) for z in zeilen]
    reakt = [float(z["minuten_bis_erste_reaktion"]) for z in zeilen]
    return (
        round(statistics.median(konv), 1),
        round(statistics.median(reakt), 1),
        len(zeilen),
    )


def lese_summary_v2() -> dict[str, dict]:
    with open(SUMMARY_V2_CSV, encoding="utf-8") as f:
        return {z["kategorie"]: z for z in csv.DictReader(f)}


# ------------------------------------------------------------------- Pipeline


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    seed = lese_seed()

    rows: list[dict] = []

    # ------------------------------------------ kuratierte neue Beispiele
    for z in seed:
        punkte = lade_punkte(z["rohdatei"])
        drop_epoch = parse_ts_utc(z["drop_ts_utc"])
        outcome_yes = z["korrekt_aufgeloestes_outcome"].strip().upper() == "YES"
        kz = bewerte_markt(punkte, drop_epoch, outcome_yes)

        hinweis_teile = [z.get("hinweis", "").strip()]
        hinweis_teile.append(
            f"fidelity=10 (10-Minuten-Raster); Baseline {kz['baseline_preis']}; "
            f"Status {kz['status']}."
        )
        if kz["minuten_bis_konvergenz"] is not None and kz["minuten_bis_konvergenz"] <= 0:
            hinweis_teile.append(
                "Konvergenz lag vor t0 (Markt bereits eingepreist); Abbildung "
                "nutzt Untergrenze 1 Minute."
            )

        rows.append(
            {
                "kategorie": KATEGORIE_DE[z["kategorie"]],
                "ereignis": EREIGNIS_DE.get(z["event"], z["event"]),
                "markt_frage": z["markt_frage"],
                "t0_utc": z["drop_ts_utc"],
                "minuten_bis_erste_reaktion": kz["minuten_bis_erste_reaktion"],
                "minuten_bis_konvergenz": kz["minuten_bis_konvergenz"],
                "praezisions_hinweis": " ".join(t for t in hinweis_teile if t),
            }
        )

    # ------------------------------------------ Politik (Tabelle A1, fix)
    lo, hi = POLITIK_A1["spanne_minuten"]
    rows.append(
        {
            "kategorie": "Politik",
            "ereignis": "US-Wahlmarkt 2024, Ereignisfenster (Tabelle A1 der Thesis)",
            "markt_frage": "diverse Wahlmaerkte (siehe Tabelle A1)",
            "t0_utc": "",
            "minuten_bis_erste_reaktion": "",
            "minuten_bis_konvergenz": POLITIK_A1["median_minuten"],
            "praezisions_hinweis": (
                "Vergleichswert OHNE Neuberechnung: erste Reaktion im "
                f"Minutenbereich, anhaltende Preisniveaus binnen ca. {lo} bis "
                f"{hi} Minuten bei den reagierenden Ereignissen; "
                f"{POLITIK_A1['median_minuten']:.0f} Min. = Spannenmitte "
                f"(Konvention). Quelle: {POLITIK_A1['quelle']}."
            ),
        }
    )

    # ------------------------------------------ Mentions (Median, fix)
    m_konv, m_reakt, m_n = mentions_mediane()
    rows.append(
        {
            "kategorie": "Mentions",
            "ereignis": f"Median aus {m_n} kuratierten Mentions-Ereignissen",
            "markt_frage": f"{m_n} Maerkte, siehe data/results/mentions_latency.csv",
            "t0_utc": "",
            "minuten_bis_erste_reaktion": m_reakt,
            "minuten_bis_konvergenz": m_konv,
            "praezisions_hinweis": (
                "Median der Status-ok-Zeilen aus mentions_latency.csv "
                "(fidelity=1; Drop = Beginn der Uebertragung, Latenz enthaelt "
                "die Zeit bis zur aufloesungsrelevanten Aussage)."
            ),
        }
    )

    csv_pfad = RESULTS_DIR / "category_latency_examples.csv"
    with open(csv_pfad, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow({k: ("" if v is None else v) for k, v in r.items()})

    for r in rows:
        print(
            f"{r['kategorie']:10s} Reaktion {str(r['minuten_bis_erste_reaktion']):>8s} "
            f"Min., Konvergenz {str(r['minuten_bis_konvergenz']):>8s} Min."
        )
    print(f"\nGeschrieben: {csv_pfad}")

    # ------------------------------------------------------------ Abbildung
    v2 = lese_summary_v2()
    speed_label = {
        "Krypto": "1 Ereignis",
        "Sport": "1 Ereignis",
        "Popkultur": "1 Ereignis",
        "Politik": "Tabelle A1",
        "Mentions": f"{m_n} Märkte",
    }
    # Label-Platzierung je Kategorie (Offsets in Punkten), gegen Ueberlappung
    label_pos = {
        "Sport": {"xytext": (0, -36), "ha": "center"},
        "Popkultur": {"xytext": (-4, 14), "ha": "center"},
        "Mentions": {"xytext": (14, -4), "ha": "left"},
        "Krypto": {"xytext": (14, -4), "ha": "left"},
        "Politik": {"xytext": (0, 14), "ha": "center"},
    }

    fig, ax = plt.subplots(figsize=(10.0, 6.4), dpi=150)
    y_min_floor = 1.0

    for r in rows:
        kat = r["kategorie"]
        brier = float(v2[kat]["brier_t7"])
        n_t7 = v2[kat]["n_t7"]
        konv = r["minuten_bis_konvergenz"]
        vor_ereignis = konv is not None and konv != "" and float(konv) <= 0
        y = y_min_floor if vor_ereignis else float(konv)
        ax.scatter(
            [brier], [y], s=170, color="#4878a8", zorder=3,
            edgecolor="white", linewidth=1.2,
        )
        label = f"{kat}\n(Brier n={n_t7}; Speed: {speed_label[kat]})"
        if vor_ereignis:
            label += "\nvor Ereignis eingepreist\n(Untergrenze 1 Min.)"
        pos = label_pos[kat]
        ax.annotate(
            label,
            (brier, y),
            textcoords="offset points",
            xytext=pos["xytext"],
            ha=pos["ha"],
            fontsize=9,
            color="#2b4a66",
        )

    ax.set_yscale("log")
    ax.set_ylim(0.5, 2000)
    ax.set_xlim(-0.02, 0.44)
    ax.set_xlabel(
        "Mittlerer Brier-Score T-7 (Vorhersagegüte, tiefer = besser)", fontsize=11
    )
    ax.set_ylabel("Median-Minuten bis Konvergenz (logarithmische Skala)", fontsize=11)
    fig.suptitle(
        "Vorhersagegüte und Einpreisungs-Geschwindigkeit je Polymarket-Kategorie",
        y=0.98,
        fontsize=13,
        fontweight="bold",
    )
    fig.text(
        0.5,
        0.945,
        "Datenstand 03.07.2026. x: mittlerer Brier-Score sieben Tage vor Auflösung (v2-Stichprobe; n in Klammern).\n"
        "y: Median-Minuten bis Konvergenz nach Informationsereignis (Preis dauerhaft auf der richtigen Seite von 0,9 bzw. 0,1).\n"
        f"Die Speed-Werte beruhen auf wenigen kuratierten Beispielen: Krypto, Sport und Popkultur je 1 Ereignis; Mentions Median aus {m_n} Märkten;\n"
        "Politik Vergleichswert aus Tabelle A1 der Thesis. Rein deskriptive Auswertung.",
        ha="center",
        va="top",
        fontsize=8.2,
        color="#666666",
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, linestyle=":", alpha=0.45)
    ax.set_axisbelow(True)

    fig.tight_layout(rect=(0, 0, 1, 0.83))
    png_pfad = RESULTS_DIR / "category_speed_quality_de.png"
    fig.savefig(png_pfad)
    plt.close(fig)
    print(f"Geschrieben: {png_pfad}")


if __name__ == "__main__":
    main()
