"""Profile fitting, paper §3.3 steps one to six, on the fitting split of one measured dataset.

Step 1  capacity series (D11/D12), Savitzky-Golay smoothing, Eq. 3 with D13/D15 -> z_t, T, t1 per unit
Step 2  all candidate families fitted per unit over t1..T; 5-fold contiguous CV-RMSE; family selected per dataset by
        median CV-RMSE over fitting units reaching EOL, with the D04 simplicity margin; theta = per-unit parameters of
        the selected family, resampled jointly with the unit's q1, T, noise and pattern rates (declarations
        theta_distribution)
Step 3  channel mappings phi_c: isotonic + PCHIP on pooled (z, x_c); capacity affine at the median q1 (C1 x C3);
        cross-channel covariance of residuals
Step 4  AR(1) noise per channel from residuals with detected-pattern positions masked
Step 5  pattern detection on the selected family's residual (k, m, max duration = smoothing window, D16)
Step 6  empirical distribution of T

Only quantities listed in paper l.238 as estimated from data are written under ``estimated_from_data`` (E1-E7).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from multiprocessing import get_context

import numpy as np
import pandas as pd

from degradx.data.audit import CleaningRule, clean_capacity
from degradx.fitting.families import FAMILIES, SIMPLICITY_ORDER, cv_rmse, fit_family
from degradx.fitting.noise_mappings import affine_capacity, ar1_from_residuals, fit_isotonic_pchip
from degradx.fitting.patterns import detect, pattern_mask
from degradx.generator.state import StateSpec, unit_state

CHANNEL_COLUMNS = {
    "capacity": "capacity_cycler_Ah",
    "charge_time": "charge_time_min",
    "mean_discharge_voltage": "mean_discharge_voltage_V",
    "internal_resistance": "internal_resistance_ohm",
    "temperature_mean": "temperature_mean_C",
}


@dataclass(frozen=True)
class ChannelRule:
    """Glitch rule for non-capacity channels (decision D17): a single-position departure beyond ``frac`` of the unit's
    channel median from the centred 11-position rolling median, with neither neighbour departing, is set to NaN.
    IR recorded as exactly 0 is missing. ``frac=None`` disables the excursion clause."""
    frac: float | None = None


def clean_channel(x: np.ndarray, rule: ChannelRule, name: str) -> np.ndarray:
    x = np.asarray(x, float).copy()
    if name == "internal_resistance":
        x[x == 0] = np.nan
    if rule.frac is None or not np.isfinite(x).any():
        return x
    med_unit = np.nanmedian(x)
    roll = pd.Series(x).rolling(11, center=True, min_periods=3).median().to_numpy()
    big = np.abs(x - roll) > rule.frac * abs(med_unit)
    big &= np.isfinite(x)
    prev_big = np.append(False, big[:-1])
    next_big = np.append(big[1:], False)
    x[big & ~prev_big & ~next_big] = np.nan
    return x


@dataclass
class Unit:
    cell_id: str
    positions: np.ndarray       # 1..n over kept cycles
    q: np.ndarray               # raw capacity [Ah]
    state: object               # UnitState
    channels: dict[str, np.ndarray]
    fit_start: int              # 1-based t1
    fit_end: int                # T or n
    fits: dict = field(default_factory=dict)
    cv: dict = field(default_factory=dict)

    @property
    def reaches(self) -> bool:
        return self.state.T is not None


def prepare_units(df: pd.DataFrame, cell_ids, q_nom: float, spec: StateSpec, rule: CleaningRule, channels, crule: ChannelRule) -> list[Unit]:
    out = []
    for cid in cell_ids:
        g = df[df["cell_id"] == cid]
        d = clean_capacity(g, CHANNEL_COLUMNS["capacity"], rule, q_nom)
        q = d[CHANNEL_COLUMNS["capacity"]].to_numpy(float)
        st = unit_state(q, spec)
        if st.excluded_by_guard:
            continue
        ch = {c: clean_channel(d[CHANNEL_COLUMNS[c]].to_numpy(float), crule, c) for c in channels if c != "capacity"}
        end = st.T if st.T is not None else len(q)
        out.append(Unit(cid, np.arange(1, len(q) + 1, dtype=float), q, st, ch, st.t1, end))
    return out


def _fit_one(args):
    u, do_cv = args
    sl = slice(u.fit_start - 1, u.fit_end)
    pos, y = u.positions[sl], u.q[sl] / u.state.q1
    fits = {n: fit_family(n, pos, y) for n in FAMILIES}
    cv = {n: (cv_rmse(n, pos, y) if do_cv else np.nan) for n in FAMILIES}
    return u.cell_id, fits, cv


def fit_families(units: list[Unit], workers: int) -> None:
    jobs = [(u, u.reaches) for u in units]
    with get_context("fork").Pool(workers) as pool:
        res = pool.map(_fit_one, jobs, chunksize=1)
    by = {cid: (f, c) for cid, f, c in res}
    for u in units:
        u.fits, u.cv = by[u.cell_id]


def select_family(units: list[Unit], margin: float, max_at_bound: float = 0.2) -> dict:
    """Lowest median CV-RMSE with the D04 simplicity margin, among families identified by the data: a family with a
    parameter at a bound in more than ``max_at_bound`` of the units is not eligible (D04); if none is, all are."""
    reach = [u for u in units if u.reaches]
    med = {n: float(np.nanmedian([u.cv[n] for u in reach])) if reach else np.nan for n in FAMILIES}
    in_sample = {n: float(np.nanmedian([u.fits[n].rmse for u in reach])) if reach else np.nan for n in FAMILIES}
    at_bound = {n: float(np.mean([len(u.fits[n].at_bound) > 0 for u in reach])) if reach else np.nan for n in FAMILIES}
    eligible = [n for n in FAMILIES if np.isfinite(med[n]) and at_bound[n] <= max_at_bound] or [n for n in FAMILIES if np.isfinite(med[n])]
    best_all = min(med, key=lambda n: med[n] if np.isfinite(med[n]) else np.inf)
    best = min(eligible, key=lambda n: med[n])
    within = [n for n in SIMPLICITY_ORDER if n in eligible and med[n] <= med[best] * (1 + margin)]
    chosen = within[0] if within else best
    return {"selected": chosen, "lowest_cv": best_all, "lowest_cv_eligible": best, "margin": margin, "margin_changed_choice": chosen != best,
            "identifiability_changed_choice": best != best_all, "max_frac_units_at_bound": max_at_bound, "frac_units_at_bound": at_bound,
            "eligible": eligible, "median_cv_rmse": med, "median_in_sample_rmse": in_sample, "units_in_selection": len(reach)}


def residual(u: Unit, family: str) -> np.ndarray:
    sl = slice(u.fit_start - 1, u.fit_end)
    return (u.q[sl] / u.state.q1 - FAMILIES[family](u.fits[family].params, u.positions[sl])) * u.state.q1


def fit_profile(df: pd.DataFrame, split: pd.DataFrame, *, dataset: str, q_nom: float, spec: StateSpec, rule: CleaningRule,
                channels: list[str], crule: ChannelRule, decl: dict, workers: int, k: float, m: int, sweep_k,
                base_seed: int = 20260915) -> tuple[dict, dict]:
    dd = decl["declared_by_design"]
    fit_ids = split.loc[split["split"] == "fitting", "cell_id"].tolist()
    units = prepare_units(df, fit_ids, q_nom, spec, rule, channels, crule)
    # ---- step 2
    fit_families(units, workers)
    sel = select_family(units, float(dd["trajectory_families"]["selection"]["simplicity_margin"]["value"]))
    fam = sel["selected"]
    W = spec.sg_window
    # ---- step 5 (needed before step 4: masks)
    unit_rows, pattern_rows, sweep_rows, masks, resid_cap = [], [], [], {}, {}
    for u in units:
        r = residual(u, fam)
        pats, s = detect(r, k, m, max_duration=W)
        off = u.fit_start - 1
        masks[u.cell_id] = pattern_mask(len(r), pats)
        resid_cap[u.cell_id] = r
        n_len = len(r)
        for p in pats:
            pattern_rows.append({"cell_id": u.cell_id, "type": "positive" if p.sign > 0 else "negative", "extremum": p.extremum + off,
                                 "amplitude_Ah": p.amplitude, "duration": p.duration, "z_at_extremum": float(u.state.z[p.extremum + off - 1])})
        for kk in sweep_k:
            pk, _ = detect(r, kk, m, max_duration=W)
            sweep_rows.append({"cell_id": u.cell_id, "k": kk, "positive": sum(p.sign > 0 for p in pk), "negative": sum(p.sign < 0 for p in pk),
                               "positive_amp_median_Ah": float(np.median([p.amplitude for p in pk if p.sign > 0])) if any(p.sign > 0 for p in pk) else np.nan,
                               "positions": n_len, "residual_scale_Ah": s})
        f = u.fits[fam]
        unit_rows.append({"cell_id": u.cell_id, "reaches_eol": u.reaches, "T": u.state.T, "t1": u.fit_start, "n_kept": len(u.q),
                          "q1": u.state.q1, "denominator": u.state.denominator, "T_from_record_end": u.state.T_from_record_end,
                          "family_params": f.params.tolist(), "family_at_bound": f.at_bound,
                          **{f"rmse_{n}": u.fits[n].rmse for n in FAMILIES}, **{f"cv_rmse_{n}": u.cv[n] for n in FAMILIES},
                          "residual_scale_Ah": s, "residual_mean_over_scale": float(np.mean(r) / s) if s > 0 else np.nan,
                          "n_positive": sum(p.sign > 0 for p in pats), "n_negative": sum(p.sign < 0 for p in pats), "fit_positions": n_len})
    units_df = pd.DataFrame(unit_rows)
    patterns_df = pd.DataFrame(pattern_rows)
    sweep_df = pd.DataFrame(sweep_rows)
    # ---- step 3: mappings
    z_all = np.concatenate([u.state.z[u.fit_start - 1:u.fit_end] for u in units])
    mappings = {"capacity": affine_capacity(float(np.median([u.state.q1 for u in units])), spec.rho, q_nom)}
    for c in channels:
        if c == "capacity":
            continue
        x_all = np.concatenate([u.channels[c][u.fit_start - 1:u.fit_end] for u in units])
        mappings[c] = fit_isotonic_pchip(c, z_all, x_all)
    # capacity affinity check per unit (Eq. 3 makes smoothed capacity affine in z with the unit's own q1)
    affinity_err = max(float(np.max(np.abs(u.state.q_smooth - (u.state.q1 - u.state.z * u.state.denominator)))) for u in units)
    # ---- step 4: noise with masked pattern positions; channel residuals x_c - phi_c(z)
    noise, resid_ch = {}, {"capacity": resid_cap}
    per_unit_noise = {u.cell_id: {} for u in units}
    for c in channels:
        if c != "capacity":
            resid_ch[c] = {u.cell_id: u.channels[c][u.fit_start - 1:u.fit_end] - mappings[c](u.state.z[u.fit_start - 1:u.fit_end]) for u in units}
        ids = [u.cell_id for u in units]
        noise[c] = ar1_from_residuals([resid_ch[c][i] for i in ids], [masks[i] for i in ids]).as_dict()
        for i in ids:
            per_unit_noise[i][c] = ar1_from_residuals([resid_ch[c][i]], [masks[i]]).as_dict()
    units_df["noise"] = units_df["cell_id"].map(per_unit_noise)
    # ---- cross-channel covariance of residuals (masked), pooled over positions of fitting units
    stack = []
    for u in units:
        cols = [np.where(masks[u.cell_id], np.nan, resid_ch[c][u.cell_id]) for c in channels]
        stack.append(np.column_stack(cols))
    R = np.vstack(stack)
    R = R[np.all(np.isfinite(R), axis=1)]
    cov = np.cov(R, rowvar=False) if len(R) > 2 else np.full((len(channels), len(channels)), np.nan)
    corr = np.corrcoef(R, rowvar=False) if len(R) > 2 else cov
    # ---- channel-role guard (declarations target.weights.guard)
    weighted = [c for c in dd["channels"]["roles"]["weighted_pattern_carrying"] + dd["channels"]["roles"]["weighted_graded"] if c in channels]
    demoted = [c for c in weighted if abs(mappings[c].delta) < np.sqrt(noise[c]["variance"])]
    # ---- step 6: lengths
    lengths = [int(u.state.T) for u in units if u.reaches]
    # ---- D05 enable rule: measured rate vs the rate on the profile's own fitted capacity noise
    from degradx.fitting.noise_mappings import ar1_sample
    from degradx.utils.seeding import rng as _rng

    er = dd["pattern_detection"]["enable_rule"]
    factor = float(er.get("noise_factor", 0.0))
    seg = int(np.median(units_df["fit_positions"])) if len(units_df) else 0
    g = _rng(base_seed, "generation", "D05", dataset)
    n_noise = {"positive": 0, "negative": 0}
    for _ in range(200):
        e = ar1_sample(g, seg, noise["capacity"]["variance"], noise["capacity"]["phi"])
        pn, _s = detect(e, k, m, max_duration=W)
        n_noise["positive"] += sum(p.sign > 0 for p in pn)
        n_noise["negative"] += sum(p.sign < 0 for p in pn)
    total_pos = float(units_df["fit_positions"].sum())
    pattern_types = {}
    for t in ("positive", "negative"):
        p = patterns_df[patterns_df["type"] == t] if len(patterns_df) else pd.DataFrame(columns=["amplitude_Ah", "duration", "cell_id"])
        measured_rate = len(p) / total_pos * 100 if total_pos else 0.0
        noise_rate = n_noise[t] / (200 * seg) * 100 if seg else np.nan
        pattern_types[t] = {"enabled": bool(len(p) > 0 and measured_rate >= factor * noise_rate), "events": int(len(p)),
                            "measured_rate_per_100": measured_rate, "noise_only_rate_per_100": noise_rate,
                            "ratio_to_noise": measured_rate / noise_rate if noise_rate > 0 else None, "noise_factor": factor,
                            "noise_segment_length": seg, "units_with_event": int(p["cell_id"].nunique()) if len(p) else 0,
                            "amplitude_Ah": p["amplitude_Ah"].tolist(), "duration": p["duration"].astype(int).tolist(),
                            "rate_per_position_by_unit": {u: float(units_df.set_index("cell_id").at[u, f"n_{t}"] / units_df.set_index("cell_id").at[u, "fit_positions"]) for u in units_df["cell_id"]}}
    profile = {
        "dataset": dataset,
        "declared_used": {"q_nom_Ah": q_nom, "rho": spec.rho, "k_q1": spec.k, "sg_window": spec.sg_window, "sg_polyorder": spec.sg_polyorder,
                          "detection_k": k, "detection_m": m, "detection_max_duration": W, "channels": channels,
                          "cleaning_rule": rule.__dict__, "channel_rule": crule.__dict__},
        "units": {"fitting": fit_ids, "fitting_passing_guard": [u.cell_id for u in units], "fitting_reaching_eol": [u.cell_id for u in units if u.reaches]},
        "estimated_from_data": {
            "E1_theta_distribution": {"family": fam, "param_names": list(FAMILIES[fam].params), "n_units": int(sum(u.reaches for u in units)),
                                      "per_unit": units_df.loc[units_df["reaches_eol"], ["cell_id", "family_params", "q1", "T", "t1", "n_positive", "n_negative", "fit_positions", "noise"]].to_dict(orient="records")},
            "E2_family_choice": sel,
            "E3_channel_mappings": {c: {**mp.as_dict(), "phi0": float(mp(0.0)), "phi1": float(mp(1.0)), "delta": mp.delta} for c, mp in mappings.items()},
            "E4_channel_covariance": {"channels": channels, "covariance": cov.tolist(), "correlation": corr.tolist(), "n_positions": int(len(R))},
            "E5_noise": noise,
            "E6_patterns": pattern_types,
            "E7_length_distribution": lengths,
        },
        "derived": {"channel_roles": {"weighted": [c for c in weighted if c not in demoted], "demoted_by_guard": demoted,
                                      "zero_weight_redundant": [c for c in channels if c not in weighted] + demoted},
                    "reference_point_x0": {c: float(mp(0.0)) for c, mp in mappings.items()},
                    "null_permuted_source_values": {"channel": "charge_time", "n": int(np.isfinite(np.concatenate([u.channels["charge_time"] for u in units])).sum()),
                                                    "median": float(np.nanmedian(np.concatenate([u.channels["charge_time"] for u in units])))},
                    "capacity_affinity_max_abs_error_Ah": affinity_err},
    }
    diag = {"units": units_df, "patterns": patterns_df, "sweep": sweep_df, "unit_objects": units, "residuals": resid_ch, "masks": masks,
            "mappings": mappings, "z_all": z_all}
    return profile, diag
