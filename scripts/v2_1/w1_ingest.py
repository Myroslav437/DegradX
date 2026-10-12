#!/usr/bin/env python
"""W1 (brief "DegradX v2.1") — convert the TRI/Stanford formation aging files to the DegradX cycle table under declarations
r4 declared_by_design.v2_1 (decision D32), one file per process (spawn, maxtasksperchild = 1, at most 3 processes).

  pass 1  per file (degradx.data.tri_formation.convert_file): BEEP writer markers and structuring_parameters, per-cycle summary
          quantities and sample statistics, diagnostic cycles, the positional charge-time validation;
          data/v2.1/processed/tri_cycles/<seq>_{cycles,diagnostics}.csv.gz
  pass 2  across files (build_cycle_table): cell scope (i)-(iv), the modal aging protocol and its tolerance, the second-protocol
          test, E2 on the files, non-aging cycles, predicates, positions, the charge-time mask, rest events (diagnostic, paused,
          gap; DST artefacts), formation protocol and tags; data/v2.1/processed/cycle_tables/TRI_FORMATION.csv.gz
  checks  declarations v2_1.converter_checks and the W1 stop cases (archive integrity was checked by w1_fetch.py)
Outputs in artifacts/v2.1/w1_ingest.
"""

from __future__ import annotations

import json
import re
import sys
from multiprocessing import get_context
from pathlib import Path

import numpy as np
import pandas as pd

from degradx import ARTIFACTS_V21, DATA_V21, REPO_ROOT
from degradx.data import tri_formation as T
from degradx.utils.checks import CheckTable
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.io import save_figure, save_table, write_json
from degradx.utils.provenance import RunRecord

DS = "TRI_FORMATION"
CELLS = DATA_V21 / "processed" / "tri_cycles"
TABLE = DATA_V21 / "processed" / "cycle_tables" / f"{DS}.csv.gz"
SEQ = re.compile(r"^Nova_Regular_(\d{3})(\.\d+)?\.json(\.gz)?$")
EXPECTED_DIAG = {"hppc": [0, 8, 24], "rpt_0.05C": [1, 25], "rpt_0.2C": [2, 26]}   # then +103k from 127 / 128 / 129


def _pass1(job):
    path, seq = job
    r = T.convert_file(Path(path), seq)
    if r.cycles is not None:
        CELLS.mkdir(parents=True, exist_ok=True)
        r.cycles.to_csv(CELLS / f"{seq}_cycles.csv.gz", index=False)
        r.diagnostics.to_csv(CELLS / f"{seq}_diagnostics.csv.gz", index=False)
    return {"name": r.name, "seq": seq, "record": r.record, "validation": r.validation, "error": r.error,
            "n_cycles": None if r.cycles is None else int(len(r.cycles))}


def expected_layout(max_ix: int) -> dict:
    out = {k: list(v) for k, v in EXPECTED_DIAG.items()}
    for k, first in (("hppc", 127), ("rpt_0.05C", 128), ("rpt_0.2C", 129)):
        out[k] += list(range(first, max_ix + 1, 103))
    return out


