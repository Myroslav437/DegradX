"""D16 harness: residual on which inserted patterns are detected.

Options (capacity D11, cleaning D12, T with D13/D15; detector k=2.5, m=2):
  a  declared: families fitted over positions 1..T; detect on the whole residual; no duration limit
  b  families fitted over t1..T (the fall from q1, as D15); detect on positions t1..T
  c  b + a run longer than the Savitzky-Golay window (11 positions) is not a pattern: it survives smoothing, so it is
     part of q_t and changes z_t, which inserted patterns must not (paper l.175)
Works test (planted transients): on every real record reaching EOL (NASA) or a fixed 30-unit sample (MATR, HUST, first 30
cell ids in sorted order), plant 5 raised-cosine transients per unit at seeded positions after t1 (duration U{2..8},
amplitude +/- U(4,10) x the unit's residual scale under option a), then rerun fit + detection. Recall = planted
transients whose span contains a detected extremum of the same sign; extra = detections on the planted record minus
detections on the clean record at matching spans (a proxy for spurious detections); amplitude ratio = detected / planted.
"""
import json
from pathlib import Path
from multiprocessing import get_context

import numpy as np
import pandas as pd

from degradx.data.audit import CleaningRule, clean_capacity
from degradx.fitting.families import FAMILIES, fit_family
from degradx.fitting.patterns import detect, residual_scale
from degradx.generator.state import StateSpec, unit_state

ROOT = Path(__file__).resolve().parents[3]
QNOM = {"MATR": 1.1, "HUST": 1.1, "NASA_PCoE": 2.0}
RULE = CleaningRule("iso05_rc", isolated_excursion_frac=0.05, drop_recovered_collapse=True)
W = 11


def detect_option(q, qn, option):
    spec = StateSpec(rho=0.8, q_nom=qn, k=20, margin=0.05, sg_window=11, sg_polyorder=2, record_end_tau=0.01)
    st = unit_state(q, spec)
    end = st.T if st.T is not None else len(q)
    start = 0 if option == "a" else st.t1 - 1
    pos = np.arange(1, len(q) + 1, dtype=float)[start:end]
    y = q[start:end] / st.q1
    fits = {n: fit_family(n, pos, y) for n in FAMILIES}
    best = min(fits, key=lambda n: fits[n].rmse if np.isfinite(fits[n].rmse) else np.inf)
    r = (y - FAMILIES[best](fits[best].params, pos)) * st.q1
    pats, s = detect(r, 2.5, 2)
    if option == "c":
        pats = [p for p in pats if p.duration <= W]
    # shift to record positions
    out = [dict(sign=p.sign, start=p.start + start, end=p.end + start, extremum=p.extremum + start, amplitude=p.amplitude, duration=p.duration) for p in pats]
    return out, s, st, start, end


def unit_job(args):
    ds, cid, q, qn, seed = args
    res = {"dataset": ds, "cell_id": cid}
    base = {}
    for opt in "abc":
        pats, s, st, start, end = detect_option(q, qn, opt)
        base[opt] = pats
        res[f"{opt}_n_pos"] = sum(p["sign"] > 0 for p in pats)
        res[f"{opt}_n_neg"] = sum(p["sign"] < 0 for p in pats)
        res[f"{opt}_early50"] = sum(p["extremum"] <= 50 for p in pats)
        res[f"{opt}_long"] = sum(p["duration"] > W for p in pats)
        res[f"{opt}_amp_abs_mAh_median"] = float(np.median([abs(p["amplitude"]) for p in pats]) * 1000) if pats else np.nan
        res[f"{opt}_dur_median"] = float(np.median([p["duration"] for p in pats])) if pats else np.nan
        if opt == "a":
            s_a, t1, end_a = s, st.t1, end
    res["reaches_eol"] = st.T is not None
    # planted transients
    rng = np.random.default_rng(seed)
    qp = q.copy()
    planted = []
    lo, hi = t1 + 10, end_a - 12
    if hi - lo > 60 and np.isfinite(s_a) and s_a > 0:
        centres = np.sort(rng.choice(np.arange(lo, hi), size=5, replace=False))
        for c in centres:
            D = int(rng.integers(2, 9)); A = float(rng.uniform(4, 10)) * s_a * rng.choice([-1, 1])
            j = np.arange(D)
            shape = A * np.sin(np.pi * (j + 1) / (D + 1)) ** 2
            idx = c - D // 2 + j
            qp[idx - 1] += shape
            planted.append((int(idx[0]), int(idx[-1]), int(np.sign(A)), A))
        for opt in "abc":
            pats, *_ = detect_option(qp, qn, opt)
            hit = 0; ratios = []
            for (a0, a1, sg, A) in planted:
                m = [p for p in pats if p["sign"] == sg and a0 <= p["extremum"] <= a1]
                if m:
                    hit += 1; ratios.append(m[0]["amplitude"] / A)
            res[f"{opt}_recall"] = hit / len(planted)
            res[f"{opt}_amp_ratio_median"] = float(np.median(ratios)) if ratios else np.nan
            res[f"{opt}_extra"] = len(pats) - len(base[opt]) - hit
    return res


jobs = []
for ds, qn in QNOM.items():
    df = pd.read_csv(ROOT / f"data/processed/cycle_tables/{ds}.csv.gz", low_memory=False)
    ids = sorted(df["cell_id"].unique())
    if ds != "NASA_PCoE":
        ids = ids[:30]
    for i, cid in enumerate(ids):
        d = clean_capacity(df[df["cell_id"] == cid], "capacity_cycler_Ah", RULE, qn)
        q = d["capacity_cycler_Ah"].to_numpy(float)
        if len(q) >= 40:
            jobs.append((ds, cid, q, qn, 1000 + i))
with get_context("fork").Pool(12) as pool:
    rows = pool.map(unit_job, jobs, chunksize=1)
u = pd.DataFrame(rows)
u.to_csv(Path(__file__).with_name("per_unit.csv"), index=False)
summary = {}
for ds, g in u.groupby("dataset"):
    gg = g if ds != "NASA_PCoE" else g[g["reaches_eol"]]
    summary[ds] = {"units": int(len(gg))}
    for opt in "abc":
        summary[ds][opt] = {k: (float(gg[f"{opt}_{k}"].sum()) if k in ("n_pos", "n_neg", "early50", "long", "extra") else float(gg[f"{opt}_{k}"].median()))
                            for k in ("n_pos", "n_neg", "early50", "long", "amp_abs_mAh_median", "dur_median", "recall", "amp_ratio_median", "extra")
                            if f"{opt}_{k}" in gg}
Path(__file__).with_name("result.json").write_text(json.dumps(summary, indent=1))
print(json.dumps(summary, indent=1))
