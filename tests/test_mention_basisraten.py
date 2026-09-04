"""Tests fuer den Basisraten-Harvester: Parsing, Outcomes, Aggregation, Vergleich, CLI."""
from __future__ import annotations

import json

from operations.analysis import mention_basisraten as mb


def _markt(frage, yes=True, closed=True, outcomes=("Yes", "No"), bid=None, ask=None):
    preise = ["1", "0"] if yes else ["0", "1"]
    if list(outcomes) == ["No", "Yes"]:
        preise = list(reversed(preise))
    m = {"question": frage, "closed": closed, "outcomes": json.dumps(list(outcomes)),
         "outcomePrices": json.dumps(preise)}
    if bid is not None:
        m["bestBid"] = str(bid)
    if ask is not None:
        m["bestAsk"] = str(ask)
    return m


def _event(eid, ende, maerkte, titel="Serie"):
    return {"id": eid, "endDate": f"{ende}T23:59:00Z", "title": titel, "markets": maerkte}


# -------------------------------------------------------------- parse_frage

def test_parse_frage_einzelwort_ohne_schwelle():
    k = mb.parse_frage('Will "Software" be said during the next episode?')
    assert k == mb.Schluessel("software", 1)


def test_parse_frage_alternativen_und_schwelle():
    k = mb.parse_frage('Will "Hundred" or "Thousand" or "Million" be said 10+ times during ...?')
    assert k == mb.Schluessel("hundred/thousand/million", 10)


def test_parse_frage_meta_markt_ist_none():
    assert mb.parse_frage("Will no episode air?") is None
    assert mb.parse_frage("") is None


# --------------------------------------------------------- outcome_aus_markt

def test_outcome_yes_und_no_in_standardreihenfolge():
    assert mb.outcome_aus_markt(_markt("q", yes=True)) is True
    assert mb.outcome_aus_markt(_markt("q", yes=False)) is False


def test_outcome_folgt_der_outcomes_reihenfolge():
    m = _markt("q", yes=True, outcomes=("No", "Yes"))
    assert mb.outcome_aus_markt(m) is True


def test_outcome_offen_oder_unentschieden_ist_none():
    assert mb.outcome_aus_markt(_markt("q", closed=False)) is None
    m = _markt("q")
    m["outcomePrices"] = json.dumps(["0.5", "0.5"])
    assert mb.outcome_aus_markt(m) is None
    m["outcomePrices"] = "kein json"
    assert mb.outcome_aus_markt(m) is None


# -------------------------------------------------------------- Aggregation

def _serie():
    return [
        _event("3", "2026-08-21", [_markt('Will "IPO" be said ...?', yes=False),
                                   _markt('Will "AI" be said 35+ times ...?', yes=True),
                                   _markt("Will no episode air?", yes=False)]),
        _event("2", "2026-08-14", [_markt('Will "IPO" be said ...?', yes=True),
                                   _markt('Will "AI" be said 35+ times ...?', yes=True)]),
        _event("1", "2026-08-07", [_markt('Will "IPO" be said ...?', yes=True),
                                   _markt('Will "AI" be said 50+ times ...?', yes=True)]),
    ]


def test_basisraten_zaehlen_je_wort_und_schwelle_getrennt():
    raten = mb.basisraten(mb.sammle_beobachtungen(_serie()))
    nach = {(r.wort, r.schwelle): r for r in raten}
    ipo = nach[("ipo", 1)]
    assert (ipo.n, ipo.yes) == (3, 2)
    assert ipo.quote == round(2 / 3, 3)
    assert ipo.laplace == round(3 / 5, 3)
    assert ipo.historie == ["2026-08-07:Y", "2026-08-14:Y", "2026-08-21:N"]
    assert (ipo.letzte3_yes, ipo.letzte3_n) == (2, 3)
    assert nach[("ai", 35)].n == 2 and nach[("ai", 50)].n == 1


def test_basisraten_sortiert_nach_n_absteigend():
    raten = mb.basisraten(mb.sammle_beobachtungen(_serie()))
    assert [r.n for r in raten] == sorted([r.n for r in raten], reverse=True)


def test_meta_markt_wird_nicht_gezaehlt():
    beob = mb.sammle_beobachtungen(_serie())
    assert all(k.wort != "" for k in beob)
    assert len(beob) == 3


# ---------------------------------------------------------------- Vergleich

def _rate(laplace, n=6):
    yes = round(laplace * (n + 2) - 1)
    return mb.Basisrate(wort="x", schwelle=1, n=n, yes=yes, quote=yes / n,
                        laplace=laplace, letzte3_yes=min(yes, 3), letzte3_n=3, historie=[])


def test_klassifiziere_taker_maker_no_fair():
    assert mb.klassifiziere(_rate(0.875), bid=0.60, ask=0.70) == "YES-Kandidat (Taker)"
    assert mb.klassifiziere(_rate(0.875), bid=0.55, ask=0.97) == "YES-Kandidat (Maker-Bid)"
    assert mb.klassifiziere(_rate(0.25), bid=0.45, ask=0.50) == "NO-Kandidat (Maker)"
    assert mb.klassifiziere(_rate(0.60), bid=0.55, ask=0.65) == "fair"
    assert mb.klassifiziere(_rate(0.60), bid=None, ask=0.65) == "keine Quotes"


def test_vergleiche_verknuepft_offenes_event_mit_historie():
    raten = mb.basisraten(mb.sammle_beobachtungen(_serie()))
    offen = _event("9", "2026-09-04", [
        _markt('Will "IPO" be said during the next episode?', closed=False, bid=0.30, ask=0.40),
        _markt('Will "Neu" be said during the next episode?', closed=False, bid=0.5, ask=0.6),
        _markt("Will no episode air?", closed=False, bid=0.01, ask=0.05),
    ])
    zeilen = mb.vergleiche(raten, offen)
    assert zeilen[0]["n"] == 3 and zeilen[0]["label"] == "YES-Kandidat (Taker)"
    assert zeilen[1]["label"] == "keine Historie"
    assert zeilen[2]["label"] == "keine Historie" and zeilen[2]["bid"] == 0.01


# ---------------------------------------------------------------------- CLI

def test_lade_serie_begrenzt_limit_auf_50():
    gesehen = {}

    def lader(url):
        gesehen["url"] = url
        return []

    mb.lade_serie(11275, lader=lader, limit=500)
    assert "limit=50" in gesehen["url"]
    assert "series_id=11275" in gesehen["url"]
    assert "closed=true" in gesehen["url"]


def test_main_schreibt_json_mit_serien_und_vergleich(tmp_path, capsys):
    offen = _event("9", "2026-09-04", [
        _markt('Will "IPO" be said during the next episode?', closed=False, bid=0.30, ask=0.40)])

    def lader(url):
        if "/events/9" in url:
            return offen
        return _serie()

    ziel = tmp_path / "out.json"
    rc = mb.main(["--serie", "11300", "--offen", "9", "--json", str(ziel)], lader=lader)
    assert rc == 0
    daten = json.loads(ziel.read_text(encoding="utf-8"))
    assert daten["serien"]["11300"]["n_events"] == 3
    assert daten["vergleich"]["zeilen"][0]["label"] == "YES-Kandidat (Taker)"
    out = capsys.readouterr().out
    assert "Serie 11300" in out and "Offenes Event 9" in out
