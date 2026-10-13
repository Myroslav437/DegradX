"""Construction of the mean component (Figure 3; brief v2.1 W9).

v2.1: drawn from the FORM profile (artifacts/v2.1/w3_fit_profiles/profiles/TRI_FORMATION.json) instead of
illustrative curves. Shared mappings plus per-unit offsets (X2): m_{t,c} = phi_c(z_t) + delta_{c,i}.

  units A, B  the fitting units at the 10th and 90th percentile (nearest rank) of the charge-time offset
              (v2.offsets_all_fitting_units); their degradation state z_t is computed from each unit's fitted theta
              (E1_theta_distribution.per_unit) by the generator's state function, i.e. the state a generated unit
              drawing that fitting unit receives, up to its EOL position T
  (b)         the fitted shared mappings phi_c (E3_channel_mappings) of the weighted channels
              (derived.channel_roles.weighted), each scaled to its change from the pristine level to EOL,
              (phi_c(z) - phi_c(0)) / (phi_c(1) - phi_c(0))
  (c)         charge time of units A and B: phi_c(z_t) (dotted, the shared part) and phi_c(z_t) + delta_{c,i} (solid)
Style: degradx.viz.style.
"""
import re
import textwrap

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from degradx.viz import style

import diagram_inputs as D

style.apply()

UNIT_B = "0.55"  # second unit, as in v2
DS = D.FORM_KEY
prof = D.profile_json(DS)
maps = D.mappings(DS)
weighted = prof["derived"]["channel_roles"]["weighted"]
off_all = prof["v2"]["offsets_all_fitting_units"]
CH = "charge_time"                      # the channel whose offset sets the rule and is drawn in (c)
unit_rule = D.offset_percentile_units(CH, (10, 90))
units = {name: cid for name, cid in zip(("A", "B"), unit_rule)}
z_of = {name: D.state_of_fitting_unit(cid, DS) for name, cid in units.items()}
unit_of_ch = re.search(r"\[(.*?)\]", D.declared()["channels"]["candidates"][CH]["derivation"]).group(1)
T_max = max(len(z) for z in z_of.values())

fig, axes = plt.subplots(1, 3, figsize=(5.75, 1.75), gridspec_kw=dict(width_ratios=[1.0, 1.2, 1.0]))

# --- (a) degradation state -------------------------------------------------------------------------------------
ax = axes[0]
sty = {"A": dict(color="black", ls="-"), "B": dict(color=UNIT_B, ls="--")}
for name, z in z_of.items():
    t = np.arange(1, len(z) + 1)
    ax.plot(t, z, lw=1.3, **sty[name])
zA, zB = z_of["A"], z_of["B"]
iB = int(np.searchsorted(zB, 0.62))
ax.text(iB - 0.02 * T_max, 0.62, "unit B", fontsize=7.5, ha="right", va="center", color=UNIT_B)
iA = int(np.searchsorted(zA, 0.30))
ax.text(iA + 0.03 * T_max, 0.27, "unit A", fontsize=7.5, ha="left", va="center")
ax.set_title("(a) degradation state", fontsize=8.5, loc="left")
ax.set_xlabel(r"position $t$")
ax.set_ylabel(r"$z_t$")
ax.set_xlim(0, 1.04 * T_max)
ax.set_ylim(-0.03, 1.08)
ax.set_yticks([0, 0.5, 1.0])

# --- (b) shared mappings ---------------------------------------------------------------------------------------
ax = axes[1]
zz = np.linspace(0, 1, 201)
LS = ["-", "--", "-."]
for k, c in enumerate(weighted):
    f = maps[c]
    ax.plot(zz, (f(zz) - f(0.0)) / (f(1.0) - f(0.0)), color="black", lw=1.1, ls=LS[k],
            label=textwrap.fill(D.channel_label(c), 11))
ax.set_title("(b) shared mappings", fontsize=8.5, loc="left")
ax.set_xlabel(r"$z$")
ax.set_ylabel(r"$\varphi_c(z)$, scaled")
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.05, 1.12)
ax.set_xticks([0, 0.5, 1.0])
ax.set_yticks([0, 0.5, 1.0])
ax.legend(loc="upper left", frameon=False, handlelength=1.4, handletextpad=0.5, borderpad=0.1, labelspacing=0.15,
          fontsize=7)

# --- (c) mean components of one channel: shared part + per-unit offset -----------------------------------------
ax = axes[2]
f = maps[CH]
arrow_at = {"A": 0.55, "B": 0.30}    # fraction of each unit's T at which its offset is marked
for name, z in z_of.items():
    t = np.arange(1, len(z) + 1)
    shared = f(z)
    delta = float(off_all[units[name]][CH])
    col = sty[name]["color"]
    ax.plot(t, shared, color=col, lw=0.8, ls=":")
    ax.plot(t, shared + delta, color=col, lw=1.1, ls="-")
    j = int(arrow_at[name] * (len(z) - 1))
    ax.annotate("", xy=(t[j], shared[j] + delta), xytext=(t[j], shared[j]),
                arrowprops=dict(arrowstyle="-|>", color=col, lw=0.8, mutation_scale=6, shrinkA=0, shrinkB=0))
    ax.text(t[j] + 0.025 * T_max, shared[j] + 0.5 * delta, rf"$\delta_{{c,{name}}}$", fontsize=7.5,
            color=col, ha="left", va="center")
ax.set_title(f"(c) {D.channel_label(CH)}", fontsize=8.5, loc="left")
ax.set_xlabel(r"position $t$")
ax.set_ylabel(rf"$m_{{t,c}}$ [{unit_of_ch}]")
ax.set_xlim(0, 1.04 * T_max)
handles = [Line2D([], [], color="black", lw=1.1, label="unit A"),
           Line2D([], [], color=UNIT_B, lw=1.1, label="unit B"),
           Line2D([], [], color="black", lw=0.8, ls=":", label=r"$\varphi_c(z_t)$")]
ax.legend(handles=handles, loc="upper right", frameon=False, handlelength=1.5, borderpad=0.1, labelspacing=0.2,
          fontsize=7)

for ax in axes:
    style.despine(ax)

fig.subplots_adjust(wspace=0.50)
out = D.save(fig, "fig_mean_component")
print(f"{out}: units {units} T {{A: {len(zA)}, B: {len(zB)}}} offsets "
      f"{ {n: round(off_all[c][CH], 3) for n, c in units.items()} } printed scale "
      f"{style.printed_scale(str(out), 0.75):.3f}")
