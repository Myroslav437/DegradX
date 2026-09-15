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

## S6 … S9

Filled in as each stage lands; see `scripts/run_all.sh` for the chained invocation.

## Git LFS policy

- Tracked by LFS (see `.gitattributes`): the compiled `paper/paper.pdf`, model checkpoints (`*.pt`,
  `*.ckpt`), generated-unit archives (`*.npz` under `data/generated/` and `results/`), and every figure
  under `artifacts/` (PNG and PDF).
- Size threshold: any other committed file larger than **1 MB** is added to `.gitattributes` before
  it is committed. Downloaded datasets are never committed (`data/` is ignored); `s1_fetch_data.py`
  and its checksums reproduce them.
- After every commit: `git push`, then `git rev-parse HEAD` must equal `git rev-parse @{u}`; when LFS
  files changed, `git lfs push --all origin main`.
