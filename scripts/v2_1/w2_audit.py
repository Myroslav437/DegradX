#!/usr/bin/env python
"""W2 (brief "DegradX v2.1") — audit, offset pre-screen and eligibility of the TRI formation profile (declarations r4
declared_by_design.v2_1.audit, eol_reported, eligibility, mechanism_diagnostic, weight_guard, offset_prescreen, readings).

  audit       S2-style per unit (audit_unit): EOL under the primary definition (rho q_nom = 0.192 Ah, D13, D15), the guard,
              monotonicity, families, detection sweep; the authors' wording read with q1 (0.8 q1) and the authors' code rule
              (80 % of the maximum summary capacity, last cycle_index at or above it) reported beside it
  split       the declared measured split (as V3 computes it)
  fit         fit_profile on the fitting split with the X2 backfit (as V3): the E5 weight guard and the D05 enable rule
  E3-E5       >= 66 units reaching EOL after the guard; every T >= 44; charge time and mean discharge voltage available in every
              unit and not demoted by the guard
  mechanism   positive runs starting 0..10 positions after a rest event against random fit-range positions (run starts placed at
              detect() start + fit_start - 1), pooled and per source, placebo window, separability branch, all guard-passing
              units and DST-artefacts-included sensitivities
  pre-screen  V4's offset_terms on the fitted mean components of the fitting units reaching EOL (z clipped at 0): Var(y_offset)
              / Var(y) per weighting, with the declared reported rows and the formation-protocol share (permutation null)
Outputs in artifacts/v2.1/w2_audit.
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "v2"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import _common as C  # noqa: E402
import v2_audit_isu as ISU  # noqa: E402  (generic helpers: rest_positions, window_fraction, mechanism)
from degradx import DATA_V21  # noqa: E402
from degradx.data.audit import CleaningRule, audit_unit, clean_capacity  # noqa: E402
from degradx.data.splits import measured_split  # noqa: E402
from degradx.fitting.patterns import detect  # noqa: E402
from degradx.fitting.profile import fit_profile, residual  # noqa: E402
from degradx.generator.generate import GeneratedUnit, Profile  # noqa: E402
from degradx.generator.state import spec_from_declarations  # noqa: E402
from degradx.targets.decomposable import TargetSpec  # noqa: E402
from degradx.utils.checks import CheckTable  # noqa: E402
from degradx.utils.cli import StageContext, stage_parser  # noqa: E402
from degradx.utils.io import save_figure, save_table, write_json  # noqa: E402
from degradx.utils.provenance import RunRecord  # noqa: E402
from degradx.utils.seeding import rng  # noqa: E402

DS = "TRI_FORMATION"
TABLE = DATA_V21 / "processed" / "cycle_tables" / f"{DS}.csv.gz"
CELLS = DATA_V21 / "processed" / "tri_cycles"
E3_MIN, E4_MIN = 66, 44


def authors_wording_T(state, q_raw, q_nom, tau):
    """eol_reported.authors_wording: T_init = min{t >= t1 : smoothed q_t <= 0.8 q1}, with D13's record-end clause."""
    thr = 0.8 * state.q1
    qs = state.q_smooth
    hit = np.flatnonzero(qs[state.t1 - 1:] <= thr)
    if hit.size:
        return int(hit[0]) + state.t1, False
    if len(q_raw) >= 5 and abs(float(np.mean(q_raw[-5:])) - thr) <= tau * q_nom:
        return len(qs), True
    return None, False


def authors_code_life(cyc: pd.DataFrame):
    """eol_reported.authors_code: on the file's summary rows as stored (pass 1 cycles), in cycle_index order."""
    q = cyc.sort_values("cycle_index")
    qd = q["capacity_cycler_Ah"].to_numpy(float)
    thr = 0.8 * np.nanmax(qd)
    if np.nanmin(qd) > thr:
        return None
    return int(q.loc[q["capacity_cycler_Ah"] >= thr, "cycle_index"].iloc[-1])


