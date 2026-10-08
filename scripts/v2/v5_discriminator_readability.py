#!/usr/bin/env python
"""V5 addendum — the D02b readability rule for the discriminative error, applied (declarations
minimum_counts.held_out_units_per_measure.discriminative_error.readability: 95% half-width <= 0.5 |0.5 - value|).

V5 applied only the D02b minimum count (8 held-out units), as v1 S5 did. This re-runs the seeded discriminators of V5 with
their test predictions kept (accuracies reproduce V5 exactly, checked), and computes per generation seed a unit bootstrap
(10 000 percentile resamples of measured and generated test units) of the discriminative error. A seed's value is readable
iff its half-width <= 0.5 |0.5 - value|; the Table 1 cell is readable iff every seed's value is. Writes
``tables/discriminator_readability.json`` in ``artifacts/v2/v5_fidelity``.
"""

from __future__ import annotations

import json
import pickle
import sys

import numpy as np

import _common as C
from degradx import ARTIFACTS_V2, DATA_V2
from degradx.data.audit import CleaningRule
from degradx.fitting.profile import prepare_units
from degradx.generator.state import spec_from_declarations
from degradx.metrics import fidelity as F
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.io import write_json


def unit_bootstrap_error(correct, units, is_gen, seed, n):
    g = np.random.default_rng(seed)
    mu = np.unique(units[~is_gen])
    gu = np.unique(units[is_gen])
    rows = {u: np.flatnonzero(units == u) for u in np.concatenate([mu, gu])}
    vals = []
    for _ in range(n):
        pick = np.concatenate([g.choice(mu, len(mu)), g.choice(gu, len(gu))])
        idx = np.concatenate([rows[u] for u in pick])
        vals.append(1.0 - correct[idx].mean())
    lo, hi = np.quantile(vals, [0.025, 0.975])
    return float(lo), float(hi)


def main() -> int:
    p = stage_parser(__doc__, "v2/v5_fidelity")
    p.add_argument("--datasets", nargs="*", default=["MATR", "HUST"])
    p.add_argument("--max-windows-per-unit", type=int, default=100)
    args = p.parse_args()
    ctx = StageContext.from_args(args)
    decl, dd = ctx.declarations, ctx.declarations["declared_by_design"]
    if args.dry_run:
        print("plan: discriminator readability")
        return 0
    n_boot = int(dd["v2"]["statistics"]["bootstrap_n_resamples"])
    L = int(dd["target"]["window_length_L"]["value"])
    rule = CleaningRule("D12", **dd["capacity_series"]["cleaning_rule"]["params"])
    crule = C.channel_rule_v2(dd)
    fid = json.loads((ARTIFACTS_V2 / "v5_fidelity" / "tables" / "fidelity.json").read_text())
    out = {}
    for ds in args.datasets:
        prof = C.v2_profile(ds)
        chans = prof["declared_used"]["channels_available"]
        q_nom = C.q_nom_of(ds)
        spec = spec_from_declarations(decl, q_nom)
        split = C.v2_split(ds)
        df = C.load_scope(ds, dd)
        fit_u = prepare_units(df, split.loc[split["split"] == "fitting", "cell_id"], q_nom, spec, rule, chans, crule)
        ho_u = prepare_units(df, split.loc[split["split"] == "held_out", "cell_id"], q_nom, spec, rule, chans, crule)
        ms_fit, ms_ho = F.measured_series(fit_u, chans), F.measured_series(ho_u, chans)
        Wf, _, _ = F.windows(ms_fit, L, max_per_unit=args.max_windows_per_unit, seed=args.seed)
        Wh, Uh, _ = F.windows(ms_ho, L, max_per_unit=args.max_windows_per_unit, seed=args.seed)
        flat = Wf.reshape(-1, Wf.shape[-1])
        mu, sd = flat.mean(axis=0), np.where(flat.std(axis=0) > 0, flat.std(axis=0), 1.0)
        seeds = []
        for s in fid[ds]["per_generation_seed"]:
            g = s["generation_seed"]
            units = pickle.loads((DATA_V2 / "generated" / ds / f"seed{g}.pkl").read_bytes())[0]
            gs = F.generated_series(units, len(chans))
            Wg, Ug, _ = F.windows(gs, L, max_per_unit=args.max_windows_per_unit, seed=args.seed + g)
            d = F.discriminative_score(Wh, Uh, Wg, Ug, mu, sd, seed=args.seed + g, device=ctx.device, return_predictions=True)
            lo, hi = unit_bootstrap_error(d["_correct"], d["_units"], d["_is_generated"], args.seed, n_boot)
            err = d["discriminative_error"]
            half = (hi - lo) / 2
            seeds.append({"generation_seed": g, "discriminative_error": err, "v5_value": s["discriminative_error"], "reproduces_v5": abs(err - s["discriminative_error"]) < 1e-12,
                          "ci_low": lo, "ci_high": hi, "half_width": half, "bound": 0.5 * abs(0.5 - err), "readable": bool(half <= 0.5 * abs(0.5 - err)),
                          "test_units": d["test_units"]})
            print(f"[v5-disc] {ds} seed {g}: {err:.3f} [{lo:.3f}, {hi:.3f}] half {half:.3f} bound {0.5 * abs(0.5 - err):.3f} readable {seeds[-1]['readable']}", flush=True)
        out[ds] = {"per_generation_seed": seeds, "readable": bool(all(x["readable"] for x in seeds)),
                   "void_reason": None if all(x["readable"] for x in seeds) else "discriminative-error interval wider than half its distance from 0.5 (D02b readability)"}
    write_json(out, ARTIFACTS_V2 / "v5_fidelity" / "tables" / "discriminator_readability.json")
    bad = [ds for ds in out for x in out[ds]["per_generation_seed"] if not x["reproduces_v5"]]
    if bad:
        print("WARNING: discriminator did not reproduce V5 for", bad)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
