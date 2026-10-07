# V4 — generate units from the v2 profiles (X2 offsets, X3 correlated noise)

## What ran

- **Command.** `python scripts/v2/v4_generate_units.py --device cpu --workers 8`, seed 20260915, CPU.
- **Units.** 300 units per profile for each generation seed 0, 1 and 2, split 0.7 / 0.15 / 0.15 at unit level (S4
  rule). Cached in `data/v2/generated/<profile>/seed<g>.pkl` (gitignored; regenerates bit-identically from the seeds).
- **X3-off set.** One extra set per profile, `seed0_x3off.pkl`: the v2 profile with independent per-channel noise.
  It isolates X3's own share at V5 (declared reading `X3_isolation`).
- **Weightings.** Recency and uniform (D25).
- **Re-run.** The checks were run a second time on the cached units after one fix in the script: the q₁-spread
  comparator is now the fitting units reaching EOL, as declared (it had used all guard-passing units).

## What came out

| | MATR seed 0 / 1 / 2 | HUST seed 0 / 1 / 2 |
|---|---|---|
| T median [IQR] | 823 [535, 1039] / 748 [506, 985] / 727 [515, 1020] | 1807 [1585, 2221] / 1903 [1602, 2178] / 1881 [1680, 2063] |
| offset share Var(y_offset) / Var(y), recency (uniform) | 0.111 (0.116) / 0.112 (0.117) / 0.104 (0.109) | 0.319 (0.320) / 0.344 (0.345) / 0.312 (0.313) |
| Var(y_offset) / Var(y_state), recency | 0.120 / 0.120 / 0.114 | 0.493 / 0.550 / 0.474 |
| corr(y_offset, y_state) | −0.03 to −0.07 | 0.03 to 0.04 |
| generated q₁ IQR (measured units reaching EOL) | 12.4 / 10.0 / 10.6 mAh (11.6) | 26.9 / 27.0 / 27.1 mAh (21.2) |
| innovation correlation repaired (X3) | no | no |

The offset contribution stays below the declared stop level of 0.5 everywhere. In HUST, the generated targets encode
cell identity to a third of their variance.

**X3 construction.**

| | MATR | HUST |
|---|---|---|
| within-unit correlation of the generated noise vs fitted ρ̄ (max \|Δ\|, mean over seeds) | **0.087** (> 0.05) | 0.008 |
| pooled comparison | 0.080 | 0.033 |
| gap implied by the pooled-φ construction, averaged over θ units | 0.127 | 0.014 |
| estimator check (V3 estimator on generated observations, generation seed 0) | 0.168 | 0.068 |

## Checks

94 pass, 6 warnings, 0 failures (`tables/checks.csv`, `logs/checks.md`). On every window of every unit, seed and
weighting:
- Σϕ* = y, to 0 relative error;
- g(x) − y = Σ w ε, to ≤ 6e-16;
- mean over units of g(x) − y is within 3 SE;
- a unit at z = 0 with zero offsets, no patterns and no noise has y = 0;
- E[ε] = 0 per channel;
- z starts at the pristine level and T is the first crossing;
- disabling patterns leaves z, T, R, the mean and the noise unchanged.

The 6 warnings are all declared readings, not construction errors:

1. **MATR X3 construction, 0.087 > 0.05.** This is the declared consequence of one innovation matrix at the pooled φ.
   MATR's per-unit lag-1 coefficients are spread out, so units away from the pooled φ generate a different stationary
   correlation. The gap implied by construction (0.127) explains the observed one. As declared, this is reported, not
   a stop case; V5's covariance agreement shows the consequence.
2. **MATR and HUST estimator check, 0.168 / 0.068.**
   - It refits the whole V3 estimator (mapping, offsets, AR(1)) on generated observations, so it compounds the
     construction gap with estimation error.
   - The offset spread round-trips well: generated vs fitted IQR is 4.96 vs 4.77 min (MATR charge time) and 1.97 vs
     1.68 min (HUST charge time).
3. **HUST q₁ spread, 26.9–27.1 against 21.2 mAh (+27 %).** Two causes, measured:
   - resampling 300 units from 54 already gives an IQR of 24.7 mAh on the resampled q₁;
   - D18 anchors the generated mapping at the trajectory's own reference Q_ref. The rollover family extrapolated back
     to the first position puts Q_ref − q₁ at −7.0 mAh median (IQR 8.7 mAh).
   As declared, this is reported in the V5 property table, not a stop case. MATR passes (10.0–12.4 against 11.6 mAh).

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
