# V3 — refit the generator with per-unit offsets (X2) and the residual correlation for correlated noise (X3)

## What ran

- **Command.** `python scripts/v2/v3_fit_profiles.py --device cpu --workers 8`, seed 20260915, about 1 min per run.
  It was re-run once after a figure-label fix; the profiles came out byte-identical (SHA-256).
- **Rules.** Declarations r3, `v2.per_unit_offsets` and `v2.correlated_noise`. The channel glitch rule is D27 (runs of
  up to three readings).
- **Split.** The same seeded measured split as v1, checked identical to the v1 S3 split tables for MATR and HUST.
- **Timing.** V3 ran while V1 (X1) was still training on the GPU. r3 declares that X2 and X3 are built whatever X1
  shows (`v2.tstr_isolation.action`), so the order of the two runs changes nothing.

## What came out

| figure | what to look for |
|---|---|
| `<ds>_offsets_mappings` | Measured (z, x) of six units spanning T, with each unit's φ(z) + δᵢ. The dashed curve is the r2 shared mapping; the solid curve is the backfitted mapping (median unit). Histograms of δ on the right. |
| `<ds>_residual_before_after` | Variance ratio and lag-1 of the per-unit-centred AR(1) residual, before and after the offsets. |
| `<ds>_correlation_before_after` | Pooled residual correlation with the r2 residuals and after the offsets. |
| `<ds>_family_cv_errors`, `<ds>_detection_sweep` | As in S3. Unchanged: the capacity cleaning is unchanged. |

**Backfitting.** It converges in 4–6 iterations on every channel, against a declared cap of 200, with a tolerance of
1e-4 of each mapping's range. Every unit has enough readings, so no δ is forced to 0.

**What the offsets absorb (fitting split).** The between-unit columns are the variance of the per-unit residual means.

| channel | between-unit, before → after | globally centred, before → after | within-unit AR(1) variance, before → after (lag-1) | Var(δ), noise-corrected |
|---|---|---|---|---|
| MATR charge time [min²] | 7.08 → 0.047 | 8.69 → 0.73 | 0.81 → 0.69 (0.91 → 0.89) | 7.04 |
| MATR mean discharge V [V²] | 2.81e-3 → 2.5e-5 | 4.05e-3 → 4.4e-4 | 5.4e-4 → 4.1e-4 (0.97 → 0.96) | 2.87e-3 |
| MATR IR [Ω²] | 1.37e-6 → 8.7e-9 | 1.22e-6 → 8.9e-8 | 9.0e-8 → 8.1e-8 (0.96 → 0.96) | 1.0e-6 |
| MATR temperature [°C²] | 2.77 → 0.045 | 3.36 → 0.53 | 0.49 → 0.49 (0.94 → 0.93) | 2.90 |
| HUST charge time [min²] | 1.71 → 0.13 | 3.20 → 1.51 | 1.40 → 1.39 (0.99 → 0.99) | 0.91 |
| HUST mean discharge V [V²] | 1.16e-3 → 1.9e-6 | 1.10e-3 → 2.7e-5 | 2.8e-5 → 2.5e-5 (0.98 → 0.98) | 1.13e-3 |

**Correlation of the residuals** (the X3 target is the within-unit ρ̄):

| MATR pair | pooled, r2 residuals | pooled, after offsets | within-unit ρ̄ (X3 target) |
|---|---|---|---|
| charge time–mean discharge V | −0.78 | −0.55 | −0.66 |
| charge time–IR | +0.81 | +0.55 | +0.62 |
| mean discharge V–IR | −0.69 | −0.56 | −0.65 |
| IR–temperature | −0.54 | −0.31 | −0.43 |

For HUST, charge time–mean discharge V moves from +0.11 (r2) to −0.21 (pooled after offsets), with ρ̄ = −0.30.

Mappings and reference point:
- MATR's charge-time offsets are bimodal (around −5 min and around 0), the charging-policy groups.
- The backfitted mapping follows the median cell. φ_CT(0) is 30.74 min against 29.34 in r2, because r2's shared fit
  was pulled toward the −5 min group.
- x⁰ moves accordingly: the reference point is the median unit's pristine level.

## Checks

32 pass, 0 warnings (`tables/checks.csv`, `logs/checks.md`):
- E1–E7 split;
- capacity affine per unit with the unit's own q₁ (≤ 1.1e-16 Ah);
- every backfitted φ monotone;
- backfit converged on every channel;
- median offset exactly 0;
- residuals centred;
- θ at bounds ≤ 2.2 %;
- families unchanged from v1 (MATR two-term exponential, HUST rollover);
- splits identical to v1.

## Anomalies

1. **S3 anomaly 4 in v1 was half right.**
   - v1's AR(1) estimator centres every unit, so constant per-cell offsets never entered its noise variance. They were
     simply absent from the v1 generator, which had no between-cell spread in any non-capacity channel.
   - With offsets, the within-unit AR(1) variance barely moves (MATR charge time 0.81 → 0.69) and the lag-1 stays at
     0.89–0.99.
   - **The slow component is within-unit, not an offset.** The offsets absorb the between-unit level differences:
     MATR charge-time between-unit variance 7.08 → 0.05.
2. **Within-unit cross-channel correlations remain large in MATR after the offsets** (ρ̄ up to |0.66|). v1 generated
   none of it; X3 generates it.
3. **HUST charge-time offsets carry real sampling noise.** With lag-1 0.993, a unit median is a noisy level estimate:
   the noise term is 0.64 of Var(δ) = 1.55 min². No shrinkage is applied, as declared, so generated HUST units carry
   slightly more between-unit charge-time spread than measured (V4/V5 report it).

## Decisions needed

None. The pre-data decisions are D25 and r3; the post-data decision is D27.

## Addendum — third profile (ISU-ILCC), run 2026-10-07 after its V2 audit

- **Run.** `python scripts/v2/v3_fit_profiles.py --datasets ISU_ILCC --profile-config ISU_ILCC=isu_ilcc`. The checks
  are in `logs/checks_ISU_ILCC.md` (all pass) and the run record in `logs/run_ISU_ILCC.json`. `tables/summary.json`
  merges all three profiles.
- **Fit.**
  - Family: power law. 102 fitting units, all reaching EOL; θ at a bound in 2 %.
  - Backfit converges in 7–8 iterations.
  - Patterns are not enabled (positive ratio 1.66, the V2 audit's value).
- **Offsets.** They absorb the test condition: charge-time between-unit variance 376.7 → 2.3 min²; mean discharge V
  4.5e-3 → 4.2e-6 V². The within-unit AR(1) charge-time variance halves (21.9 → 11.9 min²).
- **Within-unit correlation (ρ̄).** Small: capacity–mean discharge V −0.17; others |ρ̄| ≤ 0.04.
- **Consequence.** V4 measures an offset share of Var(y) of 0.76–0.82, above the stop level. See
  `artifacts/v2/STOP_REPORT_third_profile_offsets.md`.
