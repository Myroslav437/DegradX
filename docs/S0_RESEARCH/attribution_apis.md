# Attribution method APIs and default configurations (TimeSHAP, IG, feature occlusion, tint)

Scope: paper Section 3.6 "Models and Baselines" (`paper/paper.tex:285-291`) runs TimeSHAP [bento2021], Integrated Gradients [sundararajan2017] and feature occlusion [suresh2017] "at their default configurations" on a trained LSTM and on the linear reference model (`paper.tex:217-218`), scored against a dense L x C ground-truth field phi* (`paper.tex:194-198`).

Everything below was read from source or run by me on 2026-09-15. Paths are abbreviated as follows:

| Abbrev. | Absolute path / URL |
|---|---|
| `ATTR` | `/tmp/claude-1000/-home-mmishchuk-projects-DegradX/e1767cc0-419f-4700-b388-11290dc5e816/scratchpad/s0_research/attr` |
| `TS` | `ATTR/src/timeshap-1.0.4-py3-none-any/timeshap` (unpacked PyPI wheel timeshap 1.0.4; identical to what pip installed in `ATTR/venv`) |
| `SHAP` | `ATTR/venv/lib/python3.12/site-packages/shap` (shap 0.52.0) |
| `CAP` | `ATTR/venv/lib/python3.12/site-packages/captum` (captum 0.9.0) |
| `TINT` | `ATTR/venv/lib/python3.12/site-packages/tint` (time_interpret 0.3.0 wheel) |
| `TSREPO` | `ATTR/timeshap_repo` = github.com/feedzai/timeshap @ `218f2ba385cb72f73ad245d249996f8566e65360` (2023-12-21) |
| `FIT` | `ATTR/fit_repo` = github.com/sanatonek/time_series_explainability @ `c9f8e5ccd993cda5d3ed695dbef350810a6aca83` |
| `DYN` | `ATTR/dynamask_repo` = github.com/JonathanCrabbe/Dynamask @ `637d84568a3a3af56fbfd343bd9ecd474fe6f633` |
| `TINTREPO` | `ATTR/tint_repo` = github.com/josephenguehard/time_interpret @ `ebef73615dda67e4c9bd42d3bac81cce6607280f` (HEAD differs from the 0.3.0 wheel in 10 files; I cite the wheel for API claims and the repo only for experiment scripts) |
| `PAP` | `ATTR/papers/*.txt` (pdftotext of arXiv PDFs: 2012.00073v2 TimeSHAP, 1703.01365v2 IG, 1705.08498v1 Suresh, 2003.02821v3 FIT) |

Probe scripts and their logs: `ATTR/test_timeshap.py` (log `test_timeshap.log`), `test_timeshap2.py`/`test_timeshap3.py`/`test_timeshap4.py` (logs `*.log`), `test_captum.py` (`test_captum.log`), `test_tint.py` (`test_tint.log`).

Environment used for the runs: Python 3.12.3, torch 2.14.0+cu130 (cuDNN 92400; `torch.cuda.get_arch_list()` includes `sm_75`, so the GTX 1660 Ti is supported), captum 0.9.0, timeshap 1.0.4, shap 0.52.0, numpy 2.5.3, pandas 3.0.5, scikit-learn 1.9.1, altair 6.3.0, time_interpret 0.3.0, pytorch-lightning 2.6.6. These are the versions pip resolved on the day (from the `pip install` output).

---

## 0. Blocking install issue: timeshap 1.0.4 does not import with current shap

* timeshap 1.0.4 (uploaded to PyPI 2023-09-13) is the latest release. The repo has had only README commits since then (`git diff 1eb505c HEAD --stat`: README.md only). Its dependency pin is `shap>=0.37.0` with no upper bound (`TSREPO/requirements/main.txt`).
* `TS/explainer/kernel/timeshap_kernel.py:53` runs `from shap.explainers._kernel import Kernel`. With shap 0.52.0 this fails with `ImportError: cannot import name 'Kernel' from 'shap.explainers._kernel'`. I observed the error (`import timeshap.explainer`). Every `timeshap.explainer` entry point is affected.
* shap v0.42.1 still defines `class Kernel(Explainer)` (`raw.githubusercontent.com/shap/shap/v0.42.1/shap/explainers/_kernel.py:38`). From v0.43.0 on, the same line is `class KernelExplainer(Explainer)` (checked tags v0.43.0, v0.44.0, v0.44.1, v0.45.0). Wheels 0.45.1 through 0.51.0 have no alias either (grep of each wheel). shap 0.42.1 has **no cp312 wheel** (PyPI JSON: 0 cp312 files).
* **Workaround (verified):** add a one-line alias before importing timeshap:
  ```python
  import shap.explainers._kernel as _k
  if not hasattr(_k, "Kernel"): _k.Kernel = _k.KernelExplainer
  ```
  `TimeShapKernel` inherits only `solve()` from shap. The rest (`__init__`, `explain`, `allocate`, `add_sample`, `run`) is overridden in `timeshap_kernel.py:113-795`. The feature-selection logic in shap 0.52.0 `solve()` (`SHAP/explainers/_kernel.py:690-733`) is the same code as shap 0.42.1 (`ATTR/ref/shap_0.42.1_kernel.py:589-630`). With the alias, TimeSHAP reproduced the exact Shapley values of linear models to about 1e-14 (Section 1.8).
