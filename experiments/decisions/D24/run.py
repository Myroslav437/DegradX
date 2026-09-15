"""D24 harness: Table 6 layout. Compares the declared caption's layout (values averaged over profiles that pass the
usability checks) with per-profile rows, on the S8 results: does averaging preserve each profile's ordering of the
methods, and can the ensemble range (C2) be stated for an average at all?"""
import itertools
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
R = json.loads((ROOT / "artifacts/s8_reference_methods/tables/reference_values.json").read_text())
U = {ds: json.loads((ROOT / f"artifacts/s6_usability/tables/usability_{ds}.json").read_text())[ds] for ds in R}
METHODS = ("timeshap", "integrated_gradients", "feature_occlusion")
out = {}
for kind in ("recency", "uniform", "final_position"):
    passing = [ds for ds in R if U[ds][kind]["gate_pass_primary"]]
    per = {ds: {m: R[ds]["weightings"][kind]["scores"][f"trained/{m}"]["rank"]["mean"] for m in METHODS} for ds in passing}
    avg = {m: float(np.mean([per[ds][m] for ds in passing])) for m in METHODS}
    order = lambda d: sorted(METHODS, key=lambda m: -d[m])
    floors = {ds: {m: [R[ds]["weightings"][kind]["identifiability_floor"][m][k] for k in ("rank_min", "rank_max")]
                   for m in ("integrated_gradients", "feature_occlusion")} for ds in passing}
    # largest between-method difference on the trained model vs the width of the ensemble range, per profile
    gaps = {ds: {"max_between_method_difference": max(abs(per[ds][a] - per[ds][b]) for a, b in itertools.combinations(METHODS, 2)),
                 "ensemble_range_width_ig": floors[ds]["integrated_gradients"][1] - floors[ds]["integrated_gradients"][0],
                 "ensemble_range_width_occlusion": floors[ds]["feature_occlusion"][1] - floors[ds]["feature_occlusion"][0]} for ds in passing}
    spread = {m: [min(per[ds][m] for ds in passing), max(per[ds][m] for ds in passing)] for m in METHODS}
    out[kind] = {"profiles_passing": passing, "per_profile_rank_trained": per, "averaged_rank_trained": avg,
                 "order_averaged": order(avg), "order_per_profile": {ds: order(per[ds]) for ds in passing},
                 "orders_agree_with_average": {ds: order(per[ds]) == order(avg) for ds in passing},
                 "between_profile_range_per_method": spread, "ensemble_range_per_profile": floors, "gaps": gaps}
(Path(__file__).parent / "result.json").write_text(json.dumps(out, indent=2))
for kind, o in out.items():
    print(kind, "avg", {m[:4]: round(v, 3) for m, v in o["averaged_rank_trained"].items()}, "order avg", [m[:4] for m in o["order_averaged"]])
    for ds in o["profiles_passing"]:
        print("  ", ds, [m[:4] for m in o["order_per_profile"][ds]], {k: round(v, 3) for k, v in o["gaps"][ds].items()})
