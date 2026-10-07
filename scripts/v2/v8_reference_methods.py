#!/usr/bin/env python
"""V8 (brief "DegradX v2", X7) — reference values for IG, feature occlusion and TimeSHAP at the full declared scale.

Declarations r3 v2.timeshap_full_scale. Per profile, on 120 windows of V4 generated test units (generation seed 0) drawn
with v1's seeded rule (stream evaluation/s8/<profile>), from the pristine baseline (C4):
  primary trained model (V6 A/seed 0)  TimeSHAP 3 seeds x {recency, uniform}; IG and occlusion
  reference model                      TimeSHAP 3 seeds x {recency, uniform}; IG and occlusion (a correctness check: for the
                                       linear reference model IG, occlusion and exact Shapley all equal w(x - x0))
  average-event background (trained)   TimeSHAP 3 seeds x recency, scored against phi*(xbar)
  ensemble floor, all ten V6 members   TimeSHAP seed 0 x recency; IG and occlusion x {recency, uniform}
On a profile with inserted patterns the first three rows also explain the pattern-free counterpart window; the floor runs on
the counterpart only. No D23 reduction: windows, seeds and nsamples are never reduced here.

Modes (run in this order; each is resumable):
  --profile-window       cProfile of one TimeSHAP window (coalition sampling / model evaluation / LassoLarsIC / solve)
  --benchmark            throughput for 1, 2, 4, 6, 8, 12 workers, GPU vs CPU model evaluation, model batch sizes
  --equivalence          20 windows sequential vs the chosen parallel configuration (<= 1e-10 max abs difference)
  --project              projected wall time of all remaining TimeSHAP jobs from the measured throughput (> 36 h: stop)
  --run                  all jobs, checkpointed per window under data/v2/attributions/timeshap_ckpt
  --score                IG / occlusion / exact maps, scores, ensemble ranges, readings; Table 6 inputs
Outputs in ``artifacts/v2/v8_reference_methods``.
"""

from __future__ import annotations

import cProfile
import io
import json
import pickle
import pstats
import sys
import time

import numpy as np
from scipy.stats import bootstrap

import _common as C
from degradx import ARTIFACTS_V2, DATA_V2
from degradx.attribution import methods as M
from degradx.attribution import parallel_timeshap as PT
from degradx.generator.generate import Profile
from degradx.metrics.scores import channel_allocation_error, rank_agreement, retrieval_ap, temporal_profile_error, zero_weight_mass
from degradx.models.lstm import LSTMRegressor, Standardiser, TrainedModel
from degradx.targets.decomposable import TargetSpec, unit_targets
from degradx.utils.checks import CheckTable
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.io import write_json
from degradx.utils.provenance import RunRecord
from degradx.utils.seeding import rng

MODELS_DIR = ARTIFACTS_V2 / "v6_usability" / "models"
CKPT = DATA_V2 / "attributions" / "timeshap_ckpt"
METHODS = ("integrated_gradients", "feature_occlusion", "timeshap")
MEMBERS = [f"{c}{s}" for c in ("A", "B") for s in range(5)]


def load_member(path, device) -> TrainedModel:
    import torch

    ck = torch.load(path, map_location=device, weights_only=False)
    arch = ck["arch"]
    model = LSTMRegressor(len(ck["channels"]), arch["hidden_size"], arch["num_layers"]).to(device)
    model.load_state_dict(ck["state_dict"])
    sc = ck["scaler"]
    return TrainedModel(model, Standardiser(np.asarray(sc["mean"]), np.asarray(sc["std"]), float(sc["y_mean"]), float(sc["y_std"])), {}, device)


def select_windows(test_units, spec, n_windows, g):
    """v1 S8 rule (s8_reference_methods.select_windows): stratified across units."""
    eligible = [u for u in test_units if u.T >= spec.L]
    per = int(np.ceil(n_windows / len(eligible)))
    picks = []
    for ui, u in enumerate(eligible):
        ends = np.arange(spec.L, u.T + 1)
        for e in np.sort(g.choice(ends, size=min(per, len(ends)), replace=False)):
            picks.append((ui, int(e)))
    idx = np.sort(g.choice(len(picks), size=min(n_windows, len(picks)), replace=False))
    return eligible, [picks[i] for i in idx]


