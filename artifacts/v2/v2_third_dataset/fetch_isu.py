"""V2 fetch: every file of the ISU-ILCC figshare article (v2), smallest first, verified against the published md5;
SHA-256 recorded (configs/raw_checksums_v2.sha256 and artifacts/v2/v2_third_dataset/tables/raw_files.json)."""
import json, sys
from pathlib import Path
from degradx import DATA_V2, CONFIG_DIR, ARTIFACTS_V2
from degradx.data.figshare import list_files, download

dest = DATA_V2 / "raw" / "isu_ilcc"
files = sorted(list_files(22582234), key=lambda f: int(f["size"]))
print(json.dumps([(f["name"], f["size"]) for f in files]), flush=True)
recs = []
for f in files:
    recs.append(download(f, dest))
    print(recs[-1], flush=True)
    out = ARTIFACTS_V2 / "v2_third_dataset" / "tables"
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw_files.json").write_text(json.dumps({"article": 22582234, "version": "v2", "files": recs}, indent=1))
(CONFIG_DIR / "raw_checksums_v2.sha256").write_text("".join(f"{r['sha256']}  data/v2/raw/isu_ilcc/{r['name']}\n" for r in recs))
print("done", flush=True)
