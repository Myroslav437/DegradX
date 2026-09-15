# D05 — Detection stays at k = 2.5 in every profile; a pattern type is enabled only if it is detected at least twice as often as on the profile's own fitted noise

**Stage / claim affected:**
- S3 step five and the enable rule of §3.3 ("a type that is not detected in a dataset is not enabled");
- which profiles carry a sparse set: S4 generation, the S6 graded/sparse checks, S7 retrieval responsiveness, and the S8 retrieval column;
- Table 2's regeneration rows.

**Decision.** The detection multiple is declared (k = 2.5) inside a sweep, and the brief asks for the operating point to be decided from the rate and amplitude curves. The measured question is whether what the detector finds in a profile exceeds what the profile's own noise produces.

**Options considered**
- **a. As declared:** k = 2.5 in every profile; a type is enabled if at least one run is detected.
- **b.** k = 3.0 in every profile; enabled if at least one run is detected.
- **c.** Per-profile k: the smallest grid value at which the measured positive rate is at least twice the noise-only rate.
- **d.** k = 2.5 in every profile; a type is enabled only if its measured rate is at least twice the rate the same rule returns on stationary AR(1) noise with the profile's fitted capacity-noise variance and lag-1 coefficient.

**Evidence** (`experiments/decisions/D05/{run.py,result.json,options.json}`)
- Measured rates come from the fitting splits of the S3 fit.
- Noise-only rates come from 200 simulated segments of the profile's median fitted length.

| profile (noise φ) | k | measured + / − per 100 positions | noise-only per sign | ratio + / − | positive events (fitting split) |
|---|---|---|---|---|---|
| MATR (0.94) | 2.0 | 0.205 / 0.160 | 0.408 | 0.50 / 0.39 | 163 |
| | **2.5** | 0.122 / 0.108 | 0.153 | **0.79 / 0.70** | 97 |
| | 3.0 | 0.082 / 0.078 | 0.033 | 2.44 / 2.33 | 65 |
| | 3.5 | 0.059 / 0.053 | 0.011 | 5.50 / 4.92 | 47 |
| HUST (0.94) | 2.0 | 0.084 / 0.309 | 0.391 | 0.22 / 0.79 | 86 |
| | **2.5** | 0.058 / 0.126 | 0.125 | **0.46 / 1.00** | 59 |
| | 3.0 | 0.056 / 0.051 | 0.030 | 1.86 / 1.69 | 57 |
| | 3.5 | 0.039 / 0.016 | 0.006 | 7.09 / 2.84 | 40 |
| NASA PCoE (0.47) | 2.0 | 1.460 / 0.584 | 0.353 | 4.14 / 1.66 | 10 |
| | **2.5** | 1.022 / 0.146 | 0.128 | **7.97 / 1.14** | 7 |
| | 3.0 | 0.438 / 0 | 0.019 | 22.8 / 0 | 3 |

Enabled types by option (`options.json`):
- **a:** both types in every profile.
- **b:** both types in MATR and HUST; positive only in NASA.
- **c:** k = 3.0 for MATR, 3.5 for HUST, 2.0 for NASA.
- **d:** positive only in NASA; none in MATR or HUST.

Real: all four run.

Works:
- At the declared k, MATR and HUST detections are fewer than their fitted noise alone produces (ratio < 1). Enabling on "at least one run" therefore generates noise as patterns, which is the failure the paper warns against (l.245: "a multiple set too low absorbs noise into the pattern distributions").
- NASA's positive runs occur 8× more often than its noise explains.

Clear, option (d): "A pattern type is enabled in a profile only if the detection rule finds it at least twice as often in the measured residuals as in noise simulated with the profile's own fitted variance and autocorrelation." The same k applies to every profile. Failure mode: the noise model is AR(1). Heavier-tailed or more strongly structured measured noise would make the noise-only rate an underestimate, so the rule errs toward enabling.

**Chosen: d.**
1. *Logical:* it turns the paper's stated concern into the rule itself. Detection counts only what the fitted noise cannot explain. It favours no attribution method.
2. *Consistent:*
   - paper l.241 requires "the same rule has to apply to every profile", which rules out (c);
   - l.253 includes NASA for "one property the others lack", which (d) reproduces on the data and (a)/(b) contradict;
   - k stays at its declared value.
3. *Clear:* one sentence and one declared factor (2).
4. *Measured:* separates the profiles by 8.0 against 0.79/0.46 at the declared k.

**Cost.**
- **MATR and HUST profiles carry no inserted patterns.** Their sparse set is empty. The following are therefore void on those two profiles, with this reason: sparse-set retrieval scores, graded/sparse correlation, and the pattern-term ablation.
- Everything that concerns the sparse set rests on the NASA PCoE profile. Its positive type is fitted from 7 fitting-split events (D02: too few to report amplitude and duration statistics, but used for generation).
- A reviewer could argue that k = 3.0 would have enabled patterns in MATR and HUST at ratio ≈ 2. That was option (b), with enabling on any detection. Under (d)'s criterion at k = 3.0, MATR would enable both types (2.4 / 2.3) and HUST neither (1.86 / 1.69). Changing k after seeing these curves would fit the threshold to the result.
- The sweep is reported in full (S3 `tables/detection_sweep.csv`).

**Paper impact:** §3.3 detection paragraph: the enable clause becomes "detected at least a declared factor more often than on the profile's fitted noise" (round-3 amendment).
