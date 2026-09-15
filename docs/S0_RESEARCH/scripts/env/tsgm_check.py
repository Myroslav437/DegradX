import os, sys, traceback
import numpy as np
print("numpy", np.__version__, "KERAS_BACKEND env", os.environ.get("KERAS_BACKEND"))
try:
    import tsgm, keras
    print("tsgm import OK", getattr(tsgm, "__version__", "?"), "keras", keras.__version__, "backend", keras.backend.backend())
except Exception as e:
    print("tsgm import FAILED:", type(e).__name__, str(e)[:400]); traceback.print_exc(limit=3); sys.exit(1)
rng = np.random.default_rng(0)
X1 = rng.normal(size=(64, 20, 3)).astype("float32"); X2 = rng.normal(0.3, 1, size=(64, 20, 3)).astype("float32")
try:
    print("MMD", float(tsgm.metrics.MMDMetric()(X1, X2)))
except Exception as e:
    print("MMD FAILED:", type(e).__name__, str(e)[:300])
try:
    model = tsgm.models.zoo["clf_cl_n"](seq_len=20, feat_dim=3, output_dim=1).model
    model.compile(loss="binary_crossentropy", optimizer="adam", metrics=["accuracy"])
    acc = tsgm.metrics.DiscriminativeMetric()(X1, X2, model=model, test_size=0.25, n_epochs=2, random_seed=0)
    print("DiscriminativeMetric acc", acc)
except Exception as e:
    print("DiscriminativeMetric FAILED:", type(e).__name__, str(e)[:400]); traceback.print_exc(limit=4)
