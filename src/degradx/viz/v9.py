"""V9 figure (brief "DegradX v2", X9): per score, each member's IG and occlusion score on y_obs, the ensemble range against
the largest gap between methods on the primary model, beside the same quantities on the standard y when available."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from degradx.viz import style  # noqa: E402

SCORE = {"rank": "rank agreement (↑)", "allocation": "channel allocation error (↓)", "temporal": "temporal profile error [pos.] (↓)"}
METH = {"integrated_gradients": "IG", "feature_occlusion": "occlusion"}


def ensemble_vs_gap(res):
    style.apply()
    fig, axes = plt.subplots(1, 3, figsize=(style.TEXTWIDTH_IN, 2.3))
    for ax, k in zip(axes, SCORE):
        for j, (meth, lab) in enumerate(METH.items()):
            vals = [v[k]["mean"] for v in res["scores"][meth].values()]
            ax.scatter([j] * len(vals), vals, s=9, color=style.MEASURED_BUNDLE, zorder=2)
            ax.scatter([j], [res["scores"][meth]["A0"][k]["mean"]], s=18, color="black", zorder=3)
        c = res["comparison"][k]
        ax.set_xticks([0, 1], list(METH.values()))
        ax.set_xlim(-0.6, 1.6)
        ax.set_title(f"{SCORE[k]}\nmethod gap {c['largest_method_gap']:.3f}; ranges " + ", ".join(f"{c['ensemble_range'][m]:.3f}" for m in METH), fontsize=6.5)
        style.despine(ax)
    fig.suptitle("HUST, observation-level target y_obs: ten members (grey), primary (black)", fontsize=7.5)
    fig.tight_layout()
    return fig
