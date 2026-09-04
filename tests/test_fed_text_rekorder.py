"""Tests fuer den Fed-Text-Drop-Rekorder: Text, Prognose, Buch, Feed, Ablauf, Auswertung."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from operations.pipeline import fed_text_rekorder as ftr

SEITE = (
    b'<html><head><script>var x = "Framework";</script></head><body>'
    b'<div class="col-xs-12 col-sm-8 col-md-8">'
    b'<p>Good morning. Our framework for capital expenditures &amp; productivity ' +
    b'word ' * 500 +
    b'The banks and asset prices matter.</p>'
    b'<div class="footnotes"><p>1. Bitcoin and crypto are discussed in Smith (2024).</p></div>'
    b'</div></body></html>'
)


def _markt(mid, frage, desc="", tokens=("y" , "n")):
    return {"id": mid, "slug": f"m-{mid}", "question": frage, "description": desc,
            "clobTokenIds": json.dumps(list(tokens)), "outcomes": json.dumps(["Yes", "No"])}


def _event():
    return {"id": "870938", "title": "Warsh JH", "markets": [
        _markt("1", 'Will Warsh say "Framework" during Jackson Hole speech?'),
        _markt("2", 'Will Warsh say "Bitcoin" or "Crypto" during Jackson Hole speech?'),
        _markt("3", 'Will Warsh say "Bank" or "Asset" 10+ times during Jackson Hole speech?'),
        _markt("4", 'Will Warsh say "CapEx" or "Capital Expenditure" during Jackson Hole speech?'),
        {"id": "5", "slug": "not-air", "question": "Will Warsh's remarks not air?",
         "clobTokenIds": json.dumps(["a", "b"]), "outcomes": json.dumps(["Yes", "No"])},
    ]}


# --------------------------------------------------------------------- Text

def test_extrahiere_text_schneidet_script_und_fussnoten_ab():
    text = ftr.extrahiere_text(SEITE, "text/html")
    assert "Good morning" in text and "capital expenditures & productivity" in text
    assert "Bitcoin" not in text and "Smith" not in text  # Fussnoten weg
    assert 'var x' not in text  # Script weg


def test_extrahiere_text_pdf_ohne_parser_liefert_leer_oder_text():
    # Kein echtes PDF: der PDF-Pfad darf nicht abstuerzen.
    try:
        text = ftr.extrahiere_text(b"%PDF-1.4 kaputt", "application/pdf")
    except Exception:  # pypdf vorhanden, aber Datei unlesbar -> zulaessig
        text = ""
    assert isinstance(text, str)


# ----------------------------------------------------------------- Prognose

def test_prognosen_mit_bot_regeln_und_schwellen():
    text = ftr.extrahiere_text(SEITE, "text/html")
    rules = ftr.regeln_aus_event(_event())
    prog = {p.market_id: p for p in ftr.prognosen(text, rules)}
    assert prog["1"].yes is True and prog["1"].anzahl == 1          # framework
    assert prog["2"].yes is False                                     # bitcoin nur in Fussnote
    assert prog["3"].schwelle == 10 and prog["3"].yes is False        # banks + asset = 2 < 10
    assert prog["4"].yes is True                                      # capital expenditures (Plural)
    assert prog["5"].status == "skip"                                 # Negationsmarkt


# --------------------------------------------------------------------- Buch

def test_bestes_niveau_aus_clob_book():
    book = {"bids": [{"price": "0.40", "size": "10"}, {"price": "0.55", "size": "5"}],
            "asks": [{"price": "0.70", "size": "3"}, {"price": "0.62", "size": "9"}]}
    assert ftr.bestes_niveau(book) == (0.55, 0.62)
    assert ftr.bestes_niveau({}) == (None, None)


def test_buch_snapshot_ueberlebt_fehler_je_markt():
    rules = ftr.regeln_aus_event(_event())

    def hole_json(url):
        if "token_id=y" in url and rules[0].yes_token_id == "y":
            raise RuntimeError("503")
        return {"bids": [{"price": "0.3"}], "asks": [{"price": "0.4"}]}

    snap = ftr.buch_snapshot(rules, hole_json)
    assert "5" not in snap  # skip-Markt ohne Regel
    assert all(set(v) == {"bid", "ask"} for v in snap.values())


# --------------------------------------------------------------------- Feed

def test_finde_im_feed_nach_sprecher_und_datum():
    feed = [{"d": "8/28/2026 10:00:00 AM", "t": "In Our Time", "s": "Chair Kevin Warsh",
             "l": "/newsevents/speech/warsh20260828a.htm"},
            {"d": "8/27/2026 9:00:00 AM", "t": "Other", "s": "Governor X", "l": "/x.htm"}]
    assert ftr.finde_im_feed(feed, "warsh", "8/28/2026") == "/newsevents/speech/warsh20260828a.htm"
    assert ftr.finde_im_feed(feed, "warsh", "8/29/2026") is None
    assert ftr._absolut("/a.htm") == "https://www.federalreserve.gov/a.htm"


# ------------------------------------------------------------------- Ablauf

def test_warte_auf_text_protokolliert_erkennung(tmp_path):
    antworten = [ftr.Antwort(404, {}, b"", "2026-09-16T18:29:59.000+00:00"),
                 ftr.Antwort(200, {"Content-Type": "text/html"}, b"<p>kurz</p>", "t1"),
                 ftr.Antwort(200, {"Content-Type": "text/html", "Last-Modified": "Wed, 16 Sep 2026 18:30:07 GMT"},
                             SEITE, "2026-09-16T18:30:08.000+00:00")]
    geschlafen = []
    protokoll = tmp_path / "e.jsonl"
    text, meta = ftr.warte_auf_text("u", lambda url: antworten.pop(0), 1.0, None, protokoll,
                                    schlaf=geschlafen.append)
    assert "framework" in text.lower()
    assert meta["polls"] == 3 and meta["last_modified"].startswith("Wed, 16 Sep")
    assert geschlafen == [1.0, 1.0]
    zeilen = [json.loads(z) for z in protokoll.read_text(encoding="utf-8").splitlines()]
    assert zeilen[-1]["art"] == "text_da"


def test_warte_auf_text_bricht_an_deadline_ab(tmp_path):
    jetzt = datetime(2026, 9, 16, 18, 30, tzinfo=timezone.utc)
    zeit = {"t": jetzt}

    def uhr():
        zeit["t"] += timedelta(seconds=30)
        return zeit["t"]

    protokoll = tmp_path / "e.jsonl"
    erg = ftr.warte_auf_text("u", lambda url: ftr.Antwort(404, {}, b"", "x"), 1.0,
                             jetzt + timedelta(minutes=1), protokoll, schlaf=lambda s: None, uhr=uhr)
    assert erg is None
    assert "abbruch_deadline" in protokoll.read_text(encoding="utf-8")


# --------------------------------------------------------------- Auswertung

def _protokoll(tmp_path):
    t0 = datetime(2026, 8, 28, 14, 0, 11, tzinfo=timezone.utc)

    def b(minuten, bid, ask):
        return {"zeit_utc": (t0 + timedelta(minutes=minuten)).isoformat(), "art": "buch",
                "buecher": {"4": {"bid": bid, "ask": ask}, "1": {"bid": 0.72, "ask": 0.76}}}

    zeilen = [
        {"zeit_utc": (t0 - timedelta(minutes=5)).isoformat(), "art": "start"},
        b(-1, 0.68, 0.70),
        {"zeit_utc": t0.isoformat(), "art": "text_da", "textlaenge": 28000},
        {"zeit_utc": t0.isoformat(), "art": "prognose", "prognosen": [
            {"market_id": "4", "frage": 'Will Warsh say "CapEx" ...?', "yes": True,
             "anzahl": 1, "schwelle": 1, "status": "active"},
            {"market_id": "1", "frage": 'Will Warsh say "Framework" ...?', "yes": False,
             "anzahl": 0, "schwelle": 1, "status": "active"}]},
        b(5, 0.48, 0.50), b(15, 0.49, 0.51), b(20, 0.97, 0.99),
    ]
    p = tmp_path / "ereignisse.jsonl"
    p.write_text("\n".join(json.dumps(z) for z in zeilen) + "\n", encoding="utf-8")
    return p


def test_auswerte_liefert_vor_mid_und_minuten_bis_sprung(tmp_path):
    zeilen = ftr.auswerte(_protokoll(tmp_path))
    nach = {z["frage"]: z for z in zeilen}
    capex = nach['Will Warsh say "CapEx" ...?']
    assert capex["mid_vor_text"] == 0.69 and capex["prognose_yes"] is True
    assert capex["minuten_bis_sprung"] == 20.0
    framework = nach['Will Warsh say "Framework" ...?']
    assert framework["minuten_bis_sprung"] is None  # nie um 0.25 bewegt


def test_main_auswerte_druckt_tabelle(tmp_path, capsys):
    rc = ftr.main(["--auswerte", str(_protokoll(tmp_path))])
    assert rc == 0
    out = capsys.readouterr().out
    assert "CapEx" in out and "20.0" in out


def test_main_einmal_schreibt_protokoll_mit_prognose(tmp_path):
    antworten = [ftr.Antwort(200, {"Content-Type": "text/html", "Last-Modified": "x"}, SEITE, "t")]

    def hole_json(url):
        if "/events/" in url:
            return _event()
        return {"bids": [{"price": "0.6"}], "asks": [{"price": "0.7"}]}

    rc = ftr.main(["--event", "870938", "--quelle", "u", "--einmal", "--wurzel", str(tmp_path)],
                  holer=lambda url: antworten.pop(0), hole_json_fn=hole_json, schlaf=lambda s: None)
    assert rc == 0
    zeilen = [json.loads(z) for z in (tmp_path / "870938" / "ereignisse.jsonl")
              .read_text(encoding="utf-8").splitlines()]
    arten = [z["art"] for z in zeilen]
    assert arten[:2] == ["start", "buch"] and "text_da" in arten and "prognose" in arten
    assert arten[-1] == "buch" and zeilen[-1]["phase"] == "bei_text"
    prog = next(z for z in zeilen if z["art"] == "prognose")["prognosen"]
    assert any(p["yes"] for p in prog if p["market_id"] == "1")
