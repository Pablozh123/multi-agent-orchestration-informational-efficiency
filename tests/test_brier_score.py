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


def _minimal_brier_connection_with_rcp():
    """Return an in-memory DB with Polymarket, FiveThirtyEight, and RCP rows."""
    import sqlite3

    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE polymarket_prices (
            price_timestamp TEXT, price REAL
        );
        CREATE TABLE poll_forecasts (
            date TEXT, source TEXT, candidate TEXT, probability REAL, poll_type TEXT
        );
        INSERT INTO polymarket_prices VALUES
            ('2024-04-01T00:00:00.000000Z', 0.55),
            ('2024-04-02T00:00:00.000000Z', 0.60);
        INSERT INTO poll_forecasts VALUES
            ('2024-04-01', 'fivethirtyeight', 'Trump', 0.52, 'model'),
            ('2024-04-02', 'fivethirtyeight', 'Trump', 0.54, 'model'),
            ('2024-04-01', 'rcp', 'Trump', 0.51, 'polling_signal'),
            ('2024-04-02', 'rcp', 'Trump', 0.53, 'polling_signal');
    """)
    return conn


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


def test_run_brier_analysis_excludes_rcp_by_default() -> None:
    """FiveThirtyEight works by default and RCP remains excluded."""
    from operations.analysis.brier_score import run_brier_analysis

    conn = _minimal_brier_connection_with_rcp()
    result = run_brier_analysis(conn)
    conn.close()

    assert "bs_fivethirtyeight" in result.columns
    assert "forecast_fivethirtyeight" in result.columns
    assert "bs_rcp" not in result.columns
    assert "forecast_rcp" not in result.columns


def test_run_brier_analysis_rcp_inclusion_fails_without_documentation() -> None:
    from operations.analysis.brier_score import run_brier_analysis

    conn = _minimal_brier_connection_with_rcp()
    with pytest.raises(ValueError, match="RCP inclusion requires"):
        run_brier_analysis(conn, include_rcp=True)
    conn.close()


def test_load_poll_forecasts_daily_rcp_requires_explicit_flags() -> None:
    from operations.analysis.brier_score import load_poll_forecasts_daily

    conn = _minimal_brier_connection_with_rcp()
    with pytest.raises(ValueError, match="RCP inclusion requires"):
        load_poll_forecasts_daily(conn, "rcp")

    result = load_poll_forecasts_daily(
        conn,
        "rcp",
        include_rcp=True,
        rcp_transformation_documented=True,
    )
    conn.close()

    assert list(result.columns) == ["date", "rcp"]


def test_run_brier_analysis_includes_rcp_only_with_explicit_flags() -> None:
    from operations.analysis.brier_score import run_brier_analysis

    conn = _minimal_brier_connection_with_rcp()
    result = run_brier_analysis(
        conn,
        include_rcp=True,
        rcp_transformation_documented=True,
    )
    conn.close()

    assert "bs_rcp" in result.columns
    assert "forecast_rcp" in result.columns


def test_run_brier_pipeline_writes_configured_output(tmp_path):
    """run_brier_pipeline schreibt genau den konfigurierten CSV-Pfad."""
    import sqlite3
    from operations.analysis.brier_score import BrierAnalysisConfig, run_brier_pipeline

    db_path = tmp_path / "test.db"
    output_path = tmp_path / "results" / "brier.csv"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE polymarket_prices (
            price_timestamp TEXT, price REAL
        );
        CREATE TABLE poll_forecasts (
            date TEXT, source TEXT, candidate TEXT, probability REAL, poll_type TEXT
        );
        INSERT INTO polymarket_prices VALUES
            ('2024-04-01T00:00:00.000000Z', 0.55),
            ('2024-04-02T00:00:00.000000Z', 0.60);
        INSERT INTO poll_forecasts VALUES
            ('2024-04-01', 'fivethirtyeight', 'Trump', 0.52, 'model'),
            ('2024-04-02', 'fivethirtyeight', 'Trump', 0.54, 'model');
    """)
    conn.close()

    df = run_brier_pipeline(
        BrierAnalysisConfig(db_path=db_path, output_path=output_path)
    )

    assert output_path.exists()
    written = pd.read_csv(output_path)
    assert len(df) == len(written) == 2
    assert "bs_polymarket" in written.columns


def test_validate_forecast_values_rejects_out_of_range():
    """Forecast-Werte muessen Wahrscheinlichkeiten in [0, 1] sein."""
    from operations.analysis.brier_score import validate_forecast_values

    df = pd.DataFrame({"forecast": [0.1, 1.2]})
    with pytest.raises(ValueError, match="outside"):
        validate_forecast_values(df, ["forecast"])


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


def test_run_diebold_mariano_excludes_rcp_by_default() -> None:
    from operations.analysis.calibrate import run_diebold_mariano

    df = pd.DataFrame({
        "date": pd.date_range("2024-03-01", periods=50).astype(str),
        "bs_polymarket": np.full(50, 0.10),
        "bs_fivethirtyeight": np.full(50, 0.12),
        "bs_rcp": np.full(50, 0.11),
        "bs_always_50": np.full(50, 0.25),
        "bs_prior_day": np.full(50, 0.13),
    })

    results = run_diebold_mariano(df)

    assert all("RCP" not in {result.source_1, result.source_2} for result in results)


