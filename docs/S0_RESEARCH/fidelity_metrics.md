# Fidelity measures (paper Sec. 3.5.1): packaged implementations, S0 research

Date: 2026-09-15. Scope: find packaged implementations for (i) the discriminative score, (ii) a Fréchet distance in a learned representation space (Context-FID), (iii) TSTR, and (iv) cross-channel covariance agreement. Then decide what we use and what has to be our own code.
Everything below comes from source I read or commands I ran. Scratch root: `S=/tmp/claude-1000/-home-mmishchuk-projects-DegradX/e1767cc0-419f-4700-b388-11290dc5e816/scratchpad/s0_research/fid` (clones in `$S/src`, downloaded wheels/sdists in `$S/dl`, toy scripts in `$S/tests`, throwaway venvs `$S/venv_*`). No project code was written. Nothing under `data/` was touched.

---

## 0. What the paper requires (spec)

- `paper/paper.tex:262`: per profile, (a) the classification error of a discriminator that separates generated from measured **windows** [yoon2019], (b) a Fréchet-style distance in a learned representation space [psagan2022], (c) agreement of the cross-channel covariance structure. All are computed on windows, "with the window length and the effective number of independent units stated alongside".
- `paper.tex:264`: the discriminative measure is a coarse indicator only.
- `paper.tex:266`: TSTR [esteban2017]. A model is trained on the profile with the RUL transfer target and evaluated on held-out measured units. The reference is the same architecture trained on the measured fitting split. The report is **the ratio of the two errors with a bootstrap interval**, per profile, against its own dataset only.
- `paper.tex:248`: **all splits are performed at the level of units rather than windows, on both generated and measured data**, and normalization uses training units only. This rule matters for every package below: none of them splits by unit.
- `paper.tex` and `references.bib` never mention TS2Vec or Franceschi et al. (grep). `references.bib:246` cites PSA-GAN (ICLR 2022) only.

## 1. Environments used for testing

| env | how | key versions (from `pip freeze` / runtime print) |
|---|---|---|
| project `.venv` (read-only use, `PYTHONDONTWRITEBYTECODE=1`, `CUDA_CACHE_DISABLE=1`, sources imported from scratch clones) | owned by another agent; I installed nothing into it | numpy 1.26.4, scipy 1.17.1, torch 2.14.0+cu130, scikit-learn 1.9.1, pandas 3.0.5, BatteryML 0.0.1, captum 0.9.0; CUDA available, GTX 1660 Ti, `torch.cuda.get_arch_list()` includes `sm_75` |
| `$S/venv_np1` | `pip install numpy<2 torch==2.14.0(cpu) sdmetrics[torch]==0.31.0 pytorch-fid==0.3.0 torchmetrics==1.9.0 ts2vec==0.1 scipy==1.17.1`: exit 0 (`$S/log_np1.txt`) | numpy 1.26.4, pandas 2.3.3 (sdmetrics forces <3), scipy 1.17.1, torch 2.14.0+cpu (`$S/freeze_np1.txt`) |
| `$S/venv_tsgm` | `pip install tsgm[torch]==0.1.0`: exit 0 (`$S/log_tsgm.txt`); later `pandas<3` added (see §2.1) | numpy 2.5.3, keras 3.15.1, scipy 1.18.1, torch 2.14.0+cpu, pandas 3.0.5 then 2.3.3 |
| `$S/venv_tsgm_np1` | copy of venv_np1 plus `tsgm==0.1.0 --no-deps` and its runtime deps, `numpy<2` | numpy 1.26.4, keras 3.15.1, tsgm 0.1.0 |
| `$S/venv_probe` | pip 26.2.1, used only for `pip install --dry-run` resolution checks | - |

Toy data for all runs: `$S/tests/toydata.py`, 300 windows × T=50 × C=4 sinusoids. "same" means the same generator with another seed; "diff" means noise σ raised from 0.1 to 0.5.

---

## 2. Findings per candidate

### 2.1 tsgm (AlexanderVNikitin/tsgm), Apache-2.0

**Releases and requirements** (PyPI JSON `https://pypi.org/pypi/tsgm/<v>/json` and sdists in `$S/dl`):