class ProfileSetup:
    """Everything one profile needs: windows, ground truth, model specs, backgrounds."""

    def __init__(self, ds, dd, seed, weightings):
        self.ds = ds
        prof = C.v2_profile(ds)
        units, table = pickle.loads((DATA_V2 / "generated" / ds / "seed0.pkl").read_bytes())
        split = dict(zip(table["index"], table["split"]))
        test = [u for u in units if split[u.index] == "test"]
        train = [u for u in units if split[u.index] == "train"]
        self.P = Profile.from_json(prof, np.array([0.0]))
        beta, L = dd["target"]["weights"]["beta"]["value"], int(dd["target"]["window_length_L"]["value"])
        self.spec = TargetSpec.build(self.P, beta, L, 6.0)
        self.L, self.C = L, len(self.spec.channels)
        self.has_patterns = any(len(u.patterns) for u in units)
        self.eligible, self.picks = select_windows(test, self.spec, int(dd["attribution"]["windows_scored_per_profile"]), rng(seed, "evaluation", "s8", ds))
        n_ts40 = 40  # D23's subset rule, used only for the declared X7_values_hold reading
        self.d23_subset = sorted(np.sort(rng(seed, "evaluation", "s8-timeshap", ds).choice(len(self.picks), size=n_ts40, replace=False)).tolist())
        self.unit_ids = [ui for ui, _ in self.picks]
        self.weightings = weightings
        self.W = {}
        for kind in weightings:
            rows = []
            for ui, e in self.picks:
                tg = unit_targets(self.eligible[ui], self.spec, kind, ends=np.array([e]))
                rows.append({"x": tg["x"][0], "xpf": tg["x_pattern_free"][0], "graded": tg["graded"][0], "sparse_mask": tg["sparse"][0] != 0, "phi": tg["phi_star"][0]})
            self.W[kind] = rows
        self.avg_event = np.median(np.concatenate([u.x for u in train]), axis=0)
        self.x0 = self.spec.x0.copy()
        self.zero_ch = np.flatnonzero(self.spec.kappa == 0)
        self.weighted_idx = np.flatnonzero(self.spec.kappa != 0)

    def X(self, kind, pf=False):
        return np.stack([w["xpf" if pf else "x"] for w in self.W[kind]]).astype(np.float32)

    def model_specs(self):
        specs = {}
        for kind in self.weightings:
            specs[f"{self.ds}/{kind}/reference"] = PT.ModelSpec("reference", None, self.spec.weights(kind), self.x0)
            for mem in MEMBERS:
                specs[f"{self.ds}/{kind}/{mem}"] = PT.ModelSpec("trained", str(MODELS_DIR / f"{self.ds}_{kind}_{mem[0]}_seed{mem[1:]}.pt"))
        return specs

    def windows(self):
        out = {}
        for kind in self.weightings:
            out[f"{self.ds}/{kind}/x"] = self.X(kind)
            out[f"{self.ds}/{kind}/xpf"] = self.X(kind, pf=True)
        return out

    def backgrounds(self):
        return {f"{self.ds}/pristine": self.x0, f"{self.ds}/average_event": self.avg_event}

    def jobs(self, ts_seeds, primary="recency"):
        """The declared design (v2.timeshap_full_scale.design_per_profile)."""
        J = []
        n = len(self.picks)
        inputs = ["x", "xpf"] if self.has_patterns else ["x"]
        for kind in self.weightings:
            for inp in inputs:
                for s in ts_seeds:
                    for i in range(n):
                        J.append(PT.Job(f"{self.ds}/{kind}/trained/A0/pristine/{inp}", f"{self.ds}/{kind}/A0", f"{self.ds}/{kind}/{inp}", i, s, f"{self.ds}/pristine"))
                        J.append(PT.Job(f"{self.ds}/{kind}/reference/pristine/{inp}", f"{self.ds}/{kind}/reference", f"{self.ds}/{kind}/{inp}", i, s, f"{self.ds}/pristine"))
        for inp in inputs:
            for s in ts_seeds:
                for i in range(n):
                    J.append(PT.Job(f"{self.ds}/{primary}/trained/A0/average_event/{inp}", f"{self.ds}/{primary}/A0", f"{self.ds}/{primary}/{inp}", i, s, f"{self.ds}/average_event"))
        floor_inp = "xpf" if self.has_patterns else "x"
        for mem in MEMBERS:
            if mem == "A0" and floor_inp == "x":
                continue  # identical to the primary row's seed-0 maps (same model, window, seed and background): reused, not recomputed
            for i in range(n):
                J.append(PT.Job(f"{self.ds}/{primary}/trained/{mem}/pristine/{floor_inp}", f"{self.ds}/{primary}/{mem}", f"{self.ds}/{primary}/{floor_inp}", i, ts_seeds[0], f"{self.ds}/pristine"))
        return J


