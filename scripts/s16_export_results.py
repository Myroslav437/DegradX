#!/usr/bin/env python
"""S16 — results export: one JSON per results table under ``results/`` with the source artifact of every value, the result
figures (``results/fig_res_*.png``) and the provenance list ``results/provenance.json`` (table / figure cell -> artifact,
key, script, seeds), read from the stage artifacts of MATR, HUST and FORM (TRI_FORMATION) under ``artifacts/``. Cells without
a measurement are void, with the reason recorded.

Every table and Figures 7-8 read committed artifacts only; Figure 6 (``figure_fidelity``) also needs the measured cycle
tables and the generated units under ``data/``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


import numpy as np  # noqa: E402

from degradx import ARTIFACTS_DIR, REPO_ROOT, RESULTS_DIR  # noqa: E402
from degradx.utils.cli import stage_parser  # noqa: E402
from degradx.utils.io import write_json  # noqa: E402

PROFILES = ("MATR", "HUST", "TRI_FORMATION")
NAME = {"MATR": "MATR", "HUST": "HUST", "TRI_FORMATION": "FORM"}
STAGE = {"fit": "s09_fit_profiles", "generate": "s10_generate_units", "fidelity": "s11_fidelity", "usability": "s13_usability",
         "scores": "s14_degraded_map_test", "reference": "s15_reference_values"}
PROV: list[dict] = []
SEEDS_GEN = "generation 0,1,2; model_init 0-4; evaluation 20260915"
THIS = "scripts/s16_export_results.py"


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
    """Void reasons of one table; a void cell is marked void^a, void^b, ... in the order its reason first occurs."""

    def __init__(self):
        self.reasons: list[str] = []

    def void(self, reason: str) -> str:
        reason = reason.replace("$<$", "<").replace("<", "$<$")
        if reason not in self.reasons:
            self.reasons.append(reason)
        return f"void$^{{{chr(ord('a') + self.reasons.index(reason))}}}$"


def art(ds: str, stage: str) -> Path:
    return ARTIFACTS_DIR / STAGE[stage]


def script(ds: str, stage: str) -> str:
    return f"scripts/{STAGE[stage]}.py"


def prov(cell: str, source: Path, key: str, script_: str, seeds: str):
    PROV.append({"cell": cell, "artifact": Path(source).relative_to(REPO_ROOT).as_posix(), "key": key, "script": script_, "seeds": seeds})


def load_per_ds(stage: str, rel: str) -> dict:
    """{ds: (source path, the ds entry)} from the stage artifact of each profile."""
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
    """Table 1: per profile, the generator with per-unit offsets and correlated noise (X2 + X3), the same profile with X3
    switched off (generation seed 0), and the baseline generator (shared mappings, independent noise), with discriminative
    error, covariance agreement and the TSTR transfer ratio. FORM has no baseline profile and no transfer ratio without X3."""
    F = load_per_ds("fidelity", "tables/fidelity.json")
    RD = load_per_ds("fidelity", "tables/discriminator_readability.json")
    x3_src = ARTIFACTS_DIR / "s12_tstr_without_correlated_noise" / "tables" / "tstr_without_x3.json"
    X3 = json.loads(x3_src.read_text()) if x3_src.exists() else {}
    base_src = ARTIFACTS_DIR / "s07_fidelity_baseline" / "tables" / "fidelity.json"
    BASE = json.loads(base_src.read_text())
    res = {}
    for ds, (src, r) in F.items():
        u, t, v = r["units"], r["tstr"], dict(r["void"])
        disc = [s["discriminative_error"] for s in r["per_generation_seed"]]
        rd = RD.get(ds, (None, None))[1]
        if rd and not rd["readable"] and not v["discriminative_error"]:  # readability rule of the discriminative error
            seeds_txt = ", ".join(f"{f3(x['discriminative_error'], 2)} [{f3(x['ci_low'], 2)}, {f3(x['ci_high'], 2)}]" for x in rd["per_generation_seed"])
            v["discriminative_error"] = (f"{NAME[ds]}: 95\\% unit-bootstrap half-width above half the distance from 0.5 for "
                                         f"{sum(not x['readable'] for x in rd['per_generation_seed'])} of 3 generation seeds; values {seeds_txt}")
        cov = [s["cov_relative_frobenius"] for s in r["per_generation_seed"]]
        base = r["baseline_measured_fitting_vs_held_out"]
        bi = base["cov_relative_frobenius_interval"]
        off = r.get("x3_off_seed0") or {}
        # without X3 (generation seed 0)
        xo = X3.get(ds, {}).get("rows", {}).get("profile_without_x3_seed0")
        if xo:
            prov(f"Table 1 / {NAME[ds]} / transfer ratio without X3", x3_src, f"{ds}.rows.profile_without_x3_seed0", "scripts/s12_tstr_without_correlated_noise.py",
                 "generation 0 (X3-off set); model_init 0-4; evaluation 20260915")
        # baseline generator (shared mappings, independent noise)
        if ds in BASE:
            prov(f"Table 1 / {NAME[ds]} / baseline generator row", base_src, f"{ds}.{{per_generation_seed,tstr,baseline_measured_fitting_vs_held_out}}", "scripts/s07_fidelity_baseline.py",
                 "generation 0,1,2; model_init 0-4; evaluation 20260915")
        res[ds] = {"units": u, "discriminative_error_per_generation_seed": disc, "covariance_rel_frobenius_mean": float(np.mean(cov)),
                   "covariance_baseline": base["cov_relative_frobenius"], "covariance_baseline_interval": [bi["ci_low"], bi["ci_high"]],
                   "x3_off_seed0": {"discriminative_error": off.get("discriminative_error"), "cov_relative_frobenius": off.get("cov_relative_frobenius"),
                                    "transfer_ratio": xo},
                   "transfer_ratio": t["ratio"], "transfer_ci": [t["ci_low"], t["ci_high"]], "readings": r.get("readings"), "baseline_generator_vs_profile": r.get("baseline_generator_vs_profile"),
                   "x2_x3_shares": X3.get(ds, {}).get("shares"), "void": {**v, "transfer_ratio": t["void"]}, "source": src.relative_to(REPO_ROOT).as_posix()}
        for col in ("discriminative_error", "covariance_agreement", "x3_off", "transfer_ratio"):
            prov(f"Table 1 / {NAME[ds]} / {col}", src, ds, script(ds, "fidelity"), SEEDS_GEN)
        if ds in RD:
            prov(f"Table 1 / {NAME[ds]} / discriminative_error readability", RD[ds][0], ds, "scripts/s11b_fidelity_readability.py", "generation 0,1,2; evaluation 20260915")
    # X2's and X3's shares in transfer (paired log-ratio differences; declarations form.tstr_without_x3.shares)
    for ds in ("MATR", "HUST"):
        if X3.get(ds, {}).get("shares"):
            prov(f"Table 1 / {NAME[ds]} / X2 and X3 shares in transfer", x3_src, f"{ds}.shares", "scripts/s12_tstr_without_correlated_noise.py", "generation 0 and baseline 0-2; model_init 0-4; evaluation 20260915")
    res["readings_cross_profile"] = json.loads((ARTIFACTS_DIR / "s11_fidelity" / "tables" / "fidelity.json").read_text()).get("readings_cross_profile")
    write_json(res, RESULTS_DIR / "table1_fidelity.json")
    return res


# ---------------------------------------------------------------------------------------------------------------- Table 2
def table_properties():
    notes = Notes()
    data = {}
    for ds in PROFILES:
        src = art(ds, "fidelity") / "tables" / f"properties_{ds}.json"
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
    res = {}
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
            prov(f"Table 2 / {NAME[ds]} / {label}", src, prefix, script(ds, "fidelity"),
                 "generation 0; evaluation 20260915")
        res[label] = {ds: cells[i * 3:(i + 1) * 3] for i, ds in enumerate(data)}
    write_json({"profiles": list(data), "columns": list(sides), "rows": res}, RESULTS_DIR / "table2_properties.json")
    return res


# ---------------------------------------------------------------------------------------------------------------- Table 4
USABILITY_ROWS = [
    ("Accuracy, NRMSE of the primary model (members passing)", "primary_nrmse"),
    ("Offset term, share of Var$(y)$", "offset_term"),
    ("Spearman correlation of $y$ with RUL", "spearman_y_rul"),
    *[(f"Permutation importance, {lab}", f"permutation_importance.{c}") for c, lab in (("capacity", "capacity"), ("charge_time", "charge time"), ("mean_discharge_voltage", "mean discharge V"))],
    *[(f"Channel use (conditional importance), {lab}", f"channel_usage.A0.{c}") for c, lab in (("capacity", "capacity"), ("charge_time", "charge time"), ("mean_discharge_voltage", "mean discharge V"))],
    ("Members using every weighted channel", "channel_usage_gate"),
    ("Leakage, null channels (upper bound, flat / permuted)", "permutation_importance.null_*"),
    ("Redundant channels: $R^2$, conditional importance", "redundant_channels"),
    ("Pattern term, variance ratio to the mean term", "variance_ratio_pattern_to_mean"),
    ("Pattern term removed, NMSE increase", "term_ablation.pattern_term_removed"),
    ("Graded/sparse correlation $|r|$", "graded_sparse_abs_corr"),
]


def table_usability(kind="recency"):
    data = {}
    for ds in PROFILES:
        src = art(ds, "usability") / "tables" / f"usability_{ds}.json"
        if src.exists():
            data[ds] = (src, json.loads(src.read_text())[ds][kind])
    seeds = "generation 0; model_init 0-4 (A, B); evaluation 20260915"
    for label, key in USABILITY_ROWS:
        for ds, (src, _r) in data.items():
            prov(f"Table 4 / {NAME[ds]} / {label}", src, f"{ds}.{kind}.{key}", script(ds, "usability"), seeds)
    write_json({"weighting": kind, "values": {ds: r for ds, (src, r) in data.items()}}, RESULTS_DIR / "table4_usability.json")


# ---------------------------------------------------------------------------------------------------------------- Table 5
OPS = [("added_noise", "Added noise"), ("shift_to_start", "Mass to start"), ("shift_to_end", "Mass to end"), ("smoothing", "Smoothing"), ("permuted_fraction", "Permuted fraction")]


def table_scores(kind="recency"):
    data = load_per_ds("scores", "tables/degradation.json")
    for ds, (src, R) in data.items():
        prov(f"Table 5 / {NAME[ds]}", src, f"{ds}.{kind}.operators.<op>.<score>.registers", script(ds, "scores"), "generation 0; evaluation 20260915")
    # paired retrieval (profiles with patterns): resolution magnitude per operator
    pr = {ds: R[kind]["paired_retrieval"] for ds, (src, R) in data.items() if R[kind].get("paired_retrieval")}
    write_json({"weighting": kind, "profiles": list(data), "values": {ds: R for ds, (src, R) in data.items()}, "paired_retrieval": pr}, RESULTS_DIR / "table5_scores.json")
    return pr


# ---------------------------------------------------------------------------------------------------------------- Table 3
def table_isolation():
    """TSTR ratios by input set on the baseline profiles (MATR, HUST; S08) and on the profiles with offsets (S11)."""
    src1 = ARTIFACTS_DIR / "s08_tstr_isolation_baseline" / "tables" / "tstr_isolation.json"
    R1 = json.loads(src1.read_text())
    F = load_per_ds("fidelity", "tables/fidelity.json")
    prov("Table 3 / profiles without offsets (baseline)", src1, "{MATR,HUST}.input_sets, tests", "scripts/s08_tstr_isolation_baseline.py", SEEDS_GEN)
    for ds, (src, r) in F.items():
        prov(f"Table 3 / {NAME[ds]} / profile with offsets", src, f"{ds}.tstr_input_sets, x1_on_profile.tests", script(ds, "fidelity"), SEEDS_GEN)
    write_json({"baseline_profiles": {ds: {"input_sets": {k: {kk: vv for kk, vv in v.items() if kk != "runs"} for k, v in R1[ds]["input_sets"].items()},
                                     "tests": R1[ds]["tests"], "readings": R1[ds]["readings"]} for ds in ("MATR", "HUST")},
                "profiles": {ds: {"input_sets": {k: {kk: vv for kk, vv in v.items() if kk != "runs"} for k, v in r.get("tstr_input_sets", {}).items()},
                                     "x1_on_profile": r.get("x1_on_profile")} for ds, (src, r) in F.items()}},
               RESULTS_DIR / "table3_tstr_isolation.json")


# ---------------------------------------------------------------------------------------------------------------- Table 6
METHODS = [("integrated_gradients", "IG"), ("feature_occlusion", "Occlusion"), ("timeshap", "TimeSHAP")]


def table_reference(kind="recency"):
    data = load_per_ds("reference", "tables/reference_values.json")
    seeds = "generation 0; model_init 0 (A), ensemble A/B 0-4; attribution_sampling 0,1,2 (TimeSHAP), 0 (floor); evaluation 20260915"
    retr, src_of = {}, {}
    for ds, (src, Rd) in data.items():
        src_of[ds] = src
        r = Rd["weightings"][kind]
        sc = r["scores"]
        for key, label in METHODS:
            t, f = sc[f"trained/{key}"], sc[f"reference/{key}"]
            prov(f"Table 6 / {NAME[ds]} / {label}", src, f"{ds}.weightings.{kind}.scores.{{trained,reference}}/{key}", script(ds, "reference"), seeds)
            if "retrieval" in t or "retrieval" in f:
                retr.setdefault(ds, {})[label] = {"trained": t.get("retrieval"), "reference": f.get("retrieval")}
        prov(f"Table 6 / {NAME[ds]} / ensemble range", src, f"{ds}.weightings.{kind}.identifiability_floor", script(ds, "reference"), seeds)
        if "secondary_average_event" in r:
            prov(f"Table 6 / {NAME[ds]} / TimeSHAP average event", src, f"{ds}.weightings.{kind}.secondary_average_event", script(ds, "reference"), seeds)
    # trained-model sparse-set scores are read only if the pattern-term ablation of the primary model has a 95 % CI above 0
    # (declarations form.readings.sparse_set_trained); otherwise they are void
    for ds in retr:
        usrc = art(ds, "usability") / "tables" / f"usability_{ds}.json"
        prov(f"Table 6 / {NAME[ds]} / paired retrieval (note)", src_of[ds], f"{ds}.weightings.{kind}.scores.*.retrieval", script(ds, "reference"), seeds)
        prov(f"Table 6 / {NAME[ds]} / trained retrieval void reading", usrc, f"{ds}.{kind}.term_ablation.pattern_term_removed", script(ds, "usability"), seeds)
    write_json({"weighting_in_table": kind, "values": {ds: Rd for ds, (src, Rd) in data.items()}, "paired_retrieval": retr}, RESULTS_DIR / "table6_reference_values.json")


# ---------------------------------------------------------------------------------------------------------------- profile facts
def profile_facts():
    """Numbers reported about the FORM profile: ingestion, audit, offset pre-screen, pattern-enable rule and mechanism
    readings (S02, S04, S10), each with its source."""
    w1 = ARTIFACTS_DIR / "s02_ingest_form" / "tables" / "ingest_summary.json"
    w2 = ARTIFACTS_DIR / "s04_audit_form" / "tables" / "audit_summary.json"
    w4 = ARTIFACTS_DIR / "s10_generate_units" / "tables" / "summary.json"
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
        prov(f"Section 3.4 / FORM / {key}", src_, key, {w1: "scripts/s02c_ingest_form.py", w2: "scripts/s04_audit_form.py", w4: "scripts/s10_generate_units.py"}[src_],
             "split 20260915; generation 0,1,2")
    write_json(out, RESULTS_DIR / "profile_facts.json")
    return out


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
    profs = [d for d in PROFILES if (art(d, "fidelity") / "tables" / f"properties_{d}.json").exists()]
    style.apply()
    fig, axes = plt.subplots(1, len(profs), figsize=(style.TEXTWIDTH_IN, 2.0), squeeze=False)
    for ax, ds in zip(axes[0], profs):
        q_nom = C.q_nom_of(ds)
        prof = C.fitted_profile(ds)
        split = C.fitted_split(ds)
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
        prov(f"Figure 6 / {NAME[ds]}", C.profiles_dir(ds) / "profiles" / f"{ds}.json", "generated units seed 0 (first 25) + the split units",
             script(ds, "generate") + f"; {THIS}", "generation 0")
    axes[0][0].set_ylabel("capacity [Ah]")
    axes[0][0].legend(handles=[Line2D([], [], color=style.MEASURED_BUNDLE, lw=1, label="measured"), Line2D([], [], color=style.GENERATED, lw=1, label="generated")],
                      frameon=False, fontsize=6.5, loc="lower left", ncol=2, handlelength=1.5, columnspacing=1.0)
    fig.tight_layout(w_pad=2.2)
    fig.savefig(RESULTS_DIR / "fig_res_fidelity.png", dpi=200)
    plt.close(fig)


LS = {"MATR": "-", "HUST": "--", "TRI_FORMATION": ":"}


def figure_degradation(kind="recency"):
    """Figure 7: rank agreement and the temporal profile error against each operator's magnitude, per profile, with each
    profile's chance level."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from degradx.viz import style

    data = load_per_ds("scores", "tables/degradation.json")
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
    fig.savefig(RESULTS_DIR / "fig_res_degradation.png", dpi=200)
    plt.close(fig)
    for ds, (src, _R) in data.items():
        prov(f"Figure 7 / {NAME[ds]}", src, f"{ds}.{kind}.operators.<op>.{{rank,temporal}}, chance", script(ds, "scores") + f"; {THIS}",
             "generation 0; evaluation 20260915")


