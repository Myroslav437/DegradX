"""Profile fidelity measures (paper §3.5.1): windows, discriminative score, Frechet distance in a TS2Vec representation
space, cross-channel covariance agreement, TSTR error ratio with a bootstrap over held-out units.

Measured units enter as their cleaned channel series (D12/D17, isolated masked readings linearly interpolated within the
unit for window-based measures); generated units as x without null channels (null channels have no measured
counterpart, C2). Windows have the target length L. Standardisation for encoder/discriminator uses measured
fitting-split statistics.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from scipy import linalg
from torch import nn

from degradx.utils.seeding import rng, seed_everything


@dataclass
class SeriesUnit:
    unit_id: str
    X: np.ndarray          # (n, C) channel values in the profile's channel order
    T: int | None          # EOL position (1-based) or None


def interpolate_nans(X: np.ndarray) -> np.ndarray:
    X = X.copy()
    idx = np.arange(len(X))
    for c in range(X.shape[1]):
        bad = ~np.isfinite(X[:, c])
        if bad.any() and (~bad).sum() >= 2:
            X[bad, c] = np.interp(idx[bad], idx[~bad], X[~bad, c])
    return X


def measured_series(units, channels) -> list[SeriesUnit]:
    """From ``degradx.fitting.profile.Unit`` objects: capacity plus channels, positions 1..T (or 1..n if censored)."""
    out = []
    for u in units:
        end = u.state.T if u.state.T is not None else len(u.q)
        cols = [u.q[:end]] + [u.channels[c][:end] for c in channels if c != "capacity"]
        out.append(SeriesUnit(u.cell_id, interpolate_nans(np.column_stack(cols)), u.state.T))
    return out


def generated_series(gen_units, n_channels: int) -> list[SeriesUnit]:
    return [SeriesUnit(f"gen{u.index}", u.x[:, :n_channels], u.T) for u in gen_units]


def windows(series: list[SeriesUnit], L: int, stride: int = 1, max_per_unit: int | None = None, seed: int = 0,
            with_rul: bool = False, with_elapsed: bool = False):
    """(N, L, C[+1]) windows, unit index per window, and (optionally) R = T - t at the window end."""
    g = np.random.default_rng(seed)
    Xs, us, rs = [], [], []
    for i, s in enumerate(series):
        n = len(s.X)
        if n < L or (with_rul and s.T is None):
            continue
        ends = np.arange(L, n + 1, stride)
        if max_per_unit is not None and len(ends) > max_per_unit:
            ends = np.sort(g.choice(ends, size=max_per_unit, replace=False))
        idx = ends[:, None] - L + np.arange(L)[None, :]
        W = s.X[idx]
        if with_elapsed:
            W = np.concatenate([W, (idx + 1)[:, :, None].astype(float)], axis=2)
        Xs.append(W)
        us.append(np.full(len(ends), i))
        if with_rul:
            rs.append((s.T - ends).astype(float))
    X = np.concatenate(Xs) if Xs else np.empty((0, L, series[0].X.shape[1] + int(with_elapsed)))
    U = np.concatenate(us) if us else np.empty(0, int)
    R = np.concatenate(rs) if rs else None
    return X, U, R


# ---- discriminative score (Yoon et al. 2019 post-hoc discriminator) ------------------------------------------------
class _GRUDisc(nn.Module):
    def __init__(self, c, hidden=16, layers=2):
        super().__init__()
        self.gru = nn.GRU(c, hidden, num_layers=layers, batch_first=True)
        self.head = nn.Linear(hidden, 1)

    def forward(self, x):
        out, _ = self.gru(x)
        return self.head(out[:, -1]).squeeze(-1)


def discriminative_score(meas_W, meas_U, gen_W, gen_U, mu, sd, *, seed: int, device: str, iterations: int = 2000, batch: int = 128) -> dict:
    """Unit-level 80/20 split within each source, classes balanced by subsampling windows; returns test accuracy,
    discriminative error 1 - acc and |acc - 0.5| (declarations fidelity.discriminator)."""
    g = rng(seed, "evaluation", "discriminator")
    seed_everything(seed)

    def split(U):
        units = np.unique(U)
        test = set(g.choice(units, size=max(1, int(round(0.2 * len(units)))), replace=False))
        return ~np.isin(U, list(test)), np.isin(U, list(test)), len(units) - len(test), len(test)

    mtr, mte, n_mtr, n_mte = split(meas_U)
    gtr, gte, n_gtr, n_gte = split(gen_U)

    def balance(A, B):
        n = min(len(A), len(B))
        return A[g.choice(len(A), n, replace=False)], B[g.choice(len(B), n, replace=False)]

    A_tr, B_tr = balance(meas_W[mtr], gen_W[gtr])
    A_te, B_te = balance(meas_W[mte], gen_W[gte])
    norm = lambda W: torch.from_numpy(((W - mu) / sd).astype(np.float32)).to(device)  # noqa: E731
    Xtr = torch.cat([norm(A_tr), norm(B_tr)])
    ytr = torch.cat([torch.zeros(len(A_tr)), torch.ones(len(B_tr))]).to(device)
    Xte = torch.cat([norm(A_te), norm(B_te)])
    yte = torch.cat([torch.zeros(len(A_te)), torch.ones(len(B_te))]).to(device)
    model = _GRUDisc(meas_W.shape[-1]).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    lossf = nn.BCEWithLogitsLoss()
    gen = torch.Generator().manual_seed(seed)
    for _ in range(iterations):
        idx = torch.randint(0, len(Xtr), (batch,), generator=gen).to(device)
        opt.zero_grad()
        loss = lossf(model(Xtr[idx]), ytr[idx])
        loss.backward()
        opt.step()
    model.eval()
    with torch.no_grad():
        pred = torch.cat([model(Xte[i:i + 8192]) for i in range(0, len(Xte), 8192)]) > 0
    acc = float((pred.float() == yte).float().mean())
    return {"accuracy": acc, "discriminative_error": 1.0 - acc, "abs_acc_minus_half": abs(acc - 0.5), "test_windows_per_class": int(len(A_te)),
            "train_units": {"measured": n_mtr, "generated": n_gtr}, "test_units": {"measured": n_mte, "generated": n_gte}}


# ---- Frechet distance in TS2Vec space (Jeha et al. 2022 Context-FID) -----------------------------------------------
def frechet_distance(a: np.ndarray, b: np.ndarray) -> float:
    mu1, mu2 = a.mean(axis=0), b.mean(axis=0)
    s1, s2 = np.cov(a, rowvar=False), np.cov(b, rowvar=False)
    covmean, _ = linalg.sqrtm(s1.dot(s2), disp=False)
    covmean = covmean.real
    return float(np.sum((mu1 - mu2) ** 2) + np.trace(s1 + s2 - 2.0 * covmean))


def train_encoder(train_W: np.ndarray, mu, sd, *, seed: int, device: str, output_dims: int = 320):
    from degradx.metrics.ts2vec import TS2Vec

    seed_everything(seed)
    enc = TS2Vec(input_dims=train_W.shape[-1], output_dims=output_dims, device=device, batch_size=16)
    loss = enc.fit(((train_W - mu) / sd).astype(np.float32), verbose=False)
    return enc, loss


def encode(enc, W, mu, sd) -> np.ndarray:
    return enc.encode(((W - mu) / sd).astype(np.float32), encoding_window="full_series", batch_size=256)


# ---- cross-channel covariance agreement -----------------------------------------------------------------------------
def channel_correlation(W: np.ndarray, mu, sd) -> np.ndarray:
    flat = ((W - mu) / sd).reshape(-1, W.shape[-1])
    return np.corrcoef(flat, rowvar=False)


def covariance_agreement(C_ref: np.ndarray, C_cmp: np.ndarray) -> dict:
    off = ~np.eye(len(C_ref), dtype=bool)
    return {"relative_frobenius": float(np.linalg.norm(C_cmp - C_ref) / np.linalg.norm(C_ref)),
            "mean_abs_delta_rho": float(np.mean(np.abs(C_cmp - C_ref)[off]))}


# ---- TSTR ratio bootstrap over held-out units -----------------------------------------------------------------------
def per_unit_sse(pred: np.ndarray, target: np.ndarray, unit_idx: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    units = np.unique(unit_idx)
    sse = np.array([np.sum((pred[unit_idx == u] - target[unit_idx == u]) ** 2) for u in units])
    n = np.array([np.sum(unit_idx == u) for u in units])
    return units, sse, n


def ratio_bootstrap(sse_a: np.ndarray, sse_b: np.ndarray, n: np.ndarray, *, seed: int, n_resamples: int = 10000, confidence: float = 0.95) -> dict:
    """RMSE_a / RMSE_b over units (paired: the same resampled units for both), BCa via scipy.stats.bootstrap."""
    from scipy.stats import bootstrap

    def stat(idx, axis=-1):
        idx = np.asarray(idx, int)
        return np.sqrt(sse_a[idx].sum(axis=axis) / n[idx].sum(axis=axis)) / np.sqrt(sse_b[idx].sum(axis=axis) / n[idx].sum(axis=axis))

    idx = np.arange(len(n))
    point = float(stat(idx))
    if len(n) < 3:
        return {"ratio": point, "ci_low": None, "ci_high": None, "units": int(len(n)), "method": "none (fewer than 3 units)"}
    res = bootstrap((idx,), stat, vectorized=True, n_resamples=n_resamples, confidence_level=confidence, method="BCa",
                    random_state=np.random.default_rng(seed))
    return {"ratio": point, "ci_low": float(res.confidence_interval.low), "ci_high": float(res.confidence_interval.high),
            "units": int(len(n)), "method": "BCa over held-out units"}
