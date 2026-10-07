# V2 — third dataset (X6): ISU-ILCC under D28; Tongji ineligible from documentation

## What ran

1. **Documentation sweep, before any download.** Four readers, a synthesis, and 12 adversarially verified claims
   (workflow `v2-third-dataset-research`).
   - Tongji was found ineligible: the largest single cell type has 66 cells, so E3 (≥ 67) cannot hold. Recorded at v0
     (`9c25b6c`).
   - D28 was drafted, attacked from three angles (brief compliance, measurement science, an advocate for the rejected
     options) and revised as a judge required.
   - D28, the candidate rules, `configs/profiles/isu_ilcc.yaml` and the reference facts (README Table A1; the authors'
     `valid_cells_paper.csv`) were committed (`659a56f`) **before any measurement file was downloaded**.
2. **Fetch.** `artifacts/v2/v2_third_dataset/fetch_isu.py` downloaded all 7 files of figshare article 22582234 v2
   (11.19 GB). Each was verified against the published MD5. SHA-256 is in `configs/raw_checksums_v2.sha256` and
   `tables/raw_files.json`.
3. **Ingest.** `python scripts/v2/v2_third_dataset.py --ingest --workers 3`.
   - One cell per process, read directly from the zips (about 10 s and 1.4 GB per cell).
   - 145 in-scope cells plus the 10-cell side table.
   - Output: `data/v2/processed/cycle_tables/ISU_ILCC.csv.gz`.
4. **Audit.** `python scripts/v2/v2_third_dataset.py --audit --workers 8`. The first attempt crashed in the additive
   sensitivity, because `fit_profile` needs charge time for the null pool. It was fixed and re-run in full.

## What came out

**Converter checks against the raw arrays** (`logs/checks_ingest.md`):
- calibrated capacity equals the C/5 value at every anchor, to 5.6e-17 Ah;
- cycler capacity equals the maximum of the discharge Q samples exactly;
- charge time from step times equals the sample span exactly;
- every in-scope cell is in the release, and every cell has at least 2 anchors.

**Cycle predicates** over 407 249 aging cycles:
- 39 degenerate;
- 238 incomplete (discharge stopping more than 0.02 V above the cell's median end voltage, or charge ending above
  25 mA);
