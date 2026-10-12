"""TRI/Stanford formation dataset (Cui et al., Joule 8(11):3072-3087, 2024; data.matr.io/8, CC BY-NC 4.0) to DegradX
per-cycle statistics, under the declared extraction of decision D32 (declarations r4 ``declared_by_design.v2_1``).

Each aging file is a BEEP-structured MaccorDatapath JSON (gzip): ``summary`` (one row per regular cycle; diagnostic cycles are
listed in ``diagnostic_summary``), ``cycles_interpolated`` (each step of a regular cycle interpolated to ``resolution`` points
on the axis named in ``structuring_parameters``), ``diagnostic_summary`` / ``diagnostic_interpolated`` and the
``diagnostic`` config (cycle_type_to_ix). This module computes, per file, everything the declared rules need from the file
alone (pass 1); the cross-cell rules (modal protocol, tolerance, non-aging cycles, positions, rest events, masks) are applied
by ``build_cycle_table`` over all files (pass 2).

Declared quantities (v2_1.channels, aging_protocol, cycle_predicates):
  capacity_cycler_Ah        summary.discharge_capacity
  mean_discharge_voltage_V  summary.discharge_energy / summary.discharge_capacity
  charge_time_min           first kept charge sample with current > C/50 to the charge end (kept rows: up to the first row
                            whose interpolated charge_capacity reaches summary.charge_capacity - 1e-6 Ah; on a capacity axis
                            the end is extrapolated over the last grid step)
  per-cycle tuple           I_chg (p90 of positive charge current), V_cv (p99 charge voltage), I_dis (median |current| of the
                            discharge samples), V_end (minimum discharge voltage)
"""

from __future__ import annotations

import gzip
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

Q_NOM = 0.24                 # Ah (Cui et al. 2024 p.3082; configs/profiles/tri_formation.yaml)
C50 = Q_NOM / 50             # 0.0048 A: sample threshold of charge_time (v2_1.channels.charge_time.value)
C20 = Q_NOM / 20             # 0.012 A: the CV cutoff; incomplete (b) at 2 x C/20
MIN_SAMPLES = 10             # v2_1.cycle_predicates.degenerate
PAUSE_IN_CHARGE_S = 600      # v2_1.channels.charge_time.protocol_mask (c)
PAUSE_LOCATED_S = 3600       # v2_1.rest_events.sources.paused
Q_REACH_TOL = 1e-6           # Ah: kept charge rows on a non-capacity axis
FIRST_SAMPLE_Q_MAX = 0.001   # Ah: validation, first kept charge sample at the cycle's start of charge
CC_MARGIN_V = 0.01           # V: D33, constant-current samples lie below the cycle's own V_cv by more than this


def load(path: Path) -> dict:
    with gzip.open(path, "rt") as f:
        d = json.load(f)
    return json.loads(d) if isinstance(d, str) else d


def _iso_to_unix(xs) -> np.ndarray:
    t = pd.to_datetime(pd.Series(xs), utc=True, errors="coerce", format="mixed")
    return (t - pd.Timestamp("1970-01-01", tz="UTC")).dt.total_seconds().to_numpy(float)


def file_record(d: dict) -> dict:
    """archive.beep_markers and the inventory of one file."""
    sp = d.get("structuring_parameters") or {}
    ci = d.get("cycles_interpolated") or {}
    raw = d.get("raw_data")
    return {
        "top_level_keys": sorted(d.keys()),
        "rows": {k: (len(next(iter(d[k].values()))) if isinstance(d.get(k), dict) and d[k] and isinstance(next(iter(d[k].values())), list) else None)
                 for k in ("summary", "cycles_interpolated", "diagnostic_summary", "diagnostic_interpolated", "raw_data")},
        "structuring_parameters": sp,
        "writer": {"diagnostic_available_in_sp": "diagnostic_available" in sp, "top_level_diagnostic": "diagnostic" in d,
                   "step_index_in_cycles_interpolated": "step_index" in ci},
        "raw_data_nonempty": bool(isinstance(raw, dict) and raw and len(next(iter(raw.values()))) > 0),
        "metadata": {k: v for k, v in (d.get("metadata") or {}).items() if k in ("protocol", "channel_id", "start_datetime", "barcode")},
        "protocol": d.get("protocol"),
        "channel_id": d.get("channel_id"),
        "diagnostic_config": {k: sorted(int(i) for i in v) for k, v in ((d.get("diagnostic") or {}).get("cycle_type_to_ix") or {}).items()},
    }


