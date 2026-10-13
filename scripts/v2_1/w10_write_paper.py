#!/usr/bin/env python
"""W10 (brief "DegradX v2.1") — results export, paper tables and Figures 6-8 for the v2.1 scope: MATR and HUST from the
v2 stage artifacts (tag v2-results; not re-run), FORM (TRI_FORMATION) from the v2.1 W-stage artifacts, plus the one
MATR/HUST computation of v2.1 (TSTR on the V4 X3-off sets, declarations v2_1.tstr_without_x3).

Built on the V10 machinery (scripts/v2/v10_write_paper.py, itself on the S9 helpers): one JSON per table under
``results/v2.1`` with the source artifact of every value, LaTeX table bodies and notes under ``paper/tables/`` (the v2
bodies remain at tag v2-results), figures under ``paper/img/`` (PNG copies under results/v2.1), and the provenance list
``results/v2.1/provenance.json`` from which the v2.1 section of ``docs/RESULTS_PROVENANCE.md`` is written (the v2 and v1
sections are kept below it). Cells without a measurement are void with the reason in a table note.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "v2"))

import numpy as np  # noqa: E402

from degradx import ARTIFACTS_DIR, ARTIFACTS_V2, ARTIFACTS_V21, REPO_ROOT, RESULTS_V21  # noqa: E402
from degradx.utils.cli import StageContext, stage_parser  # noqa: E402
from degradx.utils.io import write_json  # noqa: E402

_spec = importlib.util.spec_from_file_location("s9", str(REPO_ROOT / "scripts" / "s9_write_paper.py"))
S9 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S9)
f3, Notes, commit_of = S9.f3, S9.Notes, S9.commit_of
PAPER = REPO_ROOT / "paper"
TABLES = PAPER / "tables"
PROFILES = ("MATR", "HUST", "TRI_FORMATION")
NAME = {"MATR": "MATR", "HUST": "HUST", "TRI_FORMATION": "FORM"}
V21 = {"TRI_FORMATION"}
STAGE = {"v3": ("v3_fit_profiles", "w3_fit_profiles"), "v4": ("v4_generate_units", "w4_generate_units"), "v5": ("v5_fidelity", "w5_fidelity"),
         "v6": ("v6_usability", "w6_usability"), "v7": ("v7_scores", "w7_scores"), "v8": ("v8_reference_methods", "w8_reference_methods")}
PROV: list[dict] = []
SEEDS_GEN = "generation 0,1,2; model_init 0-4; evaluation 20260915"


def art(ds: str, stage: str) -> Path:
    v2s, v21s = STAGE[stage]
    return ARTIFACTS_V21 / v21s if ds in V21 else ARTIFACTS_V2 / v2s


def script(ds: str, v2_script: str) -> str:
    return f"scripts/v2/{v2_script}" + (" (v2.1 W-stage run)" if ds in V21 else "")


def prov(cell: str, source: Path, key: str, script_: str, seeds: str):
    PROV.append({"cell": cell, "artifact": str(Path(source).relative_to(REPO_ROOT)), "key": key, "script": script_, "seeds": seeds,
                 "artifact_commit": commit_of(source)})


def ci(x, digits=2):
    if x is None or x.get("mean", x.get("ratio")) is None:
        return "--"
    m = x.get("mean", x.get("ratio"))
    if x.get("ci_low") is None:
        return f3(m, digits)
    return f"{f3(m, digits)} [{f3(x['ci_low'], digits)}, {f3(x['ci_high'], digits)}]"


def load_per_ds(stage: str, rel: str) -> dict:
    """{ds: (source path, the ds entry)} from the v2 or v2.1 artifact of each profile."""
    out = {}
    for ds in PROFILES:
        src = art(ds, stage) / rel
        if src.exists():
            R = json.loads(src.read_text())
            if ds in R:
                out[ds] = (src, R[ds])
    return out


# ---------------------------------------------------------------------------------------------------------------- Table 1
def table_fidelity():
    """Table 1 (v2.1): per profile, the v2 generator (X2 + X3), the same profile with X3 switched off (generation seed 0),
    and the v1 generator (shared mappings, independent noise), with discriminative error, covariance agreement and the TSTR
    transfer ratio. FORM has no v1 profile; its transfer ratio without X3 is not declared (v2_1.tstr_without_x3)."""
    F = load_per_ds("v5", "tables/fidelity.json")
    RD = load_per_ds("v5", "tables/discriminator_readability.json")
    x3_src = ARTIFACTS_V21 / "w5_fidelity" / "tstr_without_x3" / "tables" / "tstr_without_x3.json"
    X3 = json.loads(x3_src.read_text()) if x3_src.exists() else {}
    v1_src = ARTIFACTS_DIR / "s5_fidelity" / "tables" / "fidelity.json"
    V1 = json.loads(v1_src.read_text())
    notes, rows, res = Notes(), [], {}
    for di, (ds, (src, r)) in enumerate(F.items()):
        u, t, v = r["units"], r["tstr"], dict(r["void"])
        disc = [s["discriminative_error"] for s in r["per_generation_seed"]]
        rd = RD.get(ds, (None, None))[1]
        if rd and not rd["readable"] and not v["discriminative_error"]:  # D02b readability (DEVIATIONS T6)
            seeds_txt = ", ".join(f"{f3(x['discriminative_error'], 2)} [{f3(x['ci_low'], 2)}, {f3(x['ci_high'], 2)}]" for x in rd["per_generation_seed"])
            v["discriminative_error"] = (f"{NAME[ds]}: 95\\% unit-bootstrap half-width above half the distance from 0.5 for "
                                         f"{sum(not x['readable'] for x in rd['per_generation_seed'])} of 3 generation seeds; values {seeds_txt}")
        cov = [s["cov_relative_frobenius"] for s in r["per_generation_seed"]]
        base = r["baseline_measured_fitting_vs_held_out"]
        bi = base["cov_relative_frobenius_interval"]
        off = r.get("x3_off_seed0") or {}
        c_disc = notes.void(v["discriminative_error"]) if v["discriminative_error"] else f"{f3(min(disc), 2)}--{f3(max(disc), 2)}"
        c_cov = (notes.void(v["covariance_agreement"]) if v["covariance_agreement"]
                 else f"{f3(np.mean(cov), 2)} ({f3(base['cov_relative_frobenius'], 2)}; {f3(bi['ci_low'], 2)}--{f3(bi['ci_high'], 2)})")
        c_tstr = (notes.void(f"{NAME[ds]}: held-out units reaching EOL {t['held_out_units']} $<$ 20") if t["void"]
                  else f"{f3(t['ratio'], 2)} [{f3(t['ci_low'], 2)}, {f3(t['ci_high'], 2)}]")
        if di:
            rows.append("    \\midrule")
        rows.append(f"    {NAME[ds]} & offsets, correlated noise & {u['measured_held_out']} / {u['generated_per_seed']} & {c_disc} & {c_cov} & {c_tstr} \\\\")
        # without X3 (generation seed 0)
        xo = X3.get(ds, {}).get("rows", {}).get("v2_without_x3_seed0")
        if xo:
            c_x3t = f"{f3(xo['ratio'], 2)} [{f3(xo['ci_low'], 2)}, {f3(xo['ci_high'], 2)}]"
            prov(f"Table 1 / {NAME[ds]} / transfer ratio without X3", x3_src, f"{ds}.rows.v2_without_x3_seed0", "scripts/v2_1/w5_tstr_without_x3.py",
                 "generation 0 (X3-off set); model_init 0-4; evaluation 20260915")
        else:
            c_x3t = notes.void(f"{NAME[ds]}: the transfer ratio with independent noise is computed for MATR and HUST only, on their existing sets") if ds in V21 else "--"
        rows.append(f"    & \\quad independent noise & & {f3(off.get('discriminative_error'), 2)} & {f3(off.get('cov_relative_frobenius'), 2)} & {c_x3t} \\\\")
        # v1 generator (shared mappings, independent noise)
        if ds in V1:
            v1r = V1[ds]
            v1_disc = [s["discriminative_error"] for s in v1r["per_generation_seed"]]
            v1_cov = float(np.mean([s["cov_relative_frobenius"] for s in v1r["per_generation_seed"]]))
            v1t = v1r["tstr"]
            rows.append(f"    & \\quad no offsets, independent noise & & {f3(min(v1_disc), 2)}--{f3(max(v1_disc), 2)} & {f3(v1_cov, 2)} ({f3(v1r['baseline_measured_fitting_vs_held_out']['cov_relative_frobenius'], 2)}) & "
                        f"{f3(v1t['ratio'], 2)} [{f3(v1t['ci_low'], 2)}, {f3(v1t['ci_high'], 2)}] \\\\")
            prov(f"Table 1 / {NAME[ds]} / v1 generator row", v1_src, f"{ds}.{{per_generation_seed,tstr,baseline_measured_fitting_vs_held_out}}", "scripts/s5_fidelity.py (v1)",
                 "generation 0,1,2; model_init 0-4; evaluation 20260915")
        res[ds] = {"units": u, "discriminative_error_per_generation_seed": disc, "covariance_rel_frobenius_mean": float(np.mean(cov)),
                   "covariance_baseline": base["cov_relative_frobenius"], "covariance_baseline_interval": [bi["ci_low"], bi["ci_high"]],
                   "x3_off_seed0": {"discriminative_error": off.get("discriminative_error"), "cov_relative_frobenius": off.get("cov_relative_frobenius"),
                                    "transfer_ratio": xo},
                   "transfer_ratio": t["ratio"], "transfer_ci": [t["ci_low"], t["ci_high"]], "readings": r.get("readings"), "v1_vs_v2": r.get("v1_vs_v2"),
                   "x2_x3_shares": X3.get(ds, {}).get("shares"), "void": {**v, "transfer_ratio": t["void"]}, "source": str(src.relative_to(REPO_ROOT))}
        for col in ("discriminative_error", "covariance_agreement", "x3_off", "transfer_ratio"):
            prov(f"Table 1 / {NAME[ds]} / {col}", src, ds, script(ds, "v5_fidelity.py"), SEEDS_GEN)
        if ds in RD:
            prov(f"Table 1 / {NAME[ds]} / discriminative_error readability", RD[ds][0], ds, script(ds, "v5_discriminator_readability.py"), "generation 0,1,2; evaluation 20260915")
    # X2's and X3's shares in transfer (paired log-ratio differences; declarations v2_1.tstr_without_x3.shares)
    share_txt = []
    for ds in ("MATR", "HUST"):
        s = X3.get(ds, {}).get("shares")
        if s:
            x2, x3 = s["X2_share_vs_v1_full_D27"], s["X3_share_seed0"]
            s0 = X3[ds]["rows"]["v2_seed0"]  # the declared row "v2 (generation seed 0)" (v2_1.tstr_without_x3.rows), printed in this note
            share_txt.append(f"{NAME[ds]}: offsets {f3(x2['ratio_of_ratios'], 2)}$\\times$ [{f3(np.exp(x2['ci_low']), 2)}, {f3(np.exp(x2['ci_high']), 2)}], "
                             f"correlated noise {f3(x3['ratio_of_ratios'], 2)}$\\times$ [{f3(np.exp(x3['ci_low']), 2)}, {f3(np.exp(x3['ci_high']), 2)}], "
                             f"with the profile with both at {f3(s0['ratio'], 2)} [{f3(s0['ci_low'], 2)}, {f3(s0['ci_high'], 2)}] at that seed")
            prov(f"Table 1 / {NAME[ds]} / X2 and X3 shares in transfer", x3_src, f"{ds}.shares", "scripts/v2_1/w5_tstr_without_x3.py", "generation 0 and v1 0-2; model_init 0-4; evaluation 20260915")
    lead = ("Shares in transfer, at generation seed 0, as ratios of transfer ratios with paired 95\\% BCa intervals over held-out units: of the per-unit offsets, "
            "the profile without offsets (with the measured cells cleaned as for the others; Table~\\ref{tab:res:isolation}) over the profile with offsets and independent noise; "
            "of the correlated noise, the profile with independent noise over the profile with both. " + "; ".join(share_txt) + ". ") if share_txt else ""
    res["readings_cross_profile_v2"] = json.loads((ARTIFACTS_V2 / "v5_fidelity" / "tables" / "fidelity.json").read_text()).get("readings_cross_profile")
    (TABLES / "table_fidelity.tex").write_text("\n".join(rows) + "\n")
    (TABLES / "table_fidelity_notes.tex").write_text("\\def\\TabFidelityNotes{" + lead + notes.text() + "}\n")
    write_json(res, RESULTS_V21 / "table1_fidelity.json")
    return res


# ---------------------------------------------------------------------------------------------------------------- Table 2
def table_properties():
    notes = Notes()
    data = {}
    for ds in PROFILES:
        src = art(ds, "v5") / "tables" / f"properties_{ds}.json"
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
        ("Positive residual runs per 100 positions", "positive residual runs per 100 positions", lambda v: num(v, d=2)),
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
            prov(f"Table 2 / {NAME[ds]} / {label}", src, prefix, script(ds, "v5_fidelity.py") if ds in V21 else "scripts/v2/v5_properties.py (D30 re-run of the V5 property table)",
                 "generation 0; evaluation 20260915")
        lines.append(f"    {label} & " + " & ".join(cells) + " \\\\")
        res[label] = {ds: cells[i * 3:(i + 1) * 3] for i, ds in enumerate(data)}
    (TABLES / "table_properties.tex").write_text("\n".join(lines) + "\n")
    counts, short = [], []
    tol_mAh = None
    for ds in data:
        _src, drift = row_of(ds, "drift rate")
        if drift:
            ns = [drift[sd]["n"] for sd in sides]
            counts.append(f"{ns[0]}, {ns[1]} and {ns[2]} in {NAME[ds]}")
            n_gen = json.loads((art(ds, "v5") / "tables" / "fidelity.json").read_text())[ds]["units"]["generated_per_seed"]
            if ns[2] < n_gen:
                short.append((ds, n_gen - ns[2], n_gen))
    if short:
        from degradx.utils.config import load_declarations

        import _common as C
        from degradx.generator.state import spec_from_declarations
        decl = load_declarations()
        parts = []
        for ds, n_out, n_gen in short:
            sp = spec_from_declarations(decl, C.q_nom_of(ds))
            parts.append(f"in {NAME[ds]}, {n_out} of the {n_gen} generated units end more than that tolerance, {f3(sp.record_end_tau * sp.q_nom * 1000, 1)}\\,mAh, above the threshold, "
                         "since capacity noise varies slowly, and are left out of those rows")
        tail = "; " + "; ".join(parts)
    else:
        tail = ""
    extra = (" Generated series are read with the record-end tolerance applied to measured records, so a generated unit enters the rows that depend on EOL when it reaches the"
             f" threshold within that tolerance{tail}. Those rows rest on {'; '.join(counts)} units (fitting, held-out, generated). The capacity-pair correlations carry an errors-in-variables bias of the"
             " estimator (the degradation state is read from noisy capacity), once in the fitted target and again when re-estimated on generated data. Residual runs are counted by the detection rule"
             " of Section~\\ref{sec:calibration}; only FORM carries an inserted pattern type, so in MATR and HUST every run counted on generated units comes from noise.")
    (TABLES / "table_properties_notes.tex").write_text("\\def\\TabPropertiesNotes{" + (notes.text() + extra).strip() + "}\n")
    write_json({"profiles": list(data), "columns": list(sides), "rows": res}, RESULTS_V21 / "table2_properties.json")
    return res


# ---------------------------------------------------------------------------------------------------------------- Table 4
def table_usability(kind="recency"):
    notes = Notes()
    data = {}
    for ds in PROFILES:
        src = art(ds, "v6") / "tables" / f"usability_{ds}.json"
        if src.exists():
            data[ds] = (src, json.loads(src.read_text())[ds][kind])
    seeds = "generation 0; model_init 0-4 (A, B); evaluation 20260915"
    rows = []

    def add(label, fn, key):
        cells = []
        for ds, (src, r) in data.items():
            cells.append(fn(ds, r))
            prov(f"Table 4 / {NAME[ds]} / {label}", src, f"{ds}.{kind}.{key}", script(ds, "v6_usability.py"), seeds)
        rows.append(f"    {label} & " + " & ".join(cells) + " \\\\")

    def pattern_ratio(ds, r):
        vr = r.get("variance_ratio_pattern_to_mean")
        if vr is None:
            return notes.void("no inserted pattern type is enabled in the profile")
        m_, e_ = f"{vr:.1e}".split("e")
        ex = int(e_)
        ex_tex = f"-{{{abs(ex)}}}" if ex < 0 else f"{ex}"  # "-{5}": tex_minus leaves a minus before a brace alone (math mode)
        return f"${m_}\\times10^{{{ex_tex}}}$"

    def pattern_ablation(ds, r):
        if r.get("variance_ratio_pattern_to_mean") is None:
            return notes.void("no inserted pattern type is enabled in the profile")
        ab = r["term_ablation"]["pattern_term_removed"]
        return ci(ab | {"mean": ab["nmse_increase"]}, 4)

    add("Accuracy, NRMSE of the primary model (members passing)", lambda ds, r: f"{f3(r['primary_nrmse'], 3)} ({r['gate_pass_members']}/10)", "primary_nrmse")
    add("Offset term, share of Var$(y)$", lambda ds, r: f3(r.get("offset_term", {}).get("share_of_var_y"), 3), "offset_term")
    add("Spearman correlation of $y$ with RUL", lambda ds, r: f3(r["spearman_y_rul"], 2), "spearman_y_rul")
    for c, lab in (("capacity", "capacity"), ("charge_time", "charge time"), ("mean_discharge_voltage", "mean discharge V")):
        add(f"Permutation importance, {lab}", lambda ds, r, c=c: f3(r["permutation_importance"][c]["nmse_increase"], 3), f"permutation_importance.{c}")
    for c, lab in (("capacity", "capacity"), ("charge_time", "charge time"), ("mean_discharge_voltage", "mean discharge V")):
        add(f"Channel use (conditional importance), {lab}", lambda ds, r, c=c: ci(r["channel_usage"]["A0"][c] | {"mean": r["channel_usage"]["A0"][c]["nmse_increase"]}, 3), f"channel_usage.A0.{c}")
    add("Members using every weighted channel", lambda ds, r: f"{r['channel_usage_gate']['members_using_all']}/10", "channel_usage_gate")
    add("Leakage, null channels (upper bound, flat / permuted)", lambda ds, r: f"{f3(r['permutation_importance']['null_flat']['ci_high'], 4)} / {f3(r['permutation_importance']['null_permuted']['ci_high'], 4)}", "permutation_importance.null_*")
    add("Redundant channels: $R^2$, conditional importance",
        lambda ds, r: "; ".join(f"{c.replace('internal_resistance', 'IR').replace('temperature_mean', 'temp.')} {f3(v['predictability_r2'], 2)}, {f3(v['conditional_importance']['nmse_increase'], 4)}"
                                for c, v in r["redundant_channels"].items()) or "none", "redundant_channels")
    add("Pattern term, variance ratio to the mean term", pattern_ratio, "variance_ratio_pattern_to_mean")
    add("Pattern term removed, NMSE increase", pattern_ablation, "term_ablation.pattern_term_removed")
    add("Graded/sparse correlation $|r|$", lambda ds, r: f3(abs(r["graded_sparse_abs_corr"]), 3) if r.get("graded_sparse_abs_corr") is not None
        else notes.void("no inserted pattern type is enabled in the profile"), "graded_sparse_abs_corr")
    (TABLES / "table_usability.tex").write_text("\n".join(rows) + "\n")
    n_units = [f"{r['units']['test']} ({NAME[ds]})" for ds, (src, r) in data.items()]
    lead = f"Generated test units: {', '.join(n_units)}. " if n_units else ""
    (TABLES / "table_usability_notes.tex").write_text("\\def\\TabUsabilityNotes{" + lead + notes.text() + "}\n")
    write_json({"weighting": kind, "values": {ds: r for ds, (src, r) in data.items()}}, RESULTS_V21 / "table4_usability.json")


# ---------------------------------------------------------------------------------------------------------------- Table 5
OPS = [("added_noise", "Added noise"), ("shift_to_start", "Mass to start"), ("shift_to_end", "Mass to end"), ("smoothing", "Smoothing"), ("permuted_fraction", "Permuted fraction")]
SCORES = [("rank", "rank"), ("allocation", "alloc."), ("temporal", "temporal")]


def table_scores(kind="recency"):
    data = load_per_ds("v7", "tables/degradation.json")
    rows = []
    for op, lab in OPS:
        cells = []
        for ds, (src, R) in data.items():
            s = R[kind]["operators"][op]
            for k, _ in SCORES:
                m = s[k]["registers"]["registering_magnitude"]
                cells.append(f"{m}" if m is not None else "--")
        rows.append(f"    {lab} & " + " & ".join(cells) + " \\\\")
    for ds, (src, R) in data.items():
        prov(f"Table 5 / {NAME[ds]}", src, f"{ds}.{kind}.operators.<op>.<score>.registers", script(ds, "v7_scores.py"), "generation 0; evaluation 20260915")
    (TABLES / "table_resolution.tex").write_text("\n".join(rows) + "\n")
    # paired retrieval (profiles with patterns): resolution magnitude per operator, for the caption / note
    pr = {ds: R[kind]["paired_retrieval"] for ds, (src, R) in data.items() if R[kind].get("paired_retrieval")}
    write_json({"weighting": kind, "profiles": list(data), "values": {ds: R for ds, (src, R) in data.items()}, "paired_retrieval": pr}, RESULTS_V21 / "table5_scores.json")
    return pr


# ---------------------------------------------------------------------------------------------------------------- Table 3
def table_isolation():
    """X1 (D26): TSTR ratios by input set on the v1 profiles (V1; MATR, HUST) and on the v2 / v2.1 profiles (V5 / W5)."""
    src1 = ARTIFACTS_V2 / "v1_tstr_isolation" / "tables" / "tstr_isolation.json"
    R1 = json.loads(src1.read_text())
    F = load_per_ds("v5", "tables/fidelity.json")
    # the declared input-set names (declarations v2.tstr_isolation.input_sets), as Figure 5 labels them
    sets = [(k, k.replace("_", " ").capitalize()) for k in ("full", "capacity_only", "capacity_relative", "capacity_state", "full_centred")]
    rows = []
    for key, lab in sets:
        cells = [ci(R1[ds]["input_sets"].get(key)) if R1[ds]["input_sets"].get(key) else "--" for ds in ("MATR", "HUST")]
        cells += [ci(r.get("tstr_input_sets", {}).get(key)) if r.get("tstr_input_sets", {}).get(key) else "--" for ds, (src, r) in F.items()]
        rows.append(f"    {lab} & " + " & ".join(cells) + " \\\\")
    rows.append("    \\midrule")
    for name, lab in (("per_cell_structure", "$\\Delta\\log$: full vs capacity only"), ("offsets_specifically", "$\\Delta\\log$: full vs full centred"),
                      ("initial_capacity_spread", "$\\Delta\\log$: capacity only vs capacity relative")):
        cells = []
        for ds in ("MATR", "HUST"):
            t = R1[ds]["tests"][name]
            cells.append(f"{f3(t['log_ratio_difference'], 2)} [{f3(t['ci_low'], 2)}, {f3(t['ci_high'], 2)}]")
        for ds, (src, r) in F.items():
            t = r.get("x1_on_v2", {}).get("tests", {}).get(name)
            cells.append(f"{f3(t['log_ratio_difference'], 2)} [{f3(t['ci_low'], 2)}, {f3(t['ci_high'], 2)}]" if t else "--")
        rows.append(f"    {lab} & " + " & ".join(cells) + " \\\\")
    prov("Table 3 / profiles without offsets (v1)", src1, "{MATR,HUST}.input_sets, tests", "scripts/v2/v1_tstr_isolation.py", SEEDS_GEN)
    for ds, (src, r) in F.items():
        prov(f"Table 3 / {NAME[ds]} / profile with offsets", src, f"{ds}.tstr_input_sets, x1_on_v2.tests", script(ds, "v5_fidelity.py"), SEEDS_GEN)
    (TABLES / "table_isolation.tex").write_text("\n".join(rows) + "\n")
    write_json({"v1_profiles": {ds: {"input_sets": {k: {kk: vv for kk, vv in v.items() if kk != "runs"} for k, v in R1[ds]["input_sets"].items()},
                                     "tests": R1[ds]["tests"], "readings": R1[ds]["readings"]} for ds in ("MATR", "HUST")},
                "v2_profiles": {ds: {"input_sets": {k: {kk: vv for kk, vv in v.items() if kk != "runs"} for k, v in r.get("tstr_input_sets", {}).items()},
                                     "x1_on_v2": r.get("x1_on_v2")} for ds, (src, r) in F.items()}},
               RESULTS_V21 / "table3_tstr_isolation.json")


# ---------------------------------------------------------------------------------------------------------------- Table 6
METHODS = [("integrated_gradients", "IG"), ("feature_occlusion", "Occlusion"), ("timeshap", "TimeSHAP")]


def table_reference(kind="recency"):
    notes = Notes()
    data = load_per_ds("v8", "tables/reference_values.json")
    seeds = "generation 0; model_init 0 (A), ensemble A/B 0-4; attribution_sampling 0,1,2 (TimeSHAP), 0 (floor); evaluation 20260915"
    rows, retr, src_of = [], {}, {}
    for di, (ds, (src, Rd)) in enumerate(data.items()):
        src_of[ds] = src
        r = Rd["weightings"][kind]
        sc = r["scores"]
        cvoid = r.get("channel_usage_void")
        if di:
            rows.append("    \\midrule")
        rows.append(f"    \\multicolumn{{9}}{{l}}{{\\textit{{{NAME[ds]}}} ({Rd['windows']} windows from {Rd['units']} test units; every method on every window)}} \\\\")
        for key, label in METHODS:
            t, f = sc[f"trained/{key}"], sc[f"reference/{key}"]

            def tr(k, d=3):
                if cvoid and k in ("allocation", "zero_mass"):
                    return notes.void(cvoid)
                return ci(t[k], d)
            rows.append(f"    {label} & {tr('rank')} & {f3(f['rank']['mean'])} & {tr('allocation')} & {f3(f['allocation']['mean'])} & {tr('temporal', 2)} & {f3(f['temporal']['mean'], 2)} & {tr('zero_mass')} & {f3(f['zero_mass']['mean'])} \\\\")
            prov(f"Table 6 / {NAME[ds]} / {label}", src, f"{ds}.weightings.{kind}.scores.{{trained,reference}}/{key}", script(ds, "v8_reference_methods.py"), seeds)
            if "retrieval" in t or "retrieval" in f:
                retr.setdefault(ds, {})[label] = {"trained": t.get("retrieval"), "reference": f.get("retrieval")}
        ex = sc["reference_exact"]
        stk = lambda x, d: (f"\\begin{{tabular}}[t]{{@{{}}c@{{}}}}{f3(x['mean'], d)}\\\\ {{[{f3(x['ci_low'], d)}, {f3(x['ci_high'], d)}]}}"  # noqa: E731
                            "\\end{tabular}")
        rows.append(f"    Exact $w(x - x^{{0}})$ & -- & {stk(ex['rank'], 3)} & -- & {stk(ex['allocation'], 3)} & -- & {stk(ex['temporal'], 2)} & -- & {f3(ex['zero_mass']['mean'])} \\\\")
        fl = r["identifiability_floor"]
        for key, label in METHODS:
            if key not in fl:
                continue
            q = fl[key]
            rows.append(f"    Range, {label} & {f3(q['rank_min'])}--{f3(q['rank_max'])} & -- & {f3(q['allocation_min'])}--{f3(q['allocation_max'])} & -- & {f3(q['temporal_min'], 2)}--{f3(q['temporal_max'], 2)} & -- & -- & -- \\\\")
        prov(f"Table 6 / {NAME[ds]} / ensemble range", src, f"{ds}.weightings.{kind}.identifiability_floor", script(ds, "v8_reference_methods.py"), seeds)
        if "secondary_average_event" in r:
            s2 = r["secondary_average_event"]["scores"]
            rows.append(f"    TimeSHAP, average event & {ci(s2['rank'], 3)} & -- & {ci(s2['allocation'], 3)} & -- & {ci(s2['temporal'], 2)} & -- & {ci(s2['zero_mass'], 3)} & -- \\\\")
            prov(f"Table 6 / {NAME[ds]} / TimeSHAP average event", src, f"{ds}.weightings.{kind}.secondary_average_event", script(ds, "v8_reference_methods.py"), seeds)
    (TABLES / "table_reference.tex").write_text("\n".join(rows) + "\n")
    rt = ""
    for ds, by in retr.items():
        # trained-model sparse-set scores are computed only if the pattern-term ablation of the primary model has a 95 % CI above 0
        # (declarations v2_1.readings.sparse_set_trained, D21 logic); otherwise they are void and are not printed
        usrc = art(ds, "v6") / "tables" / f"usability_{ds}.json"
        ab = json.loads(usrc.read_text())[ds][kind]["term_ablation"]["pattern_term_removed"]
        trained_ok = ab["ci_low"] > 0
        n_units = next((v["reference"].get("units") for v in by.values() if v["reference"]), None)
        ref = "; ".join(f"{lab} {f3(v['reference']['mean'])}" for lab, v in by.items() if v["reference"])
        if trained_ok:
            tr = "; ".join(f"{lab} {ci(v['trained'], 3)}" for lab, v in by.items() if v["trained"])
            rt += (f"Paired retrieval (average precision of the paired difference against the sparse set), {NAME[ds]}, on the {n_units} test units whose windows "
                   f"contain the sparse set: reference model {ref}; trained model {tr}. ")
        else:
            rt += (f"Paired retrieval (average precision of the paired difference against the sparse set), {NAME[ds]}, on the {n_units} test units whose windows "
                   f"contain the sparse set: reference model {ref}; trained model void, since removing the pattern term from the training target does not "
                   f"change the model's error ({ci(ab | {'mean': ab['nmse_increase']}, 4)}). ")
        prov(f"Table 6 / {NAME[ds]} / paired retrieval (note)", src_of[ds], f"{ds}.weightings.{kind}.scores.*.retrieval", script(ds, "v8_reference_methods.py"), seeds)
        prov(f"Table 6 / {NAME[ds]} / trained retrieval void reading", usrc, f"{ds}.{kind}.term_ablation.pattern_term_removed", script(ds, "v6_usability.py"), seeds)
    (TABLES / "table_reference_notes.tex").write_text("\\def\\TabReferenceNotes{" + rt + notes.text() + "}\n")
    write_json({"weighting_in_table": kind, "values": {ds: Rd for ds, (src, Rd) in data.items()}, "paired_retrieval": retr}, RESULTS_V21 / "table6_reference_values.json")


# ---------------------------------------------------------------------------------------------------------------- profile facts
def profile_facts():
    """Numbers the text quotes about the profiles (Section 3.4, the opening of Section 4): FORM's ingestion, audit, offset
    pre-screen, D05 and mechanism readings (W1, W2, W4), and ISU-ILCC's stop (v2 V4), each with its source."""
    w1 = ARTIFACTS_V21 / "w1_ingest" / "tables" / "ingest_summary.json"
    w2 = ARTIFACTS_V21 / "w2_audit" / "tables" / "audit_summary.json"
    w4 = ARTIFACTS_V21 / "w4_generate_units" / "tables" / "summary.json"
    isu = ARTIFACTS_V2 / "v4_generate_units" / "tables" / "summary.json"
    I, A, G = json.loads(w1.read_text()), json.loads(w2.read_text()), json.loads(w4.read_text())["TRI_FORMATION"]
    out = {"FORM": {
        "cells_in_scope": I["counts"]["in_scope"], "positions": I["counts"]["positions"], "modal_protocol": I["modal_tuple"],
        "reaching_eol": A["eligibility"]["E3"]["units_reaching_eol_after_guard"], "held_out_reaching_eol": A["eligibility"]["E3"]["held_out_reaching_eol"],
        "fitting_reaching_eol": A["eligibility"]["E3"]["fitting_reaching_eol"], "T": A["audit"]["eol_primary"]["T"], "min_T": A["eligibility"]["E4"]["min_T"],
        "weight_guard": A["eligibility"]["E5"]["weight_guard"], "offset_prescreen": {k: A["offset_prescreen"]["per_weighting"][k]["share"] for k in ("recency", "uniform")},
        "formation_protocol_share": A["offset_prescreen"]["formation_protocol_share"]["headline"], "d05": A["d05"],
        "mechanism": A["mechanism_diagnostic"]["fitting_units"], "separability": A["mechanism_diagnostic"]["separability"],
        "offset_share_generated": {g: {k: v["weightings"][k]["offset_share_of_var_y"] for k in v["weightings"]} for g, v in G["seeds"].items()},
        "pattern_to_state_variance": {g: {k: v["weightings"][k]["pattern_to_state_variance_ratio"] for k in v["weightings"]} for g, v in G["seeds"].items()},
        "patterns_per_seed": {g: v["patterns"] for g, v in G["seeds"].items()}}}
    for key, src_ in (("cells_in_scope, positions, modal_protocol", w1), ("eligibility, EOL, weight guard, pre-screen, D05, mechanism", w2), ("offset share and pattern term on generated data", w4)):
        prov(f"Section 3.4 / FORM / {key}", src_, key, {w1: "scripts/v2_1/w1_ingest.py", w2: "scripts/v2_1/w2_audit.py", w4: "scripts/v2/v4_generate_units.py (v2.1 W-stage run)"}[src_],
             "split 20260915; generation 0,1,2")
    if isu.exists():
        J = json.loads(isu.read_text())
        J = J.get("ISU_ILCC", J)
        out["ISU_ILCC"] = {"offset_share": {g: {k: v["weightings"][k]["offset_share_of_var_y"] for k in v["weightings"]} for g, v in J.get("seeds", {}).items()}}
        prov("Section 3.4 / ISU-ILCC / offset share", isu, "ISU_ILCC.seeds.*.weightings.*.offset_share_of_var_y", "scripts/v2/v4_generate_units.py (v2 V4)", "generation 0,1,2")
    write_json(out, RESULTS_V21 / "profile_facts.json")
    return out


