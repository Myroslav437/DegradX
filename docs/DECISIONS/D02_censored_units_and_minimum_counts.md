# D02 — Censored units inform shape-free quantities; each use has a minimum count below which it is void

**Stage / claim affected:**
- S3: which fitting units feed θ, mappings, noise, covariance, patterns and lengths;
- S5: which held-out units feed fidelity;
- every table cell, via its minimum count.

**Decision.** Under the amended Eq. 3, the degradation state is defined for every unit that passes the guard, and only T needs attainment. Two questions:
1. Should censored (guard-passing, not reaching EOL) units contribute to the quantities that do not need T?
2. What is the minimum count per use, below which a measurement is void?

**Options considered**
- **Censored scope**
  - **a. Paper as written** (l.158 "which are excluded"): censored units are excluded from everything.
  - **b.** Censored units contribute to channel mappings, noise, cross-channel covariance and pattern detection. θ, the length distribution and the transfer target use units reaching EOL only.
- **Minimum counts**
  - **m0.** No minimum: report every number with its interval.
  - **m1.** A declared readability criterion. A statistic is reported only where the 95 % resampling half-width relative to its value is ≤ 50 %, so the interval does not span a factor of three; below the resulting count, the cell is void.

**Evidence** (`experiments/decisions/D02/{run.py,result.json}`)

Censored scope (S3 fit, fitting split):

| | MATR a (reaching only) | MATR b | NASA a | NASA b |
|---|---|---|---|---|
| units | 90 | 95 | 8 | 13 |
| positive events | 84 | 97 | 7 | 7 |
| capacity noise variance / φ | 3.04e-6 / 0.951 | 2.82e-6 / 0.942 | 2.44e-4 / 0.598 | 2.15e-4 / 0.474 |
| mean discharge voltage noise variance | 4.82e-4 | 5.36e-4 | 4.30e-4 | 2.45e-4 |
| temperature noise variance | 0.478 | 0.500 | 2.52 | 1.25 |
| charge-time φ(1) [min] | 21.00 | 21.00 | 166.6 | 158.5 |

Resampling, 95 % half-width relative to the full-pool value (300 draws):

| n | 3 | 5 | 7/8 | 10/12 | 15/20 | 21/40 |
|---|---|---|---|---|---|---|
| median T, MATR units (subsample) | 0.44 | 0.37 | 0.33 (8) | 0.30 (12) | 0.22 (20) | 0.13 (40) |
| trajectory shape (position of z = 0.5 / T) | 0.045 | 0.031 | 0.019 | 0.016 | 0.010 | 0.006 |
| median positive amplitude, NASA events (bootstrap) | 0.77 | 0.69 | 0.64 (7) | 0.48 (10) | 0.39 (15) | 0.36 (21) |

Real: all run. Works:
- (b) adds 5 NASA units (13 against 8) to the noise and mapping estimates. It changes NASA's noise variances by up to a factor of 2 and adds no events.
- Under m1, unit-based statistics are readable from 5 units (0.37) and event-based statistics from 10 events (0.48).

Clear:
- (b): "Quantities that do not need T (mappings, noise, covariance, patterns) use every unit that passes the guard; θ, lengths and the transfer target use units that reach EOL."
- m1: "A statistic is reported only if its 95 % interval spans no more than ±50 % of its value; for these statistics that is at least 5 units or 10 events, otherwise the cell is void."

Failure modes: censored units carry no late-life state, so mappings near z = 1 rest on reaching units only; the counts are calibrated on MATR units and NASA events, not on every statistic.

**Chosen: b + m1.** Declared minima:
- θ-derived and length statistics: ≥ 5 units;
- pattern amplitude, duration and rate statistics: ≥ 10 events;
- held-out measured units for distributional and transfer measures: ≥ 5 units, provisional (S5 tests this with its own resampling and may supersede it with a dated record).

Criteria:
1. *Logical:* C3 makes z available for censored units, and the brief's own reading of the amendment is that only T needs attainment.
2. *Consistent:* the paper's void convention (Table 3) extended to counts.
3. *Clear:* two sentences.
4. *Measured:* 13 vs 8 NASA units for noise; readable thresholds from the curves.

**Minimum counts gate reporting, not generation.** A pattern type enabled by D05 is generated from whatever events the fitting split supplies. The attribution ground truth is exact regardless of how precisely its amplitude distribution was estimated. What the minimum voids is the claim that the distribution matches measurement.

**Cost.**
- NASA's regeneration statistics (7 fitting-split events) are below the 10-event minimum. Their measured-vs-generated rows in Table 2 are void, while the NASA profile still generates regeneration from those 7 events. A reviewer may object that the benchmark generates from a distribution it cannot validate. The answer is that the ground truth does not depend on that validation, and the fidelity cell says so.
- Mapping and noise estimates for NASA mix groups with different ambient temperatures (24 °C and 43 °C units that pass the guard).

**Paper impact:** §3.1.1 (the ρ paragraph's "which are excluded" narrowed to the uses that need T) and one sentence on minimum counts in §4 or Table 3's void convention (round-3 amendment).
