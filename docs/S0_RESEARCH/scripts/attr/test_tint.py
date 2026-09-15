"""tint 0.3.0 on py3.12 / torch 2.14 / captum 0.9.0: do its occlusion-type methods run and match captum?"""
import torch, torch.nn as nn
import captum.attr as ca
import tint.attr as ta

dev = "cuda"; torch.manual_seed(0)
B, L, C = 8, 20, 5
class R(nn.Module):
    def __init__(s):
        super().__init__(); s.l = nn.LSTM(C, 32, batch_first=True); s.h = nn.Linear(32, 1)
    def forward(s, x):
        return s.h(s.l(x)[0][:, -1])  # (B,1)
m = R().to(dev).eval()
x = torch.randn(B, L, C, device=dev); bl = torch.randn(1, L, C, device=dev)

def run(name, fn):
    try:
        out = fn(); print(f"[OK] {name}", tuple(out.shape) if hasattr(out, "shape") else out); return out
    except Exception as e:
        print(f"[FAIL] {name}: {type(e).__name__}: {str(e).splitlines()[0] if str(e) else ''}")

with torch.no_grad():
    c_occ = ca.Occlusion(m).attribute(x, sliding_window_shapes=(1, 1), baselines=bl, target=0)
t_occ = run("tint.Occlusion (1,1)", lambda: ta.Occlusion(m).attribute(x, sliding_window_shapes=(1, 1), baselines=bl, target=0))
if t_occ is not None:
    print("   equals captum.Occlusion:", torch.allclose(c_occ, t_occ, atol=1e-5))
t_fa = run("tint.FeatureAblation", lambda: ta.FeatureAblation(m).attribute(x, baselines=bl, target=0))
if t_fa is not None:
    print("   equals captum.Occlusion:", torch.allclose(c_occ, t_fa, atol=1e-5))
run("tint TimeForwardTunnel(TemporalOcclusion) regression", lambda: ta.TimeForwardTunnel(ta.TemporalOcclusion(m)).attribute(
    x, sliding_window_shapes=(1,), baselines=bl[:, :1, :].expand(1, L, C).contiguous(), task="regression", show_progress=False))
xtr = torch.randn(64, L, C, device=dev)
run("tint AugmentedOcclusion (1,1)", lambda: ta.AugmentedOcclusion(m, data=xtr, n_sampling=10).attribute(x, sliding_window_shapes=(1, 1), target=0))
f1 = lambda inp: m(inp).squeeze(-1)
run("tint TimeForwardTunnel(TemporalOcclusion) regression, (B,) output", lambda: ta.TimeForwardTunnel(ta.TemporalOcclusion(f1)).attribute(
    x, sliding_window_shapes=(1,), baselines=bl[:, :1, :].expand(1, L, C).contiguous(), task="regression", show_progress=False))
