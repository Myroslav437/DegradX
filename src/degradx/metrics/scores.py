"""Scores of an attribution map against the attribution ground truth, and controlled degradations of a map (S7).

Maps are (L, C) arrays for one window: rows are window positions (oldest first), columns channels.

Scores (benchmark scoring protocol; own code on top of scipy/sklearn, brief R2):
  rank_agreement(map, graded)          Spearman rho over all L x C cells (scipy.stats.spearmanr); NaN if either is constant
  retrieval_ap(score, labels)          average precision of |score| ranking the sparse-set cells (sklearn); NaN without positives
  zero_weight_mass(map, zero_channels) share of |map| on channels with zero target weight
Retrieval variants for decision D01:
  plain       |map| ranks cells against the sparse set
  paired      |map(x) - map(x without patterns)| ranks cells (for phi*, exactly the sparse field)
  detrended   |map - SG-smooth(map along positions)| per channel ranks cells (the §3.3 residual rule on the map)
Degradation operators (declarations responsiveness.operators), each (map, magnitude, rng) -> map.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import savgol_filter
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score


def rank_agreement(amap: np.ndarray, graded: np.ndarray) -> float:
    a, g = np.ravel(amap), np.ravel(graded)
    if np.std(a) == 0 or np.std(g) == 0:
        return float("nan")
    return float(spearmanr(a, g).statistic)


def retrieval_ap(score: np.ndarray, labels: np.ndarray) -> float:
    lab = np.ravel(labels).astype(bool)
    if not lab.any() or lab.all():
        return float("nan")
    return float(average_precision_score(lab, np.abs(np.ravel(score))))


def detrend(amap: np.ndarray, window: int = 11, polyorder: int = 2) -> np.ndarray:
    L = amap.shape[0]
    w = min(window, L if L % 2 == 1 else L - 1)
    if w <= polyorder:
        return amap - amap.mean(axis=0, keepdims=True)
    return amap - savgol_filter(amap, window_length=w, polyorder=polyorder, axis=0, mode="interp")


def zero_weight_mass(amap: np.ndarray, zero_channels: np.ndarray) -> float:
    tot = np.abs(amap).sum()
    return float(np.abs(amap[:, zero_channels]).sum() / tot) if tot > 0 else float("nan")


# ---- degradation operators -----------------------------------------------------------------------------------------
def op_added_noise(amap, mag, rng, scale=None):
    s = float(np.std(amap)) if scale is None else scale
    return amap + rng.normal(0.0, mag * s, size=amap.shape)


def op_shift_to_start(amap, mag, rng=None):
    out = (1.0 - mag) * amap
    out[0, :] += mag * amap.sum(axis=0)
    return out


def op_shift_to_end(amap, mag, rng=None):
    out = (1.0 - mag) * amap
    out[-1, :] += mag * amap.sum(axis=0)
    return out


def op_smoothing(amap, mag, rng=None):
    return amap.copy() if mag == 0 else gaussian_filter1d(amap, sigma=mag, axis=0, mode="nearest")


def op_permuted_fraction(amap, mag, rng):
    flat = amap.ravel().copy()
    n = int(round(mag * flat.size))
    if n >= 2:
        idx = rng.choice(flat.size, size=n, replace=False)
        flat[idx] = flat[rng.permutation(idx)]
    return flat.reshape(amap.shape)


OPERATORS = {"added_noise": op_added_noise, "shift_to_start": op_shift_to_start, "shift_to_end": op_shift_to_end,
             "smoothing": op_smoothing, "permuted_fraction": op_permuted_fraction}