* numpy/pandas: with numpy 2.5.3 and pandas 3.0.5, all timeshap paths I ran worked (`test_timeshap*.log`). `alt.themes.enable("feedzai")` (`TS/__init__.py:18`) still works with altair 6.3.0.
* shap >= 0.50.0 requires `numpy>=2` (PyPI metadata: 0.50.0, 0.51.0 and 0.52.0 all list `numpy>=2`). This clashes with BatteryML's `numpy<2.0` pin. See Section 6 for the numpy<2 check.

---

## 1. TimeSHAP (timeshap 1.0.4)

### 1.1 Model entry-point contract
* The documented contract is a callable `f(np.ndarray (n_samples, seq_len, n_features)) -> np.ndarray (n_samples, 1)` (`TS/explainer/local_methods.py:141-144`; `TSREPO/README.md:73-77`; kernel docstring `timeshap_kernel.py:71-75` also allows a vector `(n_samples,)`). I checked both `(B,1)` and `(B,)` outputs: `fnull`/`vector_out` handling is at `timeshap_kernel.py:237-251`, and a `(B,1)` LSTM ran in `test_timeshap.py`.
* Optionally `f(x, hidden_state=None) -> (pred, hidden_state)`. TimeSHAP decides whether the model returns hidden states by checking `len(out_val) == 2` on the output for the background (`TS/utils/timeshap_legacy.py:74-81`). **Pitfall:** a plain model called on a background with exactly 2 rows would be mistaken for one that returns hidden states. With a 1-row average-event background this cannot happen. Hidden states are used only to speed up pruned prefixes (`timeshap_kernel.py:191-215, 603-611`). They are irrelevant without pruning.
* **Numpy windows work directly. No DataFrames or entity/time columns are needed.** `validate_local_input` accepts a 3-D numpy array whose first dimension is 1 (`local_methods.py:86-88`). `local_event`/`local_feat`/`local_cell_level` take `entity_uuid=None, entity_col=None` (I passed `None` in all probes). DataFrames are optional. When a DataFrame is used, `entity_col` becomes mandatory (`TS/utils/utils.py:58-59`). `TimeShapKernel.shap_values` itself asserts a numpy array (`timeshap_kernel.py:283`).
* **One instance per call.** `shap_values` only handles `X.shape[0] == 1` (`timeshap_kernel.py:296-306`). For larger X it falls through and returns `None`. Windows must be looped over in Python.
* **Batching:** for each explained instance, TimeSHAP builds one array `synth_data` of shape `(nsamples, L, C)` (float64; `np.tile` at `timeshap_kernel.py:614`) and calls the model **once** on all of it (`run()`, `timeshap_kernel.py:764-786`, the call is at line 782). Observed call shapes for L=12, C=4 were `[(1,12,4), (1,12,4), (4094,12,4)]` (`test_timeshap.log`). A GPU-batched wrapper therefore helps, and chunking is the wrapper's job. With a chunk size of 16384 the L=100, C=8 LSTM ran out of memory on the 6 GB card (cuDNN requested 4.18 GiB; `test_timeshap2.log`). It worked with chunks of 4096 (`test_timeshap3.log`).
* The bundled `TorchModelWrapper` (`TS/wrappers/torch_wrappers.py`) chunks by `batch_size = floor(batch_budget / seq_len)` with `batch_budget=750000` (lines 55-59, 84-85). **Side effect:** it calls `self.model.train(True)` after every prediction (lines 103, 142). I observed `model.training == True` after one call. That would silently re-enable dropout for anything that runs afterwards (e.g. IG). Recommendation: write your own `torch.no_grad()` + `eval()` chunked wrapper.

### 1.2 How the background / baseline is supplied
* It is the `baseline` argument of `calc_local_report`, `local_pruning`, `local_event`, `local_feat` and `local_cell_level` (`local_methods.py:124-136`; `pruning.py:208-215`; `event_level.py:85-92`; `feature_level.py:89-96`; `cell_level.py:252-261`), and the `background` argument of `TimeShapKernel(model, background, rs, mode, varying=None, link=IdentityLink())` (`timeshap_kernel.py:113`).
* Accepted shapes (`timeshap_kernel.py:154-181`):
  * `(1, C)`: an **average event**, tiled to `(1, L, C)` (line 165).
  * `(L, C)`: an average sequence of the same length as the window.
  * `(1, 1, C)` or `(1, L, C)`: the same two cases in 3-D.
  * More than one background row of a different length raises `ValueError`. Only a single background instance is supported (weights at `timeshap_legacy.py:46-47`).
  * `pd.DataFrame` is also accepted (`local_methods.py:90`). `.shape` must be `(1, C)`, and the kernel reads `.data` after `time_shap_convert_to_data`. Passing `avg_event.values` is safest (that is what I did).
* Helpers:
  * `calc_avg_event(data, numerical_feats, categorical_feats, model_features=None) -> pd.DataFrame (1, C)` computes the **median** of numerical features and the **mode** of categorical ones (`TS/utils/utils.py:317-374`; median at 369, mode at 371). A numpy input must be 3-D `(N, 1, C)`, which it squeezes on axis 1 (lines 362-363). A 2-D input must be a DataFrame (line 365 calls `.values`).
  * `calc_avg_sequence(...) -> np.ndarray (L, C)` computes the per-position median over equal-length sequences (`utils.py:256-314`, median at 310).
  * `get_avg_score_with_avg_event(model, med, top=1000) -> {seq_len: score}` scores the tiled average event for lengths 1..top. It is a diagnostic only, used to check that the background scores as "uninformative" (`utils.py:403-437`). It is not used inside the explainer.
