#!/usr/bin/env python
"""S7 — RQ3, responsiveness of the scores (paper §3.5.3; Tables 4-5, Figures 7-8).

Part one (no attribution method): the attribution ground truth of generated test units (generation seed 0) is degraded
by the declared operators and magnitudes; each score is computed on the degraded maps:
  rank agreement  Spearman(degraded graded field, graded field)                         (D01: the pattern-free map)
  retrieval       AP(|degraded phi* - degraded graded field|, sparse set), independent draws per map   (D01, NASA only)
  retrieval plain AP(|degraded phi*|, sparse set)                                          (secondary, NASA only)
Scores are averaged over windows within a unit; resolution = the smallest magnitude at which the paired bootstrap over
units (declarations responsiveness.reliability_criterion) gives an upper 95% bound of mean(score_m - score_0) < 0 at that
and every larger magnitude. Chance = score of a fully permuted map. Sanity (D08): permuted map at chance, undegraded at
its own ceiling.
Part two (generator settings): per value of noise variance multiplier, transition sharpness, window length and pattern
amplitude (NASA), units are generated, the primary LSTM configuration is trained on y (recency) and Integrated Gradients
(declared baseline) is scored; normalised score = (s - chance) / (ceiling - chance); saturation >= 0.95, near chance <= 0.05
or interval including chance (declarations responsiveness.operating_range). The probe choice is decision D20.
Outputs in ``artifacts/s7_responsiveness``.
"""

from __future__ import annotations

import copy
import json
import pickle
import sys

import numpy as np
import pandas as pd
import yaml
from scipy.stats import bootstrap

from degradx import ARTIFACTS_DIR, CONFIG_DIR, DATA_DIR
from degradx.attribution.methods import RawSpaceModel, ReferenceModel, integrated_gradients
from degradx.generator.generate import Profile, generate_unit
from degradx.metrics.scores import OPERATORS, rank_agreement, retrieval_ap
from degradx.models.lstm import train_regressor
from degradx.targets.decomposable import TargetSpec, unit_targets
from degradx.utils.checks import CheckTable
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.io import save_figure, save_table, write_json
from degradx.utils.seeding import rng
from degradx.utils.provenance import RunRecord

PROFILES = ("MATR", "HUST", "NASA_PCoE")


def sample_windows(units, spec, kind, per_unit: int, need_sparse: bool, g):
    rows = []
    for ui, u in enumerate(units):
        if u.T < spec.L:
            continue
        tg = unit_targets(u, spec, kind)
        idx = np.arange(len(tg["y"]))
        if need_sparse:
            idx = idx[np.abs(tg["sparse"]).sum(axis=(1, 2)) > 0]
        if not len(idx):
            continue
        idx = np.sort(g.choice(idx, size=min(per_unit, len(idx)), replace=False))
        for i in idx:
            rows.append((ui, tg["phi_star"][i], tg["graded"][i], tg["sparse"][i] != 0, tg["x"][i], tg["x_pattern_free"][i]))
    return rows


def per_unit_mean(values: np.ndarray, units: np.ndarray):
    uu = np.unique(units)
    return uu, np.array([np.nanmean(values[units == u]) for u in uu])


def resolution(unit_scores: dict, grid, seed: int) -> dict:
    """Paired bootstrap over units of mean(score_m - score_0); resolved at m if the upper 95% bound < 0 there and at every
    larger magnitude."""
    base = unit_scores[grid[0]]
    upper = {}
    for m in grid[1:]:
        d = unit_scores[m] - base
        d = d[np.isfinite(d)]
        if len(d) < 3 or np.allclose(d, d[0]):
            upper[m] = float(np.mean(d)) if len(d) else float("nan")
            continue
        res = bootstrap((d,), np.mean, n_resamples=2000, confidence_level=0.95, method="BCa", random_state=np.random.default_rng(seed))
        upper[m] = float(res.confidence_interval.high)
    resolved = None
    for i, m in enumerate(grid[1:]):
        if all(np.isfinite(upper[k]) and upper[k] < 0 for k in grid[1 + i:]):
            resolved = m
            break
    return {"upper_bound_of_mean_drop": upper, "resolution": resolved}


