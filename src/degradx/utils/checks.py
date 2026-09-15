"""Pre-declared sanity checks with a table for REVIEW.md (brief §5, §6).

A stage states what it expects before running, records what it observed, and exits non-zero
if any check failed. ``CheckTable.require`` records a check; ``finalize`` writes
``tables/checks.{csv,json}`` and returns the process exit code.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from degradx.utils.io import write_json


@dataclass
class Check:
    name: str
    expected: str
    observed: str
    passed: bool
    severity: str = "error"  # "error" fails the stage; "warn" is reported only


class CheckTable:
    def __init__(self) -> None:
        self.checks: list[Check] = []

    def require(self, name: str, passed: bool, expected: Any, observed: Any, severity: str = "error") -> bool:
        self.checks.append(Check(name, str(expected), str(observed), bool(passed), severity))
        return bool(passed)

    @property
    def failed(self) -> list[Check]:
        return [c for c in self.checks if not c.passed and c.severity == "error"]

    def markdown(self) -> str:
        lines = ["| check | expected | observed | result |", "|---|---|---|---|"]
        for c in self.checks:
            res = "pass" if c.passed else ("FAIL" if c.severity == "error" else "warn")
            lines.append(f"| {c.name} | {c.expected} | {c.observed} | {res} |")
        return "\n".join(lines)

    def finalize(self, out_dir: Path) -> int:
        import csv

        tables = Path(out_dir) / "tables"
        tables.mkdir(parents=True, exist_ok=True)
        rows = [asdict(c) for c in self.checks]
        write_json(rows, tables / "checks.json")
        with open(tables / "checks.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["name", "expected", "observed", "passed", "severity"])
            w.writeheader()
            w.writerows(rows)
        for c in self.checks:
            tag = "PASS" if c.passed else ("FAIL" if c.severity == "error" else "WARN")
            print(f"[{tag}] {c.name}: expected {c.expected}; observed {c.observed}")
        return 1 if self.failed else 0
