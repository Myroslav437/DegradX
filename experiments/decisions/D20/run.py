"""D20 harness: which probe defines the S7 operating range (Table 5, Figure 8)?

Part two of S7 trains the primary LSTM per generator setting and scores IG on it; it also scores the exact attribution of
the reference model (equal to IG and occlusion on the reference model, S8 checks) but stores only its mean. This harness
regenerates the same units, split and windows (same seeds; no training, which consumes no draws from the split stream),
recomputes the reference-model scores per unit, verifies that their mean reproduces the stored value, and applies the
declared operating-range rule (declarations responsiveness.operating_range) under each probe option:
  a  IG on the trained model (as run)
  b  the reference model (the declared primary scoring target, C2)
  c  both, a setting value inside the operating range only where neither probe is saturated or near chance
"""
import json
import pickle
import sys
from pathlib import Path

import numpy as np
from scipy.stats import bootstrap

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from degradx import ARTIFACTS_DIR, DATA_DIR  # noqa: E402
from degradx.generator.generate import Profile, generate_unit  # noqa: E402
from degradx.metrics.scores import rank_agreement, retrieval_ap  # noqa: E402
from degradx.targets.decomposable import TargetSpec, unit_targets  # noqa: E402
from degradx.utils.config import load_declarations  # noqa: E402
from degradx.utils.seeding import rng  # noqa: E402

SEED, N_UNITS, PER_UNIT, SAT, CHANCE_THR = 20260915, 150, 10, 0.95, 0.05
dd = load_declarations()["declared_by_design"]
beta = dd["target"]["weights"]["beta"]["value"]
L0 = int(dd["target"]["window_length_L"]["value"])
settings = {k: v for k, v in dd["responsiveness"]["generator_settings"].items() if k != "source"}
rows = json.loads((ARTIFACTS_DIR / "s7_responsiveness/tables/part2_generator_settings.json").read_text())
p1 = json.loads((ARTIFACTS_DIR / "s7_responsiveness/tables/part1_degradation.json").read_text())


def state(unit_vals, chance, seed=SEED):
    v = np.asarray(unit_vals, float)
    v = v[np.isfinite(v)]
    norm = (v - chance) / (1.0 - chance)
    mean = float(norm.mean())
    if len(norm) >= 3 and np.std(norm) > 0:
        ci = bootstrap((norm,), np.mean, n_resamples=2000, method="BCa", random_state=np.random.default_rng(seed)).confidence_interval
        lo, hi = float(ci.low), float(ci.high)
    else:
        lo = hi = mean
    s = "saturated" if mean >= SAT else ("near chance" if (mean <= CHANCE_THR or lo <= 0) else "responsive")
    return {"norm": mean, "ci": [lo, hi], "state": s}


out = []
for ds in ("MATR", "HUST", "NASA_PCoE"):
    prof = json.loads((ARTIFACTS_DIR / f"s3_fit_profiles/profiles/{ds}.json").read_text())
    units0, _ = pickle.loads((DATA_DIR / f"generated/{ds}/seed0.pkl").read_bytes())
    P = Profile.from_json(prof, np.concatenate([u.eps[:, len(prof["declared_used"]["channels_available"]) + 1] for u in units0]))
    has_patterns = any(len(u.patterns) for u in units0)
    c_rank, c_ret = p1[ds]["recency"]["chance_rank"], p1[ds]["recency"].get("chance_retrieval")
    for setting, grid in settings.items():
        if setting == "pattern_amplitude_multiplier" and not has_patterns:
            continue
        for val in grid:
            stored = next((r for r in rows if r["dataset"] == ds and r["setting"] == setting and r["value"] == val), None)
            if stored is None:
                continue
            ov = {} if setting == "window_length_L" else {setting: float(val)}
            L = int(val) if setting == "window_length_L" else L0
            spec = TargetSpec.build(P, beta, L, 6.0 if setting != "window_length_L" else 6.0 * L / L0)
            units, i = [], 0
            while len(units) < N_UNITS and i < 4 * N_UNITS:
                u = generate_unit(P, 0, i, overrides=ov)
                i += 1
                if u is not None and u.T >= L + 2:
                    units.append(u)
            g = rng(SEED, "split", ds, "s7", setting, val)
            perm = g.permutation(len(units))
            te = perm[int(0.85 * len(units)):]
            has_pat = any(len(units[k].patterns) for k in te)
            rank_ref, ret_ref = [], []
            for k in te:
                tg = unit_targets(units[k], spec, "recency")
                idx = np.sort(g.choice(len(tg["y"]), size=min(PER_UNIT, len(tg["y"])), replace=False))
                w = spec.weights("recency")[None]
                Rpf, R = w * (tg["x_pattern_free"][idx] - spec.x0), w * (tg["x"][idx] - spec.x0)
                rank_ref.append(np.nanmean([rank_agreement(Rpf[j], tg["graded"][idx][j]) for j in range(len(idx))]))
                if has_pat:
                    sp = tg["sparse"][idx] != 0
                    ok = [j for j in range(len(idx)) if sp[j].any()]
                    if ok:
                        ret_ref.append(np.nanmean([retrieval_ap(R[j] - Rpf[j], sp[j]) for j in ok]))
            reproduced = abs(float(np.nanmean(rank_ref)) - stored["rank_reference_exact"]) < 1e-9
            rec = {"dataset": ds, "setting": setting, "value": val, "reproduces_stored_reference_mean": reproduced, "nrmse_trained": stored["nrmse"],
                   "rank": {"a_trained_ig": state(stored["rank_ig_units"], c_rank), "b_reference": state(rank_ref, c_rank)}}
            if stored.get("retrieval_ig_units"):
                rec["retrieval"] = {"a_trained_ig": state(stored["retrieval_ig_units"], c_ret), "b_reference": state(ret_ref, c_ret) if ret_ref else None}
            for score in ("rank", "retrieval"):
                if score in rec and rec[score]["b_reference"] is not None:
                    a, b = rec[score]["a_trained_ig"]["state"], rec[score]["b_reference"]["state"]
                    rec[score]["c_both"] = "responsive" if (a == b == "responsive") else ("; ".join(sorted({x for x in (a, b) if x != "responsive"})))
            out.append(rec)
            print(ds, setting, val, "reproduced" if reproduced else "MISMATCH",
                  {s: {k: (round(v["norm"], 3), v["state"]) if isinstance(v, dict) else v for k, v in rec[s].items()} for s in ("rank", "retrieval") if s in rec}, flush=True)
(Path(__file__).parent / "result.json").write_text(json.dumps(out, indent=2))
