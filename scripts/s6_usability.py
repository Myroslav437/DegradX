#!/usr/bin/env python
"""S6 — RQ2, usability of the attribution ground truth (paper §3.5.2 as amended by C2; Table 3).

Inputs: S4 generated units (generation seed 0, declared train/validation/test unit split), S3 profiles. Per profile and
position weighting (recency, uniform, final position):
  * LSTM ensemble on the decomposable target y from windows of all channels (null and redundant channels included, no
    elapsed position): configuration A (hidden 64 x 2) and B (hidden 128 x 1), model seeds 0-4 each; the accuracy gate
    (NRMSE <= 0.30 on test units) applies to every member; member A/seed 0 is the primary model;
  * declared properties of the target: variance ratio of the two terms of Eq. 4 (band), association of y with RUL;
  * graded/sparse field correlation (from the S4 construction checks);
  * term ablation (primary configuration, model seeds 0-2): retrained on each term alone; error on the full y must increase;
  * permutation importance (primary model): null channels gated (upper 95% bound of the NMSE increase <= 0.02);
    redundant zero-weight channels reported with ridge predictability and conditional permutation importance.
Scores on a profile that fails the accuracy gate are void (paper l.277). Trained models go to ``models/`` (Git LFS).
Outputs in ``artifacts/s6_usability``.
"""

from __future__ import annotations

import copy
import json
import pickle
import sys

import numpy as np
import pandas as pd
import torch
import yaml
from scipy.stats import spearmanr

from degradx import ARTIFACTS_DIR, CONFIG_DIR, DATA_DIR
from degradx.generator.generate import Profile
from degradx.metrics import usability as U
from degradx.models.lstm import train_regressor
from degradx.targets.decomposable import WEIGHTINGS, TargetSpec, unit_targets
from degradx.utils.checks import CheckTable
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.io import save_figure, save_table, write_json
from degradx.utils.provenance import RunRecord
from degradx.utils.seeding import rng

PROFILES = ("MATR", "HUST", "NASA_PCoE")
CONFIGS = {"A": {"hidden_size": 64, "num_layers": 2}, "B": {"hidden_size": 128, "num_layers": 1}}


def build_windows(units, spec, kind, stride: int = 1):
    Xs, ys, gs, ss, us, zs, Rs = [], [], [], [], [], [], []
    for i, u in enumerate(units):
        if u.T < spec.L:
            continue
        ends = np.arange(spec.L, u.T + 1, stride)
        tg = unit_targets(u, spec, kind, ends=ends)
        Xs.append(tg["x"]); ys.append(tg["y"])
        gs.append(tg["graded"].sum(axis=(1, 2))); ss.append(tg["sparse"].sum(axis=(1, 2)))
        us.append(np.full(len(ends), i)); zs.append(tg["z_end"]); Rs.append(tg["R"])
    cat = lambda a: np.concatenate(a) if a else np.empty(0)  # noqa: E731
    return {"X": np.concatenate(Xs).astype(np.float32), "y": cat(ys), "graded_sum": cat(gs), "sparse_sum": cat(ss), "unit": cat(us).astype(int),
            "z_end": cat(zs), "R": cat(Rs)}


