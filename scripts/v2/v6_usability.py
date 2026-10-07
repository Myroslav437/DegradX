#!/usr/bin/env python
"""V6 (brief "DegradX v2") — RQ2, usability and identifiability of the attribution ground truth on the v2 profiles.

Per profile and weighting (declarations r3 v2.scope.weightings: recency primary, uniform sensitivity), on V4 generation
seed 0 (declared train/validation/test unit split):
  * ten-member LSTM ensemble on y (configurations A 64x2 and B 128x1, model seeds 0-4), every member under the accuracy
    gate (NRMSE <= 0.30); member A/seed 0 is the primary model;
  * null-channel leakage gate (upper 95% bound of the NMSE increase under permutation <= 0.02), redundant channels
    reported (ridge predictability, conditional importance), term ablation where the profile carries patterns;
  * X4 channel-usage gate: conditional permutation importance (v1 ridge conditional resampling) of every weighted channel
    on every member, 95% BCa over test units (10 000 resamples); 'used' iff the lower bound > 0 (primary), 'used
    materially' iff > 0.02 (reported); read on the primary model;
  * the offset and pattern terms of y (X2): variance shares on the test windows.
A failed accuracy gate or leakage test on a primary model is a stop-and-report case (v2.stop_rules); the script records it
and exits non-zero. Models are saved to ``artifacts/v2/v6_usability/models`` (Git LFS). Outputs in
``artifacts/v2/v6_usability``.
"""

from __future__ import annotations

import copy
import pickle
import sys

import numpy as np
import torch
import yaml
from scipy.stats import spearmanr

import _common as C
from degradx import CONFIG_DIR, DATA_V2
from degradx.generator.generate import Profile
from degradx.metrics import usability as U
from degradx.models.lstm import train_regressor
from degradx.targets.decomposable import TargetSpec, unit_targets
from degradx.utils.checks import CheckTable
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.io import save_figure, write_json
from degradx.utils.provenance import RunRecord
from degradx.utils.seeding import rng

CONFIGS = {"A": {"hidden_size": 64, "num_layers": 2}, "B": {"hidden_size": 128, "num_layers": 1}}


def build_windows(units, spec, kind, stride: int = 1):
    Xs, ys, gs, ss, os_, us, zs, Rs = [], [], [], [], [], [], [], []
    for i, u in enumerate(units):
        if u.T < spec.L:
            continue
        ends = np.arange(spec.L, u.T + 1, stride)
        tg = unit_targets(u, spec, kind, ends=ends)
        Xs.append(tg["x"]); ys.append(tg["y"])
        gs.append(tg["graded"].sum(axis=(1, 2))); ss.append(tg["sparse"].sum(axis=(1, 2)))
        if u.m_state is not None:
            idx = ends[:, None] - spec.L + np.arange(spec.L)[None, :]
            os_.append((spec.weights(kind)[None] * (u.m[idx] - u.m_state[idx])).sum(axis=(1, 2)))
        us.append(np.full(len(ends), i)); zs.append(tg["z_end"]); Rs.append(tg["R"])
    cat = lambda a: np.concatenate(a) if a else np.empty(0)  # noqa: E731
    return {"X": np.concatenate(Xs).astype(np.float32), "y": cat(ys), "graded_sum": cat(gs), "sparse_sum": cat(ss), "offset_sum": cat(os_),
            "unit": cat(us).astype(int), "z_end": cat(zs), "R": cat(Rs)}


