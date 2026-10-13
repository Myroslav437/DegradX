#!/usr/bin/env python
"""W5/W10 (brief "DegradX v2.1") — the one MATR / HUST computation of v2.1 (declarations r4
declared_by_design.v2_1.tstr_without_x3): TSTR on the existing V4 generated sets with X3 switched off
(data/v2/generated/<MATR|HUST>/seed0_x3off.pkl; nothing is regenerated), so Table 1 can separate X2's and X3's shares in
transfer.

Estimator: V5's TSTR exactly, full input set. The measured side is rebuilt as V5 builds it (V3 split, D12, D27, D13); the
generated side is the first n units of the X3-off set in list order (n = measured fitting units reaching EOL); model seeds
0-4; V5's TRTR per-unit errors are reused (artifacts/v2/v5_fidelity/tables/per_unit_sse_<ds>.npz), after a determinism check
that retrains TRTR (full, model seed 0) and TSTR (full, generation seed 0, model seed 0) and compares them with V5's stored
errors.

Reported per profile: the ratio with its 95 % BCa interval; X3's share = log ratio(v2 without X3, seed 0) - log ratio(v2,
seed 0), paired BCa; X2's share = log ratio(v1, full_D27, seeds 0-2 x 0-4) - log ratio(v2 without X3, seed 0), paired BCa on
the V1 per-unit errors (artifacts/v2/v1_tstr_isolation/tables/per_unit_sse_<ds>.npz); and, not read, the X2 share against v1's
full set (D17 measured side) and against v1 generation seed 0 only.
Outputs: artifacts/v2.1/w5_fidelity/tstr_without_x3/tables/ (tstr_without_x3.json, per_unit_sse_x3off_<ds>.npz, tstr_runs_x3off_<ds>.csv).
"""

from __future__ import annotations

import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "v2"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

import _common as C  # noqa: E402
import v1_tstr_isolation as V1  # noqa: E402
from degradx import ARTIFACTS_V2, ARTIFACTS_V21, CONFIG_DIR  # noqa: E402
from degradx.data.audit import CleaningRule  # noqa: E402
from degradx.fitting.profile import prepare_units  # noqa: E402
from degradx.generator.state import spec_from_declarations  # noqa: E402
from degradx.metrics import fidelity as F  # noqa: E402
from degradx.models.lstm import train_regressor  # noqa: E402
from degradx.utils.checks import CheckTable  # noqa: E402
from degradx.utils.cli import StageContext, stage_parser  # noqa: E402
from degradx.utils.io import save_table, write_json  # noqa: E402
from degradx.utils.provenance import RunRecord  # noqa: E402


def mean_sse(z, keys):
    return np.mean([z[k] for k in keys], axis=0)


