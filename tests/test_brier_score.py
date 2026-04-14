"""Unit-Tests fuer operations/analysis/brier_score.py und calibrate.py.

Alle Tests gegen synthetische Daten mit bekannten Ergebnissen —
kein DB-Zugriff, kein HTTP. Deterministisch.

Anforderungsabdeckung:
    H1-01 — brier_score produziert taeglische BS-Zeitreihe ohne Lookahead
    H1-02 — calibrate produziert Reliability-Diagram-Daten
    H1-03 — Diebold-Mariano Test liefert p-Wert und Teststatistik
    H1-04 — Naive Baselines berechnet und vergleichbar
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# brier_score.py Tests
# ---------------------------------------------------------------------------


def test_brier_perfect_forecast():
    """Perfekte Prognose (outcome=1, forecast=1) ergibt BS=0."""
    from operations.analysis.brier_score import brier_score
    assert brier_score(1.0, 1.0) == pytest.approx(0.0)


def test_brier_worst_forecast():
    """Schlechteste Prognose (outcome=1, forecast=0) ergibt BS=1."""
    from operations.analysis.brier_score import brier_score
    assert brier_score(0.0, 1.0) == pytest.approx(1.0)


def test_brier_uninformative_forecast():
    """Uninformative Prognose (outcome=1, forecast=0.5) ergibt BS=0.25."""
    from operations.analysis.brier_score import brier_score
    assert brier_score(0.5, 1.0) == pytest.approx(0.25)


def test_brier_vectorized():
    """brier_score funktioniert elementweise auf Arrays."""
    from operations.analysis.brier_score import brier_score
    forecasts = np.array([0.0, 0.5, 1.0])
    expected = np.array([1.0, 0.25, 0.0])
    np.testing.assert_allclose(brier_score(forecasts, 1.0), expected)


def test_compute_daily_brier_series():
    """compute_daily_brier_series berechnet BS fuer jede Zeile einer pd.Series."""
    from operations.analysis.brier_score import compute_daily_brier_series
    forecasts = pd.Series([0.9, 0.8, 0.5, 0.2], name="forecast")
    outcome = 1.0
    result = compute_daily_brier_series(forecasts, outcome)
    assert len(result) == 4
    assert result.iloc[0] == pytest.approx(0.01)   # (0.9-1)^2
    assert result.iloc[2] == pytest.approx(0.25)   # (0.5-1)^2
    assert result.iloc[3] == pytest.approx(0.64)   # (0.2-1)^2


def test_naive_baselines_always_50():
    """Naive Baseline 'always_50' gibt ueberall 0.5 zurueck."""
    from operations.analysis.brier_score import compute_naive_baselines
    dates = pd.date_range("2024-03-01", periods=5, freq="D", tz="UTC")
    result = compute_naive_baselines(dates)
    assert (result["always_50"] == 0.5).all()
    assert len(result) == 5


def test_run_brier_analysis_structure(tmp_path):
    """run_brier_analysis gibt DataFrame mit erwarteten Spalten zurueck."""
    import sqlite3
    from operations.analysis.brier_score import run_brier_analysis

    # Minimale synthetische DB
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE polymarket_prices (
            price_timestamp TEXT, price REAL
        );
        CREATE TABLE poll_forecasts (
            date TEXT, source TEXT, candidate TEXT, probability REAL, poll_type TEXT
        );
    """)
    # Fuege synthetische Daten ein (3 gemeinsame Tage)
    for i, (ts, price) in enumerate([
        ("2024-04-01T00:00:00.000000Z", 0.55),
        ("2024-04-02T00:00:00.000000Z", 0.60),
        ("2024-04-03T00:00:00.000000Z", 0.58),
    ]):
        conn.execute(
            "INSERT INTO polymarket_prices VALUES (?, ?)", (ts, price)
        )
    for date, prob in [
        ("2024-04-01", 0.52),
        ("2024-04-02", 0.54),
        ("2024-04-03", 0.53),
    ]:
        conn.execute(
            "INSERT INTO poll_forecasts VALUES (?, ?, ?, ?, ?)",
            (date, "fivethirtyeight", "Trump", prob, "national"),
        )
    conn.commit()

    result = run_brier_analysis(conn)
    conn.close()

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    required_cols = {"date", "bs_polymarket", "bs_fivethirtyeight", "bs_always_50"}
    assert required_cols.issubset(set(result.columns)), (
        f"Fehlende Spalten: {required_cols - set(result.columns)}"
    )
    # Alle BS-Werte in [0, 1]
    for col in ["bs_polymarket", "bs_fivethirtyeight", "bs_always_50"]:
        assert (result[col] >= 0).all() and (result[col] <= 1).all(), (
            f"{col} hat Werte ausserhalb [0, 1]"
        )


