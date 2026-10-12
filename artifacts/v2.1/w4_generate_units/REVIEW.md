# W4 — generated units of FORM (brief "DegradX v2.1", 2026-10-13)

## What ran

- **Command.** `scripts/v2/v4_generate_units.py --datasets TRI_FORMATION --out-dir artifacts/v2.1/w4_generate_units`,
  CPU, 95 s.
- **Code.** The v2 V4 code. Its caches are routed to `data/v2.1/generated/TRI_FORMATION/` (gitignored, reproducible from
  the seeds).
- **Sets.** Three generation seeds × 300 units, plus a seed-0 set with X3 switched off.
- **Inserted patterns.** FORM is the first v2 profile whose generator inserts patterns: the positive type, enabled by D05
  at W2 and reproduced at W3.

## Results

| generation seed | units | T median | units with patterns | patterns | offset share, recency (uniform) | Var(pattern term) / Var(state term), recency (uniform) | graded/sparse \|r\|, recency (uniform) |
|---|---|---|---|---|---|---|---|
| 0 | 300 | 680 | 216 | 741 | 0.131 (0.137) | 2.4e-5 (1.8e-5) | 0.032 (0.006) |
| 1 | 300 | 713 | 213 | 803 | 0.115 (0.120) | 2.3e-5 (1.7e-5) | 0.030 (0.010) |
| 2 | 300 | 745 | 214 | 743 | 0.129 (0.135) | 2.0e-5 (1.5e-5) | 0.038 (0.001) |

- **Patterns.** They are generated at the fitted rate and amplitude, with no inflation (D21). Positive type: amplitude
  median 2.7 mAh (5–95 %: 1.3–6.0 mAh), duration median 4 positions, the per-unit rate of the resampled source unit.
- **The pattern term is negligible in the target at fitted amplitudes.** Its variance is about 2e-5 of the state term's,
  three orders of magnitude below the band of 0.05–0.50 that the usability check reads. This is the situation NASA PCoE
  met in v1 (D21). Whether a trained model learns the pattern term is read at W6 (term ablation; r4
  `readings.sparse_set_trained`).
- **Offset share.** At most 0.137, far below the stop at 0.5. The W2 measured pre-screen read 0.120 / 0.125.
- **Weights.** κ: capacity −6.18 /Ah, charge time −0.115 /min, mean discharge voltage −8.00 /V. Null channels 0.
- **X3 isolation.** The X3-off set (seed 0) has a generated within-unit correlation of about 0, against −0.86 with X3 on.

## Checks

All construction checks pass in every seed and weighting:
- Σφ* = y (at most 4.4e-16 relative);
- g(x) − y = Σwε (1.5e-15);
- mean over units of g − y ≈ 0;
- y = 0 at z = 0 with zero offsets;
- E[ε] = 0 per channel;
- z starts pristine and T is the first crossing;
- **disabling patterns leaves z, T, R, the mean and the noise unchanged.**

**X3 construction.** The within-unit correlation of the generated noise, averaged over seeds, lies within 0.032 of the
fitted value (limit 0.05). Of that, 0.024 is the gap implied by the pooled-φ construction itself.

Two reported warnings (severity warn, as declared):
- **q₁ spread.** The generated q₁ IQR is 3.2–3.7 mAh against 2.6 mAh for the fitting units reaching EOL, more than the
  20 % margin. It is reported in the W5 property table.
- **Estimator check.** The V3 estimator re-run on generated observations recovers the within-unit correlation within
  0.156 for capacity pairs and 0.094 for the other pairs, against 0.05. This is reported. A likely contributor is the
  inserted patterns on capacity: the estimator masks detected runs, while generated runs straddle the masking thresholds
  differently.

## Next

W5: fidelity (TSTR with the five X1 input sets, discriminator with D02b readability, covariance agreement, property table).
