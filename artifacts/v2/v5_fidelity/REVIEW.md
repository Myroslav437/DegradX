# V5 — RQ1, profile fidelity on the v2 profiles (X2 + X3), with the X1 ablation repeated

## What ran

- **Command.** `python scripts/v2/v5_fidelity.py --datasets MATR HUST`, seed 20260915, CUDA.
  - Started automatically when V1 ended (22:57) and finished overnight.
  - The GPU was shared with V6 until 23:59. That is allowed for training: the models are deterministic under their
    seeds.
- **Measured side.** The S3 split (identical in v2), cleaned with D12/D17/D27.
- **Generated side.** V4 generation seeds 0–2 (300 units each), plus the X3-off set (generation seed 0).
- **Measures.**
  - The discriminator per generation seed.
  - Covariance agreement per seed, with the measured fitting-vs-held-out baseline and its 95 % unit-bootstrap
    interval (10 000 percentile resamples).
  - TSTR with the X1 input sets on the v2 profile (3 × 5 TSTR and 5 TRTR trainings per set): full, capacity only,
    capacity / q₁, two-point state, centred.
  - The property table (V3 estimator) on the fitting split, the held-out split and the generated units.
  - Representation distance is not measured (D25).

## What came out

**Table 1 inputs** (`tables/fidelity.json`):

| | MATR | HUST |
|---|---|---|
| held-out units (reaching EOL); generated per seed | 40 (38); 300 | 23 (23); 300 |
| discriminative error, seeds 0 / 1 / 2 (mean) | 0.333 / 0.244 / 0.423 (0.333) | 0.373 / 0.460 / 0.623 (0.485) |
| covariance agreement, rel. Frobenius (mean); measured baseline [95 % unit-bootstrap] | 0.209; 0.174 [0.080, 0.442] | 0.054; 0.038 [0.017, 0.125] |
| X3 off (seed 0): discriminative error / covariance agreement | 0.355 / 0.207 | 0.410 / 0.059 |
| **transfer ratio** [95 % BCa]; range over the 15 seed pairs | **1.490 [1.042, 2.291]**; 1.23–2.14 | **1.174 [0.936, 1.342]**; 1.03–1.38 |
| RMSE TSTR / TRTR [cycles] | 219.2 / 147.1 | 242.2 / 206.4 |
| v1 transfer ratio; v1 discriminator mean; v1 covariance | 3.42; 0.072; 0.687 | 1.46; 0.164; 0.424 |

**Declared readings:**
- **X2(i), MATR's gap closed (MATR inside HUST's interval): no.** 1.49 > 1.342. See D29: HUST is the fidelity anchor;
  the generator is not iterated.
- **X3, covariance gap closed: yes, both profiles.** 0.209 ≤ 0.442 and 0.054 ≤ 0.125.
- **X3, discriminator gap narrows: yes, both profiles.** +0.26 and +0.32 against v1 seed half-ranges of 0.02 and 0.04.
  The cells themselves are void under D02b readability (anomaly 5); the reading is on the shift of the seed mean.
- **X3's own share, in the two declared measures: negligible.** The X3-off set, which keeps X2's offsets, reaches the
  same covariance (0.207 / 0.059) and discriminator (0.355 / 0.410). Those gains come from the per-unit offsets.
  Transfer was not run with X3 off.

**X1 on the v2 profiles** (`tstr_input_sets`, `x1_on_v2`):

| input set | MATR | HUST |
|---|---|---|
| all channels | 1.490 [1.042, 2.291] | 1.174 [0.936, 1.342] |
| capacity only | 0.979 [0.924, 1.083] | 1.037 [0.982, 1.127] |
| capacity / q₁ | 1.084 [0.946, 1.213] | 1.111 [0.919, 1.350] |
| two-point state | 1.084 [0.926, 1.253] | 1.118 [0.877, 1.375] |
| all, non-capacity centred per unit | 1.935 [1.405, 2.580] | 0.972 [0.853, 1.170] |

Readings:
- **MATR per-cell structure:** Δlog 0.42 [0.06, 0.90]. The interval lies above 0, but the reading does not survive the
  leave-one-seed-out rule, so it does not hold.
- **Offsets specifically:** MATR −0.26 [−0.59, 0.11]; HUST +0.19 [0.01, 0.36], which also fails the leave-one-out
  rule.
- **Initial spread:** null on both.