def main() -> int:
    p = stage_parser(__doc__, "s6_usability")
    p.add_argument("--datasets", nargs="*", default=list(PROFILES))
    p.add_argument("--weightings", nargs="*", default=list(WEIGHTINGS))
    p.add_argument("--train-stride", type=int, default=1, help="window stride for training windows (test windows always stride 1)")
    args = p.parse_args()
    ctx = StageContext.from_args(args)
    decl, dd = ctx.declarations, ctx.declarations["declared_by_design"]
    if args.dry_run:
        print("plan: ensemble x weightings x profiles; gate, properties, ablation, permutation importance")
        return 0
    from degradx.viz import s6 as viz

    out, ct = ctx.out_dir, CheckTable()
    (out / "models").mkdir(parents=True, exist_ok=True)
    base_cfg = yaml.safe_load((CONFIG_DIR / "models" / "lstm.yaml").read_text())
    gate = 0.30
    null_tol = 0.02
    band = dd["usability"]["variance_ratio_band"]["value"]
    corr_bound = float(dd["usability"]["graded_sparse_correlation_bound"]["value"])
    beta = dd["target"]["weights"]["beta"]["value"]
    L = int(dd["target"]["window_length_L"]["value"])
    s4 = json.loads((ARTIFACTS_DIR / "s4_generate_units" / "tables" / "summary.json").read_text())
    results = {}
    with RunRecord("s6_usability", out, {"config": ctx.config, "datasets": args.datasets, "weightings": args.weightings, "train_stride": args.train_stride},
                   {"generation": 0, "model_init": list(range(5)), "evaluation": args.seed}, ctx.device) as rec:
        for ds in args.datasets:
            prof = json.loads((ARTIFACTS_DIR / "s3_fit_profiles" / "profiles" / f"{ds}.json").read_text())
            units, table = pickle.loads((DATA_DIR / "generated" / ds / "seed0.pkl").read_bytes())
            P = Profile.from_json(prof, np.array([0.0]))  # null pool not needed: units are generated already
            spec = TargetSpec.build(P, beta, L, 6.0)
            split = dict(zip(table["index"], table["split"]))
            by_split = {s: [u for u in units if split[u.index] == s] for s in ("train", "validation", "test")}
            has_patterns = any(len(u.patterns) for u in units)
            chans = spec.channels
            null_idx = [chans.index(c) for c in ("null_flat", "null_permuted")]
            redundant = [c for c in prof["derived"]["channel_roles"]["zero_weight_redundant"] if c in chans]
            res_ds = {}
            for kind in args.weightings:
                with rec.section(f"{ds}_{kind}_windows"):
                    trw = build_windows(by_split["train"] + by_split["validation"], spec, kind, stride=args.train_stride)
                    val_ids = set(range(len(by_split["train"]), len(by_split["train"]) + len(by_split["validation"])))
                    te = build_windows(by_split["test"], spec, kind)
                var_y = float(np.var(te["y"]))
                r = {"windows": {"train_incl_validation": int(len(trw["y"])), "test": int(len(te["y"]))},
                     "units": {k: len(v) for k, v in by_split.items()}}
                # ---- declared properties of the target
                vg, vs = float(np.var(te["graded_sum"])), float(np.var(te["sparse_sum"]))
                r["variance_ratio_pattern_to_mean"] = None if not has_patterns else vs / vg
                r["variance_ratio_void"] = None if has_patterns else "no inserted patterns in this profile (D05)"
                rho_yR = spearmanr(te["y"], te["R"]).statistic
                r["spearman_y_rul"] = float(rho_yR)
                g_s = s4[ds]["seeds"]["0"]["checks"][kind]["graded_sparse_abs_corr"]
                r["graded_sparse_correlation"] = g_s
                # ---- ensemble
                members = []
                with rec.section(f"{ds}_{kind}_ensemble"):
                    for cname, arch in CONFIGS.items():
                        for ms in range(5):
                            cfg = copy.deepcopy(base_cfg)
                            cfg["architecture"].update(arch)
                            m = train_regressor(trw["X"], trw["y"], trw["unit"], seed=ms, device=ctx.device, cfg=cfg, val_units=val_ids)
                            pred = m.predict(te["X"])
                            rmse = float(np.sqrt(np.mean((pred - te["y"]) ** 2)))
                            members.append({"config": cname, "model_seed": ms, "rmse": rmse, "nrmse": rmse / np.sqrt(var_y), "epochs": m.history["epochs"],
                                            "passes_gate": rmse / np.sqrt(var_y) <= gate, "history": {"train": m.history["train"], "val": m.history["val"]}})
                            torch.save({"state_dict": m.model.state_dict(), "arch": arch, "scaler": m.scaler.__dict__, "channels": chans, "L": L,
                                        "weighting": kind, "profile": ds}, out / "models" / f"{ds}_{kind}_{cname}_seed{ms}.pt")
                            if cname == "A" and ms == 0:
                                primary, primary_pred = m, pred
                r["ensemble"] = [{k: v for k, v in mm.items() if k != "history"} for mm in members]
                r["primary_nrmse"] = members[0]["nrmse"]
                r["gate_pass_primary"] = bool(members[0]["passes_gate"])
                r["gate_pass_members"] = int(sum(mm["passes_gate"] for mm in members))
                save_figure(viz.training_curves(ds, kind, members), out / "figures" / f"{ds.lower()}_{kind}_training_curves")
                save_figure(viz.predicted_vs_true(ds, kind, te["y"], primary_pred, te["z_end"]), out / "figures" / f"{ds.lower()}_{kind}_predicted_vs_true")
                # ---- permutation importance (primary model)
                with rec.section(f"{ds}_{kind}_importance"):
                    sse0, n = U.unit_sums((primary_pred - te["y"]) ** 2, te["unit"])
                    imp = {}
                    g = rng(args.seed, "evaluation", "s6", ds, kind)
                    for ci, c in enumerate(chans):
                        Xp = U.permute_channel(te["X"], ci, g)
                        sse1, _ = U.unit_sums((primary.predict(Xp) - te["y"]) ** 2, te["unit"])
                        imp[c] = U.nmse_increase_ci(sse0, sse1, n, var_y, seed=args.seed, n_resamples=2000)
                    cond = {}
                    for c in redundant:
                        ci = chans.index(c)
                        rm, mu, sd = U.ridge_for_channel(trw["X"], ci, 20000, g)
                        Xc = U.conditional_resample(rm, mu, sd, te["X"], ci, g)
                        sse1, _ = U.unit_sums((primary.predict(Xc) - te["y"]) ** 2, te["unit"])
                        cond[c] = {"predictability_r2": U.predictability_r2(rm, mu, sd, te["X"], ci),
                                   "conditional_importance": U.nmse_increase_ci(sse0, sse1, n, var_y, seed=args.seed, n_resamples=2000)}
                    r["permutation_importance"] = imp
                    r["redundant_channels"] = cond
                    save_figure(viz.importance(ds, kind, imp, cond, null_tol, prof["derived"]["channel_roles"]), out / "figures" / f"{ds.lower()}_{kind}_permutation_importance")
                # ---- term ablation (only meaningful with a pattern term)
                if has_patterns:
                    with rec.section(f"{ds}_{kind}_ablation"):
                        abl = {}
                        for name, target_tr in (("mean_term_removed", trw["sparse_sum"]), ("pattern_term_removed", trw["graded_sum"])):
                            diffs = []
                            for ms in range(3):
                                m = train_regressor(trw["X"], target_tr, trw["unit"], seed=ms, device=ctx.device, cfg=base_cfg, val_units=val_ids)
                                sse_ab, _ = U.unit_sums((m.predict(te["X"]) - te["y"]) ** 2, te["unit"])
                                mfull = train_regressor(trw["X"], trw["y"], trw["unit"], seed=ms, device=ctx.device, cfg=base_cfg, val_units=val_ids) if ms > 0 else primary
                                sse_f, _ = U.unit_sums((mfull.predict(te["X"]) - te["y"]) ** 2, te["unit"])
                                diffs.append((sse_f, sse_ab))
                            sf = np.mean([d[0] for d in diffs], axis=0)
                            sa = np.mean([d[1] for d in diffs], axis=0)
                            abl[name] = U.nmse_increase_ci(sf, sa, n, var_y, seed=args.seed, n_resamples=2000)
                        r["term_ablation"] = abl
                else:
                    r["term_ablation"] = {"void": "no inserted patterns in this profile (D05): the pattern term is identically zero"}
                # ---- error by degradation state
                bins = np.linspace(0, 1, 6)
                zb = np.clip(np.digitize(te["z_end"], bins) - 1, 0, 4)
                r["rmse_by_state_quintile"] = [float(np.sqrt(np.mean((primary_pred[zb == b] - te["y"][zb == b]) ** 2))) if np.any(zb == b) else None for b in range(5)]
                res_ds[kind] = r
                # ---- checks (reported per weighting)
                ct.require(f"{ds} [{kind}]: primary model reaches the accuracy gate (NRMSE <= {gate})", r["gate_pass_primary"], f"<= {gate}", f"{r['primary_nrmse']:.3f}", severity="warn")
                ct.require(f"{ds} [{kind}]: all 10 ensemble members pass the gate (identifiability floor requires it)", r["gate_pass_members"] == 10, "10/10", f"{r['gate_pass_members']}/10", severity="warn")
                for c in ("null_flat", "null_permuted"):
                    ct.require(f"{ds} [{kind}]: permutation importance of {c} <= {null_tol} (upper 95% bound; leakage test)", imp[c]["ci_high"] <= null_tol,
                               f"<= {null_tol}", f"{imp[c]['nmse_increase']:.4f} [{imp[c]['ci_low']:.4f}, {imp[c]['ci_high']:.4f}]", severity="warn")
                if has_patterns:
                    for name, a in r["term_ablation"].items():
                        ct.require(f"{ds} [{kind}]: {name.replace('_', ' ')} increases error on y (95% CI > 0)", a["ci_low"] > 0, "CI > 0",
                                   f"{a['nmse_increase']:.4f} [{a['ci_low']:.4f}, {a['ci_high']:.4f}]", severity="warn")
                    ct.require(f"{ds} [{kind}]: variance ratio of the two terms within the declared band {band}", band[0] <= r["variance_ratio_pattern_to_mean"] <= band[1],
                               str(band), f"{r['variance_ratio_pattern_to_mean']:.4f}", severity="warn")
                    if g_s is not None:
                        ct.require(f"{ds} [{kind}]: graded/sparse correlation <= {corr_bound}", abs(g_s) <= corr_bound, f"<= {corr_bound}", f"{g_s:.3f}", severity="warn")
                write_json({ds: res_ds}, out / "tables" / f"usability_{ds}.json")
            results[ds] = res_ds
        write_json(results, out / "tables" / "usability.json")
        code = ct.finalize(out)
        (out / "logs" / "checks.md").write_text(ct.markdown() + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
