"""V7 figures (brief "DegradX v2", X5): each score against the magnitude of each degradation operator, with the chance
level and the registering magnitude (declarations v2.scoring.registers_check)."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from degradx.viz import style  # noqa: E402

LABEL = {"MATR": "MATR", "HUST": "HUST", "ISU_ILCC": "ISU-ILCC"}
SCORE = {"rank": "rank agreement (↑)", "allocation": "channel allocation error (↓)", "temporal": "temporal profile error [positions] (↓)"}
OPS = {"added_noise": "added noise [×SD]", "shift_to_start": "mass to start", "shift_to_end": "mass to end", "smoothing": "smoothing σ [positions]",
       "permuted_fraction": "permuted fraction"}


def score_vs_degradation(ds, kind, r):
    style.apply()
    ops = list(r["operators"])
    fig, axes = plt.subplots(3, len(ops), figsize=(style.TEXTWIDTH_IN, 4.6), squeeze=False)
    for j, op in enumerate(ops):
        s = r["operators"][op]
        x = np.arange(len(s["grid"]))
        for i, k in enumerate(SCORE):
            ax = axes[i][j]
            ax.plot(x, s[k]["mean"], marker="o", ms=2.5, color="black", lw=style.LW_MAIN)
            ax.axhline(r["chance"][k], color=style.REFERENCE, lw=style.LW_THIN, ls="--")
            mag = s[k]["registers"]["registering_magnitude"]
            if mag is not None:
                ax.axvline(s["grid"].index(mag), color=style.MEASURED, lw=style.LW_THIN, ls=":")
            res = s[k]["resolution"]
            ax.set_title(f"{'reg. ' + str(mag) if mag is not None else 'not registered'}; res. {res}", fontsize=5.5)
            ax.set_xticks(x, [str(g) for g in s["grid"]], fontsize=5, rotation=90)
            if j == 0:
                ax.set_ylabel(SCORE[k], fontsize=6)
            if i == 2:
                ax.set_xlabel(OPS.get(op, op), fontsize=6)
            style.despine(ax)
    fig.suptitle(f"{LABEL.get(ds, ds)} [{kind}]: scores under controlled degradation of ϕ* (dashed: fully permuted map; dotted: registering magnitude)", fontsize=7)
    fig.tight_layout()
    return fig
