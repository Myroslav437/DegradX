# W7 — score validation on FORM (V7 Part A; brief "DegradX v2.1", 2026-10-13)

## What ran

- **Command.** `scripts/v2/v7_scores.py --datasets TRI_FORMATION --skip-part-b --out-dir artifacts/v2.1/w7_scores`, CPU,
  110 s.
- **Design.** This is the V7 Part A design: 20 windows from each of the 45 generated test units (generation seed 0, 900
  windows).
- **Operators.** The five declared operators degrade the graded field at every grid magnitude.
- **Scores.** Rank agreement, channel allocation error and temporal profile error are read with the declared resolution
  criterion and the registers reading (10 % of the chance-to-perfect distance).
- **Part B not run.** It concerns MATR, HUST and NASA, and is excluded by the brief.
- **New for this profile: paired retrieval (D01).** FORM carries inserted patterns, so paired retrieval is computed.
  - It is ported from v1 S7 part one into `part_a`. V7 had never run it, because no v2 profile had patterns.
  - It uses 20 windows with at least one sparse cell from each test unit that has one (32 units, 640 windows).
  - The window map φ* and its pattern-free counterpart are degraded by the same operator, with independent streams.
  - The score is the AP of the paired difference, with plain AP as the secondary score.
  - Resolution uses the declared criterion. The registers reading is also computed but is marked descriptive, because
    `v2.scoring.registers_check` names only the three X5 scores.

## Results (`tables/degradation.json`)

### Registering magnitude (recency)

Same layout as Table 5. A dash means the score does not register the operator at any grid magnitude.

| operator | rank | allocation | temporal | MATR (r / a / t) | HUST (r / a / t) |
|---|---|---|---|---|---|
| added noise | 0.2 | 0.1 | 0.5 | 0.05 / 0.1 / 0.5 | 0.2 / 0.1 / 0.5 |
| mass to start | 1.0 | – | 0.05 | 1.0 / – / 0.05 | 1.0 / – / 0.05 |
| mass to end | 1.0 | – | 0.1 | 1.0 / – / 0.1 | 1.0 / – / 0.1 |
| smoothing | – | – | 8 | – / – / 8 | – / – / 8 |
| permuted fraction | 0.2 | 0.1 | 0.2 | 0.2 / 0.1 / 0.2 | 0.2 / 0.1 / 0.2 |

- **FORM reproduces the v2 pattern.**
  - Rank agreement misses mass moved toward an end below a full shift.
  - Allocation error does not register shifts.
  - The temporal profile error registers shifts at 0.05–0.1 and smoothing at σ = 8 under recency.
- **Every score is resolved** at the smallest grid magnitude by every operator, except smoothing (resolved at 0.5).
- **Chance levels (recency):** rank −0.001, allocation 0.476, temporal 5.21 positions.
- **Uniform weighting** gives the same picture, with smoothing unregistered (expected; see the declaration).

### Paired retrieval (recency)

- **The undegraded map scores 1.0**, against a chance of 0.070.
- **Added noise, permuted fraction and both mass shifts** resolve it at 0.05. Noise at 0.05× the map SD already lowers it
  to 0.37, and a full shift to 0.10.
- **Smoothing lowers it only to 0.993 at σ = 8** (resolved at 1). The paired difference of two smoothed maps still
  localises the patterns.
- **Plain retrieval stays near chance** (0.095 undegraded). This confirms D01: on a single map the graded field outweighs
  the patterns.

## Checks

The undegraded ground truth scores perfect on all three scores, for both weightings.

## Next

W6 (ensemble and gates) and W5 (fidelity) are running on the GPU. W8 follows W6.
