#!/usr/bin/env python
"""S1 — data acquisition: fetch, verify, ingest into BatteryML BatteryData, derive per-cycle channels.

Inputs: ``data/raw/{MATR,HUST,NASA_PCoE}`` (downloaded here if absent: MATR/HUST via ``batteryml download``,
NASA from its S3 link; a failed download prints the exact file tree to place by hand). Outputs:
``configs/raw_checksums.sha256``; ``data/processed/<dataset>/*.pkl`` (BatteryData: MATR through BatteryML's own
functions one batch per process, HUST through the BatteryML CLI plus the cycler capacity, NASA through
``degradx.data.nasa``); ``data/processed/cycle_tables/<dataset>.csv.gz`` (one row per stored cycle);
``artifacts/s1_fetch_data/{tables,figures,logs}``. Checks compare unit counts and cycle counts with each
dataset's own documentation (configs/reference_facts/), cell-id uniqueness, monotone cycle indices and units.
No cell is dropped here; exclusions belong to the S2 audit. Exits non-zero if a check fails.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from degradx import CONFIG_DIR, DATA_DIR, REPO_ROOT
from degradx.utils.checks import CheckTable
from degradx.utils.cli import StageContext, stage_parser
from degradx.utils.io import save_figure, save_table, write_json
from degradx.utils.provenance import RunRecord

RAW, PROC, WORK = DATA_DIR / "raw", DATA_DIR / "processed", DATA_DIR / "work"
TABLES = PROC / "cycle_tables"
REF = CONFIG_DIR / "reference_facts"
DATASETS = {"MATR": "MATR_*.pkl", "HUST": "HUST_*.pkl", "NASA_PCoE": "NASA_*.pkl"}
CHANNELS = ["capacity_cycler_Ah", "capacity_integrated_Ah", "charge_time_min", "mean_discharge_voltage_V",
            "internal_resistance_ohm", "temperature_mean_C"]

# MATR documentation facts (docs/S0_RESEARCH/datasets.md §1.3-1.4, §1.8; configs/reference_facts/matr_probe_summary.txt)
MATR_ENTRIES = {"2017-05-12": 38811, "2017-06-30": 24920, "2018-04-12": 51007, "2019-01-24": 39673}
MATR_CELLS_IN_FILE = {"2017-05-12": 46, "2017-06-30": 48, "2018-04-12": 46, "2019-01-24": 45}
MATR_CARRY_ENTRIES = 662 + 981 + 1060 + 208 + 482
MATR_MERGED = {"MATR_b1c0": 1851, "MATR_b1c1": 2159, "MATR_b1c2": 2236, "MATR_b1c3": 1433, "MATR_b1c4": 1708}


def ingest(ctx) -> dict:
    from degradx.data import hust, matr, nasa

    logs = {}
    for d in DATASETS:
        (PROC / d).mkdir(parents=True, exist_ok=True)
    logs["matr"] = matr.ingest(RAW / "MATR", PROC / "MATR", WORK, force=ctx.args.force)
    if len(list((PROC / "HUST").glob("HUST_*.pkl"))) < 77 or ctx.args.force:
        subprocess.run([str(Path(sys.executable).with_name("batteryml")), "preprocess", "HUST", str(RAW / "HUST"), str(PROC / "HUST")],
                       check=True)
    else:
        print("[skip] HUST BatteryML preprocess: 77 pickles exist")
    logs["hust"] = hust.augment(RAW / "HUST", PROC / "HUST", force=ctx.args.force)
    logs["nasa"] = nasa.ingest(RAW / "NASA_PCoE", PROC / "NASA_PCoE", WORK, force=ctx.args.force)
    return logs


def channel_tables(ctx) -> dict[str, pd.DataFrame]:
    from degradx.data.channels import dataset_table

    TABLES.mkdir(parents=True, exist_ok=True)
    out = {}
    for d, pattern in DATASETS.items():
        path = TABLES / f"{d}.csv.gz"
        if ctx.should_skip(path, label=f"cycle table {d}"):
            out[d] = pd.read_csv(path)
            continue
        df = dataset_table(PROC / d, pattern, workers=ctx.args.workers)
        df.to_csv(path, index=False)
        out[d] = df
    return out


def nasa_reference() -> pd.DataFrame:
    rows = [json.loads(line) for line in (REF / "nasa_inspect_out.txt").read_text().splitlines() if line.startswith("{")]
    return pd.DataFrame(rows)[["cell", "n_discharge"]]


def converter_validation(ct: CheckTable, fig_dir: Path) -> dict:
    """NASA BatteryData against BatteryML-produced objects (fields, types, ordering, units) and the raw file."""
    import scipy.io
    from batteryml import BatteryData

    from degradx.viz import s1 as viz

    ref_objs = {d: BatteryData.load(sorted((PROC / d).glob(p))[0]) for d, p in (("MATR", "MATR_*.pkl"), ("HUST", "HUST_*.pkl"))}
    nasa_obj = BatteryData.load(PROC / "NASA_PCoE" / "NASA_B0005.pkl")
    out = {}
    base_keys = set(BatteryData("x", cycle_data=[]).to_dict().keys())
    for d, ref in ref_objs.items():
        rk = set(ref.to_dict().keys()) & base_keys
        nk = set(nasa_obj.to_dict().keys())
        ct.require(f"NASA BatteryData carries every BatteryData field present in {d}", rk <= nk, sorted(rk), f"missing {sorted(rk - nk)}")
        rc = set(ref.cycle_data[0].to_dict().keys())
        nc = set(nasa_obj.cycle_data[0].to_dict().keys())
        core = {"cycle_number", "voltage_in_V", "current_in_A", "charge_capacity_in_Ah", "discharge_capacity_in_Ah", "time_in_s",
                "temperature_in_C", "internal_resistance_in_ohm"}
        ct.require(f"NASA CycleData has the core CycleData fields of {d}", (rc & core) <= nc, sorted(rc & core), f"missing {sorted((rc & core) - nc)}")
    cd = nasa_obj.cycle_data
    ct.require("NASA cycle_number strictly increasing from 1", [c.cycle_number for c in cd] == list(range(1, len(cd) + 1)), "1..N", f"1..{len(cd)}")
    types_ok = all(isinstance(cd[0].voltage_in_V, list) and isinstance(cd[0].voltage_in_V[0], float) for _ in [0])
    ct.require("NASA series stored as list[float] like BatteryML", types_ok, "list[float]", type(cd[0].voltage_in_V[0]).__name__)
    mono = all(np.all(np.diff(np.asarray(c.time_in_s)) >= 0) for c in cd)
    ct.require("NASA time_in_s non-decreasing within every cycle", mono, "True", mono)
    # raw file comparison for B0005
    ops = scipy.io.loadmat(WORK / "nasa_mat" / "B0005.mat", simplify_cells=True)["B0005"]["cycle"]
    dis = [o for o in ops if o["type"] == "discharge"]
    raw_first = dis[0]["data"]
    n_d = len(raw_first["Time"])
    max_err = max(float(np.max(np.abs(np.asarray(getattr(cd[0], a))[-n_d:] - np.asarray(raw_first[k]))))
                  for a, k in (("voltage_in_V", "Voltage_measured"), ("current_in_A", "Current_measured"), ("temperature_in_C", "Temperature_measured")))
    ct.require("NASA B0005 first discharge: converted V/I/T equal raw arrays", max_err == 0.0, "max abs diff 0", max_err)
    raw_caps = np.array([float(o["data"]["Capacity"]) for o in dis])
    conv_caps = np.array([c.additional_data["capacity_cycler_Ah"] for c in cd])
    ct.require("NASA B0005 capacity_cycler_Ah equals raw Capacity for every discharge", np.array_equal(raw_caps, conv_caps), "equal", f"max diff {np.max(np.abs(raw_caps - conv_caps))}")
    integ = np.array([max(c.discharge_capacity_in_Ah) for c in cd])
    out["nasa_B0005_integrated_minus_raw_capacity_mAh_median"] = float(np.median(integ - raw_caps) * 1000)
    fig = viz.nasa_converter_check(raw_first, cd[0], raw_caps, conv_caps, "B0005")
    save_figure(fig, fig_dir / "nasa_converter_vs_raw_B0005")
    return out


def run_checks(ct: CheckTable, tables: dict[str, pd.DataFrame], logs: dict) -> dict:
    summary = {}
    all_ids = pd.concat([t["cell_id"].drop_duplicates() for t in tables.values()])
    ct.require("no duplicate cell ids across datasets", all_ids.is_unique, "unique", f"{len(all_ids)} ids, unique={all_ids.is_unique}")
    for d, df in tables.items():
        mono = df.groupby("cell_id")["cycle_number"].apply(lambda s: bool(np.all(np.diff(s.to_numpy()) > 0))).all()
        ct.require(f"{d}: cycle_number strictly increasing within every cell", mono, True, mono)
        nd = df[~df["degenerate"]]
        q = df["nominal_capacity_Ah"].iloc[0]
        # Units: a unit error shifts the whole distribution, a glitch does not. Error-level: the median cycle lies inside
        # the physical range and >= 99% of cycles with finite values do. Reported (warn): every finite cycle inside the
        # range, and the number of cycles whose raw series contain NaN. History of this check: artifacts/s1_fetch_data/REVIEW.md.
        vmax_i = np.maximum(nd["i_min"].abs(), nd["i_max"].abs())
        rng_checks = [("voltage within 1.5-4.5 V", nd["v_min"], nd["v_max"], 1.5, 4.5),
                      ("|current| <= 10 C", vmax_i, vmax_i, 0.0, 10 * q),
                      ("cycler capacity within [0, 1.5 x nominal] Ah", nd["capacity_cycler_Ah"], nd["capacity_cycler_Ah"], 0.0, 1.5 * q)]
        if nd["t_min_C"].notna().any():
            rng_checks.append(("temperature within -5..80 degC", nd["t_min_C"], nd["t_max_C"], -5.0, 80.0))
        for label, lo_s, hi_s, lo, hi in rng_checks:
            finite = lo_s.notna() & hi_s.notna()
            ok = (lo_s[finite] >= lo) & (hi_s[finite] <= hi)
            med_ok = bool(lo <= lo_s[finite].median() and hi_s[finite].median() <= hi)
            frac = float(ok.mean())
            ct.require(f"{d}: units plausible, median cycle and >= 99% of cycles with {label}", med_ok and frac >= 0.99, "median inside, >= 0.99",
                       f"median inside={med_ok}, fraction {frac:.5f}")
            ct.require(f"{d}: every finite cycle has {label}", bool(ok.all()), "all cycles",
                       f"{int((~ok).sum())} cycles in {nd.loc[finite].loc[~ok, 'cell_id'].nunique()} cells outside; {int((~finite).sum())} cycles with NaN samples", severity="warn")
            summary[f"{d}_cycles_outside_{label}"] = {"cycles": int((~ok).sum()), "cells": int(nd.loc[finite].loc[~ok, "cell_id"].nunique()),
                                                     "cycles_with_nan_samples": int((~finite).sum())}
        med_dur = float(nd["duration_s"].median())
        exp = {"MATR": (1800, 7200), "HUST": (1800, 14400), "NASA_PCoE": (3600, 86400)}[d]
        ct.require(f"{d}: median cycle duration in seconds within documented range", exp[0] <= med_dur <= exp[1], f"{exp} s", f"{med_dur:.0f} s")
        ct.require(f"{d}: time non-decreasing within cycles", float(nd["frac_negative_dt"].max()) == 0.0, "0 negative steps",
                   f"max fraction {nd['frac_negative_dt'].max():.2e}", severity="warn")
        diff = (nd["capacity_integrated_Ah"] - nd["capacity_cycler_Ah"]) * 1000
        summary[f"{d}_integrated_minus_cycler_mAh"] = {"median": float(diff.median()), "p05": float(diff.quantile(0.05)),
                                                       "p95": float(diff.quantile(0.95))}
        summary[f"{d}_units"] = int(df["cell_id"].nunique())
        summary[f"{d}_cycles"] = int(len(df))
        summary[f"{d}_cycles_per_unit"] = {"min": int(df.groupby("cell_id").size().min()), "median": float(df.groupby("cell_id").size().median()),
                                           "max": int(df.groupby("cell_id").size().max())}
        summary[f"{d}_degenerate_cycles"] = int(df["degenerate"].sum())

    # ---- MATR against documentation
    m = tables["MATR"]
    per = m.groupby("cell_id").agg(n=("position", "size"), batch=("batch", "first")).reset_index()
    dropped = {c["cell_id"]: c["dropped_placeholder_cycles"] for rec in logs["matr"] for c in rec["cells"]}
    per["dropped"] = per["cell_id"].map(dropped)
    ct.require("MATR: 180 unique cells (BatteryML convention)", len(per) == 180, 180, len(per))
    ct.require("MATR: carry-over keys b2c7/8/9/15/16 not emitted", not per["cell_id"].isin([f"MATR_{k}" for k in ("b2c7", "b2c8", "b2c9", "b2c15", "b2c16")]).any(), "absent", "absent")
    for date, cells in MATR_CELLS_IN_FILE.items():
        n_cells = int((per["batch"] == date).sum())
        expected_cells = cells - (5 if date == "2017-06-30" else 0)
        ct.require(f"MATR {date}: cells emitted", n_cells == expected_cells, expected_cells, n_cells)
        stored = int((per.loc[per["batch"] == date, "n"] + per.loc[per["batch"] == date, "dropped"] + 1).sum())
        expected = MATR_ENTRIES[date] + (MATR_CARRY_ENTRIES if date == "2017-05-12" else 0) - (MATR_CARRY_ENTRIES if date == "2017-06-30" else 0)
        # merged cells skip index 0 once, as BatteryML does; the carry-over segment's index 0 is either stored or dropped
        ct.require(f"MATR {date}: stored + dropped + skipped index 0 equals file cycle entries", stored == expected, expected, stored)
    merged = per.set_index("cell_id").loc[list(MATR_MERGED)]
    ok = all(int(merged.at[c, "n"] + merged.at[c, "dropped"] + 1) == MATR_MERGED[c] for c in MATR_MERGED)
    ct.require("MATR merged b1c0..4 lengths equal merged entries", ok, MATR_MERGED, {c: int(merged.at[c, "n"] + merged.at[c, "dropped"] + 1) for c in MATR_MERGED})
    summary["MATR_dropped_placeholder_cycles"] = {k: v for k, v in dropped.items() if v}
    # ---- HUST against ESI Table S1
    h = tables["HUST"]
    ref = pd.read_csv(REF / "hust_tableS1.csv")
    hn = h.groupby("cell_id").size()
    ids = sorted(c.split("_", 1)[1] for c in hn.index)
    ct.require("HUST: 77 cells equal to ESI Table S1 channels", ids == sorted(ref["channel"]), "Table S1 channels", f"{len(ids)} cells; diff {sorted(set(ids) ^ set(ref['channel']))}")
    exp_n = ref.set_index("channel")["cycle_life"].copy()
    exp_n.loc["7-5"] -= 2  # BatteryML skips the first two cycles of 7-5
    obs_n = hn.rename(lambda c: c.split("_", 1)[1])
    mism = {c: (int(exp_n[c]), int(obs_n.get(c, -1))) for c in exp_n.index if int(obs_n.get(c, -1)) != int(exp_n[c])}
    ct.require("HUST: per-cell cycle counts equal Table S1 cycle life (7-5 minus 2)", not mism, "0 mismatches", mism or "0 mismatches")
    ct.require("HUST: total stored cycles = 146,120", int(hn.sum()) == 146120, 146120, int(hn.sum()))
    ct.require("HUST: cycler capacity attached to every cycle", int(h["capacity_cycler_Ah"].isna().sum()) == 0, 0, int(h["capacity_cycler_Ah"].isna().sum()))
    # ---- NASA against the S0 scan of the repository files
    nref = nasa_reference().set_index("cell")["n_discharge"]
    nobs = tables["NASA_PCoE"].groupby("cell_id").size().rename(lambda c: c.split("_", 1)[1])
    mism = {c: (int(nref[c]), int(nobs.get(c, -1))) for c in nref.index if int(nobs.get(c, -1)) != int(nref[c])}
    ct.require("NASA: 34 unique cells", len(nobs) == 34 and set(nobs.index) == set(nref.index), 34, len(nobs))
    ct.require("NASA: one cycle per discharge operation (counts equal the file scan)", not mism, "0 mismatches", mism or "0 mismatches")
    return summary


def availability(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    cols = {}
    for d, df in tables.items():
        per = df[~df["degenerate"]].groupby("cell_id")[CHANNELS].apply(lambda g: g.notna().mean() > 0.5)
        cols[d] = per.mean()
    return pd.DataFrame(cols)


def main() -> int:
    p = stage_parser(__doc__, "s1_fetch_data")
    p.add_argument("--no-download", action="store_true", help="never download; print manual instructions for missing files")
    p.add_argument("--rehash", action="store_true", help="recompute SHA-256 even when CHECKSUMS.sha256 has an entry")
    p.add_argument("--workers", type=int, default=4, help="processes for per-cycle channel derivation")
    args = p.parse_args()
    ctx = StageContext.from_args(args)
    if args.dry_run:
        print("plan: verify raw files -> ingest MATR (per batch) / HUST (BatteryML CLI + cycler capacity) / NASA (converter)"
              " -> cycle tables -> checks -> figures")
        return 0
    from degradx.data import fetch
    from degradx.viz import s1 as viz

    ct = CheckTable()
    fig_dir, tab_dir = ctx.out_dir / "figures", ctx.out_dir / "tables"
    with RunRecord("s1_fetch_data", ctx.out_dir, {"config": ctx.config, "args": {k: str(v) for k, v in vars(args).items()}},
                   {"note": "no random numbers are drawn in S1"}, ctx.device) as rec:
        with rec.section("verify_raw"):
            rows = fetch.verify(RAW, try_download=not args.no_download, rehash=args.rehash)
            save_table(pd.DataFrame(rows), tab_dir / "raw_files")
            for r in rows:
                ct.require(f"raw {r['file']} present, size and sha256 as recorded", r["present"] and r["size_ok"] and r["sha256_ok"],
                           "present, size and hash match", {k: r.get(k) for k in ("present", "size_ok", "sha256_ok", "sha256_reference")})
            if not all(r["present"] for r in rows):
                print(fetch.manual_instructions(RAW))
                return ct.finalize(ctx.out_dir) or 1
        with rec.section("ingest"):
            logs = ingest(ctx)
            write_json(logs, ctx.out_dir / "logs" / "ingest_records.json")
        with rec.section("cycle_tables"):
            tables = channel_tables(ctx)
        with rec.section("checks"):
            summary = run_checks(ct, tables, logs)
            summary.update(converter_validation(ct, fig_dir))
            write_json(summary, tab_dir / "summary.json")
            avail = availability(tables)
            save_table(avail.reset_index(names="channel"), tab_dir / "channel_availability")
        with rec.section("figures"):
            save_figure(viz.capacity_trajectories(tables), fig_dir / "capacity_trajectories_raw")
            save_figure(viz.cycle_counts(tables), fig_dir / "cycles_per_unit")
            save_figure(viz.channel_availability(avail), fig_dir / "channel_availability")
            save_figure(viz.capacity_source_agreement(tables), fig_dir / "capacity_integrated_vs_cycler")
        rec.extra["skipped"] = ctx.skipped
        code = ct.finalize(ctx.out_dir)
        (ctx.out_dir / "logs" / "checks.md").write_text(ct.markdown() + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
