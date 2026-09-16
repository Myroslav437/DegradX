"""Illustration for the programme report: attribution maps of one scored window, beside the attribution ground truth.

No measurement of its own — it reproduces the S8 window selection from the same seeds and draws the maps S8 saved in
``data/attributions``. Two figures in ``artifacts/report/figures``:
  attribution_example_MATR      graded field and the maps of the reference and trained model (rank agreement per panel)
  attribution_example_NASA      sparse set and the paired difference |A(x) - A(x without patterns)| that retrieval scores
"""
import json
import pickle
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
import s8_reference_methods as S  # noqa: E402

from degradx import ARTIFACTS_DIR, DATA_DIR  # noqa: E402
from degradx.generator.generate import Profile  # noqa: E402
from degradx.metrics.scores import rank_agreement, retrieval_ap  # noqa: E402
from degradx.targets.decomposable import TargetSpec, unit_targets  # noqa: E402
from degradx.utils.config import load_declarations  # noqa: E402
from degradx.utils.seeding import rng  # noqa: E402
from degradx.viz import style  # noqa: E402

SEED, KIND = 20260915, "recency"
dd = load_declarations()["declared_by_design"]
BETA, L = dd["target"]["weights"]["beta"]["value"], int(dd["target"]["window_length_L"]["value"])
OUT = ARTIFACTS_DIR / "report" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
LABEL = {"capacity": "capacity", "charge_time": "charge time", "mean_discharge_voltage": "mean discharge V",
         "internal_resistance": "internal resistance", "temperature_mean": "temperature", "null_flat": "null (flat)",
         "null_permuted": "null (permuted)"}


def setup(ds):
    prof = json.loads((ARTIFACTS_DIR / f"s3_fit_profiles/profiles/{ds}.json").read_text())
    units, table = pickle.loads((DATA_DIR / f"generated/{ds}/seed0.pkl").read_bytes())
    split = dict(zip(table["index"], table["split"]))
    test = [u for u in units if split[u.index] == "test"]
    P = Profile.from_json(prof, np.concatenate([u.eps[:, len(prof["declared_used"]["channels_available"]) + 1] for u in units]))
    spec = TargetSpec.build(P, BETA, L, 6.0)
    eligible, picks = S.select_windows(test, spec, 120, rng(SEED, "evaluation", "s8", ds))
    ts_idx = sorted(np.sort(rng(SEED, "evaluation", "s8-timeshap", ds).choice(len(picks), size=40, replace=False)).tolist())
    W = []
    for ui, e in picks:
        tg = unit_targets(eligible[ui], spec, KIND, ends=np.array([e]))
        W.append({"unit": eligible[ui].index, "end": e, "graded": tg["graded"][0], "sparse": tg["sparse"][0],
                  "sparse_mask": tg["sparse"][0] != 0})
    return spec, picks, ts_idx, W


def load(ds, model, method, seed=None):
    name = f"{ds}_{KIND}_{model}_{method}" + (f"_seed{seed}" if seed is not None else "")
    d = np.load(DATA_DIR / "attributions" / f"{name}.npz")
    return d["A"], d["Apf"], (d["idx"] if "idx" in d else None)


