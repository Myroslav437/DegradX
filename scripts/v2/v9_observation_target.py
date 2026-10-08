#!/usr/bin/env python
"""V9 (brief "DegradX v2", X9) — exploratory pilot: does defining y on the observed window restore position-level
identifiability? Declarations r3 ``declared_by_design.v2.observation_target`` (declared before this ran).

HUST, recency, V4 generation seed 0 with its declared split. Target y_obs = sum_W w (x - x0) on the observed window, so the
reference model is the data-generating function and phi*_obs = w (x - x0). Ten LSTM members (A 64x2, B 128x1; model
seeds 0-4) are trained on y_obs; accuracy as NRMSE and relative to SD(sum w eps); the X4 channel-usage gate on every
member; IG and feature occlusion on the 120 V8 windows for every member; rank agreement, channel allocation error and
temporal profile error against phi*_obs; the ensemble range of each score against the largest gap between methods on the
primary model. One D-record and one figure; nothing enters the paper tables. Outputs in
``artifacts/v2/v9_observation_target``.
"""

from __future__ import annotations

import copy
import pickle
import sys

import numpy as np
import torch
import yaml

import _common as C
import v8_reference_methods as V8
from degradx import ARTIFACTS_V2, CONFIG_DIR, DATA_V2
from degradx.attribution import methods as M
from degradx.generator.generate import Profile
from degradx.metrics import usability as U
from degradx.metrics.scores import channel_allocation_error, rank_agreement, temporal_profile_error
from degradx.models.lstm import train_regressor
from degradx.targets.decomposable import TargetSpec, unit_targets
from degradx.utils.checks import CheckTable
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.io import save_figure, write_json
from degradx.utils.provenance import RunRecord
from degradx.utils.seeding import rng

DS, KIND = "HUST", "recency"
CONFIGS = {"A": {"hidden_size": 64, "num_layers": 2}, "B": {"hidden_size": 128, "num_layers": 1}}


def windows_obs(units, spec):
    Xs, ys, ns, us = [], [], [], []
    W = spec.weights(KIND)
    for i, u in enumerate(units):
        if u.T < spec.L:
            continue
        tg = unit_targets(u, spec, KIND)
        Xs.append(tg["x"])
        ys.append((W[None] * (tg["x"] - spec.x0[None, None, :])).sum(axis=(1, 2)))  # y_obs = g(x)
        ns.append(tg["noise_term"])
        us.append(np.full(len(tg["y"]), i))
    return {"X": np.concatenate(Xs).astype(np.float32), "y": np.concatenate(ys), "noise": np.concatenate(ns), "unit": np.concatenate(us).astype(int)}


def standard_y_comparison():
    """The V8 ensemble range and IG-occlusion gap on the standard y for the same HUST windows (None before V8 is scored)."""
    import json

    v8f = ARTIFACTS_V2 / "v8_reference_methods" / "tables" / "reference_values.json"
    r8 = json.loads(v8f.read_text()).get(DS, {}).get("weightings", {}).get(KIND) if v8f.exists() else None
    if not r8:
        return None
    return {k: {"ensemble_range": {m: r8["identifiability_floor"][m][f"{k}_max"] - r8["identifiability_floor"][m][f"{k}_min"]
                                   for m in ("integrated_gradients", "feature_occlusion")},
                "largest_method_gap_IG_occlusion": abs(r8["scores"]["trained/integrated_gradients"][k]["mean"] - r8["scores"]["trained/feature_occlusion"][k]["mean"])}
            for k in ("rank", "allocation", "temporal")}


