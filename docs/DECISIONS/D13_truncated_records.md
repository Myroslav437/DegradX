# D13 — A measured record that ends at its dataset's stopping threshold reaches EOL at its last position

**Stage / claim affected:** S2 audit (EOL attainment), S3 fitting range, S5 transfer target on measured units (HUST
would otherwise have no transfer measurement), Table 2 unit counts.

**Decision.** HUST and MATR b1/b3 records were cut by their providers at the stopping rule (80 % of nominal
capacity). Under strict Eq. 3 (`T = min{t : z_t ≥ 1}`, i.e. smoothed `q_t ≤ 0.88 Ah`), whether such a record
"reaches" EOL depends on the last mAh of noise. How is attainment defined for them?

**Options considered**
- **a. No change:** strict first crossing.
- **b. Tolerance on the state:** `T = min{t : z_t ≥ 1 − ε}`, with ε = 0.02.
- **c. Record-end rule:** strict first crossing. If the state never reaches 1 but the mean raw capacity of the last 5 recorded positions lies within τ·q_nom of the threshold (τ = 0.01), then `T` = the last recorded position.
- **d. Raise ρ to 0.85** (strict).

**Evidence** (`experiments/decisions/D13/{run.py,result.json,per_unit.csv}`; S1 measurement of how far records end above the threshold)

Real: all four run on all units. Works:

| | a | b | c | d |
|---|---|---|---|---|
| HUST units reaching EOL | 11 / 77 | 77 / 77 | **77 / 77** | 77 / 77 |
| HUST median \|T − Table S1 cycle life\| | 0 (11 units) | 17 cycles (p90 28.8) | **0 (p90 0)** | not comparable (different threshold) |
| MATR units reaching EOL | 96 / 180 | 173 | **173** | 175 |
| MATR median \|T − file `cycle_life`\| | 1 (p90 2) | 4 (p90 6) | **2 (p90 2)** | not comparable |
| NASA units reaching EOL | 12 | 12 | 12 | 14 |
| min z at T | 1.000 | 0.980 | 0.983 | 1.000 |

The non-crossing records end 0.2–1.6 mAh above 0.88 Ah (HUST, last-5 mean) and ≤ 5.2 mAh (MATR, 90th percentile). The documented unfinished cells end ~94 mAh above and stay censored under (c).

Clear, option (c) in three sentences: a measured record that stops at its dataset's documented stopping threshold (its last readings within 1 % of nominal capacity of it) has reached EOL at its last position, because the provider stopped recording at the threshold. Generated units are never truncated and use Eq. 3 unchanged. Its failure mode: a record that happens to end near the threshold for another reason (e.g. a crash) is counted as reaching EOL.

**Chosen: c.**
1. *Logical:* it follows from the datasets' own stopping rules rather than from moving an endpoint. It does not involve any attribution method.
2. *Consistent:*
   - `T` then equals the RUL label the datasets provide (HUST exactly for all 77 cells; MATR within 2 cycles), which is what §3.2.2 claims `R` is ("the same quantity that measured datasets provide as a RUL label").
   - Option (b) contradicts that claim by 17 cycles on HUST.
   - Option (d) abandons the 80 % convention that the ρ paragraph and C3 are built on.
3. *Clear:* one sentence and one declared constant (τ).
4. *Measured:* best agreement with documented cycle life at full attainment.

**Cost.**
- One more declared constant, τ = 0.01·q_nom.
- For truncated records, `z_T` lies in [0.983, 1) rather than ≥ 1, so the measured and generated definitions of `T` differ by at most that gap. A reviewer could call this a second EOL definition. The answer is that it applies only where the record itself was cut at the threshold, and the unit counts per rule are reported.
- ρ sensitivity: at ρ < 0.80 these records are censored (they end 55+ mAh above the lower threshold). The sensitivity sweep therefore reports lower attainment below 0.80, which is a property of the truncation.

**Paper impact:** §3.1.1, one sentence in the ρ-conventions paragraph and one item in the §3.3 declared list (round-2 amendment).
