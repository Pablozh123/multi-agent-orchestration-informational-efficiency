"""Tests fuer die Mentions-Latenz-Kennzahlen (operations/analysis/mentions_latency.py)."""

from __future__ import annotations

import csv

import pytest

from operations.analysis import mentions_latency as ml

DROP = 1_000_000_000  # beliebiger Epoch-Anker


def punkte_aus(*paare: tuple[int, float]) -> list[tuple[int, float]]:
    return sorted((int(t), float(p)) for t, p in paare)


# ------------------------------------------------------------ Baseline


def test_baseline_median_nimmt_nur_fenster_vor_drop() -> None:
    punkte = punkte_aus(
        (DROP - 4000, 0.90),  # vor dem Fenster
        (DROP - 3600, 0.10),  # Fenstergrenze inklusiv
        (DROP - 1800, 0.20),
        (DROP - 60, 0.30),
        (DROP, 0.80),  # Drop selbst zaehlt nicht zur Baseline
    )
    assert ml.baseline_median(punkte, DROP) == pytest.approx(0.20)


def test_baseline_median_ohne_punkte_ist_none() -> None:
    punkte = punkte_aus((DROP + 60, 0.5))
    assert ml.baseline_median(punkte, DROP) is None


# ------------------------------------------------------------ Erste Reaktion


def test_erste_reaktion_braucht_mehr_als_einen_prozentpunkt() -> None:
    punkte = punkte_aus(
        (DROP + 60, 0.51),   # genau 1 Prozentpunkt: zaehlt nicht
        (DROP + 120, 0.512),  # > 1 Prozentpunkt: erste Reaktion
    )
    assert ml.erste_reaktion_epoch(punkte, DROP, baseline=0.50) == DROP + 120


def test_erste_reaktion_ignoriert_punkte_vor_drop() -> None:
    punkte = punkte_aus((DROP - 60, 0.99), (DROP + 300, 0.55))
    assert ml.erste_reaktion_epoch(punkte, DROP, baseline=0.50) == DROP + 300


def test_erste_reaktion_none_ohne_ueberschreitung() -> None:
    punkte = punkte_aus((DROP + 60, 0.505), (DROP + 120, 0.495))
    assert ml.erste_reaktion_epoch(punkte, DROP, baseline=0.50) is None


# ------------------------------------------------------------ Konvergenz


def test_konvergenz_yes_beginnt_nach_letztem_ruecksetzer() -> None:
    punkte = punkte_aus(
        (DROP + 60, 0.95),   # erster Ausflug ueber 0.9 ...
        (DROP + 120, 0.85),  # ... haelt nicht
        (DROP + 180, 0.92),  # ab hier dauerhaft >= 0.9
        (DROP + 240, 0.97),
    )
    assert ml.konvergenz_epoch(punkte, outcome_yes=True) == DROP + 180


def test_konvergenz_no_seite() -> None:
    punkte = punkte_aus((DROP + 60, 0.40), (DROP + 120, 0.08), (DROP + 180, 0.02))
    assert ml.konvergenz_epoch(punkte, outcome_yes=False) == DROP + 120


def test_konvergenz_none_wenn_letzter_punkt_falsche_seite() -> None:
    punkte = punkte_aus((DROP + 60, 0.95), (DROP + 120, 0.50))
    assert ml.konvergenz_epoch(punkte, outcome_yes=True) is None


def test_konvergenz_leere_reihe_ist_none() -> None:
    assert ml.konvergenz_epoch([], outcome_yes=True) is None


def test_konvergenz_kann_vor_drop_liegen() -> None:
    punkte = punkte_aus((DROP - 600, 0.95), (DROP + 60, 0.96))
    assert ml.konvergenz_epoch(punkte, outcome_yes=True) == DROP - 600


# ------------------------------------------------------------ Handelbares Fenster


def test_stunden_im_band_summiert_nur_bandpunkte_nach_drop() -> None:
    punkte = punkte_aus(
        (DROP - 3600, 0.50),   # vor Drop: zaehlt nicht
        (DROP, 0.50),          # im Band, 1 h bis zum naechsten Punkt
        (DROP + 3600, 0.95),   # ausserhalb, 1 h zaehlt nicht
        (DROP + 7200, 0.50),   # im Band, 0.5 h
        (DROP + 9000, 0.05),   # ausserhalb, letzter Punkt
    )
    assert ml.stunden_im_band(punkte, DROP) == pytest.approx(1.5)


def test_stunden_im_band_grenzwerte_zaehlen_nicht() -> None:
    punkte = punkte_aus(
        (DROP, 0.10),          # exakt untere Grenze: nicht im Band
        (DROP + 3600, 0.90),   # exakt obere Grenze: nicht im Band
        (DROP + 7200, 0.50),
    )
    assert ml.stunden_im_band(punkte, DROP) == pytest.approx(0.0)


def test_stunden_im_band_leer_oder_einzelpunkt() -> None:
    assert ml.stunden_im_band([], DROP) == pytest.approx(0.0)
    assert ml.stunden_im_band([(DROP, 0.5)], DROP) == pytest.approx(0.0)


# ------------------------------------------------------------ Bewertung


def test_bewerte_markt_ok_und_minuten() -> None:
    punkte = punkte_aus(
        (DROP - 1800, 0.30),
        (DROP - 900, 0.30),
        (DROP + 300, 0.35),   # erste Reaktion: 5 Minuten
        (DROP + 1200, 0.95),  # Konvergenz: 20 Minuten
        (DROP + 1800, 0.99),
    )
    r = ml.bewerte_markt(punkte, DROP, outcome_yes=True)
    assert r["status"] == "ok"
    assert r["baseline_preis"] == pytest.approx(0.30)
    assert r["minuten_bis_erste_reaktion"] == pytest.approx(5.0)
    assert r["minuten_bis_konvergenz"] == pytest.approx(20.0)
    assert r["n_punkte_baseline"] == 2
    # Bandzeit: 0.35 bei DROP+300 (15 Min. bis DROP+1200); 0.95/0.99 ausserhalb
    assert r["stunden_im_handelbaren_fenster"] == pytest.approx(0.25)


