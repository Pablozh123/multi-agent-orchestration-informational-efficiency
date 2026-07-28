"""Entscheidungsregeln fuer Kalshi — Gebuehren und Verschreibungsfilter.

Zwei Aufsaetze auf `decision.py`, beide aus den Venue-Unterschieden
(`docs/project/KALSHI_MENTIONS_ANALYSE_2026-07-29.md` §2/§3):

1. **Gebuehren.** Kalshi nimmt Taker `ceil(0.07*P*(1-P)*100)/100` je
   Kontrakt — auf Polymarket war der Handel kostenlos. Das Maximum von
   1.75 Cent liegt bei P = 0.50, also genau im Zweifel-Fenster, aus dem
   ALLE vier bisherigen Fills der Polymarket-Strecke kamen. Der Deckel
   muss darum auf den Vollpreis (Ask + Gebuehr) gelten, nicht auf den Ask.

2. **Verschreibungsfilter fuer NO.** Kalshi loest primaer per Video auf.
   Ein Transkriptfehler zaehlt dort also gegen uns — und genau der ist
   uns am 28.07. zweimal passiert: das Boeing-Band schrieb "the guides
   that we have", gesagt war sehr wahrscheinlich "guidance"; im
   PayPal-Band stand "agent e-commerce" fuer "agentic commerce". Beide
   Maerkte loesten YES auf, waehrend unser Vollpass 0 zaehlte.

   Der Filter blockt ein NO, sobald das Transkript ein Wort enthaelt, das
   sich mit dem Zielwort einen Stamm teilt, ohne selbst ein Treffer zu
   sein. Er ist bewusst nur eine NO-Sperre: er kann einen berechtigten
   NO-Kauf verhindern (Kosten: entgangener Gewinn), aber niemals einen
   Kauf ausloesen (Kosten: echter Verlust).
"""

from __future__ import annotations

import re

from operations.pipeline import config, kalshi_client
from operations.pipeline.counter_engine import compile_patterns, count_in_text
from operations.pipeline.decision import Decision, _kein_trade, no_sperre
from operations.pipeline.market_rules import MarketRule

# Ab wie vielen gemeinsamen Anfangsbuchstaben ein Transkriptwort als
# moegliche Verschreibung des Zielworts gilt. Vier deckt die beiden
# belegten Faelle ab (guidance/guide teilen "guid", agentic/agent teilen
# "agen") und liegt ueber der Laenge, ab der zufaellige Gleichanfaenge
# haeufig werden. Kuerzere Zielwoerter werden nicht geprueft.
STAMM_MIN = 4

_WORT = re.compile(r"[A-Za-z][A-Za-z'’]*")


def vollpreis(ask: float) -> float:
    """Ask plus Taker-Gebuehr — der Preis, den wir tatsaechlich zahlen."""
    return round(ask + kalshi_client.gebuehr(ask), 4)


def deckel_erreicht(ask: float, obergrenze: float) -> bool:
    """Liegt der Vollpreis ueber der Obergrenze?

    Auf Polymarket wurde der rohe Ask gegen die Grenze geprueft. Auf
    Kalshi zahlt ein Kauf zu 0.89 effektiv 0.90 — der Deckel muss den
    Aufschlag sehen, sonst kauft der Bot systematisch einen Cent zu teuer.
    """
    return vollpreis(ask) > obergrenze + 1e-9


def _stamm_kandidaten(varianten: list[str]) -> list[str]:
    """Zielwortstaemme, gegen die das Transkript geprueft wird."""
    staemme = []
    for variante in varianten:
        for wort in _WORT.findall(variante):
            if len(wort) >= STAMM_MIN + 1:  # Stamm muss echt kuerzer sein
                staemme.append(wort.lower())
    return staemme


