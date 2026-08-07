"""Kalshi-Mentions: Regelableitung, Buchkennzahlen, Preisspur-Rekorder.

Die Tests laufen offline gegen `tests/fixtures/kalshi_mentions_snapshot.json`
— einen echten Abzug der oeffentlichen Kalshi-API vom 28.07.2026 mit drei
Events: PayPal 28.07. (abgelaufen, derselbe Call wie unser Live-Lauf, 16
Maerkte), Fed/Warsh Juli (44) und Meta 29.07. (18), dazu ein Orderbuch.

Belegt werden die drei Regelunterschiede zu Polymarket (Schwelle immer 1,
deterministische Wortvarianten, Alternativen am Schraegstrich), der
NQE-Ausschluss und die Gebuehrenformel — nicht der Live-Abruf.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from operations.pipeline import kalshi_client, kalshi_recorder, kalshi_rules

FIXTURE = Path(__file__).parent / "fixtures" / "kalshi_mentions_snapshot.json"


@pytest.fixture(scope="module")
def snapshot() -> dict:
    with open(FIXTURE, encoding="utf-8") as f:
        return json.load(f)


def _markt(maerkte: list[dict], suffix: str) -> dict:
    treffer = [m for m in maerkte if m["ticker"].endswith(suffix)]
    assert treffer, f"kein Markt mit Suffix {suffix}"
    return treffer[0]


# --- Wortvarianten ----------------------------------------------------


def test_alternativen_am_schraegstrich_werden_getrennt():
    """"AI / Artificial Intelligence" sind zwei gleichwertige Treffer."""
    assert kalshi_rules.wort_varianten("AI / Artificial Intelligence") == [
        "AI", "Artificial Intelligence"
    ]


def test_dreifach_alternative():
    """Drei Alternativen, dazu die Zischlaut-Plurale von "Gas"."""
    assert kalshi_rules.wort_varianten("Gas / Gasoline / Natural Gas") == [
        "Gas", "Gases", "Gasoline", "Natural Gas", "Natural Gases"
    ]


def test_plural_nur_wenn_nicht_blosses_s():
    """compile_patterns matcht "s" schon als Suffix — nur Sonderfaelle."""
    # Regelplural: keine eigene Variante noetig.
    assert kalshi_rules.wort_varianten("Projection") == ["Projection"]
    # Zischlaut -> "es", sonst wuerde "Taxes" nie gezaehlt.
    assert kalshi_rules.wort_varianten("Tax") == ["Tax", "Taxes"]
    # Konsonant + y -> "ies".
    assert kalshi_rules.wort_varianten("Subsidy") == ["Subsidy", "Subsidies"]
    # Vokal + y bleibt regelmaessig ("Days").
    assert kalshi_rules.wort_varianten("Day") == ["Day"]


def test_unregelmaessige_plurale_werden_nicht_geraten():
    """Lieber ein verpasster Treffer als ein Geistertreffer."""
    assert kalshi_rules.wort_varianten("Leaf") == ["Leaf"]


def test_varianten_ohne_duplikate():
    assert kalshi_rules.wort_varianten("Gas / Gas") == ["Gas", "Gases"]
    assert kalshi_rules.wort_varianten("Cloud / Cloud") == ["Cloud"]


# --- Regelableitung ---------------------------------------------------


def test_schwelle_ist_immer_eins(snapshot):
    """Kalshi-Mentions kennen keine Zaehl-Brackets."""
    regeln = kalshi_rules.build_rules(snapshot["maerkte_fed"])
    aktive = kalshi_rules.aktive(regeln)
    assert aktive
    assert {r.schwelle for r in aktive} == {1}


def test_nqe_metamarkt_wird_uebersprungen(snapshot):
    """"Event does not qualify" ist kein Wortmarkt (Template-Artefakt)."""
    nqe = _markt(snapshot["maerkte_fed"], "-NQE")
    regel = kalshi_rules.build_rule(nqe)
    assert regel.status == "skip"
    assert regel.skip_grund == "nqe_meta_markt_ohne_wortzaehlung"


def test_abgelaufene_maerkte_werden_uebersprungen(snapshot):
    """Der PayPal-Call ist durch — alle 16 Maerkte sind finalized."""
    regeln = kalshi_rules.build_rules(snapshot["maerkte_pypl"])
    assert kalshi_rules.aktive(regeln) == []
    assert all(r.skip_grund.startswith("status_") for r in regeln)


def test_ticker_traegt_beide_seiten(snapshot):
    """Kalshi hat einen Markt mit zwei Seiten, kein Token je Ausgang."""
    regel = kalshi_rules.build_rule(_markt(snapshot["maerkte_meta"], "-LLAM"))
    assert regel.status == "active"
    assert regel.market_id == regel.yes_token_id == regel.no_token_id
    assert regel.market_id.endswith("-LLAM")


def test_zielwort_und_aufloesungsart_im_extra(snapshot):
    """Auf Kalshi entscheidet das Video — Phase 2 muss das lesen koennen."""
    regel = kalshi_rules.build_rule(_markt(snapshot["maerkte_meta"], "-LLAM"))
    assert regel.extra["venue"] == "kalshi"
    assert regel.extra["wort"] == "Llama"
    assert regel.extra["aufloesung"] == "video_primaer"
    assert regel.varianten == ["Llama"]


def test_resolutionshinweis_belegt_video_vor_transkript(snapshot):
    """Der Regeltext ist die Quelle des wichtigsten Venue-Unterschieds."""
    regel = kalshi_rules.build_rule(_markt(snapshot["maerkte_meta"], "-LLAM"))
    hinweis = regel.resolution_hinweis.lower()
    assert "video" in hinweis
    assert "primarily used to resolve" in hinweis


def test_alle_aktiven_maerkte_haben_varianten(snapshot):
    for schluessel in ("maerkte_fed", "maerkte_meta"):
        for regel in kalshi_rules.aktive(
            kalshi_rules.build_rules(snapshot[schluessel])
        ):
            assert regel.varianten, regel.market_id


def test_markt_ohne_ticker_wird_uebersprungen():
    assert kalshi_rules.build_rule({}).skip_grund == "kein_ticker"


def test_markt_ohne_zielwort_wird_uebersprungen():
    regel = kalshi_rules.build_rule({"ticker": "KXX-1-ABC", "status": "active"})
    assert regel.skip_grund == "kein_zielwort"


# --- Zaehler-Kompatibilitaet -----------------------------------------


def test_varianten_matchen_plural_und_genitiv(snapshot):
    """Die Kalshi-Regel (Phrase, Plural, Genitiv) deckt sich mit dem Zaehler."""
    from operations.pipeline.counter_engine import compile_patterns, count_in_text

    regel = kalshi_rules.build_rule(_markt(snapshot["maerkte_meta"], "-LLAM"))
    muster = compile_patterns(regel.varianten)
    assert count_in_text("we shipped Llama today", muster) == 1
    assert count_in_text("two Llamas", muster) == 1
    assert count_in_text("Llama's rollout", muster) == 1
    # Tempus-/Grammatikflexionen zaehlen laut Kalshi ausdruecklich NICHT.
    assert count_in_text("we are llamafying it", muster) == 0


def test_zischlaut_plural_wird_gezaehlt():
    """Ohne die "es"-Variante bliebe "taxes" unsichtbar."""
    from operations.pipeline.counter_engine import compile_patterns, count_in_text

    muster = compile_patterns(kalshi_rules.wort_varianten("Tax"))
    assert count_in_text("we raised taxes", muster) == 1


# --- Buchkennzahlen und Gebuehren ------------------------------------


def test_yes_quotes_aus_zwei_seiten_buch(snapshot):
    """Beide Buchseiten sind Gebote; der YES-Ask ist 1 - bestes NO-Gebot."""
    buch = snapshot["orderbuch_fed_ai"]
    yes_bid, yes_ask = kalshi_client.yes_quotes(buch)
    assert yes_bid is not None and yes_ask is not None
    assert 0.0 < yes_bid < yes_ask < 1.0


def test_buchquote_deckt_sich_mit_marktfeldern(snapshot):
    """Das abgeleitete Buch muss zu den gemeldeten Marktpreisen passen."""
    markt = _markt(snapshot["maerkte_fed"], "-AI")
    yes_bid, yes_ask = kalshi_client.yes_quotes(snapshot["orderbuch_fed_ai"])
    assert yes_bid == pytest.approx(
        kalshi_client.zahl(markt["yes_bid_dollars"]), abs=0.01
    )
    assert yes_ask == pytest.approx(
        kalshi_client.zahl(markt["yes_ask_dollars"]), abs=0.01
    )


def test_gebuehr_maximal_im_zweifel_fenster():
    """1.75 Cent bei P=0.50 — genau dort, wo unsere Fills entstanden."""
    assert kalshi_client.gebuehr(0.50) == 0.02  # ceil(1.75) = 2 Cent
    assert kalshi_client.gebuehr(0.90) == 0.01
    assert kalshi_client.gebuehr(0.50) >= kalshi_client.gebuehr(0.90)


def test_gebuehr_skaliert_mit_kontrakten():
    assert kalshi_client.gebuehr(0.50, 100) == pytest.approx(2.0)


def test_leeres_buch_liefert_none():
    assert kalshi_client.yes_quotes({"orderbook_fp": {}}) == (None, None)


# --- Rekorder ---------------------------------------------------------


def test_zeile_aus_markt_traegt_preise_und_gebuehr(snapshot):
    markt = _markt(snapshot["maerkte_fed"], "-AI")
    zeile = kalshi_recorder.zeile_aus_markt(markt, "2026-07-28T22:00:00Z")
    assert zeile["ticker"].endswith("-AI")
    assert zeile["wort"] == "AI / Artificial Intelligence"
    assert zeile["spread"] == pytest.approx(
        zeile["yes_ask"] - zeile["yes_bid"], abs=1e-9
    )
    assert zeile["gebuehr_yes_ask"] == kalshi_client.gebuehr(zeile["yes_ask"])
    assert set(zeile) == set(kalshi_recorder.FELDER)


def test_statuswechsel_liefert_fensterende():
    """Aus dem Uebergang active -> closed faellt die Fensterlaenge ab."""
    vorher: dict[str, str] = {}
    erst = [{"wall_ts_utc": "t1", "ticker": "A", "wort": "X",
             "status": "active", "last_price": 0.4}]
    assert kalshi_recorder.statuswechsel(vorher, erst) == []
    spaeter = [{"wall_ts_utc": "t2", "ticker": "A", "wort": "X",
                "status": "closed", "last_price": 0.99}]
    ereignisse = kalshi_recorder.statuswechsel(vorher, spaeter)
    assert len(ereignisse) == 1
    assert ereignisse[0]["von"] == "active"
    assert ereignisse[0]["nach"] == "closed"
    assert ereignisse[0]["wall_ts_utc"] == "t2"


def test_einmal_schreibt_csv_und_regeln(tmp_path, snapshot):
    """Ein Abtastdurchlauf ohne Netz, mit injiziertem Abruf."""
    zeilen = kalshi_recorder.einmal(
        ["KXFEDMENTION-26JUL"], tmp_path, {},
        hole=lambda ev: snapshot["maerkte_fed"],
    )
    assert len(zeilen) == 44
    csv_datei = tmp_path / "kalshi_preisspur.csv"
    inhalt = csv_datei.read_text(encoding="utf-8").splitlines()
    assert inhalt[0].startswith("wall_ts_utc,")
    assert len(inhalt) == 45  # Header + 44 Maerkte


def test_einmal_haengt_an_statt_zu_ueberschreiben(tmp_path, snapshot):
    for _ in range(2):
        kalshi_recorder.einmal(
            ["KXFEDMENTION-26JUL"], tmp_path, {},
            hole=lambda ev: snapshot["maerkte_fed"],
        )
    zeilen = (tmp_path / "kalshi_preisspur.csv").read_text(
        encoding="utf-8"
    ).splitlines()
    assert len(zeilen) == 89  # ein Header, zwei Durchlaeufe


def test_fehler_beendet_den_rekorder_nicht(tmp_path):
    """Er laeuft neben einem Live-Bot — ein toter Event darf nichts kippen."""
    def kaputt(_ev):
        raise RuntimeError("429 Too Many Requests")

    zeilen = kalshi_recorder.einmal(["KXX"], tmp_path, {}, hole=kaputt)
    assert zeilen == []
    protokoll = (tmp_path / "kalshi_ereignisse.jsonl").read_text(
        encoding="utf-8"
    )
    assert "fehler" in protokoll and "429" in protokoll
