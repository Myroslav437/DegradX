#!/usr/bin/env python
"""V10 (brief "DegradX v2") — results export, paper tables and figures for the v2 scope, from v2 stage artifacts only.

Built on the S9 machinery (helpers imported from ``scripts/s9_write_paper.py``): one JSON per table under ``results/v2``
with the source artifact of every value, LaTeX table bodies and notes under ``paper/tables/`` (\\input by paper.tex; the
v1 bodies remain at tag v1-results), figures under ``paper/img/``, and the provenance list ``results/v2/provenance.json``
from which the v2 section of ``docs/RESULTS_PROVENANCE.md`` is written. Cells without a measurement are void with the
reason in a table note. Profiles: those whose stage artifacts exist (MATR, HUST; ISU-ILCC only if run past V4).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

from degradx import ARTIFACTS_DIR, ARTIFACTS_V2, REPO_ROOT, RESULTS_V2
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.io import write_json

_spec = importlib.util.spec_from_file_location("s9", str(REPO_ROOT / "scripts" / "s9_write_paper.py"))
S9 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S9)
f3, Notes, commit_of = S9.f3, S9.Notes, S9.commit_of
PAPER = REPO_ROOT / "paper"
TABLES = PAPER / "tables"
NAME = {"MATR": "MATR", "HUST": "HUST", "ISU_ILCC": "ISU-ILCC"}
PROV: list[dict] = []
SEEDS_GEN = "generation 0,1,2; model_init 0-4; evaluation 20260915"


def prov(cell: str, source: Path, key: str, script: str, seeds: str):
    PROV.append({"cell": cell, "artifact": str(Path(source).relative_to(REPO_ROOT)), "key": key, "script": script, "seeds": seeds,
                 "artifact_commit": commit_of(source)})


def profiles_with(path_fn) -> list[str]:
    return [ds for ds in ("MATR", "HUST", "ISU_ILCC") if path_fn(ds).exists() or False]


def ci(x, digits=2):
    if x is None or x.get("mean", x.get("ratio")) is None:
        return "--"
    m = x.get("mean", x.get("ratio"))
    if x.get("ci_low") is None:
        return f3(m, digits)
    return f"{f3(m, digits)} [{f3(x['ci_low'], digits)}, {f3(x['ci_high'], digits)}]"


# ---------------------------------------------------------------------------------------------------------------- Table 1
def table_fidelity():
    src = ARTIFACTS_V2 / "v5_fidelity" / "tables" / "fidelity.json"
    R = json.loads(src.read_text())
    notes, rows, res = Notes(), [], {}
    for ds in [d for d in ("MATR", "HUST", "ISU_ILCC") if d in R]:
        r = R[ds]
        u, t, v = r["units"], r["tstr"], r["void"]
        disc = [s["discriminative_error"] for s in r["per_generation_seed"]]
        cov = [s["cov_relative_frobenius"] for s in r["per_generation_seed"]]
        base = r["baseline_measured_fitting_vs_held_out"]
        bi = base["cov_relative_frobenius_interval"]
        off = r.get("x3_off_seed0") or {}
        v1 = r.get("v1_vs_v2", {})
        c_disc = notes.void(f"{v['discriminative_error']} (D02b)") if v["discriminative_error"] else f"{f3(min(disc), 2)}--{f3(max(disc), 2)}"
        c_cov = (notes.void(f"{v['covariance_agreement']} (D02b)") if v["covariance_agreement"]
                 else f"{f3(np.mean(cov), 2)} ({f3(base['cov_relative_frobenius'], 2)}; {f3(bi['ci_low'], 2)}--{f3(bi['ci_high'], 2)})")
        c_off = f"{f3(off.get('discriminative_error'), 2)} / {f3(off.get('cov_relative_frobenius'), 2)}" if off else "--"
        c_tstr = (notes.void(f"held-out units reaching EOL: {t['held_out_units']} $<$ 20 (D02b)") if t["void"] else f"{f3(t['ratio'], 2)} [{f3(t['ci_low'], 2)}, {f3(t['ci_high'], 2)}]")
        c_v1 = f"{f3(v1['tstr_ratio']['v1'][0], 2)}" if v1 else "--"
        rows.append(f"    {NAME[ds]} & {u['measured_held_out']} / {u['generated_per_seed']} & {c_disc} & {c_cov} & {c_off} & {c_tstr} & {c_v1} \\\\")
        res[ds] = {"units": u, "discriminative_error_per_generation_seed": disc, "covariance_rel_frobenius_mean": float(np.mean(cov)),
                   "covariance_baseline": base["cov_relative_frobenius"], "covariance_baseline_interval": [bi["ci_low"], bi["ci_high"]],
                   "x3_off_seed0": {"discriminative_error": off.get("discriminative_error"), "cov_relative_frobenius": off.get("cov_relative_frobenius")},
                   "transfer_ratio": t["ratio"], "transfer_ci": [t["ci_low"], t["ci_high"]], "readings": r.get("readings"), "v1_vs_v2": v1, "void": {**v, "transfer_ratio": t["void"]}}
        for col in ("discriminative_error", "covariance_agreement", "x3_off", "transfer_ratio", "v1_transfer_ratio"):
            prov(f"Table 1 / {NAME[ds]} / {col}", src, ds, "scripts/v2/v5_fidelity.py", SEEDS_GEN)
    res["readings_cross_profile"] = R.get("readings_cross_profile")
    (TABLES / "table_fidelity.tex").write_text("\n".join(rows) + "\n")
    (TABLES / "table_fidelity_notes.tex").write_text("\\def\\TabFidelityNotes{" + notes.text() + "}\n")
    write_json(res, RESULTS_V2 / "table1_fidelity.json")
    return res


# ---------------------------------------------------------------------------------------------------------------- Table 2
def table_properties():
    notes = Notes()
    data = {}
    for ds in ("MATR", "HUST", "ISU_ILCC"):
        src = ARTIFACTS_V2 / "v5_fidelity" / "tables" / f"properties_{ds}.json"
        if src.exists():
            data[ds] = (src, json.loads(src.read_text()))

    def med(v, scale=1.0, d=3):
        return f3(v["median"] * scale, d) if isinstance(v, dict) and v.get("median") is not None else "--"

    def num(v, scale=1.0, d=3):
        return f3(v * scale, d) if isinstance(v, (int, float)) and v is not None and np.isfinite(v) else "--"

    def row_of(ds, prefix):
        src, rows = data[ds]
        return src, next((r for r in rows if r["property"].startswith(prefix)), None)

    specs = [
        ("Fit error of the profile's family", "trajectory family", lambda v: (f3(float(v.split(";")[1]), 4) if isinstance(v, str) else "--")),
        ("Drift rate [mAh/100 cyc.]", "drift rate", lambda v: med(v)),
        ("Transition position [$\\times T$]", "transition position", lambda v: med(v)),
        ("Unit length $T$ [cycles]", "unit length", lambda v: med(v, d=0)),
        ("Early-life reference $q_1$, IQR [mAh]", "early-life reference", lambda v: f3(v["iqr"] * 1000, 2) if isinstance(v, dict) and v else "--"),
        ("Noise variance, capacity [mAh$^2$]", "noise variance, capacity", lambda v: num(v, 1e6)),
        ("Noise variance, charge time [min$^2$]", "noise variance, charge_time", lambda v: num(v)),
        ("Noise autocorrelation, charge time", "noise lag-1 autocorrelation, charge_time", lambda v: num(v, d=2)),
        ("Offset IQR, charge time [min]", "per-unit offset IQR, charge_time", lambda v: num(v, d=2)),
        ("Offset IQR, mean discharge V [mV]", "per-unit offset IQR, mean_discharge_voltage", lambda v: num(v, 1000, 1)),
        ("Residual correlation, rel. Frob. to fitting split", "within-unit residual correlation", lambda v: f3(v["relative_frobenius"], 2) if isinstance(v, dict) and "relative_frobenius" in v else "--"),
    ]
    sides = ("fitting", "held_out", "generated")
    lines, res = [], {}
    for label, prefix, fmt in specs:
        cells = []
        for ds in data:
            src, row = row_of(ds, prefix)
            for side in sides:
                if row is None:
                    cells.append("--")
                    continue
                if side == "held_out" and row.get("void_held_out"):
                    cells.append(notes.void(row["void_held_out"].replace("<", "$<$")))
                    continue
                cells.append(fmt(row.get(side)))
            prov(f"Table 2 / {NAME[ds]} / {label}", src, prefix, "scripts/v2/v5_fidelity.py", "generation 0; evaluation 20260915")
        lines.append(f"    {label} & " + " & ".join(cells) + " \\\\")
        res[label] = cells
    (TABLES / "table_properties.tex").write_text("\n".join(lines) + "\n")
    (TABLES / "table_properties_notes.tex").write_text("\\def\\TabPropertiesNotes{" + notes.text() + "}\n")
    write_json({"profiles": list(data), "columns": list(sides), "rows": res}, RESULTS_V2 / "table2_properties.json")
    return res


# ---------------------------------------------------------------------------------------------------------------- Table 3
def table_usability(kind="recency"):
    notes = Notes()
    data = {}
    for ds in ("MATR", "HUST", "ISU_ILCC"):
        src = ARTIFACTS_V2 / "v6_usability" / "tables" / f"usability_{ds}.json"
        if src.exists():
            data[ds] = (src, json.loads(src.read_text())[ds][kind])
    no_pat = notes.void("no inserted patterns in the profile (D05)") if data else ""
    seeds = "generation 0; model_init 0-4 (A, B); evaluation 20260915"
    rows = []

    def add(label, fn, key):
        cells = []
        for ds, (src, r) in data.items():
            cells.append(fn(r))
            prov(f"Table 3 / {NAME[ds]} / {label}", src, f"{ds}.{kind}.{key}", "scripts/v2/v6_usability.py", seeds)
        rows.append(f"    {label} & " + " & ".join(cells) + " \\\\")

    add("Accuracy, NRMSE of the primary model (members passing)", lambda r: f"{f3(r['primary_nrmse'], 3)} ({r['gate_pass_members']}/10)", "primary_nrmse")
    add("Offset term, share of Var$(y)$", lambda r: f3(r.get("offset_term", {}).get("share_of_var_y"), 3), "offset_term")
    add("Spearman correlation of $y$ with RUL", lambda r: f3(r["spearman_y_rul"], 2), "spearman_y_rul")
    for c, lab in (("capacity", "capacity"), ("charge_time", "charge time"), ("mean_discharge_voltage", "mean discharge V")):
        add(f"Permutation importance, {lab}", lambda r, c=c: f3(r["permutation_importance"][c]["nmse_increase"], 3), f"permutation_importance.{c}")
    for c, lab in (("capacity", "capacity"), ("charge_time", "charge time"), ("mean_discharge_voltage", "mean discharge V")):
        add(f"Channel use (conditional importance), {lab}", lambda r, c=c: ci(r["channel_usage"]["A0"][c] | {"mean": r["channel_usage"]["A0"][c]["nmse_increase"]}, 3), f"channel_usage.A0.{c}")
    add("Members using every weighted channel", lambda r: f"{r['channel_usage_gate']['members_using_all']}/10", "channel_usage_gate")
    add("Leakage, null channels (upper bound, flat / permuted)", lambda r: f"{f3(r['permutation_importance']['null_flat']['ci_high'], 4)} / {f3(r['permutation_importance']['null_permuted']['ci_high'], 4)}", "permutation_importance.null_*")
    add("Redundant channels: $R^2$, conditional importance",
        lambda r: "; ".join(f"{c.replace('internal_resistance', 'IR').replace('temperature_mean', 'temp.')} {f3(v['predictability_r2'], 2)}, {f3(v['conditional_importance']['nmse_increase'], 4)}"
                            for c, v in r["redundant_channels"].items()) or "none", "redundant_channels")
    add("Pattern term: variance ratio, ablation", lambda r: no_pat, "term_ablation")
    (TABLES / "table_usability.tex").write_text("\n".join(rows) + "\n")
    (TABLES / "table_usability_notes.tex").write_text("\\def\\TabUsabilityNotes{" + notes.text() + "}\n")
    write_json({"weighting": kind, "values": {ds: r for ds, (src, r) in data.items()}}, RESULTS_V2 / "table3_usability.json")


# ---------------------------------------------------------------------------------------------------------------- Table 4
OPS = [("added_noise", "Added noise"), ("shift_to_start", "Mass to start"), ("shift_to_end", "Mass to end"), ("smoothing", "Smoothing"), ("permuted_fraction", "Permuted fraction")]
SCORES = [("rank", "rank"), ("allocation", "alloc."), ("temporal", "temporal")]


def table_scores(kind="recency"):
    src = ARTIFACTS_V2 / "v7_scores" / "tables" / "degradation.json"
    R = json.loads(src.read_text())
    profs = [d for d in ("MATR", "HUST", "ISU_ILCC") if d in R]
    rows = []
    for op, lab in OPS:
        cells = []
        for ds in profs:
            s = R[ds][kind]["operators"][op]
            for k, _ in SCORES:
                m = s[k]["registers"]["registering_magnitude"]
                cells.append(f"{m}" if m is not None else "--")
        rows.append(f"    {lab} & " + " & ".join(cells) + " \\\\")
        prov(f"Table 4 / {lab}", src, f"{{{','.join(profs)}}}.{kind}.operators.{op}.<score>.registers", "scripts/v2/v7_scores.py", "generation 0; evaluation 20260915")
    (TABLES / "table_resolution.tex").write_text("\n".join(rows) + "\n")
    write_json({"weighting": kind, "profiles": profs, "values": {ds: R[ds] for ds in profs}}, RESULTS_V2 / "table4_scores.json")


# ---------------------------------------------------------------------------------------------------------------- Table 5
def table_isolation():
    """X1 (D26): TSTR ratios by input set on the v1 profiles (V1) and the v2 profiles (V5)."""
    src1 = ARTIFACTS_V2 / "v1_tstr_isolation" / "tables" / "tstr_isolation.json"
    src5 = ARTIFACTS_V2 / "v5_fidelity" / "tables" / "fidelity.json"
    R1 = json.loads(src1.read_text())
    R5 = json.loads(src5.read_text()) if src5.exists() else {}
    sets = [("full", "All channels"), ("capacity_only", "Capacity only"), ("capacity_relative", "Capacity / $q_1$"), ("capacity_state", "Two-point state"),
            ("full_centred", "All, offsets removed")]
    rows = []
    for key, lab in sets:
        cells = []
        for ds in ("MATR", "HUST"):
            x1 = R1[ds]["input_sets"].get(key)
            cells.append(ci(x1) if x1 else "--")
        for ds in ("MATR", "HUST"):
            x5 = R5.get(ds, {}).get("tstr_input_sets", {}).get(key)
            cells.append(ci(x5) if x5 else "--")
        rows.append(f"    {lab} & " + " & ".join(cells) + " \\\\")
    rows.append("    \\midrule")
    for name, lab in (("per_cell_structure", "$\\Delta\\log$: all vs capacity only"), ("offsets_specifically", "$\\Delta\\log$: all vs offsets removed"),
                      ("initial_capacity_spread", "$\\Delta\\log$: capacity vs capacity / $q_1$")):
        cells = []
        for ds in ("MATR", "HUST"):
            t = R1[ds]["tests"][name]
            cells.append(f"{f3(t['log_ratio_difference'], 2)} [{f3(t['ci_low'], 2)}, {f3(t['ci_high'], 2)}]")
        for ds in ("MATR", "HUST"):
            t = R5.get(ds, {}).get("x1_on_v2", {}).get("tests", {}).get(name)
            cells.append(f"{f3(t['log_ratio_difference'], 2)} [{f3(t['ci_low'], 2)}, {f3(t['ci_high'], 2)}]" if t else "--")
        rows.append(f"    {lab} & " + " & ".join(cells) + " \\\\")
    prov("Table 5 / v1 profiles", src1, "{MATR,HUST}.input_sets, tests", "scripts/v2/v1_tstr_isolation.py", SEEDS_GEN)
    prov("Table 5 / v2 profiles", src5, "{MATR,HUST}.tstr_input_sets, x1_on_v2.tests", "scripts/v2/v5_fidelity.py", SEEDS_GEN)
    (TABLES / "table_isolation.tex").write_text("\n".join(rows) + "\n")
    write_json({"v1_profiles": {ds: {"input_sets": {k: {kk: vv for kk, vv in v.items() if kk != "runs"} for k, v in R1[ds]["input_sets"].items()},
                                     "tests": R1[ds]["tests"], "readings": R1[ds]["readings"]} for ds in R1},
                "v2_profiles": {ds: {"input_sets": {k: {kk: vv for kk, vv in v.items() if kk != "runs"} for k, v in R5[ds].get("tstr_input_sets", {}).items()},
                                     "x1_on_v2": R5[ds].get("x1_on_v2")} for ds in R5 if isinstance(R5[ds], dict) and "tstr" in R5[ds]}},
               RESULTS_V2 / "table5_tstr_isolation.json")


# ---------------------------------------------------------------------------------------------------------------- Table 6
METHODS = [("integrated_gradients", "IG"), ("feature_occlusion", "Feature occlusion"), ("timeshap", "TimeSHAP")]


def table_reference(kind="recency"):
    notes = Notes()
    src = ARTIFACTS_V2 / "v8_reference_methods" / "tables" / "reference_values.json"
    R = json.loads(src.read_text())
    seeds = "generation 0; model_init 0 (A), ensemble A/B 0-4; attribution_sampling 0,1,2 (TimeSHAP), 0 (floor); evaluation 20260915"
    rows = []
    for di, ds in enumerate([d for d in ("MATR", "HUST", "ISU_ILCC") if d in R]):
        r = R[ds]["weightings"][kind]
        sc = r["scores"]
        cvoid = r.get("channel_usage_void")
        if di:
            rows.append("    \\midrule")
        rows.append(f"    \\multicolumn{{9}}{{l}}{{\\textit{{{NAME[ds]}}} ({R[ds]['windows']} windows from {R[ds]['units']} test units; every method on every window)}} \\\\")
        for key, label in METHODS:
            t, f = sc[f"trained/{key}"], sc[f"reference/{key}"]

            def tr(k, d=3):
                if cvoid and k in ("allocation", "zero_mass"):
                    return notes.void(cvoid)
                return ci(t[k], d)
            rows.append(f"    {label} & {tr('rank')} & {ci(f['rank'], 3)} & {tr('allocation')} & {ci(f['allocation'], 3)} & {tr('temporal', 2)} & {ci(f['temporal'], 2)} & {tr('zero_mass')} & {f3(f['zero_mass']['mean'])} \\\\")
            prov(f"Table 6 / {NAME[ds]} / {label}", src, f"{ds}.weightings.{kind}.scores.{{trained,reference}}/{key}", "scripts/v2/v8_reference_methods.py", seeds)
        ex = sc["reference_exact"]
        rows.append(f"    Exact attribution $w(x - x^{{0}})$ & -- & {ci(ex['rank'], 3)} & -- & {ci(ex['allocation'], 3)} & -- & {ci(ex['temporal'], 2)} & -- & {f3(ex['zero_mass']['mean'])} \\\\")
        fl = r["identifiability_floor"]
        for key, label in METHODS:
            if key not in fl:
                continue
            q = fl[key]
            rows.append(f"    Ensemble range, {label} & {f3(q['rank_min'])}--{f3(q['rank_max'])} & -- & {f3(q['allocation_min'])}--{f3(q['allocation_max'])} & -- & {f3(q['temporal_min'], 2)}--{f3(q['temporal_max'], 2)} & -- & -- & -- \\\\")
        prov(f"Table 6 / {NAME[ds]} / ensemble range", src, f"{ds}.weightings.{kind}.identifiability_floor", "scripts/v2/v8_reference_methods.py", seeds)
        if "secondary_average_event" in r:
            s2 = r["secondary_average_event"]["scores"]
            rows.append(f"    TimeSHAP, average-event background & {ci(s2['rank'], 3)} & -- & {ci(s2['allocation'], 3)} & -- & {ci(s2['temporal'], 2)} & -- & {f3(s2['zero_mass']['mean'])} & -- \\\\")
            prov(f"Table 6 / {NAME[ds]} / TimeSHAP average event", src, f"{ds}.weightings.{kind}.secondary_average_event", "scripts/v2/v8_reference_methods.py", seeds)
    (TABLES / "table_reference.tex").write_text("\n".join(rows) + "\n")
    (TABLES / "table_reference_notes.tex").write_text("\\def\\TabReferenceNotes{" + notes.text() + "}\n")
    write_json({"weighting_in_table": kind, "values": R}, RESULTS_V2 / "table6_reference_values.json")


def write_provenance_md(entries):
    """v2 rows on top; the v1 rows (from the v1 file, or from the v1 section of an earlier v2 file) kept below."""
    path = REPO_ROOT / "docs" / "RESULTS_PROVENANCE.md"
    old = path.read_text().splitlines()
    if any(l.startswith("## v1") for l in old):
        i = next(k for k, l in enumerate(old) if l.startswith("## v1"))
        v1_rows = [l for l in old[i:] if l.startswith("| ") and not l.startswith("| table") and not l.startswith("|---")]
    else:
        v1_rows = [l for l in old if l.startswith("| ") and not l.startswith("| table") and not l.startswith("|---")]
    head = "| table / figure cell | artifact | key | script | seeds | artifact commit |"
    lines = ["# Results provenance", "",
             "Every table cell and figure in Section 4 of `paper/paper.tex` and the artifact that produced it. The artifact commit is the",
             "last commit touching the artifact file. Seeds: generation / model_init / attribution_sampling / evaluation streams",
             "(`degradx.utils.seeding.derive_seed` under base seed 20260915). Configs: `configs/declarations.yaml` (r3 with its dated",
             "supersession log).", "",
             "## v2 (current paper; generated by `scripts/v2/v10_write_paper.py` from `results/v2/provenance.json`)", "", head, "|---|---|---|---|---|---|"]
    for e in sorted(entries, key=lambda x: x["cell"]):
        lines.append(f"| {e['cell']} | `{e['artifact']}` | {e['key']} | `{e['script']}` | {e['seeds']} | `{e['artifact_commit'][:10]}` |")
    lines += ["", "## v1 (tag `v1-results`, generated by `scripts/s9_write_paper.py`; v1 numbers the paper cites, e.g. in the v1-versus-v2 comparisons)", "",
              head, "|---|---|---|---|---|---|"] + v1_rows
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    p = stage_parser(__doc__, "v2/v10_write_paper")
    p.add_argument("--tables", nargs="*", default=["fidelity", "properties", "usability", "scores", "isolation", "reference"])
    p.add_argument("--tables-dir", default=None, help="write LaTeX bodies here instead of paper/tables (testing)")
    p.add_argument("--no-provenance", action="store_true")
    args = p.parse_args()
    global TABLES
    if args.tables_dir:
        TABLES = Path(args.tables_dir)
        TABLES.mkdir(parents=True, exist_ok=True)
    StageContext.from_args(args)
    RESULTS_V2.mkdir(parents=True, exist_ok=True)
    fns = {"fidelity": table_fidelity, "properties": table_properties, "usability": table_usability, "scores": table_scores, "isolation": table_isolation,
           "reference": table_reference}
    for t in args.tables:
        fns[t]()
        print(f"[v10] {t} done", flush=True)
    if args.no_provenance:
        return 0
    old = json.loads((RESULTS_V2 / "provenance.json").read_text()) if (RESULTS_V2 / "provenance.json").exists() else []
    keep = [x for x in old if not any(x["cell"].split(" / ")[0] == y["cell"].split(" / ")[0] for y in PROV)]
    allp = keep + PROV
    write_json(allp, RESULTS_V2 / "provenance.json")
    write_provenance_md(allp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
