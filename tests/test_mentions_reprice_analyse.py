"""Tests der Reprice-Analyse fuer Mentions-Maerkte."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from operations.analysis import mentions_reprice_analyse as mra

T0 = datetime(2026, 7, 23, 12, 0, 0, tzinfo=timezone.utc)


def _reihe(werte: list[tuple[float | None, float]],
           takt_s: float = 5.0) -> list[mra.Messpunkt]:
    """Baut eine Messreihe aus (ask, tiefe)-Paaren im festen Takt."""
    return [mra.Messpunkt(ts=T0 + timedelta(seconds=i * takt_s),
                          ask=ask, tiefe=tiefe)
            for i, (ask, tiefe) in enumerate(werte)]


# ------------------------------------------------------------- Ruhelage
def test_ruhelage_ist_median_der_ersten_punkte() -> None:
    reihe = _reihe([(0.40, 100), (0.42, 100), (0.41, 100), (0.99, 0)])
    assert mra.ruhelage(reihe, basis_n=3) == 0.41


def test_ruhelage_robust_gegen_ausreisser_am_anfang() -> None:
    """Ein einzelner Ausreisser darf die Ruhelage nicht verschieben."""
    reihe = _reihe([(0.40, 100), (0.95, 100), (0.41, 100)])
    assert mra.ruhelage(reihe, basis_n=3) == 0.41


def test_ruhelage_ohne_asks_ist_none() -> None:
    assert mra.ruhelage(_reihe([(None, 0), (None, 0)])) is None


# -------------------------------------------------------------- Ausbruch
def test_ausbruch_wird_erkannt() -> None:
    reihe = _reihe([(0.40, 200), (0.40, 200), (0.41, 200),
                    (0.75, 50), (0.90, 10), (0.97, 0)])
    assert mra.finde_ausbruch(reihe, basis=0.40) == 3


def test_einzelner_ausreisser_ist_kein_ausbruch() -> None:
    """Kernfall: In duennen Buechern erzeugen Einzeltrades Ausschlaege.

    Tesla 22.07.: ein Print ueber 1.2 Shares liess "Software" kurz auf
    0.50 fallen, die Minutenkerze zeigte einen Einbruch, der keiner war.
    Ein Punkt oberhalb der Schwelle, danach sofort zurueck in die
    Ruhelage, darf deshalb nicht als Ausbruch zaehlen.
    """
    reihe = _reihe([(0.40, 200), (0.40, 200), (0.85, 200),
                    (0.40, 200), (0.41, 200), (0.40, 200)])
    assert mra.finde_ausbruch(reihe, basis=0.40) is None


def test_ohne_bewegung_kein_ausbruch() -> None:
    reihe = _reihe([(0.40, 200)] * 6)
    assert mra.finde_ausbruch(reihe, basis=0.40) is None


def test_ausbruch_am_reihenende_wird_konservativ_verworfen() -> None:
    """Ohne Folgepunkte ist die Persistenz nicht pruefbar -> kein Ausbruch."""
    reihe = _reihe([(0.40, 200), (0.40, 200), (0.90, 0)])
    assert mra.finde_ausbruch(reihe, basis=0.40) is None


# ------------------------------------------------------------- Kennzahlen
def test_tiefe_wird_am_verzoegerungspunkt_abgelesen() -> None:
    # Takt 5s, Verzoegerung 10s -> zwei Punkte nach t0.
    reihe = _reihe([(0.40, 200), (0.75, 150), (0.90, 80), (0.97, 20)])
    tiefe_bei, max_tiefe, _ = mra.fenster_kennzahlen(
        reihe, i0=1, verzoegerung_s=10.0)
    assert tiefe_bei == 20
    assert max_tiefe == 150


def test_fensterdauer_endet_beim_unterschreiten() -> None:
    """Gemessen wird bis zur LETZTEN Beobachtung mit genug Tiefe.

    Takt 5s ab t0 (Index 1): bei t0+0 und t0+5 liegen 200 USD, bei t0+10
    nur noch 5. Die Dauer ist damit 5s — nicht 10s. Bewusst konservativ:
    zum Zeitpunkt t0+10 war die Tiefe nachweislich schon weg, ein
    laengeres Fenster zu behaupten waere nicht gedeckt.
    """
    reihe = _reihe([(0.40, 200), (0.60, 200), (0.70, 200), (0.95, 5)])
    _, _, dauer = mra.fenster_kennzahlen(
        reihe, i0=1, verzoegerung_s=10.0, mindest_usd=50.0)
    assert dauer == 5.0


# ------------------------------------------------------------ Markturteil
def test_vorgepreister_markt_wird_ausgesondert() -> None:
    reihe = _reihe([(0.97, 5), (0.98, 5), (0.99, 5), (0.99, 5)])
    b = mra.bewerte_markt("Software", 1, reihe)
    assert b.klasse == "vorgepreist"
    assert b.t0 is None


def test_fenster_wird_erkannt() -> None:
    reihe = _reihe([(0.40, 300), (0.40, 300), (0.41, 300),
                    (0.70, 300), (0.72, 280), (0.74, 260), (0.75, 240)])
    b = mra.bewerte_markt("Backlog", 1, reihe, verzoegerung_s=10.0)
    assert b.klasse == "FENSTER"
    assert b.tiefe_bei_verzoegerung == 260


def test_zu_schneller_markt_wird_erkannt() -> None:
    """Ausbruch ja, aber nach der Verzoegerung ist nichts mehr da."""
    reihe = _reihe([(0.40, 300), (0.40, 300), (0.41, 300),
                    (0.80, 20), (0.95, 5), (0.99, 0), (0.99, 0)])
    b = mra.bewerte_markt("Refinery", 1, reihe, verzoegerung_s=10.0)
    assert b.klasse == "zu_schnell"
    assert b.tiefe_bei_verzoegerung == 0


def test_markt_ohne_daten() -> None:
    b = mra.bewerte_markt("Leer", 1, _reihe([(None, 0), (None, 0)]))
    assert b.klasse == "keine_daten"


# ------------------------------------------------------------- Eventurteil
def test_urteil_kein_edge_wenn_alle_zu_schnell() -> None:
    schnell = [(0.40, 300), (0.40, 300), (0.41, 300),
               (0.80, 10), (0.95, 0), (0.99, 0), (0.99, 0)]
    ev = mra.bewerte_event({f"W{i}": _reihe(schnell) for i in range(4)})
    assert ev.urteil == "KEIN EDGE"


def test_urteil_edge_moeglich_ab_drei_fenstern() -> None:
    fenster = [(0.40, 300), (0.40, 300), (0.41, 300),
               (0.70, 300), (0.72, 280), (0.74, 260), (0.75, 240)]
    ev = mra.bewerte_event({f"W{i}": _reihe(fenster) for i in range(3)})
    assert ev.urteil == "EDGE MOEGLICH"


def test_urteil_grenzfall_bei_einem_fenster() -> None:
    fenster = [(0.40, 300), (0.40, 300), (0.41, 300),
               (0.70, 300), (0.72, 280), (0.74, 260), (0.75, 240)]
    schnell = [(0.40, 300), (0.40, 300), (0.41, 300),
               (0.80, 10), (0.95, 0), (0.99, 0), (0.99, 0)]
    ev = mra.bewerte_event({"A": _reihe(fenster), "B": _reihe(schnell)})
    assert ev.urteil == "GRENZFALL"


def test_urteil_nicht_messbar_ohne_ausbruch() -> None:
    ruhig = [(0.40, 300)] * 6
    ev = mra.bewerte_event({f"W{i}": _reihe(ruhig) for i in range(3)})
    assert ev.urteil == "NICHT MESSBAR"


# --------------------------------------------------------------- Einlesen
def test_protokoll_wird_gelesen_und_sortiert(tmp_path) -> None:
    pfad = tmp_path / "buch.jsonl"
    zeilen = [
        {"art": "start", "titel": "Testevent"},
        {"art": "buch", "wall_ts_utc": "2026-07-23T12:00:10.000Z",
         "wort": "Chip", "schwelle": 1, "best_ask": 0.55,
         "tiefe_usd_bis_90": 120.0},
        {"art": "buch", "wall_ts_utc": "2026-07-23T12:00:05.000Z",
         "wort": "Chip", "schwelle": 1, "best_ask": 0.50,
         "tiefe_usd_bis_90": 150.0},
        {"art": "buch_fehler", "wort": "Chip", "fehler": "Timeout"},
    ]
    pfad.write_text("\n".join(json.dumps(z) for z in zeilen), encoding="utf-8")
    reihen = mra.lade_protokoll(pfad)
    assert list(reihen) == ["Chip"]
    assert [m.ask for m in reihen["Chip"]] == [0.50, 0.55]  # zeitsortiert


def test_protokoll_ignoriert_kaputte_zeilen(tmp_path) -> None:
    pfad = tmp_path / "buch.jsonl"
    pfad.write_text(
        'kein json\n'
        '{"art": "buch", "wall_ts_utc": "2026-07-23T12:00:00.000Z", '
        '"wort": "Chip", "schwelle": 1, "best_ask": 0.5, '
        '"tiefe_usd_bis_90": 10.0}\n',
        encoding="utf-8")
    assert len(mra.lade_protokoll(pfad)["Chip"]) == 1
