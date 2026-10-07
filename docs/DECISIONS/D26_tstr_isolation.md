# D26 — X1: MATR's transfer gap sits in the non-capacity channels, and constant per-cell offsets explain about half of it; the missing initial-capacity spread does not contribute

**Stage / claim affected:**
- V1 (brief "DegradX v2", X1);
- RQ1 interpretation of v1's MATR TSTR ratio (3.42);
- the case for X2 (per-unit offsets) and X3 (correlated noise);
- v1 §4.1 and §5 "What resists calibration".

**Question (brief X1).** Is MATR's TSTR gap caused by per-cell structure in the non-capacity channels, or by the missing
initial-capacity spread?

**Design (declared before running, r3 `v2.tstr_isolation`).** v1 profiles, v1 generated units (generation seeds 0–2) and
model seeds 0–4. The same held-out units: 38 MATR units reaching EOL (29 605 windows) and 23 HUST units (43 272 windows).
Inputs to every TSTR and TRTR model:

| input set | MATR ratio [95 % BCa] | HUST ratio [95 % BCa] |
|---|---|---|
| full (S5 as run; reproduces v1 exactly, \|Δ\| = 0) | 3.420 [2.276, 4.958] | 1.461 [1.111, 1.764] |
| capacity + elapsed position | 1.096 [0.865, 1.497] | 1.280 [1.079, 1.529] |
| capacity / q₁ + elapsed position | 1.106 [0.971, 1.239] | 1.164 [0.920, 1.451] |
| (q₁ − q)/(q₁ − ρq_nom) + elapsed position (variant) | 1.109 [0.946, 1.299] | 1.137 [0.899, 1.396] |
| full, non-capacity channels centred per unit (variant) | 2.035 [1.415, 2.762] | 1.222 [1.049, 1.455] |
| full, measured side cleaned with D27 (descriptive) | 3.506 [2.299, 4.994] | 1.461 [1.111, 1.764] |

**Readings.** Paired BCa over held-out units, 10 000 resamples. "Holds" means the interval stays above 0 when each
generation seed and each model seed is left out in turn.

| reading | MATR Δlog [95 %] | holds | HUST Δlog [95 %] | holds |
|---|---|---|---|---|
| per-cell structure: log ratio_full − log ratio_capacity-only | **1.138 [0.657, 1.753]** (LOO lower bounds ≥ 0.560) | **yes** | 0.132 [−0.087, 0.343] | no |
| initial-capacity spread: log ratio_capacity-only − log ratio_capacity/q₁ | −0.009 [−0.325, 0.294] | no | 0.095 [−0.140, 0.343] | no |
| offsets specifically: log ratio_full − log ratio_centred | **0.519 [0.213, 0.923]** (LOO lower bounds ≥ 0.145) | **yes** | 0.179 [−0.074, 0.401] | no |

**Influence row (descriptive): MATR without the held-out unit MATR_b1c2.**
- Per-cell structure 0.902 [0.568, 1.418]; offsets 0.437 [0.158, 0.857]; initial spread 0.185 [−0.035, 0.452].
- The full input set measured with D27 cleaning differs from the v1 cleaning by −0.025 [−0.109, 0.007].
- **The paused cycle behind v1's 53.5 min² held-out variance is not what drives the gap.**

## Interpretation (what D26 states; nothing was branched on it)

1. **MATR's gap sits in the non-capacity channels.**
   - With capacity and position alone, a generated-trained model transfers almost as well as a measured-trained one
     (1.10).
   - The measured-trained model gains a lot from the other channels (RMSE 326 → 151 cycles); the generated-trained one
     does not (357 → 516).
   - The v1 generator's non-capacity channels lack something that predicts lifetime in measured MATR cells.
2. **Constant per-cell offsets are about half of it.**
   - Centring each non-capacity channel per unit, by its own early-life median, removes 0.52 of the 1.14 log-gap
     (46 %), robustly.
   - That is exactly what X2 adds to the generator.
   - The rest (0.62 log units) is non-capacity structure that is not a constant level: within-unit cross-channel
     correlation (X3 adds it), mapping shape and its interaction with the offsets.
3. **The missing initial-capacity spread does not contribute measurably.** Capacity / q₁ and the two-point state input
   give the same ratio as raw capacity (1.10–1.11). The v1 generator's lack of q₁ spread is a fidelity defect of the
   property table, not of transfer.
4. **The HUST control shows neither effect.**
   - HUST runs one charging protocol, and none of its intervals lies above 0.
   - So, by the declared HUST reading, MATR's gap can be attributed specifically to MATR's per-cell (charging-policy)
     structure, not to a generic generated-vs-measured difference in the non-capacity channels.

**Does X1 establish that X2 is the right fix?** Partly.
- X2 targets the half of MATR's gap that constant offsets explain.
- X3 targets part of the rest.
- V5 measures whether the two together bring MATR within HUST's interval (declared reading `X2_i_closes_matr_gap`).

## Protocol

- **Options:** (a) report the readings as declared; (b) re-specify the ablation after seeing it.
- **Chosen: (a).** The readings, the leave-one-out rule and the HUST reading were declared before V1 ran (r3 commit
  `9c25b6c`, script commit `ac2726e` → `0e1c76a`). Nothing was changed after the results were seen.

**Cost.**
- **The interval is conditional on the trained models.** The leave-one-seed-out rule bounds this, but the readings rest
  on 3 × 5 TSTR and 5 TRTR trainings per input set.
- **The paper's v1 account of the MATR gap must change.** v1 cited "per-cell charging-policy offsets" with the held-out
  charge-time variance as evidence. That evidence was a single paused cycle (D27), but the conclusion is now supported
  directly, and quantified (about half).
- **The capacity-only ratio's interval (MATR [0.87, 1.50]) is wide.** "Almost as well as measured" is the point
  estimate.

**Paper impact:** §4.1 Results (the X1 table as a supplementary table, with the reading in one sentence) and §5 "What
resists calibration". No methodology change; X2 and X3 are the round-7 amendments.
