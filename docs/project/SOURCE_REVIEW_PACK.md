# Quellen-Review-Pack — 11 Priority-1-Methodenquellen

Zweck: das eine echte Gate vor „abgabereif" schnell abarbeiten. Pro Quelle:
Fundstelle, gestuetzter Claim, was zu bestaetigen ist, was nicht behauptet werden
darf, und welche Ledger-Felder du eintraegst. Reihenfolge = `priority_order` aus
`data/results/thesis_source_review_worksheet.csv`.

So gehst du vor (pro Quelle, ~10 Min): Quelle oeffnen → relevanten Abschnitt
lesen → im Ledger (`data/results/thesis_source_review_progress_ledger.csv`) die
Felder `page_or_section_note`, `claim_support_decision`, `blocked_wording_check`,
`citation_use_decision`, `reviewed_by`, `reviewed_at` setzen → erst dann in
`data/literature/literature_index.csv` `status` von `skimmed` auf `reviewed`/
`cited` heben. Keine automatische Hochstufung.

---

## 1 — zotero_poly_001 · Tsang & Yang (2026), Polymarket 2024 Election
- Fundstelle: lokal `C:\Users\chole\Zotero\Polymarket\2024 election.pdf` · arXiv:2603.03136
- Stuetzt: H2 (Ereignisfenster), H3 (Wallet-Tiers/Top-Tier-Timing), Monitor
- Bestaetigen: Transaktions-/Whale-Episoden-Framing und Ereignis-Reaktion als Kontext fuer H2/H3
- Nicht behaupten: Intraday-Speed, Post-hoc-Auswahl, identifizierte Insider-Wallets, handelbare Strategie
- Hinweis: lokale PDF evtl. aeltere Version — gegen arXiv-Abstract gegenpruefen

## 2 — zotero_poly_002 · Cutting et al. (2025), Betting Markets vs Polling
- Fundstelle: lokal `...\Zotero\Polymarket\2507.08921v1.pdf` · arXiv:2507.08921
- Stuetzt: H1 (bounded), Swiss-Fallstudie
- Bestaetigen: Markt-vs-Umfrage-Forecast-Vergleich als Rahmen; bounded Brier-Aussage
- Nicht behaupten: „Polymarket immer besser", Mehr-Wahlen-Beweis, Kausalitaet, Effizienzbeweis vor dem Resultat

## 3 — lit_brier_001 · Brier (1950), Verification of Forecasts
- Fundstelle: DOI 10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2 (nicht lokal)
- Stuetzt: H1-Methode (Brier-Score)
- Bestaetigen: Brier-Score als mittlerer quadratischer Fehler von Wahrscheinlichkeitsprognosen (S. 1–3)
- Nicht behaupten: Ueberlegenheit, Reaktionsgeschwindigkeit, RCP-Wahrscheinlichkeit ohne Transformation

## 4 — lit_emh_001 · Fama (1970), Efficient Capital Markets
- Fundstelle: DOI 10.2307/2325486 (nicht lokal)
- Stuetzt: H1/H2-Rahmen (Effizienzbegriff)
- Bestaetigen: EMH-Definition (weak/semi-strong/strong) als theoretischer Rahmen
- Nicht behaupten: universelle Effizienz, allgemeine Prognosedominanz

## 5 — zotero_poly_005 · Hanson (2007), Insider Trading and Prediction Markets
- Fundstelle: lokal `...\Zotero\Polymarket\insiderbet.pdf` · hanson.gmu.edu/insiderbet.pdf
- Stuetzt: H3 (konzeptionelle/rechtliche Vorsicht)
- Bestaetigen: theoretischer Rahmen zu Insider/Information in Prognosemaerkten
- Nicht behaupten: H3-Resultat als Insider-/Kausal-/Profitabilitaetsbeweis

## 6 — lit_dm_001 · Diebold & Mariano (1995), Comparing Predictive Accuracy
- Fundstelle: DOI 10.1080/07350015.1995.10524599 (nicht lokal)
- Stuetzt: H1 (Verlustreihen-Vergleich)
- Bestaetigen: DM-Test vergleicht Prognosegenauigkeit zweier Verlustreihen, nicht Mechanismen
- Nicht behaupten: Kausalitaet, breite Ueberlegenheit

## 7 — lit_eventstudy_001 · MacKinlay (1997), Event Studies
- Fundstelle: JSTOR 2729691 (nicht lokal)
- Stuetzt: H2 (Ereignisfenster-Design)
- Bestaetigen: Event-Window-Methodik; Begruendung des Fensterdesigns
- Nicht behaupten: Intraday-Speed bei Tagesaufloesung, Post-hoc-Auswahl

## 8 — lit_granger_001 · Granger (1969), Causal Relations / Cross-Spectral
- Fundstelle: DOI 10.2307/1912791 (nicht lokal)
- Stuetzt: H3 (Lead-Lag/Granger)
- Bestaetigen: Granger-Test als praediktive Timing-Diagnostik, nicht echte Kausalitaet
- Nicht behaupten: Kausalitaetsbeweis, private Information, Profitabilitaet

## 9 — zotero_poly_006 · Buergi, Deng & Whelan (2025), Makers and Takers (Kalshi)
- Fundstelle: SSRN abstract 5502658 · lokal `...\Zotero\Polymarket\Kalshi Makers and takers paper.pdf`
- Stuetzt: Monitor-Prototyp, Future-Agents (Mikrostruktur/Favourite-Longshot)
- Bestaetigen: Mikrostruktur-Framing; nur Kontext, keine direkte Polymarket-Evidenz
- Nicht behaupten: agentenberechnete Metriken, autonomer Handel, Effizienzschluss

## 10 — zotero_poly_009 · Wu (2024), Unveiling Polymarket (Mint Ventures)
- Fundstelle: research.mintventures.fund/2024/10/09/... · lokal `...\Zotero\Polymarket\Unveiling Polymarket....htm`
- Stuetzt: Monitor-Prototyp (Kontext)
- Bestaetigen: Branchen-Kontext zu Positionierung/Risiken; keine akademische Evidenz
- Nicht behaupten: Kausal-/Misconduct-/Effizienz-/Profit-Claim

## 11 — zotero_poly_007 · Rezabek (2024), Convergence/Volatility/Biases (CU-Thesis)
- Fundstelle: hdl.handle.net/20.500.11956/194870 · lokal `...\Zotero\Polymarket\master thesis.pdf`
- Stuetzt: H3 (Wallet-Tier-Kontext, Bias/Volatilitaet)
- Bestaetigen: Framing zu Konvergenz/Volatilitaet/Bias als Limitationskontext
- Nicht behaupten: willkuerliche Whale-Schwelle, identifizierte Insider-Wallets

---

## Gesperrt / nicht jetzt
- `zotero_poly_004` (EMH.pdf): **rejected** — nicht zitieren, ersetzt durch `lit_emh_001`.
- `zotero_poly_010` (PolyBench): blocked/future-only — nur nach separater Status-Pruefung.
- `zotero_poly_003`, `zotero_poly_008`: aktuell nicht gemappt — erst zitieren, wenn an einen Claim gebunden.

Merke: Dieser Pack aendert keinen Quellenstatus. Er macht das Lesen schnell; die
Entscheidung traegst du im Ledger.
