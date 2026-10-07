#!/usr/bin/env python
"""V5 (brief "DegradX v2") — RQ1, profile fidelity on the v2 profiles (X2 offsets + X3 correlated noise).

Per profile (declarations r3 declared_by_design.v2.fidelity, .readings, .tstr_isolation):
  * TSTR ratio (S5 estimator, v2 generated units of generation seeds 0-2 x model seeds 0-4, the S3 held-out units reaching
    EOL), and the X1 ablation repeated on the v2 profiles (input sets full, capacity_only, capacity_relative,
    capacity_state, full_centred; the same paired BCa readings and leave-one-seed-out rule as V1);
  * discriminative score per generation seed; covariance agreement per generation seed with the measured
    fitting-vs-held-out baseline and its 95% unit-bootstrap interval (X3 reading); the same two measures on the X3-off set
    (generation seed 0, independent noise) for X3's own share;
  * property table with three columns: measured fitting split (the v2 profile), measured held-out split, generated
    (generation seed 0), all by the V3 estimator (offsets, D27);
  * v1-vs-v2 comparison per profile.
Representation distance is not measured (D25). Outputs in ``artifacts/v2/v5_fidelity``.
"""

from __future__ import annotations

import json
import pickle
import sys

import numpy as np
import pandas as pd
import yaml

import _common as C
import v1_tstr_isolation as V1
from degradx import ARTIFACTS_DIR, CONFIG_DIR, DATA_V2
from degradx.data.audit import CleaningRule
from degradx.fitting.profile import CHANNEL_COLUMNS, fit_profile, prepare_units
from degradx.generator.state import spec_from_declarations
from degradx.metrics import fidelity as F
from degradx.models.lstm import train_regressor
from degradx.utils.checks import CheckTable
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.io import save_figure, save_table, write_json
from degradx.utils.provenance import RunRecord

INPUT_SETS = ("full", "capacity_only", "capacity_relative", "capacity_state", "full_centred")
READINGS = {k: v for k, v in V1.READINGS.items()}
DESCRIPTIVE = {"full_vs_capacity_relative": ("full", "capacity_relative"), "full_vs_capacity_state": ("full", "capacity_state")}


def generated_frame(gen_units, channels) -> pd.DataFrame:
    rows = []
    for u in gen_units:
        x = u.x
        d = {"cell_id": f"gen{u.index}", "position": np.arange(1, u.T + 1), "cycle_number": np.arange(1, u.T + 1), "degenerate": False}
        for ci, c in enumerate(channels):
            d[CHANNEL_COLUMNS[c]] = x[:, ci]
        rows.append(pd.DataFrame(d))
    return pd.concat(rows, ignore_index=True)


def baseline_bootstrap(Wf, Wh, Uh, mu, sd, seed: int, n_resamples: int) -> dict:
    """95% unit-bootstrap (percentile) interval of the measured fitting-vs-held-out covariance agreement, resampling held-out
    units (declarations v2.readings.X3_covariance)."""
    C_f = F.channel_correlation(Wf, mu, sd)
    g = np.random.default_rng(seed)
    units = np.unique(Uh)
    rows = {u: np.flatnonzero(Uh == u) for u in units}
    vals = []
    for _ in range(n_resamples):
        pick = g.choice(units, size=len(units), replace=True)
        idx = np.concatenate([rows[u] for u in pick])
        vals.append(F.covariance_agreement(F.channel_correlation(Wh[idx], mu, sd), C_f)["relative_frobenius"])
    lo, hi = np.quantile(vals, [0.025, 0.975])
    return {"ci_low": float(lo), "ci_high": float(hi), "n_resamples": n_resamples, "method": "percentile over held-out units"}