def nachbar_verdacht(varianten: list[str], transkript: str) -> list[str]:
    """Transkriptwoerter, die Verschreibungen des Zielworts sein koennen.

    Ein Wort gilt als verdaechtig, wenn es mit einem Zielwort mindestens
    STAMM_MIN Anfangsbuchstaben teilt, selbst aber kein gezaehlter Treffer
    ist. "guides" gegen "guidance" schlaegt an, "guidance" selbst nicht
    (das waere ein Treffer und damit YES-Sache).
    """
    if not varianten or not transkript:
        return []
    treffer_muster = compile_patterns(varianten)
    staemme = _stamm_kandidaten(varianten)
    if not staemme:
        return []
    verdaechtig: list[str] = []
    for wort in _WORT.findall(transkript):
        klein = wort.lower()
        if any(klein == s for s in staemme):
            continue  # exaktes Zielwort -> Treffer, nicht Verdacht
        if count_in_text(wort, treffer_muster):
            continue  # zaehlt bereits als Variante (Plural/Genitiv)
        for stamm in staemme:
            gemeinsam = 0
            for a, b in zip(klein, stamm):
                if a != b:
                    break
                gemeinsam += 1
            if gemeinsam >= STAMM_MIN and klein != stamm:
                if wort not in verdaechtig:
                    verdaechtig.append(wort)
                break
    return verdaechtig


def entscheide_yes(
    rule: MarketRule, count: int, best_yes_ask: float | None
) -> Decision:
    """YES live, mit Gebuehr im Deckel. Schwelle ist auf Kalshi immer 1."""
    if rule.status != "active":
        return _kein_trade(rule, f"skip:{rule.skip_grund}")
    if count < 1:
        return _kein_trade(rule, f"count {count} < 1")
    if best_yes_ask is None:
        return _kein_trade(rule, "kein_yes_ask")
    if deckel_erreicht(best_yes_ask, config.ASK_OBERGRENZE):
        return _kein_trade(
            rule,
            f"vollpreis {vollpreis(best_yes_ask)} (ask {best_yes_ask} + "
            f"gebuehr) > {config.ASK_OBERGRENZE}",
        )
    return Decision(
        rule.market_id, "YES", rule.yes_token_id, "Yes", best_yes_ask,
        f"count {count} >= 1, vollpreis {vollpreis(best_yes_ask)} "
        f"<= {config.ASK_OBERGRENZE}",
    )


def entscheide_no(
    rule: MarketRule,
    final_count: int,
    best_no_ask: float | None,
    transkript: str = "",
) -> Decision:
    """NO nach vollstaendigem Transkript — mit Gebuehr und Nachbarfilter.

    `transkript` ist der VAD-freie Vollpass. Fehlt er, gibt es kein NO:
    ohne Nachbarschaftspruefung ist die Abwesenheit auf einer
    video-aufgeloesten Venue nicht belegbar (Lehre vom 28.07.).
    """
    if rule.status != "active":
        return _kein_trade(rule, f"skip:{rule.skip_grund}")
    sperre = no_sperre(rule)
    if sperre is not None:
        return _kein_trade(rule, sperre)
    if final_count > 0:
        return _kein_trade(rule, f"endstand {final_count} > 0")
    if not transkript.strip():
        return _kein_trade(rule, "kein_vollpass_transkript")
    verdacht = nachbar_verdacht(rule.varianten, transkript)
    if verdacht:
        return _kein_trade(
            rule, f"verschreibungs_verdacht {verdacht[:5]}"
        )
    if best_no_ask is None:
        return _kein_trade(rule, "kein_no_ask")
    if deckel_erreicht(best_no_ask, config.NO_ASK_OBERGRENZE):
        return _kein_trade(
            rule,
            f"vollpreis {vollpreis(best_no_ask)} > {config.NO_ASK_OBERGRENZE}",
        )
    return Decision(
        rule.market_id, "NO", rule.no_token_id, "No", best_no_ask,
        f"endstand 0, kein Nachbarverdacht, vollpreis "
        f"{vollpreis(best_no_ask)} <= {config.NO_ASK_OBERGRENZE}",
    )
