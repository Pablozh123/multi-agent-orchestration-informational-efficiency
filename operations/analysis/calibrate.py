"""H1-Analyse: Kalibrierungskurven und Diebold-Mariano Test.

Laedt die Brier-Score-Zeitreihe aus h1_brier_scores.csv (erzeugt von brier_score.py)
und berechnet:
  1. Reliability Diagram (Calibration Curve) fuer Polymarket und FiveThirtyEight
  2. Diebold-Mariano Test: statistisch signifikanter Unterschied zwischen den BS-Serien?

Kein Look-ahead-Bias: nutzt ausschliesslich Forecasts aus brier_score.py.
Deterministisch (statsmodels, scipy, matplotlib), kein LLM.

Aufruf:
    python -m operations.analysis.calibrate

Voraussetzung:
    python -m operations.analysis.brier_score  (erzeugt h1_brier_scores.csv)

Output:
    data/results/h1_reliability_curve.png
    data/results/h1_diebold_mariano.json
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple

import matplotlib
matplotlib.use("Agg")  # non-interactive backend fuer Windows

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm

RESULTS_DIR = Path("data/results")
BRIER_CSV = RESULTS_DIR / "h1_brier_scores.csv"
ELECTION_OUTCOME = 1.0

# Matplotlib OO API, LaTeX-kompatible Fonts (CLAUDE.md Anforderung Phase 05)
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "figure.dpi": 300,
})


# ---------------------------------------------------------------------------
# Calibration / Reliability Diagram
# ---------------------------------------------------------------------------


def compute_calibration_curve(
    forecasts: np.ndarray,
    outcomes: np.ndarray,
    n_bins: int = 10,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Berechnet Kalibrierungskurve (Reliability Diagram).

    Args:
        forecasts: Prognosewerte in [0, 1]
        outcomes: tatsaechliche Ergebnisse (0 oder 1)
        n_bins: Anzahl gleichmaessiger Bins

    Returns:
        (bin_centers, mean_forecast_per_bin, fraction_positive_per_bin)
        Leer-Bins werden ausgeschlossen.
    """
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_indices = np.digitize(forecasts, bins) - 1
    bin_indices = np.clip(bin_indices, 0, n_bins - 1)

    centers, mean_forecast, frac_pos = [], [], []
    for i in range(n_bins):
        mask = bin_indices == i
        if mask.sum() == 0:
            continue
        centers.append(bins[i] + (bins[i + 1] - bins[i]) / 2)
        mean_forecast.append(forecasts[mask].mean())
        frac_pos.append(outcomes[mask].mean())

    return np.array(centers), np.array(mean_forecast), np.array(frac_pos)


def plot_reliability_diagram(
    df: pd.DataFrame,
    out_path: Path,
) -> None:
    """Erstellt Reliability Diagram fuer alle Forecasting-Quellen.

    Perfekte Kalibrierung = diagonale Linie (y=x).
    Kurve unterhalb Diagonal: zu optimistisch (ueberconfident).
    Kurve oberhalb Diagonal: zu pessimistisch (underconfident).
    """
    # Alle verfuegbaren Quellen bestimmen
    sources = [
        ("Polymarket", "forecast_polymarket", "#2563eb"),
        ("FiveThirtyEight", "forecast_fivethirtyeight", "#dc2626"),
        ("Baseline: immer 50%", "forecast_always_50", "#9ca3af"),
        ("Baseline: Vortag", "forecast_prior_day", "#f59e0b"),
    ]
    if "forecast_rcp" in df.columns:
        sources.insert(2, ("RCP", "forecast_rcp", "#16a34a"))

    # Outcome-Array (Trump gewann -> outcome fuer jede Zeile = 1.0)
    outcomes = np.ones(len(df)) * ELECTION_OUTCOME

    fig, ax = plt.subplots(figsize=(7, 6))

    # Perfekte Kalibrierung
    ax.plot([0, 1], [0, 1], "k--", lw=1.2, label="Perfekte Kalibrierung", zorder=1)

    for label, col, color in sources:
        if col not in df.columns:
            continue
        forecasts = df[col].values
        _, mean_fc, frac_pos = compute_calibration_curve(forecasts, outcomes)
        ax.plot(mean_fc, frac_pos, "o-", color=color, lw=1.8, ms=5,
                label=label, zorder=2)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Mittlerer Prognosewert (pro Bin)")
    ax.set_ylabel("Beobachtete Haeufigkeit (Fraction positive)")
    ax.set_title(
        "Reliability Diagram — US-Praesidentschaftswahl 2024\n"
        f"(Overlap-Fenster: {df['date'].min()} bis {df['date'].max()})"
    )
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Reliability Diagram gespeichert: {out_path}")


# ---------------------------------------------------------------------------
# Diebold-Mariano Test
# ---------------------------------------------------------------------------


class DMResult(NamedTuple):
    """Ergebnis des Diebold-Mariano Tests."""
    source_1: str
    source_2: str
    dm_statistic: float
    p_value: float
    n_obs: int
    interpretation: str


