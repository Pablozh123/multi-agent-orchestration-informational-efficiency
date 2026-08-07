"""Vorflug-Check: was koennte der Bot auf einem Kalshi-Event ueberhaupt kaufen?

Beantwortet vor einem Call zwei Fragen, ohne API-Key und ohne Order:

1. **Welche Maerkte sind handelbar?** Fuer jeden Markt wird angenommen, das
   Wort faellt jetzt — die echte Entscheidung laeuft gegen das echte Buch.
   Was am Deckel scheitert, faellt hier schon durch.
2. **Was frisst die Gebuehr?** Der Vollpreis (Ask + Taker-Gebuehr) steht
   neben dem rohen Ask; die Spalte `gebuehr_%` zeigt den Aufschlag als
   Anteil des Einsatzes. Das ist die offene Frage aus der Analyse (§6.2):
   auf Polymarket war der Handel kostenlos, hier kostet er am meisten
   genau im Zweifel-Fenster.

Gerechnet wird mit `KalshiDryRunExecutor`, also mit derselben Budget-,
Tiefen- und Groessenlogik wie im Live-Betrieb — nur ohne Order.

    python -m operations.pipeline.kalshi_probelauf --event KXFEDMENTION-26JUL
"""

from __future__ import annotations

import argparse
from pathlib import Path

from operations.pipeline import (
    config,
    kalshi_client,
    kalshi_decision,
    kalshi_execution,
    kalshi_rules,
)


def pruefe_markt(regel, buch: dict, executor) -> dict:
    """Ein Markt: Entscheidung und simulierter Kauf gegen das echte Buch."""
    poly_buch = kalshi_client.buch_als_polymarket(buch)
    asks = poly_buch.get("asks") or []
    ask = asks[0]["price"] if asks else None
    zeile = {
        "ticker": regel.market_id,
        "wort": regel.extra.get("wort", ""),
        "ask": ask,
        "vollpreis": None if ask is None else kalshi_decision.vollpreis(ask),
        "aktion": "NONE",
        "kontrakte": 0.0,
        "einsatz_usd": 0.0,
        "grund": "",
    }
    # Annahme fuer den Vorflug: das Wort faellt jetzt -> Zaehlerstand 1.
    entscheidung = kalshi_decision.entscheide_yes(regel, 1, ask)
    zeile["aktion"] = entscheidung.action
    zeile["grund"] = entscheidung.reason
    if entscheidung.action != "YES":
        return zeile
    ergebnis = executor.place(entscheidung, poly_buch)
    zeile["kontrakte"] = ergebnis.size_shares
    zeile["einsatz_usd"] = ergebnis.size_usd
    zeile["grund"] = f"{ergebnis.status}: {ergebnis.detail[:60]}"
    return zeile


def lauf(event: str, log_pfad: Path | None = None) -> list[dict]:
    """Jeder Markt wird EINZELN geprueft, mit vollem Marktbudget.

    Ein gemeinsamer Executor waere hier falsch: er kauft den Pool in
    Listenreihenfolge leer, und alle spaeteren Maerkte meldeten dann
    "budget_rest=0" — das laese sie untradebar aussehen, obwohl nur das
    Geld alle war. Die Frage des Vorflugs ist aber "welcher Markt WAERE
    kaufbar", nicht "was passiert bei dieser Reihenfolge".
    """
    maerkte = kalshi_client.hole_maerkte(event)
    regeln = kalshi_rules.build_rules(maerkte)
    zeilen = []
    for regel in regeln:
        if regel.status != "active":
            zeilen.append({
                "ticker": regel.market_id, "wort": regel.extra.get("wort", ""),
                "ask": None, "vollpreis": None, "aktion": "SKIP",
                "kontrakte": 0.0, "einsatz_usd": 0.0,
                "grund": regel.skip_grund,
            })
            continue
        try:
            buch = kalshi_client.hole_orderbuch(regel.market_id)
        except Exception as fehler:  # noqa: BLE001
            zeilen.append({
                "ticker": regel.market_id, "wort": regel.extra.get("wort", ""),
                "ask": None, "vollpreis": None, "aktion": "FEHLER",
                "kontrakte": 0.0, "einsatz_usd": 0.0,
                "grund": str(fehler)[:80],
            })
            continue
        executor = kalshi_execution.baue_executor(False, log_pfad)
        zeilen.append(pruefe_markt(regel, buch, executor))
    return zeilen


def drucke(zeilen: list[dict]) -> None:
    kopf = (f"{'Wort':<28}{'Ask':>7}{'Voll':>7}{'Geb%':>7}"
            f"{'Kontr.':>9}{'USD':>8}  Ergebnis")
    print(kopf)
    print("-" * len(kopf))
    for z in sorted(zeilen, key=lambda z: (z["aktion"] != "YES", z["wort"])):
        ask, voll = z["ask"], z["vollpreis"]
        geb = "" if not ask else f"{(voll - ask) / ask * 100:.1f}"
        print(f"{(z['wort'] or '')[:27]:<28}"
              f"{'' if ask is None else f'{ask:.2f}':>7}"
              f"{'' if voll is None else f'{voll:.2f}':>7}"
              f"{geb:>7}"
              f"{z['kontrakte']:>9.2f}{z['einsatz_usd']:>8.2f}  "
              f"{z['aktion']}: {z['grund'][:52]}")
    kaufbar = [z for z in zeilen if z["aktion"] == "YES" and z["kontrakte"] > 0]
    summe = sum(z["einsatz_usd"] for z in kaufbar)
    gebuehren = [
        (z["vollpreis"] - z["ask"]) / z["ask"] * 100
        for z in kaufbar if z["ask"]
    ]
    print("-" * len(kopf))
    print(f"{len(kaufbar)} von {len(zeilen)} Maerkten kaufbar. Je Markt volle "
          f"Kappe {config.MAX_USD_PRO_MARKT} USD gerechnet (kein geteilter "
          f"Pool) -> {summe:.2f} USD, falls ALLE ausloesen; der Live-Pool "
          f"({config.MAX_USD_GESAMT} USD) deckelt das.")
    if gebuehren:
        print(f"Gebuehrenaufschlag auf den Einsatz: "
              f"{min(gebuehren):.1f}% bis {max(gebuehren):.1f}% "
              f"(Median {sorted(gebuehren)[len(gebuehren) // 2]:.1f}%), "
              f"Deckel {config.ASK_OBERGRENZE}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--event", required=True, help="Kalshi-Event-Ticker")
    p.add_argument("--log", default=None, help="Pfad fuer das Entscheidungslog")
    args = p.parse_args()
    drucke(lauf(args.event, Path(args.log) if args.log else None))


if __name__ == "__main__":
    main()
