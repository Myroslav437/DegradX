"""D13 harness: EOL attainment when records are truncated at the stopping threshold.

Options (capacity = cycler capacity, D11; no glitch cleaning here beyond degenerate cycles; Eq. 3 r2 with k=20):
  a  strict: T = min{t : z_t >= 1}                                   (declarations r2 as written)
  b  state tolerance: T = min{t : z_t >= 1 - eps}, eps = 0.02
  c  record-end rule: T = min{t : z_t >= 1}; if never, T = N when the mean raw capacity of the last 5 recorded cycles
     lies within tau = 0.01 * q_nom of rho * q_nom (the record ends at the dataset's own stopping rule)
  d  rho = 0.85, strict
Metrics per dataset: units reaching EOL; |T - documented cycle life| where documented (HUST ESI Table S1, MATR
cycle_life field; NASA has none); z at T.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from degradx.generator.state import StateSpec, unit_state

ROOT = Path(__file__).resolve().parents[3]
TAB = ROOT / "data/processed/cycle_tables"
QNOM = {"MATR": 1.1, "HUST": 1.1, "NASA_PCoE": 2.0}
tab1 = pd.read_csv(ROOT / "configs/reference_facts/hust_tableS1.csv").set_index("channel")
res, per_unit = {}, []
for ds, qn in QNOM.items():
    df = pd.read_csv(TAB / f"{ds}.csv.gz", low_memory=False)
    df = df[~df["degenerate"]]
    stats = {o: {"reach": 0, "diffs": [], "zT": []} for o in "abcd"}
    n_units = 0
    for cid, g in df.groupby("cell_id"):
        q = g["capacity_cycler_Ah"].to_numpy(float)
        if len(q) < 21:
            continue
        n_units += 1
        spec = StateSpec(rho=0.8, q_nom=qn, k=20, margin=0.05, sg_window=11, sg_polyorder=2)
        st = unit_state(q, spec)
        if ds == "HUST":
            ch = cid.split("_", 1)[1]
            doc = int(tab1.at[ch, "cycle_life"]) - (2 if ch == "7-5" else 0)
        elif ds == "MATR":
            doc = float(g["cycle_life"].iloc[0])
        else:
            doc = np.nan
        Ts = {}
        Ts["a"] = st.T
        if not st.excluded_by_guard:
            hit = np.flatnonzero(st.z >= 1 - 0.02)
            Ts["b"] = int(hit[0]) + 1 if hit.size else None
            Ts["c"] = st.T if st.T is not None else (len(q) if abs(q[-5:].mean() - 0.8 * qn) <= 0.01 * qn else None)
        else:
            Ts["b"] = Ts["c"] = None
        Ts["d"] = unit_state(q, StateSpec(**{**spec.__dict__, "rho": 0.85})).T
        row = {"dataset": ds, "cell_id": cid, "N": len(q), "documented": doc, **{f"T_{o}": Ts[o] for o in "abcd"}}
        per_unit.append(row)
        for o in "abcd":
            if Ts[o] is not None:
                stats[o]["reach"] += 1
                if np.isfinite(doc) and o != "d":
                    stats[o]["diffs"].append(abs(Ts[o] - doc))
                zz = st.z if o != "d" else unit_state(q, StateSpec(**{**spec.__dict__, "rho": 0.85})).z
                stats[o]["zT"].append(float(zz[Ts[o] - 1]))
    res[ds] = {"units": n_units, **{o: {"reach": s["reach"], "median_abs_T_minus_documented": float(np.median(s["diffs"])) if s["diffs"] else None,
                                         "p90_abs_T_minus_documented": float(np.quantile(s["diffs"], 0.9)) if s["diffs"] else None,
                                         "documented_compared": len(s["diffs"]),
                                         "z_at_T_min": float(np.min(s["zT"])) if s["zT"] else None} for o, s in stats.items()}}
pd.DataFrame(per_unit).to_csv(Path(__file__).with_name("per_unit.csv"), index=False)
Path(__file__).with_name("result.json").write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