| version | upload | requirement highlights | py3.12 install (pip dry-run / real) |
|---|---|---|---|
| 0.0.1 | 2023-03-01 | `tensorflow==2.9.1` (sdist `setup.py:53-56`) | **fails**: "No matching distribution found for tensorflow==2.9.1" |
| 0.0.2, 0.0.3, 0.0.4 | 0.0.3: 2023-09-28 | unpinned `tensorflow`, `tensorflow-probability` (0.0.3 `setup.py:62-76`) | resolves to tensorflow 2.21.0 + numpy 2.5.3 + keras 3.15.1 (dry-run only; whether the TF-2.x-era code runs on TF 2.21/Keras 3 is **UNVERIFIED**) |
| 0.0.5, 0.0.6, 0.0.7 | 0.0.7: 2024-06-24 | `tensorflow<2.16`, `tensorflow-probability<0.24.0` | **fails** (0.0.7 dry-run): "No matching distribution found for tensorflow<2.16" (py3.12 wheels start at 2.16) |
| 0.0.9a0 | 2025-11-08 | `numpy>=2.0`, `keras>=3.10.0`, `statsmodels==0.14.5`, extra `torch==2.6.0` | resolves (dry-run) to numpy 2.5.3 |
| 0.1.0 | 2025-11-08 | `numpy>=2.0`, `keras>=3.10.0`, `statsmodels==0.14.5`, `yfinance==0.2.61`, extra `torch>=2.6.0` | installs. `tsgm==0.1.0` together with `numpy<2`: **ResolutionImpossible** |

The metrics module is TF-bound up to 0.0.7 (`tsgm/utils/mmd.py:7-9` imports `tensorflow`, `tensorflow_probability`) and Keras-3-bound from 0.0.9a0 (`tsgm/utils/mmd.py:8 from keras import ops`). `import tsgm` imports every submodule (`tsgm/__init__.py`), including keras, statsmodels and yfinance. The file `tsgm/metrics/metrics.py` is identical in 0.1.0 and master (180369c, 2026-03-10) for `DiscriminativeMetric`.

**Metric classes** (0.1.0, `tsgm/metrics/__init__.py`): `DistanceMetric`, `ConsistencyMetric`, `DownstreamPerformanceMetric`, `PrivacyMembershipInferenceMetric`, `MMDMetric`, `DiscriminativeMetric`, `EntropyMetric`, `DemographicParityMetric`, `ShannonEntropyMetric`, `PairwiseDistanceMetric`, `PredictiveParityMetric`. `DiscriminativeMetric` first appears in 0.0.3 (0.0.1 lacks it). **tsgm has no Context-FID or any Fréchet distance, no TSTR, and no cross-channel correlation statistic** (`tsgm/metrics/statistics.py` offers only axis max/min/mean/mode/percentile/percent-autocorr/power).

- `DiscriminativeMetric.__call__` (`metrics.py:278-292`) is a thin wrapper: it concatenates the arrays, calls `sklearn.model_selection.train_test_split` (**random split by sample, not by unit**), `model.fit(X_train, y_train, epochs=n_epochs)`, `model.predict(X_test)`, and returns accuracy. The model is duck-typed, so a pure PyTorch object with `fit/predict` works. I verified this: `$S/tests/t_tsgm.py` gives accuracy 0.542 (same) and 0.983 (diff).
  - **Bug found:** for a binary Keras model whose sigmoid head returns shape `(N,1)`, `len(pred.shape)==1` is false, so the code takes `argmax(axis=-1)`, which is always 0 (`metrics.py:285-288`). With keras 3.15.1 on the torch backend, same and diff both returned **0.533**, which equals the fraction of label 0 in `y_test` (`$S/tests/t_tsgm_bug.py`: "fraction of label 0 in y_test: 0.5333"; "keras predict output shape: (5, 1)").
- `DownstreamPerformanceMetric` (`metrics.py:138-178`) returns `evaluate(D1∪D2) − evaluate(D1)`. That is an **augmentation gain, not TSTR**.
- `MMDMetric` uses `exp_quad_kernel` with a fixed `length_scale=1.0` on raw windows (`utils/mmd.py:51-63`). On my toy it returned 0.0200000 for both same and diff at n=100, which is exactly 2/n (the off-diagonal kernel values vanish). On numpy 1.26 (`venv_tsgm_np1`) it returned 0.1 = 2/20 at n=20. It is degenerate unless the caller supplies a bandwidth.
- **Import failure as resolved today:** `tsgm[torch]==0.1.0` resolves pandas 3.0.5. `import tsgm` then raises `TypeError: deprecate_kwarg() missing 1 required positional argument: 'new_arg_name'` from `statsmodels/tsa/stattools.py:395`, because the pinned statsmodels 0.14.5 calls the pandas-3 `deprecate_kwarg(klass, old, new, ...)` signature wrongly (`pandas/util/_decorators.py:104-108`). It works after `pip install "pandas<3"`. The project `.venv` has pandas 3.0.5.
- On numpy 1.26 with `--no-deps`, `import tsgm` works and `DiscriminativeMetric`/`MMDMetric` run, but `pip check` reports that tsgm 0.1.0, ml-dtypes 0.6.0 and contourpy 1.4.0 require numpy>=2.
- **Fit: no.** It offers no Context-FID and no TSTR, splits by sample, has the Keras-output bug, and pulls in heavy import-time dependencies (keras, yfinance, statsmodels) that conflict with the main env (numpy<2 and pandas 3).

### 2.2 TS2Vec (encoder for Context-FID)

