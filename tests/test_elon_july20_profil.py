"""Armierung Elon-Post-Woche 20.-26.07.2026 (Event 715491) — 23.07.2026.

Nachfolgeprofil von `elon_july13`. Der Regeltext der Serie ist wortgleich
zur Vorwoche (am 23.07. an der Gamma-Beschreibung von Markt 2966514
gegengelesen), der Matcher aus `elon_bot` traegt deshalb unveraendert.
Neu gegenueber july13 sind nur Event-Bindung, Marktperiode und die
tiefere Startscan-Historie, weil mitten in der Periode armiert wird.

Die Tests laufen offline gegen synthetische Gamma-Maerkte mit den echten
market_ids und Fragen des Events — sie belegen die Regel-Ableitung und
das Wort-Matching, nicht den Live-Abruf.
"""

from __future__ import annotations

import importlib
import json

import pytest

from operations.pipeline import config
from operations.pipeline.elon_bot import ElonMatcher, baue_elon_rules
from operations.pipeline.market_rules import MarketRule

PROFIL = "elon_july20"


def _markt(mid: str, frage: str, closed: bool = False) -> dict:
    """Minimaler Gamma-Markt mit YES/NO-Token und der echten Frage."""
    return {
        "id": mid,
        "slug": f"will-elon-post-{mid}",
        "question": frage,
        # Gekuerzter Originaltext inklusive der Bildtext-Klausel — sie
        # traegt das "only if", an dem build_rule jeden Markt verwerfen
        # wuerde (Grund fuer die eigene Regel-Ableitung in elon_bot).
        "description": (
            'This market will resolve to "Yes" if @elonmusk posts the '
            "listed term between July 20, 2026, 12:00 AM ET and July 26, "
            '2026, 11:59 PM ET. Otherwise, this market will resolve to "No." '
            "Text posted in images, memes, or other non-animated, non-video "
            'media that are not strictly text will qualify towards a "Yes" '
            "resolution only if the listed term is spelled out clearly and "
            "in full."
        ),
        "outcomes": json.dumps(["Yes", "No"]),
        "clobTokenIds": json.dumps([f"yes-{mid}", f"no-{mid}"]),
        "closed": closed,
    }


# Echte market_ids/Fragen des Events (Gamma, 23.07.2026). Die vier
# geschlossenen Maerkte standen beim Erheben bereits auf 1.00.
EVENT_MARKETS = [
    _markt("2966512", 'Will Elon post "Soccer" on X this week?'),
    _markt("2966527", 'Will Elon post "Crypto" or "Bitcoin" on X this week?'),
    _markt("2966520", 'Will Elon post "Iran" or "Iranian" on X this week?'),
    _markt("2966522", 'Will Elon post "IPO" on X this week?'),
    _markt("2966514", 'Will Elon post "Trump" on X this week?'),
    _markt("2966511", 'Will Elon post "Football" on X this week?'),
    _markt("2966513", 'Will Elon post "President" on X this week?'),
    _markt("2966516", 'Will Elon post "Neuralink" on X this week?'),
    _markt("2966521", 'Will Elon post "China" on X this week?'),
    _markt("2966526", 'Will Elon post "Texas" on X this week?'),
    _markt("2966524", 'Will Elon post "ChatGPT" on X this week?'),
    _markt("2966517", 'Will Elon post "Never" on X this week?'),
    _markt("2966518", 'Will Elon post "Always" on X this week?'),
    _markt("2966515", 'Will Elon post "Tesla" on X this week?', closed=True),
    _markt("2966519",
           'Will Elon post "Video game" or "Videogame" on X this week?',
           closed=True),
    _markt("2966523", 'Will Elon post "Claude" on X this week?', closed=True),
    _markt("2966525", 'Will Elon post "SpaceX" on X this week?', closed=True),
]


@pytest.fixture
def profil(monkeypatch):
    """Aktiviert elon_july20 fuer die config-abgeleiteten Werte."""
    monkeypatch.setenv("BOT_PROFIL", PROFIL)
    importlib.reload(config)
    yield
    monkeypatch.delenv("BOT_PROFIL", raising=False)
    importlib.reload(config)


@pytest.fixture
def snapshot(profil, tmp_path, monkeypatch):
    """Gamma-Snapshot des Events auf der Platte, wie ihn der Bot liest."""
    pfad = tmp_path / "gamma_event_snapshot.json"
    pfad.write_text(json.dumps(
        {"event_id": "715491", "slug": config.PROFILE[PROFIL]["event_slug"],
         "markets": EVENT_MARKETS}), encoding="utf-8")
    monkeypatch.setattr(config, "GAMMA_SNAPSHOT", pfad)
    return pfad


