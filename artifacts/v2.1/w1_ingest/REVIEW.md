# W1 — acquisition and ingestion of the TRI/Stanford formation dataset (brief "DegradX v2.1", 2026-10-13)

## What ran

1. **Fetch** (`scripts/v2_1/w1_fetch.py`).
   - Both archives were downloaded into empty directories under `data/v2.1/raw/`. Their byte size, ETag and
     Last-Modified match the declared HEAD values (r4 `archive.integrity`), and the S3 version ids were recorded.
   - The SHA-256 and full member list of each archive were committed **before any member was opened** (commit
     `01889fd`, W1 part 1).
   - The pinned parameter sheet (cx26 @ 2bc2313) and the notes copy (Rhyu @ 9530854) were fetched with their declared
     SHA-256.
2. **Extraction** (`scripts/v2_1/w1_extract.py`).
   - Only the declared members of the current archive were extracted, with the tarfile `data` filter: 182 aging files,
     plus 182 `._*` AppleDouble stubs caught by the literal metadata pattern. The stubs are Finder metadata, not data.
   - The original archive contributes no file, because all 39 of its seqs are also in the current archive (r4
     `archive.rule`).
   - The three `Nova_Regular_Ref_100-102` files exist only in the original archive. That archive is not used, so they
     are listed and not converted.
3. **Conversion** (`src/degradx/data/tri_formation.py`, `scripts/v2_1/w1_ingest.py`).
   - Pass 1 runs one file per process, at most 3 processes, and computes per-cycle statistics.
   - Pass 2 applies the cross-cell rules: scope, modal protocol and tolerance, predicates, positions, masks and rest
     events.
   - The resulting cycle table is `data/v2.1/processed/cycle_tables/TRI_FORMATION.csv.gz`.
   - Wall time 943 s.

## What the archives hold

| | current `data_03032025.tgz` | original `data.tar.gz` |
|---|---|---|
| bytes, SHA-256 | 15 639 357 254, `4e6ec37a…c032` | 3 254 154 716, `b3fdf331…78c0` |
| layout | `data_03032025/Aging` (aging), `data_03032025/Formation` (formation) | `data/maccor`, `data/novonix` |
| aging files | 182, one per seq, every seq in the sheet | 39 (all also in the current archive) + `Ref_100-102` |

- **BEEP writer.** Every file was written by post-2023 BEEP: it has a top-level `diagnostic` config and `step_index` in
  `cycles_interpolated`, and carries no `raw_data`. So `cycles_interpolated` is the profile-wide source (r4
  `channels.charge_time.source`).
- **Structuring parameters.** They are identical in all 182 files:
  - `nominal_capacity` 0.24;
  - **`full_fast_charge` 1**;
  - `charge_axis` and `discharge_axis` both `test_time`;
  - resolution 1 000;
  - `v_range` [3.0, 4.4].
- **Interpolation on time.** Each step is interpolated on its own time range, so there are no capacity-grid tails.
  r4's trim-and-extrapolate rule therefore reduces to "the last sample of the step".
- **`full_fast_charge` = 1 explains the `charge_duration` pattern the brief reported.** BEEP's threshold is
  0.24 Ah × 1, so `charge_duration` is the time to charge 0.24 Ah and is NaN once a cycle charges less.
- **Maccor program names differ only in the pre-aging OCV rest.** `Formation_Maccor_5_ocv_0h` (68 files), `_72h` (71)
  and `_168h` (43) match the sheet's `ocv_time` (Table S4, step 0). The regular cycles are identical in every file.

## The brief's one-cell observations (§1), verified on `Nova_Regular_197.034`

| brief | measured |
|---|---|
| 0.2452 Ah at the start | 0.2456 Ah at the first aging cycle (cycle_index 3) |
| crosses 0.8 × 0.24 Ah at cycle 631 | first cycle ≤ 0.192 Ah at cycle_index 631 |
| 0.088 Ah by cycle ~871 | 0.0883 Ah at cycle_index 871 |
| mean discharge voltage 3.742 → 3.719 V by EOL | 3.742 → 3.717 V at cycle_index 631 |
| `charge_duration` NaN from cycle 213, 74 % | 74.4 % NaN, explained by `full_fast_charge` = 1 (above) |
| interpolated charge step 76.7 min early | step span 77.1 min; the declared CC-CV charge time is 72.0 min, which excludes a ≈ 5 min zero-current segment at the start of the step |
| temperature NaN, IR zero | yes, in all 182 files: neither channel is available |

## Converter checks (r4 `converter_checks`)

All pass; the table is in `logs/checks.md`.

- **Table equals summaries.** Capacity is identical to `summary.discharge_capacity`, and mean discharge voltage equals
  E/Q to within 1.6e-14 relative.
