"""DegradX: dataset-calibrated synthetic benchmark for attribution evaluation on degrading systems.

The package implements Section 3 of the paper. Stage scripts under ``scripts/`` are the
human-facing entry points; everything they compute lives here.
"""

from pathlib import Path

__version__ = "0.0.1"

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "configs"
DATA_DIR = REPO_ROOT / "data"
ARTIFACTS_DIR = REPO_ROOT / "artifacts"
RESULTS_DIR = REPO_ROOT / "results"
DECLARATIONS_PATH = CONFIG_DIR / "declarations.yaml"

# v2 (brief "DegradX v2", declarations r3 declared_by_design.v2.paths): v2 stages write only under these roots; v1
# artifacts, results and data are read-only inputs to v2.
ARTIFACTS_V2 = ARTIFACTS_DIR / "v2"
RESULTS_V2 = RESULTS_DIR / "v2"
DATA_V2 = DATA_DIR / "v2"
