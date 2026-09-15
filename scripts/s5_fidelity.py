#!/usr/bin/env python
"""S5 — RQ1, profile fidelity (paper §3.5.1; Tables 1-2, Figure 6).

Inputs: S3 profiles and splits, S4 generated units (``data/generated``), S1 cycle tables. Per profile:
  * discriminative score (2-layer GRU, 2000 iterations, unit-level 80/20 split, balanced classes) of generated vs held-out
    measured windows, per generation seed (coarse indicator only, paper l.264);
  * Frechet distance in a TS2Vec representation (encoder trained on measured fitting-split windows), generated vs held-out,
    with the measured fitting-vs-held-out distance as baseline;
  * cross-channel correlation agreement (relative Frobenius, mean |delta rho|), with the same baseline;
  * TSTR: LSTM on generated units (transfer target R, channels + elapsed position) vs the same architecture on measured
    fitting-split units, both evaluated on held-out measured units reaching EOL; ratio of RMSEs from per-unit squared errors
    averaged over generation seeds x model-initialisation seeds; BCa interval over held-out units;
  * property table: the S3 estimators applied to held-out measured units and to generated units (seed 0).
Window length and effective numbers of units are written next to every number; measurements below the declared minimum
counts (D02) are marked void. Outputs in ``artifacts/s5_fidelity``.
"""

from __future__ import annotations

import json
import pickle
import sys

import numpy as np
import pandas as pd
import yaml

from degradx import ARTIFACTS_DIR, CONFIG_DIR, DATA_DIR
from degradx.data.audit import CleaningRule
from degradx.fitting.families import FAMILIES
from degradx.fitting.profile import ChannelRule, fit_profile, prepare_units
from degradx.generator.state import spec_from_declarations
from degradx.metrics import fidelity as F
from degradx.models.lstm import train_regressor
from degradx.utils.checks import CheckTable
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.config import load_yaml
from degradx.utils.io import save_figure, save_table, write_json
from degradx.utils.provenance import RunRecord

PROFILES = {"MATR": "matr", "HUST": "hust", "NASA_PCoE": "nasa_pcoe"}
COLS = {"capacity": "capacity_cycler_Ah", "charge_time": "charge_time_min", "mean_discharge_voltage": "mean_discharge_voltage_V",
        "internal_resistance": "internal_resistance_ohm", "temperature_mean": "temperature_mean_C"}


def generated_frame(gen_units, channels) -> pd.DataFrame:
    rows = []
    for u in gen_units:
        x = u.x
        d = {"cell_id": f"gen{u.index}", "position": np.arange(1, u.T + 1), "cycle_number": np.arange(1, u.T + 1), "degenerate": False}
        for ci, c in enumerate(channels):
            d[COLS[c]] = x[:, ci]
        rows.append(pd.DataFrame(d))
    return pd.concat(rows, ignore_index=True)


def trajectory_properties(prof: dict, q_nom: float, rho: float) -> dict:
    """Drift rate (capacity fall per 100 cycles from q1 to EOL) and transition position (argmax |second difference| of the
    fitted trajectory, as a fraction of T), per unit reaching EOL."""
    e = prof["estimated_from_data"]["E1_theta_distribution"]
    drift, trans = [], []
    for u in e["per_unit"]:
        T = int(u["T"])
        n = np.arange(1, T + 1, dtype=float)
        Q = u["q1"] * FAMILIES[e["family"]](np.array(u["family_params"]), n)
        drift.append((u["q1"] - rho * q_nom) / T * 100 * 1000)  # mAh per 100 cycles
        d2 = np.abs(np.diff(Q, 2)) if T > 3 else np.array([0.0])
        trans.append((int(np.argmax(d2)) + 2) / T)
    return {"drift_mAh_per_100": drift, "transition_fraction_of_T": trans}


def summarise(v) -> dict:
    v = np.asarray([x for x in v if x is not None and np.isfinite(x)], float)
    if not len(v):
        return {"n": 0}
    return {"n": int(len(v)), "median": float(np.median(v)), "q25": float(np.quantile(v, 0.25)), "q75": float(np.quantile(v, 0.75))}


