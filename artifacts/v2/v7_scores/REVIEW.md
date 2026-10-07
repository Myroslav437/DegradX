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
    - *registers*: a mean change of at least 10 % of the chance-to-perfect distance at some magnitude and at every
      larger one.
- **Part B.** The same scores on the saved v1 S8 maps (`data/attributions`) against the v1 ground truth regenerated from
  `data/generated`, for MATR, HUST and (v1 only) NASA PCoE, under recency and uniform weighting. No new attribution.
- **Third profile.** ISU-ILCC is not run: it is parked by the V4 stop rule
  (`artifacts/v2/STOP_REPORT_third_profile_offsets.md`).

## What came out

**Part A: smallest registering magnitude** (`tables/degradation.json`; figures `<ds>_<weighting>_score_vs_degradation`).
"—" means not registered within the grid.

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

## Checks

18 pass, 0 warnings (`logs/checks.md`):
- the undegraded ground truth scores perfect on every score, profile and weighting;
- on the v1 maps, IG on the reference model scores as the exact attribution on the temporal error, to ≤ 4e-6 (MATR,
  HUST, NASA PCoE).

## Anomalies

1. **A first Part B run scored the reference model's exact map on the window, not on its pattern-free counterpart.**
   This mattered only for NASA PCoE, the one profile with patterns. The check above caught it (4.7e-3 against the
   1e-3 bound). It was fixed and re-run; MATR and HUST were unaffected.
2. **The temporal profile error is undefined in about 5 of 120 windows per profile** (a weighted channel with zero ϕ*
   mass: windows at z = 0 where the capacity term vanishes). These are counted (`temporal_excluded`), as declared.

## Decisions needed

None.