def test_no_lookahead_bias_in_brier(tmp_path):
    """Lookahead-Assertion: kein price_timestamp nach Election Day."""
    import sqlite3
    from operations.analysis.brier_score import load_polymarket_daily

    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE polymarket_prices (price_timestamp TEXT, price REAL)"
    )
    # Alle Timestamps vor Election Day (2024-11-05) — kein Fehler erwartet
    for ts in ["2024-01-01T00:00:00.000000Z", "2024-11-04T23:59:59.000000Z"]:
        conn.execute("INSERT INTO polymarket_prices VALUES (?, 0.6)", (ts,))
    conn.commit()
    df = load_polymarket_daily(conn)  # darf keinen AssertionError werfen
    assert len(df) == 2
    conn.close()


# ---------------------------------------------------------------------------
# calibrate.py Tests
# ---------------------------------------------------------------------------


def test_calibration_curve_perfect():
    """Perfekt kalibrierter Forecaster: frac_pos == mean_forecast."""
    from operations.analysis.calibrate import compute_calibration_curve
    # Forecasts gleichmaessig ueber [0,1] verteilt
    rng = np.random.default_rng(42)
    forecasts = rng.uniform(0, 1, 1000)
    # Outcomes: 1 mit Wahrscheinlichkeit = forecast (perfekte Kalibrierung)
    outcomes = (rng.uniform(0, 1, 1000) < forecasts).astype(float)

    _, mean_fc, frac_pos = compute_calibration_curve(forecasts, outcomes, n_bins=10)

    # Bei 1000 Samples: mean_fc und frac_pos sollten nah beieinander liegen
    # (grosszuegige Toleranz wegen Stochastik)
    np.testing.assert_allclose(mean_fc, frac_pos, atol=0.12)


def test_calibration_curve_returns_arrays():
    """compute_calibration_curve gibt drei gleich lange Arrays zurueck."""
    from operations.analysis.calibrate import compute_calibration_curve
    forecasts = np.array([0.2, 0.4, 0.6, 0.8])
    outcomes = np.array([0.0, 1.0, 1.0, 1.0])
    centers, mean_fc, frac_pos = compute_calibration_curve(forecasts, outcomes, n_bins=5)
    assert len(centers) == len(mean_fc) == len(frac_pos)
    assert all(0 <= c <= 1 for c in centers)
    assert all(0 <= f <= 1 for f in frac_pos)


def test_diebold_mariano_identical_series():
    """DM-Test bei identischen Serien: Statistik ~0, p-Wert ~1."""
    from operations.analysis.calibrate import diebold_mariano_test
    errors = np.random.default_rng(0).uniform(0, 1, 100)
    stat, pval = diebold_mariano_test(errors, errors)
    # Identische Serien — kein Unterschied detektierbar
    assert abs(stat) < 1e-10
    assert pval > 0.99


def test_diebold_mariano_clear_difference():
    """DM-Test bei klar unterschiedlichen Serien liefert signifikanten p-Wert."""
    from operations.analysis.calibrate import diebold_mariano_test
    rng = np.random.default_rng(1)
    # Quelle 1: hohe Brier Scores (schlechter Forecaster)
    errors_bad = rng.uniform(0.3, 0.8, 200)
    # Quelle 2: niedrige Brier Scores (guter Forecaster)
    errors_good = rng.uniform(0.0, 0.1, 200)
    stat, pval = diebold_mariano_test(errors_bad, errors_good)
    assert pval < 0.05, f"Erwartete Signifikanz, aber p={pval:.4f}"
    assert stat > 0, "Quelle 1 (schlechter) sollte positive DM-Statistik haben"


def test_run_diebold_mariano_returns_results():
    """run_diebold_mariano gibt fuer alle Paarungen DMResult-Objekte zurueck."""
    from operations.analysis.calibrate import run_diebold_mariano
    # Minimaler DataFrame wie von brier_score.run_brier_analysis() produziert
    df = pd.DataFrame({
        "date": pd.date_range("2024-03-01", periods=50).astype(str),
        "bs_polymarket": np.random.default_rng(2).uniform(0, 0.5, 50),
        "bs_fivethirtyeight": np.random.default_rng(3).uniform(0, 0.5, 50),
        "bs_always_50": np.full(50, 0.25),
        "bs_prior_day": np.random.default_rng(4).uniform(0, 0.5, 50),
    })
    results = run_diebold_mariano(df)
    assert len(results) >= 3
    for r in results:
        assert 0.0 <= r.p_value <= 1.0, f"p_value ausserhalb [0,1]: {r.p_value}"
        assert isinstance(r.interpretation, str) and len(r.interpretation) > 0
