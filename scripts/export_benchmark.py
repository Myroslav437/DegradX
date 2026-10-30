#!/usr/bin/env python
"""Benchmark bundle: the generated units of the evaluated profiles with their attribution ground truth, as a
self-contained directory (and archive) for release.

Inputs: the generated-unit caches written by the generation stage (``data/generated/<dataset>/seed<g>.pkl``; regenerate
them with ``scripts/run_all.sh`` or the generation commands
in the README), the fitted profiles, and the target constants (kappa, x0) recorded by the generation stage. No measured
data are read.

Per profile and generation seed the bundle stores the exact decomposition of every unit (state z, mean component m,
inserted patterns p, noise eps) in ``<PROFILE>/seed<g>.npz``; the windows, the target y and the ground truth phi* are
rebuilt from it by ``degradx_benchmark.py`` (NumPy only), which is checked here against ``degradx.targets`` on every window
of every exported unit (exact equality). Also written: the fitted profiles, the evaluation windows of the reported
reference values, the scoring functions (``scores.py``), a datasheet (``README.md``), ``manifest.json`` and ``SHA256SUMS``.

    python scripts/export_benchmark.py                       # all profiles, seeds 0-2 -> dist/DegradX-benchmark/ + .zip
    python scripts/export_benchmark.py --profiles FORM --seeds 0 --no-archive
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np  # noqa: E402

import _common as C  # noqa: E402
from degradx import ARTIFACTS_DIR, REPO_ROOT, __version__  # noqa: E402
from degradx.generator.generate import NULL_CHANNELS, Profile  # noqa: E402
from degradx.targets.decomposable import TargetSpec, unit_targets  # noqa: E402
from degradx.utils.config import load_declarations  # noqa: E402
from degradx.utils.seeding import rng  # noqa: E402

# public profile name -> dataset key used by the pipeline
PROFILES = {"MATR": "MATR", "HUST": "HUST", "FORM": "TRI_FORMATION"}
GEN_SUMMARY = ARTIFACTS_DIR / "s10_generate_units" / "tables" / "summary.json"
MODELS = "artifacts/s13_usability/models"
BUNDLE_SRC = Path(__file__).resolve().parent / "bundle"
BASE_SEED = 20260915


def target_spec(ds: str, decl: dict) -> TargetSpec:
    """The TargetSpec the generation stage used. x0 of null_permuted is the median of the measured null pool, recorded with
    kappa and x0 in the generation summary, so the bundle needs no measured data."""
    dd = decl["declared_by_design"]
    summ = json.loads(GEN_SUMMARY.read_text())[ds]
    P = Profile.from_json(C.fitted_profile(ds), np.array([summ["x0"]["null_permuted"]]))
    spec = TargetSpec.build(P, dd["target"]["weights"]["beta"]["value"], int(dd["target"]["window_length_L"]["value"]), 6.0)
    for name, rec in (("kappa", spec.kappa), ("x0", spec.x0)):
        want = np.array([summ[name][c] for c in spec.channels])
        if not np.allclose(rec, want, rtol=0, atol=1e-12):
            raise RuntimeError(f"{ds}: {name} rebuilt from the profile differs from the generation summary")
    return spec


def select_windows(test_units, L: int, n_windows: int, g):
    """The reference-value window rule (scripts/s15_reference_values.py select_windows): stratified across test units."""
    eligible = [u for u in test_units if u.T >= L]
    per = int(np.ceil(n_windows / len(eligible)))
    picks = []
    for ui, u in enumerate(eligible):
        ends = np.arange(L, u.T + 1)
        for e in np.sort(g.choice(ends, size=min(per, len(ends)), replace=False)):
            picks.append((ui, int(e)))
    idx = np.sort(g.choice(len(picks), size=min(n_windows, len(picks)), replace=False))
    return [(eligible[picks[i][0]].index, picks[i][1]) for i in idx]


def jsonable(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.bool_,)):
        return bool(o)
    raise TypeError(type(o))


def export_seed(ds: str, name: str, gs: int, out: Path) -> dict:
    units, table = pickle.loads((C.generated_dir(ds) / f"seed{gs}.pkl").read_bytes())
    split = dict(zip(table["index"], table["split"]))
    T = np.array([u.T for u in units], int)
    offsets = np.concatenate([[0], np.cumsum(T)])
    np.savez_compressed(out / name / f"seed{gs}.npz",
                        unit_index=np.array([u.index for u in units], int), source_unit=np.array([u.source_unit for u in units], dtype="U"),
                        split=np.array([split[u.index] for u in units], dtype="U"), T=T, offsets=offsets,
                        z=np.concatenate([u.z for u in units]), m=np.concatenate([u.m for u in units]),
                        p=np.concatenate([u.p for u in units]), eps=np.concatenate([u.eps for u in units]))
    write(out / name / f"seed{gs}_patterns.json", json.dumps([u.patterns for u in units], default=jsonable))
    return {"units": len(units), "positions": int(T.sum()), "splits": {s: int(sum(v == s for v in split.values())) for s in ("train", "validation", "test")},
            "units_with_patterns": int(sum(len(u.patterns) > 0 for u in units)), "patterns": int(sum(len(u.patterns) for u in units)),
            "T_median": float(np.median(T)), "T_min": int(T.min()), "T_max": int(T.max())}, units, split


def verify(units, spec: TargetSpec, out: Path, name: str, gs: int, weightings) -> int:
    """Every window of every exported unit, rebuilt by the bundle loader, equals degradx.targets.unit_targets exactly."""
    if str(out) not in sys.path:
        sys.path.insert(0, str(out))
    import degradx_benchmark as B

    b = B.load(name, gs, root=out)
    n = 0
    for i, u in enumerate(units):
        bu = b.unit(i)
        assert bu.index == u.index and bu.T == u.T
        if u.T < spec.L:
            continue
        for kind in weightings:
            ref, got = unit_targets(u, spec, kind), b.windows(bu, kind)
            for k in ("x", "x_pattern_free", "graded", "sparse", "phi_star", "y", "g", "R", "z_end"):
                if not np.array_equal(ref[k], got[k]):
                    raise RuntimeError(f"{name} seed {gs} unit {u.index} [{kind}]: loader differs from degradx on {k}")
            n += len(ref["y"])
    return n


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")  # LF on every platform, so SHA256SUMS checks anywhere


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--profiles", nargs="*", default=list(PROFILES), choices=list(PROFILES))
    p.add_argument("--seeds", nargs="*", type=int, default=None, help="generation seeds (default: the declared ones)")
    p.add_argument("--out", type=Path, default=REPO_ROOT / "dist" / "DegradX-benchmark")
    p.add_argument("--no-archive", action="store_true", help="write the directory only, no .zip")
    p.add_argument("--skip-verify", action="store_true")
    args = p.parse_args()

    decl = load_declarations()
    dd = decl["declared_by_design"]
    seeds = args.seeds if args.seeds is not None else list(dd["statistics"]["seeds"]["generation"])
    sc = dd["protocol"]["scope"]["weightings"]
    weightings = [sc["primary"], sc["sensitivity"]]
    n_eval = int(dd["attribution"]["windows_scored_per_profile"])
    out = args.out
    if out.exists():
        shutil.rmtree(out)
    (out / "profiles").mkdir(parents=True)
    shutil.copy(BUNDLE_SRC / "degradx_benchmark.py", out / "degradx_benchmark.py")
    shutil.copy(REPO_ROOT / "src" / "degradx" / "metrics" / "scores.py", out / "scores.py")
    manifest = {"name": "DegradX benchmark", "degradx_version": __version__, "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "base_seed": BASE_SEED, "generation_seeds": seeds, "weightings": weightings, "profiles": {}}
    for name in args.profiles:
        ds = PROFILES[name]
        spec = target_spec(ds, decl)
        (out / name).mkdir()
        shutil.copy(C.profiles_dir(ds) / "profiles" / f"{ds}.json", out / "profiles" / f"{name}.json")
        prof = C.fitted_profile(ds)
        info = {"dataset_key": ds, "channels": spec.channels, "weighted_channels": [c for c, k in zip(spec.channels, spec.kappa) if k != 0],
                "null_channels": list(NULL_CHANNELS), "kappa": spec.kappa.tolist(), "x0": spec.x0.tolist(), "L": spec.L,
                "position_profiles": {k: spec.pi[k].tolist() for k in weightings}, "pattern_channel": spec.pattern_channel,
                "pattern_types_enabled": [t for t, v in prof["estimated_from_data"]["E6_patterns"].items() if isinstance(v, dict) and v.get("enabled")],
                "trajectory_family": prof["estimated_from_data"]["E1_theta_distribution"]["family"], "q_nom_Ah": prof["declared_used"]["q_nom_Ah"],
                "rho": prof["declared_used"]["rho"], "trained_models_in_repository": MODELS, "seeds": {}}
        manifest["profiles"][name] = info
        for gs in seeds:
            stats, units, split = export_seed(ds, name, gs, out)
            write(out / "manifest.json", json.dumps(manifest, indent=1))  # the loader reads the profile constants from it
            if not args.skip_verify:
                stats["windows_verified"] = verify(units, spec, out, name, gs, weightings)
            info["seeds"][str(gs)] = stats
            if gs == 0:
                test = [u for u in units if split[u.index] == "test"]
                picks = select_windows(test, spec.L, n_eval, rng(BASE_SEED, "evaluation", "s8", ds))
                write(out / name / "evaluation_windows.csv", "unit_index,t\n" + "".join(f"{ui},{t}\n" for ui, t in picks))
                info["evaluation_windows"] = len(picks)
            print(f"[bundle] {name} seed {gs}: {stats}", flush=True)
    write(out / "manifest.json", json.dumps(manifest, indent=1))
    tmpl = (BUNDLE_SRC / "DATASHEET.md").read_text(encoding="utf-8")
    rows = "\n".join(f"| {n} | {', '.join(i['channels'])} | {', '.join(i['weighted_channels'])} | {i['trajectory_family']} | "
                     f"{', '.join(i['pattern_types_enabled']) or 'none'} | "
                     + " / ".join(f"{s['units']} ({s['positions']:,} pos.)" for s in i["seeds"].values()) + " |" for n, i in manifest["profiles"].items())
    write(out / "README.md", tmpl.replace("{{PROFILE_ROWS}}", rows).replace("{{SEEDS}}", ", ".join(map(str, seeds))))
    files = sorted(f for f in out.rglob("*") if f.is_file() and f.name != "SHA256SUMS" and "__pycache__" not in f.parts)
    write(out / "SHA256SUMS", "".join(f"{sha256(f)}  {f.relative_to(out).as_posix()}\n" for f in files))
    shutil.rmtree(out / "__pycache__", ignore_errors=True)
    print(f"[bundle] wrote {out} ({sum(f.stat().st_size for f in files) / 1e6:.1f} MB)")
    if not args.no_archive:
        arc = shutil.make_archive(str(out), "zip", root_dir=out.parent, base_dir=out.name)
        print(f"[bundle] archive {arc} ({Path(arc).stat().st_size / 1e6:.1f} MB), sha256 {sha256(Path(arc))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
