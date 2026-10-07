#!/usr/bin/env python
"""V3 (brief "DegradX v2", X2 + X3) — refit the profiles with per-unit offsets and the residual correlation the
generator draws its noise with (declarations r3 declared_by_design.v2.per_unit_offsets / correlated_noise; D27).

Per profile, on the measured fitting split (recomputed with the declared seed; for MATR and HUST checked identical to the
v1 S3 split table):
  * the v1 six-step fit (paper §3.3) with the extended channel glitch rule (D27, runs of up to three positions);
  * X2: non-capacity mappings phi_c(z) + delta_{c,i} by backfitting (median_i delta = 0, declared tolerance and
    iteration cap); capacity affine with the unit's own q1; x0 at the median q1;
  * X3: the pooled residual cross-channel correlation after the offsets (E4), which V4 generates noise with;
  * reported: residual variance and lag-1 per channel before (r2 residual) and after the offsets; correlation before
    and after; offsets per channel; backfit convergence.
Outputs in ``artifacts/v2/v3_fit_profiles`` (profiles/<dataset>.json, tables/, figures/, logs/).
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

import _common as C
from degradx import ARTIFACTS_DIR
from degradx.data.audit import CleaningRule, clean_capacity
from degradx.data.splits import measured_split
from degradx.fitting.noise_mappings import fit_isotonic_pchip
from degradx.fitting.profile import fit_profile
from degradx.generator.state import spec_from_declarations, unit_state
from degradx.utils.checks import CheckTable
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.io import save_figure, save_table, write_json
from degradx.utils.provenance import RunRecord

ESTIMATED_KEYS = {"E1_theta_distribution", "E2_family_choice", "E3_channel_mappings", "E4_channel_covariance", "E5_noise",
                  "E6_patterns", "E7_length_distribution"}


def main() -> int:
    p = stage_parser(__doc__, "v2/v3_fit_profiles")
    p.add_argument("--workers", type=int, default=12)
    p.add_argument("--datasets", nargs="*", default=["MATR", "HUST"])
    p.add_argument("--profile-config", nargs="*", default=[], help="extra dataset=config_stem pairs (third profile)")
    args = p.parse_args()
    for kv in args.profile_config:
        C.register_profile(*kv.split("="))
    ctx = StageContext.from_args(args)
    decl, dd = ctx.declarations, ctx.declarations["declared_by_design"]
    if args.dry_run:
        print(f"plan: v2 profiles (X2 offsets, X3 correlation, D27 channel rule) for {args.datasets}")
        return 0
    from degradx.viz import s3 as viz3
    from degradx.viz import v3 as viz

    out = ctx.out_dir
    (out / "profiles").mkdir(parents=True, exist_ok=True)
    ct = CheckTable()
    rule = CleaningRule("D12", **dd["capacity_series"]["cleaning_rule"]["params"])
    crule = C.channel_rule_v2(dd)
    offs = C.offsets_params(dd)
    k = float(dd["pattern_detection"]["multiple_k"]["value"])
    m = int(dd["pattern_detection"]["min_run_length"]["value"])
    sweep_k = dd["pattern_detection"]["sweep"]["multiple_k"]
    summary = json.loads((ctx.out_dir / "tables" / "summary.json").read_text()) if (ctx.out_dir / "tables" / "summary.json").exists() else {}
    seeds = {"split": f"derive_seed({args.seed}, 'split', <dataset>)", "D05_noise": f"derive_seed({args.seed}, 'generation', 'D05', <dataset>)"}
    with RunRecord("v2/v3_fit_profiles", out, {"config": ctx.config, "datasets": args.datasets, "channel_rule": crule.__dict__, "offsets": offs},
                   seeds, ctx.device) as rec:
        for ds in args.datasets:
            q_nom = C.q_nom_of(ds)
            spec = spec_from_declarations(decl, q_nom)
            df = C.load_scope(ds, dd)
            channels = C.available_channels(df)
            with rec.section(f"{ds}_split"):
                elig = []
                for cid, g in df.groupby("cell_id"):
                    d = clean_capacity(g, "capacity_cycler_Ah", rule, q_nom)
                    if len(d) < max(20, spec.sg_window):
                        continue
                    st = unit_state(d["capacity_cycler_Ah"].to_numpy(float), spec)
                    if not st.excluded_by_guard:
                        elig.append({"cell_id": cid, "reaches_eol": st.T is not None})
                split = measured_split(pd.DataFrame(elig), args.seed, ds, float(dd["statistics"]["splits"]["measured"]["fitting"]))
                save_table(split, out / "tables" / f"split_{ds}")
                v1_split = ARTIFACTS_DIR / "s3_fit_profiles" / "tables" / f"split_{ds}.csv"
                if v1_split.exists():
                    same = pd.read_csv(v1_split).sort_values("cell_id").reset_index(drop=True)[["cell_id", "split"]].equals(
                        split.sort_values("cell_id").reset_index(drop=True)[["cell_id", "split"]])
                    ct.require(f"{ds}: measured split identical to v1 (same units held out)", same, "identical", same)
            with rec.section(f"{ds}_fit"):
                prof, diag = fit_profile(df, split, dataset=ds, q_nom=q_nom, spec=spec, rule=rule, channels=channels, crule=crule, decl=decl,
                                         workers=args.workers, k=k, m=m, sweep_k=sweep_k, base_seed=args.seed, offsets=offs)
            prof["declared_used"]["channels_available"] = channels
            write_json(prof, out / "profiles" / f"{ds}.json")
            u = diag["units"]
            save_table(u.drop(columns=["noise", "offsets"]), out / "tables" / f"units_{ds}")
            save_table(pd.DataFrame([{"cell_id": cid, **d} for cid, d in prof["v2"]["offsets_all_fitting_units"].items()]), out / "tables" / f"offsets_{ds}")
            save_table(diag["patterns"], out / "tables" / f"patterns_{ds}")
            save_table(diag["sweep"].groupby("k").sum(numeric_only=True).reset_index(), out / "tables" / f"detection_sweep_{ds}")
            e = prof["estimated_from_data"]
            ba = prof["v2"]["residual_before_after"]
            save_table(pd.DataFrame([{"channel": c, "variance_before": v["before_r2"]["variance"], "lag1_before": v["before_r2"]["phi"],
                                      "variance_after": v["after_offsets"]["variance"], "lag1_after": v["after_offsets"]["phi"],
                                      "variance_ratio": v["variance_ratio_after_to_before"]} for c, v in ba.items()]), out / "tables" / f"residual_before_after_{ds}")
            with rec.section(f"{ds}_figures"):
                units = diag["unit_objects"]
                maps_r2 = {}
                for c in channels:
                    if c == "capacity":
                        continue
                    maps_r2[c] = fit_isotonic_pchip(c, np.concatenate([uu.state.z[uu.fit_start - 1:uu.fit_end] for uu in units]),
                                                    np.concatenate([uu.channels[c][uu.fit_start - 1:uu.fit_end] for uu in units]))
                save_figure(viz.offsets_mappings(ds, units, diag["mappings"], maps_r2, prof["v2"]["offsets_all_fitting_units"], channels),
                            out / "figures" / f"{ds.lower()}_offsets_mappings")
                save_figure(viz.residual_before_after(ds, ba), out / "figures" / f"{ds.lower()}_residual_before_after")
                save_figure(viz.correlation_before_after(ds, channels, prof["v2"]["correlation_r2_residuals"], e["E4_channel_covariance"]["correlation"]),
                            out / "figures" / f"{ds.lower()}_correlation_before_after")
                save_figure(viz3.cv_errors(ds, u, e["E2_family_choice"]), out / "figures" / f"{ds.lower()}_family_cv_errors")
                save_figure(viz3.sweep(ds, diag["sweep"], e["E6_patterns"], k), out / "figures" / f"{ds.lower()}_detection_sweep")
            # ---- checks
            reach = u[u["reaches_eol"]]
            ct.require(f"{ds}: estimated/declared split matches paper §3.3 (E1-E7 only under estimated_from_data)", set(e.keys()) == ESTIMATED_KEYS,
                       sorted(ESTIMATED_KEYS), sorted(e.keys()))
            aff = prof["derived"]["capacity_affinity_max_abs_error_Ah"]
            ct.require(f"{ds}: capacity affine in z per unit with the unit's own q1 (Eq. 3; X2 capacity mapping)", aff < 1e-9, "< 1e-9 Ah", f"{aff:.2e}")
            for c, mp in diag["mappings"].items():
                if mp.kind == "isotonic_pchip":
                    zz = np.linspace(0, 1, 1001)
                    dv = np.diff(mp(zz))
                    mono = bool(np.all(dv >= -1e-12) if mp.increasing else np.all(dv <= 1e-12))
                    ct.require(f"{ds}: phi_{c} monotone on [0, 1] (backfitted)", mono, "monotone", mono)
            for c, b in prof["v2"]["backfit"].items():
                ct.require(f"{ds}: backfit of {c} converged within {offs['max_iter']} iterations (declared tolerance 1e-4 of the mapping range)", b["converged"],
                           "converged", f"{b['iterations']} it., last change δ {b['last_change_delta']:.2e} / φ {b['last_change_phi']:.2e} (tol {b['tolerance']:.2e})", severity="warn")
                med = float(np.median([d[c] for d in prof["v2"]["offsets_all_fitting_units"].values()]))
                ct.require(f"{ds}: median offset of {c} over fitting units = 0 (constraint)", abs(med) < 1e-9 * max(1.0, abs(b["phi0_r2"])), "0", f"{med:.2e}")
            centred = float((reach["residual_mean_over_scale"].abs() <= 0.5).mean()) if len(reach) else float("nan")
            ct.require(f"{ds}: fit residuals centred (|mean| <= 0.5 residual scale) in >= 90% of units", centred >= 0.9, ">= 0.90", f"{centred:.3f}")
            at_bound = float((reach["family_at_bound"].apply(len) > 0).mean()) if len(reach) else float("nan")
            ct.require(f"{ds}: theta not collapsing to bounds (units with any parameter at a bound <= 20%)", at_bound <= 0.2, "<= 0.20", f"{at_bound:.3f}", severity="warn")
            ct.require(f"{ds}: theta from >= 5 units reaching EOL (D02)", len(reach) >= int(dd["minimum_counts"]["value"]["theta_and_length_units"]), ">= 5", len(reach), severity="warn")
            v1p = ARTIFACTS_DIR / "s3_fit_profiles" / "profiles" / f"{ds}.json"
            v1fam = None
            if v1p.exists():
                v1prof = json.loads(v1p.read_text())
                v1fam = v1prof["estimated_from_data"]["E2_family_choice"]["selected"]
                ct.require(f"{ds}: trajectory family unchanged from v1 (capacity cleaning unchanged)", v1fam == e["E2_family_choice"]["selected"], v1fam,
                           e["E2_family_choice"]["selected"], severity="warn")
            summary[ds] = {"family": e["E2_family_choice"]["selected"], "family_v1": v1fam, "channels": channels,
                           "weighted": prof["derived"]["channel_roles"]["weighted"], "demoted": prof["derived"]["channel_roles"]["demoted_by_guard"],
                           "x0": prof["derived"]["reference_point_x0"], "backfit": prof["v2"]["backfit"], "residual_before_after": ba,
                           "correlation_before": prof["v2"]["correlation_r2_residuals"], "correlation_after": e["E4_channel_covariance"]["correlation"],
                           "q1_fitting_units": prof["v2"]["q1_fitting_units"], "noise": e["E5_noise"],
                           "patterns_enabled": {t: v["enabled"] for t, v in e["E6_patterns"].items()},
                           "patterns_ratio_to_noise": {t: v["ratio_to_noise"] for t, v in e["E6_patterns"].items()},
                           "units": {"fitting_passing_guard": len(prof["units"]["fitting_passing_guard"]), "fitting_reaching_eol": len(prof["units"]["fitting_reaching_eol"])}}
            write_json(summary, out / "tables" / "summary.json")
        code = ct.finalize(out)
        (out / "logs" / ("checks.md" if set(args.datasets) == {"MATR", "HUST"} else f"checks_{'_'.join(args.datasets)}.md")).write_text(ct.markdown() + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
