#!/usr/bin/env python
"""V7 (brief "DegradX v2", X5) — RQ3, score validation by the degraded-map test, and the X5 scores on the saved v1 maps.

Part A (declarations r3 v2.scoring): the attribution ground truth of generated test units (V4, generation seed 0; 20
windows per unit, as v1 part one) is degraded by the five v1 operators over their declared grids, under recency and
uniform weighting. Scores on the pattern-free counterpart map against the graded field (D01):
  rank agreement (higher is better; kept for continuity), channel allocation error and temporal profile error (lower is
  better, X5); paired retrieval only where the profile carries patterns.
Per score and operator: the resolution (v1 criterion, sign-aware: for error scores the LOWER bound of the 95% paired BCa
interval of mean(degraded - undegraded) > 0 at this and every larger magnitude; 10 000 resamples), the mean change at the
resolved magnitude, and the declared registers check (mean change >= 10% of |s_chance - s_perfect| at some magnitude and
every larger one; s_chance from fully permuted maps).
Part B: the same scores recomputed on the saved v1 S8 maps (``data/attributions``) against the v1 ground truth regenerated
from ``data/generated`` (recency and uniform; no new attribution). Outputs in ``artifacts/v2/v7_scores``.
"""

from __future__ import annotations

import json
import pickle
import sys

import numpy as np
from scipy.stats import bootstrap

import _common as C
from degradx import ARTIFACTS_DIR, DATA_DIR, DATA_V2
from degradx.generator.generate import Profile
from degradx.metrics.scores import OPERATORS, channel_allocation_error, rank_agreement, retrieval_ap, temporal_profile_error, zero_weight_mass
from degradx.targets.decomposable import TargetSpec, unit_targets
from degradx.utils.checks import CheckTable
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.io import save_figure, write_json
from degradx.utils.provenance import RunRecord
from degradx.utils.seeding import rng

SCORES = {"rank": +1, "allocation": -1, "temporal": -1}  # +1: higher is better, -1: error score (0 perfect)
PERFECT = {"rank": 1.0, "allocation": 0.0, "temporal": 0.0}


def score_window(amap, graded, weighted_idx):
    tpe, excl = temporal_profile_error(amap, graded, weighted_idx)
    return {"rank": rank_agreement(amap, graded), "allocation": channel_allocation_error(amap, graded), "temporal": tpe, "temporal_excluded": excl}


def sample_windows(units, spec, kind, per_unit, g):
    rows = []
    for ui, u in enumerate(units):
        if u.T < spec.L:
            continue
        tg = unit_targets(u, spec, kind)
        idx = np.sort(g.choice(len(tg["y"]), size=min(per_unit, len(tg["y"])), replace=False))
        for i in idx:
            rows.append((ui, tg["phi_star"][i], tg["graded"][i], tg["sparse"][i] != 0))
    return rows


def unit_means(vals, units):
    uu = np.unique(units)
    return uu, np.array([np.nanmean(vals[units == u]) if np.isfinite(vals[units == u]).any() else np.nan for u in uu])


def resolution(unit_scores: dict, grid, sign: int, seed: int, n_resamples: int) -> dict:
    """Paired bootstrap over units of mean(score_m - score_0). Higher-is-better scores (sign +1): resolved at m iff the upper
    bound < 0 at m and every larger magnitude (v1). Error scores (sign -1): the lower bound > 0 likewise."""
    base = unit_scores[grid[0]]
    bound, mean_change = {}, {}
    for m in grid[1:]:
        d = unit_scores[m] - base
        d = d[np.isfinite(d)]
        mean_change[m] = float(np.mean(d)) if len(d) else float("nan")
        if len(d) < 3 or np.allclose(d, d[0]):
            bound[m] = mean_change[m]
            continue
        ci = bootstrap((d,), np.mean, n_resamples=n_resamples, confidence_level=0.95, method="BCa", random_state=np.random.default_rng(seed)).confidence_interval
        bound[m] = float(ci.high) if sign > 0 else float(ci.low)
    ok = {m: np.isfinite(bound[m]) and (bound[m] < 0 if sign > 0 else bound[m] > 0) for m in grid[1:]}
    resolved = next((m for i, m in enumerate(grid[1:]) if all(ok[k] for k in grid[1 + i:])), None)
    return {"bound": bound, "mean_change": mean_change, "resolution": resolved, "change_at_resolution": mean_change.get(resolved) if resolved is not None else None}


