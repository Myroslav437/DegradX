"""S3 figures (per dataset): capacity + EOL sheet, family fits, CV errors, theta, mappings, residual ACF, patterns, sweep,
lengths."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from degradx.fitting.families import FAMILIES  # noqa: E402
from degradx.viz import style  # noqa: E402

LABEL = {"MATR": "MATR", "HUST": "HUST", "NASA_PCoE": "NASA PCoE"}
FAM_LABEL = {"power_law": "power law", "two_term_exponential": "two-term exp.", "rollover": "rollover"}
LS = {"power_law": ":", "two_term_exponential": "--", "rollover": "-"}


def _sample(units, n):
    reach = [u for u in units if u.reaches]
    pool = sorted(reach or units, key=lambda u: u.state.T or len(u.q))
    idx = np.linspace(0, len(pool) - 1, min(n, len(pool))).round().astype(int)
    return [pool[i] for i in idx]


def capacity_sheet(ds, units, q_nom, rho):
    style.apply()
    sel = _sample(units, 6)
    fig, axes = plt.subplots(2, 3, figsize=(style.TEXTWIDTH_IN, 3.6), squeeze=False)
    for ax, u in zip(axes.ravel(), sel):
        ax.plot(u.positions, u.q, color=style.MEASURED_BUNDLE, lw=style.LW_THIN, label="raw")
        ax.plot(u.positions, u.state.q_smooth, color="black", lw=style.LW_MAIN, label="Savitzky–Golay")
        ax.axhline(rho * q_nom, color=style.REFERENCE, lw=style.LW_THIN, ls="--")
        ax.axvline(u.fit_start, color=style.GREY, lw=style.LW_THIN, ls=":")
        if u.state.T:
            ax.axvline(u.state.T, color="black", lw=style.LW_THIN, ls="--")
        ax.set_title(f"{u.cell_id.split('_', 1)[1]}: $t_1$={u.fit_start}, T={u.state.T}" + (" (record end)" if u.state.T_from_record_end else ""), fontsize=7.5)
        ax.set_xlabel("position (cycle)")
        ax.set_ylabel("capacity [Ah]")
        style.despine(ax)
    axes[0][0].legend(frameon=False, fontsize=6)
    fig.suptitle(f"{LABEL[ds]}: sampled units (dashed horizontal: ρ·q_nom; dotted: $t_1$; dashed vertical: EOL)", fontsize=8)
    fig.tight_layout()
    return fig


def family_fits(ds, units, family_selected):
    style.apply()
    sel = _sample(units, 3)
    fig, axes = plt.subplots(2, len(sel), figsize=(style.TEXTWIDTH_IN, 3.4), squeeze=False, gridspec_kw={"height_ratios": [2, 1]})
    for j, u in enumerate(sel):
        s = slice(u.fit_start - 1, u.fit_end)
        pos, q = u.positions[s], u.q[s]
        axes[0][j].plot(pos, q, color=style.MEASURED_BUNDLE, lw=style.LW_THIN)
        for name in FAMILIES:
            fit = u.fits[name].params
            yhat = FAMILIES[name](fit, pos) * u.state.q1
            axes[0][j].plot(pos, yhat, color="black", ls=LS[name], lw=style.LW_MAIN if name == family_selected else style.LW_THIN,
                            label=f"{FAM_LABEL[name]} (RMSE {u.fits[name].rmse * u.state.q1 * 1000:.1f} mAh)")
            axes[1][j].plot(pos, (q - yhat) * 1000, color="black" if name == family_selected else style.MEASURED, ls=LS[name], lw=style.LW_THIN)
        axes[0][j].set_title(u.cell_id.split("_", 1)[1], fontsize=8)
        axes[0][j].legend(frameon=False, fontsize=5.5)
        axes[1][j].axhline(0, color=style.REFERENCE, lw=style.LW_THIN)
        axes[1][j].set_xlabel("position (cycle)")
        for i in range(2):
            style.despine(axes[i][j])
    axes[0][0].set_ylabel("capacity [Ah]")
    axes[1][0].set_ylabel("residual [mAh]")
    fig.suptitle(f"{LABEL[ds]}: candidate families fitted from $t_1$ to EOL (bold: selected)", fontsize=8)
    fig.tight_layout()
    return fig


def cv_errors(ds, units_df, sel):
    style.apply()
    fig, ax = plt.subplots(figsize=(3.2, 2.2))
    r = units_df[units_df["reaches_eol"]]
    data = [r[f"cv_rmse_{n}"].dropna() * 100 for n in FAMILIES]
    ax.boxplot(data, tick_labels=[FAM_LABEL[n] for n in FAMILIES], widths=0.5, showfliers=False,
               medianprops={"color": "black"}, boxprops={"color": style.MEASURED}, whiskerprops={"color": style.MEASURED}, capprops={"color": style.MEASURED})
    for i, d in enumerate(data, start=1):
        ax.scatter(np.full(len(d), i) + np.linspace(-0.15, 0.15, len(d)), d, s=3, color=style.MEASURED_BUNDLE, zorder=0)
    ax.set_ylabel("CV RMSE [% of $q_1$]")
    ax.set_yscale("log")
    ax.set_title(f"{LABEL[ds]}: selected {FAM_LABEL[sel['selected']]} ({sel['units_in_selection']} units)", fontsize=8)
    style.despine(ax)
    fig.tight_layout()
    return fig


def theta_distributions(ds, profile):
    style.apply()
    e = profile["estimated_from_data"]["E1_theta_distribution"]
    P = np.array([p["family_params"] for p in e["per_unit"]])
    names = e["param_names"]
    fig, axes = plt.subplots(1, len(names) + 1, figsize=(style.TEXTWIDTH_IN, 1.9), squeeze=False)
    for j, nm in enumerate(names):
        axes[0][j].hist(P[:, j], bins=15, color=style.MEASURED)
        axes[0][j].set_xlabel(nm)
        style.despine(axes[0][j])
    axes[0][-1].hist([p["q1"] for p in e["per_unit"]], bins=15, color=style.MEASURED)
    axes[0][-1].set_xlabel("$q_1$ [Ah]")
    style.despine(axes[0][-1])
    axes[0][0].set_ylabel("units")
    fig.suptitle(f"{LABEL[ds]}: θ of {FAM_LABEL[e['family']]} over {e['n_units']} units (n in thousands of cycles)", fontsize=8)
    fig.tight_layout()
    return fig


def mappings(ds, units, maps, channels):
    style.apply()
    chans = [c for c in channels if c != "capacity"]
    fig, axes = plt.subplots(1, len(chans), figsize=(style.TEXTWIDTH_IN, 2.1), squeeze=False)
    rng = np.random.default_rng(0)  # illustration subsample only
    for ax, c in zip(axes[0], chans):
        z = np.concatenate([u.state.z[u.fit_start - 1:u.fit_end] for u in units])
        x = np.concatenate([u.channels[c][u.fit_start - 1:u.fit_end] for u in units])
        ok = np.isfinite(z) & np.isfinite(x)
        idx = rng.choice(np.flatnonzero(ok), size=min(4000, ok.sum()), replace=False)
        ax.scatter(z[idx], x[idx], s=1, color=style.MEASURED_BUNDLE, rasterized=True)
        zz = np.linspace(0, 1, 101)
        ax.plot(zz, maps[c](zz), color="black", lw=style.LW_MAIN)
        lo, hi = np.nanquantile(x[ok], [0.005, 0.995])
        ax.set_ylim(lo - 0.1 * (hi - lo), hi + 0.1 * (hi - lo))
        ax.set_xlim(-0.1, 1.1)
        ax.set_xlabel("degradation state $z$")
        ax.set_title(c.replace("_", " "), fontsize=8)
        style.despine(ax)
    fig.suptitle(f"{LABEL[ds]}: fitted mappings $\\varphi_c$ (black) over measured readings (grey, subsample)", fontsize=8)
    fig.tight_layout()
    return fig


def residual_acf(ds, residuals, masks, channels, noise):
    from statsmodels.tsa.stattools import acf

    style.apply()
    fig, axes = plt.subplots(1, len(channels), figsize=(style.TEXTWIDTH_IN, 1.9), squeeze=False)
    for ax, c in zip(axes[0], channels):
        acfs = []
        for cid, r in residuals[c].items():
            rr = np.where(masks[cid], np.nan, r)
            if np.isfinite(rr).sum() > 40:
                acfs.append(acf(rr - np.nanmean(rr), nlags=20, missing="conservative", fft=False))
        a = np.nanmedian(np.array(acfs), axis=0)
        ax.bar(np.arange(1, 21), a[1:], color=style.MEASURED, width=0.7)
        ax.plot(np.arange(1, 21), noise[c]["phi"] ** np.arange(1, 21), color="black", lw=style.LW_THIN, ls="--")
        ax.set_ylim(-0.2, 1.0)
        ax.set_xlabel("lag [positions]")
        ax.set_title(f"{c.replace('_', ' ')}\nvar {noise[c]['variance']:.3g}", fontsize=7)
        style.despine(ax)
    axes[0][0].set_ylabel("median ACF over units")
    fig.suptitle(f"{LABEL[ds]}: residual autocorrelation (bars) and fitted AR(1) (dashed)", fontsize=8)
    fig.tight_layout()
    return fig


def pattern_traces(ds, units, residuals, patterns_df, k, scales):
    style.apply()
    cand = sorted(units, key=lambda u: (-(patterns_df["cell_id"] == u.cell_id).sum() if len(patterns_df) else 0, u.cell_id))[:3]
    fig, axes = plt.subplots(len(cand), 1, figsize=(style.TEXTWIDTH_IN, 1.4 * len(cand)), squeeze=False)
    for ax, u in zip(axes[:, 0], cand):
        r = residuals["capacity"][u.cell_id] * 1000
        pos = u.positions[u.fit_start - 1:u.fit_end]
        ax.plot(pos, r, color=style.MEASURED, lw=style.LW_THIN)
        s = scales[u.cell_id] * 1000
        for sg in (1, -1):
            ax.axhline(sg * k * s, color="black", lw=style.LW_THIN, ls="--")
        pu = patterns_df[patterns_df["cell_id"] == u.cell_id] if len(patterns_df) else []
        for _, p in (pu.iterrows() if len(pu) else []):
            st = int(p["extremum"] - (p["duration"] // 2))
            sl = (pos >= st) & (pos < st + p["duration"])
            ax.plot(pos[sl], r[sl], color="black", lw=1.6)
        ax.set_ylabel("residual [mAh]")
        ax.set_title(f"{u.cell_id.split('_', 1)[1]}: {len(pu)} detected", fontsize=7.5)
        style.despine(ax)
    axes[-1][0].set_xlabel("position (cycle)")
    fig.suptitle(f"{LABEL[ds]}: capacity residual of the selected family, ±{k}× residual scale, detected runs bold", fontsize=8)
    fig.tight_layout()
    return fig


def sweep(ds, sweep_df, profile_patterns, k0):
    style.apply()
    fig, ax = plt.subplots(figsize=(3.2, 2.2))
    g = sweep_df.groupby("k").agg(pos=("positive", "sum"), neg=("negative", "sum"), n=("positions", "sum"))
    ax.plot(g.index, g["pos"] / g["n"] * 100, color="black", marker="o", ms=3, label="positive (measured)")
    ax.plot(g.index, g["neg"] / g["n"] * 100, color=style.MEASURED, marker="s", ms=3, label="negative (measured)")
    nr = profile_patterns["positive"]["noise_only_rate_per_100"]
    ax.scatter([k0], [nr], marker="x", color="black", zorder=5, label=f"noise-only at k={k0}")
    ax.scatter([k0], [2 * nr], marker="+", color="black", zorder=5, label="enable threshold (2×)")
    ax.axvline(k0, color=style.REFERENCE, lw=style.LW_THIN)
    ax.set_yscale("symlog", linthresh=0.01)
    ax.set_xlabel("multiple k of residual scale")
    ax.set_ylabel("events per 100 positions")
    ax.legend(frameon=False, fontsize=5.5)
    en = ", ".join(t for t, v in profile_patterns.items() if v["enabled"]) or "none"
    ax.set_title(f"{LABEL[ds]}: enabled types: {en}", fontsize=8)
    style.despine(ax)
    fig.tight_layout()
    return fig


def lengths(ds, T):
    style.apply()
    fig, ax = plt.subplots(figsize=(3.2, 2.0))
    ax.hist(T, bins=15, color=style.MEASURED)
    ax.set_xlabel("EOL position T [cycles]")
    ax.set_ylabel("units")
    ax.set_title(f"{LABEL[ds]}: {len(T)} fitting units reaching EOL", fontsize=8)
    style.despine(ax)
    fig.tight_layout()
    return fig
