#!/usr/bin/env python
"""S04b — post-hoc sensitivity of the FORM mechanism diagnostic (NOT declared; reported beside the declared separability reading, never replacing it).

At S04 most 'gap' rest events of the declared rule sat one position after a diagnostic event: the first aging cycle after a
diagnostic block charges from the RPT's C/5 (or HPPC's held) discharge and lasts longer than its neighbours, so the declared gap
rule reads the next start-to-start interval as a pause. Such events echo the diagnostic interruption one cycle later. This script
repeats the mechanism diagnostic on the non-diagnostic rest events that have no diagnostic event in the 11 preceding positions
(their placebo window cannot contain a diagnostic event), on the same fitting units, residuals and run detection as s04_audit_form.py.
Writes artifacts/s04_audit_form/tables/mechanism_posthoc.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import _common as C  # noqa: E402
from degradx.data import mechanism as MECH  # noqa: E402
import s04_audit_form as A  # noqa: E402
from degradx.data.audit import CleaningRule, clean_capacity  # noqa: E402
from degradx.fitting.profile import fit_profile  # noqa: E402
from degradx.generator.state import spec_from_declarations  # noqa: E402
from degradx.utils.config import load_declarations  # noqa: E402
from degradx import ARTIFACTS_DIR  # noqa: E402


def main() -> int:
    decl = load_declarations()
    dd = decl["declared_by_design"]
    seed = 20260915
    q_nom = C.q_nom_of(A.DS)
    spec = spec_from_declarations(decl, q_nom)
    rule = CleaningRule("D12", **dd["capacity_series"]["cleaning_rule"]["params"])
    crule = C.channel_rule(dd)
    k = float(dd["pattern_detection"]["multiple_k"]["value"])
    m = int(dd["pattern_detection"]["min_run_length"]["value"])
    W = int(dd["smoothing"]["window_length"]["value"])
    n_boot = int(dd["protocol"]["statistics"]["bootstrap_n_resamples"])
    out = ARTIFACTS_DIR / "s04_audit_form" / "tables"
    df = C.load_scope(A.DS, dd)
    split = pd.read_csv(out / f"split_{A.DS}.csv")
    channels = C.available_channels(df)
    prof, diag = fit_profile(df, split, dataset=A.DS, q_nom=q_nom, spec=spec, rule=rule, channels=channels, crule=crule, decl=decl,
                             workers=8, k=k, m=m, sweep_k=dd["pattern_detection"]["sweep"]["multiple_k"], base_seed=seed, offsets=C.offsets_params(dd))
    fam = prof["estimated_from_data"]["E2_family_choice"]["selected"]
    runs = []
    for u in diag["unit_objects"]:
        g_raw = df[df["cell_id"] == u.cell_id].copy()
        g_cl = clean_capacity(g_raw, "capacity_cycler_Ah", rule, q_nom)
        src = g_raw["rest_event_source"].fillna("").astype(str).to_numpy()
        pos = g_raw["position"].to_numpy()
        diag_pos = pos[src == "diagnostic"]
        far = np.array([s_ in ("paused", "gap", "file") and not np.any((p_ - diag_pos >= 1) & (p_ - diag_pos <= 11)) for s_, p_ in zip(src, pos)])
        near = np.array([s_ in ("paused", "gap", "file") and bool(np.any((p_ - diag_pos >= 1) & (p_ - diag_pos <= 11))) for s_, p_ in zip(src, pos)])
        sets = {}
        for name, sel in (("non_diagnostic_far", far), ("non_diagnostic_within_11_after_diagnostic", near)):
            sets[name] = MECH.rest_positions(g_cl, g_raw.assign(rest_event=sel))
        runs.append(A.unit_runs_form(u, fam, sets, k, m, W))
    res = {"note": "post-hoc, not declared: the declared separability reading (audit_summary.json) stands; this separates gap events that echo a diagnostic block",
           **{name: {"post_0_10": A.mech(runs, name, seed, n_boot), "placebo_-11_-1": A.mech(runs, name, seed, n_boot, -11, -1)}
              for name in ("non_diagnostic_far", "non_diagnostic_within_11_after_diagnostic")}}
    (out / "mechanism_posthoc.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
