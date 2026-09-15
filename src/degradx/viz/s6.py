"""S6 figures: training/validation curves, predicted vs true y with error by state, permutation importance."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from degradx.viz import style  # noqa: E402

LABEL = {"MATR": "MATR", "HUST": "HUST", "NASA_PCoE": "NASA PCoE"}


def training_curves(ds, kind, members):
    style.apply()
    fig, axes = plt.subplots(1, 2, figsize=(style.TEXTWIDTH_IN * 0.7, 1.9), sharey=True)
    for ax, cname in zip(axes, ("A", "B")):
        for mm in members:
            if mm["config"] != cname:
                continue
            ax.plot(mm["history"]["train"], color=style.MEASURED_BUNDLE, lw=style.LW_THIN)
            ax.plot(mm["history"]["val"], color="black", lw=style.LW_THIN)
        ax.set_yscale("log")
        ax.set_xlabel("epoch")
        ax.set_title(f"config {cname}", fontsize=8)
        style.despine(ax)
    axes[0].set_ylabel("MSE (standardised y)")
    fig.suptitle(f"{LABEL[ds]} [{kind}]: training (grey) and validation (black), 5 seeds per configuration", fontsize=7.5)
    fig.tight_layout()
    return fig


def predicted_vs_true(ds, kind, y, pred, z):
    style.apply()
    fig, axes = plt.subplots(1, 2, figsize=(style.TEXTWIDTH_IN * 0.7, 2.1))
    g = np.random.default_rng(0)  # plotting subsample only
    idx = g.choice(len(y), size=min(5000, len(y)), replace=False)
    ax = axes[0]
    ax.scatter(y[idx], pred[idx], s=1, color=style.MEASURED, rasterized=True)
    lim = [min(y.min(), pred.min()), max(y.max(), pred.max())]
    ax.plot(lim, lim, color="black", lw=style.LW_THIN, ls="--")
    ax.set_xlabel("true y")
    ax.set_ylabel("predicted y")
    style.despine(ax)
    ax = axes[1]
    bins = np.linspace(0, 1, 11)
    b = np.clip(np.digitize(z, bins) - 1, 0, 9)
    rmse = [np.sqrt(np.mean((pred[b == i] - y[b == i]) ** 2)) if np.any(b == i) else np.nan for i in range(10)]
    ax.bar((bins[:-1] + bins[1:]) / 2, rmse, width=0.08, color=style.MEASURED)
    ax.set_xlabel("degradation state at window end $z_t$")
    ax.set_ylabel("RMSE of y")
    style.despine(ax)
    fig.suptitle(f"{LABEL[ds]} [{kind}]: primary model on test units", fontsize=7.5)
    fig.tight_layout()
    return fig


def importance(ds, kind, imp, cond, tol, roles):
    style.apply()
    chans = list(imp)
    fig, ax = plt.subplots(figsize=(3.4, 0.28 * len(chans) + 0.9))
    for i, c in enumerate(chans):
        v = imp[c]
        role = "null" if c.startswith("null") else ("weighted" if c in roles["weighted"] else "redundant")
        col = {"null": "black", "weighted": style.FILL, "redundant": style.MEASURED}[role]
        ax.barh(i, v["nmse_increase"], color=col, height=0.6)
        ax.plot([v["ci_low"], v["ci_high"]], [i, i], color="black", lw=0.8)
        if c in cond:
            ci = cond[c]["conditional_importance"]
            ax.plot([ci["nmse_increase"]], [i], marker="D", ms=3, color="black")
    ax.axvline(tol, color="black", lw=style.LW_THIN, ls="--")
    ax.set_yticks(range(len(chans)), [c.replace("_", " ") for c in chans], fontsize=7)
    ax.set_xscale("symlog", linthresh=0.01)
    ax.set_xlabel("NMSE increase when permuted (95% CI)")
    ax.invert_yaxis()
    ax.set_title(f"{LABEL[ds]} [{kind}]: dashed = null-channel tolerance; ◆ conditional", fontsize=7)
    style.despine(ax)
    fig.tight_layout()
    return fig