- **Official repo:** `github.com/yuezhihan/ts2vec`, now redirected by the GitHub API to `zhihanyue/ts2vec`. MIT license ("Copyright (c) 2022 Zhihan Yue", `$S/src/ts2vec/LICENSE`). Last commit b0088e14 (2023-06-06, "Fix typo"). It is **not a package**: it has no setup.py or pyproject, and imports are top-level (`ts2vec.py:5-7 from models import TSEncoder`). `requirements.txt` pins torch==1.8.1 and numpy==1.19.2 (py3.8 era).
- **PyPI `ts2vec==0.1`** (uploaded 2025-01-11, py3-none-any wheel): METADATA has only Name and Version, with **no author, homepage, license or dependencies**, and the wheel contains no LICENSE file. `diff` against the official repo: `ts2vec.py` differs only in relative imports (`from .models ...`); `models/*.py` and `utils.py` are identical. It is an unofficial repackaging of MIT code without the license text, so vendoring the official repo (with LICENSE) is preferable to depending on it.
- **Torch compatibility (run in the project `.venv`, torch 2.14.0+cu130, GTX 1660 Ti, `$S/tests/t_mainenv.py`):** `fit` with default n_iters (200 when `train_data.size <= 100000`, `ts2vec.py:74-75`) finished in 5.7 s on cuda:0. `encode(..., encoding_window='full_series')` returns (300, 320). `save`/`load` roundtrip max abs diff was 4.5e-7 with `device="cuda:0"`.
  - **Incompatibility:** with `device=0` (the integer form used in the official README and in Diffusion-TS `Utils/context_fid.py:23`), `load()` fails under torch 2.14 with `TypeError: 'int' object is not callable` inside `torch.serialization` (`ts2vec.py:317 torch.load(fn, map_location=self.device)`). Pass a string device.
  - Only `utils.data_dropout` uses `np.bool`, which was removed in numpy ≥1.24 (`utils.py:62`); it is not on the fit/encode path. The CPU run in `venv_np1` (numpy 1.26.4, torch 2.14 cpu) also worked: 200 iters in 10.9 s.
  - **Nondeterminism:** two identical GPU runs gave Context-FID 0.5007 vs 0.5008 (same) and 2.9890 vs 2.9894 (diff). The CPU run gave 0.502 / 3.177. The value depends on the encoder seed and on cuDNN.

### 2.3 Where Context-FID reference implementations live, and how they compute it

**PSA-GAN, the original.** Paper: arXiv 2108.00981v3, ICLR 2022 (`$S/psagan.txt`).
- Encoder: **not TS2Vec.** "Context-FID, leveraging unsupervised time series embeddings (Franceschi et al., 2019)" (`psagan.txt:81-83`). Appendix D: "we replace InceptionV3 … with the encoder E of Franceschi et al. (2019), which we train separately for each dataset. … select a time range [t, t+τ]. We then sample a batch of synthetic time series … and a batch of real time series … that we encode with E … compute the FID score of the embeddings" (`psagan.txt:938-944`). Window lengths used: 16, 32, 64, 128, 256 (`run_experiment.py:116`). Data min-max scaled to [0,1] (`psagan.txt:311`).
- Code: `github.com/mbohlkeschneider/psa-gan`, Apache-2.0, a GluonTS fork, last commit a2b409b (2022-03-09, "camera ready").
  - `src/gluonts/nursery/ContextFIDExperiment/FID.py:26-92`: the pytorch-fid "stable" Fréchet formula, `linalg.sqrtm(sigma1.dot(sigma2), disp=False)` with an eps-diagonal retry and an imaginary-part check.
  - Encoder: `src/gluonts/model/psagan/cnn_encoder/_model.py` `CausalCNNEncoder` ("code from: github.com/White-Link/UnsupervisedScalableRepresentationLearningTimeSeries", Apache-2.0).
  - FID is computed per batch and averaged over `nb_run` batches (`experimental_setup_refactored.py:188-217`).
  - **Not runnable as released:** `res2tex` is imported (`run_experiment.py:28`) but missing, dataset paths are hard-coded to `/home/ec2-user/SageMaker/...` (`experimental_setup_refactored.py:63-68`), no encoder weights are included, and `requirements-pytorch.txt` pins torch~=1.6 plus mxnet. Issue #1 (2022-03-21), maintainer: "there aren't really any instructions yet".

**Diffusion-TS** (`github.com/Y-debug-sys/Diffusion-TS`, MIT, commit 566307e, 2025-02-28).
- `Utils/context_fid.py:22-32`: `TS2Vec(input_dims=C, device=0, batch_size=8, lr=0.001, output_dims=320, max_train_length=3000)`, then `fit(ori_data)` (the encoder is trained **on the same real data being evaluated**, re-trained on every call, default n_iters), then `encode(..., encoding_window='full_series')`, then `calculate_fid`.
- `calculate_fid` (`:7-20`) is the naive variant: `scipy.linalg.sqrtm(sigma1.dot(sigma2))`, keep only `.real`, with no eps retry.
- `gen_represenation[idx]` uses the permutation of the real indices, so it requires n_gen ≥ n_real.
- `Models/ts2vec/` is the official TS2Vec with one renamed kwarg (`causal`→`casual`) and changed import paths (diff with `--strip-trailing-cr`).
- Usage: `Experiments/metric_pytorch.ipynb` runs 5 repetitions and reports mean ± t-interval (`Utils/metric_utils.py:11-16`).

