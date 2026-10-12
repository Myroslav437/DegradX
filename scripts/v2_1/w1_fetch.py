#!/usr/bin/env python
"""W1 (brief "DegradX v2.1") — fetch both archives of the TRI/Stanford formation dataset (declarations r4
declared_by_design.v2_1.archive) into their own empty directories, then record each archive's byte size, SHA-256 and full
member list (name, size, type) BEFORE any member is opened, and fetch the pinned formation-protocol sheet
(v2_1.formation_mapping). Nothing is extracted here.

Outputs: data/v2.1/raw/{archive_current,archive_original,formation_mapping}/ (gitignored),
configs/raw_checksums_v2_1.sha256, artifacts/v2.1/w1_ingest/tables/archive_members_<version>.csv and
artifacts/v2.1/w1_ingest/tables/raw_files.json.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import time
from email.utils import parsedate_to_datetime
from pathlib import Path

from degradx import ARTIFACTS_V21, CONFIG_DIR, DATA_V21, REPO_ROOT
from degradx.utils.config import load_declarations

OUT = ARTIFACTS_V21 / "w1_ingest" / "tables"
SHEET_URL = "https://raw.githubusercontent.com/cx26/formation-analysis/{commit}/data/Formation_2022-Parameter.csv"
NOTES_URL = ("https://raw.githubusercontent.com/JinwookRhyu/Systematic_Feature_Design_Framework_Formation/"
             "9530854b76f83f5cd85ad66d7e273c86dc8ea437/tsfresh_feature_extraction/Formation_2022_Parameter.csv")
NOTES_SHA = "8d824556b10a92c414e8fd15d7cd351ae731e96810d1fd2ae6c7aac936788cbe"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def fetch(url: str, dest: Path, headers: Path | None = None) -> dict:
    """Resumable GET with retries; returns the final response's headers (lower-cased names)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["curl", "-L", "--fail", "--retry", "10", "--retry-delay", "5", "-C", "-", "-o", str(dest)]
    if headers is not None:
        cmd += ["-D", str(headers)]
    subprocess.run(cmd + [url], check=True)
    return parse_headers(headers) if headers is not None else {}


def parse_headers(p: Path) -> dict:
    """Headers of the last response block in a curl -D dump."""
    blocks = [b for b in p.read_text(errors="replace").replace("\r", "").split("\n\n") if b.strip()]
    out = {}
    for line in blocks[-1].splitlines()[1:] if blocks else []:
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out


