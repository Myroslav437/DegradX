#!/usr/bin/env python
"""S9 — results export and paper tables/figures from measured artifacts only (brief S9).

Reads the stage artifacts (S2-S8), writes machine-readable results to ``results/`` (one JSON per table, with the source
artifact path of every value), LaTeX table bodies to ``paper/tables/<name>.tex`` (\\input by paper.tex) and the Results
figures to ``paper/img/`` (PDF, paper style), and a provenance list to ``results/provenance.json`` that
``docs/RESULTS_PROVENANCE.md`` is built from. Cells without a measurement are written as void with the reason in a note.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from degradx import ARTIFACTS_DIR, REPO_ROOT, RESULTS_DIR
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.io import write_json

PAPER = REPO_ROOT / "paper"
TABLES = PAPER / "tables"
NAME = {"MATR": "MATR", "HUST": "HUST", "NASA_PCoE": "NASA PCoE"}
PROV: list[dict] = []


def commit_of(path: Path) -> str:
    out = subprocess.run(["git", "log", "-n", "1", "--format=%H", "--", str(path)], cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip()
    return out or "uncommitted"


def prov(cell: str, source: Path, key: str, script: str, seeds: str):
    PROV.append({"cell": cell, "artifact": str(source.relative_to(REPO_ROOT)), "key": key, "script": script, "seeds": seeds, "artifact_commit": commit_of(source)})


def f3(x, digits=3):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "--"
    ax = abs(x)
    if ax >= 100:
        return f"{x:.0f}"
    if ax >= 10:
        return f"{x:.1f}"
    if ax >= 1:
        return f"{x:.2f}"
    return f"{x:.{digits}f}"


class Notes:
    def __init__(self):
        self.reasons: list[str] = []

    def void(self, reason: str) -> str:
        reason = reason.replace("$<$", "<").replace("<", "$<$")
        if reason not in self.reasons:
            self.reasons.append(reason)
        return f"void$^{{{chr(ord('a') + self.reasons.index(reason))}}}$"

    def text(self) -> str:
        return " ".join(f"$^{{{chr(ord('a') + i)}}}${r}." for i, r in enumerate(self.reasons))


# ---------------------------------------------------------------------------------------------------------------- Table 1
def table_fidelity():
    src = ARTIFACTS_DIR / "s5_fidelity" / "tables" / "fidelity.json"
    R = json.loads(src.read_text())
    notes, rows, res = Notes(), [], {}
    for ds in ("MATR", "HUST", "NASA_PCoE"):
        r = R[ds]
        u = r["units"]
        seeds = r["per_generation_seed"]
        disc = [s["discriminative_error"] for s in seeds]
        fid = [s["frechet_ts2vec"] for s in seeds]
        cov = [s["cov_relative_frobenius"] for s in seeds]
        base = r["baseline_measured_fitting_vs_held_out"]
        units = f"{u['measured_held_out']} / {u['generated_per_seed']}"
        v = r["void"]
        c_disc = notes.void(f"{v['discriminative_error']} (D02b)") if v["discriminative_error"] else f"{f3(min(disc), 2)}--{f3(max(disc), 2)}"
        c_fid = (notes.void("representation-distance interval wider than half its value at the available held-out units (D02b)") if v["representation_distance"]
                 else f"{f3(np.mean(fid))} ({f3(base['frechet_ts2vec'])})")
        c_cov = notes.void(f"{v['covariance_agreement']} (D02b)") if v["covariance_agreement"] else f"{f3(np.mean(cov), 2)} ({f3(base['cov_relative_frobenius'], 2)})"
        t = r["tstr"]
        c_tstr = (notes.void(f"held-out units reaching EOL: {t['held_out_units']} $<$ 20 (D02b)") if t["void"]
                  else f"{f3(t['ratio'], 2)} [{f3(t['ci_low'], 2)}, {f3(t['ci_high'], 2)}]")
        rows.append(f"    {NAME[ds]} & {units} & {c_disc} & {c_fid} & {c_cov} & {c_tstr} \\\\")
        res[ds] = {"units_held_out": u["measured_held_out"], "units_held_out_reaching_eol": u["measured_held_out_reaching_eol"], "generated_units_per_seed": u["generated_per_seed"],
                   "window_length": r["window_length"], "discriminative_error_per_generation_seed": disc, "representation_distance_mean": float(np.mean(fid)),
                   "representation_distance_baseline": base["frechet_ts2vec"], "covariance_rel_frobenius_mean": float(np.mean(cov)), "covariance_baseline": base["cov_relative_frobenius"],
                   "transfer_ratio": t["ratio"], "transfer_ci": [t["ci_low"], t["ci_high"]], "void": {**v, "transfer_ratio": t["void"]}}
        for col in ("discriminative_error", "representation_distance", "covariance_agreement", "transfer_ratio"):
            prov(f"Table 1 / {NAME[ds]} / {col}", src, f"{ds}", "scripts/s5_fidelity.py", "generation 0,1,2; model_init 0-4; evaluation 20260915")
    body = "\n".join(rows)
    TABLES.mkdir(parents=True, exist_ok=True)
    (TABLES / "table_fidelity.tex").write_text(body + "\n")
    (TABLES / "table_fidelity_notes.tex").write_text("\\def\\TabFidelityNotes{" + notes.text() + "}\n")
    write_json(res, RESULTS_DIR / "table1_fidelity.json")
    return res


# ---------------------------------------------------------------------------------------------------------------- Table 2
def table_properties():
    notes = Notes()
    data = {}
    for ds in ("MATR", "HUST", "NASA_PCoE"):
        src = ARTIFACTS_DIR / "s5_fidelity" / "tables" / f"properties_{ds}.json"
        data[ds] = (src, {row["property"]: row for row in json.loads(src.read_text())})

    def med(v):
        return f3(v["median"]) if isinstance(v, dict) and "median" in v else "--"

    def cell(ds, prop, side, fmt):
        src, rows = data[ds]
        row = next((r for p, r in rows.items() if p.startswith(prop)), None)
        if row is None:
            return "--"
        if row.get("void") and side == "measured":
            return notes.void(row["void"].replace("<", "$<$") + " (D02)")
        val = row.get(side)
        prov(f"Table 2 / {NAME[ds]} / {prop} / {side}", src, prop, "scripts/s5_fidelity.py", "generation 0; evaluation 20260915")
        return fmt(val, row)

    specs = [
        ("Trajectory family, fit error", "trajectory family", lambda v, r: (v.split(";")[0].replace("two_term_exponential", "2-exp").replace("power_law", "power").replace("rollover", "roll.") + ", " + f3(float(v.split(";")[1]), 4)) if isinstance(v, str) else "--"),
        ("Drift rate [mAh/100 cyc.]", "drift rate", lambda v, r: med(v)),
        ("Transition position [$\\times T$]", "transition position", lambda v, r: med(v)),
        ("Noise variance, capacity [mAh$^2$]", "noise variance, capacity", lambda v, r: f3(v * 1e6) if isinstance(v, float) else "--"),
        ("Noise variance, charge time [min$^2$]", "noise variance, charge_time", lambda v, r: f3(v) if isinstance(v, float) else "--"),
        ("Noise autocorrelation, capacity", "noise lag-1 autocorrelation, capacity", lambda v, r: f3(v, 2) if isinstance(v, float) else "--"),
        ("Unit length [cycles]", "unit length", lambda v, r: med(v)),
        ("Regeneration rate [/100 pos.]", "positive pattern rate", lambda v, r: f3(v, 2) if isinstance(v, float) else "--"),
        ("Regeneration amplitude [mAh]", "positive pattern amplitude", lambda v, r: med(v)),
        ("Regeneration duration [pos.]", "positive pattern duration", lambda v, r: med(v)),
        ("Cross-channel covariance [rel. Frob.]", "cross-channel residual correlation", lambda v, r: (f3(r.get("relative_frobenius"), 2) if r.get("relative_frobenius") is not None else "--")),
    ]
    lines, res = [], {}
    for label, prop, fmt in specs:
        cells = []
        for ds in ("MATR", "HUST", "NASA_PCoE"):
            if prop.startswith("cross-channel"):
                cells += ["\\multicolumn{2}{c}{" + cell(ds, prop, "generated", fmt) + "}"]
            else:
                cells += [cell(ds, prop, "measured", fmt), cell(ds, prop, "generated", fmt)]
        lines.append(f"    {label} & " + " & ".join(cells) + " \\\\")
        res[label] = cells
    (TABLES / "table_properties.tex").write_text("\n".join(lines) + "\n")
    (TABLES / "table_properties_notes.tex").write_text("\\def\\TabPropertiesNotes{" + notes.text() + "}\n")
    write_json(res, RESULTS_DIR / "table2_properties.json")
    return res


OPS = [("added_noise", "Added noise"), ("shift_to_start", "Shifted mass (start)"), ("shift_to_end", "Shifted mass (end)"), ("smoothing", "Smoothing"),
       ("permuted_fraction", "Permuted fraction")]


def table_resolution(kind="recency"):
    """Table 4: smallest reliably resolved magnitude per score and operator, with the mean change of the score there."""
    src = ARTIFACTS_DIR / "s7_responsiveness" / "tables" / "part1_degradation.json"
    R = json.loads(src.read_text())
    rows, res = [], {}

    def cell(s, key):
        rr = s[f"{key}_resolution"]["resolution"] if f"{key}_resolution" in s else None
        grid = s["grid"]
        means = s[f"{key}_mean"]
        if rr is None:
            return "not resolved", None
        drop = means[grid.index(rr)] - means[0]
        return f"{rr:g} ({drop:+.3f})", drop

    for label, ds_list, key in (("Rank agreement, graded field", ("MATR", "HUST", "NASA_PCoE"), "rank"),
                                ("Retrieval (paired), sparse set", ("NASA_PCoE",), "retrieval"),
                                ("Retrieval (plain), sparse set", ("NASA_PCoE",), "plain_retrieval")):
        for ds in ds_list:
            r = R[ds][kind]
            cells = []
            for op, _ in OPS:
                s = r["operators"][op]
                if key == "plain_retrieval":
                    s = {"grid": s["grid"], "plain_retrieval_mean": s["plain_retrieval_mean"], "plain_retrieval_resolution": s["plain_retrieval_resolution"]}
                txt, drop = cell(s, key)
                cells.append(txt)
                res.setdefault(f"{label} / {NAME[ds]}", {})[op] = {"resolution": s[f"{key}_resolution"]["resolution"], "drop": drop}
                prov(f"Table 4 / {label} / {NAME[ds]} / {op}", src, f"{ds}.{kind}.operators.{op}", "scripts/s7_responsiveness.py", "generation 0; evaluation 20260915")
            rows.append(f"    {label.split(',')[0]} ({NAME[ds]}) & " + " & ".join(cells) + " \\\\")
    (TABLES / "table_resolution.tex").write_text("\n".join(rows) + "\n")
    write_json(res, RESULTS_DIR / "table4_resolution.json")
    return res


def figure_degradation(kind="recency"):
    """Figure 7: each score against degradation magnitude, one panel per operator (recency weighting)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from degradx.viz import style

    src = ARTIFACTS_DIR / "s7_responsiveness" / "tables" / "part1_degradation.json"
    R = json.loads(src.read_text())
    style.apply()
    fig, axes = plt.subplots(1, len(OPS), figsize=(style.TEXTWIDTH_IN, 2.1), sharey=True)
    ls = {"MATR": "-", "HUST": "--", "NASA_PCoE": ":"}
    xlab = {"added_noise": "noise SD [× map SD]", "shift_to_start": "fraction to start", "shift_to_end": "fraction to end", "smoothing": "Gaussian σ [positions]",
            "permuted_fraction": "fraction permuted"}
    for ax, (op, title) in zip(axes, OPS):
        for ds in ("MATR", "HUST", "NASA_PCoE"):
            s = R[ds][kind]["operators"][op]
            x = np.arange(len(s["grid"]))
            ax.plot(x, s["rank_mean"], color="black", ls=ls[ds], lw=1.0, marker="o", ms=2, label=f"rank, {NAME[ds]}")
            if "retrieval_mean" in s:
                ax.plot(x, s["retrieval_mean"], color=style.MEASURED, lw=1.2, marker="s", ms=2, label="retrieval (paired), NASA PCoE")
                ax.plot(x, s["plain_retrieval_mean"], color=style.MEASURED_BUNDLE, ls=":", lw=1.2, marker="^", ms=2, label="retrieval (plain), NASA PCoE")
                ax.axhline(R[ds][kind]["chance_retrieval"], color=style.REFERENCE, lw=style.LW_THIN, ls="--")
        ax.axhline(R["MATR"][kind]["chance_rank"], color=style.REFERENCE, lw=style.LW_THIN)
        ax.set_xticks(x, [f"{g:g}" for g in s["grid"]], fontsize=5.5, rotation=60)
        ax.set_title(title, fontsize=7.5)
        ax.set_xlabel(xlab[op], fontsize=6.5)
        style.despine(ax)
    axes[0].set_ylabel("score")
    axes[0].legend(frameon=False, fontsize=5, loc="lower left")
    fig.tight_layout()
    fig.savefig(PAPER / "img" / "fig_res_degradation.pdf")
    fig.savefig(RESULTS_DIR / "fig_res_degradation.png", dpi=200)
    plt.close(fig)
    prov("Figure 7", src, f"all profiles, {kind}", "scripts/s7_responsiveness.py; scripts/s9_write_paper.py", "generation 0; evaluation 20260915")


