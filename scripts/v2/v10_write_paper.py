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
    rd_src = ARTIFACTS_V2 / "v5_fidelity" / "tables" / "discriminator_readability.json"
    RD = json.loads(rd_src.read_text()) if rd_src.exists() else {}
    notes, rows, res = Notes(), [], {}
    for ds in [d for d in ("MATR", "HUST", "ISU_ILCC") if d in R]:
        r = R[ds]
        u, t, v = r["units"], r["tstr"], r["void"]
        disc = [s["discriminative_error"] for s in r["per_generation_seed"]]
        rd = RD.get(ds)
        if rd and not rd["readable"] and not v["discriminative_error"]:  # D02b readability (DEVIATIONS T6)
            seeds_txt = ", ".join(f"{f3(x['discriminative_error'], 2)} [{f3(x['ci_low'], 2)}, {f3(x['ci_high'], 2)}]" for x in rd["per_generation_seed"])
            v = {**v, "discriminative_error": f"{NAME[ds]}: 95\\% unit-bootstrap half-width above half the distance from 0.5 for "
                                              f"{sum(not x['readable'] for x in rd['per_generation_seed'])} of 3 generation seeds; values {seeds_txt}"}
        cov = [s["cov_relative_frobenius"] for s in r["per_generation_seed"]]
        base = r["baseline_measured_fitting_vs_held_out"]
        bi = base["cov_relative_frobenius_interval"]
        off = r.get("x3_off_seed0") or {}
        v1 = r.get("v1_vs_v2", {})
        c_disc = notes.void(f"{v['discriminative_error']}") if v["discriminative_error"] else f"{f3(min(disc), 2)}--{f3(max(disc), 2)}"
        if rd:
            prov(f"Table 1 / {NAME[ds]} / discriminative_error readability", rd_src, ds, "scripts/v2/v5_discriminator_readability.py", "generation 0,1,2; evaluation 20260915")
        c_cov = (notes.void(f"{v['covariance_agreement']}") if v["covariance_agreement"]
                 else f"{f3(np.mean(cov), 2)} ({f3(base['cov_relative_frobenius'], 2)}; {f3(bi['ci_low'], 2)}--{f3(bi['ci_high'], 2)})")
        c_off = f"{f3(off.get('discriminative_error'), 2)} / {f3(off.get('cov_relative_frobenius'), 2)}" if off else "--"
        c_tstr = (notes.void(f"held-out units reaching EOL: {t['held_out_units']} $<$ 20") if t["void"] else f"{f3(t['ratio'], 2)} [{f3(t['ci_low'], 2)}, {f3(t['ci_high'], 2)}]")
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
        ("Fit error of the profile's family [fraction of $q_1$]", "trajectory family", lambda v: (f3(float(v.split(";")[1]), 4) if isinstance(v, str) else "--")),
        ("Drift rate [mAh/100 cyc.]", "drift rate", lambda v: med(v)),
        ("Transition position [$\\times T$]", "transition position", lambda v: med(v)),
        ("Unit length $T$ [cycles]", "unit length", lambda v: med(v, d=0)),
        ("Early-life reference $q_1$, IQR [mAh]", "early-life reference", lambda v: f3(v["iqr"] * 1000, 2) if isinstance(v, dict) and v else "--"),
        ("Noise variance, capacity [mAh$^2$]", "noise variance, capacity", lambda v: num(v, 1e6)),
        ("Noise variance, charge time [min$^2$]", "noise variance, charge_time", lambda v: num(v)),
        ("Noise autocorrelation, charge time", "noise lag-1 autocorrelation, charge_time", lambda v: num(v, d=2)),
        ("Offset IQR, charge time [min]", "per-unit offset IQR, charge_time", lambda v: num(v, d=2)),
        ("Offset IQR, mean discharge V [mV]", "per-unit offset IQR, mean_discharge_voltage", lambda v: num(v, 1000, 1)),
        ("Residual correlation, rel. Frob. to fitting split", "within-unit residual correlation (X3", lambda v: f3(v["relative_frobenius"], 2) if isinstance(v, dict) and "relative_frobenius" in v else "--"),
        ("\\quad capacity pairs, mean $|\\Delta r|$", "within-unit residual correlation, capacity pairs", lambda v: num(v, d=3)),
        ("\\quad other pairs, mean $|\\Delta r|$", "within-unit residual correlation, non-capacity pairs", lambda v: num(v, d=3)),
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
            prov(f"Table 2 / {NAME[ds]} / {label}", src, prefix, "scripts/v2/v5_properties.py (D30 re-run of the V5 property table)", "generation 0; evaluation 20260915")
        lines.append(f"    {label} & " + " & ".join(cells) + " \\\\")
        res[label] = cells
    (TABLES / "table_properties.tex").write_text("\n".join(lines) + "\n")
    counts = []
    for ds in data:
        _src, drift = row_of(ds, "drift rate")
        if drift:
            ns = [str(drift[sd]["n"]) for sd in sides]
            counts.append(f"{ns[0]}, {ns[1]} and {ns[2]} units in {NAME[ds]}" if not counts else f"{ns[0]}, {ns[1]} and {ns[2]} in {NAME[ds]}")
    extra = (" Generated series are read with the record-end tolerance applied to measured records, so every generated unit"
             f" enters the rows that depend on EOL; those rows rest on {' and '.join(counts)} (fitting, held-out, generated). The capacity-pair correlations carry an errors-in-variables bias of the"
             " estimator (the degradation state is read from noisy capacity), once in the fitted target and again when"
             " re-estimated on generated data.")
    (TABLES / "table_properties_notes.tex").write_text("\\def\\TabPropertiesNotes{" + (notes.text() + extra).strip() + "}\n")
    write_json({"profiles": list(data), "columns": list(sides), "rows": res}, RESULTS_V2 / "table2_properties.json")
    return res