def figure_floor(kind="recency"):
    """Figure 8: for each method, the primary trained model's score and the ten-member ensemble range, against the exact
    attribution of the reference model, for rank agreement, channel allocation error and temporal profile error."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from degradx.viz import style

    data = load_per_ds("reference", "tables/reference_values.json")
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
    fig.savefig(RESULTS_DIR / "fig_res_floor.png", dpi=200)
    plt.close(fig)
    for ds, (src, _R) in data.items():
        prov(f"Figure 8 / {NAME[ds]}", src, f"{ds}.weightings.{kind}.{{scores,identifiability_floor}}", script(ds, "reference") + f"; {THIS}",
             "generation 0; model_init A/B 0-4; attribution_sampling 0,1,2; evaluation 20260915")


def main() -> int:
    p = stage_parser(__doc__, "s16_export_results")
    p.add_argument("--tables", nargs="*", default=["facts", "fidelity", "properties", "usability", "scores", "isolation", "reference", "figure_fidelity", "figure_degradation",
                                                    "figure_floor"])
    p.add_argument("--no-provenance", action="store_true")
    args = p.parse_args()
    if args.dry_run:
        print(f"plan: results tables/figures {args.tables}")
        return 0
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    fns = {"facts": profile_facts, "fidelity": table_fidelity, "properties": table_properties, "usability": table_usability, "scores": table_scores, "isolation": table_isolation,
           "reference": table_reference, "figure_fidelity": figure_fidelity, "figure_degradation": figure_degradation, "figure_floor": figure_floor}
    for t in args.tables:
        fns[t]()
        print(f"[s16] {t} done", flush=True)
    if args.no_provenance:
        return 0
    # entries of tables / figures not regenerated in this run are kept
    old = json.loads((RESULTS_DIR / "provenance.json").read_text()) if (RESULTS_DIR / "provenance.json").exists() else []
    keep = [x for x in old if not any(x["cell"].split(" / ")[0] == y["cell"].split(" / ")[0] for y in PROV)]
    write_json(keep + PROV, RESULTS_DIR / "provenance.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