# ---------------------------------------------------------------------------------------------------------------- diagrams (W9)
DIAGRAMS = [
    ("Figure 1", "fig_loop", "declarations v2_1.scope.profiles, statistics.splits.measured, fidelity, v2.fidelity.table2, v2.tstr_isolation.input_sets, usability.identifiability_floor; viz LABEL"),
    ("Figure 2", "fig_generator", "data/v2.1/generated/TRI_FORMATION/seed0.pkl unit 173 (selection rule in the script); W3 profile TRI_FORMATION.json (offsets, within_unit_correlation, mappings, E6_patterns); v2 profiles MATR/HUST E6_patterns.enabled; declarations target.window_length_L, position_profiles.recency, weights.beta"),
    ("Figure 3", "fig_mean_component", "W3 profile TRI_FORMATION.json (offsets_all_fitting_units, E1_theta_distribution, E3_channel_mappings, declared_used); units at the 10th / 90th percentile of the charge-time offset"),
    ("Figure 4", "fig_weights", "declarations target.window_length_L, position_profiles.{recency,final_position}, v2.scope.weightings and v2.scope.dropped"),
    ("Figure 5", "fig_tstr", "declarations v2.tstr_isolation.input_sets (full_D27 excluded), statistics.splits.measured"),
]


def diagrams():
    for cell, name, inputs in DIAGRAMS:
        prov(f"{cell} / {name} (methodology diagram)", PAPER / "img" / f"{name}.pdf", inputs, f"paper/img/scripts/{name}.py (with paper/img/scripts/diagram_inputs.py)", "none (deterministic)")