def part_one(ds, units, spec, kind, ops, has_patterns, seed, per_unit=20):
    g = rng(seed, "evaluation", "s7", ds, kind)
    W = sample_windows(units, spec, kind, per_unit, need_sparse=False, g=g)
    WS = sample_windows(units, spec, kind, per_unit, need_sparse=True, g=g) if has_patterns else []
    out = {"windows_rank": len(W), "units_rank": len({w[0] for w in W}), "windows_retrieval": len(WS), "units_retrieval": len({w[0] for w in WS})}
    # chance: fully permuted maps
    ch_rank = [rank_agreement(g.permutation(w[2].ravel()).reshape(w[2].shape), w[2]) for w in W]
    out["chance_rank"] = float(np.nanmean(ch_rank))
    if WS:
        out["chance_retrieval"] = float(np.nanmean([retrieval_ap(g.permutation(w[1].ravel()).reshape(w[1].shape), w[3]) for w in WS]))
    series = {}
    for op, cfg in ops.items():
        grid = cfg["grid"]
        f = OPERATORS[op]
        rank_u, ret_u, plain_u = {}, {}, {}
        for mi, mag in enumerate(grid):
            vals = []
            for wi, (ui, phi, grd, lab, _x, _xpf) in enumerate(W):
                ga = rng(seed, "evaluation", "s7", ds, kind, op, mi, wi, "a")
                d = f(grd, mag, ga) if op != "added_noise" else f(grd, mag, ga, scale=np.std(grd))
                vals.append(rank_agreement(d, grd))
            uu, rank_u[mag] = per_unit_mean(np.array(vals), np.array([w[0] for w in W]))
            if WS:
                rv, pv = [], []
                for wi, (ui, phi, grd, lab, _x, _xpf) in enumerate(WS):
                    gb, gc = rng(seed, "evaluation", "s7", ds, kind, op, mi, wi, "b"), rng(seed, "evaluation", "s7", ds, kind, op, mi, wi, "c")
                    d1 = f(phi, mag, gb) if op != "added_noise" else f(phi, mag, gb, scale=np.std(phi))
                    d2 = f(grd, mag, gc) if op != "added_noise" else f(grd, mag, gc, scale=np.std(phi))
                    rv.append(retrieval_ap(d1 - d2, lab))
                    pv.append(retrieval_ap(d1, lab))
                _, ret_u[mag] = per_unit_mean(np.array(rv), np.array([w[0] for w in WS]))
                _, plain_u[mag] = per_unit_mean(np.array(pv), np.array([w[0] for w in WS]))
        s = {"grid": grid, "rank_mean": [float(np.nanmean(rank_u[m])) for m in grid],
             "rank_ci": [list(np.nanquantile(rank_u[m], [0.025, 0.975])) for m in grid], "rank_resolution": resolution(rank_u, grid, seed)}
        if WS:
            s.update({"retrieval_mean": [float(np.nanmean(ret_u[m])) for m in grid], "retrieval_ci": [list(np.nanquantile(ret_u[m], [0.025, 0.975])) for m in grid],
                      "retrieval_resolution": resolution(ret_u, grid, seed), "plain_retrieval_mean": [float(np.nanmean(plain_u[m])) for m in grid],
                      "plain_retrieval_resolution": resolution(plain_u, grid, seed)})
        series[op] = s
    out["operators"] = series
    return out