def test_run_diebold_mariano_rcp_inclusion_fails_without_documentation() -> None:
    from operations.analysis.calibrate import run_diebold_mariano

    df = pd.DataFrame({
        "date": pd.date_range("2024-03-01", periods=50).astype(str),
        "bs_polymarket": np.full(50, 0.10),
        "bs_fivethirtyeight": np.full(50, 0.12),
        "bs_rcp": np.full(50, 0.11),
        "bs_always_50": np.full(50, 0.25),
        "bs_prior_day": np.full(50, 0.13),
    })

    with pytest.raises(ValueError, match="RCP inclusion requires"):
        run_diebold_mariano(df, include_rcp=True)


def test_run_diebold_mariano_includes_rcp_only_with_explicit_flags() -> None:
    from operations.analysis.calibrate import run_diebold_mariano

    df = pd.DataFrame({
        "date": pd.date_range("2024-03-01", periods=50).astype(str),
        "bs_polymarket": np.full(50, 0.10),
        "bs_fivethirtyeight": np.full(50, 0.12),
        "bs_rcp": np.full(50, 0.11),
        "bs_always_50": np.full(50, 0.25),
        "bs_prior_day": np.full(50, 0.13),
    })

    results = run_diebold_mariano(
        df,
        include_rcp=True,
        rcp_transformation_documented=True,
    )

    assert any("RCP" in {result.source_1, result.source_2} for result in results)


def test_reliability_diagram_rcp_inclusion_fails_without_documentation(tmp_path) -> None:
    from operations.analysis.calibrate import plot_reliability_diagram

    df = pd.DataFrame({
        "date": pd.date_range("2024-03-01", periods=10).astype(str),
        "forecast_polymarket": np.full(10, 0.60),
        "forecast_fivethirtyeight": np.full(10, 0.55),
        "forecast_rcp": np.full(10, 0.57),
        "forecast_always_50": np.full(10, 0.50),
        "forecast_prior_day": np.full(10, 0.58),
    })

    with pytest.raises(ValueError, match="RCP inclusion requires"):
        plot_reliability_diagram(df, tmp_path / "reliability.png", include_rcp=True)


def test_summary_brier_windows_exclude_rcp_by_default() -> None:
    import json
    import sqlite3

    from operations.analysis.generate_summaries import compute_brier_score_windows

    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE polymarket_prices (
            price_timestamp TEXT, market_id TEXT, token_id TEXT, price REAL
        );
        CREATE TABLE poll_forecasts (
            date TEXT, source TEXT, probability REAL
        );
        INSERT INTO polymarket_prices VALUES
            ('2024-04-01T00:00:00.000000Z', 'm1', 't1', 0.55),
            ('2024-04-02T00:00:00.000000Z', 'm1', 't1', 0.60);
        INSERT INTO poll_forecasts VALUES
            ('2024-04-01', 'fivethirtyeight', 0.52),
            ('2024-04-02', 'fivethirtyeight', 0.54),
            ('2024-04-01', 'rcp', 0.51),
            ('2024-04-02', 'rcp', 0.53);
    """)

    rows = compute_brier_score_windows(conn)
    conn.close()
    sources = {json.loads(row.value_json)["source"] for row in rows}

    assert sources == {"fivethirtyeight"}


def test_summary_brier_windows_rcp_inclusion_fails_without_documentation() -> None:
    import sqlite3

    from operations.analysis.generate_summaries import compute_brier_score_windows

    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE polymarket_prices (
            price_timestamp TEXT, market_id TEXT, token_id TEXT, price REAL
        );
        CREATE TABLE poll_forecasts (
            date TEXT, source TEXT, probability REAL
        );
        INSERT INTO polymarket_prices VALUES
            ('2024-04-01T00:00:00.000000Z', 'm1', 't1', 0.55);
        INSERT INTO poll_forecasts VALUES
            ('2024-04-01', 'fivethirtyeight', 0.52),
            ('2024-04-01', 'rcp', 0.51);
    """)

    with pytest.raises(ValueError, match="RCP inclusion requires"):
        compute_brier_score_windows(conn, include_rcp=True)
    conn.close()


def test_summary_brier_windows_include_rcp_only_with_explicit_flags() -> None:
    import json
    import sqlite3

    from operations.analysis.generate_summaries import compute_brier_score_windows

    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE polymarket_prices (
            price_timestamp TEXT, market_id TEXT, token_id TEXT, price REAL
        );
        CREATE TABLE poll_forecasts (
            date TEXT, source TEXT, probability REAL
        );
        INSERT INTO polymarket_prices VALUES
            ('2024-04-01T00:00:00.000000Z', 'm1', 't1', 0.55);
        INSERT INTO poll_forecasts VALUES
            ('2024-04-01', 'fivethirtyeight', 0.52),
            ('2024-04-01', 'rcp', 0.51);
    """)

    rows = compute_brier_score_windows(
        conn,
        include_rcp=True,
        rcp_transformation_documented=True,
    )
    conn.close()
    sources = {json.loads(row.value_json)["source"] for row in rows}

    assert sources == {"fivethirtyeight", "rcp"}
