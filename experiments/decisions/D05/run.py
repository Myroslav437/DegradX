"""D05 harness: detection operating point k (m = 2, max duration = 11, D16).

For each profile: measured detected rate per 100 positions at each k in the declared sweep (fitting split, selected
family residuals; S3 smoke fit), against the rate the same detector returns on pure noise: stationary AR(1) series with
the profile's fitted capacity-noise variance and lag-1 coefficient, cut into segments of the profile's median fitted
length, 200 segments, seed 5 (generation stream, not used elsewhere). The ratio measured / noise-only is the fraction
of detections the noise model alone cannot explain.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from degradx.data.audit import CleaningRule, clean_capacity
from degradx.data.splits import measured_split
from degradx.fitting.noise_mappings import ar1_sample
from degradx.fitting.patterns import detect
from degradx.fitting.profile import ChannelRule, fit_profile
from degradx.generator.state import spec_from_declarations, unit_state
from degradx.utils.config import load_declarations
from degradx.utils.seeding import rng

ROOT = Path(__file__).resolve().parents[3]
decl = load_declarations()
KS = [2.0, 2.5, 3.0, 3.5, 4.0]
RULE = CleaningRule("iso05_rc", isolated_excursion_frac=0.05, drop_recovered_collapse=True)
CFG = {"MATR": (1.1, ["capacity", "charge_time"]), "HUST": (1.1, ["capacity", "charge_time"]), "NASA_PCoE": (2.0, ["capacity", "charge_time"])}
out = {}
for ds, (qn, chans) in CFG.items():
    df = pd.read_csv(ROOT / f"data/processed/cycle_tables/{ds}.csv.gz", low_memory=False)
    if ds == "MATR":
        df = df[df["batch"] != "2019-01-24"]
    spec = spec_from_declarations(decl, qn)
    elig = []
    for cid, g in df.groupby("cell_id"):
        d = clean_capacity(g, "capacity_cycler_Ah", RULE, qn)
        if len(d) < 20:
            continue
        st = unit_state(d["capacity_cycler_Ah"].to_numpy(float), spec)
        if not st.excluded_by_guard:
            elig.append({"cell_id": cid, "reaches_eol": st.T is not None})
    split = measured_split(pd.DataFrame(elig), 20260915, ds)
    prof, diag = fit_profile(df, split, dataset=ds, q_nom=qn, spec=spec, rule=RULE, channels=chans, crule=ChannelRule(0.05), decl=decl,
                             workers=12, k=2.5, m=2, sweep_k=KS)
    sw = diag["sweep"]
    noise = prof["estimated_from_data"]["E5_noise"]["capacity"]
    seg_len = int(np.median(diag["units"]["fit_positions"]))
    g = rng(5, "generation", "D05", ds)
    res = {"noise_variance": noise["variance"], "noise_phi": noise["phi"], "segment_length": seg_len, "k": {}}
    for kk in KS:
        s = sw[sw["k"] == kk]
        pos_rate = float(s["positive"].sum() / s["positions"].sum() * 100)
        neg_rate = float(s["negative"].sum() / s["positions"].sum() * 100)
        n_pos = n_neg = 0
        for _ in range(200):
            e = ar1_sample(g, seg_len, noise["variance"], noise["phi"])
            pats, _s = detect(e, kk, 2, max_duration=11)
            n_pos += sum(p.sign > 0 for p in pats); n_neg += sum(p.sign < 0 for p in pats)
        noise_rate = (n_pos + n_neg) / 2 / (200 * seg_len) * 100
        amp = s["positive_amp_median_Ah"].median()
        res["k"][kk] = {"measured_positive_per100": pos_rate, "measured_negative_per100": neg_rate, "noise_only_per_sign_per100": noise_rate,
                        "positive_ratio_to_noise": pos_rate / noise_rate if noise_rate > 0 else None,
                        "negative_ratio_to_noise": neg_rate / noise_rate if noise_rate > 0 else None,
                        "positive_events": int(s["positive"].sum()), "median_positive_amp_mAh": float(amp * 1000) if np.isfinite(amp) else None}
    out[ds] = res
    print(ds, json.dumps(res), flush=True)
Path(__file__).with_name("result.json").write_text(json.dumps(out, indent=1))
