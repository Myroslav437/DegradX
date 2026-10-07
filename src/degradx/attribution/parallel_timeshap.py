"""TimeSHAP over many windows in a process pool, with a checkpoint per window (brief "DegradX v2", X7 / V8; declarations
r3 declared_by_design.v2.timeshap_full_scale.feasibility).

The method is unchanged: every window is explained by ``degradx.attribution.methods.timeshap`` with its declared
attribution-sampling seed, nsamples and l1_reg; only the scheduling changes. Windows are independent, so a pool over
windows returns the same maps as a sequential loop when each worker evaluates the model on the same device with the same
batch size (checked on 20 windows before a full run: maximum absolute difference <= 1e-10).

A job is (row key, window index, seed); its map is written to ``<checkpoint_dir>/<row>/w<idx>_s<seed>.npy`` and a
finished job is skipped on restart. Throughput is appended to ``<checkpoint_dir>/throughput.jsonl``.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

_W: dict = {}  # per-worker state


@dataclass(frozen=True)
class ModelSpec:
    """How a worker builds the explained function: a trained member checkpoint or the reference model."""
    kind: str                     # "trained" | "reference"
    path: str | None = None       # checkpoint (.pt) for trained members
    weights: np.ndarray | None = None
    x0: np.ndarray | None = None


@dataclass(frozen=True)
class Job:
    row: str                      # output key, e.g. "MATR/recency/trained/primary/window" (unique per model, weighting, input kind)
    model_key: str                # key into the model-spec table passed to the pool
    window_key: str               # key into the window table (arrays (N, L, C))
    index: int                    # window index within that array
    seed: int                     # declared attribution-sampling seed
    background_key: str           # key into the background-event table


def _init_worker(model_specs: dict, backgrounds: dict, windows: dict, device: str, chunk: int, nsamples: int, l1_reg, threads: int) -> None:
    os.environ["OMP_NUM_THREADS"] = str(threads)
    os.environ["MKL_NUM_THREADS"] = str(threads)
    os.environ["OPENBLAS_NUM_THREADS"] = str(threads)
    import torch

    torch.set_num_threads(threads)
    _W.update(model_specs=model_specs, backgrounds=backgrounds, windows=windows, device=device, chunk=chunk, nsamples=nsamples, l1_reg=l1_reg,
              models={})


def _model(key: str):
    if key not in _W["models"]:
        from degradx.attribution import methods as M

        spec: ModelSpec = _W["model_specs"][key]
        if spec.kind == "reference":
            _W["models"][key] = M.ReferenceModel(spec.weights, spec.x0)
        else:
            from degradx.models.lstm import LSTMRegressor, Standardiser, TrainedModel
            import torch

            ck = torch.load(spec.path, map_location=_W["device"], weights_only=False)
            arch = ck["arch"]
            model = LSTMRegressor(len(ck["channels"]), arch["hidden_size"], arch["num_layers"]).to(_W["device"])
            model.load_state_dict(ck["state_dict"])
            sc = ck["scaler"]
            tm = TrainedModel(model, Standardiser(np.asarray(sc["mean"]), np.asarray(sc["std"]), float(sc["y_mean"]), float(sc["y_std"])), {}, _W["device"])
            _W["models"][key] = M.RawSpaceModel(tm)
    return _W["models"][key]


def explain_one(job: Job) -> tuple[Job, np.ndarray, float]:
    """One window with its declared seed (the code path of methods.timeshap, single window)."""
    from degradx.attribution.timeshap_compat import import_timeshap

    import_timeshap()
    from timeshap.explainer.kernel import TimeShapKernel

    from degradx.attribution.methods import numpy_callable

    t0 = time.perf_counter()
    x = _W["windows"][job.window_key][job.index:job.index + 1].astype(float)
    L, C = x.shape[1], x.shape[2]
    bg = np.asarray(_W["backgrounds"][job.background_key], float).reshape(1, C)
    f = numpy_callable(_model(job.model_key), _W["device"], chunk=_W["chunk"])
    ker = TimeShapKernel(f, bg, job.seed, "cell", varying=(list(range(L)), list(range(C))))
    phi = ker.shap_values(x, pruning_idx=0, nsamples=_W["nsamples"], l1_reg=_W["l1_reg"])
    return job, np.asarray(phi, dtype=float).reshape(L, C), time.perf_counter() - t0


def job_path(ckpt: Path, job: Job) -> Path:
    return Path(ckpt) / job.row.replace("/", "__") / f"w{job.index:04d}_s{job.seed}.npy"


def run_jobs(jobs: list[Job], *, model_specs: dict, backgrounds: dict, windows: dict, checkpoint_dir: Path, workers: int, device: str = "cpu",
             chunk: int = 4096, nsamples: int = 32000, l1_reg="auto", threads_per_worker: int = 1, log_every: int = 20, label: str = "") -> dict:
    """Run every job not yet checkpointed; returns counts and throughput. ``windows`` maps a window key to an array
    (N, L, C); ``model_specs`` maps a model key to a ModelSpec; ``backgrounds`` maps a key to a (C,) event."""
    ckpt = Path(checkpoint_dir)
    todo = [j for j in jobs if not job_path(ckpt, j).exists()]
    t0 = time.perf_counter()
    done, secs = 0, []
    init = (model_specs, backgrounds, windows, device, chunk, nsamples, l1_reg, threads_per_worker)
    tp_log = ckpt / "throughput.jsonl"
    ckpt.mkdir(parents=True, exist_ok=True)

    def _store(job, phi, s):
        p = job_path(ckpt, job)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp.npy")
        np.save(tmp, phi)
        os.replace(tmp, p)

    if workers <= 1:
        _init_worker(*init)
        for j in todo:
            job, phi, s = explain_one(j)
            _store(job, phi, s)
            done += 1
            secs.append(s)
            if done % log_every == 0:
                _log(tp_log, label, done, len(todo), t0, secs)
    else:
        from multiprocessing import get_context

        with get_context("spawn").Pool(workers, initializer=_init_worker, initargs=init) as pool:
            for job, phi, s in pool.imap_unordered(explain_one, todo, chunksize=1):
                _store(job, phi, s)
                done += 1
                secs.append(s)
                if done % log_every == 0:
                    _log(tp_log, label, done, len(todo), t0, secs)
    wall = time.perf_counter() - t0
    out = {"label": label, "jobs": len(jobs), "already_done": len(jobs) - len(todo), "ran": done, "wall_s": wall,
           "windows_per_hour": done / wall * 3600 if wall > 0 and done else None, "mean_window_s": float(np.mean(secs)) if secs else None,
           "workers": workers, "device": device, "chunk": chunk}
    with open(tp_log, "a") as fh:
        fh.write(json.dumps({**out, "final": True}) + "\n")
    return out


def _log(path: Path, label: str, done: int, total: int, t0: float, secs: list) -> None:
    wall = time.perf_counter() - t0
    rec = {"label": label, "done": done, "of": total, "wall_s": wall, "windows_per_hour": done / wall * 3600, "mean_window_s": float(np.mean(secs)),
           "eta_h": (total - done) / (done / wall) / 3600 if done else None, "time": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(path, "a") as fh:
        fh.write(json.dumps(rec) + "\n")
    print(f"[timeshap] {label} {done}/{total} {rec['windows_per_hour']:.0f}/h eta {rec['eta_h']:.2f} h", flush=True)


def collect(jobs: list[Job], checkpoint_dir: Path) -> dict:
    """{row: {seed: (N, L, C) array}} from the checkpoints of ``jobs`` (missing windows raise)."""
    out: dict = {}
    for j in jobs:
        out.setdefault(j.row, {}).setdefault(j.seed, {})[j.index] = np.load(job_path(checkpoint_dir, j))
    return {r: {s: np.stack([d[i] for i in sorted(d)]) for s, d in by.items()} for r, by in out.items()}
