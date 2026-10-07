#!/usr/bin/env python
"""V2 (brief "DegradX v2", X6) — third dataset: ISU-ILCC under decision D28 (declarations r3
v2.third_profile.candidate_rules). Runs alongside MATR/HUST and never blocks them.

  --ingest   one cell at a time (a process per cell, released after it): Cycling and RPT JSON read directly from the
             downloaded zips, converted with degradx.data.isu_ilcc (declared predicates, anchors, f, channels, rest events),
             per-cell tables under data/v2/processed/isu_ilcc_cells/, the in-scope cycle table
             data/v2/processed/cycle_tables/ISU_ILCC.csv.gz, the side table of the 10 released in-range cells outside the
             authors' list, and converter checks against the raw arrays
  --audit    S2-style audit (EOL attainment under D13/D15, monotonicity, families, detection sweep, channel availability),
             the eligibility re-check E3-E5 under the declared rules, and the declared X6(ii) diagnostics: D05 per stratum,
             mechanism diagnostic with placebo window, recovery index and overshoot, operator-null check, additive
             sensitivity, q1-versus-C/5 and EOL-agreement cross-checks
Outputs in ``artifacts/v2/v2_third_dataset``. Raw files and their checksums: data/v2/raw/isu_ilcc, configs/raw_checksums_v2.sha256.
"""

from __future__ import annotations

import json
import sys
import zipfile
from multiprocessing import get_context
from pathlib import Path

import numpy as np
import pandas as pd

import _common as C
from degradx import CONFIG_DIR, DATA_V2
from degradx.data import isu_ilcc as ISU
from degradx.utils.checks import CheckTable
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.io import save_table, write_json
from degradx.utils.provenance import RunRecord

DS = "ISU_ILCC"
RAW = DATA_V2 / "raw" / "isu_ilcc"
CELLS_DIR = DATA_V2 / "processed" / "isu_ilcc_cells"
TABLE = DATA_V2 / "processed" / "cycle_tables" / f"{DS}.csv.gz"
SIDE = ["G9C3", "G11C1", "G11C2", "G11C3", "G11C4", "G14C2", "G14C3", "G14C4", "G36C1", "G37C1"]


def table_a1() -> pd.DataFrame:
    return pd.read_csv(CONFIG_DIR / "reference_facts" / "isu_ilcc_tableA1.csv", comment="#").set_index("group")


def members(zpath: Path) -> dict:
    with zipfile.ZipFile(zpath) as zf:
        return {Path(n).stem: n for n in zf.namelist() if n.endswith(".json")}


def _convert(args):
    cell, cyc_member, rpt_member, meta = args
    with zipfile.ZipFile(RAW / "Cycling_json.zip") as zc, zipfile.ZipFile(RAW / "RPT_json.zip") as zr:
        cyc = ISU.load_json_from_zip(zc, cyc_member)
        rpt = ISU.load_json_from_zip(zr, rpt_member)
    res = ISU.convert_cell(cell, cyc, rpt, meta)
    # C/5 series for the cross-checks (EOL interval, q1 vs week-0 C/5)
    c5 = [ISU._num(v) for v in rpt["capacity_discharge_C_5"]]
    r_start = [ISU._ts(v) for v in rpt["start_stop_time"]["start"]]
    if res.table is not None:
        CELLS_DIR.mkdir(parents=True, exist_ok=True)
        res.table.to_csv(CELLS_DIR / f"{cell}.csv.gz", index=False)
    return {"cell_id": cell, "excluded": res.excluded, "anchors": res.anchors, "checks": res.checks, "c5": c5, "rpt_start": r_start, "meta": meta}


