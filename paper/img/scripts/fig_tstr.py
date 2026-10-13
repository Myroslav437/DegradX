"""The transfer measurement (Figure 5; brief v2.1 W9). New script: the v2 fig_tstr.pdf had none.

Flow as in the v2 figure: a model trained on generated units (target R) and a reference model trained on the measured
fitting split are both evaluated on the held-out measured units; the reported quantity is the ratio of their errors.
v2.1 adds the input-set ablation (X1): the two models and the held-out windows use the same input set s, and the
ratio is computed once per set. The sets are the declared v2.tstr_isolation.input_sets minus the one declared
"sensitivity, not a reading" (cross-checked against scripts/v2/v5_fidelity.py INPUT_SETS), labelled by their keys
with '_' read as a space; the error is the declared fidelity.tstr.error. Style: degradx.viz.style.
"""
import textwrap

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from degradx.viz import style

import diagram_inputs as D

style.apply()
GREY = style.GREY

sets = [D.input_set_label(k) for k in D.input_sets()]
f_fit, f_held = D.split_fractions()

fig, ax = plt.subplots(figsize=(4.90, 1.95))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

BOX = dict(boxstyle="round,pad=0.0,rounding_size=0.02", fc="white", ec="black", lw=0.8, mutation_aspect=2.5)
FS, FS_LAB = 7.3, 6.9


def box(x0, x1, y0, y1, text, fs=FS, dashed=False, **kw):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, **{**BOX, "ls": "--" if dashed else "-"}))
    ax.text(0.5 * (x0 + x1), 0.5 * (y0 + y1), text, ha="center", va="center", fontsize=fs, linespacing=1.25,
            zorder=5, **kw)
    return dict(l=x0, r=x1, b=y0, t=y1, cx=0.5 * (x0 + x1), cy=0.5 * (y0 + y1))


def arrow(p0, p1, rad=0.0, label=None, lpos=None, ha="center", va="bottom", color="black"):
    ax.annotate("", xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=0.8, shrinkA=0, shrinkB=0, mutation_scale=8,
                                connectionstyle=f"arc3,rad={rad}"))
    if label is not None:
        ax.text(lpos[0], lpos[1], label, fontsize=FS_LAB, color=GREY, ha=ha, va=va)


TOP, BOT = (0.78, 0.98), (0.02, 0.22)
gen = box(0.005, 0.205, *TOP, "generated units\n" + r"target $R$")
mea = box(0.005, 0.205, *BOT, f"measured units\nfitting split ({f_fit:g})")
mg = box(0.285, 0.475, *TOP, "model trained\non generated")
mm = box(0.285, 0.475, *BOT, "model trained\non measured")
ev = box(0.585, 0.775, 0.36, 0.64, "evaluate on\nheld-out ({:g})\nmeasured units".format(f_held))
rt = box(0.840, 0.995, 0.40, 0.60, "error ratio", dashed=True)

# training arrows
yT, yB = 0.5 * sum(TOP), 0.5 * sum(BOT)
arrow((gen["r"], yT), (mg["l"], yT), label="train", lpos=(0.245, yT + 0.015))
arrow((mea["r"], yB), (mm["l"], yB), label="train", lpos=(0.245, yB - 0.02), va="top")

# input set s: one box feeding both training arrows and the evaluation
lines = textwrap.wrap(", ".join(sets), 40)
ins = box(0.005, 0.475, 0.355, 0.645, r"input set $s$:" + "\n" + "\n".join(lines), fs=FS_LAB)
arrow((0.245, ins["t"]), (0.245, yT - 0.004), color="0.35")
arrow((0.245, ins["b"]), (0.245, yB + 0.004), color="0.35")
arrow((ins["r"], ins["cy"]), (ev["l"], ins["cy"]), color="0.35")

# evaluation and ratio
arrow((mg["r"], yT), (ev["l"] + 0.02, ev["t"]), rad=-0.25, label="TSTR", lpos=(0.535, 0.85), ha="left")
arrow((mm["r"], yB), (ev["l"] + 0.02, ev["b"]), rad=0.25, label="reference", lpos=(0.535, 0.15), ha="left",
      va="top")
arrow((ev["r"], ev["cy"]), (rt["l"], rt["cy"]))
ax.text(rt["cx"], rt["b"] - 0.04, "TSTR / reference,\none per input set $s$", fontsize=FS_LAB, color=GREY,
        ha="center", va="top", style="italic", linespacing=1.2)

fig.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0)
out = D.save(fig, "fig_tstr")
print(f"{out}: input sets {sets}; split {f_fit:g}/{f_held:g}; printed scale {style.printed_scale(str(out), 0.8):.3f}")
