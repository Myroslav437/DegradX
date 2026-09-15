"""Shared command-line interface for stage scripts (brief §4).

Every ``scripts/s*.py`` builds its parser with ``stage_parser`` so the flags ``--config``,
``--out-dir``, ``--seed``, ``--device``, ``--dry-run`` and ``--force`` behave identically, and
uses ``StageContext`` for skip-if-done logic and run provenance.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path

from degradx import ARTIFACTS_DIR, CONFIG_DIR
from degradx.utils.config import load_declarations, load_stage_config
from degradx.utils.device import default_device, resolve_device


def stage_parser(description: str, stage_dir: str, default_seed: int = 20260915) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=description, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--config", type=Path, default=CONFIG_DIR / "stages" / f"{stage_dir}.yaml",
                   help="stage run config (YAML); declared constants come from configs/declarations.yaml")
    p.add_argument("--out-dir", type=Path, default=ARTIFACTS_DIR / stage_dir, help="artifact directory for this stage")
    p.add_argument("--seed", type=int, default=default_seed, help="base seed; per-source seeds are derived from it")
    p.add_argument("--device", choices=["cuda", "cpu"], default=default_device(), help="compute device")
    p.add_argument("--dry-run", action="store_true", help="print the plan and exit without computing")
    p.add_argument("--force", action="store_true", help="recompute outputs that already exist")
    return p


@dataclass
class StageContext:
    args: argparse.Namespace
    config: dict
    declarations: dict
    device: str
    out_dir: Path
    skipped: list[str] = field(default_factory=list)

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "StageContext":
        cfg = load_stage_config(args.config) if Path(args.config).exists() else {}
        out = Path(args.out_dir)
        for sub in ("figures", "tables", "logs"):
            (out / sub).mkdir(parents=True, exist_ok=True)
        return cls(args=args, config=cfg, declarations=load_declarations(), device=resolve_device(args.device), out_dir=out)

    def should_skip(self, *outputs: Path, label: str) -> bool:
        """True when every output exists and --force was not given; records the skip."""
        if self.args.force:
            return False
        if outputs and all(Path(o).exists() for o in outputs):
            self.skipped.append(label)
            print(f"[skip] {label}: outputs exist ({', '.join(str(o) for o in outputs)}); use --force to recompute")
            return True
        return False
