"""MATR ingestion through BatteryML, one batch per process (brief R3; docs/S0_RESEARCH/datasets.md §1.5-1.7).

BatteryML's ``MATRPreprocessor.process`` loads all four batches before writing anything (estimated
~12.5 GB peak against ~9 GB available). This module calls the same BatteryML functions
(``load_batch``, ``clean_batches``, ``organize_cell``) but one batch per child process, in the order
b2 -> b1 -> b3 -> b4, so the batch-1/batch-2 carry-over merge is BatteryML's own code path.

Two additions are made to each ``BatteryData`` before it is dumped, both recorded on the object:

* ``time_in_s`` is multiplied by 60. The MATR ``cycles.t`` arrays are in minutes (a full cycle spans
  ~60 units; the ``summary.chargetime`` field is also in minutes), and BatteryML copies them into
  ``time_in_s`` unconverted. Attribute ``time_unit_converted_from_minutes = True``.
* The per-cycle ``summary`` fields BatteryML drops are attached to ``CycleData.additional_data``
  (``summary_QDischarge_Ah``, ``summary_QCharge_Ah``, ``summary_chargetime_min``, ``summary_Tavg_C``,
  ``summary_Tmin_C``, ``summary_Tmax_C``, ``summary_cycle``), indexed exactly as BatteryML indexes
  ``summary['IR']`` for ``internal_resistance_in_ohm``. Cell-level ``cycle_life``, ``charge_policy``
  and ``batch`` are attached as attributes.

Cycles whose raw arrays are MATLAB empty placeholders (fewer than ``MIN_SAMPLES`` samples) are dropped
and counted in ``dropped_placeholder_cycles`` on the object; BatteryML already skips index 0 of every
cell, which is the placeholder in batch 1 (and a real cycle in batches 2-4; kept as BatteryML does).
"""

from __future__ import annotations

import json
import pickle
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

BATCH_FILES = {
    1: "MATR_batch_20170512.mat",
    2: "MATR_batch_20170630.mat",
    3: "MATR_batch_20180412.mat",
    4: "MATR_batch_20190124.mat",
}
BATCH_DATES = {1: "2017-05-12", 2: "2017-06-30", 3: "2018-04-12", 4: "2019-01-24"}
CARRY_KEYS = ["b2c7", "b2c8", "b2c9", "b2c15", "b2c16"]
MIN_SAMPLES = 10
SUMMARY_FIELDS = {  # BatteryML summary key -> additional_data name
    "QD": "summary_QDischarge_Ah",
    "QC": "summary_QCharge_Ah",
    "chargetime": "summary_chargetime_min",
    "Tavg": "summary_Tavg_C",
    "Tmin": "summary_Tmin_C",
    "Tmax": "summary_Tmax_C",
    "cycle": "summary_cycle",
}


def _augment_and_dump(battery, cell: dict, batch: int, out_dir: Path, log: list) -> None:
    summary = cell["summary"]
    kept, dropped = [], 0
    for cd in battery.cycle_data:
        j = cd.cycle_number  # organize_cell sets cycle_number = raw index, and indexes summary['IR'][j]
        if cd.voltage_in_V is None or len(cd.voltage_in_V) < MIN_SAMPLES:
            dropped += 1
            continue
        cd.time_in_s = (np.asarray(cd.time_in_s, dtype=float) * 60.0).tolist()
        for src, name in SUMMARY_FIELDS.items():
            cd.additional_data[name] = float(summary[src][j]) if j < len(summary[src]) else float("nan")
        kept.append(cd)
    battery.cycle_data = kept
    battery.time_unit_converted_from_minutes = True
    battery.dropped_placeholder_cycles = dropped
    battery.cycle_life = float(np.asarray(cell["cycle_life"]).ravel()[0]) if np.size(cell["cycle_life"]) else float("nan")
    battery.charge_policy = cell["charge_policy"]
    battery.batch = BATCH_DATES[batch]
    battery.dump(out_dir / f"{battery.cell_id}.pkl")
    log.append({"cell_id": battery.cell_id, "n_cycles": len(kept), "dropped_placeholder_cycles": dropped,
                "cycle_life_field": battery.cycle_life, "policy": battery.charge_policy, "batch": battery.batch})


def run_batch(batch: int, raw_dir: Path, out_dir: Path, work_dir: Path) -> None:
    """Process one MATR batch in the current process (called in a child process by ``ingest``)."""
    from batteryml.preprocess.preprocess_MATR import clean_batches, load_batch, organize_cell

    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    data = load_batch(raw_dir / BATCH_FILES[batch], batch)
    t_load = time.perf_counter() - t0
    log: list = []

    if batch == 2:
        carry = {k: data[k] for k in CARRY_KEYS}
        with open(work_dir / "matr_b2_carry.pkl", "wb") as f:
            pickle.dump(carry, f, protocol=pickle.HIGHEST_PROTOCOL)
        del carry
    if batch == 1:
        with open(work_dir / "matr_b2_carry.pkl", "rb") as f:
            carry = pickle.load(f)

        def dump(battery):
            key = battery.cell_id.split("_", 1)[1]
            _augment_and_dump(battery, data[key], 1, out_dir, log)
            data[key]["cycles"] = {}  # release raw arrays of a dumped cell

        clean_batches([data, carry], dump, silent=True)  # BatteryML merge of b2c7..16 into b1c0..4
    else:
        for key in list(data.keys()):
            if batch == 2 and key in CARRY_KEYS:
                continue
            battery = organize_cell(data[key], key)
            _augment_and_dump(battery, data[key], batch, out_dir, log)
            del battery
            data[key]["cycles"] = {}

    with open(work_dir / f"matr_b{batch}_log.json", "w") as f:
        json.dump({"batch": batch, "load_s": t_load, "total_s": time.perf_counter() - t0, "cells": log}, f, indent=1)


def ingest(raw_dir: Path, out_dir: Path, work_dir: Path, force: bool = False) -> list[dict]:
    """Run b2, b1, b3, b4 each in a fresh interpreter; skip batches whose log exists unless ``force``."""
    records = []
    for batch in (2, 1, 3, 4):
        log_path = work_dir / f"matr_b{batch}_log.json"
        if log_path.exists() and not force:
            print(f"[skip] MATR batch {batch}: {log_path} exists")
        else:
            if batch == 1 and not (work_dir / "matr_b2_carry.pkl").exists():
                raise RuntimeError("batch 1 needs the batch-2 carry-over pickle; run batch 2 first")
            cmd = [sys.executable, "-c",
                   "import sys; from pathlib import Path; from degradx.data.matr import run_batch; "
                   f"run_batch({batch}, Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))",
                   str(raw_dir), str(out_dir), str(work_dir)]
            print(f"[run] MATR batch {batch} in a child process")
            subprocess.run(cmd, check=True)
        with open(log_path) as f:
            records.append(json.load(f))
    return records


if __name__ == "__main__":  # python -m degradx.data.matr <raw_dir> <out_dir> <work_dir>
    ingest(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
