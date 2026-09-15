import os, warnings, time
warnings.filterwarnings("ignore")
import numpy as np, torch, torch.nn as nn
torch.backends.cudnn.deterministic = True; torch.backends.cudnn.benchmark = False
torch.use_deterministic_algorithms(True)
torch.manual_seed(0)
dev = "cuda"
class M(nn.Module):
    def __init__(s): super().__init__(); s.l = nn.LSTM(4, 16, batch_first=True); s.h = nn.Linear(16, 1)
    def forward(s, x): o, _ = s.l(x); return s.h(o[:, -1])
m = M().to(dev)
x = torch.randn(3, 20, 4, device=dev)
# --- captum
import captum
from captum.attr import IntegratedGradients, FeatureAblation, Occlusion
for mode in ["eval", "train"]:
    getattr(m, mode)()
    try:
        a, delta = IntegratedGradients(m).attribute(x, baselines=torch.zeros_like(x), return_convergence_delta=True)
        print(f"captum {captum.__version__} IG (model.{mode}()) OK shape", tuple(a.shape), "max|delta|", float(delta.abs().max()))
    except Exception as e:
        print(f"captum IG (model.{mode}()) FAILED:", type(e).__name__, str(e).splitlines()[0][:200])
m.eval()
with torch.backends.cudnn.flags(enabled=False):
    a, delta = IntegratedGradients(m).attribute(x, baselines=torch.zeros_like(x), return_convergence_delta=True)
    print("captum IG (model.eval(), cudnn disabled) OK max|delta|", float(delta.abs().max()))
fa = FeatureAblation(m).attribute(x); print("captum FeatureAblation OK", tuple(fa.shape))
oc = Occlusion(m).attribute(x, sliding_window_shapes=(1, 1), baselines=0.0); print("captum Occlusion OK", tuple(oc.shape))
# --- timeshap
import timeshap
from timeshap.explainer import event_level, feature_level
from timeshap.wrappers import TorchModelWrapper
def f(arr):
    with torch.no_grad():
        return m(torch.as_tensor(arr, dtype=torch.float32, device=dev)).cpu().numpy()
xi = x[:1].cpu().numpy(); base = np.zeros((1, 4))
t0 = time.time()
ev = event_level(f, xi, base, pruned_idx=0, random_seed=42, nsamples=1000)
ft = feature_level(f, xi, base, pruned_idx=0, random_seed=42, nsamples=1000, model_feats=["c0","c1","c2","c3"])
pred = float(f(xi)[0,0]); base_pred = float(f(np.zeros_like(xi))[0,0])
print(f"timeshap {timeshap.__version__ if hasattr(timeshap,'__version__') else ''} event_level OK rows={len(ev)} sum={ev['Shapley Value'].sum():.5f} f(x)-f(base)={pred-base_pred:.5f}; feature_level OK rows={len(ft)} ({time.time()-t0:.1f}s)")
