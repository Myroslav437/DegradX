"""D04 harness: family selection when candidates are close and when a family is not identifiable.

For every fitting unit reaching EOL (S3 split and fits), per family: CV-RMSE (from S3), fraction of units with a parameter
at a bound, and T reproduction: the first position at which the family's fitted trajectory reaches z >= 1, compared with
the unit's measured T (|T_fit - T| / T). Options:
  a  declared rule only (lowest median CV-RMSE, 5% simplicity margin)
  b  a + a family with parameters at a bound in > 20% of units (the declared S3 sanity threshold) is not eligible
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from degradx.fitting.families import FAMILIES, SIMPLICITY_ORDER, fit_family

ROOT = Path(__file__).resolve().parents[3]
QNOM = {"MATR": 1.1, "HUST": 1.1, "NASA_PCoE": 2.0}
out = {}
for ds, qn in QNOM.items():
    u = pd.read_csv(ROOT / f"artifacts/s3_fit_profiles/tables/units_{ds}.csv")
    r = u[u["reaches_eol"]].copy()
    prof = json.loads((ROOT / f"artifacts/s3_fit_profiles/profiles/{ds}.json").read_text())
    import pickle  # noqa
    # refit per family on the same series to get parameters for every family (S3 table stores only the selected family's)
    from degradx.data.audit import CleaningRule, clean_capacity
    from degradx.generator.state import spec_from_declarations, unit_state
    from degradx.utils.config import load_declarations
    decl = load_declarations()
    spec = spec_from_declarations(decl, qn)
    df = pd.read_csv(ROOT / f"data/processed/cycle_tables/{ds}.csv.gz", low_memory=False)
    rule = CleaningRule("D12", isolated_excursion_frac=0.05, drop_recovered_collapse=True)
    stats = {n: {"at_bound": 0, "T_rel_err": [], "cv": float(np.nanmedian(r[f"cv_rmse_{n}"]))} for n in FAMILIES}
    for cid in r["cell_id"]:
        d = clean_capacity(df[df["cell_id"] == cid], "capacity_cycler_Ah", rule, qn)
        q = d["capacity_cycler_Ah"].to_numpy(float)
        st = unit_state(q, spec)
        pos = np.arange(1, len(q) + 1, dtype=float)[st.t1 - 1:st.T]
        y = q[st.t1 - 1:st.T] / st.q1
        for n in FAMILIES:
            f = fit_family(n, pos, y)
            stats[n]["at_bound"] += len(f.at_bound) > 0
            long = np.arange(st.t1, 3 * st.T + 1, dtype=float)
            zf = (1 - FAMILIES[n](f.params, long)) * st.q1 / st.denominator
            hit = np.flatnonzero(zf >= 1)
            Tf = long[hit[0]] if hit.size else np.inf
            stats[n]["T_rel_err"].append(abs(Tf - st.T) / st.T)
    res = {}
    for n in FAMILIES:
        e = np.array(stats[n]["T_rel_err"])
        res[n] = {"median_cv_rmse": stats[n]["cv"], "frac_units_at_bound": stats[n]["at_bound"] / len(r),
                  "T_rel_err_median": float(np.median(e)), "T_rel_err_p90": float(np.quantile(e, 0.9)), "T_not_reached": int(np.isinf(e).sum())}
    def choose(eligible):
        med = {n: res[n]["median_cv_rmse"] for n in eligible}
        best = min(med, key=med.get)
        within = [n for n in SIMPLICITY_ORDER if n in med and med[n] <= med[best] * 1.05]
        return within[0]
    res["choice_a"] = choose(list(FAMILIES))
    res["choice_b"] = choose([n for n in FAMILIES if res[n]["frac_units_at_bound"] <= 0.2] or list(FAMILIES))
    res["units"] = int(len(r))
    out[ds] = res
    print(ds, json.dumps(res), flush=True)
Path(__file__).with_name("result.json").write_text(json.dumps(out, indent=1))
