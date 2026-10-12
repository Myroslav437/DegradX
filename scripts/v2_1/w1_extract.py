#!/usr/bin/env python
"""W1 (brief "DegradX v2.1") — extract the declared members (declarations r4 declared_by_design.v2_1.archive.extraction and
.rule) after the member lists and checksums were committed (w1_fetch.py). Members are selected from the committed lists, never
by opening other members:
  * aging files: base name matching ^Nova_Regular_.*\\.json(\\.gz)?$ OR located under a directory named maccor (any case),
    never a base name starting with Nova_Formation; members matched by only one of the two criteria are listed;
  * text metadata that could carry the formation-protocol mapping: README*, *.md, *.txt, and *.csv / *.xlsx / *.json whose base
    name does not start with Nova_;
  * the original (2024) archive contributes an aging file only for a seq the current archive lacks (archive.rule (b)); an
    integrity failure of the current archive is recorded and stops the script for the archive.rule (a) decision.
Safe extraction (tarfile 'data' filter) into new directories data/v2.1/raw/extracted_{current,original}/. Writes
artifacts/v2.1/w1_ingest/tables/extraction_manifest.json (member, archive, criterion, bytes, sha256).
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import tarfile
from pathlib import Path, PurePosixPath

from degradx import ARTIFACTS_V21, DATA_V21, REPO_ROOT

TABLES = ARTIFACTS_V21 / "w1_ingest" / "tables"
AGING_NAME = re.compile(r"^Nova_Regular_.*\.json(\.gz)?$")
SEQ_NAME = re.compile(r"^Nova_Regular_(\d{3})(\.\d+)?\.json(\.gz)?$")
TEXT_META = re.compile(r"^(README.*|.*\.md|.*\.txt)$", re.I)
TABLE_META = re.compile(r".*\.(csv|xlsx|json)$", re.I)


def classify(name: str) -> dict:
    p = PurePosixPath(name)
    base = p.name
    by_name = bool(AGING_NAME.match(base))
    by_dir = any(part.lower() == "maccor" for part in p.parts[:-1])
    aging = (by_name or by_dir) and not base.startswith("Nova_Formation")
    meta = (not aging) and (bool(TEXT_META.match(base)) or (bool(TABLE_META.match(base)) and not base.startswith("Nova_")))
    m = SEQ_NAME.match(base)
    return {"aging": aging, "by_name": by_name, "by_dir": by_dir, "meta": meta, "seq": int(m.group(1)) if m else None, "base": base}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def read_members(tag: str) -> list[dict]:
    with open(TABLES / f"archive_members_{tag}.csv") as f:
        return [r for r in csv.DictReader(f) if r["type"] == "file"]


def main() -> int:
    raw = json.loads((TABLES / "raw_files.json").read_text())
    paths = {a["version"]: REPO_ROOT / a["path"] for a in raw["archives"]}
    plan = {}
    cur = [dict(m, **classify(m["name"])) for m in read_members("current")]
    orig = [dict(m, **classify(m["name"])) for m in read_members("original")]
    cur_seqs = {m["seq"] for m in cur if m["aging"] and m["seq"] is not None}
    plan["current"] = [m for m in cur if m["aging"] or m["meta"]]
    plan["original"] = [m for m in orig if m["aging"] and m["seq"] is not None and m["seq"] not in cur_seqs]
    one_criterion = [{"archive": t, "name": m["name"], "by_name": m["by_name"], "by_dir": m["by_dir"]}
                     for t, ms in (("current", cur), ("original", orig)) for m in ms if m["aging"] and (m["by_name"] != m["by_dir"])]
    manifest = {"rule": "declarations v2_1.archive.extraction / .rule", "matched_by_one_criterion_only": one_criterion,
                "original_used_for_seqs_missing_in_current": sorted({m["seq"] for m in plan["original"]}), "members": []}
    for tag, members in plan.items():
        if not members:
            continue
        dest = DATA_V21 / "raw" / f"extracted_{tag}"
        dest.mkdir(parents=True, exist_ok=True)
        wanted = {m["name"]: m for m in members}
        print(f"[w1-extract] {tag}: {len(wanted)} members to extract", flush=True)
        try:
            with tarfile.open(paths[tag], mode="r|*") as tf:
                for ti in tf:
                    if ti.name not in wanted:
                        continue
                    tf.extract(ti, dest, filter="data")
                    m = wanted[ti.name]
                    fp = dest / ti.name
                    manifest["members"].append({"archive": tag, "name": ti.name, "kind": "aging" if m["aging"] else "metadata", "seq": m["seq"],
                                                "bytes": fp.stat().st_size, "sha256": sha256(fp), "path": str(fp.relative_to(REPO_ROOT))})
                    print(f"[w1-extract] {tag} {ti.name} ({fp.stat().st_size / 1e6:.1f} MB)", flush=True)
        except (tarfile.TarError, OSError, EOFError) as e:          # archive.rule (a): corrupt current archive
            manifest["integrity_failure"] = {"archive": tag, "error": repr(e)}
            (TABLES / "extraction_manifest.json").write_text(json.dumps(manifest, indent=1))
            print(f"[w1-extract] INTEGRITY FAILURE in {tag}: {e!r}", flush=True)
            return 2
    got = {m["name"] for m in manifest["members"]}
    manifest["missing_after_extraction"] = [n for ms in plan.values() for n in (m["name"] for m in ms) if n not in got]
    (TABLES / "extraction_manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"[w1-extract] done: {len(got)} members; missing {len(manifest['missing_after_extraction'])}", flush=True)
    return 0 if not manifest["missing_after_extraction"] else 1


if __name__ == "__main__":
    sys.exit(main())
