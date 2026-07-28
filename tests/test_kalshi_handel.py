"""Kalshi Phase 2/3: Gebuehrendeckel, Verschreibungsfilter, Ausfuehrung.

Offline. Die Signaturpruefung erzeugt ein Wegwerf-RSA-Schluesselpaar und
verifiziert die Signatur gegen den oeffentlichen Teil — es wird nie ein
echter Key gelesen und nie ein Request abgesetzt.

Die beiden Verschreibungsfaelle vom 28.07. sind als Regressionstests
verankert: Boeing "Guidance" (Transkript schrieb "guides") und PayPal
"Agentic Commerce" (Transkript schrieb "agent e-commerce"). Beide Maerkte
loesten YES auf, waehrend unser Vollpass 0 zaehlte — auf einer per Video
aufgeloesten Venue muss ein NO in genau diesen Faellen unterbleiben.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from operations.pipeline import (
    config,
    kalshi_client,
    kalshi_decision,
    kalshi_execution,
    kalshi_rules,
)
from operations.pipeline.decision import Decision

FIXTURE = Path(__file__).parent / "fixtures" / "kalshi_mentions_snapshot.json"


@pytest.fixture(scope="module")
def snapshot() -> dict:
    with open(FIXTURE, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def regel(snapshot):
    markt = next(
        m for m in snapshot["maerkte_meta"] if m["ticker"].endswith("-LLAM")
    )
    return kalshi_rules.build_rule(markt)


def _decision(action="YES", outcome="Yes", preis=0.50) -> Decision:
    return Decision("KXTEST-1-ABC", action, "KXTEST-1-ABC", outcome, preis, "test")


# --- Buch-Adapter -----------------------------------------------------


def test_buch_adapter_spiegelt_no_gebote_als_yes_asks(snapshot):
    """Ein YES-Ask ist das Spiegelbild eines NO-Gebots."""
    buch = kalshi_client.buch_als_polymarket(snapshot["orderbuch_fed_ai"])
    assert buch["asks"] and buch["bids"]
    # Asks aufsteigend, Bids absteigend (CLOB-Konvention).
    assert buch["asks"] == sorted(buch["asks"], key=lambda a: a["price"])
    assert buch["bids"] == sorted(
        buch["bids"], key=lambda b: b["price"], reverse=True
    )
    # Bestes Level deckt sich mit der direkten Quote-Ableitung.
    yes_bid, yes_ask = kalshi_client.yes_quotes(snapshot["orderbuch_fed_ai"])
    assert buch["bids"][0]["price"] == pytest.approx(yes_bid)
    assert buch["asks"][0]["price"] == pytest.approx(yes_ask)


def test_buch_adapter_speist_die_tiefenrechnung(snapshot):
    """Die Groessenlogik der Basisklasse laeuft unveraendert auf Kalshi."""
    from operations.pipeline.orderbook import ausfuehrbare_tiefe_usd

    buch = kalshi_client.buch_als_polymarket(snapshot["orderbuch_fed_ai"])
    tiefe = ausfuehrbare_tiefe_usd(buch, buch["asks"][0]["price"])
    assert tiefe > 0


def test_buch_adapter_no_sicht_dreht_die_seiten(snapshot):
    yes = kalshi_client.buch_als_polymarket(snapshot["orderbuch_fed_ai"], "yes")
    no = kalshi_client.buch_als_polymarket(snapshot["orderbuch_fed_ai"], "no")
    assert no["asks"][0]["price"] == pytest.approx(1.0 - yes["bids"][0]["price"])


# --- Gebuehren im Deckel ---------------------------------------------


def test_vollpreis_enthaelt_die_gebuehr():
    assert kalshi_decision.vollpreis(0.50) == pytest.approx(0.52)
    assert kalshi_decision.vollpreis(0.90) == pytest.approx(0.91)


def test_deckel_greift_auf_den_vollpreis_nicht_den_ask():
    """Ein Ask knapp unter der Grenze kann inklusive Gebuehr darueber liegen."""
    grenze = config.ASK_OBERGRENZE  # 0.90
    ask = round(grenze - 0.005, 4)  # 0.895 — roh unter der Grenze
    assert ask <= grenze
    assert kalshi_decision.vollpreis(ask) > grenze
    assert kalshi_decision.deckel_erreicht(ask, grenze)


def test_yes_wird_bei_zu_teurem_vollpreis_abgelehnt(regel):
    d = kalshi_decision.entscheide_yes(regel, 1, round(config.ASK_OBERGRENZE, 4))
    assert d.action == "NONE"
    assert "vollpreis" in d.reason


def test_yes_bei_einem_treffer_und_bezahlbarem_preis(regel):
    d = kalshi_decision.entscheide_yes(regel, 1, 0.40)
    assert d.action == "YES"
    assert d.limit_price == 0.40
    assert d.token_id == regel.market_id


def test_yes_braucht_keinen_schwellenpuffer(regel):
    """Kalshi-Mentions sind binaer — ein Treffer genuegt."""
    assert regel.schwelle == 1
    assert kalshi_decision.entscheide_yes(regel, 0, 0.40).action == "NONE"
    assert kalshi_decision.entscheide_yes(regel, 1, 0.40).action == "YES"


# --- Verschreibungsfilter --------------------------------------------


def test_guidance_fall_boeing():
    """Das Boeing-Band schrieb "guides" — gesagt war wohl "guidance"."""
    verdacht = kalshi_decision.nachbar_verdacht(
        ["Guidance"],
        "given the guides that we have related to delivery this year",
    )
    assert "guides" in [v.lower() for v in verdacht]


def test_agentic_fall_paypal():
    """Das PayPal-Band schrieb "agent e-commerce" fuer "agentic commerce"."""
    verdacht = kalshi_decision.nachbar_verdacht(
        ["Agentic Commerce"], "we see agent e-commerce as a contributor"
    )
    assert "agent" in [v.lower() for v in verdacht]


def test_echter_treffer_ist_kein_verdacht():
    """Das Zielwort selbst gehoert zu YES, nicht in den NO-Filter."""
    assert kalshi_decision.nachbar_verdacht(
        ["Guidance"], "our guidance for the year"
    ) == []


def test_gezaehlte_pluralform_ist_kein_verdacht():
    assert kalshi_decision.nachbar_verdacht(
        ["Llama"], "we shipped two Llamas"
    ) == []


def test_kurze_zielwoerter_erzeugen_keinen_verdacht():
    """Unter der Stammlaenge waeren Zufallstreffer die Regel."""
    assert kalshi_decision.nachbar_verdacht(["Tax"], "we took a taxi") == []


def test_unverwandtes_wort_ist_kein_verdacht():
    assert kalshi_decision.nachbar_verdacht(
        ["Guidance"], "revenue grew across every segment"
    ) == []


# --- NO-Entscheidung --------------------------------------------------


def test_no_ohne_vollpass_transkript_gesperrt(regel):
    d = kalshi_decision.entscheide_no(regel, 0, 0.20, transkript="")
    assert d.action == "NONE"
    assert d.reason == "kein_vollpass_transkript"


def test_no_bei_verschreibungs_verdacht_gesperrt(snapshot):
    """Der Kernfall: Vollpass zaehlt 0, das Band zeigt eine Nachbarform."""
    markt = dict(
        next(m for m in snapshot["maerkte_meta"] if m["ticker"].endswith("-LLAM"))
    )
    markt["custom_strike"] = {"Word": "Guidance"}
    markt["ticker"] = "KXTEST-1-GUID"
    r = kalshi_rules.build_rule(markt)
    d = kalshi_decision.entscheide_no(
        r, 0, 0.20, transkript="the guides that we have for the year"
    )
    assert d.action == "NONE"
    assert "verschreibungs_verdacht" in d.reason


def test_no_bei_sauberem_vollpass(regel):
    d = kalshi_decision.entscheide_no(
        regel, 0, 0.20, transkript="revenue grew across every segment"
    )
    assert d.action == "NO"
    assert d.outcome == "No"


def test_no_bei_treffer_gesperrt(regel):
    d = kalshi_decision.entscheide_no(
        regel, 1, 0.20, transkript="sauberer text"
    )
    assert d.action == "NONE"
    assert "endstand 1" in d.reason


def test_no_deckel_nutzt_die_niedrigere_grenze(regel):
    """NO behaelt den strengeren Deckel — inklusive Gebuehr."""
    zu_teuer = round(config.NO_ASK_OBERGRENZE, 4)
    d = kalshi_decision.entscheide_no(
        regel, 0, zu_teuer, transkript="revenue grew"
    )
    assert d.action == "NONE"
    assert "vollpreis" in d.reason


# --- Signatur ---------------------------------------------------------


@pytest.fixture(scope="module")
def schluesselpaar():
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key, key.public_key()


def test_signatur_ist_gegen_den_public_key_pruefbar(schluesselpaar):
    import base64

    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    privat, oeffentlich = schluesselpaar
    sig = kalshi_execution.signatur(privat, 1750000000000, "POST",
                                    kalshi_execution.ORDER_PFAD)
    nachricht = f"1750000000000POST{kalshi_execution.ORDER_PFAD}".encode()
    oeffentlich.verify(
        base64.b64decode(sig), nachricht,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256(),
    )


def test_signatur_bindet_methode_und_pfad(schluesselpaar):
    """Andere Methode oder anderer Pfad -> andere Nachricht."""
    import base64

    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    privat, oeffentlich = schluesselpaar
    sig = kalshi_execution.signatur(privat, 1, "GET", "/portfolio/balance")
    falsch = b"1POST/portfolio/balance"
    with pytest.raises(Exception):
        oeffentlich.verify(
            base64.b64decode(sig), falsch,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.DIGEST_LENGTH),
            hashes.SHA256(),
        )


def test_auth_header_traegt_die_drei_felder(schluesselpaar):
    privat, _ = schluesselpaar
    kopf = kalshi_execution.auth_header("kid-1", privat, "POST", "/x", 42)
    assert kopf["KALSHI-ACCESS-KEY"] == "kid-1"
    assert kopf["KALSHI-ACCESS-TIMESTAMP"] == "42"
    assert kopf["KALSHI-ACCESS-SIGNATURE"]


# --- Ordergroesse und -koerper ---------------------------------------


def test_kontrakte_beruecksichtigen_die_gebuehr():
    """Ohne Gebuehrenpuffer waere die Order nicht gedeckt."""
    ohne = 10.0 / 0.50
    mit = kalshi_execution.kontrakte_aus_usd(10.0, 0.50)
    assert mit < ohne
    assert mit == pytest.approx(10.0 / 0.52, abs=0.01)


def test_kontrakte_werden_abgerundet():
    assert kalshi_execution.kontrakte_aus_usd(1.0, 0.50) == pytest.approx(1.92)


def test_kontrakte_bei_null_preis():
    assert kalshi_execution.kontrakte_aus_usd(10.0, 0.0) == 0.0


def test_no_kauf_wird_als_yes_verkauf_quotiert():
    """V2 kennt nur die YES-Seite: NO zu 0.19 ist YES-Ask zu 0.81."""
    d = _decision("NO", "No", 0.19)
    assert kalshi_execution.ist_no(d)
    assert kalshi_execution.yes_seiten_preis(d) == pytest.approx(0.81)


def test_yes_kauf_behaelt_seinen_preis():
    d = _decision("YES", "Yes", 0.40)
    assert kalshi_execution.yes_seiten_preis(d) == pytest.approx(0.40)


def test_order_koerper_folgt_dem_v2_schema(schluesselpaar, monkeypatch, tmp_path):
    """Pflichtfelder, Strings statt Zahlen, FOK, korrekte Seite."""
    ex = object.__new__(kalshi_execution.KalshiExecutor)
    koerper = kalshi_execution.KalshiExecutor._order_koerper(
        ex, _decision("NO", "No", 0.19), 12.0
    )
    assert koerper["ticker"] == "KXTEST-1-ABC"
    assert koerper["side"] == "ask"          # NO-Kauf = YES-Verkauf
    assert koerper["price"] == "0.8100"      # 1 - 0.19, YES-Sicht
    assert koerper["count"] == "12.00"       # FixedPointCount als String
    assert koerper["time_in_force"] == "fill_or_kill"
    assert koerper["self_trade_prevention_type"] == "taker_at_cross"
    assert koerper["client_order_id"]
    for pflicht in ("ticker", "side", "count", "price", "time_in_force",
                    "self_trade_prevention_type"):
        assert pflicht in koerper


def test_order_koerper_yes_seite():
    ex = object.__new__(kalshi_execution.KalshiExecutor)
    koerper = kalshi_execution.KalshiExecutor._order_koerper(
        ex, _decision("YES", "Yes", 0.40), 5.0
    )
    assert koerper["side"] == "bid"
    assert koerper["price"] == "0.4000"


# --- Buchung aus der Orderantwort ------------------------------------


def test_buchung_nutzt_gemessenen_fillpreis_und_gebuehr():
    """Kein Kontostand-Delta — die Antwort ist die Quelle (PayPal-Lehre)."""
    d = _decision("YES", "Yes", 0.64)
    ergebnis = kalshi_execution.ergebnis_aus_antwort(d, {
        "order_id": "abc123", "fill_count": "25.00",
        "remaining_count": "0.00", "average_fill_price": "0.6300",
        "average_fee_paid": "0.0200",
    })
    assert ergebnis.status == "live_fill"
    assert ergebnis.size_shares == pytest.approx(25.0)
    assert ergebnis.size_usd == pytest.approx(25 * (0.63 + 0.02), abs=0.01)
    assert "average_fill_price" in ergebnis.detail
    assert "average_fee_paid" in ergebnis.detail


def test_buchung_dreht_den_fillpreis_bei_no():
    """average_fill_price steht in YES-Sicht; NO kostet 1 - Preis."""
    d = _decision("NO", "No", 0.19)
    ergebnis = kalshi_execution.ergebnis_aus_antwort(d, {
        "order_id": "abc", "fill_count": "10.00",
        "average_fill_price": "0.8100", "average_fee_paid": "0.0100",
    })
    assert ergebnis.size_usd == pytest.approx(10 * (0.19 + 0.01), abs=0.01)


def test_buchung_faellt_auf_die_formel_zurueck():
    d = _decision("YES", "Yes", 0.50)
    ergebnis = kalshi_execution.ergebnis_aus_antwort(
        d, {"order_id": "abc", "fill_count": "4.00"}
    )
    assert ergebnis.status == "live_fill"
    assert "limit_geschaetzt" in ergebnis.detail
    assert "formel" in ergebnis.detail
    assert ergebnis.size_usd == pytest.approx(4 * 0.52, abs=0.01)


def test_fok_ohne_fill_ist_gave_up():
    d = _decision()
    ergebnis = kalshi_execution.ergebnis_aus_antwort(d, {
        "order_id": "abc", "fill_count": "0.00", "remaining_count": "10.00",
    })
    assert ergebnis.status == "gave_up"
    assert ergebnis.size_usd == 0.0


# --- Dry-Run-Executor -------------------------------------------------


def test_dry_run_bucht_gebuehr_mit(tmp_path, snapshot):
    ex = kalshi_execution.KalshiDryRunExecutor(tmp_path / "log.jsonl")
    buch = kalshi_client.buch_als_polymarket(snapshot["orderbuch_fed_ai"])
    ask = buch["asks"][0]["price"]
    ergebnis = ex.place(_decision("YES", "Yes", ask), buch)
    assert ergebnis.status == "dry_run_fill"
    # Einsatz je Kontrakt liegt ueber dem reinen Preis.
    assert ergebnis.size_usd > ergebnis.size_shares * ask
    assert ex.ausgegeben_usd == ergebnis.size_usd


def test_ohne_tiefe_unter_dem_limit_kein_kauf(tmp_path, snapshot):
    """Die Tiefenpruefung der Basisklasse greift auf Kalshi unveraendert."""
    ex = kalshi_execution.KalshiDryRunExecutor(tmp_path / "log.jsonl")
    buch = kalshi_client.buch_als_polymarket(snapshot["orderbuch_fed_ai"])
    zu_billig = round(buch["asks"][0]["price"] - 0.20, 4)
    ergebnis = ex.place(_decision("YES", "Yes", zu_billig), buch)
    assert ergebnis.status == "skipped_budget"
    assert ex.ausgegeben_usd == 0.0


def test_dry_run_haelt_den_stop_schalter(tmp_path, snapshot, monkeypatch):
    stop = tmp_path / "STOP"
    stop.write_text("x", encoding="utf-8")
    monkeypatch.setattr(config, "STOP_FILE", stop)
    ex = kalshi_execution.KalshiDryRunExecutor(tmp_path / "log.jsonl")
    buch = kalshi_client.buch_als_polymarket(snapshot["orderbuch_fed_ai"])
    ergebnis = ex.place(_decision("YES", "Yes", 0.50), buch)
    assert ergebnis.status == "skipped_stop"


def test_baue_executor_ohne_live_platziert_nichts(tmp_path):
    ex = kalshi_execution.baue_executor(False, tmp_path / "log.jsonl")
    assert isinstance(ex, kalshi_execution.KalshiDryRunExecutor)


def test_live_executor_ohne_key_bricht_ab(tmp_path, monkeypatch):
    monkeypatch.delenv("KALSHI_KEY_ID", raising=False)
    monkeypatch.delenv("KALSHI_PRIVATE_KEY_PFAD", raising=False)
    monkeypatch.setattr(
        "operations.pipeline.kalshi_execution.load_dotenv", lambda *a, **k: None,
        raising=False,
    )
    with pytest.raises(RuntimeError, match="KALSHI_KEY_ID"):
        kalshi_execution.KalshiExecutor(tmp_path / "log.jsonl")
