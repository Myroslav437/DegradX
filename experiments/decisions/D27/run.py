"""D27 — held-out MATR charge-time excursions: extend D17 to short multi-cycle excursions, or keep the cells and report?

For MATR and HUST (v1 profiles, v1 S3 split), every measured non-capacity channel, both splits: readings masked and the
pooled residual variance / lag-1 autocorrelation about the v1 mapping phi_c(z) (S3 estimator, fit range t1..T) under
candidate channel rules: D17 (max_run 1), max_run 2, 3, 5; and the unit/position behind the held-out charge-time variance.
Writes result.json next to this file. Brief "DegradX v2" V1 (D27).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from degradx import ARTIFACTS_DIR, CONFIG_DIR, DATA_DIR
from degradx.data.audit import CleaningRule
from degradx.fitting.noise_mappings import Mapping, ar1_from_residuals
from degradx.fitting.profile import ChannelRule, prepare_units
from degradx.generator.state import spec_from_declarations
from degradx.utils.config import load_declarations, load_yaml

HERE = Path(__file__).parent
decl = load_declarations()
dd = decl["declared_by_design"]
RULE = CleaningRule("D12", **dd["capacity_series"]["cleaning_rule"]["params"])
RULES = {"D17_max_run_1": ChannelRule(0.05, 1), "max_run_2": ChannelRule(0.05, 2), "max_run_3": ChannelRule(0.05, 3), "max_run_5": ChannelRule(0.05, 5)}
out = {}
for ds, pf in (("MATR", "matr"), ("HUST", "hust")):
    prof = json.loads((ARTIFACTS_DIR / "s3_fit_profiles" / "profiles" / f"{ds}.json").read_text())
    chans = prof["declared_used"]["channels_available"]
    q_nom = float(load_yaml(CONFIG_DIR / "profiles" / f"{pf}.yaml")["nominal_capacity_Ah"]["value"])
    spec = spec_from_declarations(decl, q_nom)
    split = pd.read_csv(ARTIFACTS_DIR / "s3_fit_profiles" / "tables" / f"split_{ds}.csv")
    df = pd.read_csv(DATA_DIR / "processed" / "cycle_tables" / f"{ds}.csv.gz", low_memory=False)
    maps = {c: Mapping(c, np.asarray(d["grid"]), np.asarray(d["values"]), bool(d["increasing"]), d["kind"])
            for c, d in prof["estimated_from_data"]["E3_channel_mappings"].items()}
    out[ds] = {}
    for rname, cr in RULES.items():
        out[ds][rname] = {}
        for sp in ("fitting", "held_out"):
            units = prepare_units(df, split.loc[split["split"] == sp, "cell_id"], q_nom, spec, RULE, chans, cr)
            res = {}
            for c in chans:
                if c == "capacity":
                    continue
                resid, masked, total, per_unit = [], 0, 0, []
                for u in units:
                    sl = slice(u.fit_start - 1, u.fit_end)
                    x = u.channels[c][sl]
                    raw = df.loc[df["cell_id"] == u.cell_id]
                    r = x - maps[c](u.state.z[sl])
                    resid.append(r)
                    masked += int(np.sum(~np.isfinite(x)))
                    total += int(len(x))
                    rc = r - np.nanmean(r)
                    per_unit.append((u.cell_id, float(np.nansum(rc ** 2)), int(np.isfinite(r).sum()), float(np.nanmax(np.abs(rc)))))
                a = ar1_from_residuals(resid)
                per_unit.sort(key=lambda t: -t[1])
                tot_ss = sum(t[1] for t in per_unit)
                res[c] = {"pooled_variance": a.variance, "lag1": a.phi, "positions": total, "masked": masked, "masked_frac": masked / total,
                          "top_unit": per_unit[0][0], "top_unit_share_of_sum_sq": per_unit[0][1] / tot_ss, "top_unit_max_abs_residual": per_unit[0][3]}
            out[ds][rname][sp] = res
            print(ds, rname, sp, {c: (f"{v['pooled_variance']:.4g}", f"{v['lag1']:.3f}", v["masked"], v["top_unit"], f"{v['top_unit_share_of_sum_sq']:.2f}") for c, v in res.items()}, flush=True)
(HERE / "result.json").write_text(json.dumps(out, indent=1))
