# Tooling decisions

Brief R2: an established package is used wherever one implements a step. Own code is written only for what
is specific to this benchmark (generator, ground truth Eq. 4–5, degradation state Eq. 3, scoring protocol),
and every such case states why no package fits. Evidence for S0 entries: `docs/S0_RESEARCH/`.

## Packages used — `step → package → why`

| step | package (version in `requirements-lock.txt`) | why |
|---|---|---|
| Battery data layer | BatteryML @ `2861ae3b` (git) | brief R3; unified `BatteryData`/`CycleData` for MATR and HUST |
| Deep learning, GPU | torch 2.14.0+cu130 | cu130 wheel lists sm_75; deterministic LSTM fwd/bwd verified bitwise across processes |
| Smoothing | `scipy.signal.savgol_filter` | §3.3 step one names Savitzky–Golay |
| Trajectory fitting | `scipy.optimize.least_squares` | nonlinear least squares with bounds and multistart |
| Monotone channel mappings φ_c | `sklearn.isotonic.IsotonicRegression` + `scipy.interpolate.PchipInterpolator` | isotonic gives monotonicity without a shape assumption; PCHIP makes it smooth and preserves monotonicity. `csaps` and LOWESS are smooth but not monotone |
| Noise autocorrelation | `statsmodels.tsa.stattools.acf` | standard estimator |
| Bootstrap intervals | `scipy.stats.bootstrap` (BCa) | resampling over units |
| Retrieval / rank scores | `sklearn.metrics.average_precision_score`, `scipy.stats.spearmanr` | standard definitions |
| Integrated Gradients, occlusion | captum 0.9.0 | reference implementations; IG runs with cuDNN disabled because eval-mode cuDNN RNN backward is unsupported |
| TimeSHAP | timeshap 1.0.4 + shap 0.49.1 | only implementation; needs the `Kernel` alias in `degradx.attribution.timeshap_compat` |
| MATR ingestion | BatteryML `load_batch`, `clean_batches`, `organize_cell` (one batch per child process) | brief R3; the CLI loads all four batches at once (~12.5 GB estimated peak); same functions, same merge semantics |
| HUST ingestion | `batteryml preprocess HUST` (CLI) | brief R3, run as documented |
| Raw download | `batteryml download MATR/HUST`; `urllib` for NASA S3 | BatteryML's own links; NASA is not in BatteryML |
| Per-cycle `.mat` reading (NASA) | `scipy.io.loadmat(simplify_cells=True)` | MATLAB v5 files |
| Paper build | TinyTeX (TeX Live 2026, pdfTeX 1.40.29), latexdiff 1.4.0 | pdfTeX produced the committed PDF; tectonic 0.17 (XeTeX) was tried and silently dropped em/en dashes and `ć`/`ł` |
| Figure style | matplotlib + `degradx.viz.style` | reconstruction of the missing `style.py`; reproduces Figures 1–4 byte-identically under matplotlib 3.10.8 |

## Rejected packages

| candidate | for | reason (evidence in `docs/S0_RESEARCH/`) |
|---|---|---|
| tsgm (all releases) | discriminator, Context-FID, TSTR | 0.1.0 needs numpy≥2 (conflicts with BatteryML pin); 0.0.5–0.0.7 need TensorFlow without py3.12 wheels; no Context-FID or regression TSTR; window-level splits |
| time_interpret (tint) | occlusion utilities | installs, but its occlusion equals captum's and its time-series wrapper fails on window-level regressors; removes no work |
| sdmetrics, synthcity, ydata-synthetic | fidelity metrics | pandas<3 / torch<2.3 / Python<3.12 constraints; no time-series regression metrics |
| tectonic | LaTeX | drops glyphs (see above) |

## Own code — `step → why no package fits`

| step | module | why no package fits |
|---|---|---|
| Stage CLI, provenance, seeding by source | `degradx.utils` | glue specific to this repository's reproducibility contract (brief §4); `argparse`, `PyYAML`, `numpy.random.SeedSequence` do the actual work |
| TimeSHAP import shim | `degradx.attribution.timeshap_compat` | upstream timeshap is unmaintained since 2023 and imports a renamed shap class |
| Discriminative score | `degradx.metrics.fidelity` | tsgm unusable (above); ~60 lines of torch GRU following TimeGAN defaults, with the unit-level split the paper requires |
| Fréchet distance in representation space | `degradx.metrics.fidelity` + vendored TS2Vec (`degradx.metrics.ts2vec`, official commit b0088e1, MIT; import lines only changed) | TS2Vec official code is not pip-installable; the PyPI `ts2vec` is an unlicensed copy; FID formula via `scipy.linalg.sqrtm` |
| NASA PCoE → BatteryData converter | `degradx.data.nasa` | brief §2.2: BatteryML has no NASA preprocessor; validated against raw arrays (max diff 0) and against BatteryML MATR/HUST object fields (S1 checks) |
| MATR time-unit fix and summary attachment | `degradx.data.matr` | BatteryML stores MATR minutes as `time_in_s` and drops summary fields the channel set needs |
| HUST cycler capacity attachment | `degradx.data.hust` | BatteryML drops the source `dq`; D11 |
| Per-cycle channel derivation | `degradx.data.channels` | benchmark-specific channel definitions (declarations `channels.candidates`); integration follows BatteryML's `calc_Q` rule |
| Degradation state Eq. 3 | `degradx.generator.state` | benchmark definition (R2 exception); smoothing is `scipy.signal.savgol_filter` |
| Pattern detection rule | `degradx.fitting.patterns` | benchmark rule of §3.3 step five; residual scale is a MAD |
| TSTR ratio | `degradx.metrics.fidelity` + `scipy.stats.bootstrap` (BCa over units) | no package provides a regression TSTR error ratio with a unit-level bootstrap |
| LSTM regressor and training loop | `degradx.models.lstm` (torch) | architecture declared in configs/models/lstm.yaml; a training loop with unit-level validation and early stopping is a few lines of torch |
