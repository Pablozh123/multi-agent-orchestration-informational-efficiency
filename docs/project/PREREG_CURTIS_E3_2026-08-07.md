# Preregistration: President Curtis S01E03 "Ex" — mention-market test run

> English translation (2026-08-22) of the German original pre-registered on
> 2026-08-07. Substance unchanged; the original wording is preserved in the
> git history of this file.

Created 2026-08-07 ~21:20 CEST, BEFORE any orders were placed and before
airing (Sun 2026-08-09 23:30 EST = Mon 2026-08-10 05:30 CEST). Purpose: test
of the thesis "transcript base rates + episode-content information beat
generic market making in TV-episode mention markets". Evaluation after
resolution via Brier comparison against this table — table NOT to be changed
afterwards.

Event: `what-will-be-said-during-the-third-episode-of-president-curtis-season-1-20260804193637080`

## Evidence base

- Full transcripts E1 ("Pilot") + E2 ("Triangle"), scrapsfromtheloft.com,
  counted with exact word boundaries, dialogue contexts checked manually
  (the sites' synopsis boilerplate excluded).
- E3 content: Curtis at his ex-wife's inauguration gala; Banks + O'Doyle
  in a job evaluation (offsite). No monster-of-the-week plot apparent.
- O'Doyle is a Secret Service agent (main character, present in every episode).
- Rules: recap/preview segments and background music do not count.

## Forecasts (p_ours) vs. the market, as of 2026-08-07 ~21:15 CEST

| Market | E1 | E2 | Market bid/ask | p_ours | Order |
| --- | --- | --- | --- | --- | --- |
| Secret | ~6 | ~5 | 0.34/0.38 | **0.88** | Taker: YES 100 @ 0.38 (core) |
| Paranormal | 0 | 2 | 0.12/0.16 | **0.40** | Taker: YES 100 @ 0.16 |
| Rick | 1 | 0 | 0.09/0.13 | **0.25** | Taker small: YES 50–100 @ 0.13 (optional) |
| President 10+ | ~22 | ~15 | 0.06/0.93 | **0.85** | Maker: YES bid 0.60, 25–50 sh |
| Ghost | 1 | 4 | 0.08/0.87 | **0.55** | Maker: YES bid 0.40, 25–50 sh |
| White House | 8 | 0 | 0.05/0.92 | **0.55** | Maker: YES bid 0.35, 25–50 sh |
| CIA | 18 | ~0 | 0.05/0.92 | **0.35** | none |
| Morty | 1 | 0 | 0.05/0.50 | **0.20** | none |
| Security | ~2 | 1 | 0.981/0.999 | **0.93** | none (no buffer to the ask) |
| Black | 0 | 0 | 0.08/0.92 | **0.30** | optional Maker: NO bid 0.60 |
| Anomaly | 0 | 0 | 0.05/0.95 | **0.15** | optional Maker: NO bid 0.60 |
| Episode does not air | — | — | 0.001/0.048 | **0.02** | none |

Total taker capital frame: ≤ 67 USD (38 + 16 + 13). Maker limits bind an
additional ≤ ~60 USD. All within the usual clip sizes.

## Execution rules

1. Watch the official E3 promo clip first (Adult Swim YouTube /
   Bleeding Cool preview): every target word audible there → p to ~0.97,
   buying up to just under promo certainty is defensible. Record the
   finding here.
2. NEVER market-order past the top level of the book — behind the
   100-share clips the book is empty (next asks 0.74–0.98).
3. Maker fills are adversely selected (press screeners exist) — hence
   small clips; a filled limit is a data point, not a signal to add.
4. Post-air sweep Mon ~06:00 CEST only with our own viewing/recording;
   the two-method consensus before any NO still applies (ear + HBO Max
   subtitles).

## Promo finding (rule 1 done, 2026-08-07 ~21:45 CEST)

Official clip "EARLY PREVIEW: Curtis Prepares To See His Ex-Wife"
(YouTube GMWhuF5oWK8, Adult Swim channel, 122 s; large-v3 transcript in
the session scratchpad, `promo_e3_transkript.txt`). Target-word hits:

- "Security" 1× ("the head of Homeland Security") — confirms the
  0.98 market, no trade.
- "President" 1× ("brandished an edged weapon at the president") —
  the counter ticks, meaningless for 10+.
- All other target words: 0 in the clip. Absence proves nothing
  (2 scenes of ~22 min) — no forecast change.

New content information: the offsite facility is called "West Wing World";
new agent "Chomps" replaces O'Doyle; O'Doyle's suspension keeps the
Secret Service thread central (qualitatively supports p=0.88 for "Secret").

**Forecasts unchanged.** Execution: `curtis_e3_orders.py`
(operations/pipeline), placement by the author herself.

## Placement status (2026-08-07 19:56 UTC, executed by the author)

All 6 orders placed (`curtis_e3_orders.py --scharf --mit-rick`,
log `data/live/curtis_e3/orders.jsonl`, wallet 0x29afE1…F88d):

- Taker, all fully filled (MATCHED): Secret 100 @ 0.38, Paranormal
  100 @ 0.16, Rick 100 @ 0.13 — 67 USD invested.
- Maker GTC resting: President 10+ 50 @ 0.60, Ghost 40 @ 0.40,
  White House 40 @ 0.35 — 60 USD bound.

Max taker payout at 3× YES: 300 USD. Monitoring plan: NO ongoing
book-watching (no action needed before airing; filled maker limits are
data points, not signals to add). Next checkpoint: Monday 2026-08-10
during the day CEST — maker fill status, HBO Max/subtitle comparison,
UMA resolutions, then the Brier table.

## Evaluation (to be filled in after resolution)

| Market | Outcome | p_ours | Market mid beforehand | Brier ours | Brier market |
| --- | --- | --- | --- | --- | --- |
| … | | | | | |
