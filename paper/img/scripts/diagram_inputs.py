"""Inputs of the methodology diagrams (Figures 1-5; brief v2.1 W9).

Every number and label that a diagram prints is read here from the declarations, a fitted profile, or a generated set;
nothing is typed by hand except purely structural words. The helpers only read files and evaluate fitted mappings; no
stage computation is re-run.

Sources (paths relative to the repository root):
  configs/declarations.yaml
      declared_by_design.v2_1.scope.profiles          profiles evaluated (final_from_v2 + new)
      declared_by_design.statistics.splits.measured   fitting / held-out fractions
      declared_by_design.target.window_length_L       L
      declared_by_design.target.position_profiles     recency (h), uniform, final_position (and its supersession)
      declared_by_design.v2.scope.weightings          primary / sensitivity weighting
      declared_by_design.v2.scope.dropped             final_position_weighting, representation_distance (D25)
      declared_by_design.fidelity                     fidelity measures (minus superseded ones)
      declared_by_design.v2.fidelity.table2           property table
      declared_by_design.v2.tstr_isolation.input_sets X1 input sets (minus the sensitivity-only set)
      declared_by_design.usability.identifiability_floor.value   ensemble seeds x configurations
      declared_by_design.channels.roles.weighted_pattern_carrying channel that carries inserted patterns
  scripts/v2/v5_fidelity.py (INPUT_SETS, read with ast, not executed)  cross-check of the input sets
  src/degradx/viz/s3.py LABEL                          display label of each profile key
  artifacts/v2.1/w3_fit_profiles/profiles/TRI_FORMATION.json        FORM profile
  artifacts/v2/v3_fit_profiles/profiles/{MATR,HUST}.json            E6 pattern flags of MATR, HUST
  data/v2.1/generated/TRI_FORMATION/seed0.pkl                       FORM generated units, generation seed 0
"""
from __future__ import annotations

import ast
import json
import pickle
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[3]
IMG = ROOT / "paper" / "img"
DECLARATIONS = ROOT / "configs" / "declarations.yaml"
V5_SCRIPT = ROOT / "scripts" / "v2" / "v5_fidelity.py"
FORM_KEY = "TRI_FORMATION"
FORM_PROFILE = ROOT / "artifacts" / "v2.1" / "w3_fit_profiles" / "profiles" / f"{FORM_KEY}.json"
FORM_GENERATED = ROOT / "data" / "v2.1" / "generated" / FORM_KEY / "seed0.pkl"
V2_PROFILE = ROOT / "artifacts" / "v2" / "v3_fit_profiles" / "profiles" / "{ds}.json"


# ---------------------------------------------------------------------------------------------- declarations
@lru_cache(maxsize=1)
def declared() -> dict:
    with open(DECLARATIONS) as fh:
        return yaml.safe_load(fh)["declared_by_design"]


def label(ds: str) -> str:
    from degradx.viz.s3 import LABEL
    return LABEL[ds]


def profiles() -> list[str]:
    """Profile keys evaluated in v2.1: the profiles kept from v2, then the new one."""
    sc = declared()["v2_1"]["scope"]["profiles"]
    return list(sc["final_from_v2"]) + [sc["new"]]


def split_fractions() -> tuple[float, float]:
    s = declared()["statistics"]["splits"]["measured"]
    return float(s["fitting"]), float(s["held_out"])


def window() -> tuple[int, float]:
    """(L, h) of the recency weighting: L from target.window_length_L, h parsed from 'h = L/4 = 6'."""
    t = declared()["target"]
    L = int(t["window_length_L"]["value"])
    m = re.search(r"h\s*=\s*L\s*/\s*(\d+)\s*=\s*([\d.]+)", t["position_profiles"]["recency"]["value"])
    div, h = int(m.group(1)), float(m.group(2))
    assert abs(L / div - h) < 1e-12, (L, div, h)
    return L, h


def weightings() -> dict:
    """Primary and sensitivity weighting, and whether final-position weighting is scored."""
    d = declared()
    sc = d["v2"]["scope"]
    fp = d["target"]["position_profiles"]["final_position"]
    return {"primary": sc["weightings"]["primary"], "sensitivity": sc["weightings"]["sensitivity"],
            "final_position_scored": not ("superseded_r3" in fp or "final_position_weighting" in sc["dropped"])}


def fidelity_measures() -> list[str]:
    """Measures reported: declared fidelity measures not superseded (D25), then the property table (v2.fidelity.table2)."""
    d = declared()
    f = d["fidelity"]
    keys = [k for k, v in f.items() if isinstance(v, dict) and "superseded_r3" not in v
            and k not in d["v2"]["scope"]["dropped"]]
    order = {"tstr": 0, "covariance_agreement": 1, "discriminator": 3}
    keys = sorted(keys, key=lambda k: order.get(k, 9))
    out = [k for k in keys]
    if "table2" in d["v2"]["fidelity"]:
        out.insert(2, "property_table")
    return out