def property_rows(ds, profs: dict, q_nom, rho, minimum) -> list[dict]:
    """profs: {"fitting": ..., "held_out": ..., "generated": ...} profiles from the V3 estimator."""
    rows = []

    def traj(prof):
        e = prof["estimated_from_data"]["E1_theta_distribution"]
        from degradx.fitting.families import FAMILIES

        drift, trans = [], []
        for u in e["per_unit"]:
            T = int(u["T"])
            n = np.arange(1, T + 1, dtype=float)
            Q = u["q1"] * FAMILIES[e["family"]](np.array(u["family_params"]), n)
            drift.append((u["q1"] - rho * q_nom) / T * 100 * 1000)
            d2 = np.abs(np.diff(Q, 2)) if T > 3 else np.array([0.0])
            trans.append((int(np.argmax(d2)) + 2) / T)
        return {"drift_mAh_per_100": drift, "transition_fraction_of_T": trans}

    cols = list(profs)
    e = {k: profs[k]["estimated_from_data"] for k in cols}
    n_units = {k: e[k]["E1_theta_distribution"]["n_units"] for k in cols}
    fam_sel = e["fitting"]["E2_family_choice"]["selected"]
    rows.append({"property": "trajectory family (selected); median CV-RMSE of the profile's family [fraction of q1]",
                 **{k: f"{e[k]['E2_family_choice']['selected']}; {e[k]['E2_family_choice']['median_cv_rmse'][fam_sel]:.4f}" for k in cols}, "units": n_units})
    tr = {k: traj(profs[k]) for k in cols}
    for key, label in (("drift_mAh_per_100", "drift rate [mAh per 100 cycles]"), ("transition_fraction_of_T", "transition position [fraction of T]")):
        rows.append({"property": label, **{k: C.summarise(tr[k][key]) for k in cols}, "units": n_units})
    rows.append({"property": "unit length T [cycles]", **{k: C.summarise(e[k]["E7_length_distribution"]) for k in cols}, "units": n_units})
    rows.append({"property": "early-life reference q1 [Ah], units reaching EOL", **{k: (profs[k].get("v2") or {}).get("q1_fitting_units_reaching_eol") for k in cols}})
    for c in e["fitting"]["E5_noise"]:
        rows.append({"property": f"noise variance, {c} (per-unit-centred AR(1))", **{k: e[k]["E5_noise"][c]["variance"] for k in cols}})
        rows.append({"property": f"noise lag-1 autocorrelation, {c}", **{k: e[k]["E5_noise"][c]["phi"] for k in cols}})
        if c != "capacity":
            rows.append({"property": f"per-unit offset IQR, {c}", **{k: (profs[k]["v2"]["backfit"][c]["delta_iqr"] if profs[k].get("v2") else None) for k in cols}})
    for t in ("positive", "negative"):
        rows.append({"property": f"{t} residual runs per 100 positions (enabled in profile: {e['fitting']['E6_patterns'][t]['enabled']})",
                     **{k: e[k]["E6_patterns"][t]["measured_rate_per_100"] for k in cols}, "events": {k: e[k]["E6_patterns"][t]["events"] for k in cols}})
    cm = {k: np.asarray(profs[k]["v2"]["within_unit_correlation"]) for k in cols}
    rows.append({"property": "within-unit residual correlation (X3 estimator): relative Frobenius / mean |delta rho| against the fitting split",
                 **{k: F.covariance_agreement(cm["fitting"], cm[k]) for k in cols}})
    for r in rows:
        r["dataset"] = ds
    if n_units["held_out"] < minimum["theta_and_length_units"]:
        for r in rows:
            r["void_held_out"] = f"held-out units reaching EOL {n_units['held_out']} < {minimum['theta_and_length_units']}"
    return rows


