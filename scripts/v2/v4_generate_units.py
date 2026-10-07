#!/usr/bin/env python
"""V4 (brief "DegradX v2") — generate units from the v2 profiles (X2 offsets, X3 correlated noise) and verify them.

Per profile and generation seed (declared [0, 1, 2]), 300 units split 0.7 / 0.15 / 0.15 at unit level (S4 rule), cached in
``data/v2/generated/<profile>/seed<g>.pkl``. Checks (declarations target.s4_acceptance_checks for recency and uniform
weighting, D25; declared_by_design.v2.generator_checks):
  * sum(phi*) = y and g(x) - y = sum w eps on every window; mean over units of g(x) - y ~ 0; E[eps] = 0 per channel;
  * z starts at the pristine level and T is the first crossing; disabling patterns leaves z, T, R and noise unchanged;
  * a unit at z = 0 with zero offsets (q1 = q1_bar, delta = 0), no patterns and no noise has y = 0;
  * construction: pooled sample correlation of the generated noise within 0.05 of the fitted residual correlation;
    estimator: the V3 estimator (backfit + E4) on generated observations against the fitted correlation (reported);
  * generated q1 (S3 estimator on generated capacity) spread against the fitting split (IQR within 20%);
  * offset contribution: Var(y_offset) / Var(y) and Var(y_offset) / Var(y_state) per seed and weighting over all windows;
    above 0.5 of Var(y) is a stop-and-report case (brief §6);
  * innovation-correlation repairs (X3): units repaired and largest entry change.
Outputs in ``artifacts/v2/v4_generate_units``.
"""

from __future__ import annotations

import pickle
import sys
from copy import deepcopy

import numpy as np
import pandas as pd

import _common as C
from degradx import DATA_V2
from degradx.data.audit import CleaningRule, clean_capacity
from degradx.fitting.profile import fit_profile, prepare_units
from degradx.generator.generate import Profile, generate_unit
from degradx.generator.state import spec_from_declarations, unit_state
from degradx.targets.decomposable import TargetSpec, unit_targets
from degradx.utils.checks import CheckTable
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.io import save_figure, save_table, write_json
from degradx.utils.provenance import RunRecord
from degradx.utils.seeding import rng

from degradx.fitting.noise_mappings import within_unit_correlation  # noqa: E402


def load_v2_profile(ds: str, decl: dict):
    prof = C.v2_profile(ds)
    split = C.v2_split(ds)
    q_nom = C.q_nom_of(ds)
    dd = decl["declared_by_design"]
    df = C.load_scope(ds, dd)
    units = prepare_units(df, split.loc[split["split"] == "fitting", "cell_id"], q_nom, spec_from_declarations(decl, q_nom),
                          CleaningRule("D12", **dd["capacity_series"]["cleaning_rule"]["params"]), ["capacity", "charge_time"], C.channel_rule_v2(dd))
    pool = np.concatenate([u.channels["charge_time"][u.fit_start - 1:u.fit_end] for u in units])
    return Profile.from_json(prof, pool[np.isfinite(pool)]), prof, q_nom, df, split


def generate_set(P: Profile, gen_seed: int, n_units: int, base_seed: int):
    units, idx = [], 0
    while len(units) < n_units:
        u = generate_unit(P, gen_seed, idx)
        idx += 1
        if u is not None:
            units.append(u)
        if idx > 20 * n_units:
            raise RuntimeError("generator rejects too many draws")
    g = rng(base_seed, "split", P.name, "generated", gen_seed)
    perm = g.permutation(len(units))
    n_tr, n_va = int(round(0.7 * len(units))), int(round(0.15 * len(units)))
    split = np.empty(len(units), dtype=object)
    split[perm[:n_tr]], split[perm[n_tr:n_tr + n_va]], split[perm[n_tr + n_va:]] = "train", "validation", "test"
    table = pd.DataFrame({"index": [u.index for u in units], "source_unit": [u.source_unit for u in units], "T": [u.T for u in units],
                          "q1": [u.q1 for u in units], "n_patterns": [len(u.patterns) for u in units], "split": split})
    return units, table


