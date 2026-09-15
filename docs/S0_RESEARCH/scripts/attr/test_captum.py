"""captum 0.9.0 IG / Occlusion / FeatureAblation on a (B, L, C) -> (B,1) LSTM regressor, GPU, eval mode."""
import time, traceback
import numpy as np
import torch, torch.nn as nn
import captum
from captum.attr import IntegratedGradients, Occlusion, FeatureAblation
print("torch", torch.__version__, "captum", captum.__version__, "cudnn", torch.backends.cudnn.version())

dev = "cuda"
torch.manual_seed(0)
B, L, C = 16, 40, 6

class LSTMReg(nn.Module):
    def __init__(self, dropout=0.2):
        super().__init__()
        self.lstm = nn.LSTM(C, 64, num_layers=2, batch_first=True, dropout=dropout)
        self.head = nn.Linear(64, 1)
    def forward(self, x):
        o, _ = self.lstm(x)
        return self.head(o[:, -1, :])   # (B,1)

model = LSTMReg().to(dev).eval()
x = torch.randn(B, L, C, device=dev)
fwd = lambda inp: model(inp).squeeze(-1)  # (B,) scalar per example -> no target needed

def attempt(name, fn):
    try:
        t = time.time(); out = fn(); torch.cuda.synchronize()
        print(f"[OK] {name} ({time.time()-t:.2f}s)", out if not isinstance(out, torch.Tensor) else tuple(out.shape))
        return out
    except Exception as e:
        print(f"[FAIL] {name}: {type(e).__name__}: {str(e).splitlines()[0]}")

ig = IntegratedGradients(fwd)
print("\n== IG defaults, model.eval(), cudnn enabled")
attempt("ig.attribute(x) eval+cudnn", lambda: ig.attribute(x))

print("\n== workaround 1: torch.backends.cudnn.flags(enabled=False)")
def w1():
    with torch.backends.cudnn.flags(enabled=False):
        a, d = ig.attribute(x, return_convergence_delta=True)
    return (tuple(a.shape), "max|delta|=%.2e" % d.abs().max().item(), "delta shape", tuple(d.shape))
attempt("IG eval + cudnn disabled", w1)

print("\n== workaround 2: model.train() (dropout active -> nondeterministic)")
def w2():
    model.train()
    a1 = ig.attribute(x); a2 = ig.attribute(x)
    model.eval()
    return "two train-mode runs identical: %s" % torch.allclose(a1, a2)
attempt("IG train mode", w2)

print("\n== workaround 3: model.train() but dropout modules eval")
def w3():
    model.train()
    for m in model.modules():
        if isinstance(m, nn.Dropout): m.eval()
    model.lstm.dropout = 0.0  # nn.LSTM inter-layer dropout is a float attribute, not a module
    a1 = ig.attribute(x); a2 = ig.attribute(x)
    model.lstm.dropout = 0.2; model.eval()
    with torch.backends.cudnn.flags(enabled=False):
        a3 = ig.attribute(x)
    return "reproducible: %s, matches cudnn-disabled eval: max abs diff %.2e" % (torch.allclose(a1, a2), (a1 - a3).abs().max().item())
attempt("IG train-mode/no-dropout vs cudnn-off eval", w3)

print("\n== IG internal_batch_size / methods")
def w4():
    with torch.backends.cudnn.flags(enabled=False):
        a = ig.attribute(x)
        b = ig.attribute(x, internal_batch_size=64)
        r = ig.attribute(x, method="riemann_trapezoid")
    return "internal_batch_size=64 max diff %.2e ; trapezoid vs GL max diff %.2e" % ((a - b).abs().max().item(), (a - r).abs().max().item())
attempt("IG internal_batch_size", w4)

print("\n== IG on linear reference model (exactness vs a*(x-b))")
A = torch.randn(L, C, device=dev); A[:, -1] = 0
lin = lambda inp: (inp * A).sum(dim=(1, 2))
bl = torch.randn(1, L, C, device=dev)
a, d = IntegratedGradients(lin).attribute(x, baselines=bl, return_convergence_delta=True)
print("IG linear max err %.2e, max|delta| %.2e" % ((a - A * (x - bl)).abs().max().item(), d.abs().max().item()))

print("\n== Occlusion (1,1) window == FeatureAblation default mask, on linear model")
occ = Occlusion(lin).attribute(x, sliding_window_shapes=(1, 1), baselines=bl)
fa = FeatureAblation(lin).attribute(x, baselines=bl)
print("occlusion err %.2e ; FA err %.2e ; occ==fa %s" % ((occ - A * (x - bl)).abs().max().item(), (fa - A * (x - bl)).abs().max().item(), torch.allclose(occ, fa, atol=1e-5)))

print("\n== Occlusion / FeatureAblation on LSTM: default baselines(0) and perturbations_per_eval")
calls = []
def counting(inp):
    calls.append(inp.shape[0]);
    with torch.no_grad():
        return fwd(inp)
for ppe in [1, 64]:
    calls.clear(); t = time.time()
    o = Occlusion(counting).attribute(x, sliding_window_shapes=(1, 1), perturbations_per_eval=ppe); torch.cuda.synchronize()
    print(f"Occlusion ppe={ppe}: {time.time()-t:.2f}s, forward calls {len(calls)}, max batch {max(calls)}, out {tuple(o.shape)}")
calls.clear(); t = time.time()
fa = FeatureAblation(counting).attribute(x, perturbations_per_eval=64); torch.cuda.synchronize()
print(f"FeatureAblation ppe=64: {time.time()-t:.2f}s, calls {len(calls)}, equal to occlusion: {torch.allclose(o, fa, atol=1e-5)}")

print("\n== FO over whole channel (all positions of channel c at once) via feature_mask")
mask = torch.arange(C, device=dev).view(1, 1, C).expand(1, L, C)
fa_ch = FeatureAblation(counting).attribute(x, feature_mask=mask, perturbations_per_eval=C)
print("channel-level shape", tuple(fa_ch.shape), "constant along L:", torch.allclose(fa_ch, fa_ch[:, :1, :].expand_as(fa_ch)))
occ_ch = Occlusion(counting).attribute(x, sliding_window_shapes=(L, 1))
print("Occlusion window (L,1) equals channel-level FA:", torch.allclose(occ_ch, fa_ch, atol=1e-5))
