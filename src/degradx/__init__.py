"""DegradX: dataset-calibrated synthetic testbed for attribution evaluation on degrading systems.

The package implements the generator, the fitting procedure, the decomposable target and its attribution ground truth,
the fidelity / usability measures and the attribution scores. Stage scripts under ``scripts/`` are the entry points.
"""

from pathlib import Path

__version__ = "0.0.1"

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "configs"
DATA_DIR = REPO_ROOT / "data"
ARTIFACTS_DIR = REPO_ROOT / "artifacts"
RESULTS_DIR = REPO_ROOT / "results"
DECLARATIONS_PATH = CONFIG_DIR / "declarations.yaml"
