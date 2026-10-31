"""Loader for the DegradX benchmark bundle (NumPy only).

Each ``<PROFILE>/seed<g>.npz`` holds the generated units of one profile and generation seed as concatenated per-position
arrays: the degradation state ``z``, the mean component ``m``, the summed inserted patterns ``p`` (capacity channel only)
and the noise ``eps`` (for the two null channels, their whole value). The observation is ``x = m + eps`` plus ``p`` on the
capacity channel. ``windows`` rebuilds, for every window of ``L`` positions ending at ``t``, the input, the decomposable
target and its exact attribution ground truth:

    w_{u,c}    = pi_u * kappa_c                       pi: position profile (recency or uniform), kappa: channel weight
    graded     = w * (m - x0)                         dense field from the mean component
    sparse     = w * p                                inserted patterns (non-zero only where patterns lie)
    phi_star   = graded + sparse                      sums exactly to y over the window
    y          = sum(phi_star)                        regression target
    g(x)       = sum(w * (x - x0))                    reference model; g(x) - y = sum(w * eps)
    R          = T - t                                remaining useful life at the window end

Window positions run oldest first (row L - 1 is the window end). Example::

    from degradx_benchmark import load
    b = load("FORM", seed=0)                     # path of the bundle root defaults to this file's directory
    unit = b.units("test")[0]
    w = b.windows(unit, "recency")               # dict of arrays, one row per window
    w["x"].shape, w["phi_star"].shape            # (N, L, C), (N, L, C)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent


@dataclass
class Unit:
    index: int          # unit index within the generation seed
    source_unit: str    # measured fitting unit whose parameters it resampled
    split: str          # train / validation / test
    T: int              # length = end of life (first position with z >= 1)
    z: np.ndarray       # (T,)    degradation state, 0 pristine, 1 end of life
    m: np.ndarray       # (T, C)  mean component (null channels: 0)
    p: np.ndarray       # (T,)    summed inserted patterns on the capacity channel
    eps: np.ndarray     # (T, C)  noise (null channels: their whole value)
    patterns: list      # inserted patterns: type, start (1-based position), duration, amplitude

    @property
    def x(self) -> np.ndarray:
        x = self.m + self.eps
        x[:, 0] += self.p
        return x

    @property
    def x_pattern_free(self) -> np.ndarray:
        return self.m + self.eps


class Benchmark:
    def __init__(self, profile: str, seed: int, root: Path):
        self.root = Path(root)
        d = self.root / profile
        with np.load(d / f"seed{seed}.npz", allow_pickle=False) as npz:
            z = {k: npz[k] for k in npz.files}  # decompress once: every NpzFile access decompresses the whole array again
        meta = json.loads((self.root / "manifest.json").read_text())["profiles"][profile]
        self.profile, self.seed = profile, seed
        self.channels: list[str] = list(meta["channels"])
        self.weighted: list[str] = list(meta["weighted_channels"])
        self.kappa = np.asarray(meta["kappa"], float)
        self.x0 = np.asarray(meta["x0"], float)
        self.L = int(meta["L"])
        self.pi = {k: np.asarray(v, float) for k, v in meta["position_profiles"].items()}
        self.pattern_channel = int(meta["pattern_channel"])
        self._z = z
        self._patterns = json.loads((d / f"seed{seed}_patterns.json").read_text())
        self._offsets = z["offsets"]

    def __len__(self) -> int:
        return len(self._z["unit_index"])

    def unit(self, i: int) -> Unit:
        a, b = int(self._offsets[i]), int(self._offsets[i + 1])
        Z = self._z
        return Unit(int(Z["unit_index"][i]), str(Z["source_unit"][i]), str(Z["split"][i]), int(Z["T"][i]),
                    Z["z"][a:b], Z["m"][a:b], Z["p"][a:b], Z["eps"][a:b], self._patterns[i])

    def units(self, split: str | None = None) -> list[Unit]:
        return [self.unit(i) for i in range(len(self)) if split is None or str(self._z["split"][i]) == split]

    def weights(self, weighting: str) -> np.ndarray:
        """(L, C) window weights w = pi kappa."""
        return np.outer(self.pi[weighting], self.kappa)

    def windows(self, unit: Unit, weighting: str, ends=None) -> dict:
        """All full windows of a unit (or those ending at the 1-based positions ``ends``) under one position weighting."""
        L = self.L
        ends = np.arange(L, unit.T + 1) if ends is None else np.asarray(ends, int)
        idx = ends[:, None] - L + np.arange(L)[None, :]
        m, eps = unit.m[idx], unit.eps[idx]
        pch = np.zeros_like(m)
        pch[:, :, self.pattern_channel] = unit.p[idx]
        W = self.weights(weighting)[None]
        x = m + eps + pch
        graded, sparse = W * (m - self.x0), W * pch
        return {"t": ends, "x": x, "x_pattern_free": m + eps, "graded": graded, "sparse": sparse, "phi_star": graded + sparse,
                "y": graded.sum(axis=(1, 2)) + sparse.sum(axis=(1, 2)), "g": (W * (x - self.x0)).sum(axis=(1, 2)), "R": unit.T - ends, "z_end": unit.z[ends - 1]}

    def evaluation_windows(self) -> list[tuple[Unit, int]]:
        """The windows scored in the reported reference values (generation seed 0, test units): (unit, end position)."""
        if self.seed != 0:
            raise ValueError("the evaluation windows are drawn from generation seed 0")
        rows = np.loadtxt(self.root / self.profile / "evaluation_windows.csv", delimiter=",", skiprows=1, dtype=int, ndmin=2)
        by_index = {int(i): k for k, i in enumerate(self._z["unit_index"])}
        return [(self.unit(by_index[int(u)]), int(t)) for u, t in rows]


def load(profile: str, seed: int = 0, root: str | Path | None = None) -> Benchmark:
    return Benchmark(profile, seed, Path(root) if root is not None else ROOT)


def profiles(root: str | Path | None = None) -> list[str]:
    return list(json.loads((Path(root or ROOT) / "manifest.json").read_text())["profiles"])
