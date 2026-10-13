# W8 — reference values on FORM, with paired maps (V8 design; brief "DegradX v2.1", 2026-10-13)

## What ran

- **Command.** `scripts/v2/v8_reference_methods.py --datasets TRI_FORMATION --out-dir artifacts/v2.1/w8_reference_methods`,
  in four modes. The models are the W6 ensembles; the TimeSHAP checkpoints are under `data/v2.1/attributions` (gitignored).
  - `--benchmark` (12 CPU workers, chunk 4096: 1 920 windows/h).
  - `--equivalence --project`: the parallel runner against the sequential path, max |diff| 0. Projection 4 680 jobs =
    2.44 h, within the 36 h ceiling.
  - `--run`: 4 680 TimeSHAP jobs, 02:46–04:04, **1.31 h**.
  - `--score`: CUDA, 21 s.
- **Design (r3 `v2.timeshap_full_scale`, unchanged).**
  - 120 windows of the 45 generated test units, generation seed 0.
  - IG, feature occlusion and TimeSHAP (seeds 0, 1, 2) on the primary trained model and on the reference model, under
    recency and uniform weighting.
  - The ensemble floor on all ten members, with TimeSHAP under recency only.
  - TimeSHAP from the average event, as the secondary readout.
- **New for this profile: paired maps.** FORM carries inserted patterns, so every method also explains each window's
  pattern-free counterpart. That gives 4 680 explanations instead of 2 880. Paired retrieval is the AP of
  map(x) − map(x without patterns) against the sparse set. The floor runs on the counterpart only.

## Results (`tables/reference_values.json`; recency unless stated)

| | IG | occlusion | TimeSHAP | exact w(x − x⁰) |
|---|---|---|---|---|
| rank agreement, trained | 0.770 [0.723, 0.806] | 0.744 [0.696, 0.783] | 0.771 [0.725, 0.808] | **0.849** [0.795, 0.891] |
| allocation error, trained | 0.215 | 0.265 | 0.220 | **0.125** |
| temporal error [positions], trained | 3.89 | 3.71 | 3.82 | **0.63** |
| zero-weight mass, trained | 0.039 | 0.048 | 0.039 | 0 |
| ensemble range, rank | 0.438–0.776 | 0.431–0.753 | 0.458–0.779 | — |
| ensemble range, allocation | 0.196–0.257 | 0.229–0.271 | 0.194–0.262 | — |
| ensemble range, temporal | 2.97–3.89 | 3.19–3.71 | 2.82–3.82 | — |

- **Reference model: exact.** Max |method − w(x − x⁰)|:
  - IG 4.6e-8, occlusion 1.4e-7, TimeSHAP ≤ 2.4e-5;
  - against a max |exact| of 0.056 (recency) and 0.021 (uniform).
  - The method columns on the reference model equal the ceiling to 3 decimals; TimeSHAP's rank is 0.850.
- **Floor (X7): no ordering is supported in FORM, in any score, under either weighting.**
  - Rank: largest method gap 0.027 against ranges of 0.32–0.34.
  - Allocation: gap 0.050 (occlusion vs IG) against ranges of 0.061 (IG), 0.042 (occlusion) and 0.068 (TimeSHAP).
  - Temporal: gap 0.18 against 0.52–1.01.
  - The primary model sits near the top of its ensemble in rank agreement: the ten FORM models disagree far more
    than the MATR (0.10–0.12) or HUST (0.15–0.21) ensembles do.
- **Paired retrieval** (r4 `readings.sparse_set_trained`). It is computed on the 11 test units whose sampled windows
  contain the sparse set.
  - **Reference model: 1.00 for every method.** The pattern term is part of the reference function, so the paired
    difference is w·p.
  - **Trained model: void.** W6's pattern-term ablation is 0.0000 [−0.0001, 0.0002]. The computed values (IG 0.84,
    occlusion 0.82, TimeSHAP 0.94) are not printed. They show that the attribution changes where the input changes,
    not that the model uses the pattern for y.
  - On minimum counts: the reference value has zero interval width, which meets `statistics.minimum_counts.criterion`.
- **TimeSHAP sampling.** Unit means differ across seeds by at most 0.0024 in rank, 0.001 in allocation and 0.006
  positions in temporal error.
- **The D23 subset** (40 of 120 windows) means lie inside the 120-window intervals in every TimeSHAP cell, for both
  models and both weightings (`x7_values_hold` all true).
- **Average-event background** (TimeSHAP, its own ground truth):
  - rank 0.771 → 0.740, allocation 0.220 → 0.247, temporal 3.82 → 3.57;
  - TimeSHAP moves from first to last in rank, within the floor.
- **Uniform weighting**, on the models trained for it:
  - rank falls to 0.532–0.570, against a ceiling of 0.826. MATR and HUST changed by at most 0.04, so this is the
    largest weighting effect of the three profiles;
  - allocation 0.222–0.262 (changes ≤ 0.013);
  - temporal 3.63–4.25, against a ceiling of 0.82 and a permuted ground truth of 1.77 (W7). Above chance, as in MATR
    and HUST.
  - The method order changes in every score, by less than the floor.

## Checks

`logs/checks.md`: 13 of 13 pass. They cover IG and occlusion exactness and TimeSHAP reproduction on the reference model
(per seed and weighting), and all declared TimeSHAP jobs being present. The run's own benchmark, equivalence and projection
logs are `logs/stdout_bench.log`, `stdout_eq.log` and `stdout_run.log`. `timing.json` and `run.json` record the last
mode run (`--score`).

## Paper

- **Table 6** gains FORM's block, with paired retrieval in the note (reference 1.00; trained void, with the reason).
- **Figure 8** gains FORM's row.
- **§4.4**: FORM's ceiling, floor and retrieval, and the uniform-weighting drop.
- **§5 "What the benchmark can adjudicate"**: FORM's floor and the sparse set on the reference model.
