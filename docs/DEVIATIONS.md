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
