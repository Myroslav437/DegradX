#!/usr/bin/env python
"""S4 — generator and attribution ground truth (paper §3.1-3.2; Eq. 1-6 as amended by C1-C4).

Inputs: S3 profiles (``artifacts/s3_fit_profiles/profiles/<dataset>.json`` and split tables) and the S1 cycle tables (for the
null_permuted pool: fitting-split charge-time readings after D17). For every profile and generation seed in the declared
list, generates the declared number of units, splits them 0.7/0.15/0.15 at unit level (seed stream 'split'), and caches
them under ``data/generated/<profile>/seed<g>.pkl`` (gitignored; regenerated bit-identically from the seeds). Verifies the
construction checks of declarations target.s4_acceptance_checks on every window under all three weightings, runs the
rho-sensitivity refit over the declared grid under both EOL definitions, and draws paper Figures 2, 3, 4 on generated units
and the generated-vs-measured overlay (paper Figure 6). Outputs in ``artifacts/s4_generate_units``.
"""

from __future__ import annotations

import json
import pickle
import sys

import numpy as np
import pandas as pd

from degradx import CONFIG_DIR, DATA_DIR
from degradx.data.audit import CleaningRule, clean_capacity
from degradx.fitting.profile import ChannelRule, fit_profile, prepare_units
from degradx.generator.generate import Profile, generate_unit
from degradx.generator.state import StateSpec, spec_from_declarations
from degradx.targets.decomposable import WEIGHTINGS, TargetSpec, unit_targets
from degradx.utils.checks import CheckTable
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.config import load_yaml
from degradx.utils.io import save_figure, save_table, write_json
from degradx.utils.provenance import RunRecord
from degradx.utils.seeding import rng

PROFILES = {"MATR": "matr", "HUST": "hust", "NASA_PCoE": "nasa_pcoe"}
S3 = "s3_fit_profiles"


def load_profile(ds: str, decl: dict, artifacts) -> tuple[Profile, dict, float]:
    prof = json.loads((artifacts / S3 / "profiles" / f"{ds}.json").read_text())
    q_nom = float(load_yaml(CONFIG_DIR / "profiles" / f"{PROFILES[ds]}.yaml")["nominal_capacity_Ah"]["value"])
    split = pd.read_csv(artifacts / S3 / "tables" / f"split_{ds}.csv")
    df = pd.read_csv(DATA_DIR / "processed" / "cycle_tables" / f"{ds}.csv.gz", low_memory=False)
    dd = decl["declared_by_design"]
    units = prepare_units(df, split.loc[split["split"] == "fitting", "cell_id"], q_nom, spec_from_declarations(decl, q_nom),
                          CleaningRule("D12", **dd["capacity_series"]["cleaning_rule"]["params"]), ["capacity", "charge_time"],
                          ChannelRule(float(dd["channel_series"]["cleaning_rule"]["frac"])))
    pool = np.concatenate([u.channels["charge_time"][u.fit_start - 1:u.fit_end] for u in units])
    return Profile.from_json(prof, pool[np.isfinite(pool)]), prof, q_nom


def generate_set(P: Profile, gen_seed: int, n_units: int, base_seed: int) -> tuple[list, pd.DataFrame]:
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
                          "n_patterns": [len(u.patterns) for u in units], "split": split})
    return units, table