def part_two(ds, P, spec_kw, settings, base_cfg, device, seed, n_units=150, per_unit=10, overrides_key=None):
    rows = []
    beta, L0, h = spec_kw
    for setting, grid in settings.items():
        for val in grid:
            ov = {} if setting == "window_length_L" else {setting: float(val)}
            L = int(val) if setting == "window_length_L" else L0
            spec = TargetSpec.build(P, beta, L, h if setting != "window_length_L" else h * L / L0)
            units, i = [], 0
            while len(units) < n_units and i < 4 * n_units:
                u = generate_unit(P, 0, i, overrides=ov)
                i += 1
                if u is not None and u.T >= L + 2:
                    units.append(u)
            g = rng(seed, "split", ds, "s7", setting, val)
            perm = g.permutation(len(units))
            tr, va, te = perm[: int(0.7 * len(units))], perm[int(0.7 * len(units)): int(0.85 * len(units))], perm[int(0.85 * len(units)):]
            Xs, ys, us = [], [], []
            for k in np.concatenate([tr, va]):
                tg = unit_targets(units[k], spec, "recency")
                Xs.append(tg["x"]); ys.append(tg["y"]); us.append(np.full(len(tg["y"]), k))
            X, y, U = np.concatenate(Xs).astype(np.float32), np.concatenate(ys), np.concatenate(us)
            m = train_regressor(X, y, U, seed=0, device=device, cfg=base_cfg, val_units=set(va.tolist()))
            model = RawSpaceModel(m)
            ref = ReferenceModel(spec.weights("recency"), spec.x0)
            base = np.broadcast_to(spec.x0, (L, len(spec.x0)))
            rank_ig, rank_ref, ret_ig, ret_ref, nrmse = [], [], [], [], []
            yt, pt = [], []
            has_pat = any(len(units[k].patterns) for k in te)
            for k in te:
                u = units[k]
                tg = unit_targets(u, spec, "recency")
                pt.append(m.predict(tg["x"].astype(np.float32))); yt.append(tg["y"])
                idx = np.sort(g.choice(len(tg["y"]), size=min(per_unit, len(tg["y"])), replace=False))
                A = integrated_gradients(model, tg["x"][idx], base, device)
                Apf = integrated_gradients(model, tg["x_pattern_free"][idx], base, device)
                Rpf = spec.weights("recency")[None] * (tg["x_pattern_free"][idx] - spec.x0)
                R = spec.weights("recency")[None] * (tg["x"][idx] - spec.x0)
                rank_ig.append(np.nanmean([rank_agreement(Apf[j], tg["graded"][idx][j]) for j in range(len(idx))]))
                rank_ref.append(np.nanmean([rank_agreement(Rpf[j], tg["graded"][idx][j]) for j in range(len(idx))]))
                if has_pat:
                    sp = tg["sparse"][idx] != 0
                    ok = [j for j in range(len(idx)) if sp[j].any()]
                    if ok:
                        ret_ig.append(np.nanmean([retrieval_ap(A[j] - Apf[j], sp[j]) for j in ok]))
                        ret_ref.append(np.nanmean([retrieval_ap(R[j] - Rpf[j], sp[j]) for j in ok]))
            yt, pt = np.concatenate(yt), np.concatenate(pt)
            row = {"dataset": ds, "setting": setting, "value": val, "units": len(units), "test_units": int(len(te)),
                   "nrmse": float(np.sqrt(np.mean((pt - yt) ** 2)) / np.std(yt)),
                   "rank_ig": float(np.nanmean(rank_ig)), "rank_ig_units": rank_ig, "rank_reference_exact": float(np.nanmean(rank_ref)),
                   "retrieval_ig": float(np.nanmean(ret_ig)) if ret_ig else None, "retrieval_ig_units": ret_ig,
                   "retrieval_reference_exact": float(np.nanmean(ret_ref)) if ret_ref else None}
            rows.append(row)
            print(f"[s7-2] {ds} {setting}={val}: nrmse {row['nrmse']:.3f} rank IG {row['rank_ig']:.3f} ref {row['rank_reference_exact']:.3f} retrieval IG {row['retrieval_ig']}", flush=True)
    return rows


