"""D15 harness: where the EOL search starts.

Options (capacity = cycler (D11), cleaning = iso05_rc (D12 candidate), record-end rule tau=0.01 (D13)):
  a  T = min{t >= 1 : z_t >= 1}                  (implementation as written at S1)
  b  T = min{t >= t1 : z_t >= 1}, t1 = position of q1 (the fall is measured from q1)
  c  a, but units with T <= k are excluded as data failures
Metric: units with T <= k (=20), units reaching EOL, T of every unit whose value differs between options.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from degradx.data.audit import CleaningRule, clean_capacity
from degradx.generator.state import StateSpec, smooth, unit_state

ROOT = Path(__file__).resolve().parents[3]
QNOM = {"MATR": 1.1, "HUST": 1.1, "NASA_PCoE": 2.0}
rule = CleaningRule("iso05_rc", isolated_excursion_frac=0.05, drop_recovered_collapse=True)
out, diffs = {}, []
for ds, qn in QNOM.items():
    df = pd.read_csv(ROOT / f"data/processed/cycle_tables/{ds}.csv.gz", low_memory=False)
    spec = StateSpec(rho=0.8, q_nom=qn, k=20, margin=0.05, sg_window=11, sg_polyorder=2, record_end_tau=0.01)
    cnt = {"a_reach": 0, "a_T_le_k": 0, "b_reach": 0, "b_T_le_k": 0, "c_reach": 0, "units": 0}
    for cid, g in df.groupby("cell_id"):
        d = clean_capacity(g, "capacity_cycler_Ah", rule, qn)
        q = d["capacity_cycler_Ah"].to_numpy(float)
        if len(q) < 20:
            continue
        cnt["units"] += 1
        st = unit_state(q, spec)
        Ta = st.T
        qs = smooth(q, spec)
        t1 = int(np.argmax(qs[:20]))
        Tb = None
        if not st.excluded_by_guard:
            hit = np.flatnonzero(qs[t1:] <= 0.8 * qn)
            Tb = int(hit[0]) + t1 + 1 if hit.size else (len(q) if abs(q[-5:].mean() - 0.8 * qn) <= 0.01 * qn else None)
        Tc = Ta if (Ta is not None and Ta > 20) else None
        cnt["a_reach"] += Ta is not None; cnt["a_T_le_k"] += (Ta is not None and Ta <= 20)
        cnt["b_reach"] += Tb is not None; cnt["b_T_le_k"] += (Tb is not None and Tb <= 20)
        cnt["c_reach"] += Tc is not None
        if Ta != Tb:
            diffs.append({"dataset": ds, "cell_id": cid, "t1": t1 + 1, "T_a": Ta, "T_b": Tb, "q_first5": np.round(q[:5], 3).tolist()})
    out[ds] = cnt
Path(__file__).with_name("result.json").write_text(json.dumps({"counts": out, "differences": diffs}, indent=1))
print(json.dumps(out, indent=1)); print(pd.DataFrame(diffs).to_string())
