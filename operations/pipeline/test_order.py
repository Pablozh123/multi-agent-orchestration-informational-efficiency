"""Einmalige kleine Testorder (~1 USD) zur Verifikation der Handelsanbindung.

Waehlt unter den aktiven july-3-Maerkten den YES-Token mit dem
guenstigsten besten Ask, kauft dort die Mindestgroesse (min_order_size,
typisch 5 Shares) per GTC-Limit zum gesehenen Ask, wartet kurz auf den
Fill und loggt alles nach data/live/allin_july3/bot_events.jsonl.

Aufruf: python -m operations.pipeline.test_order [--max-usd 1.2]
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone

from operations.pipeline import config
from operations.pipeline.market_rules import lade_snapshot_rules
from operations.pipeline.orderbook import best_ask, fetch_book


def _log(daten: dict) -> None:
    pfad = config.LIVE_DIR / "bot_events.jsonl"
    with open(pfad, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "wall_ts_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "art": "test_order", **daten,
        }, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--max-usd", type=float, default=1.2)
    argv = parser.parse_args()

    from py_clob_client_v2.clob_types import OrderArgs, OrderType
    from py_clob_client_v2.order_builder.constants import BUY

    from operations.pipeline.execution import baue_live_client

    client, funder = baue_live_client()
    from py_clob_client_v2 import AssetType, BalanceAllowanceParams, SignatureTypeV2
    client.update_balance_allowance(BalanceAllowanceParams(
        asset_type=AssetType.COLLATERAL, signature_type=SignatureTypeV2.POLY_1271))
    print(f"Deposit-Wallet (funder): {funder}")

    # Guenstigsten YES-Ask suchen, dessen Mindestgroesse unter max-usd bleibt.
    kandidaten = []
    for r in lade_snapshot_rules():
        if r.status != "active":
            continue
        book = fetch_book(r.yes_token_id)
        ask = best_ask(book)
        min_size = float(book.get("min_order_size") or 5)
        if ask is not None and ask * min_size <= argv.max_usd:
            kandidaten.append((ask, min_size, r, book))
    if not kandidaten:
        raise SystemExit("Kein Markt mit Mindestgroesse unter dem USD-Limit.")
    ask, min_size, rule, book = min(kandidaten, key=lambda k: k[0])
    # Server-Minimum: marketable BUY braucht mindestens 1 USD Notional.
    shares = round(max(min_size, 1.05 / ask), 2)

    print(f"Testorder: {rule.question}")
    print(f"  Limit BUY YES {shares} Shares @ {ask} "
          f"(~{round(ask * shares, 2)} USD)")

    order = client.create_order(OrderArgs(
        price=ask, size=shares, side=BUY, token_id=rule.yes_token_id))
    antwort = client.post_order(order, OrderType.GTC)
    order_id = antwort.get("orderID") or antwort.get("orderId") or ""
    print(f"  post_order: success={antwort.get('success')} id={order_id[:20]}...")

    status = {}
    for _ in range(6):
        time.sleep(5)
        try:
            status = client.get_order(order_id)
        except Exception as ex:  # noqa: BLE001
            status = {"fehler": str(ex)}
            continue
        if float(status.get("size_matched") or 0) >= shares - 1e-6:
            break

    gefuellt = float(status.get("size_matched") or 0)
    print(f"  Fill: {gefuellt}/{shares} Shares, Status: {status.get('status')}")
    if gefuellt < shares - 1e-6:
        print("  Unvollstaendig — storniere Rest.")
        try:
            from py_clob_client_v2.clob_types import OrderPayload
            client.cancel_order(OrderPayload(orderID=order_id))
        except Exception as ex:  # noqa: BLE001
            print(f"  Cancel-Fehler: {ex}")

    _log({
        "markt": rule.slug, "frage": rule.question, "preis": ask,
        "shares": shares, "usd": round(ask * shares, 2),
        "order_id": order_id, "gefuellt": gefuellt,
        "status": status.get("status"),
        "book_snapshot": {"asks": (book.get("asks") or [])[-5:],
                          "bids": (book.get("bids") or [])[-5:]},
    })
    print("  Geloggt in bot_events.jsonl (art=test_order).")


if __name__ == "__main__":
    main()
