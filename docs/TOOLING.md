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
| Discriminative score (planned, S5) | `degradx.metrics` | tsgm unusable (above); ~60 lines of torch GRU following TimeGAN defaults, with the unit-level split the paper requires |
| Fréchet distance in representation space (planned, S5) | `degradx.metrics` + vendored TS2Vec (MIT) | TS2Vec official code is not pip-installable; the PyPI `ts2vec` is an unlicensed copy |
| TSTR ratio (planned, S5) | `degradx.metrics` | no package provides a regression TSTR error ratio with a unit-level bootstrap |