# ---------------------------------------------------------------------------------------------------------------- provenance
def write_provenance_md(entries):
    """v2.1 rows on top; the v2 and v1 sections of the existing file kept verbatim below."""
    path = REPO_ROOT / "docs" / "RESULTS_PROVENANCE.md"
    old = path.read_text()
    keep = old[old.index("## v2 "):] if "## v2 " in old else ""
    head = "| table / figure cell | artifact | key | script | seeds | artifact commit |"
    lines = ["# Results provenance", "",
             "Every table cell and figure of `paper/paper.tex` and the artifact that produced it. The artifact commit is the last",
             "commit touching the artifact file. Seeds: generation / model_init / attribution_sampling / evaluation streams",
             "(`degradx.utils.seeding.derive_seed` under base seed 20260915). Configs: `configs/declarations.yaml` (r4 with its dated",
             "supersession log).", "",
             "## v2.1 (current paper; generated by `scripts/v2_1/w10_write_paper.py` from `results/v2.1/provenance.json`; MATR and HUST read from the v2 artifacts, FORM from v2.1)", "",
             head, "|---|---|---|---|---|---|"]
    for e in sorted(entries, key=lambda x: x["cell"]):
        lines.append(f"| {e['cell']} | `{e['artifact']}` | {e['key']} | `{e['script']}` | {e['seeds']} | `{e['artifact_commit'][:10]}` |")
    path.write_text("\n".join(lines) + "\n\n" + keep)


