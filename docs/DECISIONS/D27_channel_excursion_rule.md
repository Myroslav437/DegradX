# D27 — The non-capacity glitch rule (D17) is extended to runs of up to three departing positions; v2 applies it to every profile before refitting

**Stage / claim affected:**
- V1 (brief "DegradX v2"), taken after inspecting the held-out MATR cells and before any v2 refit;
- `declared_by_design.channel_series.cleaning_rule` (r3, `max_run_v2`);
- Table 2 (charge-time noise row);
- v1 S5 anomaly 2, which the v1 Results text cites as evidence for the cause of MATR's TSTR gap.

**Decision.** In v1, MATR's held-out charge-time residual variance was 53.5 min², against 0.82 in the fitting split and
0.66 generated. v1 read this as "a few held-out cells with multi-cycle excursions". What is it, and does the cleaning
rule change?

**What the inspection found** (`experiments/decisions/D27/{run.py,result.json,run.log}`, v1 profile and split, residual
about the v1 mapping φ_c(z) over t₁..T):
- **One cell carries 98 % of the held-out charge-time sum of squares:** MATR_b1c2, maximum absolute residual 1 275 min.
- **The cause is a single reading:** 1 301.6 min at position 2 174, where the cycle duration is 79 358 s. That is a
  charge interrupted by a pause of about 21 h. The next position (25.8 min) departs from the centred rolling median
  (24.2) by 0.0505 of the cell's median charge time, just over the 0.05 threshold. Because one neighbour departs, D17's
  "neither neighbour departs" clause leaves the 1 301.6 min reading in.
- **The cell's two other large readings were already removed by D17:** 440.1 min at position 10 and 297.4 min at
  position 846, both isolated.
- No other held-out MATR cell, and no HUST cell, holds a comparable excursion. The largest per-unit share elsewhere is
  0.11–0.21.

So the held-out variance is not "multi-cycle excursions in a few cells". It is one paused cycle in one cell, together
with its recovery reading.

**Options considered**
- **a. Runs of up to two departing positions** with non-departing neighbours are masked.
- **b. Runs of up to three departing positions** with non-departing neighbours are masked (an interrupted cycle plus up
  to two recovery cycles).
- **c. Keep the rule and the cell, and report.** Table 2 shows the fitting-split value next to the held-out value
  either way.
- **d. Runs of up to five.**

**Evidence (pooled residual variance and lag-1; readings masked over all positions)**

| rule | MATR fitting charge time | MATR held-out charge time | MATR fitting temperature | HUST charge time, fitting / held-out |
|---|---|---|---|---|
| D17 (runs of 1, v1) | 0.826, φ 0.906; 379 / 79 568 masked | **53.0**, φ 0.766; 274 / 31 642 | 0.504; 51 masked | 1.397 / 1.472; 4 / 1 masked |
| (a) runs ≤ 2 | 0.823, φ 0.907; 411 | 1.095, φ 0.833; 320 | 0.497; 93 | unchanged; 6 / 1 |
| (b) runs ≤ 3 | 0.823, φ 0.909; 420 | **1.073**, φ 0.855; 332 | 0.497; 99 | unchanged; 6 / 1 |
| (d) runs ≤ 5 | 0.819, φ 0.909; 425 | 1.073, φ 0.855; 332 | 0.496; 103 | unchanged; 6 / 1 |

Mean discharge voltage and IR change by less than 2 % under every rule.

Real: all four are possible.

Works:
- (a), (b) and (d) bring the held-out charge-time variance from 53.0 to 1.07–1.10, within 1.3× the fitting split. They
  differ from each other by at most 2 % of any variance.
- (c) leaves one paused cycle setting a Table 2 row.

Clear:
- (b) in one sentence: "a reading, or a run of up to three consecutive readings, that departs from the local median by
  more than 5 % of the unit's typical value while the readings on either side do not is a measurement artefact and is
  removed."
- (a) reads as tuned to the one observed case: the smallest run length that removes it.

**Chosen: b** (runs of up to three positions; `max_run_v2: 3`).
1. *Logical:* a charge interrupted by a pause produces one aberrant reading, and possibly one or two disturbed readings
   after it. None is a degradation reading. Only non-capacity channels are affected. Capacity keeps D12, and inserted
   patterns live on capacity only, so the rule cannot remove a pattern.
2. *Consistent:* it is D17 with the run length extended, with the same threshold and the same rolling median, and it is
   applied to every profile before refitting, as the brief requires.
3. *Clear:* one sentence.
4. *Measured:* 41 more charge-time and 48 more temperature readings masked in the MATR fitting split (0.05 % and 0.06 %);
   the held-out row becomes readable.

**Cost.**
- **The rule was set after the data were seen.** It is listed among the post-data rules in the v2 Limitations.
- The run length 3 is a declaration, not an estimate. Runs of 2 and 5 give the same held-out variance to 2 %.
- **v1's account of the MATR transfer gap partly rested on this artefact.** The v1 paper cited the 53.5 min² held-out
  variance as evidence of per-cell charging structure; it was one paused cycle. V1 (D26) tests the per-cell-structure
  explanation directly.
- V1 itself re-runs v1's TSTR with D17 so that the full input set reproduces v1. A sensitivity row with D27 applied to
  the measured side is reported beside it.

**Paper impact:** AMENDMENTS round 7. §3.3 step one: "a single reading" becomes "a reading or a short run of
readings". The Table 2 note states the fitting-split column.
