# Deviations from the paper's methodology

Every departure from Section 3 of the paper, including ones forced by data or tooling, is logged here
(brief R4). Entries are never deleted; a reverted deviation is marked as such.

Format per entry:

- **ID / stage / class** — `tooling` (no effect on what the paper can claim) or `methodological`
  (changes a claim; these are stop-and-report events and carry a pointer to the human decision).
- **Paper says** — quotation with `paper/paper.tex` line numbers.
- **What was done**
- **Why**
- **Cost to the claim**

---

<!-- entries appended below, newest last -->

### T1 — S1 — tooling — MATR time stored in minutes by BatteryML
- **Paper says:** nothing (data layer). Brief R3: measured data enter as BatteryML `BatteryData`.
- **What was done:** `degradx.data.matr` multiplies BatteryML's MATR `time_in_s` by 60 before dumping and records `time_unit_converted_from_minutes=True`.
- **Why:** MATR `cycles.t` is in minutes (a full cycle spans ~60; `summary.chargetime` ~10 min); BatteryML copies it unconverted.
- **Cost to the claim:** none; without it every MATR duration and charge time would be 60x too small.

### T2 — S1 — tooling — NASA PCoE through an own converter
- **Paper says:** l.253 NASA PCoE is one of three profiles. Brief §2.2: BatteryML does not cover it.
- **What was done:** `degradx.data.nasa` maps each discharge operation (with its preceding charge) to a `CycleData`; checked field-for-field against BatteryML MATR/HUST objects and against the raw arrays (S1 checks).
- **Why:** no BatteryML preprocessor exists.
- **Cost to the claim:** none methodological; a converter bug would propagate, hence the raw-array equality checks.

### T3 — S1 — data layer — capacity channel is the cycler-reported per-cycle capacity (D11)
- **Paper says:** "the capacity channel" (l.148, l.236); declarations r2: "max discharge capacity of the cycle [Ah]".
- **What was done:** capacity = MATR `summary.QDischarge` (identical to max Qd), HUST `dq`, NASA `Capacity`.
- **Why:** docs/DECISIONS/D11_capacity_source.md (HUST integrated capacity reads +18 mAh and never reaches the documented stopping threshold).
- **Cost to the claim:** none to the methodology; the integrated series remains in the cycle tables.

### T4 — S6–S8 (v1), recorded at v2 V0 (2026-10-07) — tooling — bootstrap intervals with 2 000 instead of 10 000 resamples
- **Paper says / declared:** `declared_by_design.statistics.bootstrap.n_resamples: 10000` (BCa over units).
- **What was done:** v1 S6 (`s6_usability.py`: permutation importance, conditional importance, term ablation), S7 (`s7_responsiveness.py`: resolution and operating-range intervals) and S8 (`s8_reference_methods.py`: unit-mean intervals) used `n_resamples=2000`. S5 used 10 000.
- **Why:** run-time choice in v1, not recorded at the time; found by the v2 pre-registration review.
- **Cost to the claim:** none to any point estimate. The interval endpoints carry more Monte Carlo error (for BCa at 2 000 resamples, a few per cent of the interval width). Whether any v1 reading sits within that distance of its threshold has not been re-checked; v1 intervals are cited with this caveat. Every v2 interval uses 10 000 (declarations r3 `v2.statistics.bootstrap_n_resamples`).

### T5 — V2 (v2) — tooling — ISU-ILCC cycle timestamps step back in 16 cells
- **Paper says / declared:** D28 rest events and calibration anchors are placed from cycle and RPT timestamps
  (`declared_by_design.v2.third_profile.candidate_rules`).
- **What was done:** 16 in-scope cells (G41C1, G55C1–C4, G56C1–C3, G61C2–C4, G62C1, G62C3, G63C3, G63C4, G64C4) carry one
  or two backward steps of 3–53 min in the cycle start times. The steps fall at the same wall-clock moments across
  cells (Unix ≈ 1.66816e9 and 1.67858e9), so they are logger clock adjustments. The order of cycles in the files is
  chronological. The converter keeps file order. Block-start rest events are found in index order, and anchors and RPT
  overlaps are separated from RPTs by hours, not minutes, so the declared rules place every event as they would on
  monotone times. The ingest check reports the cells at warning level.
- **Why:** a property of the released timestamps.
- **Cost to the claim:** none found. There are 18 steps, and no rest event of either source lies within 3 cycles of any
  of them (checked). Pause detection ignores negative gaps.

### T6 — S5 (v1) and V5 (v2), recorded 2026-10-08 — methodological (a declared rule left out, now applied) — D02b readability of the discriminative error
- **Paper says / declared:** `declared_by_design.minimum_counts.held_out_units_per_measure.discriminative_error`: at least
  8 held-out units, and the value is readable only if its 95 % half-width is ≤ 0.5 |0.5 − value| (D02b); otherwise the
  cell is void with the reason stated.
- **What was done:** v1 S5 and the first V5 run applied the minimum count only. The v2 pipeline review found the gap.
  `scripts/v2/v5_discriminator_readability.py` re-runs V5's seeded discriminators with their test predictions kept. The
  accuracies reproduce V5 exactly, and the script applies a unit bootstrap per generation seed (10 000 percentile resamples).
  - MATR: seeds 0 / 1 / 2 read 0.333 [0.187, 0.483], 0.244 [0.154, 0.359] and 0.423 [0.281, 0.561]. Only seed 1 is
    readable.
  - HUST: seeds 0 / 1 / 2 read 0.373 [0.267, 0.482], 0.460 [0.381, 0.544] and 0.623 [0.584, 0.663]. Only seed 2 is
    readable.
- **Why:** an omission in v1 that V5 inherited.
- **Cost to the claim:**
  - **Table 1's v2 discriminator cells are void under D02b for both profiles:** not every seed is readable
    (`artifacts/v2/v5_fidelity/tables/discriminator_readability.json`).
  - **The values are still reported, with the void reason.** The X3 reading "the discriminator gap narrows" rests on
    the mean moving from 0.07 / 0.16 (v1) to 0.33 / 0.49, against v1 seed half-ranges of 0.02 / 0.04. That reading is
    a shift of the seed mean, not a readable level, and it is reported as such.
  - **v1's S5 cells were not re-checked:** v1's predictions were not saved, and v1 is not re-run. They are cited with
    this caveat.
  - No other measure is affected.
