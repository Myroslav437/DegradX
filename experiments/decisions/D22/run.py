"""D22 harness: TimeSHAP l1_reg at cell level ('auto', the value local_cell_level fixes, vs False, dense) and cost per window.

NASA PCoE recency: 12 test windows (evaluation stream), on the reference model (exact Shapley = w (x - x0)) and on the
primary trained LSTM; nsamples 32000, background = pristine event (C4), attribution seed 0 (and seed 1 for convergence).
Metrics: max abs error to the exact attribution (reference model), rank agreement with the graded field, share of exactly
zero cells, seconds per window, seed-to-seed rank spread.
"""
import json
import pickle
import time
from pathlib import Path

import numpy as np
import torch
import yaml

from degradx.attribution import methods as M
from degradx.generator.generate import Profile
from degradx.metrics.scores import rank_agreement
from degradx.models.lstm import LSTMRegressor, Standardiser, TrainedModel
from degradx.targets.decomposable import TargetSpec, unit_targets
from degradx.utils.seeding import rng

ROOT = Path(__file__).resolve().parents[3]
dd = yaml.safe_load((ROOT / "configs/declarations.yaml").read_text())["declared_by_design"]
ds = "NASA_PCoE"
prof = json.loads((ROOT / f"artifacts/s3_fit_profiles/profiles/{ds}.json").read_text())
units, table = pickle.loads((ROOT / f"data/generated/{ds}/seed0.pkl").read_bytes())
P = Profile.from_json(prof, np.concatenate([u.eps[:, len(prof["declared_used"]["channels_available"]) + 1] for u in units]))
spec = TargetSpec.build(P, dd["target"]["weights"]["beta"]["value"], 24, 6.0)
split = dict(zip(table["index"], table["split"]))
test = [u for u in units if split[u.index] == "test" and u.T >= 24]
g = rng(0, "evaluation", "D22")
W = []
for u in g.choice(len(test), size=12, replace=False):
    tg = unit_targets(test[u], spec, "recency")
    i = int(g.integers(len(tg["y"])))
    W.append((tg["x_pattern_free"][i], tg["graded"][i]))
X = np.stack([w[0] for w in W]).astype(np.float32)
ck = torch.load(ROOT / f"artifacts/s6_usability/models/{ds}_recency_A_seed0.pt", weights_only=False)
lm = LSTMRegressor(len(ck["channels"]), ck["arch"]["hidden_size"], ck["arch"]["num_layers"]); lm.load_state_dict(ck["state_dict"])
sc = ck["scaler"]
trained = M.RawSpaceModel(TrainedModel(lm.cuda(), Standardiser(np.asarray(sc["mean"]), np.asarray(sc["std"]), sc["y_mean"], sc["y_std"]), {}, "cuda"))
ref = M.ReferenceModel(spec.weights("recency"), spec.x0)
exact = spec.weights("recency")[None] * (X - spec.x0)
out = {}
for name, model in (("reference", ref), ("trained", trained)):
    for l1 in ("auto", False):
        t0 = time.perf_counter()
        A0 = M.timeshap(model, X, spec.x0, "cuda", seed=0, l1_reg=l1)
        dt = (time.perf_counter() - t0) / len(X)
        A1 = M.timeshap(model, X, spec.x0, "cuda", seed=1, l1_reg=l1)
        r0 = [rank_agreement(A0[i], W[i][1]) for i in range(len(W))]
        r1 = [rank_agreement(A1[i], W[i][1]) for i in range(len(W))]
        rec = {"seconds_per_window": dt, "rank_mean_seed0": float(np.nanmean(r0)), "rank_mean_seed1": float(np.nanmean(r1)),
               "zero_cell_share": float(np.mean(A0 == 0)), "max_abs_seed_diff": float(np.abs(A0 - A1).max())}
        if name == "reference":
            rec["max_abs_error_to_exact"] = float(np.abs(A0 - exact).max())
            rec["exact_scale"] = float(np.abs(exact).max())
        out[f"{name}/l1_reg={l1}"] = rec
        print(name, l1, json.dumps(rec), flush=True)
out["exact_rank_mean"] = float(np.nanmean([rank_agreement(exact[i], W[i][1]) for i in range(len(W))]))
Path(__file__).with_name("result.json").write_text(json.dumps(out, indent=1))
