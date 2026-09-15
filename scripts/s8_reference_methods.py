#!/usr/bin/env python
"""S8 — reference values for published methods (paper §3.6; Table 6).

TimeSHAP, Integrated Gradients and feature occlusion at their default configurations (declarations attribution.methods)
on the primary trained LSTM (S6 configuration A, model seed 0) and on the reference model, per profile and position
weighting, on windows drawn from generated test units (generation seed 0) with the 'evaluation' seed stream, stratified
across units. Baseline: the declared pristine window (C4). Scores (declarations scoring, D01):
  rank agreement   Spearman(map on the pattern-free counterpart, graded field)
  retrieval        AP(|map(x) - map(x without patterns)|, sparse set) — NASA PCoE only (D05); void on trained models (D21)
  retrieval plain  AP(|map(x)|, sparse set), secondary
  zero-weight mass share of |map| on channels with zero target weight (error by construction)
Also: the exact attribution of the reference model w(x - x0) (noise ceiling), TimeSHAP convergence over attribution
sampling seeds, and the identifiability floor: IG and occlusion on all ten S6 ensemble members (C2). Reported in aggregate
(no position stratification, no diagnosis of causes). Outputs in ``artifacts/s8_reference_methods``; raw maps in
``data/attributions`` (gitignored).
"""

from __future__ import annotations

import json
import pickle
import sys
import time

import numpy as np
import torch
from scipy.stats import bootstrap

from degradx import ARTIFACTS_DIR, DATA_DIR
from degradx.attribution import methods as M
from degradx.generator.generate import Profile
from degradx.metrics.scores import rank_agreement, retrieval_ap, zero_weight_mass
from degradx.models.lstm import LSTMRegressor, Standardiser, TrainedModel
from degradx.targets.decomposable import WEIGHTINGS, TargetSpec, unit_targets
from degradx.utils.checks import CheckTable
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.io import save_figure, save_table, write_json
from degradx.utils.provenance import RunRecord
from degradx.utils.seeding import rng

PROFILES = ("MATR", "HUST", "NASA_PCoE")


def load_member(path, device) -> TrainedModel:
    ck = torch.load(path, map_location=device, weights_only=False)
    arch = ck["arch"]
    model = LSTMRegressor(len(ck["channels"]), arch["hidden_size"], arch["num_layers"]).to(device)
    model.load_state_dict(ck["state_dict"])
    sc = ck["scaler"]
    return TrainedModel(model, Standardiser(np.asarray(sc["mean"]), np.asarray(sc["std"]), float(sc["y_mean"]), float(sc["y_std"])), {}, device)


def select_windows(test_units, spec, n_windows, g):
    eligible = [u for u in test_units if u.T >= spec.L]
    per = int(np.ceil(n_windows / len(eligible)))
    picks = []
    for ui, u in enumerate(eligible):
        ends = np.arange(spec.L, u.T + 1)
        for e in np.sort(g.choice(ends, size=min(per, len(ends)), replace=False)):
            picks.append((ui, int(e)))
    idx = np.sort(g.choice(len(picks), size=min(n_windows, len(picks)), replace=False))
    return eligible, [picks[i] for i in idx]


def unit_mean_ci(values, unit_ids, seed):
    v, u = np.asarray(values, float), np.asarray(unit_ids)
    uu = np.unique(u[np.isfinite(v)])
    means = np.array([np.nanmean(v[(u == k)]) for k in uu])
    if len(means) < 3:
        return {"mean": float(np.nanmean(means)) if len(means) else None, "ci_low": None, "ci_high": None, "units": int(len(means))}
    res = bootstrap((means,), np.mean, n_resamples=2000, method="BCa", random_state=np.random.default_rng(seed))
    return {"mean": float(means.mean()), "ci_low": float(res.confidence_interval.low), "ci_high": float(res.confidence_interval.high), "units": int(len(means))}


def score_maps(A, Apf, W, zero_ch):
    out = {"rank": [], "retrieval": [], "retrieval_plain": [], "zero_mass": []}
    for i, w in enumerate(W):
        out["rank"].append(rank_agreement(Apf[i], w["graded"]))
        out["zero_mass"].append(zero_weight_mass(A[i], zero_ch))
        if w["sparse_mask"].any():
            out["retrieval"].append(retrieval_ap(A[i] - Apf[i], w["sparse_mask"]))
            out["retrieval_plain"].append(retrieval_ap(A[i], w["sparse_mask"]))
        else:
            out["retrieval"].append(np.nan)
            out["retrieval_plain"].append(np.nan)
    return out


