"""D01 harness: scoring the sparse set when the graded field dominates (NASA PCoE, the only profile with patterns, D05).

Windows: generated NASA PCoE units (generation seed 0, all splits), recency weighting, windows with >= 1 sparse cell;
at most 1500 windows drawn with the 'evaluation' seed stream. For each declared S7 operator and magnitude, the ground
truth phi* is degraded; retrieval of the sparse set is scored three ways:
  plain      AP of |degraded phi*|
  paired     AP of |degraded phi* - degraded graded|; the two degradations draw independent randomness (a method run on the
             pattern-free counterpart window does not share the degradation), except deterministic operators
  detrended  AP of |degraded phi* - SG-smooth(degraded phi*)| (declared window 11, order 2, along positions)
Also: the reference model's exact attribution w(x - x0) (noise included) under each variant, and graded-field rank agreement
plain (degraded phi* vs graded) vs paired (degraded graded vs graded).
Metrics: undegraded score (ceiling), chance (random permutation of cells), monotonicity of the mean score over the
magnitude grid (number of increases), and the SD of the score over windows.
"""
import json
import pickle
from pathlib import Path

import numpy as np
import yaml

from degradx.generator.generate import Profile
from degradx.metrics.scores import OPERATORS, detrend, rank_agreement, retrieval_ap
from degradx.targets.decomposable import TargetSpec, unit_targets
from degradx.utils.seeding import rng

ROOT = Path(__file__).resolve().parents[3]
decl = yaml.safe_load((ROOT / "configs/declarations.yaml").read_text())
dd = decl["declared_by_design"]
units, table = pickle.loads((ROOT / "data/generated/NASA_PCoE/seed0.pkl").read_bytes())
prof = json.loads((ROOT / "artifacts/s3_fit_profiles/profiles/NASA_PCoE.json").read_text())
P = Profile.from_json(prof, np.array([160.0]))  # null pool irrelevant here (zero weight); x0 of null_permuted unused
spec = TargetSpec.build(P, dd["target"]["weights"]["beta"]["value"], int(dd["target"]["window_length_L"]["value"]), 6.0)
W = []
for u in units:
    if u.T < spec.L:
        continue
    tg = unit_targets(u, spec, "recency")
    keep = np.flatnonzero(np.abs(tg["sparse"]).sum(axis=(1, 2)) > 0)
    for i in keep:
        W.append((tg["phi_star"][i], tg["graded"][i], tg["sparse"][i] != 0, spec.weights("recency") * (tg["x"][i] - spec.x0), spec.weights("recency") * (tg["x_pattern_free"][i] - spec.x0)))
g = rng(0, "evaluation", "D01")
sel = g.choice(len(W), size=min(1500, len(W)), replace=False)
W = [W[i] for i in sel]
ops = dd["responsiveness"]["operators"]
out = {"windows": len(W), "operators": {}}


def scores(phi, grd, lab, gen1, gen2, op, mag):
    f = OPERATORS[op]
    d1 = f(phi, mag, gen1) if op != "added_noise" else f(phi, mag, gen1, scale=np.std(phi))
    d2 = f(grd, mag, gen2) if op != "added_noise" else f(grd, mag, gen2, scale=np.std(phi))
    return (retrieval_ap(d1, lab), retrieval_ap(d1 - d2, lab), retrieval_ap(detrend(d1), lab), rank_agreement(d1, grd), rank_agreement(d2, grd))


for op, cfg in ops.items():
    if op == "source":
        continue
    rows = []
    for mag in cfg["grid"]:
        vals = []
        for wi, (phi, grd, lab, wx, wxpf) in enumerate(W):
            g1, g2 = rng(1, "evaluation", "D01", op, mag, wi, "a"), rng(1, "evaluation", "D01", op, mag, wi, "b")
            vals.append(scores(phi, grd, lab, g1, g2, op, mag))
        v = np.array(vals, float)
        rows.append({"magnitude": mag, "plain_mean": float(np.nanmean(v[:, 0])), "plain_sd": float(np.nanstd(v[:, 0])),
                     "paired_mean": float(np.nanmean(v[:, 1])), "paired_sd": float(np.nanstd(v[:, 1])),
                     "detrended_mean": float(np.nanmean(v[:, 2])), "detrended_sd": float(np.nanstd(v[:, 2])),
                     "rank_plain_mean": float(np.nanmean(v[:, 3])), "rank_paired_mean": float(np.nanmean(v[:, 4]))})
    out["operators"][op] = rows
    for key in ("plain", "paired", "detrended", "rank_plain", "rank_paired"):
        seq = [r[f"{key}_mean"] for r in rows]
        out.setdefault("monotone_increases", {}).setdefault(op, {})[key] = int(np.sum(np.diff(seq) > 1e-9))
    print(op, json.dumps(rows[0]), json.dumps(rows[-1]), out["monotone_increases"][op], flush=True)
# chance and reference-model ceilings
chance = []
for wi, (phi, grd, lab, wx, wxpf) in enumerate(W):
    gg = rng(2, "evaluation", "D01", wi)
    chance.append(retrieval_ap(gg.permutation(phi.ravel()).reshape(phi.shape), lab))
out["chance_ap_mean"] = float(np.nanmean(chance))
out["positive_rate_mean"] = float(np.mean([lab.mean() for _, _, lab, _, _ in W]))
ref = np.array([(retrieval_ap(wx, lab), retrieval_ap(wx - wxpf, lab), retrieval_ap(detrend(wx), lab), rank_agreement(wxpf, grd)) for phi, grd, lab, wx, wxpf in W])
out["reference_model_exact_attribution"] = {"plain": float(np.nanmean(ref[:, 0])), "paired": float(np.nanmean(ref[:, 1])),
                                            "detrended": float(np.nanmean(ref[:, 2])), "rank_paired": float(np.nanmean(ref[:, 3]))}
Path(__file__).with_name("result.json").write_text(json.dumps(out, indent=1))
print("chance", out["chance_ap_mean"], "positive rate", out["positive_rate_mean"], "reference model", out["reference_model_exact_attribution"])