def unit_mean_ci(values, unit_ids, seed, n_resamples):
    v, u = np.asarray(values, float), np.asarray(unit_ids)
    uu = np.unique(u[np.isfinite(v)])
    means = np.array([np.nanmean(v[u == k]) for k in uu])
    if len(means) < 3:
        return {"mean": float(np.nanmean(means)) if len(means) else None, "ci_low": None, "ci_high": None, "units": int(len(means))}
    ci = bootstrap((means,), np.mean, n_resamples=n_resamples, method="BCa", random_state=np.random.default_rng(seed)).confidence_interval
    return {"mean": float(means.mean()), "ci_low": float(ci.low), "ci_high": float(ci.high), "units": int(len(means))}


def score_maps(A, Apf, rows, zero_ch, weighted_idx, graded_key="graded"):
    out = {"rank": [], "allocation": [], "temporal": [], "zero_mass": [], "retrieval": [], "temporal_excluded": 0}
    for i, w in enumerate(rows):
        g = w[graded_key]
        out["rank"].append(rank_agreement(Apf[i], g))
        out["allocation"].append(channel_allocation_error(Apf[i], g))
        t, ex = temporal_profile_error(Apf[i], g, weighted_idx)
        out["temporal"].append(t)
        out["temporal_excluded"] += ex
        out["zero_mass"].append(zero_weight_mass(A[i], zero_ch))
        out["retrieval"].append(retrieval_ap(A[i] - Apf[i], w["sparse_mask"]) if w["sparse_mask"].any() else np.nan)
    return out


def summarise_scores(sc, unit_ids, seed, n_boot, has_patterns):
    keys = ["rank", "allocation", "temporal", "zero_mass"] + (["retrieval"] if has_patterns else [])
    return {**{k: unit_mean_ci(sc[k], unit_ids, seed, n_boot) for k in keys}, "temporal_excluded": sc["temporal_excluded"]}


