"""Unit-level splits (paper l.247: all splits at the level of units; declarations statistics.splits.measured)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from degradx.utils.seeding import rng


def measured_split(units: pd.DataFrame, base_seed: int, dataset: str, fitting_fraction: float = 0.7) -> pd.DataFrame:
    """``units``: one row per eligible unit with columns cell_id, reaches_eol. Returns cell_id, split, reaches_eol.

    Stratified by EOL attainment; within each stratum round(fraction * n) units (at least 1 if the stratum is
    non-empty) go to the fitting split, drawn with the 'split' seed stream for this dataset.
    """
    g = rng(base_seed, "split", dataset)
    rows = []
    for reach, stratum in units.sort_values("cell_id").groupby("reaches_eol", sort=True):
        ids = stratum["cell_id"].to_numpy()
        n_fit = max(1, int(round(fitting_fraction * len(ids)))) if len(ids) else 0
        perm = g.permutation(len(ids))
        fit = set(ids[perm[:n_fit]])
        rows += [{"cell_id": c, "split": "fitting" if c in fit else "held_out", "reaches_eol": bool(reach)} for c in ids]
    return pd.DataFrame(rows).sort_values("cell_id").reset_index(drop=True)
