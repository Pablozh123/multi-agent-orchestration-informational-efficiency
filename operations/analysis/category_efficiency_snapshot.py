"""Kategorie-Effizienz-Snapshot ueber Polymarket-Marktkategorien (deskriptiv).

Zweck
-----
Deterministische Auswertung der Frage, wie gut die Preise aufgeloester
Polymarket-Maerkte kurz vor der Aufloesung auf der richtigen Seite lagen,
getrennt nach fuenf Kategorien (politics, sports, crypto, pop-culture,
mentions). Rein deskriptiv: keine Handels- oder Profitabilitaetsaussagen.

Dieses Skript rechnet AUSSCHLIESSLICH aus den im Repo gespeicherten
JSON-Dateien (kein Netzzugriff):
  - data/raw/category_efficiency/<slug>.json          (Gamma-Feld-Extrakte)
  - data/raw/category_efficiency/clob_validation/clob_series.json

Datenherkunft (Abrufdatum: 03.07.2026)
--------------------------------------
1) Gamma-API, Endpunkt /markets, je Kategorie die nach Volumen groessten
   aufgeloesten Maerkte:
   https://gamma-api.polymarket.com/markets?tag_id=<ID>&closed=true
        &order=volumeNum&ascending=false&volume_num_min=<SCHWELLE>&limit=40
   Tag-IDs: politics=2, sports=1, crypto=21, pop-culture=596,
   mentions=100343 (Slug 'mention-markets'; der naheliegende Slug 'mentions'
   existiert in der Gamma-Tag-Tabelle nicht, siehe meta der Rohdatei).
2) CLOB-API fuer 10 Maerkte (2 je Kategorie) als Validierungs- und
   Preisquelle: /prices-history mit fidelity=1440 (Tagespunkte).

Stichprobenkonventionen
-----------------------
- Mindestvolumen: 10000 USD je Markt; fuer mentions 1000 USD, weil
  Mentions-Maerkte typischerweise duenn gehandelt werden (in der
  Top-Stichprobe liegen faktisch alle Maerkte weit darueber).
- Zielgroesse war 30 bis 80 Maerkte je Kategorie. Erreicht wurden 12 bis 16,
  weil das Abrufwerkzeug API-Antworten bei ca. 90 kB kappt; die Stichprobe
  umfasst daher je Kategorie die 12 bis 16 volumenstaerksten aufgeloesten
  Maerkte. Diese Verkleinerung ist eine dokumentierte Limitation.
- Auswertungsebene: einzelne binaere Outcome-Maerkte (YES/NO). Multi-Outcome-
  Events (z. B. Mentions-Events, NBA Champion) steuern mehrere Maerkte bei;
  die Anzahl dahinterstehender Events wird je Kategorie mit ausgewiesen.

Gewinnerbestimmung
------------------
outcomePrices der aufgeloesten Maerkte ist ["1","0"] (YES gewinnt) oder
["0","1"] (NO gewinnt). y = 1.0 bzw. 0.0 aus dem ersten Element (YES-Seite).
Maerkte ohne eindeutige 0/1-Aufloesung wuerden ausgeschlossen (kam in der
Stichprobe nicht vor).

Preis einen Tag vor Aufloesung (T-1) und sieben Tage davor (T-7)
----------------------------------------------------------------
Bevorzugte Quelle: CLOB-Tagesreihe (10 Maerkte). Genommen wird der letzte
Punkt mit Zeitstempel <= closedTime - 86400 s (T-1) bzw. - 604800 s (T-7).

Fuer die uebrigen Maerkte Rekonstruktion aus Gamma-Feldern:
  p_close = Schlusspreis-Schaetzer (siehe unten)
  p_T1 = clip01(p_close - oneDayPriceChange)   (fehlend -> 0.0)
  p_T7 = clip01(p_close - oneWeekPriceChange)

Schlusspreis-Schaetzer p_close (ergebnisUNabhaengig, wichtig gegen Bias):
  1. bestBid und bestAsk vorhanden und Spread <= 0.1  ->  Mittelpunkt.
  2. sonst lastTradePrice; widerspricht dieser aber einer vorhandenen
     einseitigen Quote um mehr als 0.5 (z. B. lastTradePrice=1 bei
     bestAsk=0.001), wird die Quote verwendet. Hintergrund: Bei vielen
     NO-aufgeloesten Maerkten ist lastTradePrice=1 ein Artefakt (Zerfalls-
     oder Fehltrade nach Handelsende); validiert an CLOB-Beispielen
     (u. a. will-eleven-die-..., will-kamala-harris-win-...-popular-vote).
  3. sonst einzige vorhandene Quote; ohne jedes Preissignal Ausschluss.

Validierung der Rekonstruktion (gegen CLOB, 10 Maerkte)
-------------------------------------------------------
Das Skript berechnet fuer die 10 CLOB-Maerkte den Rekonstruktionsfehler
|p_rekon - p_CLOB| und die Richtungs-Uebereinstimmung und gibt beides aus.
Ergebnis beim Erstellen dieses Snapshots: 9 von 10 T-1-Richtungen stimmen,
mittlerer absoluter T-1-Fehler ohne Ausreisser ca. 0.02. Ein dokumentierter
Ausreisser (harris-popular-vote): oneDayPriceChange fror beim faktischen
Handelsende (Wahlnacht 06.11.2024) ein, der Markt schloss aber erst am
12.11.2024; die Rekonstruktion liefert dort 0.72 statt wahr 0.002. Fuer die
10 CLOB-Maerkte werden daher die CLOB-Werte verwendet.

T-7-Sonderregel: Bei Maerkten, die vor dem 01.04.2025 schlossen, wurde
oneWeekPriceChange serverseitig teils auf 0 zurueckgesetzt (validiert:
tiktok-banned, btc-100k-november, Wahlmaerkte 11/2024). T-7 wird deshalb nur
berechnet, wenn (a) CLOB-Daten vorliegen oder (b) der Markt am/nach dem
01.04.2025 schloss UND oneWeekPriceChange vorhanden (nicht null) ist.
Beide Kriterien sind ergebnisunabhaengig. T-1 kennt keine solche Regel;
oneDayPriceChange erwies sich in der Validierung auch fuer aeltere Maerkte
als brauchbar (Restrisiko dokumentiert, s. o.).

Metriken je Kategorie
---------------------
- Richtungs-Trefferquote T-1: Anteil Maerkte mit (p_T1 > 0.5 und YES) oder
  (p_T1 < 0.5 und NO). p_T1 == 0.5 zaehlt als Fehler (kam nicht vor).
- Mittlerer Brier-Score T-1: Mittel von (p_T1 - y)^2.
- Dieselben Groessen bei T-7 (reduziertes n wegen T-7-Regel).
- n Maerkte, n Events, Median-Volumen (Feld volumeNum, wie von der API
  gemeldet; enthaelt auch Bot-/Wash-Anteile, keine Bereinigung).

Ausschluesse (vollstaendige Liste)
----------------------------------
1. Je Kategorie der letzte, durch die Antwort-Kappung unvollstaendige
   Datensatz (5 Maerkte insgesamt; IDs in den meta-Bloecken der Rohdateien).
2. Maerkte ohne Handel (volumeNum fehlend/0 oder kein Preissignal aus
   lastTradePrice/bestBid/bestAsk): in der Stichprobe 0 Faelle (Schwelle
   greift serverseitig via volume_num_min).
3. Maerkte ohne eindeutige 0/1-Aufloesung: 0 Faelle.
4. Nur T-7: Maerkte, die die T-7-Sonderregel nicht erfuellen.

Ausgaben
--------
- data/results/category_efficiency_summary.csv  (eine Zeile je Kategorie)
- data/results/category_efficiency_de.png       (deutsche Beschriftung,
  ss statt scharfem S, keine Gedankenstriche)
- stdout: Validierungstabelle Rekonstruktion vs. CLOB.

Erweiterung v2 (Stichproben-Verbreiterung, Abruf 03.07.2026)
------------------------------------------------------------
Zusaetzlich zur Basisdatei je Kategorie liegen Ergaenzungsseiten
<slug>_p2.json bis <slug>_p4.json vor, gezogen ueber den Events-Endpunkt
(aufgeloeste Events nach Event-Volumen absteigend, Raenge 16 bis 60):
  https://gamma-api.polymarket.com/events?tag_slug=<SLUG>&closed=true
       &order=volume&ascending=false&limit=15&offset=<15|30|45>
(tag_slug mention-markets fuer die Dateibasis mentions). Auch diese
Antworten kappt das Abrufwerkzeug bei ca. 90 kB; jede Seite enthaelt daher
nur die vordersten Events der Seite als Feld-Extrakt (gleiches Format wie
die Basisdateien, angeschnittene Datensaetze verworfen und in der meta
der jeweiligen Datei dokumentiert).

Der v2-Lauf liest Basisdatei plus alle Ergaenzungsseiten, dedupliziert
nach Markt-id (Basisdatei hat Vorrang, damit die CLOB-Werte der
Validierungsmaerkte erhalten bleiben) und rechnet mit UNVERAENDERTEN
Konventionen (Volumen-Schwellen, buchkorrigierter T-1-Schaetzer,
ergebnisunabhaengige T-7-Sonderregel). Zweistufige Stichprobe als
dokumentierte Eigenschaft: Basis = volumenstaerkste Maerkte (Markt-Ebene,
/markets-Endpunkt), Seiten 2 bis 4 = Maerkte der Events auf den
Volumen-Raengen 16 bis 60 (Event-Ebene, inkl. kleinerer Maerkte grosser
Events oberhalb der Schwelle). Maerkte ohne closed_time werden
ausgeschlossen (zaehlt in n_ausgeschlossen_in_auswertung).

Zusaetzliche Ausgabe:
- data/results/category_efficiency_summary_v2.csv (gleiche Spalten plus
  n_alt = ausgewertete Maerkte aus der Basisdatei und n_neu = ausgewertete
  Maerkte der Ergaenzungsseiten; n_maerkte = n_alt + n_neu).
Die v1-Ausgaben (summary.csv, PNG) bleiben unveraendert erhalten.
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
RAW_DIR = REPO_ROOT / "data" / "raw" / "category_efficiency"
RESULTS_DIR = REPO_ROOT / "data" / "results"

ABRUFDATUM = "03.07.2026"
T7_CUTOFF = datetime(2025, 4, 1, tzinfo=timezone.utc)
DAY = 86400
WEEK = 7 * DAY

KATEGORIEN = [
    ("politics", "Politik", 10000),
    ("sports", "Sport", 10000),
    ("crypto", "Krypto", 10000),
    ("pop-culture", "Popkultur", 10000),
    ("mentions", "Mentions", 1000),
]


def clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def parse_closed_time(s: str) -> datetime:
    """Gamma closedTime wie '2025-01-22 00:31:19+00' -> UTC-datetime.

    Tolerant gegenueber Sekundenbruchteilen ('... 00:31:19.123+00'); an den
    Basisdateien aendert das nichts (dort ohne Bruchteile validiert).
    """
    s = s.strip()
    if s.endswith("+00"):
        s = s[:-3]
    fmt = "%Y-%m-%d %H:%M:%S.%f" if "." in s else "%Y-%m-%d %H:%M:%S"
    return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)


def outcome_y(outcome_prices: list[str]) -> float | None:
    """1.0 wenn YES gewann, 0.0 wenn NO gewann, sonst None (Ausschluss)."""
    try:
        yes = float(outcome_prices[0])
        no = float(outcome_prices[1])
    except (TypeError, ValueError, IndexError):
        return None
    if yes > 0.99 and no < 0.01:
        return 1.0
    if yes < 0.01 and no > 0.99:
        return 0.0
    return None


def p_close_estimate(m: dict) -> float | None:
    """ErgebnisUNabhaengiger Schlusspreis-Schaetzer (siehe Docstring)."""
    bid = m.get("best_bid")
    ask = m.get("best_ask")
    lt = m.get("last_trade_price")
    if bid is not None and ask is not None and 0.0 <= bid <= ask <= 1.0 and (ask - bid) <= 0.1:
        return (bid + ask) / 2.0
    if lt is not None:
        p = float(lt)
        if ask is not None and p > ask + 0.5:
            return float(ask)
        if bid is not None and p < bid - 0.5:
            return float(bid)
        return p
    if ask is not None:
        return float(ask)
    if bid is not None:
        return float(bid)
    return None


def clob_price_before(history: list[dict], deadline_epoch: int) -> float | None:
    """Letzter Tagespunkt mit t <= deadline_epoch."""
    pts = [h for h in history if h["t"] <= deadline_epoch]
    return pts[-1]["p"] if pts else None


def load_clob() -> dict:
    with open(RAW_DIR / "clob_validation" / "clob_series.json", encoding="utf-8") as f:
        data = json.load(f)
    return {s["market_id"]: s for s in data["series"]}


def lade_maerkte_mit_seiten(slug: str) -> list[tuple[dict, bool]]:
    """Basisdatei plus Ergaenzungsseiten <slug>_p*.json, dedupliziert nach id.

    Rueckgabe: Liste (markt, ist_neu); ist_neu=False fuer Maerkte der
    Basisdatei (v1-Stichprobe), True fuer Maerkte der Ergaenzungsseiten.
    Die Basisdatei hat bei Duplikaten Vorrang (CLOB-Validierungsmaerkte).
    """
    with open(RAW_DIR / f"{slug}.json", encoding="utf-8") as f:
        basis = json.load(f)["markets"]
    maerkte = [(m, False) for m in basis]
    gesehen = {m["id"] for m in basis}
    for pfad in sorted(RAW_DIR.glob(f"{slug}_p*.json")):
        with open(pfad, encoding="utf-8") as f:
            for m in json.load(f)["markets"]:
                if m["id"] in gesehen:
                    continue
                gesehen.add(m["id"])
                maerkte.append((m, True))
    return maerkte


def werte_kategorie_aus(
    slug: str,
    name_de: str,
    schwelle: int,
    maerkte: list[tuple[dict, bool]],
    clob: dict,
    validation_sink: list[str] | None = None,
) -> dict:
    """Kennzahlen-Zeile einer Kategorie (Konventionen siehe Docstring).

    validation_sink: Liste fuer die CLOB-Validierungszeilen; None, wenn die
    Zeilen nicht (erneut) gesammelt werden sollen.
    """
    t1_hits, t1_briers = [], []
    t7_hits, t7_briers = [], []
    volumes, event_ids = [], set()
    n_clob_t1 = 0
    n_ausgeschlossen = 0
    n_alt = 0
    n_neu = 0

    for m, ist_neu in maerkte:
        vol = m.get("volume_num")
        y = outcome_y(m.get("outcome_prices"))
        p_close = p_close_estimate(m)
        if (
            vol is None
            or vol < schwelle
            or vol <= 0
            or y is None
            or p_close is None
            or m.get("closed_time") is None
        ):
            n_ausgeschlossen += 1
            continue

        closed_dt = parse_closed_time(m["closed_time"])
        closed_epoch = int(closed_dt.timestamp())
        d1 = m.get("one_day_price_change")
        w1 = m.get("one_week_price_change")

        p_t1_rekon = clip01(p_close - (d1 if d1 is not None else 0.0))

        series = clob.get(m["id"])
        if series is not None:
            p_t1 = clob_price_before(series["history"], closed_epoch - DAY)
            p_t7 = clob_price_before(series["history"], closed_epoch - WEEK)
            if p_t1 is not None:
                n_clob_t1 += 1
                if validation_sink is not None:
                    richtung_ok = (p_t1_rekon > 0.5) == (p_t1 > 0.5)
                    validation_sink.append(
                        f"{slug:12s} {m['slug'][:52]:52s} "
                        f"p_T1 CLOB={p_t1:.4f} Rekon={p_t1_rekon:.4f} "
                        f"|Fehler|={abs(p_t1_rekon - p_t1):.4f} "
                        f"Richtung {'OK' if richtung_ok else 'ABWEICHUNG'}"
                    )
        else:
            p_t1 = p_t1_rekon
            if closed_dt >= T7_CUTOFF and w1 is not None:
                p_t7 = clip01(p_close - w1)
            else:
                p_t7 = None  # T-7-Sonderregel (siehe Docstring)

        volumes.append(vol)
        event_ids.add(m.get("event_id"))
        if ist_neu:
            n_neu += 1
        else:
            n_alt += 1

        hit_t1 = (p_t1 > 0.5 and y == 1.0) or (p_t1 < 0.5 and y == 0.0)
        t1_hits.append(1.0 if hit_t1 else 0.0)
        t1_briers.append((p_t1 - y) ** 2)

        if p_t7 is not None:
            hit_t7 = (p_t7 > 0.5 and y == 1.0) or (p_t7 < 0.5 and y == 0.0)
            t7_hits.append(1.0 if hit_t7 else 0.0)
            t7_briers.append((p_t7 - y) ** 2)

    n = len(t1_hits)
    return {
        "kategorie": name_de,
        "tag_slug": slug,
        "n_maerkte": n,
        "n_events": len(event_ids),
        "trefferquote_t1": round(sum(t1_hits) / n, 4),
        "brier_t1": round(sum(t1_briers) / n, 4),
        "n_t7": len(t7_hits),
        "trefferquote_t7": round(sum(t7_hits) / len(t7_hits), 4) if t7_hits else "",
        "brier_t7": round(sum(t7_briers) / len(t7_briers), 4) if t7_briers else "",
        "median_volumen_usd": round(statistics.median(volumes), 2),
        "volumen_schwelle_usd": schwelle,
        "n_t1_aus_clob": n_clob_t1,
        "n_ausgeschlossen_in_auswertung": n_ausgeschlossen,
        "n_alt": n_alt,
        "n_neu": n_neu,
    }


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    clob = load_clob()

    rows = []
    rows_v2 = []
    validation_lines = []

    for slug, name_de, schwelle in KATEGORIEN:
        alle = lade_maerkte_mit_seiten(slug)
        basis = [(m, ist_neu) for m, ist_neu in alle if not ist_neu]
        row_v1 = werte_kategorie_aus(
            slug, name_de, schwelle, basis, clob, validation_lines
        )
        rows.append({k: v for k, v in row_v1.items() if k not in ("n_alt", "n_neu")})
        rows_v2.append(werte_kategorie_aus(slug, name_de, schwelle, alle, clob, None))

    csv_path = RESULTS_DIR / "category_efficiency_summary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    csv_v2_path = RESULTS_DIR / "category_efficiency_summary_v2.csv"
    with open(csv_v2_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows_v2[0].keys()))
        writer.writeheader()
        writer.writerows(rows_v2)

    print("Validierung Rekonstruktion vs. CLOB (T-1):")
    for line in validation_lines:
        print("  " + line)
    print()
    print("v1 (nur Basisdateien):")
    for r in rows:
        print(r)
    print()
    print("v2 (Basis plus Ergaenzungsseiten, dedupliziert):")
    for r in rows_v2:
        print(r)
    print(f"\nGeschrieben: {csv_v2_path}")

    # ------------------------------------------------------------- Abbildung
    fig, ax = plt.subplots(figsize=(10.0, 6.0), dpi=150)
    xs = range(len(rows))
    quoten = [r["trefferquote_t1"] * 100 for r in rows]
    labels = [f"{r['kategorie']}\n(n={r['n_maerkte']})" for r in rows]
    bars = ax.bar(xs, quoten, width=0.62, color="#4878a8", edgecolor="white")

    for bar, r in zip(bars, rows):
        q = r["trefferquote_t1"] * 100
        ax.annotate(
            f"{q:.1f} %".replace(".", ","),
            (bar.get_x() + bar.get_width() / 2, q),
            textcoords="offset points",
            xytext=(0, 4),
            ha="center",
            fontsize=11,
            fontweight="bold",
            color="#2b4a66",
        )
        brier_txt = "Brier " + f"{r['brier_t1']:.4f}".replace(".", ",")
        ax.annotate(
            brier_txt,
            (bar.get_x() + bar.get_width() / 2, q / 2),
            ha="center",
            fontsize=8.5,
            color="white",
        )

    ax.set_xticks(list(xs))
    ax.set_xticklabels(labels, fontsize=10.5)
    ax.set_ylim(0, 112)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("Trefferquote T-1 in Prozent", fontsize=11)
    ax.set_xlabel("Kategorie (n = Anzahl ausgewerteter Outcome-Märkte)", fontsize=11)
    fig.suptitle(
        "Richtungs-Trefferquote einen Tag vor Marktauflösung je Kategorie",
        y=0.975,
        fontsize=13.5,
        fontweight="bold",
    )
    fig.text(
        0.5,
        0.9,
        "Polymarket, je Kategorie die volumenstärksten aufgelösten Märkte. Datenabruf: 03.07.2026. "
        "Mindestvolumen 10000 USD, bei Mentions 1000 USD.\n"
        "Anteil Märkte, deren Preis einen Tag vor Auflösung auf der richtigen Seite von 0,5 lag. "
        "In den Balken: mittlerer Brier-Score bei T-1. Rein deskriptive Auswertung.",
        ha="center",
        fontsize=8.2,
        color="#666666",
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, linestyle=":", alpha=0.45)
    ax.set_axisbelow(True)

    fig.tight_layout(rect=(0, 0, 1, 0.87))
    png_path = RESULTS_DIR / "category_efficiency_de.png"
    fig.savefig(png_path)
    print(f"\nGeschrieben: {csv_path}")
    print(f"Geschrieben: {png_path}")


if __name__ == "__main__":
    main()