def head(url: str) -> dict:
    r = subprocess.run(["curl", "-sIL", "--fail", url], check=True, capture_output=True, text=True)
    blocks = [b for b in r.stdout.replace("\r", "").split("\n\n") if b.strip()]
    out = {}
    for line in blocks[-1].splitlines()[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out


def members(p: Path) -> list[dict]:
    rows = []
    with tarfile.open(p, mode="r|*") as tf:      # streaming: headers only, no member data is read
        for m in tf:
            rows.append({"name": m.name, "size": m.size, "type": "dir" if m.isdir() else ("file" if m.isfile() else "other")})
    return rows


def main() -> int:
    from degradx.utils.config import load_yaml

    dd = load_declarations()["declared_by_design"]["v2_1"]
    arch = dd["archive"]
    fm = load_yaml(CONFIG_DIR / "profiles" / "tri_formation.yaml")["formation_mapping"]
    free = shutil.disk_usage(DATA_V21.parent if DATA_V21.parent.exists() else REPO_ROOT).free
    need = arch["primary"]["head_2026_10_11"]["bytes"] + arch["original"]["head_2026_10_11"]["bytes"]
    print(f"[w1] free disk {free / 1e9:.1f} GB; archives {need / 1e9:.1f} GB (+ extraction)", flush=True)
    if free < 3 * need:
        print("[w1] STOP: not enough disk for archives plus extraction (brief v2.1 §5)", flush=True)
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    recs = []
    for version in ("primary", "original"):
        a = arch[version]
        want = a["head_2026_10_11"]
        d = DATA_V21 / "raw" / ("archive_current" if version == "primary" else "archive_original")
        dest = d / Path(a["url"]).name
        hdr = d.parent / f"{d.name}_get_headers.txt"
        t0 = time.time()
        h_now = head(a["url"])
        print(f"[w1] HEAD {a['url']}: {h_now.get('content-length')} {h_now.get('last-modified')} {h_now.get('etag')}", flush=True)
        got = {}
        for attempt in (1, 2):           # archive.integrity: a byte-size mismatch is re-downloaded once
            if not (dest.exists() and dest.stat().st_size == want["bytes"]):
                got = fetch(a["url"], dest, hdr)
            elif hdr.exists():
                got = parse_headers(hdr)
            if dest.stat().st_size == want["bytes"]:
                break
            print(f"[w1] size mismatch ({dest.stat().st_size} != {want['bytes']}), attempt {attempt}", flush=True)
            dest.unlink()
        size = dest.stat().st_size if dest.exists() else -1
        etag = (got.get("etag") or h_now.get("etag") or "").strip('"')
        lm = got.get("last-modified") or h_now.get("last-modified") or ""
        lm_norm = parsedate_to_datetime(lm).strftime("%Y-%m-%d %H:%M:%S GMT") if lm else ""
        match = size == want["bytes"] and etag == want["etag"] and lm_norm == want["last_modified"]
        tag = "current" if version == "primary" else "original"
        rec = {"version": tag, "url": a["url"], "path": str(dest.relative_to(REPO_ROOT)), "bytes": size, "bytes_head": want["bytes"],
               "etag": etag, "etag_declared": want["etag"], "last_modified": lm, "last_modified_declared": want["last_modified"],
               "s3_version_id": got.get("x-amz-version-id") or h_now.get("x-amz-version-id"), "matches_declared_head": bool(match)}
        if not match:
            recs.append(rec)
            print(f"[w1] STOP: {tag} archive does not match its declared HEAD values (archive.integrity): {json.dumps(rec)}", flush=True)
            (OUT / "raw_files.json").write_text(json.dumps({"archives": recs, "stop": "archive.integrity"}, indent=1))
            return 3
        rec["sha256"] = sha256(dest)
        rows = members(dest)
        with open(OUT / f"archive_members_{tag}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["name", "size", "type"])
            w.writeheader()
            w.writerows(rows)
        rec.update({"members": len(rows), "files": sum(r["type"] == "file" for r in rows), "recorded_unix": time.time(),
                    "seconds": round(time.time() - t0, 1)})
        recs.append(rec)
        print(f"[w1] {json.dumps(rec)}", flush=True)
    # pinned formation-protocol sheet (never committed) and the notes copy
    sheets = []
    for name, url, want in (("Formation_2022-Parameter.csv", SHEET_URL.format(commit=fm["commit"]), fm["sha256"]),
                            ("Formation_2022_Parameter_rhyu.csv", NOTES_URL, NOTES_SHA)):
        dest = DATA_V21 / "raw" / "formation_mapping" / name
        if not dest.exists():
            fetch(url, dest)
        got = sha256(dest)
        sheets.append({"name": name, "url": url, "sha256": got, "expected": want, "match": got == want})
        print(f"[w1] {name}: sha256 {'OK' if got == want else 'MISMATCH ' + got}", flush=True)
    (OUT / "raw_files.json").write_text(json.dumps({"archives": recs, "formation_mapping": sheets}, indent=1))
    (CONFIG_DIR / "raw_checksums_v2_1.sha256").write_text(
        "".join(f"{r['sha256']}  {r['path']}\n" for r in recs)
        + "".join(f"{s['sha256']}  data/v2.1/raw/formation_mapping/{s['name']}\n" for s in sheets))
    return 0 if all(s["match"] for s in sheets) else 1


if __name__ == "__main__":
    sys.exit(main())
