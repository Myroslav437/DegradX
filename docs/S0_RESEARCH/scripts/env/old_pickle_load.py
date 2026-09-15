import pickle, sys, pandas as pd, numpy as np
for p in sys.argv[1:]:
    try:
        with open(p, "rb") as f: o = pickle.load(f)
        d = o["1-1"]["data"][1]
        print(f"plain pickle.load OK  pandas {pd.__version__} numpy {np.__version__} {p.split('/')[-1]}:", d["Current (mA)"].values / 1000., d.dtypes.tolist()[:2])
    except Exception as e:
        print(f"plain pickle.load FAIL pandas {pd.__version__} {p.split('/')[-1]}: {type(e).__name__}: {e}")
        try:
            o = pd.read_pickle(p); print("   pd.read_pickle OK")
        except Exception as e2:
            print("   pd.read_pickle FAIL", type(e2).__name__, e2)
