"""Weighting of positions within a window (Fig. weights).

Change v2: the vertical range is now set by the recency weighting rather than by
the final-position weighting, so that the recency and uniform curves are
distinguishable. The final-position weighting leaves the axis and is annotated.
"""
import numpy as np
import matplotlib.pyplot as plt
import style

style.apply()

L = 40
u = np.arange(1, L + 1)
tau = 8.0

w_rec = np.exp(-(L - u) / tau)
w_rec = w_rec / w_rec.sum()
w_uni = np.full(L, 1.0 / L)

fig, ax = plt.subplots(figsize=(2.482, 1.682))

ax.plot(u, w_rec, color="black", lw=1.4, label="recency (default)")
ax.plot(u, w_uni, color="black", lw=1.0, ls="--", label="uniform")

top = 1.34 * w_rec.max()
ax.plot([L, L], [0.0, top], color=style.GREY, lw=1.0, ls=":",
        label="final position")
ax.plot([L], [w_rec.max() * 1.02], marker="", ms=0)
ax.annotate(r"$1$", xy=(L, top), xytext=(L - 1.0, top * 0.955),
            ha="right", va="top", fontsize=7, color=style.GREY)
ax.annotate("", xy=(L, top), xytext=(L, top * 0.80),
            arrowprops=dict(arrowstyle="-|>", color=style.GREY, lw=0.9,
                            mutation_scale=7))

ax.set_xlim(0, L + 1.5)
ax.set_ylim(0, top)
ax.set_xlabel(r"position within window $u$")
ax.set_ylabel(r"weight $a_{u,c}$")
ax.set_yticks([])
ax.set_xticks([0, 10, 20, 30, 40])
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.legend(loc="upper left", frameon=False, handlelength=1.6,
          borderpad=0.1, labelspacing=0.25)

fig.savefig("../img/fig_weights.pdf")
print("recency max %.4f  uniform %.4f  ratio %.2f" %
      (w_rec.max(), w_uni[0], w_rec.max() / w_uni[0]))
