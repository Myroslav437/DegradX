# D31 — X9 pilot: an observation-level target makes the channel allocation identifiable on HUST, but not the position-level scores; the benchmark keeps y

**Stage / claim affected:**
- V9 (brief "DegradX v2", X9; exploratory, HUST, recency);
- §5 Discussion (future work on the target definition);
- nothing in the paper tables (brief V9).

**Question (brief X9).** Does defining y on the observed window restore position-level identifiability?

**Design (declared before running, r3 `v2.observation_target`, 2026-10-07).**
- **Target.** y_obs = Σ w (x − x⁰) on the observed window, with noise and offsets included.
- **Reference.** The reference model g is then the data-generating function, and ϕ*_obs = w (x − x⁰).
- **Data.** V4 generation seed 0, with the declared train / validation / test split (210 / 45 / 45 units).
- **Models.** Ten LSTM members as V6: configurations A (64 × 2) and B (128 × 1) × model seeds 0–4.
- **Measures.**
  - Accuracy, as NRMSE and as RMSE relative to SD(Σwε).
  - The X4 gate on every member.
  - IG and feature occlusion (pristine baseline) on V8's 120 HUST windows, for every member.
  - Rank agreement, channel allocation error and temporal profile error against ϕ*_obs.
- **Reading.** Identifiability is restored for a score iff the ensemble range of every method (max − min of the ten
  member means) falls below the largest gap between methods on the primary member (A0).

**Evidence** (`artifacts/v2/v9_observation_target/tables/observation_target.json`; figure
`figures/hust_yobs_ensemble_vs_method_gap`).

| | value |
|---|---|
| NRMSE on y_obs, ten members | 0.0012–0.0019 (gate 0.30) |
| RMSE / SD(Σwε) (declared reading: ≤ 0.5 means the model reads the cell-level values) | 0.013–0.018; **all ten members read the cells** |
| X4 conditional importance, A0: capacity / charge time / mean discharge V | 0.031 [0.027, 0.038] / 0.034 [0.030, 0.041] / 0.606 [0.526, 0.708]; all used materially by all ten members |
| IG on the reference model vs ϕ*_obs (correctness check) | max \|Δ\| 7.5e-8 |

| score (against ϕ*_obs) | A0: IG / occlusion | largest method gap | ten-member range: IG / occlusion | restored |
|---|---|---|---|---|
| rank agreement (↑) | 0.961 [0.959, 0.962] / 0.958 [0.954, 0.960] | 0.003 | 0.077 / 0.072 | **no** |
| channel allocation error (↓) | 0.004 [0.003, 0.005] / 0.019 [0.015, 0.023] | 0.015 | 0.006 / 0.013 | **yes** |
| temporal profile error [positions] (↓) | 0.79 [0.72, 0.85] / 0.75 [0.70, 0.82] | 0.035 | 0.47 / 0.45 | **no** |

Notes on the ranges:
- **Rank agreement.** The range comes mostly from one member: B3 reads 0.888 and 0.891, while the other nine lie
  within 0.950–0.965. Without B3 the range is still about 0.013, four times the gap.
- **Temporal error.** It spreads over 0.53–1.02 positions across members for both methods.

**On the standard y, the same 120 windows (V8, `reference_values.json`), HUST recency:**

| score | primary member: IG / occlusion, against ϕ* | largest IG–occlusion gap | ten-member range: IG / occlusion |
|---|---|---|---|
| rank agreement | 0.734 / 0.750 | 0.016 | 0.151 / 0.206 |
| channel allocation error | 0.164 / 0.182 | 0.018 | 0.093 / 0.098 |
| temporal profile error | 2.82 / 2.93 | 0.108 | 1.17 / 0.73 |

Changing the target narrows the ensemble ranges:
- rank agreement: 2–3 times narrower;
- channel allocation error: 7–15 times narrower;
- temporal profile error: 1.6–2.5 times narrower.

The levels improve as well: rank agreement 0.73–0.75 → 0.96, temporal error 2.8–2.9 → 0.75–0.79 positions.

## Interpretation

- **What the pilot shows.** A model trained on y_obs learns the cell-level function, and its maps agree with the
  observation-level ground truth far better than maps of the standard-y models agree with ϕ*: rank agreement 0.96
  against 0.73–0.75 on the same windows. The channel allocation becomes identifiable: the ten members disagree less than IG and
  occlusion differ.
- **Positions stay unidentifiable.** The members agree on which channel carries the attribution, but not on where in
  the window it sits. Every member reaches the same accuracy (NRMSE ≤ 0.002), yet their temporal profile errors span
  half a position or more, ten times the gap between methods.
  - **The likely cause.** The LSTM can represent the same linear function of the window with different positional
    sensitivities. Neighbouring positions are almost collinear (lag-1 noise autocorrelation 0.94–0.99 on HUST, Table 2), so
    the accuracy barely constrains how the weight is split along the window.
  - The pilot does not test this cause. It is stated as the likely one.
- **Answer to X9: no.** Defining y on the observed window does not restore position-level identifiability on HUST. It
  restores channel-level identifiability.

## Decision

**Options considered**
- **a. Keep the benchmark target y and report the pilot as future work.** The scores of the paper rest on y.
- **b. Adopt y_obs as the benchmark target.**
  - This changes the declared target, the attribution ground truth and every score after V6.
  - The brief puts V9 outside the paper tables. Position-level identifiability is still not restored, so the
    reason to switch would be the channel level alone.
- **c. Adopt y_obs for the channel allocation score only.** Two ground truths for one map is not a design a reader
  can follow.

Real: (a) is what the brief prescribes. (b) and (c) would need a new methodology round.

Works: (a) keeps every reported number on one declared target. (b) gains channel-level identifiability and loses
continuity with v1 and V5–V8.

Clear, (a): "On an observation-level target the channel allocation becomes identifiable, the positions do not; the
benchmark keeps the state-level target."

**Chosen: a.**
1. *Logical:* the pilot's question is answered (no). The partial gain does not answer the position-level question.
2. *Consistent:* the brief (nothing from V9 in the tables) and r3 `observation_target.outputs`.
3. *Clear:* one sentence.
4. *Measured:* the table above.

**Cost.**
- **Limited scope.** One profile (HUST) and one weighting. IG and occlusion only; TimeSHAP was optional and was not
  run.
- **The cause of the positional spread** (near-collinear neighbouring positions) is a hypothesis and is not tested.
- **The "restored" reading for the allocation error has a small margin:** the occlusion range is 0.013 against a gap of
  0.015.

**Paper impact:** §5, one sentence in future work (target defined on the observed window). Nothing in the tables.
