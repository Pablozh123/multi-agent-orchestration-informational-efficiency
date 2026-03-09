---
name: brier-score
description: Brier Score Berechnung und Kalibrierungsanalyse. Nutze bei Forecast-Vergleichen, Prognosequalität, Calibration Curves.
---

# Brier Score & Kalibrierung

## Brier Score Formel
BS = (1/N) × Σ(forecast_i - outcome_i)²
- forecast_i: Vorhersage zwischen 0.0 und 1.0
- outcome_i: Tatsächliches Ergebnis (0 oder 1)
- BS = 0: Perfekte Vorhersage
- BS = 1: Maximal falsch

## Brier Skill Score
BSS = 1 - (BS_modell / BS_referenz)
- BSS > 0: Besser als Referenz
- BSS = 0: Gleich wie Referenz
- BSS < 0: Schlechter als Referenz

## Python-Implementierung
```python
from sklearn.metrics import brier_score_loss
from sklearn.calibration import calibration_curve

bs = brier_score_loss(outcomes, forecasts)
prob_true, prob_pred = calibration_curve(outcomes, forecasts, n_bins=10)
```

## Kalibrierungskurve (Reliability Diagram)
- X-Achse: Vorhergesagte Wahrscheinlichkeit (binned)
- Y-Achse: Tatsächliche Häufigkeit
- Perfekte Kalibrierung = Diagonale
- Über der Diagonale = Underconfident
- Unter der Diagonale = Overconfident