def table_usability(kind="recency"):
    """Table 3: declared target properties and usability checks per profile (recency weighting; other weightings in results)."""
    notes = Notes()
    U = {}
    for ds in ("MATR", "HUST", "NASA_PCoE"):
        src = ARTIFACTS_DIR / "s6_usability" / "tables" / f"usability_{ds}.json"
        U[ds] = (src, json.loads(src.read_text())[ds])
    no_pat = "no inserted patterns in the profile (D05)"

    def ci(x):
        return f"{f3(x['nmse_increase'], 4)} [{f3(x['ci_low'], 4)}, {f3(x['ci_high'], 4)}]"

    rows = []

    def row(label, bound, fn):
        cells = []
        for ds in ("MATR", "HUST", "NASA_PCoE"):
            src, r = U[ds]
            cells.append(fn(ds, r[kind]))
            prov(f"Table 3 / {label} / {NAME[ds]}", src, f"{ds}.{kind}", "scripts/s6_usability.py", "generation 0; model_init 0-4 (A, B); evaluation 20260915")
        rows.append(f"    {label} & {bound} & " + " & ".join(cells) + " \\\\")

    row("Variance ratio of the two terms of Eq.~\\ref{eq:target}", "0.05--0.50",
        lambda ds, r: notes.void(no_pat) if r["variance_ratio_pattern_to_mean"] is None else f3(r["variance_ratio_pattern_to_mean"], 4))
    row("Association of $y$ with RUL (Spearman)", "reported", lambda ds, r: f3(r["spearman_y_rul"], 2))
    row("Model error on $y$ (NRMSE; members passing)", "$\\le$ 0.30", lambda ds, r: f"{f3(r['primary_nrmse'], 3)} ({r['gate_pass_members']}/10)")
    row("Correlation of graded and sparse fields", "$\\le$ 0.30",
        lambda ds, r: notes.void(no_pat) if r["graded_sparse_correlation"] is None else f3(r["graded_sparse_correlation"], 3))
    for name, label in (("mean_term_removed", "Error change, mean term removed"), ("pattern_term_removed", "Error change, pattern term removed")):
        row(label, "$>0$", lambda ds, r, name=name: notes.void(no_pat) if "void" in r["term_ablation"] else ci(r["term_ablation"][name]))
    for c, label in (("null_flat", "Permutation importance, null channel (flat)"), ("null_permuted", "Permutation importance, null channel (permuted)")):
        row(label, "$\\le$ 0.02", lambda ds, r, c=c: ci(r["permutation_importance"][c]))

    def redundant(ds, r):
        red = r["redundant_channels"]
        if not red:
            return "--"
        return "; ".join(f"{c.replace('_', ' ').replace('internal resistance', 'IR').replace('temperature mean', 'temp.')}: {f3(v['predictability_r2'], 2)}, {f3(v['conditional_importance']['nmse_increase'], 4)}"
                         for c, v in red.items())
    row("Redundant channels: $R^2$ from others, conditional importance", "reported", redundant)
    (TABLES / "table_usability.tex").write_text("\n".join(rows) + "\n")
    (TABLES / "table_usability_notes.tex").write_text("\\def\\TabUsabilityNotes{" + notes.text() + "}\n")
    write_json({ds: U[ds][1] for ds in U}, RESULTS_DIR / "table3_usability.json")


