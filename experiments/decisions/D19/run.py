"""D19 harness: NASA PCoE fidelity below the held-out minimum — void, or cross-fitted estimate?

Option a (declared single split): NASA has 5 held-out units, 3 reaching EOL (S5): TSTR and distributional rows void.
Option b (cross-fitting): the 18 guard-passing NASA units are split into 5 folds (stratified by EOL attainment, seed
stream 'split'); for each fold, the S3 profile fit runs on the other folds, 300 units are generated from that fold's
profile (generation seed 0), TSTR / TRTR LSTMs are trained (model seeds 0-4) and evaluated on the fold's held-out units
reaching EOL; per-unit squared errors are pooled over folds and the ratio's BCa interval is taken over all held-out units.
Metrics: pooled units, ratio, relative 95% half-width, per-fold family/enabled patterns (how much the profile moves).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from degradx.data.audit import CleaningRule, clean_capacity
from degradx.data.splits import measured_split
from degradx.fitting.profile import ChannelRule, fit_profile, prepare_units
from degradx.generator.generate import Profile, generate_unit
from degradx.generator.state import spec_from_declarations, unit_state
from degradx.metrics import fidelity as F
from degradx.models.lstm import train_regressor
from degradx.utils.config import load_declarations
from degradx.utils.seeding import rng

ROOT = Path(__file__).resolve().parents[3]
decl = load_declarations()
dd = decl["declared_by_design"]
ds, qn, L = "NASA_PCoE", 2.0, 24
chans = ["capacity", "charge_time", "mean_discharge_voltage", "temperature_mean"]
df = pd.read_csv(ROOT / f"data/processed/cycle_tables/{ds}.csv.gz", low_memory=False)
spec = spec_from_declarations(decl, qn)
rule, cr = CleaningRule("D12", isolated_excursion_frac=0.05, drop_recovered_collapse=True), ChannelRule(0.05)
cfg = yaml.safe_load((ROOT / "configs/models/lstm.yaml").read_text())
elig = []
for cid, g in df.groupby("cell_id"):
    d = clean_capacity(g, "capacity_cycler_Ah", rule, qn)
    if len(d) < 20:
        continue
    st = unit_state(d["capacity_cycler_Ah"].to_numpy(float), spec)
    if not st.excluded_by_guard:
        elig.append({"cell_id": cid, "reaches_eol": st.T is not None})
elig = pd.DataFrame(elig).sort_values("cell_id").reset_index(drop=True)
g = rng(20260915, "split", ds, "crossfit")
folds = np.zeros(len(elig), int)
for reach, idx in elig.groupby("reaches_eol").groups.items():
    idx = np.array(sorted(idx))
    folds[idx[g.permutation(len(idx))]] = np.arange(len(idx)) % 5
elig["fold"] = folds
sse_a, sse_b, nn, fold_info = [], [], [], []
for k in range(5):
    split = elig.assign(split=np.where(elig["fold"] == k, "held_out", "fitting"))[["cell_id", "split", "reaches_eol"]]
    prof, diag = fit_profile(df, split, dataset=ds, q_nom=qn, spec=spec, rule=rule, channels=chans, crule=cr, decl=decl, workers=12, k=2.5, m=2,
                             sweep_k=[2.5], base_seed=20260915)
    prof["declared_used"]["channels_available"] = chans
    fit_u = prepare_units(df, split[split.split == "fitting"].cell_id, qn, spec, rule, chans, cr)
    ho_u = prepare_units(df, split[split.split == "held_out"].cell_id, qn, spec, rule, chans, cr)
    pool = np.concatenate([u.channels["charge_time"] for u in fit_u]); pool = pool[np.isfinite(pool)]
    P = Profile.from_json(prof, pool)
    gen = [u for u in (generate_unit(P, 0, i) for i in range(400)) if u is not None][:300]
    ms_fit, ms_ho = F.measured_series(fit_u, chans), F.measured_series(ho_u, chans)
    n_tr = sum(s.T is not None for s in ms_fit)
    Xm, Um, Rm = F.windows(ms_fit, L, with_rul=True, with_elapsed=True)
    Xg, Ug, Rg = F.windows(F.generated_series(gen[:n_tr], len(chans)), L, with_rul=True, with_elapsed=True)
    Xh, Uh, Rh = F.windows(ms_ho, L, with_rul=True, with_elapsed=True)
    if len(Xh) == 0:
        fold_info.append({"fold": k, "held_out_reaching": 0}); continue
    a, b = [], []
    for ms in range(5):
        _, s1, n1 = F.per_unit_sse(train_regressor(Xg, Rg, Ug, seed=ms, device="cuda", cfg=cfg).predict(Xh), Rh, Uh)
        _, s2, _ = F.per_unit_sse(train_regressor(Xm, Rm, Um, seed=ms, device="cuda", cfg=cfg).predict(Xh), Rh, Uh)
        a.append(s1); b.append(s2)
    sse_a.append(np.mean(a, 0)); sse_b.append(np.mean(b, 0)); nn.append(n1)
    fold_info.append({"fold": k, "fitting_units": len(fit_u), "held_out_reaching": int(len(n1)), "family": prof["estimated_from_data"]["E2_family_choice"]["selected"],
                      "positive_enabled": prof["estimated_from_data"]["E6_patterns"]["positive"]["enabled"],
                      "fold_ratio": float(np.sqrt(np.sum(sse_a[-1]) / np.sum(n1)) / np.sqrt(np.sum(sse_b[-1]) / np.sum(n1)))})
    print(fold_info[-1], flush=True)
A, B, N = np.concatenate(sse_a), np.concatenate(sse_b), np.concatenate(nn)
res = F.ratio_bootstrap(A, B, N, seed=0, n_resamples=10000)
res["relative_half_width_95"] = (res["ci_high"] - res["ci_low"]) / 2 / res["ratio"] if res["ci_low"] is not None else None
out = {"option_b_crossfit": res, "folds": fold_info, "option_a_single_split": "held-out units reaching EOL 3 < 5: void (S5)"}
Path(__file__).with_name("result.json").write_text(json.dumps(out, indent=1))
print(json.dumps(res, indent=1))