def main() -> int:
    p = stage_parser(__doc__, "s7_responsiveness")
    p.add_argument("--datasets", nargs="*", default=list(PROFILES))
    p.add_argument("--skip-part-two", action="store_true")
    p.add_argument("--skip-part-one", action="store_true", help="reuse tables/part1_degradation.json")
    args = p.parse_args()
    ctx = StageContext.from_args(args)
    decl, dd = ctx.declarations, ctx.declarations["declared_by_design"]
    if args.dry_run:
        print("plan: part one (operators on ground truth), part two (generator settings with IG probe)")
        return 0
    from degradx.viz import s7 as viz

    out, ct = ctx.out_dir, CheckTable()
    beta = dd["target"]["weights"]["beta"]["value"]
    L = int(dd["target"]["window_length_L"]["value"])
    ops = {k: v for k, v in dd["responsiveness"]["operators"].items() if k != "source"}
    settings_all = {k: v for k, v in dd["responsiveness"]["generator_settings"].items() if k != "source"}
    base_cfg = yaml.safe_load((CONFIG_DIR / "models" / "lstm.yaml").read_text())
    res1, res2 = {}, []
    with RunRecord("s7_responsiveness", out, {"config": ctx.config, "datasets": args.datasets}, {"evaluation": args.seed, "generation": 0, "model_init": 0}, ctx.device) as rec:
        for ds in args.datasets:
            prof = json.loads((ARTIFACTS_DIR / "s3_fit_profiles" / "profiles" / f"{ds}.json").read_text())
            units, table = pickle.loads((DATA_DIR / "generated" / ds / "seed0.pkl").read_bytes())
            test = [u for u in units if table.set_index("index").at[u.index, "split"] == "test"]
            # the null_permuted pool (measured charge-time readings) is only needed to generate part-two units; the values the
            # generator drew for S4 units are draws from that pool, so their union reproduces its support
            P = Profile.from_json(prof, np.concatenate([u.eps[:, len(prof["declared_used"]["channels_available"]) + 1] for u in units]))
            spec = TargetSpec.build(P, beta, L, 6.0)
            has_patterns = any(len(u.patterns) for u in units)
            if args.skip_part_one:
                res1 = json.loads((out / "tables" / "part1_degradation.json").read_text())
            else:
                res1[ds] = {}
            for kind in (() if args.skip_part_one else ("recency", "uniform", "final_position")):
                with rec.section(f"{ds}_{kind}_part1"):
                    r = part_one(ds, test, spec, kind, ops, has_patterns, args.seed)
                res1[ds][kind] = r
                # sanity checks (D08): permuted map at chance; undegraded at its ceiling
                for op, s in r["operators"].items():
                    if op == "permuted_fraction":
                        ct.require(f"{ds} [{kind}]: fully permuted graded map scores at chance (rank)", abs(s["rank_mean"][-1] - r["chance_rank"]) < 0.05,
                                   f"~ chance {r['chance_rank']:.3f}", f"{s['rank_mean'][-1]:.3f}")
                        if "retrieval_mean" in s:
                            ct.require(f"{ds} [{kind}]: fully permuted map scores at chance (paired retrieval)", abs(s["retrieval_mean"][-1] - r["chance_retrieval"]) < 0.05,
                                       f"~ chance {r['chance_retrieval']:.3f}", f"{s['retrieval_mean'][-1]:.3f}")
                    ct.require(f"{ds} [{kind}] {op}: undegraded ground truth at its ceiling (rank agreement 1)", abs(s["rank_mean"][0] - 1.0) < 1e-9, "1", f"{s['rank_mean'][0]:.6f}")
                    if "retrieval_mean" in s:
                        ct.require(f"{ds} [{kind}] {op}: undegraded ground truth at its ceiling (paired retrieval 1)", abs(s["retrieval_mean"][0] - 1.0) < 1e-9, "1", f"{s['retrieval_mean'][0]:.6f}")
                write_json(res1, out / "tables" / "part1_degradation.json")
                save_figure(viz.degradation(ds, kind, r), out / "figures" / f"{ds.lower()}_{kind}_score_vs_degradation")
            if not args.skip_part_two:
                settings = {k: v for k, v in settings_all.items() if k != "pattern_amplitude_multiplier" or has_patterns}
                with rec.section(f"{ds}_part2"):
                    rows = part_two(ds, P, (beta, L, 6.0), settings, base_cfg, ctx.device, args.seed)
                res2 += rows
                write_json(res2, out / "tables" / "part2_generator_settings.json")
        if res2:
            with rec.section("operating_range"):
                rows, table5 = operating_range(res2, res1, dd, args.seed)
                write_json(rows, out / "tables" / "part2_generator_settings.json")
                save_table(pd.DataFrame(table5), out / "tables" / "operating_range")
                save_figure(viz.settings_panel(rows, None), out / "figures" / "score_vs_generator_settings")
        code = ct.finalize(out)
        (out / "logs" / "checks.md").write_text(ct.markdown() + "\n")
    return code