**TSGBench** (`github.com/YihaoAng/TSGBench`, commit 3d090e5, 2025-07-13). **No license** (GitHub API `license: null`, no LICENSE file), so its code must not be copied.
- `src/evaluation.py:14-27` uses the same naive `calculate_fid`, and `:111-116` trains TS2Vec on the train split.
- `src/ts2vec.py:12-21`: `output_dims=100`, batch 8, lr 1e-3, max_train_length 3000.

**GenTS** (`github.com/WillWang1113/GenTS`, MIT, commit 3a0c3c9, 2026-06-03; paper arXiv 2605.17804).
- `gents/evaluation/model_based/cfid.py:6-62` uses the naive formula. The encoder is trained on an explicit `train_data` or loaded from `ts2vec_path`. `_ts2vec.py:13` sets `output_dims=100`.
- Acknowledges TSGBench and ImagenTime (`gents/evaluation/__init__.py:1-3`).
- **Not on PyPI:** PyPI `gents` 1.3.0 is an unrelated Earth-system-model tool. `setup.py` has no `install_requires`, and `requirements.txt` pins numpy==2.2.6 and torch==2.5.1. `import gents.evaluation` needs POT (`model_free/distribution_distance.py:4 import ot`).

**Numerical agreement of Fréchet formulas** (`$S/tests/t_np1.py`, TS2Vec embeddings, float64). pytorch-fid `calculate_frechet_distance`, the naive Diffusion-TS/TSGBench/GenTS formula and torchmetrics `_compute_fid` (eigvals) gave **identical values to 6 decimals**: same 0.502039 / 0.502039 / 0.502039; diff 3.177421 / 3.177421 / 3.177421.

**SciPy break:** `scipy.linalg.sqrtm(..., disp=False)`, as used by pytorch-fid and PSA-GAN `FID.py`, emits "The `disp` argument is deprecated and will be removed in SciPy 1.18.0." on scipy 1.17.1 and raises **`TypeError: sqrtm() got an unexpected keyword argument 'disp'` on scipy 1.18.1** (`$S/tests/t_tsgm.py` in venv_tsgm). The project `.venv` has scipy 1.17.1.

**Finite-sample bias** (`$S/tests/t_fd_rank.py`). Two independent N(0, I) samples, so the true FD is 0. All three implementations agree:

| n | d | FD |
|---|---|---|
| 2000 | 32 | 0.300 |
| 400 | 320 | 130.156 |
| 100 | 320 | 353.434 |
| 30 | 320 | 486.459 |

With few measured units (NASA PCoE in particular) and d=320, the raw number is dominated by estimation bias. Consequences: a measured-vs-measured reference is needed, d must be declared, and n/d must be reported.

### 2.4 Discriminative score reference implementations

- **TimeGAN paper vs code.** The paper (`$S/timegan.txt:623-628`) describes "a post-hoc time-series classification model (by optimizing a 2-layer LSTM) … report the classification error on the held-out test set". The tables say "Discriminative Score (Lower the better)" with a maximum of .500 (`timegan.txt:664-668`).
  - The official code (`jsyoon0823/TimeGAN`, commit 8f6181c, license file with an Apache-2.0 header; GitHub API reports "NOASSERTION") differs. `metrics/discriminative_metrics.py:51-53,77,127` uses a **1-layer GRU** with `hidden_dim=int(dim/2)`, 2000 iterations, batch 128, an 80/20 random split per source (`utils.py:28`), and returns **|accuracy − 0.5|**. `requirements.txt` pins `tensorflow==1.15.0`.
  - So the literature's "discriminative score" is |acc−0.5| (0 is best), not the raw classification error. For C=4 channels, `int(dim/2)` gives a hidden size of 2.
- **Diffusion-TS** `Utils/discriminative_metric.py`: TF1-compat port despite the "pytorch" header (`:22-23` imports tensorflow). It copies the bug `generated_time = extract_time(ori_data)` (`:69`), uses `hidden_dim=int(dim/2)` and 2000 iters (`:74-75`), and returns `np.abs(0.5-acc)` (`:159`). Running it under TF≥2.16/Keras 3 on py3.12 is **UNVERIFIED** (TF not installed).
- **TSGBench** `src/ds_ps.py` is TensorFlow, with no license.
- **GenTS** `gents/evaluation/model_based/ds.py` is **the only PyTorch port found**.
  - GRU with `hidden_dim=int(C/2) if C>1 else 16`, 2000 iters, batch 128 (`:29-31`), 80/20 random split by sample (`:114-142`), returns |acc−0.5| (`:109`).
  - Ran in the project `.venv` on cuda: same **0.042**, diff **0.500**, about 4.5 s each.
  - **Crashes when n_real ≠ n_gen** (real 300, fake 200): `ValueError: all the input array dimensions except for the concatenation axis must match` (label construction at `:103-105`).