# ---------------------------------------------------------------------------------------------------------------- Table 4 (usability)
def table_usability(kind="recency"):
    notes = Notes()
    data = {}
    for ds in ("MATR", "HUST", "ISU_ILCC"):
        src = ARTIFACTS_V2 / "v6_usability" / "tables" / f"usability_{ds}.json"
        if src.exists():
            data[ds] = (src, json.loads(src.read_text())[ds][kind])
    no_pat = notes.void("no inserted patterns in the profile") if data else ""
    seeds = "generation 0; model_init 0-4 (A, B); evaluation 20260915"
    rows = []

    def add(label, fn, key):
        cells = []
        for ds, (src, r) in data.items():
            cells.append(fn(r))
            prov(f"Table 4 / {NAME[ds]} / {label}", src, f"{ds}.{kind}.{key}", "scripts/v2/v6_usability.py", seeds)
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
    n_units = sorted({r["units"]["test"] for _src, r in data.values()})
    lead = f"{' / '.join(str(n) for n in n_units)} generated test units per profile. " if n_units else ""
    (TABLES / "table_usability_notes.tex").write_text("\\def\\TabUsabilityNotes{" + lead + notes.text() + "}\n")
    write_json({"weighting": kind, "values": {ds: r for ds, (src, r) in data.items()}}, RESULTS_V2 / "table4_usability.json")


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
        prov(f"Table 5 / {lab}", src, f"{{{','.join(profs)}}}.{kind}.operators.{op}.<score>.registers", "scripts/v2/v7_scores.py", "generation 0; evaluation 20260915")
    (TABLES / "table_resolution.tex").write_text("\n".join(rows) + "\n")
    write_json({"weighting": kind, "profiles": profs, "values": {ds: R[ds] for ds in profs}}, RESULTS_V2 / "table5_scores.json")


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
    prov("Table 3 / profiles without offsets", src1, "{MATR,HUST}.input_sets, tests", "scripts/v2/v1_tstr_isolation.py", SEEDS_GEN)
    prov("Table 3 / profiles with offsets", src5, "{MATR,HUST}.tstr_input_sets, x1_on_v2.tests", "scripts/v2/v5_fidelity.py", SEEDS_GEN)
    (TABLES / "table_isolation.tex").write_text("\n".join(rows) + "\n")
    write_json({"v1_profiles": {ds: {"input_sets": {k: {kk: vv for kk, vv in v.items() if kk != "runs"} for k, v in R1[ds]["input_sets"].items()},
                                     "tests": R1[ds]["tests"], "readings": R1[ds]["readings"]} for ds in R1},
                "v2_profiles": {ds: {"input_sets": {k: {kk: vv for kk, vv in v.items() if kk != "runs"} for k, v in R5[ds].get("tstr_input_sets", {}).items()},
                                     "x1_on_v2": R5[ds].get("x1_on_v2")} for ds in R5 if isinstance(R5[ds], dict) and "tstr" in R5[ds]}},
               RESULTS_V2 / "table3_tstr_isolation.json")