def registers(mean_change: dict, grid, chance: float, perfect: float, frac: float = 0.10) -> dict:
    thr = frac * abs(chance - perfect)
    mags = grid[1:]
    big = {m: np.isfinite(mean_change[m]) and abs(mean_change[m]) >= thr for m in mags}
    mag = next((m for i, m in enumerate(mags) if all(big[k] for k in mags[i:])), None)
    return {"threshold": thr, "registering_magnitude": mag, "registers": mag is not None}


def part_a(ds, units, spec, kind, ops, weighted_idx, seed, n_boot, has_patterns, per_unit=20):
    g = rng(seed, "evaluation", "v7", ds, kind)
    W = sample_windows(units, spec, kind, per_unit, g)
    U_ = np.array([w[0] for w in W])
    out = {"windows": len(W), "units": int(len(np.unique(U_)))}
    ch = [score_window(g.permutation(w[2].ravel()).reshape(w[2].shape), w[2], weighted_idx) for w in W]
    out["chance"] = {k: float(np.nanmean([c[k] for c in ch])) for k in SCORES}
    series = {}
    for op, cfg in ops.items():
        grid = cfg["grid"]
        f = OPERATORS[op]
        per = {k: {} for k in SCORES}
        excl = {}
        for mi, mag in enumerate(grid):
            vals = {k: [] for k in SCORES}
            ex = 0
            for wi, (ui, phi, grd, lab) in enumerate(W):
                ga = rng(seed, "evaluation", "v7", ds, kind, op, mi, wi, "a")
                d = f(grd, mag, ga) if op != "added_noise" else f(grd, mag, ga, scale=np.std(grd))
                sw = score_window(d, grd, weighted_idx)
                for k in SCORES:
                    vals[k].append(sw[k])
                ex += sw["temporal_excluded"]
            for k in SCORES:
                _, per[k][mag] = unit_means(np.array(vals[k], float), U_)
            excl[mag] = ex
        s = {"grid": grid, "temporal_channels_excluded": excl}
        for k, sign in SCORES.items():
            res = resolution(per[k], grid, sign, seed, n_boot)
            s[k] = {"mean": [float(np.nanmean(per[k][m])) for m in grid], **res,
                    "registers": registers(res["mean_change"], grid, out["chance"][k], PERFECT[k])}
        series[op] = s
    out["operators"] = series
    return out


# ---- part B: the X5 scores on the saved v1 S8 maps -----------------------------------------------------------------
def v1_windows(ds, kind, seed):
    """Rebuild the v1 S8 windows (same seeded selection) and their v1 ground truth."""
    import importlib.util

    from pathlib import Path

    sp = importlib.util.spec_from_file_location("s8v1", str(Path(__file__).resolve().parents[1] / "s8_reference_methods.py"))
    s8 = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(s8)
    prof = json.loads((ARTIFACTS_DIR / "s3_fit_profiles" / "profiles" / f"{ds}.json").read_text())
    units, table = pickle.loads((DATA_DIR / "generated" / ds / "seed0.pkl").read_bytes())
    split = dict(zip(table["index"], table["split"]))
    test = [u for u in units if split[u.index] == "test"]
    P = Profile.from_json(prof, np.concatenate([u.eps[:, len(prof["declared_used"]["channels_available"]) + 1] for u in units]))
    spec = TargetSpec.build(P, {"capacity": 1 / 3, "charge_time": 1 / 3, "mean_discharge_voltage": 1 / 3}, 24, 6.0)
    eligible, picks = s8.select_windows(test, spec, 120, rng(seed, "evaluation", "s8", ds))
    W = []
    for ui, e in picks:
        tg = unit_targets(eligible[ui], spec, kind, ends=np.array([e]))
        W.append({"unit": ui, "graded": tg["graded"][0], "x": tg["x"][0], "xpf": tg["x_pattern_free"][0]})
    return spec, W