- **sdmetrics 0.31.0** (MIT, `sdmetrics/timeseries/detection.py`, `ml_scorers.py`). `LSTMDetection` builds one sequence per `sequence_key`, uses `train_test_split(shuffle=True, stratify=y)` with **no seed parameter** (`detection.py:99`), trains a torch 1-layer LSTM with hidden 32 for 1024 full-batch Adam steps at lr 1e-2 (`ml_scorers.py:28-69`), and returns `1 − accuracy` (`detection.py:101`). The docstring says "one minus the average ROC AUC" (`detection.py:20`), but the code returns accuracy (`ml_scorers.py:69`). Ran in venv_np1: same **0.440**, diff **0.053**, about 9 s each (`$S/tests/t_sdm.py`). It requires `pandas<3.0.0` for py3.12 (PyPI requires_dist), which conflicts with pandas 3.0.5 in the project `.venv`.
- **synthcity 0.2.12** (Apache-2.0). `metrics/eval_detection.py:26-128` **flattens** each sequence (`reshape(len(X), -1)`), runs sklearn/XGB/MLP/GMM with `StratifiedKFold` by sample, and reports AUROC. It has no post-hoc RNN. It requires `torch<2.3,>=2.1`, `numpy<2.0,>=1.20`, `networkx<3.0`, `fastai<2.8`, `pykeops`, `monai`, `tsai`, …. A pip dry-run on py3.12 resolves in isolation (torch 2.2.2+cpu), while `synthcity==0.2.12` together with `torch==2.14.0` gives **ResolutionImpossible**. Not installed or run.

### 2.5 TSTR

- **Esteban et al. 2017** (arXiv 1706.02633, `$S/rgan.txt:251-270`, Algorithm 1): train a classifier on synthetic data generated with the training labels, then score it on the held-out real test set. The original code, `ratschlab/RGAN`, is MIT and TensorFlow, last pushed 2018-10-07. TSTR is a protocol, not a metric function.
- **sdmetrics** `LSTMClassifierEfficacy` (`timeseries/efficacy/base.py`) is the closest in spirit: it returns `synt_acc / real_acc` (`:83`), a TSTR/TRTR ratio. But it is **classification only**, with one label per sequence (`group.pop(target).iloc[0]`), a random unseeded split, no regression target and no bootstrap.
- **synthcity** `_evaluate_time_series_performance` (`metrics/eval_performance.py:341-470`) trains on real vs synthetic, tests on real (`gt`, `syn_id`, `syn_ood`) with R² and KFold over sequences, using its own model templates. The torch<2.3 pin makes it incompatible. Routing and behaviour were not run (**UNVERIFIED**).
- **tsgm** `DownstreamPerformanceMetric` computes augmentation gain (§2.1), which is not TSTR.
- TimeGAN, Diffusion-TS and GenTS "predictive score" is next-step MAE after training on synthetic data, not RUL.
  - TimeGAN and Diffusion-TS predict the last channel from the first C−1 (`Diffusion-TS/Utils/predictive_metric.py:103-105`).
  - GenTS predicts all channels (`ps.py:88-89`).

### 2.6 Cross-channel covariance or correlation agreement

- **Diffusion-TS** `Utils/cross_correlation.py`: `cacf_torch` (`:5`) standardizes each channel over (samples, time) jointly and multiplies lower-triangular channel pairs, diagonal included, at lags 0..max_lag−1. `CrossCorrelLoss` (`:44-52`) takes `sum |mean_ccf_fake − mean_ccf_real|` at lag 0 divided by 10. The notebook computes it on 5 random subsets of size n/5. It is pure torch and ran in the project `.venv`: same 0.02219, diff 0.02567. The toy channels are independent, so this toy is not informative about sensitivity. TSGBench and GenTS do not include it. This correlation is pooled over time; in mean-nonstationary degradation windows it is dominated by the shared trend, so our definition must be declared.
- **sdmetrics** `column_pairs/statistical/correlation_similarity.py:127` scores `1 − |ρ_real − ρ_syn|/2` per column pair with Pearson or Spearman. It is tabular and pandas<3.
- tsgm, synthcity, torchmetrics and pytorch-fid have nothing comparable.

### 2.7 Frechet helpers