def _rule(begriffe: list[str]) -> MarketRule:
    return MarketRule(
        market_id="1", slug="s", question="q", varianten=begriffe,
        schwelle=1, yes_token_id="y", no_token_id="n",
        homophon_sensitiv=False,
    )


# ------------------------------------------------ Profil-Grundwerte


def test_profil_grunddaten(profil) -> None:
    p = config.PROFILE[PROFIL]
    alt = config.PROFILE["elon_july13"]
    assert p["event_id"] == "715491"
    assert p["event_slug"] == (
        "what-will-elon-post-this-week-july-20-july-26-20260717142325168")
    assert p["discovery_slug_filter"] in p["event_slug"]
    # Quelle und Deckel unveraendert zur Vorwoche: gleicher Account,
    # gleiche EV-Parameter, gleicher Poll-Takt.
    assert p["x_user_id"] == alt["x_user_id"] == "44196397"
    assert p["p_win"] == alt["p_win"]
    assert p["min_edge"] == alt["min_edge"]
    assert p["x_poll_s"] == alt["x_poll_s"]
    # Kein Audio-Pfad: der Elon-Bot laeuft rein ueber den X-Feed.
    assert p["rss_feed_url"] is None
    assert p["yt_channel_id"] is None
    assert p["mp3_probe_muster"] is None
    # Eigenes Live-Verzeichnis -> Vorwochen-Events bleiben unberuehrt.
    assert p["live_dir"] == PROFIL
    assert p["live_dir"] != alt["live_dir"]


def test_marktperiode_deckt_20_bis_26_juli_et(profil) -> None:
    # 20.07. 00:00 ET = 04:00 UTC, 26.07. 23:59 ET = 27.07. 03:59 UTC (EDT).
    assert config.PERIODE_START_UTC == "2026-07-20T04:00:00Z"
    assert config.PERIODE_ENDE_UTC == "2026-07-27T03:59:59Z"
    # Nahtlos an die Vorwoche: july13 endete eine Sekunde vor diesem Start.
    from datetime import datetime, timedelta

    def _utc(s: str) -> datetime:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")

    vorwoche_ende = _utc(config.PROFILE["elon_july13"]["periode_ende_utc"])
    assert vorwoche_ende + timedelta(seconds=1) == _utc(
        config.PERIODE_START_UTC)
    # Sieben Kalendertage Laufzeit (Mo 00:00 ET bis So 23:59 ET).
    dauer = _utc(config.PERIODE_ENDE_UTC) - _utc(config.PERIODE_START_UTC)
    assert dauer == timedelta(days=7) - timedelta(seconds=1)


def test_nur_yes_deckel_094(profil) -> None:
    # p_win 0.97 - min_edge 0.03 = 0.94; der harte Deckel 0.97 greift nicht.
    assert config.ASK_OBERGRENZE == pytest.approx(0.94)
    assert config.ASK_OBERGRENZE < config.HARD_ASK_DECKEL
    # NUR YES: elon_bot.py ruft ausschliesslich entscheide_yes auf, ein
    # NO-Zweig existiert dort nicht. Der Test haelt das gegen ein
    # versehentliches Kopieren des Audio-Bot-Pfads fest.
    import operations.pipeline.elon_bot as eb

    quelltext = eb.__doc__ or ""
    assert "NUR YES" in quelltext
    assert not hasattr(eb, "entscheide_no")


def test_budget_und_sweep(profil) -> None:
    # Budget wie Vorwoche (elon_july13). Standard-Sweep: 15 USD je Clip,
    # 10 Clips -> effektiv budget-limitiert bei 13 offenen Maerkten.
    assert config.MAX_USD_GESAMT == pytest.approx(170.0)
    assert config.MAX_USD_PRO_MARKT == pytest.approx(15.0)
    assert config.MAX_CLIPS_PRO_MARKT == 10


def test_startscan_tiefer_als_bei_wochenstart(profil) -> None:
    # Armierung an Tag 4 von 7: 4 Seiten (Default) reichen nicht bis zum
    # Periodenstart zurueck.
    assert config.X_STARTSCAN_SEITEN == 12
    assert config.X_STARTSCAN_SEITEN > config.PROFILE["elon_july13"].get(
        "startscan_seiten", 4)


def test_startscan_default_bleibt_vier() -> None:
    # Aktives Testprofil (Default allin_july10) hat keinen Override.
    assert config.X_STARTSCAN_SEITEN == 4


# ------------------------------------------------ Regel-Ableitung