def tex_minus():
    import re

    for name in ("table_fidelity", "table_properties", "table_usability", "table_resolution", "table_isolation", "table_reference",
                 "table_fidelity_notes", "table_properties_notes", "table_usability_notes", "table_reference_notes"):
        f = TABLES / f"{name}.tex"
        if f.exists():
            t = f.read_text()
            f.write_text(re.sub(r"(?<![\w$\-])-(?=\d)", "$-$", t))


# ---------------------------------------------------------------------------------------------------------------- Figures
def figure_fidelity():
    """Figure 6: measured (grey) and generated (black) capacity trajectories per profile, z = 0 and z = 1 marked."""
    import pickle

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    import _common as C
    from degradx.data.audit import CleaningRule, clean_capacity
    from degradx.utils.config import load_declarations
    from degradx.viz import style

    dd = load_declarations()["declared_by_design"]
    rule = CleaningRule("D12", **dd["capacity_series"]["cleaning_rule"]["params"])
    profs = [d for d in PROFILES if (art(d, "v5") / "tables" / f"properties_{d}.json").exists()]
    style.apply()
    fig, axes = plt.subplots(1, len(profs), figsize=(style.TEXTWIDTH_IN, 2.0), squeeze=False)
    for ax, ds in zip(axes[0], profs):
        q_nom = C.q_nom_of(ds)
        prof = C.v2_profile(ds)
        split = C.v2_split(ds)
        df = C.load_scope(ds, dd)
        for cid in split["cell_id"]:
            d = clean_capacity(df[df["cell_id"] == cid], "capacity_cycler_Ah", rule, q_nom)
            ax.plot(d["position"], d["capacity_cycler_Ah"], color=style.MEASURED_BUNDLE, lw=style.LW_THIN, zorder=1)
        units, _ = pickle.loads((C.generated_dir(ds) / "seed0.pkl").read_bytes())
        for u in units[:25]:
            ax.plot(np.arange(1, u.T + 1), u.x[:, 0], color=style.GENERATED, lw=0.5, zorder=2)
        q1 = prof["estimated_from_data"]["E3_channel_mappings"]["capacity"]["phi0"]
        rho = prof["declared_used"]["rho"]
        ax.set_ylim(0.9 * rho * q_nom, 1.08 * q1)
        for val, lab in ((q1, r"$z=0$"), (rho * q_nom, r"$z=1$")):
            ax.axhline(val, color=style.REFERENCE, lw=style.LW_THIN, ls="--", zorder=0)
            ax.text(1.01, val, lab, transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=6, color=style.GREY, clip_on=False)
        ax.set_title(f"{NAME[ds]} ({len(split)} measured units)", fontsize=8.5)
        ax.set_xlabel(r"position $t$ (cycle)")
        style.despine(ax)
        prov(f"Figure 6 / {NAME[ds]}", C.v3_dir(ds) / "profiles" / f"{ds}.json", "generated units seed 0 (first 25) + the split units",
             script(ds, "v4_generate_units.py") + "; scripts/v2_1/w10_write_paper.py", "generation 0")
    axes[0][0].set_ylabel("capacity [Ah]")
    axes[0][0].legend(handles=[Line2D([], [], color=style.MEASURED_BUNDLE, lw=1, label="measured"), Line2D([], [], color=style.GENERATED, lw=1, label="generated")],
                      frameon=False, fontsize=6.5, loc="lower left", ncol=2, handlelength=1.5, columnspacing=1.0)
    fig.tight_layout(w_pad=2.2)
    fig.savefig(PAPER / "img" / "fig_res_fidelity.pdf")
    fig.savefig(RESULTS_V21 / "fig_res_fidelity.png", dpi=200)
    plt.close(fig)