def main() -> int:
    p = stage_parser(__doc__, "v2/v6_usability")
    p.add_argument("--datasets", nargs="*", default=["MATR", "HUST"])
    p.add_argument("--profile-config", nargs="*", default=[])
    p.add_argument("--weightings", nargs="*", default=None)
    p.add_argument("--train-stride", type=int, default=1)
    args = p.parse_args()
    for kv in args.profile_config:
        C.register_profile(*kv.split("="))
    ctx = StageContext.from_args(args)
    decl, dd = ctx.declarations, ctx.declarations["declared_by_design"]
    sc = dd["v2"]["scope"]["weightings"]
    weightings = args.weightings or [sc["primary"], sc["sensitivity"]]
    if args.dry_run:
        print(f"plan: usability v2 for {args.datasets} x {weightings}")
        return 0
    from degradx.viz import s6 as viz

    out, ct = ctx.out_dir, CheckTable()
    (out / "models").mkdir(parents=True, exist_ok=True)
    base_cfg = yaml.safe_load((CONFIG_DIR / "models" / "lstm.yaml").read_text())
    gate = 0.30
    null_tol = 0.02
    n_boot = int(dd["v2"]["statistics"]["bootstrap_n_resamples"])
    band = dd["usability"]["variance_ratio_band"]["value"]
    corr_bound = float(dd["usability"]["graded_sparse_correlation_bound"]["value"])
    beta = dd["target"]["weights"]["beta"]["value"]
    L = int(dd["target"]["window_length_L"]["value"])
    results, stop = {}, []
    with RunRecord("v2/v6_usability", out, {"config": ctx.config, "datasets": args.datasets, "weightings": weightings, "train_stride": args.train_stride},
                   {"generation": 0, "model_init": list(range(5)), "evaluation": args.seed}, ctx.device) as rec:
        for ds in args.datasets:
            prof = C.v2_profile(ds)
            units, table = pickle.loads((DATA_V2 / "generated" / ds / "seed0.pkl").read_bytes())
            P = Profile.from_json(prof, np.array([0.0]))
            spec = TargetSpec.build(P, beta, L, 6.0)
            split = dict(zip(table["index"], table["split"]))
            by_split = {s: [u for u in units if split[u.index] == s] for s in ("train", "validation", "test")}
            has_patterns = any(len(u.patterns) for u in units)
            chans = spec.channels
            weighted = [c for c in prof["derived"]["channel_roles"]["weighted"] if c in chans]
            redundant = [c for c in prof["derived"]["channel_roles"]["zero_weight_redundant"] if c in chans]
            res_ds = {}
            for kind in weightings:
                with rec.section(f"{ds}_{kind}_windows"):
                    trw = build_windows(by_split["train"] + by_split["validation"], spec, kind, stride=args.train_stride)
                    val_ids = set(range(len(by_split["train"]), len(by_split["train"]) + len(by_split["validation"])))
                    te = build_windows(by_split["test"], spec, kind)
                var_y = float(np.var(te["y"]))
                r = {"windows": {"train_incl_validation": int(len(trw["y"])), "test": int(len(te["y"]))}, "units": {k: len(v) for k, v in by_split.items()},
                     "weighted_channels": weighted}
                vg, vs = float(np.var(te["graded_sum"])), float(np.var(te["sparse_sum"]))
                r["variance_ratio_pattern_to_mean"] = vs / vg if has_patterns else None
                r["variance_ratio_void"] = None if has_patterns else "no inserted patterns in this profile (D05)"
                if len(te["offset_sum"]):
                    y_state = te["graded_sum"] - te["offset_sum"]
                    r["offset_term"] = {"share_of_var_y": float(np.var(te["offset_sum"]) / var_y), "ratio_to_state_term": float(np.var(te["offset_sum"]) / np.var(y_state)),
                                        "corr_with_state_term": float(np.corrcoef(te["offset_sum"], y_state)[0, 1])}
                r["spearman_y_rul"] = float(spearmanr(te["y"], te["R"]).statistic)
                # ---- ensemble
                members, models = [], {}
                with rec.section(f"{ds}_{kind}_ensemble"):
                    for cname, arch in CONFIGS.items():
                        for ms in range(5):
                            cfg = copy.deepcopy(base_cfg)
                            cfg["architecture"].update(arch)
                            m = train_regressor(trw["X"], trw["y"], trw["unit"], seed=ms, device=ctx.device, cfg=cfg, val_units=val_ids)
                            pred = m.predict(te["X"])
                            rmse = float(np.sqrt(np.mean((pred - te["y"]) ** 2)))
                            members.append({"member": f"{cname}{ms}", "config": cname, "model_seed": ms, "rmse": rmse, "nrmse": rmse / np.sqrt(var_y),
                                            "epochs": m.history["epochs"], "passes_gate": rmse / np.sqrt(var_y) <= gate,
                                            "history": {"train": m.history["train"], "val": m.history["val"]}})
                            models[f"{cname}{ms}"] = (m, pred)
                            torch.save({"state_dict": m.model.state_dict(), "arch": arch, "scaler": m.scaler.__dict__, "channels": chans, "L": L,
                                        "weighting": kind, "profile": ds, "version": "v2"}, out / "models" / f"{ds}_{kind}_{cname}_seed{ms}.pt")
                primary, primary_pred = models["A0"]
                r["ensemble"] = [{k: v for k, v in mm.items() if k != "history"} for mm in members]
                r["primary_nrmse"] = members[0]["nrmse"]
                r["gate_pass_primary"] = bool(members[0]["passes_gate"])
                r["gate_pass_members"] = int(sum(mm["passes_gate"] for mm in members))
                save_figure(viz.training_curves(ds, kind, members), out / "figures" / f"{ds.lower()}_{kind}_training_curves")
                save_figure(viz.predicted_vs_true(ds, kind, te["y"], primary_pred, te["z_end"]), out / "figures" / f"{ds.lower()}_{kind}_predicted_vs_true")
                # ---- permutation importance (primary), null gate, redundant channels
                with rec.section(f"{ds}_{kind}_importance"):
                    sse0, n = U.unit_sums((primary_pred - te["y"]) ** 2, te["unit"])
                    imp = {}
                    g = rng(args.seed, "evaluation", "v6", ds, kind)
                    for ci, c in enumerate(chans):
                        Xp = U.permute_channel(te["X"], ci, g)
                        sse1, _ = U.unit_sums((primary.predict(Xp) - te["y"]) ** 2, te["unit"])
                        imp[c] = U.nmse_increase_ci(sse0, sse1, n, var_y, seed=args.seed, n_resamples=n_boot)
                    r["permutation_importance"] = imp
                    ridge = {}
                    for c in redundant + weighted:
                        ci = chans.index(c)
                        ridge[c] = U.ridge_for_channel(trw["X"], ci, 20000, rng(args.seed, "evaluation", "X4", ds, kind, c, "ridge"))
                    r["redundant_channels"] = {}
                    for c in redundant:
                        ci = chans.index(c)
                        rm, mu, sd = ridge[c]
                        Xc = U.conditional_resample(rm, mu, sd, te["X"], ci, rng(args.seed, "evaluation", "X4", ds, kind, c, "A0"))
                        sse1, _ = U.unit_sums((primary.predict(Xc) - te["y"]) ** 2, te["unit"])
                        r["redundant_channels"][c] = {"predictability_r2": U.predictability_r2(rm, mu, sd, te["X"], ci),
                                                      "conditional_importance": U.nmse_increase_ci(sse0, sse1, n, var_y, seed=args.seed, n_resamples=n_boot)}
                    save_figure(viz.importance(ds, kind, imp, r["redundant_channels"], null_tol, prof["derived"]["channel_roles"]),
                                out / "figures" / f"{ds.lower()}_{kind}_permutation_importance")
                # ---- X4 channel-usage gate on every member
                with rec.section(f"{ds}_{kind}_x4"):
                    usage = {}
                    for mname, (m, pred) in models.items():
                        s0, nn = U.unit_sums((pred - te["y"]) ** 2, te["unit"])
                        usage[mname] = {}
                        for c in weighted:
                            ci = chans.index(c)
                            rm, mu, sd = ridge[c]
                            Xc = U.conditional_resample(rm, mu, sd, te["X"], ci, rng(args.seed, "evaluation", "X4", ds, kind, c, mname))
                            s1, _ = U.unit_sums((m.predict(Xc) - te["y"]) ** 2, te["unit"])
                            ci_ = U.nmse_increase_ci(s0, s1, nn, var_y, seed=args.seed, n_resamples=n_boot)
                            usage[mname][c] = {**ci_, "used": bool(ci_["ci_low"] > 0), "used_materially": bool(ci_["ci_low"] > null_tol),
                                               "predictability_r2": U.predictability_r2(rm, mu, sd, te["X"], ci)}
                    r["channel_usage"] = usage
                    unused = [c for c in weighted if not usage["A0"][c]["used"]]
                    r["channel_usage_gate"] = {"primary_used": {c: usage["A0"][c]["used"] for c in weighted},
                                               "primary_used_materially": {c: usage["A0"][c]["used_materially"] for c in weighted},
                                               "unused_on_primary": unused,
                                               "void_channel_level_scores": (f"weighted channel(s) {', '.join(unused)} not used (X4)" if unused else None),
                                               "members_using_all": int(sum(all(usage[mm][c]["used"] for c in weighted) for mm in usage))}
                # ---- term ablation (only with a pattern term)
                if has_patterns:
                    with rec.section(f"{ds}_{kind}_ablation"):
                        abl = {}
                        for name, target_tr in (("mean_term_removed", trw["sparse_sum"]), ("pattern_term_removed", trw["graded_sum"])):
                            diffs = []
                            for ms in range(3):
                                m = train_regressor(trw["X"], target_tr, trw["unit"], seed=ms, device=ctx.device, cfg=base_cfg, val_units=val_ids)
                                sse_ab, _ = U.unit_sums((m.predict(te["X"]) - te["y"]) ** 2, te["unit"])
                                mfull = models[f"A{ms}"][0]
                                sse_f, _ = U.unit_sums((mfull.predict(te["X"]) - te["y"]) ** 2, te["unit"])
                                diffs.append((sse_f, sse_ab))
                            sf = np.mean([d_[0] for d_ in diffs], axis=0)
                            sa = np.mean([d_[1] for d_ in diffs], axis=0)
                            abl[name] = U.nmse_increase_ci(sf, sa, n, var_y, seed=args.seed, n_resamples=n_boot)
                        r["term_ablation"] = abl
                else:
                    r["term_ablation"] = {"void": "no inserted patterns in this profile (D05): the pattern term is identically zero"}
                bins = np.linspace(0, 1, 6)
                zb = np.clip(np.digitize(te["z_end"], bins) - 1, 0, 4)
                r["rmse_by_state_quintile"] = [float(np.sqrt(np.mean((primary_pred[zb == b] - te["y"][zb == b]) ** 2))) if np.any(zb == b) else None for b in range(5)]
                res_ds[kind] = r
                # ---- checks (gate and leakage failures are stop-and-report cases)
                ct.require(f"{ds} [{kind}]: primary model reaches the accuracy gate (NRMSE <= {gate})", r["gate_pass_primary"], f"<= {gate}", f"{r['primary_nrmse']:.3f}")
                ct.require(f"{ds} [{kind}]: all 10 ensemble members pass the gate", r["gate_pass_members"] == 10, "10/10", f"{r['gate_pass_members']}/10", severity="warn")
                if not r["gate_pass_primary"]:
                    stop.append(f"{ds} [{kind}]: accuracy gate failed (NRMSE {r['primary_nrmse']:.3f})")
                for c in ("null_flat", "null_permuted"):
                    passed = imp[c]["ci_high"] <= null_tol
                    ct.require(f"{ds} [{kind}]: permutation importance of {c} <= {null_tol} (upper 95% bound; leakage test)", passed, f"<= {null_tol}",
                               f"{imp[c]['nmse_increase']:.4f} [{imp[c]['ci_low']:.4f}, {imp[c]['ci_high']:.4f}]")
                    if not passed:
                        stop.append(f"{ds} [{kind}]: null-channel leakage on {c} ({imp[c]['ci_high']:.4f} > {null_tol})")
                for c in weighted:
                    u_ = usage["A0"][c]
                    ct.require(f"{ds} [{kind}]: X4 weighted channel {c} used by the primary model (lower bound > 0; reported, voids channel-level trained scores if not)",
                               u_["used"], "> 0", f"{u_['nmse_increase']:.4f} [{u_['ci_low']:.4f}, {u_['ci_high']:.4f}]", severity="warn")
                if has_patterns:
                    for name, a in r["term_ablation"].items():
                        ct.require(f"{ds} [{kind}]: {name.replace('_', ' ')} increases error on y (95% CI > 0)", a["ci_low"] > 0, "CI > 0",
                                   f"{a['nmse_increase']:.4f} [{a['ci_low']:.4f}, {a['ci_high']:.4f}]", severity="warn")
                    ct.require(f"{ds} [{kind}]: variance ratio within the declared band {band}", band[0] <= r["variance_ratio_pattern_to_mean"] <= band[1],
                               str(band), f"{r['variance_ratio_pattern_to_mean']:.4f}", severity="warn")
                write_json({ds: res_ds}, out / "tables" / f"usability_{ds}.json")
            results[ds] = res_ds
        results["_stop_and_report"] = stop
        write_json(results, out / "tables" / "usability.json")
        code = ct.finalize(out)
        (out / "logs" / "checks.md").write_text(ct.markdown() + "\n")
    if stop:
        print("STOP AND REPORT (brief §6):", *stop, sep="\n  ")
        return 2
    return code


if __name__ == "__main__":
    sys.exit(main())
