#!/usr/bin/env python
"""S3 — profile fitting (paper §3.3, six steps, in order), one profile per dataset.

Inputs: ``data/processed/cycle_tables/<dataset>.csv.gz`` (S1); declarations r2 with the dated decisions D02, D04, D05,
D11-D17. Per dataset: eligible units (pass the denominator guard after cleaning) are split into fitting / held-out at
unit level, stratified by EOL attainment (seed stream 'split'); the profile is fitted on the fitting split only.
Outputs: ``artifacts/s3_fit_profiles/profiles/<dataset>.json`` (the profile: estimated_from_data E1-E7, declared values
used, derived channel roles and reference point), ``tables/`` (splits, per-unit fits, patterns, detection sweep,
family selection), ``figures/`` (per dataset), ``logs/``. Exits non-zero on a failed check.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from degradx import CONFIG_DIR, DATA_DIR
from degradx.data.audit import CleaningRule, clean_capacity
from degradx.data.splits import measured_split
from degradx.fitting.profile import ChannelRule, fit_profile
from degradx.generator.state import spec_from_declarations, unit_state
from degradx.utils.checks import CheckTable
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.config import load_yaml
from degradx.utils.io import save_figure, save_table, write_json
from degradx.utils.provenance import RunRecord

TABLES = DATA_DIR / "processed" / "cycle_tables"
PROFILE_FILES = {"MATR": "matr", "HUST": "hust", "NASA_PCoE": "nasa_pcoe"}
CANDIDATES = ["capacity", "charge_time", "mean_discharge_voltage", "internal_resistance", "temperature_mean"]
ESTIMATED_KEYS = {"E1_theta_distribution", "E2_family_choice", "E3_channel_mappings", "E4_channel_covariance", "E5_noise",
                  "E6_patterns", "E7_length_distribution"}


def load_scope(ds: str, dd: dict) -> pd.DataFrame:
    df = pd.read_csv(TABLES / f"{ds}.csv.gz", low_memory=False)
    if ds == "MATR":
        batches = [f"{str(b)[:4]}-{str(b)[4:6]}-{str(b)[6:]}" for b in dd["datasets"]["matr_batches"]["value"]]
        df = df[df["batch"].isin(batches)]
    return df


def available_channels(df: pd.DataFrame) -> list[str]:
    """declarations channels.availability_rule: a candidate is used iff available in every unit (S2 definition)."""
    from degradx.fitting.profile import CHANNEL_COLUMNS

    nd = df[~df["degenerate"].astype(bool)]
    out = ["capacity"]
    for c in CANDIDATES[1:]:
        v = nd[CHANNEL_COLUMNS[c]]
        if c == "internal_resistance":
            v = v.where(v != 0)
        if (v.notna().groupby(nd["cell_id"]).mean() >= 0.5).all():
            out.append(c)
    return out


def main() -> int:
    p = stage_parser(__doc__, "s3_fit_profiles")
    p.add_argument("--workers", type=int, default=12)
    p.add_argument("--datasets", nargs="*", default=list(PROFILE_FILES))
    args = p.parse_args()
    ctx = StageContext.from_args(args)
    decl, dd = ctx.declarations, ctx.declarations["declared_by_design"]
    if args.dry_run:
        print(f"plan: fit profiles for {args.datasets}; seed {args.seed}")
        return 0
    from degradx.viz import s3 as viz

    out = ctx.out_dir
    (out / "profiles").mkdir(parents=True, exist_ok=True)
    ct = CheckTable()
    cap = dd["capacity_series"]["cleaning_rule"]["params"]
    rule = CleaningRule("D12", **cap)
    crule = ChannelRule(float(dd["channel_series"]["cleaning_rule"]["frac"]))
    k = float(dd["pattern_detection"]["multiple_k"]["value"])
    m = int(dd["pattern_detection"]["min_run_length"]["value"])
    sweep_k = dd["pattern_detection"]["sweep"]["multiple_k"]
    seeds = {"split": f"derive_seed({args.seed}, 'split', <dataset>)", "D05_noise": f"derive_seed({args.seed}, 'generation', 'D05', <dataset>)"}
    with RunRecord("s3_fit_profiles", out, {"config": ctx.config, "datasets": args.datasets}, seeds, ctx.device) as rec:
        for ds in args.datasets:
            q_nom = float(load_yaml(CONFIG_DIR / "profiles" / f"{PROFILE_FILES[ds]}.yaml")["nominal_capacity_Ah"]["value"])
            spec = spec_from_declarations(decl, q_nom)
            df = load_scope(ds, dd)
            channels = available_channels(df)
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
            with rec.section(f"{ds}_fit"):
                prof, diag = fit_profile(df, split, dataset=ds, q_nom=q_nom, spec=spec, rule=rule, channels=channels, crule=crule, decl=decl,
                                         workers=args.workers, k=k, m=m, sweep_k=sweep_k, base_seed=args.seed)
            prof["declared_used"]["channels_available"] = channels
            write_json(prof, out / "profiles" / f"{ds}.json")
            u = diag["units"]
            save_table(u.drop(columns=["noise"]), out / "tables" / f"units_{ds}")
            save_table(diag["patterns"], out / "tables" / f"patterns_{ds}")
            save_table(diag["sweep"].groupby("k").sum(numeric_only=True).reset_index(), out / "tables" / f"detection_sweep_{ds}")
            e = prof["estimated_from_data"]
            save_table(pd.DataFrame([{"family": n, "median_cv_rmse": e["E2_family_choice"]["median_cv_rmse"][n],
                                      "median_in_sample_rmse": e["E2_family_choice"]["median_in_sample_rmse"][n],
                                      "selected": n == e["E2_family_choice"]["selected"]} for n in e["E2_family_choice"]["median_cv_rmse"]]),
                       out / "tables" / f"family_selection_{ds}")
            with rec.section(f"{ds}_figures"):
                units = diag["unit_objects"]
                scales = dict(zip(u["cell_id"], u["residual_scale_Ah"]))
                figs = {
                    "capacity_eol_sheet": viz.capacity_sheet(ds, units, q_nom, spec.rho),
                    "family_fits": viz.family_fits(ds, units, e["E2_family_choice"]["selected"]),
                    "family_cv_errors": viz.cv_errors(ds, u, e["E2_family_choice"]),
                    "theta_distributions": viz.theta_distributions(ds, prof),
                    "channel_mappings": viz.mappings(ds, units, diag["mappings"], channels),
                    "residual_acf": viz.residual_acf(ds, diag["residuals"], diag["masks"], channels, e["E5_noise"]),
                    "pattern_traces": viz.pattern_traces(ds, units, diag["residuals"], diag["patterns"], k, scales),
                    "detection_sweep": viz.sweep(ds, diag["sweep"], e["E6_patterns"], k),
                    "length_distribution": viz.lengths(ds, e["E7_length_distribution"]),
                }
                for name, fig in figs.items():
                    save_figure(fig, out / "figures" / f"{ds.lower()}_{name}")
            # ---- checks
            reach = u[u["reaches_eol"]]
            ct.require(f"{ds}: estimated/declared split matches paper §3.3 (E1-E7 only under estimated_from_data)",
                       set(e.keys()) == ESTIMATED_KEYS, sorted(ESTIMATED_KEYS), sorted(e.keys()))
            aff = prof["derived"]["capacity_affinity_max_abs_error_Ah"]
            ct.require(f"{ds}: capacity mapping affine in z per unit (Eq. 3)", aff < 1e-9, "< 1e-9 Ah", f"{aff:.2e}")
            for c, mp in diag["mappings"].items():
                if mp.kind == "isotonic_pchip":
                    zz = np.linspace(0, 1, 1001)
                    dv = np.diff(mp(zz))
                    mono = bool(np.all(dv >= -1e-12) if mp.increasing else np.all(dv <= 1e-12))
                    ct.require(f"{ds}: phi_{c} monotone on [0, 1]", mono, "monotone", mono)
            centred = float((reach["residual_mean_over_scale"].abs() <= 0.5).mean()) if len(reach) else float("nan")
            ct.require(f"{ds}: fit residuals centred (|mean| <= 0.5 residual scale) in >= 90% of units", centred >= 0.9, ">= 0.90", f"{centred:.3f}")
            at_bound = float((reach["family_at_bound"].apply(len) > 0).mean()) if len(reach) else float("nan")
            ct.require(f"{ds}: theta not collapsing to bounds (units with any parameter at a bound <= 20%)", at_bound <= 0.2, "<= 0.20",
                       f"{at_bound:.3f}", severity="warn")
            ct.require(f"{ds}: theta from >= 5 units reaching EOL (D02 minimum; else theta statistics void)", len(reach) >= int(dd["minimum_counts"]["value"]["theta_and_length_units"]),
                       ">= 5", len(reach), severity="warn")
            ct.require(f"{ds}: D05 enable rule evaluated for both types", all("ratio_to_noise" in v for v in e["E6_patterns"].values()), "evaluated", "evaluated")
            rec.extra[ds] = {"family": e["E2_family_choice"]["selected"], "channels": channels,
                             "enabled": {t: v["enabled"] for t, v in e["E6_patterns"].items()}}
        code = ct.finalize(out)
        (out / "logs" / "checks.md").write_text(ct.markdown() + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
