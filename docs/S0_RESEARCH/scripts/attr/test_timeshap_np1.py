"""Probe timeshap 1.0.4 behaviour on a toy LSTM regressor (numpy windows, no DataFrames)."""
import sys, time, warnings, traceback
import numpy as np
import torch, torch.nn as nn

# --- shim: timeshap 1.0.4 imports `Kernel` which shap>=0.43 renamed to KernelExplainer
import shap, shap.explainers._kernel as _k
if not hasattr(_k, "Kernel"):
    _k.Kernel = _k.KernelExplainer
print("shap", shap.__version__, "numpy", np.__version__, "torch", torch.__version__)

import timeshap
from timeshap.explainer import local_pruning, local_event, local_feat, local_cell_level, calc_local_report
from timeshap.explainer.kernel import TimeShapKernel
from timeshap.utils import calc_avg_event, get_avg_score_with_avg_event
from timeshap.wrappers import TorchModelWrapper
print("timeshap", timeshap.__version__)

torch.manual_seed(0); np.random.seed(0)
L, C = 12, 4
dev = "cuda" if torch.cuda.is_available() else "cpu"

class LSTMReg(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(C, 16, batch_first=True)
        self.head = nn.Linear(16, 1)
    def forward(self, x):
        o, _ = self.lstm(x)
        return self.head(o[:, -1, :])          # (B, 1)

model = LSTMReg().to(dev).eval()
calls = []
def f(x: np.ndarray) -> np.ndarray:
    calls.append(x.shape)
    with torch.no_grad():
        return model(torch.as_tensor(x, dtype=torch.float32, device=dev)).cpu().numpy()  # (B,1)

X_train = np.random.randn(200, L, C)
x = np.random.randn(1, L, C)

# baseline: average (median) event, as in the AReM tutorial
flat = X_train.reshape(-1, 1, C)
avg_event = calc_avg_event(flat, numerical_feats=list(range(C)), categorical_feats=[])
print("calc_avg_event type/shape:", type(avg_event).__name__, avg_event.shape)
baseline = avg_event.values  # (1, C)

def section(name):
    print("\n=====", name)

section("nsamples / rs omitted in local_event dict")
try:
    calls.clear()
    ev = local_event(f, x, {}, None, None, baseline, 0)
    print(ev.head())
except Exception as e:
    print("EXCEPTION:", type(e).__name__, e)

section("local_event rs=42 nsamples=32000, pruning_idx=0")
calls.clear(); t = time.time()
ev = local_event(f, x, {"rs": 42, "nsamples": 32000}, None, None, baseline, 0)
print("time %.2fs, #model calls %d, call shapes (first 5) %s" % (time.time() - t, len(calls), calls[:5]))
print(ev.to_string())
ev2 = local_event(f, x, {"rs": 42, "nsamples": 32000}, None, None, baseline, 0)
print("same seed reproducible:", np.allclose(ev["Shapley Value"].values, ev2["Shapley Value"].values))
print("sum phi = f(x)-f(bg):", ev["Shapley Value"].sum(), f(x)[0, 0] - f(np.tile(baseline, (1, L, 1)))[0, 0])

section("local_event nsamples=500 (sampling regime, l1_reg auto)")
e1 = local_event(f, x, {"rs": 1, "nsamples": 500}, None, None, baseline, 0)["Shapley Value"].values
e2 = local_event(f, x, {"rs": 2, "nsamples": 500}, None, None, baseline, 0)["Shapley Value"].values
print("rs=1:", np.round(e1, 4)); print("rs=2:", np.round(e2, 4)); print("#exact zeros rs1:", (e1 == 0).sum())

section("local_event rs=None twice (seed handling)")
en1 = local_event(f, x, {"nsamples": 500}, None, None, baseline, 0)["Shapley Value"].values
en2 = local_event(f, x, {"nsamples": 500}, None, None, baseline, 0)["Shapley Value"].values
print("identical with rs=None:", np.allclose(en1, en2))

section("local_feat rs=42 nsamples=32000")
fe = local_feat(f, x, {"rs": 42, "nsamples": 32000}, None, None, baseline, 0)
print(fe.to_string())

section("pruning: tol=0.025 (tutorial value) and tol=0")
for tol in [0.025, 0]:
    try:
        pdata, pidx = local_pruning(f, x, {"tol": tol}, baseline, None, None, False)
        print("tol", tol, "coal_prun_idx", pidx, "-> pruning_idx", x.shape[1] + pidx)
    except Exception as e:
        print("tol", tol, "EXCEPTION", type(e).__name__, e)

section("cell level, tutorial style top_x_events=3 top_x_feats=3")
ce = local_cell_level(f, x, {"rs": 42, "nsamples": 32000, "top_x_events": 3, "top_x_feats": 3}, ev, fe, None, None, baseline, 0)
print(ce.to_string())

section("cell level, full grid: top_x_events=L top_x_feats=C, pruning_idx=0")
calls.clear(); t = time.time()
ce_full = local_cell_level(f, x, {"rs": 42, "nsamples": 32000, "top_x_events": L, "top_x_feats": C}, ev, fe, None, None, baseline, 0)
print("time %.2fs  rows %d (L*C=%d)  #calls %d  max batch %s" % (time.time() - t, len(ce_full), L * C, len(calls), max(calls)))
print(ce_full.head(8).to_string())
print("labels sample:", ce_full["Event"].unique()[:4], ce_full["Feature"].unique()[:4])
print("special rows:", ce_full[ce_full["Event"].astype(str).str.contains("Other|Pruned") | ce_full["Feature"].astype(str).str.contains("Other|Pruned")].shape[0])
print("# exact zeros:", (ce_full["Shapley Value"] == 0).sum(), "of", len(ce_full))

section("direct TimeShapKernel cell mode, full grid, l1_reg=False")
ker = TimeShapKernel(f, baseline, 42, "cell", varying=(list(range(L)), list(range(C))))
t = time.time()
phi = ker.shap_values(x, pruning_idx=0, nsamples=32000, l1_reg=False)
print("time %.2fs shape %s  nsamples used %d  M %d  #zeros %d" % (time.time() - t, phi.shape, ker.nsamples, ker.M, (phi == 0).sum()))
grid = phi.reshape(L, C)
print("sum:", grid.sum(), "f(x)-f(bg):", ker.fx[0] - ker.fnull[0])
ker2 = TimeShapKernel(f, baseline, 42, "cell", varying=(list(range(L)), list(range(C))))
phi_auto = ker2.shap_values(x, pruning_idx=0, nsamples=32000)
print("l1_reg default('auto') zeros:", (phi_auto == 0).sum(), " corr with l1_reg=False:", np.corrcoef(phi, phi_auto)[0, 1])

section("calc_local_report with pruning_dict=None")
out = calc_local_report(f, x, None, {"rs": 42, "nsamples": 2000}, {"rs": 42, "nsamples": 2000}, None, baseline)
print([type(o).__name__ for o in out])

section("TorchModelWrapper side effect on train mode")
model.eval()
wr = TorchModelWrapper(model)
_ = wr.predict_last_hs(x)
print("model.training after wrapper call:", model.training)
