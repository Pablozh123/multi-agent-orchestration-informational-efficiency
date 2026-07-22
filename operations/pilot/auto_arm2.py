"""Automatisierte Ausfuehrung von Arm 2 des Echtgeld-Mini-Piloten.

Quelle der Regeln: docs/project/PILOT_PROTOKOLL_ECHTGELD_2026-07-11.md
(Version 3 vom 22.07.2026). Version 3 hebt die manuelle Ausfuehrung fuer
Arm 2 auf; Arm 1 bleibt ausdruecklich manuell, weil er ein Urteil ueber
eine externe Referenzquelle verlangt (Beispiel-Fehlschluss: "Will bitcoin
hit $1m before GTA VI?" wird als Kandidat markiert, ist aber nichts
entschieden).

Ablauf je Lauf:

1. Signale aus ``pilot/signals.csv`` lesen, nur ``arm2``/``signal``.
2. Auswahl streng in Signal-Reihenfolge (aeltestes zuerst) -- mechanisch,
   damit keine nachtraegliche Rosinenpickerei entsteht.
3. Jeden Kandidaten am LIVE-Buch neu pruefen (Signale veralten): Ask im
   Fenster 0.90-0.97 und ausfuehrbare Tiefe >= 20 USDC.
4. Kaufen mit fixem Einsatz, Deckel: Gesamtbudget und ein Trade je Markt.
5. Alle Protokoll-Pflichtfelder nach ``pilot/trades.csv`` schreiben.

Sicherheitsnetze: Dry-Run ist Standard (Live nur mit ``--live``),
Kill-Switch ueber ``data/live/STOP``, harter Budgetdeckel aus der
bereits getaetigten Summe in ``trades.csv``, Stopp nach Fensterende,
ausschliesslich Kaeufe (Exit laeuft laut Protokoll nur ueber die
Aufloesung). Der Mentions-Bot wird nicht angefasst: eigener
Ausfuehrungspfad mit eigenen Parametern.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from operations.pilot import watcher
from operations.pipeline import config
from operations.pipeline.orderbook import ausfuehrbare_tiefe_usd, best_ask, fetch_book

# --- Eingefrorene Parameter aus Protokoll V3 -------------------------------
EINSATZ_USDC = 5.0            # je Trade (V3; V2 waren 10 USDC)
BUDGET_USDC = 100.0           # Gesamtbudget, unveraendert seit V2
MAX_TRADES = 20               # BUDGET_USDC / EINSATZ_USDC
HANDELSFENSTER_BIS = date(2026, 8, 1)
# Arm-2-Regeln unveraendert aus dem Watcher (eine Quelle der Wahrheit):
MIN_PREIS = watcher.ARM2_MIN_PREIS          # 0.90
MAX_PREIS = watcher.ARM2_MAX_PREIS          # 0.97
MIN_TIEFE_USDC = watcher.MIN_BUCHTIEFE_USDC  # 20.0

#: Boersen-Minimum: Polymarket verlangt mindestens 5 Anteile je Order.
MIN_ANTEILE = 5.0

PROTOKOLL_QUELLE = (
    "docs/project/PILOT_PROTOKOLL_ECHTGELD_2026-07-11.md (Version 3, 2026-07-22)"
)


@dataclass
class Kaufergebnis:
    status: str  # "fill", "kein_fill", "fehler", "dry_run_fill"
    ausfuehrungspreis: float | None = None
    anteile: float = 0.0
    betrag_usd: float = 0.0
    gebuehren_usd: float | None = None
    detail: str = ""


class DryRunKaeufer:
    """Simuliert den Fill zum gesehenen Ask (dokumentierte Annahme)."""

    live = False

    def kaufe(self, token_id: str, ask: float, einsatz_usd: float) -> Kaufergebnis:
        anteile = round(einsatz_usd / ask, 2)
        return Kaufergebnis(
            status="dry_run_fill",
            ausfuehrungspreis=ask,
            anteile=anteile,
            betrag_usd=round(anteile * ask, 2),
            gebuehren_usd=0.0,
            detail="DRY_RUN: angenommener Fill zum gesehenen Ask",
        )


class LiveKaeufer:
    """FAK-Kauf ueber den bestehenden CLOB-V2-Client.

    Bewusst eigener Pfad statt ``pipeline.execution.LiveExecutor``: dessen
    Deckel (``ASK_OBERGRENZE`` 0.90) stammt aus der Mentions-EV-Rechnung
    und wuerde jeden Arm-2-Kauf im Fenster 0.90-0.97 blockieren. Geteilt
    wird nur der Client-Aufbau, damit am laufenden Bot nichts veraendert
    wird.
    """

    live = True

    def __init__(self) -> None:
        from operations.pipeline.execution import baue_live_client

        self.client, self.funder = baue_live_client()

    def kaufe(self, token_id: str, ask: float, einsatz_usd: float) -> Kaufergebnis:
        import time

        from py_clob_client_v2 import MarketOrderArgsV2
        from py_clob_client_v2.clob_types import OrderType
        from py_clob_client_v2.order_builder.constants import BUY

        deckel = min(round(ask, 4), MAX_PREIS)  # nie ueber der Protokollgrenze
        order = self.client.create_market_order(
            MarketOrderArgsV2(
                token_id=token_id, amount=einsatz_usd, side=BUY,
                price=deckel, order_type=OrderType.FAK,
            )
        )
        antwort = self.client.post_order(order, OrderType.FAK)
        order_id = antwort.get("orderID") or antwort.get("orderId") or ""
        time.sleep(2)  # FAK ist sofort terminal
        try:
            status = self.client.get_order(order_id) if order_id else {}
        except Exception as exc:  # noqa: BLE001
            return Kaufergebnis("fehler", detail=f"get_order: {exc}")
        anteile = float(status.get("size_matched") or 0)
        if anteile <= 0:
            return Kaufergebnis("kein_fill", detail=f"FAK ohne Fill (deckel {deckel})")
        preis = float(status.get("price") or deckel)
        gebuehren = status.get("fee_rate_bps")
        return Kaufergebnis(
            status="fill",
            ausfuehrungspreis=preis,
            anteile=anteile,
            betrag_usd=round(anteile * preis, 2),
            gebuehren_usd=(
                round(anteile * preis * float(gebuehren) / 10_000, 4)
                if gebuehren is not None
                else None
            ),
            detail=f"FAK {order_id[:14]} deckel {deckel}",
        )


def fenster_offen(heute: date | None = None) -> bool:
    return (heute or datetime.now(timezone.utc).date()) <= HANDELSFENSTER_BIS


def lade_offene_signale(signals_pfad: Path, gehandelt: set[str]) -> list[dict]:
    """Arm-2-Signale in Signal-Reihenfolge, ohne bereits gehandelte Maerkte."""

    if not signals_pfad.exists():
        return []
    with open(signals_pfad, encoding="utf-8", newline="") as handle:
        zeilen = list(csv.DictReader(handle))
    offen: list[dict] = []
    gesehen: set[str] = set()
    for zeile in zeilen:
        markt = str(zeile.get("market_id") or "")
        if zeile.get("arm") != "arm2" or zeile.get("status") != "signal":
            continue
        if markt in gehandelt or markt in gesehen:
            continue
        gesehen.add(markt)
        offen.append(zeile)
    return sorted(offen, key=lambda z: str(z.get("ts_utc") or ""))


def bereits_ausgegeben(trades_pfad: Path) -> tuple[float, set[str], int]:
    """(Summe USD, gehandelte Markt-Ids, Anzahl Trades) aus dem Journal."""

    if not trades_pfad.exists():
        return 0.0, set(), 0
    summe = 0.0
    maerkte: set[str] = set()
    anzahl = 0
    with open(trades_pfad, encoding="utf-8", newline="") as handle:
        for zeile in csv.DictReader(handle):
            markt = str(zeile.get("markt_id") or "").strip()
            if not markt:
                continue
            maerkte.add(markt)
            anzahl += 1
            try:
                summe += float(zeile.get("groesse_usd") or 0)
            except (TypeError, ValueError):
                continue
    return round(summe, 2), maerkte, anzahl


def pruefe_am_buch(token_id: str, fetch=fetch_book) -> tuple[float | None, float, str]:
    """(Ask, ausfuehrbare Tiefe, Ablehnungsgrund) -- Signale veralten."""

    try:
        buch = fetch(token_id)
    except Exception as exc:  # noqa: BLE001
        return None, 0.0, f"buch_nicht_ladbar ({type(exc).__name__})"
    ask = best_ask(buch)
    if ask is None:
        return None, 0.0, "kein_ask"
    if not (MIN_PREIS <= ask <= MAX_PREIS):
        return ask, 0.0, f"preis_ausserhalb_fenster ({ask})"
    tiefe = ausfuehrbare_tiefe_usd(buch, MAX_PREIS)
    if tiefe < MIN_TIEFE_USDC:
        return ask, tiefe, f"tiefe_unter_minimum ({tiefe})"
    if EINSATZ_USDC / ask < MIN_ANTEILE:
        return ask, tiefe, f"unter_boersenminimum ({MIN_ANTEILE} anteile)"
    return ask, tiefe, ""


def schreibe_trade(
    trades_pfad: Path, signal: dict, ask: float, tiefe: float,
    ergebnis: Kaufergebnis, jetzt: str,
) -> None:
    watcher.ensure_trades_template(trades_pfad)
    zeile = {
        "zeitstempel_utc": jetzt,
        "markt_id": signal.get("market_id"),
        "markt_frage": signal.get("frage"),
        "arm": "arm2",
        "signal_regel": signal.get("regel"),
        "signal_ausloesewert": signal.get("ausloesewert"),
        "seite": signal.get("seite"),
        "signalpreis": ask,
        "ausfuehrungspreis": ergebnis.ausfuehrungspreis,
        "groesse_usd": ergebnis.betrag_usd,
        "gebuehren_usd": ergebnis.gebuehren_usd,
        "slippage": (
            None
            if ergebnis.ausfuehrungspreis is None
            else round(ergebnis.ausfuehrungspreis - ask, 4)
        ),
        "orderbuchtiefe_einstieg_usd": tiefe,
        "exit_zeit_utc": "",
        "exit_preis": "",
        "exit_grund": "haelt bis zur Aufloesung (Protokoll)",
        "bemerkung": f"automatisiert (V3): {ergebnis.status}; {ergebnis.detail}",
    }
    with open(trades_pfad, "a", encoding="utf-8", newline="") as handle:
        csv.DictWriter(handle, fieldnames=watcher.TRADES_CSV_FELDER).writerow(zeile)


def lauf(
    *,
    pilot_dir: Path = watcher.PILOT_DIR,
    kaeufer=None,
    fetch=fetch_book,
    heute: date | None = None,
    max_neue_trades: int | None = None,
) -> dict:
    """Ein Ausfuehrungslauf. Liefert eine Zusammenfassung als dict."""

    jetzt = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    bericht: dict = {
        "ts_utc": jetzt, "protokoll": PROTOKOLL_QUELLE, "modus": "dry_run",
        "geprueft": 0, "gekauft": 0, "abgelehnt": {}, "ausgegeben_usd": 0.0,
    }
    if not fenster_offen(heute):
        bericht["abbruch"] = f"Handelsfenster bis {HANDELSFENSTER_BIS} beendet"
        return bericht
    if config.STOP_FILE.exists():
        bericht["abbruch"] = "Kill-Switch data/live/STOP aktiv"
        return bericht

    kaeufer = kaeufer or DryRunKaeufer()
    live = bool(getattr(kaeufer, "live", False))
    bericht["modus"] = "live" if live else "dry_run"
    # Das Protokoll-Journal enthaelt ausschliesslich echte Trades. Dry-Runs
    # fuehren ein eigenes Journal, sonst waere der Nachweis verfaelscht --
    # und Probelaeufe wuerden Budget und Trade-Deckel aufbrauchen.
    trades_pfad = pilot_dir / ("trades.csv" if live else "trades_dry_run.csv")
    bericht["journal"] = trades_pfad.name
    ausgegeben, gehandelt, anzahl = bereits_ausgegeben(trades_pfad)
    if not live:
        # Ein Markt, der echt gehandelt wurde, bleibt auch im Probelauf tabu.
        gehandelt |= bereits_ausgegeben(pilot_dir / "trades.csv")[1]
    bericht["ausgegeben_usd"] = ausgegeben

    def ablehnen(grund: str) -> None:
        schluessel = grund.split(" (")[0]
        bericht["abgelehnt"][schluessel] = bericht["abgelehnt"].get(schluessel, 0) + 1

    for signal in lade_offene_signale(pilot_dir / "signals.csv", gehandelt):
        if anzahl >= MAX_TRADES or ausgegeben + EINSATZ_USDC > BUDGET_USDC:
            bericht["abbruch"] = (
                f"Budget/Trade-Deckel erreicht ({anzahl}/{MAX_TRADES} Trades, "
                f"{ausgegeben}/{BUDGET_USDC} USDC)"
            )
            break
        if max_neue_trades is not None and bericht["gekauft"] >= max_neue_trades:
            bericht["abbruch"] = f"Laufgrenze erreicht ({max_neue_trades})"
            break
        if config.STOP_FILE.exists():
            bericht["abbruch"] = "Kill-Switch waehrend des Laufs gesetzt"
            break

        bericht["geprueft"] += 1
        ask, tiefe, grund = pruefe_am_buch(str(signal.get("token_id")), fetch=fetch)
        if grund:
            ablehnen(grund)
            continue

        ergebnis = kaeufer.kaufe(str(signal.get("token_id")), ask, EINSATZ_USDC)
        if ergebnis.status in ("fill", "dry_run_fill"):
            schreibe_trade(trades_pfad, signal, ask, tiefe, ergebnis, jetzt)
            ausgegeben = round(ausgegeben + ergebnis.betrag_usd, 2)
            anzahl += 1
            bericht["gekauft"] += 1
            bericht["ausgegeben_usd"] = ausgegeben
        else:
            ablehnen(ergebnis.status)
    return bericht


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=f"Arm-2-Ausfuehrung des Piloten. Regeln: {PROTOKOLL_QUELLE}"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="ECHTES GELD. Ohne dieses Flag laeuft alles als Dry-Run.",
    )
    parser.add_argument(
        "--max-neue-trades",
        type=int,
        default=None,
        help="Obergrenze neuer Trades in DIESEM Lauf (Default: bis Budgetende).",
    )
    args = parser.parse_args(argv)

    kaeufer = LiveKaeufer() if args.live else DryRunKaeufer()
    bericht = lauf(kaeufer=kaeufer, max_neue_trades=args.max_neue_trades)
    import json

    print(json.dumps(bericht, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