def test_bewerte_markt_status_keine_baseline() -> None:
    punkte = punkte_aus((DROP + 60, 0.95), (DROP + 120, 0.96))
    r = ml.bewerte_markt(punkte, DROP, outcome_yes=True)
    assert "keine_baseline" in r["status"]
    assert r["minuten_bis_erste_reaktion"] is None
    # Konvergenz ist unabhaengig von der Baseline weiter messbar
    assert r["minuten_bis_konvergenz"] == pytest.approx(1.0)


def test_bewerte_markt_status_keine_konvergenz() -> None:
    punkte = punkte_aus((DROP - 900, 0.50), (DROP + 60, 0.60), (DROP + 120, 0.55))
    r = ml.bewerte_markt(punkte, DROP, outcome_yes=True)
    assert "keine_konvergenz_im_fenster" in r["status"]
    assert r["minuten_bis_konvergenz"] is None


def test_bewerte_markt_deterministisch() -> None:
    punkte = punkte_aus((DROP - 900, 0.3), (DROP + 300, 0.5), (DROP + 600, 0.95))
    assert ml.bewerte_markt(punkte, DROP, True) == ml.bewerte_markt(punkte, DROP, True)


# ------------------------------------------------------------ Seed


def schreibe_seed(pfad, zeilen: list[dict]) -> None:
    felder = list(zeilen[0].keys())
    with open(pfad, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=felder)
        w.writeheader()
        w.writerows(zeilen)


SEED_ZEILE = {
    "event": "test_event",
    "drop_ts_utc": "2026-01-16T17:00:00Z",
    "condition_id": "0xabc",
    "clob_token_id": "123",
    "korrekt_aufgeloestes_outcome": "no",
}


def test_lese_seed_normalisiert_outcome(tmp_path) -> None:
    pfad = tmp_path / "seed.csv"
    schreibe_seed(pfad, [SEED_ZEILE])
    zeilen = ml.lese_seed(pfad)
    assert zeilen[0]["korrekt_aufgeloestes_outcome"] == "NO"


def test_lese_seed_fehlende_datei() -> None:
    with pytest.raises(FileNotFoundError):
        ml.lese_seed(ml.SEED_PATH.parent / "gibt_es_nicht.csv")


def test_lese_seed_fehlende_pflichtspalte(tmp_path) -> None:
    pfad = tmp_path / "seed.csv"
    zeile = {k: v for k, v in SEED_ZEILE.items() if k != "clob_token_id"}
    schreibe_seed(pfad, [zeile])
    with pytest.raises(ValueError, match="Pflichtspalten"):
        ml.lese_seed(pfad)


def test_lese_seed_ungueltiges_outcome(tmp_path) -> None:
    pfad = tmp_path / "seed.csv"
    schreibe_seed(pfad, [{**SEED_ZEILE, "korrekt_aufgeloestes_outcome": "MAYBE"}])
    with pytest.raises(ValueError, match="Outcome"):
        ml.lese_seed(pfad)


def test_parse_ts_utc() -> None:
    assert ml.parse_ts_utc("1970-01-01T00:00:00Z") == 0
    assert ml.parse_ts_utc("1970-01-01T01:00:00+01:00") == 0
    with pytest.raises(ValueError):
        ml.parse_ts_utc("1970-01-01T00:00:00")


def test_berechne_ergebnisse_ausschluss_ohne_fetch() -> None:
    """Zeilen mit gesetzter Spalte ausschluss brauchen keinen Datenabruf
    und liefern nur eine Statuszeile ohne Kennzahlen."""
    seed = [{**SEED_ZEILE, "ausschluss": "zuordnungsambiguitaet"}]
    ergebnisse = ml.berechne_ergebnisse(seed, fetch=None)
    r = ergebnisse[0]
    assert r["status"] == "ausgeschlossen_zuordnungsambiguitaet"
    assert r["minuten_bis_erste_reaktion"] is None
    assert r["minuten_bis_konvergenz"] is None
    assert r["stunden_im_handelbaren_fenster"] is None
    assert r["event"] == "test_event"


# ------------------------------------------------------------ Pipeline mit Fake-Fetch


def test_berechne_ergebnisse_mit_fake_fetch(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(ml, "RAW_DIR", tmp_path / "raw")
    drop = ml.parse_ts_utc("2026-01-16T17:00:00Z")

    def fake_fetch(token_id: str, start: int, ende: int) -> dict:
        return {
            "history": [
                {"t": drop - 1200, "p": 0.30},
                {"t": drop + 120, "p": 0.45},  # Reaktion nach 2 Minuten
                {"t": drop + 600, "p": 0.05},  # Konvergenz (NO) nach 10 Minuten
                {"t": drop + 900, "p": 0.02},
            ]
        }

    seed = [dict(SEED_ZEILE)]
    ergebnisse = ml.berechne_ergebnisse(seed, fetch=fake_fetch)
    r = ergebnisse[0]
    assert r["minuten_bis_erste_reaktion"] == pytest.approx(2.0)
    assert r["minuten_bis_konvergenz"] == pytest.approx(10.0)
    assert r["status"] == "ok"
    # Cache wurde geschrieben und zweiter Lauf liest ihn (fetch darf fehlen)
    assert (tmp_path / "raw" / "prices_test_event.json").exists()
    nochmal = ml.berechne_ergebnisse(seed, fetch=None)
    assert nochmal == ergebnisse