def construction_checks(ds, P, units, spec: TargetSpec, ct: CheckTable, gen_seed: int) -> dict:
    out = {}
    L = spec.L
    long_units = [u for u in units if u.T >= L]
    for kind in WEIGHTINGS:
        e_sum, e_ref, n_win = 0.0, 0.0, 0
        unit_mean_gy, corr_g, corr_s = [], [], []
        collapse = 0.0
        for u in long_units:
            tg = unit_targets(u, spec, kind)
            e_sum = max(e_sum, float(np.max(np.abs(tg["phi_star"].sum(axis=(1, 2)) - tg["y"]) / np.maximum(1.0, np.abs(tg["y"])))))
            e_ref = max(e_ref, float(np.max(np.abs((tg["g"] - tg["y"]) - tg["noise_term"]))))
            unit_mean_gy.append(float(np.mean(tg["g"] - tg["y"])))
            n_win += len(tg["y"])
            if kind == "final_position":
                collapse = max(collapse, float(np.abs(tg["phi_star"][:, :-1, :]).max()))
            corr_g.append(np.abs(tg["graded"]).sum(axis=2).ravel())
            corr_s.append(np.abs(tg["sparse"]).sum(axis=2).ravel())
        ct.require(f"{ds} seed {gen_seed} [{kind}]: sum(phi*) == y on every window", e_sum < 1e-9, "< 1e-9 (relative)", f"{e_sum:.2e} over {n_win} windows")
        ct.require(f"{ds} seed {gen_seed} [{kind}]: g(x) - y == sum(w eps) on every window", e_ref < 1e-9, "< 1e-9", f"{e_ref:.2e}")
        mu, se = float(np.mean(unit_mean_gy)), float(np.std(unit_mean_gy, ddof=1) / np.sqrt(len(unit_mean_gy)))
        ct.require(f"{ds} seed {gen_seed} [{kind}]: mean over units of g(x) - y ~ 0", abs(mu) <= 3 * se, "|mean| <= 3 SE", f"mean {mu:.3e}, SE {se:.3e}")
        if kind == "final_position":
            ct.require(f"{ds} seed {gen_seed}: final-position weighting collapses graded and sparse fields to the last position", collapse == 0.0, "0 outside last", collapse)
        G, S = np.concatenate(corr_g), np.concatenate(corr_s)
        has_sparse = bool(np.any(S > 0))
        r = float(np.corrcoef(G, S)[0, 1]) if has_sparse and np.std(S) > 0 else None
        out[kind] = {"windows": n_win, "graded_sparse_abs_corr": r, "has_sparse": has_sparse, "g_minus_y_unit_mean": mu, "se": se}
    # pristine unit: z = 0, no patterns, no noise -> y = 0
    u = long_units[0]
    from copy import deepcopy

    pu = deepcopy(u)
    pu.z[:] = 0.0
    for ci, c in enumerate(P.channels):
        pu.m[:, ci] = P.mappings[c](0.0)
    pu.p[:] = 0.0
    pu.eps[:] = 0.0
    ymax = max(float(np.abs(unit_targets(pu, spec, k)["y"]).max()) for k in WEIGHTINGS)
    ct.require(f"{ds} seed {gen_seed}: pristine unit (z = 0, no patterns, no noise) has y = 0", ymax < 1e-12, "0", f"{ymax:.2e}")
    # E[eps] = 0 per measured channel: t-test over unit means
    for ci, c in enumerate(P.channels):
        means = np.array([np.mean(u.eps[:, ci]) for u in units])
        sd = np.sqrt(P.noise_pooled[c]["variance"])
        mu, se = float(means.mean()), float(means.std(ddof=1) / np.sqrt(len(means)))
        ct.require(f"{ds} seed {gen_seed}: E[eps_{c}] ~ 0", abs(mu) <= 3 * se, "|mean| <= 3 SE over units", f"{mu / sd:+.3f} noise SD (SE {se / sd:.3f})")
    # z runs 0 -> 1 with T the first crossing; patterns leave z, T, R unchanged
    z0 = max(float(u.z[0]) for u in units)
    first = all(u.z[-1] >= 1.0 and (u.T < 2 or u.z[-2] < 1.0) for u in units)
    ct.require(f"{ds} seed {gen_seed}: z starts at the pristine level and T is the first crossing of z = 1", first and z0 <= 0.05, "z_1 <= 0.05; z_T >= 1 > z_{T-1}", f"max z_1 {z0:.3f}; first crossing {first}")
    inv = True
    for u in units[:: max(1, len(units) // 60)]:
        u0 = generate_unit(P, gen_seed, u.index, patterns_on=False)
        inv &= u0.T == u.T and np.array_equal(u0.z, u.z) and np.array_equal(u0.R, u.R) and np.array_equal(u0.eps, u.eps)
    ct.require(f"{ds} seed {gen_seed}: disabling patterns leaves z, T, R and noise unchanged", inv, "identical", inv)
    return out


def rho_sensitivity(ds, decl, workers, base_seed, artifacts) -> pd.DataFrame:
    dd = decl["declared_by_design"]
    q_nom = float(load_yaml(CONFIG_DIR / "profiles" / f"{PROFILES[ds]}.yaml")["nominal_capacity_Ah"]["value"])
    split = pd.read_csv(artifacts / S3 / "tables" / f"split_{ds}.csv")
    df = pd.read_csv(DATA_DIR / "processed" / "cycle_tables" / f"{ds}.csv.gz", low_memory=False)
    prof0 = json.loads((artifacts / S3 / "profiles" / f"{ds}.json").read_text())
    rows = []
    rule = CleaningRule("D12", **dd["capacity_series"]["cleaning_rule"]["params"])
    crule = ChannelRule(float(dd["channel_series"]["cleaning_rule"]["frac"]))
    # all eligible units of the S3 fitting split are refitted; units excluded or censored at a given rho are counted
    for definition in ("nominal_anchor_r2", "first_position_anchor_r1"):
        for rho in dd["eol"]["rho_sensitivity_grid"]["value"]:
            spec = spec_from_declarations(decl, q_nom, rho=float(rho), definition=definition)
            try:
                prof, diag = fit_profile(df, split, dataset=ds, q_nom=q_nom, spec=spec, rule=rule, channels=["capacity", "charge_time"], crule=crule,
                                         decl=decl, workers=workers, k=float(dd["pattern_detection"]["multiple_k"]["value"]),
                                         m=int(dd["pattern_detection"]["min_run_length"]["value"]), sweep_k=[2.5], base_seed=base_seed)
            except (ValueError, KeyError, IndexError) as exc:  # no unit reaches EOL (or passes the guard) at this setting
                rows.append({"dataset": ds, "definition": "r2" if definition == "nominal_anchor_r2" else "r1", "rho": rho,
                             "units_reaching_eol": 0, "family_selected": None, "note": f"not fittable: {type(exc).__name__}"})
                print(f"[rho] {ds} {definition} {rho}: not fittable ({exc!r})", flush=True)
                continue
            e = prof["estimated_from_data"]
            T = np.array(e["E7_length_distribution"], float)
            fam = e["E2_family_choice"]["selected"]
            P = np.array([p["family_params"] for p in e["E1_theta_distribution"]["per_unit"]]) if e["E1_theta_distribution"]["per_unit"] else np.empty((0, 0))
            row = {"dataset": ds, "definition": "r2" if definition == "nominal_anchor_r2" else "r1", "rho": rho,
                   "fitting_units_passing_guard": len(prof["units"]["fitting_passing_guard"]), "units_reaching_eol": int(len(T)),
                   "family_selected": fam, "same_family_as_declared_fit": fam == prof0["estimated_from_data"]["E2_family_choice"]["selected"],
                   "T_median": float(np.median(T)) if len(T) else None, "T_q25": float(np.quantile(T, 0.25)) if len(T) else None,
                   "T_q75": float(np.quantile(T, 0.75)) if len(T) else None,
                   "q1_bar": e["E3_channel_mappings"]["capacity"]["phi0"]}
            for i, nm in enumerate(e["E1_theta_distribution"]["param_names"]):
                row[f"theta_{nm}_median"] = float(np.median(P[:, i])) if len(P) else None
            rows.append(row)
            print(f"[rho] {ds} {row['definition']} {rho}: {row['units_reaching_eol']} units, {fam}, T median {row['T_median']}", flush=True)
    return pd.DataFrame(rows)


def main() -> int:
    p = stage_parser(__doc__, "s4_generate_units")
    p.add_argument("--workers", type=int, default=12)
    p.add_argument("--datasets", nargs="*", default=list(PROFILES))
    p.add_argument("--skip-rho", action="store_true", help="skip the rho-sensitivity refits")
    args = p.parse_args()
    ctx = StageContext.from_args(args)
    decl, dd = ctx.declarations, ctx.declarations["declared_by_design"]
    if args.dry_run:
        print(f"plan: generate {dd['statistics']['generated_units']} for seeds {dd['statistics']['seeds']['generation']['value'] if isinstance(dd['statistics']['seeds']['generation'], dict) else dd['statistics']['seeds']['generation']}")
        return 0
    from degradx import ARTIFACTS_DIR
    from degradx.viz import s4 as viz

    out = ctx.out_dir
    ct = CheckTable()
    gen_seeds = dd["statistics"]["seeds"]["generation"]
    n_units = int(dd["statistics"]["generated_units"]["attribution_and_usability"])
    beta = dd["target"]["weights"]["beta"]["value"]
    L = int(dd["target"]["window_length_L"]["value"])
    summary = {}
    with RunRecord("s4_generate_units", out, {"config": ctx.config, "datasets": args.datasets},
                   {"generation": gen_seeds, "split": f"derive_seed({args.seed}, 'split', <profile>, 'generated', <g>)"}, ctx.device) as rec:
        profiles = {}
        for ds in args.datasets:
            P, prof, q_nom = load_profile(ds, decl, ARTIFACTS_DIR)
            profiles[ds] = (P, prof, q_nom)
            spec = TargetSpec.build(P, beta, L, 6.0)
            summary[ds] = {"kappa": dict(zip(spec.channels, spec.kappa.tolist())), "x0": dict(zip(spec.channels, spec.x0.tolist())), "seeds": {}}
            for gs in gen_seeds:
                cache = DATA_DIR / "generated" / ds / f"seed{gs}.pkl"
                with rec.section(f"{ds}_generate_seed{gs}"):
                    if ctx.should_skip(cache, label=f"{ds} seed {gs} units"):
                        units, table = pickle.loads(cache.read_bytes())
                    else:
                        units, table = generate_set(P, gs, n_units, args.seed)
                        cache.parent.mkdir(parents=True, exist_ok=True)
                        cache.write_bytes(pickle.dumps((units, table), protocol=pickle.HIGHEST_PROTOCOL))
                save_table(table, out / "tables" / f"generated_units_{ds}_seed{gs}")
                with rec.section(f"{ds}_checks_seed{gs}"):
                    res = construction_checks(ds, P, units, spec, ct, gs)
                summary[ds]["seeds"][gs] = {"units": len(units), "T_median": float(table["T"].median()), "T_q25": float(table["T"].quantile(0.25)),
                                            "T_q75": float(table["T"].quantile(0.75)), "units_with_patterns": int((table["n_patterns"] > 0).sum()),
                                            "patterns": int(table["n_patterns"].sum()), "checks": res}
                bound = float(dd["usability"]["graded_sparse_correlation_bound"]["value"])
                for kind, r in res.items():
                    if r["has_sparse"]:
                        ct.require(f"{ds} seed {gs} [{kind}]: |graded|/|sparse| correlation below the declared bound", abs(r["graded_sparse_abs_corr"]) <= bound,
                                   f"<= {bound}", f"{r['graded_sparse_abs_corr']:.3f}", severity="warn")
            with rec.section(f"{ds}_figures"):
                units, table = pickle.loads((DATA_DIR / "generated" / ds / f"seed{gen_seeds[0]}.pkl").read_bytes())
                df = pd.read_csv(DATA_DIR / "processed" / "cycle_tables" / f"{ds}.csv.gz", low_memory=False)
                split = pd.read_csv(ARTIFACTS_DIR / S3 / "tables" / f"split_{ds}.csv")
                save_figure(viz.overlay_measured_generated(ds, P, units, df, split, decl, q_nom), out / "figures" / f"{ds.lower()}_generated_vs_measured")
                save_figure(viz.weightings_check(TargetSpec.build(P, beta, L, 6.0)), out / "figures" / f"{ds.lower()}_weightings_as_implemented")
        # paper-layout figures from real fitted parameters
        if "NASA_PCoE" in profiles:
            P, _, _ = profiles["NASA_PCoE"]
            units, _t = pickle.loads((DATA_DIR / "generated" / "NASA_PCoE" / f"seed{gen_seeds[0]}.pkl").read_bytes())
            save_figure(viz.figure2_layout(P, units, TargetSpec.build(P, beta, L, 6.0)), out / "figures" / "figure2_layout_nasa_pcoe")
        if "MATR" in profiles:
            P, _, _ = profiles["MATR"]
            save_figure(viz.figure3_layout(P), out / "figures" / "figure3_layout_matr")
        write_json(summary, out / "tables" / "summary.json")
        if not args.skip_rho:
            frames = []
            for ds in args.datasets:
                with rec.section(f"{ds}_rho_sensitivity"):
                    frames.append(rho_sensitivity(ds, decl, args.workers, args.seed, ARTIFACTS_DIR))
            rho = pd.concat(frames, ignore_index=True)
            save_table(rho, out / "tables" / "rho_sensitivity")
            save_figure(viz.rho_sensitivity(rho), out / "figures" / "rho_sensitivity")
        code = ct.finalize(out)
        (out / "logs" / "checks.md").write_text(ct.markdown() + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
