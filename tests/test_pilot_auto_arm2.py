"""Tests fuer die automatisierte Arm-2-Ausfuehrung (Protokoll V3)."""

from __future__ import annotations

import csv
from datetime import date

import pytest

from operations.pilot import auto_arm2, watcher

SIGNAL_FELDER = watcher.SIGNAL_CSV_FELDER


def schreibe_signale(pilot_dir, eintraege: list[dict]) -> None:
    pfad = pilot_dir / "signals.csv"
    with open(pfad, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SIGNAL_FELDER)
        writer.writeheader()
        for e in eintraege:
            writer.writerow({k: e.get(k, "") for k in SIGNAL_FELDER})


def signal(market_id: str, ts: str = "2026-07-22T10:00:00Z", **extra) -> dict:
    basis = {
        "ts_utc": ts, "arm": "arm2", "market_id": market_id,
        "frage": f"Frage {market_id}?", "seite": "No",
        "token_id": f"tok_{market_id}", "signal_preis": "0.95",
        "buchtiefe_usd": "500", "restlaufzeit_tage": "5",
        "regel": "arm2_favorit_090_097_max21d", "ausloesewert": "ask=0.95",
        "status": "signal",
    }
    basis.update(extra)
    return basis


def buch(ask: float, size: float = 100.0) -> dict:
    return {"asks": [{"price": str(ask), "size": str(size)}],
            "bids": [{"price": "0.5", "size": "10"}]}


def fetch_fest(ask: float, size: float = 100.0):
    def fetch(token_id: str) -> dict:
        return buch(ask, size)
    return fetch


@pytest.fixture
def pilot_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(auto_arm2.config, "STOP_FILE", tmp_path / "KEIN_STOP")
    watcher.ensure_trades_template(tmp_path / "trades.csv")
    return tmp_path


# ------------------------------------------------- Parameter


def test_parameter_entsprechen_protokoll_v3() -> None:
    assert auto_arm2.EINSATZ_USDC == 5.0
    assert auto_arm2.BUDGET_USDC == 100.0
    assert auto_arm2.MAX_TRADES == 20
    assert auto_arm2.HANDELSFENSTER_BIS == date(2026, 8, 1)
    # Arm-2-Regeln kommen aus dem Watcher, nicht aus einer zweiten Quelle.
    assert auto_arm2.MIN_PREIS == watcher.ARM2_MIN_PREIS
    assert auto_arm2.MAX_PREIS == watcher.ARM2_MAX_PREIS
    assert auto_arm2.MIN_TIEFE_USDC == watcher.MIN_BUCHTIEFE_USDC
    assert "Version 3" in auto_arm2.PROTOKOLL_QUELLE


# ------------------------------------------------- Sicherheitsnetze


def test_dry_run_ist_der_standard(pilot_dir) -> None:
    schreibe_signale(pilot_dir, [signal("m1")])
    bericht = auto_arm2.lauf(
        pilot_dir=pilot_dir, fetch=fetch_fest(0.95), heute=date(2026, 7, 22)
    )
    assert bericht["modus"] == "dry_run"
    assert bericht["gekauft"] == 1


def test_dry_run_fasst_das_echte_journal_nicht_an(pilot_dir) -> None:
    """Probelaeufe duerfen den Protokoll-Nachweis nicht verfaelschen."""

    echtes_journal = pilot_dir / "trades.csv"
    vorher = echtes_journal.read_text(encoding="utf-8")
    schreibe_signale(pilot_dir, [signal("m1")])
    bericht = auto_arm2.lauf(
        pilot_dir=pilot_dir, fetch=fetch_fest(0.95), heute=date(2026, 7, 22)
    )
    assert bericht["journal"] == "trades_dry_run.csv"
    assert echtes_journal.read_text(encoding="utf-8") == vorher
    assert (pilot_dir / "trades_dry_run.csv").exists()


def test_dry_run_respektiert_echte_trades(pilot_dir) -> None:
    """Ein echt gehandelter Markt bleibt auch im Probelauf tabu."""

    with open(pilot_dir / "trades.csv", "a", encoding="utf-8", newline="") as handle:
        csv.DictWriter(handle, fieldnames=watcher.TRADES_CSV_FELDER).writerow(
            {"zeitstempel_utc": "2026-07-22T09:00:00Z", "markt_id": "m1",
             "arm": "arm2", "groesse_usd": "5.0"}
        )
    schreibe_signale(pilot_dir, [signal("m1")])
    bericht = auto_arm2.lauf(
        pilot_dir=pilot_dir, fetch=fetch_fest(0.95), heute=date(2026, 7, 22)
    )
    assert bericht["gekauft"] == 0


