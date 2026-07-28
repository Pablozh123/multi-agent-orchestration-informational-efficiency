"""Kalshi-Orderausfuehrung: Signatur, FOK-Orders, Buchung aus der Antwort.

Erbt Budget, Kill-Switch, Groessendeckel und Entscheidungslog unveraendert
von `execution.ExecutorBase` — das Kalshi-Buch wird dafuer per
`kalshi_client.buch_als_polymarket` in das CLOB-Format uebersetzt.

Order-Schema ist die V2-Form (`POST /portfolio/events/orders`); das alte
`/portfolio/orders` wird laut Spezifikation ab Mai 2026 abgekuendigt.
V2 quotiert **alles aus YES-Sicht**: `side: bid` kauft YES zum Preis,
`side: ask` verkauft YES — wirtschaftlich ein NO-Kauf zu `1 - price`.
Preise und Stueckzahlen sind Dezimalstrings, Bruchteile ab 0.01 Kontrakt.

Drei bewusste Abweichungen vom Polymarket-Executor:

- **Keine `_budget_sync`-Ueberschreibung.** Dort ersetzte sie die korrekte
  Fill-Summe durch ein Kontostand-Delta, das Sekunden nach dem Fill noch
  stale war (PayPal 28.07.: `ausgegeben_usd 0.0` trotz 16.08 USD Fill).
- **Buchung aus `average_fill_price` und `average_fee_paid`.** Die
  V2-Antwort liefert beide, sobald etwas gefuellt wurde — der Einsatz ist
  damit gemessen statt geschaetzt.
- **FOK statt Level-Sweep.** Kalshi hat 1-Cent-Ticks und ein bekanntes
  bestes Level; eine Teilfuellung zu schlechteren Preisen ist hier weder
  noetig noch erwuenscht. Faellt die Order durch, greift der naechste
  Durchlauf mit frischem Buch.

Zugangsdaten kommen aus `.env` (`KALSHI_KEY_ID`, `KALSHI_PRIVATE_KEY_PFAD`)
und werden nie geloggt. Ohne `--live` und ohne Key passiert nichts.
"""

from __future__ import annotations

import base64
import math
import os
import time
import uuid
from pathlib import Path

from operations.pipeline import kalshi_client
from operations.pipeline.decision import Decision
from operations.pipeline.execution import ExecutorBase, PlacementResult

ORDER_PFAD = "/portfolio/events/orders"

# Kleinste handelbare Menge laut FixedPointCount (2 Nachkommastellen).
MIN_KONTRAKTE = 0.01


def lade_private_key(pfad: str | Path):
    """RSA-Private-Key aus PEM-Datei laden (nur lokal, nie geloggt)."""
    from cryptography.hazmat.primitives import serialization

    return serialization.load_pem_private_key(
        Path(pfad).read_bytes(), password=None
    )


