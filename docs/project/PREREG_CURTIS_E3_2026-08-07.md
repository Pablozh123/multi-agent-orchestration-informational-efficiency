# Preregistration: President Curtis S01E03 „Ex" — Mention-Markt-Testlauf

Angelegt 07.08.2026 ~21:20 CEST, VOR Platzierung jeglicher Orders und vor
Ausstrahlung (So 09.08. 23:30 EST = Mo 10.08. 05:30 CEST). Zweck: Test der
These „Transkript-Basisraten + Folgeninhalts-Infos schlagen generisches
Market-Making in TV-Episoden-Mention-Märkten". Auswertung nach Resolution
per Brier-Abgleich gegen diese Tabelle — Tabelle danach NICHT ändern.

Event: `what-will-be-said-during-the-third-episode-of-president-curtis-season-1-20260804193637080`

## Evidenzbasis

- Volltranskripte E1 („Pilot") + E2 („Triangle"), scrapsfromtheloft.com,
  Zählung mit exakten Wortgrenzen, Dialog-Kontexte manuell geprüft
  (Synopsis-Boilerplate der Seiten ausgeschlossen).
- E3-Inhalt: Curtis auf Inaugurations-Gala der Ex-Frau; Banks + O'Doyle
  in Job-Evaluation (Offsite). Kein Monster-of-the-week-Plot erkennbar.
- O'Doyle ist Secret-Service-Agent (Hauptfigur, jede Episode präsent).
- Regeln: Recap/Preview-Segmente und Hintergrundmusik zählen nicht.

## Prognosen (p_uns) vs. Markt, Stand 07.08. ~21:15 CEST

| Markt | E1 | E2 | Markt Bid/Ask | p_uns | Order |
| --- | --- | --- | --- | --- | --- |
| Secret | ~6 | ~5 | 0.34/0.38 | **0.88** | Taker: YES 100 @ 0.38 (Kern) |
| Paranormal | 0 | 2 | 0.12/0.16 | **0.40** | Taker: YES 100 @ 0.16 |
| Rick | 1 | 0 | 0.09/0.13 | **0.25** | Taker klein: YES 50–100 @ 0.13 (optional) |
| President 10+ | ~22 | ~15 | 0.06/0.93 | **0.85** | Maker: YES-Bid 0.60, 25–50 Sh |
| Ghost | 1 | 4 | 0.08/0.87 | **0.55** | Maker: YES-Bid 0.40, 25–50 Sh |
| White House | 8 | 0 | 0.05/0.92 | **0.55** | Maker: YES-Bid 0.35, 25–50 Sh |
| CIA | 18 | ~0 | 0.05/0.92 | **0.35** | keine |
| Morty | 1 | 0 | 0.05/0.50 | **0.20** | keine |
| Security | ~2 | 1 | 0.981/0.999 | **0.93** | keine (kein Puffer zum Ask) |
| Black | 0 | 0 | 0.08/0.92 | **0.30** | optional Maker: NO-Bid 0.60 |
| Anomaly | 0 | 0 | 0.05/0.95 | **0.15** | optional Maker: NO-Bid 0.60 |
| Episode airt nicht | — | — | 0.001/0.048 | **0.02** | keine |

Kapitalrahmen Taker gesamt: ≤ 67 USD (38 + 16 + 13). Maker-Limits
zusätzlich ≤ ~60 USD gebunden. Alles innerhalb der üblichen Clip-Größen.

## Regeln für die Ausführung

1. Vorher den offiziellen E3-Promo-Clip ansehen (Adult-Swim-YouTube /
   Bleeding-Cool-Preview): jedes dort hörbare Zielwort → p auf ~0.97,
   Kauf bis knapp unter Promo-Sicherheit vertretbar. Befund hier notieren.
2. NIE über das Top-Level des Buchs hinaus marketordern — hinter den
   100er-Clips ist das Buch leer (nächste Asks 0.74–0.98).
3. Maker-Fills sind adversely selected (Presse-Screener existieren) —
   deshalb kleine Clips; ein gefülltes Limit ist ein Datenpunkt, kein
   Nachlege-Signal.
4. Post-Air-Sweep Mo ~06:00 CEST nur mit eigener Sichtung/Aufnahme;
   Zwei-Methoden-Konsens vor jedem NO gilt weiter (Ohr + HBO-Max-Subs).

## Promo-Befund (Regel 1 erledigt, 07.08. ~21:45 CEST)

Offizieller Clip „EARLY PREVIEW: Curtis Prepares To See His Ex-Wife"
(YouTube GMWhuF5oWK8, Adult-Swim-Kanal, 122 s; large-v3-Transkript im
Session-Scratchpad, `promo_e3_transkript.txt`). Zielwort-Treffer:

- „Security" 1× („the head of Homeland Security") — bestätigt den
  0.98-Markt, kein Trade.
- „President" 1× („brandished an edged weapon at the president") —
  Zähler tickt, für 10+ ohne Aussagekraft.
- Alle übrigen Zielwörter: 0 im Clip. Absenz beweist nichts
  (2 Szenen von ~22 min) — keine Prognoseänderung.

Neue Inhalts-Infos: Offsite-Einrichtung heißt „West Wing World";
neuer Agent „Chomps" ersetzt O'Doyle; O'Doyle-Suspendierung hält den
Secret-Service-Strang zentral (stützt p=0.88 für „Secret" qualitativ).

**Prognosen unverändert.** Ausführung: `curtis_e3_orders.py`
(operations/pipeline), Platzierung durch die Autorin selbst.

## Auswertung (nach Resolution auszufüllen)

| Markt | Ergebnis | p_uns | Markt-Mid vorab | Brier uns | Brier Markt |
| --- | --- | --- | --- | --- | --- |
| … | | | | | |
