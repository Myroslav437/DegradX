"""D12 harness: which stored cycles enter the capacity series before smoothing and fitting.

Options (all drop degenerate cycles; capacity = cycler capacity (D11); record-end rule tau = 0.01 (D13)):
  none       no further rule
  iso05      + isolated single-position excursions > 0.05 q_nom from the centred 11-position rolling median
  iso10      + the same at 0.10 q_nom
  iso05_rc   + iso05 and readings < 0.5 q_nom that the record later recovers from (>= 0.8 q_nom)
Metrics per dataset: cycles/units affected, guard exclusions, EOL attainment, monotone fraction, detected events at
(k=2.5, m=2), residual scale, NASA B0005/6/7/18 positive events, units whose q1 moves > 0.01 q_nom vs 'none'.
"""
import json
import sys
from functools import partial
from multiprocessing import get_context
from pathlib import Path

import numpy as np
import pandas as pd

from degradx.data.audit import CleaningRule, audit_unit
from degradx.generator.state import spec_from_declarations
from degradx.utils.config import load_declarations

ROOT = Path(__file__).resolve().parents[3]
decl = load_declarations()
dd = decl["declared_by_design"]
QNOM = {"MATR": 1.1, "HUST": 1.1, "NASA_PCoE": 2.0}
OPTIONS = {
    "none": CleaningRule("none"),
    "iso05": CleaningRule("iso05", isolated_excursion_frac=0.05),
    "iso10": CleaningRule("iso10", isolated_excursion_frac=0.10),
    "iso05_rc": CleaningRule("iso05_rc", isolated_excursion_frac=0.05, drop_recovered_collapse=True),
}
results, per_unit = {}, []
for ds, qn in QNOM.items():
    df = pd.read_csv(ROOT / f"data/processed/cycle_tables/{ds}.csv.gz", low_memory=False)
    groups = [g for _, g in df.groupby("cell_id", sort=True)]
    spec = spec_from_declarations(decl, qn)
    base_q1 = None
    for name, rule in OPTIONS.items():
        fn = partial(audit_unit, column="capacity_cycler_Ah", rule=rule, q_nom=qn, decl=decl, rho_grid=[0.8], k_grid=[20],
                     sweep_k=[2.5], sweep_m=[2], k_default=2.5, m_default=2, mono_tol=0.01, spec_base=spec)
        with get_context("fork").Pool(12) as pool:
            recs = pool.map(fn, groups, chunksize=2)
        for r in recs:
            r.pop("_trace", None)
            pats = r.pop("patterns", [])
            r["option"], r["dataset"] = name, ds
            per_unit.append(r)
        u = pd.DataFrame(recs)
        ok = u[~u["too_short"].astype(bool)]
        q1 = ok.set_index("cell_id")["q1"]
        if name == "none":
            base_q1 = q1
        moved = int(((q1 - base_q1.reindex(q1.index)).abs() > 0.01 * qn).sum())
        nasa_core = ok[ok["cell_id"].isin(["NASA_B0005", "NASA_B0006", "NASA_B0007", "NASA_B0018"])]
        results.setdefault(ds, {})[name] = {
            "cycles_dropped": int(u["n_dropped_by_cleaning"].sum()), "units_with_dropped": int((u["n_dropped_by_cleaning"] > 0).sum()),
            "too_short": int(u["too_short"].sum()), "guard_excluded": int(ok["excluded_by_guard"].sum()),
            "reach_eol": int(ok["T"].notna().sum()), "monotone_fraction": float(ok["monotone_within_tol"].mean()),
            "positive_events": int(ok["n_pos_k2.5_m2"].sum()), "negative_events": int(ok["n_neg_k2.5_m2"].sum()),
            "units_with_positive": int((ok["n_pos_k2.5_m2"] > 0).sum()),
            "median_residual_scale_mAh": float(ok["residual_scale_Ah"].median() * 1000),
            "median_best_rmse_rel": float(ok[[c for c in ok if c.startswith("rmse_")]].min(axis=1).median()),
            "q1_moved_vs_none": moved,
            "nasa_core_positive_events": int(nasa_core["n_pos_k2.5_m2"].sum()) if ds == "NASA_PCoE" else None,
        }
        print(ds, name, results[ds][name], flush=True)
pd.DataFrame(per_unit).to_csv(Path(__file__).with_name("per_unit.csv"), index=False)
Path(__file__).with_name("result.json").write_text(json.dumps(results, indent=1))
