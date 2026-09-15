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
    fns = {"fidelity": table_fidelity, "properties": table_properties, "figure_fidelity": figure_fidelity}
    for t in args.tables:
        fns[t]()
    old = json.loads((RESULTS_DIR / "provenance.json").read_text()) if (RESULTS_DIR / "provenance.json").exists() else []
    keep = [x for x in old if not any(x["cell"].startswith(y["cell"].split(" / ")[0]) for y in PROV)]
    write_json(keep + PROV, RESULTS_DIR / "provenance.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
