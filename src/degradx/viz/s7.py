"""S7 figures: score vs degradation magnitude per operator (paper Figure 7), score vs generator settings (paper Figure 8)."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from degradx.viz import style  # noqa: E402

LABEL = {"MATR": "MATR", "HUST": "HUST", "NASA_PCoE": "NASA PCoE"}
OP_LABEL = {"added_noise": "added noise [× SD of map]", "shift_to_start": "mass shifted to start [fraction]", "shift_to_end": "mass shifted to end [fraction]",
            "smoothing": "smoothing [Gaussian σ, positions]", "permuted_fraction": "permuted fraction of cells"}


def degradation(ds, kind, r):
    style.apply()
    ops = list(r["operators"])
    fig, axes = plt.subplots(1, len(ops), figsize=(style.TEXTWIDTH_IN, 1.9), squeeze=False, sharey=True)
    for ax, op in zip(axes[0], ops):
        s = r["operators"][op]
        x = np.arange(len(s["grid"]))
        ci = np.array(s["rank_ci"])
        ax.fill_between(x, ci[:, 0], ci[:, 1], color=style.FILL, lw=0)
        ax.plot(x, s["rank_mean"], color="black", marker="o", ms=2.5, label="rank agreement, graded field")
        if "retrieval_mean" in s:
            ci = np.array(s["retrieval_ci"])
            ax.plot(x, s["retrieval_mean"], color="black", ls="--", marker="s", ms=2.5, label="retrieval (paired), sparse set")
            ax.plot(x, s["plain_retrieval_mean"], color=style.MEASURED, ls=":", marker="^", ms=2.5, label="retrieval (plain), sparse set")
            ax.axhline(r["chance_retrieval"], color=style.REFERENCE, lw=style.LW_THIN, ls="--")
        ax.axhline(r["chance_rank"], color=style.REFERENCE, lw=style.LW_THIN)
        ax.set_xticks(x, [f"{g:g}" for g in s["grid"]], fontsize=6, rotation=45)
        ax.set_xlabel(OP_LABEL[op], fontsize=7)
        style.despine(ax)
    axes[0][0].set_ylabel("score")
    axes[0][0].legend(frameon=False, fontsize=5.5, loc="lower left")
    fig.suptitle(f"{LABEL[ds]} [{kind}]: scores of the degraded attribution ground truth (grey lines: chance)", fontsize=7.5)
    fig.tight_layout()
    return fig


def settings_panel(rows, ops_range):
    style.apply()
    settings = ["noise_variance_multiplier", "transition_sharpness_multiplier", "window_length_L", "pattern_amplitude_multiplier"]
    labels = {"noise_variance_multiplier": "noise variance [× fitted]", "transition_sharpness_multiplier": "transition sharpness [exponent on z]",
              "window_length_L": "window length L", "pattern_amplitude_multiplier": "pattern amplitude [× fitted]"}
    present = [s for s in settings if any(r["setting"] == s for r in rows)]
    fig, axes = plt.subplots(1, len(present), figsize=(style.TEXTWIDTH_IN, 2.0), squeeze=False, sharey=True)
    ls = {"MATR": "-", "HUST": "--", "NASA_PCoE": ":"}
    for ax, st in zip(axes[0], present):
        for ds in ("MATR", "HUST", "NASA_PCoE"):
            rr = [r for r in rows if r["setting"] == st and r["dataset"] == ds]
            if not rr:
                continue
            x = [r["value"] for r in rr]
            ax.plot(x, [r["rank_ig_norm"] for r in rr], color="black", ls=ls[ds], marker="o", ms=2.5, label=f"{LABEL[ds]} rank")
            if st == "pattern_amplitude_multiplier" or any(r.get("retrieval_ig_norm") is not None for r in rr):
                ax.plot(x, [r.get("retrieval_ig_norm") for r in rr], color=style.MEASURED, ls=ls[ds], marker="s", ms=2.5, label=f"{LABEL[ds]} retrieval")
        ax.axhspan(0.95, 1.05, color=style.FILL, lw=0)
        ax.axhspan(-0.05, 0.05, color=style.FILL, lw=0)
        ax.set_xscale("log", base=2)
        ax.set_xlabel(labels[st], fontsize=7)
        style.despine(ax)
    axes[0][0].set_ylabel("normalised score (IG, trained model)")
    axes[0][0].legend(frameon=False, fontsize=5.5)
    fig.suptitle("Score response to generator settings; shaded: saturation (>= 0.95) and near chance (<= 0.05)", fontsize=7.5)
    fig.tight_layout()
    return fig