- **torchmetrics 1.9.0** (Apache-2.0, requires torch>=2.0, `numpy>1.20.0`). `torchmetrics/image/fid.py:174-194 _compute_fid(mu1, sigma1, mu2, sigma2)` computes `‖Δμ‖² + tr Σ1 + tr Σ2 − 2·Σ sqrt(eigvals(Σ1Σ2)).real`. It is a **private, underscore** function; the public `FrechetInceptionDistance` is image and Inception only. Importing `torchmetrics.image.fid` without torch-fidelity worked (venv_np1). The pip dry-run with numpy<2 resolves.
- **pytorch-fid 0.3.0** (Apache-2.0). `pytorch_fid/fid_score.py:152-206 calculate_frechet_distance`. The module imports torchvision and PIL at the top (`:38-52`), so torchvision is required. It uses `sqrtm(disp=False)`: a deprecation warning on scipy 1.17 and a **TypeError on scipy ≥1.18** (§2.3).

### 2.8 ydata-synthetic

PyPI 2.0.1 has `requires_python <3.12,>=3.9`, `tensorflow==2.15.*`, `numpy<2`; the py3.12 dry-run found "No matching distribution". The repo moved to `Data-Centric-AI-Community/fg-data-synthetic` (MIT, LICENSE "Copyright (c) 2022 YData"). `src/data_synthetic/evaluation/` contains only `__init__.py`, so it has **no fidelity metrics**; "discriminator" hits are GAN internals.

---

## 3. Comparison table

| package (version checked) | relevant metric(s) | backend | install on py3.12 (what I ran) | numpy constraint | license | fits our use? |
|---|---|---|---|---|---|---|
| tsgm 0.1.0 (also 0.0.9a0) | DiscriminativeMetric (wrapper), MMDMetric, DownstreamPerformanceMetric (augmentation gain) | Keras 3 (jax/tf/torch); duck-typed model OK | installs; **import fails with resolved pandas 3.0.5** (statsmodels 0.14.5), works with pandas<3; ran toy | declares `numpy>=2` (numpy<2 → ResolutionImpossible); runs on 1.26 with `--no-deps` | Apache-2.0 | **No**: no C-FID/TSTR, sample-level split, `(N,1)` Keras-output bug, degenerate default MMD bandwidth, heavy deps |
| tsgm 0.0.5–0.0.7 | same minus later classes | TensorFlow <2.16 | **fails** (no TF<2.16 for py3.12) | unpinned | Apache-2.0 | No |
| tsgm 0.0.1 | no DiscriminativeMetric | TF 2.9.1 | **fails** | ≥1.21.6 | Apache-2.0 | No |
| tsgm 0.0.2–0.0.4 | Discriminative (from 0.0.3) | TF unpinned | dry-run resolves TF 2.21 + numpy 2.5.3; runtime UNVERIFIED | unpinned | Apache-2.0 | No (TF-only) |
| TS2Vec official (zhihanyue/ts2vec @b0088e1) | encoder for C-FID | PyTorch | not pip-installable; ran fit/encode/save/load on torch 2.14 cu130 GPU (load needs string device) | none declared; works on 1.26.4 | MIT | **Yes (vendor)** |
| `ts2vec` 0.1 (PyPI) | same code, relative imports | PyTorch | installs, ran on CPU | no deps declared | **none in metadata** (unofficial repackaging) | Usable but prefer vendoring official |
| PSA-GAN (mbohlkeschneider/psa-gan) | original Context-FID (Franceschi CausalCNN encoder) + FID.py | PyTorch 1.6 + GluonTS/mxnet fork | not installable/runnable as released (missing `res2tex`, hard-coded paths) | - | Apache-2.0 | Reference only |
| Diffusion-TS (@566307e) | Context_FID (TS2Vec), CrossCorrelLoss, disc./pred. score | torch (FID, CC); **TF1-compat** (disc./pred.) | not a package; CrossCorrelLoss ran in project env | - | MIT | Reference; formulas small enough to reimplement |
| TSGBench (@3d090e5) | C-FID (TS2Vec d=100), DS/PS (TF), MDD/ACD/SD/KD | torch + TF | not a package | - | **no license** | No (cannot reuse code) |
| GenTS (@3a0c3c9) | context_fid (TS2Vec d=100), discriminative_score & predictive_score in **torch** | PyTorch | not on PyPI; ds.py ran on project env GPU | requirements pin 2.2.6 (not enforced) | MIT | Reference for a torch discriminator; crashes on unequal n; sample-level split |
| sdmetrics 0.31.0 | LSTMDetection (1−acc), LSTMClassifierEfficacy (synt/real acc ratio), CorrelationSimilarity | torch (extra) | installs with numpy<2, ran LSTMDetection | numpy ≥1.26 (py3.12); **pandas <3** | MIT | **No**: pandas<3 conflicts with main env; sample-level unseeded split; classification only |
| synthcity 0.2.12 | detection (flattened, AUROC), TS performance (R²), image FID | torch | dry-run resolves with torch 2.2.2; **conflicts with torch 2.14** (ResolutionImpossible); not run | `numpy<2` | Apache-2.0 | **No** |
| ydata-synthetic 2.0.1 | none | TF 2.15 | **fails** (`Requires-Python <3.12`) | `numpy<2` | MIT | No |
| torchmetrics 1.9.0 | `_compute_fid` helper (private) | torch | installs with numpy<2; ran | `numpy>1.20.0` | Apache-2.0 | Formula OK, but private API; not worth a dependency for 5 lines |
| pytorch-fid 0.3.0 | `calculate_frechet_distance` | numpy/scipy (+ torchvision import) | installs with numpy<2; ran | unpinned | Apache-2.0 | Formula OK but **breaks on scipy ≥1.18** (`disp`) and pulls torchvision |
| RGAN (ratschlab) | TSTR (classification) | TF | not tried | - | MIT | Reference (definition only) |
| TimeGAN (jsyoon0823) | discriminative/predictive score | TF 1.15 | not tried (TF1) | - | Apache-2.0 header | Reference (definition/defaults only) |

