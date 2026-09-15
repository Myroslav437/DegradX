"""D11 harness: capacity source (integrated I dt vs cycler-reported) against documented end of life.

HUST: documented cycle life (ESI Table S1) is the last recorded cycle, and cycling stopped when "the maximum capacity
first reached 80% of nominal". MATR: file field cycle_life (cycles until 0.88 Ah). For each unit, the first raw
crossing of 0.8 * q_nom under each source is compared with the documented value. NASA: README stopping rules are
stated on rated capacity for B0005-B0018 (1.4 Ah); first crossing per source is compared with the file's own
last discharge for those cells.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
T = ROOT / "data/processed/cycle_tables"
out = {}
tab1 = pd.read_csv(ROOT / "configs/reference_facts/hust_tableS1.csv").set_index("channel")


def first_cross(q, thr):
    idx = np.flatnonzero(np.asarray(q) <= thr)
    return int(idx[0]) + 1 if idx.size else None


for ds, thr in (("HUST", 0.88), ("MATR", 0.88), ("NASA_PCoE", 1.4)):
    df = pd.read_csv(T / f"{ds}.csv.gz", low_memory=False)
    df = df[~df["degenerate"]]
    rows = []
    for cid, g in df.groupby("cell_id"):
        r = {"cell_id": cid, "n": len(g)}
        for src in ("capacity_cycler_Ah", "capacity_integrated_Ah"):
            r[f"cross_{src}"] = first_cross(g[src], thr)
        if ds == "HUST":
            ch = cid.split("_", 1)[1]
            r["documented"] = int(tab1.at[ch, "cycle_life"]) - (2 if ch == "7-5" else 0)
        elif ds == "MATR":
            r["documented"] = float(g["cycle_life"].iloc[0]) if "cycle_life" in g else np.nan
        else:
            r["documented"] = len(g) if cid in ("NASA_B0005", "NASA_B0006", "NASA_B0018") else np.nan
        rows.append(r)
    u = pd.DataFrame(rows)
    res = {}
    for src in ("capacity_cycler_Ah", "capacity_integrated_Ah"):
        c = u[f"cross_{src}"]
        docd = u["documented"]
        m = c.notna() & docd.notna()
        res[src] = {"units": int(len(u)), "units_crossing": int(c.notna().sum()),
                    "median_abs_diff_to_documented_cycles": float((c[m] - docd[m]).abs().median()) if m.any() else None,
                    "within_5_cycles_of_documented": int(((c[m] - docd[m]).abs() <= 5).sum()), "comparable_units": int(m.sum())}
    out[ds] = res
    u.to_csv(Path(__file__).with_name(f"{ds}_crossings.csv"), index=False)
Path(__file__).with_name("result.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))

# Addendum (after D13 option c): EOL attainment under the record-end rule for each capacity source.
from degradx.generator.state import StateSpec, unit_state  # noqa: E402

add = {}
for ds, qn in (("MATR", 1.1), ("HUST", 1.1), ("NASA_PCoE", 2.0)):
    df = pd.read_csv(T / f"{ds}.csv.gz", low_memory=False)
    df = df[~df["degenerate"]]
    add[ds] = {}
    for src in ("capacity_cycler_Ah", "capacity_integrated_Ah"):
        reach = 0
        for cid, g in df.groupby("cell_id"):
            q = g[src].to_numpy(float)
            if len(q) < 21:
                continue
            st = unit_state(q, StateSpec(rho=0.8, q_nom=qn, k=20, margin=0.05, sg_window=11, sg_polyorder=2))
            Tc = st.T if st.T is not None else (len(q) if (not st.excluded_by_guard and abs(q[-5:].mean() - 0.8 * qn) <= 0.01 * qn) else None)
            reach += Tc is not None
        add[ds][src] = reach
Path(__file__).with_name("result_record_end_rule.json").write_text(json.dumps(add, indent=1))
print(json.dumps(add, indent=1))