def main() -> int:
    p = stage_parser(__doc__, "v2/v5_fidelity")
    p.add_argument("--workers", type=int, default=12)
    p.add_argument("--datasets", nargs="*", default=["MATR", "HUST"])
    p.add_argument("--profile-config", nargs="*", default=[])
    p.add_argument("--max-windows-per-unit", type=int, default=100)
    p.add_argument("--skip-ablation", action="store_true", help="TSTR on the full input set only")
    args = p.parse_args()
    for kv in args.profile_config:
        C.register_profile(*kv.split("="))
    ctx = StageContext.from_args(args)
    decl, dd = ctx.declarations, ctx.declarations["declared_by_design"]
    if args.dry_run:
        print(f"plan: v2 fidelity for {args.datasets}")
        return 0
    from degradx.viz import s5 as viz

    out, ct = ctx.out_dir, CheckTable()
    L = int(dd["target"]["window_length_L"]["value"])
    k = int(dd["eol"]["q1_reference"]["k"])
    gen_seeds, model_seeds = dd["statistics"]["seeds"]["generation"], dd["statistics"]["seeds"]["model_init"]
    n_boot = int(dd["v2"]["statistics"]["bootstrap_n_resamples"])
    minimum = dd["minimum_counts"]["value"]
    hm = dd["minimum_counts"]["held_out_units_per_measure"]
    lstm_cfg = yaml.safe_load((CONFIG_DIR / "models" / "lstm.yaml").read_text())
    rule = CleaningRule("D12", **dd["capacity_series"]["cleaning_rule"]["params"])
    crule = C.channel_rule_v2(dd)
    v1fid = json.loads((ARTIFACTS_DIR / "s5_fidelity" / "tables" / "fidelity.json").read_text())
    results = {}
    sets = INPUT_SETS if not args.skip_ablation else ("full",)
    with RunRecord("v2/v5_fidelity", out, {"config": ctx.config, "datasets": args.datasets, "input_sets": list(sets)},
                   {"generation": gen_seeds, "model_init": model_seeds, "evaluation": args.seed}, ctx.device) as rec:
        for ds in args.datasets:
            prof = C.v2_profile(ds)
            chans = prof["declared_used"]["channels_available"]
            q_nom = C.q_nom_of(ds)
            spec = spec_from_declarations(decl, q_nom)
            spec_q1 = spec_from_declarations(decl, q_nom, measured=False)
            split = C.v2_split(ds)
            df = C.load_scope(ds, dd)
            fit_u = prepare_units(df, split.loc[split["split"] == "fitting", "cell_id"], q_nom, spec, rule, chans, crule)
            ho_u = prepare_units(df, split.loc[split["split"] == "held_out", "cell_id"], q_nom, spec, rule, chans, crule)
            ms_fit, ms_ho = F.measured_series(fit_u, chans), F.measured_series(ho_u, chans)
            n_ho, n_ho_reach = len(ms_ho), sum(s.T is not None for s in ms_ho)
            gens = {g: pickle.loads((DATA_V2 / "generated" / ds / f"seed{g}.pkl").read_bytes())[0] for g in gen_seeds}
            x3off_f = DATA_V2 / "generated" / ds / "seed0_x3off.pkl"
            gen_off = pickle.loads(x3off_f.read_bytes())[0] if x3off_f.exists() else None
            res = {"window_length": L, "channels": chans, "units": {"measured_fitting": len(ms_fit), "measured_held_out": n_ho,
                                                                     "measured_held_out_reaching_eol": n_ho_reach, "generated_per_seed": len(gens[gen_seeds[0]])}}
            # ---- distributional: discriminator and covariance agreement (+ baseline interval), and the X3-off set
            with rec.section(f"{ds}_distributional"):
                Wf, Uf, _ = F.windows(ms_fit, L, max_per_unit=args.max_windows_per_unit, seed=args.seed)
                Wh, Uh, _ = F.windows(ms_ho, L, max_per_unit=args.max_windows_per_unit, seed=args.seed)
                flat = Wf.reshape(-1, Wf.shape[-1])
                mu, sd = flat.mean(axis=0), np.where(flat.std(axis=0) > 0, flat.std(axis=0), 1.0)
                C_h, C_f = F.channel_correlation(Wh, mu, sd), F.channel_correlation(Wf, mu, sd)
                res["baseline_measured_fitting_vs_held_out"] = {**{f"cov_{kk}": v for kk, v in F.covariance_agreement(C_h, C_f).items()},
                                                                "cov_relative_frobenius_interval": baseline_bootstrap(Wf, Wh, Uh, mu, sd, args.seed, n_boot)}
                per_seed = []
                sets_d = [(g, units) for g, units in gens.items()] + ([("x3off", gen_off)] if gen_off is not None else [])
                for g, units in sets_d:
                    gs_ = F.generated_series(units, len(chans))
                    gseed = 0 if g == "x3off" else g
                    Wg, Ug, _ = F.windows(gs_, L, max_per_unit=args.max_windows_per_unit, seed=args.seed + gseed)
                    disc = F.discriminative_score(Wh, Uh, Wg, Ug, mu, sd, seed=args.seed + gseed, device=ctx.device)
                    C_g = F.channel_correlation(Wg, mu, sd)
                    per_seed.append({"generation_seed": g, **disc, **{f"cov_{kk}": v for kk, v in F.covariance_agreement(C_h, C_g).items()},
                                     "generated_windows": int(len(Wg))})
                res["per_generation_seed"] = [r for r in per_seed if r["generation_seed"] != "x3off"]
                res["x3_off_seed0"] = next((r for r in per_seed if r["generation_seed"] == "x3off"), None)
                errs = np.array([s_["discriminative_error"] for s_ in res["per_generation_seed"]])
                res["discriminative_error_mean"] = float(errs.mean())
                res["discriminative_error_seed_half_range"] = float((errs.max() - errs.min()) / 2)
                res["cov_relative_frobenius_mean"] = float(np.mean([s_["cov_relative_frobenius"] for s_ in res["per_generation_seed"]]))
                res["void"] = {"discriminative_error": (f"held-out units {n_ho} < {hm['discriminative_error']['min_units']}" if n_ho < hm["discriminative_error"]["min_units"] else None),
                               "covariance_agreement": f"held-out units {n_ho} < {hm['covariance_agreement']['min_units']}" if n_ho < hm["covariance_agreement"]["min_units"] else None}
            # ---- TSTR with the X1 ablation on the v2 profile
            with rec.section(f"{ds}_tstr"):
                q1_fit, q1_ho = V1.q1_of(ms_fit, spec_q1), V1.q1_of(ms_ho, spec_q1)
                em_fit, em_ho = V1.early_medians(ms_fit, k), V1.early_medians(ms_ho, k)
                rho_qnom = spec.rho * spec.q_nom
                Xm, Um, Rm = F.windows(ms_fit, L, with_rul=True, with_elapsed=True)
                Xh, Uh2, Rh = F.windows(ms_ho, L, with_rul=True, with_elapsed=True)
                n_train_units = sum(s_.T is not None for s_ in ms_fit)
                gen_w = {}
                for g, units in gens.items():
                    gs_ = F.generated_series(units[:n_train_units], len(chans))
                    Xg, Ug, Rg = F.windows(gs_, L, with_rul=True, with_elapsed=True)
                    gen_w[g] = (Xg, Ug, Rg, V1.q1_of(gs_, spec_q1), V1.early_medians(gs_, k))
                runs_sse, tstr = {}, {}
                for which in sets:
                    runs_sse[which] = {"TSTR": {}, "TRTR": {}}
                    runs = []
                    Xh_r = V1.restrict(Xh, Uh2, q1_ho, which, rho_qnom, em_ho)
                    Xm_r = V1.restrict(Xm, Um, q1_fit, which, rho_qnom, em_fit)
                    for ms in model_seeds:
                        m = train_regressor(Xm_r, Rm, Um, seed=ms, device=ctx.device, cfg=lstm_cfg)
                        units_h, s_, nh = F.per_unit_sse(m.predict(Xh_r), Rh, Uh2)
                        runs_sse[which]["TRTR"][ms] = s_
                        runs.append({"model": "TRTR", "generation_seed": None, "model_seed": ms, "rmse": float(np.sqrt(s_.sum() / nh.sum())), "epochs": m.history["epochs"]})
                    for g, (Xg, Ug, Rg, q1g, emg) in gen_w.items():
                        Xg_r = V1.restrict(Xg, Ug, q1g, which, rho_qnom, emg)
                        for ms in model_seeds:
                            m = train_regressor(Xg_r, Rg, Ug, seed=ms, device=ctx.device, cfg=lstm_cfg)
                            _, s_, nh = F.per_unit_sse(m.predict(Xh_r), Rh, Uh2)
                            runs_sse[which]["TSTR"][(g, ms)] = s_
                            runs.append({"model": "TSTR", "generation_seed": g, "model_seed": ms, "rmse": float(np.sqrt(s_.sum() / nh.sum())), "epochs": m.history["epochs"]})
                    a = np.mean(list(runs_sse[which]["TSTR"].values()), axis=0)
                    b = np.mean(list(runs_sse[which]["TRTR"].values()), axis=0)
                    trtr_mean = np.mean([r["rmse"] for r in runs if r["model"] == "TRTR"])
                    tstr[which] = {**F.ratio_bootstrap(a, b, nh, seed=args.seed, n_resamples=n_boot), "rmse_tstr_cycles": float(np.sqrt(a.sum() / nh.sum())),
                                   "rmse_trtr_cycles": float(np.sqrt(b.sum() / nh.sum())), "held_out_units": int(len(nh)), "held_out_windows": int(nh.sum()),
                                   "training_units_each": n_train_units,
                                   "ratio_spread": {"min": float(min(r["rmse"] for r in runs if r["model"] == "TSTR") / trtr_mean),
                                                    "max": float(max(r["rmse"] for r in runs if r["model"] == "TSTR") / trtr_mean)},
                                   "runs": runs}
                    save_table(pd.DataFrame(runs), out / "tables" / f"tstr_runs_{ds}_{which}")
                    print(f"[v5] {ds} {which}: ratio {tstr[which]['ratio']:.3f} [{tstr[which]['ci_low']:.3f}, {tstr[which]['ci_high']:.3f}]", flush=True)
                res["tstr"] = {**tstr["full"], "void": (f"held-out units reaching EOL {tstr['full']['held_out_units']} < {hm['transfer_ratio']['min_units_reaching_eol']}"
                                                        if tstr["full"]["held_out_units"] < hm["transfer_ratio"]["min_units_reaching_eol"] else None)}
                res["tstr_input_sets"] = tstr
                if not args.skip_ablation:
                    res["x1_on_v2"] = {"tests": V1.ratio_tests(runs_sse, nh, READINGS, args.seed, n_boot),
                                       "descriptive": V1.ratio_tests(runs_sse, nh, DESCRIPTIVE, args.seed, n_boot),
                                       "leave_one_out": {**{f"without_generation_seed_{g}": V1.ratio_tests(runs_sse, nh, READINGS, args.seed, n_boot, drop={"g": g}) for g in gen_seeds},
                                                         **{f"without_model_seed_{ms}": V1.ratio_tests(runs_sse, nh, READINGS, args.seed, n_boot, drop={"ms": ms}) for ms in model_seeds}}}
                    res["x1_on_v2"]["readings"] = {name: {"interval_above_zero": bool(res["x1_on_v2"]["tests"][name]["ci_low"] > 0),
                                                          "holds": bool(res["x1_on_v2"]["tests"][name]["ci_low"] > 0
                                                                        and all(l_[name]["ci_low"] > 0 for l_ in res["x1_on_v2"]["leave_one_out"].values()))}
                                                   for name in READINGS}
                ids = [ms_ho[i].unit_id for i in units_h]
                np.savez_compressed(out / "tables" / f"per_unit_sse_{ds}.npz", units=np.array(ids), n_windows=nh,
                                    **{f"{w}__TSTR__g{g}_m{ms}": v for w in sets for (g, ms), v in runs_sse[w]["TSTR"].items()},
                                    **{f"{w}__TRTR__m{ms}": v for w in sets for ms, v in runs_sse[w]["TRTR"].items()})
            # ---- property table: fitting / held-out / generated, V3 estimator
            with rec.section(f"{ds}_properties"):
                offs = C.offsets_params(dd)
                ho_split = split[split["split"] == "held_out"].assign(split="fitting")
                meas_ho, _ = fit_profile(df, ho_split, dataset=ds, q_nom=q_nom, spec=spec, rule=rule, channels=chans, crule=crule, decl=decl,
                                         workers=args.workers, k=2.5, m=2, sweep_k=[2.5], base_seed=args.seed, offsets=offs)
                gdf = generated_frame(gens[gen_seeds[0]], chans)
                gsplit = pd.DataFrame({"cell_id": gdf["cell_id"].unique(), "split": "fitting", "reaches_eol": True})
                gen_prof, _ = fit_profile(gdf, gsplit, dataset=ds, q_nom=q_nom, spec=spec_q1, rule=rule, channels=chans, crule=crule, decl=decl,
                                          workers=args.workers, k=2.5, m=2, sweep_k=[2.5], base_seed=args.seed, offsets=offs)
                rows = property_rows(ds, {"fitting": prof, "held_out": meas_ho, "generated": gen_prof}, q_nom, spec.rho, minimum)
                write_json(rows, out / "tables" / f"properties_{ds}.json")
                res["properties_file"] = f"tables/properties_{ds}.json"
                save_figure(viz.property_distributions(ds, meas_ho, gen_prof, q_nom, spec.rho), out / "figures" / f"{ds.lower()}_property_distributions")
            # ---- readings and v1-vs-v2
            base_hi = res["baseline_measured_fitting_vs_held_out"]["cov_relative_frobenius_interval"]["ci_high"]
            res["readings"] = {"X3_covariance_closed": bool(res["cov_relative_frobenius_mean"] <= base_hi), "X3_covariance_threshold": base_hi}
            if ds in v1fid:
                v1 = v1fid[ds]
                v1_err = np.array([s_["discriminative_error"] for s_ in v1["per_generation_seed"]])
                v1_half = float((v1_err.max() - v1_err.min()) / 2)
                res["readings"]["X3_discriminator_narrows"] = bool(res["discriminative_error_mean"] - float(v1_err.mean()) > v1_half)
                res["v1_vs_v2"] = {"tstr_ratio": {"v1": [v1["tstr"]["ratio"], v1["tstr"]["ci_low"], v1["tstr"]["ci_high"]],
                                                  "v2": [res["tstr"]["ratio"], res["tstr"]["ci_low"], res["tstr"]["ci_high"]]},
                                   "discriminative_error_mean": {"v1": float(v1_err.mean()), "v1_seed_half_range": v1_half, "v2": res["discriminative_error_mean"]},
                                   "cov_relative_frobenius_mean": {"v1": float(np.mean([s_["cov_relative_frobenius"] for s_ in v1["per_generation_seed"]])),
                                                                   "v1_baseline": v1["baseline_measured_fitting_vs_held_out"]["cov_relative_frobenius"],
                                                                   "v2": res["cov_relative_frobenius_mean"], "v2_baseline_interval": res["baseline_measured_fitting_vs_held_out"]}}
            results[ds] = res
            write_json(results, out / "tables" / "fidelity.json")
            ct.require(f"{ds}: discriminator does not separate trivially (accuracy < 0.99)", np.mean([s_["accuracy"] for s_ in res["per_generation_seed"]]) < 0.99,
                       "< 0.99", f"{np.mean([s_['accuracy'] for s_ in res['per_generation_seed']]):.3f}", severity="warn")
            ct.require(f"{ds}: TSTR ratio finite with interval", np.isfinite(res["tstr"]["ratio"]), "finite", res["tstr"]["ratio"])
        # ---- cross-profile reading X2(i) and the anchor rule
        if "MATR" in results and "HUST" in results:
            h = results["HUST"]["tstr"]
            closed = bool(h["ci_low"] <= results["MATR"]["tstr"]["ratio"] <= h["ci_high"])
            results["readings_cross_profile"] = {"X2_i_matr_gap_closed": closed, "matr_ratio": results["MATR"]["tstr"]["ratio"], "hust_interval": [h["ci_low"], h["ci_high"]],
                                                 "anchor_d_record_needed": not closed}
            write_json(results, out / "tables" / "fidelity.json")
        save_figure(viz.tstr_ratios(results_for_viz(results)), out / "figures" / "tstr_error_ratio")
        save_figure(viz.discriminator(results_for_viz(results)), out / "figures" / "discriminative_score")
        code = ct.finalize(out)
        (out / "logs" / "checks.md").write_text(ct.markdown() + "\n")
    return code


def results_for_viz(results: dict) -> dict:
    return {k: v for k, v in results.items() if isinstance(v, dict) and "tstr" in v}


if __name__ == "__main__":
    sys.exit(main())