def _charge_stats(g: pd.DataFrame, q_chg: float, axis: str, thr_dur: float) -> dict:
    """Kept charge rows and every charge quantity of one regular cycle (v2_1.channels.charge_time)."""
    out = {"n_charge": 0, "charge_time_min": np.nan, "I_chg": np.nan, "I_chg_p90_r4": np.nan, "n_cc_samples": 0, "V_cv": np.nan, "I_last": np.nan, "Q_first": np.nan,
           "max_dt_charge_s": np.nan, "t_charge_first": np.nan, "t_charge_end": np.nan, "d_thr_min": np.nan, "charge_steps": ""}
    ch = g[g["step_type"] == "charge"].dropna(subset=["test_time", "current", "voltage", "charge_capacity"]).sort_values("test_time", kind="stable")
    out["n_charge"] = int(len(ch))
    out["charge_steps"] = ",".join(str(int(s)) for s in sorted(ch["step_index"].dropna().unique())) if "step_index" in ch else ""
    if len(ch) < 2 or not np.isfinite(q_chg):
        return out
    q = ch["charge_capacity"].to_numpy(float)
    if axis == "charge_capacity":
        kept = ch[q <= q_chg + 1e-12]
    else:
        reach = np.flatnonzero(q >= q_chg - Q_REACH_TOL)
        kept = ch.iloc[: (reach[0] + 1) if len(reach) else len(ch)]
    pos = kept[kept["current"] > C50]
    if len(pos) < 2:
        return out
    t = pos["test_time"].to_numpy(float)
    t_end = t[-1]
    if axis == "charge_capacity":
        last = pos.iloc[-1]
        t_end = t[-1] + 3600.0 * max(q_chg - float(last["charge_capacity"]), 0.0) / float(last["current"])
    v_cv = float(np.percentile(kept["voltage"], 99))
    cc = pos[pos["voltage"] < v_cv - CC_MARGIN_V]
    out.update({
        "charge_time_min": (t_end - t[0]) / 60.0,
        "I_chg_p90_r4": float(np.percentile(kept.loc[kept["current"] > 0, "current"], 90)),
        "I_chg": float(np.median(cc["current"])) if len(cc) >= MIN_SAMPLES else np.nan,   # D33: the CC level, CC samples only
        "n_cc_samples": int(len(cc)),
        "V_cv": v_cv,
        "I_last": float(pos["current"].iloc[-1]),
        "Q_first": float(pos["charge_capacity"].iloc[0]),
        "max_dt_charge_s": float(np.max(np.diff(t))) if len(t) > 1 else np.nan,
        "t_charge_first": float(t[0]),
        "t_charge_end": float(t_end),
    })
    reach_thr = pos[pos["charge_capacity"] >= thr_dur]
    if len(reach_thr):
        out["d_thr_min"] = (float(reach_thr["test_time"].iloc[0]) - t[0]) / 60.0
    return out


def _discharge_stats(g: pd.DataFrame, q_dis: float, t_charge_end: float) -> dict:
    out = {"n_discharge": 0, "I_dis": np.nan, "V_end": np.nan, "V_cw_samples": np.nan, "Q_span_frac": np.nan,
           "overlap_charge_frac": np.nan, "max_dt_discharge_s": np.nan}
    dc = g[g["step_type"] == "discharge"].dropna(subset=["test_time", "current", "voltage", "discharge_capacity"]).sort_values("test_time", kind="stable")
    out["n_discharge"] = int(len(dc))
    if len(dc) < 2:
        return out
    out["I_dis"] = float(np.median(np.abs(dc["current"])))
    out["V_end"] = float(dc["voltage"].min())
    out["max_dt_discharge_s"] = float(np.max(np.diff(dc["test_time"].to_numpy(float))))
    if np.isfinite(t_charge_end):
        out["overlap_charge_frac"] = float((dc["test_time"] < t_charge_end - 1.0).mean())
    qd = dc["discharge_capacity"].to_numpy(float)
    v = dc["voltage"].to_numpy(float)
    span = qd.max() - qd.min()
    if np.isfinite(q_dis) and q_dis > 0:
        out["Q_span_frac"] = float(span / q_dis)
        if span >= 0.95 * q_dis:
            dq = np.diff(qd)
            out["V_cw_samples"] = float(np.sum(0.5 * (v[1:] + v[:-1]) * dq) / np.sum(dq)) if np.sum(dq) > 0 else np.nan
    return out