def unit_runs_v21(u, fam, rests_by_src, k, m, W):
    """Positive-run starts at their true positions (start + fit_start - 1; mechanism_diagnostic.start_index) against the rest
    events of each source; hits in the declared window 0..10 and the placebo -11..-1, and the expected hits at random fit-range
    positions."""
    r = residual(u, fam)
    pats, _ = detect(r, k, m, max_duration=W)
    off = u.fit_start - 1
    starts = np.array([p.start + off for p in pats if p.sign > 0], int)
    fit_pos = np.arange(u.fit_start, u.fit_end + 1)
    rec = {"cell_id": u.cell_id, "runs": int(len(starts)), "positions": int(len(fit_pos))}
    for name, rests in rests_by_src.items():
        rr = rests[(rests >= u.fit_start) & (rests <= u.fit_end)]
        rec[f"{name}__rests"] = int(len(rr))
        for lo, hi in ((0, 10), (-11, -1)):
            _, _, a, _ = ISU.window_fraction(starts, rr, lo, hi, fit_pos)
            rec[f"{name}__hits_{lo}_{hi}"] = a
            rec[f"{name}__exp_hits_{lo}_{hi}"] = int(sum(bool(np.any((s - rr >= lo) & (s - rr <= hi))) for s in fit_pos)) if len(rr) else 0
    return rec


def mech(units_runs, name, seed, n_boot, lo=0, hi=10):
    rows = [{"runs": u["runs"], "positions": u["positions"], f"hits_{lo}_{hi}": u[f"{name}__hits_{lo}_{hi}"],
             f"exp_hits_{lo}_{hi}": u[f"{name}__exp_hits_{lo}_{hi}"]} for u in units_runs]
    res = ISU.mechanism(rows, seed, n_boot, lo, hi)
    res["rest_events"] = int(sum(u[f"{name}__rests"] for u in units_runs))
    return res


def rest_sets(g_raw: pd.DataFrame, g_cl: pd.DataFrame, include_dst: bool = False) -> dict:
    """Rest-event positions (after D12 re-indexing) per source group, placed as rest_positions places them."""
    out = {}
    src = g_raw["rest_event_source"].fillna("").astype(str)
    art = g_raw["dst_artefact"].astype(bool)
    for name, sel in (("all", src != ""), ("diagnostic", src == "diagnostic"), ("non_diagnostic", src.isin(["paused", "gap", "file"]))):
        if include_dst and name in ("all", "non_diagnostic"):
            sel = sel | art
        gg = g_raw.assign(rest_event=sel.to_numpy())
        out[name] = ISU.rest_positions(g_cl, gg)
    return out


def measured_mean_units(prof: dict, P: Profile, units, rho_qnom: float):
    """Fitted mean components of measured units as GeneratedUnit objects (noise and patterns zero), for V4's offset_terms
    (offset_prescreen.terms): z clipped at 0; non-capacity m_state = phi_c(z) (Mapping holds end values outside [0, 1]), m = m_state +
    delta_{c,i}; capacity m_state = q1_bar - z (q1_bar - rho q_nom), m = q1_i - z (q1_i - rho q_nom)."""
    offs = prof["v2"]["offsets_all_fitting_units"]
    q1_bar = P.x0["capacity"]
    out = []
    for u in units:
        T = u.state.T if u.state.T is not None else len(u.q)
        z = np.maximum(np.asarray(u.state.z[:T], float), 0.0)
        C_all = len(P.all_channels)
        m_state = np.zeros((T, C_all))
        m = np.zeros((T, C_all))
        for ci, c in enumerate(P.all_channels):
            if c == "capacity":
                m_state[:, ci] = q1_bar - z * (q1_bar - rho_qnom)
                m[:, ci] = u.state.q1 - z * (u.state.q1 - rho_qnom)
            elif c in P.mappings:
                m_state[:, ci] = P.mappings[c](z)
                m[:, ci] = m_state[:, ci] + float((offs.get(u.cell_id) or {}).get(c, 0.0))
            else:
                m_state[:, ci] = m[:, ci] = P.x0[c]
        out.append(GeneratedUnit(DS, len(out), u.cell_id, T, z, m, np.zeros(T), np.zeros((T, C_all)), [], P.all_channels, m_state=m_state, q1=u.state.q1))
    return out


