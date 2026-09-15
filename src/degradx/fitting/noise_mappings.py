"""Channel mappings phi_c and per-channel noise (paper §3.3 steps three and four).

Mappings: isotonic regression (sklearn, ``increasing='auto'``) of pooled (z, x_c) pairs over fitting-split units,
evaluated on a 101-point grid of z in [0, 1] and interpolated with a PCHIP (scipy) through the grid values, which
keeps the fit monotone and makes it continuously differentiable (declarations ``channel_mappings``). The capacity
mapping is the declared affine function phi_cap(z) = q1_bar - z (q1_bar - rho q_nom).

Noise: AR(1) per channel (declarations ``noise``): marginal variance and lag-1 autocorrelation of the residual
series, with positions occupied by detected patterns masked. Lag-1 autocorrelation uses
``statsmodels.tsa.stattools.acf(missing='conservative')`` on the residual with masked positions set to NaN, so
pairs that straddle a masked position do not contribute.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.interpolate import PchipInterpolator
from sklearn.isotonic import IsotonicRegression

Z_GRID = np.linspace(0.0, 1.0, 101)


@dataclass
class Mapping:
    channel: str
    grid: np.ndarray
    values: np.ndarray
    increasing: bool
    kind: str  # "isotonic_pchip" or "affine_capacity"

    def __call__(self, z):
        z = np.asarray(z, float)
        if self.kind == "affine_capacity":
            a, b = self.values  # phi(z) = a + b z
            return a + b * z
        interp = PchipInterpolator(self.grid, self.values, extrapolate=False)
        zc = np.clip(z, self.grid[0], self.grid[-1])  # outside [0, 1] the mapping is held at its end values
        return interp(zc)

    @property
    def delta(self) -> float:
        """phi_c(1) - phi_c(0)."""
        return float(self(1.0) - self(0.0))

    def as_dict(self) -> dict:
        return {"channel": self.channel, "kind": self.kind, "increasing": self.increasing,
                "grid": self.grid.tolist(), "values": np.asarray(self.values).tolist()}


def fit_isotonic_pchip(channel: str, z: np.ndarray, x: np.ndarray) -> Mapping:
    ok = np.isfinite(z) & np.isfinite(x)
    z, x = np.asarray(z, float)[ok], np.asarray(x, float)[ok]
    iso = IsotonicRegression(increasing="auto", out_of_bounds="clip").fit(z, x)
    inc = bool(iso.increasing_)
    vals = iso.predict(Z_GRID)
    # PCHIP needs strictly increasing knots; flat isotonic steps are allowed in values (monotone, not strict)
    return Mapping(channel, Z_GRID.copy(), vals, inc, "isotonic_pchip")


def affine_capacity(q1_bar: float, rho: float, q_nom: float) -> Mapping:
    return Mapping("capacity", np.array([0.0, 1.0]), np.array([q1_bar, -(q1_bar - rho * q_nom)]), False, "affine_capacity")


@dataclass
class AR1:
    variance: float
    phi: float
    n_used: int

    def as_dict(self) -> dict:
        return {"variance": self.variance, "phi": self.phi, "n_used": self.n_used}


def ar1_from_residuals(residuals: list[np.ndarray], masks: list[np.ndarray] | None = None) -> AR1:
    """Pooled AR(1) over units: variance of unmasked residuals; lag-1 autocorrelation averaged over units by length."""
    from statsmodels.tsa.stattools import acf

    vals, phis, weights = [], [], []
    for i, r in enumerate(residuals):
        r = np.asarray(r, float).copy()
        if masks is not None:
            r[np.asarray(masks[i], bool)] = np.nan
        good = np.isfinite(r)
        if good.sum() < 10:
            continue
        rc = r - np.nanmean(r)
        vals.append(rc[good])
        a = acf(rc, nlags=1, missing="conservative", fft=False)
        if np.isfinite(a[1]):
            phis.append(float(a[1]))
            weights.append(int(good.sum()))
    if not vals:
        return AR1(np.nan, np.nan, 0)
    allv = np.concatenate(vals)
    return AR1(float(np.var(allv)), float(np.average(phis, weights=weights)) if phis else np.nan, int(allv.size))


def ar1_sample(rng: np.random.Generator, n: int, variance: float, phi: float) -> np.ndarray:
    """Stationary AR(1) with the given marginal variance and lag-1 coefficient; zero mean (paper E[eps] = 0)."""
    phi = float(np.clip(phi, -0.999, 0.999))
    sd_innov = np.sqrt(max(variance, 0.0) * (1.0 - phi**2))
    e = np.empty(n)
    e[0] = rng.normal(0.0, np.sqrt(max(variance, 0.0)))
    innov = rng.normal(0.0, sd_innov, n)
    for t in range(1, n):
        e[t] = phi * e[t - 1] + innov[t]
    return e