- **Charge-time validation** passes on 178 of 178 evaluable files; 4 files are not evaluable (seq 291, 292, 307 and
  317, batch 2, fewer than 20 cycles that charge 0.24 Ah).
  - BEEP's `charge_duration` exceeds the reproduced time by a near-constant o = 5.40-5.49 min (median per file; IQR at
    most 0.30 min).
  - That offset is the zero-current segment that BEEP counts from the cycle's first record and the declared charge time
    excludes. It is the documented reason the brief allows.
  - The finiteness of `charge_duration` agrees with the reproduction in 100 % of comparable cycles.
- **Index structure.**
  - Summary and diagnostic indices are disjoint, and the summary is increasing.
  - `cycle_index` is contiguous from 0 in 181 of 182 files (not in seq 317), so BEEP's positional assignment aligns.
- **Diagnostics.**
  - The C/20 RPT discharges at 0.0120 A and the C/5 RPT at 0.0480 A in every cell.
  - The documented layout holds in 543 of 546 (cell, type) pairs. Cell 152 has a shifted schedule.
  - No labelled diagnostic cycle has an aging discharge current.
- **Protocol.**
  - The modal tuple is 0.24 A / 0.18 A / 4.4 V / 3.0 V, equal to the documented one (E2 on the files: pass).
  - Incomplete cycles are 1 of about 189 000 (0.0005 %).
  - **No second aging protocol** (under D33, below).
- **Mapping.** The protocol grouping equals the authors' consecutive triplets in every case: 63 groups including the
  baseline, 2-3 cells each.

## D33 — a post-data correction (read before the counts)

- **The problem.** r4 read the per-cycle charge current as the 90th percentile of all positive charge samples. Applied
  as declared:
  - 40 cells carry runs of more than 11 cycles whose charge current departs by more than 10 %;
  - the rule reads them as a second aging protocol: 40 sources, 114 agreeing pairs, which is a stop case.
- **What the runs really are.** Every departing cycle is long after EOL, with capacity collapsed to 0.006-0.046 Ah. The
  cell reaches 4.4 V almost at once, so its charge is nearly all CV.
  - Where a CC phase exists the maximum current is still 0.240 A.
  - Discharge current, V_cv and V_end equal the modal values.
- **The fix.** D33 reads the charge current on the constant-current samples only (below the cycle's own V_cv − 10 mV).
  A cycle without a CC phase is not tested for a charge-current departure.
- **Result.** No cell is out of tolerance and no second protocol is present.
- **Where the literal outcome is kept.** `tables/ingest_summary_r4_literal.json`, `tables/cells_r4_literal.csv`,
  `logs/checks_r4_literal.md`, and the `d33_r4_literal_estimator` block of `tables/ingest_summary.json`.
- D33 is logged in the declarations (2026-10-13) and listed for the authors.

## Counts (r4 `cell_scope.counts_reported`)

- **Cells.** 182 aging files, 182 parsed, 182 with a sheet row, **182 in scope**, none excluded. The sheet has
  183 rows; seq 298 has no file. For comparison: 186 designed, 180 design rows, Rhyu et al.'s 178. The baseline cells
  324-326 are in scope.
- **Positions.** 189 485 aging positions, 736-1 625 per cell (median 1 020).
- **Predicates.** 8 cycles degenerate for lack of samples, 1 incomplete (clause c), 1 non-aging.
- **Charge-time mask.** 2 322 cycles masked after an interruption (diagnostic, or the first aging cycle). No pause
  inside a charge.
- **Rest events.**
  - 2 140 diagnostic, 88 paused and 112 gap events.
  - **75 DST artefacts were set aside.** These are 1 h steps at the 2022-11-06 and 2023-11-05 fall-back hour that BEEP
    maps as PDT.
  - 6 events near a spring-forward instant are flagged and kept.
  - No paused gap lies inside the sampled steps (`paused_located` 0).
- **Interpolation ramps.** 190 cycles carry a ramp in the interpolated discharge step: a stray zero-current record at
  the cycle start, almost always after the initial RPT. None of them changes a protocol reading.
- **Cross-check.** The mean discharge voltage integrated from the discharge samples agrees with E/Q: median
  |difference| 3.8e-5 V.
- **Notes.** 13 cells carry lab-note tags (`formation_mapping.lab_notes`). Tags never exclude a cell.

## Observations for W2

- **One level outlier, TRI_270.** Its mean discharge voltage reads about 3.61 V where the others read 3.70-3.74 V, and
  its charge time about 80 min where the others read 70-75 min. It belongs to the repeated batch 269-287, built with a
  different electrolyte lot according to the lab notes. It stays in the profile: formation and build differences are the
  variation the profile carries. The W2 leave-one-out influence row will name it if it moves the pre-screen.
- **Post-EOL collapse.** Capacity falls to 0.01 Ah and the mean discharge voltage jumps upward. Fits use positions up to
  EOL, so neither affects the profile.

## Decisions

- **D33** (post-data, W1): the charge-current estimator of the protocol check.

## Next

W2: audit, offset pre-screen and eligibility on the 182 cells.
