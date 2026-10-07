# V0 — setup and declarations r3 (brief "DegradX v2", 2026-10-07)

## What ran

- **Tag and branch.** `v1-results` tags the v1 HEAD (`a6be383`) and is pushed. All v2 work is on branch `v2`.
- **Output roots.** `artifacts/v2/`, `results/v2/` and `data/v2/` (`data/` is gitignored, as in v1). Their paths are in
  `degradx.ARTIFACTS_V2`, `RESULTS_V2` and `DATA_V2`.
- **Declarations r3.** Added as `declared_by_design.v2` in `configs/declarations.yaml`, with dated (2026-10-07)
  supersession entries. The declarations as they stood at `v1-results` are kept in
  `configs/declarations_history/declarations_at_v1-results.yaml`.
- **Decision record.** D25 (scope reductions, X8).
- **DEVIATIONS T4.** v1 S6–S8 intervals used 2 000 bootstrap resamples instead of the declared 10 000.

## What r3 declares (one line each)

| block | declares |
|---|---|
| `scope` | D25: final-position weighting, setting sweep, representation distance, NASA PCoE and cross-fitting dropped. Recency is primary and uniform is the sensitivity readout. |
| `statistics` | 10 000 resamples for every v2 interval; weightings read from `scope`; noise fallback; post-offset noise in the weight guard; X4 permutation streams; the 36 h TimeSHAP threshold covers all profiles together. |
| `stop_rules` | The six cases of brief §6. They supersede, for v2, the r2 action on a failed leakage test ("the profile is corrected"). |
| `tstr_isolation` (X1) | The input sets as the brief states them: full, capacity only, capacity / q₁. Two reported variants: two-point state normalisation, and non-capacity channels centred per unit. Paired BCa readings with the leave-one-seed-out robustness rule, the HUST control reading, and the descriptive extras. "X2 is built whatever X1 shows." |
| `per_unit_offsets` (X2) | Backfitting (tolerance 1e-4 of each mapping's range, 200 iterations, 10 readings minimum). The capacity mapping uses the unit's own reference (measured: S3 q₁; generated: the trajectory's Q_ref per D18). Joint resampling. Reports include the between-unit variance of residual means and the offset sampling-noise term. Stop if Var(y_offset) / Var(y) > 0.5. |
| `correlated_noise` (X3) | Target: the within-unit residual correlation ρ̄ (the variance-weighted mean of per-unit correlations). One innovation matrix per profile at the pooled φ, repaired by Higham if not positive definite. The construction check compares the same estimator on generated noise, within 0.05 on the mean over three seeds. |
| `generator_checks` | The S4 checks, plus: y = 0 at z = 0 with zero offsets; the correlation check; the q₁ spread (IQR within 20 % of the units reaching EOL). |
| `channel_usage_gate` (X4) | Ridge conditional resampling with BCa over test units. "Used" iff the lower bound > 0, as the brief states; a materiality reading (> 0.02) is reported beside it. The void covers channel-level scores only (allocation error, zero-weight mass, and the unused channel's temporal error). Rank agreement stays reported. |
| `scoring` (X5) | TV channel allocation error and the ϕ*-mass-weighted 1-Wasserstein temporal profile error, with undefined cases counted. The resolution criterion is unchanged (sign flipped for error scores). A registers check uses a materiality of 10 % of the chance-to-perfect distance, with smoothing read on recency. The scores are recomputed on the v1 S8 maps. |
| `third_profile` (X6) | E1–E6. E3 is binding at 67. E4 is dataset-level. E5 is operational: charge time and mean discharge voltage must pass the weight guard. Tongji was found ineligible from its documentation before download. The mechanism diagnostic is defined. |
| `timeshap_full_scale` (X7) | The brief's design: 3 000 explanations per profile; on a profile with patterns the floor runs on the pattern-free counterpart window. Feasibility steps; equivalence ≤ 1e-10; stop above 36 h. |
| `readings` | Declared readings for X2(i), X2(ii), X3 (covariance, discriminator, plus a run with X3 switched off), X6(i), X6(ii) and X7 (values against the 40-window subset; floor against the method gap). |
| `fidelity` | Table 2 gets a fitting-split column; the anchor D-record if MATR stays outside HUST's interval. |
| `observation_target` (X9) | Pending: declared and committed before V9. |

## Review before commit

Three independent reviewers checked r3 and D25 against the brief, for mathematical soundness and for
pre-registration hygiene. Each finding was then given to a skeptic told to refute it. The findings that survived were
applied before this commit. The main ones:

- **X3 attenuation.** Per-unit φ pushes the innovation correlation past its feasibility bound in many units. A
  correlation pooled over units with different variances is attenuated twice when imposed per unit. Fix: one profile
  matrix at the pooled φ, and the within-unit target ρ̄.
- **X1 interpretation.** Capacity / q₁ moves the initial-capacity spread to EOL rather than removing it, so a
  state-normalised variant was added. A positive per-cell-structure reading only says "the gap sits in the non-capacity
  channels", so a per-unit-centred variant was added to test offsets specifically. The interval is conditional on the
  trained models, so the leave-one-seed-out rule was added.
- **X2 reporting.** v1's AR(1) estimator centres each unit, so constant offsets never entered the v1 noise variance.
  The before/after report now includes the between-unit variance of residual means.
- **D18 consistency.** A generated unit's capacity mapping uses its own trajectory reference Q_ref. Using the source
  unit's q₁ would reintroduce the offset D18 removed.
- **X4 materiality.** "> 0" is kept as the brief states. The materiality reading at the leakage tolerance is reported
  beside it.
- **Commit order.** D27 (the channel excursion rule) was decided after inspecting held-out cells. It is committed
  separately, after this commit.

## Checks

- `load_declarations()` parses r3, and every `v2` key is present.
- v1 generation is unchanged by the library additions. Units regenerated from the v1 profiles are bit-identical to
  the cached v1 units: MATR, HUST and NASA PCoE, 25 units each.

## Decisions needed

None for a human. Taken: D25.