* Tutorial usage: `average_event = calc_avg_event(d_train_normalized, numerical_feats=model_features, categorical_feats=[])`, passed as `baseline` to every call (`TSREPO/notebooks/AReM/AReM.ipynb`, code cells 31 and 42-57).

### 1.3 Sampling budget (`nsamples`) and random seed
* **Kernel level.** `nsamples` defaults to `"auto"`, which means `2*M + 2**11` (`timeshap_kernel.py:393-395`). It is capped at `2**M - 2` when `M <= 30`, which gives full enumeration (lines 398-402). `M` is the number of perturbed groups: L events, C features, or the number of cells.
* **`local_*` level (what you call).** There is **no default**. `local_event`/`local_feat`/`local_cell_level` forward `dict.get("nsamples")` and `dict.get("rs")` (`event_level.py:129`, `feature_level.py:133`, `cell_level.py:304`). Omitting `nsamples` crashes with `TypeError: '>' not supported between instances of 'NoneType' and 'int'` (observed; comes from line 401).
* **Global (`*_explain_all`) level.** `verify_event_dict` and `verify_feature_dict` fill in `rs=[42]` and `nsamples=[32000]` when absent (`event_level.py:162-182`, `feature_level.py:165-186`). This is the only package-level "default" budget.
* **Paper.** "We set the maximum number of coalition samples to n_samples = 32K" (`PAP/bento2021_timeshap.txt:288-290`, Section 4). The tutorial uses `{'rs': 42, 'nsamples': 32000}` for event, feature and cell (AReM.ipynb cells 42, 53, 55, 57).
* **Seed handling.** The kernel calls `np.random.seed(self.random_seed)` just before coalition sampling (`timeshap_kernel.py:463`) and then uses the **global** numpy RNG (`np.random.choice` at 471, `np.random.permutation` at 479). Consequences:
  1. `rs=None` reseeds from OS entropy and is not reproducible (observed: two `rs=None` runs differed).
  2. Every explained instance **reseeds numpy's global RNG**. Generator and model-init code must use their own `np.random.Generator` / `torch.Generator`, or the paper's "separate seeds" requirement (`paper.tex:291`) is broken by TimeSHAP.
  3. With the same `rs`, results are bit-reproducible (observed `True`).
  4. When `M` is small enough for full enumeration (e.g. event level with `L <= 17` at 32000 samples, or `L = 12` in my probe), the seed has no effect.
* Pruning uses a fixed `rs=0` and `nsamples=4` (`pruning.py:178-179`). Pruning mode has `M=2`, so it is always fully enumerated.

### 1.4 Solver regularisation: `l1_reg="auto"` is on by default and makes the output sparse
* `explain()` reads `l1_reg = kwargs.get("l1_reg", "auto")` (`timeshap_kernel.py:390`). None of the `local_*` wrappers pass `l1_reg` (`event_level.py:70`, `feature_level.py:74`, `cell_level.py:220`), so `"auto"` always applies there.
* In shap's `solve`, `"auto"` runs LassoLarsIC(AIC) feature selection whenever `nsamples / max_samples < 0.2` (`SHAP/explainers/_kernel.py:701-728`). Unselected groups get **exactly 0**. With `nsamples=32000`, event level triggers this for `L >= 18` (since 32000/(2^18-2) < 0.2), and cell level triggers it for essentially every L x C grid.
* Observed on a random 1-layer LSTM (hidden 32, zero background):

  | Window | Event level nonzero | Full-grid cell level nonzero (`"auto"`) |
  |---|---|---|
  | L=30, C=8 | 13/30 | 101/240 |
  | L=60, C=8 | 15/60 | 131/480 |
  | L=100, C=8 | 14/100 | 79/800 |

  Sources: `test_timeshap2.log`, `test_timeshap3.log`. With `l1_reg=False` the output was fully dense.
* On the **linear** reference model, `"auto"` and `False` both recovered exact Shapley values (max error 2-3e-14 at M=320 and M=400). The only zeros were the true zero-weight channel (`test_timeshap4.log`).
* Implication: at default configuration, TimeSHAP maps on the trained LSTM contain many exact zeros (ties). This affects rank-agreement scores against the graded field.

### 1.5 Pruning: default, tolerance and semantics
* Pruning is **on whenever a `pruning_dict` is passed** and off with `pruning_dict=None` (`local_methods.py:209-215` prints "No pruning dict passed. Skipping pruning procedures"). `pruning_dict` must contain `tol` as a float or as the int `0` (`local_methods.py:92-96`). The package has no default tolerance.
* Paper: pruning tolerance eta = 0.025, chosen as a trade-off; cell-level threshold theta = 0.1 (`PAP/bento2021_timeshap.txt:295-300, 332-335, 376`, Section 4 and 4.1). Tutorial: `pruning_dict = {'tol': 0.025}` (AReM.ipynb cells 42, 51).
* Algorithm (`pruning.py:177-205`): for `seq_len = L..0`, compute a 2-player Shapley split between "events >= seq_len" and "events < seq_len". Stop at the first `seq_len < L` where `|phi(older)| <= tol` (lines 190-194). All events before `pruning_idx` then form **one group, "Pruned Events", with a single Shapley value** (`timeshap_kernel.py:317, 339-340`; `event_level.py:76-77`).
* `tol` is in **model-output units**, so it is scale-dependent. On the toy model (f(x) - f(bg) = 0.011) the tutorial's `tol=0.025` pruned the window down to its **last event only** (`coal_prun_idx=-1`; `test_timeshap.log`). It also printed a spurious "Unable to prune sequence." because the check at `pruning.py:187-188` compares the all-events coalition.
* `tol=0` (int) disables pruning in practice. `if tolerance and ...` is falsy, so the function returns `-L` and `pruning_idx = L + (-L) = 0` (lines 187-198; observed `pruning_idx 0`).
* **For a dense L x C field, pruning must be off.** Pruned positions receive no per-position or per-cell attribution.

