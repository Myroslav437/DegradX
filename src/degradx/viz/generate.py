"""S06 figures: Figure 3/4 layouts on generated units, generated-vs-measured overlay (paper Figure 6), rho sensitivity."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from degradx.generator.generate import generate_unit  # noqa: E402
from degradx.targets.decomposable import WEIGHTINGS, unit_targets  # noqa: E402
from degradx.viz import style  # noqa: E402

LABEL = {"MATR": "MATR", "HUST": "HUST", "TRI_FORMATION": "FORM"}


def figure3_layout(P):
    """Paper Fig. 3 layout from MATR fitted parameters: two units at different paces, the same mappings, their mean components."""
    style.apply()
    Ts = np.array([u["T"] for u in P.theta_units])
    iA, iB = int(np.argsort(Ts)[len(Ts) // 5]), int(np.argsort(Ts)[4 * len(Ts) // 5])
    uA = generate_unit(P, 0, 0, patterns_on=False, overrides={"theta_unit": iA})
    uB = generate_unit(P, 0, 1, patterns_on=False, overrides={"theta_unit": iB})
    chans = [c for c in ("capacity", "internal_resistance", "charge_time") if c in P.channels]
    ls = {"capacity": "-", "internal_resistance": "--", "charge_time": "-."}
    names = {"capacity": "capacity", "internal_resistance": "internal resistance", "charge_time": "charge time"}
    fig, axes = plt.subplots(1, 3, figsize=(style.TEXTWIDTH_IN, 1.9))
    ax = axes[0]
    ax.plot(np.arange(1, uA.T + 1), uA.z, color="black", lw=1.3)
    ax.plot(np.arange(1, uB.T + 1), uB.z, color=style.MEASURED, lw=1.3, ls="--")
    ax.set_title("(a) degradation state", fontsize=8.5, loc="left")
    ax.set_xlabel(r"position $t$")
    ax.set_ylabel(r"$z_t$")
    ax = axes[1]
    zz = np.linspace(0, 1, 200)
    for c in chans:
        ax.plot(zz, P.mappings[c](zz) / P.mappings[c](0.0), color="black", lw=1.2, ls=ls[c], label=names[c])
    ax.set_title("(b) channel mappings", fontsize=8.5, loc="left")
    ax.set_xlabel(r"$z$")
    ax.set_ylabel(r"$\varphi_c(z)/\varphi_c(0)$")
    ax.legend(frameon=False, fontsize=6.5)
    ax = axes[2]
    for c in chans:
        ci = P.channels.index(c)
        ax.plot(np.arange(1, uA.T + 1), uA.m[:, ci] / P.mappings[c](0.0), color="black", lw=1.1, ls=ls[c])
        ax.plot(np.arange(1, uB.T + 1), uB.m[:, ci] / P.mappings[c](0.0), color=style.MEASURED, lw=1.1, ls=ls[c])
    ax.set_title("(c) mean components", fontsize=8.5, loc="left")
    ax.set_xlabel(r"position $t$")
    ax.set_ylabel(r"$m_{t,c}/\varphi_c(0)$")
    ax.legend(handles=[Line2D([], [], color="black", lw=1.1, label=f"unit A (T={uA.T})"),
                       Line2D([], [], color=style.MEASURED, lw=1.1, label=f"unit B (T={uB.T})")], frameon=False, fontsize=6.5)
    for a in axes:
        style.despine(a)
    fig.suptitle("Mean component from fitted MATR parameters (two resampled units, shared mappings)", fontsize=8)
    fig.tight_layout()
    return fig


def weightings_check(spec):
    style.apply()
    fig, ax = plt.subplots(figsize=(2.6, 1.8))
    u = np.arange(1, spec.L + 1)
    ax.plot(u, spec.pi["recency"], color="black", lw=1.4, label="recency (default)")
    ax.plot(u, spec.pi["uniform"], color="black", lw=1.0, ls="--", label="uniform")
    top = 1.34 * spec.pi["recency"].max()
    ax.plot([spec.L, spec.L], [0, top], color=style.GREY, lw=1.0, ls=":", label="final position (= 1)")
    ax.set_ylim(0, top)
    ax.set_xlabel("position within window $u$")
    ax.set_ylabel(r"position profile $\pi_u$")
    ax.legend(frameon=False, fontsize=6.5, loc="upper left")
    style.despine(ax)
    fig.tight_layout()
    return fig


def overlay_measured_generated(ds, P, units, df, split, decl, q_nom):
    """Paper Fig. 6 panel: measured capacity trajectories (grey) and generated units (black), with z = 0 and z = 1 marked."""
    from degradx.data.audit import CleaningRule, clean_capacity

    dd = decl["declared_by_design"]
    rule = CleaningRule("D12", **dd["capacity_series"]["cleaning_rule"]["params"])
    style.apply()
    fig, ax = plt.subplots(figsize=(style.TEXTWIDTH_IN / 3 + 0.3, 2.1))
    for cid in split["cell_id"]:
        d = clean_capacity(df[df["cell_id"] == cid], "capacity_cycler_Ah", rule, q_nom)
        ax.plot(d["position"], d["capacity_cycler_Ah"], color=style.MEASURED_BUNDLE, lw=style.LW_THIN, zorder=1)
    for u in units[:25]:
        ax.plot(np.arange(1, u.T + 1), u.x[:, 0], color=style.GENERATED, lw=0.5, zorder=2)
    q1 = P.mappings["capacity"](0.0)
    for val, lab in ((q1, r"$z=0$"), (P.rho * q_nom, r"$z=1$")):
        ax.axhline(val, color=style.REFERENCE, lw=style.LW_THIN, ls="--", zorder=0)
        ax.text(ax.get_xlim()[1] if False else 0.99, val, lab, transform=ax.get_yaxis_transform(), ha="right", va="bottom", fontsize=6.5, color=style.GREY)
    ax.set_title(LABEL[ds], fontsize=8.5)
    ax.set_xlabel(r"position $t$ (cycle)")
    ax.set_ylabel("capacity [Ah]")
    lo, hi = 0.85 * P.rho * q_nom, 1.1 * q1
    ax.set_ylim(lo, hi)
    ax.legend(handles=[Line2D([], [], color=style.MEASURED_BUNDLE, lw=1, label=f"measured ({len(split)} units)"),
                       Line2D([], [], color=style.GENERATED, lw=1, label="generated (25 units)")], frameon=False, fontsize=6.5, loc="lower left")
    style.despine(ax)
    fig.tight_layout()
    return fig


def rho_sensitivity(rho: pd.DataFrame):
    style.apply()
    ds_list = list(rho["dataset"].unique())
    fig, axes = plt.subplots(1, len(ds_list), figsize=(style.TEXTWIDTH_IN, 2.0), squeeze=False)
    for ax, ds in zip(axes[0], ds_list):
        r = rho[rho["dataset"] == ds]
        for definition, lsty, mk in (("r2", "-", "o"), ("r1", "--", "s")):
            rr = r[(r["definition"] == definition) & r["T_median"].notna()]
            ax.errorbar(rr["rho"], rr["T_median"], yerr=[rr["T_median"] - rr["T_q25"], rr["T_q75"] - rr["T_median"]], ls=lsty, marker=mk, ms=3,
                        color="black" if definition == "r2" else style.MEASURED, capsize=2, lw=1, label=f"{definition}")
        ax.set_title(LABEL[ds], fontsize=8.5)
        ax.set_xlabel(r"EOL fraction $\rho$")
        style.despine(ax)
    axes[0][0].set_ylabel("T of fitted units (median, IQR)")
    axes[0][0].legend(frameon=False, fontsize=6.5, title="EOL definition", title_fontsize=6.5)
    fig.tight_layout()
    return fig
