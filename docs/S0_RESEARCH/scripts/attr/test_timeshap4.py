import numpy as np, time
import shap.explainers._kernel as _k
_k.Kernel = getattr(_k, "Kernel", _k.KernelExplainer)
from timeshap.explainer.kernel import TimeShapKernel
from timeshap.explainer import local_event
rng = np.random.default_rng(1)
for L, C in [(40, 8), (100, 4)]:
    A = rng.normal(size=(L, C)); A[:, -1] = 0
    # recency-like weights on a smooth drifting input to mimic the benchmark's dense field
    f = lambda x: np.einsum("blc,lc->b", x, A)[:, None]
    x = rng.normal(size=(1, L, C)); bg = np.zeros((1, C)); truth = A * (x[0] - bg)
    for l1 in ["auto", False]:
        k = TimeShapKernel(f, bg, 42, "cell", varying=(list(range(L)), list(range(C))))
        t = time.time(); phi = k.shap_values(x, pruning_idx=0, nsamples=32000, l1_reg=l1).reshape(L, C)
        print(f"linear L={L} C={C} M={L*C} l1_reg={l1!r}: max err {np.abs(phi-truth).max():.2e}, zeros {int((phi==0).sum())} (truth {int((truth==0).sum())}), {time.time()-t:.1f}s")
    ev = local_event(f, x, {"rs": 42, "nsamples": 32000}, None, None, bg, 0)["Shapley Value"].values[::-1]
    print(f"   event-level (default) max err {np.abs(ev - truth.sum(1)).max():.2e}")
