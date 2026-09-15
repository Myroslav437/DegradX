# D20 — The operating range is read on two probes, the reference model and IG on the trained model, with the accuracy gate applied

**Stage / claim affected:** S7 part two (Table 5, Figure 8); the RQ3 answer about the settings over which the benchmark is informative.

**Decision.** §3.5.3 requires the second part of RQ3 to vary the generator settings and report the range over which the scores remain responsive, and declarations `responsiveness.operating_range` fixes the rule (normalised score $\ge 0.95$ saturated, $\le 0.05$ or interval including chance near chance). Neither says on which model's attribution map the score is computed. What is the probe?

**Options considered**
- **a. Integrated Gradients on the primary trained model** (what the stage computes per setting value).
- **b. The reference model.** Its exact attribution $w(x - x^{0})$; IG and occlusion on it equal that to 1e-7 (S8 checks), so this is "IG on the reference model".
- **c. Both**, a setting value inside the range only where the score is responsive on both probes and the trained model passes the declared accuracy gate.
- **d. TimeSHAP on the trained model.** Not chosen: at 5–7 s per window (D22) a sampling-based probe over 57 setting values is outside the budget the same stage already reduced (D23), and it would add sampling variance to a range boundary.

**Evidence** (`experiments/decisions/D20/{run.py,result.json,run.log}`): 57 setting values over the three profiles, recency weighting. The harness regenerates each row's units, split and windows from the same seeds and recomputes the reference-model scores per unit; the recomputed mean reproduces the stored value at all 57 values (|diff| < 1e-9), so the two probes are compared on identical windows.

| probe | rank agreement | paired retrieval (NASA PCoE, 23 values) |
|---|---|---|
| a. IG on the trained model | responsive at 57 of 57 values | saturated at 20 of 23 |
| b. reference model | responsive at 51, saturated at 6 | saturated at 23 of 23 (1 by construction) |
| accuracy gate (NRMSE ≤ 0.30) | failed at 2 values (NASA PCoE, noise ×8: 0.334; ×16: 0.361) | same 2 values |

Real: all measured. Works:
- (a) excludes nothing: every examined value is "responsive", including the two where the trained model is below the accuracy gate and §3.5.2 voids its scores.
- (b) excludes the 6 values where the ceiling saturates but keeps those 2.
- (c) excludes 8 values: the 6 saturated ceilings and the 2 gate failures.

Clear: "a setting value is inside the operating range when the score is neither saturated nor at chance on the reference model and on the trained model with Integrated Gradients, and the trained model passes the accuracy gate."

**Chosen: c.**
1. *Logical:* the reference model is the declared primary scoring target (C2), and where its exact attribution saturates, no faithful method can be told from another whatever the trained model does; the trained probe adds the failure the ceiling cannot show, a model too inaccurate for its scores to mean anything.
2. *Consistent:* uses the declared saturation and near-chance rule and the declared accuracy gate; introduces no new constant.
3. *Clear:* one sentence, no new term.
4. *Measured:* (a) excludes 0 of 57 values, (b) 6, (c) 8.

**Cost.**
- The stage stores per-unit scores for both probes and recomputes them for rows cached before this decision: 6 CPU-minutes over all profiles, no GPU.
- The boundary is unstable where the ceiling sits near 0.95: HUST noise ×0.5 (0.966) falls outside while ×0.25 (0.946) and ×1 (0.923) are inside, and HUST $L=48$ (0.956) is isolated in the same way. Table 5 marks such values in the failure column instead of smoothing the interval.
- Paired retrieval has no operating range under this rule on any setting: on the reference model it is exactly 1 at every value by construction, and on the trained model it is saturated at 20 of 23. Table 5 reports it as void with that reason. A reviewer may read this as a defect of the retrieval score rather than of the settings; it is reported, not corrected.

**Paper impact:** Table 5 gains a profile and a score column and states the two probes in its caption; §4.3 reports the range per probe and Figure 8 plots both. Recorded in `docs/AMENDMENTS.md` (round 6).