def figure_fidelity():
    """Paper Figure 6: measured (grey) and generated (black) capacity trajectories, one panel per profile, z = 0 and z = 1 marked."""
    import pickle

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd
    from matplotlib.lines import Line2D

    from degradx import CONFIG_DIR, DATA_DIR
    from degradx.data.audit import CleaningRule, clean_capacity
    from degradx.utils.config import load_declarations, load_yaml
    from degradx.viz import style

    decl = load_declarations()
    dd = decl["declared_by_design"]
    rule = CleaningRule("D12", **dd["capacity_series"]["cleaning_rule"]["params"])
    style.apply()
    fig, axes = plt.subplots(1, 3, figsize=(style.TEXTWIDTH_IN, 2.0))
    for ax, ds, f in zip(axes, ("MATR", "HUST", "NASA_PCoE"), ("matr", "hust", "nasa_pcoe")):
        q_nom = float(load_yaml(CONFIG_DIR / "profiles" / f"{f}.yaml")["nominal_capacity_Ah"]["value"])
        prof = json.loads((ARTIFACTS_DIR / "s3_fit_profiles" / "profiles" / f"{ds}.json").read_text())
        split = pd.read_csv(ARTIFACTS_DIR / "s3_fit_profiles" / "tables" / f"split_{ds}.csv")
        df = pd.read_csv(DATA_DIR / "processed" / "cycle_tables" / f"{ds}.csv.gz", low_memory=False)
        for cid in split["cell_id"]:
            d = clean_capacity(df[df["cell_id"] == cid], "capacity_cycler_Ah", rule, q_nom)
            ax.plot(d["position"], d["capacity_cycler_Ah"], color=style.MEASURED_BUNDLE, lw=style.LW_THIN, zorder=1)
        units, _ = pickle.loads((DATA_DIR / "generated" / ds / "seed0.pkl").read_bytes())
        for u in units[:25]:
            ax.plot(np.arange(1, u.T + 1), u.x[:, 0], color=style.GENERATED, lw=0.5, zorder=2)
        q1 = prof["estimated_from_data"]["E3_channel_mappings"]["capacity"]["phi0"]
        rho = prof["declared_used"]["rho"]
        ax.set_ylim(0.9 * rho * q_nom, 1.06 * q1)
        for val, lab in ((q1, r"$z=0$"), (rho * q_nom, r"$z=1$")):
            ax.axhline(val, color=style.REFERENCE, lw=style.LW_THIN, ls="--", zorder=0)
            ax.text(1.01, val, lab, transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=6.5, color=style.GREY, clip_on=False)
        ax.set_title(f"{NAME[ds]} ({len(split)} measured units)", fontsize=8.5)
        ax.set_xlabel(r"position $t$ (cycle)")
        style.despine(ax)
        prov(f"Figure 6 / {NAME[ds]}", ARTIFACTS_DIR / "s3_fit_profiles" / "profiles" / f"{ds}.json", "generated units seed 0 (first 25) + S3 split units", "scripts/s4_generate_units.py; scripts/s9_write_paper.py", "generation 0")
    axes[0].set_ylabel("capacity [Ah]")
    axes[1].legend(handles=[Line2D([], [], color=style.MEASURED_BUNDLE, lw=1, label="measured"), Line2D([], [], color=style.GENERATED, lw=1, label="generated")],
                   frameon=False, fontsize=6.5, loc="lower left", bbox_to_anchor=(0.0, -0.03), ncol=2, handlelength=1.5, columnspacing=1.0)
    fig.tight_layout(w_pad=1.6)
    fig.savefig(PAPER / "img" / "fig_res_fidelity.pdf")
    fig.savefig(RESULTS_DIR / "fig_res_fidelity.png", dpi=200)
    plt.close(fig)


