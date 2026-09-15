# Stage 5 — RQ1, profile fidelity (paper §3.5.1; Tables 1–2, Figure 6)

## What ran

- Command: `python scripts/s5_fidelity.py --datasets MATR HUST NASA_PCoE` (seed 20260915, CUDA), 13 min.
- Generated sets: S4 generation seeds 0, 1, 2 (300 units each).
- LSTM (configs/models/lstm.yaml) trained with model-initialisation seeds 0–4.
- TS2Vec encoder vendored from the official code at commit b0088e1, MIT (`src/degradx/metrics/ts2vec`); only the import lines differ from upstream.
- Decision harnesses: D02b (held-out minimum per measure) and D19 (NASA cross-fitting).

Measured sets:
- fitting split: the units the profile was fitted on;
- held-out split: units that took no part in fitting.

Every distributional measure compares generated windows (L = 24, at most 100 per unit, null channels excluded) with held-out measured windows. Its baseline is the same measure between measured fitting and held-out windows. The transfer measurement follows the paper exactly.

## What came out

| figure | what to look for |
|---|---|
| `tstr_error_ratio` | TSTR ratio with its 95 % BCa interval over held-out units; grey bar: range over the 15 (generation × model seed) pairs; grey marker: void (D02b). |
| `discriminative_score` | Discriminative error per generation seed; annotated as a coarse indicator. |
| `<ds>_property_distributions` | Held-out measured vs generated T and drift distributions, and noise variances per channel (same S3 estimators on both sides). |
| `<ds>_window_embedding_illustration` | t-SNE of TS2Vec window representations, labelled as illustration. |
| `../s4_generate_units/figures/<ds>_generated_vs_measured` | Paper Fig. 6 panels (S4). |

**Table 1 (`tables/fidelity.json`)**, L = 24:

| profile | units (held-out / reaching EOL; generated per seed) | discriminative error (seeds 0/1/2) | representation distance: generated vs held-out (baseline: fitting vs held-out) | covariance agreement, rel. Frobenius (baseline) | transfer ratio [95 % CI] |
|---|---|---|---|---|---|
| MATR | 40 / 38; 300 | 0.093 / 0.071 / 0.052 | 64.2 / 64.1 / 64.1 (59.9): **void**, unit-bootstrap half-width 1.45 × value | 0.685 / 0.683 / 0.694 (0.278) | **3.42 [2.28, 4.96]**: RMSE 515.8 vs 150.8 cycles; seed-pair range 2.56–5.56 |
| HUST | 23 / 23; 300 | 0.204 / 0.117 / 0.172 | 2.93 / 2.96 / 2.95 [2.13, 4.50] (0.164) | 0.421 / 0.426 / 0.426 (0.038) | **1.46 [1.11, 1.76]**: RMSE 301.6 vs 206.4; range 1.27–1.93 |
| NASA PCoE | 5 / 3; 300 | **void** (5 < 8 units; seed values 0.50 / 0.02 / 0.02 from 1 test unit) | **void** (half-width 0.93) | **void** (5 < 12) | **void** (3 < 20): 1.64 [0.87, 2.00] measured but not reportable |

**Table 2 (`tables/properties_<ds>.json`):** the S3 estimators applied to held-out measured units and to generated units (seed 0).

| property | MATR measured / generated | HUST measured / generated |
|---|---|---|
| family; median CV-RMSE of the profile's family | two-term exp. 0.0054 / two-term exp. 0.0028 | rollover 0.0032 / rollover 0.0014 |
| drift [mAh / 100 cycles], median [IQR] | 25.6 [20.1, 40.7] / 24.4 [19.3, 38.7] | 16.3 [14.7, 20.0] / 17.4 [14.4, 20.8] |
| transition position [fraction of T] | 0.999 / 0.999 | 0.651 [0.63, 0.71] / 0.674 [0.64, 0.72] |
| unit length T, median [IQR] | 744 [486, 975] / 807 [506, 1010] | 1940 [1570, 2250] / 1800 [1500, 2170] |
| noise variance capacity [Ah²] / φ | 4.57e-6, 0.915 / 1.95e-6, 0.926 | 1.06e-6, 0.948 / 9.43e-7, 0.919 |
| noise variance charge time [min²] / φ | **53.5**, 0.768 / 0.658, 0.900 | 1.45, 0.993 / 1.08, 0.988 |
| noise variance mean discharge V [V²] / φ | 4.96e-4, 0.971 / 4.18e-4, 0.961 | 3.55e-5, 0.984 / 2.34e-5, 0.974 |
| positive / negative residual runs per 100 positions (not enabled in either profile) | 0.12 / 0.10; 0.20 / 0.10 | 0.044 / 0.114; 0.156 / 0.116 |
| residual cross-channel correlation: relative Frobenius, mean \|Δρ\| | 0.68, 0.37 | 0.26, 0.12 |

NASA Table 2 rows:
- measured side void where counts fall below D02 (3 units reaching EOL < 5; regeneration events 3 < 10);
- noise rows: measured capacity variance 1.48e-4 (φ 0.15) vs generated 2.44e-4 (φ 0.51).

## Checks

9 pass, 0 warnings. Recorded per profile:
- window length and effective unit counts;
- discriminator accuracy below 0.99 (no trivial separation artefact: MATR 0.93, HUST 0.84);
- TSTR ratio finite.

Structural checks that also hold:
- no model input carries T or R: windows carry channel values and the elapsed position only;
- held-out units took no part in fitting (split from S3);
- bootstraps resample units, not windows.

## Anomalies

1. **MATR transfers poorly (3.42).** A model trained on the profile predicts measured RUL with 3.4× the error of one trained on measured cells, while trajectory-level properties (drift, T, family, capacity noise) match closely. The charge-time residual correlations and the band structure at S3 point to per-cell charging-policy offsets. They carry lifetime information in MATR, and the generator cannot express them, because its mappings are shared across units (paper §3.1). A reviewer will read this as the main fidelity limitation. It is a property that resists calibration (RQ1), not an implementation error. HUST, where cells share one charge protocol, transfers at 1.46.
2. **MATR held-out charge-time noise variance (53.5) is 65× its fitting-split value (0.82).** A few held-out cells have multi-cycle charge-time excursions that the isolated-reading rule (D17) does not remove. They also make the representation distance unreadable (bootstrap half-width 1.45 × value).
3. **The discriminator separates generated from measured windows in every readable profile** (error 0.05–0.20). This is the saturation the paper anticipates ("coarse indicator only").
4. **Generated residuals contain runs the detector finds at noise-level rates** (MATR 0.10 per 100 positions, HUST 0.11), although no patterns were inserted. This is consistent with D05's finding that measured MATR/HUST runs are at noise level.
5. **NASA PCoE is void on every Table 1 column** (D02b, D19). Cross-fitting over all 18 units gives 1.22 [1.06, 3.07], still unreadable, with the family changing across folds.

## Decisions needed

None for a human. Taken:
- D02b: per-measure held-out minima;
- D19: NASA fidelity void at the declared split.
