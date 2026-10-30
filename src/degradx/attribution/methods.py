"""Attribution methods at their default configurations (paper §3.6; declarations attribution.methods), wrapped so that every
method explains the same function in raw input space: f(x_raw) = model(standardise(x_raw)) in target units. Attributions
are therefore in target units per cell and comparable with phi* = w (x~ - baseline).

  integrated_gradients  captum IntegratedGradients, n_steps 50, gausslegendre (captum defaults); baseline = declared window;
                        cuDNN disabled inside attribution (eval-mode RNN backward, S0 env.md)
  feature_occlusion     captum FeatureAblation with the default per-scalar mask (one cell at a time); baseline = declared window
  timeshap              timeshap 1.0.4 cell-level explanation over the full L x C grid: pruning off, top_x_events = L,
                        top_x_feats = C, nsamples 32000, l1_reg per declaration; background = the declared (1, C) event
The reference model g(x) = sum w (x - x0) is wrapped as a torch module so every method runs on it unchanged.
"""

from __future__ import annotations

import numpy as np
import torch
from torch import nn


class RawSpaceModel(nn.Module):
    """Trained LSTM behind its standardiser: raw windows in, target units out."""

    def __init__(self, trained):
        super().__init__()
        self.inner = trained.model
        sc = trained.scaler
        self.register_buffer("mu", torch.tensor(sc.mean, dtype=torch.float32))
        self.register_buffer("sd", torch.tensor(sc.std, dtype=torch.float32))
        self.y_mean, self.y_std = float(sc.y_mean), float(sc.y_std)

    def forward(self, x):
        return self.inner((x - self.mu) / self.sd) * self.y_std + self.y_mean


class ReferenceModel(nn.Module):
    """g(x) = sum_{u,c} w_{u,c} (x_{u,c} - x0_c)."""

    def __init__(self, weights: np.ndarray, x0: np.ndarray):
        super().__init__()
        self.register_buffer("w", torch.tensor(weights, dtype=torch.float32))
        self.register_buffer("x0", torch.tensor(x0, dtype=torch.float32))

    def forward(self, x):
        return ((x - self.x0) * self.w).sum(dim=(1, 2))


def _t(a, device):
    return torch.as_tensor(np.asarray(a, dtype=np.float32), device=device)


def integrated_gradients(model: nn.Module, X: np.ndarray, baseline: np.ndarray, device: str, batch: int = 64) -> np.ndarray:
    from captum.attr import IntegratedGradients

    model = model.to(device).eval()
    ig = IntegratedGradients(model)
    out = []
    b = _t(np.broadcast_to(baseline, X.shape[1:]), device)
    with torch.backends.cudnn.flags(enabled=False):
        for i in range(0, len(X), batch):
            xb = _t(X[i:i + batch], device)
            out.append(ig.attribute(xb, baselines=b.expand_as(xb).contiguous(), n_steps=50, method="gausslegendre").detach().cpu().numpy())
    return np.concatenate(out)


def feature_occlusion(model: nn.Module, X: np.ndarray, baseline: np.ndarray, device: str, batch: int = 16) -> np.ndarray:
    from captum.attr import FeatureAblation

    model = model.to(device).eval()
    fa = FeatureAblation(model)
    out = []
    b = _t(np.broadcast_to(baseline, X.shape[1:]), device)
    with torch.no_grad():
        for i in range(0, len(X), batch):
            xb = _t(X[i:i + batch], device)
            out.append(fa.attribute(xb, baselines=b.expand_as(xb).contiguous(), perturbations_per_eval=X.shape[1] * X.shape[2]).cpu().numpy())
    return np.concatenate(out)


def numpy_callable(model: nn.Module, device: str, chunk: int = 4096):
    model = model.to(device).eval()

    def f(xx):
        res = []
        with torch.no_grad(), torch.backends.cudnn.flags(enabled=True):
            for i in range(0, xx.shape[0], chunk):
                res.append(model(_t(xx[i:i + chunk], device)).float().cpu().numpy())
        return np.concatenate(res)[:, None]
    return f


def timeshap(model: nn.Module, X: np.ndarray, background_event: np.ndarray, device: str, *, seed: int, nsamples: int = 32000,
             l1_reg="auto") -> np.ndarray:
    """Cell-level TimeSHAP over the full grid via the package's kernel (the path local_cell_level takes with
    top_x_events = L and top_x_feats = C and no pruning; the kernel exposes l1_reg, which local_cell_level fixes at 'auto')."""
    from degradx.attribution.timeshap_compat import import_timeshap

    import_timeshap()
    from timeshap.explainer.kernel import TimeShapKernel

    f = numpy_callable(model, device)
    N, L, C = X.shape
    bg = np.asarray(background_event, dtype=float).reshape(1, C)
    out = np.zeros((N, L, C))
    for i in range(N):
        ker = TimeShapKernel(f, bg, seed, "cell", varying=(list(range(L)), list(range(C))))
        phi = ker.shap_values(X[i:i + 1].astype(float), pruning_idx=0, nsamples=nsamples, l1_reg=l1_reg)
        out[i] = np.asarray(phi, dtype=float).reshape(L, C)
    return out
