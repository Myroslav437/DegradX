import importlib, importlib.metadata as md, warnings, sys
mods = ["numpy","scipy","pandas","sklearn","statsmodels","csaps","h5py","matplotlib","yaml","omegaconf","typer","pytest","umap","tqdm","torch","captum","shap","altair","timeshap","batteryml","xgboost","numba"]
dists = {"sklearn":"scikit-learn","yaml":"pyyaml","umap":"umap-learn"}
for m in mods:
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            importlib.import_module(m)
        d = dists.get(m, m)
        print(f"OK   {m:12s} {md.version(d)}  warnings={len(w)}" + ("" if not w else "  first: " + str(w[0].message)[:160]))
    except Exception as e:
        print(f"FAIL {m:12s} {type(e).__name__}: {e}")