def offset_terms(u, spec: TargetSpec, kind: str):
    """Per window: y, the state term sum w (m_state - x0) and the offset term sum w (m - m_state) (patterns separately)."""
    ends = np.arange(spec.L, u.T + 1)
    tg = unit_targets(u, spec, kind, ends=ends)
    idx = ends[:, None] - spec.L + np.arange(spec.L)[None, :]
    W = spec.weights(kind)[None]
    ms = u.m_state[idx]
    y_state = (W * (ms - spec.x0[None, None, :])).sum(axis=(1, 2))
    y_off = (W * (u.m[idx] - ms)).sum(axis=(1, 2))
    y_pat = tg["sparse"].sum(axis=(1, 2))
    return tg, y_state, y_off, y_pat


def main() -> int:
    p = stage_parser(__doc__, "v2/v4_generate_units")
    p.add_argument("--workers", type=int, default=12)
    p.add_argument("--datasets", nargs="*", default=["MATR", "HUST"])
    p.add_argument("--profile-config", nargs="*", default=[])
    args = p.parse_args()
    for kv in args.profile_config:
        C.register_profile(*kv.split("="))
    ctx = StageContext.from_args(args)
    decl, dd = ctx.declarations, ctx.declarations["declared_by_design"]
    if args.dry_run:
        print(f"plan: generate 3 x 300 units for {args.datasets} with the v2 profiles")
        return 0
    from degradx.viz import s4 as viz

    out, ct = ctx.out_dir, CheckTable()
    sc = dd["v2"]["scope"]["weightings"]
    WEIGHTINGS_V2 = (sc["primary"], sc["sensitivity"])
    gen_seeds = dd["statistics"]["seeds"]["generation"]
    n_units = int(dd["statistics"]["generated_units"]["attribution_and_usability"])
    beta = dd["target"]["weights"]["beta"]["value"]
    L = int(dd["target"]["window_length_L"]["value"])
    tol_corr = 0.05
    stop_share = 0.5
    rule = CleaningRule("D12", **dd["capacity_series"]["cleaning_rule"]["params"])
    summary = {}
    with RunRecord("v2/v4_generate_units", out, {"config": ctx.config, "datasets": args.datasets},
                   {"generation": gen_seeds, "split": f"derive_seed({args.seed}, 'split', <profile>, 'generated', <g>)"}, ctx.device) as rec:
        for ds in args.datasets:
            P, prof, q_nom, df, msplit = load_v2_profile(ds, decl)
            spec = TargetSpec.build(P, beta, L, 6.0)
            r_pool = np.asarray(prof["estimated_from_data"]["E4_channel_covariance"]["correlation"])
            r_fit = np.asarray(prof["v2"]["within_unit_correlation"])
            nmeas = len(P.channels)
            phis_pool = np.clip([P.noise_pooled[c]["phi"] for c in P.channels], -0.999, 0.999)
            summary[ds] = {"kappa": dict(zip(spec.channels, spec.kappa.tolist())), "x0": dict(zip(spec.channels, spec.x0.tolist())), "seeds": {},
                           "innovation_correlation": P.innov_repair, "within_unit_correlation_fitted": r_fit.tolist(), "pooled_correlation_fitted": r_pool.tolist()}
            # implied per-unit stationary correlation r_eps * B(own phi) over the theta units (X3 feasibility report)
            implied = []
            for uu in P.theta_units:
                ph = []
                for c in P.channels:
                    v = ((uu.get("noise") or {}).get(c) or {}).get("phi")
                    ph.append(v if v is not None and np.isfinite(v) else P.noise_pooled[c]["phi"])
                ph = np.clip(ph, -0.999, 0.999)
                B = np.sqrt(np.outer(1 - ph ** 2, 1 - ph ** 2)) / (1 - np.outer(ph, ph))
                implied.append(P.innov_corr * B)
            implied = np.array(implied)
            off_ = ~np.eye(nmeas, dtype=bool)
            summary[ds]["implied_stationary_correlation"] = {"mean_over_units": implied.mean(axis=0).tolist(),
                                                             "max_abs_mean_minus_target": float(np.max(np.abs(implied.mean(axis=0) - r_fit)[off_])) if nmeas > 1 else 0.0}
            gen_spec = spec_from_declarations(decl, q_nom, measured=False)
            for gs in gen_seeds:
                cache = DATA_V2 / "generated" / ds / f"seed{gs}.pkl"
                with rec.section(f"{ds}_generate_seed{gs}"):
                    if ctx.should_skip(cache, label=f"{ds} seed {gs} units"):
                        units, table = pickle.loads(cache.read_bytes())
                    else:
                        units, table = generate_set(P, gs, n_units, args.seed)
                        cache.parent.mkdir(parents=True, exist_ok=True)
                        cache.write_bytes(pickle.dumps((units, table), protocol=pickle.HIGHEST_PROTOCOL))
                save_table(table, out / "tables" / f"generated_units_{ds}_seed{gs}")
                res = {"units": len(units), "T_median": float(table["T"].median()), "T_q25": float(table["T"].quantile(0.25)), "T_q75": float(table["T"].quantile(0.75)),
                       "units_with_patterns": int((table["n_patterns"] > 0).sum()), "patterns": int(table["n_patterns"].sum()), "weightings": {}}
                long_units = [u for u in units if u.T >= L]
                with rec.section(f"{ds}_checks_seed{gs}"):
                    for kind in WEIGHTINGS_V2:
                        e_sum = e_ref = 0.0
                        n_win = 0
                        gy, ys, yst, yo, yp, cg, cs = [], [], [], [], [], [], []
                        for u in long_units:
                            tg, y_state, y_off, y_pat = offset_terms(u, spec, kind)
                            e_sum = max(e_sum, float(np.max(np.abs(tg["phi_star"].sum(axis=(1, 2)) - tg["y"]) / np.maximum(1.0, np.abs(tg["y"])))))
                            e_ref = max(e_ref, float(np.max(np.abs((tg["g"] - tg["y"]) - tg["noise_term"]))))
                            gy.append(float(np.mean(tg["g"] - tg["y"])))
                            n_win += len(tg["y"])
                            ys.append(tg["y"]); yst.append(y_state); yo.append(y_off); yp.append(y_pat)
                            cg.append(np.abs(tg["graded"]).sum(axis=2).ravel()); cs.append(np.abs(tg["sparse"]).sum(axis=2).ravel())
                        ct.require(f"{ds} seed {gs} [{kind}]: sum(phi*) == y on every window", e_sum < 1e-9, "< 1e-9 (relative)", f"{e_sum:.2e} over {n_win} windows")
                        ct.require(f"{ds} seed {gs} [{kind}]: g(x) - y == sum(w eps) on every window", e_ref < 1e-9, "< 1e-9", f"{e_ref:.2e}")
                        mu, se = float(np.mean(gy)), float(np.std(gy, ddof=1) / np.sqrt(len(gy)))
                        ct.require(f"{ds} seed {gs} [{kind}]: mean over units of g(x) - y ~ 0", abs(mu) <= 3 * se, "|mean| <= 3 SE", f"mean {mu:.3e}, SE {se:.3e}")
                        Y, YS, YO, YP = (np.concatenate(a) for a in (ys, yst, yo, yp))
                        share, ratio = float(np.var(YO) / np.var(Y)), float(np.var(YO) / np.var(YS))
                        ct.require(f"{ds} seed {gs} [{kind}]: offset contribution Var(y_offset)/Var(y) <= {stop_share} (brief §6 stop rule)", share <= stop_share,
                                   f"<= {stop_share}", f"{share:.3f} (Var(y_offset)/Var(y_state) {ratio:.3f})")
                        G, S = np.concatenate(cg), np.concatenate(cs)
                        has_sparse = bool(np.any(S > 0))
                        res["weightings"][kind] = {"windows": n_win, "offset_share_of_var_y": share, "offset_to_state_variance_ratio": ratio,
                                                   "corr_offset_state": float(np.corrcoef(YO, YS)[0, 1]),
                                                   "pattern_to_state_variance_ratio": float(np.var(YP) / np.var(YS)) if has_sparse else None,
                                                   "graded_sparse_abs_corr": float(np.corrcoef(G, S)[0, 1]) if has_sparse and np.std(S) > 0 else None,
                                                   "var_y": float(np.var(Y)), "max_rel_sum_error": e_sum, "max_ref_error": e_ref}
                    # pristine unit: z = 0, zero offsets (q1 = q1_bar, delta = 0), no patterns, no noise -> y = 0
                    pu = deepcopy(long_units[0])
                    pu.z[:] = 0.0
                    for ci, c in enumerate(P.channels):
                        pu.m[:, ci] = P.mappings[c](0.0)
                    pu.m_state = pu.m.copy()
                    pu.p[:] = 0.0
                    pu.eps[:] = 0.0
                    ymax = max(float(np.abs(unit_targets(pu, spec, kd)["y"]).max()) for kd in WEIGHTINGS_V2)
                    ct.require(f"{ds} seed {gs}: unit at z = 0 with zero offsets, no patterns, no noise has y = 0", ymax < 1e-12, "0", f"{ymax:.2e}")
                    # E[eps] = 0 per measured channel
                    for ci, c in enumerate(P.channels):
                        means = np.array([np.mean(u.eps[:, ci]) for u in units])
                        sd = np.sqrt(P.noise_pooled[c]["variance"])
                        mu, se = float(means.mean()), float(means.std(ddof=1) / np.sqrt(len(means)))
                        ct.require(f"{ds} seed {gs}: E[eps_{c}] ~ 0", abs(mu) <= 3 * se, "|mean| <= 3 SE over units", f"{mu / sd:+.3f} noise SD (SE {se / sd:.3f})")
                    z0 = max(float(u.z[0]) for u in units)
                    first = all(u.z[-1] >= 1.0 and (u.T < 2 or u.z[-2] < 1.0) for u in units)
                    ct.require(f"{ds} seed {gs}: z starts at the pristine level and T is the first crossing of z = 1", first and z0 <= 0.05,
                               "z_1 <= 0.05; z_T >= 1 > z_{T-1}", f"max z_1 {z0:.3f}; first crossing {first}")
                    inv = True
                    for u in units[:: max(1, len(units) // 60)]:
                        u0 = generate_unit(P, gs, u.index, patterns_on=False)
                        inv &= u0.T == u.T and np.array_equal(u0.z, u.z) and np.array_equal(u0.R, u.R) and np.array_equal(u0.eps, u.eps) and np.array_equal(u0.m, u.m)
                    ct.require(f"{ds} seed {gs}: disabling patterns leaves z, T, R, mean and noise unchanged", inv, "identical", inv)
                    # X3: the within-unit estimator on the generated noise (construction check read on the mean over seeds below)
                    r_gen = within_unit_correlation([u.eps[:, :nmeas] for u in units])
                    r_gen_pool = np.corrcoef(np.vstack([u.eps[:, :nmeas] for u in units]), rowvar=False)
                    res["noise_within_unit_correlation_generated"] = r_gen.tolist()
                    res["noise_pooled_correlation_generated"] = r_gen_pool.tolist()
                    # generated q1 spread (S3 estimator on generated capacity)
                    q1g = np.array([unit_state(u.x[:, 0], gen_spec).q1 for u in units])
                    q1m = prof["v2"]["q1_fitting_units_reaching_eol"]  # declared comparator: the population generation resamples
                    iqr_g = float(np.subtract(*np.percentile(q1g, [75, 25])))
                    res["q1_generated"] = C.summarise(q1g) | {"iqr": iqr_g}
                    ct.require(f"{ds} seed {gs}: generated q1 shows the measured spread (IQR within 20% of the fitting units reaching EOL)",
                               abs(iqr_g - q1m["iqr"]) <= 0.2 * q1m["iqr"], f"{q1m['iqr'] * 1000:.1f} mAh +- 20%", f"{iqr_g * 1000:.1f} mAh", severity="warn")
                summary[ds]["seeds"][gs] = res
                write_json(summary, out / "tables" / "summary.json")
            # X3 construction check on the mean over generation seeds (declared)
            off = ~np.eye(nmeas, dtype=bool)
            r_mean = np.mean([np.asarray(summary[ds]["seeds"][g]["noise_within_unit_correlation_generated"]) for g in gen_seeds], axis=0)
            rp_mean = np.mean([np.asarray(summary[ds]["seeds"][g]["noise_pooled_correlation_generated"]) for g in gen_seeds], axis=0)
            dmax = float(np.max(np.abs(r_mean - r_fit)[off])) if nmeas > 1 else 0.0
            dpool = float(np.max(np.abs(rp_mean - r_pool)[off])) if nmeas > 1 else 0.0
            summary[ds]["x3_construction"] = {"within_unit_mean_over_seeds": r_mean.tolist(), "max_abs_diff_within_unit": dmax,
                                              "pooled_mean_over_seeds": rp_mean.tolist(), "max_abs_diff_pooled": dpool,
                                              "explained_by_pooled_phi_construction": bool(summary[ds]["implied_stationary_correlation"]["max_abs_mean_minus_target"] > tol_corr)}
            ct.require(f"{ds}: X3 construction - within-unit correlation of generated noise (mean over seeds) within {tol_corr} of the fitted rho_bar", dmax <= tol_corr,
                       f"<= {tol_corr}", f"max |delta r| {dmax:.3f} (pooled comparison {dpool:.3f}; implied-by-construction gap "
                                         f"{summary[ds]['implied_stationary_correlation']['max_abs_mean_minus_target']:.3f})", severity="warn")
            # X3 isolation (declared reading X3_isolation): one set from the v2 profile with independent per-channel noise
            with rec.section(f"{ds}_x3_off_set"):
                cache_off = DATA_V2 / "generated" / ds / "seed0_x3off.pkl"
                if ctx.should_skip(cache_off, label=f"{ds} X3-off set"):
                    pass
                else:
                    P_off = deepcopy(P)
                    P_off.innov_corr = None
                    units_off, table_off = generate_set(P_off, gen_seeds[0], n_units, args.seed)
                    cache_off.write_bytes(pickle.dumps((units_off, table_off), protocol=pickle.HIGHEST_PROTOCOL))
                    summary[ds]["x3_off_set"] = {"file": str(cache_off.relative_to(DATA_V2.parent.parent)), "units": len(units_off),
                                                 "within_unit_correlation": within_unit_correlation([u.eps[:, :nmeas] for u in units_off]).tolist()}
            # X3 estimator check on generation seed 0: V3 estimator applied to generated observations
            with rec.section(f"{ds}_estimator_check"):
                units0, _t = pickle.loads((DATA_V2 / "generated" / ds / f"seed{gen_seeds[0]}.pkl").read_bytes())
                rows = []
                for u in units0:
                    x = u.x
                    d = {"cell_id": f"gen{u.index}", "position": np.arange(1, u.T + 1), "cycle_number": np.arange(1, u.T + 1), "degenerate": False}
                    from degradx.fitting.profile import CHANNEL_COLUMNS

                    for ci, c in enumerate(P.channels):
                        d[CHANNEL_COLUMNS[c]] = x[:, ci]
                    rows.append(pd.DataFrame(d))
                gdf = pd.concat(rows, ignore_index=True)
                gsplit = pd.DataFrame({"cell_id": gdf["cell_id"].unique(), "split": "fitting", "reaches_eol": True})
                gprof, _ = fit_profile(gdf, gsplit, dataset=ds, q_nom=q_nom, spec=gen_spec, rule=rule, channels=P.channels, crule=C.channel_rule_v2(dd), decl=decl,
                                       workers=args.workers, k=2.5, m=2, sweep_k=[2.5], base_seed=args.seed, offsets=C.offsets_params(dd))
                r_est = np.asarray(gprof["estimated_from_data"]["E4_channel_covariance"]["correlation"])
                off = ~np.eye(nmeas, dtype=bool)
                dmax_e = float(np.max(np.abs(r_est - r_fit)[off])) if nmeas > 1 else 0.0
                summary[ds]["estimator_check"] = {"correlation_estimated_on_generated": r_est.tolist(), "max_abs_diff": dmax_e,
                                                  "noise_generated_estimated": gprof["estimated_from_data"]["E5_noise"],
                                                  "offsets_generated_iqr": {c: b["delta_iqr"] for c, b in gprof["v2"]["backfit"].items()},
                                                  "offsets_fitted_iqr": {c: b["delta_iqr"] for c, b in prof["v2"]["backfit"].items()}}
                ct.require(f"{ds}: S3/V3 estimator on generated observations recovers the fitted residual correlation within {tol_corr} (reported)", dmax_e <= tol_corr,
                           f"<= {tol_corr}", f"max |delta r| {dmax_e:.3f}", severity="warn")
            with rec.section(f"{ds}_figures"):
                save_figure(viz.overlay_measured_generated(ds, P, units0, df, msplit, decl, q_nom), out / "figures" / f"{ds.lower()}_generated_vs_measured")
            write_json(summary, out / "tables" / "summary.json")
        code = ct.finalize(out)
        (out / "logs" / "checks.md").write_text(ct.markdown() + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
