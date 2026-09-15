"""D18 harness: origin of the generated degradation state.

For every theta unit of each S3 profile (the vectors the generator resamples), the family trajectory Q(n) = q1_j y(n) is
converted to z two ways:
  a  (current) z = (q1_j - Q(n)) / (q1_j - rho q_nom), q1_j the measured unit's robust early-life reference
  b  z = (Q_ref - Q(n)) / (Q_ref - rho q_nom), Q_ref = max of Q over the first k = 20 positions (Eq. 3's early-life
     reference applied to the generated trajectory itself)
Metrics: z at position 1 and at the reference position; T under each (identical by construction if Q_ref > rho q_nom);
the offset q1_j - Q_ref in mAh.
"""
import json
from pathlib import Path

import numpy as np

from degradx.fitting.families import FAMILIES

ROOT = Path(__file__).resolve().parents[3]
out = {}
for ds, qn in (("MATR", 1.1), ("HUST", 1.1), ("NASA_PCoE", 2.0)):
    prof = json.loads((ROOT / f"artifacts/s3_fit_profiles/profiles/{ds}.json").read_text())
    fam = prof["estimated_from_data"]["E1_theta_distribution"]["family"]
    rows = []
    for u in prof["estimated_from_data"]["E1_theta_distribution"]["per_unit"]:
        n = np.arange(1, int(3 * u["T"]) + 1, dtype=float)
        Q = u["q1"] * FAMILIES[fam](np.array(u["family_params"]), n)
        za = np.maximum((u["q1"] - Q) / (u["q1"] - 0.8 * qn), 0)
        qref = Q[:20].max()
        zb = np.maximum((qref - Q) / (qref - 0.8 * qn), 0)
        Ta = int(np.flatnonzero(za >= 1)[0]) + 1 if (za >= 1).any() else None
        Tb = int(np.flatnonzero(zb >= 1)[0]) + 1 if (zb >= 1).any() else None
        rows.append({"cell": u["cell_id"], "offset_mAh": float((u["q1"] - qref) * 1000), "z1_a": float(za[0]), "z1_b": float(zb[0]), "T_a": Ta, "T_b": Tb})
    off = np.array([r["offset_mAh"] for r in rows])
    out[ds] = {"units": len(rows), "z1_a_median": float(np.median([r["z1_a"] for r in rows])), "z1_a_max": float(np.max([r["z1_a"] for r in rows])),
               "z1_b_max": float(np.max([r["z1_b"] for r in rows])), "T_identical": int(sum(r["T_a"] == r["T_b"] for r in rows)),
               "offset_q1_minus_Qref_mAh_median": float(np.median(off)), "offset_max_mAh": float(off.max()), "per_unit": rows}
    print(ds, {k: v for k, v in out[ds].items() if k != "per_unit"})
Path(__file__).with_name("result.json").write_text(json.dumps(out, indent=1))
