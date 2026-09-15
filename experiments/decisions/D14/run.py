"""D14 harness: MATR scope. Per-batch audit properties (from artifacts/s2_audit_datasets/tables/units.csv) and channel
availability, comparing (a) all four batches, (b) the three batches of Severson et al. 2019 (the cited dataset),
(c) the Severson-124 cell list (notebook exclusions)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
units = pd.read_csv(ROOT / "artifacts/s2_audit_datasets/tables/units.csv", low_memory=False)
units = units[units["dataset"] == "MATR"]
cyc = pd.read_csv(ROOT / "data/processed/cycle_tables/MATR.csv.gz", low_memory=False)
meta = cyc.groupby("cell_id").agg(batch=("batch", "first"), ir_zero_frac=("internal_resistance_ohm", lambda s: float((s == 0).mean())),
                                  temp_nan_frac=("temperature_mean_C", lambda s: float(s.isna().mean())),
                                  charge_policy=("charge_policy", "first"),
                                  charge_time_med=("charge_time_min", "median"), mdv_med=("mean_discharge_voltage_V", "median"))
u = units.merge(meta, left_on="cell_id", right_index=True)
# Severson notebook exclusions (docs/S0_RESEARCH/datasets.md §1.3): b1 unfinished cells and six b3 noisy/unfinished cells
sev_excl = {"MATR_b1c8", "MATR_b1c10", "MATR_b1c12", "MATR_b1c13", "MATR_b1c22", "MATR_b3c37", "MATR_b3c2", "MATR_b3c23", "MATR_b3c32", "MATR_b3c42", "MATR_b3c43"}
scopes = {"a_all_four": u, "b_severson_batches": u[u["batch"] != "2019-01-24"], "c_severson_124": u[(u["batch"] != "2019-01-24") & ~u["cell_id"].isin(sev_excl)]}
out = {}
for name, s in scopes.items():
    out[name] = {
        "cells": int(len(s)), "reach_eol": int(s["T"].notna().sum()),
        "ir_available_every_cell": bool((s["ir_zero_frac"] < 0.5).all()), "cells_ir_all_zero": int((s["ir_zero_frac"] > 0.99).sum()),
        "temperature_available_every_cell": bool((s["temp_nan_frac"] < 0.5).all()),
        "best_family_counts": s["best_family_in_sample"].value_counts().to_dict(),
        "residual_scale_mAh_median": float(s["residual_scale_Ah"].median() * 1000),
        "T_median": float(s["T"].median()), "T_iqr": [float(s["T"].quantile(0.25)), float(s["T"].quantile(0.75))],
        "positive_events_per_100": float(s["n_pos_k2.5_m2"].sum() / (s["fit_end"] - s["fit_start"] + 1).sum() * 100),
        "distinct_charge_policies": int(s["charge_policy"].nunique()),
    }
per_batch = u.groupby("batch").agg(cells=("cell_id", "size"), reach=("T", lambda x: int(x.notna().sum())), T_med=("T", "median"),
                                   resid_mAh=("residual_scale_Ah", lambda x: float(x.median() * 1000)), ir_zero=("ir_zero_frac", "mean"),
                                   charge_time_med=("charge_time_med", "median"), mdv_med=("mdv_med", "median"),
                                   pos_events=("n_pos_k2.5_m2", "sum"))
Path(__file__).with_name("result.json").write_text(json.dumps({"scopes": out, "per_batch": json.loads(per_batch.to_json(orient="index"))}, indent=1))
print(json.dumps(out, indent=1)); print(per_batch.round(4).to_string())