def test_baue_rules_ueberspringt_geschlossene_maerkte(snapshot) -> None:
    rules = baue_elon_rules()
    ids = {r.market_id for r in rules}
    assert len(rules) == 13
    # Tesla/Video game/Claude/SpaceX standen am 23.07. bereits auf 1.00.
    for geschlossen in ("2966515", "2966519", "2966523", "2966525"):
        assert geschlossen not in ids
    for offen in ("2966512", "2966527", "2966520", "2966522"):
        assert offen in ids


def test_baue_rules_liest_beide_begriffe_bei_oder_maerkten(snapshot) -> None:
    nach_id = {r.market_id: r for r in baue_elon_rules()}
    assert nach_id["2966527"].varianten == ["Crypto", "Bitcoin"]
    assert nach_id["2966520"].varianten == ["Iran", "Iranian"]
    assert nach_id["2966512"].varianten == ["Soccer"]
    # Schwelle 1 und YES-Token verdrahtet; kein ASR -> kein Homophon-Gate.
    r = nach_id["2966512"]
    assert r.schwelle == 1
    assert r.yes_token_id == "yes-2966512"
    assert r.homophon_sensitiv is False


def test_baue_rules_verwirft_boilerplate_only_if_nicht(snapshot) -> None:
    # "only if" ist Standard-Boilerplate der Bildtext-Regel. Der generische
    # market_rules.build_rule stuft eine "only if"-Klausel als Ausnahme ein
    # und verwirft den Markt — baue_elon_rules bewusst nicht (manuell
    # geprueft 13.07., Regeltext 23.07. unveraendert).
    from operations.pipeline import market_rules as mr

    markt = EVENT_MARKETS[0]
    assert "only if" in markt["description"]
    generisch = mr.build_rule(markt)
    assert generisch.status == "skip"
    assert generisch.skip_grund == "aufloesungsregel_mit_ausnahmebedingung"
    # Der Elon-Pfad haelt denselben Markt aktiv.
    eigen = {r.market_id: r for r in baue_elon_rules()}[markt["id"]]
    assert eigen.status == "active"
    assert eigen.varianten == ["Soccer"]


# ------------------------------------------------ Wort-Matching


def test_matcher_plural_possessiv_case_und_sigils() -> None:
    m = ElonMatcher(_rule(["Neuralink"]))
    for text in ["Neuralink update", "neuralink", "NEURALINK",
                 "Neuralinks are live", "Neuralink's team", "#Neuralink",
                 "@Neuralink", "Great work by Neuralink."]:
        assert m.pruefe(text)[0] is True, text


def test_matcher_symbole_im_wort_disqualifizieren() -> None:
    m = ElonMatcher(_rule(["Texas"]))
    # "Extraneous symbols being inserted into a word ... will disqualify it"
    for text in ["T3xas", "Tex_as", "Te$xas", "Texas2"]:
        assert m.pruefe(text)[0] is False, text


def test_matcher_misspellings_zaehlen_nicht() -> None:
    m = ElonMatcher(_rule(["China"]))
    for text in ["Chinaaa", "Chna", "Chinna"]:
        assert m.pruefe(text)[0] is False, text


def test_matcher_compound_kommt_als_verdacht_nicht_als_kauf() -> None:
    # "Instances where the term is used in a compound word will count" —
    # per Regex nicht von Ableitungen trennbar, daher nur Hinweis-Event.
    m = ElonMatcher(_rule(["Iran", "Iranian"]))
    strikt, verdacht = m.pruefe("pro-Iranian rhetoric")
    assert strikt is True  # Bindestrich ist Wortgrenze -> sauberer Treffer
    strikt, verdacht = m.pruefe("Iranophobia")
    assert (strikt, verdacht) == (False, True)


def test_matcher_ipo_bleibt_wortgenau() -> None:
    m = ElonMatcher(_rule(["IPO"]))
    assert m.pruefe("The IPO is next week")[0] is True
    assert m.pruefe("ipo")[0] is True
    assert m.pruefe("IPOs")[0] is True
    # Kein Treffer in laengeren Woertern (dort nur Verdacht).
    assert m.pruefe("XIPOX")[0] is False


def test_matcher_chatgpt_und_spacex_tragen_ziffern_und_grossbuchstaben() -> None:
    m = ElonMatcher(_rule(["ChatGPT"]))
    assert m.pruefe("chatgpt is wrong again")[0] is True
    assert m.pruefe("ChatGPT-5")[0] is True  # Bindestrich = Wortgrenze
    assert m.pruefe("ChatGPT4")[0] is False  # angrenzende Ziffer blockt


def test_matcher_mehrwort_begriff_mit_und_ohne_bindestrich() -> None:
    m = ElonMatcher(_rule(["Video game", "Videogame"]))
    for text in ["video game", "Video-Game", "videogame", "Video games"]:
        assert m.pruefe(text)[0] is True, text