def property_table(ds, meas_prof, gen_prof, q_nom, rho, minimum) -> list[dict]:
    rows = []
    em, eg = meas_prof["estimated_from_data"], gen_prof["estimated_from_data"]
    nm_units, ng_units = em["E1_theta_distribution"]["n_units"], eg["E1_theta_distribution"]["n_units"]
    fam_m, fam_g = em["E2_family_choice"], eg["E2_family_choice"]
    rows.append({"property": "trajectory family (selected); median CV-RMSE of the profile's family [fraction of q1]",
                 "measured": f"{fam_m['selected']}; {fam_m['median_cv_rmse'][fam_g['selected']]:.4f}" if fam_m.get("median_cv_rmse") else None,
                 "generated": f"{fam_g['selected']}; {fam_g['median_cv_rmse'][fam_g['selected']]:.4f}", "units_measured": nm_units, "units_generated": ng_units})
    tm, tg = trajectory_properties(meas_prof, q_nom, rho), trajectory_properties(gen_prof, q_nom, rho)
    for key, label in (("drift_mAh_per_100", "drift rate [mAh per 100 cycles]"), ("transition_fraction_of_T", "transition position [fraction of T]")):
        rows.append({"property": label, "measured": summarise(tm[key]), "generated": summarise(tg[key]), "units_measured": nm_units, "units_generated": ng_units})
    for c in em["E5_noise"]:
        rows.append({"property": f"noise variance, {c}", "measured": em["E5_noise"][c]["variance"], "generated": eg["E5_noise"][c]["variance"],
                     "units_measured": len(meas_prof["units"]["fitting_passing_guard"]), "units_generated": len(gen_prof["units"]["fitting_passing_guard"])})
        rows.append({"property": f"noise lag-1 autocorrelation, {c}", "measured": em["E5_noise"][c]["phi"], "generated": eg["E5_noise"][c]["phi"],
                     "units_measured": len(meas_prof["units"]["fitting_passing_guard"]), "units_generated": len(gen_prof["units"]["fitting_passing_guard"])})
    rows.append({"property": "unit length T [cycles]", "measured": summarise(em["E7_length_distribution"]), "generated": summarise(eg["E7_length_distribution"]),
                 "units_measured": nm_units, "units_generated": ng_units})
    for t in ("positive", "negative"):
        pm, pg = em["E6_patterns"][t], eg["E6_patterns"][t]
        void_m = pm["events"] < minimum["pattern_events"]
        void_g = pg["events"] < minimum["pattern_events"]
        rows.append({"property": f"{t} pattern rate [per 100 positions] (enabled in profile: {meas_prof.get('_profile_enabled', {}).get(t)})",
                     "measured": pm["measured_rate_per_100"], "generated": pg["measured_rate_per_100"], "events_measured": pm["events"], "events_generated": pg["events"],
                     "noise_only_rate_measured": pm["noise_only_rate_per_100"], "noise_only_rate_generated": pg["noise_only_rate_per_100"]})
        rows.append({"property": f"{t} pattern amplitude [mAh]", "measured": None if void_m else summarise(np.array(pm["amplitude_Ah"]) * 1000),
                     "generated": None if void_g else summarise(np.array(pg["amplitude_Ah"]) * 1000), "events_measured": pm["events"], "events_generated": pg["events"],
                     "void": f"measured events {pm['events']} < {minimum['pattern_events']}" if void_m else None})
        rows.append({"property": f"{t} pattern duration [positions]", "measured": None if void_m else summarise(pm["duration"]),
                     "generated": None if void_g else summarise(pg["duration"]), "events_measured": pm["events"], "events_generated": pg["events"],
                     "void": f"measured events {pm['events']} < {minimum['pattern_events']}" if void_m else None})
    cm, cg = np.array(em["E4_channel_covariance"]["correlation"]), np.array(eg["E4_channel_covariance"]["correlation"])
    agr = F.covariance_agreement(cm, cg) if cm.shape == cg.shape else {}
    rows.append({"property": "cross-channel residual correlation (relative Frobenius distance, mean |delta rho|)", "measured": em["E4_channel_covariance"]["correlation"],
                 "generated": eg["E4_channel_covariance"]["correlation"], **agr})
    for r in rows:
        r["dataset"] = ds
        if ("units_measured" in r and r["units_measured"] is not None and isinstance(r["units_measured"], int) and r["units_measured"] < minimum["theta_and_length_units"]
                and r["property"].split(" ")[0] in ("trajectory", "drift", "transition", "unit")):
            r["void"] = f"measured units {r['units_measured']} < {minimum['theta_and_length_units']}"
    return rows


