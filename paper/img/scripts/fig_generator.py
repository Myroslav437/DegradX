"""Decomposition of a generated unit (Figure 2; brief v2.1 W9).

v2.1: every curve is one generated FORM unit (data/v2.1/generated/TRI_FORMATION/seed0.pkl), chosen by the fixed rule
of diagram_inputs.illustrated_unit (at least two inserted patterns, T within 5 % of the median T, largest |charge-time
offset|). Left column: the channel that carries inserted patterns (declarations channels.roles.weighted_pattern_carrying,
capacity); right column: charge time.

  (a) m_{t,c} (black) and its shared-mapping part phi_c(z_t) (GeneratedUnit.m_state, dashed); on charge time the gap
      is the unit's offset delta_{c,i} (X2); capacity carries no offset (affine in z with the unit's own q1)
  (b) sum_k p_{k,t,c}: the term exists only for a pattern type the profile enables (E6_patterns.*.enabled): FORM
      enables the positive type; MATR and HUST (artifacts/v2/v3_fit_profiles) enable none, so the term is zero there
  (c) eps_{t,c}: capacity; charge time (black) with mean discharge voltage (grey), each standardised by its SD over
      the unit; r is the profile's fitted within-unit correlation (v2.within_unit_correlation, X3)
  (d) x_{t,c} = m + sum_k p + eps (GeneratedUnit.x); shaded: the window of (e)
  (e) phi*_{u,c} of one window under the primary weighting, computed by degradx.targets.decomposable.unit_targets
      (graded field shaded, sparse set as stems). Window rule: the L positions ending at the last position of the
      unit's last inserted pattern (by start), so the whole pattern lies in the window.
Vertical scales are per panel (no ticks). Style: degradx.viz.style.
"""
import numpy as np
import matplotlib.pyplot as plt
from degradx.viz import style
from degradx.generator.generate import Profile
from degradx.targets.decomposable import TargetSpec, unit_targets

import diagram_inputs as D

style.apply()

DS = D.FORM_KEY
prof = D.profile_json(DS)
unit, T_med = D.illustrated_unit()
L, h = D.window()
W = D.weightings()
CH_P = D.pattern_channel()               # capacity
CH_R = "charge_time"                      # right column
CH_N = "mean_discharge_voltage"           # paired with CH_R in (c)
ci = {c: unit.channels.index(c) for c in (CH_P, CH_R, CH_N)}
t = np.arange(1, unit.T + 1)
x = unit.x
delta = float(prof["v2"]["offsets_all_fitting_units"][unit.source_unit][CH_R])
chans = prof["estimated_from_data"]["E4_channel_covariance"]["channels"]
r_fit = float(prof["v2"]["within_unit_correlation"][chans.index(CH_R)][chans.index(CH_N)])
with_types = [D.label(p) for p in D.profiles() if D.enabled_pattern_types(p)]
without = [D.label(p) for p in D.profiles() if not D.enabled_pattern_types(p)]
types = D.enabled_pattern_types(DS)

# ground truth of one window (exact construction of the benchmark)
P = Profile.from_json(prof, np.array([prof["derived"]["null_permuted_source_values"]["median"]]))
spec = TargetSpec.build(P, D.declared()["target"]["weights"]["beta"]["value"], L, h)
last = max(unit.patterns, key=lambda q: q["start"])
end = int(last["start"] + last["duration"] - 1)
assert end >= L
gt = unit_targets(unit, spec, W["primary"], ends=np.array([end]))
graded, sparse = gt["graded"][0], gt["sparse"][0]       # (L, C)
u = np.arange(1, L + 1)

fig = plt.figure(figsize=(3.95, 3.72))
gs = fig.add_gridspec(6, 2, height_ratios=[1, 1, 1, 1, 0.42, 1.05], hspace=0.38, wspace=0.08,
                      left=0.10, right=0.99, top=0.95, bottom=0.08)
ax = {}
for col in range(2):
    for row in range(4):
        ax[row, col] = fig.add_subplot(gs[row, col], sharex=ax[0, col] if row else None)
    ax[4, col] = fig.add_subplot(gs[5, col])

ANN = 7.3
GREY_LINE = "0.45"


def shade(a):
    a.axvspan(end - L + 0.5, end + 0.5, color="0.88", lw=0, zorder=0)


# (a) mean component
for col, c in enumerate((CH_P, CH_R)):
    a = ax[0, col]
    a.plot(t, unit.m_state[:, ci[c]], color="0.55", lw=0.9, ls="--")
    a.plot(t, unit.m[:, ci[c]], color="black", lw=1.1)
    a.set_title(D.channel_label(c), fontsize=8.5)
a = ax[0, 1]
j = int(0.30 * unit.T)
ms, mm = unit.m_state[j, ci[CH_R]], unit.m[j, ci[CH_R]]
a.annotate("", xy=(t[j], mm), xytext=(t[j], ms),
           arrowprops=dict(arrowstyle="-|>", color="black", lw=0.8, mutation_scale=6, shrinkA=0, shrinkB=0))