def main() -> int:
    p = stage_parser(__doc__, "v2/v9_observation_target")
    p.add_argument("--compare-only", action="store_true", help="add the V8 standard-y comparison to an existing V9 result and redraw the figure")
    args = p.parse_args()
    if args.compare_only:
        import json

        from degradx.viz import v9 as viz

        f = ARTIFACTS_V2 / "v9_observation_target" / "tables" / "observation_target.json"
        res = json.loads(f.read_text())
        res["standard_y_for_comparison"] = standard_y_comparison()
        write_json(res, f)
        save_figure(viz.ensemble_vs_gap(res), ARTIFACTS_V2 / "v9_observation_target" / "figures" / "hust_yobs_ensemble_vs_method_gap")
        return 0 if res["standard_y_for_comparison"] else 1
    ctx = StageContext.from_args(args)
    decl, dd = ctx.declarations, ctx.declarations["declared_by_design"]
    if args.dry_run:
        print("plan: X9 pilot on HUST recency")
        return 0
    out, ct = ctx.out_dir, CheckTable()
    (out / "models").mkdir(parents=True, exist_ok=True)
    base_cfg = yaml.safe_load((CONFIG_DIR / "models" / "lstm.yaml").read_text())
    n_boot = int(dd["v2"]["statistics"]["bootstrap_n_resamples"])
    beta, L = dd["target"]["weights"]["beta"]["value"], int(dd["target"]["window_length_L"]["value"])
    prof = C.v2_profile(DS)
    units, table = pickle.loads((DATA_V2 / "generated" / DS / "seed0.pkl").read_bytes())
    P = Profile.from_json(prof, C.null_pool(DS, decl))  # real pool: the null_permuted reference point enters the baseline
    spec = TargetSpec.build(P, beta, L, 6.0)
    split = dict(zip(table["index"], table["split"]))
    by = {s: [u for u in units if split[u.index] == s] for s in ("train", "validation", "test")}
    chans = spec.channels
    weighted = [c for c in prof["derived"]["channel_roles"]["weighted"] if c in chans]
    res = {"profile": DS, "weighting": KIND}
    with RunRecord("v2/v9_observation_target", out, {"config": ctx.config}, {"generation": 0, "model_init": list(range(5)), "evaluation": args.seed}, ctx.device) as rec:
        trw = windows_obs(by["train"] + by["validation"], spec)
        te = windows_obs(by["test"], spec)
        val_ids = set(range(len(by["train"]), len(by["train"]) + len(by["validation"])))
        var_y, sd_noise = float(np.var(te["y"])), float(np.std(te["noise"]))
        members, models = [], {}
        with rec.section("ensemble"):
            for cname, arch in CONFIGS.items():
                for ms in range(5):
                    cfg = copy.deepcopy(base_cfg)
                    cfg["architecture"].update(arch)
                    m = train_regressor(trw["X"], trw["y"], trw["unit"], seed=ms, device=ctx.device, cfg=cfg, val_units=val_ids)
                    pred = m.predict(te["X"])
                    rmse = float(np.sqrt(np.mean((pred - te["y"]) ** 2)))
                    members.append({"member": f"{cname}{ms}", "rmse": rmse, "nrmse": rmse / np.sqrt(var_y), "rmse_over_sd_noise": rmse / sd_noise,
                                    "reads_cells": bool(rmse <= 0.5 * sd_noise), "epochs": m.history["epochs"]})
                    models[f"{cname}{ms}"] = (m, pred)
                    torch.save({"state_dict": m.model.state_dict(), "arch": arch, "scaler": m.scaler.__dict__, "channels": chans, "L": L, "weighting": KIND,
                                "profile": DS, "target": "y_obs"}, out / "models" / f"{DS}_{KIND}_{cname}_seed{ms}_yobs.pt")
                    print(f"[v9] {cname}{ms}: NRMSE {members[-1]['nrmse']:.4f}, RMSE/SD(noise) {members[-1]['rmse_over_sd_noise']:.3f}", flush=True)
        res["accuracy"] = {"members": members, "sd_noise_term": sd_noise, "sd_y_obs": float(np.sqrt(var_y)),
                           "primary_reads_cells": members[0]["reads_cells"], "members_reading_cells": int(sum(mm["reads_cells"] for mm in members))}
        # X4 on every member against y_obs
        with rec.section("x4"):
            usage = {}
            ridge = {c: U.ridge_for_channel(trw["X"], chans.index(c), 20000, rng(args.seed, "evaluation", "X4-yobs", DS, c, "ridge")) for c in weighted}
            for mname, (m, pred) in models.items():
                s0, nn = U.unit_sums((pred - te["y"]) ** 2, te["unit"])
                usage[mname] = {}
                for c in weighted:
                    rm, mu, sd = ridge[c]
                    Xc = U.conditional_resample(rm, mu, sd, te["X"], chans.index(c), rng(args.seed, "evaluation", "X4-yobs", DS, c, mname))
                    s1, _ = U.unit_sums((m.predict(Xc) - te["y"]) ** 2, te["unit"])
                    q = U.nmse_increase_ci(s0, s1, nn, var_y, seed=args.seed, n_resamples=n_boot)
                    usage[mname][c] = {**q, "used": bool(q["ci_low"] > 0), "used_materially": bool(q["ci_low"] > 0.02)}
            res["channel_usage"] = usage
        # IG and occlusion on the 120 V8 windows, every member; scores against phi*_obs = w (x - x0)
        with rec.section("attribution"):
            S = V8.ProfileSetup(DS, dd, args.seed, [KIND])
            X = S.X(KIND)
            phi_obs = spec.weights(KIND)[None] * (X - spec.x0)
            baseline = np.broadcast_to(spec.x0, (L, len(spec.x0))).copy()
            widx = np.flatnonzero(spec.kappa != 0)
            scores = {}
            for mname, (m, _p) in models.items():
                rs = M.RawSpaceModel(m)
                for meth, fn in (("integrated_gradients", M.integrated_gradients), ("feature_occlusion", M.feature_occlusion)):
                    A = fn(rs, X, baseline, ctx.device)
                    vals = {"rank": [rank_agreement(A[i], phi_obs[i]) for i in range(len(X))],
                            "allocation": [channel_allocation_error(A[i], phi_obs[i]) for i in range(len(X))],
                            "temporal": [temporal_profile_error(A[i], phi_obs[i], widx)[0] for i in range(len(X))]}
                    scores.setdefault(meth, {})[mname] = {k: (V8.unit_mean_ci(v, S.unit_ids, args.seed, n_boot) if mname == "A0" else {"mean": V8.unit_mean(v, S.unit_ids)})
                                                          for k, v in vals.items()}
            ref = M.ReferenceModel(spec.weights(KIND), spec.x0)
            A = M.integrated_gradients(ref, X, baseline, ctx.device)
            ct.require("V9: IG on the reference model equals phi*_obs = w(x - x0) (correctness check)", float(np.max(np.abs(A - phi_obs))) < 1e-3 * max(1.0, np.abs(phi_obs).max()),
                       "< 1e-3 relative", f"{float(np.max(np.abs(A - phi_obs))):.2e}")
            res["scores"] = scores
        # comparison: ensemble range per method vs largest method gap on the primary model
        comp = {}
        for k in ("rank", "allocation", "temporal"):
            prim = {meth: scores[meth]["A0"][k]["mean"] for meth in scores}
            gap = float(max(prim.values()) - min(prim.values()))
            rngs = {meth: float(max(v[k]["mean"] for v in scores[meth].values()) - min(v[k]["mean"] for v in scores[meth].values())) for meth in scores}
            comp[k] = {"primary": prim, "largest_method_gap": gap, "ensemble_range": rngs, "restored": bool(all(r < gap for r in rngs.values()))}
        res["comparison"] = comp
        # the same comparison on the standard y (V8, same windows); filled by --compare-only once V8 is scored
        res["standard_y_for_comparison"] = standard_y_comparison()
        write_json(res, out / "tables" / "observation_target.json")
        from degradx.viz import v9 as viz

        save_figure(viz.ensemble_vs_gap(res), out / "figures" / "hust_yobs_ensemble_vs_method_gap")
        ct.require("V9: primary model passes the accuracy gate on y_obs", members[0]["nrmse"] <= 0.30, "<= 0.30", f"{members[0]['nrmse']:.3f}", severity="warn")
        code = ct.finalize(out)
        (out / "logs" / "checks.md").write_text(ct.markdown() + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