LS = {"MATR": "-", "HUST": "--", "TRI_FORMATION": ":"}


def figure_degradation(kind="recency"):
    """Figure 7: rank agreement and the temporal profile error against each operator's magnitude (X5), per profile, with
    each profile's chance level and registering magnitude."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from degradx.viz import style

    data = load_per_ds("v7", "tables/degradation.json")
    profs = list(data)
    style.apply()
    fig, axes = plt.subplots(2, len(OPS), figsize=(style.TEXTWIDTH_IN, 3.3), sharey="row")
    xlab = {"added_noise": "noise SD [× map SD]", "shift_to_start": "fraction to start", "shift_to_end": "fraction to end", "smoothing": "Gaussian σ [positions]",
            "permuted_fraction": "fraction permuted"}
    for j, (op, title) in enumerate(OPS):
        for ds in profs:
            s = data[ds][1][kind]["operators"][op]
            x = np.arange(len(s["grid"]))
            axes[0][j].plot(x, s["rank"]["mean"], color="black", ls=LS[ds], lw=1.0, marker="o", ms=2, label=NAME[ds])
            axes[1][j].plot(x, s["temporal"]["mean"], color=style.MEASURED, ls=LS[ds], lw=1.0, marker="s", ms=2, label=NAME[ds])
        for i, k in ((0, "rank"), (1, "temporal")):
            for ds in profs:
                axes[i][j].axhline(data[ds][1][kind]["chance"][k], color=style.REFERENCE, lw=style.LW_THIN, ls=LS[ds])
            axes[i][j].set_xticks(x, [f"{g:g}" for g in s["grid"]], fontsize=5.5, rotation=60)
            style.despine(axes[i][j])
        axes[0][j].set_title(title, fontsize=7.5)
        axes[1][j].set_xlabel(xlab[op], fontsize=6.5)
    axes[0][0].set_ylabel("rank agreement (↑)", fontsize=7)
    axes[1][0].set_ylabel("temporal profile error\n[positions] (↓)", fontsize=7)
    axes[0][0].legend(frameon=False, fontsize=5.5, loc="lower left")
    fig.tight_layout()
    fig.savefig(PAPER / "img" / "fig_res_degradation.pdf")
    fig.savefig(RESULTS_V21 / "fig_res_degradation.png", dpi=200)
    plt.close(fig)
    for ds, (src, _R) in data.items():
        prov(f"Figure 7 / {NAME[ds]}", src, f"{ds}.{kind}.operators.<op>.{{rank,temporal}}, chance", script(ds, "v7_scores.py") + "; scripts/v2_1/w10_write_paper.py",
             "generation 0; evaluation 20260915")


def figure_floor(kind="recency"):
    """Figure 8: for each method, the primary trained model's score and the ten-member ensemble range, against the exact
    attribution of the reference model, for rank agreement, channel allocation error and temporal profile error."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from degradx.viz import style

    data = load_per_ds("v8", "tables/reference_values.json")
    profs = list(data)
    keys = [("rank", "rank agreement (↑)"), ("allocation", "channel allocation error (↓)"), ("temporal", "temporal profile error [pos.] (↓)")]
    style.apply()
    fig, axes = plt.subplots(len(profs), 3, figsize=(style.TEXTWIDTH_IN, 1.75 * len(profs)), squeeze=False)
    for i, ds in enumerate(profs):
        r = data[ds][1]["weightings"][kind]
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
    fig.savefig(RESULTS_V21 / "fig_res_floor.png", dpi=200)
    plt.close(fig)
    for ds, (src, _R) in data.items():
        prov(f"Figure 8 / {NAME[ds]}", src, f"{ds}.weightings.{kind}.{{scores,identifiability_floor}}", script(ds, "v8_reference_methods.py") + "; scripts/v2_1/w10_write_paper.py",
             "generation 0; model_init A/B 0-4; attribution_sampling 0,1,2; evaluation 20260915")


