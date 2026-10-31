# DegradX

DegradX is a dataset-calibrated synthetic testbed for evaluating feature attribution on degrading systems.

A generator is fitted to a measured battery-degradation dataset; each fitted configuration is called a *profile*. The
generated multivariate sequences carry a regression target that is an exact additive function of a nonstationary mean
component and of localized patterns inserted at known positions. The contribution of every observation to the target is
therefore known by construction. This gives two kinds of attribution ground truth: a dense graded field from the mean
component, and a sparse set of positions that carry the inserted patterns. An evaluation protocol reports, for each
profile:

- its fidelity to the dataset it stands for;
- whether models trained on the generated data can use the ground truth;
- how attribution scores respond to controlled degradations of an attribution map;
- reference values for Integrated Gradients, feature occlusion and TimeSHAP.

This repository contains the generator, the fitted parameters, the seeds, the trained models, the code that produces
the ground truth and the scores, and the code and outputs behind every reported number.

## Citation

> M. Mishchuk, R. Cupek, O. Pavliuk. *DegradX: A Dataset-Calibrated Synthetic Testbed for Attribution Evaluation on
> Degrading Systems.* Asian Conference on Intelligent Information and Database Systems (ACIIDS 2027),
> <https://aciids.pwr.edu.pl/2027/>. Submitted.

```bibtex
@inproceedings{mishchuk2027degradx,
  title     = {{DegradX}: A Dataset-Calibrated Synthetic Testbed for Attribution Evaluation on Degrading Systems},
  author    = {Mishchuk, Myroslav and Cupek, Rafa{\l} and Pavliuk, Olena},
  booktitle = {Asian Conference on Intelligent Information and Database Systems (ACIIDS 2027)},
  year      = {2027},
  note      = {Submitted}
}
```

GitHub's "Cite this repository" button reads the same entry from [`CITATION.cff`](CITATION.cff).

## Profiles

| profile | dataset | cells (fitting / held-out) | notes |
|---|---|---|---|
| **MATR** | Severson et al., *Nature Energy* 2019, the three batches of that paper | 135 (95 / 40) | |
| **HUST** | Ma et al., *Energy & Environmental Science* 2022 | 77 (54 / 23) | the profile against which fidelity is primarily read |
| **FORM** | Cui et al., *Joule* 2024 (TRI/Stanford formation dataset) | 182 (127 / 55) | the only profile with an inserted pattern type (capacity recovery after diagnostic blocks) |

## Getting the benchmark data

The generated units with their ground truth are distributed as a self-contained bundle, `DegradX-benchmark.zip`, attached
to this repository's [Releases](../../releases). It holds 3 profiles × 3 generation seeds × 300 units, split
210 / 45 / 45 (train / validation / test) at unit level. Its `README.md` is a full datasheet. The bundle contains:

- `<PROFILE>/seed<g>.npz`: the exact decomposition of every unit: degradation state `z`, mean component `m`, inserted
  patterns `p`, noise `eps`.
- `profiles/<PROFILE>.json`: the fitted parameters.
- `<PROFILE>/evaluation_windows.csv`: the 120 test windows scored in the reported reference values.
- `degradx_benchmark.py`: a NumPy-only loader that rebuilds, for any window, the input `x`, the target `y` and the
  ground truth `phi*` (graded and sparse parts).
- `scores.py`: the scoring functions.
- `manifest.json` and `SHA256SUMS`.

```python
from degradx_benchmark import load      # run inside the unpacked bundle

b = load("FORM", seed=0)
unit = b.units("test")[0]
w = b.windows(unit, "recency")          # every full window of the unit
w["x"].shape, w["y"].shape, w["phi_star"].shape   # (n, 24, C), (n,), (n, 24, C); phi_star sums to y exactly
```

### Building the bundle yourself

The units are not committed. They regenerate bit-identically from the fitted profiles and the seeds. The only exception
is the `null_permuted` channel, which draws from measured charge-time readings, so the measured data are needed once:

```bash
bash scripts/setup_env.sh && source .venv/bin/activate
bash scripts/run_all.sh                     # full pipeline (see below); or only the stages up to S10
python scripts/export_benchmark.py          # -> dist/DegradX-benchmark/ and dist/DegradX-benchmark.zip
```

`export_benchmark.py` reads the generated units from `data/generated/`. It checks the
bundled loader against the library's own target code on every window, with exact equality. It then writes the
datasheet, the manifest and the checksums. Options: `--profiles FORM --seeds 0` for a subset, `--no-archive`.

## What is where

