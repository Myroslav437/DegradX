# Stage 3 — Profile fitting (paper §3.3, six steps)

## What ran

- Command: `python scripts/s3_fit_profiles.py --workers 12` (seed 20260915), CPU, 58 s wall clock (`logs/timing.json`).
- Declarations: r2 plus the dated D02, D04 (margin declared in a commit before S3; identifiability clause added after the first run), D05, D11–D17.
- Decision harnesses run during this stage, under `experiments/decisions/`: D02, D04, D05, D17.

Every profile is written to `profiles/<dataset>.json`:
- `estimated_from_data` holds E1–E7 only;
- `declared_used` lists the declared constants the fit consumed;
- `derived` holds the channel roles after the weight guard, the reference point x⁰ = φ_c(0), and the capacity affinity check.

## What came out

Per dataset `<ds>` ∈ {matr, hust, nasa_pcoe}, in `figures/`:

| figure | what to look for |
|---|---|
| `<ds>_capacity_eol_sheet` | Six units spanning the range of T: raw vs Savitzky–Golay capacity, t₁, EOL, and whether EOL came from the record-end rule (D13). |
| `<ds>_family_fits` | All three families on the same three units with residuals; the selected family in bold. |
| `<ds>_family_cv_errors` | Per-unit CV-RMSE per family (log scale) with the selected family in the title. |
| `<ds>_theta_distributions` | Per-unit parameters of the selected family, and q₁. |
| `<ds>_channel_mappings` | Isotonic + PCHIP φ_c over a subsample of measured (z, x_c). The MATR charge-time band structure is per-cell charging policy; the mapping passes through its middle. |
| `<ds>_residual_acf` | Median ACF of residuals per channel against the fitted AR(1). |
| `<ds>_pattern_traces` | Capacity residuals with ±k·s and detected runs (NASA B0006 shows the regeneration sawtooth). |
| `<ds>_detection_sweep` | Measured event rates vs k, with the noise-only rate and the 2× enable threshold at the declared k. |
| `<ds>_length_distribution` | T of the fitting units reaching EOL. |

Profiles:

| | MATR (135 cells) | HUST (77) | NASA PCoE (18 pass the guard) |
|---|---|---|---|
| split: fitting reach / censored; held-out reach / censored | 90 / 5; 38 / 2 | 54 / 0; 23 / 0 | 8 / 5; 3 / 2 |
| family (D04) | two-term exponential | rollover | power law |
| median CV-RMSE, fraction of q₁ (power / exp2 / rollover) | 0.0129 / **0.0061** / 0.0067 | 0.0100 / 0.0084 / **0.0027** | **0.0111** / 0.0113 / 0.0105 (rollover and exp2 not identifiable: 75 % and 88 % of units at a bound) |
| channels (availability rule) | capacity, charge time, mean discharge V, IR, temperature | capacity, charge time, mean discharge V | capacity, charge time, mean discharge V, temperature |
| weighted after guard / zero-weight redundant | cap, CT, MDV / IR, T | cap, CT, MDV / — | cap, CT, MDV / T |
| x⁰: capacity φ(0) = q̄₁ [Ah] (φ(1) = ρ·q_nom) | 1.0747 (0.88) | 1.1922 (0.88) | 1.8182 (1.60) |
| charge time φ(0) → φ(1) [min] | 29.34 → 21.00 | 34.40 → 21.53 | 166.45 → 158.55 |
| mean discharge V φ(0) → φ(1) [V] | 2.783 → 2.586 | 3.101 → 3.042 | 3.487 → 3.468 |
| capacity noise variance [Ah²] / AR(1) φ | 2.82e-6 / 0.942 | 1.10e-6 / 0.941 | 2.46e-4 / 0.508 |
| charge-time noise variance [min²] / φ | 0.816 / 0.906 | 1.40 / 0.993 | 47.2 / 0.509 |
| strongest residual cross-channel correlation | CT–IR +0.81, CT–MDV −0.78 | CT–MDV +0.11 | CT–T −0.63 |
| positive patterns: events (units) / measured vs noise-only rate per 100 / enabled | 97 (55) / 0.122 vs 0.144 (0.85×) / **no** | 59 (38) / 0.058 vs 0.122 (0.47×) / **no** | 6 (5) / 0.876 vs 0.128 (6.83×) / **yes**, median amplitude +40.2 mAh |
| negative patterns: events / ratio / enabled | 86 / 0.78× / no | 128 / 0.98× / no | 1 / 1.14× / no |
| T of fitting units: n, median [IQR] | 90, 770.5 [509, 997] | 54, 1860.5 [1656, 2162] | 8, 61.5 [31.8, 76.8] |

## Checks

31 pass, 0 warnings (`tables/checks.csv`, `logs/checks.md`):
- the estimated/declared split holds exactly E1–E7;
- capacity mapping affine in z per unit (max error ≤ 2.9e-16 Ah);
- every isotonic φ_c monotone on [0, 1];
- residuals centred (|mean| ≤ 0.5 s) in 100 % of units;
- θ units at a bound: MATR 2 %, HUST 0 %, NASA 12 % (after D04);
- θ from ≥ 5 units;
- D05 evaluated for both types.

**Regression fixed during the stage.** The at-bound tolerance was `1e-6·|hi − lo|`, which is infinite for one-sided bounds, so every rollover unit was flagged. It now scales by the parameter value on unbounded sides (`tests/test_state_patterns_families.py::test_at_bound_not_flagged_for_interior_parameters_with_infinite_bounds`).

## Anomalies

1. **MATR and HUST residual runs are what their noise produces** (D05). At the declared k they are detected at 0.85× and 0.47× the rate of AR(1) noise with the fitted variance and φ, so neither profile enables inserted patterns. Consequence: **sparse-set measurements exist only on the NASA PCoE profile.**
2. **NASA regeneration rests on 6 fitting-split events from 5 units.**
   - This is below the D02 minimum of 10 for reporting pattern statistics, so its measured-vs-generated regeneration rows are void.
   - Generation still uses the 6 events (D02: minimum counts gate reporting, not generation).
   - The held-out split holds 3 units reaching EOL, below the provisional held-out minimum of 5; S5 tests the alternatives.
3. **Rollover is not identifiable on NASA's short records.** δ sits at its 5-cycle lower bound in 6 of 8 units, and EOL reproduction p90 is 26 %. D04 selects the power law (p90 9.6 %, 5.7 % higher CV error). NASA profiles therefore have no knee.
4. **Channel residuals in MATR and HUST are strongly autocorrelated** (φ 0.91–0.99). The shared mapping φ_c(z) cannot represent per-cell charging-policy offsets, so they end up as slow AR(1) noise. The MATR residual correlations CT–IR +0.81 and CT–MDV −0.78 have the same origin. Generation adds noise independently per channel (declared), so S5's cross-channel covariance comparison is expected to show the mismatch.
5. **NASA charge time stays a weighted channel by a narrow margin**: |φ(1) − φ(0)| = 7.9 min against a noise SD of 6.9 min under D17. Without the channel glitch rule it would be demoted.

## Decisions needed

None for a human. Taken:
- D02: censored scope and minimum counts;
- D04: 5 % margin and identifiability;
- D05: noise-calibrated enable rule;
- D17: channel glitch rule.

The paper amendments are round 3 (`artifacts/amendments/latexdiff_round3.pdf`). Carried to S4: D06 (graded/sparse correlation, NASA only) and D01 (sparse retrieval, NASA only).
