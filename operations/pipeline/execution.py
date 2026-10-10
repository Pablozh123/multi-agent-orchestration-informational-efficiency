"""Order-Ausfuehrung: Dry-Run-Standard, Live nur mit --live und Key.

Regeln:
- Nur Limit-Orders zum gesehenen besten Ask.
- Groesse = min(ausfuehrbare Tiefe, MAX_USD_PRO_MARKT, Restbudget).
- MAX_USD_GESAMT als Gesamtlimit im Standardpfad; All-In opt-in nutzt das Wallet.
- Maximal MAX_NACHBESSERUNGEN Nachbesserungen, danach aufgeben.
- Jede Entscheidung wird mit Orderbuch-Snapshot als JSONL geloggt.
- Kill-Switch: existiert data/live/STOP, wird nichts mehr platziert.

Dry-Run simuliert einen vollstaendigen Fill zum Limitpreis (dokumentierte
Annahme fuer die spaetere Auswertung). Live-Ausfuehrung laeuft ueber
py-clob-client; der private Key kommt aus .env (POLY_PRIVATE_KEY) und wird
nie geloggt.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Condition, Lock, RLock

from operations.pipeline import config
from operations.pipeline.decision import Decision
from operations.pipeline.orderbook import ausfuehrbare_tiefe_usd


@dataclass
class PlacementResult:
    market_id: str
    action: str
    token_id: str | None
    limit_price: float | None
    size_usd: float
    size_shares: float
    status: str  # "dry_run_fill", "live_fill", "live_partial", "gave_up",
    #              "skipped_budget", "skipped_stop", "skipped_size", "error"
    detail: str = ""


def preis_deckel_fuer(outcome: str | None) -> float:
    """FAK-Preisdeckel je Seite: NO niedriger als YES (E281-Lehre).

    Der Deckel muss auch in der AUSFUEHRUNG gelten, nicht nur in der
    Entscheidung: entscheide_no prueft nur den besten Ask beim Einstieg,
    der Level-Sweep fuellte danach aber bis ASK_OBERGRENZE (0.90) nach —
    fuer NO-Orders am 0.80-Deckel vorbei (Review-Befund 18.07.).
    """
    if (outcome or "").strip().lower() == "no":
        return config.NO_ASK_OBERGRENZE
    return config.ASK_OBERGRENZE


def berechne_groesse(
    book: dict, limit_price: float, budget_rest: float
) -> tuple[float, float]:
    """(USD, Shares) fuer die Order: min(Tiefe, Marktlimit, Restbudget)."""
    tiefe = ausfuehrbare_tiefe_usd(book, limit_price)
    usd = min(tiefe, config.MAX_USD_PRO_MARKT, max(budget_rest, 0.0))
    usd = round(usd, 2)
    shares = round(usd / limit_price, 2) if limit_price > 0 else 0.0
    return usd, shares


def fill_aus_antwort(
    antwort: dict | None, status: dict | None, fallback_preis: float | None
) -> tuple[float, float, str]:
    """(Shares, USD, Quelle) eines FAK-BUY-Clips.

    Prioritaet: takingAmount/makingAmount der Post-Antwort — die exakten
    Fill-Werte (BUY: taking = erhaltene Shares, making = bezahlte USDC).
    Fallback: size_matched des Order-Status, bewertet zum besten Ask am
    Entscheid (fallback_preis). status['price'] ist bewusst KEINE Quelle:
    es ist der Order-Deckel, nicht der Fill-Preis — der Wallet-Abgleich
    vom 18.07. zeigte dadurch ueberschaetzte Einsaetze (E281: 360 statt
    288 USD). Die Quelle wird geloggt, damit Abgleiche sie pruefen koennen.
    """

    def _f(wert: object) -> float:
        try:
            return float(wert or 0)
        except (TypeError, ValueError):
            return 0.0

    taking = _f((antwort or {}).get("takingAmount"))
    making = _f((antwort or {}).get("makingAmount"))
    if taking > 0 and making > 0:
        return round(taking, 2), round(making, 2), "post_antwort"
    gefuellt = _f((status or {}).get("size_matched"))
    preis = _f(fallback_preis)
    return round(gefuellt, 2), round(gefuellt * preis, 2), "status_geschaetzt"


class ExecutorBase:
    """Gemeinsame Logik: Budget, Kill-Switch, Entscheidungslog."""

    nutzt_markt_orders = False

    def __init__(self, log_pfad: Path | None = None) -> None:
        self.log_pfad = log_pfad or (config.LIVE_DIR / "decisions_log.jsonl")
        self.log_pfad.parent.mkdir(parents=True, exist_ok=True)
        self.ausgegeben_usd = 0.0
        self._log_lock = Lock()
        self._place_lock = RLock()

    def _stop_aktiv(self) -> bool:
        abort = getattr(self, "abort_event", None)
        return config.STOP_FILE.exists() or (abort is not None and abort.is_set())

    def _log(self, decision: Decision, book: dict, result: PlacementResult) -> None:
        eintrag = {
            "wall_ts_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "decision": asdict(decision),
            "result": asdict(result),
            "book_snapshot": {
                "asks": (book.get("asks") or [])[:10],
                "bids": (book.get("bids") or [])[:10],
                "timestamp": book.get("timestamp"),
                "min_order_size": book.get("min_order_size"),
                "neg_risk": book.get("neg_risk"),
            },
        }
        with self._log_lock, open(self.log_pfad, "a", encoding="utf-8") as f:
            f.write(json.dumps(eintrag, ensure_ascii=False) + "\n")

    def place(self, decision: Decision, book: dict) -> PlacementResult:
        if decision.action == "NONE" or decision.token_id is None:
            result = PlacementResult(
                decision.market_id, decision.action, decision.token_id,
                decision.limit_price, 0.0, 0.0, "no_action", decision.reason,
            )
            self._log(decision, book, result)
            return result
        if self._stop_aktiv():
            result = PlacementResult(
                decision.market_id, decision.action, decision.token_id,
                decision.limit_price, 0.0, 0.0, "skipped_stop",
                "Kill-Switch data/live/STOP aktiv",
            )
            self._log(decision, book, result)
            return result

        budget_rest = config.MAX_USD_GESAMT - self.ausgegeben_usd
        if self.nutzt_markt_orders:
            # FAK-Market-Order mit Preisdeckel limitiert sich selbst auf die
            # verfuegbare Tiefe; keine Depth-Berechnung noetig.
            usd = round(min(config.MAX_USD_PRO_MARKT, max(budget_rest, 0.0)), 2)
            shares = round(usd / decision.limit_price, 2) if decision.limit_price else 0.0
        else:
            usd, shares = berechne_groesse(book, decision.limit_price, budget_rest)
        if usd <= 0 or shares <= 0:
            result = PlacementResult(
                decision.market_id, decision.action, decision.token_id,
                decision.limit_price, 0.0, 0.0, "skipped_budget",
                f"budget_rest={round(budget_rest, 2)}, tiefe unzureichend",
            )
            self._log(decision, book, result)
            return result

        if usd < 1.0:  # Server-Minimum: marketable BUY braucht >= 1 USD
            result = PlacementResult(
                decision.market_id, decision.action, decision.token_id,
                decision.limit_price, usd, shares, "skipped_size",
                f"usd {usd} unter Server-Minimum 1 USD",
            )
            self._log(decision, book, result)
            return result
        min_size = float(book.get("min_order_size") or 0)
        if not self.nutzt_markt_orders and shares < min_size:
            result = PlacementResult(
                decision.market_id, decision.action, decision.token_id,
                decision.limit_price, usd, shares, "skipped_size",
                f"shares {shares} < min_order_size {min_size}",
            )
            self._log(decision, book, result)
            return result

        result = self._platziere(decision, usd, shares)
        if result.status in ("dry_run_fill", "live_fill", "live_partial"):
            self.ausgegeben_usd = round(self.ausgegeben_usd + result.size_usd, 2)
        # Live: Schaetzung durch echten Wallet-Stand ersetzen (Lehre aus dem
        # IPO-Sweep 10.7.: Deckelpreis-Schaetzung ueberzeichnete das Budget
        # und blockierte fuenf berechtigte Folgetrades).
        self._budget_sync()
        self._log(decision, book, result)
        return result

    def _budget_sync(self) -> None:
        """Basisklasse: keine echte Wallet-Anbindung."""

    def _platziere(
        self, decision: Decision, usd: float, shares: float
    ) -> PlacementResult:
        raise NotImplementedError


class DryRunExecutor(ExecutorBase):
    """Simuliert Fills zum Limitpreis (Annahme fuer die Auswertung)."""

    def place(self, decision: Decision, book: dict) -> PlacementResult:
        with self._place_lock:
            return super().place(decision, book)

    def _platziere(
        self, decision: Decision, usd: float, shares: float
    ) -> PlacementResult:
        return PlacementResult(
            decision.market_id, decision.action, decision.token_id,
            decision.limit_price, usd, shares, "dry_run_fill",
            "DRY_RUN: angenommener Fill zum Limitpreis",
        )


def baue_live_client():
    """CLOB-V2-Client im Deposit-Wallet-Modus (POLY_1271 + funder).

    Voraussetzung: operations.pipeline.setup_deposit_wallet wurde einmalig
    ausgefuehrt (Deposit-Wallet deployed, pUSD transferiert, Approvals).
    """
    import json as _json
    import os

    from dotenv import load_dotenv
    from py_clob_client_v2 import SignatureTypeV2
    from py_clob_client_v2.client import ClobClient

    load_dotenv()
    key = os.environ.get("POLY_PRIVATE_KEY")
    if not key:
        raise RuntimeError("POLY_PRIVATE_KEY fehlt in .env — Live nicht moeglich")
    # Profilunabhaengig: eine Deposit-Wallet fuer alle Events.
    wallet_json = config.REPO_ROOT / "data" / "live" / "deposit_wallet.json"
    if not wallet_json.exists():
        raise RuntimeError(
            "deposit_wallet.json fehlt — zuerst "
            "python -m operations.pipeline.setup_deposit_wallet ausfuehren"
        )
    with open(wallet_json, encoding="utf-8") as f:
        funder = _json.load(f)["deposit_wallet"]
    client = ClobClient(
        config.CLOB_HOST, key=key, chain_id=config.CHAIN_ID,
        signature_type=SignatureTypeV2.POLY_1271, funder=funder,
    )
    client.set_api_creds(client.create_or_derive_api_key())
    return client, funder


class OrderNotSent(RuntimeError):
    """Signing/STOP failed before a request could reach the exchange."""


class WalletBudget:
    """One in-process wallet, conservative fee reserve, no stale-cache refunds."""

    def __init__(self, balance: float | None) -> None:
        self._condition = Condition()
        self._remaining = self._valid_balance(balance)
        self._holds: dict[int, tuple[float, float]] = {}
        self._working: set[int] = set()
        self._next = 0
        self.spent_usd = 0.0

    @staticmethod
    def _valid_balance(value):
        if value is None:
            return None
        value = float(value)
        if not math.isfinite(value) or value < 0:
            raise ValueError("invalid wallet balance")
        return value

    @property
    def available(self) -> float:
        with self._condition:
            return max(0.0, (self._remaining or 0)-sum(h[1] for h in self._holds.values()))

    def reserve(self) -> tuple[int, float] | None:
        with self._condition:
            usd = math.floor(min(config.MAX_USD_PRO_MARKT, self.available*0.97)*100)/100
            if usd < 1:
                return None
            self._next += 1
            hold = min(self.available, math.ceil(usd/0.97*100)/100)
            self._holds[self._next] = (usd, hold)
            self._working.add(self._next)
            return self._next, usd

    def settle(self, ticket: int, spent: float) -> None:
        with self._condition:
            usd, hold = self._holds[ticket]
            if not math.isfinite(spent) or not 0 <= spent <= usd+0.01:
                raise ValueError("fill outside reserved amount")
            self._remaining = max(0.0, self._remaining-min(hold, math.ceil(spent/0.97*100)/100))
            self.spent_usd = round(self.spent_usd+spent, 2)
            del self._holds[ticket]
            self._working.discard(ticket)
            self._condition.notify_all()

    def pending(self, ticket: int) -> None:
        with self._condition:
            self._working.discard(ticket)  # hold stays until terminal confirmation
            self._condition.notify_all()

    def wait_for_settlement(self) -> bool:
        with self._condition:
            if not self._working:
                return False
            self._condition.wait(timeout=0.05)
            return True

    def refresh(self, balance: float | None) -> None:
        balance = self._valid_balance(balance)
        with self._condition:
            if balance is not None and not self._holds:
                self._remaining = (balance if self._remaining is None or self.spent_usd == 0
                                   else min(self._remaining, balance))


class LiveExecutor(ExecutorBase):
    """Echte FAK-Market-Orders ueber py-clob-client-v2 (nur mit --live).

    Deposit-Wallet-Flow (Pflicht seit CLOB V2): Orders werden mit
    POLY_1271 signiert, Collateral ist pUSD auf der Deposit-Wallet.
    Market-Order (FAK) mit seitenabhaengigem Preisdeckel (YES
    ASK_OBERGRENZE, NO NO_ASK_OBERGRENZE): fuellt sofort alles bis zum
    Deckel, Rest verfaellt. Maximal eine Wiederholung, falls nichts
    gefuellt wurde und der Ask wieder unter dem Deckel liegt.
    """

    nutzt_markt_orders = True

    def __init__(self, log_pfad: Path | None = None) -> None:
        super().__init__(log_pfad)
        from py_clob_client_v2 import (
            AssetType,
            BalanceAllowanceParams,
            SignatureTypeV2,
        )

        self.client, self.funder = baue_live_client()
        # Server-seitigen Balance/Allowance-Cache aktualisieren.
        self.client.update_balance_allowance(
            BalanceAllowanceParams(
                asset_type=AssetType.COLLATERAL,
                signature_type=SignatureTypeV2.POLY_1271,
            )
        )
        self._start_balance = self._wallet_balance()

    def prepare_markets(self, rules) -> dict:
        """Populate SDK token/tick/fee context before waiting for the drop."""
        prepared, errors = [], []
        for token in dict.fromkeys(
            token for rule in rules
            for token in (rule.yes_token_id, rule.no_token_id) if token
        ):
            try:
                self.client.get_fee_exponent(token)
                prepared.append(token)
            except Exception as exc:
                errors.append({"token": token, "error": str(exc)[:160]})
        return {"prepared_tokens": len(prepared), "errors": errors}

    def enable_wallet_budget(self) -> None:
        """Opt-in for All-In. Other profiles retain their configured budget."""
        self.wallet_budget = WalletBudget(self._start_balance)
        self._wallet_lock = RLock()
        self._pending_orders = {}
        self._next_balance_refresh = 0.0

    def place(self, decision: Decision, book: dict) -> PlacementResult:
        if not hasattr(self, "wallet_budget") or decision.action == "NONE":
            return super().place(decision, book)
        result = self._place_wallet(decision, book)
        self._log(decision, book, result)
        return result

    def _settle_wallet(self, ticket: int, spent: float) -> None:
        with self._wallet_lock:
            self.wallet_budget.settle(ticket, spent)
            self.ausgegeben_usd = self.wallet_budget.spent_usd

    @staticmethod
    def _terminal_status(status: dict, cap: float):
        if str(status.get("status", "")).upper() not in {"MATCHED", "FILLED", "CANCELED", "CANCELLED", "EXPIRED"}:
            return None
        raw = status.get("size_matched")
        if raw is None:
            return None
        shares = float(raw)
        if not math.isfinite(shares) or shares < 0:
            raise ValueError("invalid matched size")
        return round(shares, 2), round(shares*cap, 2)

    def _wallet_clip(self, d: Decision, usd: float):
        cap = preis_deckel_fuer(d.outcome)
        answer = self._bestell(d.token_id, usd, cap)
        order_id = answer.get("orderID") or answer.get("orderId") or ""
        if answer.get("success") is False:
            return 0.0, 0.0, order_id, True, "rejected"
        try:
            taking, making = float(answer.get("takingAmount") or 0), float(answer.get("makingAmount") or 0)
            if not all(math.isfinite(v) and v >= 0 for v in (taking, making)):
                raise ValueError("invalid post fill")
        except (ValueError, TypeError):
            return 0.0, 0.0, order_id, False, "invalid post fill"
        if taking > 0 and making > 0 and str(answer.get("status", "")).lower() not in {"delayed", "live", "pending"}:
            return round(taking, 2), round(making, 2), order_id, True, "post_antwort"
        if order_id:
            try:
                terminal = self._terminal_status(self._order_status(order_id), cap)
            except Exception:
                terminal = None
            if terminal is not None:
                shares, estimate = terminal
                return shares, min(usd, estimate), order_id, True, "status_cap_estimate"
        return 0.0, 0.0, order_id, False, "pending"

    def _place_wallet(self, d: Decision, book: dict) -> PlacementResult:
        from operations.pipeline.orderbook import best_ask

        shares_total = usd_total = 0.0
        attempts = empty = 0
        status, detail = "gave_up", "no executable asks"
        while not self._stop_aktiv():
            try:
                current = self.book_source(d.token_id)
                ask = best_ask(current)
            except Exception as exc:
                detail = f"book unavailable: {exc}"
                break
            if ask is None or ask > preis_deckel_fuer(d.outcome):
                break
            reserved = self.wallet_budget.reserve()
            if reserved is None:
                if self.wallet_budget.wait_for_settlement():
                    continue
                status, detail = "skipped_budget", "wallet fully spent or reserved"
                break
            ticket, usd = reserved
            if self._stop_aktiv():
                self._settle_wallet(ticket, 0)
                status = "skipped_stop"
                break
            order_id = ""
            try:
                shares, cost, order_id, terminal, source = self._wallet_clip(d, usd)
                if terminal:
                    self._settle_wallet(ticket, cost)
                else:
                    self.wallet_budget.pending(ticket)
            except OrderNotSent as exc:
                self._settle_wallet(ticket, 0)
                status, detail = ("skipped_stop" if self._stop_aktiv() else "error"), str(exc)
                break
            except Exception as exc:
                self.wallet_budget.pending(ticket)
                shares, cost, terminal, source = 0.0, 0.0, False, str(exc)
            attempts += 1
            if not terminal:
                with self._wallet_lock:
                    self._pending_orders[ticket] = (d, order_id, book, usd)
                status, detail = "pending_confirmation", f"reservation retained; order={order_id}; {source}"
                break
            shares_total += shares
            usd_total += cost
            detail = f"{attempts} FAK clips; last fill source={source}"
            empty = empty+1 if shares <= 0 else 0
            if empty > config.MAX_NACHBESSERUNGEN:
                break
        else:
            status = "skipped_stop"
        if shares_total > 0 and status != "pending_confirmation":
            status = "live_fill"
        return PlacementResult(d.market_id, d.action, d.token_id, d.limit_price,
                               round(usd_total, 2), round(shares_total, 2), status, detail)

    def reconcile_wallet(self) -> list[PlacementResult]:
        """Off the audio path. Unknown posts keep their reservation."""
        resolved = []
        with self._wallet_lock:
            pending = list(self._pending_orders.items())
        for ticket, (d, order_id, book, usd) in pending:
            if not order_id:
                continue
            try:
                terminal = self._terminal_status(self._order_status(order_id), preis_deckel_fuer(d.outcome))
                if terminal is None:
                    continue
                shares, estimate = terminal
                cost = min(usd, estimate)
                with self._wallet_lock:
                    if ticket not in self._pending_orders:
                        continue
                    self._settle_wallet(ticket, cost)
                    del self._pending_orders[ticket]
                result = PlacementResult(d.market_id, d.action, d.token_id, d.limit_price,
                                         cost, shares, "live_fill" if shares else "gave_up",
                                         f"reconciled {order_id}; cost bounded by price cap")
                self._log(d, book, result)
                resolved.append(result)
            except Exception:
                continue  # keep reservation when confirmation is unavailable
        if time.monotonic() < self._next_balance_refresh:
            return resolved
        self._next_balance_refresh = time.monotonic() + 5
        with self._wallet_lock:
            spent_before_read = self.ausgegeben_usd
        balance = self._wallet_balance()
        with self._wallet_lock:
            # A fill completed while the snapshot was in flight. Subtract it
            # even if the server snapshot may already include it, never refund it.
            delta = self.ausgegeben_usd-spent_before_read
            adjusted = max(0.0, balance-delta/0.97) if balance is not None else None
            self.wallet_budget.refresh(adjusted)
        return resolved

    def _wallet_balance(self) -> float | None:
        """Aktuelles pUSD-Guthaben der Deposit-Wallet (Server-Sicht)."""
        from py_clob_client_v2 import (
            AssetType,
            BalanceAllowanceParams,
            SignatureTypeV2,
        )

        try:
            params = BalanceAllowanceParams(
                asset_type=AssetType.COLLATERAL,
                signature_type=SignatureTypeV2.POLY_1271,
            )
            self.client.update_balance_allowance(params)
            antwort = self.client.get_balance_allowance(params)
            roh = antwort.get("balance") if isinstance(antwort, dict) else None
            return round(int(roh) / 1e6, 2) if roh is not None else None
        except Exception:  # noqa: BLE001 - Fallback auf Schaetzung
            return None

    def _budget_sync(self) -> None:
        """Setzt die Ausgaben auf das echte Wallet-Delta (statt Schaetzung)."""
        if self._start_balance is None:
            return
        aktuell = self._wallet_balance()
        if aktuell is not None:
            self.ausgegeben_usd = round(self._start_balance - aktuell, 2)

    def _bestell(self, token_id: str, usd: float, preis_deckel: float) -> dict:
        """FAK-Market-Order: Betrag in USD, Preisdeckel je Seite."""
        from py_clob_client_v2 import MarketOrderArgsV2
        from py_clob_client_v2.clob_types import OrderType
        from py_clob_client_v2.order_builder.constants import BUY

        try:
            order = self.client.create_market_order(
                MarketOrderArgsV2(
                    token_id=token_id, amount=usd, side=BUY,
                    price=preis_deckel, order_type=OrderType.FAK,
                )
            )
        except Exception as exc:
            raise OrderNotSent(f"order not signed: {exc}") from exc
        if self._stop_aktiv():
            raise OrderNotSent("STOP before post_order")
        try:
            return self.client.post_order(order, OrderType.FAK)
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            if isinstance(status, int) and status in {400, 401, 403, 404, 422}:
                raise OrderNotSent(f"order rejected ({status}): {exc}") from exc
            raise

    def _order_status(self, order_id: str) -> dict:
        return self.client.get_order(order_id)

    def _cancel(self, order_id: str) -> None:
        from py_clob_client_v2.clob_types import OrderPayload

        self.client.cancel_order(OrderPayload(orderID=order_id))

    def _ein_clip(
        self, decision: Decision, usd: float
    ) -> tuple[float, float, str, str]:
        """Ein FAK-Clip; liefert (Shares, USD, order_id, Fill-Quelle)."""
        import time

        antwort = self._bestell(
            decision.token_id, usd, preis_deckel_fuer(decision.outcome)
        )
        order_id = antwort.get("orderID") or antwort.get("orderId") or ""
        gefuellt, usd_eff, quelle = fill_aus_antwort(
            antwort, None, decision.limit_price
        )
        if quelle == "post_antwort":
            return gefuellt, usd_eff, order_id, quelle
        time.sleep(2)  # FAK ist sofort terminal
        try:
            status = self._order_status(order_id) if order_id else {}
        except Exception:  # noqa: BLE001
            status = {}
        gefuellt, usd_eff, quelle = fill_aus_antwort(
            None, status, decision.limit_price
        )
        return gefuellt, usd_eff, order_id, quelle

    def _platziere(
        self, decision: Decision, usd: float, shares: float
    ) -> PlacementResult:
        """Level-Sweep: wiederholte FAK-Clips (je MAX_USD_PRO_MARKT), bis der
        beste Ask ueber dem Seiten-Deckel liegt (YES 0.90 / NO 0.80),
        nichts mehr fuellt oder der Gesamtpool erschoepft ist."""
        from operations.pipeline.orderbook import best_ask, fetch_book

        deckel = preis_deckel_fuer(decision.outcome)
        summe_shares = 0.0
        summe_usd = 0.0
        clips: list[str] = []
        leere_versuche = 0

        for _ in range(config.MAX_CLIPS_PRO_MARKT):
            budget_rest = (config.MAX_USD_GESAMT - self.ausgegeben_usd
                           - summe_usd)
            # 3% Fee-Puffer: Server lehnt Orders ab, deren Betrag plus
            # Gebuehrenschaetzung das Guthaben uebersteigt (E280-Befund:
            # 5 NO-Chancen verloren bei Clip 15.00 auf Guthaben 15.01).
            clip_usd = round(min(config.MAX_USD_PRO_MARKT,
                                 budget_rest * 0.97), 2)
            if clip_usd < 1.0 or self._stop_aktiv():
                break
            try:
                gefuellt, usd_eff, order_id, quelle = self._ein_clip(
                    decision, clip_usd
                )
            except Exception as ex:  # noqa: BLE001
                if not clips:
                    return PlacementResult(
                        decision.market_id, decision.action, decision.token_id,
                        decision.limit_price, 0.0, 0.0, "error",
                        f"post_order: {ex}",
                    )
                break
            clips.append(
                f"{order_id[:14]}:{gefuellt}sh/{usd_eff}$[{quelle}]"
            )
            summe_shares += gefuellt
            summe_usd += usd_eff
            if gefuellt <= 0:
                leere_versuche += 1
                if leere_versuche > config.MAX_NACHBESSERUNGEN:
                    break
            else:
                leere_versuche = 0
            # Naechstes Level pruefen: nur weiter, wenn wieder Ware unter
            # dem Deckel liegt.
            try:
                source = getattr(self, "book_source", fetch_book)
                neuer_ask = best_ask(source(decision.token_id))
            except Exception:  # noqa: BLE001
                break
            if neuer_ask is None or neuer_ask > deckel:
                break

        summe_usd = round(summe_usd, 2)
        if summe_shares > 0:
            return PlacementResult(
                decision.market_id, decision.action, decision.token_id,
                decision.limit_price, summe_usd, round(summe_shares, 2),
                "live_fill",
                f"Sweep: {len(clips)} Clips, {clips}",
            )
        return PlacementResult(
            decision.market_id, decision.action, decision.token_id,
            decision.limit_price, 0.0, 0.0, "gave_up",
            f"Sweep ohne Fill ({len(clips)} Clips): {clips}",
        )
