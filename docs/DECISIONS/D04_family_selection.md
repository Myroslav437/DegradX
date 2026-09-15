# D04 — Family selection: 5 % simplicity margin; a family whose parameters sit at their bounds in more than 20 % of units is not eligible

**Stage / claim affected:** S3 step two, which sets each profile's trajectory family and θ distribution. Downstream: S4 generation, Table 2 row "Trajectory family, fit error", and S5 transfer.

**Decision.** When candidate families have close cross-validated errors, or when the best-scoring family is not identified by short records, which family does the profile use?

**Options considered**
- **a. Declared rule (fixed before S3 in commit `declare D04…`):** lowest median CV-RMSE over fitting units reaching EOL; a family with fewer parameters wins if it is within 5 % of that error.
- **b.** Rule (a), restricted to families whose parameters sit at a bound of their declared range in at most 20 % of units. If no family qualifies, all are eligible.
- **c.** Widen the rollover bounds so that the NASA fits are interior. This was dropped without testing: the bounds were declared before fitting, and moving them after seeing the fits tunes the family to the data.

**Evidence** (`experiments/decisions/D04/{run.py,result.json}`; S3 tables `family_selection_<dataset>.csv`)

| profile (units) | family | median CV-RMSE (fraction of q₁) | units with a parameter at a bound | \|T_fit − T\| / T median, p90 |
|---|---|---|---|---|
| MATR (90) | power law | 0.01291 | 0.39 | 0.013, 0.041 |
| | **two-term exp.** | **0.00609** | 0.02 | 0.004, 0.008 |
| | rollover | 0.00673 | 0.34 | 0.002, 0.004 |
| HUST (54) | power law | 0.01003 | 0.00 | 0.009, 0.017 |
| | two-term exp. | 0.00841 | 0.04 | 0.009, 0.016 |
| | **rollover** | **0.00271** | 0.00 | 0.002, 0.006 |
| NASA PCoE (8) | **power law** | 0.01113 | **0.12** | 0.049, **0.096** |
| | two-term exp. | 0.01133 | 0.88 | 0.049, ∞ (one unit never reaches z = 1) |
| | rollover | 0.01053 | **0.75** (transition width δ at its 5-cycle lower bound in 6 units) | 0.033, **0.262** |

- Choice under (a): MATR two-term exponential, HUST rollover, NASA rollover.
- Choice under (b): MATR two-term exponential, HUST rollover, NASA **power law**.
- In no profile did the 5 % simplicity margin change the choice. On NASA, the power law is 5.7 % above rollover, just outside the margin.

Real: all options run. Works:
- NASA rollover's transition parameters are set by their bounds, not by the data: 6 of 8 units put the transition as sharp as allowed, and one unit has a terminal slope of −239 per 1000 cycles.
- Its θ therefore reproduces the measured EOL position worse at the tail (p90 26 % against 9.6 % for the power law), despite a 5.7 % lower CV error.

Clear, option (b) in two sentences:
1. The family is the one with the lowest cross-validated error among those whose fitted parameters are determined by the data, that is, not held at a bound in more than a fifth of the units.
2. Within 5 % of that error, the family with fewer parameters is used.

Failure mode: a family that is correct but needs wider bounds is excluded; the at-bound fraction is reported for every family.

**Chosen: b.**
1. *Logical:* paper l.161 says the shape is "decided by the data it stands for rather than by us". A distribution of θ held at declared bounds is decided by the bounds.
2. *Consistent:* the brief's S3 check is "θ distributions not collapsing to bounds". Option (b) makes that check part of selection instead of a warning after it. MATR and HUST are unchanged.
3. *Clear:* one clause added to the declared rule.
4. *Measured:* NASA EOL reproduction p90 improves from 26 % to 9.6 % at a 5.7 % CV cost.

**Cost.**
- The NASA profile's trajectories cannot express a transition, because a power law has none. Generated NASA units fade without a knee.
- The 20 % threshold was written into the S3 sanity check before the first S3 run. It became a selection rule after that run showed NASA at 75 %, and it was committed together with the S3 results, not before them. A reviewer can see that sequence in the git history and in this record.
- NASA's θ rests on 8 units, above the D02 minimum of 5.

**Paper impact:** §3.3 step two: selection "among families whose parameters are identified by the data, with a declared margin within which the simpler family is preferred" (round-3 amendment).
