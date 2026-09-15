"""Degradation state and EOL, paper Eq. 3 (own code: benchmark-specific definition, brief R2).

r2 definition (C3):  z_t = (q1 - q_t) / (q1 - rho * q_nom),   T = min{t : z_t >= 1}
    q_t  smoothed capacity (Savitzky-Golay, declared window/order/mode)
    q1   max of q_t over the first k positions (declared k)
    guard: a unit with q1 - rho * q_nom < margin * q_nom is excluded (declared margin)
r1 definition (paper as given, kept as a sensitivity point): z_t = (q1 - q_t) / ((1 - rho) q1), q1 = q_t at t=1.

Record-end rule (decision D13, measured records only): if the smoothed state never reaches 1 but the mean raw capacity of
the last 5 recorded positions lies within ``record_end_tau * q_nom`` of the threshold, the record ended at the dataset's
own stopping rule and ``T`` is its last position (``T_from_record_end = True``).

EOL search start (decision D15): T = min{t >= t1 : z_t >= 1}, t1 the position of q1.

Positions are 1-based in the paper; arrays here are 0-based, so ``T`` is returned 1-based (``T = idx + 1``)
and ``None`` when the threshold is never reached (a censored unit).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import savgol_filter


@dataclass(frozen=True)
class StateSpec:
    rho: float
    q_nom: float
    k: int
    margin: float
    sg_window: int
    sg_polyorder: int
    sg_mode: str = "interp"
    definition: str = "nominal_anchor_r2"  # or "first_position_anchor_r1"
    record_end_tau: float | None = None    # D13: measured records only; None for generated units


def spec_from_declarations(decl: dict, q_nom: float, rho: float | None = None, definition: str = "nominal_anchor_r2",
                           k: int | None = None, measured: bool = True) -> StateSpec:
    d = decl["declared_by_design"]
    rer = d["eol"].get("record_end_rule")
    return StateSpec(
        rho=float(d["eol"]["rho"]["value"] if rho is None else rho),
        q_nom=float(q_nom),
        k=int(d["eol"]["q1_reference"]["k"] if k is None else k),
        margin=0.05,  # declared_by_design.eol.denominator_guard (0.05 * q_nom)
        sg_window=int(d["smoothing"]["window_length"]["value"]),
        sg_polyorder=int(d["smoothing"]["polyorder"]["value"]),
        sg_mode=str(d["smoothing"]["mode"]["value"]),
        definition=definition,
        record_end_tau=float(rer["tau"]) if (measured and rer) else None,
    )


def smooth(q: np.ndarray, spec: StateSpec) -> np.ndarray:
    q = np.asarray(q, dtype=float)
    w = spec.sg_window
    if len(q) < w:  # too short to smooth with the declared window: odd window no longer than the series
        w = len(q) if len(q) % 2 == 1 else len(q) - 1
        if w <= spec.sg_polyorder:
            return q.copy()
    return savgol_filter(q, window_length=w, polyorder=spec.sg_polyorder, mode=spec.sg_mode)


@dataclass
class UnitState:
    q_smooth: np.ndarray
    q1: float
    q1_first: float
    denominator: float
    z: np.ndarray
    T: int | None          # 1-based EOL position, None if censored
    excluded_by_guard: bool
    T_from_record_end: bool = False
    t1: int = 1            # 1-based position of the early-life reference q1

    @property
    def reaches_eol(self) -> bool:
        return self.T is not None


def unit_state(q_raw: np.ndarray, spec: StateSpec) -> UnitState:
    qs = smooth(q_raw, spec)
    q1_first = float(qs[0])
    t1 = 0
    if spec.definition == "nominal_anchor_r2":
        t1 = int(np.argmax(qs[: max(1, spec.k)]))
        q1 = float(qs[t1])
        threshold = spec.rho * spec.q_nom
        denom = q1 - threshold
        guard = denom < spec.margin * spec.q_nom
    elif spec.definition == "first_position_anchor_r1":
        q1 = q1_first
        threshold = spec.rho * q1
        denom = (1.0 - spec.rho) * q1
        guard = denom <= 0
    else:
        raise ValueError(spec.definition)
    z = (q1 - qs) / denom if denom != 0 else np.full_like(qs, np.nan)
    T = None
    if not guard:
        # z >= 1 <=> q_t <= threshold (denominator > 0); the fall is measured from q1, so the search starts at its
        # position t1 (decision D15; identical to a search from t = 1 whenever no reading before t1 is below threshold)
        hit = np.flatnonzero(qs[t1:] <= threshold)
        T = int(hit[0]) + t1 + 1 if hit.size else None
    from_end = False
    if T is None and not guard and spec.record_end_tau is not None and len(qs) >= 5:
        if abs(float(np.mean(np.asarray(q_raw, float)[-5:])) - threshold) <= spec.record_end_tau * spec.q_nom:
            T, from_end = len(qs), True
    return UnitState(q_smooth=qs, q1=q1, q1_first=q1_first, denominator=float(denom), z=z, T=T, excluded_by_guard=bool(guard),
                     T_from_record_end=from_end, t1=t1 + 1)
