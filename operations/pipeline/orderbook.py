"""Orderbuch-Abruf und Kennzahlen (CLOB /book), plus periodischer Logger."""

from __future__ import annotations

import csv
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from threading import Event, Lock, Thread
import time

from operations.pipeline import config


class MarketBooks:
    """Public market stream with complete snapshots and connection freshness.

    An unchanged quote may be old while a healthy stream confirms no changes.
    A silent/disconnected stream is unusable until a new complete snapshot.
    """
    def __init__(self, token_ids: list[str]) -> None:
        self.tokens = set(token_ids)
        self._books: dict[str, dict] = {}
        self._lock = Lock()
        self._stop = Event()
        self._last_message: float | None = None
        self.last_error: str | None = None
        self._socket = None
        self._thread = Thread(target=self._run, daemon=True)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *_):
        self._stop.set()
        if self._socket is not None:
            self._socket.close()
        self._thread.join(timeout=4)
        self.disconnect()

    def disconnect(self) -> None:
        with self._lock:
            self._books.clear()
            self._last_message = None

    def get(self, token_id: str) -> dict:
        with self._lock:
            if (self._last_message is None or self._stop.is_set()
                    or time.monotonic()-self._last_message > 20
                    or token_id not in self._books):
                raise LookupError(f"no connected market snapshot for {token_id}")
            return deepcopy(self._books[token_id])

    @staticmethod
    def _level(level: dict) -> tuple[float, float]:
        price, size = float(level["price"]), float(level["size"])
        if not (math.isfinite(price) and 0 < price < 1
                and math.isfinite(size) and size >= 0):
            raise ValueError("invalid orderbook level")
        return price, size

    def apply(self, message) -> None:
        """Apply the documented raw market message, also used by offline replay."""
        messages = message if isinstance(message, list) else [message]
        try:
            with self._lock:
                for item in messages:
                    if item == "PONG":
                        continue
                    event = item.get("event_type")
                    token = item.get("asset_id")
                    if event == "book" and token in self.tokens:
                        book = dict(item)
                        for side in ("asks", "bids"):
                            book[side] = [{"price": str(p), "size": str(s)}
                                          for p, s in map(self._level, item[side]) if s]
                        self._books[token] = book
                    elif event == "price_change":
                        for change in item.get("price_changes", []):
                            token = change.get("asset_id")
                            if token not in self._books:
                                continue
                            book = self._books[token]
                            price, size = self._level(change)
                            if change["side"] not in ("BUY", "SELL"):
                                raise ValueError("invalid orderbook side")
                            side = "bids" if change["side"] == "BUY" else "asks"
                            levels = {float(v["price"]): v for v in book[side]}
                            if size:
                                levels[price] = {"price": str(price), "size": str(size)}
                            else:
                                levels.pop(price, None)
                            book[side] = list(levels.values())
                            book["timestamp"] = item.get("timestamp")
                    elif event == "tick_size_change" and token in self._books:
                        tick = float(item["new_tick_size"])
                        if not math.isfinite(tick) or not 0 < tick < 1:
                            raise ValueError("invalid tick size")
                        self._books[token]["tick_size"] = str(tick)
                self._last_message = time.monotonic()
        except (KeyError, TypeError, ValueError, AttributeError):
            self.disconnect()
            raise

    def _run(self) -> None:
        from websockets.sync.client import connect

        while not self._stop.is_set():
            try:
                with connect("wss://ws-subscriptions-clob.polymarket.com/ws/market",
                             open_timeout=3, close_timeout=1, max_size=4*1024*1024) as ws:
                    self._socket = ws
                    ws.send(json.dumps({"assets_ids": sorted(self.tokens), "type": "market"}))
                    connected_at = time.monotonic()
                    last_ping = 0.0
                    while not self._stop.is_set():
                        now = time.monotonic()
                        if now-last_ping >= 10:
                            ws.send("PING")
                            last_ping = now
                        last_seen = self._last_message if self._last_message is not None else connected_at
                        if now-last_seen > 20:
                            raise TimeoutError("market heartbeat expired")
                        try:
                            raw = ws.recv(timeout=1)
                        except TimeoutError:
                            continue
                        self.apply("PONG" if raw == "PONG" else json.loads(raw))
                        self.last_error = None
            except Exception as exc:  # reconnect public data, never reuse disconnected books
                self.last_error = f"{type(exc).__name__}: {str(exc)[:160]}"
            finally:
                self._socket = None
                self.disconnect()
            self._stop.wait(1)


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
            try:
                book = fetch(tok)
            except Exception:  # noqa: BLE001 - ein toter Token (aufgeloester
                # Markt -> CLOB 404) darf nicht den ganzen Buchlog-Batch
                # abbrechen; diesen Token ueberspringen, Rest weiter loggen.
                continue
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
