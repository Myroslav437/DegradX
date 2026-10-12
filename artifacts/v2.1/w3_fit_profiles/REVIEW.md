# W3 — refit of FORM under X2 and X3 (brief "DegradX v2.1", 2026-10-13)

## What ran

- **Command.** `scripts/v2/v3_fit_profiles.py --datasets TRI_FORMATION --out-dir artifacts/v2.1/w3_fit_profiles`, CPU,
  40 s.
- **Code.** This is the v2 V3 code unchanged. `_common.py` maps the dataset to the v2.1 roots.
- **What it fits.**
  - X2: backfitted per-unit offsets, with each unit's own q₁ in the capacity mapping.
  - X3: within-unit residual correlation at the pooled φ.
  - D27: the channel rule.

## Results

- **The fit reproduces W2 exactly** (D05 governance):
  - the same split (127 fitting, 55 held out);
  - the same family (two-term exponential);
  - D05 positive enabled, ratio 2.285, 312 runs; negative not enabled, ratio 0.958.
- **Channels.** Capacity, charge time and mean discharge voltage, all weighted. Temperature and IR are not available, so
  there are no redundant channels.
- **Reference point x₀.** 0.2459 Ah, 72.03 min, 3.738 V.
- **Mappings.**
  - Charge time decreases by 2.91 min from z = 0 to z = 1.
  - Mean discharge voltage decreases by 41.7 mV.
  - The backfit converged in 4 and 5 iterations.
- **Noise** (variance, lag-1 φ):

  | channel | variance | φ |
  |---|---|---|
  | capacity | 1.43e-6 Ah² | 0.95 |
  | charge time | 0.765 min² | 0.95 |
  | mean discharge voltage | 5.06e-5 V² | 0.975 |

- **Within-unit residual correlation (X3).**
  - Charge time against mean discharge voltage is **−0.89**. In v2 no MATR or HUST pair came close.
  - Capacity against the other two is about ±0.12.
  - The innovation matrix is positive definite, so no repair was needed.
- **θ.** Taken from 127 fitting units reaching EOL. 11.8 % of units have a parameter at a bound.

## Checks

All pass (`logs/checks_TRI_FORMATION.md`):
- the E1–E7 split of keys;
- capacity affine in z (error 4e-17);
- monotone mappings;
- backfit convergence;
- median offsets of 0;
- residuals centred in 100 % of units;
- θ not collapsing to the bounds.

## Next

W4: generation.
