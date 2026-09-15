"""Per-cycle channel derivation from BatteryML ``BatteryData`` (declarations ``channels.candidates``).

One row per ``CycleData``. Integration uses the right-rectangle rule of BatteryML's ``calc_Q`` (sample i
carries dt_i = t_i - t_{i-1}). A sample counts as charging when I > thr and discharging when I < -thr,
with thr = ``CURRENT_THRESHOLD_C`` x nominal capacity (A), so rests and CV tails below C/100 are ignored.

Columns:
  position                1..N in stored order (the index S2+ use)
  cycle_number            BatteryML cycle_number
  capacity_integrated_Ah  max of BatteryML discharge_capacity_in_Ah
  capacity_cycler_Ah      the cycler's own per-cycle capacity (MATR summary QDischarge, HUST dq, NASA Capacity)
  charge_time_min         total duration of charging samples
  mean_discharge_voltage_V  time-weighted mean voltage over discharging samples
  temperature_mean_C      time-weighted mean temperature over the cycle (NaN if not recorded)
  internal_resistance_ohm per-cycle IR as recorded (MATR only; NaN otherwise)
  duration_s, n_samples, frac_negative_dt, v_min, v_max, i_min, i_max, t_min_C, t_max_C  (unit checks)
  start_unix_s            NASA discharge start (rest-time analysis); NaN elsewhere
  degenerate              fewer than 10 samples, or NASA flags it
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

CURRENT_THRESHOLD_C = 0.01
CYCLER_CAPACITY_KEYS = ("summary_QDischarge_Ah", "capacity_cycler_Ah")


def _cycle_row(cd, thr: float) -> dict:
    ad = cd.additional_data or {}
    t = np.asarray(cd.time_in_s if cd.time_in_s is not None else [], dtype=float)
    I = np.asarray(cd.current_in_A if cd.current_in_A is not None else [], dtype=float)  # noqa: E741
    V = np.asarray(cd.voltage_in_V if cd.voltage_in_V is not None else [], dtype=float)
    T = np.asarray(cd.temperature_in_C, dtype=float) if cd.temperature_in_C is not None and len(cd.temperature_in_C) else None
    Qd = np.asarray(cd.discharge_capacity_in_Ah if cd.discharge_capacity_in_Ah is not None else [], dtype=float)
    n = len(t)
    row = {"cycle_number": cd.cycle_number, "n_samples": n}
    cyc_cap = next((ad[k] for k in CYCLER_CAPACITY_KEYS if k in ad), np.nan)
    row["capacity_cycler_Ah"] = float(cyc_cap) if cyc_cap is not None else np.nan
    row["capacity_integrated_Ah"] = float(np.nanmax(Qd)) if Qd.size else np.nan
    row["internal_resistance_ohm"] = float(cd.internal_resistance_in_ohm) if cd.internal_resistance_in_ohm is not None else np.nan
    row["start_unix_s"] = float(ad["discharge_start_unix_s"]) if ad.get("discharge_start_unix_s") is not None else np.nan
    row["degenerate"] = bool(n < 10 or ad.get("degenerate", False))
    for k in ("summary_chargetime_min", "summary_Tavg_C", "summary_cycle", "ambient_temperature_C"):
        if k in ad:
            row[k] = float(ad[k]) if ad[k] is not None else np.nan
    if n < 2:
        row.update(charge_time_min=np.nan, mean_discharge_voltage_V=np.nan, temperature_mean_C=np.nan, duration_s=np.nan,
                   frac_negative_dt=np.nan, v_min=np.nan, v_max=np.nan, i_min=np.nan, i_max=np.nan, t_min_C=np.nan, t_max_C=np.nan)
        return row
    dt = np.diff(t, prepend=t[0])
    row["frac_negative_dt"] = float(np.mean(dt < 0))
    dt = np.clip(dt, 0.0, None)
    chg, dis = I > thr, I < -thr
    row["charge_time_min"] = float(dt[chg].sum() / 60.0) if chg.any() else np.nan
    row["mean_discharge_voltage_V"] = float((V[dis] * dt[dis]).sum() / dt[dis].sum()) if dis.any() and dt[dis].sum() > 0 else np.nan
    if T is not None and T.size == n and dt.sum() > 0:
        row["temperature_mean_C"] = float((T * dt).sum() / dt.sum())
        row["t_min_C"], row["t_max_C"] = float(T.min()), float(T.max())
    else:
        row["temperature_mean_C"] = row["t_min_C"] = row["t_max_C"] = np.nan
    row["duration_s"] = float(t.max() - t.min())
    row["v_min"], row["v_max"], row["i_min"], row["i_max"] = float(V.min()), float(V.max()), float(I.min()), float(I.max())
    return row


def cell_table(pkl_path: str | Path) -> pd.DataFrame:
    from batteryml import BatteryData

    b = BatteryData.load(pkl_path)
    thr = CURRENT_THRESHOLD_C * float(b.nominal_capacity_in_Ah)
    rows = [_cycle_row(cd, thr) for cd in b.cycle_data]
    df = pd.DataFrame(rows)
    df.insert(0, "position", np.arange(1, len(df) + 1))
    df.insert(0, "cell_id", b.cell_id)
    df["nominal_capacity_Ah"] = float(b.nominal_capacity_in_Ah)
    for attr in ("batch", "charge_policy", "cycle_life"):
        if hasattr(b, attr):
            df[attr] = getattr(b, attr)
    return df


def dataset_table(processed_dir: str | Path, pattern: str, workers: int = 4) -> pd.DataFrame:
    import multiprocessing as mp

    paths = sorted(Path(processed_dir).glob(pattern))
    # fork context with worker recycling; ProcessPoolExecutor(max_tasks_per_child=...) switches to spawn and
    # deadlocked here (regression noted in artifacts/s1_fetch_data/REVIEW.md)
    with mp.get_context("fork").Pool(processes=workers, maxtasksperchild=4) as pool:
        frames = pool.map(cell_table, paths, chunksize=1)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
