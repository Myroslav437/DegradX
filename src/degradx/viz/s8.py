"""S8 figures: method scores on trained vs reference model per weighting, with the identifiability floor."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from degradx.viz import style  # noqa: E402

LABEL = {"MATR": "MATR", "HUST": "HUST", "NASA_PCoE": "NASA PCoE"}
METH = {"timeshap": "TimeSHAP", "integrated_gradients": "IG", "feature_occlusion": "occlusion"}


def method_scores(ds, res):
    style.apply()
    kinds = list(res["weightings"])
    fig, axes = plt.subplots(1, len(kinds), figsize=(style.TEXTWIDTH_IN, 2.1), squeeze=False, sharey=True)
    for ax, kind in zip(axes[0], kinds):
        r = res["weightings"][kind]
        for j, meth in enumerate(("timeshap", "integrated_gradients", "feature_occlusion")):
            for dx, model, col in ((-0.15, "trained", "black"), (0.15, "reference", style.MEASURED)):
                s = r["scores"].get(f"{model}/{meth}", {}).get("rank")
                if not s or s.get("mean") is None:
                    continue
                ax.plot([j + dx], [s["mean"]], marker="o", ms=4, color=col, label=model if j == 0 else None)
                if s.get("ci_low") is not None:
                    ax.plot([j + dx, j + dx], [s["ci_low"], s["ci_high"]], color=col, lw=1)
            fl = r.get("identifiability_floor", {}).get(meth)
            if fl:
                ax.plot([j - 0.3, j - 0.3], [fl["rank_min"], fl["rank_max"]], color=style.FILL, lw=4, solid_capstyle="butt", label="ensemble range" if j == 1 else None)
        ex = r["scores"]["reference_exact"]["rank"]["mean"]
        ax.axhline(ex, color=style.REFERENCE, lw=style.LW_THIN, ls="--")
        ax.set_xticks(range(3), [METH[m] for m in ("timeshap", "integrated_gradients", "feature_occlusion")], fontsize=7)
        ax.set_title(kind.replace("_", " "), fontsize=8)
        style.despine(ax)
    axes[0][0].set_ylabel("rank agreement with graded field")
    axes[0][0].legend(frameon=False, fontsize=6)
    fig.suptitle(f"{LABEL[ds]}: reference values ({res['windows']} windows, {res['units']} units); dashed: exact attribution of the reference model", fontsize=7.5)
    fig.tight_layout()
    return fig
