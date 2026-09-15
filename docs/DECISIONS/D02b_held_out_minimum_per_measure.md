# D02b — Minimum held-out measured units per fidelity measure (supersedes D02's provisional 5)

**Stage / claim affected:** Table 1 (every column) and the NASA PCoE fidelity row; S5 void flags.

**Decision.** D02 set a provisional minimum of 5 held-out units for all distributional and transfer measures. S5 then showed it is not enough for the discriminator: NASA's 5 held-out units leave 1 measured unit in the discriminator's test split, and its accuracy swings from 0.50 to 0.98 across generation seeds. What minimum applies to each measure?

**Options considered**
- **a.** Keep 5 units for every measure.
- **b.** Per-measure minima from resampling, using D02's criterion (95 % half-width ≤ 50 % of the value) for every measure.
- **c.** As (b), but the discriminative error, whose informative reading is its distance from 0.5 (indistinguishable), counts as readable when its half-width is at most half of |0.5 − value|. For the representation distance, which no subsample size up to 20 made readable, readability is checked by a bootstrap over the profile's own held-out units.

**Evidence** (`experiments/decisions/D02b/{run.py,result.json,run.log}`): MATR's 38–40 held-out units; draws without replacement; 40 draws per size (8 for the retrained discriminator).

95 % half-width relative to the full-sample value:

| held-out units n | 3 | 5 | 8 | 12 | 20 |
|---|---|---|---|---|---|
| TSTR ratio (full 3.68) | 2.05 | 1.54 | 0.85 | 0.51 | **0.42** |
| representation distance (full 86.2) | 6.81 | 4.06 | 2.52 | 1.66 | 0.99 |
| covariance agreement, rel. Frobenius (full 0.69) | 0.62 | 0.56 | 0.55 | **0.43** | 0.28 |
| discriminative error (full 0.031) | 7.70 | 7.99 | 7.02 | 3.91 | 1.54 |
| discriminative error half-width in absolute terms | 0.241 | 0.250 | **0.219** | 0.122 | 0.048 |
| half of \|0.5 − 0.031\| | 0.234 | 0.234 | 0.234 | 0.234 | 0.234 |

Real: all run. Works:
- (a) reports a discriminator trained and tested on single units.
- (b) voids the discriminative error at every size, because a small error has a large relative interval even when the separation is unambiguous (0.03 ± 0.05 reads as "separates"), and the relative criterion was never meant for a score whose zero is informative.
- (c) gives readable minima for every measure except the representation distance, which needs a direct check at the available count.

Clear, option (c):
1. The transfer ratio needs at least 20 held-out units reaching EOL, and covariance agreement at least 12.
2. The discriminative error needs at least 8 held-out units; its interval must stay within half its distance from 0.5.
3. The representation distance is reported only where a bootstrap over the profile's held-out units shows its interval within half its value.

Failure mode: the curves come from one profile (MATR), and other profiles' variances differ.

**Chosen: c.** Minima:
- transfer ratio: 20 held-out units reaching EOL;
- covariance agreement: 12 held-out units;
- discriminative error: 8 held-out units, readable relative to |0.5 − value|;
- representation distance: unit bootstrap at the profile's own count, half-width ≤ 50 % of the value.

Criteria:
1. *Logical:* D02's criterion applied per measure; the discriminator clause reads the score where it carries its meaning.
2. *Consistent:* D02's "counts gate reporting" and Table 3's void convention.
3. *Clear:* four one-line rules.
4. *Measured:* the curves above.

**Cost.**
- NASA PCoE (5 held-out, 3 reaching EOL) is void on every Table 1 column.
- HUST's transfer ratio stands on 23 units, just above its minimum.
- Two readability definitions exist, and a reviewer may call the discriminator's distance-to-0.5 clause a softer standard. It is the reading the paper already assigns to the discriminator ("coarse indicator only").
- The curves are MATR-specific.

**Paper impact:** none beyond D02's round-3 sentence (minimum counts exist and are declared). The values go in the Results table notes.
