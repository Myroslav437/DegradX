"""Device selection with CPU fallback (brief R9)."""

from __future__ import annotations

import warnings


def default_device() -> str:
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


def resolve_device(requested: str | None) -> str:
    """Return the device to use; falls back to CPU with a warning when CUDA is unavailable."""
    requested = requested or default_device()
    if requested == "cuda":
        try:
            import torch

            if not torch.cuda.is_available():
                warnings.warn("--device cuda requested but CUDA is unavailable; falling back to cpu")
                return "cpu"
        except ImportError:
            return "cpu"
    if requested not in ("cuda", "cpu"):
        raise ValueError(f"device must be 'cuda' or 'cpu', got {requested!r}")
    return requested


def device_info(device: str) -> dict:
    info = {"device": device}
    try:
        import torch

        info["torch"] = torch.__version__
        info["cuda_available"] = torch.cuda.is_available()
        if device == "cuda" and torch.cuda.is_available():
            info["gpu"] = torch.cuda.get_device_name(0)
            info["cuda_runtime"] = torch.version.cuda
            info["cudnn"] = torch.backends.cudnn.version()
    except ImportError:
        info["torch"] = None
    return info
