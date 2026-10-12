#!/usr/bin/env python
"""W1 helper: print the structure of one BEEP-structured aging file (top-level keys, types, table columns and lengths,
structuring_parameters, writer markers) without converting it. Run with python -I on a path; reads only that file."""
from __future__ import annotations

import gzip
import json
import sys


def describe(v, depth=0):
    pad = "  " * depth
    if isinstance(v, dict):
        keys = list(v.keys())
        if keys and all(isinstance(v[k], list) for k in keys):
            lens = {k: len(v[k]) for k in keys}
            print(f"{pad}table {len(keys)} cols, lengths {set(lens.values())}: {keys}")
            return
        for k in keys:
            x = v[k]
            if isinstance(x, (dict, list)):
                print(f"{pad}{k}: {type(x).__name__} ({len(x)})")
                if depth < 2:
                    describe(x, depth + 1)
            else:
                print(f"{pad}{k}: {x!r}"[:300])
    elif isinstance(v, list) and v:
        print(f"{pad}list of {type(v[0]).__name__}, first: {repr(v[0])[:200]}")


def main(path: str) -> None:
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt") as f:
        d = json.load(f)
    if isinstance(d, str):
        d = json.loads(d)
    print("TOP:", list(d.keys()))
    describe(d)


if __name__ == "__main__":
    main(sys.argv[1])
