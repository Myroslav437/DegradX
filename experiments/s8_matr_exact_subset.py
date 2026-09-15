"""Post-hoc for the MATR S8 run (made before the subset ceiling was added): exact reference-model attribution scored on the
TimeSHAP window subset, using the S8 script's own seeded window selection. Writes the entry into reference_values.json."""
import json, pickle, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import s8_reference_methods as S
from degradx import ARTIFACTS_DIR, DATA_DIR
from degradx.generator.generate import Profile
from degradx.targets.decomposable import TargetSpec, unit_targets
from degradx.utils.config import load_declarations
from degradx.utils.seeding import rng
dd = load_declarations()["declared_by_design"]
ds, seed = "MATR", 20260915
prof = json.loads((ARTIFACTS_DIR / "s3_fit_profiles/profiles/MATR.json").read_text())
units, table = pickle.loads((DATA_DIR / "generated/MATR/seed0.pkl").read_bytes())
split = dict(zip(table["index"], table["split"]))
test = [u for u in units if split[u.index] == "test"]
P = Profile.from_json(prof, np.concatenate([u.eps[:, len(prof["declared_used"]["channels_available"]) + 1] for u in units]))
spec = TargetSpec.build(P, dd["target"]["weights"]["beta"]["value"], 24, 6.0)
eligible, picks = S.select_windows(test, spec, 120, rng(seed, "evaluation", "s8", ds))
ts_idx = sorted(np.sort(rng(seed, "evaluation", "s8-timeshap", ds).choice(len(picks), size=40, replace=False)).tolist())
saved = np.load(DATA_DIR / "attributions/MATR_recency_reference_timeshap_seed0.npz")
assert list(saved["idx"]) == ts_idx, "window subset mismatch"
path = ARTIFACTS_DIR / "s8_reference_methods/tables/reference_values.json"
R = json.loads(path.read_text())
zero_ch = np.flatnonzero(spec.kappa == 0)
for kind in ("recency", "uniform", "final_position"):
    W = []
    for ui, e in picks:
        tg = unit_targets(eligible[ui], spec, kind, ends=np.array([e]))
        W.append({"unit": ui, "graded": tg["graded"][0], "sparse_mask": tg["sparse"][0] != 0, "x": tg["x"][0], "xpf": tg["x_pattern_free"][0]})
    X = np.stack([W[i]["x"] for i in ts_idx]); Xpf = np.stack([W[i]["xpf"] for i in ts_idx])
    Wt = spec.weights(kind)
    sc = S.score_maps(Wt[None] * (X - spec.x0), Wt[None] * (Xpf - spec.x0), [W[i] for i in ts_idx], zero_ch)
    R[ds]["weightings"][kind]["scores"]["reference_exact_timeshap_windows"] = {k: S.unit_mean_ci(v, [W[i]["unit"] for i in ts_idx], seed) for k, v in sc.items()}
    ts = np.load(DATA_DIR / f"attributions/MATR_{kind}_reference_timeshap_seed0.npz")["A"]
    print(kind, "exact on subset", R[ds]["weightings"][kind]["scores"]["reference_exact_timeshap_windows"]["rank"]["mean"],
          "max |timeshap - exact|", float(np.abs(ts - Wt[None] * (X - spec.x0)).max()))
path.write_text(json.dumps(R, indent=2) + "\n")
