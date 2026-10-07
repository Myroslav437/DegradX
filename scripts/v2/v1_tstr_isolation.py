#!/usr/bin/env python
"""V1 (brief "DegradX v2", X1) — TSTR isolation ablation on the v1 profiles; no generator change.

Question: is MATR's TSTR gap (v1 ratio 3.42) caused by per-cell structure in the non-capacity channels, or by the missing
initial-capacity spread? Declarations r3 ``declared_by_design.v2.tstr_isolation`` (declared before this script ran).

Re-runs S5's TSTR and TRTR (v1 profile, v1 generated units of generation seeds 0-2, model seeds 0-4, the S3 held-out
units reaching EOL) with three input sets:
  full               all measured channels + elapsed position (S5 as run in v1; reproduces v1's ratio)
  capacity_only      capacity + elapsed position
  capacity_relative  capacity / q1_i + elapsed position, q1_i the unit's own early-life reference (S3 estimator on the
                     unit's own capacity series, measured and generated alike)
Readings (declared): per-cell structure supported iff the paired BCa interval of log(ratio_full) - log(ratio_capacity_only)
lies above 0; the missing initial-capacity spread contributes iff that of log(ratio_capacity_only) -
log(ratio_capacity_relative) lies above 0. HUST is the control. Sensitivity (D27, decided at this stage after inspecting
the held-out cells): ``full_D27`` repeats the full input set with the measured fitting and held-out series cleaned by the
extended channel rule (runs of up to three departing positions). Outputs in ``artifacts/v2/v1_tstr_isolation``.
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
from degradx.fitting.profile import ChannelRule, prepare_units
from degradx.generator.state import spec_from_declarations, unit_state
from degradx.metrics import fidelity as F
from degradx.models.lstm import train_regressor
from degradx.utils.checks import CheckTable
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.config import load_yaml
from degradx.utils.io import save_table, write_json
from degradx.utils.provenance import RunRecord

PROFILES = {"MATR": "matr", "HUST": "hust"}
INPUT_SETS = ("full", "capacity_only", "capacity_relative", "capacity_state", "full_centred", "full_D27")
# readings (declared): per_cell_structure (full vs capacity_only), initial_capacity_spread (capacity_only vs capacity_relative),
# offsets_specifically (full vs full_centred). Reported variants: capacity_state. Descriptive: full_D27 and its contrasts,
# and the influence row leaving out the held-out unit MATR_b1c2.
READINGS = {"per_cell_structure": ("full", "capacity_only"), "initial_capacity_spread": ("capacity_only", "capacity_relative"),
            "offsets_specifically": ("full", "full_centred")}
DESCRIPTIVE = {"full_vs_capacity_relative": ("full", "capacity_relative"), "full_vs_capacity_state": ("full", "capacity_state"),
               "capacity_only_vs_capacity_state": ("capacity_only", "capacity_state"),
               "sensitivity_D27_per_cell_structure": ("full_D27", "capacity_only"), "sensitivity_full_vs_full_D27": ("full", "full_D27")}
INFLUENCE_UNIT = "MATR_b1c2"


def q1_of(series: list[F.SeriesUnit], spec) -> np.ndarray:
    """Robust early-life reference of each unit from its own capacity column (declarations eol.q1_reference)."""
    return np.array([unit_state(s.X[:, 0], spec).q1 for s in series])


def restrict(X: np.ndarray, U: np.ndarray, q1: np.ndarray, which: str, rho_qnom: float, early_median: np.ndarray | None = None) -> np.ndarray:
    """X: (N, L, C + 1) windows with the elapsed position last; U: series index of each window; q1: per-series early-life
    reference; early_median: (n_series, C) per-series median of each channel over positions 1..k (full_centred)."""
    if which == "full":
        return X
    if which == "full_centred":
        Xc = X.copy()
        Xc[:, :, 1:-1] = X[:, :, 1:-1] - early_median[U][:, None, 1:]
        return Xc
    cap = X[:, :, :1]
    if which == "capacity_relative":
        cap = cap / q1[U][:, None, None]
    elif which == "capacity_state":
        cap = (q1[U][:, None, None] - cap) / (q1[U][:, None, None] - rho_qnom)
    return np.concatenate([cap, X[:, :, -1:]], axis=2)


def early_medians(series: list[F.SeriesUnit], k: int) -> np.ndarray:
    return np.array([np.nanmedian(s.X[:k], axis=0) for s in series])


def ratio_tests(runs_sse: dict, nh: np.ndarray, pairs: dict, seed: int, n_boot: int, keep_units=None, drop: dict | None = None) -> dict:
    """Paired log-ratio bootstraps for the given input-set pairs. runs_sse[which] = {"TSTR": {(g, ms): sse}, "TRTR": {ms: sse}};
    ``drop`` removes a generation seed ('g') or a model seed ('ms', from TSTR and TRTR together); ``keep_units`` restricts the
    held-out units (influence row)."""
    def agg(which):
        t = [v for (g, ms), v in runs_sse[which]["TSTR"].items() if not (drop and (drop.get("g") == g or drop.get("ms") == ms))]
        r = [v for ms, v in runs_sse[which]["TRTR"].items() if not (drop and drop.get("ms") == ms)]
        a, b = np.mean(t, axis=0), np.mean(r, axis=0)
        return (a[keep_units], b[keep_units]) if keep_units is not None else (a, b)
    n = nh[keep_units] if keep_units is not None else nh
    return {name: F.log_ratio_difference_bootstrap(agg(x), agg(y), n, seed=seed, n_resamples=n_boot) for name, (x, y) in pairs.items()}


def main() -> int:
    p = stage_parser(__doc__, "v2/v1_tstr_isolation")
    p.add_argument("--datasets", nargs="*", default=list(PROFILES))
    args = p.parse_args()
    ctx = StageContext.from_args(args)
    decl, dd = ctx.declarations, ctx.declarations["declared_by_design"]
    if args.dry_run:
        print(f"plan: TSTR/TRTR x {INPUT_SETS} for {args.datasets}")
        return 0
    out, ct = ctx.out_dir, CheckTable()
    L = int(dd["target"]["window_length_L"]["value"])
    k = int(dd["eol"]["q1_reference"]["k"])
    gen_seeds, model_seeds = dd["statistics"]["seeds"]["generation"], dd["statistics"]["seeds"]["model_init"]
    n_boot = int(dd["statistics"]["bootstrap"]["n_resamples"])
    lstm_cfg = yaml.safe_load((CONFIG_DIR / "models" / "lstm.yaml").read_text())
    rule = CleaningRule("D12", **dd["capacity_series"]["cleaning_rule"]["params"])
    crule = ChannelRule(float(dd["channel_series"]["cleaning_rule"]["frac"]))
    v1 = json.loads((ARTIFACTS_DIR / "s5_fidelity" / "tables" / "fidelity.json").read_text())
    results = {}
    with RunRecord("v2/v1_tstr_isolation", out, {"config": ctx.config, "datasets": args.datasets, "input_sets": list(INPUT_SETS)},
                   {"generation": gen_seeds, "model_init": model_seeds, "evaluation": args.seed}, ctx.device) as rec:
        for ds in args.datasets:
            prof = json.loads((ARTIFACTS_DIR / "s3_fit_profiles" / "profiles" / f"{ds}.json").read_text())
            chans = prof["declared_used"]["channels_available"]
            q_nom = float(load_yaml(CONFIG_DIR / "profiles" / f"{PROFILES[ds]}.yaml")["nominal_capacity_Ah"]["value"])
            spec = spec_from_declarations(decl, q_nom)
            spec_q1 = spec_from_declarations(decl, q_nom, measured=False)  # q1 only: the record-end rule does not enter
            split = pd.read_csv(ARTIFACTS_DIR / "s3_fit_profiles" / "tables" / f"split_{ds}.csv")
            df = pd.read_csv(DATA_DIR / "processed" / "cycle_tables" / f"{ds}.csv.gz", low_memory=False)
            fit_u = prepare_units(df, split.loc[split["split"] == "fitting", "cell_id"], q_nom, spec, rule, chans, crule)
            ho_u = prepare_units(df, split.loc[split["split"] == "held_out", "cell_id"], q_nom, spec, rule, chans, crule)
            ms_fit, ms_ho = F.measured_series(fit_u, chans), F.measured_series(ho_u, chans)
            crule27 = ChannelRule(float(dd["channel_series"]["cleaning_rule"]["frac"]), int(dd["channel_series"]["cleaning_rule"]["max_run_v2"]))
            fit27 = F.measured_series(prepare_units(df, split.loc[split["split"] == "fitting", "cell_id"], q_nom, spec, rule, chans, crule27), chans)
            ho27 = F.measured_series(prepare_units(df, split.loc[split["split"] == "held_out", "cell_id"], q_nom, spec, rule, chans, crule27), chans)
            assert [s.unit_id for s in fit27] == [s.unit_id for s in ms_fit] and [s.unit_id for s in ho27] == [s.unit_id for s in ms_ho]
            Xm27, Um27, Rm27 = F.windows(fit27, L, with_rul=True, with_elapsed=True)
            Xh27, Uh27, Rh27 = F.windows(ho27, L, with_rul=True, with_elapsed=True)
            assert np.array_equal(Uh27, F.windows(ms_ho, L, with_rul=True, with_elapsed=True)[1])
            n_train_units = sum(s.T is not None for s in ms_fit)
            gens = {g: pickle.loads((DATA_DIR / "generated" / ds / f"seed{g}.pkl").read_bytes())[0] for g in gen_seeds}
            q1_fit, q1_ho = q1_of(ms_fit, spec_q1), q1_of(ms_ho, spec_q1)
            em_fit, em_ho = early_medians(ms_fit, k), early_medians(ms_ho, k)
            rho_qnom = spec.rho * spec.q_nom
            Xm, Um, Rm = F.windows(ms_fit, L, with_rul=True, with_elapsed=True)
            Xh, Uh, Rh = F.windows(ms_ho, L, with_rul=True, with_elapsed=True)
            ends_h = Xh[:, -1, -1]
            gen_w = {}
            for g, units in gens.items():
                gs = F.generated_series(units[:n_train_units], len(chans))
                Xg, Ug, Rg = F.windows(gs, L, with_rul=True, with_elapsed=True)
                gen_w[g] = (Xg, Ug, Rg, q1_of(gs, spec_q1), early_medians(gs, k))
            res = {"channels": chans, "window_length": L, "k": k, "held_out_windows_min_end": int(ends_h.min()),
                   "windows_ending_before_k": int(np.sum(ends_h < k)), "training_units_each": n_train_units,
                   "q1_spread": {"measured_fitting": {"median": float(np.median(q1_fit)), "iqr": float(np.subtract(*np.percentile(q1_fit, [75, 25]))),
                                                      "p05_p95": np.percentile(q1_fit, [5, 95]).tolist()},
                                 "measured_held_out": {"median": float(np.median(q1_ho)), "iqr": float(np.subtract(*np.percentile(q1_ho, [75, 25]))),
                                                       "p05_p95": np.percentile(q1_ho, [5, 95]).tolist()},
                                 "generated_seed0": {"median": float(np.median(gen_w[gen_seeds[0]][3])),
                                                     "iqr": float(np.subtract(*np.percentile(gen_w[gen_seeds[0]][3], [75, 25]))),
                                                     "p05_p95": np.percentile(gen_w[gen_seeds[0]][3], [5, 95]).tolist()}},
                   "input_sets": {}}
            sse, runs_sse = {}, {}
            for which in INPUT_SETS:
                with rec.section(f"{ds}_{which}"):
                    if which == "full_D27":
                        Xh_r, Xm_r = Xh27, Xm27
                    else:
                        Xh_r = restrict(Xh, Uh, q1_ho, which, rho_qnom, em_ho)
                        Xm_r = restrict(Xm, Um, q1_fit, which, rho_qnom, em_fit)
                    sse_trtr, sse_tstr, runs = [], [], []
                    runs_sse[which] = {"TSTR": {}, "TRTR": {}}
                    for ms in model_seeds:
                        m = train_regressor(Xm_r, Rm, Um, seed=ms, device=ctx.device, cfg=lstm_cfg)
                        units_h, s_, nh = F.per_unit_sse(m.predict(Xh_r), Rh, Uh)
                        sse_trtr.append(s_)
                        runs_sse[which]["TRTR"][ms] = s_
                        runs.append({"model": "TRTR", "generation_seed": None, "model_seed": ms, "rmse": float(np.sqrt(s_.sum() / nh.sum())), "epochs": m.history["epochs"]})
                    for g, (Xg, Ug, Rg, q1g, emg) in gen_w.items():
                        Xg_r = Xg if which == "full_D27" else restrict(Xg, Ug, q1g, which, rho_qnom, emg)
                        for ms in model_seeds:
                            m = train_regressor(Xg_r, Rg, Ug, seed=ms, device=ctx.device, cfg=lstm_cfg)
                            _, s_, nh = F.per_unit_sse(m.predict(Xh_r), Rh, Uh)
                            sse_tstr.append(s_)
                            runs_sse[which]["TSTR"][(g, ms)] = s_
                            runs.append({"model": "TSTR", "generation_seed": g, "model_seed": ms, "rmse": float(np.sqrt(s_.sum() / nh.sum())), "epochs": m.history["epochs"]})
                    a, b = np.mean(sse_tstr, axis=0), np.mean(sse_trtr, axis=0)
                    sse[which] = (a, b)
                    trtr_mean = np.mean([r["rmse"] for r in runs if r["model"] == "TRTR"])
                    res["input_sets"][which] = {**F.ratio_bootstrap(a, b, nh, seed=args.seed, n_resamples=n_boot),
                                                "rmse_tstr_cycles": float(np.sqrt(a.sum() / nh.sum())), "rmse_trtr_cycles": float(np.sqrt(b.sum() / nh.sum())),
                                                "held_out_units": int(len(nh)), "held_out_windows": int(nh.sum()), "n_inputs": int(Xh_r.shape[-1]),
                                                "ratio_spread_over_tstr_runs": {"min": float(min(r["rmse"] for r in runs if r["model"] == "TSTR") / trtr_mean),
                                                                                "max": float(max(r["rmse"] for r in runs if r["model"] == "TSTR") / trtr_mean)},
                                                "runs": runs}
                    save_table(pd.DataFrame(runs), out / "tables" / f"runs_{ds}_{which}")
                    print(f"[v1] {ds} {which}: ratio {res['input_sets'][which]['ratio']:.3f} "
                          f"[{res['input_sets'][which]['ci_low']:.3f}, {res['input_sets'][which]['ci_high']:.3f}]", flush=True)
            res["held_out_unit_ids"] = [ms_ho[i].unit_id for i in units_h]
            res["tests"] = ratio_tests(runs_sse, nh, READINGS, args.seed, n_boot)
            res["descriptive"] = ratio_tests(runs_sse, nh, DESCRIPTIVE, args.seed, n_boot)
            # robustness (declared): leave one generation seed / one model seed out; a reading holds only if its interval stays
            # on the same side of 0 in every leave-one-out
            loo = {}
            for g in gen_seeds:
                loo[f"without_generation_seed_{g}"] = ratio_tests(runs_sse, nh, READINGS, args.seed, n_boot, drop={"g": g})
            for ms in model_seeds:
                loo[f"without_model_seed_{ms}"] = ratio_tests(runs_sse, nh, READINGS, args.seed, n_boot, drop={"ms": ms})
            res["leave_one_out"] = loo
            res["readings"] = {}
            for name in READINGS:
                full_t = res["tests"][name]
                side = full_t["ci_low"] > 0
                same = all((l[name]["ci_low"] > 0) == side and (side or l[name]["ci_high"] >= 0) for l in loo.values())
                res["readings"][name] = {"interval_above_zero": bool(full_t["ci_low"] > 0), "robust_to_leave_one_out": bool(same),
                                         "holds": bool(full_t["ci_low"] > 0 and all(l[name]["ci_low"] > 0 for l in loo.values()))}
            # influence row (descriptive): leave out the held-out unit behind the v1 charge-time variance
            ids = res["held_out_unit_ids"]
            if INFLUENCE_UNIT in ids:
                keep = np.array([u != INFLUENCE_UNIT for u in ids])
                res["influence_without_" + INFLUENCE_UNIT] = {
                    "tests": ratio_tests(runs_sse, nh, {**READINGS, **DESCRIPTIVE}, args.seed, n_boot, keep_units=keep),
                    "ratios": {w: float(np.sqrt(np.mean(list(runs_sse[w]["TSTR"].values()), axis=0)[keep].sum() / nh[keep].sum())
                                        / np.sqrt(np.mean(list(runs_sse[w]["TRTR"].values()), axis=0)[keep].sum() / nh[keep].sum())) for w in INPUT_SETS}}
            np.savez_compressed(out / "tables" / f"per_unit_sse_{ds}.npz", units=np.array(ids), n_windows=nh,
                                **{f"{w}__TSTR__g{g}_m{ms}": v for w in INPUT_SETS for (g, ms), v in runs_sse[w]["TSTR"].items()},
                                **{f"{w}__TRTR__m{ms}": v for w in INPUT_SETS for ms, v in runs_sse[w]["TRTR"].items()})
            v1r = v1[ds]["tstr"]
            res["v1_reproduction"] = {"v1_ratio": v1r["ratio"], "v2_full_ratio": res["input_sets"]["full"]["ratio"],
                                      "abs_diff": abs(v1r["ratio"] - res["input_sets"]["full"]["ratio"]),
                                      "v1_rmse_tstr": v1r["rmse_tstr_cycles"], "v1_rmse_trtr": v1r["rmse_trtr_cycles"]}
            results[ds] = res
            write_json(results, out / "tables" / "tstr_isolation.json")
            ct.require(f"{ds}: the full input set reproduces v1's TSTR ratio (S5, same seeds and units)", res["v1_reproduction"]["abs_diff"] < 1e-6,
                       f"{v1r['ratio']:.6f}", f"{res['input_sets']['full']['ratio']:.6f}", severity="warn")
            ct.require(f"{ds}: held-out units reaching EOL >= 20 (D02b transfer minimum)", res["input_sets"]["full"]["held_out_units"] >= 20, ">= 20",
                       res["input_sets"]["full"]["held_out_units"], severity="warn")
            ct.require(f"{ds}: every scored window ends at or after k = {k}", res["windows_ending_before_k"] == 0, "0", res["windows_ending_before_k"])
        code = ct.finalize(out)
        (out / "logs" / "checks.md").write_text(ct.markdown() + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
