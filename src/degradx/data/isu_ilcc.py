"""ISU-ILCC Battery Aging Dataset (figshare 10.25380/iastate.22582234 v2, CC BY 4.0; Li et al., Cell Rep. Phys. Sci. 5:101891,
2024) to a DegradX cycle table, under the declared extraction of decision D28 (declarations r3
``declared_by_design.v2.third_profile.candidate_rules``).

Raw layout (README_V2.0 §4; the dataset's own loader process_data.py): one double-encoded JSON per cell in
``Cycling_json/<Release>/<cell>.json`` and ``RPT_json/<Release>/<cell>.json``.
  Cycling: capacity_discharge / capacity_charge per aging cycle [Ah]; QV_discharge / QV_charge {Q, V, I, E, t} per cycle;
           time_series_charge / time_series_discharge {start, stop} per cycle; start_stop_time {start, stop} per weekly block.
  RPT:     capacity_discharge_C_5 per RPT [Ah] ('[]' if lost); start_stop_time per RPT.

D28 extraction, per cell (order as declared):
  1 predicates on raw cycles. degenerate: < 10 samples, capacity_discharge non-finite/<= 0/empty, or a missing charge or
    discharge start time; incomplete: last discharge voltage > the unit's median last-discharge voltage + 0.02 V, or last
    charge current > 0.025 A (2 x C/20); non-aging: overlaps an RPT start-stop interval, or median |discharge current|
    departs > 10% from the group's discharge C-rate x 0.25 A. Degenerate and incomplete cycles are flagged ``degenerate``
    (the D12 rule drops them from the positions); non-aging cycles are excluded from the table. All counted.
  2 anchors from unmasked cycles: every RPT w with a finite C/5 and >= 5 unmasked cycles before its start gives
    f_w = C5_w / median of the last 5 (knot at the last); the week-0 anchor is C5_0 / median of the first 5 unmasked
    cycles (knot at the last of those).
  3 f = PCHIP over the knots, constant beyond the first and last knot; fewer than 2 anchors: reported, no table.
  4 capacity_cycler_Ah = capacity_discharge x f. (D12 then runs on this series in the S2/S3 machinery.)
  channels: charge_time_min from time_series_charge start/stop, missing by protocol at every RPT-following rest event;
            mean_discharge_voltage_V = time-weighted mean voltage over the discharge samples.
  rest events: the first unmasked aging cycle of each Cycling block after the first, and the first cycle after a pause
            (discharge stop to next charge start more than 30 min above the unit's median gap); never position 1; RPT
            stop times as a cross-check (mismatches counted).
Every row keeps the raw aging capacity and f; the additive variant g (C5_w - anchor median, PCHIP) is stored as well.
"""

from __future__ import annotations

import io
import json
import zipfile
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

ANCHOR_CYCLES = 5
INCOMPLETE_DV = 0.02          # V above the unit's median last-discharge voltage
INCOMPLETE_I = 0.025          # A, 2 x C/20 at 0.25 Ah
NONAGING_REL_I = 0.10         # relative departure of the median discharge current from C-rate x 0.25 A
PAUSE_EXTRA_S = 30 * 60       # recorded pause: gap above the unit's median gap by more than this
Q_RATED = 0.25


def load_json_from_zip(zf: zipfile.ZipFile, member: str) -> dict:
    """The files are JSON strings containing JSON (process_data: json.loads(json.load(file)))."""
    with zf.open(member) as fh:
        obj = json.load(io.TextIOWrapper(fh, encoding="utf-8"))
    return json.loads(obj) if isinstance(obj, str) else obj


def _ts(x) -> float:
    if x is None or (isinstance(x, (list, str)) and len(x) == 0) or x == "[]":
        return np.nan
    return float(np.datetime64(x, "ms").astype("int64")) / 1000.0


def _ts_array(xs) -> np.ndarray:
    if not xs:
        return np.empty(0)
    return np.asarray(np.array(xs, dtype="datetime64[ms]").astype("int64"), float) / 1000.0


def _num(v) -> float:
    if isinstance(v, list) or v is None:
        return np.nan
    try:
        return float(v)
    except (TypeError, ValueError):
        return np.nan