# ---------------------------------------------------------------------------------------------------------------- Table 6
METHODS = [("integrated_gradients", "IG"), ("feature_occlusion", "Occlusion"), ("timeshap", "TimeSHAP")]


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
            # reference model: unit means only (equal to the exact attribution by construction; its interval is on the exact row)
            rows.append(f"    {label} & {tr('rank')} & {f3(f['rank']['mean'])} & {tr('allocation')} & {f3(f['allocation']['mean'])} & {tr('temporal', 2)} & {f3(f['temporal']['mean'], 2)} & {tr('zero_mass')} & {f3(f['zero_mass']['mean'])} \\\\")
            prov(f"Table 6 / {NAME[ds]} / {label}", src, f"{ds}.weightings.{kind}.scores.{{trained,reference}}/{key}", "scripts/v2/v8_reference_methods.py", seeds)
        ex = sc["reference_exact"]
        stk = lambda x, d: (f"\\begin{{tabular}}[t]{{@{{}}c@{{}}}}{f3(x['mean'], d)}\\\\ {{[{f3(x['ci_low'], d)}, {f3(x['ci_high'], d)}]}}"  # noqa: E731
                            "\\end{tabular}")  # interval under the mean, top-aligned with the row
        rows.append(f"    Exact $w(x - x^{{0}})$ & -- & {stk(ex['rank'], 3)} & -- & {stk(ex['allocation'], 3)} & -- & {stk(ex['temporal'], 2)} & -- & {f3(ex['zero_mass']['mean'])} \\\\")
        fl = r["identifiability_floor"]
        for key, label in METHODS:
            if key not in fl:
                continue
            q = fl[key]
            rows.append(f"    Range, {label} & {f3(q['rank_min'])}--{f3(q['rank_max'])} & -- & {f3(q['allocation_min'])}--{f3(q['allocation_max'])} & -- & {f3(q['temporal_min'], 2)}--{f3(q['temporal_max'], 2)} & -- & -- & -- \\\\")
        prov(f"Table 6 / {NAME[ds]} / ensemble range", src, f"{ds}.weightings.{kind}.identifiability_floor", "scripts/v2/v8_reference_methods.py", seeds)
        if "secondary_average_event" in r:
            s2 = r["secondary_average_event"]["scores"]
            rows.append(f"    TimeSHAP, average event & {ci(s2['rank'], 3)} & -- & {ci(s2['allocation'], 3)} & -- & {ci(s2['temporal'], 2)} & -- & {ci(s2['zero_mass'], 3)} & -- \\\\")
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


def tex_minus():
    """Typeset negative numbers in the generated table bodies with a math minus ("-0.09" -> "$-$0.09"); ranges written
    with "--" and the void marker are left alone. Notes are not touched (they may contain math)."""
    import re

    for f in TABLES.glob("table_*.tex"):
        if f.name.endswith("_notes.tex"):
            continue
        t = f.read_text()
        f.write_text(re.sub(r"(?<![\w$\-])-(?=\d)", "$-$", t))


def main() -> int:
    p = stage_parser(__doc__, "v2/v10_write_paper")
    p.add_argument("--tables", nargs="*", default=["fidelity", "properties", "usability", "scores", "isolation", "reference", "figure_fidelity", "figure_degradation",
                                                    "figure_floor"])
    p.add_argument("--tables-dir", default=None, help="write LaTeX bodies here instead of paper/tables (testing)")
    p.add_argument("--no-provenance", action="store_true")
    args = p.parse_args()
    global TABLES, PAPER
    if args.dry_run:
        print(f"plan: v2 tables/figures {args.tables}")
        return 0
    if args.tables_dir:  # testing: tables and figures go to a scratch directory, never into paper/
        TABLES = Path(args.tables_dir)
        TABLES.mkdir(parents=True, exist_ok=True)
        PAPER = TABLES
        (PAPER / "img").mkdir(parents=True, exist_ok=True)
    StageContext.from_args(args)
    RESULTS_V2.mkdir(parents=True, exist_ok=True)
    fns = {"fidelity": table_fidelity, "properties": table_properties, "usability": table_usability, "scores": table_scores, "isolation": table_isolation,
           "reference": table_reference, "figure_fidelity": figure_fidelity, "figure_degradation": figure_degradation, "figure_floor": figure_floor}
    for t in args.tables:
        fns[t]()
        print(f"[v10] {t} done", flush=True)
    tex_minus()
    if args.no_provenance:
        return 0
    old = json.loads((RESULTS_V2 / "provenance.json").read_text()) if (RESULTS_V2 / "provenance.json").exists() else []
    keep = [x for x in old if not any(x["cell"].split(" / ")[0] == y["cell"].split(" / ")[0] for y in PROV)]
    allp = keep + PROV
    write_json(allp, RESULTS_V2 / "provenance.json")
    write_provenance_md(allp)
    return 0



