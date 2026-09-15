# D08 — Where a score does not fall under a degradation, the cause is the construction of the field, not the implementation

**Stage / claim affected:** S7 part one (Table 4, Figure 7); the reading of each score's resolution.

**Decision.** Some (score, operator, weighting) combinations do not resolve any degradation magnitude, or fall only by amounts too small to matter. Each needs to be either an implementation bug or a property of the score.

**Options considered**
- **a.** Implementation bug: fix and rerun.
- **b.** Property of the score on this field: report it as such.
- **c.** No change to the scores; report resolution only (the declared criterion) without the size of the drop.

**Evidence** (`artifacts/s7_responsiveness/tables/part1_degradation.json`, `logs/checks.md`; generation seed 0 test units, 900 windows on MATR and HUST, 706 on NASA, 378 NASA windows with sparse cells)

Sanity tests, which must pass before any insensitivity is read as a finding (brief S7; 72 checks, 0 failures):
- a fully permuted graded map scores at chance (Spearman within 0.05 of the permuted-map chance level, ≈ 0.00) in every profile and weighting;
- the fully permuted paired retrieval scores at chance (NASA: 0.048 vs chance 0.050, recency);
- every operator at magnitude 0 leaves both scores at exactly 1.

Non-responses and near-non-responses:

| profile / weighting | score | operator | mean score over the grid | reading |
|---|---|---|---|---|
| all / final position | rank agreement | mass shifted to end | 1.000 at every magnitude, including 1.0 | the final-position field already lies entirely on the last position, so the operator is the identity on it |
| NASA / final position | paired retrieval | mass shifted to end; smoothing | 1.000 at every magnitude | the sparse set under final-position weighting is at most one cell per window, and neither operator moves it off the top rank |
| all / recency, uniform | rank agreement | smoothing σ = 0.5 → 8 | 1.000 → 0.997 (resolved at 0.5 by the declared criterion) | the graded field is smooth along positions, so Gaussian smoothing hardly reorders it; statistically resolved, practically insensitive |
| all / recency | rank agreement | mass shifted to end, f = 0.05 … 0.8 | 1.000 (rounded) until f = 1.0 (0.24–0.26) | under recency weighting the last position already carries the largest graded value, so moving mass there keeps the order until the whole field is one cell |
| NASA / uniform, recency | plain retrieval | several operators | unresolved | plain retrieval is at chance for the undegraded ground truth (D01) |

Real: all measured. Works:
- (a) is excluded by the sanity tests.
- (b) explains every non-response from the field's construction.
- (c) would report "resolved at σ = 0.5" for a 0.3 % change without qualification.

Clear, option (b) with the drop reported: a score's resolution is the smallest degradation it detects reliably, and the size of the drop at that magnitude is reported next to it. Where a score does not respond, the reason is that the operator does not change what the score measures on that field, which is a property of the pair.

**Chosen: b, with the mean change at the resolved magnitude reported beside each resolution.**
1. *Logical:* the brief's rule ("a score that does not fall under degradation is a finding about the score … verify it is not an implementation bug first").
2. *Consistent:* the declared reliability criterion is unchanged.
3. *Clear.*
4. *Measured:* the sanity tests pass.

**Cost.**
- Rank agreement cannot tell a correct map from a smoothed one on recency and uniform fields, where the drop is under 0.3 % at σ = 8. It also cannot see mass moved toward the recent end until the field collapses.
- A reviewer may read Table 4's "resolution" as practical sensitivity. The drop column prevents that reading.

**Paper impact:** none in the methodology; §4.3 reports these cases.
