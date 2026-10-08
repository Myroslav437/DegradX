# D29 — HUST is the fidelity anchor of v2; MATR is reported with its remaining transfer gap, and the generator is not iterated

**Stage / claim affected:**
- V5 (brief "DegradX v2", RQ1);
- the declared reading `v2.readings.X2_i_closes_matr_gap` and `v2.fidelity.anchor_rule`;
- Table 1, §4.1, §5 "What resists calibration".

**Decision.**
- The declared reading for X2(i) is that MATR's gap is closed iff MATR's v2 transfer ratio lies within HUST's v2 95 %
  interval. **It does not:** MATR 1.490 [1.042, 2.291] against HUST [0.936, 1.342].
- The brief: "If MATR's ratio is not brought within HUST's interval, do not iterate on the generator. Report the
  result, and record in a D-record which profile is the fidelity anchor."
- Which profile is the anchor?

**Evidence** (`artifacts/v2/v5_fidelity/tables/fidelity.json`; v1 values from `artifacts/s5_fidelity`)

| measure | MATR v1 → v2 | HUST v1 → v2 | declared reading |
|---|---|---|---|
| transfer ratio [95 % BCa] | 3.42 [2.28, 4.96] → **1.49 [1.04, 2.29]** | 1.46 [1.11, 1.76] → **1.17 [0.94, 1.34]** | X2(i): MATR within HUST's interval → **no** |
| discriminative error (mean over generation seeds; 0.5 = indistinguishable) | 0.072 → 0.333 | 0.164 → 0.485 | X3: narrows beyond v1's seed half-range → yes (both) |
| covariance agreement, rel. Frobenius (measured baseline, its 95 % unit-bootstrap upper end) | 0.687 → 0.209 (0.174; 0.442) | 0.424 → 0.054 (0.038; 0.125) | X3: within the baseline's interval → **closed** (both) |
| same two measures, X3 switched off (generation seed 0) | disc. 0.355; cov. 0.207 | disc. 0.410; cov. 0.059 | X3's own share: negligible; the change comes from X2 |
| X1 on the v2 profile: per-cell structure, Δlog [95 %] | 1.14 → 0.42 [0.06, 0.90], not robust to leave-one-seed-out | 0.13 → 0.12 [−0.07, 0.26] | |

**Options considered**
- **a. HUST is the anchor.**
  - Its transfer interval contains 1: a generated-trained model is as accurate on held-out measured cells as a
    measured-trained one.
  - Its discriminator is at chance (0.485), and its covariance agreement lies within the measured baseline's interval.
  - MATR is reported with the residual gap.
- **b. MATR is the anchor.** It has more cells and the dataset the paper cites first. Its ratio is still above 1, with
  a lower bound of 1.04.
- **c. No anchor:** both profiles reported side by side, with no profile stated as the one whose fidelity the benchmark
  rests on.

Real: all three are possible.

Works:
- (a) states a profile on which every fidelity measure is satisfied.
- (b) would anchor the benchmark on a profile that fails the declared reading.
- (c) does not do what the brief asks.

Clear: (a) in one sentence: "HUST is the profile whose fidelity is established on every measure; MATR transfers at
1.49 times the measured error, down from 3.42."

**Chosen: a.**
1. *Logical:* the anchor is the profile whose fidelity the declared readings support.
2. *Consistent:* the brief's anchor rule; no generator iteration.
3. *Clear:* one sentence.
4. *Measured:* every HUST reading passes; MATR fails one.

**What the remaining MATR gap is.**
- The X1 ablation on the v2 profile still finds most of it in the non-capacity channels: capacity alone transfers at
  0.98 [0.92, 1.08]. But the interval of the difference is no longer robust when single seeds are left out.
- Centring the non-capacity channels per unit now worsens transfer (1.94). The generated offsets match the measured
  ones well enough that removing them removes information both sides share.
- What remains is non-capacity structure that is neither a constant offset nor the pooled within-unit correlation.
  Charge-time trajectories that differ in shape between charging policies (Figure 3 of v1 S3 shows the band structure)
  are the obvious candidate. The brief forbids iterating, so this is stated, not fixed.

**Cost.**
- MATR stays a profile with a measured transfer gap (1.49), and its scores carry that caveat.
- The anchor is the smaller profile (77 cells, one charging protocol).
- **X3 did not do what it was introduced for.** Its contribution to the covariance and discriminator gains is
  negligible beside X2's. This is reported as a negative result for X3.

**Paper impact:** §4.1 (anchor sentence, v1 → v2 table, X3 isolation in the table note); §5 "What resists calibration"
rewritten.