def prescreen(gunits, spec: TargetSpec, kind: str, offset_terms) -> dict:
    ys, yst, yo, per_unit, chan = [], [], [], [], {}
    W = spec.weights(kind)
    for u in gunits:
        if u.T < spec.L:
            continue
        tg, y_state, y_off, _ = offset_terms(u, spec, kind)
        ys.append(tg["y"]), yst.append(y_state), yo.append(y_off)
        per_unit.append({"cell_id": u.source_unit, "y_offset_mean": float(np.mean(y_off)), "windows": int(len(y_off))})
        ends = np.arange(spec.L, u.T + 1)
        idx = ends[:, None] - spec.L + np.arange(spec.L)[None, :]
        for ci, c in enumerate(spec.channels):
            if spec.kappa[ci] == 0:
                continue
            chan.setdefault(c, []).append((W[None, :, ci] * (u.m[idx, ci] - u.m_state[idx, ci])).sum(axis=1))
    Y, YS, YO = (np.concatenate(a) for a in (ys, yst, yo))
    return {"share": float(np.var(YO) / np.var(Y)), "offset_to_state": float(np.var(YO) / np.var(YS)), "corr_offset_state": float(np.corrcoef(YO, YS)[0, 1]),
            "var_y": float(np.var(Y)), "windows": int(len(Y)), "units": len(per_unit),
            "per_channel_share": {c: float(np.var(np.concatenate(v)) / np.var(Y)) for c, v in chan.items()}, "_per_unit": per_unit, "_Y": (Y, YO)}


def r2_by_group(values: np.ndarray, groups: np.ndarray) -> float:
    v = np.asarray(values, float)
    ss_tot = np.sum((v - v.mean()) ** 2)
    if ss_tot == 0:
        return np.nan
    df = pd.DataFrame({"v": v, "g": groups})
    gm = df.groupby("g")["v"].transform("mean").to_numpy()
    return float(1 - np.sum((v - gm) ** 2) / ss_tot)


def protocol_share(values, groups, seed_rng, n_perm: int) -> dict:
    values, groups = np.asarray(values, float), np.asarray(groups)
    r2 = r2_by_group(values, groups)
    null = np.array([r2_by_group(values, seed_rng.permutation(groups)) for _ in range(n_perm)])
    g, n = len(set(groups)), len(values)
    adj = 1 - (1 - r2) * (n - 1) / (n - g) if n > g else np.nan
    mn = float(np.mean(null))
    return {"r2": r2, "adjusted_r2": float(adj), "mean_null_r2": mn, "expected_null_r2": (g - 1) / (n - 1) if n > 1 else np.nan,
            "p_value": float((1 + np.sum(null >= r2)) / (n_perm + 1)), "calibrated_share": float((r2 - mn) / (1 - mn)) if mn < 1 else np.nan,
            "groups": g, "units": n}


