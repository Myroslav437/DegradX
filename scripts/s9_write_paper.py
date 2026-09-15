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
            ax.text(0.98, val, lab, transform=ax.get_yaxis_transform(), ha="right", va="bottom", fontsize=6.5, color=style.GREY)
        ax.set_title(f"{NAME[ds]} ({len(split)} measured units)", fontsize=8.5)
        ax.set_xlabel(r"position $t$ (cycle)")
        style.despine(ax)
        prov(f"Figure 6 / {NAME[ds]}", ARTIFACTS_DIR / "s3_fit_profiles" / "profiles" / f"{ds}.json", "generated units seed 0 (first 25) + S3 split units", "scripts/s4_generate_units.py; scripts/s9_write_paper.py", "generation 0")
    axes[0].set_ylabel("capacity [Ah]")
    axes[0].legend(handles=[Line2D([], [], color=style.MEASURED_BUNDLE, lw=1, label="measured"), Line2D([], [], color=style.GENERATED, lw=1, label="generated")],
                   frameon=False, fontsize=6.5, loc="lower left")
    fig.tight_layout()
    fig.savefig(PAPER / "img" / "fig_res_fidelity.pdf")
    fig.savefig(RESULTS_DIR / "fig_res_fidelity.png", dpi=200)
    plt.close(fig)


def main() -> int:
    p = stage_parser(__doc__, "s9_write_paper")
    p.add_argument("--tables", nargs="*", default=["fidelity", "properties", "figure_fidelity"])
    args = p.parse_args()
    StageContext.from_args(args)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    fns = {"fidelity": table_fidelity, "properties": table_properties, "figure_fidelity": figure_fidelity, "resolution": table_resolution,
           "figure_degradation": figure_degradation}
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