def measure_label(key: str) -> str:
    return "TSTR" if key == "tstr" else key.replace("_", " ")


def input_sets() -> list[str]:
    """X1 input sets read as results: the declared sets minus the one declared 'sensitivity, not a reading'.
    Cross-checked against the INPUT_SETS constant of the V5/W5 fidelity script (parsed, not executed)."""
    sets = declared()["v2"]["tstr_isolation"]["input_sets"]
    keys = [k for k, v in sets.items() if not str(v).lstrip().lower().startswith("sensitivity")]
    tree = ast.parse(V5_SCRIPT.read_text())
    ran = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "INPUT_SETS" for t in node.targets):
            ran = list(ast.literal_eval(node.value))
    assert ran == keys, (ran, keys)
    return keys


def input_set_label(key: str) -> str:
    return key.replace("_", " ")


def ensemble() -> dict:
    """Identifiability floor: model_init seeds x configurations, parsed from the declared value."""
    v = declared()["usability"]["identifiability_floor"]["value"]
    seeds = [int(s) for s in re.search(r"seeds\s*\[([\d,\s]+)\]", v).group(1).split(",")]
    conf = re.search(r"configurations\s*\{([^}]*)\}", v).group(1)
    configs = dict(re.findall(r"([A-Z]):\s*([^,]+)", conf))
    return {"seeds": seeds, "configurations": configs, "n_members": len(seeds) * len(configs)}


def pattern_channel() -> str:
    ch = declared()["channels"]["roles"]["weighted_pattern_carrying"]
    assert len(ch) == 1
    return ch[0]


def channel_label(c: str) -> str:
    return c.replace("_", " ")


# ---------------------------------------------------------------------------------------------- profiles
@lru_cache(maxsize=None)
def profile_json(ds: str) -> dict:
    path = FORM_PROFILE if ds == FORM_KEY else Path(str(V2_PROFILE).format(ds=ds))
    with open(path) as fh:
        return json.load(fh)


def enabled_pattern_types(ds: str) -> list[str]:
    e6 = profile_json(ds)["estimated_from_data"]["E6_patterns"]
    return [t for t, spec in e6.items() if spec.get("enabled")]


def mappings(ds: str = FORM_KEY) -> dict:
    """Fitted shared mappings phi_c (E3), evaluated exactly as the generator evaluates them."""
    from degradx.fitting.noise_mappings import Mapping
    out = {}
    for c, d in profile_json(ds)["estimated_from_data"]["E3_channel_mappings"].items():
        out[c] = Mapping(c, np.asarray(d["grid"]), np.asarray(d["values"]), bool(d["increasing"]), d["kind"])
    return out


def state_of_fitting_unit(cell_id: str, ds: str = FORM_KEY) -> np.ndarray:
    """z_t of a fitting unit from its fitted theta, by the generator's own state function (the state a generated
    unit drawing this fitting unit receives), truncated at T."""
    from types import SimpleNamespace
    from degradx.generator.generate import _state_from_theta
    p = profile_json(ds)
    e1 = p["estimated_from_data"]["E1_theta_distribution"]
    u = next(x for x in e1["per_unit"] if x["cell_id"] == cell_id)
    ns = SimpleNamespace(family=e1["family"], rho=float(p["declared_used"]["rho"]), q_nom=float(p["declared_used"]["q_nom_Ah"]))
    z, T = _state_from_theta(ns, u, int(3 * u["T"]))
    return z[:T]


# ---------------------------------------------------------------------------------------------- generated units
@lru_cache(maxsize=1)
def form_units() -> list:
    with open(FORM_GENERATED, "rb") as fh:
        units, _ = pickle.load(fh)
    return units


def illustrated_unit():
    """The FORM unit drawn in Figure 2, by a fixed rule on generation seed 0: among units with at least two inserted
    patterns and T within 5 % of the median T of the set, the one whose charge-time offset is largest in absolute
    value (so that the offset is visible); ties broken by unit index."""
    units = form_units()
    T_med = float(np.median([u.T for u in units]))
    off = profile_json(FORM_KEY)["v2"]["offsets_all_fitting_units"]
    cand = [u for u in units if len(u.patterns) >= 2 and abs(u.T - T_med) <= 0.05 * T_med]
    return max(cand, key=lambda u: (abs(off[u.source_unit]["charge_time"]), -u.index)), T_med


def offset_percentile_units(channel: str = "charge_time", qs=(10, 90)) -> list[str]:
    """Fitting units of FORM at the given percentiles (nearest rank) of the offset of `channel` (Figure 3)."""
    off = profile_json(FORM_KEY)["v2"]["offsets_all_fitting_units"]
    keys = sorted(off, key=lambda k: (off[k][channel], k))
    vals = np.array([off[k][channel] for k in keys])
    out = []
    for q in qs:
        v = np.percentile(vals, q, method="nearest")
        out.append(keys[int(np.flatnonzero(vals == v)[0])])
    return out


def save(fig, name: str) -> Path:
    path = IMG / f"{name}.pdf"
    fig.savefig(path)
    return path
