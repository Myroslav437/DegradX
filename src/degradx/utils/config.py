"""Loading of frozen declarations and per-stage run configs.

``configs/declarations.yaml`` holds every constant the paper declares by design (R7). Stage
configs under ``configs/stages/`` may only add run-level settings (paths, budgets, which
profiles to process); they never redefine a declared constant. ``load_stage_config`` enforces
that by refusing a stage config that carries a top-level ``declared`` key.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from degradx import CONFIG_DIR, DECLARATIONS_PATH


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_declarations(path: str | Path = DECLARATIONS_PATH) -> dict[str, Any]:
    decl = load_yaml(path)
    for key in ("declared_by_design", "estimated_from_data"):
        if key not in decl:
            raise KeyError(f"{path} must contain a top-level '{key}' section (paper §3.3 split)")
    return decl


def declared(decl: dict[str, Any], dotted: str) -> Any:
    """Fetch a declared constant by dotted path, e.g. ``declared(d, 'eol.rho')``."""
    node: Any = decl["declared_by_design"]
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            raise KeyError(f"declaration '{dotted}' not found (missing '{part}')")
        node = node[part]
    if isinstance(node, dict) and "value" in node:
        return node["value"]
    return node


def load_stage_config(path: str | Path) -> dict[str, Any]:
    cfg = load_yaml(path)
    if "declared_by_design" in cfg or "declared" in cfg:
        raise ValueError(f"{path}: stage configs must not redefine declared constants; edit declarations.yaml")
    return cfg


def load_profile_config(profile: str) -> dict[str, Any]:
    return load_yaml(CONFIG_DIR / "profiles" / f"{profile}.yaml")
