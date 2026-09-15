"""Validate TimeSHAP against exact Shapley values of a linear sequence model.
For f(X)=sum_{t,c} W[t,c] X[t,c] and baseline event b, exact event-level phi_t = sum_c W[t,c](x[t,c]-b[c]),
feature-level phi_c = sum_t W[t,c](x[t,c]-b[c]). With M groups and nsamples >= 2^M - 2 KernelSHAP enumerates all coalitions."""
import os, sys, warnings
warnings.filterwarnings("ignore")
import numpy as np
if os.environ.get("SHAP_KERNEL_SHIM") == "1":
    import shap.explainers._kernel as _k
    if not hasattr(_k, "Kernel"):
        _k.Kernel = _k.KernelExplainer
        print("shim: shap.explainers._kernel.Kernel = KernelExplainer")
import shap, timeshap
from timeshap.explainer import event_level, feature_level, cell_level
print("shap", shap.__version__, "numpy", np.__version__)
rng = np.random.default_rng(0)
T, C = 8, 3
W = rng.normal(size=(T, C)); x = rng.normal(size=(1, T, C)); b = rng.normal(size=(1, C))
f = lambda X: np.einsum("ntc,tc->n", np.asarray(X, dtype=float), W)[:, None]
exact_ev = ((x[0] - b) * W).sum(1)          # per event, event index 0 = oldest
exact_ft = ((x[0] - b) * W).sum(0)
ev = event_level(f, x, b, pruned_idx=0, random_seed=42, nsamples=2**T)
ft = feature_level(f, x, b, pruned_idx=0, random_seed=42, nsamples=2**C, model_feats=[f"c{i}" for i in range(C)])
# TimeSHAP labels events "Event -1" = most recent
ev_vals = np.array([ev.loc[ev.Feature == f"Event -{k}", "Shapley Value"].item() for k in range(1, T+1)])[::-1]
ft_vals = ft["Shapley Value"].to_numpy()
print("event  max|err| =", np.abs(ev_vals - exact_ev).max(), " sum phi =", ev_vals.sum(), " f(x)-f(b) =", (f(x) - f(np.repeat(b[:, None, :], T, 1)))[0, 0])
print("feature max|err| =", np.abs(ft_vals - exact_ft).max())