**Property table** (`tables/properties_<ds>.json`; fitting / held-out / generated). It was re-run on 2026-10-08 under
D30 (`scripts/v2/v5_properties.py`): generated series are now read with D13's record-end clause, as measured records
are. The first table is kept as `tables/properties_<ds>_run1.json`.
- **Units.** Every generated unit now enters the EOL-dependent rows: 300 of 300 on both profiles, against 222 (MATR)
  and 177 (HUST) in run 1. The noise, offset and correlation rows do not depend on EOL and are unchanged.
- **The trajectory side is reproduced, as in v1.**
  - MATR drift 25.6 / 25.6 / 23.9 mAh per 100 cycles; T 770 / 744 / 823.
  - HUST transition 0.69 / 0.65 / 0.68; T 1860 / 1938 / 1807.
- **The q₁ spread** (units reaching EOL) is 10.8 / 10.4 / 12.4 mAh for MATR and 21.2 / 19.6 / 26.9 mAh for HUST
  (run 1: 30.3). v1 generated about 1.8 and 1.4 mAh.
- **MATR charge-time noise variance** is 0.69 / **0.80** / 0.58 min², against 0.82 / **53.5** / 0.66 in v1. The
  held-out artefact is gone (D27).
- **MATR charge-time offset IQR** is 4.77 / 1.30 / 4.96 min. The held-out cells span fewer charging-policy groups than
  the fitting cells.
- **Within-unit residual correlation against the fitting split**, rel. Frobenius, held-out / generated: MATR 0.09 /
  0.11, HUST 0.03 / 0.03.
  - Split by pairs (mean |Δρ|, held-out / generated):
    - MATR capacity pairs 0.026 / **0.075**, other pairs 0.059 / 0.056;
    - HUST 0.023 / 0.029 and 0.012 / 0.013.
  - MATR's excess sits entirely in the capacity pairs. That is the estimator's errors-in-variables bias (anomaly 4).

## Checks

4 pass, 0 warnings:
- the discriminator does not separate trivially;
- the transfer ratio is finite, on both profiles.

## Anomalies

1. **Where X3 was isolated, the improvement is X2's.**
   - The v2 generator (X2 + X3) moved MATR's transfer from 3.42 to 1.49, its covariance distance from 0.69 to 0.21 and
     its discriminator from 0.07 to 0.33.
   - Turning the correlated noise off changes neither the covariance distance nor the discriminator by more than the
     seed spread. Those are the two measures declared for the X3-off set (`readings.X3_isolation`).
   - Transfer and the property table were not run with X3 off, so X3's share in those is not measured.
   - The within-unit correlation that X3 adds is real (V3), but it does not register in the two measures where X3 was
     isolated (corrected 2026-10-08: the first wording claimed every fidelity measure).
2. **Centring the non-capacity channels now hurts MATR's transfer** (1.94 against 1.49). In v1 it helped (2.04 against
   3.42). The generated offsets now resemble the measured ones closely enough that both sides lose information when
   they are removed.
3. **HUST's discriminator is at chance on average (0.485), but one seed reads 0.62.** Above 0.5 means the discriminator
   predicts the wrong class more than half the time, which is what the "coarse indicator" caveat of §3.5.1 covers.
4. **The X3 estimator is biased on the capacity pairs (errors in variables; v2 pipeline review).**
   - ρ̄ is estimated from residuals about φ_c(ẑ). ẑ is read from noisy capacity, so capacity noise enters every
     channel's residual with the slope of its mapping, and capacity-pair correlations are inflated.
   - The fitted ρ̄, the generator's target, carries this bias once. The estimator on generated data adds it again,
     which doubles the generated-vs-fitting distance in MATR's capacity pairs (above).
   - The generator is not changed (D29: no iteration). This is reported as a limitation of the X3 target, and it does
     not touch the non-capacity pairs.
5. **D02b readability of the discriminator was not applied in the first V5 run (DEVIATIONS T6).**
   - `scripts/v2/v5_discriminator_readability.py` re-ran the seeded discriminators with their predictions kept; they
     reproduce V5 exactly.
   - Unit bootstrap per seed, 10 000 resamples:
     - MATR 0.333 [0.187, 0.483], 0.244 [0.154, 0.359], 0.423 [0.281, 0.561];
     - HUST 0.373 [0.267, 0.482], 0.460 [0.381, 0.544], 0.623 [0.584, 0.663].
   - Only one seed per profile is readable, so **both Table 1 discriminator cells are void under D02b**
     (`tables/discriminator_readability.json`).
   - The values are reported with the void reason. The X3 reading "narrows" is a shift of the seed mean, not a
     readable level.

## Decisions needed

None. Taken: D29 (HUST is the fidelity anchor; no generator iteration) and D30 (record-end clause for generated series in
the property table; post-data).
