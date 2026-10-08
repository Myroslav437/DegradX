# V8 — reference values for IG, feature occlusion and TimeSHAP at full scale (X7)

## What ran

- **Command.** `python scripts/v2/v8_reference_methods.py --datasets MATR HUST`, seed 20260915. The modes ran in the
  declared order, 2026-10-08:
  - `--profile-window`, `--benchmark`, `--equivalence --project`: 11:14–11:33;
  - `--run`: 11:33–13:16;
  - `--score`: 13:16–13:17.
- **Machine state.** No other job ran during the profile and the benchmark. V9 trained on the GPU during the run, which
  the brief allows "whenever the GPU is idle": TimeSHAP evaluated its models on the CPU, so it did not share the GPU.
- **Windows.** 120 per profile, from 45 V4 test units (generation seed 0), drawn with v1's seeded rule
  (`evaluation/s8/<profile>`). Pristine baseline (C4), with the real `null_permuted` pool.
- **TimeSHAP.** Run as declared: nsamples 32 000, `l1_reg` 'auto', cell level, no pruning. No D23 reduction: windows,
  seeds and nsamples are all as declared.
  - Per profile: trained A/seed 0 and the reference model × seeds 0, 1, 2 × recency and uniform (1 440 explanations).
  - Average-event background on the trained model × 3 seeds × recency (360).
  - Ensemble floor: the other nine V6 members × seed 0 × recency (1 080). A0's floor maps are its primary seed-0 maps.
  - In total, 2 880 explanations per profile and 5 760 over both. Checkpointed per window in
    `data/v2/attributions/timeshap_ckpt` (gitignored, 23 MB), with a manifest.
- **IG and occlusion** (captum, declared configurations): on the primary and reference models and on all ten members,
  under both weightings.
- **Scores.** Rank agreement, channel allocation error, temporal profile error and zero-weight mass, as unit means over
  the 45 test units with 95 % BCa (10 000 resamples).
  - X4 void rule: no weighted channel is unused on any primary model (V6), so nothing is voided.

## Feasibility (`tables/feasibility.json`)

**Profile of one window (MATR, A0):** 6.6 s. Coalition sampling takes 74 %, LassoLarsIC 12 %, the solve 8 % and model
evaluation 3 %. TimeSHAP's cost is CPU-bound Python, not the model.

**Throughput benchmark** (windows/h; at least 4 windows per worker):

| workers | 1 | 2 | 4 | 6 | 8 | 12 |
|---|---|---|---|---|---|---|
| CPU, chunk 4096 | 434 | 741 | 1 196 | 1 585 | 1 745 | **1 932** |
| CUDA model evaluation | 563 | 891 | 1 442 | 1 879 | out of memory | — |

- **Chunk size.** 1024 / 16384 / 32768 at 8 CPU workers: 1 847 / 1 612 / 1 575. At 6 CUDA workers: 1 853, and out of
  memory for the two larger chunks.
- **Chosen:** 12 CPU workers, chunk 4096.
- **The earlier benchmark is superseded.** It was measured before the baseline and thread fixes and is kept in
  `logs/feasibility_superseded_2026-10-08.json`.

**Equivalence** (20 windows, sequential vs 12 workers): maximum absolute difference **0** (≤ 1e-10 required). The first
window also matches v1's in-process code path exactly.

**Projection:** 5 760 jobs at 1 932/h = **2.98 h** (threshold 36 h). **Actual:** 1.71 h at 3 376/h. The reference-model
jobs are cheaper than the benchmark's trained-model windows.

## What came out (`tables/reference_values.json`; Table 6 and Figure 8 via V10)

**Recency, unit means [95 % BCa]:**