def unit_mean_ci(values, unit_ids, seed, n_resamples):
    v, u = np.asarray(values, float), np.asarray(unit_ids)
    uu = np.unique(u[np.isfinite(v)])
    means = np.array([np.nanmean(v[u == k]) for k in uu])
    if len(means) < 3:
        return {"mean": float(np.nanmean(means)) if len(means) else None, "ci_low": None, "ci_high": None, "units": int(len(means))}
    ci = bootstrap((means,), np.mean, n_resamples=n_resamples, method="BCa", random_state=np.random.default_rng(seed)).confidence_interval
    return {"mean": float(means.mean()), "ci_low": float(ci.low), "ci_high": float(ci.high), "units": int(len(means))}


def part_b(ds, kind, seed, n_boot):
    spec, W = v1_windows(ds, kind, seed)
    widx = np.flatnonzero(spec.kappa != 0)
    zero = np.flatnonzero(spec.kappa == 0)
    uid = [w["unit"] for w in W]
    out = {}
    exact = np.stack([spec.weights(kind) * (w["x"] - spec.x0) for w in W])
    exact_pf = np.stack([spec.weights(kind) * (w["xpf"] - spec.x0) for w in W])  # the counterpart map (D01) on a profile with patterns
    maps = {"reference_exact": {"A": exact, "Apf": exact_pf, "idx": np.arange(len(W))}}
    for f in sorted((DATA_DIR / "attributions").glob(f"{ds}_{kind}_*.npz")):
        name = f.stem[len(f"{ds}_{kind}_"):]
        z = np.load(f)
        maps[name] = {"A": z["A"], "Apf": z["Apf"], "idx": z["idx"] if "idx" in z else np.arange(len(W))}
    for name, mp in maps.items():
        sc = {"rank": [], "allocation": [], "temporal": [], "zero_mass": [], "temporal_excluded": 0}
        for j, i in enumerate(mp["idx"]):
            sw = score_window(mp["Apf"][j], W[i]["graded"], widx)
            for k in ("rank", "allocation", "temporal"):
                sc[k].append(sw[k])
            sc["temporal_excluded"] += sw["temporal_excluded"]
            sc["zero_mass"].append(zero_weight_mass(mp["A"][j], zero))
        u_ = [uid[i] for i in mp["idx"]]
        out[name] = {k: unit_mean_ci(sc[k], u_, seed, n_boot) for k in ("rank", "allocation", "temporal", "zero_mass")}
        out[name]["windows"] = int(len(mp["idx"]))
        out[name]["temporal_excluded"] = sc["temporal_excluded"]
    return out


