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
