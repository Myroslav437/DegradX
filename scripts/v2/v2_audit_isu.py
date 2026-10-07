"""V2 audit of the ISU-ILCC cycle table under D28 (imported by v2_third_dataset.py --audit).

S2-style audit, eligibility re-check (E3, E4, E5 under the declared rules) and the declared X6(ii) diagnostics
(declarations r3 v2.third_profile.candidate_rules, .mechanism_diagnostic; readings.X6_ii_superseded_D28).
"""

from __future__ import annotations

import json
from functools import partial
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from scipy.stats import bootstrap

import _common as C
from degradx import DATA_V2
from degradx.data.audit import CleaningRule, audit_unit, clean_capacity
from degradx.data.splits import measured_split
from degradx.fitting.families import FAMILIES
from degradx.fitting.noise_mappings import ar1_from_residuals, ar1_sample
from degradx.fitting.patterns import detect
from degradx.fitting.profile import fit_profile, prepare_units, residual
from degradx.generator.state import spec_from_declarations, unit_state
from degradx.utils.io import save_table, write_json
from degradx.utils.seeding import rng

DS = "ISU_ILCC"
TABLE = DATA_V2 / "processed" / "cycle_tables" / f"{DS}.csv.gz"


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


def unit_runs(u, fam, rests, k, m, W):
    r = residual(u, fam)
    pats, _s = detect(r, k, m, max_duration=W)
    off = u.fit_start - 1
    pos_starts = np.array([p.start + off + 1 for p in pats if p.sign > 0], int)
    neg_starts = np.array([p.start + off + 1 for p in pats if p.sign < 0], int)
    fit_pos = np.arange(u.fit_start, u.fit_end + 1)
    rr = rests[(rests >= u.fit_start) & (rests <= u.fit_end)]
    rec = {"cell_id": u.cell_id, "runs": int(len(pos_starts)), "neg_runs": int(len(neg_starts)), "positions": int(len(fit_pos)), "rests": int(len(rr))}
    for lo, hi in ((0, 10), (-11, -1)):
        _, _, a, _ = window_fraction(pos_starts, rr, lo, hi, fit_pos)
        rec[f"hits_{lo}_{hi}"] = a
        rec[f"exp_hits_{lo}_{hi}"] = int(sum(bool(np.any((s - rr >= lo) & (s - rr <= hi))) for s in fit_pos)) if len(rr) else 0
        _, _, an, _ = window_fraction(neg_starts, rr, lo, hi, fit_pos)
        rec[f"neg_hits_{lo}_{hi}"] = an
    return rec


