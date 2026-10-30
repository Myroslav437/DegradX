#!/usr/bin/env python
"""S14 (X5) — RQ3, score validation by the degraded-map test.

Part A (declarations protocol.scoring): the attribution ground truth of generated test units (S10, generation seed 0; 20
windows per unit, as declared) is degraded by the five declared operators over their declared grids, under recency and
uniform weighting. Scores on the pattern-free counterpart map against the graded field (D01):
  rank agreement (higher is better; kept for continuity), channel allocation error and temporal profile error (lower is
  better, X5); paired retrieval only where the profile carries patterns.
Per score and operator: the resolution (baseline criterion, sign-aware: for error scores the LOWER bound of the 95% paired BCa
interval of mean(degraded - undegraded) > 0 at this and every larger magnitude; 10 000 resamples), the mean change at the
resolved magnitude, and the declared registers check (resolved, and the mean change toward chance >= 10% of
|s_chance - s_perfect| at some magnitude and every larger one; s_chance from fully permuted maps). Windows on which a
score is undefined are counted per magnitude.
Outputs in ``artifacts/s14_degraded_map_test``.
"""

from __future__ import annotations

import json
import pickle
import sys

import numpy as np
from scipy.stats import bootstrap

import _common as C
from degradx.generator.generate import Profile
from degradx.metrics.scores import OPERATORS, channel_allocation_error, rank_agreement, retrieval_ap, temporal_profile_error
from degradx.targets.decomposable import TargetSpec, unit_targets
from degradx.utils.checks import CheckTable
from degradx.utils.cli import StageContext, run_tag, stage_parser
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
    bound < 0 at m and every larger magnitude. Error scores (sign -1): the lower bound > 0 likewise."""
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


def registers(mean_change: dict, grid, chance: float, perfect: float, resolved, frac: float = 0.10) -> dict:
    """Declared reading (protocol.scoring.registers_check): (i) resolved, and (ii) the mean change toward chance reaches frac of
    |s_chance - s_perfect| at this and every larger magnitude. Since resolution holds at every magnitude from the resolved one
    on, (i) and (ii) together give the smallest magnitude >= the resolved one from which (ii) holds throughout."""
    thr = frac * abs(chance - perfect)
    toward = np.sign(chance - perfect)
    mags = grid[1:]
    big = {m: bool(np.isfinite(mean_change[m]) and toward * mean_change[m] >= thr) for m in mags}
    ok = {m: big[m] and resolved is not None and m >= resolved for m in mags}
    mag = next((m for i, m in enumerate(mags) if all(ok[k] for k in mags[i:])), None)
    size_only = next((m for i, m in enumerate(mags) if all(big[k] for k in mags[i:])), None)
    return {"threshold": thr, "registering_magnitude": mag, "registers": mag is not None, "size_condition_only_magnitude": size_only}


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
        excl, undef = {}, {}
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
            undef[mag] = {k: int(np.sum(~np.isfinite(np.array(vals[k], float)))) for k in SCORES}
        s = {"grid": grid, "temporal_channels_excluded": excl, "windows_undefined": undef}
        for k, sign in SCORES.items():
            res = resolution(per[k], grid, sign, seed, n_boot)
            s[k] = {"mean": [float(np.nanmean(per[k][m])) for m in grid], **res,
                    "registers": registers(res["mean_change"], grid, out["chance"][k], PERFECT[k], res["resolution"])}
        series[op] = s
    out["operators"] = series
    if has_patterns:
        out["paired_retrieval"] = paired_retrieval(ds, units, spec, kind, ops, seed, n_boot, per_unit)
    return out


def sample_sparse_windows(units, spec, kind, per_unit, g):
    """Windows with at least one sparse cell (sample_windows with need_sparse=True)."""
    rows = []
    for ui, u in enumerate(units):
        if u.T < spec.L:
            continue
        tg = unit_targets(u, spec, kind)
        idx = np.arange(len(tg["y"]))[np.abs(tg["sparse"]).sum(axis=(1, 2)) > 0]
        if not len(idx):
            continue
        for i in np.sort(g.choice(idx, size=min(per_unit, len(idx)), replace=False)):
            rows.append((ui, tg["phi_star"][i], tg["graded"][i], tg["sparse"][i] != 0))
    return rows


def paired_retrieval(ds, units, spec, kind, ops, seed, n_boot, per_unit=20):
    """Paired retrieval (D01) on a profile with inserted patterns, as declared: the window map phi* and its
    pattern-free counterpart (the graded field) are degraded by the same operator with independent streams; AP of
    |d(phi*) - d(graded)| against the sparse set; plain AP of d(phi*) as the secondary score. Resolution by the declared
    criterion (higher is better); the registers reading is computed as for the X5 scores and marked descriptive, since
    declarations protocol.scoring.registers_check names rank, allocation and temporal only."""
    g = rng(seed, "evaluation", "v7", ds, kind, "sparse")
    WS = sample_sparse_windows(units, spec, kind, per_unit, g)
    if not WS:
        return {"void": "no test window contains a sparse cell"}
    US = np.array([w[0] for w in WS])
    out = {"windows": len(WS), "units": int(len(np.unique(US))),
           "chance": float(np.nanmean([retrieval_ap(g.permutation(w[1].ravel()).reshape(w[1].shape), w[3]) for w in WS])),
           "chance_plain": float(np.nanmean([retrieval_ap(g.permutation(w[1].ravel()).reshape(w[1].shape), w[3]) for w in WS]))}
    series = {}
    for op, cfg in ops.items():
        grid = cfg["grid"]
        f = OPERATORS[op]
        paired_u, plain_u = {}, {}
        for mi, mag in enumerate(grid):
            pv, qv = [], []
            for wi, (ui, phi, grd, lab) in enumerate(WS):
                gb = rng(seed, "evaluation", "v7", ds, kind, op, mi, wi, "b")
                gc = rng(seed, "evaluation", "v7", ds, kind, op, mi, wi, "c")
                d1 = f(phi, mag, gb) if op != "added_noise" else f(phi, mag, gb, scale=np.std(phi))
                d2 = f(grd, mag, gc) if op != "added_noise" else f(grd, mag, gc, scale=np.std(phi))
                pv.append(retrieval_ap(d1 - d2, lab))
                qv.append(retrieval_ap(d1, lab))
            _, paired_u[mag] = unit_means(np.array(pv, float), US)
            _, plain_u[mag] = unit_means(np.array(qv, float), US)
        s = {"grid": grid}
        for name, per, ch in (("paired", paired_u, out["chance"]), ("plain", plain_u, out["chance_plain"])):
            res = resolution(per, grid, +1, seed, n_boot)
            s[name] = {"mean": [float(np.nanmean(per[m])) for m in grid], **res,
                       "registers_descriptive": registers(res["mean_change"], grid, ch, 1.0, res["resolution"])}
        series[op] = s
    out["operators"] = series
    return out


def main() -> int:
    p = stage_parser(__doc__, "s14_degraded_map_test")
    p.add_argument("--datasets", nargs="*", default=["MATR", "HUST"])
    p.add_argument("--profile-config", nargs="*", default=[])
    args = p.parse_args()
    for kv in args.profile_config:
        C.register_profile(*kv.split("="))
    ctx = StageContext.from_args(args)
    tag = run_tag(args.datasets)  # MATR_HUST or TRI_FORMATION: one run per dataset group
    decl, dd = ctx.declarations, ctx.declarations["declared_by_design"]
    sc_w = dd["protocol"]["scope"]["weightings"]
    weightings = [sc_w["primary"], sc_w["sensitivity"]]
    if args.dry_run:
        print(f"plan: degraded-map test for {args.datasets} x {weightings}")
        return 0
    out, ct = ctx.out_dir, CheckTable()
    n_boot = int(dd["protocol"]["statistics"]["bootstrap_n_resamples"])
    ops = {k: v for k, v in dd["responsiveness"]["operators"].items() if k != "source"}
    beta = dd["target"]["weights"]["beta"]["value"]
    L = int(dd["target"]["window_length_L"]["value"])
    res_a = {}
    prev = out / "tables" / "degradation.json"
    if prev.exists():
        res_a = json.loads(prev.read_text())
    with RunRecord("s14_degraded_map_test", out, {"config": ctx.config, "datasets": args.datasets, "weightings": weightings},
                   {"evaluation": args.seed}, ctx.device, tag=tag) as rec:
        for ds in args.datasets:
            prof = C.fitted_profile(ds)
            units, table = pickle.loads((C.generated_dir(ds) / "seed0.pkl").read_bytes())
            split = dict(zip(table["index"], table["split"]))
            test = [u for u in units if split[u.index] == "test"]
            P = Profile.from_json(prof, np.array([0.0]))  # dummy null pool: only x0 of null_permuted changes, which has zero weight in y and phi*
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
                        print(f"[s14] {ds} {kind} {op:18s} {k:10s} resolved {s[k]['resolution']} (change {s[k]['change_at_resolution']}); "
                              f"registers {s[k]['registers']['registering_magnitude']}", flush=True)
                # undegraded truth is perfect on every score (construction check)
                for k in SCORES:
                    m0 = r["operators"]["added_noise"][k]["mean"][0]
                    ct.require(f"{ds} [{kind}]: undegraded ground truth scores perfect on {k}", abs(m0 - PERFECT[k]) < 1e-9, PERFECT[k], f"{m0:.3g}")
        try:
            from degradx.viz import scores as viz

            for ds, by in res_a.items():
                for kind, r in by.items():
                    save_figure(viz.score_vs_degradation(ds, kind, r), out / "figures" / f"{ds.lower()}_{kind}_score_vs_degradation")
        except ImportError:
            pass
        code = ct.finalize(out, tag)
        (out / "logs" / f"checks_{tag}.md").write_text(ct.markdown() + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