def main() -> int:
    p = stage_parser(__doc__, "v2.1/w10_write_paper")
    p.add_argument("--tables", nargs="*", default=["diagrams", "facts", "fidelity", "properties", "usability", "scores", "isolation", "reference", "figure_fidelity", "figure_degradation",
                                                    "figure_floor"])
    p.add_argument("--tables-dir", default=None, help="write LaTeX bodies and figures here instead of paper/ (testing)")
    p.add_argument("--no-provenance", action="store_true")
    args = p.parse_args()
    global TABLES, PAPER
    if args.dry_run:
        print(f"plan: v2.1 tables/figures {args.tables}")
        return 0
    if args.tables_dir:
        TABLES = Path(args.tables_dir)
        TABLES.mkdir(parents=True, exist_ok=True)
        PAPER = TABLES
        (PAPER / "img").mkdir(parents=True, exist_ok=True)
    StageContext.from_args(args)
    RESULTS_V21.mkdir(parents=True, exist_ok=True)
    fns = {"diagrams": diagrams, "facts": profile_facts, "fidelity": table_fidelity, "properties": table_properties, "usability": table_usability, "scores": table_scores, "isolation": table_isolation,
           "reference": table_reference, "figure_fidelity": figure_fidelity, "figure_degradation": figure_degradation, "figure_floor": figure_floor}
    for t in args.tables:
        fns[t]()
        print(f"[w10] {t} done", flush=True)
    tex_minus()
    if args.no_provenance:
        return 0
    old = json.loads((RESULTS_V21 / "provenance.json").read_text()) if (RESULTS_V21 / "provenance.json").exists() else []
    keep = [x for x in old if not any(x["cell"].split(" / ")[0] == y["cell"].split(" / ")[0] for y in PROV)]
    allp = keep + PROV
    write_json(allp, RESULTS_V21 / "provenance.json")
    write_provenance_md(allp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