def operating_range(rows, res1, dd, seed):
    """Normalised score (s - chance) / (ceiling - chance) with ceiling 1 (the undegraded ground truth scores 1 under D01) and
    chance from part one (recency); 95% interval over test units; saturation >= 0.95, near chance <= 0.05 or interval
    including chance (declarations responsiveness.operating_range)."""
    sat, chance_thr = 0.95, 0.05
    out_rows, table = [], []
    for r in rows:
        ds = r["dataset"]
        c_rank = res1[ds]["recency"]["chance_rank"]
        c_ret = res1[ds]["recency"].get("chance_retrieval")
        r = dict(r)
        for key, c, units_key in (("rank_ig", c_rank, "rank_ig_units"), ("retrieval_ig", c_ret, "retrieval_ig_units")):
            vals = np.asarray(r.get(units_key) or [], float)
            vals = vals[np.isfinite(vals)]
            if c is None or not len(vals):
                r[f"{key}_norm"] = None
                continue
            norm = (vals - c) / (1.0 - c)
            r[f"{key}_norm"] = float(norm.mean())
            if len(norm) >= 3 and np.std(norm) > 0:
                ci = bootstrap((norm,), np.mean, n_resamples=2000, method="BCa", random_state=np.random.default_rng(seed)).confidence_interval
                r[f"{key}_norm_ci"] = [float(ci.low), float(ci.high)]
            else:
                r[f"{key}_norm_ci"] = [float(norm.mean()), float(norm.mean())]
            lo = r[f"{key}_norm_ci"][0]
            r[f"{key}_state"] = "saturated" if r[f"{key}_norm"] >= sat else ("near chance" if (r[f"{key}_norm"] <= chance_thr or lo <= 0) else "responsive")
        out_rows.append(r)
    for ds in sorted({r["dataset"] for r in out_rows}):
        for setting in sorted({r["setting"] for r in out_rows if r["dataset"] == ds}):
            rr = [r for r in out_rows if r["dataset"] == ds and r["setting"] == setting]
            for key in ("rank_ig", "retrieval_ig"):
                states = [(r["value"], r.get(f"{key}_state")) for r in rr if r.get(f"{key}_state")]
                if not states:
                    continue
                resp = [v for v, s in states if s == "responsive"]
                table.append({"dataset": ds, "setting": setting, "score": key, "range_examined": [rr[0]["value"], rr[-1]["value"]],
                              "responsive_values": resp, "responsive_range": [min(resp), max(resp)] if resp else None,
                              "outside": {str(v): s for v, s in states if s != "responsive"}})
    return out_rows, table


if __name__ == "__main__":
    sys.exit(main())