# ------------------------------------------------------------------------------------------------------ Figure 8, Table 5
SETTINGS = [("noise_variance_multiplier", "Noise variance", "multiple of fitted variance"), ("transition_sharpness_multiplier", "Transition sharpness", "exponent s in $z^s$"),
            ("window_length_L", "Sequence length", "window length $L$"), ("pattern_amplitude_multiplier", "Pattern amplitude", "multiple of fitted amplitude")]


SCORES = [("Rank agreement", "rank"), ("Retrieval (paired)", "retrieval")]


def table_range():
    """Table 5: the operating range per generator setting, profile and score. A setting value is inside the range when the
    score is neither saturated nor near chance on either probe (D20: the reference model, which is the declared primary
    scoring target, and IG on the trained model) and the trained model passes the accuracy gate; outside, the table names
    the probe and the failure."""
    notes = Notes()
    src = ARTIFACTS_DIR / "s7_responsiveness" / "tables" / "part2_generator_settings.json"
    rows = json.loads(src.read_text())
    label = {"reference_exact": "reference model", "ig": "IG on the trained model"}
    out, res = [], {}
    for setting, title, _x in SETTINGS:
        for ds in ("MATR", "HUST", "NASA_PCoE"):
            rr = sorted([r for r in rows if r["dataset"] == ds and r["setting"] == setting], key=lambda r: r["value"])
            if not rr:
                continue
            for score_name, score in SCORES:
                probes = [p for p in ("reference_exact", "ig") if any(r.get(f"{score}_{p}_state") for r in rr)]
                if not probes:
                    continue
                states = {}
                for r in rr:
                    s = {label[p]: r.get(f"{score}_{p}_state") for p in probes}
                    if r["nrmse"] > 0.3:  # scores on a model below the accuracy gate are void (Section 3.5.2)
                        s[label["ig"]] = "below the accuracy gate"
                    states[r["value"]] = s
                inside = [v for v, s in states.items() if all(x == "responsive" for x in s.values())]
                outside = {v: "; ".join(f"{p} {x}" for p, x in s.items() if x != "responsive") for v, s in states.items() if v not in inside}
                examined = f"{rr[0]['value']:g}--{rr[-1]['value']:g}"
                rng = f"{min(inside):g}--{max(inside):g}" if inside else notes.void("no value of this setting leaves the score responsive on both probes")
                gaps = [v for v in states if v not in inside and min(inside, default=0) < v < max(inside, default=0)]
                by_probe = {}  # one clause per probe and failure, with the values it occurs at
                for v, s in states.items():
                    for p, x in s.items():
                        if x != "responsive":
                            by_probe.setdefault((p, x), []).append(v)
                fail = "; ".join(f"{p} {x} " + ("at every value" if len(vs) == len(states) else "at " + ", ".join(f"{v:g}" for v in sorted(vs)))
                                 for (p, x), vs in by_probe.items()) or "--"
                out.append(f"    {title} & {NAME[ds]} & {score_name} & {examined} & {rng}{'$^{*}$' if gaps else ''} & {fail} \\\\")
                res[f"{setting} / {ds} / {score}"] = {"range_examined": [rr[0]["value"], rr[-1]["value"]], "responsive_values": inside, "outside": outside,
                                                     "states": states, "probes": probes}
                prov(f"Table 5 / {title} / {NAME[ds]} / {score_name}", src, f"{ds}.{setting}", "scripts/s7_responsiveness.py", "generation 0; model_init 0; evaluation 20260915")
    star = " $^{*}$A value inside the interval is not responsive; the failure column names it." if any("$^{*}$" in line for line in out) else ""
    (TABLES / "table_range.tex").write_text("\n".join(out) + "\n")
    (TABLES / "table_range_notes.tex").write_text("\\def\\TabRangeNotes{" + notes.text() + star + "}\n")
    write_json(res, RESULTS_DIR / "table5_operating_range.json")


