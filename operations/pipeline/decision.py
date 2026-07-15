"""Asymmetrische Entscheidungsregeln fuer YES (live) und NO (final).

YES sofort, sobald der Zaehler die Schwelle plus Puffer erreicht (bei
Schwelle 1 reicht ein eindeutiger Treffer) und der beste Ask hoechstens
0.85 betraegt. NO erst nach vollstaendigem Transkript, wenn der Endstand
hoechstens 70% der Schwelle betraegt und der beste NO-Ask hoechstens 0.85
ist. Sonst kein Trade.
"""

from __future__ import annotations

from dataclasses import dataclass

from operations.pipeline import config
from operations.pipeline.market_rules import MarketRule


@dataclass
class Decision:
    market_id: str
    action: str          # "YES", "NO" oder "NONE"
    token_id: str | None
    outcome: str | None  # "Yes" / "No" / None
    limit_price: float | None
    reason: str


def _kein_trade(rule: MarketRule, grund: str) -> Decision:
    return Decision(rule.market_id, "NONE", None, None, None, grund)


def nach_edge_sortiert(kandidaten: list, ask_key=lambda k: k.get("best_ask")):
    """Kaufkandidaten nach bestem Ask AUFSTEIGEND (billigste zuerst).

    Bei gleichzeitig ausgeloesten Maerkten und knappem Pool holt der Bot
    so zuerst die Shares mit dem hoechsten Grenzgewinn je Dollar (die
    billigen Tranchen), statt in Listen-Reihenfolge (first-come) einen
    teuren Markt den Pool leerkaufen zu lassen. Kandidaten ohne Ask ans
    Ende. Stabil (gleiche Asks behalten ihre Reihenfolge)."""
    def schluessel(k):
        a = ask_key(k)
        return (a is None, a if a is not None else 1.0)

    return sorted(kandidaten, key=schluessel)


def entscheide_yes(rule: MarketRule, count: int, best_yes_ask: float | None) -> Decision:
    """Live-Entscheidung fuer YES waehrend des Streams."""
    if rule.status != "active":
        return _kein_trade(rule, f"skip:{rule.skip_grund}")
    ziel = 1 if rule.schwelle <= 1 else rule.schwelle + config.YES_SCHWELLE_PUFFER
    if count < ziel:
        return _kein_trade(rule, f"count {count} < ziel {ziel}")
    if best_yes_ask is None:
        return _kein_trade(rule, "kein_yes_ask")
    if best_yes_ask > config.ASK_OBERGRENZE:
        return _kein_trade(rule, f"yes_ask {best_yes_ask} > {config.ASK_OBERGRENZE}")
    return Decision(
        rule.market_id, "YES", rule.yes_token_id, "Yes", best_yes_ask,
        f"count {count} >= ziel {ziel}, ask {best_yes_ask} <= {config.ASK_OBERGRENZE}",
    )


def entscheide_no(rule: MarketRule, final_count: int, best_no_ask: float | None) -> Decision:
    """Finale Entscheidung fuer NO nach vollstaendigem Transkript."""
    if rule.status != "active":
        return _kein_trade(rule, f"skip:{rule.skip_grund}")
    grenze = config.NO_ANTEIL * rule.schwelle
    if final_count > grenze:
        return _kein_trade(rule, f"endstand {final_count} > grenze {grenze}")
    if best_no_ask is None:
        return _kein_trade(rule, "kein_no_ask")
    if best_no_ask > config.ASK_OBERGRENZE:
        return _kein_trade(rule, f"no_ask {best_no_ask} > {config.ASK_OBERGRENZE}")
    return Decision(
        rule.market_id, "NO", rule.no_token_id, "No", best_no_ask,
        f"endstand {final_count} <= grenze {grenze}, ask {best_no_ask} <= {config.ASK_OBERGRENZE}",
    )