def test_kill_switch_stoppt_sofort(pilot_dir, monkeypatch) -> None:
    stop = pilot_dir / "STOP"
    stop.write_text("halt", encoding="utf-8")
    monkeypatch.setattr(auto_arm2.config, "STOP_FILE", stop)
    schreibe_signale(pilot_dir, [signal("m1")])
    bericht = auto_arm2.lauf(
        pilot_dir=pilot_dir, fetch=fetch_fest(0.95), heute=date(2026, 7, 22)
    )
    assert bericht["gekauft"] == 0
    assert "Kill-Switch" in bericht["abbruch"]


def test_nach_fensterende_wird_nicht_gehandelt(pilot_dir) -> None:
    schreibe_signale(pilot_dir, [signal("m1")])
    bericht = auto_arm2.lauf(
        pilot_dir=pilot_dir, fetch=fetch_fest(0.95), heute=date(2026, 8, 2)
    )
    assert bericht["gekauft"] == 0
    assert "Handelsfenster" in bericht["abbruch"]


def test_budgetdeckel_begrenzt_die_gesamtsumme(pilot_dir) -> None:
    schreibe_signale(pilot_dir, [signal(f"m{i}", ts=f"2026-07-22T10:{i:02d}:00Z")
                                 for i in range(30)])
    bericht = auto_arm2.lauf(
        pilot_dir=pilot_dir, fetch=fetch_fest(0.95), heute=date(2026, 7, 22)
    )
    assert bericht["gekauft"] == auto_arm2.MAX_TRADES
    assert bericht["ausgegeben_usd"] <= auto_arm2.BUDGET_USDC
    assert "Deckel erreicht" in bericht["abbruch"]


def test_ein_trade_je_markt(pilot_dir) -> None:
    schreibe_signale(pilot_dir, [signal("m1"), signal("m1", ts="2026-07-22T11:00:00Z")])
    bericht = auto_arm2.lauf(
        pilot_dir=pilot_dir, fetch=fetch_fest(0.95), heute=date(2026, 7, 22)
    )
    assert bericht["gekauft"] == 1


def test_bereits_gehandelte_maerkte_werden_uebersprungen(pilot_dir) -> None:
    schreibe_signale(pilot_dir, [signal("m1")])
    auto_arm2.lauf(pilot_dir=pilot_dir, fetch=fetch_fest(0.95),
                   heute=date(2026, 7, 22))
    zweiter = auto_arm2.lauf(pilot_dir=pilot_dir, fetch=fetch_fest(0.95),
                             heute=date(2026, 7, 22))
    assert zweiter["gekauft"] == 0


def test_laufgrenze_bremst_einen_einzelnen_lauf(pilot_dir) -> None:
    schreibe_signale(pilot_dir, [signal(f"m{i}", ts=f"2026-07-22T10:{i:02d}:00Z")
                                 for i in range(5)])
    bericht = auto_arm2.lauf(
        pilot_dir=pilot_dir, fetch=fetch_fest(0.95), heute=date(2026, 7, 22),
        max_neue_trades=2,
    )
    assert bericht["gekauft"] == 2


# ------------------------------------------------- Neupruefung am Buch


def test_veraltetes_signal_wird_am_buch_abgelehnt(pilot_dir) -> None:
    """Signal sagt 0.95, das Buch steht inzwischen bei 0.99."""

    schreibe_signale(pilot_dir, [signal("m1")])
    bericht = auto_arm2.lauf(
        pilot_dir=pilot_dir, fetch=fetch_fest(0.99), heute=date(2026, 7, 22)
    )
    assert bericht["gekauft"] == 0
    assert bericht["abgelehnt"]["preis_ausserhalb_fenster"] == 1


def test_zu_duennes_buch_wird_abgelehnt(pilot_dir) -> None:
    schreibe_signale(pilot_dir, [signal("m1")])
    bericht = auto_arm2.lauf(
        pilot_dir=pilot_dir, fetch=fetch_fest(0.95, size=10), heute=date(2026, 7, 22)
    )
    assert bericht["gekauft"] == 0
    assert bericht["abgelehnt"]["tiefe_unter_minimum"] == 1


def test_boersenminimum_von_fuenf_anteilen(pilot_dir, monkeypatch) -> None:
    """Bei 5 USDC und hohem Preis darf kein Zwerg-Auftrag entstehen."""

    monkeypatch.setattr(auto_arm2, "EINSATZ_USDC", 1.0)  # 1 USDC = ~1 Anteil
    schreibe_signale(pilot_dir, [signal("m1")])
    bericht = auto_arm2.lauf(
        pilot_dir=pilot_dir, fetch=fetch_fest(0.95), heute=date(2026, 7, 22)
    )
    assert bericht["gekauft"] == 0
    assert bericht["abgelehnt"]["unter_boersenminimum"] == 1


