# V4 — generate units from the v2 profiles (X2 offsets, X3 correlated noise)

## What ran

- **Command.** `python scripts/v2/v4_generate_units.py --device cpu --workers 8`, seed 20260915, CPU.
- **Units.** 300 units per profile for each generation seed 0, 1 and 2, split 0.7 / 0.15 / 0.15 at unit level (S4
  rule). Cached in `data/v2/generated/<profile>/seed<g>.pkl` (gitignored; regenerates bit-identically from the seeds).
- **X3-off set.** One extra set per profile, `seed0_x3off.pkl`: the v2 profile with independent per-channel noise.
  It isolates X3's own share at V5 (declared reading `X3_isolation`).
- **Weightings.** Recency and uniform (D25).
- **Re-runs.** Both re-ran the checks on the cached units; generation was not repeated.
  - **Second run.** The q₁-spread comparator is now the fitting units reaching EOL, as declared. It had used all
    guard-passing units.
  - **Third run, 2026-10-08, after the v2 pipeline review.**
    - The estimator check is now like with like: the within-unit estimator against the fitted ρ̄, and E4 against
      E4. It had compared E4 on generated data with ρ̄.
    - It reads generated series with D13's record-end clause (D30).
    - A cached re-run now keeps the X3-off set's summary entry.

## What came out

| | MATR seed 0 / 1 / 2 | HUST seed 0 / 1 / 2 |
|---|---|---|
| T median [IQR] | 823 [535, 1039] / 748 [506, 985] / 727 [515, 1020] | 1807 [1585, 2221] / 1903 [1602, 2178] / 1881 [1680, 2063] |
| offset share Var(y_offset) / Var(y), recency (uniform) | 0.111 (0.116) / 0.112 (0.117) / 0.104 (0.109) | 0.319 (0.320) / 0.344 (0.345) / 0.312 (0.313) |
| Var(y_offset) / Var(y_state), recency | 0.120 / 0.120 / 0.114 | 0.493 / 0.550 / 0.474 |
| corr(y_offset, y_state) | −0.03 to −0.07 | 0.03 to 0.04 |
| generated q₁ IQR (measured units reaching EOL) | 12.4 / 10.0 / 10.6 mAh (10.8) | 26.9 / 27.0 / 27.1 mAh (21.2) |
| innovation correlation repaired (X3) | no | no |

The offset contribution stays below the declared stop level of 0.5 everywhere. In HUST, the generated targets encode
cell identity to a third of their variance.

**X3 construction.**

| | MATR | HUST |
|---|---|---|
| within-unit correlation of the generated noise vs fitted ρ̄ (max \|Δ\|, mean over seeds) | **0.087** (> 0.05) | 0.008 |
| pooled comparison | 0.080 | 0.033 |
| gap implied by the pooled-φ construction, averaged over θ units | 0.127 | 0.014 |
| estimator check: V3 within-unit estimator on generated observations vs fitted ρ̄ (generation seed 0) | **0.106** | 0.035 |
| same, capacity pairs / other pairs | 0.106 / 0.090 | 0.035 / 0.013 |
| E4 (pooled) on generated observations vs fitted E4 | 0.089 | 0.032 |

## Checks

95 pass, 5 warnings, 0 failures (`tables/checks.csv`, `logs/checks.md`). On every window of every unit, seed and
weighting:
- Σϕ* = y, to 0 relative error;
- g(x) − y = Σ w ε, to ≤ 6e-16;
- mean over units of g(x) − y is within 3 SE;
- a unit at z = 0 with zero offsets, no patterns and no noise has y = 0;
- E[ε] = 0 per channel;
- z starts at the pristine level and T is the first crossing;
- disabling patterns leaves z, T, R, the mean and the noise unchanged.

The 5 warnings are all declared readings, not construction errors:

1. **MATR X3 construction, 0.087 > 0.05.** This is the declared consequence of one innovation matrix at the pooled φ.
   MATR's per-unit lag-1 coefficients are spread out, so units away from the pooled φ generate a different stationary
   correlation. The gap implied by construction (0.127) explains the observed one. As declared, this is reported, not
   a stop case; V5's covariance agreement shows the consequence.
2. **MATR estimator check, 0.106. HUST passes at 0.035.**
   - **What the check does.** It refits the whole V3 estimator (mapping, offsets, AR(1)) on generated observations, so
     it compounds the construction gap with estimation error.
   - **Earlier values.** The first two runs read 0.168 / 0.068, because they compared E4 with ρ̄ rather than like with
     like.
   - **MATR's non-capacity pairs (0.090)** are close to the construction gap (0.087).
   - **MATR's capacity pairs (0.106)** carry, in addition, the estimator's errors-in-variables bias. ẑ is read from
     noisy capacity, so capacity noise enters every residual through its mapping's slope (V3 anomaly 4, V5 anomaly 4).
   - The offset spread round-trips well: generated vs fitted IQR is 4.96 vs 4.77 min (MATR charge time) and 1.97 vs
     1.68 min (HUST charge time).
3. **HUST q₁ spread, 26.9–27.1 against 21.2 mAh (+27 %).** Two causes, measured:
   - resampling 300 units from 54 already gives an IQR of 24.7 mAh on the resampled q₁;
   - D18 anchors the generated mapping at the trajectory's own reference Q_ref. The rollover family extrapolated back
     to the first position puts Q_ref − q₁ at −7.0 mAh median (IQR 8.7 mAh).
   As declared, this is reported in the V5 property table, not a stop case. MATR passes (10.0–12.4 against 10.8 mAh).

## Anomalies

1. **HUST's generated target carries a large offset term (a third of Var(y)).** HUST's charge time and mean discharge
   voltage differ systematically between cells, and β gives those channels two thirds of the weight. This is the X2
   question (ii): it gives a trained model a reason to read those channels. V6's channel-usage gate answers whether it
   does.
2. **The pooled-φ construction cannot reproduce MATR's within-unit correlation unit by unit** (see Checks 1). The
   alternative, per-unit matrices, was rejected before data because they would need repairs in most MATR units. V5
   reports the cost.

## Decisions needed

None.

## Addendum — third profile (ISU-ILCC): **stop and report** (brief §6)

- **Run.** `python scripts/v2/v4_generate_units.py --datasets ISU_ILCC --profile-config ISU_ILCC=isu_ilcc`. The checks
  are in `logs/checks_ISU_ILCC.md` and `tables/checks_ISU_ILCC.*`.
- **Construction checks pass:**
  - Σϕ* = y; g(x) − y = Σwε; pristine y = 0; E[ε] = 0;
  - z and T as declared; pattern invariance;
  - X3 construction 0.019 ≤ 0.05.
- **Fails, as a declared stop case: the offset share Var(y_offset) / Var(y) = 0.773 / 0.765 / 0.823** for generation
  seeds 0 / 1 / 2 (recency; uniform the same to 0.001). Above 0.5.
  - The offsets are 99.2 % (charge time) and 97.6 % (mean discharge V) explained by the test condition, so the target
    would mostly encode the protocol a cell ran under.
  - The state, the options and the recommendation (report ISU-ILCC as the X6 outcome and continue v2 with MATR and
    HUST) are in `artifacts/v2/STOP_REPORT_third_profile_offsets.md`.
  - **The third profile is parked pending the authors' decision.**
- **Also reported, not stop cases:**
  - Generated q₁ IQR 11.0–13.7 mAh against 2.7 mAh measured (power-law back-extrapolation to the first position).
  - Estimator check 0.231.
