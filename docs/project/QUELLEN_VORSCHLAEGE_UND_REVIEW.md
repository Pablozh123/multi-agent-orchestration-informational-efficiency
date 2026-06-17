# Quellen: Vorschlaege und Review (Stand 2026-06-17)

Zwei Teile: A) gepruefte neue Quellen-Kandidaten fuer die Literatur-Luecken,
B) Review-Workflow und Status der vorhandenen Quellen. Alle neuen Quellen sind
VOR der Zitation zu reviewen (Originalstelle bestaetigen).

---

## Teil A — Vorgeschlagene neue Quellen

Auswahl nach wissenschaftlichem Standard: peer-reviewed Top-Journals und
etablierte Working Paper, einschlaegig fuer Forschungsfrage und Hypothesen. Die
ersten sechs sind vollstaendig verifiziert, die letzten zwei sind aktuell und im
Review noch in den Autorenangaben zu bestaetigen.

**1. Wolfers & Zitzewitz (2004) — Prediction Markets.**
*Journal of Economic Perspectives, 18*(2), 107–126. Peer-reviewed (Top-Journal).
Passt zu: Kapitel 2 (Markteffizienz/Informationsaggregation), Kapitel 1 (Relevanz).
Beleg fuer: Maerkte aggregieren verteilte Information zu meist treffsicheren
Forecasts und schlagen einfache Benchmarks. Zugang: AEA / NBER w10504.

**2. Wolfers & Zitzewitz (2006) — Interpreting Prediction Market Prices as Probabilities.**
NBER Working Paper Nr. 12200. Working Paper (stark zitiert). Passt zu: Kapitel 2
(Begriffsklaerung) und Kapitel 3 (Methodik, Preis als Wahrscheinlichkeit / RCP).
Beleg fuer: unter welchen Bedingungen Marktpreise mittleren Erwartungen entsprechen.

**3. Manski (2006) — Interpreting the Predictions of Prediction Markets.**
*Economics Letters, 91*(3), 425–429 (Seiten im Review bestaetigen). Peer-reviewed.
Passt zu: Kapitel 2 (kritische Einordnung) und Kapitel 8 (Limitationen). Beleg fuer:
Preise vermengen Erwartungen und Risikopraeferenzen — Vorsicht bei der Gleichsetzung
Preis = Wahrscheinlichkeit. Wichtig fuer die scope-spezifische Argumentation.

**4. Berg, Nelson & Rietz (2008) — Prediction Market Accuracy in the Long Run.**
*International Journal of Forecasting, 24*(2), 285–300 (Seiten im Review bestaetigen).
Peer-reviewed. Passt zu: Kapitel 2 (Maerkte vs. Umfragen) und H1. Beleg fuer: IEM
schlagen Umfragen langfristig in rund 74 Prozent der Vergleiche, relativer Vorteil
steigt mit dem Prognosehorizont.

**5. Arrow et al. (2008) — The Promise of Prediction Markets.**
*Science, 320*(5878), 877–878. DOI 10.1126/science.1157679. Peer-reviewed
(Multi-Autoren-Statement fuehrender Oekonomen). Passt zu: Kapitel 2 (Effizienz-
und Politik-Rahmung, Autoritaet). Beleg fuer: Prognosemaerkte als legitimes,
informationsaggregierendes Forecast-Instrument.

**6. Gneiting & Raftery (2007) — Strictly Proper Scoring Rules, Prediction, and Estimation.**
*Journal of the American Statistical Association, 102*(477), 359–378. Peer-reviewed.
Passt zu: Kapitel 2 (Messung der Prognosequalitaet) und Kapitel 3 (Methodik). Beleg
fuer: der Brier-Score ist ein strikt-proper Scoring Rule (belohnt ehrliche,
gut kalibrierte Wahrscheinlichkeiten) — methodische Rechtfertigung von H1.

**7. Iowa Electronic Markets: Forecasting the 2024 U.S. Presidential Election (2025).**
*PS: Political Science & Politics, 58*(2). Peer-reviewed. Autoren im Review
bestaetigen. Passt zu: Kapitel 2 / H1 (aktuelle 2024-Markt-vs-Umfrage-Evidenz).

**8. Prediction Markets? The Accuracy and Efficiency of \$2.4 Billion in the 2024 Presidential Election (2024).**
SocArXiv d5yx2 (Preprint). Autoren/Status im Review bestaetigen. Passt zu: Kapitel 2
und Kapitel 8. Beleg fuer: Gegenakzent — plattformuebergreifend war die Trefferquote
gemischt (Polymarket niedriger als PredictIt). Stuetzt die vorsichtige Lesart und
verhindert eine Ueberzeichnung der Marktueberlegenheit.

Optional spaeter: Hayek (1945, Informationsaggregation), falls Kapitel 2 die
theoretische Tiefe braucht.

