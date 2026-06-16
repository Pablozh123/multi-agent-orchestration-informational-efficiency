# Swiss Referendum Final Case Study

## Generated Or Inspected

- Official result: rejected on 2026-06-14; official Yes share 45.21%, No share 54.79%, turnout 58.86%.
- Cantonal vote result: 10.0 Yes and 13.0 No cantonal votes.
- Poll rows compared: 7.
- Live Polymarket rows compared: 74.
- Price-history rows compared: 504.
- Official sources: https://swissvotes.ch/vote/686.00 and https://abstimmungen.admin.ch/details/2026-06-14?proposalId=6860.

## Key Numerical Result

- Latest live snapshot 2026-06-14T00:04:17Z: Polymarket Yes 21.50%; vote-share error 23.71 pp.
- Matched poll at latest live snapshot (SRG/gfs.bern / srg_gfs_bern_2026_w2): raw Yes 45.00%, raw error 0.21 pp; decided Yes 46.39%, decided error 1.18 pp.
- Live vote-share comparison: Polymarket beats the matched raw poll in 0/74 rows and the matched decided-share poll in 0/74 rows.
- Live binary outcome proxy: Polymarket has lower Brier loss than the raw poll proxy in 74/74 rows and than the decided-share poll proxy in 74/74 rows.
- Historical price window: Polymarket is closer to the official Yes share than the matched raw poll in 36/504 rows, first at 2026-04-28T10:00:06Z and last at 2026-06-01T12:00:07Z.
- Historical decided-share window: Polymarket beats the decided-share poll proxy in 108/504 rows, first at 2026-04-28T10:00:06Z and last at 2026-05-09T20:00:07Z.
- Best historical vote-share Polymarket point: 2026-04-29T17:00:05Z with Yes 44.50% and error 0.71 pp.

## Final Poll Accuracy

- SRG/gfs.bern final poll srg_gfs_bern_2026_w2: raw Yes 45.00%, raw error 0.21 pp; decided Yes 46.39%, decided error 1.18 pp.
- Tamedia/20 Minuten/LeeWas final poll tamedia_leewas_2026_w2: raw Yes 47.00%, raw error 1.79 pp; decided Yes 47.47%, decided error 2.26 pp.
- YouGov Schweiz final poll yougov_2026_w2_final: raw Yes 38.00%, raw error 7.21 pp; decided Yes 40.86%, decided error 4.35 pp.

## Bounded Interpretation

- Stimmenanteilsvergleich: Die finalen Umfragen, besonders SRG/gfs.bern, lagen naeher am offiziellen Ja-Anteil von 45.21% als die spaeten Polymarket-Live-Snapshots. Deshalb darf das Fallbeispiel nicht als Beleg formuliert werden, dass Polymarket den Stimmenanteil genauer vorhergesagt hat.
- Ergebnisrichtung: Die Initiative wurde abgelehnt. In der binaeren Proxy-Lesart zeigte Polymarket im lokalen Live-Fenster eine deutlich niedrigere Annahmewahrscheinlichkeit als die Umfrage-Ja-Anteile und damit ein staerkeres Ablehnungssignal.
- Historisches Fenster: Vor dem spaeten Live-Fenster gab es einzelne Price-History-Zeilen, in denen Polymarket naeher am spaeteren Ja-Anteil lag als der jeweilige Poll-Proxy. Das ist ein begrenzter Timing-Befund, kein Effizienzbeweis.

## Main Limitation

- Polymarket-Preise messen eine Annahmewahrscheinlichkeit, Umfragen messen Stimmenanteile. Die Brier-Proxy-Zeilen fuer Umfragen sind deshalb nur ein transparenter Vergleichsmodus und keine echte Kalibrierungsstudie traditioneller Prognosemodelle.

## Figure

![Swiss final case study figure](swiss_referendum_10mio_final_case_study.png)
