"""timeshap 1.0.4: (a) full-grid cell output mapping + exactness on a linear reference model; (b) cost scaling."""
import time, sys
import numpy as np
import torch
import shap.explainers._kernel as _k
if not hasattr(_k, "Kernel"):
    _k.Kernel = _k.KernelExplainer
from timeshap.explainer import local_event, local_feat, local_cell_level
from timeshap.explainer.kernel import TimeShapKernel

rng = np.random.default_rng(0)

def linear_ref(L, C):
    A = rng.normal(size=(L, C)); A[:, -1] = 0.0          # last channel zero-weight
    def f(x):
        return np.einsum("blc,lc->b", x, A)[:, None]     # (B,1)
    return A, f

# (a) mapping + exactness
L, C = 10, 3
A, f = linear_ref(L, C)
x = rng.normal(size=(1, L, C)); bg = rng.normal(size=(1, C))
truth = A * (x[0] - bg)                                   # exact Shapley for additive model
ev = local_event(f, x, {"rs": 42, "nsamples": 32000}, None, None, bg, 0)
fe = local_feat(f, x, {"rs": 42, "nsamples": 32000}, None, None, bg, 0)
ce = local_cell_level(f, x, {"rs": 42, "nsamples": 32000, "top_x_events": L, "top_x_feats": C}, ev, fe, None, None, bg, 0)
grid = np.zeros((L, C))
for _, r in ce.iterrows():
    u = L - int(str(r["Event"]).split()[-1].lstrip("-"))  # "Event -k" -> position L-k
    c = int(str(r["Feature"]).split()[-1])
    grid[u, c] = r["Shapley Value"]
print("event-level exact (Event -1 is last position):",
      np.allclose(ev["Shapley Value"].values, truth.sum(1)[::-1], atol=1e-6))
print("feature-level exact:", np.allclose(fe["Shapley Value"].values, truth.sum(0), atol=1e-6))
print("cell full-grid (default l1_reg=auto) max abs err: %.2e, zeros %d (truth zeros %d)" % (np.abs(grid - truth).max(), (grid == 0).sum(), (truth == 0).sum()))
ker = TimeShapKernel(f, bg, 42, "cell", varying=(list(range(L)), list(range(C))))
phi = ker.shap_values(x, pruning_idx=0, nsamples=32000, l1_reg=False).reshape(L, C)
print("cell full-grid direct kernel l1_reg=False max abs err: %.2e" % np.abs(phi - truth).max())

# (b) scaling of full-grid cell level with a GPU LSTM
dev = "cuda"
torch.manual_seed(0)
class M(torch.nn.Module):
    def __init__(s, C):
        super().__init__(); s.l = torch.nn.LSTM(C, 32, batch_first=True); s.h = torch.nn.Linear(32, 1)
    def forward(s, x):
        return s.h(s.l(x)[0][:, -1])
for (L, C, ns) in [(30, 8, 32000), (60, 8, 32000), (100, 8, 32000)]:
    m = M(C).to(dev).eval()
    def g(xx):
        out = []
        with torch.no_grad():
            for i in range(0, xx.shape[0], 16384):
                out.append(m(torch.as_tensor(xx[i:i+16384], dtype=torch.float32, device=dev)).cpu().numpy())
        return np.concatenate(out)
    x = rng.normal(size=(1, L, C)); bg = np.zeros((1, C))
    t = time.time(); ev = local_event(g, x, {"rs": 42, "nsamples": ns}, None, None, bg, 0); te = time.time() - t
    t = time.time(); fe = local_feat(g, x, {"rs": 42, "nsamples": ns}, None, None, bg, 0); tf = time.time() - t
    ker = TimeShapKernel(g, bg, 42, "cell", varying=(list(range(L)), list(range(C))))
    t0 = time.time()
    phi_auto = ker.shap_values(x, pruning_idx=0, nsamples=ns)
    tc = time.time() - t0
    ker = TimeShapKernel(g, bg, 42, "cell", varying=(list(range(L)), list(range(C))))
    t0 = time.time()
    phi_nol1 = ker.shap_values(x, pruning_idx=0, nsamples=ns, l1_reg=False)
    tc2 = time.time() - t0
    print(f"L={L} C={C} nsamples={ns}: event {te:.1f}s (nonzero {np.count_nonzero(ev['Shapley Value'])}/{L}), feat {tf:.1f}s, "
          f"cell-full auto {tc:.1f}s (nonzero {np.count_nonzero(phi_auto)}/{L*C}), cell-full l1_reg=False {tc2:.1f}s")
    sys.stdout.flush()