a.text(t[j] + 0.03 * unit.T, 0.5 * (ms + mm), r"$\delta_{c,i}$", fontsize=ANN, ha="left", va="center")
a.text(0.78 * unit.T, ms + 0.06 * (mm - ms), r"$\varphi_c(z_t)$", fontsize=ANN, ha="center", va="bottom",
       color="0.4")
lo = min(unit.m_state[:, ci[CH_R]].min(), unit.m[:, ci[CH_R]].min())
hi = max(unit.m_state[:, ci[CH_R]].max(), unit.m[:, ci[CH_R]].max())
a.set_ylim(lo - 0.08 * (hi - lo), hi + 0.12 * (hi - lo))

# (b) inserted patterns
a = ax[1, 0]
a.plot(t, unit.p, color="black", lw=1.0)
a.text(0.98, 0.92, f"{', '.join(with_types)}: {', '.join(types)} type\n{', '.join(without)}: zero",
       transform=a.transAxes, fontsize=ANN, ha="right", va="top", linespacing=1.2)
a.set_ylim(-0.08 * unit.p.max(), 1.15 * unit.p.max())
a = ax[1, 1]
a.axhline(0, color="black", lw=1.0)
a.text(0.98, 0.90, "none on this channel", transform=a.transAxes, fontsize=ANN, ha="right", va="top")
a.set_ylim(-0.08, 1.15)

# (c) noise, standardised per channel over the unit
a = ax[2, 0]
e = unit.eps[:, ci[CH_P]]
a.plot(t, e / e.std(), color=GREY_LINE, lw=0.45)
a = ax[2, 1]
for c, col, lw in ((CH_N, "0.6", 0.45), (CH_R, "black", 0.45)):
    e = unit.eps[:, ci[c]]
    a.plot(t, e / e.std(), color=col, lw=lw)
a.text(1.0, 1.02, rf"$r = {r_fit:.2f}$", transform=a.transAxes, fontsize=ANN, ha="right", va="bottom")

# (d) observation
for col, c in enumerate((CH_P, CH_R)):
    a = ax[3, col]
    a.plot(t, x[:, ci[c]], color="black", lw=0.5)
    a.set_xlabel(r"position $t$", fontsize=8.5, labelpad=1.5)
for row in range(4):
    for col in range(2):
        shade(ax[row, col])

# (e) attribution ground truth of the shaded window
for col, c in enumerate((CH_P, CH_R)):
    a = ax[4, col]
    g = graded[:, ci[c]]
    a.fill_between(u, 0, g, step="mid", color=style.FILL, lw=0)
    a.step(u, g, where="mid", color=GREY_LINE, lw=0.7)
    s = sparse[:, ci[c]]
    nz = np.flatnonzero(np.abs(s) > 0)
    for k in nz:
        a.plot([u[k], u[k]], [0, s[k]], color="black", lw=1.0)
    if nz.size:
        a.plot(u[nz], s[nz], ls="none", marker="o", ms=2.0, mfc="white", mec="black", mew=0.8)
    a.axhline(0, color="0.6", lw=0.6)
    vals = np.concatenate([g, s, [0.0]])
    span = vals.max() - vals.min()
    a.set_ylim(vals.min() - 0.12 * span, vals.max() + 0.12 * span)
    a.set_xlim(0.3, L + 0.7)
    a.set_xticks([1, L // 2, L])

labels = [r"(a) $m_{t,c}$", r"(b) $\Sigma_k\,p_{k,t,c}$", r"(c) $\varepsilon_{t,c}$", r"(d) $x_{t,c}$",
          r"(e) $\phi^{\star}_{u,c}$"]
for row in range(5):
    for col in range(2):
        a = ax[row, col]
        a.set_yticks([])
        style.despine(a)
        a.tick_params(labelsize=7.5)
        if row < 3:
            plt.setp(a.get_xticklabels(), visible=False)
    ax[row, 0].set_ylabel(labels[row], fontsize=8.5)
for col in range(2):
    ax[0, col].set_xlim(0, unit.T + 5)
bb0, bb1 = ax[4, 0].get_position(), ax[4, 1].get_position()
fig.text(0.5 * (bb0.x0 + bb1.x1), bb0.y0 - 0.062, r"position $u$ in the shaded window", fontsize=8.5,
         ha="center", va="top")

out = D.save(fig, "fig_generator")
print(f"{out}: unit {unit.index} (source {unit.source_unit}) T={unit.T} (median {T_med:g}) patterns "
      f"{[(q['start'], q['duration'], round(q['amplitude_Ah'] * 1e3, 2)) for q in unit.patterns]} delta={delta:.3f} "
      f"window ends {end}; r_fit={r_fit:.3f}; unit noise r={np.corrcoef(unit.eps[:, ci[CH_R]], unit.eps[:, ci[CH_N]])[0, 1]:.3f}; "
      f"printed scale {style.printed_scale(str(out), 0.6):.3f}")
