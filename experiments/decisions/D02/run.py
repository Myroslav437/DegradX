"""D02 harness: (1) what censored units add, (2) where minimum counts per use sit.

(1) NASA and MATR fitting splits (S3 fit, seed 20260915): noise variance/phi, positive events and mapping endpoints with
    censored (guard-passing, not reaching EOL) units included vs excluded.
(2) Resampling curves. theta: MATR fitting units reaching EOL (largest pool); for n in {3,5,8,12,20,40}, 300 subsamples
    without replacement; statistic = median T and median position at which the selected family's trajectory reaches
    z = 0.5 divided by T; spread = (p97.5 - p2.5) / (2 * full-pool value). Patterns: pooled S2 NASA positive-event
    amplitudes (all 21 audit events, used only as a distribution to subsample); for n in {3,5,7,10,15,21}, 300 bootstrap
    resamples of size n; statistic = median amplitude; same relative half-width.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from degradx.data.audit import CleaningRule, clean_capacity
from degradx.data.splits import measured_split
from degradx.fitting.families import FAMILIES
from degradx.fitting.profile import ChannelRule, fit_profile
from degradx.generator.state import spec_from_declarations, unit_state
from degradx.utils.config import load_declarations
from degradx.utils.seeding import rng

ROOT = Path(__file__).resolve().parents[3]
decl = load_declarations()
RULE = CleaningRule("iso05_rc", isolated_excursion_frac=0.05, drop_recovered_collapse=True)
CFG = {"MATR": (1.1, ["capacity", "charge_time", "mean_discharge_voltage", "internal_resistance", "temperature_mean"]),
       "NASA_PCoE": (2.0, ["capacity", "charge_time", "mean_discharge_voltage", "temperature_mean"])}
out = {"censored": {}, "resampling": {}}
fits = {}
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
    res = {}
    for name, sp in (("with_censored", split), ("reaching_only", split[split["reaches_eol"]])):
        prof, diag = fit_profile(df, sp, dataset=ds, q_nom=qn, spec=spec, rule=RULE, channels=chans, crule=ChannelRule(0.05), decl=decl,
                                 workers=12, k=2.5, m=2, sweep_k=[2.5])
        e = prof["estimated_from_data"]
        res[name] = {"fitting_units": len(prof["units"]["fitting_passing_guard"]), "reaching": len(prof["units"]["fitting_reaching_eol"]),
                     "family": e["E2_family_choice"]["selected"], "positive_events": e["E6_patterns"]["positive"]["events"],
                     "noise_variance": {c: e["E5_noise"][c]["variance"] for c in chans}, "noise_phi": {c: e["E5_noise"][c]["phi"] for c in chans},
                     "phi1": {c: e["E3_channel_mappings"][c]["phi1"] for c in chans}}
        if name == "with_censored":
            fits[ds] = (prof, diag)
    out["censored"][ds] = res
    print(ds, json.dumps(res), flush=True)

# (2) resampling: theta-derived quantities on MATR
prof, diag = fits["MATR"]
fam = prof["estimated_from_data"]["E1_theta_distribution"]["family"]
per = prof["estimated_from_data"]["E1_theta_distribution"]["per_unit"]
T = np.array([p["T"] for p in per], float)
half = []
for p in per:
    pos = np.arange(1, int(p["T"]) + 1, dtype=float)
    y = FAMILIES[fam](np.array(p["family_params"]), pos)
    z = (1 - y) * p["q1"] / (p["q1"] - 0.8 * 1.1)
    idx = np.flatnonzero(z >= 0.5)
    half.append((idx[0] + 1) / p["T"] if idx.size else np.nan)
half = np.array(half)
g = rng(7, "bootstrap", "D02")
curves = {"theta_median_T": {}, "theta_median_half_life_fraction": {}, "pattern_median_amplitude": {}}
for n in (3, 5, 8, 12, 20, 40):
    mT, mh = [], []
    for _ in range(300):
        s = g.choice(len(T), size=n, replace=False)
        mT.append(np.median(T[s])); mh.append(np.nanmedian(half[s]))
    curves["theta_median_T"][n] = float((np.quantile(mT, 0.975) - np.quantile(mT, 0.025)) / 2 / np.median(T))
    curves["theta_median_half_life_fraction"][n] = float((np.nanquantile(mh, 0.975) - np.nanquantile(mh, 0.025)) / 2 / np.nanmedian(half))
amps = pd.read_csv(ROOT / "artifacts/s2_audit_datasets/tables/patterns_default_threshold.csv")
amps = amps[(amps["dataset"] == "NASA_PCoE") & (amps["sign"] > 0)]["amplitude"].to_numpy(float)
for n in (3, 5, 7, 10, 15, 21):
    med = [np.median(g.choice(amps, size=n, replace=True)) for _ in range(300)]
    curves["pattern_median_amplitude"][n] = float((np.quantile(med, 0.975) - np.quantile(med, 0.025)) / 2 / np.median(amps))
out["resampling"] = {"relative_half_width_95": curves, "pools": {"MATR_reaching_fitting_units": int(len(T)), "NASA_S2_positive_events": int(len(amps))}}
Path(__file__).with_name("result.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out["resampling"], indent=1))
