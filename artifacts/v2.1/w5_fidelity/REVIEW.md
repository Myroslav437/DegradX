# W5 — fidelity of FORM (RQ1; V5 design) and the one MATR/HUST computation of v2.1 (brief "DegradX v2.1", 2026-10-13)

## What ran

- **FORM.** `scripts/v2/v5_fidelity.py --datasets TRI_FORMATION --out-dir artifacts/v2.1/w5_fidelity --workers 8`, CUDA,
  3 366 s (TSTR 3 054 s). Then `scripts/v2/v5_discriminator_readability.py` (the D02b rule, DEVIATIONS T6).
  - **TSTR.** All five declared X1 input sets, 3 generation × 5 initialization seeds, 127 fitting / 55 held-out units
    (all reach EOL, 38 890 held-out windows).
  - **Discriminator and covariance.** Generation seeds 0–2 and the independent-noise set (seed 0).
  - **Property table.** Fitting, held-out and generated (seed 0) sides, V3 estimator, with the D30 record-end rule on
    generated series.
- **MATR and HUST** (the brief's one exception, declarations `v2_1.tstr_without_x3`). `scripts/v2_1/w5_tstr_without_x3.py`
  runs V5's TSTR on the existing independent-noise sets `data/v2/generated/<MATR|HUST>/seed0_x3off.pkl`, full input set.
  Nothing is regenerated, and V5's TRTR models are reused. Output: `tstr_without_x3/`.

## Results — FORM

### Transfer (`tables/fidelity.json`, Table 1 and Table 3)

| input set | ratio [95 % BCa] | RMSE TSTR / TRTR [cycles] |
|---|---|---|
| full | **1.54 [1.28, 1.74]** (15 seed combinations 1.42–1.78) | 145 / 94 |
| capacity only | 1.08 [0.99, 1.15] | 147 / 135 |
| capacity relative | 1.12 [1.08, 1.17] | 138 / 123 |
| capacity state | 1.10 [1.06, 1.15] | 141 / 128 |
| full centred | 1.16 [1.05, 1.23] | 133 / 114 |

- **Declared reading** (`v2_1.readings.transfer`):
  - the interval does not contain 1;
  - the point estimate lies outside HUST's interval [0.936, 1.342], as MATR's does;
  - the intervals overlap (1.28 < 1.34).
  - HUST stays the anchor (D29; brief decision). This is listed in the Notes box.
- **Where the gap sits** (X1 tests on the v2 profile; "holds" means the interval stays above 0 with each generation
  seed and each initialization seed left out):
  - **full vs capacity only:** 0.35 [0.17, 0.48]. **Holds** (leave-one-out lower bounds 0.13–0.21).
  - **full vs full centred:** 0.28 [0.10, 0.40]. **Holds** (lower bounds 0.05–0.17).
  - **capacity only vs capacity relative:** −0.03 [−0.10, 0.01]. Does not hold.
- **Reading.**
  - The gap sits in the channels other than capacity. Most of it, 0.28 of 0.35 log units, goes when those channels are
    centred per unit on their first k positions.
  - The measured-trained model lowers its error from 135 to 94 cycles with those channels. The generated-trained model
    does not (147 → 145).
  - So the level of a cell's channels at early life tells a model about its life in the measured cells, more than it
    does in the generated ones. That is the configuration of MATR's v1 profile, not of its v2 profile.
  - Joint resampling of (θ, q1, offsets) keeps each fitting unit's offsets with its life. But an offset is the
    median over the unit's whole life. A channel whose early-life level, relative to that median, varies with the
    formation protocol carries information that the generated units, with one mapping shared by all units, do not.
  - Trajectory shapes that vary with the protocol are the evident, untested candidate.
  - This is not decided here, and the generator is left as fitted.

### Discriminator, covariance (Table 1)

- **Discriminative error: readable on all three seeds** (D02b). This is the first readable cell of v2:
  - seed 0: 0.097 [0.059, 0.154];
  - seed 1: 0.103 [0.082, 0.124];
  - seed 2: 0.168 [0.122, 0.223].
  - A window classifier separates generated FORM windows from measured ones with about 90 % accuracy.
  - It does not say which property is responsible (Section 3.5.1). Independent noise: 0.087.
- **Covariance agreement:** 0.35 (seeds 0.37, 0.33, 0.35), against 0.30 [0.20, 0.43] between measured fitting and
  held-out windows. **Closed** under the declared reading (≤ the upper end 0.43).
  - Independent noise: 0.32. As in MATR and HUST, the correlated noise does not move the covariance agreement.

### Property table (`tables/properties_TRI_FORMATION.json`, Table 2)

Values are fitting / held-out / generated.

- **Reproduced:**
  - family: two-term exponential on all three sides, with fit error 0.0105 / 0.0109 / 0.0077 of q1;
  - drift 7.78 / 8.27 / 7.87 mAh per 100 cycles;
  - T 701 / 665 / 683 cycles;
  - offset IQRs: charge time 1.43 / 1.21 / 1.31 min, mean discharge voltage 13.3 / 8.5 / 12.9 mV;
  - noise autocorrelations 0.95 / 0.95 / 0.94 (charge time);
  - positive residual runs 0.33 / 0.29 / 0.27 per 100 positions. The inserted patterns plus noise reproduce the
    detected rate.
- **Departing by a quarter or more:**
  - capacity noise variance 1.43 / 1.56 / 0.99 mAh²;
  - charge-time noise variance 0.77 / 0.62 / 0.58 min²;
  - q1 IQR 2.63 / 2.31 / 3.43 mAh. This is the W4 warning, from the guard on the resampled units.
- **Residual correlation:** relative Frobenius 0.13 (generated) against 0.10 (held-out). Capacity pairs 0.109 against
  0.065, the estimator's errors-in-variables bias seen in MATR. Other pairs 0.094 against 0.085.
- **Generated units in the EOL rows: 279 of 300.**
  - The other 21 end 2.4–4.6 mAh above the threshold, beyond the declared record-end tolerance (1 % of 0.24 Ah =
    2.4 mAh). The slowly varying capacity noise (lag-1 0.91 on generated units) holds their last readings above it.
  - This is D30's rule applied as declared. Nothing is changed, and the table note states it.
  - MATR and HUST kept all 300.

## Results — MATR and HUST without X3 (`tstr_without_x3/tables/tstr_without_x3.json`)

| | v1 (printed) | v1 full_D27 | v2 without X3, seed 0 | v2, seed 0 | v2, three seeds |
|---|---|---|---|---|---|
| MATR | 3.42 [2.28, 4.96] | 3.51 [2.30, 4.99] | **1.60 [1.06, 2.50]** | 1.58 [1.13, 2.37] | 1.49 [1.04, 2.29] |
| HUST | 1.46 [1.11, 1.76] | 1.46 [1.11, 1.76] | **1.12 [0.92, 1.29]** | 1.15 [0.91, 1.31] | 1.17 [0.94, 1.34] |

- **Shares, as ratios of ratios with paired BCa:**
  - X2 (offsets): MATR 2.19× [1.69, 2.79], HUST 1.30× [1.03, 1.60];
  - X3 (correlated noise): MATR 1.02× [0.92, 1.10], HUST 0.98× [0.88, 1.06].
- **Reading.** In transfer, the per-unit offsets carry the improvement from v1 to v2. The correlated noise carries none.
  Both shares read the same way in the covariance agreement and the discriminator (V5).
- **Determinism.** Exact: the retrained TRTR and TSTR at seed 0 reproduce V5's per-unit errors (max relative difference
  0), and the held-out units and windows are identical to V5 and V1.

## Checks

- `logs/checks.md`: the discriminator does not separate trivially (accuracy 0.877 < 0.99), and the ratio is finite.
- `tstr_without_x3/logs/checks_tstr_without_x3.md`: 8/8 pass.
- **No stop case.** Fidelity has no stop rule in §5. The transfer reading is reported, not gated.

## Paper

- **Table 1.** FORM's block:
  - discriminator 0.10–0.17 (readable);
  - covariance 0.35 (0.30; 0.20–0.43);
  - transfer 1.54 [1.28, 1.74];
  - independent noise 0.09 / 0.32, with its transfer void (declared for MATR and HUST only).
  - MATR and HUST gain the "independent noise" row (1.60, 1.12) and the "no offsets" ablation row (3.42, 1.46). The
    shares and the declared seed-0 row are in the note.
- **Tables 2 and 3:** FORM columns.
