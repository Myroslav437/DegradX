# V7 — RQ3, score validation by the degraded-map test (X5), and the X5 scores on the v1 maps

## What ran

- **Command.** `python scripts/v2/v7_scores.py --datasets MATR HUST --v1-datasets MATR HUST NASA_PCoE`, seed 20260915,
  CPU, a few minutes.
- **Part A.** On the V4 generated test units (generation seed 0; 20 windows per unit; 900 windows from 45 units per
  profile), the ground truth was degraded by the five v1 operators over their declared grids, under recency and uniform
  weighting.
  - Scores, all on the pattern-free counterpart map against the graded field (D01; identical to the window map here):
    rank agreement, channel allocation error (TV distance), temporal profile error (ϕ*-mass-weighted 1-Wasserstein over
    positions).
  - Readings, declared in r3 `v2.scoring`:
    - *resolution*: the v1 criterion, sign-aware, with 10 000 BCa resamples;
    - *registers*: as declared, (i) resolved and (ii) a mean change toward chance of at least 10 % of the
      chance-to-perfect distance, at some magnitude and at every larger one.
- **Part B.** The same scores on the saved v1 S8 maps (`data/attributions`) against the v1 ground truth regenerated from
  `data/generated`, for MATR, HUST and (v1 only) NASA PCoE, under recency and uniform weighting. No new attribution.
- **Re-run 2026-10-08** after the v2 pipeline review. Three changes:
  - `registers()` now applies condition (i), which the first run left out. It also takes the direction of the change
    into account (toward chance).
  - Undefined windows are counted per magnitude.
  - Part B adds every map scored on the 40 windows v1 explained with TimeSHAP.
  - The first run's tables are in the session scratch only; they are superseded.
- **Third profile.** ISU-ILCC is not run: it is parked by the V4 stop rule
  (`artifacts/v2/STOP_REPORT_third_profile_offsets.md`).

## What came out

**Part A: smallest registering magnitude** (`tables/degradation.json`; figures `<ds>_<weighting>_score_vs_degradation`).
"—" means not registered within the grid. The re-run with condition (i) gives the same magnitudes in every cell: each
registering magnitude was already at or above the resolved magnitude (`size_condition_only_magnitude` is reported
alongside).

| operator | rank agreement, MATR / HUST | channel allocation error | **temporal profile error** |
|---|---|---|---|
| added noise (× SD) | 0.05 / 0.2 | 0.1 / 0.1 | 0.5 / 0.5 |
| mass to start | 1.0 / 1.0 | — | **0.05 / 0.05** |
| **mass to end** | **1.0 / 1.0** (full shift only) | — | **0.1 / 0.1** (0.32 positions already at 0.05) |
| **smoothing σ** | **— / —** (change ≤ 0.004 at σ = 8) | — | **8 / 8** (1.38 / 1.35 positions at σ = 8) |
| permuted fraction | 0.2 / 0.2 | 0.1 / 0.1 | 0.2 / 0.2 |

Under uniform weighting, smoothing is registered by no score: the graded field is nearly flat along the window, which
was declared in advance as expected. Mass to end then registers for the temporal error at 0.05.

**Chance levels** (fully permuted map), recency, MATR / HUST:
- rank agreement 0.002 / 0.002;
- allocation error 0.632 / 0.464;
- temporal error 5.43 / 5.05 positions.

**Resolution alone is uninformative, as in v1.** The paired criterion resolves almost every operator at its smallest
magnitude for every score, even where the mean change is 1e-5 (allocation error under the shift operators). The
registers reading is what answers X5.

**X5 answer.**
- The temporal profile error registers end-loaded attributions at 10 % of the mass moved and blurred attributions at
  σ = 8 positions (recency).
- Rank agreement registers neither: only a complete shift to the end, and never smoothing.
- The channel allocation error registers what moves mass between channels (noise, permutation) and, by construction,
  nothing positional.
- The two new scores decompose what rank agreement conflates.

**Part B: the v1 maps rescored** (`tables/v1_maps_scores.json`), recency, unit means:

