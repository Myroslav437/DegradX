#!/usr/bin/env python
"""S2 — dataset property audit (paper §3.4: "before a profile is built"), measured on the data.

Inputs: ``data/processed/cycle_tables/<dataset>.csv.gz`` (S1). Per dataset and unit: capacity after the
declared glitch rule (D12) from the declared capacity source (D11); smoothed capacity; EOL attainment under the
r2 (nominal-anchored) and r1 (first-position-anchored) definitions over the declared rho grid; how often the robust
early-life reference differs materially from the first-position value; monotonicity within tolerance; unit
lengths; channel availability; and pattern detection with the S3 rule on the residual of the per-unit best of the
three candidate families, at the declared (k, m) and over the declared sweep. Outputs under
``artifacts/s2_audit_datasets/{tables,figures,logs}``; the per-unit records also feed S3's decisions.
"""

from __future__ import annotations

import sys
from concurrent.futures import ProcessPoolExecutor
from functools import partial

import numpy as np
import pandas as pd

from degradx import CONFIG_DIR, DATA_DIR
from degradx.data.audit import CleaningRule, audit_unit
from degradx.generator.state import spec_from_declarations
from degradx.utils.checks import CheckTable
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.config import load_yaml
from degradx.utils.io import save_figure, save_table, write_json
from degradx.utils.provenance import RunRecord

TABLES = DATA_DIR / "processed" / "cycle_tables"
PROFILE_FILES = {"MATR": "matr", "HUST": "hust", "NASA_PCoE": "nasa_pcoe"}


def audit_dataset(ds: str, ctx) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    decl = ctx.declarations
    dd = decl["declared_by_design"]
    cfg = ctx.config
    q_nom = float(load_yaml(CONFIG_DIR / "profiles" / f"{PROFILE_FILES[ds]}.yaml")["nominal_capacity_Ah"]["value"])
    spec = spec_from_declarations(decl, q_nom)
    rule = CleaningRule(**cfg["cleaning_rule"])
    df = pd.read_csv(TABLES / f"{ds}.csv.gz", low_memory=False)
    if ds == "MATR":  # declarations datasets.matr_batches (D14)
        batches = [f"{str(b)[:4]}-{str(b)[4:6]}-{str(b)[6:]}" for b in dd["datasets"]["matr_batches"]["value"]]
        df = df[df["batch"].isin(batches)]
    fn = partial(audit_unit, column=cfg["capacity_column"], rule=rule, q_nom=q_nom, decl=decl,
                 rho_grid=dd["eol"]["rho_sensitivity_grid"]["value"], k_grid=dd["eol"]["q1_reference"]["sensitivity_k"],
                 sweep_k=dd["pattern_detection"]["sweep"]["multiple_k"], sweep_m=dd["pattern_detection"]["sweep"]["min_run_length"],
                 k_default=float(dd["pattern_detection"]["multiple_k"]["value"]), m_default=int(dd["pattern_detection"]["min_run_length"]["value"]),
                 mono_tol=float(dd["audit"]["monotonicity_tolerance"]["value"]), spec_base=spec)
    # channel availability within scope: a channel is available in a unit if >= 50% of its non-degenerate cycles carry a
    # finite value (IR recorded as exactly 0 counts as missing); "available in every unit" feeds channels.availability_rule
    nd = df[~df["degenerate"].astype(bool)]
    avail = {}
    for ch in ("charge_time_min", "mean_discharge_voltage_V", "internal_resistance_ohm", "temperature_mean_C"):
        v = nd[ch].where(~((ch == "internal_resistance_ohm") & (nd[ch] == 0)))
        per_unit = v.notna().groupby(nd["cell_id"]).mean() >= 0.5
        avail[ch] = {"units_with_channel": int(per_unit.sum()), "units": int(per_unit.size), "available_in_every_unit": bool(per_unit.all())}
    groups = [g for _, g in df.groupby("cell_id", sort=True)]
    with ProcessPoolExecutor(max_workers=ctx.args.workers) as ex:
        recs = list(ex.map(fn, groups, chunksize=2))
    traces = {r["cell_id"]: r.pop("_trace") for r in recs if "_trace" in r}
    patterns = pd.DataFrame([p for r in recs for p in r.pop("patterns", [])])
    units = pd.DataFrame(recs)
    units.insert(1, "dataset", ds)
    units.attrs["channel_availability"] = avail
    return units, patterns, traces


