"""Realisierte Trades im South-Park-E6-Fenster (deskriptiv).

Zweck
-----
Zieht die realisierten Trades des Mentions-Markts southpark_s27e6
(Polymarket Data-API) und wertet das Fenster vom Content-Drop
(2025-10-16 02:00 UTC, TV-Premiere) bis Drop + 16 Stunden aus. Die
Fenstergroesse folgt der gemessenen Konvergenzdauer (961 Minuten) aus
data/results/mentions_latency.csv. Rein deskriptive Auswertung:
keine Handels-, Strategie- oder Profitabilitaetsaussagen.

Datenquelle
-----------
https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N
Antworten kommen neueste zuerst und kennen keinen Zeitfilter. Es wird
rueckwaerts paginiert, bis die Zeitstempel vor 2025-10-16 01:00 UTC
(eine Stunde vor Drop) liegen. Rohantworten werden unter
data/raw/mentions_latency/ gecacht; ohne --refresh rechnet das Skript
ausschliesslich aus dem Cache.

Die conditionId stammt aus der Seed-Zeile southpark_s27e6 in
data/events/mentions_latency_seed.csv.

Ausgaben
--------
- data/results/southpark_e6_window_trades.csv (eine Zeile je Trade im
  Fenster, ohne Wallet-Adressen)
- data/results/southpark_e6_window_trades_metadata.json mit Kennzahlen:
  Anzahl Trades, Gesamt-USD, groesster Einzeltrade, USD je Stunde nach
  Drop, sowie separat YES-Kaeufe mit Preis unter 0.7.

Aufruf: python -m operations.analysis.southpark_window_trades [--refresh]
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = REPO_ROOT / "data" / "events" / "mentions_latency_seed.csv"
RAW_DIR = REPO_ROOT / "data" / "raw" / "mentions_latency"
RESULTS_DIR = REPO_ROOT / "data" / "results"

TRADES_URL = "https://data-api.polymarket.com/trades"
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

EVENT = "southpark_s27e6"
SEITENLIMIT = 500
MAX_SEITEN = 200  # Sicherheitsgrenze gegen Endlos-Pagination
FENSTER_STUNDEN = 16
YES_KAUF_PREISSCHWELLE = 0.7


# ------------------------------------------------------------ Kennzahlen


def filtere_fenster(
    trades: list[dict], drop_epoch: int, stunden: int = FENSTER_STUNDEN
) -> list[dict]:
    """Trades mit drop <= timestamp < drop + stunden, aelteste zuerst."""
    ende = drop_epoch + stunden * 3600
    im_fenster = [
        t for t in trades if drop_epoch <= int(t["timestamp"]) < ende
    ]
    return sorted(im_fenster, key=lambda t: int(t["timestamp"]))


def trade_usd(trade: dict) -> float:
    """USD-Volumen eines Trades (Preis mal Stueckzahl)."""
    return float(trade["price"]) * float(trade["size"])


def usd_je_stunde(
    trades: list[dict], drop_epoch: int, stunden: int = FENSTER_STUNDEN
) -> list[dict]:
    """USD-Summe je voller Stunde nach Drop (Stunde 0 bis stunden-1)."""
    summen = [0.0] * stunden
    zaehler = [0] * stunden
    for t in trades:
        idx = (int(t["timestamp"]) - drop_epoch) // 3600
        if 0 <= idx < stunden:
            summen[idx] += trade_usd(t)
            zaehler[idx] += 1
    return [
        {"stunde_nach_drop": i, "n_trades": zaehler[i], "usd": round(summen[i], 2)}
        for i in range(stunden)
    ]


def yes_kaeufe_unter(
    trades: list[dict], schwelle: float = YES_KAUF_PREISSCHWELLE
) -> list[dict]:
    """YES-Kaeufe mit Preis strikt unter der Schwelle."""
    return [
        t
        for t in trades
        if t["side"] == "BUY"
        and t["outcome"] == "Yes"
        and float(t["price"]) < schwelle
    ]


def fasse_zusammen(trades: list[dict], drop_epoch: int) -> dict:
    """Kennzahlen fuer die Fenster-Trades (deterministisch)."""
    gesamt = round(sum(trade_usd(t) for t in trades), 2)
    groesster = round(max((trade_usd(t) for t in trades), default=0.0), 2)
    yes_billig = yes_kaeufe_unter(trades)
    return {
        "n_trades": len(trades),
        "gesamt_usd": gesamt,
        "groesster_einzeltrade_usd": groesster,
        "usd_je_stunde_nach_drop": usd_je_stunde(trades, drop_epoch),
        "yes_kaeufe_preis_unter_0_7": {
            "n_trades": len(yes_billig),
            "gesamt_usd": round(sum(trade_usd(t) for t in yes_billig), 2),
            "groesster_einzeltrade_usd": round(
                max((trade_usd(t) for t in yes_billig), default=0.0), 2
            ),
            "preisschwelle": YES_KAUF_PREISSCHWELLE,
        },
    }


# ------------------------------------------------------------ Abruf und Seed


def parse_ts_utc(wert: str) -> int:
    dt = datetime.fromisoformat(wert.strip().replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError(f"Zeitstempel ohne Zeitzone: {wert!r}")
    return int(dt.astimezone(timezone.utc).timestamp())


def lese_seed_zeile(event: str = EVENT, pfad: Path = SEED_PATH) -> dict:
    with open(pfad, encoding="utf-8") as f:
        for zeile in csv.DictReader(f):
            if zeile["event"] == event:
                return zeile
    raise ValueError(f"Event {event!r} nicht in {pfad}")


def _fetch_trades_seite(condition_id: str, offset: int) -> list[dict]:
    """Eine Seite Trades von der Data-API (neueste zuerst), mit Retry."""
    import httpx
    from tenacity import retry, stop_after_attempt, wait_random_exponential

    @retry(stop=stop_after_attempt(3), wait=wait_random_exponential(1, 10), reraise=True)
    def _abruf() -> list[dict]:
        resp = httpx.get(
            TRADES_URL,
            params={"market": condition_id, "limit": SEITENLIMIT, "offset": offset},
            headers=HTTP_HEADERS,
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()

    return _abruf()


def lade_trades(
    condition_id: str,
    cutoff_epoch: int,
    refresh: bool = False,
    fetch_seite: Callable[[str, int], list[dict]] | None = None,
) -> list[dict]:
    """Laedt alle Trades bis vor den Cutoff, aus Cache oder live.

    Live-Pagination: neueste zuerst; es wird weitergeblaettert, bis der
    aelteste Zeitstempel einer Seite vor dem Cutoff liegt oder eine
    Seite leer/unvollstaendig zurueckkommt.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cache = RAW_DIR / f"trades_{EVENT}.json"
    if cache.exists() and not refresh:
        with open(cache, encoding="utf-8") as f:
            return json.load(f)["trades"]

    fetch_seite = fetch_seite or _fetch_trades_seite
    alle: list[dict] = []
    for seite in range(MAX_SEITEN):
        batch = fetch_seite(condition_id, seite * SEITENLIMIT)
        if not batch:
            break
        alle.extend(batch)
        aeltester = min(int(t["timestamp"]) for t in batch)
        if aeltester < cutoff_epoch or len(batch) < SEITENLIMIT:
            break
    else:
        raise RuntimeError(
            f"Pagination nach {MAX_SEITEN} Seiten abgebrochen; "
            "Cutoff nicht erreicht."
        )

    with open(cache, "w", encoding="utf-8") as f:
        json.dump(
            {
                "meta": {
                    "quelle_url": TRADES_URL,
                    "parameter": {
                        "market": condition_id,
                        "limit": SEITENLIMIT,
                        "pagination": "offset rueckwaerts bis vor Cutoff",
                        "cutoff_epoch": cutoff_epoch,
                    },
                    "abgerufen_am_utc": datetime.now(timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    "hinweis": (
                        "Vollstaendige Rohantworten inkl. Wallet-Feldern; "
                        "Ergebnisdateien enthalten keine Wallet-Adressen."
                    ),
                },
                "trades": alle,
            },
            f,
            ensure_ascii=False,
        )
    return alle


# ------------------------------------------------------------ Pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--refresh", action="store_true",
        help="Trades neu von der Data-API abrufen (sonst nur Cache).",
    )
    argv = parser.parse_args()

    seed = lese_seed_zeile()
    drop_epoch = parse_ts_utc(seed["drop_ts_utc"])
    cutoff_epoch = drop_epoch - 3600

    trades = lade_trades(seed["condition_id"], cutoff_epoch, refresh=argv.refresh)
    fenster = filtere_fenster(trades, drop_epoch)
    kennzahlen = fasse_zusammen(fenster, drop_epoch)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_pfad = RESULTS_DIR / "southpark_e6_window_trades.csv"
    with open(csv_pfad, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["timestamp_utc", "minuten_nach_drop", "seite", "outcome", "preis",
             "stueckzahl", "usd"]
        )
        for t in fenster:
            ts = int(t["timestamp"])
            writer.writerow(
                [
                    datetime.fromtimestamp(ts, timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    round((ts - drop_epoch) / 60.0, 1),
                    t["side"],
                    t["outcome"],
                    float(t["price"]),
                    float(t["size"]),
                    round(trade_usd(t), 2),
                ]
            )

    meta_pfad = RESULTS_DIR / "southpark_e6_window_trades_metadata.json"
    meta = {
        "beschreibung": (
            "Realisierte Trades des Markts southpark_s27e6 im Fenster vom "
            "Content-Drop (TV-Premiere 2025-10-16 02:00 UTC) bis Drop + "
            f"{FENSTER_STUNDEN} Stunden. Fenstergroesse folgt der gemessenen "
            "Konvergenzdauer (961 Minuten). Rein deskriptiv, keine Handels- "
            "oder Profitabilitaetsaussagen; YES-Kaeufe unter 0.7 beschreiben "
            "beobachtete Transaktionen, nicht deren Ertrag."
        ),
        "datenquelle": (
            f"{TRADES_URL}?market=<conditionId>&limit={SEITENLIMIT}&offset=N, "
            "neueste zuerst, rueckwaerts paginiert bis vor "
            "2025-10-16T01:00:00Z; Rohdaten-Cache unter data/raw/mentions_latency/."
        ),
        "condition_id": seed["condition_id"],
        "drop_ts_utc": seed["drop_ts_utc"],
        "fenster_stunden": FENSTER_STUNDEN,
        "kennzahlen": kennzahlen,
        "enthaelt_wallet_adressen": False,
        "erstellt_am_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(meta_pfad, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    print(f"Trades gesamt (Cache): {len(trades)}")
    print(f"Trades im Fenster:     {kennzahlen['n_trades']}")
    print(f"Gesamt-USD:            {kennzahlen['gesamt_usd']}")
    print(f"Groesster Einzeltrade: {kennzahlen['groesster_einzeltrade_usd']}")
    yk = kennzahlen["yes_kaeufe_preis_unter_0_7"]
    print(f"YES-Kaeufe < 0.7:      {yk['n_trades']} Trades, {yk['gesamt_usd']} USD")
    print(f"\nGeschrieben: {csv_pfad}")
    print(f"Geschrieben: {meta_pfad}")


if __name__ == "__main__":
    main()
