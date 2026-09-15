"""Candidate capacity-fade families and their fitting (paper §3.3 step two; declarations ``trajectory_families``).

All families are fitted to y_n = q_n / q1 (raw capacity over the unit's robust early-life reference) against
n = position / 1000 (thousands of cycles, for conditioning), by ``scipy.optimize.least_squares`` (trf, linear
loss) from a deterministic set of starts; the start with the lowest cost wins.

* two_term_exponential [He et al. 2011]:  y = a e^{b n} + c e^{d n}
* rollover [Saxena et al. 2022]:          y = y0 + m_o n + (m_f - m_o) delta ln[(e^{n/delta} + e^{N_k/delta}) / (1 + e^{N_k/delta})]
                                          (m_o, m_f <= 0; delta, N_k in thousands of cycles)
* power_law:                              y = y0 - a n^b
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.optimize import least_squares

SCALE = 1000.0


def _exp2(p, n):
    a, b, c, d = p
    return a * np.exp(b * n) + c * np.exp(d * n)


def _rollover(p, n):
    y0, m_o, n_k, delta, m_f = p
    soft = np.logaddexp(n / delta, n_k / delta) - np.logaddexp(0.0, n_k / delta)
    return y0 + m_o * n + (m_f - m_o) * delta * soft


def _power(p, n):
    y0, a, b = p
    return y0 - a * np.power(np.clip(n, 0.0, None), b)


@dataclass(frozen=True)
class Family:
    name: str
    params: tuple[str, ...]
    fn: Callable
    n_params: int

    def __call__(self, p, positions):
        return self.fn(np.asarray(p, dtype=float), np.asarray(positions, dtype=float) / SCALE)


FAMILIES = {
    "power_law": Family("power_law", ("y0", "a", "b"), _power, 3),
    "two_term_exponential": Family("two_term_exponential", ("a", "b", "c", "d"), _exp2, 4),
    "rollover": Family("rollover", ("y0", "m_o", "N_k", "delta", "m_f"), _rollover, 5),
}
SIMPLICITY_ORDER = ("power_law", "two_term_exponential", "rollover")


def _bounds_and_starts(name: str, n_max: float):
    """Bounds from declarations.trajectory_families (n in thousands of cycles) and deterministic starts."""
    if name == "two_term_exponential":
        lo, hi = [-2, -20, -2, -20], [2, 20, 2, 20]
        starts = [[1.0, -0.1, -1e-3, b] for b in (1.0, 3.0, 8.0)] + [[1.0, -0.5, -1e-4, 5.0 / max(n_max, 1e-3)], [0.5, 0.0, 0.5, -1.0]]
    elif name == "rollover":
        nk_hi = max(1.5 * n_max, 0.01)
        lo, hi = [0.5, -np.inf, 0.0, 0.005, -np.inf], [1.5, 0.0, nk_hi, 0.5, 0.0]
        starts = [[1.0, -0.05, f * n_max, dl, -1.0] for f in (0.3, 0.6, 0.9) for dl in (0.02, 0.1)]
    elif name == "power_law":
        lo, hi = [0.5, 0.0, 0.0], [1.5, np.inf, 5.0]
        starts = [[1.0, 0.2, b] for b in (0.5, 1.0, 2.0, 4.0)]
    else:
        raise KeyError(name)
    return np.array(lo, float), np.array(hi, float), [np.clip(np.array(s, float), np.array(lo) + 1e-9, np.array(hi) - 1e-9) for s in starts]


@dataclass
class FitResult:
    family: str
    params: np.ndarray
    rmse: float
    success: bool
    at_bound: list[str]


def fit_family(name: str, positions: np.ndarray, y: np.ndarray) -> FitResult:
    fam = FAMILIES[name]
    positions = np.asarray(positions, float)
    y = np.asarray(y, float)
    n_max = float(positions.max()) / SCALE
    lo, hi, starts = _bounds_and_starts(name, n_max)
    best = None
    for s in starts:
        try:
            r = least_squares(lambda p: fam(p, positions) - y, s, bounds=(lo, hi), method="trf", loss="linear", x_scale="jac", max_nfev=2000)
        except (ValueError, FloatingPointError):
            continue
        if np.isfinite(r.cost) and (best is None or r.cost < best.cost):
            best = r
    if best is None:
        return FitResult(name, np.full(fam.n_params, np.nan), np.nan, False, [])
    rmse = float(np.sqrt(np.mean((fam(best.x, positions) - y) ** 2)))
    tol = 1e-6 * np.maximum(1.0, np.abs(hi - lo))
    at_bound = [fam.params[i] for i in range(fam.n_params)
                if (np.isfinite(lo[i]) and best.x[i] - lo[i] < tol[i]) or (np.isfinite(hi[i]) and hi[i] - best.x[i] < tol[i])]
    return FitResult(name, best.x, rmse, bool(best.success), at_bound)


def contiguous_folds(n: int, k: int = 5) -> list[np.ndarray]:
    edges = np.linspace(0, n, k + 1).round().astype(int)
    return [np.arange(edges[i], edges[i + 1]) for i in range(k)]


def cv_rmse(name: str, positions: np.ndarray, y: np.ndarray, k: int = 5) -> float:
    """Mean over k contiguous held-out blocks of the block RMSE (declarations trajectory_families.selection)."""
    positions, y = np.asarray(positions, float), np.asarray(y, float)
    errs = []
    for idx in contiguous_folds(len(y), k):
        if len(idx) == 0:
            continue
        train = np.setdiff1d(np.arange(len(y)), idx)
        fit = fit_family(name, positions[train], y[train])
        if not np.all(np.isfinite(fit.params)):
            return np.nan
        errs.append(np.sqrt(np.mean((FAMILIES[name](fit.params, positions[idx]) - y[idx]) ** 2)))
    return float(np.mean(errs)) if errs else np.nan