def _arr(d: dict, key: str, i: int) -> np.ndarray:
    seq = d.get(key, [])
    return np.asarray(seq[i], float) if i < len(seq) and isinstance(seq[i], list) else np.empty(0)


@dataclass
class CellResult:
    cell_id: str
    table: pd.DataFrame | None
    excluded: str | None
    anchors: list = field(default_factory=list)
    checks: dict = field(default_factory=dict)


def _anchor_knots(raw, ok, cyc_stop, c5, r_start, use_week0: bool):
    anchors = []
    for w, (cap, rs) in enumerate(zip(c5, r_start)):
        if not (np.isfinite(cap) and np.isfinite(rs)):
            continue
        before = np.flatnonzero(ok & np.isfinite(cyc_stop) & (cyc_stop <= rs))
        if len(before) < ANCHOR_CYCLES:
            continue
        last = before[-ANCHOR_CYCLES:]
        med = float(np.median(raw[last]))
        anchors.append({"rpt_index": w, "kind": "pre_rpt", "knot": int(last[-1]), "c5_Ah": cap, "aging_median_Ah": med, "f": cap / med, "g": cap - med})
    if use_week0 and len(c5) and np.isfinite(c5[0]):
        first = np.flatnonzero(ok)[:ANCHOR_CYCLES]
        if len(first) == ANCHOR_CYCLES:
            med = float(np.median(raw[first]))
            anchors.append({"rpt_index": 0, "kind": "week0", "knot": int(first[-1]), "c5_Ah": float(c5[0]), "aging_median_Ah": med,
                            "f": float(c5[0]) / med, "g": float(c5[0]) - med})
    anchors.sort(key=lambda a: a["knot"])
    out, seen = [], set()
    for a in anchors:  # one knot per cycle index (a week-0 knot coinciding with an RPT knot keeps the RPT one)
        if a["knot"] in seen:
            continue
        seen.add(a["knot"])
        out.append(a)
    return out


def _interp(anchors, n, key):
    xa = np.array([a["knot"] for a in anchors], float)
    va = np.array([a[key] for a in anchors], float)
    idx = np.clip(np.arange(n, dtype=float), xa[0], xa[-1])
    return PchipInterpolator(xa, va, extrapolate=False)(idx)


