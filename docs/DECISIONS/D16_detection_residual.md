# D16 — Patterns are detected on the fit from the early-life reference to EOL, and cannot outlast the smoothing window

**Stage / claim affected:** S2 audit pattern statistics, S3 step five (pattern rate, amplitude and duration), S4 generation, the sparse set of the attribution ground truth, and Table 2's regeneration rows.

**Decision.** With the fade families fitted over positions 1..T, the MATR and HUST residual is dominated by two kinds of trajectory misfit:
- the early capacity rise, which the fade families cannot express, gives negative runs of up to −20 mAh over the first ~50 cycles;
- low-frequency oscillations give runs of up to 120 positions.

The declared detector labels both as inserted patterns, and a generator trained on them would plant start-of-life misfit at random positions. On which residual, and with what run limits, are patterns detected?

**Options considered**
- **a. As declared (r2):** fit over 1..T; any run of length ≥ m.
- **b.** Fit over t₁..T, the fall from `q₁` as in D15.
- **c.** Option b, plus a run longer than the Savitzky–Golay window (11 positions) is not a pattern.
- A residual from a local smoother instead of the trajectory fit was not tested. The paper says steps four and five use "the residuals of the trajectory fit", and r1 rejected smoothed residuals because they keep only 37–71 % of a peak.

**Evidence** (`experiments/decisions/D16/{run.py,result.json,per_unit.csv}`): 30 MATR units, 30 HUST units, and the 9 NASA units reaching EOL with ≥ 40 kept cycles. Real: all run.

| | MATR a / b / c | HUST a / b / c | NASA a / b / c |
|---|---|---|---|
| positive / negative events | 38/94, 50/87, 48/79 | 59/95, 56/87, 34/78 | 7/1, 8/1, 8/1 |
| events with extremum in first 50 positions | 34, 18, 14 | 40, 33, 15 | 5, 6, 6 |
| runs longer than 11 positions | 10, 10, 0 | 47, 31, 0 | 0, 0, 0 |
| median \|amplitude\| [mAh] | 5.6, 3.3, 3.2 | 4.5, 4.0, 2.5 | 35.4, 35.6, 35.6 |
| planted-transient recall (5 per unit, 2–8 positions, 4–10× scale) | 1.0, 1.0, 1.0 | 1.0, 1.0, 1.0 | 0.8, 0.8, 0.8 |
| detected / planted amplitude | 0.93, 0.93, 0.93 | 0.97, 0.96, 0.96 | 0.93, 0.93, 0.93 |

On the full S2 audit (declared scope) under (c):
- MATR: 124 positive events, median +2.95 mAh; 179 negative, median −3.79 mAh.
- HUST: 78 positive, median +2.29 mAh; 196 negative, median −1.80 mAh.
- NASA: 21 positive, median +74.5 mAh; 3 negative.

Clear, option (c) in three sentences:
1. The trajectory is fitted over the fall that Eq. 3 measures, from `q₁` to EOL.
2. A departure lasting longer than the smoothing window survives smoothing, so it changes `z_t`. Paper l.175 says inserted patterns do not, so such a departure belongs to the mean component.
3. The limit is the smoothing window already declared, so no new constant is needed.

Failure mode: a slow misfit that hovers around the threshold can split into several short runs, each within the limit. This is visible in HUST 7-5, with 18 short negative runs along one dip, and is reported in S2 REVIEW. A genuine regeneration lasting more than 11 cycles would also be absorbed into the mean component.

**Chosen: c.**
1. *Logical:* both parts follow from definitions already stated: the fall is measured from `q₁` (Eq. 3, D15), and patterns do not alter `z_t` (l.175).
2. *Consistent:* the smoothing window and the detection limit become the same quantity, so a pattern and the mean component cannot overlap.
3. *Clear:* no new parameter.
4. *Measured:* long misfit runs go to 0 in MATR and HUST, and early-life misfit events fall by 59–63 %, with no loss of planted-transient recall or amplitude.

**Cost.**
- Misfit shorter than 11 positions still enters the pattern distributions of MATR and HUST. Their "patterns" are a few mAh and not physically documented regeneration.
- Low-frequency misfit that is not detected is not masked from the noise estimate, so it inflates the noise autocorrelation.
- A reviewer could argue the cap is tuned to the MATR/HUST artefacts. The answer is that the cap is the declared smoothing window, chosen at S0 for a different reason (its frequency response).

**Paper impact:** §3.3 step two ("from the early-life reference to EOL") and the detection rule (maximum run length with the reason); round-2 amendment.
