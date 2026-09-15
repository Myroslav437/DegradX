# Stage 8 — reference values for published methods (paper §3.6; Table 6)

## What ran

- One command per profile, seed 20260915, CUDA:
  `python scripts/s8_reference_methods.py --datasets <profile> --timeshap-windows 40 --timeshap-seeds 0 1 --timeshap-seeds-reference 0 --secondary-background`
  MATR 49 min and NASA PCoE 82 min by their run records; HUST about 40 min (its own wall clock was overwritten by the
  next run, and this is its TimeSHAP time, 2 077 s, plus MATR's non-TimeSHAP overhead). NASA PCoE costs most because it
  carries inserted patterns, so every TimeSHAP call is made twice, on the window and on its pattern-free counterpart.
  A final `--checks-only` pass re-ran the checks over all three profiles.
- Windows: 120 per profile from generated test units (generation seed 0), stratified across units — 45 units in MATR and
  HUST, 39 in NASA PCoE. TimeSHAP explains a stratified 40 of them (D23).
- Models: the primary trained LSTM (configuration A, model seed 0) from S6, and the reference model.
- Methods at their declared defaults: TimeSHAP (nsamples 32 000, cell level, `l1_reg` auto — D22), Integrated Gradients
  (captum, 50 steps), feature occlusion (captum FeatureAblation, one cell at a time). Baseline: the pristine window (C4).
- Also computed: the exact attribution of the reference model on all 120 windows and on the TimeSHAP subset (the
  comparable ceiling), the identifiability floor from the ten S6 ensemble members (IG and occlusion), and TimeSHAP from
  the conventional average event with the ground truth that matches that baseline (C4 secondary).
- Decision harness: D24 (Table 6 layout).

## What came out

Rank agreement, recency weighting (unit means; intervals in Table 6):

| | MATR | HUST | NASA PCoE |
|---|---|---|---|
| exact attribution of the reference model (ceiling) | 0.815 | 0.870 | 0.733 |
| IG / occlusion on the reference model | 0.815 / 0.815 | 0.870 / 0.870 | 0.733 / 0.733 |
| TimeSHAP on the reference model (ceiling on its 40 windows) | 0.755 (0.750) | 0.859 (0.859) | 0.744 (0.743) |
| IG / occlusion / TimeSHAP on the trained model | 0.551 / 0.461 / 0.468 | 0.321 / 0.298 / 0.333 | 0.316 / 0.283 / 0.286 |
| ensemble range, IG / occlusion (10 models) | 0.440–0.551 / 0.378–0.470 | 0.212–0.544 / 0.254–0.372 | 0.245–0.339 / 0.259–0.395 |
| zero-weight mass, trained (reference model: 0) | 0.113–0.136 | 0.014–0.027 | 0.237–0.255 |
| TimeSHAP from the average event (its own ground truth) | 0.561 | 0.315 | 0.435 |
| retrieval, trained / reference | void (no patterns) | void (no patterns) | void (D21) / 1.00 |

Other weightings are in `tables/reference_values.json`: under uniform weighting the trained values move by up to 0.13 and
the ordering of the methods changes in all three profiles; under final-position weighting every method scores 0.14–0.18
on the trained model while the ceiling stays at 0.84–0.87.

## Checks

45 checks, all pass (`logs/checks.md`, written by the `--checks-only` pass so that all three profiles are covered; each
per-profile run overwrites this file).
- IG and occlusion on the reference model equal $w(x-x^{0})$: largest absolute difference 1.59e-06 (NASA PCoE, final
  position), everywhere below the 1e-3 relative bound.
- All method rows present, ten ensemble members per profile and weighting, TimeSHAP background recorded, and the stored
  window count reproduced from the seeded selection.

## Anomalies

1. **The trained model costs more than the method does.** The distance from the ceiling to the trained score is 0.26 to
   0.57, while the three methods differ from each other by at most 0.089. With ensemble ranges of 0.094 to 0.332, no
   ordering of the methods on a trained model is supported (C2, D24).
2. **HUST has the widest ensemble range** (IG 0.212–0.544) although it is the profile with the lowest model error
   (NRMSE 0.012). Accuracy does not constrain which of the observationally equivalent functions a model implements.
3. **NASA PCoE puts a quarter of the attributed mass on zero-weight channels** (0.24–0.26 against 0.01–0.14 elsewhere).
   It is the profile whose zero-weight temperature channel carries information the others do not (S6 conditional
   importance 0.006–0.017), so the model reads it and the methods attribute it.
4. **TimeSHAP is exact on the reference model to 0.005** and moves by at most 0.016 between the two sampling seeds on
   trained models, which is what D22 and D23 assumed when the budget was reduced.
5. **Retrieval on the reference model is 1 at every window.** Nothing is learned from it; it is reported because the
   trained-model column is void (D21). The S7 part-two rows show that a high paired-retrieval score on a trained model
   does not imply the model uses the pattern term.
6. **The average-event background moves scores by up to 0.15 in either direction** (MATR +0.093, NASA PCoE +0.149,
   HUST −0.018). Reference values are therefore quoted with their baseline.

## Decisions needed

None for a human. Taken: D23 (budget, before the runs), D24 (Table 6 per profile).