def convert_cell(cell_id: str, cyc: dict, rpt: dict, meta: dict) -> CellResult:
    """meta: {group, mean_dod, c_chg, c_dis, stratum, in_scope}."""
    n = len(cyc["capacity_discharge"])
    c_dis = float(meta["c_dis"])
    rows = []
    for i in range(n):
        Qd = _num(cyc["capacity_discharge"][i])
        Qc = _num(cyc["capacity_charge"][i]) if i < len(cyc.get("capacity_charge", [])) else np.nan
        cs, ce = _ts(cyc["time_series_charge"]["start"][i]), _ts(cyc["time_series_charge"]["stop"][i])
        ds, de = _ts(cyc["time_series_discharge"]["start"][i]), _ts(cyc["time_series_discharge"]["stop"][i])
        Vd, Id = _arr(cyc["QV_discharge"], "V", i), _arr(cyc["QV_discharge"], "I", i)
        Ic = _arr(cyc["QV_charge"], "I", i)
        td = _ts_array(cyc["QV_discharge"]["t"][i]) if i < len(cyc["QV_discharge"]["t"]) else np.empty(0)
        tc = _ts_array(cyc["QV_charge"]["t"][i]) if i < len(cyc["QV_charge"]["t"]) else np.empty(0)
        Qdd = _arr(cyc["QV_discharge"], "Q", i)
        n_samples = int(len(Vd) + len(tc))
        mdv = float(np.trapz(Vd, td) / (td[-1] - td[0])) if len(Vd) >= 2 and len(td) == len(Vd) and td[-1] > td[0] else np.nan
        rows.append({"cell_id": cell_id, "cycle_number": i + 1, "n_samples": n_samples, "capacity_aging_raw_Ah": Qd, "capacity_charge_Ah": Qc,
                     "charge_time_min": (ce - cs) / 60.0 if np.isfinite(cs) and np.isfinite(ce) else np.nan, "mean_discharge_voltage_V": mdv,
                     "discharge_duration_min": (de - ds) / 60.0 if np.isfinite(ds) and np.isfinite(de) else np.nan,
                     "charge_start_unix_s": cs, "charge_stop_unix_s": ce, "discharge_start_unix_s": ds, "discharge_stop_unix_s": de,
                     "last_discharge_V": float(Vd[-1]) if len(Vd) else np.nan, "last_charge_I_A": float(abs(Ic[-1])) if len(Ic) else np.nan,
                     "median_discharge_I_A": float(np.median(np.abs(Id))) if len(Id) else np.nan,
                     "max_Q_minus_capacity_Ah": float(np.nanmax(Qdd) - Qd) if len(Qdd) and np.isfinite(Qd) else np.nan,
                     "samples_charge_duration_min": (tc[-1] - tc[0]) / 60.0 if len(tc) >= 2 else np.nan})
    t = pd.DataFrame(rows)
    # ---- RPT times and C/5
    c5 = [_num(v) for v in rpt["capacity_discharge_C_5"]]
    r_start = [_ts(v) for v in rpt["start_stop_time"]["start"]]
    r_stop = [_ts(v) for v in rpt["start_stop_time"]["stop"]]
    # ---- 1 predicates
    deg = (t["n_samples"] < 10) | ~np.isfinite(t["capacity_aging_raw_Ah"]) | (t["capacity_aging_raw_Ah"] <= 0) | t["charge_start_unix_s"].isna() | t["discharge_start_unix_s"].isna()
    med_last_v = float(np.nanmedian(t.loc[~deg, "last_discharge_V"])) if (~deg).any() else np.nan
    incomplete = ~deg & ((t["last_discharge_V"] > med_last_v + INCOMPLETE_DV) | (t["last_charge_I_A"] > INCOMPLETE_I))
    overlap = np.zeros(n, bool)
    for rs, rp in zip(r_start, r_stop):
        if np.isfinite(rs) and np.isfinite(rp):
            overlap |= (t["charge_start_unix_s"].to_numpy() < rp) & (t["discharge_stop_unix_s"].to_numpy() > rs)
    current_off = (np.abs(t["median_discharge_I_A"] - c_dis * Q_RATED) > NONAGING_REL_I * c_dis * Q_RATED) & ~deg
    non_aging = overlap | current_off.to_numpy()
    t["flag_degenerate"], t["flag_incomplete"], t["flag_non_aging"] = deg.to_numpy(), incomplete.to_numpy(), non_aging
    ok = ~(deg.to_numpy() | incomplete.to_numpy() | non_aging)
    raw = t["capacity_aging_raw_Ah"].to_numpy(float)
    cyc_stop = t["discharge_stop_unix_s"].to_numpy(float)
    # ---- 2-3 anchors and f (multiplicative primary, additive sensitivity), with and without the week-0 anchor
    anchors = _anchor_knots(raw, ok, cyc_stop, c5, r_start, use_week0=True)
    anchors_nw0 = _anchor_knots(raw, ok, cyc_stop, c5, r_start, use_week0=False)
    checks = {"cycles": int(n), "degenerate": int(deg.sum()), "incomplete": int(incomplete.sum()), "non_aging": int(non_aging.sum()),
              "non_aging_overlap_rpt": int(overlap.sum()), "non_aging_current": int(current_off.sum()), "anchors": len(anchors),
              "rpts": len(c5), "rpts_with_c5": int(np.isfinite(c5).sum()), "median_last_discharge_V": med_last_v}
    if len(anchors) < 2:
        return CellResult(cell_id, None, f"fewer than 2 calibration anchors ({len(anchors)})", anchors, checks)
    t["calibration_factor"] = _interp(anchors, n, "f")
    t["calibration_offset_Ah"] = _interp(anchors, n, "g")
    t["capacity_cycler_Ah"] = raw * t["calibration_factor"].to_numpy()
    t["capacity_additive_Ah"] = raw + t["calibration_offset_Ah"].to_numpy()
    t["calibration_factor_no_week0"] = _interp(anchors_nw0, n, "f") if len(anchors_nw0) >= 2 else np.nan
    # ---- rest events (block starts, pauses), RPT cross-check
    blk_start = [_ts(v) for v in cyc["start_stop_time"]["start"]]
    cstart = t["charge_start_unix_s"].to_numpy(float)
    rest_block = np.zeros(n, bool)
    for b, bs in enumerate(blk_start):
        if b == 0 or not np.isfinite(bs):
            continue
        cand = np.flatnonzero(ok & np.isfinite(cstart) & (cstart >= bs))
        if len(cand):
            rest_block[cand[0]] = True
    order = np.flatnonzero(ok)
    gaps = cstart[order[1:]] - cyc_stop[order[:-1]]
    med_gap = float(np.nanmedian(gaps)) if len(gaps) else np.nan
    rest_pause = np.zeros(n, bool)
    for k, gp in enumerate(gaps):
        if np.isfinite(gp) and gp > med_gap + PAUSE_EXTRA_S:
            rest_pause[order[k + 1]] = True
    first_ok = order[0] if len(order) else 0
    rest_block[first_ok] = rest_pause[first_ok] = False  # position 1 is never a rest event
    rest_rpt = np.zeros(n, bool)
    for rp in r_stop:
        if np.isfinite(rp):
            cand = np.flatnonzero(ok & np.isfinite(cstart) & (cstart >= rp))
            if len(cand) and cand[0] != first_ok:
                rest_rpt[cand[0]] = True
    t["rest_event"] = rest_block | rest_pause
    t["rest_event_source"] = np.where(rest_block, "block_start", np.where(rest_pause, "pause", ""))
    t["rest_event_rpt_crosscheck"] = rest_rpt
    # charge time at RPT-following rest events is missing by protocol (starts from the RPT's discharged state)
    ct_protocol = rest_block.copy()
    t["charge_time_protocol_masked"] = ct_protocol
    t.loc[ct_protocol, "charge_time_min"] = np.nan
    # ---- table: D12 drops 'degenerate' rows (degenerate or incomplete); non-aging cycles excluded
    t["degenerate"] = t["flag_degenerate"] | t["flag_incomplete"]
    t = t[~t["flag_non_aging"]].copy()
    t["position"] = np.arange(1, len(t) + 1)
    for k, v in meta.items():
        t[k] = v
    # ---- converter checks against the raw arrays
    a_err = []
    for a in anchors:
        a_err.append(abs(a["aging_median_Ah"] * t.loc[t["cycle_number"] == a["knot"] + 1, "calibration_factor"].iloc[0] - a["c5_Ah"])
                     if (t["cycle_number"] == a["knot"] + 1).any() else 0.0)
    checks.update({"anchor_identity_max_abs_Ah": float(max(a_err)) if a_err else None,
                   "max_abs_capacity_vs_max_Q_Ah": float(np.nanmax(np.abs(t["max_Q_minus_capacity_Ah"]))) if t["max_Q_minus_capacity_Ah"].notna().any() else None,
                   "max_abs_charge_time_vs_samples_min": float(np.nanmax(np.abs(t["charge_time_min"] - t["samples_charge_duration_min"]))) if t["charge_time_min"].notna().any() else None,
                   "rest_events_block": int(rest_block.sum()), "rest_events_pause": int(rest_pause.sum()), "rest_events_rpt_crosscheck": int(rest_rpt.sum()),
                   "rest_block_vs_rpt_mismatch": int((rest_block != rest_rpt).sum()), "charge_time_protocol_masked": int(ct_protocol.sum()),
                   "median_gap_s": med_gap, "f_stats": {q: float(np.nanpercentile(t["calibration_factor"], p)) for q, p in (("min", 0), ("p05", 5), ("median", 50), ("p95", 95), ("max", 100))},
                   "time_monotone": bool(np.all(np.diff(cstart[np.isfinite(cstart)]) > 0))})
    return CellResult(cell_id, t, None, anchors, checks)
