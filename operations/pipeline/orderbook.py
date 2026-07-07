"""Orderbuch-Abruf und Kennzahlen (CLOB /book), plus periodischer Logger."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from operations.pipeline import config


def fetch_book(token_id: str) -> dict:
    """Rohes Orderbuch fuer einen Token (mit Retry)."""
    import httpx
    from tenacity import retry, stop_after_attempt, wait_random_exponential

    @retry(stop=stop_after_attempt(3), wait=wait_random_exponential(1, 8), reraise=True)
    def _abruf() -> dict:
        resp = httpx.get(
            config.CLOB_BOOK_URL,
            params={"token_id": token_id},
            headers=config.HTTP_HEADERS,
            timeout=20.0,
        )
        resp.raise_for_status()
        return resp.json()

    return _abruf()


def best_ask(book: dict) -> float | None:
    """Bester (niedrigster) Ask-Preis oder None."""
    asks = book.get("asks") or []
    preise = [float(a["price"]) for a in asks]
    return min(preise) if preise else None


def best_bid(book: dict) -> float | None:
    """Bester (hoechster) Bid-Preis oder None."""
    bids = book.get("bids") or []
    preise = [float(b["price"]) for b in bids]
    return max(preise) if preise else None


def ausfuehrbare_tiefe_usd(book: dict, limit_price: float) -> float:
    """USD-Tiefe auf der Ask-Seite bis einschliesslich limit_price.

    Summiert price*size ueber alle Ask-Level mit Preis <= limit_price
    (die man mit einer Limit-Order zu limit_price nehmen koennte).
    """
    asks = book.get("asks") or []
    usd = 0.0
    for a in asks:
        preis = float(a["price"])
        if preis <= limit_price + 1e-9:
            usd += preis * float(a["size"])
    return round(usd, 2)


def snapshot_row(token_id: str, book: dict, wall_ts_utc: str) -> dict:
    return {
        "wall_ts_utc": wall_ts_utc,
        "token_id": token_id,
        "best_ask": best_ask(book),
        "best_bid": best_bid(book),
        "book_ts": book.get("timestamp"),
        "last_trade_price": book.get("last_trade_price"),
    }


def log_snapshots(
    rules, wall_ts_utc: str, pfad: Path | None = None, fetch=fetch_book
) -> list[dict]:
    """Bucht je aktiven Markt YES- und NO-Ask und haengt sie an eine CSV an."""
    pfad = pfad or (config.LIVE_DIR / "orderbook_log.csv")
    pfad.parent.mkdir(parents=True, exist_ok=True)
    zeilen = []
    for rule in rules:
        if rule.status != "active":
            continue
        for outcome, tok in (("Yes", rule.yes_token_id), ("No", rule.no_token_id)):
            if not tok:
                continue
            book = fetch(tok)
            row = snapshot_row(tok, book, wall_ts_utc)
            row["market_id"] = rule.market_id
            row["slug"] = rule.slug
            row["outcome"] = outcome
            zeilen.append(row)
    neu = not pfad.exists()
    if zeilen:
        felder = ["wall_ts_utc", "market_id", "slug", "outcome", "token_id",
                  "best_ask", "best_bid", "book_ts", "last_trade_price"]
        with open(pfad, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=felder)
            if neu:
                writer.writeheader()
            for r in zeilen:
                writer.writerow({k: r.get(k) for k in felder})
    return zeilen


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
