"""V3 figures (brief "DegradX v2", X2/X3): channel mappings with per-unit offsets, residual variance and lag-1 before and
after the offsets, residual cross-channel correlation before and after the offsets."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from degradx.viz import style  # noqa: E402

LABEL = {"MATR": "MATR", "HUST": "HUST", "ISU_ILCC": "ISU-ILCC"}
CH = {"capacity": "capacity", "charge_time": "charge time", "mean_discharge_voltage": "mean discharge V", "internal_resistance": "IR",
      "temperature_mean": "temperature"}


def offsets_mappings(ds, units, mappings, mappings_r2, delta, channels, n_units: int = 6):
    """Per non-capacity channel: measured (z, x) of a few units, the r2 shared mapping, the backfitted mapping and the
    unit curves phi(z) + delta_i; right column: the distribution of offsets over fitting units."""
    style.apply()
    chans = [c for c in channels if c != "capacity"]
    fig, axes = plt.subplots(len(chans), 2, figsize=(style.TEXTWIDTH_IN, 1.9 * len(chans)), squeeze=False,
                             gridspec_kw={"width_ratios": [3, 1]})
    reach = sorted([u for u in units if u.reaches], key=lambda u: u.state.T)
    pick = [reach[i] for i in np.linspace(0, len(reach) - 1, min(n_units, len(reach))).round().astype(int)]
    zz = np.linspace(0, 1, 201)
    for r, c in enumerate(chans):
        ax = axes[r][0]
        for k, u in enumerate(pick):
            sl = slice(u.fit_start - 1, u.fit_end)
            col = plt.cm.viridis(k / max(1, len(pick) - 1))
            ax.plot(u.state.z[sl], u.channels[c][sl], ".", ms=0.8, color=col, alpha=0.35)
            ax.plot(zz, mappings[c](zz) + delta[u.cell_id][c], color=col, lw=style.LW_THIN)
        ax.plot(zz, mappings_r2[c](zz), color="black", lw=style.LW_MAIN, ls="--", label="r2 shared mapping")
        ax.plot(zz, mappings[c](zz), color="black", lw=style.LW_MAIN, label="backfitted mapping (median unit)")
        ax.set_xlabel("degradation state z")
        ax.set_ylabel(CH.get(c, c))
        style.despine(ax)
        d = np.array([delta[i][c] for i in delta])
        axes[r][1].hist(d, bins=25, color=style.MEASURED_BUNDLE)
        axes[r][1].set_xlabel(f"offset δ ({CH.get(c, c)})")
        style.despine(axes[r][1])
    axes[0][0].legend(frameon=False, fontsize=6)
    fig.suptitle(f"{LABEL.get(ds, ds)}: per-unit offsets (coloured: six units spanning the range of T, curves φ(z) + δ_i)", fontsize=8)
    fig.tight_layout()
    return fig


def residual_before_after(ds, before_after):
    style.apply()
    chans = list(before_after)
    fig, axes = plt.subplots(1, 2, figsize=(style.TEXTWIDTH_IN, 2.2))
    x = np.arange(len(chans))
    rv = [before_after[c]["after_offsets"]["variance"] / before_after[c]["before_r2"]["variance"] for c in chans]
    axes[0].bar(x, rv, color=style.MEASURED_BUNDLE)
    axes[0].axhline(1.0, color=style.REFERENCE, lw=style.LW_THIN, ls="--")
    axes[0].set_xticks(x, [CH.get(c, c) for c in chans], rotation=20, fontsize=6.5)
    axes[0].set_ylabel("residual variance, after / before")
    b = [before_after[c]["before_r2"]["phi"] for c in chans]
    a = [before_after[c]["after_offsets"]["phi"] for c in chans]
    axes[1].bar(x - 0.18, b, width=0.36, color=style.GREY, label="before (r2)")
    axes[1].bar(x + 0.18, a, width=0.36, color="black", label="after offsets")
    axes[1].set_xticks(x, [CH.get(c, c) for c in chans], rotation=20, fontsize=6.5)
    axes[1].set_ylabel("residual lag-1 autocorrelation")
    axes[1].legend(frameon=False, fontsize=6)
    for ax in axes:
        style.despine(ax)
    fig.suptitle(f"{LABEL.get(ds, ds)}: residuals before and after per-unit offsets (fitting split)", fontsize=8)
    fig.tight_layout()
    return fig


def correlation_before_after(ds, channels, corr_r2, corr_v2):
    style.apply()
    fig, axes = plt.subplots(1, 2, figsize=(style.TEXTWIDTH_IN * 0.8, 2.6))
    labels = [CH.get(c, c) for c in channels]
    for ax, M, title in ((axes[0], np.asarray(corr_r2), "r2 residuals"), (axes[1], np.asarray(corr_v2), "after offsets (X3 target)")):
        im = ax.imshow(M, vmin=-1, vmax=1, cmap="RdBu_r")
        ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right", fontsize=6)
        ax.set_yticks(range(len(labels)), labels, fontsize=6)
        for i in range(len(labels)):
            for j in range(len(labels)):
                ax.text(j, i, f"{M[i, j]:+.2f}", ha="center", va="center", fontsize=5.5)
        ax.set_title(title, fontsize=7.5)
    fig.colorbar(im, ax=axes, shrink=0.7)
    fig.suptitle(f"{LABEL.get(ds, ds)}: residual cross-channel correlation", fontsize=8)
    return fig