| | MATR rank | MATR alloc. | MATR temporal | HUST rank | HUST alloc. | HUST temporal |
|---|---|---|---|---|---|---|
| exact w(x − x⁰), reference model | 0.869 [0.817, 0.909] | 0.075 | 0.38 | 0.957 [0.922, 0.978] | 0.063 | 0.18 |
| IG, trained | 0.485 [0.445, 0.519] | 0.294 | 1.86 | 0.734 [0.700, 0.758] | 0.164 | 2.82 |
| occlusion, trained | 0.420 [0.368, 0.466] | 0.377 | 2.56 | 0.750 [0.715, 0.776] | 0.182 | 2.93 |
| TimeSHAP, trained (seed 0) | 0.493 [0.454, 0.527] | 0.301 | 1.82 | 0.739 [0.705, 0.764] | 0.176 | 2.86 |
| ensemble range IG / occl. / TimeSHAP, rank | 0.41–0.51 / 0.33–0.45 / 0.42–0.51 | | | 0.60–0.75 / 0.57–0.77 / 0.60–0.78 | | |
| TimeSHAP, average-event background | 0.527 | 0.313 | 2.21 | 0.697 | 0.156 | 2.85 |
| zero-weight mass, trained (IG / occl. / TimeSHAP) | 0.134 / 0.198 / 0.136 | | | 0.037 / 0.040 / 0.038 | | |

- **Reference model.** IG, occlusion and TimeSHAP equal the exact attribution. The largest absolute difference in the
  maps, MATR / HUST, against max|w(x − x⁰)| of 0.02–0.08:
  - IG ≤ 1.1e-8 / 7.5e-8;
  - occlusion ≤ 1.1e-7 / 1.8e-7;
  - TimeSHAP ≤ 1.8e-5 / 2.5e-5.

  This is the declared correctness check, not a finding.
- **TimeSHAP's seed spread** is at most 0.002 in rank agreement and 0.02 positions in the temporal error, on every
  profile and weighting.

**Declared readings:**
- **X7_values_hold** (the 40-window D23 subset mean lies inside the full 120-window interval):
  - holds on MATR, both weightings, every score, trained and reference;
  - holds on HUST recency;
  - fails on two HUST uniform cells: trained temporal error (subset 3.56 against [3.03, 3.53]) and reference
    allocation error (0.051 against [0.052, 0.080]).

  On the primary weighting, then, the v1 values were not an artefact of the reduced design. Under uniform weighting
  on HUST, two cells of the subset fall just outside.
- **X7_floor** (ten-member range against the largest gap between the three methods on the primary model):

  | | rank: gap / ranges | allocation: gap / ranges | temporal: gap / ranges |
  |---|---|---|---|
  | MATR recency | 0.073 / 0.10, 0.12, 0.10 → **no ordering** | **0.083 / 0.054, 0.039, 0.051 → ordering supported** | 0.74 / 0.87, 1.03, 0.72 → no ordering |
  | HUST recency | 0.016 / 0.15, 0.21, 0.18 → no ordering | 0.018 / 0.093, 0.098, 0.094 → no ordering | 0.11 / 1.17, 0.73, 1.20 → no ordering |

  Under uniform weighting the IG and occlusion floors give the same pattern. MATR allocation is supported (gap 0.072
  against ranges 0.071 and 0.057); everything else is not.
- **The one ordering the floor supports:** on MATR, feature occlusion allocates attribution to the wrong channels more
  than IG and TimeSHAP do (0.377 against 0.294 / 0.301). This holds under both weightings, and the gap exceeds every
  member's range.
  - It is the only method difference in v2 that survives a change of model.
  - Rank agreement and the temporal error support no ordering on either profile, and neither does any score on HUST.

## Checks

22 pass, 0 warnings, 0 failures (`logs/checks.md`):
- IG and occlusion equal w(x − x⁰) on the reference model;
- TimeSHAP reproduces it (reported at 1e-2);
- every declared TimeSHAP job is present;
- the equivalence check passes (recorded in `feasibility.json`).

## Anomalies

1. **Trained-model scores rose sharply on HUST against v1** (rank agreement 0.33 → 0.74). The v1 models read capacity
   alone (V6), so two thirds of the ground truth sat on channels the model ignored. With X2, the models read every
   weighted channel, and the maps agree with ϕ* where the target lives.
2. **MATR's zero-weight mass stays high** (0.13–0.20). The trained MATR models put some attribution on the redundant
   channels: internal resistance carries the state with R² 0.75 from the others (V6). This is the non-identifiability
   the floor measures.
3. **The average-event background moves the scores by up to 0.04 in rank and 0.4 positions in temporal error**, not
   in the same direction on both profiles. A reference value is quoted with its baseline.

## Decisions needed

None.
