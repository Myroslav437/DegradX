"""Structure of the benchmark (Fig. loop).

Changes v2:
  * arrow labels identify the split and the operation ("fitting split",
    "sample theta") instead of the uninformative "fit" / "sample";
  * the split sub-label under the measured-dataset box is dropped, since the
    split now appears on the two outgoing arrows;
  * every arrow terminates on the border of its target box, so the arrow into
    the fidelity box no longer runs across it.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import style

style.apply()

GREY = "0.35"

fig, ax = plt.subplots(figsize=(4.611, 2.042))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

BOX = dict(boxstyle="round,pad=0.0,rounding_size=0.02", fc="white",
           ec="black", lw=0.9, mutation_aspect=2.2)


def box(x0, x1, y0, y1, text, fs=8.5):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, **BOX))
    ax.text(0.5 * (x0 + x1), 0.5 * (y0 + y1), text, ha="center",
            va="center", fontsize=fs, linespacing=1.25, zorder=5)
    return dict(l=x0, r=x1, b=y0, t=y1,
                cx=0.5 * (x0 + x1), cy=0.5 * (y0 + y1))


def arrow(p0, p1, rad=0.0, label=None, lpos=None, ha="center", va="bottom"):
    ax.annotate("", xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle="-|>", color="black", lw=0.9,
                                shrinkA=0, shrinkB=0, mutation_scale=9,
                                connectionstyle=f"arc3,rad={rad}"))
    if label is not None:
        ax.text(lpos[0], lpos[1], label, fontsize=7.2, color=GREY,
                ha=ha, va=va)


data = box(0.012, 0.152, 0.360, 0.610, "measured\ndataset")
prof = box(0.212, 0.358, 0.360, 0.610, "profile\nparameters")
gen = box(0.418, 0.552, 0.360, 0.610, "generated\nunits")
fid = box(0.612, 0.800, 0.680, 0.950, "distributional\ncomparison,\nTSTR", fs=7.8)
att = box(0.612, 0.800, 0.040, 0.300, "attribution\nmap under\nevaluation", fs=7.8)

# sub-labels
ax.text(prof["cx"], 0.300, r"$z,\ \varphi_c,\ \varepsilon,\ p$", fontsize=7.6,
        color=GREY, ha="center", va="top")
ax.text(gen["cx"], 0.300, r"$x,\ \phi^{\star},\ y,\ R$", fontsize=7.6,
        color=GREY, ha="center", va="top")

# main chain
arrow((data["r"], data["cy"]), (prof["l"], prof["cy"]),
      label="fitting split", lpos=(0.5 * (data["r"] + prof["l"]), 0.617))
arrow((prof["r"], prof["cy"]), (gen["l"], gen["cy"]),
      label=r"sample $\theta$", lpos=(0.5 * (prof["r"] + gen["l"]), 0.640))

# held-out split: measured dataset -> fidelity box, landing on its left border
arrow((0.100, data["t"]), (fid["l"], 0.890), rad=-0.26,
      label="held-out split", lpos=(0.33, 0.912))

# generated units -> fidelity box and -> attribution map
arrow((gen["r"], 0.585), (fid["l"], 0.735), rad=-0.16)
arrow((gen["r"], 0.386), (att["l"], 0.252), rad=0.16,
      label="explain", lpos=(0.596, 0.330), ha="left", va="center")

# outputs
arrow((fid["r"], fid["cy"]), (0.834, fid["cy"]))
ax.text(0.842, fid["cy"], "fidelity\nreport", fontsize=8.0, ha="left",
        va="center", linespacing=1.25)
arrow((att["r"], att["cy"]), (0.834, att["cy"]))
ax.text(0.842, att["cy"], "score vs.\n" + r"$\phi^{\star}$", fontsize=8.0,
        ha="left", va="center", linespacing=1.25)

fig.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0)
fig.savefig("../img/fig_loop.pdf")
