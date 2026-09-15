import pickle, sys, numpy as np, pandas as pd
df = lambda: pd.DataFrame({"Status": ["Constant current charge"]*3, "Cycle number": [1,1,1], "Current (mA)": [0., 1100., -1100.], "Voltage (V)": [3.3,3.6,3.2], "Capacity (mAh)": [0.,1.,2.], "Time (s)": [0.,10.,20.]})
obj = {"1-1": {"rul": {1: 100, 2: 99}, "dq": {1: 0.0}, "data": {1: df(), 2: df()}}}
with open(sys.argv[1], "wb") as f: pickle.dump(obj, f, protocol=int(sys.argv[2]))
print("made with pandas", pd.__version__, "numpy", np.__version__, "protocol", sys.argv[2])
