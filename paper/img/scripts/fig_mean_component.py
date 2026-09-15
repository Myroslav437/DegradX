"""Construction of the mean component (Fig. mean).

Change v2: panel (c) carries its own legend for the unit coding (the channel
coding is legended in panel (b)); axis labels use the subscript notation
z_t and m_{t,c}.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import style

style.apply()

GREY = "0.55"


def state(t, T, k=3.2):
    """Monotone state rising from 0 at t=1 to 1 at t=T, convex late."""
    s = (t - 1) / (T - 1)
    return s ** k


T_A, T_B = 720, 1000
tA = np.arange(1, T_A + 1)
tB = np.arange(1, T_B + 1)
zA, zB = state(tA, T_A), state(tB, T_B)

# channel mappings phi_c(z)
z = np.linspace(0, 1, 200)
phi = {
    "capacity": (1.0 - 0.20 * z, "-"),
    "resistance": (1.0 + 0.60 * z ** 2, "--"),
    "charge time": (1.0 + 0.25 * z ** 1.1, "-."),
}

fig, axes = plt.subplots(1, 3, figsize=(5.474, 1.59))

# --- (a) degradation state -------------------------------------------------
ax = axes[0]
ax.plot(tA, zA, color="black", lw=1.3)
ax.plot(tB, zB, color=GREY, lw=1.3, ls="--")
ax.text(575, 0.56, "unit A", fontsize=7.5, ha="right")
ax.text(1010, 0.16, "unit B", fontsize=7.5, ha="right", color=GREY)
ax.set_title("(a) degradation state", fontsize=8.5, loc="left")
ax.set_xlabel(r"position $t$")
ax.set_ylabel(r"$z_t$")
ax.set_xlim(0, 1040)
ax.set_ylim(-0.03, 1.08)
ax.set_yticks([0, 0.25, 0.50, 0.75, 1.00])

# --- (b) channel mappings --------------------------------------------------
ax = axes[1]
labels = {
    "capacity": r"$\varphi_1$ capacity",
    "resistance": r"$\varphi_2$ resistance",
    "charge time": r"$\varphi_3$ charge time",
}
for name, (vals, ls) in phi.items():
    ax.plot(z, vals, color="black", lw=1.2, ls=ls, label=labels[name])
ax.set_title("(b) channel mappings", fontsize=8.5, loc="left")
ax.set_xlabel(r"$z$")
ax.set_ylabel(r"$\varphi_c(z)$")
ax.set_xlim(-0.02, 1.02)
ax.legend(loc="upper left", frameon=False, handlelength=1.7,
          borderpad=0.1, labelspacing=0.2)

# --- (c) mean components ---------------------------------------------------
ax = axes[2]
for name, (_, ls) in phi.items():
    fn = {"capacity": lambda s: 1.0 - 0.20 * s,
          "resistance": lambda s: 1.0 + 0.60 * s ** 2,
          "charge time": lambda s: 1.0 + 0.25 * s ** 1.1}[name]
    ax.plot(tA, fn(zA), color="black", lw=1.1, ls=ls)
    ax.plot(tB, fn(zB), color=GREY, lw=1.1, ls=ls)
ax.set_title("(c) mean components", fontsize=8.5, loc="left")
ax.set_xlabel(r"position $t$")
ax.set_ylabel(r"$m_{t,c}$")
ax.set_xlim(0, 1040)
handles = [Line2D([], [], color="black", lw=1.1, label="unit A"),
           Line2D([], [], color=GREY, lw=1.1, label="unit B")]
ax.legend(handles=handles, loc="upper left", frameon=False,
          handlelength=1.5, borderpad=0.1, labelspacing=0.2)

for ax in axes:
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

fig.subplots_adjust(wspace=0.45)
fig.savefig("../img/fig_mean_component.pdf")
