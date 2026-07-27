"""Armierung Elon-Post-Woche 27.07.-02.08.2026 (Event 745693) — 27.07.2026.

Nachfolgeprofil von `elon_july20`. Der Regeltext der Serie ist wortgleich
zu july13/july20 (am 27.07. per Diff gegen den july20-Snapshot
gegengelesen — nur die Datumsangaben wechseln, die Beschreibungs-Schablone
ist ueber alle 14 Maerkte identisch), der Matcher aus `elon_bot` traegt
deshalb unveraendert. Neu gegenueber july20 sind Event-Bindung,
Marktperiode und der flachere Startscan (Armierung an Tag 1 statt Tag 4).

Die Tests laufen offline gegen synthetische Gamma-Maerkte mit den echten
market_ids und Fragen des Events — sie belegen die Regel-Ableitung, nicht
den Live-Abruf. Die generischen Matcher-Faelle stehen in
test_elon_july20_profil.py und gelten fuer diese Woche unveraendert.
"""

from __future__ import annotations

import importlib
import json

import pytest

from operations.pipeline import config
from operations.pipeline.elon_bot import ElonMatcher, baue_elon_rules
from operations.pipeline.market_rules import MarketRule

PROFIL = "elon_july27"


def _markt(mid: str, frage: str, closed: bool = False) -> dict:
    """Minimaler Gamma-Markt mit YES/NO-Token und der echten Frage."""
    return {
        "id": mid,
        "slug": f"will-elon-post-{mid}",
        "question": frage,
        # Gekuerzter Originaltext (Gamma, 27.07.) inklusive der
        # Bildtext-Klausel — ihr "only if" ist der Grund fuer die eigene
        # Regel-Ableitung in elon_bot (build_rule wuerde verwerfen).
        "description": (
            'This market will resolve to "Yes" if @elonmusk posts the '
            "listed term between July 27, 2026, 12:00 AM ET and August 2, "
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


# Echte market_ids/Fragen des Events (Gamma, 27.07.2026). Anders als beim
# Tag-4-Einstieg der Vorwoche ist noch kein Markt geschlossen.
EVENT_MARKETS = [
    _markt("3093903", 'Will Elon post "Energy" on X this week?'),
    _markt("3093904", 'Will Elon post "Nuclear" on X this week?'),
    _markt("3093905", 'Will Elon post "President" on X this week?'),
    _markt("3093906", 'Will Elon post "Trump" on X this week?'),
    _markt("3093907", 'Will Elon post "Tesla" on X this week?'),
    _markt("3093908", 'Will Elon post "Neuralink" on X this week?'),
    _markt("3093909",
           'Will Elon post "Video game" or "Videogame" on X this week?'),
    _markt("3093910", 'Will Elon post "Iran" or "Iranian" on X this week?'),
    _markt("3093911", 'Will Elon post "China" on X this week?'),
    _markt("3093912", 'Will Elon post "IPO" on X this week?'),
    _markt("3093913", 'Will Elon post "Claude" on X this week?'),
    _markt("3093914", 'Will Elon post "ChatGPT" on X this week?'),
    _markt("3093915", 'Will Elon post "Texas" on X this week?'),
    _markt("3093916", 'Will Elon post "Crypto" or "Bitcoin" on X this week?'),
]


@pytest.fixture
def profil(monkeypatch):
    """Aktiviert elon_july27 fuer die config-abgeleiteten Werte."""
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
        {"event_id": "745693", "slug": config.PROFILE[PROFIL]["event_slug"],
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
    alt = config.PROFILE["elon_july20"]
    assert p["event_id"] == "745693"
    assert p["event_slug"] == (
        "what-will-elon-post-this-week-july-27-august-2-20260724155239115")
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


def test_marktperiode_deckt_27_juli_bis_2_august_et(profil) -> None:
    # 27.07. 00:00 ET = 04:00 UTC, 02.08. 23:59 ET = 03.08. 03:59 UTC (EDT).
    assert config.PERIODE_START_UTC == "2026-07-27T04:00:00Z"
    assert config.PERIODE_ENDE_UTC == "2026-08-03T03:59:59Z"
    # Nahtlos an die Vorwoche: july20 endete eine Sekunde vor diesem Start.
    from datetime import datetime, timedelta

    def _utc(s: str) -> datetime:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")

    vorwoche_ende = _utc(config.PROFILE["elon_july20"]["periode_ende_utc"])
    assert vorwoche_ende + timedelta(seconds=1) == _utc(
        config.PERIODE_START_UTC)
    # Sieben Kalendertage Laufzeit (Mo 00:00 ET bis So 23:59 ET).
    dauer = _utc(config.PERIODE_ENDE_UTC) - _utc(config.PERIODE_START_UTC)
    assert dauer == timedelta(days=7) - timedelta(seconds=1)


def test_nur_yes_deckel_094(profil) -> None:
    # p_win 0.97 - min_edge 0.03 = 0.94; der harte Deckel 0.97 greift nicht.
    assert config.ASK_OBERGRENZE == pytest.approx(0.94)
    assert config.ASK_OBERGRENZE < config.HARD_ASK_DECKEL


def test_budget_und_sweep_wie_vorwoche(profil) -> None:
    # Vorwochen-Vorgabe (User 23.07.) unveraendert uebernommen; die
    # Bestaetigung am realen Wallet-Stand ist Runbook-Schritt, kein Code.
    assert config.MAX_USD_GESAMT == pytest.approx(400.0)
    assert config.MAX_USD_PRO_MARKT == pytest.approx(50.0)
    assert config.MAX_CLIPS_PRO_MARKT == 40
    alt = config.PROFILE["elon_july20"]
    for feld in ("max_usd_gesamt", "max_usd_pro_markt",
                 "max_clips_pro_markt"):
        assert config.PROFILE[PROFIL][feld] == alt[feld]


def test_startscan_reserve_fuer_tag1_abend(profil) -> None:
    # Armierung am Abend von Tag 1: mehr als der 4er-Default (der
    # angebrochene Tag kann bei Elons Frequenz >80 Posts tragen), aber
    # flacher als die 12 der Tag-4-Armierung von july20.
    assert config.X_STARTSCAN_SEITEN == 8
    assert config.X_STARTSCAN_SEITEN > 4
    assert config.X_STARTSCAN_SEITEN < config.PROFILE["elon_july20"][
        "startscan_seiten"]


# ------------------------------------------------ Regel-Ableitung


def test_baue_rules_traegt_alle_14_offenen_maerkte(snapshot) -> None:
    rules = baue_elon_rules()
    assert len(rules) == 14
    ids = {r.market_id for r in rules}
    assert ids == {m["id"] for m in EVENT_MARKETS}
    # Schwelle 1 und YES-Token verdrahtet; kein ASR -> kein Homophon-Gate.
    r = {x.market_id: x for x in rules}["3093903"]
    assert r.schwelle == 1
    assert r.yes_token_id == "yes-3093903"
    assert r.homophon_sensitiv is False


def test_baue_rules_liest_beide_begriffe_bei_oder_maerkten(snapshot) -> None:
    nach_id = {r.market_id: r for r in baue_elon_rules()}
    assert nach_id["3093916"].varianten == ["Crypto", "Bitcoin"]
    assert nach_id["3093910"].varianten == ["Iran", "Iranian"]
    assert nach_id["3093909"].varianten == ["Video game", "Videogame"]


def test_baue_rules_verwirft_boilerplate_only_if_nicht(snapshot) -> None:
    # "only if" ist Standard-Boilerplate der Bildtext-Regel. Der generische
    # market_rules.build_rule stuft eine "only if"-Klausel als Ausnahme ein
    # und verwirft den Markt — baue_elon_rules bewusst nicht (manuell
    # geprueft 13.07., Regeltext am 27.07. weiterhin wortgleich).
    from operations.pipeline import market_rules as mr

    markt = EVENT_MARKETS[0]
    assert "only if" in markt["description"]
    generisch = mr.build_rule(markt)
    assert generisch.status == "skip"
    assert generisch.skip_grund == "aufloesungsregel_mit_ausnahmebedingung"
    # Der Elon-Pfad haelt denselben Markt aktiv.
    eigen = {r.market_id: r for r in baue_elon_rules()}[markt["id"]]
    assert eigen.status == "active"
    assert eigen.varianten == ["Energy"]


# ------------------------------------------------ Neue Woerter der Woche


def test_matcher_neue_woerter_energy_nuclear_claude() -> None:
    # Erstmals im Board: Energy, Nuclear, Claude — einfache Einzelwoerter,
    # dieselbe Semantik wie die Vorwochen-Woerter.
    for wort, treffer, daneben in [
        ("Energy", "Solar energy is the future", "energetic"),
        ("Nuclear", "Nuclear power now", "denuclearization"),
        ("Claude", "Claude is impressive", "Claudette"),
    ]:
        m = ElonMatcher(_rule([wort]))
        assert m.pruefe(treffer)[0] is True, wort
        strikt, _ = m.pruefe(daneben)
        assert strikt is False, daneben
