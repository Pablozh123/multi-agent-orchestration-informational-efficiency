"""Tests fuer den read-only Pilot-Watcher (Regeln aus Protokoll V2)."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone

from operations.pilot import watcher

NOW = datetime(2026, 7, 16, 12, 0, 0, tzinfo=timezone.utc)


def markt(
    mid: str = "m1",
    question: str = "Will the favorite win the July final?",
    description: str = "Resolves to the official result.",
    prices: tuple[str, str] = ("0.93", "0.07"),
    end: str = "2026-07-25T12:00:00Z",
    **extra: object,
) -> dict:
    m = {
        "id": mid,
        "question": question,
        "description": description,
        "outcomes": json.dumps(["Yes", "No"]),
        "outcomePrices": json.dumps(list(prices)),
        "clobTokenIds": json.dumps([f"tok_{mid}_yes", f"tok_{mid}_no"]),
        "endDate": end,
    }
    m.update(extra)
    return m


def buch(ask: float, size: float = 40.0) -> dict:
    return {
        "asks": [{"price": str(ask), "size": str(size)}],
        "bids": [{"price": "0.50", "size": "10"}],
    }


def fetch_aus(buecher: dict):
    def fetch(token_id: str) -> dict:
        return buecher.get(token_id, {"asks": [], "bids": []})

    return fetch


# ------------------------------------------------- eingefrorene Parameter


def test_parameter_entsprechen_protokoll_v2() -> None:
    assert watcher.ARM1_MAX_ENTRY_PREIS == 0.97
    assert watcher.ARM2_MIN_PREIS == 0.90
    assert watcher.ARM2_MAX_PREIS == 0.97
    assert watcher.ARM2_MAX_RESTLAUFZEIT_TAGE == 21.0
    assert watcher.ARM2_SPAETESTE_AUFLOESUNG.strftime("%Y-%m-%d") == "2026-08-02"
    assert watcher.MIN_BUCHTIEFE_USDC == 20.0
    assert watcher.MAX_TRADES_PRO_MARKT == 1
    assert "PILOT_PROTOKOLL_ECHTGELD_2026-07-11" in watcher.PROTOKOLL_QUELLE


# ------------------------------------------------- Arm 2


def test_arm2_signal_im_fenster() -> None:
    m = markt()
    signale, _ = scan_einfach(m, ask=0.93)
    assert len(signale) == 1
    s = signale[0]
    assert s.arm == "arm2"
    assert s.status == "signal"
    assert s.seite == "Yes"
    assert s.signal_preis == 0.93
    assert s.buchtiefe_usd >= watcher.MIN_BUCHTIEFE_USDC
    assert s.restlaufzeit_tage == 9.0


def scan_einfach(m: dict, ask: float, size: float = 40.0, **scan_kwargs):
    tok = json.loads(m["clobTokenIds"])[0]
    return watcher.scan(
        [m], NOW, fetch_book_fn=fetch_aus({tok: buch(ask, size)}), **scan_kwargs
    )


def test_arm2_preis_unter_090_kein_signal() -> None:
    signale, stat = scan_einfach(markt(), ask=0.89)
    assert signale == []
    assert stat["arm2_preis_ausserhalb_090_097"] == 1


def test_arm2_preis_ueber_097_kein_signal() -> None:
    signale, stat = scan_einfach(markt(), ask=0.98)
    assert signale == []
    assert stat["arm2_preis_ausserhalb_090_097"] == 1


def test_arm2_restlaufzeit_ueber_21_tagen() -> None:
    m = markt(end="2026-08-07T12:00:00Z")
    signale, stat = scan_einfach(m, ask=0.93)
    assert signale == []
    # Nach dem 02.08. greift zuerst der Aufloesungs-Stichtag.
    assert stat["arm2_aufloesung_nach_stichtag"] == 1


def test_arm2_aufloesung_nach_stichtag_trotz_kurzer_laufzeit() -> None:
    now = datetime(2026, 7, 30, 12, 0, 0, tzinfo=timezone.utc)
    m = markt(end="2026-08-03T12:00:00Z")  # nur 4 Tage, aber nach 02.08.
    tok = json.loads(m["clobTokenIds"])[0]
    signale, stat = watcher.scan(
        [m], now, fetch_book_fn=fetch_aus({tok: buch(0.93)})
    )
    assert signale == []
    assert stat["arm2_aufloesung_nach_stichtag"] == 1


def test_arm2_unklare_aufloesung() -> None:
    m = markt(description="Resolves Yes unless the event is postponed.")
    signale, stat = scan_einfach(m, ask=0.93)
    assert signale == []
    assert stat["arm2_aufloesungsregel_unklar"] == 1


def test_arm2_laufender_streit() -> None:
    m = markt(umaResolutionStatus="disputed")
    signale, stat = scan_einfach(m, ask=0.93)
    assert signale == []
    assert stat["arm2_laufender_streit"] == 1


def test_arm2_tiefe_unter_20_usdc() -> None:
    # 0.93 * 15 Shares = 13.95 USD < 20 USD
    signale, stat = scan_einfach(markt(), ask=0.93, size=15.0)
    assert signale == []
    assert stat["arm2_tiefe_unter_20"] == 1


def test_nicht_binaere_maerkte_werden_uebersprungen() -> None:
    m = markt()
    m["outcomes"] = json.dumps(["A", "B", "C"])
    signale, stat = scan_einfach(m, ask=0.93)
    assert signale == []
    assert stat["nicht_binaer"] == 1


# ------------------------------------------------- Arm 1


def krypto_markt(mid: str = "k1", **ueberschreibungen: object) -> dict:
    felder: dict = {
        "question": "Will Bitcoin be above $120,000 on July 10?",
        "description": "Resolves via the Binance BTCUSDT 1-minute close.",
        "prices": ("0.94", "0.06"),
        "end": "2026-07-10T12:00:00Z",  # Stichtag verstrichen (NOW = 16.07.)
    }
    felder.update(ueberschreibungen)
    return markt(mid=mid, **felder)


def test_arm1_kandidat_bei_verstrichenem_stichtag() -> None:
    signale, _ = scan_einfach(krypto_markt(), ask=0.94)
    assert len(signale) == 1
    s = signale[0]
    assert s.arm == "arm1"
    assert s.status == "kandidat_referenz_pruefen"
    assert s.regel == "arm1_stichtag_verstrichen"
    assert "manuell" in s.hinweis


def test_arm1_preis_ueber_097_kein_kandidat() -> None:
    signale, stat = scan_einfach(krypto_markt(), ask=0.985)
    assert signale == []
    assert stat["arm1_preis_ueber_097"] == 1


def test_arm1_ohne_dokumentierte_referenzquelle_kein_kandidat() -> None:
    m = krypto_markt(description="Resolves to the official price.")
    # Ohne Referenzquelle faellt der Markt in den Arm-2-Pfad und scheitert
    # dort am bereits verstrichenen Enddatum.
    signale, stat = scan_einfach(m, ask=0.94)
    assert signale == []
    assert stat["arm2_bereits_abgelaufen"] == 1


def test_arm1_nicht_krypto_kein_kandidat() -> None:
    m = markt(
        question="Will the incumbent be above 50% on July 10?",
        description="Resolves via the Binance feed.",  # Quelle allein reicht nicht
        end="2026-07-10T12:00:00Z",
    )
    signale, stat = scan_einfach(m, ask=0.94)
    assert signale == []
    assert stat["arm2_bereits_abgelaufen"] == 1


def test_arm1_hat_vorrang_vor_arm2() -> None:
    m = krypto_markt(
        question="Will Bitcoin ever reach $150,000 before August?",
        end="2026-07-28T12:00:00Z",  # laeuft noch; Arm 2 waere auch moeglich
    )
    signale, _ = scan_einfach(m, ask=0.93)
    assert len(signale) == 1
    assert signale[0].arm == "arm1"
    assert signale[0].regel == "arm1_schwelle_moeglich"


# ------------------------------------------------- Dedupe und Ablage


def test_max_ein_trade_pro_markt_dedupe() -> None:
    signale, stat = scan_einfach(markt(), ask=0.93, gehandelte_maerkte={"m1"})
    assert signale == []
    assert stat["bereits_gehandelt"] == 1


def test_bereits_signalisierte_kombination_wird_uebersprungen() -> None:
    signale, stat = scan_einfach(
        markt(), ask=0.93, signalisierte={("arm2", "m1")}
    )
    assert signale == []
    assert stat["arm2_bereits_signalisiert"] == 1


def test_scan_ist_deterministisch() -> None:
    m = [markt(), krypto_markt()]
    buecher = {
        json.loads(m[0]["clobTokenIds"])[0]: buch(0.93),
        json.loads(m[1]["clobTokenIds"])[0]: buch(0.94),
    }
    lauf1 = watcher.scan(m, NOW, fetch_book_fn=fetch_aus(buecher))
    lauf2 = watcher.scan(m, NOW, fetch_book_fn=fetch_aus(buecher))
    assert [s.__dict__ for s in lauf1[0]] == [s.__dict__ for s in lauf2[0]]
    assert lauf1[1] == lauf2[1]


def test_signal_kappe_pro_lauf(tmp_path) -> None:
    maerkte = [markt(mid=f"m{i}") for i in range(watcher.MAX_SIGNALE_PRO_LAUF + 5)]
    buecher = {
        json.loads(m["clobTokenIds"])[0]: buch(0.93) for m in maerkte
    }
    signale, stat = watcher.scan(maerkte, NOW, fetch_book_fn=fetch_aus(buecher))
    assert len(signale) == watcher.MAX_SIGNALE_PRO_LAUF
    assert stat["gekappt"] == 5


def test_trades_template_hat_pflichtfelder(tmp_path) -> None:
    pfad = watcher.ensure_trades_template(tmp_path / "trades.csv")
    with open(pfad, newline="", encoding="utf-8") as f:
        header = next(csv.reader(f))
    assert header == watcher.TRADES_CSV_FELDER
    # Pflichtfelder aus dem Protokoll, Abschnitt "Dokumentation je Trade":
    for feld in [
        "zeitstempel_utc", "markt_id", "arm", "signalpreis",
        "ausfuehrungspreis", "gebuehren_usd", "slippage",
        "orderbuchtiefe_einstieg_usd", "exit_grund", "bemerkung",
    ]:
        assert feld in header
    # Keine Wallet-Spalten in Pilot-Artefakten.
    assert not any("wallet" in f.lower() for f in header)


def test_signale_schreiben_und_dedupe_lesen(tmp_path) -> None:
    signale, _ = scan_einfach(markt(), ask=0.93)
    pfad = watcher.schreibe_signale(signale, tmp_path / "signals.csv")
    assert watcher.lade_signalisierte(pfad) == {("arm2", "m1")}
    with open(pfad, newline="", encoding="utf-8") as f:
        zeilen = list(csv.DictReader(f))
    assert len(zeilen) == 1
    assert zeilen[0]["market_id"] == "m1"
    assert not any("wallet" in k.lower() for k in zeilen[0])


def test_gehandelte_maerkte_aus_trades_csv(tmp_path) -> None:
    pfad = watcher.ensure_trades_template(tmp_path / "trades.csv")
    with open(pfad, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=watcher.TRADES_CSV_FELDER)
        writer.writerow({"zeitstempel_utc": "2026-07-16T10:00:00Z",
                         "markt_id": "m7", "arm": "arm2"})
    assert watcher.lade_gehandelte_maerkte(pfad) == {"m7"}


def test_metadata_dokumentiert_parameter_und_ohne_orderpfad(tmp_path) -> None:
    pfad = watcher.schreibe_metadata(
        {"maerkte": 3}, 1, NOW, tmp_path / "meta.json"
    )
    with open(pfad, encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["parameter"]["arm2_min_preis"] == 0.90
    assert meta["parameter"]["arm2_max_preis"] == 0.97
    assert "read-only" in meta["order_pfad"]
    assert "PILOT_PROTOKOLL" in meta["protokoll"]