@dataclass
class FileResult:
    name: str
    seq: int | None
    record: dict
    cycles: pd.DataFrame | None
    diagnostics: pd.DataFrame | None
    validation: dict = field(default_factory=dict)
    error: str | None = None


def per_cycle(d: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Pass 1: one row per regular summary cycle with the summary quantities and the per-cycle sample statistics; one row per
    diagnostic cycle."""
    sp = d.get("structuring_parameters") or {}
    axis = sp.get("charge_axis", "charge_capacity")
    ffc = sp.get("full_fast_charge", 0.8)
    thr = float(sp.get("nominal_capacity", 1.1)) * float(ffc if ffc is not None else 0.8)
    s = pd.DataFrame(d["summary"]).sort_values("cycle_index", kind="stable").reset_index(drop=True)
    ds = pd.DataFrame(d.get("diagnostic_summary") or {"cycle_index": []})
    diag_ix = set(int(c) for c in ds.get("cycle_index", []))
    ci = pd.DataFrame(d["cycles_interpolated"]) if d.get("cycles_interpolated") else pd.DataFrame(columns=["cycle_index", "step_type"])
    groups = {int(k): v for k, v in ci.groupby("cycle_index")} if len(ci) else {}
    rows = []
    t_start = _iso_to_unix(s["date_time_iso"])
    for i, r in s.iterrows():
        c = int(r["cycle_index"])
        q_dis, q_chg = float(r["discharge_capacity"]), float(r["charge_capacity"])
        g = groups.get(c, pd.DataFrame(columns=ci.columns))
        cs = _charge_stats(g, q_chg, axis, thr)
        dstat = _discharge_stats(g, q_dis, cs["t_charge_end"])
        e = float(r["discharge_energy"]) if r.get("discharge_energy") is not None else np.nan
        rows.append({"cycle_index": c, "in_diagnostic_summary": c in diag_ix, "start_unix": t_start[i],
                     "capacity_cycler_Ah": q_dis, "charge_capacity_Ah": q_chg, "discharge_energy_Wh": e,
                     "mean_discharge_voltage_V": e / q_dis if np.isfinite(q_dis) and q_dis > 0 else np.nan,
                     "summary_charge_duration_min": float(r["charge_duration"]) / 60.0 if pd.notna(r.get("charge_duration")) else np.nan,
                     "summary_paused_s": float(r.get("paused") or 0.0), "summary_CV_time_s": float(r["CV_time"]) if pd.notna(r.get("CV_time")) else np.nan,
                     "internal_resistance_ohm": float(r["dc_internal_resistance"]) if pd.notna(r.get("dc_internal_resistance")) else np.nan,
                     "temperature_mean_C": float(r["temperature_average"]) if pd.notna(r.get("temperature_average")) else np.nan,
                     **cs, **dstat})
    cyc = pd.DataFrame(rows)
    # diagnostic cycles: label, start, capacity and the median |discharge current| of their discharge samples
    di = pd.DataFrame(d.get("diagnostic_interpolated") or {"cycle_index": []})
    dg = {int(k): v for k, v in di.groupby("cycle_index")} if len(di) else {}
    drows = []
    t_d = _iso_to_unix(ds["date_time_iso"]) if len(ds) else []
    for j, r in ds.reset_index(drop=True).iterrows():
        c = int(r["cycle_index"])
        g = dg.get(c)
        neg = g.loc[g["current"] < -C50, "current"] if g is not None else pd.Series(dtype=float)
        drows.append({"cycle_index": c, "cycle_type": r.get("cycle_type"), "start_unix": t_d[j], "discharge_capacity_Ah": float(r["discharge_capacity"]),
                      "paused_s": float(r.get("paused") or 0.0), "median_abs_discharge_current_A": float(np.median(np.abs(neg))) if len(neg) else np.nan})
    return cyc, pd.DataFrame(drows)


def charge_duration_validation(cyc: pd.DataFrame, diag: pd.DataFrame, raw_source: bool = False) -> dict:
    """v2_1.channels.charge_time.validation: BEEP assigns summary.charge_duration positionally over all raw cycles, so the
    value stored at label l belongs to raw cycle S[l], S = sorted(summary ∪ diagnostic_summary cycle_index)."""
    S = sorted(set(cyc["cycle_index"].astype(int)) | set(diag["cycle_index"].astype(int) if len(diag) else []))
    by_c = cyc.set_index("cycle_index")
    o, finite_agree, comparable, first_ok = [], [], 0, []
    for l, cd in zip(cyc["cycle_index"].astype(int), cyc["summary_charge_duration_min"]):
        if l >= len(S):
            continue
        src = S[l]
        if src not in by_c.index:
            continue                              # S[l] is a diagnostic cycle
        row = by_c.loc[src]
        if row["n_charge"] < MIN_SAMPLES:
            continue
        reached = np.isfinite(row["d_thr_min"])
        if np.isfinite(cd):
            finite_agree.append(reached)
            if reached:
                comparable += 1
                o.append(cd - row["d_thr_min"])
                first_ok.append(np.isfinite(row["Q_first"]) and row["Q_first"] <= FIRST_SAMPLE_Q_MAX)
        else:
            finite_agree.append(not reached)
    o = np.asarray(o, float)
    res = {"comparable_labels": int(comparable), "contiguous_from_0": S == list(range(len(S))),
           "finiteness_agreement_share": float(np.mean(finite_agree)) if finite_agree else None}
    if comparable < 20:
        res.update({"evaluable": False, "passes": None})
        return res
    q25, q75 = np.percentile(o, [25, 75])
    med = float(np.median(o))
    res.update({"evaluable": True, "o_median_min": med, "o_iqr_min": float(q75 - q25),
                "o_dev_p95_min": float(np.percentile(np.abs(o - med), 95)), "o_dev_max_min": float(np.max(np.abs(o - med))),
                "first_sample_at_start_share": float(np.mean(first_ok)) if first_ok else None})
    if raw_source:
        res["passes"] = bool(np.median(np.abs(o)) <= 1.0)
    else:
        res["passes"] = bool(med >= -1.0 and (q75 - q25) <= 1.0 and (res["first_sample_at_start_share"] or 0) >= 0.95)
    return res


def convert_file(path: Path, seq: int | None) -> FileResult:
    """Pass 1 for one file (run in its own process)."""
    try:
        d = load(path)
    except Exception as e:  # noqa: BLE001 - a file that fails to decompress or parse is reported, never silently skipped
        return FileResult(path.name, seq, {}, None, None, error=f"parse: {e!r}")
    rec = file_record(d)
    cyc, diag = per_cycle(d)
    val = charge_duration_validation(cyc, diag, raw_source=False)
    return FileResult(path.name, seq, rec, cyc, diag, validation=val)


# ---------------------------------------------------------------------------------------------------------------------------
# Pass 2: cross-cell rules (declarations r4 v2_1.cell_scope, aging_protocol, cycle_predicates, positions, channels, rest_events)

TOL_I, TOL_V, DEPART_I, RUN_W = 0.05, 0.03, 0.10, 11
INCOMPLETE_DV = 0.05
GAP_MARGIN_MIN, GAP_NEAREST = 30.0, 21
DST_WINDOW_S, DST_PAUSE_MAX_S, DST_GAP_MIN, DST_GAP_TOL = 6 * 3600, 4500, 60.0, 10.0
FORMATION_KEYS = ["formation_temperature", "formation_charge_current_1", "formation_cutoff_voltage_1", "formation_charge_current_2",
                  "formation_verification_repeat", "ocv_time"]
NOT_RIGHT = [111, 132, 133, 153, 218, 239, 164]          # cx26 load_data.py, used only for the triplet cross-check


def us_dst_instants(years) -> dict:
    """US rules (Energy Policy Act 2005): spring-forward second Sunday of March 10:00 UTC (02:00 PST), fall-back first Sunday of
    November 09:00 UTC (02:00 PDT), for US/Pacific."""
    out = {"fall_back": [], "spring_forward": []}
    for y in years:
        mar = pd.Timestamp(year=y, month=3, day=1, tz="UTC")
        sun2 = mar + pd.Timedelta(days=(6 - mar.weekday()) % 7 + 7)
        nov = pd.Timestamp(year=y, month=11, day=1, tz="UTC")
        sun1 = nov + pd.Timedelta(days=(6 - nov.weekday()) % 7)
        out["spring_forward"].append((sun2 + pd.Timedelta(hours=10)).timestamp())
        out["fall_back"].append((sun1 + pd.Timedelta(hours=9)).timestamp())
    return out


def formation_mapping(sheet: pd.DataFrame, notes_sheet: pd.DataFrame | None) -> pd.DataFrame:
    """v2_1.formation_mapping: protocol_id = group of identical six-parameter tuples among seq 100-323; 324-326 'baseline'."""
    s = sheet.copy()
    s["seq"] = s["seq_num"].astype(int)
    design = s[s["seq"] <= 323]
    key = design[FORMATION_KEYS].round(6).astype(str).agg("|".join, axis=1)
    codes = {k: f"P{i + 1:02d}" for i, k in enumerate(sorted(key.unique(), key=lambda k: design.loc[key == k, "seq"].min()))}
    s["protocol_id"] = "baseline"
    s.loc[design.index, "protocol_id"] = key.map(codes)
    s["batch"] = np.where(s["seq"] >= 324, "baseline", np.where(s["seq"] >= 288, "batch_2", "batch_1"))
    # the authors' consecutive-triplet grouping (cx26 load_data.py)
    seqs = list(range(100, 231)) + list(range(269, 327))
    trip = {}
    for i in range(0, len(seqs), 3):
        for q in seqs[i:i + 3]:
            trip[q] = i // 3
    s["triplet"] = s["seq"].map(trip)
    s["tags"] = ""
    if notes_sheet is not None:
        n = notes_sheet.astype(str)
        for col in [c for c in notes_sheet.columns if c.startswith("Unnamed")]:
            for q, txt in zip(notes_sheet["seq_num"], notes_sheet[col]):
                if isinstance(txt, str) and txt.strip() and "start regular cycling" not in txt:
                    s.loc[s["seq"] == int(q), "tags"] += txt.strip().replace("\n", " ") + "; "
        del n
    s["tag_shorted_bulged_stopped"] = s["seq"].isin([274, 276, 278, 140, 155])
    return s[["seq", "protocol_id", "batch", "triplet", "tags", "tag_shorted_bulged_stopped"] + FORMATION_KEYS]


def _mode(vals, step):
    v = np.round(np.asarray([x for x in vals if np.isfinite(x)], float) / step) * step
    if not len(v):
        return np.nan
    u, c = np.unique(np.round(v, 6), return_counts=True)
    return float(u[np.argmax(c)])


def _agree(a: dict, b: dict, modal: dict) -> bool:
    ok = (abs(a["I_chg"] - b["I_chg"]) <= TOL_I * modal["I_chg"] and abs(a["I_dis"] - b["I_dis"]) <= TOL_I * modal["I_dis"]
          and abs(a["V_cv"] - b["V_cv"]) <= TOL_V)
    if np.isfinite(a.get("V_end", np.nan)) and np.isfinite(b.get("V_end", np.nan)):
        ok = ok and abs(a["V_end"] - b["V_end"]) <= TOL_V
    return bool(ok)


def build_cycle_table(cells: dict, mapping: pd.DataFrame, documented: dict) -> dict:
    """cells: seq -> {'cycles': DataFrame (pass 1), 'diagnostics': DataFrame, 'validation': dict, 'file': name}.
    Returns the cycle table, per-cell records, the modal tuple, the stop-rule readings and the counts."""
    tup_cols = ["I_chg", "I_dis", "V_cv", "V_end"]
    recs = {}
    for seq, c in cells.items():
        cyc = c["cycles"]
        samples_ok = (cyc["n_charge"] >= MIN_SAMPLES) & (cyc["n_discharge"] >= MIN_SAMPLES)
        recs[seq] = {"seq": seq, "file": c["file"], "regular_rows": int(len(cyc)), "samples_share": float(samples_ok.mean()) if len(cyc) else 0.0,
                     "in_sheet": seq in set(mapping["seq"]), **{k: float(np.nanmedian(cyc.loc[samples_ok, k])) if samples_ok.any() else np.nan for k in tup_cols}}
    # (i) name pattern (pass 1 only receives matching files), (ii) sheet row, (iii) samples on >= 50 % of regular rows
    base = [s for s, r in recs.items() if r["in_sheet"] and r["samples_share"] >= 0.5]
    for s, r in recs.items():
        r["scope_i_ii"] = bool(r["in_sheet"])
        r["scope_iii"] = bool(r["samples_share"] >= 0.5)
    modal = {"I_chg": _mode([recs[s]["I_chg"] for s in base], 0.01), "I_dis": _mode([recs[s]["I_dis"] for s in base], 0.01),
             "V_cv": _mode([recs[s]["V_cv"] for s in base], 0.05), "V_end": _mode([recs[s]["V_end"] for s in base], 0.05)}
    v_end_ref = modal["V_end"] if np.isfinite(modal["V_end"]) else documented["V_end"]
    # E2 on the files: modal elements against the documented values
    e2_modal = {k: (abs(modal[k] / documented[k] - 1) <= TOL_I if k.startswith("I") else abs(modal[k] - documented[k]) <= TOL_V) for k in tup_cols}

    def within(t):
        return (abs(t["I_chg"] / modal["I_chg"] - 1) <= TOL_I and abs(t["I_dis"] / modal["I_dis"] - 1) <= TOL_I and abs(t["V_cv"] - modal["V_cv"]) <= TOL_V
                and t["V_end"] <= v_end_ref + TOL_V and t["V_end"] >= v_end_ref - TOL_V)

    sources = []
    tables, n_incomplete, n_regular = [], 0, 0
    for seq in sorted(recs):
        r = recs[seq]
        if not r["scope_i_ii"]:
            r["excluded"] = "no sheet row (undocumented)"
            continue
        if not r["scope_iii"]:
            r["excluded"] = "no per-cycle samples"
            continue
        if not within(r):
            r["excluded"] = "out of tolerance (aging protocol)"
            sources.append({"seq": seq, "kind": "cell", **{k: r[k] for k in tup_cols}})
            continue
        cyc = cells[seq]["cycles"].sort_values("cycle_index").reset_index(drop=True)
        diag = cells[seq]["diagnostics"]
        dep = (np.abs(cyc["I_chg"] / modal["I_chg"] - 1) > DEPART_I) | (np.abs(cyc["I_dis"] / modal["I_dis"] - 1) > DEPART_I)
        cyc["non_aging"] = dep.fillna(False).astype(bool)
        # runs of more than W non-aging regular cycles: a within-cell change of protocol
        run_id = (cyc["non_aging"] != cyc["non_aging"].shift()).cumsum()
        runs = cyc[cyc["non_aging"]].groupby(run_id[cyc["non_aging"]])
        long_runs = [g for _, g in runs if len(g) > RUN_W]
        if long_runs:
            pool = pd.concat(long_runs)
            r["excluded"] = "out of tolerance (within-cell protocol change: run of > 11 non-aging cycles)"
            sources.append({"seq": seq, "kind": "runs", "cycles": int(len(pool)), **{k: float(np.nanmedian(pool[k])) for k in tup_cols}})
            continue
        if not cells[seq]["validation"].get("passes", True) and cells[seq]["validation"].get("evaluable"):
            r["excluded"] = "charge-time validation failed"
            continue
        r["excluded"] = None
        r["non_aging_cycles"] = int(cyc["non_aging"].sum())
        # predicates on the remaining (aging) regular cycles
        no_samples = (cyc["n_charge"] < MIN_SAMPLES) | (cyc["n_discharge"] < MIN_SAMPLES)
        degenerate = ~np.isfinite(cyc["capacity_cycler_Ah"]) | (cyc["capacity_cycler_Ah"] <= 0) | no_samples
        inc_a = cyc["V_cv"] < modal["V_cv"] - INCOMPLETE_DV
        inc_b = cyc["I_last"] > 2 * C20
        inc_c = cyc["V_end"] > v_end_ref + INCOMPLETE_DV
        incomplete = (inc_a | inc_b | inc_c) & ~degenerate
        aging = ~cyc["non_aging"]
        n_incomplete += int((incomplete & aging).sum())
        n_regular += int(aging.sum())
        # interruptions in cycle_index order (diagnostic and non_aging cycles) -> mask (a) and diagnostic rest events
        diag_ix = set(diag["cycle_index"].astype(int)) if len(diag) else set()
        na_ix = set(cyc.loc[cyc["non_aging"], "cycle_index"].astype(int))
        all_ix = sorted(set(cyc["cycle_index"].astype(int)) | diag_ix)
        first_after = set()
        interrupted = False
        for ci_ in all_ix:
            if ci_ in diag_ix or ci_ in na_ix:
                interrupted = True
                continue
            if interrupted:
                first_after.add(ci_)
                interrupted = False
        # the first aging cycle overall: preceded by the initial diagnostics (position 1 masked, not a rest event)
        mask_a = cyc["cycle_index"].isin(first_after)
        mask_c = cyc["max_dt_charge_s"] > PAUSE_IN_CHARGE_S
        # rest events
        years = range(int(pd.Timestamp(np.nanmin(cyc["start_unix"]), unit="s").year), int(pd.Timestamp(np.nanmax(cyc["start_unix"]), unit="s").year) + 1)
        dst = us_dst_instants(years)
        near = lambda t, inst: any(abs(t - x) <= DST_WINDOW_S for x in inst)  # noqa: E731
        start = cyc["start_unix"].to_numpy(float)
        ix = cyc["cycle_index"].to_numpy(int)
        # start-to-start intervals between consecutive summary rows with no diagnostic cycle between them
        intervals = {}
        for k in range(1, len(cyc)):
            if ix[k] - ix[k - 1] == 1:
                intervals[int(ix[k])] = (start[k] - start[k - 1]) / 60.0
        clean = {c_: v for c_, v in intervals.items() if c_ not in na_ix and (c_ - 1) not in na_ix}
        clean_ix = np.array(sorted(clean), int)
        clean_v = np.array([clean[c_] for c_ in clean_ix], float)
        src, dst_art, spring, e_gap = [], [], [], []
        pos1 = int(np.flatnonzero(aging.to_numpy())[0]) if aging.any() else -1
        for k in range(len(cyc)):
            if not aging.iloc[k]:
                src.append(""), dst_art.append(False), spring.append(False), e_gap.append(np.nan)
                continue
            s_ = ""
            art = False
            if ix[k] in first_after and k != pos1:
                s_ = "diagnostic"
            p = cyc["summary_paused_s"].iloc[k]
            if not s_ and p > 0:
                if near(start[k], dst["fall_back"]) and PAUSE_LOCATED_S < p <= DST_PAUSE_MAX_S:
                    art = True
                else:
                    s_ = "paused"
            e = np.nan
            if ix[k] in intervals and len(clean_ix):
                others = clean_ix != ix[k]
                if others.any():
                    d_ = np.abs(clean_ix[others] - ix[k])
                    nearest = np.argsort(d_, kind="stable")[:GAP_NEAREST]
                    m_c = float(np.median(clean_v[others][nearest]))
                    prev_paused = float(cyc["summary_paused_s"].iloc[k - 1]) / 60.0
                    e = intervals[ix[k]] - prev_paused - m_c
                    if not s_ and e > GAP_MARGIN_MIN:
                        if near(start[k], dst["fall_back"]) and abs(e - DST_GAP_MIN) <= DST_GAP_TOL:
                            art = True
                        else:
                            s_ = "gap"
            if k == pos1:
                s_ = ""
            src.append(s_), dst_art.append(art), spring.append(bool(s_) and near(start[k], dst["spring_forward"])), e_gap.append(e)
        cyc["rest_event_source"] = src
        cyc["rest_event"] = cyc["rest_event_source"] != ""
        cyc["dst_artefact"] = dst_art
        cyc["spring_forward_flag"] = spring
        cyc["gap_excess_min"] = e_gap
        cyc["paused_located"] = (cyc["summary_paused_s"] > 0) & ((cyc["max_dt_charge_s"] > PAUSE_LOCATED_S) | (cyc["max_dt_discharge_s"] > PAUSE_LOCATED_S))
        cyc["flag_no_samples"] = no_samples
        cyc["flag_incomplete_a"], cyc["flag_incomplete_b"], cyc["flag_incomplete_c"] = inc_a, inc_b, inc_c
        cyc["degenerate"] = (degenerate | incomplete).astype(bool)
        cyc["charge_time_raw_min"] = cyc["charge_time_min"]
        cyc["mask_a_after_interruption"], cyc["mask_c_pause_in_charge"] = mask_a, mask_c
        cyc["charge_time_protocol_masked"] = (mask_a | mask_c).astype(bool)
        cyc.loc[cyc["charge_time_protocol_masked"], "charge_time_min"] = np.nan
        cyc["internal_resistance_ohm"] = cyc["internal_resistance_ohm"].where(cyc["internal_resistance_ohm"] != 0)
        t = cyc[aging].copy()
        t.insert(0, "cell_id", f"TRI_{seq}")
        t.insert(1, "seq", seq)
        t["position"] = np.arange(1, len(t) + 1)
        t["cycle_number"] = t["cycle_index"].astype(int)
        r["positions"] = int(len(t))
        r["counts"] = {"degenerate_no_samples": int((no_samples & aging).sum()), "degenerate_capacity": int((~np.isfinite(cyc["capacity_cycler_Ah"]) | (cyc["capacity_cycler_Ah"] <= 0))[aging].sum()),
                       "incomplete_a": int((inc_a & aging).sum()), "incomplete_b": int((inc_b & aging).sum()), "incomplete_c": int((inc_c & aging).sum()),
                       "non_aging": int(cyc["non_aging"].sum()), "mask_a": int(mask_a[aging].sum()), "mask_c_pause_in_charge": int(mask_c[aging].sum()),
                       "rest_events": t["rest_event_source"].value_counts().to_dict(), "dst_artefacts": int(t["dst_artefact"].sum()),
                       "spring_forward_flagged": int(t["spring_forward_flag"].sum()), "paused_cycles": int((t["summary_paused_s"] > 0).sum()),
                       "paused_located": int(t["paused_located"].sum()),
                       "overlap_ramp_cycles": int((t["overlap_charge_frac"] > 0).sum()),
                       "non_aging_only_with_ramp": int((cyc["non_aging"] & (cyc["overlap_charge_frac"] > 0)).sum())}
        tables.append(t)
    # second aging protocol (v2_1.aging_protocol.second_protocol): two or more agreeing sources -> stop
    agree_pairs = [(a["seq"], b["seq"]) for i, a in enumerate(sources) for b in sources[i + 1:] if _agree(a, b, modal)]
    table = pd.concat(tables, ignore_index=True) if tables else pd.DataFrame()
    if len(table):
        table = table.merge(mapping[["seq", "protocol_id", "batch", "tags"]], on="seq", how="left")
    e2_incomplete_share = n_incomplete / n_regular if n_regular else np.nan
    return {"table": table, "cells": recs, "modal": modal, "v_end_ref": v_end_ref, "documented": documented,
            "e2_files": {"modal_within_documented": e2_modal, "incomplete_share_pooled": e2_incomplete_share,
                         "fails": bool((not all(e2_modal.values())) or (e2_incomplete_share > 0.05))},
            "second_protocol": {"sources": sources, "agreeing_pairs": agree_pairs, "present": bool(agree_pairs)}}
