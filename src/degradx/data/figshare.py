"""Download of a public figshare article's files with checksums (v2 third profile, X6: "ingest from the primary release;
record checksums for every raw file").

Files are listed through the public API (``https://api.figshare.com/v2/articles/<id>/files``), streamed to disk with
resume (HTTP Range) and verified against the API's ``supplied_md5``/``computed_md5``; a SHA-256 of every file is recorded
for the repository's checksum list. Nothing is extracted here.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from pathlib import Path

API = "https://api.figshare.com/v2/articles/{id}/files?page_size=100"


def list_files(article_id: int) -> list[dict]:
    with urllib.request.urlopen(API.format(id=article_id), timeout=60) as r:
        return json.loads(r.read().decode())


def _md5_sha256(path: Path, chunk: int = 1 << 22) -> tuple[str, str]:
    m, s = hashlib.md5(), hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            m.update(b)
            s.update(b)
    return m.hexdigest(), s.hexdigest()


def download(f: dict, dest_dir: Path, retries: int = 20, log=print) -> dict:
    """Stream one file with resume; verify md5; return {name, size, md5, sha256, url}."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f["name"]
    expected_md5 = f.get("supplied_md5") or f.get("computed_md5")
    size = int(f["size"])
    if path.exists() and path.stat().st_size == size:
        md5, sha = _md5_sha256(path)
        if md5 == expected_md5:
            return {"name": f["name"], "size": size, "md5": md5, "sha256": sha, "url": f["download_url"], "status": "present"}
    part = path.with_suffix(path.suffix + ".part")
    for attempt in range(retries):
        have = part.stat().st_size if part.exists() else 0
        if have >= size:
            break
        req = urllib.request.Request(f["download_url"], headers={"Range": f"bytes={have}-", "User-Agent": "degradx-v2-ingest"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r, open(part, "ab") as out:
                t0, got = time.time(), 0
                while True:
                    b = r.read(1 << 22)
                    if not b:
                        break
                    out.write(b)
                    got += len(b)
                    if got % (1 << 30) < (1 << 22):
                        log(f"[fetch] {f['name']}: {(have + got) / 1e9:.2f} / {size / 1e9:.2f} GB ({got / max(1e-9, time.time() - t0) / 1e6:.1f} MB/s)")
        except Exception as exc:  # network hiccup: resume from what is on disk
            log(f"[fetch] {f['name']}: attempt {attempt + 1} interrupted ({exc!r}); resuming")
            time.sleep(min(60, 5 * (attempt + 1)))
    if not part.exists() or part.stat().st_size != size:
        raise RuntimeError(f"{f['name']}: incomplete download")
    md5, sha = _md5_sha256(part)
    if md5 != expected_md5:
        raise RuntimeError(f"{f['name']}: md5 {md5} != published {expected_md5}")
    part.rename(path)
    return {"name": f["name"], "size": size, "md5": md5, "sha256": sha, "url": f["download_url"], "status": "downloaded"}
