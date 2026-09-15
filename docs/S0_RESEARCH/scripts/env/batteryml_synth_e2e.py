"""Synthetic end-to-end exercise of BatteryML MATR/HUST preprocessing code paths.
Builds tiny fake inputs with the structure the preprocessors index into (NOT real data)."""
import sys, os, tempfile, pickle, zipfile, pathlib
import numpy as np, h5py, pandas as pd
from batteryml import BatteryData
from batteryml.preprocess.preprocess_MATR import load_batch, organize_cell
from batteryml.preprocess import HUSTPreprocessor
print("numpy", np.__version__, "pandas", pd.__version__, "h5py", h5py.__version__)
work = pathlib.Path(tempfile.mkdtemp())

# ---- MATR: MATLAB v7.3 (HDF5) layout with object references
fn = work / "MATR_fake.mat"
rng = np.random.default_rng(0)
with h5py.File(fn, "w") as f:
    refs = f.create_group("#refs#")
    ref_dt = h5py.ref_dtype
    n_cells, n_cyc, n_pts = 2, 4, 7
    b = f.create_group("batch")
    def ds(name, arr):
        return refs.create_dataset(name, data=arr).ref
    summ = np.empty((n_cells, 1), dtype=ref_dt); cl = np.empty((n_cells, 1), dtype=ref_dt)
    pol = np.empty((n_cells, 1), dtype=ref_dt); cyc = np.empty((n_cells, 1), dtype=ref_dt)
    for i in range(n_cells):
        g = refs.create_group(f"summary{i}")
        for k in ["IR", "QCharge", "QDischarge", "Tavg", "Tmin", "Tmax", "chargetime", "cycle"]:
            g.create_dataset(k, data=rng.random((1, n_cyc)))
        summ[i, 0] = g.ref
        cl[i, 0] = ds(f"cl{i}", np.array([[500.0 + i]]))
        policy = "3.6C(80%)-3.6C"
        pol[i, 0] = ds(f"pol{i}", np.frombuffer(policy.encode("utf-16-le"), dtype=np.uint16).reshape(-1, 1))
        cg = refs.create_group(f"cycles{i}")
        for k in ["I", "Qc", "Qd", "Qdlin", "T", "Tdlin", "V", "discharge_dQdV", "t"]:
            r = np.empty((n_cyc, 1), dtype=ref_dt)
            for j in range(n_cyc):
                r[j, 0] = ds(f"c{i}_{k}_{j}", rng.random((1, n_pts)))
            cg.create_dataset(k, data=r)
        cyc[i, 0] = cg.ref
    for name, arr in [("summary", summ), ("cycle_life", cl), ("policy_readable", pol), ("cycles", cyc)]:
        b.create_dataset(name, data=arr)
bd = load_batch(fn, 1)
cell = organize_cell(bd["b1c0"], "b1c0")
p = work / "MATR_b1c0.pkl"; cell.dump(p); back = BatteryData.load(p)
print("MATR synth: cells", list(bd), "cycles kept", len(back.cycle_data),
      "policy", bd["b1c0"]["charge_policy"], "charge_protocol rates", [c.rate_in_C for c in back.charge_protocol])

# ---- HUST: zip containing our_data/<cell>.pkl = {cell: {'data': {cycle_no: DataFrame}}}
raw = work / "hust_raw"; (raw / "our_data").mkdir(parents=True)
cells = {"1-1": {"data": {c: pd.DataFrame({"Current (mA)": [0., 1100., -1100., -1100.],
                                            "Time (s)": [0., 10., 20., 30.],
                                            "Voltage (V)": [3.3, 3.6, 3.2, 2.9]}) for c in (1, 2, 3)}}}
with open(raw / "our_data" / "1-1.pkl", "wb") as fo: pickle.dump(cells, fo)
with zipfile.ZipFile(raw / "hust_data.zip", "w") as z: z.write(raw / "our_data" / "1-1.pkl", "our_data/1-1.pkl")
import shutil; shutil.rmtree(raw / "our_data")
out = work / "hust_out"; out.mkdir()
HUSTPreprocessor(output_dir=out, silent=True)(raw)
hb = BatteryData.load(out / "HUST_1-1.pkl")
print("HUST synth: cycles", len(hb.cycle_data), "Qd last cycle", hb.cycle_data[-1].discharge_capacity_in_Ah,
      "discharge rates", [c.rate_in_C for c in hb.discharge_protocol])
print("E2E OK")
