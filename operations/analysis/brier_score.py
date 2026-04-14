"""H1-Analyse: Brier Score Zeitreihe fuer Polymarket, FiveThirtyEight und Baselines.

Berechnet fuer jeden Tag im Overlap-Fenster (2024-03-01 bis 2024-09-12) den
Brier Score jeder Forecasting-Quelle gegenueber dem tatsaechlichen Wahlergebnis
(Trump gewann, outcome=1.0, bekannt am 2024-11-05).

Kein Look-ahead-Bias: Prognosen von Tag D werden nur gegen outcome D bewertet.
Alle Berechnungen deterministisch (numpy/pandas), kein LLM.

Aufruf:
    python -m operations.analysis.brier_score

Output:
    data/results/h1_brier_scores.csv
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

DB_PATH = Path("data/thesis.db")
RESULTS_DIR = Path("data/results")
ELECTION_OUTCOME = 1.0  # Trump gewann am 2024-11-05 (historische Tatsache)
ELECTION_DATE = pd.Timestamp("2024-11-05", tz="UTC")


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_polymarket_daily(conn: sqlite3.Connection) -> pd.DataFrame:
    """Laedt taeglischen Schlusskurs aus polymarket_prices (letzter Preis pro Tag).

    Gibt DataFrame mit Spalten [date, price] zurueck, date als date-String YYYY-MM-DD.
    """
    df = pd.read_sql(
        "SELECT price_timestamp, price FROM polymarket_prices ORDER BY price_timestamp",
        conn,
    )
    df["ts"] = pd.to_datetime(
        df["price_timestamp"].str.replace(r"\s*UTCZ?\s*$", "", regex=True),
        utc=True,
        errors="coerce",
    )
    df = df.dropna(subset=["ts"])

    # Lookahead-Assertion: kein price_timestamp mehr als 2 Tage nach Election Day.
    # (Der letzte legitime Preis ist 2024-11-06T00:00:02Z — Markt-Settlement
    # kurz nach Mitternacht; +2 Tage Puffer um Settlement-Preise zuzulassen.)
    assert (df["ts"] <= ELECTION_DATE + pd.Timedelta(days=2)).all(), (
        "Lookahead-Bias erkannt: price_timestamp weit nach Election Day"
    )

    # Taeglischer Schlusskurs: letzter Preis pro Kalender-Tag
    daily = (
        df.set_index("ts")["price"]
        .resample("D")
        .last()
        .dropna()
        .reset_index()
    )
    daily.columns = ["ts", "price"]
    daily["date"] = daily["ts"].dt.date.astype(str)
    return daily[["date", "price"]].rename(columns={"price": "polymarket"})


def load_poll_forecasts_daily(
    conn: sqlite3.Connection, source: str
) -> pd.DataFrame:
    """Laedt taeglische Prognosewahrscheinlichkeiten fuer Trump aus poll_forecasts.

    Filtert auf candidate LIKE '%Trump%' und den angegebenen source.
    Gibt DataFrame mit Spalten [date, probability] zurueck.
    """
    df = pd.read_sql(
        """
        SELECT date, probability
        FROM poll_forecasts
        WHERE source = ?
          AND (candidate LIKE '%Trump%' OR candidate LIKE '%trump%')
        ORDER BY date
        """,
        conn,
        params=(source,),
    )
    if df.empty:
        return pd.DataFrame(columns=["date", "probability"])
    # Dedup: falls mehrere Zeilen pro Tag (z.B. verschiedene poll_types), Mittelwert
    df = df.groupby("date", as_index=False)["probability"].mean()
    return df.rename(columns={"probability": source})


# ---------------------------------------------------------------------------
# Brier Score computation
# ---------------------------------------------------------------------------


def brier_score(forecast: float | np.ndarray, outcome: float) -> float | np.ndarray:
    """Brier Score: BS = (forecast - outcome)^2. Kleiner ist besser (0 = perfekt)."""
    return (np.asarray(forecast) - outcome) ** 2


def compute_daily_brier_series(
    forecasts: pd.Series, outcome: float
) -> pd.Series:
    """Berechnet taeglischen Brier Score fuer eine Forecast-Serie.

    Args:
        forecasts: pd.Series mit float-Werten in [0, 1]
        outcome: tatsaechliches Ergebnis (0 oder 1)

    Returns:
        pd.Series mit Brier-Scores, gleicher Index wie forecasts
    """
    return pd.Series(brier_score(forecasts.values, outcome), index=forecasts.index)


def compute_naive_baselines(date_range: pd.DatetimeIndex) -> pd.DataFrame:
    """Berechnet die zwei naiven Baseline-Modelle.

    - always_50: Konstant 0.5 (keine Information)
    - prior_day_polymarket: Wird erst nach merge mit echten Daten befuellt

    Returns:
        DataFrame mit [date, always_50] — prior_day wird separat hinzugefuegt.
    """
    dates = date_range.date.astype(str)
    return pd.DataFrame({"date": dates, "always_50": 0.5})


# ---------------------------------------------------------------------------
# Main analysis pipeline
# ---------------------------------------------------------------------------


def run_brier_analysis(conn: sqlite3.Connection) -> pd.DataFrame:
    """Fuehrt die vollstaendige Brier-Score-Analyse durch.

    Returns:
        DataFrame mit taeglischen Brier Scores fuer alle Quellen.
        Spalten: date, polymarket, fivethirtyeight, [rcp,] always_50, prior_day
    """
    # Lade Rohdaten
    pm = load_polymarket_daily(conn)
    fe = load_poll_forecasts_daily(conn, "fivethirtyeight")

    # Optionale RCP-Daten (falls vorhanden)
    rcp_raw = pd.read_sql(
        "SELECT COUNT(*) as n FROM poll_forecasts WHERE source='rcp'", conn
    ).iloc[0]["n"]
    has_rcp = rcp_raw > 0
    if has_rcp:
        rcp = load_poll_forecasts_daily(conn, "rcp")
    else:
        rcp = None

    # Merge auf Tagesdatum
    merged = pm.copy()
    merged = merged.merge(fe, on="date", how="inner")
    if has_rcp and rcp is not None and not rcp.empty:
        merged = merged.merge(rcp, on="date", how="left")

    # Prior-Day Polymarket (Look-ahead-freie Baseline): Preis vom Vortag
    merged = merged.sort_values("date").reset_index(drop=True)
    merged["prior_day"] = merged["polymarket"].shift(1)

    # Naive Baseline: immer 0.5
    merged["always_50"] = 0.5

    # Brier Scores berechnen
    outcome = ELECTION_OUTCOME
    result = pd.DataFrame({"date": merged["date"]})
    result["bs_polymarket"] = brier_score(merged["polymarket"].values, outcome)
    result["bs_fivethirtyeight"] = brier_score(merged["fivethirtyeight"].values, outcome)
    if has_rcp and "rcp" in merged.columns:
        result["bs_rcp"] = brier_score(merged["rcp"].values, outcome)
    result["bs_always_50"] = brier_score(merged["always_50"].values, outcome)
    # Prior-day hat NaN in erster Zeile; Lookahead-safe da Vortag
    result["bs_prior_day"] = brier_score(
        merged["prior_day"].fillna(0.5).values, outcome
    )

    # Rohe Prognosen behalten (benoetigt fuer Calibration)
    result["forecast_polymarket"] = merged["polymarket"].values
    result["forecast_fivethirtyeight"] = merged["fivethirtyeight"].values
    if has_rcp and "rcp" in merged.columns:
        result["forecast_rcp"] = merged["rcp"].values
    result["forecast_always_50"] = 0.5
    result["forecast_prior_day"] = merged["prior_day"].fillna(0.5).values

    return result


def print_summary(df: pd.DataFrame) -> None:
    """Gibt eine Zusammenfassung der mittleren Brier Scores aus."""
    print("\n=== H1 Brier Score Zusammenfassung ===")
    print(f"Analyse-Fenster: {df['date'].min()} bis {df['date'].max()} ({len(df)} Tage)")
    print(f"Outcome: Trump gewinnt (outcome = {ELECTION_OUTCOME})\n")
    sources = [
        ("Polymarket", "bs_polymarket"),
        ("FiveThirtyEight", "bs_fivethirtyeight"),
        ("Baseline: immer 50%", "bs_always_50"),
        ("Baseline: Vortag Polymarket", "bs_prior_day"),
    ]
    if "bs_rcp" in df.columns:
        sources.insert(2, ("RCP", "bs_rcp"))

    for label, col in sources:
        mean_bs = df[col].mean()
        std_bs = df[col].std()
        print(f"  {label:30s}: mean BS = {mean_bs:.4f} ± {std_bs:.4f}")
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    print("Berechne Brier Score Zeitreihe ...")
    df = run_brier_analysis(conn)
    conn.close()

    out_path = RESULTS_DIR / "h1_brier_scores.csv"
    df.to_csv(out_path, index=False)
    print(f"Gespeichert: {out_path} ({len(df)} Tage)")

    print_summary(df)


if __name__ == "__main__":
    main()