### 1.6 Granularity TimeSHAP returns
| Level | Function | Output | Shape |
|---|---|---|---|
| Event (position) | `local_event(f, x, {'rs','nsamples'}, entity_uuid, entity_col, baseline, pruned_idx)` | DataFrame `['Random seed','NSamples','Feature','Shapley Value']` | `L - pruned_idx` rows (+1 "Pruned Events" row if `pruned_idx > 0`). **Row 0 = "Event -1" = last position** (`timeshap_kernel.py:317` iterates from `L-1` downwards; names at `event_level.py:72-77`). Verified exact on the linear model after reversing the order. |
| Feature (channel) | `local_feat(...)` | same columns | `C` rows (+ "Pruned Events" if pruned) (`feature_level.py:73-86`). Features equal to the background at every position are not perturbed and get 0 (`timeshap_kernel.py:320-326, 537-551`). |
| Cell (position, channel) | `local_cell_level(f, x, cell_dict, event_data, feat_data, entity_uuid, entity_col, baseline, pruned_idx)` | DataFrame `['Event','Feature','Shapley Value']` | see below |
| Report | `calc_local_report(f, data, pruning_dict, event_dict, feature_dict, cell_dict=None, baseline=None, ...)` | tuple `(pruning_df, event_df, feat_df, cell_df)` | `cell_df` is `None` without `cell_dict` (`local_methods.py:221-226`). |

**Cell level: full grid or top-k only?**
* By design, cell level covers **only the top-k events x top-k features** plus aggregate groups. `cell_dict` must contain one of `threshold`, (`event_threshold` & `feat_threshold`), `top_x`, or (`top_x_events` & `top_x_feats`) (`cell_level.py:195-209`; validation at `local_methods.py:105-121`). The kernel refuses cell mode without an explicit `varying` list ("computation is very expensive", `timeshap_kernel.py:124-128`).
* The selected events and features come from ranking the **event-level and feature-level outputs** by |Shapley value| (`cell_level.py:22-139`).
* The aggregate groups are: "Other Features" per relevant event, "Other Events" per relevant feature, one "Other Events x Other Features" cell, and "Pruned Events" (`timeshap_legacy.py:113-147`; `cell_level.py:230-246`). The paper describes the same structure: groups C*, E', F', C', P, with k = |F*||E*| + |F*| + |E*| + 2 (`PAP/bento2021_timeshap.txt:274-312`).
* The tutorial uses `top_x_events=3, top_x_feats=3` (cell 57) or 2 x 2 (cell 42). The paper uses theta = 0.1.
* So **at default/published configuration TimeSHAP cannot produce an L x C map**. It produces:
  1. a length-L event vector (or shorter, if pruned),
  2. a length-C feature vector,
  3. roughly `k_e x k_f` individual cells plus aggregate groups.
* **A full grid is reachable without modifying the code:** `pruned_idx=0` (no pruning) and `cell_dict={'rs': s, 'nsamples': 32000, 'top_x_events': L, 'top_x_feats': C}`. Then no "Other ..." groups are created (`timeshap_legacy.py:124-143`: all conditions are false). The kernel runs plain KernelSHAP over `M = L*C` cell groups with the average-event background.
  * Verified: 48 rows for L*C = 48 and 0 special rows (`test_timeshap.log`).
  * Mapping `"Event -k"` to position `L-k` and `"Feature c"` to channel `c` reproduced the exact linear-model Shapley grid to 8e-15 (`test_timeshap2.log`).
  * `l1_reg` stays `"auto"` on this path (sparse output, Section 1.4). A **dense** grid requires calling the kernel directly:
    ```python
    TimeShapKernel(f, bg, rs, "cell", varying=(list(range(L)), list(range(C)))).shap_values(x, pruning_idx=0, nsamples=32000, l1_reg=False)  # -> (L*C,), row-major (event, feature)
    ```
    Row-major order: `cell_idx_keys` loops events then features (`timeshap_kernel.py:130-134`). Verified `reshape(L, C)` equals the exact grid.
  * Local accuracy holds: the grid sums to f(x) - f(bg) (observed 0.011259883642 on both sides).
* **Cost per explained window** (GTX 1660 Ti, toy LSTM with hidden 32, nsamples 32000, including Python overhead):

  | Window | Full grid, `l1_reg="auto"` | Full grid, `l1_reg=False` | Event level | Feature level |
  |---|---|---|---|---|
  | L=30, C=8 | 10.3 s | 7.1 s | 0.8 s | < 0.1 s |
  | L=60, C=8 | 17.5 s | 12.4 s | 1.2 s | < 0.1 s |
  | L=100, C=8 | 34.0 s | 21.8 s | 1.7 s | < 0.1 s |

  Sources: `test_timeshap2.log`, `test_timeshap3.log`. This is a budget risk if thousands of windows x 2 models x seeds x 3 profiles x 3 weightings are needed.