---

## 4. Recommendations

Common reason no package fits: the paper requires **unit-level splits on both sides** (`paper.tex:248`), the effective number of units reported alongside, a **regression** transfer target with an **error ratio and bootstrap-over-units CI** (`paper.tex:266`), and compatibility with numpy<2 + pandas 3 + torch 2.14. Every packaged discriminative or efficacy metric found uses a random split by sample, by sequence or KFold. None has a groups argument, and none offers a regression TSTR ratio.

### (i) Discriminative score: own code, about 60 lines of torch

- **Architecture and defaults:** follow the TimeGAN protocol as ported to torch in GenTS `ds.py` (1-layer GRU, last hidden state, linear head, BCE, Adam, 2000 iterations, batch 128, 80/20 train/test).
  - Replace the random split with `sklearn.model_selection.GroupShuffleSplit` by unit id, applied separately to measured and generated windows.
  - Balance classes by subsampling to equal window counts, which also avoids the GenTS unequal-n crash.
  - Declare the hidden size explicitly: `int(C/2)` gives 2 for C=4, which is probably too weak; this is a declared choice.
- **Report:** test accuracy, the paper's "classification error" = 1 − acc, and |acc − 0.5| (the TimeGAN/Diffusion-TS/GenTS convention). State which one Table `tab:res:fidelity` shows, because the literature's "discriminative score" is |acc−0.5| even though the TimeGAN paper text says "classification error" (§2.4).
- Repeat over seeds and bootstrap over units.
- **Why not a package:** tsgm has a sample-level split, Keras-output bug and numpy>=2/pandas pins. sdmetrics needs pandas<3 and has an unseeded, sample-level split. synthcity flattens, uses AUROC and pins torch<2.3. The Diffusion-TS and TSGBench versions are TensorFlow. GenTS is not packaged, splits by sample and crashes on unequal n.

### (ii) Representation-space Fréchet distance: vendor TS2Vec plus about 10 lines of own Fréchet code

- **Encoder:** vendor the official TS2Vec source (`zhihanyue/ts2vec` @ b0088e14, MIT, keep LICENSE: `ts2vec.py`, `models/`, `utils.py`). Adjust the imports and always pass `device="cuda:0"` or `"cpu"`, not an int, because `load()` breaks on torch 2.14 (§2.2). Using PyPI `ts2vec==0.1` is technically possible, but that repackaging has no license or author metadata.
- **Fréchet:** own function of ~10 lines, `‖μ1−μ2‖² + tr(Σ1+Σ2) − 2·tr sqrtm(Σ1Σ2)`, in float64, either with `scipy.linalg.sqrtm` **without `disp`** or with the torchmetrics eigvals form. Cite PSA-GAN `FID.py` and pytorch-fid as the formula source; all implementations gave identical numbers (§2.3). Do not depend on pytorch-fid (breaks on scipy≥1.18, pulls torchvision) or on the private torchmetrics `_compute_fid`.
- **Protocol:** the references disagree, so each choice must be declared.
  - Encoder training data: PSA-GAN trains the encoder "separately for each dataset"; Diffusion-TS re-trains on the evaluated real data at every call; TSGBench and GenTS train on the train split. Recommended: train on **measured fitting-split windows only**, never on generated windows and never on held-out units. Then compute FD(held-out measured, generated), plus the reference FD(fitting-split measured, held-out measured), because finite-sample bias is large (FD≈353 for identical distributions at n=100, d=320; §2.3).
  - Output dims: 320 in Diffusion-TS, 100 in TSGBench/GenTS. Choose d well below the number of windows, and report n and d.
  - Pooling: `encoding_window='full_series'` max-pooling over the window, as all three TS2Vec-based references do.
  - Training length: default n_iters (200/600) or declared.
  - Repeat over several encoder seeds (a GPU run is not bit-reproducible) and bootstrap over units.
