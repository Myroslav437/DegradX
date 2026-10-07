# V6 — RQ2, usability and identifiability on the v2 profiles (X2, X3, X4)

## What ran

- **Command.** `python scripts/v2/v6_usability.py --datasets MATR HUST`, seed 20260915, CUDA, 22:30–23:59 (89 min).
  The GPU was shared first with V1 and then with V5. This is allowed for training: the models are deterministic under
  their seeds.
- **Data.** V4 generation seed 0 with its declared split, 210 / 45 / 45 units. Training plus validation windows:
  212 884 (MATR) and 477 109 (HUST). Test windows: 36 554 and 85 660.
- **Models.** For recency and uniform weighting (D25), ten members each: configuration A (64 × 2) and B (128 × 1) ×
  model seeds 0–4. Saved to `models/<profile>_<weighting>_<A|B>_seed<s>.pt` (LFS); V8 attributes them.
- **Measurements, as r2 declares them:**
  - the accuracy gate;
  - the null-channel leakage gate;
  - redundant channels (reported, not gated);
  - term ablation (void: no profile enables patterns).
- **New in v2:**
  - X4 channel-usage gate: ridge conditional resampling of each weighted channel on every member, BCa over test units
    with 10 000 resamples;
  - the offset term of y (X2) on the test windows.

## What came out (`tables/usability_<ds>.json`)

| | MATR recency (uniform) | HUST recency (uniform) | v1, recency (MATR / HUST) |
|---|---|---|---|
| primary NRMSE; members passing ≤ 0.30 | 0.091 (0.090); 10/10 (10/10); members 0.088–0.098 | 0.095 (0.095); 10/10 (10/10); 0.089–0.097 | 0.036 / 0.012 |
| offset term, share of Var(y) | 0.128 (0.134) | 0.343 (0.344) | — (no offsets) |
| Spearman(y, RUL) | −0.71 | −0.61 | −0.74 / −0.91 |
| permutation importance: capacity / charge time / mean discharge V | 0.908 / **0.256** / **0.085** | 0.525 / **0.049** / **0.808** | 2.00 / 0.0009 / 0.0003; 1.98 / 0.0002 / 0.0000 |
| **X4 conditional importance** (primary), capacity | 0.076 [0.066, 0.093] | 0.069 [0.057, 0.084] | not measured |
| **X4**, charge time | 0.053 [0.037, 0.092] | 0.015 [0.012, 0.018] | |
| **X4**, mean discharge V | 0.049 [0.038, 0.079] | 0.631 [0.545, 0.744] | |
| weighted channels used (lower bound > 0): primary; members using all three | all three; 10/10 | all three; 10/10 | |
| used materially (lower bound > 0.02) | all three | capacity, mean discharge V (charge time 0.012) | |
| leakage, null channels (upper bound) | ≤ 0.0001 | ≤ 0.0000 | ≤ 0.004 |
| redundant channels: R² from the others, conditional importance | IR 0.75, 0.0026; temperature 0.47, 0.0043 | none | IR 0.55, 0.0000 |
| pattern term (variance ratio, ablation, graded/sparse correlation) | void: no inserted patterns (D05) | void | void |

## Readings (declared)

- **X2(ii), are the weighted channels non-redundant for a trained model: yes, on both profiles.**
  - Every weighted channel passes the X4 rule on the primary model and on all ten members, under both weightings.
  - In v1 the models read capacity alone: charge time and mean discharge V had permutation importance ≤ 0.001.
  - Now charge time carries 0.26 of the error (MATR), and mean discharge voltage carries 0.81 (HUST), more than
    capacity.
  - The per-unit offsets are what makes these channels informative. An offset changes y through the channel's
    weight, and no other channel predicts it.
- **No channel-level score is void (X4)** on either profile or weighting.
- **Stop rules (brief §6): none triggered.** The accuracy gate and the leakage test pass on every profile and
  weighting after X2/X3.

## Checks

28 pass, 0 warnings, 0 failures (`logs/checks.md`):
- the primary model passes the gate;
- all ten members pass;
- both null channels are within the leakage tolerance;
- every weighted channel is used by the primary model;
under each profile and weighting.

## Anomalies

1. **The accuracy is lower than in v1** (NRMSE 0.09 against 0.01–0.04), though every member passes with a large
   margin. The target now carries the offsets, and the models must read three noisy channels instead of one clean one.
   The noise term Σwε is also larger: the non-capacity channels carry real weight and real noise.
2. **HUST's mean discharge voltage dominates the model's use** (0.81 against capacity's 0.53).
   - HUST's offsets carry a third of Var(y), and most of it through mean discharge voltage, whose offsets are large
     relative to its degradation range.
   - Charge time is used, but only at 0.015 [0.012, 0.018], below the materiality reading.
3. **The association of y with RUL weakens** (HUST −0.91 → −0.61), as the offset term, unrelated to remaining life,
   enters y. That is the cost of X2 the stop rule bounds.

## Decisions needed

None.
