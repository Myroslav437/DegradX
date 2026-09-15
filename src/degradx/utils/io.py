"""Artifact IO: tables as CSV+JSON, figures as PNG+PDF, JSON with numpy support."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


class _NumpyEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return None if np.isnan(o) else float(o)
        if isinstance(o, np.bool_):
            return bool(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, Path):
            return str(o)
        return super().default(o)


def _nan_to_none(obj: Any) -> Any:
    if isinstance(obj, float) and np.isnan(obj):
        return None
    if isinstance(obj, dict):
        return {k: _nan_to_none(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_nan_to_none(v) for v in obj]
    return obj


def write_json(obj: Any, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_nan_to_none(obj), cls=_NumpyEncoder, indent=2, sort_keys=False) + "\n")
    return path


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text())


def save_table(df, stem: str | Path) -> tuple[Path, Path]:
    """Write a pandas DataFrame to ``<stem>.csv`` and ``<stem>.json`` (records orientation)."""
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    csv_path, json_path = stem.with_suffix(".csv"), stem.with_suffix(".json")
    df.to_csv(csv_path, index=False)
    write_json(json.loads(df.to_json(orient="records")), json_path)
    return csv_path, json_path


def save_figure(fig, stem: str | Path, dpi: int = 200) -> tuple[Path, Path]:
    """Write a matplotlib figure as PNG (review) and PDF (paper) with identical styling."""
    import matplotlib.pyplot as plt

    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    png, pdf = stem.with_suffix(".png"), stem.with_suffix(".pdf")
    fig.savefig(png, dpi=dpi)
    fig.savefig(pdf)
    plt.close(fig)
    return png, pdf


def sha256_file(path: str | Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()