### 1.7 Summary: what TimeSHAP can and cannot give at default configuration
* **Can:**
  * per-position (event) Shapley values for all L positions if pruning is off, or for the last `L - pruning_idx` positions plus one lumped value if it is on;
  * per-channel Shapley values;
  * a top-k x top-k cell set plus aggregate groups.
* **Cannot (by default):** a dense L x C map. Also, pruning plus `l1_reg="auto"` both produce lumped or zeroed entries.
* **Least-invasive route to L x C:** no pruning, `top_x_events=L`, `top_x_feats=C`, `nsamples=32000`, fixed `rs`, average-event background. This uses only public API arguments. Optionally add `l1_reg=False` via the direct kernel for a dense map; that is a declared deviation. An alternative that also avoids `L*C` groups would be event x feature outer products, but that is not a TimeSHAP output and I do not recommend it.

### 1.8 Correctness checks I ran (for the reference model)
Linear `f(x) = sum_{u,c} A[u,c] x[u,c]` with an arbitrary background `b`. Exact Shapley value = `A * (x - b)`.
* Event level: exact.
* Feature level: exact.
* Full-grid cell level (API path, `"auto"`): exact to 8e-15.
* Direct kernel with `l1_reg=False`: exact to 1.6e-14.
* L=40, C=8 and L=100, C=4: exact to about 3e-14.

Sources: `test_timeshap2.log`, `test_timeshap4.log`.

---

## 2. What the TimeSHAP paper recommends as the background