- 235 non-aging, all by the current rule (median discharge current more than 10 % away from the condition's rate);
  none overlaps an RPT.

**Rest events:**
- 2 168 block starts and 2 174 including pauses (6 pauses that are not block starts);
- the RPT cross-check finds 2 131, with 37 mismatches, which are the documented lost RPTs;
- charge time is masked by protocol at the 2 168 RPT-following cycles.

**Timestamps.** 16 cells have one or two backward timestamp steps of 3–53 min at the same wall-clock moments across
cells (Unix 1.66816e9 and 1.67858e9; logger clock adjustments). File order is chronological, and the time-based rules
are unaffected:
- block starts are found in index order;
- anchors and RPT overlaps are separated from RPTs by hours, not minutes;
- a negative gap is never a pause.
Reported as a warning.

**Eligibility re-check under D28** (`tables/audit_summary.json` → `eligibility`):

| criterion | result |
|---|---|
| E3: units reaching EOL after the guard | **145** (67 required); 0 guard exclusions; 0 by the record-end rule; 43 held-out units reach EOL after the stratified split |
| E4: every EOL unit T ≥ 44 | **pass**: minimum T 265; median 875 [IQR 564, 1475], p95 2 281 |
| E5: charge time and mean discharge V in every unit, passing the weight guard | **pass**: \|Δφ\| 14.6 min against noise SD 3.45 min; 0.050 V against 0.0086 V |
| E1, E2, E6 | pass (D28; E2 under the declared-extraction reading, flagged for the authors) |

**ISU-ILCC is eligible and becomes the third profile.**

**X6(ii) — regeneration at scale** (declared reading, `readings.X6_ii_superseded_D28`). Readings are on the fitting
split.

| | pooled (102 units) | S_full (31 units, DoD ≥ 95.8 %) | S_partial (71 units) |
|---|---|---|---|
| D05 positive runs: measured vs noise-only rate per 100 positions (ratio; enabled at ≥ 2) | 0.208 vs 0.125 (**1.66**; not enabled) | 0.148 vs 0.156 (**0.94**; not enabled) | 0.228 vs 0.109 (2.10; enabled) |
| mechanism diagnostic: runs starting 0–10 positions after a rest event, against random positions | **7.21** [6.17, 8.22] (190 of 248 runs) | 0.99 [0, 2.04] (3 of 14) | 9.09 [7.96, 10.18] |
| placebo window (−11 … −1) | 0.04 [0, 0.13] | 0.32 [0, 1.13] | 0 |
| recovery index, median ln(Q after / Q before) | — | −0.0008 | +0.018 |
| overshoot over C/5 (median) | — | −0.2 mAh | +4.4 mAh |

- **Operator-null check.** The calibration operator applied to smoothed raw capacity plus AR(1) noise gives a positive
  run rate of 1.75× the D05 reference (below 2×, so it alone does not reach the enable level). Its null mechanism
  ratio is **6.16 [5.12, 7.18]**.
- **Recovery-index regression** (2 168 events, 145 units; cluster bootstrap):
  - intercept −0.040 [−0.056, −0.020];
  - 1/DoD +0.030 [0.010, 0.046];
  - discharge C-rate +0.021 [0.014, 0.029].
  Recovery grows as DoD falls and as the discharge rate rises: the kinetic signature.
- **Additive sensitivity.** Positive ratio 1.16, not enabled, the same outcome as the primary. Positive run amplitude
  median is 6.4 mAh additive against 8.6 mAh calibrated.

**Reading: regeneration is not shown at scale** (pooled not enabled, S_full not enabled). The positive runs cluster
right after RPTs, but only in partial-DoD cells. Their size grows with 1/DoD and with discharge rate. And the
calibration operator alone reproduces most of that clustering (6.2 against 7.2). The paper reports this as "post-RPT
recovery of partial-window discharge capacity, not separable from voltage-cutoff kinetics". **The third profile
enables no inserted patterns, so v2 has no sparse set in any profile.**

**Cross-checks** (`tables/cross_checks.*`, `tables/calibration_factor_to_T.csv`):
- **q₁ against week-0 C/5.**
  - With the week-0 anchor: median +0.0024 q_nom; |difference| > 0.01 q_nom in 19 of 145 units.
  - Without it: 80 of 145. The week-0 anchor does what MS3 asked of it.
- **EOL agreement.** T falls outside the RPT interval of the C/5 crossing (or the interval before it) in 4 of 145 units.
- **Calibration factor up to EOL.**
  - Median at T is 1.63; S_full 1.05, S_partial 2.10.
  - p95 at T is 4.07; the maximum is 8.68 (G27C2, 2.4C discharge).
  - 25 units exceed 3 before T, and 4 exceed 5.
  - Beyond T the records continue to the next RPT, and f reaches 32.6.
  - **"Nominal ≤ 1.94" is not a bound.** High-rate partial discharges lose far more throughput late in life than full
    capacity does. The per-unit f is reported, as D28 declared; this is a cost of the extraction (see Anomalies).

**Side table**, the 10 released in-range cells outside the authors' list (outside the profile):
- G11C2–C4 reach EOL at T 144–168, and G11C1 stops after 62 cycles.
- G14C2–C3 reach EOL at T 108 and 218.
- G36C1 at T 578; G37C1 at T 748.
- G9C3 and G14C4 do not reach 200 mAh on C/5.

## Checks

- **Ingest:** 5 pass, 1 warning (backward timestamp steps).
- **Audit:** E3, E4 and E5 pass.

## Anomalies

1. **The calibration factor grows far beyond 1 / mean DoD late in life on high-rate partial cycles** (up to 8.7 before
   EOL).
   - Within a week, the calibrated capacity of those units is mostly scaled kinetics. The capacity noise variance of
     S_partial (1.8e-5 Ah²) is 5.5× that of S_full (3.3e-6 Ah²).
   - It stands, as declared: changing the extraction now would be a post-data change.
   - It is listed in the D28 cost line, and the paper's §3.4 states it.
2. **The extraction confounds the mechanism diagnostic.**
   - Exact anchoring pins the slow residual at the knot one cycle before each rest event.
   - The operator-null check measures that: a null ratio of 6.2 against an observed 7.2.
   - The declared stratified reading and the null check are what keep X6(ii) honest. Without them, 7.2 would read as
     strong regeneration.
3. **G11** (absent from the authors' list and from Table S1) reaches EOL in 144–168 cycles in three cells, and one
   stops after 62. The documentation rule that excluded it was the right call for E4 robustness, though E4 would still
   pass here (all T ≥ 44).

## Decisions needed

None.
- **D28 was taken before download.** Its E2 reading is flagged for the authors: under the strict reading, the brief
  would require stop and report.
- **X6(i)** is answered at V3–V6 for this profile.
