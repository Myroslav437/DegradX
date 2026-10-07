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


# ---- v2 (brief "DegradX v2"; declarations r3 declared_by_design.v2) ----------------------------------------------------
@dataclass
class BackfitResult:
    mapping: Mapping
    delta: np.ndarray            # (n_units,) offsets, median 0
    iterations: int
    converged: bool
    last_change_delta: float
    last_change_phi: float
    tolerance: float
    units_without_readings: int  # units with fewer than ``min_readings`` finite readings (delta = 0)
    history: list


def backfit_offsets(channel: str, z_units: list[np.ndarray], x_units: list[np.ndarray], *, tol_frac: float = 1e-4,
                    max_iter: int = 200, min_readings: int = 10) -> BackfitResult:
    """X2: m_{t,c} = phi_c(z_t) + delta_{c,i} (declarations v2.per_unit_offsets.estimation).

    Iteration 0: delta = 0, phi_c = isotonic + PCHIP on pooled (z, x). Iteration k: (1) phi_c = isotonic + PCHIP on pooled
    (z, x - delta_i); (2) delta_i = median over the unit's positions of (x - phi_c(z)); (3) delta_i -= median_i delta_i.
    Converged when both the largest offset change and the largest change of phi on its 101-point grid are within
    ``tol_frac`` * |phi_c(1) - phi_c(0)|."""
    n = len(z_units)
    zc = np.concatenate(z_units)
    enough = np.array([np.isfinite(x).sum() >= min_readings for x in x_units])
    delta = np.zeros(n)
    mp = fit_isotonic_pchip(channel, zc, np.concatenate(x_units))
    hist, converged, ch_d, ch_phi, tol = [], False, np.inf, np.inf, np.nan
    k = 0
    for k in range(1, max_iter + 1):
        mp_new = fit_isotonic_pchip(channel, zc, np.concatenate([x - d for x, d in zip(x_units, delta)]))
        d_new = np.array([np.nanmedian(x - mp_new(z)) if ok else 0.0 for x, z, ok in zip(x_units, z_units, enough)])
        d_new = d_new - np.median(d_new[enough]) if enough.any() else d_new
        d_new[~enough] = 0.0
        tol = tol_frac * abs(mp_new.delta)
        ch_d = float(np.max(np.abs(d_new - delta)))
        ch_phi = float(np.max(np.abs(np.asarray(mp_new.values) - np.asarray(mp.values))))
        hist.append({"iteration": k, "change_delta": ch_d, "change_phi": ch_phi, "tolerance": tol})
        delta, mp = d_new, mp_new
        if ch_d <= tol and ch_phi <= tol:
            converged = True
            break
    return BackfitResult(mp, delta, k, converged, ch_d, ch_phi, float(tol), int((~enough).sum()), hist)


def innovation_correlation(r: np.ndarray, phi: np.ndarray) -> np.ndarray:
    """X3: innovation correlation r_eps,ij = r_ij (1 - phi_i phi_j) / sqrt((1 - phi_i^2)(1 - phi_j^2)), so that AR(1)
    channels with lag-1 coefficients phi driven by innovations with this correlation have stationary correlation r."""
    phi = np.clip(np.asarray(phi, float), -0.999, 0.999)
    f = (1.0 - np.outer(phi, phi)) / np.sqrt(np.outer(1.0 - phi ** 2, 1.0 - phi ** 2))
    out = np.asarray(r, float) * f
    np.fill_diagonal(out, 1.0)
    return out


def nearest_correlation(A: np.ndarray, eig_floor: float = 1e-6, max_iter: int = 1000, tol: float = 1e-12) -> np.ndarray:
    """Nearest correlation matrix (Higham 2002, alternating projections with Dykstra's correction), then the minimum
    eigenvalue floored at ``eig_floor`` and the unit diagonal restored (declarations v2.correlated_noise.repair)."""
    A = (np.asarray(A, float) + np.asarray(A, float).T) / 2
    Y, dS = A.copy(), np.zeros_like(A)
    for _ in range(max_iter):
        R = Y - dS
        w, V = np.linalg.eigh(R)
        X = (V * np.maximum(w, 0.0)) @ V.T
        dS = X - R
        Y_new = X.copy()
        np.fill_diagonal(Y_new, 1.0)
        if np.linalg.norm(Y_new - Y, "fro") <= tol * max(1.0, np.linalg.norm(Y, "fro")):
            Y = Y_new
            break
        Y = Y_new
    w, V = np.linalg.eigh((Y + Y.T) / 2)
    Y = (V * np.maximum(w, eig_floor)) @ V.T
    d = np.sqrt(np.diag(Y))
    Y = Y / np.outer(d, d)
    np.fill_diagonal(Y, 1.0)
    return Y


def is_positive_definite(A: np.ndarray, eig_floor: float = 1e-6) -> bool:
    return bool(np.all(np.isfinite(A)) and np.linalg.eigvalsh((A + A.T) / 2).min() >= eig_floor)


def ar1_joint_sample(rng: np.random.Generator, n: int, variances: np.ndarray, phis: np.ndarray, innov_corr: np.ndarray) -> np.ndarray:
    """X3: (n, C) stationary vector AR(1) with diagonal coefficients ``phis``, marginal variances ``variances`` and
    innovation correlation ``innov_corr`` (must be positive definite). The first row is drawn from the stationary
    covariance S_ij / (1 - phi_i phi_j); zero mean."""
    phis = np.clip(np.asarray(phis, float), -0.999, 0.999)
    sd_eta = np.sqrt(np.maximum(np.asarray(variances, float), 0.0) * (1.0 - phis ** 2))
    S = innov_corr * np.outer(sd_eta, sd_eta)
    stat = S / (1.0 - np.outer(phis, phis))
    C = len(phis)
    L_eta = np.linalg.cholesky(S) if np.all(sd_eta > 0) else _psd_factor(S)
    L_st = np.linalg.cholesky(stat) if np.all(sd_eta > 0) else _psd_factor(stat)
    e = np.empty((n, C))
    e[0] = L_st @ rng.standard_normal(C)
    innov = rng.standard_normal((n, C)) @ L_eta.T
    for t in range(1, n):
        e[t] = phis * e[t - 1] + innov[t]
    return e


def _psd_factor(S: np.ndarray) -> np.ndarray:
    w, V = np.linalg.eigh((S + S.T) / 2)
    return V * np.sqrt(np.maximum(w, 0.0))


def within_unit_correlation(series: list[np.ndarray], min_rows: int = 10) -> np.ndarray:
    """v2 X3 estimator: rho_bar_ij = sum_k sum_t e_ik e_jk / sum_k sqrt(sum_t e_ik^2 sum_t e_jk^2) over per-unit-centred
    residual arrays (rows with any non-finite entry dropped): the variance-weighted mean of per-unit correlations."""
    C = series[0].shape[1]
    num, den = np.zeros((C, C)), np.zeros((C, C))
    for E in series:
        E = E[np.all(np.isfinite(E), axis=1)]
        if len(E) < min_rows:
            continue
        E = E - E.mean(axis=0)
        cov = E.T @ E
        v = np.diag(cov)
        num += cov
        den += np.sqrt(np.outer(v, v))
    with np.errstate(invalid="ignore", divide="ignore"):
        r = num / den
    np.fill_diagonal(r, 1.0)
    return r