def main() -> int:
    p = stage_parser(__doc__, "v2/v7_scores")
    p.add_argument("--datasets", nargs="*", default=["MATR", "HUST"])
    p.add_argument("--profile-config", nargs="*", default=[])
    p.add_argument("--v1-datasets", nargs="*", default=["MATR", "HUST", "NASA_PCoE"])
    p.add_argument("--skip-part-a", action="store_true")
    p.add_argument("--skip-part-b", action="store_true")
    args = p.parse_args()
    for kv in args.profile_config:
        C.register_profile(*kv.split("="))
    ctx = StageContext.from_args(args)
    decl, dd = ctx.declarations, ctx.declarations["declared_by_design"]
    sc_w = dd["v2"]["scope"]["weightings"]
    weightings = [sc_w["primary"], sc_w["sensitivity"]]
    if args.dry_run:
        print(f"plan: degraded-map test for {args.datasets} x {weightings}; v1 maps for {args.v1_datasets}")
        return 0
    out, ct = ctx.out_dir, CheckTable()
    n_boot = int(dd["v2"]["statistics"]["bootstrap_n_resamples"])
    ops = {k: v for k, v in dd["responsiveness"]["operators"].items() if k != "source"}
    beta = dd["target"]["weights"]["beta"]["value"]
    L = int(dd["target"]["window_length_L"]["value"])
    res_a, res_b = {}, {}
    prev = out / "tables" / "degradation.json"
    if prev.exists():
        res_a = json.loads(prev.read_text())
    with RunRecord("v2/v7_scores", out, {"config": ctx.config, "datasets": args.datasets, "v1_datasets": args.v1_datasets, "weightings": weightings},
                   {"evaluation": args.seed}, ctx.device) as rec:
        if not args.skip_part_a:
            for ds in args.datasets:
                prof = C.v2_profile(ds)
                units, table = pickle.loads((DATA_V2 / "generated" / ds / "seed0.pkl").read_bytes())
                split = dict(zip(table["index"], table["split"]))
                test = [u for u in units if split[u.index] == "test"]
                P = Profile.from_json(prof, np.array([0.0]))
                spec = TargetSpec.build(P, beta, L, 6.0)
                widx = np.flatnonzero(spec.kappa != 0)
                has_patterns = any(len(u.patterns) for u in units)
                res_a[ds] = {}
                for kind in weightings:
                    with rec.section(f"{ds}_{kind}_part_a"):
                        r = part_a(ds, test, spec, kind, ops, widx, args.seed, n_boot, has_patterns)
                    res_a[ds][kind] = r
                    write_json(res_a, out / "tables" / "degradation.json")
                    for op, s in r["operators"].items():
                        for k in SCORES:
                            print(f"[v7] {ds} {kind} {op:18s} {k:10s} resolved {s[k]['resolution']} (change {s[k]['change_at_resolution']}); "
                                  f"registers {s[k]['registers']['registering_magnitude']}", flush=True)
                    # undegraded truth is perfect on every score (construction check)
                    for k in SCORES:
                        m0 = r["operators"]["added_noise"][k]["mean"][0]
                        ct.require(f"{ds} [{kind}]: undegraded ground truth scores perfect on {k}", abs(m0 - PERFECT[k]) < 1e-9, PERFECT[k], f"{m0:.3g}")
        if not args.skip_part_b:
            for ds in args.v1_datasets:
                res_b[ds] = {}
                for kind in dd["v2"]["statistics"]["v1_maps_weightings"]:
                    with rec.section(f"{ds}_{kind}_v1_maps"):
                        res_b[ds][kind] = part_b(ds, kind, args.seed, n_boot)
                    e = res_b[ds][kind]["reference_exact"]
                    ref_ig = res_b[ds][kind].get("reference_integrated_gradients")
                    if ref_ig:
                        ct.require(f"{ds} [{kind}] v1 maps: IG on the reference model scores as the exact attribution (temporal error)",
                                   abs(ref_ig["temporal"]["mean"] - e["temporal"]["mean"]) < 1e-3, "|diff| < 1e-3",
                                   f"{abs(ref_ig['temporal']['mean'] - e['temporal']['mean']):.2e}")
                write_json(res_b, out / "tables" / "v1_maps_scores.json")
        try:
            from degradx.viz import v7 as viz

            for ds, by in res_a.items():
                for kind, r in by.items():
                    save_figure(viz.score_vs_degradation(ds, kind, r), out / "figures" / f"{ds.lower()}_{kind}_score_vs_degradation")
        except ImportError:
            pass
        code = ct.finalize(out)
        (out / "logs" / "checks.md").write_text(ct.markdown() + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
