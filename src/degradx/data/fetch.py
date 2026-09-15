"""Raw-data acquisition and verification (brief S1: idempotent, resumable, checksummed).

MATR and HUST are downloaded with BatteryML's own ``batteryml download`` (its ``DOWNLOAD_LINKS``); NASA
PCoE is not in BatteryML and is fetched from the NASA repository's S3 link. Every file is verified
against a published or previously recorded size and, where one exists, SHA-256. When a download cannot
run (network, a portal that requires a browser), ``manual_instructions`` prints the exact file tree a
human has to place under ``data/raw/``.

Expected sizes and hashes come from docs/S0_RESEARCH/datasets.md: MATR sizes from the data.matr.io
Girder API; HUST size and SHA-256 from the Mendeley Data API; NASA size from the S3 HEAD and SHA-256
from the S0 download. MATR has no published hash; its SHA-256 is recorded at first verification into
``configs/raw_checksums.sha256`` and checked on every later run.
"""

from __future__ import annotations

import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from degradx import CONFIG_DIR
from degradx.utils.io import sha256_file


@dataclass(frozen=True)
class RawFile:
    dataset: str
    name: str
    size: int
    sha256: str | None
    source: str


RAW_FILES = [
    RawFile("MATR", "MATR_batch_20170512.mat", 3025320241, None, "batteryml download MATR (data.matr.io file 5c86c0b5fa2ede00015ddf66)"),
    RawFile("MATR", "MATR_batch_20170630.mat", 2007331155, None, "batteryml download MATR (data.matr.io file 5c86bf13fa2ede00015ddd82)"),
    RawFile("MATR", "MATR_batch_20180412.mat", 3236690412, None, "batteryml download MATR (data.matr.io file 5c86bd64fa2ede00015ddbb2)"),
    RawFile("MATR", "MATR_batch_20190124.mat", 2601295745, None, "batteryml download MATR (data.matr.io file 5dcef152110002c7215b2c90)"),
    RawFile("HUST", "hust_data.zip", 1188136932, "071d24617153693b0d29059568525e620f6af6512acc9d00c98c7adcf15125db",
            "batteryml download HUST (Mendeley Data nsc7hnsg4s v2, our_data.zip)"),
    RawFile("NASA_PCoE", "5.Battery_Data_Set.zip", 209708670, "82302a7db4fc1b34e0b6676326610438d43b816bdf11a69d1d012a464ef2f92e",
            "https://phm-datasets.s3.amazonaws.com/NASA/5.+Battery+Data+Set.zip"),
]
NASA_URL = "https://phm-datasets.s3.amazonaws.com/NASA/5.+Battery+Data+Set.zip"


def read_checksums(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text().splitlines():
        if line.strip():
            digest, name = line.split(maxsplit=1)
            out[name.strip()] = digest
    return out


def write_checksums(path: Path, sums: dict[str, str]) -> None:
    path.write_text("".join(f"{d}  {n}\n" for n, d in sorted(sums.items())))


def download(raw_root: Path, dataset: str) -> None:
    target = raw_root / dataset
    target.mkdir(parents=True, exist_ok=True)
    if dataset in ("MATR", "HUST"):
        subprocess.run([str(Path(sys.executable).with_name("batteryml")), "download", dataset, str(target)], check=True)
    elif dataset == "NASA_PCoE":
        tmp = target / "5.Battery_Data_Set.zip.part"
        urllib.request.urlretrieve(NASA_URL, tmp)
        tmp.rename(target / "5.Battery_Data_Set.zip")


def manual_instructions(raw_root: Path) -> str:
    lines = ["Place the following files exactly as shown (sizes in bytes), then re-run scripts/s1_fetch_data.py:"]
    for f in RAW_FILES:
        lines.append(f"  {raw_root / f.dataset / f.name}   size={f.size}   from: {f.source}")
    return "\n".join(lines)


def verify(raw_root: Path, try_download: bool = True, rehash: bool = False) -> list[dict]:
    """Check presence, size and SHA-256 of every raw file; download missing ones when allowed."""
    sums_path = CONFIG_DIR / "raw_checksums.sha256"  # committed: the fetch script plus these hashes reproduce data/raw
    recorded = read_checksums(sums_path)
    rows = []
    for f in RAW_FILES:
        path = raw_root / f.dataset / f.name
        key = f"{f.dataset}/{f.name}"
        if not path.exists() and try_download:
            try:
                download(raw_root, f.dataset)
            except Exception as exc:  # network or portal failure: report, do not guess
                print(f"[manual] download of {key} failed: {exc!r}")
        if not path.exists():
            rows.append({"file": key, "present": False, "size_ok": False, "sha256_ok": False, "sha256": None, "hash_source": None})
            continue
        size_ok = path.stat().st_size == f.size
        if key in recorded and not rehash:
            digest = recorded[key]  # hashed at an earlier verification of the same-size file
            hash_source = "recorded configs/raw_checksums.sha256"
        else:
            print(f"[hash] {key} ...")
            digest = sha256_file(path)
            hash_source = "computed"
        if f.sha256 is not None:
            sha_ok = digest == f.sha256
            ref = "published/S0"
        else:
            sha_ok = recorded.get(key, digest) == digest
            ref = "first verification (no published hash)"
        recorded[key] = digest
        rows.append({"file": key, "present": True, "bytes": path.stat().st_size, "expected_bytes": f.size, "size_ok": size_ok,
                     "sha256": digest, "sha256_reference": ref, "hash_source": hash_source, "sha256_ok": sha_ok})
    write_checksums(sums_path, recorded)
    return rows
