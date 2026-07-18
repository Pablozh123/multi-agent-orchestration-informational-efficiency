"""Marktregeln aus Gamma question und description ableiten.

Je Markt werden die zu zaehlenden Wortvarianten, die Schwelle und die
YES/NO-Token bestimmt. Unklare Regeln fuehren zu Status SKIP, damit der
Bot solche Maerkte nicht handelt.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from operations.pipeline import config

# Zitierte Begriffe in Gamma-Fragen stehen in geraden oder typografischen
# Anfuehrungszeichen: Will "Microsoft" be said ...
_ZITAT = re.compile(r"[\"“”‘’]([^\"“”‘’]+)[\"“”‘’]")
_SCHWELLE = re.compile(r"(\d+)\s*\+?\s*times", re.IGNORECASE)


@dataclass
class MarketRule:
    market_id: str
    slug: str
    question: str
    varianten: list[str]
    schwelle: int
    yes_token_id: str | None
    no_token_id: str | None
    homophon_sensitiv: bool
    status: str = "active"  # "active" oder "skip"
    skip_grund: str = ""
    resolution_hinweis: str = ""
    extra: dict = field(default_factory=dict)
    # Wort steht im festen Intro/Outro der Show -> nie NO (E281-Lehre).
    boilerplate_sensitiv: bool = False
    # YES-Quote des Worts in aufgeloesten Wochen der Serie (None = keine
    # Historie) und Anzahl aufgeloester Wochen; siehe basisraten.py.
    basisrate: float | None = None
    basis_n: int = 0


def parse_zitierte_begriffe(question: str) -> list[str]:
    """Alle zitierten Begriffe der Frage, Reihenfolge erhalten."""
    return [m.strip() for m in _ZITAT.findall(question) if m.strip()]


def parse_schwelle(question: str) -> int:
    """Schwelle N aus 'N+ times'; Default 1, wenn keine Angabe."""
    treffer = _SCHWELLE.search(question)
    if treffer:
        return int(treffer.group(1))
    return 1


def expandiere_varianten(begriff: str) -> list[str]:
    """Wortvarianten eines Begriffs (bekannte Map, sonst Begriff selbst)."""
    schluessel = begriff.strip().lower()
    if schluessel in config.VARIANTEN_MAP:
        return list(config.VARIANTEN_MAP[schluessel])
    return [begriff.strip()]


def _ist_homophon(begriffe: list[str]) -> bool:
    return any(b.strip().lower() in config.HOMOPHON_BEGRIFFE for b in begriffe)


def _ist_boilerplate(begriffe: list[str]) -> bool:
    """Ein Begriff des Markts steht im festen Intro/Outro der Show."""
    return any(
        b.strip().lower() in config.BOILERPLATE_BEGRIFFE for b in begriffe
    )


def _token_ids(market: dict) -> tuple[str | None, str | None]:
    """YES/NO-Token aus clobTokenIds (Reihenfolge folgt outcomes)."""
    roh = market.get("clobTokenIds")
    outcomes = market.get("outcomes")
    if not roh:
        return None, None
    ids = json.loads(roh) if isinstance(roh, str) else list(roh)
    namen = json.loads(outcomes) if isinstance(outcomes, str) else (outcomes or [])
    yes_id = no_id = None
    for name, tok in zip(namen, ids):
        if str(name).strip().lower() == "yes":
            yes_id = tok
        elif str(name).strip().lower() == "no":
            no_id = tok
    # Fallback: Polymarket-Konvention Index 0 = YES, 1 = NO
    if yes_id is None and no_id is None and len(ids) == 2:
        yes_id, no_id = ids[0], ids[1]
    return yes_id, no_id


_NEGATION = re.compile(r"\bwill no\b[^\"“”]{0,80}\bepisode\b")


def _ist_negationsmarkt(question: str) -> bool:
    """Maerkte wie 'Will no episode air?' sind keine Wortzaehl-Maerkte.

    Deckt auch Varianten mit Showname dazwischen ab ('Will no Lemonade
    Stand episode air?'). Anfuehrungszeichen im Fenster brechen den Match,
    damit Fragen mit zitiertem Begriff (Will "No" be said ...) nicht
    faelschlich als Negationsmarkt gelten.
    """
    q = question.lower()
    return (
        "no episode" in q
        or bool(_NEGATION.search(q))
        or "not air" in q
        or "be cancelled" in q
    )


def build_rule(market: dict) -> MarketRule:
    """Leitet eine MarketRule aus einem Gamma-Markt ab (oder SKIP)."""
    mid = str(market.get("id"))
    slug = market.get("slug", "")
    question = market.get("question", "")
    description = market.get("description", "") or ""
    yes_id, no_id = _token_ids(market)

    def skip(grund: str) -> MarketRule:
        return MarketRule(
            market_id=mid, slug=slug, question=question, varianten=[],
            schwelle=0, yes_token_id=yes_id, no_token_id=no_id,
            homophon_sensitiv=False, status="skip", skip_grund=grund,
            resolution_hinweis=description[:400],
        )

    if _ist_negationsmarkt(question):
        return skip("negationsmarkt_ohne_wortzaehlung")

    begriffe = parse_zitierte_begriffe(question)
    if not begriffe:
        return skip("keine_zitierten_begriffe")

    if yes_id is None or no_id is None:
        return skip("token_ids_unvollstaendig")

    varianten: list[str] = []
    for b in begriffe:
        for v in expandiere_varianten(b):
            if v not in varianten:
                varianten.append(v)

    # Auffaellige Aufloesungsregeln, die manuelle Pruefung brauchen.
    if re.search(r"\bunless\b|\bexcept\b|\bonly if\b", description, re.IGNORECASE):
        return skip("aufloesungsregel_mit_ausnahmebedingung")

    return MarketRule(
        market_id=mid,
        slug=slug,
        question=question,
        varianten=varianten,
        schwelle=parse_schwelle(question),
        yes_token_id=yes_id,
        no_token_id=no_id,
        homophon_sensitiv=_ist_homophon(begriffe),
        status="active",
        resolution_hinweis=description[:400],
        boilerplate_sensitiv=_ist_boilerplate(begriffe),
    )


def build_rules(markets: list[dict]) -> list[MarketRule]:
    return [build_rule(m) for m in markets]


def lade_snapshot_rules(pfad=config.GAMMA_SNAPSHOT) -> list[MarketRule]:
    with open(pfad, encoding="utf-8") as f:
        snap = json.load(f)
    return build_rules(snap["markets"])
