# Stage 6 — RQ2, usability of the attribution ground truth (paper §3.5.2; Table 3)

## What ran

- Commands:
  - `python scripts/s6_usability.py --datasets MATR HUST`: 143 min on CUDA.
  - `python scripts/s6_usability.py --datasets NASA_PCoE`: 3.5 min.
  - Seed 20260915 for both.
- Data: S4 generation seed 0, 300 units per profile, generated split 210 / 45 / 45 units. Windows of L = 24 over every end position.
  - Train + validation windows: MATR 212 884, HUST 477 109, NASA 11 606.
  - Test windows: 36 554, 85 660, 2 602.
- Models: the LSTM of `configs/models/lstm.yaml` trained on y for each position weighting (recency, uniform, final position).
  - Configuration A (64×2) with model seeds 0–4.
  - Configuration B (128×1) with model seeds 0–4.
  - This gives 10 members per profile × weighting, 90 in total, saved to `models/`.
  - A seed 0 is the primary model that S8 attributes.
- Measurements (declarations `usability`):
  - accuracy gate (NRMSE ≤ 0.30);
  - permutation importance of every channel, with the leakage bound ≤ 0.02 on the null channels;
  - for redundant channels, ridge R² from the other channels and conditional permutation importance (C2);
  - term ablations: retraining on y without the mean term, and without the pattern term;
  - variance ratio of the two terms, the graded/sparse correlation, and Spearman(y, RUL).
- Intervals: BCa over test units.
- Decision harness: D21, pattern amplitude multipliers ×1–×16 on NASA.

## What came out

| figure | what to look for |
|---|---|
| `<ds>_<weighting>_training_curves` | Train/validation MSE per ensemble member; early stopping, no divergence. |
| `<ds>_<weighting>_predicted_vs_true` | Primary model on test windows; points on the diagonal over the whole range of y. |
| `<ds>_<weighting>_permutation_importance` | Capacity dominates; null channels at zero; redundant channels small. |

**Table 3 (`tables/usability_<ds>.json`), recency weighting:**

| quantity | bound | MATR | HUST | NASA PCoE |
|---|---|---|---|---|
| primary NRMSE (members passing) | ≤ 0.30 | 0.036 (10/10) | 0.012 (10/10) | 0.131 (10/10) |
| Spearman(y, RUL) | reported | −0.74 | −0.91 | −0.53 |
| permutation importance, capacity | — | 2.00 | 1.98 | 1.87 |
| permutation importance, charge time / mean discharge V | — | 0.0009 / 0.0003 | 0.0002 / 0.0000 | 0.0095 / 0.0023 |
| permutation importance, null flat / permuted (upper bound) | ≤ 0.02 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0041 / 0.0026 |
| redundant channels: R², conditional importance | reported | IR 0.55, 0.0000; temp. 0.11 | none | temp. 0.13, 0.0062 [0.0032, 0.0104] |
| variance ratio pattern/mean | 0.05–0.50 | void (no patterns, D05) | void | **0.0004** |
| graded/sparse correlation | ≤ 0.30 | void | void | 0.074 |
| error change, mean term removed | > 0 | void | void | 10.3 [9.43, 10.9] |
| error change, pattern term removed | > 0 | void | void | **−0.0000 [−0.0004, 0.0003]** |

Other weightings:
- NRMSE: MATR 0.037 / 0.037, HUST 0.013 / 0.013, NASA 0.125 / 0.248 (uniform / final position).
- NASA pattern-term ablation: uniform −0.0005 [−0.0011, 0.0000], final position −0.0030 [−0.0065, −0.0006].
- NASA variance ratio: 0.0003 (uniform), 0.0024 (final position).

## Checks

- MATR and HUST: 24 pass, 0 warnings (`tables/checks_MATR_HUST.*`).
- NASA: 18 pass, 6 warnings (`logs/checks.md`). The 6 warnings are the pattern-term ablation and the variance ratio under all three weightings; Anomaly 1 explains them.
- The accuracy gate and the leakage bound are recorded at warning severity. A failing gate voids the downstream scores (void convention, §3.5.2) rather than stopping the stage. A failed leakage bound would require correcting the profile, and it passed everywhere.

## Anomalies

1. **NASA PCoE pattern term is not learned (D21).** At the fitted amplitudes (median 40 mAh, 6 fitting-split events) the pattern term carries 0.04 % of the variance of the mean term. Retraining without it leaves the error unchanged.
   - D21 harness: the ablation becomes significant at ×4; the declared band is reached at ×16.
   - The generator keeps the fitted amplitudes, and sparse-set scores on trained models are void.
   - The variance-ratio band fails in the only profile where it applies. It is reported as failed, not relaxed.
2. **Every model reads capacity almost exclusively.**
   - Capacity importance is 1.7–2.0. Charge time and mean discharge voltage carry two thirds of the target weights, yet their importance is at most 0.032 (NASA, final position).
   - This is the non-identifiability of C2: all channels are functions of one degradation state, so a capacity-only function reproduces y.
   - It is why the reference model is the primary scoring target, and why the S8 trained-model rank agreement is bounded by the ensemble spread.
3. **NASA temperature carries information the other channels do not.** Its conditional importance is 0.0062 [0.0032, 0.0104]: small but positive. The bound for redundant channels is "reported", not a gate (C2), so this is recorded, not corrected.
4. **Final-position NRMSE on NASA is 0.248,** close to the gate. All 10 members pass.

## Decisions needed

None for a human. Taken: D21 (keep the fitted amplitudes; trained-model sparse-set scores void).