def audit(ctx, dd, decl, out, ct) -> dict:
    C.register_profile(DS, "isu_ilcc")
    q_nom = C.q_nom_of(DS)
    spec = spec_from_declarations(decl, q_nom)
    cr = dd["v2"]["third_profile"]["candidate_rules"]
    rule = CleaningRule("D12", **dd["capacity_series"]["cleaning_rule"]["params"])
    crule = C.channel_rule_v2(dd)
    k = float(dd["pattern_detection"]["multiple_k"]["value"])
    m = int(dd["pattern_detection"]["min_run_length"]["value"])
    W = int(dd["smoothing"]["window_length"]["value"])
    n_boot = int(dd["v2"]["statistics"]["bootstrap_n_resamples"])
    seed = ctx.args.seed
    df = pd.read_csv(TABLE, low_memory=False)
    ingest = json.loads((out / "tables" / "ingest.json").read_text())
    by_cell = {c["cell_id"]: c for c in ingest["cells"]}
    summary = {}
    # ---- S2-style per-unit audit
    fn = partial(audit_unit, column="capacity_cycler_Ah", rule=rule, q_nom=q_nom, decl=decl, rho_grid=dd["eol"]["rho_sensitivity_grid"]["value"],
                 k_grid=dd["eol"]["q1_reference"]["sensitivity_k"], sweep_k=dd["pattern_detection"]["sweep"]["multiple_k"],
                 sweep_m=dd["pattern_detection"]["sweep"]["min_run_length"], k_default=k, m_default=m,
                 mono_tol=float(dd["audit"]["monotonicity_tolerance"]["value"]), spec_base=spec)
    groups = [g for _, g in df.groupby("cell_id", sort=True)]
    with ProcessPoolExecutor(max_workers=ctx.args.workers) as ex:
        recs = list(ex.map(fn, groups, chunksize=2))
    for r in recs:
        r.pop("_trace", None)
        r.pop("patterns", None)
    units = pd.DataFrame(recs)
    units["stratum"] = units["cell_id"].map(lambda c: by_cell[c]["meta"]["stratum"])
    units["group"] = units["cell_id"].map(lambda c: by_cell[c]["meta"]["group"])
    save_table(units, out / "tables" / "audit_units")
    passing = units[~units["too_short"].astype(bool) & ~units["excluded_by_guard"].astype(bool)]
    reach = passing[passing["T"].notna()]
    # ---- eligibility re-check
    excl = [c for c in ingest["cells"] if c["meta"]["in_scope"] and c["excluded"]]
    excl_eol = []
    for c in excl:  # fewer than 2 anchors: C/5 EOL status and aging-cycle count (counts against E4 if at EOL with T < 44)
        c5 = np.array(c["c5"], float)
        excl_eol.append({"cell_id": c["cell_id"], "c5_reaches_200mAh": bool(np.any(c5[np.isfinite(c5)] < 0.2)), "cycles": c["checks"].get("cycles")})
    e3 = int(len(reach))
    short = reach[reach["T"] < 44]
    e4_fail = list(short["cell_id"]) + [e["cell_id"] for e in excl_eol if e["c5_reaches_200mAh"]]
    avail = {}
    nd = df[~df["degenerate"].astype(bool)]
    for ch in ("charge_time_min", "mean_discharge_voltage_V"):
        per = nd[ch].notna().groupby(nd["cell_id"]).mean() >= 0.5
        avail[ch] = {"units_with_channel": int(per.sum()), "units": int(per.size), "every_unit": bool(per.all())}
    elig_df = pd.DataFrame([{"cell_id": r.cell_id, "reaches_eol": bool(pd.notna(r.T))} for r in passing.itertuples()])
    split = measured_split(elig_df, seed, DS, float(dd["statistics"]["splits"]["measured"]["fitting"]))
    save_table(split, out / "tables" / f"split_{DS}")
    channels = ["capacity", "charge_time", "mean_discharge_voltage"]
    prof, diag = fit_profile(df, split, dataset=DS, q_nom=q_nom, spec=spec, rule=rule, channels=channels, crule=crule, decl=decl, workers=ctx.args.workers,
                             k=k, m=m, sweep_k=dd["pattern_detection"]["sweep"]["multiple_k"], base_seed=seed, offsets=C.offsets_params(dd))
    weighted = prof["derived"]["channel_roles"]["weighted"]
    e5 = bool(avail["charge_time_min"]["every_unit"] and avail["mean_discharge_voltage_V"]["every_unit"] and "charge_time" in weighted and "mean_discharge_voltage" in weighted)
    held_reach = int(((split["split"] == "held_out") & split["reaches_eol"]).sum())
    summary["eligibility"] = {
        "E3": {"units_reaching_eol_after_guard": e3, "required": 67, "passes": e3 >= 67, "held_out_reaching_eol": held_reach},
        "E4": {"units_reaching_eol_with_T_below_44": e4_fail, "min_T": float(reach["T"].min()) if len(reach) else None, "passes": not e4_fail},
        "E5": {"availability": avail, "weighted_after_guard": weighted, "demoted": prof["derived"]["channel_roles"]["demoted_by_guard"],
               "mappings_range": {c: prof["estimated_from_data"]["E3_channel_mappings"][c]["delta"] for c in channels},
               "noise_sd": {c: float(np.sqrt(prof["estimated_from_data"]["E5_noise"][c]["variance"])) for c in channels}, "passes": e5},
        "excluded_fewer_than_2_anchors": excl_eol,
        "units": {"in_table": int(units["cell_id"].nunique()), "too_short": int(units["too_short"].sum()), "guard_excluded": int(units["excluded_by_guard"].fillna(False).sum()),
                  "passing_guard": int(len(passing)), "reaching_eol": e3, "T_from_record_end": int(reach["T_from_record_end"].sum())},
        "T_distribution": C.summarise(reach["T"]),
    }
    eligible = summary["eligibility"]["E3"]["passes"] and summary["eligibility"]["E4"]["passes"] and e5
    summary["eligible"] = bool(eligible)
    ct.require("ISU-ILCC E3: >= 67 units reach EOL after the guard", summary["eligibility"]["E3"]["passes"], ">= 67", e3)
    ct.require("ISU-ILCC E4: every unit reaching EOL has T >= 44", summary["eligibility"]["E4"]["passes"], "all", ", ".join(map(str, e4_fail)) or "all")
    ct.require("ISU-ILCC E5: charge time and mean discharge V available in every unit and pass the weight guard", e5, "both", json.dumps(weighted))
    # ---- D05 pooled and per stratum (fitting split)
    e6 = prof["estimated_from_data"]["E6_patterns"]
    summary["d05"] = {"pooled": {t: {kk: v[kk] for kk in ("enabled", "events", "measured_rate_per_100", "noise_only_rate_per_100", "ratio_to_noise")} for t, v in e6.items()}}
    strata = {}
    for st in ("S_full", "S_partial"):
        ids = set(units.loc[units["stratum"] == st, "cell_id"])
        sp = split[split["cell_id"].isin(ids)]
        if (sp["split"] == "fitting").sum() < 3:
            continue
        p_s, d_s = fit_profile(df, sp, dataset=f"{DS}_{st}", q_nom=q_nom, spec=spec, rule=rule, channels=channels, crule=crule, decl=decl, workers=ctx.args.workers,
                               k=k, m=m, sweep_k=[k], base_seed=seed, offsets=C.offsets_params(dd))
        strata[st] = {"d05": {t: {kk: v[kk] for kk in ("enabled", "events", "measured_rate_per_100", "noise_only_rate_per_100", "ratio_to_noise")}
                              for t, v in p_s["estimated_from_data"]["E6_patterns"].items()},
                      "capacity_noise": p_s["estimated_from_data"]["E5_noise"]["capacity"], "family": p_s["estimated_from_data"]["E2_family_choice"]["selected"],
                      "fitting_units": int((sp["split"] == "fitting").sum())}
    summary["d05"]["strata"] = strata
    # ---- mechanism diagnostic (fitting split, selected family residual), placebo window, strata
    fam = prof["estimated_from_data"]["E2_family_choice"]["selected"]
    fit_units = diag["unit_objects"]
    runs = []
    for u in fit_units:
        g_raw = df[df["cell_id"] == u.cell_id]
        g_cl = clean_capacity(g_raw, "capacity_cycler_Ah", rule, q_nom)
        rests = rest_positions(g_cl, g_raw)
        rec_u = unit_runs(u, fam, rests, k, m, W)
        rec_u["stratum"] = by_cell[u.cell_id]["meta"]["stratum"]
        runs.append(rec_u)
    save_table(pd.DataFrame(runs), out / "tables" / "mechanism_units")
    mech = {"pooled": {"post_0_10": mechanism(runs, seed, n_boot), "placebo_-11_-1": mechanism(runs, seed, n_boot, -11, -1)}}
    for st in ("S_full", "S_partial"):
        sel = [r for r in runs if r["stratum"] == st]
        if sel:
            mech[st] = {"post_0_10": mechanism(sel, seed, n_boot), "placebo_-11_-1": mechanism(sel, seed, n_boot, -11, -1)}
    summary["mechanism_diagnostic"] = mech
    # ---- recovery index and overshoot (raw aging capacity around block-start rest events)
    rows = []
    for c in ingest["cells"]:
        if not c["meta"]["in_scope"] or c["excluded"]:
            continue
        t = df[df["cell_id"] == c["cell_id"]]
        ok = ~t["degenerate"].astype(bool).to_numpy()
        raw, cal = t["capacity_aging_raw_Ah"].to_numpy(float), t["capacity_cycler_Ah"].to_numpy(float)
        cst = t["charge_start_unix_s"].to_numpy(float)
        rs = np.flatnonzero(t["rest_event"].astype(bool).to_numpy() & (t["rest_event_source"].astype(str).to_numpy() == "block_start"))
        c5 = np.array(c["c5"], float)
        rstart = np.array(c["rpt_start"], float)
        for r in rs:
            before = np.flatnonzero(ok[:r])[-5:]
            after = r + np.flatnonzero(ok[r:])[:5]
            if len(before) < 5 or len(after) < 5:
                continue
            prev_rpt = np.flatnonzero(np.isfinite(rstart) & (rstart <= cst[r]))
            c5_prev = float(c5[prev_rpt[-1]]) if len(prev_rpt) and np.isfinite(c5[prev_rpt[-1]]) else np.nan
            rows.append({"cell_id": c["cell_id"], "stratum": c["meta"]["stratum"], "inv_dod": 1.0 / c["meta"]["mean_dod"], "c_dis": c["meta"]["c_dis"],
                         "recovery_index": float(np.log(np.median(raw[after]) / np.median(raw[before]))),
                         "overshoot_Ah": float(np.median(cal[after]) - c5_prev) if np.isfinite(c5_prev) else np.nan})
    rec_df = pd.DataFrame(rows)
    save_table(rec_df, out / "tables" / "recovery_index")
    reg = {}
    if len(rec_df) > 10:
        X = np.column_stack([np.ones(len(rec_df)), rec_df["inv_dod"], rec_df["c_dis"]])
        y = rec_df["recovery_index"].to_numpy()
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        # cluster (unit) bootstrap of the coefficients
        cells = rec_df["cell_id"].unique()
        g = np.random.default_rng(seed)
        bs = []
        idx_by = {c: np.flatnonzero(rec_df["cell_id"].to_numpy() == c) for c in cells}
        for _ in range(min(n_boot, 2000)):
            ii = np.concatenate([idx_by[c] for c in g.choice(cells, len(cells), replace=True)])
            b_, *_ = np.linalg.lstsq(X[ii], y[ii], rcond=None)
            bs.append(b_)
        bs = np.array(bs)
        reg = {"coef": dict(zip(["intercept", "inv_dod", "c_dis"], beta.tolist())), "ci_low": dict(zip(["intercept", "inv_dod", "c_dis"], np.quantile(bs, 0.025, axis=0).tolist())),
               "ci_high": dict(zip(["intercept", "inv_dod", "c_dis"], np.quantile(bs, 0.975, axis=0).tolist())), "events": int(len(rec_df)), "units": int(len(cells)),
               "resamples": int(len(bs)), "note": "unit (cluster) bootstrap, percentile; 2000 resamples (descriptive regression, not a declared interval)"}
    summary["recovery_index"] = {"regression": reg, "median_by_stratum": rec_df.groupby("stratum")["recovery_index"].median().to_dict() if len(rec_df) else {},
                                 "overshoot_median_by_stratum_Ah": rec_df.groupby("stratum")["overshoot_Ah"].median().to_dict() if len(rec_df) else {}}
    # ---- operator-null check
    ref_rate = e6["positive"]["noise_only_rate_per_100"]
    null_rows = []
    for u in fit_units:
        t = df[df["cell_id"] == u.cell_id]
        keep = ~t["degenerate"].astype(bool).to_numpy()
        raw = t["capacity_aging_raw_Ah"].to_numpy(float)[keep]
        f = t["calibration_factor"].to_numpy(float)[keep]
        if len(raw) < 30:
            continue
        sm = savgol_filter(raw, 11, 2, mode="interp")
        a = ar1_from_residuals([raw - sm])
        g = rng(seed, "generation", "D28-null", u.cell_id)
        synth = (sm + ar1_sample(g, len(raw), a.variance, a.phi)) * f
        st = unit_state(synth, spec)
        if st.excluded_by_guard:
            continue
        end = st.T if st.T is not None else len(synth)
        pos = np.arange(1, len(synth) + 1, dtype=float)[st.t1 - 1:end]
        y = synth[st.t1 - 1:end] / st.q1
        from degradx.fitting.families import fit_family

        fit = fit_family(fam, pos, y)
        r = (y - FAMILIES[fam](fit.params, pos)) * st.q1
        pats, _ = detect(r, k, m, max_duration=W)
        tt = t[keep].reset_index(drop=True)
        rests = np.flatnonzero(tt["rest_event"].astype(bool).to_numpy()) + 1
        starts = np.array([p.start + st.t1 for p in pats if p.sign > 0], int)
        fit_pos = np.arange(st.t1, end + 1)
        rr = rests[(rests >= st.t1) & (rests <= end)]
        hits = sum(bool(np.any((s - rr >= 0) & (s - rr <= 10))) for s in starts) if len(rr) else 0
        exp_hits = sum(bool(np.any((s - rr >= 0) & (s - rr <= 10))) for s in fit_pos) if len(rr) else 0
        null_rows.append({"cell_id": u.cell_id, "positions": len(r), "positive_runs": int(len(starts)), "runs": int(len(starts)), f"hits_0_10": int(hits),
                          f"exp_hits_0_10": int(exp_hits)})
    nd_ = pd.DataFrame(null_rows)
    null_rate = float(nd_["positive_runs"].sum() / nd_["positions"].sum() * 100) if len(nd_) else np.nan
    summary["operator_null"] = {"positive_rate_per_100": null_rate, "d05_reference_rate_per_100": ref_rate, "ratio_to_reference": null_rate / ref_rate if ref_rate else None,
                                "noise_factor": float(dd["pattern_detection"]["enable_rule"]["noise_factor"]),
                                "reaches_enable_level": bool(ref_rate and null_rate >= float(dd["pattern_detection"]["enable_rule"]["noise_factor"]) * ref_rate),
                                "null_mechanism_ratio": mechanism(null_rows, seed, n_boot) if len(null_rows) else None, "units": int(len(nd_))}
    # ---- additive sensitivity (capacity noise, patterns, D05)
    df_add = df.copy()
    df_add["capacity_cycler_Ah"] = df_add["capacity_additive_Ah"]
    p_add, _ = fit_profile(df_add, split, dataset=f"{DS}_additive", q_nom=q_nom, spec=spec, rule=rule, channels=["capacity"], crule=crule, decl=decl,
                           workers=ctx.args.workers, k=k, m=m, sweep_k=[k], base_seed=seed)
    e6a = p_add["estimated_from_data"]["E6_patterns"]
    summary["additive_sensitivity"] = {"capacity_noise": p_add["estimated_from_data"]["E5_noise"]["capacity"],
                                       "d05": {t: {kk: v[kk] for kk in ("enabled", "events", "measured_rate_per_100", "noise_only_rate_per_100", "ratio_to_noise")} for t, v in e6a.items()},
                                       "positive_amplitude_median_mAh": float(np.median(e6a["positive"]["amplitude_Ah"]) * 1000) if e6a["positive"]["amplitude_Ah"] else None,
                                       "d05_outcome_differs_from_primary": bool(e6a["positive"]["enabled"] != e6["positive"]["enabled"])}
    summary["primary_patterns"] = {"positive_amplitude_median_mAh": float(np.median(e6["positive"]["amplitude_Ah"]) * 1000) if e6["positive"]["amplitude_Ah"] else None,
                                   "capacity_noise": prof["estimated_from_data"]["E5_noise"]["capacity"]}
    # ---- X6(ii) reading (declared)
    s_full_enabled = bool(strata.get("S_full", {}).get("d05", {}).get("positive", {}).get("enabled", False))
    present = bool(e6["positive"]["enabled"] and s_full_enabled and not summary["operator_null"]["reaches_enable_level"])
    summary["x6_ii_reading"] = {"pooled_enabled": bool(e6["positive"]["enabled"]), "s_full_enabled": s_full_enabled,
                                "operator_null_reaches_enable": summary["operator_null"]["reaches_enable_level"], "present_at_scale": present,
                                "wording": "regeneration present at scale" if present else "not shown; post-RPT recovery of partial-window discharge capacity, not separable from voltage-cutoff kinetics"}
    # ---- cross-checks: q1 vs week-0 C/5; EOL interval agreement; f statistics
    xr = []
    for r in passing.itertuples():
        c = by_cell[r.cell_id]
        c5 = np.array(c["c5"], float)
        t = df[df["cell_id"] == r.cell_id]
        d_cl = clean_capacity(t, "capacity_cycler_Ah", rule, q_nom)
        t_nw0 = t.assign(capacity_cycler_Ah=t["capacity_aging_raw_Ah"] * t["calibration_factor_no_week0"])
        q1_nw0 = unit_state(clean_capacity(t_nw0, "capacity_cycler_Ah", rule, q_nom)["capacity_cycler_Ah"].to_numpy(float), spec).q1 if t["calibration_factor_no_week0"].notna().all() else np.nan
        row = {"cell_id": r.cell_id, "q1": r.q1, "c5_week0": float(c5[0]) if len(c5) else np.nan, "q1_minus_c5_0_over_qnom": (r.q1 - c5[0]) / q_nom if len(c5) else np.nan,
               "q1_no_week0_minus_c5_0_over_qnom": (q1_nw0 - c5[0]) / q_nom if len(c5) else np.nan}
        if pd.notna(r.T):
            cyc_T = int(d_cl["cycle_number"].iloc[int(r.T) - 1])
            tT = float(t.loc[t["cycle_number"] == cyc_T, "charge_start_unix_s"].iloc[0])
            rst = np.array(c["rpt_start"], float)
            below = np.flatnonzero(np.isfinite(c5) & (c5 < 0.2))
            if len(below):
                w = below[0]
                lo_t = rst[w - 2] if w >= 2 and np.isfinite(rst[w - 2]) else -np.inf
                row.update({"T_time": tT, "c5_first_below_rpt": int(w), "eol_in_interval": bool(lo_t <= tT <= rst[w]) if np.isfinite(rst[w]) else None})
        xr.append(row)
    xr = pd.DataFrame(xr)
    save_table(xr, out / "tables" / "cross_checks")
    summary["cross_checks"] = {"q1_vs_c5_week0_over_0.01": int((xr["q1_minus_c5_0_over_qnom"].abs() > 0.01).sum()),
                               "q1_no_week0_vs_c5_week0_over_0.01": int((xr["q1_no_week0_minus_c5_0_over_qnom"].abs() > 0.01).sum()),
                               "q1_minus_c5_0_median": float(xr["q1_minus_c5_0_over_qnom"].median()), "units": int(len(xr)),
                               "eol_outside_interval": int((xr.get("eol_in_interval", pd.Series(dtype=object)) == False).sum()) if "eol_in_interval" in xr else None}  # noqa: E712
    fst = pd.DataFrame([{"cell_id": c["cell_id"], **c["checks"].get("f_stats", {})} for c in ingest["cells"] if c["meta"]["in_scope"] and not c["excluded"]])
    summary["calibration_factor"] = ({"min_over_units": float(fst["min"].min()), "median_of_unit_medians": float(fst["median"].median()),
                                      "p95_of_unit_p95": float(fst["p95"].quantile(0.95)), "max_over_units": float(fst["max"].max())} if len(fst) else {})
    summary["rest_events"] = {k_: int(sum(c["checks"].get(k_, 0) for c in ingest["cells"] if c["meta"]["in_scope"])) for k_ in
                              ("rest_events_block", "rest_events_pause", "rest_events_rpt_crosscheck", "rest_block_vs_rpt_mismatch", "charge_time_protocol_masked")}
    summary["cycle_predicates"] = {k_: int(sum(c["checks"].get(k_, 0) for c in ingest["cells"] if c["meta"]["in_scope"])) for k_ in
                                   ("cycles", "degenerate", "incomplete", "non_aging", "non_aging_overlap_rpt", "non_aging_current")}
    # side table: the 10 released in-range cells outside the authors' list
    side = []
    for c in ingest["cells"]:
        if c["meta"]["in_scope"]:
            continue
        c5 = np.array(c["c5"], float)
        row = {"cell_id": c["cell_id"], "excluded": c["excluded"], "c5_reaches_200mAh": bool(np.any(c5[np.isfinite(c5)] < 0.2)), "cycles": c["checks"].get("cycles")}
        f_ = DATA_V2 / "processed" / "isu_ilcc_cells" / f"{c['cell_id']}.csv.gz"
        if f_.exists():
            t = pd.read_csv(f_)
            d_cl = clean_capacity(t, "capacity_cycler_Ah", rule, q_nom)
            st = unit_state(d_cl["capacity_cycler_Ah"].to_numpy(float), spec)
            row.update({"T": st.T, "guard_excluded": st.excluded_by_guard})
        side.append(row)
    save_table(pd.DataFrame(side), out / "tables" / "side_table_outside_authors_list")
    summary["side_table"] = side
    write_json(prof, out / "tables" / "eligibility_profile_fit.json")
    return summary
