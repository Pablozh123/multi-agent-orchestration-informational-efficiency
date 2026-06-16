# Methodiknote: RCP Umfrage-zu-Wahrscheinlichkeit-Transformation

Thesis-Abschnitt: 3.2 (Daten und Methodik)
Status: dokumentiert, Gate noch geschlossen (Advisor-Freigabe ausstehend)
Bezug: `ingest/rcp.py`, `operations/analysis/brier_score.py`, ARCHITECTURE_DECISIONS.md §8

## Zweck

RealClearPolitics (RCP) liefert **Umfragedurchschnitte**, keine nativen
Gewinnwahrscheinlichkeiten. Architektur-Regel §8 sperrt RCP aus allen
Brier-/Kalibrierungs-Metriken, **bis die Transformation dokumentiert ist**. Diese
Note ist genau dieses fehlende Dokument. Sie beschreibt die im Code bereits
implementierte Transformation, begruendet ihre Annahmen und legt die Regeln fest,
unter denen RCP thesis-faehig wird.

Sie aendert keinen Code und stuft RCP nicht automatisch hoch. Sie macht die
Methode pruefbar und entscheidbar.

## Die Transformation

Implementiert in `ingest/rcp.py::poll_pct_to_probability`:

```
margin       = (trump_pct - harris_pct) / 100
P(Trump-Sieg) = expit(margin * 4.0)        # expit = logistische Funktion
P(Harris)     = 1 - P(Trump-Sieg)
```

Eigenschaften:

- **Symmetrisch:** gleiche Anteile ergeben exakt 0.5.
- **Beschraenkt:** Output liegt offen in (0, 1).
- **Monoton:** groesserer Vorsprung -> hoehere Wahrscheinlichkeit.
- **Kalibrierungsbeispiel:** 5 Prozentpunkte Vorsprung -> ca. 0.73.

Der Skalierungsfaktor **4.0** ist eine **methodische Entscheidung**, kein auf die
Wahlausgaenge gefitteter Parameter. Er erzeugt eine bewusst moderate Sigmoidkurve:
genug Reagibilitaet, um Vorspruenge in Wahrscheinlichkeiten zu uebersetzen, ohne
kleine Umfragevorspruenge in Quasi-Sicherheiten (>0.95) zu verwandeln. Genau weil
der Faktor gesetzt und nicht gefittet ist, bleibt die Transformation reproduzierbar
und frei von Outcome-Leakage.

## Abgrenzung: zwei getrennte Poll-Transformationen im Repo

Wichtig fuer die saubere Methodik — das Repo enthaelt **zwei verschiedene**
Umfrage-zu-Wahrscheinlichkeit-Modelle. Sie duerfen im Text nicht vermischt werden:

| Transform | Ort | Funktion | Einsatz |
| --- | --- | --- | --- |
| **RCP-Logit** (diese Note) | `ingest/rcp.py` | `expit(margin * 4.0)` | nationaler RCP-Durchschnitt Trump vs. Harris |
| **Normal-Fehler-Modell** | H1 State-Extensions | Normal-CDF ueber Margin, MAE-Annahme ~3.8 pp | State-Polling-Averages (538, 270toWin) |

Die State-Extensions (Figuren 6, 7, 10a) nutzen das Normal-CDF-Modell und sind dort
bereits per Sensitivitaetsanalyse (MAE 2.0 bis 10.0 pp) dokumentiert. Diese Note
betrifft ausschliesslich den **RCP-Logit** auf den nationalen Durchschnitt.

## Annahmen und Grenzen

- RCP ist ein Umfrage-Aggregat, kein probabilistisches Forecast-Modell; die
  abgeleitete Wahrscheinlichkeit ist ein **dokumentierter Proxy**, kein
  publizierter RCP-Forecast.
- Der Faktor 4.0 ist global und konstant; er modelliert **keine** sich mit dem
  Wahlhorizont aendernde Unsicherheit (anders als ein echtes Forecast-Modell).
- National-only: diese Note rechtfertigt keine State-Level-RCP-Nutzung.
- Datenlage: aktuell stehen **0 RCP-Zeilen** in `poll_forecasts` (nur 245
  FiveThirtyEight-Zeilen). RCP muss erst via `ingest_rcp` befuellt werden, bevor
  ein Vergleich moeglich ist.

## Verwendungsregel (Gate)

1. **Default bleibt aus.** `include_rcp=False` und
   `rcp_transformation_documented=False` bleiben Standard in
   `BrierAnalysisConfig`. Kein Code-Flip durch diese Note.
2. **RCP nie als Primaerbeleg.** Falls aktiviert, erscheint RCP nur als
   **Sekundaer-/Sensitivitaetsvergleich** neben dem FiveThirtyEight-Primaerbeleg,
   nie als Hauptergebnis fuer H1.
3. **Sensitivitaet ist Pflicht.** Vor jeder thesis-faehigen RCP-Aussage ein
   Skalierungsfaktor-Sweep (z.B. 3.0 / 4.0 / 5.0) analog zur bestehenden
   MAE-Sensitivitaet; Ergebnis nur halten, wenn die Richtung robust ist.
4. **Advisor-Freigabe.** Faktor 4.0 und die Sekundaer-Rolle mit dem Dozenten
   bestaetigen (Drafting-Schritt `draft_09_advisor_iteration`), bevor
   `rcp_transformation_documented=True` gesetzt wird.
5. **Formulierung bleibt begrenzt:** "aus dem RCP-Durchschnitt abgeleitete
   Wahrscheinlichkeit" — nie "RCP-Forecast" oder "RCP-Prognose".

## Tests

Bestehende Abdeckung in `tests/test_ingest.py`:
`test_rcp_probability_range` (Output in [0,1]) und `test_rcp_symmetric`
(gleiche Anteile -> 0.5). Vor Aktivierung ergaenzen: ein Test, der den
Kalibrierungspunkt fixiert (5 pp -> ~0.73), damit der Faktor 4.0 gegen stille
Aenderung geschuetzt ist.

## Registrierung (damit die Note zaehlt)

- Als Methodenquelle in `data/literature/literature_index.csv` eintragen
  (eigene `source_id`, z.B. `method_rcp_transform_001`, status `reviewed`).
- Evidence-ID in `data/results/thesis_evidence_map.csv` anlegen, die diese Note
  an `ingest/rcp.py` und die H1-Artefakte bindet.
- Erst danach ist das Setzen von `rcp_transformation_documented=True` regelkonform.
