"""Inserted-pattern detection on trajectory-fit residuals (paper §3.3 step five). One implementation, used by
the S2 audit and by S3 fitting (brief S2).

Rule (declarations ``pattern_detection``): residual r_t = raw capacity - fitted trajectory; residual scale
s = 1.4826 * median(|r - median(r)|) per unit; a candidate pattern is a maximal run of consecutive positions
with r_t > k s (positive type) or r_t < -k s (negative type) of length >= m and <= the smoothing window (D16).
The trajectory is fitted over positions t1..T, from the early-life reference to EOL (D16). For each pattern: extremum
position (1-based), signed amplitude (the residual at the extremum, in the units of r), duration in positions.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def residual_scale(r: np.ndarray) -> float:
    r = np.asarray(r, float)
    r = r[np.isfinite(r)]
    return float(1.4826 * np.median(np.abs(r - np.median(r)))) if r.size else np.nan


@dataclass
class Pattern:
    sign: int            # +1 regeneration, -1 measurement-condition dip
    start: int           # 1-based first position of the run
    end: int             # 1-based last position of the run
    extremum: int        # 1-based position of the largest |r| in the run
    amplitude: float     # signed residual at the extremum
    duration: int        # end - start + 1

    def as_dict(self) -> dict:
        return {"sign": self.sign, "start": self.start, "end": self.end, "extremum": self.extremum,
                "amplitude": self.amplitude, "duration": self.duration}


def detect(r: np.ndarray, k: float, m: int, scale: float | None = None, max_duration: int | None = None) -> tuple[list[Pattern], float]:
    """Runs beyond k*s of length >= m; with ``max_duration`` (decision D16: the smoothing window), longer runs are
    part of the smoothed trajectory, and so of z_t, rather than inserted patterns, and are not returned."""
    r = np.asarray(r, float)
    s = residual_scale(r) if scale is None else scale
    out: list[Pattern] = []
    if not np.isfinite(s) or s <= 0:
        return out, s
    for sign in (+1, -1):
        hit = sign * r > k * s
        i, n = 0, len(r)
        while i < n:
            if not hit[i]:
                i += 1
                continue
            j = i
            while j + 1 < n and hit[j + 1]:
                j += 1
            if j - i + 1 >= m and (max_duration is None or j - i + 1 <= max_duration):
                seg = r[i : j + 1]
                e = i + int(np.argmax(sign * seg))
                out.append(Pattern(sign, i + 1, j + 1, e + 1, float(r[e]), j - i + 1))
            i = j + 1
    out.sort(key=lambda p: p.start)
    return out, s


def pattern_mask(n: int, patterns: list[Pattern]) -> np.ndarray:
    """Boolean mask of positions occupied by detected patterns (step four excludes them from noise)."""
    mask = np.zeros(n, bool)
    for p in patterns:
        mask[p.start - 1 : p.end] = True
    return mask
