"""NASA PCoE Battery Data Set -> BatteryML ``BatteryData`` (brief §2.2; permitted own code under R2).

BatteryML has no NASA preprocessor. This thin converter maps the repository's ``.mat`` files onto the
same objects BatteryML produces for MATR and HUST, so every later stage reads one interface.

Mapping (docs/S0_RESEARCH/datasets.md §3.3, §4):

* one ``CycleData`` per ``discharge`` operation, ``cycle_number`` 1-based in discharge order;
* the most recent ``charge`` operation that started after the previous discharge is prepended, so a
  cycle holds charge followed by discharge as in MATR and HUST (``None`` if there is no such charge);
* ``voltage_in_V <- Voltage_measured``, ``current_in_A <- Current_measured`` (discharge negative),
  ``temperature_in_C <- Temperature_measured``, ``time_in_s <- Time`` offset by the charge start so the
  cycle has one clock starting at 0 s;
* ``charge_capacity_in_Ah`` / ``discharge_capacity_in_Ah``: cumulative rectangle integration of I dt over
  positive / negative current, the rule BatteryML's HUST preprocessor uses (``calc_Q``);
* ``internal_resistance_in_ohm = None`` (the dataset records EIS, not pulse DC resistance);
* ``additional_data``: ``capacity_cycler_Ah`` (the file's ``Capacity``), ``ambient_temperature_C``,
  ``discharge_start_unix_s``, ``charge_start_unix_s``, ``Re_ohm`` / ``Rct_ohm`` of the latest preceding
  impedance operation, ``n_discharge_samples``, ``degenerate`` (fewer than 10 discharge samples or an
  empty ``Capacity``).

Nothing is filtered here: degenerate operations are kept and flagged, so the S2 audit decides.
"""

from __future__ import annotations

import datetime as dt
import zipfile
from pathlib import Path

import numpy as np
import scipy.io

OUTER_ZIP = "5.Battery_Data_Set.zip"
NOMINAL_CAPACITY_AH = 2.0  # rated capacity, 1_README.txt (configs/profiles/nasa_pcoe.yaml)
MIN_SAMPLES = 10

# README facts per cell: discharge cut-off voltage (V) and the README group (docs/S0_RESEARCH/datasets.md §3.2)
CUTOFF_V = {
    "B0005": 2.7, "B0006": 2.5, "B0007": 2.2, "B0018": 2.5,
    "B0025": 2.0, "B0026": 2.2, "B0027": 2.5, "B0028": 2.7,
    "B0029": 2.0, "B0030": 2.2, "B0031": 2.5, "B0032": 2.7,
    "B0033": 2.0, "B0034": 2.2, "B0036": 2.7,
    "B0038": 2.2, "B0039": 2.5, "B0040": 2.7,
    "B0041": 2.0, "B0042": 2.2, "B0043": 2.5, "B0044": 2.7,
    "B0045": 2.0, "B0046": 2.2, "B0047": 2.5, "B0048": 2.7,
    "B0049": 2.0, "B0050": 2.2, "B0051": 2.5, "B0052": 2.7,
    "B0053": 2.0, "B0054": 2.2, "B0055": 2.5, "B0056": 2.7,
}


def extract(raw_dir: Path, work_dir: Path) -> list[Path]:
    """Extract the 34 unique cell ``.mat`` files from the nested zips (idempotent)."""
    out = work_dir / "nasa_mat"
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(raw_dir / OUTER_ZIP) as outer:
        for inner_name in sorted(n for n in outer.namelist() if n.lower().endswith(".zip")):
            with outer.open(inner_name) as fh, zipfile.ZipFile(fh) as inner:
                for member in inner.namelist():
                    name = Path(member).name
                    if name.upper().startswith("B00") and name.lower().endswith(".mat") and not (out / name).exists():
                        (out / name).write_bytes(inner.read(member))  # duplicates (B0025-28) are byte-identical
    return sorted(out.glob("B00*.mat"))


def _unix(datevec) -> float:
    y, mo, d, h, mi, s = (float(v) for v in np.ravel(datevec))
    whole = int(s)
    return dt.datetime(int(y), int(mo), int(d), int(h), int(mi), whole, int(round((s - whole) * 1e6)) % 1000000,
                       tzinfo=dt.timezone.utc).timestamp()


def _calc_q(current: np.ndarray, t: np.ndarray, charge: bool) -> np.ndarray:
    q = np.zeros_like(current, dtype=float)
    if len(current) < 2:
        return q
    dq = current[1:] * np.diff(t) / 3600.0
    mask = current[1:] > 0 if charge else current[1:] < 0
    q[1:] = np.cumsum(np.where(mask, np.abs(dq), 0.0))
    return q


