"""D17 harness: glitch rule for non-capacity channels (charge time, mean discharge voltage, IR, temperature).

Options (IR = 0 is missing in all): none | iso05: single-position departure > 5% of the unit's channel median from the
centred 11-position rolling median, neighbours not departing -> NaN | iso50: the same at 50%.
Metrics on the fitting split (seed 20260915, split as S3): readings masked per channel; phi_c(0), phi_c(1); AR(1) noise
variance and lag-1 coefficient per channel; residual cross-channel correlation.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from degradx.data.audit import CleaningRule, clean_capacity
from degradx.data.splits import measured_split
from degradx.fitting.profile import ChannelRule, clean_channel, fit_profile
from degradx.generator.state import spec_from_declarations, unit_state
from degradx.utils.config import load_declarations

ROOT = Path(__file__).resolve().parents[3]
decl = load_declarations()
RULE = CleaningRule("iso05_rc", isolated_excursion_frac=0.05, drop_recovered_collapse=True)
CFG = {"MATR": (1.1, ["capacity", "charge_time", "mean_discharge_voltage", "internal_resistance", "temperature_mean"]),
       "HUST": (1.1, ["capacity", "charge_time", "mean_discharge_voltage"]),
       "NASA_PCoE": (2.0, ["capacity", "charge_time", "mean_discharge_voltage", "temperature_mean"])}
COL = {"charge_time": "charge_time_min", "mean_discharge_voltage": "mean_discharge_voltage_V", "internal_resistance": "internal_resistance_ohm", "temperature_mean": "temperature_mean_C"}
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
    out[ds] = {}
    for name, cr in (("none", ChannelRule(None)), ("iso05", ChannelRule(0.05)), ("iso50", ChannelRule(0.5))):
        prof, diag = fit_profile(df, split, dataset=ds, q_nom=qn, spec=spec, rule=RULE, channels=chans, crule=cr, decl=decl, workers=12,
                                 k=2.5, m=2, sweep_k=[2.5])
        e = prof["estimated_from_data"]
        masked = {}
        for c in chans[1:]:
            n_mask = 0
            for u in diag["unit_objects"]:
                raw = clean_capacity(df[df["cell_id"] == u.cell_id], "capacity_cycler_Ah", RULE, qn)[COL[c]].to_numpy(float)
                if c == "internal_resistance":
                    raw = np.where(raw == 0, np.nan, raw)
                n_mask += int(np.isfinite(raw).sum() - np.isfinite(u.channels[c]).sum())
            masked[c] = n_mask
        out[ds][name] = {"masked_readings": masked,
                         "phi0": {c: e["E3_channel_mappings"][c]["phi0"] for c in chans}, "phi1": {c: e["E3_channel_mappings"][c]["phi1"] for c in chans},
                         "noise_variance": {c: e["E5_noise"][c]["variance"] for c in chans}, "noise_phi": {c: e["E5_noise"][c]["phi"] for c in chans},
                         "correlation": e["E4_channel_covariance"]["correlation"], "demoted": prof["derived"]["channel_roles"]["demoted_by_guard"]}
        print(ds, name, json.dumps({k: v for k, v in out[ds][name].items() if k != "correlation"}), flush=True)
Path(__file__).with_name("result.json").write_text(json.dumps(out, indent=1))
