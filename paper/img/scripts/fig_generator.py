"""One channel of a generated unit (Fig. generator).

Change v2: vertical axis labels carry the position and channel indices; the
inserted patterns are shown with both signs, matching the two pattern types.
"""
import numpy as np
import matplotlib.pyplot as plt
import style

style.apply()

rng = np.random.default_rng(7)

T = 950
t = np.arange(1, T + 1)

# --- mean component: two-term exponential capacity fade -------------------
m = 1.0 * np.exp(-0.00012 * t) + 0.055 * np.exp(0.0033 * t)
m = 1.02 - (m - m[0])          # falling, with a late knee
m = m - m[0] + 1.0

# --- inserted patterns: two positive, one negative ------------------------
def bump(t, pos, amp, dur):
    return amp * np.exp(-0.5 * ((t - pos) / dur) ** 2)

events = [(210, 0.040, 14), (465, -0.030, 12), (700, 0.055, 11)]
p = np.zeros_like(t, dtype=float)
for pos, amp, dur in events:
    p += bump(t, pos, amp, dur)

# --- noise ----------------------------------------------------------------
eps = 0.017 * rng.standard_normal(T)

x = m + p + eps

# --- ground truth: graded field + sparse stems ----------------------------
a = np.exp(-(T - t) / 260.0)
a = a / a.max()
phi_dense = a * (m[0] - m)          # graded contribution of the mean part
phi_dense = phi_dense / phi_dense.max()
phi_sparse = p / np.abs(p).max() * 0.85

fig, axes = plt.subplots(5, 1, figsize=(4.378, 4.248), sharex=True)

labels = [r"(a) $m_{t,c}$",
          r"(b) $\sum_k \; p_{k,t,c}$",
          r"(c) $\varepsilon_{t,c}$",
          r"(d) $x_{t,c}$",
          r"(e) $\phi^{\star}_{t,c}$"]

axes[0].plot(t, m, color="black", lw=1.1)
axes[1].plot(t, p, color="black", lw=1.1)
for pos, amp, dur in events:
    axes[1].axvline(pos, color="0.6", lw=0.6, ls=":")
axes[2].plot(t, eps, color="0.45", lw=0.5)
axes[3].plot(t, x, color="black", lw=0.55)

ax = axes[4]
ax.fill_between(t, 0, phi_dense, color="0.82", lw=0)
ax.plot(t, phi_dense, color="0.45", lw=0.7)
for pos, amp, dur in events:
    val = phi_sparse[pos - 1]
    ax.plot([pos, pos], [0, val], color="black", lw=1.1)
    ax.plot([pos], [val], marker="o", ms=3.0, mfc="white",
            mec="black", mew=0.9)
ax.axhline(0, color="0.6", lw=0.6)

for ax, lab in zip(axes, labels):
    ax.set_ylabel(lab, fontsize=8.5)
    ax.set_yticks([])
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

axes[4].set_xlabel(r"position $t$")
axes[4].set_xlim(0, T + 10)
fig.subplots_adjust(hspace=0.30)
fig.savefig("../img/fig_generator.pdf")