def main() -> int:
    p = stage_parser(__doc__, "v2.1/w1_ingest")
    p.add_argument("--workers", type=int, default=3)
    p.add_argument("--skip-pass1", action="store_true", help="reuse the per-file outputs of an earlier pass 1")
    args = p.parse_args()
    if args.workers > 3:
        print("[w1] declarations v2_1.archive.memory: at most 3 processes", flush=True)
        args.workers = 3
    ctx = StageContext.from_args(args)
    dd = ctx.declarations["declared_by_design"]["v2_1"]
    if args.dry_run:
        print("plan: W1 conversion of the TRI formation aging files")
        return 0
    out, ct = ctx.out_dir, CheckTable()
    man = json.loads((out / "tables" / "extraction_manifest.json").read_text())
    aging = [m for m in man["members"] if m["kind"] == "aging"]
    files = []
    for m in aging:
        base = Path(m["name"]).name
        mm = SEQ.match(base)
        files.append((str(REPO_ROOT / m["path"]), int(mm.group(1)) if mm else None, base))
    undocumented = [b for _, s, b in files if s is None]
    by_seq = pd.Series([s for _, s, _ in files if s is not None]).value_counts()
    several = by_seq[by_seq > 1].index.tolist()
    sheet = pd.read_csv(DATA_V21 / "raw" / "formation_mapping" / "Formation_2022-Parameter.csv")
    notes = pd.read_csv(DATA_V21 / "raw" / "formation_mapping" / "Formation_2022_Parameter_rhyu.csv", dtype=str)
    mapping = T.formation_mapping(sheet, notes)
    with RunRecord("v2.1/w1_ingest", out, {"files": len(files), "workers": args.workers}, {}, ctx.device) as rec:
        with rec.section("pass1"):
            if args.skip_pass1:
                res = json.loads((out / "tables" / "files.json").read_text())
            else:
                jobs = [(p_, s) for p_, s, _ in files if s is not None]
                with get_context("spawn").Pool(args.workers, maxtasksperchild=1) as pool:
                    res = []
                    for r in pool.imap_unordered(_pass1, jobs, chunksize=1):
                        res.append(r)
                        v = r["validation"]
                        print(f"[w1] {r['seq']}: {r['error'] or 'ok'} cycles {r['n_cycles']} validation "
                              f"{'n/e' if not v.get('evaluable') else ('pass' if v.get('passes') else 'FAIL')} o_med {v.get('o_median_min')}", flush=True)
                res.sort(key=lambda r: r["seq"])
                write_json(res, out / "tables" / "files.json")
        with rec.section("pass2"):
            cells = {}
            for r in res:
                if r["error"]:
                    continue
                cells[r["seq"]] = {"cycles": pd.read_csv(CELLS / f"{r['seq']}_cycles.csv.gz"),
                                   "diagnostics": pd.read_csv(CELLS / f"{r['seq']}_diagnostics.csv.gz"),
                                   "validation": r["validation"], "file": r["name"]}
            documented = {"I_chg": 0.24, "I_dis": 0.18, "V_cv": 4.4, "V_end": 3.0}
            built = T.build_cycle_table(cells, mapping, documented)
            table = built["table"]
            # D33: the r4 estimator as declared (p90 of all positive charge current), reported beside the D33 outcome
            lit_cells = {s: {**c, "cycles": c["cycles"].assign(I_chg=c["cycles"]["I_chg_p90_r4"])} for s, c in cells.items()}
            lit = T.build_cycle_table(lit_cells, mapping, documented)
            literal = {"excluded_by_reason": pd.Series([r.get("excluded") for r in lit["cells"].values() if r.get("excluded")]).value_counts().to_dict(),
                       "sources": len(lit["second_protocol"]["sources"]), "agreeing_pairs": len(lit["second_protocol"]["agreeing_pairs"]),
                       "second_protocol_present": lit["second_protocol"]["present"], "modal": lit["modal"]}
            TABLE.parent.mkdir(parents=True, exist_ok=True)
            table.to_csv(TABLE, index=False)
        # ---------------------------------------------------------------- checks and counts
        recs = {r["seq"]: r for r in res}
        errors = [r["seq"] for r in res if r["error"]]
        ct.require("archive: every declared aging member was extracted (extraction manifest)", not man.get("missing_after_extraction"), "none missing",
                   str(man.get("missing_after_extraction")))
        ct.require("files: every aging file parses as BEEP JSON", not errors, "all", ", ".join(map(str, errors)) or "all")
        ct.require("cell_scope (i): every aging file name matches the declared seq pattern (undocumented files counted)", True, "reported",
                   f"{len(undocumented)} undocumented: {undocumented}", severity="warn")
        ct.require("cell_scope.several_files_per_seq: no seq has more than one file", not several, "none", str(several), severity="warn")
        # converter check 1: table values equal the file summaries (row alignment after pass 2)
        worst_q, worst_v = 0.0, 0.0
        for seq, g in table.groupby("seq"):
            c = cells[seq]["cycles"].set_index("cycle_index")
            q = c.loc[g["cycle_number"], "capacity_cycler_Ah"].to_numpy()
            v = (c.loc[g["cycle_number"], "discharge_energy_Wh"] / c.loc[g["cycle_number"], "capacity_cycler_Ah"]).to_numpy()
            worst_q = max(worst_q, float(np.max(np.abs(q - g["capacity_cycler_Ah"].to_numpy()))))
            worst_v = max(worst_v, float(np.max(np.abs(v / g["mean_discharge_voltage_V"].to_numpy() - 1))))
        ct.require("converter: capacity in the cycle table equals summary.discharge_capacity", worst_q == 0.0, "identical", f"{worst_q:.2e}")
        ct.require("converter: mean discharge voltage equals summary discharge_energy / discharge_capacity", worst_v <= 1e-12, "<= 1e-12 relative", f"{worst_v:.2e}")
        # converter check 2: charge-time validation (per file) and its stop rule
        val = {s: recs[s]["validation"] for s in cells}
        evaluable = [s for s, v in val.items() if v.get("evaluable") and built["cells"][s].get("scope_i_ii")]
        failing = [s for s in evaluable if not val[s]["passes"]]
        share_fail = len(failing) / len(evaluable) if evaluable else 0.0
        ct.require("charge-time validation: failing evaluable files <= 10 % (channels.charge_time.failure; stop above)", share_fail <= 0.10,
                   "<= 10 %", f"{len(failing)} of {len(evaluable)} evaluable ({share_fail:.1%}); not evaluable {len(cells) - len(evaluable)}")
        o_med = [val[s]["o_median_min"] for s in evaluable]
        # converter check 3: index structure
        overlap = [s for s in cells if set(cells[s]["cycles"]["cycle_index"]) & set(cells[s]["diagnostics"]["cycle_index"])]
        nonmono = [s for s in cells if not cells[s]["cycles"]["cycle_index"].is_monotonic_increasing]
        contiguous = sum(bool(val[s].get("contiguous_from_0")) for s in cells)
        ct.require("index: summary and diagnostic_summary cycle_index sets are disjoint", not overlap, "disjoint", str(overlap))
        ct.require("index: summary cycle_index strictly increasing", not nonmono, "all", str(nonmono))
        ct.require("index: cycle_index contiguous from 0 over summary + diagnostic_summary (reported)", True, "reported", f"{contiguous} of {len(cells)}", severity="warn")
        # converter check 4: diagnostics
        diag_rows = []
        for s in cells:
            d = cells[s]["diagnostics"]
            exp = expected_layout(int(max(cells[s]["cycles"]["cycle_index"].max(), d["cycle_index"].max() if len(d) else 0)))
            for k in ("hppc", "rpt_0.05C", "rpt_0.2C"):
                got = sorted(d.loc[d["cycle_type"] == k, "cycle_index"].astype(int))
                diag_rows.append({"seq": s, "type": k, "n": len(got), "matches_expected_layout": got == exp[k][:len(got)] and len(got) >= len(exp[k]) - 1,
                                  "median_discharge_current_A": float(np.nanmedian(d.loc[d["cycle_type"] == k, "median_abs_discharge_current_A"])) if len(got) else np.nan})
            other = sorted(set(d["cycle_type"]) - {"hppc", "rpt_0.05C", "rpt_0.2C"})
            if other:
                diag_rows.append({"seq": s, "type": "other:" + ",".join(map(str, other)), "n": int(d["cycle_type"].isin(other).sum())})
        dg = pd.DataFrame(diag_rows)
        save_table(dg, out / "tables" / "diagnostics_layout")
        i005 = dg.loc[dg["type"] == "rpt_0.05C", "median_discharge_current_A"]
        i02 = dg.loc[dg["type"] == "rpt_0.2C", "median_discharge_current_A"]
        ct.require("diagnostics: rpt_0.05C discharge current about 0.012 A (C/20)", bool(np.all(np.abs(i005 / 0.012 - 1) < 0.10)), "within 10 %",
                   f"median {np.nanmedian(i005):.4f} A, range [{np.nanmin(i005):.4f}, {np.nanmax(i005):.4f}]", severity="warn")
        ct.require("diagnostics: rpt_0.2C discharge current about 0.048 A (C/5)", bool(np.all(np.abs(i02 / 0.048 - 1) < 0.10)), "within 10 %",
                   f"median {np.nanmedian(i02):.4f} A, range [{np.nanmin(i02):.4f}, {np.nanmax(i02):.4f}]", severity="warn")
        ct.require("diagnostics: per-cell layout matches HPPC 0, 8, 24, 127+103k / RPT 1, 25, 128+103k / 2, 26, 129+103k (reported)", True, "reported",
                   f"{int(dg.loc[dg['type'].isin(['hppc', 'rpt_0.05C', 'rpt_0.2C']), 'matches_expected_layout'].sum())} of {int(dg['type'].isin(['hppc', 'rpt_0.05C', 'rpt_0.2C']).sum())} (cell, type) pairs", severity="warn")
        # labelled diagnostic cycles with an aging discharge current (positions.diagnostic_cycles)
        lab_aging = {s: int((np.abs(cells[s]["diagnostics"]["median_abs_discharge_current_A"] / built["modal"]["I_dis"] - 1) <= 0.10).sum()) for s in cells}
        # converter check 5: protocol tuple, modal, second protocol, E2 on the files
        m = built["modal"]
        ct.require("aging protocol: modal tuple within tolerance of the documented one (E2 on the files)", all(built["e2_files"]["modal_within_documented"].values()),
                   "0.24 A / 0.18 A / 4.4 V / 3.0 V", f"I_chg {m['I_chg']} I_dis {m['I_dis']} V_cv {m['V_cv']} V_end {m['V_end']}")
        ct.require("aging protocol: incomplete cycles <= 5 % of regular cycles, pooled (E2 on the files)", built["e2_files"]["incomplete_share_pooled"] <= 0.05,
                   "<= 5 %", f"{built['e2_files']['incomplete_share_pooled']:.2%}")
        ct.require("aging protocol: no second aging protocol (two or more agreeing out-of-tolerance sources)", not built["second_protocol"]["present"], "none",
                   f"sources {len(built['second_protocol']['sources'])}, agreeing pairs {built['second_protocol']['agreeing_pairs']}")
        # converter check 6/7: inventory and BEEP markers
        sp_vals = pd.DataFrame([{**{k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in recs[s]["record"]["structuring_parameters"].items()}, "seq": s} for s in cells])
        sp_summary = {c: sp_vals[c].value_counts(dropna=False).to_dict() for c in sp_vals.columns if c != "seq"}
        writers = pd.DataFrame([{**recs[s]["record"]["writer"], "raw_data": recs[s]["record"]["raw_data_nonempty"]} for s in cells])
        protocols = pd.Series([recs[s]["record"]["protocol"] for s in cells]).value_counts().to_dict()
        ct.require("structuring_parameters: nominal_capacity 0.24 in every file (reported otherwise)", set(sp_vals["nominal_capacity"]) == {0.24}, "0.24",
                   str(sp_summary.get("nominal_capacity")), severity="warn")
        ct.require("source: raw_data absent or empty in every documented file, so cycles_interpolated is the profile-wide source (channels.charge_time.source)", True,
                   "reported", f"files with raw_data: {int(writers['raw_data'].sum())}", severity="warn")
        # counts (cell_scope.counts_reported)
        crec = built["cells"]
        excl = pd.Series([r.get("excluded") for r in crec.values() if r.get("excluded")]).value_counts().to_dict()
        in_scope = sorted(s for s, r in crec.items() if r.get("excluded") is None)
        counts = {"aging_files_current": len(files), "parsed": len(cells), "with_sheet_row": int(sum(r["in_sheet"] for r in crec.values())),
                  "in_scope": len(in_scope), "excluded_by_reason": excl, "undocumented_files_current": undocumented,
                  "undocumented_files_original_not_used": ["Nova_Regular_Ref_100.091.json.gz", "Nova_Regular_Ref_101.092.json.gz", "Nova_Regular_Ref_102.093.json.gz"],
                  "reference_counts": {"designed": 186, "sheet_rows_incl_baseline": 183, "design_rows": 180, "rhyu_used": 178},
                  "sheet_rows_without_file": sorted(set(mapping["seq"]) - set(by_seq.index)),
                  "positions": int(len(table)), "cycles_per_cell": table.groupby("cell_id").size().describe().round(1).to_dict(),
                  "missing_fields": {s: [k for k, v in recs[s]["record"]["rows"].items() if v is None and k != "raw_data"] for s in cells
                                     if any(v is None for k, v in recs[s]["record"]["rows"].items() if k != "raw_data")}}
        sums = {}
        for s in in_scope:
            for k, v in crec[s]["counts"].items():
                if isinstance(v, dict):
                    for kk, vv in v.items():
                        sums[f"{k}.{kk}"] = sums.get(f"{k}.{kk}", 0) + vv
                else:
                    sums[k] = sums.get(k, 0) + v
        counts["predicates_masks_events_total"] = sums
        counts["labelled_diagnostic_aging_current"] = {s: v for s, v in lab_aging.items() if v}
        prot_check = mapping.groupby("triplet")["protocol_id"].nunique()
        ct.require("formation mapping: protocol_id equals the authors' consecutive-triplet grouping (reported)", bool((prot_check <= 1).all()), "one protocol per triplet",
                   f"{int((prot_check > 1).sum())} mixed triplets; {mapping['protocol_id'].nunique()} protocol groups incl. baseline", severity="warn")
        summary = {"counts": counts, "d33_r4_literal_estimator": literal, "modal_tuple": m, "v_end_ref": built["v_end_ref"], "documented": built["documented"], "e2_files": built["e2_files"],
                   "second_protocol": built["second_protocol"], "charge_time_validation": {"evaluable": len(evaluable), "failing": failing,
                   "o_median_min_across_files": {"median": float(np.median(o_med)) if o_med else None, "min": float(np.min(o_med)) if o_med else None,
                                                 "max": float(np.max(o_med)) if o_med else None},
                   "o_iqr_max_min": float(max(val[s]["o_iqr_min"] for s in evaluable)) if evaluable else None,
                   "finiteness_agreement_min": float(min(val[s]["finiteness_agreement_share"] for s in evaluable)) if evaluable else None},
                   "structuring_parameters": sp_summary, "writer_markers": {" | ".join(f"{c}={v}" for c, v in zip(writers.columns, k)): int(n) for k, n in writers.astype(str).value_counts().items()} if len(writers) else {},
                   "maccor_protocol_names": protocols,
                   "formation_mapping": {"protocol_groups": int(mapping["protocol_id"].nunique()), "in_scope_per_protocol": table.drop_duplicates("seq").groupby("protocol_id").size().describe().round(2).to_dict(),
                                         "tagged_cells_in_scope": {int(s): t for s, t in zip(mapping["seq"], mapping["tags"]) if t and s in in_scope}},
                   "channels_availability_preview": {"temperature_nonnull_share": float(table["temperature_mean_C"].notna().mean()),
                                                     "ir_nonzero_share": float(table["internal_resistance_ohm"].notna().mean())},
                   "cross_check_mdv_samples_minus_summary_V": {"median_abs": float(np.nanmedian(np.abs(table["V_cw_samples"] - table["mean_discharge_voltage_V"]))),
                                                               "p95_abs": float(np.nanpercentile(np.abs(table["V_cw_samples"] - table["mean_discharge_voltage_V"]), 95))}}
        cell_rows = pd.DataFrame([{k: v for k, v in r.items() if k != "counts"} | {f"n_{k}": (v if not isinstance(v, dict) else json.dumps(v))
                                  for k, v in r.get("counts", {}).items()} for r in crec.values()]).sort_values("seq")
        cell_rows = cell_rows.merge(mapping[["seq", "protocol_id", "batch", "tags"]], on="seq", how="left")
        cell_rows["charge_time_validation"] = cell_rows["seq"].map(lambda s: json.dumps(val.get(s, {})))
        save_table(cell_rows, out / "tables" / "cells")
        write_json(summary, out / "tables" / "ingest_summary.json")
        # figures
        import matplotlib.pyplot as plt
        from degradx.viz.style import apply as style
        style()
        fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
        for s, g in table.groupby("seq"):
            ax[0].plot(g["position"], g["capacity_cycler_Ah"], lw=0.4, alpha=0.5)
            ax[1].plot(g["position"], g["charge_time_min"], lw=0.4, alpha=0.5)
            ax[2].plot(g["position"], g["mean_discharge_voltage_V"], lw=0.4, alpha=0.5)
        ax[0].axhline(0.8 * T.Q_NOM, color="k", ls="--", lw=0.8)
        for a, t in zip(ax, ["capacity (Ah), 3C/4", "charge time (min), masked after interruptions", "mean discharge voltage (V)"]):
            a.set_title(t, fontsize=9)
            a.set_xlabel("position (aging cycle)")
        save_figure(fig, out / "figures" / "tri_formation_channels")
        code = ct.finalize(out)
        (out / "logs" / "checks.md").write_text(ct.markdown() + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
