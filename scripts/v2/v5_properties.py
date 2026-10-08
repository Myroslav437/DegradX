#!/usr/bin/env python
"""V5 addendum — the property table re-run under D30 (generated series read with D13's record-end clause, as measured
records are) and with the residual-correlation row split into capacity and non-capacity pairs (v2 pipeline review).
The first V5 table is kept as ``tables/properties_<ds>_run1.json``. Outputs in ``artifacts/v2/v5_fidelity``.
"""

from __future__ import annotations

import pickle
import shutil
import sys

import pandas as pd

import _common as C
import v5_fidelity as V5
from degradx import ARTIFACTS_V2, DATA_V2
from degradx.data.audit import CleaningRule
from degradx.fitting.profile import fit_profile
from degradx.generator.state import spec_from_declarations
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.io import save_figure, write_json


def main() -> int:
    p = stage_parser(__doc__, "v2/v5_fidelity")
    p.add_argument("--datasets", nargs="*", default=["MATR", "HUST"])
    p.add_argument("--workers", type=int, default=8)
    args = p.parse_args()
    ctx = StageContext.from_args(args)
    decl, dd = ctx.declarations, ctx.declarations["declared_by_design"]
    if args.dry_run:
        return 0
    from degradx.viz import s5 as viz

    out = ARTIFACTS_V2 / "v5_fidelity"
    rule = CleaningRule("D12", **dd["capacity_series"]["cleaning_rule"]["params"])
    crule = C.channel_rule_v2(dd)
    offs = C.offsets_params(dd)
    minimum = dd["minimum_counts"]["value"]
    for ds in args.datasets:
        prof = C.v2_profile(ds)
        chans = prof["declared_used"]["channels_available"]
        q_nom = C.q_nom_of(ds)
        spec = spec_from_declarations(decl, q_nom)
        split = C.v2_split(ds)
        df = C.load_scope(ds, dd)
        f = out / "tables" / f"properties_{ds}.json"
        if f.exists() and not (out / "tables" / f"properties_{ds}_run1.json").exists():
            shutil.copy(f, out / "tables" / f"properties_{ds}_run1.json")
        ho_split = split[split["split"] == "held_out"].assign(split="fitting")
        meas_ho, _ = fit_profile(df, ho_split, dataset=ds, q_nom=q_nom, spec=spec, rule=rule, channels=chans, crule=crule, decl=decl,
                                 workers=args.workers, k=2.5, m=2, sweep_k=[2.5], base_seed=args.seed, offsets=offs)
        units = pickle.loads((DATA_V2 / "generated" / ds / "seed0.pkl").read_bytes())[0]
        gdf = V5.generated_frame(units, chans)
        gsplit = pd.DataFrame({"cell_id": gdf["cell_id"].unique(), "split": "fitting", "reaches_eol": True})
        gen_prof, _ = fit_profile(gdf, gsplit, dataset=ds, q_nom=q_nom, spec=spec, rule=rule, channels=chans, crule=crule, decl=decl,
                                  workers=args.workers, k=2.5, m=2, sweep_k=[2.5], base_seed=args.seed, offsets=offs)
        rows = V5.property_rows(ds, {"fitting": prof, "held_out": meas_ho, "generated": gen_prof}, q_nom, spec.rho, minimum)
        for r in rows:
            r["note"] = "D30: generated series read with D13's record-end clause"
        write_json(rows, f)
        save_figure(viz.property_distributions(ds, meas_ho, gen_prof, q_nom, spec.rho), out / "figures" / f"{ds.lower()}_property_distributions")
        print(f"[v5-props] {ds}: generated units reaching EOL {gen_prof['estimated_from_data']['E1_theta_distribution']['n_units']} of {len(units)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
