# S0: DegradX Python environment and LaTeX toolchain

Date: 2026-09-15. Machine: Linux, Python 3.12.3 (`/usr/bin/python3.12`), NVIDIA GeForce GTX 1660 Ti (compute capability 7.5), driver 595.84, driver CUDA 13.2 (`nvidia-smi`).
Scratch evidence directory: `/tmp/claude-1000/-home-mmishchuk-projects-DegradX/e1767cc0-419f-4700-b388-11290dc5e816/scratchpad/s0_research/env/` (called `$E` below). Every test script and log mentioned here is in that directory.

## 0. Summary of decisions

| Item | Decision | Evidence |
|---|---|---|
| Main venv | `/home/mmishchuk/projects/DegradX/.venv`, stdlib `venv` + pip 26.2.1 | §1 |
| Torch | `torch==2.14.0+cu130` from `https://download.pytorch.org/whl/cu130` | arch list contains `sm_75`; §2 |
| numpy | **1.26.4** (BatteryML's `numpy>=1.24,<2.0` pin kept) | `pip check` clean; §3 |
| tsgm | **Not installed** in the main env | §3: no tsgm release works with numpy<2 without major workarounds, and tsgm has no Fréchet/TSTR metric and splits at window level |
| TimeSHAP | 1.0.4 + shap 0.49.1 + a **2-line import alias** (required) | Out of the box, `timeshap.explainer` fails to import with any shap >= 0.43. §5 |
| LaTeX | tectonic 0.17.0 (static musl build) in `.tools/bin` | Paper compiles, 16 pages, but under XeTeX the em/en dashes, ć and ł go missing. §6 |
| Lock reproducibility | Built a fresh venv from `requirements-lock.txt` using the script. Its `pip freeze` is identical to the lock | §7 |

## 1. Main venv

```
python3 -m venv /home/mmishchuk/projects/DegradX/.venv
.venv/bin/python -m pip install --upgrade pip setuptools wheel   # -> pip 26.2.1
```
Python in venv: `3.12.3 (main, Aug 31 2026, 10:18:26) [GCC 13.3.0]`.

## 2. PyTorch, CUDA check and determinism

### Which wheel index
I listed the cp312 wheels on each PyTorch index (`curl https://download.pytorch.org/whl/<idx>/torch/`):
- cu126: up to 2.14.0
- cu128: up to 2.11.0
- cu129: up to 2.13.0
- cu130: up to 2.14.0
- cu132: up to 2.14.0
- cu118: stops at 2.7.1

PyPI `torch==2.14.0` pulls the `nvidia-*-cu13` dependencies (PyPI JSON `requires_dist`).
Choice: **cu130 index, torch 2.14.0**. Driver CUDA 13.2 is >= 13.0, and sm_75 is present in the arch list (verified below). I did not install or check cu126 or cu132.

Installed: `torch-2.14.0+cu130`, `triton-3.8.0`, `nvidia-cudnn-cu13-9.24.0.43`, `nvidia-cublas-13.1.1.3`, `cuda-toolkit-13.0.3.0`, and the other packages listed in the lock.

### CUDA check output
Script: `$E/cuda_check.py`, run with numpy present and `CUBLAS_WORKSPACE_CONFIG` unset:
```
torch 2.14.0+cu130 cuda build 13.0 cudnn 92400
cuda.is_available True
device NVIDIA GeForce GTX 1660 Ti capability (7, 5)
arch_list ['sm_75', 'sm_80', 'sm_86', 'sm_90', 'sm_100', 'sm_120']
sm_75 in arch_list True
CUBLAS_WORKSPACE_CONFIG = None
LSTM fwd+bwd OK (0.5466166138648987, 2.4568893284971343, 0.08471917590242076)
bitwise identical across two runs: True
```
Test details:
- Model: 2-layer `nn.LSTM(6,32)` with a Linear head, batch 16, length 50, on cuda.
- Settings: `cudnn.deterministic=True`, `cudnn.benchmark=False`, `torch.use_deterministic_algorithms(True)`.
- Outcome: forward and backward ran. The loss, parameter-grad L1 and input-grad L1 were bitwise identical within one process, and across separate processes run with and without `CUBLAS_WORKSPACE_CONFIG=:4096:8`. All runs printed the same tuple.

### Determinism notes
- **No `CUBLAS_WORKSPACE_CONFIG` error is raised** in torch 2.14.0+cu130. This held for the LSTM (which uses cuBLAS in the Linear head) and for plain `a@b` and `torch.bmm` on CUDA, with deterministic mode on and the variable unset.
- The installed `use_deterministic_algorithms` docstring (`.venv/lib/python3.12/site-packages/torch/__init__.py`, from line 1756) no longer mentions the variable.
- torch's own test helper still sets `CUBLAS_WORKSPACE_CONFIG=:4096:8` "If CUDA >= 10.2" (`torch/testing/_internal/common_utils.py:2737-2741`). `libtorch_cuda.so` still parses the variable (string "Could not parse CUBLAS_WORKSPACE_CONFIG ...").
- **Recommendation:** set `CUBLAS_WORKSPACE_CONFIG=:4096:8` anyway. It costs nothing and matches torch's test harness. The setup script sets it during verification.
- UNVERIFIED: whether every cuBLAS op in torch 2.14 is deterministic without the variable. I only tested the ops above.
- **cuDNN LSTM plus gradient attribution:** Captum IG on a cuDNN LSTM in `model.eval()` fails with `RuntimeError: cudnn RNN backward can only be called in training mode` (`$E/attr_smoke.py`). Two workarounds both worked:
  - `model.train()`: max |convergence delta| 4.5e-7. Only safe with dropout 0 and no train-mode-dependent layers.
  - `with torch.backends.cudnn.flags(enabled=False):` in eval mode: delta 9.3e-9.
  - This choice has to be made explicitly for IG and for any other gradient-based attribution.

## 3. numpy / BatteryML / tsgm conflict

### tsgm release metadata (PyPI JSON `https://pypi.org/pypi/tsgm/<v>/json`)
| tsgm | uploaded | numpy / backend requirements |
|---|---|---|
| 0.1.0, 0.0.9a0 | 2025-11-08 | `numpy>=2.0`, `keras>=3.10.0`, `statsmodels==0.14.5`, `networkx<3.3,>=3.1` |
| 0.0.5–0.0.7 | 2024-03..06 | `tensorflow<2.16`, `tensorflow-probability<0.24.0`, numpy unpinned |
| 0.0.4 | 2023-12-15 | `tensorflow`, `tensorflow-probability` unpinned, numpy unpinned (does not declare statsmodels) |

### (a) Can tsgm coexist with numpy<2? Venv A: `$E/venv_a_np1_tsgm`, constraint `numpy<2`
Dry-run resolution (`pip install --dry-run -c np1.txt tsgm==<v>`):
- **0.1.0 / 0.0.9a0:** `ResolutionImpossible`, because "tsgm 0.1.0 depends on numpy>=2.0".
- **0.0.5 / 0.0.6 / 0.0.7:** "No matching distribution found for tensorflow<2.16". TF 2.15.x ships only cp39–cp311 wheels (PyPI JSON for tensorflow 2.15.0 and 2.15.1).
- **0.0.4:** resolves to tensorflow 2.21.0, keras 3.15.1, tensorflow-probability 0.25.0, numpy 1.26.4, antropy 0.1.6, yfinance 0.2.28 (`$E/a_report_0.0.4.json`).

Installing 0.0.4 for real (`$E/venv_a_install.log`, `$E/tsgm_check.py`) hit three failures in turn:
1. `ModuleNotFoundError: No module named 'tf_keras'`, from tensorflow_probability. Fixed by installing `tf-keras==2.21.0`.
2. `ImportError: keras.optimizers.legacy is not supported in Keras 3`, from `tsgm.models.timeGAN`. Fixed with `TF_USE_LEGACY_KERAS=True`.
3. `ModuleNotFoundError: No module named 'statsmodels'`, an undeclared dependency. Fixed by installing statsmodels.

After all three fixes, tsgm 0.0.4 ran on CPU: `MMD 0.0312...`, `DiscriminativeMetric acc 0.531`.
**Verdict (a):** only a 2023 tsgm works with numpy<2. It needs TensorFlow 2.21 + tf-keras (legacy Keras 2) + an undeclared statsmodels + an env flag. That adds ~3.3 GB and a second DL framework next to torch. Not recommended.

### (b) Does BatteryML work under numpy 2 with `--no-deps`? Venv B: `$E/venv_b_np2`
Setup: numpy 2.5.3, torch 2.14.0+cu130, tsgm 0.1.0, keras 3.15.1 and `pip install --no-deps batteryml@git...2861ae3`.
- `pip check` then reports `batteryml 0.0.1 has requirement numpy<2.0.0,>=1.24, but you have numpy 2.5.3`, so every resolver run will complain.
- `$E/batteryml_check.py`:
  - `import batteryml`
  - builds `BatteryData`, `CycleData` and `CyclingProtocol`
  - round-trips `dump`/`BatteryData.load` (including `additional_data`)
  - imports `MATRPreprocessor`/`HUSTPreprocessor` and runs the numba `calc_Q`
  - `MATRPreprocessor.process` on an empty dir raises the expected `FileNotFoundError`
  - **all OK under numpy 2.5.3**
- `$E/batteryml_synth_e2e.py` builds tiny synthetic inputs with the structures the preprocessors index into. These are **not real data**:
  - a MATLAB-v7.3-style HDF5 with object refs, for `load_batch` + `organize_cell`
  - a `hust_data.zip` holding `our_data/1-1.pkl`, for `HUSTPreprocessor.__call__`
  - **OK under numpy 2.5.3**, and in the main venv under numpy 1.26.4.
- `ruff 0.16.7 check --select NPY201` (numpy-2 removed APIs) over the installed `batteryml/` and `bin/` found **0 NPY201 findings**. The only 2 findings were NPY002 (legacy `np.random.seed`, style only) in `batteryml/models/nn_model.py:21` and `batteryml/pipeline.py:227`.
- Cross-version pickles (`$E/xpickle/`): a BatteryData pickle dumped under numpy 2.5.3 loads under numpy 1.26.4, and the reverse also works.
- **tsgm 0.1.0 in venv B:**
  - First import failed: `TypeError: deprecate_kwarg() missing 1 required positional argument: 'new_arg_name'` at `statsmodels/tsa/stattools.py:395`. Cause: tsgm pins statsmodels==0.14.5, which does not import under pandas 3.0.5.
  - After downgrading to pandas 2.3.3, with `KERAS_BACKEND=torch` it imported and ran: `MMD 0.03125`, `DiscriminativeMetric acc 0.469`.
  - The main venv's statsmodels 0.15.0 imports `statsmodels.tsa.stattools` fine under pandas 3.0.5.

**Verdict (b):** BatteryML's MATR/HUST paths and data classes work under numpy 2 as far as tested (synthetic inputs only; not yet on the real raw files).

### What tsgm would give us (read from `$E/venv_b_np2/.../tsgm/metrics/metrics.py`)
- `DiscriminativeMetric` concatenates both sets and calls `sklearn.model_selection.train_test_split` on **windows** (line 281). The paper requires "all splits are performed at the level of units rather than windows" (paper.tex:248), so this metric cannot be used as-is.
- `grep -riE "frechet|fid|tstr"` over tsgm 0.1.0 and 0.0.4 returns nothing. There is no Fréchet-style distance and no TSTR helper.
- Only MMD and the discriminator wrapper apply. Both are a few lines in torch.

### Recommendation: ONE environment, numpy 1.26.4, no tsgm
- BatteryML installs exactly as its authors declared, and `pip check` passes ("No broken requirements found").
- The paper's three fidelity measures (discriminator error, Fréchet-style distance, TSTR ratio) should be implemented in `degradx.metrics` in torch. Unit-level splitting is then under our control, and no TF or Keras runtime is needed.
- Fallback if numpy 2 becomes necessary: numpy 2 + `batteryml --no-deps` is viable per (b). It costs a permanently failing `pip check`, and if tsgm 0.1.0 is also wanted, pandas<3 plus statsmodels 0.14.5.

## 4. BatteryML CLI
- `setup.py` declares `console_scripts: batteryml=bin.batteryml:main` and `packages=find_packages(exclude=['scripts'])`. `bin/` has an `__init__.py`, so `bin` **is packaged** as a top-level package. Installed `top_level.txt` lists `batteryml` and `bin`; `entry_points.txt` has `batteryml = bin.batteryml:main`; `direct_url.json` records commit `2861ae3b8c79938c7fc8e6fe9986b799ca71c7dd`.
- **Working invocations** (both verified):
  - `.venv/bin/batteryml --help` (exit 0; subcommands `download`, `preprocess`, `run`)
  - `.venv/bin/python -m bin.batteryml --help`
- Usage: `batteryml preprocess {MATR,HUST,...} raw_dir output_dir [-q]`. `batteryml download` supports only `{MATR,HUST,CALCE,RWTH}`, so NASA PCoE is not supported by the BatteryML downloader or preprocessors (`SUPPORTED_SOURCES` in `batteryml/preprocess/__init__.py`).
- Caveat: a top-level package named `bin` is generic. `python -m bin.batteryml` run from a directory that has its own `bin/__init__.py` would be shadowed. The console script is unaffected.
- **Risks for the data stage** (read from `batteryml/preprocess/preprocess_HUST.py`):
  - Line 31 extracts `hust_data.zip` **into the raw directory** (`raw_file.parent/our_data`), and line 123 then `rmtree`s it. It writes into `data/raw/HUST/`, so point it at a copy if raw must stay read-only.
  - Line 52 uses plain `pickle.load` on the HUST DataFrame pickles. I built pickles with old pandas (`$E/old_pickle_*.py`) and tried to load them:
    - pandas **1.3.5** pickles: plain `pickle.load` fails under **both pandas 3.0.5 and 2.3.3** with `TypeError: Argument 'placement' has incorrect type (expected pandas._libs.internals.BlockPlacement, got slice)`. `pd.read_pickle` loads them.
    - pandas 1.4.4, 1.5.3 and 2.0.3 pickles: load fine under both.
    - The pandas version that wrote the real HUST files is **UNVERIFIED** (I did not touch `data/`). If they are <=1.3.5, the stock `batteryml preprocess HUST` will fail whichever pandas we pin. The fix is a DegradX loader using `pd.read_pickle`.
  - The MATR preprocessor expects exactly the four files `MATR_batch_20170512/20170630/20180412/20190124.mat` in `raw_dir` (`preprocess_MATR.py`).

## 5. TimeSHAP / captum
- Versions: `timeshap 1.0.4` (latest on PyPI, uploaded 2023-09-13; last GitHub commit 2023-12-21), `shap 0.49.1`, `altair 6.3.0`, `feedzai-altair-theme 2.1.1`, `captum 0.9.0`.
- `import timeshap` and `import captum` succeed. `import timeshap` emits one altair DeprecationWarning ("Deprecated since altair=5.5.0. Use altair.theme instead").
- **`from timeshap.explainer import ...` FAILS** with shap 0.49.1: `ImportError: cannot import name 'Kernel' from 'shap.explainers._kernel'`. Root cause: `timeshap/explainer/kernel/timeshap_kernel.py:53` does `from shap.explainers._kernel import Kernel`, and shap renamed that class `KernelExplainer` in 0.43.0.
  - Checked sdists: `class Kernel(Explainer)` in 0.40.0, 0.41.0 and 0.42.1; `class KernelExplainer(Explainer)` in 0.43.0 and 0.44.1. Checked wheels: `KernelExplainer` in 0.45.1 through 0.49.1.
  - timeshap declares `shap>=0.37.0` with no cap, so its metadata is wrong. GitHub master still imports `Kernel`.
  - shap <=0.42.1 has no cp312 wheels (PyPI JSON).
- Two working options, both tested:
  1. **shap 0.42.1 built from sdist** on py3.12/numpy 1.26.4 (`$E/venv_c_shap042`, `$E/venv_c_shap_build.log`, "Successfully built shap"). Needs gcc at install time.
  2. **shap 0.49.1 wheel + alias before importing timeshap** (chosen):
     ```python
     import shap.explainers._kernel as _k
     if not hasattr(_k, "Kernel"): _k.Kernel = _k.KernelExplainer
     ```
     `TimeShapKernel` overrides everything except `solve`. I diffed `solve` between 0.42.1 and 0.49.1: same algorithm, with the normal-equation `inv` replaced by `np.linalg.solve` and `lstsq` as the fallback.
- **Validation** (`$E/timeshap_exact.py`, `$E/timeshap_sampled.py`):
  - Linear model with exact Shapley values (T=8, C=3, full enumeration): event-level max|err| 7.1e-15, feature-level 5.6e-16, sum phi = f(x) − f(b). Identical for shap 0.42.1 (no alias) and shap 0.49.1 (with alias).
  - Nonlinear recency-weighted model (T=30, pruned_idx=10, nsamples=600, so sampled + AIC/lasso path): event+feature Shapley values from 0.42.1 vs aliased 0.49.1 differ by at most **6.7e-16**.
  - With the alias, `timeshap.explainer` (`local_report`, `global_report`), `timeshap.utils.calc_avg_event`, `timeshap.plot` and `timeshap.wrappers` all import.
- **Action for the code stage:** put the alias in `degradx` (e.g. a compat module imported before any `timeshap.explainer` import), plus a pytest reproducing the linear exact-Shapley check. pyproject caps `shap<0.50` because only 0.49.1 was validated.
- captum 0.9.0 smoke test on CUDA LSTM (`$E/attr_smoke.py`): `IntegratedGradients`, `FeatureAblation` and `Occlusion(sliding_window_shapes=(1,1))` all OK. See §2 for the cuDNN eval-mode caveat on IG.

## 6. LaTeX (tectonic)
- Release: GitHub API `repos/tectonic-typesetting/tectonic/releases`, tag `tectonic@0.17.0` (published 2026-07-27).
  - Asset `tectonic-0.17.0-x86_64-unknown-linux-musl.tar.gz`, sha256 `8533d07f9ccbd7a65824b9e0459041bca34af1eb33daba48f59215593753a3b7`. My local `sha256sum` matches the API `digest`.
  - The gnu asset (sha256 `1a7156...d5d606`, also matched) links `libgraphite2.so.3`. The musl binary is "not a dynamic executable", so I installed musl to `/home/mmishchuk/projects/DegradX/.tools/bin/tectonic`. `tectonic --version` gives `Tectonic 0.17.0`.
- Cache kept inside the repo tools dir: `TECTONIC_CACHE_DIR=.tools/tectonic-cache` (44 MB after the first compile) and `XDG_CACHE_HOME=.tools/xdg-cache`. `~/.cache/Tectonic` was not created.
- Compile: `cp -a paper $E/paper_copy`, remove the copied pdf, then `tectonic --keep-logs --keep-intermediates paper.tex`. Exit 0 after 1m45s (bundle download included); bibtex ran automatically (`paper.bbl` written). Log: `$E/tectonic_compile.log`.
- **Pages: 16** (`pdfinfo`, Producer `xdvipdfmx (0.1)`, letter). The committed `paper/paper.pdf` also has 16 pages (Producer `pdfTeX-1.40.27`).
- No undefined citations or references and no Overfull boxes in `paper.log`. Warnings:
  - `inputenc package ignored with utf8 based engines` (paper.log:63).
  - Several `Underfull \vbox (badness 10000/3058/3281) ... while \output is active` (paper.tex:108, 141, 371).
  - **Missing characters in Times T1 (`ptmr8t`/`ptmb8t`):** "—" U+2014 (28 warnings), "–" U+2013 (19), "ć" U+0107 (9), "ł" U+0142 (4). Sources: paper.tex:81, 83, 99, 107, 156 and paper.bbl:20, 167, 178, 287, 316, 325.
  - **These glyphs are silently dropped from the PDF.** `pdftotext` finds 0 em dashes in the tectonic PDF vs 6 in the committed pdfTeX PDF.
  - Cause: XeTeX ignores `inputenc`, so raw UTF-8 dashes and diacritics reach the 8-bit T1 fonts.
- **Tested fix, not applied to `paper/`**, on a separate scratch copy `$E/paper_copy_fix`, log `$E/tectonic_compile_fix.log`. Insert this after `\usepackage[T1]{fontenc}`:
  ```latex
  \usepackage{iftex}
  \ifXeTeX
    \usepackage{newunicodechar}
    \newunicodechar{—}{\textemdash}
    \newunicodechar{–}{\textendash}
    \newunicodechar{ć}{\'{c}}
    \newunicodechar{ł}{\l{}}
    \newunicodechar{°}{\textdegree}
  \fi
  ```
  Result: exit 0, 16 pages, all "Missing character" warnings gone (only the Underfull vbox warnings remain), and 6 em dashes in the extracted text, matching the pdfTeX PDF. The `\ifXeTeX` guard leaves pdflatex builds unchanged.
- Non-ASCII in the sources: paper.tex has — ×7, ł, –, °. references.bib has – ×5, ć ×3, í ×2, é, ö, ó, ä. The Latin-1 characters rendered without warnings.

## 7. Files written
- `/home/mmishchuk/projects/DegradX/pyproject.toml`:
  - project `degradx` 0.0.1, setuptools, src layout (`package-dir {"": "src"}`, find `degradx*`), `requires-python >=3.12,<3.13`
  - lower bounds for all deps; upper bounds only where there is evidence (`numpy<2` from BatteryML, `shap<0.50` from the TimeSHAP alias validation)
  - `statsmodels>=0.15` (0.14.5 breaks under pandas 3), `timeshap==1.0.4`
  - BatteryML as a direct git reference at `2861ae3b...`
  - extras `dev=[pytest]`, `viz=[umap-learn]`
  - `pip install --dry-run` of a scratch copy (`$E/pyproj_check`) against the main venv: "Would install degradx-0.0.1", nothing else needed.
- `/home/mmishchuk/projects/DegradX/requirements-lock.txt`: `pip freeze --exclude-editable` of the main venv (98 packages). The comment header names the torch index `https://download.pytorch.org/whl/cu130` and the install command.
- `/home/mmishchuk/projects/DegradX/scripts/s0_setup_env.sh`:
  - `set -euo pipefail`; must be run from repo root (checks for `requirements-lock.txt` and `pyproject.toml`)
  - creates the venv if missing (python3.12)
  - `pip install -r requirements-lock.txt --extra-index-url .../cu130`
  - `pip install --no-deps -e .` only if `src/degradx/__init__.py` exists
  - fetches tectonic 0.17.0 musl with sha256 check if missing or wrong version
  - prints a verification table: python, numpy, torch/CUDA/cuDNN, device arch in arch list, deterministic LSTM fwd+bwd, batteryml version + commit, timeshap (explainer import through the alias) + shap, captum, degradx importability, tectonic
  - exits 2 if CUDA or arch checks fail
  - overrides: `DEGRADX_VENV`, `DEGRADX_PYTHON`, `DEGRADX_SKIP_TEX`
- Script test runs:
  - **Idempotent re-run on the main venv:** exit 0 in 7.6 s.
  - **Fresh run in a scratch repo copy** (`$E/fresh_repo`, `$E/fresh_setup.log`): new venv, lock install, tectonic downloaded and sha-checked, verification all True, exit 0 in 2m04s (pip cache warm). `pip check` was clean, and **the fresh `pip freeze` was identical to the lock** (`diff` empty).

## 8. Main-venv versions (from `pip freeze`)
torch 2.14.0+cu130 · triton 3.8.0 · numpy 1.26.4 · scipy 1.17.1 · pandas 3.0.5 · scikit-learn 1.9.1 · statsmodels 0.15.0 · csaps 1.3.3 · h5py 3.16.0 · matplotlib 3.11.2 · PyYAML 6.0.3 · omegaconf 2.3.1 · typer 0.27.2 · pytest 9.1.1 · umap-learn 0.5.12 (warns "Tensorflow not installed; ParametricUMAP will be unavailable") · tqdm 4.70.1 · captum 0.9.0 · shap 0.49.1 · timeshap 1.0.4 · altair 6.3.0 · feedzai-altair-theme 2.1.1 · BatteryML 0.0.1 @ 2861ae3b8c79938c7fc8e6fe9986b799ca71c7dd · numba 0.67.0 · llvmlite 0.49.0 · xgboost 3.4.1 (pulls `nvidia-nccl-cu13`) · seaborn 0.13.2 · plotly 7.0.0 · openpyxl 3.1.5 · fire 0.7.1 · addict 2.4.0. Full list: `requirements-lock.txt`.

## 9. Failures, side effects, open items
- **Failed:**
  - tsgm 0.1.0 with numpy<2 (unresolvable); tsgm 0.0.5–0.0.7 on py3.12 (no TF<2.16 wheels)
  - tsgm 0.0.4 stock import (needed 3 workarounds)
  - tsgm 0.1.0 under pandas 3 (statsmodels 0.14.5)
  - `timeshap.explainer` import with shap >= 0.43 (needs the alias)
  - Captum IG on a cuDNN LSTM in eval mode
  - tectonic glyph loss for — – ć ł
- **Side effect outside my write list:**
  - Another agent created `src/degradx/__init__.py` while I was working. My idempotent script run therefore did the editable install of `degradx` into the main venv. That wrote `src/degradx.egg-info/` (git-ignored via `*.egg-info/`) and `src/degradx/__pycache__/` (from `import degradx` in the verification step, git-ignored).
  - I did not modify anything else outside the allowed paths, and did not touch `data/`, `paper/` or git.
- **Scratch venvs** (safe to delete): `$E/venv_a_np1_tsgm` 3.3 G, `$E/venv_b_np2` 6.4 G, `$E/venv_c_shap042` 770 M, `$E/fresh_repo/.venv` 6.3 G, plus small `venv_old_pandas`, `venv_pd_*`, `uv_python`, `uv_cache`.
- **UNVERIFIED:**
  - the pandas version of the real HUST pickles
  - BatteryML preprocessors on the real MATR/HUST raw files
  - cu126/cu132 torch builds
  - full cuBLAS determinism without `CUBLAS_WORKSPACE_CONFIG`
  - shap 0.42.1 source-build time (not captured)