def ingest(ctx, dd, workers: int) -> dict:
    cr = dd["v2"]["third_profile"]["candidate_rules"]
    a1 = table_a1()
    scope = list(cr["scope"]["cells"])
    full_groups = set(cr["strata"]["S_full"]["groups"])
    cyc_m, rpt_m = members(RAW / "Cycling_json.zip"), members(RAW / "RPT_json.zip")
    jobs = []
    for cell in scope + SIDE:
        g = int(cell[1:cell.index("C")])
        meta = {"group": g, "mean_dod": float(a1.loc[g, "mean_DoD_percent"]) / 100, "c_chg": float(a1.loc[g, "charge_C_rate"]),
                "c_dis": float(a1.loc[g, "discharge_C_rate"]), "stratum": "S_full" if g in full_groups else "S_partial", "in_scope": cell in scope}
        if cell not in cyc_m or cell not in rpt_m:
            jobs.append((cell, None, None, meta))
            continue
        jobs.append((cell, cyc_m[cell], rpt_m[cell], meta))
    missing = [j[0] for j in jobs if j[1] is None]
    run = [j for j in jobs if j[1] is not None]
    with get_context("spawn").Pool(workers, maxtasksperchild=1) as pool:
        recs = []
        for r in pool.imap_unordered(_convert, run, chunksize=1):
            recs.append(r)
            print(f"[v2] {r['cell_id']}: {'EXCLUDED ' + r['excluded'] if r['excluded'] else 'ok'} {json.dumps({k: v for k, v in r['checks'].items() if k != 'f_stats'})}", flush=True)
    recs.sort(key=lambda r: r["cell_id"])
    frames = [pd.read_csv(CELLS_DIR / f"{r['cell_id']}.csv.gz") for r in recs if r["excluded"] is None and r["meta"]["in_scope"]]
    TABLE.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(frames, ignore_index=True).to_csv(TABLE, index=False)
    return {"cells": recs, "missing_in_release": missing}


def main() -> int:
    p = stage_parser(__doc__, "v2/v2_third_dataset")
    p.add_argument("--ingest", action="store_true")
    p.add_argument("--audit", action="store_true")
    p.add_argument("--workers", type=int, default=3)
    args = p.parse_args()
    C.register_profile(DS, "isu_ilcc")
    ctx = StageContext.from_args(args)
    decl, dd = ctx.declarations, ctx.declarations["declared_by_design"]
    if args.dry_run:
        print("plan: ingest / audit ISU-ILCC under D28")
        return 0
    out, ct = ctx.out_dir, CheckTable()
    with RunRecord("v2/v2_third_dataset", out, {"config": ctx.config, "ingest": args.ingest, "audit": args.audit}, {"generation": "D28-null streams", "split": args.seed},
                   ctx.device) as rec:
        if args.ingest:
            with rec.section("ingest"):
                res = ingest(ctx, dd, args.workers)
            write_json(res, out / "tables" / "ingest.json")
            cells = res["cells"]
            ct.require("ingest: every in-scope cell present in the release", not [c for c in res["missing_in_release"] if c not in SIDE], "none missing",
                       ", ".join(res["missing_in_release"]) or "none missing")
            inscope = [c for c in cells if c["meta"]["in_scope"]]
            ct.require("ingest: converter anchor identity (calibrated capacity at every anchor equals the C/5 value)",
                       all(c["checks"].get("anchor_identity_max_abs_Ah") is None or c["checks"]["anchor_identity_max_abs_Ah"] < 1e-9 for c in inscope), "< 1e-9 Ah",
                       f"{max((c['checks'].get('anchor_identity_max_abs_Ah') or 0) for c in inscope):.2e}")
            ct.require("ingest: cycler capacity equals the max of the discharge Q samples (raw-array check)",
                       all((c["checks"].get("max_abs_capacity_vs_max_Q_Ah") or 0) < 1e-6 for c in inscope), "< 1e-6 Ah",
                       f"{max((c['checks'].get('max_abs_capacity_vs_max_Q_Ah') or 0) for c in inscope):.2e}", severity="warn")
            ct.require("ingest: charge time from step times equals the sample span (raw-array check)",
                       all((c["checks"].get("max_abs_charge_time_vs_samples_min") or 0) < 1.0 for c in inscope), "< 1 min",
                       f"{max((c['checks'].get('max_abs_charge_time_vs_samples_min') or 0) for c in inscope):.3f}", severity="warn")
            nonmono = [c["cell_id"] for c in inscope if not c["checks"].get("time_monotone", True)]
            ct.require("ingest: cycle start times strictly increasing (reported: logger clock steps back in some cells; file order is chronological)",
                       not nonmono, "all", f"{len(nonmono)} cells with a backward timestamp step: {', '.join(nonmono)}", severity="warn")
            excl = [c["cell_id"] for c in inscope if c["excluded"]]
            ct.require("ingest: in-scope cells with fewer than 2 anchors (reported; count against E4 if at EOL)", not excl, "none", ", ".join(excl) or "none", severity="warn")
        if args.audit:
            import v2_audit_isu as A

            with rec.section("audit"):
                summary = A.audit(ctx, dd, decl, out, ct)
            write_json(summary, out / "tables" / "audit_summary.json")
        code = ct.finalize(out)
        (out / "logs" / f"checks_{'ingest' if args.ingest else 'audit'}.md").write_text(ct.markdown() + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
