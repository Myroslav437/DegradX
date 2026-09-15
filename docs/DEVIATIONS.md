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