def main() -> int:
    p = stage_parser(__doc__, "s2_audit_datasets")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--datasets", nargs="*", default=list(PROFILE_FILES))
    args = p.parse_args()
    ctx = StageContext.from_args(args)
    if args.dry_run:
        print(f"plan: audit {args.datasets} with capacity column {ctx.config.get('capacity_column')} and rule {ctx.config.get('cleaning_rule')}")
        return 0
    from degradx.viz import s2 as viz

    ct = CheckTable()
    out, fig_dir, tab_dir = ctx.out_dir, ctx.out_dir / "figures", ctx.out_dir / "tables"
    dd = ctx.declarations["declared_by_design"]
    with RunRecord("s2_audit_datasets", out, ctx.config, {"note": "deterministic; family multistarts are a fixed grid"}, ctx.device) as rec:
        all_units, all_patterns, all_traces = [], [], {}
        for ds in args.datasets:
            with rec.section(f"audit_{ds}"):
                units, patterns, traces = audit_dataset(ds, ctx)
            patterns.insert(0, "dataset", ds) if len(patterns) else None
            avail_all = locals().setdefault("avail_all", {})
            avail_all[ds] = units.attrs.get("channel_availability", {})
            all_units.append(units)
            all_patterns.append(patterns)
            all_traces[ds] = traces
        units = pd.concat(all_units, ignore_index=True)
        patterns = pd.concat([p for p in all_patterns if len(p)], ignore_index=True) if any(len(p) for p in all_patterns) else pd.DataFrame()
        save_table(units, tab_dir / "units")
        save_table(patterns, tab_dir / "patterns_default_threshold")
        summary = viz.summarise(units, patterns, dd)
        summary["channel_availability"] = avail_all
        write_json(summary, tab_dir / "summary.json")
        save_table(pd.DataFrame(summary["attainment_rows"]), tab_dir / "eol_attainment")
        save_table(pd.DataFrame(summary["sweep_rows"]), tab_dir / "detection_sweep")
        with rec.section("figures"):
            for name, fig in viz.all_figures(units, patterns, all_traces, dd, ctx.config).items():
                save_figure(fig, fig_dir / name)
        # checks: the audit is a measurement, so checks cover integrity, not outcomes
        for ds in args.datasets:
            u = units[units["dataset"] == ds]
            ct.require(f"{ds}: every unit audited", len(u) > 0 and u["n_kept"].notna().all(), "all units", len(u))
            ct.require(f"{ds}: family fits finite for every audited unit", bool(u.loc[~u["too_short"], [c for c in u if c.startswith("rmse_")]].notna().all().all()),
                       "finite", "finite" if u.loc[~u["too_short"], [c for c in u if c.startswith("rmse_")]].notna().all().all() else "some NaN", severity="warn")
            r = u[~u["too_short"].astype(bool) & u["T"].notna()]
            ct.require(f"{ds}: T >= t1 for every unit reaching EOL (D15)", bool((r["T"] >= r["t1"]).all()), "all", f"{int((r['T'] < r['t1']).sum())} violations")
            ct.require(f"{ds}: no record-end T for a unit whose smoothed state crossed", bool((~r["T_from_record_end"].astype(bool) | (r["T"] == r["n_kept"])).all()),
                       "record-end T equals last kept position", "ok")
            p_ds = patterns[patterns["dataset"] == ds] if len(patterns) else pd.DataFrame()
            if len(p_ds):
                fr = u.set_index("cell_id")[["fit_start", "fit_end"]]
                inside = p_ds.join(fr, on="cell_id")
                ok_in = bool(((inside["start"] >= inside["fit_start"]) & (inside["end"] <= inside["fit_end"])).all())
                ct.require(f"{ds}: every detected pattern lies inside its unit's fit range [t1, T]", ok_in, "all inside", ok_in)
                w = int(dd["smoothing"]["window_length"]["value"])
                m = int(dd["pattern_detection"]["min_run_length"]["value"])
                ct.require(f"{ds}: pattern durations within [m, smoothing window] (D16)", bool(p_ds["duration"].between(m, w).all()), f"[{m}, {w}]",
                           f"[{int(p_ds['duration'].min())}, {int(p_ds['duration'].max())}]")
        rec.extra["datasets"] = args.datasets
        code = ct.finalize(out)
        (out / "logs" / "checks.md").write_text(ct.markdown() + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
