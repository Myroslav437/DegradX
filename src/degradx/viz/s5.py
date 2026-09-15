"""S5 figures: TSTR error ratios, discriminative score (with caveat), property distributions, window embedding (illustration)."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from degradx.viz import style  # noqa: E402

LABEL = {"MATR": "MATR", "HUST": "HUST", "NASA_PCoE": "NASA PCoE"}


def tstr_ratios(results: dict):
    style.apply()
    fig, ax = plt.subplots(figsize=(3.2, 2.0))
    names = list(results)
    for i, ds in enumerate(names):
        t = results[ds]["tstr"]
        void = t.get("void")
        col = style.MEASURED if void else "black"
        ax.plot([t["ratio"]], [i], marker="o", ms=4, color=col)
        if t["ci_low"] is not None:
            ax.plot([t["ci_low"], t["ci_high"]], [i, i], color=col, lw=1.2)
        lo, hi = t["ratio_spread"]["min"], t["ratio_spread"]["max"]
        ax.plot([lo, hi], [i - 0.18, i - 0.18], color=style.MEASURED_BUNDLE, lw=3, solid_capstyle="butt")
        ax.text(ax.get_xlim()[1] if False else t["ratio"], i + 0.22, f"{t['ratio']:.2f}" + (" (void)" if void else ""), fontsize=6.5, ha="center")
    ax.axvline(1.0, color=style.REFERENCE, lw=style.LW_THIN, ls="--")
    ax.set_yticks(range(len(names)), [f"{LABEL[d]} ({results[d]['tstr']['held_out_units']} units)" for d in names])
    ax.set_xlabel("TSTR error ratio (RMSE generated-trained / measured-trained)")
    ax.set_xscale("log")
    from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter

    ax.xaxis.set_major_locator(FixedLocator([0.5, 1, 2, 4, 8]))
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_locator(NullLocator())
    ax.invert_yaxis()
    fig.text(0.99, 0.005, "black: ratio, 95% BCa interval over held-out units; grey bar: range over seed pairs; grey: void (D02)",
             ha="right", va="bottom", fontsize=5.5, color=style.GREY)
    style.despine(ax)
    fig.tight_layout()
    return fig


def discriminator(results: dict):
    style.apply()
    fig, ax = plt.subplots(figsize=(3.2, 1.9))
    names = list(results)
    for i, ds in enumerate(names):
        errs = [s["discriminative_error"] for s in results[ds]["per_generation_seed"]]
        ax.scatter(errs, [i] * len(errs), color="black", s=10)
    ax.axvline(0.5, color=style.REFERENCE, lw=style.LW_THIN, ls="--")
    ax.set_yticks(range(len(names)), [LABEL[d] for d in names])
    ax.set_xlim(-0.02, 0.6)
    ax.set_xlabel("discriminative error (0.5 = indistinguishable)")
    ax.invert_yaxis()
    ax.set_title("coarse indicator only: saturates on any mismatch (paper §3.5.1)", fontsize=7, color=style.GREY)
    style.despine(ax)
    fig.tight_layout()
    return fig


def _traj(prof, q_nom, rho):
    e = prof["estimated_from_data"]["E1_theta_distribution"]
    T = [u["T"] for u in e["per_unit"]]
    drift = [(u["q1"] - rho * q_nom) / u["T"] * 1e5 for u in e["per_unit"]]
    return np.array(T, float), np.array(drift, float)


def property_distributions(ds, meas_prof, gen_prof, q_nom, rho):
    style.apply()
    fig, axes = plt.subplots(1, 3, figsize=(style.TEXTWIDTH_IN, 1.9))
    Tm, dm = _traj(meas_prof, q_nom, rho)
    Tg, dg = _traj(gen_prof, q_nom, rho)
    for ax, (a, b, lab) in zip(axes[:2], ((Tm, Tg, "unit length T [cycles]"), (dm, dg, "drift [mAh / 100 cycles]"))):
        bins = np.linspace(min(a.min(), b.min()), max(a.max(), b.max()), 20)
        ax.hist(b, bins=bins, density=True, color=style.FILL, label=f"generated ({len(b)})")
        ax.hist(a, bins=bins, density=True, histtype="step", color="black", lw=1.2, label=f"measured held-out ({len(a)})")
        ax.set_xlabel(lab)
        style.despine(ax)
    axes[0].set_ylabel("density")
    axes[0].legend(frameon=False, fontsize=6)
    ax = axes[2]
    ch = list(meas_prof["estimated_from_data"]["E5_noise"])
    vm = [meas_prof["estimated_from_data"]["E5_noise"][c]["variance"] for c in ch]
    vg = [gen_prof["estimated_from_data"]["E5_noise"][c]["variance"] for c in ch]
    ax.scatter(np.log10(vm), np.log10(vg), color="black", s=12)
    lim = [min(np.log10(vm + vg)) - 0.5, max(np.log10(vm + vg)) + 0.5]
    ax.plot(lim, lim, color=style.REFERENCE, lw=style.LW_THIN, ls="--")
    for c, x, y in zip(ch, np.log10(vm), np.log10(vg)):
        ax.text(x, y, c.replace("_", " ")[:12], fontsize=5.5)
    ax.set_xlabel("log10 noise variance, measured")
    ax.set_ylabel("log10, generated")
    style.despine(ax)
    fig.suptitle(f"{LABEL[ds]}: measured held-out vs generated properties (same S3 estimators)", fontsize=8)
    fig.tight_layout()
    return fig


def window_embedding(ds, rep_meas, rep_gen, seed):
    """t-SNE of TS2Vec window representations: illustration only, not a measurement."""
    from sklearn.manifold import TSNE

    style.apply()
    n = min(len(rep_meas), len(rep_gen), 1500)
    g = np.random.default_rng(seed)
    A = rep_meas[g.choice(len(rep_meas), n, replace=False)]
    B = rep_gen[g.choice(len(rep_gen), n, replace=False)]
    Z = TSNE(n_components=2, random_state=seed, init="pca", perplexity=30).fit_transform(np.vstack([A, B]))
    fig, ax = plt.subplots(figsize=(2.6, 2.4))
    ax.scatter(Z[n:, 0], Z[n:, 1], s=2, color=style.FILL, label="generated", rasterized=True)
    ax.scatter(Z[:n, 0], Z[:n, 1], s=2, color="black", label="measured held-out", rasterized=True)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(frameon=False, fontsize=6, markerscale=3)
    ax.set_title(f"{LABEL[ds]}: t-SNE of window representations (illustration)", fontsize=7)
    style.despine(ax)
    fig.tight_layout()
    return fig
