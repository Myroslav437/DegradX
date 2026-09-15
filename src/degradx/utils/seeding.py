"""Seeding, with seeds separated by source.

The paper (Sec. 3.6) controls generation, model initialisation and attribution sampling by
separate seeds so their variance contributions can be reported apart. ``derive_seed`` maps
(base seed, source, keys...) to an independent 32-bit seed through numpy's SeedSequence, so
changing the model-init seed never perturbs the generation stream and vice versa.
"""

from __future__ import annotations

import hashlib
import os
import random

import numpy as np

SOURCES = ("generation", "model_init", "attribution", "split", "bootstrap", "fitting", "evaluation")


def _key_to_int(key: object) -> int:
    if isinstance(key, (int, np.integer)):
        return int(key)
    digest = hashlib.sha256(str(key).encode()).digest()
    return int.from_bytes(digest[:4], "little")


def derive_seed(base: int, source: str, *keys: object) -> int:
    """Independent 32-bit seed for one (source, keys) stream under a base seed."""
    if source not in SOURCES:
        raise ValueError(f"unknown seed source {source!r}; expected one of {SOURCES}")
    ss = np.random.SeedSequence(entropy=int(base), spawn_key=(_key_to_int(source), *map(_key_to_int, keys)))
    return int(ss.generate_state(1, dtype=np.uint32)[0])


def rng(base: int, source: str, *keys: object) -> np.random.Generator:
    return np.random.default_rng(derive_seed(base, source, *keys))


def seed_everything(seed: int, deterministic: bool = True) -> None:
    """Seed python, numpy and torch; optionally request deterministic torch kernels."""
    random.seed(seed)
    np.random.seed(seed % (2**32))
    try:
        import torch
    except ImportError:  # data-only stages run without torch
        return
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if deterministic:
        # required by cuBLAS for deterministic algorithms on CUDA >= 10.2
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        torch.use_deterministic_algorithms(True, warn_only=True)