def test_arm1_wird_nie_automatisch_gehandelt(pilot_dir) -> None:
    schreibe_signale(pilot_dir, [
        signal("k1", arm="arm1", status="kandidat_referenz_pruefen"),
        signal("m1"),
    ])
    bericht = auto_arm2.lauf(
        pilot_dir=pilot_dir, fetch=fetch_fest(0.95), heute=date(2026, 7, 22)
    )
    assert bericht["gekauft"] == 1
    with open(pilot_dir / "trades_dry_run.csv", encoding="utf-8", newline="") as handle:
        zeilen = list(csv.DictReader(handle))
    assert [z["markt_id"] for z in zeilen] == ["m1"]
    assert all(z["arm"] == "arm2" for z in zeilen)


# ------------------------------------------------- Auswahl und Journal


def test_auswahl_streng_in_signal_reihenfolge(pilot_dir) -> None:
    """Kein Rosinenpicken: aeltestes Signal zuerst, unabhaengig vom Preis."""

    schreibe_signale(pilot_dir, [
        signal("spaet", ts="2026-07-22T12:00:00Z"),
        signal("frueh", ts="2026-07-22T08:00:00Z"),
    ])
    auto_arm2.lauf(pilot_dir=pilot_dir, fetch=fetch_fest(0.95),
                   heute=date(2026, 7, 22), max_neue_trades=1)
    with open(pilot_dir / "trades_dry_run.csv", encoding="utf-8", newline="") as handle:
        zeilen = list(csv.DictReader(handle))
    assert [z["markt_id"] for z in zeilen] == ["frueh"]


def test_journal_hat_alle_pflichtfelder(pilot_dir) -> None:
    schreibe_signale(pilot_dir, [signal("m1")])
    auto_arm2.lauf(pilot_dir=pilot_dir, fetch=fetch_fest(0.95),
                   heute=date(2026, 7, 22))
    with open(pilot_dir / "trades_dry_run.csv", encoding="utf-8", newline="") as handle:
        zeile = list(csv.DictReader(handle))[0]
    for feld in ("zeitstempel_utc", "markt_id", "arm", "signalpreis",
                 "ausfuehrungspreis", "groesse_usd", "gebuehren_usd",
                 "slippage", "orderbuchtiefe_einstieg_usd", "exit_grund"):
        assert zeile[feld] != "", f"{feld} fehlt"
    # Protokoll-Definition: Ausfuehrung minus SIGNAL. Signal war 0.95, das
    # Buch stand beim Kauf ebenfalls auf 0.95 -> Abweichung null.
    assert zeile["signalpreis"] == "0.95"
    assert zeile["slippage"] == "0.0"
    assert "ask_bei_ausfuehrung=0.95" in zeile["bemerkung"]
    assert "Aufloesung" in zeile["exit_grund"]
    assert "automatisiert (V3)" in zeile["bemerkung"]
    assert not any("wallet" in k.lower() for k in zeile)


def test_slippage_misst_verfall_zwischen_signal_und_ausfuehrung(pilot_dir) -> None:
    """Signal bei 0.92, Buch beim Kauf auf 0.95 -> Slippage +0.03."""

    schreibe_signale(pilot_dir, [signal("m1", signal_preis="0.92")])
    auto_arm2.lauf(pilot_dir=pilot_dir, fetch=fetch_fest(0.95),
                   heute=date(2026, 7, 22))
    with open(pilot_dir / "trades_dry_run.csv", encoding="utf-8", newline="") as handle:
        zeile = list(csv.DictReader(handle))[0]
    assert zeile["signalpreis"] == "0.92"
    assert zeile["ausfuehrungspreis"] == "0.95"
    assert float(zeile["slippage"]) == pytest.approx(0.03, abs=1e-6)


def test_signalpreis_faellt_auf_ausloesewert_zurueck() -> None:
    assert auto_arm2.signalpreis_aus({"signal_preis": "0.93"}) == 0.93
    assert auto_arm2.signalpreis_aus({"ausloesewert": "ask=0.91"}) == 0.91
    assert auto_arm2.signalpreis_aus({"ausloesewert": "kaputt"}) is None


def test_dry_run_kaeufer_rechnet_anteile_und_betrag() -> None:
    ergebnis = DryRun = auto_arm2.DryRunKaeufer().kaufe("tok", 0.95, 5.0)
    assert ergebnis.status == "dry_run_fill"
    assert ergebnis.anteile == pytest.approx(5.26, abs=0.01)
    assert ergebnis.betrag_usd == pytest.approx(5.0, abs=0.02)
    assert DryRun.ausfuehrungspreis == 0.95