def main() -> int:
    p = stage_parser(__doc__, "s5_fidelity")
    p.add_argument("--workers", type=int, default=12)
    p.add_argument("--datasets", nargs="*", default=list(PROFILES))
    p.add_argument("--max-windows-per-unit", type=int, default=100)
    args = p.parse_args()
    ctx = StageContext.from_args(args)
    decl, dd = ctx.declarations, ctx.declarations["declared_by_design"]
    if args.dry_run:
        print("plan: discriminator, TS2Vec FID, covariance, TSTR, property table per profile")
        return 0
    from degradx.viz import s5 as viz

    out, ct = ctx.out_dir, CheckTable()
    L = int(dd["target"]["window_length_L"]["value"])
    gen_seeds, model_seeds = dd["statistics"]["seeds"]["generation"], dd["statistics"]["seeds"]["model_init"]
    minimum = dd["minimum_counts"]["value"]
    lstm_cfg = yaml.safe_load((CONFIG_DIR / "models" / "lstm.yaml").read_text())
    rule = CleaningRule("D12", **dd["capacity_series"]["cleaning_rule"]["params"])
    crule = ChannelRule(float(dd["channel_series"]["cleaning_rule"]["frac"]))
    results = {}
    with RunRecord("s5_fidelity", out, {"config": ctx.config, "datasets": args.datasets, "max_windows_per_unit": args.max_windows_per_unit},
                   {"generation": gen_seeds, "model_init": model_seeds, "evaluation": args.seed}, ctx.device) as rec:
        for ds in args.datasets:
            prof = json.loads((ARTIFACTS_DIR / "s3_fit_profiles" / "profiles" / f"{ds}.json").read_text())
            chans = prof["declared_used"]["channels_available"]
            q_nom = float(load_yaml(CONFIG_DIR / "profiles" / f"{PROFILES[ds]}.yaml")["nominal_capacity_Ah"]["value"])
            spec = spec_from_declarations(decl, q_nom)
            split = pd.read_csv(ARTIFACTS_DIR / "s3_fit_profiles" / "tables" / f"split_{ds}.csv")
            df = pd.read_csv(DATA_DIR / "processed" / "cycle_tables" / f"{ds}.csv.gz", low_memory=False)
            fit_u = prepare_units(df, split.loc[split["split"] == "fitting", "cell_id"], q_nom, spec, rule, chans, crule)
            ho_u = prepare_units(df, split.loc[split["split"] == "held_out", "cell_id"], q_nom, spec, rule, chans, crule)
            ms_fit, ms_ho = F.measured_series(fit_u, chans), F.measured_series(ho_u, chans)
            n_ho, n_ho_reach = len(ms_ho), sum(s.T is not None for s in ms_ho)
            gens = {g: pickle.loads((DATA_DIR / "generated" / ds / f"seed{g}.pkl").read_bytes())[0] for g in gen_seeds}
            res = {"window_length": L, "channels": chans, "units": {"measured_fitting": len(ms_fit), "measured_held_out": n_ho,
                                                                     "measured_held_out_reaching_eol": n_ho_reach, "generated_per_seed": len(gens[gen_seeds[0]])}}
            # ---- distributional measures
            with rec.section(f"{ds}_distributional"):
                Wf, Uf, _ = F.windows(ms_fit, L, max_per_unit=args.max_windows_per_unit, seed=args.seed)
                Wh, Uh, _ = F.windows(ms_ho, L, max_per_unit=args.max_windows_per_unit, seed=args.seed)
                flat = Wf.reshape(-1, Wf.shape[-1])
                mu, sd = flat.mean(axis=0), np.where(flat.std(axis=0) > 0, flat.std(axis=0), 1.0)
                enc, enc_loss = F.train_encoder(Wf, mu, sd, seed=args.seed, device=ctx.device)
                rep_h = F.encode(enc, Wh, mu, sd)
                g_fit = np.random.default_rng(args.seed)
                rep_f = F.encode(enc, Wf[g_fit.choice(len(Wf), size=min(len(Wf), len(Wh)), replace=False)], mu, sd)
                C_h, C_f = F.channel_correlation(Wh, mu, sd), F.channel_correlation(Wf, mu, sd)
                res["baseline_measured_fitting_vs_held_out"] = {"frechet_ts2vec": F.frechet_distance(rep_f, rep_h), **{f"cov_{k}": v for k, v in F.covariance_agreement(C_h, C_f).items()},
                                                                "windows": {"fitting": int(len(rep_f)), "held_out": int(len(rep_h))}}
                res["encoder_final_loss"] = float(enc_loss[-1]) if enc_loss else None
                per_seed = []
                for g, units in gens.items():
                    gs = F.generated_series(units, len(chans))
                    Wg, Ug, _ = F.windows(gs, L, max_per_unit=args.max_windows_per_unit, seed=args.seed + g)
                    disc = F.discriminative_score(Wh, Uh, Wg, Ug, mu, sd, seed=args.seed + g, device=ctx.device)
                    rep_g = F.encode(enc, Wg[np.random.default_rng(g).choice(len(Wg), size=min(len(Wg), len(Wh)), replace=False)], mu, sd)
                    C_g = F.channel_correlation(Wg, mu, sd)
                    entry = {"generation_seed": g, **disc, "frechet_ts2vec": F.frechet_distance(rep_g, rep_h),
                             **{f"cov_{k}": v for k, v in F.covariance_agreement(C_h, C_g).items()}, "generated_windows": int(len(Wg))}
                    if g == gen_seeds[0]:  # D02b: readability of the representation distance at this profile's held-out count
                        bg = np.random.default_rng(args.seed)
                        ho_units = np.unique(Uh)
                        boot = []
                        for _b in range(200):
                            pick = bg.choice(ho_units, size=len(ho_units), replace=True)
                            rows_b = np.concatenate([np.flatnonzero(Uh == u) for u in pick])
                            boot.append(F.frechet_distance(rep_g, rep_h[rows_b]))
                        lo, hi = np.quantile(boot, [0.025, 0.975])
                        entry["frechet_bootstrap_units"] = {"ci_low": float(lo), "ci_high": float(hi), "relative_half_width": float((hi - lo) / 2 / entry["frechet_ts2vec"])}
                    per_seed.append(entry)
                res["per_generation_seed"] = per_seed
                hm = dd["minimum_counts"]["held_out_units_per_measure"]
                errs = np.array([s["discriminative_error"] for s in per_seed])
                half = (errs.max() - errs.min()) / 2
                res["void"] = {
                    "discriminative_error": (f"held-out units {n_ho} < {hm['discriminative_error']['min_units']}" if n_ho < hm["discriminative_error"]["min_units"]
                                             else None),
                    "covariance_agreement": f"held-out units {n_ho} < {hm['covariance_agreement']['min_units']}" if n_ho < hm["covariance_agreement"]["min_units"] else None,
                    "representation_distance": (None if per_seed[0]["frechet_bootstrap_units"]["relative_half_width"] <= 0.5
                                                else f"bootstrap half-width {per_seed[0]['frechet_bootstrap_units']['relative_half_width']:.2f} of the value > 0.5 at {n_ho} held-out units"),
                }
                res["discriminative_error_seed_half_range"] = float(half)
                save_figure(viz.window_embedding(ds, rep_h, F.encode(enc, Wg[:len(Wh)], mu, sd), args.seed), out / "figures" / f"{ds.lower()}_window_embedding_illustration")
            # ---- TSTR
            with rec.section(f"{ds}_tstr"):
                Xm, Um, Rm = F.windows(ms_fit, L, with_rul=True, with_elapsed=True)
                Xh, Uh2, Rh = F.windows(ms_ho, L, with_rul=True, with_elapsed=True)
                n_train_units = sum(s.T is not None for s in ms_fit)
                sse_trtr, sse_tstr, runs = [], [], []
                for ms in model_seeds:
                    m = train_regressor(Xm, Rm, Um, seed=ms, device=ctx.device, cfg=lstm_cfg)
                    units_h, sse, nh = F.per_unit_sse(m.predict(Xh), Rh, Uh2)
                    sse_trtr.append(sse)
                    runs.append({"model": "TRTR", "generation_seed": None, "model_seed": ms, "rmse": float(np.sqrt(sse.sum() / nh.sum())), "epochs": m.history["epochs"]})
                for g, units in gens.items():
                    gs = F.generated_series(units[:n_train_units], len(chans))
                    Xg, Ug, Rg = F.windows(gs, L, with_rul=True, with_elapsed=True)
                    for ms in model_seeds:
                        m = train_regressor(Xg, Rg, Ug, seed=ms, device=ctx.device, cfg=lstm_cfg)
                        _, sse, nh = F.per_unit_sse(m.predict(Xh), Rh, Uh2)
                        sse_tstr.append(sse)
                        runs.append({"model": "TSTR", "generation_seed": g, "model_seed": ms, "rmse": float(np.sqrt(sse.sum() / nh.sum())), "epochs": m.history["epochs"]})
                a, b = np.mean(sse_tstr, axis=0), np.mean(sse_trtr, axis=0)
                res["tstr"] = {**F.ratio_bootstrap(a, b, nh, seed=args.seed, n_resamples=int(dd["statistics"]["bootstrap"]["n_resamples"])),
                               "rmse_tstr_cycles": float(np.sqrt(a.sum() / nh.sum())), "rmse_trtr_cycles": float(np.sqrt(b.sum() / nh.sum())),
                               "held_out_units": int(len(nh)), "held_out_windows": int(nh.sum()), "training_units_each": n_train_units,
                               "runs": runs,
                               "void": (f"held-out units reaching EOL {len(nh)} < {dd['minimum_counts']['held_out_units_per_measure']['transfer_ratio']['min_units_reaching_eol']}"
                                        if len(nh) < dd["minimum_counts"]["held_out_units_per_measure"]["transfer_ratio"]["min_units_reaching_eol"] else None)}
                ratios_by_run = [r["rmse"] for r in runs if r["model"] == "TSTR"]
                res["tstr"]["ratio_spread"] = {"min": float(np.min(ratios_by_run) / np.mean([r["rmse"] for r in runs if r["model"] == "TRTR"])),
                                               "max": float(np.max(ratios_by_run) / np.mean([r["rmse"] for r in runs if r["model"] == "TRTR"]))}
                save_table(pd.DataFrame(runs), out / "tables" / f"tstr_runs_{ds}")
            # ---- property table
            with rec.section(f"{ds}_properties"):
                ho_split = split[split["split"] == "held_out"].assign(split="fitting")
                meas_prof, _ = fit_profile(df, ho_split, dataset=ds, q_nom=q_nom, spec=spec, rule=rule, channels=chans, crule=crule, decl=decl,
                                           workers=args.workers, k=2.5, m=2, sweep_k=[2.5], base_seed=args.seed)
                gdf = generated_frame(gens[gen_seeds[0]], chans)
                gsplit = pd.DataFrame({"cell_id": gdf["cell_id"].unique(), "split": "fitting", "reaches_eol": True})
                gen_spec = spec_from_declarations(decl, q_nom, measured=False)
                gen_prof, _ = fit_profile(gdf, gsplit, dataset=ds, q_nom=q_nom, spec=gen_spec, rule=rule, channels=chans, crule=crule, decl=decl,
                                          workers=args.workers, k=2.5, m=2, sweep_k=[2.5], base_seed=args.seed)
                meas_prof["_profile_enabled"] = {t: v["enabled"] for t, v in prof["estimated_from_data"]["E6_patterns"].items()}
                rows = property_table(ds, meas_prof, gen_prof, q_nom, spec.rho, minimum)
                write_json(rows, out / "tables" / f"properties_{ds}.json")
                res["properties_file"] = f"tables/properties_{ds}.json"
                save_figure(viz.property_distributions(ds, meas_prof, gen_prof, q_nom, spec.rho), out / "figures" / f"{ds.lower()}_property_distributions")
            results[ds] = res
            write_json(results, out / "tables" / "fidelity.json")
            # checks
            ct.require(f"{ds}: window length and effective unit counts recorded next to every measure", all(k in res["units"] for k in ("measured_held_out", "generated_per_seed")), "recorded", res["units"])
            disc_acc = np.mean([s["accuracy"] for s in res["per_generation_seed"]])
            ct.require(f"{ds}: discriminator does not separate trivially (accuracy < 0.99; else look for a scaling/padding artefact)", disc_acc < 0.99, "< 0.99", f"{disc_acc:.3f}", severity="warn")
            ct.require(f"{ds}: TSTR ratio finite with interval", np.isfinite(res["tstr"]["ratio"]), "finite", res["tstr"]["ratio"])
        save_figure(viz.tstr_ratios(results), out / "figures" / "tstr_error_ratio")
        save_figure(viz.discriminator(results), out / "figures" / "discriminative_score")
        code = ct.finalize(out)
        (out / "logs" / "checks.md").write_text(ct.markdown() + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
