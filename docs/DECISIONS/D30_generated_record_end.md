# D30 — The property table reads generated series with the same EOL rule as measured records (D13's record-end clause)

**Stage / claim affected:**
- V5 property table (Table 2, generated column) for MATR and HUST;
- the r2 note that D13 "never [applies] to generated units, whose trajectories are not truncated" (`eol.record_end_rule.applies_to`);
- v1 S5 Table 2 had the same issue.

Taken 2026-10-08, after the V5 run, on a finding of the v2 pipeline review: post-data.

**Decision.** The property table compares measured and generated units through the same S3 estimator. For a generated
series it ran without D13's record-end clause, on the r2 premise that generated trajectories are not truncated. But the
generator stores every unit only up to its own EOL T (`generate_unit` keeps z[:T]), so the series stops at the threshold
exactly as HUST and MATR records do. The Savitzky–Golay-smoothed noisy capacity has often not crossed the threshold at
the last stored position, so the estimator reads those units as censored and drops them from every EOL-dependent row:
222 of 300 MATR units and 177 of 300 HUST units were kept (generation seed 0). Should the estimator read generated
series with the record-end clause?

**Options considered**
- **a. Keep the r2 reading.** The generated column then rests on the units whose noisy capacity happened to cross before
  the end, a subset biased toward the units whose last readings fell below the threshold.
- **b. Apply D13's record-end clause to generated series in the property estimator only.** The generator, the targets and
  T itself are untouched. It is the same estimator on both sides, which is what the table is meant to compare.
- **c. Store generated series beyond T** (the generator stops at T by design, D18). This changes the generator, which the
  brief forbids after V5 (D29).

Real: (a) is what ran. (b) is a one-line change to the estimator's spec in V5's property step. (c) changes the generator.

Works:
- (b) recovers every generated unit that ends within D13's tolerance, and generated T then equals the generator's own T.
- (a) leaves a 26–41 % selection.
- (c) is excluded.

Clear, (b): "The property table applies one estimator to measured and generated series, including the clause that a
series ending at the EOL threshold reaches EOL at its last position."

**Chosen: b.**
1. *Logical:* a like-for-like comparison needs one estimator, and r2's premise for the exclusion is false for stored
   generated series.
2. *Consistent:* D13 as declared, applied to series that end where D13's do.
3. *Clear:* one sentence.
4. *Measured:* the generated n in the T and θ rows goes from 222/177 to the full set (reported at the re-run).

**Cost.**
- **The rule was set after the data were seen.** It is listed with the v2 post-data rules.
- **The generated column of v1's Table 2 had the same selection.** v1 numbers are cited unchanged, with a note.
- Nothing else depends on it: TSTR, the targets and V6–V8 use the generator's own T.

**Paper impact:** the Table 2 note; Limitations (post-data rule).