| profile | exact attribution of the reference model: rank / allocation / temporal | IG / occlusion / TimeSHAP on the v1 trained model: allocation | temporal [positions] |
|---|---|---|---|
| MATR | 0.815 / 0.164 / 0.70 | 0.613 / 0.644 / 0.639 | 3.70 / 3.42 / 4.00 |
| HUST | 0.870 / 0.131 / 0.29 | 0.689 / 0.672 / 0.674 | 2.70 / 2.87 / 3.39 |
| NASA PCoE (v1 only) | 0.733 / 0.171 / 1.20 | 0.626 / 0.641 / 0.623 | 4.04 / 3.62 / 3.76 |

- **The v1 trained-model maps were wrong mainly in channel allocation.** Every method put about two thirds of the
  attributed mass on the wrong channels (TV 0.61–0.69), because the v1 models read capacity only (v1 S6). Against
  that, the exact attribution's 0.13–0.18 is the noise term w·ε. The temporal errors (2.7–4.0 positions) add a
  positional error on top.
- The v1 rank agreement values are reproduced exactly (MATR 0.815 / 0.551 / 0.461 / 0.468), so the like-for-like v1/v2
  comparison at V8 rests on the same windows and maps.

**Part B on the 40 TimeSHAP windows** (`on_timeshap_windows`), recency. In v1, TimeSHAP was scored on 40 windows (D23)
and IG and occlusion on 120. Restricted to the same 40 windows:

| profile | exact (reference): rank / temporal, 120 → 40 windows | trained rank: IG / occlusion / TimeSHAP s0, on 40 | trained temporal: IG / occlusion / TimeSHAP s0, on 40 |
|---|---|---|---|
| MATR | 0.815 → 0.750; 0.70 → 0.82 | 0.489 / 0.434 / 0.468 (120: 0.551 / 0.461) | 3.83 / 3.78 / 4.00 (120: 3.70 / 3.42) |
| HUST | 0.870 → 0.859; 0.29 → 0.27 | 0.346 / 0.352 / 0.333 (120: 0.321 / 0.298) | 2.67 / 2.88 / 3.39 (120: 2.70 / 2.87) |
| NASA PCoE | 0.733 → 0.743; 1.20 → 1.09 | 0.329 / 0.263 / 0.286 (120: 0.316 / 0.283) | 3.94 / 3.54 / 3.76 (120: 4.04 / 3.62) |

- **The window set moves the scores by as much as the methods differ.** The exact map alone moves 0.065 in rank
  agreement on MATR.
- **v1's TimeSHAP comparisons mixed window sets.** On matched windows, MATR's TimeSHAP rank agreement sits between IG
  and occlusion (gap to IG 0.021, against 0.083 on mixed sets).
- **Still valid:** v1's IG–occlusion gap (0.090, MATR, the rationale of the 10 % threshold). Both methods ran on the
  same 120 windows.
- **Consequence for V8:** the full-scale run explains all 120 windows with every method, so the v2 comparison is
  like-for-like by design. The v1 Table 6 TimeSHAP comparisons are cited with this caveat.

## Checks

18 pass, 0 warnings (`logs/checks.md`):
- the undegraded ground truth scores perfect on every score, profile and weighting;
- on the v1 maps, IG on the reference model scores as the exact attribution on the temporal error, to ≤ 4e-6 (MATR,
  HUST, NASA PCoE).

## Anomalies

1. **A first Part B run scored the reference model's exact map on the window, not on its pattern-free counterpart.**
   This mattered only for NASA PCoE, the one profile with patterns. The check above caught it (4.7e-3 against the
   1e-3 bound). It was fixed and re-run; MATR and HUST were unaffected.
2. **Some channels are left out of the temporal profile error, but the score is defined in every window.**
   - A weighted channel is excluded from a window's average when its ϕ* mass or its attributed mass is zero, e.g. the
     capacity term at z = 0. These exclusions are counted (`temporal_excluded`, channel-windows), as declared.
   - Part A: 2 of 2 700 channel-windows (MATR), 0 (HUST).
   - Part B: 5 (MATR), 25 (HUST) and 0 (NASA PCoE) per 120-window map. TimeSHAP's 40-window maps have 4 and 6.
   - Windows where the score itself is undefined: 0 everywhere (`windows_undefined`).

## Decisions needed

None.
