"""S1 figures: raw capacity trajectories, per-unit cycle counts, channel availability, converter validation."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from degradx.viz import style  # noqa: E402

DATASETS = ("MATR", "HUST", "NASA_PCoE")
LABEL = {"MATR": "MATR", "HUST": "HUST", "NASA_PCoE": "NASA PCoE"}


def capacity_trajectories(tables: dict[str, pd.DataFrame], column: str = "capacity_cycler_Ah"):
    style.apply()
    fig, axes = plt.subplots(1, len(tables), figsize=(style.TEXTWIDTH_IN, 2.2))
    for ax, (ds, df) in zip(np.atleast_1d(axes), tables.items()):
        for _, g in df.groupby("cell_id", sort=False):
            ax.plot(g["position"], g[column], color=style.MEASURED_BUNDLE, lw=style.LW_THIN)
        q = df["nominal_capacity_Ah"].iloc[0]
        ax.axhline(0.8 * q, color=style.REFERENCE, lw=style.LW_THIN, ls="--")
        ax.set_ylim(0.0, 1.4 * q)  # a few single-cycle glitches exceed this (counted in tables/summary.json)
        ax.set_title(f"{LABEL[ds]} ({df['cell_id'].nunique()} units)")
        ax.set_xlabel("position (cycle)")
        style.despine(ax)
    np.atleast_1d(axes)[0].set_ylabel("discharge capacity [Ah]")
    fig.text(0.99, 0.01, "dashed: 80% of nominal capacity; axis cut at 1.4x nominal", ha="right", va="bottom", fontsize=7, color=style.GREY)
    fig.tight_layout()
    return fig


def cycle_counts(tables: dict[str, pd.DataFrame]):
    style.apply()
    fig, axes = plt.subplots(1, len(tables), figsize=(style.TEXTWIDTH_IN, 2.0))
    for ax, (ds, df) in zip(np.atleast_1d(axes), tables.items()):
        n = df.groupby("cell_id").size().sort_values().to_numpy()
        ax.bar(np.arange(len(n)), n, color=style.MEASURED, width=0.8)
        ax.set_title(LABEL[ds])
        ax.set_xlabel("unit (sorted by length)")
        style.despine(ax)
    np.atleast_1d(axes)[0].set_ylabel("stored cycles per unit")
    fig.tight_layout()
    return fig


def channel_availability(avail: pd.DataFrame):
    """``avail``: index = channel, columns = dataset, values = fraction of units with the channel non-missing."""
    style.apply()
    fig, ax = plt.subplots(figsize=(3.4, 0.35 * len(avail) + 0.8))
    im = ax.imshow(avail.to_numpy(dtype=float), cmap="Greys", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(avail.shape[1]), [LABEL.get(c, c) for c in avail.columns])
    ax.set_yticks(range(avail.shape[0]), avail.index)
    for i in range(avail.shape[0]):
        for j in range(avail.shape[1]):
            v = avail.iat[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7, color="white" if v > 0.5 else "black")
    cb = fig.colorbar(im, ax=ax, fraction=0.05)
    cb.set_label("fraction of units with channel")
    ax.tick_params(length=0)
    fig.tight_layout()
    return fig


def capacity_source_agreement(tables: dict[str, pd.DataFrame]):
    style.apply()
    fig, axes = plt.subplots(1, len(tables), figsize=(style.TEXTWIDTH_IN, 2.2))
    for ax, (ds, df) in zip(np.atleast_1d(axes), tables.items()):
        d = df[~df["degenerate"]]
        diff = (d["capacity_integrated_Ah"] - d["capacity_cycler_Ah"]) * 1000
        lim = float(np.nanquantile(diff.abs(), 0.99)) * 1.1 + 1.0
        ax.hist(diff.dropna().clip(-lim, lim), bins=60, color=style.MEASURED)
        ax.axvline(0, color=style.REFERENCE, lw=style.LW_THIN)
        ax.set_title(f"{LABEL[ds]}: median {np.nanmedian(diff):+.1f} mAh")
        ax.set_xlabel("integrated − cycler [mAh]")
        style.despine(ax)
    np.atleast_1d(axes)[0].set_ylabel("cycles")
    fig.tight_layout()
    return fig


def nasa_converter_check(raw_cycle: dict, conv_cycle, raw_caps: np.ndarray, conv_caps: np.ndarray, cell: str):
    """Raw .mat discharge operation vs the converted CycleData (discharge segment), and the capacity trajectory."""
    style.apply()
    fig, axes = plt.subplots(1, 4, figsize=(style.TEXTWIDTH_IN, 1.9))
    n_d = len(raw_cycle["Time"])
    t_conv = np.asarray(conv_cycle.time_in_s)[-n_d:]
    t_conv = t_conv - t_conv[0]
    for ax, key, attr, unit in zip(axes[:3], ("Voltage_measured", "Current_measured", "Temperature_measured"),
                                   ("voltage_in_V", "current_in_A", "temperature_in_C"), ("V", "A", "°C")):
        ax.plot(np.asarray(raw_cycle["Time"]) / 60, raw_cycle[key], color=style.MEASURED, lw=2.4, label="raw .mat")
        ax.plot(t_conv / 60, np.asarray(getattr(conv_cycle, attr))[-n_d:], color=style.GENERATED, lw=style.LW_THIN, ls="--",
                label="BatteryData")
        ax.set_xlabel("time in discharge [min]")
        ax.set_ylabel(f"{key.split('_')[0].lower()} [{unit}]")
        style.despine(ax)
    axes[0].legend(frameon=False)
    ax = axes[3]
    ax.plot(np.arange(1, len(raw_caps) + 1), raw_caps, color=style.MEASURED, lw=2.4, label="raw Capacity")
    ax.plot(np.arange(1, len(conv_caps) + 1), conv_caps, color=style.GENERATED, lw=style.LW_THIN, ls="--", label="converted")
    ax.set_xlabel("discharge (position)")
    ax.set_ylabel("capacity [Ah]")
    ax.legend(frameon=False, loc="lower left")
    style.despine(ax)
    fig.suptitle(f"NASA {cell}: converter output against raw file (first discharge)", fontsize=8)
    fig.tight_layout()
    return fig