def heatmap(ax, M, channels, title, vmax=None):
    v = vmax or np.abs(M).max()
    D = np.sign(M) * np.sqrt(np.abs(M) / v)  # square-root shading: the maps concentrate on a few cells
    im = ax.imshow(D.T, aspect="auto", cmap="RdBu_r", vmin=-1, vmax=1, interpolation="nearest")
    ax.set_title(title, fontsize=7.5)
    ax.set_yticks(range(len(channels)), [LABEL.get(c, c) for c in channels], fontsize=6)
    ax.set_xticks([0, M.shape[0] // 2, M.shape[0] - 1], ["1", str(M.shape[0] // 2 + 1), str(M.shape[0])], fontsize=6)
    return im


def figure_matr():
    ds = "MATR"
    spec, picks, ts_idx, W = setup(ds)
    ig_t, _, _ = load(ds, "trained", "integrated_gradients")
    oc_t, _, _ = load(ds, "trained", "feature_occlusion")
    ts_t, _, idx = load(ds, "trained", "timeshap", 0)
    ig_r, _, _ = load(ds, "reference", "integrated_gradients")
    # a window from the TimeSHAP subset whose trained-IG score is the median of that subset: neither best nor worst case
    ranks = np.array([rank_agreement(ig_t[i], W[i]["graded"]) for i in idx])
    pick = int(idx[int(np.argsort(ranks)[len(ranks) // 2])])
    j = list(idx).index(pick)
    panels = [("attribution ground truth\n(graded field)", W[pick]["graded"]), ("reference model, IG\n(= exact)", ig_r[pick]),
              ("trained model, IG", ig_t[pick]), ("trained model, occlusion", oc_t[pick]), ("trained model, TimeSHAP", ts_t[j])]
    style.apply()
    fig, axes = plt.subplots(1, len(panels), figsize=(style.TEXTWIDTH_IN * 1.35, 2.5), sharey=True)
    for ax, (title, M) in zip(axes, panels):
        r = rank_agreement(M, W[pick]["graded"])
        heatmap(ax, M, spec.channels, f"{title}\nrank agreement {r:.2f}" if "ground truth" not in title else title + "\n ")
        ax.set_xlabel("position in window", fontsize=6.5)
    fig.suptitle(f"MATR, recency weighting: unit {W[pick]['unit']}, window ending at position {W[pick]['end']}"
                 " — square-root shading, each panel scaled to its own maximum", fontsize=8)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"attribution_example_MATR.{ext}", dpi=200)
    plt.close(fig)
    print("MATR window", W[pick]["unit"], W[pick]["end"], "ranks", {t: round(float(rank_agreement(M, W[pick]["graded"])), 3) for t, M in panels})


def figure_nasa():
    ds = "NASA_PCoE"
    spec, picks, ts_idx, W = setup(ds)
    ig_t, ig_t_pf, _ = load(ds, "trained", "integrated_gradients")
    ig_r, ig_r_pf, _ = load(ds, "reference", "integrated_gradients")
    cand = [i for i in range(len(W)) if W[i]["sparse_mask"].any()]
    pick = cand[int(np.argsort([W[i]["sparse_mask"].sum() for i in cand])[len(cand) // 2])]
    panels = [("inserted patterns\n(sparse set)", W[pick]["sparse"], None),
              ("reference model, IG:\npaired difference", np.abs(ig_r[pick] - ig_r_pf[pick]),
               retrieval_ap(ig_r[pick] - ig_r_pf[pick], W[pick]["sparse_mask"])),
              ("trained model, IG:\npaired difference", np.abs(ig_t[pick] - ig_t_pf[pick]),
               retrieval_ap(ig_t[pick] - ig_t_pf[pick], W[pick]["sparse_mask"])),
              ("trained model, IG:\nsingle map", np.abs(ig_t[pick]),
               retrieval_ap(ig_t[pick], W[pick]["sparse_mask"]))]
    style.apply()
    fig, axes = plt.subplots(1, len(panels), figsize=(style.TEXTWIDTH_IN * 1.15, 2.5), sharey=True)
    for ax, (title, M, ap) in zip(axes, panels):
        heatmap(ax, M, spec.channels, title + (f"\nretrieval AP {ap:.2f}" if ap is not None else "\n "))
        ax.set_xlabel("position in window", fontsize=6.5)
    fig.suptitle(f"NASA PCoE, recency weighting: unit {W[pick]['unit']}, window ending at position {W[pick]['end']}"
                 " — square-root shading, each panel scaled to its own maximum", fontsize=8)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"attribution_example_NASA.{ext}", dpi=200)
    plt.close(fig)
    print("NASA window", W[pick]["unit"], W[pick]["end"], "sparse cells", int(W[pick]["sparse_mask"].sum()),
          "AP", [None if a is None else round(float(a), 3) for _, _, a in panels])


if __name__ == "__main__":
    figure_matr()
    figure_nasa()