# ---------------------------------------------------------------------------------------------------------------- Figures
def figure_fidelity():
    """Figure 6 (v2): measured (grey) and generated (black) capacity trajectories per v2 profile, z = 0 and z = 1 marked."""
    import pickle

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd
    from matplotlib.lines import Line2D

    import _common as C
    from degradx import DATA_V2
    from degradx.data.audit import CleaningRule, clean_capacity
    from degradx.utils.config import load_declarations
    from degradx.viz import style

    dd = load_declarations()["declared_by_design"]
    rule = CleaningRule("D12", **dd["capacity_series"]["cleaning_rule"]["params"])
    profs = [d for d in ("MATR", "HUST") if (ARTIFACTS_V2 / "v5_fidelity" / "tables" / f"properties_{d}.json").exists()]
    style.apply()
    fig, axes = plt.subplots(1, len(profs), figsize=(style.TEXTWIDTH_IN * len(profs) / 3 + 0.6, 2.0), squeeze=False)
    for ax, ds in zip(axes[0], profs):
        q_nom = C.q_nom_of(ds)
        prof = C.v2_profile(ds)
        split = C.v2_split(ds)
        df = C.load_scope(ds, dd)
        for cid in split["cell_id"]:
            d = clean_capacity(df[df["cell_id"] == cid], "capacity_cycler_Ah", rule, q_nom)
            ax.plot(d["position"], d["capacity_cycler_Ah"], color=style.MEASURED_BUNDLE, lw=style.LW_THIN, zorder=1)
        units, _ = pickle.loads((DATA_V2 / "generated" / ds / "seed0.pkl").read_bytes())
        for u in units[:25]:
            ax.plot(np.arange(1, u.T + 1), u.x[:, 0], color=style.GENERATED, lw=0.5, zorder=2)
        q1 = prof["estimated_from_data"]["E3_channel_mappings"]["capacity"]["phi0"]
        rho = prof["declared_used"]["rho"]
        ax.set_ylim(0.9 * rho * q_nom, 1.08 * q1)
        for val, lab in ((q1, r"$z=0$ (median $q_1$)"), (rho * q_nom, r"$z=1$")):
            ax.axhline(val, color=style.REFERENCE, lw=style.LW_THIN, ls="--", zorder=0)
            ax.text(1.01, val, lab, transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=6, color=style.GREY, clip_on=False)
        ax.set_title(f"{NAME[ds]} ({len(split)} measured units)", fontsize=8.5)
        ax.set_xlabel(r"position $t$ (cycle)")
        style.despine(ax)
        prov(f"Figure 6 / {NAME[ds]}", ARTIFACTS_V2 / "v3_fit_profiles" / "profiles" / f"{ds}.json", "V4 generated units seed 0 (first 25) + V3 split units",
             "scripts/v2/v4_generate_units.py; scripts/v2/v10_write_paper.py", "generation 0")
    axes[0][0].set_ylabel("capacity [Ah]")
    axes[0][0].legend(handles=[Line2D([], [], color=style.MEASURED_BUNDLE, lw=1, label="measured"), Line2D([], [], color=style.GENERATED, lw=1, label="generated")],
                      frameon=False, fontsize=6.5, loc="lower left", ncol=2, handlelength=1.5, columnspacing=1.0)
    fig.tight_layout(w_pad=2.2)
    fig.savefig(PAPER / "img" / "fig_res_fidelity.pdf")
    fig.savefig(RESULTS_V2 / "fig_res_fidelity.png", dpi=200)
    plt.close(fig)