def signatur(private_key, timestamp_ms: int, methode: str, pfad: str) -> str:
    """RSA-PSS/SHA-256 ueber `timestamp + METHODE + pfad`, Base64.

    Der Pfad wird OHNE Query-String signiert — Kalshi verwirft die
    Signatur sonst. Salt-Laenge ist die Digest-Laenge.
    """
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    nachricht = f"{timestamp_ms}{methode.upper()}{pfad}".encode()
    roh = private_key.sign(
        nachricht,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH,
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(roh).decode()


def auth_header(
    key_id: str, private_key, methode: str, pfad: str,
    timestamp_ms: int | None = None,
) -> dict:
    """Die drei Kalshi-Auth-Header fuer einen Request."""
    ts = timestamp_ms if timestamp_ms is not None else int(time.time() * 1000)
    return {
        "KALSHI-ACCESS-KEY": key_id,
        "KALSHI-ACCESS-TIMESTAMP": str(ts),
        "KALSHI-ACCESS-SIGNATURE": signatur(private_key, ts, methode, pfad),
    }


def ist_no(decision: Decision) -> bool:
    return (decision.outcome or "").strip().lower() == "no"


def yes_seiten_preis(decision: Decision) -> float:
    """Limitpreis in YES-Sicht — V2 quotiert nur diese Seite.

    `decision.limit_price` ist der Ask der gekauften Seite. Ein NO-Kauf zu
    0.19 ist ein YES-Verkauf zu 0.81.
    """
    preis = decision.limit_price or 0.0
    return round(1.0 - preis, 4) if ist_no(decision) else round(preis, 4)


def kontrakte_aus_usd(usd: float, preis: float) -> float:
    """Kontrakte, die inklusive Gebuehr in `usd` passen (2 Nachkommastellen).

    `preis` ist der Preis der gekauften Seite, nicht die YES-Sicht. Der
    Gebuehrenaufschlag muss in die Rechnung, sonst lehnt die Boerse die
    Order wegen Deckung ab — dieselbe Falle wie der 3%-Fee-Puffer auf der
    Polymarket-Seite (E280).
    """
    if preis <= 0:
        return 0.0
    je_kontrakt = preis + kalshi_client.gebuehr(preis)
    if je_kontrakt <= 0:
        return 0.0
    return math.floor(usd / je_kontrakt * 100) / 100


class KalshiDryRunExecutor(ExecutorBase):
    """Simuliert Fills zum Limitpreis, rechnet aber die echte Gebuehr mit."""

    def _platziere(
        self, decision: Decision, usd: float, shares: float
    ) -> PlacementResult:
        preis = decision.limit_price or 0.0
        kontrakte = kontrakte_aus_usd(usd, preis)
        if kontrakte < MIN_KONTRAKTE:
            return PlacementResult(
                decision.market_id, decision.action, decision.token_id,
                decision.limit_price, 0.0, 0.0, "skipped_size",
                f"usd {usd} reicht nicht fuer {MIN_KONTRAKTE} Kontrakte",
            )
        gebuehr = kalshi_client.gebuehr(preis) * kontrakte
        kosten = round(kontrakte * preis + gebuehr, 2)
        return PlacementResult(
            decision.market_id, decision.action, decision.token_id,
            decision.limit_price, kosten, kontrakte, "dry_run_fill",
            f"DRY_RUN: {kontrakte} Kontrakte zu {preis} "
            f"(YES-Seite {yes_seiten_preis(decision)}), "
            f"Gebuehr {round(gebuehr, 4)}",
        )


class KalshiExecutor(ExecutorBase):
    """Echte FOK-Orders ueber die Kalshi-REST-API (nur mit --live)."""

    def __init__(
        self, log_pfad: Path | None = None, basis: str = kalshi_client.BASIS_URL
    ) -> None:
        super().__init__(log_pfad)
        from dotenv import load_dotenv

        load_dotenv()
        self.basis = basis
        self.key_id = os.environ.get("KALSHI_KEY_ID") or ""
        key_pfad = os.environ.get("KALSHI_PRIVATE_KEY_PFAD") or ""
        if not self.key_id or not key_pfad:
            raise RuntimeError(
                "KALSHI_KEY_ID / KALSHI_PRIVATE_KEY_PFAD fehlen in .env — "
                "Live nicht moeglich"
            )
        if not Path(key_pfad).exists():
            raise RuntimeError(f"Kalshi-Private-Key nicht gefunden: {key_pfad}")
        self.private_key = lade_private_key(key_pfad)

    def _post(self, pfad: str, koerper: dict) -> dict:
        import httpx

        kopf = {
            **kalshi_client.HTTP_HEADERS,
            "Content-Type": "application/json",
            **auth_header(self.key_id, self.private_key, "POST", pfad),
        }
        resp = httpx.post(
            self.basis + pfad, json=koerper, headers=kopf, timeout=15.0
        )
        resp.raise_for_status()
        return resp.json()

    def _order_koerper(self, decision: Decision, kontrakte: float) -> dict:
        """FOK-Order im V2-Schema (alles aus YES-Sicht, Werte als Strings)."""
        return {
            "ticker": decision.token_id,
            "client_order_id": str(uuid.uuid4()),
            "side": "ask" if ist_no(decision) else "bid",
            "count": f"{kontrakte:.2f}",
            "price": f"{yes_seiten_preis(decision):.4f}",
            "time_in_force": "fill_or_kill",
            "self_trade_prevention_type": "taker_at_cross",
            "post_only": False,
        }

    def _platziere(
        self, decision: Decision, usd: float, shares: float
    ) -> PlacementResult:
        preis = decision.limit_price or 0.0
        kontrakte = kontrakte_aus_usd(usd, preis)
        if kontrakte < MIN_KONTRAKTE:
            return PlacementResult(
                decision.market_id, decision.action, decision.token_id,
                decision.limit_price, 0.0, 0.0, "skipped_size",
                f"usd {usd} reicht nicht fuer {MIN_KONTRAKTE} Kontrakte",
            )
        try:
            antwort = self._post(
                ORDER_PFAD, self._order_koerper(decision, kontrakte)
            )
        except Exception as ex:  # noqa: BLE001
            return PlacementResult(
                decision.market_id, decision.action, decision.token_id,
                decision.limit_price, 0.0, 0.0, "error", f"post_order: {ex}",
            )
        return ergebnis_aus_antwort(decision, antwort)


def ergebnis_aus_antwort(decision: Decision, antwort: dict) -> PlacementResult:
    """Buchung ausschliesslich aus der Orderantwort (kein Kontostand).

    `average_fill_price` steht in YES-Sicht — bei einem NO-Kauf ist der
    Einsatz je Kontrakt `1 - average_fill_price`. `average_fee_paid` ist
    die tatsaechlich belastete Gebuehr je Kontrakt und ersetzt unsere
    Formelschaetzung, sobald sie vorliegt.
    """
    z = kalshi_client.zahl
    order = antwort or {}
    gefuellt = z(order.get("fill_count")) or 0.0
    order_id = str(order.get("order_id") or "")[:14]
    if gefuellt <= 0:
        return PlacementResult(
            decision.market_id, decision.action, decision.token_id,
            decision.limit_price, 0.0, 0.0, "gave_up",
            f"FOK ohne Fill (order {order_id}, "
            f"rest {order.get('remaining_count')})",
        )

    yes_preis = z(order.get("average_fill_price"))
    if yes_preis is None:
        einsatz_je = decision.limit_price or 0.0
        preis_quelle = "limit_geschaetzt"
    else:
        einsatz_je = 1.0 - yes_preis if ist_no(decision) else yes_preis
        preis_quelle = "average_fill_price"

    gebuehr_je = z(order.get("average_fee_paid"))
    if gebuehr_je is None:
        gebuehr_je = kalshi_client.gebuehr(einsatz_je)
        gebuehr_quelle = "formel"
    else:
        gebuehr_quelle = "average_fee_paid"

    kosten = round(gefuellt * (einsatz_je + gebuehr_je), 2)
    return PlacementResult(
        decision.market_id, decision.action, decision.token_id,
        decision.limit_price, kosten, gefuellt, "live_fill",
        f"FOK {gefuellt} Kontrakte zu {round(einsatz_je, 4)} "
        f"[{preis_quelle}], Gebuehr {round(gebuehr_je, 4)}/Kontrakt "
        f"[{gebuehr_quelle}], order {order_id}",
    )


def baue_executor(live: bool, log_pfad: Path | None = None, demo: bool = False):
    """Executor je Betriebsart; ohne `live` wird nichts platziert."""
    if not live:
        return KalshiDryRunExecutor(log_pfad)
    basis = kalshi_client.DEMO_URL if demo else kalshi_client.BASIS_URL
    return KalshiExecutor(log_pfad, basis=basis)


__all__ = [
    "KalshiDryRunExecutor", "KalshiExecutor", "auth_header", "baue_executor",
    "ergebnis_aus_antwort", "ist_no", "kontrakte_aus_usd", "lade_private_key",
    "signatur", "yes_seiten_preis",
]
