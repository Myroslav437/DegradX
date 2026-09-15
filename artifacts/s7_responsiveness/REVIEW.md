# Stage 7 — RQ3, responsiveness of the scores (paper §3.5.3; Tables 4–5, Figures 7–8)

## What ran

- Part one, no attribution method: `python scripts/s7_responsiveness.py --skip-part-two --device cpu`, 3 min.
  - The attribution ground truth of generated test units (generation seed 0) is degraded by the declared operators and
    magnitudes, and each score is computed on the degraded map.
  - Windows: 900 from 45 units in MATR and HUST; 706 from 39 units in NASA PCoE, of which 378 from 23 units carry
    inserted patterns.
  - Chance from a fully permuted map: rank −0.0006 / 0.0022 / −0.0009; retrieval 0.0496 (NASA PCoE).
- Part two, generator settings: `python scripts/s7_responsiveness.py --skip-part-one`, 32 min on GPU.
  - 57 setting values over the three profiles (noise variance, transition sharpness, sequence length, and pattern
    amplitude on NASA PCoE).
  - Per value: 150 generated units with that setting alone changed, split 0.7 / 0.15 / 0.15, one LSTM of configuration A
    trained with model seed 0, then Integrated Gradients on 10 windows per test unit and the exact attribution of the
    reference model on the same windows.
  - Each finished row is appended to `logs/part2_rows.jsonl`, so a restarted run resumes (the first attempt ran out of
    GPU memory in the validation pass at $L=96$; the validation chunk is now bounded by the window length).
- A second `--skip-part-one` pass, 36 s, recomputed the per-unit reference-model scores for the cached rows, ran the
  part-two checks and wrote the operating range.
- Decision harness: D20 (probe for the operating range), 6 CPU-min.

## What came out

| figure | what to look for |
|---|---|
| `<ds>_<weighting>_score_vs_degradation` | Each score against the magnitude of each operator; chance lines; the undegraded map at 1. |
| `score_vs_generator_settings` | Paper Figure 8: both probes against each setting, with the chance and saturation levels. |

**Table 4 (`tables/part1_degradation.json`), recency weighting:** smallest magnitude resolved (mean change there).

| score (profile) | added noise | mass to start | mass to end | smoothing | permuted fraction |
|---|---|---|---|---|---|
| rank agreement (MATR) | 0.05 (−0.115) | 0.05 (−0.009) | 0.05 (−0.000) | 0.5 (−0.000) | 0.05 (−0.041) |
| rank agreement (HUST) | 0.05 (−0.053) | 0.05 (−0.024) | 0.05 (−0.000) | 0.5 (−0.000) | 0.05 (−0.040) |
| rank agreement (NASA PCoE) | 0.05 (−0.115) | 0.05 (−0.020) | 0.05 (−0.000) | 0.5 (−0.006) | 0.05 (−0.041) |
| retrieval, paired (NASA PCoE) | 0.05 (−0.330) | 0.05 (−0.002) | 0.05 (−0.002) | 1 (−0.012) | 0.05 (−0.716) |
| retrieval, plain (NASA PCoE) | 0.05 (−0.004) | not resolved | 1 (−0.036) | 4 (−0.007) | 0.05 (−0.003) |

The mass-to-end and smoothing columns are resolved statistically at the smallest magnitudes while the score changes by
0.000 to 0.006: the paired bootstrap detects a consistent but negligible change. Plain retrieval scores the undegraded
map at 0.084 against a chance level of 0.050, so all of its resolutions lie inside that range.

Rank agreement is 0.997 / 0.999 / 0.967 at a smoothing width of 8 positions and changes by less than 0.001 for every
shift-to-end fraction below 1.

**Part two (`tables/part2_generator_settings.json`, `tables/operating_range.*`):**

| probe | rank agreement over the 57 values | paired retrieval (NASA PCoE, 23 values) |
|---|---|---|
| IG on the trained model | responsive everywhere (0.09–0.67) | saturated at 20 of 23 (raw 0.84–1.00) |
| reference model, exact | saturated at 6 values, responsive at 51 | 1 at every value by construction |
| accuracy gate | failed at NASA PCoE noise ×8 (0.334) and ×16 (0.361) | same two values |

Operating range (D20: both probes, plus the gate): the whole examined range for noise variance in MATR and HUST and for
sequence length in all three profiles; sharpness 1–4; NASA PCoE noise 0.25–4. Paired retrieval: void everywhere.

## Checks

220 checks, 218 pass, 2 warnings.
- Part one: the undegraded ground truth scores exactly 1 in rank agreement and in paired retrieval at every operator, and
  a fully permuted map scores at chance (D08).
- Part two: every declared setting value is measured; the recomputed per-unit reference-model scores reproduce the stored
  means at all 57 values (|diff| < 1e-9); the exact attribution retrieves the sparse set with paired AP 1 at every NASA
  PCoE value, which also confirms the pattern-free counterpart under amplitude overrides.
- The 2 warnings are the accuracy-gate failures above; by §3.5.2 the scores there are void, which is how Table 5 reports
  them.

## Anomalies

1. **Rank agreement does not register two failures.** Smoothing over 8 positions leaves it above 0.96, and mass shifted
   toward the end changes it by less than 0.001 below a full shift. Both follow from the shape of the graded field under
   recency weighting. Reported in §4.3 and in the Discussion.
2. **Plain retrieval is barely above chance on the correct map** (0.084 against 0.050), so it cannot serve as the
   retrieval measure. The paired score (D01) is the declared one.
3. **Paired retrieval on trained models is high at every setting** (≥ 0.84) although S6 shows the trained model does not
   use the pattern term. The paired score compares the map of a window with that of its pattern-free counterpart, so it
   registers input sensitivity rather than use of the term. This supports D21's void rather than contradicting it.
4. **Two isolated values cross the saturation level** (HUST noise ×0.5 at 0.966 and HUST $L=48$ at 0.956, with their
   neighbours at 0.92–0.95). Table 5 marks them instead of smoothing the interval.
5. **Equivalent runs differ.** The three rows at the default settings differ only in the unit split, and their rank
   agreement differs by up to 0.074 on the trained model and 0.049 on the reference model. Differences between settings
   below that are not readable.

## Decisions needed

None for a human. Taken: D20 (two probes plus the accuracy gate define the operating range).
