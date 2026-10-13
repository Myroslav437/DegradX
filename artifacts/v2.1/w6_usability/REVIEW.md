# W6 — usability of FORM (RQ2; V6 design; brief "DegradX v2.1", 2026-10-13)

## What ran

- **Command.** `scripts/v2/v6_usability.py --datasets TRI_FORMATION --out-dir artifacts/v2.1/w6_usability`, CUDA (shared
  with W5), 2 370 s.
- **Ensembles.** Ten members per weighting: configuration A (64 × 2) and configuration B (128 × 1), each with seeds 0–4.
  Data: generated seed-0 units, 210 train + 45 validation + 45 test, 184 700 training and 30 413 test windows.
- **Gates.** The accuracy gate, the null-channel leakage gate, and the X4 channel-usage gate on every weighted channel.
- **Pattern-term reading.** It runs for the first time on a v2 profile, because FORM carries inserted patterns:
  - the variance ratio of the pattern term to the mean term;
  - term ablation (3 seeds per removed term);
  - the graded/sparse correlation on the test windows. This check was declared (`usability.graded_sparse_correlation_bound`)
    but never computed in V6; it is added for profiles with patterns and does not change MATR or HUST.

## Results

| quantity | recency | uniform |
|---|---|---|
| accuracy, NRMSE of the primary model (members passing) | **0.179** (10/10; members 0.176–0.190) | 0.183 (10/10) |
| offset term, share of Var(y) (test windows) | 0.159 | 0.167 |
| Spearman(y, RUL) | −0.69 | −0.69 |
| null leakage, upper bound (flat / permuted) | 0.0003 / 0.0003 | 0.0003 / 0.0008 |
| X4 conditional importance, capacity | 0.146 [0.128, 0.181] | 0.143 [0.127, 0.172] |
| X4, charge time | 0.094 [0.074, 0.120] | 0.100 [0.079, 0.127] |
| X4, mean discharge voltage | 0.096 [0.076, 0.122] | 0.100 [0.080, 0.125] |
| members using every weighted channel | 10/10 | 10/10 |
| permutation importance (capacity / charge time / mean discharge V) | 0.876 / 0.151 / 0.243 | — |
| pattern term, variance ratio | 1.7e-5 (band 0.05–0.50) | 1.3e-5 |
| ablation, mean term removed (NMSE increase) | 2.58 [2.23, 3.03] | 2.58 [2.22, …] |
| ablation, **pattern term removed** | **0.0000 [−0.0001, 0.0002]** | 0.0003 [−0.0006, 0.0012] |
| graded/sparse \|r\| (bound 0.30) | 0.045 | 0.008 |

- **Gates.** The accuracy gate and the null-channel leakage gate pass on both weightings, so there is no stop case.
- **Channel use.** Every weighted channel is used by every member, and materially (lower bound > 0.02). As on MATR and
  HUST, X2 makes the channels non-redundant for the trained model.
- **The pattern term is not learned** (declared reading `v2_1.readings.sparse_set_trained`, D21 logic).
  - Removing it from the training target does not raise the error on y: the interval contains 0 on both weightings.
  - At the fitted amplitudes its variance is about 1e-5 of the mean term's.
  - **Trained-model sparse-set scores for FORM are therefore void.** Paired retrieval is read on the reference model and
    in the degraded-map test (W7) only.
  - No amplitude is inflated (D21; brief §2). This is the outcome NASA PCoE had in v1.
- **The graded/sparse correlation** is far below the bound.

## Checks

All gates pass (`logs/checks.md`). The pattern ablation and the variance band are recorded as warnings, the declared
severity.

## Next

W8 is the full-scale reference values, with paired maps because FORM has patterns (4 680 TimeSHAP explanations).