def _arr(data: dict, key: str) -> np.ndarray:
    v = data.get(key)
    return np.atleast_1d(np.asarray(v, dtype=float)) if v is not None and np.size(v) else np.array([], dtype=float)


def convert_cell(mat_path: Path):
    from batteryml import BatteryData, CycleData, CyclingProtocol

    cell = mat_path.stem
    ops = scipy.io.loadmat(mat_path, simplify_cells=True)[cell]["cycle"]
    cycles, last_charge, last_imp = [], None, (None, None)
    for op in ops:
        kind, data = op["type"], op["data"]
        if kind == "charge":
            last_charge = op
        elif kind == "impedance":
            last_imp = (float(np.real(np.ravel(data.get("Re", np.nan))[0])) if np.size(data.get("Re", [])) else None,
                        float(np.real(np.ravel(data.get("Rct", np.nan))[0])) if np.size(data.get("Rct", [])) else None)
        elif kind == "discharge":
            d_start = _unix(op["time"])
            V_d, I_d, T_d, t_d = (_arr(data, k) for k in ("Voltage_measured", "Current_measured", "Temperature_measured", "Time"))
            cap = _arr(data, "Capacity")
            if last_charge is not None:
                c = last_charge["data"]
                c_start = _unix(last_charge["time"])
                V_c, I_c, T_c, t_c = (_arr(c, k) for k in ("Voltage_measured", "Current_measured", "Temperature_measured", "Time"))
                offset = d_start - c_start
            else:
                c_start, V_c, I_c, T_c, t_c, offset = None, *(np.array([], dtype=float),) * 4, 0.0
            V = np.concatenate([V_c, V_d]); I = np.concatenate([I_c, I_d])  # noqa: E702
            T = np.concatenate([T_c, T_d]); t = np.concatenate([t_c, t_d + offset])  # noqa: E702
            q_d = _calc_q(I, t, charge=False)
            q_c = _calc_q(I, t, charge=True)
            cycles.append(CycleData(
                cycle_number=len(cycles) + 1,
                voltage_in_V=V.tolist(), current_in_A=I.tolist(), temperature_in_C=T.tolist(), time_in_s=t.tolist(),
                discharge_capacity_in_Ah=q_d.tolist(), charge_capacity_in_Ah=q_c.tolist(),
                internal_resistance_in_ohm=None,
                capacity_cycler_Ah=float(cap[0]) if cap.size else float("nan"),
                ambient_temperature_C=float(op["ambient_temperature"]),
                discharge_start_unix_s=d_start, charge_start_unix_s=c_start,
                n_charge_samples=int(len(t_c)), n_discharge_samples=int(len(t_d)),
                Re_ohm=last_imp[0], Rct_ohm=last_imp[1],
                degenerate=bool(len(t_d) < MIN_SAMPLES or cap.size == 0),
            ))
            last_charge = None  # a charge is used by at most one discharge
    cutoff = CUTOFF_V.get(cell)
    return BatteryData(
        cell_id=f"NASA_{cell}",
        cycle_data=cycles,
        form_factor="cylindrical_18650",
        anode_material=None,
        cathode_material=None,  # chemistry not stated in any README (UNVERIFIED)
        nominal_capacity_in_Ah=NOMINAL_CAPACITY_AH,
        charge_protocol=[CyclingProtocol(current_in_A=1.5, end_voltage_in_V=4.2), CyclingProtocol(voltage_in_V=4.2)],
        discharge_protocol=[CyclingProtocol(end_voltage_in_V=cutoff)],
        max_voltage_limit_in_V=4.2,
        min_voltage_limit_in_V=cutoff,
        reference="B. Saha and K. Goebel (2007). Battery Data Set, NASA Prognostics Data Repository, NASA Ames Research Center",
        description="converted by degradx.data.nasa (BatteryML has no NASA preprocessor)",
    )


def ingest(raw_dir: Path, out_dir: Path, work_dir: Path, force: bool = False) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for mat in extract(raw_dir, work_dir):
        target = out_dir / f"NASA_{mat.stem}.pkl"
        if target.exists() and not force:
            print(f"[skip] {target.name} exists")
            records.append({"cell_id": f"NASA_{mat.stem}", "skipped": True})
            continue
        battery = convert_cell(mat)
        battery.dump(target)
        records.append({"cell_id": battery.cell_id, "n_cycles": len(battery.cycle_data),
                        "n_degenerate": sum(c.additional_data["degenerate"] for c in battery.cycle_data)})
    return records
