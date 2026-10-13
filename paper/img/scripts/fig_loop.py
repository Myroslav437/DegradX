"""Structure of the benchmark (Figure 1; brief v2.1 W9).

v2.1: the measured datasets are the three evaluated profiles (declarations v2_1.scope.profiles, display labels from
degradx.viz.s3.LABEL); the split fractions come from statistics.splits.measured; the profile carries per-unit offsets
(X2) and correlated noise (X3); the fidelity box lists the measures actually reported (declared fidelity measures minus
those dropped by D25, plus the property table of v2.fidelity.table2), with the number of X1 input sets of the TSTR
ratio (v2.tstr_isolation.input_sets, minus the sensitivity-only set); attribution maps are scored on the reference
model g as a correctness check and on trained LSTMs, the primary model and the identifiability-floor ensemble
(usability.identifiability_floor: seeds x configurations). Flow left to right as in v2. Style: degradx.viz.style.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from degradx.viz import style

import diagram_inputs as D

style.apply()
GREY = style.GREY

profiles = [D.label(p) for p in D.profiles()]
f_fit, f_held = D.split_fractions()
measures = D.fidelity_measures()
n_sets = len(D.input_sets())
ens = D.ensemble()

fig, ax = plt.subplots(figsize=(5.15, 2.45))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

BOX = dict(boxstyle="round,pad=0.0,rounding_size=0.02", fc="white", ec="black", lw=0.9, mutation_aspect=2.0)
LINE = 0.046  # height of one 7 pt text line in axes units (2.45 in figure)


def box(x0, x1, y0, y1, text, fs=8.0, sub=None, sub_fs=6.9):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, **BOX))
    cx, cy = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
    if sub is None:
        ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, linespacing=1.25, zorder=5)
    else:  # title and sub-lines as one block, centred vertically
        n = sub.count("\n") + 1
        h = 1.15 * LINE * fs / 7.0 + n * 1.25 * LINE * sub_fs / 7.0
        top = cy + 0.5 * h
        ax.text(cx, top, text, ha="center", va="top", fontsize=fs, zorder=5)
        ax.text(cx, top - 1.2 * LINE * fs / 7.0, sub, ha="center", va="top", fontsize=sub_fs, color=GREY,
                linespacing=1.25, zorder=5)
    return dict(l=x0, r=x1, b=y0, t=y1, cx=cx, cy=cy)


def arrow(p0, p1, rad=0.0, label=None, lpos=None, ha="center", va="bottom", fs=7.0):
    ax.annotate("", xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle="-|>", color="black", lw=0.9, shrinkA=0, shrinkB=0, mutation_scale=9,
                                connectionstyle=f"arc3,rad={rad}"))
    if label is not None:
        ax.text(lpos[0], lpos[1], label, fontsize=fs, color=GREY, ha=ha, va=va, linespacing=1.2)


# main chain
Y0, Y1 = 0.40, 0.62
data = box(0.005, 0.125, Y0, Y1, "measured\ndatasets")
prof = box(0.230, 0.330, Y0, Y1, "profile")
gen = box(0.415, 0.545, Y0, Y1, "generated\nunits")
ax.text(data["cx"], Y0 - 0.035, "\n".join(profiles), fontsize=7.0, color=GREY, ha="center", va="top",
        linespacing=1.2)
ax.text(prof["cx"], Y0 - 0.035, r"$z,\ \varphi_c,\ \delta_{c,i}$" + "\n" + r"$\varepsilon,\ p$", fontsize=7.2,
        color=GREY, ha="center", va="top", linespacing=1.35)
ax.text(gen["cx"], Y0 - 0.035, r"$x,\ \phi^{\star},\ y,\ R$", fontsize=7.2, color=GREY, ha="center", va="top")

arrow((data["r"], data["cy"]), (prof["l"], prof["cy"]), label=f"fitting\nsplit ({f_fit:g})",
      lpos=(0.5 * (data["r"] + prof["l"]), data["cy"] + 0.02))
arrow((prof["r"], prof["cy"]), (gen["l"], gen["cy"]), label="sample\n" + r"$\theta$",
      lpos=(0.5 * (prof["r"] + gen["l"]), prof["cy"] + 0.02))

# fidelity
XB0, XB1 = 0.612, 0.828
lines = [f"{D.measure_label(m)}, {n_sets} input sets" if m == "tstr" else D.measure_label(m) for m in measures]
fid = box(XB0, XB1, 0.625, 0.995, "fidelity", sub="\n".join(lines))
arrow((0.040, data["t"]), (fid["l"], 0.945), rad=-0.30, label=f"held-out split ({f_held:g})", lpos=(0.40, 0.865), va="top")
arrow((gen["r"], 0.595), (fid["l"], 0.700), rad=-0.18)

# attribution: reference model and trained models
ref = box(XB0, XB1, 0.300, 0.525, r"reference model $g$", sub="exact attribution\nknown")
trn = box(XB0, XB1, 0.005, 0.230, "trained LSTMs", sub=f"primary model and\n{ens['n_members']}-member ensemble")
arrow((gen["r"], 0.450), (ref["l"], 0.415))
arrow((gen["r"], 0.420), (trn["l"], 0.120), rad=0.18, label="explain", lpos=(0.560, 0.200), ha="right",
      va="center")

# outputs
OX = 0.856
for b, text in ((fid, "fidelity\nreport"),
                (ref, "correctness\ncheck"),
                (trn, "scores vs. " + r"$\phi^{\star}$," + "\nensemble floor")):
    arrow((b["r"], b["cy"]), (OX - 0.008, b["cy"]))
    ax.text(OX, b["cy"], text, fontsize=7.8, ha="left", va="center", linespacing=1.25)

fig.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0)
out = D.save(fig, "fig_loop")
print(f"{out}: profiles {profiles}; split {f_fit:g}/{f_held:g}; measures {measures}; input sets {n_sets}; "
      f"ensemble {ens}; printed scale {style.printed_scale(str(out), 0.8):.3f}")