def figure_range():
    """Figure 8: scores against the generator settings (recency), IG on the trained model and the exact attribution of the
    reference model (D20), with the saturation and chance levels of the normalised score."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from degradx.viz import style

    src = ARTIFACTS_DIR / "s7_responsiveness" / "tables" / "part2_generator_settings.json"
    p1 = json.loads((ARTIFACTS_DIR / "s7_responsiveness" / "tables" / "part1_degradation.json").read_text())
    rows = json.loads(src.read_text())
    style.apply()
    fig, axes = plt.subplots(1, len(SETTINGS), figsize=(style.TEXTWIDTH_IN, 2.2), sharey=True)
    ls = {"MATR": "-", "HUST": "--", "NASA_PCoE": ":"}
    for ax, (setting, title, xlabel) in zip(axes, SETTINGS):
        for ds in ("MATR", "HUST", "NASA_PCoE"):
            rr = sorted([r for r in rows if r["dataset"] == ds and r["setting"] == setting], key=lambda r: r["value"])
            if not rr:
                continue
            x = [r["value"] for r in rr]
            ax.plot(x, [r["rank_ig"] for r in rr], color="black", ls=ls[ds], lw=1.0, marker="o", ms=2, label=f"rank, IG on trained, {NAME[ds]}")
            ax.plot(x, [r["rank_reference_exact"] for r in rr], color=style.MEASURED, ls=ls[ds], lw=1.0, marker="o", ms=2, label=f"rank, reference model, {NAME[ds]}")
            if any(r.get("retrieval_ig") is not None for r in rr):
                ax.plot(x, [r["retrieval_ig"] for r in rr], color="black", lw=1.2, marker="s", ms=2.5, label="retrieval, IG on trained, NASA PCoE")
                ax.axhline(p1[ds]["recency"]["chance_retrieval"], color=style.REFERENCE, lw=style.LW_THIN, ls="--")
        ax.axhline(p1["MATR"]["recency"]["chance_rank"], color=style.REFERENCE, lw=style.LW_THIN)
        ax.axhline(0.95, color=style.REFERENCE, lw=style.LW_THIN, ls=":")
        ax.set_xscale("log", base=2)
        vals = sorted({r["value"] for r in rows if r["setting"] == setting})
        ax.set_xticks(vals, [f"{v:g}" for v in vals], fontsize=5.5)
        ax.minorticks_off()
        ax.set_title(title, fontsize=7.5)
        ax.set_xlabel(xlabel, fontsize=6.5)
        style.despine(ax)
    axes[0].set_ylabel("score")
    from matplotlib.lines import Line2D

    handles = [Line2D([], [], color="black", lw=1.0, marker="o", ms=2, label="rank agreement, IG on the trained model"),
               Line2D([], [], color=style.MEASURED, lw=1.0, marker="o", ms=2, label="rank agreement, exact attribution of the reference model"),
               Line2D([], [], color="black", lw=1.2, marker="s", ms=2.5, label="retrieval (paired), IG on the trained model")]
    handles += [Line2D([], [], color="black", ls=ls[ds], lw=1.0, label=NAME[ds]) for ds in ls]
    fig.legend(handles=handles, frameon=False, fontsize=5, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    fig.savefig(PAPER / "img" / "fig_res_range.pdf")
    fig.savefig(RESULTS_DIR / "fig_res_range.png", dpi=200)
    plt.close(fig)
    prov("Figure 8", src, "all profiles, recency", "scripts/s7_responsiveness.py; scripts/s9_write_paper.py", "generation 0; model_init 0; evaluation 20260915")


# ---------------------------------------------------------------------------------------------------------------- Table 6
METHODS = [("timeshap", "TimeSHAP"), ("integrated_gradients", "IG"), ("feature_occlusion", "Feature occlusion")]


def table_reference(kind="recency"):
    """Table 6: reference values per profile (D24), trained vs reference model, with the exact attribution of the reference
    model, the ensemble range (C2) and TimeSHAP from the average event (C4 secondary)."""
    notes = Notes()
    src = ARTIFACTS_DIR / "s8_reference_methods" / "tables" / "reference_values.json"
    R = json.loads(src.read_text())
    seeds = "generation 0; model_init 0 (A), ensemble A/B 0-4; attribution_sampling 0-1 (TimeSHAP trained), 0 (reference); evaluation 20260915"
    no_pat = "no inserted patterns in the profile (D05)"
    unused = "the trained model does not use the pattern term (Table~\\ref{tab:res:usability}; D21)"

    def mean_ci(s, digits=3):
        if s is None or s.get("mean") is None:
            return "--"
        if s.get("ci_low") is None:
            return f3(s["mean"], digits)
        return f"{f3(s['mean'], digits)} [{f3(s['ci_low'], digits)}, {f3(s['ci_high'], digits)}]"

    rows = []
    for di, ds in enumerate(("MATR", "HUST", "NASA_PCoE")):
        if ds not in R:
            continue
        r = R[ds]["weightings"][kind]
        sc, void = r["scores"], r["void"]
        has_pat = "no inserted patterns" not in (void["trained_retrieval"] or "")
        if di:
            rows.append("    \\midrule")
        rows.append(f"    \\multicolumn{{7}}{{l}}{{\\textit{{{NAME[ds]}}} ({R[ds]['windows']} windows from {R[ds]['units']} test units; TimeSHAP on {R[ds]['timeshap_windows']} of them)}} \\\\")
        for key, label in METHODS:
            t, f = sc[f"trained/{key}"], sc[f"reference/{key}"]
            if void["trained_all"]:
                rt = zt = retr_t = notes.void(void["trained_all"])
            else:
                rt, zt = mean_ci(t["rank"]), f3(t["zero_mass"]["mean"])
                retr_t = notes.void(no_pat) if not has_pat else (notes.void(unused) if void["trained_retrieval"] else mean_ci(t["retrieval"]))
            retr_f = notes.void(no_pat) if not has_pat else mean_ci(f["retrieval"])
            rows.append(f"    {label} & {rt} & {mean_ci(f['rank'])} & {retr_t} & {retr_f} & {zt} & {f3(f['zero_mass']['mean'])} \\\\")
            prov(f"Table 6 / {NAME[ds]} / {label}", src, f"{ds}.weightings.{kind}.scores.{{trained,reference}}/{key}", "scripts/s8_reference_methods.py", seeds)
        ex, exs = sc["reference_exact"], sc["reference_exact_timeshap_windows"]
        rows.append(f"    Exact attribution $w(x - x^{{0}})$ & -- & {mean_ci(ex['rank'])} & -- & {notes.void(no_pat) if not has_pat else mean_ci(ex['retrieval'])} & -- & {f3(ex['zero_mass']['mean'])} \\\\")
        rows.append(f"    \\quad on the TimeSHAP windows & -- & {mean_ci(exs['rank'])} & -- & {notes.void(no_pat) if not has_pat else mean_ci(exs['retrieval'])} & -- & -- \\\\")
        prov(f"Table 6 / {NAME[ds]} / exact attribution", src, f"{ds}.weightings.{kind}.scores.reference_exact(_timeshap_windows)", "scripts/s8_reference_methods.py", seeds)
        fl = r["identifiability_floor"]
        for key, label in (("integrated_gradients", "IG"), ("feature_occlusion", "Feature occlusion")):
            q = fl[key]
            rows.append(f"    Ensemble range, {label} (10 models) & {f3(q['rank_min'])}--{f3(q['rank_max'])} & -- & -- & -- & -- & -- \\\\")
        prov(f"Table 6 / {NAME[ds]} / ensemble range", src, f"{ds}.weightings.{kind}.identifiability_floor", "scripts/s8_reference_methods.py", seeds)
        if "secondary_average_event" in r:
            s2 = r["secondary_average_event"]["scores"]
            rows.append(f"    TimeSHAP, average-event background & {mean_ci(s2['rank'])} & -- & -- & -- & {f3(s2['zero_mass']['mean'])} & -- \\\\")
            prov(f"Table 6 / {NAME[ds]} / TimeSHAP average event", src, f"{ds}.weightings.{kind}.secondary_average_event", "scripts/s8_reference_methods.py", seeds)
    (TABLES / "table_reference.tex").write_text("\n".join(rows) + "\n")
    (TABLES / "table_reference_notes.tex").write_text("\\def\\TabReferenceNotes{" + notes.text() + "}\n")
    write_json({"weighting_in_table": kind, "values": R}, RESULTS_DIR / "table6_reference_values.json")


def main() -> int:
    p = stage_parser(__doc__, "s9_write_paper")
    p.add_argument("--tables", nargs="*", default=["fidelity", "properties", "figure_fidelity"])
    args = p.parse_args()
    StageContext.from_args(args)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    fns = {"fidelity": table_fidelity, "properties": table_properties, "figure_fidelity": figure_fidelity, "resolution": table_resolution,
           "figure_degradation": figure_degradation, "usability": table_usability, "reference": table_reference,
           "range": table_range, "figure_range": figure_range}
    for t in args.tables:
        fns[t]()
    old = json.loads((RESULTS_DIR / "provenance.json").read_text()) if (RESULTS_DIR / "provenance.json").exists() else []
    keep = [x for x in old if not any(x["cell"].startswith(y["cell"].split(" / ")[0]) for y in PROV)]
    allp = keep + PROV
    write_json(allp, RESULTS_DIR / "provenance.json")
    write_provenance_md(allp)
    return 0


def write_provenance_md(entries):
    lines = ["# Results provenance", "",
             "Every table cell and figure in Section 4 of `paper/paper.tex` and the artifact that produced it. Generated by",
             "`scripts/s9_write_paper.py` from `results/provenance.json`; the artifact commit is the last commit touching the artifact",
             "file. Seeds: generation / model_init / attribution_sampling / evaluation streams (`degradx.utils.seeding.derive_seed` under",
             "base seed 20260915 unless stated). Configs: `configs/declarations.yaml` (r2 + dated decisions) and `configs/stages/<stage>.yaml`.", "",
             "| table / figure cell | artifact | key | script | seeds | artifact commit |", "|---|---|---|---|---|---|"]
    for e in sorted(entries, key=lambda x: x["cell"]):
        lines.append(f"| {e['cell']} | `{e['artifact']}` | {e['key']} | `{e['script']}` | {e['seeds']} | `{e['artifact_commit'][:10]}` |")
    (REPO_ROOT / "docs" / "RESULTS_PROVENANCE.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
