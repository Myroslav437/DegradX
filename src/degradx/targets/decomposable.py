"""Decomposable target, attribution ground truth, reference model and transfer target (paper Eq. 4-6, amended by C1/C4).

For a window W of L positions ending at t (u = t-L+1..t) and channels c:
    w_{u,c}    = kappa_c * pi_u,  kappa_c = beta_c / (phi_c(1) - phi_c(0)) on weighted channels, 0 otherwise
    y          = sum_{u,c} w_{u,c} (m_{u,c} - x0_c) + sum_{u,c} w_{u,c} p_{u,c}                         (Eq. 4)
    phi*_{u,c} = w_{u,c} (m_{u,c} - x0_c)  [graded]  +  w_{u,c} p_{u,c}  [sparse]                        (Eq. 5)
    g(x)       = sum_{u,c} w_{u,c} (x_{u,c} - x0_c)          reference model; g(x) - y = sum w eps
    phi*(b)    = w (m + p - b)                               ground truth from any baseline b (C4)
    R_t        = T - t                                        transfer target (Eq. 6)
Position index within the window: 0 = oldest (u = t-L+1), L-1 = last (u = t).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

WEIGHTINGS = ("recency", "uniform", "final_position")


def position_profile(kind: str, L: int, half_life: float = 6.0) -> np.ndarray:
    """pi over window positions 0..L-1 (last = most recent), normalised to sum 1 (declarations target.position_profiles)."""
    if kind == "recency":
        age = np.arange(L - 1, -1, -1, dtype=float)  # t - u
        w = 2.0 ** (-age / half_life)
    elif kind == "uniform":
        w = np.ones(L)
    elif kind == "final_position":
        w = np.zeros(L)
        w[-1] = 1.0
    else:
        raise ValueError(kind)
    return w / w.sum()


@dataclass
class TargetSpec:
    channels: list[str]
    kappa: np.ndarray      # (C,)
    x0: np.ndarray         # (C,)
    L: int
    pi: dict[str, np.ndarray]
    pattern_channel: int = 0

    @classmethod
    def build(cls, profile, beta: dict[str, float], L: int, half_life: float) -> "TargetSpec":
        chans = profile.all_channels
        weighted = [c for c in profile.weighted]
        b = {c: beta.get(c, 0.0) for c in weighted}
        tot = sum(b.values())
        b = {c: v / tot for c, v in b.items()} if tot > 0 else b  # renormalise after any demotion (declarations weights.guard)
        kappa = np.array([b[c] / profile.mappings[c].delta if c in b else 0.0 for c in chans])
        x0 = np.array([profile.x0[c] for c in chans])
        return cls(chans, kappa, x0, L, {k: position_profile(k, L, half_life) for k in WEIGHTINGS})

    def weights(self, kind: str) -> np.ndarray:
        return np.outer(self.pi[kind], self.kappa)  # (L, C)


def window_ends(T: int, L: int, stride: int = 1) -> np.ndarray:
    """1-based end positions t of all full windows (t = L..T)."""
    return np.arange(L, T + 1, stride)


def _windows(a: np.ndarray, ends: np.ndarray, L: int) -> np.ndarray:
    idx = ends[:, None] - L + np.arange(L)[None, :]  # 0-based rows
    return a[idx]


def unit_targets(unit, spec: TargetSpec, kind: str, ends: np.ndarray | None = None) -> dict:
    """Windows and all target quantities for one generated unit under one position weighting."""
    L = spec.L
    ends = window_ends(unit.T, L) if ends is None else ends
    Wt = spec.weights(kind)
    m = _windows(unit.m, ends, L)                    # (N, L, C)
    eps = _windows(unit.eps, ends, L)
    pch = np.zeros_like(m)
    pch[:, :, spec.pattern_channel] = _windows(unit.p, ends, L)
    x = m + eps + pch
    graded = Wt[None] * (m - spec.x0[None, None, :])
    sparse = Wt[None] * pch
    y = graded.sum(axis=(1, 2)) + sparse.sum(axis=(1, 2))
    g = (Wt[None] * (x - spec.x0[None, None, :])).sum(axis=(1, 2))
    return {"ends": ends, "x": x, "x_pattern_free": m + eps, "graded": graded, "sparse": sparse, "phi_star": graded + sparse, "y": y,
            "g": g, "noise_term": (Wt[None] * eps).sum(axis=(1, 2)), "R": unit.T - ends, "t": ends, "z_end": unit.z[ends - 1]}


def ground_truth_from_baseline(unit, spec: TargetSpec, kind: str, ends: np.ndarray, baseline: np.ndarray) -> np.ndarray:
    """phi*(b) = w (m + p - b) for a baseline window b of shape (L, C) or (C,) (C4)."""
    L = spec.L
    m = _windows(unit.m, ends, L)
    pch = np.zeros_like(m)
    pch[:, :, spec.pattern_channel] = _windows(unit.p, ends, L)
    b = baseline if baseline.ndim == 2 else np.broadcast_to(baseline, (L, len(spec.kappa)))
    return spec.weights(kind)[None] * (m + pch - b[None])


def reference_model(x: np.ndarray, spec: TargetSpec, kind: str) -> np.ndarray:
    """g(x) for windows x of shape (N, L, C)."""
    return (spec.weights(kind)[None] * (x - spec.x0[None, None, :])).sum(axis=(1, 2))
