"""HUST ingestion: BatteryML CLI, then attach the cycler's per-cycle capacity (brief R3).

``batteryml preprocess HUST <raw> <processed>`` writes one ``BatteryData`` per cell but drops the
source pickle's ``dq`` (per-cycle discharge capacity recorded by the cycler, mAh) and recomputes
``discharge_capacity_in_Ah`` by rectangle integration of I dt, which reads about 20 mAh above ``dq``
on the cells inspected at S0 (docs/S0_RESEARCH/datasets.md §2.3). Because the dataset's stopping rule
("until the maximum capacity first reached 80% of nominal") is stated on the cycler's capacity, ``dq`` is
attached to every ``CycleData`` as ``additional_data['capacity_cycler_Ah']`` (Ah), matched on
``cycle_number`` (BatteryML sets ``cycle_number = source cycle key``; ``HUST_7-5`` starts at 3).
The integrated field is left untouched; S1 reports the agreement of the two.
"""

from __future__ import annotations

import pickle
import zipfile
from pathlib import Path

RAW_ZIP = "hust_data.zip"


def augment(raw_dir: Path, processed_dir: Path, force: bool = False) -> list[dict]:
    from batteryml import BatteryData

    records = []
    with zipfile.ZipFile(raw_dir / RAW_ZIP) as zf:
        members = {Path(n).stem: n for n in zf.namelist() if n.endswith(".pkl")}
        for pkl in sorted(processed_dir.glob("HUST_*.pkl")):
            battery = BatteryData.load(pkl)
            if getattr(battery, "cycler_capacity_attached", False) and not force:
                records.append({"cell_id": battery.cell_id, "skipped": True})
                continue
            cell = battery.cell_id.split("_", 1)[1]
            with zf.open(members[cell]) as fh:
                src = pickle.load(fh)[cell]
            dq = src["dq"]
            missing = 0
            for cd in battery.cycle_data:
                val = dq.get(cd.cycle_number)
                if val is None:
                    missing += 1
                cd.additional_data["capacity_cycler_Ah"] = float(val) / 1000.0 if val is not None else float("nan")
            battery.cycler_capacity_attached = True
            battery.source_n_cycles = len(src["data"])
            battery.dump(pkl)
            records.append({"cell_id": battery.cell_id, "n_cycles": len(battery.cycle_data),
                            "source_n_cycles": len(src["data"]), "dq_missing": missing})
            del battery, src
    return records
