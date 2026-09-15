"""Usability measures (paper §3.5.2 as amended by C2): accuracy gate, permutation importance on null channels (gated),
predictability and conditional permutation importance on redundant zero-weight channels (reported), term ablation.

Increases in error are normalised by the variance of y over the test windows (NMSE); intervals are BCa bootstraps over
test units (scipy.stats.bootstrap), with per-unit squared-error sums as the resampled quantity.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import bootstrap
from sklearn.linear_model import RidgeCV


def unit_sums(err2: np.ndarray, unit_idx: np.ndarray):
    units, inv = np.unique(unit_idx, return_inverse=True)
    return np.bincount(inv, weights=err2), np.bincount(inv).astype(float)


def nmse_increase_ci(sse_base: np.ndarray, sse_alt: np.ndarray, n: np.ndarray, var_y: float, *, seed: int, n_resamples: int = 10000) -> dict:
    def stat(idx, axis=-1):
        idx = np.asarray(idx, int)
        return (sse_alt[idx].sum(axis=axis) - sse_base[idx].sum(axis=axis)) / n[idx].sum(axis=axis) / var_y

    idx = np.arange(len(n))
    point = float(stat(idx))
    res = bootstrap((idx,), stat, vectorized=True, n_resamples=n_resamples, confidence_level=0.95, method="BCa",
                    random_state=np.random.default_rng(seed))
    return {"nmse_increase": point, "ci_low": float(res.confidence_interval.low), "ci_high": float(res.confidence_interval.high), "units": int(len(n))}


def permute_channel(X: np.ndarray, c: int, rng: np.random.Generator) -> np.ndarray:
    """Swap channel c's whole window slice between test windows (declarations: permuted across windows)."""
    Xp = X.copy()
    Xp[:, :, c] = X[rng.permutation(len(X)), :, c]
    return Xp


def ridge_for_channel(Xtr: np.ndarray, c: int, max_windows: int, rng: np.random.Generator):
    """RidgeCV predicting channel c's window (L values) from the other channels' windows (flattened), trained on training
    windows; features standardised with training statistics."""
    idx = rng.choice(len(Xtr), size=min(max_windows, len(Xtr)), replace=False)
    A = np.delete(Xtr[idx], c, axis=2).reshape(len(idx), -1)
    B = Xtr[idx, :, c]
    mu, sd = A.mean(0), np.where(A.std(0) > 0, A.std(0), 1.0)
    model = RidgeCV(alphas=np.logspace(-3, 3, 13)).fit((A - mu) / sd, B)
    return model, mu, sd


def ridge_predict(model, mu, sd, X: np.ndarray, c: int) -> np.ndarray:
    A = np.delete(X, c, axis=2).reshape(len(X), -1)
    return model.predict((A - mu) / sd)


def predictability_r2(model, mu, sd, X: np.ndarray, c: int) -> float:
    pred = ridge_predict(model, mu, sd, X, c)
    true = X[:, :, c]
    ss_res = np.sum((true - pred) ** 2)
    ss_tot = np.sum((true - true.mean()) ** 2)
    return float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")


def conditional_resample(model, mu, sd, X: np.ndarray, c: int, rng: np.random.Generator) -> np.ndarray:
    """Model-X style conditional resampling: channel c := ridge prediction from the other channels + residuals permuted
    across windows (declarations usability.redundant_channels)."""
    pred = ridge_predict(model, mu, sd, X, c)
    resid = X[:, :, c] - pred
    Xc = X.copy()
    Xc[:, :, c] = pred + resid[rng.permutation(len(X))]
    return Xc