---

## Teil B — Review der Quellen

### Workflow (pro Behauptung)
1. Originalstelle aufsuchen (richtige Quelle, richtiger Abschnitt).
2. Pruefen: stuetzt die Stelle die konkrete Aussage im Text wirklich?
3. Exakte Seite oder Abschnitt notieren.
4. Zitierform festlegen (Paraphrase oder Zitat mit Seitenzahl).
5. Im Ledger `final_citation_ready = TRUE` setzen. Bei Nichtdeckung: Aussage
   umformulieren oder Quelle ersetzen.

Regeln: Seitenzahl bei direkten Zitaten Pflicht, Sekundaerzitate (`zitiert nach`)
nur als Ausnahme, abgelehnte Quelle `zotero_poly_004` nicht verwenden.

### Status der vorhandenen Quellen (Ledger, alle noch FALSE)

| Quelle | Zu bestaetigen | Wer |
|---|---|---|
| lit_brier_001 | Brier-Formel S. 1–3 | ich (Klassiker, hohe Sicherheit) |
| lit_dm_001 | Test-Setup gleiche Genauigkeit | ich |
| lit_emh_001 | Weak/semi-strong/strong-Abschnitt | ich |
| lit_eventstudy_001 | Estimation-/Event-Window + CAR | ich |
| lit_granger_001 | Granger-Definition (praediktiv, nicht kausal) | ich |
| zotero_poly_001 | Volumen-Dekomposition / Grosskonto (arXiv) | ich (arXiv abrufbar) |
| zotero_poly_002 | Swing-State-Resultat (arXiv) | ich (arXiv abrufbar) |
| zotero_poly_005 | Aggregation/Maerkte-vs-Umfragen — Volltext gelesen | nur ready setzen |
| zotero_poly_007 | Biases + hoehere Volatilitaet | ich (zugaenglich) |
| zotero_poly_009 | Information discovery, nicht Truth-Machine — gelesen | nur ready setzen |
| zotero_poly_006 | SSRN nicht abrufbar, lokale PDF | DU (lokale PDF lesen) |

Noch nicht im Ledger (spaeter ergaenzt, Review-Eintrag fehlt): lit_kyle_001,
zotero_delvecchio_001, news_polymarket_integrity_001, news_chainalysis_forensics_001.

### Was ich uebernehmen kann
Die fuenf Methoden-Klassiker und die oeffentlich (arXiv/Web) zugaenglichen
Polymarket-Quellen kann ich gegen die jeweils gestuetzte Aussage pruefen und im
Ledger ready setzen. Nur `zotero_poly_006` braucht deine Lesung der lokalen PDF.

---

## Anhang — Ready-to-paste BibTeX (erst nach Review in references.bib)

```bibtex
@article{lit_wolfers_2004, author={Wolfers, Justin and Zitzewitz, Eric},
  title={Prediction Markets}, journal={Journal of Economic Perspectives},
  year={2004}, volume={18}, number={2}, pages={107--126}}
@techreport{lit_wolfers_2006, author={Wolfers, Justin and Zitzewitz, Eric},
  title={Interpreting Prediction Market Prices as Probabilities},
  institution={NBER Working Paper No. 12200}, year={2006}}
@article{lit_manski_2006, author={Manski, Charles F.},
  title={Interpreting the Predictions of Prediction Markets},
  journal={Economics Letters}, year={2006}, volume={91}, number={3}, pages={425--429}}
@article{lit_berg_2008, author={Berg, Joyce E. and Nelson, Forrest D. and Rietz, Thomas A.},
  title={Prediction Market Accuracy in the Long Run},
  journal={International Journal of Forecasting}, year={2008}, volume={24}, number={2}, pages={285--300}}
@article{lit_arrow_2008, author={Arrow, Kenneth J. and others},
  title={The Promise of Prediction Markets}, journal={Science},
  year={2008}, volume={320}, number={5878}, pages={877--878}}
@article{lit_gneiting_2007, author={Gneiting, Tilmann and Raftery, Adrian E.},
  title={Strictly Proper Scoring Rules, Prediction, and Estimation},
  journal={Journal of the American Statistical Association}, year={2007},
  volume={102}, number={477}, pages={359--378}}
@article{lit_iem_2024, author={Berg, Joyce E. and others},
  title={Iowa Electronic Markets: Forecasting the 2024 U.S. Presidential Election},
  journal={PS: Political Science \& Politics}, year={2025}, volume={58}, number={2},
  note={Autoren im Review bestaetigen}}
@misc{lit_poly24_accuracy,
  title={Prediction Markets? The Accuracy and Efficiency of \$2.4 Billion in the 2024 Presidential Election},
  year={2024}, note={SocArXiv d5yx2; Autoren im Review bestaetigen}}
```