* Bento et al. (KDD'21, arXiv 2012.00073v2), Section 2: "b ... is often taken to be the zero vector, b = 0, or to be composed of the average feature values in the input dataset" (`PAP/bento2021_timeshap.txt:93-95`).
* Section 3.1, their own choice: "In our setting, we define the background matrix B in R^{l x d} as containing the average feature values in the training dataset". Eq. (5) shows the same average event repeated at every position (`PAP/bento2021_timeshap.txt:167-182`).
* Section 4.2 notes that null feature attributions "might stem from our choice of a background/uninformative event" (`PAP/bento2021_timeshap.txt:431-433`).
* **Code vs paper discrepancy:** the package helper `calc_avg_event` uses the **median** (numerical) and **mode** (categorical), not the mean (`TS/utils/utils.py:369-371`). The docstrings say "Median/Mean of numerical features and mode of categorical" (`local_methods.py:175-177`).
* **Recommendation:** the paper-faithful choice is the per-channel training-set **mean**, tiled over the window, computed on training units only in model-input space. For z-scored inputs this is the zero vector, which also coincides with the IG and occlusion defaults (Sections 3 and 4).

---

## 3. captum IntegratedGradients (captum 0.9.0)

### 3.1 Signature and defaults (`CAP/attr/_core/integrated_gradients.py`)
* Constructor: `IntegratedGradients(forward_func, multiply_by_inputs=True)` (lines 45-49). `True` means attributions are multiplied by `(inputs - baselines)` (lines 65-67, 392-398).
* Call: `attribute(inputs, baselines=None, target=None, additional_forward_args=None, n_steps=50, method="gausslegendre", internal_batch_size=None, return_convergence_delta=False)` (lines 106-115).
  * `baselines=None` means a scalar **0** for every input (docstring lines 163-166; `CAP/_utils/common.py:157-165` returns `_zeros(inputs)`, lines 149-154).
  * `method`: `gausslegendre` by default. Riemann `left/right/middle/trapezoid` are also available (docstring lines 211-214; `CAP/attr/_utils/approximation_methods.py:27-40`).
  * `internal_batch_size=None` means all `n_steps x batch` points go into one forward/backward pass (lines 215-225, 271-292). Observed: `internal_batch_size=64` changed results by at most 4.7e-10.
  * `return_convergence_delta=True` returns `(attr, delta)`, with delta = completeness error per example, shape `(B,)` (lines 226-230, 294-310).
* Paper guidance: Sundararajan et al. recommend a baseline with near-zero score (`PAP/sundararajan2017.txt:147-148, 290`) and state "between 20 and 300 steps are enough to approximate the integral (within 5%)", advising a completeness check (`PAP/sundararajan2017.txt:356-369`). captum's 50 steps are inside that range.

### 3.2 Usage for a (B, L, C) -> scalar LSTM regressor
* The forward may return `(B,)` or `(B,1)`. Scalar-per-example output needs no `target` (captum FAQ, `ATTR/ref/captum_faq.md:22`, fetched from `github.com/pytorch/captum/blob/413e888e1e8f22cf8da1631cc9ca2133ce30a9db/docs/faq.md`).
* Observed: for a `(B,1)` output, `target=None`, `target=0` and a squeezed `(B,)` forward gave identical attributions.
* The returned attributions have the input's shape, `(B, L, C)`: a dense L x C map per window with no post-processing.
* On the linear reference model, IG gave `A*(x-b)` to 4.8e-7 (float32) with max |delta| 5.7e-6 (`test_captum.log`).

### 3.3 cuDNN RNN backward in eval mode (verified)
* torch 2.14.0+cu130 with cuDNN 9.24 and a 2-layer `nn.LSTM` in `model.eval()` on the GPU: `ig.attribute(x)` raises `RuntimeError: cudnn RNN backward can only be called in training mode` (`test_captum.log`). The string is compiled into `torch/lib/libtorch_cuda.so` (`strings` grep). captum's own code contains nothing about cuDNN apart from a test helper (`grep -rn cudnn CAP`).
* The official workaround (captum FAQ `docs/faq.md:74-77`) is to set `torch.backends.cudnn.enabled=False`. The scoped form I verified is:
  ```python
  model.eval()
  with torch.backends.cudnn.flags(enabled=False):
      attr, delta = IntegratedGradients(fwd).attribute(x, return_convergence_delta=True)
  ```
  This ran with max |delta| = 2.4e-8 on the LSTM.
* Alternative seen in the FIT repo: `model.train()` before attributing (`FIT/evaluation/baselines.py:285`). With `nn.LSTM(dropout=0.2)` this makes two IG runs **differ** (observed `False`), because dropout is active. Only if every dropout is disabled (including `nn.LSTM.dropout`, which is a float attribute rather than a module) does train mode match cuDNN-disabled eval, to 3e-9 (observed). **Use the cuDNN-disabled context, not `train()`.**

---

## 4. Feature occlusion [suresh2017]

### 4.1 What Suresh et al. (2017) actually did
Source: arXiv 1705.08498v1, Section 4.5.1 "LSTM Feature-Level Occlusions" (p. 6), and Section 5.2 / Figure 4 (p. 8). The MLHC/PMLR version was not checked (UNVERIFIED that its text is identical).
* Quote: "we remove features one by one from the patients (by replacing the given feature with noise drawn from a uniform distribution in [0,1)). We then compare the predictive ability of the model with and without each feature" (`PAP/suresh2017.txt:286-290`).
* **Replacement value:** uniform noise U[0,1). Their numeric inputs had "been transformed to a 0-1 range (normalized and mean imputed)" (`PAP/suresh2017.txt:314-315`), so the noise spans the data range.
* **Granularity:** the whole feature (channel), removed "one by one". There is no per-time-step occlusion.
* **Output:** a **dataset-level** drop in AUC per feature. Figure 4 shows "the top eight features that cause a decrease in prediction AUC" (`PAP/suresh2017.txt:457-459`). It is a global per-feature importance, not a per-instance map.
* Number of noise draws: not stated (UNVERIFIED).

### 4.2 How the time-series XAI benchmark code bases implement "FO"
* **FIT (Tonekaboni et al., 2020).** The paper cites Suresh as [32]: "importance is assigned based on the difference in model prediction when each feature x_i is replaced with a random sample from the uniform distribution" (`PAP/tonekaboni2020_fit.txt:246-251`). The code is `FOExplainer.attribute(x, y, retrospective=False, n_samples=10)` (`FIT/TSX/explainers.py:159-193`), with input `[batch, features, time]`:
  * For every t in 1..T-1 and every feature i, it replaces the **single cell** `x[:, i, t]` with `U(-3, +3)` noise (line 184).
  * It scores the model on the prefix `x[:, :, :t+1]` (non-retrospective, line 179).
  * Importance = mean over `n_samples=10` of `|y_hat - p_y_t|` after the activation, softmax by default (lines 160, 183-192).
  * Result: a per-(feature, time) **absolute, Monte-Carlo** map with first column `t=0` left at 0 (loop starts at 1, line 177).
  * Called with defaults from `FIT/evaluation/baselines.py:216-220, 291`. The older experiment path uses the same `np.random.uniform(-3,+3)` per cell (`FIT/TSX/experiments.py:825, 849-857`).
* **Dynamask (Crabbe & van der Schaar, 2021).**
  * State/MIMIC experiments reuse FIT's FO verbatim (`DYN/experiments/run_state.sh:14`, `run_mimic.sh:21`: `python -m fit.evaluation.baselines --explainer fo`).
  * The rare-time and rare-feature experiments use captum: `Occlusion(forward_func=f).attribute(X, sliding_window_shapes=(1,), baselines=torch.mean(X, dim=0, keepdim=True))`, then `normalize(abs(attr))` (`DYN/baselines/explainers.py:24-35`; used at `DYN/experiments/rare_time.py:95-97`).
  * There, `X` is one series of shape `(T, D)` and the white box returns one output per time step (`rare_time.py:72-78`). The baseline is therefore each feature's **temporal mean**, and occlusion is per (t, d) through the per-time output.
* **tint (Enguehard, 2023) experiments.**
  * HMM (classification): `TimeForwardTunnel(TemporalOcclusion(classifier)).attribute(x_test, sliding_window_shapes=(1,), baselines=x_train.mean(0, keepdim=True), attributions_fn=abs, task="binary")` followed by `.abs()` (`TINTREPO/experiments/hmm/main.py:260-269`).
  * MIMIC blood pressure (regression): same, with `TemporalOcclusion(regressor)` (`TINTREPO/experiments/mimic3/blood_pressure/main.py:155-167`).
  * ARMA: plain `Occlusion(sliding_window_shapes=(1,), baselines=mean over time)` (`TINTREPO/experiments/arma/main.py:129-139`).
  * `TemporalOcclusion` sets the time window to the full time dimension and masks only the last time step (`TINT/attr/temporal_occlusion.py`; repo lines 214-217, 277). `TimeForwardTunnel` slides over prefixes. Together they are the FIT construction with a **training-mean** replacement instead of uniform noise.

### 4.3 Mapping onto captum and a defensible "default configuration"
* **captum.attr.Occlusion.** Signature: `attribute(inputs, sliding_window_shapes, strides=None, baselines=None, target=None, additional_forward_args=None, perturbations_per_eval=1, show_progress=False)` (`CAP/attr/_core/occlusion.py:51-63`).
  * `strides=None` means stride 1 (docstring).
  * `baselines=None` means 0 (docstring; the same `_format_baseline` as IG).
  * Attribution = `f(x) - f(x_occluded)`, signed (`CAP/attr/_core/feature_ablation.py:1166`).
* **captum.attr.FeatureAblation.** Signature: `attribute(inputs, baselines=None, target=None, additional_forward_args=None, feature_mask=None, perturbations_per_eval=1, show_progress=False, **kwargs)` (`feature_ablation.py:291-300`). `feature_mask=None` ablates every scalar independently.
* Verified equivalences on the LSTM and the linear model (`test_captum.log`):
  * `Occlusion(sliding_window_shapes=(1,1))` == `FeatureAblation()` (default mask). Per-cell, output `(B, L, C)`. Exact `A*(x-b)` on the linear model (3.6e-6, float32).
  * `Occlusion(sliding_window_shapes=(L,1))` == `FeatureAblation(feature_mask=channel ids)`. Whole channel over time (Suresh granularity); the map is constant along L.
  * `perturbations_per_eval=64` gave identical results with 5 instead of 241 forward calls for B=16, L=40, C=6. Valid because the forward returns one value per example.
* Choice of "default configuration":
  * **Granularity.** Suresh's literal method (whole channel, dataset AUC drop) yields no L x C map, so it cannot be scored against phi*. All three benchmark code bases that cite or implement FO on time series (FIT, Dynamask, tint) occlude **one cell (feature, time) at a time**. I therefore propose `sliding_window_shapes=(1,1)`, `strides=1`. Our model maps a whole window to one scalar, so the prefix construction of FIT and tint (`TimeForwardTunnel`, for per-time-step predictions) does not apply. It also failed on our regressor: `AssertionError: Output must be 2D to select tensor of targets` and `Tensor target dimension torch.Size([8, 1]) is not valid` (`test_tint.log`).
  * **Replacement value.** Suresh used U[0,1) noise on [0,1]-scaled data; FIT used U(-3,3) noise (mean 0) on standardized data; Dynamask and tint (captum-based) used the mean. A deterministic mean or zero baseline removes an extra Monte-Carlo seed. On z-scored inputs, the captum default 0 equals the training mean, which is also the expectation of FIT's zero-mean noise. **Proposal:** `baselines = per-channel training mean in model-input space`, i.e. 0 if inputs are z-scored with training statistics (the captum default). The same background should be used for TimeSHAP (Section 2).
  * **Sign.** Keep the signed captum output (`f(x) - f(x_occ)`). FIT, Dynamask and tint take `abs()`. Whether the scorer uses |.| is a scoring decision; state it.

---

## 5. tint / time_interpret 0.3.0

* **Install:** `pip install time_interpret==0.3.0` installed on Python 3.12.3 on top of torch 2.14.0 and captum 0.9.0. It added pytorch-lightning 2.6.6, torchmetrics 1.9.0 and aiohttp (pip output). Its classifiers only list up to Python 3.11 (`TINTREPO/pyproject.toml`), but there is no `requires-python` upper bound (`>=3.7`). `import tint` and `from tint.attr import ...` for all occlusion, IG and tunnel classes worked.
* **What it provides** (`TINT/attr/__init__.py`): `AugmentedOcclusion`, `BayesKernelShap`, `BayesLime`, `DiscretetizedIntegratedGradients`, `DynaMask`, `ExtremalMask`, `FeatureAblation`, `Fit`, `GeodesicIntegratedGradients`, `LofKernelShap`, `LofLime`, `NonLinearitiesTunnel`, `Occlusion`, `Retain`, `SequentialIntegratedGradients`, `TemporalAugmentedOcclusion`, `TemporalIntegratedGradients`, `TemporalOcclusion`, `TimeForwardTunnel`. **There is no TimeSHAP** and no TimeSHAP-style event or cell grouping.
* `tint.attr.Occlusion` and `tint.attr.FeatureAblation` are forks of captum's classes with an extra `attributions_fn` argument (`TINT/attr/feature_ablation.py:63-71, 402-403`; `TINT/attr/occlusion.py:69-82`). On the LSTM they gave **identical** outputs to `captum.attr.Occlusion((1,1))` (`test_tint.log`). `AugmentedOcclusion(data=x_train, n_sampling=10)` (AFO) also ran.
* **Does it remove work? No.**
  * The three methods are fully covered by captum (IG, Occlusion) and timeshap.
  * tint's time-series FO wrapper (`TimeForwardTunnel` + `TemporalOcclusion`) targets per-time-step models and failed on our window regressor.
  * It adds a pytorch-lightning dependency, and its GitHub HEAD differs from the 0.3.0 wheel.
  * Recommendation: do not depend on tint.

---

## 6. numpy<2 co-installation check (BatteryML pin)
* Second venv `ATTR/venv_np1`: `pip install "numpy>=1.24,<2.0" torch captum==0.9.0 timeshap==1.0.4`. pip resolved **numpy 1.26.4, shap 0.49.1** (the newest shap without `numpy>=2`), pandas 3.0.5, torch 2.14.0+cu130, captum 0.9.0 and altair 6.3.0 (pip list in the task output).
* shap 0.49.1 also lacks `Kernel` (wheel grep, Section 0), so the same shim is required.
* All probes gave the same results as the numpy-2 stack:
  * `test_timeshap_np1.log`: identical event values, full grid 48/48, same 5 zeros under `"auto"`, and the same `TorchModelWrapper` train-mode side effect.
  * `test_timeshap4_np1.log`: linear exactness 2-4e-14.
  * `test_captum_np1.log`: same cuDNN error and workaround, IG linear error 4.8e-7, Occlusion == FeatureAblation.
* Conclusion: a single Python 3.12 environment with BatteryML's `numpy<2` pin can run all three methods (shap 0.49.1 + shim). I did not install BatteryML itself into this venv (UNVERIFIED that its other pins do not conflict).

---

## 7. Risks and decisions for the orchestrator

1. **"Default configuration" is not well defined for any of the three methods under an L x C ground truth.**
   * TimeSHAP's published defaults (pruning eta = 0.025, cell theta = 0.1 or top-k) cannot produce a dense map.
   * Suresh's FO is a global channel-level AUC drop.
   * Only IG's captum defaults produce an L x C map unchanged.
   * The paper text (`paper.tex:289`, `paper.tex:425`) should declare the exact settings used, including the full-grid cell setting and no pruning for TimeSHAP, and per-cell occlusion for FO.
2. **The reference model's analytic solution depends on the baseline.** For a linear model, TimeSHAP (exact), IG and single-cell occlusion all return `a*(x - baseline)`, not `phi* = a*m + b*p` (Eq. `eq:groundtruth`). The two agree (up to `a*eps`) only when the baseline is the zero vector **in the units in which y is defined**. If model inputs are z-scored, the "analytically available solution" of `paper.tex:218` has to be restated as `a*(x - baseline)`, or scoring has to use raw-unit zero baselines. This choice changes rank agreement on the graded field.
3. **Separate seeds.** TimeSHAP reseeds numpy's global RNG on every call (`timeshap_kernel.py:463`). Generation and initialisation must not use the global numpy RNG.
4. **Sparse TimeSHAP maps** from `l1_reg="auto"` (Section 1.4) create ties in rank metrics on the trained LSTM. Either accept this as default behaviour and report it, or declare `l1_reg=False` as a deviation.
5. **Compute budget.** A full-grid TimeSHAP cell map costs about 7-34 s per window on this GPU for L = 30-100 and C = 8 (Section 1.6). IG and occlusion take well under 1 s per batch.
6. **Environment.**
   * timeshap needs the `Kernel` alias shim with shap >= 0.43 (Section 0).
   * `TorchModelWrapper` flips the model to train mode after each call (`torch_wrappers.py:103, 142`).
   * The GPU LSTM needs the cuDNN-disabled context for IG (Section 3.3).
   * Chunk TimeSHAP's `(32000, L, C)` model calls (a 16384-sample chunk ran out of memory at L=100).

---

## 8. PROPOSAL: config spec (not yet agreed; for review)

```yaml
# PROPOSAL - attribution methods at "default configuration" adapted to a dense L x C ground truth.
# Every entry marked `deviation:` departs from the published/tool default and must be declared in the paper.
common:
  background: per_channel_train_mean          # computed on training units only, in model-input space; shape (1, C)
                                              # (= zeros if inputs are z-scored with train stats)
  attribution_seed: <separate seed stream>    # never the global numpy RNG for generation/model init
  model_call: torch.no_grad(), model.eval(), chunked (e.g. 4096 windows/chunk), returns np.ndarray (n, 1)

timeshap:   # timeshap==1.0.4 + shim: shap.explainers._kernel.Kernel = KernelExplainer
  entry: timeshap.explainer.local_event / local_feat / local_cell_level   # numpy (1, L, C) per window
  pruning_dict: null                          # deviation: paper/tutorial use tol=0.025; pruning lumps positions
  pruned_idx: 0
  event_dict:   {rs: <seed>, nsamples: 32000} # 32000 = paper Sec.4 + global-API default (event_level.py:181-182)
  feature_dict: {rs: <seed>, nsamples: 32000}
  cell_dict:    {rs: <seed>, nsamples: 32000, top_x_events: L, top_x_feats: C}   # deviation: paper theta=0.1 / tutorial top 2-3
  l1_reg: auto                                # tool default via local_cell_level (sparse output)
  sensitivity_variant:                        # optional, declared deviation
    call: TimeShapKernel(f, background, rs, "cell", varying=(range(L), range(C))).shap_values(x, pruning_idx=0, nsamples=32000, l1_reg=False)
  output_map: cell rows -> (L, C): "Event -k" -> position L-k, "Feature c" -> channel c

integrated_gradients:   # captum==0.9.0
  class: captum.attr.IntegratedGradients(forward_func, multiply_by_inputs=True)
  attribute_kwargs: {baselines: null, target: null, n_steps: 50, method: gausslegendre,
                     internal_batch_size: null, return_convergence_delta: true}   # baselines null == 0 (captum default)
  context: torch.backends.cudnn.flags(enabled=False), model.eval()   # required for GPU LSTM backward
  log: max |delta| per batch

feature_occlusion:      # captum==0.9.0
  class: captum.attr.Occlusion(forward_func)
  attribute_kwargs: {sliding_window_shapes: [1, 1], strides: null, baselines: null,   # per cell; stride 1; 0 == train mean if z-scored
                     target: null, perturbations_per_eval: 64}                          # ppe only changes speed (verified identical)
  sign: signed f(x) - f(x_occluded) (captum); scorer decides abs()
  deviation: Suresh 2017 = whole channel, U[0,1) noise, dataset AUC drop; cell-level form follows FIT/Dynamask/tint
  equivalent: captum.attr.FeatureAblation(forward_func).attribute(x, baselines=None, perturbations_per_eval=64)
```