| component | location |
|---|---|
| generator (Eq. 1–3: state, mean component, inserted patterns, noise) | [`src/degradx/generator/`](src/degradx/generator) |
| profile fitting (trajectory families, channel mappings, noise, pattern detection, per-unit offsets) | [`src/degradx/fitting/`](src/degradx/fitting) |
| decomposable target, attribution ground truth, reference model | [`src/degradx/targets/decomposable.py`](src/degradx/targets/decomposable.py) |
| scores (rank agreement, channel allocation error, temporal profile error, zero-weight mass, retrieval) and degradation operators | [`src/degradx/metrics/scores.py`](src/degradx/metrics/scores.py) |
| fidelity (TSTR, discriminative error, covariance agreement) and usability measures | [`src/degradx/metrics/`](src/degradx/metrics) |
| attribution methods (IG, occlusion, TimeSHAP) | [`src/degradx/attribution/`](src/degradx/attribution) |
| LSTM regressor | [`src/degradx/models/lstm.py`](src/degradx/models/lstm.py) |
| declared constants (window length, weights, position profiles, EOL threshold, seeds, rules) | [`configs/declarations.yaml`](configs/declarations.yaml) |
| dataset-level facts (nominal capacity, channels) | [`configs/profiles/`](configs/profiles) |
| raw-file checksums | `configs/raw_checksums*.sha256` |
| **fitted parameters (profiles)** | `artifacts/s09_fit_profiles/profiles/{MATR,HUST,TRI_FORMATION}.json` |
| fitted parameters of the baseline generator (no offsets; comparison rows) | `artifacts/s05_fit_baseline/profiles/{MATR,HUST}.json` |
| **trained models** (10-member LSTM ensemble per profile and weighting) | `artifacts/s13_usability/models/` (Git LFS) |
| per-unit tables of the generated units (length, source unit, split, pattern count) | `artifacts/**/tables/generated_units_<PROFILE>_seed<g>.csv` |
| **results** (every reported table and figure) | [`results/`](results) |
| stage scripts | [`scripts/`](scripts) |

Git LFS stores the trained models. Run `git lfs install` before cloning, or `git lfs pull` after cloning.

### Seeds

Every random stream derives from the base seed `20260915` through `degradx.utils.seeding.derive_seed(base, source, *keys)`:

- generation seeds 0, 1, 2 (300 units each);
- model-initialization seeds 0–4 (architectures A: 64×2 and B: 128×1, giving 10 ensemble members);
- attribution-sampling seeds 0, 1, 2 (TimeSHAP);
- the evaluation stream (window selection, bootstraps), which uses 10 000 BCa resamples over units.

Each stage records its seeds in `logs/run*.json`, together with the command line, package versions, device and wall
clock.

### Trained models

```python
import torch
from degradx.models.lstm import LSTMRegressor, Standardiser, TrainedModel

ck = torch.load("artifacts/s13_usability/models/TRI_FORMATION_recency_A_seed0.pt", map_location="cpu", weights_only=False)
net = LSTMRegressor(len(ck["channels"]), ck["arch"]["hidden_size"], ck["arch"]["num_layers"])
net.load_state_dict(ck["state_dict"])
sc = ck["scaler"]
model = TrainedModel(net, Standardiser(sc["mean"], sc["std"], sc["y_mean"], sc["y_std"]))
y_hat = model.predict(X)        # X: (n, L, C) windows, channels in ck["channels"] order
```

Member `A_seed0` is the primary model of each profile and weighting. `recency` is the primary weighting; `uniform` is
the sensitivity weighting.

## Results

`results/` holds one JSON per reported table, with the values and their source artifacts:

| file | content |
|---|---|
| `table1_fidelity.json` | fidelity: discriminative error, covariance agreement, TSTR transfer ratio (with and without correlated noise, and the generator without offsets) |
| `table2_properties.json` | property table: fitting split, held-out split, generated units |
| `table3_tstr_isolation.json` | TSTR ratio by input set |
| `table4_usability.json` | accuracy gate, null-channel leakage, channel use, offset and pattern terms |
| `table5_scores.json` | degraded-map test: the magnitude at which each score registers each degradation |
| `table6_reference_values.json` | IG, occlusion and TimeSHAP on trained and reference models; ten-member ensemble ranges |
| `profile_facts.json` | numbers reported about the FORM profile (eligibility, audit, offset share, inserted patterns) |
| `fig_res_fidelity.png`, `fig_res_degradation.png`, `fig_res_floor.png` | measured vs generated trajectories; scores vs degradation; scores vs ensemble range |
| `provenance.json` | for every table cell and figure: source artifact, key, producing script and seeds |

`python scripts/s16_export_results.py` rebuilds all of them from the committed artifacts. Only
`fig_res_fidelity.png` also needs the measured and generated data.

## Reproducing everything

Requirements: Linux, Python 3.12 and a CUDA GPU. The reference machine had 16 cores, a GTX 1660 Ti (6 GB) and 15 GB
RAM. Any stage also runs with `--device cpu`, more slowly. Disk: about 12 GB for the MATR / HUST raw data,
plus the TRI formation archives and the processed tables. PyTorch comes from the CUDA 13.0 wheel index; the
exact versions are in `requirements-lock.txt`.

