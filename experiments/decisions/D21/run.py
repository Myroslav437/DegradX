"""D21 harness: the pattern term of the decomposable target is negligible at NASA PCoE's fitted amplitudes.

S6 (NASA, recency): Var(pattern term) / Var(mean term) = 0.0004 (declared band [0.05, 0.50]); retraining without the
pattern term does not change the error on y. For pattern amplitude multipliers {1, 2, 4, 8, 16} (a declared S7 generator
setting), 300 units are generated (generation seed 0, amplitude override), split 70/15/15, and measured:
  variance ratio of the two terms over test windows, per weighting
  ablation: LSTM (config A, model seeds 0-1) trained on y vs on the graded term alone; NMSE increase on y (bootstrap over units)
  fidelity cost: median generated inserted amplitude vs the measured NASA regeneration amplitudes (S2 audit, 21 events;
  S3 fitting split, 6 events), and the share of generated amplitudes above the largest measured one
"""
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from degradx.generator.generate import Profile, generate_unit
from degradx.metrics import usability as U
from degradx.models.lstm import train_regressor
from degradx.targets.decomposable import TargetSpec, unit_targets

ROOT = Path(__file__).resolve().parents[3]
decl = yaml.safe_load((ROOT / "configs/declarations.yaml").read_text())
dd = decl["declared_by_design"]
prof = json.loads((ROOT / "artifacts/s3_fit_profiles/profiles/NASA_PCoE.json").read_text())
units0, _ = pickle.loads((ROOT / "data/generated/NASA_PCoE/seed0.pkl").read_bytes())
P = Profile.from_json(prof, np.concatenate([u.eps[:, len(prof["declared_used"]["channels_available"]) + 1] for u in units0]))
spec = TargetSpec.build(P, dd["target"]["weights"]["beta"]["value"], 24, 6.0)
cfg = yaml.safe_load((ROOT / "configs/models/lstm.yaml").read_text())
audit = pd.read_csv(ROOT / "artifacts/s2_audit_datasets/tables/patterns_default_threshold.csv")
meas_amp = audit[(audit.dataset == "NASA_PCoE") & (audit.sign > 0)]["amplitude"].to_numpy() * 1000
fit_amp = np.array(prof["estimated_from_data"]["E6_patterns"]["positive"]["amplitude_Ah"]) * 1000
out = {"measured_amplitude_mAh": {"audit_median": float(np.median(meas_amp)), "audit_max": float(meas_amp.max()), "fitting_median": float(np.median(fit_amp))}, "multipliers": {}}


def windows(units, kind):
    X, y, g, s, u = [], [], [], [], []
    for i, un in enumerate(units):
        if un.T < 24:
            continue
        tg = unit_targets(un, spec, kind)
        X.append(tg["x"]); y.append(tg["y"]); g.append(tg["graded"].sum(axis=(1, 2))); s.append(tg["sparse"].sum(axis=(1, 2))); u.append(np.full(len(tg["y"]), i))
    return np.concatenate(X).astype(np.float32), np.concatenate(y), np.concatenate(g), np.concatenate(s), np.concatenate(u)


for mult in (1, 2, 4, 8, 16):
    units = [x for x in (generate_unit(P, 0, i, overrides={"pattern_amplitude_multiplier": mult}) for i in range(400)) if x is not None][:300]
    perm = np.random.default_rng(0).permutation(len(units))
    tr, va, te = perm[:210], perm[210:255], perm[255:]
    amps = np.array([p["amplitude_Ah"] for u in units for p in u.patterns]) * 1000
    r = {"generated_amplitude_median_mAh": float(np.median(amps)), "share_above_measured_max": float(np.mean(amps > meas_amp.max())), "variance_ratio": {}}
    for kind in ("recency", "uniform", "final_position"):
        _, _, g, s, _ = windows([units[k] for k in te], kind)
        r["variance_ratio"][kind] = float(np.var(s) / np.var(g))
    Xtr, ytr, gtr, _, Utr = windows([units[k] for k in np.concatenate([tr, va])], "recency")
    Xte, yte, _, _, Ute = windows([units[k] for k in te], "recency")
    val = set(range(len(tr), len(tr) + len(va)))
    sf, sa = [], []
    for ms in (0, 1):
        m_full = train_regressor(Xtr, ytr, Utr, seed=ms, device="cuda", cfg=cfg, val_units=val)
        m_ab = train_regressor(Xtr, gtr, Utr, seed=ms, device="cuda", cfg=cfg, val_units=val)
        a, n = U.unit_sums((m_full.predict(Xte) - yte) ** 2, Ute)
        b, _ = U.unit_sums((m_ab.predict(Xte) - yte) ** 2, Ute)
        sf.append(a); sa.append(b)
    r["ablation_pattern_term_removed"] = U.nmse_increase_ci(np.mean(sf, 0), np.mean(sa, 0), n, float(np.var(yte)), seed=0, n_resamples=2000)
    r["full_model_nrmse"] = float(np.sqrt(np.mean(sf[0].sum() / n.sum())) / np.std(yte))
    out["multipliers"][mult] = r
    print(mult, json.dumps(r), flush=True)
Path(__file__).with_name("result.json").write_text(json.dumps(out, indent=1))
