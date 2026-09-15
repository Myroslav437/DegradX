import os, sys, warnings; warnings.filterwarnings("ignore")
import numpy as np
if os.environ.get("SHAP_KERNEL_SHIM") == "1":
    import shap.explainers._kernel as _k
    if not hasattr(_k, "Kernel"): _k.Kernel = _k.KernelExplainer
import shap
from timeshap.explainer import event_level, feature_level, cell_level
rng = np.random.default_rng(1)
T, C = 30, 4
W1 = rng.normal(size=(C, 8)); w2 = rng.normal(size=8); decay = 0.9 ** np.arange(T)[::-1]
def f(X):  # nonlinear, recency-weighted
    X = np.asarray(X, float); h = np.tanh(X @ W1) @ w2
    return (h * decay).sum(1, keepdims=True)
x = rng.normal(size=(1, T, C)); b = np.zeros((1, C))
ev = event_level(f, x, b, pruned_idx=10, random_seed=42, nsamples=600)
ft = feature_level(f, x, b, pruned_idx=10, random_seed=42, nsamples=600, model_feats=list("abcd"))
ce = None
out = np.concatenate([ev["Shapley Value"].to_numpy(), ft["Shapley Value"].to_numpy()] + ([ce["Shapley Value"].to_numpy()] if ce is not None else []))
np.save(sys.argv[1], out); print(shap.__version__, "n values", out.shape, "cell rows", None if ce is None else len(ce))