def main() -> int:
    p = stage_parser(__doc__, "v2/v8_reference_methods")
    p.add_argument("--datasets", nargs="*", default=["MATR", "HUST"])
    p.add_argument("--profile-config", nargs="*", default=[])
    for m in ("profile-window", "benchmark", "equivalence", "project", "run", "score"):
        p.add_argument(f"--{m}", action="store_true")
    p.add_argument("--workers", type=int, default=None, help="TimeSHAP pool size (default: the benchmark's choice)")
    p.add_argument("--ts-device", default=None, help="model evaluation device inside TimeSHAP workers (default: the benchmark's choice)")
    p.add_argument("--chunk", type=int, default=None)
    p.add_argument("--bench-workers", nargs="*", type=int, default=[1, 2, 4, 6, 8, 12])
    args = p.parse_args()
    for kv in args.profile_config:
        C.register_profile(*kv.split("="))
    ctx = StageContext.from_args(args)
    decl, dd = ctx.declarations, ctx.declarations["declared_by_design"]
    sc_w = dd["v2"]["scope"]["weightings"]
    weightings = [sc_w["primary"], sc_w["sensitivity"]]
    ts_cfg = dd["attribution"]["methods"]["timeshap"]
    nsamples, l1 = int(ts_cfg["nsamples"]), ts_cfg["l1_reg"]
    ts_seeds = dd["statistics"]["seeds"]["attribution_sampling"]
    n_boot = int(dd["v2"]["statistics"]["bootstrap_n_resamples"])
    if args.dry_run:
        print(f"plan: V8 for {args.datasets}")
        return 0
    out, ct = ctx.out_dir, CheckTable()
    feas_f = out / "tables" / "feasibility.json"
    feas = json.loads(feas_f.read_text()) if feas_f.exists() else {}
    setups = {ds: ProfileSetup(ds, dd, args.seed, weightings) for ds in args.datasets}
    specs, wins, bgs = {}, {}, {}
    for s_ in setups.values():
        specs.update(s_.model_specs())
        wins.update(s_.windows())
        bgs.update(s_.backgrounds())
    all_jobs = [j for s_ in setups.values() for j in s_.jobs(ts_seeds)]
    with RunRecord("v2/v8_reference_methods", out, {"config": ctx.config, "datasets": args.datasets, "nsamples": nsamples, "l1_reg": str(l1), "seeds": ts_seeds},
                   {"evaluation": args.seed, "attribution_sampling": ts_seeds, "generation": 0}, ctx.device) as rec:
        # ---------------------------------------------------------------- profile one window
        if args.profile_window:
            ds = args.datasets[0]
            PT._init_worker(specs, bgs, wins, "cuda" if ctx.device == "cuda" else "cpu", 4096, nsamples, l1, 1)
            job = next(j for j in all_jobs if j.model_key.endswith("/A0") and j.background_key.endswith("pristine"))
            PT.explain_one(job)  # warm-up (imports, model load)
            pr = cProfile.Profile()
            pr.enable()
            t0 = time.perf_counter()
            PT.explain_one(job)
            el = time.perf_counter() - t0
            pr.disable()
            st = pstats.Stats(pr)
            tot = {k: 0.0 for k in ("coalition_sampling", "model_evaluation", "lasso_lars_ic", "solve")}
            for (fname, _ln, func), (_cc, _nc, _tt, cum, _callers) in st.stats.items():
                if func == "add_sample" and "timeshap_kernel" in fname:
                    tot["coalition_sampling"] = max(tot["coalition_sampling"], cum)
                elif func == "run" and "timeshap_kernel" in fname:
                    tot["model_evaluation"] = max(tot["model_evaluation"], cum)
                elif func == "fit" and "_least_angle" in fname:
                    tot["lasso_lars_ic"] = max(tot["lasso_lars_ic"], cum)
                elif func == "lstsq" and "linalg" in fname:
                    tot["solve"] += cum
            s = io.StringIO()
            pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(30)
            (out / "logs" / "cprofile_one_window.txt").write_text(s.getvalue())
            feas["profile_one_window"] = {"profile": ds, "device": ctx.device, "wall_s": el, "split_s": tot, "split_share": {k: v / el for k, v in tot.items()}}
            write_json(feas, feas_f)
            print("[v8] one window:", json.dumps(feas["profile_one_window"], indent=1), flush=True)
        # ---------------------------------------------------------------- throughput benchmark
        if args.benchmark:
            bench_dir = DATA_V2 / "attributions" / "benchmark"
            ds = args.datasets[0]
            pool = [j for j in all_jobs if j.model_key.endswith("/A0") and j.background_key.endswith("pristine") and j.seed == ts_seeds[0]]
            rows_b = []
            configs = [(w, "cpu", 4096) for w in args.bench_workers] + [(w, "cuda", 4096) for w in args.bench_workers if w <= 8] + \
                      [(8, d, ch) for d in ("cpu", "cuda") for ch in (1024, 16384, 32768)]
            for w, dev, ch in configs:
                if dev == "cuda" and ctx.device != "cuda":
                    continue
                import shutil

                shutil.rmtree(bench_dir, ignore_errors=True)
                jobs_b = pool[:max(2 * w, 4)]
                t0 = time.perf_counter()
                r_ = PT.run_jobs(jobs_b, model_specs=specs, backgrounds=bgs, windows=wins, checkpoint_dir=bench_dir, workers=w, device=dev, chunk=ch,
                                 nsamples=nsamples, l1_reg=l1, label=f"bench w{w} {dev} chunk{ch}", log_every=10 ** 6)
                rows_b.append({"workers": w, "device": dev, "chunk": ch, "windows": len(jobs_b), "wall_s": time.perf_counter() - t0,
                               "windows_per_hour": r_["windows_per_hour"], "mean_window_s": r_["mean_window_s"]})
                print(f"[v8] bench {rows_b[-1]}", flush=True)
                feas["benchmark"] = rows_b
                write_json(feas, feas_f)
            best = max(rows_b, key=lambda r: r["windows_per_hour"] or 0)
            feas["chosen"] = {"workers": best["workers"], "device": best["device"], "chunk": best["chunk"], "windows_per_hour": best["windows_per_hour"]}
            write_json(feas, feas_f)
        chosen = feas.get("chosen", {})
        workers = args.workers or chosen.get("workers", 8)
        ts_dev = args.ts_device or chosen.get("device", "cpu")
        chunk = args.chunk or chosen.get("chunk", 4096)
        # ---------------------------------------------------------------- equivalence check
        if args.equivalence:
            eq_seq, eq_par = DATA_V2 / "attributions" / "equivalence_seq", DATA_V2 / "attributions" / "equivalence_par"
            import shutil

            shutil.rmtree(eq_seq, ignore_errors=True)
            shutil.rmtree(eq_par, ignore_errors=True)
            jobs_e = [j for j in all_jobs if j.model_key.endswith("/A0") and j.background_key.endswith("pristine") and j.seed == ts_seeds[0]][:20]
            PT.run_jobs(jobs_e, model_specs=specs, backgrounds=bgs, windows=wins, checkpoint_dir=eq_seq, workers=1, device=ts_dev, chunk=chunk, nsamples=nsamples,
                        l1_reg=l1, label="equivalence sequential")
            PT.run_jobs(jobs_e, model_specs=specs, backgrounds=bgs, windows=wins, checkpoint_dir=eq_par, workers=workers, device=ts_dev, chunk=chunk, nsamples=nsamples,
                        l1_reg=l1, label="equivalence parallel")
            a = PT.collect(jobs_e, eq_seq)
            b = PT.collect(jobs_e, eq_par)
            dmax = max(float(np.max(np.abs(a[r][s] - b[r][s]))) for r in a for s in a[r])
            # also against the in-process path used in v1 (methods.timeshap), on the first window
            j0 = jobs_e[0]
            mdl = M.RawSpaceModel(load_member(specs[j0.model_key].path, ts_dev))
            v1path = M.timeshap(mdl, wins[j0.window_key][j0.index:j0.index + 1], bgs[j0.background_key], ts_dev, seed=j0.seed, nsamples=nsamples, l1_reg=l1)[0]
            d_v1 = float(np.max(np.abs(v1path - a[j0.row][j0.seed][0])))
            feas["equivalence"] = {"windows": len(jobs_e), "workers": workers, "device": ts_dev, "chunk": chunk, "max_abs_diff_sequential_vs_parallel": dmax,
                                   "max_abs_diff_vs_v1_code_path_first_window": d_v1, "passes": bool(dmax <= 1e-10)}
            write_json(feas, feas_f)
            ct.require("V8: sequential and parallel TimeSHAP agree on 20 windows (<= 1e-10 max abs difference)", dmax <= 1e-10, "<= 1e-10", f"{dmax:.2e}")
            print(f"[v8] equivalence max |diff| {dmax:.3e} (vs v1 code path {d_v1:.3e})", flush=True)
        # ---------------------------------------------------------------- projection
        if args.project:
            todo = [j for j in all_jobs if not PT.job_path(CKPT, j).exists()]
            wph = chosen.get("windows_per_hour")
            proj_h = len(todo) / wph if wph else None
            feas["projection"] = {"jobs_total": len(all_jobs), "jobs_remaining": len(todo), "windows_per_hour": wph, "projected_hours": proj_h,
                                  "threshold_hours": 36, "within_threshold": bool(proj_h is not None and proj_h <= 36),
                                  "per_profile_jobs": {ds: sum(j.row.startswith(ds + "/") for j in all_jobs) for ds in args.datasets},
                                  "recorded": time.strftime("%Y-%m-%d %H:%M:%S")}
            write_json(feas, feas_f)
            print(f"[v8] projection: {len(todo)} jobs at {wph} windows/h = {proj_h} h", flush=True)
            if proj_h is None or proj_h > 36:
                print("STOP AND REPORT (brief §6): projected TimeSHAP wall time exceeds 36 h", flush=True)
                return 2
        # ---------------------------------------------------------------- full run
        if args.run:
            r_ = PT.run_jobs(all_jobs, model_specs=specs, backgrounds=bgs, windows=wins, checkpoint_dir=CKPT, workers=workers, device=ts_dev, chunk=chunk,
                             nsamples=nsamples, l1_reg=l1, label="v8 full run")
            feas.setdefault("runs", []).append({**r_, "datasets": args.datasets, "finished": time.strftime("%Y-%m-%d %H:%M:%S")})
            write_json(feas, feas_f)
        # ---------------------------------------------------------------- scoring
        if args.score:
            res_f = out / "tables" / "reference_values.json"
            results = json.loads(res_f.read_text()) if res_f.exists() else {}
            usab = {}
            for ds in args.datasets:
                f = ARTIFACTS_V2 / "v6_usability" / "tables" / f"usability_{ds}.json"
                usab.update(json.loads(f.read_text()) if f.exists() else {})
            maps_dir = DATA_V2 / "attributions" / "maps"
            maps_dir.mkdir(parents=True, exist_ok=True)
            for ds, S in setups.items():
                jobs_ds = [j for j in all_jobs if j.row.startswith(ds + "/")]
                ts_maps = PT.collect(jobs_ds, CKPT)
                res = {"windows": len(S.picks), "units": len(set(S.unit_ids)), "baseline": dict(zip(S.spec.channels, S.x0.tolist())),
                       "average_event": dict(zip(S.spec.channels, S.avg_event.tolist())), "has_patterns": S.has_patterns, "weightings": {}}
                for kind in weightings:
                    rows = S.W[kind]
                    X, Xpf = S.X(kind), S.X(kind, pf=True)
                    exact = S.spec.weights(kind)[None] * (X - S.x0)
                    exact_pf = S.spec.weights(kind)[None] * (Xpf - S.x0)
                    u6 = usab.get(ds, {}).get(kind, {})
                    gate = u6.get("channel_usage_gate", {})
                    r = {"scores": {}, "gate_pass_primary": u6.get("gate_pass_primary"), "channel_usage_void": gate.get("void_channel_level_scores"),
                         "unused_weighted_channels": gate.get("unused_on_primary", [])}
                    r["scores"]["reference_exact"] = summarise_scores(score_maps(exact, exact_pf, rows, S.zero_ch, S.weighted_idx), S.unit_ids, args.seed, n_boot, S.has_patterns)
                    baseline = np.broadcast_to(S.x0, (S.L, S.C)).copy()
                    models = {"trained": M.RawSpaceModel(load_member(MODELS_DIR / f"{ds}_{kind}_A_seed0.pt", ctx.device)),
                              "reference": M.ReferenceModel(S.spec.weights(kind), S.x0)}
                    for mname, mdl in models.items():
                        for meth, fn in (("integrated_gradients", M.integrated_gradients), ("feature_occlusion", M.feature_occlusion)):
                            A = fn(mdl, X, baseline, ctx.device)
                            Apf = fn(mdl, Xpf, baseline, ctx.device) if S.has_patterns else A
                            np.savez_compressed(maps_dir / f"{ds}_{kind}_{mname}_{meth}.npz", A=A, Apf=Apf)
                            r["scores"][f"{mname}/{meth}"] = summarise_scores(score_maps(A, Apf, rows, S.zero_ch, S.weighted_idx), S.unit_ids, args.seed, n_boot, S.has_patterns)
                            if mname == "reference":
                                err = float(np.max(np.abs(A - exact)))
                                ct.require(f"{ds} [{kind}]: {meth} on the reference model equals w(x - x0) (correctness check)", err < 1e-3 * max(1.0, np.abs(exact).max()),
                                           "< 1e-3 relative", f"{err:.2e}")
                        # TimeSHAP: three seeds
                        row = f"{ds}/{kind}/{'trained/A0' if mname == 'trained' else 'reference'}/pristine"
                        per_seed = []
                        for s in ts_seeds:
                            A = ts_maps[f"{row}/x"][s]
                            Apf = ts_maps[f"{row}/xpf"][s] if S.has_patterns else A
                            np.savez_compressed(maps_dir / f"{ds}_{kind}_{mname}_timeshap_seed{s}.npz", A=A, Apf=Apf)
                            per_seed.append(score_maps(A, Apf, rows, S.zero_ch, S.weighted_idx))
                            if mname == "reference":
                                err = float(np.max(np.abs(A - exact)))
                                ct.require(f"{ds} [{kind}]: TimeSHAP seed {s} on the reference model equals w(x - x0) (correctness check)",
                                           err < 1e-3 * max(1.0, np.abs(exact).max()), "< 1e-3 relative", f"{err:.2e}")
                        r["scores"][f"{mname}/timeshap"] = summarise_scores(per_seed[0], S.unit_ids, args.seed, n_boot, S.has_patterns)
                        r["scores"][f"{mname}/timeshap"]["seed_spread"] = {k: [float(np.nanmean([np.nanmean(np.array(ps[k])[np.array(S.unit_ids) == u]) for u in set(S.unit_ids)]))
                                                                              for ps in per_seed] for k in ("rank", "allocation", "temporal", "zero_mass")}
                        r["scores"][f"{mname}/timeshap"]["seed_means"] = {k: [summarise_scores(ps, S.unit_ids, args.seed, n_boot, S.has_patterns)[k]["mean"] for ps in per_seed]
                                                                         for k in ("rank", "allocation", "temporal")}
                        # declared X7_values_hold: the D23 40-window subset mean inside the full 120-window interval
                        sub = S.d23_subset
                        sub_sc = {k: [per_seed[0][k][i] for i in sub] for k in ("rank", "allocation", "temporal")}
                        r["scores"][f"{mname}/timeshap"]["d23_subset"] = {k: unit_mean_ci(v, [S.unit_ids[i] for i in sub], args.seed, n_boot)["mean"] for k, v in sub_sc.items()}
                        full = r["scores"][f"{mname}/timeshap"]
                        r["scores"][f"{mname}/timeshap"]["x7_values_hold"] = {k: bool(full[k]["ci_low"] is not None and full[k]["ci_low"] <= full["d23_subset"][k] <= full[k]["ci_high"])
                                                                             for k in ("rank", "allocation", "temporal")}
                    # average-event background (recency): scored against phi*(xbar)
                    if kind == weightings[0]:
                        rows_b = []
                        for i, (ui, e) in enumerate(S.picks):
                            m_win = S.eligible[ui].m[e - S.L:e]
                            rows_b.append({"graded": S.spec.weights(kind) * (m_win - S.avg_event), "sparse_mask": rows[i]["sparse_mask"]})
                        per_seed = []
                        for s in ts_seeds:
                            A = ts_maps[f"{ds}/{kind}/trained/A0/average_event/x"][s]
                            Apf = ts_maps[f"{ds}/{kind}/trained/A0/average_event/xpf"][s] if S.has_patterns else A
                            per_seed.append(score_maps(A, Apf, rows_b, S.zero_ch, S.weighted_idx))
                        r["secondary_average_event"] = {"scores": summarise_scores(per_seed[0], S.unit_ids, args.seed, n_boot, S.has_patterns),
                                                        "seed_means": {k: [float(np.nanmean(ps[k])) for ps in per_seed] for k in ("rank", "allocation", "temporal")}}
                    # identifiability floor: IG and occlusion on all ten members (both weightings), TimeSHAP on all ten (recency)
                    floor = {m: [] for m in METHODS}
                    for mem in MEMBERS:
                        mm = M.RawSpaceModel(load_member(MODELS_DIR / f"{ds}_{kind}_{mem[0]}_seed{mem[1:]}.pt", ctx.device))
                        for meth, fn in (("integrated_gradients", M.integrated_gradients), ("feature_occlusion", M.feature_occlusion)):
                            Apf = fn(mm, Xpf, baseline, ctx.device)
                            A = fn(mm, X, baseline, ctx.device) if S.has_patterns else Apf
                            sc_ = score_maps(A, Apf, rows, S.zero_ch, S.weighted_idx)
                            floor[meth].append({"member": mem, **{k: unit_mean_ci(sc_[k], S.unit_ids, args.seed, 1)["mean"] for k in ("rank", "allocation", "temporal", "zero_mass")}})
                        if kind == weightings[0]:
                            inp = "xpf" if S.has_patterns else "x"
                            key = f"{ds}/{kind}/trained/{mem}/pristine/{inp}" if not (mem == "A0" and inp == "x") else f"{ds}/{kind}/trained/A0/pristine/x"
                            Apf = ts_maps[key][ts_seeds[0]]
                            sc_ = score_maps(Apf, Apf, rows, S.zero_ch, S.weighted_idx)
                            floor["timeshap"].append({"member": mem, **{k: unit_mean_ci(sc_[k], S.unit_ids, args.seed, 1)["mean"] for k in ("rank", "allocation", "temporal", "zero_mass")}})
                    r["identifiability_floor"] = {}
                    for meth, v in floor.items():
                        if not v:
                            continue
                        r["identifiability_floor"][meth] = {"members": v, **{f"{k}_{q}": f(x[k] for x in v) for k in ("rank", "allocation", "temporal")
                                                                             for q, f in (("min", min), ("max", max))},
                                                            **{f"{k}_median": float(np.median([x[k] for x in v])) for k in ("rank", "allocation", "temporal")}}
                    # declared X7_floor reading: ensemble range vs the largest gap between methods on the primary trained model
                    r["x7_floor"] = {}
                    for k in ("rank", "allocation", "temporal"):
                        vals = [r["scores"][f"trained/{m}"][k]["mean"] for m in METHODS]
                        gap = float(max(vals) - min(vals))
                        rngs = {m: float(r["identifiability_floor"][m][f"{k}_max"] - r["identifiability_floor"][m][f"{k}_min"]) for m in r["identifiability_floor"]}
                        r["x7_floor"][k] = {"largest_method_gap": gap, "ensemble_range": rngs, "no_ordering_supported": bool(any(v > gap for v in rngs.values()))}
                    r["method_ordering"] = {k: sorted(METHODS, key=lambda m: r["scores"][f"trained/{m}"][k]["mean"], reverse=SCORE_SIGN[k] > 0) for k in ("rank", "allocation", "temporal")}
                    res["weightings"][kind] = r
                    results[ds] = res
                    write_json(results, res_f)
                ct.require(f"{ds}: all declared TimeSHAP jobs present", all(PT.job_path(CKPT, j).exists() for j in jobs_ds), "all", "all")
        code = ct.finalize(out)
        (out / "logs" / "checks.md").write_text(ct.markdown() + "\n")
    return code


SCORE_SIGN = {"rank": +1, "allocation": -1, "temporal": -1}

if __name__ == "__main__":
    sys.exit(main())
