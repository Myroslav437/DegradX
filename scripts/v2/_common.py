"""Helpers shared by the v2 stage scripts (brief "DegradX v2"). v1 scripts are left untouched; these reproduce the v1
definitions they need (S3 scope and channel availability) without importing a stage script."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from degradx import ARTIFACTS_V2, CONFIG_DIR, DATA_DIR, DATA_V2
from degradx.fitting.profile import CHANNEL_COLUMNS

CANDIDATES = ["capacity", "charge_time", "mean_discharge_voltage", "internal_resistance", "temperature_mean"]
# dataset -> profile config stem under configs/profiles
PROFILE_CONFIG = {"MATR": "matr", "HUST": "hust"}


def register_profile(ds: str, stem: str) -> None:
    PROFILE_CONFIG[ds] = stem


def cycle_table(ds: str) -> pd.DataFrame:
    """v1 cycle tables (MATR, HUST) or the v2 third-profile table."""
    for root in (DATA_DIR / "processed" / "cycle_tables", DATA_V2 / "processed" / "cycle_tables"):
        f = root / f"{ds}.csv.gz"
        if f.exists():
            return pd.read_csv(f, low_memory=False)
    raise FileNotFoundError(f"no cycle table for {ds}")


def load_scope(ds: str, dd: dict) -> pd.DataFrame:
    df = cycle_table(ds)
    if ds == "MATR":
        batches = [f"{str(b)[:4]}-{str(b)[4:6]}-{str(b)[6:]}" for b in dd["datasets"]["matr_batches"]["value"]]
        df = df[df["batch"].isin(batches)]
    return df


def available_channels(df: pd.DataFrame) -> list[str]:
    """declarations channels.availability_rule (S3 definition): a candidate is used iff available in every unit."""
    nd = df[~df["degenerate"].astype(bool)]
    out = ["capacity"]
    for c in CANDIDATES[1:]:
        if CHANNEL_COLUMNS[c] not in nd:
            continue
        v = nd[CHANNEL_COLUMNS[c]]
        if c == "internal_resistance":
            v = v.where(v != 0)
        if (v.notna().groupby(nd["cell_id"]).mean() >= 0.5).all():
            out.append(c)
    return out


def q_nom_of(ds: str) -> float:
    from degradx.utils.config import load_yaml

    return float(load_yaml(CONFIG_DIR / "profiles" / f"{PROFILE_CONFIG[ds]}.yaml")["nominal_capacity_Ah"]["value"])


def v2_profile(ds: str) -> dict:
    return json.loads((ARTIFACTS_V2 / "v3_fit_profiles" / "profiles" / f"{ds}.json").read_text())


def v2_split(ds: str) -> pd.DataFrame:
    return pd.read_csv(ARTIFACTS_V2 / "v3_fit_profiles" / "tables" / f"split_{ds}.csv")


def channel_rule_v2(dd: dict):
    from degradx.fitting.profile import ChannelRule

    cr = dd["channel_series"]["cleaning_rule"]
    return ChannelRule(float(cr["frac"]), int(cr.get("max_run_v2", 1)))


def offsets_params(dd: dict) -> dict:
    e = dd["v2"]["per_unit_offsets"]["estimation"]
    return {"tol_frac": float(e["tolerance_frac"]), "max_iter": int(e["max_iterations"]), "min_readings": int(e["minimum_readings_n"]),
            "declared": e["convergence_tolerance"]}


def summarise(v) -> dict:
    v = np.asarray([x for x in v if x is not None and np.isfinite(x)], float)
    if not len(v):
        return {"n": 0}
    return {"n": int(len(v)), "median": float(np.median(v)), "q25": float(np.quantile(v, 0.25)), "q75": float(np.quantile(v, 0.75)),
            "p05": float(np.quantile(v, 0.05)), "p95": float(np.quantile(v, 0.95))}


def null_pool(ds: str, decl: dict) -> np.ndarray:
    """The null_permuted pool of a v2 profile: fitting-split charge-time readings over the fit range after D12/D17/D27,
    as V4 generates with (declarations channels.null.null_permuted). Its median is the channel's pristine reference
    point, which V8/V9 use as the attribution baseline; a dummy pool would set it to 0."""
    from degradx.data.audit import CleaningRule
    from degradx.fitting.profile import prepare_units
    from degradx.generator.state import spec_from_declarations

    dd = decl["declared_by_design"]
    q_nom = q_nom_of(ds)
    split = v2_split(ds)
    df = load_scope(ds, dd)
    units = prepare_units(df, split.loc[split["split"] == "fitting", "cell_id"], q_nom, spec_from_declarations(decl, q_nom),
                          CleaningRule("D12", **dd["capacity_series"]["cleaning_rule"]["params"]), ["capacity", "charge_time"], channel_rule_v2(dd))
    pool = np.concatenate([u.channels["charge_time"][u.fit_start - 1:u.fit_end] for u in units])
    return pool[np.isfinite(pool)]
