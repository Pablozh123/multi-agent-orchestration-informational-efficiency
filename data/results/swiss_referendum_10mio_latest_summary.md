# Swiss 10-Million Referendum Latest Summary

## Generated Or Inspected

- Comparison rows: 16.
- Polymarket snapshot rows: 16.
- Bounded price-history rows: 504.
- Curated poll rows: 7 from SRG/gfs.bern, Tamedia/20 Minuten/LeeWas, YouGov Schweiz.
- Poll-impact rows: 7 (observed_pre_post: 7).
- Poll reaction-window rows: 28.
- Poll reaction windows: 1h: latest observed +0.0 pp; 6h: latest observed -1.0 pp; 24h: latest observed -4.0 pp; 48h: latest observed -5.0 pp.
- Latest poll-source comparison rows: 3.
- Source-audit rows: 9.

## Poll Release Timing Summary

- tamedia_leewas_2026_w1 (Tamedia/20 Minuten/LeeWas, 2026-04-29T00:00:00Z): first post observation after 0.0 h, first change +1.0 pp; windows 1h +1.0 pp, 6h +2.0 pp, 24h +4.0 pp, 48h +5.0 pp; status observed_pre_post; descriptive no-causality scope.
- yougov_2026_w1 (YouGov Schweiz, 2026-05-05T00:00:00Z): first post observation after 0.0 h, first change +0.5 pp; windows 1h +0.5 pp, 6h +0.5 pp, 24h +0.0 pp, 48h -0.5 pp; status observed_pre_post; descriptive no-causality scope.
- srg_gfs_bern_2026_w1 (SRG/gfs.bern, 2026-05-08T03:56:00Z): first post observation after 0.1 h, first change +0.0 pp; windows 1h +0.0 pp, 6h +1.0 pp, 24h +1.0 pp, 48h -5.0 pp; status observed_pre_post; descriptive no-causality scope.
- yougov_2026_w2_interim (YouGov Schweiz, 2026-05-27T00:00:00Z): first post observation after 0.0 h, first change +1.0 pp; windows 1h +1.0 pp, 6h +1.5 pp, 24h -1.0 pp, 48h +1.0 pp; status observed_pre_post; descriptive no-causality scope.
- yougov_2026_w2_final (YouGov Schweiz, 2026-06-02T00:00:00Z): first post observation after 0.0 h, first change +3.0 pp; windows 1h +3.0 pp, 6h +1.5 pp, 24h +0.0 pp, 48h -5.0 pp; status observed_pre_post; descriptive no-causality scope.
- tamedia_leewas_2026_w2 (Tamedia/20 Minuten/LeeWas, 2026-06-03T00:00:00Z): first post observation after 0.0 h, first change +0.0 pp; windows 1h +0.0 pp, 6h -3.0 pp, 24h -5.0 pp, 48h -5.0 pp; status observed_pre_post; descriptive no-causality scope.
- srg_gfs_bern_2026_w2 (SRG/gfs.bern, 2026-06-03T03:55:00Z): first post observation after 0.1 h, first change +0.0 pp; windows 1h +0.0 pp, 6h -1.0 pp, 24h -4.0 pp, 48h -5.0 pp; status observed_pre_post; descriptive no-causality scope.

## Latest Poll-Source Comparison

- SRG/gfs.bern: srg_gfs_bern_2026_w2 published 2026-06-03T03:55:00Z; poll Yes 45.0%, decided Yes 46.4%, raw gap -22.0 pp, decided gap -23.4 pp; below_poll_proxy.
- Tamedia/20 Minuten/LeeWas: tamedia_leewas_2026_w2 published 2026-06-03T00:00:00Z; poll Yes 47.0%, decided Yes 47.5%, raw gap -24.0 pp, decided gap -24.5 pp; below_poll_proxy.
- YouGov Schweiz: yougov_2026_w2_final published 2026-06-02T00:00:00Z; poll Yes 38.0%, decided Yes 40.9%, raw gap -15.0 pp, decided gap -17.9 pp; below_poll_proxy.

## Key Numerical Result

- Latest snapshot: 2026-06-08T16:22:16Z.
- Latest matched poll: srg_gfs_bern_2026_w2 (SRG/gfs.bern).
- Polymarket Yes probability: 23.0%.
- Latest poll Yes share: 45.0%.
- Latest poll decided Yes share: 46.4%.
- Raw Yes gap: -22.0 pp.
- Decided Yes gap: -23.4 pp.
- Poll-proxy relation: below_poll_proxy.

## Bounded Interpretation

- The latest local Polymarket Yes probability is below the latest curated poll Yes share under the deterministic poll-proxy label. This is a descriptive comparison only.

## Main Limitation

- Poll shares are survey shares, not model-implied win probabilities. The decided-voter value is only yes_share / (yes_share + no_share). Poll-impact rows describe first observable pre/post Polymarket points and do not identify causality, market efficiency, tradeability, or true mispricing.

## Figure

![Swiss referendum comparison figure](swiss_referendum_10mio_efficiency.png)

## Reaction Window Figure

![Swiss referendum reaction-window figure](swiss_referendum_10mio_reaction_windows.png)

## Source Boundary

- BFS/admin.ch rows are context sources only. Current voting-intention poll inputs are SRG/gfs.bern, Tamedia/LeeWas, and YouGov Schweiz rows in the curated poll catalog.

## Local Artifacts

- Dashboard: `data\results\swiss_referendum_10mio_dashboard.html`.
- Figure: `data\results\swiss_referendum_10mio_efficiency.png`.
