import sys, tempfile, os, pathlib, warnings
warnings.simplefilter("default")
import numpy as np
import batteryml
from batteryml import BatteryData, CycleData, CyclingProtocol
from batteryml.preprocess import MATRPreprocessor, HUSTPreprocessor, SUPPORTED_SOURCES
from batteryml.builders import PREPROCESSORS
from batteryml.preprocess.preprocess_HUST import calc_Q
print("numpy", np.__version__, "batteryml file", batteryml.__file__)
cycles = [CycleData(i, voltage_in_V=list(np.linspace(3.5,2.0,5)), current_in_A=list(-np.ones(5)),
                    discharge_capacity_in_Ah=list(np.linspace(0,1.1-0.001*i,5)), time_in_s=list(np.arange(5.)),
                    internal_resistance_in_ohm=np.float64(0.015), Qdlin=list(np.zeros(3))) for i in range(1, 4)]
b = BatteryData("TEST_cell", cycle_data=cycles, nominal_capacity_in_Ah=1.1,
                charge_protocol=CyclingProtocol(rate_in_C=1.0), discharge_protocol=[CyclingProtocol(rate_in_C=4.0)])
d = tempfile.mkdtemp()
p = os.path.join(d, "TEST_cell.pkl"); b.dump(p)
b2 = BatteryData.load(p)
assert b2.cell_id == b.cell_id and len(b2.cycle_data) == 3
assert b2.cycle_data[2].discharge_capacity_in_Ah == b.cycle_data[2].discharge_capacity_in_Ah
assert b2.cycle_data[0].additional_data["Qdlin"] == [0.0,0.0,0.0]
print("dump/load roundtrip OK; IR type after load:", type(b2.cycle_data[0].internal_resistance_in_ohm))
I = np.array([0., 1., 1., -1., -1.]); t = np.arange(5.)*3600
print("HUST calc_Q (numba njit) charge:", calc_Q(I, t, True), "discharge:", calc_Q(I, t, False))
print("PREPROCESSORS registered:", sorted(PREPROCESSORS._module_dict.keys()) if hasattr(PREPROCESSORS, "_module_dict") else PREPROCESSORS)
# MATR preprocessor constructed against a temp output dir, pointed at an empty dir -> expect FileNotFoundError path
pre = MATRPreprocessor(output_dir=d, silent=True)
try:
    pre.process(pathlib.Path(d))
except FileNotFoundError as e:
    print("MATRPreprocessor.process on empty dir -> FileNotFoundError as expected:", str(e)[-40:])
print("SUPPORTED_SOURCES", SUPPORTED_SOURCES)