```bash
bash scripts/setup_env.sh             # .venv with the locked dependencies and an editable degradx; prints a check
source .venv/bin/activate
bash scripts/run_all.sh               # ~10 h of compute + downloads; DEGRADX_FROM=s09 resumes, DEGRADX_WORKERS=<n> pool size
```

`scripts/run_all.sh` runs the stages in order, with the arguments that produced the committed artifacts. Each stage
`scripts/sNN_<name>.py` writes `artifacts/sNN_<name>/`:

| stage | what it does |
|---|---|
| S01 `s01_ingest_matr_hust` | fetch MATR and HUST (checksums verified), ingest into BatteryML objects, per-cycle channel tables |
| S02 `s02a/b/c_*_form` | fetch, extract and ingest the TRI/Stanford formation dataset (FORM) |
| S03 `s03_audit_matr_hust` | property audit of MATR and HUST: EOL attainment, monotonicity, families, pattern detection |
| S04 `s04_audit_form` (+ `s04b`) | FORM audit, eligibility, offset pre-screen, mechanism diagnostic of its capacity recovery |
| S05 `s05_fit_baseline` | baseline fit (no per-unit offsets) and the measured fitting / held-out split |
| S06 `s06_generate_baseline` | baseline generator: units and construction checks |
| S07 `s07_fidelity_baseline` | fidelity of the baseline generator (comparison rows of Table 1) |
| S08 `s08_tstr_isolation_baseline` | TSTR by input set on the baseline profiles (Table 3) |
| S09 `s09_fit_profiles` | profiles with per-unit offsets and correlated noise (MATR, HUST, FORM) |
| S10 `s10_generate_units` | generated units (3 seeds × 300, and the set without correlated noise) and construction checks |
| S11 `s11_fidelity` (+ `s11b`) | fidelity: TSTR, discriminative error and its readability, covariance, property table (Tables 1–3) |
| S12 `s12_tstr_without_correlated_noise` | TSTR of MATR and HUST without correlated noise (Table 1) |
| S13 `s13_usability` | LSTM ensembles: accuracy gate, null-channel leakage, channel use, offset and pattern terms (Table 4) |
| S14 `s14_degraded_map_test` | scores against controlled degradations of the ground truth (Table 5, Figure 7) |
| S15 `s15_reference_values` | IG, occlusion and TimeSHAP on trained and reference models, ensemble ranges (Table 6, Figure 8) |
| S16 `s16_export_results` | `results/` |

Stages S09–S15 run once for MATR and HUST and once for FORM. Both runs write the same stage directory, and their run
records and checks carry the dataset group (`*_MATR_HUST`, `*_TRI_FORMATION`).

Measured datasets are not redistributed. The fetch stages download them from their primary releases and verify them
against `configs/raw_checksums*.sha256`. Every stage script takes `--config --out-dir --seed --device {cuda,cpu}
--dry-run --force`. A stage skips work whose outputs exist unless `--force` is given, writes `tables/checks*.{json,csv}`,
and exits non-zero when a check fails.

Each stage directory under `artifacts/` holds:

- `tables/`: the stage's measurements and checks;
- `profiles/`: the fitted parameters;
- `models/`: the trained models;
- `logs/run*.json` and `logs/timing*.json`: the run records.

Data written by the stages live under `data/` (not committed): `raw/`, `processed/` (cycle tables), `generated/` (units
of S10), `generated_baseline/` (units of S06) and `attributions/` (maps and TimeSHAP checkpoints of S15).

The `declarations_sha256` in a run record is the hash of `configs/declarations.yaml` at run time. The file has since been
edited in its comments, key names and section names; the declared values are unchanged.

## Licence of derived data

- **TRI/Stanford formation profile (FORM).** The profile parameters and the generated units derived from the
  TRI/Stanford formation dataset are released under **CC BY-NC 4.0**
  (<https://creativecommons.org/licenses/by-nc/4.0/>), the licence of the source data. This covers
  `artifacts/s09_fit_profiles/profiles/TRI_FORMATION.json` and the units generated from it. Attribution: X. Cui,
  S. D. Kang, S. Wang, J. A. Rose, H. Lian, A. Geslin, S. B. Torrisi, M. Z. Bazant, S. Sun, W. C. Chueh, *Data-driven
  analysis of battery formation reveals the role of electrode utilization in extending cycle life*, Joule 8(11),
  3072–3087 (2024); data: Toyota Research Institute, <https://data.matr.io/8/> (version of 2025-03-03).
- **Other profiles.** Profiles derived from other datasets follow the licences of their sources.

`src/degradx/metrics/ts2vec/` is vendored from TS2Vec under its own licence (see the `LICENSE` file in that directory).
