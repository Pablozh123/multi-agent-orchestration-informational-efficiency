"""Einpreisungs-Latenz von Mentions-Maerkten nach Content-Drop (deskriptiv).

Zweck
-----
Misst je kuratiertem Polymarket-Mentions-Markt, wie schnell der Marktpreis
nach dem Content-Drop (Beginn der Rede, des Interviews, des Earnings Calls
oder der Uebertragung) reagiert und zum korrekt aufgeloesten Outcome
konvergiert. Rein deskriptive Auswertung: keine Handels-, Strategie- oder
Profitabilitaetsaussagen.

Input
-----
data/events/mentions_latency_seed.csv mit den Pflichtspalten:
  event, drop_ts_utc, condition_id, clob_token_id,
  korrekt_aufgeloestes_outcome
Optionale Spalten:
  aufloesung_ts_utc (Ende des Abruffensters; sonst drop + 7 Tage),
  quelle_url, hinweis (Dokumentation der Event-Kuration).

`clob_token_id` ist der YES-Outcome-Token des Markts.
`korrekt_aufgeloestes_outcome` ist YES oder NO (Gewinnerseite des Markts).

Datenquelle
-----------
CLOB-API /prices-history mit fidelity=1 (Minutenaufloesung), Fenster von
60 Minuten vor Drop (Baseline) bis zur Aufloesung. Rohantworten werden
unter data/raw/mentions_latency/ gecacht; ohne --refresh rechnet das
Skript ausschliesslich aus dem Cache (reproduzierbar, kein Netzzugriff).

Kennzahlen je Markt
-------------------
- Baseline: Medianpreis der 60 Minuten vor dem Drop.
- Erste Reaktion: erster Zeitpunkt t >= drop, an dem der Preis mehr als
  1 Prozentpunkt (> 0.01) von der Baseline abweicht.
- Konvergenz: erster Zeitpunkt, ab dem der Preis dauerhaft (bis zum Ende
  der Reihe) auf der richtigen Seite von 0.9 (Outcome YES) bzw. 0.1
  (Outcome NO) bleibt.
- Stunden im handelbaren Fenster: Zeit nach dem Drop, in der der Preis
  strikt zwischen 0.1 und 0.9 lag (deskriptive Fenstergroesse, keine
  Handels- oder Profitabilitaetsaussage).

Ausgaben
--------
- data/results/mentions_latency.csv (eine Zeile je Markt)
- data/results/mentions_latency_metadata.json
- data/results/mentions_latency_de.png (deutsche Beschriftung,
  ss statt scharfem S, keine Gedankenstriche)

Aufruf: python -m operations.analysis.mentions_latency [--refresh]
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = REPO_ROOT / "data" / "events" / "mentions_latency_seed.csv"
RAW_DIR = REPO_ROOT / "data" / "raw" / "mentions_latency"
RESULTS_DIR = REPO_ROOT / "data" / "results"

CLOB_URL = "https://clob.polymarket.com/prices-history"
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

BASELINE_FENSTER_S = 3600
REAKTIONS_SCHWELLE = 0.01
KONVERGENZ_BAND = 0.9
STANDARD_HORIZONT_S = 7 * 86400
PFLICHTSPALTEN = [
    "event",
    "drop_ts_utc",
    "condition_id",
    "clob_token_id",
    "korrekt_aufgeloestes_outcome",
]

Punkt = tuple[int, float]  # (Epoch-Sekunden UTC, Preis des YES-Tokens)


# ------------------------------------------------------------ Kennzahlen


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


# ------------------------------------------------------------ Seed und Abruf


def parse_ts_utc(wert: str) -> int:
    """ISO-8601-Zeitstempel (Z oder +00:00) -> Epoch-Sekunden UTC."""
    dt = datetime.fromisoformat(wert.strip().replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError(f"Zeitstempel ohne Zeitzone: {wert!r}")
    return int(dt.astimezone(timezone.utc).timestamp())


def lese_seed(pfad: Path = SEED_PATH) -> list[dict]:
    """Liest und validiert die kuratierte Seed-Datei."""
    if not pfad.exists():
        raise FileNotFoundError(
            f"Seed-Datei fehlt: {pfad}. Events muessen vor der Analyse "
            "kuratiert werden (Zeitstempel + Quelle)."
        )
    with open(pfad, encoding="utf-8") as f:
        zeilen = list(csv.DictReader(f))
    if not zeilen:
        raise ValueError(f"Seed-Datei ist leer: {pfad}")
    fehlend = [s for s in PFLICHTSPALTEN if s not in zeilen[0]]
    if fehlend:
        raise ValueError(f"Seed-Datei ohne Pflichtspalten: {fehlend}")
    for z in zeilen:
        outcome = z["korrekt_aufgeloestes_outcome"].strip().upper()
        if outcome not in ("YES", "NO"):
            raise ValueError(
                f"Ungueltiges Outcome {z['korrekt_aufgeloestes_outcome']!r} "
                f"fuer Event {z['event']!r} (erwartet YES oder NO)."
            )
        z["korrekt_aufgeloestes_outcome"] = outcome
    return zeilen


def _fetch_prices_history(token_id: str, start: int, ende: int) -> dict:
    """Live-Abruf der CLOB-Preishistorie (fidelity=1) mit Retry."""
    import httpx
    from tenacity import retry, stop_after_attempt, wait_random_exponential

    @retry(stop=stop_after_attempt(3), wait=wait_random_exponential(1, 10), reraise=True)
    def _abruf() -> dict:
        resp = httpx.get(
            CLOB_URL,
            params={"market": token_id, "startTs": start, "endTs": ende, "fidelity": 1},
            headers=HTTP_HEADERS,
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()

    return _abruf()


def lade_preisreihe(
    event: str,
    token_id: str,
    start: int,
    ende: int,
    refresh: bool = False,
    fetch: Callable[[str, int, int], dict] | None = None,
) -> list[Punkt]:
    """Laedt die Preisreihe aus dem Cache oder (bei Bedarf) live und cacht sie."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cache = RAW_DIR / f"prices_{event}.json"
    if cache.exists() and not refresh:
        with open(cache, encoding="utf-8") as f:
            daten = json.load(f)
    else:
        fetch = fetch or _fetch_prices_history
        antwort = fetch(token_id, start, ende)
        daten = {
            "meta": {
                "quelle_url": CLOB_URL,
                "parameter": {
                    "market": token_id,
                    "startTs": start,
                    "endTs": ende,
                    "fidelity": 1,
                },
                "abgerufen_am_utc": datetime.now(timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
            },
            "history": antwort.get("history", []),
        }
        with open(cache, "w", encoding="utf-8") as f:
            json.dump(daten, f, ensure_ascii=False)
    return sorted((int(h["t"]), float(h["p"])) for h in daten["history"])


# ------------------------------------------------------------ Pipeline


def berechne_ergebnisse(
    seed: list[dict], refresh: bool = False, fetch: Callable | None = None
) -> list[dict]:
    """Berechnet die Latenz-Kennzahlen fuer alle Seed-Maerkte."""
    ergebnisse = []
    for z in seed:
        drop_epoch = parse_ts_utc(z["drop_ts_utc"])
        ende = (
            parse_ts_utc(z["aufloesung_ts_utc"])
            if z.get("aufloesung_ts_utc", "").strip()
            else drop_epoch + STANDARD_HORIZONT_S
        )
        punkte = lade_preisreihe(
            z["event"],
            z["clob_token_id"],
            drop_epoch - BASELINE_FENSTER_S - 1800,
            ende,
            refresh=refresh,
            fetch=fetch,
        )
        outcome_yes = z["korrekt_aufgeloestes_outcome"] == "YES"
        kennzahlen = bewerte_markt(punkte, drop_epoch, outcome_yes)
        ergebnisse.append(
            {
                "event": z["event"],
                "condition_id": z["condition_id"],
                "clob_token_id": z["clob_token_id"],
                "drop_ts_utc": z["drop_ts_utc"],
                "korrekt_aufgeloestes_outcome": z["korrekt_aufgeloestes_outcome"],
                **kennzahlen,
            }
        )
    return ergebnisse


def schreibe_csv(ergebnisse: list[dict], pfad: Path) -> None:
    with open(pfad, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(ergebnisse[0].keys()))
        writer.writeheader()
        for r in ergebnisse:
            writer.writerow({k: ("" if v is None else v) for k, v in r.items()})


def schreibe_metadata(ergebnisse: list[dict], seed: list[dict], pfad: Path) -> None:
    meta = {
        "beschreibung": (
            "Einpreisungs-Latenz kuratierter Polymarket-Mentions-Maerkte nach "
            "Content-Drop. Baseline = Medianpreis 60 Minuten vor Drop; erste "
            "Reaktion = erstes Ueberschreiten von 1 Prozentpunkt Abweichung von "
            "der Baseline; Konvergenz = erster Zeitpunkt, ab dem der Preis "
            "dauerhaft auf der richtigen Seite von 0.9 (YES) bzw. 0.1 (NO) "
            "bleibt; Stunden im handelbaren Fenster = Zeit nach Drop mit Preis "
            "strikt zwischen 0.1 und 0.9 (deskriptive Fenstergroesse, keine "
            "Handels- oder Profitabilitaetsaussage)."
        ),
        "datenquelle": (
            "Polymarket CLOB-API /prices-history, fidelity=1 (Minutenpunkte), "
            "YES-Outcome-Token, Rohdaten-Cache unter data/raw/mentions_latency/."
        ),
        "seed_datei": "data/events/mentions_latency_seed.csv",
        "n_maerkte": len(ergebnisse),
        "parameter": {
            "baseline_fenster_minuten": BASELINE_FENSTER_S // 60,
            "reaktions_schwelle_prozentpunkte": REAKTIONS_SCHWELLE * 100,
            "konvergenz_band": KONVERGENZ_BAND,
            "handelbares_fenster_band": [
                round(1.0 - KONVERGENZ_BAND, 4),
                KONVERGENZ_BAND,
            ],
        },
        "einordnung": (
            "Vergleichswert: Im US-Wahlmarkt lagen die Reaktionszeiten bei "
            "Minuten bis rund einer Stunde (Tabelle A1 der Thesis)."
        ),
        "limitationen": [
            "Drop-Zeitpunkte sind kuratierte, quellenbelegte Beginnzeiten der "
            "Events bzw. Ausstrahlungen; der tatsaechliche Moment der "
            "aufloesungsrelevanten Aussage innerhalb des Events kann spaeter "
            "liegen. Die Latenz enthaelt diese Differenz.",
            "Minutenpunkte der CLOB-API sind bei duennem Handel lueckenhaft; "
            "Reaktions- und Konvergenzzeiten sind dann Obergrenzen auf "
            "Beobachtungsraster-Ebene.",
            "Kleine kuratierte Stichprobe, keine Zufallsauswahl; Maerkte ohne "
            "punktfoermigen Content-Drop (Mehrtagesfenster) wurden ausgeschlossen.",
            "Rein deskriptiv: keine Handels-, Strategie- oder "
            "Profitabilitaetsaussagen; keine Kausalaussagen.",
        ],
        "events": [
            {
                "event": z["event"],
                "drop_ts_utc": z["drop_ts_utc"],
                "quelle_url": z.get("quelle_url", ""),
                "hinweis": z.get("hinweis", ""),
            }
            for z in seed
        ],
        "erstellt_am_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)


def zeichne_abbildung(ergebnisse: list[dict], pfad: Path) -> None:
    """Horizontale Balken je Markt: Minuten bis erste Reaktion und Konvergenz."""
    daten = [r for r in ergebnisse if r["minuten_bis_erste_reaktion"] is not None]
    daten = sorted(
        daten,
        key=lambda r: (
            r["minuten_bis_konvergenz"]
            if r["minuten_bis_konvergenz"] is not None
            else float("inf")
        ),
    )

    fig, ax = plt.subplots(figsize=(10.0, 0.62 * len(daten) + 3.2), dpi=150)
    ys = range(len(daten))
    hoehe = 0.36
    minimum = 0.05  # Untergrenze fuer die Log-Skala

    def wert_text(w: float) -> str:
        text = f"{w:.1f}" if w < 10 else f"{w:.0f}"
        return text.replace(".", ",")

    reakt = [max(r["minuten_bis_erste_reaktion"], minimum) for r in daten]
    konv = [
        max(r["minuten_bis_konvergenz"], minimum)
        if r["minuten_bis_konvergenz"] is not None
        else minimum
        for r in daten
    ]

    b1 = ax.barh(
        [y + hoehe / 2 for y in ys], reakt, height=hoehe,
        color="#4878a8", label="Minuten bis erste Reaktion (> 1 Prozentpunkt)",
    )
    b2 = ax.barh(
        [y - hoehe / 2 for y in ys], konv, height=hoehe,
        color="#c26a3d", label="Minuten bis Konvergenz (dauerhaft richtige Seite)",
    )

    for bar, wert in zip(b1, reakt):
        ax.annotate(
            wert_text(wert),
            (bar.get_width(), bar.get_y() + bar.get_height() / 2),
            textcoords="offset points", xytext=(4, 0),
            va="center", fontsize=8.5, color="#333333",
        )
    for bar, y, r in zip(b2, ys, daten):
        konv_min = r["minuten_bis_konvergenz"]
        if konv_min is None:
            text, stil = "keine Konvergenz im Fenster", "#888888"
        elif konv_min <= 0:
            text, stil = "vor Drop konvergiert", "#888888"
        else:
            text, stil = wert_text(konv_min), "#333333"
        ax.annotate(
            text,
            (bar.get_width(), bar.get_y() + bar.get_height() / 2),
            textcoords="offset points", xytext=(4, 0),
            va="center", fontsize=8.5, color=stil,
            style="italic" if stil == "#888888" else "normal",
        )

    ax.axvline(60, color="#666666", linestyle=":", linewidth=1.2)
    ax.plot(
        [], [], linestyle=":", color="#666666",
        label="Vergleichswert US-Wahlmarkt: rund eine Stunde (Tabelle A1)",
    )

    ax.set_xscale("log")
    ax.set_xlim(minimum, max(max(reakt), max(konv)) * 3)
    ax.set_ylim(-2.1, len(daten) - 0.4)  # Freiraum unten fuer die Legende
    ax.set_yticks(list(ys))
    ax.set_yticklabels([r["event"] for r in daten], fontsize=9)
    ax.set_xlabel("Minuten nach Content-Drop (logarithmische Skala)", fontsize=11)
    fig.suptitle(
        "Einpreisungs-Latenz von Mentions-Maerkten nach Content-Drop",
        fontsize=13, fontweight="bold",
    )
    ax.set_title(
        "Erste Reaktion: mehr als 1 Prozentpunkt Abweichung von der Baseline "
        "(Median 60 Min. vor Drop).\nKonvergenz: Preis bleibt dauerhaft auf der "
        "richtigen Seite von 0,9 bzw. 0,1. Rein deskriptive Auswertung.",
        fontsize=8.5, color="#666666", loc="left", pad=10,
    )
    ax.legend(fontsize=8.5, loc="lower right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.xaxis.grid(True, linestyle=":", alpha=0.45)
    ax.set_axisbelow(True)

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(pfad)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--refresh", action="store_true",
        help="Preisreihen neu von der CLOB-API abrufen (sonst nur Cache).",
    )
    argv = parser.parse_args()

    seed = lese_seed()
    ergebnisse = berechne_ergebnisse(seed, refresh=argv.refresh)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_pfad = RESULTS_DIR / "mentions_latency.csv"
    meta_pfad = RESULTS_DIR / "mentions_latency_metadata.json"
    png_pfad = RESULTS_DIR / "mentions_latency_de.png"

    schreibe_csv(ergebnisse, csv_pfad)
    schreibe_metadata(ergebnisse, seed, meta_pfad)
    zeichne_abbildung(ergebnisse, png_pfad)

    for r in ergebnisse:
        print(
            f"{r['event']:32s} Reaktion "
            f"{str(r['minuten_bis_erste_reaktion']):>8s} Min., Konvergenz "
            f"{str(r['minuten_bis_konvergenz']):>8s} Min., Status {r['status']}"
        )
    print(f"\nGeschrieben: {csv_pfad}")
    print(f"Geschrieben: {meta_pfad}")
    print(f"Geschrieben: {png_pfad}")


if __name__ == "__main__":
    main()
