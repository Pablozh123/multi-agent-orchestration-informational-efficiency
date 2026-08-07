"""Preregistrierte Orders fuer den Curtis-E3-Mention-Testlauf (PREREG_CURTIS_E3_2026-08-07).

Platziert die im Prereg-Dokument festgeschriebenen GTC-Limits:

  Taker (gegen liegende Asks, Preis = Prereg-Limit, nie hoeher):
    Secret     YES 100 @ 0.38   (~38 USD)
    Paranormal YES 100 @ 0.16   (~16 USD)
    Rick       YES 100 @ 0.13   (~13 USD, nur mit --mit-rick)

  Maker (Bids in die toten Spreads, zusammen ~60 USD):
    President 10+  YES  50 @ 0.60  (30 USD)
    Ghost          YES  40 @ 0.40  (16 USD)
    White House    YES  40 @ 0.35  (14 USD)

Ohne --scharf werden nur die Buecher gezeigt (Trockenlauf). Preise sind
harte Obergrenzen: ist der Ask inzwischen hoeher, ruht die Order als
Maker-Limit am Prereg-Preis statt zu jagen. Maker-Orders bleiben als GTC
liegen. Log: data/live/curtis_e3/orders.jsonl.

Aufruf (im ba-thesis-Klon): python -m operations.pipeline.curtis_e3_orders [--scharf] [--mit-rick]
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone

from operations.pipeline import config
from operations.pipeline.orderbook import fetch_book

LOG_DIR = config.REPO_ROOT / "data" / "live" / "curtis_e3"

# (Name, YES-Token, Limitpreis, Shares, Art) — exakt wie preregistriert.
ORDERS = [
    ("Secret", "33718139071566081432586571892289623786376304279461073176402212795164683313793",
     0.38, 100, "taker"),
    ("Paranormal", "25187059571507237149845358209582710018348046311515037331774818273684259246850",
     0.16, 100, "taker"),
    ("Rick", "6119025837596426859104208195500513359228089207123806509334579474315087537864",
     0.13, 100, "taker_optional"),
    ("President 10+", "34113922232708347403944556306040172553527115287167011098137107925994036940473",
     0.60, 50, "maker"),
    ("Ghost", "40830126866231433770323496350481196220498628887619699588595369994387990755130",
     0.40, 40, "maker"),
    ("White House", "49602326880337809265186807715940582464565460866598339474427599787079534089334",
     0.35, 40, "maker"),
]


def _log(daten: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_DIR / "orders.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "wall_ts_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            **daten,
        }, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scharf", action="store_true",
                        help="Orders wirklich platzieren (sonst Trockenlauf)")
    parser.add_argument("--mit-rick", action="store_true",
                        help="auch die optionale Rick-Order platzieren")
    argv = parser.parse_args()

    aktiv = [o for o in ORDERS
             if o[4] != "taker_optional" or argv.mit_rick]
    summe = sum(p * s for _, _, p, s, _ in aktiv)
    print(f"{len(aktiv)} Orders, max. Kapitalbindung {summe:.2f} USD "
          f"({'SCHARF' if argv.scharf else 'Trockenlauf'})")

    client = None
    if argv.scharf:
        from py_clob_client_v2 import (AssetType, BalanceAllowanceParams,
                                       SignatureTypeV2)

        from operations.pipeline.execution import baue_live_client
        client, funder = baue_live_client()
        client.update_balance_allowance(BalanceAllowanceParams(
            asset_type=AssetType.COLLATERAL,
            signature_type=SignatureTypeV2.POLY_1271))
        print(f"Deposit-Wallet (funder): {funder}")

    for name, token, preis, shares, art in aktiv:
        book = fetch_book(token)
        asks = sorted(book.get("asks") or [], key=lambda a: float(a["price"]))
        bids = sorted(book.get("bids") or [], key=lambda a: -float(a["price"]))
        top_ask = asks[0] if asks else None
        top_bid = bids[0] if bids else None
        print(f"\n{name} ({art}): Limit BUY YES {shares} @ {preis} "
              f"(~{preis * shares:.2f} USD)")
        print(f"  Buch: Bid {top_bid and (top_bid['price'], top_bid['size'])} / "
              f"Ask {top_ask and (top_ask['price'], top_ask['size'])}")
        if art.startswith("taker") and (top_ask is None
                                        or float(top_ask["price"]) > preis):
            print("  Hinweis: Ask ueber Prereg-Limit — Order wuerde als "
                  "Maker am Limit ruhen, nicht jagen.")
        if not argv.scharf:
            continue

        from py_clob_client_v2.clob_types import OrderArgs, OrderType
        from py_clob_client_v2.order_builder.constants import BUY
        order = client.create_order(OrderArgs(
            price=preis, size=shares, side=BUY, token_id=token))
        antwort = client.post_order(order, OrderType.GTC)
        order_id = antwort.get("orderID") or antwort.get("orderId") or ""
        print(f"  post_order: success={antwort.get('success')} "
              f"id={order_id[:20]}...")

        gefuellt, status = 0.0, {}
        if art.startswith("taker"):
            for _ in range(4):
                time.sleep(4)
                try:
                    status = client.get_order(order_id)
                except Exception as ex:  # noqa: BLE001
                    status = {"fehler": str(ex)}
                    continue
                gefuellt = float(status.get("size_matched") or 0)
                if gefuellt >= shares - 1e-6:
                    break
            print(f"  Fill: {gefuellt}/{shares} "
                  f"(Rest ruht als GTC-Limit weiter)")

        _log({
            "markt": name, "art": art, "preis": preis, "shares": shares,
            "order_id": order_id, "gefuellt": gefuellt,
            "status": status.get("status"),
            "book_snapshot": {"asks": asks[:3], "bids": bids[:3]},
        })

    if argv.scharf:
        print("\nAlle Orders platziert und geloggt "
              "(data/live/curtis_e3/orders.jsonl). GTC-Limits bleiben "
              "bis Ausstrahlung liegen.")


if __name__ == "__main__":
    main()