def main() -> int:
    p = stage_parser(__doc__, "v2.1/w5_fidelity/tstr_without_x3")
    p.add_argument("--datasets", nargs="*", default=["MATR", "HUST"])
    args = p.parse_args()
    ctx = StageContext.from_args(args)
    decl, dd = ctx.declarations, ctx.declarations["declared_by_design"]
    if args.dry_run:
        print("plan: TSTR on the V4 seed0_x3off sets of MATR and HUST (v2_1.tstr_without_x3)")
        return 0
    out, ct = ctx.out_dir, CheckTable()
    L = int(dd["target"]["window_length_L"]["value"])
    model_seeds = dd["statistics"]["seeds"]["model_init"]
    gen_seeds = dd["statistics"]["seeds"]["generation"]
    n_boot = int(dd["v2"]["statistics"]["bootstrap_n_resamples"])
    lstm_cfg = yaml.safe_load((CONFIG_DIR / "models" / "lstm.yaml").read_text())
    rule = CleaningRule("D12", **dd["capacity_series"]["cleaning_rule"]["params"])
    crule = C.channel_rule_v2(dd)
    results = {"declaration": "declared_by_design.v2_1.tstr_without_x3", "input_set": "full"}
    with RunRecord("v2.1/w5_tstr_without_x3", out, {"datasets": args.datasets}, {"model_init": model_seeds, "evaluation": args.seed}, ctx.device) as rec:
        for ds in args.datasets:
            with rec.section(ds):
                prof = C.v2_profile(ds)
                chans = prof["declared_used"]["channels_available"]
                q_nom = C.q_nom_of(ds)
                spec = spec_from_declarations(decl, q_nom)
                split = C.v2_split(ds)
                df = C.load_scope(ds, dd)
                fit_u = prepare_units(df, split.loc[split["split"] == "fitting", "cell_id"], q_nom, spec, rule, chans, crule)
                ho_u = prepare_units(df, split.loc[split["split"] == "held_out", "cell_id"], q_nom, spec, rule, chans, crule)
                ms_fit, ms_ho = F.measured_series(fit_u, chans), F.measured_series(ho_u, chans)
                Xm, Um, Rm = F.windows(ms_fit, L, with_rul=True, with_elapsed=True)
                Xh, Uh, Rh = F.windows(ms_ho, L, with_rul=True, with_elapsed=True)
                n_train = sum(s.T is not None for s in ms_fit)
                z5 = np.load(ARTIFACTS_V2 / "v5_fidelity" / "tables" / f"per_unit_sse_{ds}.npz", allow_pickle=True)
                z1 = np.load(ARTIFACTS_V2 / "v1_tstr_isolation" / "tables" / f"per_unit_sse_{ds}.npz", allow_pickle=True)
                gens = {"x3off": pickle.loads((C.generated_dir(ds) / "seed0_x3off.pkl").read_bytes())[0],
                        0: pickle.loads((C.generated_dir(ds) / "seed0.pkl").read_bytes())[0]}
                gw = {}
                for g, units in gens.items():
                    gs_ = F.generated_series(units[:n_train], len(chans))
                    gw[g] = F.windows(gs_, L, with_rul=True, with_elapsed=True)
                # alignment with V5's stored per-unit errors (same held-out units, same windows)
                units_h, _, nh = F.per_unit_sse(np.zeros(len(Rh)), Rh, Uh)
                ids = [ms_ho[i].unit_id for i in units_h]
                aligned = list(z5["units"]) == ids and np.array_equal(z5["n_windows"], nh) and list(z1["units"]) == ids and np.array_equal(z1["n_windows"], nh)
                ct.require(f"{ds}: held-out units and windows equal V5's and V1's stored per-unit errors", aligned, "identical", str(aligned))
                if not aligned:
                    continue
                runs, sse_off = [], {}
                # determinism: retrain TRTR full m0 and TSTR full g0 m0, compare with V5's stored errors
                m = train_regressor(Xm, Rm, Um, seed=model_seeds[0], device=ctx.device, cfg=lstm_cfg)
                _, s_trtr, _ = F.per_unit_sse(m.predict(Xh), Rh, Uh)
                Xg, Ug, Rg = gw[0]
                m = train_regressor(Xg, Rg, Ug, seed=model_seeds[0], device=ctx.device, cfg=lstm_cfg)
                _, s_tstr0, _ = F.per_unit_sse(m.predict(Xh), Rh, Uh)
                d_trtr = float(np.max(np.abs(s_trtr - z5[f"full__TRTR__m{model_seeds[0]}"]) / np.maximum(z5[f"full__TRTR__m{model_seeds[0]}"], 1e-12)))
                d_tstr = float(np.max(np.abs(s_tstr0 - z5[f"full__TSTR__g0_m{model_seeds[0]}"]) / np.maximum(z5[f"full__TSTR__g0_m{model_seeds[0]}"], 1e-12)))
                ct.require(f"{ds}: retrained TRTR full m0 reproduces V5's per-unit errors", d_trtr < 1e-6, "max rel diff < 1e-6", f"{d_trtr:.2e}", severity="warn")
                ct.require(f"{ds}: retrained TSTR full g0 m0 reproduces V5's per-unit errors", d_tstr < 1e-6, "max rel diff < 1e-6", f"{d_tstr:.2e}", severity="warn")
                Xg, Ug, Rg = gw["x3off"]
                for ms in model_seeds:
                    m = train_regressor(Xg, Rg, Ug, seed=ms, device=ctx.device, cfg=lstm_cfg)
                    _, s_, _ = F.per_unit_sse(m.predict(Xh), Rh, Uh)
                    sse_off[ms] = s_
                    runs.append({"model": "TSTR_x3off", "generation_seed": 0, "model_seed": ms, "rmse": float(np.sqrt(s_.sum() / nh.sum())), "epochs": m.history["epochs"]})
                    print(f"[w5-x3off] {ds} m{ms}: rmse {runs[-1]['rmse']:.2f}", flush=True)
                a_off = np.mean(list(sse_off.values()), axis=0)
                b = mean_sse(z5, [f"full__TRTR__m{ms}" for ms in model_seeds])
                a_v2_0 = mean_sse(z5, [f"full__TSTR__g0_m{ms}" for ms in model_seeds])
                a_v2_3 = mean_sse(z5, [f"full__TSTR__g{g}_m{ms}" for g in gen_seeds for ms in model_seeds])
                a_v1_d27 = mean_sse(z1, [f"full_D27__TSTR__g{g}_m{ms}" for g in gen_seeds for ms in model_seeds])
                b_v1_d27 = mean_sse(z1, [f"full_D27__TRTR__m{ms}" for ms in model_seeds])
                a_v1_full = mean_sse(z1, [f"full__TSTR__g{g}_m{ms}" for g in gen_seeds for ms in model_seeds])
                b_v1_full = mean_sse(z1, [f"full__TRTR__m{ms}" for ms in model_seeds])
                a_v1_d27_g0 = mean_sse(z1, [f"full_D27__TSTR__g0_m{ms}" for ms in model_seeds])
                ct.require(f"{ds}: V5 TRTR equals V1 full_D27 TRTR (the measured side of the X2-share comparator)",
                           np.allclose(b, b_v1_d27, rtol=1e-9), "equal", f"max rel {float(np.max(np.abs(b - b_v1_d27) / b)):.2e}")
                rb = lambda a, bb: F.ratio_bootstrap(a, bb, nh, seed=args.seed, n_resamples=n_boot)  # noqa: E731
                lrd = lambda p1, p2: F.log_ratio_difference_bootstrap(p1, p2, nh, seed=args.seed, n_resamples=n_boot)  # noqa: E731
                res = {"held_out_units": int(len(nh)), "held_out_windows": int(nh.sum()), "training_units": n_train,
                       "rows": {"v1_full_printed": rb(a_v1_full, b_v1_full), "v1_full_D27": rb(a_v1_d27, b_v1_d27),
                                "v2_without_x3_seed0": rb(a_off, b), "v2_seed0": rb(a_v2_0, b), "v2_three_seeds": rb(a_v2_3, b)},
                       "shares": {"X3_share_seed0": lrd((a_off, b), (a_v2_0, b)),
                                  "X2_share_vs_v1_full_D27": lrd((a_v1_d27, b_v1_d27), (a_off, b)),
                                  "not_read": {"X2_share_vs_v1_full_D17": lrd((a_v1_full, b_v1_full), (a_off, b)),
                                               "X2_share_vs_v1_full_D27_seed0": lrd((a_v1_d27_g0, b_v1_d27), (a_off, b))}},
                       "determinism": {"trtr_full_m0_max_rel_diff": d_trtr, "tstr_full_g0_m0_max_rel_diff": d_tstr},
                       "runs": runs}
                results[ds] = res
                np.savez(out / "tables" / f"per_unit_sse_x3off_{ds}.npz", units=np.array(ids), n_windows=nh,
                         **{f"full__TSTR__gx3off_m{ms}": v for ms, v in sse_off.items()})
                save_table(pd.DataFrame(runs), out / "tables" / f"tstr_runs_x3off_{ds}")
                r = res["rows"]
                print(f"[w5-x3off] {ds}: v1 {r['v1_full_printed']['ratio']:.3f} (D27 {r['v1_full_D27']['ratio']:.3f}) | v2 w/o X3 seed0 "
                      f"{r['v2_without_x3_seed0']['ratio']:.3f} [{r['v2_without_x3_seed0']['ci_low']:.3f}, {r['v2_without_x3_seed0']['ci_high']:.3f}] | "
                      f"v2 seed0 {r['v2_seed0']['ratio']:.3f} | v2 3 seeds {r['v2_three_seeds']['ratio']:.3f}", flush=True)
    write_json(results, out / "tables" / "tstr_without_x3.json")
    code = ct.finalize(out)
    (out / "logs" / "checks_tstr_without_x3.md").write_text(ct.markdown() + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
