# Vorregistrierung: President Curtis S01E07 „Ghosts" — Mention-Markt-Testlauf

Erstellt 04.09.2026 ~19:50 MESZ, VOR jeder Order und vor der Ausstrahlung
(So 06.09.2026 23:30 EST = Mo 07.09. 05:30 MESZ). Zweck: dritter Test der
These „Transkript-Basisraten + Episodeninhalt schlagen generisches Market
Making in TV-Episoden-Mention-Maerkten" — nach E3 (Wallet-Delta +142.94
inkl. E3) und E6 (Brier 0.143 vs. Markt-Mid 0.183, aber alle drei
Taker-Legs verloren). Auswertung nach Aufloesung per Brier gegen diese
Tabelle — Tabelle danach NICHT aendern.

Event: `956826` — „What will be said during the seventh episode of
President Curtis: Season 1?" (Gamma, liq 4.3k am 04.09.).

## Evidenzbasis

- Volltranskripte E1–E6 (scrapsfromtheloft.com), Zaehlung mit exakten
  Wortgrenzen (`curtis_e7.py`, Session-Scratchpad 04.09.), drei bekannte
  Synopsis-Boilerplate-Saetze entfernt. „president" enthaelt weiterhin
  Titelnennungen („President Curtis") und ist unzuverlaessig: E6 zaehlte
  roh 21, der Markt „President 10+" resolvte NO.
- Aufgeloeste Gamma-Wochen der Serie 12413 (E2–E6) via
  `python -m operations.analysis.mention_basisraten --serie 12413 --offen 956826`
  (Ergebnis `data/results/mention_basisraten_curtis_2026-09-04.json`).
- E6-Thesentest (Dossier §9.1): Treffer waren die Maker-Kandidaten (God
  5+ YES bei Mid 0.57, Monster YES bei Mid 0.41), Verluste die
  Taker-Kandidaten (Leprechaun 4/5 → NO, President 10+ → NO, Bank 5+ →
  NO: der Figurenname „Banks" zaehlte NICHT — Regelkanten-These
  falsifiziert).
- E7-Inhalt („Ghosts", Adult-Swim-Synopsis): Banks faengt sich Malware,
  O'Doyle steigt in ihr Computer-Gehirn; Curtis gibt dem Geist von
  President Lincoln ein Geschenk fuer dessen unerledigte Angelegenheiten.
- Regeln (gegen gelesen E6/E7, identische Schablone): Musik sowie
  Recap-/Preview-Segmente zaehlen nicht; Quelle ist der Initial-Release;
  „episode not air" 0.01.

## Prognosen (p_ours) vs. Markt, Stand 04.09.2026 ~19:15 MESZ

| Markt | E1–E6 (roh) | Gamma-Historie | Markt bid/ask | p_ours | Order (nur Maker) |
| --- | --- | --- | --- | --- | --- |
| God 5+ | 8·11·11·6·11·8 | 3/3 | 0.42/0.97 | **0.85** | YES-Bid 0.60, 40 sh |
| Hell | 4·5·6·9·3·8 | 3/3 | 0.52/0.97 | **0.85** | YES-Bid 0.65, 40 sh |
| Monster | 1·20·2·0·2·1 | 2/3 | 0.02/0.98 | 0.55 | YES-Bid 0.35, 30 sh (optional) |
| President 10+ | 27·21·20·16·14·21 (roh, E6=NO) | 2/5, letzte 3: 0/3 | 0.14/0.74 | 0.50 (Lincoln-Plot hebt) | YES-Bid 0.30, 30 sh (optional) |
| Worm | 0·3·0·0·0·3 | 1/1 | 0.07/0.98 | 0.35 (Malware ≈ „computer worm" moeglich) | YES-Bid 0.20, 30 sh (optional, klein) |
| Power | 1·3·2·0·3·21 | 2/3 | 0.66/0.97 | 0.65 | keine (Bid steht schon bei 0.66) |
| White House | 8·0·0·3·3·0 | 2/5 | 0.65/0.71 | 0.45 | keine — Bid 0.65 kann Screener-Info sein; weder kaufen noch faden |
| Leprechaun | 3·3·2·2·0·0 | 1/3 | 0.99/0.999 | = Markt (informiert) | keine — Regel: nie gegen ≥0.95 bei Plot-Woertern |
| Security | 2·1·2·1·1·1 | 5/5 | 0.958/1.00 | 0.90 | keine (kein Puffer) |
| Agent 5+ | 4·0·9·1·0·0 | 0/3 | 0.03/0.98 | 0.30 (Agenten-Plot, aber E6=0) | keine |
| Bank 5+ | 1·0·1·0·1·0 (nur Singular; Name zaehlt nicht) | 0/3 | 0.06/0.11 | 0.05 | keine |
| CIA · Rick | 17·0·0·0·0·0 · 2·0·0·0·0·0 | 0/5 · 0/5 | ~0.02/0.98 | 0.05 · 0.05 | keine |
| Episode not air | — | — | –/0.01 | 0.02 | keine |

Gebundenes Maker-Kapital, wenn alles ruht: 24 + 26 + 10.5 + 9 + 6 ≈
**75.5 USD**. Kein Taker-Leg (E6-Lektion; alle Asks stehen bei 0.97+).

## Ausfuehrungsregeln

1. **Promo-Clip zuerst** (Adult-Swim-YouTube / Bleeding Cool): jedes
   Zielwort, das hoerbar ist → p auf ~0.97; dann ist ein Taker-Kauf bis
   knapp unter Promo-Sicherheit vertretbar. Befund unten eintragen.
2. **Nur Maker-Limits**, kleine Clips. Gefuellte Limits sind adverse
   selektiert (Presse-Screener) — ein Fill ist ein Datenpunkt, kein
   Signal zum Nachlegen.
3. **Rezenz vor Gesamtquote** (Leprechaun-Lektion E6: 4/5 gesamt, 0/2
   zuletzt → NO). Wo die letzten drei Episoden von der Gesamtquote
   abweichen, gilt die Rezenz.
4. **Nie faden, was ≥0.95 steht**, wenn der Plot es erklaeren kann
   (Worm E6 0.93 → YES; Leprechaun E7 0.99).
5. Post-Air-Sweep Mo ~06:00 MESZ nur mit eigener Sichtung/Aufnahme;
   Zwei-Methoden-Konsens (Ohr + HBO-Max-Untertitel) vor jedem NO.
6. Platzierung durch die Autorin selbst (kein Bot, kein Order-Pfad in
   dieser Session).

## Promo-Befund (Regel 1, VOR Orders eintragen)

*(offen — Clip ansehen, Zielwoerter notieren, p anpassen, Zeitstempel.)*

## Platzierungsstand

*(offen)*

## Auswertung (nach Aufloesung)

| Markt | Outcome | p_ours | Markt-Mid vorher | Brier ours | Brier Markt |
| --- | --- | --- | --- | --- | --- |
| … | | | | | |
