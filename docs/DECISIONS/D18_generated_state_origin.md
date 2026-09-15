# D18 — A generated unit's degradation state is anchored at its own trajectory's early-life reference

**Stage / claim affected:** S4 generator (the origin of z, and hence of the mean component). The S4 check "z runs 0 → 1" fails on NASA PCoE without this change.

**Decision.** Each generated unit resamples a fitted unit's θ and that unit's measured `q₁`. The measured `q₁` is the maximum of the smoothed noisy capacity over the first 20 positions, so on noisy records it sits above the fitted trend's own start by up to 22 mAh (NASA). The generated state then begins above 0: z₁ reaches 0.087 on NASA and 0.040 on HUST. Where does the generated state start?

**Options considered**
- **a. No change:** `z = (q₁,j − Q(n)) / (q₁,j − ρ q_nom)`.
- **b.** `z = (Q_ref − Q(n)) / (Q_ref − ρ q_nom)`, with `Q_ref` the maximum of the generated trajectory Q over the first 20 positions. This is Eq. 3's early-life reference applied to the generated trajectory.
- **c.** Keep (a) and relax the S4 check tolerance. This is not admissible, since it weakens a check so the result passes.

**Evidence** (`experiments/decisions/D18/{run.py,result.json}`: every θ unit of every profile)

| | MATR (90) | HUST (54) | NASA PCoE (8) |
|---|---|---|---|
| q₁,j − Q_ref, median [max] mAh | −2.7 [1.7] | 6.5 [13.6] | 0.5 [21.9] |
| z at position 1, max: a / b | 0.0087 / 0.0004 | 0.040 / 0.000 | 0.087 / 0.000 |
| units whose T is identical under a and b | 90 / 90 | 54 / 54 | 8 / 8 |

Real: both run. Works: (b) removes the offset, and T is unchanged in every unit, because z = 1 falls where Q = ρ·q_nom under either reference.

Clear, option (b): "A generated unit's degradation state is measured from its own trajectory's early-life reference, exactly as Eq. 3 measures a measured unit's state from its own." Failure mode: none on T. A trajectory rising over its first 20 positions would move the origin to the peak, as Eq. 3 does for measured units.

**Chosen: b.**
1. *Logical:* it is Eq. 3 applied to the generated series.
2. *Consistent:* measured units have z = 0 at t₁ by definition, and generated units now do too. The paper's reading ("the degradation state runs from 0 at the early-life reference to 1 at EOL") holds for both.
3. *Clear:* one clause.
4. *Measured:* z₁ ≤ 0.0004 everywhere, T identical.

**Cost.** Generated capacity starts at the shared mapping's pristine level q̄₁ regardless of the source unit's measured q₁ bias. That was already the case through the shared capacity mapping (C1 × C3), so nothing new is lost. A reviewer may ask why measured and generated references differ in construction. Both are "the maximum over the first 20 positions of the series the state is defined on".

**Paper impact:** none (generator implementation of Eq. 3).
