"""S2 summaries and figures: monotonicity, regeneration, lengths, EOL attainment, detection sweep."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from degradx.viz import style  # noqa: E402

LABEL = {"MATR": "MATR", "HUST": "HUST", "NASA_PCoE": "NASA PCoE"}


def _q(x, qs=(0.0, 0.25, 0.5, 0.75, 1.0)):
    x = pd.Series(x).dropna()
    return {f"q{int(q * 100)}": float(x.quantile(q)) for q in qs} if len(x) else {}


def summarise(units: pd.DataFrame, patterns: pd.DataFrame, dd: dict) -> dict:
    rho0 = float(dd["eol"]["rho"]["value"])
    k0, m0 = float(dd["pattern_detection"]["multiple_k"]["value"]), int(dd["pattern_detection"]["min_run_length"]["value"])
    out: dict = {"datasets": {}, "attainment_rows": [], "sweep_rows": []}
    for ds, u in units.groupby("dataset", sort=False):
        ok = u[~u["too_short"].astype(bool)]
        s: dict = {"units": int(len(u)), "too_short_after_cleaning": int(u["too_short"].sum()),
                   "cycles_dropped_by_cleaning": int(u["n_dropped_by_cleaning"].sum()),
                   "units_with_dropped_cycles": int((u["n_dropped_by_cleaning"] > 0).sum())}
        s["guard_excluded_r2_declared_rho"] = int(ok["excluded_by_guard"].sum())
        s["reach_eol_r2_declared_rho"] = int(ok["T"].notna().sum())
        s["monotone_within_tolerance"] = {"n": int(ok["monotone_within_tol"].sum()), "of": int(len(ok)),
                                          "fraction": float(ok["monotone_within_tol"].mean()) if len(ok) else None}
        s["q1_material_difference"] = {"n": int(ok["q1_material_diff"].sum()), "of": int(len(ok))}
        s["q1_minus_first_mAh"] = _q((ok["q1"] - ok["q1_first"]) * 1000)
        s["length_stored_cycles"] = _q(u["n_stored"])
        s["length_kept_cycles"] = _q(ok["n_kept"])
        s["T_r2_declared_rho"] = _q(ok["T"])
        s["best_family_in_sample"] = ok["best_family_in_sample"].value_counts().to_dict()
        s["residual_scale_mAh"] = _q(ok["residual_scale_Ah"] * 1000)
        fit_len = ok["fit_end"] - ok["fit_start"] + 1
        positions = float(fit_len.sum())
        pats = patterns[patterns["dataset"] == ds] if len(patterns) else pd.DataFrame(columns=["sign", "amplitude", "duration", "cell_id"])
        for sign, name in ((1, "positive_regeneration"), (-1, "negative_dip")):
            p = pats[pats["sign"] == sign]
            per_unit = ok[f"n_{'pos' if sign > 0 else 'neg'}_k{k0}_m{m0}"] / fit_len * 100
            s[name] = {"events": int(len(p)), "units_with_event": int((ok[f"n_{'pos' if sign > 0 else 'neg'}_k{k0}_m{m0}"] > 0).sum()),
                       "pooled_rate_per_100_cycles": float(len(p) / positions * 100) if positions else None,
                       "per_unit_rate_per_100_cycles": _q(per_unit), "amplitude_mAh": _q(p["amplitude"] * 1000),
                       "duration_positions": _q(p["duration"])}
        out["datasets"][ds] = s
        for definition in ("r2", "r1"):
            for rho in dd["eol"]["rho_sensitivity_grid"]["value"]:
                tcol, gcol = f"T_{definition}_rho{rho:.2f}", f"guard_{definition}_rho{rho:.2f}"
                n_eval = int(len(ok))
                n_guard = int(ok[gcol].sum())
                n_reach = int(ok[tcol].notna().sum())
                out["attainment_rows"].append({"dataset": ds, "definition": definition, "rho": rho, "units_audited": n_eval,
                                               "excluded_by_guard": n_guard, "reach_threshold": n_reach,
                                               "fraction_reach": n_reach / n_eval if n_eval else None})
        for kk in dd["pattern_detection"]["sweep"]["multiple_k"]:
            for mm in dd["pattern_detection"]["sweep"]["min_run_length"]:
                npos, nneg = ok[f"n_pos_k{kk}_m{mm}"], ok[f"n_neg_k{kk}_m{mm}"]
                out["sweep_rows"].append({"dataset": ds, "k": kk, "m": mm, "positive_events": int(npos.sum()), "negative_events": int(nneg.sum()),
                                          "units_with_positive": int((npos > 0).sum()), "units_with_negative": int((nneg > 0).sum()),
                                          "positive_rate_per_100_cycles": float(npos.sum() / positions * 100) if positions else None,
                                          "negative_rate_per_100_cycles": float(nneg.sum() / positions * 100) if positions else None})
    return out


def monotonicity(units: pd.DataFrame, tol: float):
    style.apply()
    ds_list = list(units["dataset"].unique())
    fig, axes = plt.subplots(1, len(ds_list), figsize=(style.TEXTWIDTH_IN, 2.0), squeeze=False)
    for ax, ds in zip(axes[0], ds_list):
        u = units[(units["dataset"] == ds) & ~units["too_short"].astype(bool)]
        v = u["monotone_violation_Ah"] / u["q1"] * 100
        ax.hist(v.clip(upper=10), bins=40, color=style.MEASURED)
        ax.axvline(tol * 100, color="black", lw=style.LW_THIN, ls="--")
        ax.set_title(f"{LABEL[ds]}: {u['monotone_within_tol'].mean():.0%} within {tol:.0%}")
        ax.set_xlabel("largest rise above running min [% of $q_1$]")
        style.despine(ax)
    axes[0][0].set_ylabel("units")
    fig.tight_layout()
    return fig


def eol_attainment(rows: pd.DataFrame):
    style.apply()
    ds_list = list(rows["dataset"].unique())
    fig, axes = plt.subplots(1, len(ds_list), figsize=(style.TEXTWIDTH_IN, 2.1), squeeze=False, sharey=True)
    for ax, ds in zip(axes[0], ds_list):
        r = rows[rows["dataset"] == ds]
        for definition, ls, mk, lab in (("r2", "-", "o", r"$\rho$ of nominal (r2)"), ("r1", "--", "s", r"$\rho$ of first-position (r1)")):
            rr = r[r["definition"] == definition]
            ax.plot(rr["rho"], rr["fraction_reach"], ls=ls, marker=mk, ms=3.5, color="black" if definition == "r2" else style.MEASURED, label=lab)
        ax.set_title(f"{LABEL[ds]} ({int(r['units_audited'].iloc[0])} units)")
        ax.set_xlabel(r"EOL fraction $\rho$")
        ax.set_ylim(-0.03, 1.03)
        style.despine(ax)
    axes[0][0].set_ylabel("fraction of units reaching EOL")
    axes[0][0].legend(frameon=False, loc="lower right")
    fig.tight_layout()
    return fig


def lengths(units: pd.DataFrame):
    style.apply()
    ds_list = list(units["dataset"].unique())
    fig, axes = plt.subplots(1, len(ds_list), figsize=(style.TEXTWIDTH_IN, 2.0), squeeze=False)
    for ax, ds in zip(axes[0], ds_list):
        u = units[(units["dataset"] == ds) & ~units["too_short"].astype(bool)]
        bins = np.linspace(0, max(u["n_kept"].max(), 1), 25)
        ax.hist(u["n_kept"], bins=bins, color=style.FILL, label="cycles kept")
        ax.hist(u["T"].dropna(), bins=bins, histtype="step", color="black", lw=style.LW_MAIN, label=r"$T$ (units reaching EOL)")
        ax.set_title(LABEL[ds])
        ax.set_xlabel("positions (cycles)")
        style.despine(ax)
    axes[0][0].set_ylabel("units")
    axes[0][0].legend(frameon=False)
    fig.tight_layout()
    return fig


def regeneration(units: pd.DataFrame, patterns: pd.DataFrame, k0: float, m0: int):
    style.apply()
    ds_list = list(units["dataset"].unique())
    fig, axes = plt.subplots(3, len(ds_list), figsize=(style.TEXTWIDTH_IN, 4.8), squeeze=False)
    for j, ds in enumerate(ds_list):
        u = units[(units["dataset"] == ds) & ~units["too_short"].astype(bool)]
        p = patterns[patterns["dataset"] == ds] if len(patterns) else pd.DataFrame(columns=["sign", "amplitude", "duration"])
        rate = u[f"n_pos_k{k0}_m{m0}"] / (u["fit_end"] - u["fit_start"] + 1) * 100
        axes[0][j].hist(rate, bins=20, color=style.MEASURED)
        axes[0][j].set_xlabel("positive events per 100 cycles")
        axes[0][j].set_title(f"{LABEL[ds]} (k={k0}, m={m0})")
        for sign, col, lab in ((1, "black", "positive (regeneration)"), (-1, style.MEASURED, "negative")):
            a = p[p["sign"] == sign]["amplitude"] * 1000
            if len(a):
                axes[1][j].hist(a, bins=30, color=col, alpha=0.8, label=lab)
                axes[2][j].hist(p[p["sign"] == sign]["duration"], bins=np.arange(1.5, 25.5, 1), color=col, alpha=0.8, label=lab)
        axes[1][j].set_xlabel("signed amplitude [mAh]")
        axes[2][j].set_xlabel("duration [positions]")
        for i in range(3):
            style.despine(axes[i][j])
    axes[0][0].set_ylabel("units")
    axes[1][0].set_ylabel("events")
    axes[2][0].set_ylabel("events")
    axes[1][0].legend(frameon=False)
    fig.tight_layout()
    return fig


def residual_examples(units: pd.DataFrame, traces: dict, k0: float, m0: int, per_dataset: int = 2):
    from degradx.fitting.patterns import detect

    style.apply()
    ds_list = list(traces)
    fig, axes = plt.subplots(len(ds_list), per_dataset, figsize=(style.TEXTWIDTH_IN, 1.6 * len(ds_list)), squeeze=False)
    for i, ds in enumerate(ds_list):
        u = units[(units["dataset"] == ds) & ~units["too_short"].astype(bool)].copy()
        u["n_pos"] = u[f"n_pos_k{k0}_m{m0}"]
        # deterministic example choice: the unit with most positive events and the median-length unit
        picks = [u.sort_values(["n_pos", "cell_id"], ascending=[False, True])["cell_id"].iloc[0],
                 u.iloc[(u["n_kept"] - u["n_kept"].median()).abs().argsort()]["cell_id"].iloc[0]]
        for j, cid in enumerate(picks[:per_dataset]):
            tr = traces[ds][cid]
            r = tr["residual"] * 1000
            pats, s = detect(tr["residual"], k0, m0, max_duration=11)  # declared smoothing window (D16)
            ax = axes[i][j]
            ax.plot(tr["position"], r, color=style.MEASURED, lw=style.LW_THIN)
            for sgn in (1, -1):
                ax.axhline(sgn * k0 * s * 1000, color="black", lw=style.LW_THIN, ls="--")
            for p in pats:
                sl = slice(p.start - 1, p.end)
                ax.plot(tr["position"][sl], r[sl], color="black", lw=1.6)
            ax.set_title(f"{LABEL[ds]} {cid.split('_', 1)[1]}: {sum(p.sign > 0 for p in pats)} pos / {sum(p.sign < 0 for p in pats)} neg", fontsize=7.5)
            ax.set_xlabel("position (cycle)")
            ax.set_ylabel("residual [mAh]")
            style.despine(ax)
    fig.text(0.99, 0.005, f"dashed: ±{k0}× residual scale; bold: detected runs ({m0}-11 positions); fit from $q_1$ to EOL", ha="right", va="bottom", fontsize=7, color=style.GREY)
    fig.tight_layout()
    return fig


def detection_sweep(rows: pd.DataFrame, k0: float):
    style.apply()
    ds_list = list(rows["dataset"].unique())
    fig, axes = plt.subplots(1, len(ds_list), figsize=(style.TEXTWIDTH_IN, 2.0), squeeze=False)
    for ax, ds in zip(axes[0], ds_list):
        r = rows[rows["dataset"] == ds]
        for m, ls in ((2, "-"), (3, "--")):
            rr = r[r["m"] == m]
            ax.plot(rr["k"], rr["positive_rate_per_100_cycles"], ls=ls, color="black", marker="o", ms=3, label=f"positive, m={m}")
            ax.plot(rr["k"], rr["negative_rate_per_100_cycles"], ls=ls, color=style.MEASURED, marker="s", ms=3, label=f"negative, m={m}")
        ax.axvline(k0, color=style.REFERENCE, lw=style.LW_THIN)
        ax.set_yscale("symlog", linthresh=0.01)
        ax.set_title(LABEL[ds])
        ax.set_xlabel("multiple k of residual scale")
        style.despine(ax)
    axes[0][0].set_ylabel("events per 100 cycles")
    axes[0][0].legend(frameon=False, fontsize=6)
    fig.tight_layout()
    return fig


def all_figures(units, patterns, traces, dd, cfg) -> dict:
    k0, m0 = float(dd["pattern_detection"]["multiple_k"]["value"]), int(dd["pattern_detection"]["min_run_length"]["value"])
    summ = summarise(units, patterns, dd)
    return {
        "monotonicity_histogram": monotonicity(units, float(dd["audit"]["monotonicity_tolerance"]["value"])),
        "eol_attainment": eol_attainment(pd.DataFrame(summ["attainment_rows"])),
        "length_distribution": lengths(units),
        "regeneration_distributions": regeneration(units, patterns, k0, m0),
        "residual_traces_with_threshold": residual_examples(units, traces, k0, m0),
        "detection_sweep": detection_sweep(pd.DataFrame(summ["sweep_rows"]), k0),
    }