def figure_degradation(kind="recency"):
    """Figure 7 (v2): rank agreement and the temporal profile error against each operator's magnitude (X5)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from degradx.viz import style

    src = ARTIFACTS_V2 / "v7_scores" / "tables" / "degradation.json"
    R = json.loads(src.read_text())
    profs = [d for d in ("MATR", "HUST", "ISU_ILCC") if d in R]
    style.apply()
    fig, axes = plt.subplots(2, len(OPS), figsize=(style.TEXTWIDTH_IN, 3.3), sharey="row")
    ls = {"MATR": "-", "HUST": "--", "ISU_ILCC": ":"}
    xlab = {"added_noise": "noise SD [× map SD]", "shift_to_start": "fraction to start", "shift_to_end": "fraction to end", "smoothing": "Gaussian σ [positions]",
            "permuted_fraction": "fraction permuted"}
    for j, (op, title) in enumerate(OPS):
        for ds in profs:
            s = R[ds][kind]["operators"][op]
            x = np.arange(len(s["grid"]))
            axes[0][j].plot(x, s["rank"]["mean"], color="black", ls=ls[ds], lw=1.0, marker="o", ms=2, label=f"{NAME[ds]}")
            axes[1][j].plot(x, s["temporal"]["mean"], color=style.MEASURED, ls=ls[ds], lw=1.0, marker="s", ms=2, label=f"{NAME[ds]}")
            for i, k in ((0, "rank"), (1, "temporal")):
                m = s[k]["registers"]["registering_magnitude"]
                if m is not None and ds == profs[0]:
                    axes[i][j].axvline(s["grid"].index(m), color=style.GREY, lw=style.LW_THIN, ls=":")
        for i, k in ((0, "rank"), (1, "temporal")):
            axes[i][j].axhline(R[profs[0]][kind]["chance"][k], color=style.REFERENCE, lw=style.LW_THIN, ls="--")
            axes[i][j].set_xticks(x, [f"{g:g}" for g in s["grid"]], fontsize=5.5, rotation=60)
            style.despine(axes[i][j])
        axes[0][j].set_title(title, fontsize=7.5)
        axes[1][j].set_xlabel(xlab[op], fontsize=6.5)
    axes[0][0].set_ylabel("rank agreement (↑)", fontsize=7)
    axes[1][0].set_ylabel("temporal profile error\n[positions] (↓)", fontsize=7)
    axes[0][0].legend(frameon=False, fontsize=5.5, loc="lower left")
    fig.tight_layout()
    fig.savefig(PAPER / "img" / "fig_res_degradation.pdf")
    fig.savefig(RESULTS_V2 / "fig_res_degradation.png", dpi=200)
    plt.close(fig)
    prov("Figure 7", src, f"{{{','.join(profs)}}}.{kind}.operators.<op>.{{rank,temporal}}", "scripts/v2/v7_scores.py; scripts/v2/v10_write_paper.py", "generation 0; evaluation 20260915")


def figure_floor(kind="recency"):
    """Figure 8 (v2): for each method, the primary trained model's score and the ten-member ensemble range, against the
    exact attribution of the reference model, for rank agreement, channel allocation error and temporal profile error."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from degradx.viz import style

    src = ARTIFACTS_V2 / "v8_reference_methods" / "tables" / "reference_values.json"
    R = json.loads(src.read_text())
    profs = [d for d in ("MATR", "HUST", "ISU_ILCC") if d in R]
    keys = [("rank", "rank agreement (↑)"), ("allocation", "channel allocation error (↓)"), ("temporal", "temporal profile error [pos.] (↓)")]
    style.apply()
    fig, axes = plt.subplots(len(profs), 3, figsize=(style.TEXTWIDTH_IN, 1.75 * len(profs)), squeeze=False)
    for i, ds in enumerate(profs):
        r = R[ds]["weightings"][kind]
        for j, (k, lab) in enumerate(keys):
            ax = axes[i][j]
            for m, (key, mlab) in enumerate(METHODS):
                fl = r["identifiability_floor"].get(key)
                if fl:
                    vals = [x[k] for x in fl["members"]]
                    ax.plot([m, m], [min(vals), max(vals)], color=style.FILL, lw=5, solid_capstyle="butt", zorder=1)
                    ax.scatter([m] * len(vals), vals, s=5, color=style.MEASURED_BUNDLE, zorder=2)
                t = r["scores"][f"trained/{key}"][k]
                ax.errorbar([m], [t["mean"]], yerr=[[t["mean"] - t["ci_low"]], [t["ci_high"] - t["mean"]]] if t.get("ci_low") is not None else None,
                            fmt="o", ms=3.5, color="black", lw=0.8, capsize=1.5, zorder=3)
            ax.axhline(r["scores"]["reference_exact"][k]["mean"], color=style.REFERENCE, lw=style.LW_THIN, ls="--")
            ax.set_xticks(range(len(METHODS)), [lab_ for _, lab_ in METHODS], fontsize=6.5)
            if i == 0:
                ax.set_title(lab, fontsize=7.5)
            if j == 0:
                ax.set_ylabel(NAME[ds], fontsize=8)
            style.despine(ax)
    fig.tight_layout()
    fig.savefig(PAPER / "img" / "fig_res_floor.pdf")
    fig.savefig(RESULTS_V2 / "fig_res_floor.png", dpi=200)
    plt.close(fig)
    prov("Figure 8", src, f"{{{','.join(profs)}}}.weightings.{kind}.{{scores,identifiability_floor}}", "scripts/v2/v8_reference_methods.py; scripts/v2/v10_write_paper.py",
         "generation 0; model_init A/B 0-4; attribution_sampling 0,1,2; evaluation 20260915")


if __name__ == "__main__":
    sys.exit(main())
