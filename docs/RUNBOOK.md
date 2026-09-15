# RUNBOOK

Copy-pasteable commands for every stage, from the repository root. Every stage script takes
`--config --out-dir --seed --device {cuda,cpu} --dry-run --force`, skips completed work unless
`--force`, writes `artifacts/s{N}_*/logs/{run,timing}.json`, and exits non-zero on a failed check.

## S0 — environment and toolchain

```bash
bash scripts/s0_setup_env.sh        # venv (.venv), locked deps, editable degradx, TinyTeX (.tools/.TinyTeX)
source .venv/bin/activate
export PATH="$PWD/.tools/.TinyTeX/bin/x86_64-linux:$PATH"   # pdflatex, bibtex, latexdiff
pytest -q
```

- PyTorch comes from `https://download.pytorch.org/whl/cu130` (sm_75 verified on GTX 1660 Ti).
- CPU fallback: pass `--device cpu` to any stage.

## Paper build

```bash
cd paper && pdflatex paper && bibtex paper && pdflatex paper && pdflatex paper
```

The preamble switch `\reviewtrue` / `\reviewfalse` toggles highlighting of amended spans.

## S1 — data acquisition

```bash
python scripts/s1_fetch_data.py --device cpu --workers 4        # fetch/verify, ingest, cycle tables, checks, figures
python scripts/s1_fetch_data.py --no-download                    # print the manual file tree instead of downloading
python scripts/s1_fetch_data.py --rehash                         # recompute SHA-256 of raw files
```

- Needs ~12 GB for raw data, ~12.5 GB for `data/processed/`, ~5 GB RAM per MATR batch process, and ~4.3 GB of temporary
  disk for BatteryML's HUST extraction.
- MATR runs one batch per child process (b2, b1, b3, b4). A batch whose `data/work/matr_b<k>_log.json` exists is skipped
  unless `--force`.

## S2 — dataset property audit

```bash
python scripts/s2_audit_datasets.py --workers 12              # all three datasets, ~2 min
python scripts/s2_audit_datasets.py --datasets NASA_PCoE      # one dataset
python experiments/decisions/D12/run.py                        # decision harnesses (D11-D16) re-run standalone
```

## S3 — profile fitting

```bash
python scripts/s3_fit_profiles.py --workers 12                 # ~1 min; profiles/<dataset>.json
python scripts/s3_fit_profiles.py --datasets NASA_PCoE
```

## S4 — generator and ground truth

```bash
python scripts/s4_generate_units.py --workers 12              # 3 seeds x 300 units per profile, checks, figures, rho sweep (~15 min)
python scripts/s4_generate_units.py --skip-rho                 # without the rho-sensitivity refits
```

Generated units are cached in `data/generated/<profile>/seed<g>.pkl` and regenerate bit-identically from the seeds.

## S5 — fidelity

```bash
python scripts/s5_fidelity.py                                  # ~13 min on GPU
python experiments/decisions/D02b/run.py; python experiments/decisions/D19/run.py
```

## S6 — usability

```bash
python scripts/s6_usability.py --datasets MATR HUST            # ~2.4 h on GPU: 10 ensemble members x 3 weightings, ablations
python scripts/s6_usability.py --datasets NASA_PCoE            # ~4 min
python experiments/decisions/D21/run.py                        # pattern amplitude multipliers (NASA), ~40 min
```

Models are saved to `artifacts/s6_usability/models/<profile>_<weighting>_<A|B>_seed<s>.pt` (LFS); S8 loads them. A run
per dataset group writes its own `usability_<profile>.json`; the checks of the MATR/HUST run are kept as
`tables/checks_MATR_HUST.*`.

## S7 — responsiveness

```bash
python scripts/s7_responsiveness.py                            # part one (~3 min, CPU) and part two (~35 min, GPU)
python scripts/s7_responsiveness.py --skip-part-one            # part two only, reusing tables/part1_degradation.json
python scripts/s7_responsiveness.py --skip-part-two
```

Part two trains one LSTM per (profile, setting, value) and appends each finished row to `logs/part2_rows.jsonl`; a
restarted run skips cached rows. Delete that file to recompute from scratch.

## S8 — reference values

```bash
for ds in MATR HUST NASA_PCoE; do                              # ~2.5 h (MATR, HUST), ~1.5 h (NASA; paired maps)
  python scripts/s8_reference_methods.py --datasets $ds --timeshap-windows 40 --timeshap-seeds 0 1 \
      --timeshap-seeds-reference 0 --secondary-background     # D23 budget
done
python scripts/s8_reference_methods.py --checks-only           # checks over all profiles (each run overwrites checks.md)
```

Runs merge into `tables/reference_values.json`; raw maps go to `data/attributions/` (not committed).
`experiments/s8_matr_exact_subset.py` added the exact-attribution ceiling on the TimeSHAP window subset to the MATR entry,
which ran before the script computed it; the current script computes it directly.

## S9 — results and paper

```bash
python scripts/s9_write_paper.py --tables fidelity properties figure_fidelity resolution figure_degradation usability \
    range figure_range reference                               # results/*.json, paper/tables/*.tex, paper/img/fig_res_*.pdf,
                                                               # docs/RESULTS_PROVENANCE.md
bash scripts/build_paper.sh                                    # paper.pdf (review) and paper_clean.pdf
bash scripts/latexdiff_round.sh <commit-before-round> round<N> # artifacts/amendments/round<N>_diff.pdf
```

`scripts/run_all.sh` chains S1–S9 with these invocations (`DEGRADX_FROM=s6` resumes from a stage).

## Git LFS policy

- Tracked by LFS (see `.gitattributes`): the compiled `paper/paper.pdf`, model checkpoints (`*.pt`,
  `*.ckpt`), generated-unit archives (`*.npz` under `data/generated/` and `results/`), and every figure
  under `artifacts/` (PNG and PDF).
- Size threshold: any other committed file larger than **1 MB** is added to `.gitattributes` before
  it is committed. Downloaded datasets are never committed (`data/` is ignored); `s1_fetch_data.py`
  and its checksums reproduce them.
- After every commit: `git push`, then `git rev-parse HEAD` must equal `git rev-parse @{u}`; when LFS
  files changed, `git lfs push --all origin main`.
