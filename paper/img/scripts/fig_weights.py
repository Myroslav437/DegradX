"""Weighting of positions within a window (Figure 4; brief v2.1 W9).

v2.1: L and h from the declarations (target.window_length_L, target.position_profiles.recency: h = L/4); recency is the
primary weighting and uniform the sensitivity (v2.scope.weightings); final-position weighting is drawn lighter and
labelled as defined but not scored (target.position_profiles.final_position.superseded_r3, v2.scope.dropped; D25).
Vertical axis: the position profile pi_u of w_{u,c} = kappa_c pi_u. Style: degradx.viz.style.
"""
import numpy as np
import matplotlib.pyplot as plt
from degradx.viz import style
from degradx.targets.decomposable import position_profile

import diagram_inputs as D

style.apply()

L, h = D.window()
W = D.weightings()
u = np.arange(1, L + 1)
# the benchmark's own position profiles (degradx.targets.decomposable.position_profile), oldest position first
pi = {k: position_profile(k, L, half_life=h) for k in ("recency", "uniform", "final_position")}
role = {W["primary"]: "primary", W["sensitivity"]: "sensitivity"}

fig, ax = plt.subplots(figsize=(2.30, 1.78))

ax.plot(u, pi["recency"], color="black", lw=1.4, marker="o", ms=1.8, mew=0,
        label=f"recency ({role['recency']})")
ax.plot(u, pi["uniform"], color="black", lw=1.0, ls="--", label=f"uniform ({role['uniform']})")

top = 1.38 * pi["recency"].max()
fp_label = "final position" + ("" if W["final_position_scored"] else "\n(defined, not scored)")
uf = int(u[np.argmax(pi["final_position"])])  # the single position with weight 1 (= L)
ax.plot([uf, uf], [0.0, top], color="0.62", lw=1.0, ls=":", label=fp_label)
ax.annotate("", xy=(uf, top), xytext=(uf, top * 0.80),
            arrowprops=dict(arrowstyle="-|>", color="0.62", lw=0.9, mutation_scale=7))
ax.text(uf - 0.6, top * 0.985, rf"${pi['final_position'][-1]:g}$", ha="right", va="top", fontsize=7, color="0.5")

ax.set_xlim(0, L + 1)
ax.set_ylim(0, top)
ax.set_xlabel(r"position within window $u$")
ax.set_ylabel(r"position profile $\pi_u$")
ax.set_xticks(np.arange(0, L + 1, int(h)))
ax.set_yticks([0, 0.05, 0.10])
ax.yaxis.set_major_formatter(plt.FormatStrFormatter("%.2f"))
style.despine(ax)
ax.legend(loc="upper left", frameon=False, handlelength=1.6, borderpad=0.1, labelspacing=0.3, fontsize=7)

out = D.save(fig, "fig_weights")
print(f"{out}: L={L} h={h:g} recency max {pi['recency'].max():.4f} uniform {pi['uniform'][0]:.4f} "
      f"printed scale {style.printed_scale(str(out), 0.35):.3f}")
