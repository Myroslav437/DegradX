"""Per-unit property audit (paper §3.4; brief S2). Shares Eq. 3, family fitting and pattern detection with S3.

For one unit's per-cycle table this computes, on the data:
  * the capacity series after the declared glitch rule (``clean_capacity``),
  * smoothed capacity, robust and first-position q1, EOL attainment under both definitions over the rho grid,
  * monotonicity of the smoothed capacity within tolerance over positions 1..min(T, N),
  * the three candidate families fitted over positions t1..min(T, N) (D16), the per-unit best by in-sample RMSE,
    and pattern detection on that fit's residual at every (k, m) of the declared sweep.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from degradx.fitting.families import FAMILIES, fit_family
from degradx.fitting.patterns import detect
from degradx.generator.state import StateSpec, unit_state


@dataclass(frozen=True)
class CleaningRule:
    """Which stored cycles enter the capacity series. Chosen by decision D12 (docs/DECISIONS)."""
    name: str
    drop_degenerate: bool = True
    capacity_low_frac: float | None = None   # drop cycles with capacity < low * q_nom
    capacity_high_frac: float | None = None  # drop cycles with capacity > high * q_nom
    isolated_excursion_frac: float | None = None  # drop a single position deviating > frac * q_nom from the centred
                                                  # 11-position rolling median while neither neighbour does
    drop_recovered_collapse: bool = False    # drop readings < 0.5 * q_nom that precede a later reading >= 0.8 * q_nom


def clean_capacity(df: pd.DataFrame, column: str, rule: CleaningRule, q_nom: float) -> pd.DataFrame:
    keep = df[column].notna() & np.isfinite(df[column])
    if rule.drop_degenerate:
        keep &= ~df["degenerate"].astype(bool)
    if rule.capacity_low_frac is not None:
        keep &= df[column] >= rule.capacity_low_frac * q_nom
    if rule.capacity_high_frac is not None:
        keep &= df[column] <= rule.capacity_high_frac * q_nom
    if rule.drop_recovered_collapse:
        q = df[column].to_numpy(float)
        later_ok = np.flip(np.maximum.accumulate(np.flip(np.where(np.isfinite(q), q, -np.inf))))
        # a reading below half of nominal followed later in the record by one at >= 0.8 q_nom is a failed measurement
        later_after = np.append(later_ok[1:], -np.inf)
        keep &= ~((q < 0.5 * q_nom) & (later_after >= 0.8 * q_nom))
    if rule.isolated_excursion_frac is not None:
        q = df[column].where(keep).to_numpy(float)
        med = pd.Series(q).rolling(11, center=True, min_periods=3).median().to_numpy()
        big = np.abs(q - med) > rule.isolated_excursion_frac * q_nom
        prev_big = np.append(False, big[:-1])
        next_big = np.append(big[1:], False)
        keep &= ~(big & ~prev_big & ~next_big)
    out = df.loc[keep].copy()
    out["position_stored"] = out["position"]
    out["position"] = np.arange(1, len(out) + 1)  # positions are re-indexed over kept cycles
    return out


def monotone_violation(qs: np.ndarray) -> float:
    """max_t (q_t - min_{s<=t} q_s): the largest recovery above the running minimum."""
    return float(np.max(qs - np.minimum.accumulate(qs))) if len(qs) else np.nan


def audit_unit(df: pd.DataFrame, *, column: str, rule: CleaningRule, q_nom: float, decl: dict, rho_grid, k_grid,
               sweep_k, sweep_m, k_default: float, m_default: int, mono_tol: float, spec_base: StateSpec) -> dict:
    cid = df["cell_id"].iloc[0]
    d = clean_capacity(df, column, rule, q_nom)
    q = d[column].to_numpy(float)
    rec: dict = {"cell_id": cid, "n_stored": int(len(df)), "n_kept": int(len(d)), "n_dropped_by_cleaning": int(len(df) - len(d))}
    if len(d) < max(spec_base.sg_window, 20):
        rec["too_short"] = True
        return rec
    rec["too_short"] = False
    st = unit_state(q, spec_base)
    rec.update(q1=st.q1, q1_first=st.q1_first, q1_material_diff=bool(abs(st.q1 - st.q1_first) > 0.01 * q_nom),
               denominator=st.denominator, excluded_by_guard=st.excluded_by_guard, T=st.T)
    for kk in k_grid:
        s2 = unit_state(q, StateSpec(**{**spec_base.__dict__, "k": int(kk)}))
        rec[f"q1_k{kk}"] = s2.q1
    for rho in rho_grid:
        for definition in ("nominal_anchor_r2", "first_position_anchor_r1"):
            s = unit_state(q, StateSpec(**{**spec_base.__dict__, "rho": float(rho), "definition": definition}))
            tag = "r2" if definition == "nominal_anchor_r2" else "r1"
            rec[f"T_{tag}_rho{rho:.2f}"] = s.T
            rec[f"guard_{tag}_rho{rho:.2f}"] = s.excluded_by_guard
    rec["t1"] = st.t1
    rec["T_from_record_end"] = st.T_from_record_end
    end = st.T if st.T is not None else len(q)
    start = st.t1 - 1  # D16: the fall is fitted from the early-life reference
    qs = st.q_smooth[:end]
    rec["fit_start"], rec["fit_end"] = int(start + 1), int(end)
    rec["monotone_violation_Ah"] = monotone_violation(qs)
    rec["monotone_within_tol"] = bool(rec["monotone_violation_Ah"] <= mono_tol * st.q1)
    pos = d["position"].to_numpy(float)[start:end]
    y = q[start:end] / st.q1
    fits = {name: fit_family(name, pos, y) for name in FAMILIES}
    for name, f in fits.items():
        rec[f"rmse_{name}"] = f.rmse
    best = min(fits, key=lambda n: fits[n].rmse if np.isfinite(fits[n].rmse) else np.inf)
    rec["best_family_in_sample"] = best
    resid = (y - FAMILIES[best](fits[best].params, pos)) * st.q1  # back to Ah
    pats_by = {}
    for kk in sweep_k:
        for mm in sweep_m:
            pats, scale = detect(resid, kk, mm, max_duration=spec_base.sg_window)
            pats = [type(p)(p.sign, p.start + start, p.end + start, p.extremum + start, p.amplitude, p.duration) for p in pats]
            pats_by[(kk, mm)] = pats
            rec[f"n_pos_k{kk}_m{mm}"] = sum(p.sign > 0 for p in pats)
            rec[f"n_neg_k{kk}_m{mm}"] = sum(p.sign < 0 for p in pats)
    rec["residual_scale_Ah"] = scale
    rec["patterns"] = [dict(p.as_dict(), cell_id=cid) for p in pats_by[(k_default, m_default)]]
    rec["_trace"] = {"position": pos, "q_raw": q[start:end], "q_smooth": qs[start:], "fit": FAMILIES[best](fits[best].params, pos) * st.q1,
                     "residual": resid}
    return rec