def diebold_mariano_test(
    errors_1: np.ndarray,
    errors_2: np.ndarray,
    h: int = 1,
) -> tuple[float, float]:
    """Diebold-Mariano Test auf Basis quadratischer Verluste (Brier Score).

    Testet H0: Kein Unterschied in der Prognosegenauigkeit.
    Implementierung nach Harvey, Leybourne & Newbold (1997), HLN-Korrektur.

    Args:
        errors_1: Brier Scores fuer Quelle 1 (array der Laenge T)
        errors_2: Brier Scores fuer Quelle 2 (array der Laenge T)
        h: Forecast-Horizont (1 fuer taeglich)

    Returns:
        (dm_statistic, p_value) — zweiseitiger Test
    """
    d = errors_1 - errors_2  # Verlustdifferenzen
    T = len(d)
    d_bar = d.mean()

    # Varianzschaetzer mit Bartlett-Kern fuer bis zu h-1 Autokovarianzen
    gamma_0 = np.var(d, ddof=1)
    gamma_sum = 0.0
    for lag in range(1, h):
        cov = np.cov(d[lag:], d[:-lag], ddof=1)[0, 1]
        gamma_sum += (1 - lag / h) * cov
    v_d = (gamma_0 + 2 * gamma_sum) / T

    if v_d <= 0:
        return 0.0, 1.0  # Degenerate case

    dm_stat = d_bar / np.sqrt(v_d)

    # HLN-Korrektur fuer kleine Stichproben
    hln_correction = np.sqrt((T + 1 - 2 * h + h * (h - 1) / T) / T)
    dm_stat_hln = dm_stat * hln_correction

    # Zweiseitiger p-Wert (Student-t Approximation mit T-1 Freiheitsgraden)
    from scipy.stats import t as t_dist
    p_value = 2 * t_dist.sf(abs(dm_stat_hln), df=T - 1)

    return float(dm_stat_hln), float(p_value)


def run_diebold_mariano(df: pd.DataFrame) -> list[DMResult]:
    """Fuehrt DM-Test fuer alle sinnvollen Paarungen durch.

    Vergleicht: Polymarket vs FiveThirtyEight, Polymarket vs Baselines.
    """
    comparisons = [
        ("Polymarket", "bs_polymarket", "FiveThirtyEight", "bs_fivethirtyeight"),
        ("Polymarket", "bs_polymarket", "immer_50%", "bs_always_50"),
        ("Polymarket", "bs_polymarket", "Vortag_Polymarket", "bs_prior_day"),
        ("FiveThirtyEight", "bs_fivethirtyeight", "immer_50%", "bs_always_50"),
    ]
    if "bs_rcp" in df.columns:
        comparisons.insert(1, ("Polymarket", "bs_polymarket", "RCP", "bs_rcp"))
        comparisons.insert(2, ("FiveThirtyEight", "bs_fivethirtyeight", "RCP", "bs_rcp"))

    results = []
    for s1, col1, s2, col2 in comparisons:
        if col1 not in df.columns or col2 not in df.columns:
            continue
        # Nur vollstaendige Zeilen (Prior-Day hat NaN in Zeile 0)
        mask = df[col1].notna() & df[col2].notna()
        e1 = df.loc[mask, col1].values
        e2 = df.loc[mask, col2].values
        stat, pval = diebold_mariano_test(e1, e2)

        if pval < 0.01:
            interp = f"{s1} und {s2} unterscheiden sich hochsignifikant (p<0.01)"
        elif pval < 0.05:
            interp = f"{s1} und {s2} unterscheiden sich signifikant (p<0.05)"
        elif pval < 0.10:
            interp = f"Schwacher Hinweis auf Unterschied zwischen {s1} und {s2} (p<0.10)"
        else:
            interp = f"Kein signifikanter Unterschied zwischen {s1} und {s2}"

        results.append(DMResult(
            source_1=s1,
            source_2=s2,
            dm_statistic=stat,
            p_value=pval,
            n_obs=int(mask.sum()),
            interpretation=interp,
        ))

    return results


def print_dm_results(results: list[DMResult]) -> None:
    print("\n=== Diebold-Mariano Testergebnisse ===")
    for r in results:
        sig = "***" if r.p_value < 0.01 else ("**" if r.p_value < 0.05 else ("*" if r.p_value < 0.10 else ""))
        print(f"  {r.source_1:20s} vs {r.source_2:20s}: "
              f"DM={r.dm_statistic:+.3f}, p={r.p_value:.4f} {sig}")
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    if not BRIER_CSV.exists():
        print(f"FEHLER: {BRIER_CSV} nicht gefunden.")
        print("Zuerst ausfuehren: python -m operations.analysis.brier_score")
        return

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(BRIER_CSV)
    print(f"Geladen: {BRIER_CSV} ({len(df)} Tage, {df['date'].min()} bis {df['date'].max()})")

    # 1. Reliability Diagram
    plot_reliability_diagram(df, RESULTS_DIR / "h1_reliability_curve.png")

    # 2. Diebold-Mariano
    dm_results = run_diebold_mariano(df)
    print_dm_results(dm_results)

    dm_out = RESULTS_DIR / "h1_diebold_mariano.json"
    dm_dicts = [r._asdict() for r in dm_results]
    dm_out.write_text(json.dumps(dm_dicts, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"DM-Ergebnisse gespeichert: {dm_out}")


if __name__ == "__main__":
    main()