- **Citation:** the paper cites PSA-GAN, whose Context-FID uses the **Franceschi et al. 2019 causal-CNN encoder, not TS2Vec** (`psagan.txt:81-83, 938-940`). If TS2Vec is used, the paper should say it follows the TS2Vec variant of later benchmarks (Diffusion-TS/TSGBench/GenTS code) and cite TS2Vec (Yue et al., AAAI 2022). The alternative is the Franceschi encoder code (White-Link repo, Apache-2.0, also vendored in the PSA-GAN fork).

### (iii) TSTR: own code

It is a protocol around the project's own LSTM RUL model, which is project code anyway:
- Model A is trained on profile-generated units; model B (same architecture and seed schedule) is trained on the measured fitting-split units.
- Both are evaluated on the same held-out measured units with the RUL label.
- Report ratio = err_A / err_B, with a bootstrap over held-out units by resampling units, not windows. Declare whether the ratio is recomputed per bootstrap sample (recommended).

About 40 lines on top of the training loop. **Why not a package:** sdmetrics' efficacy ratio is classification-only with one label per sequence; synthcity's is R² with its own models and incompatible torch pins; tsgm's DownstreamPerformanceMetric is augmentation gain; the TimeGAN-family "predictive score" is next-step MAE, not RUL.

### (iv) Cross-channel covariance agreement: own numpy code, about 10 lines

- **Definition:** declare exactly which matrix is compared. Recommended: the channel **correlation** matrix of per-unit **detrended residuals** (or of normalized window values), averaged over units. The generator's step 3 records "the covariance among channels" (`paper.tex:236`), so compare the same statistic on generated and held-out measured units.
- **Agreement:** report `‖R_gen − R_meas‖_F / ‖R_meas‖_F` and the mean |Δρ_ij| over off-diagonal pairs. The Diffusion-TS `CrossCorrelLoss` (lag-0, sum|Δρ|/10, diagonal included) can be reported in addition for comparability with the generative literature; it is pure torch, ~20 lines, MIT.
- Bootstrap over units, and give the measured-vs-measured reference (fitting vs held-out) as in (ii).
- **Why not a package:** no time-series package implements it except the unpackaged Diffusion-TS loss. sdmetrics' CorrelationSimilarity is tabular and pandas<3. Pooling correlations over time in mean-nonstationary windows mixes the degradation trend into the statistic, so this definition must be ours.

---

## 5. Risks and open points

1. **Main-env pins:** pandas 3.0.5 in `.venv` excludes sdmetrics (pandas<3), and also tsgm 0.1.0 as currently resolved. scipy 1.17.1 still accepts `sqrtm(disp=…)`, but any future move to scipy ≥1.18 breaks pytorch-fid- and PSA-GAN-style code. Our own Fréchet code must not pass `disp`.
2. **Small-n bias of FD** (§2.3). NASA PCoE fidelity numbers will be dominated by estimation error unless d is small and a measured-vs-measured reference is reported. I did not verify unit counts per dataset here (downloads are in progress); **UNVERIFIED**.
3. **Discriminative saturation** is conceded by the paper (`paper.tex:264`). The GenTS toy already gave |acc−0.5| = 0.500 for a modest noise mismatch.
4. **Definition ambiguity**: "classification error" vs |acc−0.5| (§2.4) must be fixed before Table 1 is filled.
5. **Encoder choice** (Franceschi vs TS2Vec) must be declared and cited (§4 ii).
6. **UNVERIFIED items:** runtime of tsgm 0.0.2–0.0.4 on TF 2.21; runtime of the TF1-compat Diffusion-TS/TSGBench discriminators on TF ≥2.16; synthcity behaviour (only resolution checked); whether PSA-GAN's missing `res2tex` exists in another branch.

## 6. Artifacts

- Toy scripts: `$S/tests/t_mainenv.py` (TS2Vec GPU, GenTS ds, Diffusion-TS CrossCorrelLoss in project `.venv`), `$S/tests/t_np1.py` (TS2Vec CPU, three Fréchet implementations), `$S/tests/t_fd_rank.py` (finite-sample bias), `$S/tests/t_sdm.py` (sdmetrics LSTMDetection), `$S/tests/t_tsgm.py` and `$S/tests/t_tsgm_bug.py` (tsgm), `$S/tests/toydata.py`.
- Install logs and freezes: `$S/log_tsgm.txt`, `$S/log_np1.txt`, `$S/freeze_tsgm.txt`, `$S/freeze_np1.txt`.
- Clones: `$S/src/{ts2vec,Diffusion-TS,psa-gan,TSGBench,GenTS,tsgm,TimeGAN,ydata-synthetic}`. Wheels/sdists: `$S/dl`. Papers as text: `$S/psagan.txt`, `$S/timegan.txt`, `$S/rgan.txt`.
- Throwaway venvs, deletable: `$S/venv_probe`, `$S/venv_tsgm`, `$S/venv_np1`, `$S/venv_tsgm_np1`.
