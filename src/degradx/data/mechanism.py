"""Mechanism diagnostic of inserted-pattern candidates: do positive capacity-residual runs start within a window after a
rest event more often than random positions do? Used by the FORM audit (``scripts/s04_audit_form.py``).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def rest_positions(dclean: pd.DataFrame, draw: pd.DataFrame) -> np.ndarray:
    """1-based positions (after D12 re-indexing) of rest events: a rest-event cycle dropped by cleaning moves to the next kept
    cycle before the following rest event."""
    ev = draw.loc[draw["rest_event"].astype(bool), "cycle_number"].to_numpy()
    kept = dclean["cycle_number"].to_numpy()
    pos = []
    for k, c in enumerate(ev):
        nxt = ev[k + 1] if k + 1 < len(ev) else np.inf
        j = np.flatnonzero((kept >= c) & (kept < nxt))
        if len(j):
            pos.append(int(dclean["position"].iloc[j[0]]))
    return np.array(pos, int)


def window_fraction(starts, rests, lo, hi, positions) -> tuple[float, float, int, int]:
    """Share of run starts s with lo <= s - r <= hi for some rest event r, and the same share over the given positions."""
    def hit(s):
        return bool(len(rests)) and bool(np.any((s - rests >= lo) & (s - rests <= hi)))
    a = sum(hit(s) for s in starts)
    b = sum(hit(s) for s in positions)
    return (a / len(starts) if len(starts) else np.nan), (b / len(positions) if len(positions) else np.nan), int(a), int(len(starts))


def mechanism(units_runs: list[dict], seed: int, n_boot: int, lo=0, hi=10) -> dict:
    """Pooled observed share / expected share, with a unit bootstrap of the ratio (percentile)."""
    def ratio(sel):
        hits = sum(u[f"hits_{lo}_{hi}"] for u in sel)
        runs = sum(u["runs"] for u in sel)
        exp_num = sum(u[f"exp_hits_{lo}_{hi}"] for u in sel)
        exp_den = sum(u["positions"] for u in sel)
        if runs == 0 or exp_den == 0 or exp_num == 0:
            return np.nan
        return (hits / runs) / (exp_num / exp_den)
    point = ratio(units_runs)
    g = np.random.default_rng(seed)
    bs = [ratio([units_runs[i] for i in g.integers(0, len(units_runs), len(units_runs))]) for _ in range(n_boot)]
    bs = np.array([b for b in bs if np.isfinite(b)])
    lo_ci, hi_ci = (np.quantile(bs, [0.025, 0.975]) if len(bs) > 10 else (np.nan, np.nan))
    return {"ratio": float(point), "ci_low": float(lo_ci), "ci_high": float(hi_ci), "runs": int(sum(u["runs"] for u in units_runs)),
            "hits": int(sum(u[f"hits_{lo}_{hi}"] for u in units_runs)), "units": len(units_runs)}