def main() -> int:
    p = stage_parser(__doc__, "s8_reference_methods")
    p.add_argument("--datasets", nargs="*", default=list(PROFILES))
    p.add_argument("--weightings", nargs="*", default=list(WEIGHTINGS))
    p.add_argument("--windows", type=int, default=None, help="windows per profile (default: declarations attribution.windows_scored_per_profile)")
    p.add_argument("--timeshap-windows", type=int, default=None, help="windows explained by TimeSHAP (budget lever; default = --windows)")
    p.add_argument("--timeshap-seeds", nargs="*", type=int, default=None, help="TimeSHAP attribution sampling seeds (default: declared)")
    p.add_argument("--timeshap-seeds-reference", nargs="*", type=int, default=None, help="TimeSHAP seeds on the reference model (default: same as trained)")
    p.add_argument("--secondary-background", action="store_true", help="also run TimeSHAP on the trained model from the average event (C4 secondary, D09)")
    p.add_argument("--timeshap-l1", default="auto", help="TimeSHAP l1_reg ('auto' = library default at cell level, or 'False')")
    p.add_argument("--skip-ensemble", action="store_true")
    args = p.parse_args()
    ctx = StageContext.from_args(args)
    decl, dd = ctx.declarations, ctx.declarations["declared_by_design"]
    n_win = args.windows or int(dd["attribution"]["windows_scored_per_profile"])
    ts_seeds = args.timeshap_seeds if args.timeshap_seeds is not None else dd["statistics"]["seeds"]["attribution_sampling"]
    l1 = False if str(args.timeshap_l1) == "False" else args.timeshap_l1
    if args.dry_run:
        print(f"plan: {n_win} windows/profile; TimeSHAP windows {args.timeshap_windows or n_win}, seeds {ts_seeds}, l1_reg {l1}")
        return 0
    from degradx.viz import s8 as viz

    out, ct = ctx.out_dir, CheckTable()
    beta = dd["target"]["weights"]["beta"]["value"]
    L = int(dd["target"]["window_length_L"]["value"])
    s6 = {}
    for ds in args.datasets:
        f = ARTIFACTS_DIR / "s6_usability" / "tables" / f"usability_{ds}.json"
        s6.update(json.loads(f.read_text()) if f.exists() else {})
    prev = out / "tables" / "reference_values.json"
    results = json.loads(prev.read_text()) if prev.exists() else {}  # runs per dataset merge into one file
    maps_dir = DATA_DIR / "attributions"
    maps_dir.mkdir(parents=True, exist_ok=True)
    with RunRecord("s8_reference_methods", out, {"config": ctx.config, "windows": n_win, "timeshap_windows": args.timeshap_windows, "timeshap_seeds": ts_seeds, "l1_reg": str(l1)},
                   {"evaluation": args.seed, "attribution_sampling": ts_seeds, "generation": 0, "model_init": 0}, ctx.device) as rec:
        for ds in args.datasets:
            prof = json.loads((ARTIFACTS_DIR / "s3_fit_profiles" / "profiles" / f"{ds}.json").read_text())
            units, table = pickle.loads((DATA_DIR / "generated" / ds / "seed0.pkl").read_bytes())
            split = dict(zip(table["index"], table["split"]))
            test = [u for u in units if split[u.index] == "test"]
            P = Profile.from_json(prof, np.concatenate([u.eps[:, len(prof["declared_used"]["channels_available"]) + 1] for u in units]))
            spec = TargetSpec.build(P, beta, L, 6.0)
            zero_ch = np.flatnonzero(spec.kappa == 0)
            has_patterns = any(len(u.patterns) for u in units)
            g = rng(args.seed, "evaluation", "s8", ds)
            eligible, picks = select_windows(test, spec, n_win, g)
            n_ts = min(args.timeshap_windows or n_win, len(picks))
            ts_idx = set(np.sort(rng(args.seed, "evaluation", "s8-timeshap", ds).choice(len(picks), size=n_ts, replace=False)).tolist())
            baseline = np.broadcast_to(spec.x0, (L, len(spec.x0))).copy()
            results[ds] = {"windows": len(picks), "units": len({p_[0] for p_ in picks}), "timeshap_windows": n_ts, "baseline": dict(zip(spec.channels, spec.x0.tolist())),
                           "timeshap_background_event": dict(zip(spec.channels, spec.x0.tolist())), "weightings": {}}
            for kind in args.weightings:
                W = []
                for ui, e in picks:
                    tg = unit_targets(eligible[ui], spec, kind, ends=np.array([e]))
                    W.append({"unit": ui, "x": tg["x"][0], "xpf": tg["x_pattern_free"][0], "graded": tg["graded"][0], "sparse_mask": tg["sparse"][0] != 0,
                              "phi": tg["phi_star"][0]})
                X = np.stack([w["x"] for w in W]).astype(np.float32)
                Xpf = np.stack([w["xpf"] for w in W]).astype(np.float32)
                unit_ids = [w["unit"] for w in W]
                trained = M.RawSpaceModel(load_member(ARTIFACTS_DIR / "s6_usability" / "models" / f"{ds}_{kind}_A_seed0.pt", ctx.device))
                ref = M.ReferenceModel(spec.weights(kind), spec.x0)
                gate_ok = bool(s6.get(ds, {}).get(kind, {}).get("gate_pass_primary", False))
                abl = s6.get(ds, {}).get(kind, {}).get("term_ablation", {})
                patterns_used = bool(abl.get("pattern_term_removed", {}).get("ci_low", -1) > 0) if has_patterns else False
                res_k = {"gate_pass_primary": gate_ok, "patterns_used_by_trained_model": patterns_used, "scores": {}, "timing_s": {}}
                # exact attribution of the reference model: noise ceiling
                Wt = spec.weights(kind)
                exact = Wt[None] * (X - spec.x0)
                exact_pf = Wt[None] * (Xpf - spec.x0)
                sc = score_maps(exact, exact_pf, W, zero_ch)
                res_k["scores"]["reference_exact"] = {k: unit_mean_ci(v, unit_ids, args.seed) for k, v in sc.items()}
                for model_name, model in (("trained", trained), ("reference", ref)):
                    for meth in ("integrated_gradients", "feature_occlusion", "timeshap"):
                        t0 = time.perf_counter()
                        if meth == "timeshap":
                            idx = sorted(ts_idx)
                            per_seed = []
                            seeds_here = ts_seeds if (model_name == "trained" or args.timeshap_seeds_reference is None) else args.timeshap_seeds_reference
                            for s in seeds_here:
                                A = M.timeshap(model, X[idx], spec.x0, ctx.device, seed=s, l1_reg=l1)
                                Apf = M.timeshap(model, Xpf[idx], spec.x0, ctx.device, seed=s, l1_reg=l1) if has_patterns else A
                                per_seed.append(score_maps(A, Apf, [W[i] for i in idx], zero_ch))
                                np.savez_compressed(maps_dir / f"{ds}_{kind}_{model_name}_{meth}_seed{s}.npz", A=A, Apf=Apf, idx=np.array(idx))
                            sc = per_seed[0]
                            uid = [unit_ids[i] for i in idx]
                            res_k["scores"][f"{model_name}/{meth}"] = {k: unit_mean_ci(v, uid, args.seed) for k, v in sc.items()}
                            res_k["scores"][f"{model_name}/{meth}"]["seed_spread"] = {k: [float(np.nanmean(ps[k])) for ps in per_seed] for k in sc}
                        else:
                            fn = M.integrated_gradients if meth == "integrated_gradients" else M.feature_occlusion
                            A = fn(model, X, baseline, ctx.device)
                            Apf = fn(model, Xpf, baseline, ctx.device) if has_patterns else A
                            np.savez_compressed(maps_dir / f"{ds}_{kind}_{model_name}_{meth}.npz", A=A, Apf=Apf)
                            sc = score_maps(A, Apf, W, zero_ch)
                            res_k["scores"][f"{model_name}/{meth}"] = {k: unit_mean_ci(v, unit_ids, args.seed) for k, v in sc.items()}
                        res_k["timing_s"][f"{model_name}/{meth}"] = time.perf_counter() - t0
                        print(f"[s8] {ds} {kind} {model_name}/{meth}: rank {res_k['scores'][f'{model_name}/{meth}']['rank']['mean']} "
                              f"({res_k['timing_s'][f'{model_name}/{meth}']:.0f}s)", flush=True)
                        if model_name == "reference" and meth in ("integrated_gradients", "feature_occlusion"):
                            err = float(np.max(np.abs(A - exact)))
                            ct.require(f"{ds} [{kind}]: {meth} on the reference model equals w(x - x0)", err < 1e-3 * max(1.0, np.abs(exact).max()), "< 1e-3 relative", f"{err:.2e}")
                # C4 secondary: TimeSHAP on the trained model from the conventional average event (per-channel median over
                # training windows, timeshap calc_avg_event convention), scored against the ground truth for that baseline
                if args.secondary_background and kind == "recency":
                    train_units = [u for u in units if split[u.index] == "train"]
                    avg_event = np.median(np.concatenate([u.x for u in train_units]), axis=0)
                    idx = sorted(ts_idx)
                    A = M.timeshap(trained, X[idx], avg_event, ctx.device, seed=ts_seeds[0], l1_reg=l1)
                    Apf = M.timeshap(trained, Xpf[idx], avg_event, ctx.device, seed=ts_seeds[0], l1_reg=l1) if has_patterns else A
                    Wb = []
                    for i in idx:
                        ui, e = picks[i]
                        m_win = eligible[ui].m[e - L:e]  # graded field from baseline b on the pattern-free window: w (m - b) (C4)
                        Wb.append({"unit": ui, "graded": spec.weights(kind) * (m_win - avg_event), "sparse_mask": W[i]["sparse_mask"]})
                    scb = score_maps(A, Apf, Wb, zero_ch)
                    res_k["secondary_average_event"] = {"background_event": dict(zip(spec.channels, avg_event.tolist())),
                                                        "scores": {k: unit_mean_ci(v, [unit_ids[i] for i in idx], args.seed) for k, v in scb.items()}}
                # void flags
                res_k["void"] = {"trained_all": None if gate_ok else "primary model below the accuracy gate",
                                 "trained_retrieval": ("no inserted patterns (D05)" if not has_patterns else (None if patterns_used else "pattern term not used by the trained model (S6 ablation; D21)"))}
                # identifiability floor: IG and occlusion on the ten ensemble members
                if not args.skip_ensemble:
                    floor = {"integrated_gradients": [], "feature_occlusion": []}
                    for cname in ("A", "B"):
                        for ms in range(5):
                            path = ARTIFACTS_DIR / "s6_usability" / "models" / f"{ds}_{kind}_{cname}_seed{ms}.pt"
                            mm = M.RawSpaceModel(load_member(path, ctx.device))
                            for meth, fn in (("integrated_gradients", M.integrated_gradients), ("feature_occlusion", M.feature_occlusion)):
                                A = fn(mm, X, baseline, ctx.device)
                                Apf = fn(mm, Xpf, baseline, ctx.device) if has_patterns else A
                                sc = score_maps(A, Apf, W, zero_ch)
                                floor[meth].append({"member": f"{cname}{ms}", "rank": float(np.nanmean([np.nanmean(np.array(sc["rank"])[np.array(unit_ids) == u]) for u in set(unit_ids)])),
                                                    "zero_mass": float(np.nanmean(sc["zero_mass"]))})
                    res_k["identifiability_floor"] = {m: {"members": v, "rank_min": min(x["rank"] for x in v), "rank_median": float(np.median([x["rank"] for x in v])),
                                                          "rank_max": max(x["rank"] for x in v), "rank_iqr": float(np.subtract(*np.percentile([x["rank"] for x in v], [75, 25])))}
                                                      for m, v in floor.items()}
                results[ds]["weightings"][kind] = res_k
                write_json(results, out / "tables" / "reference_values.json")
            ct.require(f"{ds}: TimeSHAP background instance recorded", "timeshap_background_event" in results[ds], "recorded", "recorded")
        with rec.section("figures"):
            for ds in args.datasets:
                save_figure(viz.method_scores(ds, results[ds]), out / "figures" / f"{ds.lower()}_score_distributions")
        code = ct.finalize(out)
        (out / "logs" / "checks.md").write_text(ct.markdown() + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