def main() -> int:
    p = stage_parser(__doc__, "v2.1/w2_audit")
    p.add_argument("--workers", type=int, default=8)
    args = p.parse_args()
    ctx = StageContext.from_args(args)
    decl, dd = ctx.declarations, ctx.declarations["declared_by_design"]
    v21 = dd["v2_1"]
    if args.dry_run:
        print("plan: W2 audit, offset pre-screen and eligibility of TRI_FORMATION")
        return 0
    import v4_generate_units as V4

    out, ct = ctx.out_dir, CheckTable()
    q_nom = C.q_nom_of(DS)
    spec = spec_from_declarations(decl, q_nom)
    rule = CleaningRule("D12", **dd["capacity_series"]["cleaning_rule"]["params"])
    crule = C.channel_rule_v2(dd)
    k = float(dd["pattern_detection"]["multiple_k"]["value"])
    m = int(dd["pattern_detection"]["min_run_length"]["value"])
    W = int(dd["smoothing"]["window_length"]["value"])
    n_boot = int(dd["v2"]["statistics"]["bootstrap_n_resamples"])
    L = int(dd["target"]["window_length_L"]["value"])
    beta = dd["target"]["weights"]["beta"]["value"]
    tau = float(dd["eol"]["record_end_rule"]["tau"])
    seed = args.seed
    df = C.load_scope(DS, dd)
    summary = {"dataset": DS, "q_nom_Ah": q_nom, "threshold_Ah": spec.rho * q_nom}
    with RunRecord("v2.1/w2_audit", out, {"table": str(TABLE)}, {"split": seed, "D05": f"('generation','D05','{DS}')"}, ctx.device) as rec:
        # ---------------------------------------------------------------- S2-style audit
        with rec.section("audit"):
            fn = partial(audit_unit, column="capacity_cycler_Ah", rule=rule, q_nom=q_nom, decl=decl, rho_grid=dd["eol"]["rho_sensitivity_grid"]["value"],
                         k_grid=dd["eol"]["q1_reference"]["sensitivity_k"], sweep_k=dd["pattern_detection"]["sweep"]["multiple_k"],
                         sweep_m=dd["pattern_detection"]["sweep"]["min_run_length"], k_default=k, m_default=m,
                         mono_tol=float(dd["audit"]["monotonicity_tolerance"]["value"]), spec_base=spec)
            groups = [g for _, g in df.groupby("cell_id", sort=True)]
            with ProcessPoolExecutor(max_workers=args.workers) as ex:
                recs = list(ex.map(fn, groups, chunksize=2))
            for r in recs:
                r.pop("_trace", None)
                r.pop("patterns", None)
            units = pd.DataFrame(recs)
            # authors' definitions (reported only)
            from degradx.generator.state import unit_state
            aw, ac = [], []
            for g in groups:
                cid = g["cell_id"].iloc[0]
                d = clean_capacity(g, "capacity_cycler_Ah", rule, q_nom)
                q = d["capacity_cycler_Ah"].to_numpy(float)
                if len(q) < max(spec.sg_window, 20):
                    aw.append((cid, None, False))
                else:
                    st = unit_state(q, spec)
                    aw.append((cid, *authors_wording_T(st, q, q_nom, tau)))
                seq = int(g["seq"].iloc[0])
                ac.append((cid, authors_code_life(pd.read_csv(CELLS / f"{seq}_cycles.csv.gz"))))
            units["T_authors_wording"] = units["cell_id"].map({c: t for c, t, _ in aw})
            units["T_authors_wording_from_record_end"] = units["cell_id"].map({c: e for c, _, e in aw})
            units["life_authors_code_cycle_index"] = units["cell_id"].map(dict(ac))
            meta = df.drop_duplicates("cell_id").set_index("cell_id")[["seq", "protocol_id", "batch", "tags"]]
            units = units.join(meta, on="cell_id")
            save_table(units, out / "tables" / "audit_units")
            passing = units[~units["too_short"].astype(bool) & ~units["excluded_by_guard"].fillna(False).astype(bool)]
            reach = passing[passing["T"].notna()]
            sweep = {f"k{kk}_m{mm}": {"positive": int(units.get(f"n_pos_k{kk}_m{mm}", pd.Series(dtype=float)).sum()),
                                      "negative": int(units.get(f"n_neg_k{kk}_m{mm}", pd.Series(dtype=float)).sum())}
                     for kk in dd["pattern_detection"]["sweep"]["multiple_k"] for mm in dd["pattern_detection"]["sweep"]["min_run_length"]}
            rho_att = {f"rho{rho:.2f}": {"r2": int(passing[f"T_r2_rho{rho:.2f}"].notna().sum()), "r1": int(passing[f"T_r1_rho{rho:.2f}"].notna().sum())}
                       for rho in dd["eol"]["rho_sensitivity_grid"]["value"]}
            summary["audit"] = {
                "units_in_table": int(len(units)), "too_short": int(units["too_short"].sum()),
                "guard_excluded": int(units["excluded_by_guard"].fillna(False).astype(bool).sum()), "passing_guard": int(len(passing)),
                "eol_primary": {"reaching": int(len(reach)), "from_record_end": int(reach["T_from_record_end"].fillna(False).sum()), "T": C.summarise(reach["T"])},
                "eol_authors_wording_q1": {"reaching": int(passing["T_authors_wording"].notna().sum()),
                                           "from_record_end": int(passing["T_authors_wording_from_record_end"].fillna(False).sum()),
                                           "T": C.summarise(passing["T_authors_wording"].dropna()),
                                           "agreement_with_primary_T": C.summarise((passing["T_authors_wording"] - passing["T"]).dropna()),
                                           "label": "the paper's wording with 'initial' read as q1 (DegradX's operationalisation)"},
                "eol_authors_code": {"with_life": int(units["life_authors_code_cycle_index"].notna().sum()), "rhyu_178": 178,
                                     "life_cycle_index": C.summarise(units["life_authors_code_cycle_index"].dropna()),
                                     "label": "the authors' definition as implemented in their code (cx26 get_cycle_life), cycle_index units"},
                "eol_attainment_rho_grid": rho_att,
                "q1_material_difference_units": int(passing["q1_material_diff"].sum()),
                "monotone_within_tolerance": {"units": int(passing["monotone_within_tol"].sum()), "of": int(len(passing))},
                "best_family_in_sample": passing["best_family_in_sample"].value_counts().to_dict(),
                "detection_sweep_counts": sweep,
                "cycles_dropped_by_D12": int(units["n_dropped_by_cleaning"].sum()),
            }
        # ---------------------------------------------------------------- split and fit (as V3)
        with rec.section("fit"):
            elig_df = pd.DataFrame([{"cell_id": r.cell_id, "reaches_eol": bool(pd.notna(r.T))} for r in passing.itertuples()])
            split = measured_split(elig_df, seed, DS, float(dd["statistics"]["splits"]["measured"]["fitting"]))
            save_table(split, out / "tables" / f"split_{DS}")
            channels = C.available_channels(df)
            prof, diag = fit_profile(df, split, dataset=DS, q_nom=q_nom, spec=spec, rule=rule, channels=channels, crule=crule, decl=decl,
                                     workers=args.workers, k=k, m=m, sweep_k=dd["pattern_detection"]["sweep"]["multiple_k"], base_seed=seed, offsets=C.offsets_params(dd))
            prof["declared_used"]["channels_available"] = channels
            write_json(prof, out / "tables" / "w2_profile_fit.json")
        # ---------------------------------------------------------------- E3-E5
        nd = df[~df["degenerate"].astype(bool)]
        avail = {}
        for ch in ("charge_time_min", "mean_discharge_voltage_V", "internal_resistance_ohm", "temperature_mean_C"):
            per = nd[ch].notna().groupby(nd["cell_id"]).mean() >= 0.5
            avail[ch] = {"units_with_channel": int(per.sum()), "units": int(per.size), "every_unit": bool(per.all())}
        roles = prof["derived"]["channel_roles"]
        e_maps = prof["estimated_from_data"]["E3_channel_mappings"]
        e_noise = prof["estimated_from_data"]["E5_noise"]
        guard = {c: {"delta": float(e_maps[c]["delta"]), "noise_sd": float(np.sqrt(e_noise[c]["variance"])),
                     "ratio": float(abs(e_maps[c]["delta"]) / np.sqrt(e_noise[c]["variance"]))} for c in ("charge_time", "mean_discharge_voltage") if c in e_maps}
        e3 = int(len(reach))
        held_reach = int(((split["split"] == "held_out") & split["reaches_eol"]).sum())
        e4_fail = list(reach.loc[reach["T"] < E4_MIN, "cell_id"])
        e5 = bool(avail["charge_time_min"]["every_unit"] and avail["mean_discharge_voltage_V"]["every_unit"]
                  and "charge_time" in roles["weighted"] and "mean_discharge_voltage" in roles["weighted"])
        summary["eligibility"] = {
            "E1": "pass (documentation; cells with a documented identity only)", "E2": "pass (documentation; E2 on the files at W1)",
            "E3": {"units_reaching_eol_after_guard": e3, "required": E3_MIN, "passes": e3 >= E3_MIN, "held_out_reaching_eol": held_reach,
                   "fitting_reaching_eol": int(((split["split"] == "fitting") & split["reaches_eol"]).sum())},
            "E4": {"units_reaching_eol_with_T_below_44": e4_fail, "min_T": float(reach["T"].min()) if len(reach) else None, "passes": not e4_fail},
            "E5": {"availability": avail, "channels_used": channels, "weighted_after_guard": roles["weighted"], "demoted": roles.get("demoted_by_guard"),
                   "weight_guard": guard, "passes": e5},
            "E6": "pass with the CC BY-NC condition (documentation)"}
        ct.require("E3: >= 66 units reach EOL after the guard", e3 >= E3_MIN, ">= 66", f"{e3} (held out {held_reach})")
        ct.require("E4: every unit reaching EOL has T >= 44", not e4_fail, "all", ", ".join(e4_fail) or "all")
        ct.require("E5: charge time and mean discharge voltage available in every unit and pass the weight guard", e5, "both",
                   json.dumps({c: round(v["ratio"], 2) for c, v in guard.items()}))
        # ---------------------------------------------------------------- D05 and the mechanism diagnostic
        e6 = prof["estimated_from_data"]["E6_patterns"]
        summary["d05"] = {t: {kk: v.get(kk) for kk in ("enabled", "events", "measured_rate_per_100", "noise_only_rate_per_100", "ratio_to_noise")} for t, v in e6.items()}
        fam = prof["estimated_from_data"]["E2_family_choice"]["selected"]
        with rec.section("mechanism"):
            def runs_for(unit_objs, include_dst=False):
                out_r = []
                for u in unit_objs:
                    g_raw = df[df["cell_id"] == u.cell_id]
                    g_cl = clean_capacity(g_raw, "capacity_cycler_Ah", rule, q_nom)
                    out_r.append(unit_runs_v21(u, fam, rest_sets(g_raw, g_cl, include_dst), k, m, W))
                return out_r
            fit_runs = runs_for(diag["unit_objects"])
            save_table(pd.DataFrame(fit_runs), out / "tables" / "mechanism_units")
            mres = {name: {"post_0_10": mech(fit_runs, name, seed, n_boot), "placebo_-11_-1": mech(fit_runs, name, seed, n_boot, -11, -1)}
                    for name in ("all", "diagnostic", "non_diagnostic")}
            n_nd = mres["non_diagnostic"]["post_0_10"]["rest_events"]
            ci_nd = (mres["non_diagnostic"]["post_0_10"]["ci_low"], mres["non_diagnostic"]["post_0_10"]["ci_high"])
            if n_nd < 10:
                branch = (f"(i) not separable in this dataset: only {n_nd} readable rests are not preceded by a lower-rate diagnostic discharge")
            elif np.isfinite(ci_nd[0]) and ci_nd[0] > 1:
                branch = "(ii) positive runs cluster after rests without a rate change: rest-induced recovery is separable from the rate change"
            else:
                branch = ("(iii) rests without a rate change are not followed by clustered positive runs; clustering after diagnostic blocks, where "
                          "their interval lies above 1, is attributed to the diagnostic block (its lower-rate or held discharge and its rests), not to rest alone")
            # sensitivities: DST artefacts included; all guard-passing units
            dst_runs = runs_for(diag["unit_objects"], include_dst=True)
            split_all = split.assign(split="fitting")
            _, diag_all = fit_profile(df, split_all, dataset=f"{DS}_all", q_nom=q_nom, spec=spec, rule=rule, channels=channels, crule=crule, decl=decl,
                                      workers=args.workers, k=k, m=m, sweep_k=[k], base_seed=seed, offsets=C.offsets_params(dd))
            all_runs = runs_for(diag_all["unit_objects"])
            pooled = mres["all"]["post_0_10"]
            placebo = mres["all"]["placebo_-11_-1"]
            rest_induced = bool(pooled["ci_low"] > 1 and not (placebo["ci_low"] > 1))
            summary["mechanism_diagnostic"] = {
                "fitting_units": mres, "separability": {"n_non_diagnostic_rests": n_nd, "branch": branch},
                "sensitivity_dst_included": {name: {"post_0_10": mech(dst_runs, name, seed, n_boot)} for name in ("all", "non_diagnostic")},
                "sensitivity_all_guard_passing_units": {name: {"post_0_10": mech(all_runs, name, seed, n_boot), "placebo_-11_-1": mech(all_runs, name, seed, n_boot, -11, -1)}
                                                       for name in ("all", "diagnostic", "non_diagnostic")},
                "start_index": "detect() start + fit_start - 1 (DEVIATIONS T7 corrected)"}
            pos_on = bool(e6.get("positive", {}).get("enabled"))
            summary["readings"] = {"X6_ii_regeneration": ("present at scale" if pos_on else "not present at scale (D05 does not enable the positive type)")
                                   + ("; rest-induced (pooled ratio interval above 1, placebo not)" if pos_on and rest_induced else
                                      ("; regeneration not localised after rest events" if pos_on else "")),
                                   "rest_induced_test": {"pooled_ci_low": pooled["ci_low"], "placebo_ci_low": placebo["ci_low"], "rest_induced": rest_induced},
                                   "patterns_enabled": {t: bool(v.get("enabled")) for t, v in e6.items()}}
        # ---------------------------------------------------------------- offset pre-screen
        with rec.section("prescreen"):
            # null_permuted reference point: fitting-split charge-time readings over the fit range (as V4 / _common.null_pool)
            pool = np.concatenate([u.channels["charge_time"][u.fit_start - 1:u.fit_end] for u in diag["unit_objects"]])
            P = Profile.from_json(prof, pool[np.isfinite(pool)])
            tspec = TargetSpec.build(P, beta, L, 6.0)          # h = 6 (target.position_profiles.recency), as V4 builds it
            fit_objs = diag["unit_objects"]
            reach_objs = [u for u in fit_objs if u.state.T is not None]
            rho_qnom = spec.rho * q_nom
            g_reach = measured_mean_units(prof, P, reach_objs, rho_qnom)
            g_all = measured_mean_units(prof, P, fit_objs, rho_qnom)
            ps = {}
            for kind in ("recency", "uniform"):
                r_main = prescreen(g_reach, tspec, kind, V4.offset_terms)
                r_all = prescreen(g_all, tspec, kind, V4.offset_terms)
                tagged = set(df.loc[df["seq"].isin([274, 276, 278, 140, 155]), "cell_id"])
                r_untag = prescreen([u for u in g_reach if u.source_unit not in tagged], tspec, kind, V4.offset_terms)
                # leave-one-unit-out influence
                loo = []
                for i, u in enumerate(g_reach):
                    rr = prescreen(g_reach[:i] + g_reach[i + 1:], tspec, kind, V4.offset_terms)
                    loo.append((abs(rr["share"] - r_main["share"]), u.source_unit, rr["share"]))
                loo.sort(reverse=True)
                ps[kind] = {k_: v for k_, v in r_main.items() if not k_.startswith("_")}
                ps[kind]["sensitivity_all_fitting_units"] = r_all["share"]
                ps[kind]["without_tagged_cells"] = {"share": r_untag["share"], "units": r_untag["units"]}
                ps[kind]["largest_leave_one_out"] = {"cell_id": loo[0][1], "share_without": loo[0][2], "abs_change": loo[0][0]}
                ps[kind]["_per_unit"] = r_main["_per_unit"]
            # formation-protocol share (headline: unit-mean y_offset under recency)
            pu = pd.DataFrame(ps["recency"]["_per_unit"]).merge(df.drop_duplicates("cell_id")[["cell_id", "protocol_id", "seq"]], on="cell_id")
            g_ = rng(seed, "evaluation", "W2-protocol", DS)
            n_perm = int(n_boot)
            head = protocol_share(pu["y_offset_mean"], pu["protocol_id"], g_, n_perm)
            offs = prof["v2"]["offsets_all_fitting_units"]
            per_ch = {}
            ids = pu["cell_id"].tolist()
            for c in [c for c in channels if c != "capacity"]:
                per_ch[f"delta_{c}"] = protocol_share([offs[i][c] for i in ids], pu["protocol_id"], g_, n_perm)
            q1_by = {u.cell_id: u.state.q1 for u in reach_objs}
            per_ch["q1_minus_q1bar"] = protocol_share([q1_by[i] - P.x0["capacity"] for i in ids], pu["protocol_id"], g_, n_perm)
            for kind in ps:
                ps[kind].pop("_per_unit", None)
            rba = prof["v2"].get("residual_before_after", {})
            summary["offset_prescreen"] = {"per_weighting": ps, "max_share": max(ps[k_]["share"] for k_ in ps), "stop_threshold": 0.5,
                                           "stop": bool(max(ps[k_]["share"] for k_ in ps) > 0.5),
                                           "offset_sampling_noise": {c: {kk: rba.get(c, {}).get(kk) for kk in ("offset_variance", "offset_sampling_noise_term", "offset_variance_noise_corrected")}
                                                                     for c in rba},
                                           "formation_protocol_share": {"headline": head, "reading": "formation protocol explains part of the offsets" if head["p_value"] < 0.05
                                                                        else "no evidence that formation protocol explains the offsets (p >= 0.05)", "per_channel": per_ch},
                                           "units_reaching_eol": len(g_reach), "e3_without_tagged_cells": int(len(reach[~reach["cell_id"].isin(tagged)]))}
            ct.require("offset pre-screen: Var(y_offset)/Var(y) <= 0.5 under both weightings (stop before fitting above)", not summary["offset_prescreen"]["stop"],
                       "<= 0.5", json.dumps({k_: round(ps[k_]["share"], 3) for k_ in ps}))
        summary["eligible"] = bool(e3 >= E3_MIN and not e4_fail and e5 and not summary["offset_prescreen"]["stop"])
        write_json(summary, out / "tables" / "audit_summary.json")
        # ---------------------------------------------------------------- figures
        import matplotlib.pyplot as plt
        from degradx.viz.style import apply as style
        style()
        fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
        ax[0].hist(reach["T"], bins=30, color="0.4")
        ax[0].set_title(f"T (positions), {len(reach)} units reaching EOL", fontsize=9)
        for c, a in (("charge_time", ax[1]), ("mean_discharge_voltage", ax[2])):
            mp = e_maps[c]
            a.plot(mp["grid"], mp["values"], "k-")
            a.set_title(f"phi_{c}(z): delta {guard[c]['delta']:.3g}, noise SD {guard[c]['noise_sd']:.3g}", fontsize=8)
            a.set_xlabel("z")
        save_figure(fig, out / "figures" / "tri_formation_audit")
        code = ct.finalize(out)
        (out / "logs" / "checks.md").write_text(ct.markdown() + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
