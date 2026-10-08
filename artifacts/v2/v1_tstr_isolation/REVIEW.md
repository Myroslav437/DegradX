# V1 — X1: TSTR isolation ablation on the v1 profiles (no generator change)

## What ran

- **Command.** `python scripts/v2/v1_tstr_isolation.py`, seed 20260915, CUDA, 70 min wall clock (21:44–22:55).
  - From 22:30 it shared the GPU with V6 (allowed: training determinism does not depend on sharing; only V8's timing
    runs need an exclusive GPU).
  - The empty output folders created at 21:21 came from a `--dry-run`, which creates them but reads no data. They were
    removed before the real run.
- **Models.** For each profile (MATR, HUST) and each of 6 input sets: TRTR (model seeds 0–4) and TSTR (v1 generation
  seeds 0–2 × model seeds 0–4).
  - The same held-out units as S5.
  - The LSTM of `configs/models/lstm.yaml`.
  - 240 trainings in total.
- **Declared beforehand.** The readings, the leave-one-out robustness rule, the HUST control reading and the
  descriptive extras: declarations r3 `v2.tstr_isolation`, committed in `9c25b6c` (r3) and `ac2726e` (D27) before
  this run.

## What came out

- **Reproduction.** The full input set reproduces v1's S5 ratios exactly (|Δ| = 0): MATR 3.420 [2.276, 4.958], HUST
  1.461 [1.111, 1.764].
- **Readings** (D26, paired BCa over held-out units, 10 000 resamples, robust to leaving out each seed):
  - **MATR per-cell structure holds:** Δlog 1.138 [0.657, 1.753]. Capacity-only ratio 1.096 [0.865, 1.497].
  - **MATR offsets specifically hold:** Δlog 0.519 [0.213, 0.923]. Centred ratio 2.035; about 46 % of the
    non-capacity log-gap.
  - **The initial-capacity spread does not contribute:** Δlog −0.009 [−0.325, 0.294].
  - **HUST (control):** no reading holds.
  - **Note on `robust_to_leave_one_out` (added 2026-10-08, v2 pipeline review).**
    - **What decides a reading.** The `holds` field implements the declared rule: the full interval lies above 0, and
      so does every leave-one-seed-out interval.
    - **What the flag means.** It is descriptive. For an interval that does not lie above 0, it asks whether every
      leave-one-out interval still contains 0.
    - **A known gap.** The flag would wrongly mark an interval that lies wholly below 0 as not robust. No V1 or V5
      interval lies below 0, so nothing reported is affected.
    - **HUST per-cell row.** Its `False` is correct: leaving out generation seed 2 gives [0.012, 0.470], so the null is
      not robust either.
- **Descriptive.**
  - D27-cleaned measured side: 3.506 (MATR), so the held-out artefact does not drive the gap.
  - Leaving MATR_b1c2 out keeps every MATR reading (per-cell 0.902 [0.568, 1.418]; offsets 0.437 [0.158, 0.857]).
- **Files.** `tables/tstr_isolation.json`; per-unit squared errors of every run in `tables/per_unit_sse_<ds>.npz`;
  runs in `tables/runs_<ds>_<input set>.*`.

## Checks

6 pass (`logs/checks.md`):
- the full input set reproduces v1 for MATR and HUST;
- held-out units reaching EOL ≥ 20 (MATR 38, HUST 23);
- every window ends at or after k.

## Anomalies

1. **The measured-trained (TRTR) model uses the non-capacity channels a great deal; the generated-trained (TSTR) model
   cannot.** MATR TRTR RMSE: 326 cycles on capacity alone, 151 with all channels. TSTR: 357 and 516. This asymmetry is
   the gap.
2. **The v1 generator's q₁ spread is far below the measured spread** (generated IQR 1.8 mAh against 11.6 measured,
   MATR), but it does not affect transfer. X2's per-unit capacity mapping fixes the spread anyway (V4: 10.0–12.4 mAh).

## Decisions needed

None. Taken: D26 (readings as declared).
