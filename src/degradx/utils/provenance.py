"""Run provenance: every stage writes logs/run.json and logs/timing.json (brief §4, R1).

``RunRecord`` captures what is needed to trace a number back to its origin: git commit and
dirty state, hashes of the resolved stage config and of the frozen declarations, package
versions, device, seeds, and wall-clock.
"""

from __future__ import annotations

import datetime as _dt
import platform
import subprocess
import sys
import time
from importlib import metadata
from pathlib import Path
from typing import Any

import yaml

from degradx import DECLARATIONS_PATH, REPO_ROOT
from degradx.utils.device import device_info
from degradx.utils.io import sha256_file, sha256_text, write_json

TRACKED_PACKAGES = (
    "numpy", "scipy", "pandas", "scikit-learn", "statsmodels", "torch", "captum", "timeshap",
    "shap", "BatteryML", "h5py", "matplotlib", "csaps", "kneed", "degradx",
)


def git_state() -> dict[str, Any]:
    def run(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip()

    try:
        commit = run("rev-parse", "HEAD")
        dirty = bool(run("status", "--porcelain", "--untracked-files=no"))
        return {"commit": commit or None, "dirty": dirty, "branch": run("rev-parse", "--abbrev-ref", "HEAD")}
    except FileNotFoundError:
        return {"commit": None, "dirty": None, "branch": None}


def package_versions(names: tuple[str, ...] = TRACKED_PACKAGES) -> dict[str, str | None]:
    out = {}
    for name in names:
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            out[name] = None
    return out


def config_hash(cfg: dict) -> str:
    return sha256_text(yaml.safe_dump(cfg, sort_keys=True))


class RunRecord:
    """Context manager that times a stage and writes run.json + timing.json on exit."""

    def __init__(self, stage: str, out_dir: Path, config: dict, seeds: dict, device: str, argv: list[str] | None = None):
        self.stage = stage
        self.out_dir = Path(out_dir)
        self.config = config
        self.seeds = seeds
        self.device = device
        self.argv = argv if argv is not None else sys.argv
        self.timings: dict[str, float] = {}
        self.extra: dict[str, Any] = {}
        self._t0 = 0.0
        self._sections: dict[str, float] = {}

    def __enter__(self) -> "RunRecord":
        self._t0 = time.perf_counter()
        self.started = _dt.datetime.now(_dt.timezone.utc).isoformat()
        return self

    def section(self, name: str) -> "_Section":
        return _Section(self, name)

    def __exit__(self, exc_type, exc, tb) -> None:
        wall = time.perf_counter() - self._t0
        logs = self.out_dir / "logs"
        record = {
            "stage": self.stage,
            "argv": self.argv,
            "started_utc": self.started,
            "finished_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "wall_clock_s": round(wall, 3),
            "status": "error" if exc_type else "ok",
            "error": repr(exc) if exc else None,
            "git": git_state(),
            "config_hash": config_hash(self.config),
            "config": self.config,
            "declarations_sha256": sha256_file(DECLARATIONS_PATH) if DECLARATIONS_PATH.exists() else None,
            "seeds": self.seeds,
            "device": device_info(self.device),
            "python": sys.version,
            "platform": platform.platform(),
            "packages": package_versions(),
            **self.extra,
        }
        write_json(record, logs / "run.json")
        write_json({"stage": self.stage, "device": self.device, "wall_clock_s": round(wall, 3),
                    "sections_s": {k: round(v, 3) for k, v in self.timings.items()}}, logs / "timing.json")


class _Section:
    def __init__(self, record: RunRecord, name: str):
        self.record, self.name = record, name

    def __enter__(self) -> None:
        self.t0 = time.perf_counter()

    def __exit__(self, *exc) -> None:
        self.record.timings[self.name] = self.record.timings.get(self.name, 0.0) + time.perf_counter() - self.t0
